# C1 option-order flip probe (2026-10-08)

`scripts/probe_option_order.py /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/evals/T1/T1_dev40.jsonl --model /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/ckpt/T1_run --device cpu --permutations 5 --seed 13 --split all --splits  --out results/T3arm/smoke_20261008-1021/T1/flip_dev40.json` — 2026-10-08T10:23:31+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1_dev40 | all | 16 | 4 | 0.375 | 0.175 [0.062, 0.338] | 0.062–0.312 | 0.438 [0.188, 0.688] | 0.338 (0.312–0.375) | 0.052 | fail | yes | - |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## T1_dev40 (all, n=16, 4 options)

- per-permutation flip by permutation: 0.250, 0.312, 0.188, 0.062, 0.062
- accuracy by permutation: 0.375, 0.312, 0.375, 0.312, 0.312 (original 0.375)
- identity permutations drawn: 3 of 80
- predicted labels, original: partial 8, observe 5, stop 2, continue 1
- predicted labels, mean per permutation: partial 8.0, observe 4.4, stop 2.8, human_review 0.6, continue 0.2
- chosen slot share under permutation (uniform 0.250): 0.212, 0.237, 0.250, 0.300; chi2 1.3, df 3, p 0.73
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.294/17, 1: 0.273/33, 2: 0.389/18, 3: 0.500/12

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| continue | 2 | 0.600 | 1.000 | 0.500 | 0.000 |
| human_review | 4 | 0.350 | 1.000 | 0.000 | 0.150 |
| observe | 2 | 0.100 | 0.500 | 1.000 | 0.900 |
| harmful | 2 | 0.000 | 0.000 | 0.000 | 0.000 |
| partial | 3 | 0.000 | 0.000 | 1.000 | 1.000 |
| success | 3 | 0.000 | 0.000 | 0.000 | 0.000 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| continue | 1 | 1.000 | 1.000 | 1.000 | 0.000 |
| observe | 5 | 0.280 | 0.800 | 0.400 | 0.440 |
| stop | 2 | 0.200 | 1.000 | 0.000 | 0.100 |
| partial | 8 | 0.000 | 0.000 | 0.375 | 0.375 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.0, 0.5) | 13 | 0.215 | 0.538 | 0.385 | 0.338 |
| [0.5, 0.7) | 3 | 0.000 | 0.000 | 0.333 | 0.333 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-08T10:23:31+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "/var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T/t3arm_smoke.E01Th9/ckpt/T1_run", "realpath": "/private/var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T/t3arm_smoke.E01Th9/ckpt/T1_run", "snapshot_sha": null, "weights_blob": null, "head_max_len": 192, "max_len": 512} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 2.8 |
| warnings | [] |
| finished_at | 2026-10-08T10:23:57+0900 |
| total_seconds | 25.3 |
| dataset /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/evals/T1/T1_dev40.jsonl | sha256 bf2750aaaf921de8ef0e7cf473fcb7956aeb341fc2985026ac8e72764c19616b, questions_sha256 419065996a0e0c02fadba913ca5dd8bf467c363464abb3beffeb3caacfc8b8e0, split rule state sha256 % 2, check null, 23s |
