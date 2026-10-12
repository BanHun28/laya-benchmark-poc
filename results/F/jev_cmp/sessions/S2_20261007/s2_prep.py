"""S2 run plan and per-run Playwright fill scripts (no Jev request here).

    .venv/bin/python results/F/jev_cmp/sessions/S2_20261007/s2_prep.py

Items are numbered by plan order; requests (jev_cmp.py `run`) are numbered in send order, so a retry takes the next
run number and later items shift (s2_record.py RUN ITEM). Part A (items 1-39): T1 typed-decisions, one Multiple-questions run per case with the case's non-excluded questions in
form order; row 30 is not resent (S1 run 1 sent the same payload, sha12 5a9e5492744b). Part B (items 40-79): T3 emotion,
Single question / Choice. Each raw/js/iNN_*.js fills the form, waits in window.__jev.ready() for >= 12 s since the last
Run click and the payload hash, and clicks Run only if the hash equals the payload jev_cmp.py builds from the form file.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import jev_cmp as J  # noqa: E402

S1_ROW30_SHA12 = "5a9e5492744b"
DRIVER = r"""
  const busyGone = async () => { for (let i = 0; i < 300 && await page.locator('button.run-button').isDisabled(); i++) await page.waitForTimeout(100); };
  if (!(await page.evaluate(() => !!(window.__jev && window.__jev.v === 'S2')))) throw new Error('instrumentation missing');
  await busyGone();
  const TL = { choice: 'Choice', boolean: 'Boolean', score: 'Score' };
  const modeBtn = page.getByRole('group', { name: 'Playground mode' }).getByRole('button', { name: S.mode, exact: true });
  if ((await modeBtn.getAttribute('aria-pressed')) !== 'true') await modeBtn.click();
  const setChoices = async (scope, sel, n) => {
    let m = await scope.locator(sel).count();
    while (m < n) { await scope.getByRole('button', { name: '+ Add choice' }).click(); m++; }
    while (m > n) { await scope.getByRole('button', { name: 'Remove choice ' + m, exact: true }).click(); m--; }
  };
  if (S.mode === 'Multiple questions') {
    const cards = page.locator('section.question-card');
    while ((await cards.count()) < S.qs.length) await page.getByRole('button', { name: '+ Add question' }).click();
    while ((await cards.count()) > S.qs.length) await page.getByRole('button', { name: 'Remove question ' + (await cards.count()), exact: true }).click();
    for (let k = 0; k < S.qs.length; k++) {
      const q = S.qs[k];
      const tb = page.getByRole('group', { name: 'Decision type for question ' + (k + 1), exact: true }).getByRole('button', { name: TL[q.type], exact: true });
      if ((await tb.getAttribute('aria-pressed')) !== 'true') await tb.click();
      const card = page.locator('section.question-card[aria-labelledby="mq-' + k + '-title"]');
      if (q.type === 'choice') await setChoices(card, 'input[id^="mq-' + k + '-c-"]', q.options.length);
      await page.fill('#mq-' + k + '-question', q.question);
      if (q.type === 'choice') for (let i = 0; i < q.options.length; i++) await page.fill('#mq-' + k + '-c-' + i, q.options[i]);
      if (q.type === 'score') for (let i = 0; i < q.options.length; i++) await page.fill('#mq-' + k + '-r-' + i, q.options[i]);
    }
  } else {
    const q = S.qs[0];
    const tb = page.getByRole('group', { name: 'Decision type', exact: true }).getByRole('button', { name: TL[q.type], exact: true });
    if ((await tb.getAttribute('aria-pressed')) !== 'true') await tb.click();
    if (q.type === 'choice') await setChoices(page.locator('form'), 'input[id^="choice-"]', q.options.length);
    await page.fill('#question', q.question);
    if (q.type === 'choice') for (let i = 0; i < q.options.length; i++) await page.fill('#choice-' + i, q.options[i]);
    if (q.type === 'score') for (let i = 0; i < q.options.length; i++) await page.fill('#rubric-' + i, q.options[i]);
  }
  await page.fill('#state', S.state);
  const pre = await page.evaluate((sha) => window.__jev.ready(sha, 15000), S.sha12);
  if (!pre.ok || !S.click) return { item: S.item, row: S.row, pre, clicked: false };
  await page.locator('button.run-button').click();
  return { item: S.item, row: S.row, pre, clicked: true };
"""


def spec(item, stem, row, its, multi):
    return {"item": item, "set": stem, "row": row, "mode": "Multiple questions" if multi else "Single question",
            "sha12": J.sha12(J.canon(J.payload(its, multi))), "state": its[0]["state_text"], "click": True,
            "qs": [{"qid": it["qid"], "type": it["decision_type"], "question": it["question"], "options": it["options"]} for it in its]}


def plan():
    runs = []
    _, t1 = J.load_items("T1_typed_decisions_40")
    for row in sorted({it["row"] for it in t1}):
        qids = [it["qid"] for it in t1 if it["row"] == row and not it.get("jev_excluded")]
        its = J.row_items(t1, row, qids)
        if row == 30:
            assert J.sha12(J.canon(J.payload(its, True))) == S1_ROW30_SHA12  # reused from S1, not resent
            continue
        assert 2 <= len(its) <= 5 and all(len(o) <= 80 for it in its for o in it["options"])
        assert all(len(it["options"]) == 5 for it in its if it["decision_type"] == "score")
        runs.append(("A", spec(len(runs) + 1, "T1_typed_decisions_40", row, its, True), qids))
    _, t3 = J.load_items("T3_emotion_40")
    opts = t3[0]["options"]
    for it in t3:
        assert it["options"] == opts and len(opts) == 6 and all(len(o) <= 80 for o in opts) and it["decision_type"] == "choice"
        runs.append(("B", spec(len(runs) + 1, "T3_emotion_40", it["row"], [it], False), None))
    return runs


def main():
    out = HERE / "raw/js"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for part, s, qids in plan():
        name = "i%02d_%s_row%02d" % (s["item"], s["set"].split("_")[0], s["row"])
        (out / (name + ".js")).write_text("async (page) => {\n  const S = %s;\n%s}\n" % (json.dumps(s, ensure_ascii=False), DRIVER),
                                          encoding="utf-8")
        rows.append({"part": part, "item": s["item"], "set": s["set"], "row": s["row"], "name": name, "sha12": s["sha12"],
                     "qids": qids, "types": [q["type"] for q in s["qs"]]})
    (HERE / "raw/run_plan.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("%d runs: A %d, B %d" % (len(rows), sum(r["part"] == "A" for r in rows), sum(r["part"] == "B" for r in rows)))


if __name__ == "__main__":
    main()
