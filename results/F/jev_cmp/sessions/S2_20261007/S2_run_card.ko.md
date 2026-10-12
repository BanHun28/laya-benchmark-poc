# Run 20261007-0849_jev-playground_S2 (T1_typed_decisions_40 A안 39 + T3_emotion_40)

| 항목 | 값 |
|---|---|
| run_id | 20261007-0849_jev-playground_S2 (Track F, Laya vs Jev 비교 세션 S2: T1 A안 39 case + T3 DAIR Emotion 40) |
| 날짜 / 시작 시각 | 2026-10-07 (KST). 자료 읽기 약 08:41, 페이지 로드 08:46:26, 첫 평가 클릭 08:49:40.382, 마지막 평가 클릭 09:12:47.969, 브라우저 종료 약 09:13, 분석·문서 09:13\~09:25 |
| 트랙 / PoC phase | F (`docs/09_laya_vs_jev_plan.md` §7 S2, §7.2 2일차) |
| 가설 | 해당 없음. H1\~H10에 Jev 직접 비교 가설이 없다. 질문은 "같은 입력에서 Jev와 Laya(english / multilingual / Router)의 정답·확률·지연이 어떻게 다른가"이다 |
| 목적 (한 줄) | T1의 Jev 비교 가능 decisions(A안, case당 Multiple questions 1회)와 T3 Emotion 40을 Jev에 보내 Laya와 같은 decisions로 짝 비교한다 |
| 명령어 | 계획·입력 스크립트: `.venv/bin/python results/F/jev_cmp/sessions/S2_20261007/s2_prep.py`(`jev_cmp.py` `payload`/`row_items`로 sha12를 만들고 항목별 `raw/js/iNN_*.js`를 생성(`raw/js/`는 공개 저장소에는 포함하지 않음). row 30은 S1 payload와 같음을 assert하고 제외). 브라우저: Playwright MCP `browser_navigate https://jevplayground.com/` → `browser_run_code_unsafe raw/js/instrument.js`(passive listener + `/api/evaluate` fetch wrapper) → 항목마다 `browser_run_code_unsafe raw/js/iNN_*.js`(폼 입력 → `window.__jev.ready(sha12, 15000)` → 해시가 맞을 때만 `button.run-button` 클릭) → `browser_evaluate window.__jev.dump()`를 `raw/rNN_<T>_rowRR.json`(공개 저장소에는 포함하지 않음)으로 저장 → `.venv/bin/python …/s2_record.py RUN ITEM`(= `jev_cmp.py record S2 <SET> RUN DUMP --row R [--qids …]` + 중단 문구 검사). 분석: `.venv/bin/python results/F/jev_cmp/jev_cmp.py t1 S1,S2`, `… analyze S2 T3_emotion_40` |
| 환경 기록 | 로컬 모델 실행 없음. 브라우저는 Playwright MCP Chromium. 대상은 jevplayground.com `POST /api/evaluate`. Laya 수치는 S0 리포트(CPU fp32)에서 읽었다 |
| 체크포인트 | Jev: 응답 `model`과 View details Model ID `typesafe-ai/jev` 79/79, 버전 미표기. Laya english / multilingual / typed-decisions revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`(리포트 config.revisions), Router는 T1 120·T3 40 모두 english |
| 데이터셋 | T1: `data/evals/jev_cmp/T1_typed_decisions_40.jsonl`, 40 case / 200 decisions(Jev 비교 120), dataset_sha256 `749a24c4c0db977686f29eeecd41201e16b97629a9fbd641a6ffb5dfe6163834`, questions_sha256 `d46ef26a6ec2f2f8c6fc0cfa1e81715751dda05f173cd028ae3eaaa4b9d519cb`(리포트 config), 폼 `T1_typed_decisions_40_playground.json` sha256 `b0eacae8e2ee78fe8372d910da3a1d6c7cad7be4e4a623c101db4fe1c3a6af65`. noul no-criteria 변형: dataset_sha256 `2508b8172b70cd65f02d1e7ba21dca97ebd7d6603b3ee9f7ad8a057e06b50283`, questions_sha256 `7b7f5dac86a48ee9fc492bbb9b29e1a406444c311578f902e6d93097c08dbd25`. T3: `T3_emotion_40.jsonl`, n=40, dataset_sha256 `2246b5f04b1ed714ef9789548d6e0cf932db1fa40aed95a4b9a3f616a11510cb`, questions_sha256 `bd7cc49e3561bf50d45db8c2d35820b8ddea855c9dfbc081303636596b4b4c97`, 폼 sha256 `4b0becf94e58d6b6e221028f4783bbdca8c2b953f0ab3120c90bac111fa65356` |
| 디바이스 / 정밀도 / 스레드 | Jev: hosted, 미상. Laya: S0 리포트 기준 CPU fp32, intra-op 10 / inter-op 1, batch 8 |
| 파라미터 | Part A: Multiple questions, case의 비교 가능 질문(agent_trace 3, customer_service 2, invoice 3, security 4)을 폼 순서대로 입력. choice 라벨은 `key: description`(최대 78자), score rubric은 `level k: …` 5칸, Boolean은 질문 문장만. Part B: Single question / Choice, 옵션 6개 고정 순서, Question ``Which emotion is most strongly expressed in `text`?``, State = 폼 `state_text`. 운영: Run 간격 가드 12 s(run 1\~4) → 15 s(run 5\~), run 62부터 monotonic 기준. 5xx는 60 s 뒤 1회 재시도, 429·제한 문구·captcha는 즉시 중단 |
| 반복 / warm-up | 단일 패스, warm-up 없음. 항목당 성공 1회(row 0만 attempt 2) |
| 소요 시간 | 브라우저 세션 약 27분(평가 구간 23분 8초). 작업 전체 약 45분(자료 읽기·준비 약 6분, 브라우저 27분, 분석·문서 약 12분) |

## 결과

| 지표 | 값 | upstream 참고치 (출처) | 차이 | 비고 |
|---|---|---|---|---|
| T1 accuracy, Jev (120 decisions) | 104/120 = 0.867 [0.794, 0.916] | Jev 0.727 (BENCHMARKS.md, 제3자, 2,000 decisions; `docs/09_laya_vs_jev_plan.md` §1) | +0.140 | 문항 구성이 다르다(4레벨 score 70·80자 초과 choice 10 제외). 같은 부분집합에서 Laya english도 0.330 → 0.383 |
| T1 accuracy, Laya english / multilingual / Router (같은 120) | 0.383 / 0.367 / 0.383 | 0.362 / 0.352 (BENCHMARKS.md, 2,000 decisions) | | 문항별 최빈 0.575 미만 |
| T1 accuracy, Laya typed-decisions (파인튜닝 참고선) | 104/120 = 0.867 | 0.766 (같은 곳) | | Jev vs 이 체크포인트 b=10 / c=10, p=1.0 |
| choice_accuracy | T1 Jev 42/50 = 0.840 [0.715, 0.917]; T3 Jev 28/40 = 0.700 [0.546, 0.819] | T1 Laya en 0.280 / ml 0.320; T3 Jev 0.480 (제3자, 100 items), Laya en 0.573 (upstream T4) | T3 Jev +0.220 | T3 표본이 쉬운 쪽이다(Laya en도 +0.177) |
| noul_accuracy | T1 Jev 56/60 = 0.933 [0.841, 0.974] | Laya en 0.467(no-criteria 0.517), ml 0.433(0.417), `laya_summary.md` §2b | | 같은 입력(no-criteria)에서도 b=27 / c=2(en), 34 / 3(ml) |
| score (5레벨 10개) | argmax 6/10 = 0.600; MAE \|E[level] − teacher\| 0.389 | Jev MAE 0.391 (제3자, 2,000 decisions); Laya en 0.400 / 0.584 | | n=10 |
| T1 soft accuracy / Brier vs soft | 0.590 / 0.077 | Jev 0.580 / 0.148 (제3자) | +0.010 / −0.071 | Jev 확률 2자리 반올림 |
| ece | T1 0.181, T3 0.278 (15 bins) | Jev typed-decisions 0.144, nibzard 0.246 (09 §1) | | T1 과소확신, T3 과대확신 |
| mean_confidence (Jev 표시 top p) | T1 0.733 (정답 0.758 / 오답 0.569), T3 0.901 (정답 0.918 / 오답 0.861) | n/a | | T3 오답 7/12가 ≥ 90%, 정답 옵션 0% 7/40 (공개치 16%) |
| McNemar | T1 Jev vs en b=66 / c=8 p < 0.0001, vs ml 66 / 6 p < 0.0001; T3 Jev vs en 2 / 4 p=0.6875, vs ml 6 / 3 p=0.5078 | n/a | | |
| latency (Jev 표시 "server + network" = latencyMs) | A(T1 multi 2\~4문항) median 226 (164\~355) ms, B(T3) 241 (170\~713) ms | Jev 제3자 p50 236\~276 ms (09 §1) | 범위 안 | 표시 = latencyMs half-up 79/79 |
| latency (브라우저 POST / 클릭→완료) | A 481 / 483 ms, B 469 / 471.5 ms (median) | n/a (하드웨어·네트워크 다름) | | POST − latencyMs 중앙 235.6 ms |
| 토큰 (View details) | A 입력 760 (640\~953) / 출력 141 (138\~214); B 387.5 (372\~422) / 61 (61\~62) | n/a | | 합계 입력 45,616 / 출력 8,806 |

## §7.3 세션 필드

| 항목 | 값 |
|---|---|
| 사이트 상태 확인 | 08:46:26 페이지 정상 로드(UI·DOM id가 S1과 같음). 예산 때문에 기본 예시는 실행하지 않았다. 첫 요청(08:49:40)이 HTTP 502 "Jev is temporarily unavailable."였고, 73.7 s 뒤 재시도(run 2)가 200으로 끝났다(Jev의 항목별 출력은 공개 저장소에서 생략) |
| 요청 수 | `POST /api/evaluate` 80회 = Part A 40(성공 39 + 502 1) + Part B 40(성공 40). 5xx 1, 4xx 0, 재시도 1(성공). 세션 상한 80 중 80. 네트워크 목록도 POST 80(200 79, 502 1), GET 39(문서 1, 정적 19, RSC prefetch 19) |
| 요청 없는 클릭 | 0. 무클릭 dry run 2회(Part A 첫 항목, Part B 첫 항목)는 폼 입력과 해시 대조만 했다 |
| 간격 | wall clock 기준 최소 12.1 s, 중앙 15.1 s, 최대 131.7 s(run 61 계측 수정 뒤). monotonic 기준 최소 12.1 s(run 4), 13.07 s(run 61), 중앙 15.1 s. 79개 간격 모두 ≥ 10 s |
| Model ID / 토큰 범위 | `typesafe-ai/jev` 79/79. 입력 372\~953, 출력 61\~214. `rounding` {probabilityDecimals 2, scoreDecimals 2}, `warnings` [] 79/79 |
| 입력 해시 대조 | 요청 전 sha12 80/80 일치(재시도 포함). 요청 후 request body가 폼 파일 payload와 바이트 단위로 80/80 같다 |
| 파싱 실패 | 0. S2의 choice 답 89개(T1 49 + T3 40)는 모두 입력 라벨 중 하나와 정확히 같고, 확률 키도 옵션 key와 같다(89/89). 화면 = 응답 79 runs / 156 decisions 전부(`shown_ok`) |
| 오류 문구 | run 1: HTTP 502, 응답 `{"ok":false,"error":{"code":"UNAVAILABLE","message":"Jev is temporarily unavailable."}}`, 화면 "Unable to evaluate / Jev is temporarily unavailable. / No decision was generated. Your inputs are still here." 처리: 즉시 기록 → 60 s 넘게 대기 → 같은 항목 1회 재시도(성공). 그 외 429·제한 문구·captcha 0. 콘솔 오류는 이 502 1건(MCP 콘솔 로그), 나머지는 CSS preload 경고 |
| Laya 대응 리포트 | `results/F/jev_cmp/laya/T1_typed_decisions_40_{english,multilingual,router,typed-decisions}.json`(questions_sha256 `d46ef26a…`), `T1_typed_decisions_40_noulnocrit_{english,multilingual}.json`(`7b7f5dac…`), `T3_emotion_40_{english,multilingual,router}.json`(`bd7cc49e…`) |
| 오늘 누적 사이트 사용량 | 80(S2만. `jev_runs_all.jsonl`에 2026-10-07의 다른 요청 없음. 하루 상한 100) |
| 비용 | n/a. Jev 단가는 확인하지 않았다. 토큰 합계 입력 45,616 / 출력 8,806 |

## 산출물

- `results/F/jev_cmp/sessions/S2_20261007/S2_summary.md`: T1·T3 결과, McNemar, noul 같은 입력 비교, workflow·질문별, score 상세, 보정, 지연·토큰, 관찰과 한계
- `results/F/jev_cmp/sessions/S2_20261007/S2_requests.jsonl`(80줄), `results/F/jev_cmp/jev_runs_all.jsonl`(master 151줄) (두 파일은 공개 저장소에는 포함하지 않음)
- `results/F/jev_cmp/sessions/S2_20261007/raw/`: dump 80 + timeout dump 1, `run_plan.json`, `js/`(instrument, patch_clock, 항목 스크립트 79, dry run 1), `evaluate_timing_all.json`, `network_requests.txt`, `console.log`, `mcp/`(snapshot 3, 콘솔 로그) (`run_plan.json` 외에는 공개 저장소에는 포함하지 않음)
- `results/F/jev_cmp/sessions/S2_20261007/shots/`(공개 저장소에는 포함하지 않음): Part A 1·20·39번째 항목, Part B 1·20·40번째 항목(View details 열림, full page)
- `results/F/jev_cmp/sessions/S2_20261007/s2_prep.py`, `s2_record.py`
- `results/F/jev_cmp/jev_cmp.py`: `t1` subcommand와 `record` 확장(아래)

## 이상 / 주석

- **502 1회.** 첫 요청이 502였다. 규칙대로 60 s 이상 기다린 뒤 1회 재시도해 성공했고, 이후 79회는 모두 200이다. 재시도 때문에 요청 번호(`run`)가 항목 번호보다 1 크다. Part A 항목 1\~39는 run 2\~40(run 1은 502), Part B 항목 40\~79는 run 41\~80이다. `raw/run_plan.json`의 `item`과 dump 파일명의 `rNN`을 구분해 읽어야 한다. 예산이 정확히 80이 되어 Part B에서 5xx가 한 번 더 났다면 마지막 항목은 보내지 못했을 것이다.
- **wall clock 스텝(측정 이상).** run 60과 61 사이에 호스트 시계가 +1.98 s 스텝했다(`Date.now() − performance.now()`가 timeOrigin 대비 +1,990 ms). resource timing을 `performance.timeOrigin + startTime`으로 환산하던 dump가 run 61의 POST 항목을 클릭 전으로 보고 timeout났다. 요청은 1회만 나갔고 200이었다(wrapper 기록 1, resource timing 1). dump와 간격 가드를 현재 오프셋·monotonic 기준으로 고쳤고(`raw/js/patch_clock.js`, 요청 없음), run 61을 다시 dump해 기록했다. 다음 세션은 처음부터 monotonic 기준 계측을 쓰는 것이 맞다.
- **계측·입력 방식 변경(S1 대비).** 상태 문자열을 손으로 옮기지 않도록 `s2_prep.py`가 폼 파일에서 항목별 Playwright 스크립트를 만들고, 스크립트는 해시가 맞을 때만 클릭한다. 간격 가드를 12 s에서 15 s로 올렸다(run 5부터). Single 모드에서는 폼을 고치면 결과 패널이 "Your Jev decision will appear here."로 초기화된다(관찰만, 영향 없음).
- **`jev_cmp.py` 변경(최소).** (1) `expected_view`: score 표시 레벨을 클라이언트와 같은 `Math.round`(half-up, `floor(score + 0.5)`)로 계산한다. Python `round`는 half-even이라 x.50에서 표시 대조가 틀릴 수 있었다(이번 세션에 x.50 score는 없었다). (2) `record`: `omitted` 사유를 폼 항목의 `reason`에서 가져온다. decision마다 화면 문자열 `shown`·`shown_pct`·`shown_ok`, score는 `shown_score`(`x.xx / 4`, 화면 대조 포함)를 남긴다. (3) `t1` subcommand: `laya_summary.py`의 `decisions` / `metrics` / `t1_extra`로 Jev와 Laya를 같은 코드로 채점한다. 변경 후 S1 run 1(T1 multi)과 S1 T2 row 0 dump를 쓰기 없이 다시 기록해 기존 필드가 그대로임을 확인했다.
- **T1 데이터셋 sha.** S1 run card의 T1 dataset_sha256(`45806a15…`)은 2026-10-06 10:28 재빌드 후 `749a24c4…`로 바뀌었다. questions_sha256(`d46ef26a…`)은 같고, Laya T1 리포트도 `749a24c4…`다. row 30의 A안 payload는 S1 run 1과 같다(sha12 `5a9e5492744b`).
- **비교 조건 차이.** T1의 Jev는 case당 질문 2\~4개를 한 요청에서 함께 평가했고 Laya는 질문을 독립 row로 평가했다. T1 gold(teacher argmax)와 Jev의 관계는 확인하지 못했다(확인 필요).
- Playwright MCP 출력 디렉터리(snapshot 3, 콘솔 로그 1)는 `raw/mcp/`로 복사한 뒤 레포 루트에서 삭제했다.

## 다음 액션

- `docs/09_laya_vs_jev_plan.md` §7.1\~7.2에 S2 결과 반영(별도 작업. 이 세션은 docs를 편집하지 않았다).
- S3(3일차): T4 Banking77-10 40 + T5 BoolQ 40 = 80. 계획이 상한 80과 같아 5xx 재시도 여유가 없다. 재시도가 생기면 마지막 항목을 S4로 넘기는 규칙을 미리 정해 둘 것을 제안한다. 계측은 처음부터 monotonic 기준(`patch_clock.js` 반영)으로 시작한다.
- T1 후속(선택, 예산 필요): Multiple questions의 "함께 평가" 효과를 분리하려면 일부 case를 Single 모드(C안)로 다시 보내 같은 decision을 비교한다. teacher 라벨 출처 확인.

[English](S2_run_card.md) | **한국어**
