# Run 20261007-1336_jev-playground_S3 (T4_banking77_10opt_40 + T5_boolq_40)

| Item | Value |
|---|---|
| run_id | 20261007-1336_jev-playground_S3 (Track F, Laya vs Jev comparison session S3: T4 Banking77-10 key-only 40 + T5 BoolQ 40) |
| Date / start time | 2026-10-07 (KST). Reading materials about 13:27 (start time not recorded; estimate), script generation 13:34\~13:35, page load 13:35:43, first evaluation click 13:36:13.671, last of Part A 13:46:24.494, first click of Part B 13:46:47.317, last evaluation click 13:56:39.010, browser closed 13:57:22, analysis and write-up 13:57\~14:08 |
| Track / PoC phase | F (`docs/09_laya_vs_jev_plan.md` §7 S3, §7.2 day 3) |
| Hypothesis | None applies. There is no direct Jev comparison hypothesis among H1\~H10. The question is "On the same inputs, how do Jev and Laya (english / multilingual / Router) differ in answers, probabilities and latency?" |
| Purpose (one line) | Send T4 Banking77-10 (key-only, 10 options) and T5 BoolQ to Jev with inputs byte-identical to Laya's and compare them pairwise on the same 40 rows each |
| Commands | Plan and input scripts: `.venv/bin/python results/F/jev_cmp/sessions/S3_20261007/s3_prep.py` (computes sha12 with `jev_cmp.py` `payload` and generates the per-item `raw/js/iNN_*.js` and the no-click `dry_i01_*`, `dry_i41_*` (`raw/js/` is not included in the public repository); asserts that state, question and option order are identical between the form file and the Laya JSONL, 10 options of at most 80 characters, and no noul criteria). Browser: Playwright MCP `browser_navigate https://jevplayground.com/` → `browser_run_code_unsafe raw/js/instrument.js` (passive listeners, a fetch wrapper that observes `/api/evaluate` only, monotonic clock) → for each item `browser_run_code_unsafe raw/js/iNN_*.js` (fill the form → `window.__jev.ready(sha12, 15000)` → click `button.run-button` only if the hash matches) → save `browser_evaluate window.__jev.dump()` to `raw/rNN_<T>_rowRR.json` (not included in the public repository) → `.venv/bin/python …/s3_record.py RUN ITEM` (= `jev_cmp.py record S3 <SET> RUN DUMP --row R` + stop-condition classification). Analysis: `.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S3 T4_banking77_10opt_40`, `… analyze S3 T5_boolq_40` |
| Environment record | No local model run. Browser: Playwright MCP Chromium. Target: jevplayground.com `POST /api/evaluate`. Laya figures were read from the S0 reports (`results/F/jev_cmp/laya/`, laya 0.3.23, device cpu) |
| Checkpoint | Jev: response `model` and View details Model ID `typesafe-ai/jev` 80/80, no version shown. Laya english / multilingual revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` (report config.revisions). Router chose english for all 40 rows of both T4 and T5 |
| Dataset | T4: `data/evals/jev_cmp/T4_banking77_10opt_40.jsonl`, n=40, dataset_sha256 `b124b7fb685abe85de45689984013d9b012c7e0e361d1b29ee55eb12dd2d23bc`, questions_sha256 `3c4b9b99f9cc5adcd3a2930f1fd99613bd115873234f06d8e5b6176ab5bc7074` (report config), form `T4_banking77_10opt_40_playground.json` sha256 `f91e53ca31e0ae9351bc9ed8d6f45a5002dfb4bf10174333a4bfabafd69549e3`. T5: `T5_boolq_40.jsonl`, n=40 (true 20 / false 20), dataset_sha256 `2b140a293790121b93dce29fb5c2804054570ee23238618b43a7915a6fe0786a`, questions_sha256 `d8699dd37a63aa7bfbc74dd05ad250872384751ff635e5aeaaaf84cc5d69cebe`, form sha256 `5512be765fe3407b087c05c1501c75af6b2c469cad5efd04a285e9de19de2425`. All three Laya reports share both hashes with the form files |
| Device / precision / threads | Jev: hosted, unknown. Laya: per the S0 reports, CPU fp32, intra-op 10 / inter-op 1, batch 8 |
| Parameters | Part A: Single question / Choice. The 10 options (key-only, up to 48 characters) were entered in form order; Question `` Which banking intent does `message` express? ``, State = form `state_text`. Part B: Single question / Boolean. Question `` Based on `passage`, is the answer to `question` yes? ``, State = form `state_text` (up to 1,194 characters). Operation: monotonic-based Run gap guard of 15 s from the start. On a 5xx, 1 retry of the same item after 65 s (`next_gap`); stop if the retry also fails. On a 429, limit message or captcha, stop the session immediately without retrying. Session cap 100 (planned 80) |
| Repetitions / warm-up | Single pass, no warm-up. 1 per item, 0 retries (run number = item number) |
| Duration | Browser session 21 min 39 s (13:35:43\~13:57:22), evaluation window 20 min 25 s. Whole task about 41 min (reading and preparation about 8 min, browser 22 min, analysis and write-up about 11 min) |

## Results

| Metric | Value | Upstream reference (source) | Difference | Notes |
|---|---|---|---|---|
| choice_accuracy (T4, same 40 rows) | Jev 37/40 = 0.925 [0.801, 0.974]; Laya english and Router 0.725 [0.572, 0.839], multilingual 0.750 [0.598, 0.858] | Jev Banking77 0.870 (72 labels, 3rd-party; `docs/09_laya_vs_jev_plan.md` §1), Laya 0.425 (77 options, BENCHMARKS.md:162) | Not comparable | The number of options differs. Context: Laya v0 (`key: key spaced`) english 0.825 / multilingual 0.575 (`laya_summary.md` §4b); v0 was not sent to Jev |
| noul_accuracy (T5, same 40 rows) | Jev 37/40 = 0.925 [0.801, 0.974]; Laya english and Router 0.725 [0.572, 0.839], multilingual 0.600 [0.446, 0.737] | Laya english 0.830 / multilingual 0.787 (README.md:1353, N=600, in training mix). No published Jev figure | english −0.105, multilingual −0.187 | The english CI contains 0.830; the multilingual CI does not contain 0.787 |
| McNemar (exact) | T4 Jev vs english and Router b=9 / c=1 p=0.0215, vs multilingual 8 / 1 p=0.0391. T5 vs english and Router 9 / 1 p=0.0215, vs multilingual 15 / 2 p=0.0023 | n/a | | Same label/prediction: T4 30·31/40, T5 30·23/40 |
| AUROC p(true) (T5) | Jev 0.988 [0.955, 1.000], english 0.810 [0.662, 0.942], multilingual 0.682 [0.496, 0.838] | n/a | Jev − english +0.177 [+0.043, +0.326], − multilingual +0.305 [+0.152, +0.486] | bootstrap with 2,000 resamples (seed 13), ties 0.5. Predicted true 21 / 19 / 18 (gold 20) |
| score_mae | n/a | n/a | | No score task |
| Brier | T4 Jev 0.114, english 0.349, multilingual 0.478; T5 Jev 0.098, english 0.393, multilingual 0.615 | n/a | | Σ(p − onehot)²; T4 over each row's 10 options, T5 over the 2 cells {false, true}. Jev probabilities rounded to 2 decimals |
| ece | T4 Jev 0.069 (english 0.150, multilingual 0.262); T5 Jev 0.103 (0.190, 0.294) | Jev typed-decisions 0.144, nibzard 0.246 (09 §1) | | 15 bins, based on max p |
| mean_confidence (Jev displayed top p) | T4 0.973 (correct 0.984 / wrong 0.847), 100% displayed 31/40, wrong with ≥ 0.90 1/3, gold option at 0% 0/40. T5 0.913 (0.931 / 0.697), 100% displayed 0/40, wrong with ≥ 0.90 0/3 | n/a | | T5: keeping top ≥ 0.80 retains 34/40 with 0 errors (descriptive statistic on the same 40 rows) |
| latency (Jev displayed "server + network" = latencyMs) | T4 median 227.5 (181\~417) ms, T5 200.5 (172\~363) ms | Jev 3rd-party p50 236\~276 ms (09 §1) | Within or slightly below the range | displayed = latencyMs half-up 80/80 |
| latency (browser POST / click→complete) | T4 470.5 / 472.5 ms, T5 442 / 443 ms (median) | n/a (different hardware and network) | | POST − latencyMs median 233.8 ms |
| Tokens (View details) | T4 input 476 (455\~546) / output 116.5 (107\~125); T5 402.5 (330\~545) / 20 (20) | n/a | | Totals: input 35,756 / output 5,460 |

## §7.3 Session fields

| Item | Value |
|---|---|
| Site status check | 13:35:43 page loaded normally. UI and DOM ids are the same as in S2 (Single question by default, example "Support Routing" with 4 Choice fields). When the instrumentation was installed, the check of the page body for limit messages found none. Because of the budget, the default example was not run |
| Request count | `POST /api/evaluate` 80 = Part A 40 + Part B 40, all 200. 5xx 0, 4xx 0 (429 0), retries 0. 80 of the session cap of 100. Network list: POST 80 (all `/api/evaluate`, 200), GET 70 (document 1, static 34, Next.js RSC prefetch 35, all 200) |
| Clicks without a request | 0. The 2 no-click dry runs (first item of Part A, first item of Part B) only filled the form and compared hashes. The 6 clicks that expanded View details (for screenshots) were not on the Run button and made no request |
| Gaps | 79 gaps on the monotonic clock: min 15.024 s, median 15.125 s, max 28.862 s (run 4). Part A 15.025 / 15.126 / 28.862, Part B 15.024 / 15.125 / 22.823. The resource-timing start gaps are the same. The gaps by Date.now() have the same values, and the wall − mono offset grew gradually from 0 to 15 ms (no step) |
| Model ID / token range | `typesafe-ai/jev` 80/80. Input 330\~546, output 20\~125. `rounding` {probabilityDecimals 2, scoreDecimals 2}, `warnings` [] 80/80. provider `confidence` on T4 40/40 (`decision`), T5 0/40 |
| Input hash check | sha12 before the request matched 80/80. After the request, the request body equals the form file payload byte for byte 80/80 |
| Parse failures | 0. All 40 T4 choice answers exactly equal one of the input labels, and the probability key set equals the 10 options (40/40, sum 1.00). The 40 T5 Boolean answers each returned a single `probability` (0.02\~0.99). Screen = response 80/80 |
| Error messages | None. 429, limit messages, captcha, "temporarily unavailable": 0. The console has 193 warnings (CSS preload) and 0 errors |
| Corresponding Laya reports | `results/F/jev_cmp/laya/T4_banking77_10opt_40_{english,multilingual,router}.json` (questions_sha256 `3c4b9b99…`), `T5_boolq_40_{english,multilingual,router}.json` (`d8699dd3…`) |
| Cumulative site usage today | 160 = S2 80 + S3 80 (the 2026-10-07 rows of `jev_runs_all.jsonl`). Our own daily cap of 100 was lifted by an owner decision on 2026-10-07. The 101st request was S3 run 21 (13:41:37.352), and there was no limit signal through run 80 |
| Cost | n/a. Jev pricing was not checked. Token totals: input 35,756 / output 5,460 |

## Outputs

- `results/F/jev_cmp/sessions/S3_20261007/S3_summary.md`: T4 and T5 results, McNemar, AUROC and bootstrap, calibration and confidence, error analysis, latency and tokens, observations and limitations
- `results/F/jev_cmp/sessions/S3_20261007/S3_requests.jsonl` (80 lines), `results/F/jev_cmp/jev_runs_all.jsonl` (master, 231 lines; the first 151 lines are byte-identical to the pre-S3 copy) (the two files are not included in the public repository)
- `results/F/jev_cmp/sessions/S3_20261007/raw/`: 80 dumps, `run_plan.json`, `js/` (instrument, 80 item scripts, 2 dry runs), `evaluate_timing_all.json`, `network_requests.txt`, `network_requests_all.txt`, `console.log`, `mcp/` (2 snapshots, MCP console log) (everything except `run_plan.json` is not included in the public repository)
- `results/F/jev_cmp/sessions/S3_20261007/shots/` (not included in the public repository): items 1·20·40 of Part A and items 1·20·40 of Part B (View details open, full page)
- `results/F/jev_cmp/sessions/S3_20261007/s3_prep.py`, `s3_record.py`
- `results/F/jev_cmp/jev_cmp.py`: `analyze` extension (below)

## Anomalies / notes

- **No errors.** This time there was no transient outage like the 502 on S2's first request, so the "S3 carry-over rule" of `docs/09` §7.2 (move the last item to S4 on a 5xx retry) was not used. With the owner decision (session cap 100), there was also room for 20 retries.
- **Instrumentation (vs S2).** From the start, all times were recorded on a single monotonic axis (`performance.timeOrigin + performance.now()`). Clicks, the fetch wrapper, the status log and resource timing all share this axis, so `click_epoch_ms`·`click_kst` in the S3 records are values on this axis, not Date.now() (difference from wall ≤ 15 ms). The dumps also keep `clicks_wall` (Date.now()) and `wall_minus_mono_ms`. The gap guard measures from the later of the last Run click and the last `/api/evaluate` resource entry (`raw/js/instrument.js:104-114`).
- **Recording wrapper (`s3_record.py`).** It calls the existing `jev_cmp.py record`, after first checking that the dump's click is newer than the last click already recorded (`s3_record.py:30-34`). This prevents a stale dump from passing the body check when the same payload is retried; it did not fire this time. Exit codes: 0 recorded, 1 not recorded, 2 5xx (wait over 60 s, then 1 retry), 4 429 or limit message/captcha (stop immediately), 5 other error (stop), 3 succeeded but a stop message is visible (`:52-65`).
- **`jev_cmp.py` changes (minimal).**
  1. `analyze` now computes Brier with each row's own options (`jev_cmp.py:328-329`, `:341-342`). The old code used the option set of row 0 for every row, which gave wrong values for T4 (and likewise T7), where the options differ per row. Before the fix, the T4 output was Jev 0.000, Laya english 0.019; after the fix the Laya values equal `laya_summary.md` (0.349 / 0.478). When the options differ per row, it outputs a list of wrong gold → pred instead of the per-class table and confusion matrix (`:367-391`).
  2. Added a branch for Boolean sets, `boolean_lines` (`:333-336`, `:461-515`). It outputs accuracy (p(true) ≥ 0.5), the predicted-positive rate, 2-cell Brier, ECE, AUROC with item-bootstrap CI, the paired AUROC difference, the same-sample optimal threshold, confidence, and a per-row table. `auroc` (`:455-458`) uses the same definition as the auroc of `scripts/calibrate_ko.py` (ties 0.5).
  3. The latency table and request lines moved into the functions `latency_lines`·`request_lines` (`:433-452`). The output is unchanged.
  4. Regression check: the outputs of `analyze S1 T2_ag_news_40` and `analyze S2 T3_emotion_40` are byte-identical before and after the change. `t1 S1,S2` also still runs.
- **Maximum gap 28.9 s (run 4).** This is the time spent fixing the recording wrapper between runs 3 and 4, unrelated to the site. The Part B maximum of 22.8 s (run 41) is the time for the Part B dry run and screenshots.
- **Judgments involving interpretation (to be verified).** Treating the 2 T4 rows that all four systems got wrong as cases with an ambiguous label boundary, and judging the gold of the 1 T5 row that all three systems got wrong to be ambiguous, are judgments made from reading the texts. Scoring used the dataset labels as they are.
- `docs/` and `data/evals/` were not edited. The Laya models were not run. The Playwright MCP output directory (2 snapshots, 1 console log) was copied to `raw/mcp/` and then deleted from the repository root.

## Next actions

- Reflect the S3 results in `docs/09_laya_vs_jev_plan.md` §7.1\~7.2 (a separate task; this session did not edit docs). The site-wide cumulative total through day 3 is 258 (day 1 98 + day 2 80 + day 3 80).
- S4: T6 SST-5 40 (Score, 5 levels) + T7 en·de 40. T7 has different options per row, so this session's `analyze` Brier fix applies directly.
- Optional (budget +40): send the T4 v0 (`key: key spaced`) rendering to Jev as well, to compare rendering sensitivity (open question 8, §7.2 S5-b).
- The Boolean abstention threshold (0 errors at top ≥ 0.80) is a descriptive statistic on the same 40 rows. To use it, it must be fixed in advance and validated on a separate sample (T8 or another BoolQ draw).

**English** | [한국어](S3_run_card.ko.md)
