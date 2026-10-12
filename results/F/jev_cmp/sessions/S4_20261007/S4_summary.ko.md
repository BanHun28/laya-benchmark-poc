# S4 요약: T6 SST-5 40 (Score 5레벨) + T7 MASSIVE intent-10 en 20 · de 20 (2026-10-07)

**판정.**
1. **T6 SST-5에서 Jev가 오차 크기로는 Laya 세 러너보다 분명히 작고, 주 지표(argmax 정확도)로는 english와 유의하게 구분되지 않는다.** argmax 레벨 정확도는 Jev 26/40 = **0.650** [0.495, 0.779], Laya english·Router 0.425, multilingual 0.325다. exact McNemar(b/c)는 Jev vs english 15/6 p=0.078, vs multilingual 18/5 p=0.011이다. 보조 지표(E[level]을 반올림한 레벨, 플레이그라운드 표시 규칙)로는 0.675 vs 0.400 / 0.325이고 15/4 p=0.019, 19/5 p=0.007이다. E[level]의 MAE는 Jev **0.432**, english 0.888, multilingual 1.419다. paired bootstrap 차이는 −0.456 [−0.711, −0.207], −0.987 [−1.341, −0.622]로 두 쌍 모두 0을 포함하지 않는다. Brier(5레벨)는 0.502 / 0.770 / 1.149다.
2. **Laya의 T6 실패는 척도 압축이다. #131의 첫 레벨 회피는 이 표본에서 재현되지 않았다.** 평균 부호 오차(E − gold)는 Jev −0.014, english −0.687, multilingual −1.280이다. english는 레벨 4를 한 번도 고르지 않았다(0/40, gold 8/40). multilingual은 40행 모두 레벨 0 또는 1을 골랐다(11 / 29, 레벨 2\~4는 0/40). multilingual의 첫 레벨 선택은 11/40으로 gold 8/40보다 많다. Jev의 레벨 분포는 4/13/6/12/5이고 양 끝 레벨을 덜 고른다(첫 레벨 4/40, 마지막 레벨 5/40).
3. **T7 MASSIVE-10에서 Jev는 en과 de에서 같은 정확도를 냈고, Laya는 de에서 크게 떨어졌다.** Jev는 en 18/20, de 18/20(0.900)이다. Laya english는 0.70 → 0.35, multilingual은 0.85 → 0.40, Router는 0.70 → 0.35다. de에서 Jev vs english는 b/c 11/0 p=0.001, vs multilingual 11/1 p=0.006이다. en에서는 4/0 p=0.125, 3/2 p=1.0으로 구분되지 않는다. en+de 40을 합치면 Jev 36/40 = 0.900, english 21/40, multilingual 25/40이고 b/c는 15/0 p=0.0001, 14/3 p=0.013이다. 같은 id에서 en과 de의 라벨이 같은 비율은 Jev 19/20, english 10/20, multilingual 7/20이다. n=20 언어별 결과는 방향 신호다.
4. **운영:** 요청 80회(A 40 + B 20 + C 20)가 모두 HTTP 200이었다. 5xx, 4xx(429 포함), 제한 문구, captcha는 0건이고 재시도도 없었다. 간격은 monotonic 기준 최소 15.013 s, 중앙 15.125 s다. 오늘 누적은 S2 80 + S3 80 + S4 80 = 240회이고 끝까지 제한 신호가 없었다.

플레이그라운드 경유이며 API가 아니다. 모델 버전은 표기되지 않았다(`typesafe-ai/jev` 80/80). 표본은 T6 n=40, T7 언어당 n=20이다. Jev 확률과 score는 소수 둘째 자리로 반올림된다. T6(SST-5)는 upstream 표기상 Laya held out이고 T7은 unknown이다. Jev의 학습 데이터는 알 수 없다.

## 1. 실행 개요

| 항목 | 값 |
|---|---|
| 요청 | `POST /api/evaluate` 80회 = Part A(T6) 40 + Part B(T7 en) 20 + Part C(T7 de) 20, 모두 HTTP 200. 세션 상한 100(계획 80), 하루 상한은 프로젝트 책임자 결정(2026-10-07)으로 해제 |
| 중단 조건 | 5xx 0, 4xx 0(429 0), 제한 문구 0, captcha 0, 오류 화면 0. 매 run마다 결과 패널·status·title·`[role=alert]`·body 텍스트를 제한 문구 정규식으로 검사했고 captcha iframe 유무도 확인했다(`s4_record.py`, dump `page`). 80회 모두 `body_stop_match` null, alerts [], captcha_frames []였다 |
| 간격 (Run 클릭 사이) | 가드 15 s, 처음부터 monotonic 기준(`performance.timeOrigin + performance.now()`). 79개 간격: 최소 15.013 s, 중앙 15.125 s, 최대 31.109 s(run 2, run 1 스크린샷 시간). resource timing `startTime` 차로 다시 재면 15.014 / 15.125 / 31.105 s다. 파트 경계(run 41, 61)는 dry run과 스크린샷 때문에 21.1 s였다 |
| 입력 동일성 | 요청 전: 폼 값으로 만든 payload sha12가 폼 파일 기대값과 80/80 일치(`window.__jev.ready`). 요청 후: 캡처한 request body가 `jev_cmp.py` payload와 바이트 단위로 80/80 같다(`payload_exact`). 무클릭 dry run 3회(item 1, 41, 61) |
| 입력 내용 | T6: Single / Score. Rubric level 0\~4 칸에 폼 `options`를 그대로 넣었다(`level 0: very negative` … `level 4: very positive`, 최대 22자). 이 문자열은 Laya가 score 질문에서 읽는 렌더링(`laya/common.py` `render_options`: `"level %d: %s"`)과 같고, `s4_prep.py`가 `render_options(Agent._to_internal(q))`와의 일치를 40행 모두 assert했다. S1·S2의 T1 score run도 같은 렌더링을 보냈다(S1 run 1 request body). T7: Single / Choice. 옵션 10개 `key: key spaced`(최대 50자)를 폼 순서대로 넣었다. en과 de는 같은 id·gold·옵션 목록이다(`s4_prep.py` assert). State는 모든 과제에서 Laya가 읽는 JSON 문자열(`state_text`)이다 |
| 화면 = 응답 | 80/80. T6은 SCORE 카드(표시 레벨 = `rubric[Math.round(score)]`, "x.xx / 4", 막대 "k — level k: …")를 응답과 대조했다. 단일 모드 Score 카드의 머리글은 DECISION이 아니라 SCORE라서 `parse_single_display`를 그에 맞게 고쳤다(아래 §7). 표시 지연 = `latencyMs` half-up 80/80 |
| Model ID / 응답 메타 | `model`과 View details 모두 `typesafe-ai/jev` 80/80. `rounding` {2, 2}, `warnings` [] 80/80. provider `confidence.decision`은 80/80에 있다(T6 포함). T6의 Jev score는 40/40이 정수가 아니었다("Nearest rubric level. Jev returned an interpolated score.") |

## 2. T6 SST-5 (40행, gold 레벨 0\~4 각 8)

Jev E[level]은 응답의 `score`(소수 둘째 자리)이고 Laya E[level]은 `answer.score`다. argmax는 동점이면 낮은 레벨이다(`np.argmax`와 같다). Jev는 이번 40행에 argmax 동점이 없었다. Jev `score`와 반올림 확률로 계산한 Σ k·p_k의 차이는 최대 0.020이다.

### 2.1 정확도·오차·보정 (같은 40행, 같은 질문과 레벨 문구)

| system | argmax 레벨 정답 [Wilson 95%] | 반올림 E[level] 정답 [Wilson 95%] | MAE E[level] | 평균 E − gold | ±1 레벨 이내 | Brier (5레벨) | ECE (15 bins, argmax p) | 평균 top p | argmax ≠ 반올림 E |
|---|---|---|---|---|---|---|---|---|---|
| Jev (playground, 표시 p, 2자리) | 26/40 = **0.650** [0.495, 0.779] | 27/40 = 0.675 [0.520, 0.799] | **0.432** | −0.014 | 0.875 | 0.502 | 0.184 | 0.751 | 2 |
| Laya english | 17/40 = 0.425 [0.285, 0.578] | 16/40 = 0.400 [0.263, 0.554] | 0.888 | −0.687 | 0.650 | 0.770 | 0.239 | 0.654 | 6 |
| Laya multilingual | 13/40 = 0.325 [0.201, 0.480] | 13/40 = 0.325 [0.201, 0.480] | 1.419 | −1.280 | 0.400 | 1.149 | 0.513 | 0.824 | 0 |
| Laya Router (40 모두 english) | 17/40 = 0.425 | 16/40 = 0.400 | 0.888 | −0.687 | 0.650 | 0.770 | 0.239 | 0.654 | 6 |

- Laya 값은 `laya_summary.json` `results.T6_sst5_40`(accuracy 0.425 / 0.325, brier 0.770 / 1.149, ece 0.239 / 0.513, score_mae 0.888 / 1.419, within_1_level 0.650 / 0.400)과 같다.
- Jev는 표시 규칙(반올림 E)과 argmax가 2행에서 갈렸다. 1행은 표시 레벨만 맞았고, 1행은 둘 다 틀렸다(Jev의 항목별 출력은 공개 저장소에서 생략). 그래서 표시 규칙이 1행 더 맞는다. Laya english는 반대로 표시 규칙이 1행 손해다(17 → 16).

### 2.2 일치, exact McNemar, MAE 차이 (b = Jev만 정답, c = Laya만 정답)

| pair | n | 같은 argmax | argmax b / c | p | 반올림 E b / c | p | MAE Jev − Laya [paired bootstrap 95%] |
|---|---|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 17 | 15 / 6 | 0.0784 | 15 / 4 | 0.0192 | −0.456 [−0.711, −0.207] |
| Jev vs Laya multilingual | 40 | 11 | 18 / 5 | 0.0106 | 19 / 5 | 0.0066 | −0.987 [−1.341, −0.622] |
| Jev vs Laya Router | 40 | 17 | 15 / 6 | 0.0784 | 15 / 4 | 0.0192 | −0.456 [−0.711, −0.207] |

bootstrap은 항목 재표본 2,000회, seed 13, percentile이다. 주 지표(argmax)로 Jev vs english는 n=40에서 구분되지 않는다(p=0.078). 보조 지표와 MAE에서는 차이가 0을 벗어난다. 세 시스템이 모두 argmax로 틀린 행은 7개다.

### 2.3 예측 레벨 분포와 첫/마지막 레벨 선택률

| system | 규칙 | 레벨 0 | 1 | 2 | 3 | 4 | 첫 레벨 선택 | 마지막 레벨 선택 |
|---|---|---|---|---|---|---|---|---|
| gold | - | 8 | 8 | 8 | 8 | 8 | 8/40 | 8/40 |
| Jev | argmax | 4 | 13 | 6 | 12 | 5 | 4/40 | 5/40 |
| Jev | 반올림 E | 4 | 12 | 8 | 11 | 5 | 4/40 | 5/40 |
| Laya english (= Router) | argmax | 10 | 15 | 10 | 5 | 0 | 10/40 | **0/40** |
| Laya english (= Router) | 반올림 E | 6 | 18 | 12 | 4 | 0 | 6/40 | 0/40 |
| Laya multilingual | argmax | 11 | 29 | 0 | 0 | 0 | 11/40 | **0/40** |
| Laya multilingual | 반올림 E | 11 | 29 | 0 | 0 | 0 | 11/40 | 0/40 |

- **#131(multilingual 첫 레벨 회피)은 이번 T6에서 나타나지 않았다.** multilingual은 레벨 0을 11/40 골라 gold(8/40)보다 많다. 실제 실패는 반대쪽이다. 레벨 2\~4를 한 번도 고르지 않았고(0/40, gold 24/40), gold 4인 8행의 평균 E가 1.02다. 다만 SST-5의 레벨 0은 내용상 "very negative"라 위치 효과와 내용 효과가 섞여 있다. 이 표본으로 #131을 반증하지는 않는다(P0·P0b의 한국어 frustration 레벨 0 선택 0/30과는 rubric도 언어도 다르다).
- english는 마지막 레벨을 한 번도 고르지 않았다(0/40). gold 4인 8행 중 5행을 3으로, 2행을 2로, 1행(row 21 "gosling provides an amazing performance…", E 0.53)을 0으로 골랐다.
- Jev는 양 끝을 안쪽으로 당긴다. gold 0인 8행 중 4행을 1로, gold 4인 8행 중 3행을 3으로 골랐다. 그래도 평균 부호 오차는 −0.014로 치우침이 없다.

### 2.4 gold 레벨별 정답과 혼동

| gold 레벨 | n | Jev argmax 정답 (평균 E) | Laya english | Laya multilingual |
|---|---|---|---|---|
| 0 | 8 | 4 (0.47) | 6 (0.45) | 6 (0.29) |
| 1 | 8 | 6 (1.07) | 7 (0.83) | 7 (0.87) |
| 2 | 8 | 4 (1.85) | 4 (1.30) | 0 (0.58) |
| 3 | 8 | 7 (2.89) | 0 (1.58) | 0 (0.83) |
| 4 | 8 | 5 (3.65) | 0 (2.41) | 0 (1.02) |

Jev의 평균 E는 gold를 거의 따라간다(0.47 → 3.65). english는 단조롭게 오르지만 0.45 → 2.41로 압축된다. multilingual은 0.29\~1.02로 사실상 평평하다. Laya 두 체크포인트 모두 gold 3·4 16행에서 argmax 정답이 0이다.

혼동 행렬 (argmax, 행 = gold, 열 = 예측)

| gold \ pred | Jev 0 | 1 | 2 | 3 | 4 | | Laya english 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | **4** | 4 | 0 | 0 | 0 | | **6** | 2 | 0 | 0 | 0 |
| 1 | 0 | **6** | 1 | 1 | 0 | | 1 | **7** | 0 | 0 | 0 |
| 2 | 0 | 3 | **4** | 1 | 0 | | 0 | 4 | **4** | 0 | 0 |
| 3 | 0 | 0 | 1 | **7** | 0 | | 2 | 2 | 4 | **0** | 0 |
| 4 | 0 | 0 | 0 | 3 | **5** | | 1 | 0 | 2 | 5 | **0** |

- Jev 오답 14개 중 13개는 인접 레벨이다. 두 레벨 이상 틀린 것은 1개다(gold 1).
- Laya english 오답 23개 중 2레벨 이상 틀린 것은 7개다(gold 3 → 0·1 4행, gold 4 → 0·2 3행).
- english만 맞히고 Jev가 틀린 6행(c)은 1행(2레벨 차이)을 빼면 모두 한 레벨 차이이고, 그중 2행은 gold 0 → Jev 1이다.

### 2.5 확신도 (Jev 표시 top p)

| system | 100% 표시 | 평균 top p (정답 / 오답) | 오답 중 top ≥ 0.90 | gold 레벨 0% 표시 | provider confidence 평균 (정답 / 오답) |
|---|---|---|---|---|---|
| Jev | 0/40 | 0.751 (0.785 / 0.688) | 0/14 | 1/40 | 0.776 (0.812 / 0.710) |
| Laya english | - | 0.654 (0.711 / 0.612) | 0/23 | - | - |
| Laya multilingual | - | 0.824 (0.862 / 0.806) | 10/27 | - | - |

- Score에서 Jev는 100% 표시가 한 번도 없었다(choice T4 31/40, T7 27/40와 대조된다). provider confidence는 top p와 같은 값이 6/40뿐이라 별도 통계다(범위 0.37\~0.99).
- multilingual은 오답 27개 중 10개를 0.90 이상으로 냈다. 레벨 0·1로 몰리면서 확신은 높다.

### 2.6 맥락 (비교 불가 수치, 참고용)

| 수치 | 값 | 이번 측정과의 관계 |
|---|---|---|
| Laya SST-5 upstream (N=600, held out) | english 0.372 / MAE 0.905 / ±1 0.632, multilingual 0.282 / 1.359 / 0.450 (`laya_summary.md` §3, research/results/t4_colab_benchmark.json) | 이번 english 0.425의 CI [0.285, 0.578]와 multilingual 0.325의 CI [0.201, 0.480]가 각각 upstream 값을 포함한다. 표본이 upstream과 크게 어긋나지 않는다 |
| Jev SST-5 공개치 | 없음 | |
| 학습 믹스 | Laya: held out(README.md:1356). Jev: 알 수 없음 | |

## 3. T7 MASSIVE intent-10 (en 20 · de 20, 같은 id·gold·옵션)

### 3.1 언어별 정확도·보정

| lang | system | correct / n | accuracy [Wilson 95%] | Brier | ECE | 평균 top p |
|---|---|---|---|---|---|---|
| en | Jev | 18/20 | **0.900** [0.699, 0.972] | 0.143 | 0.092 | 0.934 |
| en | Laya english | 14/20 | 0.700 [0.481, 0.855] | 0.394 | 0.214 | 0.899 |
| en | Laya multilingual | 17/20 | 0.850 [0.640, 0.948] | 0.293 | 0.184 | 0.895 |
| en | Laya Router (20 모두 english) | 14/20 | 0.700 | 0.394 | 0.214 | 0.899 |
| de | Jev | 18/20 | **0.900** [0.699, 0.972] | 0.150 | 0.086 | 0.940 |
| de | Laya english | 7/20 | 0.350 [0.181, 0.567] | 1.046 | 0.513 | 0.848 |
| de | Laya multilingual | 8/20 | 0.400 [0.219, 0.613] | 0.890 | 0.453 | 0.797 |
| de | Laya Router (multilingual 15 / english 5) | 7/20 | 0.350 [0.181, 0.567] | 1.009 | 0.485 | 0.835 |

Laya 정확도는 `laya_summary.md` §4(en .70 / .85 / .70, de .35 / .40 / .35)와 같다. Brier는 행마다 그 행의 옵션 10개로 계산했다(S3 수정).

### 3.2 일치와 exact McNemar

| lang | pair | 같은 라벨 | b | c | p |
|---|---|---|---|---|---|
| en | Jev vs Laya english | 14 | 4 | 0 | 0.1250 |
| en | Jev vs Laya multilingual | 15 | 3 | 2 | 1.0000 |
| en | Jev vs Laya Router | 14 | 4 | 0 | 0.1250 |
| de | Jev vs Laya english | 8 | 11 | 0 | **0.0010** |
| de | Jev vs Laya multilingual | 7 | 11 | 1 | **0.0063** |
| de | Jev vs Laya Router | 6 | 12 | 1 | **0.0034** |

### 3.3 en + de 합산 (40)

| system | correct / 40 | accuracy [Wilson 95%] | Brier | ECE | b / c vs Jev | McNemar p |
|---|---|---|---|---|---|---|
| Jev | 36 | 0.900 [0.769, 0.960] | 0.147 | 0.088 | - | - |
| Laya english | 21 | 0.525 [0.375, 0.671] | 0.720 | 0.363 | 15 / 0 | 0.0001 |
| Laya multilingual | 25 | 0.625 [0.470, 0.758] | 0.592 | 0.250 | 14 / 3 | 0.0127 |
| Laya Router | 21 | 0.525 [0.375, 0.671] | 0.701 | 0.350 | 16 / 1 | 0.0003 |

합산 40은 같은 20개 id가 두 번 들어가 독립 표본이 아니다. McNemar p는 행 독립을 가정하므로 낙관적이다. 언어 차이의 방향을 요약하는 용도로만 쓴다.

### 3.4 언어 간 일관성 (같은 id, en vs de)

| system | 두 언어 같은 라벨 | 둘 다 정답 | en만 정답 | de만 정답 | 둘 다 오답 |
|---|---|---|---|---|---|
| Jev | 19/20 | 18 | 0 | 0 | 2 |
| Laya english | 10/20 | 7 | 7 | 0 | 6 |
| Laya multilingual | 7/20 | 7 | 10 | 1 | 2 |
| Laya Router | 6/20 | 5 | 9 | 2 | 4 |

Jev는 en과 de에서 같은 두 id를 틀리고 나머지 18 id를 모두 맞혔다. 출력 토큰도 19/20 id에서 en과 de가 같다. Laya multilingual은 en에서 맞힌 17 id 중 10개를 de에서 틀렸다.

### 3.5 확신도

| lang | system | 100% 표시 | 평균 top (정답 / 오답) | 오답 중 top ≥ 0.90 | 정답 옵션 0% 표시 | provider confidence (정답 / 오답) |
|---|---|---|---|---|---|---|
| en | Jev | 15/20 | 0.968 / 0.635 | 1/2 | 0 | 0.964 / 0.585 |
| de | Jev | 12/20 | 0.971 / 0.665 | 1/2 | 0 | 0.968 / 0.630 |
| en | Laya english / multilingual | - | 0.981 / 0.707, 0.911 / 0.806 | 1/6, 2/3 | - | - |
| de | Laya english / multilingual | - | 0.958 / 0.788, 0.927 / 0.711 | 6/13, 5/12 | - | - |

de에서 Laya는 오답의 절반 가까이를 0.90 이상으로 냈다(english 6/13, multilingual 5/12, Router 7/13). Jev는 0% 칸이 328/400으로 많지만 정답 옵션이 0%로 표시된 행은 없다.

### 3.6 Jev 오답 (4 = 2 id × 2 언어)

| row (id) | utterance (en / de) | gold | Jev en / de (top) | Laya english en / de | Laya multilingual en / de |
|---|---|---|---|---|---|
| — | — | — | — | — | — |
| — | — | — | — | — | — |

두 id 모두 MASSIVE 라벨이 발화만으로 정해지기 어려운 경우다. 이 판단은 발화를 읽고 내린 해석이고 채점은 데이터셋 라벨 그대로 했다. 두 언어 모두 Jev는 두 id 중 하나를 0.40 미만으로 낮게, 다른 하나를 0.90 이상으로 냈다.

### 3.7 맥락

| 수치 | 값 | 비고 |
|---|---|---|
| Laya MASSIVE upstream (20옵션) | en english 0.820 / multilingual 0.710, de 0.420 / 0.500 (CPU sweep, `laya_summary.md` §4) | 옵션 수가 달라(10 vs 20) 방향만 본다. de에서 Laya가 크게 떨어지는 방향은 upstream과 같다 |
| Jev MASSIVE 공개치 | 없음 | |
| 학습 믹스 | unknown(04 §1 규칙). upstream은 MASSIVE 미학습으로 표기 | |

## 4. 지연·토큰

| 구분 | runs | 표시 "server + network" ms median / min / max | 브라우저 POST ms median / min / max | 클릭 → 완료 ms median | POST − latencyMs median | 입력 토큰 median (min\~max) | 출력 토큰 median (min\~max) |
|---|---|---|---|---|---|---|---|
| Part A T6 (Score) | 40 | 236 / 172 / 348 | 477.5 / 393 / 1342 | 479 | 233.9 | 365.5 (349\~391) | 17 (17\~17) |
| Part B T7 en (choice 10) | 20 | 220.5 / 175 / 253 | 451 / 403 / 523 | 452.5 | 227.7 | 536.5 (510\~566) | 150.5 (136\~172) |
| Part C T7 de (choice 10) | 20 | 230.5 / 195 / 310 | 460 / 411 / 613 | 461.5 | 227.7 | 536.5 (517\~569) | 150.5 (136\~172) |
| S4 전체 | 80 | 227 / 172 / 348 | 461.5 / 393 / 1342 | | 230.1 | | |

- 토큰 합계는 입력 36,289, 출력 6,798이다(A 14,636 / 680, B 10,796 / 3,058, C 10,857 / 3,060).
- Score 출력은 17 토큰으로 일정했다(Boolean 20, S3). T7 출력 토큰은 행의 옵션 문자열 길이와 r = 0.55\~0.56이다. 출력이 옵션별 확률을 나열하는 구조라는 S3의 추정과 맞는 방향이다(확인 필요).
- T6의 한 run에서 브라우저 POST가 1,342 ms(최대)였다. 같은 run의 `latencyMs`는 표시 지연 범위 안이라 차이는 네트워크 쪽이다. 오류는 아니다.
- 표시 지연은 S1 T2 234 ms, S3 T4 227.5 ms와 같은 수준이다. Laya 로컬 참조(P2 laya-serve 왕복 20.1 ms, D1 english CPU 1문항 86.6 ms)는 하드웨어와 경로가 달라 모델 속도 비교가 아니다.

## 5. 관찰과 한계

**핵심 관찰 3개**
1. **SST-5의 차이는 정확한 레벨 적중보다 척도 사용에서 크다.** argmax 정확도 차이(0.650 vs 0.425)는 n=40에서 경계선(p=0.078)이다. 그러나 MAE(0.432 vs 0.888, 차이 CI가 0 배제), ±1 이내(0.875 vs 0.650), 부호 오차(−0.014 vs −0.687)에서는 차이가 분명하다. Laya english는 gold 3·4 16행에서 argmax 정답이 0이고 레벨 4를 한 번도 고르지 않았다. multilingual은 40행 모두 레벨 0·1이다. Jev는 5레벨을 모두 쓰고 E[level]이 gold를 따라간다.
2. **Score에서는 표시 규칙(반올림 E)과 argmax가 거의 같아 비교 규칙 선택이 결론을 바꾸지 않는다.** Jev는 2/40, english 6/40, multilingual 0/40 행에서 두 규칙이 갈렸다. 정답 수 변화는 ±1이다. 다만 McNemar p는 규칙에 따라 0.078 ↔ 0.019로 움직인다. 그래서 주 지표를 argmax로 고정한 사전 규칙(docs/09 §2)을 그대로 따르고, 반올림 E는 보조로만 보고한다.
3. **Jev는 en과 de에서 같은 결정을 내렸고, Laya는 언어를 바꾸면 무너졌다.** 같은 id·같은 영어 옵션에서 Jev의 라벨은 19/20 id가 en과 de에서 같고 정확도도 0.900으로 같다. Laya는 en에서 Jev와 구분되지 않지만(b/c 4/0, 3/2) de에서는 english 0.35, multilingual 0.40, Router 0.35로 떨어진다(b/c 11/0, 11/1, 12/1). multilingual 체크포인트도 de에서 english와 비슷하게 떨어지고, Router가 de 15행을 multilingual로 보낸 결과(0.35)도 english와 같다. 언어당 20행이라 크기는 방향 신호로만 읽는다.

**한계**
- 플레이그라운드 경유이며 API가 아니다. 모델 버전이 표기되지 않고 프롬프트 래핑을 알 수 없다. T6 n=40은 95% CI 폭이 약 ±0.15이고 T7은 언어당 n=20이다.
- Jev 확률·score는 2자리 반올림이다. T6 E[level]의 반올림 오차는 최대 0.005이고, Σ k·p_k(반올림 확률)와 `score`의 차이는 최대 0.020이다.
- en+de 합산 McNemar는 같은 id 쌍을 독립으로 센다(§3.3).
- T6 레벨 0의 의미("very negative")와 위치(첫 레벨)가 겹쳐 #131의 위치 효과를 분리할 수 없다. 레벨 순서를 뒤집은 변형은 이번 범위가 아니다.
- T7 Jev 오답 2 id와 T6 2레벨 오답 1행의 해석(라벨 경계, 혼합 감정)은 문장을 읽고 내린 판단이다.

## 6. 운영 기록과 이상

- 사이트 상태: 14:15:58 페이지 로드, 계측 설치 시 body 제한 문구 검사 결과 없음. UI는 S3와 같았다(Single question 기본, Decision type group, Score 선택 시 "ORDERED SCALE", "Rubric / Lowest → highest", Rubric level 0\~4 textbox). 예산 때문에 기본 예시는 실행하지 않았다.
- 네트워크 목록: POST 80(모두 `/api/evaluate`, 200), GET 77(문서 1, 정적 40, Next.js RSC prefetch 36, 모두 200). 콘솔: 경고 198건(CSS preload), 오류 0건.
- 호스트 wall clock: wall − mono 오프셋이 0 ms에서 +14 ms까지 서서히 늘었고, run 77과 78 사이에 −52 ms 스텝(+14 → −38 ms)이 한 번 있었다. 간격 가드와 dump 매칭은 모두 monotonic 축이라 영향이 없다(S2 run 60/61의 +1.98 s 스텝과 같은 종류, 크기는 작다).
- 요청 없는 클릭: Run 클릭은 80회뿐이다. 무클릭 dry run 3회와 View details 펼치기 6회(스크린샷용, Run 버튼 아님)는 요청을 만들지 않았다(resource timing `/api/evaluate` 80건 = 클릭 80회).

## 7. 파일

| 파일 | 내용 |
|---|---|
| `results/F/jev_cmp/sessions/S4_20261007/S4_requests.jsonl`(공개 저장소에는 포함하지 않음) | 80줄(run = item, 재시도 없음). T6 decision은 `score`(E[level]), `probs`(레벨별), `pred`(argmax), `top_p`, `expected_level`, `shown`(표시 레벨 문구), `shown_score`("x.xx / 4") |
| `results/F/jev_cmp/jev_runs_all.jsonl`(공개 저장소에는 포함하지 않음) | master, 311줄(S1 41 + S1b 30 + S2 80 + S3 80 + S4 80). 앞 231줄은 S4 전 사본과 바이트 동일, 뒤 80줄은 `S4_requests.jsonl`과 동일 |
| `raw/rNN_<T6|T7en|T7de>_rowRR.json`(공개 저장소에는 포함하지 않음) | 요청별 dump 80개 |
| `raw/run_plan.json`, `raw/js/`(공개 저장소에는 포함하지 않음) | 항목 계획 80, 계측 `instrument.js`(S3와 같고 버전 태그만 S4), 항목별 입력 스크립트 `i01~i80`, 무클릭 dry run `dry_i01_T6_row00.js`, `dry_i41_T7en_row00.js`, `dry_i61_T7de_row00.js` |
| `raw/evaluate_timing_all.json`, `raw/network_requests.txt`, `raw/network_requests_all.txt`, `raw/console.log`, `raw/mcp/`(다섯 항목 모두 공개 저장소에는 포함하지 않음) | `/api/evaluate` resource timing 80건과 클릭 시각(monotonic·wall), 네트워크 목록, 콘솔, MCP snapshot(페이지 로드, dry run 폼)과 MCP 콘솔 로그 |
| `shots/`(공개 저장소에는 포함하지 않음) | `S4_A_item01_run01_T6_row00.png`, `S4_A_item40_run40_T6_row39.png`, `S4_B_item41_run41_T7en_row00.png`, `S4_B_item60_run60_T7en_row19.png`, `S4_C_item61_run61_T7de_row00.png`, `S4_C_item80_run80_T7de_row19.png`(View details 열림, full page) |
| `s4_prep.py`, `s4_record.py` | 계획·입력 스크립트 생성(Laya `render_options` 일치, en·de id·옵션 동일성 assert), 기록 래퍼(S3와 같은 중단 조건 분류와 stale dump 거부) |
| `results/F/jev_cmp/jev_cmp.py` | `parse_single_display` SCORE 머리글, `analyze`의 score 분기(`score_lines`), 콤마로 묶은 세트 합산과 언어 간 일관성(`crosslang_lines`), Router answered-by. 상세는 run card |
| 재현 | `.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S4 T6_sst5_40`, `… analyze S4 T7_massive_intent_10opt_en_20`, `… analyze S4 T7_massive_intent_10opt_de_20`, `… analyze S4 T7_massive_intent_10opt_en_20,T7_massive_intent_10opt_de_20` |

[English](S4_summary.md) | **한국어**
