# C1 option-order flip probe (2026-10-08)

`scripts/probe_option_order.py /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/evals/T4/T4_dev40.jsonl --model /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/ckpt/T4_run --device cpu --permutations 5 --seed 13 --split all --splits  --out results/T3arm/smoke_20261008-1021/T4/flip_dev40.json` — 2026-10-08T10:26:59+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T4_dev40 | all | 8 | 10 | 1.000 | 0.000 [0.000, 0.000] | 0.000–0.000 | 0.000 [0.000, 0.000] | 1.000 (1.000–1.000) | 0.021 | pass | no | - |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## T4_dev40 (all, n=8, 10 options)

- per-permutation flip by permutation: 0.000, 0.000, 0.000, 0.000, 0.000
- accuracy by permutation: 1.000, 1.000, 1.000, 1.000, 1.000 (original 1.000)
- identity permutations drawn: 0 of 40
- predicted labels, original: exchange via app 2, card linking 1, exchange rate 1, pending cash withdrawal 1, fiat currency support 1, lost or stolen card 1, contactless not working 1
- predicted labels, mean per permutation: exchange via app 2.0, card linking 1.0, exchange rate 1.0, pending cash withdrawal 1.0, fiat currency support 1.0, lost or stolen card 1.0, contactless not working 1.0
- chosen slot share under permutation (uniform 0.100): 0.075, 0.100, 0.100, 0.125, 0.050, 0.075, 0.200, 0.150, 0.025, 0.100; chi2 9.0, df 9, p 0.44
- accuracy by gold slot under permutation (slot: acc/n): 0: 1.000/3, 1: 1.000/4, 2: 1.000/4, 3: 1.000/5, 4: 1.000/2, 5: 1.000/3, 6: 1.000/8, 7: 1.000/6, 8: 1.000/1, 9: 1.000/4

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| card linking | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| contactless not working | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| exchange rate | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| exchange via app | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| fiat currency support | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| lost or stolen card | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| pending cash withdrawal | 1 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| card linking | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| contactless not working | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| exchange rate | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| exchange via app | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| fiat currency support | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| lost or stolen card | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| pending cash withdrawal | 1 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.9, 1.0] | 8 | 0.000 | 0.000 | 1.000 | 1.000 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-08T10:26:59+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "/var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T/t3arm_smoke.E01Th9/ckpt/T4_run", "realpath": "/private/var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T/t3arm_smoke.E01Th9/ckpt/T4_run", "snapshot_sha": null, "weights_blob": null, "head_max_len": 192, "max_len": 512} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 2.8 |
| warnings | [] |
| finished_at | 2026-10-08T10:27:09+0900 |
| total_seconds | 9.7 |
| dataset /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/evals/T4/T4_dev40.jsonl | sha256 39b0c89241bf1af12a955dab2c74423b6f0e1bff129e7247393cdd1a7da81e6b, questions_sha256 c2b4e5cd0076fd0ae1f29ab34e44f1386df4ca7f13a4a56ac1025250f3f54f02, split rule state sha256 % 2, check null, 7s |
