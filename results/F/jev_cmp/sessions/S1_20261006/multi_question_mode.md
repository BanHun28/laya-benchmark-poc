# S1 exploration: jevplayground.com "Multiple questions" mode (2026-10-06)

**Verdict.** Multiple questions mode supports mixed types (choice, boolean, score), 2\~5 questions and a shared State, and returns a DECISION and probabilities per question. However, **Score accepts exactly 5 levels (0\~4) only.** 70 of T1's 80 score decisions are 4-level, and urgency (4-level) is in every workflow, so **none of the 40 cases can be entered with all 5 questions as is.** Following the prescribed rule ("cannot carry a T1 case faithfully → FALL BACK to Step 2b"), the main S1 run was switched to T2 AG News. The exploration used 1 evaluation (row 30, the 4 representable questions).

Sources: on-screen observation; the client bundle `https://jevplayground.com/_next/static/immutable/chunks/2zf_0ui8glm88.js` (module 94827: schema·payload·resultView; module 84725: Playground UI; excerpts in `raw/explore_js_schema.json`, `raw/explore_js_payload.json`); the run record `raw/r01_T1_row30_multi.json`; `S1_requests.jsonl` run 1 (the excerpts and the run records are not included in the public repository).

## 1. Confirmed facts

| Item | Finding | Evidence |
|---|---|---|
| Mode switch | Button "Multiple questions" (aria-pressed) in the group "Playground mode". Switching loads the example "Agent Action Gate (3 questions)" | Screen |
| State | A single `textarea#state`, maxlength 8000. Text: "Shared by every question below.", "All questions evaluate the same State in one Jev request." | Screen, DOM |
| Number of questions | 2\~5. "+ Add question" is disabled at 5 ("5 of 5 questions"); with 2 questions none can be removed (`canRemove: questions.length > 2`). Schema: "Add at least 2 questions." / "Use at most 5 questions." | Screen, bundle |
| Per-question type | Each question has a group "Decision type for question k" → Choice / Boolean / Score. Types can be mixed in one request (run 1: boolean, choice, score, boolean) | Screen, run 1 |
| Choice | Separate options per question, 2\~10 (`#mq-{k}-c-{i}`, "+ Add choice", "N of 10"). Labels are 1\~80 characters after trimming; case-insensitive duplicates are rejected ("Use a unique label.") | Bundle |
| Boolean | The only input is the question sentence; there are no label or description fields. "Jev returns P(true). The probability of “No” is its complement." | Screen, bundle `d()` |
| Score | The rubric inputs `#mq-{k}-r-{0..4}` ("Rubric level i", maxlength 80) are **fixed at 5 fields**, with no add or remove buttons. Defaults "No urgency / Low / Moderate / High / Critical". Schema: "Use exactly five ordered levels (0–4)." An empty field gives "Enter a label." | Screen, bundle |
| 80-character limit | Both choice and rubric have `maxLength:80`. Filling an 89-character option (`request_information: …`) **truncates it to 80 characters without any error** ("…before anything can"). A request could go out with a truncated label, so such options must be excluded beforehand | DOM probe |
| Client-side validation | zod validation on submit. On failure no request is sent, and the status "Check the highlighted fields and try again." plus field errors are shown. Clicking Run with a 4-level urgency (level 4 empty) gave `questions.4.rubric.4-error` "Enter a label." and 0 `/api/evaluate` requests (fetch wrapper 0, resource timing 0) | `shots/explore02_*.png` (screenshots are not included in the public repository) |
| Single mode | Same label and rubric rules (`validateDraft` applies the same `o()` check), so **4-level scores are impossible in Single mode too** | Bundle |
| Request format | `POST /api/evaluate`, body `{"state": …, "questions": {"q1": {"instructions": …, "type": "boolean"}, "q2": {"instructions": …, "type": "choice", "criteria": {"<label>": "<label>", …}}, "q3": {"instructions": …, "type": "score", "criteria": ["<level 0>", …, "<level 4>"]}}}`. Single mode uses `{"questions": {"decision": {…}}}`. Labels and questions are trimmed; state is sent as is. timeout 40 s | Bundle `toMultiPayload`/`toPayload`, run 1 request body |
| Response format | `{"ok": true, "model": "typesafe-ai/jev", "latencyMs": —, "result": {"answers": {"q1": {"type": "boolean", "probability": —}, "q2": {"type": "choice", "choice": "<label>", "probabilities": {…}}, "q3": {"type": "score", "score": —, "probabilities": {"0": —, "1": —, …}}}, "usage": {…}, "rounding": {"probabilityDecimals": 2, "scoreDecimals": 2}, "confidence": {"q2": —, "q3": —}, "warnings": []}}` (Jev's per-item outputs are omitted in the public repository) | run 1 response body |
| Result display | status "Evaluation complete. 4 answers returned." → "MULTIPLE DECISIONS / 4 answers in one call / Jev evaluated these questions together against the same State." → one card per question: "Question k / BOOLEAN·CHOICE·SCORE / question sentence / DECISION (SCORE for score) / value / explanation / Probability distribution / label·%" | `shots/explore04_*.png` |
| Boolean display | DECISION "Yes"/"No" ("Equally likely" when p = 0.5), bars Yes = P(true), No = 1 − P(true) | Bundle `resultView` |
| Score display | SCORE = `rubric[round(score)]`, "— / 4", "Nearest rubric level. Jev returned an interpolated score." ("Level on your submitted rubric." for an integer), bars "s — <level text>" | run 1 |
| Score meaning | `score` = Σ s·p_s, rounded to 2 decimals. The displayed level is the level nearest the expected value, so it **can differ from the argmax level** | run 1 |
| % notation | `${Number((100·p).toFixed(2))}%`. The API rounds probabilities to two decimal places (`probabilityDecimals: 2`), so they appear as integer % | Bundle, 41/41 |
| Latency notation | "N ms · server + network" = round(`latencyMs`) (41/41 match). Shorter than the browser POST | `S1_requests.jsonl` |
| View details | `<details>`: Model ID `typesafe-ai/jev`, Input tokens, Output tokens, "Normalized result. Confidence, when returned, is a separate provider statistic." + the full result JSON | run 1 |
| confidence | Present only for choice and score questions (`q2`, `q3`); absent for boolean | run 1 |
| Tokens | run 1 (4 questions): input —, output —. T2 single (4 options): input median 425, output median 68 | `S1_requests.jsonl` |

## 2. Operating recipe (Playwright MCP, exactly as used in this session)

1. `browser_navigate https://jevplayground.com/` → install the passive listeners with `browser_evaluate`: a capture-phase click listener (button text "Run Jev"), a `[role="status"]` MutationObserver, and a fetch wrapper around `/api/evaluate` only (records the request body, response text and times; the request itself is passed through unchanged). Functions `window.__jev.form/payload/precheck/ready/dump`.
2. Mode: `[role="group"][aria-label="Playground mode"] button` (first Single, second Multiple).
3. Setting the number of questions: "+ Add question" / `button[aria-label="Remove question k"]`. Type: `getByRole('group', {name: 'Decision type for question k'}).getByRole('button', {name: 'Score'})`.
4. Number of Choice options: "+ Add choice" inside the question card (switching from Boolean to Choice starts with 0 options; a new question starts with 2 empty fields).
5. Entering values: `browser_fill_form` with id selectors. `#state`, `#mq-{k}-question`, `#mq-{k}-c-{i}`, `#mq-{k}-r-{0..4}`. In Single mode: `#state`, `#question`, `#choice-{i}`, `#rubric-{0..4}`, and the type group is `[role="group"][aria-labelledby="mode-label"]`.
6. precheck: `window.__jev.ready('<sha12>')` waits 12 s after the last click, builds the same payload as the client from the form values, and compares the first 12 hex digits of its SHA-256. The expected value comes from `.venv/bin/python results/F/jev_cmp/jev_cmp.py expect <SET> [--rows R --qids a,b]`.
7. Click `button.run-button` → save `browser_evaluate window.__jev.dump()` with `filename=results/F/jev_cmp/sessions/S1_20261006/raw/rNN_*.json` (including the wait for the completion status).
8. `jev_cmp.py record S1 <SET> <run> <dump> --row R [--qids …]`: checks that the captured request body is **byte-identical** to the payload built from the form file, checks the on-screen values against the response, then appends one line each to the session JSONL and the master JSONL (exit 2 on an error).

## 3. Losses when putting T1 into this mode

| Cause | Affected decisions | Notes |
|---|---|---|
| Score rubric fixed at 5 levels | 70 / 80 score (risk 10, churn_risk 10, discrepancy_severity 10, urgency 40) | At least 1 in every one of the 40 cases. Padding a 5th level changes the scale (0\~3 → 0\~4) and the expected value, so it is no longer the same input |
| choice label 80 characters | 10 / 60 choice (customer_service/action, `jev_excluded`) | maxlength truncates silently, so a different label is sent |
| No Boolean labels | The false/true descriptions of 60 / 60 boolean | The question sentence is the same. Laya reads the `false: …`/`true: …` descriptions and Jev cannot (information asymmetry, partial loss) |

**120 / 200** decisions can be sent as is (choice 50, boolean 60, 5-level score 10). Questions per case are agent_trace 3 (action, needs_review, outcome), customer_service 2 (category, needs_human), invoice 3 (disposition, duplicate, matches_order), security 4 (credential_compromise, disposition, severity, true_positive), all meeting the Multiple questions minimum of 2.

Options for proceeding with T1 (decision needed):

| Option | Content | Jev requests | Cost |
|---|---|---|---|
| A | Multiple questions, 1 per case, representable questions only (2\~4) | 40; 39 because row 30 has the same payload as run 1 | With only 10 scores, score MAE effectively drops out. The question mix differs from upstream typed-decisions (Jev 0.727), which weakens the representativeness check |
| B | Pad a 5th level onto the 4-level questions and run everything | 40 | Inputs differ from Laya's (scale change). Reportable only as a separate variant |
| C | Single mode, 1 per representable decision | 120 | The same 120 decisions as A, but 3 times the requests. Conditions are closer to Laya, which evaluates questions separately (Jev multi evaluates "together") |

The plan's 7.1 estimate of "about 200 requests when run per question in Single" becomes **at most 120 requests**, because 4-level scores are blocked in Single as well.

## 4. The 1 exploration run: T1 row 30 (security_incidents_000017), 4 questions

payload sha12 `5a9e5492744b` (2,077 B, byte-identical to the form file). urgency (4-level) was omitted (recorded as `omitted`).

| Question | gold | Jev | Laya english | Laya multilingual | teacher soft |
|---|---|---|---|---|---|
| credential_compromise (boolean) | true | — | true (0.79) | true (0.99) | [0.37, 0.63] |
| disposition (choice) | investigate | — | X close_benign (0.35) | X monitor (0.92) | investigate 0.67 |
| severity (score, 5 levels) | 2 (teacher score 1.62) | — | E[level] 1.62 | E[level] 1.02 | [0.07, 0.37, 0.45, 0.11, 0.01] |
| true_positive (boolean) | true | — | true (0.65) | true (0.99) | [0.22, 0.78] |

Because argmax-level and nearest-level correctness can disagree, the comparison rule for score questions (argmax-level accuracy + E[level] MAE) must be fixed in advance for T6 and T1. With 1 case, this is not used as an accuracy figure. Model ID `typesafe-ai/jev`.

## 5. Implications for the other tasks

- T6 SST-5 has 5 levels, so it fits the Score rubric as is (options up to 22 characters). T6 comparison rule: argmax-level accuracy; MAE of Jev `score` (= E[level]) and of Laya E[level] against the gold level.
- T3·T4·T7 (choice, up to 50 characters) and T5·T8 (boolean; Laya has no criteria either) do not hit the Single-mode constraints (full check of the form files: 0 over 80 characters, 0 over 10 options).
- Multiple questions with 4 questions also had a latency similar to single with 1 question (median 234 ms, 68 tokens). Getting several decisions in one request has a cost advantage, but tasks other than T1 have a single question, so it does not apply.

## 6. Screenshots (not included in the public repository)

- `shots/explore01_form_row30_all5q_urgency_4levels.png`: the form with all 5 questions of row 30 (urgency level 4 empty).
- `shots/explore02_validation_blocked_4level_rubric_no_request.png`: the client-side validation block after clicking Run (no request).
- `shots/explore03_form_row30_4q_representable.png`: the 4-question form after removing urgency (precheck matched).
- `shots/explore04_result_row30_4q_details_open.png`: the 4-question result with View details.

**English** | [한국어](multi_question_mode.ko.md)
