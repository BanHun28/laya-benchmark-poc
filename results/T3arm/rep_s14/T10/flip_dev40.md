# C1 option-order flip probe (2026-10-09)

`scripts/probe_option_order.py poc/finetune/data/t3arm/T10_dev40.jsonl --model poc/finetune/ckpt_t3arm_rep_s14/T10_run --device cpu --permutations 5 --seed 13 --split all --splits  --out results/T3arm/rep_s14/T10/flip_dev40.json` — 2026-10-09T00:22:44+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T10_dev40 | all | 40 | 10 | 0.400 | 0.165 [0.090, 0.250] | 0.125–0.200 | 0.425 [0.275, 0.575] | 0.390 (0.350–0.425) | 0.033 | fail | yes | - |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## T10_dev40 (all, n=40, 10 options)

- per-permutation flip by permutation: 0.125, 0.175, 0.150, 0.175, 0.200
- accuracy by permutation: 0.400, 0.425, 0.350, 0.400, 0.375 (original 0.400)
- identity permutations drawn: 0 of 200
- predicted labels, original: Technical Support 12, Customer Service 9, IT Support 5, Product Support 5, Billing and Payments 4, Service Outages and Maintenance 3, Returns and Exchanges 1, Sales and Pre-Sales 1
- predicted labels, mean per permutation: Technical Support 11.6, Customer Service 9.8, IT Support 7.0, Billing and Payments 3.8, Product Support 2.8, Service Outages and Maintenance 2.6, Returns and Exchanges 2.0, Sales and Pre-Sales 0.4
- chosen slot share under permutation (uniform 0.100): 0.105, 0.080, 0.120, 0.070, 0.070, 0.100, 0.055, 0.110, 0.145, 0.145; chi2 17.6, df 9, p 0.04
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.435/23, 1: 0.300/20, 2: 0.318/22, 3: 0.238/21, 4: 0.267/15, 5: 0.474/19, 6: 0.235/17, 7: 0.389/18, 8: 0.583/24, 9: 0.571/21

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| IT Support | 9 | 0.267 | 0.667 | 0.222 | 0.289 |
| Technical Support | 10 | 0.200 | 0.400 | 0.500 | 0.480 |
| Product Support | 8 | 0.175 | 0.375 | 0.250 | 0.200 |
| Customer Service | 2 | 0.100 | 0.500 | 0.500 | 0.400 |
| Billing and Payments | 6 | 0.067 | 0.333 | 0.667 | 0.633 |
| Returns and Exchanges | 4 | 0.050 | 0.250 | 0.250 | 0.250 |
| Service Outages and Maintenance | 1 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| Sales and Pre-Sales | 1 | 1.000 | 1.000 | 0.000 | 0.000 |
| Product Support | 5 | 0.440 | 1.000 | 0.400 | 0.360 |
| Service Outages and Maintenance | 3 | 0.133 | 0.333 | 0.333 | 0.467 |
| Technical Support | 12 | 0.133 | 0.417 | 0.417 | 0.450 |
| IT Support | 5 | 0.120 | 0.200 | 0.400 | 0.280 |
| Customer Service | 9 | 0.067 | 0.333 | 0.111 | 0.089 |
| Billing and Payments | 4 | 0.050 | 0.250 | 1.000 | 0.950 |
| Returns and Exchanges | 1 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.0, 0.5) | 34 | 0.188 | 0.471 | 0.294 | 0.288 |
| [0.7, 0.9) | 1 | 0.200 | 1.000 | 1.000 | 0.800 |
| [0.9, 1.0] | 5 | 0.000 | 0.000 | 1.000 | 1.000 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-09T00:22:44+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "poc/finetune/ckpt_t3arm_rep_s14/T10_run", "realpath": "/Users/banhun/banhun28/lab/benchmarkforLaya/poc/finetune/ckpt_t3arm_rep_s14/T10_run", "snapshot_sha": null, "weights_blob": null, "head_max_len": 192, "max_len": 512} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 2.3 |
| warnings | [] |
| finished_at | 2026-10-09T00:23:12+0900 |
| total_seconds | 28.3 |
| dataset poc/finetune/data/t3arm/T10_dev40.jsonl | sha256 33e9ff5ddbf2b83bdecfd523308319a6e84a5494e2b640a4f70d21ef7d6b6931, questions_sha256 8fadd3f6b2a4436087c97e0538a2d2f3a37e82051f090d83b19ee11868952a60, split rule state sha256 % 2, check null, 26s |
