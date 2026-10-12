# C1 option-order flip probe (2026-10-08)

`scripts/probe_option_order.py poc/finetune/data/t3arm/T10_dev40.jsonl --model poc/finetune/ckpt_t3arm/T10_run --device cpu --permutations 5 --seed 13 --split all --splits  --out results/T3arm/T10/flip_dev40.json` — 2026-10-08T15:00:55+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T10_dev40 | all | 40 | 10 | 0.450 | 0.175 [0.105, 0.250] | 0.150–0.200 | 0.450 [0.300, 0.600] | 0.395 (0.375–0.400) | 0.030 | fail | yes | - |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## T10_dev40 (all, n=40, 10 options)

- per-permutation flip by permutation: 0.175, 0.175, 0.200, 0.150, 0.175
- accuracy by permutation: 0.400, 0.400, 0.375, 0.400, 0.400 (original 0.450)
- identity permutations drawn: 0 of 200
- predicted labels, original: Technical Support 13, Customer Service 8, IT Support 6, Billing and Payments 5, Service Outages and Maintenance 3, Product Support 2, Human Resources 1, General Inquiry 1, Returns and Exchanges 1
- predicted labels, mean per permutation: Technical Support 11.8, Customer Service 7.8, IT Support 7.2, Billing and Payments 4.0, Service Outages and Maintenance 3.2, Returns and Exchanges 2.0, Product Support 1.8, Human Resources 0.8, General Inquiry 0.8, Sales and Pre-Sales 0.6
- chosen slot share under permutation (uniform 0.100): 0.100, 0.095, 0.095, 0.105, 0.070, 0.110, 0.045, 0.100, 0.140, 0.140; chi2 14.6, df 9, p 0.1
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.304/23, 1: 0.350/20, 2: 0.455/22, 3: 0.286/21, 4: 0.267/15, 5: 0.526/19, 6: 0.118/17, 7: 0.444/18, 8: 0.583/24, 9: 0.524/21

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| Product Support | 8 | 0.250 | 0.750 | 0.250 | 0.225 |
| IT Support | 9 | 0.222 | 0.556 | 0.333 | 0.333 |
| Customer Service | 2 | 0.200 | 0.500 | 0.000 | 0.100 |
| Billing and Payments | 6 | 0.167 | 0.167 | 0.833 | 0.667 |
| Technical Support | 10 | 0.140 | 0.400 | 0.600 | 0.480 |
| Returns and Exchanges | 4 | 0.050 | 0.250 | 0.250 | 0.250 |
| Service Outages and Maintenance | 1 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| Product Support | 2 | 0.300 | 1.000 | 1.000 | 0.700 |
| IT Support | 6 | 0.267 | 0.500 | 0.500 | 0.333 |
| Billing and Payments | 5 | 0.200 | 0.200 | 1.000 | 0.800 |
| General Inquiry | 1 | 0.200 | 1.000 | 0.000 | 0.000 |
| Human Resources | 1 | 0.200 | 1.000 | 0.000 | 0.000 |
| Technical Support | 13 | 0.200 | 0.462 | 0.462 | 0.462 |
| Service Outages and Maintenance | 3 | 0.133 | 0.667 | 0.333 | 0.467 |
| Customer Service | 8 | 0.050 | 0.250 | 0.000 | 0.000 |
| Returns and Exchanges | 1 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.0, 0.5) | 34 | 0.206 | 0.529 | 0.353 | 0.288 |
| [0.9, 1.0] | 6 | 0.000 | 0.000 | 1.000 | 1.000 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-08T15:00:55+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "poc/finetune/ckpt_t3arm/T10_run", "realpath": "/Users/banhun/banhun28/lab/benchmarkforLaya/poc/finetune/ckpt_t3arm/T10_run", "snapshot_sha": null, "weights_blob": null, "head_max_len": 192, "max_len": 512} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 2.3 |
| warnings | [] |
| finished_at | 2026-10-08T15:01:24+0900 |
| total_seconds | 28.8 |
| dataset poc/finetune/data/t3arm/T10_dev40.jsonl | sha256 33e9ff5ddbf2b83bdecfd523308319a6e84a5494e2b640a4f70d21ef7d6b6931, questions_sha256 8fadd3f6b2a4436087c97e0538a2d2f3a37e82051f090d83b19ee11868952a60, split rule state sha256 % 2, check null, 26s |
