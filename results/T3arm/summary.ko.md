# 3-arm 비교 종합: Jev vs vanilla Laya vs trained Laya (S3, 2026-10-12 13:50)

> Jev는 독립 제3자 플레이그라운드 경유 기록(`results/F/jev_cmp/`, 이 종합은 새 요청 없음)이다. T1-T8은 F 종합의 값이고, T9·T10은 세션 S7(`results/F/jev_cmp/sessions/S7_20261008`)의 기록(공개 저장소에는 포함하지 않음)을 같은 함수로 계산했다. vanilla는 trained와 같은 base(영어 과제 english, T7 multilingual)를 학습 없이 쓴다. vanilla + 과제 T는 vanilla에 과제 calib로 맞춘 temperature만 넣은 보정 분리 열이다(§4). trained는 과제 라벨로 과제마다 따로 파인튜닝한 Laya라 zero-shot이 아니라 전문화 비교다(라벨 수와 학습 시간은 §5). §1-§6의 trained는 run 1(본 학습)이고 반복 학습 run 2는 §7이다. 이 문서의 수치는 `summary.json`과 같고 `t3arm_summary.py verify`가 대조한다.

**상태.** `results/T3arm/run_all_status.log`의 마지막 줄은 `RUN_ALL FINISHED`다. 결과 있는 과제 10개(T1, T2, T3, T4, T5, T6, T7, T8, T9, T10), 결과 없음 0개(-). 결과 없는 과제는 표에 "결과 없음"으로 두고 검정과 집계에서 뺐다.

**반복 학습(§7).** `results/T3arm/rep_s14/run_all_status.log`의 마지막 줄은 `RUN_ALL FINISHED`다. 결과 있는 과제 10개(T1, T2, T3, T4, T5, T6, T7, T8, T9, T10), 결과 없음 0개(-).

## 1. Jev 항목 3-arm 비교 (Q2)

### 1.1 종합 표

| 과제 | 범주 | n | Jev | vanilla | trained | trained vs Jev: b/c, p (Holm p) | trained vs vanilla: b/c, p (Holm p) | Jev vs vanilla: b/c, p (Holm p) | 판정 (Holm 후): trained vs Jev / trained vs vanilla / Jev vs vanilla |
|---|---|---|---|---|---|---|---|---|---|
| T1 typed-decisions | 제외 | 120 (40 case) | 104/120 = 0.867 [0.794, 0.916] | 46/120 = 0.383 [0.301, 0.473] | 95/120 = 0.792 [0.711, 0.855] | 10/19, 0.1360 (0.9523) | 56/7, 1.4e-10 (1.4e-09) | 66/8, 1.8e-12 (1.8e-11) | 비유의 (비유의) / trained 유의 우세 (trained 유의 우세) / Jev 유의 우세 (Jev 유의 우세) |
| T2 AG News | 포함 | 40 | 35/40 = 0.875 [0.739, 0.945] | 39/40 = 0.975 [0.871, 0.996] | 38/40 = 0.950 [0.835, 0.986] | 3/0, 0.2500 (1.0000) | 0/1, 1.0000 (1.0000) | 0/4, 0.1250 (0.6250) | 비유의 (비유의) / 비유의 (비유의) / 비유의 (비유의) |
| T3 DAIR Emotion | 제외 | 40 | 28/40 = 0.700 [0.546, 0.819] | 30/40 = 0.750 [0.598, 0.858] | 38/40 = 0.950 [0.835, 0.986] | 11/1, 0.0063 (0.0635) | 10/2, 0.0386 (0.2314) | 2/4, 0.6875 (1.0000) | trained 유의 우세 (비유의) / trained 유의 우세 (비유의) / 비유의 (비유의) |
| T4 Banking77-10 | 제외 | 40 | 37/40 = 0.925 [0.801, 0.974] | 29/40 = 0.725 [0.572, 0.839] | 38/40 = 0.950 [0.835, 0.986] | 3/2, 1.0000 (1.0000) | 9/0, 0.0039 (0.0312) | 9/1, 0.0215 (0.1719) | 비유의 (비유의) / trained 유의 우세 (trained 유의 우세) / Jev 유의 우세 (비유의) |
| T5 BoolQ | 포함 | 40 | 37/40 = 0.925 [0.801, 0.974] | 29/40 = 0.725 [0.572, 0.839] | 31/40 = 0.775 [0.625, 0.877] | 2/8, 0.1094 (0.8750) | 2/0, 0.5000 (1.0000) | 9/1, 0.0215 (0.1719) | 비유의 (비유의) / 비유의 (비유의) / Jev 유의 우세 (비유의) |
| T6 SST-5 | 제외 | 40 | 26/40 = 0.650 [0.495, 0.779] | 17/40 = 0.425 [0.285, 0.578] | 27/40 = 0.675 [0.520, 0.799] | 6/5, 1.0000 (1.0000) | 16/6, 0.0525 (0.2624) | 15/6, 0.0784 (0.4701) | 비유의 (비유의) / 비유의 (비유의) / 비유의 (비유의) |
| T7 MASSIVE intent-10 | 제외 | 100 (20 id x 5 언어) | 91/100 = 0.910 [0.838, 0.952] | 62/100 = 0.620 [0.522, 0.709] | 91/100 = 0.910 [0.838, 0.952] | 7/7, 1.0000 (1.0000) | 32/3, 4.2e-07 (3.8e-06) | 36/7, 9.0e-06 (8.1e-05) | 비유의 (비유의) / trained 유의 우세 (trained 유의 우세) / Jev 유의 우세 (Jev 유의 우세) |
| T8 prompt-injections | 제외 | 40 | 31/40 = 0.775 [0.625, 0.877] | 31/40 = 0.775 [0.625, 0.877] | 39/40 = 0.975 [0.871, 0.996] | 9/1, 0.0215 (0.1934) | 9/1, 0.0215 (0.1504) | 5/5, 1.0000 (1.0000) | trained 유의 우세 (비유의) / trained 유의 우세 (비유의) / 비유의 (비유의) |
| T9 Enron spam | 포함 | 40 | 40/40 = 1.000 [0.912, 1.000] | 40/40 = 1.000 [0.912, 1.000] | 39/40 = 0.975 [0.871, 0.996] | 0/1, 1.0000 (1.0000) | 0/1, 1.0000 (1.0000) | 0/0, 1.0000 (1.0000) | 비유의 (비유의) / 비유의 (비유의) / 비유의 (비유의) |
| T10 support tickets | 포함 | 40 | 10/40 = 0.250 [0.142, 0.402] | 12/40 = 0.300 [0.181, 0.454] | 12/40 = 0.300 [0.181, 0.454] | 5/3, 0.7266 (1.0000) | 1/1, 1.0000 (1.0000) | 3/5, 0.7266 (1.0000) | 비유의 (비유의) / 비유의 (비유의) / 비유의 (비유의) |

- 기존 8과제 family와의 차이: T9·T10의 Jev(S7)가 들어와 Holm을 trained vs Jev 8 → 10과제, Jev vs vanilla 8 → 10과제로 다시 했다. T1-T8에서 Holm 후 판정이 바뀐 칸은 없다.
- 정확도 칸은 정답/n = 정확도 [Wilson 95%]다. b = 앞 arm만 정답, c = 뒤 arm만 정답이고 p는 exact McNemar(양측)다. Holm은 family마다 따로 적용했다(trained vs Jev 10과제, trained vs vanilla 10과제, Jev vs vanilla 10과제).
- 판정 규칙은 F와 같다. p < 0.05이고 b > c면 앞 arm 유의 우세, c > b면 뒤 arm 유의 우세, 아니면 비유의. 괄호는 Holm 보정 p에 같은 규칙을 적용한 결과다.
- 판정 열의 trained vs Jev와 trained vs vanilla는 run 1(본 학습)의 판정이다. 판정은 두 run의 결론이 같을 때만 확정한다(프로젝트 책임자 결정). 두 열의 확정 여부는 §7.2에 있다. Jev vs vanilla는 학습과 무관해 두 run에 같다.
- Jev vs vanilla는 T1-T8에서 F의 McNemar를 그대로 쓴다(`results/F/jev_cmp/summary.json`의 base 러너: T7 multilingual, 나머지 english). T9·T10은 S7 master 기록(공개 저장소에는 포함하지 않음)에서 같은 함수(`s6_summary.systems_boolean`·`systems_choice`·`mcn`)로 계산한 base 러너(english) 검정이다. F의 판정은 과제별 최고 Laya 러너 기준이라 T4(F의 최고는 multilingual)에서 이 표와 다르고, Holm은 이 표의 base 러너 검정끼리 다시 했다.
- T1은 Jev와 비교 가능한 decision만 쓴다(Laya arm의 전체 200 decision은 §1.2). T1(case)과 T7(id)은 decision이 군집으로 묶여 Wilson 구간과 item 단위 McNemar가 낙관적이다. 군집 bootstrap은 §1.4에 있다.
- 학습 믹스 포함 과제는 vanilla가 이미 그 데이터를 봤으므로 trained − vanilla가 작게 나올 수 있다(retention 상한, §3).

### 1.2 T1 typed-decisions: Jev 비교 120 decision과 전체 200 decision

| arm | Jev 비교 120 decision | soft acc | Brier vs soft | score MAE | 전체 200 decision (Laya arm) | soft acc | Brier vs soft | score MAE |
|---|---|---|---|---|---|---|---|---|
| Jev | 104/120 = 0.867 [0.794, 0.916] | 0.590 | 0.077 | 0.390 | - | - | - | - |
| vanilla | 46/120 = 0.383 [0.301, 0.473] | 0.361 | 0.333 | 0.584 | 66/200 = 0.330 [0.269, 0.398] | 0.320 | 0.334 | 0.719 |
| trained | 95/120 = 0.792 [0.711, 0.855] | 0.515 | 0.104 | 0.254 | 137/200 = 0.685 [0.618, 0.745] | 0.458 | 0.113 | 0.368 |

- soft acc·Brier vs soft·score MAE는 teacher 분포 기준이다(upstream Part B, `laya_summary.py t1_extra`). Jev 줄은 F의 값이다.
- trained vs vanilla, 전체 200 decision: b/c 85/14, p=1.4e-13, 정확도 차이 +0.355 (드라이버 `paired_T1_typed_decisions_40.json`).

### 1.3 T7 MASSIVE intent-10: 언어별 (같은 20 id)

| arm | en | de | ja | zh-CN | ko | 합산 |
|---|---|---|---|---|---|---|
| Jev | 18/20 = 0.900 | 18/20 = 0.900 | 19/20 = 0.950 | 18/20 = 0.900 | 18/20 = 0.900 | 91/100 = 0.910 [0.838, 0.952] |
| vanilla | 17/20 = 0.850 | 8/20 = 0.400 | 16/20 = 0.800 | 12/20 = 0.600 | 9/20 = 0.450 | 62/100 = 0.620 [0.522, 0.709] |
| trained | 19/20 = 0.950 | 17/20 = 0.850 | 19/20 = 0.950 | 18/20 = 0.900 | 18/20 = 0.900 | 91/100 = 0.910 [0.838, 0.952] |

- 옵션은 10개 영어 key이고 발화만 언어별로 다르다. 언어당 n이 작아 언어별 차이는 방향 신호다.

### 1.4 군집 bootstrap: T1 (case), T7 (id)

| 과제 | 비교 | 정확도 차이 | 군집 bootstrap 95% | 군집 / decision | 참고: item 단위 McNemar b/c, p |
|---|---|---|---|---|---|
| T1 | trained − Jev | −0.075 | [−0.185, +0.025] | 40 / 120 | 10/19, 0.1360 |
| T1 | trained − vanilla | +0.408 | [+0.304, +0.516] | 40 / 120 | 56/7, 1.4e-10 |
| T1 | Jev − vanilla | +0.483 | [+0.371, +0.597] | 40 / 120 | 66/8, 1.8e-12 |
| T7 | trained − Jev | +0.000 | [−0.100, +0.110] | 20 / 100 | 7/7, 1.0000 |
| T7 | trained − vanilla | +0.290 | [+0.150, +0.440] | 20 / 100 | 32/3, 4.2e-07 |
| T7 | Jev − vanilla | +0.290 | [+0.100, +0.470] | 20 / 100 | 36/7, 9.0e-06 |

- 군집을 복원 재표본(10,000회, seed 13)해 뽑힌 군집의 decision 전체로 정확도 차이를 다시 계산했다(`s6_summary.cluster_boot`). Jev − vanilla는 F의 값이다.

### 1.5 보조 지표 (docs/09와 같은 정의)

| 과제 | 지표 | Jev | vanilla | trained |
|---|---|---|---|---|
| T5 BoolQ | AUROC p(true) | 0.988 | 0.810 | 0.831 |
| T6 SST-5 | MAE of E[level] | 0.432 | 0.888 | 0.472 |
| T8 prompt-injections | AUROC p(true) | 1.000 | 0.929 | 1.000 |
| T9 Enron spam | AUROC p(true) | 1.000 | 1.000 | 1.000 |

- T1의 soft acc·Brier vs soft·score MAE는 §1.2에 있다. AUROC는 p(true)의 순위(동점은 절반)이고 MAE는 기대 레벨과 gold 레벨의 절대 차이다. Jev 값은 F의 값이고 T9는 S7 기록에서 같은 함수로 계산했다(소수 둘째 자리 반올림 확률, MAE는 Jev의 score 필드).

### 1.6 T10 support tickets: 라벨 점검 (Jev 항목 40행)

| 큐 (gold) | Jev | vanilla english | vanilla multilingual (참고) | trained |
|---|---|---|---|---|
| Technical Support | 1/4 | 3/4 | 3/4 | 2/4 |
| Product Support | 0/4 | 0/4 | 2/4 | 0/4 |
| Customer Service | 0/4 | 0/4 | 0/4 | 0/4 |
| IT Support | 1/4 | 0/4 | 2/4 | 0/4 |
| Billing and Payments | 2/4 | 4/4 | 4/4 | 4/4 |
| Returns and Exchanges | 1/4 | 1/4 | 2/4 | 1/4 |
| Service Outages and Maintenance | 3/4 | 4/4 | 3/4 | 4/4 |
| Sales and Pre-Sales | 1/4 | 0/4 | 2/4 | 1/4 |
| Human Resources | 0/4 | 0/4 | 0/4 | 0/4 |
| General Inquiry | 1/4 | 0/4 | 0/4 | 0/4 |
| 합계 | 10/40 | 12/40 | 18/40 | 12/40 |

- 네 시스템(Jev, vanilla english, vanilla multilingual, trained)이 모두 틀린 행은 18/40이다. trained를 빼면 18/40으로 S7 analyze(`raw/analyze/T10.md`, 공개 저장소에는 포함하지 않음)의 per item 표와 같은 행이다.
- 라벨 품질 의심, 수작업 확인 필요(`S7_summary.md` 근거). 그 문서 §3.6은 오답 다수에서 gold 큐가 질문에 준 큐 설명과 맞지 않는다고 읽었다(해석). 큐당 행이 적어 큐별 수치는 방향 신호다. multilingual은 3-arm 밖의 참고 러너다(T10 base는 english).

## 2. ext 세트: vanilla vs trained

### 2.1 과제별 표

| 과제 | 범주 | n | vanilla | trained | trained − vanilla [bootstrap 95%] | b/c, p (Holm p) | 판정 (Holm 후) |
|---|---|---|---|---|---|---|---|
| T1 typed-decisions | 제외 | 2,000 | 727/2000 = 0.363 [0.343, 0.385] | 1373/2000 = 0.686 [0.666, 0.706] | +0.323 [+0.290, +0.355] | 818/172, 2.8e-101 (2.8e-100) | trained 유의 우세 (trained 유의 우세) |
| T2 AG News | 포함 | 500 | 470/500 = 0.940 [0.916, 0.958] | 473/500 = 0.946 [0.923, 0.963] | +0.006 [−0.014, +0.026] | 14/11, 0.6900 (1.0000) | 비유의 (비유의) |
| T3 DAIR Emotion | 제외 | 500 | 244/500 = 0.488 [0.444, 0.532] | 443/500 = 0.886 [0.855, 0.911] | +0.398 [+0.352, +0.446] | 209/10, 1.4e-49 (1.3e-48) | trained 유의 우세 (trained 유의 우세) |
| T4 Banking77-10 | 제외 | 500 | 438/500 = 0.876 [0.844, 0.902] | 482/500 = 0.964 [0.944, 0.977] | +0.088 [+0.062, +0.116] | 47/3, 3.7e-11 (2.2e-10) | trained 유의 우세 (trained 유의 우세) |
| T5 BoolQ | 포함 | 500 | 417/500 = 0.834 [0.799, 0.864] | 416/500 = 0.832 [0.797, 0.862] | −0.002 [−0.024, +0.020] | 16/17, 1.0000 (1.0000) | 비유의 (비유의) |
| T6 SST-5 | 제외 | 500 | 169/500 = 0.338 [0.298, 0.381] | 295/500 = 0.590 [0.546, 0.632] | +0.252 [+0.200, +0.304] | 172/46, 2.6e-18 (2.1e-17) | trained 유의 우세 (trained 유의 우세) |
| T7 MASSIVE intent-10 | 제외 | 500 | 346/500 = 0.692 [0.650, 0.731] | 439/500 = 0.878 [0.846, 0.904] | +0.186 [+0.124, +0.248] | 110/17, 7.4e-18 (5.2e-17) | trained 유의 우세 (trained 유의 우세) |
| T8 prompt-injections | 제외 | 116 | 81/116 = 0.698 [0.609, 0.774] | 112/116 = 0.966 [0.915, 0.987] | +0.267 [+0.181, +0.353] | 33/2, 3.7e-08 (1.8e-07) | trained 유의 우세 (trained 유의 우세) |
| T9 Enron spam | 포함 | 500 | 496/500 = 0.992 [0.980, 0.997] | 494/500 = 0.988 [0.974, 0.994] | −0.004 [−0.012, +0.004] | 1/3, 0.6250 (1.0000) | 비유의 (비유의) |
| T10 support tickets | 포함 | 500 | 132/500 = 0.264 [0.227, 0.304] | 166/500 = 0.332 [0.292, 0.374] | +0.068 [+0.028, +0.106] | 68/34, 0.0010 (0.0039) | trained 유의 우세 (trained 유의 우세) |

- 차이와 구간은 같은 항목의 paired bootstrap(10,000회, seed 13)이다. T1은 case, T7은 id를 군집으로 재표본하고 나머지는 항목을 재표본한다(`s6_summary.cluster_boot`).
- b = trained만 정답, c = vanilla만 정답이다. b/c와 p는 드라이버의 `paired_<stem>.json` 값이고 T7은 언어 파일 5개의 합이다. Holm은 10과제에 적용했다.
- trained와 판정은 run 1(본 학습)이다. 두 run의 결론이 같을 때만 판정을 확정한다(§7.2).
- ext는 vanilla vs trained의 좁은 CI용이다(Jev 없음). 표본은 대부분 라벨 층화라 upstream 공개치와 분포가 다르다(`PREP_20261008.md` §5).

### 2.2 T1 typed-decisions test 2,000 decision (V2와 같은 지표)

| 모델 | accuracy (dataset label, upstream 정의) | accuracy (argmax gold) | soft acc | Brier vs soft | ECE | score MAE | choice / noul / score |
|---|---|---|---|---|---|---|---|
| upstream `laya-typed-decisions` (V2 a) | 0.766 | 0.767 | 0.471 | 0.061 | 0.214 | 0.242 | 0.733 / 0.858 / 0.724 |
| 준비 V2(b): 우리 파이프라인의 T1 학습 | 0.747 | 0.746 | 0.495 | 0.059 | 0.148 | 0.253 | 0.732 / 0.832 / 0.693 |
| vanilla english | 0.361 | 0.363 | 0.331 | 0.316 | 0.173 | 0.694 | 0.290 / 0.488 / 0.325 |
| trained (본 학습 T1) | 0.690 | 0.686 | 0.463 | 0.099 | 0.112 | 0.359 | 0.700 / 0.782 / 0.605 |

- 공개치 0.766(V2 a 기준 ±0.02), V2 b 기준 ≥ 0.562와 majority 0.461(docs/11 §4). vanilla english 줄은 `V2_upstream_repro.json`의 english와 같아야 한다(verify가 대조).
- trained는 본 학습의 T1(english base, 과제 dev로 epoch 선택)이다. V2 b는 같은 설정의 준비 run이다.

## 3. 범주 집계 (Q1, Q2)

범주는 upstream이 밝힌 Laya 학습 믹스 기준이다(docs/11 §2). 포함은 T2·T5·T9·T10, 제외는 T1·T3·T4·T6·T7·T8이다. Jev가 들어간 집계의 포함 범주는 T2·T5·T9·T10이다.

### 3.1 arm별 범주 macro 정확도

| 기준 | arm | 포함 macro [95%] | 포함 과제 | 제외 macro [95%] | 제외 과제 |
|---|---|---|---|---|---|
| Jev 항목 | Jev | 0.762 [0.419, 0.969] | T2·T5·T9·T10 | 0.804 [0.721, 0.885] | T1·T3·T4·T6·T7·T8 |
| Jev 항목 | vanilla | 0.750 [0.469, 0.988] | T2·T5·T9·T10 | 0.613 [0.491, 0.732] | T1·T3·T4·T6·T7·T8 |
| Jev 항목 | trained | 0.750 [0.462, 0.963] | T2·T5·T9·T10 | 0.875 [0.784, 0.952] | T1·T3·T4·T6·T7·T8 |
| ext | vanilla | 0.758 [0.433, 0.966] | T2·T5·T9·T10 | 0.576 [0.428, 0.730] | T1·T3·T4·T6·T7·T8 |
| ext | trained | 0.774 [0.485, 0.967] | T2·T5·T9·T10 | 0.828 [0.716, 0.937] | T1·T3·T4·T6·T7·T8 |

### 3.2 arm 간 차이와 difference-in-differences

| 기준 | 차이 | 포함 평균 [95%] | 제외 평균 [95%] | 제외 − 포함 [95%] |
|---|---|---|---|---|
| Jev 항목 | Jev − vanilla | +0.013 [−0.075, +0.138] | +0.191 [+0.054, +0.330] | +0.179 [−0.008, +0.356] |
| Jev 항목 | trained − vanilla | +0.000 [−0.025, +0.031] | +0.262 [+0.212, +0.327] | +0.262 [+0.202, +0.333] |
| Jev 항목 | trained − Jev | −0.013 [−0.100, +0.062] | +0.071 [−0.017, +0.163] | +0.083 [−0.035, +0.215] |
| ext | trained − vanilla | +0.017 [−0.003, +0.051] | +0.252 [+0.171, +0.328] | +0.235 [+0.147, +0.316] |

- **Q1 difference-in-differences** = 제외 평균(Jev − vanilla) − 포함 평균(Jev − vanilla) = +0.179 [−0.008, +0.356] (Jev 항목). 양수면 vanilla의 열세가 학습 제외 과제에서 더 크다.
- 과제별 정확도(T1은 Jev 비교 decision, T7은 언어 합산)를 같은 가중치로 평균했다. 구간은 범주 안에서 과제를 복원 재표본(10,000회, seed 13)한 percentile이고 대비는 두 범주를 따로 재표본한 차이다. 범주당 과제가 적어(Jev 포함 범주는 4개) 모집단 추론이 아니라 기술통계다.
- 포함 과제의 trained − vanilla는 vanilla가 이미 그 데이터를 본 만큼 작을 수 있다(retention 상한).

## 4. 보정

### 4.1 Jev 항목

| 과제 | arm | temperature 출처 | Brier | ECE | coverage@오류 5% | coverage@오류 10% |
|---|---|---|---|---|---|---|
| T1 | Jev | - | 0.237 | 0.181 | 0.808 | 0.933 |
| T1 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.724 | 0.205 | 0.000 | 0.000 |
| T1 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 7.613 → 5.000, score 4.176, noul 10.000 → 5.000 | 0.656 | 0.129 | 0.000 | 0.000 |
| T1 | trained | 과제 calib fit: choice 1.101, score 1.049, noul 1.091 | 0.353 | 0.180 | 0.525 | 0.592 |
| T2 | Jev | - | 0.220 | 0.118 | 0.800 | 0.875 |
| T2 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.053 | 0.083 | 1.000 | 1.000 |
| T2 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.475, score 1.200, noul 1.200 | 0.051 | 0.064 | 1.000 | 1.000 |
| T2 | trained | 과제 calib fit: choice 4.487, score 1.200, noul 1.200 | 0.095 | 0.011 | 1.000 | 1.000 |
| T3 | Jev | - | 0.537 | 0.278 | 0.000 | 0.000 |
| T3 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.429 | 0.174 | 0.175 | 0.400 |
| T3 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 3.575, score 1.200, noul 1.200 | 0.428 | 0.209 | 0.250 | 0.625 |
| T3 | trained | 과제 calib fit: choice 4.527, score 1.200, noul 1.200 | 0.093 | 0.074 | 1.000 | 1.000 |
| T4 | Jev | - | 0.114 | 0.069 | 0.900 | 1.000 |
| T4 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.349 | 0.150 | 0.575 | 0.775 |
| T4 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.162, score 1.200, noul 1.200 | 0.337 | 0.155 | 0.575 | 0.775 |
| T4 | trained | 과제 calib fit: choice 3.599, score 1.200, noul 1.200 | 0.072 | 0.012 | 1.000 | 1.000 |
| T5 | Jev | - | 0.098 | 0.103 | 0.875 | 1.000 |
| T5 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.393 | 0.190 | 0.125 | 0.125 |
| T5 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.200, score 1.200, noul 1.108 | 0.447 | 0.229 | 0.125 | 0.125 |
| T5 | trained | 과제 calib fit: choice 1.200, score 1.200, noul 4.820 | 0.411 | 0.190 | 0.075 | 0.550 |
| T6 | Jev | - | 0.502 | 0.184 | 0.225 | 0.350 |
| T6 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.770 | 0.239 | 0.150 | 0.150 |
| T6 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.200, score 3.826, noul 1.200 | 0.687 | 0.112 | 0.100 | 0.100 |
| T6 | trained | 과제 calib fit: choice 1.200, score 1.751, noul 1.200 | 0.461 | 0.153 | 0.225 | 0.275 |
| T7 | Jev | - | 0.140 | 0.068 | 0.850 | 1.000 |
| T7 | vanilla | 기본값 1.0 (형식 전부) | 0.584 | 0.216 | 0.280 | 0.400 |
| T7 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 2.094, score 1.200, noul 1.200 | 0.525 | 0.083 | 0.240 | 0.340 |
| T7 | trained | 과제 calib fit: choice 4.744, score 1.200, noul 1.200 | 0.173 | 0.074 | 0.850 | 1.000 |
| T8 | Jev | - | 0.307 | 0.194 | 0.675 | 0.800 |
| T8 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.401 | 0.223 | 0.000 | 0.675 |
| T8 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.200, score 1.200, noul 10.000 → 5.000 | 0.337 | 0.168 | 0.600 | 0.700 |
| T8 | trained | 과제 calib fit: choice 1.200, score 1.200, noul 1.860 | 0.035 | 0.021 | 1.000 | 1.000 |
| T9 | Jev | - | 0.019 | 0.060 | 1.000 | 1.000 |
| T9 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.005 | 0.014 | 1.000 | 1.000 |
| T9 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.200, score 1.200, noul 1.077 | 0.001 | 0.004 | 1.000 | 1.000 |
| T9 | trained | 과제 calib fit: choice 1.200, score 1.200, noul 4.345 | 0.029 | 0.026 | 1.000 | 1.000 |
| T10 | Jev | - | 1.319 | 0.623 | 0.000 | 0.000 |
| T10 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.775 | 0.253 | 0.175 | 0.275 |
| T10 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.835, score 1.200, noul 1.200 | 0.733 | 0.162 | 0.175 | 0.250 |
| T10 | trained | 과제 calib fit: choice 1.426, score 1.200, noul 1.200 | 0.752 | 0.184 | 0.125 | 0.125 |

### 4.2 ext

| 과제 | arm | temperature 출처 | Brier | ECE | coverage@오류 5% | coverage@오류 10% |
|---|---|---|---|---|---|---|
| T1 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.749 | 0.173 | 0.000 | 0.000 |
| T1 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 7.613 → 5.000, score 4.176, noul 10.000 → 5.000 | 0.685 | 0.035 | 0.001 | 0.001 |
| T1 | trained | 과제 calib fit: choice 1.101, score 1.049, noul 1.091 | 0.434 | 0.112 | 0.172 | 0.275 |
| T2 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.096 | 0.032 | 0.974 | 1.000 |
| T2 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.475, score 1.200, noul 1.200 | 0.096 | 0.020 | 0.976 | 1.000 |
| T2 | trained | 과제 calib fit: choice 4.487, score 1.200, noul 1.200 | 0.097 | 0.013 | 0.988 | 1.000 |
| T3 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.894 | 0.411 | 0.000 | 0.000 |
| T3 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 3.575, score 1.200, noul 1.200 | 0.666 | 0.074 | 0.000 | 0.000 |
| T3 | trained | 과제 calib fit: choice 4.527, score 1.200, noul 1.200 | 0.196 | 0.077 | 0.812 | 0.954 |
| T4 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.211 | 0.074 | 0.732 | 0.940 |
| T4 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.162, score 1.200, noul 1.200 | 0.212 | 0.077 | 0.738 | 0.942 |
| T4 | trained | 과제 calib fit: choice 3.599, score 1.200, noul 1.200 | 0.061 | 0.015 | 1.000 | 1.000 |
| T5 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.256 | 0.083 | 0.462 | 0.762 |
| T5 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.200, score 1.200, noul 1.108 | 0.291 | 0.137 | 0.460 | 0.762 |
| T5 | trained | 과제 calib fit: choice 1.200, score 1.200, noul 4.820 | 0.295 | 0.128 | 0.174 | 0.696 |
| T6 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.863 | 0.313 | 0.002 | 0.002 |
| T6 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.200, score 3.826, noul 1.200 | 0.724 | 0.087 | 0.002 | 0.002 |
| T6 | trained | 과제 calib fit: choice 1.200, score 1.751, noul 1.200 | 0.530 | 0.074 | 0.018 | 0.022 |
| T7 | vanilla | 기본값 1.0 (형식 전부) | 0.490 | 0.187 | 0.296 | 0.520 |
| T7 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 2.094, score 1.200, noul 1.200 | 0.436 | 0.094 | 0.286 | 0.464 |
| T7 | trained | 과제 calib fit: choice 4.744, score 1.200, noul 1.200 | 0.196 | 0.050 | 0.802 | 0.962 |
| T8 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.526 | 0.262 | 0.000 | 0.000 |
| T8 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.200, score 1.200, noul 10.000 → 5.000 | 0.439 | 0.207 | 0.440 | 0.586 |
| T8 | trained | 과제 calib fit: choice 1.200, score 1.200, noul 1.860 | 0.057 | 0.034 | 1.000 | 1.000 |
| T9 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.014 | 0.006 | 1.000 | 1.000 |
| T9 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.200, score 1.200, noul 1.077 | 0.014 | 0.006 | 1.000 | 1.000 |
| T9 | trained | 과제 calib fit: choice 1.200, score 1.200, noul 4.345 | 0.018 | 0.005 | 1.000 | 1.000 |
| T10 | vanilla | upstream fit (형식별, 옵션 수 구간별) | 0.851 | 0.201 | 0.102 | 0.122 |
| T10 | vanilla + 과제 T | 과제 calib fit (0-step export): choice 1.835, score 1.200, noul 1.200 | 0.801 | 0.088 | 0.104 | 0.126 |
| T10 | trained | 과제 calib fit: choice 1.426, score 1.200, noul 1.200 | 0.757 | 0.054 | 0.146 | 0.156 |

- Brier는 옵션 전체의 Σ(p − onehot)² 평균, ECE는 15 bins top p 기준이다. coverage@오류 x%는 top p가 높은 순으로 받아들일 때 오류율이 x% 이하인 최대 coverage다(`scripts/metrics_extra.py coverage_table`, 같은 confidence는 나누지 않음). Jev 확률은 소수 둘째 자리 반올림이라 Brier·ECE에 약 ±0.005의 하한 오차가 있다.
- **주의.** trained의 보정 개선에는 temperature refit 효과가 섞인다(V1). trained의 temperature는 과제 calib로 다시 맞춘 값이고 vanilla english는 upstream이 맞춘 값, multilingual은 기본값이다. V1에서 학습 없이 refit만으로 ECE가 english 0.083 → 0.064, multilingual 0.365 → 0.179로 바뀌었다. 이 효과를 과제마다 떼어 낸 것이 vanilla + 과제 T 행과 §4.3이다. 정확도 비교는 영향이 없다(temperature는 argmax를 바꾸지 않는다).
- vanilla + 과제 T는 base 가중치를 그대로 두고 그 과제 calib로 temperature만 맞춘 0-step export다(`results/T3arm/calib_sep/<task>/`, V1과 같은 절차, 프로젝트 책임자 결정 3). temperature 출처의 a → b는 fit 값 a를 laya가 로드 때 b로 자른 clamp다(리포트 `config.checkpoint`의 `temperature_raw` → `temperature_applied`; 해당 과제 T1, T8).

### 4.3 보정 분리: refit 효과와 학습 효과

| 과제 | Jev 항목 ECE: refit / 학습 | Jev 항목 Brier: refit / 학습 | ext ECE: refit / 학습 | ext Brier: refit / 학습 |
|---|---|---|---|---|
| T1 typed-decisions | −0.076 / +0.051 | −0.067 / −0.303 | −0.138 / +0.077 | −0.064 / −0.250 |
| T2 AG News | −0.019 / −0.052 | −0.002 / +0.043 | −0.012 / −0.006 | −0.000 / +0.001 |
| T3 DAIR Emotion | +0.034 / −0.135 | −0.002 / −0.334 | −0.336 / +0.002 | −0.228 / −0.470 |
| T4 Banking77-10 | +0.005 / −0.143 | −0.012 / −0.265 | +0.004 / −0.063 | +0.001 / −0.151 |
| T5 BoolQ | +0.039 / −0.039 | +0.054 / −0.036 | +0.055 / −0.010 | +0.035 / +0.003 |
| T6 SST-5 | −0.127 / +0.041 | −0.084 / −0.226 | −0.226 / −0.013 | −0.139 / −0.194 |
| T7 MASSIVE intent-10 | −0.133 / −0.009 | −0.060 / −0.352 | −0.093 / −0.045 | −0.054 / −0.240 |
| T8 prompt-injections | −0.055 / −0.147 | −0.065 / −0.302 | −0.055 / −0.173 | −0.087 / −0.382 |
| T9 Enron spam | −0.010 / +0.022 | −0.004 / +0.029 | +0.000 / −0.001 | +0.000 / +0.003 |
| T10 support tickets | −0.091 / +0.022 | −0.042 / +0.019 | −0.113 / −0.034 | −0.050 / −0.045 |

- refit 효과 = (vanilla + 과제 T) − vanilla, 학습 효과 = trained − (vanilla + 과제 T)다. 둘의 합이 trained − vanilla이고 음수면 그 지표가 낮아진(좋아진) 것이다. T1의 Jev 항목은 Jev와 비교 가능한 120 decision이다.
- vanilla + 과제 T의 답은 vanilla와 같다. argmax 일치 6,735/6,736(반올림 동률을 같은 답으로 보면 6,736/6,736), 정답 여부 6,736/6,736 일치다(`same_<stem>.json`, Jev 항목과 ext 전체). 그래서 정확도와 정확도 검정은 vanilla 칸 그대로이고 Brier·ECE·coverage만 다르다. 엄격 불일치 1 decision(`T6_sst5_ext500`)은 동률을 같은 답으로 보면 일치한다.

## 5. 비용 (Q3)

| 과제 | base | 라벨 합계 | train items | calib | dev | epoch / optimizer step | item 출처 (학습은 item-pass 수) | train loop (분) | run_ft wall (분) | items/s | MPS allocated / driver peak (GB) | 체크포인트 (GB) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 typed-decisions | english | 6,000 | 5,000 | 400 | 600 | 2 / 314 | train ← train 10,000; calibration ← calib 400 | 39.9 | 40.4 | 4.18 | 20.7 / 30.2 | 0.85 |
| T2 AG News | english | 6,400 | 5,000 | 400 | 1,000 | 2 / 314 | train ← train 10,000; calibration ← calib 400 | 14.4 | 14.6 | 11.61 | 15.2 / 21.6 | 0.85 |
| T3 DAIR Emotion | english | 6,400 | 5,000 | 400 | 1,000 | 2 / 314 | train ← train 10,000; calibration ← calib 400 | 10.1 | 10.3 | 16.53 | 8.8 / 16.2 | 0.85 |
| T4 Banking77-10 | english | 6,400 | 5,000 | 400 | 1,000 | 2 / 314 | train ← train 10,000; calibration ← calib 400 | 11.6 | 11.8 | 14.37 | 9.7 / 18.4 | 0.85 |
| T5 BoolQ | english | 6,400 | 5,000 | 400 | 1,000 | 2 / 314 | train ← train 10,000; calibration ← calib 400 | 28.3 | 28.7 | 5.89 | 20.7 / 26.2 | 0.85 |
| T6 SST-5 | english | 6,100 | 5,000 | 400 | 700 | 2 / 314 | train ← train 10,000; calibration ← calib 400 | 11.4 | 11.6 | 14.58 | 9.1 / 17.7 | 0.85 |
| T7 MASSIVE intent-10 | multilingual | 6,400 | 5,000 | 400 | 1,000 | 2 / 314 | train ← train 10,000; calibration ← calib 400 | 7.5 | 7.7 | 22.10 | 6.7 / 15.9 | 0.68 |
| T8 prompt-injections | english | 544 | 444 | 40 | 60 | 2 / 28 | train ← train 888; calibration ← calib 40 | 1.4 | 1.5 | 10.48 | 20.8 / 26.0 | 0.85 |
| T9 Enron spam | english | 6,400 | 5,000 | 400 | 1,000 | 2 / 314 | train ← train 10,000; calibration ← calib 400 | 43.3 | 43.9 | 3.85 | 20.7 / 32.3 | 0.85 |
| T10 support tickets | english | 6,400 | 5,000 | 400 | 1,000 | 2 / 314 | train ← train 10,000; calibration ← calib 400 | 26.8 | 27.2 | 6.21 | 18.1 / 22.7 | 0.85 |

- 라벨 합계 = train + calib(temperature fit) + dev(epoch 선택)다. 시간과 메모리는 run_ft 리포트(`<task>/train_timing.json`, 학습은 MPS fp32), 체크포인트는 `poc/finetune/ckpt_t3arm/<task>/`(공개 저장소에는 포함하지 않음)의 파일 크기 합(십진 GB)이다. Jev와 vanilla는 라벨과 학습이 없다.

## 6. 학습 검증 (Q4)

### 6.1 과제별 진단

| 과제 | dev epoch 0 (vanilla) | epoch 1 | epoch 2 | 선택 epoch | train − dev | fitted T (choice, score, noul) | clamp | flip dev40 [95%] | 클래스 recall 변화 (상승 / 하락 / 동일; 최저, 최고) | 학습 실패 |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 typed-decisions | 0.365 | 0.667 | 0.683 | 2 | +0.054 | 1.101, 1.049, 1.091 | 없음 | 0.031 [0.000, 0.069] (n=58) | 30 / 10 / 14; disposition=close_benign −1.000, disposition=investigate +1.000 | 아니오 |
| T2 AG News | 0.936 | 0.934 | 0.937 | 2 | +0.027 | 4.487, 1.200, 1.200; 기본값 형식: score, noul | 없음 | 0.005 [0.000, 0.015] (n=40) | 1 / 2 / 1; business −0.016, sci_tech +0.024 | 아니오 |
| T3 DAIR Emotion | 0.612 | 0.864 | 0.897 | 2 | +0.034 | 4.527, 1.200, 1.200; 기본값 형식: score, noul | 없음 | 0.015 [0.000, 0.040] (n=40) | 6 / 0 / 0; joy +0.176, surprise +0.600 | 아니오 |
| T4 Banking77-10 | 0.842 | 0.922 | 0.946 | 2 | +0.013 | 3.599, 1.200, 1.200; 기본값 형식: score, noul | 없음 | 0.035 [0.000, 0.095] (n=40) | 47 / 7 / 23; cash withdrawal charge −0.154, get physical card +0.615 | 아니오 |
| T5 BoolQ | 0.986 | 0.955 | 0.971 | 2 | +0.009 | 1.200, 1.200, 4.820; 기본값 형식: choice, score | 없음 | - (choice 아님) | 0 / 2 / 0; True −0.016, False −0.014 | 예 |
| T6 SST-5 | 0.360 | 0.490 | 0.506 | 2 | +0.142 | 1.200, 1.751, 1.200; 기본값 형식: choice, noul | 없음 | - (choice 아님) | 3 / 2 / 0; 1 −0.148, 4 +0.635 | 아니오 |
| T7 MASSIVE intent-10 | 0.671 | 0.854 | 0.868 | 2 | +0.069 | 4.744, 1.200, 1.200; 기본값 형식: score, noul | 없음 | 0.010 [0.000, 0.025] (n=40) | 46 / 3 / 8; play_music −0.250, recommendation_events +0.667 | 아니오 |
| T8 prompt-injections | 0.683 | 0.967 | 0.950 | 1 (재보정) | +0.033 | 1.200, 1.200, 1.860; 기본값 형식: choice, score | 없음 | - (choice 아님) | 1 / 0 / 1; False +0.000, True +0.567 | 아니오 |
| T9 Enron spam | 0.996 | 0.995 | 0.995 | 1 (재보정) | −0.001 | 1.200, 1.200, 4.345; 기본값 형식: choice, score | 없음 | - (choice 아님) | 1 / 1 / 0; True −0.008, False +0.006 | 예 |
| T10 support tickets | 0.419 | 0.367 | 0.385 | 2 | +0.083 | 1.426, 1.200, 1.200; 기본값 형식: score, noul | 없음 | 0.175 [0.105, 0.250] (n=40) | 7 / 1 / 0; Technical Support −0.477, Returns and Exchanges +0.191 | 예 |

- dev는 epoch 선택에만 쓰는 held-out 조각이다. 마지막 epoch 칸은 최종 export(마지막 epoch + fitted T)이고 temperature는 argmax를 바꾸지 않는다. 선택 규칙은 dev 최고, 동률이면 앞 epoch이다(docs/11 §4). 앞 epoch을 고르면 같은 calib로 다시 맞춘다(재보정).
- train − dev = 마지막 창의 train 정확도(dropout을 켠 학습 forward) − 선택 epoch의 dev 정확도. fitted T는 선택 체크포인트의 값이고, 기본값 형식은 calib 표본이 없어 스크립트 기본값을 받은 형식이다. clamp는 fit 범위 경계값과 load 범위(laya가 로드 때 자르는 구간) 밖의 값이다.
- flip은 dev 앞 40행(choice 과제)의 옵션 순서를 바꾼 순열당 답 변경 비율이다. 학습 실패 = 모든 epoch의 dev가 epoch 0(vanilla)보다 낮음.
- T5의 학습 실패 표시: dev가 BoolQ train split에서 왔고 BoolQ는 upstream 학습 믹스에 있다. vanilla가 그 행을 기억해 dev 기준선이 부풀었다. validation 기반 ext에서는 vanilla와 trained가 같다(§2.1). 파이프라인 실패가 아니다(`PREP_20261008.md` "본 학습 중 발견" 절).
- T9의 학습 실패 표시: 천장 효과다. dev 차이는 1,000행 중 1행이고, vanilla의 dev와 ext가 거의 같아 기억 신호는 없다. 파이프라인 실패가 아니다(`PREP_20261008.md` "본 학습 중 발견" 절).
- T10의 학습 실패 표시: dev는 자연 분포라 Technical Support 몫이 가장 크고 train·ext는 균등에 가깝다. vanilla는 이 큐로 예측이 쏠려 있다. trained는 dev의 8개 큐 중 7개에서 recall이 오르고 dev macro recall도 오른다. 파이프라인 실패가 아니다(`PREP_20261008.md` "본 학습 중 발견" 절).

### 6.2 학습 검증 V1-V6 요약

| ID | 검증 | 핵심 수치 | 기준 충족 | 파일 (`results/T3arm/validity/`) |
|---|---|---|---|---|
| V1 | zero-step identity | english 텐서 값 206/206 동일, argmax 40/40, base T 복원 답 40/40 동일; multilingual 텐서 값 170/170 동일, argmax 20/20, base T 복원 답 20/20 동일. refit만으로 ECE english 0.083 → 0.064, multilingual 0.365 → 0.179 | 예 | `V1_*_{export_diff,same,basetemp_same}.json` |
| V2 | upstream 재현 | (a) upstream 체크포인트 0.766 (공개 0.766, ±0.02) (b) 우리 학습 0.747 (기준 ≥ 0.562, majority 0.461) | 예 | `V2_upstream_repro.json` |
| V3 | label-shuffle | permuted 0.385, 실제 라벨(준비 run) 0.831, vanilla 0.612, majority 0.296 | 통과 (프로젝트 책임자 판정, §6.3) | `V3_label_shuffle.json` |
| V4 | 형식 동일성 | 10과제, 추론 시퀀스와 토큰 일치 250/250, 옵션 decode·target 점검 49,084 items | 예 | `V4_format_identity.json` |
| V5 | smoke | english 3.95 items/s, multilingual 20.14 items/s. 드라이버 SMOKE STEP OK 163, FAILED 0 (`results/T3arm/smoke_20261008-1021/run_all_status.log`) | 예 | `V5_*` |
| V6 | 누수 | 10과제 train·dev·calib와 평가 텍스트의 교집합 정확 0 / 정규화 0. 추출 전 제거 T3 1, T7 24 | 예 | `V6_leakage.json` |

- 기준은 docs/11 §4다. V1-V2·V4-V6의 기준 충족은 위 수치로 다시 계산했고 `PREP_20261008.md` §3의 판정과 같아야 한다. V3는 프로젝트 책임자 판정이다(§6.3).

### 6.3 V3 재판정 수치와 프로젝트 책임자 판정

| 기준 | 조건 | 값 | 기준값 | 값 − 기준값 |
|---|---|---|---|---|
| (a) 엄격 | permuted ≤ majority + 0.05 | permuted 0.385 | 0.346 | +0.039 |
| (b) 차이 | 실제 라벨 epoch 1 − permuted ≥ 0.30 | 0.864 − 0.385 = +0.479 | 0.30 | +0.179 |
| (c) 대안 | permuted < vanilla zero-shot dev, 그리고 (b) | vanilla 0.612 − permuted 0.385 = +0.227; (b) 차이 +0.479 | 0 초과, (b) | - |

- **프로젝트 책임자 판정 (2026-10-08, 본 학습 수치 기준): 통과.** (b) 차이 기준과 (c) 대안 기준을 충족하고, (a) 엄격 기준의 +0.039 미달은 계획과의 편차로 기록한다(`PREP_20261008.md "프로젝트 책임자 결정" 1`).
- 실제 라벨 epoch 1 = 본 학습 T3의 `dev_ep1.json` 정확도(0.864; 2 epoch cosine의 중간 지점)다. 준비 단계의 대조 run(같은 items, cosine이 한 epoch에 끝남)은 0.831이었다.
- permuted, majority, vanilla는 `V3_label_shuffle.json`(T3 dev 전체, english)이다. 본 학습 T3의 dev epoch 0(vanilla)은 0.612다(같은 dev면 vanilla와 같아야 한다).

### 6.4 같은 설정 T1 재학습 편차

준비 V2(b)와 본 학습 T1은 스크립트, items, seed, 인자가 같다(`PREP_20261008.md` 마지막 절). 원인은 MPS 학습이 비트 단위로 결정적이지 않은 데 있다. 두 run의 micro-batch 손실은 12번에서 처음 갈라진다(1.20023 대 1.20035).

| 지표 | V2(b) (준비) | 본 학습 T1 |
|---|---|---|
| dev epoch 1 | 0.708 | 0.667 |
| dev epoch 2 | 0.738 | 0.683 |
| test accuracy (dataset label, upstream 정의) | 0.747 | 0.690 |
| test accuracy (argmax gold) | 0.746 | 0.686 |
| test soft acc | 0.495 | 0.463 |
| test Brier vs soft | 0.059 | 0.099 |
| test score MAE | 0.253 | 0.359 |
| test ECE | 0.148 | 0.112 |
| calibration 행 정확도 | 0.718 | 0.685 |
| 마지막 train CE 창 | 0.864 | 0.930 |

| 짝 비교 (test 2,000 decision) | b/c | exact McNemar p | 정확도 차이 V2(b) − 본 학습 (argmax gold) | case 군집 bootstrap 95% | 군집 / decision |
|---|---|---|---|---|---|
| V2(b) vs 본 학습 | 217/98 | 1.7e-11 | +0.059 | [+0.040, +0.081] | 400 / 2000 |

| micro-batch 손실 (ce) | 0-11 | 12-39 | 40-99 | 100-299 | 300-624 | 625-1249 |
|---|---|---|---|---|---|---|
| 두 run의 평균 절대 차이 | 0.0000 | 0.0159 | 0.0248 | 0.0536 | 0.0653 | 0.0823 |

- b = V2(b)만 정답, c = 본 학습만 정답이다(같은 decision). 군집 bootstrap은 case를 복원 재표본(10,000회, seed 13)했다(`s6_summary.cluster_boot`).
- 손실 구간은 micro-batch index다(두 epoch 합 1250개). 값은 각 run의 `train_timing.json` `micro_batch_trace` 다섯째 필드(ce)다.
- 같은 설정에서도 학습 run마다 결과가 달라진다. 그래서 §1-§6의 trained 수치는 run 하나(run 1)의 표본이다. seed를 바꾼 반복 학습과 판정 확정은 §7, T1 세 run 비교는 §7.4다.

## 7. 반복 학습과 판정 확정

run 1은 본 학습(torch seed 13, `results/T3arm/<task>/`), run 2는 같은 설정에서 seed만 14로 바꾼 반복 학습(`results/T3arm/rep_s14/<task>/`)이다. 데이터 순서는 같고 seed는 dropout과 RLCD 노이즈를 바꾼다(`PREP_20261008.md` "프로젝트 책임자 결정" 4). 판정은 두 run의 결론이 같을 때만 확정한다. run 2의 결과 있는 과제 10개(T1, T2, T3, T4, T5, T6, T7, T8, T9, T10), 결과 없음 0개(-). vanilla·Jev·vanilla + 과제 T는 학습이 없어 두 run에 같다.

### 7.1 과제별 정확도와 두 run의 짝 비교

| 과제 | 범주 | Jev 항목 정확도: run 1 / run 2 / 평균 | ext 정확도: run 1 / run 2 / 평균 | ext run 1 vs run 2: b/c, p | 선택 epoch: run 1 / run 2 |
|---|---|---|---|---|---|
| T1 typed-decisions | 제외 | 0.792 / 0.858 / 0.825 | 0.686 / 0.735 / 0.711 | 117/214, 1.1e-07; 군집 bootstrap run 1 − run 2 −0.049 [−0.069, −0.028] | 2 / 2 |
| T2 AG News | 포함 | 0.950 / 0.975 / 0.962 | 0.946 / 0.942 / 0.944 | 12/10, 0.8318 | 2 / 1 |
| T3 DAIR Emotion | 제외 | 0.950 / 0.925 / 0.938 | 0.886 / 0.886 / 0.886 | 11/11, 1.0000 | 2 / 2 |
| T4 Banking77-10 | 제외 | 0.950 / 0.925 / 0.938 | 0.964 / 0.962 / 0.963 | 9/8, 1.0000 | 2 / 2 |
| T5 BoolQ | 포함 | 0.775 / 0.700 / 0.738 | 0.832 / 0.838 / 0.835 | 21/24, 0.7660 | 2 / 2 |
| T6 SST-5 | 제외 | 0.675 / 0.725 / 0.700 | 0.590 / 0.578 / 0.584 | 38/32, 0.5504 | 2 / 2 |
| T7 MASSIVE intent-10 | 제외 | 0.910 / 0.870 / 0.890 | 0.878 / 0.882 / 0.880 | 16/18, 0.8642; 군집 bootstrap run 1 − run 2 −0.004 [−0.032, +0.024] | 2 / 2 |
| T8 prompt-injections | 제외 | 0.975 / 1.000 / 0.988 | 0.966 / 0.957 / 0.961 | 2/1, 1.0000 | 1 / 2 |
| T9 Enron spam | 포함 | 0.975 / 0.975 / 0.975 | 0.988 / 0.988 / 0.988 | 2/2, 1.0000 | 1 / 2 |
| T10 support tickets | 포함 | 0.300 / 0.425 / 0.362 | 0.332 / 0.340 / 0.336 | 33/37, 0.7202 | 2 / 2 |

- 정확도는 trained의 정확도다(Jev 항목은 §1.1과 같은 decision, 평균은 두 run의 단순 평균). b = run 1만 정답, c = run 2만 정답(같은 ext 항목)이고 p는 exact McNemar다.
- T1·T7은 decision이 case·id 군집으로 묶여 item 단위 p가 낙관적이라 run 1 − run 2 정확도 차이의 군집 bootstrap(10,000회, bootstrap seed 13)을 함께 둔다.
- §6.4는 seed가 같은 두 run(준비 V2(b), 본 학습)이 MPS 비결정성만으로 갈라진 편차다. run 2는 seed까지 바꿨다.

### 7.2 판정 일치표

| 과제 | 비교 | run 1 판정 (Holm p) | run 2 판정 (Holm p) | 결론 |
|---|---|---|---|---|
| T1 typed-decisions | Jev 항목 trained vs Jev | 비유의 (0.9523) | 비유의 (1.0000) | 확정 |
| T1 typed-decisions | Jev 항목 trained vs vanilla | trained 유의 우세 (1.4e-09) | trained 유의 우세 (1.3e-11) | 확정 |
| T1 typed-decisions | ext trained vs vanilla | trained 유의 우세 (2.8e-100) | trained 유의 우세 (1.6e-128) | 확정 |
| T2 AG News | Jev 항목 trained vs Jev | 비유의 (1.0000) | 비유의 (0.7500) | 확정 |
| T2 AG News | Jev 항목 trained vs vanilla | 비유의 (1.0000) | 비유의 (1.0000) | 확정 |
| T2 AG News | ext trained vs vanilla | 비유의 (1.0000) | 비유의 (1.0000) | 확정 |
| T3 DAIR Emotion | Jev 항목 trained vs Jev | 비유의 (0.0635) | 비유의 (0.1797) | 확정 |
| T3 DAIR Emotion | Jev 항목 trained vs vanilla | 비유의 (0.2314) | 비유의 (0.3271) | 확정 |
| T3 DAIR Emotion | ext trained vs vanilla | trained 유의 우세 (1.3e-48) | trained 유의 우세 (1.3e-48) | 확정 |
| T4 Banking77-10 | Jev 항목 trained vs Jev | 비유의 (1.0000) | 비유의 (1.0000) | 확정 |
| T4 Banking77-10 | Jev 항목 trained vs vanilla | trained 유의 우세 (0.0312) | 비유의 (0.0547) | 불일치 |
| T4 Banking77-10 | ext trained vs vanilla | trained 유의 우세 (2.2e-10) | trained 유의 우세 (4.2e-09) | 확정 |
| T5 BoolQ | Jev 항목 trained vs Jev | 비유의 (0.8750) | 비유의 (0.1055) | 확정 |
| T5 BoolQ | Jev 항목 trained vs vanilla | 비유의 (1.0000) | 비유의 (1.0000) | 확정 |
| T5 BoolQ | ext trained vs vanilla | 비유의 (1.0000) | 비유의 (1.0000) | 확정 |
| T6 SST-5 | Jev 항목 trained vs Jev | 비유의 (1.0000) | 비유의 (1.0000) | 확정 |
| T6 SST-5 | Jev 항목 trained vs vanilla | 비유의 (0.2624) | 비유의 (0.0709) | 확정 |
| T6 SST-5 | ext trained vs vanilla | trained 유의 우세 (2.1e-17) | trained 유의 우세 (3.4e-15) | 확정 |
| T7 MASSIVE intent-10 | Jev 항목 trained vs Jev | 비유의 (1.0000) | 비유의 (1.0000) | 확정 |
| T7 MASSIVE intent-10 | Jev 항목 trained vs vanilla | trained 유의 우세 (3.8e-06) | trained 유의 우세 (4.2e-05) | 확정 |
| T7 MASSIVE intent-10 | ext trained vs vanilla | trained 유의 우세 (5.2e-17) | trained 유의 우세 (1.7e-18) | 확정 |
| T8 prompt-injections | Jev 항목 trained vs Jev | 비유의 (0.1934) | trained 유의 우세 (0.0391) | 불일치 |
| T8 prompt-injections | Jev 항목 trained vs vanilla | 비유의 (0.1504) | trained 유의 우세 (0.0312) | 불일치 |
| T8 prompt-injections | ext trained vs vanilla | trained 유의 우세 (1.8e-07) | trained 유의 우세 (7.7e-08) | 확정 |
| T9 Enron spam | Jev 항목 trained vs Jev | 비유의 (1.0000) | 비유의 (1.0000) | 확정 |
| T9 Enron spam | Jev 항목 trained vs vanilla | 비유의 (1.0000) | 비유의 (1.0000) | 확정 |
| T9 Enron spam | ext trained vs vanilla | 비유의 (1.0000) | 비유의 (1.0000) | 확정 |
| T10 support tickets | Jev 항목 trained vs Jev | 비유의 (1.0000) | 비유의 (0.6460) | 확정 |
| T10 support tickets | Jev 항목 trained vs vanilla | 비유의 (1.0000) | 비유의 (0.5000) | 확정 |
| T10 support tickets | ext trained vs vanilla | trained 유의 우세 (0.0039) | trained 유의 우세 (0.0015) | 확정 |

- 결론: 확정 27, 불일치 3, 결과 없음 0 (비교 30개 = 과제 10개 x 비교 3종). 불일치: T4 Jev 항목 trained vs vanilla, T8 Jev 항목 trained vs Jev, T8 Jev 항목 trained vs vanilla.
- 확정 = 두 run의 Holm 후 판정이 같음. 판정 규칙과 Holm family(비교마다 따로)는 §1.1·§2.1과 같고, run 2의 Holm은 run 2에 결과 있는 과제끼리 따로 했다(지금 10과제, 끝나면 10과제).

### 7.3 범주 집계: ext trained − vanilla

| run | 포함 평균 [95%] | 포함 과제 | 제외 평균 [95%] | 제외 과제 | 제외 − 포함 [95%] |
|---|---|---|---|---|---|
| run 1 (seed 13) | +0.017 [−0.003, +0.051] | T2·T5·T9·T10 | +0.252 [+0.171, +0.328] | T1·T3·T4·T6·T7·T8 | +0.235 [+0.147, +0.316] |
| run 2 (seed 14) | +0.020 [−0.002, +0.058] | T2·T5·T9·T10 | +0.257 [+0.169, +0.340] | T1·T3·T4·T6·T7·T8 | +0.238 [+0.144, +0.325] |

- §3.2와 같은 방식이다(과제를 같은 가중치로 평균, 범주 안 과제 재표본 bootstrap 10,000회). 제외 − 포함이 difference-in-differences다. run 2는 결과 있는 과제만 들어가 run 1과 과제 구성이 다를 수 있다.

### 7.4 T1 세 run: 준비 V2(b), 본 학습, run 2

| 지표 | V2(b) (준비, seed 13) | 본 학습 run 1 (seed 13) | run 2 (seed 14) |
|---|---|---|---|
| dev epoch 1 | 0.708 | 0.667 | 0.702 |
| dev epoch 2 | 0.738 | 0.683 | 0.750 |
| test accuracy (dataset label, upstream 정의) | 0.747 | 0.690 | 0.735 |
| test accuracy (argmax gold) | 0.746 | 0.686 | 0.735 |
| test soft acc | 0.495 | 0.463 | 0.491 |
| test Brier vs soft | 0.059 | 0.099 | 0.063 |
| test score MAE | 0.253 | 0.359 | 0.262 |
| test ECE | 0.148 | 0.112 | 0.144 |
| calibration 행 정확도 | 0.718 | 0.685 | 0.720 |
| 마지막 train CE 창 | 0.864 | 0.930 | 0.870 |

| 짝 비교 (test 2,000 decision) | b/c | exact McNemar p | 정확도 차이 (argmax gold) | case 군집 bootstrap 95% | 군집 / decision |
|---|---|---|---|---|---|
| V2(b) vs run 2 | 118/96 | 0.1510 | +0.011 | [−0.003, +0.025] | 400 / 2000 |
| 본 학습 vs run 2 | 117/214 | 1.1e-07 | −0.049 | [−0.069, −0.028] | 400 / 2000 |

- 같은 seed의 V2(b)와 본 학습 편차는 §6.4다. b = 앞 run만 정답, c = run 2만 정답이고 정확도 차이는 앞 run − run 2다.

## 8. 그림

- 범주 색 슬롯 1\~3(파랑 Jev, 주황 vanilla, 청록 trained)은 F의 그림과 같은 색이다. 팔레트 검증기 출력(`figs/palette_check.txt`, F에서 복사)에서 최악 CVD ΔE는 슬롯 1\~3 인접쌍 9.2, 전체쌍 9.2로 통과다. 청록(대비 2.74)은 밝은 배경 대비 3:1 미만이라 표와 막대 안 직접 라벨을 함께 둔다. 정적 PNG/SVG라 라이트 모드만 만들었다.

![과제별 3-arm 정확도 (Jev 항목)](figs/accuracy_3arm.png)

![ext: trained − vanilla](figs/ext_trained_minus_vanilla.png)

![과제별 dev 곡선](figs/dev_curves.png)

![범주별 arm macro](figs/category_macro.png)

## 9. 재현

- `nice -n 10 .venv/bin/python results/T3arm/t3arm_summary.py build --root results/T3arm --out <out>`
- `nice -n 10 .venv/bin/python results/T3arm/t3arm_summary.py verify --root results/T3arm --out <out>`
- 입력: Jev `results/F/jev_cmp/jev_runs_all.jsonl`(s6_summary 경로; T9·T10은 412-491번째 줄 = 세션 S7, verify는 `results/F/jev_cmp/sessions/S7_20261008/raw/analyze/`와 대조, 둘 다 공개 저장소에는 포함하지 않음), F 종합 `results/F/jev_cmp/summary.json`, vanilla `results/F/jev_cmp/laya/`(T1-T8 Jev 세트)와 `results/T3arm/vanilla/`(T9·T10 Jev 형식 세트, 모든 ext), vanilla + 과제 T `results/T3arm/calib_sep/<task>/`, trained run 1 `<root>/<task>/`와 run 2 `<root>/rep_s14/<task>/`, 검증 `results/T3arm/validity/`.
- 모델 로드와 평가는 하지 않는다. 통계는 `s6_summary.py`(McNemar, Holm, 군집 bootstrap, 그림 스타일), `laya_summary.py`(decision 매핑, T1 Part B), `scripts/metrics_extra.py`(coverage)를 import해 쓴다.
