"""P0b zero-shot schema ablation analysis (throwaway). n=30, self-labelled, no CI: every number is indicative.

    .venv/bin/python results/poc/P0b_ablation_analyze.py > <tables.md>

Reads results/poc/P0b_<variant>.jsonl (expected values incl. the V3/V5 remaps) and the laya-evals
reports results/poc/P0b_<variant>_<model>.json (`cases[*]`: expected, answer, correct). Reports that do
not exist yet are skipped, so the same script runs before and after V8.

V8 selection rule, fixed in code before any V1..V7 result was read (select_v8). MARGIN = 2 items,
a heuristic on n=30, not a significance test:
  R1 binary form in {V0, V1, V2, V3a, V3b}: max total binary correct (/120); forms within MARGIN of
     the max tie; among ties min mean |predicted positives - expected positives|; then listed order.
  R2 intent: EN descriptions (V6) only if V6 intent correct >= V0 + MARGIN. 4 classes (V5) only if V5
     correct >= that 6-class run's answers collapsed to the same 4 classes + MARGIN.
  R3 complexity: EN descriptions (V6) only if V6 complexity correct >= V0 + MARGIN.
  R4 Korean instructions (V4), per family: intent / complexity if correct >= V0 + MARGIN; binaries if
     total >= V0 + MARGIN and the positive-count distance is not worse; frustration if MAE <= V0 - 0.10.
  R5 plain-string state + field-less instructions (V7): only if V7 correct over intent + complexity +
     binaries >= V0 + 3 and frustration MAE <= V0 + 0.10. If R4 and R5 both fire, keep the larger gain.
"""
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import fmean

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from P0_probe_analyze import NOULS, QIDS, level_argmax  # noqa: E402
from P0b_build_variants import INTENT6_TO_4  # noqa: E402

VARIANTS = ["V0_v1", "V1_criteria", "V2_labels_ab", "V3a_choice_ab", "V3b_choice_semantic",
            "V4_ko_instructions", "V5_intent4", "V6_en_descriptions", "V7_plain_state", "V8_combo"]
RUNS = [(v, "multilingual") for v in VARIANTS] + [("V0_v1", "english"), ("V8_combo", "english")]
BINARY_FORMS = ["V0_v1", "V1_criteria", "V2_labels_ab", "V3a_choice_ab", "V3b_choice_semantic"]
MARGIN = 2
SHORT = {"is_urgent": "U", "refund_requested": "R", "churn_risk": "C", "needs_llm": "L"}
CODE = {"refund": "rf", "technical_help": "th", "billing_question": "bq", "information": "in",
        "cancellation": "ca", "other": "ot", "billing": "B", "technical": "T"}
CODE4 = {"cancellation": "C", "other": "O"}
# negation rows of the P0 probe (P0_20261002.md:174): row -> the binary whose target the message negates
NEG_ROWS = {4: "churn_risk", 7: "churn_risk", 10: "churn_risk", 11: "refund_requested", 29: "churn_risk"}
P0_REPORT = {"multilingual": "P0_probe_multilingual.json", "english": "P0_probe_english.json"}


def load_jsonl(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


P0_ROWS = load_jsonl(HERE / "P0_probe_sentences.jsonl")


def code(label, four):
    return (CODE4.get(label) or CODE[label]) if four else CODE[label]


def grouped(cases, rows):
    assert len(cases) == len(rows) * len(QIDS), len(cases)
    out = []
    for i, row in enumerate(rows):
        group = cases[i * len(QIDS):(i + 1) * len(QIDS)]
        assert [c["qid"] for c in group] == QIDS
        assert all(c["expected"] == row["expected"][c["qid"]] for c in group)
        out.append({c["qid"]: c for c in group})
    return out


def run_metrics(variant, model):
    rows = load_jsonl(HERE / ("P0b_%s.jsonl" % variant))
    rep = json.load(open(HERE / ("P0b_%s_%s.json" % (variant, model)), encoding="utf-8"))
    per_row = grouped(rep["cases"], rows)
    questions = rows[0]["questions"]
    four = list(questions["intent"]["criteria"]) == ["billing", "technical", "cancellation", "other"]
    m = {"variant": variant, "model": model, "config": rep["config"], "rows": per_row, "questions": questions,
         "four": four, "plain_state": isinstance(rows[0]["state"], str)}

    for q in ("intent", "complexity"):
        preds = [r[q]["answer"]["choice"] for r in per_row]
        exps = [r[q]["expected"] for r in per_row]
        assert all(r[q]["correct"] == (p == e) for r, p, e in zip(per_row, preds, exps))
        m[q] = {"correct": sum(p == e for p, e in zip(preds, exps)), "preds": preds, "exps": exps,
                "mean_ac": fmean(r[q]["answer"]["answer_confidence"] for r in per_row)}
    it = m["intent"]
    if four:
        it["acc4"] = it["correct"]
    else:
        it["acc4"] = sum(INTENT6_TO_4[p] == INTENT6_TO_4[e] for p, e in zip(it["preds"], it["exps"]))
    conf = Counter((e, p) for e, p in zip(it["exps"], it["preds"]) if e != p)
    it["top3"] = sorted(conf.items(), key=lambda kv: (-kv[1], kv[0]))[:3]

    for q in NOULS:
        qd = questions[q]
        if qd["type"] == "choice":
            keys = {r["expected"][q] for r, p0 in zip(rows, P0_ROWS) if p0["expected"][q] is True}
            assert len(keys) == 1, keys
            pos_key = keys.pop()
            pos = [r[q]["answer"]["choice"] == pos_key for r in per_row]
            p_true = [r[q]["answer"]["probabilities"][pos_key] for r in per_row]
        else:
            pos = [r[q]["answer"]["noul"] >= 0.5 for r in per_row]
            p_true = [r[q]["answer"]["noul"] for r in per_row]
        exp = [p0["expected"][q] for p0 in P0_ROWS]
        assert all(r[q]["correct"] == (a == e) for r, a, e in zip(per_row, pos, exp))
        m[q] = {"correct": sum(a == e for a, e in zip(pos, exp)), "pos_pred": sum(pos), "pos_exp": sum(exp),
                "tp": sum(a and e for a, e in zip(pos, exp)), "fp": sum(a and not e for a, e in zip(pos, exp)),
                "fn": sum(e and not a for a, e in zip(pos, exp)), "pos": pos, "p_true": p_true,
                "mean_ac": fmean(r[q]["answer"]["answer_confidence"] for r in per_row), "form": qd["type"]}
    m["binary_total"] = sum(m[q]["correct"] for q in NOULS)
    m["binary_posdist"] = fmean(abs(m[q]["pos_pred"] - m[q]["pos_exp"]) for q in NOULS)

    fr = [(r["frustration"]["expected"], r["frustration"]["answer"]) for r in per_row]
    m["frustration"] = {"mae": fmean(abs(a["score"] - e) for e, a in fr),
                        "exact": sum(level_argmax(a) == e for e, a in fr),
                        "l0_argmax": sum(level_argmax(a) == 0 for e, a in fr),
                        "l0_round": sum(round(a["score"]) == 0 for e, a in fr),
                        "l0_exp": sum(e == 0 for e, a in fr),
                        "score_min": min(a["score"] for e, a in fr), "score_max": max(a["score"] for e, a in fr),
                        "mean_ac": fmean(a["answer_confidence"] for e, a in fr)}

    # cross-check against the harness's own per-qid slices
    sl = rep["slices"]["qid"]
    for q in QIDS:
        t = questions[q]["type"]
        if t == "choice":
            assert abs(sl[q]["choice_accuracy"] - m[q]["correct"] / 30) < 1e-9, (variant, q)
        elif t == "noul":
            assert abs(sl[q]["noul_accuracy"] - m[q]["correct"] / 30) < 1e-9, (variant, q)
        else:
            assert abs(sl[q]["score_mae"] - m["frustration"]["mae"]) < 1e-9, (variant, q)
    return m


def answer_delta(a, b):
    """(argmax flipped?, max |dp|) between two answers to the same question."""
    if a["type"] == "noul":
        return (a["noul"] >= 0.5) != (b["noul"] >= 0.5), abs(a["noul"] - b["noul"])
    pa, pb = a["probabilities"], b["probabilities"]
    flip = max(pa, key=pa.get) != max(pb, key=pb.get)
    return flip, max(abs(pa[k] - pb[k]) for k in pa)


def select_v8(M):
    """Apply the rule in the module docstring to the multilingual V0..V7 metrics."""
    g = lambda v: M[(v, "multilingual")]
    v0 = g("V0_v1")
    notes = []
    cands = [(v, g(v)["binary_total"], g(v)["binary_posdist"]) for v in BINARY_FORMS]
    best = max(c[1] for c in cands)
    tied = [c for c in cands if c[1] >= best - MARGIN]
    form = min(tied, key=lambda c: (c[2], BINARY_FORMS.index(c[0])))[0]
    notes.append("R1 binary form: totals %s; max %d, tied (>= %d) %s -> %s"
                 % (", ".join("%s %d/120 (|pos-exp| %.2f)" % c for c in cands), best, best - MARGIN,
                    [c[0] for c in tied], form))

    v6 = g("V6_en_descriptions")
    intent_desc = "en" if v6["intent"]["correct"] >= v0["intent"]["correct"] + MARGIN else "ko"
    best6 = v6 if intent_desc == "en" else v0
    v5 = g("V5_intent4")
    intent4 = v5["intent"]["correct"] >= best6["intent"]["acc4"] + MARGIN
    notes.append("R2 intent: V0 %d/30, V6 %d/30 -> %s descriptions; V5 %d/30 vs %s collapsed-to-4 %d/30 -> %s"
                 % (v0["intent"]["correct"], v6["intent"]["correct"], intent_desc, v5["intent"]["correct"],
                    best6["variant"], best6["intent"]["acc4"], "4 classes" if intent4 else "6 classes"))

    cx_desc = "en" if v6["complexity"]["correct"] >= v0["complexity"]["correct"] + MARGIN else "ko"
    notes.append("R3 complexity: V0 %d/30, V6 %d/30 -> %s descriptions"
                 % (v0["complexity"]["correct"], v6["complexity"]["correct"], cx_desc))

    v4 = g("V4_ko_instructions")
    ko = {"intent": v4["intent"]["correct"] >= v0["intent"]["correct"] + MARGIN,
          "complexity": v4["complexity"]["correct"] >= v0["complexity"]["correct"] + MARGIN,
          "binaries": v4["binary_total"] >= v0["binary_total"] + MARGIN and v4["binary_posdist"] <= v0["binary_posdist"],
          "frustration": v4["frustration"]["mae"] <= v0["frustration"]["mae"] - 0.10}
    gain4 = sum([v4["intent"]["correct"] - v0["intent"]["correct"] if ko["intent"] else 0,
                 v4["complexity"]["correct"] - v0["complexity"]["correct"] if ko["complexity"] else 0,
                 v4["binary_total"] - v0["binary_total"] if ko["binaries"] else 0])
    notes.append("R4 Korean instructions: intent %d vs %d, complexity %d vs %d, binaries %d vs %d (|pos-exp| %.2f vs %.2f), "
                 "frustration MAE %.3f vs %.3f -> adopt for %s"
                 % (v4["intent"]["correct"], v0["intent"]["correct"], v4["complexity"]["correct"], v0["complexity"]["correct"],
                    v4["binary_total"], v0["binary_total"], v4["binary_posdist"], v0["binary_posdist"],
                    v4["frustration"]["mae"], v0["frustration"]["mae"], [k for k, on in ko.items() if on] or "none"))

    v7 = g("V7_plain_state")
    tot = lambda m: m["intent"]["correct"] + m["complexity"]["correct"] + m["binary_total"]
    gain7 = tot(v7) - tot(v0)
    plain = gain7 >= 3 and v7["frustration"]["mae"] <= v0["frustration"]["mae"] + 0.10
    if plain and any(ko.values()):
        if gain7 > gain4:
            ko = {k: False for k in ko}
        else:
            plain = False
    notes.append("R5 plain state: V7 %d vs V0 %d over intent+complexity+binaries (gain %+d), frustration MAE %.3f -> %s"
                 % (tot(v7), tot(v0), gain7, v7["frustration"]["mae"], "adopt" if plain else "keep {\"message\": ...}"))
    return {"binary_form": form, "intent_desc": intent_desc, "intent4": intent4, "complexity_desc": cx_desc,
            "ko_instructions": ko, "plain_state": plain}, notes


def frac(x, n=30):
    return "%d/%d" % (x, n)


def main():
    M = {}
    for v, model in RUNS:
        if (HERE / ("P0b_%s_%s.json" % (v, model))).exists():
            M[(v, model)] = run_metrics(v, model)
    keys = [k for k in RUNS if k in M]
    label = lambda k: "%s (%s)" % (k[0], "ml" if k[1] == "multilingual" else "en")
    exp_pos = {q: sum(p0["expected"][q] for p0 in P0_ROWS) for q in NOULS}
    maj = lambda labels: Counter(labels).most_common(1)[0][1]

    print("## Summary table (n=30, self-labelled by one ad-hoc labeller, no CI; counts are x/30)\n")
    print("Binary cells: `correct/30 (pred pos k)`. intent of V5 is 4-class (see intent table for the like-for-like "
          "collapsed comparison). ml = multilingual, en = english control.\n")
    print("| variant | intent | complexity | is_urgent | refund_requested | churn_risk | needs_llm | binary Σ /120 | "
          "mean abs(pos-exp) | frustration MAE | level-0 pick (argmax) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    i6 = [p0["expected"]["intent"] for p0 in P0_ROWS]
    print("| baseline / expected | majority %s (4-class %s) | majority %s | %s | %s | %s | %s | always-no %d | - | always-0 %.3f | expected %s |"
          % (frac(maj(i6)), frac(maj([INTENT6_TO_4[x] for x in i6])),
             frac(maj([p0["expected"]["complexity"] for p0 in P0_ROWS])),
             *["always-no %s (exp pos %d)" % (frac(30 - exp_pos[q]), exp_pos[q]) for q in NOULS],
             sum(30 - exp_pos[q] for q in NOULS), fmean(p0["expected"]["frustration"] for p0 in P0_ROWS),
             frac(sum(p0["expected"]["frustration"] == 0 for p0 in P0_ROWS))))
    for k in keys:
        m = M[k]
        print("| %s | %s%s | %s | %s | %s | %s | %s | %d | %.2f | %.3f | %s |" % (
            label(k), frac(m["intent"]["correct"]), " (4-cl)" if m["four"] else "", frac(m["complexity"]["correct"]),
            *["%s (pos %d)" % (frac(m[q]["correct"]), m[q]["pos_pred"]) for q in NOULS],
            m["binary_total"], m["binary_posdist"], m["frustration"]["mae"], frac(m["frustration"]["l0_argmax"])))

    print("\n## Mean answer_confidence per question\n")
    print("| variant | " + " | ".join(QIDS) + " |")
    print("|---|" + "---|" * len(QIDS))
    for k in keys:
        print("| %s | %s |" % (label(k), " | ".join("%.3f" % (M[k][q]["mean_ac"] if q != "frustration"
                                                               else M[k]["frustration"]["mean_ac"]) for q in QIDS)))

    print("\n## Binary detail: TP/FN/FP (expected positives: %s)\n"
          % ", ".join("%s %d" % (q, exp_pos[q]) for q in NOULS))
    print("Post-hoc diagnostics, not part of the V8 rule: balanced accuracy = mean(TPR, TNR), always-no = 0.500. "
          "'above & near' = binaries with accuracy strictly above always-no AND abs(pred pos - exp pos) <= 2 items.\n")
    print("| variant | form | " + " | ".join(NOULS) + " | mean balanced acc | above always-no & near expected |")
    print("|---|---|" + "---|" * len(NOULS) + "---|---|")
    for k in keys:
        m = M[k]
        forms = sorted({m[q]["form"] for q in NOULS})
        ba = fmean((m[q]["tp"] / exp_pos[q] + (30 - exp_pos[q] - m[q]["fp"]) / (30 - exp_pos[q])) / 2 for q in NOULS)
        good = [q for q in NOULS if m[q]["correct"] > 30 - exp_pos[q] and abs(m[q]["pos_pred"] - exp_pos[q]) <= 2]
        print("| %s | %s | %s | %.3f | %s |" % (label(k), "/".join(forms),
                                               " | ".join("%d/%d/%d" % (m[q]["tp"], m[q]["fn"], m[q]["fp"]) for q in NOULS),
                                               ba, ", ".join(good) or "none"))

    print("\n## Intent detail\n")
    print("collapsed-4 = the run's answers and labels mapped refund/billing_question->billing, technical_help->technical, "
          "information/other->other (V5 is natively 4-class). changed vs V0 = items whose answer differs from the same "
          "model's V0 run (V5 compared in the 4-class space).\n")
    print("| variant | intent | collapsed-4 | changed vs V0 | negation rows correct | top-3 confusions (expected→predicted ×n) |")
    print("|---|---|---|---|---|---|")
    for k in keys:
        m = M[k]
        base = M.get(("V0_v1", k[1]))
        if base is None:
            changed = "-"
        elif m["four"]:
            changed = frac(sum(p != INTENT6_TO_4[b] for p, b in zip(m["intent"]["preds"], base["intent"]["preds"])))
        else:
            changed = frac(sum(p != b for p, b in zip(m["intent"]["preds"], base["intent"]["preds"])))
        neg = sum(m["intent"]["preds"][i] == m["intent"]["exps"][i] for i in NEG_ROWS)
        top = ", ".join("%s→%s ×%d" % (e, p, n) for (e, p), n in m["intent"]["top3"])
        print("| %s | %s | %s | %s | %s | %s |" % (label(k), frac(m["intent"]["correct"]), frac(m["intent"]["acc4"]),
                                                   changed, frac(neg, 5), top))

    print("\n## Frustration detail (expected level-0 %s)\n" % frac(M[keys[0]]["frustration"]["l0_exp"]))
    print("| variant | MAE | exact level (argmax) | level-0 pick argmax | level-0 pick round(score) | score range |")
    print("|---|---|---|---|---|---|")
    for k in keys:
        f = M[k]["frustration"]
        print("| %s | %.3f | %s | %s | %s | %.2f-%.2f |" % (label(k), f["mae"], frac(f["exact"]), frac(f["l0_argmax"]),
                                                          frac(f["l0_round"]), f["score_min"], f["score_max"]))

    print("\n## Negation rows (P0 rows 4, 7, 10, 11, 29): false positive on the negated binary target\n")
    print("| variant | " + " | ".join("row %d %s" % (i, SHORT[q]) for i, q in NEG_ROWS.items()) + " | FP total |")
    print("|---|" + "---|" * (len(NEG_ROWS) + 1))
    for k in keys:
        m = M[k]
        cells = ["%s %.2f" % ("FP" if m[q]["pos"][i] else "ok", m[q]["p_true"][i]) for i, q in NEG_ROWS.items()]
        print("| %s | %s | %s |" % (label(k), " | ".join(cells), frac(sum(m[q]["pos"][i] for i, q in NEG_ROWS.items()), 5)))

    print("\n## Per-row intent answers (✗ = wrong; V5 codes B/T/C/O are 4-class)\n")
    print("| # | message | expected | " + " | ".join(label(k) for k in keys) + " |")
    print("|---|---|---|" + "---|" * len(keys))
    for i, p0 in enumerate(P0_ROWS):
        msg = p0["state"]["message"]
        cells = []
        for k in keys:
            m = M[k]
            p, e = m["intent"]["preds"][i], m["intent"]["exps"][i]
            cells.append(code(p, m["four"]) + ("" if p == e else "✗"))
        print("| %d | %s | %s | %s |" % (i, msg if len(msg) <= 22 else msg[:21] + "…", code(p0["expected"]["intent"], False),
                                         " | ".join(cells)))

    print("\n## Per-row binary answers (U=is_urgent R=refund_requested C=churn_risk L=needs_llm; letter = predicted positive)\n")
    print("| # | expected | " + " | ".join(label(k) for k in keys) + " |")
    print("|---|---|" + "---|" * len(keys))
    flags = lambda bits: "".join(SHORT[q] if b else "-" for q, b in zip(NOULS, bits))
    for i, p0 in enumerate(P0_ROWS):
        print("| %d | %s | %s |" % (i, flags([p0["expected"][q] for q in NOULS]),
                                    " | ".join(flags([M[k][q]["pos"][i] for q in NOULS]) for k in keys)))

    print("\n## Sanity checks\n")
    for model in ("multilingual", "english"):
        if ("V0_v1", model) not in M:
            continue
        p0 = json.load(open(HERE / P0_REPORT[model], encoding="utf-8"))
        same = sum(a["answer"] == b["answer"] for a, b in zip(p0["cases"], json.load(
            open(HERE / ("P0b_V0_v1_%s.json" % model), encoding="utf-8"))["cases"]))
        print("- V0 (%s) answers identical to %s: %d/210 cases; questions_sha256 %s"
              % (model, P0_REPORT[model], same, "equal" if p0["config"]["questions_sha256"] == M[("V0_v1", model)]["config"]["questions_sha256"] else "DIFFERENT"))
    for k in keys:
        if k[0] == "V0_v1" or ("V0_v1", k[1]) not in M:
            continue
        m, base = M[k], M[("V0_v1", k[1])]
        if m["plain_state"]:
            print("- %s: state differs from V0 (plain string), no question shared" % label(k))
            continue
        same_q = [q for q in QIDS if m["questions"][q] == base["questions"][q]]
        flips, dmax = 0, 0.0
        for q in same_q:
            for r, b in zip(m["rows"], base["rows"]):
                f, d = answer_delta(r[q]["answer"], b[q]["answer"])
                flips += f
                dmax = max(dmax, d)
        print("- %s: questions identical to V0 %s -> argmax flips %d, max abs(dp) %.4f"
              % (label(k), same_q or "none", flips, dmax))
    pairs = flips = 0
    dmax = 0.0
    for a in keys:
        for b in keys:
            if a >= b or a[1] != b[1] or M[a]["plain_state"] != M[b]["plain_state"]:
                continue
            for q in QIDS:
                if M[a]["questions"][q] != M[b]["questions"][q]:
                    continue
                pairs += 1
                for ra, rb in zip(M[a]["rows"], M[b]["rows"]):
                    f, d = answer_delta(ra[q]["answer"], rb[q]["answer"])
                    flips += f
                    dmax = max(dmax, d)
    print("- every pair of runs (same model, same state form) that shares an identical question definition: "
          "%d (run pair, question) combinations, argmax flips %d, max abs(dp) %.4f" % (pairs, flips, dmax))
    print("- per-qid accuracy / MAE recomputed from cases == report slices.qid for every run (asserted)")

    if all(("%s" % v, "multilingual") in M for v in VARIANTS[:9]):
        choice, notes = select_v8(M)
        print("\n## V8 selection (rule in the analyzer docstring, applied mechanically to the multilingual V0..V7 runs)\n")
        for n in notes:
            print("- " + n)
        print("- selected: %s" % json.dumps(choice, ensure_ascii=False))

    print("\n## Report `overall` (laya-evals aggregates; choice_accuracy pools every choice question of the run, so it "
          "is not comparable across variants whose question types differ; latency fields exist but are not reported)\n")
    print("| run | choice_accuracy | noul_accuracy | score_mae | ece | mean_confidence |")
    print("|---|---|---|---|---|---|")
    for k in keys:
        o = json.load(open(HERE / ("P0b_%s_%s.json" % k), encoding="utf-8"))["overall"]
        print("| %s | %s | %s | %.4f | %.4f | %.4f |" % (
            label(k), "%.4f" % o["choice_accuracy"], "%.4f" % o["noul_accuracy"] if "noul_accuracy" in o else "n/a (no noul)",
            o["score_mae"], o["ece"], o["mean_confidence"]))

    print("\n## Run identity (from each report's config)\n")
    print("| run | report | dataset_sha256 | questions_sha256 | revision |")
    print("|---|---|---|---|---|")
    for k in keys:
        c = M[k]["config"]
        print("| %s | results/poc/P0b_%s_%s.json | %s | %s | %s |" % (label(k), k[0], k[1], c["dataset_sha256"],
                                                                     c["questions_sha256"], ", ".join(c["revisions"].values())))


if __name__ == "__main__":
    main()
