# C1 option-order flip probe (2026-10-08)

`scripts/probe_option_order.py /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/evals/T7/T7_dev40.jsonl --model /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/ckpt/T7_run --device cpu --permutations 5 --seed 13 --split all --splits  --out results/T3arm/smoke_20261008-1021/T7/flip_dev40.json` — 2026-10-08T10:31:40+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T7_dev40 | all | 8 | 10 | 0.875 | 0.125 [0.000, 0.375] | 0.125–0.125 | 0.125 [0.000, 0.375] | 0.875 (0.875–0.875) | 0.017 | fail | yes | - |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## T7_dev40 (all, n=8, 10 options)

- per-permutation flip by permutation: 0.125, 0.125, 0.125, 0.125, 0.125
- accuracy by permutation: 0.875, 0.875, 0.875, 0.875, 0.875 (original 0.875)
- identity permutations drawn: 0 of 40
- predicted labels, original: lists_remove 2, alarm_set 1, weather_query 1, general_joke 1, audio_volume_mute 1, recommendation_locations 1, iot_coffee 1
- predicted labels, mean per permutation: lists_remove 2.0, alarm_set 1.0, weather_query 1.0, general_joke 1.0, audio_volume_mute 1.0, recommendation_locations 1.0, audio_volume_other 0.6, takeaway_order 0.2, lists_query 0.2
- chosen slot share under permutation (uniform 0.100): 0.075, 0.150, 0.100, 0.075, 0.100, 0.125, 0.125, 0.025, 0.075, 0.150; chi2 5.5, df 9, p 0.79
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.667/3, 1: 1.000/5, 2: 0.800/5, 3: 0.750/4, 4: 1.000/4, 5: 1.000/5, 6: 1.000/4, 7: 0.500/2, 8: 0.750/4, 9: 1.000/4

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| email_querycontact | 1 | 1.000 | 1.000 | 0.000 | 0.000 |
| alarm_set | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| audio_volume_mute | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| general_joke | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| lists_remove | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| recommendation_locations | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| weather_query | 1 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| iot_coffee | 1 | 1.000 | 1.000 | 0.000 | 0.000 |
| alarm_set | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| audio_volume_mute | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| general_joke | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| lists_remove | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| recommendation_locations | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| weather_query | 1 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.0, 0.5) | 1 | 1.000 | 1.000 | 0.000 | 0.000 |
| [0.9, 1.0] | 7 | 0.000 | 0.000 | 1.000 | 1.000 |

| MASSIVE scenario (gold) | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| email | 1 | 1.000 | 1.000 | 0.000 | 0.000 |
| alarm | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| audio | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| general | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| lists | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| recommendation | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| weather | 1 | 0.000 | 0.000 | 1.000 | 1.000 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-08T10:31:40+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "/var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T/t3arm_smoke.E01Th9/ckpt/T7_run", "realpath": "/private/var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T/t3arm_smoke.E01Th9/ckpt/T7_run", "snapshot_sha": null, "weights_blob": null, "head_max_len": 256, "max_len": 1024} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 3.9 |
| warnings | [] |
| finished_at | 2026-10-08T10:31:47+0900 |
| total_seconds | 7.1 |
| dataset /var/folders/rr/m9ffhdw52t55qph5_8kf12200000gn/T//t3arm_smoke.E01Th9/evals/T7/T7_dev40.jsonl | sha256 8d347adae8e1bb826dfea21017a5c6bde68300a231a3f0d755cc523c65d7e679, questions_sha256 29bcfdc1bc43ff5e7077323c89e4483bc48c6c666315ce272dddc2e4eebde2e5, split rule state sha256 % 2, check null, 3s |
