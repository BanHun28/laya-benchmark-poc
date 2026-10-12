# S3 요약: T4 Banking77-10 (key-only) 40 + T5 BoolQ 40 (2026-10-07)

**판정.**
1. **T4 Banking77-10에서 Jev가 Laya 세 러너를 유의하게 앞선다.** Jev 37/40 = **0.925** [0.801, 0.974]. Laya english·Router는 29/40 = 0.725, multilingual은 30/40 = 0.750이다. Jev vs english는 b=9 / c=1(exact McNemar p=0.0215), vs multilingual은 b=8 / c=1(p=0.0391)이다. Jev 오답 3개 중 2개는 Laya 세 러너도 같은 라벨로 틀렸다. Jev만 틀린 행은 1개다(Jev의 항목별 출력은 공개 저장소에서 생략).
2. **T5 BoolQ에서도 Jev가 앞서고, 차이는 임계값이 아니라 순위 품질에서 온다.** Jev 37/40 = **0.925**, Laya english·Router 0.725, multilingual 0.600(McNemar b/c 9/1 p=0.0215, 15/2 p=0.0023). p(true)의 AUROC는 Jev 0.988 [0.955, 1.000], english 0.810 [0.662, 0.942], multilingual 0.682 [0.496, 0.838]이다. paired bootstrap 차이 CI는 두 쌍 모두 0을 포함하지 않는다(+0.177 [+0.043, +0.326], +0.305 [+0.152, +0.486]). 예측 양성률은 Jev 21, english 19, multilingual 18로 셋 다 gold 20/40에 가깝다. 이 40행에서 고른 최적 임계값으로도 Laya english는 0.775라, NSMC E6처럼 임계값을 옮겨 회복할 수 있는 구조가 아니다(기술통계, 주장용 아님).
3. **Jev 확률의 형태가 결정 타입마다 다르다.** 단일 choice(T4)는 100% 표시가 31/40이고 오답 하나가 0.90 이상이다. Boolean(T5)은 100% 표시가 0/40(p(true) 0.02\~0.99)이고 오답 3개가 모두 top < 0.80이다. top ≥ 0.80만 남기면 34/40을 덮고 오류가 0이다(같은 40행 기술통계). S2의 T1 noul(과소확신)과 T3 choice(과대확신)에서 본 패턴과 같은 방향이다.
4. **운영:** 요청 80회가 모두 HTTP 200이었다. 5xx, 4xx(429 포함), 제한 문구, captcha는 0건이고 재시도도 없었다. 간격은 monotonic 기준 최소 15.02 s, 중앙 15.13 s다. 오늘 누적은 S2 80 + S3 80 = 160회이고, 101번째 요청(S3 run 21, 13:41:37) 이후에도 제한 신호가 없었다.

플레이그라운드 경유이며 API가 아니다. 모델 버전은 표기되지 않고(`typesafe-ai/jev` 80/80), n=40이다. Jev 확률은 소수 둘째 자리 반올림이다. T5(BoolQ)는 upstream 표기상 Laya 학습 믹스에 포함되고, Jev의 학습 데이터는 알 수 없다.

## 1. 실행 개요

| 항목 | 값 |
|---|---|
| 요청 | `POST /api/evaluate` 80회 = Part A(T4) 40 + Part B(T5) 40, 모두 HTTP 200. 세션 상한 100(계획 80), 하루 상한은 프로젝트 책임자 결정(2026-10-07)으로 해제 |
| 중단 조건 | 5xx 0, 4xx 0(429 0), 제한 문구 0, captcha 0, 오류 화면 0. 매 run마다 결과 패널·status·title·`[role=alert]`·body 텍스트를 제한 문구 정규식으로 검사했고 captcha iframe 유무도 확인했다(`s3_record.py`, dump `page`) |
| 간격 (Run 클릭 사이) | 가드 15 s, 처음부터 monotonic 기준(`performance.timeOrigin + performance.now()`, resource timing과 같은 축). 79개 간격: 최소 15.024 s, 중앙 15.125 s, 최대 28.862 s(run 4: 기록 래퍼를 고친 시간). resource timing `startTime` 차로 다시 재도 같다(15.024 / 15.125 / 28.861). wall − mono 오프셋은 0 → 15 ms로 서서히 늘었고 스텝은 없었다 |
| 입력 동일성 | 요청 전: 폼 값으로 만든 payload sha12가 폼 파일 기대값과 80/80 일치(`window.__jev.ready`). 요청 후: 캡처한 request body가 `jev_cmp.py` payload와 바이트 단위로 80/80 같다(`payload_exact`). 무클릭 dry run 2회(item 1, 41) |
| 입력 내용 | T4: Single / Choice. 옵션 10개(key-only, 최대 48자)를 폼 파일 순서대로 넣었다. 행마다 옵션 순서가 Laya criteria key 순서와 같다(`s3_prep.py` assert). T5: Single / Boolean. 질문 문장만 넣었다(Laya noul에도 criteria가 없다). State는 두 과제 모두 Laya가 읽는 JSON 문자열(`state_text`)이다 |
| 화면 = 응답 | 80/80(DECISION, 막대 %). 표시 지연 = `latencyMs` half-up 반올림 80/80. Single Boolean 화면("DECISION / No / More probable answer, derived from Jev’s P(true). / Yes 5% / No 95%")도 기존 파서로 맞았다 |
| Model ID / 응답 메타 | `model`과 View details 모두 `typesafe-ai/jev` 80/80. `rounding` {2, 2}, `warnings` [] 80/80. provider `confidence`는 T4 40/40에 있고(top p와 같은 값 34/40), T5 Boolean에는 없다(0/40) |

## 2. T4 Banking77-10 (key-only, 40행, 정답 라벨 40종)

### 2.1 정확도·보정 (같은 40행, 같은 옵션 문자열과 순서)

| system | correct / n | accuracy [Wilson 95%] | Brier | ECE (15 bins) | mean top p |
|---|---|---|---|---|---|
| Jev (playground, 표시 p, 2자리 반올림) | 37/40 | 0.925 [0.801, 0.974] | 0.114 | 0.069 | 0.973 |
| Laya english | 29/40 | 0.725 [0.572, 0.839] | 0.349 | 0.150 | 0.860 |
| Laya multilingual | 30/40 | 0.750 [0.598, 0.858] | 0.478 | 0.262 | 0.832 |
| Laya Router (40 모두 english) | 29/40 | 0.725 [0.572, 0.839] | 0.349 | 0.150 | 0.860 |

Brier는 Σ(p − onehot)²를 행마다 그 행의 옵션 10개로 계산했다. Laya 값은 `laya_summary.md` §1(0.349 / 0.478, ECE 0.150 / 0.262)과 같다.

### 2.2 일치와 exact McNemar (b = Jev만 정답, c = Laya만 정답)

| pair | n | 같은 라벨 | b | c | p |
|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 30 | 9 | 1 | 0.0215 |
| Jev vs Laya multilingual | 40 | 31 | 8 | 1 | 0.0391 |
| Jev vs Laya Router | 40 | 30 | 9 | 1 | 0.0215 |

### 2.3 확신도

| system | top = 100% | 평균 top (정답 / 오답) | 오답 중 top ≥ 0.90 | 정답 옵션 0% 표시 | provider confidence (정답 / 오답) |
|---|---|---|---|---|---|
| Jev | 31/40 (78%) | 0.973 (0.984 / 0.847) | 1/3 | 0/40 | 0.970 (0.982 / 0.827) |
| Laya english | - | 0.860 (0.961 / 0.596) | 3/11 | - | - |
| Laya multilingual | - | 0.832 (0.828 / 0.846) | 6/10 | - | - |

Jev는 0% 칸이 348/400이고 모든 run에 0% 옵션이 있다. 그러나 정답 옵션이 0%로 표시된 행은 없다(S2 T3는 7/40). 오답 3개의 p(gold)는 0.01\~0.28이다. multilingual은 오답의 평균 확신(0.846)이 정답(0.828)보다 높다.

### 2.4 오답과 혼동

| row | message (요약) | gold | Jev (top) | Laya english | Laya multilingual |
|---|---|---|---|---|---|
| — | — | — | — | — | — |
| — | — | — | — | — | — |
| — | — | — | — | — | — |

- 네 시스템이 모두 같은 라벨로 틀린 행은 2개다. 두 행 모두 Banking77 라벨 경계가 애매한 사례다.
- Laya english 오답 11개 중 9개는 Jev가 맞혔다. 가장 잦은 오답 라벨은 lost or stolen card(2회)다. multilingual 오답 10개 중 8개도 Jev가 맞혔다. Laya 두 체크포인트는 Jev가 맞힌 행 2개에서도 같은 라벨로 틀렸다.

### 2.5 맥락 (비교 불가 수치, 참고용)

| 수치 | 값 | 이번 측정과의 관계 |
|---|---|---|
| Laya T4 v0(`key: key spaced` 렌더링, 같은 40행·옵션 집합·순서) | english 0.825 / multilingual 0.575 (`laya_summary.md` §4b) | Jev에는 v0 렌더링을 보내지 않았다. 렌더링만 바꿔도 Laya multilingual이 +0.175 움직였으므로(p=0.016) 같은 입력 비교는 key-only뿐이다 |
| Jev Banking77 공개치 | 0.870 (72 라벨, 제3자, BENCHMARKS.md) | 옵션 수가 다르다(10 vs 72). 이번 0.925와 직접 비교하지 않는다 |
| Laya Banking77 upstream | 0.425 (77 옵션, BENCHMARKS.md:162) | 옵션 수가 달라 비교 불가 |
| 학습 믹스 | MANIFEST `in_training_mix: unknown`(upstream은 held out으로 표기) | |

## 3. T5 BoolQ (40행, gold true 20 / false 20)

### 3.1 정확도·양성률·순위 품질

| system | correct / n | accuracy [Wilson 95%] | 예측 true | Brier | ECE (15 bins) | mean top p | AUROC p(true) [bootstrap 95%] | 같은 40행 최적 임계값 정확도 (기술통계) |
|---|---|---|---|---|---|---|---|---|
| Jev (playground, 표시 p, 2자리) | 37/40 | 0.925 [0.801, 0.974] | 21 | 0.098 | 0.103 | 0.913 | 0.988 [0.955, 1.000] | 38/40 = 0.950 (t 0.63\~0.85) |
| Laya english | 29/40 | 0.725 [0.572, 0.839] | 19 | 0.393 | 0.190 | 0.897 | 0.810 [0.662, 0.942] | 31/40 = 0.775 (t 0.41\~0.90) |
| Laya multilingual | 24/40 | 0.600 [0.446, 0.737] | 18 | 0.615 | 0.294 | 0.870 | 0.682 [0.496, 0.838] | 27/40 = 0.675 (t 0.94) |
| Laya Router (40 모두 english) | 29/40 | 0.725 [0.572, 0.839] | 19 | 0.393 | 0.190 | 0.897 | 0.810 [0.662, 0.942] | 31/40 = 0.775 |

- 판정 규칙은 p(true) ≥ 0.5(laya-evals 규칙)다. Jev가 정확히 0.5("Equally likely")를 낸 행은 없다.
- Brier는 `laya_summary.py`와 같이 {false, true} 두 칸의 Σ(p − onehot)²다(= 2(p − y)²). 한 칸 (p − y)² 기준이면 값이 절반이다. Laya 값은 `laya_summary.md` §1(0.393 / 0.615, ECE 0.190 / 0.294)과 같다.
- AUROC는 Mann-Whitney 방식이고 동점은 0.5로 센다(`scripts/calibrate_ko.py` auroc와 같은 정의). CI는 항목 재표본 2,000회 percentile이다(seed 13). Jev p(true)는 2자리 반올림이라 서로 다른 값이 21개뿐이고, 동점이 AUROC를 약간 낮출 수 있다.
- 최적 임계값 열은 같은 40행에서 고른 값이라 낙관적 편향이 있다. 결론에는 쓰지 않는다.

### 3.2 일치, exact McNemar, AUROC 차이

| pair | n | 같은 예측 | b | c | McNemar p | AUROC Jev − Laya [paired bootstrap 95%] |
|---|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 30 | 9 | 1 | 0.0215 | +0.177 [+0.043, +0.326] |
| Jev vs Laya multilingual | 40 | 23 | 15 | 2 | 0.0023 | +0.305 [+0.152, +0.486] |
| Jev vs Laya Router | 40 | 30 | 9 | 1 | 0.0215 | +0.177 [+0.043, +0.326] |

### 3.3 확신도와 보류 임계값

| system | 100% 표시 (p ∈ {0, 1}) | 평균 top (정답 / 오답) | 오답 중 top ≥ 0.90 | 정답 쪽 0% 표시 | 서로 다른 p(true) 값 |
|---|---|---|---|---|---|
| Jev | 0/40 | 0.931 / 0.697 | 0/3 | 0 | 21 |
| Laya english | 2/40 | 0.929 / 0.815 | 4/11 | 0 | 39 |
| Laya multilingual | 0/40 | 0.891 / 0.839 | 7/16 | 0 | 40 |

같은 40행에서 Jev top p로 보류하면 다음과 같다(기술통계, 임계값 검증 아님).

| 남기는 기준 | 남는 행 | 남은 행의 오답 | 보류된 정답 |
|---|---|---|---|
| top ≥ 0.80 | 34/40 | 0 | 3 |
| top ≥ 0.90 | 31/40 | 0 | 6 |
| top ≥ 0.95 | 24/40 | 0 | 13 |

### 3.4 오답

| row | question | gold | Jev p(true) | Laya english | Laya multilingual |
|---|---|---|---|---|---|
| — | — | — | — | — | — |
| — | — | — | — | — | — |
| — | — | — | — | — | — |

- 세 시스템이 모두 틀린 행은 1개다. 지문 내용상 그 행의 gold가 애매하다.
- Laya english 오답 11개 중 9개를 Jev가 맞혔다. english 오답 중 4개는 top 0.90 이상이다(row 0 p(true) 0.99, row 17 0.98, row 27 0.96, row 38 0.04).

### 3.5 맥락

| 수치 | 값 | 비고 |
|---|---|---|
| Laya BoolQ upstream | english 0.830 / multilingual 0.787 (README.md:1353, N=600, in training mix) | 이번 english 0.725의 CI [0.572, 0.839]는 0.830을 포함한다. multilingual 0.600의 CI [0.446, 0.737]는 0.787을 포함하지 않는다 |
| Jev BoolQ 공개치 | 없음 | |
| 학습 믹스 | Laya: in training(upstream 표기). Jev: 알 수 없음 | Laya에 유리할 수 있는 과제인데도 Laya가 낮다 |

## 4. 보정과 확신도: 과제 형식별 (Jev, S1\~S3)

| 과제 (Jev) | 형식 | n | 정확도 | 평균 top p | 100% 표시 | 오답 중 top ≥ 0.90 | 정답 0% 표시 | ECE |
|---|---|---|---|---|---|---|---|---|
| S1 T2 AG News | single choice 4 | 40 | 0.875 | 0.977 | 29/40 | 4/5 (≥ 93%) | 1/40 | 0.118 |
| S2 T3 Emotion | single choice 6 | 40 | 0.700 | 0.901 | 15/40 | 7/12 | 7/40 | 0.278 |
| **S3 T4 Banking77-10** | single choice 10 | 40 | 0.925 | 0.973 | 31/40 | 1/3 | 0/40 | 0.069 |
| S1·S2 T1 choice | multi choice | 50 | 0.840 | 0.735 | 8/50 | 0/8 | 0/50 | |
| S1·S2 T1 noul | multi Boolean | 60 | 0.933 | 0.732 | 0/60 | 0/4 | 0/60 | |
| **S3 T5 BoolQ** | single Boolean | 40 | 0.925 | 0.913 | 0/40 | 0/3 | 0/40 | 0.103 |

- Boolean은 모드와 상관없이(T1 multi, T5 single) 100% 표시가 한 번도 없었고(0/60, 0/40), 오답이 모두 top 0.90 미만이었다(4/4, 3/3). 단일 choice는 100% 표시가 흔하고(38\~78%) 오답 일부가 90% 이상이다. T4에서 오답 3개 중 2개는 0.90 미만이었지만 하나는 걸러지지 않는다.
- T4의 ECE(0.069)는 낮다. 다만 평균 top 0.973이 정확도 0.925보다 높아 약한 과대확신이다. T5는 평균 top 0.913, 정확도 0.925로 차이가 작다. 그런데도 ECE가 0.103인 것은 15개 bin에 40행이 흩어진 영향이다.

## 5. 지연·토큰

| 구분 | runs | 표시 "server + network" ms median / min / max | 브라우저 POST ms median / min / max | 클릭 → 완료 ms median | POST − latencyMs median | 입력 토큰 median (min\~max) | 출력 토큰 median (min\~max) |
|---|---|---|---|---|---|---|---|
| Part A T4 (choice 10) | 40 | 227.5 / 181 / 417 | 470.5 / 406 / 679 | 472.5 | 237.7 | 476 (455\~546) | 116.5 (107\~125) |
| Part B T5 (Boolean) | 40 | 200.5 / 172 / 363 | 442 / 373 / 691 | 443 | 232.2 | 402.5 (330\~545) | 20 (20\~20) |
| S3 전체 | 80 | 215.5 / 172 / 417 | 454.5 / 373 / 691 | | 233.8 | | |

- 토큰 합계는 입력 35,756, 출력 5,460이다(A 19,138 / 4,660, B 16,618 / 800).
- T4 출력 토큰은 행마다 옵션 문자열 길이와 함께 움직인다(Pearson r = 0.77, 옵션 합계 172\~256자). 옵션이 고정인 T3(6옵션)는 61\~62, Boolean은 20으로 일정했다. 출력이 옵션별 확률을 나열하는 구조일 가능성이 있다(추정, 확인 필요). T5 입력 토큰은 state 길이와 r = 0.96이다.
- 표시 지연은 S1 T2 234 ms, S2 T3 241 ms, S2 T1 226 ms와 같은 수준이다. Boolean이 choice 10보다 27 ms 빠르고(중앙값) 출력 토큰도 적다. POST − latencyMs(약 234 ms)는 S1 232, S2 235.6과 같다.
- Laya 로컬 지연 참조: P2 laya-serve 왕복 20.1 ms(`results/poc/P2_20261003.md:67`), D1 english CPU 1문항 86.6 ms(`results/D/D_summary_20261003.md:34`). 하드웨어와 경로가 달라 모델 속도 비교가 아니다.

## 6. 관찰과 한계

**핵심 관찰 3개**
1. **같은 입력 짝 비교에서 Jev가 두 과제 모두 Laya base를 유의하게 앞선다.** T4(held out/unknown)는 b/c 9/1과 8/1, T5(Laya 학습 믹스 포함)는 9/1과 15/2다. S1 T2(Laya 우세 방향, 유의하지 않음)와 S2 T3(구분 안 됨)와 달리, 10옵션 intent와 지문 기반 yes/no에서 차이가 0.2 이상 벌어졌다. T4에서 Jev가 틀린 3행 중 2행은 네 시스템이 모두 같은 라벨로 틀린 라벨 경계 사례이고, Jev만 틀린 행은 1개다.
2. **T5의 격차는 판별력에서 온다.** 세 시스템의 예측 양성률(21 / 19 / 18 vs gold 20)은 모두 균형이다. 그런데 AUROC가 0.988 vs 0.810 / 0.682이고 paired bootstrap CI가 0을 제외한다. 같은 40행에서 최적 임계값을 골라도 Laya english는 0.775에 그친다. Laya english는 오답 11개 중 4개를 0.90 이상으로 낸다. "임계값·보정으로 회복"(E6 NSMC 시나리오)이 아니라 순위 자체의 차이다.
3. **보류 정책은 결정 타입별로 따로 검증해야 한다.** Jev Boolean은 100% 표시가 없고 오답이 저확신이라(top 0.52\~0.79), top ≥ 0.80 보류가 같은 40행에서 오답 3개를 모두 걸렀다(정답 3개 보류). 단일 choice(T4)는 100% 표시가 78%이고, 0.90 이상 오답이 남는다. S2 T1(multi) 과소확신, T3(single choice) 과대확신과 같은 방향이다.

**한계**
- 플레이그라운드 경유이며 API가 아니다. 모델 버전이 표기되지 않고 프롬프트 래핑을 알 수 없다. n=40이라 95% CI 폭이 약 ±0.15다.
- Jev 확률은 2자리 반올림이다. 하한 오차는 Brier ±0.005 수준이고, Boolean p(true)는 서로 다른 값이 21개뿐이라 AUROC 동점이 생긴다. AUROC와 차이의 bootstrap CI는 n=40 재표본이라 거칠다.
- 최적 임계값과 보류 표는 같은 40행에서 계산한 기술통계다. 임계값을 고정하려면 별도 표본으로 검증해야 한다.
- T5 BoolQ는 Laya 학습 믹스 포함이고 Jev 학습 데이터는 알 수 없다. 이 40행이 쉬운 표본인지는 Jev 공개치가 없어 점검하지 못했다. Laya english 0.725는 upstream 0.830의 CI 안이다.
- T4 key-only 렌더링은 두 시스템에 같다. Laya는 렌더링에 민감하다(v0 대비 english −0.100, multilingual +0.175). Jev가 `key: description`에서 어떻게 움직이는지는 측정하지 않았다(계획 §7.2 S5-b 후보).

## 7. 파일

| 파일 | 내용 |
|---|---|
| `results/F/jev_cmp/sessions/S3_20261007/S3_requests.jsonl`(공개 저장소에는 포함하지 않음) | 80줄(run = item, 재시도 없음). decision별 `pred`·`probs`·`p_true`·`top_p`·`shown`·`shown_pct`, run별 `latency_ms_response`·`displayed_ms`·`fetch_dur_ms`·`click_to_complete_ms`·`usage`·`confidence`·`model_id_details`. `click_epoch_ms`는 monotonic 축(`performance.timeOrigin + performance.now()`)이다 |
| `results/F/jev_cmp/jev_runs_all.jsonl`(공개 저장소에는 포함하지 않음) | master, 231줄(S1 41 + S1b 30 + S2 80 + S3 80). 앞 151줄은 S3 전 사본과 바이트 동일 |
| `raw/rNN_<T>_rowRR.json`(공개 저장소에는 포함하지 않음) | 요청별 dump 80개(request body, 응답 text, DOM text·HTML, resource timing, status log, `clicks_wall`, `wall_minus_mono_ms`, 페이지 제한 문구 검사 결과) |
| `raw/run_plan.json`, `raw/js/`(공개 저장소에는 포함하지 않음) | 항목 계획 80, 계측 `instrument.js`(monotonic), 항목별 입력 스크립트 `i01~i80`, 무클릭 dry run `dry_i01_T4_row00.js`·`dry_i41_T5_row00.js` |
| `raw/evaluate_timing_all.json`, `raw/network_requests.txt`, `raw/network_requests_all.txt`, `raw/console.log`, `raw/mcp/`(다섯 항목 모두 공개 저장소에는 포함하지 않음) | `/api/evaluate` resource timing 80건과 클릭 시각(monotonic·wall), 네트워크 목록(POST 80 모두 200, GET 70 = 문서 1 + 정적 34 + RSC prefetch 35), 콘솔(경고 193 = CSS preload, 오류 0), MCP snapshot 2개와 MCP 콘솔 로그 |
| `shots/`(공개 저장소에는 포함하지 않음) | `S3_A_item01_run01_T4_row00.png`, `S3_A_item20_run20_T4_row19.png`, `S3_A_item40_run40_T4_row39.png`, `S3_B_item41_run41_T5_row00.png`, `S3_B_item60_run60_T5_row19.png`, `S3_B_item80_run80_T5_row39.png`(View details 열림, full page) |
| `s3_prep.py`, `s3_record.py` | 계획·입력 스크립트 생성(폼 파일 ↔ Laya JSONL 동일성 assert), 기록 래퍼(중단 조건 분류, stale dump 거부) |
| `results/F/jev_cmp/jev_cmp.py` | `analyze` 확장: 행별 옵션 집합 Brier, 혼동 목록, Boolean 분기(AUROC·bootstrap·임계값). 상세는 run card |
| 재현 | `.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S3 T4_banking77_10opt_40`, `… analyze S3 T5_boolq_40` |

[English](S3_summary.md) | **한국어**
