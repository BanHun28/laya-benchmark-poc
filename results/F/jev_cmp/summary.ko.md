# Laya vs Jev 통제 비교 종합 (S6, 2026-10-07)

> 독립 제3자 플레이그라운드(jevplayground.com) 경유이며 API가 아니다. 모델 버전은 표기되지 않는다(Model ID `typesafe-ai/jev`). 과제당 n=40의 소표본이다. 이 문서의 모든 수치는 `results/F/jev_cmp/summary.json`과 같고, `s6_summary.py verify`가 세션 요약과 `jev_cmp.py` 재생성 출력에 대조했다(§10).

**판정.**
1. 과제마다 Jev를 그 과제에서 정확도가 가장 높은 zero-shot Laya 러너와 exact McNemar(양측, α 0.05)로 비교하면 Jev 유의 우세 4개(T1, T4, T5, T7), 비유의 4개(T2, T3, T6, T8), Laya 유의 우세 0개다. 8개 검정에 Holm 보정을 하면 Jev 유의 우세는 T1·T7의 2개만 남는다.
2. 8과제 macro 정확도는 Jev 0.828, Laya english 0.646, multilingual 0.598, Router 0.661이다. 과제 8개를 재표본한 paired bootstrap(10,000회)에서 Jev − Router는 +0.167 [+0.044, +0.293], Jev − 과제별 최고 Laya(사후 선택)는 +0.153 [+0.031, +0.281]다. 이질적인 8과제를 평균한 기술통계다.
3. 서로 독립인 단일 문항 240개(T2·T3·T4·T5·T6·T8, T6은 argmax)를 합치면 Jev 194, 과제별 최고 Laya 176이고 b/c 39/21, exact McNemar p=0.0273이다. 군집이 있는 T1(case 40개)과 T7(id 20개)은 군집 bootstrap으로 따로 보며, Jev − 최고 Laya는 T1 +0.483 [+0.371, +0.597], T7 +0.290 [+0.100, +0.470]다.
4. Jev 확률의 의미는 문항 형식마다 다르다. 단일 choice는 100% 표시가 65%이고 오답의 59%가 top ≥ 0.90이다. Boolean은 100% 표시가 0건이고, T8에서는 오답 9개가 모두 미탐(FN)이다. 다문항(T1)은 평균 top 0.733이 정확도 0.867보다 낮은 과소확신이다. 확신도로 자동 처리 여부를 가르려면 과제별 held-out 데이터로 임계값을 따로 맞춰야 한다.
5. Laya의 열세는 zero-shot 형식 일반화에서 나오고 파인튜닝으로 닫힌다. T1의 typed-decisions 파인튜닝 체크포인트는 104/120으로 Jev(104/120)와 같고(b/c 10/10), 한국어 도메인 라우팅 ft-v1은 같은 24행에서 22/24로 Jev(20/24) 이상이다. 두 줄 모두 zero-shot이 아닌 참고선이다(§3).

## 1. 개요

| 항목 | 내용 | 출처 |
|---|---|---|
| 비교 단위 | 같은 state 바이트(Laya가 읽는 JSON 직렬화 문자열 `state_text`), 같은 질문 문장, 같은 옵션 문자열과 순서. 요청 body가 폼 payload와 바이트 단위로 같았던 요청 411/411 | `docs/09_laya_vs_jev_plan.md` §4, `jev_runs_all.jsonl` `payload_exact`(공개 저장소에는 포함하지 않음) |
| Jev | 공개 플레이그라운드 `https://jevplayground.com`의 `POST /api/evaluate`. Model ID `typesafe-ai/jev` 410/410, 확률·score 소수 둘째 자리 반올림 410/410 | 세션 run card, `jev_runs_all.jsonl`(공개 저장소에는 포함하지 않음) |
| Laya | laya 0.3.23, revision `55cf4c4`, english / multilingual / Router(입력별 자동 선택), zero-shot, CPU fp32, intra-op 10 / inter-op 1, batch 8 (results/F/jev_cmp/run_laya.sh) | `results/F/jev_cmp/S0_20261006.md`, `laya_summary.md` |
| 과제 | T1\~T8, 8개. 과제당 n=40, T1은 40 case의 비교 가능 decision 120개, T7은 같은 20 id x 5개 언어 = 100 | `data/evals/jev_cmp/MANIFEST.json` |
| 기간 (KST) | 2026-10-06: 파일럿 08:09\~08:33, S1 10:04\~10:17, S1b 10:29\~10:38. 2026-10-07: S2 08:49\~09:12, S3 13:36\~13:56, S4 14:16\~14:36, S5 14:53\~15:18 (첫 클릭\~마지막 클릭) | 세션 run card |
| 요청 수 | 사이트 전체 438회 = 마스터 로그 411(S1 41, S1b 30, S2 80, S3 80, S4 80, S5 100) + 도구화 이전 27(한국어 파일럿 25, 상태 확인 2). 일자별 2026-10-06 98, 2026-10-07 340 | `jev_runs_all.jsonl`, `results/F/jev_runs_raw.jsonl`(둘 다 공개 저장소에는 포함하지 않음), `S1_summary.md` §7 |
| 간격 | Run 클릭 간격 최소 S1 17.0 s, S1b 17.3 s, S2 12.1 s, S3 15.0 s, S4 15.0 s, S5 15.0 s(중앙 15.1\~17.5 s), 파일럿 21.6 s. 규칙 ≥ 10 s | 요청 기록 `gap_from_prev_click_s`(공개 저장소에는 포함하지 않음) |
| 오류 | HTTP 502 2회: 파일럿 run 2(규칙대로 세션 중단, 13분 뒤 재개해 같은 행 성공), S2 run 1(`UNAVAILABLE`, 73.7 s 뒤 같은 payload 1회 재시도 성공). HTTP 429 0회, 제한 문구·captcha 0회 | `F_jev_20261006.md`, `S2_run_card.md` |
| 성공 요청 | 마스터 410 + 파일럿 24. 아래 분석은 마스터 410건(490 decision)과 파일럿 24행 | 같은 곳 |

## 2. 과제별 결과

### 2.1 종합 표

| 과제 | n | 형식 / 옵션 | Laya 학습 믹스 | Jev | Laya english | Laya multilingual | Laya Router | Jev vs 최고 Laya: b/c, p (Holm p) | Brier Jev / 최고 Laya | ECE Jev / 최고 Laya | 판정 (Holm 후) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 typed-decisions | 120 (40 case) | 혼합 (Multiple questions: choice 50 / Boolean 60 / 5레벨 score 10) / case당 2\~4문항, 옵션 ≤ 5 | no | 104/120 = 0.867 [0.794, 0.916] | 46/120 = 0.383 [0.301, 0.473] | 44/120 = 0.367 [0.286, 0.456] | 46/120 = 0.383 [0.301, 0.473] | english: 66/8, 1.8e-12 (1.4e-11) | 0.237 / 0.724 | 0.181 / 0.205 | Jev 유의 우세 (Jev 유의 우세) |
| T2 AG News | 40 | single choice / 4 | yes | 35/40 = 0.875 [0.739, 0.945] | 39/40 = 0.975 [0.871, 0.996] | 37/40 = 0.925 [0.801, 0.974] | 39/40 = 0.975 [0.871, 0.996] | english: 0/4, 0.1250 (0.3750) | 0.220 / 0.053 | 0.118 / 0.083 | 비유의 (비유의) |
| T3 DAIR Emotion | 40 | single choice / 6 | no | 28/40 = 0.700 [0.546, 0.819] | 30/40 = 0.750 [0.598, 0.858] | 25/40 = 0.625 [0.470, 0.758] | 30/40 = 0.750 [0.598, 0.858] | english: 2/4, 0.6875 (1.0000) | 0.537 / 0.429 | 0.278 / 0.174 | 비유의 (비유의) |
| T4 Banking77-10 | 40 | single choice / 10 (key-only) | held out (upstream build_benchmark_nb.py:760-762) | 37/40 = 0.925 [0.801, 0.974] | 29/40 = 0.725 [0.572, 0.839] | 30/40 = 0.750 [0.598, 0.858] | 29/40 = 0.725 [0.572, 0.839] | multilingual: 8/1, 0.0391 (0.1953) | 0.114 / 0.478 | 0.069 / 0.262 | Jev 유의 우세 (비유의) |
| T5 BoolQ | 40 | single Boolean / 2 | yes | 37/40 = 0.925 [0.801, 0.974] | 29/40 = 0.725 [0.572, 0.839] | 24/40 = 0.600 [0.446, 0.737] | 29/40 = 0.725 [0.572, 0.839] | english: 9/1, 0.0215 (0.1289) | 0.098 / 0.393 | 0.103 / 0.190 | Jev 유의 우세 (비유의) |
| T6 SST-5 | 40 | single score / 5 레벨 | no | 26/40 = 0.650 [0.495, 0.779] | 17/40 = 0.425 [0.285, 0.578] | 13/40 = 0.325 [0.201, 0.480] | 17/40 = 0.425 [0.285, 0.578] | english: 15/6, 0.0784 (0.3134) | 0.502 / 0.770 | 0.184 / 0.239 | 비유의 (비유의) |
| T7 MASSIVE intent-10 | 100 (20 id x 5 언어) | single choice / 10 (영어 key) | held out (upstream build_benchmark_nb.py:760-762) | 91/100 = 0.910 [0.838, 0.952] | 41/100 = 0.410 [0.319, 0.508] | 62/100 = 0.620 [0.522, 0.709] | 58/100 = 0.580 [0.482, 0.672] | multilingual: 36/7, 9.0e-06 (6.3e-05) | 0.140 / 0.584 | 0.068 / 0.216 | Jev 유의 우세 (Jev 유의 우세) |
| T8 prompt-injections | 40 | single Boolean / 2 | no | 31/40 = 0.775 [0.625, 0.877] | 31/40 = 0.775 [0.625, 0.877] | 23/40 = 0.575 [0.422, 0.715] | 29/40 = 0.725 [0.572, 0.839] | english: 5/5, 1.0000 (1.0000) | 0.307 / 0.401 | 0.194 / 0.223 | 비유의 (비유의) |

- 정확도 칸은 정답/n = 정확도 [Wilson 95%]다. b = Jev만 정답, c = Laya만 정답이고 p는 exact McNemar(양측)다. 최고 Laya는 english, multilingual, Router 중 정확도가 가장 높은 러너이고 동률이면 english, multilingual, Router 순으로 고른다(사후 선택이라 Laya에 유리하다, §9).
- 판정 규칙: p < 0.05이고 b > c면 Jev 유의 우세, c > b면 Laya 유의 우세, 아니면 비유의. 괄호는 같은 규칙을 8개 검정의 Holm 보정 p에 적용한 결과다.
- Brier는 행마다 그 행의 옵션 전체로 Σ(p − onehot)²를 낸 평균이다(Boolean은 두 칸이라 2(p − y)², score는 5레벨, T1은 argmax gold 대비 one-hot). ECE는 15 bins, top p 기준이다. Jev 확률은 소수 둘째 자리 반올림이라 Brier·ECE에 약 ±0.005의 하한 오차가 있다.
- Router 배정: T1\~T6은 전부 english, T7은 english 25 / multilingual 75(en 20은 english, de는 multilingual 15 / english 5, ja·zh-CN·ko는 multilingual), T8은 english 26 / multilingual 14.
- T1(40 case)과 T7(20 id)은 decision이 군집으로 묶여 있어 Wilson 구간과 item 단위 McNemar가 낙관적이다. 군집 bootstrap은 §4.4에 있다.
- 출처: `jev_cmp.py analyze`(T2\~T8)와 `jev_cmp.py t1 S1,S2`(T1) 재생성 출력(공개 저장소에는 포함하지 않음), 세션 요약 `sessions/S1_20261006/S1_summary.md` §2, `S2_20261007/S2_summary.md` §2\~§3, `S3_20261007/S3_summary.md` §2\~§3, `S4_20261007/S4_summary.md` §2\~§3, `S5_20261007/S5_summary.md` §2\~§4. 학습 믹스는 MANIFEST `in_training_mix`다. upstream은 T2·T5만 Laya 학습 믹스(retention)로 적고 T3·T4·T6·T8은 held out, T1(typed-decisions)·T7(MASSIVE)은 두 체크포인트 모두 학습하지 않았다고 적는다(`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`; upstream 클론은 공개 저장소에는 포함하지 않음, `https://github.com/NandhaKishorM/laya`를 commit `4aa6761`로 clone하면 재현된다). 표의 no와 held out은 모두 학습 믹스에 없다는 뜻이다.

### 2.2 T1 typed-decisions: 타입별 (같은 120 decision, 40 case)

| system | 전체 | choice (50) | Boolean / noul (60) | score 5레벨 (10) | soft acc | Brier vs soft | score MAE (E[level] vs teacher, Jev는 반올림 p) |
|---|---|---|---|---|---|---|---|
| Jev | 104/120 = 0.867 [0.794, 0.916] | 42/50 = 0.840 [0.715, 0.917] | 56/60 = 0.933 [0.841, 0.974] | 6/10 = 0.600 [0.313, 0.832] | 0.590 | 0.077 | 0.390 |
| Laya english | 46/120 = 0.383 [0.301, 0.473] | 14/50 = 0.280 [0.175, 0.417] | 28/60 = 0.467 [0.346, 0.591] | 4/10 = 0.400 [0.168, 0.687] | 0.361 | 0.333 | 0.584 |
| Laya multilingual | 44/120 = 0.367 [0.286, 0.456] | 16/50 = 0.320 [0.208, 0.458] | 26/60 = 0.433 [0.316, 0.559] | 2/10 = 0.200 [0.057, 0.510] | 0.351 | 0.574 | 0.671 |
| Laya Router | 46/120 = 0.383 [0.301, 0.473] | 14/50 = 0.280 [0.175, 0.417] | 28/60 = 0.467 [0.346, 0.591] | 4/10 = 0.400 [0.168, 0.687] | 0.361 | 0.333 | 0.584 |
| 참고: Laya typed-decisions (파인튜닝) | 104/120 = 0.867 [0.794, 0.916] | 40/50 = 0.800 [0.670, 0.888] | 57/60 = 0.950 [0.863, 0.983] | 7/10 = 0.700 [0.397, 0.892] | 0.519 | 0.059 | 0.255 |

- 타입별 exact McNemar(b/c, p): english는 choice 31/3 (7.7e-07), noul 31/3 (7.7e-07), score 4/2 (0.6875). multilingual은 choice 27/1 (2.2e-07), noul 33/3 (2.3e-07), score 6/2 (0.2891). score 10개만 n이 작아 구분되지 않는다.
- Jev Boolean에는 설명 칸이 없다. Laya에서 true/false criteria를 뺀 같은 입력 변형도 english 31/60(b/c 27/2), multilingual 25/60(b/c 34/3)로 차이가 그대로다.
- 이 120 decision의 문항별 최빈 기준선은 0.575이고 Laya base 세 러너는 모두 그보다 낮다. Jev score MAE는 응답 `score` 필드 기준 0.389다. 출처: `S2_summary.md` §2.

### 2.3 T5 BoolQ, T8 prompt-injections: Boolean 순위 품질

| 과제 | system | 정확도 (p(true) ≥ 0.5) | 예측 true (gold 20) | FN / FP | AUROC [bootstrap 95%] | AUROC Jev − Laya [paired bootstrap 95%] | 같은 40행 최적 임계값 정확도 (기술통계) |
|---|---|---|---|---|---|---|---|
| T5 | Jev (playground) | 37/40 = 0.925 [0.801, 0.974] | 21 | 1 / 2 | 0.988 [0.955, 1.000] | - | 38/40 |
| T5 | Laya english | 29/40 = 0.725 [0.572, 0.839] | 19 | 6 / 5 | 0.810 [0.662, 0.942] | +0.177 [+0.043, +0.326] | 31/40 |
| T5 | Laya multilingual | 24/40 = 0.600 [0.446, 0.737] | 18 | 9 / 7 | 0.682 [0.496, 0.838] | +0.305 [+0.152, +0.486] | 27/40 |
| T5 | Laya Router | 29/40 = 0.725 [0.572, 0.839] | 19 | 6 / 5 | 0.810 [0.662, 0.942] | +0.177 [+0.043, +0.326] | 31/40 |
| T8 | Jev (playground) | 31/40 = 0.775 [0.625, 0.877] | 11 | 9 / 0 | 1.000 [1.000, 1.000] | - | 40/40 |
| T8 | Laya english | 31/40 = 0.775 [0.625, 0.877] | 11 | 9 / 0 | 0.929 [0.840, 0.997] | +0.071 [+0.003, +0.160] | 35/40 |
| T8 | Laya multilingual | 23/40 = 0.575 [0.422, 0.715] | 9 | 14 / 3 | 0.781 [0.615, 0.919] | +0.219 [+0.081, +0.385] | 31/40 |
| T8 | Laya Router | 29/40 = 0.725 [0.572, 0.839] | 11 | 10 / 1 | 0.868 [0.738, 0.969] | +0.132 [+0.031, +0.262] | 33/40 |

- T8의 Jev는 이 40행에서 완전 분리다(gold false p(true) 0.01\~0.04, gold true 0.08\~0.99). 그래서 percentile bootstrap CI가 폭 0으로 퇴화했고 차이 CI도 낙관적이다. bootstrap은 항목 재표본 2,000회, seed 13(`jev_cmp.py` 정의). 출처: `S3_summary.md` §3, `S5_summary.md` §4.

### 2.4 T6 SST-5: 레벨 적중과 척도 사용

| system | argmax 레벨 정확도 (주 지표) | 반올림 E[level] 정확도 (표시 규칙) | MAE of E[level] | 평균 E − gold | ±1 레벨 이내 | 예측 레벨 분포 0/1/2/3/4 (argmax, gold 각 8) |
|---|---|---|---|---|---|---|
| Jev (playground) | 26/40 = 0.650 [0.495, 0.779] | 27/40 = 0.675 [0.520, 0.799] | 0.432 | −0.014 | 0.875 | 4/13/6/12/5 |
| Laya english | 17/40 = 0.425 [0.285, 0.578] | 16/40 = 0.400 [0.263, 0.554] | 0.888 | −0.687 | 0.650 | 10/15/10/5/0 |
| Laya multilingual | 13/40 = 0.325 [0.201, 0.480] | 13/40 = 0.325 [0.201, 0.480] | 1.419 | −1.280 | 0.400 | 11/29/0/0/0 |
| Laya Router | 17/40 = 0.425 [0.285, 0.578] | 16/40 = 0.400 [0.263, 0.554] | 0.888 | −0.687 | 0.650 | 10/15/10/5/0 |

- Jev vs english: argmax b/c 15/6 p=0.0784(비유의), 반올림 E b/c 15/4 p=0.0192, MAE 차이 −0.456 [−0.711, −0.207]. Jev vs multilingual: argmax 18/5 p=0.0106, 반올림 E 19/5 p=0.0066, MAE 차이 −0.987 [−1.341, −0.622]. MAE 차이 CI는 항목 재표본 2,000회, seed 13. 출처: `S4_summary.md` §2.
- Laya english가 마지막 레벨 4를 고른 행은 0/40이고 multilingual은 40/40행을 레벨 0·1로 냈다(gold는 레벨마다 8행). 척도 압축이 Laya의 주된 실패다.

### 2.5 T7 MASSIVE intent-10: 언어별 (같은 20 id, 언어당 n=20)

| system | en | de | ja | zh-CN | ko | 합산 100 |
|---|---|---|---|---|---|---|
| Jev (playground) | 18/20 = 0.900 | 18/20 = 0.900 | 19/20 = 0.950 | 18/20 = 0.900 | 18/20 = 0.900 | 91/100 = 0.910 [0.838, 0.952] |
| Laya english | 14/20 = 0.700 | 7/20 = 0.350 | 9/20 = 0.450 | 9/20 = 0.450 | 2/20 = 0.100 | 41/100 = 0.410 [0.319, 0.508] |
| Laya multilingual | 17/20 = 0.850 | 8/20 = 0.400 | 16/20 = 0.800 | 12/20 = 0.600 | 9/20 = 0.450 | 62/100 = 0.620 [0.522, 0.709] |
| Laya Router | 14/20 = 0.700 | 7/20 = 0.350 | 16/20 = 0.800 | 12/20 = 0.600 | 9/20 = 0.450 | 58/100 = 0.580 [0.482, 0.672] |
| Jev vs english: b/c, p | 4/0, 0.1250 | 11/0, 0.0010 | 10/0, 0.0020 | 9/0, 0.0039 | 17/1, 0.0001 | 51/1, 2.4e-14 (독립 아님) |
| Jev vs multilingual: b/c, p | 3/2, 1.0000 | 11/1, 0.0063 | 3/0, 0.2500 | 8/2, 0.1094 | 11/2, 0.0225 | 36/7, 9.0e-06 (독립 아님) |
| Jev vs Router: b/c, p | 4/0, 0.1250 | 12/1, 0.0034 | 3/0, 0.2500 | 8/2, 0.1094 | 11/2, 0.0225 | 38/5, 2.5e-07 (독립 아님) |

- 옵션은 10개 영어 key 렌더링이고 발화만 언어별로 다르다. 합산 McNemar는 같은 id가 5번 들어가 독립 표본이 아니다. 출처: `S4_summary.md` §3, `S5_summary.md` §2\~§3, `jev_cmp.py analyze S4,S5 <5개 세트>`(출력은 공개 저장소에는 포함하지 않음).

## 3. 참고선 (zero-shot 아님)

| 참고선 | 과제·표본 | 결과 | Jev 대비 | 출처 |
|---|---|---|---|---|
| Laya typed-decisions 체크포인트 (typed-decisions train으로 파인튜닝) | T1, 같은 120 decision | 104/120 = 0.867 [0.794, 0.916]. choice 40/50, noul 57/60, score 7/10, soft acc 0.519 | Jev 104/120 = 0.867 [0.794, 0.916], b/c 10/10, p=1.0000 | `S2_summary.md` §2.1\~§2.2 |
| Laya ft-v1 (한국어 domain_8 train으로 파인튜닝) | 한국어 도메인 라우팅 파일럿 24행 (`key: 한국어 설명` 8옵션) | 22/24 = 0.917 [0.742, 0.977]. 같은 행 zero-shot multilingual 10/24 = 0.417 | Jev 20/24 = 0.833 [0.641, 0.933]. Jev vs ft-v1 b/c 0/2, p=0.5000. Jev vs zero-shot 10/0, p=0.0020 | `results/F/jev_playground_manual_20261006.md` §3 |
| Laya ft-v1 | ko_massive_domain_8 test 절반 250행 | 0.900 [0.860, 0.936] (bootstrap CI). 같은 행 zero-shot multilingual 0.492 [0.432, 0.552] | Jev는 이 250행을 받지 않았다 | `results/P4/metrics/full_20261003-1156_summary.md:19` |

- 두 파인튜닝 선은 같은 분포의 train으로 학습했다. 학습 데이터가 없는 zero-shot 시스템(Jev)과의 비교에서 in-domain 이점을 가진다. 파일럿에서 Jev가 ft-v1에 진 2행은 라벨 설명에 없는 MASSIVE 관례(`play` → `media`)였고 ft-v1은 이를 학습했다(파일럿 §4). T7은 intent 과제라 ft-v1을 T7 참고선으로 두지 않았다(docs/09 열린 질문 5).

## 4. 종합

### 4.1 판정 집계 (8과제, Jev vs 최고 zero-shot Laya)

| 기준 | Jev 유의 우세 | 비유의 | Laya 유의 우세 |
|---|---|---|---|
| exact McNemar, 보정 전 α 0.05 | 4 (T1, T4, T5, T7) | 4 (T2, T3, T6, T8) | 0 |
| Holm 보정 (8개 검정) | 2 (T1, T7) | 6 (T2, T3, T4, T5, T6, T8) | 0 |

Holm 보정 p: T1 1.4e-11, T7 6.3e-05, T5 0.1289, T4 0.1953, T6 0.3134, T2 0.3750, T3 1.0000, T8 1.0000. T6은 주 지표(argmax)로 비유의이지만 보조 지표(반올림 E, MAE)로는 Jev 쪽 차이가 0을 벗어난다(§2.4).

### 4.2 macro 평균 정확도 (8과제 단순 평균)

| system | macro 정확도 | Jev − system [과제 bootstrap 95%] | bootstrap에서 차이 ≤ 0 비율 | T1 제외 7과제 macro |
|---|---|---|---|---|
| Jev | 0.828 | - | - | 0.823 |
| Laya english | 0.646 | +0.182 [+0.041, +0.325] | 0.0051 | 0.684 |
| Laya multilingual | 0.598 | +0.230 [+0.121, +0.339] | 0.0000 | 0.631 |
| Laya Router | 0.661 | +0.167 [+0.044, +0.293] | 0.0029 | 0.701 |
| 과제별 최고 Laya (사후 선택) | 0.675 | +0.153 [+0.031, +0.281] | 0.0065 | 0.717 |

- 과제별 정확도(T1은 120 decision, T7은 100 항목 합산)를 같은 가중치로 평균했다. bootstrap은 8개 과제를 복원 재표본(10,000회, seed 13)해 Jev − Laya의 평균을 다시 계산한 percentile 구간이다. 과제가 8개뿐이고 서로 이질적이라 모집단 추론이 아니라 기술통계다.
- T1(차이가 가장 큰 과제)을 빼도 Jev가 앞선다(Jev 0.823 vs 최고 Laya 0.717).

### 4.3 독립 단일 문항 합산 exact McNemar (T2·T3·T4·T5·T6·T8, 240항목)

| Laya 비교 대상 | Jev 정답 | Laya 정답 | b | c | exact p | 과제별 b/c (T2 / T3 / T4 / T5 / T6 / T8) |
|---|---|---|---|---|---|---|
| 과제별 최고 Laya (사후 선택) | 194/240 | 176/240 | 39 | 21 | 0.0273 | 0/4 / 2/4 / 8/1 / 9/1 / 15/6 / 5/5 |
| english 고정 | 194/240 | 175/240 | 40 | 21 | 0.0204 | 0/4 / 2/4 / 9/1 / 9/1 / 15/6 / 5/5 |
| multilingual 고정 | 194/240 | 152/240 | 58 | 16 | 9.7e-07 | 0/2 / 6/3 / 8/1 / 15/2 / 18/5 / 11/3 |
| Router 고정 | 194/240 | 173/240 | 42 | 21 | 0.0111 | 0/4 / 2/4 / 9/1 / 9/1 / 15/6 / 7/5 |

- 항목이 과제를 넘어 독립이라고 보고 합친 검정이다. 과제별 최고 러너 선택은 Laya에 유리한 사후 선택이고, 고정 러너 세 줄이 그 민감도다. T1·T7은 군집 때문에 넣지 않았다.

### 4.4 군집 과제: T1 (case 군집), T7 (id 군집)

| 과제 | 군집 | Laya | 정확도 차이 Jev − Laya | 군집 bootstrap 95% | 참고: item 단위 McNemar b/c, p (독립 가정) |
|---|---|---|---|---|---|
| T1 | 40 case, 120 decision | english (최고) | +0.483 | [+0.371, +0.597] | 66/8, 1.8e-12 |
| T1 | 40 case, 120 decision | multilingual | +0.500 | [+0.385, +0.614] | 66/6, 7.3e-14 |
| T1 | 40 case, 120 decision | Router | +0.483 | [+0.371, +0.597] | 66/8, 1.8e-12 |
| T7 | 20 id x 5 언어 = 100 | english | +0.500 | [+0.370, +0.640] | 51/1, 2.4e-14 |
| T7 | 20 id x 5 언어 = 100 | multilingual (최고) | +0.290 | [+0.100, +0.470] | 36/7, 9.0e-06 |
| T7 | 20 id x 5 언어 = 100 | Router | +0.330 | [+0.170, +0.490] | 38/5, 2.5e-07 |

- 군집을 복원 재표본(10,000회, seed 13)하고 뽑힌 군집의 decision 전체로 정답 수 차이를 다시 계산했다. 모든 구간이 0을 포함하지 않는다.

## 5. 보정과 확신도

### 5.1 과제별 Brier·ECE와 과대/과소확신

| 과제 | Jev Brier | Jev ECE | Jev 평균 top − 정확도 | Jev 오답 중 top ≥ 0.90 | 최고 Laya | Laya Brier | Laya ECE | Laya 평균 top − 정확도 | Laya 오답 중 top ≥ 0.90 |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 0.237 | 0.181 | −0.134 | 1/16 | english | 0.724 | 0.205 | +0.152 | 1/74 |
| T2 | 0.220 | 0.118 | +0.102 | 4/5 | english | 0.053 | 0.083 | −0.045 | 0/1 |
| T3 | 0.537 | 0.278 | +0.201 | 7/12 | english | 0.429 | 0.174 | +0.150 | 4/10 |
| T4 | 0.114 | 0.069 | +0.048 | 1/3 | multilingual | 0.478 | 0.262 | +0.082 | 6/10 |
| T5 | 0.098 | 0.103 | −0.012 | 0/3 | english | 0.393 | 0.190 | +0.172 | 4/11 |
| T6 | 0.502 | 0.184 | +0.101 | 0/14 | english | 0.770 | 0.239 | +0.229 | 0/23 |
| T7 | 0.140 | 0.068 | +0.037 | 5/9 | multilingual | 0.584 | 0.216 | +0.212 | 14/38 |
| T8 | 0.307 | 0.194 | +0.146 | 2/9 | english | 0.401 | 0.223 | +0.187 | 6/9 |

평균 top − 정확도 > 0은 과대확신, < 0은 과소확신이다. Jev의 top은 표시 확률(2자리 반올림), Laya는 `answer_confidence`(Boolean은 max(p, 1 − p), score는 최대 레벨 확률)다.

### 5.2 Jev 확신도: 문항 형식별

| 형식 | 과제 | n | 정확도 | 평균 top | 100% 표시 | 오답 | 오답 중 top ≥ 0.90 |
|---|---|---|---|---|---|---|---|
| 단일 choice | T2·T3·T4·T7 | 220 | 0.868 | 0.949 | 144 (65%) | 29 | 17 (59%) |
| 단일 Boolean | T5·T8 | 80 | 0.850 | 0.917 | 0 (0%) | 12 | 2 (17%) |
| 단일 score | T6 | 40 | 0.650 | 0.751 | 0 (0%) | 14 | 0 (0%) |
| Multiple questions (2\~4문항) | T1 | 120 | 0.867 | 0.733 | 9 (8%) | 16 | 1 (6%) |

- **단일 choice**: 100% 표시가 흔하고 오답 다수가 0.90 이상이다(T2 4/5, T3 7/12, T4 1/3, T7 5/9). T3에서는 정답 옵션을 0%로 표시한 행이 7/40다. top 확률 임계값으로 오답을 거르기 어렵다.
- **Boolean**: 100% 표시가 없다(0/80). 임계값의 적정 위치는 과제마다 다르다. T5는 예측 true 21(gold 20)로 0.5가 거의 최적이고(0.5에서 37/40, 같은 40행 최적 38/40), 오답 3개가 모두 top < 0.90이다. T8은 예측 true 11(gold 20)이고 오답 9개가 전부 미탐이며, gold false의 p(true)가 0.04 이하라 최적 임계값이 0.5보다 훨씬 낮다(0.04 초과 0.08 이하에서 40/40).
- **Multiple questions (T1)**: 과소확신이다. 타입별 평균 top(정답 / 오답)은 choice 0.775 / 0.526, noul 0.745 / 0.550, score 0.767 / 0.672이고 오답 16개 중 top ≥ 0.90은 1개뿐이다. 여기서는 낮은 top이 오답 신호라 보류 임계값이 작동할 여지가 있다.
- **score (T6)**: 100% 표시 0/40, 오답 14개 모두 top < 0.90, 평균 top 0.751 vs 정확도 0.650로 약한 과대확신이다.

### 5.3 Laya 확신도

- 최고 Laya 러너를 형식별로 묶으면 모두 과대확신이다(평균 top − 정확도: 단일 choice +0.130, Boolean +0.180, score +0.229, T1 +0.152). 과제별로 과소확신은 T2 english(−0.045)뿐이다. 오답 중 top ≥ 0.90은 단일 choice 24/59, Boolean 10/20다.
- 형식이나 언어가 낯설수록 확신한 채로 틀린다. T7 de에서 english ECE 0.513, multilingual 0.453이고, T8 english는 p(true)가 정확히 0 또는 1인 행이 27/40다. multilingual은 T6에서 레벨 0·1로 몰리면서 오답 27개 중 10개를 0.90 이상으로 냈다(`S4_summary.md` §2.5).
- Laya english의 T2 ECE 0.083처럼 학습 믹스 과제에서는 보정이 양호하다. upstream은 도메인별 temperature fitting 뒤 ECE를 보고한다(README "Where Jev leads").

### 5.4 확신도 기반 자동화에 대한 함의

- 같은 "90%"가 Jev 단일 choice에서는 오답을 거르지 못하고(오답의 59%가 0.90 이상), Jev T1에서는 대부분의 오답을 거른다. Boolean은 임계값 자체가 과제마다 다른 자리에 있다.
- 따라서 두 시스템 모두 과제(질문 형식, 옵션 수, 언어)별 held-out 표본으로 임계값이나 temperature를 맞추고, coverage@오류를 확인한 뒤 자동 처리 범위를 정해야 한다. 이 문서의 최적 임계값 열은 같은 40행에서 고른 기술통계라 그대로 쓰면 안 된다.

## 6. 견고성

| 점검 | Jev | Laya | 출처 |
|---|---|---|---|
| 결정성: 같은 payload 재전송 (T2 10행, 16\~23분 뒤, 중앙 20분) | 라벨 10/10 같음, 확률 벡터 9/10 같음(최대 \|Δp\| 0.01), 토큰 수 10/10 같음 | english로 T1 200 decision을 재실행한 답이 완전히 같았다 | `S1b_summary.md` §2, `laya_summary.md` §5 |
| 옵션 순서 flip (T2 20행, Laya probe와 같은 순열 1개) | 0/20 = 0.000 [0.000, 0.161] | english 0/20, multilingual 0/20 (probe 40행 전체도 0.000) | `S1b_summary.md` §3 |

- 순서 flip은 정보량이 낮다. AG News 4옵션의 고확신 행 위주라 두 시스템 모두 0이었고, 제3자 공개 Jev flip 0.13도 배제하지 못한다(그 값에서 0/20이 나올 확률 0.062).

### 6.1 T7 언어 간 일관성과 언어 페널티 (같은 20 id x 5개 언어)

| system | 5개 언어 모두 같은 라벨 | 언어쌍 평균 일치 (10쌍) | 5개 언어 모두 정답 | 5개 언어 모두 오답 | en 대비 페널티 de / ja / zh-CN / ko | 평균 페널티 |
|---|---|---|---|---|---|---|
| Jev (playground) | 18/20 | 0.935 | 17 | 1 | +0.000 / +0.050 / +0.000 / +0.000 | +0.012 |
| Laya english | 0/20 | 0.325 | 0 | 5 | −0.350 / −0.250 / −0.250 / −0.600 | −0.362 |
| Laya multilingual | 5/20 | 0.545 | 5 | 1 | −0.450 / −0.050 / −0.250 / −0.400 | −0.287 |
| Laya Router | 4/20 | 0.485 | 4 | 0 | −0.350 / +0.100 / −0.100 / −0.250 | −0.150 |

- Jev는 언어를 바꿔도 같은 결정을 낸다. 라벨이 언어마다 달라진 id 2개는 번역 문장의 내용이 언어마다 달랐던 경우다(`S5_summary.md` §2.4, §3.4). Laya는 english가 ko에서 0.100, multilingual도 de에서 0.400로 떨어진다. 언어당 n=20이라 페널티 크기는 방향 신호다.

## 7. 지연과 비용

**배포 형태가 다르다.** Jev 값은 서울의 브라우저 → 플레이그라운드 서버 → Jev로 이어지는 인터넷 왕복이고, Laya 값은 같은 Apple M4 Pro 안의 in-process 호출과 localhost HTTP다. 아래 값의 차이는 모델 속도 비교가 아니다.

### 7.1 Jev (마스터 로그 성공 410건)

| 요청 형식 | 과제 | 요청 | 표시값 'server + network' 중앙 (p5\~p95) ms | 브라우저 POST 중앙 (p5\~p95) ms | POST − latencyMs 중앙 ms |
|---|---|---|---|---|---|
| 단일 choice | T2(S1b 포함)·T3·T4·T7 | 250 | 227 (188\~332.7) | 463 (415.9\~606.2) | 231.6 |
| 단일 Boolean | T5·T8 | 80 | 215.5 (175\~296.5) | 453.5 (407\~593.1) | 231.5 |
| 단일 score | T6 | 40 | 236 (189.8\~287.6) | 477.5 (417.9\~597.1) | 233.9 |
| Multiple questions 2\~4문항 | T1 | 40 | 225 (191.6\~300.2) | 480 (414.8\~753.2) | 245.2 |
| 단일 문항 전체 | - | 370 | 226.5 (184\~327) | 463 (414\~601.8) | 231.7 |
| 전체 | - | 410 | 226 (184\~325.6) | 465 (414\~616.2) | 232.3 |

- 표시값은 응답 `latencyMs`의 반올림이고 화면 표시와 응답이 410/410 일치했다(세션 요약). 정의는 공개되지 않았고 브라우저와 플레이그라운드 사이 구간(중앙 약 232 ms)이 빠져 있다. 전체 중앙 226 ms는 제3자 공개 Jev p50 236\~276 ms(`third_party/laya/README.md:1288`)보다 약간 낮다. 요청당 문항이 2\~4개여도 표시값 중앙은 225 ms로 1문항(226.5 ms)과 비슷하다.

### 7.2 Laya (로컬, Apple M4 Pro, 기존 측정 인용)

| 경로 | 체크포인트 | 장치 | 1문항 ms | 3문항 ms | 출처 |
|---|---|---|---|---|---|
| in-process 연속 (D1, short state) | english | CPU fp32 10스레드 | 86.6 | 184.4 | `results/D/D_summary_20261003.md:34` |
| in-process 연속 (D1, short state) | multilingual | CPU fp32 10스레드 | 37.7 | 56.4 | `results/D/D_summary_20261003.md:36` |
| in-process 연속 (D1, short state) | english | MPS | 31.8 | 79.6 | `results/D/D_summary_20261003.md:40` |
| in-process 연속 (D1, short state) | multilingual | MPS | 13.8 | 22.5 | `results/D/D_summary_20261003.md:42` |
| in-process 간헐 호출 1 s 간격 (D1c) | multilingual | CPU | 76.2 | 97.6 | `results/D/D_summary_20261003.md:87`, `results/D/D_summary_20261003.md:88` |
| in-process 간헐 호출 1 s 간격 (D1c) | multilingual | MPS | 49.2 | 51 | `results/D/D_summary_20261003.md:89`, `results/D/D_summary_20261003.md:90` |
| laya-serve HTTP 연속 c=1 (D6) | multilingual | MPS | 20.3 | 45.6 | `results/D/D_summary_20261003.md:203`, `results/D/D_summary_20261003.md:209` |
| laya-serve HTTP 연속 c=1 (D6) | multilingual | CPU 10스레드 | 50.7 | 99.5 | `results/D/D_summary_20261003.md:222`, `results/D/D_summary_20261003.md:224` |
| `/poc/decide` HTTP 연속 (P2, p50) | ft-v1 | MPS | 20.1 | - | `results/poc/P2_20261003.md:67` |

- Jev 요청의 Run 클릭 간격은 최소 12.1 s(S2)였고 S3\~S5는 15 s 간격 가드로 보냈다(§1, 세션 run card). 연속 호출이 아니므로 Laya 쪽의 가까운 조건은 간헐 호출(D1c)이다. 그 조건에서도 multilingual 1문항은 MPS 49.2 ms, CPU 76.2 ms다. laya-serve open-loop 10 RPS 3문항 p50 63.5 / p95 79.4 ms(D6)는 서버 부하 조건의 값이다.
- 그림 `figs/latency.png`는 이 두 표의 값을 로그 축에 같이 놓은 것이다.

### 7.3 토큰과 비용

| 과제 | 요청 | decision | 입력 / 출력 토큰 중앙 (요청당) | 입력 / 출력 토큰 중앙 (decision당) | decision당 평균 토큰 (합계 ÷ decision) | 1,000 decision당 Jev 비용 (USD, 단가 확인 필요) |
|---|---|---|---|---|---|---|
| T1 | 40 | 120 | 761.5 / 151 | 243.8 / 57.5 | 311.2 | 0.0131 |
| T2 | 70 | 70 | 425 / 68 | 425 / 68 | 498.3 | 0.0209 |
| T3 | 40 | 40 | 387.5 / 61 | 387.5 / 61 | 451.2 | 0.0189 |
| T4 | 40 | 40 | 476 / 116.5 | 476 / 116.5 | 595.0 | 0.0250 |
| T5 | 40 | 40 | 402.5 / 20 | 402.5 / 20 | 435.4 | 0.0183 |
| T6 | 40 | 40 | 365.5 / 17 | 365.5 / 17 | 382.9 | 0.0161 |
| T7 | 100 | 100 | 538 / 150 | 538 / 150 | 695.8 | 0.0292 |
| T8 | 40 | 40 | 305 / 20 | 305 / 20 | 340.5 | 0.0143 |
| 전체 | 410 | 490 | 439.5 / 70 | 423 / 68 | 469.4 | 0.0197 |

- 공식: 1,000 decision당 비용 = (입력 + 출력 토큰 합계 ÷ decision 수) x 1,000 x $0.042 ÷ 1,000,000. 단가 $0.042 / 1M tokens는 upstream README가 인용한 제3자 수치(`third_party/laya/README.md:1291`)이고 입력·출력 단가 구분이 없다. 이 세션들에서 공식 단가를 확인하지 않았다(**단가 확인 필요**). 전체 490 decision의 토큰 합계는 입력 193,982, 출력 36,012다.
- 출력 토큰은 형식에 따라 다르다(Boolean 20, score 17, choice는 옵션 수와 라벨 길이에 따라 61\~150). 여러 문항을 한 요청에 묶으면(T1) state 토큰이 공유돼 decision당 토큰이 줄어든다.
- 참고: 한국어 파일럿(8옵션, `key: 한국어 설명`)은 요청당 입력 716 / 출력 255 토큰이었다(`results/F/jev_playground_manual_20261006.md` §3).
- Laya의 한계 비용은 토큰 과금이 없고 로컬 연산뿐이다. 단일 프로세스 laya-serve의 연속 1문항 처리량은 MPS 48.4 RPS, CPU 19.65 RPS(D6, `results/D/D_summary_20261003.md:203`, `:222`)라 1,000 decision에 각각 약 20.7 s, 50.9 s의 머신 시간이 든다. 전력과 장비 감가상각은 측정하지 않았다.

## 8. 해석

- **Jev가 앞서는 곳: 지시 따르기와 처음 보는 형식.** T1 typed-decisions(Jev − english +0.483, case 군집 CI [+0.371, +0.597]), Banking77-10(T4, multilingual 대비 b/c 8/1, p=0.0391, Holm 0.1953), BoolQ(T5, Laya 학습 믹스 과제인데도 AUROC 0.988 vs 0.810로 순위 품질 자체가 다르다), SST-5(T6, 주 지표 argmax는 p=0.0784로 비유의지만 MAE 0.432 vs 0.888, Laya의 척도 압축), 다국어 intent(T7, Jev 언어별 0.900\~0.950, multilingual 대비 id 군집 CI [+0.100, +0.470]). 이 중 T5만 Laya 학습 믹스 과제이고 나머지(T1·T4·T6·T7)는 두 체크포인트가 학습하지 않은 소스다(§2.1).
- **비슷한 곳: AG News, Emotion, prompt-injections.** T2는 Laya 쪽 방향(b/c 0/4)이지만 비유의이고 Laya 학습 믹스 과제다. T3는 b/c 2/4다. T8은 정확도가 같지만(0.775) 오류 구조가 다르다. Jev는 오탐 0·미탐 9로 역할 지시형 주입을 놓치고, Laya english는 독일어 덮어쓰기 문장을 놓친다(`S5_summary.md` §4.3). Laya가 같거나 앞선 이 세 과제 중 학습 믹스 과제는 T2뿐이고 T3·T8은 held out이다.
- **Laya의 레버 1, 파인튜닝.** T1 파인튜닝 체크포인트 104/120 = Jev, 한국어 ft-v1 22/24 ≥ Jev 20/24. upstream의 자기 평가("a fast base to specialise, not ... a zero-shot decision engine", `third_party/laya/README.md:1530` Fine-Tuning 절)와 맞는다. 다만 두 선 모두 같은 분포의 train을 쓴 in-domain 결과다.
- **레버 2, 러너 선택.** english와 multilingual의 차이가 과제마다 크고 방향도 바뀐다(T5 0.725 vs 0.600, T8 0.775 vs 0.575, T7 ja 0.450 vs 0.800, T4는 multilingual 0.750 > english 0.725). Router는 언어로만 고르므로 영어 과제는 전부 english, 비라틴 문자는 multilingual로 보내고 de는 섞인다(T7 de Router 0.350).
- **레버 3, 옵션 렌더링.** 같은 T4 40행·같은 옵션 집합에서 `key: key spaced`(v0)와 key-only만 바꿔도 english 0.825 → 0.725(b/c 4/0, p=0.1250), multilingual 0.575 → 0.750(0/7, p=0.0156)로 움직인다(`laya_summary.md` §4b). 비교에서는 두 시스템에 같은 문자열을 넣어 통제했고, 배포에서는 렌더링도 검증 대상이다. Jev가 렌더링에 얼마나 민감한지는 측정하지 않았다.
- **운영 관점.** 학습 데이터 없이 바로 zero-shot 정확도가 필요하면 Jev 쪽이 유리하다. 지연·비용·데이터 외부 전송이 더 중요하고 과제별 학습 데이터를 만들 수 있으면 Laya를 파인튜닝해 쓰는 쪽이 맞다. 어느 쪽이든 확신도 임계값은 과제별로 다시 맞춰야 한다(§5.4).

## 9. 위협과 한계

- **플레이그라운드 ≠ API.** 모델 버전이 표기되지 않는다(Model ID만 `typesafe-ai/jev`). 확률이 소수 둘째 자리로 반올림돼 Brier·ECE에 약 ±0.005 오차가 생기고 AUROC에 동점이 생긴다. 서버 측 프롬프트 래핑이나 정규화가 있을 수 있고 "Real model execution" 주장은 검증할 수 없다. 표시 지연의 정의도 공개되지 않았다.
- **소표본.** 과제당 n=40이면 Wilson 95% 구간 반폭이 약 ±0.15다(p=0.5 기준, 예: T4 Jev [0.801, 0.974]). T7은 언어당 n=20(약 ±0.2)다. docs/09 §6 기준으로 차이가 약 0.2보다 작으면 대부분 구분되지 않는다.
- **표본 쉬움(seed 13).** T3에서 Jev 28/40 = 0.700 [0.546, 0.819]의 구간이 제3자 공개치 0.480을 포함하지 않고 Laya english 0.750도 upstream 0.573보다 높다. 짝 비교에는 쓰되 공개치와 비교해 일반화하지 않는다. T2는 Jev 35/40 = 0.875 [0.739, 0.945]의 구간이 공개치 0.910을 포함한다.
- **T1 teacher 미확인.** gold는 teacher 분포의 argmax이고 teacher와 Jev의 관계는 확인하지 못했다. Jev 0.867은 공개치 0.727(2,000 decision, 다른 문항 구성)보다 높다. teacher 정렬 효과를 배제할 수 없다(docs/09 열린 질문 10).
- **Jev는 다문항을 함께 평가한다.** T1에서 Jev는 case의 질문 2\~4개를 한 요청에서 함께 평가했고 Laya는 질문마다 독립 평가했다. 이 차이의 효과는 분리하지 않았다.
- **학습 오염.** upstream 표기로 Laya 학습 믹스에 들어간 과제는 T2·T5뿐이고 나머지는 held out이다(§2.1). 이 표기는 upstream의 자기 보고이고 학습 데이터 자체는 확인하지 않았다. Jev의 학습 데이터는 알 수 없고 모든 소스가 공개 데이터셋이다.
- **러너 사후 선택.** 과제별 최고 Laya는 결과를 보고 고른 것이라 Laya에 유리하다. 모든 러너를 표에 남겼고 고정 러너 기준 합산(§4.3)도 같은 방향이다.
- **다중 비교.** 8개 과제 검정에 Holm 보정을 하면 T1·T7만 유의하다(T5 0.1289, T4 0.1953, T6 0.3134). 보정 전 판정 4/4/0은 탐색적 요약으로 읽는다.
- **군집과 퇴화.** T1(case)·T7(id)의 item 단위 검정은 낙관적이라 군집 bootstrap을 따로 냈다. T8 Jev AUROC CI는 완전 분리로 퇴화했다.
- **입력 표현의 제약.** 플레이그라운드 Boolean에는 설명 칸이 없고 Score는 5레벨만 받으며 choice 입력은 80자로 잘린다. 그래서 T1은 200개 중 120개만 비교했고 T4는 key-only로 다시 만들었다(docs/09 §2).
- **지연·비용.** 지연은 배포 형태가 달라 모델 속도 비교가 아니다. Jev 단가는 제3자 인용치이고 확인되지 않았다.

## 10. 재현

```bash
source env.sh
# Jev 세션 분석 (모델 호출·사이트 요청 없음, 기록된 jsonl만 읽는다; 세션 원기록과 T2 세트는 공개 저장소에는 포함하지 않음)
.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S1 T2_ag_news_40
.venv/bin/python results/F/jev_cmp/jev_cmp.py stability S1 S1b T2_ag_news_40
.venv/bin/python results/F/jev_cmp/jev_cmp.py t1 S1,S2
.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S2 T3_emotion_40
.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S3 T4_banking77_10opt_40
.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S3 T5_boolq_40
.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S4 T6_sst5_40
for L in en de; do .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S4 T7_massive_intent_10opt_${L}_20; done
for L in ja zh-CN ko; do .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S5 T7_massive_intent_10opt_${L}_20; done
.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S5 T8_prompt_injections_40
.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S4,S5 T7_massive_intent_10opt_en_20,T7_massive_intent_10opt_de_20,T7_massive_intent_10opt_ja_20,T7_massive_intent_10opt_zh-CN_20,T7_massive_intent_10opt_ko_20
# Laya 측 (S0, CPU fp32) 과 세트 빌드
export HF_HOME=$PWD/data/raw/hf && .venv/bin/python scripts/build_jev_cmp_sets.py all
bash results/F/jev_cmp/run_laya.sh && .venv/bin/python results/F/jev_cmp/laya_summary.py
# S6 종합: summary.json, summary.ko.md, figs/ 생성과 대조
.venv/bin/python results/F/jev_cmp/s6_summary.py build
.venv/bin/python results/F/jev_cmp/s6_summary.py verify
```

| 파일 | 내용 |
|---|---|
| `results/F/jev_cmp/summary.md`, `summary.json` | 이 문서와 같은 수치의 JSON(Laya의 항목별 정오 비트열 포함, Jev는 집계만) |
| `results/F/jev_cmp/figs/accuracy_by_task.{png,svg}` | 과제별 정확도, Wilson 95% CI, 판정 |
| `results/F/jev_cmp/figs/t7_languages.{png,svg}` | T7 언어별 정확도, 언어별 McNemar |
| `results/F/jev_cmp/figs/latency.{png,svg}` | 배포 형태별 지연(로그 축) |
| `results/F/jev_cmp/s6_summary.py` | build / verify |
| `results/F/jev_cmp/S6_20261007.md` | S6 run card |
| `results/F/jev_cmp/jev_runs_all.jsonl` | Jev 요청 마스터 로그 411줄(세션 요청 로그의 이어붙임과 동일, build가 assert, 공개 저장소에는 포함하지 않음) |
| `results/F/jev_cmp/sessions/S{1,1b,2,3,4,5}_*/` | 세션 요약, run card, 요청 로그, 원기록(요청 로그와 원기록은 공개 저장소에는 포함하지 않음) |
| `results/F/jev_cmp/laya/*.json`, `laya_summary.{md,json}` | Laya 리포트(S0) |
| `data/evals/jev_cmp/MANIFEST.json` | 세트 n, `jev_comparable_n`, `in_training_mix`, 소스 revision |
| `results/F/jev_playground_manual_20261006.md`, `results/F/jev_runs_raw.jsonl`, `jev_sample_24.jsonl` | 한국어 파일럿(`jev_runs_raw.jsonl`은 공개 저장소에는 포함하지 않음) |
| `results/D/D_summary_20261003.md`, `results/poc/P2_20261003.md` | Laya 지연 인용 출처 |

## 그림

![과제별 정확도](figs/accuracy_by_task.png)

![T7 언어별 정확도](figs/t7_languages.png)

![지연](figs/latency.png)

그림은 범주 색 슬롯 1\~4(파랑 Jev, 주황 Laya english, 청록 Laya multilingual, 노랑 Laya Router)를 쓴다. 팔레트 검증기(`figs/palette_check.txt`)에서 최악 CVD ΔE는 슬롯 1\~3 인접쌍 9.2, 전체쌍 9.2, 슬롯 1\~4 인접쌍 9.1로 모두 통과했다. 청록(대비 2.74)과 노랑(2.11)은 밝은 배경 대비 3:1 미만이라 막대 안 직접 라벨과 이 문서의 표를 함께 둔다. 정적 PNG/SVG라 라이트 모드만 만들었다.
