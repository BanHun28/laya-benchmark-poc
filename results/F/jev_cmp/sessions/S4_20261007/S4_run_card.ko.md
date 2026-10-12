# Run 20261007-1616_jev-playground_S4 (T6_sst5_40 + T7_massive_intent_10opt_en_20 + T7_massive_intent_10opt_de_20)

| 항목 | 값 |
|---|---|
| run_id | 20261007-1616_jev-playground_S4 (Track F, Laya vs Jev 비교 세션 S4: T6 SST-5 40 Score 5레벨 + T7 MASSIVE intent-10 en 20 · de 20) |
| 날짜 / 시작 시각 | 2026-10-07 (KST). 자료 읽기 약 14:10(시작 시각 미기록, 첫 명령 14:12:40), 스크립트·회귀 점검 14:13\~14:15, 페이지 로드 14:15:58, 계측 설치 14:16:03.520, 첫 평가 클릭 14:16:25.459, Part A 마지막 14:26:30.854, Part B 14:26:51.990\~14:31:41.745, Part C 14:32:02.821\~14:36:52.645, 브라우저 종료 약 14:37:20, 분석·문서 14:37\~14:47 |
| 트랙 / PoC phase | F (`docs/09_laya_vs_jev_plan.md` §7 S4, §7.2) |
| 가설 | 해당 없음. H1\~H10에 Jev 직접 비교 가설이 없다. 질문은 "같은 입력에서 Jev와 Laya(english / multilingual / Router)의 score 레벨·의도 분류·확률·지연이 어떻게 다른가, de에서 어떻게 달라지는가"이다 |
| 목적 (한 줄) | T6 SST-5(Score 5레벨)와 T7 MASSIVE-10 en·de를 Laya와 바이트 동일한 입력으로 Jev에 보내 같은 행끼리 짝 비교한다 |
| 명령어 | 계획·입력: `source env.sh && .venv/bin/python results/F/jev_cmp/sessions/S4_20261007/s4_prep.py`(항목별 `raw/js/iNN_*.js`, 무클릭 `dry_i01_*`, `dry_i41_*`, `dry_i61_*` 생성(`raw/js/`는 공개 저장소에는 포함하지 않음). 폼 옵션 = Laya `render_options(Agent._to_internal(q))` 80/80 assert(`s4_prep.py:75`), T6은 `level %d: %s` 5개, T7 en·de는 행마다 id·gold·옵션 목록 동일 assert(`:89`)). 브라우저: Playwright MCP `browser_navigate https://jevplayground.com/` → `browser_run_code_unsafe raw/js/instrument.js`(S3 계측, 버전 태그만 S4) → 항목마다 `browser_run_code_unsafe raw/js/iNN_*.js`(폼 입력 → `window.__jev.ready(sha12, 15000)` → 해시가 맞을 때만 `button.run-button` 클릭) → `browser_evaluate window.__jev.dump()`를 `raw/rNN_<T6|T7en|T7de>_rowRR.json`(공개 저장소에는 포함하지 않음)으로 저장 → `.venv/bin/python …/s4_record.py RUN ITEM`(= `jev_cmp.py record S4 <SET> RUN DUMP --row R` + 중단 조건 분류). 분석: `.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S4 T6_sst5_40`, `… analyze S4 T7_massive_intent_10opt_en_20`, `… analyze S4 T7_massive_intent_10opt_de_20`, `… analyze S4 T7_massive_intent_10opt_en_20,T7_massive_intent_10opt_de_20` |
| 환경 기록 | 로컬 모델 실행 없음. 브라우저는 Playwright MCP Chromium. 대상은 jevplayground.com `POST /api/evaluate`. Laya 수치는 S0 리포트(`results/F/jev_cmp/laya/`, laya 0.3.23, device cpu)에서 읽었다 |
| 체크포인트 | Jev: 응답 `model`과 View details Model ID `typesafe-ai/jev` 80/80, 버전 미표기. Laya english / multilingual revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`(리포트 config.revisions). Router는 T6 40 · T7 en 20 모두 english, T7 de는 multilingual 15 / english 5 |
| 데이터셋 | T6: `data/evals/jev_cmp/T6_sst5_40.jsonl`, n=40(레벨 0\~4 각 8), dataset_sha256 `f56ebc3bb73ed687db54f3f273645911ee0727bdd2806664e2b86cd9e01904f0`, questions_sha256 `9f4cb5fe47389ccf726aafb6656db26bc69fcc587fdd9ee55dac025d89cfd94f`, 폼 sha256 `dd9c56ea8db2d920408528557696528be74b440626d7a8f5e3cea9e0eaeb5037`. T7 en: `T7_massive_intent_10opt_en_20.jsonl`, n=20, dataset_sha256 `034e2c88a730463215407fc1f3883093f08bde494dc5bd933be44834913bf04f`, 폼 sha256 `a2756ef8a3655fce45f82e41a4beee59bdfc1c289c91aa5a83ae5b6a14e5919d`. T7 de: `T7_massive_intent_10opt_de_20.jsonl`, n=20, dataset_sha256 `56e7943c697a3bc551d4750d0789b60c8730f3c8e003c876d936da8d79372f72`, 폼 sha256 `94794de84b3c8eb4fcb15a1870e9a8e67b1e3a98ef71177469aff99b97d20955`. T7 questions_sha256 `e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588`(en·de 공통). 세 Laya 리포트 모두 폼 파일과 두 해시가 같다 |
| 디바이스 / 정밀도 / 스레드 | Jev: hosted, 미상. Laya: S0 리포트 기준 CPU fp32, intra-op 10 / inter-op 1, batch 8 |
| 파라미터 | Part A: Single question / Score. Question `` How positive is the sentiment of `text`? ``, Rubric level 0\~4 = `level 0: very negative` / `level 1: negative` / `level 2: neutral` / `level 3: positive` / `level 4: very positive`(Laya score 렌더링, 최대 22자), State = 폼 `state_text`(최대 209자). Part B·C: Single question / Choice. Question `` What is the user asking for in `utterance`? ``, 옵션 10개 `key: key spaced`(최대 50자) 폼 순서, State = `{"utterance": …}`. 운영: 처음부터 monotonic 기준 Run 간격 가드 15 s(규칙 ≥ 10 s). 5xx면 65 s 뒤 같은 항목 1회 재시도(`next_gap`), 재시도도 실패하면 종료. 429·제한 문구·captcha는 재시도 없이 즉시 세션 중단. 세션 상한 100(계획 80) |
| 반복 / warm-up | 단일 패스, warm-up 없음. 항목당 1회, 재시도 0(run 번호 = 항목 번호) |
| 소요 시간 | 브라우저 세션 약 21분 22초(14:15:58\~14:37:20), 평가 구간 20분 27.2초(첫 클릭\~마지막 클릭). 작업 전체 약 37분(자료 읽기·준비 약 6분, 브라우저 21분, 분석·문서 약 10분) |

## 결과

| 지표 | 값 | upstream 참고치 (출처) | 차이 | 비고 |
|---|---|---|---|---|
| score 정확도, argmax 레벨 (T6, 주 지표) | Jev 26/40 = 0.650 [0.495, 0.779]; Laya english·Router 0.425 [0.285, 0.578], multilingual 0.325 [0.201, 0.480] | Laya english 0.372 / multilingual 0.282 (N=600, held out; `laya_summary.md` §3). Jev 공개치 없음 | english +0.053, multilingual +0.043 | Laya 두 CI 모두 upstream 값을 포함 |
| score 정확도, 반올림 E[level] (T6, 보조 = 표시 규칙) | Jev 27/40 = 0.675; english 0.400; multilingual 0.325 | n/a | | argmax와 갈린 행: Jev 2, english 6, multilingual 0 |
| score_mae (E[level] vs gold) | Jev 0.432, english 0.888, multilingual 1.419 | english 0.905 / multilingual 1.359 (upstream N=600) | english −0.017, multilingual +0.060 | Jev − Laya paired bootstrap: −0.456 [−0.711, −0.207], −0.987 [−1.341, −0.622] |
| McNemar (exact) | T6 argmax: Jev vs english·Router 15/6 p=0.078, vs multilingual 18/5 p=0.011; 반올림 E: 15/4 p=0.019, 19/5 p=0.007. T7 en: 4/0 p=0.125, 3/2 p=1.0, Router 4/0. T7 de: 11/0 p=0.001, 11/1 p=0.006, Router 12/1 p=0.003. 합산 40: 15/0 p=0.0001, 14/3 p=0.013, 16/1 p=0.0003 | n/a | | 합산 40은 같은 id 쌍이라 독립 아님 |
| choice_accuracy (T7) | en: Jev 18/20 = 0.900, english·Router 0.700, multilingual 0.850. de: Jev 0.900, english 0.350, multilingual 0.400, Router 0.350. 합산: Jev 0.900, english 0.525, multilingual 0.625 | 20옵션 CPU sweep: en english 0.820 / multilingual 0.710, de 0.420 / 0.500 (`laya_summary.md` §4) | 비교 불가 | 옵션 수가 다르다(10 vs 20). 언어당 n=20, 방향 신호 |
| Brier | T6(5레벨): Jev 0.502, english 0.770, multilingual 1.149. T7 en: 0.143 / 0.394 / 0.293, de: 0.150 / 1.046 / 0.890 | n/a | | Σ(p − onehot)². T7은 행별 옵션 10개. Jev 확률 2자리 반올림 |
| ece | T6: Jev 0.184 (english 0.239, multilingual 0.513). T7 en: 0.092 (0.214, 0.184), de: 0.086 (0.513, 0.453) | Jev typed-decisions 0.144, nibzard 0.246 (09 §1) | | 15 bins, argmax p 기준 |
| mean_confidence (Jev 표시 top p) | T6 0.751 (정답 0.785 / 오답 0.688), 100% 표시 0/40, 오답 중 ≥ 0.90 0/14. T7 en 0.934, de 0.940, 100% 표시 15/20 · 12/20, 오답 중 ≥ 0.90 1/2 · 1/2, 정답 옵션 0% 0/40 | n/a | | Laya multilingual T6 오답 중 ≥ 0.90 10/27, de english 6/13 |
| 첫/마지막 레벨 선택률 (T6, argmax) | Jev 4/40 · 5/40, english 10/40 · 0/40, multilingual 11/40 · 0/40 (gold 8/40 · 8/40) | #131: multilingual 첫 레벨 회피(README.md Honest limits) | 재현 안 됨 | multilingual은 40행 모두 레벨 0·1(레벨 2\~4 0/40) |
| latency (Jev 표시 "server + network" = latencyMs) | T6 median 236 (172\~348) ms, T7 en 220.5 (175\~253), de 230.5 (195\~310) | Jev 제3자 p50 236\~276 ms (09 §1) | 범위 안 또는 약간 아래 | 표시 = latencyMs half-up 80/80 |
| latency (브라우저 POST / 클릭→완료) | T6 477.5 / 479 ms, T7 en 451 / 452.5, de 460 / 461.5 (median) | n/a (하드웨어·네트워크 다름) | | POST − latencyMs 중앙 230.1 ms. POST 최대 1,342 ms(Jev의 항목별 출력은 공개 저장소에서 생략) |
| 토큰 (View details) | T6 입력 365.5 (349\~391) / 출력 17 (17); T7 en 536.5 (510\~566) / 150.5 (136\~172); de 536.5 (517\~569) / 150.5 (136\~172) | n/a | | 합계 입력 36,289 / 출력 6,798 |

## §7.3 세션 필드

| 항목 | 값 |
|---|---|
| 사이트 상태 확인 | 14:15:58 페이지 정상 로드. 계측 설치 시 body 제한 문구 검사 결과 없음. UI·DOM id가 S3와 같다. Score 선택 시 "ORDERED SCALE / Jev rates the situation against your rubric from lowest to highest.", "Rubric / Lowest → highest", textbox "Rubric level 0\~4"(`raw/mcp/snapshot_dry_i01_T6_row00_form.yml`). 예산 때문에 기본 예시는 실행하지 않았다 |
| 요청 수 | `POST /api/evaluate` 80회 = Part A 40 + Part B 20 + Part C 20, 모두 200. 5xx 0, 4xx 0(429 0), 재시도 0. 세션 상한 100 중 80. 네트워크 목록: POST 80(전부 `/api/evaluate`, 200), GET 77(문서 1, 정적 40, Next.js RSC prefetch 36, 모두 200) |
| 요청 없는 클릭 | 0. 무클릭 dry run 3회(item 1, 41, 61)는 폼 입력과 해시 대조만 했다. View details 펼치기 클릭 6회(스크린샷용)는 Run 버튼이 아니며 요청을 만들지 않았다(resource timing `/api/evaluate` 80건 = Run 클릭 80회, 클릭 → fetch 시작 0\~5 ms) |
| 간격 | monotonic 기준 79개 간격: 최소 15.013 s, 중앙 15.125 s, 최대 31.109 s(run 2: run 1 스크린샷 시간). Part A 15.024 / 15.118 / 31.109, Part B 15.033 / 15.133 / 21.136, Part C 15.013 / 15.133 / 21.076(파트 첫 run은 dry run·스크린샷 뒤). resource timing 시작 간격 15.014 / 15.125 / 31.105 s |
| Model ID / 토큰 범위 | `typesafe-ai/jev` 80/80. 입력 349\~569, 출력 17\~172. `rounding` {probabilityDecimals 2, scoreDecimals 2}, `warnings` [] 80/80. provider `confidence.decision` 80/80(top p와 같은 값: T6 6/40, T7 33/40) |
| 입력 해시 대조 | 요청 전 sha12 80/80 일치. 요청 후 request body가 폼 파일 payload와 바이트 단위로 80/80 같다 |
| 파싱 실패 | 0. T6 score 40개는 모두 레벨 5개 확률과 `score`(0.02\~3.99, 정수 0/40)를 돌려주었고 표시 SCORE 레벨 = `rubric[Math.round(score)]` 40/40. T7 choice 40개는 답이 입력 라벨 중 하나와 정확히 같고 확률 키 집합이 옵션 10개와 같다. 화면 = 응답 80/80 |
| 오류 문구 | 없음. 429·제한 문구·captcha·"temporarily unavailable" 0건. 콘솔은 경고 198건(CSS preload)이고 오류 0건 |
| Laya 대응 리포트 | `results/F/jev_cmp/laya/T6_sst5_40_{english,multilingual,router}.json`(questions_sha256 `9f4cb5fe…`), `T7_massive_intent_10opt_{en,de}_20_{english,multilingual,router}.json`(`e587cdad…`) |
| 오늘 누적 사이트 사용량 | 240 = S2 80 + S3 80 + S4 80(`jev_runs_all.jsonl`의 2026-10-07 행). 하루 100 자체 상한은 2026-10-07 프로젝트 책임자 결정으로 해제했다. 사이트 전체 누적은 338(1일차 98 + 오늘 240). S4 run 80(오늘 240번째, 14:36:52)까지 제한 신호가 없었다 |
| 비용 | n/a. Jev 단가는 확인하지 않았다. 토큰 합계 입력 36,289 / 출력 6,798 |

## 산출물

- `results/F/jev_cmp/sessions/S4_20261007/S4_summary.md`: T6·T7 결과, McNemar, MAE bootstrap, 레벨 분포(#131), 언어 간 일관성, 확신도, 오답, 지연·토큰, 관찰과 한계
- `results/F/jev_cmp/sessions/S4_20261007/S4_requests.jsonl`(80줄), `results/F/jev_cmp/jev_runs_all.jsonl`(master 311줄. 앞 231줄은 S4 전 사본과 바이트 동일, 뒤 80줄은 `S4_requests.jsonl`과 동일) (두 파일은 공개 저장소에는 포함하지 않음)
- `results/F/jev_cmp/sessions/S4_20261007/raw/`: dump 80, `run_plan.json`, `js/`(instrument, 항목 스크립트 80, dry run 3), `evaluate_timing_all.json`, `network_requests.txt`, `network_requests_all.txt`, `console.log`, `mcp/`(페이지 로드 snapshot, dry run 폼 snapshot, MCP 콘솔 로그) (`run_plan.json` 외에는 공개 저장소에는 포함하지 않음)
- `results/F/jev_cmp/sessions/S4_20261007/shots/`(공개 저장소에는 포함하지 않음): Part A·B·C 각 첫·마지막 run(View details 열림, full page) 6장
- `results/F/jev_cmp/sessions/S4_20261007/s4_prep.py`, `s4_record.py`
- `results/F/jev_cmp/jev_cmp.py`: `parse_single_display`·`analyze` 확장(아래)

## 이상 / 주석

- **오류 없음.** 5xx·429·제한 문구가 없어 재시도 규칙(65 s 뒤 1회)과 중단 규칙은 발동하지 않았다.
- **Score 렌더링 확인.** S1 레시피는 score 질문의 rubric 칸에 폼 `options` 문자열 전체(`level i: …`)를 넣는다(S1 run 1 request body의 `criteria`). Laya도 score 질문을 `level %d: %s`로 렌더링해서 읽으므로(`laya/common.py` `render_options`), T6 rubric 칸에 같은 문자열을 넣었다. `s4_prep.py:75`가 Laya `render_options` 출력과 폼 옵션의 일치를 assert한다. 화면 막대 라벨은 그래서 "0 — level 0: very negative" 형태다.
- **`jev_cmp.py` 변경(최소).**
  1. `parse_single_display`(`jev_cmp.py:128-131`): 단일 모드 Score 카드의 머리글은 DECISION이 아니라 SCORE다. DECISION이 없으면 SCORE를 찾는다. 회귀: 기존 단일 모드 dump 190개(S1\~S3)의 파싱 결과가 변경 전과 모두 같다. 첫 T6 dump(run 1)는 기록 전에 화면 파싱을 따로 대조했다.
  2. `analyze`의 세트 인자에 콤마를 허용해 여러 세트를 합친다(`:318-320`, Laya 리포트도 세트별로 읽어 합침 `:334-337`). 두 세트면 같은 id의 언어 간 일관성 표를 낸다(`crosslang_lines`, `:373-375`, `:465-479`).
  3. score 세트 분기 `score_lines`(`:338-342`, `:482-573`): argmax 레벨 정확도(주), 반올림 E[level] 정확도(보조, 표시 규칙 `Math.round`와 같은 half-up), E[level] MAE·부호 오차·±1 이내, 5레벨 Brier, ECE(argmax p), McNemar 두 규칙, MAE 차이 paired bootstrap(2,000회, seed 13), 예측 레벨 분포와 첫/마지막 레벨 선택, gold 레벨별 정답과 평균 E, 혼동 행렬(Jev, Laya english), Jev 확신도, 행별 표. Laya 값은 `laya_summary.json` `results.T6_sst5_40`의 accuracy·brier·ece·mean_confidence·score_mae·within_1_level과 같다.
  4. `request_lines`(`:454-462`): Router 리포트 줄에 "answered by"(체크포인트별 행 수)를 붙였다. 회귀: `analyze S1 T2`, `S2 T3`, `S3 T4`, `S3 T5`, `S4 T7 en·de` 출력은 이 한 줄의 접미사만 다르고 나머지는 바이트 동일하다. `t1 S1,S2`는 바이트 동일하다.
- **호스트 wall clock 스텝.** wall − mono 오프셋이 run 77과 78 사이에 +14 → −38 ms(−52 ms)로 한 번 바뀌었다. 간격 가드와 dump 매칭은 monotonic 축이라 영향이 없다. `click_epoch_ms`·`click_kst`는 S3와 같이 monotonic 축 값이다.
- **간격 최대 31.1 s(run 2).** run 1 뒤 첫 T6 화면 파싱 수동 대조와 스크린샷 시간이다. 사이트와는 무관하다.
- **해석이 들어간 판단(확인 필요).** T7 Jev 오답 2 id를 라벨 경계 사례로 본 것, T6 2레벨 오답 1행을 혼합 감정 문장으로 본 것은 문장을 읽고 내린 판단이다. 채점은 데이터셋 라벨 그대로 했다.
- `docs/`와 `data/evals/`는 편집하지 않았다. Laya 모델은 실행하지 않았다. 레포 루트의 Playwright MCP 출력 디렉터리(snapshot 1, 콘솔 로그 1)는 `raw/mcp/`로 복사한 뒤 삭제했다.

## 다음 액션

- `docs/09_laya_vs_jev_plan.md` §7.1\~7.2에 S4 결과 반영(별도 작업. 이 세션은 docs를 편집하지 않았다). 사이트 전체 누적 338(1일차 98 + 오늘 240).
- S5: T7 ja·zh-CN·ko 60(+ T8 40). `analyze`는 콤마로 언어를 합칠 수 있지만 언어 간 일관성 표는 두 세트일 때만 낸다. 다섯 언어 비교에는 en을 기준으로 한 쌍별 표가 필요하다.
- 선택: T6 레벨 순서를 뒤집은 변형(레벨 4 → 0)을 Laya multilingual에 로컬로 돌리면 #131 위치 효과와 "very negative" 내용 효과를 분리할 수 있다(Jev 요청 불필요).

[English](S4_run_card.md) | **한국어**
