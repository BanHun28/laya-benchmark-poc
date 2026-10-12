# C1 option-order flip probe (2026-10-08)

`scripts/probe_option_order.py poc/finetune/data/t3arm/T3_dev40.jsonl --model poc/finetune/ckpt_t3arm/T3_run --device cpu --permutations 5 --seed 13 --split all --splits  --out results/T3arm/T3/flip_dev40.json` — 2026-10-08T12:16:34+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T3_dev40 | all | 40 | 6 | 0.925 | 0.015 [0.000, 0.040] | 0.000–0.050 | 0.050 [0.000, 0.125] | 0.920 (0.900–0.925) | 0.012 | pass | no | - |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## T3_dev40 (all, n=40, 6 options)

- per-permutation flip by permutation: 0.000, 0.025, 0.050, 0.000, 0.000
- accuracy by permutation: 0.925, 0.900, 0.925, 0.925, 0.925 (original 0.925)
- identity permutations drawn: 1 of 200
- predicted labels, original: sadness 19, anger 8, love 6, joy 3, fear 3, surprise 1
- predicted labels, mean per permutation: sadness 19.2, anger 7.4, love 6.0, fear 3.4, joy 3.0, surprise 1.0
- chosen slot share under permutation (uniform 0.167): 0.160, 0.180, 0.155, 0.210, 0.145, 0.150; chi2 3.6, df 5, p 0.61
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.879/33, 1: 0.970/33, 2: 0.882/34, 3: 0.930/43, 4: 0.962/26, 5: 0.903/31

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| anger | 8 | 0.050 | 0.125 | 0.875 | 0.825 |
| sadness | 21 | 0.010 | 0.048 | 0.905 | 0.914 |
| fear | 3 | 0.000 | 0.000 | 1.000 | 1.000 |
| joy | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| love | 5 | 0.000 | 0.000 | 1.000 | 1.000 |
| surprise | 1 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| anger | 8 | 0.075 | 0.250 | 0.875 | 0.850 |
| fear | 3 | 0.000 | 0.000 | 1.000 | 1.000 |
| joy | 3 | 0.000 | 0.000 | 0.667 | 0.667 |
| love | 6 | 0.000 | 0.000 | 0.833 | 0.833 |
| sadness | 19 | 0.000 | 0.000 | 1.000 | 1.000 |
| surprise | 1 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.0, 0.5) | 1 | 0.400 | 1.000 | 1.000 | 0.600 |
| [0.7, 0.9) | 4 | 0.050 | 0.250 | 0.250 | 0.300 |
| [0.9, 1.0] | 35 | 0.000 | 0.000 | 1.000 | 1.000 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-08T12:16:34+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "poc/finetune/ckpt_t3arm/T3_run", "realpath": "/Users/banhun/banhun28/lab/benchmarkforLaya/poc/finetune/ckpt_t3arm/T3_run", "snapshot_sha": null, "weights_blob": null, "head_max_len": 192, "max_len": 512} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 2.3 |
| warnings | [] |
| finished_at | 2026-10-08T12:16:49+0900 |
| total_seconds | 15.5 |
| dataset poc/finetune/data/t3arm/T3_dev40.jsonl | sha256 bd33d92e966ca3bed2918e390b84bf1f61430c7bf54a67d51b79da99ac46d888, questions_sha256 bd7cc49e3561bf50d45db8c2d35820b8ddea855c9dfbc081303636596b4b4c97, split rule state sha256 % 2, check null, 13s |
