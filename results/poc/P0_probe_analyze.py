"""P0 zero-shot probe analysis (throwaway). Not poc/service code: decide() below is a verbatim copy of the
05_poc_plan.md:293-310 sketch, run here only to see the action mix on the probe.

    .venv/bin/python results/poc/P0_probe_analyze.py > results/poc/P0_probe_analysis.md

Reads results/poc/P0_probe_sentences.jsonl and the laya-evals reports P0_probe_{multilingual,english}.json.
n=30, self-labelled by one ad-hoc labeller, no CI: every number here is indicative only.
"""
import copy
import json
from collections import Counter
from pathlib import Path
from statistics import fmean

from laya.confidence import apply_confidence_gate

HERE = Path(__file__).resolve().parent
QIDS = ["intent", "is_urgent", "frustration", "refund_requested", "churn_risk", "needs_llm", "complexity"]
NOULS = ["is_urgent", "refund_requested", "churn_risk", "needs_llm"]
INTENTS = ["refund", "technical_help", "billing_question", "information", "cancellation", "other"]

# ---- 05_poc_plan.md:294-310, verbatim
T = {"intent": 0.80, "is_urgent": 0.70, "refund_requested": 0.75, "churn_risk": 0.75}   # 초기값, P3에서 교체
ROUTE = {"refund": "billing", "billing_question": "billing", "technical_help": "tech",
         "cancellation": "retention", "information": "faq", "other": "general"}


def decide(answers):
    intent = answers["intent"]
    if intent.get("abstention") != "passed" or intent["answer_confidence"] < T["intent"]:
        return "HUMAN_REVIEW", "intent below T or gate not evaluated"
    if answers.get("needs_llm", {}).get("noul", 0.0) >= 0.5 \
            or answers.get("complexity", {}).get("choice") == "complex":
        return "FORWARD_LLM", "free-form reply needed"
    urgent = answers["is_urgent"]["noul"] >= 0.5 or answers["frustration"]["score"] >= 2.5
    refund = answers["refund_requested"]["noul"] >= 0.5 and answers["refund_requested"]["answer_confidence"] >= T["refund_requested"]
    churn = answers["churn_risk"]["noul"] >= 0.5 and answers["churn_risk"]["answer_confidence"] >= T["churn_risk"]
    queue = "retention" if churn else ROUTE[intent["choice"]]
    tags = [t for t, on in (("refund", refund), ("churn", churn), ("urgent", urgent)) if on]
    return ("ESCALATE" if urgent else "AUTO_ROUTE"), {"queue": queue, "tags": tags}
# ----


def load_rows():
    rows = []
    for line in (HERE / "P0_probe_sentences.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            rows.append(json.loads(line))
    return rows


def per_row_answers(report, rows):
    """Cases are emitted per example in `expected` order, so consecutive groups of 7 are one row."""
    cases = report["cases"]
    assert len(cases) == len(rows) * len(QIDS), len(cases)
    grouped = []
    for i, row in enumerate(rows):
        group = cases[i * len(QIDS):(i + 1) * len(QIDS)]
        assert [c["qid"] for c in group] == QIDS
        assert all(c["expected"] == row["expected"][c["qid"]] and c["tags"] == row["tags"] for c in group)
        grouped.append({c["qid"]: c["answer"] for c in group})
    return grouped


def level_argmax(ans):
    probs = ans["probabilities"]
    return int(max(probs, key=probs.get))


def metrics(rows, answers):
    out = {}
    for q in ("intent", "complexity"):
        out[q] = {"acc": fmean(a[q]["choice"] == r["expected"][q] for r, a in zip(rows, answers))}
    for q in NOULS:
        out[q] = {"acc": fmean((a[q]["noul"] >= 0.5) == r["expected"][q] for r, a in zip(rows, answers)),
                  "pos_pred": fmean(a[q]["noul"] >= 0.5 for a in answers),
                  "pos_exp": fmean(r["expected"][q] for r in rows)}
    f = [(r["expected"]["frustration"], a["frustration"]) for r, a in zip(rows, answers)]
    out["frustration"] = {"mae": fmean(abs(a["score"] - e) for e, a in f),
                          "exact_argmax": fmean(level_argmax(a) == e for e, a in f),
                          "exact_round": fmean(round(a["score"]) == e for e, a in f),
                          "first_pick_argmax": fmean(level_argmax(a) == 0 for e, a in f),
                          "first_pick_round": fmean(round(a["score"]) == 0 for e, a in f),
                          "first_exp": fmean(e == 0 for e, a in f)}
    for q in QIDS:
        out[q]["mean_ac"] = fmean(a[q]["answer_confidence"] for a in answers)
    return out


def main():
    rows = load_rows()
    ml = json.load(open(HERE / "P0_probe_multilingual.json", encoding="utf-8"))
    en = json.load(open(HERE / "P0_probe_english.json", encoding="utf-8"))
    ans_ml, ans_en = per_row_answers(ml, rows), per_row_answers(en, rows)
    m_ml, m_en = metrics(rows, ans_ml), metrics(rows, ans_en)

    # cross-check against the harness's own per-qid slices
    for m, rep in ((m_ml, ml), (m_en, en)):
        sl = rep["slices"]["qid"]
        for q in ("intent", "complexity"):
            assert abs(sl[q]["choice_accuracy"] - m[q]["acc"]) < 1e-9
        for q in NOULS:
            assert abs(sl[q]["noul_accuracy"] - m[q]["acc"]) < 1e-9
        assert abs(sl["frustration"]["score_mae"] - m["frustration"]["mae"]) < 1e-9

    print("# P0 zero-shot probe analysis (n=30, self-labelled, no CI, indicative only)\n")
    print("dataset_sha256=%s questions_sha256=%s revisions=%s / english revisions=%s\n" % (
        ml["config"]["dataset_sha256"], ml["config"]["questions_sha256"], ml["config"]["revisions"], en["config"]["revisions"]))

    print("## Per-question (multilingual vs english control)\n")
    print("baseline: majority-class accuracy for choice, always-no accuracy for noul, always-level-0 MAE for score.\n")
    print("| qid | metric | multilingual | english | baseline / expected rate | ml mean answer_confidence | en mean answer_confidence |")
    print("|---|---|---|---|---|---|---|")
    for q in QIDS:
        a, b = m_ml[q], m_en[q]
        if q in ("intent", "complexity"):
            majority = Counter(r["expected"][q] for r in rows).most_common(1)[0][1] / len(rows)
            print("| %s | choice_accuracy | %.3f | %.3f | majority %.3f | %.3f | %.3f |" % (q, a["acc"], b["acc"], majority, a["mean_ac"], b["mean_ac"]))
        elif q in NOULS:
            print("| %s | noul_accuracy | %.3f | %.3f | always-no %.3f | %.3f | %.3f |" % (q, a["acc"], b["acc"], 1 - a["pos_exp"], a["mean_ac"], b["mean_ac"]))
            print("| %s | positive rate (p>=0.5) | %.3f | %.3f | expected %.3f | | |" % (q, a["pos_pred"], b["pos_pred"], a["pos_exp"]))
        else:
            always0 = fmean(r["expected"]["frustration"] for r in rows)
            print("| frustration | score_mae | %.3f | %.3f | always-0 %.3f | %.3f | %.3f |" % (a["mae"], b["mae"], always0, a["mean_ac"], b["mean_ac"]))
            print("| frustration | exact level (argmax) | %.3f | %.3f | - | | |" % (a["exact_argmax"], b["exact_argmax"]))
            print("| frustration | exact level (round(score)) | %.3f | %.3f | - | | |" % (a["exact_round"], b["exact_round"]))
            print("| frustration | level-0 pick rate (argmax) | %.3f | %.3f | %.3f | | |" % (a["first_pick_argmax"], b["first_pick_argmax"], a["first_exp"]))
            print("| frustration | level-0 pick rate (round(score)) | %.3f | %.3f | %.3f | | |" % (a["first_pick_round"], b["first_pick_round"], a["first_exp"]))

    print("\n## Intent confusion, multilingual (rows = expected, cols = predicted)\n")
    conf = Counter((r["expected"]["intent"], a["intent"]["choice"]) for r, a in zip(rows, ans_ml))
    print("| expected \\ predicted | " + " | ".join(INTENTS) + " |")
    print("|---|" + "---|" * len(INTENTS))
    for e in INTENTS:
        print("| %s | %s |" % (e, " | ".join(str(conf[(e, p)]) for p in INTENTS)))

    print("\n## Intent confusion, english control\n")
    conf = Counter((r["expected"]["intent"], a["intent"]["choice"]) for r, a in zip(rows, ans_en))
    print("| expected \\ predicted | " + " | ".join(INTENTS) + " |")
    print("|---|" + "---|" * len(INTENTS))
    for e in INTENTS:
        print("| %s | %s |" % (e, " | ".join(str(conf[(e, p)]) for p in INTENTS)))

    # 05 §5: min_confidence = min(T.values()) turns on the abstention states; the probe run had no gate, so
    # apply laya's own gate function to the recorded answers (it only adds fields, never changes an answer).
    gate = min(T.values())
    decisions = []
    for a in ans_ml:
        res = {"answers": copy.deepcopy(a)}
        apply_confidence_gate([res], gate)
        decisions.append(decide(res["answers"]))
    gold = []
    for r in rows:
        e = r["expected"]
        fake = {"intent": {"choice": e["intent"], "answer_confidence": 1.0, "abstention": "passed"},
                "is_urgent": {"noul": float(e["is_urgent"]), "answer_confidence": 1.0},
                "frustration": {"score": float(e["frustration"]), "answer_confidence": 1.0},
                "refund_requested": {"noul": float(e["refund_requested"]), "answer_confidence": 1.0},
                "churn_risk": {"noul": float(e["churn_risk"]), "answer_confidence": 1.0},
                "needs_llm": {"noul": float(e["needs_llm"])}, "complexity": {"choice": e["complexity"]}}
        gold.append(decide(fake))
    print("\n## Policy action distribution (05 §5 decide(), T initial, gate min_confidence=%.2f), multilingual\n" % gate)
    print("| action | multilingual | if answers were the expected labels (reference) |")
    print("|---|---|---|")
    acts = Counter(d[0] for d in decisions)
    gacts = Counter(d[0] for d in gold)
    for act in ("HUMAN_REVIEW", "FORWARD_LLM", "ESCALATE", "AUTO_ROUTE"):
        print("| %s | %d | %d |" % (act, acts[act], gacts[act]))
    abst = Counter(a["intent"]["answer_confidence"] >= gate for a in ans_ml)
    print("\nintent answer_confidence >= gate 0.70: %d/30; >= T_intent 0.80: %d/30" % (
        abst[True], sum(a["intent"]["answer_confidence"] >= T["intent"] for a in ans_ml)))
    wrong_passed = [(i, r["expected"]["intent"], a["intent"]["choice"], a["intent"]["answer_confidence"], d[0])
                    for i, (r, a, d) in enumerate(zip(rows, ans_ml, decisions))
                    if d[0] != "HUMAN_REVIEW" and a["intent"]["choice"] != r["expected"]["intent"]]
    passed = sum(d[0] != "HUMAN_REVIEW" for d in decisions)
    print("rows past the intent gate: %d; of those with wrong intent: %d -> %s" % (passed, len(wrong_passed), wrong_passed))
    print("AUTO_ROUTE/ESCALATE queues/tags:", Counter((d[0], d[1]["queue"], tuple(d[1]["tags"]))
                                                     for d in decisions if isinstance(d[1], dict)))

    print("\n## Per-row answers, multilingual (exp -> pred; noul as p_true; frustration as score/argmax level)\n")
    print("| # | message | intent | urgent | frustr | refund | churn | needs_llm | complexity | action |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for i, (r, a, d) in enumerate(zip(rows, ans_ml, decisions)):
        e = r["expected"]
        msg = r["state"]["message"]
        cell = lambda q: "%s→%.2f" % ("T" if e[q] else "F", a[q]["noul"])
        print("| %d | %s | %s→%s (%.2f) | %s | %s | %s | %s | %s | %s→%s (%.2f) | %s |" % (
            i, msg if len(msg) <= 40 else msg[:38] + "…", e["intent"], a["intent"]["choice"], a["intent"]["answer_confidence"],
            cell("is_urgent"), "%d→%.2f/%d" % (e["frustration"], a["frustration"]["score"], level_argmax(a["frustration"])),
            cell("refund_requested"), cell("churn_risk"), cell("needs_llm"),
            e["complexity"], a["complexity"]["choice"], a["complexity"]["answer_confidence"],
            d[0] if not isinstance(d[1], dict) else "%s %s %s" % (d[0], d[1]["queue"], "+".join(d[1]["tags"]) or "-")))


if __name__ == "__main__":
    main()
