# S4 summary: T6 SST-5 40 (Score, 5 levels) + T7 MASSIVE intent-10 en 20 · de 20 (2026-10-07)

**Verdict.**
1. **On T6 SST-5, Jev's errors are clearly smaller than those of all three Laya runners, but on the primary metric (argmax accuracy) it is not significantly different from english.** argmax-level accuracy: Jev 26/40 = **0.650** [0.495, 0.779], Laya english and Router 0.425, multilingual 0.325. exact McNemar (b/c): Jev vs english 15/6 p=0.078, vs multilingual 18/5 p=0.011. On the secondary metric (the level obtained by rounding E[level], the playground's display rule) it is 0.675 vs 0.400 / 0.325, with 15/4 p=0.019 and 19/5 p=0.007. The MAE of E[level] is Jev **0.432**, english 0.888, multilingual 1.419. The paired-bootstrap differences are −0.456 [−0.711, −0.207] and −0.987 [−1.341, −0.622]; neither pair's CI contains 0. Brier (5 levels) is 0.502 / 0.770 / 1.149.
2. **Laya's T6 failure is scale compression; the first-level avoidance of #131 was not reproduced on this sample.** The mean signed error (E − gold) is Jev −0.014, english −0.687, multilingual −1.280. english never chose level 4 (0/40, gold 8/40). multilingual chose level 0 or 1 on all 40 rows (11 / 29; levels 2\~4: 0/40). multilingual's first-level selections are 11/40, more than the gold 8/40. Jev's level distribution is 4/13/6/12/5, choosing the two end levels less often (first level 4/40, last level 5/40).
3. **On T7 MASSIVE-10, Jev had the same accuracy in en and de, while Laya dropped sharply in de.** Jev: en 18/20, de 18/20 (0.900). Laya english 0.70 → 0.35, multilingual 0.85 → 0.40, Router 0.70 → 0.35. In de, Jev vs english is b/c 11/0 p=0.001, vs multilingual 11/1 p=0.006. In en, at 4/0 p=0.125 and 3/2 p=1.0, they cannot be told apart. Pooling en+de 40 gives Jev 36/40 = 0.900, english 21/40, multilingual 25/40, with b/c 15/0 p=0.0001 and 14/3 p=0.013. The share of ids with the same label in en and de is Jev 19/20, english 10/20, multilingual 7/20. The per-language results at n=20 are directional signals.
4. **Operations:** all 80 requests (A 40 + B 20 + C 20) returned HTTP 200. 5xx, 4xx (including 429), limit messages and captcha: 0, and no retries. Gaps on the monotonic clock: min 15.013 s, median 15.125 s. Today's cumulative total is S2 80 + S3 80 + S4 80 = 240, with no limit signal to the end.

Via the playground, not the API. The model version is not shown (`typesafe-ai/jev` 80/80). Samples: T6 n=40, T7 n=20 per language. Jev's probabilities and score are rounded to two decimal places. Per upstream, T6 (SST-5) is held out for Laya, and T7 is unknown. Jev's training data is unknown.

## 1. Execution overview

| Item | Value |
|---|---|
| Requests | `POST /api/evaluate` 80 = Part A (T6) 40 + Part B (T7 en) 20 + Part C (T7 de) 20, all HTTP 200. Session cap 100 (planned 80); the daily cap was lifted by an owner decision (2026-10-07) |
| Stop conditions | 5xx 0, 4xx 0 (429 0), limit messages 0, captcha 0, error screens 0. After every run, the result panel, status, title, `[role=alert]` and body text were checked with a limit-message regex, and the presence of a captcha iframe was checked (`s4_record.py`, dump `page`). All 80 had `body_stop_match` null, alerts [], captcha_frames [] |
| Gaps (between Run clicks) | Guard 15 s, monotonic from the start (`performance.timeOrigin + performance.now()`). 79 gaps: min 15.013 s, median 15.125 s, max 31.109 s (run 2, time for the run 1 screenshot). Re-measured from resource timing `startTime` differences: 15.014 / 15.125 / 31.105 s. At the part boundaries (runs 41, 61) the gaps were 21.1 s because of dry runs and screenshots |
| Input identity | Before the request: the payload sha12 built from the form values matched the form file's expected value 80/80 (`window.__jev.ready`). After the request: the captured request body equals the `jev_cmp.py` payload byte for byte 80/80 (`payload_exact`). 3 no-click dry runs (items 1, 41, 61) |
| Input content | T6: Single / Score. The form `options` were entered as they are in the Rubric level 0\~4 fields (`level 0: very negative` … `level 4: very positive`, up to 22 characters). These strings equal the rendering Laya reads for score questions (`laya/common.py` `render_options`: `"level %d: %s"`), and `s4_prep.py` asserted the match with `render_options(Agent._to_internal(q))` for all 40 rows. The T1 score runs of S1 and S2 sent the same rendering (S1 run 1 request body). T7: Single / Choice. The 10 options `key: key spaced` (up to 50 characters) were entered in form order. en and de have the same id, gold and option list (`s4_prep.py` assert). In all tasks, State is the JSON string Laya reads (`state_text`) |
| Screen = response | 80/80. For T6, the SCORE card (displayed level = `rubric[Math.round(score)]`, "x.xx / 4", bars "k — level k: …") was checked against the response. In single mode the Score card is headed SCORE rather than DECISION, so `parse_single_display` was adjusted accordingly (§7 below). Displayed latency = `latencyMs` half-up 80/80 |
| Model ID / response metadata | `model` and View details both `typesafe-ai/jev` 80/80. `rounding` {2, 2}, `warnings` [] 80/80. provider `confidence.decision` is present in 80/80 (including T6). Jev's T6 score was a non-integer in 40/40 ("Nearest rubric level. Jev returned an interpolated score.") |

## 2. T6 SST-5 (40 rows, 8 per gold level 0\~4)

Jev's E[level] is the response `score` (two decimal places), and Laya's E[level] is `answer.score`. On ties argmax takes the lower level (same as `np.argmax`); Jev had no argmax tie in these 40 rows. The difference between Jev's `score` and Σ k·p_k computed from the rounded probabilities is at most 0.020.

### 2.1 Accuracy, error and calibration (same 40 rows, same question and level wording)

| system | argmax level correct [Wilson 95%] | rounded E[level] correct [Wilson 95%] | MAE E[level] | mean E − gold | within ±1 level | Brier (5 levels) | ECE (15 bins, argmax p) | mean top p | argmax ≠ rounded E |
|---|---|---|---|---|---|---|---|---|---|
| Jev (playground, displayed p, 2 decimals) | 26/40 = **0.650** [0.495, 0.779] | 27/40 = 0.675 [0.520, 0.799] | **0.432** | −0.014 | 0.875 | 0.502 | 0.184 | 0.751 | 2 |
| Laya english | 17/40 = 0.425 [0.285, 0.578] | 16/40 = 0.400 [0.263, 0.554] | 0.888 | −0.687 | 0.650 | 0.770 | 0.239 | 0.654 | 6 |
| Laya multilingual | 13/40 = 0.325 [0.201, 0.480] | 13/40 = 0.325 [0.201, 0.480] | 1.419 | −1.280 | 0.400 | 1.149 | 0.513 | 0.824 | 0 |
| Laya Router (all 40 to english) | 17/40 = 0.425 | 16/40 = 0.400 | 0.888 | −0.687 | 0.650 | 0.770 | 0.239 | 0.654 | 6 |

- The Laya values equal `laya_summary.json` `results.T6_sst5_40` (accuracy 0.425 / 0.325, brier 0.770 / 1.149, ece 0.239 / 0.513, score_mae 0.888 / 1.419, within_1_level 0.650 / 0.400).
- For Jev, the display rule (rounded E) and argmax diverged on 2 rows. 1 row was right only by the displayed level, and 1 row was wrong under both (Jev's per-item outputs are omitted in the public repository). So the display rule gets 1 more row right. For Laya english, conversely, the display rule costs 1 row (17 → 16).

### 2.2 Agreement, exact McNemar, MAE difference (b = only Jev right, c = only Laya right)

| pair | n | same argmax | argmax b / c | p | rounded E b / c | p | MAE Jev − Laya [paired bootstrap 95%] |
|---|---|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 17 | 15 / 6 | 0.0784 | 15 / 4 | 0.0192 | −0.456 [−0.711, −0.207] |
| Jev vs Laya multilingual | 40 | 11 | 18 / 5 | 0.0106 | 19 / 5 | 0.0066 | −0.987 [−1.341, −0.622] |
| Jev vs Laya Router | 40 | 17 | 15 / 6 | 0.0784 | 15 / 4 | 0.0192 | −0.456 [−0.711, −0.207] |

The bootstrap uses 2,000 item resamples, seed 13, percentile intervals. On the primary metric (argmax), Jev vs english cannot be told apart at n=40 (p=0.078). On the secondary metric and on MAE the difference excludes 0. 7 rows are wrong by argmax for all three systems.

### 2.3 Predicted-level distribution and first/last level selection rate

| system | rule | level 0 | 1 | 2 | 3 | 4 | first level chosen | last level chosen |
|---|---|---|---|---|---|---|---|---|
| gold | - | 8 | 8 | 8 | 8 | 8 | 8/40 | 8/40 |
| Jev | argmax | 4 | 13 | 6 | 12 | 5 | 4/40 | 5/40 |
| Jev | rounded E | 4 | 12 | 8 | 11 | 5 | 4/40 | 5/40 |
| Laya english (= Router) | argmax | 10 | 15 | 10 | 5 | 0 | 10/40 | **0/40** |
| Laya english (= Router) | rounded E | 6 | 18 | 12 | 4 | 0 | 6/40 | 0/40 |
| Laya multilingual | argmax | 11 | 29 | 0 | 0 | 0 | 11/40 | **0/40** |
| Laya multilingual | rounded E | 11 | 29 | 0 | 0 | 0 | 11/40 | 0/40 |

- **#131 (multilingual avoiding the first level) did not appear on this T6.** multilingual chose level 0 in 11/40, more than the gold (8/40). The actual failure is on the other side: it never chose levels 2\~4 (0/40, gold 24/40), and the mean E of the 8 rows with gold 4 is 1.02. However, SST-5's level 0 means "very negative", so position and content effects are mixed. This sample does not refute #131 (both the rubric and the language differ from P0·P0b, where the Korean frustration level 0 was chosen 0/30).
- english never chose the last level (0/40). Of the 8 rows with gold 4, it chose 3 for 5 rows, 2 for 2 rows, and 0 for 1 row (row 21 "gosling provides an amazing performance…", E 0.53).
- Jev pulls both ends inward: of the 8 rows with gold 0 it chose 1 for 4, and of the 8 rows with gold 4 it chose 3 for 3. Its mean signed error is still −0.014, i.e. unbiased.

### 2.4 Correct answers per gold level and confusions

| gold level | n | Jev argmax correct (mean E) | Laya english | Laya multilingual |
|---|---|---|---|---|
| 0 | 8 | 4 (0.47) | 6 (0.45) | 6 (0.29) |
| 1 | 8 | 6 (1.07) | 7 (0.83) | 7 (0.87) |
| 2 | 8 | 4 (1.85) | 4 (1.30) | 0 (0.58) |
| 3 | 8 | 7 (2.89) | 0 (1.58) | 0 (0.83) |
| 4 | 8 | 5 (3.65) | 0 (2.41) | 0 (1.02) |

Jev's mean E nearly tracks the gold (0.47 → 3.65). english rises monotonically but is compressed to 0.45 → 2.41. multilingual is practically flat at 0.29\~1.02. Both Laya checkpoints have 0 argmax-correct answers on the 16 rows with gold 3·4.

Confusion matrix (argmax, rows = gold, columns = prediction)

| gold \ pred | Jev 0 | 1 | 2 | 3 | 4 | | Laya english 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | **4** | 4 | 0 | 0 | 0 | | **6** | 2 | 0 | 0 | 0 |
| 1 | 0 | **6** | 1 | 1 | 0 | | 1 | **7** | 0 | 0 | 0 |
| 2 | 0 | 3 | **4** | 1 | 0 | | 0 | 4 | **4** | 0 | 0 |
| 3 | 0 | 0 | 1 | **7** | 0 | | 2 | 2 | 4 | **0** | 0 |
| 4 | 0 | 0 | 0 | 3 | **5** | | 1 | 0 | 2 | 5 | **0** |

- 13 of Jev's 14 wrong answers are an adjacent level. Only 1 is off by two or more levels (gold 1).
- Of Laya english's 23 wrong answers, 7 are off by 2 or more levels (gold 3 → 0·1: 4 rows, gold 4 → 0·2: 3 rows).
- Of the 6 rows that only english got right and Jev got wrong (c), all except 1 row (off by 2 levels) are off by one level, and 2 of them are gold 0 → Jev 1.

### 2.5 Confidence (Jev displayed top p)

| system | 100% displayed | mean top p (correct / wrong) | wrong with top ≥ 0.90 | gold level shown at 0% | mean provider confidence (correct / wrong) |
|---|---|---|---|---|---|
| Jev | 0/40 | 0.751 (0.785 / 0.688) | 0/14 | 1/40 | 0.776 (0.812 / 0.710) |
| Laya english | - | 0.654 (0.711 / 0.612) | 0/23 | - | - |
| Laya multilingual | - | 0.824 (0.862 / 0.806) | 10/27 | - | - |

- On Score, Jev never displayed 100% (in contrast with choice: T4 31/40, T7 27/40). provider confidence equals top p in only 6/40, so it is a separate statistic (range 0.37\~0.99).
- multilingual gave 10 of its 27 wrong answers at 0.90 or above: while crowding into levels 0·1, it is highly confident.

### 2.6 Context (non-comparable figures, for reference)

| Figure | Value | Relation to this measurement |
|---|---|---|
| Laya SST-5 upstream (N=600, held out) | english 0.372 / MAE 0.905 / ±1 0.632, multilingual 0.282 / 1.359 / 0.450 (`laya_summary.md` §3, research/results/t4_colab_benchmark.json) | The CI [0.285, 0.578] of this english 0.425 and the CI [0.201, 0.480] of multilingual 0.325 each contain the upstream value. The sample does not deviate much from upstream |
| Jev SST-5 published | none | |
| Training mix | Laya: held out (README.md:1356). Jev: unknown | |

## 3. T7 MASSIVE intent-10 (en 20 · de 20, same id, gold and options)

### 3.1 Accuracy and calibration by language

| lang | system | correct / n | accuracy [Wilson 95%] | Brier | ECE | mean top p |
|---|---|---|---|---|---|---|
| en | Jev | 18/20 | **0.900** [0.699, 0.972] | 0.143 | 0.092 | 0.934 |
| en | Laya english | 14/20 | 0.700 [0.481, 0.855] | 0.394 | 0.214 | 0.899 |
| en | Laya multilingual | 17/20 | 0.850 [0.640, 0.948] | 0.293 | 0.184 | 0.895 |
| en | Laya Router (all 20 to english) | 14/20 | 0.700 | 0.394 | 0.214 | 0.899 |
| de | Jev | 18/20 | **0.900** [0.699, 0.972] | 0.150 | 0.086 | 0.940 |
| de | Laya english | 7/20 | 0.350 [0.181, 0.567] | 1.046 | 0.513 | 0.848 |
| de | Laya multilingual | 8/20 | 0.400 [0.219, 0.613] | 0.890 | 0.453 | 0.797 |
| de | Laya Router (multilingual 15 / english 5) | 7/20 | 0.350 [0.181, 0.567] | 1.009 | 0.485 | 0.835 |

The Laya accuracies equal `laya_summary.md` §4 (en .70 / .85 / .70, de .35 / .40 / .35). Brier was computed for each row over that row's 10 options (S3 fix).

### 3.2 Agreement and exact McNemar

| lang | pair | same label | b | c | p |
|---|---|---|---|---|---|
| en | Jev vs Laya english | 14 | 4 | 0 | 0.1250 |
| en | Jev vs Laya multilingual | 15 | 3 | 2 | 1.0000 |
| en | Jev vs Laya Router | 14 | 4 | 0 | 0.1250 |
| de | Jev vs Laya english | 8 | 11 | 0 | **0.0010** |
| de | Jev vs Laya multilingual | 7 | 11 | 1 | **0.0063** |
| de | Jev vs Laya Router | 6 | 12 | 1 | **0.0034** |

### 3.3 en + de pooled (40)

| system | correct / 40 | accuracy [Wilson 95%] | Brier | ECE | b / c vs Jev | McNemar p |
|---|---|---|---|---|---|---|
| Jev | 36 | 0.900 [0.769, 0.960] | 0.147 | 0.088 | - | - |
| Laya english | 21 | 0.525 [0.375, 0.671] | 0.720 | 0.363 | 15 / 0 | 0.0001 |
| Laya multilingual | 25 | 0.625 [0.470, 0.758] | 0.592 | 0.250 | 14 / 3 | 0.0127 |
| Laya Router | 21 | 0.525 [0.375, 0.671] | 0.701 | 0.350 | 16 / 1 | 0.0003 |

The pooled 40 contain the same 20 ids twice, so they are not an independent sample. McNemar p assumes independent rows and is therefore optimistic. It is used only to summarize the direction of the language difference.

### 3.4 Cross-language consistency (same id, en vs de)

| system | same label in both languages | both correct | only en correct | only de correct | both wrong |
|---|---|---|---|---|---|
| Jev | 19/20 | 18 | 0 | 0 | 2 |
| Laya english | 10/20 | 7 | 7 | 0 | 6 |
| Laya multilingual | 7/20 | 7 | 10 | 1 | 2 |
| Laya Router | 6/20 | 5 | 9 | 2 | 4 |

Jev got the same two ids wrong in en and de and all other 18 ids right. Its output tokens are also the same in en and de for 19/20 ids. Laya multilingual got 10 of the 17 ids it got right in en wrong in de.

### 3.5 Confidence

| lang | system | 100% displayed | mean top (correct / wrong) | wrong with top ≥ 0.90 | gold option shown at 0% | provider confidence (correct / wrong) |
|---|---|---|---|---|---|---|
| en | Jev | 15/20 | 0.968 / 0.635 | 1/2 | 0 | 0.964 / 0.585 |
| de | Jev | 12/20 | 0.971 / 0.665 | 1/2 | 0 | 0.968 / 0.630 |
| en | Laya english / multilingual | - | 0.981 / 0.707, 0.911 / 0.806 | 1/6, 2/3 | - | - |
| de | Laya english / multilingual | - | 0.958 / 0.788, 0.927 / 0.711 | 6/13, 5/12 | - | - |

In de, Laya gave nearly half of its wrong answers at 0.90 or above (english 6/13, multilingual 5/12, Router 7/13). Jev has many 0% cells (328/400), but no row shows the gold option at 0%.

### 3.6 Jev errors (4 = 2 ids × 2 languages)

| row (id) | utterance (en / de) | gold | Jev en / de (top) | Laya english en / de | Laya multilingual en / de |
|---|---|---|---|---|---|
| — | — | — | — | — | — |
| — | — | — | — | — | — |

Both ids are cases where the MASSIVE label is hard to determine from the utterance alone. This judgment is an interpretation made from reading the utterances; scoring used the dataset labels as they are. In both languages, Jev gave one of the two ids a low value (below 0.40) and the other 0.90 or above.

### 3.7 Context

| Figure | Value | Notes |
|---|---|---|
| Laya MASSIVE upstream (20 options) | en english 0.820 / multilingual 0.710, de 0.420 / 0.500 (CPU sweep, `laya_summary.md` §4) | Different number of options (10 vs 20), so only the direction is considered. The direction of Laya dropping sharply in de is the same as upstream |
| Jev MASSIVE published | none | |
| Training mix | unknown (04 §1 rule). Upstream lists MASSIVE as not trained on | |

## 4. Latency and tokens

| Group | runs | displayed "server + network" ms median / min / max | browser POST ms median / min / max | click → complete ms median | POST − latencyMs median | input tokens median (min\~max) | output tokens median (min\~max) |
|---|---|---|---|---|---|---|---|
| Part A T6 (Score) | 40 | 236 / 172 / 348 | 477.5 / 393 / 1342 | 479 | 233.9 | 365.5 (349\~391) | 17 (17\~17) |
| Part B T7 en (choice 10) | 20 | 220.5 / 175 / 253 | 451 / 403 / 523 | 452.5 | 227.7 | 536.5 (510\~566) | 150.5 (136\~172) |
| Part C T7 de (choice 10) | 20 | 230.5 / 195 / 310 | 460 / 411 / 613 | 461.5 | 227.7 | 536.5 (517\~569) | 150.5 (136\~172) |
| S4 overall | 80 | 227 / 172 / 348 | 461.5 / 393 / 1342 | | 230.1 | | |

- Token totals are input 36,289 and output 6,798 (A 14,636 / 680, B 10,796 / 3,058, C 10,857 / 3,060).
- Score output was constant at 17 tokens (Boolean 20, S3). T7 output tokens correlate with the row's option-string length at r = 0.55\~0.56. This is consistent with S3's inference that the output lists per-option probabilities (to be verified).
- The browser POST of one T6 run took 1,342 ms (the maximum). The same run's `latencyMs` was within the displayed-latency range, so the difference is on the network side. It is not an error.
- The displayed latency is at the same level as S1 T2 234 ms and S3 T4 227.5 ms. The Laya local references (P2 laya-serve round trip 20.1 ms, D1 english CPU 1 question 86.6 ms) use different hardware and paths, so they are not a model-speed comparison.

## 5. Observations and limitations

**3 key observations**
1. **On SST-5 the difference lies more in the use of the scale than in hitting the exact level.** The argmax accuracy difference (0.650 vs 0.425) is borderline at n=40 (p=0.078). But the difference is clear in MAE (0.432 vs 0.888, difference CI excludes 0), within ±1 (0.875 vs 0.650) and signed error (−0.014 vs −0.687). Laya english has 0 argmax-correct answers on the 16 rows with gold 3·4 and never chose level 4. multilingual is at level 0·1 on all 40 rows. Jev uses all 5 levels, and its E[level] tracks the gold.
2. **On Score, the display rule (rounded E) and argmax are nearly the same, so the choice of comparison rule does not change the conclusions.** The two rules diverged on 2/40 rows for Jev, 6/40 for english and 0/40 for multilingual, changing the number correct by ±1. McNemar p does move, however, 0.078 ↔ 0.019 depending on the rule. We therefore follow the prior rule that fixes argmax as the primary metric (docs/09 §2) and report rounded E only as secondary.
3. **Jev made the same decisions in en and de, while Laya collapsed when the language changed.** With the same ids and the same English options, Jev's label is the same in en and de for 19/20 ids, and its accuracy is the same 0.900. Laya is indistinguishable from Jev in en (b/c 4/0, 3/2) but drops in de to english 0.35, multilingual 0.40, Router 0.35 (b/c 11/0, 11/1, 12/1). The multilingual checkpoint also drops in de about as much as english, and the result of the Router sending 15 de rows to multilingual (0.35) equals english. With 20 rows per language, the magnitudes should be read only as directional signals.

**Limitations**
- Via the playground, not the API. The model version is not shown and the prompt wrapping is unknown. For T6, n=40 gives a 95% CI width of about ±0.15, and T7 has n=20 per language.
- Jev's probabilities and score are rounded to 2 decimals. The rounding error of the T6 E[level] is at most 0.005, and the difference between Σ k·p_k (rounded probabilities) and `score` is at most 0.020.
- The pooled en+de McNemar counts pairs of the same id as independent (§3.3).
- The meaning ("very negative") and the position (first level) of T6 level 0 coincide, so the position effect of #131 cannot be isolated. A variant with reversed level order is out of scope here.
- The interpretations of the 2 ids of Jev's T7 errors and of the 1 T6 row off by 2 levels (label boundary, mixed sentiment) are judgments made from reading the sentences.

## 6. Operations log and anomalies

- Site status: page load 14:15:58; at instrumentation install, the body check for limit messages found none. The UI was the same as in S3 (Single question by default, Decision type group, and with Score selected "ORDERED SCALE", "Rubric / Lowest → highest", Rubric level 0\~4 textboxes). Because of the budget, the default example was not run.
- Network list: POST 80 (all `/api/evaluate`, 200), GET 77 (document 1, static 40, Next.js RSC prefetch 36, all 200). Console: 198 warnings (CSS preload), 0 errors.
- Host wall clock: the wall − mono offset grew gradually from 0 ms to +14 ms, with one −52 ms step (+14 → −38 ms) between runs 77 and 78. The gap guard and dump matching both use the monotonic axis, so there is no effect (the same kind as the +1.98 s step at S2 runs 60/61, but smaller).
- Clicks without a request: there were only 80 Run clicks. The 3 no-click dry runs and the 6 View details expansions (for screenshots, not the Run button) made no request (80 `/api/evaluate` resource-timing entries = 80 clicks).

## 7. Files

| File | Contents |
|---|---|
| `results/F/jev_cmp/sessions/S4_20261007/S4_requests.jsonl` (not included in the public repository) | 80 lines (run = item, no retries). T6 decisions have `score` (E[level]), `probs` (per level), `pred` (argmax), `top_p`, `expected_level`, `shown` (displayed level text), `shown_score` ("x.xx / 4") |
| `results/F/jev_cmp/jev_runs_all.jsonl` (not included in the public repository) | master, 311 lines (S1 41 + S1b 30 + S2 80 + S3 80 + S4 80). The first 231 lines are byte-identical to the pre-S4 copy, the last 80 identical to `S4_requests.jsonl` |
| `raw/rNN_<T6|T7en|T7de>_rowRR.json` (not included in the public repository) | 80 per-request dumps |
| `raw/run_plan.json`, `raw/js/` (not included in the public repository) | item plan 80, instrumentation `instrument.js` (same as S3, only the version tag set to S4), per-item input scripts `i01~i80`, no-click dry runs `dry_i01_T6_row00.js`, `dry_i41_T7en_row00.js`, `dry_i61_T7de_row00.js` |
| `raw/evaluate_timing_all.json`, `raw/network_requests.txt`, `raw/network_requests_all.txt`, `raw/console.log`, `raw/mcp/` (none of the five items is included in the public repository) | 80 `/api/evaluate` resource timings and click times (monotonic and wall), network list, console, MCP snapshots (page load, dry-run form) and the MCP console log |
| `shots/` (not included in the public repository) | `S4_A_item01_run01_T6_row00.png`, `S4_A_item40_run40_T6_row39.png`, `S4_B_item41_run41_T7en_row00.png`, `S4_B_item60_run60_T7en_row19.png`, `S4_C_item61_run61_T7de_row00.png`, `S4_C_item80_run80_T7de_row19.png` (View details open, full page) |
| `s4_prep.py`, `s4_record.py` | generates the plan and input scripts (asserts the match with Laya `render_options` and identical en·de ids and options); recording wrapper (same stop-condition classification and stale-dump rejection as S3) |
| `results/F/jev_cmp/jev_cmp.py` | `parse_single_display` SCORE heading, score branch of `analyze` (`score_lines`), pooling of comma-joined sets and cross-language consistency (`crosslang_lines`), Router answered-by. Details in the run card |
| Reproduction | `.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S4 T6_sst5_40`, `… analyze S4 T7_massive_intent_10opt_en_20`, `… analyze S4 T7_massive_intent_10opt_de_20`, `… analyze S4 T7_massive_intent_10opt_en_20,T7_massive_intent_10opt_de_20` |

**English** | [한국어](S4_summary.ko.md)
