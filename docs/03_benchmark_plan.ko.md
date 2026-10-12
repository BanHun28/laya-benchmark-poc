# 03. Laya 벤치마크 계획

**목적**: Laya 0.3.23의 세 체크포인트와 Router를 이 Mac(M4 Pro)에서 한국어 중심으로 측정해 01_laya_analysis.md §9의 가설 H1\~H10을 판정하고, 00_README.md §6 Go/No-Go와 05_poc_plan.md 설계 결정에 측정 근거를 공급한다.
**선행 문서**: 00_README.md(진행 순서, Go/No-Go), 01_laya_analysis.md(§9 가설), 02_environment_setup.md(환경, 스모크 테스트), 04_korean_evalset_spec.md(평가셋 구축), 06_templates.md(런 카드, REPORT 템플릿).
**산출물**: `results/<track>/*.json|.md`, `results/REPORT.md`, `poc/calibration/ko_v1.json`, `scripts/*.py`(§3.8 스펙대로 구현).

모든 명령은 프로젝트 루트에서 `source env.sh` 후 실행한다. upstream 공개 수치에는 전부 출처를 붙였고, 우리 수치는 전부 "측정 예정"이다.

## 1. 목표와 결정 질문

이 벤치마크는 아래 다섯 결정에 답하기 위해 존재한다. 결정에 영향을 주지 않는 측정은 하지 않는다.

| # | 결정 질문 | 근거 트랙 | 관련 가설 |
|---|---|---|---|
| Q1 | PoC 시나리오(05 = C 도메인 라우터, `ko_massive_domain_8`)에 Laya를 zero-shot으로 채택할 수 있는가 | B, C, F | H3, H5, H6, H7 |
| Q2 | 어느 체크포인트를 쓰는가 (english / multilingual / typed-decisions / Router auto) | A, B | H1, H2 |
| Q3 | 배포 형태는 무엇인가 (CPU torch / MPS / ONNX int8 CPU / laya-serve) | D | H8, H9, H10 |
| Q4 | confidence gating 정책 (min_confidence 값, 기대 coverage, 보정 payload) | E | H4 |
| Q5 | 파인튜닝(05 P4)이 필요한가, zero-shot + gating으로 충분한가 | B, E, F | H3, H4 |

(결정 질문 번호는 Q로 적어 Track D의 단계 번호 D1\~D8과 구분한다.)

가설별 판정 기준. 수치는 CPU fp32 기준이고 bootstrap 95% CI를 함께 보고한다(§3.6).

| 가설 | 트랙 | 판정 기준 (지지 조건) | 판정(2026-10-02) |
|---|---|---|---|
| H1 ko MASSIVE 재현 | A | ko: laya 0.110 / multilingual 0.470, en: 0.820 / 0.710 각각 ±0.03 이내 (출처: BENCHMARKS.md:71, §Languages 표) | **지지**. 4칸 모두 Δ 0.000, ECE도 일치 (`results/A/README.md`) |
| H2 multilingual ≫ english, Router 100% | B | 모든 ko 세트에서 multilingual 정확도 − english 정확도 ≥ +0.20; Router auto 런의 `model` slice가 100% multilingual | **부분 지지**. 10개 질문 중 7개에서 ≥ +0.20(예외 NSMC noul +0.122, K-MHaS hate +0.082, 3i4K +0.004). 한글이 있는 행은 100% multilingual, 한글 없는 행 4개만 default (`results/B/summary_20261002.md`) |
| H3 ≤7옵션 과제: majority 위, supervised 아래 | B, F | 정확도 ≥ majority + 0.20 이고 supervised 문헌값 미만 | 전반부 **지지**(choice 과제, 3i4K 제외). noul 두 세트는 미달(always-false 편향). 후반부 **미결**(F3 문헌값 미조회) |
| H4 as-shipped ECE > 0.25, refit 후 ≤ 0.10 | E | ko 세트 절반 이상에서 as-shipped ECE > 0.25; held-out 절반에서 refit 후 ECE ≤ 0.10 | 전반부 **부분**(domain_8 test 0.263은 초과, ynat 0.148은 미만). 후반부 **지지(경계)**: pooled refit 후 domain_8 test 0.098, ynat 0.063 (`results/E/E_summary_20261002.md`) |
| H5 옵션 순서 flip 10\~30% | C | 7\~20옵션 세트의 per-permutation flip rate가 0.10\~0.30 | **지지**. domain_8 0.270, ynat_7 0.168, scenario_18 0.241 (`results/C/C1_option_order_20261002.md`) |
| H6 noul < 2-choice(중립 키) | C | NSMC에서 A/B 2-choice 정확도 − noul 정확도 ≥ +0.05, McNemar p < 0.05 (P0b 조기 신호는 반대 방향; C3에서 판정) | **미결**. C3 미실행. NSMC의 의미 key choice 0.774 > noul 0.638(p=6.5e-10)은 중립 키 조건이 아니라 참고치 |
| H7 부정문 zero-shot 실패 | C | 긍정 절반 정확도 ≥ 0.80 인데 부정 절반 ≤ 0.50 | **미결**. C4 미실행(ko_negation_probe 미구축) |
| H8 MPS 1문항 3\~6x, 문항 수에 sub-linear | D | mps 1q median ≤ cpu 1q / 3; mps 10q/1q 비 ≤ 3 이면서 cpu 10q/1q 비 ≥ 7 | **기각**(2026-10-03 D1: MPS/CPU 1q 2.33\~2.80배, 10q/1q MPS 4.52\~9.05 vs CPU 3.22\~8.65. `results/D/D_summary_20261003.md`) |
| H9 sort_by_length ≥ 1.3x, flip 0 | D | 혼합 길이 한국어 256건, CPU, paired median speedup ≥ 1.3x, argmax flip 0 | **지지**(2026-10-03 D4: n=256 unsorted 대비 1.67 / 1.83 / 2.08배(bs 8/16/32), loop 대비 1.39 / 1.42 / 1.29배, flip 0, max \|Δp\| 0.0001) |
| H10 ONNX int8 ≈ 2x, ECE drift ≤ 0.01 | D | int8 latency ≤ torch CPU × 0.6, \|ΔECE\| ≤ 0.01, choice_accuracy 차 ≤ 0.01 | **기각**(2026-10-03 D7: int8 525.9 ms vs torch 302.2 ms로 1.74배 느림, ΔECE +0.0154, Δacc −0.012, argmax 일치 0.930) |

파인튜닝 체크포인트 ft-v1(05 P4, 2026-10-03)은 PoC 게이트(G1\~G4)를 바꾸지만 H1\~H7은 zero-shot 체크포인트에 대한 가설이므로 판정을 바꾸지 않는다. ft-v1의 수치(domain_8 test 0.900, flip 0.037, ECE 0.053)는 `results/go_no_go.json`과 05 §6 P4에 기록한다.

## 2. 범위와 비범위

포함:
- 체크포인트 3종 + Router auto, laya 0.3.23, 체크포인트 reviewed SHA pin(02 참조).
- 04_korean_evalset_spec.md의 한국어 세트 전부. 영어는 대조군(MASSIVE en, upstream fixture)으로만.
- 디바이스: CPU fp32(정확도 기준), MPS(지연 기준), ONNX Runtime CPU(fp32, int8).
- laya-serve HTTP 로컬 부하 측정.
- temperature refit과 coverage 곡선.
- 베이스라인: majority/random, LLM zero-shot(선택), supervised 문헌값, Jev 공개 수치.

제외:
- Jev API 직접 측정. 접근 권한이 없고 upstream도 미측정이다(출처: research/README.md §On comparisons with Jev).
- 파인튜닝. 05_poc_plan.md P4에서만 다룬다. 2026-10-02에 P4가 시작됐다: 1,000행 1 epoch 프로브로 domain_8 test 0.492 → 0.720, YNAT 망각 없음(`results/P4/P4_probe_20261002.md`). 본 학습은 GPU 큐가 비면 자동 시작.
- CUDA, TileLang fast path, torch.compile. 이 머신에 NVIDIA GPU가 없으므로 upstream 수치만 인용.
- 학습 데이터 오염 감사. upstream의 "in training mix / held out" 표기만 전달(출처: BENCHMARKS.md §Themes).
- MCP 서버, LangChain/CrewAI/LlamaIndex 래퍼, TypeScript SDK. 05에서 필요 시 기능 확인만.
- 장문(long context)은 n=20 지표성 측정까지만.

## 3. 공통 프로토콜

### 3.1 run identity

- 각 트랙 시작 전 02_environment_setup.md의 환경 스냅샷 단계를 재실행해 `results/env/env_<YYYYMMDD-HHMM>.json`을 남긴다.
- 모든 스크립트는 06_templates.md §1 런 카드 필드를 stdout과 결과 JSON의 `run_card`에 기록한다: laya_version, torch, transformers, 디바이스, dtype, 스레드(intra/inter), 체크포인트 SHA, dataset_sha256, questions_sha256, 시작 시각, 전원 상태(`pmset -g batt` 요약), 스크립트 리포가 git이면 git SHA.
- `laya-evals run --json`은 `config` 블록에 dataset_sha256, questions_sha256, laya_version, revisions, thresholds, timing을 스스로 기록한다(출처: docs/evals.md §Run identity). Hub 캐시로 로드되면 `revisions`에 커밋이 찍히지만, `models/`(공개 저장소에는 포함하지 않음) 심볼릭 링크의 하위 폴더(`laya-multilingual`, `laya-typed-decisions`)는 `snapshot_revision()`이 None을 돌려주므로(laya/revisions.py `snapshot_revision`) 로컬 경로를 쓰는 우리 스크립트는 SHA를 런 카드에 직접 기록한다.
- 체크포인트 pin은 env.sh의 `LAYA_REVISION=reviewed`가 Hub 로드 전부에 적용된다(laya/revisions.py `resolve_revision`).

### 3.2 데이터 규칙

- 레이블 정책은 모델을 돌리기 전에 04에서 확정하고 파일을 해시한다. 모델 결과를 보고 레이블을 고치면 새 파일명(`_v2`)으로만 만든다.
- 평가 항목은 전부 test/validation split. dev/test 50/50 분할의 단일 출처는 `results/B/B_splits.json`(`scripts/metrics_extra.py` `row_splits`)이다: 쌍 MASSIVE 세트(ko/en domain_8, ko/en intent_20opt)는 행 index parity(짝수 dev, 홀수 test, 두 파일이 같은 id 순서), 나머지 세트는 state JSON의 sha256 홀짝이다. 보정 fit(Track E)과 ablation은 dev 절반만 쓰고 새 분할(hash50)을 만들지 않는다. test 절반은 동결된 스키마 버전마다 한 번만 채점한다.
- seed 13(upstream `SEED`와 동일: research/scripts/bench_local.py 상단), 레이블 층화 추출. 크기: MASSIVE 재현용 100, 그 외 세트 300\~500(04 기준). 전수 실행은 선택.
- JSONL 파일은 해시된 뒤 불변. `dataset_sha256`이 다른 리포트는 `laya-evals compare`가 거절한다(출처: docs/evals.md §Baseline and CI gate).

### 3.3 측정 규칙

- 워밍업: 지연 측정 전 최소 3회 호출을 버린다. upstream은 MPS에서 (batch, length) shape마다 첫 호출에 최대 약 13초의 Metal 커널 컴파일이 붙는다고 적었지만(출처: examples/README.md "Before you start") 이 머신 실측은 약 0.1 s다(2026-10-03 D3, `results/D/20261003-1306_coldload.md`). 그래도 측정에 쓰는 shape마다 최소 1회 선행 호출을 유지한다.
- 반복: 지연은 ≥10회, median과 p95(및 min)를 보고. 정확도는 CPU fp32 단일 결정적 패스. MPS 정확도는 §3.4 parity 게이트 통과 후에만 사용.
- 시간은 `time.perf_counter()`로 `predict()` 호출만 감싼다(in-process). HTTP는 요청 송신부터 응답 파싱까지. 둘을 한 표에서 비교하지 않는다.
- 측정 중 다른 무거운 프로세스 종료, AC 전원, 화면 잠김 방지. 스로틀링 의심 시 같은 설정을 10분 뒤 재측정해 median 차이 10% 이내인지 확인.

### 3.4 디바이스/정밀도 규칙

- CPU fp32가 정확도 reference. `torch.set_num_threads(10)`, `torch.set_num_interop_threads(1)`. inter-op 1은 upstream이 바쁜 호스트에서 12x를 본 설정이다(출처: BENCHMARKS.md §Laptop CPU).
- MPS는 rows ≥ 5일 때만 fp16 autocast가 걸린다(`MPS_AMP_MIN_ROWS_DEFAULT = 5`, laya/agent.py:278). 1문항 `predict`는 MPS에서도 fp32, 5문항 이상 또는 `predict_batch`는 fp16. `LAYA_MPS_AMP_MIN_ROWS=100000`으로 fp32 강제.
- MPS parity 게이트(A5, C9): 같은 항목에서 fp32 경로는 argmax 100% 일치, max|Δp| ≤ 0.01; fp16 경로는 argmax ≥ 99%, max|Δp| ≤ 0.05. upstream fast-path parity 기준(max|Δp| ≤ 0.05 vs fp32, argmax ≥ 47/48: 출처 README §GPU Fast Path)을 차용. 통과 전까지 MPS 수치는 지연 전용.

### 3.5 저장 규약

- `results/<track>/<YYYYMMDD-HHMM>_<model>_<dataset>.json` + 같은 이름 `.md`. 덮어쓰기 금지. 실패 런도 `_FAILED` 접미사로 남긴다.
- 검토를 마친 리포트는 `results/baselines/<dataset>_<model>_baseline.json`으로 복사하고, 이후 런은 `laya-evals compare REPORT --baseline ... --tolerance choice_accuracy=0.02`로 드리프트를 본다.
- LLM 프롬프트 원문은 `results/F/prompts/`, 보정 payload는 `poc/calibration/`.

### 3.6 통계

- 모든 정확도/ECE에 bootstrap 95% CI(1000 resample, percentile). n=100이면 p≈0.5에서 약 ±0.10, n=400이면 약 ±0.05.
- 같은 항목에 대한 A/B 비교(디바이스, 변형, 프리미티브)는 exact McNemar. upstream도 위치 민감도 비교에 같은 검정을 썼다(출처: research/README.md §Headline findings).
- 5포인트 차이를 유의하게 보려면 n ≥ 400을 목표로 하고, n=100 세트(MASSIVE 재현)는 순위 판단에 쓰지 않는다.
- Track A "재현" 기준은 ±0.03. 첫 100행 고정 + seed 13 구성은 결정적이므로 그 이상의 차이는 노이즈가 아니라 구성 또는 버전 차이다. 원인을 찾아 기록한다.

### 3.7 베이스라인 공정성

- 동일 레이블 집합, 동일 설명문(criteria 텍스트를 그대로 프롬프트에 렌더링), few-shot 금지, state에 레이블명 노출 금지.
- LLM은 같은 항목 N개, temperature 0, 레이블만 담은 JSON 출력. 무효 출력은 버리지 않고 오류율로 보고.
- supervised 문헌값은 "supervised ceiling"으로 표기하고 zero-shot과 같은 표에 둘 때 열 머리에 명시.

### 3.8 스크립트 스펙 (구현은 별도)

| 스크립트 | 목적 | 입력 | 출력 | 재사용 upstream |
|---|---|---|---|---|
| `scripts/env_report.py` | 환경 스냅샷(버전, 디바이스, 스레드, 체크포인트 SHA, 데이터셋 sha256) | 선택적 JSONL 경로들 | `results/env/env_*.json` | `laya.revisions.snapshot_revision` (스펙: 02 §2.10) |
| `scripts/build_ko_evalsets.py` | 한국어 평가셋 빌드·검증·MANIFEST | 서브커맨드 `all`, `massive`, `ynat`, ... (04 §6) | `data/evals/*.jsonl`, `MANIFEST.json` | `laya.evals.Dataset`, `questions_fingerprint`; `laya-evals validate` (스펙: 04 §6) |
| `scripts/bench_massive_ko.py` | Track A 재현 (ko/en MASSIVE 20옵션) | `--langs`, `--per-lang`, `--models`, `--device` | `results/A/*.json|.md` | `third_party/laya/research/scripts/bench_local.py`(upstream 클론, 공개 저장소에는 포함하지 않음. https://github.com/NandhaKishorM/laya 를 commit 4aa6761로 클론해 재현)의 `build_massive`, `score_cases`, `metrics`, `softmax_t`, `temp_for`, `load`. bench_local은 import 시점에 `LAYA_MODELS`를 읽으므로(bench_local.py:39) import 전에 `os.environ["LAYA_MODELS"] = os.environ["LAYA_MODELS_DIR"]`를 설정한다(02 §2.8) |
| `scripts/metrics_extra.py` (구현됨, 388줄) | macro-F1, Brier, bootstrap CI, coverage 곡선, McNemar, parity, majority/random. 서브커맨드 방식: `summary REPORT...`, `paired A B`, `parity A B`, `coverage REPORT`, `majority REPORT`, 공통 `--split-rule auto\|index\|hash --out --json`(`scripts/metrics_extra.py:342`) | laya-evals 리포트 JSON들 | `results/<track>/metrics/*.md,json` | `laya.common.ece_score`; 리포트 per-case 기록(`cases[].answer`에 확률 포함, laya/evals.py:728-744) |
| `scripts/probe_option_order.py` | 옵션 순열 flip | JSONL들, `--permutations`, `--seed` | `results/C/*_option_order.json` | `build_benchmark_nb.py:640-678` 방식 |
| `scripts/probe_wording_ladder.py` | wording 사다리 | PoC JSONL | `results/C/*_wording_ladder.json` | `research/benchmarks/zh_short_commands` 사다리 정의 |
| `scripts/bench_latency_local.py` | in-process 지연 행렬, 스레드 스윕, cold load, RSS | `--checkpoints`, `--questions`, `--devices`, `--states`, `--threads`, `--interop`, `--repeat` | `results/D/*_latency_*.json` | `verify/bench_devices.py`, `examples/_common.py timed`, `bench_latency.py` 질문 세트 |
| `scripts/bench_batch_local.py` | predict 루프 vs predict_batch, sort_by_length, parity | `--states`, `--n`, `--batch-size`, `--sort-by-length`, `--devices`, `--rounds` | `results/D/*_batch.json` | `research/scripts/bench_length_batching.py`, `benchmarks/bench_predict_batch.py` |
| `scripts/bench_http_local.py` | laya-serve 부하 (closed/open loop, batch) | `--url`, `--closed`, `--open`, `--duration`, `--batch-states` | `results/D/*_http_*.json` | 없음 (httpx + asyncio) |
| `scripts/calibrate_ko.py` (구현됨, 약 515줄) | temperature refit, payload 저장, 전후 ECE/NLL, coverage(보정 후 곡선은 로짓이 있는 이 스크립트만 계산 가능) | `--sets`, `--splits results/B/B_splits.json`, `--model`, `--device`, `--pooled`/`--per-task`, `--min-bucket-n`, `--out-payload`, `--out` | `poc/calibration/ko_v1.json`, `results/E/*.json` | `laya.calibrate.records_from_labeled`(단, `torch.no_grad()`로 감싸야 함: 아래 E2 결함 노트), `fit_temperature_map`, `fit_one_temperature`, `calibration_payload` |
| `scripts/llm_baseline.py` (선택) | LLM zero-shot 베이스라인 | JSONL들, `--model`, `--n`, `--cache` | `results/F/*.json`, `results/F/prompts/` | 없음 (anthropic SDK) |
| `scripts/bench_long_context_ko.py` | C8 장문·위치 민감도(한국어) | `--device`, `--pads` | `results/C/*_long_context.json` | `research/scripts/bench_long_context.py` 복사본에서 `REQUESTS`, `FILLER` 상수만 한국어로 교체 |
| `scripts/build_dashboard.py` | 결과 대시보드: 트랙별 표·차트, 가설 판정, Go/No-Go를 단일 HTML로 생성(§12 항목 11) | `--results results/` (최신 `results/env/env_*.json`, `results/{A,B,C,D,E,F,poc}/*.json`, `results/verdicts.json`, `results/go_no_go.json`), `--out results/dashboard/index.html`, `--open` | `results/dashboard/index.html` (자기완결 HTML, 데이터 inline JSON) | 없음. 차트는 cdnjs의 Chart.js 또는 inline SVG, 표는 순수 HTML(오프라인에서도 표는 보임). 출력은 결정적이고 생성 시각은 푸터 한 줄만 |

모든 스크립트는 JSON과 Markdown 표를 `results/<track>/`에 쓰고 런 카드 필드를 출력한다.

## 4. 지표 정의

| 지표 | 정의 | 계산 위치 | 프리미티브 |
|---|---|---|---|
| accuracy (`choice_accuracy`, `noul_accuracy`) | argmax 레이블 일치율; noul은 p ≥ 0.5 이진화 | laya-evals | choice, noul |
| macro-F1 | 클래스별 F1 단순 평균 | metrics_extra | choice |
| Brier | 옵션별 (p_o − y_o)² 합의 평균 (multi-class 합) | metrics_extra | choice, noul |
| ECE | 15-bin, `answer_confidence`(= max p) 기준 (출처: docs/evals.md §Metrics) | laya-evals, metrics_extra(CI) | 전부 |
| mean_confidence | `answer_confidence` 평균 | laya-evals | 전부 |
| coverage@accuracy, acc@50%cov | confidence 상위 x%만 응답했을 때 정확도; bench_local `metrics`의 `acc_at_50_coverage`와 같은 정의 | metrics_extra | choice, noul |
| abstention rate@T | `--min-confidence T`에서 `abstention == "abstained"` 비율 | laya-evals | 전부 |
| option-order flip rate | 원 순서 답과 무작위 순열 답의 argmax 불일치 비율(순열당 평균) + any-flip(k 순열 중 1회 이상) | probe_option_order | choice |
| wording-ladder Δ | 사다리 단계별 accuracy 차와 noul always-true 비율 | probe_wording_ladder | choice, noul |
| recall@k (shortlist) | shortlist가 gold를 보존한 비율, `evaluate_shortlist`의 `shortlist_recall_at_k` (출처: docs/evals.md §Attributing shortlist errors) | laya.evals_shortlist | choice |
| score_mae, score_within_t | 기대 레벨과 gold 레벨(0-base 인덱스)의 절대차, 허용오차 내 비율 | laya-evals | score |
| latency p50/p95 | in-process: `predict` 호출 벽시계; HTTP: 요청\~응답(직렬화 포함). 분리 보고 | bench_latency_local, bench_http_local | 전부 |
| throughput | states/s, decisions/s(= states × 질문 수) | bench_batch_local, bench_http_local | 전부 |
| cold load | 새 프로세스에서 import → load → 첫 답까지 초 | bench_latency_local | 전부 |
| peak RSS | psutil 최대 RSS; MPS는 `torch.mps.current_allocated_memory()` 병기 | bench_latency_local, bench_batch_local | 전부 |
| parity | 두 경로의 argmax 일치율과 max \|Δp\| (출처: benchmarks/parity_fast.py 방식) | metrics_extra | 전부 |

laya-evals가 내지 않는 지표(macro-F1, Brier, CI, coverage 곡선, McNemar)는 `scripts/metrics_extra.py`가 리포트 JSON의 per-case 기록에서 계산한다. 리포트의 `cases[]`는 케이스마다 `expected`, `answer`(확률 포함 전체 answer dict), `correct`를 보존하므로(출처: laya/evals.py:728-744, `EvalReport.to_json()` :376-379) 모델을 다시 호출할 필요가 없다.

## 5. Track A 재현

목적: 우리 환경이 upstream 수치를 내는지 확인하는 sanity 게이트. 통과 전엔 다른 트랙을 시작하지 않는다.

### A1 fixture [단계 → 검증]

02_environment_setup.md의 스모크 테스트가 이미 수행했다. 기대값(english, CPU): choice_acc 0.75, noul_acc 1.00, score_mae 1.3418, ece 0.1596 (출처: docs/evals.md §Evaluating an ONNX export 표). 검증: 그 리포트를 `results/A/`에 복사하고 네 수치가 일치하는지만 본다.

### A2 ko/en MASSIVE 20옵션, upstream 스크립트 경로 [단계 → 검증]

```bash
python scripts/bench_massive_ko.py --langs ko,en --per-lang 100 --models english,multilingual \
  --device cpu --out results/A/$(date +%Y%m%d-%H%M)_massive20_ko_en.json
```

- 구성은 upstream과 바이트 단위로 같아야 한다: config `ko`/`en`의 test split 첫 100행, 옵션 20개 = gold + `random.Random(13)`으로 19개 추출 후 shuffle, criteria 텍스트는 키의 `_`→공백, `.`→`: `, instructions "What is the user asking for in `utterance`?" (출처: research/scripts/bench_local.py:165-183). 스크립트는 그 함수를 import하고 재구현하지 않는다.
- 기대값 (upstream 공개 수치, 출처: BENCHMARKS.md:71 및 §Languages 표의 `en` 행):

| 언어 | laya acc | multilingual acc | laya ECE | multilingual ECE |
|---|---|---|---|---|
| ko | 0.110 | 0.470 | 0.680 | 0.311 |
| en | 0.820 | 0.710 | 0.138 | 0.233 |

- 검증: 정확도 ±0.03, ECE ±0.05. ECE가 어긋나면 temperature regime을 먼저 의심한다. 커밋된 51개 언어 sweep의 ECE 열은 #42 clamp 이전 값이고 표 머리의 macro ECE(laya 0.5709)는 clamp 후 "as served" 값이다(출처: BENCHMARKS.md 서두 clamp 설명). multilingual은 fitted temperature 없이 출하되므로(출처: README §Calibration) clamp 영향이 없고 0.311이 그대로 나와야 한다.
- 어긋날 때 점검 순서: (1) `id` 필드로 첫 100행 동일성(mteb 데이터셋 lastModified 2026-02-24, 행 순서 변경 가능), (2) 체크포인트 SHA, (3) laya 버전, (4) criteria 렌더링 문자열 diff.

### A3 같은 100개를 laya-evals 경로로 [단계 → 검증]

```bash
ts=$(date +%Y%m%d-%H%M)
laya-evals validate data/evals/ko_massive_intent_20opt.jsonl
laya-evals run data/evals/ko_massive_intent_20opt.jsonl --model multilingual --device cpu \
  --slice language --json results/A/${ts}_multilingual_ko_massive20.json --markdown results/A/${ts}_multilingual_ko_massive20.md
laya-evals run data/evals/ko_massive_intent_20opt.jsonl --model english --device cpu \
  --slice language --json results/A/${ts}_english_ko_massive20.json
```

- 검증: `choice_accuracy`가 A2의 같은 모델 ko 정확도와 동일. 1개 이상 다르면 (a) JSONL 구성이 bench_local과 다른지(옵션 순서, criteria 문자열), (b) 배치 shape 차이(bench_local `score_cases`는 길이순 packing, harness는 행별 호출)로 임계 근처 확률이 흔들렸는지 확인. 확률 차 < 0.01인 flip 1개까지는 기록 후 수용.
- 이 단계가 Track B의 전제다. harness 경로와 스크립트 경로가 같은 답을 내야 B의 수치를 upstream 표 옆에 둘 수 있다.

### A4 (선택) zh 앵커 [단계 → 검증]

```bash
laya-evals run third_party/laya/research/evals/zh_decision_bench.jsonl --model multilingual --device cpu \
  --slice tag --json results/A/$(date +%Y%m%d-%H%M)_multilingual_zh_decision_bench.json
```

기대: voice routing(n=179) 0.883, CS routing(n=25) 0.640, urgency 0.560, scam/promo 0.667, escalate 0.550 (출처: BENCHMARKS.md §Community evaluation zh §2, laya 0.3.20 CUDA). 검증: 0.3.23 + CPU fp32이므로 argmax는 거의 전부 같아야 하고 n=179 slice에서 ±0.02 이내면 수용. 비영어 두 번째 재현 앵커.

### A5 MPS parity [단계 → 검증]

```bash
ts=$(date +%Y%m%d-%H%M)
laya-evals run data/evals/ko_massive_intent_20opt.jsonl --model multilingual --device mps \
  --json results/A/${ts}_multilingual_ko_massive20_mps_fp32path.json
laya-evals run data/evals/ko_massive_intent_20opt.jsonl --model multilingual --device mps --batch-size 16 \
  --json results/A/${ts}_multilingual_ko_massive20_mps_fp16path.json
python scripts/metrics_extra.py parity results/A/${ts}_multilingual_ko_massive20.json results/A/${ts}_multilingual_ko_massive20_mps_fp32path.json
python scripts/metrics_extra.py parity results/A/${ts}_multilingual_ko_massive20.json results/A/${ts}_multilingual_ko_massive20_mps_fp16path.json
```

1문항 호출은 1 row라 MPS에서도 fp32로 돈다(§3.4). `--batch-size 16`은 20옵션 세트에서 행마다 질문이 달라 실제로는 묶이지 않을 수 있다. 묶이지 않으면 fp16 경로 검증은 C9에서 질문을 공유하는 YNAT로 대신한다. 검증 기준은 §3.4.

### 게이트

A2, A3 통과(그리고 A5 fp32 경로 100/100)면 Track D로. 실패 시 원인을 `results/A/INVESTIGATION.md`에 기록하고 해결 전에는 진행하지 않는다.

## 6. Track D 성능

### D1 in-process 지연 행렬 [단계 → 검증]

```bash
python scripts/bench_latency_local.py --checkpoints english,multilingual,typed-decisions \
  --questions 1,3,5,10,50 --devices cpu,mps --states short,long --repeat 10 \
  --out results/D/$(date +%Y%m%d-%H%M)_latency_matrix.json
```

- 상태: `short` 한국어 문의 약 60 토큰, `long` 약 400 토큰(04의 PoC 세트에서 1개씩 고정). 질문은 upstream bench_latency처럼 3옵션 choice와 noul을 교대로(출처: research/scripts/bench_latency.py `Q_CHOICE`, `Q_NOUL`, `qs(n)`).
- 보고: 설정별 median/p95, ms/question, 문항 수 기울기(10q/1q 비).
- 기대치 비교표:

| 설정 | english 1q | multilingual 1q | multilingual 10q | 출처 |
|---|---|---|---|---|
| Tesla T4 GPU | 39.5 ms | 32.8 ms | 72.3 ms | BENCHMARKS.md §Speed (upstream) |
| EPYC 9R14 4코어 CPU fp32 | 580 ms | 193 ms | 1,842 ms | BENCHMARKS.md §Server CPU (upstream) |
| Ryzen 6900HX 8스레드, in-process 1q (HTTP 경유 3q는 783 ms) | 329 ms p50 | 측정 없음 | 측정 없음 | BENCHMARKS.md §Laptop CPU (upstream) |
| M4 Pro CPU 10스레드 (추정 250\~500 / 80\~200) | **86.6 / 204.5** ms (short 123 tok / long 919 tok) | **37.7 / 81.8** ms (short 59 / long 433) | **121.4 / 596.5** ms | 본 트랙 측정 2026-10-03 (`results/D/20261003-1249_latency_matrix.md`) |
| M4 Pro MPS (추정 30\~80 / 20\~60) | **31.8 / 85.6** ms | **13.8 / 35.1** ms | **62.4 / 284.8** ms | 본 트랙 측정 2026-10-03 |

- 검증(H8): CPU는 문항 수에 거의 선형이어야 하고(EPYC 문항당 multilingual \~185 ms, english \~600 ms: 출처 BENCHMARKS.md §Server CPU), MPS는 sub-linear(T4 10q 7.2 ms/q, GB10 문항당 7.0 ms: 출처 BENCHMARKS.md §Speed, §NVIDIA GB10). 추정치는 가설이며 측정값으로 대체한다.

### D2 CPU 스레드 스윕 [단계 → 검증]

```bash
python scripts/bench_latency_local.py --checkpoints multilingual --questions 1,10 --devices cpu \
  --threads 4,8,10,14 --interop 1,default --repeat 10 --out results/D/$(date +%Y%m%d-%H%M)_threads.json
```

검증: P-코어 수(10) 근처가 최적이고 14(E-코어 포함)는 같거나 느려야 한다. upstream은 "물리 코어 수 + 약간"을 권하고 SMT 형제 코어 경합을 보고했다(출처: BENCHMARKS.md §Laptop CPU). env.sh의 `OMP_NUM_THREADS=10`이 적절한지 여기서 확정.

### D3 cold load [단계 → 검증]

새 프로세스에서 `import laya` → `laya.load(...)` → 첫 `predict`까지를 3회(1회차는 OS 파일 캐시 cold) 측정. 체크포인트 3종 × {cpu, mps}. upstream은 multilingual의 34 MB tokenizer.json 파싱이 가중치 적용보다 비싸다고 적었지만(출처: README §Production Preload & Memory), 이 머신 실측은 tokenizer 약 1.0 s, 가중치·모듈 빌드 약 2.0 s로 반대다(2026-10-03 D3). MPS는 첫 shape 컴파일이 더해지므로 "time to first answer"를 CPU와 분리 보고. 검증 참조값: EPYC cold load english 4.4 s, multilingual 2.5 s, typed-decisions 0.5 s(캐시 효과, 근사: 출처 BENCHMARKS.md §Server CPU). 우리 값이 2배 이상 느리면 디스크/캐시 상태를 먼저 본다.

### D4 상태 배칭 [단계 → 검증]

```bash
python scripts/bench_batch_local.py --checkpoint multilingual \
  --states data/evals/ko_nsmc_sentiment.jsonl,data/evals/ko_klue_ynat_7.jsonl --n 64,256 \
  --batch-size 8,16,32 --sort-by-length both --devices cpu,mps --rounds 3 --interleave \
  --out results/D/$(date +%Y%m%d-%H%M)_batch.json
```

- 비교: `predict` 루프 vs `predict_batch(batch_size=N, sort_by_length=False/True)`. upstream CLI 측정처럼 라운드를 교대 실행하고 paired median을 보고(출처: README §Command line의 1.42x 측정 방법).
- parity: 항목별 argmax flip 수(기대 0), max|Δp| (CPU ≤ 0.01; MPS fp16은 기록만).
- 검증(H9): MPS 배치 3\~4x(decide_batch 8건 3.6x on Apple M: 출처 README §Schema-driven decisions), CPU는 batch_size만으론 \~1x, sort_by_length로 1.3\~2.15x(출처: README §Command line 1.42x; research/README.md §Length batching 2.15x). 측정(2026-10-03 D4): MPS 배치는 정렬해도 loop 대비 1.21\~1.25배에 그쳐 기대 3\~4배에 크게 못 미쳤고, CPU는 정렬 없는 배치가 loop보다 느렸으며(0.62\~0.93배) sort_by_length가 unsorted 대비 1.67\~2.08배(n=256)였다.

### D5 Router 이종 배치 [단계 → 검증]

ko/en 교차 32건을 `Router(max_loaded=1)`과 `Router(max_loaded=2)`에서 `predict` 루프와 `predict_batch`로 실행, 총 시간과 reload 횟수(`on_load`/`on_evict` 훅 카운트)를 보고. 검증 참조값: reload CPU 7.4 s / T4 10.3 s median(출처: README §Production Preload & Memory). PoC가 영어 트래픽을 함께 받을 때의 설계 근거(05).

### D6 HTTP, laya-serve [단계 → 검증]

```bash
# env.sh는 LAYA_MODELS를 export하지 않는다(LAYA_MODELS_DIR 사용, 02 §2.8). 아래 LAYA_MODELS는 laya-serve의 preload 이름 목록이다.
LAYA_MODELS=multilingual LAYA_DEVICE=mps LAYA_PRELOAD=1 LAYA_HOST=127.0.0.1 LAYA_PORT=8000 laya-serve &
python scripts/bench_http_local.py --url http://127.0.0.1:8000 --questions 1,3 \
  --closed 1,4,8 --open 5,10,20 --duration 60 --batch-states 16,64 \
  --out results/D/$(date +%Y%m%d-%H%M)_http_mps.json
```

- 모드: closed-loop 동시성 1/4/8, open-loop 5/10/20 RPS 각 60 s, `/v1/systemone/batch` 16/64 states(상한 64: 출처 README §Self-Hosting).
- 보고: p50/p95, 달성 RPS, 오류율, 503 수와 `Retry-After` 준수(출처: README §What's new in 0.3.21).
- 같은 절차를 `LAYA_DEVICE=cpu LAYA_THREADS=10`으로 반복해 GPU 없는 배포 그림을 얻는다.
- 검증: 00_README.md §6의 "10 RPS에서 p95 ≤ 150 ms(MPS)".

### D7 ONNX CPU [단계 → 검증]

```bash
python third_party/laya/scripts/export_onnx.py --model models/laya-multilingual \
  --output models/onnx/laya-multilingual.onnx --quantize
ts=$(date +%Y%m%d-%H%M)
laya-evals run data/evals/ko_klue_ynat_7.jsonl --model models/laya-multilingual \
  --onnx models/onnx/laya-multilingual.onnx --batch-size 16 --json results/D/${ts}_onnx_fp32_ynat.json
laya-evals run data/evals/ko_klue_ynat_7.jsonl --model models/laya-multilingual \
  --onnx models/onnx/laya-multilingual.int8.onnx --batch-size 16 --json results/D/${ts}_onnx_int8_ynat.json
laya-evals run data/evals/ko_klue_ynat_7.jsonl --model multilingual --device cpu --batch-size 16 \
  --json results/D/${ts}_torch_cpu_ynat.json
```

- `--onnx`일 때 `--model`은 Router 단축명이 아니라 export 원본의 경로/Hub id다(출처: docs/evals.md §Evaluating an ONNX export). `--quantize` 기본은 per-tensor(per-channel은 eager와 agreement 32%로 붕괴: 출처 README §What's new in 0.3.23). int8 파일은 `--output` 옆에 `<stem>.int8.onnx`로 쓰인다(`int8_output_path`: `laya.onnx` → `laya.int8.onnx`, 출처: scripts/export_onnx.py).
- 검증(H10): fp32 ONNX는 torch와 지표 동일; int8은 fixture에서 torch 116.8 → onnx 66.3 → int8 46.3 ms, ece 0.1596 → 0.1658(출처: docs/evals.md). 수용: int8 ≤ torch × 0.6, |ΔECE| ≤ 0.01, choice_accuracy 차 ≤ 0.01.

### D8 메모리 [단계 → 검증]

`Router(preload=True)`로 1/2/3개 상주 시 RSS, 64-state 배치 중 peak RSS(psutil 10 ms 샘플링, upstream 방식: 출처 research/README.md §Length batching). 검증 자릿수: fp32 가중치 english 약 1.7 GB, multilingual 약 1.3 GB + tokenizer. upstream 전체 스크립트 peak 9.3 GiB(5회 로드)(출처: BENCHMARKS.md §Server CPU). 48 GB 머신이므로 메모리는 제약이 아니고 PoC 컨테이너 사이징 근거로만 쓴다.

### 측정값 (2026-10-03, Apple M4 Pro, 단독 실행)

출처: `results/D/D_summary_20261003.md`(런 카드 `results/D/D_20261003.md`). 조건: AC 전원, thermal 경고 없음, 외부 GPU 작업 없음, warm-up 3회(+MPS shape당 1회) 후 10회 median, CPU intra-op 10 / inter-op 1.

**D1 in-process 지연 행렬** (median ms; 3q는 p95 병기; `results/D/20261003-1249_latency_matrix.json`)

| 체크포인트 · state | CPU 1q / 3q (p95) / 10q | MPS 1q / 3q (p95) / 10q | CPU÷MPS 1q |
|---|---|---|---|
| multilingual · short 59 tok | 37.7 / 56.4 (57.8) / 121.4 | 13.8 / 22.5 (22.6) / 62.4 | 2.73x |
| multilingual · long 433 tok | 81.8 / 195.8 (247.8) / 596.5 | 35.1 / 92.2 (92.5) / 284.8 | 2.33x |
| english · short 123 tok | 86.6 / 184.4 (186.5) / 472.8 | 31.8 / 79.6 (80.0) / 232.3 | 2.73x |
| english · long 919 tok (512 절단) | 204.5 / 515.1 (529.5) / 1658.1 | 85.6 / 242.1 (242.8) / 747.4 | 2.39x |
| typed-decisions · short 123 | 89.3 / 192.0 (194.4) / 507.9 | 31.9 / 79.8 (80.2) / 231.8 | 2.80x |
| typed-decisions · long 919 | 399.6 / 1143.6 (1175.7) / 3457.3 | 163.1 / 484.6 (485.0) / 1475.4 | 2.45x |

- dtype: CPU 전 셀 fp32, MPS 1q·3q fp32, 5q 이상 fp16 autocast. D1b(`LAYA_MPS_AMP_MIN_ROWS=100000`으로 fp32 강제): fp16 autocast 이득은 최대 8%(english long 50q)이고 짧은 행 5\~10q에서는 오히려 6\~16% 느리다.
- D1c(간헐 호출, idle gap ≥ 100 ms, `results/D/20261003-1312_latency_paced.json`): MPS 2.2\~3.6배, CPU 1.1\~2.3배 느려진다(multilingual short 3q: MPS 22.2 → 49.5\~51.0 ms, CPU 53.1 → 60.8\~97.6 ms). 서버 open-loop에서도 같은 현상이 보였다.
- **G5 통과**(PoC 구성 multilingual 3q p95: MPS 22.6 / 92.5 ms, CPU 57.8 / 247.8 ms; 간헐 호출에서도 MPS ≤ 90.6, CPU ≤ 100.5 ms). english·typed-decisions long은 CPU 기준 미달(529.5 / 1175.7 ms).
- **H8 기각**: MPS 1q 이점 2.33\~2.80배(기준 3\~6배 미달), 10q/1q MPS 4.52\~9.05로 sub-linear하지 않음, 문항 수가 늘어도 CPU÷MPS 1.9\~2.8배로 일정.

**D2 CPU 스레드 스윕** (`results/D/20261003-1304_threads.json`): intra-op 10이 최적(short 10q 114.7, long 1q 81.0, long 10q 597.6 ms). 14(E-코어 포함)는 2\~22% 느림. inter-op 1과 default(14)의 차는 −3.1\~+1.0%로 측정 오차 수준. 예외: 행 1개짜리 short 1q는 4 스레드가 27.0 ms로 10 스레드 33.2 ms보다 빠름. env.sh `OMP_NUM_THREADS=10` 확정.

**D3 cold load** (디스크 캐시 warm, 새 프로세스, `results/D/20261003-1306_coldload.json`): 첫 답까지 english·typed-decisions 2.82\~2.97 s, multilingual 3.45\~3.67 s(load 3.0 s 중 tokenizer 약 1.0 s, 가중치·모듈 빌드 약 2.0 s). MPS 첫 호출 컴파일 추가분 약 0.1 s.

**D4 상태 배칭** (multilingual, router_v1 1문항, 혼합 길이 한국어 64·256 states, 3라운드 교대, `results/D/20261003-1314_batch.json`)

| device | n | loop | b8 / b8s | b16 / b16s | b32 / b32s | sort÷unsort (bs 8/16/32) |
|---|---|---|---|---|---|---|
| CPU | 256 | 15.73 s | 18.97 / **11.32** | 20.15 / 11.06 | 25.52 / 12.18 | 1.67 / 1.83 / 2.08 |
| CPU | 64 | 4.16 s | 4.30 / 2.79 | 5.16 / 3.53 | 6.58 / 4.47 | 1.56 / 1.49 / 1.46 |
| MPS | 256 | 6.64 s | 8.72 / 5.48 | 9.46 / 5.35 | 10.83 / 5.36 | 1.59 / 1.77 / 2.02 |
| MPS | 64 | 1.65 s | 1.97 / 1.32 | 2.14 / 1.48 | 2.79 / 1.92 | 1.49 / 1.44 / 1.45 |

- parity(각 디바이스의 loop 대비): CPU 모든 모드 argmax flip 0, max \|Δp\| 0.0001; MPS fp16 배치 flip 0, 0.0081\~0.0085. **G7 통과**(정의대로 측정한 첫 근거).
- **H9 지지**(n=256 CPU sort 1.67\~2.08배, loop 대비 b8s 1.39 / b16s 1.42배, flip 0). 정렬 없는 CPU 배치는 loop보다 느리다(0.62\~0.93배, 패딩 슬롯 1.6\~2.2배). MPS는 정렬해도 loop 대비 1.21\~1.25배.

**D5 Router 이종 배치** (ko/en 교차 32건, `results/D/20261003-1328_router_batch.json`): 체크포인트 전환 1회 비용 CPU 0.130 s / MPS 0.206 s(로컬 경로 + 프로세스 내 tokenizer 캐시 조건; upstream 7.4 / 10.3 s와 직접 비교는 어려움). `max_loaded=1`이어도 `predict_batch`면 pass당 로드 2회로 1.07\~1.69 s. `max_loaded=2`(기본)는 reload 0회.

**D6 HTTP, laya-serve** (`LAYA_MODELS=multilingual LAYA_PRELOAD=1 LAYA_THREADS=10`, 60 s, `results/D/20261003-1330_http_mps.json`, `-1343_http_cpu.json`)

| 서버 | 조건 | p50 / p95 ms | 503 |
|---|---|---|---|
| MPS | closed c=1, 1q | 20.3 / 22.6 | 0 |
| MPS | closed c=1, 3q | 45.6 / 48.6 | 0 |
| MPS | open 10 RPS, 1q | 47.3 / 57.3 | 0 |
| **MPS** | **open 10 RPS, 3q** | **63.5 / 79.4** (p99 85.1) | 0 |
| CPU | closed c=1, 3q | 99.5 / 103.5 | 0 |
| CPU | open 10 RPS, 3q | 99.9 / 135.8 | 0 |

- **G6 통과**(MPS 10 RPS 3q p95 79.4 ms ≤ 150; CPU도 135.8로 기준 안). 오류·503 0건이라 Retry-After 경로는 미실행(동시성 8·20 RPS가 `LAYA_MAX_CONCURRENT` 기본 16을 넘지 않음).
- 서버는 추론을 직렬 처리한다(`ThreadPoolExecutor(max_workers=1)`, laya/serve.py:701; asyncio.Lock gate :863-867). 처리량 상한은 MPS 1q 약 50 RPS, 3q 22.6 RPS, CPU 1q 19.7 RPS, 3q 10 RPS이고 동시성을 올리면 지연만 는다. `/v1/systemone/batch`는 16 / 64 states에 218 / 848 ms(약 75 states/s).

**D7 ONNX CPU** (ko_klue_ynat_7 500행 전체, batch 16; test 절반을 포함하므로 경로 간 비교용이며 Track B 판정에는 쓰지 않음; `results/D/20261003-1347_*_ynat.json`)

| 경로 | acc | ece | p50 ms (16행 호출) |
|---|---|---|---|
| torch CPU (intra 10) | 0.634 | 0.1723 | 302.2 |
| ONNX fp32 | 0.634 | 0.1723 | 455.0 |
| ONNX int8 (per-tensor) | 0.622 | 0.1877 | 525.9 |

- ORT를 intra 10 / inter 1로 고정해도 fp32 457, int8 499 ms로 변화 없음. 파일: `laya-multilingual.onnx` + `.onnx.data`(1.29 GB), `.int8.onnx`(925 MB). int8 argmax 일치 0.930(35 flip), max \|Δp\| 0.646.
- **H10 기각**(int8이 torch보다 1.74배 느림, ΔECE +0.0154, Δacc −0.012). 이 Apple silicon에서는 torch fp32가 ONNX보다 빠르고 정확하다.

**D8 메모리** (`results/D/20261003-1307_rss_preload.json`, `-1349_rss_peak_batch.json`): CPU 상주 1 / 2 / 3개 RSS 2.07 / 3.63 / 5.23 GiB(multilingual +1.88, english +1.57, typed +1.60). 64-state `predict_batch` 피크(로드 후 대비): bs16 +2.43, bs16+sort +1.86, 64개 한 forward +5.49 GiB. MPS는 RSS 1.1\~1.7 GiB + driver 할당 1.24\~5.25 GiB.

**판정 요약**: G5 통과 · G6 통과 · G7 통과 · H8 기각 · H9 지지 · H10 기각. 측정 합계 3,509 s(12:49\~13:51).

### 시간 예산

| 단계 | 호출 수(대략) | 예상 wall time | 비고 |
|---|---|---|---|
| D1 | 60 설정 × 13 | CPU 30\~40분, MPS 10분 | english 50q CPU 호출이 지배 |
| D2 | 8 설정 × 13 | 10분 | |
| D3 | 18 프로세스 | 5\~10분 | |
| D4 | 2 세트 × 2 n × 7 모드 × 3 라운드 | CPU 30분, MPS 10분 | |
| D5 | 4 설정 | 5분 | reload 10 s 단위 |
| D6 | 6 모드 × 60 s + 배치 | 15분 × 2 디바이스 | |
| D7 | export + 3 런 | 15분 | onnx extra 설치 포함 |
| D8 | 5 측정 | 5분 | |

## 7. Track B 한국어 품질

### B1 전 세트 × 전 체크포인트 + Router auto [단계 → 검증]

```bash
for set in ko_massive_intent_20opt ko_massive_scenario_18 ko_massive_domain_8 ko_klue_ynat_7 ko_klue_nli_3 \
           ko_nsmc_sentiment ko_kmhas_hate ko_3i4k_speechact_7; do   # ko_poc_triage_v1은 보류(05 §2). en_massive_domain_8은 아래 쌍 런으로
  for m in english multilingual typed-decisions; do
    ts=$(date +%Y%m%d-%H%M)
    laya-evals run data/evals/$set.jsonl --model $m --device cpu --batch-size 16 \
      --slice qid --slice tag --json results/B/${ts}_${m}_${set}.json --markdown results/B/${ts}_${m}_${set}.md
  done
  ts=$(date +%Y%m%d-%H%M)
  laya-evals run data/evals/$set.jsonl --device cpu --batch-size 16 --slice model --slice qid \
    --json results/B/${ts}_router_${set}.json --markdown results/B/${ts}_router_${set}.md
done
```

- `--batch-size 16`은 체크포인트와 질문 스키마가 같은 연속 행만 묶는다(출처: docs/evals.md §Batching and timing). MASSIVE-20은 행마다 옵션이 달라 묶이지 않는다. B의 latency 열은 참고용이고 지연은 Track D가 담당.
- `ko_poc_triage_v1`은 보류(P4 결정 후)라 이 루프에 없다. 두 질문이 든 `ko_nsmc_sentiment`는 `--slice qid`로 질문별 지표를 본다.
- 검증(H2 후반): 한글이 있는 행은 Router auto가 100% multilingual로 보낸다(`lang.py:43` hangul 범위). 한글이 없는 행은 default(english)로 가므로 "100%"는 데이터에 비한글 행이 없을 때만 성립한다. 2026-10-02 측정: 9개 ko 세트 중 7개가 100%, NSMC 3행(영어 문장 1, 한글 자판을 잊고 친 `wjehdlhs;lhlshlsifhow;` 1)과 K-MHaS type_8 1행(영어)만 english로 갔고 multilingual 고정 런 대비 flip은 2 case(`results/B/summary_20261002.md` §4).
- typed-decisions는 영어 fine-tune이라 한국어에서 english와 비슷하거나 더 나쁠 것으로 예상. 대조군으로만.

### B2 보조 지표 [단계 → 검증]

```bash
python scripts/metrics_extra.py results/B/*.json --bootstrap 1000 --seed 13 \
  --out results/B/summary_$(date +%Y%m%d).md
```

세트 × 체크포인트별 accuracy(CI), macro-F1, Brier, ECE(CI), mean_conf, majority, random, Δ(acc − majority), acc@50%cov. 검증: 각 세트의 `choice_accuracy`가 리포트 JSON의 overall 값과 일치(계산 경로 자기 검증).

### B3 instructions 언어 ablation [단계 → 검증]

YNAT-7과 domain_8에 대해 instructions만 한국어로 바꾼 변형 파일(04 §4의 `*_ko-instr.jsonl`, 빌더 `--instructions ko`; MASSIVE-20의 ko-instr 변형은 만들지 않았다)과 설명을 영어로 바꾼 `*_en-desc.jsonl`(scenario_18은 key 렌더링)을 multilingual로, dev 절반에서만 실행. criteria 설명은 두 변형 모두 한국어. `questions_sha256`이 달라지므로 별개 실험이며 `compare` 대상이 아니다(출처: docs/evals.md §Run identity). 검증: McNemar p와 정확도 차. 더 좋은 쪽을 PoC 스키마 언어로 확정.

### B4 state 형식 ablation [단계 → 검증]

YNAT-7에서 state를 (a) 문자열, (b) `{"title": text}`, (c) `{"utterance": text}`로 바꿔 multilingual 실행. instructions가 백틱으로 필드명을 가리킬 때 state 키와 어긋나면 모델이 없는 필드를 보게 되는 함정이 있다(laya/presets.py `state_field` 주석). 검증: McNemar. 04의 PoC 스키마 state 형식을 이 결과로 확정.

### B5 분석 표와 체크포인트 선택 규칙

| 세트 | 옵션 수 | majority | english | multilingual | typed-decisions | Router | 기대 범위(가설) |
|---|---|---|---|---|---|---|---|
| ko_massive_intent_20opt | 20 | 측정 | 0.110 (upstream) | 0.470 (upstream) | 측정 | 측정 | A2 재현값 |
| ko_massive_scenario_18 | 18 | 측정 | 측정 | 측정 | 측정 | 측정 | P0c 미리보기 0.52 (play/music 병합 시 0.66, `results/poc/P0c_20261002.md`; upstream 비영어 scenario 평균 0.439: BENCHMARKS.md §English vs the rest) |
| ko_massive_domain_8 (PoC 주 과제) | 8 | 측정 | 측정 | 측정 | 측정 | 측정 | scenario_18 0.52가 병합으로 0.66 이상으로 오를 것으로 추정(P0c play/music 병합 0.66, `results/poc/P0c_20261002.md`). G1 입력 |
| en_massive_domain_8 (같은 id의 en 쌍, multilingual만) | 8 | 측정 | 해당 없음 | 측정 | 해당 없음 | 해당 없음 | 한국어 페널티 측정(07 §5 E1: 한국어 설명에서 ko 52 vs en 62, 비유의). 쌍 McNemar. english 체크포인트는 이 파일의 한국어 설명을 옵션당 22토큰으로 자르므로(04 §7 stats) 페널티 측정은 두 파일 모두 multilingual로 하고 english 런은 참고치로만 둔다. scenario_18은 head가 252/256토큰이라 설명을 늘리는 wording ablation은 cap에 걸린다 |
| ko_klue_ynat_7 | 7 | 측정 | 측정 | 측정 | 측정 | 측정 | P0c n=100 미리보기 0.65 (acc@50%cov 0.86, `results/poc/P0c_20261002.md`) |
| ko_klue_nli_3 | 3 | 측정 | 측정 | 측정 | 측정 | 측정 | 0.45\~0.65 (XNLI 15개 언어에 한국어 없음) |
| ko_nsmc_sentiment (noul / A-B) | 2 | 측정 | 측정 | 측정 | 측정 | 측정 | 0.60\~0.80 |
| ko_kmhas_hate (noul) | 2 | 측정 | 측정 | 측정 | 측정 | 측정 | 0.55\~0.75 (upstream held-out moderation 0.530: BENCHMARKS.md §Themes) |
| ko_3i4k_speechact_7 | 7 | 측정 | 측정 | 측정 | 측정 | 측정 | 0.40\~0.60 |
| ko_poc_triage_v1 (보류, P4 결정 후) | 05 §4.2 스키마 | 측정 | 측정 | 측정 | 측정 | 측정 | P0b n=30 프로브 intent 0.40\~0.50, 이진 always-no 수준 |

기대 범위는 추정이며 측정값으로 대체한다. 체크포인트 선택 규칙: `ko_massive_domain_8` test 절반 정확도 최대 → 동률이면 Track E refit 후 ECE 최소 → 그래도 동률이면 D1 지연 최소.

**측정값(2026-10-02, `results/B/summary_20261002.md`, CPU fp32, 46런).** multilingual / english / typed-decisions / Router 순.

| 세트 | multilingual (all / dev / test) | english | typed-decisions | Router | 비고 |
|---|---|---|---|---|---|
| ko_massive_domain_8 | 0.526 [0.486, 0.568] / 0.560 / **0.492** [0.432, 0.552] | 0.262 | 0.288 | 0.526 | macro-F1 0.518(test 0.468), ECE 0.229(test 0.263), majority 0.126. smart_home 예측 140(gold 63), general 80(gold 62)이 오답 흡수 |
| en_massive_domain_8 (같은 id) | 0.510 / 0.476 / 0.544 | 0.446(설명 절단) | 해당 없음 | 해당 없음 | 한국어 페널티 Δ(en−ko) −0.016 [−0.054, +0.022], McNemar p=0.47(b=50, c=42): 한국어 설명 계기에서는 페널티 없음 |
| ko_klue_ynat_7 | 0.634 / 0.612 / **0.655** [0.600, 0.710] | 0.216 | 0.234 | 0.634 | society recall 0.21, economy가 오답 흡수 |
| ko_massive_scenario_18 (n=100) | 0.520 / 0.551 / 0.490 | 0.310 | 0.330 | 0.520 | P0c와 동일 |
| ko_massive_intent_20opt | 0.470 | 0.110 | 측정 | 0.470 | upstream 일치(A) |
| en_massive_intent_20opt | 0.710 | 0.820 | 측정 | 해당 없음 | upstream 일치(A) |
| ko_klue_nli_3 | 0.750 | 0.448 | 측정 | 0.750 | |
| ko_nsmc_sentiment | choice 0.774 / noul 0.638 | 0.528 / 0.516 | 측정 | 동일(996/1000 multilingual) | noul은 always-false 편향(false 예측 427/500) |
| ko_kmhas_hate | 0.582 | 0.500 | 측정 | 0.582 | false 예측 417/500 |
| ko_kmhas_type_8 | 0.394 | 0.146 | 측정 | 동일(499/500) | |
| ko_3i4k_speechact_7 | 0.178 | 0.174 | 측정 | 0.178 | majority 0.144, chance 수준 |

ablation(dev 절반, multilingual, base 대비 McNemar): domain_8 ko-instr 0.540(−0.020, p=0.23), en-desc 0.532(−0.028, p=0.34); ynat_7 ko-instr 0.608(p=1.0), en-desc 0.637(+0.024, p=0.42); scenario_18 en-desc(key 렌더링) 0.429(−0.122, p=0.11). 유의한 효과 없음 → router_v1의 영어 instructions + 한국어 설명 유지. 선택: **multilingual 고정 + `lang="ko"`**(test 절반에서 english·typed-decisions 대비 p ≤ 2.2e-08; Router는 한국어에서 답이 같고 english 로드 경로만 추가). G1 사전 판독: domain_8 test 0.492는 기준 0.80에 −0.308, CI 상한 0.552도 미달. dev 0.560 vs test 0.492 차이는 index parity 분할의 scenario 구성 차이(test에 alarm 1행, calendar 0/16). Router auto는 한국어 전용 트래픽이면 multilingual 고정과 같아야 하고, 영어 혼입이 있으면 D5 reload 비용과 함께 판단.

## 8. Track C 견고성

### C1 옵션 순서 flip [단계 → 검증]

```bash
python scripts/probe_option_order.py data/evals/ko_massive_domain_8.jsonl data/evals/ko_klue_ynat_7.jsonl data/evals/ko_massive_scenario_18.jsonl \
  --model multilingual --device cpu --permutations 5 --seed 13 --split dev --splits results/B/B_splits.json \
  --out results/C/C1_option_order_$(date +%Y%m%d).json      # dev 절반만, test 절반은 건드리지 않는다
```

방법은 upstream과 동일: 항목마다 criteria 키 순서를 `rng.shuffle`로 섞은 dict를 만들고 원 순서 답과 argmax가 다르면 flip(출처: research/scripts/build_benchmark_nb.py:640-678). 보고: 순열당 flip rate 평균, any-flip rate, 순열별 accuracy. 참조값: en 20옵션 0.150(laya)/0.230(multilingual), 6레이블 emotion 0.040/0.090, Jev 0.13(출처: BENCHMARKS.md §Option-order robustness); zh CS routing 28%, voice 10.6%(출처: BENCHMARKS.md §Community evaluation zh). 검증(H5): 7\~20옵션에서 0.10\~0.30. PoC 스키마 수용은 ≤ 0.10(00 §6).

**측정값(2026-10-02, `results/C/C1_option_order_20261002.md`, dev 절반, 순열 5, multilingual).** router_v1(domain_8, n=250): 순열당 flip 0.270 [0.230, 0.310], any-flip 0.512, 정확도 0.528\~0.560. ynat_7(n=245): 0.168 [0.135, 0.206], any-flip 0.318. scenario_18(n=49): 0.241, any-flip 0.469. 원 순서 답은 Track B 리포트와 argmax 100% 일치. **G4(≤ 0.10) 미달**, H5 지지. flip 337건 중 74%가 원 순서 오답에서 나왔고, answer_confidence ≥ 0.9인 항목(108/250)만 보면 flip 0.094다. 위치 효과는 있으나(chi2 p=0.0009; 슬롯 1은 덜, 2\~4는 더 뽑힘) smart_home 흡수는 순열 평균 58.6건, 맨 뒤로 옮겨도 60건이라 의미적 현상이다. 첫 옵션 과예측 의심은 기각(productivity는 과소예측).

**스키마 v2 프로브(`results/C/C_schema_v2_20261002.md`, domain_8 dev 250행).** v1 0.560 대비: v2a 설명 강화 0.536, v2b general 제거(7옵션, 220행) 0.545, v2c 예시 문장 추가 0.540(옵션 토큰 418 > 한도 240이라 모두 30토큰으로 절단; head 512 진단 런은 0.408), v2d 순서 변경 0.516, v2e 5클래스 0.536. **v1을 넘는 변형 없음**. general 행은 게이트로 걸러지지 않는다(v2b에서 general 30행 중 23행이 smart_home, confidence 중앙값 0.76). 계약을 바꾸는 대안으로 v1 확률을 5클래스로 합산하면 dev 0.682(v2e 0.536 대비 p=3.8e-4).

### C2 wording 사다리 [단계 → 검증]

```bash
python scripts/probe_wording_ladder.py data/evals/ko_poc_triage_v1.jsonl --model multilingual --device cpu \
  --out results/C/$(date +%Y%m%d-%H%M)_wording_ladder.json
```

zh 사다리를 PoC 스키마에 한국어로 복제: choice는 criteria-only → +시나리오 문장 → +JSON state, noul은 plain(`poc/schema/triage_v1.json`, criteria 없음) → +criteria(`poc/schema/triage_v1b.json`, `true`/`false` 한국어 설명, 05 §4.1) → +시나리오 → +JSON state. 단계별 accuracy, macro-F1, noul always-true 비율(p ≥ 0.5 비율), mean/SD conf. 참조값: zh choice 0.722 → 0.778 → 0.667, noul 0.667 → 0.458 → 0.472 → 0.417로 criteria가 붙자 모든 noul이 true로 붕괴(출처: research/benchmarks/zh_short_commands/README.md). 검증: 단계별 McNemar. 가장 좋은 단계를 PoC 스키마 wording으로 고정하고 04/05에 반영. 조기 신호: 한국어 instructions는 YNAT·scenario-18(n=100, `results/poc/P0c_20261002.md`)에서 Δ0이었고, triage 프로브(P0b, `results/poc/P0b_20261002.md`)에서는 is_urgent에만 작은 효과(+1)가 있었다.

### C3 noul vs 2-choice 중립 키 [단계 → 검증]

NSMC의 noul 변형과 A/B 2-choice 변형(04), 그리고 noul에 `labels: {"true": "A", "false": "B"}` 오버라이드를 건 변형(출처: README §Honest limits)을 english/multilingual로 실행. 검증(H6): 같은 항목이므로 McNemar. 결과에 따라 PoC의 이진 질문을 noul로 둘지 2-choice로 둘지 결정. P0b 조기 신호(n=30, `results/poc/P0b_20261002.md`): `labels` A/B는 효과 없음(93/120 = 기준선), A/B 2-choice는 A로 붕괴(68/120), criteria는 질문별로 엇갈림(churn_risk 28/30, refund_requested 과양성). H6("noul < 2-choice 중립 키")은 프로브와 반대 방향이며 NSMC n=500의 이 C3이 판정한다.

### C4 부정문 [단계 → 검증]

`data/evals/ko_negation_probe.jsonl`(쌍 구성)을 두 체크포인트로 실행. 긍정/부정 절반 정확도, 부정 절반에서 "취소" 류 레이블의 확률 분포, paired McNemar. 참조값 #377: english는 부정 요청 4/4를 cancel_account로, multilingual은 2/4(출처: README §Honest limits). 검증(H7). 실패 시 PoC에서 부정 패턴을 confidence가 아닌 규칙으로 걸러야 한다는 설계 입력이 된다.

### C5 boolean-word 레이블 [단계 → 검증]

PoC 이진 질문 하나를 키 `yes`/`no`, 의미 키(예: `refund`/`no_refund`), 불투명 키 `A`/`B`로 각각 렌더링해 정확도 비교. upstream 권고는 boolean-word 키 회피(출처: README §Honest limits). 검증: 세 변형 간 McNemar; 최선 키 방식을 04에 반영.

### C6 고카디널리티 [단계 → 검증]

`ko_massive_intent_full60.jsonl`(약 60개 intent 단일 질문)을 세 설정으로 실행한다.

```bash
# (a) 기본 예산
laya-evals run data/evals/ko_massive_intent_full60.jsonl --model multilingual --device cpu \
  --json results/C/$(date +%Y%m%d-%H%M)_full60_default.json
# (b) head_max_len 512 / max_len 1024, (c) predict_shortlist k=20: harness에 플래그가 없어 짧은 python으로
python - <<'EOF'
import json, laya
from laya.evals import Dataset, evaluate
from laya.evals_shortlist import evaluate_shortlist
from laya.shortlist import embed_fn_from_agent
agent = laya.load("models/laya-multilingual", device="cpu")
ds = Dataset.from_jsonl("data/evals/ko_massive_intent_full60.jsonl")
agent.cfg["head_max_len"], agent.cfg["max_len"] = 512, 1024
json.dump(evaluate(agent, ds).to_json(), open("results/C/full60_head512.json", "w"))   # 주의: 아래 결함 노트
agent.cfg["head_max_len"], agent.cfg["max_len"] = 256, 1024
rep = evaluate_shortlist(agent, ds, embed_fn_from_agent(agent), k=20,
                         checkpoint_id="laya-multilingual@55cf4c4", embedder_id="laya-multilingual-meanpool@55cf4c4",
                         dataset_path="data/evals/ko_massive_intent_full60.jsonl")
json.dump(rep.to_json(), open("results/C/full60_shortlist20.json", "w"))
EOF

**실행 전 확인된 결함, 수정 필요.** `evaluate()`는 runner의 `predict(..., model=...)`를 호출하는데(laya/evals.py:704) `Agent.predict`에는 `model` 인자가 없다(laya/agent.py:1704). 위 스니펫처럼 `Agent`를 그대로 넘기면 TypeError가 난다. `Router`를 넘기거나(이 경우 `cfg` 변경은 Router가 보유한 agent에 해야 함), `model` 키워드를 버리는 얇은 runner 래퍼를 쓴다(Track C의 head 512 진단 런에서 쓴 방식: `results/C/C_schema_v2_20261002.md`).
```

`EvalReport.to_json()`은 `{config, overall, slices, cases}` dict를 돌려준다(출처: laya/evals.py:376-379). 보고: 설정별 accuracy, (c)의 `shortlist_recall_at_k`와 `retrieval_miss`/`decision_miss` 분포(출처: docs/evals.md §Attributing shortlist errors). 검증: 기본 예산은 옵션당 `max(4, (256-16)//60) = 4` 토큰으로 바닥에 붙어 붕괴해야 하고(banking77 77레이블 0.425 양쪽 동일: 출처 BENCHMARKS.md §On the public datasets), 512 예산은 개선(English MASSIVE 58레이블 24/58 → 34/58 at 384: 출처 README §Command line), shortlist는 리포터 수치 54.3 → 60.8%(출처 README §Honest limits, upstream 미재측정) 방향이어야 한다.

### C7 score 첫 레벨 편향 [단계 → 검증]

ko_poc_triage_v1의 score 질문 `frustration`(05 §4.1)에서 gold가 최저 레벨인 항목 50개와 최고 레벨 50개를 뽑아 multilingual과 english의 첫 레벨 선택률과 gold 비율을 비교. 참조값 #131: multilingual은 어떤 언어에서든 첫 레벨을 거의 고르지 않음(출처: README §Honest limits). 검증: 첫 레벨 선택률이 gold 비율의 절반 미만이면 편향 확인. PoC 스키마에 score 질문이 없으면 생략.

### C8 장문, 지표성 [단계 → 검증]

upstream 스크립트를 복사해 `REQUESTS` 20개와 `FILLER`만 한국어로 바꾼 `scripts/bench_long_context_ko.py`(코드 변경은 그 두 상수만)를 `--device mps`로 실행(pads 0/1000/2000/4000/7000, 기본 한도와 `max_len=8192`). 위치 민감도는 4,000 토큰에서 5개 위치만. n=20이라 셀당 ±0.22 CI이므로 지표성으로만 보고(출처: research/README.md §Headline findings). 지연 참조: 4,000 토큰 입력 약 1.7 s on Apple GPU(출처: README §Installation). 검증: 기본 한도에서 pad ≥ 1000이면 정확도가 떨어지고 8192에서 회복하는 방향.

### C9 디바이스 parity [단계 → 검증]

A5에 더해 질문을 공유하는 세트(YNAT-7, NSMC)를 `--device mps --batch-size 16`으로 실행해 B의 CPU 리포트와 케이스 단위로 비교(`python scripts/metrics_extra.py parity <cpu_report> <mps_report>`). `LAYA_MPS_AMP_MIN_ROWS=100000`을 건 fp32 강제 런도 1개 추가. 검증 기준 §3.4. 통과하면 B의 나머지 세트를 MPS로 돌려 시간을 줄일 수 있다.

### C10 라우팅 견고성 [단계 → 검증]

`results/korean_support/part3_routing_battery.md`의 46건 배터리(순수 한국어, 라틴 다수 혼합문, 영어 래퍼 속 짧은 한국어, 로마자, 자모, 이모지, 한자 혼용, NFD)를 `scripts/probe_routing.py`로 재실행하고 NFD·NFC 쌍과 PoC 세트 문장을 추가한다. 모델 로드 없이 `Router().route()`와 `laya.lang.analyse()`만 쓴다. 보고: 입력 유형별 `model`·`reason`, `default="english"` vs `"multilingual"` 차이, `lang="ko"` 명시 시 결과. 기준값: 2026-10-02 배터리는 정상 28 / 무방 4 / default 의존 4 / 실패 10이었고 실패 유형 F1\~F6은 `07_korean_support_audit.md` §4에 있다. 검증: 실패 유형이 07 §4의 목록 밖에서 새로 나오면 기록하고, `lang="ko"` 명시 경로는 46건 전부 multilingual이어야 한다.

## 9. Track E 캘리브레이션

### E1 as-shipped [단계 → 검증]

B 리포트에서 세트 × 체크포인트 ECE와 15-bin reliability 표(metrics_extra; 그림은 선택). multilingual은 fitted temperature 없이 출하되고 english는 over-confident(출처: README §Calibration). upstream refit 효과: laya 0.466 → 0.081, multilingual 0.314 → 0.106(출처: BENCHMARKS.md §Calibration). routing 과제에서는 반대로 under-confident였다는 보고도 있으므로 방향을 가정하지 않는다(출처: BENCHMARKS.md §Calibration on a routing task). 검증(H4 전반): ko 세트 절반 이상에서 ECE > 0.25인지.

### E2 refit [단계 → 검증]

```bash
python scripts/calibrate_ko.py --model models/laya-multilingual --device cpu \
  --sets data/evals/ko_massive_domain_8.jsonl,data/evals/ko_klue_ynat_7.jsonl \
  --splits results/B/B_splits.json --pooled --per-task --min-bucket-n 100 \
  --out-payload poc/calibration/ko_v1.json --out results/E/$(date +%Y%m%d-%H%M)_calibration_multilingual.json
```

- 분할은 새로 만들지 않고 `results/B/B_splits.json`을 그대로 쓴다(§3.2). 새 hash50 분할을 만들면 G1에 쓴 test 행이 fit에 섞인다. fit 절반(dev)에서 `records_from_labeled(agent, pairs)`로 (qtype, logits, target, k) 기록을 만들고 `fit_temperature_map(records, compute_ece=True, seed=13)`(laya/calibrate.py:211, :261).
- **upstream 결함(이슈 후보).** `records_from_labeled`에는 `@torch.no_grad()`가 없어 실제 `Agent`로 부르면 `RuntimeError: Can't call numpy() on Tensor that requires grad`가 난다(laya/calibrate.py:286 → agent.py:1177; `predict_batch`에는 데코레이터가 있다, agent.py:1248; upstream 테스트는 stub forward라 이 경로를 검증하지 않는다, tests/test_calibrate.py:425-466). `scripts/calibrate_ko.py:93`은 호출을 `torch.no_grad()`로 감싼다. predict_batch와 같은 실행 조건이므로 수치를 바꾸는 우회가 아니다(T=1에서 B 리포트와 argmax 500/500 일치로 확인).
- 버킷은 `temp_bucket(qtype, k)`: choice:3-5, choice:6-10, choice:11+, noul:2, score:3-5 등. 버킷별 온도는 `MIN_BUCKET_N = 2000` 이상이어야 기록되고(calibrate.py:205) 그 아래는 타입 스칼라(`MIN_TYPE_N = 10`)만 남는다(laya/calibrate.py 상단 상수와 모듈 docstring). 세트당 250\~500개면 버킷 온도는 안 나오므로 (i) 공식 map(타입 스칼라)과 (ii) `fit_one_temperature`(laya/calibrate.py:71)를 버킷별로 직접 호출한 저floor(min_n 100) 버전을 둘 다 보고하고, payload로 쓸 쪽을 held-out 성능으로 정한다. 레코드가 한 버킷(choice:6-10)에만 있으면 두 값은 같다. 세트를 pooling하는 것 자체가 설계 결정이므로 기록한다.
- pooled(4세트 합산) vs per-task(세트별) fit을 각 held-out 절반에 교차 적용해 전이성을 본다. YNAT로 맞춘 T가 PoC 세트에서도 ECE를 줄이는지가 PoC 운영의 핵심.
- 보고: 버킷별 raw T, clamp 여부(`[0.5, 5.0]`), held-out ECE/NLL before → after. zh 사례처럼 noul:2 raw T가 5를 넘으면(10.23 → 5.00, ECE 0.180 → 0.098: 출처 BENCHMARKS.md §Community evaluation zh §3) clamp가 보정 범위를 제한한다는 사실을 기록.
- 검증(H4 후반): held-out ECE ≤ 0.10.

**측정값(2026-10-02, `results/E/E_summary_20261002.md`, dev fit → test 평가, multilingual).** T(choice:6-10, clamp 없음): domain_8 2.0245, ynat_7 1.8149, pooled 1.9161. test ECE before → after: domain_8 0.263 → 0.098(pooled) / 0.123(per-task), ynat_7 0.148 → 0.063(pooled). NLL은 모두 개선(domain_8 1.727 → 1.37\~1.39). 채택 fit은 pooled(사전 규칙 "pooled가 domain_8 test ECE를 0.02 넘게 낮출 때만", 실제 0.025). G3는 점추정 통과이나 경계값(T를 1.8\~2.2로 움직이면 0.077\~0.119). 남은 과신은 dev → test 정확도 차이(0.560 → 0.492)에서 온다.

### E3 coverage 곡선과 min_confidence 스윕 [단계 → 검증]

held-out 절반의 (보정 전/후) 확률로 T ∈ {0.50, 0.55, ..., 0.95}에서 coverage(answer_confidence ≥ T 비율)와 covered accuracy를 metrics_extra가 계산. 교차 확인으로 `laya-evals run ... --min-confidence 0.8`을 돌려 `abstention` 필드의 abstained 비율이 우리 곡선의 1 − coverage(0.8)와 일치하는지 본다(출처: docs/evals.md §The abstention gate). torch 경로의 harness는 보정 payload를 받지 않으므로(laya/evals_cli.py:325는 `Router(device, preload=False, **pins)`만 생성) 보정 후 곡선은 로짓을 가진 `scripts/calibrate_ko.py`가 계산한다(`metrics_extra.py coverage`는 리포트의 4자리 반올림 확률만 있어 보정 전 곡선만 낸다). ONNX 경로의 `--calibration` 재검증과 `--min-confidence` 교차 확인은 2026-10-02 실행 범위 밖이다. 검증: 두 경로의 coverage가 ±0.01.

**측정값(2026-10-02, domain_8 test, dev에서 고른 T).** 오류 예산 5%: as-shipped T 0.9941 → test coverage 0.232 / 오류 0.069(초과), refit pooled T 0.8799 → 0.224 / 0.036. 10%: 0.300 / 0.093 → 0.308 / 0.091. 15%: 0.392 / 0.173 → 0.400 / 0.160. 보정은 게이트 눈금(0.994 → 0.880)과 ECE를 바꾸지만 예산별 최대 coverage(5%: 0.216 → 0.228)와 AUROC(0.840 → 0.841)는 거의 바꾸지 못한다. 스칼라 T가 행 간 순위를 안 바꾼다는 전제는 k=2에서만 정확하고 k=8에서는 행 쌍의 2.3%가 바뀌지만 frontier 영향은 ±0.03 이내다. 도메인별 T는 dev coverage 0.180 → 0.316이지만 test에서 5%·10% 예산을 모두 넘겨 **기각**(도메인당 dev 12\~66행 과적합). general은 단일 T에서 0/40이 route되어 사실상 항상 FALLBACK이다. 정확도 a에서 오류 e 이하 coverage의 상한은 a/(1−e) = 0.518이므로 G2(0.70)는 G1 개선 없이는 정의상 닿지 않는다.

### E4 payload 영속화 [단계 → 검증]

`calibration_payload(...)`로 `poc/calibration/ko_v1.json`을 쓰고, PoC는 `laya.load("models/laya-multilingual", calibration="poc/calibration/ko_v1.json")`(laya/agent.py:1875 `calibration` 인자) 또는 `apply_calibration_payload(agent, payload)`(laya/calibrate.py:393)로 적용. 검증: 적용한 agent로 held-out 절반을 다시 돌려 ECE가 E2의 after 값과 ±0.005 이내. payload의 config identity 경고(laya/calibrate.py `_warn_if_identity_mismatch`, :330-337)는 경로 문자열과 config만 비교하고 가중치 SHA는 보지 않는다. realpath로 로드하면 같은 체크포인트라도 UserWarning이 나므로 서비스는 `models/laya-multilingual` 문자열로 로드하고 SHA는 ADR에 따로 고정한다. 경고는 SHA 변경의 필요조건도 충분조건도 아니다.

**측정값(2026-10-02).** `poc/calibration/ko_v1.json` = pooled fit, temperature [1.9161, 1, 1](type 스칼라 형태), sha256 a217cb5d…. `laya.load(calibration=)`로 재채점한 domain_8 test ECE 0.0980(E2 값과 |Δ| 0), fresh agent에 `apply_calibration_payload` 적용 시 답 250/250 동일. 결정 대기: type 스칼라 형태는 검증하지 않은 다른 choice 질문(k=2, 3-5, 11+)에도 T=1.92를 걸므로 `{"choice:6-10": 1.9161}`로 범위를 한정한 형태와 ADR에서 택일한다(router_v1에서는 두 형태 출력이 같다).

### E5 수용

00_README.md §6: refit 후 held-out ECE ≤ 0.10, `ko_massive_domain_8` test에서 오류 ≤ 5%일 때 coverage ≥ 0.70. 미달이면 05의 gating 정책(abstain → LLM fallback)과 P4 파인튜닝 검토로 넘긴다. 임계값은 05가 정하는 정책이고 여기서는 곡선만 공급한다.

**판정(2026-10-02).** G3 통과(경계, pooled 0.098; per-task면 0.123 미달). G2 **미달**(0.224 vs 0.70; 상한 0.518). 대안 예산 10%면 0.308, 15%면 0.400.

### E6 noul 결정 임계값 [단계 → 검증]

multilingual의 noul은 언어와 무관하게 p(true)가 0.5 아래로 눌려 있으면서도 순위(AUROC 0.76\~0.92)로는 state를 읽는다(`07_korean_support_audit.md` §5 E4). temperature는 2-class softmax의 0.5 경계를 옮기지 못하므로 보정이 아니라 결정 임계값의 문제다. 각 noul 질문에 대해 dev half의 p(true)와 정답으로 ROC를 그리고 Youden J 최대점(또는 오류 예산 5%를 만족하는 최대 재현율 점)을 `T_noul[qid]`로 고른 뒤, test half에서 0.5 기준과 `T_noul` 기준의 accuracy·양성률·precision/recall을 전후 비교한다. 적용 위치는 laya가 아니라 05의 정책 레이어다(`decide()`의 `T_NOUL`). 검증: test half에서 `T_noul` 기준 accuracy가 always-no 기저를 넘고 양성률이 기대 ±5pt 안에 들어오면 수용. 결과는 `results/E/*_noul_threshold.json`과 ADR에 기록한다.

**측정값(2026-10-02, NSMC noul, `results/E/20261002-1733_calibration_multilingual_noul_threshold.json`).** AUROC dev 0.860 / test 0.822. dev Youden 임계값 p(true) ≥ 0.0073(dev 중앙값 0.0099의 극단 꼬리). test 정확도 0.725(0.5 기준 0.641, always-no 0.522, 의미 key 2-choice 0.773), 예측 양성률 0.506(gold 0.478)으로 수용 기준 충족. 다만 2-choice보다 낮고 wording·체크포인트가 바뀌면 다시 골라야 한다.

## 10. Track F 베이스라인

### F1 majority / random [단계 → 검증]

metrics_extra가 expected 레이블에서 계산: majority = 최빈 레이블 비율, random = 1/k(noul 0.5). 다질문 세트는 질문별 majority를 따로 둔다(upstream typed-decisions의 per-question majority 0.461 방식: 출처 BENCHMARKS.md §typed-decisions). 검증: 세트별 레이블 분포 표와 함께 보고.

### F2 LLM zero-shot, 선택 [단계 → 검증] (미실행: API 키 미제공, 2026-10-06 기준)

```bash
python scripts/llm_baseline.py data/evals/ko_poc_triage_v1.jsonl data/evals/ko_klue_ynat_7.jsonl \
  --model claude-haiku-4-5-20251001 --n 300 --seed 13 --concurrency 4 \
  --cache data/raw/llm_cache --prompts-out results/F/prompts \
  --out results/F/$(date +%Y%m%d-%H%M)_llm_haiku.json
```

- `.env`의 `ANTHROPIC_API_KEY` 필요(커밋 금지). 프롬프트는 laya 질문의 instructions와 criteria 텍스트를 그대로 렌더링하고 레이블만 담은 JSON을 요구. temperature 0, 재시도 3회, 응답은 `data/raw/llm_cache/*.jsonl`(공개 저장소에는 포함하지 않음)에 캐시해 재실행 비용 0.
- 기록: 입력/출력 토큰, 벽시계 p50/p95, 무효 출력률. 비용은 토큰 수 × 공식 pricing 페이지의 단가(실행 시점에 조회해 단가와 날짜를 런 카드에 기록). 단가를 코드에 박지 않는다.
- 비대칭을 표에 명시: LLM은 호출당 1\~3 s와 과금, Laya는 한계비용 ≈ 0. LLM은 확률을 주지 않으므로 ECE/coverage 비교는 없고 accuracy와 지연/비용만 비교.
- 검증: 같은 300개 항목을 Laya도 다시 돌려 짝지은 McNemar.

### F3 supervised 참조값

리포트 작성 시점에 문헌에서 찾아 출처, 모델, split, 지표를 함께 적는다: KLUE YNAT macro-F1과 KLUE NLI 정확도(KLUE 리더보드/논문), NSMC 정확도(fine-tuned BERT 계열 0.89\~0.90 통념, 검증 필요), 3i4K와 K-MHaS는 원 논문 수치. 열 머리에 "supervised ceiling"을 적고 zero-shot과 직접 비교하지 않는다.

### F4 Jev 공개 수치

| 출처 | 수치 |
|---|---|
| AbdelStark/jev-benchmarks | AG News 0.910, Banking77 0.870(72레이블), DAIR Emotion 0.480, p50 236\~246 ms |
| nibzard/decision-model-benchmark | ECE 0.246, banking77 0.763, 옵션 순서 flip 13%, p50 264\~276 ms |

(출처: research/README.md §On comparisons with Jev, BENCHMARKS.md §Headline). 공개된 한국어 Jev 수치는 없으며, 우리가 측정한 한국어 값은 F5의 n=24 수동 표본뿐이다. 표본과 프롬프트가 다른 제3자 측정이며 통제 비교가 아니다.

### F5 Jev 수동 비교 (수행됨 2026-10-06)

공식 API 키가 없어 공개 제3자 플레이그라운드 https://jevplayground.com 로 소표본 수동 비교를 했다(`results/F/jev_playground_manual_20261006.md`, run card `results/F/F_jev_20261006.md`).

- 프로토콜: `ko_massive_domain_8` test 절반에서 train 겹침 16행 제외 후 도메인별 3행씩 `random.Random(13)`으로 24행(`results/F/jev_sample_24.jsonl`). 질문 "Which domain should handle this request?", 선택지 8개를 `key: 한국어 설명`(router_v1과 같은 문자열·순서)으로 입력. 요청 25회(502 1회 포함), 간격 ≥ 21 s, 영어 key 전용 pass 2 생략. Laya 값은 Track B·P4 리포트에서 같은 행 조회.
- 결과: Jev 20/24 (0.833 [0.641, 0.933]), Laya zero-shot 10/24 (0.417), ft-v1 22/24 (0.917). Jev vs zero-shot b=10 c=0 p=0.002, Jev vs ft-v1 b=0 c=2 p=0.5. 표시 지연 중앙값 249.5 ms(브라우저 POST 497.5 ms) vs 로컬 P2 왕복 20.1 ms. Jev 오답 4건은 top 확률 41\~86%로 확신이 낮았고, 2건은 media 설명에 없는 "게임" 발화였다.
- 주의: n=24 단일 패스, 플레이그라운드(모델 버전 미표기, 라벨 1칸 형식), 무료 사이트 사용량 제한 안에서만 실행. ft-v1 대비 우열은 이 표본으로 판정 불가.

## 11. 실행 순서와 소요 추정

가정: multilingual CPU 20옵션 1문항 ≈ 0.2\~0.4 s(EPYC 4코어 3옵션 193 ms에서 보정), english ≈ 3배, MPS 1문항 ≈ 30\~60 ms. 전부 측정으로 대체.

| 순서 | 트랙 | 선행 조건 | 예상 wall time | 산출물 |
|---|---|---|---|---|
| 1 | A 재현 | 02 완료, 04의 ko_massive_intent_20opt | 30분(디버깅 포함) | results/A/*, 게이트 판정 |
| 2 | D 성능 | A 통과 | 2\~3 h | results/D/*, 디바이스 선택 입력 |
| 3 | B 품질 | 04 전 세트, D1로 시간 재추정 | CPU 2.5\~3 h (8세트 × 3+1 런 × \~400) | results/B/*, summary.md |
| 4 | C 견고성 | B, 04의 probe 세트 | 2\~3 h (순열 ×5가 지배) | results/C/* |
| 5 | E 캘리브레이션 | B, C9 | 30분 | poc/calibration/ko_v1.json, results/E/* |
| 6 | F 베이스라인 | B 항목 고정, API 키(선택) | 30분 | results/F/* |
| 7 | 리포트 | 전부 | 반일 | results/REPORT.md |
| 8 | 대시보드 | 리포트 JSON 전부, `verdicts.json`·`go_no_go.json` 기입 | 15분 | results/dashboard/index.html |

합계 약 1.5\~2 작업일. C9 parity가 통과하면 B/C를 MPS로 돌려 절반 이하로 줄일 수 있지만, PoC 세트와 MASSIVE-20은 CPU 기준값을 반드시 남긴다. 05 P4 파인튜닝은 이 표 밖의 추가 작업이다: 프로브 721 s(1,000행), 본 학습 추정 GPU 경합 시 3.1\~3.2 h / 유휴 시 1\~1.5 h, 평가 약 10분(`results/P4/P4_probe_20261002.md`). 실측(2026-10-03, run `full_20261003-1156`, GPU 유휴): 학습 2,150 s(35.8분, 15.6 items/s, 11,094행 × 3 epoch), 평가·flip 프로브 포함 전체 44분(`results/P4/full_20261003-1156_timing.json`, `results/P4/full_run_status.log`). 실측 소요(2026-10-02): B 46런 22분, C 4.9분, E 3.4분(모델 시간). **Track D는 단독 실행**이 조건이다: B/C/E 실행 중 다른 무거운 프로세스(다른 프로젝트의 실험)가 머신을 같이 썼으므로 B 리포트의 latency 열은 해석하지 않는다.

## 12. 리포트 구성

`results/REPORT.md`는 06_templates.md §2 템플릿을 채운다. 필수 구성:
1. 환경과 pin(env_*.json 요약, 체크포인트 SHA, 버전).
2. Track A 재현 표(upstream vs 측정, 차이, 판정).
3. Track D 지연/처리량/메모리 표와 디바이스 권고.
4. Track B 세트 × 체크포인트 표(§7 B5 레이아웃)와 체크포인트 선택.
5. Track C 견고성 표(flip, 사다리, noul/choice, 부정, 카디널리티, parity).
6. Track E 보정 전후 ECE, coverage 곡선, 채택 payload.
7. Track F 베이스라인 표(공정성 주석 포함).
8. 가설 판정표: H1\~H10 각 행에 지지/기각/미결, 근거 결과 파일 경로, CI. 원본은 `results/verdicts.json`(수동 유지: H1\~H10 각 `{"verdict": "지지|기각|미결", "run_ids": [...], "note": "..."}`)이고 REPORT.md §3은 그 파일을 옮겨 적는다.
9. 00_README.md §6 Go/No-Go 채움(항목별 측정값과 통과 여부). 원본은 `results/go_no_go.json`(G0\~G7 각 `{"value": ..., "pass": true|false|null, "run_ids": [...]}`; 리포트 JSON에서 계산 가능한 항목은 `build_dashboard.py`가 채우고 나머지는 수동)이고 REPORT.md §4는 그 파일을 옮겨 적는다.
10. 05_poc_plan.md로 넘기는 설계 입력(체크포인트, 디바이스, 스키마 wording, gating 정책, 부정문 처리, 파인튜닝 필요성).
11. `results/dashboard/index.html` 생성: `python scripts/build_dashboard.py --results results/ --out results/dashboard/index.html --open`. REPORT.md와 같은 JSON에서 생성되므로 두 산출물의 수치가 다르면 JSON이 기준이다. 포함 섹션: (1) 요약(환경 버전·SHA·디바이스, 판정 한 줄, 데이터 출처 run_id 수) (2) Track A 재현: upstream vs 측정 표(ko/en × english/multilingual, acc·ECE, ±0.03 판정 색) (3) Track D 성능: 체크포인트×디바이스×질문 수 median/p95 막대, 스레드 스윕 라인, 배치 speedup 막대, cold load·RSS 표 (4) Track B 품질: 세트×체크포인트 accuracy 표(majority, CI 병기)와 ECE 표, Router `model` slice (5) Track C 견고성: flip rate 막대(세트별, upstream 참고선 0.150/0.230), wording 사다리 라인(accuracy, always-true 비율), 부정문 쌍 정확도, 고카디널리티 3설정 막대, parity 표 (6) Track E 캘리브레이션: reliability diagram(15 bins, 전/후), coverage@accuracy 곡선(전/후, 오류율 5% 선), 버킷별 T 표 (7) Track F 베이스라인: 세트별 laya vs majority vs LLM(있으면) 막대, 지연·비용 표 (8) 가설 H1\~H10 판정표(`verdicts.json`) (9) Go/No-Go 매트릭스(`go_no_go.json`, 00 §6 기준값 병기) (10) run_id 목록과 결과 파일 상대 링크. 공유가 필요하면 생성된 HTML 한 파일을 artifact 등으로 게시할 수 있다.

## 13. 리스크와 완화

| 리스크 | 영향 | 완화 |
|---|---|---|
| MPS 수치 드리프트(fp16, shape별 커널) | 정확도 비교 오염 | §3.4 parity 게이트, CPU fp32 기준값 필수 보존 |
| 데이터셋 접근/라이선스(스크립트형 데이터셋 비호환, 401) | 세트 결손 | 04가 raw 다운로드 경로를 둠; 결손 세트는 리포트에 "미실행" 표기 |
| 레이블 품질(PoC 수작업 레이블) | H3/D1 판정 왜곡 | 레이블 정책 선확정, 이중 라벨링 표본 50개로 일치율 보고 |
| CPU 시간 폭증(english 50q 호출 수십 초) | 일정 초과 | D1을 먼저 돌려 B/C 규모 재조정, 세트 300으로 축소 옵션 |
| 열 스로틀링(노트북급 SoC) | 지연 수치 변동 | AC 전원, 10분 간격 재측정, median 10% 이내 확인 |
| HF online/offline 전환, 캐시 재다운로드 | 다른 revision 로드 | `LAYA_REVISION=reviewed`, 리포트 `revisions` 확인, 고정 실행은 `HF_HUB_OFFLINE=1` |
| upstream 버전 드리프트(0.3.x 잦은 릴리스) | 재현 불가 | laya 0.3.23, torch 2.14.1, transformers 5.18.0, 체크포인트 SHA 전부 pin |
| n=100 과잉 해석 | 잘못된 체크포인트/정책 선택 | CI 병기, 순위 판단은 n ≥ 400 세트에서만 |
| env 변수 이름 충돌(`LAYA_MODELS`) | laya-serve가 디렉터리 경로를 체크포인트 이름으로 해석해 실패 | 해결됨: env.sh는 `LAYA_MODELS_DIR`만 export, research 스크립트는 `LAYA_MODELS="$LAYA_MODELS_DIR"` 인라인(02 §2.8) |
| 혼합문 라우팅 실패 | 라틴 다수 혼합문·영어 래퍼 속 짧은 한국어가 english로 가 한국어 세트 수치가 오염됨 | 한국어 세트 실행은 `--model multilingual` 고정 또는 `lang="ko"`, Router auto 런은 `model` slice로 라우팅 결과 확인(C10, 07 §4) |
| NFD 입력 | 토큰 3.09배 증가, 자모·byte 조각화로 정확도·예산 오염(07 §3) | 평가셋 빌더는 NFC로 저장(04 §5 공통 규칙은 정규화 안 함이므로 소스가 NFD면 MANIFEST에 기록), PoC는 추론 전 NFC |
| 동시 실행 중인 다른 부하(2026-10-02: 다른 프로젝트의 실험) | 레이턴시 수치 오염 | 정확도 트랙(A/B/C/E)은 결정적이라 무관. Track D는 머신이 조용할 때 단독으로 돌리고 run card에 `pmset`·부하 상태를 기록 |

## 열린 질문 / 가정

1. (확인 완료) `laya-evals run --json` 리포트는 `cases[].answer`에 확률을 포함한 전체 answer dict를 보존한다(laya/evals.py:728-744). metrics_extra는 모델을 다시 호출하지 않는다.
2. BENCHMARKS.md:71의 ko ECE 0.680/0.311이 clamp 후 값인지는 표 머리의 macro ECE(0.5709)로부터 추정했다. A2에서 ±0.05 밖이면 regime 차이로 먼저 해석.
3. mteb/amazon_massive_intent의 행 순서가 upstream sweep 시점과 같다고 가정. A2에서 `id`로 확인.
4. (확인 완료) B3의 한국어 instructions 변형은 04 §4의 `*_ko-instr.jsonl`(빌더 `--instructions ko`)이다.
5. C7은 PoC 스키마에 score 질문이 있을 때만 의미가 있다. 05 스키마 확정 후 결정.
6. (확인 완료) ONNX int8 출력 파일명은 `<stem>.int8.onnx`(scripts/export_onnx.py `int8_output_path`), `EvalReport` 직렬화는 `to_json()`(laya/evals.py:376)이다.
7. LLM 베이스라인은 API 키와 비용 승인이 있을 때만 실행. 모델은 claude-haiku-4-5-20251001로 가정했고 변경 가능.
8. (해결됨) `LAYA_MODELS` 이름 충돌은 02 §2.8의 규약으로 푼다: env.sh는 `LAYA_MODELS_DIR`만 export하고, upstream research 스크립트(research/scripts/bench_local.py:39)에는 `LAYA_MODELS="$LAYA_MODELS_DIR"`를 인라인으로 주며, laya-serve의 `LAYA_MODELS`는 서버 실행 줄에서 이름 목록으로 준다.
9. CPU 스레드 10(P-코어)이 최적이라는 가정은 D2로 확정한다.
10. supervised 참조값은 리포트 시점 문헌 조회로 채우며 본 문서의 "0.89\~0.90(NSMC)"은 미검증 통념이다.
11. D1 표의 M4 Pro 추정치(CPU 80\~500 ms, MPS 20\~80 ms)는 EPYC/T4 수치에서 외삽한 가설이며 근거 측정이 없다.

[English](03_benchmark_plan.md) | **한국어**
