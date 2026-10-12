# C1 option-order flip probe (2026-10-06)

`scripts/probe_option_order.py data/evals/jev_cmp/T2_ag_news_40.jsonl --model models/laya --device cpu --permutations 1 --seed 13 --split all --splits  --reference results/F/jev_cmp/laya/T2_ag_news_40_english.json --out results/F/jev_cmp/T2_option_order_k1_english.json` — 2026-10-06T09:37:06+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T2_ag_news_40 | all | 40 | 4 | 0.975 | 0.000 [0.000, 0.000] | 0.000–0.000 | 0.000 [0.000, 0.000] | 0.975 (0.975–0.975) | 0.008 | pass | no | 40/40 argmax, max abs Δp 0.0000 |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## T2_ag_news_40 (all, n=40, 4 options)

- per-permutation flip by permutation: 0.000
- accuracy by permutation: 0.975 (original 0.975)
- identity permutations drawn: 2 of 40
- predicted labels, original: business 11, sci_tech 10, sports 10, world 9
- predicted labels, mean per permutation: business 11.0, sci_tech 10.0, sports 10.0, world 9.0
- chosen slot share under permutation (uniform 0.250): 0.275, 0.100, 0.375, 0.250; chi2 6.2, df 3, p 0.1
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.917/12, 1: 1.000/4, 2: 1.000/14, 3: 1.000/10

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| business | 10 | 0.000 | 0.000 | 1.000 | 1.000 |
| sci_tech | 10 | 0.000 | 0.000 | 1.000 | 1.000 |
| sports | 10 | 0.000 | 0.000 | 1.000 | 1.000 |
| world | 10 | 0.000 | 0.000 | 0.900 | 0.900 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| business | 11 | 0.000 | 0.000 | 0.909 | 0.909 |
| sci_tech | 10 | 0.000 | 0.000 | 1.000 | 1.000 |
| sports | 10 | 0.000 | 0.000 | 1.000 | 1.000 |
| world | 9 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.5, 0.7) | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| [0.7, 0.9) | 5 | 0.000 | 0.000 | 0.800 | 0.800 |
| [0.9, 1.0] | 33 | 0.000 | 0.000 | 1.000 | 1.000 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-06T09:37:06+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "models/laya", "realpath": "/Users/banhun/.cache/huggingface/hub/models--convaiinnovations--laya/snapshots/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "snapshot_sha": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "weights_blob": "891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c", "head_max_len": 192, "max_len": 512} |
| power | Now drawing from 'Battery Power' \|  -InternalBattery-0 (id=22085731)	85%; discharging; 6:31 remaining present: true |
| git_sha | null |
| load_seconds | 2.9 |
| warnings | ["/Users/banhun/banhun28/lab/benchmarkforLaya/.venv/lib/python3.12/site-packages/laya/agent.py:1869: RuntimeWarning: laya: this checkpoint ships invalid temperatures or values outside [0.5, 5]; using choice:11+=0.10058280825614929 -> 0.5. Treat confidence from the affected entries as uncalibrated."] |
| finished_at | 2026-10-06T09:37:15+0900 |
| total_seconds | 9.2 |
| dataset data/evals/jev_cmp/T2_ag_news_40.jsonl | sha256 555c7cd7d38c78d183fe884c62e1bbb102d040871bf6e66a8911269eba20fd21, questions_sha256 c472cb1cb971dab3d01c811ccc0f997d39516555fd43f513a8c59654e0457be1, split rule state sha256 % 2, check null, 6s |
