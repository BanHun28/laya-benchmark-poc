# Laya 벤치마크와 PoC

[Laya](https://github.com/NandhaKishorM/laya) 0.3.23(upstream 커밋 4aa6761, 체크포인트 번들 `convaiinnovations/laya` @ 55cf4c4)의 독립 벤치마크이자 개념 증명(PoC)이다. Laya는 encoder 한 번의 forward pass로 typed decision(choice, score, noul)의 확률 분포를 내는 오픈소스 비자동회귀 "System-1" 결정 엔진이다. 이 저장소에는 한국어 도메인 라우팅 PoC를 포함한 한국어 적용성 연구(Track A–F, 단계 P0–P4, 파인튜닝한 라우터와 PoC 서비스), TypeSafe의 호스팅 결정 API인 Jev와의 과제 T1–T10 통제 비교, seed 14 반복 학습을 포함한 3-arm 연구(Jev vs vanilla Laya vs 과제별 파인튜닝 Laya)가 있다. Laya 실행은 모두 Apple M4 Pro 한 대(48 GB, macOS 26.6.2)에서 했다.

> **고지.** 이 프로젝트는 독립 프로젝트이며 Laya 개발자(Convai Innovations)나 TypeSafe와 관계가 없다. Jev는 Jev API가 아니라 독립 공개 플레이그라운드 [jevplayground.com](https://jevplayground.com)을 거쳐 측정했다. 모델 버전은 표시되지 않고, 확률은 소수 둘째 자리로 반올림되며, 표본이 작다(통제 비교에서 과제당 n=40).

## 주요 결과

- **zero-shot에서는 Jev가 더 정확하다.** 같은 state·질문·옵션 문자열에서 Jev는 8과제 T1\~T8 중 4개에서 정확 McNemar 검정으로 유의하게 앞섰고(Holm 보정 후 2개, T1과 T7) Laya가 유의하게 앞선 과제는 없었으며, 격차는 지시형·다국어 과제에서 특히 크다. macro 정확도는 Jev 0.828, Laya english 0.646, multilingual 0.598, Router 0.661이다(`docs/10_paper_laya_vs_jev.md` 초록, `results/REPORT.md` §0).
- **지연과 비용은 서로 다른 배포 형태를 반영한다.** Jev 플레이그라운드 표시 지연은 중앙 226 ms(브라우저 POST 465 ms, 인터넷 왕복 포함)이고, 로컬 Laya는 1문항에 in-process 13.8\~86.6 ms, localhost HTTP 20.1\~50.7 ms다. 모델 속도 비교가 아니다. Jev 비용은 1,000 decision당 $0.0197(제3자 인용 단가, 확인 필요)이고 Laya는 토큰 과금이 없다(`results/REPORT.md` §0).
- **확신도 임계값은 과제마다 맞춰야 한다.** Jev 확률의 의미는 문항 형식마다 다르다(단일 choice는 오답의 59%가 top ≥ 0.90, 다문항 T1은 과소확신, T10은 ECE 0.623). 두 시스템 모두 확신도 기반 자동 처리의 임계값을 과제별 held-out 데이터로 다시 맞춰야 한다(`docs/10_paper_laya_vs_jev.md` 초록, §4.3).
- **과제별 파인튜닝을 하면 Laya는 Jev에 유의하게 뒤지지 않는다.** 과제당 라벨 약 6,400개(M4 Pro MPS 학습 7.5\~43.3분, T8은 1.4분)로 파인튜닝한 Laya는 본 학습 run 1에서 10과제 모두 Holm 보정 후 Jev와 유의차가 없었고, 반복 학습 run 2에서는 T8에서만 유의하게 앞섰다. 두 run 모두 Holm 보정 후 Jev가 유의하게 앞선 경우는 없다. 이는 전문화한 Laya와 zero-shot Jev의 비교다(`docs/10_paper_laya_vs_jev.md` 초록).
- **학습 이득은 Laya 학습 믹스 밖의 과제에 몰린다.** 확장 평가 세트(ext)에서 trained − vanilla는 포함 범주 4과제(upstream이 밝힌 Laya 학습 믹스에 든 과제)에서 +0.017, 제외 범주 6과제에서 +0.252이고, 차이의 차이는 run 1에서 +0.235 [+0.147, +0.316]이다(run 2: +0.020, +0.257, +0.238 [+0.144, +0.325]) (`docs/10_paper_laya_vs_jev.md` 초록).
- **판정은 두 학습 run이 일치할 때만 확정한다.** 판정 30개(과제 10개 × 비교 3종) 가운데 27개가 확정, 3개가 불일치이고, 불일치는 모두 Holm p가 0.05 근처인 n=40 Jev 항목 비교다. MPS 학습은 비트 단위로 결정적이지 않다. 같은 파이프라인의 T1 세 run은 0.747 / 0.690 / 0.735를 냈다(`docs/11_three_arm_plan.md` §9).
- **한국어 도메인 라우팅에는 파인튜닝이 필요하다.** zero-shot 8도메인 라우팅은 test 절반에서 0.492다. MASSIVE ko train 11,094행으로 36분 파인튜닝한 ft-v1은 같은 test 절반에서 0.900(전체 test 2,917행에서 0.913), ECE 0.053, 옵션 순서 flip 0.037이고, PoC 판정은 Conditional Go(파인튜닝 파이프라인 전제)다(`results/REPORT.md` §0).

## 문서

읽는 순서:

1. [`results/REPORT.md`](results/REPORT.md): 모든 Track의 결과 리포트. Laya vs Jev 비교(§0a)와 3-arm 비교(§0b)를 담았다.
2. [`docs/10_paper_laya_vs_jev.md`](docs/10_paper_laya_vs_jev.md): 소논문(v3). zero-shot 비교와 3-arm 연구를 다룬다.
3. [`docs/11_three_arm_plan.md`](docs/11_three_arm_plan.md): 3-arm 계획. 결과는 §9에 있다.
4. [`docs/00_README.md`](docs/00_README.md): 계획 문서의 색인(범위, 문서 맵, 진행 순서, Go/No-Go 매트릭스).

| 문서 | 제목 |
|---|---|
| [`docs/00_README.md`](docs/00_README.md) | Laya 벤치마킹 · PoC 진행 가이드 |
| [`docs/01_laya_analysis.md`](docs/01_laya_analysis.md) | Laya 분석: 아키텍처, API, 공개 수치, 한계 |
| [`docs/02_environment_setup.md`](docs/02_environment_setup.md) | 환경 구성 |
| [`docs/03_benchmark_plan.md`](docs/03_benchmark_plan.md) | Laya 벤치마크 계획 |
| [`docs/04_korean_evalset_spec.md`](docs/04_korean_evalset_spec.md) | 한국어 평가셋 구축 스펙 |
| [`docs/05_poc_plan.md`](docs/05_poc_plan.md) | PoC 계획: 한국어 도메인 라우터(시나리오 C) |
| [`docs/06_templates.md`](docs/06_templates.md) | 기록 템플릿 |
| [`docs/07_korean_support_audit.md`](docs/07_korean_support_audit.md) | 한국어 지원 감사 결과와 설계 함의 |
| [`docs/08_paper_ko.md`](docs/08_paper_ko.md) | 소논문: Laya 다국어 System-1 결정 엔진의 한국어 적용성: zero-shot 벤치마크, 파인튜닝, 그리고 도메인 라우팅 PoC |
| [`docs/09_laya_vs_jev_plan.md`](docs/09_laya_vs_jev_plan.md) | Laya vs Jev 소표본 비교 계획 |
| [`docs/10_paper_laya_vs_jev.md`](docs/10_paper_laya_vs_jev.md) | 소논문(v3): Jev, vanilla Laya, trained Laya의 3-arm 통제 비교: 비자동회귀 결정 엔진의 zero-shot 정확도와 과제별 파인튜닝 효과 |
| [`docs/10_paper_laya_vs_jev_v2.md`](docs/10_paper_laya_vs_jev_v2.md) | 소논문(v2, v3로 대체됨): Laya와 Jev의 통제된 비교: 비자동회귀 결정 엔진의 zero-shot 정확도, 보정, 다국어 일관성, 지연 |
| [`docs/11_three_arm_plan.md`](docs/11_three_arm_plan.md) | 3-arm 확장 계획: Jev vs vanilla Laya vs trained Laya |

언어:

- 각 문서의 영어판은 `X.md`이고, 그 옆에 한국어판 `X.ko.md`가 있다. 두 파일은 줄 단위로 맞춰져 있어 `file:line` 인용이 양쪽에서 그대로 성립한다.
- 스크립트가 생성하는 리포트(예: `results/F/jev_cmp/summary.ko.md`, `results/T3arm/summary.ko.md`)의 한국어판은 스크립트가 쓰고 영어판은 정적 번역이며, 리포트를 다시 생성하면 한국어 파일만 바뀐다.
- PoC UI(`poc/service/ui/`), 결과 대시보드(`results/dashboard/index.html`), 일부 코드 주석은 한국어다.

## 저장소 구성

| 디렉터리 | 내용 |
|---|---|
| `docs/` | 계획, 스펙, 한국어 지원 감사, 소논문(00–11) |
| `data/` | `MANIFEST.json`을 갖춘 laya-evals JSONL 평가셋(`data/evals/`): 한국어 세트, 플레이그라운드 폼을 포함한 Laya vs Jev 세트(`jev_cmp/`), 확장 세트(`jev_cmp_ext/`). 원본 다운로드(`data/raw/`)는 포함하지 않는다 |
| `scripts/` | 세트 빌더, 옵션 순서 probe, 지연·배치·HTTP 벤치마크, 보정, 지표, 환경 기록, 대시보드 빌더 |
| `results/` | run card, 리포트, 지표: Track `A`–`F`, `korean_support/`, `poc/`(P0–P2), `P4/`, `F/jev_cmp/`(Laya vs Jev), `T3arm/`(3-arm), `env/`, `dashboard/`, `REPORT.md` |
| `poc/` | PoC 서비스(`service/`, 데모 UI는 `service/ui/`), 질문 스키마, 보정 payload, shadow 로그, 학습 행을 포함한 파인튜닝 파이프라인(`finetune/`) |
| `models/` | 포함하지 않음: 내려받은 체크포인트로의 심볼릭 링크(`docs/02_environment_setup.md` §2.7) |
| `third_party/` | 포함하지 않음: 커밋 4aa6761의 upstream Laya clone(`docs/02_environment_setup.md` §2.5) |

루트 파일: `env.sh`(환경 변수, `docs/02_environment_setup.md` §2.8), `LICENSE`, `NOTICE`, `DATA_LICENSES.md`.

## 재현

### 환경

설치, 버전 고정, smoke test는 `docs/02_environment_setup.md`에 있다. 측정에는 Python 3.12.12, laya 0.3.23, torch 2.14.1, transformers 5.18.0(`results/env/env_20261002-1333.json`), 커밋 4aa6761의 upstream clone, revision 55cf4c4의 체크포인트 번들을 썼다. 품질 수치는 CPU fp32이고 파인튜닝은 MPS에서 돌렸다.

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python "laya[serve,onnx,structured]==0.3.23" datasets pandas scikit-learn psutil matplotlib
git clone https://github.com/NandhaKishorM/laya.git third_party/laya
git -C third_party/laya checkout 4aa6761be8173de4ce6d92c31b3e40b6eaf59a7c
hf download convaiinnovations/laya --revision 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 --quiet | tee results/env/snapshot_path.txt
# models/ 심볼릭 링크: docs/02_environment_setup.md §2.7. 그다음 새 셸마다:
source env.sh
```

### 포함하지 않은 것

정확한 목록은 `.gitignore`에 있다.

- 파인튜닝 체크포인트 `poc/finetune/ckpt_*/`(약 20 GB). 학습으로 다시 만들 수 있지만 비트 단위로 같지는 않다(아래 참조).
- 내려받은 모델(`models/`: Laya 체크포인트와 ONNX export), upstream clone(`third_party/`), 데이터셋 원본 다운로드(`data/raw/`). 위의 설치 명령과 아래 빌더가 체크포인트, clone, 데이터셋을 고정 revision으로 다시 받으며, ONNX export는 Track D(`results/D/D_run.sh`)가 만든다.
- 문서의 PDF 렌더링(`*.pdf`). 원본은 Markdown 파일이다.
- Jev 플레이그라운드 캡처(스크린샷, 페이지·accessibility snapshot, 네트워크·콘솔 로그, 주입 스크립트), Jev 원기록(요청별 응답, 요청 로그, 마스터 로그, 요청별 timing), Jev의 문항별 출력. 아래 "Jev 측정 방법" 참조.
- AG News 파생 파일: T2 평가셋, T2 학습 파일, S1·S1b 플레이그라운드 기록. 코퍼스 이용 조건 때문에 제외했다(`DATA_LICENSES.md`).

### 다시 만들기

빌더는 원본 데이터셋을 고정 revision이나 checksum으로 읽고(`data/raw/`에 내려받음), 바이트가 다른 기존 세트 파일은 `--force` 없이는 덮어쓰지 않는다. 제외한 T2 파일을 포함해 평가·학습 세트를 다시 만들려면:

```bash
source env.sh && export HF_HOME=$PWD/data/raw/hf && unset HF_HUB_OFFLINE
.venv/bin/python scripts/build_ko_evalsets.py all --n 500 --seed 13   # 한국어 세트, data/evals/ (ablation 변형: docs/04 §6)
.venv/bin/python scripts/build_jev_cmp_sets.py all                    # T1-T10 세트와 플레이그라운드 폼, data/evals/jev_cmp/
.venv/bin/python scripts/build_train_sets.py all                      # ext 세트와 과제별 train/dev/calib 행
.venv/bin/python poc/finetune/ft_task.py items --task T2 --base english --out poc/finetune/data/t3arm/T2_english.pt
.venv/bin/python poc/finetune/ft_task.py devsub --task T2 --n 40      # 옵션 순서 probe용 T2 dev 부분집합
```

다른 과제의 학습 items와 P4 행·items(`poc/finetune/make_domain8_items.py rows|items`)는 포함돼 있다. 학습은 MPS에서 체크포인트를 다시 만들며, 3-arm 게이트(`poc/finetune/READY_T3ARM`)는 먼저 `PREFLIGHT_ONLY=1`로 점검한다:

```bash
bash poc/finetune/run_full.sh                                # P4 ft-v1 -> poc/finetune/ckpt_domain8_v1/
PREFLIGHT_ONLY=1 bash poc/finetune/run_all_tasks.sh          # 3-arm 게이트 점검만
bash poc/finetune/run_all_tasks.sh                           # 3-arm 본 학습 run 1 -> poc/finetune/ckpt_t3arm/<task>/
SEED=14 RUN_TAG=rep_s14 bash poc/finetune/run_all_tasks.sh   # 반복 학습 run 2 (seed 14) -> poc/finetune/ckpt_t3arm_rep_s14/
```

모든 Track, PoC, 두 비교의 전체 명령 목록은 `results/REPORT.md` §9에 있고, 3-arm 준비·검증 명령은 `results/T3arm/PREP_20261008.md` "명령어" 절에 있다. MPS 학습은 비트 단위로 결정적이지 않아 다시 학습한 체크포인트는 측정에 쓴 것과 다르고, 보관된 체크포인트의 평가는 결정적이다(`results/REPORT.md` §8).

### 새 clone에서 돌릴 수 없는 것

아래는 공개하지 않은 입력을 읽는다:

- `results/F/jev_cmp/s6_summary.py build|verify`와 `results/T3arm/t3arm_summary.py build|verify`: Jev 원기록과 T2 세트를 읽고, 3-arm 종합은 크기를 재려고 체크포인트 디렉터리도 읽는다.
- Jev 세션 도구 `results/F/jev_cmp/jev_cmp.py record|analyze|stability|t1`, 세션별 `results/F/jev_cmp/sessions/*/s*_record.py` 스크립트, `results/F/jev_f.py record|analyze`: 요청별 기록과 브라우저 dump를 읽는다.
- `results/poc/P2_offline_check.py`와 PoC 서비스 `poc/service/app.py`: ft-v1 체크포인트 `poc/finetune/ckpt_domain8_v1/`이 필요하다. 서비스는 체크포인트의 `rl_agent_config.json` 해시가 임계값 T 0.907을 고른 체크포인트의 해시와 다르면 기동하지 않는다(`poc/service/policy.py`, `docs/05_poc_plan.md` §5).

두 종합의 공개 산출물(`summary.json`, `summary.ko.md`)은 로컬의 전체 입력으로 만들었고, 문서에는 `verify` 불일치 0이 기록돼 있다(`docs/09_laya_vs_jev_plan.md` §8, `docs/11_three_arm_plan.md` §9).

## Jev 측정 방법

Jev는 플레이그라운드 자체 엔드포인트(jevplayground.com의 `POST /api/evaluate`, Model ID `typesafe-ai/jev`, 버전 미표기)로만, 사람이 쓰는 속도로 호출했고, Laya가 읽는 것과 같은 state 바이트·질문·옵션 문자열을 넣었다. 한국어 파일럿(n=24)은 수작업으로 했고, 세션 S1, S1b, S2–S5, S7은 플레이그라운드 폼 파일로 폼을 채우고 payload 해시가 맞을 때만 Run을 누르는 브라우저 자동화(Playwright MCP, Chromium)를 썼다. 운영 규칙(`docs/09_laya_vs_jev_plan.md` §2):

- 요청 간격 10 s 이상(관측된 최소 간격 12.1 s);
- 세션별 요청 상한, 그리고 2026-10-07 프로젝트 책임자가 해제하기 전까지 하루 100 요청 상한;
- 5xx이면 60 s 뒤 그 항목만 한 번 재시도, 429·제한 문구·captcha이면 즉시 세션 중단;
- 성공 여부와 관계없이 모든 요청을 요청 로그에 기록. 자동화 세션에서는 보낸 body를 폼 payload와 바이트 단위로 대조했다(411/411, 80/80 일치).

사이트가 받은 요청은 2026-10-06부터 2026-10-08까지 모두 518회이고, 파일럿 25회와 상태 확인 2회를 포함한다(`docs/09_laya_vs_jev_plan.md` §7.2). 그중 2회가 HTTP 502였고 HTTP 429는 없었다(같은 문서 §9).

Jev 원기록(요청별 응답, 요청 로그, timing), 플레이그라운드 캡처, Jev의 문항별 출력은 공개하지 않는다(프로젝트 책임자 결정 2026-10-12). 문서에는 집계 결과와 방법을 남겼고, 세션별 절차는 각 run card(`results/F/jev_cmp/sessions/S*/S*_run_card.md`, 파일럿은 `results/F/F_jev_20261006.md`)에 있다.

## 라이선스

코드와 문서는 Apache-2.0(`LICENSE`)으로 배포하고, `NOTICE`에 Laya(Convai Innovations, Apache-2.0)에서 파생한 파일을 적었다. 공개 데이터셋에서 파생한 데이터 파일과 `DATA_LICENSES.md`에 적은 그 밖의 제삼자 자료는 원래 라이선스를 따르며 Apache-2.0 허락 범위에 들지 않는다. 그중에는 ShareAlike(CC BY-SA)와 NonCommercial(CC BY-NC 4.0) 자료가 있다. AG News 파생 파일은 포함하지 않는다.

[English](README.md) | **한국어**
