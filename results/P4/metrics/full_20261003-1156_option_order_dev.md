# C1 option-order flip probe (2026-10-03)

`scripts/probe_option_order.py data/evals/ko_massive_domain_8.jsonl --model poc/finetune/ckpt_domain8_v1 --device cpu --permutations 5 --seed 13 --split dev --splits results/B/B_splits.json --reference results/P4/full_20261003-1156_ft-v1_ko_massive_domain_8.json --out results/P4/metrics/full_20261003-1156_option_order_dev.json` — 2026-10-03T12:39:10+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ko_massive_domain_8 | dev | 250 | 8 | 0.888 | 0.037 [0.022, 0.057] | 0.032–0.048 | 0.084 [0.052, 0.124] | 0.894 (0.884–0.904) | 0.033 | pass | no | 250/250 argmax, max abs Δp 0.0000 |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## ko_massive_domain_8 (dev, n=250, 8 options)

- per-permutation flip by permutation: 0.032, 0.048, 0.036, 0.036, 0.032
- accuracy by permutation: 0.884, 0.896, 0.888, 0.900, 0.904 (original 0.888)
- identity permutations drawn: 0 of 1250
- predicted labels, original: productivity 41, media 36, info_qa 34, transport 31, smart_home 30, communication 28, lifestyle 27, general 23
- predicted labels, mean per permutation: productivity 38.0, media 37.4, info_qa 33.6, transport 31.0, smart_home 30.0, communication 28.2, lifestyle 26.8, general 25.0
- chosen slot share under permutation (uniform 0.125): 0.143, 0.113, 0.123, 0.122, 0.121, 0.125, 0.126, 0.127; chi2 5.2, df 7, p 0.64
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.888/187, 1: 0.931/130, 2: 0.926/148, 3: 0.911/146, 4: 0.840/163, 5: 0.888/152, 6: 0.901/161, 7: 0.883/163

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| general | 30 | 0.093 | 0.267 | 0.633 | 0.660 |
| lifestyle | 27 | 0.059 | 0.111 | 0.889 | 0.881 |
| media | 37 | 0.049 | 0.054 | 0.946 | 0.973 |
| productivity | 33 | 0.042 | 0.061 | 0.939 | 0.933 |
| communication | 30 | 0.027 | 0.067 | 0.867 | 0.873 |
| smart_home | 30 | 0.013 | 0.067 | 0.967 | 0.960 |
| info_qa | 31 | 0.006 | 0.032 | 0.871 | 0.877 |
| transport | 32 | 0.006 | 0.031 | 0.969 | 0.969 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| productivity | 41 | 0.093 | 0.171 | 0.756 | 0.771 |
| general | 23 | 0.087 | 0.174 | 0.826 | 0.800 |
| info_qa | 34 | 0.035 | 0.118 | 0.794 | 0.800 |
| lifestyle | 27 | 0.030 | 0.074 | 0.889 | 0.904 |
| smart_home | 30 | 0.027 | 0.067 | 0.967 | 0.980 |
| media | 36 | 0.011 | 0.028 | 0.972 | 0.983 |
| communication | 28 | 0.007 | 0.036 | 0.929 | 0.936 |
| transport | 31 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.0, 0.5) | 17 | 0.306 | 0.647 | 0.353 | 0.376 |
| [0.5, 0.7) | 5 | 0.080 | 0.400 | 0.400 | 0.400 |
| [0.7, 0.9) | 9 | 0.289 | 0.556 | 0.444 | 0.533 |
| [0.9, 1.0] | 219 | 0.005 | 0.014 | 0.959 | 0.961 |

| MASSIVE scenario (gold) | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| music | 6 | 0.133 | 0.167 | 0.833 | 0.833 |
| recommendation | 13 | 0.108 | 0.154 | 0.769 | 0.769 |
| general | 30 | 0.093 | 0.267 | 0.633 | 0.660 |
| calendar | 20 | 0.070 | 0.100 | 0.950 | 0.940 |
| social | 9 | 0.067 | 0.111 | 0.778 | 0.778 |
| play | 25 | 0.040 | 0.040 | 0.960 | 1.000 |
| cooking | 9 | 0.022 | 0.111 | 1.000 | 0.978 |
| iot | 30 | 0.013 | 0.067 | 0.967 | 0.960 |
| qa | 16 | 0.013 | 0.062 | 0.812 | 0.825 |
| email | 21 | 0.010 | 0.048 | 0.905 | 0.914 |
| transport | 32 | 0.006 | 0.031 | 0.969 | 0.969 |
| alarm | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| audio | 6 | 0.000 | 0.000 | 1.000 | 1.000 |
| datetime | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| lists | 7 | 0.000 | 0.000 | 0.857 | 0.857 |
| news | 7 | 0.000 | 0.000 | 1.000 | 1.000 |
| takeaway | 5 | 0.000 | 0.000 | 1.000 | 1.000 |
| weather | 8 | 0.000 | 0.000 | 0.875 | 0.875 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-03T12:39:10+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "poc/finetune/ckpt_domain8_v1", "realpath": "/Users/banhun/banhun28/lab/benchmarkforLaya/poc/finetune/ckpt_domain8_v1", "snapshot_sha": null, "weights_blob": null, "head_max_len": 256, "max_len": 1024} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 3.0 |
| warnings | [] |
| finished_at | 2026-10-03T12:40:27+0900 |
| total_seconds | 76.9 |
| dataset data/evals/ko_massive_domain_8.jsonl | sha256 edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b, questions_sha256 a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54, split rule index parity, check {"rule": "index parity", "rows": 250, "label_distribution_match": true}, 74s |
