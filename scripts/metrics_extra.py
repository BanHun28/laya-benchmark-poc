#!/usr/bin/env python
"""Metrics laya-evals does not emit, computed from `laya-evals run --json` reports alone (03 §3.8, §4).

No model call; stdlib + numpy. A report's `cases[*]` keep `expected`, the full `answer` (probabilities /
noul) and `correct` (laya/evals.py:728-744). The dataset named in `config.dataset` is read to map cases
to rows (dev/test split, option order); its bytes must hash to `config.dataset_sha256`.

  summary  REPORT... [--bootstrap 1000 --seed 13]      acc (CI), macro-F1, Brier, ECE (CI), baselines, recall
  paired   A B [--split all dev test]                   exact McNemar, Δ (B−A) with Wald CI, argmax agreement
  parity   REF OTHER...                                 argmax agreement, max |Δp| over probabilities
  coverage REPORT [--grid 0.5:0.95:0.05] [--error-budget 0.05,0.10]
  majority REPORT
Common: [--split-rule auto|index|hash] [--out X.md] [--json X.json]

Split rule (Track B / PoC P1, 2026-10-02): `index` = data-row index parity in the dataset file (even → dev,
odd → test), used for the ko/en paired MASSIVE files whose rows are in the same id order; `hash` =
int(sha256(json.dumps(state, ensure_ascii=False, sort_keys=True)), 16) % 2 (0 → dev, 1 → test). `auto` picks
index for (ko|en)_massive_(domain_8|intent_20opt)* and hash otherwise. A dataset whose header has a
`# split: <name>` line is a pre-split copy and all of its rows are <name>.
"""
import argparse
import hashlib
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SPLITS = ("all", "dev", "test")
INDEX_SPLIT_FILES = re.compile(r"^(ko|en)_massive_(domain_8|intent_20opt)")
BINS = 15


# ---------------------------------------------------------------- loading
def state_key(state):
    return hashlib.sha256(json.dumps(state, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def read_dataset(path):
    """Same line rule as laya.evals.Dataset.from_jsonl: strip, skip blank and `#` lines."""
    rows, header = [], []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("#"):
            header.append(s)
        elif s:
            rows.append(json.loads(s))
    return rows, header


def row_splits(rows, header, rule, name):
    fixed = [h[len("# split:"):].split()[0] for h in header if h.startswith("# split:")]
    if fixed:
        return [fixed[0]] * len(rows), "pre-split copy (%s)" % fixed[0]
    if rule == "auto":
        rule = "index" if INDEX_SPLIT_FILES.match(name) else "hash"
    if rule == "index":
        return ["dev" if i % 2 == 0 else "test" for i in range(len(rows))], "index parity"
    return ["dev" if int(state_key(r["state"]), 16) % 2 == 0 else "test" for r in rows], "state sha256 % 2"


def resolve(path):
    p = Path(path)
    return p if p.is_absolute() or p.exists() else ROOT / p


def load_report(path, rule="auto"):
    rep = json.loads(Path(path).read_text(encoding="utf-8"))
    cfg = rep["config"]
    ds = resolve(cfg["dataset"])
    assert hashlib.sha256(ds.read_bytes()).hexdigest() == cfg["dataset_sha256"], "dataset bytes differ: %s" % ds
    rows, header = read_dataset(ds)
    splits, rule_used = row_splits(rows, header, rule, ds.name)
    cases, skipped, it = [], 0, iter(rep["cases"])
    for i, (row, sp) in enumerate(zip(rows, splits)):
        skey = state_key(row["state"])
        for qid, gold in row["expected"].items():
            c = next(it)
            assert c["qid"] == qid and c["expected"] == gold and c["tags"] == list(row.get("tags", [])), (path, i, qid)
            a = c["answer"]
            if a["type"] == "choice":
                pred, probs, opts = a["choice"], {k: float(v) for k, v in a["probabilities"].items()}, \
                    list(row["questions"][qid]["criteria"])
            elif a["type"] == "noul":
                gold = "true" if gold else "false"
                pred, probs, opts = ("true" if a["noul"] >= 0.5 else "false"), \
                    {"true": float(a["noul"]), "false": 1.0 - float(a["noul"])}, ["true", "false"]
            else:
                skipped += 1
                continue
            assert (pred == gold) == bool(c["correct"]), (path, i, qid)
            cases.append({"row": i, "split": sp, "qid": qid, "type": a["type"], "gold": gold, "pred": pred,
                          "correct": pred == gold, "conf": float(c["confidence"]), "probs": probs, "opts": opts,
                          "tags": c["tags"], "model": c.get("model"), "skey": skey})
    assert next(it, None) is None, "%s: more cases than dataset rows x questions" % path
    verify(rep, cases, skipped)
    model = cfg.get("model") or "router"
    return {"path": str(path), "rep": rep, "cases": cases, "set": ds.stem, "model": model,
            "label": "%s/%s" % (ds.stem, model), "rule": rule_used,
            "run_card": {"report": str(path), "dataset": cfg["dataset"], "laya_version": cfg.get("laya_version"),
                         "dataset_sha256": cfg["dataset_sha256"], "questions_sha256": cfg.get("questions_sha256"),
                         "revisions": cfg.get("revisions"), "model": cfg.get("model") or "router (auto)",
                         "device": cfg.get("device"), "batch_size": cfg.get("timing", {}).get("batch_size"),
                         "split_rule": rule_used, "rows": len(rows),
                         "split_rows": dict(Counter(splits))}}


def verify(rep, cases, skipped):
    """Self-check of the computation path: our numbers must equal the harness's own overall block."""
    ov = rep["overall"]
    for typ, key in (("choice", "choice_accuracy"), ("noul", "noul_accuracy")):
        sel = [c["correct"] for c in cases if c["type"] == typ]
        if sel:
            assert abs(sum(sel) / len(sel) - ov[key]) < 1e-12, (key, sum(sel) / len(sel), ov[key])
    conf = np.array([c["conf"] for c in cases])
    corr = np.array([c["correct"] for c in cases], float)
    assert abs(ece(conf, corr) - ov["ece"]) < 1e-9, ("ece", ece(conf, corr), ov["ece"])
    if not skipped:
        assert abs(conf.mean() - ov["mean_confidence"]) < 1e-9


# ---------------------------------------------------------------- statistics
def ece_bins(conf):
    """Bin index with laya.common.ece_score edges: [0, 1/15], then (lo, hi] (laya/common.py:651-661)."""
    return np.clip(np.searchsorted(np.linspace(0, 1, BINS + 1), conf, side="left") - 1, 0, BINS - 1)


def ece(conf, corr):
    b = ece_bins(conf)
    return float(np.abs(np.bincount(b, conf, BINS) - np.bincount(b, corr, BINS)).sum() / len(conf))


def boot_ci(conf, corr, n_boot, seed):
    """Percentile 95% CI of accuracy and ECE over `n_boot` case resamples (03 §3.6)."""
    n = len(conf)
    idx = np.random.default_rng(seed).integers(0, n, size=(n_boot, n))
    acc = corr[idx].mean(axis=1)
    off = (ece_bins(conf)[idx] + BINS * np.arange(n_boot)[:, None]).ravel()
    sums = [np.bincount(off, w[idx].ravel(), BINS * n_boot).reshape(n_boot, BINS) for w in (conf, corr)]
    e = np.abs(sums[0] - sums[1]).sum(axis=1) / n
    return [float(x) for x in np.percentile(acc, [2.5, 97.5])], [float(x) for x in np.percentile(e, [2.5, 97.5])]


def macro_f1(gold, pred, labels):
    f = []
    for lab in labels:
        tp = sum(g == lab and p == lab for g, p in zip(gold, pred))
        fp = sum(g != lab and p == lab for g, p in zip(gold, pred))
        fn = sum(g == lab and p != lab for g, p in zip(gold, pred))
        f.append(2 * tp / max(1, 2 * tp + fp + fn))  # research/scripts/bench_local.py:126-133
    return float(np.mean(f)) if f else None


def mcnemar_exact(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def group_metrics(cs, n_boot=0, seed=13):
    n = len(cs)
    conf = np.array([c["conf"] for c in cs])
    corr = np.array([c["correct"] for c in cs], float)
    gold, pred = [c["gold"] for c in cs], [c["pred"] for c in cs]
    gcount, pcount = Counter(gold), Counter(pred)
    maj_label, maj_n = max(sorted(gcount.items()), key=lambda kv: kv[1])
    first = Counter(c["opts"][0] for c in cs).most_common(1)[0][0]
    m = {"n": n, "accuracy": float(corr.mean()),
         "macro_f1_union": macro_f1(gold, pred, sorted(set(gold) | set(pred))),
         "macro_f1_gold": macro_f1(gold, pred, sorted(gcount)),
         "brier": float(np.mean([sum((c["probs"].get(o, 0.0) - (o == c["gold"])) ** 2
                                     for o in set(c["probs"]) | {c["gold"]}) for c in cs])),
         "ece": ece(conf, corr), "mean_confidence": float(conf.mean()),
         "acc_at_50_coverage": float(corr[np.argsort(-conf)[:max(1, n // 2)]].mean()),  # bench_local.py:148
         "majority": maj_n / n, "majority_label": maj_label,
         "random": float(np.mean([1.0 / len(c["opts"]) for c in cs]))}
    m["delta_vs_majority"] = m["accuracy"] - m["majority"]
    if n_boot:
        m["accuracy_ci"], m["ece_ci"] = boot_ci(conf, corr, n_boot, seed)
    m["recall"] = {g: [sum(c["correct"] for c in cs if c["gold"] == g), k] for g, k in sorted(gcount.items())}
    m["pred_counts"] = dict(pcount.most_common())
    # per row, so it also reads the shuffled 20-option rows: how often the row's first listed option is gold / chosen
    m["first_option"] = {"label": first, "gold_n": sum(c["gold"] == c["opts"][0] for c in cs),
                         "pred_n": sum(c["pred"] == c["opts"][0] for c in cs)}
    m["confusions_top5"] = [[g, p, k] for (g, p), k in
                            Counter((c["gold"], c["pred"]) for c in cs if not c["correct"]).most_common(5)]
    m["models"] = dict(Counter(c["model"] for c in cs))
    return m


def groups(r, splits=SPLITS):
    for qid in dict.fromkeys(c["qid"] for c in r["cases"]):
        for sp in splits:
            cs = [c for c in r["cases"] if c["qid"] == qid and (sp == "all" or c["split"] == sp)]
            if cs:
                yield qid, sp, cs


# ---------------------------------------------------------------- subcommands
def f3(x):
    return "-" if x is None else "%.3f" % x


def fp(x):
    return "%.4f" % x if x >= 0.001 else "%.1e" % x


def ci(m, key):
    lo, hi = m.get(key + "_ci", (None, None))
    return "%s [%s, %s]" % (f3(m[key]), f3(lo), f3(hi)) if lo is not None else f3(m[key])


def cmd_summary(reports, a):
    out = ["| set | model | qid | split | n | accuracy [95% CI] | macro-F1 ∪ | macro-F1 gold | Brier | ECE [95% CI] "
           "| mean conf | acc@50%cov | majority | random | Δ vs majority |", "|" + "---|" * 15]
    res, details = [], []
    for r in reports:
        for qid, sp, cs in groups(r):
            m = group_metrics(cs, a.bootstrap, a.seed)
            res.append({"report": r["path"], "set": r["set"], "model": r["model"], "qid": qid, "split": sp, **m})
            out.append("| %s | %s | %s | %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %+.3f |" % (
                r["set"], r["model"], qid, sp, m["n"], ci(m, "accuracy"), f3(m["macro_f1_union"]),
                f3(m["macro_f1_gold"]), f3(m["brier"]), ci(m, "ece"), f3(m["mean_confidence"]),
                f3(m["acc_at_50_coverage"]), f3(m["majority"]), f3(m["random"]), m["delta_vs_majority"]))
            if sp == "all":
                details += ["", "### %s / %s" % (r["label"], qid), "",
                            "- recall: " + ", ".join("%s %d/%d" % (g, *v) for g, v in m["recall"].items()),
                            "- predicted: " + ", ".join("%s %d" % kv for kv in m["pred_counts"].items()),
                            "- first listed option (most common: `%(label)s`): gold %(gold_n)d, predicted %(pred_n)d" % m["first_option"],
                            "- top confusions: " + ", ".join("%s→%s ×%d" % tuple(x) for x in m["confusions_top5"]),
                            "- answering model (cases): " + ", ".join("%s %d" % kv for kv in m["models"].items())]
    return out + ["", "## Per-class detail (split = all; dev/test in the JSON)"] + details, {"results": res}


def cmd_paired(reports, a):
    A, B = reports
    out = ["A = `%s`, B = `%s`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; "
           "95%% Wald CI for the paired difference; exact two-sided McNemar." % (A["path"], B["path"]), "",
           "| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    res = []
    for qid in dict.fromkeys(c["qid"] for c in A["cases"]):
        for sp in a.split:
            xa = [c for c in A["cases"] if c["qid"] == qid and (sp == "all" or c["split"] == sp)]
            xb = [c for c in B["cases"] if c["qid"] == qid and (sp == "all" or c["split"] == sp)]
            if not xa or not xb:
                continue
            assert len(xa) == len(xb), "%s/%s: %d vs %d cases" % (qid, sp, len(xa), len(xb))
            for x, y in zip(xa, xb):
                assert x["gold"] == y["gold"], (qid, sp, x["row"], y["row"])
                sa, sb = ([t for t in z["tags"] if t.startswith("scenario:")] for z in (x, y))
                assert not (sa and sb) or sa == sb, (qid, sp, x["row"], sa, sb)
            n = len(xa)
            b = sum(x["correct"] and not y["correct"] for x, y in zip(xa, xb))
            c = sum(y["correct"] and not x["correct"] for x, y in zip(xa, xb))
            d, se = (c - b) / n, math.sqrt(max(b + c - (c - b) ** 2 / n, 0.0)) / n
            m = {"qid": qid, "split": sp, "n": n, "acc_a": sum(x["correct"] for x in xa) / n,
                 "acc_b": sum(y["correct"] for y in xb) / n, "delta": d, "delta_ci": [d - 1.96 * se, d + 1.96 * se],
                 "b": b, "c": c, "p": mcnemar_exact(b, c),
                 "agreement": sum(x["pred"] == y["pred"] for x, y in zip(xa, xb)) / n,
                 "same_state": sum(x["skey"] == y["skey"] for x, y in zip(xa, xb)) / n}
            res.append(m)
            out.append("| %s | %s | %d | %.3f | %.3f | %+.3f [%+.3f, %+.3f] | %d | %d | %s | %.3f | %.2f |" % (
                qid, sp, n, m["acc_a"], m["acc_b"], d, *m["delta_ci"], b, c, fp(m["p"]), m["agreement"], m["same_state"]))
    return out, {"a": A["path"], "b": B["path"], "results": res}


def cmd_parity(reports, a):
    ref = reports[0]
    out = ["Reference `%s`. Δp over every option probability (noul: p(true))." % ref["path"], "",
           "| other | n | argmax agreement | flips | max abs Δp | mean abs Δ answer_confidence |", "|---|---|---|---|---|---|"]
    res = []
    for o in reports[1:]:
        assert len(o["cases"]) == len(ref["cases"])
        for x, y in zip(ref["cases"], o["cases"]):
            assert x["qid"] == y["qid"] and x["gold"] == y["gold"]
        agree = sum(x["pred"] == y["pred"] for x, y in zip(ref["cases"], o["cases"]))
        dp = max(abs(x["probs"].get(k, 0.0) - y["probs"].get(k, 0.0)) for x, y in zip(ref["cases"], o["cases"])
                 for k in set(x["probs"]) | set(y["probs"]))
        dc = float(np.mean([abs(x["conf"] - y["conf"]) for x, y in zip(ref["cases"], o["cases"])]))
        n = len(ref["cases"])
        res.append({"other": o["path"], "n": n, "agreement": agree / n, "flips": n - agree, "max_abs_dp": dp,
                    "mean_abs_dconf": dc})
        out.append("| %s | %d | %.4f | %d | %.4f | %.4f |" % (o["path"], n, agree / n, n - agree, dp, dc))
    return out, {"reference": ref["path"], "results": res}


def coverage_table(cs, grid, budgets):
    conf = np.array([c["conf"] for c in cs])
    corr = np.array([c["correct"] for c in cs], float)
    n = len(cs)
    curve = [{"T": t, "coverage": float((conf >= t).mean()), "n": int((conf >= t).sum()),
              "accuracy": float(corr[conf >= t].mean()) if (conf >= t).any() else None} for t in grid]
    order = np.argsort(-conf, kind="stable")
    sc, cum = conf[order], np.cumsum(corr[order])
    ends = [i for i in range(n) if i == n - 1 or sc[i + 1] < sc[i]]  # a threshold cannot split tied confidences
    best = {}
    for bud in budgets:
        ok = [i for i in ends if 1 - cum[i] / (i + 1) <= bud + 1e-12]
        i = max(ok) if ok else None
        best[str(bud)] = {"coverage": (i + 1) / n, "T": float(sc[i]), "n": i + 1, "accuracy": float(cum[i] / (i + 1))} \
            if ok else {"coverage": 0.0, "T": None, "n": 0, "accuracy": None}
    return curve, best


def cmd_coverage(reports, a):
    lo, hi, step = (float(x) for x in a.grid.split(":"))
    grid = [round(t, 4) for t in np.arange(lo, hi + step / 2, step)]
    budgets = [float(x) for x in a.error_budget.split(",")]
    out, res = [], []
    for r in reports:
        for qid, sp, cs in groups(r):
            curve, best = coverage_table(cs, grid, budgets)
            res.append({"report": r["path"], "qid": qid, "split": sp, "curve": curve, "max_coverage": best})
            out += ["", "### %s / %s / %s (n=%d)" % (r["label"], qid, sp, len(cs)), "",
                    "| T | coverage | n covered | covered accuracy |", "|---|---|---|---|"]
            out += ["| %.2f | %.3f | %d | %s |" % (x["T"], x["coverage"], x["n"], f3(x["accuracy"])) for x in curve]
            out += [""] + ["- error ≤ %s: max coverage %.3f (n=%d) at T = %s, covered accuracy %s" % (
                bud, v["coverage"], v["n"], f3(v["T"]), f3(v["accuracy"])) for bud, v in best.items()]
    return out, {"results": res}


def cmd_majority(reports, a):
    out = ["| set | qid | split | n | label distribution | majority | random |", "|---|---|---|---|---|---|---|"]
    res = []
    for r in reports:
        for qid, sp, cs in groups(r):
            dist = dict(Counter(c["gold"] for c in cs).most_common())
            m = group_metrics(cs)
            res.append({"report": r["path"], "qid": qid, "split": sp, "n": len(cs), "distribution": dist,
                        "majority": m["majority"], "majority_label": m["majority_label"], "random": m["random"]})
            out.append("| %s | %s | %s | %d | %s | %.3f (%s) | %.3f |" % (
                r["set"], qid, sp, len(cs), ", ".join("%s %d" % kv for kv in dist.items()), m["majority"],
                m["majority_label"], m["random"]))
    return out, {"results": res}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--split-rule", choices=("auto", "index", "hash"), default="auto")
    common.add_argument("--out", help="Markdown output (default stdout)")
    common.add_argument("--json", help="JSON output")
    s = sub.add_parser("summary", parents=[common])
    s.add_argument("reports", nargs="+")
    s.add_argument("--bootstrap", type=int, default=1000)
    s.add_argument("--seed", type=int, default=13)
    s = sub.add_parser("paired", parents=[common])
    s.add_argument("reports", nargs=2)
    s.add_argument("--split", nargs="+", choices=SPLITS, default=list(SPLITS))
    s = sub.add_parser("parity", parents=[common])
    s.add_argument("reports", nargs="+")
    s = sub.add_parser("coverage", parents=[common])
    s.add_argument("reports", nargs="+")
    s.add_argument("--grid", default="0.5:0.95:0.05")
    s.add_argument("--error-budget", default="0.05,0.10")
    s = sub.add_parser("majority", parents=[common])
    s.add_argument("reports", nargs="+")
    a = ap.parse_args(argv)
    reports = [load_report(p, a.split_rule) for p in a.reports]
    lines, payload = globals()["cmd_" + a.cmd](reports, a)
    card = {"tool": "scripts/metrics_extra.py", "argv": sys.argv[1:] if argv is None else list(argv),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "reports": [r["run_card"] for r in reports]}
    md = ["# metrics_extra %s" % a.cmd, "", "`%s` (%s)" % (" ".join(["scripts/metrics_extra.py"] + card["argv"]),
                                                          card["generated_at"]), ""] + lines
    md += ["", "## run_card", "", "| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |",
           "|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %s | %s | %s | %s | %s | %s |" % (
        c["report"], c["model"], c["laya_version"], c["dataset_sha256"], c["questions_sha256"],
        json.dumps(c["revisions"]), c["split_rule"], json.dumps(c["split_rows"])) for c in card["reports"]]
    text = "\n".join(md) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    if a.json:
        Path(a.json).write_text(json.dumps({"run_card": card, **payload}, ensure_ascii=False, indent=1) + "\n",
                                encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
