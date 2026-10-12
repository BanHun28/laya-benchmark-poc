# Jev playground 수동 head-to-head: 한국어 domain routing 24행 (2026-10-06)

**판정.** 같은 24개 한국어 라우팅 항목에서 Jev는 Laya zero-shot을 이기고, ft-v1은 이기지 못한다. n = 24 단일 패스라 둘 다 indicative 수준이다.

- Jev 20/24 = 0.833 vs zero-shot 10/24 = 0.417. b = 10, c = 0, exact McNemar p = 0.002.
- ft-v1 22/24 = 0.917 vs Jev. b = 0, c = 2, p = 0.5. 차이는 유의하지 않지만 방향은 ft-v1 쪽이고, Jev가 맞힌 행은 ft-v1도 모두 맞혔다.

| 항목 | 값 |
|---|---|
| 정확도 (Wilson 95%) | Jev 20/24 = 0.833 [0.641, 0.933], Laya zero-shot 10/24 = 0.417 [0.245, 0.612], Laya ft-v1 22/24 = 0.917 [0.742, 0.977] |
| 사이트로 보낸 Jev 실행 | `POST /api/evaluate` 25회. 1차 세션 2회(200 1, 502 1), 2차 세션 23회(모두 200) |
| 2차 세션 예산 | 46회 중 23회 사용 |
| 재시도 | 60 s 재시도 규칙 발동 0회. row 37은 1차 세션의 502 뒤 재개하면서 다시 실행했다(attempt 2) |
| pacing | 같은 페이지 로드 안의 클릭 간격 최소 21.6 s(규칙 ≥ 3 s) |
| pass 2 (key-only 라벨) | 생략(재개 시 결정, 옵션 c) |
| 브라우저 세션 (KST) | 1차 08:07:14\~08:13(run 2에서 502로 중단). 2차 08:24:18\~08:34(run 2\~24) |

## 1. 방법

### 1.1 표본 (모델 실행 없음, `results/F/jev_f.py sample`)

- 원본: `data/evals/ko_massive_domain_8.jsonl` 500행. dataset_sha256 `edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b`, questions_sha256 `a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54`.
- test 절반: `results/B/B_splits.json`의 index parity 규칙(데이터 행 index가 홀수면 test. `scripts/metrics_extra.py` `row_splits`)으로 250행.
- train 중복 제외: utterance가 `poc/finetune/data/domain8_train.jsonl`(11,094행)에 그대로 있는 16행을 뺐다. 남은 것은 234행이다. P4 문서에 기록된 test 중복 16행과 일치한다.
- 선택 규칙(해석을 명시한다): 후보를 행 index 오름차순으로 정렬한다. 도메인을 schema 순서(productivity, media, smart_home, info_qa, communication, lifestyle, transport, general)로 돌면서 `random.Random(13)` 인스턴스 하나로 `rng.sample(후보, 3)`을 뽑는다. 뽑힌 24행은 행 index 순으로 정렬해 실행 순서로 쓴다. 도메인별 후보 수는 28/24/30/28/32/33/27/32이다.
- Laya 예측: zero-shot은 `results/B/20261002-1643_multilingual_ko_massive_domain_8.json`, ft-v1은 `results/P4/full_20261003-1156_ft-v1_ko_massive_domain_8.json`의 `cases[row_index]`에서 읽었다. p는 `answer.answer_confidence`이다. 두 리포트 모두 dataset_sha256이 같은지, case와 row가 expected·tags 기준으로 정렬되는지 assert한다.
- 대표성: 24행에서 zero-shot 0.417 / ft-v1 0.917이다. clean test 234행에서는 0.496 / 0.893이고, 도메인을 균등 가중하면 0.491 / 0.898이다. 표본은 도메인 균등(도메인당 3행)이다.

### 1.2 Jev 프로토콜 (Laya가 받은 것과 같은 정보)

- https://jevplayground.com/ , "Single question", Decision type "Choice".
- State: 원문 한국어 utterance 그대로.
- Question: `Which domain should handle this request?`. Laya의 instructions는 ``Which domain should handle the request in `utterance`?``이다. Jev의 state는 dict가 아니라 원문이어서 문구가 조금 다르다.
- Choices: 8개를 schema 순서로 고정했다. 각 항목은 `key: 한국어 설명`이고 문자열은 `poc/schema/router_v1.json` criteria에서 그대로 가져왔다. 두 세션 모두 "+ Add choice"를 4번 눌러 카운터가 "8 of 10"인 것을 확인했다. choice 입력의 maxlength는 80자이고 가장 긴 라벨은 43자다.
- 오류 규칙:
  - 1차 세션: 오류가 나면 즉시 중단.
  - 2차 세션(재개 시 결정): 5xx 또는 "temporarily unavailable"이면 60 s 뒤 그 행만 1회 재시도하고, 재시도도 실패하면 중단한다. 429·rate-limit 문구·captcha는 즉시 중단한다. 실패 요청도 요청 수에 넣는다.

### 1.3 계측과 검증 (사이트 요청을 늘리지 않는 read-only 장치)

- Run 전 precheck: 브라우저에서 State·Question·Choices 값의 SHA-256을 계산해 Python이 표본 파일에서 계산한 값과 비교한다. 카운터 "8 of 10"과 "Single question"·"Choice" pressed 상태도 확인한다. 25회 모두 통과한 뒤에 Run을 눌렀다.
- 페이지에 passive listener를 두었다. capture 단계 click listener가 Run 클릭 시각을, MutationObserver가 status 텍스트 변화를 기록한다. 그래서 읽은 결과가 마지막 클릭 이후의 최종 상태("Evaluation complete" 또는 오류)임을 확인할 수 있다. State를 편집하면 결과 패널이 초기화되므로 이전 결과를 다시 읽을 위험도 없다.
- 결과 읽기: 결과 region의 DOM을 `results/F/jev_raw/p1_NN.json`(공개 저장소에는 포함하지 않음)에 저장한다. 여기에는 innerText, 접힌 "View details" JSON, form 값, PerformanceResourceTiming의 POST 상태와 소요 시간이 들어 있다. `jev_f.py record`가 이를 파싱·검증해 `jev_runs_raw.jsonl`(공개 저장소에는 포함하지 않음)에 append한다. Playwright MCP가 클릭 직후 저장한 accessibility snapshot(결과 포함, 공개 저장소에는 포함하지 않음)과도 같은 레코드 안에서 대조했다. 대상은 DECISION heading, 확률 목록, ms, state이고 성공한 24회 모두 일치했다.
- 레코드 검증 항목:
  - state가 표본 utterance와 같다. choices와 question이 정확히 같다.
  - 이 페이지 로드의 클릭 수가 그 로드에서 만든 레코드 수 + 1이다(중복 클릭 없음).
  - 직전 클릭과의 간격이 3 s 이상이다.
  - 해당 클릭 이후 `POST /api/evaluate`가 정확히 1회 있었다.
  - 성공한 run은 추가로 다음을 확인한다:
    - 표시된 결정, details JSON의 choice, status 문구가 같다.
    - 표시된 %가 round(details 확률 × 100)와 같다.
    - 결정이 표시된 확률의 argmax다.
- 레코드에는 `attempt` 필드가 있다. 1차 세션의 레코드 2건에는 나중에 `attempt: 1`을 넣었다. 저장된 evidence(dump, snapshot)로 그 2건을 다시 만들면 갱신된 파일과 바이트 단위로 같다.

## 2. 실행 기록

- **1차 세션.**
  - run 1(row 1)은 정상이었다. 08:09:33.548 클릭, POST 200(Jev의 항목별 출력은 공개 저장소에서 생략).
  - run 2(row 37)는 08:11:43.600 클릭 후 "Jev is temporarily unavailable." / "Unable to evaluate"가 떴다. 콘솔에는 `Failed to load resource: the server responded with a status of 502 () @ https://jevplayground.com/api/evaluate`가 찍혔다.
  - 당시 규칙대로 재시도 없이 중단하고, evidence만 모은 뒤 브라우저를 닫았다.
- **복구 확인.** 08:20에 기본 예시로 복구된 것을 확인했다. 이 실행은 별도 확인 실행이라 아래 집계에 넣지 않았다. 08:01의 사전 확인 1회도 같다.
- **2차 세션.**
  - 08:24:18에 페이지를 새로 열고 같은 설정(Question, 8개 choice, "8 of 10")을 다시 입력했다. passive listener도 다시 설치했다.
  - run 2\~24(23행)를 실행했다. 23회 모두 200이었고 콘솔 오류는 0건이었다(경고 98건은 모두 CSS preload 안내).
  - 60 s 재시도 규칙은 한 번도 발동하지 않았다. 남은 예산 46회 중 23회를 썼다.
- **브라우저가 기록한 HTTP 요청.**
  - 1차 세션 36건: 정적 20, Next.js RSC prefetch GET 14, `POST /api/evaluate` 2(200, 502).
  - 2차 세션 57건: 정적 20, RSC prefetch 14, `POST /api/evaluate` 23(모두 200).
  - 출처: `results/F/jev_raw/network_requests_session{,2}.txt`(공개 저장소에는 포함하지 않음).
- **프로토콜 스크린샷**(공개 저장소에는 포함하지 않음):
  - `results/F/jev_shots/p1_run01_row001.png`: run 1.
  - `results/F/jev_shots/p1_run02_row037_error502.png`: 1차 세션 run 2의 502 화면.
  - `results/F/jev_shots/p1_run12_row239.png`: run 12.
  - `results/F/jev_shots/p1_run24_row459.png`: run 24.

## 3. 결과 표 (`.venv/bin/python results/F/jev_f.py analyze` 출력)

### Per-row (O = gold, X = wrong; Jev p = displayed %, Laya p = answer_confidence)

| # | row | utterance | gold | Jev pass 1 (key: ko-description) | Laya zero-shot | Laya ft-v1 |
|---|---|---|---|---|---|---|
| 1 | 1 | 내 화면 밝기 현황 알려줘 | general | — | X smart_home (0.81) | X smart_home (0.94) |
| 2 | 37 | 아들 방 불 꺼 줘 | smart_home | — [attempt 2] | O smart_home (0.99) | O smart_home (0.95) |
| 3 | 39 | 도미노피자에서 소세지 피자 주문해줘 | lifestyle | — | O lifestyle (1.00) | O lifestyle (0.94) |
| 4 | 61 | 올리야 집 컬러 밝은 거에서 어두운 색으로 바꿔 | smart_home | — | O smart_home (0.99) | O smart_home (0.93) |
| 5 | 71 | 이 동네 최신 뉴스 | info_qa | — | X media (0.32) | O info_qa (0.95) |
| 6 | 77 | 스피커 볼륨 무음으로 해줘 | media | — | X smart_home (0.81) | O media (0.95) |
| 7 | 117 | 진공 청소기 켜서 사용해 | smart_home | — | O smart_home (0.93) | O smart_home (0.96) |
| 8 | 181 | 올리 내 하루에 대해 너에게 말해야만 해 | general | — | X info_qa (0.57) | O general (0.92) |
| 9 | 201 | 휴가 스포츠 | general | — | X smart_home (0.92) | X media (0.36) |
| 10 | 207 | 내일 서울 회의 리마인더 추가해 | productivity | — | X general (0.95) | O productivity (0.96) |
| 11 | 209 | 이번 주말에 시내에 일정 있어 | productivity | — | X info_qa (0.46) | O productivity (0.94) |
| 12 | 239 | 유월 이십이일에 현수 생일이라고 표시해줘 | productivity | — | X general (0.43) | O productivity (0.94) |
| 13 | 259 | 채소 라자냐 만드는 데 얼마나 걸려 | lifestyle | — | O lifestyle (1.00) | O lifestyle (0.93) |
| 14 | 269 | 오븐에 굽는 거랑 직화에 굽는 거랑 뭐가 달라 | lifestyle | — | X smart_home (0.66) | O lifestyle (0.93) |
| 15 | 277 | 사가 열어 | media | — | X smart_home (0.99) | O media (0.90) |
| 16 | 279 | 게임들 열어 | media | — | X smart_home (0.38) | O media (0.94) |
| 17 | 335 | 부산에서 울산 가는 다음 기차 언제야 | transport | — | O transport (1.00) | O transport (0.95) |
| 18 | 357 | 장소 가는 택시 한 대 예약해 | transport | — | O transport (1.00) | O transport (0.96) |
| 19 | 383 | 청주 에 기차 몇 시에 도착하지 | transport | — | O transport (1.00) | O transport (0.94) |
| 20 | 411 | 달러 에서 유로 로 | info_qa | — | X transport (0.35) | O info_qa (0.95) |
| 21 | 435 | 삼성 t.v. 에 관한 설명 찾아줘 | info_qa | — | X transport (0.64) | O info_qa (0.95) |
| 22 | 445 | 트위터 열어서 메시지 보내 | communication | — | O communication (0.54) | O communication (0.96) |
| 23 | 453 | 유플러스에 불만 트윗 해 | communication | — | X general (0.64) | O communication (0.96) |
| 24 | 459 | 민호에게 보낼 이메일 작성해줘 | communication | — | O communication (1.00) | O communication (0.96) |

### Accuracy

| system | rows | correct | accuracy | Wilson 95% CI |
|---|---|---|---|---|
| Jev pass 1 (key: ko-description) | 24 | 20/24 | 0.833 | [0.641, 0.933] |
| Laya zero-shot multilingual | 24 | 10/24 | 0.417 | [0.245, 0.612] |
| Laya ft-v1 | 24 | 22/24 | 0.917 | [0.742, 0.977] |

### Agreement and exact McNemar (paired rows only; b = Jev right & Laya wrong, c = Jev wrong & Laya right)

| pair | n | same label | b | c | exact McNemar p |
|---|---|---|---|---|---|
| Jev pass 1 vs zero-shot | 24 | 10 | 10 | 0 | 0.0020 |
| Jev pass 1 vs ft-v1 | 24 | 20 | 0 | 2 | 0.5000 |

### Jev confidence behaviour (displayed %; the playground rounds probabilities to 2 decimals)

| pass | runs | top = 100% | runs with any 0% option | 0% cells / all cells | mean top % | mean top % right / wrong | wrong with top >= 90% | mean provider confidence |
|---|---|---|---|---|---|---|---|---|
| 1 | 24 | 14 | 23 | 145/192 | 91.3 | 96.5 / 65.5 | 0/4 | 0.899 (n=24) |

### Jev latency (ms, successful runs)

| pass | runs | displayed 'server + network' median / min / max | browser POST /api/evaluate median / min / max | click -> 'Evaluation complete' median / min / max |
|---|---|---|---|---|
| 1 | 24 | 249.5 / 203 / 570 | 497.5 / 444 / 913 | 502.5 / 446 / 916 |

### Jev model and token usage (details panel)

| pass | runs | model_id values | input tokens median / min / max | output tokens median / min / max |
|---|---|---|---|---|
| 1 | 24 | `typesafe-ai/jev` x24 | 716 / 708 / 727 | 255 / 249 / 262 |

### Per-domain correct

| gold domain | rows | Jev pass 1 (key: ko-description) | Laya zero-shot | Laya ft-v1 |
|---|---|---|---|---|
| productivity | 3 | 3/3 | 0/3 | 3/3 |
| media | 3 | 1/3 | 0/3 | 3/3 |
| smart_home | 3 | 3/3 | 3/3 | 3/3 |
| info_qa | 3 | 3/3 | 0/3 | 3/3 |
| communication | 3 | 3/3 | 2/3 | 3/3 |
| lifestyle | 3 | 3/3 | 2/3 | 3/3 |
| transport | 3 | 3/3 | 3/3 | 3/3 |
| general | 3 | 1/3 | 0/3 | 1/3 |

### Requests sent to jevplayground.com /api/evaluate

Total 25: HTTP 200 24, other 1; retries (attempt > 1) 1; smallest gap between consecutive clicks in one page load 21.6 s.

| pass | run | attempt | row | KST click time | gap from previous click (s) | HTTP | displayed ms | outcome |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | — | — | — | — | — |
| 1 | 2 | 1 | 37 | — | — | — | — | — |
| 1 | 2 | 2 | 37 | — | — | — | — | — |
| 1 | 3 | 1 | 39 | — | — | — | — | — |
| 1 | 4 | 1 | 61 | — | — | — | — | — |
| 1 | 5 | 1 | 71 | — | — | — | — | — |
| 1 | 6 | 1 | 77 | — | — | — | — | — |
| 1 | 7 | 1 | 117 | — | — | — | — | — |
| 1 | 8 | 1 | 181 | — | — | — | — | — |
| 1 | 9 | 1 | 201 | — | — | — | — | — |
| 1 | 10 | 1 | 207 | — | — | — | — | — |
| 1 | 11 | 1 | 209 | — | — | — | — | — |
| 1 | 12 | 1 | 239 | — | — | — | — | — |
| 1 | 13 | 1 | 259 | — | — | — | — | — |
| 1 | 14 | 1 | 269 | — | — | — | — | — |
| 1 | 15 | 1 | 277 | — | — | — | — | — |
| 1 | 16 | 1 | 279 | — | — | — | — | — |
| 1 | 17 | 1 | 335 | — | — | — | — | — |
| 1 | 18 | 1 | 357 | — | — | — | — | — |
| 1 | 19 | 1 | 383 | — | — | — | — | — |
| 1 | 20 | 1 | 411 | — | — | — | — | — |
| 1 | 21 | 1 | 435 | — | — | — | — | — |
| 1 | 22 | 1 | 445 | — | — | — | — | — |
| 1 | 23 | 1 | 453 | — | — | — | — | — |
| 1 | 24 | 1 | 459 | — | — | — | — | — |

주석:
- 요청 표의 "retries (attempt > 1) 1"은 재개할 때 row 37을 다시 실행한 것이다. 60 s 재시도 규칙에 따른 재시도는 0회다.
- 2차 세션 첫 클릭(row 37, attempt 2)은 새 페이지 로드의 첫 클릭이라 간격 칸이 비어 있다. 1차 세션 마지막 클릭과는 798 s 떨어져 있다.
- 표본 검정력: 이 표본에서 Jev가 ft-v1을 유의하게 이기는 것은 처음부터 불가능했다. ft-v1이 22/24라서 Jev가 24/24여도 b = 2, c = 0, p = 0.5에 그친다.

## 4. 관찰

1. **오류 구조: Jev가 ft-v1에 진 두 행은 설명문에 없는 MASSIVE 관례다.**
   - Jev가 틀린 4행 중 2행은 `scenario:general`의 모호한 문장이고 ft-v1과 zero-shot도 둘 다 틀렸다.
   - 나머지 2행은 `scenario:play`의 게임 실행 문장이다.
   - 이 데이터의 도메인 매핑은 MASSIVE `play` 시나리오를 `media`로 묶지만, 우리 `media` 설명("음악, 라디오, 팟캐스트, 오디오북 재생과 음량 조절")에는 게임이 없다. ft-v1은 학습 데이터에서 이 관례를 배웠고(0.90 / 0.94), zero-shot Laya도 둘 다 틀렸다(`smart_home`).
   - 따라서 ft-v1 대비 차이는 모델 능력보다 라벨 설명에 빠진 정보에서 나왔을 가능성이 크다. 설명에 "게임"을 넣으면 zero-shot 시스템의 이 두 행이 바뀌는지는 검증하지 않은 가설이다.
   - 한편 zero-shot Laya가 틀린 14행 중 Jev는 10행을 맞혔다. productivity·info_qa는 0/3 → 3/3, media 0/3 → 1/3이다.
2. **신뢰도: Jev의 오답은 확신하지 않았다.**
   - 24회 중 14회가 표시 100%였고, 192칸 중 145칸이 0%였다. playground가 소수 둘째 자리로 반올림하므로 0.995 이상은 100%, 0.005 미만은 0%로 보인다.
   - 오답 4건의 top 확률은 41\~86%(평균 65.5%)로 모두 90% 미만이었다. 정답의 평균은 96.5%다.
   - 90%에서 자르면 Jev는 24행 중 18행을 받고 18/18이 맞는다. ft-v1을 P2 정책 임계값 T = 0.907로 자르면 22행을 받고 21/22가 맞는다. 받은 오답은 row 1(0.94)이다.
   - details의 별도 provider `confidence.decision`은 정답 평균 0.958, 오답 평균 0.603이었다.
   - n = 24라 indicative 수준이다.
3. **지연과 비용 구조: hosted 생성형 호출과 로컬 encoder.**
   - Jev 표시값("server + network")은 중앙값 249.5 ms(203\~570)다. 같은 요청을 브라우저에서 재면 POST 중앙값 497.5 ms(444\~913)다. 표시값은 클라이언트 왕복이 아니다.
   - details 기준 결정 1건에 입력 약 716 토큰, 출력 약 255 토큰(249\~262)이 든다. 생성형 디코딩으로 보인다(추정).
   - 로컬 Laya 참조치:
     - P2 `/poc/decide` 왕복 p50 20.1 ms(ft-v1, MPS, loopback. `results/poc/P2_20261003.md:67`).
     - Track D in-process 13.8 ms(multilingual MPS 1문항. `results/D/D_summary_20261003.md:42`).
   - 배수: 표시값 기준 12.4배 / 18.1배, 브라우저 기준 24.8배 / 36.1배다.
   - 이 배수는 인터넷 왕복과 hosted 서비스(Jev), 로컬 loopback과 in-process(Laya)의 차이를 포함하므로 모델 속도 비교가 아니다.
   - 표시값 중앙값은 제3자가 공개한 Jev p50 236\~276 ms(`docs/03_benchmark_plan.md` §10 F4) 범위 안이다.

**그 밖의 사실:**
- details의 Model ID는 24회 모두 `typesafe-ai/jev`였고 버전 표기는 없었다.
- `rounding.probabilityDecimals`는 항상 2였고 `warnings`는 늘 비어 있었다.
- 응답 JSON의 probabilities 키 순서는 입력 choice 순서와 달랐다. playground나 API가 순서를 바꾸는지는 알 수 없다.
- 가용성: 1차 세션에서 502가 1회 났고, 약 13분 뒤 2차 세션 23회는 모두 정상이었다.

## 5. Caveats

- **n**: n = 24, 단일 패스다. 정확도·McNemar·신뢰도 수치는 모두 indicative 수준이다. 표본은 도메인 균등이라 자연 분포의 정확도와 다르다.
- **playground는 API가 아니다**:
  - 이 사이트는 독립 제3자 도구다("not affiliated with or endorsed by TypeSafe AI").
  - 모델 버전은 알 수 없다. 페이지는 "TypeSafe Jev"라고만 하고 details에는 Model ID `typesafe-ai/jev`만 있다.
  - 응답은 playground의 정규화(확률 2자리 반올림)와 자체 백엔드를 거친다.
  - "Real model execution. No simulated answers."는 페이지의 주장이고 검증할 수 없다.
  - 두 세션은 약 13분 떨어진 서로 다른 페이지 로드다. Model ID는 같았다.
- **옵션 표현**: Jev choice에는 description 필드가 없다. 그래서 `key: 설명`을 라벨 문자열 하나로 넣었다. Laya는 criteria dict로 key와 설명을 따로 받는다. 질문 문구도 조금 다르다(§1.2). key-only 라벨(pass 2)은 생략했으므로 Jev가 한국어 설명을 얼마나 쓰는지는 측정하지 않았다.
- **Jev의 한국어 지원**은 문서화돼 있지 않다(미확인).
- **Laya 쪽**: 수치는 기존 리포트(CPU fp32, 2026-10-02/03)에서 읽었고 이번에 다시 돌리지 않았다. ft-v1은 같은 MASSIVE 분포의 train으로 학습했다(정확히 같은 utterance는 제외). 그래서 zero-shot 시스템인 Jev와 비교하면 in-domain 이점이 있다. §4.1의 `play` → `media` 관례가 그 예다.
- **재현성**: Jev 출력이 결정론적인지 확인하지 않았다. 같은 행을 두 번 성공시킨 적이 없다.

## 6. 결정과 재개 기록

- 1차 세션은 정지 규칙대로 run 2의 502에서 멈췄다.
- 08:20에 복구를 확인한 뒤 다음을 결정했다:
  1. 나머지 23행을 같은 8개 choice로 실행한다.
  2. 5xx나 "temporarily unavailable"이면 60 s 뒤 1회 재시도하고, 다시 실패하면 중단한다. 총 요청은 46회 이내로 한다.
  3. pass 2는 생략한다(옵션 c).
  4. Playwright MCP 출력 디렉터리는 다른 실행이 남긴 파일까지 포함해 삭제한다.
- 2차 세션은 23회로 끝났고 예산 23회가 남았다.
- 코드 변경: `jev_f.py record`가 성공과 오류를 모두 기록하도록 바꾸고(오류면 exit 2), `attempt`를 붙인다. `record_error`는 1차 세션 명령 이름이라 alias로 남겼다. `analyze`는 실행하지 않은 pass를 표에서 뺀다.

## 7. 파일

| 파일 | 내용 |
|---|---|
| `results/F/jev_f.py` | sample / record (record_error alias) / analyze. 모델 호출 없음 |
| `results/F/jev_sample_24.jsonl` | 24행: utterance, gold, laya_zs, laya_zs_p, laya_ft, laya_ft_p, row_index |
| `results/F/jev_runs_raw.jsonl`(공개 저장소에는 포함하지 않음) | Jev 요청 25건(성공 24, row 37의 1차 시도 502 1건) |
| `results/F/jev_raw/` | 요청별 DOM dump(`p1_NN.json`, `p1_02_error.json`)와 accessibility snapshot(`*.snapshot.yml`) 25쌍, `network_requests_session{,2}.txt`, `console_session{,2}.log`(DOM dump, accessibility snapshot, 네트워크 목록, 콘솔 로그는 공개 저장소에는 포함하지 않음) |
| `results/F/jev_shots/`(공개 저장소에는 포함하지 않음) | `p1_run01_row001.png`, `p1_run02_row037_error502.png`, `p1_run12_row239.png`, `p1_run24_row459.png` |
| `results/F/F_jev_20261006.md` | Run Card (`docs/06_templates.md` §1) |

[English](jev_playground_manual_20261006.md) | **한국어**
