# S2 요약: T1 typed-decisions (A안 39 + S1 row 30) + T3 DAIR Emotion 40 (2026-10-07)

**판정.**
1. **T1, 같은 120 decisions.** Jev 104/120 = **0.867** [0.794, 0.916]. Laya english·Router 46/120 = 0.383, multilingual 44/120 = 0.367이고 셋 다 문항별 최빈 기준선 0.575보다 낮다. Jev vs english는 b=66 / c=8(exact McNemar p < 0.0001), vs multilingual은 b=66 / c=6(p < 0.0001)이다. choice(0.840 vs 0.280·0.320)와 noul(0.933 vs 0.467·0.433)에서 모두 유의하고, 5레벨 score 10개만 n이 작아 구분되지 않는다(6/10 vs 4/10·2/10, p=0.69·0.29). 참고선인 파인튜닝 체크포인트(typed-decisions, zero-shot 아님)도 104/120이라, Jev zero-shot은 이 체크포인트와 구분되지 않는다(b=10 / c=10, p=1.0).
2. **noul은 같은 입력에서도 차이가 그대로다.** Jev Boolean에는 설명 칸이 없으므로 criteria를 뺀 Laya 변형과 비교했다. Jev 56/60, Laya english no-criteria 31/60(b=27 / c=2), multilingual no-criteria 25/60(b=34 / c=3)이다. 차이는 true/false 설명의 정보 비대칭에서 오지 않는다.
3. **T3에서는 유의한 차이가 없다.** Jev 28/40 = 0.700 [0.546, 0.819], Laya english 0.750(b=2 / c=4, p=0.69), multilingual 0.625(b=6 / c=3, p=0.51). 이 seed-13 표본은 두 시스템 모두에게 쉬운 쪽이다. Jev 0.700의 CI는 Jev 공개치 0.480을 포함하지 않고, Laya english도 upstream 0.573보다 0.177 높다. 발표치와 비교해 일반화하면 안 된다.
4. **보정 양상은 과제에 따라 반대다.** T1에서 Jev는 과소확신이다(평균 top p 0.733, 정확도 0.867, ECE 0.181). 오답 16개 중 top ≥ 0.90은 score 1개뿐이고 noul 오답 4개는 모두 p(true) 0.39\~0.54였다. T3에서는 과대확신이다. 100% 표시 15/40, 오답 12개 중 7개가 ≥ 90%, 정답 옵션이 0%로 표시된 사례가 7/40(17.5%)이다. 이는 공개치 "정답 라벨 확률 0인 사례 16%"와 비슷하다.

플레이그라운드 경유이며 API가 아니다. 모델 버전은 표기되지 않고(`typesafe-ai/jev` 79/79), 표본이 작다. T1의 Jev는 한 요청에 질문 2\~4개를 함께 평가했고(Multiple questions), Laya는 질문마다 따로 평가했다.

## 1. 실행 개요

| 항목 | 값 |
|---|---|
| 요청 | `POST /api/evaluate` 80회 = Part A 40(성공 39 + HTTP 502 1) + Part B 40(성공 40). 세션 상한 80, 하루 상한 100 |
| 502 처리 | run 1(row 0, 08:49:40)이 `{"code":"UNAVAILABLE","message":"Jev is temporarily unavailable."}`로 실패했다. 즉시 기록하고 60 s 넘게 기다린 뒤(73.7 s) 같은 payload로 1회 재시도했고 run 2가 200으로 성공했다(attempt 2). 이후 5xx·429·제한 문구·captcha는 0건이다 |
| 간격 (Run 클릭 사이) | wall clock 최소 12.1 s, 중앙 15.1 s, 최대 131.7 s. monotonic(resource timing startTime 차) 최소 12.1 s(run 4: 가드가 12 s였던 구간. run 5부터 15 s로 올림), 13.07 s(run 61), 중앙 15.1 s. 79개 간격 모두 10 s 이상이다 |
| 입력 동일성 | 요청 전: 폼 값으로 만든 payload의 sha12가 폼 파일 기대값과 80/80 일치(`window.__jev.ready`). 요청 후: 캡처한 request body가 `jev_cmp.py` payload와 바이트 단위로 80/80 같다(`payload_exact`) |
| 화면 = 응답 | 79/79(DECISION·SCORE 문자열, 막대 %, score 카드의 `x.xx / 4`). 표시 지연 = `latencyMs` half-up 반올림 79/79 |
| row 30 | 다시 보내지 않았다. S1 run 1(payload sha12 `5a9e5492744b`)이 A안 payload와 같음을 `s2_prep.py`에서 확인했고(assert), 분석에는 그 기록을 썼다 |
| T3 옵션 | 6개(`sadness, joy, love, anger, fear, surprise`) 순서가 40행 모두 폼 파일과 같고, 모두 80자 이하다(최대 8자, `s2_prep.py` assert). Question은 ``Which emotion is most strongly expressed in `text`?``, State는 폼 `state_text` |
| 측정 이상 | run 60과 61 사이에 호스트 wall clock이 +1.98 s 스텝했다. resource timing을 `performance.timeOrigin` 기준으로 환산하던 dump가 run 61의 POST 항목을 클릭 이전으로 보고 45 s 대기 후 timeout났다(`raw/r61_T3_row20_timedout_dump1.json`, 공개 저장소에는 포함하지 않음). 요청은 1회만 나갔고 200으로 끝났다. dump와 간격 가드를 `Date.now() − performance.now()` 오프셋과 monotonic 기준으로 고쳤고(`raw/js/patch_clock.js`(공개 저장소에는 포함하지 않음), 요청 없음), run 61을 다시 dump해 기록했다. run 61의 wall 간격 15.05 s는 실제로 13.07 s다 |

## 2. T1 typed-decisions (120 Jev-comparable decisions)

대상: 40 case의 비교 가능 decision 전부(choice 50, noul 60, 5레벨 score 10). 제외 80개(4레벨 score 70, 80자 초과 choice 10)는 Jev에 보내지 않았다(`omitted`에 사유 기록). case당 1회, Multiple questions 모드, 폼 파일의 질문 순서다. workflow별 질문 수는 agent_trace 3, customer_service 2, invoice 3, security 4였고 Single 모드가 필요한 case는 없었다. 채점은 `laya_summary.py`의 `decisions` / `metrics` / `t1_extra`를 그대로 썼다(`jev_cmp.py t1 S1,S2`). gold는 teacher 분포의 argmax다. 이 120개에는 dataset `label` ≠ argmax인 사례와 gold 동점이 없고 Jev argmax 동점도 없어, upstream식(label 기준) 정확도와 값이 같다.

### 2.1 정확도·보정 (같은 120 decisions)

| system | all | choice | noul | score (5 levels, argmax) | soft acc | Brier vs soft | Brier (one-hot) | ECE (15 bins) | score MAE: E[level] vs teacher |
|---|---|---|---|---|---|---|---|---|---|
| Jev (playground) | 104/120 = 0.867 [0.794, 0.916] | 42/50 = 0.840 [0.715, 0.917] | 56/60 = 0.933 [0.841, 0.974] | 6/10 = 0.600 [0.313, 0.832] | 0.590 | 0.077 | 0.237 | 0.181 | 0.389 (Jev `score` field) / 0.390 (from rounded p) |
| Laya english | 46/120 = 0.383 [0.301, 0.473] | 14/50 = 0.280 [0.175, 0.417] | 28/60 = 0.467 [0.346, 0.591] | 4/10 = 0.400 [0.168, 0.687] | 0.361 | 0.333 | 0.724 | 0.205 | 0.584 |
| Laya multilingual | 44/120 = 0.367 [0.286, 0.456] | 16/50 = 0.320 [0.208, 0.458] | 26/60 = 0.433 [0.316, 0.559] | 2/10 = 0.200 [0.057, 0.510] | 0.351 | 0.574 | 0.949 | 0.391 | 0.671 |
| Laya Router (120 모두 english) | 46/120 = 0.383 [0.301, 0.473] | 14/50 = 0.280 [0.175, 0.417] | 28/60 = 0.467 [0.346, 0.591] | 4/10 = 0.400 [0.168, 0.687] | 0.361 | 0.333 | 0.724 | 0.205 | 0.584 |
| 참고: Laya typed-decisions (typed-decisions train으로 파인튜닝, zero-shot 아님) | 104/120 = 0.867 [0.794, 0.916] | 40/50 = 0.800 [0.670, 0.888] | 57/60 = 0.950 [0.863, 0.983] | 7/10 = 0.700 [0.397, 0.892] | 0.519 | 0.059 | 0.343 | 0.279 | 0.255 |
| 문항별 최빈 기준선 | 0.575 | | | | | | | | |

- Laya 수치는 `results/F/jev_cmp/laya_summary.md` §2(120 기준)와 같다. 같은 코드로 다시 계산해 확인했다.
- Jev 확률은 소수 둘째 자리로 반올림된 값이다. soft accuracy와 Brier vs soft는 합으로 정규화한 뒤 계산했다(`t1_extra`). one-hot Brier와 ECE는 반올림값을 그대로 썼다.
- score MAE는 10개 decision의 |E[level] − teacher score|다. Jev `score`(서버가 준 기대값)와 반올림 확률에서 다시 계산한 기대값의 차이는 0.001이다.

### 2.2 Exact McNemar (b = Jev만 정답, c = Laya만 정답)

| pair | subset | n | both right | b | c | both wrong | p |
|---|---|---|---|---|---|---|---|
| Jev vs english | all | 120 | 38 | 66 | 8 | 8 | 0.0000 |
| Jev vs english | choice | 50 | 11 | 31 | 3 | 5 | 0.0000 |
| Jev vs english | noul | 60 | 25 | 31 | 3 | 1 | 0.0000 |
| Jev vs english | score | 10 | 2 | 4 | 2 | 2 | 0.6875 |
| Jev vs multilingual | all | 120 | 38 | 66 | 6 | 10 | 0.0000 |
| Jev vs multilingual | choice | 50 | 15 | 27 | 1 | 7 | 0.0000 |
| Jev vs multilingual | noul | 60 | 23 | 33 | 3 | 1 | 0.0000 |
| Jev vs multilingual | score | 10 | 0 | 6 | 2 | 2 | 0.2891 |
| Jev vs Router | all | 120 | 38 | 66 | 8 | 8 | 0.0000 |
| Jev vs Router | choice / noul / score | 50 / 60 / 10 | english와 같음 | | | | |
| 참고: Jev vs typed-decisions (파인튜닝) | all | 120 | 94 | 10 | 10 | 6 | 1.0000 |
| 참고: Jev vs typed-decisions | choice | 50 | 35 | 7 | 5 | 3 | 0.7744 |
| 참고: Jev vs typed-decisions | noul | 60 | 54 | 2 | 3 | 1 | 1.0000 |
| 참고: Jev vs typed-decisions | score | 10 | 5 | 1 | 2 | 2 | 1.0000 |

0.0000은 p < 0.00005다(english all: b=66, c=8).

### 2.3 noul: 같은 입력(설명 없음) 비교

Jev Boolean은 질문 문장만 받는다. Laya no-criteria 변형(`laya/T1_typed_decisions_40_noulnocrit_{english,multilingual}.json`)이 Jev와 같은 정보를 받은 조건이다. 60개 중 20개(duplicate, credential_compromise)는 원래 T1에도 criteria가 없어 네 조건 모두 입력이 같다.

| system | input | all (60) | T1에 criteria가 있던 40 | criteria가 원래 없던 20 | soft acc | Brier vs soft | predicted true (gold true 23) | b / c vs Jev | McNemar p |
|---|---|---|---|---|---|---|---|---|---|
| Jev (playground) | 질문만 | 56/60 = 0.933 [0.841, 0.974] | 37/40 = 0.925 [0.801, 0.974] | 19/20 = 0.950 [0.764, 0.991] | 0.660 | 0.045 | 23 | - | - |
| Laya english | criteria 포함 | 28/60 = 0.467 [0.346, 0.591] | 23/40 = 0.575 [0.422, 0.715] | 5/20 = 0.250 [0.112, 0.469] | 0.462 | 0.369 | 43 | 31 / 3 | 0.0000 |
| Laya english | criteria 없음 | 31/60 = 0.517 [0.393, 0.638] | 26/40 = 0.650 [0.495, 0.779] | 5/20 = 0.250 [0.112, 0.469] | 0.483 | 0.403 | 32 | 27 / 2 | 0.0000 |
| Laya multilingual | criteria 포함 | 26/60 = 0.433 [0.316, 0.559] | 18/40 = 0.450 [0.307, 0.602] | 8/20 = 0.400 [0.219, 0.613] | 0.407 | 0.723 | 41 | 33 / 3 | 0.0000 |
| Laya multilingual | criteria 없음 | 25/60 = 0.417 [0.301, 0.543] | 17/40 = 0.425 [0.285, 0.578] | 8/20 = 0.400 [0.219, 0.613] | 0.398 | 0.775 | 42 | 34 / 3 | 0.0000 |

Jev는 true를 23번 예측했고 gold true도 23개다. Laya는 true 쪽으로 크게 기운다(41\~43, no-criteria english만 32).

### 2.4 workflow·질문별 (정답 수 / n)

| workflow | question | type | n | Jev | english | multilingual | Router | typed-decisions (참고) |
|---|---|---|---|---|---|---|---|---|
| agent_trace_observability | action | choice | 10 | 8 | 4 | 2 | 4 | 7 |
| | needs_review | noul | 10 | 9 | 7 | 6 | 7 | 9 |
| | outcome | choice | 10 | 8 | 3 | 3 | 3 | 8 |
| | **all** | | 30 | 25 | 14 | 11 | 14 | 24 |
| customer_service | category | choice | 10 | 10 | 4 | 8 | 4 | 8 |
| | needs_human | noul | 10 | 9 | 7 | 4 | 7 | 10 |
| | **all** | | 20 | 19 | 11 | 12 | 11 | 18 |
| invoice_processing | disposition | choice | 10 | 9 | 2 | 2 | 2 | 8 |
| | duplicate | noul | 10 | 10 | 0 | 0 | 0 | 10 |
| | matches_order | noul | 10 | 10 | 2 | 2 | 2 | 9 |
| | **all** | | 30 | 29 | 4 | 4 | 4 | 27 |
| security_incidents | credential_compromise | noul | 10 | 9 | 5 | 8 | 5 | 9 |
| | disposition | choice | 10 | 7 | 1 | 1 | 1 | 9 |
| | severity | score | 10 | 6 | 4 | 2 | 4 | 7 |
| | true_positive | noul | 10 | 9 | 7 | 6 | 7 | 10 |
| | **all** | | 40 | 31 | 17 | 17 | 17 | 35 |

workflow 정확도: Jev 0.833 / 0.950 / 0.967 / 0.775, Laya english 0.467 / 0.550 / 0.133 / 0.425. 가장 큰 차이는 invoice_processing(29/30 vs 4/30)이다. Laya base 체크포인트는 duplicate 0/10, matches_order 2/10에서 거의 전부 틀린다.

### 2.5 score (security_incidents/severity, 5 levels)

| row | gold level | teacher E | Jev p(0..4) (Jev의 항목별 출력은 공개 저장소에서 생략) | Jev `score` | Jev argmax | Jev 표시 레벨 | Laya en E / argmax | Laya ml E / argmax |
|---|---|---|---|---|---|---|---|---|
| 30 | 2 | 1.62 | — | — | — | — | 1.62 / 1 X | 1.02 / 0 X |
| 31 | 3 | 2.73 | — | — | — | — | 1.81 / 2 X | 1.36 / 1 X |
| 32 | 2 | 1.19 | — | — | — | — | 1.79 / 2 | 1.56 / 1 X |
| 33 | 2 | 1.88 | — | — | — | — | 2.11 / 2 | 1.56 / 1 X |
| 34 | 3 | 2.46 | — | — | — | — | 1.47 / 1 X | 1.68 / 1 X |
| 35 | 1 | 1.65 | — | — | — | — | 1.99 / 1 | 1.79 / 1 |
| 36 | 3 | 2.77 | — | — | — | — | 2.05 / 2 X | 1.60 / 1 X |
| 37 | 2 | 2.26 | — | — | — | — | 2.17 / 2 | 1.94 / 2 |
| 38 | 3 | 2.14 | — | — | — | — | 0.90 / 0 X | 1.34 / 1 X |
| 39 | 3 | 2.81 | — | — | — | — | 2.11 / 1 X | 1.98 / 2 X |

- 고정 규칙(argmax 레벨)으로 Jev는 6/10이다. 화면에 표시되는 레벨(E[level]의 최근접)로 보면 7/10이고, 둘이 다른 사례는 1개다.
- MAE는 Jev 0.389, Laya english 0.584, multilingual 0.671, 파인튜닝 0.255다. Jev는 E[level]이 teacher보다 높은 쪽으로 치우쳤다(10개 중 9개가 teacher E보다 큼, 평균 +0.35).

### 2.6 공개치와의 대조 (맥락 전용)

| 지표 | Jev, 이번 120 decisions | Jev 공개치 (BENCHMARKS.md, 제3자, Jev 1.13.0) | 비고 |
|---|---|---|---|
| accuracy | 0.867 [0.794, 0.916] | 0.727 | 공개치는 2,000 decisions·dataset label 기준이고 4레벨 score와 80자 초과 옵션을 포함한다. 같은 부분집합 효과로 Laya english도 0.330(200) → 0.383(120)으로 오른다 |
| soft accuracy | 0.590 | 0.580 | |
| Brier (vs soft) | 0.077 | 0.148 | Jev 확률 2자리 반올림 |
| ECE | 0.181 | 0.144 | 15 bins, 반올림으로 bin이 성기다 |
| score MAE | 0.389 (n=10) | 0.391 | n=10이라 수치 일치는 우연 수준이다 |

## 3. T3 DAIR Emotion (40, Single question / Choice)

### 3.1 정확도·McNemar

| system | correct / n | accuracy [Wilson 95%] | Brier | ECE (15 bins) | mean top p |
|---|---|---|---|---|---|
| Jev (playground, 표시 p, 2자리 반올림) | 28/40 | 0.700 [0.546, 0.819] | 0.537 | 0.278 | 0.901 |
| Laya english | 30/40 | 0.750 [0.598, 0.858] | 0.429 | 0.174 | 0.900 |
| Laya multilingual | 25/40 | 0.625 [0.470, 0.758] | 0.631 | 0.313 | 0.924 |
| Laya Router (40 모두 english) | 30/40 | 0.750 [0.598, 0.858] | 0.429 | 0.174 | 0.900 |

| pair | n | 같은 라벨 | b | c | exact McNemar p |
|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 32 | 2 | 4 | 0.6875 |
| Jev vs Laya multilingual | 40 | 27 | 6 | 3 | 0.5078 |
| Jev vs Laya Router | 40 | 32 | 2 | 4 | 0.6875 |

### 3.2 클래스별 정답 수와 Jev 혼동

| gold | n | Jev | Laya english | Laya multilingual | Laya Router |
|---|---|---|---|---|---|
| sadness | 7 | 7 | 6 | 6 | 6 |
| joy | 7 | 5 | 7 | 5 | 7 |
| love | 7 | 3 | 3 | 4 | 3 |
| anger | 7 | 5 | 6 | 4 | 6 |
| fear | 6 | 5 | 4 | 3 | 4 |
| surprise | 6 | 3 | 4 | 3 | 4 |

| gold \ Jev | sadness | joy | love | anger | fear | surprise |
|---|---|---|---|---|---|---|
| sadness | 7 | 0 | 0 | 0 | 0 | 0 |
| joy | 1 | 5 | 1 | 0 | 0 | 0 |
| love | 0 | 3 | 3 | 0 | 1 | 0 |
| anger | 1 | 0 | 0 | 5 | 1 | 0 |
| fear | 1 | 0 | 0 | 0 | 5 | 0 |
| surprise | 1 | 0 | 1 | 0 | 1 | 3 |

Jev 오답 12개 중 4개가 sadness로 갔고(fear·joy·surprise·anger 각 1, top p 97\~100%), love → joy가 3개다. 세 시스템이 모두 틀린 행은 7개이고, 그중 다수에서 세 시스템이 같은 라벨(joy 또는 sadness)을 골랐다.

### 3.3 표본 쉬움 caveat

| 시스템 | 우리 seed-13 40행 | 기준 | 차이 |
|---|---|---|---|
| Jev | 0.700 [0.546, 0.819] | 공개치 0.480 (Jev 자체 100-item 표본, 제3자) | +0.220, CI 밖 |
| Laya english | 0.750 [0.598, 0.858] | upstream 0.573 (test 첫 600행, 우리 파이프라인으로 재현 0.5733, `laya_summary.md` §6) | +0.177 |
| Laya multilingual | 0.625 | upstream 0.513 / 0.530 | +0.095\~0.112 |

이 표본은 두 시스템 모두에게 쉽다. 짝 비교(McNemar)에는 쓸 수 있지만 절대 정확도를 발표치와 비교해 일반화하면 안 된다. 같은 seed로 뽑은 표본에서 Jev와 Laya english가 비슷한 폭으로 오른 것은 둘이 같은 쉬운 항목을 맞힌다는 뜻이다(같은 라벨 32/40).

### 3.4 확신도

| 시스템 | top = 100% | 평균 top (정답 / 오답) | 오답 중 top ≥ 0.90 | 정답 옵션 0% 표시 | provider confidence 평균 (정답 / 오답) |
|---|---|---|---|---|---|
| Jev | 15/40 (38%) | 0.900 (0.918 / 0.861) | 7/12 | 7/40 = 17.5% (공개치 16%) | 0.878 (0.899 / 0.830) |
| Laya english | - | 0.900 (0.923 / 0.834) | 4/10 | - | - |
| Laya multilingual | - | 0.924 (0.951 / 0.880) | 9/15 | - | - |

Jev 오답 중 100% 표시가 3개다(joy → sadness, surprise → sadness, love → joy). 0% 칸은 153/240이다.

## 4. 보정과 확신도: 과제별 비교

| 과제 (Jev) | n | 정확도 | 평균 top p | 오답 중 top ≥ 0.90 | ECE | 해석 |
|---|---|---|---|---|---|---|
| T1 choice (multi) | 50 | 0.840 | 0.735 | 0/8 | | 오답의 top p 0.42\~0.76 |
| T1 noul (multi) | 60 | 0.933 | 0.732 | 0/4 | | p(true)가 ≥ 0.80 4개, ≤ 0.20 19개뿐이고 오답 4개는 0.39\~0.54 |
| T1 score (multi) | 10 | 0.600 | 0.729 | 1/4 | | — |
| T1 전체 | 120 | 0.867 | 0.733 | 1/16 | 0.181 | 과소확신 |
| T3 (single) | 40 | 0.700 | 0.901 | 7/12 | 0.278 | 과대확신 |
| 참고: S1 T2 AG News (single) | 40 | 0.875 | 0.977 | 4/5 (≥ 93%) | 0.118 | 과대확신 (`S1_summary.md`) |

T1에서는 Jev의 top p가 낮을수록 실제로 틀릴 가능성이 높다(정답 평균 0.758, 오답 평균 0.569). 그래서 임계값(예: 0.60 미만은 보류)으로 오답을 거를 여지가 있다. T2·T3처럼 단일 choice 과제에서는 오답 대부분이 90% 이상이라 같은 방법이 통하지 않는다. provider confidence(T1에서는 choice·score에만 온다)도 같은 방향이다(T1 정답 0.711 / 오답 0.454).

## 5. 지연·토큰

| 구분 | runs | 표시 "server + network" ms median / min / max | 브라우저 POST ms median / min / max | 클릭 → 완료 ms median | 입력 토큰 median (min\~max) | 출력 토큰 median (min\~max) |
|---|---|---|---|---|---|---|
| Part A T1 (S2, 2\~4문항/요청) | 39 | 226 / 164 / 355 | 481 / 409 / 847 | 483 | 760 (640\~953) | 141 (138\~214) |
| T1 2문항 (customer_service) | 10 | 221 / 184 / 262 | 471.5 / 428 / 680 | | 741.5 (640\~953) | 138 (138\~140) |
| T1 3문항 (agent_trace, invoice) | 20 | 225.5 / 164 / 355 | 478.5 / 409 / 758 | | 731.5 (679\~799) | 172.5 (141\~214) |
| T1 4문항 (security, S1 row 30 포함) | 10 | 239 / 211 / 299 | 483.5 / 455 / 847 | | 863.5 (803\~903) | 162 (161\~166) |
| Part B T3 (single) | 40 | 241 / 170 / 713 | 469 / 406 / 951 | 471.5 | 387.5 (372\~422) | 61 (61\~62) |
| S2 전체 | 79 | 229 / 164 / 713 | 476 / 406 / 951 | 479 | 422 (372\~953) | 62 (61\~214) |

- 4행(문항 수별)은 `jev_cmp.py t1` 출력으로 S1 row 30을 포함한다(40 runs). 첫 행은 S2의 39 runs다.
- T1 multi 요청은 질문 2\~4개를 한 번에 돌려준다. 표시 지연을 질문 수로 나누면 중앙값이 2문항 111 ms, 3문항 75 ms, 4문항 60 ms다. 요청당 지연은 문항 수에 거의 비례하지 않는다(221 → 239 ms).
- 브라우저 POST − latencyMs의 중앙값은 235.6 ms다(S1 232, S1b 234와 같은 수준).
- 토큰 합계는 입력 45,616, 출력 8,806이다(A 30,023 / 6,352, B 15,593 / 2,454).
- Laya 로컬 지연 참조: P2 laya-serve 왕복 20.1 ms(`results/poc/P2_20261003.md:67`), D1 english CPU 1문항 86.6 ms(`results/D/D_summary_20261003.md:34`). 하드웨어와 경로가 달라 모델 속도 비교가 아니다.

## 6. 관찰과 한계

**핵심 관찰 3개**
1. **T1에서 Jev zero-shot은 Laya 파인튜닝 체크포인트 수준이고, Laya base(english·multilingual·Router)는 최빈 기준선보다 낮다.** 차이는 noul criteria 비대칭으로 설명되지 않는다(no-criteria 변형에서도 b=27\~34 / c=2\~3). "Laya is a fast base to specialise, not a zero-shot decision engine"(upstream README "Honest limits")이라는 자기 평가와 일치한다.
2. **T3에서는 Jev와 Laya english가 구분되지 않는다**(0.700 vs 0.750, b=2 / c=4). 둘 다 이 표본에서 발표치보다 0.18\~0.22 높고, 같은 7개 행을 함께 틀린다. love/joy, surprise 경계가 공통 약점이다.
3. **Jev 확률의 의미가 과제 형식에 따라 다르다.** Multiple questions의 T1에서는 과소확신이고 오답이 저확신이다. 단일 choice(T2·T3)에서는 오답 다수가 90\~100%로 표시된다. 임계값 기반 보류 정책을 Jev 확률 위에 세울 때 과제별 검증이 필요하다.

**한계**
- 플레이그라운드 경유이며 API가 아니다. 모델 버전이 표기되지 않고 프롬프트 래핑을 알 수 없다. n이 작다(T1 120, T3 40).
- T1의 Jev는 한 case의 질문 2\~4개를 한 요청에서 함께 평가했다("evaluated together against the same State"). Laya는 질문마다 독립 row로 평가했다. 함께 평가하는 것이 정확도에 미치는 영향은 이 설계로 분리할 수 없다.
- T1 gold는 teacher 분포의 argmax다. teacher 모델과 Jev의 관계는 확인하지 못했다(확인 필요). 공개 Jev 0.727이 teacher 상한 0.735(`docs/01_laya_analysis.md` §(b))에 가까우므로 teacher와의 정렬 효과를 배제할 수 없다.
- 4레벨 score 70개와 80자 초과 choice 10개를 제외해 공개치(2,000 decisions)와 문항 구성이 다르다. score MAE는 n=10이다.
- Jev 확률은 소수 둘째 자리로 반올림된다(Brier·ECE 하한 오차 약 ±0.005). T3는 100%·0% 표시가 많아 ECE bin이 성기다.
- 측정 이상 1건(wall clock 스텝): 요청 수와 결과에는 영향이 없다. run 61의 간격을 wall 기준으로 기록하면 15.05 s, monotonic 기준이면 13.07 s다.

## 7. 파일

| 파일 | 내용 |
|---|---|
| `results/F/jev_cmp/sessions/S2_20261007/S2_requests.jsonl`(공개 저장소에는 포함하지 않음) | 80줄(run 1 = 502, run 2 = row 0 재시도). decision별 `pred`·`probs`·`p_true`·`score`·`shown`(표시 문자열)·`shown_pct`, run별 `latency_ms_response`·`displayed_ms`·`fetch_dur_ms`·`usage`·`confidence`·`model_id_details` |
| `results/F/jev_cmp/jev_runs_all.jsonl`(공개 저장소에는 포함하지 않음) | master, 151줄(S1 41 + S1b 30 + S2 80) |
| `results/F/jev_cmp/sessions/S2_20261007/raw/rNN_<T>_rowRR.json`(공개 저장소에는 포함하지 않음) | 요청별 dump 80개(request body, 응답 text, DOM text·HTML, resource timing, status log) + `r61_T3_row20_timedout_dump1.json` |
| `raw/run_plan.json`, `raw/js/iNN_*.js`, `raw/js/instrument.js`, `raw/js/patch_clock.js`, `raw/js/dry_i40_T3_row00.js`(`raw/js/`는 공개 저장소에는 포함하지 않음) | 항목 계획(79), 항목별 Playwright 입력 스크립트(폼 파일에서 생성), 계측 코드, 시계 패치, Part B 무클릭 dry run |
| `raw/evaluate_timing_all.json`, `raw/network_requests.txt`, `raw/console.log`, `raw/mcp/`(네 항목 모두 공개 저장소에는 포함하지 않음) | `/api/evaluate` resource timing 80건(monotonic), 네트워크 목록(POST 80: 200 79·502 1, GET 39), 콘솔(MCP 로그 기준 오류 1 = 502, 나머지 CSS preload 경고), MCP snapshot 3개와 콘솔 로그 사본 |
| `results/F/jev_cmp/sessions/S2_20261007/shots/`(공개 저장소에는 포함하지 않음) | `S2_A_item01_run02_T1_row00.png`, `S2_A_item20_run21_T1_row19.png`, `S2_A_item39_run40_T1_row39.png`, `S2_B_item01_run41_T3_row00.png`, `S2_B_item20_run60_T3_row19.png`, `S2_B_item40_run80_T3_row39.png`(View details 열림) |
| `results/F/jev_cmp/sessions/S2_20261007/s2_prep.py`, `s2_record.py` | 계획·입력 스크립트 생성, 기록 래퍼(중단 문구 검사) |
| `results/F/jev_cmp/jev_cmp.py` | `t1` subcommand 추가, `record` 소폭 확장(아래 run card) |

[English](S2_summary.md) | **한국어**
