# Laya analysis: architecture, API, published numbers, limits (01_laya_analysis)

**Purpose**: A summary of the facts about Laya on which the benchmark and PoC designs rest. Every number written here is an upstream published number; values we will measure are marked "to be measured".
**Prerequisite documents**: `00_README.md`.
**Outputs**: a summary of the checkpoints·API surface, a table of upstream numbers, the Honest limits → Track mapping, M4 Pro expectations (hypotheses), hypotheses H1-H10.

The subject of the analysis is laya 0.3.23, upstream commit `4aa6761` (2026-10-01). File·line citations refer to that commit and can be checked in `third_party/laya/` (not included in the public repository; recreate it by cloning https://github.com/NandhaKishorM/laya at commit 4aa6761).

## 1. One-line summary and positioning

Laya is a "multilingual, non-autoregressive System 1 decision engine" (source: the opening of README.md). It takes a state (text·email·JSON) and a bundle of typed questions (choice / score / noul) and returns a per-question probability distribution from a single encoder forward pass. There is no text generation, so there is nothing to parse and nothing to hallucinate. It was trained with RLCD (RL that uses a strictly proper scoring rule as the reward), and on that basis it claims its probabilities are calibrated. Apache 2.0, runs fully locally.

A summary of the positioning table in docs/use-cases.md (source: docs/use-cases.md "Decision Engine vs. LLM vs. Embedding Retrieval"):

| Axis | Embedding retrieval | Laya | Autoregressive LLM |
|---|---|---|---|
| Computation | vector cosine | 1 forward pass, no decoding loop | sequential token generation |
| Hosting | in-process / vector DB | in-process (CPU/GPU) or self-hosted HTTP | remote API or large-GPU serving |
| Input attention | pooled vector | bidirectional attention over the whole input | causal |
| Output | unstructured chunks | schema-aligned distributions (choice/score/noul) | free text, needs JSON repair |
| Main use | candidate retrieval | classification·policy gates·routing | generation·summarization·translation |

There are four reasons it is worth benchmarking. (1) Latency: 32.8 ms for 1 question on a T4, 6-7× compared with Jev's 3rd-party published 236-276 ms (source: README.md "Benchmarks"). (2) The claim that its probabilities can be used for gating. (3) Local execution, so data does not leave the machine. (4) Apache 2.0 weights.

The biggest caveat is one upstream wrote down itself. The base checkpoints are near chance zero-shot on the typed-decisions benchmark (0.362 / 0.352, random 0.318, majority 0.461), and 0.766 is the number of a checkpoint fine-tuned on that benchmark's training split. "Laya is a fast base to specialise, not a zero-shot decision engine" (source: README.md "Honest limits"). Our benchmark measures exactly this boundary: "how far can it be used zero-shot in Korean?"

## 2. Architecture

**Encoder + decision head.** english and typed-decisions put a decision head on ModernBERT-large (421M, context 512 / 1024), and multilingual on mmBERT-base (322M, default 1024, up to 8,192 with RoPE) (source: the checkpoint table in README.md). Each question becomes one row of the forward pass, and the questions of one call form one batch of rows that repeat the same state. So "bundling questions into one call" is the source of GPU throughput, while on CPU the cost grows almost linearly with the number of rows (source: the description in examples/36_batch_throughput.py, BENCHMARKS.md §Server CPU).

**Sequence construction and token budget.** Each row is built from `"<type> question: <instructions>"` + option rendering (head) + state. The budget rules are as follows (source: README.md "Honest limits"; implemented in `build_sequence` / `render_options` of `laya/common.py`):

- `head_max_len` is an **upper bound** on the head, not its length. Defaults: english 192, multilingual·typed-decisions 256.
- The actual head length uses only as much as the question and option explanations need, and the room left for the state is `room = max_len - head_len - 1`. upstream's example: on english, the department question's head is 48 tokens, so 463 tokens remain for the state (not the 320 computed from the cap).
- Tokens per option are `per = max(4, (head_max_len - 16) // k)`. When the number of options k exceeds roughly `head_max_len / 4`, the head grows **past** the cap and the state gets truncated.

| Checkpoint, max_len | k options | head | Actual room | Value by the cap |
|---|---|---|---|---|
| laya, 512 | 77 | 319 | 192 | 320 |
| laya, 512 | 100 | 411 | 100 | 320 |
| laya-multilingual, 1024 | 100 | 411 | 612 | 768 |

(Source: the table in README.md "Honest limits", upstream published numbers.) This rule is why banking77 (77 labels) collapses to 0.425. There are three mitigations: raising `head_max_len` / `max_len` per call, embedding-based top-k narrowing with `predict_shortlist`, and splitting the question into two stages, coarse/fine. With 58 MASSIVE labels in one question, upstream reported 24/58 → 34/58 with `--head-max-len 384`, at 1.4× the CPU time (source: README.md "Command line").

**Temperature.** When a checkpoint is loaded, the temperature per `(question type, option-count bucket)` is clamped to `[0.5, 5.0]` (source: README.md "Calibration", `laya/common.py` TEMP_MIN / TEMP_MAX). multilingual ships with no fitted temperature.

**Answer dict.** Keys of the per-question answer dict, per `laya/agent.py:1213-1244`:

| Key | Per type | Meaning |
|---|---|---|
| `choice` / `score` / `noul` | choice: the label; score: the expected level (on a 0-based index scale); noul: P(true) | The answer |
| `probabilities` | choice: label→p, score: index→p | Distribution |
| `legend` | score only | index→level description |
| `confidence` | all types | choice/score: 1 - normalized entropy; noul: max(p, 1-p). Moves with the number of options |
| `answer_confidence` | all types | The probability of the reported answer, max p. This is what is calibrated, and gating uses this value |
| `action` | all types | Includes `act_probability`. upstream states it has "no usable signal" (#185: almost always 1.0, AUROC 0.30 vs confidence 0.77) |

At the call level there are `usage.input_tokens / output_tokens`; via the Router, `routing.model / repo / reason`; for `predict_long`, `usage.windows`; and with `min_confidence`, `low_confidence`, `abstention` and `abstention_threshold` (source: README.md "Quickstart", "Opt-in abstention").

## 3. Checkpoints and the Router

| Name | encoder | params | context | Use | Weight size | HF path | pinned SHA |
|---|---|---|---|---|---|---|---|
| english (`laya`) | ModernBERT-large | 421M | 512 | English | 842.6 MB | `convaiinnovations/laya` (root) | `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` (bundle repo) |
| multilingual | mmBERT-base | 322M | 1024 (up to 8,192) | 100+ languages, about 2× the speed of english | 643.8 MB + tokenizer 34.4 MB | bundle `convaiinnovations/laya/multilingual`, standalone `convaiinnovations/laya-multilingual` | standalone repo `e4e9ddf21a7b1903b7acffd8814ad4307bf63a67` |
| typed-decisions | ModernBERT-large | 421M | 1024 | the 4 typed-decisions workflows (English) | 842.6 MB | bundle `.../typed-decisions`, standalone `convaiinnovations/laya-typed-decisions` | standalone repo `1a793eb568e6718f15941d08f85432581df534e3` |

(Sizes are from the HF API; the whole bundle is 2.37GB. Source of the pinned SHAs: `laya/revisions.py` PINNED_REVISIONS.) The safetensors size is 2 bytes per parameter, so the weights are stored in bf16/fp16 and are loaded as fp32 on CPU/MPS.

**Router behavior** (source: README.md "Quickstart: Route Mode", `laya/lang.py`, `laya/router.py:511-525`):

- Script detection comes first. Hangul is caught by the `hangul` range in `laya/lang.py:43` (U+1100\~11FF, 3130\~318F, AC00\~D7AF), and **pure Hangul goes to multilingual**. The observed reason is "non-Latin script (hangul, 100% of letters); the English checkpoint cannot read it" (02 §3.1). However, mixed text with mostly Latin letters (F1, e.g. "Stripe webhook이 timeout 나요") and Korean of fewer than 10 syllables inside dict fields·conversation turns (F2) go to english because of the thresholds in `lang.py:364-371` (non-Latin share 0.2, or 0.1 with at least 10 letters). In the 46-case battery 10 cases failed, and only `lang="ko"` fixes them all (`07_korean_support_audit.md` §4).
- For Latin script, a function-word heuristic decides whether the text is English. Short Latin text has no evidence, so it falls to `default` (default `"english"`). In Korean-centric traffic, to keep short inputs with only English letters (e.g. "ok", product codes) from going to english, use `Router(default="multilingual")` or `LAYA_DEFAULT_MODEL=multilingual`.
- Priority: explicit `model=` > `task=` > `lang=` (skips detection) > `lang_guess` (a code or a callable; decides only English/non-English) > detection > `default`.
- Memory: default `max_loaded=2` (english + multilingual LRU). With `max_loaded=1`, every language change triggers a reload, costing a median of CPU 7.4 s / T4 10.3 s. With `preload=True`, all three stay resident. The tokenizer is parsed once per process and reused (multilingual tokenizer.json 34 MB) (source: README.md "Production Preload & Memory").
- `Router.predict_batch` first routes everything, groups by checkpoint and, within that, by question schema·token budget, sends the groups to `Agent.predict_batch`, and restores the results to the original order. Questions whose `instructions` differ by even one character are in different groups.
- Revision pinning: `Router(revision=...)`, `revisions={...}`, or the environment variable `LAYA_REVISION=reviewed` (applies PINNED_REVISIONS) (source: `laya/revisions.py`).

## 4. API surface

**SDK** (source: README.md, `laya/__init__.py` `__all__`):

| API | Gist |
|---|---|
| `laya.load(id_or_path, device=, subfolder=, revision=, fast=, compile=, calibration=)` / `Agent` | Loads a single checkpoint. Also accepts aliases such as `"english"`, `"ml"` (`laya/agent.py:1867`) |
| `Router(models=, device=, revision=, max_loaded=2, default="english", preload=False, lang_guess=, hooks=)` | Routing entry point. `route()` returns only the decision, without a forward pass (`laya/router.py:511`) |
| `predict(state, questions, model=, lang=, lang_guess=, min_confidence=, max_len=, head_max_len=)` | A bundle of questions in one pass. `system_one` is the same |
| `predict_batch(states, questions, batch_size=, sort_by_length=, min_confidence=)` | Several states for the same questions. `sort_by_length` has an effect only when `1 < batch_size < len(states)` (`laya/agent.py:1250`) |
| `predict_long(state, questions, window=, stride=)` | Window scan over a long state. noul takes the max, choice/score the highest-confidence window; `answer["window"]` reports the evidence span |
| `decide(state, schema=)` / `decide_batch` | Converts a JSON schema or a pydantic model (`laya[structured]`) into questions and returns typed values; `return_details=True` gives per-field confidence |
| `predict_shortlist(agent, state, questions, embed_fn=, k=)` / `embed_fn_from_agent` / `cached_embed_fn` | Narrows a high-cardinality choice to an embedding top-k, then one pass. `laya.evals_shortlist.evaluate_shortlist` reports retrieval misses / decision misses separately |
| `fit_temperature_map(records)` / `records_from_labeled(agent, pairs)` / `calibration_payload` / `apply_calibration_payload` | Fits per-bucket temperatures from labeled pairs. Bucket floor `MIN_BUCKET_N=2000`, type floor 10 (source: the module docstring of `laya/calibrate.py`) |
| hooks | `on_predict_start / on_predict_end / on_route / on_load / on_evict / on_error`. The start hook can rewrite the state·call `ctx.skip()`, the end hook rewrites the result. `hooks_raise=True` by default |
| `min_confidence` | If `answer_confidence < T`, then `low_confidence: True`. Every answer of a call given a threshold gets `abstention` ∈ {passed, abstained, unevaluated} and `abstention_threshold`. Without one, the payload is unchanged |

**Presets** (source: `laya/presets.py`). All of them name a specific key of the state in backticks (`message`, `body`, `prompt`, `post`, `request`), and `state_field(questions)` returns that key. The Korean PoC must rewrite the instructions and criteria in Korean, so the presets are not used as is; only their structure serves as a reference.

| preset | Questions |
|---|---|
| `triage_questions()` | intent(choice 6: refund, technical_help, billing_question, information, cancellation, other), is_urgent(noul), frustration(score 4), refund_requested(noul), churn_risk(noul) |
| `email_questions(categories=)` | category(choice 6: billing, technical, sales, security, hr, other), is_spam(noul), is_phishing(noul, criteria true/false stated explicitly), urgency(score 3), needs_reply(noul) |
| `guard_questions()` | jailbreak, prompt_injection, sensitive_data (3 noul), harm_severity(score 4), topic(choice 6, no explanations) |
| `moderation_questions()` | toxic, harassment, threat, spam (4 noul), severity(score 4) |
| `router_questions()` | difficulty(score 4), domain(choice 6: code, math_or_logic, writing, factual_lookup, data_analysis, chitchat), needs_tools(noul), is_sensitive(noul) |

**CLI / HTTP / other surfaces**:

| Surface | Gist |
|---|---|
| `laya "..."` | By default only the routing decision (no download). `--predict`, `--preset`, `--questions FILE`, `--batch FILE [--batch-size N --sort-by-length --json]`, `--model`, `--lang`, `--lang-guess`, `--min-confidence`, `--max-len`, `--head-max-len` (source: README.md "Command line") |
| `laya-evals validate / run / compare` | Evaluation of JSONL label sets. `run --model --device --batch-size --sort-by-length --min-confidence --revision --onnx --calibration --slice {language,model,qid,tag} --baseline --tolerance M=V --min-accuracy --max-ece --score-within --min/--max M=V --gate-policy --on-error --json --markdown` (`laya/evals_cli.py:151-215`). Metrics: choice_accuracy, noul_accuracy, score_mae, score_within_t, ece (15 bins, on `answer_confidence`), mean_confidence, latency_p50/p95_ms, cost_per_decision_p50/p95_ms. The report `config` has dataset_sha256, questions_sha256, laya_version, revisions, thresholds (source: docs/evals.md) |
| `laya-serve` | FastAPI. `POST /v1/systemone`, `POST /v1/systemone/batch` (states ≤ 64), `GET /health` (`laya/serve.py:755, 818, 905`). The same wire protocol as Jev. Environment variables `LAYA_HOST / PORT / DEVICE / PRELOAD / MODELS / THREADS / AUTO_TASK / DEFAULT_MODEL / MAX_LOADED / API_KEY / ROOT_PATH / MAX_TOKEN_BUDGET`. More than 100 choice options gives 413 (`MAX_CHOICE_OPTIONS = 100`), hook arguments give 422, busy gives 503 with `Retry-After` (source: README.md "Self-Hosting") |
| `laya-mcp-server` | stdio MCP server (`laya[mcp]`). `laya_predict_batch`, `laya_route_batch`, `laya_decide`, etc. (source: README.md "What's new in 0.3.21") |
| `examples/server.py` | Web GUI playground + `/predict`, `/predict/batch` JSON API (`laya[serve]`) |
| ONNX | `scripts/export_onnx.py --model --output [--quantize] [--per-channel]`. `--quantize` defaults to per-tensor INT8 (per-channel collapses to 32% agreement with eager, README "What's new in 0.3.23"). `ONNXAgent` provides predict / predict_batch / predict_long / decide_batch; `laya-evals run --onnx`. upstream fixture (12 rows, english, CPU) p50: torch 116.8 ms, onnx fp32 66.3 ms, int8 46.3 ms, identical accuracy, score_mae +0.009, ece +0.006 (source: docs/evals.md "Evaluating an ONNX export") |
| TileLang fast path | `laya[fast]`, `load(..., fast=True)`. CUDA only; CPU/MPS fall back to the stock forward. Cannot be measured on this Mac |
| TypeScript | `laya-ts` (local ONNX inference in the browser/Node), `laya-client` (`sdk/typescript`, an HTTP client for laya-serve) |
| Docker | `compose.yaml` (CPU), `compose.cuda.yaml`, `compose.spark.yaml` (GB10/aarch64), `compose.modelscope.yaml`, `compose.http.yaml`. The CPU quickstart needs 8GB RAM, 10GB disk (source: docs/docker.md) |
| Example·verification scripts | 41 learning-path scripts in `examples/` (17 timing, 33 high cardinality, 34 temperature, 35 device, 36 throughput). In `verify/`: `bench_devices.py`, `soak_check.py`, `numerics_check.py`, `edge_sweep.py`, `laya_smoke_test.py`. In `research/scripts/`: `bench_local.py` (MASSIVE, 51 languages), `bench_apps.py`, `bench_latency.py`, `bench_length_batching.py`, `bench_long_context.py`. The research scripts expect the directories `laya/`, `laya-multilingual/`, `laya-typed-decisions/` under `LAYA_MODELS` (source: research/README.md) |

## 5. Published benchmark numbers (upstream)

All of these are numbers upstream published. The Jev numbers are **3rd-party published values, not upstream measurements**, with different sample sizes and prompts (source: the opening of BENCHMARKS.md, research/README.md "On comparisons with Jev").

**(a) MASSIVE intent, 51 languages, 20 options (random 0.050)** (source: BENCHMARKS.md §Languages, refreshed rerun values. The committed multilingual file did not reproduce and was replaced with the refreshed one, #208)

| | laya | laya-multilingual |
|---|---|---|
| macro accuracy | 0.2269 | 0.4008 |
| macro ECE | 0.5709 | 0.3911 |
| Languages above 3x random | 23 / 51 | 48 / 51 |
| `ko` accuracy / ECE | 0.110 / 0.680 | **0.470 / 0.311** |
| `en` accuracy / ECE | 0.820 / 0.138 | 0.710 / 0.233 |
| `zh-CN` accuracy / ECE (0.3.20 rerun, per-lang 100) | 0.620 / 0.320 | 0.650 / 0.219 |

The zh-CN row holds the Part A rerun values from §Community evaluation. The English checkpoint is confidently wrong on non-Latin scripts: Khmer has 0.000 accuracy with raw confidence 0.952 (0.705 after the clamp) (source: BENCHMARKS.md §English vs the rest).

T4 Colab set (MASSIVE 14 languages, XNLI 15 languages) (source: BENCHMARKS.md §English vs the rest, in the order laya / multilingual): MASSIVE intent en 0.783 / 0.657, others 0.306 / 0.451. MASSIVE scenario en 0.603 / 0.560, others 0.281 / 0.439. XNLI en 0.860 / 0.843, others 0.521 / 0.731.

**(b) typed-decisions, 400 cases, 2,000 decisions** (source: BENCHMARKS.md §typed-decisions)

| Model | accuracy | soft acc | Brier | ECE | score MAE |
|---|---|---|---|---|---|
| laya-typed-decisions (fine-tuned) | 0.766 | 0.471 | 0.061 | 0.213 | 0.242 |
| laya | 0.362 | 0.332 | 0.316 | 0.175 | 0.694 |
| laya-multilingual | 0.352 | 0.328 | 0.463 | 0.314 | 0.760 |
| Jev 1.13.0 (3rd-party published) | 0.727 | 0.580 | 0.148 | 0.144 | 0.391 |
| teacher upper bound / majority / random | 0.735 / 0.461 / 0.318 | | | | |

**(c) Applied-workflow Themes, N=400, laya 0.2.1, CPU** (source: BENCHMARKS.md §Themes)

| theme | laya | multilingual | typed-decisions | Data |
|---|---|---|---|---|
| Email spam | 0.993 | 0.993 | 0.958 | in training |
| Phishing | 0.980 | 0.993 | 0.940 | in training |
| LLM guardrails (jailbreak) | 0.708 | 0.755 | 0.762 | held out |
| Moderation (toxicity) | 0.530 | 0.525 | 0.530 | held out (macro-F1 0.400) |
| RAG passage relevance | 0.625 | 0.657 | 0.625 | in training |
| Support triage (10-way) | 0.502 | 0.522 | 0.505 | in training |
| Model routing (domain) | 0.639 | 0.123 | 0.659 | held out |

**(d) Public datasets with published Jev numbers** (source: BENCHMARKS.md §On the public datasets where Jev numbers exist)

| Dataset | laya | multilingual | typed-decisions | Jev (3rd party) |
|---|---|---|---|---|
| AG News (4) | 0.950 | 0.930 | 0.953 | 0.910 |
| DAIR Emotion (6) | 0.595 | 0.530 | 0.600 | 0.480 |
| banking77 (77. Jev: 72) | 0.425 | 0.425 | 0.492 | 0.870 |

**(e) Speed, Tesla T4** (source: BENCHMARKS.md §Speed)

| Questions/call | laya | laya-multilingual |
|---|---|---|
| 1 | 39.5 ms | 32.8 ms |
| 5 | 84.5 ms | 40.1 ms |
| 10 | 158.6 ms (15.9 ms/q) | 72.3 ms (7.2 ms/q) |
| 50 | 771.3 ms | 337.4 ms |

Batch throughput 103-332 questions/s. Jev 3rd-party measurement p50 236-276 ms.

**(f) Calibration** (source: BENCHMARKS.md §Calibration): shipped ECE laya 0.466 → refit 0.081, multilingual 0.314 → 0.106. The refit uses one temperature per (question type, option count) bucket, fitted on held-out data.

**(g) option-order flip rate** (source: BENCHMARKS.md §Option-order robustness, in the order laya / multilingual): massive_intent.en 0.150 / 0.230, en.emotion 0.040 / 0.090, xnli.en 0.000 / 0.015. Jev 3rd-party measurement 0.13.

**(h) zh community bench, the closest precedent for what we will build in Korean** (source: BENCHMARKS.md §Community evaluation, laya 0.3.20 CUDA, acc / ECE)

| Task (n) | multilingual | english |
|---|---|---|
| voice routing, 6-domain (179) | 0.883 / 0.061 | 0.754 / 0.281 |
| CS routing (25) | 0.640 / 0.293 | 0.520 / 0.184 |
| urgency score (25) | 0.560 / 0.091 | 0.520 / 0.207 |
| scam/promo (15) | 0.667 / 0.311 | 0.667 / 0.321 |
| escalate noul (40) | 0.550 / 0.230 | 0.575 / 0.269 |

option-order flip 28% (CS) / 10.6% (voice); flip on zh-CN → zh-TW parallel utterances 12.8%. In the temperature refit, the raw T 10.23 of the `noul:2` bucket hit the clamp ceiling 5.0 (ECE 0.180 → 0.098), and `choice:6-10` actually got worse after the refit, 0.062 → 0.093. This means the refit overfits easily at small n, and it is the rationale for the held-out design of our Track E.

## 6. Honest limits → mapping to our benchmark

| Limitation | upstream evidence | Track / probe where we test it |
|---|---|---|
| The base checkpoints are near chance on zero-shot typed-decisions | 0.362 / 0.352 vs random 0.318, majority 0.461 (source: README.md "Honest limits") | Report majority/random baselines alongside every Track B set. Check the zero-shot ceiling on `ko_poc_triage_v1` |
| head budget collapse above 20 options | banking77 0.425, `per = max(4, (head_max_len-16)//k)` (source: README.md "Honest limits") | Track C: compare the default budget vs `head_max_len=512, max_len=1024` vs `predict_shortlist(k=20)` on `ko_massive_intent_full60.jsonl` |
| noul follows the labels instead of the state (worst on english) | #156: criteria take only true/false keys, notation changed to `labels`, noul without criteria is always "no" on english (source: README.md "Honest limits") | Track C: run and compare four variants on `ko_nsmc_sentiment.jsonl`: noul+criteria (canonical) / `--opaque-labels` (labels A·B) / 2-choice with semantic keys (positive·negative) / `--opaque-keys` (A·B) (04 §5.4). The PoC schema's criteria-less noul vs `triage_v1b.json` (+criteria) is the Track C2 ladder |
| Negation failure | #377: all 4 negated cancellation requests pick `cancel_account` (laya), 2 on multilingual, one at p=0.9998 (source: README.md "Honest limits") | Track C: `ko_negation_probe.jsonl` (affirmative control group + negation pairs) |
| No boolean-word labels (true/false, yes/no) | The label strings are rendered as is (source: README.md "Honest limits") | Reflected as a design rule for every Korean schema (`04_korean_evalset_spec.md`). No separate probe |
| multilingual's bias against the first score level | #131, all languages (source: README.md "Honest limits") | Track C: compare the level distribution vs the gold distribution on the frustration/urgency scores of the triage schema; reverse the level order |
| Over-confident as shipped; multilingual has no temperature | ECE 0.466 / 0.314 as shipped (source: BENCHMARKS.md §Calibration). One routing task, however, is under-confident (source: BENCHMARKS.md §Other hardware "Calibration on a routing task") | Track E: measure the shipped ECE → refit with `fit_temperature_map` → held-out ECE, coverage@error curves. Record the direction (over/under) per set |
| option-order instability | 0.150 / 0.230 at 20 options (source: BENCHMARKS.md §Option-order robustness) | Track C: permutation flip rate on `ko_klue_ynat_7`, `ko_massive_intent_20opt` and the PoC schema |
| moderation is weak on held-out data | 0.530, macro-F1 0.400 (source: BENCHMARKS.md §Themes) | Track B: Korean hate-speech noul/choice with `ko_kmhas_hate.jsonl`. Risk evidence for PoC option B |
| Adding criteria·scenarios·a JSON state pushes noul to always-true (zh) | noul_plain 0.667 → noul_json_state 0.417 (the same as the always-true baseline) (source: research/benchmarks/zh_short_commands/README.md) | Track C: reproduce the same ladder with 18-30 short Korean commands (plain / criteria / scenario / json_state) |
| Long documents are position-sensitive; positions inside the document sit at the majority floor | With 4,000 tokens of filler, pos 0.25 0.550 vs pos 1.00 0.950, n=20 (source: research/README.md "Headline findings") | Track C, optional: compare `predict_long` vs a single window only if the PoC scenario has long inputs |
| `act_probability` carries no signal | #185 AUROC 0.30 (source: README.md "Honest limits") | Not measured. Gating uses only `answer_confidence` |
| Cost linear in the number of questions on CPU | EPYC 4 cores: english \~600 ms/question, multilingual \~185 ms/question. GPU is sub-linear (source: BENCHMARKS.md §Server CPU, §Speed) | Track D: scaling curves over 1/3/5/10 questions on CPU vs MPS |

## 7. Reference latencies by hardware and M4 Pro expectations

**upstream published measurements.** All are measurements by upstream or contributors under different conditions, so they are not compared with each other directly.

| Environment | Conditions | Numbers | Source |
|---|---|---|---|
| Tesla T4 | in-process, 1 / 10 questions | multilingual 32.8 / 72.3 ms, english 39.5 / 158.6 ms | BENCHMARKS.md §Speed |
| AMD EPYC 9R14, 4 cores (m7a.xlarge), fp32, torch 2.14.0 | in-process, 1 / 5 / 10 / 50 questions | english 580 / 3,072 / 6,244 / 35,969 ms, multilingual 193 / 912 / 1,842 / 11,157 ms. cold load 4.4 s / 2.5 s. Whole-script peak RSS 9.3 GiB (up to 5 loaded) | BENCHMARKS.md §Server CPU |
| Ryzen 9 6900HX, WSL2 (checkpoint not stated) | 3 questions over HTTP, torch default threads → intra 8 + inter-op 1 | p50 9,396 ms → 783 ms (12x). in-process 1 question, 8 threads: p50 329 ms, p95 378 ms | BENCHMARKS.md §Other hardware |
| Intel Arc B390 XPU vs the same laptop's CPU, english | 1 / 3 / 10 questions | XPU 29.7 / 45.4 / 96.9 ms, CPU 288.2 / 730.6 / 2,608.7 ms | BENCHMARKS.md §Other hardware |
| NVIDIA GB10 (DGX Spark), over HTTP, typed-decisions | 1 / 50 questions | p50 100.2 / 443.1 ms, \~7.0 ms per question, fixed overhead \~93 ms | BENCHMARKS.md §Other hardware |
| NVIDIA RTX, TileLang fast path (see that section for the GPU model) | 1 question of 72 tok, stock → fast | english 17.7 → 4.6 ms, multilingual 14.1 → 2.8 ms | BENCHMARKS.md §GPU fast path |
| H100 NVL, TensorRT FP16 serving (external study) | p99 ≤ 50 / ≤ 130 ms SLO | 105 / 175 decisions/s. RTX PRO 6000: 146 decisions/s @ 130 ms | BENCHMARKS.md §Independent NVIDIA CUDA capacity study |
| Apple GPU (MPS), multilingual max_len=8192 | 4,000-token input | about 1.7 s | README.md "Quickstart" note on long documents |
| Apple silicon, CLI `--batch` 128 Yelp reviews, batch 8 | unsorted vs sorted | 41.25 s → 29.23 s (1.42x), 0 decision changes | README.md "Command line" |
| Apple M-series MPS, `decide_batch` 8 tickets | individual calls vs batch | 2,624 ms → 723 ms (3.6x) | README.md "Schema-driven decisions" |

**Expectations and measurements for this Mac (Apple M4 Pro, 10P+4E, 20-core GPU, 48GB).** The hypotheses were written on 2026-10-02, and the measurements are Track D on 2026-10-03 (`results/D/D_summary_20261003.md`). The hypothesis column is kept to record the prediction error.

| Item | Hypothesized range (2026-10-02) | Measured (2026-10-03) | Verdict |
|---|---|---|---|
| CPU fp32, 10 threads, inter-op 1, 1 question | multilingual 120-250 ms, english 300-600 ms | multilingual 37.7 ms (short 59 tok) / 81.8 (long 433), english 86.6 / 204.5 | 2.1-3.5× faster than hypothesized |
| CPU, scaling with the number of questions | 7-10× from 1 → 10 questions | short 3.22-5.69×, long 7.29-8.65× | Linear only for long inputs |
| MPS, 1 question, after warm-up | 30-80 ms | multilingual 13.8 ms, english 31.8 ms | Faster than the lower bound |
| MPS, scaling with the number of questions | 2-4× from 1 → 10 questions (sub-linear) | 4.52-9.05× | Rejected (close to linear) |
| First MPS call | Several seconds per new shape, about 13 s of Metal kernel compilation the first time (examples/README.md) | about 0.1 s | Rejected |
| `predict_batch(sort_by_length=True)`, Korean of mixed lengths | CPU 1.3-2.0x, MPS 1.4-1.8x | CPU 1.67-2.08x vs unsorted (n=256), 1.29-1.42x vs loop; MPS 1.21-1.25x vs loop | Supported on CPU; MPS below the lower bound |
| cold load (disk cache warm) | multilingual 2-4 s, english 3-6 s | multilingual 3.45-3.67 s (tokenizer about 1.0 s), english 2.82-2.97 s | multilingual within range; english faster than hypothesized |
| Memory | english ≈ 1.7 GB, multilingual ≈ 1.3 GB (fp32 resident). All three preloaded ≈ 5 GB | CPU RSS with 1 resident 2.07 GiB (multilingual, including the runtime), +english 1.57, +typed 1.60 → all three 5.23 GiB | Same order of magnitude |
| MPS vs CPU (1 question) | 3-6× | 2.33-2.80× | Below the hypothesized lower bound |

## 8. License·operations considerations

- **License**: both code and weights are Apache 2.0 (source: README.md "License", HF tag `license:apache-2.0`). Commercial use is allowed.
- **Fully local**: by upstream's rules, features that depend on hosted services are not accepted (source: AGENTS.md "Do NOT"). After the first download, it works even with the network cut off via `HF_HUB_OFFLINE=1`.
- **Supply-chain pinning**: commits are pinned with `LAYA_REVISION=reviewed` or `revision=`, and file digests are verified with `LAYA_SHA256_DIGESTS` / `expected_sha256` (source: `laya/revisions.py`). Our reports record which commit answered via `config.revisions` of `laya-evals`.
- **Security change (0.3.23)**: on a server with `LAYA_API_KEY` set, `GET /health` exposes only liveness and gives the checkpoint names·SHA·device state only with a bearer token (#812, source: README.md "What's new in 0.3.23"). Private vulnerability reports go through SECURITY.md.
- **CPU threads**: `torch.set_num_threads(near the number of physical cores)`, `set_num_interop_threads(1)`. upstream reported a case where leaving the defaults was 12× slower (source: BENCHMARKS.md §Other hardware). For `laya-serve`, `LAYA_THREADS`.
- **dtype and threshold**: against fp32, CUDA bf16 flips 3 of 864 argmaxes and fp16 0 (source: README.md "Automated Confidence Gating"). MPS uses fp16 at 5 rows or more. Thresholds must be fitted·validated **in the dtype that will be served**.
- **Docker/CUDA-only note**: `TORCH_DISABLE_NATIVE_JIT=1` addresses Triton compilation failures in slim CUDA images (#365) and is irrelevant on this Mac (source: docs/docker.md).
- **Concurrency**: in 0.3.23 the GPU OOM fallback is isolated behind a reader-writer gate, so it does not break in-flight requests (#649). Concurrent-request behavior on MPS is to be measured (PoC P2).

## 9. Implications for the benchmark design (hypotheses H1-H10)

Each hypothesis corresponds to a Track in `03_benchmark_plan.md`. The verdict criteria are fixed in that document.

| # | Hypothesis | Track | Rationale |
|---|---|---|---|
| H1 | Running `ko_massive_intent_20opt` on CPU fp32 reproduces multilingual 0.470 ± 0.03 and english 0.110 ± 0.03 | A | The `ko` row of BENCHMARKS.md §Languages. Deterministic if the conversion follows seed 13·the first 100 rows·20 options exactly |
| H2 | The Router sends 100% of Hangul states to multilingual, and multilingual is far ahead of english on every Korean set | B | The hangul range in `laya/lang.py:43`, ko 0.470 vs 0.110 (07 §4: mixed text·short Korean are exceptions) |
| H3 | On Korean topic/intent/NLI with ≤7 options (YNAT, 3i4K, KLUE-NLI), zero-shot accuracy is well above majority but below published supervised Korean encoders | B, F | zh 6-domain 0.883 vs CS routing 0.640. The range is wide depending on the domain·number of options |
| H4 | On Korean, the shipped ECE is at least 0.25, and after a per-bucket refit the held-out ECE is ≤ 0.10. Buckets with small n (the zh choice:6-10 case) may get worse with the refit | E | §Calibration 0.314 → 0.106, the zh refit table |
| H5 | The option-order flip rate of Korean choices with 7-20 options is 10-30% | C | upstream 0.150 / 0.230 (20 options), zh 28% / 10.6% |
| H6 | For Korean binary judgments, a 2-choice with neutral keys (A/B) is more accurate than noul, and adding criteria can push noul toward always-true | C | #156, the zh_short_commands ladder. In the P0b probe (n=30) the 2-choice A/B collapsed to A, a signal in the opposite direction (`results/poc/P0b_20261002.md`) |
| H7 | The negation probe fails at zero-shot (more than half of the negated requests are classified as affirmative) | C | #377 |
| H8 | MPS at 1 question is 3-6× faster than CPU at 10 threads and sub-linear in the number of questions; CPU is linear | D | §Speed, §Server CPU, the Arc comparison. Verdict (2026-10-03): **rejected** (MPS/CPU 1q 2.33-2.80×, 10q/1q MPS 4.52-9.05, `results/D/D_summary_20261003.md`) |
| H9 | On 64 Korean inputs of mixed lengths, `sort_by_length=True` gives ≥ 1.3× on CPU, 0 argmax changes, max \|Δp\| ≤ 0.01 | D | research/README.md "Length batching" 2.15x, 0 changes. Verdict (2026-10-03): **supported** (n=256: 1.67-2.08× vs unsorted, 1.29-1.42× vs loop, flip 0, 0.0001) |
| H10 | ONNX INT8 (per-tensor) on CPU takes ≤ 0.6× the time of torch, with \|ΔECE\| ≤ 0.01 and a choice_accuracy difference ≤ 0.01 (aligned with the 03 §1 criteria) | D | docs/evals.md 116.8 → 46.3 ms, ece +0.006. Verdict (2026-10-03): **rejected** (int8 1.74× slower, ΔECE +0.0154, Δacc −0.012, argmax agreement 0.930) |

If H1 fails, it is a problem in the measurement pipeline. H2-H7 map out "the area that can be trusted zero-shot in Korean", and H8-H10 decide the deployment form (MPS in-process, CPU ONNX, HTTP).

## Open questions / assumptions

- The M4 Pro numbers in §7 are all hypotheses. Update the §7 table with the Track D results, but do not delete the hypothesis column; keep two columns, "hypothesis vs measurement", to record the prediction error.
- The Korean tokenizer efficiency of mmBERT-base (tokens per character) has not been measured yet. Korean may need more tokens than Latin-script languages, so `room` runs out sooner. Phase 1 records the mean token count per set.
- All Jev numbers are 3rd-party published values. Our reports keep the same labeling (3rd party, not measured).
- The typed-decisions checkpoint is for English workflows only, so with the default `auto_task_detection=False` the Router does not pick it. The experiment that feeds Korean through an explicit `model="typed-decisions"` is limited to 1 reference run in Track B.
- The multilingual column of upstream's 51-language table holds refreshed rerun values, not the committed file (#208). The ko 0.470 we use as our comparison baseline is also a refreshed value. The committed values are not referenced.
- The ECE of `laya-evals` uses 15 bins on `answer_confidence`. Whether the ECE in BENCHMARKS.md has the same definition must be checked in `metrics()` of `research/scripts/bench_local.py`. If the definitions differ, the Track A reproduction verdict is made on accuracy alone and ECE is kept as a reference value.

**English** | [한국어](01_laya_analysis.ko.md)
