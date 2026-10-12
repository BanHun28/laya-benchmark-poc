# C1 option-order flip probe (2026-10-03)

`scripts/probe_option_order.py data/evals/ko_massive_domain_8.jsonl --model results/P4/smoke_full/ckpt_20261003-1148 --device cpu --permutations 5 --seed 13 --split dev --splits results/B/B_splits.json --reference results/P4/smoke_full/smoke_20261003-1148_ft-smoke_ko_massive_domain_8.json --out results/P4/smoke_full/metrics/smoke_20261003-1148_option_order_dev.json` — 2026-10-03T11:53:39+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ko_massive_domain_8 | dev | 250 | 8 | 0.592 | 0.261 [0.224, 0.301] | 0.208–0.296 | 0.512 [0.448, 0.572] | 0.590 (0.580–0.604) | 0.129 | fail | yes | 250/250 argmax, max abs Δp 0.0001 |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## ko_massive_domain_8 (dev, n=250, 8 options)

- per-permutation flip by permutation: 0.264, 0.296, 0.272, 0.264, 0.208
- accuracy by permutation: 0.580, 0.584, 0.584, 0.604, 0.596 (original 0.592)
- identity permutations drawn: 0 of 1250
- predicted labels, original: info_qa 41, transport 41, lifestyle 36, general 33, communication 30, smart_home 27, productivity 22, media 20
- predicted labels, mean per permutation: general 36.6, productivity 36.6, transport 36.4, info_qa 35.2, smart_home 28.8, lifestyle 26.8, media 26.2, communication 23.4
- chosen slot share under permutation (uniform 0.125): 0.132, 0.102, 0.145, 0.140, 0.146, 0.128, 0.102, 0.105; chi2 26.0, df 7, p 0.0005
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.610/187, 1: 0.577/130, 2: 0.689/148, 3: 0.610/146, 4: 0.595/163, 5: 0.605/152, 6: 0.509/161, 7: 0.528/163

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| general | 30 | 0.400 | 0.700 | 0.300 | 0.393 |
| info_qa | 31 | 0.394 | 0.774 | 0.548 | 0.471 |
| productivity | 33 | 0.309 | 0.576 | 0.455 | 0.515 |
| media | 37 | 0.308 | 0.514 | 0.541 | 0.611 |
| lifestyle | 27 | 0.259 | 0.630 | 0.593 | 0.489 |
| communication | 30 | 0.233 | 0.467 | 0.667 | 0.587 |
| smart_home | 30 | 0.120 | 0.333 | 0.700 | 0.693 |
| transport | 32 | 0.056 | 0.125 | 0.938 | 0.931 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| info_qa | 41 | 0.420 | 0.829 | 0.415 | 0.429 |
| general | 33 | 0.358 | 0.576 | 0.273 | 0.321 |
| lifestyle | 36 | 0.350 | 0.694 | 0.444 | 0.456 |
| communication | 30 | 0.273 | 0.500 | 0.667 | 0.680 |
| productivity | 22 | 0.182 | 0.500 | 0.682 | 0.655 |
| transport | 41 | 0.171 | 0.317 | 0.732 | 0.707 |
| smart_home | 27 | 0.104 | 0.259 | 0.778 | 0.763 |
| media | 20 | 0.080 | 0.200 | 1.000 | 0.920 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.0, 0.5) | 49 | 0.567 | 0.918 | 0.204 | 0.290 |
| [0.5, 0.7) | 57 | 0.389 | 0.754 | 0.368 | 0.379 |
| [0.7, 0.9) | 34 | 0.259 | 0.588 | 0.618 | 0.559 |
| [0.9, 1.0] | 110 | 0.058 | 0.182 | 0.873 | 0.842 |

| MASSIVE scenario (gold) | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| audio | 6 | 0.600 | 0.667 | 0.000 | 0.367 |
| news | 7 | 0.571 | 1.000 | 0.429 | 0.343 |
| social | 9 | 0.511 | 0.778 | 0.111 | 0.022 |
| datetime | 2 | 0.500 | 1.000 | 0.000 | 0.300 |
| lists | 7 | 0.429 | 0.714 | 0.286 | 0.314 |
| general | 30 | 0.400 | 0.700 | 0.300 | 0.393 |
| weather | 8 | 0.350 | 0.750 | 0.375 | 0.400 |
| qa | 16 | 0.338 | 0.688 | 0.688 | 0.562 |
| recommendation | 13 | 0.323 | 0.692 | 0.308 | 0.277 |
| calendar | 20 | 0.310 | 0.600 | 0.450 | 0.510 |
| play | 25 | 0.256 | 0.480 | 0.640 | 0.640 |
| music | 6 | 0.233 | 0.500 | 0.667 | 0.733 |
| cooking | 9 | 0.200 | 0.667 | 0.889 | 0.711 |
| takeaway | 5 | 0.200 | 0.400 | 0.800 | 0.640 |
| iot | 30 | 0.120 | 0.333 | 0.700 | 0.693 |
| email | 21 | 0.114 | 0.333 | 0.905 | 0.829 |
| transport | 32 | 0.056 | 0.125 | 0.938 | 0.931 |
| alarm | 4 | 0.000 | 0.000 | 1.000 | 1.000 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-03T11:53:39+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "results/P4/smoke_full/ckpt_20261003-1148", "realpath": "/Users/banhun/banhun28/lab/benchmarkforLaya/results/P4/smoke_full/ckpt_20261003-1148", "snapshot_sha": null, "weights_blob": null, "head_max_len": 256, "max_len": 1024} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 3.1 |
| warnings | [] |
| finished_at | 2026-10-03T11:54:56+0900 |
| total_seconds | 77.1 |
| dataset data/evals/ko_massive_domain_8.jsonl | sha256 edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b, questions_sha256 a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54, split rule index parity, check {"rule": "index parity", "rows": 250, "label_distribution_match": true}, 74s |
