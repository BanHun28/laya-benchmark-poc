# metrics_extra summary

`scripts/metrics_extra.py summary results/B/20261002-1643_english_ko_massive_domain_8.json results/B/20261002-1643_multilingual_ko_massive_domain_8.json results/B/20261002-1644_typed-decisions_ko_massive_domain_8.json results/B/20261002-1645_english_ko_klue_ynat_7.json results/B/20261002-1645_multilingual_ko_klue_ynat_7.json results/B/20261002-1645_router_ko_massive_domain_8.json results/B/20261002-1646_typed-decisions_ko_klue_ynat_7.json results/B/20261002-1647_multilingual_ko_massive_scenario_18.json results/B/20261002-1647_router_ko_klue_ynat_7.json results/B/20261002-1648_english_en_massive_domain_8.json results/B/20261002-1648_english_ko_massive_scenario_18.json results/B/20261002-1648_multilingual_en_massive_domain_8.json results/B/20261002-1648_router_ko_massive_scenario_18.json results/B/20261002-1648_typed-decisions_ko_massive_scenario_18.json results/B/20261002-1649_multilingual_ko_massive_domain_8_en-desc_dev.json results/B/20261002-1649_multilingual_ko_massive_domain_8_ko-instr_dev.json results/B/20261002-1650_english_ko_massive_intent_20opt.json results/B/20261002-1650_multilingual_ko_klue_ynat_7_en-desc_dev.json results/B/20261002-1650_multilingual_ko_klue_ynat_7_ko-instr_dev.json results/B/20261002-1650_multilingual_ko_massive_intent_20opt.json results/B/20261002-1650_multilingual_ko_massive_scenario_18_en-desc_dev.json results/B/20261002-1650_typed-decisions_ko_massive_intent_20opt.json results/B/20261002-1651_english_en_massive_intent_20opt.json results/B/20261002-1651_multilingual_en_massive_intent_20opt.json results/B/20261002-1651_router_ko_massive_intent_20opt.json results/B/20261002-1651_typed-decisions_en_massive_intent_20opt.json results/B/20261002-1652_english_ko_klue_nli_3.json results/B/20261002-1652_multilingual_ko_klue_nli_3.json results/B/20261002-1653_typed-decisions_ko_klue_nli_3.json results/B/20261002-1654_english_ko_nsmc_sentiment.json results/B/20261002-1654_multilingual_ko_nsmc_sentiment.json results/B/20261002-1654_router_ko_klue_nli_3.json results/B/20261002-1656_typed-decisions_ko_nsmc_sentiment.json results/B/20261002-1657_multilingual_ko_kmhas_hate.json results/B/20261002-1657_router_ko_nsmc_sentiment.json results/B/20261002-1658_english_ko_kmhas_hate.json results/B/20261002-1659_router_ko_kmhas_hate.json results/B/20261002-1659_typed-decisions_ko_kmhas_hate.json results/B/20261002-1700_english_ko_kmhas_type_8.json results/B/20261002-1700_multilingual_ko_kmhas_type_8.json results/B/20261002-1701_typed-decisions_ko_kmhas_type_8.json results/B/20261002-1703_english_ko_3i4k_speechact_7.json results/B/20261002-1703_multilingual_ko_3i4k_speechact_7.json results/B/20261002-1703_router_ko_kmhas_type_8.json results/B/20261002-1704_typed-decisions_ko_3i4k_speechact_7.json results/B/20261002-1705_router_ko_3i4k_speechact_7.json --bootstrap 1000 --seed 13 --out results/B/metrics/summary_all.md --json results/B/metrics/summary_all.json` (2026-10-02T17:05:31+0900)

| set | model | qid | split | n | accuracy [95% CI] | macro-F1 ∪ | macro-F1 gold | Brier | ECE [95% CI] | mean conf | acc@50%cov | majority | random | Δ vs majority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ko_massive_domain_8 | english | domain | all | 500 | 0.262 [0.226, 0.300] | 0.218 | 0.218 | 0.841 | 0.082 [0.059, 0.120] | 0.303 | 0.380 | 0.126 | 0.125 | +0.136 |
| ko_massive_domain_8 | english | domain | dev | 250 | 0.248 [0.196, 0.296] | 0.206 | 0.206 | 0.845 | 0.108 [0.074, 0.161] | 0.297 | 0.376 | 0.148 | 0.125 | +0.100 |
| ko_massive_domain_8 | english | domain | test | 250 | 0.276 [0.216, 0.336] | 0.228 | 0.228 | 0.838 | 0.061 [0.044, 0.125] | 0.309 | 0.384 | 0.140 | 0.125 | +0.136 |
| ko_massive_domain_8 | multilingual | domain | all | 500 | 0.526 [0.486, 0.568] | 0.518 | 0.518 | 0.664 | 0.229 [0.197, 0.271] | 0.755 | 0.764 | 0.126 | 0.125 | +0.400 |
| ko_massive_domain_8 | multilingual | domain | dev | 250 | 0.560 [0.500, 0.620] | 0.555 | 0.555 | 0.634 | 0.200 [0.161, 0.261] | 0.756 | 0.792 | 0.148 | 0.125 | +0.412 |
| ko_massive_domain_8 | multilingual | domain | test | 250 | 0.492 [0.432, 0.552] | 0.468 | 0.468 | 0.695 | 0.263 [0.217, 0.320] | 0.755 | 0.752 | 0.140 | 0.125 | +0.352 |
| ko_massive_domain_8 | typed-decisions | domain | all | 500 | 0.288 [0.248, 0.326] | 0.267 | 0.267 | 0.819 | 0.068 [0.046, 0.104] | 0.253 | 0.408 | 0.126 | 0.125 | +0.162 |
| ko_massive_domain_8 | typed-decisions | domain | dev | 250 | 0.288 [0.232, 0.344] | 0.270 | 0.270 | 0.820 | 0.088 [0.053, 0.144] | 0.246 | 0.416 | 0.148 | 0.125 | +0.140 |
| ko_massive_domain_8 | typed-decisions | domain | test | 250 | 0.288 [0.232, 0.348] | 0.261 | 0.261 | 0.817 | 0.063 [0.047, 0.122] | 0.259 | 0.384 | 0.140 | 0.125 | +0.148 |
| ko_klue_ynat_7 | english | topic | all | 500 | 0.216 [0.180, 0.252] | 0.158 | 0.158 | 0.949 | 0.274 [0.238, 0.307] | 0.490 | 0.304 | 0.144 | 0.143 | +0.072 |
| ko_klue_ynat_7 | english | topic | dev | 245 | 0.184 [0.135, 0.233] | 0.140 | 0.140 | 0.957 | 0.297 [0.254, 0.345] | 0.481 | 0.262 | 0.163 | 0.143 | +0.020 |
| ko_klue_ynat_7 | english | topic | test | 255 | 0.247 [0.192, 0.302] | 0.175 | 0.175 | 0.941 | 0.252 [0.203, 0.308] | 0.499 | 0.331 | 0.165 | 0.143 | +0.082 |
| ko_klue_ynat_7 | multilingual | topic | all | 500 | 0.634 [0.590, 0.674] | 0.617 | 0.617 | 0.550 | 0.172 [0.144, 0.217] | 0.806 | 0.804 | 0.144 | 0.143 | +0.490 |
| ko_klue_ynat_7 | multilingual | topic | dev | 245 | 0.612 [0.547, 0.673] | 0.601 | 0.601 | 0.575 | 0.202 [0.164, 0.268] | 0.812 | 0.795 | 0.163 | 0.143 | +0.449 |
| ko_klue_ynat_7 | multilingual | topic | test | 255 | 0.655 [0.600, 0.710] | 0.631 | 0.631 | 0.525 | 0.148 [0.121, 0.209] | 0.800 | 0.811 | 0.165 | 0.143 | +0.490 |
| ko_massive_domain_8 | router | domain | all | 500 | 0.526 [0.486, 0.568] | 0.518 | 0.518 | 0.664 | 0.229 [0.197, 0.271] | 0.755 | 0.764 | 0.126 | 0.125 | +0.400 |
| ko_massive_domain_8 | router | domain | dev | 250 | 0.560 [0.500, 0.620] | 0.555 | 0.555 | 0.634 | 0.200 [0.161, 0.261] | 0.756 | 0.792 | 0.148 | 0.125 | +0.412 |
| ko_massive_domain_8 | router | domain | test | 250 | 0.492 [0.432, 0.552] | 0.468 | 0.468 | 0.695 | 0.263 [0.217, 0.320] | 0.755 | 0.752 | 0.140 | 0.125 | +0.352 |
| ko_klue_ynat_7 | typed-decisions | topic | all | 500 | 0.234 [0.198, 0.270] | 0.202 | 0.202 | 0.851 | 0.080 [0.062, 0.124] | 0.304 | 0.304 | 0.144 | 0.143 | +0.090 |
| ko_klue_ynat_7 | typed-decisions | topic | dev | 245 | 0.241 [0.192, 0.294] | 0.206 | 0.206 | 0.853 | 0.071 [0.044, 0.130] | 0.300 | 0.303 | 0.163 | 0.143 | +0.078 |
| ko_klue_ynat_7 | typed-decisions | topic | test | 255 | 0.227 [0.180, 0.282] | 0.194 | 0.194 | 0.849 | 0.105 [0.079, 0.160] | 0.308 | 0.315 | 0.165 | 0.143 | +0.063 |
| ko_massive_scenario_18 | multilingual | scenario | all | 100 | 0.520 [0.430, 0.620] | 0.367 | 0.550 | 0.694 | 0.250 [0.189, 0.352] | 0.747 | 0.760 | 0.210 | 0.056 | +0.310 |
| ko_massive_scenario_18 | multilingual | scenario | dev | 49 | 0.551 [0.429, 0.694] | 0.381 | 0.534 | 0.613 | 0.261 [0.196, 0.380] | 0.744 | 0.917 | 0.184 | 0.056 | +0.367 |
| ko_massive_scenario_18 | multilingual | scenario | test | 51 | 0.490 [0.353, 0.627] | 0.322 | 0.450 | 0.773 | 0.301 [0.224, 0.448] | 0.751 | 0.680 | 0.235 | 0.056 | +0.255 |
| ko_klue_ynat_7 | router | topic | all | 500 | 0.634 [0.590, 0.674] | 0.617 | 0.617 | 0.550 | 0.172 [0.144, 0.217] | 0.806 | 0.804 | 0.144 | 0.143 | +0.490 |
| ko_klue_ynat_7 | router | topic | dev | 245 | 0.612 [0.547, 0.673] | 0.601 | 0.601 | 0.575 | 0.202 [0.164, 0.268] | 0.812 | 0.795 | 0.163 | 0.143 | +0.449 |
| ko_klue_ynat_7 | router | topic | test | 255 | 0.655 [0.600, 0.710] | 0.631 | 0.631 | 0.525 | 0.148 [0.121, 0.209] | 0.800 | 0.811 | 0.165 | 0.143 | +0.490 |
| en_massive_domain_8 | english | domain | all | 500 | 0.446 [0.404, 0.490] | 0.410 | 0.410 | 0.678 | 0.044 [0.043, 0.094] | 0.461 | 0.640 | 0.126 | 0.125 | +0.320 |
| en_massive_domain_8 | english | domain | dev | 250 | 0.428 [0.364, 0.492] | 0.397 | 0.397 | 0.690 | 0.065 [0.066, 0.139] | 0.457 | 0.640 | 0.148 | 0.125 | +0.280 |
| en_massive_domain_8 | english | domain | test | 250 | 0.464 [0.404, 0.528] | 0.419 | 0.419 | 0.666 | 0.087 [0.069, 0.151] | 0.465 | 0.640 | 0.140 | 0.125 | +0.324 |
| ko_massive_scenario_18 | english | scenario | all | 100 | 0.310 [0.220, 0.400] | 0.211 | 0.274 | 1.026 | 0.403 [0.343, 0.503] | 0.713 | 0.420 | 0.210 | 0.056 | +0.100 |
| ko_massive_scenario_18 | english | scenario | dev | 49 | 0.347 [0.224, 0.490] | 0.236 | 0.307 | 1.011 | 0.412 [0.309, 0.556] | 0.729 | 0.417 | 0.184 | 0.056 | +0.163 |
| ko_massive_scenario_18 | english | scenario | test | 51 | 0.275 [0.157, 0.392] | 0.207 | 0.228 | 1.041 | 0.443 [0.355, 0.558] | 0.697 | 0.400 | 0.235 | 0.056 | +0.039 |
| en_massive_domain_8 | multilingual | domain | all | 500 | 0.510 [0.468, 0.552] | 0.491 | 0.491 | 0.735 | 0.279 [0.244, 0.321] | 0.789 | 0.704 | 0.126 | 0.125 | +0.384 |
| en_massive_domain_8 | multilingual | domain | dev | 250 | 0.476 [0.416, 0.540] | 0.451 | 0.451 | 0.798 | 0.311 [0.262, 0.374] | 0.787 | 0.648 | 0.148 | 0.125 | +0.328 |
| en_massive_domain_8 | multilingual | domain | test | 250 | 0.544 [0.484, 0.604] | 0.521 | 0.521 | 0.672 | 0.251 [0.207, 0.311] | 0.791 | 0.752 | 0.140 | 0.125 | +0.404 |
| ko_massive_scenario_18 | router | scenario | all | 100 | 0.520 [0.430, 0.620] | 0.367 | 0.550 | 0.694 | 0.250 [0.189, 0.352] | 0.747 | 0.760 | 0.210 | 0.056 | +0.310 |
| ko_massive_scenario_18 | router | scenario | dev | 49 | 0.551 [0.429, 0.694] | 0.381 | 0.534 | 0.613 | 0.261 [0.196, 0.380] | 0.744 | 0.917 | 0.184 | 0.056 | +0.367 |
| ko_massive_scenario_18 | router | scenario | test | 51 | 0.490 [0.353, 0.627] | 0.322 | 0.450 | 0.773 | 0.301 [0.224, 0.448] | 0.751 | 0.680 | 0.235 | 0.056 | +0.255 |
| ko_massive_scenario_18 | typed-decisions | scenario | all | 100 | 0.330 [0.240, 0.430] | 0.247 | 0.346 | 0.829 | 0.112 [0.104, 0.236] | 0.412 | 0.440 | 0.210 | 0.056 | +0.120 |
| ko_massive_scenario_18 | typed-decisions | scenario | dev | 49 | 0.306 [0.184, 0.449] | 0.233 | 0.303 | 0.861 | 0.170 [0.134, 0.323] | 0.402 | 0.417 | 0.184 | 0.056 | +0.122 |
| ko_massive_scenario_18 | typed-decisions | scenario | test | 51 | 0.353 [0.216, 0.490] | 0.287 | 0.316 | 0.799 | 0.153 [0.129, 0.300] | 0.421 | 0.480 | 0.235 | 0.056 | +0.118 |
| ko_massive_domain_8_en-desc | multilingual | domain | all | 250 | 0.532 [0.472, 0.592] | 0.509 | 0.509 | 0.669 | 0.213 [0.168, 0.269] | 0.745 | 0.728 | 0.148 | 0.125 | +0.384 |
| ko_massive_domain_8_en-desc | multilingual | domain | dev | 250 | 0.532 [0.472, 0.592] | 0.509 | 0.509 | 0.669 | 0.213 [0.168, 0.269] | 0.745 | 0.728 | 0.148 | 0.125 | +0.384 |
| ko_massive_domain_8_ko-instr | multilingual | domain | all | 250 | 0.540 [0.480, 0.600] | 0.529 | 0.529 | 0.656 | 0.233 [0.187, 0.288] | 0.773 | 0.760 | 0.148 | 0.125 | +0.392 |
| ko_massive_domain_8_ko-instr | multilingual | domain | dev | 250 | 0.540 [0.480, 0.600] | 0.529 | 0.529 | 0.656 | 0.233 [0.187, 0.288] | 0.773 | 0.760 | 0.148 | 0.125 | +0.392 |
| ko_massive_intent_20opt | english | intent | all | 100 | 0.110 [0.050, 0.170] | 0.041 | 0.068 | 1.510 | 0.680 [0.611, 0.753] | 0.790 | 0.140 | 0.170 | 0.050 | -0.060 |
| ko_massive_intent_20opt | english | intent | dev | 50 | 0.060 [0.000, 0.140] | 0.022 | 0.036 | 1.602 | 0.733 [0.646, 0.819] | 0.793 | 0.040 | 0.140 | 0.050 | -0.080 |
| ko_massive_intent_20opt | english | intent | test | 50 | 0.160 [0.080, 0.260] | 0.066 | 0.110 | 1.419 | 0.628 [0.532, 0.737] | 0.788 | 0.240 | 0.200 | 0.050 | -0.040 |
| ko_klue_ynat_7_en-desc | multilingual | topic | all | 245 | 0.637 [0.571, 0.694] | 0.608 | 0.608 | 0.575 | 0.220 [0.179, 0.284] | 0.843 | 0.787 | 0.163 | 0.143 | +0.473 |
| ko_klue_ynat_7_en-desc | multilingual | topic | dev | 245 | 0.637 [0.571, 0.694] | 0.608 | 0.608 | 0.575 | 0.220 [0.179, 0.284] | 0.843 | 0.787 | 0.163 | 0.143 | +0.473 |
| ko_klue_ynat_7_ko-instr | multilingual | topic | all | 245 | 0.608 [0.539, 0.669] | 0.598 | 0.598 | 0.571 | 0.208 [0.160, 0.266] | 0.803 | 0.770 | 0.163 | 0.143 | +0.445 |
| ko_klue_ynat_7_ko-instr | multilingual | topic | dev | 245 | 0.608 [0.539, 0.669] | 0.598 | 0.598 | 0.571 | 0.208 [0.160, 0.266] | 0.803 | 0.770 | 0.163 | 0.143 | +0.445 |
| ko_massive_intent_20opt | multilingual | intent | all | 100 | 0.470 [0.380, 0.570] | 0.304 | 0.374 | 0.777 | 0.311 [0.242, 0.403] | 0.777 | 0.680 | 0.170 | 0.050 | +0.300 |
| ko_massive_intent_20opt | multilingual | intent | dev | 50 | 0.480 [0.340, 0.620] | 0.366 | 0.505 | 0.723 | 0.286 [0.207, 0.411] | 0.762 | 0.760 | 0.140 | 0.050 | +0.340 |
| ko_massive_intent_20opt | multilingual | intent | test | 50 | 0.460 [0.320, 0.600] | 0.232 | 0.292 | 0.831 | 0.368 [0.267, 0.497] | 0.792 | 0.680 | 0.200 | 0.050 | +0.260 |
| ko_massive_scenario_18_en-desc | multilingual | scenario | all | 49 | 0.429 [0.286, 0.571] | 0.330 | 0.430 | 0.946 | 0.416 [0.315, 0.562] | 0.840 | 0.583 | 0.184 | 0.056 | +0.245 |
| ko_massive_scenario_18_en-desc | multilingual | scenario | dev | 49 | 0.429 [0.286, 0.571] | 0.330 | 0.430 | 0.946 | 0.416 [0.315, 0.562] | 0.840 | 0.583 | 0.184 | 0.056 | +0.245 |
| ko_massive_intent_20opt | typed-decisions | intent | all | 100 | 0.060 [0.020, 0.110] | 0.037 | 0.064 | 1.260 | 0.506 [0.450, 0.561] | 0.566 | 0.120 | 0.170 | 0.050 | -0.110 |
| ko_massive_intent_20opt | typed-decisions | intent | dev | 50 | 0.020 [0.000, 0.060] | 0.009 | 0.016 | 1.290 | 0.528 [0.471, 0.595] | 0.548 | 0.040 | 0.140 | 0.050 | -0.120 |
| ko_massive_intent_20opt | typed-decisions | intent | test | 50 | 0.100 [0.020, 0.180] | 0.063 | 0.112 | 1.230 | 0.483 [0.396, 0.567] | 0.583 | 0.160 | 0.200 | 0.050 | -0.100 |
| en_massive_intent_20opt | english | intent | all | 100 | 0.820 [0.740, 0.890] | 0.674 | 0.752 | 0.288 | 0.138 [0.082, 0.215] | 0.958 | 0.980 | 0.170 | 0.050 | +0.650 |
| en_massive_intent_20opt | english | intent | dev | 50 | 0.800 [0.660, 0.900] | 0.652 | 0.776 | 0.310 | 0.156 [0.080, 0.270] | 0.956 | 0.960 | 0.140 | 0.050 | +0.660 |
| en_massive_intent_20opt | english | intent | test | 50 | 0.840 [0.740, 0.940] | 0.754 | 0.754 | 0.266 | 0.139 [0.060, 0.223] | 0.960 | 1.000 | 0.200 | 0.050 | +0.640 |
| en_massive_intent_20opt | multilingual | intent | all | 100 | 0.710 [0.620, 0.800] | 0.503 | 0.658 | 0.506 | 0.233 [0.177, 0.329] | 0.888 | 0.920 | 0.170 | 0.050 | +0.540 |
| en_massive_intent_20opt | multilingual | intent | dev | 50 | 0.640 [0.500, 0.760] | 0.446 | 0.617 | 0.587 | 0.275 [0.173, 0.389] | 0.898 | 0.920 | 0.140 | 0.050 | +0.500 |
| en_massive_intent_20opt | multilingual | intent | test | 50 | 0.780 [0.660, 0.880] | 0.575 | 0.726 | 0.425 | 0.219 [0.154, 0.352] | 0.877 | 0.920 | 0.200 | 0.050 | +0.580 |
| ko_massive_intent_20opt | router | intent | all | 100 | 0.470 [0.380, 0.570] | 0.304 | 0.374 | 0.777 | 0.311 [0.242, 0.403] | 0.777 | 0.680 | 0.170 | 0.050 | +0.300 |
| ko_massive_intent_20opt | router | intent | dev | 50 | 0.480 [0.340, 0.620] | 0.366 | 0.505 | 0.723 | 0.286 [0.207, 0.411] | 0.762 | 0.760 | 0.140 | 0.050 | +0.340 |
| ko_massive_intent_20opt | router | intent | test | 50 | 0.460 [0.320, 0.600] | 0.232 | 0.292 | 0.831 | 0.368 [0.267, 0.497] | 0.792 | 0.680 | 0.200 | 0.050 | +0.260 |
| en_massive_intent_20opt | typed-decisions | intent | all | 100 | 0.820 [0.740, 0.890] | 0.632 | 0.778 | 0.276 | 0.093 [0.060, 0.159] | 0.901 | 0.980 | 0.170 | 0.050 | +0.650 |
| en_massive_intent_20opt | typed-decisions | intent | dev | 50 | 0.860 [0.760, 0.940] | 0.712 | 0.881 | 0.217 | 0.091 [0.058, 0.179] | 0.907 | 0.960 | 0.140 | 0.050 | +0.720 |
| en_massive_intent_20opt | typed-decisions | intent | test | 50 | 0.780 [0.660, 0.900] | 0.594 | 0.671 | 0.334 | 0.119 [0.074, 0.222] | 0.894 | 1.000 | 0.200 | 0.050 | +0.580 |
| ko_klue_nli_3 | english | relation | all | 500 | 0.448 [0.402, 0.492] | 0.438 | 0.438 | 0.694 | 0.215 [0.177, 0.260] | 0.658 | 0.548 | 0.334 | 0.333 | +0.114 |
| ko_klue_nli_3 | english | relation | dev | 263 | 0.456 [0.395, 0.513] | 0.440 | 0.440 | 0.688 | 0.212 [0.164, 0.273] | 0.666 | 0.588 | 0.342 | 0.333 | +0.114 |
| ko_klue_nli_3 | english | relation | test | 237 | 0.439 [0.376, 0.506] | 0.436 | 0.436 | 0.701 | 0.218 [0.164, 0.279] | 0.649 | 0.534 | 0.354 | 0.333 | +0.084 |
| ko_klue_nli_3 | multilingual | relation | all | 500 | 0.750 [0.712, 0.786] | 0.747 | 0.747 | 0.435 | 0.196 [0.164, 0.233] | 0.919 | 0.872 | 0.334 | 0.333 | +0.416 |
| ko_klue_nli_3 | multilingual | relation | dev | 263 | 0.760 [0.707, 0.814] | 0.760 | 0.760 | 0.422 | 0.190 [0.150, 0.243] | 0.915 | 0.870 | 0.342 | 0.333 | +0.418 |
| ko_klue_nli_3 | multilingual | relation | test | 237 | 0.738 [0.679, 0.793] | 0.729 | 0.729 | 0.449 | 0.203 [0.154, 0.263] | 0.924 | 0.864 | 0.354 | 0.333 | +0.384 |
| ko_klue_nli_3 | typed-decisions | relation | all | 500 | 0.496 [0.452, 0.540] | 0.482 | 0.482 | 0.617 | 0.086 [0.060, 0.133] | 0.565 | 0.604 | 0.334 | 0.333 | +0.162 |
| ko_klue_nli_3 | typed-decisions | relation | dev | 263 | 0.479 [0.422, 0.536] | 0.468 | 0.468 | 0.617 | 0.121 [0.090, 0.185] | 0.569 | 0.595 | 0.342 | 0.333 | +0.137 |
| ko_klue_nli_3 | typed-decisions | relation | test | 237 | 0.515 [0.451, 0.582] | 0.493 | 0.493 | 0.617 | 0.060 [0.055, 0.145] | 0.562 | 0.619 | 0.354 | 0.333 | +0.160 |
| ko_nsmc_sentiment | english | sentiment_noul | all | 500 | 0.516 [0.472, 0.560] | 0.442 | 0.442 | 0.732 | 0.325 [0.283, 0.371] | 0.836 | 0.532 | 0.500 | 0.500 | +0.016 |
| ko_nsmc_sentiment | english | sentiment_noul | dev | 249 | 0.506 [0.442, 0.570] | 0.446 | 0.446 | 0.755 | 0.342 [0.282, 0.409] | 0.837 | 0.508 | 0.522 | 0.500 | -0.016 |
| ko_nsmc_sentiment | english | sentiment_noul | test | 251 | 0.526 [0.462, 0.590] | 0.436 | 0.436 | 0.709 | 0.309 [0.257, 0.380] | 0.834 | 0.552 | 0.522 | 0.500 | +0.004 |
| ko_nsmc_sentiment | english | sentiment_choice | all | 500 | 0.528 [0.484, 0.570] | 0.513 | 0.513 | 0.612 | 0.203 [0.173, 0.254] | 0.724 | 0.540 | 0.500 | 0.500 | +0.028 |
| ko_nsmc_sentiment | english | sentiment_choice | dev | 249 | 0.542 [0.478, 0.602] | 0.532 | 0.532 | 0.580 | 0.184 [0.141, 0.253] | 0.718 | 0.565 | 0.522 | 0.500 | +0.020 |
| ko_nsmc_sentiment | english | sentiment_choice | test | 251 | 0.514 [0.454, 0.574] | 0.493 | 0.493 | 0.643 | 0.244 [0.191, 0.309] | 0.729 | 0.496 | 0.522 | 0.500 | -0.008 |
| ko_nsmc_sentiment | multilingual | sentiment_noul | all | 500 | 0.638 [0.598, 0.678] | 0.586 | 0.586 | 0.619 | 0.289 [0.254, 0.331] | 0.925 | 0.744 | 0.500 | 0.500 | +0.138 |
| ko_nsmc_sentiment | multilingual | sentiment_noul | dev | 249 | 0.635 [0.582, 0.691] | 0.592 | 0.592 | 0.621 | 0.297 [0.247, 0.359] | 0.916 | 0.742 | 0.522 | 0.500 | +0.112 |
| ko_nsmc_sentiment | multilingual | sentiment_noul | test | 251 | 0.641 [0.582, 0.701] | 0.578 | 0.578 | 0.617 | 0.301 [0.252, 0.364] | 0.934 | 0.744 | 0.522 | 0.500 | +0.120 |
| ko_nsmc_sentiment | multilingual | sentiment_choice | all | 500 | 0.774 [0.736, 0.810] | 0.771 | 0.771 | 0.357 | 0.134 [0.106, 0.173] | 0.905 | 0.888 | 0.500 | 0.500 | +0.274 |
| ko_nsmc_sentiment | multilingual | sentiment_choice | dev | 249 | 0.775 [0.719, 0.823] | 0.774 | 0.774 | 0.359 | 0.143 [0.110, 0.200] | 0.910 | 0.895 | 0.522 | 0.500 | +0.253 |
| ko_nsmc_sentiment | multilingual | sentiment_choice | test | 251 | 0.773 [0.725, 0.821] | 0.767 | 0.767 | 0.355 | 0.132 [0.096, 0.186] | 0.900 | 0.888 | 0.522 | 0.500 | +0.251 |
| ko_klue_nli_3 | router | relation | all | 500 | 0.750 [0.712, 0.786] | 0.747 | 0.747 | 0.435 | 0.196 [0.164, 0.233] | 0.919 | 0.872 | 0.334 | 0.333 | +0.416 |
| ko_klue_nli_3 | router | relation | dev | 263 | 0.760 [0.707, 0.814] | 0.760 | 0.760 | 0.422 | 0.190 [0.150, 0.243] | 0.915 | 0.870 | 0.342 | 0.333 | +0.418 |
| ko_klue_nli_3 | router | relation | test | 237 | 0.738 [0.679, 0.793] | 0.729 | 0.729 | 0.449 | 0.203 [0.154, 0.263] | 0.924 | 0.864 | 0.354 | 0.333 | +0.384 |
| ko_nsmc_sentiment | typed-decisions | sentiment_noul | all | 500 | 0.532 [0.486, 0.578] | 0.504 | 0.504 | 0.520 | 0.105 [0.075, 0.155] | 0.635 | 0.584 | 0.500 | 0.500 | +0.032 |
| ko_nsmc_sentiment | typed-decisions | sentiment_noul | dev | 249 | 0.538 [0.478, 0.602] | 0.520 | 0.520 | 0.517 | 0.121 [0.074, 0.181] | 0.636 | 0.597 | 0.522 | 0.500 | +0.016 |
| ko_nsmc_sentiment | typed-decisions | sentiment_noul | test | 251 | 0.526 [0.466, 0.586] | 0.486 | 0.486 | 0.523 | 0.108 [0.073, 0.177] | 0.634 | 0.576 | 0.522 | 0.500 | +0.004 |
| ko_nsmc_sentiment | typed-decisions | sentiment_choice | all | 500 | 0.506 [0.462, 0.546] | 0.482 | 0.482 | 0.568 | 0.155 [0.120, 0.202] | 0.656 | 0.496 | 0.500 | 0.500 | +0.006 |
| ko_nsmc_sentiment | typed-decisions | sentiment_choice | dev | 249 | 0.522 [0.462, 0.582] | 0.493 | 0.493 | 0.540 | 0.123 [0.085, 0.196] | 0.645 | 0.540 | 0.522 | 0.500 | +0.000 |
| ko_nsmc_sentiment | typed-decisions | sentiment_choice | test | 251 | 0.490 [0.430, 0.554] | 0.472 | 0.472 | 0.597 | 0.189 [0.143, 0.253] | 0.667 | 0.448 | 0.522 | 0.500 | -0.032 |
| ko_kmhas_hate | multilingual | is_hate | all | 500 | 0.582 [0.542, 0.624] | 0.530 | 0.530 | 0.642 | 0.275 [0.239, 0.319] | 0.854 | 0.680 | 0.500 | 0.500 | +0.082 |
| ko_kmhas_hate | multilingual | is_hate | dev | 237 | 0.582 [0.523, 0.646] | 0.534 | 0.534 | 0.627 | 0.263 [0.216, 0.332] | 0.846 | 0.669 | 0.502 | 0.500 | +0.080 |
| ko_kmhas_hate | multilingual | is_hate | test | 263 | 0.582 [0.521, 0.639] | 0.525 | 0.525 | 0.656 | 0.286 [0.238, 0.356] | 0.861 | 0.679 | 0.502 | 0.500 | +0.080 |
| ko_nsmc_sentiment | router | sentiment_noul | all | 500 | 0.640 [0.598, 0.682] | 0.589 | 0.589 | 0.615 | 0.287 [0.251, 0.329] | 0.925 | 0.744 | 0.500 | 0.500 | +0.140 |
| ko_nsmc_sentiment | router | sentiment_noul | dev | 249 | 0.635 [0.582, 0.691] | 0.592 | 0.592 | 0.621 | 0.297 [0.247, 0.359] | 0.916 | 0.742 | 0.522 | 0.500 | +0.112 |
| ko_nsmc_sentiment | router | sentiment_noul | test | 251 | 0.645 [0.586, 0.705] | 0.585 | 0.585 | 0.609 | 0.296 [0.250, 0.360] | 0.933 | 0.744 | 0.522 | 0.500 | +0.124 |
| ko_nsmc_sentiment | router | sentiment_choice | all | 500 | 0.776 [0.740, 0.812] | 0.773 | 0.773 | 0.352 | 0.132 [0.102, 0.170] | 0.904 | 0.888 | 0.500 | 0.500 | +0.276 |
| ko_nsmc_sentiment | router | sentiment_choice | dev | 249 | 0.775 [0.719, 0.823] | 0.774 | 0.774 | 0.359 | 0.143 [0.110, 0.200] | 0.910 | 0.895 | 0.522 | 0.500 | +0.253 |
| ko_nsmc_sentiment | router | sentiment_choice | test | 251 | 0.777 [0.729, 0.829] | 0.771 | 0.771 | 0.345 | 0.126 [0.092, 0.179] | 0.899 | 0.888 | 0.522 | 0.500 | +0.255 |
| ko_kmhas_hate | english | is_hate | all | 500 | 0.500 [0.458, 0.542] | 0.333 | 0.333 | 0.918 | 0.454 [0.413, 0.496] | 0.949 | 0.480 | 0.500 | 0.500 | +0.000 |
| ko_kmhas_hate | english | is_hate | dev | 237 | 0.502 [0.439, 0.565] | 0.334 | 0.334 | 0.922 | 0.454 [0.392, 0.519] | 0.954 | 0.500 | 0.502 | 0.500 | +0.000 |
| ko_kmhas_hate | english | is_hate | test | 263 | 0.498 [0.437, 0.559] | 0.332 | 0.332 | 0.915 | 0.458 [0.398, 0.516] | 0.945 | 0.443 | 0.502 | 0.500 | -0.004 |
| ko_kmhas_hate | router | is_hate | all | 500 | 0.582 [0.542, 0.624] | 0.530 | 0.530 | 0.642 | 0.275 [0.239, 0.319] | 0.854 | 0.680 | 0.500 | 0.500 | +0.082 |
| ko_kmhas_hate | router | is_hate | dev | 237 | 0.582 [0.523, 0.646] | 0.534 | 0.534 | 0.627 | 0.263 [0.216, 0.332] | 0.846 | 0.669 | 0.502 | 0.500 | +0.080 |
| ko_kmhas_hate | router | is_hate | test | 263 | 0.582 [0.521, 0.639] | 0.525 | 0.525 | 0.656 | 0.286 [0.238, 0.356] | 0.861 | 0.679 | 0.502 | 0.500 | +0.080 |
| ko_kmhas_hate | typed-decisions | is_hate | all | 500 | 0.500 [0.458, 0.542] | 0.333 | 0.333 | 0.657 | 0.282 [0.240, 0.325] | 0.775 | 0.492 | 0.500 | 0.500 | +0.000 |
| ko_kmhas_hate | typed-decisions | is_hate | dev | 237 | 0.502 [0.439, 0.565] | 0.334 | 0.334 | 0.657 | 0.277 [0.218, 0.342] | 0.778 | 0.492 | 0.502 | 0.500 | +0.000 |
| ko_kmhas_hate | typed-decisions | is_hate | test | 263 | 0.498 [0.437, 0.559] | 0.332 | 0.332 | 0.657 | 0.287 [0.226, 0.345] | 0.771 | 0.466 | 0.502 | 0.500 | -0.004 |
| ko_kmhas_type_8 | english | hate_type | all | 500 | 0.146 [0.118, 0.178] | 0.067 | 0.067 | 1.145 | 0.432 [0.398, 0.468] | 0.570 | 0.152 | 0.144 | 0.125 | +0.002 |
| ko_kmhas_type_8 | english | hate_type | dev | 244 | 0.160 [0.115, 0.205] | 0.082 | 0.082 | 1.129 | 0.413 [0.368, 0.463] | 0.563 | 0.164 | 0.152 | 0.125 | +0.008 |
| ko_kmhas_type_8 | english | hate_type | test | 256 | 0.133 [0.094, 0.176] | 0.055 | 0.055 | 1.160 | 0.449 [0.403, 0.496] | 0.576 | 0.133 | 0.176 | 0.125 | -0.043 |
| ko_kmhas_type_8 | multilingual | hate_type | all | 500 | 0.394 [0.350, 0.436] | 0.381 | 0.381 | 0.958 | 0.403 [0.362, 0.444] | 0.797 | 0.508 | 0.144 | 0.125 | +0.250 |
| ko_kmhas_type_8 | multilingual | hate_type | dev | 244 | 0.385 [0.328, 0.447] | 0.376 | 0.376 | 0.964 | 0.424 [0.369, 0.483] | 0.810 | 0.516 | 0.152 | 0.125 | +0.234 |
| ko_kmhas_type_8 | multilingual | hate_type | test | 256 | 0.402 [0.344, 0.461] | 0.385 | 0.385 | 0.952 | 0.382 [0.331, 0.442] | 0.785 | 0.516 | 0.176 | 0.125 | +0.227 |
| ko_kmhas_type_8 | typed-decisions | hate_type | all | 500 | 0.180 [0.148, 0.216] | 0.114 | 0.114 | 0.906 | 0.145 [0.113, 0.180] | 0.325 | 0.208 | 0.144 | 0.125 | +0.036 |
| ko_kmhas_type_8 | typed-decisions | hate_type | dev | 244 | 0.168 [0.123, 0.217] | 0.112 | 0.112 | 0.908 | 0.157 [0.112, 0.205] | 0.320 | 0.164 | 0.152 | 0.125 | +0.016 |
| ko_kmhas_type_8 | typed-decisions | hate_type | test | 256 | 0.191 [0.145, 0.238] | 0.111 | 0.111 | 0.904 | 0.139 [0.106, 0.191] | 0.330 | 0.242 | 0.176 | 0.125 | +0.016 |
| ko_3i4k_speechact_7 | english | speech_act | all | 500 | 0.174 [0.144, 0.206] | 0.121 | 0.121 | 0.949 | 0.178 [0.142, 0.212] | 0.346 | 0.204 | 0.144 | 0.143 | +0.030 |
| ko_3i4k_speechact_7 | english | speech_act | dev | 241 | 0.174 [0.124, 0.220] | 0.126 | 0.126 | 0.939 | 0.171 [0.134, 0.231] | 0.340 | 0.208 | 0.162 | 0.143 | +0.012 |
| ko_3i4k_speechact_7 | english | speech_act | test | 259 | 0.174 [0.127, 0.220] | 0.116 | 0.116 | 0.959 | 0.184 [0.142, 0.238] | 0.351 | 0.202 | 0.162 | 0.143 | +0.012 |
| ko_3i4k_speechact_7 | multilingual | speech_act | all | 500 | 0.178 [0.146, 0.212] | 0.166 | 0.166 | 1.055 | 0.353 [0.317, 0.391] | 0.531 | 0.152 | 0.144 | 0.143 | +0.034 |
| ko_3i4k_speechact_7 | multilingual | speech_act | dev | 241 | 0.195 [0.145, 0.245] | 0.183 | 0.183 | 1.038 | 0.335 [0.282, 0.394] | 0.530 | 0.158 | 0.162 | 0.143 | +0.033 |
| ko_3i4k_speechact_7 | multilingual | speech_act | test | 259 | 0.162 [0.124, 0.212] | 0.150 | 0.150 | 1.071 | 0.371 [0.320, 0.424] | 0.533 | 0.147 | 0.162 | 0.143 | +0.000 |
| ko_kmhas_type_8 | router | hate_type | all | 500 | 0.394 [0.350, 0.436] | 0.381 | 0.381 | 0.958 | 0.403 [0.362, 0.444] | 0.797 | 0.508 | 0.144 | 0.125 | +0.250 |
| ko_kmhas_type_8 | router | hate_type | dev | 244 | 0.385 [0.328, 0.447] | 0.376 | 0.376 | 0.964 | 0.424 [0.368, 0.482] | 0.809 | 0.516 | 0.152 | 0.125 | +0.234 |
| ko_kmhas_type_8 | router | hate_type | test | 256 | 0.402 [0.344, 0.461] | 0.385 | 0.385 | 0.952 | 0.382 [0.331, 0.442] | 0.785 | 0.516 | 0.176 | 0.125 | +0.227 |
| ko_3i4k_speechact_7 | typed-decisions | speech_act | all | 500 | 0.162 [0.130, 0.196] | 0.114 | 0.114 | 0.875 | 0.052 [0.025, 0.082] | 0.214 | 0.172 | 0.144 | 0.143 | +0.018 |
| ko_3i4k_speechact_7 | typed-decisions | speech_act | dev | 241 | 0.170 [0.129, 0.220] | 0.119 | 0.119 | 0.873 | 0.045 [0.021, 0.090] | 0.215 | 0.183 | 0.162 | 0.143 | +0.008 |
| ko_3i4k_speechact_7 | typed-decisions | speech_act | test | 259 | 0.154 [0.112, 0.197] | 0.111 | 0.111 | 0.876 | 0.058 [0.029, 0.101] | 0.212 | 0.163 | 0.162 | 0.143 | -0.008 |
| ko_3i4k_speechact_7 | router | speech_act | all | 500 | 0.178 [0.146, 0.212] | 0.166 | 0.166 | 1.055 | 0.353 [0.317, 0.391] | 0.531 | 0.152 | 0.144 | 0.143 | +0.034 |
| ko_3i4k_speechact_7 | router | speech_act | dev | 241 | 0.195 [0.145, 0.245] | 0.183 | 0.183 | 1.038 | 0.335 [0.282, 0.394] | 0.530 | 0.158 | 0.162 | 0.143 | +0.033 |
| ko_3i4k_speechact_7 | router | speech_act | test | 259 | 0.162 [0.124, 0.212] | 0.150 | 0.150 | 1.071 | 0.371 [0.320, 0.424] | 0.533 | 0.147 | 0.162 | 0.143 | +0.000 |

## Per-class detail (split = all; dev/test in the JSON)

### ko_massive_domain_8/english / domain

- recall: communication 49/62, general 0/62, info_qa 1/63, lifestyle 31/62, media 19/63, productivity 10/63, smart_home 11/63, transport 10/62
- predicted: communication 198, lifestyle 125, media 115, productivity 28, smart_home 11, transport 10, info_qa 7, general 6
- first listed option (most common: `productivity`): gold 63, predicted 28
- top confusions: smart_home→communication ×32, info_qa→communication ×26, productivity→communication ×22, media→communication ×21, productivity→media ×20
- answering model (cases): english 500

### ko_massive_domain_8/multilingual / domain

- recall: communication 41/62, general 19/62, info_qa 21/63, lifestyle 33/62, media 28/63, productivity 10/63, smart_home 51/63, transport 60/62
- predicted: smart_home 140, general 80, transport 76, lifestyle 54, communication 53, info_qa 46, media 32, productivity 19
- first listed option (most common: `productivity`): gold 63, predicted 19
- top confusions: media→smart_home ×24, general→smart_home ×22, info_qa→general ×22, productivity→smart_home ×22, productivity→general ×13
- answering model (cases): multilingual 500

### ko_massive_domain_8/typed-decisions / domain

- recall: communication 46/62, general 2/62, info_qa 10/63, lifestyle 26/62, media 23/63, productivity 13/63, smart_home 14/63, transport 10/62
- predicted: communication 155, media 121, lifestyle 97, info_qa 63, productivity 24, smart_home 17, general 13, transport 10
- first listed option (most common: `productivity`): gold 63, predicted 24
- top confusions: productivity→communication ×22, info_qa→communication ×20, productivity→media ×19, info_qa→media ×18, general→communication ×17
- answering model (cases): typed-decisions 500

### ko_klue_ynat_7/english / topic

- recall: culture_life 4/71, economy 50/72, it_science 33/72, politics 1/71, society 0/72, sports 10/71, world 10/71
- predicted: economy 261, it_science 135, world 58, culture_life 24, sports 19, society 2, politics 1
- first listed option (most common: `it_science`): gold 72, predicted 135
- top confusions: society→economy ×45, politics→economy ×40, world→economy ×35, culture_life→economy ×33, sports→economy ×32
- answering model (cases): english 500

### ko_klue_ynat_7/multilingual / topic

- recall: culture_life 41/71, economy 63/72, it_science 62/72, politics 44/71, society 15/72, sports 57/71, world 35/71
- predicted: economy 114, it_science 93, politics 77, sports 69, world 61, culture_life 51, society 35
- first listed option (most common: `it_science`): gold 72, predicted 93
- top confusions: society→economy ×25, world→politics ×15, society→politics ×14, society→it_science ×11, politics→world ×11
- answering model (cases): multilingual 500

### ko_massive_domain_8/router / domain

- recall: communication 41/62, general 19/62, info_qa 21/63, lifestyle 33/62, media 28/63, productivity 10/63, smart_home 51/63, transport 60/62
- predicted: smart_home 140, general 80, transport 76, lifestyle 54, communication 53, info_qa 46, media 32, productivity 19
- first listed option (most common: `productivity`): gold 63, predicted 19
- top confusions: media→smart_home ×24, general→smart_home ×22, info_qa→general ×22, productivity→smart_home ×22, productivity→general ×13
- answering model (cases): multilingual 500

### ko_klue_ynat_7/typed-decisions / topic

- recall: culture_life 25/71, economy 39/72, it_science 23/72, politics 0/71, society 5/72, sports 8/71, world 17/71
- predicted: economy 173, culture_life 120, world 104, it_science 58, society 29, sports 15, politics 1
- first listed option (most common: `it_science`): gold 72, predicted 58
- top confusions: society→economy ×32, politics→economy ×31, world→culture_life ×23, sports→world ×22, world→economy ×21
- answering model (cases): typed-decisions 500

### ko_massive_scenario_18/multilingual / scenario

- recall: alarm 6/7, audio 1/7, datetime 6/9, general 5/7, iot 8/21, music 4/4, news 6/9, play 1/17, takeaway 5/6, weather 10/13
- predicted: music 20, alarm 16, weather 14, general 12, iot 9, datetime 6, news 6, takeaway 5, qa 3, calendar 2, transport 2, audio 2, email 1, social 1, play 1
- first listed option (most common: `alarm`): gold 7, predicted 16
- top confusions: play→music ×14, iot→alarm ×7, audio→general ×4, iot→general ×2, datetime→weather ×2
- answering model (cases): multilingual 100

### ko_klue_ynat_7/router / topic

- recall: culture_life 41/71, economy 63/72, it_science 62/72, politics 44/71, society 15/72, sports 57/71, world 35/71
- predicted: economy 114, it_science 93, politics 77, sports 69, world 61, culture_life 51, society 35
- first listed option (most common: `it_science`): gold 72, predicted 93
- top confusions: society→economy ×25, world→politics ×15, society→politics ×14, society→it_science ×11, politics→world ×11
- answering model (cases): multilingual 500

### en_massive_domain_8/english / domain

- recall: communication 38/62, general 10/62, info_qa 0/63, lifestyle 30/62, media 13/63, productivity 20/63, smart_home 56/63, transport 56/62
- predicted: communication 157, smart_home 86, lifestyle 77, transport 63, media 55, productivity 36, general 26
- first listed option (most common: `productivity`): gold 63, predicted 36
- top confusions: info_qa→communication ×32, media→communication ×31, general→lifestyle ×20, productivity→communication ×20, media→smart_home ×14
- answering model (cases): english 500

### ko_massive_scenario_18/english / scenario

- recall: alarm 3/7, audio 2/7, datetime 2/9, general 0/7, iot 4/21, music 0/4, news 4/9, play 7/17, takeaway 0/6, weather 9/13
- predicted: play 29, audio 20, alarm 14, weather 9, iot 7, datetime 5, music 5, news 4, lists 3, takeaway 2, social 1, qa 1
- first listed option (most common: `alarm`): gold 7, predicted 14
- top confusions: iot→audio ×9, datetime→play ×6, audio→alarm ×5, takeaway→play ×4, iot→music ×4
- answering model (cases): english 100

### en_massive_domain_8/multilingual / domain

- recall: communication 41/62, general 17/62, info_qa 23/63, lifestyle 32/62, media 19/63, productivity 6/63, smart_home 57/63, transport 60/62
- predicted: smart_home 143, general 83, transport 72, info_qa 58, communication 51, lifestyle 49, media 31, productivity 13
- first listed option (most common: `productivity`): gold 63, predicted 13
- top confusions: media→smart_home ×34, info_qa→general ×25, productivity→smart_home ×24, general→info_qa ×19, productivity→general ×15
- answering model (cases): multilingual 500

### ko_massive_scenario_18/router / scenario

- recall: alarm 6/7, audio 1/7, datetime 6/9, general 5/7, iot 8/21, music 4/4, news 6/9, play 1/17, takeaway 5/6, weather 10/13
- predicted: music 20, alarm 16, weather 14, general 12, iot 9, datetime 6, news 6, takeaway 5, qa 3, calendar 2, transport 2, audio 2, email 1, social 1, play 1
- first listed option (most common: `alarm`): gold 7, predicted 16
- top confusions: play→music ×14, iot→alarm ×7, audio→general ×4, iot→general ×2, datetime→weather ×2
- answering model (cases): multilingual 100

### ko_massive_scenario_18/typed-decisions / scenario

- recall: alarm 1/7, audio 1/7, datetime 4/9, general 3/7, iot 5/21, music 0/4, news 5/9, play 4/17, takeaway 3/6, weather 7/13
- predicted: play 30, datetime 16, takeaway 13, iot 9, weather 7, audio 6, news 6, general 4, social 3, lists 2, recommendation 1, alarm 1, qa 1, music 1
- first listed option (most common: `alarm`): gold 7, predicted 1
- top confusions: iot→play ×9, play→takeaway ×5, iot→audio ×4, datetime→play ×4, audio→play ×4
- answering model (cases): typed-decisions 100

### ko_massive_domain_8_en-desc/multilingual / domain

- recall: communication 16/30, general 11/30, info_qa 5/31, lifestyle 14/27, media 23/37, productivity 8/33, smart_home 25/30, transport 31/32
- predicted: smart_home 54, transport 38, general 35, media 32, lifestyle 31, communication 25, info_qa 18, productivity 17
- first listed option (most common: `productivity`): gold 33, predicted 17
- top confusions: general→smart_home ×7, info_qa→general ×7, productivity→smart_home ×7, media→smart_home ×6, info_qa→lifestyle ×6
- answering model (cases): multilingual 250

### ko_massive_domain_8_ko-instr/multilingual / domain

- recall: communication 20/30, general 10/30, info_qa 8/31, lifestyle 14/27, media 16/37, productivity 9/33, smart_home 27/30, transport 31/32
- predicted: smart_home 67, general 43, transport 40, lifestyle 30, communication 29, media 16, info_qa 13, productivity 12
- first listed option (most common: `productivity`): gold 33, predicted 12
- top confusions: info_qa→general ×13, general→smart_home ×11, media→smart_home ×10, productivity→smart_home ×8, communication→general ×7
- answering model (cases): multilingual 250

### ko_massive_intent_20opt/english / intent

- recall: alarm_query 0/2, alarm_remove 0/3, alarm_set 0/2, audio_volume_mute 0/4, audio_volume_up 0/3, datetime_convert 0/1, datetime_query 5/8, general_greet 0/1, general_joke 1/4, general_quirky 0/2, iot_cleaning 0/4, iot_coffee 0/1, iot_hue_lightchange 0/3, iot_hue_lightdim 0/2, iot_hue_lightoff 0/4, iot_hue_lighton 0/2, iot_hue_lightup 0/1, iot_wemo_off 0/1, iot_wemo_on 1/3, music_likeness 0/3, music_query 0/1, news_query 1/9, play_music 2/17, takeaway_order 0/2, takeaway_query 1/4, weather_query 0/13
- predicted: general_joke 15, datetime_query 8, qa_maths 7, qa_factoid 7, general_greet 5, play_music 4, recommendation_events 4, iot_wemo_on 3, datetime_convert 3, calendar_query 3, lists_createoradd 3, play_game 3, audio_volume_other 2, news_query 2, lists_remove 2, audio_volume_mute 2, takeaway_query 2, email_sendemail 2, iot_wemo_off 2, calendar_set 2, music_dislikeness 2, alarm_remove 2, general_quirky 2, iot_hue_lightoff 1, qa_definition 1, recommendation_movies 1, calendar_remove 1, social_post 1, audio_volume_down 1, audio_volume_up 1, music_likeness 1, iot_cleaning 1, iot_hue_lightchange 1, music_query 1, iot_hue_lightdim 1, lists_query 1
- first listed option (most common: `qa_maths`): gold 4, predicted 4
- top confusions: weather_query→general_joke ×4, weather_query→general_greet ×3, audio_volume_mute→qa_maths ×2, iot_hue_lighton→qa_factoid ×2, iot_cleaning→general_joke ×2
- answering model (cases): english 100

### ko_klue_ynat_7_en-desc/multilingual / topic

- recall: culture_life 24/39, economy 24/34, it_science 27/30, politics 25/38, society 3/31, sports 26/33, world 27/40
- predicted: it_science 52, world 46, politics 46, economy 36, culture_life 31, sports 29, society 5
- first listed option (most common: `it_science`): gold 30, predicted 52
- top confusions: society→it_science ×10, world→politics ×9, society→politics ×8, politics→world ×7, society→economy ×6
- answering model (cases): multilingual 245

### ko_klue_ynat_7_ko-instr/multilingual / topic

- recall: culture_life 23/39, economy 28/34, it_science 25/30, politics 20/38, society 8/31, sports 26/33, world 19/40
- predicted: economy 55, it_science 41, politics 36, sports 34, world 32, culture_life 28, society 19
- first listed option (most common: `it_science`): gold 30, predicted 41
- top confusions: society→economy ×12, world→politics ×9, politics→world ×7, world→society ×6, society→it_science ×6
- answering model (cases): multilingual 245

### ko_massive_intent_20opt/multilingual / intent

- recall: alarm_query 0/2, alarm_remove 3/3, alarm_set 1/2, audio_volume_mute 3/4, audio_volume_up 1/3, datetime_convert 1/1, datetime_query 1/8, general_greet 1/1, general_joke 1/4, general_quirky 1/2, iot_cleaning 2/4, iot_coffee 0/1, iot_hue_lightchange 2/3, iot_hue_lightdim 1/2, iot_hue_lightoff 0/4, iot_hue_lighton 2/2, iot_hue_lightup 0/1, iot_wemo_off 1/1, iot_wemo_on 0/3, music_likeness 0/3, music_query 0/1, news_query 6/9, play_music 10/17, takeaway_order 1/2, takeaway_query 0/4, weather_query 9/13
- predicted: play_music 12, weather_query 9, iot_hue_lightchange 7, general_greet 6, audio_volume_mute 6, news_query 6, iot_cleaning 5, general_joke 5, iot_hue_lighton 4, iot_hue_lightup 4, takeaway_order 4, iot_wemo_off 4, iot_wemo_on 3, music_dislikeness 3, datetime_convert 3, alarm_remove 3, iot_hue_lightdim 2, audio_volume_other 2, iot_hue_lightoff 2, alarm_set 1, music_query 1, datetime_query 1, takeaway_query 1, transport_traffic 1, qa_factoid 1, calendar_query 1, music_settings 1, audio_volume_up 1, general_quirky 1
- first listed option (most common: `qa_maths`): gold 4, predicted 3
- top confusions: play_music→audio_volume_other ×2, datetime_query→general_joke ×2, iot_cleaning→iot_hue_lightchange ×2, iot_hue_lightoff→iot_cleaning ×2, audio_volume_mute→general_greet ×1
- answering model (cases): multilingual 100

### ko_massive_scenario_18_en-desc/multilingual / scenario

- recall: alarm 4/5, audio 0/4, datetime 2/3, general 0/3, iot 2/9, music 3/3, news 4/5, play 0/7, takeaway 2/5, weather 4/5
- predicted: alarm 9, music 9, iot 8, weather 5, cooking 4, news 4, takeaway 3, general 2, datetime 2, audio 1, transport 1, qa 1
- first listed option (most common: `alarm`): gold 5, predicted 9
- top confusions: play→music ×6, iot→alarm ×3, audio→alarm ×2, iot→cooking ×2, audio→cooking ×1
- answering model (cases): multilingual 49

### ko_massive_intent_20opt/typed-decisions / intent

- recall: alarm_query 0/2, alarm_remove 0/3, alarm_set 0/2, audio_volume_mute 0/4, audio_volume_up 0/3, datetime_convert 0/1, datetime_query 3/8, general_greet 0/1, general_joke 0/4, general_quirky 1/2, iot_cleaning 0/4, iot_coffee 0/1, iot_hue_lightchange 0/3, iot_hue_lightdim 0/2, iot_hue_lightoff 0/4, iot_hue_lighton 0/2, iot_hue_lightup 0/1, iot_wemo_off 0/1, iot_wemo_on 0/3, music_likeness 0/3, music_query 0/1, news_query 1/9, play_music 0/17, takeaway_order 0/2, takeaway_query 1/4, weather_query 0/13
- predicted: general_joke 15, general_greet 9, recommendation_events 7, calendar_query 6, datetime_query 5, news_query 5, calendar_set 5, lists_createoradd 5, qa_factoid 5, lists_query 4, qa_definition 3, social_post 3, music_dislikeness 3, alarm_query 2, email_sendemail 2, weather_query 2, play_audiobook 2, iot_hue_lightdim 2, general_quirky 1, iot_wemo_on 1, calendar_remove 1, audio_volume_down 1, takeaway_query 1, qa_maths 1, iot_cleaning 1, play_game 1, email_query 1, iot_hue_lightchange 1, music_query 1, datetime_convert 1, music_settings 1, lists_remove 1, audio_volume_other 1
- first listed option (most common: `qa_maths`): gold 4, predicted 8
- top confusions: weather_query→general_greet ×3, play_music→lists_createoradd ×3, iot_cleaning→general_joke ×2, play_music→general_greet ×2, play_music→recommendation_events ×2
- answering model (cases): typed-decisions 100

### en_massive_intent_20opt/english / intent

- recall: alarm_query 2/2, alarm_remove 3/3, alarm_set 2/2, audio_volume_mute 3/4, audio_volume_up 2/3, datetime_convert 1/1, datetime_query 8/8, general_greet 1/1, general_joke 4/4, general_quirky 0/2, iot_cleaning 3/4, iot_coffee 1/1, iot_hue_lightchange 1/3, iot_hue_lightdim 2/2, iot_hue_lightoff 2/4, iot_hue_lighton 0/2, iot_hue_lightup 0/1, iot_wemo_off 1/1, iot_wemo_on 3/3, music_likeness 3/3, music_query 1/1, news_query 8/9, play_music 15/17, takeaway_order 2/2, takeaway_query 2/4, weather_query 12/13
- predicted: play_music 15, weather_query 12, datetime_query 9, news_query 8, iot_hue_lightoff 5, iot_wemo_on 4, iot_cleaning 4, general_joke 4, iot_wemo_off 4, alarm_set 3, audio_volume_mute 3, alarm_remove 3, music_likeness 3, takeaway_order 3, qa_factoid 3, alarm_query 2, iot_hue_lightchange 2, iot_hue_lightdim 2, takeaway_query 2, audio_volume_up 2, general_greet 1, datetime_convert 1, transport_taxi 1, audio_volume_down 1, iot_hue_lighton 1, iot_coffee 1, music_query 1
- first listed option (most common: `qa_maths`): gold 4, predicted 4
- top confusions: iot_hue_lightchange→iot_hue_lightoff ×2, iot_hue_lighton→iot_wemo_on ×1, general_quirky→iot_hue_lightoff ×1, iot_hue_lightup→iot_hue_lightchange ×1, takeaway_query→transport_taxi ×1
- answering model (cases): english 100

### en_massive_intent_20opt/multilingual / intent

- recall: alarm_query 2/2, alarm_remove 3/3, alarm_set 2/2, audio_volume_mute 4/4, audio_volume_up 1/3, datetime_convert 0/1, datetime_query 7/8, general_greet 1/1, general_joke 4/4, general_quirky 1/2, iot_cleaning 4/4, iot_coffee 1/1, iot_hue_lightchange 2/3, iot_hue_lightdim 0/2, iot_hue_lightoff 1/4, iot_hue_lighton 1/2, iot_hue_lightup 0/1, iot_wemo_off 1/1, iot_wemo_on 1/3, music_likeness 0/3, music_query 1/1, news_query 5/9, play_music 13/17, takeaway_order 2/2, takeaway_query 1/4, weather_query 13/13
- predicted: play_music 15, weather_query 13, datetime_query 8, news_query 5, iot_hue_lightchange 5, audio_volume_mute 4, iot_cleaning 4, iot_hue_lightup 4, iot_hue_lightdim 4, general_joke 4, general_greet 3, alarm_remove 3, takeaway_order 3, alarm_set 2, iot_hue_lightoff 2, iot_hue_lighton 2, alarm_query 2, audio_volume_down 2, qa_maths 1, takeaway_query 1, transport_taxi 1, audio_volume_other 1, datetime_convert 1, iot_wemo_off 1, music_settings 1, music_dislikeness 1, iot_wemo_on 1, play_game 1, qa_factoid 1, audio_volume_up 1, iot_coffee 1, general_quirky 1, music_query 1
- first listed option (most common: `qa_maths`): gold 4, predicted 5
- top confusions: music_likeness→play_music ×2, takeaway_query→general_greet ×2, audio_volume_up→audio_volume_down ×2, news_query→iot_hue_lightchange ×2, iot_hue_lightoff→iot_hue_lightdim ×2
- answering model (cases): multilingual 100

### ko_massive_intent_20opt/router / intent

- recall: alarm_query 0/2, alarm_remove 3/3, alarm_set 1/2, audio_volume_mute 3/4, audio_volume_up 1/3, datetime_convert 1/1, datetime_query 1/8, general_greet 1/1, general_joke 1/4, general_quirky 1/2, iot_cleaning 2/4, iot_coffee 0/1, iot_hue_lightchange 2/3, iot_hue_lightdim 1/2, iot_hue_lightoff 0/4, iot_hue_lighton 2/2, iot_hue_lightup 0/1, iot_wemo_off 1/1, iot_wemo_on 0/3, music_likeness 0/3, music_query 0/1, news_query 6/9, play_music 10/17, takeaway_order 1/2, takeaway_query 0/4, weather_query 9/13
- predicted: play_music 12, weather_query 9, iot_hue_lightchange 7, general_greet 6, audio_volume_mute 6, news_query 6, iot_cleaning 5, general_joke 5, iot_hue_lighton 4, iot_hue_lightup 4, takeaway_order 4, iot_wemo_off 4, iot_wemo_on 3, music_dislikeness 3, datetime_convert 3, alarm_remove 3, iot_hue_lightdim 2, audio_volume_other 2, iot_hue_lightoff 2, alarm_set 1, music_query 1, datetime_query 1, takeaway_query 1, transport_traffic 1, qa_factoid 1, calendar_query 1, music_settings 1, audio_volume_up 1, general_quirky 1
- first listed option (most common: `qa_maths`): gold 4, predicted 3
- top confusions: play_music→audio_volume_other ×2, datetime_query→general_joke ×2, iot_cleaning→iot_hue_lightchange ×2, iot_hue_lightoff→iot_cleaning ×2, audio_volume_mute→general_greet ×1
- answering model (cases): multilingual 100

### en_massive_intent_20opt/typed-decisions / intent

- recall: alarm_query 2/2, alarm_remove 3/3, alarm_set 2/2, audio_volume_mute 3/4, audio_volume_up 1/3, datetime_convert 1/1, datetime_query 8/8, general_greet 1/1, general_joke 4/4, general_quirky 1/2, iot_cleaning 3/4, iot_coffee 1/1, iot_hue_lightchange 2/3, iot_hue_lightdim 2/2, iot_hue_lightoff 2/4, iot_hue_lighton 0/2, iot_hue_lightup 0/1, iot_wemo_off 1/1, iot_wemo_on 1/3, music_likeness 3/3, music_query 1/1, news_query 8/9, play_music 15/17, takeaway_order 2/2, takeaway_query 2/4, weather_query 13/13
- predicted: play_music 15, weather_query 13, datetime_query 9, news_query 8, iot_hue_lightdim 5, audio_volume_mute 4, iot_cleaning 4, audio_volume_down 4, general_joke 4, alarm_remove 3, music_likeness 3, iot_hue_lightchange 3, alarm_set 2, iot_hue_lightoff 2, alarm_query 2, takeaway_order 2, takeaway_query 2, iot_wemo_off 2, music_dislikeness 1, general_greet 1, datetime_convert 1, transport_taxi 1, transport_traffic 1, recommendation_locations 1, iot_wemo_on 1, iot_hue_lighton 1, lists_query 1, audio_volume_up 1, iot_coffee 1, general_quirky 1, music_query 1
- first listed option (most common: `qa_maths`): gold 4, predicted 7
- top confusions: audio_volume_up→audio_volume_down ×2, iot_hue_lightchange→music_dislikeness ×1, iot_hue_lighton→audio_volume_mute ×1, general_quirky→audio_volume_down ×1, iot_hue_lightup→iot_hue_lightchange ×1
- answering model (cases): typed-decisions 100

### ko_klue_nli_3/english / relation

- recall: contradiction 87/166, entailment 93/167, neutral 44/167
- predicted: contradiction 224, entailment 201, neutral 75
- first listed option (most common: `entailment`): gold 167, predicted 201
- top confusions: neutral→contradiction ×71, entailment→contradiction ×66, contradiction→entailment ×56, neutral→entailment ×52, contradiction→neutral ×23
- answering model (cases): english 500

### ko_klue_nli_3/multilingual / relation

- recall: contradiction 125/166, entailment 146/167, neutral 104/167
- predicted: entailment 201, contradiction 174, neutral 125
- first listed option (most common: `entailment`): gold 167, predicted 201
- top confusions: neutral→contradiction ×36, contradiction→entailment ×28, neutral→entailment ×27, entailment→contradiction ×13, contradiction→neutral ×13
- answering model (cases): multilingual 500

### ko_klue_nli_3/typed-decisions / relation

- recall: contradiction 54/166, entailment 123/167, neutral 71/167
- predicted: entailment 260, neutral 133, contradiction 107
- first listed option (most common: `entailment`): gold 167, predicted 260
- top confusions: contradiction→entailment ×72, neutral→entailment ×65, contradiction→neutral ×40, neutral→contradiction ×31, entailment→neutral ×22
- answering model (cases): typed-decisions 500

### ko_nsmc_sentiment/english / sentiment_noul

- recall: false 220/250, true 38/250
- predicted: false 432, true 68
- first listed option (most common: `true`): gold 250, predicted 68
- top confusions: true→false ×212, false→true ×30
- answering model (cases): english 500

### ko_nsmc_sentiment/english / sentiment_choice

- recall: negative 88/250, positive 176/250
- predicted: positive 338, negative 162
- first listed option (most common: `positive`): gold 250, predicted 338
- top confusions: negative→positive ×162, positive→negative ×74
- answering model (cases): english 500

### ko_nsmc_sentiment/multilingual / sentiment_noul

- recall: false 248/250, true 71/250
- predicted: false 427, true 73
- first listed option (most common: `true`): gold 250, predicted 73
- top confusions: true→false ×179, false→true ×2
- answering model (cases): multilingual 500

### ko_nsmc_sentiment/multilingual / sentiment_choice

- recall: negative 221/250, positive 166/250
- predicted: negative 305, positive 195
- first listed option (most common: `positive`): gold 250, predicted 195
- top confusions: positive→negative ×84, negative→positive ×29
- answering model (cases): multilingual 500

### ko_klue_nli_3/router / relation

- recall: contradiction 125/166, entailment 146/167, neutral 104/167
- predicted: entailment 201, contradiction 174, neutral 125
- first listed option (most common: `entailment`): gold 167, predicted 201
- top confusions: neutral→contradiction ×36, contradiction→entailment ×28, neutral→entailment ×27, entailment→contradiction ×13, contradiction→neutral ×13
- answering model (cases): multilingual 500

### ko_nsmc_sentiment/typed-decisions / sentiment_noul

- recall: false 192/250, true 74/250
- predicted: false 368, true 132
- first listed option (most common: `true`): gold 250, predicted 132
- top confusions: true→false ×176, false→true ×58
- answering model (cases): typed-decisions 500

### ko_nsmc_sentiment/typed-decisions / sentiment_choice

- recall: negative 73/250, positive 180/250
- predicted: positive 357, negative 143
- first listed option (most common: `positive`): gold 250, predicted 357
- top confusions: negative→positive ×177, positive→negative ×70
- answering model (cases): typed-decisions 500

### ko_kmhas_hate/multilingual / is_hate

- recall: false 229/250, true 62/250
- predicted: false 417, true 83
- first listed option (most common: `true`): gold 250, predicted 83
- top confusions: true→false ×188, false→true ×21
- answering model (cases): multilingual 500

### ko_nsmc_sentiment/router / sentiment_noul

- recall: false 248/250, true 72/250
- predicted: false 426, true 74
- first listed option (most common: `true`): gold 250, predicted 74
- top confusions: true→false ×178, false→true ×2
- answering model (cases): multilingual 498, english 2

### ko_nsmc_sentiment/router / sentiment_choice

- recall: negative 221/250, positive 167/250
- predicted: negative 304, positive 196
- first listed option (most common: `positive`): gold 250, predicted 196
- top confusions: positive→negative ×83, negative→positive ×29
- answering model (cases): multilingual 498, english 2

### ko_kmhas_hate/english / is_hate

- recall: false 250/250, true 0/250
- predicted: false 500
- first listed option (most common: `true`): gold 250, predicted 0
- top confusions: true→false ×250
- answering model (cases): english 500

### ko_kmhas_hate/router / is_hate

- recall: false 229/250, true 62/250
- predicted: false 417, true 83
- first listed option (most common: `true`): gold 250, predicted 83
- top confusions: true→false ×188, false→true ×21
- answering model (cases): multilingual 500

### ko_kmhas_hate/typed-decisions / is_hate

- recall: false 250/250, true 0/250
- predicted: false 500
- first listed option (most common: `true`): gold 250, predicted 0
- top confusions: true→false ×250
- answering model (cases): typed-decisions 500

### ko_kmhas_type_8/english / hate_type

- recall: age 1/65, gender 1/66, origin 58/70, physical 8/68, politics 5/72, profanity 0/69, race 0/27, religion 0/63
- predicted: origin 412, politics 42, physical 39, age 5, profanity 1, gender 1
- first listed option (most common: `origin`): gold 70, predicted 412
- top confusions: politics→origin ×62, profanity→origin ×57, gender→origin ×57, physical→origin ×55, age→origin ×52
- answering model (cases): english 500

### ko_kmhas_type_8/multilingual / hate_type

- recall: age 12/65, gender 42/66, origin 2/70, physical 15/68, politics 34/72, profanity 43/69, race 15/27, religion 34/63
- predicted: profanity 198, race 91, gender 68, politics 52, religion 44, physical 24, age 21, origin 2
- first listed option (most common: `origin`): gold 70, predicted 2
- top confusions: origin→profanity ×35, age→profanity ×30, origin→race ×26, physical→profanity ×24, religion→profanity ×22
- answering model (cases): multilingual 500

### ko_kmhas_type_8/typed-decisions / hate_type

- recall: age 4/65, gender 1/66, origin 26/70, physical 8/68, politics 47/72, profanity 0/69, race 0/27, religion 4/63
- predicted: politics 275, origin 177, physical 24, age 10, profanity 7, religion 5, gender 2
- first listed option (most common: `origin`): gold 70, predicted 177
- top confusions: physical→politics ×41, religion→politics ×38, origin→politics ×38, age→politics ×36, profanity→origin ×35
- answering model (cases): typed-decisions 500

### ko_3i4k_speechact_7/english / speech_act

- recall: command 45/71, fragment 0/72, intonation_dependent 23/71, question 2/72, rhetorical_command 2/71, rhetorical_question 14/71, statement 1/72
- predicted: command 224, intonation_dependent 162, rhetorical_question 52, fragment 30, rhetorical_command 17, question 12, statement 3
- first listed option (most common: `fragment`): gold 72, predicted 30
- top confusions: fragment→intonation_dependent ×62, question→command ×45, statement→command ×35, rhetorical_question→command ×30, intonation_dependent→command ×30
- answering model (cases): english 500

### ko_3i4k_speechact_7/multilingual / speech_act

- recall: command 3/71, fragment 14/72, intonation_dependent 27/71, question 3/72, rhetorical_command 15/71, rhetorical_question 14/71, statement 13/72
- predicted: intonation_dependent 207, fragment 100, statement 69, rhetorical_question 61, rhetorical_command 44, command 15, question 4
- first listed option (most common: `fragment`): gold 72, predicted 100
- top confusions: fragment→intonation_dependent ×49, rhetorical_question→intonation_dependent ×34, statement→intonation_dependent ×31, question→intonation_dependent ×28, command→intonation_dependent ×21
- answering model (cases): multilingual 500

### ko_kmhas_type_8/router / hate_type

- recall: age 12/65, gender 42/66, origin 2/70, physical 15/68, politics 34/72, profanity 43/69, race 15/27, religion 34/63
- predicted: profanity 198, race 91, gender 68, politics 52, religion 44, physical 24, age 21, origin 2
- first listed option (most common: `origin`): gold 70, predicted 2
- top confusions: origin→profanity ×35, age→profanity ×30, origin→race ×26, physical→profanity ×24, religion→profanity ×22
- answering model (cases): multilingual 499, english 1

### ko_3i4k_speechact_7/typed-decisions / speech_act

- recall: command 3/71, fragment 0/72, intonation_dependent 32/71, question 3/72, rhetorical_command 5/71, rhetorical_question 35/71, statement 3/72
- predicted: intonation_dependent 215, rhetorical_question 177, question 36, rhetorical_command 28, command 20, statement 15, fragment 9
- first listed option (most common: `fragment`): gold 72, predicted 9
- top confusions: fragment→intonation_dependent ×46, question→rhetorical_question ×39, command→intonation_dependent ×33, rhetorical_command→intonation_dependent ×30, statement→intonation_dependent ×28
- answering model (cases): typed-decisions 500

### ko_3i4k_speechact_7/router / speech_act

- recall: command 3/71, fragment 14/72, intonation_dependent 27/71, question 3/72, rhetorical_command 15/71, rhetorical_question 14/71, statement 13/72
- predicted: intonation_dependent 207, fragment 100, statement 69, rhetorical_question 61, rhetorical_command 44, command 15, question 4
- first listed option (most common: `fragment`): gold 72, predicted 100
- top confusions: fragment→intonation_dependent ×49, rhetorical_question→intonation_dependent ×34, statement→intonation_dependent ×31, question→intonation_dependent ×28, command→intonation_dependent ×21
- answering model (cases): multilingual 500

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1643_english_ko_massive_domain_8.json | english | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/B/20261002-1643_multilingual_ko_massive_domain_8.json | multilingual | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/B/20261002-1644_typed-decisions_ko_massive_domain_8.json | typed-decisions | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/B/20261002-1645_english_ko_klue_ynat_7.json | english | 0.3.23 | 52c1af160c0433405763a919c593afea3d4f62c51c3d893a84b6ea2610da991f | 2eec39b823fd3a6eec8d54cb1bfb8caafccd93375fe2ef33c608d232ad37f260 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 255, "dev": 245} |
| results/B/20261002-1645_multilingual_ko_klue_ynat_7.json | multilingual | 0.3.23 | 52c1af160c0433405763a919c593afea3d4f62c51c3d893a84b6ea2610da991f | 2eec39b823fd3a6eec8d54cb1bfb8caafccd93375fe2ef33c608d232ad37f260 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 255, "dev": 245} |
| results/B/20261002-1645_router_ko_massive_domain_8.json | router (auto) | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/B/20261002-1646_typed-decisions_ko_klue_ynat_7.json | typed-decisions | 0.3.23 | 52c1af160c0433405763a919c593afea3d4f62c51c3d893a84b6ea2610da991f | 2eec39b823fd3a6eec8d54cb1bfb8caafccd93375fe2ef33c608d232ad37f260 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 255, "dev": 245} |
| results/B/20261002-1647_multilingual_ko_massive_scenario_18.json | multilingual | 0.3.23 | 28694e08bfed61ee6e4cf5a02bb024c33ffb7c3228012267d4a022f3de0ac03e | 7bf1c9b1b314f6bdd03e49cbcd471106c2a7209c06407698e82bcdb182f30a44 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 51, "dev": 49} |
| results/B/20261002-1647_router_ko_klue_ynat_7.json | router (auto) | 0.3.23 | 52c1af160c0433405763a919c593afea3d4f62c51c3d893a84b6ea2610da991f | 2eec39b823fd3a6eec8d54cb1bfb8caafccd93375fe2ef33c608d232ad37f260 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 255, "dev": 245} |
| results/B/20261002-1648_english_en_massive_domain_8.json | english | 0.3.23 | c52a5f4ef33ee2eca77424de6e6b466c175910e8096f3b095f249c6180362b0a | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/B/20261002-1648_english_ko_massive_scenario_18.json | english | 0.3.23 | 28694e08bfed61ee6e4cf5a02bb024c33ffb7c3228012267d4a022f3de0ac03e | 7bf1c9b1b314f6bdd03e49cbcd471106c2a7209c06407698e82bcdb182f30a44 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 51, "dev": 49} |
| results/B/20261002-1648_multilingual_en_massive_domain_8.json | multilingual | 0.3.23 | c52a5f4ef33ee2eca77424de6e6b466c175910e8096f3b095f249c6180362b0a | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/B/20261002-1648_router_ko_massive_scenario_18.json | router (auto) | 0.3.23 | 28694e08bfed61ee6e4cf5a02bb024c33ffb7c3228012267d4a022f3de0ac03e | 7bf1c9b1b314f6bdd03e49cbcd471106c2a7209c06407698e82bcdb182f30a44 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 51, "dev": 49} |
| results/B/20261002-1648_typed-decisions_ko_massive_scenario_18.json | typed-decisions | 0.3.23 | 28694e08bfed61ee6e4cf5a02bb024c33ffb7c3228012267d4a022f3de0ac03e | 7bf1c9b1b314f6bdd03e49cbcd471106c2a7209c06407698e82bcdb182f30a44 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 51, "dev": 49} |
| results/B/20261002-1649_multilingual_ko_massive_domain_8_en-desc_dev.json | multilingual | 0.3.23 | 4be87d318fe5a933eb08f35c6c667541e68a8ebb0ab8ec3fd1944196715ecd77 | c3ab76c59d099b54016d035d4a6092ccdf81af32802542b368d7bf7121784264 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 250} |
| results/B/20261002-1649_multilingual_ko_massive_domain_8_ko-instr_dev.json | multilingual | 0.3.23 | 23c194945d9536c606c8c201a376c745a9abf4b5b7a2a5570d41b3c940b6f686 | e924d75af7fc83b50c5eeb2a446a757ed9484de5c596e05912f7d0a65b5d64f8 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 250} |
| results/B/20261002-1650_english_ko_massive_intent_20opt.json | english | 0.3.23 | 4e936ea663ba6072e8e7ab0cc5a4f22784824378ce74cb1266a8f955b4efb596 | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
| results/B/20261002-1650_multilingual_ko_klue_ynat_7_en-desc_dev.json | multilingual | 0.3.23 | 8b8735f1fbbb4353a7bab7f2f9ed379ff6e86a6757807c35527be3deeea0d099 | 76a972f1309983a590e9a2c459a4645dea8fd9b34d86a9f4956d2114d741d1f9 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 245} |
| results/B/20261002-1650_multilingual_ko_klue_ynat_7_ko-instr_dev.json | multilingual | 0.3.23 | 56df846e83b9986299bdd32c55f78613fff73f8fa57ffd697953a03bbf75eebd | da716935ac306caa48da5786cac233d7dabe4dbba8ff1bd957c9f7fa344c5c93 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 245} |
| results/B/20261002-1650_multilingual_ko_massive_intent_20opt.json | multilingual | 0.3.23 | 4e936ea663ba6072e8e7ab0cc5a4f22784824378ce74cb1266a8f955b4efb596 | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
| results/B/20261002-1650_multilingual_ko_massive_scenario_18_en-desc_dev.json | multilingual | 0.3.23 | fbd46b83f67a2f981121c3dcf6d258a825593d0f8a2eb149ce7708335c3f6715 | 233520130f429820bf54b950d333db61a991e637addf592f3925b18c0245e85e | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 49} |
| results/B/20261002-1650_typed-decisions_ko_massive_intent_20opt.json | typed-decisions | 0.3.23 | 4e936ea663ba6072e8e7ab0cc5a4f22784824378ce74cb1266a8f955b4efb596 | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
| results/B/20261002-1651_english_en_massive_intent_20opt.json | english | 0.3.23 | de461b875166c454792aba5b13ba553fdf20c8514f8acb4f2ec9e93b7a427b9a | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
| results/B/20261002-1651_multilingual_en_massive_intent_20opt.json | multilingual | 0.3.23 | de461b875166c454792aba5b13ba553fdf20c8514f8acb4f2ec9e93b7a427b9a | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
| results/B/20261002-1651_router_ko_massive_intent_20opt.json | router (auto) | 0.3.23 | 4e936ea663ba6072e8e7ab0cc5a4f22784824378ce74cb1266a8f955b4efb596 | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
| results/B/20261002-1651_typed-decisions_en_massive_intent_20opt.json | typed-decisions | 0.3.23 | de461b875166c454792aba5b13ba553fdf20c8514f8acb4f2ec9e93b7a427b9a | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
| results/B/20261002-1652_english_ko_klue_nli_3.json | english | 0.3.23 | ae2787b1350acfe99e75d33e713004b72f30435bab8edb37f24e160f842086ff | 3f131f442bc7f0fd83b45e1c06454dc27b432b063dd8af7f374cffcd823986ec | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 263, "test": 237} |
| results/B/20261002-1652_multilingual_ko_klue_nli_3.json | multilingual | 0.3.23 | ae2787b1350acfe99e75d33e713004b72f30435bab8edb37f24e160f842086ff | 3f131f442bc7f0fd83b45e1c06454dc27b432b063dd8af7f374cffcd823986ec | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 263, "test": 237} |
| results/B/20261002-1653_typed-decisions_ko_klue_nli_3.json | typed-decisions | 0.3.23 | ae2787b1350acfe99e75d33e713004b72f30435bab8edb37f24e160f842086ff | 3f131f442bc7f0fd83b45e1c06454dc27b432b063dd8af7f374cffcd823986ec | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 263, "test": 237} |
| results/B/20261002-1654_english_ko_nsmc_sentiment.json | english | 0.3.23 | 68efeccdcbcc93d8856be721af93e4275e344293b00ef8eb6646b12e40639f1d | c76e85a04f5bbbc4d45f27a81ec2d7a6bdf76cfc958d27be0ef78c0f07668a98 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 251, "dev": 249} |
| results/B/20261002-1654_multilingual_ko_nsmc_sentiment.json | multilingual | 0.3.23 | 68efeccdcbcc93d8856be721af93e4275e344293b00ef8eb6646b12e40639f1d | c76e85a04f5bbbc4d45f27a81ec2d7a6bdf76cfc958d27be0ef78c0f07668a98 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 251, "dev": 249} |
| results/B/20261002-1654_router_ko_klue_nli_3.json | router (auto) | 0.3.23 | ae2787b1350acfe99e75d33e713004b72f30435bab8edb37f24e160f842086ff | 3f131f442bc7f0fd83b45e1c06454dc27b432b063dd8af7f374cffcd823986ec | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 263, "test": 237} |
| results/B/20261002-1656_typed-decisions_ko_nsmc_sentiment.json | typed-decisions | 0.3.23 | 68efeccdcbcc93d8856be721af93e4275e344293b00ef8eb6646b12e40639f1d | c76e85a04f5bbbc4d45f27a81ec2d7a6bdf76cfc958d27be0ef78c0f07668a98 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 251, "dev": 249} |
| results/B/20261002-1657_multilingual_ko_kmhas_hate.json | multilingual | 0.3.23 | 4e15c044a81e71fcad18f90a4d8cfd3452bdb6921a401f83ba012bc1f45e72c6 | ae97133388aac00d0eb6b8707db941904acf249795e7c0b551c28adf41fec213 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 263, "dev": 237} |
| results/B/20261002-1657_router_ko_nsmc_sentiment.json | router (auto) | 0.3.23 | 68efeccdcbcc93d8856be721af93e4275e344293b00ef8eb6646b12e40639f1d | c76e85a04f5bbbc4d45f27a81ec2d7a6bdf76cfc958d27be0ef78c0f07668a98 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 251, "dev": 249} |
| results/B/20261002-1658_english_ko_kmhas_hate.json | english | 0.3.23 | 4e15c044a81e71fcad18f90a4d8cfd3452bdb6921a401f83ba012bc1f45e72c6 | ae97133388aac00d0eb6b8707db941904acf249795e7c0b551c28adf41fec213 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 263, "dev": 237} |
| results/B/20261002-1659_router_ko_kmhas_hate.json | router (auto) | 0.3.23 | 4e15c044a81e71fcad18f90a4d8cfd3452bdb6921a401f83ba012bc1f45e72c6 | ae97133388aac00d0eb6b8707db941904acf249795e7c0b551c28adf41fec213 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 263, "dev": 237} |
| results/B/20261002-1659_typed-decisions_ko_kmhas_hate.json | typed-decisions | 0.3.23 | 4e15c044a81e71fcad18f90a4d8cfd3452bdb6921a401f83ba012bc1f45e72c6 | ae97133388aac00d0eb6b8707db941904acf249795e7c0b551c28adf41fec213 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 263, "dev": 237} |
| results/B/20261002-1700_english_ko_kmhas_type_8.json | english | 0.3.23 | 5791b97163144d6ce806a790895c804bcc1031ec02ddfdbd0884eab5db4ce16c | 3d6d4f200328097ff59f023c0f4d94823aa970a1543a20ed40676c5e8759772e | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 244, "test": 256} |
| results/B/20261002-1700_multilingual_ko_kmhas_type_8.json | multilingual | 0.3.23 | 5791b97163144d6ce806a790895c804bcc1031ec02ddfdbd0884eab5db4ce16c | 3d6d4f200328097ff59f023c0f4d94823aa970a1543a20ed40676c5e8759772e | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 244, "test": 256} |
| results/B/20261002-1701_typed-decisions_ko_kmhas_type_8.json | typed-decisions | 0.3.23 | 5791b97163144d6ce806a790895c804bcc1031ec02ddfdbd0884eab5db4ce16c | 3d6d4f200328097ff59f023c0f4d94823aa970a1543a20ed40676c5e8759772e | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 244, "test": 256} |
| results/B/20261002-1703_english_ko_3i4k_speechact_7.json | english | 0.3.23 | 88e47bec5b3966b5b2747b385744ecb1d738b2e3fb2b7a186755c85d48c6f741 | bc89af6329eca2b09e2ac19c4d6f6deea507e7fb01b964bf5067822f213274e7 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 259, "dev": 241} |
| results/B/20261002-1703_multilingual_ko_3i4k_speechact_7.json | multilingual | 0.3.23 | 88e47bec5b3966b5b2747b385744ecb1d738b2e3fb2b7a186755c85d48c6f741 | bc89af6329eca2b09e2ac19c4d6f6deea507e7fb01b964bf5067822f213274e7 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 259, "dev": 241} |
| results/B/20261002-1703_router_ko_kmhas_type_8.json | router (auto) | 0.3.23 | 5791b97163144d6ce806a790895c804bcc1031ec02ddfdbd0884eab5db4ce16c | 3d6d4f200328097ff59f023c0f4d94823aa970a1543a20ed40676c5e8759772e | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 244, "test": 256} |
| results/B/20261002-1704_typed-decisions_ko_3i4k_speechact_7.json | typed-decisions | 0.3.23 | 88e47bec5b3966b5b2747b385744ecb1d738b2e3fb2b7a186755c85d48c6f741 | bc89af6329eca2b09e2ac19c4d6f6deea507e7fb01b964bf5067822f213274e7 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 259, "dev": 241} |
| results/B/20261002-1705_router_ko_3i4k_speechact_7.json | router (auto) | 0.3.23 | 88e47bec5b3966b5b2747b385744ecb1d738b2e3fb2b7a186755c85d48c6f741 | bc89af6329eca2b09e2ac19c4d6f6deea507e7fb01b964bf5067822f213274e7 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 259, "dev": 241} |
