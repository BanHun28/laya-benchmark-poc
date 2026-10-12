# C1 option-order flip probe (2026-10-02)

`scripts/probe_option_order.py data/evals/ko_massive_domain_8.jsonl data/evals/ko_klue_ynat_7.jsonl data/evals/ko_massive_scenario_18.jsonl --model models/laya-multilingual --device cpu --permutations 5 --seed 13 --split dev --splits results/B/B_splits.json --reference results/B/20261002-1643_multilingual_ko_massive_domain_8.json --reference results/B/20261002-1645_multilingual_ko_klue_ynat_7.json --reference results/B/20261002-1647_multilingual_ko_massive_scenario_18.json --out results/C/C1_option_order_20261002.json`(`models/`는 공개 저장소에는 포함하지 않음) — 2026-10-02T17:30:07+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ko_massive_domain_8 | dev | 250 | 8 | 0.560 | 0.270 [0.230, 0.310] | 0.244–0.288 | 0.512 [0.452, 0.572] | 0.550 (0.528–0.560) | 0.142 | fail | yes | 250/250 argmax, max abs Δp 0.0001 |
| ko_klue_ynat_7 | dev | 245 | 7 | 0.612 | 0.168 [0.135, 0.206] | 0.151–0.180 | 0.318 [0.261, 0.376] | 0.626 (0.600–0.641) | 0.097 | fail | yes | 245/245 argmax, max abs Δp 0.0001 |
| ko_massive_scenario_18 | dev | 49 | 18 | 0.551 | 0.241 [0.159, 0.327] | 0.163–0.306 | 0.469 [0.327, 0.612] | 0.510 (0.449–0.551) | 0.150 | fail | yes | 49/49 argmax, max abs Δp 0.0001 |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## ko_massive_domain_8 (dev, n=250, 8 options)

- per-permutation flip by permutation: 0.252, 0.288, 0.284, 0.280, 0.244
- accuracy by permutation: 0.556, 0.560, 0.528, 0.556, 0.548 (original 0.560)
- identity permutations drawn: 0 of 1250
- predicted labels, original: smart_home 66, general 40, transport 38, communication 28, lifestyle 26, media 21, info_qa 19, productivity 12
- predicted labels, mean per permutation: smart_home 58.6, general 37.8, transport 36.8, media 28.0, lifestyle 24.6, communication 22.8, productivity 21.8, info_qa 19.6
- chosen slot share under permutation (uniform 0.125): 0.118, 0.085, 0.138, 0.138, 0.144, 0.128, 0.118, 0.130; chi2 24.5, df 7, p 0.00092
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.519/187, 1: 0.531/130, 2: 0.628/148, 3: 0.582/146, 4: 0.552/163, 5: 0.579/152, 6: 0.503/161, 7: 0.515/163

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| lifestyle | 27 | 0.422 | 0.741 | 0.519 | 0.444 |
| info_qa | 31 | 0.413 | 0.839 | 0.323 | 0.284 |
| general | 30 | 0.407 | 0.733 | 0.367 | 0.340 |
| productivity | 33 | 0.370 | 0.636 | 0.303 | 0.333 |
| communication | 30 | 0.247 | 0.467 | 0.633 | 0.580 |
| media | 37 | 0.238 | 0.514 | 0.541 | 0.578 |
| smart_home | 30 | 0.073 | 0.167 | 0.833 | 0.867 |
| transport | 32 | 0.013 | 0.031 | 0.969 | 0.956 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| info_qa | 19 | 0.432 | 0.789 | 0.526 | 0.379 |
| lifestyle | 26 | 0.400 | 0.692 | 0.538 | 0.477 |
| general | 40 | 0.350 | 0.675 | 0.275 | 0.270 |
| productivity | 12 | 0.283 | 0.583 | 0.833 | 0.733 |
| smart_home | 66 | 0.282 | 0.530 | 0.379 | 0.461 |
| communication | 28 | 0.257 | 0.464 | 0.679 | 0.671 |
| media | 21 | 0.095 | 0.286 | 0.952 | 0.876 |
| transport | 38 | 0.095 | 0.184 | 0.816 | 0.805 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.0, 0.5) | 47 | 0.557 | 0.872 | 0.255 | 0.289 |
| [0.5, 0.7) | 50 | 0.412 | 0.800 | 0.320 | 0.348 |
| [0.7, 0.9) | 45 | 0.231 | 0.511 | 0.533 | 0.516 |
| [0.9, 1.0] | 108 | 0.094 | 0.222 | 0.815 | 0.770 |

| MASSIVE scenario (gold) | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| takeaway | 5 | 0.720 | 1.000 | 0.600 | 0.480 |
| news | 7 | 0.571 | 1.000 | 0.143 | 0.314 |
| datetime | 2 | 0.500 | 1.000 | 0.000 | 0.300 |
| social | 9 | 0.467 | 0.778 | 0.000 | 0.022 |
| lists | 7 | 0.429 | 0.429 | 0.000 | 0.143 |
| weather | 8 | 0.425 | 1.000 | 0.125 | 0.075 |
| general | 30 | 0.407 | 0.733 | 0.367 | 0.340 |
| cooking | 9 | 0.356 | 0.667 | 0.778 | 0.622 |
| recommendation | 13 | 0.354 | 0.692 | 0.308 | 0.308 |
| calendar | 20 | 0.350 | 0.650 | 0.300 | 0.330 |
| qa | 16 | 0.338 | 0.688 | 0.500 | 0.375 |
| alarm | 4 | 0.300 | 0.750 | 1.000 | 0.700 |
| audio | 6 | 0.267 | 0.833 | 0.000 | 0.200 |
| music | 6 | 0.233 | 0.333 | 0.667 | 0.800 |
| play | 25 | 0.232 | 0.480 | 0.640 | 0.616 |
| email | 21 | 0.152 | 0.333 | 0.905 | 0.819 |
| iot | 30 | 0.073 | 0.167 | 0.833 | 0.867 |
| transport | 32 | 0.013 | 0.031 | 0.969 | 0.956 |


## ko_klue_ynat_7 (dev, n=245, 7 options)

- per-permutation flip by permutation: 0.151, 0.163, 0.176, 0.171, 0.180
- accuracy by permutation: 0.633, 0.629, 0.629, 0.641, 0.600 (original 0.612)
- identity permutations drawn: 0 of 1225
- predicted labels, original: economy 55, it_science 42, politics 35, sports 35, world 33, culture_life 28, society 17
- predicted labels, mean per permutation: economy 49.2, it_science 44.8, world 39.0, politics 32.4, culture_life 32.2, sports 31.6, society 15.8
- chosen slot share under permutation (uniform 0.143): 0.137, 0.140, 0.140, 0.128, 0.160, 0.144, 0.150; chi2 5.3, df 6, p 0.51
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.570/165, 1: 0.599/182, 2: 0.582/170, 3: 0.612/165, 4: 0.648/179, 5: 0.693/179, 6: 0.670/185

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| society | 31 | 0.323 | 0.484 | 0.258 | 0.226 |
| world | 40 | 0.250 | 0.500 | 0.500 | 0.565 |
| politics | 38 | 0.205 | 0.447 | 0.500 | 0.468 |
| culture_life | 39 | 0.149 | 0.282 | 0.590 | 0.631 |
| it_science | 30 | 0.093 | 0.133 | 0.833 | 0.927 |
| sports | 33 | 0.085 | 0.152 | 0.818 | 0.752 |
| economy | 34 | 0.059 | 0.176 | 0.824 | 0.847 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| society | 17 | 0.494 | 0.824 | 0.471 | 0.400 |
| politics | 35 | 0.263 | 0.514 | 0.543 | 0.583 |
| economy | 55 | 0.200 | 0.309 | 0.509 | 0.564 |
| world | 33 | 0.133 | 0.364 | 0.606 | 0.606 |
| sports | 35 | 0.131 | 0.257 | 0.771 | 0.726 |
| it_science | 42 | 0.052 | 0.143 | 0.595 | 0.624 |
| culture_life | 28 | 0.050 | 0.071 | 0.821 | 0.843 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.0, 0.5) | 25 | 0.592 | 0.880 | 0.360 | 0.352 |
| [0.5, 0.7) | 31 | 0.329 | 0.645 | 0.290 | 0.432 |
| [0.7, 0.9) | 79 | 0.172 | 0.380 | 0.532 | 0.524 |
| [0.9, 1.0] | 110 | 0.024 | 0.055 | 0.818 | 0.816 |


## ko_massive_scenario_18 (dev, n=49, 18 options)

- per-permutation flip by permutation: 0.306, 0.245, 0.163, 0.245, 0.245
- accuracy by permutation: 0.551, 0.449, 0.490, 0.531, 0.531 (original 0.551)
- identity permutations drawn: 0 of 245
- predicted labels, original: music 10, alarm 9, weather 7, general 5, takeaway 5, news 4, iot 3, datetime 1, transport 1, calendar 1, qa 1, social 1, play 1
- predicted labels, mean per permutation: music 9.6, alarm 8.8, weather 5.6, news 4.0, iot 3.6, takeaway 3.6, general 3.4, play 2.8, qa 2.6, datetime 1.2, social 1.0, audio 1.0, transport 0.8, calendar 0.6, cooking 0.4
- chosen slot share under permutation (uniform 0.056): 0.061, 0.024, 0.053, 0.037, 0.045, 0.061, 0.069, 0.094, 0.118, 0.073, 0.065, 0.049, 0.073, 0.029, 0.053, 0.053, 0.020, 0.020; chi2 49.0, df 17, p 6.1e-05
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.692/13, 1: 0.231/13, 2: 0.438/16, 3: 0.286/14, 4: 0.455/11, 5: 0.500/12, 6: 0.400/15, 7: 0.611/18, 8: 0.600/15, 9: 0.462/13, 10: 0.556/18, 11: 0.583/12, 12: 0.591/22, 13: 0.571/7, 14: 0.529/17, 15: 0.800/10, 16: 0.333/12, 17: 0.571/7

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| general | 3 | 0.600 | 0.667 | 0.667 | 0.333 |
| audio | 4 | 0.400 | 1.000 | 0.000 | 0.100 |
| takeaway | 5 | 0.360 | 0.800 | 1.000 | 0.640 |
| iot | 9 | 0.289 | 0.556 | 0.333 | 0.333 |
| datetime | 3 | 0.267 | 0.667 | 0.333 | 0.267 |
| play | 7 | 0.200 | 0.429 | 0.143 | 0.171 |
| alarm | 5 | 0.160 | 0.200 | 0.800 | 0.880 |
| weather | 5 | 0.120 | 0.200 | 0.800 | 0.800 |
| news | 5 | 0.080 | 0.200 | 0.800 | 0.800 |
| music | 3 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| qa | 1 | 0.800 | 1.000 | 0.000 | 0.000 |
| transport | 1 | 0.600 | 1.000 | 0.000 | 0.000 |
| general | 5 | 0.480 | 0.800 | 0.400 | 0.200 |
| calendar | 1 | 0.400 | 1.000 | 0.000 | 0.200 |
| datetime | 1 | 0.400 | 1.000 | 1.000 | 0.600 |
| social | 1 | 0.400 | 1.000 | 0.000 | 0.000 |
| takeaway | 5 | 0.360 | 0.800 | 1.000 | 0.640 |
| weather | 7 | 0.229 | 0.286 | 0.571 | 0.629 |
| music | 10 | 0.160 | 0.300 | 0.300 | 0.320 |
| alarm | 9 | 0.156 | 0.444 | 0.444 | 0.533 |
| iot | 3 | 0.133 | 0.333 | 1.000 | 0.867 |
| news | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| play | 1 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.0, 0.5) | 11 | 0.600 | 1.000 | 0.273 | 0.109 |
| [0.5, 0.7) | 7 | 0.314 | 0.571 | 0.143 | 0.171 |
| [0.7, 0.9) | 9 | 0.267 | 0.667 | 0.333 | 0.311 |
| [0.9, 1.0] | 22 | 0.027 | 0.091 | 0.909 | 0.900 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-02T17:30:07+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "models/laya-multilingual", "realpath": "\~/.cache/huggingface/hub/models--convaiinnovations--laya/snapshots/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/multilingual", "snapshot_sha": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "weights_blob": "9d628fd971b700382ac6f65920a86f149777b2e748e0c955fb3b19695aa8f204", "head_max_len": 256, "max_len": 1024} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 4.2 |
| warnings | [] |
| finished_at | 2026-10-02T17:32:49+0900 |
| total_seconds | 161.9 |
| dataset data/evals/ko_massive_domain_8.jsonl | sha256 edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b, questions_sha256 a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54, split rule index parity, check {"rule": "index parity", "rows": 250, "label_distribution_match": true}, 77s |
| dataset data/evals/ko_klue_ynat_7.jsonl | sha256 52c1af160c0433405763a919c593afea3d4f62c51c3d893a84b6ea2610da991f, questions_sha256 2eec39b823fd3a6eec8d54cb1bfb8caafccd93375fe2ef33c608d232ad37f260, split rule state sha256 % 2, check {"rule": "state sha256 % 2", "rows": 245, "label_distribution_match": true}, 63s |
| dataset data/evals/ko_massive_scenario_18.jsonl | sha256 28694e08bfed61ee6e4cf5a02bb024c33ffb7c3228012267d4a022f3de0ac03e, questions_sha256 7bf1c9b1b314f6bdd03e49cbcd471106c2a7209c06407698e82bcdb182f30a44, split rule state sha256 % 2, check {"rule": "state sha256 % 2", "rows": 49, "label_distribution_match": true}, 18s |

## 판독 (수기, 생성 후 추가; 스크립트를 다시 돌리면 이 절은 사라진다)

1. **G4 미달.** router_v1(= `ko_massive_domain_8`의 `domain` 질문, 05 §4) dev 250행의 per-permutation flip은 0.270 [0.230, 0.310]이다. CI 하한도 기준 0.10의 두 배를 넘고, any-flip은 0.512다. 00 §6 판정 규칙에서 G4 미달은 조건부 Go(운영 가드 추가) 사안이다. G4 문구는 per-permutation과 any-flip 중 어느 쪽인지 정하지 않았다(00_README.md:99, 05_poc_plan.md:20). 여기서는 upstream과 비교 가능한 per-permutation으로 판정했고, any-flip 기준이면 더 큰 폭으로 미달이다.
2. **H5 지지.** 7·8·18옵션 세 세트가 모두 0.10\~0.30 범위에 든다(0.168, 0.270, 0.241).
3. **upstream 대비.** router_v1 0.270은 multilingual 20옵션 en 0.230과 Jev 0.13보다 높고, zh CS routing 0.28과 비슷하며, zh voice routing 0.106의 2.5배다. 00_README.md:99의 "≤7 옵션이면 더 낮아야 한다"는 가설은 8옵션 router_v1에서 성립하지 않는다. flip을 좌우하는 것은 옵션 수보다 클래스 경계다. transport 0.013, smart_home 0.073은 안정적이고, lifestyle 0.42, info_qa 0.41, general 0.41, productivity 0.37은 불안정하다. 이 순서는 클래스별 정확도 순서와 거의 같다.
4. **정확도는 순열에 거의 불변이다**(domain_8 0.528\~0.560, 원 순서 0.560). flip은 대부분 이미 틀린 항목에서 일어난다. domain_8의 flip 337건 중 251건(74%)이 원 순서 오답에서 출발했다(오답→오답 178, 오답→정답 73, 정답→오답 86). per-permutation flip은 원 순서 정답 항목 0.123, 오답 항목 0.456이다. 원 순서 answer_confidence ≥ 0.9인 항목(108/250)의 per-permutation flip은 0.094다. 게이트를 통과한 결정만 보면 G4 수준에 가깝다. < 0.5 구간에서는 0.557이다. YNAT의 ≥ 0.9 구간은 0.024다.
5. **위치 편향.** domain_8의 선택 슬롯 분포는 균등이 아니다(chi2 24.5, df 7, p=0.0009). 슬롯 1이 0.085로 적게 뽑히고 슬롯 2\~4가 0.138\~0.144로 많이 뽑힌다. 첫 슬롯 과예측은 없다(0.118 < 0.125). 05_poc_plan.md:232의 "첫 옵션 productivity 과예측" 의심은 기각한다. productivity는 원 순서(슬롯 0)에서 12건, 순열 평균 21.8건으로 맨 앞에서 오히려 덜 뽑힌다. YNAT에는 슬롯 편향이 없다(p=0.51). Track B의 "YNAT 첫 옵션 it_science 과예측"도 위치 효과가 아니다(dev 원 순서 42건, 순열 평균 44.8건). scenario_18은 가운데 슬롯을 선호한다(p=6e-5). 다만 답이 245개뿐이라 지표성이다.
6. **Track B의 smart_home 흡수원은 순열 뒤에도 남는다**(원 순서 66건 → 순열 평균 58.6건, gold 30). 원 순서에서 smart_home이 선호 슬롯(2)에 있던 몫이 일부 있지만 대부분은 의미 효과다. general은 40 → 37.8로 위치 효과가 거의 없다.
7. **재현성 점검.** 세 세트 모두에서 원 순서 답이 Track B laya-evals 리포트와 argmax 100% 일치한다. max abs Δp 0.0001은 반올림 수준이다. 단일 상태 호출(이 프로브)과 16행 배치(laya-evals)의 경로 차이는 결과에 영향이 없었다.

[English](C1_option_order_20261002.md) | **한국어**
