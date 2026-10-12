# Run 20261008-1522_jev-playground_S7 (T9_enron_spam_40 + T10_support_tickets_queue_40)

| 항목 | 값 |
|---|---|
| run_id | 20261008-1522_jev-playground_S7 (Track F, Laya vs Jev 비교 세션 S7. 3-arm 확장 과제 T9 Enron spam 40 + T10 고객지원 티켓 큐 40. 프로젝트 책임자 승인: `results/T3arm/PREP_20261008.md` "프로젝트 책임자 결정" 5번) |
| 날짜 / 시작 시각 | 2026-10-08 (KST). 자료 읽기 약 15:1x(시작 시각 미기록, 첫 시각 기록 15:18:38 master 백업), 스크립트·회귀 15:18\~15:21, 페이지 로드 15:21:49, 계측 설치 15:21:52.647, 무클릭 dry run 4회 15:22, 첫 평가 클릭 15:22:54.937, Part A 마지막 15:33:10.768, Part B 15:33:29.511\~15:43:23.504, 브라우저 종료 약 15:43:55, 분석·문서 15:44\~15:55 |
| 트랙 / PoC phase | F (`docs/09_laya_vs_jev_plan.md` §2 운영 규칙, §4 입력 동일성, §7.3 run card 필드). 3-arm 확장(`docs/11_three_arm_plan.md`)의 Jev arm |
| 가설 | 해당 없음(H1\~H10에 Jev 직접 비교 가설 없음). 질문: "Laya 학습 믹스에 들어 있는 두 과제(T9 spam, T10 10-way 큐)에서, 같은 입력의 Jev zero-shot과 Laya vanilla(english / multilingual / Router)는 어떻게 다른가" |
| 목적 (한 줄) | T9·T10을 Laya와 바이트 동일한 입력으로 Jev에 보내 같은 행끼리 짝 비교한다 |
| 명령어 | 준비: `source env.sh && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python results/F/jev_cmp/sessions/S7_20261008/s7_prep.py`(항목 스크립트 `raw/js/iNNN_*.js` 80개, 무클릭 `dry_i001_T9_row00.js`·`dry_i021_T9_row20.js`·`dry_i029_T9_row28.js`·`dry_i041_T10_row00.js`(`raw/js/`는 공개 저장소에는 포함하지 않음), `raw/run_plan.json`. state = Laya `serialize_state` = `json.dumps(state, ensure_ascii=False)` 80/80, 옵션 = `render_options(Agent._to_internal(q))` 80/80, T10 옵션 = `"key: description"` 렌더링 40/40, T9 noul criteria 없음 40/40, body ≤ 3,000자, 입력에 중단 문구 정규식 일치 0을 assert). 브라우저: Playwright MCP `browser_navigate https://jevplayground.com/` → `browser_run_code_unsafe raw/js/instrument.js`(S5 계측 + 버전 태그 S7 + 세션 상한 90) → dry run 4회(+ 폼 snapshot 2) → 항목마다 `browser_run_code_unsafe raw/js/iNNN_*.js`(폼 입력 → `window.__jev.ready(sha12, 15000)` → 해시·간격·상한이 맞을 때만 `button.run-button` 클릭) → `browser_evaluate window.__jev.dump()`를 `raw/rNNN_<T9|T10>_rowRR.json`(공개 저장소에는 포함하지 않음)으로 저장 → `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python …/s7_record.py RUN ITEM`(= `jev_cmp.py record S7 <SET> RUN DUMP --row R` + 중단 조건 분류). 분석: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S7 T9_enron_spam_40`, `… analyze S7 T10_support_tickets_queue_40`(출력 `raw/analyze/T9.md`, `T10.md`, 공개 저장소에는 포함하지 않음) |
| 환경 기록 | 로컬 모델 실행·평가 없음(GPU 학습 진행 중). `s7_prep.py`는 laya의 `Agent._to_internal`·`render_options`·`serialize_state`만 쓰고 체크포인트를 로드하지 않는다. 브라우저는 Playwright MCP Chromium, 대상은 jevplayground.com `POST /api/evaluate`. Laya 수치는 vanilla 리포트(`results/T3arm/vanilla/`, laya 0.3.23, device cpu)에서 읽었다 |
| 체크포인트 | Jev: 응답 `model`과 View details Model ID `typesafe-ai/jev` 80/80, 버전 미표기. Laya english / multilingual revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`(리포트 config.revisions). Router는 T9·T10 80행 모두 english |
| 데이터셋 | T9: `data/evals/jev_cmp/T9_enron_spam_40.jsonl`, n=40(true 20 / false 20), `SetFit/enron_spam` test @1916f66c, dataset_sha256 `3ba26d0895e28f0a856e997c27103cbda88b6bc3c4252649d1d69f36cd6b8303`, questions_sha256 `efe610280673d5f90948552b0428277c6a9ab25434e447e62eedcaa1610fb318`, 폼 sha256 `d3a597c223e3b2321d989548118dc56aa9378644f1585ee6255f112fb604ce7d`. T10: `T10_support_tickets_queue_40.jsonl`, n=40(큐당 4), `Tobi-Bueck/customer-support-tickets` @ddf1c81a(hash test 몫), dataset_sha256 `e2c573561b8336dc4ba282f015c56617eb1c2aafd3042d7ad470833104236f40`, questions_sha256 `8fadd3f6b2a4436087c97e0538a2d2f3a37e82051f090d83b19ee11868952a60`, 폼 sha256 `a075d6ac0fc96029deb2e7d326ad62a0152553a5a8f39d4f50459e72c240962d`. 두 파일 해시가 MANIFEST와 같고, Laya 리포트 6개 모두 폼 파일과 dataset_sha256 · questions_sha256이 같다. 학습 믹스: 둘 다 Laya in training(BENCHMARKS.md:142, :147) |
| 디바이스 / 정밀도 / 스레드 | Jev: hosted, 미상. Laya: vanilla 리포트 기준 CPU fp32, intra-op 10 / inter-op 1, batch 8 |
| 파라미터 | Part A: Single question / Boolean. Question `Is this email unsolicited spam or bulk marketing?`, State = `{"subject", "body"}`(최대 2,117자, body 최대 1,984자). Part B: Single question / Choice. Question `Which support queue should handle this ticket?`, 옵션 10개 `key: description`(30\~73자, 모든 행 같은 목록·같은 순서), State 최대 781자. 운영: 처음부터 monotonic 기준 Run 간격 가드 15 s(규칙 ≥ 10 s), 5xx면 65 s 뒤 같은 항목 1회 재시도(`next_gap`), 재시도도 실패하면 종료, 429·제한 문구·captcha는 재시도 없이 즉시 중단. 세션 상한 90(계획 80 + 재시도 여유), 계측에서 Run 클릭 90회 이상이면 클릭 차단 |
| 반복 / warm-up | 단일 패스, warm-up 없음. 항목당 1회, 재시도 0(run 번호 = 항목 번호) |
| 소요 시간 | 브라우저 세션 약 22분(15:21:49\~15:43:55), 평가 구간 20분 28.6초(첫 클릭\~마지막 클릭). 기록된 구간 15:18:38\~15:55 약 36분(준비·회귀 약 3분, 브라우저 22분, 분석·문서 약 11분). 자료 읽기 시간은 시작 시각을 기록하지 않아 빠져 있다 |

## 결과

| 지표 | 값 | upstream 참고치 (출처) | 차이 | 비고 |
|---|---|---|---|---|
| noul_accuracy (T9, p(true) ≥ 0.5) | Jev 40/40 = 1.000 [0.912, 1.000]; Laya english · multilingual · Router 모두 40/40 = 1.000 [0.912, 1.000] | Laya english 0.993 / multilingual 0.993 (BENCHMARKS.md:142 Themes Email spam, N=400, in training). vanilla ext500 0.992 / 0.990 (`PREP_20261008.md` §5) | english +0.007 | 천장. Jev 공개치 없음 |
| 예측 양성률 (T9, gold 20/40) | Jev 20, english 20, multilingual 20, Router 20 | n/a | | FP 0 / FN 0 모두 |
| AUROC p(true) (T9) [bootstrap 95%] | 네 시스템 모두 1.000 [1.000, 1.000](완전 분리, CI 퇴화). 차이 0 | n/a | | 항목 재표본 2,000회, seed 13 |
| McNemar (exact, b/c) | T9: 세 쌍 모두 0/0, p=1.0. T10: vs english 3/5 p=0.7266, vs multilingual 4/12 p=0.0768, vs Router 3/5 p=0.7266 | n/a | | T10 Router = english(40/40 english) |
| choice_accuracy (T10) | Jev 10/40 = 0.250 [0.142, 0.402]; english 12/40 = 0.300 [0.181, 0.454]; multilingual 18/40 = 0.450 [0.307, 0.602]; Router 12/40 = 0.300 | Laya english 0.502 / multilingual 0.522 (BENCHMARKS.md:147, 영어 앞 400행 자연 분포, in training). vanilla ext500 큐 균등 0.264 / 0.454 (`PREP_20261008.md` §5) | 비교 불가(표본 분포 다름) | 큐당 4행이라 큐별 수치는 방향 신호. Jev 공개치 없음 |
| Brier | T9: Jev 0.019, english 0.005, multilingual 0.000, Router 0.005. T10: Jev 1.319, english 0.775, multilingual 0.611, Router 0.775 | n/a | | T9는 2(p − y)², T10은 행별 옵션 10개 Σ(p − onehot)². Jev 확률 2자리 반올림 |
| ece | T9: Jev 0.060 (english 0.014, multilingual 0.000). T10: Jev 0.623 (english 0.253, multilingual 0.215) | Laya 리포트 overall과 같음 | | 15 bins, top p 기준 |
| mean_confidence (Jev 표시 top p) | T9 0.940(100% 표시 0/40, 서로 다른 p(true) 16개, gold true 최소 0.58 / gold false 최대 0.09). T10 0.873(정답 0.861 / 오답 0.877), 100% 표시 8/40, 오답 중 top ≥ 0.90 18/30, **정답 옵션 0% 표시 20/40** | Jev 제3자 zero-probability 실패 16%(Emotion, bench_apps.py `JEV_PUBLISHED`) | T10 +34%p | provider confidence: T10 40/40(평균 0.859, top p와 같은 값 18/40), T9 0/40 |
| latency (Jev 표시 "server + network" = latencyMs) | median T9 214.5 (169\~388), T10 226 (154\~311), 전체 219 ms | Jev 제3자 p50 236\~276 ms (09 §1) | 범위 아래 또는 근처 | 표시 = latencyMs half-up 80/80 |
| latency (브라우저 POST / 클릭 → 완료) | T9 481.5 / 482.5, T10 495 / 496.5 ms (median) | n/a (하드웨어·네트워크 다름) | | POST − latencyMs 중앙 239.0 ms. POST 최대 1,243 ms(Jev의 항목별 출력은 공개 저장소에서 생략) |
| 토큰 (View details) | T9 입력 427 (309\~1,059) / 출력 20(고정); T10 입력 681.5 (613\~739) / 출력 191 (185\~194) | n/a | | 합계 입력 46,313 / 출력 8,444. T9 입력 토큰과 state 길이 r = 0.964 |

## §7.3 세션 필드

| 항목 | 값 |
|---|---|
| 사이트 상태 확인 | 15:21:49 페이지 정상 로드, 15:21:52 계측 설치 시 body 제한 문구 검사 결과 없음(`Free to try · Usage limits apply` 고정 문구는 정규식에 걸리지 않음). UI · DOM id가 S5와 같다(Single question 기본, Decision type group, Boolean 선택 시 "YES / NO — Jev returns P(true). The probability of "No" is its complement." 라벨·설명 칸 없음, `raw/mcp/snapshot_dry_i029_T9_row28_form.yml`, 공개 저장소에는 포함하지 않음). 지시에 따라 기본 예시는 실행하지 않았다(사이트 이용은 80개 항목뿐) |
| 요청 수 | `POST /api/evaluate` 80회 = Part A(T9) 40 + Part B(T10) 40, 모두 HTTP 200. 성공 80 / 실패 0, 5xx 0, 4xx 0(429 0), 재시도 0. 세션 상한 90 중 80. 네트워크 목록: POST 80(전부 `/api/evaluate`, 200), GET 58(문서 1, 정적 31, Next.js RSC prefetch 26 = 13개 경로 × 2, 모두 200). RSC prefetch는 사이트 클라이언트가 화면의 링크를 미리 받는 요청이고 페이지 이동은 없었다 |
| 요청 없는 클릭 | 0. 무클릭 dry run 4회(item 1, 21, 29, 41)는 폼 입력과 해시·DOM 대조만 했다. 스크린샷용 View details는 클릭 없이 DOM에서 `details.open = true`로 열었다(4회). resource timing `/api/evaluate` 80건 = Run 클릭 80회, 클릭 → fetch 시작 0\~3 ms |
| 간격 | monotonic 기준 79개 간격: 최소 15.009 s, 중앙 15.134 s, 최대 22.770 s(run 2: run 1 스크린샷 뒤). Part A 15.012 / 15.133 / 22.770, Part B(run 41 포함) 15.009 / 15.149 / 19.024(run 42: run 41 스크린샷 뒤, run 41은 파트 경계 18.7 s). resource timing 시작 간격 15.008 / 15.134 / 22.768 s |
| Model ID / 토큰 범위 | `typesafe-ai/jev` 80/80. 입력 309\~1,059, 출력 20\~194. `rounding` {probabilityDecimals 2, scoreDecimals 2}, `warnings` [] 80/80. provider `confidence.decision`은 T10 40/40(top p와 같은 값 18/40), T9 0/40(S3 T5 · S5 T8의 Boolean과 같다) |
| 입력 해시 대조 | 요청 전 sha12 80/80 일치(`window.__jev.ready`). 요청 후 request body가 폼 파일 payload와 바이트 단위로 80/80 같다(`payload_exact`, payload 224\~2,284 bytes T9, 1,378\~2,051 bytes T10). dry run 4회는 추가로 폼 값 = 입력 문자열(State · Question · 선택지 10개)과 길이·`maxLength`(State 8,000, Question 2,000, 선택지 80)·카운터("2,117 / 8,000" 등)를 확인했다(`raw/dry_runs.json`) |
| 파싱 실패 | 0. T10 choice 40개는 답이 입력 라벨 중 하나와 정확히 같고 확률 키 집합이 라벨 10개와 같다. T9 Boolean 40개는 답이 `{type, probability}`이다. 화면 DECISION · 막대 % = 응답 80/80 |
| 오류 문구 | 없음. 429 · 제한 문구 · captcha · "temporarily unavailable" 0건(dump 80개와 세션 끝 `body_stop_match` null, alerts [], captcha iframe 없음). 콘솔은 경고 182건(전부 CSS preload)이고 오류 0건 |
| Laya 대응 리포트 | `results/T3arm/vanilla/T9_enron_spam_40_{english,multilingual,router}.json`(questions_sha256 `efe61028…`), `T10_support_tickets_queue_40_{english,multilingual,router}.json`(`8fadd3f6…`). Router는 두 세트 모두 40/40 english |
| 오늘 누적 사이트 사용량 | 80(2026-10-08은 S7뿐, master의 `date` 20261008 행 80). 사이트 전체 누적 518 = 438 + 80. master `jev_runs_all.jsonl` 491줄 |
| 비용 | n/a. Jev 단가는 확인하지 않았다. 토큰 합계 입력 46,313 / 출력 8,444 |

## 산출물

- `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md`: T9 · T10 결과(정확도, McNemar, AUROC, 양성률, 보정, 확신도, 오류 구조), 지연 · 토큰, 관찰과 한계
- `results/F/jev_cmp/sessions/S7_20261008/S7_requests.jsonl`(80줄), `results/F/jev_cmp/jev_runs_all.jsonl`(master 491줄. 앞 634,031 bytes = 411줄은 S7 전 사본과 바이트 동일(sha256 `648c879f272698173f56f5dd0957eb132d1306e997e3ac00575caf95dcb35aed`), 뒤 80줄은 `S7_requests.jsonl`과 바이트 동일) (두 파일은 공개 저장소에는 포함하지 않음)
- `raw/`: dump 80(`rNNN_<T9|T10>_rowRR.json`), `run_plan.json`, `dry_runs.json`, `js/`(instrument, 항목 스크립트 80, dry run 4), `evaluate_timing_all.json`, `network_requests.txt`, `network_requests_all.txt`, `console.log`, `mcp/`(페이지 로드 snapshot, dry run 폼 snapshot 2, MCP 콘솔 로그), `analyze/`(`T9.md`, `T10.md`) (이 중 `run_plan.json`·`dry_runs.json` 외에는 공개 저장소에는 포함하지 않음)
- `shots/`: Part A · B 각 첫 · 마지막 run(View details 열림, full page) 4장(공개 저장소에는 포함하지 않음)
- `s7_prep.py`, `s7_record.py`
- `results/F/jev_cmp/jev_cmp.py`: Laya 리포트 경로를 T9 · T10만 `results/T3arm/vanilla/`로 보게 한 최소 수정(아래)

## 이상 / 주석

- **오류 없음.** 5xx · 429 · 제한 문구가 없어 재시도 규칙(65 s 뒤 1회)과 중단 규칙은 발동하지 않았다.
- **입력 동일성(dry run 먼저).** 첫 요청 전에 무클릭 dry run 4회를 했다: 각 파트 첫 항목(item 1 T9 row 0, item 41 T10 row 0), T9 최장 state(item 29 row 28, 2,117자), C1 제어문자 U+0092가 든 T9 state(item 21 row 20). 4회 모두 폼 값이 입력 문자열과 같고 잘림이 없었으며(State maxLength 8,000, 선택지 maxLength 80, 최장 라벨 73자) sha12가 맞았다. 그래서 변환 없이 진행했다. U+0092는 원 데이터의 문자이고(Windows-1252 오른쪽 작은따옴표가 잘못 디코딩된 것으로 보임, 확인 필요) Laya가 읽는 문자열에도 그대로 있다. textarea와 `JSON.stringify`를 거쳐도 보존됐다(run 21 body 바이트 대조 일치).
- **T9 옵션 칸.** 폼 파일의 T9 `options`("false: no, the statement does not hold", "true: yes, the statement holds")는 Laya가 noul에서 읽는 렌더링이다(`render_options`, criteria 없음). Jev Boolean에는 라벨 · 설명 칸이 없으므로 두 시스템 모두 질문 문장만 받는 T5 · T8과 같은 조건이다.
- **`jev_cmp.py` 변경(최소).** `analyze`가 Laya 리포트를 `results/F/jev_cmp/laya/`에서만 읽었으므로, T9 · T10 접두사만 `results/T3arm/vanilla/`로 보내는 `LAYA_DIRS`(`jev_cmp.py:41-42`)와 `laya_report()`(`:308-309`)를 더하고 `laya_cases`(`:313`)와 `request_lines`의 경로 표시(`:467`)가 이를 쓰게 했다. `laya/`에는 파일을 복사하지 않았다. 회귀: 변경 전후 `analyze S1 T2`, `S2 T3`, `S3 T4`, `S3 T5`, `S4 T6`, `S4 T7 en`, `S4 T7 en,de`, `S5 T7 ja · zh-CN · ko`, `S5 T8`, `S4,S5 T7 5개 언어`, `stability S1 S1b T2`, `t1 S1,S2` 14개 출력이 바이트 동일하고, `S5 T8`은 S5의 `raw/analyze/T8.md`와도 같다.
- **계측 변경(최소).** `instrument.js`는 S5와 같고 버전 태그(S7)와 세션 상한(90)만 바꿨다(diff 3줄). 항목 스크립트의 클릭 경로는 S5와 같다. dry run(`click: false`)에서만 폼 DOM 상태를 읽어 돌려주는 읽기 전용 블록을 더했다(`s7_prep.py` DRIVER). 80회에서 끝나 상한은 발동하지 않았다.
- **호스트 wall clock.** wall − mono 오프셋 −1 \~ +1 ms, 스텝 없음. `click_epoch_ms` · `click_kst`는 S3\~S5와 같이 monotonic 축 값이다.
- **세션 중 다른 프로세스의 파일 변경(이 세션의 변경 아님).** `results/F/jev_cmp/__pycache__/s6_summary.cpython-312.pyc`가 15:18:14에 생겼고, `docs/00_README.md`(15:24:47), `docs/09_laya_vs_jev_plan.md` · `docs/11_three_arm_plan.md`(15:28:07), `docs/10_paper_laya_vs_jev.md` · `.pdf`(15:37:39 · 15:37:43, PDF는 공개 저장소에는 포함하지 않음)가 수정됐다. 이 세션은 `docs/`를 읽기만 했고 Python은 모두 `PYTHONDONTWRITEBYTECODE=1`로 돌렸다. 09 §2 운영 규칙과 §7.3 필드는 수정 뒤에도 같은 내용이다.
- **해석이 들어간 판단(확인 필요).** T10 오답 중 다수에서 gold 큐가 두 시스템에 준 큐 설명과 맞지 않는다고 본 것은 티켓을 읽고 내린 판단이다. 채점은 데이터셋 라벨 그대로 했다.
- `data/`, `docs/`, `results/T3arm/`, `results/F/jev_cmp/laya/`, `summary.*`, `s6_summary.py`는 편집하지 않았다. 레포 루트의 Playwright MCP 출력 디렉터리(페이지 로드 snapshot 1, 콘솔 로그 1)는 `raw/mcp/`로 복사한 뒤 삭제했다.

## 다음 액션

- 3-arm 종합에 T9 · T10 Jev 열 반영(이 세션 범위 밖. F 종합 T1-T8은 고정이라 `summary.*`는 건드리지 않았다).
- T10 gold 품질 점검(확인 필요): 40행 중 세 시스템 모두 틀린 행이 18개다. 큐 설명과 gold가 어긋나는 행을 사람이 다시 라벨링하거나, 데이터셋 카드에서 큐 라벨 생성 방식을 확인해야 T10 정확도를 "라우팅 능력"으로 읽을 수 있다.
- T9는 네 시스템 모두 40/40이라 변별력이 없다. 차이를 보려면 더 어려운 held-out spam 표본이 필요하다(Jev 요청 필요, 프로젝트 책임자 결정).

## 후속 수정 (2026-10-08 16:40)

- **증상.** S7이 master `jev_runs_all.jsonl`에 80줄을 붙인 뒤 `results/F/jev_cmp/s6_summary.py build`가 `master log != concatenation of the session request logs`로 실패했다. `master_records()`가 master를 S1-S5 로그를 이은 것과 같다고 검사했기 때문이다. F verify는 이 함수를 쓰지 않아 영향이 없었다.
- **수정.** `s6_summary.py:121-123`이 "master가 S1-S5 로그로 시작한다"를 검사하고 그 앞부분만 돌려준다. F 종합의 범위는 그대로 S1-S5다. 3-arm 종합은 `t3arm_summary.py`에서 `S6.SESSIONS`에 S7을 더해 전체를 읽는다.
- **확인.** 수정한 build를 scratch로 돌린 출력이 기존 F 출력과 같다. `summary.md`와 PNG는 바이트 동일하고, `summary.json`은 `built_kst` 한 줄만 다르다. SVG는 날짜 메타데이터와 matplotlib clip-path ID만 다르다. `s6_summary.py verify`는 no mismatches이고, F 출력 파일은 다시 쓰지 않았다(mtime 10-07 16:42 유지).

[English](S7_run_card.md) | **한국어**
