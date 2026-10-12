# C1 option-order flip probe (2026-10-08)

`scripts/probe_option_order.py poc/finetune/data/t3arm/T2_dev40.jsonl --model poc/finetune/ckpt_t3arm/T2_run --device cpu --permutations 5 --seed 13 --split all --splits  --out results/T3arm/T2/flip_dev40.json` — 2026-10-08T12:04:00+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T2_dev40 | all | 40 | 4 | 0.950 | 0.005 [0.000, 0.015] | 0.000–0.025 | 0.025 [0.000, 0.075] | 0.945 (0.925–0.950) | 0.006 | pass | no | - |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## T2_dev40 (all, n=40, 4 options)

- per-permutation flip by permutation: 0.000, 0.000, 0.000, 0.025, 0.000
- accuracy by permutation: 0.950, 0.950, 0.950, 0.925, 0.950 (original 0.950)
- identity permutations drawn: 8 of 200
- predicted labels, original: business 15, world 10, sports 8, sci_tech 7
- predicted labels, mean per permutation: business 14.8, world 10.2, sports 8.0, sci_tech 7.0
- chosen slot share under permutation (uniform 0.250): 0.270, 0.245, 0.305, 0.180; chi2 6.7, df 3, p 0.083
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.925/53, 1: 0.959/49, 2: 0.966/59, 3: 0.923/39

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| business | 17 | 0.012 | 0.059 | 0.882 | 0.871 |
| sci_tech | 7 | 0.000 | 0.000 | 1.000 | 1.000 |
| sports | 8 | 0.000 | 0.000 | 1.000 | 1.000 |
| world | 8 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| business | 15 | 0.013 | 0.067 | 1.000 | 0.987 |
| sci_tech | 7 | 0.000 | 0.000 | 1.000 | 1.000 |
| sports | 8 | 0.000 | 0.000 | 1.000 | 1.000 |
| world | 10 | 0.000 | 0.000 | 0.800 | 0.800 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.5, 0.7) | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| [0.9, 1.0] | 39 | 0.005 | 0.026 | 0.949 | 0.944 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-08T12:04:00+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "poc/finetune/ckpt_t3arm/T2_run", "realpath": "/Users/banhun/banhun28/lab/benchmarkforLaya/poc/finetune/ckpt_t3arm/T2_run", "snapshot_sha": null, "weights_blob": null, "head_max_len": 192, "max_len": 512} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 2.3 |
| warnings | [] |
| finished_at | 2026-10-08T12:04:20+0900 |
| total_seconds | 19.4 |
| dataset poc/finetune/data/t3arm/T2_dev40.jsonl | sha256 3a047a225850f42982f4aa625a82c32ba4e41f74baaa073c4c75432da9181f73, questions_sha256 c472cb1cb971dab3d01c811ccc0f997d39516555fd43f513a8c59654e0457be1, split rule state sha256 % 2, check null, 17s |
