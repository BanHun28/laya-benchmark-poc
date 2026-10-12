"""S4 run plan and per-item Playwright fill scripts (no Jev request here).

    source env.sh && .venv/bin/python results/F/jev_cmp/sessions/S4_20261007/s4_prep.py

Part A (items 1-40): T6 SST-5, Single question / Score. The five rubric fields #rubric-0..4 get the form's `options`
verbatim ("level i: description"), which is what Laya's head reads for a score question (laya/common.py render_options:
"level %d: %s"); the S1/S2 T1 score runs sent the same rendering (S1 run 1 request body). Part B (41-60) / Part C (61-80):
T7 MASSIVE intent-10 en / de, Single question / Choice, the form's 10 `key: key spaced` options in form order; the two
languages share ids, gold and option lists. State = form `state_text` (the JSON string Laya reads), Question = form
`question`. Items are numbered by plan order; requests (jev_cmp.py `run`) are numbered in send order, so a retry takes the
next run number (s4_record.py RUN ITEM). Each raw/js/iNN_*.js fills the form, waits in window.__jev.ready() for >= 15 s on
the monotonic clock since the last Run click / evaluate request, checks the payload hash, and clicks Run only if it equals
the payload jev_cmp.py builds from the form file. dry_*.js are the same fills without the click.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import jev_cmp as J  # noqa: E402
from laya.agent import Agent  # noqa: E402
from laya.common import render_options  # noqa: E402

PARTS = (("A", "T6_sst5_40", "T6", "score", 40), ("B", "T7_massive_intent_10opt_en_20", "T7en", "choice", 20),
         ("C", "T7_massive_intent_10opt_de_20", "T7de", "choice", 20))
DRIVER = r"""
  const busyGone = async () => { for (let i = 0; i < 300 && await page.locator('button.run-button').isDisabled(); i++) await page.waitForTimeout(100); };
  if (!(await page.evaluate(() => !!(window.__jev && window.__jev.v === 'S4')))) throw new Error('instrumentation missing');
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
  if (q.type === 'score') {
    for (let i = 0; i < q.options.length; i++) await page.fill('#rubric-' + i, q.options[i]);
    if (await page.locator('#rubric-' + q.options.length).count()) throw new Error('more rubric fields than levels');
  }
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
    runs, t7 = [], {}
    for part, stem, tag, typ, n in PARTS:
        doc, items = J.load_items(stem)
        rows = laya_rows(stem)
        assert len(items) == len(rows) == n and [it["row"] for it in items] == list(range(n))
        for it in items:
            lq = rows[it["row"]]["questions"][it["qid"]]
            # the Jev input is the string Laya reads: same state JSON, same question, Laya's rendered option strings in order
            assert it["decision_type"] == typ and not it.get("jev_excluded")
            assert it["state_text"] == json.dumps(rows[it["row"]]["state"], ensure_ascii=False) and len(it["state_text"]) <= 8000
            assert it["question"] == lq["instructions"] and it["question"] == it["question"].strip()
            o = it["options"]
            assert o == render_options(Agent._to_internal(lq)), it["id"]
            assert all(1 <= len(x) <= 80 and x == x.strip() for x in o) and len({x.lower() for x in o}) == len(o), it["id"]
            assert it["gold"] == rows[it["row"]]["expected"][it["qid"]]
            if typ == "score":
                assert len(o) == 5 and o == ["level %d: %s" % (k, c) for k, c in enumerate(lq["criteria"])] and it["gold"] in range(5)
            else:
                assert len(o) == 10 and [J.key_of(x) for x in o] == list(lq["criteria"]) and it["gold_option"] in o
                assert J.key_of(it["gold_option"]) == it["gold"]
                t7.setdefault(it["row"], []).append((it["id"].split("/", 1)[1], o, it["gold"]))
            s = {"item": len(runs) + 1, "set": stem, "tag": tag, "row": it["row"], "mode": "Single question",
                 "sha12": J.sha12(J.canon(J.payload([it], False))), "state": it["state_text"], "click": True,
                 "qs": [{"qid": it["qid"], "type": typ, "question": it["question"], "options": o}]}
            runs.append((part, s))
    # T7 en and de: same MASSIVE ids, same gold and the same option list in the same order per row
    assert len(t7) == 20 and all(len(v) == 2 and v[0] == v[1] for v in t7.values())
    return runs


def script(s):
    return "async (page) => {\n  const S = %s;\n%s}\n" % (json.dumps(s, ensure_ascii=False), DRIVER)


def main():
    out = HERE / "raw/js"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for part, s in plan():
        name = "i%02d_%s_row%02d" % (s["item"], s["tag"], s["row"])
        (out / (name + ".js")).write_text(script(s), encoding="utf-8")
        if s["item"] in (1, 41, 61):  # no-click dry run of each part's first item
            (out / ("dry_" + name + ".js")).write_text(script(dict(s, click=False)), encoding="utf-8")
        rows.append({"part": part, "item": s["item"], "set": s["set"], "tag": s["tag"], "row": s["row"], "name": name,
                     "sha12": s["sha12"], "qids": None, "types": [q["type"] for q in s["qs"]]})
    (HERE / "raw/run_plan.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("%d items: %s; max option chars %d; distinct sha12 %d" % (
        len(rows), ", ".join("%s %d" % (p, sum(r["part"] == p for r in rows)) for p in "ABC"),
        max(len(o) for _, stem, *_ in PARTS for it in J.load_items(stem)[1] for o in it["options"]), len({r["sha12"] for r in rows})))


if __name__ == "__main__":
    main()
