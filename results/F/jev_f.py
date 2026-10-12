"""Track F: TypeSafe Jev (jevplayground.com, manual browser runs) vs Laya on 24 Korean domain-routing rows.
No model call here: Laya predictions come from existing reports, Jev results from the playground runs.

    .venv/bin/python results/F/jev_f.py sample                 # results/F/jev_sample_24.jsonl + precheck hashes
    .venv/bin/python results/F/jev_f.py record PASS N EVAL.json [SNAPSHOT.yml]  # append one Run click of row N to jev_runs_raw.jsonl
    .venv/bin/python results/F/jev_f.py analyze                                   # markdown tables on whatever runs exist
`record` writes an error record and exits 2 when the click returned no decision (a retry of the same row is attempt 2);
`record_error` is the name the first error was recorded with and is kept as an alias.
"""
import hashlib
import json
import math
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from metrics_extra import mcnemar_exact, read_dataset, row_splits  # noqa: E402
import yaml  # noqa: E402

F = ROOT / "results/F"
DATA = ROOT / "data/evals/ko_massive_domain_8.jsonl"
TRAIN = ROOT / "poc/finetune/data/domain8_train.jsonl"
ZS = ROOT / "results/B/20261002-1643_multilingual_ko_massive_domain_8.json"
FT = ROOT / "results/P4/full_20261003-1156_ft-v1_ko_massive_domain_8.json"
SAMPLE = F / "jev_sample_24.jsonl"
RAW = F / "jev_runs_raw.jsonl"
QUESTION = "Which domain should handle this request?"
CRIT = json.loads((ROOT / "poc/schema/router_v1.json").read_text(encoding="utf-8"))["questions"]["domain"]["criteria"]
KEYS = list(CRIT)
CHOICES = {1: ["%s: %s" % (k, v) for k, v in CRIT.items()], 2: KEYS}
KST = timezone(timedelta(hours=9))


def sha12(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def laya(path, rows):
    rep = json.loads(path.read_text(encoding="utf-8"))
    assert rep["config"]["dataset_sha256"] == hashlib.sha256(DATA.read_bytes()).hexdigest(), path
    assert len(rep["cases"]) == len(rows)
    for c, r in zip(rep["cases"], rows):  # one question per row, cases in row order
        assert c["qid"] == "domain" and c["expected"] == r["expected"]["domain"] and c["tags"] == r.get("tags", [])
    return [(c["answer"]["choice"], c["answer"]["answer_confidence"]) for c in rep["cases"]]


def cmd_sample():
    rows, header = read_dataset(DATA)
    splits, rule = row_splits(rows, header, "auto", DATA.name)
    assert rule == "index parity"
    seen = {r["state"]["utterance"] for r in read_dataset(TRAIN)[0]}
    zs, ft = laya(ZS, rows), laya(FT, rows)
    pool = defaultdict(list)
    for i, (r, s) in enumerate(zip(rows, splits)):  # ascending row index
        if s == "test" and r["state"]["utterance"] not in seen:
            pool[r["expected"]["domain"]].append(i)
    rng = random.Random(13)
    pick = sorted(i for k in KEYS for i in rng.sample(pool[k], 3))
    out = []
    for i in pick:
        u = rows[i]["state"]["utterance"]
        out.append({"utterance": u, "gold": rows[i]["expected"]["domain"], "laya_zs": zs[i][0], "laya_zs_p": zs[i][1],
                    "laya_ft": ft[i][0], "laya_ft_p": ft[i][1], "row_index": i})
    SAMPLE.write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out), encoding="utf-8")
    print("pool (test, train-clean):", {k: len(pool[k]) for k in KEYS}, "total", sum(len(v) for v in pool.values()))
    print("question sha12", sha12(QUESTION), "| choices sha12 pass1", sha12("\n".join(CHOICES[1])),
          "pass2", sha12("\n".join(CHOICES[2])))
    for n, o in enumerate(out, 1):
        print("%2d row %3d %-13s %s %s" % (n, o["row_index"], o["gold"], sha12(o["utterance"]), json.dumps(o["utterance"], ensure_ascii=False)))


def key_of(label):
    return label.split(":", 1)[0].strip()


def parse_text(text):
    """Result region innerText: DECISION, the label/percent pairs, the 'N ms · server + network' line."""
    ls = [x.strip() for x in text.splitlines() if x.strip()]
    i, j = ls.index("DECISION"), ls.index("Probability distribution")
    probs, k = {}, j + 1
    while re.fullmatch(r"\d+(\.\d+)?%", ls[k + 1]):
        probs[ls[k]] = float(ls[k + 1][:-1])
        k += 2
    ms = re.search(r"([\d,]+) ms · server \+ network", text)
    return {"decision": ls[i + 1], "probs": probs, "ms": int(ms.group(1).replace(",", ""))}


def unq(v):
    v = v.strip()
    return yaml.safe_load(v) if v[:1] in "'\"" else v


def parse_snapshot(path):
    """Same fields from the accessibility snapshot Playwright MCP saved after the Run click."""
    ls = Path(path).read_text(encoding="utf-8").splitlines()
    item = [unq(x.strip()[2:]) if x.strip().startswith("- ") else x.strip() for x in ls]
    st = next(i for i, x in enumerate(item) if str(x).startswith('textbox "State"'))
    state = next(str(x)[len("text: "):] for x in item[st + 1:st + 4] if str(x).startswith("text: "))
    r = next(i for i, x in enumerate(item) if str(x).startswith('region "Jev result"'))
    status = next(unq(str(x).split(": ", 1)[1]) for x in item[r:] if str(x).startswith("status [ref="))
    d = next(i for i in range(r, len(item)) if item[i] == "text: DECISION")
    decision = re.match(r'heading "(.*)" \[level=2\]', str(item[d + 1])).group(1)
    pd = next(i for i in range(d, len(item)) if str(item[i]).startswith('heading "Probability distribution"'))
    probs = {}
    for i in range(pd, len(item) - 1):
        a, b = str(item[i]), str(item[i + 1])
        if a.startswith("generic [ref=") and b.startswith("strong [ref="):
            pct = unq(b.split(": ", 1)[1])
            if re.fullmatch(r"\d+(\.\d+)?%", str(pct)):
                probs[unq(a.split(": ", 1)[1])] = float(str(pct)[:-1])
        if a.startswith("paragraph") and probs:
            break
    ms = next(int(m.group(1).replace(",", "")) for x in item[pd:] for m in [re.search(r"([\d,]+) ms · server \+ network", str(x))] if m)
    return {"state": state, "status": status, "decision": decision, "probs": probs, "ms": ms}


def cmd_record(pas, n, dump, snap=None):
    pas, n = int(pas), int(n)
    row = [json.loads(x) for x in SAMPLE.read_text(encoding="utf-8").splitlines()][n - 1]
    prev = [json.loads(x) for x in RAW.read_text(encoding="utf-8").splitlines()] if RAW.exists() else []
    mine = [p for p in prev if p["pass"] == pas and p["run"] == n]
    assert not any(p["decision_key"] for p in mine), "already recorded"
    d = json.loads(Path(dump).read_text(encoding="utf-8"))
    bad = []
    chk = lambda ok, msg: ok or bad.append(msg)  # noqa: E731
    f = d["form"]
    chk(f["state"] == row["utterance"], "state %r != sample %r" % (f["state"], row["utterance"]))
    chk(f["question"] == QUESTION, "question %r" % f["question"])
    chk(f["choices"] == CHOICES[pas], "choices %r" % f["choices"])
    chk(f["counter"] == "8 of 10" and "Single question" in f["pressed"] and "Choice" in f["pressed"], "form %r" % f)
    page = [x for x in prev if x["click_epoch_ms"] >= d["clicks"][0]]  # records made in this page load (hook resets on reload)
    chk(len(d["clicks"]) == len(page) + 1, "clicks in page %d, records in page %d" % (len(d["clicks"]), len(page)))
    gap = (d["clicks"][-1] - d["clicks"][-2]) / 1000 if len(d["clicks"]) > 1 else None
    chk(gap is None or gap >= 3, "gap %.2f s < 3 s" % (gap or 0))
    ev = [x for x in d.get("fetches", d.get("fetches_all_session", []))
          if x["url"].endswith("/api/evaluate") and x["start"] >= d["click"] - 50]
    chk(len(ev) == 1, "fetches %r" % ev)
    if bad:
        print("NOT RECORDED:\n  " + "\n  ".join(bad))
        sys.exit(1)
    head = {"pass": pas, "labels": "key: ko-description" if pas == 1 else "key only", "run": n, "attempt": len(mine) + 1,
            "row_index": row["row_index"], "utterance": row["utterance"], "gold": row["gold"]}
    ts = datetime.fromtimestamp(d["click"] / 1000, KST).isoformat(timespec="milliseconds")
    fetch = {"path": "/api/evaluate", "status": ev[0]["status"], "dur_ms": ev[0]["dur"]}
    raw = str(Path(dump).resolve().relative_to(ROOT))
    if snap:
        dst = Path(dump).with_suffix(".snapshot.yml")
        if Path(snap).resolve() != dst.resolve():
            shutil.copy(snap, dst)
    if d["fin"] is None or ev[0]["status"] != 200:
        end = d["status_log"][-1]
        rec = dict(head, decision_label=None, decision_key=None, probs=None, probs_key=None, ms=None, timestamp=ts,
                   click_epoch_ms=d["click"], complete_epoch_ms=end[0], client_ms=end[0] - d["click"], fetch=fetch,
                   gap_from_prev_click_s=gap, status_text=d["status_now"].strip(),
                   error=" | ".join(x.strip() for x in d["text"].splitlines() if x.strip())[:300], raw=raw, snapshot_crosscheck=False)
        with RAW.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("p%d run %2d attempt %d row %3d ERROR HTTP %d after %d ms: %s | gap %s s | %s" % (
            pas, n, rec["attempt"], rec["row_index"], ev[0]["status"], ev[0]["dur"], rec["status_text"],
            "-" if gap is None else "%.1f" % gap, ts))
        sys.exit(2)
    t = parse_text(d["text"])
    ft = d["full_text"]
    det = json.JSONDecoder().raw_decode(ft[ft.index("{", ft.index("View details")):])[0]
    dd = det["answers"]["decision"]
    model_id = re.search(r"Model ID(.*?)Input tokens", ft).group(1)
    chk(d["fin"][0] >= d["click"], "'Evaluation complete' before the click")
    chk(list(t["probs"]) == CHOICES[pas], "displayed labels %r" % list(t["probs"]))
    chk(t["decision"] == dd["choice"] and d["status_now"].strip() == "Evaluation complete. %s." % t["decision"], "decision mismatch")
    chk(all(round(dd["probabilities"][k] * 100) == v for k, v in t["probs"].items()), "displayed %% != details")
    chk(t["probs"][t["decision"]] == max(t["probs"].values()), "decision is not the displayed argmax")
    if snap:
        sn = parse_snapshot(snap)
        chk(sn["state"] == row["utterance"] and sn["decision"] == t["decision"] and sn["probs"] == t["probs"] and sn["ms"] == t["ms"]
            and sn["status"] == d["status_now"].strip(), "snapshot != DOM: %r" % sn)
    if bad:
        print("NOT RECORDED:\n  " + "\n  ".join(bad))
        sys.exit(1)
    rec = dict(head, decision_label=t["decision"], decision_key=key_of(t["decision"]), probs=t["probs"],
               probs_key={key_of(k): v for k, v in t["probs"].items()},
               details_probabilities={key_of(k): v for k, v in dd["probabilities"].items()}, ms=t["ms"], timestamp=ts,
               click_epoch_ms=d["click"], complete_epoch_ms=d["fin"][0], client_ms=d["fin"][0] - d["click"], fetch=fetch,
               gap_from_prev_click_s=gap, model_id=model_id, usage=det.get("usage"), provider_confidence=det.get("confidence"),
               rounding=det.get("rounding"), warnings=det.get("warnings"), status_text=d["status_now"].strip(), raw=raw,
               snapshot_crosscheck=bool(snap))
    with RAW.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    p = rec["probs_key"][rec["decision_key"]]
    print("p%d run %2d attempt %d row %3d gold %-13s jev %-13s %3.0f%% %s | %d ms shown, fetch %d ms %d, client %d ms | gap %s s | %s" % (
        pas, n, rec["attempt"], rec["row_index"], rec["gold"], rec["decision_key"], p,
        "OK " if rec["decision_key"] == rec["gold"] else "XX ", rec["ms"], fetch["dur_ms"], fetch["status"], rec["client_ms"],
        "-" if gap is None else "%.1f" % gap, ts))


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def med(xs):
    xs = sorted(xs)
    return None if not xs else (xs[len(xs) // 2] if len(xs) % 2 else (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2)


def cmd_analyze():
    sample = [json.loads(x) for x in SAMPLE.read_text(encoding="utf-8").splitlines()]
    raw = [json.loads(x) for x in RAW.read_text(encoding="utf-8").splitlines()] if RAW.exists() else []
    passes = sorted({r["pass"] for r in raw}) or [1]
    jev = {(r["pass"], r["row_index"]): r for r in raw if r["decision_key"]}
    fails = defaultdict(list)
    for r in raw:
        if not r["decision_key"]:
            fails[(r["pass"], r["row_index"])].append(r)
    runs = {ps: [r for r in raw if r["pass"] == ps and r["decision_key"]] for ps in passes}
    name = {1: "Jev pass 1 (key: ko-description)", 2: "Jev pass 2 (key only)"}
    out = []
    w = out.append
    f1 = lambda xs: "%.1f" % (sum(xs) / len(xs)) if xs else "-"  # noqa: E731
    mmm = lambda xs: "%g / %g / %g" % (med(xs), min(xs), max(xs))  # noqa: E731

    def jcell(ps, o):
        r = jev.get((ps, o["row_index"]))
        if r:
            tag = " [attempt %d]" % r["attempt"] if r["attempt"] > 1 else ""
            return "%s %s (%g%%)%s" % ("O" if r["decision_key"] == o["gold"] else "X", r["decision_key"],
                                      r["probs_key"][r["decision_key"]], tag)
        e = fails.get((ps, o["row_index"]))
        return "error HTTP %s" % "/".join(str(x["fetch"]["status"]) for x in e) if e else "not run"

    lcell = lambda key, p, gold: "%s %s (%.2f)" % ("O" if key == gold else "X", key, p)  # noqa: E731
    w("### Per-row (O = gold, X = wrong; Jev p = displayed %, Laya p = answer_confidence)\n")
    w("| # | row | utterance | gold | %s | Laya zero-shot | Laya ft-v1 |" % " | ".join(name[ps] for ps in passes))
    w("|---|---|---|---|%s---|---|" % ("---|" * len(passes)))
    for n, o in enumerate(sample, 1):
        w("| %d | %d | %s | %s | %s | %s | %s |" % (n, o["row_index"], o["utterance"], o["gold"],
                                                  " | ".join(jcell(ps, o) for ps in passes),
                                                  lcell(o["laya_zs"], o["laya_zs_p"], o["gold"]),
                                                  lcell(o["laya_ft"], o["laya_ft_p"], o["gold"])))
    w("\n### Accuracy\n")
    w("| system | rows | correct | accuracy | Wilson 95% CI |")
    w("|---|---|---|---|---|")
    systems = []
    for ps in passes:
        systems.append((name[ps], [o for o in sample if (ps, o["row_index"]) in jev],
                        lambda o, ps=ps: jev[(ps, o["row_index"])]["decision_key"]))
    systems += [("Laya zero-shot multilingual", sample, lambda o: o["laya_zs"]), ("Laya ft-v1", sample, lambda o: o["laya_ft"])]
    for ps in passes:
        rows = [o for o in sample if (ps, o["row_index"]) in jev]
        if 0 < len(rows) < len(sample):
            systems += [("Laya zero-shot, Jev pass %d rows" % ps, rows, lambda o: o["laya_zs"]),
                        ("Laya ft-v1, Jev pass %d rows" % ps, rows, lambda o: o["laya_ft"])]
    for nm, rows, pred in systems:
        k = sum(pred(o) == o["gold"] for o in rows)
        ci = wilson(k, len(rows))
        w("| %s | %d | %d/%d | %s | %s |" % (nm, len(rows), k, len(rows), "%.3f" % (k / len(rows)) if rows else "-",
                                           "[%.3f, %.3f]" % ci if ci else "-"))
    w("\n### Agreement and exact McNemar (paired rows only; b = Jev right & Laya wrong, c = Jev wrong & Laya right)\n")
    w("| pair | n | same label | b | c | exact McNemar p |")
    w("|---|---|---|---|---|---|")
    for ps in passes:
        rows = [o for o in sample if (ps, o["row_index"]) in jev]
        for lname, lk in (("zero-shot", "laya_zs"), ("ft-v1", "laya_ft")):
            jk = [jev[(ps, o["row_index"])]["decision_key"] for o in rows]
            b = sum(j == o["gold"] and o[lk] != o["gold"] for j, o in zip(jk, rows))
            c = sum(j != o["gold"] and o[lk] == o["gold"] for j, o in zip(jk, rows))
            w("| Jev pass %d vs %s | %d | %d | %d | %d | %.4f |" % (ps, lname, len(rows), sum(j == o[lk] for j, o in zip(jk, rows)),
                                                               b, c, mcnemar_exact(b, c)))
    w("\n### Jev confidence behaviour (displayed %; the playground rounds probabilities to 2 decimals)\n")
    w("| pass | runs | top = 100% | runs with any 0% option | 0% cells / all cells | mean top % | mean top % right / wrong "
      "| wrong with top >= 90% | mean provider confidence |")
    w("|---|---|---|---|---|---|---|---|---|")
    for ps in passes:
        rs = runs[ps]
        top = [r["probs_key"][r["decision_key"]] for r in rs]
        ok = [r["decision_key"] == r["gold"] for r in rs]
        mw = [t for t, y in zip(top, ok) if not y]
        pc = [r["provider_confidence"]["decision"] for r in rs if (r.get("provider_confidence") or {}).get("decision") is not None]
        w("| %d | %d | %d | %d | %d/%d | %s | %s / %s | %d/%d | %s |" % (
            ps, len(rs), sum(t == 100 for t in top), sum(any(v == 0 for v in r["probs_key"].values()) for r in rs),
            sum(v == 0 for r in rs for v in r["probs_key"].values()), 8 * len(rs), f1(top), f1([t for t, y in zip(top, ok) if y]),
            f1(mw), sum(t >= 90 for t in mw), len(mw), "%.3f (n=%d)" % (sum(pc) / len(pc), len(pc)) if pc else "-"))
    w("\n### Jev latency (ms, successful runs)\n")
    w("| pass | runs | displayed 'server + network' median / min / max | browser POST /api/evaluate median / min / max "
      "| click -> 'Evaluation complete' median / min / max |")
    w("|---|---|---|---|---|")
    for ps in passes:
        rs = runs[ps]
        if rs:
            w("| %d | %d | %s | %s | %s |" % (ps, len(rs), mmm([r["ms"] for r in rs]), mmm([r["fetch"]["dur_ms"] for r in rs]),
                                            mmm([r["client_ms"] for r in rs])))
    w("\n### Jev model and token usage (details panel)\n")
    w("| pass | runs | model_id values | input tokens median / min / max | output tokens median / min / max |")
    w("|---|---|---|---|---|")
    for ps in passes:
        rs = runs[ps]
        if rs:
            models = ", ".join("`%s` x%d" % kv for kv in sorted(Counter(r["model_id"] for r in rs).items()))
            w("| %d | %d | %s | %s | %s |" % (ps, len(rs), models, mmm([r["usage"]["inputTokens"] for r in rs]),
                                            mmm([r["usage"]["outputTokens"] for r in rs])))
    w("\n### Per-domain correct\n")
    w("| gold domain | rows | %s | Laya zero-shot | Laya ft-v1 |" % " | ".join(name[ps] for ps in passes))
    w("|---|---|%s---|---|" % ("---|" * len(passes)))
    for k in KEYS:
        rows = [o for o in sample if o["gold"] == k]
        jj = []
        for ps in passes:
            have = [o for o in rows if (ps, o["row_index"]) in jev]
            jj.append("%d/%d" % (sum(jev[(ps, o["row_index"])]["decision_key"] == k for o in have), len(have)) if have else "-")
        w("| %s | %d | %s | %d/%d | %d/%d |" % (k, len(rows), " | ".join(jj), sum(o["laya_zs"] == k for o in rows), len(rows),
                                              sum(o["laya_ft"] == k for o in rows), len(rows)))
    w("\n### Requests sent to jevplayground.com /api/evaluate\n")
    gaps = [r["gap_from_prev_click_s"] for r in raw if r["gap_from_prev_click_s"] is not None]
    w("Total %d: HTTP 200 %d, other %d; retries (attempt > 1) %d; smallest gap between consecutive clicks in one page load %s s.\n" % (
        len(raw), sum(r["fetch"]["status"] == 200 for r in raw), sum(r["fetch"]["status"] != 200 for r in raw),
        sum(r["attempt"] > 1 for r in raw), "%.1f" % min(gaps) if gaps else "-"))
    w("| pass | run | attempt | row | KST click time | gap from previous click (s) | HTTP | displayed ms | outcome |")
    w("|---|---|---|---|---|---|---|---|---|")
    for r in raw:
        w("| %d | %d | %d | %d | %s | %s | %d | %s | %s |" % (
            r["pass"], r["run"], r["attempt"], r["row_index"], r["timestamp"][11:23],
            "-" if r["gap_from_prev_click_s"] is None else "%.1f" % r["gap_from_prev_click_s"], r["fetch"]["status"],
            r["ms"] if r["ms"] is not None else "-", r["decision_key"] or r["status_text"]))
    print("\n".join(out))

if __name__ == "__main__":
    {"sample": cmd_sample, "record": cmd_record, "record_error": cmd_record, "analyze": cmd_analyze}[sys.argv[1]](*sys.argv[2:])
