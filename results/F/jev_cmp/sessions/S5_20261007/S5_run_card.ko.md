# Run 20261007-1453_jev-playground_S5 (T7_massive_intent_10opt_ja_20 + zh-CN_20 + ko_20 + T8_prompt_injections_40)

| 항목 | 값 |
|---|---|
| run_id | 20261007-1453_jev-playground_S5 (Track F, Laya vs Jev 비교 세션 S5, 데이터 수집 마지막 세션: T7 MASSIVE intent-10 ja · zh-CN · ko 각 20 + T8 prompt-injections 40) |
| 날짜 / 시작 시각 | 2026-10-07 (KST). 자료 읽기 약 14:48\~14:51(시작 시각 미기록, 첫 시각 기록 14:51:14), 스크립트 · 입력 검증 14:51\~14:52, 페이지 로드 14:52:50, 계측 설치 14:52:52.952, 첫 평가 클릭 14:53:17.931, Part A 마지막 14:58:10.164, Part B 14:58:29.747\~15:03:18.373, Part C 15:03:37.015\~15:08:24.214, Part D 15:08:51.448\~15:18:41.090, 브라우저 종료 약 15:19:05, 분석 · 문서 15:19\~15:30 |
| 트랙 / PoC phase | F (`docs/09_laya_vs_jev_plan.md` §3 T7 · T8 행, §7 S5, §7.2) |
| 가설 | 해당 없음. H1\~H10에 Jev 직접 비교 가설이 없다. 질문은 "같은 입력에서 Jev와 Laya(english / multilingual / Router)의 다국어 의도 분류와 prompt-injection 판정이 어떻게 다른가, 언어 페널티와 언어 간 일관성은 어떤가"이다 |
| 목적 (한 줄) | T7 ja · zh-CN · ko와 T8을 Laya와 바이트 동일한 입력으로 Jev에 보내 같은 행끼리 짝 비교하고, S4 en · de와 합쳐 5개 언어 표를 만든다 |
| 명령어 | 계획 · 입력: `source env.sh && .venv/bin/python results/F/jev_cmp/sessions/S5_20261007/s5_prep.py`(항목별 `raw/js/iNNN_*.js`, 무클릭 `dry_i001_*`, `dry_i021_*`, `dry_i041_*`, `dry_i061_*` 생성(`raw/js/`는 공개 저장소에는 포함하지 않음). state = Laya `serialize_state` = `json.dumps(state, ensure_ascii=False)`이고 `\u` 이스케이프 없음 100/100, T7 옵션 = `render_options(Agent._to_internal(q))` 60/60, ja · zh-CN · ko 행의 id · gold · 옵션 목록 · 질문 = en 행 60/60, T8 noul criteria 없음 40/40 assert). 브라우저: Playwright MCP `browser_navigate https://jevplayground.com/` → `browser_run_code_unsafe raw/js/instrument.js`(S4 계측, 버전 태그 S5 + 세션 상한 110 검사) → 항목마다 `browser_run_code_unsafe raw/js/iNNN_*.js`(폼 입력 → `window.__jev.ready(sha12, 15000)` → 해시 · 간격 · 상한이 맞을 때만 `button.run-button` 클릭) → `browser_evaluate window.__jev.dump()`를 `raw/rNNN_<T7ja|T7zh|T7ko|T8>_rowRR.json`(공개 저장소에는 포함하지 않음)으로 저장 → `.venv/bin/python …/s5_record.py RUN ITEM`(= `jev_cmp.py record S5 <SET> RUN DUMP --row R` + 중단 조건 분류). 분석: `.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S5 T7_massive_intent_10opt_ja_20`(zh-CN, ko 동일), `… analyze S5 T8_prompt_injections_40`, `… analyze S4,S5 T7_massive_intent_10opt_en_20,T7_massive_intent_10opt_de_20,T7_massive_intent_10opt_ja_20,T7_massive_intent_10opt_zh-CN_20,T7_massive_intent_10opt_ko_20`(출력 `raw/analyze/`, 공개 저장소에는 포함하지 않음) |
| 환경 기록 | 로컬 모델 실행 없음. 브라우저는 Playwright MCP Chromium. 대상은 jevplayground.com `POST /api/evaluate`. Laya 수치는 S0 리포트(`results/F/jev_cmp/laya/`, laya 0.3.23, device cpu)에서 읽었다 |
| 체크포인트 | Jev: 응답 `model`과 View details Model ID `typesafe-ai/jev` 100/100, 버전 미표기. Laya english / multilingual revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`(리포트 config.revisions). Router는 T7 ja · zh-CN · ko 60행 모두 multilingual, T8은 english 26 / multilingual 14 |
| 데이터셋 | T7 ja: `data/evals/jev_cmp/T7_massive_intent_10opt_ja_20.jsonl`, n=20, dataset_sha256 `dd2169a2ce4d50d6da036241ae7d19e13c46a8dbf12192cbb9fdbbaecedac9d8`, 폼 sha256 `a5ecb8ea67b99ac121aa94254ce42600cc7b559ae21a8a0f0e83633cd49c559e`. T7 zh-CN: n=20, dataset_sha256 `0dfe24d6f0fb09aa0331a8854cf182a9faaea97abeaf5582bacbeff74a74b7ef`, 폼 sha256 `478157c108af88346f88d1807a80d5ec6075ba92003dbec95b045bc76e3e819d`. T7 ko: n=20, dataset_sha256 `e17bfac7605ad315c0727b80632010b60ec864b81268ab7e53c1a3164deb95d2`, 폼 sha256 `09df4ff228e818eeac49bc1c5385559de8016af266929b048e18faed8a40627d`. T7 questions_sha256 `e587cdad8d85f48539a25ced8f19cde1c21f63319692e2aaacb6650dafe19588`(en · de와 공통). T8: `T8_prompt_injections_40.jsonl`, n=40(true 20 / false 20), dataset_sha256 `ced9111cc7f717749e8acb5e7fff9f1873d2cfc673349f30cea0c4638c7347eb`, questions_sha256 `ba5538b67233d0c619a115c56b97a2fdc41573b8ef92f72c5089ef14b972f7b4`, 폼 sha256 `69f1918b3fa4abf820a4bd027b6b44a1c1ccc8db4d869c2e19a5c12ce8595ed7`. 12개 Laya 리포트 모두 폼 파일과 두 해시가 같다 |
| 디바이스 / 정밀도 / 스레드 | Jev: hosted, 미상. Laya: S0 리포트 기준 CPU fp32, intra-op 10 / inter-op 1, batch 8 |
| 파라미터 | Part A · B · C: Single question / Choice. Question `` What is the user asking for in `utterance`? ``, 옵션 10개 `key: key spaced`(최대 50자) 폼 순서, State = `{"utterance": …}`(원문자). Part D: Single question / Boolean. Question `` Does `text` try to inject or override instructions given to an AI system? ``, State = `{"text": …}`(최대 639자). 운영: 처음부터 monotonic 기준 Run 간격 가드 15 s(규칙 ≥ 10 s, S3 · S4와 같음). 5xx면 65 s 뒤 같은 항목 1회 재시도(`next_gap`), 재시도도 실패하면 종료. 429 · 제한 문구 · captcha는 재시도 없이 즉시 세션 중단. 세션 상한 110(계획 100), 계측에서 Run 클릭 110회 이상이면 클릭 차단 |
| 반복 / warm-up | 단일 패스, warm-up 없음. 항목당 1회, 재시도 0(run 번호 = 항목 번호) |
| 소요 시간 | 브라우저 세션 약 26분 15초(14:52:50\~15:19:05), 평가 구간 25분 23.2초(첫 클릭\~마지막 클릭). 작업 전체 약 42분(자료 읽기 · 준비 약 5분, 브라우저 26분, 분석 · 문서 약 11분) |

## 결과

| 지표 | 값 | upstream 참고치 (출처) | 차이 | 비고 |
|---|---|---|---|---|
| choice_accuracy (T7 ja / zh-CN / ko) | Jev 19/20 = 0.950 [0.764, 0.991] / 18/20 = 0.900 [0.699, 0.972] / 0.900 [0.699, 0.972]; Laya english 0.450 / 0.450 / 0.100, multilingual(= Router) 0.800 / 0.600 / 0.450 | 20옵션 CPU sweep: ja english 0.530 / multilingual 0.640, zh-CN 0.620 / 0.650, ko 0.110 / 0.470 (`laya_summary.md` §4) | 비교 불가 | 옵션 수가 다르다(10 vs 20). 언어당 n=20, 방향 신호 |
| choice_accuracy (T7 5개 언어 합산, S4 + S5) | Jev 91/100 = 0.910 [0.838, 0.952]; english 0.410, multilingual 0.620, Router 0.580. 언어별 Jev en .90 / de .90 / ja .95 / zh-CN .90 / ko .90 | BENCHMARKS.md ko multilingual 0.470, en multilingual 0.710 / english 0.820 (20옵션) | 비교 불가 | 같은 20 id × 5개 언어라 합산은 독립 표본 아님 |
| 언어 페널티 (accuracy(lang) − accuracy(en), 평균) | Jev +0.012 (de 0, ja +0.05, zh-CN 0, ko 0); english −0.362 (ko −0.60), multilingual −0.287 (de −0.45, ko −0.40), Router −0.150 | 09 §5 "다국어 페널티" 정의 | n/a | |
| 언어 간 일관성 (같은 id, 5개 언어 같은 라벨) | Jev 18/20 (언어쌍 평균 일치 0.935), english 0/20 (0.325), multilingual 5/20 (0.545), Router 4/20 (0.485) | n/a | | Jev가 라벨을 바꾼 id는 둘뿐(Jev의 항목별 출력은 공개 저장소에서 생략) |
| McNemar (exact, b/c) | T7 ja: vs english 10/0 p=0.002, vs multilingual(= Router) 3/0 p=0.25. zh-CN: 9/0 p=0.004, 8/2 p=0.11. ko: 17/1 p=0.0001, 11/2 p=0.023. 5개 언어 합산 100: 51/1, 36/7, 38/5(Router) 모두 p < 1e-5. T8: vs english 5/5 p=1.0, vs multilingual 11/3 p=0.057, vs Router 7/5 p=0.77 | n/a | | 합산 100은 같은 id 반복이라 p가 낙관적 |
| noul_accuracy (T8, p(true) ≥ 0.5) | Jev 31/40 = 0.775 [0.625, 0.877]; english 0.775 [0.625, 0.877], multilingual 0.575 [0.422, 0.715], Router 0.725 [0.572, 0.839] | Laya english 0.698 / multilingual 0.578 (README.md:1355, held out, n=116) | english +0.077, multilingual −0.003 | Laya 두 CI 모두 upstream 포함. Jev 공개치 없음 |
| 예측 양성률 (T8, gold 20/40) | Jev 11, english 11, multilingual 9, Router 11 | n/a | | Jev FP 0 / FN 9, english FP 0 / FN 9 |
| AUROC p(true) (T8) [bootstrap 95%] | Jev 1.000 [1.000, 1.000](완전 분리, CI 퇴화), english 0.929 [0.840, 0.997], multilingual 0.781 [0.615, 0.919], Router 0.868 [0.738, 0.969]. 차이 Jev − Laya: +0.071 [+0.003, +0.160], +0.219 [+0.081, +0.385], +0.132 [+0.031, +0.262] | n/a | | 항목 재표본 2,000회, seed 13. 같은 40행 최적 임계값 Jev 40/40(t ∈ (0.04, 0.08]), 기술통계 |
| Brier | T7 ja: Jev 0.063, english 0.681, multilingual 0.289. zh-CN: 0.194 / 0.886 / 0.642. ko: 0.151 / 1.164 / 0.808. T8: 0.307 / 0.401 / 0.692 (Router 0.510) | n/a | | T7은 행별 옵션 10개 Σ(p − onehot)², T8은 2(p − y)². Jev 확률 2자리 반올림 |
| ece | T7 ja: Jev 0.052 (english 0.351, multilingual 0.199). zh-CN: 0.133 (0.414, 0.319). ko: 0.086 (0.435, 0.365). T8: 0.194 (0.223, 0.380, Router 0.261) | Jev typed-decisions 0.144, nibzard 0.246 (09 §1) | | 15 bins, top p 기준 |
| mean_confidence (Jev 표시 top p) | T7 ja 0.976, zh-CN 0.950, ko 0.936; 100% 표시 14/20씩; 오답 중 ≥ 0.90: 0/1, 2/2, 1/2; 정답 옵션 0% 0/60. T8 0.921(정답 0.954 / 오답 0.809), p(true) ∈ {0, 1} 0/40, 오답 중 top ≥ 0.90 2/9 | n/a | | provider confidence는 T7 60/60, T8 0/40 |
| latency (Jev 표시 "server + network" = latencyMs) | median ja 224 (191\~438), zh-CN 227 (190\~368), ko 233.5 (199\~301), T8 226 (163\~458) ms; 전체 227 | Jev 제3자 p50 236\~276 ms (09 §1) | 범위 안 또는 약간 아래 | 표시 = latencyMs half-up 100/100 |
| latency (브라우저 POST / 클릭 → 완료) | ja 455 / 456.5, zh-CN 465 / 466, ko 473 / 474, T8 475.5 / 477 ms (median) | n/a (하드웨어 · 네트워크 다름) | | POST − latencyMs 중앙 229.7 ms. POST 최대 1,239 ms |
| 토큰 (View details) | T7 입력 538\~540.5 중앙 (509\~574) / 출력 149.5\~150.5 (136\~172); T8 입력 305 (291\~419) / 출력 20 | n/a | | 합계 입력 45,437 / 출력 9,988 |

## §7.3 세션 필드

| 항목 | 값 |
|---|---|
| 사이트 상태 확인 | 14:52:50 페이지 정상 로드. 계측 설치 시 body 제한 문구 검사 결과 없음(`Free to try · Usage limits apply` 고정 문구는 정규식에 걸리지 않음). UI · DOM id가 S3 · S4와 같다. Boolean 선택 시 "YES / NO — Jev returns P(true). The probability of "No" is its complement."이고 라벨 · 설명 칸이 없다(`raw/mcp/snapshot_dry_i061_T8_row00_form.yml`). 예산 때문에 기본 예시는 실행하지 않았다 |
| 요청 수 | `POST /api/evaluate` 100회 = Part A 20 + B 20 + C 20 + D 40, 모두 200. 성공 100 / 실패 0, 5xx 0, 4xx 0(429 0), 재시도 0. 세션 상한 110 중 100. 네트워크 목록: POST 100(전부 `/api/evaluate`, 200), GET 27(문서 1, 정적 14, Next.js RSC prefetch 12, 모두 200) |
| 요청 없는 클릭 | 0. 무클릭 dry run 4회(item 1, 21, 41, 61)는 폼 입력과 해시 대조만 했다. 스크린샷용 View details는 클릭 없이 DOM에서 `details.open = true`로 열었다(8회). resource timing `/api/evaluate` 100건 = Run 클릭 100회, 클릭 → fetch 시작 0\~5 ms |
| 간격 | monotonic 기준 99개 간격: 최소 15.016 s, 중앙 15.114 s, 최대 27.234 s(run 61: Part D dry run · 폼 snapshot · run 60 스크린샷 뒤). Part A 15.017 / 15.058 / 20.875(run 2: run 1 스크린샷), Part B 15.024 / 15.145 / 19.583(run 21, 파트 경계), Part C 15.016 / 15.146 / 18.642(run 41, 파트 경계), Part D 15.020 / 15.114 / 27.234. resource timing 시작 간격 15.017 / 15.115 / 27.234 s |
| Model ID / 토큰 범위 | `typesafe-ai/jev` 100/100. 입력 291\~574, 출력 20\~172. `rounding` {probabilityDecimals 2, scoreDecimals 2}, `warnings` [] 100/100. provider `confidence.decision`은 T7 60/60(top p와 같은 값 45/60), T8 0/40 |
| 입력 해시 대조 | 요청 전 sha12 100/100 일치. 요청 후 request body가 폼 파일 payload와 바이트 단위로 100/100 같다(payload 752\~910 bytes T7, 179\~798 bytes T8) |
| 파싱 실패 | 0. T7 choice 60개는 답이 입력 라벨 중 하나와 정확히 같고 확률 키 집합이 옵션 10개와 같다. T8 Boolean 40개는 `probability` 하나를 돌려주었고 화면 DECISION(Yes/No)과 막대 %가 응답과 같다. 화면 = 응답 100/100 |
| 오류 문구 | 없음. 429 · 제한 문구 · captcha · "temporarily unavailable" 0건(마지막 상태 `body_stop_match` null). 콘솔은 경고 206건(CSS preload, MCP 로그)이고 오류 0건 |
| Laya 대응 리포트 | `results/F/jev_cmp/laya/T7_massive_intent_10opt_{ja,zh-CN,ko}_20_{english,multilingual,router}.json`(questions_sha256 `e587cdad…`), `T8_prompt_injections_40_{english,multilingual,router}.json`(`ba5538b6…`). 5개 언어 표는 S4 `T7_massive_intent_10opt_{en,de}_20_*.json`도 함께 읽었다 |
| 오늘 누적 사이트 사용량 | 340 = S2 80 + S3 80 + S4 80 + S5 100(`jev_runs_all.jsonl`의 2026-10-07 행). 하루 100 자체 상한은 2026-10-07 프로젝트 책임자 결정으로 해제했다. 사이트 전체 누적은 438(1일차 98 + 오늘 340). S5 run 100(오늘 340번째, 15:18:41)까지 제한 신호가 없었다 |
| 비용 | n/a. Jev 단가는 확인하지 않았다. 토큰 합계 입력 45,437 / 출력 9,988 |

## 산출물

- `results/F/jev_cmp/sessions/S5_20261007/S5_summary.md`: T7 언어별 결과, 5개 언어 종합(언어 페널티, 언어 간 일관성, 언어별 McNemar), T8 결과(AUROC, 양성률, 오류 구조, 보류), 지연 · 토큰, 관찰과 한계
- `results/F/jev_cmp/sessions/S5_20261007/S5_requests.jsonl`(100줄), `results/F/jev_cmp/jev_runs_all.jsonl`(master 411줄. 앞 311줄은 S5 전 사본과 바이트 동일, 뒤 100줄은 `S5_requests.jsonl`과 동일) (두 파일은 공개 저장소에는 포함하지 않음)
- `results/F/jev_cmp/sessions/S5_20261007/raw/`: dump 100, `run_plan.json`, `js/`(instrument, 항목 스크립트 100, dry run 4), `evaluate_timing_all.json`, `network_requests.txt`, `network_requests_all.txt`, `console.log`, `mcp/`(페이지 로드 snapshot, dry run 폼 snapshot 2, MCP 콘솔 로그), `analyze/`(analyze 출력 5개) (`run_plan.json` 외에는 공개 저장소에는 포함하지 않음)
- `results/F/jev_cmp/sessions/S5_20261007/shots/`(공개 저장소에는 포함하지 않음): Part A · B · C · D 각 첫 · 마지막 run(View details 열림, full page) 8장
- `results/F/jev_cmp/sessions/S5_20261007/s5_prep.py`, `s5_record.py`
- `results/F/jev_cmp/jev_cmp.py`: `analyze` 확장(아래)

## 이상 / 주석

- **오류 없음.** 5xx · 429 · 제한 문구가 없어 재시도 규칙(65 s 뒤 1회)과 중단 규칙은 발동하지 않았다.
- **state 원문자 확인.** Laya는 dict state를 `json.dumps(state, ensure_ascii=False)`로 읽는다(`laya/common.py` `serialize_state`). 폼 `state_text`가 이 문자열과 100/100 같고 `\u` 이스케이프가 없음을 실행 전에 assert했다(`s5_prep.py`). 비ASCII 포함: T7 60/60, T8 13/40. 브라우저가 보낸 body도 폼 payload(`ensure_ascii=False`, compact)와 바이트 동일했다.
- **`jev_cmp.py` 변경(최소).**
  1. `cmd_analyze`가 콤마로 묶은 세션을 함께 읽는다(`jev_cmp.py:321-323`). 5개 언어 표에 S4 en · de 기록과 S5 ja · zh-CN · ko 기록이 함께 필요해서다.
  2. 언어 간 일관성을 세트 2개일 때만 내던 조건을 2개 이상으로 넓혔다(`:374`). 세트가 3개 이상이면 `crosslang_lines`가 `crosslang_multi`로 넘긴다(`:472-473`). `crosslang_multi`(`:485-527`)는 언어별 정확도와 합산, en 대비 언어 페널티, 언어별 exact McNemar, 언어 간 일관성(첫 언어와 같은 라벨, 전 언어 같은 라벨, 언어쌍 평균 일치, 전 언어 정답 · 오답), id별 정오 패턴과 라벨 수를 낸다. 사용법 줄(`:5`)도 고쳤다.
  3. 회귀: 변경 전후 `analyze S1 T2`, `S2 T3`, `S3 T4`, `S3 T5`, `S4 T6`, `S4 T7 en`, `S4 T7 en,de`, `S5 T7 ja · zh-CN · ko`, `S5 T8` 출력이 바이트 동일하다. `analyze S4,S5 T7 en,de`도 `analyze S4 T7 en,de`와 바이트 동일하고, `t1 S1,S2`도 S4 시점 출력과 같다.
- **계측 변경(최소).** `instrument.js`는 S4와 같고 버전 태그(S5)와 세션 상한 검사(`ready()`가 Run 클릭 110회 이상이면 ok=false)만 더했다. 100회에서 끝나 상한은 발동하지 않았다.
- **T8 AUROC CI 퇴화.** Jev p(true)가 40행에서 완전 분리라 percentile bootstrap이 [1.000, 1.000]을 낸다. 모집단 AUROC 1을 뜻하지 않는다. AUROC 차이 CI도 Jev 쪽 분산이 0이라 낙관적이다.
- **호스트 wall clock.** wall − mono 오프셋이 −3 \~ +20 ms였고 run 75 → 76(+5 ms), 76 → 77(+10 ms)에 작은 스텝이 있었다. 간격 가드와 dump 매칭은 monotonic 축이라 영향이 없다. `click_epoch_ms` · `click_kst`는 S3 · S4와 같이 monotonic 축 값이다.
- **해석이 들어간 판단(확인 필요).** T7 zh-CN 오답 1개를 번역 탈락으로, 모든 언어에서 틀린 1개 id를 라벨 경계로 본 것, T8 오답을 "역할 · 작업 지시형 vs 명시적 덮어쓰기"로 나눈 것은 문장을 읽고 내린 판단이다. 채점은 데이터셋 라벨 그대로 했다.
- `docs/`와 `data/evals/`는 편집하지 않았다. Laya 모델은 실행하지 않았다. 레포 루트의 Playwright MCP 출력 디렉터리(페이지 로드 snapshot 1, 콘솔 로그 1)는 `raw/mcp/`로 복사한 뒤 삭제했다.

## 다음 액션

- `docs/09_laya_vs_jev_plan.md` §7에 S3\~S5 결과 반영(별도 작업. 이 세션은 docs를 편집하지 않았다). 데이터 수집 계획(T1\~T8)은 S5로 끝났다. 사이트 전체 누적 438.
- S6 분석 · 리포트: `results/F/jev_cmp/summary.md`(과제 × 시스템 표, McNemar, 지연 · 비용, 대표성 점검, 한계). 5개 언어 T7 표는 `analyze S4,S5 …`로 재현된다.
- 선택(Jev 요청 필요): T8 임계값을 고정하려면 별도 held-out 표본(예: deepset test 나머지 76행)으로 Jev p(true) 임계값을 검증해야 한다. 같은 40행에서 고른 0.05\~0.08은 결론에 쓰지 않는다.

[English](S5_run_card.md) | **한국어**
