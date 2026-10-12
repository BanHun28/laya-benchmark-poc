# S1 요약: Multiple questions 탐색 + T2 AG News 40 (2026-10-06)

**판정.**
1. Multiple questions 모드는 Score를 정확히 5레벨로만 받아 T1 case를 온전히 실을 수 없다(4레벨 score 70/80 decisions). 규칙대로 Step 2b(T2)로 전환했다. 상세는 `multi_question_mode.md`.
2. T2 AG News 40에서 Jev 35/40 = 0.875, Laya english·router 39/40 = 0.975, multilingual 37/40 = 0.925. Jev가 맞히고 Laya가 틀린 항목은 0개라 b = 0이고, exact McNemar p는 english 0.125, multilingual 0.5다. n = 40에서는 구분되지 않는다.
3. Jev의 오답 5개 중 4개가 표시 확률 93\~99%였다. 파일럿(오답 전부 < 90%)과 반대로, 이 과제에서는 확신도 임계값으로 오답을 거를 수 없었다.

플레이그라운드 경유이며 API가 아니다. 모델 버전은 표기되지 않고(`typesafe-ai/jev`), 소표본(n = 40)이다. T2는 Laya 학습 믹스에 포함된 소스라 Laya 쪽에 유리할 수 있다(MANIFEST `in_training_mix: yes`).

## 1. 실행

| 항목 | 값 |
|---|---|
| 요청 (`POST /api/evaluate`) | 41회, 모두 HTTP 200. 탐색 1(T1 row 30, Multiple questions 4문항) + T2 40(Single question, Choice 4) |
| 오류·재시도 | 0 / 0. 5xx·429·rate-limit 문구·captcha 없음. 콘솔 오류 0(경고 185는 CSS preload 안내) |
| 요청 없는 Run 클릭 | 1회(4레벨 rubric 검증 probe). 클라이언트 검증에서 막혔고 요청 0건을 wrapper와 resource timing으로 확인 |
| 간격 | Run 클릭 간격 최소 17.0 s, 중앙 17.4 s(규칙 ≥ 10 s). precheck 함수가 마지막 클릭 뒤 12 s 전에는 반환하지 않는다 |
| 입력 동일성 | 41/41 요청 body가 폼 파일에서 만든 payload와 바이트 단위로 같다(precheck sha12 + 사후 body 대조) |
| 표시 대조 | 41/41 화면 DECISION·%·ms가 응답 JSON과 같다. "N ms · server + network" = round(`latencyMs`) |
| 세션 예산 | 50 중 41 사용, 9 남음 |

## 2. T2 결과 (같은 40 항목)

| system | 정답 / n | accuracy | Wilson 95% CI | Brier | ECE (15 bins) | 평균 top p |
|---|---|---|---|---|---|---|
| Jev (playground, 표시 확률) | 35/40 | 0.875 | [0.739, 0.945] | 0.220 | 0.118 | 0.977 |
| Laya english | 39/40 | 0.975 | [0.871, 0.996] | 0.053 | 0.083 | 0.930 |
| Laya multilingual | 37/40 | 0.925 | [0.801, 0.974] | 0.107 | 0.058 | 0.983 |
| Laya router (40/40 english로 라우팅) | 39/40 | 0.975 | [0.871, 0.996] | 0.053 | 0.083 | 0.930 |

Jev Brier·ECE는 2자리 반올림 확률로 계산했다(Brier 하한 오차 약 ±0.005, ECE는 bin이 성겨 참고용).

**짝 비교** (b = Jev 정답 & Laya 오답, c = Jev 오답 & Laya 정답)

| pair | n | 같은 라벨 | b | c | exact McNemar p |
|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 36 | 0 | 4 | 0.125 |
| Jev vs Laya multilingual | 40 | 38 | 0 | 2 | 0.500 |
| Jev vs Laya router | 40 | 36 | 0 | 4 | 0.125 |

**클래스별 정답** (gold당 10)

| gold | Jev | Laya english | Laya multilingual | Laya router |
|---|---|---|---|---|
| world | 8 | 9 | 8 | 9 |
| sports | 10 | 10 | 10 | 10 |
| business | 10 | 10 | 10 | 10 |
| sci_tech | 7 | 10 | 9 | 10 |

Jev 혼동: world → business 2, sci_tech → business 2, sci_tech → world 1. Jev는 오답 5개를 모두 business 또는 world로 냈다.

**Jev 오답 5개**

| row | id | 기사 (앞부분) (AG News 원문 생략) | gold | Jev (표시 %) (Jev의 항목별 출력은 공개 저장소에서 생략) | Laya en | Laya ml |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |
| — | — | — | — | — | — | — |
| — | — | — | — | — | — | — |
| — | — | — | — | — | — | — |
| — | — | — | — | — | — | — |

오답 중 1개는 gold 자체가 의심스럽다. 3개도 business와 겹치는 경계 사례다. AG News의 sci_tech는 기술 기업 뉴스까지 포함하는데, Jev는 "science and technology" 설명을 더 좁게 읽는 것으로 보인다(추정).

## 3. Jev 확신도

| 지표 | 값 |
|---|---|
| top = 100% 표시 | 29/40 (72%) |
| 0% 옵션이 있는 run | 40/40. 0% 칸 109/160 |
| 평균 top % (정답 / 오답) | 98.5 / 92.2 |
| 오답 중 top ≥ 90% | 4/5 |
| gold 옵션이 0%로 표시된 run | 1 |
| provider confidence 평균 (정답 / 오답) | 0.980 / 0.894 |
| p ≥ 0.90만 수용 | 38/40 수용, 34 정답(0.895) |
| coverage @ 오류 ≤ 5% / 10% | 0.800 (t = 0.98) / 0.875 (t = 0.94) |

비교: Laya english는 p ≥ 0.90에서 33/40 수용, 33 정답(1.000)이고, 유일한 오답(row 15)의 확신도는 0.76이다. multilingual은 38/40 수용, 37 정답이며 오답 3개 중 1개(row 15, 0.98)가 0.90 이상이다. coverage @ 오류 ≤ 5%는 english 1.000, multilingual 0.950이다.

## 4. 지연·토큰 (Jev 성공 40회)

| 측정 | median / min / max (ms) |
|---|---|
| 표시 "server + network" (= 응답 `latencyMs`) | 234 / 188 / 448 |
| 브라우저 POST (resource timing) | 468 / 415 / 749 |
| 클릭 → "Evaluation complete" | 470.5 / 417 / 751 |

| Laya 로컬 참조 (하드웨어·경로가 달라 모델 속도 비교 아님) | ms | 출처 |
|---|---|---|
| P2 `/poc/decide` HTTP loopback 왕복 p50 (ft-v1, MPS) | 20.1 | `results/poc/P2_20261003.md:67` |
| D1 in-process 1q median, english CPU fp32, short state 123 tok | 86.6 | `results/D/D_summary_20261003.md:34` |
| D1 in-process 1q median, english MPS | 31.8 | `results/D/D_summary_20261003.md:40` |
| D1 in-process 1q median, multilingual MPS (파일럿 인용치) | 13.8 | `results/D/D_summary_20261003.md:42` |

Jev 브라우저 POST 중앙값은 P2 왕복의 23.3배, english CPU in-process의 5.4배다. 표시값은 브라우저 POST보다 중앙 232 ms 짧아 클라이언트↔playground 구간을 빼고 잰 값이다. 파일럿(249.5 vs 497.5 ms)과 같은 구조이고, 제3자 공개 Jev p50 236\~276 ms 범위 안이다.

토큰: 입력 중앙 425 (402\~534), 출력 중앙 68 (66\~71). Model ID `typesafe-ai/jev` 40/40, `rounding` {probabilityDecimals 2, scoreDecimals 2}, `warnings` 항상 빈 배열. 파일럿(한국어 8옵션)의 출력 255 토큰보다 훨씬 적어, 출력 토큰이 옵션 수나 라벨 길이에 따라 늘어나는 것으로 보인다(추정).

## 5. 대표성

- Jev 0.875 [0.739, 0.945]는 제3자 공개 Jev AG News 0.910(`docs/09_laya_vs_jev_plan.md` §1) 범위 안이다.
- Laya english 0.975 [0.871, 0.996]는 upstream 0.947 / 0.950(`laya_summary.md` §1) 범위 안이다.
- 따라서 이 표본이 두 시스템의 공개 수준에서 벗어났다는 증거는 없다. 다만 CI 폭이 약 ±0.1이다.

## 6. 관찰 3가지

1. **차이의 방향은 일관되지만 유의하지 않다.** Laya가 맞히고 Jev가 틀린 4항목(english 기준)은 있고 반대 방향은 0이다. b = 0이라 n = 40에서 최소 p는 c에만 달려 있다. c = 6 이상이어야 p < 0.05가 된다.
2. **Jev의 확률은 이 과제에서 과신한다.** 표시 72%가 100%이고 오답 4/5가 93% 이상이라 Brier 0.220(Laya english 0.053)이다. 파일럿 한국어 라우팅에서는 오답이 모두 41\~86%여서 90% 임계값이 오답을 걸렀다. 과제에 따라 보정 양상이 달라지므로 T3(emotion, 공개 Jev 0.480)에서 다시 봐야 한다.
3. **오답은 라벨 경계에 몰려 있다.** 5개 모두 business/world와 sci_tech/world의 경계 사례이고, 1개는 gold가 의심스럽다. 라벨 설명 한 줄(`sci_tech: science and technology`)이 AG News의 "기술 기업 뉴스 = sci_tech" 관례를 담지 못한다. 파일럿의 `play → media` 사례와 같은 "설명에 없는 데이터셋 관례" 유형이다. Laya english는 4/5를 맞혔는데, T2가 Laya 학습 믹스에 있다는 점과 분리할 수 없다.

## 7. 남은 예산 (S2 이후)

| 과제 | 계획 요청 | S1 사용 | 남은 요청 | 비고 |
|---|---|---|---|---|
| T1 typed-decisions | 40 (multi) | 1 (row 30, 탐색) | 안 A 39 / 안 C 120 / 결정 필요 | 4레벨 score 70 decisions는 어느 모드로도 같은 입력 불가(`multi_question_mode.md` §3) |
| T2 AG News | 40 + 순열 20 | 40 | 순열 프로브 20 | 본 측정 완료 |
| T3 Emotion | 40 | 0 | 40 | |
| T4 Banking77-10 (key-only 재빌드) | 40 | 0 | 40 | |
| T5 BoolQ | 40 | 0 | 40 | Boolean, 제약 없음 |
| T6 SST-5 | 40 | 0 | 40 | Score 5레벨, 루브릭에 그대로 들어감 |
| T7 MASSIVE 5개 언어 | 100 | 0 | 100 | |
| T8 prompt-injections (선택) | 40 | 0 | 40 | |
| 결정성 점검 | 10 | 0 | 10 | |

오늘(2026-10-06) 사이트 사용량은 파일럿 25회(`results/F/F_jev_20261006.md`) + 가용성 확인 2회(08:01, 08:20, 같은 문서에 별도 기재) + S1 41회 = 68회다. 하루 상한 100까지 오늘은 32회 남는다. 세션 80 / 하루 100 상한을 지키는 안:

| 일차 | 세션 | 내용 | 요청 |
|---|---|---|---|
| 1 (오늘, 선택) | S2a | T2 순열 프로브 20 + 결정성 10 | 30 |
| 2 | S3 | T1 안 A 39(결정 시) + T3 40 | 79 |
| 3 | S4 | T4 40 + T5 40 | 80 |
| 4 | S5 | T6 40 + T7 en·de 40 | 80 |
| 5 | S6 | T7 ja·zh-CN·ko 60 (+ 여유 시 T8 일부) | 60\~80 |
| 6 (선택) | S7 | T8 나머지 | ≤ 40 |

T1을 안 C(Single 120)로 하면 2\~3일차에 T1만 120을 두 세션으로 나누고 T8을 뺀다.

갱신(10:38): 1일차 S2a(T2 순열 20 + 결정성 10)는 S1b로 실행했다(`results/F/jev_cmp/sessions/S1b_20261006/S1b_summary.md`). 오늘 누적은 98회이고, T2의 남은 요청은 0이다.

## 8. 파일

| 파일 | 내용 |
|---|---|
| `results/F/jev_cmp/sessions/S1_20261006/multi_question_mode.md` | 모드 탐색, 조작 레시피, 한계, T1 선택지 |
| `results/F/jev_cmp/sessions/S1_20261006/S1_requests.jsonl`(공개 저장소에는 포함하지 않음) | 세션 요청 41줄(성공·실패 모두 기록하는 형식) |
| `results/F/jev_cmp/jev_runs_all.jsonl`(공개 저장소에는 포함하지 않음) | master append-only 로그(현재 41줄, `session` 필드) |
| `results/F/jev_cmp/sessions/S1_20261006/raw/rNN_*.json`(공개 저장소에는 포함하지 않음) | 요청별 DOM dump, 요청 body, 응답 text, resource timing, 상태 로그 |
| `results/F/jev_cmp/sessions/S1_20261006/raw/network_requests.txt`, `console.log`, `mcp/` | 브라우저 네트워크 목록(POST 41, GET 104), 콘솔 로그, MCP 자동 snapshot 63개(세 항목 모두 공개 저장소에는 포함하지 않음) |
| `results/F/jev_cmp/sessions/S1_20261006/shots/`(공개 저장소에는 포함하지 않음) | 탐색 4장, T2 run 1·20·40 |
| `results/F/jev_cmp/jev_cmp.py` | expect / record / analyze. 이 요약의 표는 `analyze S1 T2_ag_news_40` 출력이다 |
| `results/F/jev_cmp/sessions/S1_20261006/S1_run_card.md` | run card |

## 부록: 항목별 결과 (`jev_cmp.py analyze S1 T2_ag_news_40`)

| # | row | id | gold | Jev (top %) | Laya english (p) | Laya multilingual (p) | Laya router (p) |
|---|---|---|---|---|---|---|---|
| 1 | 0 | 63 | sci_tech | — | O sci_tech (0.98) | O sci_tech (1.00) | O sci_tech (0.98) |
| 2 | 1 | 320 | business | — | O business (0.97) | O business (1.00) | O business (0.97) |
| 3 | 2 | 501 | sports | — | O sports (1.00) | O sports (1.00) | O sports (1.00) |
| 4 | 3 | 630 | sci_tech | — | O sci_tech (0.94) | O sci_tech (1.00) | O sci_tech (0.94) |
| 5 | 4 | 974 | sports | — | O sports (0.99) | O sports (1.00) | O sports (0.99) |
| 6 | 5 | 1125 | sci_tech | — | O sci_tech (0.82) | O sci_tech (0.96) | O sci_tech (0.82) |
| 7 | 6 | 1145 | sports | — | O sports (0.89) | O sports (1.00) | O sports (0.89) |
| 8 | 7 | 1223 | business | — | O business (0.96) | O business (1.00) | O business (0.96) |
| 9 | 8 | 1418 | sports | — | O sports (0.99) | O sports (1.00) | O sports (0.99) |
| 10 | 9 | 1506 | world | — | O world (0.93) | O world (0.97) | O world (0.93) |
| 11 | 10 | 1740 | sports | — | O sports (0.98) | O sports (1.00) | O sports (0.98) |
| 12 | 11 | 1782 | sports | — | O sports (0.99) | O sports (1.00) | O sports (0.99) |
| 13 | 12 | 1958 | business | — | O business (0.99) | O business (1.00) | O business (0.99) |
| 14 | 13 | 2053 | world | — | O world (0.84) | X business (0.76) | O world (0.84) |
| 15 | 14 | 2185 | sci_tech | — | O sci_tech (0.57) | O sci_tech (0.95) | O sci_tech (0.57) |
| 16 | 15 | 2306 | world | — | X business (0.76) | X business (0.98) | X business (0.76) |
| 17 | 16 | 2636 | business | — | O business (0.98) | O business (1.00) | O business (0.98) |
| 18 | 17 | 3699 | business | — | O business (0.96) | O business (1.00) | O business (0.96) |
| 19 | 18 | 4536 | business | — | O business (0.99) | O business (1.00) | O business (0.99) |
| 20 | 19 | 5043 | sci_tech | — | O sci_tech (0.58) | X business (0.77) | O sci_tech (0.58) |
| 21 | 20 | 5209 | sports | — | O sports (0.98) | O sports (1.00) | O sports (0.98) |
| 22 | 21 | 5236 | world | — | O world (0.98) | O world (1.00) | O world (0.98) |
| 23 | 22 | 5458 | sports | — | O sports (0.99) | O sports (1.00) | O sports (0.99) |
| 24 | 23 | 5561 | world | — | O world (0.99) | O world (1.00) | O world (0.99) |
| 25 | 24 | 5568 | world | — | O world (0.98) | O world (1.00) | O world (0.98) |
| 26 | 25 | 5751 | business | — | O business (0.88) | O business (1.00) | O business (0.88) |
| 27 | 26 | 6060 | sports | — | O sports (0.94) | O sports (1.00) | O sports (0.94) |
| 28 | 27 | 6183 | business | — | O business (0.96) | O business (1.00) | O business (0.96) |
| 29 | 28 | 6492 | sci_tech | — | O sci_tech (0.92) | O sci_tech (0.99) | O sci_tech (0.92) |
| 30 | 29 | 6514 | world | — | O world (0.93) | O world (0.98) | O world (0.93) |
| 31 | 30 | 6653 | sci_tech | — | O sci_tech (0.94) | O sci_tech (1.00) | O sci_tech (0.94) |
| 32 | 31 | 6815 | sci_tech | — | O sci_tech (0.91) | O sci_tech (1.00) | O sci_tech (0.91) |
| 33 | 32 | 6900 | business | — | O business (0.98) | O business (1.00) | O business (0.98) |
| 34 | 33 | 6942 | world | — | O world (0.97) | O world (0.99) | O world (0.97) |
| 35 | 34 | 6961 | business | — | O business (0.97) | O business (1.00) | O business (0.97) |
| 36 | 35 | 7120 | sci_tech | — | O sci_tech (0.92) | O sci_tech (1.00) | O sci_tech (0.92) |
| 37 | 36 | 7152 | sports | — | O sports (0.99) | O sports (1.00) | O sports (0.99) |
| 38 | 37 | 7257 | world | — | O world (0.98) | O world (1.00) | O world (0.98) |
| 39 | 38 | 7302 | sci_tech | — | O sci_tech (0.98) | O sci_tech (1.00) | O sci_tech (0.98) |
| 40 | 39 | 7460 | world | — | O world (0.91) | O world (0.99) | O world (0.91) |

[English](S1_summary.md) | **한국어**
