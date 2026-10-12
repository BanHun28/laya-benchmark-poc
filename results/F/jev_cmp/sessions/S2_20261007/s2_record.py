"""Record one S2 run from its dump (jev_cmp.py record) and flag stop conditions.

    .venv/bin/python results/F/jev_cmp/sessions/S2_20261007/s2_record.py RUN ITEM   # dump raw/rRR_<T>_rowNN.json
exit 0 = recorded OK; 2 = error record written (stop / retry rule); 1 = not recorded (no request after the click, gap or
payload mismatch); 3 = recorded but stop wording seen on the page.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
STOP = re.compile(r"temporarily unavailable|rate.?limit|too many requests|captcha|usage limit (reached|exceeded)|try again later", re.I)


def main():
    run, item = int(sys.argv[1]), int(sys.argv[2])
    p = next(r for r in json.loads((HERE / "raw/run_plan.json").read_text()) if r["item"] == item)
    dump = HERE / "raw" / ("r%02d_%s_row%02d.json" % (run, p["set"].split("_")[0], p["row"]))
    cmd = [str(ROOT / ".venv/bin/python"), str(HERE.parents[1] / "jev_cmp.py"), "record", "S2", p["set"], str(run), str(dump),
           "--row", str(p["row"])] + (["--qids", ",".join(p["qids"])] if p["qids"] else [])
    rc = subprocess.run(cmd, cwd=ROOT).returncode
    d = json.loads(dump.read_text(encoding="utf-8"))
    d = json.loads(d) if isinstance(d, str) else d
    hits = sorted({m.group(0) for m in STOP.finditer(d.get("text", "") + " " + (d.get("status_now") or ""))})
    if d.get("timed_out"):
        print("dump timed out")
    if hits:
        print("STOP WORDING:", hits)
    sys.exit(rc if rc else (3 if hits else 0))


if __name__ == "__main__":
    main()
