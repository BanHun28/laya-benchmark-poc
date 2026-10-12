"""S3 run plan and per-item Playwright fill scripts (no Jev request here).

    .venv/bin/python results/F/jev_cmp/sessions/S3_20261007/s3_prep.py

Part A (items 1-40): T4 Banking77-10, Single question / Choice, the form file's 10 key-only options in form order.
Part B (items 41-80): T5 BoolQ, Single question / Boolean (no label or description field; Laya's noul has no criteria).
State = form `state_text` (the JSON string Laya reads), Question = form `question`. Items are numbered by plan order;
requests (jev_cmp.py `run`) are numbered in send order, so a retry takes the next run number (s3_record.py RUN ITEM).
Each raw/js/iNN_*.js fills the form, waits in window.__jev.ready() for >= 15 s on the monotonic clock since the last
Run click / evaluate request and checks the payload hash, and clicks Run only if the hash equals the payload jev_cmp.py
builds from the form file. dry_*.js are the same fills without the click.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import jev_cmp as J  # noqa: E402

DRIVER = r"""
  const busyGone = async () => { for (let i = 0; i < 300 && await page.locator('button.run-button').isDisabled(); i++) await page.waitForTimeout(100); };
  if (!(await page.evaluate(() => !!(window.__jev && window.__jev.v === 'S3')))) throw new Error('instrumentation missing');
  await busyGone();
  const TL = { choice: 'Choice', boolean: 'Boolean', score: 'Score' };
  const modeBtn = page.getByRole('group', { name: 'Playground mode' }).getByRole('button', { name: S.mode, exact: true });
  if ((await modeBtn.getAttribute('aria-pressed')) !== 'true') await modeBtn.click();
  const setChoices = async (scope, sel, n) => {
    let m = await scope.locator(sel).count();
    while (m < n) { await scope.getByRole('button', { name: '+ Add choice' }).click(); m++; }
    while (m > n) { await scope.getByRole('button', { name: 'Remove choice ' + m, exact: true }).click(); m--; }
  };
  const q = S.qs[0];
  const tb = page.getByRole('group', { name: 'Decision type', exact: true }).getByRole('button', { name: TL[q.type], exact: true });
  if ((await tb.getAttribute('aria-pressed')) !== 'true') await tb.click();
  if (q.type === 'choice') await setChoices(page.locator('form'), 'input[id^="choice-"]', q.options.length);
  await page.fill('#question', q.question);
  if (q.type === 'choice') for (let i = 0; i < q.options.length; i++) await page.fill('#choice-' + i, q.options[i]);
  await page.fill('#state', S.state);
  const pre = await page.evaluate((sha) => window.__jev.ready(sha, 15000), S.sha12);
  if (!pre.ok || !S.click) return { item: S.item, row: S.row, pre, clicked: false };
  await page.locator('button.run-button').click();
  return { item: S.item, row: S.row, pre, clicked: true };
"""


def laya_rows(stem):
    lines = (J.DATA / (stem + ".jsonl")).read_text(encoding="utf-8").splitlines()
    return [json.loads(x) for x in lines if x.strip() and not x.startswith("#")]


def plan():
    runs = []
    for part, stem, typ in (("A", "T4_banking77_10opt_40", "choice"), ("B", "T5_boolq_40", "boolean")):
        doc, items = J.load_items(stem)
        rows = laya_rows(stem)
        assert len(items) == len(rows) == 40 and [it["row"] for it in items] == list(range(40))
        for it in items:
            lq = rows[it["row"]]["questions"][it["qid"]]
            # the Jev input is the string Laya reads: same state JSON, same question, same option strings in the same order
            assert it["decision_type"] == typ and not it.get("jev_excluded")
            assert it["state_text"] == json.dumps(rows[it["row"]]["state"], ensure_ascii=False) and len(it["state_text"]) <= 8000
            assert it["question"] == lq["instructions"] and it["question"] == it["question"].strip()
            if typ == "choice":
                o = it["options"]
                assert len(o) == 10 and all(1 <= len(x) <= 80 and x == x.strip() for x in o), it["id"]
                assert len({x.lower() for x in o}) == 10 and o == list(lq["criteria"]) and it["gold"] in o
            else:
                assert lq["type"] == "noul" and "criteria" not in lq and isinstance(it["gold"], bool)
            s = {"item": len(runs) + 1, "set": stem, "row": it["row"], "mode": "Single question",
                 "sha12": J.sha12(J.canon(J.payload([it], False))), "state": it["state_text"], "click": True,
                 "qs": [{"qid": it["qid"], "type": typ, "question": it["question"],
                         "options": it["options"] if typ == "choice" else []}]}
            runs.append((part, s))
    return runs


def script(s):
    return "async (page) => {\n  const S = %s;\n%s}\n" % (json.dumps(s, ensure_ascii=False), DRIVER)


def main():
    out = HERE / "raw/js"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for part, s in plan():
        name = "i%02d_%s_row%02d" % (s["item"], s["set"].split("_")[0], s["row"])
        (out / (name + ".js")).write_text(script(s), encoding="utf-8")
        if s["item"] in (1, 41):  # no-click dry run of each part's first item
            (out / ("dry_" + name + ".js")).write_text(script(dict(s, click=False)), encoding="utf-8")
        rows.append({"part": part, "item": s["item"], "set": s["set"], "row": s["row"], "name": name, "sha12": s["sha12"],
                     "qids": None, "types": [q["type"] for q in s["qs"]]})
    (HERE / "raw/run_plan.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("%d items: A %d, B %d; max option chars %d" % (
        len(rows), sum(r["part"] == "A" for r in rows), sum(r["part"] == "B" for r in rows),
        max(len(o) for it in J.load_items("T4_banking77_10opt_40")[1] for o in it["options"])))


if __name__ == "__main__":
    main()
