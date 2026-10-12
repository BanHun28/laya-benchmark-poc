# S5 summary: T7 MASSIVE intent-10 ja · zh-CN · ko, 20 each (+ 5-language synthesis including en · de) + T8 prompt-injections 40 (2026-10-07)

**Verdict.**
1. **On T7 ja · zh-CN · ko, Jev stayed at the same level as in en · de, while Laya swung widely from language to language.** Jev: ja 19/20 (0.950), zh-CN 18/20 (0.900), ko 18/20 (0.900). Laya english 0.450 / 0.450 / 0.100, multilingual 0.800 / 0.600 / 0.450. The Router sent all 60 rows of the three languages to multilingual, so it equals multilingual. exact McNemar (b/c) for Jev vs english is 10/0 p=0.002, 9/0 p=0.004, 17/1 p=0.0001. Jev vs multilingual is 3/0 p=0.25, 8/2 p=0.11, 11/2 p=0.023, below 0.05 only in ko.
2. **5-language synthesis (the same 20 ids × en · de · ja · zh-CN · ko).** Jev's accuracy is 0.900 / 0.900 / 0.950 / 0.900 / 0.900 (pooled 91/100), and its language penalty vs en is 0 / +0.05 / 0 / 0 (mean +0.012). Laya's mean penalty is english −0.362 (ko −0.600), multilingual −0.287 (de −0.450, ko −0.400, ja −0.050), Router −0.150. The share of ids with the same label in all five languages is Jev 18/20 (mean pairwise language agreement 0.935), multilingual 5/20 (0.545), english 0/20 (0.325). Jev's 9 wrong answers are one id × 5 languages (all the same wrong answer), one id × 3 (en · de · ko) and one id × 1 (zh-CN) (Jev's per-item outputs are omitted in the public repository). With n=20 per language and the same ids repeated, the per-language magnitudes are directional signals and the pooled p-values are optimistic.
3. **On T8 prompt-injections, accuracy at the 0.5 cut is the same for Jev and Laya english (0.775, b/c 5/5 p=1.0), while Jev's ranking quality is higher.** The AUROC of Jev's p(true) is 1.000 (perfect separation on these 40 rows: all 20 benign rows at 0.01\~0.04, all 20 injection rows at 0.08 or above). Because the separation is perfect, the percentile bootstrap CI degenerates to [1.000, 1.000] and cannot express uncertainty. english 0.929 [0.840, 0.997], multilingual 0.781, Router 0.868; the CIs of the AUROC differences exclude 0 for all three pairs (+0.071 [+0.003, +0.160], +0.219, +0.132). Jev and english both predict 11/40 positive (gold 20/40), and all 9 of their wrong answers are misses (FN). With a threshold of 0.05\~0.08 chosen on the same 40 rows, Jev would get 40/40, but this is only a descriptive statistic. The CI of Laya english 0.775 [0.625, 0.877] contains upstream 0.698 (held out, n=116).
4. **Operations:** all 100 requests (A 20 + B 20 + C 20 + D 40) returned HTTP 200. 5xx · 4xx (including 429) · limit messages · captcha · error screens: 0, and no retries. Gaps on the monotonic clock: min 15.016 s, median 15.114 s. Today's cumulative total is S2\~S4 240 + S5 100 = 340, with no limit signal through the 340th request (15:18:41).

Via the playground, not the API. The model version is not shown (`typesafe-ai/jev` 100/100). T7 has n=20 per language, T8 n=40. Jev probabilities are rounded to two decimal places. T7's training-mix status is unknown, T8 is held out for Laya, and Jev's training data is unknown.

## 1. Execution overview

| Item | Value |
|---|---|
| Requests | `POST /api/evaluate` 100 = Part A (T7 ja) 20 + Part B (T7 zh-CN) 20 + Part C (T7 ko) 20 + Part D (T8) 40, all HTTP 200. Planned 100, session cap 110 (room for retries). The instrumentation's `ready()` blocked clicking once there had been 110 or more Run clicks (`raw/js/instrument.js`, not included in the public repository) |
| Stop conditions | 5xx 0, 4xx 0 (429 0), limit messages 0, captcha 0, error screens 0. After every run, the result panel · status · title · `[role=alert]` · body text were checked with a limit-message regex, and captcha iframes were checked too (`s5_record.py`, dump `page`). All 100: `body_stop_match` null, alerts [], captcha_frames []. Before the run we confirmed that 0 of the input strings (including the T8 injection sentences) match this regex |
| Gaps (between Run clicks) | Guard 15 s (rule ≥ 10 s, same as S3 · S4), monotonic from the start. 99 gaps: min 15.016 s, median 15.114 s, max 27.234 s (run 61: after the Part D no-click dry run · form snapshot · run 60 screenshot). Resource-timing start gaps also 15.017 / 15.115 / 27.234 s |
| Input identity | Before the request: the payload sha12 built from the form values matched the form file's expected value 100/100 (`window.__jev.ready`). After the request: the captured request body equals the `jev_cmp.py` payload byte for byte 100/100 (`payload_exact`). 4 no-click dry runs (items 1, 21, 41, 61) |
| Input content | T7: Single / Choice, 10 options `key: key spaced` (up to 50 characters) in form order. In each ja · zh-CN · ko row, the MASSIVE id · gold · option list · question equal those of the en row sent in S4 (`s5_prep.py` assert). T8: Single / Boolean, the question sentence only (Laya noul has no criteria either; the Boolean form has no label · description fields: `raw/mcp/snapshot_dry_i061_T8_row00_form.yml`, not included in the public repository). State is always the string Laya reads, `json.dumps(state, ensure_ascii=False)` (`laya/common.py` `serialize_state`); before the run we confirmed for all 100 rows that it equals `state_text` and has no `\u` escapes. States containing non-ASCII characters: T7 60/60, T8 13/40 (German etc.) |
| Screen = response | 100/100 (DECISION, bar %). Displayed latency = `latencyMs` half-up 100/100 |
| Model ID / response metadata | `model` and View details both `typesafe-ai/jev` 100/100. `rounding` {2, 2}, `warnings` [] 100/100. provider `confidence.decision` is present on T7 60/60 and absent on the 40 T8 Booleans (as in S3 T5) |

## 2. T7 ja · zh-CN · ko (20 rows per language, same id · gold · options)

### 2.1 Accuracy · calibration

| lang | system | correct / n | accuracy [Wilson 95%] | Brier | ECE | mean top p |
|---|---|---|---|---|---|---|
| ja | Jev | 19/20 | **0.950** [0.764, 0.991] | 0.063 | 0.052 | 0.976 |
| ja | Laya english | 9/20 | 0.450 [0.258, 0.658] | 0.681 | 0.351 | 0.678 |
| ja | Laya multilingual (= Router, all 20 to multilingual) | 16/20 | 0.800 [0.584, 0.919] | 0.289 | 0.199 | 0.870 |
| zh-CN | Jev | 18/20 | **0.900** [0.699, 0.972] | 0.194 | 0.133 | 0.950 |
| zh-CN | Laya english | 9/20 | 0.450 [0.258, 0.658] | 0.886 | 0.414 | 0.864 |
| zh-CN | Laya multilingual (= Router, all 20 to multilingual) | 12/20 | 0.600 [0.387, 0.781] | 0.642 | 0.319 | 0.781 |
| ko | Jev | 18/20 | **0.900** [0.699, 0.972] | 0.151 | 0.086 | 0.936 |
| ko | Laya english | 2/20 | 0.100 [0.028, 0.301] | 1.164 | 0.435 | 0.535 |
| ko | Laya multilingual (= Router, all 20 to multilingual) | 9/20 | 0.450 [0.258, 0.658] | 0.808 | 0.365 | 0.815 |

Brier is Σ(p − onehot)², computed for each row over that row's 10 options. ECE uses 15 bins, based on top p. The Laya values equal `laya_summary.md` §1 · §4 (ja .45 / .80, zh-CN .45 / .60, ko .10 / .45).

### 2.2 Agreement and exact McNemar (b = only Jev right, c = only Laya right)

| lang | pair | same label | b | c | p |
|---|---|---|---|---|---|
| ja | Jev vs Laya english | 9 | 10 | 0 | **0.0020** |
| ja | Jev vs Laya multilingual (= Router) | 16 | 3 | 0 | 0.2500 |
| zh-CN | Jev vs Laya english | 10 | 9 | 0 | **0.0039** |
| zh-CN | Jev vs Laya multilingual (= Router) | 10 | 8 | 2 | 0.1094 |
| ko | Jev vs Laya english | 2 | 17 | 1 | **0.0001** |
| ko | Jev vs Laya multilingual (= Router) | 7 | 11 | 2 | **0.0225** |

### 2.3 Confidence

| lang | system | 100% displayed | mean top (correct / wrong) | wrong with top ≥ 0.90 | gold option shown at 0% | provider confidence (correct / wrong) |
|---|---|---|---|---|---|---|
| ja | Jev | 14/20 | 0.986 / 0.780 | 0/1 | 0 | 0.984 / 0.750 |
| zh-CN | Jev | 14/20 | 0.953 / 0.915 | 2/2 | 0 | 0.948 / 0.900 |
| ko | Jev | 14/20 | 0.968 / 0.650 | 1/2 | 0 | 0.964 / 0.610 |
| ja | Laya english / multilingual | - | 0.851 / 0.537, 0.917 / 0.680 | 1/11, 1/4 | - | - |
| zh-CN | Laya english / multilingual | - | 0.977 / 0.772, 0.857 / 0.669 | 5/11, 3/8 | - | - |
| ko | Laya english / multilingual | - | 0.672 / 0.519, 0.940 / 0.713 | 1/18, 3/11 | - | - |

Jev has many 0% cells in all three languages (163\~167/200), but no row shows the gold option at 0%. The 2 zh-CN wrong answers are both at 0.90 or above. Laya english gave 5 of its 11 zh-CN wrong answers at 0.90 or above.

### 2.4 Jev errors (5 = ja 1 + zh-CN 2 + ko 2)

| lang | row (id) | utterance | gold | Jev (top) | Laya english / multilingual |
|---|---|---|---|---|---|
| — | — | — | — | — | — |
| — | — | — | — | — | — |
| — | — | — | — | — | — |
| — | — | — | — | — | — |
| — | — | — | — | — | — |

- 1 id was wrong in all five languages (the same wrong answer as in S4 en · de). Another id was wrong in S4 en · de and in ko, but right in ja · zh-CN, whose translations differ in content.
- For the id wrong only in zh-CN, unlike in the other languages, the action verb was lost in translation. This interpretation (translation difference, label boundary) is a judgment made from reading the utterances; scoring used the dataset labels as they are.

## 3. T7 5-language synthesis (S4 en · de + S5 ja · zh-CN · ko, same 20 ids)

`.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S4,S5 T7_..._en_20,T7_..._de_20,T7_..._ja_20,T7_..._zh-CN_20,T7_..._ko_20` (output `raw/analyze/T7_all5_S4S5.md`, not included in the public repository). The same 20 ids appear five times, so the pooled tests are not on an independent sample.

### 3.1 Accuracy by language

| system | en | de | ja | zh-CN | ko | pooled (100) |
|---|---|---|---|---|---|---|
| Jev | 18/20 = 0.900 | 18/20 = 0.900 | 19/20 = 0.950 | 18/20 = 0.900 | 18/20 = 0.900 | **91/100 = 0.910** [0.838, 0.952] |
| Laya english | 14/20 = 0.700 | 7/20 = 0.350 | 9/20 = 0.450 | 9/20 = 0.450 | 2/20 = 0.100 | 41/100 = 0.410 [0.319, 0.508] |
| Laya multilingual | 17/20 = 0.850 | 8/20 = 0.400 | 16/20 = 0.800 | 12/20 = 0.600 | 9/20 = 0.450 | 62/100 = 0.620 [0.522, 0.709] |
| Laya Router | 14/20 = 0.700 (english 20) | 7/20 = 0.350 (multilingual 15 / english 5) | 16/20 = 0.800 (multilingual) | 12/20 = 0.600 (multilingual) | 9/20 = 0.450 (multilingual) | 58/100 = 0.580 [0.482, 0.672] |

### 3.2 Language penalty = accuracy(lang) − accuracy(en)

| system | de | ja | zh-CN | ko | mean |
|---|---|---|---|---|---|
| Jev | +0.000 | +0.050 | +0.000 | +0.000 | **+0.012** |
| Laya english | −0.350 | −0.250 | −0.250 | −0.600 | −0.362 |
| Laya multilingual | −0.450 | −0.050 | −0.250 | −0.400 | −0.287 |
| Laya Router | −0.350 | +0.100 | −0.100 | −0.250 | −0.150 |

The Router's ja +0.100 results from sending en to english and ja to multilingual (relative to multilingual en 0.850 it is −0.050). With n=20 per language, ±0.05 is one row.

### 3.3 Exact McNemar by language (b / c, p)

| pair | en | de | ja | zh-CN | ko | pooled 100 (not independent) |
|---|---|---|---|---|---|---|
| Jev vs Laya english | 4 / 0, 0.125 | 11 / 0, 0.001 | 10 / 0, 0.002 | 9 / 0, 0.004 | 17 / 1, 0.0001 | 51 / 1, 2.4e-14 |
| Jev vs Laya multilingual | 3 / 2, 1.000 | 11 / 1, 0.006 | 3 / 0, 0.250 | 8 / 2, 0.109 | 11 / 2, 0.023 | 36 / 7, 9.0e-6 |
| Jev vs Laya Router | 4 / 0, 0.125 | 12 / 1, 0.003 | 3 / 0, 0.250 | 8 / 2, 0.109 | 11 / 2, 0.023 | 38 / 5, 2.5e-7 |

Jev vs multilingual cannot be told apart in en · ja · zh-CN and has p < 0.05 in de · ko. Against english, p < 0.01 in all four languages other than en.

### 3.4 Cross-language consistency (same label for the same id)

| system | same as en: de | ja | zh-CN | ko | same label in all 5 languages | mean pairwise agreement (10 pairs) | correct in all 5 languages | wrong in all 5 languages |
|---|---|---|---|---|---|---|---|---|
| Jev | 19/20 | 19/20 | 18/20 | 19/20 | **18/20** | **0.935** | 17 | 1 |
| Laya english | 10/20 | 11/20 | 12/20 | 1/20 | 0/20 | 0.325 | 0 | 5 |
| Laya multilingual | 7/20 | 17/20 | 12/20 | 11/20 | 5/20 | 0.545 | 5 | 1 |
| Laya Router | 6/20 | 14/20 | 9/20 | 8/20 | 4/20 | 0.485 | 4 | 0 |

- Jev changed its label across languages for two ids. For both ids, the content of the translated sentence differs between languages (§2.4).
- Jev's T7 output token counts are the same across the five languages for 18/20 ids, and the two differing ids are exactly the two ids whose label changed. This is consistent with the S3 · S4 inference that the output is determined by the options and the chosen label rather than by the utterance (inferred, to be verified).
- Of the 17 ids Laya multilingual got right in en, it got 10 wrong in de and 8 wrong in ko. Its most frequent wrong label is iot_hue_lightdim (10 of 38; lightoff → lightdim 4, lightup → lightdim 4). english's most frequent wrong label is general_joke (9 of 59).

### 3.5 Calibration and confidence (by language)

| system | Brier en / de / ja / zh-CN / ko (pooled) | ECE en / de / ja / zh-CN / ko (pooled) |
|---|---|---|
| Jev | 0.143 / 0.150 / 0.063 / 0.194 / 0.151 (0.140) | 0.092 / 0.086 / 0.052 / 0.133 / 0.086 (0.068) |
| Laya english | 0.394 / 1.046 / 0.681 / 0.886 / 1.164 (0.834) | 0.214 / 0.513 / 0.351 / 0.414 / 0.435 (0.355) |
| Laya multilingual | 0.293 / 0.890 / 0.289 / 0.642 / 0.808 (0.584) | 0.184 / 0.453 / 0.199 / 0.319 / 0.365 (0.216) |
| Laya Router | 0.394 / 1.009 / 0.289 / 0.642 / 0.808 (0.628) | 0.214 / 0.485 / 0.199 / 0.319 / 0.365 (0.260) |

| Jev (by language) | en | de | ja | zh-CN | ko |
|---|---|---|---|---|---|
| 100% displayed | 15/20 | 12/20 | 14/20 | 14/20 | 14/20 |
| mean top (correct) | 0.968 | 0.971 | 0.986 | 0.953 | 0.968 |
| top of wrong answers | — | — | — | — | — |
| gold option shown at 0% | 0 | 0 | 0 | 0 | 0 |

The en · de values come from the same records as S4 (`S4_summary.md` §3.1 · §3.5). Of the 100, Jev shows the gold option at 0% on no row, and 5 of its 9 wrong answers have top ≥ 0.90.

### 3.6 Context (non-comparable figures)

| Figure | Value | Notes |
|---|---|---|
| Laya MASSIVE upstream (20 options) | ja english 0.530 / multilingual 0.640, zh-CN 0.620 / 0.650, ko 0.110 / 0.470 (CPU sweep, `laya_summary.md` §4). BENCHMARKS.md ko multilingual 0.470, en 0.710 / english 0.820 | Different number of options (10 vs 20), so only the direction is considered. The direction, with english collapsing in ko and multilingual around 0.45, is the same as upstream |
| Jev MASSIVE published | none | |
| Training mix | unknown (04 §1 rule) | |

## 4. T8 prompt-injections (40 rows, gold true 20 / false 20)

### 4.1 Accuracy · positive rate · ranking quality

| system | correct / n | accuracy [Wilson 95%] | predicted true (gold 20) | Brier | ECE | mean top p | AUROC p(true) [bootstrap 95%] | accuracy at the optimal threshold on the same 40 rows (descriptive) |
|---|---|---|---|---|---|---|---|---|
| Jev (playground, displayed p, 2 decimals) | 31/40 | **0.775** [0.625, 0.877] | 11 | 0.307 | 0.194 | 0.921 | **1.000** [1.000, 1.000]* | 40/40 = 1.000 (t ∈ (0.04, 0.08]) |
| Laya english | 31/40 | 0.775 [0.625, 0.877] | 11 | 0.401 | 0.223 | 0.962 | 0.929 [0.840, 0.997] | 35/40 = 0.875 |
| Laya multilingual | 23/40 | 0.575 [0.422, 0.715] | 9 | 0.692 | 0.380 | 0.940 | 0.781 [0.615, 0.919] | 31/40 = 0.775 |
| Laya Router (english 26 / multilingual 14) | 29/40 | 0.725 [0.572, 0.839] | 11 | 0.510 | 0.261 | 0.979 | 0.868 [0.738, 0.969] | 33/40 = 0.825 |

- The decision rule is p(true) ≥ 0.5 (the laya-evals rule). No row got exactly 0.5 from Jev.
- As in S3, Brier is Σ(p − onehot)² over the two cells {false, true} (= 2(p − y)²); on a single-cell basis it is halved. The Laya values equal `laya_summary.md` §1 (0.401 / 0.692 / 0.510, ECE 0.223 / 0.380 / 0.261).
- *Jev separates these 40 rows perfectly (gold false: p(true) 0.01\~0.04; gold true: 0.08\~0.99). Every bootstrap resample therefore has AUROC 1, and the percentile CI degenerates to width 0. This does not mean the population AUROC is 1: at n=40, perfect separation can also arise from a population whose AUROC is below 1. The CIs of the Jev − Laya AUROC differences are also optimistic, because the variance on the Jev side is 0.
- Jev's p(true) has only 19 distinct values (rounded to 2 decimals). The optimal-threshold column is chosen on the same 40 rows and is not used for conclusions.

### 4.2 Agreement, exact McNemar, AUROC difference

| pair | n | same prediction | b | c | McNemar p | AUROC Jev − Laya [paired bootstrap 95%] |
|---|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 30 | 5 | 5 | 1.0000 | +0.071 [+0.003, +0.160] |
| Jev vs Laya multilingual | 40 | 26 | 11 | 3 | 0.0574 | +0.219 [+0.081, +0.385] |
| Jev vs Laya Router | 40 | 28 | 7 | 5 | 0.7744 | +0.132 [+0.031, +0.262] |

### 4.3 Error structure: misses (FN) and false alarms (FP)

| system | FP (gold false → true) | FN (gold true → false) | wrong with top ≥ 0.90 | p(true) ∈ {0, 1} (100% displayed) |
|---|---|---|---|---|
| Jev | **0** | 9 | 2/9 | 0/40 |
| Laya english | 0 | 9 | 6/9 | 27/40 |
| Laya multilingual | 3 (rows 3, 17, 23) | 14 | 12/17 | 4/40 |
| Laya Router | 1 (row 17) | 10 | 10/11 | 20/40 |

Jev and english both have FP 0 · FN 9 and the same accuracy, but they miss different injections.

| Group | rows | Content (summary) |
|---|---|---|
| Wrong for Jev only (english right) | — | Role · task instruction type (5). Jev p(true) 0.17\~0.40 |
| Wrong for english only (Jev right) | — | Explicit ignore · override (5). In 4 of the 5 the override sentence is in German. Jev p(true) 0.76\~0.98 |
| Wrong for all three systems | — | Role-play type (2), ignore-instruction type (1) |

This classification (role · task instruction type vs explicit override) is an interpretation made from reading the sentences. Scoring used the deepset labels as they are. The question wording ("inject or override instructions") is the same for both systems.

### 4.4 Abstention threshold (Jev top p, same 40 rows, descriptive)

| Keep criterion | rows kept | wrong among kept rows |
|---|---|---|
| top ≥ 0.80 | 37/40 | 7 |
| top ≥ 0.90 | 29/40 | 2 |
| top ≥ 0.95 | 27/40 | 0 |

On T5 (BoolQ), abstaining at top ≥ 0.80 filtered out all 3 wrong answers. On T8, 7 of the 9 misses have top 0.80 or above (p(true) 0.08\~0.19), so the same policy does not work. T8's problem is not the ranking but the position of the 0.5 threshold.

### 4.5 By Router language assignment (descriptive, small n)

| Router assignment | n (gold true) | Jev | Laya english | Laya multilingual | Laya Router |
|---|---|---|---|---|---|
| english | 26 (11) | 20 | 21 | 15 | 21 |
| multilingual | 14 (9) | 11 | 10 | 8 | 8 |

### 4.6 Context

| Figure | Value | Notes |
|---|---|---|
| Laya prompt-injections upstream | english 0.698 / multilingual 0.578 (README.md:1355, held out, n=116) | Both this english 0.775 [0.625, 0.877] and multilingual 0.575 [0.422, 0.715] contain the upstream values within their CIs |
| Jev prompt-injections published | none | |
| Training mix | Laya: held out. Jev: unknown | deepset/prompt-injections is a public dataset |

## 5. Latency · tokens

| Group | runs | displayed "server + network" ms median / min / max | browser POST ms median / min / max | click → complete ms median | POST − latencyMs median | input tokens median (min\~max), total | output tokens median (min\~max), total |
|---|---|---|---|---|---|---|---|
| Part A T7 ja | 20 | 224 / 191 / 438 | 455 / 414 / 667 | 456.5 | 229.4 | 540.5 (516\~574), 10,913 | 150.5 (136\~172), 3,066 |
| Part B T7 zh-CN | 20 | 227 / 190 / 368 | 465 / 417 / 1,239 | 466 | 227.6 | 538 (512\~568), 10,844 | 149.5 (136\~172), 3,063 |
| Part C T7 ko | 20 | 233.5 / 199 / 301 | 473 / 428 / 563 | 474 | 232.6 | 538 (509\~567), 10,859 | 150.5 (136\~172), 3,059 |
| Part D T8 (Boolean) | 40 | 226 / 163 / 458 | 475.5 / 408 / 688 | 477 | 230.0 | 305 (291\~419), 12,821 | 20 (20\~20), 800 |
| S5 overall | 100 | 227 / 163 / 458 | 466.5 / 408 / 1,239 | 467.5 | 229.7 | 45,437 | 9,988 |

- The T7 input-token medians are en 536.5 / de 536.5 / ja 540.5 / zh-CN 538 / ko 538, a small difference across languages, because most of the input is the question · 10 options.
- T8 input tokens correlate with the state length at r = 0.989. Boolean output is constant at 20 tokens, as in T5. T7 output tokens correlate with the summed option-key length at r = 0.566 (the same level as S4's 0.55\~0.56).
- The browser POST of one zh-CN run took 1,239 ms (the maximum). The same run's `latencyMs` was within the displayed-latency range, so the difference is on the network side (the same kind as the S4 case). It is not an error.
- The displayed latency is at the same level as the per-part medians of S3 · S4 (200.5\~236 ms), within or slightly below the Jev 3rd-party p50 of 236\~276 ms (09 §1). The Laya local latencies (P2 laya-serve round trip 20.1 ms, etc.) use different hardware and paths and are not compared.

## 6. Observations and limitations

**3 key observations**
1. **Jev's multilingual intent classification was nearly language-independent, while Laya's language penalty was large, depending on checkpoint and language.** On the same 20 ids, Jev scores 0.90\~0.95 in all five languages and gives the same label in all five for 18/20 ids. Laya english drops to 0.10 in ko (penalty −0.60), and multilingual is also at de −0.45, ko −0.40; ja hurt multilingual the least (−0.05). The two ids where Jev changed its label coincide with content differences in the translated sentences. The 1 id wrong in every language is a label-boundary case (interpretation, §2.4).
2. **On T8, under the same accuracy (0.775), the two systems' error structures differ.** Jev's ranking is perfect (AUROC 1.000 on this sample) with 0 false alarms, but at the 0.5 threshold it misses role · task instruction-type injections by scoring them low, 0.08\~0.40. Laya english catches the role-instruction type but misses 4 explicit overrides written in German. For Jev, lowering the threshold (0.05\~0.08 on the same 40 rows) separates the classes, so this is a threshold-calibration problem; it becomes usable only once the threshold is fixed on a held-out sample.
3. **Where Jev's Boolean probabilities sit differs by task.** On T5 BoolQ, with 21/40 predicted positive (gold 20), the 0.5 cut fit, and all wrong answers had top < 0.80. On T8, 11/40 are predicted positive and 7 of the 9 misses have top ≥ 0.80. A fixed threshold · abstention policy must not be applied to Boolean across the board; per-task calibration is needed. On Choice (T7), 5 of the 9 wrong answers have top ≥ 0.90, so the S1 · S2 · S4 pattern of remaining high-confidence errors holds.

**Limitations**
- Via the playground, not the API. The model version is not shown and the prompt wrapping is unknown.
- T7 has n=20 per language (95% CI width about ±0.2). The magnitude of the language penalty is a directional signal. The 5-language pool repeats the same 20 ids, so the pooled McNemar p is optimistic.
- The bootstrap CI of the T8 Jev AUROC degenerated because of perfect separation (§4.1). The CIs of the AUROC differences are also optimistic. The optimal threshold · abstention tables are descriptive statistics computed on the same 40 rows.
- Jev probabilities are rounded to 2 decimals (T8 p(true): 19 distinct values).
- The T8 gold follows deepset's labeling policy (role instructions are also labeled as injections). Under a different labeling policy, the ranking of the two systems could change.
- MASSIVE translation quality (e.g., the zh-CN translation dropout in §2.4) is mixed into the per-language results.

## 7. Operations log and anomalies

- Site status: 14:52:50 page loaded normally; at instrumentation install, no limit message in the body. UI · DOM ids are the same as in S3 · S4 (Single question by default, Decision type group, with Boolean selected "YES / NO — Jev returns P(true). The probability of "No" is its complement."). Because of the budget, the default example was not run.
- Network list: POST 100 (all `/api/evaluate`, 200), GET 27 (document 1, static 14, Next.js RSC prefetch 12, all 200). 100 `/api/evaluate` resource-timing entries = 100 Run clicks; click → fetch start 0\~5 ms.
- Console: 206 warnings (MCP log, all CSS preload), 0 errors. The `browser_console_messages` dump (`raw/console.log`) has 186 entries (warnings only), as of the MCP buffer.
- Host wall clock: the wall − mono offset was within −3 \~ +20 ms, with small steps at runs 75 → 76 (+5 ms) and 76 → 77 (+10 ms). The gap guard and dump matching use the monotonic axis, so there is no effect.
- Clicks without a request: there were only 100 Run clicks. The 4 no-click dry runs only filled the form and compared hashes. For screenshots, View details was opened without a click via `details.open = true` in the DOM (S4 used clicks).
- The maximum gap of 27.2 s (run 61) is the Part D preparation time (dry run, form snapshot, run 60 screenshot); at the part boundaries, runs 21 · 41 had 19.6 s · 18.6 s, and run 2 had 20.9 s (run 1 screenshot).

## 8. Files

| File | Contents |
|---|---|
| `results/F/jev_cmp/sessions/S5_20261007/S5_requests.jsonl` (not included in the public repository) | 100 lines (run = item, no retries). Choice has `pred` · `probs` · `top_p` · `shown_pct`, Boolean `p_true` · `pred`; per run `latency_ms_response` · `displayed_ms` · `fetch_dur_ms` · `click_to_complete_ms` · `usage` · `confidence` · `model_id_details`. `click_epoch_ms` is on the monotonic axis |
| `results/F/jev_cmp/jev_runs_all.jsonl` (not included in the public repository) | master, 411 lines. The first 311 lines are byte-identical to the pre-S5 copy, the last 100 identical to `S5_requests.jsonl` |
| `raw/rNNN_<T7ja|T7zh|T7ko|T8>_rowRR.json` (not included in the public repository) | 100 per-request dumps |
| `raw/run_plan.json`, `raw/js/` (not included in the public repository) | item plan 100, instrumentation `instrument.js` (S4 recipe + version tag S5 + session-cap check at 110), per-item input scripts `i001~i100`, no-click dry runs `dry_i001_T7ja_row00.js` · `dry_i021_T7zh_row00.js` · `dry_i041_T7ko_row00.js` · `dry_i061_T8_row00.js` |
| `raw/evaluate_timing_all.json`, `raw/network_requests.txt`, `raw/network_requests_all.txt`, `raw/console.log`, `raw/mcp/` (none of the five items is included in the public repository) | 100 resource timings and click times (monotonic · wall), network list, console, MCP snapshots (page load, 2 dry-run forms) and the MCP console log |
| `raw/analyze/` (not included in the public repository) | `T7_ja.md`, `T7_zh-CN.md`, `T7_ko.md`, `T8.md` (`analyze S5 <SET>` output), `T7_all5_S4S5.md` (`analyze S4,S5` 5-language output) |
| `shots/` (not included in the public repository) | 8 images, the first · last run of each part (View details open, full page): `S5_A_item001_run001_T7ja_row00.png`, `S5_A_item020_run020_T7ja_row19.png`, `S5_B_item021_run021_T7zh_row00.png`, `S5_B_item040_run040_T7zh_row19.png`, `S5_C_item041_run041_T7ko_row00.png`, `S5_C_item060_run060_T7ko_row19.png`, `S5_D_item061_run061_T8_row00.png`, `S5_D_item100_run100_T8_row39.png` |
| `s5_prep.py`, `s5_record.py` | generates the plan · input scripts (asserts the match with Laya `serialize_state` · `render_options`, identical id · gold · options with the en rows, and no T8 noul criteria); recording wrapper (same stop-condition classification as S4, stale-dump rejection, 3-digit run numbers) |
| `results/F/jev_cmp/jev_cmp.py` | `analyze` reads comma-joined sessions together and, with three or more sets, outputs `crosslang_multi` (per-language accuracy, penalty vs en, per-language McNemar, cross-language consistency, per-id patterns). Details in the run card |
| Reproduction | `.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S5 T7_massive_intent_10opt_ja_20` (likewise zh-CN, ko), `… analyze S5 T8_prompt_injections_40`, `… analyze S4,S5 T7_massive_intent_10opt_en_20,T7_massive_intent_10opt_de_20,T7_massive_intent_10opt_ja_20,T7_massive_intent_10opt_zh-CN_20,T7_massive_intent_10opt_ko_20` |

**English** | [한국어](S5_summary.ko.md)
