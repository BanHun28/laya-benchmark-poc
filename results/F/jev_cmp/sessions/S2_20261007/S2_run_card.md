# Run 20261007-0849_jev-playground_S2 (T1_typed_decisions_40 option A 39 + T3_emotion_40)

| Item | Value |
|---|---|
| run_id | 20261007-0849_jev-playground_S2 (Track F, Laya vs Jev comparison session S2: T1 option A, 39 cases + T3 DAIR Emotion 40) |
| Date / start time | 2026-10-07 (KST). Reading materials about 08:41, page load 08:46:26, first evaluation click 08:49:40.382, last evaluation click 09:12:47.969, browser closed about 09:13, analysis and write-up 09:13\~09:25 |
| Track / PoC phase | F (`docs/09_laya_vs_jev_plan.md` §7 S2, §7.2 day 2) |
| Hypothesis | None applies. There is no direct Jev comparison hypothesis among H1\~H10. The question is "On the same inputs, how do Jev and Laya (english / multilingual / Router) differ in answers, probabilities and latency?" |
| Purpose (one line) | Send T1's Jev-comparable decisions (option A, 1 Multiple questions request per case) and T3 Emotion 40 to Jev and compare them pairwise with Laya on the same decisions |
| Commands | Plan and input scripts: `.venv/bin/python results/F/jev_cmp/sessions/S2_20261007/s2_prep.py` (computes sha12 with `jev_cmp.py` `payload`/`row_items` and generates the per-item `raw/js/iNN_*.js` (`raw/js/` is not included in the public repository); asserts that row 30 equals the S1 payload and excludes it). Browser: Playwright MCP `browser_navigate https://jevplayground.com/` → `browser_run_code_unsafe raw/js/instrument.js` (passive listeners + `/api/evaluate` fetch wrapper) → for each item `browser_run_code_unsafe raw/js/iNN_*.js` (fill the form → `window.__jev.ready(sha12, 15000)` → click `button.run-button` only if the hash matches) → save `browser_evaluate window.__jev.dump()` to `raw/rNN_<T>_rowRR.json` (not included in the public repository) → `.venv/bin/python …/s2_record.py RUN ITEM` (= `jev_cmp.py record S2 <SET> RUN DUMP --row R [--qids …]` + stop-message check). Analysis: `.venv/bin/python results/F/jev_cmp/jev_cmp.py t1 S1,S2`, `… analyze S2 T3_emotion_40` |
| Environment record | No local model run. Browser: Playwright MCP Chromium. Target: jevplayground.com `POST /api/evaluate`. Laya figures were read from the S0 reports (CPU fp32) |
| Checkpoint | Jev: response `model` and View details Model ID `typesafe-ai/jev` 79/79, no version shown. Laya english / multilingual / typed-decisions revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` (report config.revisions); Router chose english for all of T1 120 and T3 40 |
| Dataset | T1: `data/evals/jev_cmp/T1_typed_decisions_40.jsonl`, 40 cases / 200 decisions (120 Jev-comparable), dataset_sha256 `749a24c4c0db977686f29eeecd41201e16b97629a9fbd641a6ffb5dfe6163834`, questions_sha256 `d46ef26a6ec2f2f8c6fc0cfa1e81715751dda05f173cd028ae3eaaa4b9d519cb` (report config), form `T1_typed_decisions_40_playground.json` sha256 `b0eacae8e2ee78fe8372d910da3a1d6c7cad7be4e4a623c101db4fe1c3a6af65`. noul no-criteria variant: dataset_sha256 `2508b8172b70cd65f02d1e7ba21dca97ebd7d6603b3ee9f7ad8a057e06b50283`, questions_sha256 `7b7f5dac86a48ee9fc492bbb9b29e1a406444c311578f902e6d93097c08dbd25`. T3: `T3_emotion_40.jsonl`, n=40, dataset_sha256 `2246b5f04b1ed714ef9789548d6e0cf932db1fa40aed95a4b9a3f616a11510cb`, questions_sha256 `bd7cc49e3561bf50d45db8c2d35820b8ddea855c9dfbc081303636596b4b4c97`, form sha256 `4b0becf94e58d6b6e221028f4783bbdca8c2b953f0ab3120c90bac111fa65356` |
| Device / precision / threads | Jev: hosted, unknown. Laya: per the S0 reports, CPU fp32, intra-op 10 / inter-op 1, batch 8 |
| Parameters | Part A: Multiple questions; the case's comparable questions (agent_trace 3, customer_service 2, invoice 3, security 4) entered in form order. Choice labels are `key: description` (up to 78 characters), the score rubric is 5 fields `level k: …`, Boolean takes the question sentence only. Part B: Single question / Choice, 6 options in fixed order, Question ``Which emotion is most strongly expressed in `text`?``, State = form `state_text`. Operation: Run gap guard 12 s (runs 1\~4) → 15 s (runs 5\~), monotonic-based from run 62. On a 5xx, 1 retry after 60 s; immediate stop on a 429, limit message or captcha |
| Repetitions / warm-up | Single pass, no warm-up. 1 success per item (attempt 2 for row 0 only) |
| Duration | Browser session about 27 min (evaluation window 23 min 8 s). Whole task about 45 min (reading and preparation about 6 min, browser 27 min, analysis and write-up about 12 min) |

## Results

| Metric | Value | Upstream reference (source) | Difference | Notes |
|---|---|---|---|---|
| T1 accuracy, Jev (120 decisions) | 104/120 = 0.867 [0.794, 0.916] | Jev 0.727 (BENCHMARKS.md, 3rd-party, 2,000 decisions; `docs/09_laya_vs_jev_plan.md` §1) | +0.140 | Different question mix (70 4-level scores and 10 choices over 80 characters excluded). On the same subset Laya english also goes 0.330 → 0.383 |
| T1 accuracy, Laya english / multilingual / Router (same 120) | 0.383 / 0.367 / 0.383 | 0.362 / 0.352 (BENCHMARKS.md, 2,000 decisions) | | Below the per-question majority baseline of 0.575 |
| T1 accuracy, Laya typed-decisions (fine-tuned reference line) | 104/120 = 0.867 | 0.766 (same source) | | Jev vs this checkpoint b=10 / c=10, p=1.0 |
| choice_accuracy | T1 Jev 42/50 = 0.840 [0.715, 0.917]; T3 Jev 28/40 = 0.700 [0.546, 0.819] | T1 Laya en 0.280 / ml 0.320; T3 Jev 0.480 (3rd-party, 100 items), Laya en 0.573 (upstream T4) | T3 Jev +0.220 | The T3 sample is on the easy side (Laya en also +0.177) |
| noul_accuracy | T1 Jev 56/60 = 0.933 [0.841, 0.974] | Laya en 0.467 (no-criteria 0.517), ml 0.433 (0.417), `laya_summary.md` §2b | | Even on identical inputs (no-criteria): b=27 / c=2 (en), 34 / 3 (ml) |
| score (10 with 5 levels) | argmax 6/10 = 0.600; MAE \|E[level] − teacher\| 0.389 | Jev MAE 0.391 (3rd-party, 2,000 decisions); Laya en 0.400 / 0.584 | | n=10 |
| T1 soft accuracy / Brier vs soft | 0.590 / 0.077 | Jev 0.580 / 0.148 (3rd-party) | +0.010 / −0.071 | Jev probabilities rounded to 2 decimals |
| ece | T1 0.181, T3 0.278 (15 bins) | Jev typed-decisions 0.144, nibzard 0.246 (09 §1) | | T1 underconfident, T3 overconfident |
| mean_confidence (Jev displayed top p) | T1 0.733 (correct 0.758 / wrong 0.569), T3 0.901 (correct 0.918 / wrong 0.861) | n/a | | T3: 7/12 wrong answers ≥ 90%; gold option shown at 0% in 7/40 (published 16%) |
| McNemar | T1 Jev vs en b=66 / c=8 p < 0.0001, vs ml 66 / 6 p < 0.0001; T3 Jev vs en 2 / 4 p=0.6875, vs ml 6 / 3 p=0.5078 | n/a | | |
| latency (Jev displayed "server + network" = latencyMs) | A (T1 multi, 2\~4 questions) median 226 (164\~355) ms, B (T3) 241 (170\~713) ms | Jev 3rd-party p50 236\~276 ms (09 §1) | Within range | displayed = latencyMs half-up 79/79 |
| latency (browser POST / click→complete) | A 481 / 483 ms, B 469 / 471.5 ms (median) | n/a (different hardware and network) | | POST − latencyMs median 235.6 ms |
| Tokens (View details) | A input 760 (640\~953) / output 141 (138\~214); B 387.5 (372\~422) / 61 (61\~62) | n/a | | Totals: input 45,616 / output 8,806 |

## §7.3 Session fields

| Item | Value |
|---|---|
| Site status check | 08:46:26 page loaded normally (UI and DOM ids same as in S1). Because of the budget, the default example was not run. The first request (08:49:40) returned HTTP 502 "Jev is temporarily unavailable."; the retry 73.7 s later (run 2) returned 200 (Jev's per-item outputs are omitted in the public repository) |
| Request count | `POST /api/evaluate` 80 = Part A 40 (success 39 + 502 1) + Part B 40 (success 40). 5xx 1, 4xx 0, retries 1 (succeeded). 80 of the session cap of 80. The network list also shows POST 80 (200: 79, 502: 1), GET 39 (document 1, static 19, RSC prefetch 19) |
| Clicks without a request | 0. The 2 no-click dry runs (first item of Part A, first item of Part B) only filled the form and compared hashes |
| Gaps | By wall clock: min 12.1 s, median 15.1 s, max 131.7 s (run 61, after the instrumentation fix). By monotonic clock: min 12.1 s (run 4), 13.07 s (run 61), median 15.1 s. All 79 gaps ≥ 10 s |
| Model ID / token range | `typesafe-ai/jev` 79/79. Input 372\~953, output 61\~214. `rounding` {probabilityDecimals 2, scoreDecimals 2}, `warnings` [] 79/79 |
| Input hash check | sha12 before the request matched 80/80 (including the retry). After the request, the request body equals the form file payload byte for byte 80/80 |
| Parse failures | 0. All 89 choice answers in S2 (T1 49 + T3 40) exactly equal one of the input labels, and the probability keys equal the option keys (89/89). Screen = response for all 79 runs / 156 decisions (`shown_ok`) |
| Error messages | run 1: HTTP 502, response `{"ok":false,"error":{"code":"UNAVAILABLE","message":"Jev is temporarily unavailable."}}`, screen "Unable to evaluate / Jev is temporarily unavailable. / No decision was generated. Your inputs are still here." Handling: recorded immediately → waited over 60 s → retried the same item 1 time (succeeded). Otherwise 429, limit messages, captcha: 0. The only console error is this 1 502 (MCP console log); the rest are CSS preload warnings |
| Corresponding Laya reports | `results/F/jev_cmp/laya/T1_typed_decisions_40_{english,multilingual,router,typed-decisions}.json` (questions_sha256 `d46ef26a…`), `T1_typed_decisions_40_noulnocrit_{english,multilingual}.json` (`7b7f5dac…`), `T3_emotion_40_{english,multilingual,router}.json` (`bd7cc49e…`) |
| Cumulative site usage today | 80 (S2 only; `jev_runs_all.jsonl` has no other request on 2026-10-07; daily cap 100) |
| Cost | n/a. Jev pricing was not checked. Token totals: input 45,616 / output 8,806 |

## Outputs

- `results/F/jev_cmp/sessions/S2_20261007/S2_summary.md`: T1 and T3 results, McNemar, noul same-input comparison, per workflow and question, score details, calibration, latency and tokens, observations and limitations
- `results/F/jev_cmp/sessions/S2_20261007/S2_requests.jsonl` (80 lines), `results/F/jev_cmp/jev_runs_all.jsonl` (master, 151 lines) (the two files are not included in the public repository)
- `results/F/jev_cmp/sessions/S2_20261007/raw/`: 80 dumps + 1 timeout dump, `run_plan.json`, `js/` (instrument, patch_clock, 79 item scripts, 1 dry run), `evaluate_timing_all.json`, `network_requests.txt`, `console.log`, `mcp/` (3 snapshots, console log) (everything except `run_plan.json` is not included in the public repository)
- `results/F/jev_cmp/sessions/S2_20261007/shots/` (not included in the public repository): items 1·20·39 of Part A and items 1·20·40 of Part B (View details open, full page)
- `results/F/jev_cmp/sessions/S2_20261007/s2_prep.py`, `s2_record.py`
- `results/F/jev_cmp/jev_cmp.py`: `t1` subcommand and `record` extension (below)

## Anomalies / notes

- **1 502.** The first request returned 502. Per the rule, we waited at least 60 s and retried 1 time, which succeeded; all 79 later requests returned 200. Because of the retry, the request number (`run`) is 1 higher than the item number: Part A items 1\~39 are runs 2\~40 (run 1 was the 502), and Part B items 40\~79 are runs 41\~80. Read the `item` in `raw/run_plan.json` and the `rNN` in dump file names as distinct. With the budget at exactly 80, one more 5xx in Part B would have meant the last item could not be sent.
- **Wall-clock step (measurement anomaly).** Between runs 60 and 61 the host clock stepped by +1.98 s (`Date.now() − performance.now()` was +1,990 ms relative to timeOrigin). The dump, which converted resource timing via `performance.timeOrigin + startTime`, took run 61's POST entry to be before the click and timed out. Only 1 request went out, and it returned 200 (wrapper records 1, resource timing 1). The dump and the gap guard were changed to use the current offset and the monotonic clock (`raw/js/patch_clock.js`, no request), and run 61 was dumped again and recorded. The next session should use monotonic-based instrumentation from the start.
- **Instrumentation and input changes (vs S1).** To avoid copying state strings by hand, `s2_prep.py` generates a Playwright script per item from the form file, and the script clicks only when the hash matches. The gap guard was raised from 12 s to 15 s (from run 5). In Single mode, editing the form resets the result panel to "Your Jev decision will appear here." (observation only, no effect).
- **`jev_cmp.py` changes (minimal).** (1) `expected_view`: computes the displayed score level with the same `Math.round` as the client (half-up, `floor(score + 0.5)`). Python's `round` is half-even, so the display check could fail at x.50 (there was no x.50 score in this session). (2) `record`: takes the `omitted` reason from the form item's `reason`. For each decision it stores the screen strings `shown`·`shown_pct`·`shown_ok`, and for score `shown_score` (`x.xx / 4`, including the screen check). (3) `t1` subcommand: scores Jev and Laya with the same code, via `decisions` / `metrics` / `t1_extra` of `laya_summary.py`. After the change, S1 run 1 (T1 multi) and the S1 T2 row 0 dump were re-recorded without writing, confirming that the existing fields are unchanged.
- **T1 dataset sha.** The T1 dataset_sha256 in the S1 run card (`45806a15…`) changed to `749a24c4…` after the rebuild at 2026-10-06 10:28. questions_sha256 (`d46ef26a…`) is the same, and the Laya T1 reports are also `749a24c4…`. The option-A payload for row 30 equals S1 run 1 (sha12 `5a9e5492744b`).
- **Difference in comparison conditions.** For T1, Jev evaluated the 2\~4 questions of a case together in one request, while Laya evaluated each question as an independent row. The relation between the T1 gold (teacher argmax) and Jev could not be checked (to be verified).
- The Playwright MCP output directory (3 snapshots, 1 console log) was copied to `raw/mcp/` and then deleted from the repository root.

## Next actions

- Reflect the S2 results in `docs/09_laya_vs_jev_plan.md` §7.1\~7.2 (a separate task; this session did not edit docs).
- S3 (day 3): T4 Banking77-10 40 + T5 BoolQ 40 = 80. The plan equals the cap of 80, leaving no room for a 5xx retry. We propose fixing in advance a rule that moves the last item to S4 if a retry occurs. Instrumentation should be monotonic-based from the start (incorporating `patch_clock.js`).
- T1 follow-up (optional, needs budget): to isolate the "evaluated together" effect of Multiple questions, resend some cases in Single mode (option C) and compare the same decisions. Check the source of the teacher labels.

**English** | [한국어](S2_run_card.ko.md)
