# S1 summary: Multiple questions exploration + T2 AG News 40 (2026-10-06)

**Verdict.**
1. Multiple questions mode accepts Score only with exactly 5 levels, so it cannot carry T1 cases faithfully (70/80 score decisions are 4-level). Per the rule, we switched to Step 2b (T2). Details in `multi_question_mode.md`.
2. On T2 AG News 40: Jev 35/40 = 0.875, Laya english and router 39/40 = 0.975, multilingual 37/40 = 0.925. 0 items were right for Jev and wrong for Laya, so b = 0; exact McNemar p is 0.125 for english and 0.5 for multilingual. At n = 40 the systems cannot be told apart.
3. 4 of Jev's 5 wrong answers had displayed probabilities of 93\~99%. Unlike the pilot (all wrong answers < 90%), a confidence threshold could not filter out the wrong answers on this task.

Via the playground, not the API. The model version is not shown (`typesafe-ai/jev`), and the sample is small (n = 40). T2 is a source in Laya's training mix, which may favor Laya (MANIFEST `in_training_mix: yes`).

## 1. Execution

| Item | Value |
|---|---|
| Requests (`POST /api/evaluate`) | 41, all HTTP 200. Exploration 1 (T1 row 30, Multiple questions, 4 questions) + T2 40 (Single question, Choice 4) |
| Errors / retries | 0 / 0. No 5xx, 429, rate-limit message or captcha. Console errors 0 (the 185 warnings are CSS preload notices) |
| Run clicks without a request | 1 (4-level rubric validation probe). Blocked by client-side validation; 0 requests confirmed by the wrapper and resource timing |
| Gaps | Gap between Run clicks: min 17.0 s, median 17.4 s (rule ≥ 10 s). The precheck function does not return until 12 s after the last click |
| Input identity | 41/41 request bodies are byte-identical to the payloads built from the form files (precheck sha12 + post-hoc body comparison) |
| Display check | 41/41: the on-screen DECISION, % and ms match the response JSON. "N ms · server + network" = round(`latencyMs`) |
| Session budget | 41 of 50 used, 9 left |

## 2. T2 results (same 40 items)

| system | correct / n | accuracy | Wilson 95% CI | Brier | ECE (15 bins) | mean top p |
|---|---|---|---|---|---|---|
| Jev (playground, displayed probabilities) | 35/40 | 0.875 | [0.739, 0.945] | 0.220 | 0.118 | 0.977 |
| Laya english | 39/40 | 0.975 | [0.871, 0.996] | 0.053 | 0.083 | 0.930 |
| Laya multilingual | 37/40 | 0.925 | [0.801, 0.974] | 0.107 | 0.058 | 0.983 |
| Laya router (40/40 routed to english) | 39/40 | 0.975 | [0.871, 0.996] | 0.053 | 0.083 | 0.930 |

Jev's Brier and ECE were computed from probabilities rounded to 2 decimals (Brier floor error about ±0.005; ECE is for reference only because the bins are sparse).

**Paired comparison** (b = Jev right & Laya wrong, c = Jev wrong & Laya right)

| pair | n | same label | b | c | exact McNemar p |
|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 36 | 0 | 4 | 0.125 |
| Jev vs Laya multilingual | 40 | 38 | 0 | 2 | 0.500 |
| Jev vs Laya router | 40 | 36 | 0 | 4 | 0.125 |

**Correct by class** (10 per gold)

| gold | Jev | Laya english | Laya multilingual | Laya router |
|---|---|---|---|---|
| world | 8 | 9 | 8 | 9 |
| sports | 10 | 10 | 10 | 10 |
| business | 10 | 10 | 10 | 10 |
| sci_tech | 7 | 10 | 9 | 10 |

Jev confusions: world → business 2, sci_tech → business 2, sci_tech → world 1. All 5 of Jev's wrong answers were business or world.

**Jev's 5 wrong answers**

| row | id | article (opening) (AG News text omitted) | gold | Jev (displayed %) (Jev's per-item outputs are omitted in the public repository) | Laya en | Laya ml |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |
| — | — | — | — | — | — | — |
| — | — | — | — | — | — | — |
| — | — | — | — | — | — | — |
| — | — | — | — | — | — | — |

For 1 of the wrong answers the gold itself is doubtful. 3 are also borderline cases that overlap with business. AG News's sci_tech includes news about technology companies, whereas Jev appears to read the "science and technology" description more narrowly (inferred).

## 3. Jev confidence

| Metric | Value |
|---|---|
| top = 100% displayed | 29/40 (72%) |
| runs with a 0% option | 40/40. 0% cells 109/160 |
| mean top % (correct / wrong) | 98.5 / 92.2 |
| wrong with top ≥ 90% | 4/5 |
| runs where the gold option shows 0% | 1 |
| mean provider confidence (correct / wrong) | 0.980 / 0.894 |
| accept only p ≥ 0.90 | 38/40 accepted, 34 correct (0.895) |
| coverage @ error ≤ 5% / 10% | 0.800 (t = 0.98) / 0.875 (t = 0.94) |

For comparison: at p ≥ 0.90 Laya english accepts 33/40 with 33 correct (1.000), and its only wrong answer (row 15) has confidence 0.76. multilingual accepts 38/40 with 37 correct, and 1 of its 3 wrong answers (row 15, 0.98) is at 0.90 or above. coverage @ error ≤ 5% is 1.000 for english and 0.950 for multilingual.

## 4. Latency and tokens (40 successful Jev runs)

| Measurement | median / min / max (ms) |
|---|---|
| displayed "server + network" (= response `latencyMs`) | 234 / 188 / 448 |
| browser POST (resource timing) | 468 / 415 / 749 |
| click → "Evaluation complete" | 470.5 / 417 / 751 |

| Laya local reference (different hardware and path; not a model-speed comparison) | ms | source |
|---|---|---|
| P2 `/poc/decide` HTTP loopback round trip p50 (ft-v1, MPS) | 20.1 | `results/poc/P2_20261003.md:67` |
| D1 in-process 1q median, english CPU fp32, short state 123 tok | 86.6 | `results/D/D_summary_20261003.md:34` |
| D1 in-process 1q median, english MPS | 31.8 | `results/D/D_summary_20261003.md:40` |
| D1 in-process 1q median, multilingual MPS (value cited in the pilot) | 13.8 | `results/D/D_summary_20261003.md:42` |

The Jev browser POST median is 23.3× the P2 round trip and 5.4× english CPU in-process. The displayed value is a median 232 ms shorter than the browser POST, i.e. it is measured without the client↔playground leg. This is the same structure as in the pilot (249.5 vs 497.5 ms) and within the 3rd-party published Jev p50 range of 236\~276 ms.

Tokens: input median 425 (402\~534), output median 68 (66\~71). Model ID `typesafe-ai/jev` 40/40, `rounding` {probabilityDecimals 2, scoreDecimals 2}, `warnings` always an empty array. Output is far below the pilot's 255 tokens (Korean, 8 options), so output tokens appear to grow with the number of options or the label length (inferred).

## 5. Representativeness

- Jev 0.875 [0.739, 0.945] is within range of the 3rd-party published Jev AG News 0.910 (`docs/09_laya_vs_jev_plan.md` §1).
- Laya english 0.975 [0.871, 0.996] is within range of upstream 0.947 / 0.950 (`laya_summary.md` §1).
- So there is no evidence that this sample departs from either system's published level. The CI width is about ±0.1, however.

## 6. Observations (3)

1. **The direction of the difference is consistent but not significant.** There are 4 items (vs english) that Laya got right and Jev got wrong, and 0 in the other direction. With b = 0, the minimum p at n = 40 depends only on c; p < 0.05 requires c = 6 or more.
2. **Jev's probabilities are overconfident on this task.** 72% of the displays are 100% and 4/5 wrong answers are at 93% or above, giving Brier 0.220 (Laya english 0.053). In the pilot's Korean routing, all wrong answers were at 41\~86%, so a 90% threshold filtered them out. Since the calibration pattern varies by task, this should be revisited on T3 (emotion, published Jev 0.480).
3. **The errors cluster at label boundaries.** All 5 are business/world or sci_tech/world borderline cases, and 1 has a doubtful gold. The one-line label description (`sci_tech: science and technology`) does not capture AG News's convention that "tech-company news = sci_tech". This is the same "dataset convention missing from the description" type as the pilot's `play → media` case. Laya english got 4/5 of them right, which cannot be separated from T2 being in Laya's training mix.

## 7. Remaining budget (from S2 on)

| Task | Planned requests | Used in S1 | Remaining requests | Notes |
|---|---|---|---|---|
| T1 typed-decisions | 40 (multi) | 1 (row 30, exploration) | option A 39 / option C 120 / decision needed | The 70 4-level score decisions cannot be sent with the same inputs in any mode (`multi_question_mode.md` §3) |
| T2 AG News | 40 + permutation 20 | 40 | permutation probe 20 | Main measurement done |
| T3 Emotion | 40 | 0 | 40 | |
| T4 Banking77-10 (key-only rebuild) | 40 | 0 | 40 | |
| T5 BoolQ | 40 | 0 | 40 | Boolean, no constraints |
| T6 SST-5 | 40 | 0 | 40 | Score with 5 levels; fits the rubric as is |
| T7 MASSIVE, 5 languages | 100 | 0 | 100 | |
| T8 prompt-injections (optional) | 40 | 0 | 40 | |
| Determinism check | 10 | 0 | 10 | |

Site usage today (2026-10-06) is pilot 25 (`results/F/F_jev_20261006.md`) + 2 availability checks (08:01, 08:20, recorded separately in the same document) + S1 41 = 68. Up to the daily cap of 100, 32 remain today. A plan that respects the caps of 80 per session / 100 per day:

| Day | Session | Content | Requests |
|---|---|---|---|
| 1 (today, optional) | S2a | T2 permutation probe 20 + determinism 10 | 30 |
| 2 | S3 | T1 option A 39 (if chosen) + T3 40 | 79 |
| 3 | S4 | T4 40 + T5 40 | 80 |
| 4 | S5 | T6 40 + T7 en·de 40 | 80 |
| 5 | S6 | T7 ja·zh-CN·ko 60 (+ part of T8 if budget allows) | 60\~80 |
| 6 (optional) | S7 | rest of T8 | ≤ 40 |

If T1 is done as option C (Single, 120), days 2\~3 split T1's 120 alone over two sessions, and T8 is dropped.

Update (10:38): the day-1 S2a (T2 permutation 20 + determinism 10) was run as S1b (`results/F/jev_cmp/sessions/S1b_20261006/S1b_summary.md`). Today's cumulative total is 98, and T2 has 0 requests left.

## 8. Files

| File | Contents |
|---|---|
| `results/F/jev_cmp/sessions/S1_20261006/multi_question_mode.md` | mode exploration, operating recipe, limits, T1 options |
| `results/F/jev_cmp/sessions/S1_20261006/S1_requests.jsonl` (not included in the public repository) | 41 lines of session requests (a format that records both successes and failures) |
| `results/F/jev_cmp/jev_runs_all.jsonl` (not included in the public repository) | master append-only log (currently 41 lines, `session` field) |
| `results/F/jev_cmp/sessions/S1_20261006/raw/rNN_*.json` (not included in the public repository) | per-request DOM dump, request body, response text, resource timing, status log |
| `results/F/jev_cmp/sessions/S1_20261006/raw/network_requests.txt`, `console.log`, `mcp/` | browser network list (POST 41, GET 104), console log, 63 automatic MCP snapshots (none of the three is included in the public repository) |
| `results/F/jev_cmp/sessions/S1_20261006/shots/` (not included in the public repository) | 4 exploration shots, T2 runs 1·20·40 |
| `results/F/jev_cmp/jev_cmp.py` | expect / record / analyze. The tables in this summary are the output of `analyze S1 T2_ag_news_40` |
| `results/F/jev_cmp/sessions/S1_20261006/S1_run_card.md` | run card |

## Appendix: per-item results (`jev_cmp.py analyze S1 T2_ag_news_40`)

| # | row | id | gold | Jev (top %) | Laya english (p) | Laya multilingual (p) | Laya router (p) |
|---|---|---|---|---|---|---|---|
| 1 | 0 | 63 | sci_tech | — | O sci_tech (0.98) | O sci_tech (1.00) | O sci_tech (0.98) |
| 2 | 1 | 320 | business | — | O business (0.97) | O business (1.00) | O business (0.97) |
| 3 | 2 | 501 | sports | — | O sports (1.00) | O sports (1.00) | O sports (1.00) |
| 4 | 3 | 630 | sci_tech | — | O sci_tech (0.94) | O sci_tech (1.00) | O sci_tech (0.94) |
| 5 | 4 | 974 | sports | — | O sports (0.99) | O sports (1.00) | O sports (0.99) |
| 6 | 5 | 1125 | sci_tech | — | O sci_tech (0.82) | O sci_tech (0.96) | O sci_tech (0.82) |
| 7 | 6 | 1145 | sports | — | O sports (0.89) | O sports (1.00) | O sports (0.89) |
| 8 | 7 | 1223 | business | — | O business (0.96) | O business (1.00) | O business (0.96) |
| 9 | 8 | 1418 | sports | — | O sports (0.99) | O sports (1.00) | O sports (0.99) |
| 10 | 9 | 1506 | world | — | O world (0.93) | O world (0.97) | O world (0.93) |
| 11 | 10 | 1740 | sports | — | O sports (0.98) | O sports (1.00) | O sports (0.98) |
| 12 | 11 | 1782 | sports | — | O sports (0.99) | O sports (1.00) | O sports (0.99) |
| 13 | 12 | 1958 | business | — | O business (0.99) | O business (1.00) | O business (0.99) |
| 14 | 13 | 2053 | world | — | O world (0.84) | X business (0.76) | O world (0.84) |
| 15 | 14 | 2185 | sci_tech | — | O sci_tech (0.57) | O sci_tech (0.95) | O sci_tech (0.57) |
| 16 | 15 | 2306 | world | — | X business (0.76) | X business (0.98) | X business (0.76) |
| 17 | 16 | 2636 | business | — | O business (0.98) | O business (1.00) | O business (0.98) |
| 18 | 17 | 3699 | business | — | O business (0.96) | O business (1.00) | O business (0.96) |
| 19 | 18 | 4536 | business | — | O business (0.99) | O business (1.00) | O business (0.99) |
| 20 | 19 | 5043 | sci_tech | — | O sci_tech (0.58) | X business (0.77) | O sci_tech (0.58) |
| 21 | 20 | 5209 | sports | — | O sports (0.98) | O sports (1.00) | O sports (0.98) |
| 22 | 21 | 5236 | world | — | O world (0.98) | O world (1.00) | O world (0.98) |
| 23 | 22 | 5458 | sports | — | O sports (0.99) | O sports (1.00) | O sports (0.99) |
| 24 | 23 | 5561 | world | — | O world (0.99) | O world (1.00) | O world (0.99) |
| 25 | 24 | 5568 | world | — | O world (0.98) | O world (1.00) | O world (0.98) |
| 26 | 25 | 5751 | business | — | O business (0.88) | O business (1.00) | O business (0.88) |
| 27 | 26 | 6060 | sports | — | O sports (0.94) | O sports (1.00) | O sports (0.94) |
| 28 | 27 | 6183 | business | — | O business (0.96) | O business (1.00) | O business (0.96) |
| 29 | 28 | 6492 | sci_tech | — | O sci_tech (0.92) | O sci_tech (0.99) | O sci_tech (0.92) |
| 30 | 29 | 6514 | world | — | O world (0.93) | O world (0.98) | O world (0.93) |
| 31 | 30 | 6653 | sci_tech | — | O sci_tech (0.94) | O sci_tech (1.00) | O sci_tech (0.94) |
| 32 | 31 | 6815 | sci_tech | — | O sci_tech (0.91) | O sci_tech (1.00) | O sci_tech (0.91) |
| 33 | 32 | 6900 | business | — | O business (0.98) | O business (1.00) | O business (0.98) |
| 34 | 33 | 6942 | world | — | O world (0.97) | O world (0.99) | O world (0.97) |
| 35 | 34 | 6961 | business | — | O business (0.97) | O business (1.00) | O business (0.97) |
| 36 | 35 | 7120 | sci_tech | — | O sci_tech (0.92) | O sci_tech (1.00) | O sci_tech (0.92) |
| 37 | 36 | 7152 | sports | — | O sports (0.99) | O sports (1.00) | O sports (0.99) |
| 38 | 37 | 7257 | world | — | O world (0.98) | O world (1.00) | O world (0.98) |
| 39 | 38 | 7302 | sci_tech | — | O sci_tech (0.98) | O sci_tech (1.00) | O sci_tech (0.98) |
| 40 | 39 | 7460 | world | — | O world (0.91) | O world (0.99) | O world (0.91) |

**English** | [한국어](S1_summary.ko.md)
