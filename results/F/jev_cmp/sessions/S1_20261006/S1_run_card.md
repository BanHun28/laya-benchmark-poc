# Run 20261006-1004_jev-playground_S1 (T1 exploration 1 + T2_ag_news_40)

| Item | Value |
|---|---|
| run_id | 20261006-1004_jev-playground_S1 (Track F, Laya vs Jev comparison session S1: Multiple questions exploration + Step 2b fallback run T2 AG News) |
| Date / start time | 2026-10-06 (KST). Reading materials about 09:50, page load 09:54:55, first evaluation click 10:04:18.760, last evaluation click 10:17:27.517, browser closed 10:17:43, analysis and write-up until \~10:30 |
| Track / PoC phase | F (`docs/09_laya_vs_jev_plan.md` §7 S1, Step 2b fallback) |
| Hypothesis | None applies. There is no direct Jev comparison hypothesis among H1\~H10. The question is "On the same inputs, how do Jev and Laya (english / multilingual / router) differ in answers, probabilities and latency?" |
| Purpose (one line) | Check whether Multiple questions mode can carry T1 as is; if it cannot, send T2 AG News 40 to Jev with the same inputs and compare it pairwise with Laya |
| Commands | Expected payload: `.venv/bin/python results/F/jev_cmp/jev_cmp.py expect T2_ag_news_40` (T1: `expect T1_typed_decisions_40 --rows 30 --qids credential_compromise,disposition,severity,true_positive`). Browser: Playwright MCP to https://jevplayground.com/ → install the passive listeners and the `/api/evaluate` fetch wrapper → fill the form (`browser_fill_form`, id selectors) → `window.__jev.ready('<sha12>')` (12 s gap wait + hash comparison) → click `button.run-button` → save `window.__jev.dump()` to `raw/rNN_*.json` (not included in the public repository). Record: `.venv/bin/python results/F/jev_cmp/jev_cmp.py record S1 T2_ag_news_40 <run> raw/rNN_T2_rowRR.json --row RR`. Analysis: `jev_cmp.py analyze S1 T2_ag_news_40` |
| Environment record | No local model run. Browser: Playwright MCP Chromium (UA Chrome/154, macOS). Target: `POST /api/evaluate` of the Next.js site jevplayground.com. Laya figures were read from the S0 reports (CPU fp32, intra-op 10) |
| Checkpoint | Jev: page "TypeSafe Jev", response `model` and details Model ID `typesafe-ai/jev` (41/41), no version shown. Laya: english / multilingual revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` (report config.revisions) |
| Dataset | T2: `data/evals/jev_cmp/T2_ag_news_40.jsonl` (the T2 files are not included in the public repository), n=40, dataset_sha256 `555c7cd7d38c78d183fe884c62e1bbb102d040871bf6e66a8911269eba20fd21`, questions_sha256 `c472cb1cb971dab3d01c811ccc0f997d39516555fd43f513a8c59654e0457be1` (copied from the Laya report config). Form `T2_ag_news_40_playground.json` sha256 `1da0f5494068650edbcc6a23bf26f46790ef6592339f28f46d922f32370191d9`. T1 exploration: `T1_typed_decisions_40.jsonl` dataset_sha256 `45806a15aa17863895d5a3e2be24f06ac4d39b751de76eea4f2dcaefc227ba85`, questions_sha256 `d46ef26a6ec2f2f8c6fc0cfa1e81715751dda05f173cd028ae3eaaa4b9d519cb` (rebuilt during the session at 09:55:26; see the anomaly below) |
| Device / precision / threads | Jev: hosted, unknown. Laya: per the original reports, CPU fp32, intra-op 10 / inter-op 1, batch 8 |
| Parameters | T2: Single question, Decision type Choice, Question ``What is the topic of `article`?``, 4 choices in fixed order `world: world news and international politics` / `sports: sports` / `business: business and economy` / `sci_tech: science and technology`, State = form `state_text` (JSON string). T1 exploration: Multiple questions, row 30, 4 questions (boolean, choice 4, score 5-level, boolean), urgency (4-level) omitted. Operating rules: Run gap ≥ 10 s (actual ≥ 17 s), 1 retry after 60 s on a 5xx, immediate stop on a 429, limit message or captcha |
| Repetitions / warm-up | Single pass, no warm-up, 1 success per item |
| Duration | Browser session about 23 min (evaluation window 13 min 9 s). Whole task about 40 min |

## Results

| Metric | Value | Upstream reference (source) | Difference | Notes |
|---|---|---|---|---|
| choice_accuracy, Jev (T2) | 35/40 = 0.875, Wilson 95% [0.739, 0.945] | Jev AG News 0.910 (`docs/09_laya_vs_jev_plan.md` §1, 3rd-party published figure) | −0.035 | Within CI |
| choice_accuracy, Laya english / router (same 40) | 39/40 = 0.975 [0.871, 0.996] | 0.947 (T4) / 0.950 (apps) (`results/F/jev_cmp/laya_summary.md` §1) | +0.025\~0.028 | router sent 40/40 to english |
| choice_accuracy, Laya multilingual (same 40) | 37/40 = 0.925 [0.801, 0.974] | 0.937 / 0.930 (same source) | −0.005\~−0.012 | |
| Jev vs Laya english | Same label 36/40, b=0, c=4, exact McNemar p=0.125 | n/a | Jev −0.100 | Not significant |
| Jev vs Laya multilingual | Same label 38/40, b=0, c=2, p=0.500 | n/a | Jev −0.050 | Not significant |
| noul_accuracy | n/a (T2 is choice). T1 exploration row 30 boolean — (Jev's per-item outputs are omitted in the public repository) | n/a | n/a | 1 case, not used as a metric |
| score_mae | n/a. T1 exploration severity |score − teacher| = — | Jev typed-decisions MAE 0.391 | n/a | 1 decision |
| ece | Jev 0.118 / Laya english 0.083 / multilingual 0.058 (15 bins) | Jev 0.246 (nibzard, 09 §1) | n/a | Reference only for Jev (probabilities rounded to 2 decimals) |
| Brier | Jev 0.220 / Laya english 0.053 / multilingual 0.107 | n/a | n/a | 4/5 Jev wrong answers have top ≥ 93% |
| mean_confidence | Jev displayed top 0.977 (correct 0.985 / wrong 0.922), 100% displayed 29/40 | n/a | n/a | provider confidence 0.980 / 0.894 |
| latency (Jev displayed "server + network" = latencyMs) | median 234, min 188, max 448 ms (n=40) | Jev 3rd-party p50 236\~276 ms (09 §1) | Within range | |
| latency (Jev browser POST / click→complete) | median 468 (415\~749) / 470.5 (417\~751) ms | n/a (different hardware and network) | n/a | Laya: P2 round trip 20.1 ms (`results/poc/P2_20261003.md:67`), D1 english CPU 1q 86.6 ms (`results/D/D_summary_20261003.md:34`) |
| Tokens (Jev details) | T2 input median 425 (402\~534), output median 68 (66\~71). T1 exploration, 4 questions: — / — | n/a | n/a | |

## §7.2 Session fields

| Item | Value |
|---|---|
| Site status check | 09:54:55 page loaded normally. To save budget, the default example was not run; the first request (exploration, 10:04:18.760) returned 200, which doubled as the status check |
| Request count | `POST /api/evaluate` 41 times: success 41, 5xx 0, 4xx 0, retries 0. 41 of the session budget of 50. The browser network list also shows POST 41 (all 200), GET 104 (static 59, Next.js RSC prefetch 44, document 1) |
| Clicks without a request | 1 Run (10:04:00.602) was blocked by client-side validation (4-level rubric, level 4 empty). Wrapper records 0, resource timing 0 |
| Gaps | Between evaluation clicks: min 17.0 s, median 17.4 s, max 94.5 s (T1 exploration → switch to T2). The exploration request came 18.2 s after the validation-probe click |
| Model ID / token range | `typesafe-ai/jev` 41/41. Input 402\~803, output 66\~162. `rounding` {2, 2}, `warnings` [] |
| Input hash check | Before the request: the sha12 of the payload built in the page from the form values matched the form file's expected value 41/41. After the request: the captured request body matched the expected payload byte for byte 41/41 |
| Parse failures | 0. Response DECISION exactly equal to one of the input labels 40/40 (T2); screen display matches the response 41/41 |
| Error messages | None (5xx, "temporarily unavailable", 429, rate-limit, captcha: 0). Console errors 0; all 185 warnings are CSS preload notices |
| Corresponding Laya reports | `results/F/jev_cmp/laya/T2_ag_news_40_{english,multilingual,router}.json` (questions_sha256 `c472cb1cb971dab3…`); for the T1 exploration comparison, `T1_typed_decisions_40_{english,multilingual,router,typed-decisions}.json` (`d46ef26a6ec2f2f8…`) |
| Cost | n/a. Jev pricing was not checked in this session. Token totals for the 40 T2 runs: input 17,182 / output 2,739 |

## Outputs

- `results/F/jev_cmp/sessions/S1_20261006/multi_question_mode.md`: mode exploration, recipe, limits, T1 options
- `results/F/jev_cmp/sessions/S1_20261006/S1_summary.md`: T2 results, confidence, latency, observations, remaining budget
- `results/F/jev_cmp/sessions/S1_20261006/S1_requests.jsonl`, `results/F/jev_cmp/jev_runs_all.jsonl` (master, 41 lines) (the two files are not included in the public repository)
- `results/F/jev_cmp/sessions/S1_20261006/raw/`: `r01_T1_row30_multi.json`, `r02_T2_row00.json` … `r41_T2_row39.json`, `explore_js_{hits,payload,schema}.json` (client-bundle excerpts), `network_requests.txt`, `console.log`, `mcp/` (copies of the 63 automatic MCP snapshots and of the console log) (the files in this directory are not included in the public repository)
- `results/F/jev_cmp/sessions/S1_20261006/shots/` (not included in the public repository): `explore01~04_*.png`, `T2_run01_row00.png`, `T2_run20_row19.png`, `T2_run40_row39.png`
- `results/F/jev_cmp/jev_cmp.py`: expect / record / analyze

## Anomalies / notes

- **T1 Step 2a not possible.** The Score rubric takes exactly 5 levels, so the 70 4-level score decisions cannot be sent with the same inputs (Single mode applies the same validation). Per the rule, we switched to Step 2b (T2). The T1 options (A/B/C) are in `multi_question_mode.md` §3.
- **Data rebuilt during the session.** At 09:55:26 `data/evals/jev_cmp/*` was rewritten (T1 marked with `jev_excluded`, T4 rebuilt key-only, MANIFEST updated). The T1 dataset_sha256 changed from `fb70f4cb…` to `45806a15…`; questions_sha256 `d46ef26a…` is unchanged. The Laya T1 reports were also rewritten with the new sha at 09:56\~09:58. Both the exploration request (10:04) and the T2 requests were checked against payloads built from the post-rebuild files. The T2 file sha did not change. `docs/09_laya_vs_jev_plan.md` was also updated at 10:05 (reflecting the 80-character decision). This session did not edit docs or data.
- **Instrumentation change (vs the pilot).** In addition to the pilot's passive listeners, a fetch wrapper around `/api/evaluate` only was added to record the request body and the response text. Request arguments are passed through unchanged and no extra request is made. To read the client-side validation rules, the already loaded JS chunk was re-read 3 times with `cache: 'force-cache'` (static GET, not an API request).
- **Definition of the displayed latency.** Jev's displayed latency (`latencyMs`) appears to be measured by the playground server; its definition is not published. The difference from the browser POST (median 232 ms) is of the same size as in the pilot.
- **Playwright MCP output cleanup.** The Playwright MCP output directory created in the repository root during the session (63 snapshots and the console log) was copied to `raw/mcp/` and then deleted.

## Next actions

- Decide the T1 option (A: multi, 39 requests / B: padded-rubric variant / C: single, 120 requests). With option A, run 1 for row 30 can be reused (identical payload).
- Fix the T6 comparison rule: argmax-level accuracy + E[level] MAE (Jev's `score` is E[level]).
- Site budget left today: 32 (pilot 25 + checks 2 + S1 41 = 68). S2a candidate: T2 permutation probe 20 + determinism 10.

**English** | [한국어](S1_run_card.ko.md)
