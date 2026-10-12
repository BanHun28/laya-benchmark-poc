"""S6 synthesis of the Laya vs Jev comparison (docs/09_laya_vs_jev_plan.md §7 S6). No model call, no request to the Jev site.

    source env.sh
    .venv/bin/python results/F/jev_cmp/s6_summary.py build    # summary.json, summary.ko.md, figs/*.png + *.svg
    .venv/bin/python results/F/jev_cmp/s6_summary.py verify   # re-runs jev_cmp.py and cross-checks session summaries / json / md

Per-task numbers reuse jev_cmp.py's helpers and data paths (wilson, ece, auroc, mcnemar_exact, laya_cases, the T1 assembly
of `jev_cmp.py t1`, laya_summary.py's metrics / t1_extra), so they are the session summaries' numbers by construction;
`verify` checks that against fresh `jev_cmp.py` output and against the session summary files. New in S6: the
aggregates (macro average with a bootstrap over tasks, pooled McNemar, cluster bootstraps for T1 and T7, Holm), the
latency / token / cost roll-up over all 410 successful requests, and the figures.
"""
import json
import math
import random
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import jev_cmp as J  # noqa: E402  (also puts scripts/ on sys.path for metrics_extra)
import laya_summary as LS  # noqa: E402

RUNNERS = J.LAYA_RUNNERS  # english, multilingual, router
SEED = 13
N_TASK_BOOT = 10_000
N_CLUSTER_BOOT = 10_000
LANGS = ("en", "de", "ja", "zh-CN", "ko")
SESSIONS = ("S1", "S1b", "S2", "S3", "S4", "S5")
OUT_JSON, OUT_MD, FIGS = HERE / "summary.json", HERE / "summary.ko.md", HERE / "figs"
PRICE_PER_M = 0.042  # USD per 1M tokens, third-party figure quoted by upstream (third_party/laya/README.md:1291)

TASKS = {
    "T1": dict(name="typed-decisions", sets=["T1_typed_decisions_40"], sessions=["S1", "S2"], kind="t1",
               form="혼합 (Multiple questions: choice 50 / Boolean 60 / 5레벨 score 10)", options="case당 2~4문항, 옵션 ≤ 5"),
    "T2": dict(name="AG News", sets=["T2_ag_news_40"], sessions=["S1"], kind="choice", form="single choice", options="4"),
    "T3": dict(name="DAIR Emotion", sets=["T3_emotion_40"], sessions=["S2"], kind="choice", form="single choice", options="6"),
    "T4": dict(name="Banking77-10", sets=["T4_banking77_10opt_40"], sessions=["S3"], kind="choice", form="single choice",
               options="10 (key-only)"),
    "T5": dict(name="BoolQ", sets=["T5_boolq_40"], sessions=["S3"], kind="boolean", form="single Boolean", options="2"),
    "T6": dict(name="SST-5", sets=["T6_sst5_40"], sessions=["S4"], kind="score", form="single score", options="5 레벨"),
    "T7": dict(name="MASSIVE intent-10 x5", sets=["T7_massive_intent_10opt_%s_20" % l for l in LANGS], sessions=["S4", "S5"],
               kind="choice", form="single choice", options="10 (영어 key)"),
    "T8": dict(name="prompt-injections", sets=["T8_prompt_injections_40"], sessions=["S5"], kind="boolean",
               form="single Boolean", options="2"),
}
POOLED_TASKS = ("T2", "T3", "T4", "T5", "T6", "T8")  # independent single-question items (T6 by argmax)

# External reference values: (value, file, line). `verify` checks each value string is on that line.
EXT = {
    "d1_english_cpu_1q": (86.6, "results/D/D_summary_20261003.md", 34), "d1_english_cpu_3q": (184.4, "results/D/D_summary_20261003.md", 34),
    "d1_multilingual_cpu_1q": (37.7, "results/D/D_summary_20261003.md", 36), "d1_multilingual_cpu_3q": (56.4, "results/D/D_summary_20261003.md", 36),
    "d1_english_mps_1q": (31.8, "results/D/D_summary_20261003.md", 40), "d1_english_mps_3q": (79.6, "results/D/D_summary_20261003.md", 40),
    "d1_multilingual_mps_1q": (13.8, "results/D/D_summary_20261003.md", 42), "d1_multilingual_mps_3q": (22.5, "results/D/D_summary_20261003.md", 42),
    "d1c_multilingual_cpu_1q_gap1000": (76.2, "results/D/D_summary_20261003.md", 87), "d1c_multilingual_cpu_3q_gap1000": (97.6, "results/D/D_summary_20261003.md", 88),
    "d1c_multilingual_mps_1q_gap1000": (49.2, "results/D/D_summary_20261003.md", 89), "d1c_multilingual_mps_3q_gap1000": (51.0, "results/D/D_summary_20261003.md", 90),
    "d6_mps_1q_c1_p50": (20.3, "results/D/D_summary_20261003.md", 203), "d6_mps_1q_c1_rps": (48.40, "results/D/D_summary_20261003.md", 203),
    "d6_mps_3q_c1_p50": (45.6, "results/D/D_summary_20261003.md", 209), "d6_mps_3q_open10_p50": (63.5, "results/D/D_summary_20261003.md", 213),
    "d6_mps_3q_open10_p95": (79.4, "results/D/D_summary_20261003.md", 213), "d6_cpu_1q_c1_p50": (50.7, "results/D/D_summary_20261003.md", 222),
    "d6_cpu_1q_c1_rps": (19.65, "results/D/D_summary_20261003.md", 222), "d6_cpu_3q_c1_p50": (99.5, "results/D/D_summary_20261003.md", 224),
    "p2_poc_decide_p50": (20.1, "results/poc/P2_20261003.md", 67), "p2_poc_decide_p95": (21.1, "results/poc/P2_20261003.md", 67),
    "readme_jev_price_per_1m_tokens": (0.042, "third_party/laya/README.md", 1291), "readme_jev_p50_lo": (236, "third_party/laya/README.md", 1288),
    "readme_jev_p50_hi": (276, "third_party/laya/README.md", 1288), "readme_laya_p50_1q_t4": (32.8, "third_party/laya/README.md", 1288),
    "published_jev_ag_news": (0.910, "third_party/laya/README.md", 1284), "published_jev_emotion": (0.480, "third_party/laya/README.md", 1285),
    "published_jev_typed_decisions": (0.727, "third_party/laya/README.md", 1283), "published_jev_banking77_72": (0.870, "third_party/laya/README.md", 1286),
    "published_jev_flip": (0.13, "docs/09_laya_vs_jev_plan.md", 23), "upstream_laya_emotion_english": (0.573, "results/F/jev_cmp/laya_summary.md", 22),
    "published_jev_typed_decisions_n": (2000, "third_party/laya/README.md", 1283), "docs09_min_detectable_diff": (0.2, "docs/09_laya_vs_jev_plan.md", 139), "p4_ftv1_domain8_test_acc": (0.900, "results/P4/metrics/full_20261003-1156_summary.md", 19),
}


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def wil(k, n):
    lo, hi = J.wilson(k, n)
    return [lo, hi]


def mcn(cj, cl, pj=None, pl=None):
    b = sum(x and not y for x, y in zip(cj, cl))
    c = sum(y and not x for x, y in zip(cj, cl))
    out = {"b": b, "c": c, "p": J.mcnemar_exact(b, c), "n": len(cj)}
    if pj is not None:
        out["same"] = sum(x == y for x, y in zip(pj, pl))
    return out


def summ(cor, conf, brier):
    n, k = len(cor), sum(cor)
    right = [c for c, y in zip(conf, cor) if y]
    wrong = [c for c, y in zip(conf, cor) if not y]
    return {"correct": k, "n": n, "acc": k / n, "wilson": wil(k, n), "brier": mean(brier), "ece": J.ece(conf, cor),
            "mean_top": mean(conf), "mean_top_right": mean(right), "mean_top_wrong": mean(wrong), "wrong": n - k,
            "wrong_ge90": sum(c >= 0.9 for c in wrong), "gap_top_minus_acc": mean(conf) - k / n}


def bits(cor):
    return "".join("1" if x else "0" for x in cor)


def pct_jev(xs):  # jev_cmp.py boolean_lines / score_lines percentile (2,000 resamples, seed 13)
    v = sorted(x for x in xs if x == x)
    return [v[round(0.025 * (len(v) - 1))], v[round(0.975 * (len(v) - 1))]]


# ---------------------------------------------------------------- data
def master_records():
    rows = [json.loads(x) for x in (HERE / "jev_runs_all.jsonl").read_text(encoding="utf-8").splitlines()]
    cat = []
    for s in SESSIONS:
        cat += [json.loads(x) for x in (J.session_dir(s) / ("%s_requests.jsonl" % s)).read_text(encoding="utf-8").splitlines()]
    # later sessions (S7: 3-arm T9/T10) append to the same master log; this summary covers SESSIONS only
    assert rows[:len(cat)] == cat, "master log does not start with the concatenation of the session request logs"
    return rows[:len(cat)]


def load_task(t, master):
    stems, sess = TASKS[t]["sets"], TASKS[t]["sessions"]
    items = [it for s in stems for it in J.load_items(s)[1]]
    recs = [r for r in master if r["session"] in sess and r["set"] in stems and r.get("decisions") and r["phase"] == "main"]
    by_id = {}
    for r in recs:
        for d in r["decisions"]:
            by_id[d["id"]] = (r, d)
    its = [it for it in items if it["id"] in by_id]
    assert len(its) == len(items), (t, len(its), len(items))
    laya = {m: {k: c for s in stems for k, c in J.laya_cases(s, m, J.load_items(s)[1])[1].items()} for m in RUNNERS}
    answered = {m: dict(Counter(laya[m][it["id"]]["model"] for it in its)) for m in RUNNERS}
    answered["router_by_set"] = {st: dict(Counter(laya["router"][it["id"]]["model"] for it in its if it["id"].startswith(st + "/"))) for st in stems}
    return its, by_id, laya, answered


def systems_choice(its, by_id, laya):
    keys = lambda it: [J.key_of(o) for o in it["options"]]  # noqa: E731
    br = lambda pr, it: sum((pr.get(k, 0.0) - (k == it["gold"])) ** 2 for k in keys(it))  # noqa: E731
    jd = [by_id[it["id"]][1] for it in its]
    S = {"jev": dict(pred=[d["pred"] for d in jd], conf=[d["top_p"] for d in jd], brier=[br(d["probs"], it) for d, it in zip(jd, its)])}
    for m in RUNNERS:
        a = [laya[m][it["id"]]["answer"] for it in its]
        S[m] = dict(pred=[x["choice"] for x in a], conf=[x["answer_confidence"] for x in a],
                    brier=[br(x["probabilities"], it) for x, it in zip(a, its)])
    for v in S.values():
        v["cor"] = [p == it["gold"] for p, it in zip(v["pred"], its)]
    extra = {"jev_top100": sum(t == 1 for t in S["jev"]["conf"]),
             "jev_gold_shown0": sum(d["probs"][it["gold"]] == 0 for d, it in zip(jd, its)),
             "jev_provider_conf_mean": mean((by_id[it["id"]][0].get("confidence") or {}).get("decision") for it in its
                                            if (by_id[it["id"]][0].get("confidence") or {}).get("decision") is not None)}
    return S, extra


def systems_boolean(its, by_id, laya):
    y = [bool(it["gold"]) for it in its]
    P = {"jev": [by_id[it["id"]][1]["p_true"] for it in its], **{m: [laya[m][it["id"]]["answer"]["noul"] for it in its] for m in RUNNERS}}
    S = {}
    for s, p in P.items():
        S[s] = dict(pred=[v >= 0.5 for v in p], conf=[max(v, 1 - v) for v in p], brier=[2 * (v - g) ** 2 for v, g in zip(p, y)], p=p)
        S[s]["cor"] = [(v >= 0.5) == g for v, g in zip(p, y)]
    rng = random.Random(SEED)
    idx = [[rng.randrange(len(y)) for _ in y] for _ in range(2000)]
    boot = {s: [J.auroc([p[k] for k in ix], [y[k] for k in ix]) for ix in idx] for s, p in P.items()}
    extra = {"gold_true": sum(y)}
    for s, p in P.items():
        thr = sorted(set(p)) + [float("inf")]
        acc = [sum((v >= t) == g for v, g in zip(p, y)) for t in thr]
        best = [t for t, n in zip(thr, acc) if n == max(acc)]
        extra[s] = {"auroc": J.auroc(p, y), "auroc_ci": pct_jev(boot[s]), "pred_true": sum(v >= 0.5 for v in p),
                    "fn": sum(g and v < 0.5 for v, g in zip(p, y)), "fp": sum((not g) and v >= 0.5 for v, g in zip(p, y)),
                    "best_thr_correct": max(acc), "best_thr_range": [best[0], best[-1]], "p_extreme": sum(v in (0, 1) for v in p),
                    "distinct_p": len(set(p))}
        if s != "jev":
            extra[s]["auroc_diff"] = J.auroc(P["jev"], y) - J.auroc(p, y)
            extra[s]["auroc_diff_ci"] = pct_jev([u - v for u, v in zip(boot["jev"], boot[s])])
    neg, pos = [v for v, g in zip(P["jev"], y) if not g], [v for v, g in zip(P["jev"], y) if g]
    extra["jev_p_true_range_gold_false"], extra["jev_p_true_range_gold_true"] = [min(neg), max(neg)], [min(pos), max(pos)]
    return S, extra


def systems_score(its, by_id, laya):
    K = len(its[0]["options"])
    y = [it["gold"] for it in its]
    jd = [by_id[it["id"]][1] for it in its]
    P = {"jev": ([[d["probs"][str(k)] for k in range(K)] for d in jd], [d["score"] for d in jd]),
         **{m: ([[laya[m][it["id"]]["answer"]["probabilities"][str(k)] for k in range(K)] for it in its],
                [laya[m][it["id"]]["answer"]["score"] for it in its]) for m in RUNNERS}}
    S, extra = {}, {}
    for s, (ps, es) in P.items():
        A = [p.index(max(p)) for p in ps]
        R = [math.floor(e + 0.5) for e in es]
        S[s] = dict(pred=A, conf=[max(p) for p in ps], brier=[sum((p[k] - (k == g)) ** 2 for k in range(K)) for p, g in zip(ps, y)],
                    cor=[a == g for a, g in zip(A, y)], cor_rounded=[r == g for r, g in zip(R, y)], ae=[abs(e - g) for e, g in zip(es, y)])
        k = sum(S[s]["cor_rounded"])
        extra[s] = {"rounded_correct": k, "rounded_acc": k / len(y), "rounded_wilson": wil(k, len(y)), "mae": mean(S[s]["ae"]),
                    "mean_signed": mean(e - g for e, g in zip(es, y)), "within1": mean(a <= 1 for a in S[s]["ae"]),
                    "levels_argmax": [A.count(v) for v in range(K)], "argmax_ne_rounded": sum(a != r for a, r in zip(A, R))}
    rng = random.Random(SEED)
    idx = [[rng.randrange(len(y)) for _ in y] for _ in range(2000)]
    for m in RUNNERS:
        extra[m]["mcnemar_rounded"] = mcn(S["jev"]["cor_rounded"], S[m]["cor_rounded"])
        extra[m]["mae_diff"] = (sum(S["jev"]["ae"]) - sum(S[m]["ae"])) / len(y)
        extra[m]["mae_diff_ci"] = pct_jev([sum(S["jev"]["ae"][k] - S[m]["ae"][k] for k in ix) / len(ix) for ix in idx])
    extra["gold_levels"] = [y.count(v) for v in range(K)]
    return S, extra


def t1_systems(master):
    """`jev_cmp.py t1 S1,S2` assembly: Jev's latest successful record per decision vs every Laya T1 report."""
    stem = "T1_typed_decisions_40"
    form = {(it["row"], it["qid"]): it for it in J.load_items(stem)[1]}
    rows = LS.read_dataset(J.DATA / (stem + ".jsonl"))[0]
    gold = json.loads(LS.GOLD.read_text(encoding="utf-8"))["decisions"]
    jrec = {}
    for r in master:
        if r["session"] in ("S1", "S2") and r["set"] == stem and r.get("decisions"):
            jrec.update({d["id"]: (r, d) for d in r["decisions"]})
    laya = {m: LS.decisions(HERE / "laya" / ("%s_%s.json" % (stem, m)))[1] for m in RUNNERS + ("typed-decisions",)}
    keep = [i for i, d in enumerate(laya["english"]) if not d["jev_excluded"]]
    G = [gold[i] for i in keep]
    jev = []
    for i in keep:
        d0 = laya["english"][i]
        r, d = jrec[form[(d0["row"], d0["qid"])]["id"]]
        q = rows[d0["row"]]["questions"][d0["qid"]]
        if d0["type"] == "choice":
            keys = list(q["criteria"])
            p, pi = [d["probs"][k] for k in keys], keys.index(d["pred"])
        elif d0["type"] == "noul":
            p, pi = [1 - d["p_true"], d["p_true"]], int(d["pred"])
        else:
            p, pi = [d["probs"][str(k)] for k in range(len(q["criteria"]))], d["pred"]
        jev.append(dict(d0, pred=d["pred"], pi=pi, p=p, conf=max(p), score=d.get("score"), model="jev"))
    D = {"jev": jev, **{m: [laya[m][i] for i in keep] for m in laya}}
    nocrit = {m: {(d["row"], d["qid"]): d for d in LS.decisions(HERE / "laya" / ("%s_noulnocrit_%s.json" % (stem, m)))[1]}
              for m in ("english", "multilingual")}
    return D, G, nocrit, rows, len({(r["session"], r["run"]) for r, _ in jrec.values()})


def task_t1(master):
    D, G, nocrit, rows, runs = t1_systems(master)
    ok = lambda d: d["pred"] == d["gold"]  # noqa: E731
    S, extra = {}, {"by_type": {}, "runs": runs, "cases": len({d["row"] for d in D["jev"]})}
    for s, ds in D.items():
        mt, x = LS.metrics(ds), LS.t1_extra(ds, G)
        S[s] = dict(cor=[ok(d) for d in ds], conf=[d["conf"] for d in ds], pred=[d["pred"] for d in ds], case=[d["row"] for d in ds],
                    type=[d["type"] for d in ds], summary={**summ([ok(d) for d in ds], [d["conf"] for d in ds], [0.0] * len(ds)),
                                                           "brier": mt["brier"], "ece": mt["ece"]})
        extra[s] = {"soft_acc": x["soft_accuracy"], "brier_vs_soft": x["brier_vs_soft"], "score_mae": x["score_mae"]}
        for t in ("choice", "noul", "score"):
            sel = [ok(d) for d in ds if d["type"] == t]
            extra["by_type"].setdefault(t, {})[s] = {"correct": sum(sel), "n": len(sel), "acc": sum(sel) / len(sel), "wilson": wil(sum(sel), len(sel))}
    extra["majority"] = LS.t1_extra(D["english"], G)["per_question_majority"]
    extra["jev_score_mae_field"] = statistics.mean(abs(d["score"] - g["gold_score"]) for d, g in zip(D["jev"], G) if d["type"] == "score")
    extra["mcnemar_by_type"] = {m: {t: mcn([ok(d) for d in D["jev"] if d["type"] == t], [ok(d) for d in D[m] if d["type"] == t])
                                    for t in ("choice", "noul", "score")} for m in list(RUNNERS) + ["typed-decisions"]}
    jn = [d for d in D["jev"] if d["type"] == "noul"]
    extra["noul_nocrit"] = {}
    for m in ("english", "multilingual"):
        ds = [nocrit[m][(d["row"], d["qid"])] for d in jn]
        extra["noul_nocrit"][m] = {"correct": sum(map(ok, ds)), "n": len(ds), **mcn([ok(d) for d in jn], [ok(d) for d in ds])}
    conf_t = {}
    for t in ("choice", "noul", "score"):
        ds = [d for d in D["jev"] if d["type"] == t]
        conf_t[t] = {"n": len(ds), "mean_top_right": mean(d["conf"] for d in ds if ok(d)), "mean_top_wrong": mean(d["conf"] for d in ds if not ok(d)),
                     "wrong": sum(not ok(d) for d in ds), "wrong_ge90": sum(d["conf"] >= 0.9 and not ok(d) for d in ds),
                     "top100": sum(d["conf"] >= 0.995 for d in ds), "acc": mean(ok(d) for d in ds), "mean_top": mean(d["conf"] for d in ds)}
    extra["jev_conf_by_type"] = conf_t
    return S, extra


def build_task(t, master):
    kind = TASKS[t]["kind"]
    if kind == "t1":
        S, extra = task_t1(master)
        res = {s: v["summary"] for s, v in S.items()}
        answered = {"router": {"english": 120}}
    else:
        its, by_id, laya, answered = load_task(t, master)
        S, extra = {"choice": systems_choice, "boolean": systems_boolean, "score": systems_score}[kind](its, by_id, laya)
        res = {s: summ(v["cor"], v["conf"], v["brier"]) for s, v in S.items()}
        if kind == "choice":
            res["jev"].update(top100=extra.pop("jev_top100"), gold_shown0=extra.pop("jev_gold_shown0"))
        S["_items"] = its
    for s in res:
        if s != "jev":  # Jev results are published as aggregates only (owner decision 2026-10-12)
            res[s]["item_correct"] = bits(S[s]["cor"])
    mc = {m: mcn(S["jev"]["cor"], S[m]["cor"], S["jev"]["pred"], S[m]["pred"]) for m in RUNNERS}
    if kind == "t1":
        mc["typed-decisions"] = mcn(S["jev"]["cor"], S["typed-decisions"]["cor"], S["jev"]["pred"], S["typed-decisions"]["pred"])
    order = ("english", "multilingual", "router")  # tie-break: the plain checkpoints before the Router meta-runner
    best = max(order, key=lambda m: (res[m]["acc"], -order.index(m)))
    man = json.loads((J.DATA / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
    mix = sorted({man[s + ".jsonl"]["in_training_mix"] for s in TASKS[t]["sets"]})
    assert len(mix) == 1, (t, mix)
    out = {**TASKS[t], "systems": res, "mcnemar": mc, "best_laya": best, "extra": extra, "router_answered_by": answered.get("router"),
           "router_by_set": answered.get("router_by_set"),
           "in_training_mix": mix[0], "jev_comparable_n": sum(man[s + ".jsonl"]["jev_comparable_n"] for s in TASKS[t]["sets"])}
    return out, S


def t7_details(S, its):
    """Per language accuracy / McNemar, language penalty, cross-language consistency, as jev_cmp.py crosslang_multi."""
    lang_of = lambda it: it["id"].split("/")[0].rsplit("_", 2)[1]  # noqa: E731
    out = {"per_lang": {}, "penalty": {}, "consistency": {}}
    for L in LANGS:
        ix = [k for k, it in enumerate(its) if lang_of(it) == L]
        out["per_lang"][L] = {s: {"correct": sum(S[s]["cor"][k] for k in ix), "n": len(ix), "acc": sum(S[s]["cor"][k] for k in ix) / len(ix),
                                  "wilson": wil(sum(S[s]["cor"][k] for k in ix), len(ix)), "brier": mean(S[s]["brier"][k] for k in ix),
                                  "ece": J.ece([S[s]["conf"][k] for k in ix], [S[s]["cor"][k] for k in ix])} for s in ("jev",) + RUNNERS}
        for m in RUNNERS:
            out["per_lang"][L][m]["mcnemar"] = mcn([S["jev"]["cor"][k] for k in ix], [S[m]["cor"][k] for k in ix])
    for s in ("jev",) + RUNNERS:
        d = [out["per_lang"][L][s]["acc"] - out["per_lang"]["en"][s]["acc"] for L in LANGS[1:]]
        out["penalty"][s] = {**dict(zip(LANGS[1:], d)), "mean": mean(d)}
    groups = defaultdict(dict)
    for k, it in enumerate(its):
        groups[it["id"].split("/", 1)[1]][lang_of(it)] = k
    G = [[g[L] for L in LANGS] for g in groups.values()]
    pairs = [(u, v) for u in range(5) for v in range(u + 1, 5)]
    for s in ("jev",) + RUNNERS:
        lab = [[S[s]["pred"][k] for k in g] for g in G]
        okk = [[S[s]["cor"][k] for k in g] for g in G]
        out["consistency"][s] = {"same_all5": sum(len(set(x)) == 1 for x in lab), "ids": len(G), "pairs": len(pairs),
                                 "pairwise_agree": sum(x[u] == x[v] for x in lab for u, v in pairs) / (len(G) * len(pairs)),
                                 "right_all5": sum(all(o) for o in okk), "wrong_all5": sum(not any(o) for o in okk),
                                 "same_as_en": {L: sum(x[0] == x[i] for x in lab) for i, L in enumerate(LANGS) if i}}
    out["id_groups"] = G
    return out


def cluster_boot(cor_j, cor_l, cluster, n_boot=N_CLUSTER_BOOT, seed=SEED):
    """Cluster (case / id) bootstrap of the paired accuracy difference Jev - Laya: resample clusters with replacement,
    difference of correct counts over the decisions in the drawn clusters."""
    cl = sorted(set(cluster))
    dj = np.array([sum(j for j, c in zip(cor_j, cluster) if c == k) for k in cl], float)
    dl = np.array([sum(x for x, c in zip(cor_l, cluster) if c == k) for k in cl], float)
    nn = np.array([sum(c == k for c in cluster) for k in cl], float)
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(cl), size=(n_boot, len(cl)))
    d = (dj[ix].sum(1) - dl[ix].sum(1)) / nn[ix].sum(1)
    return {"diff": (dj.sum() - dl.sum()) / nn.sum(), "ci": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
            "clusters": len(cl), "items": int(nn.sum()), "resamples": n_boot}


def holm(ps):
    order = sorted(ps, key=ps.get)
    out, run = {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (len(ps) - i) * ps[k]))
        out[k] = run
    return out


# ---------------------------------------------------------------- latency, tokens, robustness, references
TYPE_OF = {"T1": "multi", "T2": "single_choice", "T3": "single_choice", "T4": "single_choice", "T7": "single_choice",
           "T5": "single_boolean", "T8": "single_boolean", "T6": "single_score"}


def lat_stats(rr):
    def q(xs):
        a = np.array(xs, float)
        return {"median": float(np.median(a)), "p5": float(np.percentile(a, 5)), "p95": float(np.percentile(a, 95)),
                "min": float(a.min()), "max": float(a.max())}
    tok_in = [r["usage"]["inputTokens"] for r in rr]
    tok_out = [r["usage"]["outputTokens"] for r in rr]
    nd = [len(r["decisions"]) for r in rr]
    return {"requests": len(rr), "decisions": sum(nd), "displayed_ms": q([r["displayed_ms"] for r in rr]),
            "browser_post_ms": q([r["fetch_dur_ms"] for r in rr]), "latency_ms_response_median": float(np.median([r["latency_ms_response"] for r in rr])),
            "post_minus_latency_median": float(np.median([r["fetch_dur_ms"] - r["latency_ms_response"] for r in rr])),
            "tokens_in_req_median": float(np.median(tok_in)), "tokens_out_req_median": float(np.median(tok_out)),
            "tokens_in_dec_median": float(np.median([a / n for a, n in zip(tok_in, nd)])),
            "tokens_out_dec_median": float(np.median([a / n for a, n in zip(tok_out, nd)])),
            "tokens_in_total": sum(tok_in), "tokens_out_total": sum(tok_out),
            "tokens_per_dec_mean": (sum(tok_in) + sum(tok_out)) / sum(nd),
            "cost_per_1k_dec_usd": (sum(tok_in) + sum(tok_out)) / sum(nd) * 1000 * PRICE_PER_M / 1e6}


def latency(master):
    ok = [r for r in master if r.get("decisions")]
    out = {"by_task": {t: lat_stats([r for r in ok if r["task"] == t]) for t in TASKS},
           "by_type": {k: lat_stats([r for r in ok if TYPE_OF[r["task"]] == k]) for k in ("single_choice", "single_boolean", "single_score", "multi")},
           "single_all": lat_stats([r for r in ok if r["task"] != "T1"]), "all": lat_stats(ok)}
    out["by_task"]["T2_main"] = lat_stats([r for r in ok if r["task"] == "T2" and r["session"] == "S1"])
    out["model_ids"] = dict(Counter(r["model_id_details"] for r in ok))
    out["rounding"] = dict(Counter(json.dumps(r["rounding"], sort_keys=True) for r in ok))
    return out


def requests_meta(master):
    by_s = {}
    for s in SESSIONS:
        rr = [r for r in master if r["session"] == s]
        gaps = [r["gap_from_prev_click_s"] for r in rr if r["gap_from_prev_click_s"] is not None]
        by_s[s] = {"requests": len(rr), "ok": sum(bool(r.get("decisions")) for r in rr), "http": dict(Counter(str(r["http_status"]) for r in rr)),
                   "retries": sum(r["attempt"] > 1 for r in rr), "first_click": rr[0]["click_kst"], "last_click": rr[-1]["click_kst"],
                   "gap_min_s": min(gaps), "gap_median_s": statistics.median(gaps), "date": rr[0]["date"]}
    pilot = [json.loads(x) for x in (ROOT / "results/F/jev_runs_raw.jsonl").read_text(encoding="utf-8").splitlines()]
    p_ok = [r for r in pilot if r["fetch"]["status"] == 200]
    pilot_gaps = [r["gap_from_prev_click_s"] for r in pilot if r.get("gap_from_prev_click_s") is not None]
    err = [r for r in master if not r.get("decisions")]
    retry = [r for r in master if r["attempt"] > 1]
    from datetime import datetime, timedelta, timezone
    kst = lambda ms: datetime.fromtimestamp(ms / 1000, timezone(timedelta(hours=9))).strftime("%H:%M:%S")  # noqa: E731
    return {"master_records": len(master), "master_ok": sum(bool(r.get("decisions")) for r in master), "by_session": by_s,
            "master_errors": [{"session": r["session"], "run": r["run"], "http": r["http_status"], "error": r.get("error")} for r in err],
            "retries": [{"session": r["session"], "run": r["run"], "gap_s": r["gap_from_prev_click_s"]} for r in retry],
            "payload_exact": sum(bool(r.get("payload_exact")) for r in master),
            "pilot_first_click": kst(min(r["click_epoch_ms"] for r in pilot)), "pilot_last_click": kst(max(r["click_epoch_ms"] for r in pilot)),
            "pilot_resume_after_min": (min(r["click_epoch_ms"] for r in pilot if r["attempt"] > 1) - max(r["click_epoch_ms"] for r in pilot if r["fetch"]["status"] == 502)) / 60000,
            "display_matches": sum(bool(r.get("display_matches_response")) for r in master),
            "pilot_requests": len(pilot), "pilot_ok": len(p_ok), "pilot_http": dict(Counter(str(r["fetch"]["status"]) for r in pilot)),
            "pilot_gap_min_s": min(pilot_gaps), "coordinator_checks": 2,
            "pre_tooling": len(pilot) + 2, "total_site": len(master) + len(pilot) + 2,
            "by_day": {"2026-10-06": len(pilot) + 2 + by_s["S1"]["requests"] + by_s["S1b"]["requests"],
                       "2026-10-07": sum(by_s[s]["requests"] for s in ("S2", "S3", "S4", "S5"))},
            "http_502_total": sum(r["http_status"] == 502 for r in master) + sum(r["fetch"]["status"] == 502 for r in pilot),
            "http_429_total": sum(r["http_status"] == 429 for r in master) + sum(r["fetch"]["status"] == 429 for r in pilot)}


def robustness(master):
    ref = {r["row"]: r for r in master if r["session"] == "S1" and r["set"] == "T2_ag_news_40" and r.get("decisions") and r["phase"] == "main"}
    cur = [r for r in master if r["session"] == "S1b" and r.get("decisions")]
    det = [r for r in cur if r["phase"] == "determinism"]
    flp = [r for r in cur if r["phase"] == "option_order"]
    top = lambda r: r["decisions"][0]  # noqa: E731
    dps = [max(abs(top(ref[r["row"]])["probs"].get(k, 0) - top(r)["probs"].get(k, 0)) for k in set(top(r)["probs"]) | set(top(ref[r["row"]])["probs"])) for r in det]
    probes = {m: {x["row"]: x for x in json.loads((HERE / ("T2_option_order_k1_%s.json" % m)).read_text(encoding="utf-8"))["sets"][0]["items"]}
              for m in ("english", "multilingual")}
    flips = sum(top(ref[r["row"]])["pred"] != top(r)["pred"] for r in flp)
    lflips = {m: sum(probes[m][r["row"]]["perms"][0]["pred"] != probes[m][r["row"]]["orig"]["pred"] for r in flp) for m in probes}
    laya_det = json.loads((HERE / "laya_summary.json").read_text(encoding="utf-8"))["determinism"]
    return {"determinism": {"rows": len(det), "same_label": sum(top(ref[r["row"]])["pred"] == top(r)["pred"] for r in det),
                            "resend_after_min_median": statistics.median((r["click_epoch_ms"] - ref[r["row"]]["click_epoch_ms"]) / 60000 for r in det),
                            "resend_after_min_range": [f((r["click_epoch_ms"] - ref[r["row"]]["click_epoch_ms"]) / 60000 for r in det) for f in (min, max)],
                            "identical_probs": sum(x == 0 for x in dps), "max_abs_dp": max(dps),
                            "tokens_identical": sum((ref[r["row"]]["usage"]["inputTokens"], ref[r["row"]]["usage"]["outputTokens"]) ==
                                                    (r["usage"]["inputTokens"], r["usage"]["outputTokens"]) for r in det),
                            "laya_t1_english_rerun_identical": laya_det["answers_identical"], "laya_t1_rerun_decisions": laya_det.get("cases", 200)},
            "option_order": {"rows": len(flp), "jev_flips": flips, "jev_wilson": wil(flips, len(flp)), "laya_flips": lflips,
                             "p_zero_flips_if_013": 0.87 ** len(flp), "laya_probe_40_rows_flip": {m: 0.0 for m in probes}}}


def references(t1):
    s24 = {r["row_index"]: r for r in (json.loads(x) for x in (ROOT / "results/F/jev_sample_24.jsonl").read_text(encoding="utf-8").splitlines())}
    pilot = [json.loads(x) for x in (ROOT / "results/F/jev_runs_raw.jsonl").read_text(encoding="utf-8").splitlines()]
    jev = {r["row_index"]: r["decision_key"] for r in pilot if r["fetch"]["status"] == 200}
    rows = sorted(s24)
    cj = [jev[i] == s24[i]["gold"] for i in rows]
    cz = [s24[i]["laya_zs"] == s24[i]["gold"] for i in rows]
    cf = [s24[i]["laya_ft"] == s24[i]["gold"] for i in rows]
    ok = [r for r in pilot if r["fetch"]["status"] == 200]
    p4 = json.loads((ROOT / "results/P4/metrics/full_20261003-1156_summary.json").read_text(encoding="utf-8"))["results"]
    row = lambda model: next(x for x in p4 if x["set"] == "ko_massive_domain_8" and x["model"] == model and x["split"] == "test" and x["n"] == 250)  # noqa: E731
    ft, zs = row("ft-v1"), row("multilingual")
    return {"t1_typed_decisions": {"correct": t1["systems"]["typed-decisions"]["correct"], "n": 120, "acc": t1["systems"]["typed-decisions"]["acc"],
                                   "wilson": t1["systems"]["typed-decisions"]["wilson"], "mcnemar_vs_jev": t1["mcnemar"]["typed-decisions"],
                                   "by_type": {t: t1["extra"]["by_type"][t]["typed-decisions"] for t in ("choice", "noul", "score")},
                                   "soft_acc": t1["extra"]["typed-decisions"]["soft_acc"], "brier": t1["systems"]["typed-decisions"]["brier"],
                                   "ece": t1["systems"]["typed-decisions"]["ece"]},
            "ko_pilot": {"n": len(rows), "jev": sum(cj), "laya_zero_shot": sum(cz), "laya_ft_v1": sum(cf),
                         "jev_acc": sum(cj) / len(rows), "zs_acc": sum(cz) / len(rows), "ft_acc": sum(cf) / len(rows),
                         "jev_wilson": wil(sum(cj), len(rows)), "zs_wilson": wil(sum(cz), len(rows)), "ft_wilson": wil(sum(cf), len(rows)),
                         "mcnemar_jev_vs_zs": mcn(cj, cz), "mcnemar_jev_vs_ft": mcn(cj, cf),
                         "jev_displayed_median": statistics.median(r["ms"] for r in ok), "jev_post_median": statistics.median(r["fetch"]["dur_ms"] for r in ok),
                         "jev_tokens_in_median": statistics.median(r["usage"]["inputTokens"] for r in ok),
                         "jev_tokens_out_median": statistics.median(r["usage"]["outputTokens"] for r in ok)},
            "p4_domain8_test_half": {"ft_v1": {"acc": ft["accuracy"], "ci": ft["accuracy_ci"], "n": ft["n"]},
                                     "multilingual_zero_shot": {"acc": zs["accuracy"], "ci": zs["accuracy_ci"], "n": zs["n"]}},
            "t4_rendering": json.loads((HERE / "laya_summary.json").read_text(encoding="utf-8"))["t4_v0_vs_key_only"]}


# ---------------------------------------------------------------- build
def build():
    master = master_records()
    tasks, S = {}, {}
    for t in TASKS:
        tasks[t], S[t] = build_task(t, master)
    t7 = t7_details(S["T7"], S["T7"]["_items"])
    tasks["T7"]["extra"].update({k: v for k, v in t7.items() if k != "id_groups"})
    t7_ids = [S["T7"]["_items"][g[0]]["id"].split("/", 1)[1] for g in t7["id_groups"]]
    clus_t7 = [next(i for i, g in enumerate(t7["id_groups"]) if k in g) for k in range(len(S["T7"]["_items"]))]

    # per-task verdict: exact McNemar, Jev vs the best zero-shot Laya runner, two-sided alpha 0.05; Holm over the 8 tests
    pvals = {t: tasks[t]["mcnemar"][tasks[t]["best_laya"]]["p"] for t in TASKS}
    hp = holm(pvals)
    for t in TASKS:
        m = tasks[t]["mcnemar"][tasks[t]["best_laya"]]
        sig = lambda p: "Jev 유의 우세" if p < 0.05 and m["b"] > m["c"] else ("Laya 유의 우세" if p < 0.05 and m["c"] > m["b"] else "비유의")  # noqa: E731
        tasks[t]["verdict"], tasks[t]["holm_p"], tasks[t]["verdict_holm"] = sig(m["p"]), hp[t], sig(hp[t])
    clusters = {"T1": {m: cluster_boot(S["T1"]["jev"]["cor"], S["T1"][m]["cor"], S["T1"]["jev"]["case"]) for m in RUNNERS},
                "T7": {m: cluster_boot(S["T7"]["jev"]["cor"], S["T7"][m]["cor"], clus_t7) for m in RUNNERS}}
    clusters["T1"]["note"], clusters["T7"]["note"] = "40 cases (rows), 120 decisions", "20 MASSIVE ids x 5 languages"
    clusters["T7"]["ids"] = t7_ids

    # macro average over the 8 tasks and a paired bootstrap over tasks (descriptive: 8 heterogeneous tasks)
    acc = {s: [tasks[t]["systems"][s]["acc"] for t in TASKS] for s in ("jev",) + RUNNERS}
    acc["best"] = [tasks[t]["systems"][tasks[t]["best_laya"]]["acc"] for t in TASKS]
    rng = np.random.default_rng(SEED)
    ix = rng.integers(0, len(TASKS), size=(N_TASK_BOOT, len(TASKS)))
    macro = {"tasks": list(TASKS), "resamples": N_TASK_BOOT, "seed": SEED, "acc": {s: float(np.mean(v)) for s, v in acc.items()}, "diff": {}}
    for s in RUNNERS + ("best",):
        d = np.array(acc["jev"]) - np.array(acc[s])
        bd = d[ix].mean(1)
        macro["diff"][s] = {"diff": float(d.mean()), "ci": [float(np.percentile(bd, 2.5)), float(np.percentile(bd, 97.5))],
                            "share_le0": float((bd <= 0).mean())}
    no_t1 = [k for k, t in enumerate(TASKS) if t != "T1"]
    macro["without_T1"] = {s: float(np.mean([acc[s][k] for k in no_t1])) for s in ("jev",) + RUNNERS + ("best",)}

    # pooled exact McNemar over the independent single-question items (240)
    pooled = {}
    for lab, pick in (("best", None), ("english", "english"), ("multilingual", "multilingual"), ("router", "router")):
        cj, cl, per = [], [], {}
        for t in POOLED_TASKS:
            m = pick or tasks[t]["best_laya"]
            cj += S[t]["jev"]["cor"]
            cl += S[t][m]["cor"]
            per[t] = {"runner": m, "b": tasks[t]["mcnemar"][m]["b"], "c": tasks[t]["mcnemar"][m]["c"]}
        pooled[lab] = {**mcn(cj, cl), "jev_correct": sum(cj), "laya_correct": sum(cl), "per_task": per}

    lat = latency(master)
    out = {
        "meta": {"generated_by": "results/F/jev_cmp/s6_summary.py build", "date": "2026-10-07",
                 "jev": {"site": "https://jevplayground.com", "endpoint": "POST /api/evaluate", "model_ids": lat.pop("model_ids"),
                         "rounding": lat.pop("rounding")},
                 "laya": {"version": "0.3.23", "revision": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "runners": list(RUNNERS),
                          "device": "CPU fp32, intra-op 10 / inter-op 1, batch 8 (results/F/jev_cmp/run_laya.sh)"},
                 "methods": {"ci": 0.95, "ece_bins": 15, "alpha": 0.05, "seed": SEED, "task_boot": N_TASK_BOOT, "cluster_boot": N_CLUSTER_BOOT,
                             "jev_cmp_boot": 2000, "conf_hi": 0.9, "bool_threshold": 0.5, "price_per_1m_tokens_usd": PRICE_PER_M,
                             "pooled_tasks": list(POOLED_TASKS), "pooled_items": sum(tasks[t]["systems"]["jev"]["n"] for t in POOLED_TASKS),
                             "n_tasks": len(TASKS), "langs": len(LANGS), "jev_rounding_err": 0.005, "pacing_guard_s": 15, "per_k": 1000,
                             "per_m_tokens": 1_000_000, "ci_halfwidth_n40": (lambda w: (w[1] - w[0]) / 2)(wil(20, 40)),
                             "ci_halfwidth_n20": (lambda w: (w[1] - w[0]) / 2)(wil(10, 20))},
                 "limits": json.loads((J.DATA / "MANIFEST.json").read_text(encoding="utf-8"))["limits"],
                 "t1_decisions_total": json.loads((J.DATA / "MANIFEST.json").read_text(encoding="utf-8"))["files"]["T1_typed_decisions_40.jsonl"]["decisions"],
                 "requests": requests_meta(master)},
        "tasks": tasks,
        "aggregate": {"verdicts": dict(Counter(tasks[t]["verdict"] for t in TASKS)), "verdicts_holm": dict(Counter(tasks[t]["verdict_holm"] for t in TASKS)),
                      "macro": macro, "pooled_mcnemar": pooled, "cluster_bootstrap": clusters},
        "robustness": robustness(master),
        "latency_tokens": lat,
        "references": references(tasks["T1"]),
        "external": {k: {"value": v, "source": "%s:%d" % (f, ln)} for k, (v, f, ln) in EXT.items()},
        "calibration": calibration(tasks, S),
        "laya_capacity": {"mps_1q_rps": EXT["d6_mps_1q_c1_rps"][0], "cpu_1q_rps": EXT["d6_cpu_1q_c1_rps"][0],
                          "sec_per_1k_mps": 1000 / EXT["d6_mps_1q_c1_rps"][0], "sec_per_1k_cpu": 1000 / EXT["d6_cpu_1q_c1_rps"][0]},
    }
    import matplotlib
    out["meta"]["env"] = {"python": sys.version.split()[0], "numpy": np.__version__, "matplotlib": matplotlib.__version__}
    out["meta"]["s6_run"] = {"work_started_kst": "2026-10-07 15:32", "built_kst": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}
    E = {k: v for k, (v, _, _) in EXT.items()}
    out["representativeness"] = {t: {"jev_acc": tasks[t]["systems"]["jev"]["acc"], "published": E[k], "diff": tasks[t]["systems"]["jev"]["acc"] - E[k],
                                     "inside_wilson": tasks[t]["systems"]["jev"]["wilson"][0] <= E[k] <= tasks[t]["systems"]["jev"]["wilson"][1]}
                                 for t, k in (("T1", "published_jev_typed_decisions"), ("T2", "published_jev_ag_news"), ("T3", "published_jev_emotion"))}
    out["figures"] = make_figures(out)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(out), encoding="utf-8")
    print("wrote", OUT_JSON.relative_to(ROOT), OUT_MD.relative_to(ROOT), "and figs/", ", ".join(k for k in out["figures"] if k != "palette"))


def calibration(tasks, S):
    """Jev confidence patterns per question type and the same counts for the best Laya runner per task."""
    def roll(ts, sys_of):
        n = sum(tasks[t]["systems"][sys_of(t)]["n"] for t in ts)
        conf = [c for t in ts for c in S[t][sys_of(t)]["conf"]]
        cor = [c for t in ts for c in S[t][sys_of(t)]["cor"]]
        wrong = [c for c, y in zip(conf, cor) if not y]
        return {"tasks": list(ts), "n": n, "acc": mean(cor), "mean_top": mean(conf), "gap": mean(conf) - mean(cor),
                "top100": sum(c >= 0.995 for c in conf), "top100_share": sum(c >= 0.995 for c in conf) / n,
                "wrong": len(wrong), "wrong_ge90": sum(c >= 0.9 for c in wrong),
                "wrong_ge90_share": (sum(c >= 0.9 for c in wrong) / len(wrong)) if wrong else None}
    groups = {"single_choice": ("T2", "T3", "T4", "T7"), "single_boolean": ("T5", "T8"), "single_score": ("T6",), "multi": ("T1",)}
    return {"jev": {k: roll(ts, lambda t: "jev") for k, ts in groups.items()},
            "best_laya": {k: roll(ts, lambda t: tasks[t]["best_laya"]) for k, ts in groups.items()},
            "per_task": {t: {s: {"top100": sum(c >= 0.995 for c in S[t][s]["conf"])} for s in ("jev",) + RUNNERS} for t in TASKS}}


# ---------------------------------------------------------------- figures (dataviz skill: palette.md slots, marks-and-anatomy.md specs)
PAL = {"jev": "#2a78d6", "english": "#eb6834", "multilingual": "#1baf7a", "router": "#eda100"}  # categorical slots 1-4, light mode
INK = {"primary": "#0b0b0b", "secondary": "#52514e", "muted": "#898781", "grid": "#e1e0d9", "axis": "#c3c2b7", "surface": "#fcfcfb"}
SYS_LABEL = {"jev": "Jev (playground)", "english": "Laya english", "multilingual": "Laya multilingual", "router": "Laya Router"}


def _contrast(a, b):  # WCAG 2 contrast ratio of two hex colours
    def lum(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _pv(p):
    return ("p=%.1e" % p) if p < 0.001 else ("p=%.3f" % p)


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "Apple SD Gothic Neo", "font.size": 12, "axes.unicode_minus": False, "svg.fonttype": "path",
                         "axes.edgecolor": INK["axis"], "axes.labelcolor": INK["secondary"], "xtick.color": INK["muted"],
                         "ytick.color": INK["secondary"], "figure.facecolor": INK["surface"], "axes.facecolor": INK["surface"]})
    return plt


def _hbar(ax, y, x1, h, color, r_px=4.0):
    """Horizontal bar from the x=0 baseline to x1: square at the baseline, 4 px rounded data end (marks-and-anatomy.md)."""
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath
    bb, (x0a, x1a), (y0a, y1a) = ax.get_window_extent(), ax.get_xlim(), ax.get_ylim()
    rx = min(r_px * (x1a - x0a) / bb.width, x1 / 2)
    ry = min(r_px * abs(y1a - y0a) / bb.height, h / 2)
    yb, yt = y - h / 2, y + h / 2
    v = [(0, yb), (x1 - rx, yb), (x1, yb), (x1, yb + ry), (x1, yt - ry), (x1, yt), (x1 - rx, yt), (0, yt), (0, yb)]
    c = [MPath.MOVETO, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.LINETO, MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(v, c), facecolor=color, edgecolor="none", zorder=3))


def _frame(ax, xticks, xlabel):
    ax.set_xticks(xticks)
    ax.grid(axis="x", color=INK["grid"], linewidth=1, zorder=0)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=0, labelsize=11)
    for s in ("top", "right", "bottom"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(INK["axis"])
    ax.set_xlabel(xlabel, fontsize=11.5, color=INK["secondary"])


def _titles(fig, title, subtitle):
    fig.text(0.02, 0.965, title, fontsize=17, fontweight="bold", color=INK["primary"], va="top")
    fig.text(0.02, 0.915, subtitle, fontsize=11, color=INK["secondary"], va="top", linespacing=1.45)


def _grouped(ax, groups, series, values, cis, slot=0.24, bar=0.22):
    """groups top to bottom, series bars inside a group with a 2 px surface gap (slot - bar), Wilson whiskers in ink."""
    k = len(series)
    for gi, g in enumerate(groups):
        for si, s in enumerate(series):
            y = gi + (si - (k - 1) / 2) * slot
            v, (lo, hi) = values[g][s], cis[g][s]
            _hbar(ax, y, v, bar, PAL[s])
            ax.plot([lo, hi], [y, y], color=INK["secondary"], linewidth=1.3, zorder=4, solid_capstyle="butt")
            for x in (lo, hi):
                ax.plot([x, x], [y - bar * 0.3, y + bar * 0.3], color=INK["secondary"], linewidth=1.3, zorder=4)
            if gi == 0:  # direct labels inside the first group's bars (legend carries the rest); ink or white by contrast
                ax.text(0.012, y, SYS_LABEL[s], va="center", fontsize=10, zorder=5,
                        color="#ffffff" if _contrast("#ffffff", PAL[s]) >= _contrast(INK["primary"], PAL[s]) else INK["primary"])


def _legend(fig, series, y=0.845):
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(facecolor=PAL[s], edgecolor="none", label=SYS_LABEL[s]) for s in series], loc="upper left",
               bbox_to_anchor=(0.02, y), ncol=len(series), frameon=False, fontsize=11.5, handlelength=1.4, handleheight=0.9,
               labelcolor=INK["secondary"], columnspacing=1.6)


def _save(fig, name):
    FIGS.mkdir(exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(FIGS / ("%s.%s" % (name, ext)), dpi=100, facecolor=INK["surface"])


def palette_check():
    """Worst CVD Delta E and sub-3:1 contrasts from figs/palette_check.txt (the dataviz skill's validate_palette.js output)."""
    txt = (FIGS / "palette_check.txt").read_text(encoding="utf-8")
    parts = re.split(r"^## ", txt, flags=re.M)[1:]
    out = {}
    for name, part in zip(("slots3_adjacent", "slots3_all_pairs", "slots4_adjacent"), parts):
        cvd = re.search(r"CVD separation\s+worst [\w-]+ \S+ ΔE ([\d.]+)", part)
        con = re.search(r"Contrast vs surface.*?(\[\[.*\]\])", part)
        out[name] = {"worst_cvd_de": float(cvd.group(1)), "below_3to1": dict(json.loads(con.group(1))) if con else {},
                     "all_pass": "ALL CHECKS PASS" in part}
    out["validator"] = re.search(r"\(node (v[\d.]+)\)", txt).group(1)
    return out


def make_figures(out):
    plt = _plt()
    T = out["tasks"]
    pv = _pv
    figs = {}

    # 1. accuracy by task
    series = ("jev", "english", "multilingual")
    groups = list(T)
    vals = {t: {s: T[t]["systems"][s]["acc"] for s in series} for t in groups}
    cis = {t: {s: T[t]["systems"][s]["wilson"] for s in series} for t in groups}
    nlab = {"T1": "n=120 (40 case)", "T7": "n=100 (20 ids x 5 languages)"}
    verdict_en = {"Jev 유의 우세": "Jev significantly better", "Laya 유의 우세": "Laya significantly better", "비유의": "not significant"}
    fig = plt.figure(figsize=(16, 9), dpi=100)
    ax = fig.add_axes([0.205, 0.085, 0.57, 0.715])
    ax.set_xlim(0, 1.0)
    ax.set_ylim(len(groups) - 0.5, -0.5)
    _frame(ax, [0, 0.2, 0.4, 0.6, 0.8, 1.0], "Accuracy (bars), Wilson 95% CI (thin lines)")
    _grouped(ax, groups, series, vals, cis)
    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels(["%s %s\n%s" % (t, T[t]["name"].replace(" x5", ""), nlab.get(t, "n=%d" % T[t]["systems"]["jev"]["n"])) for t in groups],
                       fontsize=11.5, linespacing=1.35)
    for gi, t in enumerate(groups):
        b = T[t]["best_laya"]
        m = T[t]["mcnemar"][b]
        ax.text(1.03, gi - 0.13, verdict_en[T[t]["verdict"]], transform=ax.get_yaxis_transform(), fontsize=11, color=INK["primary"], va="center")
        ax.text(1.03, gi + 0.15, "vs %s  b/c %d/%d, %s, Holm %s" % (b, m["b"], m["c"], pv(m["p"]), pv(T[t]["holm_p"])[2:]),
                transform=ax.get_yaxis_transform(), fontsize=10, color=INK["secondary"], va="center")
    ax.text(1.03, -0.62, "Verdict vs best zero-shot Laya: exact McNemar", transform=ax.get_yaxis_transform(), fontsize=10,
            color=INK["muted"], va="center")
    _titles(fig, "Accuracy by task: Jev (playground) vs Laya zero-shot",
            "Same state bytes, same question, same options. n=%d per task (T1: %d cases, %d comparable decisions; T7: the same %d ids x %d languages).\n"
            "Wilson intervals for T1·T7 ignore the case/id clusters and are too narrow (summary.md §4.4, cluster bootstrap). Router bars are in the tables only."
            % (T["T2"]["systems"]["jev"]["n"], T["T1"]["extra"]["cases"], T["T1"]["systems"]["jev"]["n"],
               out["aggregate"]["cluster_bootstrap"]["T7"]["multilingual"]["clusters"], len(LANGS)))
    _legend(fig, series)
    _save(fig, "accuracy_by_task")
    plt.close(fig)
    figs["accuracy_by_task"] = {"series": list(series), "groups": groups, "values": vals, "wilson": cis}

    # 2. T7 by language
    series = ("jev", "english", "multilingual", "router")
    pl = T["T7"]["extra"]["per_lang"]
    vals = {L: {s: pl[L][s]["acc"] for s in series} for L in LANGS}
    cis = {L: {s: pl[L][s]["wilson"] for s in series} for L in LANGS}
    fig = plt.figure(figsize=(16, 9), dpi=100)
    ax = fig.add_axes([0.11, 0.085, 0.63, 0.715])
    ax.set_xlim(0, 1.0)
    ax.set_ylim(len(LANGS) - 0.5, -0.5)
    _frame(ax, [0, 0.2, 0.4, 0.6, 0.8, 1.0], "Accuracy (bars), Wilson 95% CI (thin lines), n=20 per language")
    _grouped(ax, LANGS, series, vals, cis, slot=0.2, bar=0.18)
    ax.set_yticks(range(len(LANGS)))
    ax.set_yticklabels(LANGS, fontsize=13)
    for gi, L in enumerate(LANGS):
        for k, m in enumerate(("english", "multilingual")):
            x = pl[L][m]["mcnemar"]
            ax.text(1.03, gi + (k - 0.5) * 0.26, "Jev vs %s  b/c %d/%d, %s" % (m, x["b"], x["c"], pv(x["p"])),
                    transform=ax.get_yaxis_transform(), fontsize=10.5, color=INK["secondary"], va="center")
    ax.text(1.03, -0.62, "Exact McNemar per language (same 20 ids)", transform=ax.get_yaxis_transform(), fontsize=10, color=INK["muted"], va="center")
    ra = T["T7"]["router_answered_by"]
    _titles(fig, "T7 MASSIVE intent-10: accuracy by language (same 20 ids, 10 options with English keys)",
            "Jev: %.2f~%.2f in all 5 languages; Laya: %.2f~%.2f depending on language and checkpoint. With n=%d per language, sizes are directional signals.\n"
            "Router assignment: %s (total english %d, multilingual %d)."
            % (min(vals[L]["jev"] for L in LANGS), max(vals[L]["jev"] for L in LANGS), min(vals[L][s] for L in LANGS for s in series[1:]),
               max(vals[L][s] for L in LANGS for s in series[1:]), pl["en"]["jev"]["n"],
               ", ".join("%s %s" % (L, " / ".join("%s %d" % (k, n) for k, n in sorted(T["T7"]["router_by_set"]["T7_massive_intent_10opt_%s_20" % L].items(), key=lambda kv: -kv[1])))
                         for L in LANGS), ra["english"], ra["multilingual"]))
    _legend(fig, series)
    _save(fig, "t7_languages")
    plt.close(fig)
    figs["t7_languages"] = {"series": list(series), "groups": list(LANGS), "values": vals, "wilson": cis}

    # 3. latency by deployment shape (log scale dot plot)
    lt, E = out["latency_tokens"], {k: v["value"] for k, v in out["external"].items()}
    one, multi = lt["single_all"], lt["by_type"]["multi"]
    rows = [("Hosted: Jev via the playground (internet, %d s between requests)" % out["meta"]["methods"]["pacing_guard_s"], None),
            ("Jev displayed 'server + network', 1 question per request (n=%d)" % one["requests"], ("jev", True, one["displayed_ms"])),
            ("Jev displayed, 2-4 questions per request (T1, n=%d)" % multi["requests"], ("jev", False, multi["displayed_ms"])),
            ("Jev browser POST round trip, 1 question per request (n=%d)" % one["requests"], ("jev", True, one["browser_post_ms"])),
            ("Jev browser POST round trip, 2-4 questions per request (T1, n=%d)" % multi["requests"], ("jev", False, multi["browser_post_ms"])),
            ("Third-party published Jev p50 (quoted in upstream README)", ("band", None, {"lo": E["readme_jev_p50_lo"], "hi": E["readme_jev_p50_hi"]})),
            ("Local HTTP loopback: Laya (Apple M4 Pro, back-to-back calls)", None),
            ("laya-serve multilingual, MPS, 1 question (D6)", ("multilingual", True, {"median": E["d6_mps_1q_c1_p50"]})),
            ("laya-serve multilingual, CPU 10 threads, 1 question (D6)", ("multilingual", True, {"median": E["d6_cpu_1q_c1_p50"]})),
            ("P2 /poc/decide ft-v1 (multilingual-based), MPS, 1 question", ("multilingual", True, {"median": E["p2_poc_decide_p50"]})),
            ("In-process: Laya (Apple M4 Pro, short state, 1 question)", None),
            ("english, CPU fp32 10 threads, back-to-back (D1)", ("english", True, {"median": E["d1_english_cpu_1q"]})),
            ("english, MPS, back-to-back (D1)", ("english", True, {"median": E["d1_english_mps_1q"]})),
            ("multilingual, CPU fp32 10 threads, back-to-back (D1)", ("multilingual", True, {"median": E["d1_multilingual_cpu_1q"]})),
            ("multilingual, MPS, back-to-back (D1)", ("multilingual", True, {"median": E["d1_multilingual_mps_1q"]})),
            ("multilingual, CPU, intermittent calls 1 s apart (D1c)", ("multilingual", True, {"median": E["d1c_multilingual_cpu_1q_gap1000"]})),
            ("multilingual, MPS, intermittent calls 1 s apart (D1c)", ("multilingual", True, {"median": E["d1c_multilingual_mps_1q_gap1000"]}))]
    fig = plt.figure(figsize=(16, 9), dpi=100)
    ax = fig.add_axes([0.335, 0.085, 0.6, 0.715])
    ax.set_xscale("log")
    ax.set_xlim(8, 1100)
    ax.set_ylim(len(rows) - 0.5, -0.5)
    _frame(ax, [10, 20, 50, 100, 200, 500, 1000], "Latency (ms, log axis). Dot = median, thin line = Jev requests p5~p95")
    ax.set_xticklabels(["10", "20", "50", "100", "200", "500", "1000"])
    from matplotlib.ticker import NullLocator
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=11)
    plotted = []
    for i, (lab, spec) in enumerate(rows):
        if spec is None:
            ax.get_yticklabels()[i].set_fontweight("bold")
            ax.get_yticklabels()[i].set_color(INK["primary"])
            continue
        s, filled, st = spec
        if s == "band":
            ax.fill_betweenx([i - 0.22, i + 0.22], st["lo"], st["hi"], color=INK["muted"], alpha=0.35, linewidth=0, zorder=2)
            ax.text(st["hi"] * 1.06, i, "%g~%g ms" % (st["lo"], st["hi"]), va="center", fontsize=10.5, color=INK["secondary"])
            plotted.append({"row": lab, "lo": st["lo"], "hi": st["hi"]})
            continue
        if "p5" in st:
            ax.plot([st["p5"], st["p95"]], [i, i], color=PAL[s], linewidth=2, zorder=3, solid_capstyle="round")
        ax.scatter([st["median"]], [i], s=110, zorder=5, facecolor=PAL[s] if filled else INK["surface"], edgecolor=PAL[s] if not filled else INK["surface"],
                   linewidth=2.2)
        ax.text((st.get("p95") or st["median"]) * 1.07, i, "%g ms" % st["median"], va="center", fontsize=10.5, color=INK["secondary"])
        plotted.append({"row": lab, "system": s, "filled": filled, "median": st["median"], **({"p5": st["p5"], "p95": st["p95"]} if "p5" in st else {})})
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    hand = [Line2D([], [], marker="o", linestyle="none", markersize=10, markerfacecolor=PAL[s], markeredgecolor=INK["surface"], label=l)
            for s, l in (("jev", "Jev (playground)"), ("english", "Laya english"), ("multilingual", "Laya multilingual family (incl. ft-v1)"))]
    hand += [Line2D([], [], marker="o", linestyle="none", markersize=10, markerfacecolor=INK["surface"], markeredgecolor=INK["secondary"],
                    markeredgewidth=2, label="Hollow dot: 2-4 questions per request (Jev T1)"), Patch(facecolor=INK["muted"], alpha=0.35, label="Third-party published Jev p50 range")]
    fig.legend(handles=hand, loc="upper left", bbox_to_anchor=(0.02, 0.845), ncol=5, frameon=False, fontsize=11, labelcolor=INK["secondary"],
               columnspacing=1.4, handletextpad=0.5)
    _titles(fig, "Latency: the deployment shapes differ (not a model speed comparison)",
            "Jev values are round trips to a hosted service over the internet (displayed = 'server + network' measured by the playground server; POST = browser resource timing).\n"
            "Laya values are in-process calls and localhost HTTP on the same machine (quoted from results/D/D_summary_20261003.md, results/poc/P2_20261003.md).")
    _save(fig, "latency")
    plt.close(fig)
    figs["latency"] = {"rows": plotted}
    figs["palette"] = palette_check()
    return figs


def jo(s, pair):
    """Attach a Korean particle pair (with-final-consonant form, without form) by the reading of the last character."""
    last = s.rstrip()[-1]
    if last.isdigit():
        bat, rieul = last in "013678", last in "178"  # 영/십/백/천, 일, 삼, 육, 칠, 팔
    elif "가" <= last <= "힣":
        code = (ord(last) - 0xAC00) % 28
        bat, rieul = code != 0, code == 8
    else:
        bat, rieul = False, False
    if pair == ("으로", "로"):
        return s + ("로" if not bat or rieul else "으로")
    return s + (pair[0] if bat else pair[1])


def render_md(o):
    T, A, R, LT, REF, M = o["tasks"], o["aggregate"], o["robustness"], o["latency_tokens"], o["references"], o["meta"]
    E = {k: v["value"] for k, v in o["external"].items()}
    Q, C, MAC, POOL, CB = M["requests"], o["calibration"], A["macro"], A["pooled_mcnemar"], A["cluster_bootstrap"]
    f3 = lambda x: "%.3f" % x  # noqa: E731
    ci = lambda w: "[%.3f, %.3f]" % (w[0], w[1])  # noqa: E731
    sg = lambda x: ("%+.3f" % x).replace("-", "−")  # noqa: E731
    sci = lambda w: "[%s, %s]" % (sg(w[0]), sg(w[1]))  # noqa: E731
    pv = lambda p: ("%.1e" % p) if p < 0.0001 else ("%.4f" % p)  # noqa: E731
    g = lambda x: "%g" % x  # noqa: E731
    acc = lambda s: "%d/%d = %.3f %s" % (s["correct"], s["n"], s["acc"], ci(s["wilson"]))  # noqa: E731
    pct = lambda x: "%.0f%%" % (100 * x)  # noqa: E731
    lab = {"english": "english", "multilingual": "multilingual", "router": "Router"}
    S = lambda t, s: T[t]["systems"][s]  # noqa: E731
    best = lambda t: T[t]["best_laya"]  # noqa: E731
    mb = lambda t: T[t]["mcnemar"][best(t)]  # noqa: E731
    L = []
    w = L.append
    v = A["verdicts"]
    vh = A["verdicts_holm"]
    sig = [t for t in T if T[t]["verdict"] == "Jev 유의 우세"]
    ns = [t for t in T if T[t]["verdict"] == "비유의"]
    sigh = [t for t in T if T[t]["verdict_holm"] == "Jev 유의 우세"]
    jc = C["jev"]
    rq = Q["by_session"]

    w("# Laya vs Jev 통제 비교 종합 (S6, 2026-10-07)\n")
    w("> 독립 제3자 플레이그라운드(jevplayground.com) 경유이며 API가 아니다. 모델 버전은 표기되지 않는다(Model ID `typesafe-ai/jev`). "
      "과제당 n=%d의 소표본이다. 이 문서의 모든 수치는 `results/F/jev_cmp/summary.json`과 같고, `s6_summary.py verify`가 세션 요약과 "
      "`jev_cmp.py` 재생성 출력에 대조했다(§10).\n" % S("T2", "jev")["n"])
    w("**판정.**")
    w("1. 과제마다 Jev를 그 과제에서 정확도가 가장 높은 zero-shot Laya 러너와 exact McNemar(양측, α %s)로 비교하면 Jev 유의 우세 %d개(%s), "
      "비유의 %d개(%s), Laya 유의 우세 %d개다. 8개 검정에 Holm 보정을 하면 Jev 유의 우세는 %s의 %d개만 남는다."
      % (g(M["methods"]["alpha"]), v.get("Jev 유의 우세", 0), ", ".join(sig), v.get("비유의", 0), ", ".join(ns), v.get("Laya 유의 우세", 0),
         "·".join(sigh), vh.get("Jev 유의 우세", 0)))
    w("2. %d과제 macro 정확도는 Jev %s, Laya english %s, multilingual %s, Router %s. 과제 %d개를 재표본한 paired bootstrap(%s회)에서 "
      "Jev − Router는 %s %s, Jev − 과제별 최고 Laya(사후 선택)는 %s %s다. 이질적인 %d과제를 평균한 기술통계다."
      % (len(T), f3(MAC["acc"]["jev"]), f3(MAC["acc"]["english"]), f3(MAC["acc"]["multilingual"]), jo(f3(MAC["acc"]["router"]), ("이다", "다")), len(T),
         "{:,}".format(MAC["resamples"]), sg(MAC["diff"]["router"]["diff"]), sci(MAC["diff"]["router"]["ci"]), sg(MAC["diff"]["best"]["diff"]),
         sci(MAC["diff"]["best"]["ci"]), len(T)))
    pb = POOL["best"]
    w("3. 서로 독립인 단일 문항 %d개(%s, T6은 argmax)를 합치면 Jev %d, 과제별 최고 Laya %d이고 b/c %d/%d, exact McNemar p=%s. "
      "군집이 있는 T1(case %d개)과 T7(id %d개)은 군집 bootstrap으로 따로 보며, Jev − 최고 Laya는 T1 %s %s, T7 %s %s다."
      % (pb["n"], "·".join(POOLED_TASKS), pb["jev_correct"], pb["laya_correct"], pb["b"], pb["c"], jo(pv(pb["p"]), ("이다", "다")), CB["T1"]["english"]["clusters"],
         CB["T7"]["multilingual"]["clusters"], sg(CB["T1"][best("T1")]["diff"]), sci(CB["T1"][best("T1")]["ci"]),
         sg(CB["T7"][best("T7")]["diff"]), sci(CB["T7"][best("T7")]["ci"])))
    w("4. Jev 확률의 의미는 문항 형식마다 다르다. 단일 choice는 100%% 표시가 %s이고 오답의 %s가 top ≥ 0.90이다. Boolean은 100%% 표시가 %d건이고, "
      "T8에서는 오답 %d개가 모두 미탐(FN)이다. 다문항(T1)은 평균 top %s 정확도 %s보다 낮은 과소확신이다. 확신도로 자동 처리 여부를 가르려면 "
      "과제별 held-out 데이터로 임계값을 따로 맞춰야 한다."
      % (pct(jc["single_choice"]["top100_share"]), pct(jc["single_choice"]["wrong_ge90_share"]), jc["single_boolean"]["top100"],
         T["T8"]["extra"]["jev"]["fn"], jo(f3(jc["multi"]["mean_top"]), ("이", "가")), f3(jc["multi"]["acc"])))
    rt, rk = REF["t1_typed_decisions"], REF["ko_pilot"]
    w("5. Laya의 열세는 zero-shot 형식 일반화에서 나오고 파인튜닝으로 닫힌다. T1의 typed-decisions 파인튜닝 체크포인트는 %s Jev(%d/%d)와 같고"
      "(b/c %d/%d), 한국어 도메인 라우팅 ft-v1은 같은 %d행에서 %s Jev(%d/%d) 이상이다. 두 줄 모두 zero-shot이 아닌 참고선이다(§3).\n"
      % (jo("%d/%d" % (rt["correct"], rt["n"]), ("으로", "로")), S("T1", "jev")["correct"], S("T1", "jev")["n"], rt["mcnemar_vs_jev"]["b"], rt["mcnemar_vs_jev"]["c"],
         rk["n"], jo("%d/%d" % (rk["laya_ft_v1"], rk["n"]), ("으로", "로")), rk["jev"], rk["n"]))

    # 1
    w("## 1. 개요\n")
    w("| 항목 | 내용 | 출처 |")
    w("|---|---|---|")
    w("| 비교 단위 | 같은 state 바이트(Laya가 읽는 JSON 직렬화 문자열 `state_text`), 같은 질문 문장, 같은 옵션 문자열과 순서. 요청 body가 폼 payload와 바이트 단위로 같았던 요청 %d/%d | "
      "`docs/09_laya_vs_jev_plan.md` §4, `jev_runs_all.jsonl` `payload_exact`(공개 저장소에는 포함하지 않음) |" % (Q["payload_exact"], Q["master_records"]))
    w("| Jev | 공개 플레이그라운드 `%s`의 `%s`. Model ID `typesafe-ai/jev` %d/%d, 확률·score 소수 둘째 자리 반올림 %d/%d | 세션 run card, `jev_runs_all.jsonl`(공개 저장소에는 포함하지 않음) |"
      % (M["jev"]["site"], M["jev"]["endpoint"], M["jev"]["model_ids"]["typesafe-ai/jev"], Q["master_ok"], sum(M["jev"]["rounding"].values()), Q["master_ok"]))
    w("| Laya | laya %s, revision `55cf4c4`, english / multilingual / Router(입력별 자동 선택), zero-shot, %s | `results/F/jev_cmp/S0_20261006.md`, `laya_summary.md` |"
      % (M["laya"]["version"], M["laya"]["device"]))
    w("| 과제 | T1~T8, %d개. 과제당 n=%d, T1은 %d case의 비교 가능 decision %d개, T7은 같은 %d id x %d개 언어 = %d | `data/evals/jev_cmp/MANIFEST.json` |"
      % (len(T), S("T2", "jev")["n"], T["T1"]["extra"]["cases"], S("T1", "jev")["n"], CB["T7"]["multilingual"]["clusters"], M["methods"]["langs"], S("T7", "jev")["n"]))
    w("| 기간 (KST) | 2026-10-06: 파일럿 %s~%s, S1 %s~%s, S1b %s~%s. 2026-10-07: S2 %s~%s, S3 %s~%s, S4 %s~%s, S5 %s~%s (첫 클릭~마지막 클릭) | 세션 run card |"
      % ((Q["pilot_first_click"][:5], Q["pilot_last_click"][:5]) + tuple(x for s in SESSIONS for x in (rq[s]["first_click"][11:16], rq[s]["last_click"][11:16]))))
    w("| 요청 수 | 사이트 전체 %d회 = 마스터 로그 %d(S1 %d, S1b %d, S2 %d, S3 %d, S4 %d, S5 %d) + 도구화 이전 %d(한국어 파일럿 %d, 상태 확인 %d). 일자별 2026-10-06 %d, 2026-10-07 %d | "
      "`jev_runs_all.jsonl`, `results/F/jev_runs_raw.jsonl`(둘 다 공개 저장소에는 포함하지 않음), `S1_summary.md` §7 |"
      % ((Q["total_site"], Q["master_records"]) + tuple(rq[s]["requests"] for s in SESSIONS) + (Q["pre_tooling"], Q["pilot_requests"], Q["coordinator_checks"],
                                                                                              Q["by_day"]["2026-10-06"], Q["by_day"]["2026-10-07"])))
    w("| 간격 | Run 클릭 간격 최소 S1 %.1f s, S1b %.1f s, S2 %.1f s, S3 %.1f s, S4 %.1f s, S5 %.1f s(중앙 %.1f~%.1f s), 파일럿 %.1f s. 규칙 ≥ 10 s | 요청 기록 `gap_from_prev_click_s`(공개 저장소에는 포함하지 않음) |"
      % (tuple(rq[s]["gap_min_s"] for s in SESSIONS) + (min(rq[s]["gap_median_s"] for s in SESSIONS), max(rq[s]["gap_median_s"] for s in SESSIONS), Q["pilot_gap_min_s"])))
    w("| 오류 | HTTP 502 %d회: 파일럿 run 2(규칙대로 세션 중단, %.0f분 뒤 재개해 같은 행 성공), S2 run 1(`UNAVAILABLE`, %.1f s 뒤 같은 payload 1회 재시도 성공). "
      "HTTP 429 %d회, 제한 문구·captcha 0회 | `F_jev_20261006.md`, `S2_run_card.md` |" % (Q["http_502_total"], Q["pilot_resume_after_min"], Q["retries"][0]["gap_s"], Q["http_429_total"]))
    w("| 성공 요청 | 마스터 %d + 파일럿 %d. 아래 분석은 마스터 %d건(%d decision)과 파일럿 %d행 | 같은 곳 |\n"
      % (Q["master_ok"], Q["pilot_ok"], Q["master_ok"], LT["all"]["decisions"], REF["ko_pilot"]["n"]))

    # 2
    w("## 2. 과제별 결과\n")
    w("### 2.1 종합 표\n")
    w("| 과제 | n | 형식 / 옵션 | Laya 학습 믹스 | Jev | Laya english | Laya multilingual | Laya Router | Jev vs 최고 Laya: b/c, p (Holm p) | Brier Jev / 최고 Laya | ECE Jev / 최고 Laya | 판정 (Holm 후) |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    nlab = {"T1": "%d (%d case)" % (S("T1", "jev")["n"], T["T1"]["extra"]["cases"]), "T7": "%d (%d id x %d 언어)" % (S("T7", "jev")["n"], CB["T7"]["multilingual"]["clusters"], M["methods"]["langs"])}
    for t in T:
        b, m = best(t), mb(t)
        w("| %s %s | %s | %s / %s | %s | %s | %s | %s | %s | %s: %d/%d, %s (%s) | %s / %s | %s / %s | %s (%s) |" % (
            t, T[t]["name"].replace(" x5", ""), nlab.get(t, str(S(t, "jev")["n"])), T[t]["form"], T[t]["options"], T[t]["in_training_mix"],
            acc(S(t, "jev")), acc(S(t, "english")), acc(S(t, "multilingual")), acc(S(t, "router")), lab[b], m["b"], m["c"], pv(m["p"]), pv(T[t]["holm_p"]),
            f3(S(t, "jev")["brier"]), f3(S(t, b)["brier"]), f3(S(t, "jev")["ece"]), f3(S(t, b)["ece"]), T[t]["verdict"], T[t]["verdict_holm"]))
    w("")
    w("- 정확도 칸은 정답/n = 정확도 [Wilson 95%]다. b = Jev만 정답, c = Laya만 정답이고 p는 exact McNemar(양측)다. 최고 Laya는 english, multilingual, Router 중 정확도가 가장 높은 러너이고 "
      "동률이면 english, multilingual, Router 순으로 고른다(사후 선택이라 Laya에 유리하다, §9).")
    w("- 판정 규칙: p < %s이고 b > c면 Jev 유의 우세, c > b면 Laya 유의 우세, 아니면 비유의. 괄호는 같은 규칙을 8개 검정의 Holm 보정 p에 적용한 결과다." % g(M["methods"]["alpha"]))
    w("- Brier는 행마다 그 행의 옵션 전체로 Σ(p − onehot)²를 낸 평균이다(Boolean은 두 칸이라 2(p − y)², score는 5레벨, T1은 argmax gold 대비 one-hot). ECE는 %d bins, top p 기준이다. "
      "Jev 확률은 소수 둘째 자리 반올림이라 Brier·ECE에 약 ±%s의 하한 오차가 있다." % (M["methods"]["ece_bins"], g(M["methods"]["jev_rounding_err"])))
    w("- Router 배정: T1~T6은 전부 english, T7은 english %d / multilingual %d(en 20은 english, de는 multilingual 15 / english 5, ja·zh-CN·ko는 multilingual), T8은 english %d / multilingual %d."
      % (T["T7"]["router_answered_by"]["english"], T["T7"]["router_answered_by"]["multilingual"], T["T8"]["router_answered_by"]["english"], T["T8"]["router_answered_by"]["multilingual"]))
    w("- T1(%d case)과 T7(%d id)은 decision이 군집으로 묶여 있어 Wilson 구간과 item 단위 McNemar가 낙관적이다. 군집 bootstrap은 §4.4에 있다."
      % (T["T1"]["extra"]["cases"], CB["T7"]["multilingual"]["clusters"]))
    w("- 출처: `jev_cmp.py analyze`(T2~T8)와 `jev_cmp.py t1 S1,S2`(T1) 재생성 출력(공개 저장소에는 포함하지 않음), 세션 요약 `sessions/S1_20261006/S1_summary.md` §2, `S2_20261007/S2_summary.md` §2~§3, "
      "`S3_20261007/S3_summary.md` §2~§3, `S4_20261007/S4_summary.md` §2~§3, `S5_20261007/S5_summary.md` §2~§4. 학습 믹스는 MANIFEST `in_training_mix`다. upstream은 T2·T5만 Laya 학습 믹스(retention)로 적고 "
      "T3·T4·T6·T8은 held out, T1(typed-decisions)·T7(MASSIVE)은 두 체크포인트 모두 학습하지 않았다고 적는다"
      "(`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`; upstream 클론은 공개 저장소에는 포함하지 않음, "
      "`https://github.com/NandhaKishorM/laya`를 commit `4aa6761`로 clone하면 재현된다). 표의 no와 held out은 모두 학습 믹스에 없다는 뜻이다.\n")

    t1 = T["T1"]["extra"]
    w("### 2.2 T1 typed-decisions: 타입별 (같은 %d decision, %d case)\n" % (S("T1", "jev")["n"], t1["cases"]))
    w("| system | 전체 | choice (%d) | Boolean / noul (%d) | score 5레벨 (%d) | soft acc | Brier vs soft | score MAE (E[level] vs teacher, Jev는 반올림 p) |" % tuple(t1["by_type"][k]["jev"]["n"] for k in ("choice", "noul", "score")))
    w("|---|---|---|---|---|---|---|---|")
    for s, name in (("jev", "Jev"), ("english", "Laya english"), ("multilingual", "Laya multilingual"), ("router", "Laya Router"), ("typed-decisions", "참고: Laya typed-decisions (파인튜닝)")):
        w("| %s | %s | %s | %s | %s | %s | %s | %s |" % (name, acc(S("T1", s)), *(acc(t1["by_type"][k][s]) for k in ("choice", "noul", "score")),
                                                         f3(t1[s]["soft_acc"]), f3(t1[s]["brier_vs_soft"]), f3(t1[s]["score_mae"])))
    mt = t1["mcnemar_by_type"]
    w("")
    w("- 타입별 exact McNemar(b/c, p): english는 choice %d/%d (%s), noul %d/%d (%s), score %d/%d (%s). multilingual은 choice %d/%d (%s), noul %d/%d (%s), score %d/%d (%s). "
      "score 10개만 n이 작아 구분되지 않는다." % tuple(x for m in ("english", "multilingual") for k in ("choice", "noul", "score")
                                                    for x in (mt[m][k]["b"], mt[m][k]["c"], pv(mt[m][k]["p"]))))
    nn = t1["noul_nocrit"]
    w("- Jev Boolean에는 설명 칸이 없다. Laya에서 true/false criteria를 뺀 같은 입력 변형도 english %d/%d(b/c %d/%d), multilingual %d/%d(b/c %d/%d)로 차이가 그대로다."
      % (nn["english"]["correct"], nn["english"]["n"], nn["english"]["b"], nn["english"]["c"], nn["multilingual"]["correct"], nn["multilingual"]["n"], nn["multilingual"]["b"], nn["multilingual"]["c"]))
    w("- 이 %d decision의 문항별 최빈 기준선은 %s이고 Laya base 세 러너는 모두 그보다 낮다. Jev score MAE는 응답 `score` 필드 기준 %s다. 출처: `S2_summary.md` §2.\n"
      % (S("T1", "jev")["n"], f3(t1["majority"]), f3(t1["jev_score_mae_field"])))

    w("### 2.3 T5 BoolQ, T8 prompt-injections: Boolean 순위 품질\n")
    w("| 과제 | system | 정확도 (p(true) ≥ %s) | 예측 true (gold %d) | FN / FP | AUROC [bootstrap 95%%] | AUROC Jev − Laya [paired bootstrap 95%%] | 같은 40행 최적 임계값 정확도 (기술통계) |"
      % (g(M["methods"]["bool_threshold"]), T["T5"]["extra"]["gold_true"]))
    w("|---|---|---|---|---|---|---|---|")
    for t in ("T5", "T8"):
        X = T[t]["extra"]
        for s in ("jev",) + RUNNERS:
            w("| %s | %s | %s | %d | %d / %d | %s %s | %s | %d/%d |" % (
                t, SYS_LABEL[s], acc(S(t, s)), X[s]["pred_true"], X[s]["fn"], X[s]["fp"], f3(X[s]["auroc"]), ci(X[s]["auroc_ci"]),
                "-" if s == "jev" else "%s %s" % (sg(X[s]["auroc_diff"]), sci(X[s]["auroc_diff_ci"])), X[s]["best_thr_correct"], S(t, s)["n"]))
    x8 = T["T8"]["extra"]
    w("")
    w("- T8의 Jev는 이 40행에서 완전 분리다(gold false p(true) %s~%s, gold true %s~%s). 그래서 percentile bootstrap CI가 폭 0으로 퇴화했고 차이 CI도 낙관적이다. "
      "bootstrap은 항목 재표본 %s회, seed %d(`jev_cmp.py` 정의). 출처: `S3_summary.md` §3, `S5_summary.md` §4.\n"
      % (g(x8["jev_p_true_range_gold_false"][0]), g(x8["jev_p_true_range_gold_false"][1]), g(x8["jev_p_true_range_gold_true"][0]), g(x8["jev_p_true_range_gold_true"][1]),
         "{:,}".format(M["methods"]["jev_cmp_boot"]), M["methods"]["seed"]))

    x6 = T["T6"]["extra"]
    w("### 2.4 T6 SST-5: 레벨 적중과 척도 사용\n")
    w("| system | argmax 레벨 정확도 (주 지표) | 반올림 E[level] 정확도 (표시 규칙) | MAE of E[level] | 평균 E − gold | ±1 레벨 이내 | 예측 레벨 분포 0/1/2/3/4 (argmax, gold 각 %d) |" % x6["gold_levels"][0])
    w("|---|---|---|---|---|---|---|")
    for s in ("jev",) + RUNNERS:
        w("| %s | %s | %d/%d = %s %s | %s | %s | %s | %s |" % (SYS_LABEL[s], acc(S("T6", s)), x6[s]["rounded_correct"], S("T6", s)["n"], f3(x6[s]["rounded_acc"]),
                                                          ci(x6[s]["rounded_wilson"]), f3(x6[s]["mae"]), sg(x6[s]["mean_signed"]), f3(x6[s]["within1"]),
                                                          "/".join(str(c) for c in x6[s]["levels_argmax"])))
    w("")
    w("- Jev vs english: argmax b/c %d/%d p=%s(비유의), 반올림 E b/c %d/%d p=%s, MAE 차이 %s %s. Jev vs multilingual: argmax %d/%d p=%s, 반올림 E %d/%d p=%s, MAE 차이 %s %s. "
      "MAE 차이 CI는 항목 재표본 %s회, seed %d. 출처: `S4_summary.md` §2."
      % (T["T6"]["mcnemar"]["english"]["b"], T["T6"]["mcnemar"]["english"]["c"], pv(T["T6"]["mcnemar"]["english"]["p"]), x6["english"]["mcnemar_rounded"]["b"],
         x6["english"]["mcnemar_rounded"]["c"], pv(x6["english"]["mcnemar_rounded"]["p"]), sg(x6["english"]["mae_diff"]), sci(x6["english"]["mae_diff_ci"]),
         T["T6"]["mcnemar"]["multilingual"]["b"], T["T6"]["mcnemar"]["multilingual"]["c"], pv(T["T6"]["mcnemar"]["multilingual"]["p"]),
         x6["multilingual"]["mcnemar_rounded"]["b"], x6["multilingual"]["mcnemar_rounded"]["c"], pv(x6["multilingual"]["mcnemar_rounded"]["p"]),
         sg(x6["multilingual"]["mae_diff"]), sci(x6["multilingual"]["mae_diff_ci"]), "{:,}".format(M["methods"]["jev_cmp_boot"]), M["methods"]["seed"]))
    w("- Laya english가 마지막 레벨 4를 고른 행은 %d/%d이고 multilingual은 %d/%d행을 레벨 0·1로 냈다(gold는 레벨마다 %d행). 척도 압축이 Laya의 주된 실패다.\n"
      % (x6["english"]["levels_argmax"][-1], S("T6", "english")["n"], sum(x6["multilingual"]["levels_argmax"][:2]), S("T6", "multilingual")["n"], x6["gold_levels"][0]))

    pl = T["T7"]["extra"]["per_lang"]
    w("### 2.5 T7 MASSIVE intent-10: 언어별 (같은 %d id, 언어당 n=%d)\n" % (CB["T7"]["multilingual"]["clusters"], pl["en"]["jev"]["n"]))
    w("| system | %s | 합산 %d |" % (" | ".join(LANGS), S("T7", "jev")["n"]))
    w("|---|%s---|" % ("---|" * len(LANGS)))
    for s in ("jev",) + RUNNERS:
        w("| %s | %s | %s |" % (SYS_LABEL[s], " | ".join("%d/%d = %s" % (pl[L][s]["correct"], pl[L][s]["n"], f3(pl[L][s]["acc"])) for L in LANGS), acc(S("T7", s))))
    for m in RUNNERS:
        w("| Jev vs %s: b/c, p | %s | %d/%d, %s (독립 아님) |" % (lab[m], " | ".join("%d/%d, %s" % (pl[L][m]["mcnemar"]["b"], pl[L][m]["mcnemar"]["c"], pv(pl[L][m]["mcnemar"]["p"]))
                                                                               for L in LANGS), T["T7"]["mcnemar"][m]["b"], T["T7"]["mcnemar"][m]["c"], pv(T["T7"]["mcnemar"][m]["p"])))
    w("")
    w("- 옵션은 10개 영어 key 렌더링이고 발화만 언어별로 다르다. 합산 McNemar는 같은 id가 5번 들어가 독립 표본이 아니다. 출처: `S4_summary.md` §3, `S5_summary.md` §2~§3, "
      "`jev_cmp.py analyze S4,S5 <5개 세트>`(출력은 공개 저장소에는 포함하지 않음).\n")

    # 3
    p4 = REF["p4_domain8_test_half"]
    w("## 3. 참고선 (zero-shot 아님)\n")
    w("| 참고선 | 과제·표본 | 결과 | Jev 대비 | 출처 |")
    w("|---|---|---|---|---|")
    w("| Laya typed-decisions 체크포인트 (typed-decisions train으로 파인튜닝) | T1, 같은 %d decision | %s. choice %d/%d, noul %d/%d, score %d/%d, soft acc %s | Jev %s, b/c %d/%d, p=%s | `S2_summary.md` §2.1~§2.2 |"
      % (rt["n"], acc({**rt, "wilson": rt["wilson"]}), rt["by_type"]["choice"]["correct"], rt["by_type"]["choice"]["n"], rt["by_type"]["noul"]["correct"], rt["by_type"]["noul"]["n"],
         rt["by_type"]["score"]["correct"], rt["by_type"]["score"]["n"], f3(rt["soft_acc"]), acc(S("T1", "jev")), rt["mcnemar_vs_jev"]["b"], rt["mcnemar_vs_jev"]["c"], pv(rt["mcnemar_vs_jev"]["p"])))
    w("| Laya ft-v1 (한국어 domain_8 train으로 파인튜닝) | 한국어 도메인 라우팅 파일럿 %d행 (`key: 한국어 설명` 8옵션) | %d/%d = %s %s. 같은 행 zero-shot multilingual %d/%d = %s | "
      "Jev %d/%d = %s %s. Jev vs ft-v1 b/c %d/%d, p=%s. Jev vs zero-shot %d/%d, p=%s | `results/F/jev_playground_manual_20261006.md` §3 |"
      % (rk["n"], rk["laya_ft_v1"], rk["n"], f3(rk["laya_ft_v1"] / rk["n"]), ci(rk["ft_wilson"]), rk["laya_zero_shot"], rk["n"], f3(rk["laya_zero_shot"] / rk["n"]),
         rk["jev"], rk["n"], f3(rk["jev"] / rk["n"]), ci(rk["jev_wilson"]), rk["mcnemar_jev_vs_ft"]["b"], rk["mcnemar_jev_vs_ft"]["c"], pv(rk["mcnemar_jev_vs_ft"]["p"]),
         rk["mcnemar_jev_vs_zs"]["b"], rk["mcnemar_jev_vs_zs"]["c"], pv(rk["mcnemar_jev_vs_zs"]["p"])))
    w("| Laya ft-v1 | ko_massive_domain_8 test 절반 %d행 | %s %s (bootstrap CI). 같은 행 zero-shot multilingual %s %s | Jev는 이 %d행을 받지 않았다 | `results/P4/metrics/full_20261003-1156_summary.md:19` |"
      % (p4["ft_v1"]["n"], f3(p4["ft_v1"]["acc"]), ci(p4["ft_v1"]["ci"]), f3(p4["multilingual_zero_shot"]["acc"]), ci(p4["multilingual_zero_shot"]["ci"]), p4["ft_v1"]["n"]))
    w("")
    w("- 두 파인튜닝 선은 같은 분포의 train으로 학습했다. 학습 데이터가 없는 zero-shot 시스템(Jev)과의 비교에서 in-domain 이점을 가진다. 파일럿에서 Jev가 ft-v1에 진 %d행은 라벨 설명에 없는 "
      "MASSIVE 관례(`play` → `media`)였고 ft-v1은 이를 학습했다(파일럿 §4). T7은 intent 과제라 ft-v1을 T7 참고선으로 두지 않았다(docs/09 열린 질문 5).\n" % rk["mcnemar_jev_vs_ft"]["c"])

    # 4
    w("## 4. 종합\n")
    w("### 4.1 판정 집계 (%d과제, Jev vs 최고 zero-shot Laya)\n" % len(T))
    w("| 기준 | Jev 유의 우세 | 비유의 | Laya 유의 우세 |")
    w("|---|---|---|---|")
    w("| exact McNemar, 보정 전 α %s | %d (%s) | %d (%s) | %d |" % (g(M["methods"]["alpha"]), v.get("Jev 유의 우세", 0), ", ".join(sig), v.get("비유의", 0), ", ".join(ns), v.get("Laya 유의 우세", 0)))
    w("| Holm 보정 (8개 검정) | %d (%s) | %d (%s) | %d |" % (vh.get("Jev 유의 우세", 0), ", ".join(sigh), vh.get("비유의", 0),
                                                          ", ".join(t for t in T if T[t]["verdict_holm"] == "비유의"), vh.get("Laya 유의 우세", 0)))
    w("")
    w("Holm 보정 p: %s. T6은 주 지표(argmax)로 비유의이지만 보조 지표(반올림 E, MAE)로는 Jev 쪽 차이가 0을 벗어난다(§2.4).\n"
      % ", ".join("%s %s" % (t, pv(T[t]["holm_p"])) for t in sorted(T, key=lambda k: T[k]["holm_p"])))
    w("### 4.2 macro 평균 정확도 (%d과제 단순 평균)\n" % len(T))
    w("| system | macro 정확도 | Jev − system [과제 bootstrap 95%%] | bootstrap에서 차이 ≤ 0 비율 | T1 제외 %d과제 macro |" % (len(T) - 1))
    w("|---|---|---|---|---|")
    w("| Jev | %s | - | - | %s |" % (f3(MAC["acc"]["jev"]), f3(MAC["without_T1"]["jev"])))
    for s, name in (("english", "Laya english"), ("multilingual", "Laya multilingual"), ("router", "Laya Router"), ("best", "과제별 최고 Laya (사후 선택)")):
        d = MAC["diff"][s]
        w("| %s | %s | %s %s | %s | %s |" % (name, f3(MAC["acc"][s]), sg(d["diff"]), sci(d["ci"]), "%.4f" % d["share_le0"], f3(MAC["without_T1"][s])))
    w("")
    w("- 과제별 정확도(T1은 120 decision, T7은 100 항목 합산)를 같은 가중치로 평균했다. bootstrap은 %d개 과제를 복원 재표본(%s회, seed %d)해 Jev − Laya의 평균을 다시 계산한 percentile 구간이다. "
      "과제가 %d개뿐이고 서로 이질적이라 모집단 추론이 아니라 기술통계다." % (len(T), "{:,}".format(MAC["resamples"]), MAC["seed"], len(T)))
    w("- T1(차이가 가장 큰 과제)을 빼도 Jev가 앞선다(Jev %s vs 최고 Laya %s).\n" % (f3(MAC["without_T1"]["jev"]), f3(MAC["without_T1"]["best"])))
    w("### 4.3 독립 단일 문항 합산 exact McNemar (%s, %d항목)\n" % ("·".join(POOLED_TASKS), pb["n"]))
    w("| Laya 비교 대상 | Jev 정답 | Laya 정답 | b | c | exact p | 과제별 b/c (%s) |" % " / ".join(POOLED_TASKS))
    w("|---|---|---|---|---|---|---|")
    for k, name in (("best", "과제별 최고 Laya (사후 선택)"), ("english", "english 고정"), ("multilingual", "multilingual 고정"), ("router", "Router 고정")):
        x = POOL[k]
        w("| %s | %d/%d | %d/%d | %d | %d | %s | %s |" % (name, x["jev_correct"], x["n"], x["laya_correct"], x["n"], x["b"], x["c"], pv(x["p"]),
                                                         " / ".join("%d/%d" % (x["per_task"][t]["b"], x["per_task"][t]["c"]) for t in POOLED_TASKS)))
    w("")
    w("- 항목이 과제를 넘어 독립이라고 보고 합친 검정이다. 과제별 최고 러너 선택은 Laya에 유리한 사후 선택이고, 고정 러너 세 줄이 그 민감도다. T1·T7은 군집 때문에 넣지 않았다.\n")
    w("### 4.4 군집 과제: T1 (case 군집), T7 (id 군집)\n")
    w("| 과제 | 군집 | Laya | 정확도 차이 Jev − Laya | 군집 bootstrap 95% | 참고: item 단위 McNemar b/c, p (독립 가정) |")
    w("|---|---|---|---|---|---|")
    for t, cl in (("T1", "%d case, %d decision" % (CB["T1"]["english"]["clusters"], CB["T1"]["english"]["items"])),
                  ("T7", "%d id x %d 언어 = %d" % (CB["T7"]["english"]["clusters"], M["methods"]["langs"], CB["T7"]["english"]["items"]))):
        for m in RUNNERS:
            x = CB[t][m]
            w("| %s | %s | %s%s | %s | %s | %d/%d, %s |" % (t, cl, lab[m], " (최고)" if m == best(t) else "", sg(x["diff"]), sci(x["ci"]), T[t]["mcnemar"][m]["b"],
                                                          T[t]["mcnemar"][m]["c"], pv(T[t]["mcnemar"][m]["p"])))
    w("")
    w("- 군집을 복원 재표본(%s회, seed %d)하고 뽑힌 군집의 decision 전체로 정답 수 차이를 다시 계산했다. 모든 구간이 0을 포함하지 않는다.\n" % ("{:,}".format(N_CLUSTER_BOOT), SEED))

    # 5
    w("## 5. 보정과 확신도\n")
    w("### 5.1 과제별 Brier·ECE와 과대/과소확신\n")
    w("| 과제 | Jev Brier | Jev ECE | Jev 평균 top − 정확도 | Jev 오답 중 top ≥ 0.90 | 최고 Laya | Laya Brier | Laya ECE | Laya 평균 top − 정확도 | Laya 오답 중 top ≥ 0.90 |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for t in T:
        j, b = S(t, "jev"), S(t, best(t))
        w("| %s | %s | %s | %s | %d/%d | %s | %s | %s | %s | %d/%d |" % (t, f3(j["brier"]), f3(j["ece"]), sg(j["gap_top_minus_acc"]), j["wrong_ge90"], j["wrong"], lab[best(t)],
                                                                         f3(b["brier"]), f3(b["ece"]), sg(b["gap_top_minus_acc"]), b["wrong_ge90"], b["wrong"]))
    w("")
    w("평균 top − 정확도 > 0은 과대확신, < 0은 과소확신이다. Jev의 top은 표시 확률(2자리 반올림), Laya는 `answer_confidence`(Boolean은 max(p, 1 − p), score는 최대 레벨 확률)다.\n")
    w("### 5.2 Jev 확신도: 문항 형식별\n")
    w("| 형식 | 과제 | n | 정확도 | 평균 top | 100% 표시 | 오답 | 오답 중 top ≥ 0.90 |")
    w("|---|---|---|---|---|---|---|---|")
    for k, name in (("single_choice", "단일 choice"), ("single_boolean", "단일 Boolean"), ("single_score", "단일 score"), ("multi", "Multiple questions (2~4문항)")):
        x = jc[k]
        w("| %s | %s | %d | %s | %s | %d (%s) | %d | %d (%s) |" % (name, "·".join(x["tasks"]), x["n"], f3(x["acc"]), f3(x["mean_top"]), x["top100"], pct(x["top100_share"]),
                                                                x["wrong"], x["wrong_ge90"], pct(x["wrong_ge90_share"])))
    x5, ct = T["T5"]["extra"], t1["jev_conf_by_type"]
    w("")
    w("- **단일 choice**: 100%% 표시가 흔하고 오답 다수가 0.90 이상이다(T2 %d/%d, T3 %d/%d, T4 %d/%d, T7 %d/%d). T3에서는 정답 옵션을 0%%로 표시한 행이 %d/%d다. "
      "top 확률 임계값으로 오답을 거르기 어렵다."
      % (S("T2", "jev")["wrong_ge90"], S("T2", "jev")["wrong"], S("T3", "jev")["wrong_ge90"], S("T3", "jev")["wrong"], S("T4", "jev")["wrong_ge90"], S("T4", "jev")["wrong"],
         S("T7", "jev")["wrong_ge90"], S("T7", "jev")["wrong"], S("T3", "jev")["gold_shown0"], S("T3", "jev")["n"]))
    w("- **Boolean**: 100%% 표시가 없다(0/%d). 임계값의 적정 위치는 과제마다 다르다. T5는 예측 true %d(gold %d)로 0.5가 거의 최적이고(0.5에서 %d/%d, 같은 40행 최적 %d/%d), "
      "오답 %d개가 모두 top < 0.90이다. T8은 예측 true %d(gold %d)이고 오답 %d개가 전부 미탐이며, gold false의 p(true)가 %s 이하라 최적 임계값이 0.5보다 훨씬 낮다(%s 초과 %s 이하에서 %d/%d)."
      % (jc["single_boolean"]["n"], x5["jev"]["pred_true"], x5["gold_true"], S("T5", "jev")["correct"], S("T5", "jev")["n"], x5["jev"]["best_thr_correct"], S("T5", "jev")["n"],
         S("T5", "jev")["wrong"], x8["jev"]["pred_true"], x8["gold_true"], x8["jev"]["fn"], g(x8["jev_p_true_range_gold_false"][1]),
         g(x8["jev_p_true_range_gold_false"][1]), g(x8["jev_p_true_range_gold_true"][0]), x8["jev"]["best_thr_correct"], S("T8", "jev")["n"]))
    w("- **Multiple questions (T1)**: 과소확신이다. 타입별 평균 top(정답 / 오답)은 choice %s / %s, noul %s / %s, score %s / %s이고 오답 %d개 중 top ≥ 0.90은 %d개뿐이다. "
      "여기서는 낮은 top이 오답 신호라 보류 임계값이 작동할 여지가 있다."
      % (f3(ct["choice"]["mean_top_right"]), f3(ct["choice"]["mean_top_wrong"]), f3(ct["noul"]["mean_top_right"]), f3(ct["noul"]["mean_top_wrong"]),
         f3(ct["score"]["mean_top_right"]), f3(ct["score"]["mean_top_wrong"]), jc["multi"]["wrong"], jc["multi"]["wrong_ge90"]))
    w("- **score (T6)**: 100%% 표시 0/%d, 오답 %d개 모두 top < 0.90, 평균 top %s vs 정확도 %s로 약한 과대확신이다.\n"
      % (S("T6", "jev")["n"], S("T6", "jev")["wrong"], f3(S("T6", "jev")["mean_top"]), f3(S("T6", "jev")["acc"])))
    bl = C["best_laya"]
    w("### 5.3 Laya 확신도\n")
    under = [t for t in T if S(t, best(t))["gap_top_minus_acc"] < 0]
    w("- 최고 Laya 러너를 형식별로 묶으면 모두 과대확신이다(평균 top − 정확도: 단일 choice %s, Boolean %s, score %s, T1 %s). 과제별로 과소확신은 %s뿐이다. "
      "오답 중 top ≥ 0.90은 단일 choice %d/%d, Boolean %d/%d다."
      % (sg(bl["single_choice"]["gap"]), sg(bl["single_boolean"]["gap"]), sg(bl["single_score"]["gap"]), sg(bl["multi"]["gap"]),
         ", ".join("%s %s(%s)" % (t, lab[best(t)], sg(S(t, best(t))["gap_top_minus_acc"])) for t in under), bl["single_choice"]["wrong_ge90"],
         bl["single_choice"]["wrong"], bl["single_boolean"]["wrong_ge90"], bl["single_boolean"]["wrong"]))
    w("- 형식이나 언어가 낯설수록 확신한 채로 틀린다. T7 de에서 english ECE %s, multilingual %s이고, T8 english는 p(true)가 정확히 0 또는 1인 행이 %d/%d다. "
      "multilingual은 T6에서 레벨 0·1로 몰리면서 오답 %d개 중 %d개를 0.90 이상으로 냈다(`S4_summary.md` §2.5)."
      % (f3(pl["de"]["english"]["ece"]), f3(pl["de"]["multilingual"]["ece"]),
         x8["english"]["p_extreme"], S("T8", "english")["n"], S("T6", "multilingual")["wrong"], S("T6", "multilingual")["wrong_ge90"]))
    w("- Laya english의 T2 ECE %s처럼 학습 믹스 과제에서는 보정이 양호하다. upstream은 도메인별 temperature fitting 뒤 ECE를 보고한다(README \"Where Jev leads\").\n"
      % f3(S("T2", "english")["ece"]))
    w("### 5.4 확신도 기반 자동화에 대한 함의\n")
    w("- 같은 \"%.0f%%\"가 Jev 단일 choice에서는 오답을 거르지 못하고(오답의 %s가 0.90 이상), Jev T1에서는 대부분의 오답을 거른다. Boolean은 임계값 자체가 과제마다 다른 자리에 있다."
      % (100 * M["methods"]["conf_hi"], pct(jc["single_choice"]["wrong_ge90_share"])))
    w("- 따라서 두 시스템 모두 과제(질문 형식, 옵션 수, 언어)별 held-out 표본으로 임계값이나 temperature를 맞추고, coverage@오류를 확인한 뒤 자동 처리 범위를 정해야 한다. "
      "이 문서의 최적 임계값 열은 같은 40행에서 고른 기술통계라 그대로 쓰면 안 된다.\n")

    # 6
    det, oo = R["determinism"], R["option_order"]
    w("## 6. 견고성\n")
    w("| 점검 | Jev | Laya | 출처 |")
    w("|---|---|---|---|")
    w("| 결정성: 같은 payload 재전송 (T2 %d행, %.0f~%.0f분 뒤, 중앙 %.0f분) | 라벨 %d/%d 같음, 확률 벡터 %d/%d 같음(최대 \\|Δp\\| %s), 토큰 수 %d/%d 같음 | english로 T1 %d decision을 재실행한 답이 %s | `S1b_summary.md` §2, `laya_summary.md` §5 |"
      % (det["rows"], det["resend_after_min_range"][0], det["resend_after_min_range"][1], det["resend_after_min_median"], det["same_label"], det["rows"], det["identical_probs"], det["rows"], "%.2f" % det["max_abs_dp"], det["tokens_identical"], det["rows"],
         det["laya_t1_rerun_decisions"], "완전히 같았다" if det["laya_t1_english_rerun_identical"] else "달랐다"))
    w("| 옵션 순서 flip (T2 %d행, Laya probe와 같은 순열 1개) | %d/%d = %s %s | english %d/%d, multilingual %d/%d (probe 40행 전체도 0.000) | `S1b_summary.md` §3 |"
      % (oo["rows"], oo["jev_flips"], oo["rows"], f3(oo["jev_flips"] / oo["rows"]), ci(oo["jev_wilson"]), oo["laya_flips"]["english"], oo["rows"], oo["laya_flips"]["multilingual"], oo["rows"]))
    w("")
    w("- 순서 flip은 정보량이 낮다. AG News 4옵션의 고확신 행 위주라 두 시스템 모두 0이었고, 제3자 공개 Jev flip %s도 배제하지 못한다(그 값에서 0/%d이 나올 확률 %s).\n"
      % (g(E["published_jev_flip"]), oo["rows"], "%.3f" % oo["p_zero_flips_if_013"]))
    cs, pen = T["T7"]["extra"]["consistency"], T["T7"]["extra"]["penalty"]
    w("### 6.1 T7 언어 간 일관성과 언어 페널티 (같은 %d id x %d개 언어)\n" % (cs["jev"]["ids"], M["methods"]["langs"]))
    w("| system | 5개 언어 모두 같은 라벨 | 언어쌍 평균 일치 (%d쌍) | 5개 언어 모두 정답 | 5개 언어 모두 오답 | en 대비 페널티 de / ja / zh-CN / ko | 평균 페널티 |" % cs["jev"]["pairs"])
    w("|---|---|---|---|---|---|---|")
    for s in ("jev",) + RUNNERS:
        x = cs[s]
        w("| %s | %d/%d | %s | %d | %d | %s | %s |" % (SYS_LABEL[s], x["same_all5"], x["ids"], f3(x["pairwise_agree"]), x["right_all5"], x["wrong_all5"],
                                                      " / ".join(sg(pen[s][L]) for L in LANGS[1:]), sg(pen[s]["mean"])))
    w("")
    w("- Jev는 언어를 바꿔도 같은 결정을 낸다. 라벨이 언어마다 달라진 id %d개는 번역 문장의 내용이 언어마다 달랐던 경우다(`S5_summary.md` §2.4, §3.4). "
      "Laya는 english가 ko에서 %s, multilingual도 de에서 %s로 떨어진다. 언어당 n=%d이라 페널티 크기는 방향 신호다.\n"
      % (cs["jev"]["ids"] - cs["jev"]["same_all5"], f3(pl["ko"]["english"]["acc"]), f3(pl["de"]["multilingual"]["acc"]), pl["en"]["jev"]["n"]))

    # 7
    one, multi = LT["single_all"], LT["by_type"]["multi"]
    w("## 7. 지연과 비용\n")
    w("**배포 형태가 다르다.** Jev 값은 서울의 브라우저 → 플레이그라운드 서버 → Jev로 이어지는 인터넷 왕복이고, Laya 값은 같은 Apple M4 Pro 안의 in-process 호출과 localhost HTTP다. "
      "아래 값의 차이는 모델 속도 비교가 아니다.\n")
    w("### 7.1 Jev (마스터 로그 성공 %d건)\n" % LT["all"]["requests"])
    w("| 요청 형식 | 과제 | 요청 | 표시값 'server + network' 중앙 (p5~p95) ms | 브라우저 POST 중앙 (p5~p95) ms | POST − latencyMs 중앙 ms |")
    w("|---|---|---|---|---|---|")
    for k, name, ts in (("single_choice", "단일 choice", "T2(S1b 포함)·T3·T4·T7"), ("single_boolean", "단일 Boolean", "T5·T8"), ("single_score", "단일 score", "T6"),
                        ("multi", "Multiple questions 2~4문항", "T1")):
        x = LT["by_type"][k]
        w("| %s | %s | %d | %s (%s~%s) | %s (%s~%s) | %s |" % (name, ts, x["requests"], g(x["displayed_ms"]["median"]), g(round(x["displayed_ms"]["p5"], 1)),
                                                          g(round(x["displayed_ms"]["p95"], 1)), g(x["browser_post_ms"]["median"]), g(round(x["browser_post_ms"]["p5"], 1)),
                                                          g(round(x["browser_post_ms"]["p95"], 1)), "%.1f" % x["post_minus_latency_median"]))
    for k, name in (("single_all", "단일 문항 전체"), ("all", "전체")):
        x = LT[k]
        w("| %s | - | %d | %s (%s~%s) | %s (%s~%s) | %s |" % (name, x["requests"], g(x["displayed_ms"]["median"]), g(round(x["displayed_ms"]["p5"], 1)), g(round(x["displayed_ms"]["p95"], 1)),
                                                          g(x["browser_post_ms"]["median"]), g(round(x["browser_post_ms"]["p5"], 1)), g(round(x["browser_post_ms"]["p95"], 1)),
                                                          "%.1f" % x["post_minus_latency_median"]))
    w("")
    w("- 표시값은 응답 `latencyMs`의 반올림이고 화면 표시와 응답이 %d/%d 일치했다(세션 요약). 정의는 공개되지 않았고 브라우저와 플레이그라운드 사이 구간(중앙 약 %.0f ms)이 빠져 있다. "
      "전체 중앙 %s ms는 제3자 공개 Jev p50 %d~%d ms(`third_party/laya/README.md:1288`)%s. 요청당 문항이 2~4개여도 표시값 중앙은 %s ms로 1문항(%s ms)과 비슷하다.\n"
      % (Q["display_matches"], Q["master_ok"], LT["all"]["post_minus_latency_median"], g(LT["all"]["displayed_ms"]["median"]), E["readme_jev_p50_lo"], E["readme_jev_p50_hi"],
         "의 범위 안이다" if E["readme_jev_p50_lo"] <= LT["all"]["displayed_ms"]["median"] <= E["readme_jev_p50_hi"] else
         ("보다 약간 낮다" if LT["all"]["displayed_ms"]["median"] < E["readme_jev_p50_lo"] else "보다 높다"), g(multi["displayed_ms"]["median"]), g(one["displayed_ms"]["median"])))
    w("### 7.2 Laya (로컬, Apple M4 Pro, 기존 측정 인용)\n")
    w("| 경로 | 체크포인트 | 장치 | 1문항 ms | 3문항 ms | 출처 |")
    w("|---|---|---|---|---|---|")
    for row in (("in-process 연속 (D1, short state)", "english", "CPU fp32 10스레드", "d1_english_cpu_1q", "d1_english_cpu_3q"),
                ("in-process 연속 (D1, short state)", "multilingual", "CPU fp32 10스레드", "d1_multilingual_cpu_1q", "d1_multilingual_cpu_3q"),
                ("in-process 연속 (D1, short state)", "english", "MPS", "d1_english_mps_1q", "d1_english_mps_3q"),
                ("in-process 연속 (D1, short state)", "multilingual", "MPS", "d1_multilingual_mps_1q", "d1_multilingual_mps_3q"),
                ("in-process 간헐 호출 1 s 간격 (D1c)", "multilingual", "CPU", "d1c_multilingual_cpu_1q_gap1000", "d1c_multilingual_cpu_3q_gap1000"),
                ("in-process 간헐 호출 1 s 간격 (D1c)", "multilingual", "MPS", "d1c_multilingual_mps_1q_gap1000", "d1c_multilingual_mps_3q_gap1000"),
                ("laya-serve HTTP 연속 c=1 (D6)", "multilingual", "MPS", "d6_mps_1q_c1_p50", "d6_mps_3q_c1_p50"),
                ("laya-serve HTTP 연속 c=1 (D6)", "multilingual", "CPU 10스레드", "d6_cpu_1q_c1_p50", "d6_cpu_3q_c1_p50"),
                ("`/poc/decide` HTTP 연속 (P2, p50)", "ft-v1", "MPS", "p2_poc_decide_p50", None)):
        src = sorted({o["external"][k]["source"] for k in row[3:] if k})
        w("| %s | %s | %s | %s | %s | `%s` |" % (row[0], row[1], row[2], g(E[row[3]]), g(E[row[4]]) if row[4] else "-", "`, `".join(src)))
    w("")
    gmin = min(SESSIONS, key=lambda s: rq[s]["gap_min_s"])
    w("- Jev 요청의 Run 클릭 간격은 최소 %.1f s(%s)였고 S3~S5는 %d s 간격 가드로 보냈다(§1, 세션 run card). 연속 호출이 아니므로 "
      "Laya 쪽의 가까운 조건은 간헐 호출(D1c)이다. 그 조건에서도 multilingual 1문항은 MPS %s ms, CPU %s ms다. "
      "laya-serve open-loop 10 RPS 3문항 p50 %s / p95 %s ms(D6)는 서버 부하 조건의 값이다."
      % (rq[gmin]["gap_min_s"], gmin, M["methods"]["pacing_guard_s"], g(E["d1c_multilingual_mps_1q_gap1000"]), g(E["d1c_multilingual_cpu_1q_gap1000"]), g(E["d6_mps_3q_open10_p50"]), g(E["d6_mps_3q_open10_p95"])))
    w("- 그림 `figs/latency.png`는 이 두 표의 값을 로그 축에 같이 놓은 것이다.\n")
    w("### 7.3 토큰과 비용\n")
    w("| 과제 | 요청 | decision | 입력 / 출력 토큰 중앙 (요청당) | 입력 / 출력 토큰 중앙 (decision당) | decision당 평균 토큰 (합계 ÷ decision) | 1,000 decision당 Jev 비용 (USD, 단가 확인 필요) |")
    w("|---|---|---|---|---|---|---|")
    for t in list(T) + ["all"]:
        x = LT["by_task"][t] if t != "all" else LT["all"]
        w("| %s | %d | %d | %s / %s | %s / %s | %.1f | %.4f |" % ("전체" if t == "all" else t, x["requests"], x["decisions"], g(x["tokens_in_req_median"]), g(x["tokens_out_req_median"]),
                                                              g(round(x["tokens_in_dec_median"], 1)), g(round(x["tokens_out_dec_median"], 1)), x["tokens_per_dec_mean"], x["cost_per_1k_dec_usd"]))
    cap = o["laya_capacity"]
    w("")
    w("- 공식: 1,000 decision당 비용 = (입력 + 출력 토큰 합계 ÷ decision 수) x 1,000 x $%s ÷ 1,000,000. 단가 $%s / 1M tokens는 upstream README가 인용한 제3자 수치(`third_party/laya/README.md:1291`)이고 "
      "입력·출력 단가 구분이 없다. 이 세션들에서 공식 단가를 확인하지 않았다(**단가 확인 필요**). 전체 %d decision의 토큰 합계는 입력 %s, 출력 %s다."
      % (g(PRICE_PER_M), g(PRICE_PER_M), LT["all"]["decisions"], "{:,}".format(LT["all"]["tokens_in_total"]), "{:,}".format(LT["all"]["tokens_out_total"])))
    w("- 출력 토큰은 형식에 따라 다르다(Boolean %s, score %s, choice는 옵션 수와 라벨 길이에 따라 %s~%s). 여러 문항을 한 요청에 묶으면(T1) state 토큰이 공유돼 decision당 토큰이 줄어든다."
      % (g(LT["by_task"]["T5"]["tokens_out_req_median"]), g(LT["by_task"]["T6"]["tokens_out_req_median"]), g(LT["by_task"]["T3"]["tokens_out_req_median"]),
         g(LT["by_task"]["T7"]["tokens_out_req_median"])))
    w("- 참고: 한국어 파일럿(8옵션, `key: 한국어 설명`)은 요청당 입력 %s / 출력 %s 토큰이었다(`results/F/jev_playground_manual_20261006.md` §3)."
      % (g(rk["jev_tokens_in_median"]), g(rk["jev_tokens_out_median"])))
    w("- Laya의 한계 비용은 토큰 과금이 없고 로컬 연산뿐이다. 단일 프로세스 laya-serve의 연속 1문항 처리량은 MPS %s RPS, CPU %s RPS(D6, `results/D/D_summary_20261003.md:203`, `:222`)라 "
      "1,000 decision에 각각 약 %.1f s, %.1f s의 머신 시간이 든다. 전력과 장비 감가상각은 측정하지 않았다.\n"
      % (g(cap["mps_1q_rps"]), g(cap["cpu_1q_rps"]), cap["sec_per_1k_mps"], cap["sec_per_1k_cpu"]))

    # 8
    t4r = REF["t4_rendering"]
    w("## 8. 해석\n")
    w("- **Jev가 앞서는 곳: 지시 따르기와 처음 보는 형식.** T1 typed-decisions(Jev − english %s, case 군집 CI %s), Banking77-10(T4, multilingual 대비 b/c %d/%d, p=%s, Holm %s), BoolQ(T5, Laya 학습 믹스 과제인데도 "
      "AUROC %s vs %s로 순위 품질 자체가 다르다), SST-5(T6, 주 지표 argmax는 p=%s로 비유의지만 MAE %s vs %s, Laya의 척도 압축), 다국어 intent(T7, Jev 언어별 %s~%s, multilingual 대비 id 군집 CI %s). "
      "이 중 T5만 Laya 학습 믹스 과제이고 나머지(T1·T4·T6·T7)는 두 체크포인트가 학습하지 않은 소스다(§2.1)."
      % (sg(CB["T1"]["english"]["diff"]), sci(CB["T1"]["english"]["ci"]), T["T4"]["mcnemar"]["multilingual"]["b"], T["T4"]["mcnemar"]["multilingual"]["c"],
         pv(T["T4"]["mcnemar"]["multilingual"]["p"]), pv(T["T4"]["holm_p"]),
         f3(x5["jev"]["auroc"]), f3(x5["english"]["auroc"]), pv(T["T6"]["mcnemar"]["english"]["p"]), f3(x6["jev"]["mae"]), f3(x6["english"]["mae"]),
         f3(min(pl[L]["jev"]["acc"] for L in LANGS)), f3(max(pl[L]["jev"]["acc"] for L in LANGS)), sci(CB["T7"]["multilingual"]["ci"])))
    w("- **비슷한 곳: AG News, Emotion, prompt-injections.** T2는 Laya 쪽 방향(b/c %d/%d)이지만 비유의이고 Laya 학습 믹스 과제다. T3는 b/c %d/%d다. T8은 정확도가 같지만(%s) 오류 구조가 다르다. "
      "Jev는 오탐 %d·미탐 %d로 역할 지시형 주입을 놓치고, Laya english는 독일어 덮어쓰기 문장을 놓친다(`S5_summary.md` §4.3). "
      "Laya가 같거나 앞선 이 세 과제 중 학습 믹스 과제는 T2뿐이고 T3·T8은 held out이다."
      % (mb("T2")["b"], mb("T2")["c"], mb("T3")["b"], mb("T3")["c"], f3(S("T8", "jev")["acc"]), x8["jev"]["fp"], x8["jev"]["fn"]))
    w("- **Laya의 레버 1, 파인튜닝.** T1 파인튜닝 체크포인트 %d/%d = Jev, 한국어 ft-v1 %d/%d ≥ Jev %d/%d. upstream의 자기 평가(\"a fast base to specialise, not ... a zero-shot decision engine\", "
      "`third_party/laya/README.md:1530` Fine-Tuning 절)와 맞는다. 다만 두 선 모두 같은 분포의 train을 쓴 in-domain 결과다." % (rt["correct"], rt["n"], rk["laya_ft_v1"], rk["n"], rk["jev"], rk["n"]))
    w("- **레버 2, 러너 선택.** english와 multilingual의 차이가 과제마다 크고 방향도 바뀐다(T5 %s vs %s, T8 %s vs %s, T7 ja %s vs %s, T4는 multilingual %s > english %s). "
      "Router는 언어로만 고르므로 영어 과제는 전부 english, 비라틴 문자는 multilingual로 보내고 de는 섞인다(T7 de Router %s)."
      % (f3(S("T5", "english")["acc"]), f3(S("T5", "multilingual")["acc"]), f3(S("T8", "english")["acc"]), f3(S("T8", "multilingual")["acc"]), f3(pl["ja"]["english"]["acc"]),
         f3(pl["ja"]["multilingual"]["acc"]), f3(S("T4", "multilingual")["acc"]), f3(S("T4", "english")["acc"]), f3(pl["de"]["router"]["acc"])))
    w("- **레버 3, 옵션 렌더링.** 같은 T4 40행·같은 옵션 집합에서 `key: key spaced`(v0)와 key-only만 바꿔도 english %s → %s(b/c %d/%d, p=%s), multilingual %s → %s(%d/%d, p=%s)로 움직인다"
      "(`laya_summary.md` §4b). 비교에서는 두 시스템에 같은 문자열을 넣어 통제했고, 배포에서는 렌더링도 검증 대상이다. Jev가 렌더링에 얼마나 민감한지는 측정하지 않았다."
      % (f3(t4r["english"]["v0"]), f3(t4r["english"]["v1"]), t4r["english"]["v0_only"], t4r["english"]["v1_only"], pv(t4r["english"]["mcnemar_p"]),
         f3(t4r["multilingual"]["v0"]), f3(t4r["multilingual"]["v1"]), t4r["multilingual"]["v0_only"], t4r["multilingual"]["v1_only"], pv(t4r["multilingual"]["mcnemar_p"])))
    w("- **운영 관점.** 학습 데이터 없이 바로 zero-shot 정확도가 필요하면 Jev 쪽이 유리하다. 지연·비용·데이터 외부 전송이 더 중요하고 과제별 학습 데이터를 만들 수 있으면 Laya를 파인튜닝해 쓰는 쪽이 맞다. "
      "어느 쪽이든 확신도 임계값은 과제별로 다시 맞춰야 한다(§5.4).\n")

    # 9
    w("## 9. 위협과 한계\n")
    w("- **플레이그라운드 ≠ API.** 모델 버전이 표기되지 않는다(Model ID만 `typesafe-ai/jev`). 확률이 소수 둘째 자리로 반올림돼 Brier·ECE에 약 ±%s 오차가 생기고 AUROC에 동점이 생긴다. "
      "서버 측 프롬프트 래핑이나 정규화가 있을 수 있고 \"Real model execution\" 주장은 검증할 수 없다. 표시 지연의 정의도 공개되지 않았다." % g(M["methods"]["jev_rounding_err"]))
    w("- **소표본.** 과제당 n=%d이면 Wilson 95%% 구간 반폭이 약 ±%.2f다(p=0.5 기준, 예: T4 Jev %s). T7은 언어당 n=%d(약 ±%.1f)다. docs/09 §6 기준으로 차이가 약 %s보다 작으면 대부분 구분되지 않는다."
      % (S("T2", "jev")["n"], M["methods"]["ci_halfwidth_n40"], ci(S("T4", "jev")["wilson"]), pl["en"]["jev"]["n"], M["methods"]["ci_halfwidth_n20"], g(E["docs09_min_detectable_diff"])))
    w("- **표본 쉬움(seed %d).** T3에서 Jev %s의 구간이 제3자 공개치 %s 포함하지 않고 Laya english %s도 upstream %s보다 높다. 짝 비교에는 쓰되 공개치와 비교해 일반화하지 않는다. "
      "T2는 Jev %s의 구간이 공개치 %s 포함한다." % (M["methods"]["seed"], acc(S("T3", "jev")), jo(f3(E["published_jev_emotion"]), ("을", "를")), f3(S("T3", "english")["acc"]),
                                           f3(E["upstream_laya_emotion_english"]), acc(S("T2", "jev")), jo(f3(E["published_jev_ag_news"]), ("을", "를"))))
    w("- **T1 teacher 미확인.** gold는 teacher 분포의 argmax이고 teacher와 Jev의 관계는 확인하지 못했다. Jev %s은 공개치 %s(%s decision, 다른 문항 구성)보다 높다. "
      "teacher 정렬 효과를 배제할 수 없다(docs/09 열린 질문 10)." % (f3(S("T1", "jev")["acc"]), f3(E["published_jev_typed_decisions"]), "{:,}".format(E["published_jev_typed_decisions_n"])))
    w("- **Jev는 다문항을 함께 평가한다.** T1에서 Jev는 case의 질문 2~4개를 한 요청에서 함께 평가했고 Laya는 질문마다 독립 평가했다. 이 차이의 효과는 분리하지 않았다.")
    w("- **학습 오염.** upstream 표기로 Laya 학습 믹스에 들어간 과제는 T2·T5뿐이고 나머지는 held out이다(§2.1). 이 표기는 upstream의 자기 보고이고 "
      "학습 데이터 자체는 확인하지 않았다. Jev의 학습 데이터는 알 수 없고 모든 소스가 공개 데이터셋이다.")
    w("- **러너 사후 선택.** 과제별 최고 Laya는 결과를 보고 고른 것이라 Laya에 유리하다. 모든 러너를 표에 남겼고 고정 러너 기준 합산(§4.3)도 같은 방향이다.")
    w("- **다중 비교.** 8개 과제 검정에 Holm 보정을 하면 T1·T7만 유의하다(T5 %s, T4 %s, T6 %s). 보정 전 판정 4/4/0은 탐색적 요약으로 읽는다."
      % (pv(T["T5"]["holm_p"]), pv(T["T4"]["holm_p"]), pv(T["T6"]["holm_p"])))
    w("- **군집과 퇴화.** T1(case)·T7(id)의 item 단위 검정은 낙관적이라 군집 bootstrap을 따로 냈다. T8 Jev AUROC CI는 완전 분리로 퇴화했다.")
    w("- **입력 표현의 제약.** 플레이그라운드 Boolean에는 설명 칸이 없고 Score는 5레벨만 받으며 choice 입력은 %d자로 잘린다. 그래서 T1은 %d개 중 %d개만 비교했고 T4는 key-only로 다시 만들었다(docs/09 §2)."
      % (M["limits"]["choice_input_chars"], M["t1_decisions_total"], S("T1", "jev")["n"]))
    w("- **지연·비용.** 지연은 배포 형태가 달라 모델 속도 비교가 아니다. Jev 단가는 제3자 인용치이고 확인되지 않았다.\n")

    # 10
    w("## 10. 재현\n")
    w("```bash")
    w("source env.sh")
    w("# Jev 세션 분석 (모델 호출·사이트 요청 없음, 기록된 jsonl만 읽는다; 세션 원기록과 T2 세트는 공개 저장소에는 포함하지 않음)")
    w(".venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S1 T2_ag_news_40")
    w(".venv/bin/python results/F/jev_cmp/jev_cmp.py stability S1 S1b T2_ag_news_40")
    w(".venv/bin/python results/F/jev_cmp/jev_cmp.py t1 S1,S2")
    w(".venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S2 T3_emotion_40")
    w(".venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S3 T4_banking77_10opt_40")
    w(".venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S3 T5_boolq_40")
    w(".venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S4 T6_sst5_40")
    w("for L in en de; do .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S4 T7_massive_intent_10opt_${L}_20; done")
    w("for L in ja zh-CN ko; do .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S5 T7_massive_intent_10opt_${L}_20; done")
    w(".venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S5 T8_prompt_injections_40")
    w(".venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S4,S5 T7_massive_intent_10opt_en_20,T7_massive_intent_10opt_de_20,T7_massive_intent_10opt_ja_20,T7_massive_intent_10opt_zh-CN_20,T7_massive_intent_10opt_ko_20")
    w("# Laya 측 (S0, CPU fp32) 과 세트 빌드")
    w("export HF_HOME=$PWD/data/raw/hf && .venv/bin/python scripts/build_jev_cmp_sets.py all")
    w("bash results/F/jev_cmp/run_laya.sh && .venv/bin/python results/F/jev_cmp/laya_summary.py")
    w("# S6 종합: summary.json, summary.ko.md, figs/ 생성과 대조")
    w(".venv/bin/python results/F/jev_cmp/s6_summary.py build")
    w(".venv/bin/python results/F/jev_cmp/s6_summary.py verify")
    w("```\n")
    w("| 파일 | 내용 |")
    w("|---|---|")
    for a, b in (("`results/F/jev_cmp/summary.md`, `summary.json`", "이 문서와 같은 수치의 JSON(Laya의 항목별 정오 비트열 포함, Jev는 집계만)"),
                 ("`results/F/jev_cmp/figs/accuracy_by_task.{png,svg}`", "과제별 정확도, Wilson 95% CI, 판정"),
                 ("`results/F/jev_cmp/figs/t7_languages.{png,svg}`", "T7 언어별 정확도, 언어별 McNemar"),
                 ("`results/F/jev_cmp/figs/latency.{png,svg}`", "배포 형태별 지연(로그 축)"),
                 ("`results/F/jev_cmp/s6_summary.py`", "build / verify"),
                 ("`results/F/jev_cmp/S6_20261007.md`", "S6 run card"),
                 ("`results/F/jev_cmp/jev_runs_all.jsonl`", "Jev 요청 마스터 로그 411줄(세션 요청 로그의 이어붙임과 동일, build가 assert, 공개 저장소에는 포함하지 않음)"),
                 ("`results/F/jev_cmp/sessions/S{1,1b,2,3,4,5}_*/`", "세션 요약, run card, 요청 로그, 원기록(요청 로그와 원기록은 공개 저장소에는 포함하지 않음)"),
                 ("`results/F/jev_cmp/laya/*.json`, `laya_summary.{md,json}`", "Laya 리포트(S0)"),
                 ("`data/evals/jev_cmp/MANIFEST.json`", "세트 n, `jev_comparable_n`, `in_training_mix`, 소스 revision"),
                 ("`results/F/jev_playground_manual_20261006.md`, `results/F/jev_runs_raw.jsonl`, `jev_sample_24.jsonl`", "한국어 파일럿(`jev_runs_raw.jsonl`은 공개 저장소에는 포함하지 않음)"),
                 ("`results/D/D_summary_20261003.md`, `results/poc/P2_20261003.md`", "Laya 지연 인용 출처")):
        w("| %s | %s |" % (a, b))
    w("")
    w("## 그림\n")
    w("![과제별 정확도](figs/accuracy_by_task.png)\n")
    w("![T7 언어별 정확도](figs/t7_languages.png)\n")
    w("![지연](figs/latency.png)\n")
    pc = o["figures"]["palette"]
    w("그림은 범주 색 슬롯 1~4(파랑 Jev, 주황 Laya english, 청록 Laya multilingual, 노랑 Laya Router)를 쓴다. 팔레트 검증기(`figs/palette_check.txt`)에서 최악 CVD ΔE는 "
      "슬롯 1~3 인접쌍 %s, 전체쌍 %s, 슬롯 1~4 인접쌍 %s로 모두 통과했다. 청록(대비 %s)과 노랑(%s)은 밝은 배경 대비 3:1 미만이라 막대 안 직접 라벨과 이 문서의 표를 함께 둔다. "
      "정적 PNG/SVG라 라이트 모드만 만들었다." % (g(pc["slots3_adjacent"]["worst_cvd_de"]), g(pc["slots3_all_pairs"]["worst_cvd_de"]), g(pc["slots4_adjacent"]["worst_cvd_de"]),
                                          g(pc["slots4_adjacent"]["below_3to1"]["#1baf7a"]), g(pc["slots4_adjacent"]["below_3to1"]["#eda100"])))
    return esc_tilde("\n".join(L) + "\n")


def esc_tilde(md):
    """GitHub renders a pair of single `~` on one line as strikethrough: escape the prose tildes (not in code spans or fences)."""
    out, code = [], False
    for line in md.split("\n"):
        if line.startswith("```"):
            code = not code
        elif not code:
            line = "`".join(p if k % 2 else p.replace("~", "\\~") for k, p in enumerate(line.split("`")))
        out.append(line)
    return "\n".join(out)


# ---------------------------------------------------------------- verify
REGEN = [("T2", "S1", ["analyze", "S1", "T2_ag_news_40"]), ("T2_stability", "S1b", ["stability", "S1", "S1b", "T2_ag_news_40"]),
         ("T1", "S2", ["t1", "S1,S2"]), ("T3", "S2", ["analyze", "S2", "T3_emotion_40"]), ("T4", "S3", ["analyze", "S3", "T4_banking77_10opt_40"]),
         ("T5", "S3", ["analyze", "S3", "T5_boolq_40"]), ("T6", "S4", ["analyze", "S4", "T6_sst5_40"]),
         ("T7_en", "S4", ["analyze", "S4", "T7_massive_intent_10opt_en_20"]), ("T7_de", "S4", ["analyze", "S4", "T7_massive_intent_10opt_de_20"]),
         ("T7_ende", "S4", ["analyze", "S4", "T7_massive_intent_10opt_en_20,T7_massive_intent_10opt_de_20"]),
         ("T7_ja", "S5", ["analyze", "S5", "T7_massive_intent_10opt_ja_20"]), ("T7_zh-CN", "S5", ["analyze", "S5", "T7_massive_intent_10opt_zh-CN_20"]),
         ("T7_ko", "S5", ["analyze", "S5", "T7_massive_intent_10opt_ko_20"]), ("T8", "S5", ["analyze", "S5", "T8_prompt_injections_40"]),
         ("T7_all5", "S5", ["analyze", "S4,S5", ",".join("T7_massive_intent_10opt_%s_20" % L for L in LANGS)])]
# regenerated tables compared row by row with the session summary (by index in the regenerated output)
# (T2's confusion matrix and T8's confidence table are prose or different columns in S1 / S5, so they are not compared)
REGEN_TABLES = {"T2": (0, 1, 2), "T2_stability": (0, 1), "T1": (0, 1, 2, 3, 4), "T3": (0, 1, 2, 3), "T4": (0, 1), "T5": (0, 1, 2), "T6": (0, 1, 2, 3),
                "T7_en": (0, 1), "T7_de": (0, 1), "T7_ende": (0, 1, 2), "T7_ja": (0, 1), "T7_zh-CN": (0, 1), "T7_ko": (0, 1), "T8": (0, 1),
                "T7_all5": (2, 3, 4, 5)}
TNUM = re.compile(r"[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?")
MDNUM = re.compile(r"(?<![A-Za-z0-9_.§/])(?<![A-Za-z]/)[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?(?![A-Za-z0-9_])")


def md_tables(text):
    tables, cur = [], []
    for line in text.replace("\\|", "¦").replace("\\~", "~").splitlines():
        if line.startswith("|"):
            cur.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif cur:
            tables.append(cur)
            cur = []
    if cur:
        tables.append(cur)
    return [[r for r in t if not all(re.fullmatch(r":?-{3,}:?", c) for c in r)][1:] for t in tables]


def tnums(cells):
    out = []
    for c in cells:
        c = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", c.replace("−", "-").replace("**", ""))
        for m in TNUM.finditer(c):
            x = m.group(0)
            out.append((float(x), None if "e" in x else (len(x.split(".")[1]) if "." in x else 0)))
    return out


def _eq(a, b):
    (x, dx), (y, dy) = a, b
    if dx is None or dy is None:
        return abs(x - y) <= 0.06 * max(abs(x), abs(y)) + 1e-15
    return abs(x - y) <= 0.5 * 10 ** (-min(dx, dy)) + 1e-9


def _subseq(a, b):
    i = 0
    for y in b:
        if i < len(a) and _eq(a[i], y):
            i += 1
    return i == len(a)


def _key(cells):
    """What a row is about: ('vs', runner) for McNemar rows, ('sys', name) for system rows, None otherwise."""
    c0 = cells[0].lower()
    if " vs " in c0:
        return ("vs", c0.split()[-1])
    for k in ("typed-decisions", "multilingual", "english", "router"):
        if c0.startswith("laya " + k):
            return ("sys", k)
    return ("sys", "jev") if c0.startswith("jev") else None


def _row_nums(cells, key):
    """Numbers after the cell that names the system (so counts inside a name like 'Router (40 모두 english)' are skipped)."""
    if key is None:
        return tnums(cells)
    for i, c in enumerate(cells):
        cl = c.lower()
        if (key[0] == "vs" and " vs " in cl and key[1] in cl) or (key[0] == "sys" and key[1] in cl and " vs " not in cl):
            return tnums(cells[i + 1:])
    return None


def _lcs(a, b):
    m = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a)):
        for j in range(len(b)):
            m[i + 1][j + 1] = m[i][j] + 1 if _eq(a[i], b[j]) else max(m[i][j + 1], m[i + 1][j])
    return m[-1][-1]


def find_row(expected, tables, key, must_cell=None, extra=None, lcs=False, src=None):
    """A row in `tables` about `key` (and holding a cell equal to must_cell) whose numbers contain `expected` as a subsequence,
    or (when the other side drops columns) whose numbers are a long enough subsequence of `expected`. `src`: the cells
    `expected` came from; a row of the same width that has "—" cells is compared without src's cells in those columns."""
    for t in tables:
        for cells in t:
            if must_cell is not None and must_cell not in cells:
                continue
            if extra is not None and extra not in cells:
                continue
            ns = _row_nums(cells, key)
            if not ns:
                continue
            exp = expected
            if src is not None and "—" in cells and len(cells) == len(src):  # session summaries withhold per-item Jev outputs as "—"
                exp = _row_nums(["" if c == "—" else x for x, c in zip(src, cells)], key)
            if _subseq(exp, ns) or (len(ns) >= max(4, 0.6 * len(exp)) and _subseq(ns, exp)):
                return cells
            if lcs and _lcs(exp, ns) >= max(5, 0.7 * min(len(exp), len(ns))):  # columns merged or split differently
                return cells
    return None


def verify():
    o = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    T, fails, n_ok = o["tasks"], [], Counter()

    def check(cond, kind, msg):
        n_ok[kind] += bool(cond)
        if not cond:
            fails.append("[%s] %s" % (kind, msg))

    # 0. fresh jev_cmp.py output for every session table
    regen, raw = {}, {}
    for name, _, args in REGEN:
        r = subprocess.run([sys.executable, str(HERE / "jev_cmp.py")] + args, capture_output=True, text=True, cwd=ROOT)
        check(r.returncode == 0, "regen", "%s exit %d %s" % (name, r.returncode, r.stderr[-300:]))
        regen[name], raw[name] = md_tables(r.stdout), r.stdout
    sess = {s: md_tables((J.session_dir(s) / ("%s_summary.ko.md" % s)).read_text(encoding="utf-8")) for s in SESSIONS}

    # 1. summary.json == regenerated jev_cmp.py tables
    D = lambda v, d: (float(v), d)  # noqa: E731
    acc5 = lambda x: [D(x["correct"], 0), D(x["n"], 0), D(x["acc"], 3), D(x["wilson"][0], 3), D(x["wilson"][1], 3)]  # noqa: E731
    keyof = {"jev": ("sys", "jev"), **{m: ("sys", m) for m in RUNNERS}}
    for t, reg in (("T2", "T2"), ("T3", "T3"), ("T4", "T4"), ("T5", "T5"), ("T6", "T6"), ("T7", "T7_all5"), ("T8", "T8")):
        kind, X = T[t]["kind"], T[t]["extra"]
        for s in ("jev",) + RUNNERS:
            x = T[t]["systems"][s]
            if kind == "choice":
                exp = acc5(x) + [D(x["brier"], 3), D(x["ece"], 3), D(x["mean_top"], 3)]
            elif kind == "boolean":
                exp = acc5(x) + [D(X[s]["pred_true"], 0), D(x["brier"], 3), D(x["ece"], 3), D(x["mean_top"], 3), D(X[s]["auroc"], 3)] + [D(v, 3) for v in X[s]["auroc_ci"]]
            else:
                exp = acc5(x) + [D(X[s]["rounded_correct"], 0), D(x["n"], 0), D(X[s]["rounded_acc"], 3)] + [D(v, 3) for v in X[s]["rounded_wilson"]] + [
                    D(X[s]["mae"], 3), D(X[s]["mean_signed"], 3), D(X[s]["within1"], 3), D(x["brier"], 3), D(x["ece"], 3), D(x["mean_top"], 3), D(X[s]["argmax_ne_rounded"], 0)]
            check(find_row(exp, regen[reg][:1], keyof[s]), "json=regen", "%s %s accuracy row" % (t, s))
        for m in RUNNERS:
            mc = T[t]["mcnemar"][m]
            exp = [D(mc["n"], 0), D(mc["same"], 0), D(mc["b"], 0), D(mc["c"], 0), D(mc["p"], 4)]
            if kind == "boolean":
                exp += [D(X[m]["auroc_diff"], 3)] + [D(v, 3) for v in X[m]["auroc_diff_ci"]]
            if kind == "score":
                r_ = X[m]["mcnemar_rounded"]
                exp += [D(r_["b"], 0), D(r_["c"], 0), D(r_["p"], 4), D(X[m]["mae_diff"], 3)] + [D(v, 3) for v in X[m]["mae_diff_ci"]]
            check(find_row(exp, regen[reg][1:2], ("vs", m)), "json=regen", "%s Jev vs %s McNemar row" % (t, m))
    pl = T["T7"]["extra"]["per_lang"]
    for L in LANGS:
        for s in ("jev",) + RUNNERS:
            exp = acc5(pl[L][s]) + [D(pl[L][s]["brier"], 3), D(pl[L][s]["ece"], 3)]
            check(find_row(exp, regen["T7_" + L][:1], keyof[s]), "json=regen", "T7 %s %s accuracy row" % (L, s))
            if s != "jev":
                mc = pl[L][s]["mcnemar"]
                check(find_row([D(mc["b"], 0), D(mc["c"], 0), D(mc["p"], 4)], regen["T7_" + L][1:2], ("vs", s)), "json=regen", "T7 %s Jev vs %s" % (L, s))
    cs, pen = T["T7"]["extra"]["consistency"], T["T7"]["extra"]["penalty"]
    for s in ("jev",) + RUNNERS:
        exp = [x for L in LANGS[1:] for x in (D(cs[s]["same_as_en"][L], 0), D(cs[s]["ids"], 0))] + [D(cs[s]["same_all5"], 0), D(cs[s]["ids"], 0), D(cs[s]["pairwise_agree"], 3),
                                                                                         D(cs[s]["right_all5"], 0), D(cs[s]["wrong_all5"], 0)]
        check(find_row(exp, regen["T7_all5"][5:6], keyof[s]), "json=regen", "T7 consistency %s" % s)
        check(find_row([D(pen[s][L], 3) for L in LANGS[1:]] + [D(pen[s]["mean"], 3)], regen["T7_all5"][3:4], keyof[s]), "json=regen", "T7 penalty %s" % s)
    x1 = T["T1"]["extra"]
    for s in ("jev",) + RUNNERS + ("typed-decisions",):
        exp = acc5(T["T1"]["systems"][s]) + [v for k in ("choice", "noul", "score") for v in acc5(x1["by_type"][k][s])] + [
            D(x1[s]["soft_acc"], 3), D(x1[s]["brier_vs_soft"], 3), D(T["T1"]["systems"][s]["brier"], 3), D(T["T1"]["systems"][s]["ece"], 3)]
        exp += [D(x1["jev_score_mae_field"], 3), D(x1[s]["score_mae"], 3)] if s == "jev" else [D(x1[s]["score_mae"], 3)]
        check(find_row(exp, regen["T1"][:1], ("sys", "jev") if s == "jev" else ("sys", s)), "json=regen", "T1 %s accuracy row" % s)
    for m in list(RUNNERS) + ["typed-decisions"]:
        mc = T["T1"]["mcnemar"][m]
        check(find_row([D(mc["n"], 0), D(mc["b"], 0), D(mc["c"], 0), D(mc["p"], 4)], regen["T1"][1:2], ("vs", m), extra="all"), "json=regen", "T1 Jev vs %s all" % m)
        for k in ("choice", "noul", "score"):
            mc = x1["mcnemar_by_type"][m][k]
            check(find_row([D(mc["n"], 0), D(mc["b"], 0), D(mc["c"], 0), D(mc["p"], 4)], regen["T1"][1:2], ("vs", m), extra=k), "json=regen", "T1 Jev vs %s %s" % (m, k))
    for m in ("english", "multilingual"):
        x = x1["noul_nocrit"][m]
        check(find_row([D(x["correct"], 0), D(x["n"], 0)], regen["T1"][2:3], ("sys", m), extra="no criteria") and
              find_row([D(x["b"], 0), D(x["c"], 0), D(x["p"], 4)], regen["T1"][2:3], ("sys", m), extra="no criteria"), "json=regen", "T1 noul no-criteria %s" % m)
    lt = o["latency_tokens"]["by_task"]
    lat = lambda x: [D(x["requests"], 0), D(x["displayed_ms"]["median"], 1), D(x["displayed_ms"]["min"], 0), D(x["displayed_ms"]["max"], 0),  # noqa: E731
                     D(x["browser_post_ms"]["median"], 1), D(x["browser_post_ms"]["min"], 0), D(x["browser_post_ms"]["max"], 0),
                     D(x["tokens_in_req_median"], 1), D(x["tokens_out_req_median"], 1)]
    for t, reg in (("T2_main", "T2"), ("T3", "T3"), ("T4", "T4"), ("T5", "T5"), ("T6", "T6"), ("T7", "T7_all5"), ("T8", "T8"), ("T1", "T1")):
        check(find_row(lat(lt[t]), regen[reg], None), "json=regen", "%s latency/token row" % t)
    rb, oo = o["robustness"]["determinism"], o["robustness"]["option_order"]
    for frag in ("Same label %d/%d; identical probability vectors %d/%d; max abs dp %.2f" % (rb["same_label"], rb["rows"], rb["identical_probs"], rb["rows"], rb["max_abs_dp"]),
                 "tokens identical %d/%d" % (rb["tokens_identical"], rb["rows"]),
                 "Jev flips %d/%d = %.3f, Wilson 95%% [%.3f, %.3f]" % (oo["jev_flips"], oo["rows"], oo["jev_flips"] / oo["rows"], *oo["jev_wilson"]),
                 "Laya english flips %d/%d, multilingual %d/%d" % (oo["laya_flips"]["english"], oo["rows"], oo["laya_flips"]["multilingual"], oo["rows"])):
        check(frag in raw["T2_stability"], "json=regen", "stability text '%s'" % frag)

    # 2. regenerated jev_cmp.py tables == session summaries
    sdoc = {name: s for name, s, _ in REGEN}
    for name, idx in REGEN_TABLES.items():
        lang = name.split("_")[1] if name.startswith("T7_") and name.split("_")[1] in LANGS else None
        for ti in idx:
            for cells in regen[name][ti]:
                key = _key(cells)
                ns = _row_nums(cells, key)
                if not ns or len(ns) < 2:
                    continue
                hit = find_row(ns, sess[sdoc[name]], key, must_cell=lang, lcs=True, src=cells)
                if not hit and key and key[0] == "vs":  # some summaries put b / c and p in the system row (S4 §3.3)
                    hit = find_row(ns[-3:], sess[sdoc[name]], ("sys", key[1]), must_cell=lang)
                if not hit and key and key[1] == "router":  # summaries print a Router row only where it differs from english
                    eng = [c for c in regen[name][ti] if _key(c) == (key[0], "english") and c[1:2] == cells[1:2]
                           and (key[0] == "vs" or c[1:2] == cells[1:2])]
                    hit = eng and tnums(eng[0][1:]) == tnums(cells[1:]) and find_row(tnums(eng[0][1:]), sess[sdoc[name]], (key[0], "english"), must_cell=lang, lcs=True)
                    n_ok["router=english (session omits Router row)"] += bool(hit)
                check(hit, "regen=session", "%s table %d row '%s' not found in %s_summary.ko.md" % (name, ti, " | ".join(cells)[:110], sdoc[name]))

    # 3. every number in summary.md / the run card exists in summary.json
    allowed, strings = set(), []

    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                strings.append(str(k))
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, bool) or v is None:
            pass
        elif isinstance(v, (int, float)):
            for x in (v, abs(v), 100 * v, 100 * abs(v)):
                allowed.update({"%.0f" % x, "%.1f" % x, "%.2f" % x, "%.3f" % x, "%.4f" % x, "%g" % x, "%.1e" % x, "%.2e" % x, "%g" % round(x, 1)})
                if float(x).is_integer():
                    allowed.add(str(int(x)))
        else:
            strings.append(str(v))
    walk(o)
    blob = "\n".join(strings)
    for st in strings:
        for m in TNUM.finditer(st):
            allowed.add(m.group(0).lstrip("+-"))
    for doc in (OUT_MD, HERE / "S6_20261007.ko.md"):
        if not doc.exists():
            check(False, "md=json", "%s missing" % doc.name)
            continue
        text = doc.read_text(encoding="utf-8")
        check("—" not in text and "–" not in text, "no-dash", "%s has an em or en dash" % doc.name)
        body = re.sub(r"`[^`]*`", " ", text)
        body = re.sub(r"(?m)^#+ [\d.]+", " ", body)  # section numbers in headings
        body = re.sub(r"\]\([^)]*\)", "]", body)
        for dt in re.findall(r"\d{4}-\d{2}-\d{2}|\b\d{2}:\d{2}(?::\d{2})?\b", body):
            check(dt in blob or dt.replace("-", "") in blob, "md=json", "%s: date/time %s not in summary.json" % (doc.name, dt))
        body = re.sub(r"\d{4}-\d{2}-\d{2}|\b\d{2}:\d{2}(?::\d{2})?\b", " ", body)
        body = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", body.replace("−", "-"))
        for m in MDNUM.finditer(body):
            tok = m.group(0)
            check(tok.lstrip("+-") in allowed, "md=json", "%s: number %s (…%s…) not in summary.json" % (doc.name, tok, body[max(0, m.start() - 40):m.end() + 20].replace("\n", " ")))

    # 3b. summary.md is exactly the rendering of summary.json, and its tables carry the right JSON field in the right row
    md = OUT_MD.read_text(encoding="utf-8")
    check(md == render_md(o), "md=render(json)", "summary.ko.md differs from render_md(summary.json)")
    sec = {m.group(1): md[m.end():] for m in re.finditer(r"(?m)^##+ ([\d.]+) ", md)}
    tab = lambda k: md_tables(sec[k])[0]  # noqa: E731
    rowof = lambda rows, *keys: next((r for r in rows if all(any(k == c or c.startswith(k + " ") for c in r) for k in keys)), None)  # noqa: E731
    acc5c = lambda x: [D(x["correct"], 0), D(x["n"], 0), D(x["acc"], 3), D(x["wilson"][0], 3), D(x["wilson"][1], 3)]  # noqa: E731

    def sem(rows, keys, exp, what):
        r = rowof(rows, *keys)
        check(r is not None and _subseq(exp, tnums(r[1:])) and len(tnums(r[1:])) >= len(exp), "md=json semantic", "%s (row %s)" % (what, keys))
    name = {"jev": "Jev (playground)", "english": "Laya english", "multilingual": "Laya multilingual", "router": "Laya Router"}
    for t in T:
        b, m = T[t]["best_laya"], T[t]["mcnemar"][T[t]["best_laya"]]
        exp = [v for s in ("jev",) + RUNNERS for v in acc5c(T[t]["systems"][s])] + [D(m["b"], 0), D(m["c"], 0), D(m["p"], 4), D(T[t]["holm_p"], 4),
                                                                                 D(T[t]["systems"]["jev"]["brier"], 3), D(T[t]["systems"][b]["brier"], 3),
                                                                                 D(T[t]["systems"]["jev"]["ece"], 3), D(T[t]["systems"][b]["ece"], 3)]
        r = next((r for r in tab("2.1") if r[0].startswith(t + " ")), None)
        check(r is not None and _subseq(exp, tnums(r[4:])) and r[-1] == "%s (%s)" % (T[t]["verdict"], T[t]["verdict_holm"]) and r[3] == T[t]["in_training_mix"],
              "md=json semantic", "§2.1 %s row" % t)
    x1 = T["T1"]["extra"]
    for s in ("jev",) + RUNNERS + ("typed-decisions",):
        sem(tab("2.2"), [{"jev": "Jev", "typed-decisions": "참고: Laya typed-decisions"}.get(s, name.get(s))], acc5c(T["T1"]["systems"][s]) + [v for k in ("choice", "noul", "score") for v in acc5c(x1["by_type"][k][s])]
            + [D(x1[s]["soft_acc"], 3), D(x1[s]["brier_vs_soft"], 3), D(x1[s]["score_mae"], 3)], "§2.2 T1 %s" % s)
    for t in ("T5", "T8"):
        X = T[t]["extra"]
        for s in ("jev",) + RUNNERS:
            sem(tab("2.3"), [t, name[s]], acc5c(T[t]["systems"][s]) + [D(X[s]["pred_true"], 0), D(X[s]["fn"], 0), D(X[s]["fp"], 0), D(X[s]["auroc"], 3)]
                + [D(v, 3) for v in X[s]["auroc_ci"]] + ([] if s == "jev" else [D(X[s]["auroc_diff"], 3)] + [D(v, 3) for v in X[s]["auroc_diff_ci"]])
                + [D(X[s]["best_thr_correct"], 0)], "§2.3 %s %s" % (t, s))
    X = T["T6"]["extra"]
    for s in ("jev",) + RUNNERS:
        sem(tab("2.4"), [name[s]], acc5c(T["T6"]["systems"][s]) + [D(X[s]["rounded_correct"], 0), D(T["T6"]["systems"][s]["n"], 0), D(X[s]["rounded_acc"], 3)] + [D(v, 3) for v in X[s]["rounded_wilson"]]
            + [D(X[s]["mae"], 3), D(X[s]["mean_signed"], 3), D(X[s]["within1"], 3)] + [D(v, 0) for v in X[s]["levels_argmax"]], "§2.4 T6 %s" % s)
    for s in ("jev",) + RUNNERS:
        sem(tab("2.5"), [name[s]], [v for L in LANGS for v in (D(pl[L][s]["correct"], 0), D(pl[L][s]["n"], 0), D(pl[L][s]["acc"], 3))] + acc5c(T["T7"]["systems"][s]), "§2.5 T7 %s" % s)
    for m in RUNNERS:
        r = next((r for r in tab("2.5") if r[0].startswith("Jev vs %s" % {"router": "Router"}.get(m, m))), None)
        exp = [v for L in LANGS for v in (D(pl[L][m]["mcnemar"]["b"], 0), D(pl[L][m]["mcnemar"]["c"], 0), D(pl[L][m]["mcnemar"]["p"], 4))] + [
            D(T["T7"]["mcnemar"][m]["b"], 0), D(T["T7"]["mcnemar"][m]["c"], 0), D(T["T7"]["mcnemar"][m]["p"], 4)]
        check(r is not None and _subseq(exp, tnums(r[1:])), "md=json semantic", "§2.5 Jev vs %s" % m)
    A, MAC = o["aggregate"], o["aggregate"]["macro"]
    for k, lab_ in (("english", "Laya english"), ("multilingual", "Laya multilingual"), ("router", "Laya Router"), ("best", "과제별 최고 Laya")):
        d_ = MAC["diff"][k]
        sem(tab("4.2"), [lab_], [D(MAC["acc"][k], 3), D(d_["diff"], 3), D(d_["ci"][0], 3), D(d_["ci"][1], 3), D(d_["share_le0"], 4), D(MAC["without_T1"][k], 3)], "§4.2 %s" % k)
    for k, lab_ in (("best", "과제별 최고 Laya"), ("english", "english 고정"), ("multilingual", "multilingual 고정"), ("router", "Router 고정")):
        x = A["pooled_mcnemar"][k]
        sem(tab("4.3"), [lab_], [D(x["jev_correct"], 0), D(x["n"], 0), D(x["laya_correct"], 0), D(x["n"], 0), D(x["b"], 0), D(x["c"], 0), D(x["p"], 4)]
            + [v for t in POOLED_TASKS for v in (D(x["per_task"][t]["b"], 0), D(x["per_task"][t]["c"], 0))], "§4.3 %s" % k)
    for t in ("T1", "T7"):
        for m in RUNNERS:
            x = A["cluster_bootstrap"][t][m]
            r = next((r for r in tab("4.4") if r[0] == t and r[2].startswith({"router": "Router"}.get(m, m))), None)
            check(r is not None and _subseq([D(x["diff"], 3), D(x["ci"][0], 3), D(x["ci"][1], 3), D(T[t]["mcnemar"][m]["b"], 0), D(T[t]["mcnemar"][m]["c"], 0),
                                             D(T[t]["mcnemar"][m]["p"], 4)], tnums(r[3:])), "md=json semantic", "§4.4 %s %s" % (t, m))
    for t in T:
        j, bb = T[t]["systems"]["jev"], T[t]["systems"][T[t]["best_laya"]]
        r = next((r for r in tab("5.1") if r[0] == t), None)
        check(r is not None and r[5] == {"router": "Router"}.get(T[t]["best_laya"], T[t]["best_laya"]) and _subseq(
            [D(j["brier"], 3), D(j["ece"], 3), D(j["gap_top_minus_acc"], 3), D(j["wrong_ge90"], 0), D(j["wrong"], 0), D(bb["brier"], 3), D(bb["ece"], 3),
             D(bb["gap_top_minus_acc"], 3), D(bb["wrong_ge90"], 0), D(bb["wrong"], 0)], tnums(r[1:])), "md=json semantic", "§5.1 %s" % t)
    for k, lab_ in (("single_choice", "단일 choice"), ("single_boolean", "단일 Boolean"), ("single_score", "단일 score"), ("multi", "Multiple questions")):
        x = o["calibration"]["jev"][k]
        sem(tab("5.2"), [lab_], [D(x["n"], 0), D(x["acc"], 3), D(x["mean_top"], 3), D(x["top100"], 0), D(100 * x["top100_share"], 0), D(x["wrong"], 0),
                                 D(x["wrong_ge90"], 0), D(100 * x["wrong_ge90_share"], 0)], "§5.2 %s" % k)
    cs = T["T7"]["extra"]["consistency"]
    for s in ("jev",) + RUNNERS:
        sem(tab("6.1"), [name[s]], [D(cs[s]["same_all5"], 0), D(cs[s]["ids"], 0), D(cs[s]["pairwise_agree"], 3), D(cs[s]["right_all5"], 0), D(cs[s]["wrong_all5"], 0)]
            + [D(pen[s][L], 3) for L in LANGS[1:]] + [D(pen[s]["mean"], 3)], "§6.1 %s" % s)
    LT = o["latency_tokens"]
    for k, lab_ in (("single_choice", "단일 choice"), ("single_boolean", "단일 Boolean"), ("single_score", "단일 score"), ("multi", "Multiple questions 2~4문항")):
        x = LT["by_type"][k]
        sem(tab("7.1"), [lab_], [D(x["requests"], 0), D(x["displayed_ms"]["median"], 1), D(x["browser_post_ms"]["median"], 1), D(x["post_minus_latency_median"], 1)], "§7.1 %s" % k)
    for t in list(T) + ["전체"]:
        x = LT["by_task"][t] if t != "전체" else LT["all"]
        sem(tab("7.3"), [t], [D(x["requests"], 0), D(x["decisions"], 0), D(x["tokens_in_req_median"], 1), D(x["tokens_out_req_median"], 1), D(x["tokens_per_dec_mean"], 1),
                              D(x["cost_per_1k_dec_usd"], 4)], "§7.3 %s" % t)
    # 3c. the hand-written run card quotes the same key numbers (phrases built from summary.json)
    card = (HERE / "S6_20261007.ko.md").read_text(encoding="utf-8") if (HERE / "S6_20261007.ko.md").exists() else ""
    card = card.replace("\\~", "~")  # the card escapes prose tildes for GitHub (strikethrough); the phrases use plain "~"
    f3, sg = (lambda x: "%.3f" % x), (lambda x: ("%+.3f" % x).replace("-", "−"))
    cb = A["cluster_bootstrap"]
    det, oo, lt_ = o["robustness"]["determinism"], o["robustness"]["option_order"], LT["all"]
    E_ = {k: v["value"] for k, v in o["external"].items()}
    d1 = [E_[k] for k in ("d1_english_cpu_1q", "d1_multilingual_cpu_1q", "d1_english_mps_1q", "d1_multilingual_mps_1q")]
    for phrase in ("Jev %s, english %s, multilingual %s, Router %s" % tuple(f3(MAC["acc"][k]) for k in ("jev", "english", "multilingual", "router")),
                   "in-process %g~%g (D1), HTTP %g (P2)" % (min(d1), max(d1), E_["p2_poc_decide_p50"]),
                   "Jev − Router %s [%s, %s]" % (sg(MAC["diff"]["router"]["diff"]), sg(MAC["diff"]["router"]["ci"][0]), sg(MAC["diff"]["router"]["ci"][1])),
                   "%d항목, b/c %d/%d, p=%.4f" % (A["pooled_mcnemar"]["best"]["n"], A["pooled_mcnemar"]["best"]["b"], A["pooled_mcnemar"]["best"]["c"], A["pooled_mcnemar"]["best"]["p"]),
                   "Router 고정 %d/%d, p=%.4f" % (A["pooled_mcnemar"]["router"]["b"], A["pooled_mcnemar"]["router"]["c"], A["pooled_mcnemar"]["router"]["p"]),
                   "T1 Jev − english %s [%s, %s]" % (sg(cb["T1"]["english"]["diff"]), sg(cb["T1"]["english"]["ci"][0]), sg(cb["T1"]["english"]["ci"][1])),
                   "T7 Jev − multilingual %s [%s, %s]" % (sg(cb["T7"]["multilingual"]["diff"]), sg(cb["T7"]["multilingual"]["ci"][0]), sg(cb["T7"]["multilingual"]["ci"][1])),
                   "보정 전: Jev 유의 우세 %d (%s)" % (A["verdicts"].get("Jev 유의 우세", 0), ", ".join(t for t in T if T[t]["verdict"] == "Jev 유의 우세")),
                   "Holm 후: %d (%s)" % (A["verdicts_holm"].get("Jev 유의 우세", 0), ", ".join(t for t in T if T[t]["verdict_holm"] == "Jev 유의 우세")),
                   "T2 Jev %s [%.3f, %.3f], T3 Jev %s [%.3f, %.3f]" % (f3(T["T2"]["systems"]["jev"]["acc"]), *T["T2"]["systems"]["jev"]["wilson"], f3(T["T3"]["systems"]["jev"]["acc"]), *T["T3"]["systems"]["jev"]["wilson"]),
                   "%s / %s" % (sg(o["representativeness"]["T2"]["diff"]), sg(o["representativeness"]["T3"]["diff"])), sg(o["representativeness"]["T1"]["diff"]),
                   "T5 Jev %s vs english %s, T8 Jev %s vs english %s" % tuple(f3(T[t]["systems"][s]["acc"]) for t in ("T5", "T8") for s in ("jev", "english")),
                   "AUROC T5 %s vs %s" % (f3(T["T5"]["extra"]["jev"]["auroc"]), f3(T["T5"]["extra"]["english"]["auroc"])),
                   "T6 Jev %s vs english %s" % (f3(T["T6"]["extra"]["jev"]["mae"]), f3(T["T6"]["extra"]["english"]["mae"])),
                   "%s [%s, %s]" % (sg(T["T6"]["extra"]["english"]["mae_diff"]), sg(T["T6"]["extra"]["english"]["mae_diff_ci"][0]), sg(T["T6"]["extra"]["english"]["mae_diff_ci"][1])),
                   "p=%.4f" % T["T6"]["mcnemar"]["english"]["p"],
                   "Jev 과제별 %s~%s, 최고 Laya %s~%s" % (f3(min(T[t]["systems"]["jev"]["ece"] for t in T)), f3(max(T[t]["systems"]["jev"]["ece"] for t in T)),
                                                    f3(min(T[t]["systems"][T[t]["best_laya"]]["ece"] for t in T)), f3(max(T[t]["systems"][T[t]["best_laya"]]["ece"] for t in T))),
                   "Jev 표시값 %g, 브라우저 POST %g (성공 %d건)" % (lt_["displayed_ms"]["median"], lt_["browser_post_ms"]["median"], lt_["requests"]),
                   "$%.4f (decision당 평균 %.1f 토큰)" % (lt_["cost_per_1k_dec_usd"], lt_["tokens_per_dec_mean"]),
                   "Jev 라벨 %d/%d, 확률 벡터 %d/%d, flip %d/%d" % (det["same_label"], det["rows"], det["identical_probs"], det["rows"], oo["jev_flips"], oo["rows"]),
                   "%.0f~%.0f분(중앙 %.0f분)" % (det["resend_after_min_range"][0], det["resend_after_min_range"][1], det["resend_after_min_median"]),
                   "english %d/%d, multilingual %d/%d, Router %d/%d" % tuple(x for k in ("english", "multilingual", "router") for x in (A["pooled_mcnemar"][k]["b"], A["pooled_mcnemar"][k]["c"])),
                   "411줄(성공 %d, %d decision)" % (lt_["requests"], lt_["decisions"]), "청록(대비 %g)과 노랑(%g)" % (o["figures"]["palette"]["slots4_adjacent"]["below_3to1"]["#1baf7a"],
                                                                                            o["figures"]["palette"]["slots4_adjacent"]["below_3to1"]["#eda100"])):
        check(phrase in card, "card=json", "run card lacks '%s'" % phrase)

    # 4. figure data == table data
    F = o["figures"]
    for t in T:
        for s in F["accuracy_by_task"]["series"]:
            check(F["accuracy_by_task"]["values"][t][s] == T[t]["systems"][s]["acc"] and F["accuracy_by_task"]["wilson"][t][s] == T[t]["systems"][s]["wilson"],
                  "figure=table", "accuracy_by_task %s %s" % (t, s))
    for L in LANGS:
        for s in F["t7_languages"]["series"]:
            check(F["t7_languages"]["values"][L][s] == pl[L][s]["acc"] and F["t7_languages"]["wilson"][L][s] == pl[L][s]["wilson"], "figure=table", "t7 %s %s" % (L, s))
    E = {k: v["value"] for k, v in o["external"].items()}
    one, multi = o["latency_tokens"]["single_all"], o["latency_tokens"]["by_type"]["multi"]
    want = [one["displayed_ms"]["median"], multi["displayed_ms"]["median"], one["browser_post_ms"]["median"], multi["browser_post_ms"]["median"],
            E["d6_mps_1q_c1_p50"], E["d6_cpu_1q_c1_p50"], E["p2_poc_decide_p50"], E["d1_english_cpu_1q"], E["d1_english_mps_1q"], E["d1_multilingual_cpu_1q"],
            E["d1_multilingual_mps_1q"], E["d1c_multilingual_cpu_1q_gap1000"], E["d1c_multilingual_mps_1q_gap1000"]]
    got = [r["median"] for r in F["latency"]["rows"] if "median" in r]
    check(got == want, "figure=table", "latency medians %s != %s" % (got, want))
    band = [r for r in F["latency"]["rows"] if "lo" in r]
    check(len(band) == 1 and (band[0]["lo"], band[0]["hi"]) == (E["readme_jev_p50_lo"], E["readme_jev_p50_hi"]), "figure=table", "latency band")
    for name in ("accuracy_by_task", "t7_languages", "latency"):
        for ext in ("png", "svg"):
            check((FIGS / ("%s.%s" % (name, ext))).stat().st_size > 10_000, "figure=table", "%s.%s missing or empty" % (name, ext))
    check(all(v["all_pass"] for k, v in F["palette"].items() if k != "validator"), "figure=table", "palette validator did not pass")

    # 5. cited external values are on the cited lines
    for k, (v, f, ln) in EXT.items():
        line = (ROOT / f).read_text(encoding="utf-8").splitlines()[ln - 1].replace(",", "")
        check(any(x in line for x in ("%g" % v, "%.3f" % v, "%.2f" % v, "%.1f" % v)), "external", "%s=%s not on %s:%d" % (k, v, f, ln))

    for f, ln, frag in (("third_party/laya/README.md", 1530, "fast base to specialise, not as a zero-shot decision engine"),
                        ("third_party/laya/README.md", 1300, "after domain temperature fitting"),
                        ("results/P4/metrics/full_20261003-1156_summary.md", 19, "| ko_massive_domain_8 | ft-v1 | domain | test | 250 | 0.900 [0.860, 0.936]")):
        check(frag in (ROOT / f).read_text(encoding="utf-8").splitlines()[ln - 1], "external", "'%s' not on %s:%d" % (frag, f, ln))

    print("checks passed: %s" % ", ".join("%s %d" % kv for kv in sorted(n_ok.items())))
    if fails:
        print("MISMATCHES (%d):\n  %s" % (len(fails), "\n  ".join(fails)))
        sys.exit(1)
    print("no mismatches")


if __name__ == "__main__":
    {"build": build, "verify": verify}[sys.argv[1]]()
