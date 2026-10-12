"""Record one S3 request from its dump (jev_cmp.py record) and classify stop conditions.

    .venv/bin/python results/F/jev_cmp/sessions/S3_20261007/s3_record.py RUN ITEM   # dump raw/rRR_<T>_rowNN.json

Exit 0 = recorded OK; 1 = not recorded (no request after the click, gap or payload mismatch);
2 = error record written, HTTP 5xx -> wait >= 60 s and retry the item once (a failed retry ends the session);
4 = error record written, HTTP 429 or rate-limit / captcha wording -> stop the whole session, no retry;
5 = error record written, any other failure (4xx, network error, unparseable) -> stop the session;
3 = recorded as success but stop wording seen on the page -> stop the session.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
LIMIT = re.compile(r"rate.?limit|too many requests|usage limit (reached|exceeded)|limit (reached|exceeded)|quota|slow down|unusual traffic"
                   r"|captcha|verify (that )?you are (a )?human", re.I)
STOP = re.compile(LIMIT.pattern + r"|temporarily unavailable|try again later|access denied", re.I)


def main():
    run, item = int(sys.argv[1]), int(sys.argv[2])
    p = next(r for r in json.loads((HERE / "raw/run_plan.json").read_text()) if r["item"] == item)
    dump = HERE / "raw" / ("r%02d_%s_row%02d.json" % (run, p["set"].split("_")[0], p["row"]))
    d = json.loads(dump.read_text(encoding="utf-8"))
    d = json.loads(d) if isinstance(d, str) else d
    jl = HERE / "S3_requests.jsonl"
    prev = [json.loads(x) for x in jl.read_text(encoding="utf-8").splitlines()] if jl.exists() else []
    if prev and (d["click"] is None or d["click"] <= max(r["click_epoch_ms"] for r in prev)):
        print("STALE DUMP: its click is not newer than the last recorded click (a retry of the same payload would pass the body check)")
        sys.exit(1)
    cmd = [str(ROOT / ".venv/bin/python"), str(HERE.parents[1] / "jev_cmp.py"), "record", "S3", p["set"], str(run), str(dump),
           "--row", str(p["row"])]
    rc = subprocess.run(cmd, cwd=ROOT).returncode
    pg = d.get("page") or {}
    seen = " ".join([d.get("text", ""), d.get("status_now") or "", pg.get("title") or "", " ".join(pg.get("alerts") or []),
                     pg.get("body_stop_match") or ""])
    hits = sorted({m.group(0) for m in STOP.finditer(seen)})
    limit = bool(LIMIT.search(seen)) or bool(pg.get("captcha_frames"))
    click = d["click"]
    calls = [c for c in d["calls"] if c["t0"] >= click - 50]
    status = calls[0].get("status") if calls else None
    body = (calls[0].get("resp_text") or "") if calls else ""
    if d.get("timed_out"):
        print("dump timed out")
    if hits or pg.get("captcha_frames"):
        print("STOP WORDING:", hits, pg.get("captcha_frames") or "")
    print("wall - mono offset %s ms" % d.get("wall_minus_mono_ms"))
    if rc == 1:
        sys.exit(1)
    if status == 429 or limit or LIMIT.search(body):
        print("STOP_LIMIT: HTTP %s, wording %s | body %s" % (status, hits, body[:300]))
        sys.exit(4)
    if rc == 2:
        if status is not None and 500 <= status <= 599:
            print("RETRY_5XX: HTTP %s | body %s" % (status, body[:300]))
            sys.exit(2)
        print("STOP_OTHER: HTTP %s | body %s" % (status, body[:300]))
        sys.exit(5)
    if rc:
        sys.exit(rc)
    sys.exit(3 if hits else 0)


if __name__ == "__main__":
    main()
