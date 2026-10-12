# S0 Laya summary — jev_cmp sets (2026-10-06)

`.venv/bin/python results/F/jev_cmp/laya_summary.py`. CPU fp32, intra-op 10 / inter-op 1, `--batch-size 8`. accuracy = argmax (noul: p(true) >= 0.5) with Wilson 95% CI; macro-F1 over gold ∪ pred; Brier = Σ(p − onehot)²; ECE 15 bins on max p (= answer_confidence); majority = gold majority rate (T1: per-(workflow, question) majority). Choice/noul values equal `scripts/metrics_extra.py summary` (cross-check 92/92 questions; bootstrap CIs and per-class detail in `laya/metrics_extra_summary.md`). Score questions (T6, T1) come from the bench_local port only. n=40 (T7: 20 per language), so a 95% CI is about ±0.15.

## 1. Accuracy by set and checkpoint

| set | in training mix | model (answered by) | n | accuracy [Wilson 95%] | macro-F1 | Brier | ECE | mean conf | majority | Δ vs majority | upstream published (english / multilingual / typed-decisions) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1_typed_decisions_40 | no | english (english 200) | 200 | 66/200 = 0.330 [0.269, 0.398] | - | 0.778 | 0.206 | 0.526 | 0.530 | -0.200 | 0.362 / 0.352 / 0.766 (fine-tuned) (BENCHMARKS.md:172-174 (2,000 decisions); Jev 0.727 (:175)) |
| T1_typed_decisions_40, Jev-comparable | no | english (english 120) | 120 | 46/120 = 0.383 [0.301, 0.473] | - | 0.724 | 0.205 | 0.536 | 0.575 | -0.192 | 0.362 / 0.352 / 0.766 (fine-tuned) (BENCHMARKS.md:172-174 (2,000 decisions); Jev 0.727 (:175)) |
| T1_typed_decisions_40 | no | multilingual (multilingual 200) | 200 | 61/200 = 0.305 [0.245, 0.372] | - | 0.965 | 0.383 | 0.680 | 0.530 | -0.225 | 0.362 / 0.352 / 0.766 (fine-tuned) (BENCHMARKS.md:172-174 (2,000 decisions); Jev 0.727 (:175)) |
| T1_typed_decisions_40, Jev-comparable | no | multilingual (multilingual 120) | 120 | 44/120 = 0.367 [0.286, 0.456] | - | 0.949 | 0.391 | 0.752 | 0.575 | -0.208 | 0.362 / 0.352 / 0.766 (fine-tuned) (BENCHMARKS.md:172-174 (2,000 decisions); Jev 0.727 (:175)) |
| T1_typed_decisions_40 | no | router (english 200) | 200 | 66/200 = 0.330 [0.269, 0.398] | - | 0.778 | 0.206 | 0.526 | 0.530 | -0.200 | 0.362 / 0.352 / 0.766 (fine-tuned) (BENCHMARKS.md:172-174 (2,000 decisions); Jev 0.727 (:175)) |
| T1_typed_decisions_40, Jev-comparable | no | router (english 120) | 120 | 46/120 = 0.383 [0.301, 0.473] | - | 0.724 | 0.205 | 0.536 | 0.575 | -0.192 | 0.362 / 0.352 / 0.766 (fine-tuned) (BENCHMARKS.md:172-174 (2,000 decisions); Jev 0.727 (:175)) |
| T1_typed_decisions_40 | no | typed-decisions (typed-decisions 200) | 200 | 159/200 = 0.795 [0.734, 0.845] | - | 0.386 | 0.240 | 0.561 | 0.530 | +0.265 | 0.362 / 0.352 / 0.766 (fine-tuned) (BENCHMARKS.md:172-174 (2,000 decisions); Jev 0.727 (:175)) |
| T1_typed_decisions_40, Jev-comparable | no | typed-decisions (typed-decisions 120) | 120 | 104/120 = 0.867 [0.794, 0.916] | - | 0.343 | 0.279 | 0.588 | 0.575 | +0.292 | 0.362 / 0.352 / 0.766 (fine-tuned) (BENCHMARKS.md:172-174 (2,000 decisions); Jev 0.727 (:175)) |
| T1_typed_decisions_40_noulnocrit | no | english (english 60) | 60 | 31/60 = 0.517 [0.393, 0.638] | - | 0.655 | 0.278 | 0.745 | - | - | comparison-only variant, §2b |
| T1_typed_decisions_40_noulnocrit | no | multilingual (multilingual 60) | 60 | 25/60 = 0.417 [0.301, 0.543] | - | 0.997 | 0.479 | 0.888 | - | - | comparison-only variant, §2b |
| T2_ag_news_40 | yes | english (english 40) | 40 | 39/40 = 0.975 [0.871, 0.996] | 0.975 | 0.053 | 0.083 | 0.930 | 0.250 | +0.725 | 0.947 (T4) or 0.950 (apps) / 0.937 or 0.930 / 0.953 (README.md:1352 T4 N=600, BENCHMARKS.md:160 apps N=400; Jev 0.910) |
| T2_ag_news_40 | yes | multilingual (multilingual 40) | 40 | 37/40 = 0.925 [0.801, 0.974] | 0.926 | 0.107 | 0.058 | 0.983 | 0.250 | +0.675 | 0.947 (T4) or 0.950 (apps) / 0.937 or 0.930 / 0.953 (README.md:1352 T4 N=600, BENCHMARKS.md:160 apps N=400; Jev 0.910) |
| T2_ag_news_40 | yes | router (english 40) | 40 | 39/40 = 0.975 [0.871, 0.996] | 0.975 | 0.053 | 0.083 | 0.930 | 0.250 | +0.725 | 0.947 (T4) or 0.950 (apps) / 0.937 or 0.930 / 0.953 (README.md:1352 T4 N=600, BENCHMARKS.md:160 apps N=400; Jev 0.910) |
| T3_emotion_40 | no | english (english 40) | 40 | 30/40 = 0.750 [0.598, 0.858] | 0.752 | 0.429 | 0.174 | 0.900 | 0.175 | +0.575 | 0.573 (T4) or 0.595 (apps) / 0.513 or 0.530 / 0.600 (README.md:1354, BENCHMARKS.md:161; Jev 0.480) |
| T3_emotion_40 | no | multilingual (multilingual 40) | 40 | 25/40 = 0.625 [0.470, 0.758] | 0.619 | 0.631 | 0.313 | 0.924 | 0.175 | +0.450 | 0.573 (T4) or 0.595 (apps) / 0.513 or 0.530 / 0.600 (README.md:1354, BENCHMARKS.md:161; Jev 0.480) |
| T3_emotion_40 | no | router (english 40) | 40 | 30/40 = 0.750 [0.598, 0.858] | 0.752 | 0.429 | 0.174 | 0.900 | 0.175 | +0.575 | 0.573 (T4) or 0.595 (apps) / 0.513 or 0.530 / 0.600 (README.md:1354, BENCHMARKS.md:161; Jev 0.480) |
| T4_banking77_10opt_40 | unknown | english (english 40) | 40 | 29/40 = 0.725 [0.572, 0.839] | 0.636 | 0.349 | 0.150 | 0.860 | 0.025 | +0.700 | (0.425 @77 opt) / (0.425 @77 opt) / (0.492 @77 opt) (BENCHMARKS.md:162, 77 options: not comparable; Jev 0.870 @72) |
| T4_banking77_10opt_40 | unknown | multilingual (multilingual 40) | 40 | 30/40 = 0.750 [0.598, 0.858] | 0.624 | 0.478 | 0.262 | 0.832 | 0.025 | +0.725 | (0.425 @77 opt) / (0.425 @77 opt) / (0.492 @77 opt) (BENCHMARKS.md:162, 77 options: not comparable; Jev 0.870 @72) |
| T4_banking77_10opt_40 | unknown | router (english 40) | 40 | 29/40 = 0.725 [0.572, 0.839] | 0.636 | 0.349 | 0.150 | 0.860 | 0.025 | +0.700 | (0.425 @77 opt) / (0.425 @77 opt) / (0.492 @77 opt) (BENCHMARKS.md:162, 77 options: not comparable; Jev 0.870 @72) |
| T5_boolq_40 | yes | english (english 40) | 40 | 29/40 = 0.725 [0.572, 0.839] | 0.725 | 0.393 | 0.190 | 0.897 | 0.500 | +0.225 | 0.830 / 0.787 / - (README.md:1353 (N=600)) |
| T5_boolq_40 | yes | multilingual (multilingual 40) | 40 | 24/40 = 0.600 [0.446, 0.737] | 0.599 | 0.615 | 0.294 | 0.870 | 0.500 | +0.100 | 0.830 / 0.787 / - (README.md:1353 (N=600)) |
| T5_boolq_40 | yes | router (english 40) | 40 | 29/40 = 0.725 [0.572, 0.839] | 0.725 | 0.393 | 0.190 | 0.897 | 0.500 | +0.225 | 0.830 / 0.787 / - (README.md:1353 (N=600)) |
| T6_sst5_40 | no | english (english 40) | 40 | 17/40 = 0.425 [0.285, 0.578] | 0.344 | 0.770 | 0.239 | 0.654 | 0.200 | +0.225 | 0.372 / 0.282 / - (README.md:1356 (argmax level, N=600)) |
| T6_sst5_40 | no | multilingual (multilingual 40) | 40 | 13/40 = 0.325 [0.201, 0.480] | 0.202 | 1.149 | 0.513 | 0.824 | 0.200 | +0.125 | 0.372 / 0.282 / - (README.md:1356 (argmax level, N=600)) |
| T6_sst5_40 | no | router (english 40) | 40 | 17/40 = 0.425 [0.285, 0.578] | 0.344 | 0.770 | 0.239 | 0.654 | 0.200 | +0.225 | 0.372 / 0.282 / - (README.md:1356 (argmax level, N=600)) |
| T7_massive_intent_10opt_de_20 | unknown | english (english 20) | 20 | 7/20 = 0.350 [0.181, 0.567] | 0.295 | 1.046 | 0.513 | 0.848 | 0.150 | +0.200 | 20-opt refs in §4 |
| T7_massive_intent_10opt_de_20 | unknown | multilingual (multilingual 20) | 20 | 8/20 = 0.400 [0.219, 0.613] | 0.310 | 0.890 | 0.453 | 0.797 | 0.150 | +0.250 | 20-opt refs in §4 |
| T7_massive_intent_10opt_de_20 | unknown | router (multilingual 15, english 5) | 20 | 7/20 = 0.350 [0.181, 0.567] | 0.262 | 1.009 | 0.485 | 0.835 | 0.150 | +0.200 | 20-opt refs in §4 |
| T7_massive_intent_10opt_en_20 | unknown | english (english 20) | 20 | 14/20 = 0.700 [0.481, 0.855] | 0.544 | 0.394 | 0.214 | 0.899 | 0.150 | +0.550 | 20-opt refs in §4 |
| T7_massive_intent_10opt_en_20 | unknown | multilingual (multilingual 20) | 20 | 17/20 = 0.850 [0.640, 0.948] | 0.748 | 0.293 | 0.184 | 0.895 | 0.150 | +0.700 | 20-opt refs in §4 |
| T7_massive_intent_10opt_en_20 | unknown | router (english 20) | 20 | 14/20 = 0.700 [0.481, 0.855] | 0.544 | 0.394 | 0.214 | 0.899 | 0.150 | +0.550 | 20-opt refs in §4 |
| T7_massive_intent_10opt_ja_20 | unknown | english (english 20) | 20 | 9/20 = 0.450 [0.258, 0.658] | 0.288 | 0.681 | 0.351 | 0.678 | 0.150 | +0.300 | 20-opt refs in §4 |
| T7_massive_intent_10opt_ja_20 | unknown | multilingual (multilingual 20) | 20 | 16/20 = 0.800 [0.584, 0.919] | 0.733 | 0.289 | 0.199 | 0.870 | 0.150 | +0.650 | 20-opt refs in §4 |
| T7_massive_intent_10opt_ja_20 | unknown | router (multilingual 20) | 20 | 16/20 = 0.800 [0.584, 0.919] | 0.733 | 0.289 | 0.199 | 0.870 | 0.150 | +0.650 | 20-opt refs in §4 |
| T7_massive_intent_10opt_ko_20 | unknown | english (english 20) | 20 | 2/20 = 0.100 [0.028, 0.301] | 0.052 | 1.164 | 0.435 | 0.535 | 0.150 | -0.050 | 20-opt refs in §4 |
| T7_massive_intent_10opt_ko_20 | unknown | multilingual (multilingual 20) | 20 | 9/20 = 0.450 [0.258, 0.658] | 0.325 | 0.808 | 0.365 | 0.815 | 0.150 | +0.300 | 20-opt refs in §4 |
| T7_massive_intent_10opt_ko_20 | unknown | router (multilingual 20) | 20 | 9/20 = 0.450 [0.258, 0.658] | 0.325 | 0.808 | 0.365 | 0.815 | 0.150 | +0.300 | 20-opt refs in §4 |
| T7_massive_intent_10opt_zh-CN_20 | unknown | english (english 20) | 20 | 9/20 = 0.450 [0.258, 0.658] | 0.297 | 0.886 | 0.414 | 0.864 | 0.150 | +0.300 | 20-opt refs in §4 |
| T7_massive_intent_10opt_zh-CN_20 | unknown | multilingual (multilingual 20) | 20 | 12/20 = 0.600 [0.387, 0.781] | 0.516 | 0.642 | 0.319 | 0.781 | 0.150 | +0.450 | 20-opt refs in §4 |
| T7_massive_intent_10opt_zh-CN_20 | unknown | router (multilingual 20) | 20 | 12/20 = 0.600 [0.387, 0.781] | 0.516 | 0.642 | 0.319 | 0.781 | 0.150 | +0.450 | 20-opt refs in §4 |
| T8_prompt_injections_40 | no | english (english 40) | 40 | 31/40 = 0.775 [0.625, 0.877] | 0.763 | 0.401 | 0.223 | 0.962 | 0.500 | +0.275 | 0.698 / 0.578 / - (README.md:1355 (n=116)) |
| T8_prompt_injections_40 | no | multilingual (multilingual 40) | 40 | 23/40 = 0.575 [0.422, 0.715] | 0.540 | 0.692 | 0.380 | 0.940 | 0.500 | +0.075 | 0.698 / 0.578 / - (README.md:1355 (n=116)) |
| T8_prompt_injections_40 | no | router (english 26, multilingual 14) | 40 | 29/40 = 0.725 [0.572, 0.839] | 0.710 | 0.510 | 0.261 | 0.979 | 0.500 | +0.225 | 0.698 / 0.578 / - (README.md:1355 (n=116)) |

## 2. T1 typed-decisions (40 cases / 200 decisions, Part B metrics)

Upstream (BENCHMARKS.md:170-178, 2,000 decisions): english 0.362 / soft 0.332 / Brier 0.316 / ECE 0.175 / MAE 0.694; multilingual 0.352 / 0.328 / 0.463 / 0.314 / 0.760; laya-typed-decisions 0.766 / 0.471 / 0.061 / 0.213 / 0.242 (fine-tuned on typed-decisions train, not zero-shot); Jev 1.13.0 published 0.727 / 0.580 / 0.148 / 0.144 / 0.391; majority 0.461. Brier here is Part B's `brier_vs_soft`; score MAE is |E[level] − teacher score|.

| model | accuracy (vs argmax gold) | accuracy (vs dataset `label`, upstream's) | soft acc | Brier vs soft | ECE | score MAE | within 1 level | choice / noul / score acc | majority per qid (upstream rule) / per (workflow, qid) |
|---|---|---|---|---|---|---|---|---|---|
| english | 0.330 [0.269, 0.398] | 0.325 | 0.320 | 0.334 | 0.206 | 0.719 | 0.787 | 0.233 / 0.467 / 0.300 | 0.530 / 0.605 |
| multilingual | 0.305 [0.245, 0.372] | 0.300 | 0.305 | 0.528 | 0.383 | 0.773 | 0.688 | 0.300 / 0.433 / 0.212 | 0.530 / 0.605 |
| router | 0.330 [0.269, 0.398] | 0.325 | 0.320 | 0.334 | 0.206 | 0.719 | 0.787 | 0.233 / 0.467 / 0.300 | 0.530 / 0.605 |
| typed-decisions | 0.795 [0.734, 0.845] | 0.790 | 0.475 | 0.062 | 0.240 | 0.225 | 0.988 | 0.750 / 0.950 / 0.713 | 0.530 / 0.605 |

Jev-comparable decisions only (120 = choice 50 + noul 60 + 5-level score 10; excluded: the 70 4-level score decisions, since the playground's Score takes 5 levels, and customer_service/action, whose options reach 87-89 chars > the 80-char choice input; `jev_comparable_n` in MANIFEST). Wilson 95% CIs; Brier (one-hot) is against the argmax gold, Brier vs soft against the teacher distribution; score MAE over the 10 five-level decisions:

| model | all 120 | choice (50) | noul (60) | score, 5 levels (10) | soft acc | Brier vs soft | Brier (one-hot) | score MAE | majority per qid |
|---|---|---|---|---|---|---|---|---|---|
| english | 46/120 = 0.383 [0.301, 0.473] | 14/50 = 0.280 [0.175, 0.417] | 28/60 = 0.467 [0.346, 0.591] | 4/10 = 0.400 [0.168, 0.687] | 0.361 | 0.333 | 0.724 | 0.584 | 0.575 |
| multilingual | 44/120 = 0.367 [0.286, 0.456] | 16/50 = 0.320 [0.208, 0.458] | 26/60 = 0.433 [0.316, 0.559] | 2/10 = 0.200 [0.057, 0.510] | 0.351 | 0.574 | 0.949 | 0.671 | 0.575 |
| router | 46/120 = 0.383 [0.301, 0.473] | 14/50 = 0.280 [0.175, 0.417] | 28/60 = 0.467 [0.346, 0.591] | 4/10 = 0.400 [0.168, 0.687] | 0.361 | 0.333 | 0.724 | 0.584 | 0.575 |
| typed-decisions | 104/120 = 0.867 [0.794, 0.916] | 40/50 = 0.800 [0.670, 0.888] | 57/60 = 0.950 [0.863, 0.983] | 7/10 = 0.700 [0.397, 0.892] | 0.519 | 0.059 | 0.343 | 0.255 | 0.575 |

## 2b. T1 noul with and without true/false criteria (playground Boolean has no description field)

`T1_typed_decisions_40_noulnocrit.jsonl` = the 60 noul questions with `criteria` removed (20 of them, duplicate and credential_compromise, never had any: same input, so their answers must match). Paired on (row, question); with only / without only = right in one condition and wrong in the other; exact McNemar.

| model | decisions | accuracy with criteria | without | with only / without only | McNemar p | predicted true with / without (gold true) | identical p(true) |
|---|---|---|---|---|---|---|---|
| english | all (60) | 0.467 | 0.517 | 4 / 7 | 0.5488 | 43 / 32 (23) | 20/60 |
| english | had criteria (40) | 0.575 | 0.650 | 4 / 7 | 0.5488 | 24 / 13 (19) | 0/40 |
| english | never had criteria (20) | 0.250 | 0.250 | 0 / 0 | 1.0000 | 19 / 19 (4) | 20/20 |
| multilingual | all (60) | 0.433 | 0.417 | 4 / 3 | 1.0000 | 41 / 42 (23) | 20/60 |
| multilingual | had criteria (40) | 0.450 | 0.425 | 4 / 3 | 1.0000 | 25 / 26 (19) | 0/40 |
| multilingual | never had criteria (20) | 0.400 | 0.400 | 0 / 0 | 1.0000 | 16 / 16 (4) | 20/20 |

| model | agent_trace_observability | customer_service | invoice_processing | security_incidents |
|---|---|---|---|---|
| english | 0.420 | 0.360 | 0.160 | 0.380 |
| multilingual | 0.260 | 0.420 | 0.120 | 0.420 |
| router | 0.420 | 0.360 | 0.160 | 0.380 |
| typed-decisions | 0.800 | 0.740 | 0.800 | 0.840 |

## 3. T6 SST-5 (score, 5 levels)

Upstream N=600 (research/results/t4_colab_benchmark.json `en.sst5`): english acc 0.372, MAE 0.905, within 1 0.632; multilingual 0.282, 1.359, 0.450.

| model | accuracy (argmax level) | score MAE (laya-evals) | within 1 level |
|---|---|---|---|
| english | 0.425 [0.285, 0.578] | 0.888 | 0.650 |
| multilingual | 0.325 [0.201, 0.480] | 1.419 | 0.400 |
| router | 0.425 [0.285, 0.578] | 0.888 | 0.650 |

## 4. T7 MASSIVE intent, 10 options, same 20 ids per language

Upstream is 20 options (random 0.05; ours 0.10): T4 notebook 300/lang and CPU sweep 100/lang, english / multilingual.

| lang | english | multilingual | router (answered by) | upstream 20-opt T4 | upstream 20-opt CPU sweep |
|---|---|---|---|---|---|
| en | 14/20 = 0.70 | 17/20 = 0.85 | 14/20 = 0.70 (english) | 0.783 / 0.657 | 0.820 / 0.710 |
| de | 7/20 = 0.35 | 8/20 = 0.40 | 7/20 = 0.35 (multilingual, english) | 0.420 / 0.467 | 0.420 / 0.500 |
| ja | 9/20 = 0.45 | 16/20 = 0.80 | 16/20 = 0.80 (multilingual) | 0.547 / 0.587 | 0.530 / 0.640 |
| zh-CN | 9/20 = 0.45 | 12/20 = 0.60 | 12/20 = 0.60 (multilingual) | 0.593 / 0.607 | 0.620 / 0.650 |
| ko | 2/20 = 0.10 | 9/20 = 0.45 | 9/20 = 0.45 (multilingual) | 0.103 / 0.490 | 0.110 / 0.470 |

## 4b. T4 option rendering: archived v0 vs key-only (same 40 rows, options and option order)

v0 (`T4_banking77_10opt_40_v0.jsonl`, sha256 df700caa…) rendered each option `key: key spaced`, up to 98 chars; the key-only rebuild (coordinator decision (b)) is upstream's rendering (bench_apps.py:120-122), max 48 chars. v0 reports are kept as `laya/T4_banking77_10opt_40_v0_<model>.json`.

| model | v0 accuracy | key-only accuracy | right only in v0 / only in key-only | exact McNemar p | same choice |
|---|---|---|---|---|---|
| english | 0.825 | 0.725 | 4 / 0 | 0.1250 | 33/40 |
| multilingual | 0.575 | 0.750 | 0 / 7 | 0.0156 | 32/40 |
| router | 0.825 | 0.725 | 4 / 0 | 0.1250 | 33/40 |

## 5. Determinism, option order, truncation

- Determinism (T1 english run twice, 200 decisions): answers identical True, overall identical except timing True.
- Option-order probe, T2 AG News, 1 permutation per item (`scripts/probe_option_order.py`, upstream method build_benchmark_nb.py:640-678; upstream refs 20-opt en 0.150 / 0.230, emotion 0.040 / 0.090, Jev 0.13):

| checkpoint | n | options | orig acc | per-perm flip [95% CI] | perm acc | identity perms | mean |Δ conf| | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|
| english | 40 | 4 | 0.975 | 0.000 [0.000, 0.000] | 0.975 | 2 | 0.008 | 40/40 argmax, max |Δp| 0.0000 |
| multilingual | 40 | 4 | 0.925 | 0.000 [0.000, 0.000] | 0.925 | 2 | 0.004 | 40/40 argmax, max |Δp| 0.0000 |

State truncation (decisions whose state lost tokens to `max_len`; Jev reads the whole state):

| set | english (512) | multilingual (1024) | typed-decisions (1024) |
|---|---|---|---|
| T1_typed_decisions_40 | 4/200 (max 55 tok dropped) | 0/200 (max 0 tok dropped) | 0/200 (max 0 tok dropped) |
| T1_typed_decisions_40_noulnocrit | 0/60 (max 0 tok dropped) | 0/60 (max 0 tok dropped) | 0/60 (max 0 tok dropped) |
| T2_ag_news_40 | 0/40 (max 0 tok dropped) | 0/40 (max 0 tok dropped) | 0/40 (max 0 tok dropped) |
| T3_emotion_40 | 0/40 (max 0 tok dropped) | 0/40 (max 0 tok dropped) | 0/40 (max 0 tok dropped) |
| T4_banking77_10opt_40 | 0/40 (max 0 tok dropped) | 0/40 (max 0 tok dropped) | 0/40 (max 0 tok dropped) |
| T5_boolq_40 | 0/40 (max 0 tok dropped) | 0/40 (max 0 tok dropped) | 0/40 (max 0 tok dropped) |
| T6_sst5_40 | 0/40 (max 0 tok dropped) | 0/40 (max 0 tok dropped) | 0/40 (max 0 tok dropped) |
| T7_massive_intent_10opt_de_20 | 0/20 (max 0 tok dropped) | 0/20 (max 0 tok dropped) | 0/20 (max 0 tok dropped) |
| T7_massive_intent_10opt_en_20 | 0/20 (max 0 tok dropped) | 0/20 (max 0 tok dropped) | 0/20 (max 0 tok dropped) |
| T7_massive_intent_10opt_ja_20 | 0/20 (max 0 tok dropped) | 0/20 (max 0 tok dropped) | 0/20 (max 0 tok dropped) |
| T7_massive_intent_10opt_ko_20 | 0/20 (max 0 tok dropped) | 0/20 (max 0 tok dropped) | 0/20 (max 0 tok dropped) |
| T7_massive_intent_10opt_zh-CN_20 | 0/20 (max 0 tok dropped) | 0/20 (max 0 tok dropped) | 0/20 (max 0 tok dropped) |
| T8_prompt_injections_40 | 0/40 (max 0 tok dropped) | 0/40 (max 0 tok dropped) | 0/40 (max 0 tok dropped) |

## 6. Pipeline check against upstream, and T3 representativeness (english)

- Upstream en.emotion suite (first 600 test rows, same question; `checks/emotion_first600.jsonl`): accuracy 0.5733, ECE 0.3237. Upstream T4 run: 0.5733, ECE 0.3238 (research/results/t4_colab_benchmark.json `en.emotion`), so this pipeline (laya-evals, CPU fp32, checkpoint 55cf4c4) reproduces the published number.
- Whole test split (2,000 rows): accuracy 0.5950; per-class recall anger 0.498, fear 0.379, joy 0.679, love 0.365, sadness 0.713, surprise 0.364.
- T3's 40 rows get the same choice, probabilities and answer_confidence inside the 2,000-row run (40/40; whole answer dict 39/40, the other differs only in the entropy `confidence` at the 4th decimal, batch padding), and under the whole-split per-class recall their class mix would score 0.506; observed 0.750. The T3 draw (seed 13) is easy for Laya english, not representative: compare systems paired on it, not against published accuracies.

## 7. Run identity

| report | dataset_sha256 | questions_sha256 | revisions |
|---|---|---|---|
| T1_typed_decisions_40_english | 749a24c4c0db9776 | d46ef26a6ec2f2f8 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T1_typed_decisions_40_rerun | 749a24c4c0db9776 | d46ef26a6ec2f2f8 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T1_typed_decisions_40_multilingual | 749a24c4c0db9776 | d46ef26a6ec2f2f8 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T1_typed_decisions_40_router | 749a24c4c0db9776 | d46ef26a6ec2f2f8 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T1_typed_decisions_40_typed-decisions | 749a24c4c0db9776 | d46ef26a6ec2f2f8 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T1_typed_decisions_40_noulnocrit_english | 2508b8172b70cd65 | 7b7f5dac86a48ee9 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T1_typed_decisions_40_noulnocrit_multilingual | 2508b8172b70cd65 | 7b7f5dac86a48ee9 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T2_ag_news_40_english | 555c7cd7d38c78d1 | c472cb1cb971dab3 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T2_ag_news_40_multilingual | 555c7cd7d38c78d1 | c472cb1cb971dab3 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T2_ag_news_40_router | 555c7cd7d38c78d1 | c472cb1cb971dab3 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T3_emotion_40_english | 2246b5f04b1ed714 | bd7cc49e3561bf50 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T3_emotion_40_multilingual | 2246b5f04b1ed714 | bd7cc49e3561bf50 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T3_emotion_40_router | 2246b5f04b1ed714 | bd7cc49e3561bf50 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T4_banking77_10opt_40_english | b124b7fb685abe85 | 3c4b9b99f9cc5adc | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T4_banking77_10opt_40_multilingual | b124b7fb685abe85 | 3c4b9b99f9cc5adc | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T4_banking77_10opt_40_router | b124b7fb685abe85 | 3c4b9b99f9cc5adc | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T5_boolq_40_english | 2b140a293790121b | d8699dd37a63aa7b | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T5_boolq_40_multilingual | 2b140a293790121b | d8699dd37a63aa7b | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T5_boolq_40_router | 2b140a293790121b | d8699dd37a63aa7b | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T6_sst5_40_english | f56ebc3bb73ed687 | 9f4cb5fe47389ccf | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T6_sst5_40_multilingual | f56ebc3bb73ed687 | 9f4cb5fe47389ccf | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T6_sst5_40_router | f56ebc3bb73ed687 | 9f4cb5fe47389ccf | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_de_20_english | 56e7943c697a3bc5 | e587cdad8d85f485 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_de_20_multilingual | 56e7943c697a3bc5 | e587cdad8d85f485 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_de_20_router | 56e7943c697a3bc5 | e587cdad8d85f485 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_en_20_english | 034e2c88a7304632 | e587cdad8d85f485 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_en_20_multilingual | 034e2c88a7304632 | e587cdad8d85f485 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_en_20_router | 034e2c88a7304632 | e587cdad8d85f485 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_ja_20_english | dd2169a2ce4d50d6 | e587cdad8d85f485 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_ja_20_multilingual | dd2169a2ce4d50d6 | e587cdad8d85f485 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_ja_20_router | dd2169a2ce4d50d6 | e587cdad8d85f485 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_ko_20_english | e17bfac7605ad315 | e587cdad8d85f485 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_ko_20_multilingual | e17bfac7605ad315 | e587cdad8d85f485 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_ko_20_router | e17bfac7605ad315 | e587cdad8d85f485 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_zh-CN_20_english | 0dfe24d6f0fb09aa | e587cdad8d85f485 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_zh-CN_20_multilingual | 0dfe24d6f0fb09aa | e587cdad8d85f485 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T7_massive_intent_10opt_zh-CN_20_router | 0dfe24d6f0fb09aa | e587cdad8d85f485 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T8_prompt_injections_40_english | ced9111cc7f71774 | ba5538b67233d0c6 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T8_prompt_injections_40_multilingual | ced9111cc7f71774 | ba5538b67233d0c6 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
| T8_prompt_injections_40_router | ced9111cc7f71774 | ba5538b67233d0c6 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} |
