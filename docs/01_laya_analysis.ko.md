# Laya 분석: 아키텍처, API, 공개 수치, 한계 (01_laya_analysis)

**목적**: 벤치마크와 PoC 설계의 근거가 되는 Laya 사실 정리. 여기 적힌 수치는 모두 upstream 공개 수치이고, 우리가 잴 값은 "측정 예정"으로 구분한다.
**선행 문서**: `00_README.md`.
**산출물**: 체크포인트·API 표면 정리, upstream 수치표, Honest limits → 트랙 매핑, M4 Pro 기대치(가설), 가설 H1\~H10.

분석 대상은 laya 0.3.23, upstream 커밋 `4aa6761` (2026-10-01)이다. 파일·라인 인용은 그 커밋 기준이며 `third_party/laya/`(공개 저장소에는 포함하지 않음, https://github.com/NandhaKishorM/laya 를 commit 4aa6761로 clone해 재현)에서 확인할 수 있다.

## 1. 한 줄 요약과 포지셔닝

Laya는 "multilingual, non-autoregressive System 1 decision engine"이다 (출처: README.md 서두). state(텍스트·이메일·JSON)와 typed question 묶음(choice / score / noul)을 받아 encoder forward pass 한 번으로 질문별 확률 분포를 돌려준다. 텍스트 생성이 없으니 파싱할 것도, hallucination 할 것도 없다. 학습은 RLCD(strictly proper scoring rule을 보상으로 쓰는 RL)로 했고, 그래서 확률이 캘리브레이션 되어 있다고 주장한다. Apache 2.0, 완전 로컬 실행.

docs/use-cases.md의 포지셔닝 표를 요약하면 (출처: docs/use-cases.md "Decision Engine vs. LLM vs. Embedding Retrieval"):

| 축 | Embedding retrieval | Laya | Autoregressive LLM |
|---|---|---|---|
| 계산 | 벡터 cosine | forward pass 1회, 디코딩 루프 없음 | 토큰 순차 생성 |
| 호스팅 | in-process / vector DB | in-process(CPU/GPU) 또는 self-hosted HTTP | 원격 API 또는 대형 GPU 서빙 |
| 입력 attention | pooled 벡터 | 전체 입력에 대한 양방향 attention | causal |
| 출력 | 비정형 청크 | 스키마 정렬 분포(choice/score/noul) | 자유 텍스트, JSON 복구 필요 |
| 주 용도 | 후보 검색 | 분류·정책 게이트·라우팅 | 생성·요약·번역 |

벤치마크할 가치가 있는 이유는 넷이다. (1) 레이턴시: T4에서 1질문 32.8 ms, Jev 제3자 공개치 236\~276 ms 대비 6\~7배 (출처: README.md "Benchmarks"). (2) 확률을 게이팅에 쓸 수 있다는 주장. (3) 로컬 실행으로 데이터가 밖으로 나가지 않음. (4) Apache 2.0 가중치.

가장 큰 주의점은 upstream 스스로 적어 둔 것이다. base 체크포인트는 typed-decisions 벤치마크에서 zero-shot으로 chance 근처(0.362 / 0.352, random 0.318, majority 0.461)이고, 0.766은 그 벤치마크의 학습 split으로 파인튠한 체크포인트의 수치다. "Laya is a fast base to specialise, not a zero-shot decision engine" (출처: README.md "Honest limits"). 우리 벤치마크는 바로 이 경계, 즉 "한국어에서 zero-shot으로 어디까지 쓸 수 있는가"를 재는 일이다.

## 2. 아키텍처

**Encoder + decision head.** english와 typed-decisions는 ModernBERT-large(421M, 컨텍스트 512 / 1024), multilingual은 mmBERT-base(322M, 기본 1024, RoPE로 8,192까지) 위에 decision head를 얹었다 (출처: README.md 체크포인트 표). 질문 하나가 forward pass의 한 row가 되고, 한 호출의 질문들은 같은 state를 반복한 row들로 한 배치를 이룬다. 그래서 "질문을 한 호출에 묶는" 것이 GPU 처리량의 원천이고, CPU에서는 row 수에 거의 선형으로 비용이 늘어난다 (출처: examples/36_batch_throughput.py 설명문, BENCHMARKS.md §Server CPU).

**시퀀스 구성과 토큰 예산.** 각 row는 `"<type> question: <instructions>"` + 옵션 렌더링(head) + state로 만들어진다. 예산 규칙은 다음과 같다 (출처: README.md "Honest limits", 구현은 `laya/common.py`의 `build_sequence` / `render_options`):

- `head_max_len`은 head의 **상한**이지 길이가 아니다. 기본값 english 192, multilingual·typed-decisions 256.
- 실제 head 길이는 질문과 옵션 설명이 필요한 만큼만 쓰고, state에 남는 room은 `room = max_len - head_len - 1`이다. upstream 예시: english에서 department 질문의 head가 48토큰이라 state에 463토큰이 남는다(cap 기준 계산값 320이 아니다).
- 옵션당 토큰은 `per = max(4, (head_max_len - 16) // k)`. 옵션 수 k가 `head_max_len / 4` 근방을 넘으면 head가 cap을 **넘어** 자라고 state가 잘린다.

| 체크포인트, max_len | k 옵션 | head | 실제 room | cap 기준 수치 |
|---|---|---|---|---|
| laya, 512 | 77 | 319 | 192 | 320 |
| laya, 512 | 100 | 411 | 100 | 320 |
| laya-multilingual, 1024 | 100 | 411 | 612 | 768 |

(출처: README.md "Honest limits" 표, upstream 공개 수치.) banking77(77 라벨)에서 0.425로 무너지는 이유가 이 규칙이다. 완화책은 `head_max_len` / `max_len`을 호출별로 올리기, `predict_shortlist`로 embedding 기반 top-k 축소, 질문을 coarse/fine 두 단계로 나누기 세 가지다. upstream은 58개 MASSIVE 라벨을 한 질문에 넣었을 때 `--head-max-len 384`로 24/58 → 34/58, CPU 시간 1.4배를 보고했다 (출처: README.md "Command line").

**Temperature.** 체크포인트 로드 시 `(question type, 옵션 수 버킷)`별 temperature를 `[0.5, 5.0]`으로 clamp 한다 (출처: README.md "Calibration", `laya/common.py` TEMP_MIN / TEMP_MAX). multilingual은 출하 시 fitted temperature가 없다.

**답 dict.** `laya/agent.py:1213-1244` 기준 질문별 answer dict 키:

| 키 | 타입별 | 의미 |
|---|---|---|
| `choice` / `score` / `noul` | choice는 라벨, score는 레벨 기대값(0부터 시작하는 인덱스 스케일), noul은 P(true) | 답 |
| `probabilities` | choice: 라벨→p, score: 인덱스→p | 분포 |
| `legend` | score만 | 인덱스→레벨 설명 |
| `confidence` | 전 타입 | choice/score는 1 - 정규화 엔트로피, noul은 max(p, 1-p). 옵션 수에 따라 움직임 |
| `answer_confidence` | 전 타입 | 보고된 답의 확률 max p. 캘리브레이션 대상이며 게이팅은 이 값으로 |
| `action` | 전 타입 | `act_probability` 포함. upstream이 "usable signal 없음"으로 명시 (#185: 거의 항상 1.0, AUROC 0.30 vs confidence 0.77) |

호출 수준에는 `usage.input_tokens / output_tokens`, Router 경유 시 `routing.model / repo / reason`, `predict_long`은 `usage.windows`, `min_confidence` 사용 시 `low_confidence`, `abstention`, `abstention_threshold`가 붙는다 (출처: README.md "Quickstart", "Opt-in abstention").

## 3. 체크포인트와 Router

| 이름 | encoder | params | context | 용도 | 가중치 크기 | HF 경로 | pinned SHA |
|---|---|---|---|---|---|---|---|
| english (`laya`) | ModernBERT-large | 421M | 512 | 영어 | 842.6 MB | `convaiinnovations/laya` (root) | `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` (번들 repo) |
| multilingual | mmBERT-base | 322M | 1024 (8,192까지) | 100+ 언어, english의 약 2배 속도 | 643.8 MB + tokenizer 34.4 MB | 번들 `convaiinnovations/laya/multilingual`, 단독 `convaiinnovations/laya-multilingual` | 단독 repo `e4e9ddf21a7b1903b7acffd8814ad4307bf63a67` |
| typed-decisions | ModernBERT-large | 421M | 1024 | typed-decisions 4개 워크플로(영어) | 842.6 MB | 번들 `.../typed-decisions`, 단독 `convaiinnovations/laya-typed-decisions` | 단독 repo `1a793eb568e6718f15941d08f85432581df534e3` |

(크기는 HF API 조회값, 번들 전체 2.37GB. pinned SHA 출처: `laya/revisions.py` PINNED_REVISIONS.) safetensors 크기가 파라미터당 2바이트이므로 가중치는 bf16/fp16으로 저장되어 있고, CPU/MPS에서는 fp32로 올라간다.

**Router 동작** (출처: README.md "Quickstart: Route Mode", `laya/lang.py`, `laya/router.py:511-525`):

- script 감지가 먼저다. 한글은 `laya/lang.py:43`의 `hangul` 범위(U+1100\~11FF, 3130\~318F, AC00\~D7AF)로 잡혀 **순수 한글이면 multilingual**로 간다. 실측 reason은 "non-Latin script (hangul, 100% of letters); the English checkpoint cannot read it"이다(02 §3.1). 단 라틴 문자가 다수인 혼합문(F1, 예: "Stripe webhook이 timeout 나요")과 dict 필드·대화 턴 속 10음절 미만의 한국어(F2)는 `lang.py:364-371`의 임계값(비라틴 비율 0.2, 또는 0.1이면서 10글자 이상) 때문에 english로 간다. 46건 배터리에서 10건이 실패했고 `lang="ko"`만이 전부를 해결한다(`07_korean_support_audit.md` §4).
- Latin script는 function-word 휴리스틱으로 영어 여부를 판단한다. 짧은 Latin 텍스트는 근거가 없어 `default`(기본 `"english"`)로 떨어진다. 한국어 중심 트래픽에서 영어 알파벳만 있는 짧은 입력(예: "ok", 제품 코드)이 english로 가는 것을 피하려면 `Router(default="multilingual")` 또는 `LAYA_DEFAULT_MODEL=multilingual`을 쓴다.
- 우선순위: 명시 `model=` > `task=` > `lang=`(감지 생략) > `lang_guess`(코드 또는 callable, 영어/비영어만 결정) > 감지 > `default`.
- 메모리: 기본 `max_loaded=2`(english + multilingual LRU). `max_loaded=1`이면 언어가 바뀔 때마다 재로드하고 그 비용이 CPU 7.4 s / T4 10.3 s 중앙값이다. `preload=True`면 세 개 모두 상주. tokenizer는 프로세스당 한 번 파싱해 재사용한다(multilingual tokenizer.json 34 MB) (출처: README.md "Production Preload & Memory").
- `Router.predict_batch`는 먼저 전부 라우팅하고 체크포인트별, 그 안에서 질문 스키마·토큰 예산별로 묶어 `Agent.predict_batch`에 보내고 결과를 원래 순서로 돌려놓는다. 질문 `instructions` 한 글자만 달라도 다른 그룹이다.
- revision 고정: `Router(revision=...)`, `revisions={...}`, 또는 환경변수 `LAYA_REVISION=reviewed`(PINNED_REVISIONS 적용) (출처: `laya/revisions.py`).

## 4. API 표면

**SDK** (출처: README.md, `laya/__init__.py` `__all__`):

| API | 요지 |
|---|---|
| `laya.load(id_or_path, device=, subfolder=, revision=, fast=, compile=, calibration=)` / `Agent` | 단일 체크포인트 로드. `"english"`, `"ml"` 같은 별칭도 받음 (`laya/agent.py:1867`) |
| `Router(models=, device=, revision=, max_loaded=2, default="english", preload=False, lang_guess=, hooks=)` | 라우팅 진입점. `route()`는 forward pass 없이 결정만 반환 (`laya/router.py:511`) |
| `predict(state, questions, model=, lang=, lang_guess=, min_confidence=, max_len=, head_max_len=)` | 질문 묶음을 한 pass로. `system_one`은 동일 |
| `predict_batch(states, questions, batch_size=, sort_by_length=, min_confidence=)` | 같은 질문에 여러 state. `sort_by_length`는 `1 < batch_size < len(states)`일 때만 효과 (`laya/agent.py:1250`) |
| `predict_long(state, questions, window=, stride=)` | 긴 state를 윈도우 스캔. noul은 max, choice/score는 최고 confidence 윈도우, `answer["window"]`로 근거 span 보고 |
| `decide(state, schema=)` / `decide_batch` | JSON schema 또는 pydantic 모델(`laya[structured]`)을 질문으로 변환해 타입 값 반환, `return_details=True`로 필드별 confidence |
| `predict_shortlist(agent, state, questions, embed_fn=, k=)` / `embed_fn_from_agent` / `cached_embed_fn` | 고카디널리티 choice를 embedding top-k로 축소 후 한 pass. `laya.evals_shortlist.evaluate_shortlist`가 retrieval miss / decision miss를 분리 보고 |
| `fit_temperature_map(records)` / `records_from_labeled(agent, pairs)` / `calibration_payload` / `apply_calibration_payload` | 라벨 쌍으로 버킷별 temperature 적합. 버킷 floor `MIN_BUCKET_N=2000`, 타입 floor 10 (출처: `laya/calibrate.py` 모듈 docstring) |
| hooks | `on_predict_start / on_predict_end / on_route / on_load / on_evict / on_error`. start hook은 state 재작성·`ctx.skip()` 가능, end hook은 결과 재작성. `hooks_raise=True` 기본 |
| `min_confidence` | `answer_confidence < T`면 `low_confidence: True`. threshold를 준 호출의 모든 답에 `abstention` ∈ {passed, abstained, unevaluated}와 `abstention_threshold`. 안 주면 payload 불변 |

**Presets** (출처: `laya/presets.py`). 모두 state의 특정 키를 백틱으로 지명하고(`message`, `body`, `prompt`, `post`, `request`), `state_field(questions)`로 그 키를 얻는다. 한국어 PoC에서는 instructions와 criteria를 한국어로 다시 써야 하므로 그대로 쓰지 않고 구조만 참고한다.

| preset | 질문 |
|---|---|
| `triage_questions()` | intent(choice 6: refund, technical_help, billing_question, information, cancellation, other), is_urgent(noul), frustration(score 4), refund_requested(noul), churn_risk(noul) |
| `email_questions(categories=)` | category(choice 6: billing, technical, sales, security, hr, other), is_spam(noul), is_phishing(noul, criteria true/false 명시), urgency(score 3), needs_reply(noul) |
| `guard_questions()` | jailbreak, prompt_injection, sensitive_data(noul 3개), harm_severity(score 4), topic(choice 6, 설명 없음) |
| `moderation_questions()` | toxic, harassment, threat, spam(noul 4개), severity(score 4) |
| `router_questions()` | difficulty(score 4), domain(choice 6: code, math_or_logic, writing, factual_lookup, data_analysis, chitchat), needs_tools(noul), is_sensitive(noul) |

**CLI / HTTP / 기타 표면**:

| 표면 | 요지 |
|---|---|
| `laya "..."` | 기본은 라우팅 결정만(다운로드 없음). `--predict`, `--preset`, `--questions FILE`, `--batch FILE [--batch-size N --sort-by-length --json]`, `--model`, `--lang`, `--lang-guess`, `--min-confidence`, `--max-len`, `--head-max-len` (출처: README.md "Command line") |
| `laya-evals validate / run / compare` | JSONL 라벨셋 평가. `run --model --device --batch-size --sort-by-length --min-confidence --revision --onnx --calibration --slice {language,model,qid,tag} --baseline --tolerance M=V --min-accuracy --max-ece --score-within --min/--max M=V --gate-policy --on-error --json --markdown` (`laya/evals_cli.py:151-215`). 지표: choice_accuracy, noul_accuracy, score_mae, score_within_t, ece(15 bins, `answer_confidence` 기준), mean_confidence, latency_p50/p95_ms, cost_per_decision_p50/p95_ms. 리포트 `config`에 dataset_sha256, questions_sha256, laya_version, revisions, thresholds (출처: docs/evals.md) |
| `laya-serve` | FastAPI. `POST /v1/systemone`, `POST /v1/systemone/batch`(states ≤ 64), `GET /health` (`laya/serve.py:755, 818, 905`). Jev와 같은 wire protocol. 환경변수 `LAYA_HOST / PORT / DEVICE / PRELOAD / MODELS / THREADS / AUTO_TASK / DEFAULT_MODEL / MAX_LOADED / API_KEY / ROOT_PATH / MAX_TOKEN_BUDGET`. choice 옵션 100개 초과는 413(`MAX_CHOICE_OPTIONS = 100`), hook 인자는 422, busy는 `Retry-After` 503 (출처: README.md "Self-Hosting") |
| `laya-mcp-server` | stdio MCP 서버(`laya[mcp]`). `laya_predict_batch`, `laya_route_batch`, `laya_decide` 등 (출처: README.md "What's new in 0.3.21") |
| `examples/server.py` | 웹 GUI 플레이그라운드 + `/predict`, `/predict/batch` JSON API (`laya[serve]`) |
| ONNX | `scripts/export_onnx.py --model --output [--quantize] [--per-channel]`. `--quantize` 기본은 per-tensor INT8(per-channel은 eager 대비 32% 일치로 붕괴, README "What's new in 0.3.23"). `ONNXAgent`가 predict / predict_batch / predict_long / decide_batch 제공, `laya-evals run --onnx`. upstream fixture(12행, english, CPU) p50: torch 116.8 ms, onnx fp32 66.3 ms, int8 46.3 ms, 정확도 동일, score_mae +0.009, ece +0.006 (출처: docs/evals.md "Evaluating an ONNX export") |
| TileLang fast path | `laya[fast]`, `load(..., fast=True)`. CUDA 전용, CPU/MPS는 stock forward로 fallback. 이 Mac에서는 측정 불가 |
| TypeScript | `laya-ts`(브라우저/Node에서 ONNX 로컬 추론), `laya-client`(`sdk/typescript`, laya-serve HTTP 클라이언트) |
| Docker | `compose.yaml`(CPU), `compose.cuda.yaml`, `compose.spark.yaml`(GB10/aarch64), `compose.modelscope.yaml`, `compose.http.yaml`. CPU 퀵스타트 요구 RAM 8GB, 디스크 10GB (출처: docs/docker.md) |
| 예제·검증 스크립트 | `examples/` 41개 학습 경로 스크립트(17 타이밍, 33 고카디널리티, 34 temperature, 35 디바이스, 36 처리량). `verify/`의 `bench_devices.py`, `soak_check.py`, `numerics_check.py`, `edge_sweep.py`, `laya_smoke_test.py`. `research/scripts/`의 `bench_local.py`(MASSIVE 51개 언어), `bench_apps.py`, `bench_latency.py`, `bench_length_batching.py`, `bench_long_context.py`. research 스크립트는 `LAYA_MODELS` 아래 `laya/`, `laya-multilingual/`, `laya-typed-decisions/` 디렉토리를 기대한다 (출처: research/README.md) |

## 5. 공개 벤치마크 수치 (upstream)

전부 upstream이 공개한 수치다. Jev 수치는 **upstream이 측정한 것이 아니라 제3자 공개치**이며 샘플 수와 프롬프트가 다르다 (출처: BENCHMARKS.md 서두, research/README.md "On comparisons with Jev").

**(a) MASSIVE intent, 51개 언어, 20옵션 (random 0.050)** (출처: BENCHMARKS.md §Languages, refreshed 재실행 값. committed multilingual 파일은 재현되지 않아 refreshed로 교체됨, #208)

| | laya | laya-multilingual |
|---|---|---|
| macro accuracy | 0.2269 | 0.4008 |
| macro ECE | 0.5709 | 0.3911 |
| 3x random 초과 언어 | 23 / 51 | 48 / 51 |
| `ko` accuracy / ECE | 0.110 / 0.680 | **0.470 / 0.311** |
| `en` accuracy / ECE | 0.820 / 0.138 | 0.710 / 0.233 |
| `zh-CN` accuracy / ECE (0.3.20 재실행, per-lang 100) | 0.620 / 0.320 | 0.650 / 0.219 |

zh-CN 행은 §Community evaluation의 Part A 재실행 값이다. 영어 체크포인트는 비Latin script에서 자신 있게 틀린다. Khmer 0.000 정확도에 raw confidence 0.952(clamp 후 0.705) (출처: BENCHMARKS.md §English vs the rest).

T4 Colab 세트(MASSIVE 14개 언어, XNLI 15개 언어) (출처: BENCHMARKS.md §English vs the rest, laya / multilingual 순): MASSIVE intent en 0.783 / 0.657, 그 외 0.306 / 0.451. MASSIVE scenario en 0.603 / 0.560, 그 외 0.281 / 0.439. XNLI en 0.860 / 0.843, 그 외 0.521 / 0.731.

**(b) typed-decisions, 400 case 2,000 decisions** (출처: BENCHMARKS.md §typed-decisions)

| 모델 | accuracy | soft acc | Brier | ECE | score MAE |
|---|---|---|---|---|---|
| laya-typed-decisions (파인튠) | 0.766 | 0.471 | 0.061 | 0.213 | 0.242 |
| laya | 0.362 | 0.332 | 0.316 | 0.175 | 0.694 |
| laya-multilingual | 0.352 | 0.328 | 0.463 | 0.314 | 0.760 |
| Jev 1.13.0 (제3자 공개) | 0.727 | 0.580 | 0.148 | 0.144 | 0.391 |
| teacher 상한 / majority / random | 0.735 / 0.461 / 0.318 | | | | |

**(c) 응용 워크플로 Themes, N=400, laya 0.2.1, CPU** (출처: BENCHMARKS.md §Themes)

| theme | laya | multilingual | typed-decisions | 데이터 |
|---|---|---|---|---|
| Email spam | 0.993 | 0.993 | 0.958 | in training |
| Phishing | 0.980 | 0.993 | 0.940 | in training |
| LLM guardrails (jailbreak) | 0.708 | 0.755 | 0.762 | held out |
| Moderation (toxicity) | 0.530 | 0.525 | 0.530 | held out (macro-F1 0.400) |
| RAG passage relevance | 0.625 | 0.657 | 0.625 | in training |
| Support triage (10-way) | 0.502 | 0.522 | 0.505 | in training |
| Model routing (domain) | 0.639 | 0.123 | 0.659 | held out |

**(d) Jev 공개 수치가 있는 공개 데이터셋** (출처: BENCHMARKS.md §On the public datasets where Jev numbers exist)

| 데이터셋 | laya | multilingual | typed-decisions | Jev (제3자) |
|---|---|---|---|---|
| AG News (4) | 0.950 | 0.930 | 0.953 | 0.910 |
| DAIR Emotion (6) | 0.595 | 0.530 | 0.600 | 0.480 |
| banking77 (77. Jev는 72) | 0.425 | 0.425 | 0.492 | 0.870 |

**(e) 속도, Tesla T4** (출처: BENCHMARKS.md §Speed)

| 질문/호출 | laya | laya-multilingual |
|---|---|---|
| 1 | 39.5 ms | 32.8 ms |
| 5 | 84.5 ms | 40.1 ms |
| 10 | 158.6 ms (15.9 ms/q) | 72.3 ms (7.2 ms/q) |
| 50 | 771.3 ms | 337.4 ms |

배치 처리량 103\~332 질문/초. Jev 제3자 측정 p50 236\~276 ms.

**(f) 캘리브레이션** (출처: BENCHMARKS.md §Calibration): 출하 ECE laya 0.466 → refit 0.081, multilingual 0.314 → 0.106. refit은 (question type, 옵션 수) 버킷별 temperature 하나씩, held-out 데이터로.

**(g) option-order flip rate** (출처: BENCHMARKS.md §Option-order robustness, laya / multilingual 순): massive_intent.en 0.150 / 0.230, en.emotion 0.040 / 0.090, xnli.en 0.000 / 0.015. Jev 제3자 측정 0.13.

**(h) zh 커뮤니티 벤치, 우리가 한국어로 만들 것의 가장 가까운 선례** (출처: BENCHMARKS.md §Community evaluation, laya 0.3.20 CUDA, acc / ECE)

| 태스크 (n) | multilingual | english |
|---|---|---|
| voice routing, 6-domain (179) | 0.883 / 0.061 | 0.754 / 0.281 |
| CS routing (25) | 0.640 / 0.293 | 0.520 / 0.184 |
| urgency score (25) | 0.560 / 0.091 | 0.520 / 0.207 |
| scam/promo (15) | 0.667 / 0.311 | 0.667 / 0.321 |
| escalate noul (40) | 0.550 / 0.230 | 0.575 / 0.269 |

option-order flip 28%(CS) / 10.6%(voice), zh-CN → zh-TW 병렬 발화 flip 12.8%. temperature refit에서 `noul:2` 버킷 raw T 10.23이 clamp 상한 5.0에 걸렸고(ECE 0.180 → 0.098), `choice:6-10`은 refit 후 오히려 0.062 → 0.093으로 나빠졌다. 작은 n에서 refit은 쉽게 과적합한다는 뜻이고, 우리 Track E의 held-out 설계 근거다.

## 6. Honest limits → 우리 벤치마크 매핑

| 한계 | upstream 근거 | 우리가 검증할 트랙 / 프로브 |
|---|---|---|
| base 체크포인트는 zero-shot typed-decisions에서 chance 근처 | 0.362 / 0.352 vs random 0.318, majority 0.461 (출처: README.md "Honest limits") | Track B 전 세트에 majority/random 베이스라인을 같이 보고. `ko_poc_triage_v1`에서 zero-shot 상한 확인 |
| 옵션 20개 초과 시 head budget 붕괴 | banking77 0.425, `per = max(4, (head_max_len-16)//k)` (출처: README.md "Honest limits") | Track C: `ko_massive_intent_full60.jsonl`에서 기본 budget vs `head_max_len=512, max_len=1024` vs `predict_shortlist(k=20)` 비교 |
| noul이 state 대신 라벨을 따라감 (english에서 가장 심함) | #156: criteria는 true/false 키만, `labels`로 표기 변경, criteria 없는 noul은 english에서 항상 "no" (출처: README.md "Honest limits") | Track C: `ko_nsmc_sentiment.jsonl`의 noul+criteria(정규) / `--opaque-labels`(labels A·B) / 2-choice 의미 키(positive·negative) / `--opaque-keys`(A·B) 네 변형을 돌려 비교(04 §5.4). PoC 스키마의 criteria-less noul vs `triage_v1b.json`(+criteria)은 Track C2 사다리 |
| 부정문 실패 | #377: 부정된 취소 요청 4건 전부 `cancel_account` 선택(laya), multilingual 2건, 한 건은 p=0.9998 (출처: README.md "Honest limits") | Track C: `ko_negation_probe.jsonl`(긍정 통제군 + 부정문 쌍) |
| boolean 단어 라벨(true/false, yes/no) 금지 | 라벨 문자열이 그대로 렌더링됨 (출처: README.md "Honest limits") | 모든 한국어 스키마 설계 규칙으로 반영(`04_korean_evalset_spec.md`). 별도 프로브는 하지 않음 |
| multilingual의 score 첫 레벨 회피 편향 | #131, 모든 언어 (출처: README.md "Honest limits") | Track C: triage 스키마의 frustration/urgency score에서 레벨 분포 vs gold 분포 비교, 레벨 순서 뒤집기 |
| 출하 시 over-confident, multilingual은 temperature 없음 | ECE 0.466 / 0.314 출하 (출처: BENCHMARKS.md §Calibration). 단 라우팅 태스크 한 건은 under-confident (출처: BENCHMARKS.md §Other hardware "Calibration on a routing task") | Track E: 출하 ECE 측정 → `fit_temperature_map`으로 refit → held-out ECE, coverage@error 곡선. 방향(over/under)을 세트별로 기록 |
| option-order 불안정 | 0.150 / 0.230 at 20옵션 (출처: BENCHMARKS.md §Option-order robustness) | Track C: `ko_klue_ynat_7`, `ko_massive_intent_20opt`, PoC 스키마에서 permutation flip rate |
| moderation은 held-out에서 약함 | 0.530, macro-F1 0.400 (출처: BENCHMARKS.md §Themes) | Track B: `ko_kmhas_hate.jsonl`로 한국어 혐오 발언 noul/choice. PoC B안 리스크 근거 |
| criteria·시나리오·JSON state 추가가 noul을 always-true로 만듦 (zh) | noul_plain 0.667 → noul_json_state 0.417(always-true 기준선과 동일) (출처: research/benchmarks/zh_short_commands/README.md) | Track C: 한국어 짧은 명령 18\~30건으로 같은 ladder 재현(plain / criteria / scenario / json_state) |
| 긴 문서는 위치 민감, 문서 내부 위치는 majority floor | 4,000 토큰 filler에서 pos 0.25 0.550 vs pos 1.00 0.950, n=20 (출처: research/README.md "Headline findings") | Track C 선택: `predict_long` vs 단일 윈도우 비교는 PoC 시나리오에 긴 입력이 있을 때만 |
| `act_probability`는 신호 없음 | #185 AUROC 0.30 (출처: README.md "Honest limits") | 측정하지 않음. 게이팅은 `answer_confidence`만 사용 |
| CPU에서 질문 수에 선형 비용 | EPYC 4코어: english \~600 ms/질문, multilingual \~185 ms/질문. GPU는 sub-linear (출처: BENCHMARKS.md §Server CPU, §Speed) | Track D: CPU vs MPS에서 1/3/5/10 질문 스케일링 곡선 |

## 7. 하드웨어별 레이턴시 참고치와 M4 Pro 기대치

**upstream 공개 측정치.** 모두 upstream 또는 기여자 측정이고 조건이 다르므로 서로 직접 비교하지 않는다.

| 환경 | 조건 | 수치 | 출처 |
|---|---|---|---|
| Tesla T4 | in-process, 1 / 10 질문 | multilingual 32.8 / 72.3 ms, english 39.5 / 158.6 ms | BENCHMARKS.md §Speed |
| AMD EPYC 9R14, 4코어 (m7a.xlarge), fp32, torch 2.14.0 | in-process, 1 / 5 / 10 / 50 질문 | english 580 / 3,072 / 6,244 / 35,969 ms, multilingual 193 / 912 / 1,842 / 11,157 ms. cold load 4.4 s / 2.5 s. 전체 스크립트 peak RSS 9.3 GiB(최대 5개 로드) | BENCHMARKS.md §Server CPU |
| Ryzen 9 6900HX, WSL2 (체크포인트 미기재) | HTTP 경유 3질문, torch 기본 스레드 → intra 8 + inter-op 1 | p50 9,396 ms → 783 ms (12x). in-process 1질문 8 threads p50 329 ms, p95 378 ms | BENCHMARKS.md §Other hardware |
| Intel Arc B390 XPU vs 같은 노트북 CPU, english | 1 / 3 / 10 질문 | XPU 29.7 / 45.4 / 96.9 ms, CPU 288.2 / 730.6 / 2,608.7 ms | BENCHMARKS.md §Other hardware |
| NVIDIA GB10 (DGX Spark), HTTP 경유, typed-decisions | 1 / 50 질문 | p50 100.2 / 443.1 ms, 질문당 \~7.0 ms, 고정 오버헤드 \~93 ms | BENCHMARKS.md §Other hardware |
| NVIDIA RTX, TileLang fast path (GPU 모델은 해당 절 참조) | 1질문 72 tok, stock → fast | english 17.7 → 4.6 ms, multilingual 14.1 → 2.8 ms | BENCHMARKS.md §GPU fast path |
| H100 NVL, TensorRT FP16 서빙 (외부 연구) | p99 ≤ 50 / ≤ 130 ms SLO | 105 / 175 decisions/s. RTX PRO 6000은 146 decisions/s @ 130 ms | BENCHMARKS.md §Independent NVIDIA CUDA capacity study |
| Apple GPU (MPS), multilingual max_len=8192 | 4,000 토큰 입력 | 약 1.7 s | README.md "Quickstart" 롱 문서 노트 |
| Apple silicon, CLI `--batch` 128 Yelp 리뷰, batch 8 | unsorted vs sorted | 41.25 s → 29.23 s (1.42x), 결정 변화 0 | README.md "Command line" |
| Apple M-series MPS, `decide_batch` 8 티켓 | 개별 호출 vs batch | 2,624 ms → 723 ms (3.6x) | README.md "Schema-driven decisions" |

**이 Mac(Apple M4 Pro, 10P+4E, 20코어 GPU, 48GB)에 대한 기대치와 측정값.** 가설은 2026-10-02에 적은 값이고, 측정은 2026-10-03 Track D(`results/D/D_summary_20261003.md`)다. 가설 열은 예측 오차 기록용으로 남긴다.

| 항목 | 가설 범위 (2026-10-02) | 측정 (2026-10-03) | 판정 |
|---|---|---|---|
| CPU fp32, 10 threads, inter-op 1, 1질문 | multilingual 120\~250 ms, english 300\~600 ms | multilingual 37.7 ms (short 59 tok) / 81.8 (long 433), english 86.6 / 204.5 | 가설보다 2.1\~3.5배 빠름 |
| CPU, 질문 수 스케일링 | 1 → 10 질문에서 7\~10배 | short 3.22\~5.69배, long 7.29\~8.65배 | 긴 입력만 선형 |
| MPS, 1질문, 워밍업 후 | 30\~80 ms | multilingual 13.8 ms, english 31.8 ms | 하한보다 빠름 |
| MPS, 질문 수 스케일링 | 1 → 10 질문에서 2\~4배 (sub-linear) | 4.52\~9.05배 | 기각(선형에 가까움) |
| MPS 첫 호출 | 새 shape마다 수 초, 최초 약 13 s Metal 커널 컴파일 (examples/README.md) | 약 0.1 s | 기각 |
| `predict_batch(sort_by_length=True)`, 혼합 길이 한국어 | CPU 1.3\~2.0x, MPS 1.4\~1.8x | CPU unsorted 대비 1.67\~2.08x (n=256), loop 대비 1.29\~1.42x; MPS loop 대비 1.21\~1.25x | CPU 지지, MPS 하한 미달 |
| cold load (디스크 캐시 warm) | multilingual 2\~4 s, english 3\~6 s | multilingual 3.45\~3.67 s (tokenizer 약 1.0 s), english 2.82\~2.97 s | multilingual 범위 안, english 가설보다 빠름 |
| 메모리 | english ≈ 1.7 GB, multilingual ≈ 1.3 GB (fp32 상주). 셋 preload ≈ 5 GB | CPU RSS 상주 1개 2.07 GiB(multilingual, 런타임 포함), +english 1.57, +typed 1.60 → 셋 5.23 GiB | 자릿수 일치 |
| MPS vs CPU (1질문) | 3\~6배 | 2.33\~2.80배 | 가설 하한 미달 |

## 8. 라이선스·운영 고려사항

- **라이선스**: 코드와 가중치 모두 Apache 2.0 (출처: README.md "License", HF 태그 `license:apache-2.0`). 상용 사용 가능.
- **완전 로컬**: upstream 규칙상 호스팅 서비스 의존 기능은 들어오지 않는다 (출처: AGENTS.md "Do NOT"). 첫 다운로드 후 `HF_HUB_OFFLINE=1`로 네트워크를 끊어도 동작한다.
- **공급망 고정**: `LAYA_REVISION=reviewed` 또는 `revision=`으로 커밋 고정, `LAYA_SHA256_DIGESTS` / `expected_sha256`로 파일 digest 검증 (출처: `laya/revisions.py`). 우리 리포트는 `laya-evals`의 `config.revisions`로 어떤 커밋이 답했는지 남긴다.
- **보안 변경(0.3.23)**: `LAYA_API_KEY`가 설정된 서버에서 `GET /health`는 liveness만 공개하고 체크포인트 이름·SHA·디바이스 상태는 bearer가 있어야 준다 (#812, 출처: README.md "What's new in 0.3.23"). 비공개 취약점 보고는 SECURITY.md.
- **CPU 스레드**: `torch.set_num_threads(물리 코어 수 근처)`, `set_num_interop_threads(1)`. upstream은 기본값 방치가 12배 느린 사례를 보고했다 (출처: BENCHMARKS.md §Other hardware). `laya-serve`는 `LAYA_THREADS`.
- **dtype과 threshold**: CUDA bf16은 fp32 대비 864개 argmax 중 3개 flip, fp16은 0 (출처: README.md "Automated Confidence Gating"). MPS는 5 row 이상에서 fp16. threshold는 **서빙할 dtype에서** 적합·검증해야 한다.
- **Docker/CUDA 전용 노트**: `TORCH_DISABLE_NATIVE_JIT=1`은 slim CUDA 이미지의 Triton 컴파일 실패(#365) 대응이며 이 Mac에서는 무관하다 (출처: docs/docker.md).
- **동시성**: 0.3.23에서 GPU OOM fallback이 reader-writer gate로 격리되어 진행 중 요청을 깨지 않는다 (#649). MPS에서의 동시 요청 동작은 측정 예정(PoC P2).

## 9. 벤치마크 설계에 주는 함의 (가설 H1\~H10)

각 가설은 `03_benchmark_plan.md`의 트랙에 대응한다. 판정 기준은 그 문서에서 확정한다.

| # | 가설 | 트랙 | 근거 |
|---|---|---|---|
| H1 | `ko_massive_intent_20opt`를 CPU fp32로 돌리면 multilingual 0.470 ± 0.03, english 0.110 ± 0.03이 재현된다 | A | BENCHMARKS.md §Languages `ko` 행. 변환이 seed 13·처음 100행·20옵션을 그대로 따르면 결정론적 |
| H2 | 한글 state는 Router가 100% multilingual로 보내고, 모든 한국어 세트에서 multilingual이 english를 크게 앞선다 | B | `laya/lang.py:43` hangul 범위, ko 0.470 vs 0.110 (07 §4: 혼합문·짧은 한국어는 예외) |
| H3 | 옵션 ≤7개 한국어 topic/intent/NLI(YNAT, 3i4K, KLUE-NLI)에서 zero-shot 정확도는 majority를 크게 넘지만 supervised 한국어 encoder 공개치에는 못 미친다 | B, F | zh 6-domain 0.883 vs CS routing 0.640. 도메인·옵션 수에 따라 폭이 크다 |
| H4 | 한국어에서 출하 ECE는 0.25 이상이고, 버킷별 refit 후 held-out ECE ≤ 0.10. 단 n이 작은 버킷(zh의 choice:6-10 사례)은 refit이 악화시킬 수 있다 | E | §Calibration 0.314 → 0.106, zh refit 표 |
| H5 | 한국어 7\~20옵션 choice의 option-order flip rate는 10\~30% | C | upstream 0.150 / 0.230(20옵션), zh 28% / 10.6% |
| H6 | 한국어 이진 판단은 noul보다 중립 키(A/B) 2-choice가 더 정확하고, criteria 추가는 noul을 always-true 쪽으로 밀 수 있다 | C | #156, zh_short_commands ladder. P0b 프로브(n=30)에서는 2-choice A/B가 A로 붕괴해 반대 신호 (`results/poc/P0b_20261002.md`) |
| H7 | 부정문 프로브는 zero-shot에서 실패한다(부정 요청의 절반 이상을 긍정으로 분류) | C | #377 |
| H8 | MPS 1질문은 CPU 10 threads 대비 3\~6배 빠르고 질문 수 증가에 sub-linear하다. CPU는 선형이다 | D | §Speed, §Server CPU, Arc 비교. 판정(2026-10-03): **기각**(MPS/CPU 1q 2.33\~2.80배, 10q/1q MPS 4.52\~9.05, `results/D/D_summary_20261003.md`) |
| H9 | 혼합 길이 한국어 64건에서 `sort_by_length=True`는 CPU에서 ≥ 1.3배, argmax 변화 0, max \|Δp\| ≤ 0.01 | D | research/README.md "Length batching" 2.15x, 변화 0. 판정(2026-10-03): **지지**(n=256 unsorted 대비 1.67\~2.08배, loop 대비 1.29\~1.42배, flip 0, 0.0001) |
| H10 | ONNX INT8(per-tensor)은 CPU에서 torch 대비 ≤ 0.6배 시간, \|ΔECE\| ≤ 0.01, choice_accuracy 차 ≤ 0.01 (03 §1 기준으로 통일) | D | docs/evals.md 116.8 → 46.3 ms, ece +0.006. 판정(2026-10-03): **기각**(int8 1.74배 느림, ΔECE +0.0154, Δacc −0.012, argmax 일치 0.930) |

H1이 깨지면 측정 파이프라인 문제다. H2\~H7은 "한국어에서 zero-shot으로 믿을 수 있는 영역"을 그리고, H8\~H10은 배포 형태(MPS in-process, CPU ONNX, HTTP)를 정한다.

## 열린 질문 / 가정

- §7의 M4 Pro 수치는 전부 가설이다. Track D 결과로 §7 표를 갱신하되, 가설 열은 지우지 않고 "가설 vs 측정" 두 열로 남겨 예측 오차를 기록한다.
- mmBERT-base의 한국어 토크나이저 효율(글자당 토큰 수)을 아직 재지 않았다. 한국어는 Latin 언어보다 토큰이 많이 들 수 있어 `room`이 더 빨리 소진된다. Phase 1에서 세트별 평균 토큰 수를 기록한다.
- Jev 수치는 전부 제3자 공개치다. 우리 리포트에서도 같은 표기(제3자, 미측정)를 유지한다.
- typed-decisions 체크포인트는 영어 워크플로 전용이라 `auto_task_detection=False` 기본값에서 Router가 고르지 않는다. 명시 `model="typed-decisions"`로 한국어를 넣는 실험은 Track B에서 참고용 1회만 한다.
- upstream 51개 언어 표의 multilingual 열은 committed 파일이 아니라 refreshed 재실행 값이다(#208). 우리가 비교 기준으로 쓰는 ko 0.470도 refreshed 값이다. committed 값은 참조하지 않는다.
- `laya-evals`의 ECE는 `answer_confidence` 기준 15 bins다. BENCHMARKS.md의 ECE가 같은 정의인지는 `research/scripts/bench_local.py`의 `metrics()`에서 확인해야 한다. 정의가 다르면 Track A 재현 판정은 accuracy만으로 하고 ECE는 참고치로 둔다.

[English](01_laya_analysis.md) | **한국어**
