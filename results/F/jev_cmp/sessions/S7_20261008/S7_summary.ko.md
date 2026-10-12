# S7 요약: T9 Enron spam 40 + T10 고객지원 티켓 큐 40 (2026-10-08)

**판정.**
1. **T9 Enron spam은 네 시스템 모두 천장이라 구분되지 않는다.** Jev, Laya english, multilingual, Router가 모두 40/40 = 1.000 [0.912, 1.000]이다. 예측 양성은 모두 20/40(gold 20)이고, exact McNemar는 세 쌍 모두 b/c 0/0, p=1.0이다. p(true)의 AUROC도 네 시스템 모두 1.000이다(완전 분리라 bootstrap CI가 [1.000, 1.000]으로 퇴화). 보정만 다르다. Brier는 Jev 0.019, english 0.005, multilingual 0.000이다. Jev는 100% 표시가 0/40이고, 가장 애매한 행도 p(true) 0.58(gold true)과 0.09(gold false)라 0.5에서 떨어져 있다. T9는 Laya 학습 믹스 과제이고(BENCHMARKS.md:142 "in training"), upstream english 0.993과 같은 수준이다.
2. **T10 10-way 큐 라우팅은 세 시스템 모두 낮고, 차이는 유의하지 않다.** Jev 10/40 = 0.250 [0.142, 0.402], Laya english(= Router) 12/40 = 0.300 [0.181, 0.454], multilingual 18/40 = 0.450 [0.307, 0.602]이다. exact McNemar(b = Jev만 정답, c = Laya만 정답)는 vs english 3/5 p=0.727, vs multilingual 4/12 p=0.077이다. n=40에서 0.2 차이(multilingual)도 0.05 아래로 내려가지 않았다.
3. **T10의 Jev는 크게 과대확신이다.** 평균 top p 0.873인데 정확도는 0.250이다. 오답 30개 중 18개가 top ≥ 0.90이고, 정답 옵션을 0%로 표시한 행이 20/40(50%)이다. top ≥ 0.90만 남겨도 24행 중 18행이 오답이다. 같은 기준에서 Laya english는 6행 중 0, multilingual은 8행 중 0이 오답이다. Brier는 Jev 1.319, english 0.775, multilingual 0.611이고, ECE는 0.623 / 0.253 / 0.215다.
4. **T10의 낮은 정확도에는 gold 라벨 문제가 섞여 있다(해석, 확인 필요).** 세 시스템이 모두 틀린 행이 18/40이다. Human Resources와 Customer Service는 세 시스템 모두 0/4다. 이 행들의 티켓 내용은 우리가 준 큐 설명과 맞지 않는 경우가 많다. Jev의 오답 중 상당수는 설명을 따른 선택으로 읽힌다(가격 문의 → Sales and Pre-Sales) (Jev의 항목별 출력은 공개 저장소에서 생략). Laya가 앞선 Billing and Payments(Laya 4/4, Jev 2/4)는 "가격 문의 → Billing"이라는 데이터셋 관례와 맞는다. T10은 Laya 학습 믹스 과제다(BENCHMARKS.md:147).
5. **운영:** 요청 80회(A 40 + B 40)가 모두 HTTP 200이었다. 5xx · 4xx(429 포함) · 제한 문구 · captcha · 오류 화면은 0건이고 재시도도 없었다. 간격은 monotonic 기준 최소 15.009 s, 중앙 15.134 s다. 요청 전 sha12와 요청 후 body 바이트 대조가 80/80 일치했다. 사이트 전체 누적은 518회다.

플레이그라운드 경유이며 API가 아니다. 모델 버전은 표기되지 않았다(`typesafe-ai/jev` 80/80). 과제당 n=40이다. Jev 확률은 소수 둘째 자리 반올림이다. T9 · T10은 Laya 학습 믹스 과제이고 Jev 학습 데이터는 알 수 없다.

## 1. 실행 개요

| 항목 | 값 |
|---|---|
| 요청 | `POST /api/evaluate` 80회 = Part A(T9) 40 + Part B(T10) 40, 모두 HTTP 200. 계획 80, 세션 상한 90(재시도 여유). 계측 `ready()`가 Run 클릭 90회 이상이면 클릭하지 않도록 막았다(`raw/js/instrument.js`, 공개 저장소에는 포함하지 않음) |
| 중단 조건 | 5xx 0, 4xx 0(429 0), 제한 문구 0, captcha 0, 오류 화면 0. 매 run마다 결과 패널 · status · title · `[role=alert]` · body 텍스트를 제한 문구 정규식으로 검사했고 captcha iframe도 확인했다(`s7_record.py`, dump `page`). 80회 모두 `body_stop_match` null, alerts [], captcha_frames []. 입력 문자열(state · 질문 · 옵션) 중 이 정규식에 걸리는 것은 실행 전 0건으로 확인했다(`s7_prep.py` assert) |
| 간격 (Run 클릭 사이) | 가드 15 s(규칙 ≥ 10 s), 처음부터 monotonic 기준. 79개 간격: 최소 15.009 s, 중앙 15.134 s, 최대 22.770 s(run 2: run 1 스크린샷 뒤). resource timing 시작 간격도 15.008 / 15.134 / 22.768 s |
| 입력 동일성 | 요청 전: 폼 값으로 만든 payload sha12가 폼 파일 기대값과 80/80 일치(`window.__jev.ready`). 요청 후: 캡처한 request body가 `jev_cmp.py` payload와 바이트 단위로 80/80 같다(`payload_exact`). 첫 요청 전 무클릭 dry run 4회(item 1, 21, 29, 41) |
| 입력 내용 | T9: Single / Boolean, 질문 문장만(Laya noul에도 criteria 없음, Boolean 폼에는 라벨 · 설명 칸이 없다). T10: Single / Choice, 옵션 10개 `key: description`(Laya `render_options` 렌더링 그대로, 30\~73자, 모든 행 같은 목록 · 순서). State는 모두 Laya가 읽는 문자열 `json.dumps(state, ensure_ascii=False)`이고, 실행 전에 80행 모두 `state_text`와 같음을 확인했다. T9 body 최대 1,984자(upstream 절단 3,000자 미만), state 최대 2,117자(한도 8,000) |
| dry run 결과 | 4회 모두 폼 값 = 입력 문자열, sha12 일치, alert · invalid 없음. State 카운터 "712 / 8,000", "1,124 / 8,000", "2,117 / 8,000", "672 / 8,000". T10 선택지 10칸 길이 66 · 48 · 54 · 50 · 65 · 54 · 73 · 44 · 51 · 30자(maxLength 80)로 잘림 없음. item 21(T9 row 20)의 U+0092 문자도 보존됐다(`raw/dry_runs.json`) |
| 화면 = 응답 | 80/80(DECISION, 막대 %). 표시 지연 = `latencyMs` half-up 80/80 |
| Model ID / 응답 메타 | `model`과 View details 모두 `typesafe-ai/jev` 80/80. `rounding` {2, 2}, `warnings` [] 80/80. provider `confidence.decision`은 T10 40/40에 있고 T9 Boolean 40에는 없다 |

## 2. T9 Enron spam (40행, gold true 20 / false 20)

### 2.1 정확도 · 양성률 · 순위 품질

| system | correct / n | accuracy [Wilson 95%] | 예측 true (gold 20) | Brier | ECE | 평균 top p | AUROC p(true) [bootstrap 95%] |
|---|---|---|---|---|---|---|---|
| Jev (playground, 표시 p, 2자리) | 40/40 | **1.000** [0.912, 1.000] | 20 | 0.019 | 0.060 | 0.940 | 1.000 [1.000, 1.000]* |
| Laya english | 40/40 | 1.000 [0.912, 1.000] | 20 | 0.005 | 0.014 | 0.986 | 1.000 [1.000, 1.000]* |
| Laya multilingual | 40/40 | 1.000 [0.912, 1.000] | 20 | 0.000 | 0.000 | 1.000 | 1.000 [1.000, 1.000]* |
| Laya Router (40 모두 english) | 40/40 | 1.000 [0.912, 1.000] | 20 | 0.005 | 0.014 | 0.986 | 1.000 [1.000, 1.000]* |

- 판정 규칙은 p(true) ≥ 0.5(laya-evals 규칙)다. Brier는 S3 · S5와 같이 {false, true} 두 칸의 Σ(p − onehot)²(= 2(p − y)²)다.
- *네 시스템 모두 이 40행에서 완전 분리다. 그래서 모든 bootstrap 재표본의 AUROC가 1이 되어 percentile CI가 폭 0으로 퇴화했다. 모집단 AUROC가 1이라는 뜻이 아니다.
- Laya 값은 `PREP_20261008.md` §5의 vanilla T9 Jev 형식 40(1.000 / 1.000 / 1.000, Brier en / ml 0.005 / 0.000, ECE 0.014 / 0.000)과 같다.

### 2.2 일치, exact McNemar, AUROC 차이

| pair | n | 같은 예측 | b | c | McNemar p | AUROC Jev − Laya [paired bootstrap 95%] |
|---|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 40 | 0 | 0 | 1.0000 | +0.000 [+0.000, +0.000] |
| Jev vs Laya multilingual | 40 | 40 | 0 | 0 | 1.0000 | +0.000 [+0.000, +0.000] |
| Jev vs Laya Router | 40 | 40 | 0 | 0 | 1.0000 | +0.000 [+0.000, +0.000] |

### 2.3 확신도와 여유

| system | p(true) ∈ {0, 1} (100% 표시) | gold true 최소 p(true) | gold false 최대 p(true) | 서로 다른 p(true) 값 |
|---|---|---|---|---|
| Jev | 0/40 | 0.58 | 0.09 | 16 |
| Laya english (= Router) | 34/40 | 0.76 (row 23, id 1068) | 0.17 (row 26, id 1163) | 8 |
| Laya multilingual | 39/40 | 1.00 | 0.002 | 3 |

- Jev의 gold true p(true)는 0.58\~0.97(0.90 미만은 2개)이고 gold false는 0.01\~0.09다.
- Boolean에서 Jev가 100%를 표시하지 않는 패턴은 T5 · T8과 같다(`S5_summary.md` §4.3).

### 2.4 맥락

| 수치 | 값 | 비고 |
|---|---|---|
| Laya Enron spam upstream | english 0.993 / multilingual 0.993 (BENCHMARKS.md:142, test 앞 400행, in training) | 이번 40행 Wilson CI [0.912, 1.000] 안 |
| Laya vanilla ext500 | english 0.992 / multilingual 0.990 (`PREP_20261008.md` §5) | 같은 test split, 학습 세트와 겹치는 261행을 뺀 층화 표본 |
| Jev spam 공개치 | Enron 없음(제3자 SMS spam 0.930은 다른 데이터, bench_apps.py `JEV_PUBLISHED`) | |

## 3. T10 고객지원 티켓 큐 (40행, 큐당 4)

### 3.1 정확도 · 보정

| system | correct / n | accuracy [Wilson 95%] | Brier | ECE | 평균 top p |
|---|---|---|---|---|---|
| Jev (playground, 표시 p, 2자리) | 10/40 | **0.250** [0.142, 0.402] | 1.319 | 0.623 | 0.873 |
| Laya english | 12/40 | 0.300 [0.181, 0.454] | 0.775 | 0.253 | 0.504 |
| Laya multilingual | 18/40 | 0.450 [0.307, 0.602] | 0.611 | 0.215 | 0.586 |
| Laya Router (40 모두 english) | 12/40 | 0.300 [0.181, 0.454] | 0.775 | 0.253 | 0.504 |

Brier는 행마다 옵션 10개로 Σ(p − onehot)²를 계산했다. ECE는 15 bins, top p 기준이다. Laya 값은 `PREP_20261008.md` §5의 vanilla T10 Jev 형식 40(0.300 / 0.450 / 0.300, Brier 0.775 / 0.611, ECE 0.253 / 0.215)과 같다.

### 3.2 일치와 exact McNemar (b = Jev만 정답, c = Laya만 정답)

| pair | 같은 라벨 | b | c | p | b 행 | c 행 |
|---|---|---|---|---|---|---|
| Jev vs Laya english (= Router) | 18 | 3 | 5 | 0.7266 | — | — |
| Jev vs Laya multilingual | 9 | 4 | 12 | 0.0768 | — | — |

세 시스템 모두 정답 5행, 모두 오답 18행이다. multilingual과의 0.200 차이도 n=40에서 유의하지 않다(b=4이면 c ≥ 13이어야 p < 0.05).

### 3.3 큐별 정답 (n=4씩)

| gold | Jev | Laya english | Laya multilingual |
|---|---|---|---|
| Technical Support | 1 | 3 | 3 |
| Product Support | 0 | 0 | 2 |
| Customer Service | 0 | 0 | 0 |
| IT Support | 1 | 0 | 2 |
| Billing and Payments | 2 | 4 | 4 |
| Returns and Exchanges | 1 | 1 | 2 |
| Service Outages and Maintenance | 3 | 4 | 3 |
| Sales and Pre-Sales | 1 | 0 | 2 |
| Human Resources | 0 | 0 | 0 |
| General Inquiry | 1 | 0 | 0 |

### 3.4 예측 분포 (gold는 큐당 4)

| system | 예측 라벨 분포 |
|---|---|
| Jev | Technical Support 12, IT Support 9, General Inquiry 6, Sales and Pre-Sales 5, Service Outages 3, Billing 2, Product Support 2, Returns 1, Customer Service 0, Human Resources 0 |
| Laya english | Technical Support 21, Customer Service 5, Billing 4, Service Outages 4, Product Support 3, Returns 1, Sales 1, IT Support 1, General Inquiry 0, Human Resources 0 |
| Laya multilingual | Product Support 10, Technical Support 8, Billing 5, Customer Service 5, IT Support 4, Returns 3, Service Outages 3, Sales 2, General Inquiry 0, Human Resources 0 |

Jev는 Technical Support와 IT Support에 21/40을 몰았고, Laya english는 Technical Support에 21/40을 몰았다(`PREP_20261008.md` §5의 ext500 쏠림 281/500과 같은 방향). 아무 시스템도 Human Resources를 고르지 않았다.

### 3.5 확신도와 보류

| 항목 | Jev | Laya english | Laya multilingual |
|---|---|---|---|
| 평균 top p (정답 / 오답) | 0.861 / 0.877 | 0.780 / 0.386 | 0.797 / 0.413 |
| 오답 중 top ≥ 0.90 | 18/30 | 0/28 | 0/22 |
| 100% 표시 | 8/40(그중 오답 6) | - | - |
| 정답 옵션 0% 표시 | 20/40 | - | - |
| provider confidence (정답 / 오답) | 0.846 / 0.863 | - | - |

| 남기는 기준 | Jev 남는 행 / 오답 | Laya english 남는 행 / 오답 | Laya multilingual 남는 행 / 오답 |
|---|---|---|---|
| top ≥ 0.80 | 29 / 22 | 8 / 1 | 10 / 0 |
| top ≥ 0.90 | 24 / 18 | 6 / 0 | 8 / 0 |
| top ≥ 0.95 | 19 / 13 | - | - |

- Jev는 정답과 오답의 확신도가 같다(0.861 vs 0.877). 그래서 확신도 기준 보류가 오답을 걸러내지 못한다. Laya 두 체크포인트는 오답 확신도가 낮아 0.90 이상만 남기면 이 표본에서 오답이 0이다(같은 40행 기술통계).
- 정답 옵션 0% 비율 50%는 Jev 제3자 Emotion zero-probability 실패율 16%(bench_apps.py `JEV_PUBLISHED`)와 S2 T3 7/40(17.5%)보다 훨씬 높다.
- provider confidence는 top p와 같은 값이 18/40이고 정답 · 오답 평균이 거의 같아 별도 신호가 되지 않는다.

### 3.6 오류 구조 (해석, 확인 필요)

| 구분 | rows | 내용 (요약) |
|---|---|---|
| Jev가 100%로 틀림 | — | Technical Support 4개(gold Sales 1, Returns 2, IT 1), Sales 2개(gold Billing 2) |
| 세 시스템 모두 0/4인 큐 | Human Resources / Customer Service | HR gold 티켓은 의료 데이터 무단 접근 보고, 게임 상품 홍보 전략 문의, SaaS 통합 문의, QuickBooks 연동 문의다. CS gold 티켓은 시스템 성능 저하, 데이터 유출, 캠페인 참여 감소, 브랜드 성장 전략 문의다 |
| Laya만 정답 (Billing) | — | 가격 · 결제 옵션 문의를 Laya 세 러너가 모두 Billing으로 보냈다(0.98\~1.00). Jev는 "Sales and Pre-Sales: pricing, quotes, buying" 설명을 따라 Sales로 보냈다(100%) |

- 위 분류는 티켓을 읽고 내린 판단이다. 채점은 데이터셋 라벨 그대로 했다.
- 읽은 바로는 T10 gold의 상당수가 질문에 준 큐 설명(upstream bench_apps.py의 `QUEUES`와 같은 문구)과 맞지 않는다. 이 데이터셋에서 정확도는 "설명에 맞는 라우팅"보다 "데이터셋 라벨 관례와의 일치"에 가깝게 읽어야 한다. Laya는 이 데이터셋으로 학습했다고 upstream이 표기한다(in training).

### 3.7 맥락

| 수치 | 값 | 비고 |
|---|---|---|
| Laya support triage upstream | english 0.502 / multilingual 0.522 (BENCHMARKS.md:147, 영어 앞 400행, 자연 분포, in training) | 큐 분포가 달라 비교 불가. 우리 표본은 큐당 4로 균등 |
| Laya vanilla ext500 (큐 균등) | english 0.264 / multilingual 0.454 (`PREP_20261008.md` §5) | 두 값 모두 이번 40행 Wilson CI([0.181, 0.454], [0.307, 0.602]) 안 |
| Jev 고객지원 큐 공개치 | 없음 | |

## 4. 지연 · 토큰

| 구분 | runs | 표시 "server + network" ms median / min / max | 브라우저 POST ms median / min / max | 클릭 → 완료 ms median | POST − latencyMs median | 입력 토큰 median (min\~max), 합계 | 출력 토큰 median (min\~max), 합계 |
|---|---|---|---|---|---|---|---|
| Part A T9 (Boolean) | 40 | 214.5 / 169 / 388 | 481.5 / 388 / 1,243 | 482.5 | 243.2 | 427 (309\~1,059), 19,234 | 20 (20\~20), 800 |
| Part B T10 (Choice 10) | 40 | 226 / 154 / 311 | 495 / 388 / 702 | 496.5 | 239.0 | 681.5 (613\~739), 27,079 | 191 (185\~194), 7,644 |
| S7 전체 | 80 | 219 / 154 / 388 | 488.5 / 388 / 1,243 | 491 | 239.0 | 46,313 | 8,444 |

- T9 입력 토큰은 state 길이와 r = 0.964다. Boolean 출력은 T5 · T8과 같이 20 토큰으로 일정하다. T10 출력 191 토큰은 S5 T7(10옵션 key 렌더링) 150 안팎보다 많다. 옵션 문자열이 더 길어서로 보인다(추정).
- T9의 한 run에서 브라우저 POST가 1,243 ms(최대)였다. 같은 run의 `latencyMs`는 표시 지연 범위 안이라 차이는 네트워크 쪽이다(S5의 같은 사례와 같은 종류). 오류는 아니다.
- 표시 지연은 S1\~S5 파트별 중앙값(200\~241 ms)과 같은 수준이고 Jev 제3자 p50 236\~276 ms(09 §1)보다 약간 낮다. Laya 로컬 지연은 하드웨어와 경로가 달라 비교하지 않는다.

## 5. 관찰과 한계

**핵심 관찰 3개**
1. **T9는 변별력이 없다.** 네 시스템이 같은 40행을 모두 맞혔고 순위도 완전하다. 남은 차이는 보정뿐이다(Jev는 0/1을 내지 않고 0.01\~0.97 범위, Laya는 대부분 0 또는 1). Laya의 학습 믹스 과제라는 점을 감안해도 Jev zero-shot이 같은 정확도를 냈다.
2. **T10에서 Jev는 정확도가 가장 낮고(0.250) 보정이 가장 나쁘다.** 정답 옵션을 0%로 표시한 행이 절반이고, 고확신 오답이 많아 확신도 보류가 통하지 않는다. 오답 중 top ≥ 0.90 비율(18/30 = 60%)은 S6 종합의 단일 choice 패턴(오답의 59%, `docs/09_laya_vs_jev_plan.md` §10 "보정")과 같은 수준이고, 정답 옵션 0% 비율(50%)은 지금까지 측정한 단일 choice · score 과제 중 가장 높다(T2 1/40, T3 7/40, T4 0/40, T6 1/40, T7 0/100; 각 세션 `analyze` 출력).
3. **T10 정확도의 상당 부분은 gold 라벨 관례 문제와 섞여 있다(해석).** 세 시스템 모두 틀린 행이 18/40이고, HR · Customer Service는 모두 0/4다. Laya가 앞선 큐(Billing)는 데이터셋 관례와 맞는 쪽이다. Laya multilingual 0.450 대 Jev 0.250의 차이(p=0.077)를 "라우팅 능력" 차이로 읽으려면 gold 점검이 먼저다.

**한계**
- 플레이그라운드 경유이며 API가 아니다. 모델 버전이 표기되지 않고 프롬프트 래핑을 알 수 없다.
- 과제당 n=40(95% CI 폭 약 ±0.15)이다. T10은 큐당 4행이라 큐별 수치는 방향 신호다.
- T9 AUROC의 bootstrap CI는 완전 분리로 퇴화했다. AUROC 차이도 정보가 없다.
- Jev 확률은 2자리 반올림이다(T9 p(true) 서로 다른 값 16개).
- T9 · T10은 upstream 표기로 Laya 학습 믹스 과제다(BENCHMARKS.md:142, :147). Jev 학습 데이터는 알 수 없다. T10은 공개 split이 하나뿐이라 우리 test 몫이 upstream 학습에 들어갔을 수 있다(`PREP_20261008.md` §2).
- T10 gold 라벨의 품질은 확인하지 않았다(§3.6은 해석).

## 6. 운영 기록과 이상

- 사이트 상태: 15:21:49 페이지 정상 로드, 계측 설치 시 body 제한 문구 없음. UI · DOM id는 S5와 같다. 지시에 따라 기본 예시는 실행하지 않았다.
- 네트워크 목록: POST 80(모두 `/api/evaluate`, 200), GET 58(문서 1, 정적 31, Next.js RSC prefetch 26 = 13개 경로 × 2, 모두 200). RSC prefetch는 사이트가 화면의 링크를 미리 받는 요청이고 이동은 없었다(S5는 12건). resource timing `/api/evaluate` 80건 = Run 클릭 80회, 클릭 → fetch 시작 0\~3 ms.
- 콘솔: 경고 182건(모두 CSS preload), 오류 0건(`raw/console.log`, 공개 저장소에는 포함하지 않음).
- 호스트 wall clock: wall − mono 오프셋 −1 \~ +1 ms, 스텝 없음.
- 요청 없는 클릭: Run 클릭은 80회뿐이다. 무클릭 dry run 4회는 폼 입력과 해시 · DOM 대조만 했다. 스크린샷용 View details는 클릭 없이 DOM에서 `details.open = true`로 열었다.
- 간격 최대 22.8 s(run 2)는 run 1 스크린샷, 19.0 s(run 42)는 run 41 스크린샷, 18.7 s(run 41)는 파트 경계와 run 40 스크린샷 시간이다.
- 세션 중 다른 프로세스가 `docs/`(00, 09, 10, 11)와 `results/F/jev_cmp/__pycache__/s6_summary.cpython-312.pyc`를 바꿨다. 이 세션의 변경이 아니다(`S7_run_card.md` "이상 / 주석").

## 7. 파일

| 파일 | 내용 |
|---|---|
| `results/F/jev_cmp/sessions/S7_20261008/S7_requests.jsonl`(공개 저장소에는 포함하지 않음) | 80줄(run = item, 재시도 없음). choice는 `pred` · `probs` · `top_p` · `shown_pct`, Boolean은 `p_true` · `pred`, run별 `latency_ms_response` · `displayed_ms` · `fetch_dur_ms` · `click_to_complete_ms` · `usage` · `confidence` · `model_id_details`. `click_epoch_ms`는 monotonic 축 |
| `results/F/jev_cmp/jev_runs_all.jsonl`(공개 저장소에는 포함하지 않음) | master 491줄. 앞 411줄(634,031 bytes)은 S7 전 사본과 바이트 동일, 뒤 80줄은 `S7_requests.jsonl`과 동일 |
| `raw/rNNN_<T9|T10>_rowRR.json`(공개 저장소에는 포함하지 않음) | 요청별 dump 80개 |
| `raw/run_plan.json`, `raw/js/`, `raw/dry_runs.json` | 항목 계획 80, 계측 `instrument.js`(S5 + 버전 태그 S7 + 세션 상한 90), 항목별 입력 스크립트 `i001~i080`, 무클릭 dry run 4개와 그 결과(`raw/js/`는 공개 저장소에는 포함하지 않음) |
| `raw/evaluate_timing_all.json`, `raw/network_requests.txt`, `raw/network_requests_all.txt`, `raw/console.log`, `raw/mcp/` | resource timing 80건과 클릭 시각(monotonic · wall), 네트워크 목록, 콘솔, MCP snapshot(페이지 로드, dry run 폼 2개)과 MCP 콘솔 로그(다섯 항목 모두 공개 저장소에는 포함하지 않음) |
| `raw/analyze/`(공개 저장소에는 포함하지 않음) | `T9.md`, `T10.md`(`analyze S7 <SET>` 출력) |
| `shots/` | 파트별 첫 · 마지막 run 4장(View details 열림, full page, 공개 저장소에는 포함하지 않음): `S7_A_item001_run001_T9_row00.png`, `S7_A_item040_run040_T9_row39.png`, `S7_B_item041_run041_T10_row00.png`, `S7_B_item080_run080_T10_row39.png` |
| `s7_prep.py`, `s7_record.py` | 계획 · 입력 스크립트 생성(Laya `serialize_state` · `render_options` 일치, T10 `key: description` 렌더링, T9 noul criteria 없음, body ≤ 3,000자, 입력 중단 문구 0 assert), 기록 래퍼(S5와 같은 중단 조건 분류, stale dump 거부) |
| `results/F/jev_cmp/jev_cmp.py` | T9 · T10의 Laya 리포트를 `results/T3arm/vanilla/`에서 읽는 최소 수정(`LAYA_DIRS`, `laya_report`). 상세는 run card |
| 재현 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S7 T9_enron_spam_40`, `… analyze S7 T10_support_tickets_queue_40` |

[English](S7_summary.md) | **한국어**
