# C1 option-order flip probe (2026-10-08)

`scripts/probe_option_order.py poc/finetune/data/t3arm/T7_dev40.jsonl --model poc/finetune/ckpt_t3arm_rep_s14/T7_run --device cpu --permutations 5 --seed 13 --split all --splits  --out results/T3arm/rep_s14/T7/flip_dev40.json` — 2026-10-08T18:48:55+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T7_dev40 | all | 40 | 10 | 0.950 | 0.025 [0.005, 0.045] | 0.000–0.050 | 0.125 [0.025, 0.225] | 0.940 (0.925–0.950) | 0.024 | pass | no | - |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## T7_dev40 (all, n=40, 10 options)

- per-permutation flip by permutation: 0.050, 0.000, 0.025, 0.000, 0.050
- accuracy by permutation: 0.925, 0.950, 0.925, 0.950, 0.950 (original 0.950)
- identity permutations drawn: 0 of 200
- predicted labels, original: alarm_set 2, weather_query 2, general_joke 2, audio_volume_mute 2, lists_remove 2, recommendation_locations 2, email_querycontact 2, iot_hue_lightchange 2, datetime_convert 2, calendar_query 2, music_query 2, datetime_query 2, takeaway_order 1, iot_hue_lightup 1, music_settings 1, news_query 1, audio_volume_up 1, general_quirky 1, calendar_remove 1, transport_query 1, qa_definition 1, iot_wemo_off 1, alarm_query 1, music_likeness 1, iot_coffee 1, takeaway_query 1, calendar_set 1, lists_query 1
- predicted labels, mean per permutation: datetime_convert 2.2, alarm_set 2.0, weather_query 2.0, general_joke 2.0, audio_volume_mute 2.0, lists_remove 2.0, recommendation_locations 2.0, email_querycontact 2.0, iot_hue_lightchange 2.0, calendar_query 2.0, music_query 1.8, datetime_query 1.8, music_likeness 1.2, iot_coffee 1.2, music_settings 1.0, news_query 1.0, audio_volume_up 1.0, general_quirky 1.0, calendar_remove 1.0, transport_query 1.0, qa_definition 1.0, iot_wemo_off 1.0, alarm_query 1.0, calendar_set 1.0, lists_query 1.0, takeaway_order 0.8, iot_hue_lightup 0.8, takeaway_query 0.8, qa_stock 0.2, iot_hue_lightoff 0.2
- chosen slot share under permutation (uniform 0.100): 0.105, 0.120, 0.100, 0.110, 0.085, 0.125, 0.095, 0.060, 0.120, 0.080; chi2 7.6, df 9, p 0.57
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.913/23, 1: 1.000/21, 2: 0.870/23, 3: 0.913/23, 4: 0.933/15, 5: 0.923/26, 6: 1.000/18, 7: 0.857/14, 8: 1.000/22, 9: 1.000/15

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| iot_hue_lightoff | 1 | 0.200 | 1.000 | 0.000 | 0.200 |
| takeaway_query | 2 | 0.200 | 1.000 | 0.500 | 0.400 |
| datetime_query | 2 | 0.100 | 0.500 | 1.000 | 0.900 |
| music_query | 2 | 0.100 | 0.500 | 1.000 | 0.900 |
| alarm_query | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| alarm_set | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| audio_volume_mute | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| audio_volume_up | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| calendar_query | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| calendar_remove | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| calendar_set | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| datetime_convert | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| email_querycontact | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| general_joke | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| general_quirky | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| iot_coffee | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| iot_hue_lightchange | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| iot_wemo_off | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| lists_query | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| lists_remove | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| music_likeness | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| music_settings | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| news_query | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| qa_definition | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| recommendation_locations | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| transport_query | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| weather_query | 2 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| iot_hue_lightup | 1 | 0.200 | 1.000 | 0.000 | 0.200 |
| takeaway_order | 1 | 0.200 | 1.000 | 0.000 | 0.000 |
| takeaway_query | 1 | 0.200 | 1.000 | 1.000 | 0.800 |
| datetime_query | 2 | 0.100 | 0.500 | 1.000 | 0.900 |
| music_query | 2 | 0.100 | 0.500 | 1.000 | 0.900 |
| alarm_query | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| alarm_set | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| audio_volume_mute | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| audio_volume_up | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| calendar_query | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| calendar_remove | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| calendar_set | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| datetime_convert | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| email_querycontact | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| general_joke | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| general_quirky | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| iot_coffee | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| iot_hue_lightchange | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| iot_wemo_off | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| lists_query | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| lists_remove | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| music_likeness | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| music_settings | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| news_query | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| qa_definition | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| recommendation_locations | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| transport_query | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| weather_query | 2 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.0, 0.5) | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| [0.7, 0.9) | 2 | 0.100 | 0.500 | 0.500 | 0.600 |
| [0.9, 1.0] | 36 | 0.022 | 0.111 | 0.972 | 0.956 |

| MASSIVE scenario (gold) | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| takeaway | 2 | 0.200 | 1.000 | 0.500 | 0.400 |
| datetime | 4 | 0.050 | 0.250 | 1.000 | 0.950 |
| music | 4 | 0.050 | 0.250 | 1.000 | 0.950 |
| iot | 5 | 0.040 | 0.200 | 0.800 | 0.840 |
| alarm | 3 | 0.000 | 0.000 | 1.000 | 1.000 |
| audio | 3 | 0.000 | 0.000 | 1.000 | 1.000 |
| calendar | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| email | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| general | 3 | 0.000 | 0.000 | 1.000 | 1.000 |
| lists | 3 | 0.000 | 0.000 | 1.000 | 1.000 |
| news | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| qa | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| recommendation | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| transport | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| weather | 2 | 0.000 | 0.000 | 1.000 | 1.000 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-08T18:48:55+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "poc/finetune/ckpt_t3arm_rep_s14/T7_run", "realpath": "/Users/banhun/banhun28/lab/benchmarkforLaya/poc/finetune/ckpt_t3arm_rep_s14/T7_run", "snapshot_sha": null, "weights_blob": null, "head_max_len": 256, "max_len": 1024} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 4.1 |
| warnings | [] |
| finished_at | 2026-10-08T18:49:11+0900 |
| total_seconds | 16.5 |
| dataset poc/finetune/data/t3arm/T7_dev40.jsonl | sha256 594d7e9b0fd7a045e74816a292f423abbc22d03f963d0a85609de96949376113, questions_sha256 7e873767665bac17b6b9f2f3564b2d59d5b504a2b06c959873d1bdeb61ad8b91, split rule state sha256 % 2, check null, 12s |
