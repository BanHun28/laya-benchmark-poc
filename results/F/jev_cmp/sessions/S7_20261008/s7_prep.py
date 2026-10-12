"""S7 run plan and per-item Playwright fill scripts (no Jev request here).

    source env.sh && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python results/F/jev_cmp/sessions/S7_20261008/s7_prep.py

Part A (items 1-40): T9 Enron spam, Single question / Boolean (no label or description field; Laya's noul has no
criteria either, so both systems get the question sentence only). Part B (items 41-80): T10 support-ticket queue,
Single question / Choice, the form's 10 `key: description` options in form order (Laya render_options of the row's
criteria; the same 10-way list on every row). State = form `state_text`, the string Laya reads (laya/common.py
serialize_state: json.dumps(state, ensure_ascii=False), so native characters, no \\u escapes); Question = form
`question`. Items are numbered by plan order; requests (jev_cmp.py `run`) are numbered in send order, so a retry takes
the next run number (s7_record.py RUN ITEM). Each raw/js/iNNN_*.js fills the form, waits in window.__jev.ready() for
>= 15 s on the monotonic clock since the last Run click / evaluate request, checks the payload hash and the session cap
(90), and clicks Run only if the hash equals the payload jev_cmp.py builds from the form file. dry_*.js are the same
fills without the click (each part's first item, T9's longest state and the T9 state with a C1 control character) and
also return the form's DOM view (value equality, lengths, maxlength, the State counter).
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import jev_cmp as J  # noqa: E402
from laya.agent import Agent  # noqa: E402
from laya.common import render_options, serialize_state  # noqa: E402

PARTS = (("A", "T9_enron_spam_40", "T9", "boolean", 40), ("B", "T10_support_tickets_queue_40", "T10", "choice", 40))
BODY_CHARS = 3000  # upstream state = email/ticket subject + body[:3000] (bench_apps.py, MANIFEST question_source)
# the stop-wording patterns of s7_record.py and instrument.js: no input string may match them, so a match on the page
# can only come from the site
STOP = re.compile(r"rate.?limit|too many requests|usage limit (reached|exceeded)|limit (reached|exceeded)|quota|slow down|unusual traffic"
                  r"|captcha|verify (that )?you are (a )?human|temporarily unavailable|try again later|access denied", re.I)
DRIVER = r"""
  const busyGone = async () => { for (let i = 0; i < 300 && await page.locator('button.run-button').isDisabled(); i++) await page.waitForTimeout(100); };
  if (!(await page.evaluate(() => !!(window.__jev && window.__jev.v === 'S7')))) throw new Error('instrumentation missing');
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
  // dry run only: what the form holds (read-only DOM view, no click)
  const DOM = (s) => {
    const st = document.getElementById('state'), qe = document.getElementById('question');
    const cs = Array.from(document.querySelectorAll('input[id^="choice-"]'));
    const leaf = Array.from(document.querySelectorAll('form *')).filter((e) => !e.children.length).map((e) => (e.textContent || '').trim());
    return { state_equal: !!st && st.value === s.state, state_len: st ? st.value.length : null, state_maxlength: st ? st.maxLength : null,
             state_counter: leaf.find((t) => /^[\d,]+ \/ [\d,]+$/.test(t)) || null,
             question_equal: !!qe && qe.value === s.qs[0].question, question_maxlength: qe ? qe.maxLength : null,
             choices_equal: JSON.stringify(cs.map((c) => c.value)) === JSON.stringify(s.qs[0].options),
             choices: cs.map((c) => ({ id: c.id, len: c.value.length, maxlength: c.maxLength })),
             run_disabled: (document.querySelector('button.run-button') || {}).disabled,
             alerts: Array.from(document.querySelectorAll('[role="alert"]')).map((e) => e.innerText).filter((t) => t && t.trim()),
             invalid: Array.from(document.querySelectorAll('form :invalid')).map((e) => e.id || e.name || e.tagName) };
  };
  if (!S.click) return { item: S.item, row: S.row, pre, clicked: false, dom: await page.evaluate(DOM, S) };
  if (!pre.ok) return { item: S.item, row: S.row, pre, clicked: false };
  await page.locator('button.run-button').click();
  return { item: S.item, row: S.row, pre, clicked: true };
"""


def laya_rows(stem):
    lines = (J.DATA / (stem + ".jsonl")).read_text(encoding="utf-8").splitlines()
    return [json.loads(x) for x in lines if x.strip() and not x.startswith("#")]


def c1(s):
    return [hex(ord(c)) for c in s if 0x80 <= ord(c) <= 0x9F]


def plan():
    runs, notes = [], {}
    for part, stem, tag, typ, n in PARTS:
        doc, items = J.load_items(stem)
        rows = laya_rows(stem)
        assert len(items) == len(rows) == n and [it["row"] for it in items] == list(range(n))
        assert all(r["language"] == "en" for r in rows)
        for it in items:
            r = rows[it["row"]]
            lq = r["questions"][it["qid"]]
            # the Jev input is the string Laya reads: same state JSON (native characters), same question, same option strings in order
            assert it["decision_type"] == typ and not it.get("jev_excluded")
            st = it["state_text"]
            assert st == serialize_state(r["state"]) == json.dumps(r["state"], ensure_ascii=False) and len(st) <= 8000
            assert "\\u" not in st and json.loads(st) == r["state"], it["id"]
            assert "\r" not in st and "\n" not in st  # a textarea normalizes CR / CRLF; JSON escapes both, so none may be raw
            assert set(r["state"]) == {"subject", "body"} and len(r["state"]["body"]) <= BODY_CHARS, it["id"]
            assert it["question"] == lq["instructions"] and it["question"] == it["question"].strip()
            o = it["options"]
            assert o == render_options(Agent._to_internal(lq)), it["id"]  # T9: the noul texts Laya reads; Jev Boolean takes none
            assert not any(STOP.search(x) for x in [st, it["question"]] + o), it["id"]
            assert it["gold"] == r["expected"][it["qid"]]
            if typ == "choice":
                assert all(1 <= len(x) <= 80 and x == x.strip() for x in o) and len({x.lower() for x in o}) == len(o) == 10, it["id"]
                assert o == ["%s: %s" % kv for kv in lq["criteria"].items()]  # criteria rendering `key: description`
                assert [J.key_of(x) for x in o] == list(lq["criteria"]) and ":" not in "".join(lq["criteria"])
                assert it["gold_option"] in o and J.key_of(it["gold_option"]) == it["gold"]
            else:
                assert lq["type"] == "noul" and "criteria" not in lq and "labels" not in lq and isinstance(it["gold"], bool)
            s = {"item": len(runs) + 1, "set": stem, "tag": tag, "row": it["row"], "mode": "Single question",
                 "sha12": J.sha12(J.canon(J.payload([it], False))), "state": st, "click": True,
                 "qs": [{"qid": it["qid"], "type": typ, "question": it["question"], "options": it["options"] if typ == "choice" else []}]}
            runs.append((part, s))
        pr = [s for p, s in runs if p == part]
        notes[tag] = {"max_state_chars": max(len(s["state"]) for s in pr), "max_body_chars": max(len(x["state"]["body"]) for x in rows),
                      "longest_item": max(pr, key=lambda s: len(s["state"]))["item"], "non_ascii_states": sum(any(ord(c) > 127 for c in s["state"]) for s in pr),
                      "c1_items": [s["item"] for s in pr if c1(s["state"])], "gold": dict(sorted(Counter(str(x["gold"]) for x in items).items()))}
        if typ == "choice":
            assert len({tuple(it["options"]) for it in items}) == 1  # one fixed 10-way list
            notes[tag]["max_option_chars"] = max(len(x) for x in items[0]["options"])
    assert sum(r[1]["set"].startswith("T9") and J.load_items("T9_enron_spam_40")[1][r[1]["row"]]["gold"] for r in runs) == 20
    return runs, notes


def script(s):
    return "async (page) => {\n  const S = %s;\n%s}\n" % (json.dumps(s, ensure_ascii=False), DRIVER)


def main():
    out = HERE / "raw/js"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    runs, notes = plan()
    dry = {1, 41, notes["T9"]["longest_item"], *notes["T9"]["c1_items"]}
    for part, s in runs:
        name = "i%03d_%s_row%02d" % (s["item"], s["tag"], s["row"])
        (out / (name + ".js")).write_text(script(s), encoding="utf-8")
        if s["item"] in dry:  # no-click dry runs
            (out / ("dry_" + name + ".js")).write_text(script(dict(s, click=False)), encoding="utf-8")
        rows.append({"part": part, "item": s["item"], "set": s["set"], "tag": s["tag"], "row": s["row"], "name": name,
                     "sha12": s["sha12"], "qids": None, "types": [q["type"] for q in s["qs"]]})
    (HERE / "raw/run_plan.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("%d items: %s; distinct sha12 %d; dry runs %s" % (len(rows), ", ".join("%s %d" % (p, sum(r["part"] == p for r in rows)) for p in "AB"),
                                                             len({r["sha12"] for r in rows}), sorted(dry)))
    for tag, v in notes.items():
        print(tag, json.dumps(v, ensure_ascii=False))


if __name__ == "__main__":
    main()
