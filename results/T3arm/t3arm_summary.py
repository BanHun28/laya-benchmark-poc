"""S3 synthesis of the 3-arm comparison: Jev vs vanilla Laya vs trained Laya (docs/11_three_arm_plan.md §5, §7).
No model call, no torch or laya import, no request to the Jev site: reports, records and logs only.

    nice -n 10 .venv/bin/python results/T3arm/t3arm_summary.py build  [--root results/T3arm] [--out results/T3arm]
    nice -n 10 .venv/bin/python results/T3arm/t3arm_summary.py verify [--root results/T3arm] [--out results/T3arm]

build writes <out>/summary.json, <out>/summary.ko.md and <out>/figs/. verify rebuilds the json from the inputs, checks
that summary.ko.md is its rendering, that every number in the md is a json number and that every table row carries its
json fields, and cross-checks the inputs (F's summary.json for Jev and vanilla on T1-T8, session S7's master lines and
analyze output for T9 and T10, the driver's paired_<stem>.json, summary.json and select.json of both training runs,
calib_sep/, validity/); it prints the mismatch count and exits 1 on any.

Arms (docs/11 §2). Jev: results/F/jev_cmp/jev_runs_all.jsonl as s6_summary reads it (T1-T8 as F's summary.json, T9 and
T10 from session S7 by the same functions). vanilla: the trained arm's base without training (english; T7 multilingual),
results/F/jev_cmp/laya/ for the T1-T8 Jev sets and results/T3arm/vanilla/ otherwise (run_all_tasks.sh vanilla_of).
vanilla + task T (calibration only): results/T3arm/calib_sep/<task>/, the base weights with the temperature fitted on the
task's calib rows. trained: run 1 <root>/<task>/{jev,ext}_<stem>.json, run 2 (torch seed 14) <root>/rep_s14/<task>/.
A task without `STEP <task>:cleanup OK` in its run_all_status.log is "결과 없음" and stays out of the tests and
aggregates. Decisions pair by item id (`<stem>/<id tag>/<qid>`, the Jev playground item id), so a SMOKE root, whose
reports cover the first rows only, pairs with the full Jev and vanilla sets on the rows it has.
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "results/F/jev_cmp"), str(ROOT / "poc/finetune")]
import s6_summary as S6  # noqa: E402  (imports jev_cmp and laya_summary and puts scripts/ on sys.path)
import t3arm_metrics as TM  # noqa: E402
from metrics_extra import coverage_table, mcnemar_exact  # noqa: E402

J, LS = S6.J, S6.LS
TASKS = tuple("T%d" % k for k in range(1, 11))
CATS = {"incl": ("T2", "T5", "T9", "T10"), "excl": ("T1", "T3", "T4", "T6", "T7", "T8")}  # Laya training mix, docs/11 §2
CAT_KO = {"incl": "포함", "excl": "제외"}
NEW = {"T9": ("Enron spam", "boolean"), "T10": ("support tickets", "choice")}
FAMS = {"trained_vs_jev": ("trained", "Jev"), "trained_vs_vanilla": ("trained", "vanilla"), "jev_vs_vanilla": ("Jev", "vanilla")}
DIFFS = (("jev", "vanilla"), ("trained", "vanilla"), ("trained", "jev"))
ARM_KO = {"jev": "Jev", "vanilla": "vanilla", "trained": "trained"}
ARMS = tuple(ARM_KO)
EXT = ROOT / "data/evals/jev_cmp_ext"
VALID = ROOT / "results/T3arm/validity"
CALIB, CALIB_KO = ROOT / "results/T3arm/calib_sep", "vanilla + 과제 T"
REP, SEEDS = "rep_s14", (13, 14)  # the repeat run's directory under the root and the torch seeds of run 1 and run 2
AGREE = (("trained_vs_jev", "Jev 항목 trained vs Jev"), ("trained_vs_vanilla", "Jev 항목 trained vs vanilla"), ("ext", "ext trained vs vanilla"))
S7 = "S7"  # Jev session of T9 and T10, after F's summary (F stays T1-T8)
SMOKE_LOG = ROOT / "results/T3arm/smoke_20261008-1021/run_all_status.log"  # the prep's driver smoke (PREP_20261008.md §6)
ALPHA, BUDGETS = 0.05, (0.05, 0.1)
V2_TOL, V2_MIN, V2_MAJORITY, V3_MARGIN, V3_GAP = 0.02, 0.562, 0.461, 0.05, 0.30  # docs/11 §4: V2 (a) and (b), V3 criteria
V3_USER = {"verdict": "통과", "date": "2026-10-08", "source": "PREP_20261008.md \"프로젝트 책임자 결정\" 1"}
T_TYPES = ("choice", "score", "noul")  # rl_agent_config temperature order
NONE, NA = "결과 없음", "해당 없음"
TRACE_SEGMENTS = ((0, 11), (12, 39), (40, 99), (100, 299), (300, 624), (625, 1249))  # micro-batch index ranges, T1: 625 per epoch
# causes of the "학습 실패" flags, traced after the run (PREP_20261008.md "본 학습 중 발견" sections)
FAIL_CAUSES = {  # numbers stay in the JSON-backed tables (§2.1, §6.1) and in PREP
    "T5": "dev가 BoolQ train split에서 왔고 BoolQ는 upstream 학습 믹스에 있다. vanilla가 그 행을 기억해 dev 기준선이 부풀었다. validation 기반 ext에서는 vanilla와 trained가 같다(§2.1)",
    "T9": "천장 효과다. dev 차이는 1,000행 중 1행이고, vanilla의 dev와 ext가 거의 같아 기억 신호는 없다",
    "T10": "dev는 자연 분포라 Technical Support 몫이 가장 크고 train·ext는 균등에 가깝다. vanilla는 이 큐로 예측이 쏠려 있다. trained는 dev의 8개 큐 중 7개에서 recall이 오르고 dev macro recall도 오른다",
}
# s6_summary's figure helpers look series up by key; the three arms take F's validated categorical slots 1-3
S6.PAL.update(vanilla=S6.PAL["english"], trained=S6.PAL["multilingual"])
S6.SYS_LABEL.update(vanilla="vanilla Laya", trained="trained Laya")
# the master log gained S7's lines after F's summary; master_records checks the log against these sessions' logs
S6.SESSIONS += (S7,)


def rj(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rel(p):
    p = Path(p).resolve()
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


def base(t):
    return "multilingual" if t == "T7" else "english"


def name(t):
    return S6.TASKS[t]["name"].replace(" x5", "") if t in S6.TASKS else NEW[t][0]


def kind(t):
    return S6.TASKS[t]["kind"] if t in S6.TASKS else NEW[t][1]


def cat(t):
    return next(c for c, ts in CATS.items() if t in ts)


def sets(t, layer):
    if layer == "jev" and t in S6.TASKS:
        return S6.TASKS[t]["sets"]
    return [p.stem for p in sorted((J.DATA if layer == "jev" else EXT).glob(t + "_*.jsonl"))]


def vanilla_report(t, layer, stem):  # run_all_tasks.sh vanilla_of
    d = S6.HERE / "laya" if layer == "jev" and t in S6.TASKS else ROOT / "results/T3arm/vanilla"
    return d / ("%s_%s.json" % (stem, base(t)))


def cluster(t, i):  # T1 decisions share a case, T7 languages share a MASSIVE id
    return i.split("/")[1] if t in ("T1", "T7") else i


# ---------------------------------------------------------------- per-decision inputs
def decisions(path, out):
    """laya_summary.decisions. A SMOKE report names a cut copy in a temp dir the driver deleted (run_all_tasks.sh
    cut_copy: the source's `#` lines, one `# smoke copy` line, its first rows); the copy is rebuilt under
    <out>/smoke_inputs/ and must hash to the report's dataset_sha256."""
    rep = rj(path)
    ds = Path(rep["config"]["dataset"])
    if (ROOT / ds).exists():
        return LS.decisions(path)
    src = (J.DATA if ds.parent.name == "jev" else EXT) / ds.name
    lines = src.read_text(encoding="utf-8").split("\n")
    body = [x for x in lines if x.strip() and not x.startswith("#")]
    k = q = 0
    while q < len(rep["cases"]):
        q, k = q + len(json.loads(body[k])["expected"]), k + 1
    text = "\n".join([x for x in lines if x.startswith("#")] + ["# smoke copy: first %d of %d rows of %s" % (k, len(body), rel(src))]
                     + body[:k]) + "\n"
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == rep["config"]["dataset_sha256"], path
    d = out / "smoke_inputs" / path.parent.name
    d.mkdir(parents=True, exist_ok=True)
    (d / ds.name).write_text(text, encoding="utf-8")
    rep["config"]["dataset"] = str(d / ds.name)
    (d / path.name).write_text(json.dumps(rep), encoding="utf-8")
    return LS.decisions(d / path.name)


def recs(path, stem, out):
    """{item id: laya_summary decision} of one report."""
    rep, ds = decisions(path, out)
    tags = [next(x[3:] for x in c["tags"] if x.startswith("id:")) for c in rep["cases"]]
    return {"%s/%s/%s" % (stem, i, d["qid"]): d for i, d in zip(tags, ds)}


def gold(layer):
    """T1 teacher distributions by (row, qid), t3arm_metrics.GOLD."""
    d = J.DATA if layer == "jev" else EXT
    return {(g["row"], g["qid"]): g for g in rj(TM.GOLD["%s/%s.jsonl" % (rel(d), sets("T1", layer)[0])])["decisions"]}


def s7_task(t, master):
    """T9, T10 (session S7) as s6_summary.load_task and build_task make an F task: the entry in F's summary.json shape
    (systems, mcnemar, extra) and the per-item systems."""
    stems = sets(t, "jev")
    its = [it for s in stems for it in J.load_items(s)[1]]
    by_id = {d["id"]: (r, d) for r in master if r["session"] == S7 and r["set"] in stems and r.get("decisions") and r["phase"] == "main"
             for d in r["decisions"]}
    assert sorted(by_id) == sorted(it["id"] for it in its), t
    laya = {m: {k: c for s in stems for k, c in J.laya_cases(s, m, J.load_items(s)[1])[1].items()} for m in S6.RUNNERS}
    S, extra = {"boolean": S6.systems_boolean, "choice": S6.systems_choice}[kind(t)](its, by_id, laya)
    entry = {"systems": {s: {**S6.summ(v["cor"], v["conf"], v["brier"]), "item_correct": S6.bits(v["cor"])} for s, v in S.items()},
             "mcnemar": {m: S6.mcn(S["jev"]["cor"], S[m]["cor"], S["jev"]["pred"], S[m]["pred"]) for m in S6.RUNNERS}, "extra": extra}
    S["_items"] = its
    return entry, S


def jev_items(t, master):
    """Jev's correctness and top probability per item id, as s6_summary builds them (T1: its 120 comparable decisions)."""
    if t == "T1":
        form = {(it["row"], it["qid"]): it["id"] for it in J.load_items(sets(t, "jev")[0])[1]}
        return {form[d["row"], d["qid"]]: {"correct": d["pred"] == d["gold"], "conf": d["conf"]} for d in S6.t1_systems(master)[0]["jev"]}
    S = (S6.build_task if t in S6.TASKS else s7_task)(t, master)[1]
    return {it["id"]: {"correct": c, "conf": f} for it, c, f in zip(S["_items"], S["jev"]["cor"], S["jev"]["conf"])}


# ---------------------------------------------------------------- statistics
def coverage(rows):
    best = coverage_table(rows, [], BUDGETS)[1]
    return {"cov05": best[str(BUDGETS[0])]["coverage"], "cov10": best[str(BUDGETS[1])]["coverage"]}


def stats(t, ds, g=None):
    """Accuracy (Wilson), Brier, ECE (15 bins), max coverage at 5% / 10% error, and the docs/09 side metric of the task."""
    m = LS.metrics(ds)
    s = {"correct": m["correct"], "n": m["n"], "acc": m["accuracy"], "wilson": list(m["wilson"]), "brier": m["brier"], "ece": m["ece"],
         **coverage([{"conf": d["conf"], "correct": d["pred"] == d["gold"]} for d in ds])}
    if kind(t) == "boolean":
        s["auroc"] = J.auroc([d["p"][1] for d in ds], [d["gold"] for d in ds])
    if kind(t) == "score":
        s["mae"] = S6.mean(abs(d["score"] - d["gold"]) for d in ds)
    if g is not None:
        x = LS.t1_extra(ds, [g[d["row"], d["qid"]] for d in ds])
        s.update(soft_acc=x["soft_accuracy"], brier_vs_soft=x["brier_vs_soft"], score_mae=x["score_mae"],
                 acc_vs_label=x["accuracy_vs_upstream_label"], by_type=x["by_question_type"])
    return s


def jev_stats(t, F, per):
    """Jev's numbers from results/F/jev_cmp/summary.json (T9, T10: s7_task's entry), coverage from its per-item top probability."""
    x, X = F["tasks"][t]["systems"]["jev"], F["tasks"][t]["extra"].get("jev", {})
    return {**{k: x[k] for k in ("correct", "n", "acc", "wilson", "brier", "ece")}, **coverage(list(per.values())),
            **{k: X[k] for k in ("auroc", "mae", "soft_acc", "brier_vs_soft", "score_mae") if k in X}}


def paired(a, b):
    """Item ids two arms both have and their correctness on them."""
    ids = sorted(set(a) & set(b))
    return ids, [a[i] for i in ids], [b[i] for i in ids]


def test(t, a, b):
    """Exact McNemar of arm a vs arm b on the items both have (b = only a right, c = only b right); T1 and T7 add the
    cluster bootstrap of the accuracy difference a - b."""
    ids, ca, cb = paired(a, b)
    m = S6.mcn(ca, cb)
    if t in ("T1", "T7"):
        m["boot"] = S6.cluster_boot(ca, cb, [cluster(t, i) for i in ids])
    return m


def driver_pair(root, t, layer):
    """The driver's paired_<stem>.json (a = vanilla, b = trained), summed over T7's five language files."""
    ps = [rj(root / t / ("paired_%s.json" % s)) for s in sets(t, layer)]
    b, c, n = (sum(p[k] for p in ps) for k in ("b_only", "a_only", "n"))
    return {"b": b, "c": c, "n": n, "p": mcnemar_exact(b, c), "delta": sum(p["delta_b_minus_a"] * p["n"] for p in ps) / n}


def cat_boot(vals):
    """Mean of per-task values per category with a percentile bootstrap over tasks (resampled within the category) and
    the contrast excl - incl; for Jev - vanilla the contrast is Q1's difference-in-differences."""
    rng = np.random.default_rng(S6.SEED)
    q = lambda a: [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]  # noqa: E731
    out, bs = {}, {}
    for c, ts in CATS.items():
        have = [t for t in ts if t in vals]
        out[c] = None
        if have:
            v = np.array([vals[t] for t in have])
            bs[c] = v[rng.integers(0, len(v), (S6.N_TASK_BOOT, len(v)))].mean(1)
            out[c] = {"tasks": have, "mean": float(v.mean()), "ci": q(bs[c])}
    out["contrast"] = {"diff": out["excl"]["mean"] - out["incl"]["mean"], "ci": q(bs["excl"] - bs["incl"])} if len(bs) == 2 else None
    return out


# ---------------------------------------------------------------- per task
def diag(root, t):
    """docs/11 §4 diagnostics from the driver's diagnostics.json (t3arm_metrics.py diag)."""
    g = rj(root / t / "diagnostics.json")
    rc0, rc1 = (g["class_recall_dev"][k] for k in ("epoch0_vanilla", "selected"))
    dr = {k: rc1[k] - rc0[k] for k in rc0}
    lo, hi = min(dr, key=dr.get), max(dr, key=dr.get)
    f = g.get("option_order_flip_dev40")
    return {"dev": [g["dev"]["epoch0_vanilla"]["accuracy"]] + g["dev"]["accuracy"], "dev_reports": g["dev"]["reports"],
            "selected_epoch": g["dev"]["reports"].index(g["dev"]["selected"]) + 1, "recalibrated": "recalibrated_epoch" in g,
            "train_acc_last": g["train_vs_dev_gap"]["train_acc_last_window"], "gap": g["train_vs_dev_gap"]["gap"],
            "temperature": g["selected_temperature"],
            "clamp": {k: g["temperature_clamp"][k] for k in ("outside_load_range", "at_script_bound")},
            "t_default": [T_TYPES[i] for i in g["temperature_clamp"]["default_1.2_for_types_without_calibration_rows"]],
            "flip": f and {k: f[k] for k in ("n_items", "flip_rate_per_perm", "flip_rate_per_perm_ci", "any_flip_rate")},
            "recall": {"up": sum(v > 0 for v in dr.values()), "down": sum(v < 0 for v in dr.values()),
                       "same": sum(v == 0 for v in dr.values()), "min": [lo, dr[lo]], "max": [hi, dr[hi]]},
            "failed": g["training_failed"]}


def cost(root, t, smoke):
    """Q3: labels, train time, throughput and MPS peak memory (run_ft timing report), size of the kept checkpoint."""
    r = rj(root / t / "train_timing.json")
    ck = ROOT / "poc/finetune/ckpt_t3arm" / t  # SMOKE checkpoints lived in a temp dir the driver deleted
    out = {"train_items": r["n_train_items"], "calib_items": r["calibration_rows"]["n"], "dev_items": len(rj(root / t / "dev_ep0.json")["cases"]),
           "item_sources": r["item_sources"], "epochs": r["epochs"], "optimizer_steps": r["optimizer_steps"],
           "train_loop_min": r["phases_s"]["train_loop"] / 60, "wall_min": r["wall_s"] / 60, "items_per_s": r["throughput"]["train_items_per_s"],
           "mps_alloc_gb": r["memory_gb"]["mps_current_allocated_peak"], "mps_driver_gb": r["memory_gb"]["mps_driver_allocated_peak"],
           "ckpt": rel(ck), "ckpt_gb": None if smoke or not ck.is_dir() else sum(f.stat().st_size for f in ck.rglob("*") if f.is_file()) / 1e9}
    out["labels"] = out["train_items"] + out["calib_items"] + out["dev_items"]
    return out


def calib(t, items, ext):
    """vanilla + task T (calib_sep/<task>/): the temperatures its 0-step export carries (the fit, then laya's load clamp), its
    answers against vanilla's (same_<stem>.json) and the ECE / Brier split into refit (calib - vanilla) and training
    (trained - calib)."""
    ck = rj(CALIB / t / ("jev_%s.json" % sets(t, "jev")[0]))["config"]["checkpoint"]
    sm = {s: rj(CALIB / t / ("same_%s.json" % s)) for s in sets(t, "jev") + sets(t, "ext")}
    return {"temperature_raw": ck["temperature_raw"], "temperature_applied": ck["temperature_applied"],
            "same": {**{k: sum(x[k] for x in sm.values()) for k in ("decisions", "argmax_agreement", "argmax_agreement_ties_agree", "correct_identical")},
                     "strict_diff": [s for s, x in sm.items() if x["argmax_agreement"] < x["decisions"]]},
            "effect": {k: {m: {"refit": X["calib"][m] - X["vanilla"][m], "train": X["trained"][m] - X["calib"][m] if X["trained"] else None}
                           for m in ("ece", "brier")} for k, X in (("items", items), ("ext", ext))}}


def task(t, root, out, F, master, done, smoke):
    js, xs = sets(t, "jev"), sets(t, "ext")
    load = lambda pairs: {i: d for p, s in pairs for i, d in recs(p, s, out).items()}  # noqa: E731
    D = {"vanilla": load((vanilla_report(t, "jev", s), s) for s in js), "vanilla_ext": load((vanilla_report(t, "ext", s), s) for s in xs),
         "calib": load((CALIB / t / ("jev_%s.json" % s), s) for s in js), "calib_ext": load((CALIB / t / ("ext_%s.json" % s), s) for s in xs),
         "trained": load((root / t / ("jev_%s.json" % s), s) for s in js) if done else {},
         "trained_ext": load((root / t / ("ext_%s.json" % s), s) for s in xs) if done else {}}
    cor = {k: {i: d["pred"] == d["gold"] for i, d in v.items()} for k, v in D.items()}
    jev = jev_items(t, master)
    cor["jev"] = {i: x["correct"] for i, x in jev.items()}
    G = {"jev": gold("jev"), "ext": gold("ext")} if t == "T1" else {"jev": None, "ext": None}
    keep = (lambda i: i in jev) if t == "T1" else (lambda i: True)  # T1: the 120 decisions Jev answered
    st = lambda k, layer, f=keep: stats(t, [d for i, d in D[k].items() if f(i)], G[layer]) if D[k] else None  # noqa: E731
    ck = {a: {i: c for i, c in cor[a].items() if keep(i)} for a in ("vanilla", "trained")}
    items = {"n": len(ck["vanilla"]), "jev": jev_stats(t, F, jev), "vanilla": st("vanilla", "jev"), "calib": st("calib", "jev"),
             "trained": st("trained", "jev"), "tests": {}}
    if t in ("T1", "T7"):
        items["clusters"] = len({cluster(t, i) for i in ck["vanilla"]})
    if t == "T1":  # the Laya arms on all 200 decisions too
        items["all"] = {a: st(a, "jev", lambda i: True) for a in ("vanilla", "trained")}
    if t == "T7":
        lang = lambda i: i.split("/")[0].split("_")[4]  # noqa: E731
        items["per_lang"] = {L: {a: {"correct": sum(c for i, c in cc.items() if lang(i) == L), "n": sum(lang(i) == L for i in cc)}
                                 for a, cc in (("jev", cor["jev"]), ("vanilla", ck["vanilla"]), ("trained", ck["trained"])) if cc}
                             for L in S6.LANGS}
        for x in items["per_lang"].values():
            for v in x.values():
                v["acc"] = v["correct"] / v["n"]
    # F's McNemar of Jev vs the base runner (b = only Jev right; T9, T10 s7_task's) and, for T1 / T7, its cluster bootstrap
    fm = F["tasks"][t]["mcnemar"][base(t)]
    items["tests"]["jev_vs_vanilla"] = {**{k: fm[k] for k in ("b", "c", "p", "n")},
                                        **({"boot": F["aggregate"]["cluster_bootstrap"][t][base(t)]} if t in ("T1", "T7") else {})}
    if done:
        items["tests"]["trained_vs_jev"] = test(t, ck["trained"], cor["jev"])
        items["tests"]["trained_vs_vanilla"] = test(t, ck["trained"], ck["vanilla"])
        if t == "T1":
            items["all_test"] = driver_pair(root, t, "jev")
    ext = {"n": len(cor["vanilla_ext"]), "vanilla": st("vanilla_ext", "ext", lambda i: True), "calib": st("calib_ext", "ext", lambda i: True),
           "trained": st("trained_ext", "ext", lambda i: True)}
    if done:  # McNemar and delta from the driver's paired files, the bootstrap on the same paired items
        ids, ct, cv = paired(cor["trained_ext"], cor["vanilla_ext"])
        ext["test"] = {**driver_pair(root, t, "ext"), "boot": S6.cluster_boot(ct, cv, [cluster(t, i) for i in ids])}
    o = {"name": name(t), "kind": kind(t), "base": base(t), "category": cat(t), "done": done, "jev_sets": js, "ext_sets": xs,
         "items": items, "ext": ext, "calib": calib(t, items, ext)}
    if done:
        o.update(diag=diag(root, t), cost=cost(root, t, smoke))
    return o, cor


def aggregate(T):
    out = {}
    for layer, arms in (("items", ("jev", "vanilla", "trained")), ("ext", ("vanilla", "trained"))):
        A = {a: {t: T[t][layer][a]["acc"] for t in TASKS if T[t][layer].get(a)} for a in arms}
        out[layer] = {"macro": {a: cat_boot(A[a]) for a in arms},
                      "diff": {"%s-%s" % (a, b): cat_boot({t: A[a][t] - A[b][t] for t in A[a] if t in A[b]}) for a, b in DIFFS
                               if a in A and b in A}}
    sm = [T[t]["calib"]["same"] for t in TASKS]
    out["calib_same"] = {**{k: sum(x[k] for x in sm) for k in sm[0] if k != "strict_diff"}, "strict_diff": [s for x in sm for s in x["strict_diff"]]}
    out["calib_same"]["strict_mismatch"] = out["calib_same"]["decisions"] - out["calib_same"]["argmax_agreement"]
    return out


def label_check(cor, out):
    """T10 Jev items, whose misses S7_summary.md §3.6 reads as label problems: the rows that every system misses and the
    correct count per gold queue, for Jev, vanilla english, vanilla multilingual (a reference runner) and trained."""
    stem = sets("T10", "jev")[0]
    its = J.load_items(stem)[1]
    ml = recs(J.laya_report(stem, "multilingual"), stem, out)
    sy = {"jev": cor["jev"], "english": cor["vanilla"], "multilingual": {i: d["pred"] == d["gold"] for i, d in ml.items()}, "trained": cor["trained"]}

    def count(sel, k):
        c = [sy[k][it["id"]] for it in sel if it["id"] in sy[k]]
        return {"correct": sum(c), "n": len(c), "acc": sum(c) / len(c) if c else None}

    def missed(ks):
        have = [it for it in its if all(it["id"] in sy[k] for k in ks)]
        rows = [it["row"] for it in have if not any(sy[k][it["id"]] for k in ks)]
        return {"wrong": len(rows), "n": len(have), "rows": rows}
    return {"systems": list(sy), "queues": {q: {k: count([it for it in its if it["gold"] == q], k) for k in sy} for q in map(J.key_of, its[0]["options"])},
            "total": {k: count(its, k) for k in sy}, "all_wrong": missed(list(sy)), "all_wrong_without_trained": missed(("jev", "english", "multilingual"))}


def jev_rows(o):
    """Pop the row lists of the T10 label check: they pair items with Jev's outcome, and Jev results are published as
    aggregates only (owner decision 2026-10-12). build drops them from summary.json, verify checks them against S7 analyze."""
    lc = o["tasks"]["T10"]["items"]["label_check"]
    return {k: lc[k].pop("rows") for k in ("all_wrong", "all_wrong_without_trained")}


def validity(T):
    """V1-V6 from results/T3arm/validity/ and the V3 numbers against the main run's T3 epoch 1 (V3's verdict is the user's)."""
    v1 = {}
    for b in ("english", "multilingual"):
        e, s1, s0 = (rj(VALID / ("V1_%s_%s.json" % (b, k))) for k in ("export_diff", "same", "basetemp_same"))
        v1[b] = {"tensors": e["tensors"], "values_equal": e["values_equal"], "argmax": s1["argmax_agreement"], "decisions": s1["decisions"],
                 "basetemp_identical": s0["answers_identical"], "ece_base_t": s1["ece"][0], "ece_refit_t": s1["ece"][1], "ref": s1["ref"]}
    m = rj(VALID / "V2_upstream_repro.json")
    pick = lambda x: {"acc_vs_label": x["accuracy_vs_label (upstream's)"], "acc": x["accuracy_vs_argmax_gold"], "soft_acc": x["soft_accuracy"],  # noqa: E731
                      "brier_vs_soft": x["brier_vs_soft"], "ece": x["ece"], "score_mae": x["score_mae"], "by_type": x["by_question_type"]}
    v3, d3 = rj(VALID / "V3_label_shuffle.json"), T["T3"].get("diag")
    real = next((a for r, a in zip(d3["dev_reports"], d3["dev"][1:]) if r.endswith("/dev_ep1.json")), None) if d3 else None
    p, maj, van = v3["dev_accuracy"]["permuted"], v3["majority"], v3["dev_accuracy"]["vanilla_english"]
    v4 = rj(VALID / "V4_format_identity.json")
    v6 = rj(VALID / "V6_leakage.json")["tasks"]
    sm = SMOKE_LOG.read_text(encoding="utf-8").splitlines()
    rows = lambda key: sum(x["%s_rows_matching_any_eval_item" % s][key] for x in v6.values() for s in ("train", "dev", "calib"))  # noqa: E731
    return {
        "V1": {**v1, "met": all(x["values_equal"] == x["tensors"] and x["argmax"] == x["basetemp_identical"] == x["decisions"] for x in v1.values())},
        "V2": {"upstream": pick(m["models"]["typed-decisions"]), "published": m["models"]["typed-decisions"]["published"][0],
               "ours": pick(m["models"]["v2-T1"]), "english": pick(m["models"]["english"]), "min": V2_MIN, "majority": V2_MAJORITY,
               "tolerance": V2_TOL, "met": all(m["criteria"].values())},
        "V3": {"permuted": p, "majority": maj, "real_prep": v3["dev_accuracy"]["real"], "vanilla_prep": van,
               "vanilla_s2": d3["dev"][0] if d3 else None, "real_ep1_s2": real, "margin": V3_MARGIN, "gap": V3_GAP,
               "a_threshold": maj + V3_MARGIN, "a_excess": p - (maj + V3_MARGIN), "b_diff": None if real is None else real - p,
               "b_excess": None if real is None else real - p - V3_GAP, "c_vanilla_minus_permuted": van - p, "user": V3_USER},
        "V4": {"tasks": len(v4), "checked": sum(x["v4_inference_identity"]["checked"] for x in v4.values()),
               "identical": sum(x["v4_inference_identity"]["identical"] for x in v4.values()),
               "items_decoded": sum(x["all_items_options_decoded_and_targets_checked"] for x in v4.values())},
        "V5": {**{b: rj(VALID / ("V5_%s_timing.json" % b))["throughput"]["train_items_per_s"] for b in ("english", "multilingual")},
               "smoke_log": rel(SMOKE_LOG), "smoke_ok": sum(bool(re.match(r"STEP \S+ OK", x)) for x in sm), "smoke_failed": sum("FAILED" in x for x in sm)},
        "V6": {"tasks": len(v6), "exact": rows("exact"), "normalized": rows("normalized"),
               "removed_before_sampling": {t: x["removed_before_sampling"]["exact"] + x["removed_before_sampling"]["normalized_only"]
                                           for t, x in v6.items() if x["removed_before_sampling"]["exact"] + x["removed_before_sampling"]["normalized_only"]}},
    }


def t1_rerun(root, out, rep=None):
    """The same-setting T1 retraining spread (PREP_20261008.md, last section): the prep's V2(b) run and the main run's T1 side by
    side, paired on the 2,000 test decisions, and their micro-batch training losses (micro_batch_trace field 5, ce) compared.
    Given the repeat run's root, its T1 (torch seed 14) joins as a third run, paired with each of the other two."""
    names = ("dev_ep1.json", "dev_final.json", "ext_T1_typed_decisions_test400.json", "train_timing.json")
    files = {"v2b": [VALID / f for f in ("V2_T1-ep1_dev.json", "V2_T1_dev.json", "V2_T1_T1_test400.json", "V2_T1_timing.json")],
             "s2": [root / "T1" / f for f in names], **({"s14": [rep / "T1" / f for f in names]} if rep else {})}
    runs, cor, ce = {}, {}, {}
    for k, (d1, d2, te, tm) in files.items():
        d, r = recs(te, sets("T1", "ext")[0], out), rj(tm)
        x = stats("T1", list(d.values()), gold("ext"))
        runs[k] = {"seed": r["seed"], "dev_ep1": LS.metrics(LS.decisions(d1)[1])["accuracy"], "dev_ep2": LS.metrics(LS.decisions(d2)[1])["accuracy"],
                   **{m: x[m] for m in ("acc_vs_label", "acc", "soft_acc", "brier_vs_soft", "score_mae", "ece")},
                   "calib_acc": r["calibration_rows"]["accuracy"], "train_ce_last": r["train_ce_windows"][-1], "files": [rel(f) for f in (d1, d2, te, tm)]}
        cor[k] = {i: y["pred"] == y["gold"] for i, y in d.items()}
        ce[k] = [m[4] for m in r["micro_batch_trace"]]
    a, b = ce["v2b"], ce["s2"]
    i = next((j for j in range(len(a)) if a[j] != b[j]), None)
    return {"status": "ok", "runs": runs, "test": test("T1", cor["v2b"], cor["s2"]),
            "trace": {"micro_batches": len(a), "first_diff": i, "first_diff_ce": None if i is None else [a[i], b[i]],
                      "segments": [{"range": [lo, hi], "mean_abs_diff": float(np.mean([abs(a[j] - b[j]) for j in range(lo, hi + 1)]))}
                                   for lo, hi in TRACE_SEGMENTS]},
            **({"test_s14": {k: test("T1", cor[k], cor["s14"]) for k in ("v2b", "s2")}} if rep else {})}


def verdict(x, p, a, b):
    """F's rule on a McNemar of arm a vs arm b (b = only a right, c = only b right) at p."""
    return ("%s 유의 우세" % a) if p < ALPHA and x["b"] > x["c"] else ("%s 유의 우세" % b) if p < ALPHA and x["c"] > x["b"] else "비유의"


def holm_judge(T):
    """Holm within each family over the tasks it has, then the verdict on the raw and on the Holm p."""
    for f, ab in list(FAMS.items()) + [("ext", ("trained", "vanilla"))]:
        xs = {t: T[t]["ext"].get("test") if f == "ext" else T[t]["items"]["tests"].get(f) for t in T}
        xs = {t: x for t, x in xs.items() if x}
        for t, hp in S6.holm({t: x["p"] for t, x in xs.items()}).items():
            xs[t].update(holm_p=hp, verdict=verdict(xs[t], xs[t]["p"], *ab), verdict_holm=verdict(xs[t], hp, *ab))


def family_change(T):
    """The families with Jev were T1-T8 before session S7: their size then and now, and the T1-T8 cells whose Holm verdict changed."""
    out = {}
    for f in ("trained_vs_jev", "jev_vs_vanilla"):
        xs = {t: T[t]["items"]["tests"][f] for t in TASKS if f in T[t]["items"]["tests"]}
        h8 = S6.holm({t: x["p"] for t, x in xs.items() if t in S6.TASKS})
        out[f] = {"before": len(h8), "after": len(xs), "changed": [t for t, hp in h8.items() if verdict(xs[t], hp, *FAMS[f]) != xs[t]["verdict_holm"]]}
    return out


def repeat(root, out, F, master, T, cor, smoke):
    """Run 2 of the trained arm (<root>/rep_s14/, torch seed 14, PREP_20261008.md "사용자 결정" 4) next to run 1: accuracies, the
    McNemar of the two runs on the ext items, run 2's own Holm verdicts and whether they agree with run 1's (a verdict stands
    only when both runs reach it)."""
    if smoke:
        return {"status": NA}, {}
    d = root / REP
    log = d / "run_all_status.log"
    status = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    done = [t for t in TASKS if "STEP %s:cleanup OK" % t in status and T[t]["done"]]
    T2, cor2 = {}, {}
    for t in done:
        T2[t], cor2[t] = task(t, d, out, F, master, True, smoke)
    holm_judge(T2)
    R = {t: {"done": False} for t in TASKS}
    for t in done:
        x, y = T[t], T2[t]
        pairs = {f: (x["ext"]["test"], y["ext"]["test"]) if f == "ext" else (x["items"]["tests"][f], y["items"]["tests"][f]) for f, _ in AGREE}
        R[t] = {"done": True, "seed": [rj(r / t / "train_timing.json")["seed"] for r in (root, d)],
                "items": {"trained": y["items"]["trained"], "tests": {f: y["items"]["tests"][f] for f in ("trained_vs_jev", "trained_vs_vanilla")}},
                "ext": {"trained": y["ext"]["trained"], "test": y["ext"]["test"]}, "diag": y["diag"],
                "mean": {k: (x[k]["trained"]["acc"] + y[k]["trained"]["acc"]) / 2 for k in ("items", "ext")},
                "runs_test": test(t, cor[t]["trained_ext"], cor2[t]["trained_ext"]),
                "agree": {f: "확정" if a["verdict_holm"] == b["verdict_holm"] else "불일치" for f, (a, b) in pairs.items()}}
    n = Counter(v for x in R.values() if x["done"] for v in x["agree"].values())
    return {"status": "ok", "root": rel(d), "status_log": rel(log), "status_last": status[-1] if status else None, "seeds": list(SEEDS),
            "done": done, "missing": [t for t in TASKS if t not in done], "tasks": R,
            "agree": {"confirmed": n["확정"], "disagree": n["불일치"], "missing": len(AGREE) * (len(TASKS) - len(done)), "comparisons": len(AGREE) * len(TASKS),
                      "tasks": len(TASKS), "per_task": len(AGREE)},
            "ext_diff": cat_boot({t: R[t]["ext"]["trained"]["acc"] - T[t]["ext"]["vanilla"]["acc"] for t in done})}, cor2


def collect(root, out):
    status = (root / "run_all_status.log").read_text(encoding="utf-8").splitlines()
    done = [t for t in TASKS if "STEP %s:cleanup OK" % t in status]
    smoke = "SMOKE=1" in status[0]
    F, master = rj(S6.OUT_JSON), S6.master_records()
    F["tasks"].update({t: s7_task(t, master)[0] for t in TASKS if t not in F["tasks"]})  # F's summary.json stops at T8
    T, cor = {}, {}
    for t in TASKS:
        T[t], cor[t] = task(t, root, out, F, master, t in done, smoke)
    holm_judge(T)
    T["T10"]["items"]["label_check"] = label_check(cor["T10"], out)
    rp, cor2 = repeat(root, out, F, master, T, cor, smoke)
    s7 = [k + 1 for k, r in enumerate(master) if r["session"] == S7]
    meta = {"generated_by": "results/T3arm/t3arm_summary.py build", "built_kst": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "root": rel(root), "status_log": rel(root / "run_all_status.log"), "status_last": status[-1], "smoke": smoke,
            "done": done, "missing": [t for t in TASKS if t not in done], "categories": CATS,
            "s7": {"session_dir": rel(J.session_dir(S7)), "master_lines": [s7[0], s7[-1]], "records": len(s7)},
            "family_change": family_change(T), "calib_dir": rel(CALIB),
            "methods": {"ci": 0.95, "alpha": ALPHA, "seed": S6.SEED, "task_boot": S6.N_TASK_BOOT, "cluster_boot": S6.N_CLUSTER_BOOT,
                        "ece_bins": 15, "budgets": list(BUDGETS), "langs": len(S6.LANGS), "jev_rounding_err": F["meta"]["methods"]["jev_rounding_err"]},
            "temperature_source": {"english": "upstream fit (형식별, 옵션 수 구간별)", "multilingual": "기본값 1.0 (형식 전부)"}}
    val = validity(T)
    val["T1_rerun"] = (t1_rerun(root, out, root / REP if "T1" in rp.get("done", []) else None) if not smoke and "T1" in done
                       else {"status": NA if smoke else NONE})
    return {"meta": meta, "tasks": T, "aggregate": aggregate(T), "validity": val, "repeat": rp}, cor, cor2, F


# ---------------------------------------------------------------- figures (s6_summary style: _plt, _frame, _grouped, _legend, _save)
def figures(o, out):
    plt = S6._plt()
    figs = out / "figs"
    figs.mkdir(parents=True, exist_ok=True)
    shutil.copy(S6.FIGS / "palette_check.txt", figs / "palette_check.txt")  # validator output for the same slot 1-3 hex values
    S6.FIGS = figs  # s6_summary._save and palette_check read this module global
    T, A, INK, pv = o["tasks"], o["aggregate"], S6.INK, S6._pv
    smoke = " SMOKE check: trained results come from truncated evaluation copies." if o["meta"]["smoke"] else ""
    cat_en = {"incl": "in-mix", "excl": "held-out"}
    rec = {"palette": S6.palette_check()}

    def stack(fig, parts, xlabel):
        """Grouped-bar panels (groups, series, values, cis, ylabels, notes) stacked top to bottom, height by group count."""
        parts = [p for p in parts if p[0]]
        n, gap, y = sum(len(p[0]) for p in parts), 0.05, 0.8
        for k, (groups, series, vals, cis, labels, notes) in enumerate(parts):
            h = (0.715 - gap * (len(parts) - 1)) * len(groups) / n
            y -= h
            ax = fig.add_axes([0.205, y, 0.57, h])
            y -= gap
            ax.set_xlim(0, 1.0)
            ax.set_ylim(len(groups) - 0.5, -0.5)
            S6._frame(ax, [0, 0.2, 0.4, 0.6, 0.8, 1.0], xlabel if k == len(parts) - 1 else "")
            px = h * fig.get_figheight() * fig.dpi / len(groups)  # pixels per group: bars stay <= 22 px with a 2 px gap
            bar = min(0.22, 22 / px)
            S6._grouped(ax, groups, series, vals, cis, slot=bar + 2 / px, bar=bar)
            ax.set_yticks(range(len(groups)))
            ax.set_yticklabels(labels, fontsize=11, linespacing=1.35)
            for gi, note in enumerate(notes):
                ax.text(1.03, gi, note, transform=ax.get_yaxis_transform(), fontsize=10, color=INK["secondary"], va="center", linespacing=1.5)

    # 1. Jev items: accuracy per task and arm
    have = [t for t in TASKS if T[t]["items"]["trained"]]
    vals = {t: {a: T[t]["items"][a]["acc"] for a in ARMS if T[t]["items"][a]} for t in have}
    cis = {t: {a: T[t]["items"][a]["wilson"] for a in ARMS if T[t]["items"][a]} for t in have}
    nlab = lambda t: "%s %s\nn=%d" % (t, T[t]["name"], T[t]["items"]["n"]) + (" (%d case)" % T[t]["items"]["clusters"] if t == "T1" else "")  # noqa: E731
    note = lambda t: "\n".join("vs %s  b/c %d/%d, %s, Holm %s" % (lab, x["b"], x["c"], pv(x["p"]), pv(x["holm_p"])[2:])  # noqa: E731
                               for f, lab in (("trained_vs_jev", "Jev"), ("trained_vs_vanilla", "vanilla")) for x in [T[t]["items"]["tests"].get(f)] if x)
    fig = plt.figure(figsize=(16, 9), dpi=100)
    stack(fig, [(have, ARMS, vals, cis, [nlab(t) for t in have], [note(t) for t in have])], "Accuracy (bars), Wilson 95% CI (thin lines)")
    S6._titles(fig, "Accuracy by task: Jev vs vanilla Laya vs trained Laya (Jev items)",
               "Same state bytes, same question, same options. T7 pools the 5 languages of the same ids. Jev on T9·T10 comes from session S7.\n"
               "Wilson intervals for T1·T7 ignore the case/id clusters and are too narrow (summary.md §1.4). Right: exact McNemar of trained (run 1). No results: %s.%s"
               % (", ".join(o["meta"]["missing"]) or "none", smoke))
    S6._legend(fig, ARMS)
    S6._save(fig, "accuracy_3arm")
    plt.close(fig)
    rec["accuracy_3arm"] = {"groups": have, "values": vals, "wilson": cis}

    # 2. ext: trained - vanilla per task, paired bootstrap CI; run 2 (seed 14) as a hollow point where it has the task
    rows = [t for t in TASKS if "test" in T[t]["ext"]]
    B = {t: T[t]["ext"]["test"]["boot"] for t in rows}
    R2 = {t: x["ext"]["test"] for t, x in o["repeat"].get("tasks", {}).items() if x["done"] and t in rows}
    lim = max([0.1] + [abs(v) for b in B.values() for v in b["ci"]] + [abs(x["boot"]["diff"]) for x in R2.values()]) * 1.15
    step = 0.1 if lim <= 0.5 else 0.2
    ticks = [k * step for k in range(-int(lim / step), int(lim / step) + 1)]
    fig = plt.figure(figsize=(16, 9), dpi=100)
    ax = fig.add_axes([0.205, 0.085, 0.5, 0.715])
    ax.set_xlim(-lim, lim)
    ax.set_ylim(max(len(rows), 1) - 0.5, -0.5)
    S6._frame(ax, ticks, "trained - vanilla accuracy difference (dots), paired bootstrap 95% CI (thin lines)")
    ax.set_xticklabels(["%+.1f" % v if abs(v) > 1e-9 else "0" for v in ticks])
    ax.axvline(0, color=INK["axis"], linewidth=1, zorder=2)
    for i, t in enumerate(rows):
        x = T[t]["ext"]["test"]
        ax.plot(B[t]["ci"], [i, i], color=INK["secondary"], linewidth=1.3, zorder=3, solid_capstyle="butt")
        ax.scatter([B[t]["diff"]], [i], s=110, color=S6.PAL["trained"], edgecolor=INK["surface"], linewidth=2, zorder=4)
        if t in R2:
            ax.scatter([R2[t]["boot"]["diff"]], [i + 0.3], s=70, color=INK["surface"], edgecolor=S6.PAL["trained"], linewidth=2, zorder=4)
        ax.text(1.03, i, "%+.3f [%+.3f, %+.3f]%s\nb/c %d/%d (n=%d), %s, Holm %s" % (B[t]["diff"], *B[t]["ci"], "   (run 2 %+.3f)" % R2[t]["boot"]["diff"] if t in R2 else "",
                                                                                  x["b"], x["c"], x["n"], pv(x["p"]), pv(x["holm_p"])[2:]),
                transform=ax.get_yaxis_transform(), fontsize=10, color=INK["secondary"], va="center", linespacing=1.5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(["%s %s (%s)\nn=%s" % (t, T[t]["name"], cat_en[T[t]["category"]], "{:,}".format(T[t]["ext"]["n"])) for t in rows],
                       fontsize=11, linespacing=1.35)
    S6._titles(fig, "ext sets: trained - vanilla accuracy difference",
               "Paired differences on the same ext items. Bootstrap 10,000 resamples, seed 13; T1 resampled by case, T7 by id cluster, the rest by item.\n"
               "b = only trained correct, c = only vanilla correct (the driver's paired_<stem>.json). Hollow dot = replicate run 2 (tasks with results only). No results: %s.%s"
               % (", ".join(o["meta"]["missing"]) or "none", smoke))
    if R2:
        from matplotlib.lines import Line2D
        fig.legend(handles=[Line2D([], [], linestyle="none", marker="o", markersize=10, markerfacecolor=fc, markeredgecolor=S6.PAL["trained"],
                                   markeredgewidth=2, label="trained run %d (seed %d)" % (k + 1, s))
                            for k, (fc, s) in enumerate(zip((S6.PAL["trained"], INK["surface"]), SEEDS))],
                   loc="upper left", bbox_to_anchor=(0.02, 0.845), ncol=2, frameon=False, fontsize=11.5, labelcolor=INK["secondary"], columnspacing=1.6)
    S6._save(fig, "ext_trained_minus_vanilla")
    plt.close(fig)
    rec["ext_diff"] = {"rows": rows, "diff": {t: B[t]["diff"] for t in rows}, "ci": {t: B[t]["ci"] for t in rows},
                       "run2": {t: x["boot"]["diff"] for t, x in R2.items()}}

    # 3. dev accuracy per epoch, small multiples (epoch 0 = vanilla)
    fig = plt.figure(figsize=(16, 9), dpi=100)
    for k, t in enumerate(TASKS):
        ax = fig.add_axes([0.045 + (k % 5) * 0.192, 0.445 - (k // 5) * 0.37, 0.15, 0.26])
        ax.set_xlim(-0.35, 2.35)
        ax.set_ylim(0, 1.15)
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(["0 vanilla", "1", "2"], fontsize=10)
        ax.set_yticks([0, 0.5, 1.0])
        ax.grid(axis="y", color=INK["grid"], linewidth=1, zorder=0)
        ax.tick_params(length=0, labelsize=10)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(INK["axis"])
        d = T[t].get("diag")
        ax.set_title("%s %s (%s)%s" % (t, T[t]["name"], cat_en[T[t]["category"]], ", training failure" if d and d["failed"] else ""), fontsize=11,
                     loc="left", color=INK["primary"])
        if not d:
            ax.text(1, 0.5, "no results", ha="center", va="center", fontsize=11, color=INK["muted"])
            continue
        e = list(range(len(d["dev"])))
        ax.plot(e, d["dev"], color=S6.PAL["trained"], linewidth=2, zorder=3, solid_joinstyle="round", solid_capstyle="round")
        ax.scatter(e, d["dev"], s=70, color=[S6.PAL["vanilla"]] + [S6.PAL["trained"]] * (len(e) - 1), edgecolor=INK["surface"], linewidth=2, zorder=4)
        s = d["selected_epoch"]
        ax.scatter([s], [d["dev"][s]], s=300, facecolor="none", edgecolor=INK["primary"], linewidth=1.5, zorder=5)
        for i in (0, e[-1]):
            ax.text(i, d["dev"][i] + 0.07, "%.3f" % d["dev"][i], ha="center", fontsize=9.5, color=INK["secondary"])
    S6._titles(fig, "Dev accuracy by task: epoch 0 (vanilla) → 1 → 2",
               "dev is a held-out slice used only to select the epoch. Ringed dot = selected epoch (best dev; the earlier epoch on ties). The last dot is the final export (last epoch + fitted T)."
               + smoke)
    S6._legend(fig, ("vanilla", "trained"))
    S6._save(fig, "dev_curves")
    plt.close(fig)
    rec["dev_curves"] = {t: T[t]["diag"]["dev"] for t in TASKS if T[t].get("diag")}

    # 4. category macro per arm, Jev items and ext
    parts, rec["category_macro"] = [], {}
    for layer, arms, lab in (("items", ARMS, "Jev items"), ("ext", ("vanilla", "trained"), "ext")):
        mac = A[layer]["macro"]
        ser = tuple(a for a in arms if all(mac[a][c] for c in CATS))
        groups = ["%s:%s" % (layer, c) for c in CATS]
        vals = {g: {a: mac[a][c]["mean"] for a in ser} for g, c in zip(groups, CATS)}
        parts.append((groups if ser else [], ser, vals, {g: {a: mac[a][c]["ci"] for a in ser} for g, c in zip(groups, CATS)},
                      ["%s\n%s" % (lab, cat_en[c]) for c in CATS],
                      ["\n".join("%s: %s" % (ARM_KO[a], "·".join(mac[a][c]["tasks"])) for a in ser) for c in CATS]))
        rec["category_macro"][layer] = {a: {c: mac[a][c]["mean"] for c in CATS} for a in ser}
    fig = plt.figure(figsize=(16, 9), dpi=100)
    stack(fig, parts, "Task macro accuracy (bars), bootstrap 95% CI resampling tasks within the category (thin lines)")
    S6._titles(fig, "Macro accuracy by category (Laya training mix)",
               "Top: the three arms on Jev items; bottom: vanilla·trained on ext. Tasks are weighted equally; with few tasks per category the bootstrap intervals are coarse.\n"
               "Jev T9·T10 come from session S7. Right: the tasks in each average." + smoke)
    S6._legend(fig, tuple(a for a in ARMS if any(a in p[1] for p in parts)))
    S6._save(fig, "category_macro")
    plt.close(fig)
    return rec


# ---------------------------------------------------------------- markdown
def render_md(o):
    M, T, A, V, FG = o["meta"], o["tasks"], o["aggregate"], o["validity"], o["figures"]
    f3 = lambda x: "-" if x is None or x != x else "%.3f" % x  # noqa: E731  (NaN: a SMOKE subset without that question type)
    ci = lambda w: "[%.3f, %.3f]" % tuple(w)  # noqa: E731
    sg = lambda x: ("%+.3f" % x).replace("-", "−")  # noqa: E731
    sci = lambda w: "[%s, %s]" % (sg(w[0]), sg(w[1]))  # noqa: E731
    pv = lambda p: ("%.1e" % p) if p < 0.0001 else ("%.4f" % p)  # noqa: E731
    big = "{:,}".format
    acc = lambda s, n=None: NONE if s is None else "%d/%d = %.3f %s%s" % (s["correct"], s["n"], s["acc"], ci(s["wilson"]), " †" if n and s["n"] < n else "")  # noqa: E731
    tc = lambda x: "%d/%d, %s (%s)" % (x["b"], x["c"], pv(x["p"]), pv(x["holm_p"]))  # noqa: E731
    mn = lambda c, f=f3, g=ci: NONE if c is None else "%s %s" % (f(c["mean"]), g(c["ci"]))  # noqa: E731
    I = lambda t: T[t]["items"]  # noqa: E731, E741
    done, ms, mt = M["done"], M["methods"], M["temperature_source"]
    L = []
    w = L.append

    w("# 3-arm 비교 종합: Jev vs vanilla Laya vs trained Laya (S3, %s)\n" % M["built_kst"])
    if M["smoke"]:
        w("> **SMOKE 점검본이다.** 입력(`%s`)은 SMOKE 드라이버 실행 결과다(과제마다 소량 학습, 평가 세트는 앞 행만 자른 사본). trained 수치는 품질 신호가 아니다. "
          "trained 칸의 †는 잘린 결과(세트의 앞 행만)이고, Jev·vanilla는 전체 세트를 쓰며, 짝 비교는 양쪽에 있는 항목만 쓴다.\n" % M["root"])
    w("> Jev는 독립 제3자 플레이그라운드 경유 기록(`results/F/jev_cmp/`, 이 종합은 새 요청 없음)이다. T1-T8은 F 종합의 값이고, T9·T10은 세션 S7(`%s`)의 기록(공개 저장소에는 포함하지 않음)을 "
      "같은 함수로 계산했다. vanilla는 trained와 같은 base(영어 과제 english, "
      "T7 multilingual)를 학습 없이 쓴다. %s는 vanilla에 과제 calib로 맞춘 temperature만 넣은 보정 분리 열이다(§4). "
      "trained는 과제 라벨로 과제마다 따로 파인튜닝한 Laya라 zero-shot이 아니라 전문화 비교다(라벨 수와 학습 시간은 §5). §1-§6의 trained는 run 1(본 학습)이고 "
      "반복 학습 run 2는 §7이다. 이 문서의 수치는 `summary.json`과 같고 `t3arm_summary.py verify`가 대조한다.\n" % (M["s7"]["session_dir"], CALIB_KO))
    w("**상태.** `%s`의 마지막 줄은 `%s`다. 결과 있는 과제 %d개(%s), 결과 없음 %d개(%s). 결과 없는 과제는 표에 \"%s\"으로 두고 검정과 집계에서 뺐다.\n"
      % (M["status_log"], M["status_last"], len(done), ", ".join(done) or "-", len(M["missing"]), ", ".join(M["missing"]) or "-", NONE))
    rp = o["repeat"]
    if rp["status"] == "ok":
        w("**반복 학습(§7).** `%s`의 마지막 줄은 `%s`다. 결과 있는 과제 %d개(%s), 결과 없음 %d개(%s).\n"
          % (rp["status_log"], rp["status_last"] or "-", len(rp["done"]), ", ".join(rp["done"]) or "-", len(rp["missing"]), ", ".join(rp["missing"]) or "-"))

    w("## 1. Jev 항목 3-arm 비교 (Q2)\n")
    w("### 1.1 종합 표\n")
    w("| 과제 | 범주 | n | Jev | vanilla | trained | trained vs Jev: b/c, p (Holm p) | trained vs vanilla: b/c, p (Holm p) | Jev vs vanilla: b/c, p (Holm p) "
      "| 판정 (Holm 후): trained vs Jev / trained vs vanilla / Jev vs vanilla |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for t in TASKS:
        x, ts = I(t), I(t)["tests"]
        nl = "%d (%d case)" % (x["n"], x["clusters"]) if t == "T1" else "%d (%d id x %d 언어)" % (x["n"], x["clusters"], ms["langs"]) if t == "T7" else str(x["n"])
        cell = lambda f: tc(ts[f]) if f in ts else NONE  # noqa: E731
        w("| %s %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            t, T[t]["name"], CAT_KO[T[t]["category"]], nl, acc(x["jev"]), acc(x["vanilla"]), acc(x["trained"], x["n"]),
            cell("trained_vs_jev"), cell("trained_vs_vanilla"), cell("jev_vs_vanilla"),
            " / ".join("%s (%s)" % (ts[f]["verdict"], ts[f]["verdict_holm"]) if f in ts else "-" for f in FAMS)))
    nf = [sum(f in I(t)["tests"] for t in TASKS) for f in FAMS]
    fc = M["family_change"]
    ch = ", ".join("%s %s" % (t, f.replace("_vs_", " vs ").replace("jev", "Jev")) for f, x in fc.items() for t in x["changed"])
    w("")
    w("- 기존 %d과제 family와의 차이: T9·T10의 Jev(S7)가 들어와 Holm을 trained vs Jev %d → %d과제, Jev vs vanilla %d → %d과제로 다시 했다. "
      "T1-T8에서 Holm 후 판정이 바뀐 칸은 %s." % (fc["jev_vs_vanilla"]["before"], fc["trained_vs_jev"]["before"], fc["trained_vs_jev"]["after"],
                                          fc["jev_vs_vanilla"]["before"], fc["jev_vs_vanilla"]["after"], S6.jo(ch, ("이다", "다")) if ch else "없다"))
    w("- 정확도 칸은 정답/n = 정확도 [Wilson 95%%]다. b = 앞 arm만 정답, c = 뒤 arm만 정답이고 p는 exact McNemar(양측)다. Holm은 family마다 따로 적용했다"
      "(trained vs Jev %d과제, trained vs vanilla %d과제, Jev vs vanilla %d과제)." % tuple(nf))
    w("- 판정 규칙은 F와 같다. p < %g이고 b > c면 앞 arm 유의 우세, c > b면 뒤 arm 유의 우세, 아니면 비유의. 괄호는 Holm 보정 p에 같은 규칙을 적용한 결과다." % ms["alpha"])
    w("- 판정 열의 trained vs Jev와 trained vs vanilla는 run 1(본 학습)의 판정이다. 판정은 두 run의 결론이 같을 때만 확정한다(프로젝트 책임자 결정). 두 열의 확정 여부는 "
      "§7.2에 있다. Jev vs vanilla는 학습과 무관해 두 run에 같다.")
    w("- Jev vs vanilla는 T1-T8에서 F의 McNemar를 그대로 쓴다(`results/F/jev_cmp/summary.json`의 base 러너: T7 multilingual, 나머지 english). T9·T10은 S7 master "
      "기록(공개 저장소에는 포함하지 않음)에서 같은 함수(`s6_summary.systems_boolean`·`systems_choice`·`mcn`)로 계산한 base 러너(english) 검정이다. F의 판정은 과제별 최고 Laya 러너 "
      "기준이라 T4(F의 최고는 multilingual)에서 이 표와 다르고, Holm은 이 표의 base 러너 검정끼리 다시 했다.")
    w("- T1은 Jev와 비교 가능한 decision만 쓴다(Laya arm의 전체 %d decision은 §1.2). T1(case)과 T7(id)은 decision이 군집으로 묶여 Wilson 구간과 item 단위 "
      "McNemar가 낙관적이다. 군집 bootstrap은 §1.4에 있다." % I("T1")["all"]["vanilla"]["n"])
    if M["smoke"]:
        w("- † 잘린 결과: trained 리포트가 세트의 앞 행만 담아 n이 작다. 짝 비교의 n은 양쪽에 있는 항목 수다.")
    w("- 학습 믹스 포함 과제는 vanilla가 이미 그 데이터를 봤으므로 trained − vanilla가 작게 나올 수 있다(retention 상한, §3).\n")

    x = I("T1")
    w("### 1.2 T1 typed-decisions: Jev 비교 %d decision과 전체 %d decision\n" % (x["n"], x["all"]["vanilla"]["n"]))
    w("| arm | Jev 비교 %d decision | soft acc | Brier vs soft | score MAE | 전체 %d decision (Laya arm) | soft acc | Brier vs soft | score MAE |"
      % (x["n"], x["all"]["vanilla"]["n"]))
    w("|---|---|---|---|---|---|---|---|---|")
    aux = lambda s: " | ".join(f3(s[k]) if s else "-" for k in ("soft_acc", "brier_vs_soft", "score_mae"))  # noqa: E731
    for a in ARMS:
        s2 = x["all"].get(a)
        w("| %s | %s | %s | %s | %s |" % (ARM_KO[a], acc(x[a], x["n"]), aux(x[a]), acc(s2, x["all"]["vanilla"]["n"]) if a != "jev" else "-", aux(s2)))
    w("")
    w("- soft acc·Brier vs soft·score MAE는 teacher 분포 기준이다(upstream Part B, `laya_summary.py t1_extra`). Jev 줄은 F의 값이다.")
    if "all_test" in x:
        y = x["all_test"]
        w("- trained vs vanilla, 전체 %d decision: b/c %d/%d, p=%s, 정확도 차이 %s (드라이버 `paired_T1_typed_decisions_40.json`)."
          % (y["n"], y["b"], y["c"], pv(y["p"]), sg(y["delta"])))
    w("")

    pl = I("T7")["per_lang"]
    w("### 1.3 T7 MASSIVE intent-10: 언어별 (같은 %d id)\n" % I("T7")["clusters"])
    w("| arm | %s | 합산 |" % " | ".join(S6.LANGS))
    w("|---|%s---|" % ("---|" * len(S6.LANGS)))
    for a in ARMS:
        w("| %s | %s | %s |" % (ARM_KO[a], " | ".join("%d/%d = %s" % (pl[L][a]["correct"], pl[L][a]["n"], f3(pl[L][a]["acc"])) if a in pl[L] else NONE
                                                      for L in S6.LANGS), acc(I("T7")[a], I("T7")["n"])))
    w("")
    w("- 옵션은 10개 영어 key이고 발화만 언어별로 다르다. 언어당 n이 작아 언어별 차이는 방향 신호다.\n")

    w("### 1.4 군집 bootstrap: T1 (case), T7 (id)\n")
    w("| 과제 | 비교 | 정확도 차이 | 군집 bootstrap 95% | 군집 / decision | 참고: item 단위 McNemar b/c, p |")
    w("|---|---|---|---|---|---|")
    for t in ("T1", "T7"):
        for f, (a, b) in FAMS.items():
            y = I(t)["tests"].get(f)
            if y is None:
                w("| %s | %s − %s | %s | - | - | - |" % (t, a, b, NONE))
                continue
            k = y["boot"]
            w("| %s | %s − %s | %s | %s | %d / %d | %d/%d, %s |" % (t, a, b, sg(k["diff"]), sci(k["ci"]), k["clusters"], k["items"], y["b"], y["c"], pv(y["p"])))
    w("")
    w("- 군집을 복원 재표본(%s회, seed %d)해 뽑힌 군집의 decision 전체로 정확도 차이를 다시 계산했다(`s6_summary.cluster_boot`). Jev − vanilla는 F의 값이다.\n"
      % (big(ms["cluster_boot"]), ms["seed"]))

    w("### 1.5 보조 지표 (docs/09와 같은 정의)\n")
    w("| 과제 | 지표 | Jev | vanilla | trained |")
    w("|---|---|---|---|---|")
    for t in TASKS:
        k = {"boolean": "auroc", "score": "mae"}.get(T[t]["kind"])
        if k:
            w("| %s %s | %s | %s | %s | %s |" % (t, T[t]["name"], "AUROC p(true)" if k == "auroc" else "MAE of E[level]",
                                               f3(I(t)["jev"][k]), f3(I(t)["vanilla"][k]), f3(I(t)["trained"][k]) if I(t)["trained"] else NONE))
    w("")
    w("- T1의 soft acc·Brier vs soft·score MAE는 §1.2에 있다. AUROC는 p(true)의 순위(동점은 절반)이고 MAE는 기대 레벨과 gold 레벨의 절대 차이다. Jev 값은 F의 값이고 "
      "T9는 S7 기록에서 같은 함수로 계산했다(소수 둘째 자리 반올림 확률, MAE는 Jev의 score 필드).\n")

    lc = I("T10")["label_check"]
    sk = {"jev": "Jev", "english": "vanilla english", "multilingual": "vanilla multilingual (참고)", "trained": "trained"}
    kn = lambda c: NONE if not c["n"] else "%d/%d" % (c["correct"], c["n"])  # noqa: E731
    w("### 1.6 T10 support tickets: 라벨 점검 (Jev 항목 %d행)\n" % lc["all_wrong_without_trained"]["n"])
    w("| 큐 (gold) | %s |" % " | ".join(sk[k] for k in lc["systems"]))
    w("|---|%s" % ("---|" * len(lc["systems"])))
    for q, x in list(lc["queues"].items()) + [("합계", lc["total"])]:
        w("| %s | %s |" % (q, " | ".join(kn(x[k]) for k in lc["systems"])))
    w("")
    a, b = lc["all_wrong"], lc["all_wrong_without_trained"]
    w("- 네 시스템(Jev, vanilla english, vanilla multilingual, trained)이 모두 틀린 행은 %s. trained를 빼면 %s S7 analyze(`raw/analyze/T10.md`, 공개 저장소에는 포함하지 않음)의 "
      "per item 표와 같은 행이다." % (S6.jo(NONE if not a["n"] else "%d/%d" % (a["wrong"], a["n"]), ("이다", "다")),
                                  S6.jo("%d/%d" % (b["wrong"], b["n"]), ("으로", "로"))))
    w("- 라벨 품질 의심, 수작업 확인 필요(`S7_summary.md` 근거). 그 문서 §3.6은 오답 다수에서 gold 큐가 질문에 준 큐 설명과 맞지 않는다고 읽었다(해석). "
      "큐당 행이 적어 큐별 수치는 방향 신호다. multilingual은 3-arm 밖의 참고 러너다(T10 base는 english).\n")

    w("## 2. ext 세트: vanilla vs trained\n")
    w("### 2.1 과제별 표\n")
    w("| 과제 | 범주 | n | vanilla | trained | trained − vanilla [bootstrap 95%] | b/c, p (Holm p) | 판정 (Holm 후) |")
    w("|---|---|---|---|---|---|---|---|")
    for t in TASKS:
        e = T[t]["ext"]
        y = e.get("test")
        w("| %s %s | %s | %s | %s | %s | %s | %s | %s |" % (
            t, T[t]["name"], CAT_KO[T[t]["category"]], big(e["n"]), acc(e["vanilla"]), acc(e["trained"], e["n"]),
            "%s %s" % (sg(y["boot"]["diff"]), sci(y["boot"]["ci"])) if y else NONE, tc(y) if y else NONE,
            "%s (%s)" % (y["verdict"], y["verdict_holm"]) if y else "-"))
    w("")
    w("- 차이와 구간은 같은 항목의 paired bootstrap(%s회, seed %d)이다. T1은 case, T7은 id를 군집으로 재표본하고 나머지는 항목을 재표본한다(`s6_summary.cluster_boot`)."
      % (big(ms["cluster_boot"]), ms["seed"]))
    w("- b = trained만 정답, c = vanilla만 정답이다. b/c와 p는 드라이버의 `paired_<stem>.json` 값이고 T7은 언어 파일 %d개의 합이다. Holm은 %d과제에 적용했다."
      % (ms["langs"], sum("test" in T[t]["ext"] for t in TASKS)))
    w("- trained와 판정은 run 1(본 학습)이다. 두 run의 결론이 같을 때만 판정을 확정한다(§7.2).")
    w("- ext는 vanilla vs trained의 좁은 CI용이다(Jev 없음). 표본은 대부분 라벨 층화라 upstream 공개치와 분포가 다르다(`PREP_20261008.md` §5).\n")

    v2, e1 = V["V2"], T["T1"]["ext"]
    w("### 2.2 T1 typed-decisions test %s decision (V2와 같은 지표)\n" % big(e1["n"]))
    w("| 모델 | accuracy (dataset label, upstream 정의) | accuracy (argmax gold) | soft acc | Brier vs soft | ECE | score MAE | choice / noul / score |")
    w("|---|---|---|---|---|---|---|---|")
    for lab, s in (("upstream `laya-typed-decisions` (V2 a)", v2["upstream"]), ("준비 V2(b): 우리 파이프라인의 T1 학습", v2["ours"]),
                   ("vanilla english", e1["vanilla"]), ("trained (본 학습 T1)", e1["trained"])):
        cells = [NONE] + ["-"] * 6 if s is None else [f3(s[k]) for k in ("acc_vs_label", "acc", "soft_acc", "brier_vs_soft", "ece", "score_mae")] + [
            " / ".join(f3(s["by_type"].get(k)) for k in ("choice", "noul", "score"))]
        w("| %s |" % " | ".join([lab] + cells))
    w("")
    w("- 공개치 %s(V2 a 기준 ±%g), V2 b 기준 ≥ %s와 majority %s(docs/11 §4). vanilla english 줄은 `V2_upstream_repro.json`의 english와 같아야 한다(verify가 대조)."
      % (f3(v2["published"]), v2["tolerance"], f3(v2["min"]), f3(v2["majority"])))
    w("- trained는 본 학습의 T1(english base, 과제 dev로 epoch 선택)이다. V2 b는 같은 설정의 준비 run이다.\n")

    ax_, ex_ = A["items"], A["ext"]
    w("## 3. 범주 집계 (Q1, Q2)\n")
    w("범주는 upstream이 밝힌 Laya 학습 믹스 기준이다(docs/11 §2). 포함은 %s, 제외는 %s. Jev가 들어간 집계의 포함 범주는 %s.\n"
      % ("·".join(M["categories"]["incl"]), S6.jo("·".join(M["categories"]["excl"]), ("이다", "다")), S6.jo("·".join(ax_["macro"]["jev"]["incl"]["tasks"]), ("이다", "다"))))
    w("### 3.1 arm별 범주 macro 정확도\n")
    w("| 기준 | arm | 포함 macro [95%] | 포함 과제 | 제외 macro [95%] | 제외 과제 |")
    w("|---|---|---|---|---|---|")
    for lab, G in (("Jev 항목", ax_), ("ext", ex_)):
        for a, c in G["macro"].items():
            w("| %s | %s | %s | %s | %s | %s |" % (lab, ARM_KO[a], mn(c["incl"]), "·".join(c["incl"]["tasks"]) if c["incl"] else "-",
                                                   mn(c["excl"]), "·".join(c["excl"]["tasks"]) if c["excl"] else "-"))
    w("")
    w("### 3.2 arm 간 차이와 difference-in-differences\n")
    w("| 기준 | 차이 | 포함 평균 [95%] | 제외 평균 [95%] | 제외 − 포함 [95%] |")
    w("|---|---|---|---|---|")
    for lab, G in (("Jev 항목", ax_), ("ext", ex_)):
        for k, c in G["diff"].items():
            a, b = k.split("-")
            w("| %s | %s − %s | %s | %s | %s |" % (lab, ARM_KO[a], ARM_KO[b], mn(c["incl"], sg, sci), mn(c["excl"], sg, sci),
                                                  NONE if c["contrast"] is None else "%s %s" % (sg(c["contrast"]["diff"]), sci(c["contrast"]["ci"]))))
    q1 = ax_["diff"]["jev-vanilla"]["contrast"]
    w("")
    w("- **Q1 difference-in-differences** = 제외 평균(Jev − vanilla) − 포함 평균(Jev − vanilla) = %s %s (Jev 항목). 양수면 vanilla의 열세가 학습 제외 과제에서 더 크다."
      % (sg(q1["diff"]), sci(q1["ci"])))
    w("- 과제별 정확도(T1은 Jev 비교 decision, T7은 언어 합산)를 같은 가중치로 평균했다. 구간은 범주 안에서 과제를 복원 재표본(%s회, seed %d)한 percentile이고 "
      "대비는 두 범주를 따로 재표본한 차이다. 범주당 과제가 적어(Jev 포함 범주는 %d개) 모집단 추론이 아니라 기술통계다."
      % (big(ms["task_boot"]), ms["seed"], len(ax_["macro"]["jev"]["incl"]["tasks"])))
    w("- 포함 과제의 trained − vanilla는 vanilla가 이미 그 데이터를 본 만큼 작을 수 있다(retention 상한).\n")

    w("## 4. 보정\n")
    AK = {**ARM_KO, "calib": CALIB_KO}
    ctemp = lambda c: ", ".join("%s %.3f%s" % (k, r, "" if r == p else " → %.3f" % p)  # noqa: E731
                                for k, r, p in zip(T_TYPES, c["temperature_raw"], c["temperature_applied"]))
    cal = [("4.1", "Jev 항목", "items", ("jev", "vanilla", "calib", "trained")), ("4.2", "ext", "ext", ("vanilla", "calib", "trained"))]
    for num, lab, layer, arms in cal:
        w("### %s %s\n" % (num, lab))
        w("| 과제 | arm | temperature 출처 | Brier | ECE | coverage@오류 %g%% | coverage@오류 %g%% |" % tuple(100 * b for b in ms["budgets"]))
        w("|---|---|---|---|---|---|---|")
        for t in TASKS:
            for a in arms:
                s = T[t][layer][a]
                src = ("-" if a == "jev" else mt[T[t]["base"]] if a == "vanilla" else "과제 calib fit (0-step export): " + ctemp(T[t]["calib"]) if a == "calib"
                       else "과제 calib fit" + (": %s" % ", ".join("%s %.3f" % kv for kv in zip(T_TYPES, T[t]["diag"]["temperature"])) if T[t]["done"] else ""))
                w("| %s | %s | %s | %s |" % (t, AK[a], src, NONE + " | -" * 3 if s is None else " | ".join(f3(s[k]) for k in ("brier", "ece", "cov05", "cov10"))))
        w("")
    w("- Brier는 옵션 전체의 Σ(p − onehot)² 평균, ECE는 %d bins top p 기준이다. coverage@오류 x%%는 top p가 높은 순으로 받아들일 때 오류율이 x%% 이하인 최대 coverage다"
      "(`scripts/metrics_extra.py coverage_table`, 같은 confidence는 나누지 않음). Jev 확률은 소수 둘째 자리 반올림이라 Brier·ECE에 약 ±%g의 하한 오차가 있다."
      % (ms["ece_bins"], ms["jev_rounding_err"]))
    v1 = V["V1"]
    w("- **주의.** trained의 보정 개선에는 temperature refit 효과가 섞인다(V1). trained의 temperature는 과제 calib로 다시 맞춘 값이고 vanilla english는 upstream이 맞춘 값, "
      "multilingual은 기본값이다. V1에서 학습 없이 refit만으로 ECE가 english %s → %s, multilingual %s → %s로 바뀌었다. 이 효과를 과제마다 떼어 낸 것이 %s 행과 §4.3이다. "
      "정확도 비교는 영향이 없다(temperature는 argmax를 바꾸지 않는다)."
      % (f3(v1["english"]["ece_base_t"]), f3(v1["english"]["ece_refit_t"]), f3(v1["multilingual"]["ece_base_t"]), f3(v1["multilingual"]["ece_refit_t"]), CALIB_KO))
    cl = [t for t in TASKS if T[t]["calib"]["temperature_raw"] != T[t]["calib"]["temperature_applied"]]
    w("- %s는 base 가중치를 그대로 두고 그 과제 calib로 temperature만 맞춘 0-step export다(`%s/<task>/`, V1과 같은 절차, 프로젝트 책임자 결정 3). temperature 출처의 "
      "a → b는 fit 값 a를 laya가 로드 때 b로 자른 clamp다(리포트 `config.checkpoint`의 `temperature_raw` → `temperature_applied`; 해당 과제 %s).\n"
      % (CALIB_KO, M["calib_dir"], ", ".join(cl) or "없음"))

    w("### 4.3 보정 분리: refit 효과와 학습 효과\n")
    w("| 과제 | Jev 항목 ECE: refit / 학습 | Jev 항목 Brier: refit / 학습 | ext ECE: refit / 학습 | ext Brier: refit / 학습 |")
    w("|---|---|---|---|---|")
    for t in TASKS:
        E = T[t]["calib"]["effect"]
        w("| %s %s | %s |" % (t, T[t]["name"], " | ".join("%s / %s" % (sg(E[k][m]["refit"]), NONE if E[k][m]["train"] is None else sg(E[k][m]["train"]))
                                                       for k in ("items", "ext") for m in ("ece", "brier"))))
    cs = A["calib_same"]
    w("")
    w("- refit 효과 = (%s) − vanilla, 학습 효과 = trained − (%s)다. 둘의 합이 trained − vanilla이고 음수면 그 지표가 낮아진(좋아진) 것이다. "
      "T1의 Jev 항목은 Jev와 비교 가능한 %d decision이다." % (CALIB_KO, CALIB_KO, I("T1")["n"]))
    w("- %s의 답은 vanilla와 같다. argmax 일치 %s/%s(반올림 동률을 같은 답으로 보면 %s/%s), 정답 여부 %s/%s 일치다(`same_<stem>.json`, Jev 항목과 ext 전체). "
      "그래서 정확도와 정확도 검정은 vanilla 칸 그대로이고 Brier·ECE·coverage만 다르다.%s\n"
      % (CALIB_KO, big(cs["argmax_agreement"]), big(cs["decisions"]), big(cs["argmax_agreement_ties_agree"]), big(cs["decisions"]),
         big(cs["correct_identical"]), big(cs["decisions"]),
         " 엄격 불일치 %d decision(%s)은 동률을 같은 답으로 보면 일치한다." % (cs["strict_mismatch"], ", ".join("`%s`" % s for s in cs["strict_diff"]))
         if cs["strict_mismatch"] else ""))

    w("## 5. 비용 (Q3)\n")
    w("| 과제 | base | 라벨 합계 | train items | calib | dev | epoch / optimizer step | item 출처 (학습은 item-pass 수) | train loop (분) | run_ft wall (분) | items/s "
      "| MPS allocated / driver peak (GB) | 체크포인트 (GB) |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for t in TASKS:
        c = T[t].get("cost")
        if c is None:
            w("| %s %s | %s | %s |%s" % (t, T[t]["name"], T[t]["base"], NONE, " - |" * 10))
            continue
        src = "; ".join("%s ← %s" % (k, ", ".join("%s %s" % (s, big(n)) for s, n in v.items())) for k, v in c["item_sources"].items())
        w("| %s %s | %s | %s | %s | %s | %s | %d / %d | %s | %.1f | %.1f | %.2f | %.1f / %.1f | %s |" % (
            t, T[t]["name"], T[t]["base"], big(c["labels"]), big(c["train_items"]), big(c["calib_items"]), big(c["dev_items"]), c["epochs"],
            c["optimizer_steps"], src, c["train_loop_min"], c["wall_min"], c["items_per_s"], c["mps_alloc_gb"], c["mps_driver_gb"],
            "-" if c["ckpt_gb"] is None else "%.2f" % c["ckpt_gb"]))
    w("")
    w("- 라벨 합계 = train + calib(temperature fit) + dev(epoch 선택)다. 시간과 메모리는 run_ft 리포트(`<task>/train_timing.json`, 학습은 MPS fp32), 체크포인트는 "
      "`poc/finetune/ckpt_t3arm/<task>/`(공개 저장소에는 포함하지 않음)의 파일 크기 합(십진 GB)이다. Jev와 vanilla는 라벨과 학습이 없다.")
    if M["smoke"]:
        w("- SMOKE는 체크포인트를 임시 디렉터리에 두고 지웠으므로 크기가 없다.")
    w("")

    w("## 6. 학습 검증 (Q4)\n")
    w("### 6.1 과제별 진단\n")
    w("| 과제 | dev epoch 0 (vanilla) | epoch 1 | epoch 2 | 선택 epoch | train − dev | fitted T (choice, score, noul) | clamp | flip dev40 [95%] "
      "| 클래스 recall 변화 (상승 / 하락 / 동일; 최저, 최고) | 학습 실패 |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for t in TASKS:
        d = T[t].get("diag")
        if d is None:
            w("| %s %s | %s |%s" % (t, T[t]["name"], NONE, " - |" * 9))
            continue
        cl = [x for k in ("outside_load_range", "at_script_bound") for x in d["clamp"][k]]
        r, f = d["recall"], d["flip"]
        w("| %s %s | %s | %s | %s | %d%s | %s | %s%s | %s | %s | %d / %d / %d; %s %s, %s %s | %s |" % (
            t, T[t]["name"], *[f3(d["dev"][k]) if k < len(d["dev"]) else "-" for k in range(3)], d["selected_epoch"], " (재보정)" if d["recalibrated"] else "",
            "-" if d["gap"] is None else sg(d["gap"]), ", ".join("%.3f" % v for v in d["temperature"]),
            "; 기본값 형식: %s" % ", ".join(d["t_default"]) if d["t_default"] else "", "범위 밖 " + ", ".join("%g" % v for v in cl) if cl else "없음",
            "- (choice 아님)" if f is None else "%s %s (n=%d)" % (f3(f["flip_rate_per_perm"]), ci(f["flip_rate_per_perm_ci"]), f["n_items"]),
            r["up"], r["down"], r["same"], r["min"][0], sg(r["min"][1]), r["max"][0], sg(r["max"][1]), "예" if d["failed"] else "아니오"))
    w("")
    w("- dev는 epoch 선택에만 쓰는 held-out 조각이다. 마지막 epoch 칸은 최종 export(마지막 epoch + fitted T)이고 temperature는 argmax를 바꾸지 않는다. 선택 규칙은 dev 최고, "
      "동률이면 앞 epoch이다(docs/11 §4). 앞 epoch을 고르면 같은 calib로 다시 맞춘다(재보정).")
    w("- train − dev = 마지막 창의 train 정확도(dropout을 켠 학습 forward) − 선택 epoch의 dev 정확도. fitted T는 선택 체크포인트의 값이고, 기본값 형식은 calib 표본이 없어 "
      "스크립트 기본값을 받은 형식이다. clamp는 fit 범위 경계값과 load 범위(laya가 로드 때 자르는 구간) 밖의 값이다.")
    w("- flip은 dev 앞 40행(choice 과제)의 옵션 순서를 바꾼 순열당 답 변경 비율이다. 학습 실패 = 모든 epoch의 dev가 epoch 0(vanilla)보다 낮음.")
    for t in TASKS:
        if T[t].get("diag") and T[t]["diag"]["failed"]:
            w("- %s의 학습 실패 표시: %s. 파이프라인 실패가 아니다(`PREP_20261008.md` \"본 학습 중 발견\" 절)." % (t, FAIL_CAUSES.get(t, "원인 미추적")))
    w("")

    w("### 6.2 학습 검증 V1-V6 요약\n")
    v3, v4, v5, v6 = V["V3"], V["V4"], V["V5"], V["V6"]
    yes = lambda b: "예" if b else "아니오"  # noqa: E731
    w("| ID | 검증 | 핵심 수치 | 기준 충족 | 파일 (`results/T3arm/validity/`) |")
    w("|---|---|---|---|---|")
    w("| V1 | zero-step identity | %s. refit만으로 ECE %s | %s | `V1_*_{export_diff,same,basetemp_same}.json` |" % (
        "; ".join("%s 텐서 값 %d/%d 동일, argmax %d/%d, base T 복원 답 %d/%d 동일" % (b, v1[b]["values_equal"], v1[b]["tensors"], v1[b]["argmax"], v1[b]["decisions"],
                                                                         v1[b]["basetemp_identical"], v1[b]["decisions"]) for b in ("english", "multilingual")),
        ", ".join("%s %s → %s" % (b, f3(v1[b]["ece_base_t"]), f3(v1[b]["ece_refit_t"])) for b in ("english", "multilingual")), yes(v1["met"])))
    w("| V2 | upstream 재현 | (a) upstream 체크포인트 %s (공개 %s, ±%g) (b) 우리 학습 %s (기준 ≥ %s, majority %s) | %s | `V2_upstream_repro.json` |" % (
        f3(v2["upstream"]["acc_vs_label"]), f3(v2["published"]), v2["tolerance"], f3(v2["ours"]["acc_vs_label"]), f3(v2["min"]), f3(v2["majority"]), yes(v2["met"])))
    w("| V3 | label-shuffle | permuted %s, 실제 라벨(준비 run) %s, vanilla %s, majority %s | %s (프로젝트 책임자 판정, §6.3) | `V3_label_shuffle.json` |" % (
        f3(v3["permuted"]), f3(v3["real_prep"]), f3(v3["vanilla_prep"]), f3(v3["majority"]), v3["user"]["verdict"]))
    w("| V4 | 형식 동일성 | %d과제, 추론 시퀀스와 토큰 일치 %d/%d, 옵션 decode·target 점검 %s items | %s | `V4_format_identity.json` |" % (
        v4["tasks"], v4["identical"], v4["checked"], big(v4["items_decoded"]), yes(v4["identical"] == v4["checked"])))
    w("| V5 | smoke | english %s items/s, multilingual %s items/s. 드라이버 SMOKE STEP OK %d, FAILED %d (`%s`) | %s | `V5_*` |" % (
        "%.2f" % v5["english"], "%.2f" % v5["multilingual"], v5["smoke_ok"], v5["smoke_failed"], v5["smoke_log"], yes(v5["smoke_failed"] == 0)))
    w("| V6 | 누수 | %d과제 train·dev·calib와 평가 텍스트의 교집합 정확 %d / 정규화 %d. 추출 전 제거 %s | %s | `V6_leakage.json` |" % (
        v6["tasks"], v6["exact"], v6["normalized"], ", ".join("%s %d" % kv for kv in v6["removed_before_sampling"].items()) or "없음",
        yes(v6["exact"] == v6["normalized"] == 0)))
    w("")
    w("- 기준은 docs/11 §4다. V1-V2·V4-V6의 기준 충족은 위 수치로 다시 계산했고 `PREP_20261008.md` §3의 판정과 같아야 한다. V3는 프로젝트 책임자 판정이다(§6.3).\n")

    w("### 6.3 V3 재판정 수치와 프로젝트 책임자 판정\n")
    na = lambda v, f=f3: NONE if v is None else f(v)  # noqa: E731
    w("| 기준 | 조건 | 값 | 기준값 | 값 − 기준값 |")
    w("|---|---|---|---|---|")
    w("| (a) 엄격 | permuted ≤ majority + %g | permuted %s | %s | %s |" % (v3["margin"], f3(v3["permuted"]), f3(v3["a_threshold"]), sg(v3["a_excess"])))
    w("| (b) 차이 | 실제 라벨 epoch 1 − permuted ≥ %.2f | %s | %.2f | %s |" % (
        v3["gap"], NONE if v3["b_diff"] is None else "%s − %s = %s" % (f3(v3["real_ep1_s2"]), f3(v3["permuted"]), sg(v3["b_diff"])), v3["gap"],
        na(v3["b_excess"], sg)))
    w("| (c) 대안 | permuted < vanilla zero-shot dev, 그리고 (b) | vanilla %s − permuted %s = %s; (b) 차이 %s | 0 초과, (b) | - |" % (
        f3(v3["vanilla_prep"]), f3(v3["permuted"]), sg(v3["c_vanilla_minus_permuted"]), na(v3["b_diff"], sg)))
    w("")
    w("- **프로젝트 책임자 판정 (%s, 본 학습 수치 기준): %s.** (b) 차이 기준과 (c) 대안 기준을 충족하고, (a) 엄격 기준의 %s 미달은 계획과의 편차로 기록한다(`%s`)."
      % (v3["user"]["date"], v3["user"]["verdict"], sg(v3["a_excess"]), v3["user"]["source"]))
    w("- 실제 라벨 epoch 1 = 본 학습 T3의 `dev_ep1.json` 정확도(%s; 2 epoch cosine의 중간 지점)다. 준비 단계의 대조 run(같은 items, cosine이 한 epoch에 끝남)은 %s."
      % (na(v3["real_ep1_s2"]), S6.jo(f3(v3["real_prep"]), ("이었다", "였다"))))
    w("- permuted, majority, vanilla는 `V3_label_shuffle.json`(T3 dev 전체, english)이다. 본 학습 T3의 dev epoch 0(vanilla)은 %s(같은 dev면 vanilla와 같아야 한다).\n"
      % S6.jo(na(v3["vanilla_s2"]), ("이다", "다")))

    x = V["T1_rerun"]
    rr = (("dev epoch 1", "dev_ep1"), ("dev epoch 2", "dev_ep2"), ("test accuracy (dataset label, upstream 정의)", "acc_vs_label"),
          ("test accuracy (argmax gold)", "acc"), ("test soft acc", "soft_acc"), ("test Brier vs soft", "brier_vs_soft"),
          ("test score MAE", "score_mae"), ("test ECE", "ece"), ("calibration 행 정확도", "calib_acc"), ("마지막 train CE 창", "train_ce_last"))
    w("### 6.4 같은 설정 T1 재학습 편차\n")
    if x["status"] != "ok":
        w("%s%s\n" % (x["status"], " (SMOKE 실행은 준비 V2(b)와 설정이 다르다)." if x["status"] == NA else " (본 학습 T1이 아직 끝나지 않았다)."))
    else:
        R, y, tr = x["runs"], x["test"], x["trace"]
        w("준비 V2(b)와 본 학습 T1은 스크립트, items, seed, 인자가 같다(`PREP_20261008.md` 마지막 절). 원인은 MPS 학습이 비트 단위로 결정적이지 않은 데 있다. "
          "두 run의 micro-batch 손실은 %d번에서 처음 갈라진다(%g 대 %g).\n" % (tr["first_diff"], *tr["first_diff_ce"]))
        w("| 지표 | V2(b) (준비) | 본 학습 T1 |")
        w("|---|---|---|")
        for lab, k in rr:
            w("| %s | %s | %s |" % (lab, f3(R["v2b"][k]), f3(R["s2"][k])))
        w("")
        w("| 짝 비교 (test %s decision) | b/c | exact McNemar p | 정확도 차이 V2(b) − 본 학습 (argmax gold) | case 군집 bootstrap 95%% | 군집 / decision |" % big(y["n"]))
        w("|---|---|---|---|---|---|")
        w("| V2(b) vs 본 학습 | %d/%d | %s | %s | %s | %d / %d |" % (y["b"], y["c"], pv(y["p"]), sg(y["boot"]["diff"]), sci(y["boot"]["ci"]),
                                                              y["boot"]["clusters"], y["boot"]["items"]))
        w("")
        w("| micro-batch 손실 (ce) | %s |" % " | ".join("%d-%d" % tuple(g["range"]) for g in tr["segments"]))
        w("|---|%s" % ("---|" * len(tr["segments"])))
        w("| 두 run의 평균 절대 차이 | %s |" % " | ".join("%.4f" % g["mean_abs_diff"] for g in tr["segments"]))
        w("")
        w("- b = V2(b)만 정답, c = 본 학습만 정답이다(같은 decision). 군집 bootstrap은 case를 복원 재표본(%s회, seed %d)했다(`s6_summary.cluster_boot`)."
          % (big(ms["cluster_boot"]), ms["seed"]))
        w("- 손실 구간은 micro-batch index다(두 epoch 합 %d개). 값은 각 run의 `train_timing.json` `micro_batch_trace` 다섯째 필드(ce)다." % tr["micro_batches"])
        w("- 같은 설정에서도 학습 run마다 결과가 달라진다. 그래서 §1-§6의 trained 수치는 run 하나(run 1)의 표본이다. seed를 바꾼 반복 학습과 판정 확정은 §7, "
          "T1 세 run 비교는 §7.4다.\n")

    w("## 7. 반복 학습과 판정 확정\n")
    if rp["status"] != "ok":
        w("%s (SMOKE root에는 반복 학습이 없다).\n" % rp["status"])
    else:
        R, (s1, s2) = rp["tasks"], rp["seeds"]
        w("run 1은 본 학습(torch seed %d, `%s/<task>/`), run 2는 같은 설정에서 seed만 %d로 바꾼 반복 학습(`%s/<task>/`)이다. 데이터 순서는 같고 seed는 dropout과 "
          "RLCD 노이즈를 바꾼다(`PREP_20261008.md` \"프로젝트 책임자 결정\" 4). 판정은 두 run의 결론이 같을 때만 확정한다. run 2의 결과 있는 과제 %d개(%s), 결과 없음 %d개(%s). "
          "vanilla·Jev·%s는 학습이 없어 두 run에 같다.\n"
          % (s1, M["root"], s2, rp["root"], len(rp["done"]), ", ".join(rp["done"]) or "-", len(rp["missing"]), ", ".join(rp["missing"]) or "-", CALIB_KO))
        w("### 7.1 과제별 정확도와 두 run의 짝 비교\n")
        w("| 과제 | 범주 | Jev 항목 정확도: run 1 / run 2 / 평균 | ext 정확도: run 1 / run 2 / 평균 | ext run 1 vs run 2: b/c, p | 선택 epoch: run 1 / run 2 |")
        w("|---|---|---|---|---|---|")
        for t in TASKS:
            r, x = R[t], T[t]
            if not r["done"]:
                w("| %s %s | %s | %s |" % (t, x["name"], CAT_KO[x["category"]], " | ".join([NONE] * 4)))
                continue
            y = r["runs_test"]
            w("| %s %s | %s | %s | %s | %s | %s |" % (
                t, x["name"], CAT_KO[x["category"]],
                *("%s / %s / %s" % (f3(x[k]["trained"]["acc"]), f3(r[k]["trained"]["acc"]), f3(r["mean"][k])) for k in ("items", "ext")),
                "%d/%d, %s%s" % (y["b"], y["c"], pv(y["p"]), "; 군집 bootstrap run 1 − run 2 %s %s" % (sg(y["boot"]["diff"]), sci(y["boot"]["ci"])) if "boot" in y else ""),
                "%d / %d" % (x["diag"]["selected_epoch"], r["diag"]["selected_epoch"])))
        w("")
        w("- 정확도는 trained의 정확도다(Jev 항목은 §1.1과 같은 decision, 평균은 두 run의 단순 평균). b = run 1만 정답, c = run 2만 정답(같은 ext 항목)이고 p는 exact McNemar다.")
        w("- T1·T7은 decision이 case·id 군집으로 묶여 item 단위 p가 낙관적이라 run 1 − run 2 정확도 차이의 군집 bootstrap(%s회, bootstrap seed %d)을 함께 둔다."
          % (big(ms["cluster_boot"]), ms["seed"]))
        w("- §6.4는 seed가 같은 두 run(준비 V2(b), 본 학습)이 MPS 비결정성만으로 갈라진 편차다. run 2는 seed까지 바꿨다.\n")

        w("### 7.2 판정 일치표\n")
        w("| 과제 | 비교 | run 1 판정 (Holm p) | run 2 판정 (Holm p) | 결론 |")
        w("|---|---|---|---|---|")
        vh = lambda y: "%s (%s)" % (y["verdict_holm"], pv(y["holm_p"])) if y else NONE  # noqa: E731
        get = lambda z, f: (z["items"]["tests"].get(f) if f != "ext" else z["ext"].get("test")) if z.get("items") else None  # noqa: E731
        bad = []
        for t in TASKS:
            r, x = R[t], T[t]
            for f, lab in AGREE:
                w("| %s %s | %s | %s | %s | %s |" % (t, x["name"], lab, vh(get(x, f)), vh(get(r, f)), r["agree"][f] if r["done"] else NONE))
                bad += ["%s %s" % (t, lab)] if r["done"] and r["agree"][f] != "확정" else []
        g = rp["agree"]
        w("")
        w("- 결론: 확정 %d, 불일치 %d, 결과 없음 %d (비교 %d개 = 과제 %d개 x 비교 %d종). 불일치: %s."
          % (g["confirmed"], g["disagree"], g["missing"], g["comparisons"], g["tasks"], g["per_task"], ", ".join(bad) or "없음"))
        w("- 확정 = 두 run의 Holm 후 판정이 같음. 판정 규칙과 Holm family(비교마다 따로)는 §1.1·§2.1과 같고, run 2의 Holm은 run 2에 결과 있는 과제끼리 "
          "따로 했다(지금 %d과제, 끝나면 %d과제)." % (len(rp["done"]), len(TASKS)))
        w("")

        w("### 7.3 범주 집계: ext trained − vanilla\n")
        w("| run | 포함 평균 [95%] | 포함 과제 | 제외 평균 [95%] | 제외 과제 | 제외 − 포함 [95%] |")
        w("|---|---|---|---|---|---|")
        for lab, c in (("run 1 (seed %d)" % s1, A["ext"]["diff"]["trained-vanilla"]), ("run 2 (seed %d)" % s2, rp["ext_diff"])):
            w("| %s | %s | %s | %s | %s | %s |" % (lab, mn(c["incl"], sg, sci), "·".join(c["incl"]["tasks"]) if c["incl"] else "-", mn(c["excl"], sg, sci),
                                              "·".join(c["excl"]["tasks"]) if c["excl"] else "-",
                                              NONE if c["contrast"] is None else "%s %s" % (sg(c["contrast"]["diff"]), sci(c["contrast"]["ci"]))))
        w("")
        w("- §3.2와 같은 방식이다(과제를 같은 가중치로 평균, 범주 안 과제 재표본 bootstrap %s회). 제외 − 포함이 difference-in-differences다. run 2는 결과 있는 과제만 "
          "들어가 run 1과 과제 구성이 다를 수 있다.\n" % big(ms["task_boot"]))

        x = V["T1_rerun"]
        w("### 7.4 T1 세 run: 준비 V2(b), 본 학습, run 2\n")
        if "test_s14" not in x:
            w("%s (run 2의 T1이 아직 끝나지 않았다).\n" % NONE)
        else:
            R3, ts = x["runs"], x["test_s14"]
            w("| 지표 | V2(b) (준비, seed %d) | 본 학습 run 1 (seed %d) | run 2 (seed %d) |" % (R3["v2b"]["seed"], R3["s2"]["seed"], R3["s14"]["seed"]))
            w("|---|---|---|---|")
            for lab, k in rr:
                w("| %s | %s | %s | %s |" % (lab, f3(R3["v2b"][k]), f3(R3["s2"][k]), f3(R3["s14"][k])))
            w("")
            w("| 짝 비교 (test %s decision) | b/c | exact McNemar p | 정확도 차이 (argmax gold) | case 군집 bootstrap 95%% | 군집 / decision |" % big(ts["s2"]["n"]))
            w("|---|---|---|---|---|---|")
            for k, lab in (("v2b", "V2(b) vs run 2"), ("s2", "본 학습 vs run 2")):
                y = ts[k]
                w("| %s | %d/%d | %s | %s | %s | %d / %d |" % (lab, y["b"], y["c"], pv(y["p"]), sg(y["boot"]["diff"]), sci(y["boot"]["ci"]),
                                                          y["boot"]["clusters"], y["boot"]["items"]))
            w("")
            w("- 같은 seed의 V2(b)와 본 학습 편차는 §6.4다. b = 앞 run만 정답, c = run 2만 정답이고 정확도 차이는 앞 run − run 2다.\n")

    w("## 8. 그림\n")
    pal = FG["palette"]
    w("- 범주 색 슬롯 1~3(파랑 Jev, 주황 vanilla, 청록 trained)은 F의 그림과 같은 색이다. 팔레트 검증기 출력(`figs/palette_check.txt`, F에서 복사)에서 최악 CVD ΔE는 "
      "슬롯 1~3 인접쌍 %g, 전체쌍 %g로 통과다. 청록(대비 %g)은 밝은 배경 대비 3:1 미만이라 표와 막대 안 직접 라벨을 함께 둔다. 정적 PNG/SVG라 라이트 모드만 만들었다.\n"
      % (pal["slots3_adjacent"]["worst_cvd_de"], pal["slots3_all_pairs"]["worst_cvd_de"], pal["slots3_adjacent"]["below_3to1"]["#1baf7a"]))
    for f, cap in (("accuracy_3arm", "과제별 3-arm 정확도 (Jev 항목)"), ("ext_trained_minus_vanilla", "ext: trained − vanilla"),
                   ("dev_curves", "과제별 dev 곡선"), ("category_macro", "범주별 arm macro")):
        w("![%s](figs/%s.png)\n" % (cap, f))

    w("## 9. 재현\n")
    w("- `nice -n 10 .venv/bin/python results/T3arm/t3arm_summary.py build --root %s --out <out>`" % M["root"])
    w("- `nice -n 10 .venv/bin/python results/T3arm/t3arm_summary.py verify --root %s --out <out>`" % M["root"])
    w("- 입력: Jev `results/F/jev_cmp/jev_runs_all.jsonl`(s6_summary 경로; T9·T10은 %d-%d번째 줄 = 세션 S7, verify는 `%s/raw/analyze/`와 대조, 둘 다 공개 저장소에는 포함하지 않음), F 종합 "
      "`results/F/jev_cmp/summary.json`, vanilla `results/F/jev_cmp/laya/`(T1-T8 Jev 세트)와 `results/T3arm/vanilla/`(T9·T10 Jev 형식 세트, 모든 ext), %s `%s/<task>/`, "
      "trained run 1 `<root>/<task>/`와 run 2 `<root>/%s/<task>/`, 검증 `results/T3arm/validity/`."
      % (M["s7"]["master_lines"][0], M["s7"]["master_lines"][1], M["s7"]["session_dir"], CALIB_KO, M["calib_dir"], REP))
    w("- 모델 로드와 평가는 하지 않는다. 통계는 `s6_summary.py`(McNemar, Holm, 군집 bootstrap, 그림 스타일), `laya_summary.py`(decision 매핑, T1 Part B), "
      "`scripts/metrics_extra.py`(coverage)를 import해 쓴다.")
    return S6.esc_tilde("\n".join(L) + "\n")


# ---------------------------------------------------------------- verify
DT = r"\d{4}-\d{2}-\d{2}|\b\d{2}:\d{2}(?::\d{2})?\b"


def json_numbers(o):
    """Every way a summary.json number may be printed, and the numbers inside its strings (s6_summary verify §3)."""
    allowed, strings = set(), []

    def walk(v):
        if isinstance(v, dict):
            strings.extend(map(str, v))
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str):
            strings.append(v)
        elif isinstance(v, (int, float)) and not isinstance(v, bool) and v == v:
            for x in (v, abs(v), 100 * v, 100 * abs(v)):
                allowed.update({"%.0f" % x, "%.1f" % x, "%.2f" % x, "%.3f" % x, "%.4f" % x, "%g" % x, "%.1e" % x})
                if float(x).is_integer():
                    allowed.add(str(int(x)))
    walk(o)
    for s in strings:
        allowed.update(m.group(0).lstrip("+-") for m in S6.TNUM.finditer(s))
    return allowed, "\n".join(strings)


def verify(root, out):
    o, md = rj(out / "summary.json"), (out / "summary.ko.md").read_text(encoding="utf-8")
    T, A, V, M = o["tasks"], o["aggregate"], o["validity"], o["meta"]
    fails, n_ok = [], Counter()

    def check(cond, kind_, msg):
        n_ok[kind_] += bool(cond)
        if not cond:
            fails.append("[%s] %s" % (kind_, msg))

    # 1. summary.json equals a rebuild from the inputs, summary.md is its rendering
    fresh, cor, cor2, F = collect(root, out)
    fresh["meta"]["built_kst"] = M["built_kst"]
    jrows = jev_rows(fresh)
    dump = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True)  # noqa: E731  (text compare: NaN != NaN)
    check(dump(fresh) == dump({k: v for k, v in o.items() if k != "figures"}), "json=inputs", "summary.json differs from a rebuild from the inputs")
    check(md == render_md(o), "md=render(json)", "summary.ko.md differs from render_md(summary.json)")

    # 2. every number in summary.md is a summary.json number
    allowed, blob = json_numbers(o)
    check("—" not in md and "–" not in md, "no-dash", "summary.ko.md has an em or en dash")
    body = re.sub(r"\]\([^)]*\)", "]", re.sub(r"(?m)^#+ [\d.]+", " ", re.sub(r"`[^`]*`", " ", md)))
    for dt in re.findall(DT, body):
        check(dt in blob, "md=json", "date/time %s not in summary.json" % dt)
    body = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", re.sub(DT, " ", body).replace("−", "-"))
    for m in S6.MDNUM.finditer(body):
        check(m.group(0).lstrip("+-") in allowed, "md=json", "number %s (...%s...) not in summary.json"
              % (m.group(0), body[max(0, m.start() - 40):m.end() + 20].replace("\n", " ")))

    # 3. every table row carries its json fields, in column order
    hd = list(re.finditer(r"(?m)^##+ ([\d.]+) ", md))
    sec = {m.group(1): md[m.end():hd[k + 1].start() if k + 1 < len(hd) else len(md)] for k, m in enumerate(hd)}
    D = lambda *vs, d=3: [(float(v), d) for v in vs if v is not None and v == v]  # noqa: E731
    a5 = lambda s: D(s["correct"], s["n"], d=0) + D(s["acc"], *s["wilson"]) if s else []  # noqa: E731
    tx = lambda x: D(x["b"], x["c"], d=0) + D(x["p"], x["holm_p"], d=4) if x else []  # noqa: E731
    mci = lambda c: D(c["mean"], *c["ci"]) if c else []  # noqa: E731

    def sem(k, keys, exp, what):
        r = next((r for tb in S6.md_tables(sec[k]) for r in tb if all(any(c == y or c.startswith(y + " ") for c in r) for y in keys)), None)
        check(r is not None and S6._subseq(exp, S6.tnums(r[1:])), "md=json semantic", "§%s %s" % (k, what))
    for t in TASKS:
        x, e, d, c = T[t]["items"], T[t]["ext"], T[t].get("diag"), T[t].get("cost")
        sem("1.1", [t], D(x["n"], d=0) + sum((a5(x[a]) for a in ARMS), []) + sum((tx(x["tests"].get(f)) for f in FAMS), []), t)
        y = e.get("test")
        sem("2.1", [t], D(e["n"], d=0) + a5(e["vanilla"]) + a5(e["trained"]) + (D(y["boot"]["diff"], *y["boot"]["ci"]) + tx(y) if y else []), t)
        k = {"boolean": "auroc", "score": "mae"}.get(T[t]["kind"])
        if k:
            sem("1.5", [t], D(*(x[a][k] for a in ARMS if x[a])), "%s %s" % (t, k))
        for num, layer, arms in (("4.1", "items", ARMS), ("4.2", "ext", ("vanilla", "trained"))):
            for a in arms:
                s = T[t][layer][a]
                if s:
                    sem(num, [t, ARM_KO[a]], D(s["brier"], s["ece"], s["cov05"], s["cov10"]), "%s %s" % (t, a))
            s, cc = T[t][layer]["calib"], T[t]["calib"]
            sem(num, [t, CALIB_KO], D(*(v for r, p in zip(cc["temperature_raw"], cc["temperature_applied"]) for v in ((r,) if r == p else (r, p))))
                + D(s["brier"], s["ece"], s["cov05"], s["cov10"]), "%s calib" % t)
        E = T[t]["calib"]["effect"]
        sem("4.3", [t], D(*(E[k][m][x] for k in ("items", "ext") for m in ("ece", "brier") for x in ("refit", "train"))), "%s calib effect" % t)
        if c:
            sem("5.", [t], D(c["labels"], c["train_items"], c["calib_items"], c["dev_items"], c["epochs"], c["optimizer_steps"], d=0)
                + D(c["train_loop_min"], c["wall_min"], d=1) + D(c["items_per_s"], d=2) + D(c["mps_alloc_gb"], c["mps_driver_gb"], d=1) + D(c["ckpt_gb"], d=2), t)
        if d:
            f = d["flip"]
            sem("6.1", [t], D(*d["dev"]) + D(d["selected_epoch"], d=0) + D(d["gap"], *d["temperature"])
                + (D(f["flip_rate_per_perm"], *f["flip_rate_per_perm_ci"]) + D(f["n_items"], d=0) if f else [])
                + D(d["recall"]["up"], d["recall"]["down"], d["recall"]["same"], d=0) + D(d["recall"]["min"][1], d["recall"]["max"][1]), t)
    lc = T["T10"]["items"]["label_check"]
    for q, x in list(lc["queues"].items()) + [("합계", lc["total"])]:
        sem("1.6", [q], D(*(v for k in lc["systems"] if x[k]["n"] for v in (x[k]["correct"], x[k]["n"])), d=0), "T10 queue " + q)
    x, pl = T["T1"]["items"], T["T7"]["items"]["per_lang"]
    aux = lambda s: D(*(s[k] for k in ("soft_acc", "brier_vs_soft", "score_mae"))) if s else []  # noqa: E731
    for a in ARMS:
        sem("1.2", [ARM_KO[a]], a5(x[a]) + aux(x[a]) + a5(x["all"].get(a)) + aux(x["all"].get(a)), "T1 " + a)
        sem("1.3", [ARM_KO[a]], sum((D(pl[L][a]["correct"], pl[L][a]["n"], d=0) + D(pl[L][a]["acc"]) for L in S6.LANGS if a in pl[L]), [])
            + a5(T["T7"]["items"][a]), "T7 " + a)
    for t in ("T1", "T7"):
        for f, ab in FAMS.items():
            y = T[t]["items"]["tests"].get(f)
            if y:
                sem("1.4", [t, "%s − %s" % ab], D(y["boot"]["diff"], *y["boot"]["ci"]) + D(y["boot"]["clusters"], y["boot"]["items"], y["b"], y["c"], d=0)
                    + D(y["p"], d=4), "%s %s" % (t, f))
    e1 = T["T1"]["ext"]
    for lab, s in (("upstream", V["V2"]["upstream"]), ("준비", V["V2"]["ours"]), ("vanilla english", e1["vanilla"]), ("trained", e1["trained"])):
        if s:
            sem("2.2", [lab], D(*(s[k] for k in ("acc_vs_label", "acc", "soft_acc", "brier_vs_soft", "ece", "score_mae")),
                                *(s["by_type"].get(k) for k in ("choice", "noul", "score"))), "T1 ext " + lab)
    for layer, lab in (("items", "Jev 항목"), ("ext", "ext")):
        for a, c in A[layer]["macro"].items():
            sem("3.1", [lab, ARM_KO[a]], mci(c["incl"]) + mci(c["excl"]), "%s %s" % (layer, a))
        for k, c in A[layer]["diff"].items():
            sem("3.2", [lab, "%s − %s" % tuple(ARM_KO[a] for a in k.split("-"))], mci(c["incl"]) + mci(c["excl"])
                + (D(c["contrast"]["diff"], *c["contrast"]["ci"]) if c["contrast"] else []), "%s %s" % (layer, k))
    v3 = V["V3"]
    sem("6.3", ["(a) 엄격"], D(v3["margin"], v3["permuted"], v3["a_threshold"], v3["a_excess"]), "V3 a")
    sem("6.3", ["(b) 차이"], D(v3["gap"], *((v3["real_ep1_s2"], v3["permuted"], v3["b_diff"]) if v3["b_diff"] is not None else ()), v3["gap"],
                              v3["b_excess"]), "V3 b")
    sem("6.3", ["(c) 대안"], D(v3["vanilla_prep"], v3["permuted"], v3["c_vanilla_minus_permuted"], v3["b_diff"]), "V3 c")
    x = V["T1_rerun"]
    check(x["status"] == ("ok" if not M["smoke"] and "T1" in M["done"] else NA if M["smoke"] else NONE), "T1 rerun", "status %s" % x["status"])
    rl = (("dev epoch 1", "dev_ep1"), ("dev epoch 2", "dev_ep2"), ("test accuracy (dataset", "acc_vs_label"), ("test accuracy (argmax gold)", "acc"),
          ("test soft acc", "soft_acc"), ("test Brier vs soft", "brier_vs_soft"), ("test score MAE", "score_mae"), ("test ECE", "ece"),
          ("calibration 행 정확도", "calib_acc"), ("마지막 train CE 창", "train_ce_last"))
    if x["status"] == "ok":
        R, y = x["runs"], x["test"]
        for lab, k in rl:
            sem("6.4", [lab], D(R["v2b"][k], R["s2"][k]), "T1 rerun " + k)
        sem("6.4", ["V2(b) vs 본 학습"], D(y["b"], y["c"], d=0) + D(y["p"], d=4) + D(y["boot"]["diff"], *y["boot"]["ci"]) + D(y["boot"]["clusters"], y["boot"]["items"], d=0),
            "T1 rerun McNemar")
        sem("6.4", ["두 run의 평균 절대 차이"], D(*(g["mean_abs_diff"] for g in x["trace"]["segments"]), d=4), "T1 rerun loss trace")
        for k in ("acc_vs_label", "acc", "soft_acc", "brier_vs_soft", "ece", "score_mae"):  # V2(b) = V2_upstream_repro.json, main run = the T1 ext row
            check(abs(R["v2b"][k] - V["V2"]["ours"][k]) < 1e-9 and abs(R["s2"][k] - T["T1"]["ext"]["trained"][k]) < 1e-9, "T1 rerun=V2/ext", k)
        check([R["s2"]["dev_ep1"], R["s2"]["dev_ep2"]] == T["T1"]["diag"]["dev"][1:], "T1 rerun=diag", "main run dev per epoch")
        check(abs((y["b"] - y["c"]) / y["n"] - (R["v2b"]["acc"] - R["s2"]["acc"])) < 1e-12 and abs(y["boot"]["diff"] - (R["v2b"]["acc"] - R["s2"]["acc"])) < 1e-12,
              "T1 rerun", "paired difference = accuracy difference")
    rp = o["repeat"]
    check(rp["status"] == (NA if M["smoke"] else "ok"), "repeat", "status %s" % rp["status"])
    for t in rp.get("done", []):
        r, x = rp["tasks"][t], T[t]
        y = r["runs_test"]
        sem("7.1", [t], sum((D(x[k]["trained"]["acc"], r[k]["trained"]["acc"], r["mean"][k]) for k in ("items", "ext")), []) + D(y["b"], y["c"], d=0)
            + D(y["p"], d=4) + (D(y["boot"]["diff"], *y["boot"]["ci"]) if "boot" in y else []) + D(x["diag"]["selected_epoch"], r["diag"]["selected_epoch"], d=0),
            "run 2 " + t)
        for f, lab in AGREE:
            a, b = (x["ext"]["test"], r["ext"]["test"]) if f == "ext" else (x["items"]["tests"][f], r["items"]["tests"][f])
            sem("7.2", [t, lab], D(a["holm_p"], b["holm_p"], d=4), "agree %s %s" % (t, f))
            check(r["agree"][f] == ("확정" if a["verdict_holm"] == b["verdict_holm"] else "불일치"), "repeat agree", "%s %s" % (t, f))
    if rp["status"] == "ok":
        g = rp["agree"]
        rows72 = [r for tb in S6.md_tables(sec["7.2"]) for r in tb]
        check(len(rows72) == g["comparisons"] == g["confirmed"] + g["disagree"] + g["missing"] == len(AGREE) * len(TASKS)
              and [r[1] for r in rows72] == [lab for _ in TASKS for _, lab in AGREE], "repeat agree", "§7.2 rows and counts %s" % g)
        for lab, c in (("run 1", A["ext"]["diff"]["trained-vanilla"]), ("run 2", rp["ext_diff"])):
            sem("7.3", [lab], mci(c["incl"]) + mci(c["excl"]) + (D(c["contrast"]["diff"], *c["contrast"]["ci"]) if c["contrast"] else []), "repeat aggregate " + lab)
    if "test_s14" in V["T1_rerun"]:
        R, r1 = V["T1_rerun"]["runs"], rp["tasks"]["T1"]
        for lab, k in rl:
            sem("7.4", [lab], D(R["v2b"][k], R["s2"][k], R["s14"][k]), "T1 three runs " + k)
        for k, lab in (("v2b", "V2(b) vs run 2"), ("s2", "본 학습 vs run 2")):
            y = V["T1_rerun"]["test_s14"][k]
            sem("7.4", [lab], D(y["b"], y["c"], d=0) + D(y["p"], d=4) + D(y["boot"]["diff"], *y["boot"]["ci"]) + D(y["boot"]["clusters"], y["boot"]["items"], d=0),
                "T1 three runs " + lab)
        for k in ("acc_vs_label", "acc", "soft_acc", "brier_vs_soft", "ece", "score_mae"):  # run 2 = the repeat's T1 ext row
            check(abs(R["s14"][k] - r1["ext"]["trained"][k]) < 1e-9, "T1 rerun=run 2", k)
        check([R["s14"]["dev_ep1"], R["s14"]["dev_ep2"]] == r1["diag"]["dev"][1:] and [R[k]["seed"] for k in ("v2b", "s2", "s14")] == [SEEDS[0], *SEEDS],
              "T1 rerun=run 2", "run 2 dev per epoch, seeds")

    # 4. the inputs agree: F (Jev and vanilla, T1-T8), the driver's paired / summary / select files, the prep's vanilla summary, V2
    for t in S6.TASKS:
        f, x, b = F["tasks"][t], T[t]["items"], base(t)
        for k in ("correct", "n", "acc", "brier", "ece") + tuple(k for k in ("auroc", "mae", "soft_acc", "brier_vs_soft", "score_mae") if k in f["extra"].get(b, {})):
            ref = f["systems"][b][k] if k in f["systems"][b] else f["extra"][b][k]
            check(abs(x["vanilla"][k] - ref) < 1e-9, "vanilla=F", "%s %s: %s vs F %s" % (t, k, x["vanilla"][k], ref))
        # F keeps Jev as aggregates only; the Jev vs vanilla check below pairs the items
        check([sum(cor[t]["jev"].values()), len(cor[t]["jev"])] == [f["systems"]["jev"][k] for k in ("correct", "n")], "jev=F", "%s Jev correct / n" % t)
        m = S6.mcn(*paired(cor[t]["jev"], cor[t]["vanilla"])[1:])
        check([m[k] for k in ("b", "c", "n")] == [f["mcnemar"][b][k] for k in ("b", "c", "n")] and abs(m["p"] - f["mcnemar"][b]["p"]) < 1e-12,
              "jev_vs_vanilla=F", "%s %s vs F %s" % (t, m, f["mcnemar"][b]))
    # T9, T10 against session S7: its lines are the master's last ones (master_records checked them against S7_requests.jsonl), and the
    # analyze output holds the same Jev and vanilla english numbers, McNemar and per-item marks (O / X) as this summary
    master = S6.master_records()
    s7 = [k + 1 for k, r in enumerate(master) if r["session"] == S7]
    n7 = len((J.session_dir(S7) / ("%s_requests.jsonl" % S7)).read_text(encoding="utf-8").splitlines())
    check(s7 == list(range(len(master) - n7 + 1, len(master) + 1)) and M["s7"]["master_lines"] == [s7[0], s7[-1]], "S7=master", "S7 lines %s" % M["s7"])
    tabs = {t: S6.md_tables((J.session_dir(S7) / "raw/analyze" / (t + ".md")).read_text(encoding="utf-8")) for t in NEW}
    per_item = {t: [r for tbl in tb for r in tbl if len(r) == 8 and r[4][:2] in ("O ", "X ")] for t, tb in tabs.items()}  # #, row, id, gold, Jev, english, ...
    for t, tb in tabs.items():
        x = T[t]["items"]
        for a, key in (("jev", ("sys", "jev")), ("vanilla", ("sys", "english"))):
            s = x[a]
            check(S6.find_row(D(s["correct"], s["n"], d=0) + D(s["acc"], *s["wilson"], s["brier"], s["ece"], s.get("auroc")), tb, key) is not None,
                  "S7=analyze", "%s %s" % (t, a))
        y = x["tests"]["jev_vs_vanilla"]
        check(S6.find_row(D(y["n"], y["b"], y["c"], d=0) + D(y["p"], d=4), tb, ("vs", "english")) is not None, "S7=analyze", "%s Jev vs english" % t)
        tag = {it["id"].split("/")[1]: it["id"] for it in J.load_items(sets(t, "jev")[0])[1]}
        for a, col in (("jev", 4), ("vanilla", 5)):
            check({tag[r[2]]: r[col].startswith("O") for r in per_item[t]} == cor[t][a], "S7=analyze", "%s %s per item" % (t, a))
    lc = T["T10"]["items"]["label_check"]
    for q, x in lc["queues"].items():  # per class table: gold, n, Jev, english, multilingual, router
        check(S6.find_row(D(x["jev"]["n"], *(x[k]["correct"] for k in ("jev", "english", "multilingual")), d=0),
                          [[r for r in tbl if len(r) == 6] for tbl in tabs["T10"]], None, must_cell=q) is not None, "S7=analyze", "T10 queue %s" % q)
    check(sorted(int(r[1]) for r in per_item["T10"] if all(r[k].startswith("X") for k in (4, 5, 6))) == jrows["all_wrong_without_trained"],
          "S7=analyze", "T10 rows that Jev, english and multilingual all miss")
    # vanilla + task T: same answers as vanilla, its same_<stem>.json names these reports, its temperatures are export_diff's fit clamped to
    # laya's load range (diagnostics.json temperature_clamp)
    lo, hi = rj(root / M["done"][0] / "diagnostics.json")["temperature_clamp"]["load_range"]
    for t in TASKS:
        c = T[t]["calib"]
        check(c["temperature_raw"] == rj(CALIB / t / "export_diff.json")["fitted_temperature"]
              and c["temperature_applied"] == [min(max(v, lo), hi) for v in c["temperature_raw"]], "calib=export", "%s temperature" % t)
        for layer, k, v in (("jev", "calib", "vanilla"), ("ext", "calib_ext", "vanilla_ext")):
            check(cor[t][k] == cor[t][v], "calib=vanilla", "%s %s per-item correctness" % (t, layer))
            for s in sets(t, layer):
                p, x = CALIB / t / ("%s_%s.json" % (layer, s)), rj(CALIB / t / ("same_%s.json" % s))
                ck = rj(p)["config"]["checkpoint"]
                check([ck["temperature_raw"], ck["temperature_applied"]] == [c["temperature_raw"], c["temperature_applied"]], "calib=export", "%s %s" % (t, s))
                check([x["ref"], x["other"]] == [rel(vanilla_report(t, layer, s)), rel(p)]
                      and x["decisions"] == x["correct_identical"] == x["argmax_agreement_ties_agree"] == sum(i.startswith(s + "/") for i in cor[t][k]),
                      "calib=same", "%s %s" % (t, s))
    # the driver's paired / summary / select files of run 1 and, for the tasks it has, the repeat run 2
    runs = [(root, M["done"], cor, lambda t: T[t]["diag"], "")]
    if rp["status"] == "ok":
        runs.append((root / REP, rp["done"], cor2, lambda t: rp["tasks"][t]["diag"], " run 2"))
        for t in rp["done"]:
            r, y = rp["tasks"][t], rp["tasks"][t]["runs_test"]
            check(r["seed"] == list(SEEDS), "repeat", "%s train_timing.json seeds %s" % (t, r["seed"]))
            check(abs((y["b"] - y["c"]) / y["n"] - (T[t]["ext"]["trained"]["acc"] - r["ext"]["trained"]["acc"])) < 1e-12, "repeat", "%s run 1 - run 2 = paired difference" % t)
    for d, ts, cc, dg, tag in runs:
        for t in ts:
            rep = {e["report"]: e for e in rj(d / t / "summary.json")}
            for layer, kt, kv in (("jev", "trained", "vanilla"), ("ext", "trained_ext", "vanilla_ext")):
                for s in sets(t, layer):
                    sub = lambda k: {i: c for i, c in cc[t][k].items() if i.startswith(s + "/")}  # noqa: E731
                    m, p = S6.mcn(*paired(sub(kt), sub(kv))[1:]), rj(d / t / ("paired_%s.json" % s))
                    check([m["b"], m["c"], m["n"]] == [p["b_only"], p["a_only"], p["n"]], "paired=driver", "%s%s %s: %s vs %s" % (t, tag, s, m, p))
                    e = rep[rel(d / t / ("%s_%s.json" % (layer, s)))]
                    check([sum(sub(kt).values()), len(sub(kt))] == [e["correct"], e["n"]], "trained=driver summary", "%s%s %s" % (t, tag, s))
            sl = rj(d / t / "select.json")
            check(dg(t)["dev"][1:] == sl["dev_accuracy"] and dg(t)["selected_epoch"] == sl["selected_index"] + 1, "diag=select", t + tag)
    vs = {e["report"]: e for e in rj(ROOT / "results/T3arm/vanilla/vanilla_summary.json")}
    for t in TASKS:
        for layer, k in (("jev", "vanilla"), ("ext", "vanilla_ext")):
            for s in sets(t, layer):
                e = vs.get(rel(vanilla_report(t, layer, s)))
                if e:  # the T1-T8 Jev sets' vanilla reports are F's, checked above
                    cc = [c for i, c in cor[t][k].items() if i.startswith(s + "/")]
                    check([sum(cc), len(cc)] == [e["correct"], e["n"]], "vanilla=prep summary", "%s %s" % (t, s))
    for k in ("acc_vs_label", "acc", "soft_acc", "brier_vs_soft", "ece", "score_mae"):
        check(abs(T["T1"]["ext"]["vanilla"][k] - V["V2"]["english"][k]) < 1e-9, "vanilla=V2", "T1 ext english %s" % k)

    # 5. figure data == table data, files written, palette validated
    FG = o["figures"]
    g = FG["accuracy_3arm"]
    check(g["groups"] == M["done"] and all(g["values"][t][a] == T[t]["items"][a]["acc"] and g["wilson"][t][a] == T[t]["items"][a]["wilson"]
                                           for t in g["groups"] for a in g["values"][t]), "figure=table", "accuracy_3arm")
    g = FG["ext_diff"]
    check(g["rows"] == M["done"] and all(g["diff"][t] == T[t]["ext"]["test"]["boot"]["diff"] and g["ci"][t] == T[t]["ext"]["test"]["boot"]["ci"]
                                         for t in g["rows"]), "figure=table", "ext_diff")
    check(g["run2"] == {t: rp["tasks"][t]["ext"]["test"]["boot"]["diff"] for t in rp.get("done", []) if t in g["rows"]}, "figure=table", "ext_diff run 2")
    check(list(FG["dev_curves"]) == M["done"] and all(FG["dev_curves"][t] == T[t]["diag"]["dev"] for t in FG["dev_curves"]), "figure=table", "dev_curves")
    check(all(v[c] == A[layer]["macro"][a][c]["mean"] for layer, x in FG["category_macro"].items() for a, v in x.items() for c in CATS),
          "figure=table", "category_macro")
    for name_ in ("accuracy_3arm", "ext_trained_minus_vanilla", "dev_curves", "category_macro"):
        for ext in ("png", "svg"):
            p = out / "figs" / ("%s.%s" % (name_, ext))
            check(p.exists() and p.stat().st_size > 10_000, "figure=table", "%s missing or empty" % p.name)
    check(all(v["all_pass"] for k, v in FG["palette"].items() if k != "validator"), "figure=table", "palette validator did not pass")

    print("checks passed: %s" % ", ".join("%s %d" % kv for kv in sorted(n_ok.items())))
    print("MISMATCHES: %d" % len(fails))
    for f in fails:
        print("  " + f)
    sys.exit(1 if fails else 0)


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("mode", choices=("build", "verify"))
    p.add_argument("--root", default="results/T3arm", help="run_all_tasks.sh results, relative to the project root (SMOKE: results/T3arm/smoke_<ts>)")
    p.add_argument("--out", default="results/T3arm", help="where summary.json, summary.ko.md and figs/ go, relative to the project root")
    a = p.parse_args()
    root, out = (ROOT / a.root).resolve(), (ROOT / a.out).resolve()
    if a.mode == "verify":
        return verify(root, out)
    out.mkdir(parents=True, exist_ok=True)
    o = collect(root, out)[0]
    o["figures"] = figures(o, out)
    jev_rows(o)
    (out / "summary.json").write_text(json.dumps(o, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "summary.ko.md").write_text(render_md(o), encoding="utf-8")
    print("wrote %s, %s and %s/ (%d of %d tasks with results)" % (rel(out / "summary.json"), rel(out / "summary.ko.md"), rel(out / "figs"),
                                                                  len(o["meta"]["done"]), len(TASKS)))


if __name__ == "__main__":
    main()
