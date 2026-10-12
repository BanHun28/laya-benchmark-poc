# C1 option-order flip probe (2026-10-08)

`scripts/probe_option_order.py /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/evals/T3/T3_dev40.jsonl --model /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/ckpt/T3_run --device cpu --permutations 5 --seed 13 --split all --splits  --out results/T3arm/smoke_20261008-1021/T3/flip_dev40.json` — 2026-10-08T10:25:54+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T3_dev40 | all | 8 | 6 | 0.500 | 0.000 [0.000, 0.000] | 0.000–0.000 | 0.000 [0.000, 0.000] | 0.500 (0.500–0.500) | 0.052 | pass | no | - |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## T3_dev40 (all, n=8, 6 options)

- per-permutation flip by permutation: 0.000, 0.000, 0.000, 0.000, 0.000
- accuracy by permutation: 0.500, 0.500, 0.500, 0.500, 0.500 (original 0.500)
- identity permutations drawn: 0 of 40
- predicted labels, original: joy 3, sadness 2, anger 2, surprise 1
- predicted labels, mean per permutation: joy 3.0, sadness 2.0, anger 2.0, surprise 1.0
- chosen slot share under permutation (uniform 0.167): 0.200, 0.200, 0.175, 0.175, 0.125, 0.125; chi2 1.4, df 5, p 0.92
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.714/7, 1: 0.444/9, 2: 0.500/8, 3: 0.600/5, 4: 0.167/6, 5: 0.600/5

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| anger | 4 | 0.000 | 0.000 | 0.500 | 0.500 |
| joy | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| sadness | 3 | 0.000 | 0.000 | 0.333 | 0.333 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| anger | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| joy | 3 | 0.000 | 0.000 | 0.333 | 0.333 |
| sadness | 2 | 0.000 | 0.000 | 0.500 | 0.500 |
| surprise | 1 | 0.000 | 0.000 | 0.000 | 0.000 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.7, 0.9) | 3 | 0.000 | 0.000 | 0.333 | 0.333 |
| [0.9, 1.0] | 5 | 0.000 | 0.000 | 0.600 | 0.600 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-08T10:25:54+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "/var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T/t3arm_smoke.E01Th9/ckpt/T3_run", "realpath": "/private/var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T/t3arm_smoke.E01Th9/ckpt/T3_run", "snapshot_sha": null, "weights_blob": null, "head_max_len": 192, "max_len": 512} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 2.8 |
| warnings | [] |
| finished_at | 2026-10-08T10:26:03+0900 |
| total_seconds | 8.8 |
| dataset /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/evals/T3/T3_dev40.jsonl | sha256 5482eeb31f12ae2d914b31f8d478d1ce42e040ef950c474814ac023e8478688d, questions_sha256 bd7cc49e3561bf50d45db8c2d35820b8ddea855c9dfbc081303636596b4b4c97, split rule state sha256 % 2, check null, 6s |
