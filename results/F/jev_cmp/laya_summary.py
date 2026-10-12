# Contains code derived from research/scripts/bench_local.py of Laya (https://github.com/NandhaKishorM/laya) at commit
# 4aa6761, Apache License 2.0. Modified by this project: ece_score, macro_f1, metrics (:114-148) and the Part B soft
# metrics (:276-302) are applied to the probabilities stored in laya-evals reports.
"""S0 Laya summary over every results/F/jev_cmp/laya/*.json laya-evals report (docs/09_laya_vs_jev_plan.md §5, §7 S0).

    source env.sh && .venv/bin/python results/F/jev_cmp/laya_summary.py

1. scripts/metrics_extra.py summary over the reports it reads -> laya/metrics_extra_summary.{md,json} (bootstrap CIs,
   per-class detail). It scores choice/noul answers only and skips score answers (scripts/metrics_extra.py:93-95),
   so the score-only T6 reports are left out of it (its verify() then has no `ece` to compare).
2. A port of research/scripts/bench_local.py `metrics` (:114-148) over every decision, score included, on the
   probabilities laya-evals stored per case; T1 adds Part B's soft accuracy / Brier vs soft / score MAE (:276-302)
   against results/F/jev_cmp/t1_gold_dists.json. Choice/noul numbers are asserted equal to step 1's.
   noul is scored as laya-evals does (p(true) >= 0.5), which differs from argmax only at exactly 0.5.
3. Router routing, determinism (T1 english vs its rerun), the T2 option-order probe, state truncation per checkpoint.
4. T1 again on the 120 Jev-comparable decisions (rows marked `jev.<qid>.jev_excluded`: options > 80 chars, score
   questions without 5 levels), the noul criteria on/off pair (T1 vs T1_typed_decisions_40_noulnocrit, McNemar), and
   the archived T4 v0 (`key: key spaced` options) against the key-only T4, paired on the same rows.
-> results/F/jev_cmp/laya_summary.md and .json
"""
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from metrics_extra import mcnemar_exact, read_dataset  # noqa: E402

HERE = ROOT / "results/F/jev_cmp"
LAYA = HERE / "laya"
GOLD = HERE / "t1_gold_dists.json"
CHECKS = HERE / "checks"
MODELS = ("english", "multilingual", "router", "typed-decisions")
CKPT = {"english": ("laya", 512, 192), "multilingual": ("laya-multilingual", 1024, 256),
        "typed-decisions": ("laya-typed-decisions", 1024, 256)}
# Published Laya numbers: (english, multilingual, typed-decisions, source). n differs from ours (40).
UPSTREAM = {
    "T1": ("0.362", "0.352", "0.766 (fine-tuned)", "BENCHMARKS.md:172-174 (2,000 decisions); Jev 0.727 (:175)"),
    "T2": ("0.947 (T4) or 0.950 (apps)", "0.937 or 0.930", "0.953", "README.md:1352 T4 N=600, BENCHMARKS.md:160 apps N=400; "
                                                                    "Jev 0.910"),
    "T3": ("0.573 (T4) or 0.595 (apps)", "0.513 or 0.530", "0.600", "README.md:1354, BENCHMARKS.md:161; Jev 0.480"),
    "T4": ("(0.425 @77 opt)", "(0.425 @77 opt)", "(0.492 @77 opt)", "BENCHMARKS.md:162, 77 options: not comparable; Jev 0.870 @72"),
    "T5": ("0.830", "0.787", "-", "README.md:1353 (N=600)"),
    "T6": ("0.372", "0.282", "-", "README.md:1356 (argmax level, N=600)"),
    "T8": ("0.698", "0.578", "-", "README.md:1355 (n=116)"),
}
# MASSIVE intent, 20 options: T4 notebook (300/lang, research/results/t4_colab_benchmark.json) and CPU sweep
# (100/lang, BENCHMARKS.md:71-117). Ours is 10 options, 20 ids: direction only.
MASSIVE20 = {"en": ("0.783", "0.657", "0.820", "0.710"), "de": ("0.420", "0.467", "0.420", "0.500"),
             "ja": ("0.547", "0.587", "0.530", "0.640"), "zh-CN": ("0.593", "0.607", "0.620", "0.650"),
             "ko": ("0.103", "0.490", "0.110", "0.470")}


def wilson(k, n, z=1.96):
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def ece_score(conf, corr, bins=15):  # bench_local.py:114-123
    conf, corr = np.asarray(conf, float), np.asarray(corr, float)
    e, edges = 0.0, np.linspace(0, 1, bins + 1)
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        s = (conf >= lo if i == 0 else conf > lo) & (conf <= hi)
        if s.any():
            e += s.mean() * abs(conf[s].mean() - corr[s].mean())
    return float(e)


def macro_f1(g, p):  # bench_local.py:126-133
    f = []
    for c in sorted(set(g) | set(p)):
        tp = sum(x == c and y == c for x, y in zip(g, p))
        fp = sum(x != c and y == c for x, y in zip(g, p))
        fn = sum(x == c and y != c for x, y in zip(g, p))
        f.append(2 * tp / max(1, 2 * tp + fp + fn))
    return float(np.mean(f))


def metrics(ds):
    """bench_local.py:136-148 on decisions. Correctness and macro-F1 use labels (T4/T7 shuffle options per row, so an
    option index is not a class); Brier/NLL use the gold index; confidence is the stored answer_confidence (= max p)."""
    g, p = [d["gold"] for d in ds], [d["pred"] for d in ds]
    corr = np.array([a == b for a, b in zip(g, p)], float)
    conf = np.array([d["conf"] for d in ds])
    k = int(corr.sum())
    return {"n": len(ds), "correct": k, "accuracy": k / len(ds), "wilson": wilson(k, len(ds)),
            "macro_f1": macro_f1(g, p) if len({d["type"] for d in ds}) == 1 else None,  # T1 pools str/bool/int labels
            "ece": ece_score(conf, corr),
            "brier": float(np.mean([((np.asarray(d["p"]) - np.eye(len(d["p"]))[d["gi"]]) ** 2).sum() for d in ds])),
            "nll": float(np.mean([-math.log(max(float(d["p"][d["gi"]]), 1e-12)) for d in ds])),
            "mean_confidence": float(conf.mean()),
            "acc_at_50_coverage": float(corr[np.argsort(-conf, kind="stable")[:max(1, len(conf) // 2)]].mean())}


def decisions(path):
    """Report cases mapped to dataset rows (row-major, expected-qid order, as laya/evals.py evaluate writes them)."""
    rep = json.loads(path.read_text(encoding="utf-8"))
    rows, _ = read_dataset(ROOT / rep["config"]["dataset"])
    it, out = iter(rep["cases"]), []
    for i, row in enumerate(rows):
        for qid, gold in row["expected"].items():
            c = next(it)
            assert c["qid"] == qid and c["expected"] == gold, (path, i, qid)
            a, q = c["answer"], row["questions"][qid]
            if a["type"] == "choice":
                keys = list(q["criteria"])
                p, gi, pi, pred = [a["probabilities"][k] for k in keys], keys.index(gold), keys.index(a["choice"]), a["choice"]
            elif a["type"] == "noul":
                p, gi, pred = [1 - a["noul"], a["noul"]], int(gold), a["noul"] >= 0.5
                pi = int(pred)
            else:
                p = [a["probabilities"][str(k)] for k in range(len(q["criteria"]))]
                gi, pi = gold, int(np.argmax(p))
                pred = pi
            out.append({"row": i, "qid": qid, "type": a["type"], "gold": gold, "pred": pred, "gi": gi, "pi": pi, "p": p,
                        "conf": float(c["confidence"]), "score": a.get("score"), "model": c.get("model"),
                        "jev_excluded": bool(row.get("jev", {}).get(qid, {}).get("jev_excluded")),
                        "workflow": next((t[9:] for t in row["tags"] if t.startswith("workflow:")), None)})
    assert next(it, None) is None, path
    return rep, out


def t1_extra(ds, gold):
    """Part B soft metrics (bench_local.py:276-302) plus accuracy against the dataset's own `label`."""
    soft, brier_s, mae, w1, by_wf, by_qt, lab = [], [], [], [], defaultdict(list), defaultdict(list), []
    for d, g in zip(ds, gold):
        assert (d["row"], d["qid"]) == (g["row"], g["qid"]) and d["gi"] == g["argmax_idx"]
        p = np.asarray(d["p"], float)
        gp = np.asarray(g["soft"], float)
        gp, pp = gp / gp.sum(), p / max(p.sum(), 1e-12)
        soft.append(float((pp * gp).sum()))
        brier_s.append(float(((pp - gp) ** 2).sum()))
        if "gold_score" in g:
            e = float((np.arange(len(p)) * p).sum())
            mae.append(abs(e - g["gold_score"]))
            w1.append(float(abs(e - g["gold_score"]) <= 1))
        by_wf[d["workflow"]].append(d)
        by_qt[d["type"]].append(d)
        lab.append(d["pi"] == g["label_idx"])
    def majority(key):  # in-sample gold majority rate pooled over the groups `key` defines
        groups = defaultdict(Counter)
        for g in gold:
            groups[key(g)][json.dumps(g["expected"])] += 1
        return sum(max(c.values()) for c in groups.values()) / len(gold)
    return {"soft_accuracy": float(np.mean(soft)), "brier_vs_soft": float(np.mean(brier_s)),
            "score_mae": float(np.mean(mae)), "within_1_level": float(np.mean(w1)),
            "accuracy_vs_upstream_label": float(np.mean(lab)),
            # upstream's 0.461 is per qid with the shared qids (urgency, disposition) merged across workflows: the same
            # rule gives 0.4610 on the 2,000 test decisions; per (workflow, qid) gives 0.5225 there
            "per_question_majority": majority(lambda g: g["qid"]),
            "per_workflow_question_majority": majority(lambda g: (g["workflow"], g["qid"])),
            "by_workflow": {k: metrics(v)["accuracy"] for k, v in sorted(by_wf.items())},
            "by_question_type": {k: metrics(v)["accuracy"] for k, v in sorted(by_qt.items())}}


def truncation(sets):
    """Decisions whose state lost tokens to max_len per checkpoint (laya/common.py build_sequence)."""
    from transformers import AutoTokenizer
    from laya.agent import Agent
    from laya.common import build_sequence
    out = {}
    for name, (ckpt, max_len, head) in CKPT.items():
        tok = AutoTokenizer.from_pretrained(str(ROOT / "models" / ckpt / "tokenizer"))
        for s in sets:
            rows, _ = read_dataset(ROOT / "data/evals/jev_cmp" / (s + ".jsonl"))
            n = cut = 0
            dropped = []
            for r in rows:
                for q in r["questions"].values():
                    *_, st = build_sequence(tok, r["state"], Agent._to_internal(q), max_len, head, return_truncation_stats=True)
                    n += 1
                    cut += st["truncated"]
                    if st["truncated"]:
                        dropped.append(st["state_tokens_dropped"])
            out.setdefault(s, {})[name] = {"decisions": n, "truncated": cut, "max_tokens_dropped": max(dropped, default=0)}
    return out


def emotion_check():
    """T3 representativeness: the upstream en.emotion suite (first 600 test rows) and the whole test split on english,
    and the accuracy the T3 class mix would have under the whole-split per-class recall."""
    first = json.loads((CHECKS / "emotion_first600_english.json").read_text())
    full = json.loads((CHECKS / "emotion_test2000_english.json").read_text())
    rec, tot = Counter(), Counter()
    for c in full["cases"]:
        tot[c["expected"]] += 1
        rec[c["expected"]] += c["correct"]
    scored = lambda a: (a["choice"], a["probabilities"], a["answer_confidence"])  # noqa: E731
    by_id = {c["tags"][0]: c["answer"] for c in full["cases"]}
    ours = json.loads((LAYA / "T3_emotion_40_english.json").read_text())["cases"]
    rows, _ = read_dataset(ROOT / "data/evals/jev_cmp/T3_emotion_40.jsonl")
    ids = [next(t for t in r["tags"] if t.startswith("id:")) for r in rows]
    return {"first600_accuracy": first["overall"]["choice_accuracy"], "first600_ece": first["overall"]["ece"],
            "test2000_accuracy": full["overall"]["choice_accuracy"],
            "test2000_recall": {k: rec[k] / tot[k] for k in sorted(tot)},
            "t3_expected_under_test2000_recall": float(np.mean([rec[r["expected"]["emotion"]] / tot[r["expected"]["emotion"]]
                                                                for r in rows])),
            "t3_observed": float(np.mean([c["correct"] for c in ours])),
            "t3_scored_fields_identical_in_test2000_run": sum(scored(by_id[i]) == scored(c["answer"]) for i, c in zip(ids, ours)),
            "t3_answers_identical_in_test2000_run": sum(by_id[i] == c["answer"] for i, c in zip(ids, ours))}


def t4_v0_vs_v1():
    """Same 40 rows, options and option order; v0 rendered `key: key spaced`, v1 the key alone. Paired on rows."""
    out = {}
    for m in ("english", "multilingual", "router"):
        a = json.loads((LAYA / ("T4_banking77_10opt_40_v0_%s.json" % m)).read_text())["cases"]
        b = json.loads((LAYA / ("T4_banking77_10opt_40_%s.json" % m)).read_text())["cases"]
        assert [x["expected"].replace("_", " ") for x in a] == [x["expected"] for x in b]
        n01 = sum(x["correct"] and not y["correct"] for x, y in zip(a, b))
        n10 = sum(y["correct"] and not x["correct"] for x, y in zip(a, b))
        out[m] = {"v0": float(np.mean([x["correct"] for x in a])), "v1": float(np.mean([y["correct"] for y in b])),
                  "v0_only": n01, "v1_only": n10, "mcnemar_p": mcnemar_exact(n01, n10),
                  "same_choice": sum(x["answer"]["choice"].replace("_", " ") == y["answer"]["choice"] for x, y in zip(a, b))}
    return out


def noul_criteria():
    """T1's noul answers with their true/false criteria vs the noulnocrit variant, paired on (row, qid)."""
    rows, _ = read_dataset(ROOT / "data/evals/jev_cmp/T1_typed_decisions_40.jsonl")
    vrows, _ = read_dataset(ROOT / "data/evals/jev_cmp/T1_typed_decisions_40_noulnocrit.jsonl")
    out = {}
    for m in ("english", "multilingual"):
        _, a = decisions(LAYA / ("T1_typed_decisions_40_%s.json" % m))
        _, b = decisions(LAYA / ("T1_typed_decisions_40_noulnocrit_%s.json" % m))
        with_c = {(d["row"], d["qid"]): d for d in a if d["type"] == "noul"}
        res = {}
        for label, keep in (("all", lambda k: True), ("had_criteria", lambda k: bool(rows[k[0]]["questions"][k[1]].get("criteria"))),
                            ("never_had_criteria", lambda k: not rows[k[0]]["questions"][k[1]].get("criteria"))):
            pairs = [(with_c[(d["row"], d["qid"])], d) for d in b if keep((d["row"], d["qid"]))]
            assert all(rows[x["row"]]["state"] == vrows[y["row"]]["state"] for x, y in pairs)
            n01 = sum(x["pred"] == x["gold"] and y["pred"] != y["gold"] for x, y in pairs)
            n10 = sum(y["pred"] == y["gold"] and x["pred"] != x["gold"] for x, y in pairs)
            res[label] = {"n": len(pairs), "with": float(np.mean([x["pred"] == x["gold"] for x, _ in pairs])),
                          "without": float(np.mean([y["pred"] == y["gold"] for _, y in pairs])),
                          "with_only": n01, "without_only": n10, "mcnemar_p": mcnemar_exact(n01, n10),
                          "pred_true_with": sum(x["pred"] for x, _ in pairs), "pred_true_without": sum(y["pred"] for _, y in pairs),
                          "gold_true": sum(x["gold"] for x, _ in pairs),
                          "identical_p": sum(x["p"] == y["p"] for x, y in pairs)}
        out[m] = res
    return out


def f3(x):
    return "-" if x is None else "%.3f" % x


def main():
    reports = sorted(p for p in LAYA.glob("T*.json") if "_v0_" not in p.name)  # archived T4 v0: see t4_v0_vs_v1
    score_only = [p for p in reports if p.name.startswith("T6_")]
    me_md, me_json = LAYA / "metrics_extra_summary.md", LAYA / "metrics_extra_summary.json"
    cmd = [sys.executable, str(ROOT / "scripts/metrics_extra.py"), "summary",
           *[str(p.relative_to(ROOT)) for p in reports if p not in score_only], "--out", str(me_md), "--json", str(me_json)]
    subprocess.run(cmd, check=True, cwd=ROOT)
    me = {(Path(r["report"]).name, r["qid"]): r for r in json.loads(me_json.read_text())["results"] if r["split"] == "all"}

    gold = json.loads(GOLD.read_text(encoding="utf-8"))["decisions"]
    res, cross = {}, []
    for p in reports:
        rep, ds = decisions(p)
        set_, model = p.stem.rsplit("_", 1) if not p.stem.endswith("_rerun") else (p.stem[:-6].rsplit("_", 1)[0], "rerun")
        m = metrics(ds)
        m["answered_by"] = dict(Counter(d["model"] for d in ds))
        m["majority"] = Counter(d["gold"] for d in ds).most_common(1)[0][1] / len(ds) if len({d["qid"] for d in ds}) == 1 else None
        m["dataset_sha256"], m["questions_sha256"] = rep["config"]["dataset_sha256"], rep["config"]["questions_sha256"]
        m["revisions"] = rep["config"].get("revisions")
        if set_ == "T1_typed_decisions_40":
            m.update(t1_extra(ds, gold))
            m["majority"] = m["per_question_majority"]
            keep = [i for i, d in enumerate(ds) if not d["jev_excluded"]]
            m["jev_comparable"] = {**metrics([ds[i] for i in keep]), **t1_extra([ds[i] for i in keep], [gold[i] for i in keep])}
            m["jev_comparable"].update(majority=m["jev_comparable"]["per_question_majority"],
                                       answered_by=dict(Counter(ds[i]["model"] for i in keep)),
                                       by_type_metrics={t: metrics([ds[i] for i in keep if ds[i]["type"] == t])
                                                        for t in ("choice", "noul", "score")})
        if set_.startswith("T6_"):
            e = [abs(d["score"] - d["gold"]) for d in ds]
            m.update(score_mae=float(np.mean(e)), within_1_level=float(np.mean([x <= 1 for x in e])),
                     laya_evals_score_mae=rep["overall"]["score_mae"])
            assert abs(m["score_mae"] - rep["overall"]["score_mae"]) < 1e-9
        for qid in dict.fromkeys(d["qid"] for d in ds):  # step 1 vs step 2 on every choice/noul question
            x = me.get((p.name, qid))
            if x is None:
                continue
            sub = metrics([d for d in ds if d["qid"] == qid])
            ok = all(abs(sub[k] - x[k2]) < 1e-9 for k, k2 in (("accuracy", "accuracy"), ("macro_f1", "macro_f1_union"),
                                                                ("ece", "ece"), ("mean_confidence", "mean_confidence")))
            ok &= abs(sub["brier"] - x["brier"]) < 1e-9
            cross.append((p.name, qid, ok))
        res.setdefault(set_, {})[model] = m

    # determinism
    a = json.loads((LAYA / "T1_typed_decisions_40_english.json").read_text())
    b = json.loads((LAYA / "T1_typed_decisions_40_english_rerun.json").read_text())
    strip = lambda o: {k: v for k, v in o.items() if not k.endswith("_ms")}  # noqa: E731
    det = {"cases": len(a["cases"]), "answers_identical": [c["answer"] for c in a["cases"]] == [c["answer"] for c in b["cases"]],
           "overall_identical_except_timing": strip(a["overall"]) == strip(b["overall"])}
    probes = {}
    for m in ("english", "multilingual"):
        pr = json.loads((HERE / ("T2_option_order_k1_%s.json" % m)).read_text())
        s = pr["sets"][0]
        probes[m] = {**{k: s["metrics"][k] for k in ("n_items", "n_options", "orig_accuracy", "flip_rate_per_perm",
                                                      "flip_rate_per_perm_ci", "perm_accuracy_mean", "identity_permutations",
                                                      "mean_abs_delta_answer_confidence")},
                     "parity": s.get("reference_parity"), "warnings": pr["run_card"]["warnings"],
                     "threads": pr["run_card"]["threads_intra_inter"], "seconds": s["seconds"]}
    trunc = truncation(sorted(res))
    emo = emotion_check()
    t4 = t4_v0_vs_v1()
    noul = noul_criteria()

    L = ["# S0 Laya summary — jev_cmp sets (2026-10-06)", "",
         "`.venv/bin/python results/F/jev_cmp/laya_summary.py`. CPU fp32, intra-op 10 / inter-op 1, `--batch-size 8`. "
         "accuracy = argmax (noul: p(true) >= 0.5) with Wilson 95%% CI; macro-F1 over gold ∪ pred; Brier = Σ(p − onehot)²; "
         "ECE 15 bins on max p (= answer_confidence); majority = gold majority rate (T1: per-(workflow, question) majority). "
         "Choice/noul values equal `scripts/metrics_extra.py summary` (cross-check %d/%d questions; bootstrap CIs and per-class "
         "detail in `laya/metrics_extra_summary.md`). Score questions (T6, T1) come from the bench_local port only. "
         "n=40 (T7: 20 per language), so a 95%% CI is about ±0.15." % (sum(ok for *_, ok in cross), len(cross)), "",
         "## 1. Accuracy by set and checkpoint", "",
         "| set | in training mix | model (answered by) | n | accuracy [Wilson 95%] | macro-F1 | Brier | ECE | mean conf | majority "
         "| Δ vs majority | upstream published (english / multilingual / typed-decisions) |", "|" + "---|" * 12]
    manifest = json.loads((ROOT / "data/evals/jev_cmp/MANIFEST.json").read_text())["files"]
    for s in sorted(res):
        up = None if s.endswith("_noulnocrit") else UPSTREAM.get(s[:2])
        for m in MODELS:
            if m not in res[s]:
                continue
            x = res[s][m]
            pub = ("%s / %s / %s (%s)" % up) if up else ("comparison-only variant, §2b" if s.endswith("_noulnocrit")
                                                           else "20-opt refs in §4")
            for label, y in ((s, x), ("%s, Jev-comparable" % s, x.get("jev_comparable"))):
                if y is None:
                    continue
                ans = ", ".join("%s %d" % kv for kv in y["answered_by"].items())
                L.append("| %s | %s | %s (%s) | %d | %d/%d = %.3f [%.3f, %.3f] | %s | %.3f | %.3f | %.3f | %s | %s | %s |" % (
                    label, manifest[s + ".jsonl"]["in_training_mix"], m, ans, y["n"], y["correct"], y["n"], y["accuracy"],
                    *y["wilson"], "-" if s.startswith("T1_") else f3(y["macro_f1"]), y["brier"], y["ece"], y["mean_confidence"],
                    f3(y["majority"]), "-" if y["majority"] is None else "%+.3f" % (y["accuracy"] - y["majority"]), pub))
    t1 = res["T1_typed_decisions_40"]
    L += ["", "## 2. T1 typed-decisions (40 cases / 200 decisions, Part B metrics)", "",
          "Upstream (BENCHMARKS.md:170-178, 2,000 decisions): english 0.362 / soft 0.332 / Brier 0.316 / ECE 0.175 / MAE 0.694; "
          "multilingual 0.352 / 0.328 / 0.463 / 0.314 / 0.760; laya-typed-decisions 0.766 / 0.471 / 0.061 / 0.213 / 0.242 "
          "(fine-tuned on typed-decisions train, not zero-shot); Jev 1.13.0 published 0.727 / 0.580 / 0.148 / 0.144 / 0.391; "
          "majority 0.461. Brier here is Part B's `brier_vs_soft`; score MAE is |E[level] − teacher score|.", "",
          "| model | accuracy (vs argmax gold) | accuracy (vs dataset `label`, upstream's) | soft acc | Brier vs soft | ECE "
          "| score MAE | within 1 level | choice / noul / score acc | majority per qid (upstream rule) / per (workflow, qid) |",
          "|" + "---|" * 10]
    for m in MODELS:
        if m in t1:
            x = t1[m]
            qt = x["by_question_type"]
            L.append("| %s | %.3f [%.3f, %.3f] | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f / %.3f / %.3f | %.3f / %.3f |" % (
                m, x["accuracy"], *x["wilson"], x["accuracy_vs_upstream_label"], x["soft_accuracy"], x["brier_vs_soft"], x["ece"],
                x["score_mae"], x["within_1_level"], qt["choice"], qt["noul"], qt["score"], x["per_question_majority"],
                x["per_workflow_question_majority"]))
    L += ["", "Jev-comparable decisions only (120 = choice 50 + noul 60 + 5-level score 10; excluded: the 70 4-level score "
          "decisions, since the playground's Score takes 5 levels, and customer_service/action, whose options reach 87-89 chars "
          "> the 80-char choice input; `jev_comparable_n` in MANIFEST). Wilson 95% CIs; Brier (one-hot) is against the argmax "
          "gold, Brier vs soft against the teacher distribution; score MAE over the 10 five-level decisions:", "",
          "| model | all 120 | choice (50) | noul (60) | score, 5 levels (10) | soft acc | Brier vs soft | Brier (one-hot) "
          "| score MAE | majority per qid |", "|" + "---|" * 10]
    cell = lambda y: "%d/%d = %.3f [%.3f, %.3f]" % (y["correct"], y["n"], y["accuracy"], *y["wilson"])  # noqa: E731
    for m in MODELS:
        if m in t1:
            x = t1[m]["jev_comparable"]
            bt = x["by_type_metrics"]
            L.append("| %s | %s | %s | %s | %s | %.3f | %.3f | %.3f | %.3f | %.3f |" % (
                m, cell(x), cell(bt["choice"]), cell(bt["noul"]), cell(bt["score"]), x["soft_accuracy"], x["brier_vs_soft"],
                x["brier"], x["score_mae"], x["per_question_majority"]))
    L += ["", "## 2b. T1 noul with and without true/false criteria (playground Boolean has no description field)", "",
          "`T1_typed_decisions_40_noulnocrit.jsonl` = the 60 noul questions with `criteria` removed (20 of them, duplicate and "
          "credential_compromise, never had any: same input, so their answers must match). Paired on (row, question); "
          "with only / without only = right in one condition and wrong in the other; exact McNemar.", "",
          "| model | decisions | accuracy with criteria | without | with only / without only | McNemar p | predicted true with / without (gold true) | identical p(true) |",
          "|---|---|---|---|---|---|---|---|"]
    for m, by_subset in noul.items():
        for label, x in by_subset.items():
            L.append("| %s | %s (%d) | %.3f | %.3f | %d / %d | %.4f | %d / %d (%d) | %d/%d |" % (
                m, label.replace("_", " "), x["n"], x["with"], x["without"], x["with_only"], x["without_only"], x["mcnemar_p"],
                x["pred_true_with"], x["pred_true_without"], x["gold_true"], x["identical_p"], x["n"]))
    L += ["", "| model | " + " | ".join(sorted(t1["english"]["by_workflow"])) + " |", "|---|---|---|---|---|"]
    L += ["| %s | %s |" % (m, " | ".join("%.3f" % v for _, v in sorted(t1[m]["by_workflow"].items()))) for m in MODELS if m in t1]
    t6 = res["T6_sst5_40"]
    L += ["", "## 3. T6 SST-5 (score, 5 levels)", "",
          "Upstream N=600 (research/results/t4_colab_benchmark.json `en.sst5`): english acc 0.372, MAE 0.905, within 1 0.632; "
          "multilingual 0.282, 1.359, 0.450.", "",
          "| model | accuracy (argmax level) | score MAE (laya-evals) | within 1 level |", "|---|---|---|---|"]
    L += ["| %s | %.3f [%.3f, %.3f] | %.3f | %.3f |" % (m, t6[m]["accuracy"], *t6[m]["wilson"], t6[m]["score_mae"],
                                                       t6[m]["within_1_level"]) for m in MODELS if m in t6]
    L += ["", "## 4. T7 MASSIVE intent, 10 options, same 20 ids per language", "",
          "Upstream is 20 options (random 0.05; ours 0.10): T4 notebook 300/lang and CPU sweep 100/lang, english / multilingual.", "",
          "| lang | english | multilingual | router (answered by) | upstream 20-opt T4 | upstream 20-opt CPU sweep |", "|---|---|---|---|---|---|"]
    for lang in ("en", "de", "ja", "zh-CN", "ko"):
        x = res["T7_massive_intent_10opt_%s_20" % lang]
        u = MASSIVE20[lang]
        L.append("| %s | %d/20 = %.2f | %d/20 = %.2f | %d/20 = %.2f (%s) | %s / %s | %s / %s |" % (
            lang, x["english"]["correct"], x["english"]["accuracy"], x["multilingual"]["correct"], x["multilingual"]["accuracy"],
            x["router"]["correct"], x["router"]["accuracy"], ", ".join(x["router"]["answered_by"]), *u))
    L += ["", "## 4b. T4 option rendering: archived v0 vs key-only (same 40 rows, options and option order)", "",
          "v0 (`T4_banking77_10opt_40_v0.jsonl`, sha256 df700caa…) rendered each option `key: key spaced`, up to 98 chars; "
          "the key-only rebuild (coordinator decision (b)) is upstream's rendering (bench_apps.py:120-122), max 48 chars. "
          "v0 reports are kept as `laya/T4_banking77_10opt_40_v0_<model>.json`.", "",
          "| model | v0 accuracy | key-only accuracy | right only in v0 / only in key-only | exact McNemar p | same choice |",
          "|---|---|---|---|---|---|"]
    L += ["| %s | %.3f | %.3f | %d / %d | %.4f | %d/40 |" % (m, x["v0"], x["v1"], x["v0_only"], x["v1_only"], x["mcnemar_p"],
                                                          x["same_choice"]) for m, x in t4.items()]
    L += ["", "## 5. Determinism, option order, truncation", "",
          "- Determinism (T1 english run twice, %d decisions): answers identical %s, overall identical except timing %s." % (
              det["cases"], det["answers_identical"], det["overall_identical_except_timing"]),
          "- Option-order probe, T2 AG News, 1 permutation per item (`scripts/probe_option_order.py`, upstream method "
          "build_benchmark_nb.py:640-678; upstream refs 20-opt en 0.150 / 0.230, emotion 0.040 / 0.090, Jev 0.13):", "",
          "| checkpoint | n | options | orig acc | per-perm flip [95% CI] | perm acc | identity perms | mean |Δ conf| | parity vs laya-evals report |",
          "|---|---|---|---|---|---|---|---|---|"]
    for m, x in probes.items():
        par = x["parity"]
        L.append("| %s | %d | %d | %.3f | %.3f [%.3f, %.3f] | %.3f | %d | %.3f | %s |" % (
            m, x["n_items"], x["n_options"], x["orig_accuracy"], x["flip_rate_per_perm"], *x["flip_rate_per_perm_ci"],
            x["perm_accuracy_mean"], x["identity_permutations"], x["mean_abs_delta_answer_confidence"],
            "%d/%d argmax, max |Δp| %.4f" % (par["argmax_agreement"], par["n"], par["max_abs_dp"]) if par else "-"))
    L += ["", "State truncation (decisions whose state lost tokens to `max_len`; Jev reads the whole state):", "",
          "| set | english (512) | multilingual (1024) | typed-decisions (1024) |", "|---|---|---|---|"]
    for s, v in trunc.items():
        L.append("| %s | %s |" % (s, " | ".join("%d/%d (max %d tok dropped)" % (v[c]["truncated"], v[c]["decisions"],
                                                                               v[c]["max_tokens_dropped"]) for c in CKPT)))
    L += ["", "## 6. Pipeline check against upstream, and T3 representativeness (english)", "",
          "- Upstream en.emotion suite (first 600 test rows, same question; `checks/emotion_first600.jsonl`): accuracy %.4f, "
          "ECE %.4f. Upstream T4 run: 0.5733, ECE 0.3238 (research/results/t4_colab_benchmark.json `en.emotion`), so this "
          "pipeline (laya-evals, CPU fp32, checkpoint 55cf4c4) reproduces the published number." % (
              emo["first600_accuracy"], emo["first600_ece"]),
          "- Whole test split (2,000 rows): accuracy %.4f; per-class recall %s." % (
              emo["test2000_accuracy"], ", ".join("%s %.3f" % kv for kv in emo["test2000_recall"].items())),
          "- T3's 40 rows get the same choice, probabilities and answer_confidence inside the 2,000-row run (%d/40; whole "
          "answer dict %d/40, the other differs only in the entropy `confidence` at the 4th decimal, batch padding), and "
          "under the whole-split per-class recall their class mix would score %.3f; observed %.3f. The T3 draw (seed 13) is "
          "easy for Laya english, not representative: compare systems paired on it, not against published accuracies." % (
              emo["t3_scored_fields_identical_in_test2000_run"], emo["t3_answers_identical_in_test2000_run"],
              emo["t3_expected_under_test2000_recall"], emo["t3_observed"])]
    L += ["", "## 7. Run identity", "", "| report | dataset_sha256 | questions_sha256 | revisions |", "|---|---|---|---|"]
    for s in sorted(res):
        for m in res[s]:
            x = res[s][m]
            L.append("| %s_%s | %s | %s | %s |" % (s, m, x["dataset_sha256"][:16], x["questions_sha256"][:16],
                                                 json.dumps(x["revisions"])))
    (HERE / "laya_summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (HERE / "laya_summary.json").write_text(json.dumps(
        {"results": res, "cross_check_metrics_extra": cross, "determinism": det, "option_order": probes, "truncation": trunc,
         "emotion_check": emo, "t4_v0_vs_key_only": t4, "noul_criteria": noul,
         "metrics_extra_cmd": " ".join(["scripts/metrics_extra.py"] + cmd[2:])},
        ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8")
    bad = [c for c in cross if not c[2]]
    print("laya_summary.md written; metrics_extra cross-check %d/%d ok%s" % (len(cross) - len(bad), len(cross),
                                                                          "" if not bad else " FAIL %s" % bad))
    return 1 if bad or not det["answers_identical"] else 0


if __name__ == "__main__":
    sys.exit(main())
