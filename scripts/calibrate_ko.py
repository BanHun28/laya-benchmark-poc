#!/usr/bin/env python
"""Track E (03 §9, 05 P3): temperature refit and gating curves for the Korean PoC, multilingual, CPU fp32.

Rows are split exactly as in Track B (scripts/metrics_extra.py `row_splits`; rule, counts and label
distribution asserted against --splits), so a test row never enters a fit. Every row of --sets goes once
through `laya.calibrate.records_from_labeled`: dev records are fitted, test records are only scored.
Confidence is `answer_confidence` (max p) rounded to 4 decimals, computed as `Agent._decode_answers` does
(float32 z / T), so a gate T found here is the value the policy compares against.

  E1 --reports R...    as-shipped 15-bin reliability per split, from laya-evals reports (no model)
  E2 --sets A,B        fits on dev records: (i) fit_temperature_map (MIN_BUCKET_N / MIN_TYPE_N floors) and
                       (ii) fit_one_temperature per temp_bucket with n >= --min-bucket-n; --per-task and/or
                       --pooled; every fit scored on every set's test half (ECE, NLL before -> after)
  E3                   coverage vs gate T on test; gate T chosen on dev per error budget, then applied to test;
                       per-label T (05 §5 T_BY_DOMAIN) chosen on dev, applied to test
  E4 --out-payload P   calibration_payload of the --payload-fit official map; the first set's test half is
                       re-scored through laya.load(calibration=P) and apply_calibration_payload on a fresh agent
  E6 --noul-report R   noul p(true): ROC-AUC, threshold chosen on dev (Youden J, max accuracy), applied to test
"""
import argparse
import contextlib
import hashlib
import json
import os
import sys
import time
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import torch

import laya
import laya.calibrate as cal
from laya.common import QTYPE_NAMES, temp_bucket

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import metrics_extra as mx  # noqa: E402  read_dataset, row_splits, load_report, ece, ece_bins, coverage_table

GRID = [round(t, 2) for t in np.arange(0.50, 0.951, 0.05)] + [0.99]
BUDGETS = (0.05, 0.10, 0.15)
SWEEP = (1.0, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.4, 2.6, 3.0)   # ECE/NLL sensitivity to a choice scalar T


def js(x):
    """JSON-safe copy: numpy to Python, NaN/inf to null."""
    if isinstance(x, dict):
        return {str(k): js(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, np.ndarray)):
        return [js(v) for v in x]
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (float, np.floating)):
        return float(x) if np.isfinite(x) else None
    if isinstance(x, np.integer):
        return int(x)
    return x


# ---------------------------------------------------------------- data and records
def load_set(path, ref, manifest):
    path = mx.resolve(path)
    rows, header = mx.read_dataset(path)
    split, rule = mx.row_splits(rows, header, "auto", path.name)
    dist = {"dev": {}, "test": {}}
    for row, sp in zip(rows, split):
        for qid, gold in row["expected"].items():
            dist[sp].setdefault(qid, Counter())[str(gold)] += 1
    got = {"rule": rule, "dev": split.count("dev"), "test": split.count("test"),
           "label_distribution": {sp: {q: dict(c) for q, c in d.items()} for sp, d in dist.items()}}
    want = ref["splits"][path.stem]
    assert got == {k: want[k] for k in got}, "%s: split differs from the Track B split file" % path.stem
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    entry = manifest["files"][path.name]
    assert sha == entry["sha256"], "%s: bytes differ from MANIFEST" % path
    return {"name": path.stem, "path": str(path), "rows": rows, "split": split, "rule": rule,
            "dataset_sha256": sha, "questions_sha256": entry["questions_sha256"]}


def collect(agent, sets):
    """One records_from_labeled call per row, so each (qtype, logits, target, k) record keeps its row and split."""
    recs = []
    for s in sets:
        for i, (row, sp) in enumerate(zip(s["rows"], s["split"])):
            qs = row["questions"]
            for qid, q in qs.items():
                assert q["type"] == "choice" and "option_order" not in q, "%s row %d %s: choice only" % (s["name"], i, qid)
            targets = {qid: [float(lab == row["expected"][qid]) for lab in q["criteria"]] for qid, q in qs.items()}
            # predict_batch runs under @torch.no_grad() (laya/agent.py:1248); records_from_labeled calls the same
            # _forward without it, and _forward's .numpy() (agent.py:1177) refuses a grad-tracking tensor.
            with torch.no_grad():
                out = cal.records_from_labeled(agent, [(row["state"], qs, targets)])
            assert len(out) == len(qs), (s["name"], i)
            for (qid, q), rec in zip(qs.items(), out):
                assert rec[2].sum() == 1.0, (s["name"], i, qid)
                recs.append({"set": s["name"], "row": i, "split": sp, "qid": qid, "rec": rec,
                             "y": int(np.argmax(rec[2])), "labels": list(q["criteria"])})
    return recs


def t_of(tmap, qt, k):
    """`Agent._decode_answers` lookup: the bucket entry, else the type scalar."""
    return tmap["temperature_by_options"].get(temp_bucket(qt, k), tmap["temperature"][qt])


def score(recs, tmap):
    conf, pmax, corr, pred, nll = [], [], [], [], []
    for r in recs:
        qt, z, _t, k = r["rec"]
        T = t_of(tmap, qt, k)
        zt = z / T
        p = np.exp(zt - zt.max())
        p = p / p.sum()
        j = int(p.argmax())
        conf.append(round(float(np.clip(p.max(), 0.0, 1.0)), 4))
        pmax.append(float(p.max()))
        corr.append(float(j == r["y"]))
        pred.append(r["labels"][j])
        z64 = z.astype(np.float64) / T
        nll.append(float(np.logaddexp.reduce(z64) - z64[r["y"]]))
    conf, corr = np.array(conf), np.array(corr)
    return {"conf": conf, "pmax": np.array(pmax), "corr": corr, "pred": np.array(pred),
            "m": {"n": len(recs), "accuracy": float(corr.mean()), "mean_conf": float(conf.mean()),
                  "ece": mx.ece(conf, corr), "ece_ci": mx.boot_ci(conf, corr, 1000, 13)[1], "nll": float(np.mean(nll))}}


# ---------------------------------------------------------------- E2 fits
@contextlib.contextmanager
def pre_clamp():
    """Collect each optimum `fit_one_temperature` hands to `clamp_temperature` (it returns only the clamped value)."""
    seen, orig = [], cal.clamp_temperature
    cal.clamp_temperature = lambda t, lo=cal.TEMP_MIN, hi=cal.TEMP_MAX: seen.append(float(t)) or orig(t, lo, hi)
    try:
        yield seen
    finally:
        cal.clamp_temperature = orig


def fit(dev, min_bucket_n, seed):
    recs = [r["rec"] for r in dev]
    with pre_clamp() as seen:
        m = cal.fit_temperature_map(recs, compute_ece=True, seed=seed)
    n_type = Counter(int(r[0]) for r in recs)
    # _fit_groups order: type scalars with n >= MIN_TYPE_N in qtype order, then buckets >= MIN_BUCKET_N
    names = ["type:" + QTYPE_NAMES[qt] for qt in sorted(QTYPE_NAMES) if n_type[qt] >= cal.MIN_TYPE_N]
    names += list(m["temperature_by_options"])
    assert len(names) == len(seen), (names, seen)
    official = {"temperature": m["temperature"], "temperature_by_options": m["temperature_by_options"],
                "raw": dict(zip(names, seen)), "n_by_bucket": m["n_by_bucket"], "fitter_report": m["report"]}
    buckets = {}
    for key, n in sorted(m["n_by_bucket"].items()):
        if n >= min_bucket_n:
            pairs = [(z, t) for qt, z, t, k in recs if temp_bucket(qt, k) == key]
            with pre_clamp() as seen:
                buckets[key] = {"n": n, "T": cal.fit_one_temperature(pairs, min_n=min_bucket_n)}
            buckets[key]["raw"] = seen[0]
    lowfloor = {"temperature": [1.0] * len(QTYPE_NAMES),
                "temperature_by_options": {k: v["T"] for k, v in buckets.items()}, "buckets": buckets}
    return {"n_dev": len(recs), "official": official, "lowfloor": lowfloor}


# ---------------------------------------------------------------- E3 gating
def as_cases(conf, corr):
    return [{"conf": float(c), "correct": bool(k)} for c, k in zip(conf, corr)]


def max_cov_T(conf, corr, budget):
    """Gate T of the largest coverage whose covered error is within budget (metrics_extra); None if there is none."""
    return mx.coverage_table(as_cases(conf, corr), [], [budget])[1][str(budget)]["T"]


def gate(conf, corr, thr):
    """05 §5: ROUTE when answer_confidence >= T. `thr` is a scalar or per row; inf = always FALLBACK."""
    covered = conf >= thr
    return {"coverage": float(covered.mean()), "n": int(covered.sum()),
            "error": float(1 - corr[covered].mean()) if covered.any() else None}


def per_label(d, t, budget):
    """T_BY_DOMAIN: per predicted label, the dev T keeping that label's routed error within budget (None = FALLBACK)."""
    Ts = {lab: max_cov_T(d["conf"][d["pred"] == lab], d["corr"][d["pred"] == lab], budget) for lab in sorted(set(d["pred"]))}
    thr = lambda x: np.array([np.inf if Ts.get(p) is None else Ts[p] for p in x["pred"]])  # noqa: E731
    return {"T": Ts, "n_dev_pred": dict(Counter(d["pred"].tolist())),
            "dev": gate(d["conf"], d["corr"], thr(d)), "test": gate(t["conf"], t["corr"], thr(t))}


def coverage_block(d, t):
    curve, oracle = mx.coverage_table(as_cases(t["conf"], t["corr"]), GRID, BUDGETS)
    out = {"curve_test": curve, "oracle_test": oracle, "dev_chosen": {}, "per_label": {}}
    for b in BUDGETS:
        T = max_cov_T(d["conf"], d["corr"], b)
        thr = np.inf if T is None else T
        out["dev_chosen"][str(b)] = {"T": T, "dev": gate(d["conf"], d["corr"], thr), "test": gate(t["conf"], t["corr"], thr)}
        out["per_label"][str(b)] = per_label(d, t, b)
    return out


def auroc(s, y):
    """P(score of a positive > score of a negative), ties counted half (Mann-Whitney U)."""
    y = np.asarray(y, bool)
    _, inv, cnt = np.unique(s, return_inverse=True, return_counts=True)
    rank = (np.cumsum(cnt) - (cnt - 1) / 2.0)[inv]
    n1, n0 = int(y.sum()), int((~y).sum())
    return float((rank[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else None


def discordant(a, b):
    """Share of row pairs ordered differently by `a` and `b` (a tie in either is not discordant)."""
    i, j = np.triu_indices(len(a), 1)
    return float((np.sign(a[i] - a[j]) * np.sign(b[i] - b[j]) < 0).mean())


# ---------------------------------------------------------------- E1, E6 (reports only)
def reliability(conf, corr):
    b = mx.ece_bins(conf)
    bins = [{"i": i, "n": int((b == i).sum()), "conf": float(conf[b == i].mean()), "acc": float(corr[b == i].mean())}
            for i in range(mx.BINS) if (b == i).any()]
    gap = float(conf.mean() - corr.mean())
    return {"n": len(conf), "accuracy": float(corr.mean()), "mean_conf": float(conf.mean()), "ece": mx.ece(conf, corr),
            "gap": gap, "direction": "over-confident" if gap > 0 else "under-confident", "bins": bins}


def e1(reports):
    out = []
    for r in reports:
        for qid, sp, cs in mx.groups(r):
            conf = np.array([c["conf"] for c in cs])
            corr = np.array([c["correct"] for c in cs], float)
            out.append({"report": r["path"], "set": r["set"], "qid": qid, "split": sp, **reliability(conf, corr)})
    return out


def e6(r):
    noul = [c for c in r["cases"] if c["type"] == "noul"]
    choice = {c["row"]: c for c in r["cases"] if c["type"] == "choice"}

    def arrays(sp):
        cs = [c for c in noul if sp == "all" or c["split"] == sp]
        return np.array([c["probs"]["true"] for c in cs]), np.array([c["gold"] == "true" for c in cs]), cs

    pd, yd, _ = arrays("dev")
    cand = np.r_[np.unique(pd), np.inf]          # predict true when p(true) >= threshold; first max on ties
    yh = pd[None, :] >= cand[:, None]
    j = (yh & yd).sum(1) / yd.sum() - (yh & ~yd).sum(1) / (~yd).sum()
    rules = {"default 0.5": 0.5, "Youden J (dev)": float(cand[np.argmax(j)]),
             "max accuracy (dev)": float(cand[np.argmax((yh == yd).mean(1))])}

    def stats(p, y, thr):
        yhat = p >= thr
        tp = int((yhat & y).sum())
        return {"accuracy": float((yhat == y).mean()), "pos_rate": float(yhat.mean()), "gold_pos_rate": float(y.mean()),
                "precision": tp / int(yhat.sum()) if yhat.any() else None, "recall": tp / int(y.sum())}

    res = {"report": r["path"], "qid": noul[0]["qid"], "auroc": {}, "always_no": {}, "choice_variant": {},
           "rules": {k: {"threshold": v} for k, v in rules.items()}}
    for sp in ("dev", "test", "all"):
        p, y, cs = arrays(sp)
        res["auroc"][sp] = auroc(p, y)
        res["always_no"][sp] = float(1 - y.mean())
        res["choice_variant"][sp] = float(np.mean([choice[c["row"]]["correct"] for c in cs]))
        for k, v in rules.items():
            res["rules"][k][sp] = stats(p, y, v)
    t = res["rules"]["Youden J (dev)"]["test"]
    res["accept_03_E6"] = {"youden_test_acc_above_always_no": t["accuracy"] > res["always_no"]["test"],
                           "youden_test_pos_rate_within_5pt": abs(t["pos_rate"] - t["gold_pos_rate"]) <= 0.05}
    return res


# ---------------------------------------------------------------- E4
def e4(a, s0, expect_ece, expect_conf):
    test = [row for row, sp in zip(s0["rows"], s0["split"]) if sp == "test"]
    answers, out = {}, {"set": s0["name"], "n": len(test), "payload": a.out_payload,
                        "payload_sha256": hashlib.sha256(Path(a.out_payload).read_bytes()).hexdigest()}
    for how in ("load_calibration", "apply_calibration_payload"):
        t0 = time.time()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            if how == "load_calibration":
                agent = laya.load(a.model, device=a.device, calibration=a.out_payload)
            else:
                agent = laya.load(a.model, device=a.device)
                cal.apply_calibration_payload(agent, json.loads(Path(a.out_payload).read_text()))
            answers[how] = [agent.predict(row["state"], row["questions"], lang="ko")["answers"] for row in test]
        out[how] = {"warnings": ["%s: %s" % (w.category.__name__, w.message) for w in caught], "secs": time.time() - t0,
                    "temperature": list(agent.temperature), "temperature_by_options": dict(agent.temperature_by_options)}
        del agent
    A, B = answers["load_calibration"], answers["apply_calibration_payload"]
    conf = np.array([ans[q]["answer_confidence"] for ans in A for q in ans])
    corr = np.array([float(ans[q]["choice"] == row["expected"][q]) for row, ans in zip(test, A) for q in ans])
    out["ece_reloaded"] = mx.ece(conf, corr)
    out["ece_e2_after"] = expect_ece
    out["abs_diff"] = abs(out["ece_reloaded"] - expect_ece)
    out["pass_within_0.005"] = out["abs_diff"] <= 0.005
    out["max_abs_dconf_vs_records"] = float(np.abs(conf - expect_conf).max())
    out["max_abs_dp_load_vs_apply"] = max(abs(x[q]["probabilities"][o] - y[q]["probabilities"][o])
                                          for x, y in zip(A, B) for q in x for o in x[q]["probabilities"])
    out["identical_answers_load_vs_apply"] = A == B
    return out


# ---------------------------------------------------------------- Markdown
def f3(x):
    return "-" if x is None else "%.3f" % x


def ce(g):
    return "%.3f / %s" % (g["coverage"], f3(g["error"]))


def render(res):
    md = ["# Track E calibration (calibrate_ko.py)", "", "`%s` (%s)" % (" ".join(res["run_card"]["argv"]), res["run_card"]["generated_at"])]
    for e in res.get("e1", []):
        if e["split"] != "dev":
            continue
        t = next(x for x in res["e1"] if (x["set"], x["qid"], x["split"]) == (e["set"], e["qid"], "test"))
        al = next(x for x in res["e1"] if (x["set"], x["qid"], x["split"]) == (e["set"], e["qid"], "all"))
        md += ["", "## E1 %s / %s (as-shipped, 15 bins of answer_confidence)" % (e["set"], e["qid"]), "",
               "| bin | dev n | dev conf | dev acc | test n | test conf | test acc |", "|---|---|---|---|---|---|---|"]
        bd, bt = {b["i"]: b for b in e["bins"]}, {b["i"]: b for b in t["bins"]}
        for i in sorted(set(bd) | set(bt)):
            x, y = bd.get(i), bt.get(i)
            md.append("| (%.3f, %.3f] | %s | %s | %s | %s | %s | %s |" % (
                i / mx.BINS, (i + 1) / mx.BINS, x["n"] if x else 0, f3(x and x["conf"]), f3(x and x["acc"]),
                y["n"] if y else 0, f3(y and y["conf"]), f3(y and y["acc"])))
        md += ["", "ECE dev %.3f / test %.3f / all %.3f; mean conf − acc: dev %+.3f, test %+.3f (%s / %s)" % (
            e["ece"], t["ece"], al["ece"], e["gap"], t["gap"], e["direction"], t["direction"])]
    if "e2" in res:
        e2 = res["e2"]
        md += ["", "## E2 refit on the dev half", "", "Records vs Track B report (T = 1): " + "; ".join(
            "%s argmax %d/%d, max |Δ answer_confidence| %.4f" % (k, v["agree"], v["n"], v["max_abs_dconf"])
            for k, v in e2["parity_vs_report"].items()), "",
            "| fit | dev n | n by bucket | (i) official map: raw → applied | fitter held-out n_eval | (ii) min_n=%d: bucket raw → applied |"
            % res["run_card"]["min_bucket_n"], "|---|---|---|---|---|---|"]
        for g, f in e2["fits"].items():
            o, lf = f["official"], f["lowfloor"]["buckets"]
            applied = {**{"type:" + QTYPE_NAMES[i]: t for i, t in enumerate(o["temperature"])}, **o["temperature_by_options"]}
            md.append("| %s | %d | %s | %s; by_options %s | %d | %s |" % (
                g, f["n_dev"], json.dumps(o["n_by_bucket"]),
                ", ".join("%s %.4f → %.4f" % (k, v, applied[k]) for k, v in o["raw"].items()), json.dumps(o["temperature_by_options"]),
                o["fitter_report"]["n_eval"], ", ".join("%s %.4f → %.4f" % (k, v["raw"], v["T"]) for k, v in lf.items())))
        md += ["", "| fit | scored on | split | ECE as-shipped → (i) [95% CI] / (ii) | NLL as-shipped → (i) / (ii) | mean conf → (i) | accuracy |",
               "|---|---|---|---|---|---|---|"]
        for g, f in e2["fits"].items():
            for s, by in f["eval"].items():
                for sp in ("test", "dev"):
                    b, o, lw = by[sp]["as-shipped"], by[sp]["official"], by[sp]["lowfloor"]
                    md.append("| %s | %s | %s | %.3f → %.3f [%.3f, %.3f] / %.3f | %.3f → %.3f / %.3f | %.3f → %.3f | %.3f |" % (
                        g, s, sp, b["ece"], o["ece"], *o["ece_ci"], lw["ece"], b["nll"], o["nll"], lw["nll"], b["mean_conf"], o["mean_conf"], o["accuracy"]))
        cols = [(s, sp) for s in e2["sweep"] for sp in ("dev", "test")]
        md += ["", "ECE / NLL with one choice temperature T (sensitivity; the fitted T values are in the table above):", "",
               "| T | " + " | ".join("%s %s" % c for c in cols) + " |", "|---|" + "---|" * len(cols)]
        for i, T in enumerate(SWEEP):
            md.append("| %.1f | " % T + " | ".join("%.3f / %.3f" % (e2["sweep"][s][sp][i]["ece"], e2["sweep"][s][sp][i]["nll"]) for s, sp in cols) + " |")
    for s, conds in res.get("e3", {}).items():
        names = list(conds)
        md += ["", "## E3 %s: test coverage / covered accuracy by gate T" % s, "",
               "| T | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
        for i, T in enumerate(GRID):
            md.append("| %.2f | " % T + " | ".join("%.3f / %s" % (conds[c]["curve_test"][i]["coverage"], f3(conds[c]["curve_test"][i]["accuracy"]))
                                                     for c in names) + " |")
        md += ["", "| condition | budget | T chosen on dev | dev cov / err | test cov / err | test oracle max cov (T) | per-label T: dev cov / err | test cov / err |",
               "|---|---|---|---|---|---|---|---|"]
        for c in names:
            for b in map(str, BUDGETS):
                dc, orc, pl = conds[c]["dev_chosen"][b], conds[c]["oracle_test"][b], conds[c]["per_label"][b]
                md.append("| %s | %s | %s | %s | %s | %.3f (%s) | %s | %s |" % (
                    c, b, f3(dc["T"]) if dc["T"] is None else "%.4f" % dc["T"], ce(dc["dev"]), ce(dc["test"]),
                    orc["coverage"], "-" if orc["T"] is None else "%.4f" % orc["T"], ce(pl["dev"]), ce(pl["test"])))
        md += ["", "Per-label T chosen on dev (None = always FALLBACK; dev predicted n in brackets):", ""]
        for c in names:
            for b in map(str, BUDGETS):
                pl = conds[c]["per_label"][b]
                md.append("- %s, budget %s: " % (c, b) + ", ".join("%s %s [%d]" % (lab, "None" if T is None else "%.4f" % T, pl["n_dev_pred"][lab])
                                                                   for lab, T in pl["T"].items()))
        rk = res["e3_ranking"][s]
        md += ["", "| refit | AUROC(answer_confidence → correct) as-shipped → refit | discordant row pairs (unrounded max p) | distinct answer_confidence values as-shipped → refit |",
               "|---|---|---|---|"]
        md += ["| %s | %.4f → %.4f | %.4f | %d → %d |" % (g, v["auroc_before"], v["auroc_after"], v["discordant"], v["distinct_before"], v["distinct_after"])
               for g, v in rk.items()]
    if "e4" in res:
        v = res["e4"]
        md += ["", "## E4 payload", "", "- `%s` sha256 %s, fit `%s` official map" % (v["payload"], v["payload_sha256"], res["run_card"]["payload_fit"]),
               "- %s test half: ECE via laya.load(calibration=) %.4f vs E2 after %.4f, |Δ| %.5f, pass ±0.005 = %s" % (
                   v["set"], v["ece_reloaded"], v["ece_e2_after"], v["abs_diff"], v["pass_within_0.005"]),
               "- max |Δ answer_confidence| reloaded vs records: %.5f" % v["max_abs_dconf_vs_records"],
               "- apply_calibration_payload on a fresh agent: identical answers = %s, max |Δp| = %.5f" % (
                   v["identical_answers_load_vs_apply"], v["max_abs_dp_load_vs_apply"])]
        for how in ("load_calibration", "apply_calibration_payload"):
            md.append("- %s: temperature %s, by_options %s, warnings: %s" % (how, v[how]["temperature"], v[how]["temperature_by_options"],
                                                                           v[how]["warnings"] or "none"))
    if "e6" in res:
        v = res["e6"]
        md += ["", "## E6 noul threshold (%s)" % v["qid"], "",
               "AUROC dev %.3f / test %.3f / all %.3f. always-no accuracy test %.3f. 2-choice variant accuracy test %.3f / all %.3f." % (
                   v["auroc"]["dev"], v["auroc"]["test"], v["auroc"]["all"], v["always_no"]["test"], v["choice_variant"]["test"], v["choice_variant"]["all"]),
               "", "| rule | threshold | dev acc | test acc | test predicted-positive rate (gold) | test precision | test recall | all acc |",
               "|---|---|---|---|---|---|---|---|"]
        for k, x in v["rules"].items():
            t = x["test"]
            md.append("| %s | %s | %.3f | %.3f | %.3f (%.3f) | %s | %.3f | %.3f |" % (
                k, f3(x["threshold"]) if x["threshold"] is None else "%.4f" % x["threshold"], x["dev"]["accuracy"], t["accuracy"],
                t["pos_rate"], t["gold_pos_rate"], f3(t["precision"]), t["recall"], x["all"]["accuracy"]))
        md += ["", "03 E6 acceptance (Youden): %s" % json.dumps(v["accept_03_E6"])]
    return "\n".join(md) + "\n"


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sets", default="", help="comma-separated JSONL files with choice questions to fit and score")
    ap.add_argument("--splits", default="results/B/B_splits.json")
    ap.add_argument("--manifest", default="data/evals/MANIFEST.json")
    ap.add_argument("--model", default="models/laya-multilingual")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--per-task", action="store_true")
    ap.add_argument("--pooled", action="store_true")
    ap.add_argument("--min-bucket-n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--payload-fit", help="fit written to --out-payload: a set name or 'pooled' (default: first set)")
    ap.add_argument("--out-payload")
    ap.add_argument("--reports", nargs="*", default=[], help="laya-evals reports: E1, and a T = 1 parity check of --sets")
    ap.add_argument("--noul-report", help="laya-evals report with a noul question (E6)")
    ap.add_argument("--out", required=True, help="results/E/<name>.json; the Markdown is written next to it")
    a = ap.parse_args(argv)
    torch.set_num_threads(10)          # project CPU convention (02/03): intra-op 10, inter-op 1
    torch.set_num_interop_threads(1)
    t_start = time.time()
    ref = json.loads(mx.resolve(a.splits).read_text())
    reports = [mx.load_report(p) for p in a.reports]
    for r in reports:
        want = ref["splits"][r["set"]]
        assert r["run_card"]["split_rows"] == {"dev": want["dev"], "test": want["test"]}, r["path"]
    res = {"run_card": {"tool": "scripts/calibrate_ko.py", "argv": ["scripts/calibrate_ko.py"] + (sys.argv[1:] if argv is None else list(argv)),
                        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "laya_version": laya.__version__,
                        "torch": torch.__version__, "threads": [torch.get_num_threads(), torch.get_num_interop_threads()],
                        "model": a.model, "model_realpath": os.path.realpath(a.model), "device": a.device,
                        "min_bucket_n": a.min_bucket_n, "seed": a.seed, "grid": GRID, "budgets": BUDGETS,
                        "reports": [r["run_card"] for r in reports]}}
    if reports:
        res["e1"] = e1(reports)
    if a.noul_report:
        res["e6"] = e6(mx.load_report(a.noul_report))
    if a.sets:
        sets = [load_set(p, ref, json.loads(mx.resolve(a.manifest).read_text())) for p in a.sets.split(",")]
        res["run_card"]["sets"] = [{k: s[k] for k in ("name", "path", "rule", "dataset_sha256", "questions_sha256")} |
                                   {"dev": s["split"].count("dev"), "test": s["split"].count("test")} for s in sets]
        t0 = time.time()
        agent = laya.load(a.model, device=a.device)
        shipped = {"temperature": list(agent.temperature), "temperature_by_options": dict(agent.temperature_by_options)}
        t1 = time.time()
        recs = collect(agent, sets)
        res["run_card"]["timing_s"] = {"load": t1 - t0, "records": time.time() - t1, "rows": len(recs)}
        part = {(s["name"], sp): [r for r in recs if r["set"] == s["name"] and r["split"] == sp] for s in sets for sp in ("dev", "test")}
        groups = {s["name"]: [s["name"]] for s in sets} if a.per_task else {}
        if a.pooled and len(sets) > 1:
            groups["pooled"] = [s["name"] for s in sets]
        fits = {g: fit([r for m in members for r in part[(m, "dev")]], a.min_bucket_n, a.seed) for g, members in groups.items()}
        scored = {(s["name"], sp, "as-shipped"): score(part[(s["name"], sp)], shipped) for s in sets for sp in ("dev", "test")}
        for g, f in fits.items():
            for form in ("official", "lowfloor"):
                scored.update({(s["name"], sp, "%s|%s" % (g, form)): score(part[(s["name"], sp)], f[form]) for s in sets for sp in ("dev", "test")})
            f["eval"] = {s["name"]: {sp: {"as-shipped": scored[(s["name"], sp, "as-shipped")]["m"],
                                          **{form: scored[(s["name"], sp, "%s|%s" % (g, form))]["m"] for form in ("official", "lowfloor")}}
                                     for sp in ("dev", "test")} for s in sets}
        parity = {}
        for r in reports:
            if r["set"] in {s["name"] for s in sets}:
                mine = [x for x in recs if x["set"] == r["set"]]
                sc = score(mine, shipped)
                assert [(c["row"], c["qid"]) for c in r["cases"]] == [(x["row"], x["qid"]) for x in mine]
                parity[r["set"]] = {"n": len(mine), "agree": int(sum(p == c["pred"] for p, c in zip(sc["pred"], r["cases"]))),
                                    "max_abs_dconf": float(np.abs(sc["conf"] - np.array([c["conf"] for c in r["cases"]])).max())}
        sweep = {s["name"]: {sp: [score(part[(s["name"], sp)], {"temperature": [T, 1.0, 1.0], "temperature_by_options": {}})["m"]
                                   for T in SWEEP] for sp in ("dev", "test")} for s in sets}
        res["e2"] = {"fits": fits, "parity_vs_report": parity, "sweep": sweep}
        res["e3"], res["e3_ranking"] = {}, {}
        for s in sets:
            n = s["name"]
            conds = {"as-shipped": "as-shipped", **{"refit:" + g: "%s|official" % g for g in fits}}
            res["e3"][n] = {c: coverage_block(scored[(n, "dev", key)], scored[(n, "test", key)]) for c, key in conds.items()}
            b, res["e3_ranking"][n] = scored[(n, "test", "as-shipped")], {}
            for g in fits:
                f = scored[(n, "test", "%s|official" % g)]
                res["e3_ranking"][n][g] = {"auroc_before": auroc(b["conf"], b["corr"]), "auroc_after": auroc(f["conf"], f["corr"]),
                                           "discordant": discordant(b["pmax"], f["pmax"]),
                                           "distinct_before": len(set(b["conf"])), "distinct_after": len(set(f["conf"]))}
        if a.out_payload:
            g = a.payload_fit or sets[0]["name"]
            res["run_card"]["payload_fit"] = g
            payload = cal.calibration_payload(fits[g]["official"]["temperature"], fits[g]["official"]["temperature_by_options"],
                                              model_id_or_path=agent.model_id_or_path, subfolder=agent.subfolder, config=agent.cfg)
            Path(a.out_payload).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out_payload).write_text(json.dumps(payload, indent=2) + "\n")   # Agent.save_calibration format
            del agent
            k = (sets[0]["name"], "test", "%s|official" % g)
            t2 = time.time()
            res["e4"] = e4(a, sets[0], scored[k]["m"]["ece"], scored[k]["conf"])
            res["run_card"]["timing_s"]["e4"] = time.time() - t2
        res["raw_records"] = [{"set": r["set"], "row": r["row"], "split": r["split"], "qid": r["qid"], "k": r["rec"][3],
                               "y": r["y"], "logits": [round(float(v), 6) for v in r["rec"][1]]} for r in recs]
    res["run_card"]["wall_s"] = time.time() - t_start
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(js(res), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if "e6" in res:
        out.with_name(out.stem + "_noul_threshold.json").write_text(
            json.dumps(js({"run_card": res["run_card"], "e6": res["e6"]}), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    out.with_suffix(".md").write_text(render(js(res)), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
