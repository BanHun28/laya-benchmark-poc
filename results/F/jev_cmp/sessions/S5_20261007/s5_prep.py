"""S5 run plan and per-item Playwright fill scripts (no Jev request here).

    source env.sh && .venv/bin/python results/F/jev_cmp/sessions/S5_20261007/s5_prep.py

Part A (items 1-20) / B (21-40) / C (41-60): T7 MASSIVE intent-10 ja / zh-CN / ko, Single question / Choice, the form's 10
`key: key spaced` options in form order (Laya render_options of the row's criteria); every row has the same MASSIVE id,
gold and option list as the en/de rows S4 sent. Part D (61-100): T8 prompt-injections, Single question / Boolean (no
label or description field; Laya's noul has no criteria either). State = form `state_text`, the string Laya reads
(laya/common.py serialize_state: json.dumps(state, ensure_ascii=False), so native characters, no \\u escapes); Question =
form `question`. Items are numbered by plan order; requests (jev_cmp.py `run`) are numbered in send order, so a retry
takes the next run number (s5_record.py RUN ITEM). Each raw/js/iNNN_*.js fills the form, waits in window.__jev.ready()
for >= 15 s on the monotonic clock since the last Run click / evaluate request, checks the payload hash and the session
cap, and clicks Run only if the hash equals the payload jev_cmp.py builds from the form file. dry_*.js are the same
fills without the click.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import jev_cmp as J  # noqa: E402
from laya.agent import Agent  # noqa: E402
from laya.common import render_options, serialize_state  # noqa: E402

PARTS = (("A", "T7_massive_intent_10opt_ja_20", "T7ja", "choice", 20), ("B", "T7_massive_intent_10opt_zh-CN_20", "T7zh", "choice", 20),
         ("C", "T7_massive_intent_10opt_ko_20", "T7ko", "choice", 20), ("D", "T8_prompt_injections_40", "T8", "boolean", 40))
T7_EN = "T7_massive_intent_10opt_en_20"
DRIVER = r"""
  const busyGone = async () => { for (let i = 0; i < 300 && await page.locator('button.run-button').isDisabled(); i++) await page.waitForTimeout(100); };
  if (!(await page.evaluate(() => !!(window.__jev && window.__jev.v === 'S5')))) throw new Error('instrumentation missing');
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
    runs, native = [], {}
    en = {it["row"]: it for it in J.load_items(T7_EN)[1]}
    for part, stem, tag, typ, n in PARTS:
        doc, items = J.load_items(stem)
        rows = laya_rows(stem)
        assert len(items) == len(rows) == n and [it["row"] for it in items] == list(range(n))
        native[tag] = 0
        for it in items:
            lq = rows[it["row"]]["questions"][it["qid"]]
            # the Jev input is the string Laya reads: same state JSON (native characters), same question, same option strings in order
            assert it["decision_type"] == typ and not it.get("jev_excluded")
            st = it["state_text"]
            assert st == serialize_state(rows[it["row"]]["state"]) == json.dumps(rows[it["row"]]["state"], ensure_ascii=False) and len(st) <= 8000
            assert "\\u" not in st and json.loads(st) == rows[it["row"]]["state"], it["id"]
            native[tag] += any(ord(c) > 127 for c in st)
            assert it["question"] == lq["instructions"] and it["question"] == it["question"].strip()
            if typ == "choice":
                o = it["options"]
                assert o == render_options(Agent._to_internal(lq)), it["id"]
                assert all(1 <= len(x) <= 80 and x == x.strip() for x in o) and len({x.lower() for x in o}) == len(o) == 10, it["id"]
                assert [J.key_of(x) for x in o] == list(lq["criteria"]) and it["gold"] == rows[it["row"]]["expected"][it["qid"]]
                assert it["gold_option"] in o and J.key_of(it["gold_option"]) == it["gold"]
                e = en[it["row"]]  # same MASSIVE id, gold and option list (same order) as the en row S4 sent
                assert (e["id"].split("/", 1)[1], e["gold"], e["options"], e["question"]) == (it["id"].split("/", 1)[1], it["gold"], o, it["question"])
            else:
                assert lq["type"] == "noul" and "criteria" not in lq and isinstance(it["gold"], bool)
                assert it["gold"] == rows[it["row"]]["expected"][it["qid"]]
            s = {"item": len(runs) + 1, "set": stem, "tag": tag, "row": it["row"], "mode": "Single question",
                 "sha12": J.sha12(J.canon(J.payload([it], False))), "state": st, "click": True,
                 "qs": [{"qid": it["qid"], "type": typ, "question": it["question"], "options": it["options"] if typ == "choice" else []}]}
            runs.append((part, s))
    assert sum(r[1]["set"].startswith("T8") and J.load_items("T8_prompt_injections_40")[1][r[1]["row"]]["gold"] for r in runs) == 20
    return runs, native


def script(s):
    return "async (page) => {\n  const S = %s;\n%s}\n" % (json.dumps(s, ensure_ascii=False), DRIVER)


def main():
    out = HERE / "raw/js"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    runs, native = plan()
    for part, s in runs:
        name = "i%03d_%s_row%02d" % (s["item"], s["tag"], s["row"])
        (out / (name + ".js")).write_text(script(s), encoding="utf-8")
        if s["item"] in (1, 21, 41, 61):  # no-click dry run of each part's first item
            (out / ("dry_" + name + ".js")).write_text(script(dict(s, click=False)), encoding="utf-8")
        rows.append({"part": part, "item": s["item"], "set": s["set"], "tag": s["tag"], "row": s["row"], "name": name,
                     "sha12": s["sha12"], "qids": None, "types": [q["type"] for q in s["qs"]]})
    (HERE / "raw/run_plan.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("%d items: %s; states with non-ASCII characters %s; max option chars %d; max state chars %d; distinct sha12 %d" % (
        len(rows), ", ".join("%s %d" % (p, sum(r["part"] == p for r in rows)) for p in "ABCD"), native,
        max(len(o) for _, s in runs for o in s["qs"][0]["options"]), max(len(s["state"]) for _, s in runs), len({r["sha12"] for r in rows})))


if __name__ == "__main__":
    main()
