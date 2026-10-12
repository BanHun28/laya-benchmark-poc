# Laya 벤치마킹 · PoC 진행 가이드 (00_README)

**목적**: [NandhaKishorM/laya](https://github.com/NandhaKishorM/laya) 0.3.23을 이 Mac에서 벤치마킹하고 한국어 PoC까지 끌고 가기 위한 문서 세트의 진입점. 어떤 순서로 무엇을 읽고 실행하는지, 어떤 가정 위에 서 있는지, 끝에서 무엇으로 Go/No-Go를 판단하는지를 한 곳에 둔다.
**선행 문서**: 없음 (이 문서가 진입점).
**산출물**: 문서 맵, Phase 0\~4 진행 순서, 확인 필요 가정 목록, Go/No-Go 결정 매트릭스, 용어집.

## 1. 목적과 범위

대상은 laya 0.3.23 (PyPI 릴리스 2026-10-01), upstream 커밋 `4aa6761be8173de4ce6d92c31b3e40b6eaf59a7c` (2026-10-01)이다. Laya는 choice / score / noul 세 가지 typed question을 encoder 한 번의 forward pass로 답하는 non-autoregressive 결정 엔진이고, 체크포인트 세 개(english, multilingual, typed-decisions)와 입력 언어에 맞는 체크포인트를 고르는 Router를 제공한다. 상세 분석은 `01_laya_analysis.md`.

**하는 것**
1. upstream이 공개한 수치 중 이 Mac에서 재현 가능한 것(한국어 MASSIVE intent, 레이턴시 스케일링, batch 동치성)을 재현해 측정 파이프라인 자체를 검증한다 (Track A, D).
2. 한국어 품질을 upstream이 재지 않은 공개 데이터셋(KLUE-YNAT, KLUE-NLI, NSMC, K-MHaS, 3i4K)과 자체 라벨셋으로 측정한다 (Track B).
3. upstream이 스스로 밝힌 한계(option-order 불안정, noul label following, negation, 고카디널리티 budget 붕괴, over-confidence)가 한국어에서도 성립하는지 프로브한다 (Track C, E).
4. 베이스라인(majority/random, 선택적으로 LLM zero-shot)과 비교해 "zero-shot으로 쓸 수 있는 영역"을 그린다 (Track F).
5. 시나리오 하나를 골라 실제 서비스 형태의 PoC를 만들고(`laya-serve` 기반), 부하·캘리브레이션·threshold 정책까지 검증한 뒤 도입 여부를 결정한다 (`05_poc_plan.md`). 결과는 브라우저 데모 UI(`/poc/ui/`)와 결과 대시보드(`results/dashboard/index.html`)로 직접 확인할 수 있는 형태로 남긴다.
6. Laya vs Jev 소표본 비교: 같은 state·질문·옵션 텍스트를 두 시스템에 넣어 정확도·보정·견고성·지연·비용을 비교한다. 접근은 공개 플레이그라운드뿐이라 소표본·수동 속도로 진행한다 (`09_laya_vs_jev_plan.md`). **완료(2026-10-07)**: zero-shot에서는 Jev가 Laya보다 정확하고(8과제 중 Laya 유의 우세 0, Holm 후 Jev 유의 우세 2), 특히 지시형·다국어 과제에서 격차가 크다. 8과제 macro 정확도는 Jev 0.828, Laya Router 0.661이다(`results/F/jev_cmp/summary.md`).
7. 3-arm 확장(Jev vs vanilla Laya vs trained Laya): Laya 학습 믹스 포함 과제(T2, T5, 신규 T9·T10)와 제외 과제(T1, T3, T4, T6, T7, T8)로 나누고, 과제 데이터로 파인튜닝한 Laya를 세 번째 arm으로 더한다. Jev는 다시 돌리지 않으며, 학습 검증 V1-V6로 Laya가 제대로 학습되었는지도 판정한다 (`11_three_arm_plan.md`). **완료(2026-10-09, 반복 학습 포함)**: 과제 라벨(과제당 약 6,400개)로 파인튜닝한 Laya는 Jev 항목에서 Jev보다 Holm 후 유의하게 낮은 과제가 두 run 모두 없고, 학습 이득은 upstream이 학습하지 않은 과제에 몰린다(ext trained − vanilla 포함 범주 +0.017, 제외 범주 +0.252). 판정은 seed 14 반복 학습과 결론이 같은 것만 확정해 30개 중 27개가 확정이고 3개(T4·T8 Jev 항목)는 불일치다. 보정 분리 열과 T9·T10 Jev 측정(세션 S7)도 끝났다(`results/T3arm/summary.md`, `11_three_arm_plan.md` §9).

**하지 않는 것**
- TypeSafe Jev API 직접 측정은 하지 않음. API 접근이 없어 upstream과 같이 제3자 공개 수치를 인용하되, 대신 공개 플레이그라운드로 24항목 수동 비교를 수행했고(2026-10-06, `results/F/jev_playground_manual_20261006.md`: Jev 0.833 / zero-shot 0.417 / ft-v1 0.917), 이어 8과제 통제 비교를 완료했다(2026-10-07, 항목 6) (출처: BENCHMARKS.md 서두, research/README.md "On comparisons with Jev").
- (범위 변경) 파인튜닝은 처음에 PoC P4 선택 단계로만 두었으나, P4(2026-10-03, 한국어 도메인 라우터)를 수행했고 3-arm 확장(항목 7, 2026-10-08)에서 과제별 파인튜닝을 정식 범위에 넣었다. 단 upstream 파인튜닝 스크립트는 수정하지 않고 사본(`poc/finetune/laya_finetune_mps_patched.py`)에서만 바꾼다.
- 다른 하드웨어. 측정은 이 Mac(Apple M4 Pro, 48GB)에서 CPU fp32와 MPS로 한다. CUDA 서버가 생기면 Track D에 열을 추가하는 방식으로 확장한다.
- upstream 코드 수정. 필요한 스크립트는 `scripts/`에 우리 것으로 쓰고, upstream은 `third_party/laya`(공개 저장소에는 포함하지 않음. https://github.com/NandhaKishorM/laya 를 커밋 4aa6761로 클론해 재현)에 읽기 전용으로 둔다.

## 2. 문서 맵

| 파일 | 역할 | 언제 읽나 | 산출물 |
|---|---|---|---|
| `00_README.md` | 진입점. 진행 순서, 가정, Go/No-Go, 용어 | 처음, 그리고 각 Phase 전환 시 | 결정 매트릭스 체크 |
| `01_laya_analysis.md` | Laya 아키텍처·API·공개 수치·Honest limits 분석, 가설 H1\~H10 | Phase 0 전에 한 번. 수치 해석이 헷갈릴 때 | 벤치마크 가설 |
| `02_environment_setup.md` | uv + Python 3.12 환경, 체크포인트 다운로드·revision pin·symlink, 스모크 테스트 | Phase 0 | `.venv/`, `third_party/laya`, `models/`(이 셋은 공개 저장소에는 포함하지 않음), 스모크 통과 로그 |
| `03_benchmark_plan.md` | Track A\~F 정의, 프로토콜, 지표, 실행 커맨드, 통과 기준 | Phase 2 | `results/<track>/*.json, *.md`, `results/dashboard/index.html` |
| `04_korean_evalset_spec.md` | 한국어 평가셋 소스·변환 규칙·라벨 정책·파일명 | Phase 1 | `data/evals/ko_*.jsonl` + sha256 |
| `05_poc_plan.md` | PoC 시나리오 A/B/C, P0\~P4 단계, 성공 기준 | Phase 3 | `poc/` 서비스 + Laya Playground 데모 UI(`/poc/ui/`, jevplayground 구조), 부하 측정, threshold 정책 |
| `06_templates.md` | 실험 기록, 결과 리포트, Go/No-Go 리포트 템플릿 | 매 측정마다, Phase 4 | 채워진 리포트 |
| `07_korean_support_audit.md` | 한국어 지원 감사 결과(문서·토크나이저·라우팅·실측)와 설계 함의 | 시나리오 결정 전, 스키마·라우팅 설계 시 | `results/korean_support/` |
| `09_laya_vs_jev_plan.md` | Laya vs Jev 소표본 비교 계획과 세션별 결과(공개 플레이그라운드 경유, 과제 T1\~T8, 운영 규칙, 지표, 세션 순서, §10 결론). 완료, 결과 `results/F/jev_cmp/summary.md` | Jev 비교 결과를 해석하거나 재현할 때 | `data/evals/jev_cmp/`, `results/F/jev_cmp/`, 소논문 v2 |
| `11_three_arm_plan.md` | 3-arm 확장 계획: Jev vs vanilla Laya vs trained Laya, Laya 학습 믹스 포함(T2, T5, T9, T10)·제외(T1, T3, T4, T6, T7, T8) 범주, 학습 데이터 구성, 학습 검증 V1-V6, 통계, 실행 순서와 예산. Jev 재실행 없음 | trained Laya 학습·평가를 준비하거나 3-arm 결과를 해석할 때 | `data/evals/jev_cmp_ext/`, `poc/finetune/ckpt_t3arm/`(공개 저장소에는 포함하지 않음), `results/T3arm/`, 소논문 v3 |

## 3. 진행 순서

| Phase | 문서 | 입력 | 산출물 | 검증 기준 | 예상 소요 |
|---|---|---|---|---|---|
| 0 환경 | 02 | 이 Mac, 네트워크 | `.venv`(py3.12, laya 0.3.23), `third_party/laya@4aa6761`, `models/` symlink 3개 | `import laya` 버전 0.3.23, `laya-evals validate` fixture exit 0, 한국어 문장 `route()`가 `multilingual`, CPU·MPS 각 1회 predict 성공 | 반나절 (체크포인트 2.37GB 다운로드 포함) |
| 1 데이터셋 | 04 | HF/GitHub 공개 데이터 (수작업 라벨은 선택) | `data/evals/*.jsonl` 14종(04 §4 표, PoC 주 과제 `ko_massive_domain_8` + `en_massive_domain_8` 쌍 포함) + MANIFEST.json, sha256 목록 | 모든 파일 `laya-evals validate` 통과, 클래스 분포·majority 기록, 라벨 정책이 모델 실행 전에 고정됨 | 1\~2일 (수작업 ≥200건 포함) |
| 2 벤치마크 | 03 | Phase 0, 1 산출물 | `results/<track>/` 리포트, 트랙별 요약 md | Track A 통과(아래 의존성), 각 트랙의 통과 기준 충족 또는 실패 사유 기록 | 2\~3일 |
| 3 PoC | 05 | Phase 2 결과, 시나리오 확정 | `poc/` 서비스, 데모 UI(`/poc/ui/`), 부하 측정, refit temperature, threshold 정책 문서 | P0\~P3 각 단계 검증 통과, Go/No-Go 매트릭스 입력값 채워짐. P2 완료 2026-10-03: ft-v1 서비스 + Laya Playground 수용 점검 11/11 ✔(`results/poc/P2_20261003.md`), `/poc/decide` 왕복 p95 21.1 ms | 3\~5일 (P4 실측: 11,094행 × 3 epoch 학습 35.8분 + 평가 10분, GPU 유휴 시) |
| 4 리포트 | 06 | Phase 2, 3 결과 | 최종 리포트 `results/REPORT.md`(작성 완료 2026-10-03), 대시보드(`results/dashboard/index.html`), Go/No-Go 결정(`results/go_no_go.json`) | 매트릭스 전 항목에 측정값·판정·근거 기재 | 1일 (실제: Track D 1.3 h + 리포트 반일) |

트랙 실행 순서는 A → D → B → C → E → F다. A를 먼저 하는 이유는 측정 파이프라인을 검증하기 위해서고, D를 앞에 두는 이유는 비용이 가장 싸고 이후 트랙의 실행 시간을 예측하게 해주기 때문이다.

**의존성**: Track A에서 `ko_massive_intent_20opt.jsonl`을 CPU fp32로 돌린 multilingual 정확도가 upstream 공개 수치 0.470 (출처: BENCHMARKS.md §Languages, `ko` 행)의 ±0.03 안에 들어와야 한다. 들어오지 않으면 데이터 변환(옵션 샘플링 seed 13, 처음 100개 test 행)이나 환경(dtype, revision) 문제이므로, 이것이 해결되기 전의 Track B/C/E 결과는 신뢰하지 않는다.

## 4. 디렉토리 레이아웃

```text
benchmarkforLaya/
├── docs/                 # 이 문서 세트 (00~06)
├── third_party/laya/     # upstream 클론 @ 4aa6761, 읽기 전용. research/scripts, examples, verify 사용
│   └── models -> ../../models   # examples/_common.py가 로컬 체크포인트를 찾는 경로
├── models/               # HF snapshot으로의 symlink: laya/, laya-multilingual/, laya-typed-decisions/ (LAYA_MODELS_DIR=$PWD/models; research 스크립트 실행 시 LAYA_MODELS="$LAYA_MODELS_DIR" 인라인)
├── data/
│   ├── raw/              # 원본 데이터 (HF datasets 캐시 또는 GitHub raw 다운로드)
│   ├── handwritten/      # 수작업 원본(부정문 쌍, PoC 라벨, 라벨 정책)
│   └── evals/            # laya-evals JSONL (ko_*.jsonl) + MANIFEST.json(sha256)
├── scripts/              # 우리 스크립트: 데이터 변환, 프로브, 레이턴시, 부하, 플롯
├── results/
│   ├── <track>/          # <YYYYMMDD-HHMM>_<model>_<dataset>.json / .md (laya-evals --json/--markdown 출력 포함)
│   ├── dashboard/        # build_dashboard.py 산출 HTML (index.html)
│   └── verdicts.json / go_no_go.json  # 가설 판정·Go/No-Go 수동 기록 (06 §2)
├── poc/                  # PoC 서비스 코드, 설정, 부하 테스트
│   └── service/ui/       # Laya Playground 데모 UI (index.html, examples.json, /poc/ui/ 로 서빙)
├── .venv/                # uv venv (Python 3.12)
└── env.sh                # 환경 변수 (02 §2.8)
```

`.gitignore` 대상(공개 저장소에는 포함하지 않음): `models/`, `third_party/`, `data/raw/`, `.venv/`, `.env`. `results/**/*.json`은 크기를 보고 결정하되 `.md` 요약은 항상 커밋한다. `git init`은 Phase 0의 선택 단계다 (`02_environment_setup.md`).

## 5. 핵심 가정 및 확인 필요 사항

각 항목은 "기본값으로 진행한다"는 뜻이다. 다르게 가려면 해당 Phase 시작 전에 바꿔야 한다.

1. **PoC 시나리오**: **결정됨 (2026-10-02): C 토픽/도메인 라우터.** 주 과제 MASSIVE ko 8도메인(`ko_massive_domain_8`, 같은 id의 영어 쌍으로 한국어 페널티 측정), 보조 KLUE YNAT 7토픽(`ko_klue_ynat_7`). A(CS triage + gateway)는 zero-shot으로 G1 미달(P0/P0b)이라 P4 파인튜닝 후보로 보류, B는 upstream held-out 가드레일 0.708\~0.762, moderation 0.530 (출처: BENCHMARKS.md §Themes)이라 제외. 근거와 taxonomy는 `05_poc_plan.md` §2, §4.
2. **LLM 베이스라인**: `claude-haiku-4-5-20251001` zero-shot 분류를 Track F 베이스라인으로 쓸지, API 키가 있는지. **기본값: 선택. 키가 없으면 majority/random과 공개 수치만으로 진행**하고 Go/No-Go G1은 절대값(≥ 0.80)으로 판정한다.
3. **하드웨어 범위**: 이 Mac만 vs CUDA 서버 추가. **기본값: Mac만.** CUDA가 있으면 Track D에 열을 추가하고 TileLang fast path와 `compile=True`도 측정 범위에 들어온다.
4. **한국어 라벨링 리소스**: C 선택으로 G1 판정에는 수작업 라벨이 필요 없다(MASSIVE·KLUE 공개 라벨). 검토 대상은 확정 taxonomy에 대한 선택적 "실제 질의" 세트 100건뿐이며(05 §열린 질문 3), A를 P4로 살릴 때만 `ko_poc_triage_v1.jsonl` ≥200건 라벨링이 다시 필요하다(그때 기본값: 1인 라벨 + 라벨 정책 선행 고정, 2인 교차 가능 시 Cohen's kappa 기록).
5. **Jev 접근**: TypeSafe Jev API 키 유무. **결정(2026-10-06): 키 없음. 공개 수치 인용 + 공개 플레이그라운드 수동 소표본(n=24)으로 대체**(`results/F/jev_playground_manual_20261006.md`). 정식 paired 비교는 API 키 확보 시.
6. **결과 공개 범위**: 한국어 결과를 upstream issue/PR(zh community bench 사례처럼)로 기여할지. **기본값: 내부 리포트. 기여는 Phase 4 이후 별도 결정.** 기여를 염두에 두면 Phase 1에서 데이터 라이선스(CC BY 4.0 등)와 raw prediction 보존을 지켜야 한다. **프로젝트 책임자 결정(2026-10-12): 공개 GitHub 저장소로 공개한다.** 데이터는 출처별 라이선스 표(`DATA_LICENSES.md`)와 함께 공개하되 AG News 파생 파일은 제외한다. Jev 원기록과 플레이그라운드 캡처, PDF, 체크포인트는 공개하지 않는다.
7. **시간 예산**: Phase 0\~4 합계 약 8\~12 영업일 (P4 파인튜닝 제외). **기본값: 이 예산 안에서 P4는 하지 않는다.**
8. **한국어 지원 판정 반영 (결정됨, 2026-10-02)**: 한국어 채널은 `lang="ko"` 명시, 추론 전 NFC 정규화, noul 결정 임계값은 0.5 고정이 아니라 질문별로 dev set에서 선택. 근거와 상세는 `07_korean_support_audit.md` §6. 열린 질문이 아니라 증거로 정해진 항목이다.

## 6. Go/No-Go 결정 매트릭스

모든 기준값은 **제안값**이며 프로젝트 책임자 확정이 필요하다. 측정값과 판정은 `06_templates.md`의 Go/No-Go 리포트에 기록한다.

| # | 기준 | 측정 트랙 | 기준값 (제안) | 근거 |
|---|---|---|---|---|
| G0 | 재현 게이트 | A | `ko_massive_intent_20opt` multilingual 정확도 0.470 ± 0.03 (CPU fp32) | upstream 공개 수치 (출처: BENCHMARKS.md §Languages). 통과 전까지 B/C/E 결과 무효 |
| G1 | PoC 태스크 정확도 | PoC P1 (Track B, `ko_massive_domain_8` test half; `ko_klue_ynat_7` 보조) | LLM zero-shot 베이스라인 대비 -5pt 이내. LLM 없으면 절대 ≥ 0.80 | upstream zh 커뮤니티 bench: 6-domain voice routing 0.883, CS routing 0.640 (출처: BENCHMARKS.md §Community evaluation). PoC 스키마는 ≤ 8 옵션(router_v1은 8)이라 head_max_len budget 영향이 없어야 한다 |
| G2 | 게이팅 후 커버리지 | E | refit temperature + `min_confidence`로 오류율 ≤ 5%에서 커버리지 ≥ 0.70 (G1에 종속: 정확도 a에서 상한 a/(1−e)) | Jev 제3자 공개 coverage_at_5pct_error AG News 0.830 (출처: research/scripts/bench_apps.py `JEV_PUBLISHED`). docs/staged-adoption.md의 "threshold는 held-out에서 고르는 정책" 원칙 |
| G3 | 캘리브레이션 | E | refit 후 held-out ECE ≤ 0.10 | upstream refit이 0.466 → 0.081 (laya), 0.314 → 0.106 (multilingual) (출처: BENCHMARKS.md §Calibration). multilingual은 출하 시 temperature 없음 |
| G4 | option-order 견고성 | C | PoC 스키마에서 순열당 flip rate(5 순열 평균) ≤ 0.10, 보조로 게이트 통과 결정의 flip | upstream 20옵션 flip 0.150 / 0.230, Jev 0.13 (출처: BENCHMARKS.md §Option-order robustness). ≤7 옵션이면 더 낮아야 한다는 가설 |
| G5 | in-process 레이턴시 | D | 3-question call p95 ≤ 100 ms (MPS), ≤ 500 ms (CPU 10 threads) | T4 1q 32.8 ms, EPYC 4코어 multilingual 1q 193 ms, 5q 912 ms (출처: BENCHMARKS.md §Speed, §Server CPU). M4 Pro 수치는 가설, Track D에서 확정 |
| G6 | 서빙 레이턴시 | D, PoC P2 | `laya-serve` 10 RPS에서 p95 ≤ 150 ms (MPS, preload) | GB10 HTTP 경유 1q p50 100 ms 중 \~93 ms가 고정 오버헤드 (출처: BENCHMARKS.md §Other hardware). HTTP 오버헤드가 지배할 수 있어 G5와 분리 |
| G7 | batch 동치성 | D, C | `predict` vs `predict_batch(sort_by_length=True)` argmax 불일치 0건, max \|Δp\| ≤ 0.01 | upstream 10,000건에서 결정 변경 0, 수치 차 ≤ 0.0001 (출처: research/README.md "Length batching"). ONNX 80건 결정 변경 0 (출처: README.md "Batch Mode") |

판정 규칙(제안): G0 미통과면 판정 보류. G1·G2·G5 중 하나라도 미달이면 No-Go 또는 "파인튜닝(P4) 후 재평가". G3·G4·G6·G7은 미달 시 조건부 Go(운영 가드 추가)로 다룬다.

**현재 판정(최종, 2026-10-03).** zero-shot router_v1 + multilingual(2026-10-02): G0 통과(Δ0) · G1 미달 0.492 · G2 미달 0.224 · G3 경계 통과 0.098 · G4 미달 0.270 → **zero-shot은 No-Go**. 파인튜닝 ft-v1(run `full_20261003-1156`, 35.8분 학습, MASSIVE ko train 11,094행): G0 통과 · G1 **통과** 0.900(중복 제외 0.893, 전체 test 2,917행 0.913) · G2 **통과** 2,917행 dev T 적용 coverage 0.923(오류 0.042), 250행 test 절반 사후 T 0.756 · G3 **통과** 0.053 · G4 **통과** 0.037 · G5 **통과** 3문항 p95 MPS 22.6 / CPU 57.8 ms · G6 **통과** laya-serve 10 RPS 3문항 p95 79.4 ms · G7 **통과** predict vs predict_batch(sort) flip 0, max \|Δp\| 0.0001 → **G0\~G7 모두 통과, Conditional Go(파인튜닝 파이프라인 전제)**. 근거: `results/go_no_go.json`, `results/REPORT.md`.

**현재 결론(Laya vs Jev, 2026-10-07).** zero-shot에서는 Jev가 Laya보다 정확하고(8과제 중 Laya 유의 우세 0, Holm 후 Jev 유의 우세 2), 특히 지시형·다국어 과제에서 격차가 크다. Laya는 로컬 실행·지연·비용과 파인튜닝으로 격차를 메울 수 있다는 점에서 경쟁력이 있다. 이 결론은 위 G0\~G7 판정(한국어 라우팅 PoC 기준)을 바꾸지 않는다. 근거: `results/F/jev_cmp/summary.md`, `results/REPORT.md` §0a.

## 7. 용어집

| 용어 | 뜻 |
|---|---|
| System 1 decision engine | 텍스트를 생성하지 않고 한 번의 forward pass로 typed 결정의 확률 분포를 내는 모델. 자유 생성이 없어 파싱·hallucination이 없다 |
| non-autoregressive | 토큰을 순차 생성하지 않음. 레이턴시가 출력 길이에 비례하지 않고 입력 길이와 질문 수에만 의존 |
| state | 판단 대상 입력. `str`, `dict`, `list`(대화 턴) 모두 가능, dict는 JSON으로 렌더링 |
| question / instructions / criteria | 질문 하나 = `type` + `instructions`(프롬프트 문장) + `criteria`(choice는 라벨→설명, score는 레벨 설명 리스트, noul은 선택적 true/false 설명) |
| choice | 닫힌 라벨 집합에서 하나 선택. `choice`와 `probabilities` 반환 |
| score | 순서형 레벨. 기대값(`score`)을 0부터 시작하는 레벨 인덱스 스케일로 반환, `legend`로 인덱스→설명 |
| noul | 진술이 성립할 확률 P(true). `noul` 필드가 그 확률 |
| Router | script·언어 감지로 체크포인트를 고르는 진입점. 한글은 항상 multilingual로 간다 |
| checkpoint english / multilingual / typed-decisions | 각각 ModernBERT-large 영어, mmBERT-base 100+ 언어, 영어 typed-decisions 파인튠 |
| max_len / head_max_len | 시퀀스 전체 토큰 예산 / 질문+옵션 머리(head)의 상한. state에 남는 room = `max_len - head_len - 1` |
| RLCD | strictly proper scoring rule을 보상으로 쓰는 RL 학습. 확률이 캘리브레이션 되도록 유도 |
| temperature / ECE | logits를 나누는 스칼라(버킷별, [0.5, 5.0]로 clamp) / Expected Calibration Error, 낮을수록 좋음, laya-evals는 15 bins |
| confidence vs answer_confidence | 전자는 1 - 정규화 엔트로피(옵션 수에 민감), 후자는 보고된 답의 확률 max p(캘리브레이션 대상). 게이팅은 후자로 |
| min_confidence / abstention | 호출 시 threshold를 주면 `answer_confidence` 미달 답에 `low_confidence`와 `abstention`(passed / abstained / unevaluated) 표기 |
| predict_batch / sort_by_length | 같은 질문 세트에 대해 여러 state를 forward pass에 묶음 / 길이 비슷한 state를 같은 pass로 묶어 padding 낭비 감소 |
| predict_long | `max_len`을 넘는 state를 겹치는 윈도우로 스캔하고 질문별로 집계(noul은 max, choice/score는 최고 confidence 윈도우) |
| laya-evals run identity | 리포트 `config`의 `dataset_sha256`, `questions_sha256`, `revisions`, `laya_version`. 베이스라인과 비교 가능 여부를 판정하는 키 |
| Jev | TypeSafe의 호스팅 결정 API. `laya-serve`가 같은 `POST /v1/systemone` 프로토콜을 제공. 수치는 제3자 공개치만 존재 |

## 열린 질문 / 가정

- §5의 1\~7번은 전부 열린 질문이며 기본값으로 진행 중이다. 특히 1번(시나리오)과 2번(LLM 베이스라인 유무)은 G1 판정 방식을 바꾼다.
- G5·G6의 레이턴시 기준값은 upstream T4/EPYC 수치에서 외삽한 가설이다. Track D 첫 측정 후 현실적인 값으로 재조정하되, 재조정 사실과 이유를 `06_templates.md` 리포트에 남긴다.
- 한국어 공개 데이터셋 중 NSMC와 3i4K는 HF `datasets` 스크립트 로더로는 더 이상 열리지 않아 GitHub raw 파일을 쓴다. 라이선스 확인은 `04_korean_evalset_spec.md`에서 한다.
- 수작업 라벨셋(≥200건)의 품질이 G1 판정의 상한을 정한다. 1인 라벨이면 라벨 노이즈를 리포트에 명시한다.
- upstream 51개 언어 표의 multilingual 열은 "refreshed" 재실행 값이다(committed 파일은 재현되지 않음, 출처: BENCHMARKS.md 서두, #208). 우리가 비교하는 ko 0.470도 refreshed 값이다.

[English](00_README.md) | **한국어**
