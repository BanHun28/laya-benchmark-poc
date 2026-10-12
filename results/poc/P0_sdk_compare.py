"""P0 device parity (throwaway): compare per-question answers of two P0_sdk_device_run.py outputs.

    .venv/bin/python results/poc/P0_sdk_compare.py results/poc/P0_sdk_mps.json results/poc/P0_sdk_cpu.json

|delta p| is taken over every reported probability: `probabilities` for choice/score, P(true) (`noul`) for noul
(P(false) moves by the same amount). Answers are rounded to 4 decimals by laya, so 1e-4 is the resolution.
"""
import json
import sys


def value(ans):
    return ans.get("choice", ans.get("score", ans.get("noul")))


def argmax(ans):
    if ans["type"] == "noul":
        return ans["noul"] >= 0.5
    probs = ans["probabilities"]
    return max(probs, key=probs.get)


def probs(ans):
    return {"true": ans["noul"]} if ans["type"] == "noul" else ans["probabilities"]


a_rec, b_rec = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])
a, b = a_rec["result"]["answers"], b_rec["result"]["answers"]
la = "%s(%s)" % (a_rec["device"], a_rec["dtype_for_7"].replace("torch.", ""))
lb = "%s(%s)" % (b_rec["device"], b_rec["dtype_for_7"].replace("torch.", ""))
print("| qid | %s value | %s value | argmax %s / %s | same | %s ac / abst | %s ac / abst | max abs dp |" % (la, lb, la, lb, la, lb))
print("|---|---|---|---|---|---|---|---|")
overall, flips = 0.0, 0
for qid in a:
    pa, pb = probs(a[qid]), probs(b[qid])
    dp = max(abs(pa[k] - pb[k]) for k in pa)
    overall = max(overall, dp)
    same = argmax(a[qid]) == argmax(b[qid])
    flips += not same
    print("| %s | %s | %s | %s / %s | %s | %.4f / %s | %.4f / %s | %.4f |" % (
        qid, value(a[qid]), value(b[qid]), argmax(a[qid]), argmax(b[qid]), same,
        a[qid]["answer_confidence"], a[qid]["abstention"], b[qid]["answer_confidence"], b[qid]["abstention"], dp))
print()
print("argmax flips: %d / %d, overall max abs dp: %.4f" % (flips, len(a), overall))
print("abstention_threshold:", {a[q]["abstention_threshold"] for q in a}, {b[q]["abstention_threshold"] for q in b})
print("usage %s:" % la, json.dumps(a_rec["result"]["usage"], ensure_ascii=False))
print("usage %s:" % lb, json.dumps(b_rec["result"]["usage"], ensure_ascii=False))
print("routing key present:", a_rec["has_routing_key"], b_rec["has_routing_key"])
