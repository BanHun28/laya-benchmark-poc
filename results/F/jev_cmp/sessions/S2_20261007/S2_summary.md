# S2 summary: T1 typed-decisions (option A 39 + S1 row 30) + T3 DAIR Emotion 40 (2026-10-07)

**Verdict.**
1. **T1, the same 120 decisions.** Jev 104/120 = **0.867** [0.794, 0.916]. Laya english and Router 46/120 = 0.383, multilingual 44/120 = 0.367, all three below the per-question majority baseline of 0.575. Jev vs english is b=66 / c=8 (exact McNemar p < 0.0001), and vs multilingual b=66 / c=6 (p < 0.0001). The difference is significant for both choice (0.840 vs 0.280·0.320) and noul (0.933 vs 0.467·0.433); only the 10 5-level scores, with their small n, cannot be told apart (6/10 vs 4/10·2/10, p=0.69·0.29). The fine-tuned reference checkpoint (typed-decisions, not zero-shot) also scores 104/120, so zero-shot Jev is indistinguishable from this checkpoint (b=10 / c=10, p=1.0).
2. **For noul the difference persists on identical inputs.** Jev's Boolean has no description field, so it was compared with a Laya variant without criteria: Jev 56/60, Laya english no-criteria 31/60 (b=27 / c=2), multilingual no-criteria 25/60 (b=34 / c=3). The difference does not come from the information asymmetry of the true/false descriptions.
3. **On T3 there is no significant difference.** Jev 28/40 = 0.700 [0.546, 0.819], Laya english 0.750 (b=2 / c=4, p=0.69), multilingual 0.625 (b=6 / c=3, p=0.51). This seed-13 sample is on the easy side for both systems: the CI of Jev's 0.700 excludes Jev's published 0.480, and Laya english is also 0.177 above upstream 0.573. It must not be generalized by comparison with the published figures.
4. **The calibration pattern is opposite across tasks.** On T1 Jev is underconfident (mean top p 0.733, accuracy 0.867, ECE 0.181): of the 16 wrong answers, only 1 score has top ≥ 0.90, and the 4 noul wrong answers all had p(true) 0.39\~0.54. On T3 it is overconfident: 15/40 displayed 100%, 7 of the 12 wrong answers are ≥ 90%, and the gold option was displayed at 0% in 7/40 (17.5%) cases. This is similar to the published "16% of cases with probability 0 on the gold label".

Via the playground, not the API. The model version is not shown (`typesafe-ai/jev` 79/79), and the samples are small. For T1, Jev evaluated 2\~4 questions together in one request (Multiple questions), whereas Laya evaluated each question separately.

## 1. Execution overview

| Item | Value |
|---|---|
| Requests | `POST /api/evaluate` 80 = Part A 40 (success 39 + HTTP 502 1) + Part B 40 (success 40). Session cap 80, daily cap 100 |
| 502 handling | run 1 (row 0, 08:49:40) failed with `{"code":"UNAVAILABLE","message":"Jev is temporarily unavailable."}`. It was recorded immediately; after waiting over 60 s (73.7 s), the same payload was retried 1 time, and run 2 succeeded with 200 (attempt 2). After that, 5xx, 429, limit messages and captcha: 0 |
| Gaps (between Run clicks) | Wall clock: min 12.1 s, median 15.1 s, max 131.7 s. Monotonic (difference of resource timing startTime): min 12.1 s (run 4, while the guard was 12 s; raised to 15 s from run 5), 13.07 s (run 61), median 15.1 s. All 79 gaps are at least 10 s |
| Input identity | Before the request: the sha12 of the payload built from the form values matched the form file's expected value 80/80 (`window.__jev.ready`). After the request: the captured request body equals the `jev_cmp.py` payload byte for byte 80/80 (`payload_exact`) |
| Screen = response | 79/79 (DECISION and SCORE strings, bar %, `x.xx / 4` on score cards). Displayed latency = `latencyMs` rounded half-up 79/79 |
| row 30 | Not sent again. `s2_prep.py` confirmed (assert) that S1 run 1 (payload sha12 `5a9e5492744b`) equals the option-A payload, and that record was used in the analysis |
| T3 options | 6 (`sadness, joy, love, anger, fear, surprise`), in the same order as the form file for all 40 rows and all at most 80 characters (max 8 characters, `s2_prep.py` assert). Question ``Which emotion is most strongly expressed in `text`?``, State the form `state_text` |
| Measurement anomaly | Between runs 60 and 61 the host wall clock stepped by +1.98 s. The dump, which converted resource timing relative to `performance.timeOrigin`, took run 61's POST entry to be before the click and timed out after waiting 45 s (`raw/r61_T3_row20_timedout_dump1.json`, not included in the public repository). Only 1 request went out, and it returned 200. The dump and the gap guard were changed to use the `Date.now() − performance.now()` offset and the monotonic clock (`raw/js/patch_clock.js` (not included in the public repository), no request), and run 61 was dumped again and recorded. Run 61's wall-clock gap of 15.05 s is actually 13.07 s |

## 2. T1 typed-decisions (120 Jev-comparable decisions)

Scope: all comparable decisions of the 40 cases (choice 50, noul 60, 5-level score 10). The 80 excluded ones (70 4-level scores, 10 choices over 80 characters) were not sent to Jev (reason recorded in `omitted`). 1 request per case, Multiple questions mode, questions in form-file order. Questions per workflow were agent_trace 3, customer_service 2, invoice 3, security 4; no case needed Single mode. Scoring used `decisions` / `metrics` / `t1_extra` of `laya_summary.py` as is (`jev_cmp.py t1 S1,S2`). The gold is the argmax of the teacher distribution. Among these 120 there is no case where the dataset `label` ≠ argmax, no gold tie and no Jev argmax tie, so the values equal the upstream-style (label-based) accuracy.

### 2.1 Accuracy and calibration (same 120 decisions)

| system | all | choice | noul | score (5 levels, argmax) | soft acc | Brier vs soft | Brier (one-hot) | ECE (15 bins) | score MAE: E[level] vs teacher |
|---|---|---|---|---|---|---|---|---|---|
| Jev (playground) | 104/120 = 0.867 [0.794, 0.916] | 42/50 = 0.840 [0.715, 0.917] | 56/60 = 0.933 [0.841, 0.974] | 6/10 = 0.600 [0.313, 0.832] | 0.590 | 0.077 | 0.237 | 0.181 | 0.389 (Jev `score` field) / 0.390 (from rounded p) |
| Laya english | 46/120 = 0.383 [0.301, 0.473] | 14/50 = 0.280 [0.175, 0.417] | 28/60 = 0.467 [0.346, 0.591] | 4/10 = 0.400 [0.168, 0.687] | 0.361 | 0.333 | 0.724 | 0.205 | 0.584 |
| Laya multilingual | 44/120 = 0.367 [0.286, 0.456] | 16/50 = 0.320 [0.208, 0.458] | 26/60 = 0.433 [0.316, 0.559] | 2/10 = 0.200 [0.057, 0.510] | 0.351 | 0.574 | 0.949 | 0.391 | 0.671 |
| Laya Router (all 120 to english) | 46/120 = 0.383 [0.301, 0.473] | 14/50 = 0.280 [0.175, 0.417] | 28/60 = 0.467 [0.346, 0.591] | 4/10 = 0.400 [0.168, 0.687] | 0.361 | 0.333 | 0.724 | 0.205 | 0.584 |
| Reference: Laya typed-decisions (fine-tuned on typed-decisions train, not zero-shot) | 104/120 = 0.867 [0.794, 0.916] | 40/50 = 0.800 [0.670, 0.888] | 57/60 = 0.950 [0.863, 0.983] | 7/10 = 0.700 [0.397, 0.892] | 0.519 | 0.059 | 0.343 | 0.279 | 0.255 |
| Per-question majority baseline | 0.575 | | | | | | | | |

- The Laya figures equal `results/F/jev_cmp/laya_summary.md` §2 (120-decision basis); recomputed with the same code to confirm.
- Jev probabilities are rounded to two decimal places. soft accuracy and Brier vs soft were computed after normalizing by the sum (`t1_extra`). one-hot Brier and ECE use the rounded values as they are.
- score MAE is |E[level] − teacher score| over the 10 decisions. The difference between Jev's `score` (the expected value given by the server) and the expected value recomputed from the rounded probabilities is 0.001.

### 2.2 Exact McNemar (b = only Jev right, c = only Laya right)

| pair | subset | n | both right | b | c | both wrong | p |
|---|---|---|---|---|---|---|---|
| Jev vs english | all | 120 | 38 | 66 | 8 | 8 | 0.0000 |
| Jev vs english | choice | 50 | 11 | 31 | 3 | 5 | 0.0000 |
| Jev vs english | noul | 60 | 25 | 31 | 3 | 1 | 0.0000 |
| Jev vs english | score | 10 | 2 | 4 | 2 | 2 | 0.6875 |
| Jev vs multilingual | all | 120 | 38 | 66 | 6 | 10 | 0.0000 |
| Jev vs multilingual | choice | 50 | 15 | 27 | 1 | 7 | 0.0000 |
| Jev vs multilingual | noul | 60 | 23 | 33 | 3 | 1 | 0.0000 |
| Jev vs multilingual | score | 10 | 0 | 6 | 2 | 2 | 0.2891 |
| Jev vs Router | all | 120 | 38 | 66 | 8 | 8 | 0.0000 |
| Jev vs Router | choice / noul / score | 50 / 60 / 10 | same as english | | | | |
| Reference: Jev vs typed-decisions (fine-tuned) | all | 120 | 94 | 10 | 10 | 6 | 1.0000 |
| Reference: Jev vs typed-decisions | choice | 50 | 35 | 7 | 5 | 3 | 0.7744 |
| Reference: Jev vs typed-decisions | noul | 60 | 54 | 2 | 3 | 1 | 1.0000 |
| Reference: Jev vs typed-decisions | score | 10 | 5 | 1 | 2 | 2 | 1.0000 |

0.0000 means p < 0.00005 (english all: b=66, c=8).

### 2.3 noul: comparison on identical inputs (no descriptions)

Jev's Boolean takes only the question sentence. The Laya no-criteria variant (`laya/T1_typed_decisions_40_noulnocrit_{english,multilingual}.json`) is the condition in which Laya receives the same information as Jev. 20 of the 60 (duplicate, credential_compromise) have no criteria even in the original T1, so their inputs are identical in all four conditions.

| system | input | all (60) | the 40 with criteria in T1 | the 20 originally without criteria | soft acc | Brier vs soft | predicted true (gold true 23) | b / c vs Jev | McNemar p |
|---|---|---|---|---|---|---|---|---|---|
| Jev (playground) | question only | 56/60 = 0.933 [0.841, 0.974] | 37/40 = 0.925 [0.801, 0.974] | 19/20 = 0.950 [0.764, 0.991] | 0.660 | 0.045 | 23 | - | - |
| Laya english | with criteria | 28/60 = 0.467 [0.346, 0.591] | 23/40 = 0.575 [0.422, 0.715] | 5/20 = 0.250 [0.112, 0.469] | 0.462 | 0.369 | 43 | 31 / 3 | 0.0000 |
| Laya english | no criteria | 31/60 = 0.517 [0.393, 0.638] | 26/40 = 0.650 [0.495, 0.779] | 5/20 = 0.250 [0.112, 0.469] | 0.483 | 0.403 | 32 | 27 / 2 | 0.0000 |
| Laya multilingual | with criteria | 26/60 = 0.433 [0.316, 0.559] | 18/40 = 0.450 [0.307, 0.602] | 8/20 = 0.400 [0.219, 0.613] | 0.407 | 0.723 | 41 | 33 / 3 | 0.0000 |
| Laya multilingual | no criteria | 25/60 = 0.417 [0.301, 0.543] | 17/40 = 0.425 [0.285, 0.578] | 8/20 = 0.400 [0.219, 0.613] | 0.398 | 0.775 | 42 | 34 / 3 | 0.0000 |

Jev predicted true 23 times, and there are also 23 gold trues. Laya leans heavily toward true (41\~43; only no-criteria english is at 32).

### 2.4 By workflow and question (correct / n)

| workflow | question | type | n | Jev | english | multilingual | Router | typed-decisions (reference) |
|---|---|---|---|---|---|---|---|---|
| agent_trace_observability | action | choice | 10 | 8 | 4 | 2 | 4 | 7 |
| | needs_review | noul | 10 | 9 | 7 | 6 | 7 | 9 |
| | outcome | choice | 10 | 8 | 3 | 3 | 3 | 8 |
| | **all** | | 30 | 25 | 14 | 11 | 14 | 24 |
| customer_service | category | choice | 10 | 10 | 4 | 8 | 4 | 8 |
| | needs_human | noul | 10 | 9 | 7 | 4 | 7 | 10 |
| | **all** | | 20 | 19 | 11 | 12 | 11 | 18 |
| invoice_processing | disposition | choice | 10 | 9 | 2 | 2 | 2 | 8 |
| | duplicate | noul | 10 | 10 | 0 | 0 | 0 | 10 |
| | matches_order | noul | 10 | 10 | 2 | 2 | 2 | 9 |
| | **all** | | 30 | 29 | 4 | 4 | 4 | 27 |
| security_incidents | credential_compromise | noul | 10 | 9 | 5 | 8 | 5 | 9 |
| | disposition | choice | 10 | 7 | 1 | 1 | 1 | 9 |
| | severity | score | 10 | 6 | 4 | 2 | 4 | 7 |
| | true_positive | noul | 10 | 9 | 7 | 6 | 7 | 10 |
| | **all** | | 40 | 31 | 17 | 17 | 17 | 35 |

Workflow accuracy: Jev 0.833 / 0.950 / 0.967 / 0.775, Laya english 0.467 / 0.550 / 0.133 / 0.425. The largest gap is invoice_processing (29/30 vs 4/30). The Laya base checkpoints get almost everything wrong on duplicate (0/10) and matches_order (2/10).

### 2.5 score (security_incidents/severity, 5 levels)

| row | gold level | teacher E | Jev p(0..4) (Jev's per-item outputs are omitted in the public repository) | Jev `score` | Jev argmax | Jev displayed level | Laya en E / argmax | Laya ml E / argmax |
|---|---|---|---|---|---|---|---|---|
| 30 | 2 | 1.62 | — | — | — | — | 1.62 / 1 X | 1.02 / 0 X |
| 31 | 3 | 2.73 | — | — | — | — | 1.81 / 2 X | 1.36 / 1 X |
| 32 | 2 | 1.19 | — | — | — | — | 1.79 / 2 | 1.56 / 1 X |
| 33 | 2 | 1.88 | — | — | — | — | 2.11 / 2 | 1.56 / 1 X |
| 34 | 3 | 2.46 | — | — | — | — | 1.47 / 1 X | 1.68 / 1 X |
| 35 | 1 | 1.65 | — | — | — | — | 1.99 / 1 | 1.79 / 1 |
| 36 | 3 | 2.77 | — | — | — | — | 2.05 / 2 X | 1.60 / 1 X |
| 37 | 2 | 2.26 | — | — | — | — | 2.17 / 2 | 1.94 / 2 |
| 38 | 3 | 2.14 | — | — | — | — | 0.90 / 0 X | 1.34 / 1 X |
| 39 | 3 | 2.81 | — | — | — | — | 2.11 / 1 X | 1.98 / 2 X |

- Under the fixed rule (argmax level), Jev scores 6/10. By the level shown on screen (nearest to E[level]) it is 7/10; the two differ in only 1 case.
- MAE: Jev 0.389, Laya english 0.584, multilingual 0.671, fine-tuned 0.255. Jev's E[level] is biased upward relative to the teacher (9 of 10 above teacher E, mean +0.35).

### 2.6 Comparison with published figures (context only)

| Metric | Jev, these 120 decisions | Jev published (BENCHMARKS.md, 3rd-party, Jev 1.13.0) | Notes |
|---|---|---|---|
| accuracy | 0.867 [0.794, 0.916] | 0.727 | The published figure is over 2,000 decisions against the dataset label and includes 4-level scores and options over 80 characters. Through the same subset effect, Laya english also rises from 0.330 (200) to 0.383 (120) |
| soft accuracy | 0.590 | 0.580 | |
| Brier (vs soft) | 0.077 | 0.148 | Jev probabilities rounded to 2 decimals |
| ECE | 0.181 | 0.144 | 15 bins; the bins are sparse because of rounding |
| score MAE | 0.389 (n=10) | 0.391 | With n=10 the numerical match is at the level of chance |

## 3. T3 DAIR Emotion (40, Single question / Choice)

### 3.1 Accuracy and McNemar

| system | correct / n | accuracy [Wilson 95%] | Brier | ECE (15 bins) | mean top p |
|---|---|---|---|---|---|
| Jev (playground, displayed p, rounded to 2 decimals) | 28/40 | 0.700 [0.546, 0.819] | 0.537 | 0.278 | 0.901 |
| Laya english | 30/40 | 0.750 [0.598, 0.858] | 0.429 | 0.174 | 0.900 |
| Laya multilingual | 25/40 | 0.625 [0.470, 0.758] | 0.631 | 0.313 | 0.924 |
| Laya Router (all 40 to english) | 30/40 | 0.750 [0.598, 0.858] | 0.429 | 0.174 | 0.900 |

| pair | n | same label | b | c | exact McNemar p |
|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 32 | 2 | 4 | 0.6875 |
| Jev vs Laya multilingual | 40 | 27 | 6 | 3 | 0.5078 |
| Jev vs Laya Router | 40 | 32 | 2 | 4 | 0.6875 |

### 3.2 Correct per class and Jev confusions

| gold | n | Jev | Laya english | Laya multilingual | Laya Router |
|---|---|---|---|---|---|
| sadness | 7 | 7 | 6 | 6 | 6 |
| joy | 7 | 5 | 7 | 5 | 7 |
| love | 7 | 3 | 3 | 4 | 3 |
| anger | 7 | 5 | 6 | 4 | 6 |
| fear | 6 | 5 | 4 | 3 | 4 |
| surprise | 6 | 3 | 4 | 3 | 4 |

| gold \ Jev | sadness | joy | love | anger | fear | surprise |
|---|---|---|---|---|---|---|
| sadness | 7 | 0 | 0 | 0 | 0 | 0 |
| joy | 1 | 5 | 1 | 0 | 0 | 0 |
| love | 0 | 3 | 3 | 0 | 1 | 0 |
| anger | 1 | 0 | 0 | 5 | 1 | 0 |
| fear | 1 | 0 | 0 | 0 | 5 | 0 |
| surprise | 1 | 0 | 1 | 0 | 1 | 3 |

4 of Jev's 12 wrong answers went to sadness (1 each from fear·joy·surprise·anger, top p 97\~100%), and 3 are love → joy. All three systems got 7 rows wrong, and on most of them all three chose the same label (joy or sadness).

### 3.3 Caveat: an easy sample

| System | Our seed-13 40 rows | Reference | Difference |
|---|---|---|---|
| Jev | 0.700 [0.546, 0.819] | published 0.480 (Jev's own 100-item sample, 3rd-party) | +0.220, outside the CI |
| Laya english | 0.750 [0.598, 0.858] | upstream 0.573 (first 600 test rows; reproduced with our pipeline as 0.5733, `laya_summary.md` §6) | +0.177 |
| Laya multilingual | 0.625 | upstream 0.513 / 0.530 | +0.095\~0.112 |

This sample is easy for both systems. It can be used for the paired comparison (McNemar), but its absolute accuracy must not be generalized by comparison with the published figures. That Jev and Laya english rose by similar amounts on a sample drawn with the same seed means that both get the same easy items right (same label 32/40).

### 3.4 Confidence

| System | top = 100% | mean top (correct / wrong) | wrong with top ≥ 0.90 | gold option shown at 0% | mean provider confidence (correct / wrong) |
|---|---|---|---|---|---|
| Jev | 15/40 (38%) | 0.900 (0.918 / 0.861) | 7/12 | 7/40 = 17.5% (published 16%) | 0.878 (0.899 / 0.830) |
| Laya english | - | 0.900 (0.923 / 0.834) | 4/10 | - | - |
| Laya multilingual | - | 0.924 (0.951 / 0.880) | 9/15 | - | - |

3 of Jev's wrong answers displayed 100% (joy → sadness, surprise → sadness, love → joy). 0% cells: 153/240.

## 4. Calibration and confidence: comparison by task

| Task (Jev) | n | accuracy | mean top p | wrong with top ≥ 0.90 | ECE | Interpretation |
|---|---|---|---|---|---|---|
| T1 choice (multi) | 50 | 0.840 | 0.735 | 0/8 | | top p of the wrong answers 0.42\~0.76 |
| T1 noul (multi) | 60 | 0.933 | 0.732 | 0/4 | | only 4 with p(true) ≥ 0.80 and 19 with ≤ 0.20; the 4 wrong answers are at 0.39\~0.54 |
| T1 score (multi) | 10 | 0.600 | 0.729 | 1/4 | | — |
| T1 overall | 120 | 0.867 | 0.733 | 1/16 | 0.181 | underconfident |
| T3 (single) | 40 | 0.700 | 0.901 | 7/12 | 0.278 | overconfident |
| Reference: S1 T2 AG News (single) | 40 | 0.875 | 0.977 | 4/5 (≥ 93%) | 0.118 | overconfident (`S1_summary.md`) |

On T1, the lower Jev's top p, the more likely the answer is actually wrong (mean 0.758 for correct, 0.569 for wrong), so a threshold (e.g. abstain below 0.60) has room to filter out wrong answers. On single-choice tasks such as T2 and T3, most wrong answers are at 90% or above, so the same method does not work. provider confidence (which on T1 comes only for choice and score) points the same way (T1 correct 0.711 / wrong 0.454).

## 5. Latency and tokens

| Group | runs | displayed "server + network" ms median / min / max | browser POST ms median / min / max | click → complete ms median | input tokens median (min\~max) | output tokens median (min\~max) |
|---|---|---|---|---|---|---|
| Part A T1 (S2, 2\~4 questions/request) | 39 | 226 / 164 / 355 | 481 / 409 / 847 | 483 | 760 (640\~953) | 141 (138\~214) |
| T1 2 questions (customer_service) | 10 | 221 / 184 / 262 | 471.5 / 428 / 680 | | 741.5 (640\~953) | 138 (138\~140) |
| T1 3 questions (agent_trace, invoice) | 20 | 225.5 / 164 / 355 | 478.5 / 409 / 758 | | 731.5 (679\~799) | 172.5 (141\~214) |
| T1 4 questions (security, incl. S1 row 30) | 10 | 239 / 211 / 299 | 483.5 / 455 / 847 | | 863.5 (803\~903) | 162 (161\~166) |
| Part B T3 (single) | 40 | 241 / 170 / 713 | 469 / 406 / 951 | 471.5 | 387.5 (372\~422) | 61 (61\~62) |
| S2 overall | 79 | 229 / 164 / 713 | 476 / 406 / 951 | 479 | 422 (372\~953) | 62 (61\~214) |

- The rows by number of questions (up to row 4) are `jev_cmp.py t1` output and include S1 row 30 (40 runs). The first row is S2's 39 runs.
- A T1 multi request returns 2\~4 questions at once. Dividing the displayed latency by the number of questions gives medians of 111 ms for 2 questions, 75 ms for 3 and 60 ms for 4. Per-request latency barely scales with the number of questions (221 → 239 ms).
- The median of browser POST − latencyMs is 235.6 ms (the same level as S1 232 and S1b 234).
- Token totals are input 45,616 and output 8,806 (A 30,023 / 6,352, B 15,593 / 2,454).
- Laya local latency reference: P2 laya-serve round trip 20.1 ms (`results/poc/P2_20261003.md:67`), D1 english CPU 1 question 86.6 ms (`results/D/D_summary_20261003.md:34`). Hardware and paths differ, so this is not a model-speed comparison.

## 6. Observations and limitations

**3 key observations**
1. **On T1, zero-shot Jev is at the level of the fine-tuned Laya checkpoint, while Laya base (english, multilingual, Router) is below the majority baseline.** The gap is not explained by the noul criteria asymmetry (b=27\~34 / c=2\~3 even in the no-criteria variants). This agrees with Laya's own assessment, "Laya is a fast base to specialise, not a zero-shot decision engine" (upstream README, "Honest limits").
2. **On T3, Jev and Laya english cannot be told apart** (0.700 vs 0.750, b=2 / c=4). Both are 0.18\~0.22 above their published figures on this sample, and they get the same 7 rows wrong. The love/joy and surprise boundaries are a shared weakness.
3. **What Jev's probabilities mean depends on the task format.** In Multiple questions on T1 it is underconfident, and its wrong answers have low confidence. In single choice (T2, T3), many wrong answers are displayed at 90\~100%. A threshold-based abstention policy built on Jev's probabilities needs per-task validation.

**Limitations**
- Via the playground, not the API. The model version is not shown and the prompt wrapping is unknown. n is small (T1 120, T3 40).
- For T1, Jev evaluated the 2\~4 questions of a case together in one request ("evaluated together against the same State"); Laya evaluated each question as an independent row. This design cannot isolate the effect of joint evaluation on accuracy.
- The T1 gold is the argmax of the teacher distribution. The relation between the teacher model and Jev could not be checked (to be verified). Since the published Jev 0.727 is close to the teacher ceiling of 0.735 (`docs/01_laya_analysis.md` §(b)), an alignment effect with the teacher cannot be ruled out.
- 70 4-level scores and 10 choices over 80 characters were excluded, so the question mix differs from the published figure (2,000 decisions). score MAE has n=10.
- Jev probabilities are rounded to two decimal places (floor error of Brier and ECE about ±0.005). T3 has many 100% and 0% displays, so the ECE bins are sparse.
- 1 measurement anomaly (wall-clock step): no effect on the request count or the results. Run 61's gap is 15.05 s by wall clock and 13.07 s by monotonic clock.

## 7. Files

| File | Contents |
|---|---|
| `results/F/jev_cmp/sessions/S2_20261007/S2_requests.jsonl` (not included in the public repository) | 80 lines (run 1 = 502, run 2 = row 0 retry). Per decision `pred`·`probs`·`p_true`·`score`·`shown` (display string)·`shown_pct`; per run `latency_ms_response`·`displayed_ms`·`fetch_dur_ms`·`usage`·`confidence`·`model_id_details` |
| `results/F/jev_cmp/jev_runs_all.jsonl` (not included in the public repository) | master, 151 lines (S1 41 + S1b 30 + S2 80) |
| `results/F/jev_cmp/sessions/S2_20261007/raw/rNN_<T>_rowRR.json` (not included in the public repository) | 80 per-request dumps (request body, response text, DOM text and HTML, resource timing, status log) + `r61_T3_row20_timedout_dump1.json` |
| `raw/run_plan.json`, `raw/js/iNN_*.js`, `raw/js/instrument.js`, `raw/js/patch_clock.js`, `raw/js/dry_i40_T3_row00.js` (`raw/js/` is not included in the public repository) | item plan (79), per-item Playwright input scripts (generated from the form file), instrumentation code, clock patch, Part B no-click dry run |
| `raw/evaluate_timing_all.json`, `raw/network_requests.txt`, `raw/console.log`, `raw/mcp/` (none of the four items is included in the public repository) | 80 `/api/evaluate` resource timings (monotonic), network list (POST 80: 200 for 79, 502 for 1; GET 39), console (per the MCP log, 1 error = the 502, the rest CSS preload warnings), copies of the 3 MCP snapshots and of the console log |
| `results/F/jev_cmp/sessions/S2_20261007/shots/` (not included in the public repository) | `S2_A_item01_run02_T1_row00.png`, `S2_A_item20_run21_T1_row19.png`, `S2_A_item39_run40_T1_row39.png`, `S2_B_item01_run41_T3_row00.png`, `S2_B_item20_run60_T3_row19.png`, `S2_B_item40_run80_T3_row39.png` (View details open) |
| `results/F/jev_cmp/sessions/S2_20261007/s2_prep.py`, `s2_record.py` | generates the plan and input scripts; recording wrapper (stop-message check) |
| `results/F/jev_cmp/jev_cmp.py` | `t1` subcommand added, `record` slightly extended (see the run card) |

**English** | [한국어](S2_summary.ko.md)
