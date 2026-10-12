# 05. PoC 계획: 한국어 도메인 라우터(시나리오 C)

**목적**: laya를 "한국어 사용자 요청을 겹치지 않는 도메인 핸들러(또는 인덱스)로 보내는 1차 라우터 + confidence 게이트 + fallback(LLM 또는 사람)"으로 production 후보에 올릴 수 있는지, 한 번의 forward pass 품질·calibration·서빙 latency·운영 가능성을 단계별로 검증한다. 벤치마크(03)가 "모델이 무엇을 얼마나 잘하는가"를 재는 반면, 이 PoC는 "우리 서비스 형태로 묶었을 때 쓸 수 있는가"를 잰다. 시나리오는 2026-10-02에 C로 결정됐다(§2). A(CS triage)는 보류하고 P4 파인튜닝 후보로만 남긴다.

**선행 문서**: `00_README.md`(진행 순서, §6 Go/No-Go 기준), `01_laya_analysis.md`(아키텍처·Honest limits·가설 H1-H10), `02_environment_setup.md`(환경·스모크), `03_benchmark_plan.md`(Track A-F 프로토콜, 측정 스크립트), `04_korean_evalset_spec.md`(`ko_massive_domain_8.jsonl`, `ko_klue_ynat_7.jsonl` 등 공개 라벨 평가셋), `06_templates.md`(run card, REPORT, ADR), `07_korean_support_audit.md`(한국어 지원 판정과 설계 함의).

**산출물**: `poc/schema/router_v1.json`(정규 스키마), `poc/service/` (hooks 포함 서빙 코드, `/poc/decide`·`/poc/shadow`·`/poc/meta` 엔드포인트), `poc/service/ui/index.html` + `poc/service/ui/examples.json` (Laya Playground 데모 UI, `/poc/ui/`), `poc/calibration/ko_v1.json`, `poc/loadtest/` (요청 바디, 부하 결과), `poc/logs/shadow.jsonl`, `results/poc/P*_*.json|md`, 정책 ADR, 최종 `results/poc/REPORT.md`. 수작업 라벨셋은 G1 판정에 필요하지 않다(공개 라벨 사용). 보류된 A의 스키마(`triage_v1.json`, `gateway_v1.json`, `*_v1b.json`)는 그대로 둔다.

---

## 1. PoC 목표와 성공 기준

PoC가 답해야 하는 질문은 하나다. **"laya(multilingual 체크포인트, `lang="ko"` 고정)를 한국어 요청 도메인 라우터(1차 라우팅 + confidence 게이트 + fallback)로 production 후보에 올릴 수 있는가?"** 답은 Go / Conditional Go(파인튜닝 또는 오류 예산 재합의 전제) / No-Go 셋 중 하나이며, 판정 기준은 `00_README.md` §6의 기본값을 그대로 쓴다(여기서 재정의하지 않는다). 아래 매핑은 제안이며 기준값은 프로젝트 책임자 확정 대상이다.

| 영역 | 측정 항목 | 기준 (00 §6, 제안) | 산출 단계 | 측정값(zero-shot 2026-10-02 → 파인튜닝 ft-v1 2026-10-03) |
|---|---|---|---|---|
| 정확도 (G1) | `ko_massive_domain_8` test half accuracy (보조: `ko_klue_ynat_7`) | LLM zero-shot baseline 대비 5 포인트 이내, baseline 없으면 절대 0.80 이상 | P1 | zero-shot **미달**: domain_8 test 0.492 [0.432, 0.552], ynat_7 test 0.655 (`results/B/summary_20261002.md`) → ft-v1 **통과**: test 0.900 [0.860, 0.936], 중복 제외 0.893, 전체 2,917행 0.913 (`results/P4/metrics/full_20261003-1156_summary.md`) |
| 선택적 자동화 (G2) | confidence 게이트 적용 후 coverage | 오류율 5% 이하에서 coverage 0.70 이상 (temperature refit 후). P0c에서 YNAT는 coverage 50%에서 정확도 0.86(오류 14%)이었으므로 달성이 어려울 수 있고, 그 경우 오류 예산을 10%로 바꿀지는 명시적 결정 사항이다(§열린 질문) | P3 | zero-shot **미달**: test coverage 0.224(오류 0.036, refit T 0.880). 상한 a/(1−e) = 0.518. 10%면 0.308, 15%면 0.400 (`results/E/E_summary_20261002.md`) → ft-v1 **통과(조건부)**: test 절반 5% 예산 사후 T 0.938에서 0.756, dev가 고른 T 0.892로는 오류 0.079(10% 예산 내); 전체 2,917행은 dev-1459가 고른 T 0.907로 test-1458 coverage 0.923, 오류 0.042 (`results/P4/metrics/full_20261003-1156_coverage_500.md`, `_coverage_2917.md`) |
| Calibration (G3) | ECE (answer_confidence, 15 bins) | refit 후 0.10 이하 | P3 | zero-shot **경계 통과**: test 0.263 → 0.098(pooled fit; per-task면 0.123) → ft-v1 **통과**: test 0.053, 2,917행 0.057(스크립트가 validation 400행으로 맞춘 T) |
| 견고성 (G4) | option-order flip rate (`router_v1`) | 0.10 이하 | P1 (Track C1 프로토콜) | zero-shot **미달**: 순열당 0.270 [0.230, 0.310], any-flip 0.512. confidence ≥ 0.9 결정만 보면 0.094 (`results/C/C1_option_order_20261002.md`) → ft-v1 **통과**: 순열당 0.037 [0.022, 0.057], any-flip 0.084 (`results/P4/metrics/full_20261003-1156_option_order_dev.md`) |
| Latency (in-process, G5) | 3-question call p95 (00 §6 기준; 1문항 router 호출은 더 쉬운 조건) | MPS 100 ms 이하, CPU 500 ms 이하 | Track D1 | **통과**(2026-10-03): multilingual 3q p95 MPS 22.6 ms(short) / 92.5(long 433 tok), CPU 10 threads 57.8 / 247.8 ms; 1q median MPS 13.8 / CPU 37.7 ms (`results/D/D_summary_20261003.md`) |
| Latency (HTTP, G6) | laya-serve p95 @ 10 RPS, MPS | 150 ms 이하 | Track D6 | **통과**(2026-10-03): 3문항 body 10 RPS p50 63.5 / p95 79.4 / p99 85.1 ms, 오류·503 0; 1문항 p95 57.3; CPU 서버 3문항 p95 135.8 (`results/D/20261003-1330_http_mps.json`) |
| 수치 일관성 (G7) | predict vs predict_batch(sort_by_length=True) | argmax flip 0, abs(delta p) 0.01 이하 | Track D4 | **통과**(2026-10-03, 정의대로 측정): CPU 64+256 states × bs 8/16/32 flip 0, max abs(delta p) 0.0001; MPS fp16 flip 0, 0.0081\~0.0085. 보조: P0 device parity 7/7, 0.0017 (`results/D/20261003-1314_batch.json`) |

기준 하나가 미달이어도 즉시 No-Go는 아니다. 정확도 미달은 P4(도메인 라우터 파인튜닝)로 가는 조건부 경로가 있고, G2 미달은 오류 예산 재합의 또는 fallback 비율 수용 여부의 문제이며, latency 미달은 배포 하드웨어 선택 문제로 분리해 판단한다(§8).

**판정(2026-10-02, zero-shot).** zero-shot 시나리오 C는 현재 스키마(router_v1)·체크포인트(multilingual)로 G1·G2·G4 미달이었다. 스키마 문구 변형 6종은 어느 것도 v1을 넘지 못했고(§4, `results/C/C_schema_v2_20261002.md`), 보정은 ECE만 고치고 coverage 상한은 바꾸지 못했다(§5). 프로젝트 책임자는 P4 파인튜닝을 택했다.

**판정(2026-10-03, 파인튜닝 ft-v1, 최종).** 파인튜닝 후 G1(0.900)·G3(0.053)·G4(0.037) 통과, G2는 전체 test 2,917행 기준 coverage 0.923(오류 0.042)으로 통과하되 250행 test 절반에서는 T 선택 방식에 민감(사후 T 0.756, dev T 적용 시 오류 0.079). Track D로 G5(3문항 p95 MPS 22.6 ms / CPU 57.8 ms)·G6(laya-serve 10 RPS 3문항 p95 79.4 ms)·G7(predict vs predict_batch(sort) flip 0, max abs(delta p) 0.0001) 통과. zero-shot은 G1/G2/G4 미달이므로 **판정 = Conditional Go(파인튜닝 파이프라인 전제)**. 조건과 운영 요건은 §6 P5, 수치는 `results/go_no_go.json`과 `results/REPORT.md`.

---

**Jev 대비 (2026-10-06, n=24 수동 비교).** 같은 24개 한국어 라우팅 항목에서 Jev(공개 플레이그라운드) 0.833, Laya zero-shot 0.417, ft-v1 0.917이다(`results/F/jev_playground_manual_20261006.md`). Jev는 Laya zero-shot을 확실히 앞서고(한국어 입력도 처리함), 파인튜닝한 ft-v1과는 이 표본에서 구분되지 않는다(Jev 0.833 vs ft-v1 0.917, p=0.5). 지연은 호스팅 Jev 표시값 249.5 ms vs 로컬 ft-v1 왕복 20.1 ms이며, 로컬 실행과 호스팅의 차이가 섞인 값이다.

## 2. 시나리오 선택

upstream이 제시한 production 패턴(출처: docs/use-cases.md §1, §3, §4, §6) 중 세 가지를 후보로 두고 비교했다. 표는 결정 전 비교 기록이다.

| 항목 | A. 한국어 CS triage + LLM gateway | B. LLM 프롬프트 가드레일 pre-filter | C. RAG 도메인 인덱스 라우터 |
|---|---|---|---|
| 핵심 결정 | intent / urgency / frustration / refund / churn + needs_llm | jailbreak / injection / sensitive_data / harm_severity | target_domain (N개 인덱스 중 하나) |
| 쓰이는 primitive | choice + score + noul 전부 | noul 위주 + score 하나 | choice 하나 |
| 측정 가능성 | 높음. 질문별 accuracy, ECE, coverage, flip rate 모두 측정 | 중간. 양성 샘플(공격 프롬프트) 한국어 데이터가 희소, false negative 비용 큼 | 가장 높음. 단일 choice라 지표가 단순 |
| 데이터 확보 | 직접 라벨링 `ko_poc_triage_v1.jsonl` (04 §5.8) + 프록시(MASSIVE ko intent, 3i4K speech act) | 영어 toxic-chat/prompt-injection은 있으나 한국어 공개셋 부족 | KLUE YNAT 7 토픽, MASSIVE 18 scenario가 바로 프록시 |
| upstream 근거 | triage preset 존재(출처: laya/presets.py `triage_questions`), 이메일/스팸 0.993 (출처: BENCHMARKS.md §Themes) | held-out guardrail 0.708-0.762, moderation 0.530 (출처: BENCHMARKS.md §Themes) | Air-gapped edge RAG router 패턴 (출처: docs/use-cases.md §4) |
| 리스크 | 한국어 zero-shot 정확도가 낮을 수 있음(MASSIVE ko 20-option 0.470) → P4 경로 | 정확도 자체가 production 기준 미달, shadow 신호로만 가능 | 비즈니스 텍스처가 적어 "도입 판단" 근거로 약함 |
| 재사용성 | 서비스·게이트·부하 테스트가 다른 스키마에 그대로 재사용 | 평가셋을 별도로 만들어야 함 | 스키마 파일만 바꾸면 A의 인프라 재사용 |

**당초 추천은 A였다.** 세 primitive와 multilingual 체크포인트, confidence gating, batch 경로, HTTP 서버를 전부 한 시나리오 안에서 검증할 수 있고 upstream preset이 직접적인 템플릿이라는 이유였다. 아래 P0 결과가 그 전제를 바꿨다.

**P0 결과 반영 (2026-10-02).** A의 zero-shot 경로는 n=30 프로브에서 intent 0.40\~0.50(변형별 최고 0.50, 4-class 환산 0.667)이고 이진 4문항은 always-no 기저 수준이라, 설계된 그대로의 A는 G1(00 §6)을 zero-shot으로 충족하지 못한다(`results/poc/P0_20261002.md`, `results/poc/P0b_20261002.md`). C 프록시는 KLUE YNAT 7토픽 n=100에서 0.65, confidence 상위 50% coverage에서 0.86(majority 0.15)이었고, MASSIVE 18도메인은 0.52에 play/music처럼 겹치는 도메인 정의에서 나온 확신 오답이 많았다(둘을 합치면 0.66, `results/poc/P0c_20261002.md`). 한국어 지원 감사(07 §5)에서는 같은 문장의 한국어 vs 영어 정확도 차이가 영어 key 옵션에서는 0.21\~0.24, 한국어 서술형 설명에서는 0.10(비유의)으로 줄었고, noul·score 약점은 영어 입력에서도 같아 체크포인트 성질로 확인됐다.

**결정: C (2026-10-02).** 근거는 넷이다. (1) A는 zero-shot으로 G1 미달이고 noul·score 약점이 한국어 문장 다듬기로 해결되지 않는다. (2) C 프록시는 7토픽에서 0.65, 게이트 적용 시 0.86으로 "1차 라우터 + fallback" 형태가 성립한다. (3) 한국어 서술형 설명을 쓰면 영어 대비 페널티가 작다(07 §5). (4) MASSIVE ko와 KLUE YNAT는 공개 ground truth가 있어 수작업 라벨링 병목이 사라진다. 과제는 둘이다. **주 과제**: MASSIVE ko 18 scenario를 겹치지 않는 8개 도메인으로 병합한 `ko_massive_domain_8`(test 2,974행, 같은 id의 영어 쌍으로 한국어 페널티 측정, upstream zh 6-domain voice routing 0.883과 비교 가능). **보조 과제**: KLUE YNAT 7개 뉴스 섹션(`ko_klue_ynat_7`, validation 9,107행, RAG 인덱스 라우팅 프록시). A는 보류한다: 스키마 파일(`triage_v1.json`, `gateway_v1.json`, `*_v1b.json`)은 P4 파인튜닝 후보로 `poc/schema/`에 남기고, 수작업 triage 세트(04 §5.8)는 P4를 결정한 뒤에만 만든다. 선택 사항으로 확정 taxonomy에 대한 수작업 "실제 질의" 세트 100건을 P1에 더할 수 있다(§열린 질문).

---

## 3. 아키텍처

```mermaid
graph TD
    C[클라이언트 / 백로그 워커] -->|POST /v1/systemone, /v1/systemone/batch| S[poc.service.app<br/>laya.serve.create_app(router)]
    UI[poc/service/ui<br/>Laya Playground 검토 화면] -->|POST /v1/systemone, /poc/decide · GET /poc/shadow, /poc/meta| S
    S --> R[Router preload=multilingual,english<br/>default=multilingual]
    R --> H1[RedactHook<br/>on_predict_start: PII 마스킹]
    H1 --> M{{forward pass<br/>1 question: domain (+ 선택 질문)}}
    M --> H2[ShadowAuditHook<br/>on_predict_end: poc/logs/shadow.jsonl]
    H2 --> H3[MetricsHook<br/>abstention / latency / fallback 카운터]
    H3 --> G[게이트 + 정책 레이어<br/>answer_confidence vs T]
    G -->|ROUTE: passed, p &ge; T| Q1[도메인 핸들러 / 인덱스<br/>productivity, media, smart_home, info_qa,<br/>communication, lifestyle, transport, general]
    G -->|FALLBACK: p &lt; T, abstained, unevaluated| L[LLM fallback 또는 사람 검수<br/>claude-haiku-4-5-20251001 또는 stub]
```

| 구성요소 | 역할 | 근거 / 비고 |
|---|---|---|
| `laya.serve.create_app(router)` | Jev 호환 `/v1/systemone`, `/v1/systemone/batch`, `/health` 제공. 추론은 단일 worker thread pool에서 직렬 실행 | 출처: laya/serve.py:685 `create_app`, :755-906 라우트, :1024 `main` |
| `Router(preload=..., default="multilingual")` | 한국어 채널 요청은 채널·로케일 메타데이터로 `predict(..., lang="ko")`를 고정하고, 메타데이터가 없을 때만 감지에 맡긴다. 순수 한글은 감지로도 multilingual로 가지만 라틴 다수 혼합문과 영어 래퍼 속 짧은 한국어는 english로 간다(07 §4). RedactHook이 추론 전 NFC 정규화도 수행한다(07 §3) | 출처: README.md "Quickstart: Route Mode", `07_korean_support_audit.md` §3-4 |
| RedactHook | 추론 전 `ctx.states` 재작성으로 전화번호·이메일·카드번호 마스킹 | 출처: README.md "Prediction Hooks", examples/hooks/redact.py |
| ShadowAuditHook | `on_predict_end`에서 run_id, model, routing, answers, probabilities, answer_confidence, elapsed_ms, checkpoint SHA, questions_sha256를 JSONL로 append | 출처: docs/staged-adoption.md §1 ShadowLog, examples/hooks/audit.py |
| MetricsHook | abstention 수, 503, fallback, latency 히스토그램 | 자체 구현 |
| 게이트·정책 레이어 | §5. laya 밖의 애플리케이션 책임 | 출처: docs/staged-adoption.md "Application/Laya boundary" |
| 데모 UI + `/poc/*` 라우트 | Laya Playground(jevplayground 구조): 예시 칩, 질문 빌더, 2단 입력/출력, 라우팅 결과 카드(ROUTE/FALLBACK), shadow 뷰. 검토용이며 액션을 실행하지 않음 | 자체 구현, laya-serve 라우트 옆에 마운트(아래 "데모 UI 라우트"). 출처: docs/staged-adoption.md §1 "A shadow logger must not turn logging into a new user-facing action" |

**hooks-over-HTTP 제약.** `laya-serve`는 요청 바디에 `hooks`, `on_predict_start`, `on_predict_end`, `hooks_raise`, `hooks_timeout`가 오면 422로 거절한다. hook은 callable이라 서버 프로세스 안에 살아야 하기 때문이다(출처: README.md "Self-Hosting: HTTP Server"). 따라서 hook은 서버 측에서 설치한다.

- **옵션 1 (채택)**: `laya.serve.create_app(router=...)`가 Router 주입을 지원한다(laya/serve.py:685, "Pass a Router to inject one"). `poc/service/app.py`에서 `Router(hooks=[...])`를 만들어 preload한 뒤 `create_app(router)`에 넘기고 uvicorn으로 띄운다. 라우트·인증·admission·토큰 예산 검증은 upstream 코드를 그대로 쓴다. `laya.serve.main()`이 끼우는 `TCP_NODELAY` 프로토콜 클래스(macOS Nagle 지연 회피, #620)는 우리가 uvicorn을 직접 호출하면 빠진다. P2 실측(2026-10-03, `results/poc/P2_20261003.md`)에서 NoDelay 없이도 HTTP 오버헤드가 p95 0.7 ms(왕복 p95 21.1 ms vs 서버 처리 20.4 ms)라 복제는 선택 사항이다.
- **옵션 2 (대안)**: 같은 `/v1/systemone` 계약을 우리 FastAPI 앱에 재구현. 옵션 1이 막힐 때(예: create_app 시그니처 변경)만 쓴다. 실행자는 착수 시 `third_party/laya/laya/serve.py`(upstream 클론, 공개 저장소에는 포함하지 않음. https://github.com/NandhaKishorM/laya 를 commit 4aa6761로 클론해 재현)에서 `create_app`의 시그니처를 다시 확인한다.
- **zero-code 경로**: P0-P2의 latency 측정처럼 hook이 필요 없는 구간은 그냥 `laya-serve`를 환경변수만으로 띄운다. 숫자 비교의 기준점(baseline)이 되므로 옵션 1 서버와 같은 요청으로 한 번은 반드시 측정한다.

```python
# poc/service/app.py (스케치)
import os
from laya import Router
from laya.serve import create_app                    # laya/serve.py:685
from poc.service.hooks import RedactHook, ShadowAuditHook, MetricsHook

CKPT_SHA = "3270d480..."   # ft-v1 rl_agent_config.json sha256(poc/finetune/ckpt_domain8_v1, base 55cf4c4). 기동 시 파일에서 재계산해 T를 정한 값과 다르면 중단(app.py:41)
QSHA = os.environ.get("POC_QUESTIONS_SHA256", "")             # router_v1.json의 questions_sha256 (기동 시 계산)

def build_router():
    # LAYA_MODELS는 laya-serve와 같은 의미(체크포인트 이름 목록); env.sh의 LAYA_MODELS_DIR와 다른 변수다(02 §2.8)
    names = [m.strip() for m in os.environ.get("LAYA_MODELS", "multilingual,english").split(",") if m.strip()]
    # 한국어 채널 요청은 predict(..., lang="ko")로 고정(07 §4). RedactHook은 마스킹 전에 unicodedata.normalize("NFC")를 적용(07 §3)
    router = Router(device=os.environ.get("LAYA_DEVICE", "mps"),
                    default=os.environ.get("LAYA_DEFAULT_MODEL", "multilingual"),
                    max_loaded=int(os.environ.get("LAYA_MAX_LOADED", "2")),
                    hooks=[RedactHook(),
                           ShadowAuditHook("poc/logs/shadow.jsonl", checkpoint_sha=CKPT_SHA, questions_sha256=QSHA),
                           MetricsHook()])
    router.preload(names)
    return router

app = create_app(router=build_router())
# 실행: uvicorn poc.service.app:app --host 127.0.0.1 --port 8000
# LAYA_API_KEY, LAYA_MAX_TOKEN_BUDGET, LAYA_ROOT_PATH 등은 create_app이 환경에서 직접 읽는다.
```

```python
# poc/service/hooks.py (스케치, 출처: docs/staged-adoption.md §1 ShadowLog 패턴)
# upstream examples/hooks/audit.py, redact.py는 함수형 hook(on_predict_end(ctx), redact(ctx))이다. 상태(경로, SHA)를
# 들고 있어야 하므로 여기서는 클래스로 감싼다. hook은 duck-typed라 둘 다 Router(hooks=[...])에 들어간다.
import json

class ShadowAuditHook:
    def __init__(self, path, checkpoint_sha, questions_sha256):
        self.path, self.sha, self.qsha = path, checkpoint_sha, questions_sha256
    def on_predict_end(self, ctx):
        rec = {"run_id": ctx.run_id, "model": ctx.model, "decision": getattr(ctx, "decision", None),
               "elapsed_ms": ctx.elapsed_ms, "error": None if ctx.error is None else repr(ctx.error),
               "results": ctx.results, "checkpoint_sha": self.sha, "questions_sha256": self.qsha}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
```

RedactHook은 `on_predict_start`에서 `ctx.states`를 마스킹된 복사본으로 교체한다. 마스킹 전 원문은 shadow 로그에도 남기지 않는다(§7).

**데모 UI 라우트.** `create_app(router)`가 돌려주는 객체는 보통의 FastAPI 앱이므로 upstream 라우트 옆에 우리 라우트를 그대로 덧붙인다. 라우트 네 개와 정적 자산 둘(`index.html`, `examples.json`)이 전부다.

| 라우트 | 요청 | 응답 | 비고 |
|---|---|---|---|
| `POST /poc/decide` | `{"utterance": str, "min_confidence": float \| null, "model": "auto" \| "multilingual" \| "english", "lang": "ko" \| null}` | `{"answers", "routing", "usage", "policy": {"action": "ROUTE" \| "FALLBACK", "domain", "handler", "p", "reason"}, "thresholds": {"T"}, "elapsed_ms", "checkpoint": {"path", "sha256_of_rl_agent_config", "base"}, "questions_sha256", "schema_version": "router_v1"}` (구현 기준, `poc/service/app.py:76`) | `router_v1.json`의 `domain` 질문 하나로 `router.predict(..., lang="ko")`를 호출하고 §5 `route(answers)`를 적용. `lang`은 기본 `"ko"`(한국어 채널, 07 §4), `null`이면 감지에 맡김. `model: "auto"`면 Router 라우팅, 아니면 `model=`로 pin. `LAYA_API_KEY`가 설정되면 laya-serve와 같은 bearer 검사(`laya.serve`의 검사 함수를 import할 수 있으면 재사용, 아니면 10줄짜리 동일 로직) |
| `GET /poc/shadow?limit=50` | 없음 | `{"records": [최근 N건], "counters": {"total", "abstained": {"count", "rate"}, "actions": {"ROUTE": n, "FALLBACK": n}, "by_domain": {domain: count}, "elapsed_ms": {"p50", "p95"}}}` | `poc/logs/shadow.jsonl`의 끝 N줄을 읽어 집계. 쓰기 없음 |
| `GET /poc/meta` | 없음 | `{"laya_version", "checkpoint": {"path", "sha256_of_rl_agent_config", "base"}, "questions_sha256", "schema_version": "router_v1", "thresholds": {"T"}, "models_loaded": [...]}` (`app.py:132`) | 서버 기동 시 계산한 값을 그대로 반환. UI 헤더 배지와 "문서와 상태" 섹션이 읽는다. run card의 SHA와 대조하는 용도 |
| `GET /poc/ui/` | 없음 | `poc/service/ui/index.html`, `poc/service/ui/examples.json` | 정적 마운트. 빌드 단계 없는 단일 HTML + vanilla JS + 인라인 CSS, 외부 의존 없음(시스템 폰트). `examples.json`은 예시(단일 5종 + 다중 4종)의 state·questions·설명·`state_key`를 담은 정적 파일이고 UI가 fetch한다. bearer 키는 입력 필드로 받아 `sessionStorage`에만 둔다 |

```python
# poc/service/app.py 에 이어서 (스케치)
import json, time
from fastapi import Body, Header
from fastapi.staticfiles import StaticFiles
from poc.service.policy import route, T, T_BY_DOMAIN

SCHEMA = json.load(open("poc/schema/router_v1.json"))["questions"]          # 1문항: domain

@app.post("/poc/decide")
def poc_decide(body: dict = Body(...), authorization: str | None = Header(default=None)):
    check_bearer(authorization)                                            # laya-serve와 같은 규칙
    model = None if body.get("model", "auto") == "auto" else body["model"]
    t0 = time.perf_counter()
    r = ROUTER.predict({"utterance": body["utterance"]}, SCHEMA, lang=body.get("lang", "ko"),
                       min_confidence=body.get("min_confidence"), model=model)   # 한국어 채널은 lang="ko" 고정(07 §4)
    action, detail = route(r["answers"])
    return {"answers": r["answers"], "routing": r["routing"], "usage": r["usage"],
            "policy": {"action": action, **detail},
            "thresholds": {"T": T}, "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
            "checkpoint": {"path": CKPT_DIR, "sha256_of_rl_agent_config": CKPT_SHA, "base": BASE_SHA},
            "questions_sha256": QSHA, "schema_version": "router_v1"}

app.mount("/poc/ui", StaticFiles(directory="poc/service/ui", html=True), name="poc-ui")
```

(`ROUTER`는 `build_router()`가 만든 인스턴스를 모듈 변수로 들고 있다는 전제. `/poc/shadow`는 같은 방식으로 `shadow.jsonl`을 읽어 집계만 한다.)

화면 구성(`poc/service/ui/index.html`, 이름 "Laya Playground"). 구조는 독립 제3자 Jev 플레이그라운드 https://jevplayground.com (2026-10-02 열람, 참고 스크린샷(공개 저장소에는 포함하지 않음) `docs/assets/reference/jevplayground_top_20261002.jpeg`, `jevplayground_full_20261002.jpeg`)을 따른다. laya-serve가 Jev와 같은 `POST /v1/systemone` 프로토콜을 제공하므로(출처: README.md "Self-Hosting: HTTP Server") 그 사이트가 Jev API를 호출하는 구조를 로컬 laya-serve로 옮기면 그대로 성립한다. upstream의 `examples/server.py` 플레이그라운드(02 §3.8)는 그대로 쓸 수 있지만 정책 카드·shadow 뷰·한국어 예시가 없으므로 PoC 검토는 이 페이지로 한다.

| 영역 | 구성 |
|---|---|
| 헤더 | 제목 "Laya Playground". 내비 Playground · PoC 라우터 · Shadow 로그 · 문서(00\~07 경로 문자열. 서버가 docs/를 서빙하지 않으므로 HTTP 링크가 아니라 복사용 경로) · 상태(`/health` 요약). 우측 배지 "로컬 실행 · laya 0.3.23 · 체크포인트 ft-v1 3270d480(base 55cf4c4)"(값은 `GET /poc/meta`의 `checkpoint`로 채움, 활성 체크포인트 기준) |
| 히어로 | eyebrow "ONE FORWARD PASS, CALIBRATED PROBABILITIES", 제목, 한 줄 설명(한국어), 배지 "✓ 로컬 체크포인트 / multilingual·english / 네트워크 없음" |
| 모드 토글 | **단일 질문 \| 다중 질문**. 단일 = 질문 빌더 1개. 다중 = 질문 목록(추가·삭제·순서 변경) + 프리셋 로드 |
| 예시 칩 | 원클릭 로드, 타입 배지, 로드 후 배너 "✓ 예시가 로드됨. 그대로 실행하거나 아무 필드나 수정하세요." 단일 5종: "도메인 라우팅 CHOICE"(PoC 정규 스키마 `router_v1.json`, state 예: "내일 아침 7시에 깨워줘", 8개 도메인 한국어 설명), "고객 문의 라우팅 CHOICE"(state 중복 결제 환불 요청 문장, 질문 "Which team should handle `message`?", 선택지 billing/technical/sales/other + 한국어 설명), "환불 요청 확인 NOUL"("Does the customer ask for money back?"), "장애 긴급도 SCORE"(4단계), "에이전트 다음 행동 CHOICE"(state 에이전트 관찰 JSON, 선택지 click/type/scroll/done). 다중 4종: "CS triage + gateway 7문항(보류 시나리오 A)"(`triage_v1.json` + `gateway_v1.json`, 예시 발화는 새로 쓴 문장. P0 프로브 문장은 재사용 금지 헤더가 있고 dev/test 구분도 없다), "이메일 분류"(`laya.presets.email_questions`), "프롬프트 가드레일"(`guard_questions`), "모델 라우터"(`router_questions`) (출처: laya/presets.py). 데이터는 `examples.json` |
| INPUT 패널(좌) | State textarea + 글자 수 카운터 "N자" + 실행 후 `usage.input_tokens` 표시(사전 토큰 추정은 하지 않음). state 형태 토글 **텍스트 \| JSON**과 `state_key` 입력란(기본 `message`. laya는 dict state를 받고 presets가 `message`/`body`/`prompt`/`post`/`request`를 백틱으로 지칭하므로 필드명이 맞아야 한다. 출처: laya/presets.py `state_field`). 질문 빌더: 질문 id(ASCII, 기본 `q1`), instructions, Decision type 세그먼트 **Choice \| Noul(Boolean) \| Score** + 설명 상자(choice "라벨 하나를 고르고 라벨별 확률을 돌려준다", noul "진술이 참일 확률 P(true)를 돌려준다. Jev의 Boolean에 대응", score "레벨 설명 목록에 대한 기대 레벨과 레벨별 확률을 돌려준다"). Choice 선택지 = 번호 칩 01.. 각각 **key(ASCII)** + **설명(한국어)** 두 칸(Jev는 라벨 한 칸이지만 laya의 criteria는 key→설명 구조이고 key가 모델이 읽는 옵션 텍스트다. 출처: README.md "Honest limits"), × 제거, "+ 선택지 추가", 카운터 "4 / 20", 20 초과 시 경고 배지 "head_max_len 예산 초과 가능(README Honest limits), 03 Track C6 참고"(서버 한도 100 초과는 413). Score = 레벨 설명 2\~7개(expected는 0-based 인덱스). Noul = true/false 설명 토글(기본 꺼짐 = v1 정책, 켜면 `criteria` 전송). 고급(접힘): 모델 auto/multilingual/english/typed-decisions, `min_confidence` 슬라이더 0.5\~0.95(기본 꺼짐, 켜면 abstention 배지 표시), `max_len`/`head_max_len`, `lang_guess`. 실행 버튼 "Run Laya ↗" + 보조 문구 "로컬 체크포인트에서 실행 · 네트워크 없음" + Ctrl+Enter(upstream `examples/server.py`와 같은 단축키. 출처: README.md "Try it locally: web GUI + JSON API") |
| OUTPUT 패널(우) | 라벨 "OUTPUT" + 배지(응답의 `routing.model`과 SHA). 빈 상태: 글리프 "[ · ]", "결정이 여기에 표시됩니다.", "state와 typed question을 주고 실행하면 결정과 확률이 보입니다.", 흐름 칩 "State + Question → Laya → Decision + Probability". 결과: PoC 모드(`router_v1` 예시 또는 "PoC 라우터" 내비)에서만 맨 위에 **라우팅 결과 카드**(ROUTE / FALLBACK, domain, handler, p, 적용 임계값 T, reason, `/poc/decide` 응답). 질문 카드(답 크게, `answer_confidence` 막대, `probabilities` 막대 목록(score는 `legend` 병기), `abstention` 배지 passed / abstained / unevaluated, noul은 P(true) 수치). 메타 행: 서버 `elapsed_ms`, 브라우저 round-trip ms, `usage.input_tokens`/`output_tokens`, `routing.reason`. 도구 버튼: "JSON 보기" 토글, "curl 복사", "Python 복사", "CLI 복사"(`laya "..." --questions FILE` 형태. 출처: README.md "Command line"). 오류 상태: "결정이 생성되지 않았습니다. 입력은 유지됩니다." + 서버 오류 본문(422/413/503 메시지 그대로, 503이면 `Retry-After` 표시). 푸터 "실제 로컬 모델 실행. 시뮬레이션 없음." |
| 하단 섹션 | **"PoC 시나리오로 시험하기"** 3카드: C 도메인 라우터(기본) → `router_v1.json` 로드 + 8도메인 예시 발화 8개 + YNAT 7토픽 질문(04 §5.2) 전환 토글, A CS triage + gateway(보류) → 7문항 로드 + 문구 "zero-shot G1 미달, P4 파인튜닝 후보(`results/poc/P0b_20261002.md`)", B 프롬프트 가드레일 → guard preset 로드 + 리스크 문구 "upstream held-out 가드레일 0.708\~0.762"(출처: BENCHMARKS.md §Themes). **"Shadow 로그"**: 테이블 최근 50건(시각, 발화 앞 40자, domain, `answer_confidence`, ROUTE/FALLBACK, `elapsed_ms`) + 카운터(abstention rate, ROUTE/FALLBACK 비율, 도메인 분포, `elapsed_ms` p50/p95), 5초마다 `GET /poc/shadow` 재조회. **"문서와 상태"**: 00\~07 경로 문자열(복사용), `/health` 요약, `/poc/meta`의 SHA·`questions_sha256`·`schema_version`. 푸터 "내부 PoC 검토 도구. 운영 배포 대상 아님. 액션을 실행하지 않음(docs/staged-adoption.md)" |
| 시각 톤 | jevplayground와 같은 밝은 배경, 흰 패널 + 얇은 회색 테두리, 모노스페이스 대문자 소제목(INPUT / OUTPUT / CHOOSE AN EXAMPLE), 파란 포인트 1색, 번호 칩. 단일 HTML + vanilla JS + 인라인 CSS, 외부 의존 없음. 900px 미만에서 1단 |

백엔드 매핑: 단일·다중 질문 일반 모드는 laya-serve의 `POST /v1/systemone`을 그대로 호출하고(요청 키 `state`, `questions`, `model`, `min_confidence`, `max_len`, `head_max_len`, `lang_guess`), PoC 모드만 `POST /poc/decide`(정책 포함)를 쓴다. 응답 키는 upstream 그대로 사용한다: `answers.<qid>.choice|score|noul`, `probabilities`, `legend`, `confidence`, `answer_confidence`, `abstention`, `usage`, `routing` (출처: laya/agent.py:1213-1244, README.md "Quickstart: Route Mode"). UI가 자체 계산하는 값은 브라우저 round-trip ms와 글자 수뿐이다.

Jev 플레이그라운드와의 차이:

| 항목 | jevplayground.com | Laya Playground |
|---|---|---|
| 이진 질문 | Boolean | noul, P(true) 수치와 0.5 기준 답 |
| 선택지 입력 | 라벨 1칸, 최대 10 | key(ASCII) + 한국어 설명 2칸, 20 권장(서버 한도 100, 초과 시 413) |
| 백엔드 | 호스팅 Jev API | 로컬 laya-serve `/v1/systemone`(같은 wire protocol) |
| 출력 | 결정 + 확률 | 결정 + 확률 + calibrated `answer_confidence` + `abstention` + `routing` + `usage` |
| 추가 화면 | 작업 데모 갤러리 9종 | 라우팅 결과 카드, shadow 로그, PoC 시나리오 3카드, 문서·상태 링크 |
| 인증 | 없음(사용량 제한) | `LAYA_API_KEY` bearer(설정 시) |

라벨 위생 규칙 두 가지. (1) UI로 입력한 문장도 shadow 로그에 남으므로 **test half 문장은 UI에 넣지 않는다.** P1의 "ablation은 dev half에서만" 규칙과 같은 이유(튜닝 누출 방지)다. (2) UI는 운영 화면이 아니라 PoC 검토 화면이다. 큐 배정이나 LLM 호출 같은 액션을 실행하지 않고 결정과 근거만 보여준다(출처: docs/staged-adoption.md §1 "A shadow logger must not turn logging into a new user-facing action").

---

---

## 4. 질문 스키마 v1 (router_v1)

스키마 파일은 `laya --questions`가 받는 `{"state_key": ..., "questions": {...}}` 형태로 두어 CLI 점검과 서비스가 같은 파일을 읽는다. instructions는 영어로 쓰고(upstream의 MASSIVE 벤치 구성과 presets가 모두 영어 instructions를 쓰는 관례. P0c와 07 §5에서 한국어 instructions는 효과가 없었다. 출처: research/scripts/bench_local.py:175-177, laya/presets.py, `results/poc/P0c_20261002.md`), criteria 설명은 한국어 서술형이다(P0c: 한국어 설명 0.52 vs key 렌더링 0.35, p<0.001). 문자열은 04 §5.1 (d)의 질문 dict와 byte-identical해야 하며, 정규 사본은 이 절의 `router_v1.json`이다.

### 4.1 `poc/schema/router_v1.json`

```json
{
  "state_key": "utterance",
  "questions": {
    "domain": {
      "type": "choice",
      "instructions": "Which domain should handle the request in `utterance`?",
      "criteria": {
        "productivity": "알람, 일정, 날짜와 시간, 할 일과 쇼핑 목록",
        "media": "음악, 라디오, 팟캐스트, 오디오북 재생과 음량 조절",
        "smart_home": "조명, 커피머신, 청소기, 플러그 등 스마트홈 기기 제어",
        "info_qa": "사실, 정의, 계산, 환율, 날씨, 뉴스 등 정보 질문",
        "communication": "이메일, 연락처, 소셜 미디어 게시와 확인",
        "lifestyle": "음식 주문과 배달, 요리법, 장소·이벤트·영화 추천",
        "transport": "교통, 택시, 티켓, 길 안내",
        "general": "인사, 잡담, 농담, 위 어디에도 속하지 않는 일반 대화"
      }
    }
  }
}
```

| 설계 항목 | 결정 | 근거 |
|---|---|---|
| 병합 규칙 | MASSIVE 18 scenario → 8 도메인: productivity ← alarm, calendar, datetime, lists / media ← music, play, audio / smart_home ← iot / info_qa ← qa, weather, news / communication ← email, social / lifestyle ← takeaway, cooking, recommendation / transport ← transport / general ← general | P0c 18도메인 오답의 대부분이 play↔music(14/17), audio→general, iot→alarm처럼 정의가 겹치거나 인접한 쌍에서 나왔고, play/music만 합쳐도 0.52 → 0.66이었다(`results/poc/P0c_20261002.md`). 8개는 핸들러 단위로도 자연스럽다 |
| 비중첩 검사 | 설명 어휘가 두 도메인에 겹치지 않는지 빌더가 토큰 집합 교집합을 출력(04 §5.1 (d)). 겹치면 설명을 고친 v2 파일 | 겹치는 어휘가 있는 옵션은 confidence 게이트로 걸러지지 않는 확신 오답을 만든다(P0c) |
| 설명 언어 | 한국어 서술형. 영어 설명 변형은 `--descriptions en` ablation으로만 | P0c −0.17(key 렌더링), 07 §5 영어 페널티 축소 |
| 옵션 순서 | 파일에 적힌 순서로 고정(production에서 섞지 않음). C1이 flip rate를 잰다 | option-order flip upstream 0.150/0.230, zh 10.6\~28% (BENCHMARKS.md) |
| 위치 편향 의심 | **기각(C1, 2026-10-02).** 첫 옵션 `productivity`는 과예측이 아니라 과소예측(원 순서 12건, 순열 평균 21.8건, gold 30)이고, smart_home 흡수(원 순서 66건, 순열 평균 58.6건, 맨 뒤로 옮긴 v2d에서도 60건)는 의미적이다. 위치 효과 자체는 있다(chi2 p=0.0009, 슬롯 1은 덜·2\~4는 더 뽑힘) | `results/C/C1_option_order_20261002.md`, `results/C/C_schema_v2_20261002.md` |
| v2 프로브 결과 | domain_8 dev 250행에서 v1 0.560 대비 설명 강화 v2a 0.536, general 제거 v2b 0.545, 예시 추가 v2c 0.540(옵션 토큰 418 > 한도 240이라 모두 30토큰으로 절단, head 512 진단 0.408), 순서 변경 v2d 0.516, 5클래스 v2e 0.536. **v1을 넘는 변형 없음.** 설명 문구로는 smart_home·general 흡수를 고칠 수 없다 | `results/C/C_schema_v2_20261002.md` |
| `general` | catch-all. ROUTE 대상으로 둘지 항상 FALLBACK으로 보낼지는 열린 질문. 기본은 ROUTE(chat 핸들러) | 잡담은 LLM 응답 경로와 겹침 |
| 옵션 수 | 8개는 head 토큰 예산(256) 안에 넉넉하다(옵션당 30 토큰) | README.md "Honest limits" 예산 규칙 |

**버전 규칙.** instructions나 criteria 한 글자라도 바꾸면 `questions_sha256`이 달라져 baseline과 비교 불가가 된다(출처: docs/evals.md "Run identity"). wording 변경은 `router_v2.json`처럼 새 파일로 만들고, run card(06 §1)에 파일명과 `questions_sha256`을 기록한다. 서비스는 기동 시 로드한 스키마 파일의 sha256을 `/poc/meta`와 shadow 로그에 함께 남긴다.

### 4.2 보류: 시나리오 A 스키마(파인튜닝 후보)

P0/P0b에서 zero-shot G1 미달로 보류됐다(§2). 파일은 `poc/schema/`에 그대로 두고 P4 파인튜닝 후보로만 쓴다. `triage_v1.json`은 아래 7문항 중 5문항(noul 3개는 presets처럼 criteria 없음), `gateway_v1.json`은 `needs_llm`·`complexity`다. `triage_v1b.json`·`gateway_v1b.json`은 noul에 `true`/`false` 한국어 criteria를 붙인 변형이며 Track C2 사다리의 "+criteria" 단이다. 04 §5.8의 수작업 세트는 P4를 결정한 뒤에만 만든다. P0b 조기 신호(n=30, `results/poc/P0b_20261002.md`): intent 최고 15/30(영어 설명, 4-class 환산 20/30), is_urgent는 한국어 instructions 26/30, churn_risk는 criteria 변형 28/30, refund_requested는 기준선 25/30(criteria는 과양성), frustration은 레벨 0 선택 0/30, needs_llm·complexity는 기저 수준. noul은 0.5 고정 임계값이 아니라 질문별 임계값이 필요하다(07 §5 E4, 03 E6).

`poc/schema/triage_v1.json`:

```json
{
  "state_key": "message",
  "questions": {
    "intent": {
      "type": "choice",
      "instructions": "What does the customer want in `message`?",
      "criteria": {
        "refund": "환불, 결제 취소, 중복 결제 환급을 요구",
        "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청",
        "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의",
        "information": "일반 정보, 가격, 사용 방법 문의",
        "cancellation": "해지, 탈퇴, 다운그레이드 요청",
        "other": "위 어느 것에도 해당하지 않음"
      }
    },
    "is_urgent": {
      "type": "noul",
      "instructions": "Does `message` communicate time pressure or a deadline?"
    },
    "frustration": {
      "type": "score",
      "instructions": "How frustrated does the customer sound in `message`?",
      "criteria": ["차분하고 중립적", "걱정하지만 정중함", "분명히 짜증남", "매우 화남 또는 강한 표현 사용"]
    },
    "refund_requested": {
      "type": "noul",
      "instructions": "Does the customer ask for money back?"
    },
    "churn_risk": {
      "type": "noul",
      "instructions": "Does `message` suggest the customer may leave for a competitor or cancel?"
    }
  }
}
```

`poc/schema/gateway_v1.json`:

```json
{
  "state_key": "message",
  "questions": {
    "needs_llm": {
      "type": "noul",
      "instructions": "Does answering `message` require a free-form generated reply rather than a templated action?"
    },
    "complexity": {
      "type": "choice",
      "instructions": "How complex is the request in `message`?",
      "criteria": {
        "canned": "인사, 표준 FAQ, 단순 상태 확인",
        "structured": "API나 템플릿으로 결정적으로 처리 가능한 요청",
        "complex": "생성형 답변, 다단계 추론, 복합 분석이 필요한 요청"
      }
    }
  }
}
```

---

## 5. 게이트와 정책

laya는 결정과 확률을 돌려줄 뿐 실행 권한을 주지 않는다. 임계값은 애플리케이션 정책이며 held-out 데이터에서 골라야 한다(출처: docs/staged-adoption.md §3). 게이트 설계는 다음 사실 위에 선다.

- `min_confidence`는 호출 단위 단일 임계값이다. 설정하면 모든 answer에 `abstention` 상태(`passed` / `abstained` / `unevaluated`)와 `abstention_threshold`가 붙고, 미달 answer는 `low_confidence: True`로 표시된다. 설정하지 않으면 응답은 바이트 단위로 기존과 같다(출처: README.md "Opt-in abstention").
- 게이트가 읽는 값은 `answer_confidence`(선택된 답의 확률, 옵션 수에 불변)이며 entropy 기반 `confidence`가 아니다. Jev에서 가져온 임계값은 이식되지 않는다.
- v1은 질문이 하나(`domain`)라 `min_confidence=T`로 abstention 보고를 켜고 정책 레이어는 같은 T로 ROUTE/FALLBACK을 결정한다. 도메인별 `T_BY_DOMAIN`은 **기각(E3, 2026-10-02)**: dev coverage는 0.180 → 0.316으로 올랐지만 test에서 5%·10% 예산을 모두 넘겨 검증에 실패했다(도메인당 dev 12\~66행 과적합). 단일 T는 pooled 보정 후 5% 예산에서 0.880이고, 그 T에서 `general`은 0/40이 route되어 사실상 항상 FALLBACK으로 동작한다(`results/E/E_summary_20261002.md`).
- 시나리오 A 보류 항목: noul의 결정 임계값은 0.5 고정이 아니라 질문별로 골라야 한다(AUROC 0.76\~0.92인데 p(true)가 0.5 아래로 눌림, 07 §5 E4). v1에는 noul이 없으므로 03 Track E6은 선택 항목이다.

```python
# poc/service/policy.py (스케치). T는 P3의 coverage 곡선으로 확정하고 ADR에 기록한다.
T = 0.907                      # answer_confidence 게이트. ft-v1 기준: 2,917행 dev-1459에서 오류 5% 이하 최대 coverage 지점, test-1458 적용 시 coverage 0.923·오류 0.042 (results/P4/metrics/full_20261003-1156_coverage_2917.md). zero-shot 시절 값은 0.880(E3)
T_BY_DOMAIN = {}               # 기각됨(E3 과적합). 코드 경로만 남기고 비워 둔다
HANDLER = {"productivity": "calendar-svc", "media": "media-svc", "smart_home": "iot-svc", "info_qa": "qa-svc",
           "communication": "comm-svc", "lifestyle": "lifestyle-svc", "transport": "transport-svc", "general": "chat-svc"}

def route(answers):
    d = answers["domain"]
    p, top = d["answer_confidence"], d["choice"]
    if d.get("abstention") not in (None, "passed"):           # abstained / unevaluated (min_confidence가 켜진 경우)
        return "FALLBACK", {"domain": top, "handler": None, "p": p, "reason": d["abstention"]}
    if p < T_BY_DOMAIN.get(top, T):
        return "FALLBACK", {"domain": top, "handler": None, "p": p, "reason": "below T"}
    return "ROUTE", {"domain": top, "handler": HANDLER[top], "p": p, "reason": "passed"}
```

| 상태 / 규칙 | 처리 | 이유 |
|---|---|---|
| `abstention == "unevaluated"` | FALLBACK | 게이트가 판단 불가(NaN, confidence 없음)인 경우를 pass로 읽지 않기 위함 |
| `abstention == "abstained"` 또는 `p < T` | FALLBACK, abstention 카운터 증가 | coverage 지표의 분모·분자. fallback은 LLM 응답 또는 사람 검수(배포 형태에 따라) |
| `passed`이고 `p >= T` | ROUTE: 도메인 핸들러(또는 인덱스)로 전달 | P3에서 합의한 오류 예산 안의 구간만 |
| `general` | 기본 ROUTE(chat 핸들러). 항상 FALLBACK으로 보낼지는 열린 질문 | 잡담은 LLM 경로와 겹침 |

**T 선정(P3).** dev half에서 answer_confidence 내림차순 coverage 대비 accuracy 곡선을 그리고, 합의한 오류율(기본 5%, §열린 질문) 이하를 만족하는 최대 coverage 지점의 confidence를 T로 잡는다. test half에서 같은 T로 coverage와 오류율을 재검증한다. T는 체크포인트 SHA, `questions_sha256`, calibration 파일 sha와 함께 ADR(06 §3)에 기록하며, 이 넷 중 하나가 바뀌면 T는 무효다.

**Batch 경로.** 백로그 라우팅은 `/v1/systemone/batch`(states 최대 64개, forward pass 공유)로 보낸다. 질문이 하나라 `min_confidence` 하나로 충분하다. 답의 수치 일관성(predict vs predict_batch)은 P2에서 parity 게이트로 확인한다.

**LLM fallback.** FALLBACK 중 즉시 응답이 필요한 채널에서는 `claude-haiku-4-5-20251001`을 호출한다. API 키가 없으면 stub(고정 응답 + 지연 시뮬레이션)으로 대체하고, 비용 논거는 호출 횟수 절감률(ROUTE 비율 × 정확도)로 계산한다.

---

## 6. 단계별 계획 [단계 → 검증]

shadow → compare → policy → bounded promotion(출처: docs/staged-adoption.md)에 P0-P5를 대응시킨다. P0-P1이 compare 전 준비, P2가 shadow, P3가 policy, P5가 promotion 판단이다. 모든 run은 06 §1 run card를 남긴다.

### P0. 스모크 (완료, 2026-10-02)

시나리오 A 스키마(7문항)로 수행했고 결과는 시나리오와 무관하게 유효하다(`results/poc/P0_20261002.md`): 스키마 파일 byte 일치, MPS/CPU argmax 7/7 일치(max abs Δp 0.0017), 7문항 호출 중앙값 MPS 74 ms / CPU 146 ms(10스레드, inter-op 1), 첫 MPS 호출 0.17 s. `router_v1.json`에 대해서는 P1 첫 실행 때 같은 parity 점검을 1문항으로 한 번 더 한다(아래 P1 6번).

### P1. 공개 라벨 평가 + 체크포인트 선택 (1일, 라벨링 없음)

1. `poc/schema/router_v1.json` 작성(§4.1 그대로) → `python -c 'import json; json.load(open("poc/schema/router_v1.json"))'`, `questions_sha256` 계산(04 §6 규약, `laya.evals.questions_fingerprint`).
2. 평가셋 빌드(04 §6 빌더, 네트워크 필요):

```bash
source env.sh && unset HF_HUB_OFFLINE
.venv/bin/python scripts/build_ko_evalsets.py massive --lang ko --mode domain --n 500     # ko_massive_domain_8.jsonl
.venv/bin/python scripts/build_ko_evalsets.py massive --lang en --mode domain --n 500     # en_massive_domain_8.jsonl (같은 id)
.venv/bin/python scripts/build_ko_evalsets.py massive --lang ko --mode scenario            # ko_massive_scenario_18.jsonl (비교용)
.venv/bin/python scripts/build_ko_evalsets.py ynat --n 500                                 # ko_klue_ynat_7.jsonl
.venv/bin/python scripts/build_ko_evalsets.py manifest
```

   빌더는 `ko_massive_domain_8.jsonl`의 `domain` 질문 dict가 `router_v1.json`의 것과 byte 일치함을 assert한다.
3. dev/test 분할은 `results/B/B_splits.json`(03 §3.2)을 쓴다: 쌍 MASSIVE 세트(ko/en domain_8)는 행 index parity(짝수 dev, 홀수 test), 나머지 세트는 state 해시 홀짝. test half는 동결된 스키마 버전마다 **한 번만** 채점한다(P1에서 G1 수치를 내고 P5 리포트는 그 수치를 재사용). instructions·설명 언어 ablation(`_ko-instr`, `_en-desc`)과 wording 변경은 dev half 수치로만 비교한다.
4. 세 체크포인트 + Router auto로 평가(Track B 명령과 동일, 03 §7 B1):

```bash
D=$(date +%Y%m%d)
ts=$(date +%Y%m%d-%H%M)
for set in ko_massive_domain_8 ko_klue_ynat_7 ko_massive_scenario_18; do
  for m in multilingual english typed-decisions; do
    laya-evals run data/evals/$set.jsonl --model $m --device cpu --batch-size 16 --slice qid --slice tag \
      --json results/B/${ts}_${m}_${set}.json --markdown results/B/${ts}_${m}_${set}.md
  done
  laya-evals run data/evals/$set.jsonl --device cpu --batch-size 16 --slice model --slice qid --slice tag \
    --json results/B/${ts}_router_${set}.json --markdown results/B/${ts}_router_${set}.md
done
laya-evals run data/evals/en_massive_domain_8.jsonl --model multilingual --device cpu --batch-size 16 --slice qid --slice tag \
  --json results/B/${ts}_multilingual_en_massive_domain_8.json       # 한국어 페널티: 같은 id의 영어 쌍 (07 §5)
python scripts/metrics_extra.py summary results/B/${ts}_*_ko_massive_domain_8.json --split-rule index --out results/B/metrics/domain_8.md
python scripts/metrics_extra.py paired results/B/${ts}_multilingual_ko_massive_domain_8.json \
  results/B/${ts}_multilingual_en_massive_domain_8.json              # 쌍 McNemar, ko vs en
```

5. 비교군: majority class(MANIFEST `majority_rate`), (선택) LLM zero-shot baseline(Track F 프로토콜, 같은 state·같은 8 옵션·같은 한국어 설명), 참고치 upstream zh 6-domain 0.883(BENCHMARKS.md §Community evaluation).
6. parity: `ko_massive_domain_8` dev half 50건을 `--device mps`로 한 번 더 돌려 CPU 리포트와 argmax 비교(1문항 호출은 MPS에서도 fp32라 flip 0이어야 함, 02 §4).
7. wording 변경은 dev half 결과로만, 최대 2라운드, 새 파일(`router_v2.json`)과 새 run card. test half는 동결된 버전마다 1회만 평가한다. 참고: `router_v1.json`은 현재 `results/C/schemas_v2/router_v1.json`에만 있고 `poc/schema/router_v1.json`은 P2에서 그 파일을 복사해 만든다(`questions_sha256` a7f2f6b8…, `data/evals/MANIFEST.json`과 일치해야 함).

검증: (1) test half `ko_massive_domain_8` accuracy(bootstrap 95% CI)와 macro-F1이 기록되고 §1 G1 기준과 비교됨 (2) 체크포인트 선택 근거가 기록됨(기대: multilingual 우세, H2) (3) 한국어 페널티(ko vs en, 같은 id)가 07 §5의 0.10 수준인지 (4) MPS parity flip 0 (5) G1 미달이면 P4 진입 여부를 ADR로 남기고 P2-P3는 계속 진행한다(latency·운영 검증은 정확도와 독립).

**P1 결과(2026-10-02, Track B로 수행, `results/B/summary_20261002.md`, `results/B/B_20261002.md`).** (1) domain_8 test 0.492 [0.432, 0.552], macro-F1 0.468, G1 **미달**; ynat_7 test 0.655. (2) multilingual 고정 + `lang="ko"` 선택(english 0.276, typed-decisions 0.288, Router는 한국어에서 답 동일). (3) 페널티 없음(ko 0.526 vs en 0.510, p=0.47). (4) parity는 P0에서 확인. (5) P4 진입은 프로젝트 책임자 결정 대기(§열린 질문). 실패 패턴: smart_home 예측 140(gold 63), general 80(gold 62), audio→smart_home 9/9, calendar→smart_home 14/36, weather·news·social 각 ≈2/18 정답.

### P2. 서비스화 + 부하 측정 (1-2일)

```bash
# zero-code baseline (stock laya-serve: LAYA_MODELS는 체크포인트 "이름" 목록이라 Hub base만 올릴 수 있고 ft-v1은 못 올린다)
LAYA_DEVICE=mps LAYA_PRELOAD=1 LAYA_MODELS=multilingual,english LAYA_DEFAULT_MODEL=multilingual \
LAYA_MAX_LOADED=2 LAYA_THREADS=10 LAYA_API_KEY=devkey LAYA_HOST=127.0.0.1 laya-serve
# hooks 포함 서버 (옵션 1). app.py가 Router(models={"multilingual": "poc/finetune/ckpt_domain8_v1", "english": "models/laya"})를
# 직접 만들므로 LAYA_MODELS는 읽지 않는다(그 변수는 stock laya-serve 전용). multilingual 자리에 ft-v1이 올라가고 english는 첫 요청 때 로드
LAYA_DEVICE=mps LAYA_API_KEY=devkey LAYA_HOST=127.0.0.1 .venv/bin/uvicorn poc.service.app:app --host 127.0.0.1 --port 8000
curl -s localhost:8000/health -H 'Authorization: Bearer devkey'    # 0.3.23: 키 설정 시 내부 상태는 bearer 필요
curl -s localhost:8000/v1/systemone -H 'Authorization: Bearer devkey' -H 'content-type: application/json' \
  -d @poc/loadtest/req_router1.json | python -m json.tool
curl -s localhost:8000/v1/systemone/batch -H 'Authorization: Bearer devkey' -H 'content-type: application/json' \
  -d @poc/loadtest/req_batch16.json | python -c 'import json,sys; r=json.load(sys.stdin); print(len(r["results"]), r["total_usage"])'
```

`poc/loadtest/req_router1.json`은 `state: {"utterance": ...}`, `router_v1.json`의 `questions`, `lang: "ko"`, `min_confidence: 0.8`, `model: "multilingual"`을 담는다. `req_batch16.json`은 `states` 16개와 같은 `questions`, `batch_size: 8`, `sort_by_length: true`.

```json
{
  "state": {"utterance": "내일 아침 7시에 깨워줘"},
  "questions": {"domain": {"type": "choice", "instructions": "Which domain should handle the request in `utterance`?",
                           "criteria": {"productivity": "알람, 일정, 날짜와 시간, 할 일과 쇼핑 목록", "media": "음악, 라디오, 팟캐스트, 오디오북 재생과 음량 조절", "smart_home": "조명, 커피머신, 청소기, 플러그 등 스마트홈 기기 제어", "info_qa": "사실, 정의, 계산, 환율, 날씨, 뉴스 등 정보 질문", "communication": "이메일, 연락처, 소셜 미디어 게시와 확인", "lifestyle": "음식 주문과 배달, 요리법, 장소·이벤트·영화 추천", "transport": "교통, 택시, 티켓, 길 안내", "general": "인사, 잡담, 농담, 위 어디에도 속하지 않는 일반 대화"}}},
  "lang": "ko",
  "min_confidence": 0.8,
  "model": "multilingual"
}
```

부하 측정은 `scripts/bench_http_local.py`(03 D6 인터페이스 기준)로 1문항 바디로:

- closed-loop concurrency 1 / 4 / 8, 60초, p50/p95, 503 비율, `Retry-After` 관찰
- open-loop 5 / 10 / 20 RPS, 60초, p50/p95, 큐잉으로 인한 p95 폭주 지점
- 같은 요청을 `LAYA_DEVICE=cpu LAYA_THREADS=10`으로 반복(Linux CPU 배포 프록시), ONNX int8 export는 Track D7 결과를 인용
- 서버 RSS(2 체크포인트 preload), 콜드 로드 시간, 첫 MPS 호출 지연

검증: (1) 1문항 p95 150 ms 이하 @ 10 RPS MPS(00 §6) (2) `/v1/systemone/batch` 16 states의 답과 단건 16회 답의 argmax 일치 0 flip, abs(delta p) 0.01 이하 (3) shadow.jsonl 레코드에 run_id, model, checkpoint_sha, questions_sha256, elapsed_ms, 라우팅 결과(ROUTE/FALLBACK, domain)가 모두 있고 원문 PII가 없다 (4) `routing.reason`이 `explicit lang='ko'` 계열인지(감지가 아니라 고정 라우팅) (5) 503이 났다면 어떤 RPS부터인지와 `Retry-After` 값.

#### P2-UI. 데모 UI [단계 → 검증] (0.5일, P2 서버 기동 이후)

§3 "데모 UI 라우트"의 네 라우트와 `poc/service/ui/index.html`, `examples.json`을 붙여, 브라우저에서 PoC 결정을 직접 확인할 수 있게 한다. 부하 측정이 아니라 기능 확인이므로 수치 기준은 argmax 일치만이다.

```bash
# 1. poc/service/ui/index.html + examples.json 작성 (단일 HTML + vanilla JS, 빌드 없음, §3 화면 구성 표대로)
# 2. 옵션 1 서버 기동 (P2와 동일; LAYA_MODELS는 app.py가 읽지 않음) 후 브라우저로 연다
LAYA_DEVICE=mps LAYA_API_KEY=devkey LAYA_HOST=127.0.0.1 .venv/bin/uvicorn poc.service.app:app --host 127.0.0.1 --port 8000
open http://127.0.0.1:8000/poc/ui/
# 3. 단일 질문 예시 5종(router_v1 포함) + 다중 질문 예시 4종을 전부 실행 (예시 발화는 dev half에서만). 하나는 Ctrl+Enter로 실행
# 4. ft-v1 대조는 in-process(CPU, laya.load("poc/finetune/ckpt_domain8_v1")) vs 서버(MPS) 답 비교로 한다(results/poc/P2_acceptance.py).
#    아래 CLI 줄은 `--model ml`이 Hub base 체크포인트를 쓰므로 ft-v1과 비교할 수 없고, base 동작의 sanity 확인용일 뿐이다(cli.py:147-148)
laya "<UI에 넣은 발화>" --model ml --lang ko --questions poc/schema/router_v1.json --json
# 5. 하단 shadow 테이블과 카운터가 5초 안에 갱신되는지 확인
# 6. 인증: 키 없이 호출 → 거절, 키 입력 후 → 정상
curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:8000/poc/decide -H 'content-type: application/json' -d '{"utterance":"내일 아침 7시에 깨워줘"}'
curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:8000/poc/decide -H 'Authorization: Bearer devkey' -H 'content-type: application/json' -d '{"utterance":"내일 아침 7시에 깨워줘"}'
# 7. 경계 동작: 선택지를 21개 입력해 경고 배지, 서버를 내린 뒤 실행해 오류 상태 문구와 입력 유지, 창 폭 900px 미만에서 1단 렌더
# 8. 메타 대조
curl -s localhost:8000/poc/meta -H 'Authorization: Bearer devkey' | python -m json.tool   # checkpoint_sha, questions_sha256을 run card와 비교
```

검증: (1) 단일 5종 + 다중 4종 예시가 모두 응답하고, router_v1 예시에는 라우팅 결과 카드에 ROUTE 또는 FALLBACK이 찍힌다 (2) `domain` argmax가 in-process ft-v1(CPU) 결과 및 "curl 복사" 재실행 결과와 일치한다(CLI `--model ml`은 base 체크포인트라 대조 대상이 아님) (3) `min_confidence` 슬라이더를 움직이면 `abstention` 배지가 passed / abstained 사이에서 바뀐다 (4) shadow 레코드에 PII 원문이 없다(RedactHook 적용 후 텍스트만) (5) 브라우저 round-trip과 서버 `elapsed_ms`의 차이가 로컬에서 수십 ms 이내다 (6) `LAYA_API_KEY` 설정 상태에서 키 없는 호출은 401 또는 403, 키를 넣으면 200 (7) 선택지 21개에서 경고 배지가 뜨고 Ctrl+Enter로 실행된다 (8) 서버가 내려간 상태에서 실행하면 "결정이 생성되지 않았습니다. 입력은 유지됩니다." 문구가 보이고 입력이 지워지지 않는다 (9) `GET /poc/meta`의 `checkpoint_sha`·`questions_sha256`이 run card 값과 같다 (10) 900px 미만 폭에서 1단으로 렌더된다. 결과는 `results/poc/P2_ui_check.md`에 체크리스트로, 화면은 `results/poc/P2_ui_*.png` 스크린샷으로 남긴다.

**P2 결과 (2026-10-03, `results/poc/P2_20261003.md`, UI 체크리스트 `results/poc/P2_ui_check.md`).**

| 항목 | 결과 |
|---|---|
| 구현 파일 | `poc/service/app.py`(142줄: Router 구성 :48-60, 기동 시 SHA·questions_sha256 검증 :41, bearer :67, `/poc/decide` :76, `/poc/shadow` :113, `/poc/meta` :132, 정적 마운트 :142), `hooks.py`(123줄: NFC+PII 마스킹 :17-36·:50, shadow JSONL :55-94, 카운터 :97), `policy.py`(31줄, T :4, ROUTE/FALLBACK :20-31), `ui/index.html`(1,050줄), `ui/examples.json`(391줄), `poc/schema/router_v1.json`(원본과 byte 동일) |
| 체크포인트 | ft-v1(`poc/finetune/ckpt_domain8_v1`, 공개 저장소에는 포함하지 않음)을 `multilingual` 자리에, english는 지연 로드. `ko_v1.json` 보정은 적용하지 않음(ft-v1은 자체 T 보유) |
| 정책 T | 0.907 (2,917행 dev-1459 기준, test-1458 coverage 0.923·오류 0.042). abstained·unevaluated·비ft-v1 체크포인트 답은 FALLBACK |
| 인증 | 키 없음 401, 틀린 키 401, 키 있음 200. `/health`는 키 없이 liveness만 |
| `/poc/meta` 대조 | questions_sha256 a7f2f6b8…, rl_agent_config sha 3270d480…, weights sha b0609f54… 모두 P4 리포트·MANIFEST와 일치 |
| 8도메인 예시 + 문서 예시 | 9/9 ROUTE, 정답 도메인 9/9, p 0.924\~0.957, `routing.reason` = explicit lang='ko' |
| FALLBACK | 무의미 문자열 p 0.222, 다중 의도 p 0.669 → FALLBACK. `min_confidence` 1.0 → abstained, 0.5 → passed이나 T 미만 → FALLBACK |
| PII | shadow에 `[email]`, `[phone]`, `[card]`로만 기록, 원문 0건 |
| 일반 모드 | `/v1/systemone` 3지선다 200, technical 0.985 |
| shadow 카운터 | 50줄 = total, ROUTE 44 + FALLBACK 5 = 도메인별 합 |
| in-process 대조 | CPU ft-v1 vs 서버 MPS: 9개 중 다른 답 0, 확률 차 최대 0.0000 |
| 브라우저 점검 | 05 §6 10개 항목 + 5초 갱신 모두 ✔ (예시 10종, Ctrl+Enter, curl·Python 복사 재실행 동일, 슬라이더 passed↔abstained, 21개 선택지 경고, 서버 다운 시 오류 문구와 입력 유지, 820px 1단). 스크린샷 `results/poc/P2_ui_1.png`(빈 상태) \~ `P2_ui_8_server_down.png` |
| `/poc/decide` 왕복 (1문항, 30회 연속) | p50 20.1 / p95 21.1 ms (서버 처리 p50 19.5 / p95 20.4, HTTP 오버헤드 p95 0.7 ms) |

주의. (1) 브라우저에서 몇 초 간격으로 누르면 서버 처리 44\~51 ms로 늘어난다. Track D의 간헐 호출 페널티(D1c, `results/D/D_summary_20261003.md`)와 같은 현상이다. (2) 예시 9개의 p가 0.92\~0.96에 몰려 T 0.907까지 여유가 0.017\~0.05뿐이라 문구나 정밀도가 조금만 바뀌어도 ROUTE/FALLBACK이 뒤집힐 수 있다. (3) 프리셋 같은 일반 모드 질문도 `multilingual` 자리의 ft-v1이 답하며 그 품질은 측정하지 않았다. (4) `min_confidence: null`은 생략과 같이 T로 처리하고, `/poc/decide`는 `model`(auto·multilingual·english)도 받는다. (5) 이번 범위 밖: 부하 측정(Track D6가 base 체크포인트로 수행, 같은 구조라 레이턴시 동일)과 503·Retry-After, 선택지 101개 초과 413의 UI 재현, 시각 톤·실기기 확인.


### P3. 캘리브레이션 + 임계값 정책 (1일)

multilingual 체크포인트는 fitted temperature가 없이 출하되며 refit이 ECE 0.314 → 0.106으로 가장 효과 큰 수정이다(출처: BENCHMARKS.md §Calibration). `laya.calibrate`의 per-bucket 하한은 `MIN_BUCKET_N = 2000`, type-level 하한은 `MIN_TYPE_N = 10`이므로(출처: laya/calibrate.py 모듈 docstring) PoC 규모에서는 **type-level temperature(choice 1개)**만 현실적이다. `--n 0`(2,917행)으로 빌드해도 dev 절반은 약 1,460행이라 버킷 하한 2,000에 못 미친다(calibrate.py:178). 저floor 버킷 fit(`--min-bucket-n 100`)은 레코드가 한 버킷(choice:6-10)뿐이라 type 스칼라와 같은 값이 된다.

```bash
python scripts/calibrate_ko.py --model models/laya-multilingual --device cpu \
  --sets data/evals/ko_massive_domain_8.jsonl,data/evals/ko_klue_ynat_7.jsonl \
  --splits results/B/B_splits.json --pooled --per-task --min-bucket-n 100 \
  --out-payload poc/calibration/ko_v1.json --out results/E/$(date +%Y%m%d-%H%M)_calibration_multilingual.json
# coverage 곡선(보정 전/후), 예산별 T, 도메인별 T 검증은 위 스크립트가 함께 계산한다. metrics_extra coverage는 리포트의 반올림 확률로 보정 전 곡선만 낸다.
```

주의: `records_from_labeled`는 `@torch.no_grad()`가 없어 실제 Agent로 부르면 grad 텐서 오류가 난다(upstream 결함, laya/calibrate.py:286 → agent.py:1177). `scripts/calibrate_ko.py:93`이 `torch.no_grad()`로 감싼다(03 E2).

- `records_from_labeled(agent, pairs)` → `fit_temperature_map(records, compute_ece=True)` → `calibration_payload(...)`로 `poc/calibration/ko_v1.json` 생성. pooled(domain_8 + ynat_7) vs per-task fit을 held-out에 교차 적용해 전이성을 본다(03 E2).
- 적용 경로: `laya.load(path, calibration="poc/calibration/ko_v1.json")`로 agent를 만들고 `router.attach("multilingual", agent)`로 Router에 붙인다. `Router` 생성자에는 calibration 인자가 없고, `laya-evals --calibration`은 ONNX 경로에만 적용되므로(출처: docs/evals.md "Evaluating an ONNX export") torch 경로의 평가는 우리 서비스 코드 또는 `apply_calibration_payload`로 한다.
- dev half에서 단일 T 선정(도메인별 T는 E3에서 과적합으로 기각) → test half에서 ECE, coverage, 오류율 재측정 → ADR 작성(체크포인트 SHA 55cf4c4, `questions_sha256`, calibration sha256, T, dataset sha256, owner, 날짜). payload 형태(type 스칼라 vs `{"choice:6-10": T}` 한정)도 ADR 항목이다.
- 03 Track E6(noul 결정 임계값)은 v1에 noul이 없으므로 선택 항목이다. 2026-10-02에 NSMC noul로 한 번 수행했다: AUROC test 0.822, dev Youden 임계값 p(true) ≥ 0.0073, test 정확도 0.725(0.5 기준 0.641, 2-choice 0.773). A를 P4로 살릴 때의 근거다.

**P3 결과(2026-10-02, Track E로 수행, `results/E/E_summary_20261002.md`).** pooled T 1.9161(domain_8 2.0245, ynat 1.8149; choice:6-10, clamp 없음). test ECE domain_8 0.263 → 0.098, ynat 0.148 → 0.063 → G3 경계 통과. 5% 예산 T 0.880 → test coverage 0.224(오류 0.036) → G2 **미달**(상한 0.518). 10% 0.308, 15% 0.400. payload `poc/calibration/ko_v1.json`(pooled, [1.9161, 1, 1], sha256 a217cb5d…) 적용 검증 완료(재채점 ECE 0.0980, 답 250/250 동일).

검증: test half에서 ECE 0.10 이하이고, 합의한 오류 예산(기본 5%) 이하 구간의 coverage 0.70 이상(00 §6). 미달이면 (a) 오류 예산 10%에서의 coverage를 함께 보고하고 (b) 어느 도메인이 끌어내리는지(tag slice `scenario:*`) (c) "그 도메인은 항상 FALLBACK" 대안을 ADR에 기록한다.

### P4. 파인튜닝 (완료, 2026-10-02 결정 → 2026-10-03 본 학습)

upstream 증거: typed-decisions zero-shot 0.362 → 파인튜닝 0.766, browser-agent 0.10 → 0.66 (출처: README.md "Fine-Tuning", docs/finetune_browser_agent.md). 2xT4에서 30k 질문 4 epoch에 4-5시간이 걸렸다. 이 머신의 소요는 아래 프로브로 측정했다(`results/P4/P4_probe_20261002.md`).

**스크립트 사실 확인(`third_party/laya/notebooks/laya_finetune_typed_decisions_mps.py`, upstream 클론으로 공개 저장소에는 포함하지 않음, 수정 없이 사용).**
- 아이템: `build_training_item(tokenizer, cfg, state, question, gold_question)`(:58-100). gold 형식은 choice `{"probabilities": {<criteria key>: p}}`(인덱스가 아니라 key), noul `"true"`/`"false"` key, score `"0".."n-1"` key다. 우리 `expected`는 `{key: 1.0}`으로 1:1 매핑된다. 시퀀스는 `build_sequence`로 옵션을 **canonical 순서 그대로** 만들며 옵션 순서 증강은 없다.
- 학습: fp32, autocast 없음. AdamW(encoder 2.5e-5, head 1e-4, wd 0.01), cosine으로 1e-6까지, warmup 없음, grad clip 1.0. loss = RLCD(σ 0.4 → 0.1 annealing, 4 sample, `proper_reward` w_sph 0.75) + soft CE. 기본값 micro-batch 2 × grad-accum 16, epochs 4. gradient checkpointing은 encoder·head 모두 기본 켜짐(`--no-checkpointing`으로 끔). seed 없음, early stopping 없음, `checkpoint_latest/`를 epoch마다 덮어쓴다.
- calibration: 같은 items 파일에서 `min(--calib-max, N//10)`개를 `random.Random(20260922)`로 위치 기준 분리해 type별 LBFGS로 T를 맞춘다. 우리 어댑터는 validation 행을 그 위치에 미리 놓아 train 행이 calibration에 들어가지 않게 한다.
- export: fp16 `model.safetensors`, `encoder/`, `tokenizer/`, `rl_agent_config.json`, `checkpoint_meta.json`(+ 같은 가중치의 `checkpoint_latest/` 사본, 합계 1.3 GB). `laya.load(output_dir)`가 정상 동작한다. config의 `model_name`은 "laya-typed-decisions"로 하드코딩되고 base의 `training` 블록이 그대로 남는다.
- mmBERT 호환: 스크립트의 다운로드 경로는 repo 루트(english)만 지원하므로 `--model-dir models/laya-multilingual`(공개 저장소에는 포함하지 않음)을 로컬로 넘긴다(가중치가 있어 다운로드 없음). `train()`은 max_len 1024 / head_max_len 256을 하드코딩하는데 multilingual config와 같다(english 512/192였다면 어긋남).
- 인자 전체: `model_dir`, `output_dir`, `--items`(기본 `./train_items.pt`), `--model-id`, `--epochs 4`, `--micro-batch 2`, `--grad-accum 16`, `--calib-max 400`, `--device auto|mps|cpu`, `--no-checkpointing`, `--force-preprocess`. **`--force-preprocess`는 우리 items 파일을 `LocalLLaMA/typed-decisions`로 덮어쓰므로 쓰지 않는다.**

**데이터와 어댑터(`poc/finetune/make_domain8_items.py`).** 빌더에는 `--split train`이 없으므로 어댑터가 MASSIVE ko `train`·`validation`을 직접 읽어 빌더의 `DOMAINS`·`DOMAIN_Q`·`pool_of`를 import해 변환한다(질문은 `data/evals/ko_massive_domain_8.jsonl`과 byte 일치, questions_sha256 a7f2f6b8 assert). train 11,514 → 11,094행(완전 중복 414, 길이 필터 6 제거), validation 2,033 → 2,012행. train 라벨 분포: productivity 2,917 / info_qa 2,194 / media 1,920 / communication 1,332 / lifestyle 896 / general 640 / smart_home 638 / transport 557(자연 분포 유지). train과 test의 발화 중복: eval 500행 중 33행(dev 17, test 16, 라벨 동일), 전체 test 2,917행 중 155행. 평가는 중복 포함·제외 두 수치를 함께 보고한다. 결정: 학습 아이템에 **옵션 순서 셔플 증강**을 어댑터에서 추가한다(G4 flip 0.270 개선 목적, upstream도 같은 처방을 권함). 산출 JSONL은 `poc/finetune/data/domain8_train.jsonl`, `domain8_dev.jsonl`.

**타이밍 프로브(1,000행, 1 epoch, 32 step, MPS, 다른 프로젝트 GPU 작업이 100% 점유 중).**

| 구성 | items/s | s/step | MPS peak alloc / driver | 비고 |
|---|---|---|---|---|
| mb2 × ga16, checkpointing on(기본) | 1.43 | 21.9 | 5.97 / 7.71 GB | setup 2.4 s, train 699 s, calibration 13 s, export 1 s, wall 721 s |
| mb2 × ga16, no-checkpointing | 1.71 | 16.7 | 5.94 / 8.16 GB | 200행 |
| mb8 × ga4, checkpointing on | 2.02 | 14.1 | 5.57 / 7.87 GB | 200행 |
| mb8 × ga4, no-checkpointing | 3.01 | 9.5 | 7.87 / 11.68 GB | 200행, 본 학습 채택 |

checkpointing은 메모리를 거의 아끼지 못하고(가중치·grad·AdamW 상태 약 5.2 GB가 지배) 1.2\~1.5배 느리다. RSS 약 3 GB. 경합이 풀린 micro-batch는 0.14\~0.35 s로 끝나, 위 수치는 3\~5배 부풀려진 값이다.

| 세트 | base | 프로브 | Δ [95% CI], McNemar p |
|---|---|---|---|
| domain_8 all (500) | 0.526 | 0.722 | +0.196 [+0.152, +0.240], 5e-17 |
| domain_8 dev | 0.560 | 0.724 | +0.164 |
| domain_8 test | 0.492 | 0.720 [0.664, 0.776] | +0.228, 3e-12 |
| validation 2,012 | 0.462 | 0.716 | +0.254 |
| YNAT dev 245 (망각 확인) | 0.612 | 0.624 | +0.012, p=0.70 |

macro-F1 0.518 → 0.733, ECE 0.229 → 0.097(T 3.058). smart_home 흡수는 해소됐지만(예측 140 → 60) general이 새 흡수원이 됐다(info_qa→general 14, media→general 12). 중복 제외 정확도 0.717로 중복의 영향은 없었다.

**본 학습(`poc/finetune/run_full.sh`).** 11,094행 × 3 epoch(1,041 step, σ annealing 세 값을 모두 거침), mb8 × ga4(effective 32), `--no-checkpointing`, calibration은 validation 400행, epoch별 체크포인트 보존 후 dev(validation) 수치로 epoch 선택. 산출 `poc/finetune/ckpt_domain8_v1/`(공개 저장소에는 포함하지 않음). 추정: GPU 경합 상태 3.1\~3.2 h, GPU 유휴 시 1\~1.5 h(미측정), 평가 약 10분, 디스크 약 3.3 GB(여유 32 GB), MPS peak 8\~9 GB. 실행 시점은 다른 프로젝트의 GPU 큐가 끝나면 자동 시작한다(프로젝트 책임자 결정, 2026-10-02).

- 평가: `laya-evals --model <디렉터리>`는 ValueError로 실패하므로(router.py:112-118) `poc/finetune/eval_ckpt.py`(`laya.evals.evaluate`에 `model=` 인자를 버리는 runner wrapper)로 돌린다. 대상: `data/evals/ko_massive_domain_8.jsonl`(dev/test 절반, `results/B/B_splits.json`), 전체 test 2,917행(`results/P4/evalsets_full/`), YNAT dev 245(망각), 그리고 파인튜닝 체크포인트에 대한 G4 flip 재측정(`scripts/probe_option_order.py`).
- 문서 차이 확인: README:91은 MPS 스크립트가 evaluate를 한다고 하지만 하지 않는다. finetune.md의 knobs(fp16, effective batch 64, 4096)는 Kaggle 노트북 값이고 MPS 스크립트는 fp32 / 32 / 2048이다. finetune.md의 "fit이 실패하면 1.2"도 노트북에만 해당하며 MPS 스크립트는 try/except 없이 중단한다.
- 시나리오 A를 P4에서 함께 살리려면 `ko_poc_triage_v1.jsonl`(04 §5.8) 라벨링이 그때 시작된다.

검증: (1) domain_8 test 절반 accuracy(bootstrap 95% CI)가 G1 0.80 이상인지, 중복 제외 수치를 나란히 기록 (2) YNAT dev 하락 0.03 이내(망각 없음) (3) 파인튜닝 체크포인트의 router_v1 flip rate(G4) 재측정 (4) 전체 test 2,917행 정확도와 validation 기준 epoch 선택 근거 기록.

**본 학습 결과 (2026-10-03, run `full_20261003-1156`, `results/P4/full_run_status.log` 14 STEP OK → RUN_FULL FINISHED).**
- 실행: 감시자 `poc/finetune/autostart_when_gpu_free.sh`가 GPU 유휴 36분 확인 후 11:56:25 자동 시작, 12:40:29 종료. 학습 wall 2,150 s(35.8분; train loop 2,136 s, calibration 5.6 s, export 0.6 s), GPU 유휴(`cotenant_found: false`, matmul 6.84 TFLOPS). 11,094행 × 3 epoch = 1,041 step, mb8 × ga4, `--no-checkpointing`, seed 13, 15.6 items/s, 2.05 s/step. 메모리: RSS 2.99 GB, MPS allocated peak 8.15 GB(driver 21.7 GB). 학습 아이템은 옵션 순서 셔플 증강(`make_domain8_items.py --shuffle-options all`, 11,093/11,094행 재배열), validation 400행은 canonical 순서로 calibration 슬롯에 배치(`poc/finetune/READY`, items sha256 0ec55377…). calibration: validation 400행, CE 1.339, accuracy 0.895, 1회 fit.
- epoch 곡선(validation 2,012행, dev-2012): ep1 0.892 [0.877, 0.906] → ep2 0.916 → ep3 0.918 [0.906, 0.930]. ep2 vs ep3 차이는 유의하지 않아 규칙대로 최종 export(ep3 가중치 + fitted T)를 v1로 채택(`epoch_select` 단계, `results/P4/metrics/full_20261003-1156_summary.md`).

| 세트 | base multilingual | ft-v1 | 중복 제외 ft-v1 (n) | 비고 |
|---|---|---|---|---|
| domain_8 500 all | 0.526 | 0.894 [0.866, 0.918] | 0.887 (467) | ECE 0.229 → 0.055, macro-F1 0.518 → 0.891 |
| domain_8 dev 250 | 0.560 | 0.888 [0.848, 0.928] | 0.880 (233) | |
| domain_8 **test 250 (G1)** | 0.492 | **0.900 [0.860, 0.936]** | **0.893 (234)** | ECE 0.053, acc@50%cov 0.992 |
| 전체 ko test 2,917 | 0.475 | **0.913 [0.902, 0.923]** | 0.908 (2,762) | ECE 0.057, macro-F1 0.893 |
| validation 2,012 | 0.462 | 0.918 [0.906, 0.930] | 0.914 (1,896) | 400행은 T fit에 사용 |
| YNAT dev 245 (망각) | 0.612 | 0.633 [0.567, 0.698] | 해당 없음 | 하락 없음(+0.021) |

- G4 재측정(`scripts/probe_option_order.py`, domain_8 dev 250행, 순열 5개, seed 13, CPU fp32): 순열당 flip 0.037 [0.022, 0.057], any-flip 0.084 [0.052, 0.124], 원 순서 acc 0.888, 순열 평균 0.894. confidence ≥ 0.9 결정 219건의 flip은 0.005. zero-shot 0.270에서 통과로 전환됐고, 셔플 증강은 유지한다(`results/P4/metrics/full_20261003-1156_option_order_dev.md`).
- coverage(G2, `results/P4/metrics/full_20261003-1156_coverage_500.md`, `_coverage_2917.md`): test 절반에서 오류 ≤ 5% 최대 coverage 0.756(사후 T 0.938, covered acc 0.952), ≤ 10%면 1.000; dev가 고른 T 0.892를 test에 적용하면 coverage 0.916에 오류 0.079. 전체 2,917행은 5% 예산 0.923(T 0.897), dev-1459가 고른 T 0.907을 test-1458에 적용해도 coverage 0.923, 오류 0.042로 예산 안이다. 250행 기준 판정은 T 선택에 민감하므로 P2 서비스의 T는 2,917행 곡선으로 정한다.
- 남은 혼동: general 재현율이 가장 낮다(ep3 dev-2012 70/120; general→info_qa 25, info_qa→general 20). `general`을 ROUTE할지 항상 FALLBACK할지는 열린 질문 4 그대로다.
- 산출물: 체크포인트 `poc/finetune/ckpt_domain8_v1/`(epoch_1\~3 사본 포함), 리포트 `results/P4/full_20261003-1156_*.{json,md}`, `results/P4/metrics/full_20261003-1156_*`, 타이밍 `results/P4/full_20261003-1156_timing.json`, 학습 로그 `results/P4/full_20261003-1156_train.log`.
- 검증 항목 결과: (1) G1 통과(0.900, 중복 제외 0.893) (2) YNAT 망각 없음(+0.021) (3) G4 통과(0.037) (4) 2,917행 0.913, epoch 선택 근거 기록 완료.

### P5. Go/No-Go 판정 + 리포트 (0.5일)

06 §2 `REPORT.md` 템플릿에 §8 표의 측정값을 채우고 00 §6 매트릭스로 판정한다. Conditional Go인 경우 조건(파인튜닝, 오류 예산 재합의, 배포 하드웨어, 항상 FALLBACK으로 보내는 도메인)을 명시한다.

**판정 결과 (2026-10-03, `results/go_no_go.json`, `results/REPORT.md`).**

| 게이트 | zero-shot (2026-10-02) | 파인튜닝 ft-v1 (2026-10-03) | 판정 |
|---|---|---|---|
| G0 재현 | ko 0.470 / en 0.710 Δ0 | 동일 | 통과 |
| G1 정확도 (domain_8 test 절반) | 0.492 | 0.900 (중복 제외 0.893; 전체 2,917행 0.913) | 통과 |
| G2 coverage @ 오류 ≤ 5% | 0.224 | 2,917행 dev T 0.907 적용 0.923(오류 0.042); 250행 사후 T 0.756 | 통과(조건부) |
| G3 ECE | 0.263 → refit 0.098 | 0.053 (2,917행 0.057) | 통과 |
| G4 옵션 순서 flip | 0.270 | 0.037 (any-flip 0.084) | 통과 |
| G5 in-process 3q p95 | Track D | MPS 22.6 ms / CPU 57.8 ms (short) | 통과 |
| G6 laya-serve 10 RPS 3q p95 | Track D | 79.4 ms (MPS), 오류·503 0 | 통과 |
| G7 predict vs predict_batch(sort) | P0 device parity만 | flip 0, max abs(delta p) 0.0001 (CPU) | 통과 |

**판정: Conditional Go(파인튜닝 파이프라인 전제).** zero-shot은 G1/G2/G4 미달로 No-Go이고, 파인튜닝 체크포인트 ft-v1은 G0\~G7 모두 통과한다. Go의 조건은 다음과 같다.

1. **파인튜닝 파이프라인 운영**: 도메인 taxonomy별로 MASSIVE 형식의 라벨 데이터(ko train 11,094행 수준)를 유지하고, taxonomy나 wording이 바뀌면 `poc/finetune/run_full.sh`로 재학습한다(M4 Pro 유휴 GPU에서 36분 + 평가 10분). 새 체크포인트마다 Track B(test 절반 1회)·C1(flip)·E(coverage 곡선, T 재선정)를 다시 돌리고 run card와 ADR을 남긴다.
2. **서빙 구성**: 한국어 채널은 `lang="ko"` 강제 + 추론 전 NFC 정규화(07 §6); 단일 임계값 T = 0.907(2,917행 test의 dev 절반 곡선, 오류 5% 예산)로 ROUTE/FALLBACK; general 유사·저신뢰 요청은 FALLBACK(LLM 또는 사람); production에서 옵션 순서 고정; 체크포인트 SHA·`questions_sha256`·T를 모든 로그에 기록.
3. **용량**: laya-serve는 추론을 한 번에 하나씩 처리하므로 프로세스당 MPS 1문항 약 50 RPS, 3문항 22.6 RPS, CPU 3문항 10 RPS가 상한이다. 그 이상은 프로세스 복제(체크포인트당 RSS 약 2.1 GiB, MPS는 driver 약 1.2 GiB 추가)로 확장한다. 간헐 트래픽에서는 MPS 지연이 2\~3.6배 늘어 CPU와 차이가 줄므로(D1c) CPU 전용 배포도 선택지다. ONNX int8은 이 플랫폼에서 더 느리고 결정 7%를 바꿔 쓰지 않는다(D7).
4. **미해결 항목**: 250행 test 절반의 G2는 T 선택 방식에 민감하므로 운영 초기 shadow 단계에서 실제 트래픽으로 coverage·오류율을 재확인한다; LLM 베이스라인(Track F2)은 미실행이라 G1은 절대 기준 0.80으로 판정했다; train과 test의 동일 발화 중복(155/2,917)은 제외 수치(0.908)를 병기했다.

---

## 7. 운영 고려사항

| 항목 | 설정 / 방침 | 근거 |
|---|---|---|
| 상주 체크포인트 | stock laya-serve: `LAYA_PRELOAD=1`, `LAYA_MODELS=multilingual,english`, `LAYA_MAX_LOADED=2`. 옵션 1 앱(`poc/service/app.py:48-60`)은 이 변수를 읽지 않고 `Router(models={"multilingual": "poc/finetune/ckpt_domain8_v1", "english": "models/laya"})`를 직접 구성(ft-v1 preload, english 지연 로드). 한국어 채널은 `lang="ko"` 고정이라 default는 영어 혼입 트래픽에만 영향(07 §4), `LAYA_DEFAULT_MODEL=multilingual` | 콜드 로드는 수 초, `max_loaded=1`은 언어 전환마다 7-10초 재로드 (출처: README.md "Production Preload & Memory") |
| 스레드 | `LAYA_THREADS`를 물리 코어 이하(M4 Pro: 10 성능 코어 기준 10), inter-op 1 | 랩톱 CPU에서 inter-op 기본값이 12배 느렸음 (출처: BENCHMARKS.md §Laptop CPU) |
| 공급망 고정 | `LAYA_REVISION=reviewed` 또는 명시 SHA, `LAYA_SHA256_DIGESTS`로 파일 digest 검증 | 출처: laya/revisions.py `PINNED_REVISIONS`, `verify_digests` |
| 인증·프록시 | `LAYA_API_KEY` 필수, 리버스 프록시 뒤에서는 `LAYA_ROOT_PATH` | 0.3.23부터 `/health` 내부 상태도 bearer 필요(#812) |
| 요청 한도 | `MAX_CHOICE_OPTIONS = 100`(413), `LAYA_MAX_TOKEN_BUDGET`로 `max_len`/`head_max_len` 상한, batch 64 states | 출처: README.md "Self-Hosting", laya/serve.py `_check_request_limits` |
| 과부하 | 503 + `Retry-After`를 클라이언트가 지수 backoff로 처리. admission 한도 `LAYA_MAX_CONCURRENT`(laya/serve.py:158)는 P2 측정값으로 결정 | 추론은 단일 worker 직렬(laya/serve.py:685 주석) |
| GPU OOM | 0.3.23: OOM fallback은 reader-writer gate로 격리, 일반 forward는 동시 진행 | 출처: README.md "What's new in 0.3.23" |
| 개인정보 | RedactHook이 추론 전 마스킹, shadow 로그에 원문 금지, 로그는 결정 근거 보존용이며 액션을 만들지 않음 | 출처: docs/staged-adoption.md §1 |
| Linux 배포 프록시 | Docker CPU 이미지(`compose.yaml`)로 동일 요청 재측정, CPU 전용 호스트는 ONNX int8(Track D7) 비교 | 출처: docs/docker.md |
| 모니터링 | abstention/FALLBACK rate(도메인별), incumbent 대비 disagreement rate, p95, LLM fallback 수, 503 수, `routing.reason`(lang='ko' 고정 여부), 모든 로그 라인에 checkpoint SHA와 `questions_sha256` | docs/staged-adoption.md §4 체크리스트 |
| 버전 드리프트 | laya 0.3.23, torch 2.14.1, transformers 5.18.0, 체크포인트 55cf4c4 고정. 업그레이드는 P1 명령 재실행 + `laya-evals compare --baseline`으로만 승인 | 출처: docs/evals.md "Baseline and CI gate" |
| 데모 UI 노출 범위 | 127.0.0.1 바인딩, bearer 필수, 운영 배포 대상 아님 | 검토용 화면. 액션 실행 없음(출처: docs/staged-adoption.md §1) |

---

---

## 8. 측정 항목과 Go/No-Go 매핑

| 측정 항목 | 산출 단계 | 기준 (00 §6) | 산출물 경로 |
|---|---|---|---|
| `ko_massive_domain_8` test half accuracy, macro-F1, 95% CI (G1) | P1 | baseline 대비 -5 포인트 이내 또는 0.80 이상 | `results/B/20261002-1643_multilingual_ko_massive_domain_8.json`, `results/B/summary_20261002.md`. zero-shot 0.492 [0.432, 0.552], F1 0.468, 미달 → **ft-v1 0.900 [0.860, 0.936], F1 0.897, 중복 제외 0.893, 통과** (`results/P4/metrics/full_20261003-1156_summary.md`) |
| `ko_klue_ynat_7` accuracy (보조 과제) | P1 | 보고 항목(G1 보조 근거) | `results/B/20261002-1645_multilingual_ko_klue_ynat_7.json`. 측정 test 0.655 |
| 한국어 페널티: 같은 id의 ko vs en 쌍(multilingual), McNemar | P1 | 보고 항목(07 §5 기준 0.10 수준 기대) | `results/B/summary_20261002.md` §2. 측정 ko 0.526 vs en 0.510, p=0.47(페널티 없음) |
| english / typed-decisions / Router 대비 체크포인트 선택 근거 | P1 | multilingual이 한국어에서 우세 (H2) | `results/B/summary_20261002.md` §6. 측정: multilingual 고정 선택 |
| 도메인별 recall, 혼동 상위 쌍, 첫 옵션 과예측 여부 | P1 | 보고 항목(taxonomy 수정 입력) | `results/B/summary_20261002.md` §5, `results/C/C_schema_v2_20261002.md`. 첫 옵션 과예측은 기각 |
| option-order flip rate (`router_v1`) (G4) | P1 (Track C1) | 0.10 이하 | `results/C/C1_option_order_20261002.md`. zero-shot 0.270(게이트 통과 결정 0.094), 미달 → **ft-v1 0.037(any-flip 0.084), 통과** (`results/P4/metrics/full_20261003-1156_option_order_dev.md`) |
| in-process p95 (3문항, MPS/CPU) (G5) | Track D1 | 100 ms / 500 ms 이하 | `results/D/D_summary_20261003.md` §1. 측정: multilingual short MPS 22.6 / CPU 57.8 ms, long 92.5 / 247.8 → **통과** |
| laya-serve p95 @ 10 RPS (3문항, MPS) (G6) | Track D6 | 150 ms 이하 | `results/D/20261003-1330_http_mps.json`. 측정: p50 63.5 / p95 79.4 / p99 85.1 ms, 503 0 → **통과** |
| 503 비율, Retry-After, RSS, 콜드 로드 | Track D6/D8/D3 | 보고 항목 | 503 0건(Retry-After 경로 미실행); RSS 상주 1개 2.07 GiB, 64-state 배치 피크 +1.86\~5.49 GiB; cold load multilingual 3.45\~3.67 s (`results/D/D_summary_20261003.md`) |
| predict vs predict_batch(sort_by_length) parity (G7) | Track D4 | 0 flip, abs(delta p) 0.01 이하 | `results/D/20261003-1314_batch.json`. 측정: CPU flip 0, max 0.0001; MPS fp16 flip 0, 0.0081\~0.0085 → **통과** |
| 데모 UI 동작 (단일 5 + 다중 4 예시 전부 응답, in-process/curl과 argmax 일치, 경고·오류 상태 동작, shadow 뷰 갱신) | P2-UI | 보고 항목(기능 확인). **측정(2026-10-03): 수용 점검 11/11 ✔, 예시 10종 응답, in-process 대조 차이 0, `/poc/decide` 왕복 p50 20.1 / p95 21.1 ms** | `results/poc/P2_ui_check.md`, `results/poc/P2_20261003.md`, 스크린샷 `results/poc/P2_ui_1.png` \~ `P2_ui_8_server_down.png` |
| ECE before/after refit (test half) (G3) | P3 | refit 후 0.10 이하 | `results/E/E_summary_20261002.md`, `poc/calibration/ko_v1.json`. zero-shot 0.263 → 0.098(pooled), 경계 통과 → **ft-v1 test 0.053, 2,917행 0.057, 통과** |
| coverage @ 오류 예산, 단일 T (G2) | P3 | 오류 5% 이하에서 coverage 0.70 이상(예산 재합의 가능) | `results/E/E_summary_20261002.md`, ADR. zero-shot 0.224(10% 0.308, 15% 0.400), 미달. 도메인별 T는 기각 → **ft-v1 test 절반 사후 T 0.756 / dev T 적용 시 오류 0.079; 2,917행 dev T 적용 coverage 0.923, 오류 0.042, 통과(조건부)** (`results/P4/metrics/full_20261003-1156_coverage_*.md`) |
| ROUTE 비율 × 정확도(LLM 호출 절감 추정) | P3 | 비용 논거, 기준 없음 | `results/poc/P3_coverage.md` |
| 파인튜닝 전후 accuracy(domain_8 test 절반, 중복 제외 병기), YNAT 망각, G4 flip 재측정 | P4 | G1 0.80, YNAT 하락 0.03 이내, flip 0.10 | `results/P4/P4_probe_20261002.md`(프로브: test 0.492 → 0.720), 본 학습 `results/P4/full_20261003-1156_*`. **측정: test 0.900(중복 제외 0.893), YNAT +0.021, flip 0.037, 전부 충족** |

판정 규칙: 정확도·coverage·ECE·flip이 모두 충족이면 Go. 정확도만 미달이고 P4가 충족시키면 Conditional Go(파인튜닝 파이프라인 운영 전제). coverage만 미달이면 Conditional Go(오류 예산 재합의 또는 fallback 비율 수용). latency만 미달이면 Conditional Go(배포 하드웨어 변경 전제). 정확도와 coverage가 P4 후에도 미달이면 No-Go.

---

## 9. 리스크와 완화

| 리스크 | 근거 | 완화 |
|---|---|---|
| 한국어 zero-shot 정확도가 낮음 | **측정됨(2026-10-02)**: domain_8 0.49\~0.56(test/dev), YNAT 0.63\~0.66, scenario_18 0.52, intent-20 0.470. 스키마 문구 변형 6종으로 개선 불가(`results/C/C_schema_v2_20261002.md`) | G1 미달 확정. 남은 경로는 P4 파인튜닝(MASSIVE ko train 11,514행) 또는 과제 계약 변경(v1 확률 5클래스 합산 dev 0.682). 프로젝트 책임자 결정 |
| G2는 G1에 종속 | 정확도 a에서 오류 e 이하 coverage의 상한은 a/(1−e). a=0.492, e=0.05이면 0.518이라 0.70은 보정으로 닿지 않음(`results/E/E_summary_20261002.md`) | G1 개선 없이는 G2 재합의(예산 10%: 0.308, 15%: 0.400)만 가능 |
| 도메인 정의 겹침으로 인한 확신 오답 | P0c: play↔music 14/17, audio→general, iot→alarm. 게이트로 걸러지지 않음 | 8도메인 병합(§4), 빌더의 설명 어휘 교집합 검사, 혼동 상위 쌍을 P1에서 보고하고 v2에서 재병합 |
| (보류 A) noul이 state 대신 라벨을 따라감, 부정문 오판 | #156, #377, P0b: 어떤 noul 형태도 always-no 기저를 합계로 넘지 못함, 07 §5: 영어 입력에서도 동일(체크포인트 성질) | v1에는 noul이 없다. A를 P4로 살릴 때 질문별 결정 임계값(03 E6)과 파인튜닝으로 다룬다 |
| (보류 A) score가 약함, multilingual 첫 레벨 편향 | SST-5 0.372, #131, P0b 레벨 0 선택 0/30 | v1에는 score가 없다. A에서는 보조 신호로만 |
| option-order flip | **측정됨**: router_v1 순열당 0.270(any-flip 0.512), ynat 0.168. flip의 74%가 오답 항목에서 나오고 confidence ≥ 0.9 결정의 flip은 0.094. 첫 옵션 위치 편향은 기각(`results/C/C1_option_order_20261002.md`) | production에서 옵션 순서 고정. G4 정의(순열당 vs 게이트 통과 결정)는 열린 질문. 설명 재작성·순서 변경으로는 개선 안 됨(v2a\~v2e) |
| 노트북급 SoC thermal throttling | 60초 부하 시 성능 코어 클럭 저하 가능 | 부하 전후 idle 측정, `powermetrics`로 클럭 기록, 3회 반복 중앙값 |
| MPS fp16(5 rows 이상)과 CPU fp32 수치 차이 | `mps_amp_min_rows` 기본 5 (출처: laya/agent.py) | P0/P2 parity 게이트, 필요하면 `LAYA_MPS_AMP_MIN_ROWS`로 fp32 강제 후 latency 재측정 |
| laya-serve 단일 worker 직렬 추론과 503 | create_app 주석(laya/serve.py:685 이하) | P2에서 포화 RPS 측정, 필요 시 프로세스 복제(체크포인트 메모리 x N) 비용 산정 |
| hooks 주입 경로 변경 | `create_app(router)` 시그니처 의존 | 착수 시 재확인, 옵션 2 대안 유지 |
| taxonomy 드리프트 | wording·병합 규칙을 dev 결과 보고 바꾸면 test half가 오염됨 | 병합 규칙은 §4에 고정, 변경은 `router_v2.json` + 재빌드, test half는 최종 1회만 평가 |
| 버전 드리프트 | laya는 주간 단위로 릴리스 중(0.3.18 → 0.3.23이 1주) | 02의 고정 버전, 업그레이드는 baseline compare 통과 시에만 |
| 혼합문 라우팅 실패 | 라틴 다수 혼합문·영어 래퍼 속 짧은 한국어가 english로 감(46건 배터리 중 10건 실패, 07 §4) | 한국어 채널은 `lang="ko"` 명시, 라우팅 결과를 shadow 로그에 남겨 모니터링 |
| NFD 입력 | NFC 정규화가 없어 NFD 한국어는 토큰 3.09배, 자모·byte 조각으로 분해(07 §3) | RedactHook 또는 서버 입구에서 `unicodedata.normalize("NFC")` |
| Jev 대비 우위는 파인튜닝 전제 | n=24 수동 비교에서 zero-shot 0.417은 Jev 0.833보다 낮고, ft-v1 0.917만 Jev와 대등(`results/F/jev_playground_manual_20261006.md`) | 도입 논거를 "zero-shot 대체"가 아니라 "로컬 파인튜닝 라우터(지연 20 ms, 비용 0)"로 세운다. 정식 비교는 Jev API 키 확보 후 500행 paired |

---

---

## 열린 질문 / 가정

1. **결정됨: C(도메인 라우터), 2026-10-02.** 주 과제 `ko_massive_domain_8`, 보조 `ko_klue_ynat_7`. A는 P4 파인튜닝 후보로 보류(§2).
2. **G2 오류 예산.** 00 §6 기본값은 오류 5%에서 coverage 0.70이다. P0c의 YNAT 수치(coverage 50%에서 오류 14%)로 보면 5%는 달성이 어려울 수 있다. 10%로 바꿀지, fallback 비율을 수용할지는 P3 곡선을 보고 프로젝트 책임자가 정한다.
3. **선택적 수작업 세트.** 확정 taxonomy에 대한 "실제 질의" 100건(실 서비스 문체, PII 없음)을 P1에 더할지. MASSIVE는 음성 비서 발화라 분포가 다르다.
4. **`general` 처리.** ROUTE(chat 핸들러)로 둘지 항상 FALLBACK으로 보낼지. P1의 `general` precision을 보고 정한다.
5. **종결: P4 완료(2026-10-03).** G1 미달(domain_8 test 0.492) 확정 후 프로젝트 책임자가 파인튜닝을 택했고, 본 학습(run `full_20261003-1156`)으로 test 0.900·flip 0.037·ECE 0.053을 얻었다. train/test 중복 행은 두 수치 병기로 처리(중복 제외 0.893), 옵션 순서 셔플 증강은 G4 통과 근거로 유지한다(§6 P4).
16. **ft-v1을 P2 서비스 체크포인트로 채택.** `laya-serve`의 `LAYA_MODELS`는 체크포인트 이름만 받으므로(laya/serve.py:667-668) 파인튜닝 체크포인트는 `poc/service/app.py`에서 `Router(models={"router": "poc/finetune/ckpt_domain8_v1", ...})` 또는 `laya.load("poc/finetune/ckpt_domain8_v1")` 직접 로드로 붙인다. 서비스 T는 2,917행 coverage 곡선(5% 예산 T ≈ 0.90)에서 정하고 ADR에 체크포인트 sha256·questions_sha256과 함께 기록한다.
6. **LLM baseline 사용 여부.** Anthropic API 키가 있으면 Track F 프로토콜로 `claude-haiku-4-5-20251001` baseline을 측정하고, 없으면 절대 기준(0.80)으로 판정한다. 비용·단가는 실행 시점의 공식 pricing 페이지 값을 run card에 기록한다.
7. **Router 내부 agent 접근.** calibration 적용은 `laya.load(..., calibration=...)` + `router.attach()` 경로를 기본으로 한다. Router가 보유한 agent에 직접 `apply_calibration_payload`를 적용하는 경로는 Router의 내부 속성 이름을 확인한 뒤에만 쓴다.
8. (확인 완료) `laya-serve`의 admission 한도 환경변수는 `LAYA_MAX_CONCURRENT`다(laya/serve.py:158 `_resolve_max_concurrent`). 값은 P2 측정으로 정한다.
9. **TCP_NODELAY 복제(해소).** 옵션 1에서 uvicorn을 직접 띄우면 `NoDelayHTTPProtocol`이 빠지지만, P2 실측에서 HTTP 오버헤드 p95 0.7 ms로 Nagle 지연이 보이지 않았다. 복제는 선택 사항으로 둔다.
10. **데모 UI 인증.** `/poc/*` 라우트가 laya-serve의 `LAYA_API_KEY` bearer를 그대로 공유할지 별도 토큰을 둘지. 기본은 공유(검토용 로컬 화면이라 키 하나로 충분).
11. **스크린샷 포함 여부.** `results/poc/P2_ui_*.png`를 REPORT.md와 대시보드에 넣을지, 체크리스트(`P2_ui_check.md`)만 남길지.
12. **데모 갤러리 범위.** jevplayground의 작업 데모 9종에 대응하는 추가 데모를 PoC 범위에 넣을지. 기본은 "PoC 시나리오로 시험하기" 3카드만이며, 백로그 일괄 라우팅 데모는 `/v1/systemone/batch`를 쓰는 별도 카드로 뒤에 붙일 수 있다.
13. (확인 완료) **파인튜닝 데이터 어댑터.** `build_training_item`의 gold는 choice에서 criteria key 기준 `{"probabilities": {key: p}}`라 우리 `expected`와 1:1이다(§6 P4, `results/P4/P4_probe_20261002.md`). 어댑터 `poc/finetune/make_domain8_items.py`가 구현돼 있다.
14. **G4 정의.** 00 §6의 "flip rate ≤ 0.10"이 순열당 flip인지 any-flip인지 정해져 있지 않았다. 어느 쪽이든 미달(0.270 / 0.512)이지만, "게이트를 통과한 결정(confidence ≥ T)의 flip"으로 재정의하면 0.094로 통과한다. 재정의 여부는 프로젝트 책임자 결정.
15. **calibration payload 형태.** type 스칼라 `[1.9161, 1, 1]`은 검증하지 않은 다른 choice 질문에도 T를 건다. `{"choice:6-10": 1.9161}`로 한정할지 ADR에서 택일(router_v1 출력은 두 형태가 같다).

[English](05_poc_plan.md) | **한국어**
