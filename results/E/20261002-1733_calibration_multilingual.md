# Track E calibration (calibrate_ko.py)

`scripts/calibrate_ko.py --sets data/evals/ko_massive_domain_8.jsonl,data/evals/ko_klue_ynat_7.jsonl --splits results/B/B_splits.json --model models/laya-multilingual --device cpu --per-task --pooled --min-bucket-n 100 --seed 13 --reports results/B/20261002-1643_multilingual_ko_massive_domain_8.json results/B/20261002-1645_multilingual_ko_klue_ynat_7.json results/B/20261002-1654_multilingual_ko_nsmc_sentiment.json --noul-report results/B/20261002-1654_multilingual_ko_nsmc_sentiment.json --payload-fit pooled --out-payload poc/calibration/ko_v1.json --out results/E/20261002-1733_calibration_multilingual.json` (2026-10-02T17:33:21+0900)

## E1 ko_massive_domain_8 / domain (as-shipped, 15 bins of answer_confidence)

| bin | dev n | dev conf | dev acc | test n | test conf | test acc |
|---|---|---|---|---|---|---|
| (0.133, 0.200] | 0 | - | - | 1 | 0.169 | 0.000 |
| (0.200, 0.267] | 3 | 0.252 | 0.333 | 6 | 0.252 | 0.167 |
| (0.267, 0.333] | 12 | 0.308 | 0.333 | 12 | 0.300 | 0.167 |
| (0.333, 0.400] | 13 | 0.359 | 0.077 | 13 | 0.363 | 0.077 |
| (0.400, 0.467] | 10 | 0.431 | 0.200 | 12 | 0.425 | 0.167 |
| (0.467, 0.533] | 16 | 0.497 | 0.375 | 17 | 0.509 | 0.294 |
| (0.533, 0.600] | 22 | 0.568 | 0.318 | 16 | 0.568 | 0.312 |
| (0.600, 0.667] | 16 | 0.636 | 0.375 | 20 | 0.631 | 0.150 |
| (0.667, 0.733] | 13 | 0.706 | 0.154 | 6 | 0.692 | 0.167 |
| (0.733, 0.800] | 15 | 0.779 | 0.667 | 7 | 0.762 | 0.571 |
| (0.800, 0.867] | 11 | 0.832 | 0.636 | 17 | 0.838 | 0.294 |
| (0.867, 0.933] | 27 | 0.901 | 0.630 | 19 | 0.898 | 0.368 |
| (0.933, 1.000] | 92 | 0.984 | 0.837 | 104 | 0.985 | 0.837 |

ECE dev 0.200 / test 0.263 / all 0.229; mean conf − acc: dev +0.196, test +0.263 (over-confident / over-confident)

## E1 ko_klue_ynat_7 / topic (as-shipped, 15 bins of answer_confidence)

| bin | dev n | dev conf | dev acc | test n | test conf | test acc |
|---|---|---|---|---|---|---|
| (0.200, 0.267] | 0 | - | - | 1 | 0.249 | 0.000 |
| (0.267, 0.333] | 5 | 0.312 | 0.000 | 3 | 0.289 | 0.333 |
| (0.333, 0.400] | 4 | 0.355 | 0.250 | 5 | 0.363 | 0.400 |
| (0.400, 0.467] | 11 | 0.438 | 0.455 | 12 | 0.437 | 0.417 |
| (0.467, 0.533] | 10 | 0.502 | 0.500 | 22 | 0.500 | 0.318 |
| (0.533, 0.600] | 14 | 0.567 | 0.143 | 13 | 0.567 | 0.538 |
| (0.600, 0.667] | 8 | 0.625 | 0.500 | 13 | 0.640 | 0.385 |
| (0.667, 0.733] | 17 | 0.712 | 0.471 | 17 | 0.696 | 0.647 |
| (0.733, 0.800] | 20 | 0.764 | 0.550 | 9 | 0.781 | 0.556 |
| (0.800, 0.867] | 29 | 0.841 | 0.483 | 24 | 0.832 | 0.583 |
| (0.867, 0.933] | 29 | 0.898 | 0.621 | 35 | 0.902 | 0.714 |
| (0.933, 1.000] | 98 | 0.974 | 0.837 | 101 | 0.978 | 0.842 |

ECE dev 0.202 / test 0.148 / all 0.172; mean conf − acc: dev +0.200, test +0.145 (over-confident / over-confident)

## E1 ko_nsmc_sentiment / sentiment_noul (as-shipped, 15 bins of answer_confidence)

| bin | dev n | dev conf | dev acc | test n | test conf | test acc |
|---|---|---|---|---|---|---|
| (0.467, 0.533] | 6 | 0.517 | 0.500 | 1 | 0.525 | 0.000 |
| (0.533, 0.600] | 6 | 0.581 | 0.500 | 5 | 0.555 | 0.000 |
| (0.600, 0.667] | 8 | 0.624 | 0.875 | 4 | 0.619 | 0.250 |
| (0.667, 0.733] | 13 | 0.708 | 0.462 | 10 | 0.700 | 0.600 |
| (0.733, 0.800] | 12 | 0.769 | 0.083 | 12 | 0.758 | 0.833 |
| (0.800, 0.867] | 14 | 0.839 | 0.714 | 13 | 0.836 | 0.846 |
| (0.867, 0.933] | 24 | 0.911 | 0.625 | 29 | 0.904 | 0.448 |
| (0.933, 1.000] | 166 | 0.990 | 0.681 | 177 | 0.991 | 0.678 |

ECE dev 0.297 / test 0.301 / all 0.289; mean conf − acc: dev +0.281, test +0.292 (over-confident / over-confident)

## E1 ko_nsmc_sentiment / sentiment_choice (as-shipped, 15 bins of answer_confidence)

| bin | dev n | dev conf | dev acc | test n | test conf | test acc |
|---|---|---|---|---|---|---|
| (0.467, 0.533] | 6 | 0.517 | 0.667 | 6 | 0.514 | 0.500 |
| (0.533, 0.600] | 4 | 0.566 | 0.250 | 7 | 0.570 | 0.429 |
| (0.600, 0.667] | 8 | 0.644 | 0.500 | 7 | 0.633 | 0.714 |
| (0.667, 0.733] | 11 | 0.713 | 0.727 | 15 | 0.700 | 0.467 |
| (0.733, 0.800] | 8 | 0.772 | 0.750 | 13 | 0.774 | 0.692 |
| (0.800, 0.867] | 21 | 0.840 | 0.476 | 20 | 0.837 | 0.700 |
| (0.867, 0.933] | 36 | 0.904 | 0.694 | 35 | 0.902 | 0.743 |
| (0.933, 1.000] | 155 | 0.979 | 0.871 | 148 | 0.983 | 0.858 |

ECE dev 0.143 / test 0.132 / all 0.134; mean conf − acc: dev +0.135, test +0.127 (over-confident / over-confident)

## E2 refit on the dev half

Records vs Track B report (T = 1): ko_massive_domain_8 argmax 500/500, max |Δ answer_confidence| 0.0001; ko_klue_ynat_7 argmax 500/500, max |Δ answer_confidence| 0.0001

| fit | dev n | n by bucket | (i) official map: raw → applied | fitter held-out n_eval | (ii) min_n=100: bucket raw → applied |
|---|---|---|---|---|---|
| ko_massive_domain_8 | 250 | {"choice:6-10": 250} | type:choice 2.0245 → 2.0245; by_options {} | 0 | choice:6-10 2.0245 → 2.0245 |
| ko_klue_ynat_7 | 245 | {"choice:6-10": 245} | type:choice 1.8149 → 1.8149; by_options {} | 0 | choice:6-10 1.8149 → 1.8149 |
| pooled | 495 | {"choice:6-10": 495} | type:choice 1.9161 → 1.9161; by_options {} | 0 | choice:6-10 1.9161 → 1.9161 |

| fit | scored on | split | ECE as-shipped → (i) [95% CI] / (ii) | NLL as-shipped → (i) / (ii) | mean conf → (i) | accuracy |
|---|---|---|---|---|---|---|
| ko_massive_domain_8 | ko_massive_domain_8 | test | 0.263 → 0.123 [0.093, 0.178] / 0.123 | 1.727 → 1.372 / 1.372 | 0.755 → 0.565 | 0.492 |
| ko_massive_domain_8 | ko_massive_domain_8 | dev | 0.200 → 0.078 [0.068, 0.146] / 0.078 | 1.636 → 1.344 / 1.344 | 0.756 → 0.550 | 0.560 |
| ko_massive_domain_8 | ko_klue_ynat_7 | test | 0.148 → 0.082 [0.069, 0.149] / 0.082 | 1.204 → 1.052 / 1.052 | 0.800 → 0.593 | 0.655 |
| ko_massive_domain_8 | ko_klue_ynat_7 | dev | 0.202 → 0.063 [0.061, 0.134] / 0.063 | 1.306 → 1.102 / 1.102 | 0.812 → 0.594 | 0.612 |
| ko_klue_ynat_7 | ko_massive_domain_8 | test | 0.263 → 0.121 [0.095, 0.181] / 0.121 | 1.727 → 1.386 / 1.386 | 0.755 → 0.598 | 0.492 |
| ko_klue_ynat_7 | ko_massive_domain_8 | dev | 0.200 → 0.075 [0.066, 0.147] / 0.075 | 1.636 → 1.349 / 1.349 | 0.756 → 0.585 | 0.560 |
| ko_klue_ynat_7 | ko_klue_ynat_7 | test | 0.148 → 0.062 [0.055, 0.126] / 0.062 | 1.204 → 1.041 / 1.041 | 0.800 → 0.631 | 0.655 |
| ko_klue_ynat_7 | ko_klue_ynat_7 | dev | 0.202 → 0.079 [0.062, 0.145] / 0.079 | 1.306 → 1.096 / 1.096 | 0.812 → 0.634 | 0.612 |
| pooled | ko_massive_domain_8 | test | 0.263 → 0.098 [0.081, 0.162] / 0.098 | 1.727 → 1.377 / 1.377 | 0.755 → 0.582 | 0.492 |
| pooled | ko_massive_domain_8 | dev | 0.200 → 0.050 [0.056, 0.127] / 0.050 | 1.636 → 1.345 / 1.345 | 0.756 → 0.568 | 0.560 |
| pooled | ko_klue_ynat_7 | test | 0.148 → 0.063 [0.059, 0.135] / 0.063 | 1.204 → 1.045 / 1.045 | 0.800 → 0.612 | 0.655 |
| pooled | ko_klue_ynat_7 | dev | 0.202 → 0.063 [0.056, 0.133] / 0.063 | 1.306 → 1.098 / 1.098 | 0.812 → 0.614 | 0.612 |

ECE / NLL with one choice temperature T (sensitivity; the fitted T values are in the table above):

| T | ko_massive_domain_8 dev | ko_massive_domain_8 test | ko_klue_ynat_7 dev | ko_klue_ynat_7 test |
|---|---|---|---|---|
| 1.0 | 0.200 / 1.636 | 0.263 / 1.727 | 0.202 / 1.306 | 0.148 / 1.204 |
| 1.5 | 0.099 / 1.390 | 0.166 / 1.443 | 0.110 / 1.116 | 0.072 / 1.050 |
| 1.6 | 0.092 / 1.372 | 0.156 / 1.419 | 0.082 / 1.105 | 0.074 / 1.043 |
| 1.7 | 0.071 / 1.359 | 0.139 / 1.401 | 0.051 / 1.098 | 0.049 / 1.040 |
| 1.8 | 0.085 / 1.350 | 0.119 / 1.388 | 0.084 / 1.096 | 0.066 / 1.041 |
| 1.9 | 0.054 / 1.346 | 0.099 / 1.378 | 0.053 / 1.097 | 0.060 / 1.044 |
| 2.0 | 0.076 / 1.344 | 0.117 / 1.373 | 0.054 / 1.101 | 0.077 / 1.050 |
| 2.1 | 0.088 / 1.344 | 0.106 / 1.369 | 0.078 / 1.106 | 0.087 / 1.058 |
| 2.2 | 0.074 / 1.347 | 0.077 / 1.368 | 0.075 / 1.113 | 0.096 / 1.066 |
| 2.4 | 0.078 / 1.356 | 0.091 / 1.371 | 0.093 / 1.131 | 0.125 / 1.087 |
| 2.6 | 0.111 / 1.369 | 0.096 / 1.379 | 0.112 / 1.151 | 0.154 / 1.111 |
| 3.0 | 0.137 / 1.401 | 0.092 / 1.405 | 0.160 / 1.197 | 0.200 / 1.160 |

## E3 ko_massive_domain_8: test coverage / covered accuracy by gate T

| T | as-shipped | refit:ko_massive_domain_8 | refit:ko_klue_ynat_7 | refit:pooled |
|---|---|---|---|---|
| 0.50 | 0.796 / 0.583 | 0.536 / 0.709 | 0.572 / 0.692 | 0.552 / 0.696 |
| 0.55 | 0.740 / 0.595 | 0.480 / 0.758 | 0.540 / 0.704 | 0.504 / 0.738 |
| 0.60 | 0.692 / 0.618 | 0.436 / 0.807 | 0.484 / 0.752 | 0.452 / 0.796 |
| 0.65 | 0.624 / 0.673 | 0.384 / 0.854 | 0.440 / 0.809 | 0.420 / 0.829 |
| 0.70 | 0.592 / 0.696 | 0.336 / 0.869 | 0.396 / 0.838 | 0.372 / 0.860 |
| 0.75 | 0.580 / 0.703 | 0.288 / 0.917 | 0.348 / 0.874 | 0.312 / 0.910 |
| 0.80 | 0.560 / 0.707 | 0.264 / 0.924 | 0.292 / 0.918 | 0.272 / 0.926 |
| 0.85 | 0.516 / 0.736 | 0.236 / 0.932 | 0.264 / 0.924 | 0.252 / 0.937 |
| 0.90 | 0.448 / 0.804 | 0.176 / 0.977 | 0.220 / 0.964 | 0.204 / 0.980 |
| 0.95 | 0.384 / 0.833 | 0.104 / 0.962 | 0.156 / 0.974 | 0.128 / 0.969 |
| 0.99 | 0.260 / 0.923 | 0.012 / 1.000 | 0.024 / 0.833 | 0.020 / 1.000 |

| condition | budget | T chosen on dev | dev cov / err | test cov / err | test oracle max cov (T) | per-label T: dev cov / err | test cov / err |
|---|---|---|---|---|---|---|---|
| as-shipped | 0.05 | 0.9941 | 0.184 / 0.043 | 0.232 / 0.069 | 0.216 (0.9951) | 0.324 / 0.025 | 0.272 / 0.074 |
| as-shipped | 0.1 | 0.9720 | 0.284 / 0.099 | 0.300 / 0.093 | 0.304 (0.9711) | 0.420 / 0.076 | 0.364 / 0.132 |
| as-shipped | 0.15 | 0.9471 | 0.340 / 0.141 | 0.392 / 0.173 | 0.376 (0.9580) | 0.468 / 0.111 | 0.428 / 0.196 |
| refit:ko_massive_domain_8 | 0.05 | 0.8570 | 0.180 / 0.044 | 0.224 / 0.036 | 0.228 (0.8531) | 0.316 / 0.025 | 0.256 / 0.078 |
| refit:ko_massive_domain_8 | 0.1 | 0.7231 | 0.280 / 0.100 | 0.308 / 0.091 | 0.312 (0.7230) | 0.412 / 0.078 | 0.328 / 0.134 |
| refit:ko_massive_domain_8 | 0.15 | 0.6349 | 0.348 / 0.149 | 0.400 / 0.160 | 0.384 (0.6504) | 0.460 / 0.113 | 0.404 / 0.218 |
| refit:ko_klue_ynat_7 | 0.05 | 0.9002 | 0.180 / 0.044 | 0.220 / 0.036 | 0.228 (0.8973) | 0.316 / 0.025 | 0.248 / 0.081 |
| refit:ko_klue_ynat_7 | 0.1 | 0.7833 | 0.280 / 0.100 | 0.300 / 0.093 | 0.312 (0.7806) | 0.412 / 0.078 | 0.328 / 0.134 |
| refit:ko_klue_ynat_7 | 0.15 | 0.6962 | 0.348 / 0.149 | 0.400 / 0.160 | 0.384 (0.7128) | 0.460 / 0.113 | 0.400 / 0.220 |
| refit:pooled | 0.05 | 0.8799 | 0.180 / 0.044 | 0.224 / 0.036 | 0.228 (0.8765) | 0.316 / 0.025 | 0.248 / 0.081 |
| refit:pooled | 0.1 | 0.7538 | 0.280 / 0.100 | 0.308 / 0.091 | 0.312 (0.7525) | 0.412 / 0.078 | 0.328 / 0.134 |
| refit:pooled | 0.15 | 0.6657 | 0.348 / 0.149 | 0.400 / 0.160 | 0.384 (0.6818) | 0.460 / 0.113 | 0.400 / 0.220 |

Per-label T chosen on dev (None = always FALLBACK; dev predicted n in brackets):

- as-shipped, budget 0.05: communication 0.9977 [28], general None [40], info_qa 0.9985 [19], lifestyle 0.9967 [26], media 0.2847 [21], productivity 0.7953 [12], smart_home 0.9948 [66], transport 0.9438 [38]
- as-shipped, budget 0.1: communication 0.6526 [28], general None [40], info_qa 0.9985 [19], lifestyle 0.9967 [26], media 0.2847 [21], productivity 0.4019 [12], smart_home 0.9773 [66], transport 0.9115 [38]
- as-shipped, budget 0.15: communication 0.6427 [28], general None [40], info_qa 0.7717 [19], lifestyle 0.9967 [26], media 0.2847 [21], productivity 0.4019 [12], smart_home 0.9621 [66], transport 0.6942 [38]
- refit:ko_massive_domain_8, budget 0.05: communication 0.9040 [28], general None [40], info_qa 0.9159 [19], lifestyle None [26], media 0.2064 [21], productivity 0.4961 [12], smart_home 0.8230 [66], transport 0.6692 [38]
- refit:ko_massive_domain_8, budget 0.1: communication 0.5314 [28], general None [40], info_qa 0.9159 [19], lifestyle None [26], media 0.2064 [21], productivity 0.2737 [12], smart_home 0.7373 [66], transport 0.5753 [38]
- refit:ko_massive_domain_8, budget 0.15: communication 0.3758 [28], general None [40], info_qa 0.4369 [19], lifestyle None [26], media 0.2064 [21], productivity 0.2737 [12], smart_home 0.7171 [66], transport 0.4138 [38]
- refit:ko_klue_ynat_7, budget 0.05: communication 0.9302 [28], general None [40], info_qa 0.9461 [19], lifestyle None [26], media 0.2157 [21], productivity 0.5419 [12], smart_home 0.8924 [66], transport 0.7312 [38]
- refit:ko_klue_ynat_7, budget 0.1: communication 0.5801 [28], general None [40], info_qa 0.9461 [19], lifestyle None [26], media 0.2157 [21], productivity 0.2907 [12], smart_home 0.7960 [66], transport 0.6352 [38]
- refit:ko_klue_ynat_7, budget 0.15: communication 0.4098 [28], general None [40], info_qa 0.4813 [19], lifestyle None [26], media 0.2157 [21], productivity 0.2907 [12], smart_home 0.7732 [66], transport 0.4510 [38]
- refit:pooled, budget 0.05: communication 0.9135 [28], general None [40], info_qa 0.9323 [19], lifestyle None [26], media 0.2109 [21], productivity 0.5188 [12], smart_home 0.8706 [66], transport 0.7005 [38]
- refit:pooled, budget 0.1: communication 0.5556 [28], general None [40], info_qa 0.9323 [19], lifestyle None [26], media 0.2109 [21], productivity 0.2820 [12], smart_home 0.7674 [66], transport 0.6051 [38]
- refit:pooled, budget 0.15: communication 0.3924 [28], general None [40], info_qa 0.4587 [19], lifestyle None [26], media 0.2109 [21], productivity 0.2820 [12], smart_home 0.7457 [66], transport 0.4321 [38]

| refit | AUROC(answer_confidence → correct) as-shipped → refit | discordant row pairs (unrounded max p) | distinct answer_confidence values as-shipped → refit |
|---|---|---|---|
| ko_massive_domain_8 | 0.8396 → 0.8410 | 0.0241 | 212 → 248 |
| ko_klue_ynat_7 | 0.8396 → 0.8413 | 0.0211 | 212 → 247 |
| pooled | 0.8396 → 0.8406 | 0.0227 | 212 → 245 |

## E3 ko_klue_ynat_7: test coverage / covered accuracy by gate T

| T | as-shipped | refit:ko_massive_domain_8 | refit:ko_klue_ynat_7 | refit:pooled |
|---|---|---|---|---|
| 0.50 | 0.871 / 0.694 | 0.639 / 0.767 | 0.686 / 0.766 | 0.659 / 0.768 |
| 0.55 | 0.812 / 0.720 | 0.580 / 0.804 | 0.631 / 0.770 | 0.608 / 0.787 |
| 0.60 | 0.780 / 0.729 | 0.498 / 0.795 | 0.573 / 0.801 | 0.537 / 0.803 |
| 0.65 | 0.753 / 0.740 | 0.416 / 0.840 | 0.486 / 0.806 | 0.451 / 0.826 |
| 0.70 | 0.690 / 0.756 | 0.341 / 0.874 | 0.420 / 0.841 | 0.392 / 0.850 |
| 0.75 | 0.659 / 0.762 | 0.243 / 0.935 | 0.341 / 0.874 | 0.298 / 0.895 |
| 0.80 | 0.627 / 0.775 | 0.196 / 0.960 | 0.251 / 0.938 | 0.231 / 0.949 |
| 0.85 | 0.557 / 0.817 | 0.129 / 1.000 | 0.192 / 0.959 | 0.157 / 1.000 |
| 0.90 | 0.471 / 0.817 | 0.047 / 1.000 | 0.106 / 1.000 | 0.082 / 1.000 |
| 0.95 | 0.361 / 0.859 | 0.012 / 1.000 | 0.031 / 1.000 | 0.020 / 1.000 |
| 0.99 | 0.141 / 1.000 | 0.000 / - | 0.004 / 1.000 | 0.004 / 1.000 |

| condition | budget | T chosen on dev | dev cov / err | test cov / err | test oracle max cov (T) | per-label T: dev cov / err | test cov / err |
|---|---|---|---|---|---|---|---|
| as-shipped | 0.05 | 0.9910 | 0.131 / 0.031 | 0.129 / 0.000 | 0.235 (0.9776) | 0.151 / 0.000 | 0.196 / 0.160 |
| as-shipped | 0.1 | 0.9679 | 0.245 / 0.100 | 0.271 / 0.101 | 0.290 (0.9636) | 0.273 / 0.060 | 0.251 / 0.141 |
| as-shipped | 0.15 | 0.9406 | 0.367 / 0.144 | 0.384 / 0.153 | 0.380 (0.9417) | 0.449 / 0.136 | 0.412 / 0.162 |
| refit:ko_massive_domain_8 | 0.05 | 0.8044 | 0.171 / 0.048 | 0.184 / 0.043 | 0.204 (0.7965) | 0.171 / 0.000 | 0.157 / 0.075 |
| refit:ko_massive_domain_8 | 0.1 | 0.7450 | 0.249 / 0.098 | 0.255 / 0.062 | 0.282 (0.7328) | 0.302 / 0.068 | 0.263 / 0.090 |
| refit:ko_massive_domain_8 | 0.15 | 0.7153 | 0.290 / 0.141 | 0.310 / 0.127 | 0.408 (0.6602) | 0.420 / 0.136 | 0.380 / 0.134 |
| refit:ko_klue_ynat_7 | 0.05 | 0.8521 | 0.171 / 0.048 | 0.188 / 0.042 | 0.208 (0.8404) | 0.167 / 0.000 | 0.153 / 0.077 |
| refit:ko_klue_ynat_7 | 0.1 | 0.7960 | 0.249 / 0.098 | 0.259 / 0.061 | 0.282 (0.7879) | 0.298 / 0.068 | 0.267 / 0.088 |
| refit:ko_klue_ynat_7 | 0.15 | 0.7685 | 0.286 / 0.143 | 0.310 / 0.127 | 0.408 (0.7137) | 0.420 / 0.136 | 0.384 / 0.143 |
| refit:pooled | 0.05 | 0.8293 | 0.171 / 0.048 | 0.188 / 0.042 | 0.208 (0.8162) | 0.171 / 0.000 | 0.157 / 0.075 |
| refit:pooled | 0.1 | 0.7712 | 0.249 / 0.098 | 0.255 / 0.062 | 0.282 (0.7609) | 0.306 / 0.067 | 0.267 / 0.088 |
| refit:pooled | 0.15 | 0.7410 | 0.290 / 0.141 | 0.314 / 0.137 | 0.408 (0.6872) | 0.420 / 0.136 | 0.380 / 0.134 |

Per-label T chosen on dev (None = always FALLBACK; dev predicted n in brackets):

- as-shipped, budget 0.05: culture_life 0.9713 [28], economy 0.9501 [55], it_science 0.9969 [42], politics 0.9984 [35], society None [17], sports 0.9927 [35], world 0.9633 [33]
- as-shipped, budget 0.1: culture_life 0.7999 [28], economy 0.9497 [55], it_science 0.9910 [42], politics 0.9984 [35], society None [17], sports 0.9848 [35], world 0.9633 [33]
- as-shipped, budget 0.15: culture_life 0.4664 [28], economy 0.9354 [55], it_science 0.9788 [42], politics 0.9984 [35], society None [17], sports 0.7477 [35], world 0.8727 [33]
- refit:ko_massive_domain_8, budget 0.05: culture_life 0.7533 [28], economy 0.7675 [55], it_science 0.8659 [42], politics 0.9295 [35], society None [17], sports 0.8161 [35], world 0.7388 [33]
- refit:ko_massive_domain_8, budget 0.1: culture_life 0.4405 [28], economy 0.7013 [55], it_science 0.8046 [42], politics 0.9295 [35], society None [17], sports 0.7938 [35], world 0.7388 [33]
- refit:ko_massive_domain_8, budget 0.15: culture_life 0.3127 [28], economy 0.6957 [55], it_science 0.7458 [42], politics 0.9295 [35], society None [17], sports 0.4606 [35], world 0.7055 [33]
- refit:ko_klue_ynat_7, budget 0.05: culture_life 0.8048 [28], economy 0.8063 [55], it_science 0.9109 [42], politics 0.9544 [35], society None [17], sports 0.8605 [35], world 0.7897 [33]
- refit:ko_klue_ynat_7, budget 0.1: culture_life 0.4967 [28], economy 0.7496 [55], it_science 0.8521 [42], politics 0.9544 [35], society None [17], sports 0.8458 [35], world 0.7897 [33]
- refit:ko_klue_ynat_7, budget 0.15: culture_life 0.3312 [28], economy 0.7429 [55], it_science 0.8005 [42], politics 0.9544 [35], society None [17], sports 0.4962 [35], world 0.7573 [33]
- refit:pooled, budget 0.05: culture_life 0.7797 [28], economy 0.7875 [55], it_science 0.8867 [42], politics 0.9430 [35], society None [17], sports 0.8393 [35], world 0.7649 [33]
- refit:pooled, budget 0.1: culture_life 0.4601 [28], economy 0.7230 [55], it_science 0.8293 [42], politics 0.9430 [35], society None [17], sports 0.8208 [35], world 0.7649 [33]
- refit:pooled, budget 0.15: culture_life 0.3218 [28], economy 0.7207 [55], it_science 0.7738 [42], politics 0.9430 [35], society None [17], sports 0.4782 [35], world 0.7318 [33]

| refit | AUROC(answer_confidence → correct) as-shipped → refit | discordant row pairs (unrounded max p) | distinct answer_confidence values as-shipped → refit |
|---|---|---|---|
| ko_massive_domain_8 | 0.7492 → 0.7467 | 0.0442 | 245 → 248 |
| ko_klue_ynat_7 | 0.7492 → 0.7474 | 0.0382 | 245 → 253 |
| pooled | 0.7492 → 0.7469 | 0.0409 | 245 → 253 |

## E4 payload

- `poc/calibration/ko_v1.json` sha256 a217cb5d3220982e2abe7cea68572cea088df083f8bc1455d9b4716c552ec90f, fit `pooled` official map
- ko_massive_domain_8 test half: ECE via laya.load(calibration=) 0.0980 vs E2 after 0.0980, |Δ| 0.00000, pass ±0.005 = True
- max |Δ answer_confidence| reloaded vs records: 0.00000
- apply_calibration_payload on a fresh agent: identical answers = True, max |Δp| = 0.00000
- load_calibration: temperature [1.916137456893921, 1.0, 1.0], by_options {}, warnings: none
- apply_calibration_payload: temperature [1.916137456893921, 1.0, 1.0], by_options {}, warnings: none

## E6 noul threshold (sentiment_noul)

AUROC dev 0.860 / test 0.822 / all 0.841. always-no accuracy test 0.522. 2-choice variant accuracy test 0.773 / all 0.774.

| rule | threshold | dev acc | test acc | test predicted-positive rate (gold) | test precision | test recall | all acc |
|---|---|---|---|---|---|---|---|
| default 0.5 | 0.5000 | 0.635 | 0.641 | 0.135 (0.478) | 0.941 | 0.267 | 0.638 |
| Youden J (dev) | 0.0073 | 0.775 | 0.725 | 0.506 (0.478) | 0.701 | 0.742 | 0.750 |
| max accuracy (dev) | 0.0068 | 0.775 | 0.729 | 0.518 (0.478) | 0.700 | 0.758 | 0.752 |

03 E6 acceptance (Youden): {"youden_test_acc_above_always_no": true, "youden_test_pos_rate_within_5pt": true}
