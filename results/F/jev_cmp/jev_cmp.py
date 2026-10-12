"""Jev playground runs for the Laya vs Jev comparison (docs/09_laya_vs_jev_plan.md §4.2, §7). No model call here.

    .venv/bin/python results/F/jev_cmp/jev_cmp.py expect SET [--rows 0,1] [--qids a,b] [--probe]  # payload sha12 per item (precheck)
    .venv/bin/python results/F/jev_cmp/jev_cmp.py record SESSION SET RUN DUMP.json --row R [--qids a,b] [--probe] [--phase explore]
    .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze SESSION[,S2] SET[,SET2,...]      # markdown tables (choice, Boolean or score set; SET,SET2 pooled)
    .venv/bin/python results/F/jev_cmp/jev_cmp.py stability REF_SESSION SESSION SET        # determinism + option-order flips
    .venv/bin/python results/F/jev_cmp/jev_cmp.py t1 S1,S2                                 # T1 mixed types vs Laya (120 decisions)

--probe sends the option order the Laya T2 option-order probe drew for that row (T2_option_order_k1_english.json).

SET is a playground form stem, e.g. T2_ag_news_40 (data/evals/jev_cmp/<SET>_playground.json). Single-question
items send {"state", "questions": {"decision": ...}}; --qids makes a multi-question payload {"q1": ..., "q2": ...}
from the named decisions of one row, built exactly as the playground client does (labels and question trimmed;
choice criteria {label: label}; score criteria = rubric list; boolean has no criteria).
`record` checks the captured request body against that payload byte for byte, appends one line per request
(success or error) to sessions/<SESSION>/<SESSION>_requests.jsonl and to the master jev_runs_all.jsonl, and exits 2
on an error record.
"""
import argparse
import hashlib
import json
import math
import re
import statistics
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from metrics_extra import mcnemar_exact  # noqa: E402

HERE = ROOT / "results/F/jev_cmp"
DATA = ROOT / "data/evals/jev_cmp"
MASTER = HERE / "jev_runs_all.jsonl"
PROBE = HERE / "T2_option_order_k1_english.json"
KST = timezone(timedelta(hours=9))
MIN_GAP_S = 10.0
LAYA_RUNNERS = ("english", "multilingual", "router")
# T9, T10 came with the 3-arm extension: their Laya (vanilla) reports are in results/T3arm/vanilla/, laya/ holds T1-T8 only
LAYA_DIRS = {"T9": ROOT / "results/T3arm/vanilla", "T10": ROOT / "results/T3arm/vanilla"}


def session_dir(session):
    hits = sorted(HERE.glob("sessions/%s_*" % session))
    assert len(hits) == 1, hits
    return hits[0]


def form_file(stem):
    return DATA / ("%s_playground.json" % stem)


def load_items(stem):
    doc = json.loads(form_file(stem).read_text(encoding="utf-8"))
    return doc, doc["items"]


def row_items(items, row, qids=None):
    its = [it for it in items if it["row"] == row]
    if qids:
        by = {it["qid"]: it for it in its}
        its = [by[q] for q in qids]
    assert its and len({it["state_text"] for it in its}) == 1
    return its


def qpayload(it):
    t = {"instructions": it["question"].strip()}
    if it["decision_type"] == "choice":
        return {**t, "type": "choice", "criteria": {o.strip(): o.strip() for o in it["options"]}}
    if it["decision_type"] == "score":
        return {**t, "type": "score", "criteria": [o.strip() for o in it["options"]]}
    return {**t, "type": "boolean"}


def payload(its, multi):
    if multi:
        return {"state": its[0]["state_text"], "questions": {"q%d" % (k + 1): qpayload(it) for k, it in enumerate(its)}}
    assert len(its) == 1
    return {"state": its[0]["state_text"], "questions": {"decision": qpayload(its[0])}}


def canon(p):
    return json.dumps(p, ensure_ascii=False, separators=(",", ":"))


def sha12(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def fmt_pct(p):
    """The playground's formatProbability: `${Number((100*p).toFixed(2))}%`."""
    v = float("%.2f" % (100 * p))
    return ("%d" % v if v == int(v) else repr(v)) + "%"


def key_of(label):
    return label.split(":", 1)[0].strip()


def probe_order(row):
    """The option order the Laya T2 probe drew for this row (random.Random(13), item-major, 1 per item), so Jev gets
    the same permuted input as Laya did (scripts/probe_option_order.py probe_file)."""
    it = next(x for x in json.loads(PROBE.read_text(encoding="utf-8"))["sets"][0]["items"] if x["row"] == row)
    return it["perms"][0]["order"]


def permuted(it, order):
    by = {key_of(o): o for o in it["options"]}
    assert sorted(order) == sorted(by), (order, list(by))
    return dict(it, options=[by[k] for k in order])


def cmd_expect(a):
    _, items = load_items(a.set)
    rows = [int(x) for x in a.rows.split(",")] if a.rows else sorted({it["row"] for it in items})
    qids = a.qids.split(",") if a.qids else None
    for r in rows:
        its = row_items(items, r, qids)
        if a.probe:
            its = [permuted(its[0], probe_order(r))]
        c = canon(payload(its, bool(qids)))
        print("row %2d  %s  sha12 %s  len %d  ids %s%s" % (r, its[0]["id"].split("/")[1], sha12(c), len(c),
                                                           ",".join(it["qid"] for it in its),
                                                           "  order " + " | ".join(its[0]["options"]) if a.probe else ""))


def parse_single_display(text):
    ls = [x.strip() for x in text.splitlines() if x.strip()]
    # a Score card is headed SCORE instead of DECISION (S1 multi_question_mode.md §1 "결과 표시")
    i, j = ls.index("DECISION") if "DECISION" in ls else ls.index("SCORE"), ls.index("Probability distribution")
    probs, k = {}, j + 1
    while k + 1 < len(ls) and re.fullmatch(r"[\d.]+%", ls[k + 1]):
        probs[ls[k]] = ls[k + 1]
        k += 2
    return {"decision": ls[i + 1], "bars": probs}


def expected_view(ans, it):
    """resultView of the playground client for one answer, as display strings."""
    if ans["type"] == "boolean":
        p = ans["probability"]
        dec = "Equally likely" if p == 0.5 else ("Yes" if p > 0.5 else "No")
        return dec, [("Yes", fmt_pct(p)), ("No", fmt_pct(1 - p))]
    if ans["type"] == "choice":
        return ans["choice"], [(o.strip(), fmt_pct(ans["probabilities"][o.strip()])) for o in it["options"]]
    rub = [o.strip() for o in it["options"]]
    # the client picks rubric[Math.round(score)] (half up); Python's round() is half-even (x.50 would differ)
    return rub[math.floor(ans["score"] + 0.5)], [("%d — %s" % (s, t), fmt_pct(ans["probabilities"][str(s)])) for s, t in enumerate(rub)]


def decision_record(ans, it):
    d = {"id": it["id"], "qid": it["qid"], "type": it["decision_type"], "gold": it["gold"]}
    if ans["type"] == "choice":
        pk = {key_of(k): v for k, v in ans["probabilities"].items()}
        d.update(pred=key_of(ans["choice"]), pred_label=ans["choice"], probs=pk, top_p=pk[key_of(ans["choice"])])
        d["correct"] = d["pred"] == it["gold"]
    elif ans["type"] == "boolean":
        p = ans["probability"]
        d.update(pred=p >= 0.5, p_true=p, top_p=max(p, 1 - p))
        d["correct"] = d["pred"] == it["gold"]
    else:
        pk = {k: v for k, v in ans["probabilities"].items()}
        lv = [pk[str(s)] for s in range(len(it["options"]))]
        d.update(score=ans["score"], probs=pk, pred=lv.index(max(lv)), top_p=max(lv),
                 expected_level=sum(s * p for s, p in enumerate(lv)) / max(sum(lv), 1e-12))
        d["correct"] = d["pred"] == it["gold"]
    return d


def append(session, rec):
    line = json.dumps(rec, ensure_ascii=False) + "\n"
    for p in (session_dir(session) / ("%s_requests.jsonl" % session), MASTER):
        with p.open("a", encoding="utf-8") as fh:
            fh.write(line)


def cmd_record(a):
    _, items = load_items(a.set)
    qids = a.qids.split(",") if a.qids else None
    its = row_items(items, a.row, qids)
    order = probe_order(a.row) if a.probe else None
    if order:
        its = [permuted(its[0], order)]
    multi = bool(qids)
    exp = canon(payload(its, multi))
    d = json.loads(Path(a.dump).read_text(encoding="utf-8"))
    if isinstance(d, str):
        d = json.loads(d)
    sdir = session_dir(a.session)
    jl = sdir / ("%s_requests.jsonl" % a.session)
    prev = [json.loads(x) for x in jl.read_text(encoding="utf-8").splitlines()] if jl.exists() else []
    assert not any(p["run"] == a.run for p in prev), "run %d already recorded" % a.run
    bad = []
    chk = lambda ok, msg: ok or bad.append(msg)  # noqa: E731
    click = d["click"]
    calls = [c for c in d["calls"] if c["t0"] >= click - 50]
    perf = [f for f in d["fetches"] if f["start"] >= click - 50]
    chk(len(calls) == 1 and len(perf) == 1, "evaluate calls after click: wrapper %d, resource timing %d" % (len(calls), len(perf)))
    all_clicks = sorted(set(d["clicks"]) | {p["click_epoch_ms"] for p in prev if p["session"] == a.session})
    i = all_clicks.index(click)
    gap = (click - all_clicks[i - 1]) / 1000 if i else None
    chk(gap is None or gap >= MIN_GAP_S, "gap %.2f s < %.0f s" % (gap or 0, MIN_GAP_S))
    body = calls[0]["req_body"] if calls else None
    chk(body == exp, "request body != expected payload (sha12 %s vs %s)" % (sha12(body or ""), sha12(exp)))
    if bad:
        print("NOT RECORDED:\n  " + "\n  ".join(bad))
        sys.exit(1)
    prev_attempts = [p for p in prev if p["set"] == a.set and p["row"] == a.row and p.get("qids") == [it["qid"] for it in its]
                     and p.get("perm") == order]
    omitted = [{"id": it["id"], "qid": it["qid"], "reason": a.omit_reason or it.get("reason") or "not representable"}
               for it in items if it["row"] == a.row and multi and it["qid"] not in qids]
    c = calls[0]
    end = next((s for s in d["status_log"] if s[0] >= click and not s[1].startswith("Running")), None)
    rec = {"session": a.session, "date": sdir.name.split("_", 1)[1], "set": a.set, "task": a.set.split("_")[0],
           "phase": a.phase, "run": a.run, "attempt": len(prev_attempts) + 1, "row": a.row,
           "item_ids": [it["id"] for it in its], "mode": "multi" if multi else "single",
           "qids": [it["qid"] for it in its], "omitted": omitted, "perm": order,
           "click_kst": datetime.fromtimestamp(click / 1000, KST).isoformat(timespec="milliseconds"),
           "click_epoch_ms": click, "gap_from_prev_click_s": gap, "http_status": c.get("status"),
           "fetch_dur_ms": perf[0]["dur"], "fetch_status_rt": perf[0]["status"],
           "wrapper_headers_ms": (c["t1"] - c["t0"]) if c.get("t1") else None,
           "click_to_complete_ms": (end[0] - click) if end else None, "status_text": end[1] if end else d["status_now"],
           "payload_sha12": sha12(exp), "payload_bytes": len(exp.encode()), "payload_exact": True,
           "raw": str(Path(a.dump).resolve().relative_to(ROOT))}
    resp = None
    try:
        resp = json.loads(c.get("resp_text") or "null")
    except ValueError:
        pass
    if c.get("status") != 200 or not (resp or {}).get("ok"):
        rec.update(error=(resp or {}).get("error") if isinstance(resp, dict) else None, resp_text=(c.get("resp_text") or "")[:500],
                   display_error=" | ".join(x.strip() for x in d["text"].splitlines() if x.strip())[:300], decisions=None)
        append(a.session, rec)
        print("run %d row %d ERROR HTTP %s: %s | gap %s s" % (a.run, a.row, c.get("status"), rec["status_text"],
                                                             "-" if gap is None else "%.1f" % gap))
        sys.exit(2)
    res = resp["result"]
    ids = list(json.loads(exp)["questions"])
    decs, disp_ok = [], []
    text = d["text"]
    for qi, it in zip(ids, its):
        ans = res["answers"][qi]
        decs.append(decision_record(ans, it))
        dec, bars = expected_view(ans, it)
        if multi:
            card = text.split("Question %d" % (ids.index(qi) + 1), 1)[1]
            nxt = "Question %d" % (ids.index(qi) + 2)
            card = card.split(nxt, 1)[0] if nxt in card else card
            pos, ok = card.find(dec), True
            for lab, pct in bars:
                pos = card.find(lab, max(pos, 0))
                q = card.find(pct, pos)
                ok &= pos >= 0 and q >= 0
                pos = q
            disp_ok.append(ok and dec in card)
        else:
            sv = parse_single_display(text)
            disp_ok.append(sv["decision"] == dec and list(sv["bars"].items()) == bars)
        if ans["type"] == "score":  # the card's "<score> / <max level>" line, JS number formatting
            s = ans["score"]
            st = "%s / %d" % ("%d" % s if s == int(s) else repr(s), len(it["options"]) - 1)
            disp_ok[-1] = disp_ok[-1] and st in (card if multi else text)
            decs[-1]["shown_score"] = st
        decs[-1].update(shown=dec, shown_pct=[p for _, p in bars], shown_ok=disp_ok[-1])
    m = re.search(r"([\d,]+) ms · server \+ network", text)
    shown_ms = int(m.group(1).replace(",", "")) if m else None
    mid = re.search(r"Model ID(.*?)Input tokens", d["full_text"])
    rec.update(displayed_ms=shown_ms, latency_ms_response=resp.get("latencyMs"), model=resp.get("model"),
               model_id_details=mid.group(1) if mid else None, usage=res.get("usage"), rounding=res.get("rounding"),
               confidence=res.get("confidence"), warnings=res.get("warnings"), display_matches_response=all(disp_ok),
               decisions=decs)
    append(a.session, rec)
    print("run %d row %d %s | %s | shown %s ms, latencyMs %s, fetch %d ms, click->done %s ms | gap %s s | display ok %s | %s" % (
        a.run, a.row, rec["click_kst"][11:23],
        "; ".join("%s=%s%s(%.2f)" % (x["qid"], x["pred"], "" if x["correct"] else "X", x["top_p"]) for x in decs),
        shown_ms, resp.get("latencyMs"), perf[0]["dur"], rec["click_to_complete_ms"], "-" if gap is None else "%.1f" % gap,
        rec["display_matches_response"], rec["model_id_details"]))
    if not rec["display_matches_response"]:
        print("WARNING: displayed values differ from the response")


def wilson(k, n, z=1.96):
    if not n:
        return (float("nan"),) * 2
    p, dd = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / dd, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / dd
    return max(0.0, c - h), min(1.0, c + h)


def ece(conf, corr, bins=15):  # results/F/jev_cmp/laya_summary.py ece_score (bench_local.py:114-123)
    e = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        s = [(c, y) for c, y in zip(conf, corr) if (c >= lo if b == 0 else c > lo) and c <= hi]
        if s:
            e += len(s) / len(conf) * abs(sum(c for c, _ in s) / len(s) - sum(y for _, y in s) / len(s))
    return e


def mmm(xs):
    xs = [x for x in xs if x is not None]
    return "%g / %g / %g" % (statistics.median(xs), min(xs), max(xs)) if xs else "-"


def laya_report(stem, runner):
    return LAYA_DIRS.get(stem.split("_")[0], HERE / "laya") / ("%s_%s.json" % (stem, runner))


def laya_cases(stem, runner, items):
    rep = json.loads(laya_report(stem, runner).read_text(encoding="utf-8"))
    doc = json.loads(form_file(stem).read_text(encoding="utf-8"))
    assert rep["config"]["dataset_sha256"] == doc["dataset_sha256"], (stem, runner)
    assert len(rep["cases"]) == len(items)
    out = {}
    for c, it in zip(rep["cases"], items):
        assert c["qid"] == it["qid"] and c["expected"] == it["gold"] and "id:" + it["id"].split("/")[1] in c["tags"], it["id"]
        out[it["id"]] = c
    return rep, out


def cmd_analyze(a):
    stems = a.set.split(",")  # comma-separated sets are pooled (T7 en,de: same ids and option lists per row)
    items = [it for s in stems for it in load_items(s)[1]]
    # comma-separated sessions are read together (T7 en, de ran in S4 and ja, zh-CN, ko in S5)
    recs = [json.loads(x) for s in a.session.split(",")
            for x in (session_dir(s) / ("%s_requests.jsonl" % s)).read_text(encoding="utf-8").splitlines()]
    recs = [r for r in recs if r["set"] in stems]
    ok = [r for r in recs if r.get("decisions") and r["phase"] == "main"]
    by_id = {}
    for r in ok:
        for dct in r["decisions"]:
            by_id[dct["id"]] = (r, dct)
    its = [it for it in items if it["id"] in by_id]
    ikeys = lambda it: [key_of(o) for o in it["options"]]  # noqa: E731
    keys = ikeys(items[0]) if len({tuple(ikeys(it)) for it in items}) == 1 else None  # None: options drawn per row (T4, T7)
    L = []
    w = L.append
    laya = {}
    for m in LAYA_RUNNERS:
        parts = [laya_cases(s, m, load_items(s)[1]) for s in stems]
        laya[m] = ([rep for rep, _ in parts], {k: c for _, cs in parts for k, c in cs.items()})
    if items[0]["decision_type"] in ("boolean", "score"):
        typed = boolean_lines if items[0]["decision_type"] == "boolean" else score_lines
        print("\n".join(typed(its, by_id, laya) + latency_lines([by_id[i["id"]][0] for i in its])
                        + request_lines(recs, laya, stems)))
        return
    jp = {it["id"]: by_id[it["id"]][1]["pred"] for it in its}
    w("### Accuracy on the same %d items (Jev-completed)\n" % len(its))
    w("| system | correct / n | accuracy | Wilson 95% CI | Brier | ECE (15 bins) | mean top p |")
    w("|---|---|---|---|---|---|---|")
    def brier(pr, it):
        return sum((pr.get(k, 0.0) - (k == it["gold"])) ** 2 for k in ikeys(it))
    rows = []
    jtop = [by_id[it["id"]][1]["top_p"] for it in its]
    jcor = [jp[it["id"]] == it["gold"] for it in its]
    rows.append(("Jev (playground, displayed p, 2-dec rounding)", sum(jcor), jtop, jcor,
                 [brier(by_id[it["id"]][1]["probs"], it) for it in its]))
    for m in LAYA_RUNNERS:
        cs = laya[m][1]
        cor = [cs[it["id"]]["answer"]["choice"] == it["gold"] for it in its]
        conf = [cs[it["id"]]["answer"]["answer_confidence"] for it in its]
        rows.append(("Laya %s" % m, sum(cor), conf, cor, [brier(cs[it["id"]]["answer"]["probabilities"], it) for it in its]))
    for name, k, conf, cor, br in rows:
        lo, hi = wilson(k, len(its))
        w("| %s | %d/%d | %.3f | [%.3f, %.3f] | %.3f | %.3f | %.3f |" % (name, k, len(its), k / len(its), lo, hi,
                                                                     sum(br) / len(br), ece(conf, cor), sum(conf) / len(conf)))
    w("\n### Agreement and exact McNemar (b = Jev right & Laya wrong, c = Jev wrong & Laya right)\n")
    w("| pair | n | same label | b | c | exact McNemar p |")
    w("|---|---|---|---|---|---|")
    for m in LAYA_RUNNERS:
        cs = laya[m][1]
        lp = {it["id"]: cs[it["id"]]["answer"]["choice"] for it in its}
        b = sum(jp[i["id"]] == i["gold"] and lp[i["id"]] != i["gold"] for i in its)
        c = sum(jp[i["id"]] != i["gold"] and lp[i["id"]] == i["gold"] for i in its)
        w("| Jev vs Laya %s | %d | %d | %d | %d | %.4f |" % (m, len(its), sum(jp[i["id"]] == lp[i["id"]] for i in its), b, c,
                                                         mcnemar_exact(b, c)))
    if len(stems) >= 2:
        L += crosslang_lines(stems, its, {"Jev": jp, **{"Laya " + m: {i["id"]: laya[m][1][i["id"]]["answer"]["choice"] for i in its}
                                                        for m in LAYA_RUNNERS}})
    if keys:
        w("\n### Per class (gold) correct\n")
        w("| gold | n | Jev | %s |" % " | ".join("Laya %s" % m for m in LAYA_RUNNERS))
        w("|---|---|---|%s" % ("---|" * len(LAYA_RUNNERS)))
        for k in keys:
            g = [it for it in its if it["gold"] == k]
            w("| %s | %d | %d | %s |" % (k, len(g), sum(jp[i["id"]] == k for i in g), " | ".join(
                "%d" % sum(laya[m][1][i["id"]]["answer"]["choice"] == k for i in g) for m in LAYA_RUNNERS)))
        w("\n### Jev confusion (rows gold, columns Jev)\n")
        w("| gold \\ Jev | %s |" % " | ".join(keys))
        w("|---|%s" % ("---|" * len(keys)))
        for k in keys:
            w("| %s | %s |" % (k, " | ".join("%d" % sum(i["gold"] == k and jp[i["id"]] == p for i in its) for p in keys)))
    else:  # every row has its own option set, so confusions are listed instead of a matrix
        preds = {"Jev": jp, **{"Laya " + m: {i["id"]: laya[m][1][i["id"]]["answer"]["choice"] for i in its} for m in LAYA_RUNNERS}}
        w("\n### Confusions (options differ per row): wrong gold -> pred pairs\n")
        w("| system | wrong | gold -> pred (count if > 1) | most frequent wrong label |")
        w("|---|---|---|---|")
        for s, pr in preds.items():
            bad = Counter((i["gold"], pr[i["id"]]) for i in its if pr[i["id"]] != i["gold"])
            lab = Counter(p for (_, p), n in bad.items() for _ in range(n)).most_common(1)
            w("| %s | %d | %s | %s |" % (s, sum(bad.values()), "; ".join("%s -> %s%s" % (g, p, " x%d" % n if n > 1 else "")
                                                                         for (g, p), n in bad.most_common()) or "-",
                                         "%s (%d)" % lab[0] if lab else "-"))
    w("\n### Jev confidence behaviour (displayed %; 2-decimal rounding)\n")
    tops = [100 * by_id[i["id"]][1]["top_p"] for i in its]
    right = [t for t, y in zip(tops, jcor) if y]
    wrong = [t for t, y in zip(tops, jcor) if not y]
    cells = [100 * v for i in its for v in by_id[i["id"]][1]["probs"].values()]
    pc = [by_id[i["id"]][0]["confidence"].get("decision") for i in its if (by_id[i["id"]][0].get("confidence") or {}).get("decision") is not None]
    pcr = [by_id[i["id"]][0]["confidence"]["decision"] for i, y in zip(its, jcor) if y and (by_id[i["id"]][0].get("confidence") or {}).get("decision") is not None]
    pcw = [by_id[i["id"]][0]["confidence"]["decision"] for i, y in zip(its, jcor) if not y and (by_id[i["id"]][0].get("confidence") or {}).get("decision") is not None]
    f1 = lambda xs: "%.1f" % (sum(xs) / len(xs)) if xs else "-"  # noqa: E731
    f3 = lambda xs: "%.3f" % (sum(xs) / len(xs)) if xs else "-"  # noqa: E731
    w("| runs | top = 100% | runs with any 0% option | 0% cells / all | mean top % (right / wrong) | wrong with top >= 90% "
      "| gold option shown 0% | provider confidence mean (right / wrong) |")
    w("|---|---|---|---|---|---|---|---|")
    g0 = sum(by_id[i["id"]][1]["probs"][i["gold"]] == 0 for i in its)
    w("| %d | %d (%.0f%%) | %d | %d/%d | %s (%s / %s) | %d/%d | %d | %s (%s / %s) |" % (
        len(its), sum(t == 100 for t in tops), 100 * sum(t == 100 for t in tops) / len(tops),
        sum(any(v == 0 for v in by_id[i["id"]][1]["probs"].values()) for i in its), sum(v == 0 for v in cells), len(cells),
        f1(tops), f1(right), f1(wrong), sum(t >= 90 for t in wrong), len(wrong), g0, f3(pc), f3(pcr), f3(pcw)))
    for m in LAYA_RUNNERS:
        cs = laya[m][1]
        conf = [cs[i["id"]]["answer"]["answer_confidence"] for i in its]
        cor = [cs[i["id"]]["answer"]["choice"] == i["gold"] for i in its]
        r_ = [c for c, y in zip(conf, cor) if y]
        w_ = [c for c, y in zip(conf, cor) if not y]
        w("\nLaya %s answer_confidence mean right / wrong: %s / %s; wrong with p >= 0.90: %d/%d" % (
            m, f3(r_), f3(w_), sum(c >= 0.9 for c in w_), len(w_)))
    L += latency_lines([by_id[i["id"]][0] for i in its])
    w("\n### Per item\n")
    w("| # | row | id | gold | Jev (top %%) | %s |" % " | ".join("Laya %s (p)" % m for m in LAYA_RUNNERS))
    w("|---|---|---|---|---|%s" % ("---|" * len(LAYA_RUNNERS)))
    for n, i in enumerate(its, 1):
        dct = by_id[i["id"]][1]
        cells = []
        for m in LAYA_RUNNERS:
            an = laya[m][1][i["id"]]["answer"]
            cells.append("%s %s (%.2f)" % ("O" if an["choice"] == i["gold"] else "X", an["choice"], an["answer_confidence"]))
        w("| %d | %d | %s | %s | %s %s (%g%%) | %s |" % (n, i["row"], i["id"].split("/")[1], i["gold"],
                                                       "O" if dct["correct"] else "X", dct["pred"], 100 * dct["top_p"], " | ".join(cells)))
    L += request_lines(recs, laya, stems)
    print("\n".join(L))


def latency_lines(rr):
    return ["\n### Jev latency (ms, successful runs) and tokens\n",
            "| runs | displayed 'server + network' median / min / max | response latencyMs median / min / max "
            "| browser POST (resource timing) median / min / max | click -> complete median / min / max | input tokens | output tokens | model |",
            "|---|---|---|---|---|---|---|---|",
            "| %d | %s | %s | %s | %s | %s | %s | %s |" % (
                len(rr), mmm([r["displayed_ms"] for r in rr]), mmm([r["latency_ms_response"] for r in rr]),
                mmm([r["fetch_dur_ms"] for r in rr]), mmm([r["click_to_complete_ms"] for r in rr]),
                mmm([(r["usage"] or {}).get("inputTokens") for r in rr]), mmm([(r["usage"] or {}).get("outputTokens") for r in rr]),
                ", ".join("`%s` x%d" % kv for kv in sorted(Counter(r["model_id_details"] for r in rr).items())))]


def request_lines(recs, laya, stems):
    gaps = [r["gap_from_prev_click_s"] for r in recs if r["gap_from_prev_click_s"] is not None]
    return ["\n### Requests (this set, this session)\n",
            "Total %d: HTTP 200 %d, other %d; attempts > 1: %d; click gap min / median %s / %s s.\n" % (
                len(recs), sum(r["http_status"] == 200 for r in recs), sum(r["http_status"] != 200 for r in recs),
                sum(r["attempt"] > 1 for r in recs), "%.1f" % min(gaps) if gaps else "-", "%.1f" % statistics.median(gaps) if gaps else "-")] + [
        "Laya %s report: %s (dataset_sha256 %s)" % (m, laya_report(s, m).relative_to(ROOT), rep["config"]["dataset_sha256"][:16])
        + ("; answered by %s" % dict(Counter(c["model"] for c in rep["cases"])) if m == "router" else "")
        for m in LAYA_RUNNERS for s, rep in zip(stems, laya[m][0])]


def crosslang_lines(stems, its, preds):
    """Two pooled sets with the same ids (T7 en, de): per system, the same label for an id in both languages, and where
    each language is right. More than two sets: crosslang_multi."""
    by = {}
    for i in its:
        by.setdefault(i["id"].split("/", 1)[1], {})[i["id"].split("/", 1)[0]] = i
    if len(stems) > 2:
        return crosslang_multi(stems, [[v[s] for s in stems] for v in by.values() if len(v) == len(stems)], preds)
    pairs = [(v[stems[0]], v[stems[1]]) for v in by.values() if len(v) == 2]
    a, b = (s.rsplit("_", 2)[1] for s in stems)
    L = ["\n### Cross-language: the same id in %s and %s (%d pairs, same gold and options)\n" % (a, b, len(pairs)),
         "| system | same label in both | both right | %s only right | %s only right | both wrong |" % (a, b), "|---|---|---|---|---|---|"]
    for s, pr in preds.items():
        ok = [(pr[x["id"]] == x["gold"], pr[y["id"]] == y["gold"]) for x, y in pairs]
        L.append("| %s | %d | %d | %d | %d | %d |" % (s, sum(pr[x["id"]] == pr[y["id"]] for x, y in pairs), ok.count((True, True)),
                                                    ok.count((True, False)), ok.count((False, True)), ok.count((False, False))))
    return L


def crosslang_multi(stems, groups, preds):
    """Three or more pooled sets with the same ids (T7 en, de, ja, zh-CN, ko); groups = per id, its items in stem order.
    Per-language accuracy, the language penalty against the first set, exact McNemar per language, and cross-language
    consistency (the same label for an id across languages)."""
    langs = [s.rsplit("_", 2)[1] for s in stems]
    n, K = len(groups), len(stems)
    ok = {s: [[pr[x["id"]] == x["gold"] for x in g] for g in groups] for s, pr in preds.items()}
    lab = {s: [[pr[x["id"]] for x in g] for g in groups] for s, pr in preds.items()}
    cnt = {s: [sum(o[k] for o in ok[s]) for k in range(K)] for s in preds}
    acc = {s: [c / n for c in cnt[s]] for s in preds}
    L = ["\n### Cross-language: the same %d ids in %s (same gold and options per id; the same ids repeat across languages, "
         "so pooled tests are not independent)\n" % (n, ", ".join(langs)),
         "| system | %s | pooled |" % " | ".join(langs), "|---|%s---|" % ("---|" * K)]
    for s in preds:
        L.append("| %s | %s | %d/%d = %.3f |" % (s, " | ".join("%d/%d = %.3f" % (c, n, c / n) for c in cnt[s]), sum(cnt[s]), n * K,
                                                 sum(cnt[s]) / (n * K)))
    L += ["\n### Language penalty: accuracy(lang) - accuracy(%s)\n" % langs[0],
          "| system | %s | mean |" % " | ".join(langs[1:]), "|---|%s---|" % ("---|" * (K - 1))]
    for s in preds:
        d = [a - acc[s][0] for a in acc[s][1:]]
        L.append("| %s | %s | %+.3f |" % (s, " | ".join("%+.3f" % x for x in d), sum(d) / len(d)))
    jn = next(iter(preds))
    L += ["\n### Exact McNemar per language (b = Jev right & Laya wrong, c = Jev wrong & Laya right)\n",
          "| pair | %s |" % " | ".join(langs), "|---|%s" % ("---|" * K)]
    for s in list(preds)[1:]:
        bc = [(sum(u[k] and not v[k] for u, v in zip(ok[jn], ok[s])), sum(v[k] and not u[k] for u, v in zip(ok[jn], ok[s]))) for k in range(K)]
        L.append("| %s vs %s | %s |" % (jn, s, " | ".join("%d / %d, p %.4f" % (b, c, mcnemar_exact(b, c)) for b, c in bc)))
    pairs = [(u, v) for u in range(K) for v in range(u + 1, K)]
    L += ["\n### Cross-language consistency: the same label for the same id\n",
          "| system | %s | same label in all %d | mean pairwise agreement (%d language pairs) | right in all %d | wrong in all %d |" % (
              " | ".join("same as %s: %s" % (langs[0], x) for x in langs[1:]), K, len(pairs), K, K),
          "|---|%s---|---|---|---|" % ("---|" * (K - 1))]
    for s in preds:
        g = lab[s]
        L.append("| %s | %s | %d/%d | %.3f | %d | %d |" % (
            s, " | ".join("%d/%d" % (sum(x[0] == x[k] for x in g), n) for k in range(1, K)), sum(len(set(x)) == 1 for x in g), n,
            sum(x[u] == x[v] for x in g for u, v in pairs) / (n * len(pairs)), sum(all(o) for o in ok[s]), sum(not any(o) for o in ok[s])))
    L += ["\n### Per id: right (O) / wrong (X) in %s, and the number of distinct labels across languages\n" % " ".join(langs),
          "| row | id | gold | %s |" % " | ".join(preds), "|---|---|---|%s" % ("---|" * len(preds))]
    for k, gr in enumerate(groups):
        L.append("| %d | %s | %s | %s |" % (gr[0]["row"], gr[0]["id"].split("/")[1], gr[0]["gold"], " | ".join(
            "%s (%d)" % ("".join("O" if o else "X" for o in ok[s][k]), len(set(lab[s][k]))) for s in preds)))
    return L


def score_lines(its, by_id, laya, n_boot=2000, seed=13):
    """Score sets (ordered levels, T6). Primary: argmax-level accuracy (ties -> lowest level, as np.argmax). Secondary: the
    level nearest to E[level], half up (the playground's displayed SCORE, rubric[Math.round(score)]). E[level] is Jev's
    response `score` (2-dec) and Laya's answer.score; MAE and signed error against the gold level, within 1 = |E - gold| <= 1
    (laya_summary.py). Brier = sum over the levels of (p - onehot)^2; ECE on the argmax p."""
    import random
    K = len(its[0]["options"])
    y = [i["gold"] for i in its]
    near = lambda e: math.floor(e + 0.5)  # noqa: E731
    jd = [by_id[i["id"]][1] for i in its]
    P = {"Jev (playground, displayed p, 2-dec)": ([[d["probs"][str(k)] for k in range(K)] for d in jd], [d["score"] for d in jd]),
         **{"Laya " + m: ([[laya[m][1][i["id"]]["answer"]["probabilities"][str(k)] for k in range(K)] for i in its],
                          [laya[m][1][i["id"]]["answer"]["score"] for i in its]) for m in LAYA_RUNNERS}}
    A = {s: [p.index(max(p)) for p in ps] for s, (ps, _) in P.items()}
    R = {s: [near(e) for e in es] for s, (_, es) in P.items()}
    rng = random.Random(seed)
    idx = [[rng.randrange(len(y)) for _ in y] for _ in range(n_boot)]

    def pct(xs):
        v = sorted(xs)
        return v[round(0.025 * (len(v) - 1))], v[round(0.975 * (len(v) - 1))]
    cell = lambda k: "%d/%d = %.3f [%.3f, %.3f]" % ((k, len(y), k / len(y)) + wilson(k, len(y)))  # noqa: E731
    L = ["### Accuracy and error on the same %d items (gold levels %s)\n" % (len(y), dict(sorted(Counter(y).items()))),
         "| system | argmax level correct [Wilson 95%] | rounded E[level] correct [Wilson 95%] | MAE of E[level] | mean E - gold "
         "| within 1 level | Brier (5 levels) | ECE (15 bins, argmax p) | mean top p | argmax != rounded E |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for s, (ps, es) in P.items():
        top = [max(p) for p in ps]
        cor = [a == g for a, g in zip(A[s], y)]
        L.append("| %s | %s | %s | %.3f | %+.3f | %.3f | %.3f | %.3f | %.3f | %d |" % (
            s, cell(sum(cor)), cell(sum(r == g for r, g in zip(R[s], y))), sum(abs(e - g) for e, g in zip(es, y)) / len(y),
            sum(e - g for e, g in zip(es, y)) / len(y), sum(abs(e - g) <= 1 for e, g in zip(es, y)) / len(y),
            sum(sum((p[k] - (k == g)) ** 2 for k in range(K)) for p, g in zip(ps, y)) / len(y), ece(top, cor), sum(top) / len(top),
            sum(a != r for a, r in zip(A[s], R[s]))))
    jn = next(iter(P))
    L += ["\n### Agreement, exact McNemar (b = Jev right & Laya wrong, c = Jev wrong & Laya right), paired MAE difference\n",
          "| pair | n | same argmax | argmax b / c | argmax McNemar p | rounded-E b / c | rounded-E McNemar p "
          "| MAE Jev - Laya [paired bootstrap 95%] |", "|---|---|---|---|---|---|---|---|"]
    ae = {s: [abs(e - g) for e, g in zip(es, y)] for s, (_, es) in P.items()}
    for s in list(P)[1:]:
        bc = []
        for pr in (A, R):
            bc += [sum(u == g and v != g for u, v, g in zip(pr[jn], pr[s], y)), sum(u != g and v == g for u, v, g in zip(pr[jn], pr[s], y))]
        d = [sum(ae[jn][k] - ae[s][k] for k in ix) / len(ix) for ix in idx]
        L.append("| Jev vs %s | %d | %d | %d / %d | %.4f | %d / %d | %.4f | %+.3f [%+.3f, %+.3f] |" % (
            (s, len(y), sum(u == v for u, v in zip(A[jn], A[s])), bc[0], bc[1], mcnemar_exact(bc[0], bc[1]), bc[2], bc[3],
             mcnemar_exact(bc[2], bc[3]), (sum(ae[jn]) - sum(ae[s])) / len(y)) + pct(d)))
    L += ["\n### Predicted level distribution (first level = 0, last level = %d)\n" % (K - 1),
          "| system | rule | %s | first-level picks | last-level picks |" % " | ".join("level %d" % k for k in range(K)),
          "|---|---|%s---|---|" % ("---|" * K),
          "| gold | - | %s | %d | %d |" % (" | ".join("%d" % y.count(k) for k in range(K)), y.count(0), y.count(K - 1))]
    for s in P:
        for rule, pr in (("argmax", A[s]), ("rounded E", R[s])):
            L.append("| %s | %s | %s | %d | %d |" % (s, rule, " | ".join("%d" % pr.count(k) for k in range(K)), pr.count(0), pr.count(K - 1)))
    L += ["\n### Per gold level: argmax correct (mean E[level])\n",
          "| gold level | n | %s |" % " | ".join(P), "|---|---|%s" % ("---|" * len(P))]
    for g in range(K):
        ks = [k for k, v in enumerate(y) if v == g]
        L.append("| %d | %d | %s |" % (g, len(ks), " | ".join("%d (%.2f)" % (sum(A[s][k] == g for k in ks), sum(P[s][1][k] for k in ks) / len(ks))
                                                            for s in P)))
    for s in (jn, "Laya english"):
        L += ["\n### Confusion, argmax level: %s (rows gold, columns predicted)\n" % s,
              "| gold \\ pred | %s |" % " | ".join("%d" % k for k in range(K)), "|---|%s" % ("---|" * K)]
        L += ["| %d | %s |" % (g, " | ".join("%d" % sum(v == g and a == k for v, a in zip(y, A[s])) for k in range(K))) for g in range(K)]
    ps, es = P[jn]
    cor = [a == g for a, g in zip(A[jn], y)]
    top = [max(p) for p in ps]
    pc = [(by_id[i["id"]][0].get("confidence") or {}).get("decision") for i in its]
    f3 = lambda xs: "%.3f" % (sum(xs) / len(xs)) if xs else "-"  # noqa: E731
    L += ["\n### Jev confidence behaviour (displayed %; 2-decimal rounding)\n",
          "| runs | top = 100% | argmax ties | mean top p (right / wrong) | wrong with top >= 0.90 | gold level shown 0% "
          "| provider confidence mean (right / wrong) | max abs(`score` - sum k p_k) |", "|---|---|---|---|---|---|---|---|",
          "| %d | %d | %d | %s (%s / %s) | %d/%d | %d | %s (%s / %s) | %.3f |" % (
              len(y), sum(t == 1 for t in top), sum(p.count(max(p)) > 1 for p in ps), f3(top), f3([t for t, c in zip(top, cor) if c]),
              f3([t for t, c in zip(top, cor) if not c]), sum(t >= 0.9 and not c for t, c in zip(top, cor)), cor.count(False),
              sum(p[g] == 0 for p, g in zip(ps, y)), f3([x for x in pc if x is not None]),
              f3([x for x, c in zip(pc, cor) if c and x is not None]), f3([x for x, c in zip(pc, cor) if not c and x is not None]),
              max(abs(e - sum(k * v for k, v in enumerate(p))) for p, e in zip(ps, es)))]
    for m in LAYA_RUNNERS:
        s = "Laya " + m
        t = [max(p) for p in P[s][0]]
        c = [a == g for a, g in zip(A[s], y)]
        L.append("\n%s argmax p mean right / wrong: %s / %s; wrong with p >= 0.90: %d/%d" % (
            s, f3([x for x, k in zip(t, c) if k]), f3([x for x, k in zip(t, c) if not k]), sum(x >= 0.9 and not k for x, k in zip(t, c)),
            c.count(False)))
    L += ["\n### Per item (argmax level / E[level]; X = argmax wrong; Jev p for levels 0..%d)\n" % (K - 1),
          "| # | row | id | gold | Jev p | %s |" % " | ".join(P), "|---|---|---|---|---|%s" % ("---|" * len(P))]
    for n, i in enumerate(its, 1):
        L.append("| %d | %d | %s | %d | %s | %s |" % (n, i["row"], i["id"].split("/")[1], y[n - 1], " ".join("%.2f" % v for v in ps[n - 1]),
                                                   " | ".join("%d%s / %.2f" % (A[s][n - 1], "" if A[s][n - 1] == y[n - 1] else " X", P[s][1][n - 1])
                                                              for s in P)))
    return L


def auroc(s, y):
    """P(score of a positive > score of a negative), ties counted half (Mann-Whitney U, as scripts/calibrate_ko.py auroc)."""
    pos, neg = [x for x, t in zip(s, y) if t], [x for x, t in zip(s, y) if not t]
    return sum((p > q) + 0.5 * (p == q) for p in pos for q in neg) / (len(pos) * len(neg)) if pos and neg else float("nan")


def boolean_lines(its, by_id, laya, n_boot=2000, seed=13):
    """Boolean sets (Jev Boolean vs Laya noul): pred = p(true) >= 0.5 (laya-evals rule); Brier = sum over {false, true} of
    (p - onehot)^2 as laya_summary.py; ECE on max(p, 1 - p); AUROC of p(true) with a percentile bootstrap over items; the
    in-sample best threshold is descriptive only (chosen on the same items)."""
    import random
    y = [bool(i["gold"]) for i in its]
    P = {"Jev (playground, displayed p, 2-dec)": [by_id[i["id"]][1]["p_true"] for i in its],
         **{"Laya " + m: [laya[m][1][i["id"]]["answer"]["noul"] for i in its] for m in LAYA_RUNNERS}}
    rng = random.Random(seed)
    idx = [[rng.randrange(len(y)) for _ in y] for _ in range(n_boot)]
    boot = {s: [auroc([p[k] for k in ix], [y[k] for k in ix]) for ix in idx] for s, p in P.items()}

    def pct(xs):
        v = sorted(x for x in xs if x == x)  # NaN = a resample without both classes
        return v[round(0.025 * (len(v) - 1))], v[round(0.975 * (len(v) - 1))]
    cor ={s: [(v >= 0.5) == t for v, t in zip(p, y)] for s, p in P.items()}
    L = ["### Accuracy on the same %d items (Jev-completed; pred = p(true) >= 0.5; gold true %d)\n" % (len(its), sum(y)),
         "| system | correct / n | accuracy | Wilson 95% CI | predicted true | Brier | ECE (15 bins) | mean top p "
         "| AUROC p(true) [bootstrap 95%] | in-sample best-threshold accuracy (p(true) >= t) |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for s, p in P.items():
        k, top = sum(cor[s]), [max(v, 1 - v) for v in p]
        thr = sorted(set(p)) + [float("inf")]
        acc = [sum((v >= t) == g for v, g in zip(p, y)) for t in thr]
        best = [t for t, n in zip(thr, acc) if n == max(acc)]
        L.append("| %s | %d/%d | %.3f | [%.3f, %.3f] | %d | %.3f | %.3f | %.3f | %.3f [%.3f, %.3f] | %d/%d = %.3f (t %s) |" % (
            (s, k, len(y), k / len(y)) + wilson(k, len(y)) + (sum(v >= 0.5 for v in p), sum(2 * (v - g) ** 2 for v, g in zip(p, y)) / len(y),
                                                               ece(top, cor[s]), sum(top) / len(top), auroc(p, y)) + pct(boot[s])
            + (max(acc), len(y), max(acc) / len(y), "%g" % best[0] if len(best) == 1 else "%g..%g" % (best[0], best[-1]))))
    jn = next(iter(P))
    L += ["\n### Agreement, exact McNemar (b = Jev right & Laya wrong, c = Jev wrong & Laya right), paired AUROC difference\n",
          "| pair | n | same prediction | b | c | exact McNemar p | AUROC Jev - Laya [paired bootstrap 95%] |", "|---|---|---|---|---|---|---|"]
    for s in list(P)[1:]:
        b = sum(x and not z for x, z in zip(cor[jn], cor[s]))
        c = sum(z and not x for x, z in zip(cor[jn], cor[s]))
        d = [u - v for u, v in zip(boot[jn], boot[s])]
        L.append("| Jev vs %s | %d | %d | %d | %d | %.4f | %+.3f [%+.3f, %+.3f] |" % (
            (s, len(y), sum((u >= 0.5) == (v >= 0.5) for u, v in zip(P[jn], P[s])), b, c, mcnemar_exact(b, c), auroc(P[jn], y) - auroc(P[s], y))
            + pct(d)))
    f3 = lambda xs: "%.3f" % (sum(xs) / len(xs)) if xs else "-"  # noqa: E731
    L += ["\n### Confidence behaviour (top p = max(p(true), 1 - p(true)); Jev displayed values)\n",
          "| system | p(true) in {0, 1} (100% shown) | mean top p right / wrong | wrong with top >= 0.90 | gold shown 0% | p(true) = 0.5 "
          "| distinct p(true) values |", "|---|---|---|---|---|---|---|"]
    for s, p in P.items():
        top = [max(v, 1 - v) for v in p]
        L.append("| %s | %d | %s / %s | %d/%d | %d | %d | %d |" % (
            s, sum(v in (0, 1) for v in p), f3([t for t, c in zip(top, cor[s]) if c]), f3([t for t, c in zip(top, cor[s]) if not c]),
            sum(t >= 0.9 and not c for t, c in zip(top, cor[s])), sum(not c for c in cor[s]),
            sum((v == 0 and g) or (v == 1 and not g) for v, g in zip(p, y)), sum(v == 0.5 for v in p), len(set(p))))
    L += ["\n### Per item (p(true); O = correct at 0.5)\n",
          "| # | row | id | gold | %s |" % " | ".join(P), "|---|---|---|---|%s" % ("---|" * len(P))]
    for n, (i, g) in enumerate(zip(its, y), 1):
        L.append("| %d | %d | %s | %s | %s |" % (n, i["row"], i["id"].split("/")[1], str(g).lower(), " | ".join(
            "%s %.2f" % ("O" if (p[n - 1] >= 0.5) == g else "X", p[n - 1]) for p in P.values())))
    return L


def load_session(session):
    return [json.loads(x) for x in (session_dir(session) / ("%s_requests.jsonl" % session)).read_text(encoding="utf-8").splitlines()]


def cmd_stability(a):
    """Determinism (same payload again) and option-order flips (the probe's permutation) against the reference session."""
    ref = {r["row"]: r for r in load_session(a.ref) if r["set"] == a.set and r.get("decisions") and r["phase"] == "main"}
    cur = [r for r in load_session(a.session) if r["set"] == a.set]
    det = [r for r in cur if r.get("decisions") and r["phase"] == "determinism"]
    flp = [r for r in cur if r.get("decisions") and r["phase"] == "option_order"]
    top = lambda r: r["decisions"][0]  # noqa: E731
    conf = lambda r: (r.get("confidence") or {}).get("decision")  # noqa: E731
    L = []
    w = L.append
    w("### Determinism: same payload as %s (%d rows)\n" % (a.ref, len(det)))
    w("| row | gold | %s (top %%) | %s (top %%) | same label | max abs dp | latencyMs %s / %s | confidence %s / %s "
      "| tokens in/out %s / %s |" % ((a.ref, a.session) * 4))
    w("|---|---|---|---|---|---|---|---|---|")
    dps, same, dconf, toks = [], 0, [], 0
    for r in det:
        r0, d0, d1 = ref[r["row"]], top(ref[r["row"]]), top(r)
        dp = max(abs(d0["probs"].get(k, 0) - d1["probs"].get(k, 0)) for k in set(d0["probs"]) | set(d1["probs"]))
        dps.append(dp)
        same += d0["pred"] == d1["pred"]
        dconf.append(abs(conf(r0) - conf(r)))
        u0, u1 = r0["usage"], r["usage"]
        toks += (u0["inputTokens"], u0["outputTokens"]) == (u1["inputTokens"], u1["outputTokens"])
        w("| %d | %s | %s (%g) | %s (%g) | %s | %.2f | %.1f / %.1f | %.2f / %.2f | %d/%d / %d/%d |" % (
            r["row"], d1["gold"], d0["pred"], 100 * d0["top_p"], d1["pred"], 100 * d1["top_p"], "yes" if d0["pred"] == d1["pred"] else "NO",
            dp, r0["latency_ms_response"], r["latency_ms_response"], conf(r0), conf(r), u0["inputTokens"], u0["outputTokens"],
            u1["inputTokens"], u1["outputTokens"]))
    if det:
        lat0 = [ref[r["row"]]["latency_ms_response"] for r in det]
        lat1 = [r["latency_ms_response"] for r in det]
        w("\nSame label %d/%d; identical probability vectors %d/%d; max abs dp %.2f; confidence identical %d/%d (max abs d %.2f); "
          "tokens identical %d/%d; latencyMs median %s %.1f vs %s %.1f, median abs d %.1f ms.\n" % (
              same, len(det), sum(x == 0 for x in dps), len(det), max(dps), sum(x == 0 for x in dconf), len(det), max(dconf),
              toks, len(det), a.ref, statistics.median(lat0), a.session, statistics.median(lat1),
              statistics.median([abs(x - y) for x, y in zip(lat0, lat1)])))
    probes = {m: {x["row"]: x for x in json.loads((HERE / ("T2_option_order_k1_%s.json" % m)).read_text(encoding="utf-8"))["sets"][0]["items"]}
              for m in ("english", "multilingual")}
    w("### Option-order flips: one permutation per row, the Laya probe's order (%d rows)\n" % len(flp))
    w("| row | gold | order sent | Jev original (top %) | Jev permuted (top %) | flip | p(original label) permuted | chosen slot "
      "| Laya en orig -> perm | Laya ml orig -> perm |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    flips, lf = 0, Counter()
    for r in flp:
        d0, d1 = top(ref[r["row"]]), top(r)
        assert r["perm"] == probes["english"][r["row"]]["perms"][0]["order"]
        f = d0["pred"] != d1["pred"]
        flips += f
        cells = []
        for m in ("english", "multilingual"):
            it = probes[m][r["row"]]
            lf[m] += it["perms"][0]["pred"] != it["orig"]["pred"]
            cells.append("%s -> %s" % (it["orig"]["pred"], it["perms"][0]["pred"]))
        w("| %d | %s | %s | %s (%g) | %s (%g) | %s | %g%% | %d | %s |" % (
            r["row"], d1["gold"], " / ".join(r["perm"]), d0["pred"], 100 * d0["top_p"], d1["pred"], 100 * d1["top_p"],
            "FLIP" if f else "-", 100 * d1["probs"][d0["pred"]], r["perm"].index(d1["pred"]), " | ".join(cells)))
    if flp:
        lo, hi = wilson(flips, len(flp))
        acc0 = sum(top(ref[r["row"]])["correct"] for r in flp)
        acc1 = sum(top(r)["correct"] for r in flp)
        w("\nJev flips %d/%d = %.3f, Wilson 95%% [%.3f, %.3f]; accuracy on these rows original %d/%d, permuted %d/%d; "
          "mean abs d top p %.3f. Same rows, same orders: Laya english flips %d/%d, multilingual %d/%d. "
          "References: Jev third-party per-permutation flip 0.13; Laya T2 probe 0.000 on all 40 rows (english and multilingual).\n" % (
              flips, len(flp), flips / len(flp), lo, hi, acc0, len(flp), acc1, len(flp),
              sum(abs(top(ref[r["row"]])["top_p"] - top(r)["top_p"]) for r in flp) / len(flp), lf["english"], len(flp),
              lf["multilingual"], len(flp)))
    ok = [r for r in cur if r.get("decisions")]
    w("### Latency (%s, successful runs %d)\n" % (a.session, len(ok)))
    w("| displayed 'server + network' median / min / max | browser POST median / min / max | click -> complete median / min / max "
      "| input tokens | output tokens | model |")
    w("|---|---|---|---|---|---|")
    w("| %s | %s | %s | %s | %s | %s |" % (
        mmm([r["displayed_ms"] for r in ok]), mmm([r["fetch_dur_ms"] for r in ok]), mmm([r["click_to_complete_ms"] for r in ok]),
        mmm([r["usage"]["inputTokens"] for r in ok]), mmm([r["usage"]["outputTokens"] for r in ok]),
        ", ".join("`%s` x%d" % kv for kv in sorted(Counter(r["model_id_details"] for r in ok).items()))))
    gaps = [r["gap_from_prev_click_s"] for r in cur if r["gap_from_prev_click_s"] is not None]
    w("\nRequests %d: HTTP 200 %d, other %d; attempts > 1: %d; click gap min / median %s / %s s." % (
        len(cur), sum(r["http_status"] == 200 for r in cur), sum(r["http_status"] != 200 for r in cur),
        sum(r["attempt"] > 1 for r in cur), "%.1f" % min(gaps) if gaps else "-", "%.1f" % statistics.median(gaps) if gaps else "-"))
    print("\n".join(L))


def cmd_t1(a):
    """T1 on the Jev-comparable decisions: Jev (latest successful record per decision over SESSIONS) against every Laya T1
    report, scored with laya_summary.py's bench_local.py port (decisions / metrics / t1_extra) so both sides share code."""
    import warnings
    import laya_summary as LS  # numpy; the metric definitions of laya_summary.md §2
    warnings.simplefilter("ignore", RuntimeWarning)  # t1_extra's score MAE on a subset without score decisions
    stem = "T1_typed_decisions_40"
    form = {(it["row"], it["qid"]): it for it in load_items(stem)[1]}
    rows = LS.read_dataset(DATA / (stem + ".jsonl"))[0]
    gold = json.loads(LS.GOLD.read_text(encoding="utf-8"))["decisions"]
    jrec = {}
    for s in a.sessions.split(","):
        for r in load_session(s):
            if r["set"] == stem and r.get("decisions"):
                jrec.update({d["id"]: (r, d) for d in r["decisions"]})
    laya = {m: LS.decisions(HERE / "laya" / ("%s_%s.json" % (stem, m)))[1] for m in LAYA_RUNNERS + ("typed-decisions",)}
    keep = [i for i, d in enumerate(laya["english"]) if not d["jev_excluded"]]
    G = [gold[i] for i in keep]
    jev = []
    for i in keep:
        d0 = laya["english"][i]
        r, d = jrec[form[(d0["row"], d0["qid"])]["id"]]
        q = rows[d0["row"]]["questions"][d0["qid"]]
        assert d["gold"] == d0["gold"] and d["qid"] == d0["qid"]
        if d0["type"] == "choice":
            keys = list(q["criteria"])
            assert sorted(keys) == sorted(d["probs"])
            p, pi = [d["probs"][k] for k in keys], keys.index(d["pred"])
        elif d0["type"] == "noul":
            p, pi = [1 - d["p_true"], d["p_true"]], int(d["pred"])
        else:
            p, pi = [d["probs"][str(k)] for k in range(len(q["criteria"]))], d["pred"]
        jev.append(dict(d0, pred=d["pred"], pi=pi, p=p, conf=max(p), score=d.get("score"), model="jev"))
    S = {"Jev": jev, **{m: [laya[m][i] for i in keep] for m in laya}}
    ok = lambda d: d["pred"] == d["gold"]  # noqa: E731
    pick = lambda ds, t: [d for d in ds if t is None or d["type"] == t]  # noqa: E731
    cell = lambda ds: "%d/%d = %.3f [%.3f, %.3f]" % ((sum(map(ok, ds)), len(ds), sum(map(ok, ds)) / len(ds)) + wilson(sum(map(ok, ds)), len(ds)))  # noqa: E731
    L = []
    w = L.append
    ex = LS.t1_extra(jev, G)
    w("### Accuracy on the same %d decisions (Jev runs: %d; argmax gold; noul p(true) >= 0.5; score = argmax level)\n" % (
        len(jev), len({(r["session"], r["run"]) for r, _ in jrec.values()})))
    w("| system | all | choice | noul | score (5 levels) | soft acc | Brier vs soft | Brier (one-hot) | ECE (15 bins) "
      "| score MAE: E[level] vs teacher |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for m, ds in S.items():
        x, mt = LS.t1_extra(ds, G), LS.metrics(ds)
        mae = "%.3f (Jev `score` field) / %.3f (from rounded p)" % (statistics.mean(
            abs(d["score"] - g["gold_score"]) for d, g in zip(ds, G) if d["type"] == "score"), x["score_mae"]) if m == "Jev" else "%.3f" % x["score_mae"]
        w("| %s | %s | %s | %s | %s | %.3f | %.3f | %.3f | %.3f | %s |" % (
            "Jev (playground)" if m == "Jev" else "Laya " + m + (" (fine-tuned, reference)" if m == "typed-decisions" else ""),
            cell(ds), cell(pick(ds, "choice")), cell(pick(ds, "noul")), cell(pick(ds, "score")), x["soft_accuracy"],
            x["brier_vs_soft"], mt["brier"], mt["ece"], mae))
    w("\nPer-question majority baseline on these decisions: %.3f (laya_summary.py t1_extra rule)." % ex["per_question_majority"])
    w("\n### Exact McNemar, Jev vs each Laya runner (b = Jev right & Laya wrong, c = Jev wrong & Laya right)\n")
    w("| pair | subset | n | both right | b | c | both wrong | p |")
    w("|---|---|---|---|---|---|---|---|")
    for m in S:
        for t in ((None, "choice", "noul", "score") if m != "Jev" else ()):
            ps = [(x, y) for x, y in zip(pick(jev, t), pick(S[m], t))]
            b, c = sum(ok(x) and not ok(y) for x, y in ps), sum(ok(y) and not ok(x) for x, y in ps)
            w("| Jev vs %s | %s | %d | %d | %d | %d | %d | %.4f |" % (m, t or "all", len(ps), sum(ok(x) and ok(y) for x, y in ps), b, c,
                                                                  sum(not ok(x) and not ok(y) for x, y in ps), mcnemar_exact(b, c)))
    w("\n### noul, same input: Jev Boolean has no description field; Laya with and without the true/false criteria\n")
    jn, Gn = pick(jev, "noul"), [g for g, d in zip(G, jev) if d["type"] == "noul"]
    had = lambda d: bool(rows[d["row"]]["questions"][d["qid"]].get("criteria"))  # noqa: E731
    w("| system | input | all | had criteria in T1 | never had criteria | soft acc | Brier vs soft | predicted true (gold true %d) "
      "| b / c vs Jev | McNemar p |" % sum(d["gold"] for d in jn))
    w("|---|---|---|---|---|---|---|---|---|---|")
    nouls = [("Jev (playground)", "question only", jn)]
    for m in ("english", "multilingual"):
        nc = {(d["row"], d["qid"]): d for d in LS.decisions(HERE / "laya" / ("%s_noulnocrit_%s.json" % (stem, m)))[1]}
        nouls += [("Laya " + m, "with criteria", pick(S[m], "noul")), ("Laya " + m, "no criteria", [nc[(d["row"], d["qid"])] for d in jn])]
    for name, inp, ds in nouls:
        x = LS.t1_extra(ds, Gn)
        b, c = sum(ok(j) and not ok(y) for j, y in zip(jn, ds)), sum(ok(y) and not ok(j) for j, y in zip(jn, ds))
        w("| %s | %s | %s | %s | %s | %.3f | %.3f | %d | %s | %s |" % (
            name, inp, cell(ds), cell([d for d in ds if had(d)]), cell([d for d in ds if not had(d)]), x["soft_accuracy"],
            x["brier_vs_soft"], sum(bool(d["pred"]) for d in ds), "-" if ds is jn else "%d / %d" % (b, c),
            "-" if ds is jn else "%.4f" % mcnemar_exact(b, c)))
    w("\n### Per workflow and per question (correct / n)\n")
    w("| workflow | question | type | n | %s |" % " | ".join(S))
    w("|---|---|---|---|%s" % ("---|" * len(S)))
    groups = list(dict.fromkeys((d["workflow"], d["qid"]) for d in jev))
    for wf in dict.fromkeys(g[0] for g in groups):
        for key in [g for g in groups if g[0] == wf] + [(wf, None)]:
            sel = lambda ds: [d for d in ds if d["workflow"] == wf and (key[1] is None or d["qid"] == key[1])]  # noqa: E731
            w("| %s | %s | %s | %d | %s |" % (wf if key[1] is None else "", "**all**" if key[1] is None else key[1],
                                              "" if key[1] is None else sel(jev)[0]["type"], len(sel(jev)),
                                              " | ".join("%d" % sum(map(ok, sel(ds))) for ds in S.values())))
    w("\n### Score decisions (security_incidents/severity, 5 levels)\n")
    w("| row | gold level | teacher E | Jev p(0..4) | Jev `score` | Jev argmax | Jev displayed level | Laya en E / argmax "
      "| Laya ml E / argmax |")
    w("|---|---|---|---|---|---|---|---|---|")
    for j, en, ml, g in zip(jev, S["english"], S["multilingual"], G):
        if j["type"] == "score":
            w("| %d | %d | %.2f | %s | %.2f | %d%s | %d%s | %.2f / %d%s | %.2f / %d%s |" % (
                j["row"], j["gold"], g["gold_score"], " ".join("%.2f" % v for v in j["p"]), j["score"], j["pred"], "" if ok(j) else " X",
                math.floor(j["score"] + 0.5), "" if math.floor(j["score"] + 0.5) == j["gold"] else " X",
                en["score"], en["pred"], "" if ok(en) else " X", ml["score"], ml["pred"], "" if ok(ml) else " X"))
    w("\n### Confidence behaviour (Jev: displayed top p, 2-decimal rounding; Laya: max p)\n")
    w("| system | type | n | mean top p right / wrong | top >= 0.90 | wrong with top >= 0.90 | top = 1.00 |")
    w("|---|---|---|---|---|---|---|")
    f3 = lambda xs: "%.3f" % statistics.mean(xs) if xs else "-"  # noqa: E731
    for m in ("Jev", "english", "multilingual"):
        for t in ("choice", "noul", "score"):
            ds = pick(S[m], t)
            w("| %s | %s | %d | %s / %s | %d | %d/%d | %d |" % (
                m, t, len(ds), f3([d["conf"] for d in ds if ok(d)]), f3([d["conf"] for d in ds if not ok(d)]),
                sum(d["conf"] >= 0.9 for d in ds), sum(d["conf"] >= 0.9 and not ok(d) for d in ds), sum(not ok(d) for d in ds),
                sum(d["conf"] >= 0.995 for d in ds)))
    runs = list({(r["session"], r["run"]): r for r, _ in jrec.values()}.values())
    w("\n### Jev T1 runs: latency and tokens by questions per request (successful runs used above)\n")
    w("| questions / run | runs | displayed ms median / min / max | browser POST ms median / min / max | displayed ms per question "
      "(median) | input tokens median / min / max | output tokens median / min / max |")
    w("|---|---|---|---|---|---|---|")
    for nq in sorted({len(r["decisions"]) for r in runs}) + [None]:
        rr = [r for r in runs if nq is None or len(r["decisions"]) == nq]
        w("| %s | %d | %s | %s | %.0f | %s | %s |" % (
            nq or "all", len(rr), mmm([r["displayed_ms"] for r in rr]), mmm([r["fetch_dur_ms"] for r in rr]),
            statistics.median(r["latency_ms_response"] / len(r["decisions"]) for r in rr), mmm([r["usage"]["inputTokens"] for r in rr]),
            mmm([r["usage"]["outputTokens"] for r in rr])))
    w("\nRuns by session: %s. Model ID: %s." % (dict(Counter(r["session"] for r in runs)),
                                                dict(Counter(r["model_id_details"] for r in runs))))
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    e = sp.add_parser("expect")
    e.add_argument("set")
    e.add_argument("--rows")
    e.add_argument("--qids")
    e.add_argument("--probe", action="store_true", help="permute options as the Laya T2 probe did for each row")
    r = sp.add_parser("record")
    r.add_argument("session")
    r.add_argument("set")
    r.add_argument("run", type=int)
    r.add_argument("dump")
    r.add_argument("--row", type=int, required=True)
    r.add_argument("--qids")
    r.add_argument("--omit-reason")
    r.add_argument("--phase", default="main")
    r.add_argument("--probe", action="store_true", help="the run sent the Laya T2 probe's option order for this row")
    n = sp.add_parser("analyze")
    n.add_argument("session")
    n.add_argument("set")
    s = sp.add_parser("stability")
    s.add_argument("ref")
    s.add_argument("session")
    s.add_argument("set")
    t = sp.add_parser("t1")
    t.add_argument("sessions", help="comma-separated sessions whose T1 records are used, e.g. S1,S2")
    a = ap.parse_args()
    {"expect": cmd_expect, "record": cmd_record, "analyze": cmd_analyze, "stability": cmd_stability, "t1": cmd_t1}[a.cmd](a)


if __name__ == "__main__":
    main()
