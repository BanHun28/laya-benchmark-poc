"""K2 analyzer (throwaway): reads the laya-evals report JSONs (`cases[*]`), the P0b Korean probe
reports and K2_E3_embed_align.json, writes results/korean_support/K2_analysis.md. No forward pass.

    source env.sh && .venv/bin/python results/korean_support/K2_analyze.py
"""
import json
import math
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
POC = ROOT / "results/poc"
sys.path.insert(0, str(POC))
from P0c_analyze import macro_f1, mcnemar_exact, wilson  # noqa: E402

META = json.loads((HERE / "K2_build_meta.json").read_text(encoding="utf-8"))
QIDS = ["intent", "is_urgent", "frustration", "refund_requested", "churn_risk", "needs_llm", "complexity"]
NOULS = ["is_urgent", "refund_requested", "churn_risk", "needs_llm"]
NEG_ROWS = {4: "churn_risk", 7: "churn_risk", 10: "churn_risk", 11: "refund_requested", 29: "churn_risk"}  # P0b negation table
# BENCHMARKS.md:71 / :117 and research/results/cpu_51_language_sweep_refreshed.json (refreshed_clamped)
UPSTREAM = {("ko", "multilingual"): (0.470, 0.3108, 0.7773, 0.68), ("en", "multilingual"): (0.710, 0.2333, 0.8876, 0.92),
            ("en", "english"): (0.820, 0.1382, 0.9582, 0.98), ("ko", "english"): (0.110, 0.6804, 0.7904, 0.14)}
out = []


def p(*lines):
    out.extend(lines)


def report(name):
    return json.loads(((HERE if name.startswith("K2_") else POC) / ("%s.json" % name)).read_text(encoding="utf-8"))


def paired_ci(b, c, n):
    """Wald 95% CI for the paired difference (B - A) = (c - b) / n."""
    d = (c - b) / n
    se = math.sqrt(max(b + c - (c - b) ** 2 / n, 0.0)) / n
    return d - 1.96 * se, d + 1.96 * se


def load_choice(name, qid, jsonl):
    rep = report(name)
    cases = [c for c in rep["cases"] if c["qid"] == qid]
    assert len(cases) == 100
    cfg = rep["config"]
    meta = META["files"][jsonl]
    assert cfg["dataset_sha256"] == meta["sha256"] and cfg["questions_sha256"] == meta["questions_sha256"], name
    r = {"name": name, "cfg": cfg, "overall": rep["overall"],
         "ids": [c["tags"][-1] for c in cases], "gold": [c["expected"] for c in cases],
         "pred": [c["answer"]["choice"] for c in cases], "correct": [bool(c["correct"]) for c in cases],
         "conf": [c["answer"]["answer_confidence"] for c in cases]}
    assert r["correct"] == [g == q for g, q in zip(r["gold"], r["pred"])]
    assert abs(sum(r["correct"]) / 100 - rep["overall"]["choice_accuracy"]) < 1e-12
    assert abs(statistics.fmean(r["conf"]) - rep["overall"]["mean_confidence"]) < 1e-9
    assert r["ids"] == ["id:%s" % i for i in META["massive"]["row_ids"]]
    return r


def acc50(r):
    c = np.asarray(r["conf"])  # research/scripts/bench_local.py:148
    return float(np.asarray(r["correct"], dtype=float)[np.argsort(-c)[:max(1, len(c) // 2)]].mean())


def summary_row(label, lang, model, r):
    x = sum(r["correct"])
    lo, hi = wilson(x, 100)
    present = sorted(set(r["gold"]))
    return "| %s | %s | %s | %d/100 (%.2f) | %.2f-%.2f | %.3f | %.3f | %.3f | %.3f | %.2f |" % (
        label, lang, model, x, x / 100, lo, hi, macro_f1(r["gold"], r["pred"], present),
        macro_f1(r["gold"], r["pred"], sorted(set(r["gold"]) | set(r["pred"]))), statistics.fmean(r["conf"]), r["overall"]["ece"], acc50(r))


def pair_row(label, a, b, la, lb):
    nb = sum(x and not y for x, y in zip(a["correct"], b["correct"]))
    nc = sum(y and not x for x, y in zip(a["correct"], b["correct"]))
    lo, hi = paired_ci(nb, nc, 100)
    agree = sum(x == y for x, y in zip(a["pred"], b["pred"]))
    both = sum(x and y for x, y in zip(a["correct"], b["correct"]))
    return "| %s | %s | %s | %d | %d | %d | %d | %d | %+.2f (%+.2f..%+.2f) | %s | %d/100 |" % (
        label, la, lb, sum(a["correct"]), sum(b["correct"]), both, nb, nc, (nc - nb) / 100, lo, hi, fmt_p(mcnemar_exact(nb, nc)), agree)


def fmt_p(x):
    return "%.4f" % x if x >= 0.001 else "%.1e" % x


SUM_HDR = ["| set | utterances | checkpoint | correct (acc) | 95% Wilson CI | macro-F1 (gold-present classes) | macro-F1 (gold∪pred) "
           "| mean answer_confidence | ECE (report) | acc@50%cov |", "|---|---|---|---|---|---|---|---|---|---|"]
PAIR_HDR = ["| comparison | A | B | A correct | B correct | both | b (A only) | c (B only) | Δ = B−A (95% Wald paired) | McNemar exact p | same argmax |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]


def e1():
    runs = {}
    for d in ("kodesc", "keydesc"):
        for lang, model in (("ko", "multilingual"), ("en", "multilingual"), ("en", "english")):
            runs[(d, lang, model)] = load_choice("K2_scen18-%s_%s_%s" % (d, lang, model), "scenario", "K2_scen18_%s_%s.jsonl" % (d, lang))
    # sanity: the ko runs use the P0c instrument and rows, so the answers must be P0c's
    for d, ref in (("kodesc", "P0c_massive-scenario18_base_multilingual"), ("keydesc", "P0c_massive-scenario18_en-desc_multilingual")):
        rc = [c for c in report(ref)["cases"] if c["qid"] == "scenario"]
        r = runs[(d, "ko", "multilingual")]
        same = sum(c["answer"]["choice"] == q for c, q in zip(rc, r["pred"]))
        dconf = max(abs(c["answer"]["answer_confidence"] - x) for c, x in zip(rc, r["conf"]))
        p("- sanity %s ko/multilingual vs %s: same argmax %d/100, max abs Δ answer_confidence %.4f" % (d, ref, same, dconf))
    desc = {"kodesc": "scenario-18, Korean descriptions (04 §5.1(c))", "keydesc": "scenario-18, upstream key-rendered descriptions"}
    p("", "### E1-a. Accuracy and calibration (n=100 per run)", "", *SUM_HDR)
    for (d, lang, model), r in runs.items():
        p(summary_row(desc[d], lang, model, r))
    p("", "### E1-b. Paired tests on the same 100 MASSIVE ids", "", *PAIR_HDR)
    for d in ("kodesc", "keydesc"):
        p(pair_row("%s: ko vs en (multilingual)" % d, runs[(d, "ko", "multilingual")], runs[(d, "en", "multilingual")], "ko/ml", "en/ml"))
        p(pair_row("%s: en multilingual vs english" % d, runs[(d, "en", "multilingual")], runs[(d, "en", "english")], "en/ml", "en/english"))
    p(pair_row("ko: kodesc vs keydesc (ml)", runs[("kodesc", "ko", "multilingual")], runs[("keydesc", "ko", "multilingual")], "ko/kodesc", "ko/keydesc"))
    p(pair_row("en: kodesc vs keydesc (ml)", runs[("kodesc", "en", "multilingual")], runs[("keydesc", "en", "multilingual")], "en/kodesc", "en/keydesc"))
    p(pair_row("en: kodesc vs keydesc (english)", runs[("kodesc", "en", "english")], runs[("keydesc", "en", "english")], "en/kodesc", "en/keydesc"))
    # per gold label, multilingual ko vs en
    for d in ("kodesc", "keydesc"):
        a, b = runs[(d, "ko", "multilingual")], runs[(d, "en", "multilingual")]
        cnt = Counter(a["gold"])
        p("", "### E1-c. %s: recall per gold scenario, multilingual (ko | en | en/english)" % d, "",
          "| gold | n | ko | en | en (english ckpt) |", "|---|---|---|---|---|")
        e = runs[(d, "en", "english")]
        for k, n in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0])):
            f = lambda r: sum(g == k and q == k for g, q in zip(r["gold"], r["pred"]))
            p("| %s | %d | %d | %d | %d |" % (k, n, f(a), f(b), f(e)))
        p("", "Top confusions (gold→pred ×n): ko %s; en %s" % (
            ", ".join("%s→%s ×%d" % (g, q, n) for (g, q), n in Counter((g, q) for g, q in zip(a["gold"], a["pred"]) if g != q).most_common(5)),
            ", ".join("%s→%s ×%d" % (g, q, n) for (g, q), n in Counter((g, q) for g, q in zip(b["gold"], b["pred"]) if g != q).most_common(5))))
    en_txt = [r["state"]["utterance"].lower() for r in jsonl(HERE / "K2_scen18_kodesc_en.jsonl")]
    p("", "### E1-d. Post-hoc: the `play` class (17 rows) vs the other 83 rows, multilingual", "",
      "| instrument | subset | n | ko correct | en correct | b (ko only) | c (en only) | McNemar p |", "|---|---|---|---|---|---|---|---|")
    for d in ("kodesc", "keydesc"):
        a, b = runs[(d, "ko", "multilingual")], runs[(d, "en", "multilingual")]
        for name, keep in (("gold = play", lambda g: g == "play"), ("gold ≠ play", lambda g: g != "play")):
            idx = [i for i, g in enumerate(a["gold"]) if keep(g)]
            nb = sum(a["correct"][i] and not b["correct"][i] for i in idx)
            nc = sum(b["correct"][i] and not a["correct"][i] for i in idx)
            p("| %s | %s | %d | %d | %d | %d | %d | %s |" % (d, name, len(idx), sum(a["correct"][i] for i in idx),
                                                         sum(b["correct"][i] for i in idx), nb, nc, fmt_p(mcnemar_exact(nb, nc))))
    b = runs[("kodesc", "en", "multilingual")]
    play = [i for i, g in enumerate(b["gold"]) if g == "play"]
    p("", "kodesc en/ml `play` rows: %d/%d contain the literal word \"play\"; correct with the word %d, correct without it %d." % (
        sum("play" in en_txt[i] for i in play), len(play), sum(b["correct"][i] and "play" in en_txt[i] for i in play),
        sum(b["correct"][i] and "play" not in en_txt[i] for i in play)))
    return runs


def jsonl(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def lexical_anchor(label, text):
    """Post-hoc indicator: some part (>= 3 chars) of the gold label key occurs as a substring of the en utterance."""
    return any(len(w) >= 3 and w in text for w in re.split(r"[_ ]", label))


def e2():
    runs = {(lang, model): load_choice("K2_intent20_%s_%s" % (lang, model), "intent", "K2_intent20_%s.jsonl" % lang)
            for lang, model in (("ko", "multilingual"), ("en", "multilingual"), ("en", "english"), ("ko", "english"))}
    p("", "### E2-a. Accuracy and calibration (n=100 per run, 20 options, random 0.05)", "", *SUM_HDR)
    for (lang, model), r in runs.items():
        p(summary_row("intent-20 (upstream-faithful)", lang, model, r))
    p("", "### E2-b. Paired tests", "", *PAIR_HDR)
    p(pair_row("ko vs en (multilingual)", runs[("ko", "multilingual")], runs[("en", "multilingual")], "ko/ml", "en/ml"))
    p(pair_row("en: multilingual vs english", runs[("en", "multilingual")], runs[("en", "english")], "en/ml", "en/english"))
    p(pair_row("ko: english vs multilingual", runs[("ko", "english")], runs[("ko", "multilingual")], "ko/english", "ko/ml"))
    p("", "### E2-c. Reproduction check vs upstream (Track A through laya-evals)", "",
      "Upstream = BENCHMARKS.md:71 (ko) / :117 (en) accuracy and ECE; mean_confidence and acc@50%cov from "
      "research/results/cpu_51_language_sweep_refreshed.json `refreshed_clamped` (laya 0.3.20, x86 CPU, one packed forward per language "
      "via research/eval/laya_eval.py). Ours = laya-evals 0.3.23, CPU fp32, Router.predict row batches of 8.", "",
      "| utterances | checkpoint | ours acc | upstream acc | Δ | within ±0.03 | ours ECE / upstream | ours mean conf / upstream | ours acc@50%cov / upstream |",
      "|---|---|---|---|---|---|---|---|---|")
    for (lang, model), r in runs.items():
        ua, ue, uc, u50 = UPSTREAM[(lang, model)]
        a = sum(r["correct"]) / 100
        p("| %s | %s | %.3f | %.3f | %+.3f | %s | %.4f / %.4f | %.4f / %.4f | %.2f / %.2f |" % (
            lang, model, a, ua, a - ua, "yes" if abs(a - ua) <= 0.03 + 1e-9 else "NO", r["overall"]["ece"], ue,
            statistics.fmean(r["conf"]), uc, acc50(r), u50))
    a, b = runs[("ko", "multilingual")], runs[("en", "multilingual")]
    cnt = Counter(g.split("_", 1)[0] for g in a["gold"])
    p("", "### E2-d. intent-20 correct per gold scenario family, multilingual (ko | en)", "",
      "| scenario family | n | ko | en | en − ko |", "|---|---|---|---|---|")
    for k, n in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0])):
        f = lambda r: sum(g.split("_", 1)[0] == k and ok for g, ok in zip(r["gold"], r["correct"]))
        p("| %s | %d | %d | %d | %+d |" % (k, n, f(a), f(b), f(b) - f(a)))
    conf_split = lambda r: (statistics.fmean([c for c, ok in zip(r["conf"], r["correct"]) if ok]),
                            statistics.fmean([c for c, ok in zip(r["conf"], r["correct"]) if not ok]))
    p("", "Mean answer_confidence correct / wrong: ko/ml %.3f / %.3f, en/ml %.3f / %.3f, en/english %.3f / %.3f, ko/english %.3f / %.3f" % (
        *conf_split(a), *conf_split(b), *conf_split(runs[("en", "english")]), *conf_split(runs[("ko", "english")])))
    en_txt = [r["state"]["utterance"].lower() for r in jsonl(HERE / "K2_intent20_en.jsonl")]
    anchor = [lexical_anchor(g, t) for g, t in zip(a["gold"], en_txt)]
    p("", "### E2-e. Post-hoc: lexical anchor (a part of the gold intent key, ≥3 chars, occurs in the en utterance), multilingual", "",
      "| subset | n | ko correct | en correct | b (ko only) | c (en only) | McNemar p |", "|---|---|---|---|---|---|---|")
    for name, flag in (("en utterance contains a gold-key word", True), ("no gold-key word in en utterance", False)):
        idx = [i for i, x in enumerate(anchor) if x == flag]
        nb = sum(a["correct"][i] and not b["correct"][i] for i in idx)
        nc = sum(b["correct"][i] and not a["correct"][i] for i in idx)
        p("| %s | %d | %d | %d | %d | %d | %s |" % (name, len(idx), sum(a["correct"][i] for i in idx), sum(b["correct"][i] for i in idx),
                                                 nb, nc, fmt_p(mcnemar_exact(nb, nc))))
    return runs


# ---------------------------------------------------------------- E4
def probe_rows(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def per_row(name, rows):
    rep = report(name)
    cases = rep["cases"]
    assert len(cases) == 30 * len(QIDS)
    grouped = []
    for i, row in enumerate(rows):
        g = cases[i * 7:(i + 1) * 7]
        assert [c["qid"] for c in g] == QIDS and all(c["expected"] == row["expected"][c["qid"]] for c in g), (name, i)
        grouped.append({c["qid"]: c["answer"] for c in g})
    return rep, grouped


def auroc(scores, labels):
    pos = [s for s, l in zip(scores, labels) if l]
    neg = [s for s, l in zip(scores, labels) if not l]
    return sum((a > b) + 0.5 * (a == b) for a in pos for b in neg) / (len(pos) * len(neg))


def level_argmax(ans):
    return int(max(ans["probabilities"], key=ans["probabilities"].get))


def probe_metrics(rows, ans):
    m = {}
    for q in ("intent", "complexity"):
        m[q] = {"ok": [a[q]["choice"] == r["expected"][q] for r, a in zip(rows, ans)]}
    for q in NOULS:
        exp = [r["expected"][q] for r in rows]
        pr = [a[q]["noul"] for a in ans]
        m[q] = {"ok": [(x >= 0.5) == e for x, e in zip(pr, exp)], "pos": sum(x >= 0.5 for x in pr), "exp_pos": sum(exp),
                "tp": sum(x >= 0.5 and e for x, e in zip(pr, exp)), "fp": sum(x >= 0.5 and not e for x, e in zip(pr, exp)),
                "auroc": auroc(pr, exp), "pmin": min(pr), "pmax": max(pr), "psd": statistics.pstdev(pr)}
    exp = [r["expected"]["frustration"] for r in rows]
    fa = [a["frustration"] for a in ans]
    m["frustration"] = {"ok": [level_argmax(a) == e for a, e in zip(fa, exp)], "mae": statistics.fmean(abs(a["score"] - e) for a, e in zip(fa, exp)),
                        "l0_argmax": sum(level_argmax(a) == 0 for a in fa), "l0_round": sum(round(a["score"]) == 0 for a in fa),
                        "smin": min(a["score"] for a in fa), "smax": max(a["score"] for a in fa), "exp_l0": sum(e == 0 for e in exp)}
    for q in QIDS:
        m[q]["ac"] = statistics.fmean(a[q]["answer_confidence"] for a in ans)
    return m


def e4():
    ko_rows = probe_rows(POC / "P0_probe_sentences.jsonl")
    en_rows = probe_rows(HERE / "probe_en.jsonl")
    assert [r["expected"] for r in ko_rows] == [r["expected"] for r in en_rows]
    runs = {"KO/ml (P0b V0)": ("P0b_V0_v1_multilingual", ko_rows), "EN/ml": ("K2_probe-en-v1_multilingual", en_rows),
            "KO/english (P0b V0)": ("P0b_V0_v1_english", ko_rows), "EN/english": ("K2_probe-en-v1_english", en_rows),
            "KO/ml v1b (P0b V1)": ("P0b_V1_criteria_multilingual", ko_rows), "EN/ml v1b": ("K2_probe-en-v1b_multilingual", en_rows)}
    M, A, R = {}, {}, {}
    for k, (name, rows) in runs.items():
        R[k], A[k] = per_row(name, rows)
        M[k] = probe_metrics(rows, A[k])
        sl = R[k]["slices"]["qid"]
        for q in ("intent", "complexity"):
            assert abs(sl[q]["choice_accuracy"] - statistics.fmean(M[k][q]["ok"])) < 1e-9
        for q in NOULS:
            assert abs(sl[q]["noul_accuracy"] - statistics.fmean(M[k][q]["ok"])) < 1e-9
        assert abs(sl["frustration"]["score_mae"] - M[k]["frustration"]["mae"]) < 1e-9
    assert R["EN/ml"]["config"]["questions_sha256"] == R["KO/ml (P0b V0)"]["config"]["questions_sha256"]
    assert R["EN/ml v1b"]["config"]["questions_sha256"] == R["KO/ml v1b (P0b V1)"]["config"]["questions_sha256"]
    v1 = ["KO/ml (P0b V0)", "EN/ml", "KO/english (P0b V0)", "EN/english"]
    p("", "### E4-a. Same 30 probe rows, Korean vs English state, v1 schema (questions_sha256 identical: %s)" % R["EN/ml"]["config"]["questions_sha256"], "",
      "Cells: choice/noul `correct/30`; noul adds `pred pos k / exp e`, AUROC of p(true) vs label (0.5 = does not rank), p(true) min–max; "
      "frustration: MAE, exact level (argmax), level-0 pick argmax / round(score) (expected 18/30), score range.", "",
      "| qid | baseline | " + " | ".join(v1) + " |", "|---|---|" + "---|" * len(v1))
    for q in QIDS:
        cells = []
        for k in v1:
            m = M[k][q]
            if q in NOULS:
                cells.append("%d/30, pos %d / exp %d, AUROC %.2f, p %.2f–%.2f" % (sum(m["ok"]), m["pos"], m["exp_pos"], m["auroc"], m["pmin"], m["pmax"]))
            elif q == "frustration":
                cells.append("MAE %.3f, exact %d/30, L0 %d / %d, score %.2f–%.2f" % (m["mae"], sum(m["ok"]), m["l0_argmax"], m["l0_round"], m["smin"], m["smax"]))
            else:
                cells.append("%d/30" % sum(m["ok"]))
        if q in NOULS:
            base = "always-no %d/30" % (30 - M[v1[0]][q]["exp_pos"])
        elif q == "frustration":
            base = "always-0 MAE 0.700"
        else:
            base = "majority %d/30" % Counter(r["expected"][q] for r in ko_rows).most_common(1)[0][1]
        p("| %s | %s | %s |" % (q, base, " | ".join(cells)))
    p("| binary Σ /120 | always-no 93 | " + " | ".join("%d" % sum(sum(M[k][q]["ok"]) for q in NOULS) for k in v1) + " |")
    p("| mean noul AUROC | 0.50 | " + " | ".join("%.2f" % statistics.fmean(M[k][q]["auroc"] for q in NOULS) for k in v1) + " |")
    p("", "Mean answer_confidence per question:", "", "| qid | " + " | ".join(v1) + " |", "|---|" + "---|" * len(v1))
    for q in QIDS:
        p("| %s | %s |" % (q, " | ".join("%.3f" % M[k][q]["ac"] for k in v1)))
    p("", "### E4-b. Paired exact McNemar, Korean vs English state (n=30; frustration uses exact argmax level)", "",
      "| checkpoint | qid | KO correct | EN correct | b (KO only) | c (EN only) | p |", "|---|---|---|---|---|---|---|")
    for ko_k, en_k, label in (("KO/ml (P0b V0)", "EN/ml", "multilingual"), ("KO/english (P0b V0)", "EN/english", "english"),
                              ("KO/ml v1b (P0b V1)", "EN/ml v1b", "multilingual v1b")):
        for q in QIDS:
            a, b = M[ko_k][q]["ok"], M[en_k][q]["ok"]
            nb = sum(x and not y for x, y in zip(a, b))
            nc = sum(y and not x for x, y in zip(a, b))
            p("| %s | %s | %d | %d | %d | %d | %.3f |" % (label, q, sum(a), sum(b), nb, nc, mcnemar_exact(nb, nc)))
    vb = ["KO/ml (P0b V0)", "EN/ml", "KO/ml v1b (P0b V1)", "EN/ml v1b"]
    p("", "### E4-c. Criteria (v1b) vs none (v1), multilingual, Korean vs English state", "",
      "| qid | expected pos | " + " | ".join(vb) + " |", "|---|---|" + "---|" * len(vb))
    for q in NOULS:
        p("| %s | %d | %s |" % (q, M[vb[0]][q]["exp_pos"], " | ".join(
            "%d/30, pos %d (TP %d, FP %d), AUROC %.2f, conf %.3f" % (sum(M[k][q]["ok"]), M[k][q]["pos"], M[k][q]["tp"], M[k][q]["fp"], M[k][q]["auroc"], M[k][q]["ac"])
            for k in vb)))
    p("| binary Σ /120 (always-no 93) | | " + " | ".join("%d" % sum(sum(M[k][q]["ok"]) for q in NOULS) for k in vb) + " |")
    p("| mean noul AUROC | | " + " | ".join("%.2f" % statistics.fmean(M[k][q]["auroc"] for q in NOULS) for k in vb) + " |")
    p("", "### E4-d. Negation rows (P0 rows 4, 7, 10, 11, 29): negated binary target p(true) and intent", "",
      "| row | negated target | expected intent | KO/ml p / intent | EN/ml p / intent | EN/english p / intent | KO/ml v1b p | EN/ml v1b p |",
      "|---|---|---|---|---|---|---|---|")
    for i, q in NEG_ROWS.items():
        f = lambda k: "%.2f / %s" % (A[k][i][q]["noul"], A[k][i]["intent"]["choice"])
        p("| %d | %s | %s | %s | %s | %s | %.2f | %.2f |" % (i, q, ko_rows[i]["expected"]["intent"], f("KO/ml (P0b V0)"), f("EN/ml"), f("EN/english"),
                                                            A["KO/ml v1b (P0b V1)"][i][q]["noul"], A["EN/ml v1b"][i][q]["noul"]))
    p("", "### E4-e. Per-row noul p(true), multilingual v1 (KO → EN); * = expected true", "",
      "| row | is_urgent | refund_requested | churn_risk | needs_llm | intent exp | KO intent | EN intent |", "|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(ko_rows):
        cells = ["%s%.2f→%.2f" % ("*" if r["expected"][q] else "", A["KO/ml (P0b V0)"][i][q]["noul"], A["EN/ml"][i][q]["noul"]) for q in NOULS]
        p("| %d | %s | %s | %s | %s |" % (i, " | ".join(cells), r["expected"]["intent"], A["KO/ml (P0b V0)"][i]["intent"]["choice"], A["EN/ml"][i]["intent"]["choice"]))
    p("", "Run identity (report config): " + "; ".join("%s = %s dataset_sha256 %s questions_sha256 %s revision %s" % (
        k, runs[k][0], R[k]["config"]["dataset_sha256"][:16], R[k]["config"]["questions_sha256"][:16], list(R[k]["config"]["revisions"].values())[0][:12]) for k in runs))
    return M


def e3():
    d = json.loads((HERE / "K2_E3_embed_align.json").read_text(encoding="utf-8"))
    p("", "### E3. Cross-lingual alignment of mean-pooled encoder embeddings (100 ko utterances ↔ 100 en twins; chance P@1 0.01, P@5 0.05)", "",
      "| checkpoint | ko→en P@1 (strict / dup-aware) | ko→en P@5 | en→ko P@1 (strict / dup-aware) | en→ko P@5 | median rank of twin ko→en / en→ko "
      "| mean cos true pairs | mean cos random pairs (sd) | gap (in random-pair sd) | ko-ko / en-en off-diagonal mean cos | tokens per utterance ko / en |",
      "|---|---|---|---|---|---|---|---|---|---|---|")
    for name, r in d["by_checkpoint"].items():
        ke, ek = r["ko_to_en"], r["en_to_ko"]
        p("| %s | %.2f / %.2f | %.2f | %.2f / %.2f | %.2f | %.0f / %.0f | %.3f | %.3f (%.3f) | %+.3f (%.1f) | %.3f / %.3f | %.1f / %.1f |" % (
            name, ke["strict"]["p_at_1"], ke["dup_aware"]["p_at_1"], ke["strict"]["p_at_5"], ek["strict"]["p_at_1"], ek["dup_aware"]["p_at_1"],
            ek["strict"]["p_at_5"], ke["strict"]["median_rank"], ek["strict"]["median_rank"], r["mean_cos_true_pairs"], r["mean_cos_random_pairs"],
            r["std_cos_random_pairs"], r["gap_true_minus_random"], r["gap_in_random_sd"], r["mean_cos_ko_ko_offdiag"], r["mean_cos_en_en_offdiag"],
            r["tokens"]["ko"]["mean_tokens"], r["tokens"]["en"]["mean_tokens"]))
    return d


def main():
    p("# K2 analysis (generated by results/korean_support/K2_analyze.py; do not edit by hand)", "")
    p("## E1. MASSIVE scenario-18, paired ko vs en", "")
    r1 = e1()
    p("", "## E2. MASSIVE intent-20 (upstream-faithful), paired ko vs en")
    r2 = e2()
    p("", "## E3. Embedding alignment")
    r3 = e3()
    p("", "## E4. P0 probe: Korean vs English state on the same checkpoint")
    e4()
    (HERE / "K2_analysis.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
