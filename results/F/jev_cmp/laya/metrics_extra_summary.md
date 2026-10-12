# metrics_extra summary

`scripts/metrics_extra.py summary results/F/jev_cmp/laya/T1_typed_decisions_40_english.json results/F/jev_cmp/laya/T1_typed_decisions_40_english_rerun.json results/F/jev_cmp/laya/T1_typed_decisions_40_multilingual.json results/F/jev_cmp/laya/T1_typed_decisions_40_noulnocrit_english.json results/F/jev_cmp/laya/T1_typed_decisions_40_noulnocrit_multilingual.json results/F/jev_cmp/laya/T1_typed_decisions_40_router.json results/F/jev_cmp/laya/T1_typed_decisions_40_typed-decisions.json results/F/jev_cmp/laya/T2_ag_news_40_english.json results/F/jev_cmp/laya/T2_ag_news_40_multilingual.json results/F/jev_cmp/laya/T2_ag_news_40_router.json results/F/jev_cmp/laya/T3_emotion_40_english.json results/F/jev_cmp/laya/T3_emotion_40_multilingual.json results/F/jev_cmp/laya/T3_emotion_40_router.json results/F/jev_cmp/laya/T4_banking77_10opt_40_english.json results/F/jev_cmp/laya/T4_banking77_10opt_40_multilingual.json results/F/jev_cmp/laya/T4_banking77_10opt_40_router.json results/F/jev_cmp/laya/T5_boolq_40_english.json results/F/jev_cmp/laya/T5_boolq_40_multilingual.json results/F/jev_cmp/laya/T5_boolq_40_router.json results/F/jev_cmp/laya/T7_massive_intent_10opt_de_20_english.json results/F/jev_cmp/laya/T7_massive_intent_10opt_de_20_multilingual.json results/F/jev_cmp/laya/T7_massive_intent_10opt_de_20_router.json results/F/jev_cmp/laya/T7_massive_intent_10opt_en_20_english.json results/F/jev_cmp/laya/T7_massive_intent_10opt_en_20_multilingual.json results/F/jev_cmp/laya/T7_massive_intent_10opt_en_20_router.json results/F/jev_cmp/laya/T7_massive_intent_10opt_ja_20_english.json results/F/jev_cmp/laya/T7_massive_intent_10opt_ja_20_multilingual.json results/F/jev_cmp/laya/T7_massive_intent_10opt_ja_20_router.json results/F/jev_cmp/laya/T7_massive_intent_10opt_ko_20_english.json results/F/jev_cmp/laya/T7_massive_intent_10opt_ko_20_multilingual.json results/F/jev_cmp/laya/T7_massive_intent_10opt_ko_20_router.json results/F/jev_cmp/laya/T7_massive_intent_10opt_zh-CN_20_english.json results/F/jev_cmp/laya/T7_massive_intent_10opt_zh-CN_20_multilingual.json results/F/jev_cmp/laya/T7_massive_intent_10opt_zh-CN_20_router.json results/F/jev_cmp/laya/T8_prompt_injections_40_english.json results/F/jev_cmp/laya/T8_prompt_injections_40_multilingual.json results/F/jev_cmp/laya/T8_prompt_injections_40_router.json --out /Users/banhun/banhun28/lab/benchmarkforLaya/results/F/jev_cmp/laya/metrics_extra_summary.md --json /Users/banhun/banhun28/lab/benchmarkforLaya/results/F/jev_cmp/laya/metrics_extra_summary.json` (2026-10-06T10:32:42+0900)

| set | model | qid | split | n | accuracy [95% CI] | macro-F1 ∪ | macro-F1 gold | Brier | ECE [95% CI] | mean conf | acc@50%cov | majority | random | Δ vs majority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1_typed_decisions_40 | english | action | all | 20 | 0.200 [0.050, 0.400] | 0.071 | 0.082 | 0.827 | 0.252 [0.178, 0.406] | 0.452 | 0.400 | 0.200 | 0.225 | +0.000 |
| T1_typed_decisions_40 | english | action | dev | 13 | 0.231 [0.000, 0.462] | 0.075 | 0.086 | 0.782 | 0.274 [0.195, 0.427] | 0.448 | 0.500 | 0.231 | 0.227 | +0.000 |
| T1_typed_decisions_40 | english | action | test | 7 | 0.143 [0.000, 0.429] | 0.062 | 0.071 | 0.912 | 0.322 [0.191, 0.522] | 0.460 | 0.333 | 0.143 | 0.221 | +0.000 |
| T1_typed_decisions_40 | english | needs_review | all | 10 | 0.700 [0.400, 1.000] | 0.600 | 0.600 | 0.505 | 0.268 [0.174, 0.515] | 0.619 | 0.400 | 0.600 | 0.500 | +0.100 |
| T1_typed_decisions_40 | english | needs_review | dev | 7 | 0.714 [0.429, 1.000] | 0.650 | 0.650 | 0.508 | 0.297 [0.197, 0.571] | 0.620 | 0.333 | 0.571 | 0.500 | +0.143 |
| T1_typed_decisions_40 | english | needs_review | test | 3 | 0.667 [0.000, 1.000] | 0.400 | 0.400 | 0.496 | 0.230 [0.036, 0.653] | 0.618 | 0.000 | 0.667 | 0.500 | +0.000 |
| T1_typed_decisions_40 | english | outcome | all | 10 | 0.300 [0.100, 0.600] | 0.196 | 0.196 | 0.762 | 0.161 [0.053, 0.459] | 0.460 | 0.200 | 0.400 | 0.250 | -0.100 |
| T1_typed_decisions_40 | english | outcome | dev | 7 | 0.143 [0.000, 0.429] | 0.100 | 0.133 | 0.845 | 0.315 [0.136, 0.497] | 0.458 | 0.000 | 0.429 | 0.250 | -0.286 |
| T1_typed_decisions_40 | english | outcome | test | 3 | 0.667 [0.000, 1.000] | 0.556 | 0.556 | 0.567 | 0.201 [0.118, 0.554] | 0.465 | 1.000 | 0.333 | 0.250 | +0.333 |
| T1_typed_decisions_40 | english | category | all | 10 | 0.400 [0.100, 0.700] | 0.347 | 0.433 | 0.704 | 0.368 [0.216, 0.573] | 0.382 | 0.200 | 0.400 | 0.200 | +0.000 |
| T1_typed_decisions_40 | english | category | dev | 6 | 0.667 [0.333, 1.000] | 0.533 | 0.711 | 0.669 | 0.436 [0.175, 0.673] | 0.357 | 0.667 | 0.500 | 0.200 | +0.167 |
| T1_typed_decisions_40 | english | category | test | 4 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 0.757 | 0.418 [0.342, 0.470] | 0.418 | 0.000 | 0.500 | 0.200 | -0.500 |
| T1_typed_decisions_40 | english | needs_human | all | 10 | 0.700 [0.400, 1.000] | 0.412 | 0.412 | 0.467 | 0.146 [0.052, 0.445] | 0.554 | 0.600 | 0.700 | 0.500 | +0.000 |
| T1_typed_decisions_40 | english | needs_human | dev | 6 | 0.667 [0.333, 1.000] | 0.400 | 0.400 | 0.438 | 0.280 [0.099, 0.479] | 0.565 | 1.000 | 0.667 | 0.500 | +0.000 |
| T1_typed_decisions_40 | english | needs_human | test | 4 | 0.750 [0.250, 1.000] | 0.429 | 0.429 | 0.510 | 0.269 [0.204, 0.554] | 0.539 | 0.500 | 0.750 | 0.500 | +0.000 |
| T1_typed_decisions_40 | english | disposition | all | 20 | 0.150 [0.000, 0.301] | 0.089 | 0.107 | 0.967 | 0.280 [0.176, 0.421] | 0.430 | 0.200 | 0.450 | 0.250 | -0.300 |
| T1_typed_decisions_40 | english | disposition | dev | 6 | 0.167 [0.000, 0.500] | 0.133 | 0.222 | 0.970 | 0.235 [0.030, 0.458] | 0.402 | 0.000 | 0.500 | 0.250 | -0.333 |
| T1_typed_decisions_40 | english | disposition | test | 14 | 0.143 [0.000, 0.357] | 0.089 | 0.111 | 0.965 | 0.300 [0.230, 0.455] | 0.442 | 0.286 | 0.500 | 0.250 | -0.357 |
| T1_typed_decisions_40 | english | duplicate | all | 10 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.175 | 0.763 [0.718, 0.810] | 0.763 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | english | duplicate | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.351 | 0.819 [0.737, 0.900] | 0.819 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | english | duplicate | test | 7 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.100 | 0.739 [0.694, 0.792] | 0.739 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | english | matches_order | all | 10 | 0.200 [0.000, 0.500] | 0.167 | 0.167 | 0.512 | 0.311 [0.014, 0.511] | 0.511 | 0.200 | 0.800 | 0.500 | -0.600 |
| T1_typed_decisions_40 | english | matches_order | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 0.532 | 0.516 [0.506, 0.525] | 0.516 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | english | matches_order | test | 7 | 0.286 [0.000, 0.571] | 0.222 | 0.222 | 0.503 | 0.223 [0.060, 0.507] | 0.509 | 0.333 | 0.714 | 0.500 | -0.429 |
| T1_typed_decisions_40 | english | credential_compromise | all | 10 | 0.500 [0.200, 0.800] | 0.451 | 0.451 | 0.673 | 0.273 [0.074, 0.593] | 0.773 | 0.600 | 0.600 | 0.500 | -0.100 |
| T1_typed_decisions_40 | english | credential_compromise | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.103 | 0.742 [0.699, 0.773] | 0.742 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | english | credential_compromise | test | 7 | 0.714 [0.286, 1.000] | 0.650 | 0.650 | 0.489 | 0.185 [0.072, 0.548] | 0.786 | 0.667 | 0.571 | 0.500 | +0.143 |
| T1_typed_decisions_40 | english | true_positive | all | 10 | 0.700 [0.400, 0.900] | 0.697 | 0.697 | 0.492 | 0.261 [0.147, 0.518] | 0.601 | 0.600 | 0.600 | 0.500 | +0.100 |
| T1_typed_decisions_40 | english | true_positive | dev | 3 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.381 | 0.435 [0.392, 0.480] | 0.565 | 1.000 | 0.667 | 0.500 | +0.333 |
| T1_typed_decisions_40 | english | true_positive | test | 7 | 0.571 [0.143, 0.857] | 0.571 | 0.571 | 0.540 | 0.324 [0.153, 0.596] | 0.617 | 0.333 | 0.714 | 0.500 | -0.143 |
| T1_typed_decisions_40 | english | action | all | 20 | 0.200 [0.050, 0.400] | 0.071 | 0.082 | 0.827 | 0.252 [0.178, 0.406] | 0.452 | 0.400 | 0.200 | 0.225 | +0.000 |
| T1_typed_decisions_40 | english | action | dev | 13 | 0.231 [0.000, 0.462] | 0.075 | 0.086 | 0.782 | 0.274 [0.195, 0.427] | 0.448 | 0.500 | 0.231 | 0.227 | +0.000 |
| T1_typed_decisions_40 | english | action | test | 7 | 0.143 [0.000, 0.429] | 0.062 | 0.071 | 0.912 | 0.322 [0.191, 0.522] | 0.460 | 0.333 | 0.143 | 0.221 | +0.000 |
| T1_typed_decisions_40 | english | needs_review | all | 10 | 0.700 [0.400, 1.000] | 0.600 | 0.600 | 0.505 | 0.268 [0.174, 0.515] | 0.619 | 0.400 | 0.600 | 0.500 | +0.100 |
| T1_typed_decisions_40 | english | needs_review | dev | 7 | 0.714 [0.429, 1.000] | 0.650 | 0.650 | 0.508 | 0.297 [0.197, 0.571] | 0.620 | 0.333 | 0.571 | 0.500 | +0.143 |
| T1_typed_decisions_40 | english | needs_review | test | 3 | 0.667 [0.000, 1.000] | 0.400 | 0.400 | 0.496 | 0.230 [0.036, 0.653] | 0.618 | 0.000 | 0.667 | 0.500 | +0.000 |
| T1_typed_decisions_40 | english | outcome | all | 10 | 0.300 [0.100, 0.600] | 0.196 | 0.196 | 0.762 | 0.161 [0.053, 0.459] | 0.460 | 0.200 | 0.400 | 0.250 | -0.100 |
| T1_typed_decisions_40 | english | outcome | dev | 7 | 0.143 [0.000, 0.429] | 0.100 | 0.133 | 0.845 | 0.315 [0.136, 0.497] | 0.458 | 0.000 | 0.429 | 0.250 | -0.286 |
| T1_typed_decisions_40 | english | outcome | test | 3 | 0.667 [0.000, 1.000] | 0.556 | 0.556 | 0.567 | 0.201 [0.118, 0.554] | 0.465 | 1.000 | 0.333 | 0.250 | +0.333 |
| T1_typed_decisions_40 | english | category | all | 10 | 0.400 [0.100, 0.700] | 0.347 | 0.433 | 0.704 | 0.368 [0.216, 0.573] | 0.382 | 0.200 | 0.400 | 0.200 | +0.000 |
| T1_typed_decisions_40 | english | category | dev | 6 | 0.667 [0.333, 1.000] | 0.533 | 0.711 | 0.669 | 0.436 [0.175, 0.673] | 0.357 | 0.667 | 0.500 | 0.200 | +0.167 |
| T1_typed_decisions_40 | english | category | test | 4 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 0.757 | 0.418 [0.342, 0.470] | 0.418 | 0.000 | 0.500 | 0.200 | -0.500 |
| T1_typed_decisions_40 | english | needs_human | all | 10 | 0.700 [0.400, 1.000] | 0.412 | 0.412 | 0.467 | 0.146 [0.052, 0.445] | 0.554 | 0.600 | 0.700 | 0.500 | +0.000 |
| T1_typed_decisions_40 | english | needs_human | dev | 6 | 0.667 [0.333, 1.000] | 0.400 | 0.400 | 0.438 | 0.280 [0.099, 0.479] | 0.565 | 1.000 | 0.667 | 0.500 | +0.000 |
| T1_typed_decisions_40 | english | needs_human | test | 4 | 0.750 [0.250, 1.000] | 0.429 | 0.429 | 0.510 | 0.269 [0.204, 0.554] | 0.539 | 0.500 | 0.750 | 0.500 | +0.000 |
| T1_typed_decisions_40 | english | disposition | all | 20 | 0.150 [0.000, 0.301] | 0.089 | 0.107 | 0.967 | 0.280 [0.176, 0.421] | 0.430 | 0.200 | 0.450 | 0.250 | -0.300 |
| T1_typed_decisions_40 | english | disposition | dev | 6 | 0.167 [0.000, 0.500] | 0.133 | 0.222 | 0.970 | 0.235 [0.030, 0.458] | 0.402 | 0.000 | 0.500 | 0.250 | -0.333 |
| T1_typed_decisions_40 | english | disposition | test | 14 | 0.143 [0.000, 0.357] | 0.089 | 0.111 | 0.965 | 0.300 [0.230, 0.455] | 0.442 | 0.286 | 0.500 | 0.250 | -0.357 |
| T1_typed_decisions_40 | english | duplicate | all | 10 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.175 | 0.763 [0.718, 0.810] | 0.763 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | english | duplicate | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.351 | 0.819 [0.737, 0.900] | 0.819 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | english | duplicate | test | 7 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.100 | 0.739 [0.694, 0.792] | 0.739 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | english | matches_order | all | 10 | 0.200 [0.000, 0.500] | 0.167 | 0.167 | 0.512 | 0.311 [0.014, 0.511] | 0.511 | 0.200 | 0.800 | 0.500 | -0.600 |
| T1_typed_decisions_40 | english | matches_order | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 0.532 | 0.516 [0.506, 0.525] | 0.516 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | english | matches_order | test | 7 | 0.286 [0.000, 0.571] | 0.222 | 0.222 | 0.503 | 0.223 [0.060, 0.507] | 0.509 | 0.333 | 0.714 | 0.500 | -0.429 |
| T1_typed_decisions_40 | english | credential_compromise | all | 10 | 0.500 [0.200, 0.800] | 0.451 | 0.451 | 0.673 | 0.273 [0.074, 0.593] | 0.773 | 0.600 | 0.600 | 0.500 | -0.100 |
| T1_typed_decisions_40 | english | credential_compromise | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.103 | 0.742 [0.699, 0.773] | 0.742 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | english | credential_compromise | test | 7 | 0.714 [0.286, 1.000] | 0.650 | 0.650 | 0.489 | 0.185 [0.072, 0.548] | 0.786 | 0.667 | 0.571 | 0.500 | +0.143 |
| T1_typed_decisions_40 | english | true_positive | all | 10 | 0.700 [0.400, 0.900] | 0.697 | 0.697 | 0.492 | 0.261 [0.147, 0.518] | 0.601 | 0.600 | 0.600 | 0.500 | +0.100 |
| T1_typed_decisions_40 | english | true_positive | dev | 3 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.381 | 0.435 [0.392, 0.480] | 0.565 | 1.000 | 0.667 | 0.500 | +0.333 |
| T1_typed_decisions_40 | english | true_positive | test | 7 | 0.571 [0.143, 0.857] | 0.571 | 0.571 | 0.540 | 0.324 [0.153, 0.596] | 0.617 | 0.333 | 0.714 | 0.500 | -0.143 |
| T1_typed_decisions_40 | multilingual | action | all | 20 | 0.200 [0.050, 0.400] | 0.163 | 0.210 | 1.258 | 0.648 [0.501, 0.770] | 0.740 | 0.100 | 0.200 | 0.225 | +0.000 |
| T1_typed_decisions_40 | multilingual | action | dev | 13 | 0.231 [0.000, 0.462] | 0.163 | 0.210 | 1.230 | 0.604 [0.405, 0.786] | 0.757 | 0.167 | 0.231 | 0.227 | +0.000 |
| T1_typed_decisions_40 | multilingual | action | test | 7 | 0.143 [0.000, 0.429] | 0.074 | 0.095 | 1.310 | 0.729 [0.627, 0.816] | 0.710 | 0.000 | 0.143 | 0.221 | +0.000 |
| T1_typed_decisions_40 | multilingual | needs_review | all | 10 | 0.600 [0.300, 0.900] | 0.524 | 0.524 | 0.768 | 0.495 [0.292, 0.721] | 0.828 | 0.200 | 0.600 | 0.500 | +0.000 |
| T1_typed_decisions_40 | multilingual | needs_review | dev | 7 | 0.429 [0.143, 0.857] | 0.300 | 0.300 | 1.049 | 0.607 [0.316, 0.865] | 0.855 | 0.333 | 0.571 | 0.500 | -0.143 |
| T1_typed_decisions_40 | multilingual | needs_review | test | 3 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.113 | 0.235 [0.203, 0.289] | 0.765 | 1.000 | 0.667 | 0.500 | +0.333 |
| T1_typed_decisions_40 | multilingual | outcome | all | 10 | 0.300 [0.000, 0.600] | 0.136 | 0.136 | 0.763 | 0.383 [0.268, 0.536] | 0.604 | 0.600 | 0.400 | 0.250 | -0.100 |
| T1_typed_decisions_40 | multilingual | outcome | dev | 7 | 0.429 [0.143, 0.714] | 0.167 | 0.222 | 0.706 | 0.427 [0.306, 0.532] | 0.639 | 1.000 | 0.429 | 0.250 | +0.000 |
| T1_typed_decisions_40 | multilingual | outcome | test | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 0.894 | 0.523 [0.428, 0.647] | 0.523 | 0.000 | 0.333 | 0.250 | -0.333 |
| T1_typed_decisions_40 | multilingual | category | all | 10 | 0.800 [0.500, 1.000] | 0.688 | 0.688 | 0.345 | 0.201 [0.039, 0.412] | 0.919 | 0.800 | 0.400 | 0.200 | +0.400 |
| T1_typed_decisions_40 | multilingual | category | dev | 6 | 0.667 [0.333, 1.000] | 0.556 | 0.556 | 0.567 | 0.284 [0.023, 0.618] | 0.914 | 0.667 | 0.500 | 0.200 | +0.167 |
| T1_typed_decisions_40 | multilingual | category | test | 4 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.012 | 0.075 [0.022, 0.119] | 0.925 | 1.000 | 0.500 | 0.200 | +0.500 |
| T1_typed_decisions_40 | multilingual | needs_human | all | 10 | 0.400 [0.100, 0.700] | 0.375 | 0.375 | 0.650 | 0.355 [0.185, 0.637] | 0.738 | 0.400 | 0.700 | 0.500 | -0.300 |
| T1_typed_decisions_40 | multilingual | needs_human | dev | 6 | 0.167 [0.000, 0.500] | 0.143 | 0.143 | 0.810 | 0.539 [0.257, 0.750] | 0.706 | 0.333 | 0.667 | 0.500 | -0.500 |
| T1_typed_decisions_40 | multilingual | needs_human | test | 4 | 0.750 [0.250, 1.000] | 0.733 | 0.733 | 0.410 | 0.366 [0.131, 0.673] | 0.787 | 0.500 | 0.750 | 0.500 | +0.000 |
| T1_typed_decisions_40 | multilingual | disposition | all | 20 | 0.150 [0.000, 0.350] | 0.087 | 0.140 | 1.156 | 0.412 [0.256, 0.564] | 0.562 | 0.200 | 0.450 | 0.250 | -0.300 |
| T1_typed_decisions_40 | multilingual | disposition | dev | 6 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.325 | 0.564 [0.519, 0.610] | 0.564 | 0.000 | 0.500 | 0.250 | -0.500 |
| T1_typed_decisions_40 | multilingual | disposition | test | 14 | 0.214 [0.071, 0.429] | 0.150 | 0.263 | 1.084 | 0.346 [0.209, 0.568] | 0.560 | 0.286 | 0.500 | 0.250 | -0.286 |
| T1_typed_decisions_40 | multilingual | duplicate | all | 10 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.915 | 0.978 [0.973, 0.983] | 0.978 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | multilingual | duplicate | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.929 | 0.982 [0.979, 0.987] | 0.982 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | multilingual | duplicate | test | 7 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.909 | 0.977 [0.970, 0.983] | 0.977 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | multilingual | matches_order | all | 10 | 0.200 [0.000, 0.500] | 0.167 | 0.167 | 1.447 | 0.751 [0.457, 0.953] | 0.951 | 0.200 | 0.800 | 0.500 | -0.600 |
| T1_typed_decisions_40 | multilingual | matches_order | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.795 | 0.947 [0.926, 0.968] | 0.947 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | multilingual | matches_order | test | 7 | 0.286 [0.000, 0.571] | 0.222 | 0.222 | 1.298 | 0.667 [0.374, 0.956] | 0.953 | 0.333 | 0.714 | 0.500 | -0.429 |
| T1_typed_decisions_40 | multilingual | credential_compromise | all | 10 | 0.800 [0.500, 1.000] | 0.800 | 0.800 | 0.482 | 0.326 [0.138, 0.551] | 0.848 | 0.600 | 0.600 | 0.500 | +0.200 |
| T1_typed_decisions_40 | multilingual | credential_compromise | dev | 3 | 0.667 [0.000, 1.000] | 0.400 | 0.800 | 0.841 | 0.596 [0.401, 0.958] | 0.710 | 0.000 | 1.000 | 0.500 | -0.333 |
| T1_typed_decisions_40 | multilingual | credential_compromise | test | 7 | 0.857 [0.571, 1.000] | 0.844 | 0.844 | 0.328 | 0.210 [0.042, 0.494] | 0.907 | 1.000 | 0.571 | 0.500 | +0.286 |
| T1_typed_decisions_40 | multilingual | true_positive | all | 10 | 0.600 [0.300, 0.900] | 0.524 | 0.524 | 0.528 | 0.310 [0.120, 0.579] | 0.873 | 1.000 | 0.600 | 0.500 | +0.000 |
| T1_typed_decisions_40 | multilingual | true_positive | dev | 3 | 0.667 [0.000, 1.000] | 0.667 | 0.667 | 0.397 | 0.299 [0.038, 0.765] | 0.878 | 1.000 | 0.667 | 0.500 | +0.000 |
| T1_typed_decisions_40 | multilingual | true_positive | test | 7 | 0.571 [0.143, 0.857] | 0.364 | 0.364 | 0.583 | 0.315 [0.073, 0.650] | 0.871 | 1.000 | 0.714 | 0.500 | -0.143 |
| T1_typed_decisions_40_noulnocrit | english | needs_review | all | 10 | 0.600 [0.300, 0.900] | 0.375 | 0.375 | 0.597 | 0.233 [0.079, 0.560] | 0.833 | 0.600 | 0.600 | 0.500 | +0.000 |
| T1_typed_decisions_40_noulnocrit | english | needs_review | dev | 7 | 0.571 [0.143, 0.857] | 0.364 | 0.364 | 0.609 | 0.249 [0.105, 0.648] | 0.820 | 0.667 | 0.571 | 0.500 | +0.000 |
| T1_typed_decisions_40_noulnocrit | english | needs_review | test | 3 | 0.667 [0.000, 1.000] | 0.400 | 0.400 | 0.570 | 0.402 [0.148, 0.899] | 0.864 | 0.000 | 0.667 | 0.500 | +0.000 |
| T1_typed_decisions_40_noulnocrit | english | needs_human | all | 10 | 0.700 [0.400, 1.000] | 0.412 | 0.412 | 0.508 | 0.352 [0.203, 0.585] | 0.734 | 0.600 | 0.700 | 0.500 | +0.000 |
| T1_typed_decisions_40_noulnocrit | english | needs_human | dev | 6 | 0.667 [0.333, 1.000] | 0.400 | 0.400 | 0.482 | 0.365 [0.199, 0.621] | 0.753 | 0.667 | 0.667 | 0.500 | +0.000 |
| T1_typed_decisions_40_noulnocrit | english | needs_human | test | 4 | 0.750 [0.250, 1.000] | 0.429 | 0.429 | 0.547 | 0.472 [0.306, 0.731] | 0.704 | 0.500 | 0.750 | 0.500 | +0.000 |
| T1_typed_decisions_40_noulnocrit | english | duplicate | all | 10 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.175 | 0.763 [0.718, 0.810] | 0.763 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40_noulnocrit | english | duplicate | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.351 | 0.819 [0.737, 0.900] | 0.819 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40_noulnocrit | english | duplicate | test | 7 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.100 | 0.739 [0.694, 0.792] | 0.739 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40_noulnocrit | english | matches_order | all | 10 | 0.700 [0.400, 1.000] | 0.412 | 0.412 | 0.442 | 0.280 [0.103, 0.481] | 0.605 | 0.800 | 0.800 | 0.500 | -0.100 |
| T1_typed_decisions_40_noulnocrit | english | matches_order | dev | 3 | 0.667 [0.000, 1.000] | 0.400 | 0.800 | 0.451 | 0.181 [0.090, 0.589] | 0.593 | 1.000 | 1.000 | 0.500 | -0.333 |
| T1_typed_decisions_40_noulnocrit | english | matches_order | test | 7 | 0.714 [0.429, 1.000] | 0.417 | 0.417 | 0.439 | 0.369 [0.238, 0.533] | 0.610 | 0.667 | 0.714 | 0.500 | +0.000 |
| T1_typed_decisions_40_noulnocrit | english | credential_compromise | all | 10 | 0.500 [0.200, 0.800] | 0.451 | 0.451 | 0.673 | 0.273 [0.074, 0.593] | 0.773 | 0.600 | 0.600 | 0.500 | -0.100 |
| T1_typed_decisions_40_noulnocrit | english | credential_compromise | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.103 | 0.742 [0.699, 0.773] | 0.742 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40_noulnocrit | english | credential_compromise | test | 7 | 0.714 [0.286, 1.000] | 0.650 | 0.650 | 0.489 | 0.185 [0.072, 0.548] | 0.786 | 0.667 | 0.571 | 0.500 | +0.143 |
| T1_typed_decisions_40_noulnocrit | english | true_positive | all | 10 | 0.600 [0.300, 0.900] | 0.583 | 0.583 | 0.533 | 0.187 [0.082, 0.494] | 0.761 | 0.400 | 0.600 | 0.500 | +0.000 |
| T1_typed_decisions_40_noulnocrit | english | true_positive | dev | 3 | 0.667 [0.000, 1.000] | 0.400 | 0.400 | 0.474 | 0.225 [0.087, 0.786] | 0.790 | 1.000 | 0.667 | 0.500 | +0.000 |
| T1_typed_decisions_40_noulnocrit | english | true_positive | test | 7 | 0.571 [0.143, 0.857] | 0.571 | 0.571 | 0.559 | 0.214 [0.083, 0.595] | 0.749 | 0.333 | 0.714 | 0.500 | -0.143 |
| T1_typed_decisions_40_noulnocrit | multilingual | needs_review | all | 10 | 0.400 [0.100, 0.700] | 0.375 | 0.375 | 0.848 | 0.407 [0.222, 0.714] | 0.807 | 0.400 | 0.600 | 0.500 | -0.200 |
| T1_typed_decisions_40_noulnocrit | multilingual | needs_review | dev | 7 | 0.143 [0.000, 0.429] | 0.125 | 0.125 | 1.141 | 0.674 [0.430, 0.881] | 0.817 | 0.333 | 0.571 | 0.500 | -0.429 |
| T1_typed_decisions_40_noulnocrit | multilingual | needs_review | test | 3 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.163 | 0.217 [0.059, 0.478] | 0.783 | 1.000 | 0.667 | 0.500 | +0.333 |
| T1_typed_decisions_40_noulnocrit | multilingual | needs_human | all | 10 | 0.500 [0.200, 0.800] | 0.451 | 0.451 | 0.524 | 0.328 [0.168, 0.578] | 0.794 | 0.800 | 0.700 | 0.500 | -0.200 |
| T1_typed_decisions_40_noulnocrit | multilingual | needs_human | dev | 6 | 0.500 [0.167, 0.833] | 0.486 | 0.486 | 0.629 | 0.329 [0.103, 0.650] | 0.806 | 0.667 | 0.667 | 0.500 | -0.167 |
| T1_typed_decisions_40_noulnocrit | multilingual | needs_human | test | 4 | 0.500 [0.000, 1.000] | 0.333 | 0.333 | 0.366 | 0.328 [0.053, 0.603] | 0.775 | 1.000 | 0.750 | 0.500 | -0.250 |
| T1_typed_decisions_40_noulnocrit | multilingual | duplicate | all | 10 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.915 | 0.978 [0.973, 0.983] | 0.978 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40_noulnocrit | multilingual | duplicate | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.929 | 0.982 [0.979, 0.987] | 0.982 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40_noulnocrit | multilingual | duplicate | test | 7 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.909 | 0.977 [0.970, 0.983] | 0.977 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40_noulnocrit | multilingual | matches_order | all | 10 | 0.200 [0.000, 0.500] | 0.167 | 0.167 | 1.586 | 0.796 [0.497, 0.996] | 0.996 | 0.200 | 0.800 | 0.500 | -0.600 |
| T1_typed_decisions_40_noulnocrit | multilingual | matches_order | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.983 | 0.996 [0.993, 0.997] | 0.996 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40_noulnocrit | multilingual | matches_order | test | 7 | 0.286 [0.000, 0.571] | 0.222 | 0.222 | 1.416 | 0.710 [0.424, 0.996] | 0.996 | 0.333 | 0.714 | 0.500 | -0.429 |
| T1_typed_decisions_40_noulnocrit | multilingual | credential_compromise | all | 10 | 0.800 [0.500, 1.000] | 0.800 | 0.800 | 0.482 | 0.326 [0.138, 0.551] | 0.848 | 0.600 | 0.600 | 0.500 | +0.200 |
| T1_typed_decisions_40_noulnocrit | multilingual | credential_compromise | dev | 3 | 0.667 [0.000, 1.000] | 0.400 | 0.800 | 0.841 | 0.596 [0.401, 0.958] | 0.710 | 0.000 | 1.000 | 0.500 | -0.333 |
| T1_typed_decisions_40_noulnocrit | multilingual | credential_compromise | test | 7 | 0.857 [0.571, 1.000] | 0.844 | 0.844 | 0.328 | 0.210 [0.042, 0.494] | 0.907 | 1.000 | 0.571 | 0.500 | +0.286 |
| T1_typed_decisions_40_noulnocrit | multilingual | true_positive | all | 10 | 0.600 [0.300, 0.900] | 0.583 | 0.583 | 0.627 | 0.365 [0.129, 0.639] | 0.906 | 0.800 | 0.600 | 0.500 | +0.000 |
| T1_typed_decisions_40_noulnocrit | multilingual | true_positive | dev | 3 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.062 | 0.125 [0.000, 0.295] | 0.875 | 1.000 | 0.667 | 0.500 | +0.333 |
| T1_typed_decisions_40_noulnocrit | multilingual | true_positive | test | 7 | 0.429 [0.143, 0.714] | 0.300 | 0.300 | 0.869 | 0.490 [0.185, 0.802] | 0.919 | 1.000 | 0.714 | 0.500 | -0.286 |
| T1_typed_decisions_40 | router | action | all | 20 | 0.200 [0.050, 0.400] | 0.071 | 0.082 | 0.827 | 0.252 [0.178, 0.406] | 0.452 | 0.400 | 0.200 | 0.225 | +0.000 |
| T1_typed_decisions_40 | router | action | dev | 13 | 0.231 [0.000, 0.462] | 0.075 | 0.086 | 0.782 | 0.274 [0.195, 0.427] | 0.448 | 0.500 | 0.231 | 0.227 | +0.000 |
| T1_typed_decisions_40 | router | action | test | 7 | 0.143 [0.000, 0.429] | 0.062 | 0.071 | 0.912 | 0.322 [0.191, 0.522] | 0.460 | 0.333 | 0.143 | 0.221 | +0.000 |
| T1_typed_decisions_40 | router | needs_review | all | 10 | 0.700 [0.400, 1.000] | 0.600 | 0.600 | 0.505 | 0.268 [0.174, 0.515] | 0.619 | 0.400 | 0.600 | 0.500 | +0.100 |
| T1_typed_decisions_40 | router | needs_review | dev | 7 | 0.714 [0.429, 1.000] | 0.650 | 0.650 | 0.508 | 0.297 [0.197, 0.571] | 0.620 | 0.333 | 0.571 | 0.500 | +0.143 |
| T1_typed_decisions_40 | router | needs_review | test | 3 | 0.667 [0.000, 1.000] | 0.400 | 0.400 | 0.496 | 0.230 [0.036, 0.653] | 0.618 | 0.000 | 0.667 | 0.500 | +0.000 |
| T1_typed_decisions_40 | router | outcome | all | 10 | 0.300 [0.100, 0.600] | 0.196 | 0.196 | 0.762 | 0.161 [0.053, 0.459] | 0.460 | 0.200 | 0.400 | 0.250 | -0.100 |
| T1_typed_decisions_40 | router | outcome | dev | 7 | 0.143 [0.000, 0.429] | 0.100 | 0.133 | 0.845 | 0.315 [0.136, 0.497] | 0.458 | 0.000 | 0.429 | 0.250 | -0.286 |
| T1_typed_decisions_40 | router | outcome | test | 3 | 0.667 [0.000, 1.000] | 0.556 | 0.556 | 0.567 | 0.201 [0.118, 0.554] | 0.465 | 1.000 | 0.333 | 0.250 | +0.333 |
| T1_typed_decisions_40 | router | category | all | 10 | 0.400 [0.100, 0.700] | 0.347 | 0.433 | 0.704 | 0.368 [0.216, 0.573] | 0.382 | 0.200 | 0.400 | 0.200 | +0.000 |
| T1_typed_decisions_40 | router | category | dev | 6 | 0.667 [0.333, 1.000] | 0.533 | 0.711 | 0.669 | 0.436 [0.175, 0.673] | 0.357 | 0.667 | 0.500 | 0.200 | +0.167 |
| T1_typed_decisions_40 | router | category | test | 4 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 0.757 | 0.418 [0.342, 0.470] | 0.418 | 0.000 | 0.500 | 0.200 | -0.500 |
| T1_typed_decisions_40 | router | needs_human | all | 10 | 0.700 [0.400, 1.000] | 0.412 | 0.412 | 0.467 | 0.146 [0.052, 0.445] | 0.554 | 0.600 | 0.700 | 0.500 | +0.000 |
| T1_typed_decisions_40 | router | needs_human | dev | 6 | 0.667 [0.333, 1.000] | 0.400 | 0.400 | 0.438 | 0.280 [0.099, 0.479] | 0.565 | 1.000 | 0.667 | 0.500 | +0.000 |
| T1_typed_decisions_40 | router | needs_human | test | 4 | 0.750 [0.250, 1.000] | 0.429 | 0.429 | 0.510 | 0.269 [0.204, 0.554] | 0.539 | 0.500 | 0.750 | 0.500 | +0.000 |
| T1_typed_decisions_40 | router | disposition | all | 20 | 0.150 [0.000, 0.301] | 0.089 | 0.107 | 0.967 | 0.280 [0.176, 0.421] | 0.430 | 0.200 | 0.450 | 0.250 | -0.300 |
| T1_typed_decisions_40 | router | disposition | dev | 6 | 0.167 [0.000, 0.500] | 0.133 | 0.222 | 0.970 | 0.235 [0.030, 0.458] | 0.402 | 0.000 | 0.500 | 0.250 | -0.333 |
| T1_typed_decisions_40 | router | disposition | test | 14 | 0.143 [0.000, 0.357] | 0.089 | 0.111 | 0.965 | 0.300 [0.230, 0.455] | 0.442 | 0.286 | 0.500 | 0.250 | -0.357 |
| T1_typed_decisions_40 | router | duplicate | all | 10 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.175 | 0.763 [0.718, 0.810] | 0.763 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | router | duplicate | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.351 | 0.819 [0.737, 0.900] | 0.819 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | router | duplicate | test | 7 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.100 | 0.739 [0.694, 0.792] | 0.739 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | router | matches_order | all | 10 | 0.200 [0.000, 0.500] | 0.167 | 0.167 | 0.512 | 0.311 [0.014, 0.511] | 0.511 | 0.200 | 0.800 | 0.500 | -0.600 |
| T1_typed_decisions_40 | router | matches_order | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 0.532 | 0.516 [0.506, 0.525] | 0.516 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | router | matches_order | test | 7 | 0.286 [0.000, 0.571] | 0.222 | 0.222 | 0.503 | 0.223 [0.060, 0.507] | 0.509 | 0.333 | 0.714 | 0.500 | -0.429 |
| T1_typed_decisions_40 | router | credential_compromise | all | 10 | 0.500 [0.200, 0.800] | 0.451 | 0.451 | 0.673 | 0.273 [0.074, 0.593] | 0.773 | 0.600 | 0.600 | 0.500 | -0.100 |
| T1_typed_decisions_40 | router | credential_compromise | dev | 3 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.103 | 0.742 [0.699, 0.773] | 0.742 | 0.000 | 1.000 | 0.500 | -1.000 |
| T1_typed_decisions_40 | router | credential_compromise | test | 7 | 0.714 [0.286, 1.000] | 0.650 | 0.650 | 0.489 | 0.185 [0.072, 0.548] | 0.786 | 0.667 | 0.571 | 0.500 | +0.143 |
| T1_typed_decisions_40 | router | true_positive | all | 10 | 0.700 [0.400, 0.900] | 0.697 | 0.697 | 0.492 | 0.261 [0.147, 0.518] | 0.601 | 0.600 | 0.600 | 0.500 | +0.100 |
| T1_typed_decisions_40 | router | true_positive | dev | 3 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.381 | 0.435 [0.392, 0.480] | 0.565 | 1.000 | 0.667 | 0.500 | +0.333 |
| T1_typed_decisions_40 | router | true_positive | test | 7 | 0.571 [0.143, 0.857] | 0.571 | 0.571 | 0.540 | 0.324 [0.153, 0.596] | 0.617 | 0.333 | 0.714 | 0.500 | -0.143 |
| T1_typed_decisions_40 | typed-decisions | action | all | 20 | 0.600 [0.400, 0.800] | 0.490 | 0.490 | 0.580 | 0.258 [0.138, 0.444] | 0.402 | 0.700 | 0.200 | 0.225 | +0.400 |
| T1_typed_decisions_40 | typed-decisions | action | dev | 13 | 0.769 [0.538, 1.000] | 0.618 | 0.618 | 0.534 | 0.408 [0.234, 0.568] | 0.405 | 1.000 | 0.231 | 0.227 | +0.538 |
| T1_typed_decisions_40 | typed-decisions | action | test | 7 | 0.286 [0.000, 0.571] | 0.129 | 0.129 | 0.666 | 0.234 [0.096, 0.405] | 0.398 | 0.333 | 0.143 | 0.221 | +0.143 |
| T1_typed_decisions_40 | typed-decisions | needs_review | all | 10 | 0.900 [0.700, 1.000] | 0.890 | 0.890 | 0.294 | 0.261 [0.185, 0.403] | 0.639 | 1.000 | 0.600 | 0.500 | +0.300 |
| T1_typed_decisions_40 | typed-decisions | needs_review | dev | 7 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.222 | 0.321 [0.265, 0.390] | 0.679 | 1.000 | 0.571 | 0.500 | +0.429 |
| T1_typed_decisions_40 | typed-decisions | needs_review | test | 3 | 0.667 [0.000, 1.000] | 0.400 | 0.400 | 0.463 | 0.196 [0.103, 0.541] | 0.548 | 1.000 | 0.667 | 0.500 | +0.000 |
| T1_typed_decisions_40 | typed-decisions | outcome | all | 10 | 0.800 [0.500, 1.000] | 0.652 | 0.652 | 0.466 | 0.415 [0.237, 0.534] | 0.465 | 1.000 | 0.400 | 0.250 | +0.400 |
| T1_typed_decisions_40 | typed-decisions | outcome | dev | 7 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.385 | 0.514 [0.477, 0.554] | 0.486 | 1.000 | 0.429 | 0.250 | +0.571 |
| T1_typed_decisions_40 | typed-decisions | outcome | test | 3 | 0.333 [0.000, 1.000] | 0.167 | 0.167 | 0.656 | 0.183 [0.093, 0.574] | 0.417 | 0.000 | 0.333 | 0.250 | +0.000 |
| T1_typed_decisions_40 | typed-decisions | category | all | 10 | 0.800 [0.500, 1.000] | 0.604 | 0.604 | 0.272 | 0.335 [0.268, 0.402] | 0.655 | 1.000 | 0.400 | 0.200 | +0.400 |
| T1_typed_decisions_40 | typed-decisions | category | dev | 6 | 0.667 [0.333, 1.000] | 0.417 | 0.556 | 0.374 | 0.364 [0.275, 0.441] | 0.619 | 1.000 | 0.500 | 0.200 | +0.167 |
| T1_typed_decisions_40 | typed-decisions | category | test | 4 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.119 | 0.291 [0.220, 0.378] | 0.709 | 1.000 | 0.500 | 0.200 | +0.500 |
| T1_typed_decisions_40 | typed-decisions | needs_human | all | 10 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.359 | 0.420 [0.387, 0.454] | 0.580 | 1.000 | 0.700 | 0.500 | +0.300 |
| T1_typed_decisions_40 | typed-decisions | needs_human | dev | 6 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.365 | 0.425 [0.387, 0.462] | 0.575 | 1.000 | 0.667 | 0.500 | +0.333 |
| T1_typed_decisions_40 | typed-decisions | needs_human | test | 4 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.350 | 0.413 [0.348, 0.467] | 0.587 | 1.000 | 0.750 | 0.500 | +0.250 |
| T1_typed_decisions_40 | typed-decisions | disposition | all | 20 | 0.850 [0.650, 1.000] | 0.653 | 0.653 | 0.442 | 0.369 [0.228, 0.496] | 0.481 | 1.000 | 0.450 | 0.250 | +0.400 |
| T1_typed_decisions_40 | typed-decisions | disposition | dev | 6 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.458 | 0.565 [0.518, 0.615] | 0.435 | 1.000 | 0.500 | 0.250 | +0.500 |
| T1_typed_decisions_40 | typed-decisions | disposition | test | 14 | 0.786 [0.571, 1.000] | 0.495 | 0.618 | 0.435 | 0.335 [0.225, 0.489] | 0.500 | 1.000 | 0.500 | 0.250 | +0.286 |
| T1_typed_decisions_40 | typed-decisions | duplicate | all | 10 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.033 | 0.128 [0.122, 0.134] | 0.872 | 1.000 | 1.000 | 0.500 | +0.000 |
| T1_typed_decisions_40 | typed-decisions | duplicate | dev | 3 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.033 | 0.128 [0.116, 0.136] | 0.872 | 1.000 | 1.000 | 0.500 | +0.000 |
| T1_typed_decisions_40 | typed-decisions | duplicate | test | 7 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.033 | 0.129 [0.120, 0.136] | 0.871 | 1.000 | 1.000 | 0.500 | +0.000 |
| T1_typed_decisions_40 | typed-decisions | matches_order | all | 10 | 0.900 [0.700, 1.000] | 0.867 | 0.867 | 0.116 | 0.193 [0.131, 0.292] | 0.831 | 1.000 | 0.800 | 0.500 | +0.100 |
| T1_typed_decisions_40 | typed-decisions | matches_order | dev | 3 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.050 | 0.150 [0.115, 0.219] | 0.850 | 1.000 | 1.000 | 0.500 | +0.000 |
| T1_typed_decisions_40 | typed-decisions | matches_order | test | 7 | 0.857 [0.571, 1.000] | 0.844 | 0.844 | 0.145 | 0.211 [0.131, 0.350] | 0.823 | 1.000 | 0.714 | 0.500 | +0.143 |
| T1_typed_decisions_40 | typed-decisions | credential_compromise | all | 10 | 0.900 [0.700, 1.000] | 0.899 | 0.899 | 0.345 | 0.311 [0.236, 0.433] | 0.593 | 1.000 | 0.600 | 0.500 | +0.300 |
| T1_typed_decisions_40 | typed-decisions | credential_compromise | dev | 3 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.317 | 0.388 [0.274, 0.490] | 0.612 | 1.000 | 1.000 | 0.500 | +0.000 |
| T1_typed_decisions_40 | typed-decisions | credential_compromise | test | 7 | 0.857 [0.571, 1.000] | 0.844 | 0.844 | 0.357 | 0.418 [0.377, 0.460] | 0.585 | 1.000 | 0.571 | 0.500 | +0.286 |
| T1_typed_decisions_40 | typed-decisions | true_positive | all | 10 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.290 | 0.379 [0.354, 0.405] | 0.621 | 1.000 | 0.600 | 0.500 | +0.400 |
| T1_typed_decisions_40 | typed-decisions | true_positive | dev | 3 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.296 | 0.382 [0.315, 0.422] | 0.618 | 1.000 | 0.667 | 0.500 | +0.333 |
| T1_typed_decisions_40 | typed-decisions | true_positive | test | 7 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.288 | 0.377 [0.349, 0.407] | 0.623 | 1.000 | 0.714 | 0.500 | +0.286 |
| T2_ag_news_40 | english | topic | all | 40 | 0.975 [0.925, 1.000] | 0.975 | 0.975 | 0.053 | 0.083 [0.046, 0.129] | 0.930 | 1.000 | 0.250 | 0.250 | +0.725 |
| T2_ag_news_40 | english | topic | dev | 16 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.007 | 0.046 [0.027, 0.069] | 0.954 | 1.000 | 0.500 | 0.250 | +0.500 |
| T2_ag_news_40 | english | topic | test | 24 | 0.958 [0.875, 1.000] | 0.958 | 0.958 | 0.083 | 0.107 [0.046, 0.185] | 0.915 | 1.000 | 0.375 | 0.250 | +0.583 |
| T2_ag_news_40 | multilingual | topic | all | 40 | 0.925 [0.825, 1.000] | 0.926 | 0.926 | 0.107 | 0.058 [0.006, 0.136] | 0.983 | 1.000 | 0.250 | 0.250 | +0.675 |
| T2_ag_news_40 | multilingual | topic | dev | 16 | 0.938 [0.812, 1.000] | 0.922 | 0.922 | 0.072 | 0.051 [0.001, 0.149] | 0.981 | 1.000 | 0.500 | 0.250 | +0.438 |
| T2_ag_news_40 | multilingual | topic | test | 24 | 0.917 [0.792, 1.000] | 0.930 | 0.930 | 0.131 | 0.067 [0.003, 0.174] | 0.984 | 1.000 | 0.375 | 0.250 | +0.542 |
| T2_ag_news_40 | router | topic | all | 40 | 0.975 [0.925, 1.000] | 0.975 | 0.975 | 0.053 | 0.083 [0.046, 0.129] | 0.930 | 1.000 | 0.250 | 0.250 | +0.725 |
| T2_ag_news_40 | router | topic | dev | 16 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.007 | 0.046 [0.027, 0.069] | 0.954 | 1.000 | 0.500 | 0.250 | +0.500 |
| T2_ag_news_40 | router | topic | test | 24 | 0.958 [0.875, 1.000] | 0.958 | 0.958 | 0.083 | 0.107 [0.046, 0.185] | 0.915 | 1.000 | 0.375 | 0.250 | +0.583 |
| T3_emotion_40 | english | emotion | all | 40 | 0.750 [0.600, 0.875] | 0.752 | 0.752 | 0.429 | 0.174 [0.087, 0.321] | 0.900 | 0.850 | 0.175 | 0.167 | +0.575 |
| T3_emotion_40 | english | emotion | dev | 24 | 0.708 [0.542, 0.875] | 0.726 | 0.726 | 0.483 | 0.221 [0.102, 0.400] | 0.895 | 0.917 | 0.208 | 0.167 | +0.500 |
| T3_emotion_40 | english | emotion | test | 16 | 0.812 [0.625, 1.000] | 0.748 | 0.748 | 0.349 | 0.169 [0.057, 0.364] | 0.909 | 0.875 | 0.312 | 0.167 | +0.500 |
| T3_emotion_40 | multilingual | emotion | all | 40 | 0.625 [0.475, 0.775] | 0.619 | 0.619 | 0.631 | 0.313 [0.184, 0.464] | 0.924 | 0.750 | 0.175 | 0.167 | +0.450 |
| T3_emotion_40 | multilingual | emotion | dev | 24 | 0.542 [0.333, 0.750] | 0.526 | 0.526 | 0.767 | 0.407 [0.234, 0.582] | 0.919 | 0.750 | 0.208 | 0.167 | +0.333 |
| T3_emotion_40 | multilingual | emotion | test | 16 | 0.750 [0.561, 0.938] | 0.755 | 0.755 | 0.426 | 0.182 [0.053, 0.402] | 0.932 | 0.875 | 0.312 | 0.167 | +0.438 |
| T3_emotion_40 | router | emotion | all | 40 | 0.750 [0.600, 0.875] | 0.752 | 0.752 | 0.429 | 0.174 [0.087, 0.321] | 0.900 | 0.850 | 0.175 | 0.167 | +0.575 |
| T3_emotion_40 | router | emotion | dev | 24 | 0.708 [0.542, 0.875] | 0.726 | 0.726 | 0.483 | 0.221 [0.102, 0.400] | 0.895 | 0.917 | 0.208 | 0.167 | +0.500 |
| T3_emotion_40 | router | emotion | test | 16 | 0.812 [0.625, 1.000] | 0.748 | 0.748 | 0.349 | 0.169 [0.057, 0.364] | 0.909 | 0.875 | 0.312 | 0.167 | +0.500 |
| T4_banking77_10opt_40 | english | intent | all | 40 | 0.725 [0.575, 0.850] | 0.636 | 0.700 | 0.349 | 0.150 [0.084, 0.263] | 0.860 | 0.950 | 0.025 | 0.100 | +0.700 |
| T4_banking77_10opt_40 | english | intent | dev | 18 | 0.611 [0.389, 0.833] | 0.478 | 0.611 | 0.435 | 0.199 [0.096, 0.337] | 0.776 | 0.889 | 0.056 | 0.100 | +0.556 |
| T4_banking77_10opt_40 | english | intent | test | 22 | 0.818 [0.636, 0.955] | 0.722 | 0.788 | 0.278 | 0.130 [0.040, 0.288] | 0.930 | 0.909 | 0.045 | 0.100 | +0.773 |
| T4_banking77_10opt_40 | multilingual | intent | all | 40 | 0.750 [0.600, 0.876] | 0.624 | 0.733 | 0.478 | 0.262 [0.177, 0.405] | 0.832 | 0.800 | 0.025 | 0.100 | +0.725 |
| T4_banking77_10opt_40 | multilingual | intent | dev | 18 | 0.667 [0.444, 0.889] | 0.507 | 0.648 | 0.681 | 0.440 [0.272, 0.620] | 0.825 | 0.556 | 0.056 | 0.100 | +0.611 |
| T4_banking77_10opt_40 | multilingual | intent | test | 22 | 0.818 [0.636, 0.955] | 0.707 | 0.803 | 0.311 | 0.188 [0.101, 0.343] | 0.839 | 0.818 | 0.045 | 0.100 | +0.773 |
| T4_banking77_10opt_40 | router | intent | all | 40 | 0.725 [0.575, 0.850] | 0.636 | 0.700 | 0.349 | 0.150 [0.084, 0.263] | 0.860 | 0.950 | 0.025 | 0.100 | +0.700 |
| T4_banking77_10opt_40 | router | intent | dev | 18 | 0.611 [0.389, 0.833] | 0.478 | 0.611 | 0.435 | 0.199 [0.096, 0.337] | 0.776 | 0.889 | 0.056 | 0.100 | +0.556 |
| T4_banking77_10opt_40 | router | intent | test | 22 | 0.818 [0.636, 0.955] | 0.722 | 0.788 | 0.278 | 0.130 [0.040, 0.288] | 0.930 | 0.909 | 0.045 | 0.100 | +0.773 |
| T5_boolq_40 | english | answer | all | 40 | 0.725 [0.575, 0.850] | 0.725 | 0.725 | 0.393 | 0.190 [0.095, 0.333] | 0.897 | 0.800 | 0.500 | 0.500 | +0.225 |
| T5_boolq_40 | english | answer | dev | 19 | 0.737 [0.526, 0.895] | 0.734 | 0.734 | 0.397 | 0.173 [0.074, 0.375] | 0.902 | 0.778 | 0.526 | 0.500 | +0.211 |
| T5_boolq_40 | english | answer | test | 21 | 0.714 [0.524, 0.905] | 0.714 | 0.714 | 0.389 | 0.206 [0.098, 0.383] | 0.893 | 0.800 | 0.524 | 0.500 | +0.190 |
| T5_boolq_40 | multilingual | answer | all | 40 | 0.600 [0.450, 0.750] | 0.599 | 0.599 | 0.615 | 0.294 [0.197, 0.460] | 0.870 | 0.750 | 0.500 | 0.500 | +0.100 |
| T5_boolq_40 | multilingual | answer | dev | 19 | 0.526 [0.316, 0.789] | 0.521 | 0.521 | 0.767 | 0.416 [0.243, 0.621] | 0.863 | 0.667 | 0.526 | 0.500 | +0.000 |
| T5_boolq_40 | multilingual | answer | test | 21 | 0.667 [0.476, 0.857] | 0.667 | 0.667 | 0.477 | 0.210 [0.086, 0.412] | 0.876 | 0.900 | 0.524 | 0.500 | +0.143 |
| T5_boolq_40 | router | answer | all | 40 | 0.725 [0.575, 0.850] | 0.725 | 0.725 | 0.393 | 0.190 [0.095, 0.333] | 0.897 | 0.800 | 0.500 | 0.500 | +0.225 |
| T5_boolq_40 | router | answer | dev | 19 | 0.737 [0.526, 0.895] | 0.734 | 0.734 | 0.397 | 0.173 [0.074, 0.375] | 0.902 | 0.778 | 0.526 | 0.500 | +0.211 |
| T5_boolq_40 | router | answer | test | 21 | 0.714 [0.524, 0.905] | 0.714 | 0.714 | 0.389 | 0.206 [0.098, 0.383] | 0.893 | 0.800 | 0.524 | 0.500 | +0.190 |
| T7_massive_intent_10opt_de_20 | english | intent | all | 20 | 0.350 [0.150, 0.551] | 0.295 | 0.406 | 1.046 | 0.513 [0.317, 0.691] | 0.848 | 0.500 | 0.150 | 0.100 | +0.200 |
| T7_massive_intent_10opt_de_20 | english | intent | dev | 12 | 0.417 [0.167, 0.667] | 0.275 | 0.424 | 1.000 | 0.474 [0.256, 0.731] | 0.865 | 0.500 | 0.167 | 0.100 | +0.250 |
| T7_massive_intent_10opt_de_20 | english | intent | test | 8 | 0.250 [0.000, 0.625] | 0.154 | 0.250 | 1.115 | 0.571 [0.315, 0.800] | 0.821 | 0.500 | 0.125 | 0.100 | +0.125 |
| T7_massive_intent_10opt_de_20 | multilingual | intent | all | 20 | 0.400 [0.200, 0.600] | 0.310 | 0.406 | 0.890 | 0.453 [0.296, 0.630] | 0.797 | 0.700 | 0.150 | 0.100 | +0.250 |
| T7_massive_intent_10opt_de_20 | multilingual | intent | dev | 12 | 0.500 [0.250, 0.750] | 0.333 | 0.455 | 0.670 | 0.353 [0.172, 0.543] | 0.760 | 0.833 | 0.167 | 0.100 | +0.333 |
| T7_massive_intent_10opt_de_20 | multilingual | intent | test | 8 | 0.250 [0.000, 0.503] | 0.139 | 0.208 | 1.220 | 0.603 [0.314, 0.852] | 0.853 | 0.500 | 0.125 | 0.100 | +0.125 |
| T7_massive_intent_10opt_de_20 | router | intent | all | 20 | 0.350 [0.150, 0.550] | 0.262 | 0.344 | 1.009 | 0.485 [0.321, 0.678] | 0.835 | 0.600 | 0.150 | 0.100 | +0.200 |
| T7_massive_intent_10opt_de_20 | router | intent | dev | 12 | 0.500 [0.250, 0.750] | 0.333 | 0.455 | 0.657 | 0.321 [0.150, 0.502] | 0.802 | 0.833 | 0.167 | 0.100 | +0.333 |
| T7_massive_intent_10opt_de_20 | router | intent | test | 8 | 0.125 [0.000, 0.375] | 0.056 | 0.083 | 1.536 | 0.760 [0.506, 0.955] | 0.885 | 0.250 | 0.125 | 0.100 | +0.000 |
| T7_massive_intent_10opt_en_20 | english | intent | all | 20 | 0.700 [0.500, 0.900] | 0.544 | 0.646 | 0.394 | 0.214 [0.088, 0.374] | 0.899 | 1.000 | 0.150 | 0.100 | +0.550 |
| T7_massive_intent_10opt_en_20 | english | intent | dev | 8 | 0.875 [0.625, 1.000] | 0.750 | 0.857 | 0.147 | 0.070 [0.003, 0.156] | 0.891 | 1.000 | 0.250 | 0.100 | +0.625 |
| T7_massive_intent_10opt_en_20 | english | intent | test | 12 | 0.583 [0.333, 0.833] | 0.444 | 0.533 | 0.559 | 0.321 [0.121, 0.547] | 0.904 | 1.000 | 0.167 | 0.100 | +0.417 |
| T7_massive_intent_10opt_en_20 | multilingual | intent | all | 20 | 0.850 [0.700, 1.000] | 0.748 | 0.842 | 0.293 | 0.184 [0.072, 0.330] | 0.895 | 0.900 | 0.150 | 0.100 | +0.700 |
| T7_massive_intent_10opt_en_20 | multilingual | intent | dev | 8 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.033 | 0.089 [0.011, 0.186] | 0.911 | 1.000 | 0.250 | 0.100 | +0.750 |
| T7_massive_intent_10opt_en_20 | multilingual | intent | test | 12 | 0.750 [0.500, 0.917] | 0.611 | 0.733 | 0.467 | 0.262 [0.086, 0.486] | 0.884 | 0.833 | 0.167 | 0.100 | +0.583 |
| T7_massive_intent_10opt_en_20 | router | intent | all | 20 | 0.700 [0.500, 0.900] | 0.544 | 0.646 | 0.394 | 0.214 [0.088, 0.374] | 0.899 | 1.000 | 0.150 | 0.100 | +0.550 |
| T7_massive_intent_10opt_en_20 | router | intent | dev | 8 | 0.875 [0.625, 1.000] | 0.750 | 0.857 | 0.147 | 0.070 [0.003, 0.156] | 0.891 | 1.000 | 0.250 | 0.100 | +0.625 |
| T7_massive_intent_10opt_en_20 | router | intent | test | 12 | 0.583 [0.333, 0.833] | 0.444 | 0.533 | 0.559 | 0.321 [0.121, 0.547] | 0.904 | 1.000 | 0.167 | 0.100 | +0.417 |
| T7_massive_intent_10opt_ja_20 | english | intent | all | 20 | 0.450 [0.250, 0.650] | 0.288 | 0.396 | 0.681 | 0.351 [0.227, 0.496] | 0.678 | 0.700 | 0.150 | 0.100 | +0.300 |
| T7_massive_intent_10opt_ja_20 | english | intent | dev | 7 | 0.571 [0.286, 0.857] | 0.400 | 0.571 | 0.618 | 0.325 [0.092, 0.599] | 0.808 | 0.667 | 0.143 | 0.100 | +0.429 |
| T7_massive_intent_10opt_ja_20 | english | intent | test | 13 | 0.385 [0.154, 0.615] | 0.157 | 0.267 | 0.715 | 0.381 [0.239, 0.522] | 0.608 | 0.500 | 0.231 | 0.100 | +0.154 |
| T7_massive_intent_10opt_ja_20 | multilingual | intent | all | 20 | 0.800 [0.600, 0.950] | 0.733 | 0.779 | 0.289 | 0.199 [0.092, 0.325] | 0.870 | 0.900 | 0.150 | 0.100 | +0.650 |
| T7_massive_intent_10opt_ja_20 | multilingual | intent | dev | 7 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.025 | 0.089 [0.022, 0.175] | 0.911 | 1.000 | 0.143 | 0.100 | +0.857 |
| T7_massive_intent_10opt_ja_20 | multilingual | intent | test | 13 | 0.692 [0.462, 0.923] | 0.567 | 0.680 | 0.431 | 0.260 [0.107, 0.428] | 0.847 | 0.833 | 0.231 | 0.100 | +0.462 |
| T7_massive_intent_10opt_ja_20 | router | intent | all | 20 | 0.800 [0.600, 0.950] | 0.733 | 0.779 | 0.289 | 0.199 [0.092, 0.325] | 0.870 | 0.900 | 0.150 | 0.100 | +0.650 |
| T7_massive_intent_10opt_ja_20 | router | intent | dev | 7 | 1.000 [1.000, 1.000] | 1.000 | 1.000 | 0.025 | 0.089 [0.022, 0.175] | 0.911 | 1.000 | 0.143 | 0.100 | +0.857 |
| T7_massive_intent_10opt_ja_20 | router | intent | test | 13 | 0.692 [0.462, 0.923] | 0.567 | 0.680 | 0.431 | 0.260 [0.107, 0.428] | 0.847 | 0.833 | 0.231 | 0.100 | +0.462 |
| T7_massive_intent_10opt_ko_20 | english | intent | all | 20 | 0.100 [0.000, 0.250] | 0.052 | 0.087 | 1.164 | 0.435 [0.327, 0.588] | 0.535 | 0.100 | 0.150 | 0.100 | -0.050 |
| T7_massive_intent_10opt_ko_20 | english | intent | dev | 10 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 1.302 | 0.561 [0.408, 0.726] | 0.561 | 0.000 | 0.100 | 0.100 | -0.100 |
| T7_massive_intent_10opt_ko_20 | english | intent | test | 10 | 0.200 [0.000, 0.500] | 0.108 | 0.175 | 1.025 | 0.440 [0.286, 0.581] | 0.509 | 0.200 | 0.300 | 0.100 | -0.100 |
| T7_massive_intent_10opt_ko_20 | multilingual | intent | all | 20 | 0.450 [0.250, 0.650] | 0.325 | 0.427 | 0.808 | 0.365 [0.232, 0.569] | 0.815 | 0.700 | 0.150 | 0.100 | +0.300 |
| T7_massive_intent_10opt_ko_20 | multilingual | intent | dev | 10 | 0.400 [0.100, 0.700] | 0.286 | 0.400 | 0.887 | 0.432 [0.202, 0.696] | 0.832 | 0.600 | 0.100 | 0.100 | +0.300 |
| T7_massive_intent_10opt_ko_20 | multilingual | intent | test | 10 | 0.500 [0.200, 0.800] | 0.348 | 0.479 | 0.729 | 0.387 [0.162, 0.610] | 0.799 | 0.800 | 0.300 | 0.100 | +0.200 |
| T7_massive_intent_10opt_ko_20 | router | intent | all | 20 | 0.450 [0.250, 0.650] | 0.325 | 0.427 | 0.808 | 0.365 [0.232, 0.569] | 0.815 | 0.700 | 0.150 | 0.100 | +0.300 |
| T7_massive_intent_10opt_ko_20 | router | intent | dev | 10 | 0.400 [0.100, 0.700] | 0.286 | 0.400 | 0.887 | 0.432 [0.202, 0.696] | 0.832 | 0.600 | 0.100 | 0.100 | +0.300 |
| T7_massive_intent_10opt_ko_20 | router | intent | test | 10 | 0.500 [0.200, 0.800] | 0.348 | 0.479 | 0.729 | 0.387 [0.162, 0.610] | 0.799 | 0.800 | 0.300 | 0.100 | +0.200 |
| T7_massive_intent_10opt_zh-CN_20 | english | intent | all | 20 | 0.450 [0.250, 0.650] | 0.297 | 0.408 | 0.886 | 0.414 [0.233, 0.608] | 0.864 | 0.700 | 0.150 | 0.100 | +0.300 |
| T7_massive_intent_10opt_zh-CN_20 | english | intent | dev | 10 | 0.600 [0.300, 0.900] | 0.385 | 0.556 | 0.631 | 0.314 [0.082, 0.572] | 0.890 | 0.800 | 0.200 | 0.100 | +0.400 |
| T7_massive_intent_10opt_zh-CN_20 | english | intent | test | 10 | 0.300 [0.000, 0.600] | 0.156 | 0.233 | 1.141 | 0.539 [0.290, 0.764] | 0.839 | 0.600 | 0.100 | 0.100 | +0.200 |
| T7_massive_intent_10opt_zh-CN_20 | multilingual | intent | all | 20 | 0.600 [0.400, 0.800] | 0.516 | 0.677 | 0.642 | 0.319 [0.193, 0.487] | 0.781 | 0.700 | 0.150 | 0.100 | +0.450 |
| T7_massive_intent_10opt_zh-CN_20 | multilingual | intent | dev | 10 | 0.400 [0.100, 0.700] | 0.286 | 0.444 | 0.918 | 0.446 [0.268, 0.659] | 0.723 | 0.400 | 0.200 | 0.100 | +0.200 |
| T7_massive_intent_10opt_zh-CN_20 | multilingual | intent | test | 10 | 0.800 [0.500, 1.000] | 0.667 | 0.800 | 0.367 | 0.217 [0.045, 0.427] | 0.840 | 1.000 | 0.100 | 0.100 | +0.700 |
| T7_massive_intent_10opt_zh-CN_20 | router | intent | all | 20 | 0.600 [0.400, 0.800] | 0.516 | 0.677 | 0.642 | 0.319 [0.193, 0.487] | 0.781 | 0.700 | 0.150 | 0.100 | +0.450 |
| T7_massive_intent_10opt_zh-CN_20 | router | intent | dev | 10 | 0.400 [0.100, 0.700] | 0.286 | 0.444 | 0.918 | 0.446 [0.268, 0.659] | 0.723 | 0.400 | 0.200 | 0.100 | +0.200 |
| T7_massive_intent_10opt_zh-CN_20 | router | intent | test | 10 | 0.800 [0.500, 1.000] | 0.667 | 0.800 | 0.367 | 0.217 [0.045, 0.427] | 0.840 | 1.000 | 0.100 | 0.100 | +0.700 |
| T8_prompt_injections_40 | english | injection | all | 40 | 0.775 [0.625, 0.900] | 0.763 | 0.763 | 0.401 | 0.223 [0.107, 0.355] | 0.962 | 0.900 | 0.500 | 0.500 | +0.275 |
| T8_prompt_injections_40 | english | injection | dev | 22 | 0.818 [0.636, 0.955] | 0.817 | 0.817 | 0.369 | 0.208 [0.066, 0.379] | 0.959 | 0.909 | 0.545 | 0.500 | +0.273 |
| T8_prompt_injections_40 | english | injection | test | 18 | 0.722 [0.500, 0.890] | 0.673 | 0.673 | 0.441 | 0.242 [0.070, 0.432] | 0.965 | 0.889 | 0.556 | 0.500 | +0.167 |
| T8_prompt_injections_40 | multilingual | injection | all | 40 | 0.575 [0.425, 0.700] | 0.540 | 0.540 | 0.692 | 0.380 [0.256, 0.520] | 0.940 | 0.750 | 0.500 | 0.500 | +0.075 |
| T8_prompt_injections_40 | multilingual | injection | dev | 22 | 0.545 [0.318, 0.727] | 0.509 | 0.509 | 0.760 | 0.420 [0.240, 0.621] | 0.939 | 0.727 | 0.545 | 0.500 | +0.000 |
| T8_prompt_injections_40 | multilingual | injection | test | 18 | 0.611 [0.389, 0.833] | 0.579 | 0.579 | 0.608 | 0.330 [0.145, 0.548] | 0.941 | 0.778 | 0.556 | 0.500 | +0.056 |
| T8_prompt_injections_40 | router | injection | all | 40 | 0.725 [0.575, 0.850] | 0.710 | 0.710 | 0.510 | 0.261 [0.142, 0.409] | 0.979 | 0.900 | 0.500 | 0.500 | +0.225 |
| T8_prompt_injections_40 | router | injection | dev | 22 | 0.636 [0.409, 0.818] | 0.624 | 0.624 | 0.663 | 0.346 [0.168, 0.545] | 0.970 | 0.818 | 0.545 | 0.500 | +0.091 |
| T8_prompt_injections_40 | router | injection | test | 18 | 0.833 [0.667, 1.000] | 0.819 | 0.819 | 0.323 | 0.157 [0.010, 0.328] | 0.991 | 0.889 | 0.556 | 0.500 | +0.278 |

## Per-class detail (split = all; dev/test in the JSON)

### T1_typed_decisions_40/english / action

- recall: answer_directly 0/2, continue 4/4, escalate_to_human 0/4, execute_refund 0/2, human_review 0/3, observe 0/3, request_information 0/2
- predicted: continue 10, close_no_action 10
- first listed option (most common: `continue`): gold 6, predicted 10
- top confusions: escalate_to_human→close_no_action ×4, observe→continue ×3, human_review→continue ×3, request_information→close_no_action ×2, answer_directly→close_no_action ×2
- answering model (cases): english 20

### T1_typed_decisions_40/english / needs_review

- recall: false 6/6, true 1/4
- predicted: false 9, true 1
- first listed option (most common: `true`): gold 4, predicted 1
- top confusions: true→false ×3
- answering model (cases): english 10

### T1_typed_decisions_40/english / outcome

- recall: failure 1/1, harmful 0/2, partial 0/3, success 2/4
- predicted: failure 6, success 4
- first listed option (most common: `failure`): gold 1, predicted 6
- top confusions: success→failure ×2, harmful→failure ×2, partial→success ×2, partial→failure ×1
- answering model (cases): english 10

### T1_typed_decisions_40/english / category

- recall: account 1/1, billing 2/4, delivery 1/4, technical 0/1
- predicted: refund 3, account 2, billing 2, technical 2, delivery 1
- first listed option (most common: `account`): gold 1, predicted 2
- top confusions: delivery→technical ×2, billing→account ×1, billing→refund ×1, technical→refund ×1, delivery→refund ×1
- answering model (cases): english 10

### T1_typed_decisions_40/english / needs_human

- recall: false 0/3, true 7/7
- predicted: true 10
- first listed option (most common: `true`): gold 7, predicted 10
- top confusions: false→true ×3
- answering model (cases): english 10

### T1_typed_decisions_40/english / disposition

- recall: approve 2/2, close_benign 1/1, hold 0/1, investigate 0/9, manual_review 0/7
- predicted: approve 10, close_benign 9, monitor 1
- first listed option (most common: `approve`): gold 3, predicted 19
- top confusions: investigate→close_benign ×8, manual_review→approve ×7, hold→approve ×1, investigate→monitor ×1
- answering model (cases): english 20

### T1_typed_decisions_40/english / duplicate

- recall: false 0/10
- predicted: true 10
- first listed option (most common: `true`): gold 0, predicted 10
- top confusions: false→true ×10
- answering model (cases): english 10

### T1_typed_decisions_40/english / matches_order

- recall: false 0/8, true 2/2
- predicted: true 10
- first listed option (most common: `true`): gold 2, predicted 10
- top confusions: false→true ×8
- answering model (cases): english 10

### T1_typed_decisions_40/english / credential_compromise

- recall: false 1/6, true 4/4
- predicted: true 9, false 1
- first listed option (most common: `true`): gold 4, predicted 9
- top confusions: false→true ×5
- answering model (cases): english 10

### T1_typed_decisions_40/english / true_positive

- recall: false 4/4, true 3/6
- predicted: false 7, true 3
- first listed option (most common: `true`): gold 6, predicted 3
- top confusions: true→false ×3
- answering model (cases): english 10

### T1_typed_decisions_40/english / action

- recall: answer_directly 0/2, continue 4/4, escalate_to_human 0/4, execute_refund 0/2, human_review 0/3, observe 0/3, request_information 0/2
- predicted: continue 10, close_no_action 10
- first listed option (most common: `continue`): gold 6, predicted 10
- top confusions: escalate_to_human→close_no_action ×4, observe→continue ×3, human_review→continue ×3, request_information→close_no_action ×2, answer_directly→close_no_action ×2
- answering model (cases): english 20

### T1_typed_decisions_40/english / needs_review

- recall: false 6/6, true 1/4
- predicted: false 9, true 1
- first listed option (most common: `true`): gold 4, predicted 1
- top confusions: true→false ×3
- answering model (cases): english 10

### T1_typed_decisions_40/english / outcome

- recall: failure 1/1, harmful 0/2, partial 0/3, success 2/4
- predicted: failure 6, success 4
- first listed option (most common: `failure`): gold 1, predicted 6
- top confusions: success→failure ×2, harmful→failure ×2, partial→success ×2, partial→failure ×1
- answering model (cases): english 10

### T1_typed_decisions_40/english / category

- recall: account 1/1, billing 2/4, delivery 1/4, technical 0/1
- predicted: refund 3, account 2, billing 2, technical 2, delivery 1
- first listed option (most common: `account`): gold 1, predicted 2
- top confusions: delivery→technical ×2, billing→account ×1, billing→refund ×1, technical→refund ×1, delivery→refund ×1
- answering model (cases): english 10

### T1_typed_decisions_40/english / needs_human

- recall: false 0/3, true 7/7
- predicted: true 10
- first listed option (most common: `true`): gold 7, predicted 10
- top confusions: false→true ×3
- answering model (cases): english 10

### T1_typed_decisions_40/english / disposition

- recall: approve 2/2, close_benign 1/1, hold 0/1, investigate 0/9, manual_review 0/7
- predicted: approve 10, close_benign 9, monitor 1
- first listed option (most common: `approve`): gold 3, predicted 19
- top confusions: investigate→close_benign ×8, manual_review→approve ×7, hold→approve ×1, investigate→monitor ×1
- answering model (cases): english 20

### T1_typed_decisions_40/english / duplicate

- recall: false 0/10
- predicted: true 10
- first listed option (most common: `true`): gold 0, predicted 10
- top confusions: false→true ×10
- answering model (cases): english 10

### T1_typed_decisions_40/english / matches_order

- recall: false 0/8, true 2/2
- predicted: true 10
- first listed option (most common: `true`): gold 2, predicted 10
- top confusions: false→true ×8
- answering model (cases): english 10

### T1_typed_decisions_40/english / credential_compromise

- recall: false 1/6, true 4/4
- predicted: true 9, false 1
- first listed option (most common: `true`): gold 4, predicted 9
- top confusions: false→true ×5
- answering model (cases): english 10

### T1_typed_decisions_40/english / true_positive

- recall: false 4/4, true 3/6
- predicted: false 7, true 3
- first listed option (most common: `true`): gold 6, predicted 3
- top confusions: true→false ×3
- answering model (cases): english 10

### T1_typed_decisions_40/multilingual / action

- recall: answer_directly 1/2, continue 2/4, escalate_to_human 0/4, execute_refund 1/2, human_review 0/3, observe 0/3, request_information 0/2
- predicted: stop 8, close_no_action 4, execute_refund 3, answer_directly 3, continue 2
- first listed option (most common: `continue`): gold 6, predicted 5
- top confusions: observe→stop ×3, human_review→stop ×3, continue→stop ×2, escalate_to_human→close_no_action ×2, request_information→close_no_action ×1
- answering model (cases): multilingual 20

### T1_typed_decisions_40/multilingual / needs_review

- recall: false 5/6, true 1/4
- predicted: false 8, true 2
- first listed option (most common: `true`): gold 4, predicted 2
- top confusions: true→false ×3, false→true ×1
- answering model (cases): multilingual 10

### T1_typed_decisions_40/multilingual / outcome

- recall: failure 0/1, harmful 0/2, partial 0/3, success 3/4
- predicted: success 7, failure 3
- first listed option (most common: `failure`): gold 1, predicted 3
- top confusions: partial→success ×2, harmful→failure ×1, harmful→success ×1, failure→success ×1, success→failure ×1
- answering model (cases): multilingual 10

### T1_typed_decisions_40/multilingual / category

- recall: account 0/1, billing 3/4, delivery 4/4, technical 1/1
- predicted: billing 4, delivery 4, account 1, technical 1
- first listed option (most common: `account`): gold 1, predicted 1
- top confusions: billing→account ×1, account→billing ×1
- answering model (cases): multilingual 10

### T1_typed_decisions_40/multilingual / needs_human

- recall: false 1/3, true 3/7
- predicted: false 5, true 5
- first listed option (most common: `true`): gold 7, predicted 5
- top confusions: true→false ×4, false→true ×2
- answering model (cases): multilingual 10

### T1_typed_decisions_40/multilingual / disposition

- recall: approve 2/2, close_benign 0/1, hold 0/1, investigate 1/9, manual_review 0/7
- predicted: monitor 7, approve 6, reject 4, contain 2, investigate 1
- first listed option (most common: `approve`): gold 3, predicted 6
- top confusions: investigate→monitor ×6, manual_review→reject ×4, manual_review→approve ×3, investigate→contain ×2, hold→approve ×1
- answering model (cases): multilingual 20

### T1_typed_decisions_40/multilingual / duplicate

- recall: false 0/10
- predicted: true 10
- first listed option (most common: `true`): gold 0, predicted 10
- top confusions: false→true ×10
- answering model (cases): multilingual 10

### T1_typed_decisions_40/multilingual / matches_order

- recall: false 0/8, true 2/2
- predicted: true 10
- first listed option (most common: `true`): gold 2, predicted 10
- top confusions: false→true ×8
- answering model (cases): multilingual 10

### T1_typed_decisions_40/multilingual / credential_compromise

- recall: false 4/6, true 4/4
- predicted: true 6, false 4
- first listed option (most common: `true`): gold 4, predicted 6
- top confusions: false→true ×2
- answering model (cases): multilingual 10

### T1_typed_decisions_40/multilingual / true_positive

- recall: false 1/4, true 5/6
- predicted: true 8, false 2
- first listed option (most common: `true`): gold 6, predicted 8
- top confusions: false→true ×3, true→false ×1
- answering model (cases): multilingual 10

### T1_typed_decisions_40_noulnocrit/english / needs_review

- recall: false 6/6, true 0/4
- predicted: false 10
- first listed option (most common: `true`): gold 4, predicted 0
- top confusions: true→false ×4
- answering model (cases): english 10

### T1_typed_decisions_40_noulnocrit/english / needs_human

- recall: false 0/3, true 7/7
- predicted: true 10
- first listed option (most common: `true`): gold 7, predicted 10
- top confusions: false→true ×3
- answering model (cases): english 10

### T1_typed_decisions_40_noulnocrit/english / duplicate

- recall: false 0/10
- predicted: true 10
- first listed option (most common: `true`): gold 0, predicted 10
- top confusions: false→true ×10
- answering model (cases): english 10

### T1_typed_decisions_40_noulnocrit/english / matches_order

- recall: false 7/8, true 0/2
- predicted: false 9, true 1
- first listed option (most common: `true`): gold 2, predicted 1
- top confusions: true→false ×2, false→true ×1
- answering model (cases): english 10

### T1_typed_decisions_40_noulnocrit/english / credential_compromise

- recall: false 1/6, true 4/4
- predicted: true 9, false 1
- first listed option (most common: `true`): gold 4, predicted 9
- top confusions: false→true ×5
- answering model (cases): english 10

### T1_typed_decisions_40_noulnocrit/english / true_positive

- recall: false 4/4, true 2/6
- predicted: false 8, true 2
- first listed option (most common: `true`): gold 6, predicted 2
- top confusions: true→false ×4
- answering model (cases): english 10

### T1_typed_decisions_40_noulnocrit/multilingual / needs_review

- recall: false 3/6, true 1/4
- predicted: false 6, true 4
- first listed option (most common: `true`): gold 4, predicted 4
- top confusions: false→true ×3, true→false ×3
- answering model (cases): multilingual 10

### T1_typed_decisions_40_noulnocrit/multilingual / needs_human

- recall: false 1/3, true 4/7
- predicted: true 6, false 4
- first listed option (most common: `true`): gold 7, predicted 6
- top confusions: true→false ×3, false→true ×2
- answering model (cases): multilingual 10

### T1_typed_decisions_40_noulnocrit/multilingual / duplicate

- recall: false 0/10
- predicted: true 10
- first listed option (most common: `true`): gold 0, predicted 10
- top confusions: false→true ×10
- answering model (cases): multilingual 10

### T1_typed_decisions_40_noulnocrit/multilingual / matches_order

- recall: false 0/8, true 2/2
- predicted: true 10
- first listed option (most common: `true`): gold 2, predicted 10
- top confusions: false→true ×8
- answering model (cases): multilingual 10

### T1_typed_decisions_40_noulnocrit/multilingual / credential_compromise

- recall: false 4/6, true 4/4
- predicted: true 6, false 4
- first listed option (most common: `true`): gold 4, predicted 6
- top confusions: false→true ×2
- answering model (cases): multilingual 10

### T1_typed_decisions_40_noulnocrit/multilingual / true_positive

- recall: false 2/4, true 4/6
- predicted: true 6, false 4
- first listed option (most common: `true`): gold 6, predicted 6
- top confusions: true→false ×2, false→true ×2
- answering model (cases): multilingual 10

### T1_typed_decisions_40/router / action

- recall: answer_directly 0/2, continue 4/4, escalate_to_human 0/4, execute_refund 0/2, human_review 0/3, observe 0/3, request_information 0/2
- predicted: continue 10, close_no_action 10
- first listed option (most common: `continue`): gold 6, predicted 10
- top confusions: escalate_to_human→close_no_action ×4, observe→continue ×3, human_review→continue ×3, request_information→close_no_action ×2, answer_directly→close_no_action ×2
- answering model (cases): english 20

### T1_typed_decisions_40/router / needs_review

- recall: false 6/6, true 1/4
- predicted: false 9, true 1
- first listed option (most common: `true`): gold 4, predicted 1
- top confusions: true→false ×3
- answering model (cases): english 10

### T1_typed_decisions_40/router / outcome

- recall: failure 1/1, harmful 0/2, partial 0/3, success 2/4
- predicted: failure 6, success 4
- first listed option (most common: `failure`): gold 1, predicted 6
- top confusions: success→failure ×2, harmful→failure ×2, partial→success ×2, partial→failure ×1
- answering model (cases): english 10

### T1_typed_decisions_40/router / category

- recall: account 1/1, billing 2/4, delivery 1/4, technical 0/1
- predicted: refund 3, account 2, billing 2, technical 2, delivery 1
- first listed option (most common: `account`): gold 1, predicted 2
- top confusions: delivery→technical ×2, billing→account ×1, billing→refund ×1, technical→refund ×1, delivery→refund ×1
- answering model (cases): english 10

### T1_typed_decisions_40/router / needs_human

- recall: false 0/3, true 7/7
- predicted: true 10
- first listed option (most common: `true`): gold 7, predicted 10
- top confusions: false→true ×3
- answering model (cases): english 10

### T1_typed_decisions_40/router / disposition

- recall: approve 2/2, close_benign 1/1, hold 0/1, investigate 0/9, manual_review 0/7
- predicted: approve 10, close_benign 9, monitor 1
- first listed option (most common: `approve`): gold 3, predicted 19
- top confusions: investigate→close_benign ×8, manual_review→approve ×7, hold→approve ×1, investigate→monitor ×1
- answering model (cases): english 20

### T1_typed_decisions_40/router / duplicate

- recall: false 0/10
- predicted: true 10
- first listed option (most common: `true`): gold 0, predicted 10
- top confusions: false→true ×10
- answering model (cases): english 10

### T1_typed_decisions_40/router / matches_order

- recall: false 0/8, true 2/2
- predicted: true 10
- first listed option (most common: `true`): gold 2, predicted 10
- top confusions: false→true ×8
- answering model (cases): english 10

### T1_typed_decisions_40/router / credential_compromise

- recall: false 1/6, true 4/4
- predicted: true 9, false 1
- first listed option (most common: `true`): gold 4, predicted 9
- top confusions: false→true ×5
- answering model (cases): english 10

### T1_typed_decisions_40/router / true_positive

- recall: false 4/4, true 3/6
- predicted: false 7, true 3
- first listed option (most common: `true`): gold 6, predicted 3
- top confusions: true→false ×3
- answering model (cases): english 10

### T1_typed_decisions_40/typed-decisions / action

- recall: answer_directly 1/2, continue 3/4, escalate_to_human 4/4, execute_refund 0/2, human_review 2/3, observe 2/3, request_information 0/2
- predicted: escalate_to_human 8, observe 4, continue 3, human_review 3, answer_directly 1, request_information 1
- first listed option (most common: `continue`): gold 6, predicted 4
- top confusions: request_information→escalate_to_human ×2, observe→human_review ×1, human_review→observe ×1, continue→observe ×1, execute_refund→request_information ×1
- answering model (cases): typed-decisions 20

### T1_typed_decisions_40/typed-decisions / needs_review

- recall: false 6/6, true 3/4
- predicted: false 7, true 3
- first listed option (most common: `true`): gold 4, predicted 3
- top confusions: true→false ×1
- answering model (cases): typed-decisions 10

### T1_typed_decisions_40/typed-decisions / outcome

- recall: failure 0/1, harmful 2/2, partial 3/3, success 3/4
- predicted: partial 5, success 3, harmful 2
- first listed option (most common: `failure`): gold 1, predicted 0
- top confusions: failure→partial ×1, success→partial ×1
- answering model (cases): typed-decisions 10

### T1_typed_decisions_40/typed-decisions / category

- recall: account 0/1, billing 3/4, delivery 4/4, technical 1/1
- predicted: billing 4, delivery 4, technical 2
- first listed option (most common: `account`): gold 1, predicted 0
- top confusions: billing→technical ×1, account→billing ×1
- answering model (cases): typed-decisions 10

### T1_typed_decisions_40/typed-decisions / needs_human

- recall: false 3/3, true 7/7
- predicted: true 7, false 3
- first listed option (most common: `true`): gold 7, predicted 7
- top confusions: 
- answering model (cases): typed-decisions 10

### T1_typed_decisions_40/typed-decisions / disposition

- recall: approve 2/2, close_benign 1/1, hold 0/1, investigate 8/9, manual_review 6/7
- predicted: investigate 8, manual_review 7, approve 3, close_benign 2
- first listed option (most common: `approve`): gold 3, predicted 5
- top confusions: manual_review→approve ×1, hold→manual_review ×1, investigate→close_benign ×1
- answering model (cases): typed-decisions 20

### T1_typed_decisions_40/typed-decisions / duplicate

- recall: false 10/10
- predicted: false 10
- first listed option (most common: `true`): gold 0, predicted 0
- top confusions: 
- answering model (cases): typed-decisions 10

### T1_typed_decisions_40/typed-decisions / matches_order

- recall: false 7/8, true 2/2
- predicted: false 7, true 3
- first listed option (most common: `true`): gold 2, predicted 3
- top confusions: false→true ×1
- answering model (cases): typed-decisions 10

### T1_typed_decisions_40/typed-decisions / credential_compromise

- recall: false 5/6, true 4/4
- predicted: true 5, false 5
- first listed option (most common: `true`): gold 4, predicted 5
- top confusions: false→true ×1
- answering model (cases): typed-decisions 10

### T1_typed_decisions_40/typed-decisions / true_positive

- recall: false 4/4, true 6/6
- predicted: true 6, false 4
- first listed option (most common: `true`): gold 6, predicted 6
- top confusions: 
- answering model (cases): typed-decisions 10

### T2_ag_news_40/english / topic

- recall: business 10/10, sci_tech 10/10, sports 10/10, world 9/10
- predicted: business 11, sci_tech 10, sports 10, world 9
- first listed option (most common: `world`): gold 10, predicted 9
- top confusions: world→business ×1
- answering model (cases): english 40

### T2_ag_news_40/multilingual / topic

- recall: business 10/10, sci_tech 9/10, sports 10/10, world 8/10
- predicted: business 13, sports 10, sci_tech 9, world 8
- first listed option (most common: `world`): gold 10, predicted 8
- top confusions: world→business ×2, sci_tech→business ×1
- answering model (cases): multilingual 40

### T2_ag_news_40/router / topic

- recall: business 10/10, sci_tech 10/10, sports 10/10, world 9/10
- predicted: business 11, sci_tech 10, sports 10, world 9
- first listed option (most common: `world`): gold 10, predicted 9
- top confusions: world→business ×1
- answering model (cases): english 40

### T3_emotion_40/english / emotion

- recall: anger 6/7, fear 4/6, joy 7/7, love 3/7, sadness 6/7, surprise 4/6
- predicted: sadness 12, joy 10, anger 7, surprise 4, fear 4, love 3
- first listed option (most common: `sadness`): gold 7, predicted 12
- top confusions: love→joy ×3, fear→sadness ×2, surprise→sadness ×2, love→sadness ×1, sadness→anger ×1
- answering model (cases): english 40

### T3_emotion_40/multilingual / emotion

- recall: anger 4/7, fear 3/6, joy 5/7, love 4/7, sadness 6/7, surprise 3/6
- predicted: sadness 11, joy 8, love 7, anger 5, fear 5, surprise 4
- first listed option (most common: `sadness`): gold 7, predicted 11
- top confusions: love→joy ×3, fear→sadness ×3, joy→surprise ×1, sadness→love ×1, surprise→fear ×1
- answering model (cases): multilingual 40

### T3_emotion_40/router / emotion

- recall: anger 6/7, fear 4/6, joy 7/7, love 3/7, sadness 6/7, surprise 4/6
- predicted: sadness 12, joy 10, anger 7, surprise 4, fear 4, love 3
- first listed option (most common: `sadness`): gold 7, predicted 12
- top confusions: love→joy ×3, fear→sadness ×2, surprise→sadness ×2, love→sadness ×1, sadness→anger ×1
- answering model (cases): english 40

### T4_banking77_10opt_40/english / intent

- recall: activate my card 1/1, age limit 1/1, atm support 1/1, balance not updated after bank transfer 1/1, balance not updated after cheque or cash deposit 0/1, card about to expire 1/1, card acceptance 0/1, card arrival 1/1, card delivery estimate 1/1, card not working 1/1, card swallowed 0/1, cash withdrawal charge 1/1, cash withdrawal not recognised 0/1, contactless not working 1/1, country support 1/1, declined card payment 1/1, disposable card limits 1/1, exchange charge 1/1, exchange via app 1/1, get physical card 0/1, getting spare card 1/1, getting virtual card 0/1, lost or stolen card 0/1, order physical card 1/1, passcode forgotten 1/1, pending card payment 1/1, pending transfer 1/1, supported cards and currencies 1/1, top up by bank transfer charge 0/1, top up by cash or cheque 1/1, top up failed 1/1, top up limits 1/1, top up reverted 1/1, transfer fee charged 0/1, transfer into account 1/1, transfer not received by recipient 0/1, verify source of funds 1/1, virtual card not working 1/1, visa or mastercard 1/1, wrong exchange rate for cash withdrawal 0/1
- predicted: lost or stolen card 2, country support 2, top up by cash or cheque 2, cash withdrawal charge 2, card arrival 1, card delivery estimate 1, card not working 1, exchange via app 1, reverted card payment? 1, age limit 1, contactless not working 1, transfer fee charged 1, top up limits 1, supported cards and currencies 1, top up reverted 1, verify my identity 1, visa or mastercard 1, disposable card limits 1, atm support 1, passcode forgotten 1, pending card payment 1, declined card payment 1, pending transfer 1, verify source of funds 1, wrong amount of cash received 1, transfer into account 1, getting spare card 1, order physical card 1, virtual card not working 1, card acceptance 1, top up failed 1, balance not updated after bank transfer 1, declined cash withdrawal 1, exchange charge 1, activate my card 1, card about to expire 1
- first listed option (most common: `visa or mastercard`): gold 2, predicted 3
- top confusions: lost or stolen card→reverted card payment? ×1, top up by bank transfer charge→transfer fee charged ×1, transfer not received by recipient→lost or stolen card ×1, getting virtual card→lost or stolen card ×1, card acceptance→country support ×1
- answering model (cases): english 40

### T4_banking77_10opt_40/multilingual / intent

- recall: activate my card 1/1, age limit 1/1, atm support 1/1, balance not updated after bank transfer 1/1, balance not updated after cheque or cash deposit 0/1, card about to expire 1/1, card acceptance 0/1, card arrival 1/1, card delivery estimate 1/1, card not working 1/1, card swallowed 1/1, cash withdrawal charge 1/1, cash withdrawal not recognised 0/1, contactless not working 1/1, country support 0/1, declined card payment 0/1, disposable card limits 1/1, exchange charge 1/1, exchange via app 1/1, get physical card 0/1, getting spare card 1/1, getting virtual card 1/1, lost or stolen card 0/1, order physical card 1/1, passcode forgotten 1/1, pending card payment 1/1, pending transfer 1/1, supported cards and currencies 1/1, top up by bank transfer charge 0/1, top up by cash or cheque 1/1, top up failed 1/1, top up limits 1/1, top up reverted 1/1, transfer fee charged 0/1, transfer into account 1/1, transfer not received by recipient 1/1, verify source of funds 1/1, virtual card not working 1/1, visa or mastercard 1/1, wrong exchange rate for cash withdrawal 0/1
- predicted: card delivery estimate 2, card not working 2, card arrival 1, exchange via app 1, verify top up 1, age limit 1, contactless not working 1, transfer fee charged 1, top up limits 1, transfer not received by recipient 1, supported cards and currencies 1, getting virtual card 1, top up reverted 1, pin blocked 1, verify my identity 1, visa or mastercard 1, disposable card limits 1, atm support 1, passcode forgotten 1, pending card payment 1, declined transfer 1, pending transfer 1, card swallowed 1, verify source of funds 1, wrong amount of cash received 1, transfer into account 1, getting spare card 1, top up by cash or cheque 1, order physical card 1, virtual card not working 1, receiving money 1, top up failed 1, balance not updated after bank transfer 1, declined cash withdrawal 1, exchange charge 1, activate my card 1, cash withdrawal charge 1, card about to expire 1
- first listed option (most common: `visa or mastercard`): gold 2, predicted 1
- top confusions: lost or stolen card→verify top up ×1, top up by bank transfer charge→transfer fee charged ×1, card acceptance→card not working ×1, balance not updated after cheque or cash deposit→pin blocked ×1, get physical card→verify my identity ×1
- answering model (cases): multilingual 40

### T4_banking77_10opt_40/router / intent

- recall: activate my card 1/1, age limit 1/1, atm support 1/1, balance not updated after bank transfer 1/1, balance not updated after cheque or cash deposit 0/1, card about to expire 1/1, card acceptance 0/1, card arrival 1/1, card delivery estimate 1/1, card not working 1/1, card swallowed 0/1, cash withdrawal charge 1/1, cash withdrawal not recognised 0/1, contactless not working 1/1, country support 1/1, declined card payment 1/1, disposable card limits 1/1, exchange charge 1/1, exchange via app 1/1, get physical card 0/1, getting spare card 1/1, getting virtual card 0/1, lost or stolen card 0/1, order physical card 1/1, passcode forgotten 1/1, pending card payment 1/1, pending transfer 1/1, supported cards and currencies 1/1, top up by bank transfer charge 0/1, top up by cash or cheque 1/1, top up failed 1/1, top up limits 1/1, top up reverted 1/1, transfer fee charged 0/1, transfer into account 1/1, transfer not received by recipient 0/1, verify source of funds 1/1, virtual card not working 1/1, visa or mastercard 1/1, wrong exchange rate for cash withdrawal 0/1
- predicted: lost or stolen card 2, country support 2, top up by cash or cheque 2, cash withdrawal charge 2, card arrival 1, card delivery estimate 1, card not working 1, exchange via app 1, reverted card payment? 1, age limit 1, contactless not working 1, transfer fee charged 1, top up limits 1, supported cards and currencies 1, top up reverted 1, verify my identity 1, visa or mastercard 1, disposable card limits 1, atm support 1, passcode forgotten 1, pending card payment 1, declined card payment 1, pending transfer 1, verify source of funds 1, wrong amount of cash received 1, transfer into account 1, getting spare card 1, order physical card 1, virtual card not working 1, card acceptance 1, top up failed 1, balance not updated after bank transfer 1, declined cash withdrawal 1, exchange charge 1, activate my card 1, card about to expire 1
- first listed option (most common: `visa or mastercard`): gold 2, predicted 3
- top confusions: lost or stolen card→reverted card payment? ×1, top up by bank transfer charge→transfer fee charged ×1, transfer not received by recipient→lost or stolen card ×1, getting virtual card→lost or stolen card ×1, card acceptance→country support ×1
- answering model (cases): english 40

### T5_boolq_40/english / answer

- recall: false 15/20, true 14/20
- predicted: false 21, true 19
- first listed option (most common: `true`): gold 20, predicted 19
- top confusions: true→false ×6, false→true ×5
- answering model (cases): english 40

### T5_boolq_40/multilingual / answer

- recall: false 13/20, true 11/20
- predicted: false 22, true 18
- first listed option (most common: `true`): gold 20, predicted 18
- top confusions: true→false ×9, false→true ×7
- answering model (cases): multilingual 40

### T5_boolq_40/router / answer

- recall: false 15/20, true 14/20
- predicted: false 21, true 19
- first listed option (most common: `true`): gold 20, predicted 19
- top confusions: true→false ×6, false→true ×5
- answering model (cases): english 40

### T7_massive_intent_10opt_de_20/english / intent

- recall: alarm_query 0/2, alarm_remove 1/1, alarm_set 1/1, audio_volume_mute 0/1, datetime_convert 1/1, datetime_query 1/3, general_greet 0/1, general_quirky 0/1, iot_cleaning 0/2, iot_hue_lightchange 0/1, iot_hue_lightoff 0/1, iot_hue_lighton 0/1, iot_hue_lightup 0/1, music_likeness 1/1, takeaway_order 1/1, weather_query 1/1
- predicted: general_joke 3, iot_hue_lightdim 2, general_quirky 2, alarm_set 1, iot_hue_lightoff 1, qa_factoid 1, music_dislikeness 1, qa_definition 1, audio_volume_mute 1, datetime_convert 1, alarm_remove 1, iot_coffee 1, music_likeness 1, datetime_query 1, takeaway_order 1, weather_query 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 2
- top confusions: audio_volume_mute→general_joke ×1, iot_hue_lightchange→iot_hue_lightoff ×1, iot_hue_lighton→qa_factoid ×1, iot_hue_lightoff→iot_hue_lightdim ×1, iot_cleaning→music_dislikeness ×1
- answering model (cases): english 20

### T7_massive_intent_10opt_de_20/multilingual / intent

- recall: alarm_query 0/2, alarm_remove 1/1, alarm_set 1/1, audio_volume_mute 0/1, datetime_convert 0/1, datetime_query 1/3, general_greet 1/1, general_quirky 0/1, iot_cleaning 0/2, iot_hue_lightchange 1/1, iot_hue_lightoff 0/1, iot_hue_lighton 1/1, iot_hue_lightup 1/1, music_likeness 0/1, takeaway_order 0/1, weather_query 1/1
- predicted: alarm_set 2, iot_hue_lighton 2, iot_hue_lightdim 2, takeaway_order 2, weather_query 2, general_joke 1, iot_hue_lightchange 1, play_radio 1, play_music 1, audio_volume_mute 1, general_greet 1, alarm_remove 1, iot_hue_lightup 1, datetime_query 1, cooking_recipe 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 3
- top confusions: audio_volume_mute→general_joke ×1, iot_hue_lightoff→iot_hue_lightdim ×1, iot_cleaning→play_radio ×1, iot_cleaning→play_music ×1, general_quirky→audio_volume_mute ×1
- answering model (cases): multilingual 20

### T7_massive_intent_10opt_de_20/router / intent

- recall: alarm_query 0/2, alarm_remove 1/1, alarm_set 1/1, audio_volume_mute 0/1, datetime_convert 0/1, datetime_query 1/3, general_greet 0/1, general_quirky 0/1, iot_cleaning 0/2, iot_hue_lightchange 0/1, iot_hue_lightoff 0/1, iot_hue_lighton 1/1, iot_hue_lightup 1/1, music_likeness 1/1, takeaway_order 0/1, weather_query 1/1
- predicted: alarm_set 2, general_joke 2, iot_hue_lighton 2, iot_hue_lightdim 2, weather_query 2, iot_hue_lightoff 1, play_radio 1, qa_definition 1, audio_volume_mute 1, alarm_remove 1, takeaway_order 1, music_likeness 1, iot_hue_lightup 1, datetime_query 1, cooking_recipe 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 3
- top confusions: audio_volume_mute→general_joke ×1, iot_hue_lightchange→iot_hue_lightoff ×1, iot_hue_lightoff→iot_hue_lightdim ×1, iot_cleaning→play_radio ×1, iot_cleaning→qa_definition ×1
- answering model (cases): multilingual 15, english 5

### T7_massive_intent_10opt_en_20/english / intent

- recall: alarm_query 2/2, alarm_remove 1/1, alarm_set 1/1, audio_volume_mute 0/1, datetime_convert 1/1, datetime_query 3/3, general_greet 1/1, general_quirky 0/1, iot_cleaning 1/2, iot_hue_lightchange 0/1, iot_hue_lightoff 1/1, iot_hue_lighton 0/1, iot_hue_lightup 0/1, music_likeness 1/1, takeaway_order 1/1, weather_query 1/1
- predicted: datetime_query 3, alarm_remove 2, music_dislikeness 2, alarm_query 2, alarm_set 1, music_settings 1, iot_hue_lightoff 1, iot_cleaning 1, audio_volume_mute 1, general_greet 1, datetime_convert 1, music_likeness 1, iot_hue_lightdim 1, takeaway_order 1, weather_query 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 1
- top confusions: audio_volume_mute→alarm_remove ×1, iot_hue_lightchange→music_dislikeness ×1, iot_hue_lighton→music_settings ×1, iot_cleaning→music_dislikeness ×1, general_quirky→audio_volume_mute ×1
- answering model (cases): english 20

### T7_massive_intent_10opt_en_20/multilingual / intent

- recall: alarm_query 2/2, alarm_remove 1/1, alarm_set 1/1, audio_volume_mute 1/1, datetime_convert 0/1, datetime_query 2/3, general_greet 1/1, general_quirky 1/1, iot_cleaning 2/2, iot_hue_lightchange 1/1, iot_hue_lightoff 1/1, iot_hue_lighton 1/1, iot_hue_lightup 0/1, music_likeness 1/1, takeaway_order 1/1, weather_query 1/1
- predicted: iot_cleaning 2, general_quirky 2, alarm_query 2, datetime_query 2, alarm_set 1, audio_volume_mute 1, iot_hue_lightchange 1, iot_hue_lighton 1, iot_hue_lightoff 1, general_greet 1, iot_wemo_on 1, alarm_remove 1, music_likeness 1, iot_hue_lightdim 1, takeaway_order 1, weather_query 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 2
- top confusions: datetime_query→general_quirky ×1, datetime_convert→iot_wemo_on ×1, iot_hue_lightup→iot_hue_lightdim ×1
- answering model (cases): multilingual 20

### T7_massive_intent_10opt_en_20/router / intent

- recall: alarm_query 2/2, alarm_remove 1/1, alarm_set 1/1, audio_volume_mute 0/1, datetime_convert 1/1, datetime_query 3/3, general_greet 1/1, general_quirky 0/1, iot_cleaning 1/2, iot_hue_lightchange 0/1, iot_hue_lightoff 1/1, iot_hue_lighton 0/1, iot_hue_lightup 0/1, music_likeness 1/1, takeaway_order 1/1, weather_query 1/1
- predicted: datetime_query 3, alarm_remove 2, music_dislikeness 2, alarm_query 2, alarm_set 1, music_settings 1, iot_hue_lightoff 1, iot_cleaning 1, audio_volume_mute 1, general_greet 1, datetime_convert 1, music_likeness 1, iot_hue_lightdim 1, takeaway_order 1, weather_query 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 1
- top confusions: audio_volume_mute→alarm_remove ×1, iot_hue_lightchange→music_dislikeness ×1, iot_hue_lighton→music_settings ×1, iot_cleaning→music_dislikeness ×1, general_quirky→audio_volume_mute ×1
- answering model (cases): english 20

### T7_massive_intent_10opt_ja_20/english / intent

- recall: alarm_query 2/2, alarm_remove 1/1, alarm_set 0/1, audio_volume_mute 0/1, datetime_convert 1/1, datetime_query 2/3, general_greet 1/1, general_quirky 0/1, iot_cleaning 1/2, iot_hue_lightchange 0/1, iot_hue_lightoff 0/1, iot_hue_lighton 0/1, iot_hue_lightup 0/1, music_likeness 1/1, takeaway_order 0/1, weather_query 0/1
- predicted: datetime_query 3, general_joke 2, music_dislikeness 2, alarm_query 2, play_music 1, recommendation_movies 1, iot_cleaning 1, audio_volume_mute 1, general_greet 1, datetime_convert 1, alarm_remove 1, music_likeness 1, iot_hue_lighton 1, lists_query 1, news_query 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 1
- top confusions: alarm_set→datetime_query ×1, audio_volume_mute→play_music ×1, iot_hue_lightchange→recommendation_movies ×1, iot_hue_lighton→general_joke ×1, iot_hue_lightoff→music_dislikeness ×1
- answering model (cases): english 20

### T7_massive_intent_10opt_ja_20/multilingual / intent

- recall: alarm_query 2/2, alarm_remove 1/1, alarm_set 1/1, audio_volume_mute 1/1, datetime_convert 1/1, datetime_query 2/3, general_greet 1/1, general_quirky 0/1, iot_cleaning 2/2, iot_hue_lightchange 1/1, iot_hue_lightoff 0/1, iot_hue_lighton 1/1, iot_hue_lightup 0/1, music_likeness 1/1, takeaway_order 1/1, weather_query 1/1
- predicted: audio_volume_mute 2, iot_hue_lightdim 2, iot_cleaning 2, alarm_query 2, datetime_query 2, alarm_set 1, iot_hue_lightchange 1, iot_hue_lighton 1, general_greet 1, general_quirky 1, datetime_convert 1, alarm_remove 1, music_likeness 1, takeaway_order 1, weather_query 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 3
- top confusions: iot_hue_lightoff→iot_hue_lightdim ×1, general_quirky→audio_volume_mute ×1, datetime_query→general_quirky ×1, iot_hue_lightup→iot_hue_lightdim ×1
- answering model (cases): multilingual 20

### T7_massive_intent_10opt_ja_20/router / intent

- recall: alarm_query 2/2, alarm_remove 1/1, alarm_set 1/1, audio_volume_mute 1/1, datetime_convert 1/1, datetime_query 2/3, general_greet 1/1, general_quirky 0/1, iot_cleaning 2/2, iot_hue_lightchange 1/1, iot_hue_lightoff 0/1, iot_hue_lighton 1/1, iot_hue_lightup 0/1, music_likeness 1/1, takeaway_order 1/1, weather_query 1/1
- predicted: audio_volume_mute 2, iot_hue_lightdim 2, iot_cleaning 2, alarm_query 2, datetime_query 2, alarm_set 1, iot_hue_lightchange 1, iot_hue_lighton 1, general_greet 1, general_quirky 1, datetime_convert 1, alarm_remove 1, music_likeness 1, takeaway_order 1, weather_query 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 3
- top confusions: iot_hue_lightoff→iot_hue_lightdim ×1, general_quirky→audio_volume_mute ×1, datetime_query→general_quirky ×1, iot_hue_lightup→iot_hue_lightdim ×1
- answering model (cases): multilingual 20

### T7_massive_intent_10opt_ko_20/english / intent

- recall: alarm_query 0/2, alarm_remove 0/1, alarm_set 0/1, audio_volume_mute 0/1, datetime_convert 0/1, datetime_query 1/3, general_greet 0/1, general_quirky 1/1, iot_cleaning 0/2, iot_hue_lightchange 0/1, iot_hue_lightoff 0/1, iot_hue_lighton 0/1, iot_hue_lightup 0/1, music_likeness 0/1, takeaway_order 0/1, weather_query 0/1
- predicted: general_joke 3, datetime_query 2, calendar_set 2, qa_factoid 1, iot_hue_lightoff 1, qa_maths 1, takeaway_order 1, qa_stock 1, general_quirky 1, qa_definition 1, play_game 1, lists_remove 1, takeaway_query 1, music_settings 1, social_query 1, datetime_convert 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 0
- top confusions: alarm_query→calendar_set ×2, alarm_set→datetime_query ×1, audio_volume_mute→qa_factoid ×1, iot_hue_lightchange→iot_hue_lightoff ×1, iot_hue_lighton→general_joke ×1
- answering model (cases): english 20

### T7_massive_intent_10opt_ko_20/multilingual / intent

- recall: alarm_query 0/2, alarm_remove 1/1, alarm_set 1/1, audio_volume_mute 0/1, datetime_convert 0/1, datetime_query 1/3, general_greet 1/1, general_quirky 1/1, iot_cleaning 2/2, iot_hue_lightchange 0/1, iot_hue_lightoff 0/1, iot_hue_lighton 1/1, iot_hue_lightup 0/1, music_likeness 1/1, takeaway_order 0/1, weather_query 0/1
- predicted: iot_hue_lightdim 3, cooking_recipe 2, iot_hue_lighton 2, iot_cleaning 2, general_quirky 2, alarm_set 1, music_dislikeness 1, general_greet 1, alarm_remove 1, play_music 1, takeaway_order 1, music_likeness 1, datetime_query 1, calendar_remove 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 4
- top confusions: audio_volume_mute→cooking_recipe ×1, iot_hue_lightchange→music_dislikeness ×1, iot_hue_lightoff→iot_hue_lightdim ×1, datetime_query→general_quirky ×1, datetime_convert→iot_hue_lightdim ×1
- answering model (cases): multilingual 20

### T7_massive_intent_10opt_ko_20/router / intent

- recall: alarm_query 0/2, alarm_remove 1/1, alarm_set 1/1, audio_volume_mute 0/1, datetime_convert 0/1, datetime_query 1/3, general_greet 1/1, general_quirky 1/1, iot_cleaning 2/2, iot_hue_lightchange 0/1, iot_hue_lightoff 0/1, iot_hue_lighton 1/1, iot_hue_lightup 0/1, music_likeness 1/1, takeaway_order 0/1, weather_query 0/1
- predicted: iot_hue_lightdim 3, cooking_recipe 2, iot_hue_lighton 2, iot_cleaning 2, general_quirky 2, alarm_set 1, music_dislikeness 1, general_greet 1, alarm_remove 1, play_music 1, takeaway_order 1, music_likeness 1, datetime_query 1, calendar_remove 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 4
- top confusions: audio_volume_mute→cooking_recipe ×1, iot_hue_lightchange→music_dislikeness ×1, iot_hue_lightoff→iot_hue_lightdim ×1, datetime_query→general_quirky ×1, datetime_convert→iot_hue_lightdim ×1
- answering model (cases): multilingual 20

### T7_massive_intent_10opt_zh-CN_20/english / intent

- recall: alarm_query 0/2, alarm_remove 1/1, alarm_set 1/1, audio_volume_mute 0/1, datetime_convert 1/1, datetime_query 3/3, general_greet 0/1, general_quirky 0/1, iot_cleaning 0/2, iot_hue_lightchange 0/1, iot_hue_lightoff 1/1, iot_hue_lighton 0/1, iot_hue_lightup 0/1, music_likeness 1/1, takeaway_order 1/1, weather_query 0/1
- predicted: datetime_query 4, alarm_remove 2, iot_hue_lightdim 2, alarm_set 1, recommendation_movies 1, weather_query 1, iot_hue_lightoff 1, music_dislikeness 1, qa_definition 1, general_joke 1, datetime_convert 1, audio_volume_mute 1, music_likeness 1, takeaway_order 1, news_query 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 1
- top confusions: audio_volume_mute→alarm_remove ×1, iot_hue_lightchange→recommendation_movies ×1, iot_hue_lighton→weather_query ×1, iot_cleaning→music_dislikeness ×1, iot_cleaning→qa_definition ×1
- answering model (cases): english 20

### T7_massive_intent_10opt_zh-CN_20/multilingual / intent

- recall: alarm_query 0/2, alarm_remove 1/1, alarm_set 1/1, audio_volume_mute 1/1, datetime_convert 1/1, datetime_query 1/3, general_greet 1/1, general_quirky 1/1, iot_cleaning 1/2, iot_hue_lightchange 1/1, iot_hue_lightoff 0/1, iot_hue_lighton 1/1, iot_hue_lightup 0/1, music_likeness 1/1, takeaway_order 1/1, weather_query 0/1
- predicted: iot_hue_lightdim 2, takeaway_order 2, alarm_set 1, audio_volume_mute 1, iot_hue_lightchange 1, iot_hue_lighton 1, play_radio 1, iot_cleaning 1, general_quirky 1, general_greet 1, datetime_convert 1, alarm_remove 1, play_music 1, recommendation_locations 1, music_likeness 1, datetime_query 1, weather_query 1, news_query 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 2
- top confusions: iot_hue_lightoff→iot_hue_lightdim ×1, iot_cleaning→play_radio ×1, datetime_query→takeaway_order ×1, alarm_query→play_music ×1, alarm_query→recommendation_locations ×1
- answering model (cases): multilingual 20

### T7_massive_intent_10opt_zh-CN_20/router / intent

- recall: alarm_query 0/2, alarm_remove 1/1, alarm_set 1/1, audio_volume_mute 1/1, datetime_convert 1/1, datetime_query 1/3, general_greet 1/1, general_quirky 1/1, iot_cleaning 1/2, iot_hue_lightchange 1/1, iot_hue_lightoff 0/1, iot_hue_lighton 1/1, iot_hue_lightup 0/1, music_likeness 1/1, takeaway_order 1/1, weather_query 0/1
- predicted: iot_hue_lightdim 2, takeaway_order 2, alarm_set 1, audio_volume_mute 1, iot_hue_lightchange 1, iot_hue_lighton 1, play_radio 1, iot_cleaning 1, general_quirky 1, general_greet 1, datetime_convert 1, alarm_remove 1, play_music 1, recommendation_locations 1, music_likeness 1, datetime_query 1, weather_query 1, news_query 1
- first listed option (most common: `takeaway_order`): gold 2, predicted 2
- top confusions: iot_hue_lightoff→iot_hue_lightdim ×1, iot_cleaning→play_radio ×1, datetime_query→takeaway_order ×1, alarm_query→play_music ×1, alarm_query→recommendation_locations ×1
- answering model (cases): multilingual 20

### T8_prompt_injections_40/english / injection

- recall: false 20/20, true 11/20
- predicted: false 29, true 11
- first listed option (most common: `true`): gold 20, predicted 11
- top confusions: true→false ×9
- answering model (cases): english 40

### T8_prompt_injections_40/multilingual / injection

- recall: false 17/20, true 6/20
- predicted: false 31, true 9
- first listed option (most common: `true`): gold 20, predicted 9
- top confusions: true→false ×14, false→true ×3
- answering model (cases): multilingual 40

### T8_prompt_injections_40/router / injection

- recall: false 19/20, true 10/20
- predicted: false 29, true 11
- first listed option (most common: `true`): gold 20, predicted 11
- top confusions: true→false ×10, false→true ×1
- answering model (cases): english 26, multilingual 14

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/F/jev_cmp/laya/T1_typed_decisions_40_english.json | english | 0.3.23 | 749a24c4c0db977686f29eeecd41201e16b97629a9fbd641a6ffb5dfe6163834 | d46ef26a6ec2f2f8c6fc0cfa1e81715751dda05f173cd028ae3eaaa4b9d519cb | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 19, "test": 21} |
| results/F/jev_cmp/laya/T1_typed_decisions_40_english_rerun.json | english | 0.3.23 | 749a24c4c0db977686f29eeecd41201e16b97629a9fbd641a6ffb5dfe6163834 | d46ef26a6ec2f2f8c6fc0cfa1e81715751dda05f173cd028ae3eaaa4b9d519cb | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 19, "test": 21} |
| results/F/jev_cmp/laya/T1_typed_decisions_40_multilingual.json | multilingual | 0.3.23 | 749a24c4c0db977686f29eeecd41201e16b97629a9fbd641a6ffb5dfe6163834 | d46ef26a6ec2f2f8c6fc0cfa1e81715751dda05f173cd028ae3eaaa4b9d519cb | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 19, "test": 21} |
| results/F/jev_cmp/laya/T1_typed_decisions_40_noulnocrit_english.json | english | 0.3.23 | 2508b8172b70cd65f02d1e7ba21dca97ebd7d6603b3ee9f7ad8a057e06b50283 | 7b7f5dac86a48ee9fc492bbb9b29e1a406444c311578f902e6d93097c08dbd25 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 19, "test": 21} |
| results/F/jev_cmp/laya/T1_typed_decisions_40_noulnocrit_multilingual.json | multilingual | 0.3.23 | 2508b8172b70cd65f02d1e7ba21dca97ebd7d6603b3ee9f7ad8a057e06b50283 | 7b7f5dac86a48ee9fc492bbb9b29e1a406444c311578f902e6d93097c08dbd25 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 19, "test": 21} |
| results/F/jev_cmp/laya/T1_typed_decisions_40_router.json | router (auto) | 0.3.23 | 749a24c4c0db977686f29eeecd41201e16b97629a9fbd641a6ffb5dfe6163834 | d46ef26a6ec2f2f8c6fc0cfa1e81715751dda05f173cd028ae3eaaa4b9d519cb | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 19, "test": 21} |
| results/F/jev_cmp/laya/T1_typed_decisions_40_typed-decisions.json | typed-decisions | 0.3.23 | 749a24c4c0db977686f29eeecd41201e16b97629a9fbd641a6ffb5dfe6163834 | d46ef26a6ec2f2f8c6fc0cfa1e81715751dda05f173cd028ae3eaaa4b9d519cb | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 19, "test": 21} |
| results/F/jev_cmp/laya/T2_ag_news_40_english.json | english | 0.3.23 | 555c7cd7d38c78d183fe884c62e1bbb102d040871bf6e66a8911269eba20fd21 | c472cb1cb971dab3d01c811ccc0f997d39516555fd43f513a8c59654e0457be1 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 24, "dev": 16} |
| results/F/jev_cmp/laya/T2_ag_news_40_multilingual.json | multilingual | 0.3.23 | 555c7cd7d38c78d183fe884c62e1bbb102d040871bf6e66a8911269eba20fd21 | c472cb1cb971dab3d01c811ccc0f997d39516555fd43f513a8c59654e0457be1 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 24, "dev": 16} |
| results/F/jev_cmp/laya/T2_ag_news_40_router.json | router (auto) | 0.3.23 | 555c7cd7d38c78d183fe884c62e1bbb102d040871bf6e66a8911269eba20fd21 | c472cb1cb971dab3d01c811ccc0f997d39516555fd43f513a8c59654e0457be1 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 24, "dev": 16} |
| results/F/jev_cmp/laya/T3_emotion_40_english.json | english | 0.3.23 | 2246b5f04b1ed714ef9789548d6e0cf932db1fa40aed95a4b9a3f616a11510cb | bd7cc49e3561bf50d45db8c2d35820b8ddea855c9dfbc081303636596b4b4c97 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 24, "test": 16} |
| results/F/jev_cmp/laya/T3_emotion_40_multilingual.json | multilingual | 0.3.23 | 2246b5f04b1ed714ef9789548d6e0cf932db1fa40aed95a4b9a3f616a11510cb | bd7cc49e3561bf50d45db8c2d35820b8ddea855c9dfbc081303636596b4b4c97 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 24, "test": 16} |
| results/F/jev_cmp/laya/T3_emotion_40_router.json | router (auto) | 0.3.23 | 2246b5f04b1ed714ef9789548d6e0cf932db1fa40aed95a4b9a3f616a11510cb | bd7cc49e3561bf50d45db8c2d35820b8ddea855c9dfbc081303636596b4b4c97 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 24, "test": 16} |
| results/F/jev_cmp/laya/T4_banking77_10opt_40_english.json | english | 0.3.23 | b124b7fb685abe85de45689984013d9b012c7e0e361d1b29ee55eb12dd2d23bc | 3c4b9b99f9cc5adcd3a2930f1fd99613bd115873234f06d8e5b6176ab5bc7074 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 22, "dev": 18} |
| results/F/jev_cmp/laya/T4_banking77_10opt_40_multilingual.json | multilingual | 0.3.23 | b124b7fb685abe85de45689984013d9b012c7e0e361d1b29ee55eb12dd2d23bc | 3c4b9b99f9cc5adcd3a2930f1fd99613bd115873234f06d8e5b6176ab5bc7074 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 22, "dev": 18} |
| results/F/jev_cmp/laya/T4_banking77_10opt_40_router.json | router (auto) | 0.3.23 | b124b7fb685abe85de45689984013d9b012c7e0e361d1b29ee55eb12dd2d23bc | 3c4b9b99f9cc5adcd3a2930f1fd99613bd115873234f06d8e5b6176ab5bc7074 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 22, "dev": 18} |
| results/F/jev_cmp/laya/T5_boolq_40_english.json | english | 0.3.23 | 2b140a293790121b93dce29fb5c2804054570ee23238618b43a7915a6fe0786a | d8699dd37a63aa7bfbc74dd05ad250872384751ff635e5aeaaaf84cc5d69cebe | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 19, "test": 21} |
| results/F/jev_cmp/laya/T5_boolq_40_multilingual.json | multilingual | 0.3.23 | 2b140a293790121b93dce29fb5c2804054570ee23238618b43a7915a6fe0786a | d8699dd37a63aa7bfbc74dd05ad250872384751ff635e5aeaaaf84cc5d69cebe | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 19, "test": 21} |
| results/F/jev_cmp/laya/T5_boolq_40_router.json | router (auto) | 0.3.23 | 2b140a293790121b93dce29fb5c2804054570ee23238618b43a7915a6fe0786a | d8699dd37a63aa7bfbc74dd05ad250872384751ff635e5aeaaaf84cc5d69cebe | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 19, "test": 21} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_de_20_english.json | english | 0.3.23 | 56e7943c697a3bc551d4750d0789b60c8730f3c8e003c876d936da8d79372f72 | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 8, "dev": 12} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_de_20_multilingual.json | multilingual | 0.3.23 | 56e7943c697a3bc551d4750d0789b60c8730f3c8e003c876d936da8d79372f72 | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 8, "dev": 12} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_de_20_router.json | router (auto) | 0.3.23 | 56e7943c697a3bc551d4750d0789b60c8730f3c8e003c876d936da8d79372f72 | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 8, "dev": 12} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_en_20_english.json | english | 0.3.23 | 034e2c88a730463215407fc1f3883093f08bde494dc5bd933be44834913bf04f | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 12, "dev": 8} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_en_20_multilingual.json | multilingual | 0.3.23 | 034e2c88a730463215407fc1f3883093f08bde494dc5bd933be44834913bf04f | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 12, "dev": 8} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_en_20_router.json | router (auto) | 0.3.23 | 034e2c88a730463215407fc1f3883093f08bde494dc5bd933be44834913bf04f | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 12, "dev": 8} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_ja_20_english.json | english | 0.3.23 | dd2169a2ce4d50d6da036241ae7d19e13c46a8dbf12192cbb9fdbbaecedac9d8 | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 13, "dev": 7} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_ja_20_multilingual.json | multilingual | 0.3.23 | dd2169a2ce4d50d6da036241ae7d19e13c46a8dbf12192cbb9fdbbaecedac9d8 | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 13, "dev": 7} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_ja_20_router.json | router (auto) | 0.3.23 | dd2169a2ce4d50d6da036241ae7d19e13c46a8dbf12192cbb9fdbbaecedac9d8 | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 13, "dev": 7} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_ko_20_english.json | english | 0.3.23 | e17bfac7605ad315c0727b80632010b60ec864b81268ab7e53c1a3164deb95d2 | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 10, "dev": 10} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_ko_20_multilingual.json | multilingual | 0.3.23 | e17bfac7605ad315c0727b80632010b60ec864b81268ab7e53c1a3164deb95d2 | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 10, "dev": 10} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_ko_20_router.json | router (auto) | 0.3.23 | e17bfac7605ad315c0727b80632010b60ec864b81268ab7e53c1a3164deb95d2 | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 10, "dev": 10} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_zh-CN_20_english.json | english | 0.3.23 | 0dfe24d6f0fb09aa0331a8854cf182a9faaea97abeaf5582bacbeff74a74b7ef | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 10, "test": 10} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_zh-CN_20_multilingual.json | multilingual | 0.3.23 | 0dfe24d6f0fb09aa0331a8854cf182a9faaea97abeaf5582bacbeff74a74b7ef | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 10, "test": 10} |
| results/F/jev_cmp/laya/T7_massive_intent_10opt_zh-CN_20_router.json | router (auto) | 0.3.23 | 0dfe24d6f0fb09aa0331a8854cf182a9faaea97abeaf5582bacbeff74a74b7ef | e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 10, "test": 10} |
| results/F/jev_cmp/laya/T8_prompt_injections_40_english.json | english | 0.3.23 | ced9111cc7f717749e8acb5e7fff9f1873d2cfc673349f30cea0c4638c7347eb | ba5538b67233d0c619a115c56b97a2fdc41573b8ef92f72c5089ef14b972f7b4 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 22, "test": 18} |
| results/F/jev_cmp/laya/T8_prompt_injections_40_multilingual.json | multilingual | 0.3.23 | ced9111cc7f717749e8acb5e7fff9f1873d2cfc673349f30cea0c4638c7347eb | ba5538b67233d0c619a115c56b97a2fdc41573b8ef92f72c5089ef14b972f7b4 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 22, "test": 18} |
| results/F/jev_cmp/laya/T8_prompt_injections_40_router.json | router (auto) | 0.3.23 | ced9111cc7f717749e8acb5e7fff9f1873d2cfc673349f30cea0c4638c7347eb | ba5538b67233d0c619a115c56b97a2fdc41573b8ef92f72c5089ef14b972f7b4 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 22, "test": 18} |
