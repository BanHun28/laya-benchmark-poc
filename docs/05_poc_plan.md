# 05. PoC plan: Korean domain router (scenario C)

**Purpose**: Verify, step by step, whether laya can be made a production candidate as "a stage-1 router that sends Korean user requests to non-overlapping domain handlers (or indexes) + a confidence gate + fallback (an LLM or a human)", covering single-forward-pass quality, calibration, serving latency and operability. Where the benchmark (03) measures "what the model does well and how well", this PoC measures "whether it is usable once packaged in the shape of our service". The scenario was decided as C on 2026-10-02 (§2). A (CS triage) is put on hold and kept only as a P4 fine-tuning candidate.

**Prerequisite documents**: `00_README.md` (execution order, §6 Go/No-Go criteria), `01_laya_analysis.md` (architecture, Honest limits, hypotheses H1-H10), `02_environment_setup.md` (environment, smoke test), `03_benchmark_plan.md` (Track A-F protocols, measurement scripts), `04_korean_evalset_spec.md` (public-label eval sets such as `ko_massive_domain_8.jsonl` and `ko_klue_ynat_7.jsonl`), `06_templates.md` (run card, REPORT, ADR), `07_korean_support_audit.md` (Korean support verdict and design implications).

**Outputs**: `poc/schema/router_v1.json` (canonical schema), `poc/service/` (serving code with hooks; `/poc/decide`, `/poc/shadow`, `/poc/meta` endpoints), `poc/service/ui/index.html` + `poc/service/ui/examples.json` (Laya Playground demo UI, `/poc/ui/`), `poc/calibration/ko_v1.json`, `poc/loadtest/` (request bodies, load results), `poc/logs/shadow.jsonl`, `results/poc/P*_*.json|md`, the policy ADR, and the final `results/poc/REPORT.md`. A hand-labeled set is not needed for the G1 verdict (public labels are used). The schemas of the on-hold scenario A (`triage_v1.json`, `gateway_v1.json`, `*_v1b.json`) are left as they are.

---

## 1. PoC goal and success criteria

The PoC has to answer one question. **"Can laya (multilingual checkpoint, `lang="ko"` fixed) be made a production candidate as a Korean request domain router (stage-1 routing + confidence gate + fallback)?"** The answer is one of three, Go / Conditional Go (premised on fine-tuning or a renegotiated error budget) / No-Go, and the verdict criteria are the defaults of `00_README.md` §6, used as they are (not redefined here). The mapping below is a proposal, and the threshold values are for the project owner to confirm.

| Area | Measurement | Criterion (00 §6, proposed) | Stage | Measured (zero-shot 2026-10-02 → fine-tuned ft-v1 2026-10-03) |
|---|---|---|---|---|
| Accuracy (G1) | `ko_massive_domain_8` test half accuracy (secondary: `ko_klue_ynat_7`) | within 5 points of an LLM zero-shot baseline; without a baseline, absolute 0.80 or higher | P1 | zero-shot **fail**: domain_8 test 0.492 [0.432, 0.552], ynat_7 test 0.655 (`results/B/summary_20261002.md`) → ft-v1 **pass**: test 0.900 [0.860, 0.936], 0.893 excluding duplicates, 0.913 on all 2,917 rows (`results/P4/metrics/full_20261003-1156_summary.md`) |
| Selective automation (G2) | coverage after applying the confidence gate | coverage 0.70 or higher at an error rate of 5% or less (after temperature refit). In P0c, YNAT had accuracy 0.86 (14% error) at 50% coverage, so this may be hard to reach; in that case, whether to change the error budget to 10% is an explicit decision (§Open questions) | P3 | zero-shot **fail**: test coverage 0.224 (error 0.036, refit T 0.880). Upper bound a/(1−e) = 0.518. 0.308 at 10%, 0.400 at 15% (`results/E/E_summary_20261002.md`) → ft-v1 **pass (conditional)**: on the test half, 0.756 at the post-hoc T 0.938 for the 5% budget, and error 0.079 (within the 10% budget) with the dev-chosen T 0.892; on all 2,917 rows, the T 0.907 chosen on dev-1459 gives test-1458 coverage 0.923, error 0.042 (`results/P4/metrics/full_20261003-1156_coverage_500.md`, `_coverage_2917.md`) |
| Calibration (G3) | ECE (answer_confidence, 15 bins) | 0.10 or lower after refit | P3 | zero-shot **borderline pass**: test 0.263 → 0.098 (pooled fit; 0.123 if per-task) → ft-v1 **pass**: test 0.053, 0.057 on 2,917 rows (T fitted by the script on 400 validation rows) |
| Robustness (G4) | option-order flip rate (`router_v1`) | 0.10 or lower | P1 (Track C1 protocol) | zero-shot **fail**: 0.270 [0.230, 0.310] per permutation, any-flip 0.512. 0.094 counting only decisions with confidence ≥ 0.9 (`results/C/C1_option_order_20261002.md`) → ft-v1 **pass**: 0.037 [0.022, 0.057] per permutation, any-flip 0.084 (`results/P4/metrics/full_20261003-1156_option_order_dev.md`) |
| Latency (in-process, G5) | 3-question call p95 (per 00 §6; a 1-question router call is an easier condition) | MPS 100 ms or less, CPU 500 ms or less | Track D1 | **pass** (2026-10-03): multilingual 3q p95 MPS 22.6 ms (short) / 92.5 (long 433 tok), CPU 10 threads 57.8 / 247.8 ms; 1q median MPS 13.8 / CPU 37.7 ms (`results/D/D_summary_20261003.md`) |
| Latency (HTTP, G6) | laya-serve p95 @ 10 RPS, MPS | 150 ms or less | Track D6 | **pass** (2026-10-03): 3-question body at 10 RPS p50 63.5 / p95 79.4 / p99 85.1 ms, errors and 503s 0; 1-question p95 57.3; CPU server 3-question p95 135.8 (`results/D/20261003-1330_http_mps.json`) |
| Numerical consistency (G7) | predict vs predict_batch(sort_by_length=True) | argmax flip 0, abs(delta p) 0.01 or less | Track D4 | **pass** (2026-10-03, measured as defined): CPU 64+256 states × bs 8/16/32 flip 0, max abs(delta p) 0.0001; MPS fp16 flip 0, 0.0081\~0.0085. Supplementary: P0 device parity 7/7, 0.0017 (`results/D/20261003-1314_batch.json`) |

Failing one criterion is not an immediate No-Go. A failed accuracy criterion has a conditional path to P4 (domain-router fine-tuning), a failed G2 is a matter of renegotiating the error budget or accepting the fallback rate, and a failed latency criterion is judged separately as a choice of deployment hardware (§8).

**Verdict (2026-10-02, zero-shot).** Zero-shot scenario C failed G1, G2 and G4 with the current schema (router_v1) and checkpoint (multilingual). None of the 6 schema wording variants beat v1 (§4, `results/C/C_schema_v2_20261002.md`), and calibration fixed only ECE without changing the coverage upper bound (§5). The project owner chose P4 fine-tuning.

**Verdict (2026-10-03, fine-tuned ft-v1, final).** After fine-tuning, G1 (0.900), G3 (0.053) and G4 (0.037) pass; G2 passes with coverage 0.923 (error 0.042) on all 2,917 test rows but is sensitive to how T is chosen on the 250-row test half (0.756 with a post-hoc T; error 0.079 when the dev T is applied). Track D passed G5 (3-question p95 MPS 22.6 ms / CPU 57.8 ms), G6 (laya-serve 10 RPS 3-question p95 79.4 ms) and G7 (predict vs predict_batch(sort) flip 0, max abs(delta p) 0.0001). Zero-shot fails G1/G2/G4, so **verdict = Conditional Go (premised on a fine-tuning pipeline)**. The conditions and operating requirements are in §6 P5; the figures are in `results/go_no_go.json` and `results/REPORT.md`.

---

**Versus Jev (2026-10-06, n=24 manual comparison).** On the same 24 Korean routing items, Jev (public playground) scores 0.833, Laya zero-shot 0.417 and ft-v1 0.917 (`results/F/jev_playground_manual_20261006.md`). Jev clearly beats Laya zero-shot (it also handles Korean input) and cannot be distinguished from the fine-tuned ft-v1 on this sample (Jev 0.833 vs ft-v1 0.917, p=0.5). Latency is 249.5 ms as displayed for the hosted Jev vs a 20.1 ms local ft-v1 round trip, a figure that mixes in the difference between local execution and hosting.

## 2. Scenario selection

Three of the production patterns that upstream presents (source: docs/use-cases.md §1, §3, §4, §6) were taken as candidates and compared. The table is the pre-decision comparison record.

| Item | A. Korean CS triage + LLM gateway | B. LLM prompt guardrail pre-filter | C. RAG domain index router |
|---|---|---|---|
| Core decision | intent / urgency / frustration / refund / churn + needs_llm | jailbreak / injection / sensitive_data / harm_severity | target_domain (one of N indexes) |
| Primitives used | all of choice + score + noul | mostly noul + one score | one choice |
| Measurability | High. Per-question accuracy, ECE, coverage and flip rate can all be measured | Medium. Korean data for positive samples (attack prompts) is scarce, and false negatives are costly | Highest. A single choice keeps the metrics simple |
| Data availability | own labeling of `ko_poc_triage_v1.jsonl` (04 §5.8) + proxies (MASSIVE ko intent, 3i4K speech act) | English toxic-chat/prompt-injection sets exist, but public Korean sets are lacking | KLUE YNAT 7 topics and MASSIVE 18 scenarios are direct proxies |
| Upstream evidence | a triage preset exists (source: laya/presets.py `triage_questions`), email/spam 0.993 (source: BENCHMARKS.md §Themes) | held-out guardrail 0.708-0.762, moderation 0.530 (source: BENCHMARKS.md §Themes) | Air-gapped edge RAG router pattern (source: docs/use-cases.md §4) |
| Risk | Korean zero-shot accuracy may be low (MASSIVE ko 20-option 0.470) → P4 path | accuracy itself falls short of the production criterion; usable only as a shadow signal | little business texture, so weak as evidence for an "adoption decision" |
| Reusability | service, gate and load tests reusable as is for other schemas | an eval set has to be built separately | A's infrastructure is reused by swapping only the schema file |

**The original recommendation was A.** The reasons were that all three primitives, the multilingual checkpoint, confidence gating, the batch path and the HTTP server could be verified within one scenario, and that the upstream preset is a direct template. The P0 results below changed that premise.

**P0 results taken into account (2026-10-02).** On an n=30 probe, A's zero-shot path scored intent 0.40\~0.50 (best per variant 0.50, 0.667 when collapsed to 4 classes) and the 4 binary questions were at the always-no base rate, so A as designed does not meet G1 (00 §6) zero-shot (`results/poc/P0_20261002.md`, `results/poc/P0b_20261002.md`). The C proxy scored 0.65 on KLUE YNAT 7 topics at n=100 and 0.86 at the top-50% confidence coverage (majority 0.15), while MASSIVE 18 domains scored 0.52 with many confident errors coming from overlapping domain definitions such as play/music (0.66 when the two are merged, `results/poc/P0c_20261002.md`). In the Korean support audit (07 §5), the Korean vs English accuracy gap on the same sentences was 0.21\~0.24 with English key options but shrank to 0.10 (not significant) with descriptive Korean descriptions, and the noul and score weaknesses were the same with English input, which confirmed them as properties of the checkpoint.

**Decision: C (2026-10-02).** There are four reasons. (1) A fails G1 zero-shot, and the noul and score weaknesses are not fixed by polishing the Korean sentences. (2) The C proxy reaches 0.65 on 7 topics and 0.86 with the gate, so the "stage-1 router + fallback" shape holds. (3) With descriptive Korean descriptions, the penalty versus English is small (07 §5). (4) MASSIVE ko and KLUE YNAT have public ground truth, which removes the hand-labeling bottleneck. There are two tasks. **Main task**: `ko_massive_domain_8`, which merges the 18 MASSIVE ko scenarios into 8 non-overlapping domains (test 2,974 rows; the Korean penalty is measured with the English pair of the same id; comparable with upstream zh 6-domain voice routing 0.883). **Secondary task**: the 7 KLUE YNAT news sections (`ko_klue_ynat_7`, validation 9,107 rows, a proxy for RAG index routing). A is put on hold: the schema files (`triage_v1.json`, `gateway_v1.json`, `*_v1b.json`) stay in `poc/schema/` as P4 fine-tuning candidates, and the hand-labeled triage set (04 §5.8) is built only after P4 is decided. Optionally, a hand-written set of 100 "real queries" for the finalized taxonomy can be added to P1 (§Open questions).

---

## 3. Architecture

```mermaid
graph TD
    C[Client / backlog worker] -->|POST /v1/systemone, /v1/systemone/batch| S[poc.service.app<br/>laya.serve.create_app(router)]
    UI[poc/service/ui<br/>Laya Playground review screen] -->|POST /v1/systemone, /poc/decide · GET /poc/shadow, /poc/meta| S
    S --> R[Router preload=multilingual,english<br/>default=multilingual]
    R --> H1[RedactHook<br/>on_predict_start: PII masking]
    H1 --> M{{forward pass<br/>1 question: domain (+ optional questions)}}
    M --> H2[ShadowAuditHook<br/>on_predict_end: poc/logs/shadow.jsonl]
    H2 --> H3[MetricsHook<br/>abstention / latency / fallback counters]
    H3 --> G[Gate + policy layer<br/>answer_confidence vs T]
    G -->|ROUTE: passed, p &ge; T| Q1[Domain handler / index<br/>productivity, media, smart_home, info_qa,<br/>communication, lifestyle, transport, general]
    G -->|FALLBACK: p &lt; T, abstained, unevaluated| L[LLM fallback or human review<br/>claude-haiku-4-5-20251001 or stub]
```

| Component | Role | Evidence / notes |
|---|---|---|
| `laya.serve.create_app(router)` | Provides the Jev-compatible `/v1/systemone`, `/v1/systemone/batch` and `/health`. Inference runs serially in a single-worker thread pool | source: laya/serve.py:685 `create_app`, :755-906 routes, :1024 `main` |
| `Router(preload=..., default="multilingual")` | Korean-channel requests are pinned to `predict(..., lang="ko")` from channel/locale metadata, and detection is relied on only when there is no metadata. Pure Hangul text goes to multilingual by detection too, but mixed text with a Latin majority and short Korean inside an English wrapper go to english (07 §4). RedactHook also performs NFC normalization before inference (07 §3) | source: README.md "Quickstart: Route Mode", `07_korean_support_audit.md` §3-4 |
| RedactHook | Masks phone numbers, email addresses and card numbers by rewriting `ctx.states` before inference | source: README.md "Prediction Hooks", examples/hooks/redact.py |
| ShadowAuditHook | Appends run_id, model, routing, answers, probabilities, answer_confidence, elapsed_ms, checkpoint SHA and questions_sha256 as JSONL in `on_predict_end` | source: docs/staged-adoption.md §1 ShadowLog, examples/hooks/audit.py |
| MetricsHook | abstention count, 503s, fallbacks, latency histogram | own implementation |
| Gate and policy layer | §5. An application responsibility outside laya | source: docs/staged-adoption.md "Application/Laya boundary" |
| Demo UI + `/poc/*` routes | Laya Playground (jevplayground layout): example chips, question builder, 2-column input/output, routing result card (ROUTE/FALLBACK), shadow view. For review only; it executes no actions | own implementation, mounted next to the laya-serve routes ("Demo UI routes" below). source: docs/staged-adoption.md §1 "A shadow logger must not turn logging into a new user-facing action" |

**hooks-over-HTTP constraint.** `laya-serve` rejects a request body with 422 if it contains `hooks`, `on_predict_start`, `on_predict_end`, `hooks_raise` or `hooks_timeout`, because hooks are callables and must live inside the server process (source: README.md "Self-Hosting: HTTP Server"). Hooks are therefore installed on the server side.

- **Option 1 (adopted)**: `laya.serve.create_app(router=...)` supports injecting a Router (laya/serve.py:685, "Pass a Router to inject one"). `poc/service/app.py` builds a `Router(hooks=[...])`, preloads it, passes it to `create_app(router)` and serves it with uvicorn. Routes, auth, admission and token-budget validation use the upstream code as is. The `TCP_NODELAY` protocol class that `laya.serve.main()` plugs in (avoids the macOS Nagle delay, #620) is lost when we call uvicorn directly. In the P2 measurement (2026-10-03, `results/poc/P2_20261003.md`), the HTTP overhead without NoDelay was p95 0.7 ms (round trip p95 21.1 ms vs server processing 20.4 ms), so replicating it is optional.
- **Option 2 (alternative)**: reimplement the same `/v1/systemone` contract in our own FastAPI app. Used only if option 1 is blocked (e.g. a change in the create_app signature). At the start of implementation, the implementer re-checks the signature of `create_app` in `third_party/laya/laya/serve.py` (the upstream clone, not included in the public repository; recreate it by cloning https://github.com/NandhaKishorM/laya at commit 4aa6761).
- **zero-code path**: for stretches that need no hooks, such as the P0-P2 latency measurements, plain `laya-serve` is started with environment variables only. As it is the reference point (baseline) for numeric comparisons, it is measured at least once with the same requests as the option 1 server.

```python
# poc/service/app.py (sketch)
import os
from laya import Router
from laya.serve import create_app                    # laya/serve.py:685
from poc.service.hooks import RedactHook, ShadowAuditHook, MetricsHook

CKPT_SHA = "3270d480..."   # ft-v1 rl_agent_config.json sha256(poc/finetune/ckpt_domain8_v1, base 55cf4c4). Recomputed from the file at startup; aborts if it differs from the value T was chosen with (app.py:41)
QSHA = os.environ.get("POC_QUESTIONS_SHA256", "")             # questions_sha256 of router_v1.json (computed at startup)

def build_router():
    # LAYA_MODELS means the same as in laya-serve (a list of checkpoint names); it is a different variable from LAYA_MODELS_DIR in env.sh (02 §2.8)
    names = [m.strip() for m in os.environ.get("LAYA_MODELS", "multilingual,english").split(",") if m.strip()]
    # Korean-channel requests are pinned with predict(..., lang="ko") (07 §4). RedactHook applies unicodedata.normalize("NFC") before masking (07 §3)
    router = Router(device=os.environ.get("LAYA_DEVICE", "mps"),
                    default=os.environ.get("LAYA_DEFAULT_MODEL", "multilingual"),
                    max_loaded=int(os.environ.get("LAYA_MAX_LOADED", "2")),
                    hooks=[RedactHook(),
                           ShadowAuditHook("poc/logs/shadow.jsonl", checkpoint_sha=CKPT_SHA, questions_sha256=QSHA),
                           MetricsHook()])
    router.preload(names)
    return router

app = create_app(router=build_router())
# Run: uvicorn poc.service.app:app --host 127.0.0.1 --port 8000
# LAYA_API_KEY, LAYA_MAX_TOKEN_BUDGET, LAYA_ROOT_PATH and the like are read by create_app directly from the environment.
```

```python
# poc/service/hooks.py (sketch, source: docs/staged-adoption.md §1 ShadowLog pattern)
# upstream examples/hooks/audit.py and redact.py are function hooks (on_predict_end(ctx), redact(ctx)). Since state (path, SHA)
# has to be held, they are wrapped in classes here. Hooks are duck-typed, so both go into Router(hooks=[...]).
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

RedactHook replaces `ctx.states` with a masked copy in `on_predict_start`. The unmasked original text is not kept in the shadow log either (§7).

**Demo UI routes.** The object returned by `create_app(router)` is an ordinary FastAPI app, so our routes are simply added next to the upstream routes. Four routes and two static assets (`index.html`, `examples.json`) are all there is.

| Route | Request | Response | Notes |
|---|---|---|---|
| `POST /poc/decide` | `{"utterance": str, "min_confidence": float \| null, "model": "auto" \| "multilingual" \| "english", "lang": "ko" \| null}` | `{"answers", "routing", "usage", "policy": {"action": "ROUTE" \| "FALLBACK", "domain", "handler", "p", "reason"}, "thresholds": {"T"}, "elapsed_ms", "checkpoint": {"path", "sha256_of_rl_agent_config", "base"}, "questions_sha256", "schema_version": "router_v1"}` (as implemented, `poc/service/app.py:76`) | Calls `router.predict(..., lang="ko")` with the single `domain` question of `router_v1.json` and applies the §5 `route(answers)`. `lang` defaults to `"ko"` (Korean channel, 07 §4); `null` leaves it to detection. With `model: "auto"` the Router routes; otherwise the model is pinned with `model=`. When `LAYA_API_KEY` is set, the same bearer check as laya-serve (reusing the check function of `laya.serve` if it can be imported, otherwise the same logic in 10 lines) |
| `GET /poc/shadow?limit=50` | none | `{"records": [last N records], "counters": {"total", "abstained": {"count", "rate"}, "actions": {"ROUTE": n, "FALLBACK": n}, "by_domain": {domain: count}, "elapsed_ms": {"p50", "p95"}}}` | Reads the last N lines of `poc/logs/shadow.jsonl` and aggregates them. No writes |
| `GET /poc/meta` | none | `{"laya_version", "checkpoint": {"path", "sha256_of_rl_agent_config", "base"}, "questions_sha256", "schema_version": "router_v1", "thresholds": {"T"}, "models_loaded": [...]}` (`app.py:132`) | Returns the values computed at server startup as they are. Read by the UI header badge and the "문서와 상태" (Docs and status) section. Used to check against the SHA in the run card |
| `GET /poc/ui/` | none | `poc/service/ui/index.html`, `poc/service/ui/examples.json` | Static mount. A single HTML file + vanilla JS + inline CSS with no build step and no external dependencies (system fonts). `examples.json` is a static file holding the state, questions, description and `state_key` of each example (5 single + 4 multi) and is fetched by the UI. The bearer key is taken from an input field and kept only in `sessionStorage` |

```python
# continuing poc/service/app.py (sketch)
import json, time
from fastapi import Body, Header
from fastapi.staticfiles import StaticFiles
from poc.service.policy import route, T, T_BY_DOMAIN

SCHEMA = json.load(open("poc/schema/router_v1.json"))["questions"]          # 1 question: domain

@app.post("/poc/decide")
def poc_decide(body: dict = Body(...), authorization: str | None = Header(default=None)):
    check_bearer(authorization)                                            # same rule as laya-serve
    model = None if body.get("model", "auto") == "auto" else body["model"]
    t0 = time.perf_counter()
    r = ROUTER.predict({"utterance": body["utterance"]}, SCHEMA, lang=body.get("lang", "ko"),
                       min_confidence=body.get("min_confidence"), model=model)   # the Korean channel is pinned to lang="ko" (07 §4)
    action, detail = route(r["answers"])
    return {"answers": r["answers"], "routing": r["routing"], "usage": r["usage"],
            "policy": {"action": action, **detail},
            "thresholds": {"T": T}, "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
            "checkpoint": {"path": CKPT_DIR, "sha256_of_rl_agent_config": CKPT_SHA, "base": BASE_SHA},
            "questions_sha256": QSHA, "schema_version": "router_v1"}

app.mount("/poc/ui", StaticFiles(directory="poc/service/ui", html=True), name="poc-ui")
```

(This assumes that `ROUTER` holds the instance built by `build_router()` as a module variable. `/poc/shadow` likewise only reads and aggregates `shadow.jsonl`.)

Screen layout (`poc/service/ui/index.html`, named "Laya Playground"). The structure follows the independent 3rd-party Jev playground https://jevplayground.com (viewed 2026-10-02; reference screenshots (not included in the public repository) `docs/assets/reference/jevplayground_top_20261002.jpeg`, `jevplayground_full_20261002.jpeg`). Since laya-serve provides the same `POST /v1/systemone` protocol as Jev (source: README.md "Self-Hosting: HTTP Server"), the site's structure of calling the Jev API carries over as is when moved onto a local laya-serve. Upstream's `examples/server.py` playground (02 §3.8) can be used as is, but it has no policy card, shadow view or Korean examples, so the PoC review is done with this page.

| Area | Contents |
|---|---|
| Header | Title "Laya Playground". Nav: Playground · PoC 라우터 (PoC router) · Shadow 로그 (Shadow log) · 문서 (Docs: path strings for 00\~07; the server does not serve docs/, so these are paths to copy rather than HTTP links) · 상태 (Status: `/health` summary). Right-hand badge "로컬 실행 · laya 0.3.23 · 체크포인트 ft-v1 3270d480(base 55cf4c4)" ("local run · … · checkpoint …"; the values are filled from `checkpoint` of `GET /poc/meta`, for the active checkpoint) |
| Hero | eyebrow "ONE FORWARD PASS, CALIBRATED PROBABILITIES", title, one-line description (Korean), badge "✓ 로컬 체크포인트 / multilingual·english / 네트워크 없음" ("✓ local checkpoint / multilingual·english / no network") |
| Mode toggle | **단일 질문 \| 다중 질문** (single \| multiple questions). Single = 1 question builder. Multiple = question list (add, delete, reorder) + preset loading |
| Example chips | One-click load, a type badge, and after loading the banner "✓ 예시가 로드됨. 그대로 실행하거나 아무 필드나 수정하세요." ("✓ Example loaded. Run it as is or edit any field."). 5 single: "도메인 라우팅 CHOICE" (domain routing; the PoC canonical schema `router_v1.json`, state e.g. "내일 아침 7시에 깨워줘", Korean descriptions of the 8 domains), "고객 문의 라우팅 CHOICE" (customer inquiry routing; the state is a sentence requesting a refund for a double charge, question "Which team should handle `message`?", options billing/technical/sales/other + Korean descriptions), "환불 요청 확인 NOUL" (refund request check; "Does the customer ask for money back?"), "장애 긴급도 SCORE" (incident urgency; 4 levels), "에이전트 다음 행동 CHOICE" (agent next action; the state is an agent observation JSON, options click/type/scroll/done). 4 multi: "CS triage + gateway 7문항(보류 시나리오 A)" (CS triage + gateway questions, on-hold scenario A; `triage_v1.json` + `gateway_v1.json`, with newly written example utterances, because the P0 probe sentences carry a do-not-reuse header and have no dev/test split), "이메일 분류" (email classification; `laya.presets.email_questions`), "프롬프트 가드레일" (prompt guardrail; `guard_questions`), "모델 라우터" (model router; `router_questions`) (source: laya/presets.py). The data is in `examples.json` |
| INPUT panel (left) | State textarea + character counter "N자" (N characters) + display of `usage.input_tokens` after a run (no token estimate beforehand). State-form toggle **텍스트 \| JSON** (text \| JSON) and a `state_key` field (default `message`; laya takes a dict state and the presets refer to `message`/`body`/`prompt`/`post`/`request` in backticks, so the field name has to match. source: laya/presets.py `state_field`). Question builder: question id (ASCII, default `q1`), instructions, Decision type segment **Choice \| Noul(Boolean) \| Score** + a description box (choice "라벨 하나를 고르고 라벨별 확률을 돌려준다" (picks one label and returns per-label probabilities), noul "진술이 참일 확률 P(true)를 돌려준다. Jev의 Boolean에 대응" (returns P(true), the probability that the statement is true; corresponds to Jev's Boolean), score "레벨 설명 목록에 대한 기대 레벨과 레벨별 확률을 돌려준다" (returns the expected level over the list of level descriptions and per-level probabilities)). Choice options = numbered chips 01.., each with two fields, **key(ASCII)** + **description (Korean)** (Jev has a single label field, but laya's criteria are a key→description structure and the key is the option text the model reads. source: README.md "Honest limits"), × to remove, "+ 선택지 추가" (+ add option), counter "4 / 20", and above 20 the warning badge "head_max_len 예산 초과 가능(README Honest limits), 03 Track C6 참고" (the head_max_len budget may be exceeded; see …) (above the server limit of 100: 413). Score = 2\~7 level descriptions (expected is a 0-based index). Noul = true/false description toggle (off by default = v1 policy; when on, `criteria` is sent). Advanced (collapsed): model auto/multilingual/english/typed-decisions, `min_confidence` slider 0.5\~0.95 (off by default; when on, the abstention badge is shown), `max_len`/`head_max_len`, `lang_guess`. Run button "Run Laya ↗" + helper text "로컬 체크포인트에서 실행 · 네트워크 없음" (runs on the local checkpoint · no network) + Ctrl+Enter (the same shortcut as upstream `examples/server.py`. source: README.md "Try it locally: web GUI + JSON API") |
| OUTPUT panel (right) | Label "OUTPUT" + badge (`routing.model` of the response and the SHA). Empty state: glyph "[ · ]", "결정이 여기에 표시됩니다." (the decision will appear here), "state와 typed question을 주고 실행하면 결정과 확률이 보입니다." (give a state and a typed question and run it to see the decision and probabilities), flow chip "State + Question → Laya → Decision + Probability". Results: only in PoC mode (the `router_v1` example or the "PoC 라우터" (PoC router) nav), a **routing result card** at the top (ROUTE / FALLBACK, domain, handler, p, applied threshold T, reason; the `/poc/decide` response). Question card (the answer in large type, an `answer_confidence` bar, a list of `probabilities` bars (with `legend` for score), an `abstention` badge passed / abstained / unevaluated, the P(true) value for noul). Meta row: server `elapsed_ms`, browser round-trip ms, `usage.input_tokens`/`output_tokens`, `routing.reason`. Tool buttons: "JSON 보기" (view JSON) toggle, "curl 복사" (copy curl), "Python 복사" (copy Python), "CLI 복사" (copy CLI; in the form `laya "..." --questions FILE`. source: README.md "Command line"). Error state: "결정이 생성되지 않았습니다. 입력은 유지됩니다." (no decision was produced; your input is kept) + the server error body (the 422/413/503 message as is; for 503, `Retry-After` is shown). Footer "실제 로컬 모델 실행. 시뮬레이션 없음." (a real local model run; no simulation) |
| Bottom sections | **"PoC 시나리오로 시험하기"** (try it with the PoC scenarios), 3 cards: C domain router (default) → loads `router_v1.json` + 8 example utterances for the 8 domains + a toggle to switch to the YNAT 7-topic question (04 §5.2); A CS triage + gateway (on hold) → loads the 7 questions + the text "zero-shot G1 미달, P4 파인튜닝 후보(`results/poc/P0b_20261002.md`)" (fails the accuracy gate zero-shot; a fine-tuning candidate); B prompt guardrail → loads the guard preset + the risk text "upstream held-out 가드레일 0.708\~0.762" (upstream held-out guardrail …) (source: BENCHMARKS.md §Themes). **"Shadow 로그"** (Shadow log): a table of the last 50 records (time, first 40 characters of the utterance, domain, `answer_confidence`, ROUTE/FALLBACK, `elapsed_ms`) + counters (abstention rate, ROUTE/FALLBACK ratio, domain distribution, `elapsed_ms` p50/p95), re-polling `GET /poc/shadow` every 5 seconds. **"문서와 상태"** (Docs and status): 00\~07 path strings (for copying), the `/health` summary, the SHA, `questions_sha256` and `schema_version` from `/poc/meta`. Footer "내부 PoC 검토 도구. 운영 배포 대상 아님. 액션을 실행하지 않음(docs/staged-adoption.md)" (internal PoC review tool; not for production deployment; executes no actions) |
| Visual tone | A light background like jevplayground, white panels + thin gray borders, monospace uppercase subheadings (INPUT / OUTPUT / CHOOSE AN EXAMPLE), 1 blue accent color, numbered chips. Single HTML + vanilla JS + inline CSS, no external dependencies. 1 column below 900px |

Backend mapping: the general single- and multi-question modes call laya-serve's `POST /v1/systemone` as is (request keys `state`, `questions`, `model`, `min_confidence`, `max_len`, `head_max_len`, `lang_guess`), and only PoC mode uses `POST /poc/decide` (with the policy). Response keys are used as upstream defines them: `answers.<qid>.choice|score|noul`, `probabilities`, `legend`, `confidence`, `answer_confidence`, `abstention`, `usage`, `routing` (source: laya/agent.py:1213-1244, README.md "Quickstart: Route Mode"). The only values the UI computes itself are the browser round-trip ms and the character count.

Differences from the Jev playground:

| Item | jevplayground.com | Laya Playground |
|---|---|---|
| Binary question | Boolean | noul, with the P(true) value and the answer at the 0.5 cutoff |
| Option input | 1 label field, at most 10 | 2 fields, key(ASCII) + Korean description; 20 recommended (server limit 100, 413 above it) |
| Backend | hosted Jev API | local laya-serve `/v1/systemone` (same wire protocol) |
| Output | decision + probabilities | decision + probabilities + calibrated `answer_confidence` + `abstention` + `routing` + `usage` |
| Extra screens | a gallery of 9 task demos | routing result card, shadow log, 3 PoC scenario cards, docs/status links |
| Auth | none (usage limits) | `LAYA_API_KEY` bearer (when set) |

Two label-hygiene rules. (1) Sentences entered through the UI also end up in the shadow log, so **test-half sentences are not entered into the UI.** The reason is the same as for P1's "ablations on the dev half only" rule (preventing tuning leakage). (2) The UI is a PoC review screen, not an operations screen. It executes no actions such as queue assignment or LLM calls, and shows only the decision and its rationale (source: docs/staged-adoption.md §1 "A shadow logger must not turn logging into a new user-facing action").

---

---

## 4. Question schema v1 (router_v1)

The schema file is kept in the `{"state_key": ..., "questions": {...}}` form that `laya --questions` accepts, so CLI checks and the service read the same file. The instructions are written in English (the convention of both upstream's MASSIVE benchmark setup and the presets, which all use English instructions; Korean instructions had no effect in P0c and 07 §5. source: research/scripts/bench_local.py:175-177, laya/presets.py, `results/poc/P0c_20261002.md`), and the criteria descriptions are descriptive Korean (P0c: Korean descriptions 0.52 vs key rendering 0.35, p<0.001). The strings must be byte-identical to the question dict in 04 §5.1 (d), and the canonical copy is the `router_v1.json` of this section.

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

| Design item | Decision | Rationale |
|---|---|---|
| Merge rule | MASSIVE 18 scenarios → 8 domains: productivity ← alarm, calendar, datetime, lists / media ← music, play, audio / smart_home ← iot / info_qa ← qa, weather, news / communication ← email, social / lifestyle ← takeaway, cooking, recommendation / transport ← transport / general ← general | Most of the P0c 18-domain errors came from pairs whose definitions overlap or are adjacent, such as play↔music (14/17), audio→general and iot→alarm, and merging only play/music already gave 0.52 → 0.66 (`results/poc/P0c_20261002.md`). The 8 domains are also natural units for handlers |
| Non-overlap check | The builder prints the token-set intersection to check that no description vocabulary is shared by two domains (04 §5.1 (d)). If they overlap, a v2 file with fixed descriptions | Options with overlapping vocabulary produce confident errors that the confidence gate does not filter out (P0c) |
| Description language | Descriptive Korean. English-description variants only as the `--descriptions en` ablation | P0c −0.17 (key rendering); 07 §5: smaller penalty versus English |
| Option order | Fixed to the order written in the file (not shuffled in production). C1 measures the flip rate | option-order flip upstream 0.150/0.230, zh 10.6\~28% (BENCHMARKS.md) |
| Suspected position bias | **Rejected (C1, 2026-10-02).** The first option `productivity` is under-predicted, not over-predicted (12 in the original order, 21.8 on average over permutations, gold 30), and the smart_home absorption (66 in the original order, 58.6 on average over permutations, still 60 in v2d, which moved it to the end) is semantic. A position effect itself does exist (chi2 p=0.0009; slot 1 is picked less, 2\~4 more) | `results/C/C1_option_order_20261002.md`, `results/C/C_schema_v2_20261002.md` |
| v2 probe results | On 250 domain_8 dev rows, vs v1 0.560: strengthened descriptions v2a 0.536, general removed v2b 0.545, examples added v2c 0.540 (option tokens 418 > limit 240, so all were truncated to 30 tokens; head 512 diagnostic 0.408), reordered v2d 0.516, 5 classes v2e 0.536. **No variant beats v1.** Description wording cannot fix the smart_home and general absorption | `results/C/C_schema_v2_20261002.md` |
| `general` | catch-all. Whether to keep it as a ROUTE target or always send it to FALLBACK is an open question. The default is ROUTE (chat handler) | small talk overlaps with the LLM response path |
| Number of options | 8 fit comfortably within the head token budget (256) (30 tokens per option) | README.md "Honest limits" budget rule |

**Versioning rule.** Changing even one character of the instructions or criteria changes `questions_sha256` and makes comparison with the baseline impossible (source: docs/evals.md "Run identity"). Wording changes go into a new file such as `router_v2.json`, and the file name and `questions_sha256` are recorded in the run card (06 §1). At startup the service records the sha256 of the loaded schema file in both `/poc/meta` and the shadow log.

### 4.2 On hold: scenario A schemas (fine-tuning candidates)

Put on hold in P0/P0b because zero-shot failed G1 (§2). The files stay in `poc/schema/` and are used only as P4 fine-tuning candidates. `triage_v1.json` holds 5 of the 7 questions below (the 3 noul questions have no criteria, as in the presets), and `gateway_v1.json` holds `needs_llm` and `complexity`. `triage_v1b.json` and `gateway_v1b.json` are variants that attach Korean `true`/`false` criteria to the noul questions, and form the "+criteria" rung of the Track C2 ladder. The hand-labeled set of 04 §5.8 is built only after P4 is decided. P0b early signals (n=30, `results/poc/P0b_20261002.md`): intent at best 15/30 (English descriptions; 20/30 when collapsed to 4 classes), is_urgent 26/30 with Korean instructions, churn_risk 28/30 with the criteria variant, refund_requested 25/30 at baseline (criteria cause false positives), frustration picks level 0 in 0/30, needs_llm and complexity at the base rate. noul needs per-question thresholds rather than a fixed 0.5 threshold (07 §5 E4, 03 E6).

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

## 5. Gate and policy

laya only returns decisions and probabilities; it grants no authority to act. Thresholds are application policy and must be chosen on held-out data (source: docs/staged-adoption.md §3). The gate design rests on the following facts.

- `min_confidence` is a single per-call threshold. When it is set, every answer gets an `abstention` status (`passed` / `abstained` / `unevaluated`) and `abstention_threshold`, and answers below it are marked `low_confidence: True`. When it is not set, the response is byte-for-byte the same as before (source: README.md "Opt-in abstention").
- The gate reads `answer_confidence` (the probability of the chosen answer, invariant to the number of options), not the entropy-based `confidence`. Thresholds taken from Jev do not transfer.
- v1 has a single question (`domain`), so abstention reporting is turned on with `min_confidence=T` and the policy layer decides ROUTE/FALLBACK with the same T. Per-domain `T_BY_DOMAIN` was **rejected (E3, 2026-10-02)**: dev coverage rose 0.180 → 0.316, but on test it exceeded both the 5% and the 10% budget and failed validation (overfitting on 12\~66 dev rows per domain). The single T is 0.880 at the 5% budget after pooled calibration, and at that T `general` routes 0/40, so it effectively always goes to FALLBACK (`results/E/E_summary_20261002.md`).
- On-hold scenario A item: the noul decision threshold must be chosen per question rather than fixed at 0.5 (AUROC 0.76\~0.92, yet p(true) is pushed below 0.5; 07 §5 E4). v1 has no noul, so 03 Track E6 is optional.

```python
# poc/service/policy.py (sketch). T is finalized from the P3 coverage curve and recorded in the ADR.
T = 0.907                      # answer_confidence gate. For ft-v1: the maximum-coverage point with error ≤ 5% on dev-1459 of the 2,917 rows; applied to test-1458, coverage 0.923, error 0.042 (results/P4/metrics/full_20261003-1156_coverage_2917.md). The zero-shot-era value was 0.880 (E3)
T_BY_DOMAIN = {}               # rejected (E3 overfitting). The code path is kept but left empty
HANDLER = {"productivity": "calendar-svc", "media": "media-svc", "smart_home": "iot-svc", "info_qa": "qa-svc",
           "communication": "comm-svc", "lifestyle": "lifestyle-svc", "transport": "transport-svc", "general": "chat-svc"}

def route(answers):
    d = answers["domain"]
    p, top = d["answer_confidence"], d["choice"]
    if d.get("abstention") not in (None, "passed"):           # abstained / unevaluated (when min_confidence is on)
        return "FALLBACK", {"domain": top, "handler": None, "p": p, "reason": d["abstention"]}
    if p < T_BY_DOMAIN.get(top, T):
        return "FALLBACK", {"domain": top, "handler": None, "p": p, "reason": "below T"}
    return "ROUTE", {"domain": top, "handler": HANDLER[top], "p": p, "reason": "passed"}
```

| State / rule | Handling | Reason |
|---|---|---|
| `abstention == "unevaluated"` | FALLBACK | so that cases the gate cannot judge (NaN, no confidence) are not read as a pass |
| `abstention == "abstained"` or `p < T` | FALLBACK, increment the abstention counter | denominator and numerator of the coverage metric. The fallback is an LLM response or human review (depending on the deployment) |
| `passed` and `p >= T` | ROUTE: hand off to the domain handler (or index) | only the range within the error budget agreed in P3 |
| `general` | ROUTE by default (chat handler). Whether to always send it to FALLBACK is an open question | small talk overlaps with the LLM path |

**Choosing T (P3).** On the dev half, plot accuracy against coverage with answer_confidence in descending order, and take as T the confidence at the maximum-coverage point that satisfies the agreed error rate (default 5%, §Open questions) or less. On the test half, re-verify coverage and error rate with the same T. T is recorded in the ADR (06 §3) together with the checkpoint SHA, `questions_sha256` and the sha of the calibration file, and T becomes invalid if any of these four changes.

**Batch path.** Backlog routing is sent to `/v1/systemone/batch` (up to 64 states, sharing the forward pass). With a single question, one `min_confidence` is enough. The numerical consistency of the answers (predict vs predict_batch) is checked with a parity gate in P2.

**LLM fallback.** For channels among the FALLBACK cases that need an immediate response, `claude-haiku-4-5-20251001` is called. Without an API key it is replaced by a stub (fixed response + simulated latency), and the cost argument is computed as the call-count reduction rate (ROUTE ratio × accuracy).

---

## 6. Phased plan [step → verification]

P0-P5 are mapped onto shadow → compare → policy → bounded promotion (source: docs/staged-adoption.md). P0-P1 are preparation before compare, P2 is shadow, P3 is policy, and P5 is the promotion decision. Every run leaves a 06 §1 run card.

### P0. Smoke test (done, 2026-10-02)

Run with the scenario A schema (7 questions); the results are valid regardless of scenario (`results/poc/P0_20261002.md`): schema file byte match, MPS/CPU argmax 7/7 match (max abs Δp 0.0017), median 7-question call MPS 74 ms / CPU 146 ms (10 threads, inter-op 1), first MPS call 0.17 s. For `router_v1.json`, the same parity check is repeated once with 1 question on the first P1 run (P1 item 6 below).

### P1. Public-label evaluation + checkpoint selection (1 day, no labeling)

1. Write `poc/schema/router_v1.json` (exactly as in §4.1) → `python -c 'import json; json.load(open("poc/schema/router_v1.json"))'`, compute `questions_sha256` (04 §6 convention, `laya.evals.questions_fingerprint`).
2. Build the eval sets (04 §6 builder, network required):

```bash
source env.sh && unset HF_HUB_OFFLINE
.venv/bin/python scripts/build_ko_evalsets.py massive --lang ko --mode domain --n 500     # ko_massive_domain_8.jsonl
.venv/bin/python scripts/build_ko_evalsets.py massive --lang en --mode domain --n 500     # en_massive_domain_8.jsonl (same id)
.venv/bin/python scripts/build_ko_evalsets.py massive --lang ko --mode scenario            # ko_massive_scenario_18.jsonl (for comparison)
.venv/bin/python scripts/build_ko_evalsets.py ynat --n 500                                 # ko_klue_ynat_7.jsonl
.venv/bin/python scripts/build_ko_evalsets.py manifest
```

   The builder asserts that the `domain` question dict of `ko_massive_domain_8.jsonl` is byte-identical to the one in `router_v1.json`.
3. The dev/test split uses `results/B/B_splits.json` (03 §3.2): the paired MASSIVE sets (ko/en domain_8) by row index parity (even dev, odd test), the other sets by the parity of the state hash. The test half is scored **only once** per frozen schema version (P1 produces the G1 figure and the P5 report reuses it). The instructions/description language ablations (`_ko-instr`, `_en-desc`) and wording changes are compared on dev-half figures only.
4. Evaluate with the three checkpoints + Router auto (same as the Track B commands, 03 §7 B1):

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
  --json results/B/${ts}_multilingual_en_massive_domain_8.json       # Korean penalty: the English pair with the same id (07 §5)
python scripts/metrics_extra.py summary results/B/${ts}_*_ko_massive_domain_8.json --split-rule index --out results/B/metrics/domain_8.md
python scripts/metrics_extra.py paired results/B/${ts}_multilingual_ko_massive_domain_8.json \
  results/B/${ts}_multilingual_en_massive_domain_8.json              # paired McNemar, ko vs en
```

5. Comparison groups: majority class (MANIFEST `majority_rate`), (optional) an LLM zero-shot baseline (Track F protocol, same states, same 8 options, same Korean descriptions), and as a reference upstream zh 6-domain 0.883 (BENCHMARKS.md §Community evaluation).
6. parity: rerun 50 dev-half items of `ko_massive_domain_8` with `--device mps` and compare argmax with the CPU report (a 1-question call is fp32 on MPS too, so the flip count must be 0; 02 §4).
7. Wording changes only on dev-half results, at most 2 rounds, with a new file (`router_v2.json`) and a new run card. The test half is evaluated only 1 time per frozen version. Note: `router_v1.json` currently exists only as `results/C/schemas_v2/router_v1.json`, and `poc/schema/router_v1.json` is created in P2 by copying that file (`questions_sha256` a7f2f6b8…, must match `data/evals/MANIFEST.json`).

Verification: (1) test-half `ko_massive_domain_8` accuracy (bootstrap 95% CI) and macro-F1 are recorded and compared with the §1 G1 criterion (2) the rationale for the checkpoint choice is recorded (expected: multilingual ahead, H2) (3) whether the Korean penalty (ko vs en, same id) is at the 0.10 level of 07 §5 (4) MPS parity flip 0 (5) if G1 fails, record in an ADR whether to enter P4, and continue with P2-P3 (latency and operational verification are independent of accuracy).

**P1 results (2026-10-02, run as Track B, `results/B/summary_20261002.md`, `results/B/B_20261002.md`).** (1) domain_8 test 0.492 [0.432, 0.552], macro-F1 0.468, G1 **fail**; ynat_7 test 0.655. (2) multilingual pinned + `lang="ko"` chosen (english 0.276, typed-decisions 0.288; the Router gives identical answers on Korean). (3) No penalty (ko 0.526 vs en 0.510, p=0.47). (4) Parity was confirmed in P0. (5) Entry into P4 awaits an owner decision (§Open questions). Failure patterns: smart_home predicted 140 (gold 63), general 80 (gold 62), audio→smart_home 9/9, calendar→smart_home 14/36, weather, news and social each ≈2/18 correct.

### P2. Service build + load measurement (1-2 days)

```bash
# zero-code baseline (stock laya-serve: LAYA_MODELS is a list of checkpoint "names", so it can load only the Hub base checkpoints, not ft-v1)
LAYA_DEVICE=mps LAYA_PRELOAD=1 LAYA_MODELS=multilingual,english LAYA_DEFAULT_MODEL=multilingual \
LAYA_MAX_LOADED=2 LAYA_THREADS=10 LAYA_API_KEY=devkey LAYA_HOST=127.0.0.1 laya-serve
# server with hooks (option 1). Because app.py builds Router(models={"multilingual": "poc/finetune/ckpt_domain8_v1", "english": "models/laya"})
# itself, it does not read LAYA_MODELS (that variable is for stock laya-serve only). ft-v1 takes the multilingual slot and english is loaded on the first request
LAYA_DEVICE=mps LAYA_API_KEY=devkey LAYA_HOST=127.0.0.1 .venv/bin/uvicorn poc.service.app:app --host 127.0.0.1 --port 8000
curl -s localhost:8000/health -H 'Authorization: Bearer devkey'    # 0.3.23: with a key set, the internal status requires the bearer
curl -s localhost:8000/v1/systemone -H 'Authorization: Bearer devkey' -H 'content-type: application/json' \
  -d @poc/loadtest/req_router1.json | python -m json.tool
curl -s localhost:8000/v1/systemone/batch -H 'Authorization: Bearer devkey' -H 'content-type: application/json' \
  -d @poc/loadtest/req_batch16.json | python -c 'import json,sys; r=json.load(sys.stdin); print(len(r["results"]), r["total_usage"])'
```

`poc/loadtest/req_router1.json` holds `state: {"utterance": ...}`, the `questions` of `router_v1.json`, `lang: "ko"`, `min_confidence: 0.8` and `model: "multilingual"`. `req_batch16.json` holds 16 `states` with the same `questions`, `batch_size: 8` and `sort_by_length: true`.

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

Load measurement with `scripts/bench_http_local.py` (per the 03 D6 interface), using the 1-question body:

- closed-loop concurrency 1 / 4 / 8, 60 s, p50/p95, 503 rate, observe `Retry-After`
- open-loop 5 / 10 / 20 RPS, 60 s, p50/p95, the point where p95 blows up from queueing
- repeat the same requests with `LAYA_DEVICE=cpu LAYA_THREADS=10` (proxy for a Linux CPU deployment); for the ONNX int8 export, cite the Track D7 results
- server RSS (2 checkpoints preloaded), cold-load time, first MPS call latency

Verification: (1) 1-question p95 150 ms or less @ 10 RPS MPS (00 §6) (2) argmax agreement between the answers for 16 states via `/v1/systemone/batch` and 16 single-call answers: 0 flips, abs(delta p) 0.01 or less (3) the shadow.jsonl records all contain run_id, model, checkpoint_sha, questions_sha256, elapsed_ms and the routing result (ROUTE/FALLBACK, domain), and no raw PII (4) whether `routing.reason` is of the `explicit lang='ko'` kind (pinned routing, not detection) (5) if 503s occurred, from which RPS on and the `Retry-After` value.

#### P2-UI. Demo UI [step → verification] (0.5 day, after the P2 server is up)

Attach the four routes of §3 "Demo UI routes" plus `poc/service/ui/index.html` and `examples.json`, so that PoC decisions can be checked directly in a browser. This is a functional check, not a load measurement, so the only numeric criterion is argmax agreement.

```bash
# 1. write poc/service/ui/index.html + examples.json (single HTML + vanilla JS, no build, following the §3 screen-layout table)
# 2. start the option 1 server (same as P2; app.py does not read LAYA_MODELS), then open it in a browser
LAYA_DEVICE=mps LAYA_API_KEY=devkey LAYA_HOST=127.0.0.1 .venv/bin/uvicorn poc.service.app:app --host 127.0.0.1 --port 8000
open http://127.0.0.1:8000/poc/ui/
# 3. run all 5 single-question examples (including router_v1) + 4 multi-question examples (example utterances from the dev half only). Run one with Ctrl+Enter
# 4. ft-v1 is checked by comparing in-process (CPU, laya.load("poc/finetune/ckpt_domain8_v1")) vs server (MPS) answers (results/poc/P2_acceptance.py).
#    The CLI line below uses the Hub base checkpoint with `--model ml`, so it cannot be compared with ft-v1; it is only a sanity check of base behavior (cli.py:147-148)
laya "<utterance entered in the UI>" --model ml --lang ko --questions poc/schema/router_v1.json --json
# 5. check that the shadow table and counters at the bottom refresh within 5 seconds
# 6. auth: call without a key → rejected; after entering the key → OK
curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:8000/poc/decide -H 'content-type: application/json' -d '{"utterance":"내일 아침 7시에 깨워줘"}'
curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:8000/poc/decide -H 'Authorization: Bearer devkey' -H 'content-type: application/json' -d '{"utterance":"내일 아침 7시에 깨워줘"}'
# 7. edge behavior: enter 21 options for the warning badge; stop the server and run for the error-state text with the input kept; 1-column rendering below a 900px window width
# 8. meta check
curl -s localhost:8000/poc/meta -H 'Authorization: Bearer devkey' | python -m json.tool   # compare checkpoint_sha and questions_sha256 with the run card
```

Verification: (1) all 5 single + 4 multi examples respond, and for the router_v1 example the routing result card shows ROUTE or FALLBACK (2) the `domain` argmax matches the in-process ft-v1 (CPU) result and the rerun of "curl 복사" (copy curl) (CLI `--model ml` is the base checkpoint and not a comparison target) (3) moving the `min_confidence` slider switches the `abstention` badge between passed / abstained (4) shadow records contain no raw PII (only the text after RedactHook) (5) the difference between the browser round trip and the server `elapsed_ms` is within a few tens of ms locally (6) with `LAYA_API_KEY` set, a call without a key gets 401 or 403, and 200 with the key (7) the warning badge appears at 21 options and Ctrl+Enter runs it (8) running with the server down shows the message "결정이 생성되지 않았습니다. 입력은 유지됩니다." (no decision was produced; your input is kept) and the input is not cleared (9) `checkpoint_sha` and `questions_sha256` from `GET /poc/meta` equal the run card values (10) it renders as 1 column below 900px width. The results are kept as a checklist in `results/poc/P2_ui_check.md` and the screens as `results/poc/P2_ui_*.png` screenshots.

**P2 results (2026-10-03, `results/poc/P2_20261003.md`, UI checklist `results/poc/P2_ui_check.md`).**

| Item | Result |
|---|---|
| Implementation files | `poc/service/app.py` (142 lines: Router setup :48-60, startup check of SHA and questions_sha256 :41, bearer :67, `/poc/decide` :76, `/poc/shadow` :113, `/poc/meta` :132, static mount :142), `hooks.py` (123 lines: NFC+PII masking :17-36·:50, shadow JSONL :55-94, counters :97), `policy.py` (31 lines, T :4, ROUTE/FALLBACK :20-31), `ui/index.html` (1,050 lines), `ui/examples.json` (391 lines), `poc/schema/router_v1.json` (byte-identical to the original) |
| Checkpoint | ft-v1 (`poc/finetune/ckpt_domain8_v1`, not included in the public repository) in the `multilingual` slot; english loaded lazily. The `ko_v1.json` calibration is not applied (ft-v1 has its own T) |
| Policy T | 0.907 (on dev-1459 of the 2,917 rows; test-1458 coverage 0.923, error 0.042). Answers that are abstained, unevaluated or from a non-ft-v1 checkpoint go to FALLBACK |
| Auth | no key 401, wrong key 401, with key 200. Without a key, `/health` gives liveness only |
| `/poc/meta` check | questions_sha256 a7f2f6b8…, rl_agent_config sha 3270d480…, weights sha b0609f54… all match the P4 report and MANIFEST |
| 8-domain examples + doc example | 9/9 ROUTE, correct domain 9/9, p 0.924\~0.957, `routing.reason` = explicit lang='ko' |
| FALLBACK | meaningless string p 0.222, multiple intents p 0.669 → FALLBACK. `min_confidence` 1.0 → abstained; 0.5 → passed but below T → FALLBACK |
| PII | recorded in shadow only as `[email]`, `[phone]`, `[card]`; 0 raw originals |
| General mode | `/v1/systemone` 3-option choice 200, technical 0.985 |
| shadow counters | 50 lines = total, ROUTE 44 + FALLBACK 5 = per-domain sum |
| in-process check | CPU ft-v1 vs server MPS: 0 different answers out of 9, max probability difference 0.0000 |
| Browser check | all 10 items of 05 §6 + the 5-second refresh ✔ (10 examples, Ctrl+Enter, curl/Python copy reruns identical, slider passed↔abstained, warning at 21 options, error text and input kept when the server is down, 1 column at 820px). Screenshots `results/poc/P2_ui_1.png` (empty state) \~ `P2_ui_8_server_down.png` |
| `/poc/decide` round trip (1 question, 30 consecutive calls) | p50 20.1 / p95 21.1 ms (server processing p50 19.5 / p95 20.4, HTTP overhead p95 0.7 ms) |

Caveats. (1) Clicking in the browser at intervals of a few seconds raises server processing to 44\~51 ms. This is the same phenomenon as Track D's intermittent-call penalty (D1c, `results/D/D_summary_20261003.md`). (2) The p of the 9 examples cluster at 0.92\~0.96, leaving only 0.017\~0.05 of headroom to T 0.907, so even a small change in wording or precision can flip ROUTE/FALLBACK. (3) General-mode questions such as the presets are also answered by the ft-v1 in the `multilingual` slot, and that quality was not measured. (4) `min_confidence: null` is treated as T, the same as omitting it, and `/poc/decide` also accepts `model` (auto·multilingual·english). (5) Out of scope this time: load measurement (done by Track D6 with the base checkpoint; same structure, hence the same latency), 503 and Retry-After, UI reproduction of the 413 for more than 101 options, and checks of the visual tone and on real devices.


### P3. Calibration + threshold policy (1 day)

The multilingual checkpoint ships without a fitted temperature, and refit is the most effective fix, ECE 0.314 → 0.106 (source: BENCHMARKS.md §Calibration). `laya.calibrate` has a per-bucket floor of `MIN_BUCKET_N = 2000` and a type-level floor of `MIN_TYPE_N = 10` (source: laya/calibrate.py module docstring), so at PoC scale only a **type-level temperature (1 for choice)** is realistic. Even when built with `--n 0` (2,917 rows), the dev half is about 1,460 rows, below the bucket floor of 2,000 (calibrate.py:178). A low-floor bucket fit (`--min-bucket-n 100`) gives the same value as the type scalar, because the records fall into a single bucket (choice:6-10).

```bash
python scripts/calibrate_ko.py --model models/laya-multilingual --device cpu \
  --sets data/evals/ko_massive_domain_8.jsonl,data/evals/ko_klue_ynat_7.jsonl \
  --splits results/B/B_splits.json --pooled --per-task --min-bucket-n 100 \
  --out-payload poc/calibration/ko_v1.json --out results/E/$(date +%Y%m%d-%H%M)_calibration_multilingual.json
# the coverage curves (before/after calibration), T per budget and the per-domain T validation are computed together by the script above. metrics_extra coverage gives only the pre-calibration curve, from the report's rounded probabilities.
```

Caveat: `records_from_labeled` lacks `@torch.no_grad()`, so calling it with a real Agent raises a grad-tensor error (upstream defect, laya/calibrate.py:286 → agent.py:1177). `scripts/calibrate_ko.py:93` wraps it in `torch.no_grad()` (03 E2).

- `records_from_labeled(agent, pairs)` → `fit_temperature_map(records, compute_ece=True)` → `calibration_payload(...)` produces `poc/calibration/ko_v1.json`. Pooled (domain_8 + ynat_7) vs per-task fits are cross-applied to the held-out data to check transferability (03 E2).
- Application path: build the agent with `laya.load(path, calibration="poc/calibration/ko_v1.json")` and attach it to the Router with `router.attach("multilingual", agent)`. The `Router` constructor has no calibration argument, and `laya-evals --calibration` applies only to the ONNX path (source: docs/evals.md "Evaluating an ONNX export"), so evaluation on the torch path is done with our service code or `apply_calibration_payload`.
- Choose a single T on the dev half (per-domain T was rejected in E3 for overfitting) → re-measure ECE, coverage and error rate on the test half → write the ADR (checkpoint SHA 55cf4c4, `questions_sha256`, calibration sha256, T, dataset sha256, owner, date). The payload form (type scalar vs restricted to `{"choice:6-10": T}`) is also an ADR item.
- 03 Track E6 (noul decision threshold) is optional, because v1 has no noul. It was run once on 2026-10-02 with NSMC noul: AUROC test 0.822, dev Youden threshold p(true) ≥ 0.0073, test accuracy 0.725 (0.641 at the 0.5 cutoff, 2-choice 0.773). This is the evidence for when A is revived through P4.

**P3 results (2026-10-02, run as Track E, `results/E/E_summary_20261002.md`).** pooled T 1.9161 (domain_8 2.0245, ynat 1.8149; choice:6-10, no clamping). test ECE domain_8 0.263 → 0.098, ynat 0.148 → 0.063 → G3 borderline pass. 5% budget T 0.880 → test coverage 0.224 (error 0.036) → G2 **fail** (upper bound 0.518). 10% 0.308, 15% 0.400. Applying the payload `poc/calibration/ko_v1.json` (pooled, [1.9161, 1, 1], sha256 a217cb5d…) was verified (rescored ECE 0.0980, answers 250/250 identical).

Verification: on the test half, ECE 0.10 or less, and coverage 0.70 or more within the agreed error budget (default 5%) (00 §6). If not met, (a) also report the coverage at a 10% error budget, (b) report which domains drag it down (tag slice `scenario:*`), and (c) record the alternative "that domain always goes to FALLBACK" in the ADR.

### P4. Fine-tuning (done, decided 2026-10-02 → main training run 2026-10-03)

Upstream evidence: typed-decisions zero-shot 0.362 → fine-tuned 0.766, browser-agent 0.10 → 0.66 (source: README.md "Fine-Tuning", docs/finetune_browser_agent.md). 4 epochs on 30k questions took 4-5 hours on 2xT4. The time needed on this machine was measured with the probe below (`results/P4/P4_probe_20261002.md`).

**Script fact check (`third_party/laya/notebooks/laya_finetune_typed_decisions_mps.py`, part of the upstream clone and not included in the public repository; used without modification).**
- Items: `build_training_item(tokenizer, cfg, state, question, gold_question)` (:58-100). The gold format is `{"probabilities": {<criteria key>: p}}` for choice (keys, not indexes), `"true"`/`"false"` keys for noul, and `"0".."n-1"` keys for score. Our `expected` maps 1:1 as `{key: 1.0}`. Sequences are built by `build_sequence` with the options **in canonical order as is**, and there is no option-order augmentation.
- Training: fp32, no autocast. AdamW (encoder 2.5e-5, head 1e-4, wd 0.01), cosine down to 1e-6, no warmup, grad clip 1.0. loss = RLCD (σ 0.4 → 0.1 annealing, 4 samples, `proper_reward` w_sph 0.75) + soft CE. Defaults micro-batch 2 × grad-accum 16, epochs 4. Gradient checkpointing is on by default for both encoder and head (turned off with `--no-checkpointing`). No seed, no early stopping; `checkpoint_latest/` is overwritten every epoch.
- calibration: `min(--calib-max, N//10)` items are split off from the same items file by position with `random.Random(20260922)`, and T is fitted per type with LBFGS. Our adapter places the validation rows at those positions in advance so that no train rows enter calibration.
- export: fp16 `model.safetensors`, `encoder/`, `tokenizer/`, `rl_agent_config.json`, `checkpoint_meta.json` (+ a `checkpoint_latest/` copy of the same weights, 1.3 GB in total). `laya.load(output_dir)` works. The config's `model_name` is hardcoded to "laya-typed-decisions", and the base's `training` block remains as is.
- mmBERT compatibility: the script's download path supports only the repo root (english), so `--model-dir models/laya-multilingual` (not included in the public repository) is passed locally (the weights are present, so nothing is downloaded). `train()` hardcodes max_len 1024 / head_max_len 256, which matches the multilingual config (with english's 512/192 it would mismatch).
- Full argument list: `model_dir`, `output_dir`, `--items` (default `./train_items.pt`), `--model-id`, `--epochs 4`, `--micro-batch 2`, `--grad-accum 16`, `--calib-max 400`, `--device auto|mps|cpu`, `--no-checkpointing`, `--force-preprocess`. **`--force-preprocess` is not used, because it overwrites our items file with `LocalLLaMA/typed-decisions`.**

**Data and adapter (`poc/finetune/make_domain8_items.py`).** The builder has no `--split train`, so the adapter reads MASSIVE ko `train` and `validation` directly and converts them by importing the builder's `DOMAINS`, `DOMAIN_Q` and `pool_of` (the question is byte-identical to `data/evals/ko_massive_domain_8.jsonl`; asserts questions_sha256 a7f2f6b8). train 11,514 → 11,094 rows (414 exact duplicates and 6 by the length filter removed), validation 2,033 → 2,012 rows. Train label distribution: productivity 2,917 / info_qa 2,194 / media 1,920 / communication 1,332 / lifestyle 896 / general 640 / smart_home 638 / transport 557 (natural distribution kept). Utterance overlap between train and test: 33 of the 500 eval rows (dev 17, test 16, same labels), 155 of all 2,917 test rows. Evaluation reports both figures, with and without the duplicates. Decision: the adapter adds **option-order shuffle augmentation** to the training items (to improve the G4 flip of 0.270; upstream recommends the same remedy). The output JSONL files are `poc/finetune/data/domain8_train.jsonl` and `domain8_dev.jsonl`.

**Timing probe (1,000 rows, 1 epoch, 32 steps, MPS, while another project's GPU job occupied 100%).**

| Configuration | items/s | s/step | MPS peak alloc / driver | Notes |
|---|---|---|---|---|
| mb2 × ga16, checkpointing on (default) | 1.43 | 21.9 | 5.97 / 7.71 GB | setup 2.4 s, train 699 s, calibration 13 s, export 1 s, wall 721 s |
| mb2 × ga16, no-checkpointing | 1.71 | 16.7 | 5.94 / 8.16 GB | 200 rows |
| mb8 × ga4, checkpointing on | 2.02 | 14.1 | 5.57 / 7.87 GB | 200 rows |
| mb8 × ga4, no-checkpointing | 3.01 | 9.5 | 7.87 / 11.68 GB | 200 rows, adopted for the main training run |

Checkpointing saves almost no memory (weights, grads and AdamW state, about 5.2 GB, dominate) and is 1.2\~1.5x slower. RSS about 3 GB. Micro-batches without contention finish in 0.14\~0.35 s, so the figures above are inflated 3\~5x.

| Set | base | probe | Δ [95% CI], McNemar p |
|---|---|---|---|
| domain_8 all (500) | 0.526 | 0.722 | +0.196 [+0.152, +0.240], 5e-17 |
| domain_8 dev | 0.560 | 0.724 | +0.164 |
| domain_8 test | 0.492 | 0.720 [0.664, 0.776] | +0.228, 3e-12 |
| validation 2,012 | 0.462 | 0.716 | +0.254 |
| YNAT dev 245 (forgetting check) | 0.612 | 0.624 | +0.012, p=0.70 |

macro-F1 0.518 → 0.733, ECE 0.229 → 0.097 (T 3.058). The smart_home absorption was resolved (predictions 140 → 60), but general became the new absorber (info_qa→general 14, media→general 12). Accuracy excluding duplicates was 0.717, so the duplicates had no effect.

**Main training run (`poc/finetune/run_full.sh`).** 11,094 rows × 3 epochs (1,041 steps, passing through all three σ annealing values), mb8 × ga4 (effective 32), `--no-checkpointing`, calibration on 400 validation rows, checkpoints kept per epoch and the epoch chosen on the dev (validation) figures. Output `poc/finetune/ckpt_domain8_v1/` (not included in the public repository). Estimates: 3.1\~3.2 h with GPU contention, 1\~1.5 h with an idle GPU (not measured), evaluation about 10 minutes, disk about 3.3 GB (32 GB free), MPS peak 8\~9 GB. It starts automatically once another project's GPU queue finishes (owner decision, 2026-10-02).

- Evaluation: `laya-evals --model <directory>` fails with a ValueError (router.py:112-118), so it is run with `poc/finetune/eval_ckpt.py` (a runner wrapper for `laya.evals.evaluate` that drops the `model=` argument). Targets: `data/evals/ko_massive_domain_8.jsonl` (dev/test halves, `results/B/B_splits.json`), all 2,917 test rows (`results/P4/evalsets_full/`), YNAT dev 245 (forgetting), and a G4 flip re-measurement on the fine-tuned checkpoint (`scripts/probe_option_order.py`).
- Documentation discrepancies: README:91 says the MPS script runs evaluate, but it does not. The knobs in finetune.md (fp16, effective batch 64, 4096) are the Kaggle notebook's values; the MPS script uses fp32 / 32 / 2048. finetune.md's "1.2 if the fit fails" also applies only to the notebook; the MPS script aborts without try/except.
- If scenario A is to be revived together in P4, labeling of `ko_poc_triage_v1.jsonl` (04 §5.8) starts at that point.

Verification: (1) whether domain_8 test-half accuracy (bootstrap 95% CI) is G1 0.80 or higher, recorded side by side with the duplicate-excluded figure (2) YNAT dev drop within 0.03 (no forgetting) (3) re-measure the router_v1 flip rate (G4) of the fine-tuned checkpoint (4) record the accuracy on all 2,917 test rows and the rationale for the validation-based epoch choice.

**Main training run results (2026-10-03, run `full_20261003-1156`, `results/P4/full_run_status.log` 14 STEP OK → RUN_FULL FINISHED).**
- Execution: the watcher `poc/finetune/autostart_when_gpu_free.sh` confirmed the GPU idle for 36 minutes, then started the run automatically at 11:56:25; it ended at 12:40:29. Training wall 2,150 s (35.8 minutes; train loop 2,136 s, calibration 5.6 s, export 0.6 s), GPU idle (`cotenant_found: false`, matmul 6.84 TFLOPS). 11,094 rows × 3 epochs = 1,041 steps, mb8 × ga4, `--no-checkpointing`, seed 13, 15.6 items/s, 2.05 s/step. Memory: RSS 2.99 GB, MPS allocated peak 8.15 GB (driver 21.7 GB). The training items use option-order shuffle augmentation (`make_domain8_items.py --shuffle-options all`, 11,093/11,094 rows reordered), and the 400 validation rows are placed in the calibration slot in canonical order (`poc/finetune/READY`, items sha256 0ec55377…). calibration: 400 validation rows, CE 1.339, accuracy 0.895, 1 fit.
- Epoch curve (2,012 validation rows, dev-2012): ep1 0.892 [0.877, 0.906] → ep2 0.916 → ep3 0.918 [0.906, 0.930]. The ep2 vs ep3 difference is not significant, so per the rule the final export (ep3 weights + fitted T) was adopted as v1 (`epoch_select` step, `results/P4/metrics/full_20261003-1156_summary.md`).

| Set | base multilingual | ft-v1 | ft-v1 excluding duplicates (n) | Notes |
|---|---|---|---|---|
| domain_8 500 all | 0.526 | 0.894 [0.866, 0.918] | 0.887 (467) | ECE 0.229 → 0.055, macro-F1 0.518 → 0.891 |
| domain_8 dev 250 | 0.560 | 0.888 [0.848, 0.928] | 0.880 (233) | |
| domain_8 **test 250 (G1)** | 0.492 | **0.900 [0.860, 0.936]** | **0.893 (234)** | ECE 0.053, acc@50%cov 0.992 |
| all ko test 2,917 | 0.475 | **0.913 [0.902, 0.923]** | 0.908 (2,762) | ECE 0.057, macro-F1 0.893 |
| validation 2,012 | 0.462 | 0.918 [0.906, 0.930] | 0.914 (1,896) | 400 rows used for the T fit |
| YNAT dev 245 (forgetting) | 0.612 | 0.633 [0.567, 0.698] | n/a | no drop (+0.021) |

- G4 re-measurement (`scripts/probe_option_order.py`, 250 domain_8 dev rows, 5 permutations, seed 13, CPU fp32): flip 0.037 [0.022, 0.057] per permutation, any-flip 0.084 [0.052, 0.124], original-order acc 0.888, permutation mean 0.894. The flip of the 219 decisions with confidence ≥ 0.9 is 0.005. It went from 0.270 zero-shot to a pass, and the shuffle augmentation is kept (`results/P4/metrics/full_20261003-1156_option_order_dev.md`).
- coverage (G2, `results/P4/metrics/full_20261003-1156_coverage_500.md`, `_coverage_2917.md`): on the test half, the maximum coverage at error ≤ 5% is 0.756 (post-hoc T 0.938, covered acc 0.952), and 1.000 at ≤ 10%; applying the dev-chosen T 0.892 to test gives coverage 0.916 with error 0.079. On all 2,917 rows, the 5% budget gives 0.923 (T 0.897), and applying the T 0.907 chosen on dev-1459 to test-1458 still gives coverage 0.923 with error 0.042, within the budget. The 250-row verdict is sensitive to the choice of T, so the T of the P2 service is set from the 2,917-row curve.
- Remaining confusion: general has the lowest recall (ep3 dev-2012 70/120; general→info_qa 25, info_qa→general 20). Whether to ROUTE `general` or always send it to FALLBACK remains open question 4.
- Outputs: checkpoint `poc/finetune/ckpt_domain8_v1/` (including copies of epoch_1\~3), reports `results/P4/full_20261003-1156_*.{json,md}`, `results/P4/metrics/full_20261003-1156_*`, timing `results/P4/full_20261003-1156_timing.json`, training log `results/P4/full_20261003-1156_train.log`.
- Verification results: (1) G1 pass (0.900, 0.893 excluding duplicates) (2) no YNAT forgetting (+0.021) (3) G4 pass (0.037) (4) 2,917 rows 0.913, rationale for the epoch choice recorded.

### P5. Go/No-Go verdict + report (0.5 day)

Fill the 06 §2 `REPORT.md` template with the measured values of the §8 table and decide with the 00 §6 matrix. For a Conditional Go, state the conditions (fine-tuning, renegotiated error budget, deployment hardware, domains always sent to FALLBACK).

**Verdict (2026-10-03, `results/go_no_go.json`, `results/REPORT.md`).**

| Gate | zero-shot (2026-10-02) | fine-tuned ft-v1 (2026-10-03) | Verdict |
|---|---|---|---|
| G0 reproduction | ko 0.470 / en 0.710 Δ0 | same | pass |
| G1 accuracy (domain_8 test half) | 0.492 | 0.900 (0.893 excluding duplicates; 0.913 on all 2,917 rows) | pass |
| G2 coverage @ error ≤ 5% | 0.224 | 0.923 with the dev T 0.907 on 2,917 rows (error 0.042); 0.756 with a post-hoc T on 250 rows | pass (conditional) |
| G3 ECE | 0.263 → refit 0.098 | 0.053 (0.057 on 2,917 rows) | pass |
| G4 option-order flip | 0.270 | 0.037 (any-flip 0.084) | pass |
| G5 in-process 3q p95 | Track D | MPS 22.6 ms / CPU 57.8 ms (short) | pass |
| G6 laya-serve 10 RPS 3q p95 | Track D | 79.4 ms (MPS), errors and 503s 0 | pass |
| G7 predict vs predict_batch(sort) | P0 device parity only | flip 0, max abs(delta p) 0.0001 (CPU) | pass |

**Verdict: Conditional Go (premised on a fine-tuning pipeline).** Zero-shot is No-Go, failing G1/G2/G4, and the fine-tuned checkpoint ft-v1 passes all of G0\~G7. The conditions for Go are as follows.

1. **Operating a fine-tuning pipeline**: maintain MASSIVE-format labeled data per domain taxonomy (on the order of 11,094 ko train rows), and retrain with `poc/finetune/run_full.sh` when the taxonomy or the wording changes (36 minutes on an idle M4 Pro GPU + 10 minutes of evaluation). For every new checkpoint, rerun Track B (test half, 1 time), C1 (flip) and E (coverage curve, re-selection of T), and leave a run card and an ADR.
2. **Serving configuration**: for the Korean channel, force `lang="ko"` + NFC normalization before inference (07 §6); ROUTE/FALLBACK with a single threshold T = 0.907 (dev-half curve of the 2,917-row test set, 5% error budget); general-like and low-confidence requests to FALLBACK (LLM or human); fixed option order in production; record the checkpoint SHA, `questions_sha256` and T in every log.
3. **Capacity**: laya-serve processes inferences one at a time, so the per-process ceiling is about 50 RPS for 1 question on MPS, 22.6 RPS for 3 questions, and 10 RPS for 3 questions on CPU. Beyond that, scale out by replicating processes (RSS about 2.1 GiB per checkpoint; MPS adds about 1.2 GiB of driver memory). Under intermittent traffic MPS latency grows 2\~3.6x and the gap to CPU narrows (D1c), so a CPU-only deployment is also an option. ONNX int8 is slower on this platform and changes 7% of the decisions, so it is not used (D7).
4. **Open items**: G2 on the 250-row test half is sensitive to how T is chosen, so coverage and error rate are re-checked on real traffic in the shadow stage early in operation; the LLM baseline (Track F2) was not run, so G1 was judged against the absolute criterion 0.80; for the identical utterances shared by train and test (155/2,917), the figure excluding them (0.908) is reported alongside.

---

## 7. Operational considerations

| Item | Setting / policy | Rationale |
|---|---|---|
| Resident checkpoints | stock laya-serve: `LAYA_PRELOAD=1`, `LAYA_MODELS=multilingual,english`, `LAYA_MAX_LOADED=2`. The option 1 app (`poc/service/app.py:48-60`) does not read these variables and builds `Router(models={"multilingual": "poc/finetune/ckpt_domain8_v1", "english": "models/laya"})` directly (ft-v1 preloaded, english loaded lazily). The Korean channel is pinned to `lang="ko"`, so the default affects only traffic with English mixed in (07 §4), `LAYA_DEFAULT_MODEL=multilingual` | a cold load takes a few seconds; `max_loaded=1` reloads for 7-10 seconds on every language switch (source: README.md "Production Preload & Memory") |
| Threads | `LAYA_THREADS` at or below the physical core count (M4 Pro: 10, based on its 10 performance cores), inter-op 1 | on a laptop CPU the inter-op default was 12x slower (source: BENCHMARKS.md §Laptop CPU) |
| Supply-chain pinning | `LAYA_REVISION=reviewed` or an explicit SHA; file digests verified with `LAYA_SHA256_DIGESTS` | source: laya/revisions.py `PINNED_REVISIONS`, `verify_digests` |
| Auth and proxy | `LAYA_API_KEY` required; `LAYA_ROOT_PATH` behind a reverse proxy | since 0.3.23 the internal status of `/health` also requires the bearer (#812) |
| Request limits | `MAX_CHOICE_OPTIONS = 100` (413), upper bound on `max_len`/`head_max_len` via `LAYA_MAX_TOKEN_BUDGET`, batch 64 states | source: README.md "Self-Hosting", laya/serve.py `_check_request_limits` |
| Overload | the client handles 503 + `Retry-After` with exponential backoff. The admission limit `LAYA_MAX_CONCURRENT` (laya/serve.py:158) is set from the P2 measurements | inference is serial on a single worker (comment at laya/serve.py:685) |
| GPU OOM | 0.3.23: the OOM fallback is isolated by a reader-writer gate; ordinary forwards proceed concurrently | source: README.md "What's new in 0.3.23" |
| Personal data | RedactHook masks before inference; no raw text in the shadow log; the log exists to preserve the rationale for decisions and creates no actions | source: docs/staged-adoption.md §1 |
| Linux deployment proxy | re-measure the same requests with the Docker CPU image (`compose.yaml`); for CPU-only hosts, compare ONNX int8 (Track D7) | source: docs/docker.md |
| Monitoring | abstention/FALLBACK rate (per domain), disagreement rate vs the incumbent, p95, number of LLM fallbacks, number of 503s, `routing.reason` (whether lang='ko' is pinned), checkpoint SHA and `questions_sha256` on every log line | docs/staged-adoption.md §4 checklist |
| Version drift | laya 0.3.23, torch 2.14.1, transformers 5.18.0, checkpoint 55cf4c4 pinned. Upgrades are approved only by rerunning the P1 commands + `laya-evals compare --baseline` | source: docs/evals.md "Baseline and CI gate" |
| Demo UI exposure | bound to 127.0.0.1, bearer required, not for production deployment | a review screen; executes no actions (source: docs/staged-adoption.md §1) |

---

---

## 8. Measurements and Go/No-Go mapping

| Measurement | Stage | Criterion (00 §6) | Output path |
|---|---|---|---|
| `ko_massive_domain_8` test half accuracy, macro-F1, 95% CI (G1) | P1 | within -5 points of the baseline, or 0.80 or higher | `results/B/20261002-1643_multilingual_ko_massive_domain_8.json`, `results/B/summary_20261002.md`. zero-shot 0.492 [0.432, 0.552], F1 0.468, fail → **ft-v1 0.900 [0.860, 0.936], F1 0.897, 0.893 excluding duplicates, pass** (`results/P4/metrics/full_20261003-1156_summary.md`) |
| `ko_klue_ynat_7` accuracy (secondary task) | P1 | reported item (secondary evidence for G1) | `results/B/20261002-1645_multilingual_ko_klue_ynat_7.json`. Measured test 0.655 |
| Korean penalty: ko vs en pairs with the same id (multilingual), McNemar | P1 | reported item (expected around the 0.10 level of 07 §5) | `results/B/summary_20261002.md` §2. Measured ko 0.526 vs en 0.510, p=0.47 (no penalty) |
| Rationale for the checkpoint choice vs english / typed-decisions / Router | P1 | multilingual ahead on Korean (H2) | `results/B/summary_20261002.md` §6. Measured: multilingual pinned |
| Per-domain recall, top confusion pairs, whether the first option is over-predicted | P1 | reported item (input for taxonomy revisions) | `results/B/summary_20261002.md` §5, `results/C/C_schema_v2_20261002.md`. First-option over-prediction rejected |
| option-order flip rate (`router_v1`) (G4) | P1 (Track C1) | 0.10 or lower | `results/C/C1_option_order_20261002.md`. zero-shot 0.270 (0.094 for decisions that pass the gate), fail → **ft-v1 0.037 (any-flip 0.084), pass** (`results/P4/metrics/full_20261003-1156_option_order_dev.md`) |
| in-process p95 (3 questions, MPS/CPU) (G5) | Track D1 | 100 ms / 500 ms or less | `results/D/D_summary_20261003.md` §1. Measured: multilingual short MPS 22.6 / CPU 57.8 ms, long 92.5 / 247.8 → **pass** |
| laya-serve p95 @ 10 RPS (3 questions, MPS) (G6) | Track D6 | 150 ms or less | `results/D/20261003-1330_http_mps.json`. Measured: p50 63.5 / p95 79.4 / p99 85.1 ms, 503 0 → **pass** |
| 503 rate, Retry-After, RSS, cold load | Track D6/D8/D3 | reported item | 0 503s (Retry-After path not exercised); RSS with 1 resident 2.07 GiB, 64-state batch peak +1.86\~5.49 GiB; cold load multilingual 3.45\~3.67 s (`results/D/D_summary_20261003.md`) |
| predict vs predict_batch(sort_by_length) parity (G7) | Track D4 | 0 flips, abs(delta p) 0.01 or less | `results/D/20261003-1314_batch.json`. Measured: CPU flip 0, max 0.0001; MPS fp16 flip 0, 0.0081\~0.0085 → **pass** |
| Demo UI behavior (all 5 single + 4 multi examples respond, argmax agreement with in-process/curl, warning and error states work, shadow view refreshes) | P2-UI | reported item (functional check). **Measured (2026-10-03): acceptance checks 11/11 ✔, 10 examples respond, 0 differences in the in-process check, `/poc/decide` round trip p50 20.1 / p95 21.1 ms** | `results/poc/P2_ui_check.md`, `results/poc/P2_20261003.md`, screenshots `results/poc/P2_ui_1.png` \~ `P2_ui_8_server_down.png` |
| ECE before/after refit (test half) (G3) | P3 | 0.10 or lower after refit | `results/E/E_summary_20261002.md`, `poc/calibration/ko_v1.json`. zero-shot 0.263 → 0.098 (pooled), borderline pass → **ft-v1 test 0.053, 2,917 rows 0.057, pass** |
| coverage @ error budget, single T (G2) | P3 | coverage 0.70 or higher at error 5% or less (the budget can be renegotiated) | `results/E/E_summary_20261002.md`, ADR. zero-shot 0.224 (10% 0.308, 15% 0.400), fail. Per-domain T rejected → **ft-v1 test half 0.756 with a post-hoc T / error 0.079 with the dev T; 2,917 rows with the dev T: coverage 0.923, error 0.042, pass (conditional)** (`results/P4/metrics/full_20261003-1156_coverage_*.md`) |
| ROUTE ratio × accuracy (estimated LLM call savings) | P3 | cost argument, no criterion | `results/poc/P3_coverage.md` |
| Accuracy before/after fine-tuning (domain_8 test half, with the duplicate-excluded figure), YNAT forgetting, G4 flip re-measurement | P4 | G1 0.80, YNAT drop within 0.03, flip 0.10 | `results/P4/P4_probe_20261002.md` (probe: test 0.492 → 0.720), main training run `results/P4/full_20261003-1156_*`. **Measured: test 0.900 (0.893 excluding duplicates), YNAT +0.021, flip 0.037, all met** |

Verdict rule: Go if accuracy, coverage, ECE and flip are all met. Conditional Go (premised on operating a fine-tuning pipeline) if only accuracy fails and P4 meets it. Conditional Go (renegotiated error budget or an accepted fallback rate) if only coverage fails. Conditional Go (premised on a change of deployment hardware) if only latency fails. No-Go if accuracy and coverage still fail after P4.

---

## 9. Risks and mitigations

| Risk | Evidence | Mitigation |
|---|---|---|
| Low Korean zero-shot accuracy | **Measured (2026-10-02)**: domain_8 0.49\~0.56 (test/dev), YNAT 0.63\~0.66, scenario_18 0.52, intent-20 0.470. Cannot be improved with the 6 schema wording variants (`results/C/C_schema_v2_20261002.md`) | G1 failure confirmed. The remaining paths are P4 fine-tuning (MASSIVE ko train 11,514 rows) or a change of the task contract (summing v1 probabilities into 5 classes: dev 0.682). Owner decision |
| G2 depends on G1 | At accuracy a, the upper bound of coverage with error e or less is a/(1−e). With a=0.492 and e=0.05 it is 0.518, so 0.70 cannot be reached through calibration (`results/E/E_summary_20261002.md`) | Without improving G1, only renegotiating G2 is possible (budget 10%: 0.308, 15%: 0.400) |
| Confident errors from overlapping domain definitions | P0c: play↔music 14/17, audio→general, iot→alarm. Not filtered out by the gate | 8-domain merge (§4), the builder's description-vocabulary intersection check, top confusion pairs reported in P1 and re-merged in v2 |
| (on-hold A) noul follows the label instead of the state; misjudges negations | #156, #377, P0b: no noul form beat the always-no base rate in total; 07 §5: the same with English input (a checkpoint property) | v1 has no noul. If A is revived through P4, this is handled with per-question decision thresholds (03 E6) and fine-tuning |
| (on-hold A) weak score, multilingual first-level bias | SST-5 0.372, #131, P0b level 0 picked 0/30 | v1 has no score. In A, only as an auxiliary signal |
| option-order flip | **Measured**: router_v1 0.270 per permutation (any-flip 0.512), ynat 0.168. 74% of the flips come from incorrectly answered items, and the flip of decisions with confidence ≥ 0.9 is 0.094. First-option position bias rejected (`results/C/C1_option_order_20261002.md`) | fixed option order in production. The G4 definition (per permutation vs decisions that pass the gate) is an open question. Not improved by rewriting descriptions or reordering (v2a\~v2e) |
| Thermal throttling of a laptop-class SoC | performance-core clocks may drop under a 60-second load | idle measurements before and after the load, record clocks with `powermetrics`, median of 3 repetitions |
| Numerical differences between MPS fp16 (5 rows or more) and CPU fp32 | `mps_amp_min_rows` defaults to 5 (source: laya/agent.py) | P0/P2 parity gate; if needed, force fp32 with `LAYA_MPS_AMP_MIN_ROWS` and re-measure latency |
| laya-serve single-worker serial inference and 503 | create_app comment (laya/serve.py:685 onward) | measure the saturation RPS in P2; if needed, estimate the cost of process replication (checkpoint memory x N) |
| Change in the hooks injection path | depends on the `create_app(router)` signature | re-check at the start of implementation; keep option 2 as the alternative |
| Taxonomy drift | changing the wording or merge rule after looking at dev results contaminates the test half | the merge rule is fixed in §4; changes go into `router_v2.json` + a rebuild; the test half is evaluated only 1 time, at the end |
| Version drift | laya is released weekly (0.3.18 → 0.3.23 took 1 week) | the pinned versions of 02; upgrades only when the baseline compare passes |
| Routing failures on mixed text | mixed text with a Latin majority and short Korean inside an English wrapper go to english (10 failures in the 46-case battery, 07 §4) | the Korean channel sets `lang="ko"` explicitly; routing results are kept in the shadow log for monitoring |
| NFD input | without NFC normalization, NFD Korean takes 3.09x the tokens and is broken into jamo and byte fragments (07 §3) | `unicodedata.normalize("NFC")` in RedactHook or at the server entry |
| An edge over Jev presupposes fine-tuning | in the n=24 manual comparison, zero-shot 0.417 is below Jev 0.833, and only ft-v1 0.917 is on par with Jev (`results/F/jev_playground_manual_20261006.md`) | build the adoption argument not as "a zero-shot replacement" but as "a locally fine-tuned router (latency 20 ms, cost 0)". A formal comparison: 500 paired rows once a Jev API key is obtained |

---

---

## Open questions / assumptions

1. **Decided: C (domain router), 2026-10-02.** Main task `ko_massive_domain_8`, secondary `ko_klue_ynat_7`. A is on hold as a P4 fine-tuning candidate (§2).
2. **G2 error budget.** The 00 §6 default is coverage 0.70 at 5% error. Judging from P0c's YNAT figures (14% error at 50% coverage), 5% may be hard to reach. Whether to change it to 10% or to accept the fallback rate is decided by the project owner after looking at the P3 curve.
3. **Optional hand-written set.** Whether to add 100 "real queries" for the finalized taxonomy (real-service style, no PII) to P1. MASSIVE consists of voice-assistant utterances, so the distribution differs.
4. **Handling `general`.** Whether to keep it as ROUTE (chat handler) or always send it to FALLBACK. Decided after looking at the `general` precision in P1.
5. **Closed: P4 done (2026-10-03).** After the G1 failure (domain_8 test 0.492) was confirmed, the project owner chose fine-tuning, and the main training run (run `full_20261003-1156`) gave test 0.900, flip 0.037 and ECE 0.053. Train/test duplicate rows are handled by reporting both figures (0.893 excluding duplicates), and option-order shuffle augmentation is kept as the basis for passing G4 (§6 P4).
16. **ft-v1 adopted as the P2 service checkpoint.** `LAYA_MODELS` of `laya-serve` accepts only checkpoint names (laya/serve.py:667-668), so the fine-tuned checkpoint is attached in `poc/service/app.py` with `Router(models={"router": "poc/finetune/ckpt_domain8_v1", ...})` or by loading it directly with `laya.load("poc/finetune/ckpt_domain8_v1")`. The service T is set from the 2,917-row coverage curve (5% budget T ≈ 0.90) and recorded in the ADR together with the checkpoint sha256 and questions_sha256.
6. **Whether to use an LLM baseline.** With an Anthropic API key, the `claude-haiku-4-5-20251001` baseline is measured with the Track F protocol; without one, the verdict uses the absolute criterion (0.80). Costs and unit prices are recorded in the run card from the official pricing page at run time.
7. **Access to the Router's internal agent.** Calibration is applied by default via `laya.load(..., calibration=...)` + `router.attach()`. Applying `apply_calibration_payload` directly to the agent held by the Router is used only after confirming the name of the Router's internal attribute.
8. (Confirmed) The admission-limit environment variable of `laya-serve` is `LAYA_MAX_CONCURRENT` (laya/serve.py:158 `_resolve_max_concurrent`). Its value is set from the P2 measurements.
9. **Replicating TCP_NODELAY (resolved).** Starting uvicorn directly in option 1 drops `NoDelayHTTPProtocol`, but the P2 measurement showed an HTTP overhead of p95 0.7 ms and no visible Nagle delay. Replication is left optional.
10. **Demo UI auth.** Whether the `/poc/*` routes share laya-serve's `LAYA_API_KEY` bearer as is or get a separate token. The default is sharing (it is a local review screen, so one key is enough).
11. **Whether to include screenshots.** Whether to put `results/poc/P2_ui_*.png` into REPORT.md and the dashboard, or to keep only the checklist (`P2_ui_check.md`).
12. **Demo gallery scope.** Whether to add to the PoC scope demos corresponding to jevplayground's 9 task demos. The default is only the 3 "PoC 시나리오로 시험하기" (try it with the PoC scenarios) cards, and a backlog bulk-routing demo can be appended later as a separate card that uses `/v1/systemone/batch`.
13. (Confirmed) **Fine-tuning data adapter.** For choice, the gold of `build_training_item` is `{"probabilities": {key: p}}` keyed by the criteria key, so it is 1:1 with our `expected` (§6 P4, `results/P4/P4_probe_20261002.md`). The adapter `poc/finetune/make_domain8_items.py` is implemented.
14. **G4 definition.** 00 §6's "flip rate ≤ 0.10" did not specify whether it means the per-permutation flip or any-flip. Either way it fails (0.270 / 0.512), but redefined as "the flip of decisions that pass the gate (confidence ≥ T)" it passes at 0.094. Whether to redefine it is an owner decision.
15. **Calibration payload form.** The type scalar `[1.9161, 1, 1]` also applies T to other choice questions that were not validated. Whether to restrict it to `{"choice:6-10": 1.9161}` is chosen in the ADR (the router_v1 output is the same under both forms).

**English** | [한국어](05_poc_plan.ko.md)
