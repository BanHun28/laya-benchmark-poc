# C1 option-order flip probe (2026-10-08)

`scripts/probe_option_order.py poc/finetune/data/t3arm/T1_dev40.jsonl --model poc/finetune/ckpt_t3arm/T1_run --device cpu --permutations 5 --seed 13 --split all --splits  --out results/T3arm/T1/flip_dev40.json` — 2026-10-08T11:45:38+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1_dev40 | all | 58 | 4 | 0.655 | 0.031 [0.000, 0.069] | 0.000–0.052 | 0.052 [0.000, 0.121] | 0.666 (0.655–0.672) | 0.024 | pass | no | - |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## T1_dev40 (all, n=58, 4 options)

- per-permutation flip by permutation: 0.017, 0.052, 0.052, 0.034, 0.000
- accuracy by permutation: 0.672, 0.672, 0.672, 0.655, 0.655 (original 0.655)
- identity permutations drawn: 8 of 290
- predicted labels, original: investigate 14, partial 7, human_review 7, escalate_to_human 4, approve 4, manual_review 4, observe 3, harmful 3, billing 3, delivery 2, continue 1, success 1, execute_refund 1, refund 1, answer_directly 1, request_information 1, technical 1
- predicted labels, mean per permutation: investigate 14.0, human_review 7.0, partial 6.4, escalate_to_human 4.8, approve 4.0, manual_review 4.0, observe 3.0, harmful 3.0, billing 3.0, success 1.6, delivery 1.6, technical 1.4, continue 1.0, execute_refund 1.0, refund 1.0, answer_directly 1.0, request_information 0.2
- chosen slot share under permutation (uniform 0.250): 0.264, 0.268, 0.239, 0.229; chi2 1.2, df 3, p 0.75
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.671/73, 1: 0.692/78, 2: 0.683/60, 3: 0.656/64

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| escalate_to_human | 3 | 0.267 | 0.333 | 0.333 | 0.600 |
| technical | 2 | 0.200 | 0.500 | 0.500 | 0.700 |
| partial | 3 | 0.200 | 0.333 | 1.000 | 0.800 |
| account | 1 | 0.000 | 0.000 | 0.000 | 0.000 |
| answer_directly | 2 | 0.000 | 0.000 | 0.500 | 0.500 |
| approve | 3 | 0.000 | 0.000 | 0.667 | 0.667 |
| billing | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| close_benign | 2 | 0.000 | 0.000 | 0.000 | 0.000 |
| continue | 2 | 0.000 | 0.000 | 0.500 | 0.500 |
| delivery | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| harmful | 3 | 0.000 | 0.000 | 1.000 | 1.000 |
| hold | 2 | 0.000 | 0.000 | 0.000 | 0.000 |
| human_review | 7 | 0.000 | 0.000 | 1.000 | 1.000 |
| investigate | 11 | 0.000 | 0.000 | 1.000 | 1.000 |
| manual_review | 3 | 0.000 | 0.000 | 0.333 | 0.333 |
| monitor | 1 | 0.000 | 0.000 | 0.000 | 0.000 |
| observe | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| refund | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| request_information | 2 | 0.000 | 0.000 | 0.000 | 0.000 |
| success | 5 | 0.000 | 0.000 | 0.200 | 0.200 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| request_information | 1 | 0.800 | 1.000 | 0.000 | 0.800 |
| delivery | 2 | 0.200 | 0.500 | 0.500 | 0.700 |
| partial | 7 | 0.086 | 0.143 | 0.429 | 0.343 |
| answer_directly | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| approve | 4 | 0.000 | 0.000 | 0.500 | 0.500 |
| billing | 3 | 0.000 | 0.000 | 0.667 | 0.667 |
| continue | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| escalate_to_human | 4 | 0.000 | 0.000 | 0.250 | 0.250 |
| execute_refund | 1 | 0.000 | 0.000 | 0.000 | 0.000 |
| harmful | 3 | 0.000 | 0.000 | 1.000 | 1.000 |
| human_review | 7 | 0.000 | 0.000 | 1.000 | 1.000 |
| investigate | 14 | 0.000 | 0.000 | 0.786 | 0.786 |
| manual_review | 4 | 0.000 | 0.000 | 0.250 | 0.250 |
| observe | 3 | 0.000 | 0.000 | 0.667 | 0.667 |
| refund | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| success | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| technical | 1 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.0, 0.5) | 28 | 0.050 | 0.071 | 0.536 | 0.543 |
| [0.5, 0.7) | 24 | 0.017 | 0.042 | 0.750 | 0.767 |
| [0.7, 0.9) | 3 | 0.000 | 0.000 | 0.667 | 0.667 |
| [0.9, 1.0] | 3 | 0.000 | 0.000 | 1.000 | 1.000 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-08T11:45:38+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "poc/finetune/ckpt_t3arm/T1_run", "realpath": "/Users/banhun/banhun28/lab/benchmarkforLaya/poc/finetune/ckpt_t3arm/T1_run", "snapshot_sha": null, "weights_blob": null, "head_max_len": 192, "max_len": 512} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 2.3 |
| warnings | [] |
| finished_at | 2026-10-08T11:46:26+0900 |
| total_seconds | 47.9 |
| dataset poc/finetune/data/t3arm/T1_dev40.jsonl | sha256 04f272e72cd3bf756be60e234e87f6035038213ba69717501b92f7b29a192ce8, questions_sha256 d46ef26a6ec2f2f8c6fc0cfa1e81715751dda05f173cd028ae3eaaa4b9d519cb, split rule state sha256 % 2, check null, 46s |
