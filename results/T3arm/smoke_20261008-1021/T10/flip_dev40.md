# C1 option-order flip probe (2026-10-08)

`scripts/probe_option_order.py /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/evals/T10/T10_dev40.jsonl --model /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/ckpt/T10_run --device cpu --permutations 5 --seed 13 --split all --splits  --out results/T3arm/smoke_20261008-1021/T10/flip_dev40.json` — 2026-10-08T10:35:11+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T10_dev40 | all | 8 | 10 | 0.250 | 0.100 [0.000, 0.250] | 0.000–0.250 | 0.250 [0.000, 0.500] | 0.250 (0.250–0.250) | 0.035 | pass | yes | - |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## T10_dev40 (all, n=8, 10 options)

- per-permutation flip by permutation: 0.000, 0.125, 0.125, 0.000, 0.250
- accuracy by permutation: 0.250, 0.250, 0.250, 0.250, 0.250 (original 0.250)
- identity permutations drawn: 0 of 40
- predicted labels, original: Technical Support 6, Product Support 1, Customer Service 1
- predicted labels, mean per permutation: Technical Support 5.2, Customer Service 1.2, Product Support 1.0, IT Support 0.6
- chosen slot share under permutation (uniform 0.100): 0.150, 0.075, 0.050, 0.125, 0.100, 0.125, 0.050, 0.075, 0.125, 0.125; chi2 4.5, df 9, p 0.88
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.500/4, 1: 0.250/4, 2: 0.125/8, 3: 0.000/3, 4: 0.000/1, 5: 0.250/4, 6: 0.333/3, 7: 0.000/4, 8: 0.400/5, 9: 0.500/4

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| Product Support | 1 | 0.600 | 1.000 | 0.000 | 0.000 |
| IT Support | 5 | 0.040 | 0.200 | 0.000 | 0.000 |
| Technical Support | 2 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| Technical Support | 6 | 0.133 | 0.333 | 0.333 | 0.333 |
| Customer Service | 1 | 0.000 | 0.000 | 0.000 | 0.000 |
| Product Support | 1 | 0.000 | 0.000 | 0.000 | 0.000 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.0, 0.5) | 7 | 0.114 | 0.286 | 0.286 | 0.286 |
| [0.5, 0.7) | 1 | 0.000 | 0.000 | 0.000 | 0.000 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-08T10:35:11+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "/var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T/t3arm_smoke.E01Th9/ckpt/T10_run", "realpath": "/private/var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T/t3arm_smoke.E01Th9/ckpt/T10_run", "snapshot_sha": null, "weights_blob": null, "head_max_len": 192, "max_len": 512} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 2.4 |
| warnings | [] |
| finished_at | 2026-10-08T10:35:20+0900 |
| total_seconds | 8.1 |
| dataset /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/evals/T10/T10_dev40.jsonl | sha256 5f4c7bd6e4b84e893b66ceedf474af95a75005b6332e2d838b45e6d28f96a58f, questions_sha256 8fadd3f6b2a4436087c97e0538a2d2f3a37e82051f090d83b19ee11868952a60, split rule state sha256 % 2, check null, 6s |
