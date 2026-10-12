# S5 요약: T7 MASSIVE intent-10 ja · zh-CN · ko 각 20 (+ en · de 포함 5개 언어 종합) + T8 prompt-injections 40 (2026-10-07)

**판정.**
1. **T7 ja · zh-CN · ko에서 Jev는 en · de와 같은 수준을 유지했고, Laya는 언어마다 크게 흔들렸다.** Jev는 ja 19/20(0.950), zh-CN 18/20(0.900), ko 18/20(0.900)이다. Laya english는 0.450 / 0.450 / 0.100, multilingual은 0.800 / 0.600 / 0.450이다. Router는 세 언어 60행을 모두 multilingual로 보내 multilingual과 같다. exact McNemar(b/c)는 Jev vs english가 10/0 p=0.002, 9/0 p=0.004, 17/1 p=0.0001이다. Jev vs multilingual은 3/0 p=0.25, 8/2 p=0.11, 11/2 p=0.023이라 ko에서만 0.05 아래다.
2. **5개 언어 종합(같은 20 id × en · de · ja · zh-CN · ko).** Jev 정확도는 0.900 / 0.900 / 0.950 / 0.900 / 0.900(합산 91/100)이고, en 대비 언어 페널티는 0 / +0.05 / 0 / 0(평균 +0.012)이다. Laya의 평균 페널티는 english −0.362(ko −0.600), multilingual −0.287(de −0.450, ko −0.400, ja −0.050), Router −0.150이다. 같은 id에 다섯 언어 모두 같은 라벨을 낸 비율은 Jev 18/20(언어쌍 평균 일치 0.935), multilingual 5/20(0.545), english 0/20(0.325)이다. Jev 오답 9개는 한 id × 5개 언어(모두 같은 오답), 한 id × 3(en · de · ko), 한 id × 1(zh-CN)이다(Jev의 항목별 출력은 공개 저장소에서 생략). 언어당 n=20이고 같은 id가 반복되므로 언어별 크기는 방향 신호이고 합산 p값은 낙관적이다.
3. **T8 prompt-injections에서 0.5 기준 정확도는 Jev와 Laya english가 같고(0.775, b/c 5/5 p=1.0), 순위 품질은 Jev가 높다.** Jev p(true)의 AUROC는 1.000(이 40행에서 완전 분리: 정상 20행 모두 0.01\~0.04, 주입 20행 모두 0.08 이상)이다. 완전 분리라 percentile bootstrap CI가 [1.000, 1.000]으로 퇴화해 불확실성을 나타내지 못한다. english 0.929 [0.840, 0.997], multilingual 0.781, Router 0.868이고, AUROC 차이 CI는 세 쌍 모두 0을 제외한다(+0.071 [+0.003, +0.160], +0.219, +0.132). Jev와 english는 둘 다 예측 양성 11/40(gold 20/40)이고 오답 9개가 모두 미탐(FN)이다. 같은 40행에서 고른 임계값 0.05\~0.08이면 Jev가 40/40이 되지만 기술통계일 뿐이다. Laya english 0.775 [0.625, 0.877]는 upstream 0.698(held out, n=116)을 CI 안에 포함한다.
4. **운영:** 요청 100회(A 20 + B 20 + C 20 + D 40)가 모두 HTTP 200이었다. 5xx · 4xx(429 포함) · 제한 문구 · captcha · 오류 화면은 0건이고 재시도도 없었다. 간격은 monotonic 기준 최소 15.016 s, 중앙 15.114 s다. 오늘 누적은 S2\~S4 240 + S5 100 = 340회이고, 340번째 요청(15:18:41)까지 제한 신호가 없었다.

플레이그라운드 경유이며 API가 아니다. 모델 버전은 표기되지 않았다(`typesafe-ai/jev` 100/100). T7은 언어당 n=20, T8은 n=40이다. Jev 확률은 소수 둘째 자리 반올림이다. T7은 학습 믹스 unknown, T8은 Laya held out이고 Jev 학습 데이터는 알 수 없다.

## 1. 실행 개요

| 항목 | 값 |
|---|---|
| 요청 | `POST /api/evaluate` 100회 = Part A(T7 ja) 20 + Part B(T7 zh-CN) 20 + Part C(T7 ko) 20 + Part D(T8) 40, 모두 HTTP 200. 계획 100, 세션 상한 110(재시도 여유). 계측 `ready()`가 Run 클릭 110회 이상이면 클릭하지 않도록 막았다(`raw/js/instrument.js`, 공개 저장소에는 포함하지 않음) |
| 중단 조건 | 5xx 0, 4xx 0(429 0), 제한 문구 0, captcha 0, 오류 화면 0. 매 run마다 결과 패널 · status · title · `[role=alert]` · body 텍스트를 제한 문구 정규식으로 검사했고 captcha iframe도 확인했다(`s5_record.py`, dump `page`). 100회 모두 `body_stop_match` null, alerts [], captcha_frames []. 입력 문자열(T8 주입 문장 포함) 중 이 정규식에 걸리는 것은 실행 전 0건으로 확인했다 |
| 간격 (Run 클릭 사이) | 가드 15 s(규칙 ≥ 10 s, S3 · S4와 같다), 처음부터 monotonic 기준. 99개 간격: 최소 15.016 s, 중앙 15.114 s, 최대 27.234 s(run 61: Part D 무클릭 dry run · 폼 snapshot · run 60 스크린샷 뒤). resource timing 시작 간격도 15.017 / 15.115 / 27.234 s |
| 입력 동일성 | 요청 전: 폼 값으로 만든 payload sha12가 폼 파일 기대값과 100/100 일치(`window.__jev.ready`). 요청 후: 캡처한 request body가 `jev_cmp.py` payload와 바이트 단위로 100/100 같다(`payload_exact`). 무클릭 dry run 4회(item 1, 21, 41, 61) |
| 입력 내용 | T7: Single / Choice, 옵션 10개 `key: key spaced`(최대 50자) 폼 순서. ja · zh-CN · ko 각 행의 MASSIVE id · gold · 옵션 목록 · 질문이 S4에서 보낸 en 행과 같다(`s5_prep.py` assert). T8: Single / Boolean, 질문 문장만(Laya noul에도 criteria 없음, Boolean 폼에는 라벨 · 설명 칸이 없다: `raw/mcp/snapshot_dry_i061_T8_row00_form.yml`, 공개 저장소에는 포함하지 않음). State는 모두 Laya가 읽는 문자열 `json.dumps(state, ensure_ascii=False)`(`laya/common.py` `serialize_state`)이고, 실행 전에 100행 모두 `state_text`와 같고 `\u` 이스케이프가 없음을 확인했다. 비ASCII 문자를 포함한 state: T7 60/60, T8 13/40(독일어 등) |
| 화면 = 응답 | 100/100(DECISION, 막대 %). 표시 지연 = `latencyMs` half-up 100/100 |
| Model ID / 응답 메타 | `model`과 View details 모두 `typesafe-ai/jev` 100/100. `rounding` {2, 2}, `warnings` [] 100/100. provider `confidence.decision`은 T7 60/60에 있고 T8 Boolean 40에는 없다(S3 T5와 같다) |

## 2. T7 ja · zh-CN · ko (언어별 20행, 같은 id · gold · 옵션)

### 2.1 정확도 · 보정

| lang | system | correct / n | accuracy [Wilson 95%] | Brier | ECE | 평균 top p |
|---|---|---|---|---|---|---|
| ja | Jev | 19/20 | **0.950** [0.764, 0.991] | 0.063 | 0.052 | 0.976 |
| ja | Laya english | 9/20 | 0.450 [0.258, 0.658] | 0.681 | 0.351 | 0.678 |
| ja | Laya multilingual (= Router, 20 모두 multilingual) | 16/20 | 0.800 [0.584, 0.919] | 0.289 | 0.199 | 0.870 |
| zh-CN | Jev | 18/20 | **0.900** [0.699, 0.972] | 0.194 | 0.133 | 0.950 |
| zh-CN | Laya english | 9/20 | 0.450 [0.258, 0.658] | 0.886 | 0.414 | 0.864 |
| zh-CN | Laya multilingual (= Router, 20 모두 multilingual) | 12/20 | 0.600 [0.387, 0.781] | 0.642 | 0.319 | 0.781 |
| ko | Jev | 18/20 | **0.900** [0.699, 0.972] | 0.151 | 0.086 | 0.936 |
| ko | Laya english | 2/20 | 0.100 [0.028, 0.301] | 1.164 | 0.435 | 0.535 |
| ko | Laya multilingual (= Router, 20 모두 multilingual) | 9/20 | 0.450 [0.258, 0.658] | 0.808 | 0.365 | 0.815 |

Brier는 행마다 그 행의 옵션 10개로 Σ(p − onehot)²를 계산했다. ECE는 15 bins, top p 기준이다. Laya 값은 `laya_summary.md` §1 · §4(ja .45 / .80, zh-CN .45 / .60, ko .10 / .45)와 같다.

### 2.2 일치와 exact McNemar (b = Jev만 정답, c = Laya만 정답)

| lang | pair | 같은 라벨 | b | c | p |
|---|---|---|---|---|---|
| ja | Jev vs Laya english | 9 | 10 | 0 | **0.0020** |
| ja | Jev vs Laya multilingual (= Router) | 16 | 3 | 0 | 0.2500 |
| zh-CN | Jev vs Laya english | 10 | 9 | 0 | **0.0039** |
| zh-CN | Jev vs Laya multilingual (= Router) | 10 | 8 | 2 | 0.1094 |
| ko | Jev vs Laya english | 2 | 17 | 1 | **0.0001** |
| ko | Jev vs Laya multilingual (= Router) | 7 | 11 | 2 | **0.0225** |

### 2.3 확신도

| lang | system | 100% 표시 | 평균 top (정답 / 오답) | 오답 중 top ≥ 0.90 | 정답 옵션 0% 표시 | provider confidence (정답 / 오답) |
|---|---|---|---|---|---|---|
| ja | Jev | 14/20 | 0.986 / 0.780 | 0/1 | 0 | 0.984 / 0.750 |
| zh-CN | Jev | 14/20 | 0.953 / 0.915 | 2/2 | 0 | 0.948 / 0.900 |
| ko | Jev | 14/20 | 0.968 / 0.650 | 1/2 | 0 | 0.964 / 0.610 |
| ja | Laya english / multilingual | - | 0.851 / 0.537, 0.917 / 0.680 | 1/11, 1/4 | - | - |
| zh-CN | Laya english / multilingual | - | 0.977 / 0.772, 0.857 / 0.669 | 5/11, 3/8 | - | - |
| ko | Laya english / multilingual | - | 0.672 / 0.519, 0.940 / 0.713 | 1/18, 3/11 | - | - |

Jev는 세 언어 모두 0% 칸이 많지만(163\~167/200) 정답 옵션이 0%로 표시된 행은 없다. zh-CN 오답 2개는 모두 0.90 이상이다. Laya english는 zh-CN 오답 11개 중 5개를 0.90 이상으로 냈다.

### 2.4 Jev 오답 (5 = ja 1 + zh-CN 2 + ko 2)

| lang | row (id) | utterance | gold | Jev (top) | Laya english / multilingual |
|---|---|---|---|---|---|
| — | — | — | — | — | — |
| — | — | — | — | — | — |
| — | — | — | — | — | — |
| — | — | — | — | — | — |
| — | — | — | — | — | — |

- 1개 id는 다섯 언어 모두에서 틀렸다(S4 en · de와 같은 오답). 다른 id 하나는 S4 en · de와 ko에서 틀렸고, 번역문의 내용이 다른 ja · zh-CN에서는 맞혔다.
- zh-CN에서만 틀린 id는 다른 언어와 달리 동작 동사가 번역에서 빠졌다. 이 해석(번역 차이, 라벨 경계)은 발화를 읽고 내린 판단이고 채점은 데이터셋 라벨 그대로 했다.

## 3. T7 5개 언어 종합 (S4 en · de + S5 ja · zh-CN · ko, 같은 20 id)

`.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S4,S5 T7_..._en_20,T7_..._de_20,T7_..._ja_20,T7_..._zh-CN_20,T7_..._ko_20`(출력 `raw/analyze/T7_all5_S4S5.md`, 공개 저장소에는 포함하지 않음). 같은 20 id가 다섯 번 들어가므로 합산 검정은 독립 표본이 아니다.

### 3.1 언어별 정확도

| system | en | de | ja | zh-CN | ko | 합산 (100) |
|---|---|---|---|---|---|---|
| Jev | 18/20 = 0.900 | 18/20 = 0.900 | 19/20 = 0.950 | 18/20 = 0.900 | 18/20 = 0.900 | **91/100 = 0.910** [0.838, 0.952] |
| Laya english | 14/20 = 0.700 | 7/20 = 0.350 | 9/20 = 0.450 | 9/20 = 0.450 | 2/20 = 0.100 | 41/100 = 0.410 [0.319, 0.508] |
| Laya multilingual | 17/20 = 0.850 | 8/20 = 0.400 | 16/20 = 0.800 | 12/20 = 0.600 | 9/20 = 0.450 | 62/100 = 0.620 [0.522, 0.709] |
| Laya Router | 14/20 = 0.700 (english 20) | 7/20 = 0.350 (multilingual 15 / english 5) | 16/20 = 0.800 (multilingual) | 12/20 = 0.600 (multilingual) | 9/20 = 0.450 (multilingual) | 58/100 = 0.580 [0.482, 0.672] |

### 3.2 언어 페널티 = accuracy(lang) − accuracy(en)

| system | de | ja | zh-CN | ko | 평균 |
|---|---|---|---|---|---|
| Jev | +0.000 | +0.050 | +0.000 | +0.000 | **+0.012** |
| Laya english | −0.350 | −0.250 | −0.250 | −0.600 | −0.362 |
| Laya multilingual | −0.450 | −0.050 | −0.250 | −0.400 | −0.287 |
| Laya Router | −0.350 | +0.100 | −0.100 | −0.250 | −0.150 |

Router의 ja +0.100은 en을 english로, ja를 multilingual로 보낸 결과다(multilingual en 0.850 대비로는 −0.050). 언어당 n=20이라 ±0.05는 한 행이다.

### 3.3 언어별 exact McNemar (b / c, p)

| pair | en | de | ja | zh-CN | ko | 합산 100 (독립 아님) |
|---|---|---|---|---|---|---|
| Jev vs Laya english | 4 / 0, 0.125 | 11 / 0, 0.001 | 10 / 0, 0.002 | 9 / 0, 0.004 | 17 / 1, 0.0001 | 51 / 1, 2.4e-14 |
| Jev vs Laya multilingual | 3 / 2, 1.000 | 11 / 1, 0.006 | 3 / 0, 0.250 | 8 / 2, 0.109 | 11 / 2, 0.023 | 36 / 7, 9.0e-6 |
| Jev vs Laya Router | 4 / 0, 0.125 | 12 / 1, 0.003 | 3 / 0, 0.250 | 8 / 2, 0.109 | 11 / 2, 0.023 | 38 / 5, 2.5e-7 |

Jev vs multilingual은 en · ja · zh-CN에서 구분되지 않고 de · ko에서 p < 0.05다. english와는 en을 뺀 네 언어에서 모두 p < 0.01이다.

### 3.4 언어 간 일관성 (같은 id에 같은 라벨)

| system | en과 같음: de | ja | zh-CN | ko | 5개 언어 모두 같은 라벨 | 언어쌍 평균 일치 (10쌍) | 5개 언어 모두 정답 | 5개 언어 모두 오답 |
|---|---|---|---|---|---|---|---|---|
| Jev | 19/20 | 19/20 | 18/20 | 19/20 | **18/20** | **0.935** | 17 | 1 |
| Laya english | 10/20 | 11/20 | 12/20 | 1/20 | 0/20 | 0.325 | 0 | 5 |
| Laya multilingual | 7/20 | 17/20 | 12/20 | 11/20 | 5/20 | 0.545 | 5 | 1 |
| Laya Router | 6/20 | 14/20 | 9/20 | 8/20 | 4/20 | 0.485 | 4 | 0 |

- Jev가 언어에 따라 라벨을 바꾼 id는 둘이다. 두 id 모두 번역 문장의 내용이 언어마다 다르다(§2.4).
- Jev의 T7 출력 토큰 수는 18/20 id에서 다섯 언어가 같고, 다른 두 id가 정확히 라벨이 바뀐 두 id다. 출력이 발화가 아니라 옵션과 선택 라벨에 따라 정해지는 구조라는 S3 · S4 추정과 맞는 방향이다(추정, 확인 필요).
- Laya multilingual은 en에서 맞힌 17 id 중 de에서 10개, ko에서 8개를 틀렸다. 가장 잦은 오답 라벨은 iot_hue_lightdim(38개 중 10개, lightoff → lightdim 4, lightup → lightdim 4)이다. english의 가장 잦은 오답 라벨은 general_joke(59개 중 9개)다.

### 3.5 보정과 확신도 (언어별)

| system | Brier en / de / ja / zh-CN / ko (합산) | ECE en / de / ja / zh-CN / ko (합산) |
|---|---|---|
| Jev | 0.143 / 0.150 / 0.063 / 0.194 / 0.151 (0.140) | 0.092 / 0.086 / 0.052 / 0.133 / 0.086 (0.068) |
| Laya english | 0.394 / 1.046 / 0.681 / 0.886 / 1.164 (0.834) | 0.214 / 0.513 / 0.351 / 0.414 / 0.435 (0.355) |
| Laya multilingual | 0.293 / 0.890 / 0.289 / 0.642 / 0.808 (0.584) | 0.184 / 0.453 / 0.199 / 0.319 / 0.365 (0.216) |
| Laya Router | 0.394 / 1.009 / 0.289 / 0.642 / 0.808 (0.628) | 0.214 / 0.485 / 0.199 / 0.319 / 0.365 (0.260) |

| Jev (언어별) | en | de | ja | zh-CN | ko |
|---|---|---|---|---|---|
| 100% 표시 | 15/20 | 12/20 | 14/20 | 14/20 | 14/20 |
| 평균 top (정답) | 0.968 | 0.971 | 0.986 | 0.953 | 0.968 |
| 오답 top | — | — | — | — | — |
| 정답 옵션 0% 표시 | 0 | 0 | 0 | 0 | 0 |

en · de 값은 S4(`S4_summary.md` §3.1 · §3.5)와 같은 기록에서 나왔다. Jev는 100개 중 정답 옵션을 0%로 표시한 행이 없고, 오답 9개 중 5개가 top ≥ 0.90이다.

### 3.6 맥락 (비교 불가 수치)

| 수치 | 값 | 비고 |
|---|---|---|
| Laya MASSIVE upstream (20옵션) | ja english 0.530 / multilingual 0.640, zh-CN 0.620 / 0.650, ko 0.110 / 0.470(CPU sweep, `laya_summary.md` §4). BENCHMARKS.md ko multilingual 0.470, en 0.710 / english 0.820 | 옵션 수가 달라(10 vs 20) 방향만 본다. ko에서 english가 무너지고 multilingual이 0.45 안팎인 방향은 upstream과 같다 |
| Jev MASSIVE 공개치 | 없음 | |
| 학습 믹스 | unknown(04 §1 규칙) | |

## 4. T8 prompt-injections (40행, gold true 20 / false 20)

### 4.1 정확도 · 양성률 · 순위 품질

| system | correct / n | accuracy [Wilson 95%] | 예측 true (gold 20) | Brier | ECE | 평균 top p | AUROC p(true) [bootstrap 95%] | 같은 40행 최적 임계값 정확도 (기술통계) |
|---|---|---|---|---|---|---|---|---|
| Jev (playground, 표시 p, 2자리) | 31/40 | **0.775** [0.625, 0.877] | 11 | 0.307 | 0.194 | 0.921 | **1.000** [1.000, 1.000]* | 40/40 = 1.000 (t ∈ (0.04, 0.08]) |
| Laya english | 31/40 | 0.775 [0.625, 0.877] | 11 | 0.401 | 0.223 | 0.962 | 0.929 [0.840, 0.997] | 35/40 = 0.875 |
| Laya multilingual | 23/40 | 0.575 [0.422, 0.715] | 9 | 0.692 | 0.380 | 0.940 | 0.781 [0.615, 0.919] | 31/40 = 0.775 |
| Laya Router (english 26 / multilingual 14) | 29/40 | 0.725 [0.572, 0.839] | 11 | 0.510 | 0.261 | 0.979 | 0.868 [0.738, 0.969] | 33/40 = 0.825 |

- 판정 규칙은 p(true) ≥ 0.5(laya-evals 규칙)다. Jev가 정확히 0.5를 낸 행은 없다.
- Brier는 S3와 같이 {false, true} 두 칸의 Σ(p − onehot)²(= 2(p − y)²)다. 한 칸 기준이면 절반이다. Laya 값은 `laya_summary.md` §1(0.401 / 0.692 / 0.510, ECE 0.223 / 0.380 / 0.261)과 같다.
- *Jev는 이 40행에서 완전 분리다(gold false p(true) 0.01\~0.04, gold true 0.08\~0.99). 그래서 모든 bootstrap 재표본의 AUROC가 1이 되어 percentile CI가 폭 0으로 퇴화했다. 모집단 AUROC가 1이라는 뜻이 아니다. n=40에서 완전 분리는 AUROC가 1보다 작은 모집단에서도 나올 수 있다. Jev − Laya AUROC 차이 CI도 Jev 쪽 분산이 0이라 낙관적이다.
- Jev p(true)는 서로 다른 값이 19개뿐이다(2자리 반올림). 최적 임계값 열은 같은 40행에서 고른 값이라 결론에 쓰지 않는다.

### 4.2 일치, exact McNemar, AUROC 차이

| pair | n | 같은 예측 | b | c | McNemar p | AUROC Jev − Laya [paired bootstrap 95%] |
|---|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 30 | 5 | 5 | 1.0000 | +0.071 [+0.003, +0.160] |
| Jev vs Laya multilingual | 40 | 26 | 11 | 3 | 0.0574 | +0.219 [+0.081, +0.385] |
| Jev vs Laya Router | 40 | 28 | 7 | 5 | 0.7744 | +0.132 [+0.031, +0.262] |

### 4.3 오류 구조: 미탐(FN)과 오탐(FP)

| system | FP (gold false → true) | FN (gold true → false) | 오답 중 top ≥ 0.90 | p(true) ∈ {0, 1} (100% 표시) |
|---|---|---|---|---|
| Jev | **0** | 9 | 2/9 | 0/40 |
| Laya english | 0 | 9 | 6/9 | 27/40 |
| Laya multilingual | 3 (rows 3, 17, 23) | 14 | 12/17 | 4/40 |
| Laya Router | 1 (row 17) | 10 | 10/11 | 20/40 |

Jev와 english는 둘 다 FP 0 · FN 9로 정확도가 같지만, 놓치는 주입이 다르다.

| 구분 | rows | 내용 (요약) |
|---|---|---|
| Jev만 오답 (english 정답) | — | 역할 · 작업 지시형(5개). Jev p(true) 0.17\~0.40 |
| english만 오답 (Jev 정답) | — | 명시적 무시 · 덮어쓰기(5개). 5개 중 4개는 덮어쓰기 문장이 독일어다. Jev p(true) 0.76\~0.98 |
| 세 시스템 모두 오답 | — | 역할극형(2개), 무시 지시형(1개) |

이 분류(역할 · 작업 지시형 vs 명시적 덮어쓰기)는 문장을 읽고 내린 해석이다. 채점은 deepset 라벨 그대로 했다. 질문 문구("inject or override instructions")는 두 시스템에 같다.

### 4.4 보류 임계값 (Jev top p, 같은 40행, 기술통계)

| 남기는 기준 | 남는 행 | 남은 행의 오답 |
|---|---|---|
| top ≥ 0.80 | 37/40 | 7 |
| top ≥ 0.90 | 29/40 | 2 |
| top ≥ 0.95 | 27/40 | 0 |

T5(BoolQ)에서는 top ≥ 0.80 보류가 오답 3개를 모두 걸렀다. T8에서는 미탐 9개 중 7개가 top 0.80 이상(p(true) 0.08\~0.19)이라 같은 정책이 통하지 않는다. T8의 문제는 순위가 아니라 0.5 임계값의 위치다.

### 4.5 Router 언어 배정별 (기술통계, 작은 n)

| Router 배정 | n (gold true) | Jev | Laya english | Laya multilingual | Laya Router |
|---|---|---|---|---|---|
| english | 26 (11) | 20 | 21 | 15 | 21 |
| multilingual | 14 (9) | 11 | 10 | 8 | 8 |

### 4.6 맥락

| 수치 | 값 | 비고 |
|---|---|---|
| Laya prompt-injections upstream | english 0.698 / multilingual 0.578 (README.md:1355, held out, n=116) | 이번 english 0.775 [0.625, 0.877], multilingual 0.575 [0.422, 0.715] 모두 upstream 값을 CI 안에 포함 |
| Jev prompt-injections 공개치 | 없음 | |
| 학습 믹스 | Laya: held out. Jev: 알 수 없음 | deepset/prompt-injections는 공개 데이터셋이다 |

## 5. 지연 · 토큰

| 구분 | runs | 표시 "server + network" ms median / min / max | 브라우저 POST ms median / min / max | 클릭 → 완료 ms median | POST − latencyMs median | 입력 토큰 median (min\~max), 합계 | 출력 토큰 median (min\~max), 합계 |
|---|---|---|---|---|---|---|---|
| Part A T7 ja | 20 | 224 / 191 / 438 | 455 / 414 / 667 | 456.5 | 229.4 | 540.5 (516\~574), 10,913 | 150.5 (136\~172), 3,066 |
| Part B T7 zh-CN | 20 | 227 / 190 / 368 | 465 / 417 / 1,239 | 466 | 227.6 | 538 (512\~568), 10,844 | 149.5 (136\~172), 3,063 |
| Part C T7 ko | 20 | 233.5 / 199 / 301 | 473 / 428 / 563 | 474 | 232.6 | 538 (509\~567), 10,859 | 150.5 (136\~172), 3,059 |
| Part D T8 (Boolean) | 40 | 226 / 163 / 458 | 475.5 / 408 / 688 | 477 | 230.0 | 305 (291\~419), 12,821 | 20 (20\~20), 800 |
| S5 전체 | 100 | 227 / 163 / 458 | 466.5 / 408 / 1,239 | 467.5 | 229.7 | 45,437 | 9,988 |

- T7 입력 토큰 중앙값은 en 536.5 / de 536.5 / ja 540.5 / zh-CN 538 / ko 538로 언어 차이가 작다. 입력 대부분이 질문 · 옵션 10개라서다.
- T8 입력 토큰은 state 길이와 r = 0.989다. Boolean 출력은 T5와 같이 20 토큰으로 일정하다. T7 출력 토큰은 옵션 key 길이 합과 r = 0.566(S4 0.55\~0.56과 같은 수준)이다.
- zh-CN의 한 run에서 브라우저 POST가 1,239 ms(최대)였다. 같은 run의 `latencyMs`는 표시 지연 범위 안이라 차이는 네트워크 쪽이다(S4의 같은 사례와 같은 종류). 오류는 아니다.
- 표시 지연은 S3 · S4 파트별 중앙값(200.5\~236 ms)과 같은 수준이고 Jev 제3자 p50 236\~276 ms(09 §1) 범위 안 또는 약간 아래다. Laya 로컬 지연(P2 laya-serve 왕복 20.1 ms 등)은 하드웨어와 경로가 달라 비교하지 않는다.

## 6. 관찰과 한계

**핵심 관찰 3개**
1. **Jev의 다국어 의도 분류는 언어에 거의 무관했고, Laya의 언어 페널티는 체크포인트와 언어에 따라 컸다.** 같은 20 id에서 Jev는 다섯 언어 모두 0.90\~0.95이고 18/20 id에 다섯 언어 같은 라벨을 냈다. Laya english는 ko에서 0.10까지 떨어지고(페널티 −0.60), multilingual도 de −0.45, ko −0.40이다. ja는 multilingual에 가장 덜 불리했다(−0.05). Jev가 라벨을 바꾼 두 id는 번역 문장의 내용 차이와 겹친다. 모든 언어에서 같이 틀린 1개 id는 라벨 경계 사례다(해석, §2.4).
2. **T8에서는 같은 정확도(0.775) 아래 두 시스템의 오류 구조가 다르다.** Jev는 순위가 완전하고(이 표본 AUROC 1.000) 오탐이 0이지만, 0.5 임계값에서 역할 · 작업 지시형 주입을 0.08\~0.40으로 낮게 매겨 놓친다. Laya english는 역할 지시형은 잡고 독일어로 된 명시적 덮어쓰기 4개를 놓친다. Jev는 임계값을 낮추면(같은 40행에서 0.05\~0.08) 분리가 되는 구조라 임계값 보정 문제이고, held-out 표본으로 임계값을 고정해야 쓸 수 있다.
3. **Jev Boolean 확률의 위치는 과제마다 다르다.** T5 BoolQ는 예측 양성 21/40(gold 20)로 0.5 기준이 맞았고 오답이 모두 top < 0.80이었다. T8은 예측 양성 11/40이고 미탐 9개 중 7개가 top ≥ 0.80이다. Boolean에 고정 임계값 · 보류 정책을 일괄 적용하면 안 되고 과제별 보정이 필요하다. Choice(T7)에서는 오답 9개 중 5개가 top ≥ 0.90이라 고확신 오답이 남는 S1 · S2 · S4 패턴이 그대로다.

**한계**
- 플레이그라운드 경유이며 API가 아니다. 모델 버전이 표기되지 않고 프롬프트 래핑을 알 수 없다.
- T7은 언어당 n=20(95% CI 폭 약 ±0.2)이다. 언어 페널티의 크기는 방향 신호다. 5개 언어 합산은 같은 20 id의 반복이라 합산 McNemar p는 낙관적이다.
- T8 Jev AUROC의 bootstrap CI는 완전 분리로 퇴화했다(§4.1). AUROC 차이 CI도 낙관적이다. 최적 임계값 · 보류 표는 같은 40행에서 계산한 기술통계다.
- Jev 확률은 2자리 반올림이다(T8 p(true) 서로 다른 값 19개).
- T8 정답은 deepset 라벨 정책(역할 지시형도 주입으로 표기)에 따른다. 다른 라벨 정책에서는 두 시스템의 순위가 달라질 수 있다.
- MASSIVE 번역 품질(§2.4의 zh-CN 번역 탈락 등)이 언어별 결과에 섞인다.

## 7. 운영 기록과 이상

- 사이트 상태: 14:52:50 페이지 정상 로드, 계측 설치 시 body 제한 문구 없음. UI · DOM id는 S3 · S4와 같다(Single question 기본, Decision type group, Boolean 선택 시 "YES / NO — Jev returns P(true). The probability of "No" is its complement."). 예산 때문에 기본 예시는 실행하지 않았다.
- 네트워크 목록: POST 100(모두 `/api/evaluate`, 200), GET 27(문서 1, 정적 14, Next.js RSC prefetch 12, 모두 200). resource timing `/api/evaluate` 100건 = Run 클릭 100회, 클릭 → fetch 시작 0\~5 ms.
- 콘솔: 경고 206건(MCP 로그, 모두 CSS preload), 오류 0건. `browser_console_messages` 덤프(`raw/console.log`)는 186건(경고만)으로 MCP 버퍼 기준이다.
- 호스트 wall clock: wall − mono 오프셋이 −3 \~ +20 ms 범위였고 run 75 → 76(+5 ms), 76 → 77(+10 ms)에 작은 스텝이 있었다. 간격 가드와 dump 매칭은 monotonic 축이라 영향이 없다.
- 요청 없는 클릭: Run 클릭은 100회뿐이다. 무클릭 dry run 4회는 폼 입력과 해시 대조만 했다. 스크린샷용 View details는 클릭 없이 DOM에서 `details.open = true`로 열었다(S4는 클릭). 
- 간격 최대 27.2 s(run 61)는 Part D 준비(dry run, 폼 snapshot, run 60 스크린샷) 시간이고, 파트 경계 run 21 · 41은 19.6 s · 18.6 s, run 2는 20.9 s(run 1 스크린샷)였다.

## 8. 파일

| 파일 | 내용 |
|---|---|
| `results/F/jev_cmp/sessions/S5_20261007/S5_requests.jsonl`(공개 저장소에는 포함하지 않음) | 100줄(run = item, 재시도 없음). choice는 `pred` · `probs` · `top_p` · `shown_pct`, Boolean은 `p_true` · `pred`, run별 `latency_ms_response` · `displayed_ms` · `fetch_dur_ms` · `click_to_complete_ms` · `usage` · `confidence` · `model_id_details`. `click_epoch_ms`는 monotonic 축 |
| `results/F/jev_cmp/jev_runs_all.jsonl`(공개 저장소에는 포함하지 않음) | master 411줄. 앞 311줄은 S5 전 사본과 바이트 동일, 뒤 100줄은 `S5_requests.jsonl`과 동일 |
| `raw/rNNN_<T7ja|T7zh|T7ko|T8>_rowRR.json`(공개 저장소에는 포함하지 않음) | 요청별 dump 100개 |
| `raw/run_plan.json`, `raw/js/`(공개 저장소에는 포함하지 않음) | 항목 계획 100, 계측 `instrument.js`(S4 레시피 + 버전 태그 S5 + 세션 상한 110 검사), 항목별 입력 스크립트 `i001~i100`, 무클릭 dry run `dry_i001_T7ja_row00.js` · `dry_i021_T7zh_row00.js` · `dry_i041_T7ko_row00.js` · `dry_i061_T8_row00.js` |
| `raw/evaluate_timing_all.json`, `raw/network_requests.txt`, `raw/network_requests_all.txt`, `raw/console.log`, `raw/mcp/`(다섯 항목 모두 공개 저장소에는 포함하지 않음) | resource timing 100건과 클릭 시각(monotonic · wall), 네트워크 목록, 콘솔, MCP snapshot(페이지 로드, dry run 폼 2개)과 MCP 콘솔 로그 |
| `raw/analyze/`(공개 저장소에는 포함하지 않음) | `T7_ja.md`, `T7_zh-CN.md`, `T7_ko.md`, `T8.md`(`analyze S5 <SET>` 출력), `T7_all5_S4S5.md`(`analyze S4,S5` 5개 언어 출력) |
| `shots/`(공개 저장소에는 포함하지 않음) | 파트별 첫 · 마지막 run 8장(View details 열림, full page): `S5_A_item001_run001_T7ja_row00.png`, `S5_A_item020_run020_T7ja_row19.png`, `S5_B_item021_run021_T7zh_row00.png`, `S5_B_item040_run040_T7zh_row19.png`, `S5_C_item041_run041_T7ko_row00.png`, `S5_C_item060_run060_T7ko_row19.png`, `S5_D_item061_run061_T8_row00.png`, `S5_D_item100_run100_T8_row39.png` |
| `s5_prep.py`, `s5_record.py` | 계획 · 입력 스크립트 생성(Laya `serialize_state` · `render_options` 일치, en 행과 id · gold · 옵션 동일, T8 noul criteria 없음 assert), 기록 래퍼(S4와 같은 중단 조건 분류, stale dump 거부, 3자리 run 번호) |
| `results/F/jev_cmp/jev_cmp.py` | `analyze`가 콤마로 묶은 세션을 함께 읽고, 세 세트 이상이면 `crosslang_multi`(언어별 정확도, en 대비 페널티, 언어별 McNemar, 언어 간 일관성, id별 패턴)를 낸다. 상세는 run card |
| 재현 | `.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S5 T7_massive_intent_10opt_ja_20`(zh-CN, ko 동일), `… analyze S5 T8_prompt_injections_40`, `… analyze S4,S5 T7_massive_intent_10opt_en_20,T7_massive_intent_10opt_de_20,T7_massive_intent_10opt_ja_20,T7_massive_intent_10opt_zh-CN_20,T7_massive_intent_10opt_ko_20` |

[English](S5_summary.md) | **한국어**
