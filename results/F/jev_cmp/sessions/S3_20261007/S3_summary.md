# S3 summary: T4 Banking77-10 (key-only) 40 + T5 BoolQ 40 (2026-10-07)

**Verdict.**
1. **On T4 Banking77-10, Jev is significantly ahead of all three Laya runners.** Jev 37/40 = **0.925** [0.801, 0.974]. Laya english and Router 29/40 = 0.725, multilingual 30/40 = 0.750. Jev vs english is b=9 / c=1 (exact McNemar p=0.0215), vs multilingual b=8 / c=1 (p=0.0391). 2 of Jev's 3 wrong answers were also wrong, with the same label, for all three Laya runners. Only 1 row was wrong for Jev alone (Jev's per-item outputs are omitted in the public repository).
2. **On T5 BoolQ Jev also leads, and the difference comes from ranking quality, not from the threshold.** Jev 37/40 = **0.925**, Laya english and Router 0.725, multilingual 0.600 (McNemar b/c 9/1 p=0.0215, 15/2 p=0.0023). The AUROC of p(true) is Jev 0.988 [0.955, 1.000], english 0.810 [0.662, 0.942], multilingual 0.682 [0.496, 0.838]. The paired-bootstrap CIs of the differences exclude 0 for both pairs (+0.177 [+0.043, +0.326], +0.305 [+0.152, +0.486]). The predicted-positive counts are Jev 21, english 19, multilingual 18, all close to the gold 20/40. Even with the optimal threshold chosen on these 40 rows, Laya english reaches only 0.775, so unlike NSMC E6 this is not a structure that moving the threshold can recover (descriptive statistic, not for claims).
3. **The shape of Jev's probabilities differs by decision type.** Single choice (T4) displays 100% in 31/40, and one wrong answer is at 0.90 or above. Boolean (T5) displays 100% in 0/40 (p(true) 0.02\~0.99), and all 3 wrong answers have top < 0.80. Keeping only top ≥ 0.80 covers 34/40 with 0 errors (descriptive statistic on the same 40 rows). This is in the same direction as the patterns seen in S2 on T1 noul (underconfident) and T3 choice (overconfident).
4. **Operations:** all 80 requests returned HTTP 200. 5xx, 4xx (including 429), limit messages and captcha: 0, and no retries. Gaps on the monotonic clock: min 15.02 s, median 15.13 s. Today's cumulative total is S2 80 + S3 80 = 160, and there was no limit signal even after the 101st request (S3 run 21, 13:41:37).

Via the playground, not the API. The model version is not shown (`typesafe-ai/jev` 80/80), and n=40. Jev probabilities are rounded to two decimal places. T5 (BoolQ) is in Laya's training mix according to upstream, and Jev's training data is unknown.

## 1. Execution overview

| Item | Value |
|---|---|
| Requests | `POST /api/evaluate` 80 = Part A (T4) 40 + Part B (T5) 40, all HTTP 200. Session cap 100 (planned 80); the daily cap was lifted by an owner decision (2026-10-07) |
| Stop conditions | 5xx 0, 4xx 0 (429 0), limit messages 0, captcha 0, error screens 0. After every run, the result panel, status, title, `[role=alert]` and body text were checked with a limit-message regex, and the presence of a captcha iframe was checked (`s3_record.py`, dump `page`) |
| Gaps (between Run clicks) | Guard 15 s, monotonic from the start (`performance.timeOrigin + performance.now()`, the same axis as resource timing). 79 gaps: min 15.024 s, median 15.125 s, max 28.862 s (run 4: time spent fixing the recording wrapper). Re-measuring from resource timing `startTime` differences gives the same (15.024 / 15.125 / 28.861). The wall − mono offset grew gradually from 0 to 15 ms with no step |
| Input identity | Before the request: the payload sha12 built from the form values matched the form file's expected value 80/80 (`window.__jev.ready`). After the request: the captured request body equals the `jev_cmp.py` payload byte for byte 80/80 (`payload_exact`). 2 no-click dry runs (items 1, 41) |
| Input content | T4: Single / Choice. The 10 options (key-only, up to 48 characters) were entered in form-file order; in every row the option order equals the Laya criteria key order (`s3_prep.py` assert). T5: Single / Boolean, the question sentence only (Laya noul has no criteria either). For both tasks, State is the JSON string Laya reads (`state_text`) |
| Screen = response | 80/80 (DECISION, bar %). Displayed latency = `latencyMs` rounded half-up 80/80. The Single Boolean screen ("DECISION / No / More probable answer, derived from Jev’s P(true). / Yes 5% / No 95%") also matched with the existing parser |
| Model ID / response metadata | `model` and View details both `typesafe-ai/jev` 80/80. `rounding` {2, 2}, `warnings` [] 80/80. provider `confidence` is present on T4 40/40 (same value as top p in 34/40) and absent on T5 Boolean (0/40) |

## 2. T4 Banking77-10 (key-only, 40 rows, 40 distinct gold labels)

### 2.1 Accuracy and calibration (same 40 rows, same option strings and order)

| system | correct / n | accuracy [Wilson 95%] | Brier | ECE (15 bins) | mean top p |
|---|---|---|---|---|---|
| Jev (playground, displayed p, rounded to 2 decimals) | 37/40 | 0.925 [0.801, 0.974] | 0.114 | 0.069 | 0.973 |
| Laya english | 29/40 | 0.725 [0.572, 0.839] | 0.349 | 0.150 | 0.860 |
| Laya multilingual | 30/40 | 0.750 [0.598, 0.858] | 0.478 | 0.262 | 0.832 |
| Laya Router (all 40 to english) | 29/40 | 0.725 [0.572, 0.839] | 0.349 | 0.150 | 0.860 |

Brier is Σ(p − onehot)², computed for each row over that row's 10 options. The Laya values equal `laya_summary.md` §1 (0.349 / 0.478, ECE 0.150 / 0.262).

### 2.2 Agreement and exact McNemar (b = only Jev right, c = only Laya right)

| pair | n | same label | b | c | p |
|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 30 | 9 | 1 | 0.0215 |
| Jev vs Laya multilingual | 40 | 31 | 8 | 1 | 0.0391 |
| Jev vs Laya Router | 40 | 30 | 9 | 1 | 0.0215 |

### 2.3 Confidence

| system | top = 100% | mean top (correct / wrong) | wrong with top ≥ 0.90 | gold option shown at 0% | provider confidence (correct / wrong) |
|---|---|---|---|---|---|
| Jev | 31/40 (78%) | 0.973 (0.984 / 0.847) | 1/3 | 0/40 | 0.970 (0.982 / 0.827) |
| Laya english | - | 0.860 (0.961 / 0.596) | 3/11 | - | - |
| Laya multilingual | - | 0.832 (0.828 / 0.846) | 6/10 | - | - |

Jev has 348/400 cells at 0%, and every run has a 0% option. Yet no row shows the gold option at 0% (S2 T3: 7/40). p(gold) of the 3 wrong answers is 0.01\~0.28. For multilingual, the mean confidence of the wrong answers (0.846) is higher than that of the correct ones (0.828).

### 2.4 Errors and confusions

| row | message (summary) | gold | Jev (top) | Laya english | Laya multilingual |
|---|---|---|---|---|---|
| — | — | — | — | — | — |
| — | — | — | — | — | — |
| — | — | — | — | — | — |

- All four systems got 2 rows wrong with the same label. Both are cases with an ambiguous Banking77 label boundary.
- Jev got 9 of Laya english's 11 wrong answers right. The most frequent wrong label is lost or stolen card (2 times). Jev also got 8 of multilingual's 10 wrong answers right. Both Laya checkpoints were also wrong with the same label on 2 rows that Jev got right.

### 2.5 Context (non-comparable figures, for reference)

| Figure | Value | Relation to this measurement |
|---|---|---|
| Laya T4 v0 (`key: key spaced` rendering, same 40 rows, option set and order) | english 0.825 / multilingual 0.575 (`laya_summary.md` §4b) | The v0 rendering was not sent to Jev. Changing only the rendering moved Laya multilingual by +0.175 (p=0.016), so key-only is the only same-input comparison |
| Jev Banking77 published | 0.870 (72 labels, 3rd-party, BENCHMARKS.md) | Different number of options (10 vs 72). Not compared directly with this 0.925 |
| Laya Banking77 upstream | 0.425 (77 options, BENCHMARKS.md:162) | Not comparable: different number of options |
| Training mix | MANIFEST `in_training_mix: unknown` (upstream lists it as held out) | |

## 3. T5 BoolQ (40 rows, gold true 20 / false 20)

### 3.1 Accuracy, positive rate and ranking quality

| system | correct / n | accuracy [Wilson 95%] | predicted true | Brier | ECE (15 bins) | mean top p | AUROC p(true) [bootstrap 95%] | accuracy at the optimal threshold on the same 40 rows (descriptive) |
|---|---|---|---|---|---|---|---|---|
| Jev (playground, displayed p, 2 decimals) | 37/40 | 0.925 [0.801, 0.974] | 21 | 0.098 | 0.103 | 0.913 | 0.988 [0.955, 1.000] | 38/40 = 0.950 (t 0.63\~0.85) |
| Laya english | 29/40 | 0.725 [0.572, 0.839] | 19 | 0.393 | 0.190 | 0.897 | 0.810 [0.662, 0.942] | 31/40 = 0.775 (t 0.41\~0.90) |
| Laya multilingual | 24/40 | 0.600 [0.446, 0.737] | 18 | 0.615 | 0.294 | 0.870 | 0.682 [0.496, 0.838] | 27/40 = 0.675 (t 0.94) |
| Laya Router (all 40 to english) | 29/40 | 0.725 [0.572, 0.839] | 19 | 0.393 | 0.190 | 0.897 | 0.810 [0.662, 0.942] | 31/40 = 0.775 |

- The decision rule is p(true) ≥ 0.5 (the laya-evals rule). No row got exactly 0.5 ("Equally likely") from Jev.
- As in `laya_summary.py`, Brier is Σ(p − onehot)² over the two cells {false, true} (= 2(p − y)²). On a single-cell (p − y)² basis the values are halved. The Laya values equal `laya_summary.md` §1 (0.393 / 0.615, ECE 0.190 / 0.294).
- AUROC is computed Mann-Whitney style, counting ties as 0.5 (same definition as the auroc of `scripts/calibrate_ko.py`). The CI is the percentile interval of 2,000 item resamples (seed 13). Jev's p(true) is rounded to 2 decimals, so there are only 21 distinct values, and ties may lower the AUROC slightly.
- The optimal-threshold column is chosen on the same 40 rows and is therefore optimistically biased. It is not used for conclusions.

### 3.2 Agreement, exact McNemar, AUROC difference

| pair | n | same prediction | b | c | McNemar p | AUROC Jev − Laya [paired bootstrap 95%] |
|---|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 30 | 9 | 1 | 0.0215 | +0.177 [+0.043, +0.326] |
| Jev vs Laya multilingual | 40 | 23 | 15 | 2 | 0.0023 | +0.305 [+0.152, +0.486] |
| Jev vs Laya Router | 40 | 30 | 9 | 1 | 0.0215 | +0.177 [+0.043, +0.326] |

### 3.3 Confidence and abstention threshold

| system | 100% displayed (p ∈ {0, 1}) | mean top (correct / wrong) | wrong with top ≥ 0.90 | 0% shown on the gold side | distinct p(true) values |
|---|---|---|---|---|---|
| Jev | 0/40 | 0.931 / 0.697 | 0/3 | 0 | 21 |
| Laya english | 2/40 | 0.929 / 0.815 | 4/11 | 0 | 39 |
| Laya multilingual | 0/40 | 0.891 / 0.839 | 7/16 | 0 | 40 |

Abstaining by Jev's top p on the same 40 rows gives the following (descriptive statistics, not a threshold validation).

| Keep criterion | rows kept | wrong among kept rows | correct answers withheld |
|---|---|---|---|
| top ≥ 0.80 | 34/40 | 0 | 3 |
| top ≥ 0.90 | 31/40 | 0 | 6 |
| top ≥ 0.95 | 24/40 | 0 | 13 |

### 3.4 Errors

| row | question | gold | Jev p(true) | Laya english | Laya multilingual |
|---|---|---|---|---|---|
| — | — | — | — | — | — |
| — | — | — | — | — | — |
| — | — | — | — | — | — |

- All three systems got only 1 row wrong. Given its passage, the gold of that row is ambiguous.
- Jev got 9 of Laya english's 11 wrong answers right. 4 of english's wrong answers have top 0.90 or above (row 0 p(true) 0.99, row 17 0.98, row 27 0.96, row 38 0.04).

### 3.5 Context

| Figure | Value | Notes |
|---|---|---|
| Laya BoolQ upstream | english 0.830 / multilingual 0.787 (README.md:1353, N=600, in training mix) | The CI [0.572, 0.839] of this english 0.725 contains 0.830. The CI [0.446, 0.737] of multilingual 0.600 does not contain 0.787 |
| Jev BoolQ published | none | |
| Training mix | Laya: in training (per upstream). Jev: unknown | Laya is lower even though the task may favor Laya |

## 4. Calibration and confidence by task format (Jev, S1\~S3)

| Task (Jev) | format | n | accuracy | mean top p | 100% displayed | wrong with top ≥ 0.90 | gold shown at 0% | ECE |
|---|---|---|---|---|---|---|---|---|
| S1 T2 AG News | single choice 4 | 40 | 0.875 | 0.977 | 29/40 | 4/5 (≥ 93%) | 1/40 | 0.118 |
| S2 T3 Emotion | single choice 6 | 40 | 0.700 | 0.901 | 15/40 | 7/12 | 7/40 | 0.278 |
| **S3 T4 Banking77-10** | single choice 10 | 40 | 0.925 | 0.973 | 31/40 | 1/3 | 0/40 | 0.069 |
| S1·S2 T1 choice | multi choice | 50 | 0.840 | 0.735 | 8/50 | 0/8 | 0/50 | |
| S1·S2 T1 noul | multi Boolean | 60 | 0.933 | 0.732 | 0/60 | 0/4 | 0/60 | |
| **S3 T5 BoolQ** | single Boolean | 40 | 0.925 | 0.913 | 0/40 | 0/3 | 0/40 | 0.103 |

- Regardless of mode (T1 multi, T5 single), Boolean never displayed 100% (0/60, 0/40), and all wrong answers had top below 0.90 (4/4, 3/3). Single choice often displays 100% (38\~78%), and some wrong answers are at 90% or above. On T4, 2 of the 3 wrong answers were below 0.90, but one would not be filtered out.
- T4's ECE (0.069) is low, but the mean top of 0.973 exceeds the accuracy of 0.925, a mild overconfidence. On T5 the mean top 0.913 and the accuracy 0.925 differ little; that the ECE is still 0.103 is due to 40 rows being spread over 15 bins.

## 5. Latency and tokens

| Group | runs | displayed "server + network" ms median / min / max | browser POST ms median / min / max | click → complete ms median | POST − latencyMs median | input tokens median (min\~max) | output tokens median (min\~max) |
|---|---|---|---|---|---|---|---|
| Part A T4 (choice 10) | 40 | 227.5 / 181 / 417 | 470.5 / 406 / 679 | 472.5 | 237.7 | 476 (455\~546) | 116.5 (107\~125) |
| Part B T5 (Boolean) | 40 | 200.5 / 172 / 363 | 442 / 373 / 691 | 443 | 232.2 | 402.5 (330\~545) | 20 (20\~20) |
| S3 overall | 80 | 215.5 / 172 / 417 | 454.5 / 373 / 691 | | 233.8 | | |

- Token totals are input 35,756 and output 5,460 (A 19,138 / 4,660, B 16,618 / 800).
- T4 output tokens move with the option-string length of each row (Pearson r = 0.77, option totals 172\~256 characters). T3, with fixed options (6 options), stayed at 61\~62, and Boolean was constant at 20. The output may be structured as a list of per-option probabilities (inferred, to be verified). T5 input tokens correlate with the state length at r = 0.96.
- The displayed latency is at the same level as S1 T2 234 ms, S2 T3 241 ms and S2 T1 226 ms. Boolean is 27 ms faster than choice 10 (median) and has fewer output tokens. POST − latencyMs (about 234 ms) is the same as S1 232 and S2 235.6.
- Laya local latency reference: P2 laya-serve round trip 20.1 ms (`results/poc/P2_20261003.md:67`), D1 english CPU 1 question 86.6 ms (`results/D/D_summary_20261003.md:34`). Hardware and paths differ, so this is not a model-speed comparison.

## 6. Observations and limitations

**3 key observations**
1. **In the same-input paired comparison, Jev is significantly ahead of Laya base on both tasks.** T4 (held out/unknown) has b/c 9/1 and 8/1, T5 (in Laya's training mix) 9/1 and 15/2. Unlike S1 T2 (in Laya's favor, not significant) and S2 T3 (indistinguishable), the gap widened to 0.2 or more on 10-option intent and passage-based yes/no. Of the 3 T4 rows Jev got wrong, 2 are label-boundary cases where all four systems were wrong with the same label, and only 1 row was wrong for Jev alone.
2. **The T5 gap comes from discrimination.** The predicted-positive counts of the three systems (21 / 19 / 18 vs gold 20) are all balanced, yet AUROC is 0.988 vs 0.810 / 0.682, and the paired-bootstrap CIs exclude 0. Even with the optimal threshold chosen on the same 40 rows, Laya english stops at 0.775, and it gives 4 of its 11 wrong answers at 0.90 or above. This is a difference in the ranking itself, not something "recoverable by threshold or calibration" (the E6 NSMC scenario).
3. **Abstention policies must be validated separately per decision type.** Jev's Boolean never displays 100% and its wrong answers have low confidence (top 0.52\~0.79), so abstaining at top ≥ 0.80 filtered out all 3 wrong answers on the same 40 rows (withholding 3 correct ones). Single choice (T4) displays 100% in 78%, and a wrong answer at 0.90 or above remains. This is in the same direction as S2's T1 (multi) underconfidence and T3 (single choice) overconfidence.

**Limitations**
- Via the playground, not the API. The model version is not shown and the prompt wrapping is unknown. With n=40, the 95% CI width is about ±0.15.
- Jev probabilities are rounded to 2 decimals. The floor error is about ±0.005 in Brier, and Boolean p(true) has only 21 distinct values, which creates AUROC ties. The bootstrap CIs of AUROC and its differences are coarse, being resamples of n=40.
- The optimal threshold and the abstention table are descriptive statistics computed on the same 40 rows. Fixing a threshold requires validation on a separate sample.
- T5 BoolQ is in Laya's training mix, and Jev's training data is unknown. Whether these 40 rows are an easy sample could not be checked, as there is no published Jev figure. The CI of Laya english 0.725 contains upstream 0.830.
- The T4 key-only rendering is the same for both systems. Laya is sensitive to rendering (vs v0: english −0.100, multilingual +0.175). How Jev moves with `key: description` was not measured (candidate S5-b in plan §7.2).

## 7. Files

| File | Contents |
|---|---|
| `results/F/jev_cmp/sessions/S3_20261007/S3_requests.jsonl` (not included in the public repository) | 80 lines (run = item, no retries). Per decision `pred`·`probs`·`p_true`·`top_p`·`shown`·`shown_pct`; per run `latency_ms_response`·`displayed_ms`·`fetch_dur_ms`·`click_to_complete_ms`·`usage`·`confidence`·`model_id_details`. `click_epoch_ms` is on the monotonic axis (`performance.timeOrigin + performance.now()`) |
| `results/F/jev_cmp/jev_runs_all.jsonl` (not included in the public repository) | master, 231 lines (S1 41 + S1b 30 + S2 80 + S3 80). The first 151 lines are byte-identical to the pre-S3 copy |
| `raw/rNN_<T>_rowRR.json` (not included in the public repository) | 80 per-request dumps (request body, response text, DOM text and HTML, resource timing, status log, `clicks_wall`, `wall_minus_mono_ms`, result of the page limit-message check) |
| `raw/run_plan.json`, `raw/js/` (not included in the public repository) | item plan 80, instrumentation `instrument.js` (monotonic), per-item input scripts `i01~i80`, no-click dry runs `dry_i01_T4_row00.js`·`dry_i41_T5_row00.js` |
| `raw/evaluate_timing_all.json`, `raw/network_requests.txt`, `raw/network_requests_all.txt`, `raw/console.log`, `raw/mcp/` (none of the five items is included in the public repository) | 80 `/api/evaluate` resource timings and click times (monotonic and wall), network list (POST 80, all 200; GET 70 = document 1 + static 34 + RSC prefetch 35), console (193 warnings = CSS preload, 0 errors), 2 MCP snapshots and the MCP console log |
| `shots/` (not included in the public repository) | `S3_A_item01_run01_T4_row00.png`, `S3_A_item20_run20_T4_row19.png`, `S3_A_item40_run40_T4_row39.png`, `S3_B_item41_run41_T5_row00.png`, `S3_B_item60_run60_T5_row19.png`, `S3_B_item80_run80_T5_row39.png` (View details open, full page) |
| `s3_prep.py`, `s3_record.py` | generates the plan and input scripts (asserts form file ↔ Laya JSONL identity); recording wrapper (stop-condition classification, stale-dump rejection) |
| `results/F/jev_cmp/jev_cmp.py` | `analyze` extensions: Brier with per-row option sets, confusion list, Boolean branch (AUROC, bootstrap, threshold). Details in the run card |
| Reproduction | `.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S3 T4_banking77_10opt_40`, `… analyze S3 T5_boolq_40` |

**English** | [한국어](S3_summary.ko.md)
