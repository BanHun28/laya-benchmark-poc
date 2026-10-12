# 09. Laya vs Jev 소표본 비교 계획

**목적**: 같은 state, 같은 질문 문구, 같은 옵션 텍스트를 Laya와 TypeSafe Jev에 넣어 정확도·보정·견고성·지연·비용을 통제된 조건에서 비교한다. upstream은 Jev를 직접 측정하지 못해 제3자 공개 수치만 인용하므로(출처: BENCHMARKS.md 서두 "Jev figures are third-party published, never measured here", research/README.md "On comparisons with Jev") 이 비교가 이 벤치마크의 핵심 기여다. 언어 중립을 원칙으로 하되(영어 공개 데이터셋 우선), 다국어는 한 슬라이스로만 다룬다. zero-shot vs zero-shot 비교이며 Laya 파인튜닝(ft-v1)은 별도 선으로만 표기한다.
**선행 문서**: `00_README.md`(범위·가정), `01_laya_analysis.md`(Jev 공개 수치, Honest limits), `03_benchmark_plan.md` §10 Track F(F4 Jev 공개 수치, F5 파일럿), `04_korean_evalset_spec.md`(세트 포맷·빌더 규약), `06_templates.md`(run card). 파일럿: `results/F/jev_playground_manual_20261006.md`.
**산출물**: `data/evals/jev_cmp/*.jsonl` + `*_playground.json` + `MANIFEST.json`, `scripts/build_jev_cmp_sets.py`, 플레이그라운드 러너 규약(`results/F/jev_f.py` 확장), Laya 측정 요약 `results/F/jev_cmp/laya_summary.md`(S0), 세션 원기록 `results/F/jev_cmp/sessions/S<k>_<date>/`, 세션 run card `results/F/jev_cmp/S<k>_<date>.md`, 요청 마스터 로그 `results/F/jev_cmp/jev_runs_all.jsonl`(세션 원기록과 마스터 로그는 공개 저장소에는 포함하지 않음), 최종 비교 요약 `results/F/jev_cmp/summary.md`(S6), 소논문 v2(`docs/10_paper_laya_vs_jev.md` 또는 `08_paper_ko.md` 개정).

---

## 1. 배경과 파일럿 결과

Jev는 TypeSafe의 호스팅 결정 API다. Laya의 HTTP 서버는 Jev와 같은 `POST /v1/systemone` 프로토콜과 같은 응답 스키마(`choice`/`score`/`noul` 답, 확률, `usage`)를 제공하므로(출처: README.md "Self-Hosting: HTTP Server (Jev-compatible)"), API 키만 있으면 요청 하나를 두 엔드포인트에 그대로 보내는 완전한 동일 조건 비교가 가능하다. 그러나 이 프로젝트는 API 키 없이 진행하기로 결정했고(00 §5 항목 5), 접근 수단은 독립 제3자 사이트인 공개 플레이그라운드 https://jevplayground.com 뿐이다. 그래서 비교는 소표본·수동 속도로 설계한다.

파일럿(2026-10-06, `results/F/jev_playground_manual_20261006.md`)은 한국어 도메인 라우팅 24항목에서 다음을 보였다.

| 시스템 | 정답/24 | 정확도 (Wilson 95%) |
|---|---|---|
| Jev (플레이그라운드, `key: 설명` 라벨) | 20 | 0.833 [0.641, 0.933] |
| Laya zero-shot (multilingual) | 10 | 0.417 [0.245, 0.612] |
| Laya ft-v1 (파인튜닝) | 22 | 0.917 [0.742, 0.977] |

Jev vs zero-shot은 b=10, c=0, p=0.002로 유의했고, Jev vs ft-v1은 b=0, c=2, p=0.5로 구분되지 않았다. Jev 표시 지연 중앙값은 249.5 ms(server + network), 브라우저 왕복 약 500 ms였고, Laya 로컬 왕복은 20.1 ms였다(`results/poc/P2_20261003.md`). 이 파일럿은 한국어 한 과제뿐이라 "Laya vs Jev"의 일반 결론으로는 부족하다. 본 계획은 과제를 영어 공개 데이터셋 중심으로 넓히고 다국어를 한 슬라이스로 포함한다.

upstream이 인용하는 Jev 제3자 수치는 다음과 같다(출처: BENCHMARKS.md §Headline, §On the public datasets where Jev numbers exist, research/scripts/bench_apps.py `JEV_PUBLISHED`): AG News 0.910, Banking77 0.870(72 라벨), DAIR Emotion 0.480(정답 라벨 확률 0인 사례 16%), typed-decisions 0.727(soft 0.580, Brier 0.148, ECE 0.144, score MAE 0.391), ECE 0.246(nibzard), 옵션 순서 flip 0.13, p50 236\~276 ms. 우리 Jev 표본이 이 범위를 재현하는지가 표본 대표성 점검의 기준이다.

---

## 2. Jev 접근 제약과 운영 규칙

플레이그라운드에서 확인한 제약(2026-10-02, 10-06 열람): "Free to try · Usage limits apply", 간헐적 백엔드 502("Jev is temporarily unavailable"), 선택지 최대 10개, state 8,000자, Single question / Multiple questions 모드, 출력 확률은 소수 둘째 자리 반올림(100%/0%가 흔함), "View details"에 Model ID `typesafe-ai/jev`(버전 없음)·입출력 토큰·별도 confidence 표시, 화면의 "N ms · server + network"는 브라우저 왕복보다 짧다(파일럿: 표시 249.5 ms vs POST 497.5 ms). 추가로 **choice 입력 한 칸은 80자 제한**이다(`results/F/jev_playground_manual_20261006.md:34`, `scripts/build_jev_cmp_sets.py:44` `CHOICE_INPUT_CHARS = 80`).

80자 제한에 대한 결정(2026-10-06, S0 보고 후): (1) T4 Banking77-10은 v0의 `key: key spaced` 렌더링(최대 98자, 8/40 항목 입력 불가)을 버리고 upstream의 key 단독 렌더링(`k.replace("_", " ")`, 최대 48자, bench_apps.py:120-122)으로 **두 시스템 모두** 다시 만들었다. v0는 `T4_banking77_10opt_40_v0.jsonl`로 보관하고 MANIFEST에 `options_rendering: key-only`, `rebuild_reason`, `previous_version`을 기록했다(`data/evals/jev_cmp/MANIFEST.json`). (2) T1 typed-decisions는 customer_service/action 10개 decision의 옵션이 87\~89자라 Jev에 같은 바이트로 넣을 수 없으므로 그 10개에 `jev_excluded: true, reason: "option > 80 chars"`를 붙이고(JSONL 행의 `jev` 메타와 폼 항목, `build_jev_cmp_sets.py:45, :147`), Jev 비교는 나머지 190 decisions로 하기로 했으나, S1에서 아래 Score 제약이 확인되어 4레벨 score 70개를 추가로 제외했다(사유 `score levels != 5`). 최종 **Jev 비교 대상은 120 decisions**(choice 50, noul 60, 5레벨 score 10)이고 MANIFEST의 `jev_comparable_n`이 과제별 비교 대상 수다(T1 120, 그 외 n 전부; `jev_exclusion_rule`에 두 규칙 기록). Laya 수치도 120 기준을 병기한다(`results/F/jev_cmp/laya_summary.md` §2).

Multiple questions 모드 확인(S1 2026-10-06, `results/F/jev_cmp/sessions/S1_20261006/multi_question_mode.md`): (1) 한 run에 질문 2\~5개를 넣을 수 있고 Choice·Boolean·Score를 섞을 수 있으며 State는 하나를 공유한다. 결과는 질문별 카드(DECISION 또는 SCORE, 확률 분포)로 나오고 "N ms · server + network"는 run당 하나다. (2) **Score는 정확히 5레벨만 받는다.** 레벨 4개를 넣으면 "Enter a label." 오류로 요청 자체가 막히고, Single 모드도 같은 검증을 쓴다. T1 score 80개 중 70개가 4레벨이라 어느 모드로도 같은 입력을 보낼 수 없다. (3) **Boolean에는 라벨·설명 칸이 없다.** Laya의 noul `criteria`(true/false 설명)는 Jev에 전달되지 않는다. 공정성 점검으로 Laya에서 criteria를 뺀 변형을 측정한 결과 noul 정확도는 유의하게 변하지 않았다(english 0.467 → 0.517, McNemar p=0.549; multilingual 0.433 → 0.417, p=1.0; `laya_summary.md` §2b). (4) choice 라벨과 rubric 레벨은 80자에서 **오류 없이 잘려** 다른 라벨이 전송된다. (5) 요청 형식은 `{"state", "questions": {"q1": {"instructions", "type", "criteria"}}}`이며 choice는 `{라벨: 라벨}`, score는 문자열 5개, boolean은 criteria 없음이다. (6) 화면에 표시되는 Score는 E[level]에 가장 가까운 레벨이라 argmax와 다를 수 있다(Jev의 항목별 출력은 공개 저장소에서 생략). 따라서 T1·T6 score 규칙은 **argmax 레벨 정확도 + E[level] 기준 MAE**로 고정한다.

운영 규칙(모든 세션에 적용, run card에 요청 수 기록):

| 항목 | 규칙 |
|---|---|
| 속도 | 사람이 쓰는 속도. 요청 간격 10 s 이상 권장, 3 s 하한 |
| 양 | 1일차와 S2는 세션당 80 요청 이하, 하루 100 요청 이하. 2026-10-07 프로젝트 책임자 결정으로 하루 상한을 해제했고 이후 세션당 100 요청 이하(S5는 재시도 여유를 둔 하드캡 110). 자동 대량 호출 금지 |
| 오류 | 5xx, 제한 문구, 캡차가 보이면 즉시 중단. 60 s 뒤 그 항목만 1회 재시도, 재시도도 실패하면 세션 종료 |
| 기록 | 요청마다 입력 해시 대조, DOM/accessibility snapshot, "View details" 캡처(snapshot·캡처와 요청별 기록은 공개 저장소에는 포함하지 않음), 표시 지연과 브라우저 왕복, Model ID와 토큰 |
| 공개 | 결과를 공유할 때 "독립 플레이그라운드 경유, API 아님, 모델 버전 미표기, 소표본"을 반드시 명시 |
| 중복 | 같은 항목을 다시 보내는 것은 결정성 점검(§5)에 한해 10건까지 |

이 규칙은 파일럿의 운영(25 요청, 간격 최소 21.6 s, 502 1회, 재시도 0회)을 기준으로 정했다(`results/F/F_jev_20261006.md`).

**하루 상한 해제(2026-10-07, 프로젝트 책임자 결정).** 사이트는 수치 한도를 공개하지 않는다(홈 "Free to try · Usage limits apply", 개인정보 페이지 "abuse protection and rate limits"). 해제 전 178회 동안 429와 제한 문구는 0회였다. 간격 ≥ 10 s(실제 가드 15 s, monotonic 기준), 5xx 시 60 s 뒤 그 항목만 1회 재시도, 429·제한 문구가 보이면 재시도 없이 즉시 세션 중단이라는 규칙은 그대로 두었다. 해제 후 S3\~S5 260회를 포함해 2026-10-07 하루 340회 동안 429, 제한 문구, captcha는 나오지 않았다(§7.1c).

---

## 3. 과제와 표본

옵션 10개 제한 때문에 upstream의 Banking77(77 라벨), MASSIVE 20옵션 구성은 그대로 쓸 수 없다. 모든 과제를 옵션 10개 이하로 맞추고 Laya에도 같은 옵션을 준다. 과제당 n=40을 기본으로 한다. 아래 n은 S0에서 빌드한 실제 값이다(`data/evals/jev_cmp/MANIFEST.json`, 소스 revision 포함). Jev 실행 수는 T1을 Multiple questions 모드로 case당 1회 돌릴 때 기준이다.

| 과제 | 소스 (공개 test split) | 타입 / 옵션 | n | Jev 실행 | 비교 대상 공개 수치 | upstream 학습 믹스 |
|---|---|---|---|---|---|---|
| T1 typed-decisions | `LocalLLaMA/typed-decisions` all/test @d0e2f0c (parquet, `load_dataset` 직접 동작; 출처: research/scripts/build_benchmark_nb.py:329) | 혼합(choice·score·noul), case당 최대 5옵션 | 40 case / 200 decisions, **Jev 비교 120** (choice 50, noul 60, 5레벨 score 10; 제외 80 = 4레벨 score 70 + 80자 초과 10, §2) | 39 (A안: Multiple questions 모드, case당 1회, 4레벨 score 질문은 생략. row 30은 S1 탐색 run으로 완료) | Jev 0.727 / soft 0.580 / Brier 0.148 / ECE 0.144 / MAE 0.391; Laya base 0.362/0.352, ft 0.766 | 미포함 ("Neither checkpoint trained on typed-decisions", research/results/t4_colab_benchmark.json) |
| T2 AG News | `fancyzhx/ag_news` test @eb185aa | choice 4 | 40 (10×4) | 40 (+20 순열 프로브) | Jev 0.910, Laya 0.947\~0.953 | in training (README.md:1348-1356) |
| T3 DAIR Emotion | `dair-ai/emotion` split/test @cab853a | choice 6 | 40 (7,7,7,7,6,6) | 40 | Jev 0.480, Laya 0.573\~0.600 | held out (README.md:1354) |
| T4 Banking77-10 | `mteb/banking77` test @18072d2, gold + 9 distractor(seed 13), 옵션은 key 단독 렌더링(§2 결정 (b)) | choice 10 | 40 (정답 라벨 40종) | 40 | 직접 비교 불가(Jev 0.870은 72 라벨, Laya 0.425는 77 라벨). 10옵션 조건은 양쪽 모두 새 측정 | held out (bench_apps.py `in_training=False`, build_benchmark_nb.py:761) |
| T5 BoolQ | `google/boolq` validation @35b264d (test 라벨 비공개) | noul(Boolean) | 40 (20/20) | 40 | Laya 0.830/0.787. Jev 공개치 없음 | in training (README.md:1348-1356) |
| T6 SST-5 | `SetFit/sst5` test @e51bdcd | score 5 levels | 40 (8×5) | 40 | Laya 0.372/0.282(정확 레벨). Jev 공개치 없음 | held out |
| T7 MASSIVE intent-10 다국어 | `mteb/amazon_massive_intent` en·de·ja·zh-CN·ko test @940fd47, 같은 id, gold + 9(seed 13) | choice 10 | 20 × 5 = 100 | 100 | 20옵션 upstream 수치(multilingual ko 0.470 / en 0.710, english en 0.820; BENCHMARKS.md:71, :117)와는 옵션 수가 달라 방향만 비교 | held out (build_benchmark_nb.py:762 "Neither checkpoint trained on typed-decisions, MASSIVE or XNLI") |
| T8 prompt-injections (선택) | `deepset/prompt-injections` test @4f61ecb (출처: README.md "English tasks", n=116 held out) | noul | 40 (20/20) | 40 | Laya 0.698/0.578 | held out |

합계: T1\~T7 = 39 + 40 + 40 + 40 + 40 + 40 + 100 = 339 요청, 순열 프로브 20과 결정성 10을 더하면 369(이 중 S1·S1b에서 71회 완료). T8을 더하면 409이며 하루 100 상한 기준 5\~6일에 나눈다. 학습 믹스 표기의 근거는 BENCHMARKS.md의 Themes 표가 아니라 README.md:1348-1356("English tasks" 표의 in training / held out)과 research/scripts/build_benchmark_nb.py:760-762다.

표본 추출 규칙은 04 §5 공통 규칙을 따른다: seed 13, 레이블 층화(몫 + 앞쪽 나머지), 완전 중복 제거, 2\~2,000자 길이 필터, 결정적 빌드와 sha256 기록. T7은 같은 MASSIVE id를 5개 언어에서 뽑아 언어 간 짝을 유지한다(`results/korean_support/K2_build.py`의 id join 방식). typed-decisions는 case 단위로 뽑고 case 안의 모든 질문을 쓴다.

주의: T2·T5는 upstream이 "in training mix"로 표기한 소스라 Laya에 유리할 수 있다. T4는 held out이고 T7(MASSIVE)은 두 체크포인트 모두 학습하지 않았다(build_benchmark_nb.py:760-762). 표에 그대로 전달하고 held-out 과제(T1, T3, T4, T6, T7, T8)와 분리해 해석한다.

---

## 4. 프로토콜 동일성

두 시스템이 바이트 단위로 같은 정보를 받도록 한다.

| 요소 | Laya | Jev 플레이그라운드 | 동일성 확보 |
|---|---|---|---|
| state | upstream이 렌더링하는 dict state(예: `{"text": ...}`), 모델은 JSON 직렬화 문자열을 읽음 | State textarea에 그 JSON 직렬화 문자열(`state_text`)을 그대로 입력 | 바이트 동일. 폼 파일의 `state_text`가 Laya가 실제로 읽는 문자열이다(`scripts/build_jev_cmp_sets.py:176` `playground`) |
| 질문 문구 | upstream 원문 `instructions` 그대로(bench_apps.py: AG News·Emotion·Banking77, build_benchmark_nb.py:414-490: BoolQ·SST-5·prompt-injections, bench_local.py:173-180: MASSIVE) | Question 필드에 같은 문장 | 같은 영어 문장. 백틱 필드 참조(예: `utterance`)도 그대로 둔다. state가 같은 JSON 문자열이라 두 시스템이 같은 필드명을 본다 |
| choice 옵션 | `criteria` dict `{key: description}` → 모델은 `key: description`을 읽음 (출처: README.md "Honest limits", laya/common.py render_options) | 라벨 텍스트 1칸 × 최대 10 | Jev 라벨에 `key: description` 문자열을 그대로 넣는다(파일럿과 동일) |
| noul | `type: noul` (+ 필요 시 criteria true/false) | Decision type Boolean | 질문 문구 동일. Laya criteria는 upstream preset 관례대로 넣지 않는다(04 §3) |
| score | `criteria` 레벨 설명 리스트, 답은 기대 레벨(실수) | Decision type Score, 레벨 설명 입력 가능 여부 확인 필요 | Jev score 출력 형식(정수 레벨인지 분포인지)을 S1에서 확인하고 비교 규칙을 고정한다 |
| 옵션 순서 | 고정 | 고정 | 같은 순서. 순열 프로브는 T2에서 20건만(k=1) |
| 다중 질문 | 한 호출 = 여러 질문 행 | Multiple questions 모드 | T1만 사용. 모드가 타입 혼합·질문 수를 지원하지 않으면 Single로 질문별 실행(요청 수 5배, 예산 재조정) |

Laya 측정은 요청 비용이 없으므로 전량 로컬에서 한다: `laya-evals run`(CPU fp32 기준, 영어 과제는 english 체크포인트, T7은 언어별로 english·multilingual 둘 다, Router auto 병기), 지연은 Track D 값(`results/D/D_summary_20261003.md`)과 laya-serve 로컬 HTTP 왕복을 인용한다. ft-v1은 T7의 ko 슬라이스에만 참고선으로 둔다(도메인 과제가 아니라 intent 과제이므로 직접 비교 대상은 아님을 표기).

Jev 측정은 파일럿 러너(`results/F/jev_f.py`: sample / record / record_error / analyze)를 확장한다. 요청 전 입력 해시 대조, 요청 후 DOM과 snapshot 저장, "View details" 캡처, 표시 지연과 브라우저 POST 시간 기록, attempt 번호 기록을 유지한다.

### 4.1 과제별 질문 문구와 옵션 렌더링

두 시스템에 들어가는 문자열을 세트 빌드 시점에 고정하고 `questions_sha256`으로 동결한다(출처: docs/evals.md "Run identity"). 문구는 upstream 원문을 그대로 쓴다. 그래야 Laya 수치를 upstream 발표치와 같은 눈금에서 읽을 수 있고, Jev에는 Laya가 읽는 것과 같은 JSON 직렬화 state를 넣으므로 백틱 필드 참조가 있어도 두 시스템이 같은 것을 본다(S0 결정, `results/F/jev_cmp/S0_20261006.md`).

| 과제 | 질문 문구와 state(두 시스템 동일, upstream 원문) | Laya criteria | Jev 라벨(최대 10, 각 80자 이하) |
|---|---|---|---|
| T1 | 데이터셋의 원 질문·옵션·state 그대로(upstream Part B와 동일) | 원 criteria | `key: description`. 10개 초과 옵션 case는 0건이었고, 80자 초과 옵션 decision 10개는 `jev_excluded`(§2) |
| T2 | bench_apps.py의 AG News 질문·dict state | upstream 라벨 설명 | `key: description` 4개 |
| T3 | bench_apps.py의 Emotion 질문·dict state | upstream 라벨 설명 | `key: description` 6개 |
| T4 | bench_apps.py의 Banking77 질문·dict state | gold + 9 distractor, key 단독 렌더링 `{k.replace("_"," "): None}`(bench_apps.py:120-122) | key 단독 10개(최대 48자) |
| T5 | build_benchmark_nb.py:414-490의 BoolQ 질문, state = passage + question dict | noul, criteria 없음 | Boolean |
| T6 | build_benchmark_nb.py:414-490의 SST-5 질문 | 5 레벨 설명 | Score, 레벨 설명 입력 가능 여부에 따라 S1에서 확정 |
| T7 | bench_local.py:173-180 "What is the user asking for in `utterance`?", state `{"utterance": text}` | gold + 9 distractor, 렌더링 `k.replace("_"," ").replace(".", ": ")`(`render_key`) | key 렌더링 10개 |
| T8 | build_benchmark_nb.py:414-490의 prompt-injections 질문 | noul | Boolean |

T2·T3·T7의 설명 문구는 영어로 쓰고(과제 언어가 영어이거나 upstream 관례), T7의 비영어 발화에도 영어 key 렌더링을 그대로 쓴다. 이 선택은 upstream의 MASSIVE 구성과 같고(출처: research/scripts/bench_local.py:165-183), 한국어 설명이 유리했던 07 §5의 관찰은 다국어 슬라이스에서 "영어 옵션 조건"임을 표기하는 것으로 반영한다. T1의 Score 질문은 Jev Score 형식 확인 전까지 Multiple questions 모드에서 제외 가능성을 열어 둔다.

### 4.2 Jev 입력 변환 규칙

`scripts/build_jev_cmp_sets.py`는 세트마다 플레이그라운드 입력 폼 `data/evals/jev_cmp/<set>_playground.json`을 함께 쓴다(`playground` :176). 항목 스키마는 `{"id", "state_text" (Laya가 읽는 JSON 직렬화 문자열), "question", "decision_type": "choice"|"boolean"|"score", "options": ["key: description" 또는 key 단독, ...] (≤ 10, 각 ≤ 80자), "gold", 선택적으로 "jev_excluded": true, "reason"}`이다. 러너는 `state_text`와 `options`를 그대로 입력하고, 요청 전 입력 해시를 대조하며, 응답의 DECISION 문자열이 `options` 중 하나와 정확히 같은지 확인한 뒤 ":" 앞 key(또는 key 단독)로 되돌린다. 일치하지 않으면 그 행은 "파싱 실패"로 기록하고 정오 판정에서 제외한다. `jev_excluded` 항목은 Jev에 보내지 않는다.

---

## 5. 지표

| 지표 | 정의 | 비고 |
|---|---|---|
| accuracy | argmax 일치율, Wilson 95% CI | 과제별, 시스템별 |
| macro-F1 | gold∪pred 클래스 기준 | choice 과제 |
| Brier | 옵션별 (p − y)² 합의 평균 | Jev 확률은 2자리 반올림이라 하한 오차 ±0.005 명시 |
| ECE | 15 bins, 선택 답의 확률 기준 | Jev는 반올림으로 bin이 성기므로 참고 지표 |
| coverage@오류 | 오류 5%·10% 이하 최대 coverage | 두 시스템 모두 top 확률로 정렬 |
| 일치율 · McNemar | 같은 항목에서 두 시스템 정오 짝 비교, exact McNemar | 주 검정 |
| 옵션 순서 flip | T2 20건, 순열 1개 | 소표본 방향 신호. Jev 공개치 0.13, Laya en 20옵션 0.150/0.230 |
| 결정성 | 같은 요청 2회 반복 10건의 argmax·확률 일치 | Jev 생성형 추정(출력 약 255 토큰, 파일럿) |
| 실패 모드 | Jev: 정답 확률 0%, "Unable to evaluate", 502. Laya: 422/413, 빈 답 | 건수 |
| 지연 | Jev 표시값과 브라우저 POST; Laya in-process(D1)와 laya-serve 왕복(D6, P2) | 호스팅 vs 로컬이라 네트워크 포함 여부를 표에 명시 |
| 비용 | Jev: 공개 단가 × 토큰(실행 시 단가 확인, 파일럿 입력 약 716·출력 약 255 토큰). Laya: 장비·전력 추정 | 1k decisions당 |
| 다국어 페널티 | T7 언어별 accuracy, en 대비 Δ | 언어당 20이라 방향 신호 |

T1은 upstream Part B 정의를 따른다: argmax accuracy, soft accuracy(teacher 분포 대비), Brier, ECE, score MAE(출처: research/scripts/bench_local.py Part B `metrics`).

---

## 6. 통계적 한계

- n=40에서 95% CI는 약 ±0.15다. 두 시스템의 차이가 0.2 이상일 때만 유의 판정이 가능하다. 그 이하의 차이는 "구분되지 않음"으로 보고한다.
- T1은 200 decisions라 ±0.07, T7은 언어당 20이라 ±0.2에 가깝다. T7은 방향 신호로만 쓴다.
- 짝 비교(McNemar)는 두 시스템이 서로 다른 항목에서 틀릴 때만 힘이 있다. 파일럿처럼 한쪽이 다른 쪽의 정답을 모두 포함하면 b 또는 c가 0이 되어 p가 0.5 이상으로 머문다.
- 대표성 점검: 우리 Jev 표본의 AG News·Emotion·typed-decisions 정확도가 Jev 발표치(0.910, 0.480, 0.727)의 CI 안에 있는지 확인한다. 밖이면 표본 편향이나 모델 버전 변화를 의심하고 결론을 보수적으로 쓴다.
- 플레이그라운드는 API가 아니다. 프롬프트 래핑이나 모델 버전이 API와 다를 수 있고 버전은 표기되지 않는다. 세션마다 Model ID와 토큰 수를 기록해 세션 간 변동을 추적한다.

---

## 7. 실행 순서 [단계 → 검증]

| 단계 | 내용 | Jev 요청 | 검증 |
|---|---|---|---|
| S0 하네스·세트 (완료 2026-10-06) | `scripts/build_jev_cmp_sets.py`로 T1\~T8 세트 12개 + 폼 생성(결정적, validate, MANIFEST), Laya 전량 측정 38회 + 순열 프로브(laya-evals, CPU fp32). T4 key-only 재빌드·재측정 8회 포함 | 0 | 12개 세트 validate 통과, 오프라인 재빌드 바이트 동일, `results/F/jev_cmp/S0_20261006.md`, `laya_summary.md` |
| S1 탐색 + T2 (완료 2026-10-06) | Multiple questions 모드 확인(탐색 1회, T1 row 30), T1이 그대로 실리지 않아 규칙대로 T2 AG News 40으로 전환 | 41 (모두 200) | `sessions/S1_20261006/multi_question_mode.md`, `S1_summary.md`; §7.1 |
| S1b 결정성 + 순열 (완료 2026-10-06) | T2 10행 재전송, T2 20행 옵션 순열(Laya probe와 같은 순열) | 30 (모두 200) | `sessions/S1b_20261006/S1b_summary.md`; §7.1 |
| S2 | T1-A 39 case(Multiple questions, 4레벨 score 생략) + T3 Emotion 40 | 79 | 120 decisions 기록, Jev 발표치(T1 0.727, T3 0.480)와 대조 |
| S3 | T4 Banking77-10 40, T5 BoolQ 40 | 80 | 10옵션 조건 양쪽 새 측정 |
| S4 | T6 SST-5 40, T7 en·de 40 | 80 | score 규칙(argmax + E[level] MAE) 적용 |
| S5 | T7 ja·zh-CN·ko 60 (+ T8 40, 예산 내; 아니면 6일차) | 60\~100 | 언어별 표 |
| S6 분석·리포트 | `results/F/jev_cmp/summary.md`(Laya 측 `laya_summary.md`와 Jev 세션 기록 `jev_runs_all.jsonl` 취합), 세션 run card 취합, 대시보드 Track F 갱신, 소논문 v2(제목 "Laya vs Jev", 한국어 연구는 사례·부록) | 0 | REPORT·대시보드·논문 수치 일치 |
| S7 (완료 2026-10-08, 3-arm 확장) | T9 Enron spam 40 + T10 고객지원 티켓 큐 40(`11_three_arm_plan.md`의 Jev arm, 프로젝트 책임자 승인 2026-10-08) | 80 (모두 200) | `sessions/S7_20261008/S7_summary.md`, `S7_run_card.md`; §7.1d |

세션은 하루 100 요청 이하로 4\~6일에 걸쳐 분산한다. 각 세션 전에 사이트 상태를 1회 확인하고, 세션 중 502가 반복되면 그날은 종료한다.

### 7.0 S0 결과 (2026-10-06, `results/F/jev_cmp/laya_summary.md`, `S0_20261006.md`)

Laya 측 측정값(CPU fp32, intra-op 10 / inter-op 1, Wilson 95% CI, n=40에서 CI 폭 약 ±0.15). Router 열의 괄호는 라우팅된 체크포인트다.

| 과제 | english | multilingual | Router | upstream 발표치 (english / multilingual) |
|---|---|---|---|---|
| T1 typed-decisions, Jev 비교 120 decisions (choice 50 / noul 60 / 5레벨 score 10) | 0.383 [0.301, 0.473] (choice 0.280, noul 0.467, score 0.400; soft 0.361, Brier 0.333) | 0.367 [0.286, 0.456] (choice 0.320, noul 0.433, score 0.200) | 0.383 (전부 english) | 0.362 / 0.352 (200 기준: 0.330 / 0.305; 190 기준: 0.347 / 0.311). 120개 질문별 최빈 기준선 0.575 |
| T1 typed-decisions 체크포인트(파인튜닝, zero-shot 아님) | 0.867 [0.794, 0.916] (choice 0.800, noul 0.950, score 0.700; soft 0.519 / Brier 0.059; 200 기준 0.795, 190 기준 0.811) | - | - | 0.766 (soft 0.471 / Brier 0.061 / MAE 0.242) |
| T2 AG News | 0.975 | 0.925 | 0.975 | 0.947 / 0.950 (Jev 제3자 0.910) |
| T3 Emotion | 0.750 [0.598, 0.858] | 0.625 | 0.750 | 0.573 / 0.595 (Jev 제3자 0.480) |
| T4 Banking77-10 (key-only) | 0.725 | 0.750 | 0.725 | 77옵션 0.425라 비교 불가 |
| T5 BoolQ | 0.725 | 0.600 | 0.725 | 0.830 / 0.787 |
| T6 SST-5 (argmax 레벨, MAE) | 0.425 (0.888) | 0.325 (1.419) | 0.425 | 0.372 / 0.282 |
| T7 MASSIVE-10 en / de / ja / zh-CN / ko | .70 / .35 / .45 / .45 / .10 | .85 / .40 / .80 / .60 / .45 | .70 / .35 / .80 / .60 / .45 | 20옵션 기준 en 0.820 / 0.710, ko 0.110 / 0.470 |
| T8 prompt-injections | 0.775 | 0.575 | 0.725 (english 26 / multilingual 14행) | 0.698 / 0.578 |

- **T4 렌더링 효과**(같은 40행·같은 옵션 집합·같은 순서, v0 `key: key spaced` vs key-only; `laya_summary.md` §4b): english 0.825 → 0.725(v0만 정답 4 / key-only만 정답 0, McNemar p=0.125), multilingual 0.575 → 0.750(0 / 7, p=0.016). 옵션 텍스트 렌더링만으로 정확도가 크게 움직이므로 Jev에도 같은 렌더링을 넣는 것이 비교의 전제다.
- **T3 표본은 Laya english에 쉬운 쪽으로 뽑혔다.** 같은 파이프라인으로 upstream 설정(test 첫 600행, 같은 질문)을 돌리면 0.5733 / ECE 0.3237로 발표치 0.5733 / 0.3238과 같다(`research/results/t4_colab_benchmark.json` en.emotion). 우리 seed 13 40행은 0.750이다. Jev와의 짝 비교에는 쓸 수 있지만 발표치와 비교해 일반화하면 안 된다.
- **T1 제외 80개**: customer_service/action(choice) 10개(옵션 87\~89자, english는 전부 오답)와 4레벨 score 70개(플레이그라운드 Score 5레벨 제약). 그래서 120 기준 정확도(0.383)가 200 기준(0.330)보다 높다. noul criteria 유무 변형(`T1_typed_decisions_40_noulnocrit.jsonl`)은 §2 참조.
- 결정성: T1 english 2회 실행 200 decisions 동일. 옵션 순서 프로브(T2, 순열 1개, 40행): flip 0.000 (english·multilingual).

### 7.1 S1·S1b 결과 (2026-10-06, `results/F/jev_cmp/sessions/S1_20261006/S1_summary.md`, `sessions/S1b_20261006/S1b_summary.md`)

**S1**: 요청 41회(탐색 1 + T2 40), 모두 HTTP 200, 5xx·429·캡차 0, 재시도 0. 41회 모두 실제 전송 body가 폼 payload와 바이트 단위로 같았다. T1은 Score 5레벨 제약으로 Multiple questions 모드에 그대로 실리지 않아(§2) 규칙대로 T2로 전환했다.

| 시스템 (T2 AG News, 같은 40행) | 정답/n | 정확도 | Wilson 95% |
|---|---|---|---|
| Jev (플레이그라운드) | 35/40 | 0.875 | [0.739, 0.945] |
| Laya english | 39/40 | 0.975 | [0.871, 0.996] |
| Laya multilingual | 37/40 | 0.925 | [0.801, 0.974] |
| Laya Router (40건 모두 english) | 39/40 | 0.975 | [0.871, 0.996] |

- McNemar: Jev vs english 같은 라벨 36, b=0 / c=4, p=0.125; Jev vs multilingual 같은 라벨 38, b=0 / c=2, p=0.5. 방향은 한쪽(Laya가 맞히고 Jev가 틀림)이지만 n=40에서 유의하지 않다(b=0이면 c ≥ 6이어야 p < 0.05).
- Jev 확신도: 100% 표시 29/40, 0% 칸 109/160. 정답 평균 top 98.5%, 오답 92.2%이고 오답 5건 중 4건이 93% 이상이라 90% 임계값으로 걸러지지 않는다. Brier 0.220(Laya english 0.053). 파일럿(한국어 24행)에서는 오답이 모두 90% 미만이었으므로 보정 양상은 과제마다 다르다.
- Jev 오답 5건은 모두 business/world 쪽이며 sci_tech/world/business 경계 사례다(1건은 gold 자체가 의심스러움). T2가 Laya 학습 믹스에 포함된 점과 분리할 수 없다.
- 지연: 표시값 중앙 234 ms(188\~448), 응답 `latencyMs` 반올림과 41/41 일치. 브라우저 POST 468 ms(415\~749). Laya 로컬 참조: P2 왕복 20.1 ms, D1 english CPU 1문항 86.6 ms, MPS 31.8 ms(하드웨어·경로가 달라 모델 속도 비교는 아님). 토큰 중앙 입력 425 / 출력 68.
- 대표성: Jev 0.875는 공개치 0.910의 CI 안, Laya english 0.975는 upstream 0.947/0.950의 CI 안이다.

**S1b**: 요청 30회 모두 200, 간격 최소 17.3 s. (1) 결정성(T2 10행을 16\~23분 뒤(중앙 20분) 같은 payload로 재전송, 요청 기록 기준, `results/F/jev_cmp/summary.md` §6): 라벨 10/10 일치, 확률 벡터 9/10(max |Δp| 0.01), View details confidence 9/10, 토큰 10/10, latencyMs 중앙 221 → 233 ms. 사실상 결정적이나 비트 단위로 같지는 않다. (2) 옵션 순서 flip(T2 20행, Laya probe와 같은 순열): Jev 0/20 [0, 0.161], Laya english 0/20, multilingual 0/20. 공개치 0.13을 배제할 수는 없다(flip률 0.13일 때 0/20이 나올 확률 0.062). 4옵션·고확신 표본(100% 표시 13/20)이라 정보량이 낮고, 순서 민감도는 T3·T4·T7에서 다시 본다. (3) 1일차 사용량: 파일럿 25 + 확인 2 + S1 41 + S1b 30 = 98/100.

### 7.1b S2 결과 (2026-10-07, `results/F/jev_cmp/sessions/S2_20261007/S2_summary.md`, `S2_run_card.md`)

**요청과 진행**: 요청 80회. Part A(T1) 40회 = 성공 39 + HTTP 502 1회(run 1, "Jev is temporarily unavailable.", 73.7 s 뒤 같은 payload로 1회 재시도해 성공), Part B(T3) 40회 모두 성공. 그 뒤 5xx·429·제한 문구·캡차는 0건이다. 간격은 최소 12.1 s, 중앙 15.1 s(monotonic 기준, 79개 간격 모두 10 s 이상). 요청 전 sha12 대조와 요청 후 body 바이트 대조가 80/80 일치했고 Model ID는 `typesafe-ai/jev` 79/79다. T1 row 30은 다시 보내지 않고 S1 탐색 run을 재사용했다(A안 payload와 sha12 `5a9e5492744b` 일치). 비교 가능 질문이 case마다 2\~4개라 모두 Multiple questions 모드로 보냈다. 2일차 사용량은 80/100이다(`S2_run_card.md`).

**T1 typed-decisions, 같은 120 decisions (S2 39 runs + S1 row 30)**

| 시스템 | 전체 | choice 50 | noul 60 | score 10 (argmax) | soft acc | Brier (soft 대비) | ECE | score MAE (5레벨 10문항) |
|---|---|---|---|---|---|---|---|---|
| Jev (플레이그라운드) | 104/120 = 0.867 [0.794, 0.916] | 42/50 | 56/60 | 6/10 | 0.590 | 0.077 | 0.181 | 0.389 |
| Laya english | 46/120 = 0.383 [0.301, 0.473] | 14/50 | 28/60 | 4/10 | 0.361 | 0.333 | 0.205 | 0.584 |
| Laya multilingual | 44/120 = 0.367 [0.286, 0.456] | 16/50 | 26/60 | 2/10 | 0.351 | 0.574 | 0.391 | 0.671 |
| Laya Router (120건 모두 english) | english와 같음 | | | | | | | |
| 참고: Laya typed-decisions (이 벤치 train으로 파인튜닝, zero-shot 아님) | 104/120 = 0.867 | 40/50 | 57/60 | 7/10 | 0.519 | 0.059 | 0.279 | 0.255 |
| 문항별 최빈 기준선 | 0.575 | | | | | | | |

- Exact McNemar(b = Jev만 정답, c = Laya만 정답): Jev vs Laya english(= Router) 66/8, p < 0.0001(choice 31/3, noul 31/3, score 4/2 p 0.69). Jev vs multilingual 66/6(choice 27/1, noul 33/3, score 6/2 p 0.29). Jev vs 파인튜닝 체크포인트 10/10, p 1.0.
- 같은 입력 noul 비교: Jev Boolean은 설명을 받지 못하므로 criteria를 뺀 Laya 변형과 견준다. Jev 56/60 = 0.933 [0.841, 0.974], Laya english 무설명 31/60 = 0.517(b/c 27/2, p < 0.0001), multilingual 무설명 25/60 = 0.417(b/c 34/3). 설명을 넣은 Laya도 28/60, 26/60이라 차이는 설명 비대칭으로 설명되지 않는다.
- workflow별 (Jev / Laya english): agent_trace 25/30 vs 14/30, customer_service 19/20 vs 11/20, invoice 29/30 vs 4/30(Laya base는 duplicate 질문 0/10), security 31/40 vs 17/40.
- 공개치 대조(맥락 전용): Jev 공개치 0.727 / soft 0.580 / Brier 0.148 / MAE 0.391은 2,000 decisions·다른 문항 구성이다. 같은 부분집합 효과로 Laya english도 0.330(200 기준)에서 0.383(120 기준)으로 오른다.

**T3 DAIR Emotion, 같은 40행**

| 시스템 | 정답/40 | 정확도 [Wilson 95%] | Brier | ECE | McNemar vs Jev (b/c, p) |
|---|---|---|---|---|---|
| Jev (플레이그라운드) | 28 | 0.700 [0.546, 0.819] | 0.537 | 0.278 | - |
| Laya english | 30 | 0.750 [0.598, 0.858] | 0.429 | 0.174 | 2/4, p 0.6875 |
| Laya multilingual | 25 | 0.625 [0.470, 0.758] | 0.631 | 0.313 | 6/3, p 0.508 |
| Laya Router (모두 english) | 30 | 0.750 | 0.429 | 0.174 | 2/4, p 0.6875 |

- 클래스별 정답(Jev / Laya english): sadness 7/6, joy 5/7, love 3/3, anger 5/6, fear 5/4, surprise 3/4. Jev 오답은 love → joy 3개, sadness로 간 것 4개이고 세 시스템이 함께 틀린 행이 7개다.
- 표본 쉬움 주의: 이 seed-13 표본은 두 시스템 모두에게 쉽다. Jev 0.700의 CI가 공개치 0.480을 포함하지 않고, Laya english 0.750도 upstream 0.573보다 높다. 짝 비교에만 쓰고 공개치와 비교해 일반화하지 않는다.

**보정과 확신도**
- T1의 Jev는 과소확신이다. 평균 top p 0.733이 정확도 0.867보다 낮고(정답 0.758, 오답 0.569), 오답 16개 중 top ≥ 0.90은 score 1개뿐이다. noul 오답 4개는 p(true) 0.39\~0.54였고 provider confidence도 정답 0.711 / 오답 0.454로 같은 방향이다. 임계값으로 Jev 오답을 보류할 여지가 있다.
- T3의 Jev는 과대확신이다. 100% 표시 15/40, 오답 12개 중 7개가 90% 이상이고, 정답 옵션이 0%로 표시된 행이 7/40(17.5%)으로 공개된 zero-probability 실패율 16%와 비슷하다. 평균 top p는 정답 0.918, 오답 0.861이다.
- 즉 Jev 확률의 의미는 과제 형식에 따라 다르다. Multiple questions의 T1에서는 오답이 저확신이고, 단일 choice인 T2·T3에서는 오답 다수가 90\~100%로 표시된다.

**지연과 토큰**
- T1(요청당 질문 2\~4개): 표시 지연 중앙 226 ms(164\~355), 질문당 표시 지연은 2문항 111 ms, 3문항 75 ms, 4문항 60 ms. 브라우저 POST 481 ms, 토큰 중앙 입력 760 / 출력 141.
- T3: 표시 지연 중앙 241 ms(170\~713), POST 469 ms, 토큰 387.5 / 61.
- 공통: 표시값은 `latencyMs` 반올림과 79/79 일치, POST − latencyMs 중앙 235.6 ms, 토큰 합계 입력 45,616 / 출력 8,806.

**한계와 주의**
- 플레이그라운드 경유이며 API가 아니고, 모델 버전이 표기되지 않으며, 표본이 작다.
- T1 gold는 데이터셋 teacher 분포의 argmax다. teacher의 정체와 Jev와의 관계는 알 수 없다(확인 필요). teacher와 비슷한 모델에 유리한 과제일 수 있고, Jev zero-shot이 이 벤치 train으로 파인튜닝한 Laya와 같은 104/120을 낸 점은 이 맥락에서 읽어야 한다(열린 질문 10).
- T1에서 Jev는 case의 질문 2\~4개를 한 요청에서 함께 평가했고, Laya는 질문마다 별도 행으로 평가했다. 이 차이의 효과는 분리하지 못했다.
- 측정 이상: run 60과 61 사이에 호스트 wall clock이 +1.98 s 스텝해 run 61의 dump 매칭이 timeout났다(실제 요청 1회, HTTP 200). dump와 간격 가드를 monotonic 기준으로 바꿔 다시 기록했고 추가 요청은 없다(`S2_run_card.md`, timeout dump는 `raw/r61_T3_row20_timedout_dump1.json`, 공개 저장소에는 포함하지 않음).

### 7.1c S3·S4·S5 결과 (2026-10-07, `results/F/jev_cmp/sessions/S3_20261007/S3_summary.md`, `S4_20261007/S4_summary.md`, `S5_20261007/S5_summary.md`)

**운영**: 하루 상한 해제(§2) 뒤 세 세션을 연속으로 돌렸다. 요청은 S3 80, S4 80, S5 100이고 모두 HTTP 200, 재시도 0, 5xx·429·제한 문구·captcha 0이다. 간격은 monotonic 기준 최소 15.013 s, 세션별 중앙 15.114\~15.125 s다. 요청 전 payload 해시와 요청 후 body 바이트 대조가 260/260 일치했고 Model ID는 260/260 `typesafe-ai/jev`였다. 이 날 누적 340회(S2 80 포함)의 마지막 요청까지 제한 신호가 없었다(`S5_run_card.md:51`). 수치는 S6 종합(`results/F/jev_cmp/summary.md` §2)과 같다.

**T4 Banking77-10 (key-only 옵션, S3, 같은 40행)**

| 시스템 | 정확도 [Wilson 95%] | Brier | ECE | McNemar vs Jev (b/c, p) |
|---|---|---|---|---|
| Jev | 37/40 = 0.925 [0.801, 0.974] | 0.114 | 0.069 | - |
| Laya english (= Router) | 29/40 = 0.725 [0.572, 0.839] | 0.349 | 0.150 | 9/1, 0.0215 |
| Laya multilingual | 30/40 = 0.750 [0.598, 0.858] | 0.478 | 0.262 | 8/1, 0.0391 |

- Jev 오답 3개 중 2개는 Laya 세 러너도 같은 라벨로 틀렸다. Jev 100% 표시 31/40, 오답 중 top ≥ 0.90은 1/3이다.

**T5 BoolQ (S3, gold true 20/40)**

| 시스템 | 정확도 (p(true) ≥ 0.5) | 예측 true | AUROC [bootstrap 95%] | Brier | McNemar vs Jev (b/c, p) |
|---|---|---|---|---|---|
| Jev | 37/40 = 0.925 [0.801, 0.974] | 21 | 0.988 [0.955, 1.000] | 0.098 | - |
| Laya english (= Router) | 29/40 = 0.725 [0.572, 0.839] | 19 | 0.810 [0.662, 0.942] | 0.393 | 9/1, 0.0215 |
| Laya multilingual | 24/40 = 0.600 [0.446, 0.737] | 18 | 0.682 [0.496, 0.838] | 0.615 | 15/2, 0.0023 |

- AUROC 차이 Jev − english +0.177 [+0.043, +0.326]이라 임계값이 아니라 순위 품질의 차이다. Jev Boolean은 100% 표시 0/40이고 오답 3개가 모두 top < 0.80이었다.

**T6 SST-5 (S4, 5레벨, gold 레벨당 8)**

| 시스템 | argmax 정확도 (주 지표) | 반올림 E[level] 정확도 | MAE of E[level] | Brier | McNemar vs Jev: argmax / 반올림 E (b/c, p) |
|---|---|---|---|---|---|
| Jev | 26/40 = 0.650 [0.495, 0.779] | 27/40 = 0.675 | 0.432 | 0.502 | - |
| Laya english (= Router) | 17/40 = 0.425 [0.285, 0.578] | 16/40 = 0.400 | 0.888 | 0.770 | 15/6, 0.0784 / 15/4, 0.0192 |
| Laya multilingual | 13/40 = 0.325 [0.201, 0.480] | 13/40 = 0.325 | 1.419 | 1.149 | 18/5, 0.0106 / 19/5, 0.0066 |

- MAE 차이 Jev − english −0.456 [−0.711, −0.207]. Laya english는 레벨 4를 0/40, multilingual은 40/40행을 레벨 0·1로 냈다(척도 압축). multilingual의 첫 레벨 회피(#131)는 이 표본에서 나타나지 않았다.

**T7 MASSIVE intent-10 (S4 en·de, S5 ja·zh-CN·ko, 같은 20 id)**

| 시스템 | en | de | ja | zh-CN | ko | 합산 100 |
|---|---|---|---|---|---|---|
| Jev | 0.900 | 0.900 | 0.950 | 0.900 | 0.900 | 91/100 = 0.910 [0.838, 0.952] |
| Laya english | 0.700 | 0.350 | 0.450 | 0.450 | 0.100 | 41/100 = 0.410 [0.319, 0.508] |
| Laya multilingual | 0.850 | 0.400 | 0.800 | 0.600 | 0.450 | 62/100 = 0.620 [0.522, 0.709] |
| Laya Router | 0.700 | 0.350 | 0.800 | 0.600 | 0.450 | 58/100 = 0.580 [0.482, 0.672] |
| Jev vs multilingual (b/c, p) | 3/2, 1.0000 | 11/1, 0.0063 | 3/0, 0.2500 | 8/2, 0.1094 | 11/2, 0.0225 | 36/7, 9.0e-06 (독립 아님) |

- 언어당 n=20이라 언어별 크기는 방향 신호다. 5개 언어 모두 같은 라벨을 낸 id는 Jev 18/20(언어쌍 평균 일치 0.935), Laya english 0/20, multilingual 5/20, Router 4/20이다. en 대비 평균 언어 페널티는 Jev +0.012, english −0.362, multilingual −0.287이다.

**T8 prompt-injections (S5, gold true 20/40)**

| 시스템 | 정확도 (p(true) ≥ 0.5) | 예측 true | FN / FP | AUROC [bootstrap 95%] | Brier | McNemar vs Jev (b/c, p) |
|---|---|---|---|---|---|---|
| Jev | 31/40 = 0.775 [0.625, 0.877] | 11 | 9 / 0 | 1.000 (완전 분리, CI 퇴화) | 0.307 | - |
| Laya english | 31/40 = 0.775 [0.625, 0.877] | 11 | 9 / 0 | 0.929 [0.840, 0.997] | 0.401 | 5/5, 1.0000 |
| Laya multilingual | 23/40 = 0.575 [0.422, 0.715] | 9 | 14 / 3 | 0.781 [0.615, 0.919] | 0.692 | 11/3, 0.0574 |
| Laya Router | 29/40 = 0.725 [0.572, 0.839] | 11 | 10 / 1 | 0.868 [0.738, 0.969] | 0.510 | 7/5, 0.7744 |

- 정확도는 같지만 오류 구조가 다르다. Jev는 역할·작업 지시형 주입을 p(true) 0.08\~0.40으로 낮게 매겨 놓쳤고, 정상 행 p(true)가 0.01\~0.04라 같은 40행의 최적 임계값이 0.04 초과 0.08 이하에 있다(기술통계). Laya english는 독일어로 된 명시적 덮어쓰기 4개를 놓쳤다(`S5_summary.md` §4).

### 7.1d S7 결과 (2026-10-08, `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md`, `S7_run_card.md`)

3-arm 확장(`11_three_arm_plan.md`)의 Laya 학습 믹스 과제 T9·T10을 같은 규칙으로 보냈다(프로젝트 책임자 승인 2026-10-08). 요청 80회(T9 40 + T10 40)가 모두 HTTP 200이고 5xx·429·제한 문구·captcha 0, 재시도 0이다. 간격은 monotonic 기준 최소 15.009 s, 중앙 15.134 s다. 요청 전 payload 해시와 요청 후 body 바이트 대조가 80/80 일치했고 Model ID는 80/80 `typesafe-ai/jev`였다. Laya 쪽은 `results/T3arm/vanilla/`의 리포트이고 Router는 80행 모두 english로 보냈다.

| 과제 | Jev | Laya english (= Router) | Laya multilingual | McNemar vs Jev: english / multilingual (b/c, p) |
|---|---|---|---|---|
| T9 Enron spam (noul, gold true 20/40) | 40/40 = 1.000 [0.912, 1.000] | 40/40 = 1.000 | 40/40 = 1.000 | 0/0, 1.0000 / 0/0, 1.0000 |
| T10 고객지원 티켓 큐 (10-way choice, 큐당 4) | 10/40 = 0.250 [0.142, 0.402] | 12/40 = 0.300 | 18/40 = 0.450 | 3/5, 0.7266 / 4/12, 0.0768 |

- T9는 네 시스템 모두 천장이라 구분되지 않는다(AUROC 모두 1.000). 보정만 다르다(Brier Jev 0.019, english 0.005, multilingual 0.000).
- T10의 Jev는 크게 과대확신이다. 평균 top p 0.873에 정확도 0.250이고, 오답 30개 중 18개가 top ≥ 0.90이며 정답 옵션을 0%로 표시한 행이 20/40이다(Brier 1.319, ECE 0.623).
- T10은 세 시스템이 모두 틀린 행이 18/40이고, 오답 다수에서 gold 큐가 질문에 준 큐 설명과 맞지 않는다(해석, 수작업 확인 필요). 3-arm 종합에서 trained를 더해도 같은 18행이다(`results/T3arm/summary.md` §1.6).
- 지연은 표시값 중앙 219 ms(T9 214.5, T10 226)다.

### 7.2 일자별 예산표(완료 2026-10-07, S7 2026-10-08)

| 일자 | 세션 | 과제 | 요청 | 누적 |
|---|---|---|---|---|
| 2026-10-06 (완료) | 파일럿 + S1 + S1b | 한국어 24(+502 1), 확인 2, 탐색 1, T2 40, 결정성 10, 순열 20 | 98 | 98 |
| 2026-10-07 (완료) | S2 | T1-A 39(row 30은 S1 재사용) + 502 재시도 1, T3 40 | 80 | 178 |
| 2026-10-07 (완료, 하루 상한 해제 후) | S3 | T4 40, T5 40 | 80 | 258 |
| 2026-10-07 (완료) | S4 | T6 40, T7 en·de 40 | 80 | 338 |
| 2026-10-07 (완료) | S5 | T7 ja·zh-CN·ko 60, T8 40 | 100 | 438 |
| 2026-10-08 (완료, 3-arm 확장) | S7 | T9 40, T10 40 | 80 | 518 |
| 미실행 (선택) | S5-b | T4 v0 렌더링을 Jev에도 +40, T3·T4·T7 순열 프로브 | 0 | |

T1은 A안으로 확정했다(case당 1회, 4레벨 score 질문 생략, 비교 120 decisions, score MAE는 5레벨 10문항만). 대안 C(Single, decision당 1회)는 같은 120개에 요청 3배라 채택하지 않는다.

누적은 사이트 전체 요청(파일럿 25·확인 2 포함) 기준이다. S6 종합까지의 합계는 438회이고, 3-arm 확장의 S7 80회를 더해 518회다. `results/F/jev_cmp/jev_runs_all.jsonl`에는 S1 41 + S1b 30 + S2 80 + S3 80 + S4 80 + S5 100 = 411행 뒤에 S7 80행이 붙어 491행이 있고(F 종합은 앞 411행만 쓴다), 파일럿과 확인 요청 27회는 별도 파일(`results/F/jev_runs_raw.jsonl`)에 기록돼 있다(두 로그는 공개 저장소에는 포함하지 않음). 2026-10-07에 하루 상한을 해제해(§2) 원래 3\~5일차로 잡은 S3\~S5를 같은 날 진행했다.

**S3 이월 규칙**: S3는 T4 40 + T5 40 = 80으로 세션 상한과 같으므로, 5xx 재시도가 생기면 남은 마지막 항목을 S4로 이월하고 S4 예산에서 차감한다. 계측은 처음부터 monotonic 기준으로 한다(S2 run 60/61 사이 wall clock 스텝 대응, §7.1b). S3\~S5에서 5xx가 없어 이 규칙은 쓰이지 않았다.

### 7.3 세션 run card 필드(06 §1에 추가되는 항목)

- 사이트 상태 확인 결과(시각, 기본 예시 응답, 표시 지연)
- 요청 수(성공 / 5xx / 재시도), 최소·중앙값 간격, 세션 시작·종료 시각
- Model ID와 입출력 토큰 범위("View details")
- 입력 해시 대조 결과(요청 전·후), 파싱 실패 건수
- 오류 문구 원문과 처리(중단·재시도·종료)
- Laya 대응 리포트 경로(같은 세트의 `laya-evals` JSON)와 `questions_sha256`

---

## 8. 산출물

| 경로 | 내용 |
|---|---|
| `data/evals/jev_cmp/T1_typed_decisions_40.jsonl` 등 T1\~T8 12개 (+ `T4_banking77_10opt_40_v0.jsonl` 보관본) | laya-evals 형식 세트(Laya용). Jev용 입력은 같은 이름의 `*_playground.json` |
| `data/evals/jev_cmp/MANIFEST.json` | sha256, n, 소스·split·revision, 라이선스, 레이블 분포, questions_sha256, `jev_comparable_n`, `jev_excluded`, T4의 `options_rendering`·`previous_version` |
| `scripts/build_jev_cmp_sets.py` | 세트 빌더(`scripts/build_ko_evalsets.py` 헬퍼 재사용) |
| `results/F/jev_f.py` 확장 또는 `scripts/jev_playground_runner.py` | sample / record / analyze, 세션 예산 카운터, 재시도 규칙 |
| `results/F/jev_cmp/laya/<set>_<model>.json|.md` | Laya laya-evals 리포트(S0) |
| `results/F/jev_cmp/laya_summary.md` / `.json` | Laya 측 요약(과제 × 체크포인트, T1 190 기준, T4 v0 대 key-only, 결정성·순열) |
| `results/F/jev_cmp/sessions/S<k>_<date>/` | Jev 세션 원기록(요청별 JSONL, DOM, snapshot, 캡처, `multi_question_mode.md`. 요청별 JSONL·DOM·snapshot·캡처는 공개 저장소에는 포함하지 않음) |
| `results/F/jev_cmp/jev_runs_all.jsonl`(공개 저장소에는 포함하지 않음) | 모든 Jev 요청의 append-only 마스터 로그(세션 id, attempt, 결과) |
| `results/F/jev_cmp/S<k>_<date>.md` | 세션별 run card(06 §1, 요청 수·간격·오류 포함). S0는 `S0_20261006.md` |
| `results/F/jev_cmp/summary.md` / `.json` | 최종 비교 요약(과제 × 시스템 표, McNemar·Holm, 종합 통계, 보정, 견고성, 지연·비용, 위협), S6 완료. `s6_summary.py build`/`verify`로 생성·대조(불일치 0건) |
| `results/F/jev_cmp/figs/accuracy_by_task.png`, `t7_languages.png`, `latency.png` (+ SVG) | S6 그림(과제별 정확도와 Wilson CI, T7 언어별 정확도, 배포 형태별 지연) |
| `docs/10_paper_laya_vs_jev.md` (또는 08 개정) | 소논문 v2 |

---

## 9. 리스크와 완화

| 리스크 | 완화 |
|---|---|
| 사이트 중단·사용량 제한 | 중단 규칙과 재시도 1회. 하루 100 이하 분산으로 시작했고 2026-10-07 프로젝트 책임자 결정으로 하루 상한을 해제했다(§2). 실제로는 502 2회, 429 0회였다. 완료하지 못한 과제는 "미실행"으로 보고 |
| 모델 버전 변동 | 세션마다 Model ID·토큰 기록, 세션 간 같은 항목 결정성 점검 10건으로 추적 |
| 플레이그라운드 vs API 차이 | 모든 표에 "플레이그라운드 경유" 표기. 키가 생기면 같은 세트를 API로 재측정하는 계획을 유지 |
| Jev 다국어 지원 미문서화 | T7 결과를 사실로만 보고, 공식 지원 범위는 주장하지 않음 |
| 옵션 10개 제한 | Banking77·MASSIVE는 10옵션 조건임을 명시, upstream 77·20옵션 수치와 직접 비교하지 않음 |
| 소표본 | CI 병기, 0.2 이상 차이에만 유의 판정, 대표성 점검 |
| 학습 믹스 비대칭 | T2·T5의 in-training 표기 전달(T4·T7을 포함한 나머지는 held out, build_benchmark_nb.py:760-762), held-out 과제(T1, T3, T4, T6, T7, T8)와 분리 해석 |
| 자동화 윤리 | 사람 속도, 상한, 재시도 1회, 공개 시 출처·한계 명시 |

---

## 10. 결론 (S6, 2026-10-07, `results/F/jev_cmp/summary.md`, `summary.json`)

**판정 한 줄.** zero-shot에서는 Jev가 Laya보다 정확하고(8과제 중 Laya 유의 우세 0, Holm 후 Jev 유의 우세 2), 특히 지시형·다국어 과제에서 격차가 크다. Laya는 로컬 실행·지연·비용과 파인튜닝으로 격차를 메울 수 있다는 점에서 경쟁력이 있다.

| 과제 | n | Jev | Laya english / multilingual / Router | 최고 Laya 대비 b/c, p (Holm p) | 판정 (Holm 후) |
|---|---|---|---|---|---|
| T1 typed-decisions | 120 (40 case) | 0.867 | 0.383 / 0.367 / 0.383 | english 66/8, 1.8e-12 (1.4e-11) | Jev 유의 우세 (Jev 유의 우세) |
| T2 AG News | 40 | 0.875 | 0.975 / 0.925 / 0.975 | english 0/4, 0.1250 (0.3750) | 비유의 (비유의) |
| T3 DAIR Emotion | 40 | 0.700 | 0.750 / 0.625 / 0.750 | english 2/4, 0.6875 (1.0000) | 비유의 (비유의) |
| T4 Banking77-10 | 40 | 0.925 | 0.725 / 0.750 / 0.725 | multilingual 8/1, 0.0391 (0.1953) | Jev 유의 우세 (비유의) |
| T5 BoolQ | 40 | 0.925 | 0.725 / 0.600 / 0.725 | english 9/1, 0.0215 (0.1289) | Jev 유의 우세 (비유의) |
| T6 SST-5 | 40 | 0.650 | 0.425 / 0.325 / 0.425 | english 15/6, 0.0784 (0.3134) | 비유의 (비유의), MAE 0.432 vs 0.888 |
| T7 MASSIVE intent-10 x5 | 100 (20 id) | 0.910 | 0.410 / 0.620 / 0.580 | multilingual 36/7, 9.0e-06 (6.3e-05) | Jev 유의 우세 (Jev 유의 우세) |
| T8 prompt-injections | 40 | 0.775 | 0.775 / 0.575 / 0.725 | english 5/5, 1.0000 (1.0000) | 비유의 (비유의) |

**종합.**
- 판정 집계(Jev 유의 우세 / 비유의 / Laya 유의 우세): 보정 전 4 / 4 / 0, Holm 보정 후 2 / 6 / 0(T1·T7만 유의).
- macro 정확도: Jev 0.828, Laya english 0.646, multilingual 0.598, Router 0.661. 과제 bootstrap(10,000회)에서 Jev − Router는 +0.167 [+0.044, +0.293]이고, 이질적인 8과제의 기술통계다.
- 독립 단일 문항 240개(T2·T3·T4·T5·T6·T8) 합산 exact McNemar: 과제별 최고 Laya 대비 b/c 39/21, p=0.0273(Jev 194, Laya 176).
- 군집 bootstrap(10,000회): T1(case) Jev − english +0.483 [+0.371, +0.597], T7(id) Jev − multilingual +0.290 [+0.100, +0.470].
- 학습 믹스: upstream 표기로 Laya 학습 믹스 과제는 T2·T5뿐이다(`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`; `third_party/laya`는 공개 저장소에는 포함하지 않음. https://github.com/NandhaKishorM/laya 를 커밋 4aa6761로 클론해 재현). Jev 유의 우세 4개 중 T1·T4·T7은 두 체크포인트가 학습하지 않은 데이터이고(Holm 후 남는 T1·T7 포함) T5만 학습 믹스 과제다. Laya가 같거나 앞선 과제는 학습 믹스인 T2와 held out인 T3·T8이다.

**보정.** Jev 확률의 의미는 문항 형식마다 다르다. 단일 choice는 100% 표시가 65%이고 오답의 59%가 top ≥ 0.90이다. Boolean은 100% 표시가 0건이며 임계값의 적정 위치가 과제마다 다르다(T5는 0.5 근처, T8은 0.04\~0.08). 다문항(T1)은 과소확신이다. 최고 Laya 러너는 형식별로 묶으면 모두 과대확신이다. 확신도로 자동 처리 범위를 정하려면 두 시스템 모두 과제별 held-out 표본으로 임계값을 맞춰야 한다(summary.md §5).

**견고성.** Jev는 같은 payload 재전송에서 라벨 10/10, 확률 벡터 9/10이 같았고 Laya는 결정적이다. T2 옵션 순서 flip은 두 시스템 모두 0/20(정보량 낮음)이다. T7에서 5개 언어 모두 같은 라벨인 id는 Jev 18/20, Laya english 0/20, multilingual 5/20, Router 4/20이다(summary.md §6).

**지연과 비용.** Jev 표시값('server + network') 중앙 226 ms, 브라우저 POST 중앙 465 ms(410건, 인터넷 왕복 포함). Laya는 in-process 13.8\~86.6 ms(D1, 체크포인트·장치별), localhost HTTP 20.1\~50.7 ms(P2·D6)다. 배포 형태가 달라 모델 속도 비교가 아니다. Jev 비용은 1,000 decision당 $0.0197(decision당 평균 469.4 토큰 × README 인용 제3자 단가 $0.042/1M 토큰, 단가 확인 필요)이고 Laya는 토큰 과금 없이 로컬 연산만 든다(summary.md §7).

**파인튜닝 참고선(zero-shot 아님).** T1에서 upstream typed-decisions 파인튜닝 체크포인트는 104/120 = 0.867로 Jev와 같다(b/c 10/10). 한국어 도메인 라우팅 ft-v1은 파일럿 24행에서 22/24 = 0.917로 Jev 20/24 = 0.833 이상이고(p=0.5), ko_massive_domain_8 test 절반에서 0.900이다(Jev는 이 250행을 받지 않았다). 두 선 모두 같은 분포의 train을 쓴 in-domain 결과다(summary.md §3).

**한계.** 플레이그라운드 경유(API 아님, 모델 버전 미표기, 확률 2자리 반올림), 과제당 n=40(CI 약 ±0.15), seed 13 표본의 쉬움(T3), T1 teacher 미확인, Jev의 다문항 공동 평가, 학습 오염(Laya는 upstream 자기 보고로 T2·T5만 학습 믹스, Jev는 알 수 없음), Laya 러너 사후 선택, 8개 검정의 다중 비교(Holm)를 함께 읽어야 한다(summary.md §9).

**3-arm 확장(2026-10-08, `11_three_arm_plan.md` §9, `results/T3arm/summary.md`).** 같은 Jev 항목에 과제 라벨로 파인튜닝한 Laya(trained, 과제당 라벨 약 6,400개, M4 Pro 학습 loop 과제당 1.4-43.3분)를 더하면, Laya 학습 믹스 과제 T9·T10(S7, §7.1d)까지 10과제 모두에서 Holm 후 Jev와 유의차가 없다. 보정 전에는 T3·T8에서 trained가 유의 우세이고 Jev가 유의하게 앞선 과제는 없다. 위 표에서 Holm 후 Jev 유의 우세였던 T1·T7의 격차는 학습 뒤 사라졌다(T7 0.910 대 0.910, T1 0.792 대 0.867, 군집 bootstrap −0.075 [−0.185, +0.025]). T9·T10의 zero-shot Jev vs vanilla는 비유의이고(T9 1.000 대 1.000, T10 0.250 대 0.300), T10은 라벨 품질이 의심된다. 이것은 zero-shot이 아니라 전문화 비교라 위 zero-shot 결론은 바뀌지 않는다. 판정은 seed 14 반복 학습과 결론이 같은 것만 확정한다. 반복 학습(10과제)에서 판정 30개 중 27개가 확정이고 3개(T4·T8 Jev 항목, Holm p 0.05 근처)는 불일치다. trained vs Jev는 9과제가 확정(비유의)이고 T8만 run 2에서 trained 유의 우세다.

---

## 열린 질문 / 가정

1. **(해결, S1)** Multiple questions 모드는 질문 2\~5개·타입 혼합을 지원하지만 Score가 5레벨 고정이라 T1은 A안(4레벨 score 생략, 비교 120)으로 간다(§2, §7.2).
2. **(해결, S1)** Score 비교 규칙은 "argmax 레벨 정확도 + E[level] 기준 MAE"로 고정했다. 플레이그라운드 표시 레벨은 E[level]에 가장 가까운 레벨이라 argmax와 다를 수 있다.
3. **BoolQ·SST-5 소스 경로**(`google/boolq` validation, `SetFit/sst5`)와 라이선스는 빌드 시 확인한다. 라이선스는 2026-10-12에 확인했다: BoolQ는 CC BY-SA 3.0(google-research-datasets/boolean-questions README, HF 카드)이고, SST-5(`SetFit/sst5`)는 어느 원 출처에도 라이선스 표기가 없어 미해결이다(확인 필요, `DATA_LICENSES.md`).
4. **Jev 단가**는 실행 시 공식 페이지에서 확인해 run card에 날짜와 함께 적는다. upstream 인용치 $0.042/1M 토큰은 참고값이다. S6은 이 인용치로 1,000 decision당 $0.0197을 계산했고 공식 단가는 여전히 확인 필요다.
5. **(해결, S6)** ft-v1은 T7 참고선으로 두지 않는다. T7은 intent 과제라 ft-v1(도메인 라우팅)과 과제가 다르다(`results/F/jev_cmp/summary.md` §3).
6. **API 키가 생기면** 같은 세트를 `POST /v1/systemone`으로 재측정해 플레이그라운드 결과와의 차이를 보고하고, 그때 n을 과제당 300\~500으로 올린다.
7. **소논문 재구성 방식**: 08 개정이 아니라 10 신규로 쓰고 08은 한국어 사례 연구로 남기는 것을 기본안으로 둔다.
8. **T4 옵션 렌더링**이 Laya 정확도를 크게 바꿨으므로(§7.0, multilingual +0.175 p=0.016) Jev에도 두 렌더링(key 단독, `key: description`)을 모두 보낼지 결정한다. 예산 +40 요청. S5-b 선택 항목으로 남겼고 실행하지 않았다(§7.2).
9. **Jev Boolean은 설명을 받지 못하므로** T1 noul 비교는 라벨 없는 질문 60개로 한정한다. Laya 쪽 criteria 제거 변형이 noul 정확도를 유의하게 바꾸지 않아(§2) 이 조건이 Laya에 불리하지 않음을 확인했다. T5 BoolQ·T8 prompt-injections도 같은 조건(Jev에는 설명 없음)이다.
10. **T1 teacher 정체 확인**(LocalLLaMA/typed-decisions 데이터 카드): T1 gold는 teacher 분포의 argmax이므로 teacher가 Jev 계열이면 T1은 Jev에 유리한 과제다. S2에서 Jev zero-shot이 이 벤치 train으로 파인튜닝한 Laya 체크포인트와 같은 104/120을 낸 점(§7.1b)의 해석이 이 확인에 달려 있다(확인 필요).
11. **도구 결함(후속 추적): Markdown→PDF 렌더러.** PDF 렌더링에 쓴 Markdown→PDF 렌더러의 smartypants는 HTML 태그를 placeholder로 바꾼 뒤 URL 패턴 `/\bhttps?:\/\/\S+/g`(렌더러의 `src/smartypants.ts:23`)을 적용한다. 링크 텍스트가 URL이면 `\S+`가 바로 뒤의 `</a>` placeholder까지 삼키고 복원은 한 번만 돌아, placeholder 문자열(`SMARTPANTS_PRESERVED_N`)이 본문에 노출되고 `</a>`가 사라져 그 뒤 문서 전체가 링크로 이어진다. 우회: 링크 텍스트에서 URL scheme을 뺀다(`[github.com/x](https://github.com/x)`, 맨 URL 금지). 별도로 GFM은 한 문단·표 칸 안의 `~` 두 개 사이를 취소선으로 렌더링하므로 범위 표기 `~`는 `\~`로 이스케이프한다. 두 우회를 docs/08·docs/10 PDF(공개 저장소에는 포함하지 않음)에 적용했다(2026-10-07). 같은 파일의 em dash 규칙 `/(\w|\s)--(\w|\s)/g`(`src/smartypants.ts:81`)은 본문의 CLI 플래그도 바꿔, `docs/08_paper_ko.md:282`의 `laya-evals --onnx`가 PDF에서 em dash로 찍힌다(우회 없음, 플래그를 코드 스팬으로 감싸면 피한다. 08 내용 변경 금지 지시로 미수정). 우회이며, 렌더러 수정(URL 패턴이 placeholder 경계에서 멈추게) 또는 렌더러 쪽 이슈 등록 여부를 결정해야 한다.

[English](09_laya_vs_jev_plan.md) | **한국어**
