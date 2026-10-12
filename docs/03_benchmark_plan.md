# 03. Laya benchmark plan

**Purpose**: Measure the three checkpoints and the Router of Laya 0.3.23 on this Mac (M4 Pro) with a focus on Korean, decide the hypotheses H1\~H10 of 01_laya_analysis.md §9, and supply measured evidence to the 00_README.md §6 Go/No-Go and to the design decisions of 05_poc_plan.md.
**Prerequisite documents**: 00_README.md (execution order, Go/No-Go), 01_laya_analysis.md (§9 hypotheses), 02_environment_setup.md (environment, smoke test), 04_korean_evalset_spec.md (building the eval sets), 06_templates.md (run card, REPORT template).
**Outputs**: `results/<track>/*.json|.md`, `results/REPORT.md`, `poc/calibration/ko_v1.json`, `scripts/*.py` (implemented per the §3.8 specs).

All commands are run from the project root after `source env.sh`. Every published upstream figure carries its source, and all of our own figures are "to be measured".

## 1. Goals and decision questions

This benchmark exists to answer the five decisions below. Measurements that do not affect a decision are not made.

| # | Decision question | Evidence tracks | Related hypotheses |
|---|---|---|---|
| Q1 | Can Laya be adopted zero-shot for the PoC scenario (05 = C domain router, `ko_massive_domain_8`)? | B, C, F | H3, H5, H6, H7 |
| Q2 | Which checkpoint is used (english / multilingual / typed-decisions / Router auto)? | A, B | H1, H2 |
| Q3 | What is the deployment form (CPU torch / MPS / ONNX int8 CPU / laya-serve)? | D | H8, H9, H10 |
| Q4 | Confidence gating policy (min_confidence value, expected coverage, calibration payload) | E | H4 |
| Q5 | Is fine-tuning (05 P4) needed, or is zero-shot + gating enough? | B, E, F | H3, H4 |

(Decision questions are numbered with Q to distinguish them from the Track D step numbers D1\~D8.)

Verdict criteria per hypothesis. Figures are for CPU fp32 and are reported with a bootstrap 95% CI (§3.6).

| Hypothesis | Track | Verdict criterion (condition for support) | Verdict (2026-10-02) |
|---|---|---|---|
| H1 ko MASSIVE reproduction | A | ko: laya 0.110 / multilingual 0.470, en: 0.820 / 0.710, each within ±0.03 (source: BENCHMARKS.md:71, §Languages table) | **Supported**. Δ 0.000 in all 4 cells, ECE also matches (`results/A/README.md`) |
| H2 multilingual ≫ english, Router 100% | B | on every ko set, multilingual accuracy − english accuracy ≥ +0.20; the `model` slice of the Router auto run is 100% multilingual | **Partially supported**. ≥ +0.20 on 7 of 10 questions (exceptions NSMC noul +0.122, K-MHaS hate +0.082, 3i4K +0.004). Rows with Hangul are 100% multilingual; only the 4 rows without Hangul go to the default (`results/B/summary_20261002.md`) |
| H3 tasks with ≤7 options: above majority, below supervised | B, F | accuracy ≥ majority + 0.20 and below the supervised literature value | First half **supported** (choice tasks, excluding 3i4K). The two noul sets fall short (always-false bias). Second half **unresolved** (F3 literature values not looked up) |
| H4 as-shipped ECE > 0.25, ≤ 0.10 after refit | E | as-shipped ECE > 0.25 on at least half of the ko sets; ECE ≤ 0.10 after refit on the held-out half | First half **partial** (domain_8 test 0.263 exceeds it, ynat 0.148 is below). Second half **supported (borderline)**: after the pooled refit, domain_8 test 0.098, ynat 0.063 (`results/E/E_summary_20261002.md`) |
| H5 option-order flip 10\~30% | C | per-permutation flip rate of 0.10\~0.30 on sets with 7\~20 options | **Supported**. domain_8 0.270, ynat_7 0.168, scenario_18 0.241 (`results/C/C1_option_order_20261002.md`) |
| H6 noul < 2-choice (neutral keys) | C | on NSMC, A/B 2-choice accuracy − noul accuracy ≥ +0.05, McNemar p < 0.05 (the P0b early signal points the other way; decided in C3) | **Unresolved**. C3 not run. NSMC's semantic-key choice 0.774 > noul 0.638 (p=6.5e-10) is not the neutral-key condition, only a reference value |
| H7 zero-shot failure on negation | C | accuracy ≥ 0.80 on the affirmative half but ≤ 0.50 on the negated half | **Unresolved**. C4 not run (ko_negation_probe not built) |
| H8 MPS 3\~6x on 1 question, sub-linear in the number of questions | D | mps 1q median ≤ cpu 1q / 3; mps 10q/1q ratio ≤ 3 while the cpu 10q/1q ratio ≥ 7 | **Rejected** (2026-10-03 D1: MPS/CPU 1q 2.33\~2.80x, 10q/1q MPS 4.52\~9.05 vs CPU 3.22\~8.65. `results/D/D_summary_20261003.md`) |
| H9 sort_by_length ≥ 1.3x, flip 0 | D | 256 Korean items of mixed length, CPU, paired median speedup ≥ 1.3x, argmax flip 0 | **Supported** (2026-10-03 D4: n=256, 1.67 / 1.83 / 2.08x vs unsorted (bs 8/16/32), 1.39 / 1.42 / 1.29x vs the loop, flip 0, max \|Δp\| 0.0001) |
| H10 ONNX int8 ≈ 2x, ECE drift ≤ 0.01 | D | int8 latency ≤ torch CPU × 0.6, \|ΔECE\| ≤ 0.01, choice_accuracy difference ≤ 0.01 | **Rejected** (2026-10-03 D7: int8 525.9 ms vs torch 302.2 ms, 1.74x slower, ΔECE +0.0154, Δacc −0.012, argmax agreement 0.930) |

The fine-tuned checkpoint ft-v1 (05 P4, 2026-10-03) changes the PoC gates (G1\~G4), but H1\~H7 are hypotheses about the zero-shot checkpoints, so their verdicts do not change. The ft-v1 figures (domain_8 test 0.900, flip 0.037, ECE 0.053) are recorded in `results/go_no_go.json` and in 05 §6 P4.

## 2. Scope and out of scope

In scope:
- The 3 checkpoints + Router auto, laya 0.3.23, checkpoints pinned to the reviewed SHA (see 02).
- All Korean sets of 04_korean_evalset_spec.md. English only as a control (MASSIVE en, upstream fixture).
- Devices: CPU fp32 (reference for accuracy), MPS (reference for latency), ONNX Runtime CPU (fp32, int8).
- Local HTTP load measurement of laya-serve.
- Temperature refit and coverage curves.
- Baselines: majority/random, LLM zero-shot (optional), supervised literature values, published Jev figures.

Out of scope:
- Direct measurement of the Jev API. We have no access, and upstream did not measure it either (source: research/README.md §On comparisons with Jev).
- Fine-tuning. Handled only in 05_poc_plan.md P4. P4 started on 2026-10-02: a 1,000-row, 1-epoch probe took domain_8 test 0.492 → 0.720, with no YNAT forgetting (`results/P4/P4_probe_20261002.md`). The main training run starts automatically once the GPU queue is empty.
- CUDA, the TileLang fast path, torch.compile. This machine has no NVIDIA GPU, so only upstream figures are cited.
- A training-data contamination audit. Only upstream's "in training mix / held out" labels are passed on (source: BENCHMARKS.md §Themes).
- The MCP server, LangChain/CrewAI/LlamaIndex wrappers, the TypeScript SDK. Only functional checks in 05, if needed.
- Long context only up to an indicative n=20 measurement.

## 3. Common protocol

### 3.1 run identity

- Before each track starts, rerun the environment snapshot step of 02_environment_setup.md and keep `results/env/env_<YYYYMMDD-HHMM>.json`.
- Every script records the run card fields of 06_templates.md §1 to stdout and to `run_card` in the result JSON: laya_version, torch, transformers, device, dtype, threads (intra/inter), checkpoint SHA, dataset_sha256, questions_sha256, start time, power state (`pmset -g batt` summary), and the git SHA if the script repo is a git repository.
- `laya-evals run --json` records dataset_sha256, questions_sha256, laya_version, revisions, thresholds and timing in its `config` block by itself (source: docs/evals.md §Run identity). When a checkpoint is loaded from the Hub cache, `revisions` gets the commit, but for the subfolders (`laya-multilingual`, `laya-typed-decisions`) of the `models/` (not included in the public repository) symlink, `snapshot_revision()` returns None (laya/revisions.py `snapshot_revision`), so our scripts, which use local paths, record the SHA in the run card directly.
- Checkpoint pinning: `LAYA_REVISION=reviewed` in env.sh applies to every Hub load (laya/revisions.py `resolve_revision`).

### 3.2 Data rules

- The label policy is finalized in 04 before any model is run, and the files are hashed. If labels are fixed after looking at model results, that is done only under a new file name (`_v2`).
- All evaluation items come from the test/validation split. The single source of the 50/50 dev/test split is `results/B/B_splits.json` (`scripts/metrics_extra.py` `row_splits`): the paired MASSIVE sets (ko/en domain_8, ko/en intent_20opt) by row index parity (even dev, odd test; both files in the same id order), the other sets by the parity of the sha256 of the state JSON. Calibration fits (Track E) and ablations use only the dev half and do not create a new split (hash50). The test half is scored only once per frozen schema version.
- seed 13 (the same as upstream `SEED`: top of research/scripts/bench_local.py), label-stratified sampling. Sizes: 100 for the MASSIVE reproduction, 300\~500 for the other sets (per 04). Running the full sets is optional.
- JSONL files are immutable once hashed. `laya-evals compare` rejects reports with a different `dataset_sha256` (source: docs/evals.md §Baseline and CI gate).

### 3.3 Measurement rules

- Warm-up: discard at least 3 calls before measuring latency. Upstream wrote that on MPS the first call for each (batch, length) shape incurs up to about 13 seconds of Metal kernel compilation (source: examples/README.md "Before you start"), but the measurement on this machine is about 0.1 s (2026-10-03 D3, `results/D/20261003-1306_coldload.md`). Even so, at least 1 preceding call is kept for every shape used in a measurement.
- Repetitions: latency ≥10 runs, reporting the median and p95 (and min). Accuracy is a single deterministic CPU fp32 pass. MPS accuracy is used only after passing the §3.4 parity gate.
- Time is measured with `time.perf_counter()` around the `predict()` call only (in-process). HTTP is from sending the request to parsing the response. The two are not compared in one table.
- During measurements: other heavy processes stopped, AC power, screen lock prevented. If throttling is suspected, re-measure the same setting 10 minutes later and check that the medians differ by 10% or less.

### 3.4 Device/precision rules

- CPU fp32 is the accuracy reference. `torch.set_num_threads(10)`, `torch.set_num_interop_threads(1)`. inter-op 1 is the setting with which upstream saw 12x on a busy host (source: BENCHMARKS.md §Laptop CPU).
- On MPS, fp16 autocast kicks in only when rows ≥ 5 (`MPS_AMP_MIN_ROWS_DEFAULT = 5`, laya/agent.py:278). A 1-question `predict` is fp32 even on MPS; 5 or more questions or `predict_batch` run in fp16. `LAYA_MPS_AMP_MIN_ROWS=100000` forces fp32.
- MPS parity gate (A5, C9): on the same items, the fp32 path must match argmax 100% with max|Δp| ≤ 0.01, and the fp16 path argmax ≥ 99% with max|Δp| ≤ 0.05. Borrowed from the upstream fast-path parity criterion (max|Δp| ≤ 0.05 vs fp32, argmax ≥ 47/48: source README §GPU Fast Path). Until the gate is passed, MPS figures are for latency only.

### 3.5 Storage conventions

- `results/<track>/<YYYYMMDD-HHMM>_<model>_<dataset>.json` + an `.md` of the same name. No overwriting. Failed runs are also kept, with the `_FAILED` suffix.
- Reviewed reports are copied to `results/baselines/<dataset>_<model>_baseline.json`, and later runs check drift with `laya-evals compare REPORT --baseline ... --tolerance choice_accuracy=0.02`.
- Raw LLM prompts go to `results/F/prompts/`, calibration payloads to `poc/calibration/`.

### 3.6 Statistics

- A bootstrap 95% CI (1000 resamples, percentile) for every accuracy/ECE. At n=100 it is about ±0.10 at p≈0.5, at n=400 about ±0.05.
- A/B comparisons on the same items (devices, variants, primitives) use the exact McNemar test. Upstream used the same test for its position-sensitivity comparison (source: research/README.md §Headline findings).
- To detect a 5-point difference as significant, aim for n ≥ 400; n=100 sets (MASSIVE reproduction) are not used for ranking decisions.
- The Track A "reproduction" criterion is ±0.03. The setup with the first 100 rows fixed + seed 13 is deterministic, so any larger difference is not noise but a difference in setup or version. Its cause is found and recorded.

### 3.7 Baseline fairness

- Same label set, same descriptions (the criteria text rendered into the prompt as is), no few-shot, no label names exposed in the state.
- The LLM gets the same N items, temperature 0, and JSON output containing only the label. Invalid outputs are not discarded but reported as an error rate.
- Supervised literature values are labeled "supervised ceiling", and this is stated in the column header when they are placed in the same table as zero-shot.

### 3.8 Script specs (implemented separately)

| Script | Purpose | Input | Output | Upstream reuse |
|---|---|---|---|---|
| `scripts/env_report.py` | environment snapshot (versions, devices, threads, checkpoint SHA, dataset sha256) | optional JSONL paths | `results/env/env_*.json` | `laya.revisions.snapshot_revision` (spec: 02 §2.10) |
| `scripts/build_ko_evalsets.py` | build and validation of the Korean eval sets, MANIFEST | subcommands `all`, `massive`, `ynat`, ... (04 §6) | `data/evals/*.jsonl`, `MANIFEST.json` | `laya.evals.Dataset`, `questions_fingerprint`; `laya-evals validate` (spec: 04 §6) |
| `scripts/bench_massive_ko.py` | Track A reproduction (ko/en MASSIVE 20 options) | `--langs`, `--per-lang`, `--models`, `--device` | `results/A/*.json|.md` | `build_massive`, `score_cases`, `metrics`, `softmax_t`, `temp_for`, `load` from `third_party/laya/research/scripts/bench_local.py` (the upstream clone, not included in the public repository; recreate it by cloning https://github.com/NandhaKishorM/laya at commit 4aa6761). bench_local reads `LAYA_MODELS` at import time (bench_local.py:39), so set `os.environ["LAYA_MODELS"] = os.environ["LAYA_MODELS_DIR"]` before importing it (02 §2.8) |
| `scripts/metrics_extra.py` (implemented, 388 lines) | macro-F1, Brier, bootstrap CI, coverage curves, McNemar, parity, majority/random. Subcommand style: `summary REPORT...`, `paired A B`, `parity A B`, `coverage REPORT`, `majority REPORT`, shared `--split-rule auto\|index\|hash --out --json` (`scripts/metrics_extra.py:342`) | laya-evals report JSONs | `results/<track>/metrics/*.md,json` | `laya.common.ece_score`; the per-case records of the report (`cases[].answer` includes probabilities, laya/evals.py:728-744) |
| `scripts/probe_option_order.py` | option-permutation flip | JSONLs, `--permutations`, `--seed` | `results/C/*_option_order.json` | the `build_benchmark_nb.py:640-678` method |
| `scripts/probe_wording_ladder.py` | wording ladder | PoC JSONL | `results/C/*_wording_ladder.json` | the ladder definition of `research/benchmarks/zh_short_commands` |
| `scripts/bench_latency_local.py` | in-process latency matrix, thread sweep, cold load, RSS | `--checkpoints`, `--questions`, `--devices`, `--states`, `--threads`, `--interop`, `--repeat` | `results/D/*_latency_*.json` | `verify/bench_devices.py`, `examples/_common.py timed`, the `bench_latency.py` question set |
| `scripts/bench_batch_local.py` | predict loop vs predict_batch, sort_by_length, parity | `--states`, `--n`, `--batch-size`, `--sort-by-length`, `--devices`, `--rounds` | `results/D/*_batch.json` | `research/scripts/bench_length_batching.py`, `benchmarks/bench_predict_batch.py` |
| `scripts/bench_http_local.py` | laya-serve load (closed/open loop, batch) | `--url`, `--closed`, `--open`, `--duration`, `--batch-states` | `results/D/*_http_*.json` | none (httpx + asyncio) |
| `scripts/calibrate_ko.py` (implemented, about 515 lines) | temperature refit, saving the payload, ECE/NLL before and after, coverage (only this script, which has the logits, can compute the post-calibration curve) | `--sets`, `--splits results/B/B_splits.json`, `--model`, `--device`, `--pooled`/`--per-task`, `--min-bucket-n`, `--out-payload`, `--out` | `poc/calibration/ko_v1.json`, `results/E/*.json` | `laya.calibrate.records_from_labeled` (which must be wrapped in `torch.no_grad()`: see the E2 defect note below), `fit_temperature_map`, `fit_one_temperature`, `calibration_payload` |
| `scripts/llm_baseline.py` (optional) | LLM zero-shot baseline | JSONLs, `--model`, `--n`, `--cache` | `results/F/*.json`, `results/F/prompts/` | none (anthropic SDK) |
| `scripts/bench_long_context_ko.py` | C8 long context and position sensitivity (Korean) | `--device`, `--pads` | `results/C/*_long_context.json` | a copy of `research/scripts/bench_long_context.py` with only the `REQUESTS` and `FILLER` constants replaced by Korean |
| `scripts/build_dashboard.py` | results dashboard: generates the per-track tables and charts, hypothesis verdicts and Go/No-Go as a single HTML file (§12 item 11) | `--results results/` (the latest `results/env/env_*.json`, `results/{A,B,C,D,E,F,poc}/*.json`, `results/verdicts.json`, `results/go_no_go.json`), `--out results/dashboard/index.html`, `--open` | `results/dashboard/index.html` (self-contained HTML, data as inline JSON) | none. Charts with Chart.js from cdnjs or inline SVG, tables in plain HTML (the tables stay visible offline). The output is deterministic, with the generation time only in a single footer line |

Every script writes JSON and Markdown tables to `results/<track>/` and prints the run card fields.

## 4. Metric definitions

| Metric | Definition | Computed in | Primitives |
|---|---|---|---|
| accuracy (`choice_accuracy`, `noul_accuracy`) | argmax label match rate; noul binarized at p ≥ 0.5 | laya-evals | choice, noul |
| macro-F1 | unweighted mean of the per-class F1 | metrics_extra | choice |
| Brier | mean of the sum over options of (p_o − y_o)² (multi-class sum) | metrics_extra | choice, noul |
| ECE | 15-bin, based on `answer_confidence` (= max p) (source: docs/evals.md §Metrics) | laya-evals, metrics_extra (CI) | all |
| mean_confidence | mean of `answer_confidence` | laya-evals | all |
| coverage@accuracy, acc@50%cov | accuracy when answering only the top x% by confidence; the same definition as `acc_at_50_coverage` in bench_local `metrics` | metrics_extra | choice, noul |
| abstention rate@T | share of `abstention == "abstained"` at `--min-confidence T` | laya-evals | all |
| option-order flip rate | argmax mismatch rate between the original-order answer and random-permutation answers (mean per permutation) + any-flip (at least 1 flip among k permutations) | probe_option_order | choice |
| wording-ladder Δ | accuracy difference per ladder step and the noul always-true rate | probe_wording_ladder | choice, noul |
| recall@k (shortlist) | share of cases where the shortlist kept the gold label, `shortlist_recall_at_k` of `evaluate_shortlist` (source: docs/evals.md §Attributing shortlist errors) | laya.evals_shortlist | choice |
| score_mae, score_within_t | absolute difference between the expected level and the gold level (0-based index), share within tolerance | laya-evals | score |
| latency p50/p95 | in-process: wall clock of the `predict` call; HTTP: request to response (including serialization). Reported separately | bench_latency_local, bench_http_local | all |
| throughput | states/s, decisions/s (= states × number of questions) | bench_batch_local, bench_http_local | all |
| cold load | seconds from import → load → first answer in a new process | bench_latency_local | all |
| peak RSS | psutil maximum RSS; for MPS, `torch.mps.current_allocated_memory()` alongside | bench_latency_local, bench_batch_local | all |
| parity | argmax agreement rate and max \|Δp\| between two paths (source: the benchmarks/parity_fast.py method) | metrics_extra | all |

Metrics that laya-evals does not produce (macro-F1, Brier, CI, coverage curves, McNemar) are computed by `scripts/metrics_extra.py` from the per-case records of the report JSON. The report's `cases[]` keeps `expected`, `answer` (the full answer dict including probabilities) and `correct` for each case (source: laya/evals.py:728-744, `EvalReport.to_json()` :376-379), so there is no need to call the model again.

## 5. Track A reproduction

Purpose: a sanity gate that checks whether our environment produces the upstream figures. No other track starts before it passes.

### A1 fixture [step → verification]

Already done by the smoke test of 02_environment_setup.md. Expected values (english, CPU): choice_acc 0.75, noul_acc 1.00, score_mae 1.3418, ece 0.1596 (source: docs/evals.md §Evaluating an ONNX export table). Verification: copy that report into `results/A/` and only check that the four figures match.

### A2 ko/en MASSIVE 20 options, upstream script path [step → verification]

```bash
python scripts/bench_massive_ko.py --langs ko,en --per-lang 100 --models english,multilingual \
  --device cpu --out results/A/$(date +%Y%m%d-%H%M)_massive20_ko_en.json
```

- The setup must be byte-identical to upstream: the first 100 rows of the test split of configs `ko`/`en`, 20 options = gold + 19 drawn with `random.Random(13)` and then shuffled, criteria text from the key with `_`→space and `.`→`: `, instructions "What is the user asking for in `utterance`?" (source: research/scripts/bench_local.py:165-183). The script imports those functions and does not reimplement them.
- Expected values (published upstream figures, source: BENCHMARKS.md:71 and the `en` row of the §Languages table):

| Language | laya acc | multilingual acc | laya ECE | multilingual ECE |
|---|---|---|---|---|
| ko | 0.110 | 0.470 | 0.680 | 0.311 |
| en | 0.820 | 0.710 | 0.138 | 0.233 |

- Verification: accuracy ±0.03, ECE ±0.05. If ECE is off, suspect the temperature regime first. The ECE column of the committed 51-language sweep holds values from before the #42 clamp, while the macro ECE in the table header (laya 0.5709) is the post-clamp "as served" value (source: the clamp explanation at the beginning of BENCHMARKS.md). multilingual ships without a fitted temperature (source: README §Calibration), so the clamp has no effect and 0.311 should come out as is.
- Check order when they differ: (1) identity of the first 100 rows via the `id` field (mteb dataset lastModified 2026-02-24; the row order may change), (2) checkpoint SHA, (3) laya version, (4) diff of the rendered criteria strings.

### A3 The same 100 items via the laya-evals path [step → verification]

```bash
ts=$(date +%Y%m%d-%H%M)
laya-evals validate data/evals/ko_massive_intent_20opt.jsonl
laya-evals run data/evals/ko_massive_intent_20opt.jsonl --model multilingual --device cpu \
  --slice language --json results/A/${ts}_multilingual_ko_massive20.json --markdown results/A/${ts}_multilingual_ko_massive20.md
laya-evals run data/evals/ko_massive_intent_20opt.jsonl --model english --device cpu \
  --slice language --json results/A/${ts}_english_ko_massive20.json
```

- Verification: `choice_accuracy` equals A2's ko accuracy for the same model. If 1 or more items differ, check (a) whether the JSONL setup differs from bench_local (option order, criteria strings) and (b) whether a difference in batch shape (bench_local `score_cases` packs by length, the harness calls per row) shook probabilities near the threshold. Up to 1 flip with a probability difference < 0.01 is recorded and accepted.
- This step is the prerequisite for Track B. Only if the harness path and the script path give the same answers can B's figures be placed next to the upstream table.

### A4 (optional) zh anchor [step → verification]

```bash
laya-evals run third_party/laya/research/evals/zh_decision_bench.jsonl --model multilingual --device cpu \
  --slice tag --json results/A/$(date +%Y%m%d-%H%M)_multilingual_zh_decision_bench.json
```

Expected: voice routing (n=179) 0.883, CS routing (n=25) 0.640, urgency 0.560, scam/promo 0.667, escalate 0.550 (source: BENCHMARKS.md §Community evaluation zh §2, laya 0.3.20 CUDA). Verification: with 0.3.23 + CPU fp32, almost all argmaxes should be the same, and within ±0.02 on the n=179 slice is accepted. A second, non-English reproduction anchor.

### A5 MPS parity [step → verification]

```bash
ts=$(date +%Y%m%d-%H%M)
laya-evals run data/evals/ko_massive_intent_20opt.jsonl --model multilingual --device mps \
  --json results/A/${ts}_multilingual_ko_massive20_mps_fp32path.json
laya-evals run data/evals/ko_massive_intent_20opt.jsonl --model multilingual --device mps --batch-size 16 \
  --json results/A/${ts}_multilingual_ko_massive20_mps_fp16path.json
python scripts/metrics_extra.py parity results/A/${ts}_multilingual_ko_massive20.json results/A/${ts}_multilingual_ko_massive20_mps_fp32path.json
python scripts/metrics_extra.py parity results/A/${ts}_multilingual_ko_massive20.json results/A/${ts}_multilingual_ko_massive20_mps_fp16path.json
```

A 1-question call is 1 row, so it runs in fp32 even on MPS (§3.4). `--batch-size 16` may not actually batch on the 20-option set, because the question differs per row. If it does not batch, the fp16 path is verified instead in C9 with YNAT, whose rows share a question. The verification criterion is §3.4.

### Gate

If A2 and A3 pass (and the A5 fp32 path is 100/100), go to Track D. On failure, record the cause in `results/A/INVESTIGATION.md` and do not proceed until it is resolved.

## 6. Track D performance

### D1 in-process latency matrix [step → verification]

```bash
python scripts/bench_latency_local.py --checkpoints english,multilingual,typed-decisions \
  --questions 1,3,5,10,50 --devices cpu,mps --states short,long --repeat 10 \
  --out results/D/$(date +%Y%m%d-%H%M)_latency_matrix.json
```

- States: `short`, a Korean inquiry of about 60 tokens, and `long`, about 400 tokens (1 of each, fixed, from the PoC set of 04). Questions alternate between a 3-option choice and a noul, as in upstream bench_latency (source: research/scripts/bench_latency.py `Q_CHOICE`, `Q_NOUL`, `qs(n)`).
- Report: median/p95 per setting, ms/question, slope in the number of questions (10q/1q ratio).
- Expected-value comparison table:

| Setting | english 1q | multilingual 1q | multilingual 10q | Source |
|---|---|---|---|---|
| Tesla T4 GPU | 39.5 ms | 32.8 ms | 72.3 ms | BENCHMARKS.md §Speed (upstream) |
| EPYC 9R14 4-core CPU fp32 | 580 ms | 193 ms | 1,842 ms | BENCHMARKS.md §Server CPU (upstream) |
| Ryzen 6900HX 8 threads, in-process 1q (3q via HTTP: 783 ms) | 329 ms p50 | not measured | not measured | BENCHMARKS.md §Laptop CPU (upstream) |
| M4 Pro CPU 10 threads (estimate 250\~500 / 80\~200) | **86.6 / 204.5** ms (short 123 tok / long 919 tok) | **37.7 / 81.8** ms (short 59 / long 433) | **121.4 / 596.5** ms | measured in this track 2026-10-03 (`results/D/20261003-1249_latency_matrix.md`) |
| M4 Pro MPS (estimate 30\~80 / 20\~60) | **31.8 / 85.6** ms | **13.8 / 35.1** ms | **62.4 / 284.8** ms | measured in this track 2026-10-03 |

- Verification (H8): CPU should be nearly linear in the number of questions (EPYC per question multilingual \~185 ms, english \~600 ms: source BENCHMARKS.md §Server CPU), MPS sub-linear (T4 10q 7.2 ms/q, GB10 7.0 ms per question: source BENCHMARKS.md §Speed, §NVIDIA GB10). The estimates are hypotheses and are replaced by measured values.

### D2 CPU thread sweep [step → verification]

```bash
python scripts/bench_latency_local.py --checkpoints multilingual --questions 1,10 --devices cpu \
  --threads 4,8,10,14 --interop 1,default --repeat 10 --out results/D/$(date +%Y%m%d-%H%M)_threads.json
```

Verification: around the number of P-cores (10) should be optimal, and 14 (including E-cores) should be the same or slower. Upstream recommends "the number of physical cores + a little" and reported contention between SMT sibling cores (source: BENCHMARKS.md §Laptop CPU). Whether `OMP_NUM_THREADS=10` in env.sh is appropriate is settled here.

### D3 cold load [step → verification]

Measure `import laya` → `laya.load(...)` → the first `predict` in a new process 3 times (the 1st with a cold OS file cache). The 3 checkpoints × {cpu, mps}. Upstream wrote that parsing multilingual's 34 MB tokenizer.json costs more than applying the weights (source: README §Production Preload & Memory), but the measurement on this machine is the opposite, tokenizer about 1.0 s and weights/module build about 2.0 s (2026-10-03 D3). MPS adds the first-shape compilation, so "time to first answer" is reported separately from CPU. Reference values for verification: EPYC cold load english 4.4 s, multilingual 2.5 s, typed-decisions 0.5 s (cache effect, approximate: source BENCHMARKS.md §Server CPU). If our values are 2x or more slower, check the disk/cache state first.

### D4 State batching [step → verification]

```bash
python scripts/bench_batch_local.py --checkpoint multilingual \
  --states data/evals/ko_nsmc_sentiment.jsonl,data/evals/ko_klue_ynat_7.jsonl --n 64,256 \
  --batch-size 8,16,32 --sort-by-length both --devices cpu,mps --rounds 3 --interleave \
  --out results/D/$(date +%Y%m%d-%H%M)_batch.json
```

- Comparison: `predict` loop vs `predict_batch(batch_size=N, sort_by_length=False/True)`. As in the upstream CLI measurement, rounds are run alternately and the paired median is reported (source: the 1.42x measurement method of README §Command line).
- parity: number of argmax flips per item (expected 0), max|Δp| (CPU ≤ 0.01; MPS fp16 recorded only).
- Verification (H9): MPS batching 3\~4x (decide_batch of 8 items 3.6x on Apple M: source README §Schema-driven decisions); on CPU \~1x from batch_size alone and 1.3\~2.15x with sort_by_length (source: README §Command line 1.42x; research/README.md §Length batching 2.15x). Measured (2026-10-03 D4): MPS batching reached only 1.21\~1.25x vs the loop even when sorted, far below the expected 3\~4x; on CPU, batches without sorting were slower than the loop (0.62\~0.93x), and sort_by_length gave 1.67\~2.08x vs unsorted (n=256).

### D5 Router heterogeneous batch [step → verification]

Run 32 alternating ko/en items with `Router(max_loaded=1)` and `Router(max_loaded=2)`, as a `predict` loop and with `predict_batch`, and report the total time and the number of reloads (`on_load`/`on_evict` hook counts). Reference values for verification: reload median CPU 7.4 s / T4 10.3 s (source: README §Production Preload & Memory). Design evidence for when the PoC also receives English traffic (05).

### D6 HTTP, laya-serve [step → verification]

```bash
# env.sh does not export LAYA_MODELS (it uses LAYA_MODELS_DIR, 02 §2.8). LAYA_MODELS below is laya-serve's list of preload names.
LAYA_MODELS=multilingual LAYA_DEVICE=mps LAYA_PRELOAD=1 LAYA_HOST=127.0.0.1 LAYA_PORT=8000 laya-serve &
python scripts/bench_http_local.py --url http://127.0.0.1:8000 --questions 1,3 \
  --closed 1,4,8 --open 5,10,20 --duration 60 --batch-states 16,64 \
  --out results/D/$(date +%Y%m%d-%H%M)_http_mps.json
```

- Modes: closed-loop concurrency 1/4/8, open-loop 5/10/20 RPS, 60 s each, `/v1/systemone/batch` with 16/64 states (cap 64: source README §Self-Hosting).
- Report: p50/p95, achieved RPS, error rate, number of 503s and `Retry-After` compliance (source: README §What's new in 0.3.21).
- Repeat the same procedure with `LAYA_DEVICE=cpu LAYA_THREADS=10` to get the picture for a deployment without a GPU.
- Verification: "p95 ≤ 150 ms at 10 RPS (MPS)" of 00_README.md §6.

### D7 ONNX CPU [step → verification]

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

- With `--onnx`, `--model` is not a Router short name but the path/Hub id of the export source (source: docs/evals.md §Evaluating an ONNX export). The `--quantize` default is per-tensor (per-channel collapses to 32% agreement with eager: source README §What's new in 0.3.23). The int8 file is written next to `--output` as `<stem>.int8.onnx` (`int8_output_path`: `laya.onnx` → `laya.int8.onnx`, source: scripts/export_onnx.py).
- Verification (H10): fp32 ONNX has the same metrics as torch; for int8 the fixture gave torch 116.8 → onnx 66.3 → int8 46.3 ms, ece 0.1596 → 0.1658 (source: docs/evals.md). Acceptance: int8 ≤ torch × 0.6, |ΔECE| ≤ 0.01, choice_accuracy difference ≤ 0.01.

### D8 Memory [step → verification]

RSS with 1/2/3 resident via `Router(preload=True)`, and peak RSS during a 64-state batch (psutil sampling every 10 ms, the upstream method: source research/README.md §Length batching). Order of magnitude for verification: fp32 weights english about 1.7 GB, multilingual about 1.3 GB + tokenizer. Upstream whole-script peak 9.3 GiB (5 loads) (source: BENCHMARKS.md §Server CPU). This is a 48 GB machine, so memory is not a constraint and is used only as evidence for sizing the PoC container.

### Measured values (2026-10-03, Apple M4 Pro, run alone)

Source: `results/D/D_summary_20261003.md` (run card `results/D/D_20261003.md`). Conditions: AC power, no thermal warnings, no external GPU jobs, median of 10 runs after 3 warm-up calls (+1 per MPS shape), CPU intra-op 10 / inter-op 1.

**D1 in-process latency matrix** (median ms; 3q with p95 alongside; `results/D/20261003-1249_latency_matrix.json`)

| Checkpoint · state | CPU 1q / 3q (p95) / 10q | MPS 1q / 3q (p95) / 10q | CPU÷MPS 1q |
|---|---|---|---|
| multilingual · short 59 tok | 37.7 / 56.4 (57.8) / 121.4 | 13.8 / 22.5 (22.6) / 62.4 | 2.73x |
| multilingual · long 433 tok | 81.8 / 195.8 (247.8) / 596.5 | 35.1 / 92.2 (92.5) / 284.8 | 2.33x |
| english · short 123 tok | 86.6 / 184.4 (186.5) / 472.8 | 31.8 / 79.6 (80.0) / 232.3 | 2.73x |
| english · long 919 tok (truncated to 512) | 204.5 / 515.1 (529.5) / 1658.1 | 85.6 / 242.1 (242.8) / 747.4 | 2.39x |
| typed-decisions · short 123 | 89.3 / 192.0 (194.4) / 507.9 | 31.9 / 79.8 (80.2) / 231.8 | 2.80x |
| typed-decisions · long 919 | 399.6 / 1143.6 (1175.7) / 3457.3 | 163.1 / 484.6 (485.0) / 1475.4 | 2.45x |

- dtype: CPU fp32 in every cell, MPS 1q and 3q fp32, 5q and above fp16 autocast. D1b (fp32 forced with `LAYA_MPS_AMP_MIN_ROWS=100000`): the fp16 autocast gain is at most 8% (english long 50q), and for short rows at 5\~10q it is actually 6\~16% slower.
- D1c (intermittent calls, idle gap ≥ 100 ms, `results/D/20261003-1312_latency_paced.json`): MPS gets 2.2\~3.6x slower, CPU 1.1\~2.3x (multilingual short 3q: MPS 22.2 → 49.5\~51.0 ms, CPU 53.1 → 60.8\~97.6 ms). The same phenomenon appeared in the server's open-loop runs.
- **G5 pass** (PoC configuration multilingual 3q p95: MPS 22.6 / 92.5 ms, CPU 57.8 / 247.8 ms; with intermittent calls too, MPS ≤ 90.6, CPU ≤ 100.5 ms). english and typed-decisions long fail the CPU criterion (529.5 / 1175.7 ms).
- **H8 rejected**: MPS 1q advantage 2.33\~2.80x (short of the 3\~6x criterion), 10q/1q MPS 4.52\~9.05, so not sub-linear; CPU÷MPS stays constant at 1.9\~2.8x as the number of questions grows.

**D2 CPU thread sweep** (`results/D/20261003-1304_threads.json`): intra-op 10 is optimal (short 10q 114.7, long 1q 81.0, long 10q 597.6 ms). 14 (including E-cores) is 2\~22% slower. The difference between inter-op 1 and the default (14) is −3.1\~+1.0%, at the level of measurement error. Exception: for the 1-row short 1q, 4 threads at 27.0 ms are faster than 10 threads at 33.2 ms. env.sh `OMP_NUM_THREADS=10` confirmed.

**D3 cold load** (warm disk cache, new process, `results/D/20261003-1306_coldload.json`): to the first answer, english and typed-decisions 2.82\~2.97 s, multilingual 3.45\~3.67 s (of the 3.0 s load, tokenizer about 1.0 s, weights/module build about 2.0 s). The additional compilation on the first MPS call is about 0.1 s.

**D4 state batching** (multilingual, router_v1 1 question, mixed-length Korean 64·256 states, 3 alternating rounds, `results/D/20261003-1314_batch.json`)

| device | n | loop | b8 / b8s | b16 / b16s | b32 / b32s | sort÷unsort (bs 8/16/32) |
|---|---|---|---|---|---|---|
| CPU | 256 | 15.73 s | 18.97 / **11.32** | 20.15 / 11.06 | 25.52 / 12.18 | 1.67 / 1.83 / 2.08 |
| CPU | 64 | 4.16 s | 4.30 / 2.79 | 5.16 / 3.53 | 6.58 / 4.47 | 1.56 / 1.49 / 1.46 |
| MPS | 256 | 6.64 s | 8.72 / 5.48 | 9.46 / 5.35 | 10.83 / 5.36 | 1.59 / 1.77 / 2.02 |
| MPS | 64 | 1.65 s | 1.97 / 1.32 | 2.14 / 1.48 | 2.79 / 1.92 | 1.49 / 1.44 / 1.45 |

- parity (vs each device's loop): CPU flip 0 in every mode, max \|Δp\| 0.0001; MPS fp16 batches flip 0, 0.0081\~0.0085. **G7 pass** (the first evidence measured as defined).
- **H9 supported** (n=256 CPU sort 1.67\~2.08x, vs the loop b8s 1.39 / b16s 1.42x, flip 0). Unsorted CPU batches are slower than the loop (0.62\~0.93x, padding slots 1.6\~2.2x). MPS is 1.21\~1.25x vs the loop even when sorted.

**D5 Router heterogeneous batch** (32 alternating ko/en items, `results/D/20261003-1328_router_batch.json`): cost of 1 checkpoint switch CPU 0.130 s / MPS 0.206 s (with local paths + the in-process tokenizer cache; hard to compare directly with upstream's 7.4 / 10.3 s). Even with `max_loaded=1`, `predict_batch` loads 2 times per pass, 1.07\~1.69 s. `max_loaded=2` (default) has 0 reloads.

**D6 HTTP, laya-serve** (`LAYA_MODELS=multilingual LAYA_PRELOAD=1 LAYA_THREADS=10`, 60 s, `results/D/20261003-1330_http_mps.json`, `-1343_http_cpu.json`)

| Server | Condition | p50 / p95 ms | 503 |
|---|---|---|---|
| MPS | closed c=1, 1q | 20.3 / 22.6 | 0 |
| MPS | closed c=1, 3q | 45.6 / 48.6 | 0 |
| MPS | open 10 RPS, 1q | 47.3 / 57.3 | 0 |
| **MPS** | **open 10 RPS, 3q** | **63.5 / 79.4** (p99 85.1) | 0 |
| CPU | closed c=1, 3q | 99.5 / 103.5 | 0 |
| CPU | open 10 RPS, 3q | 99.9 / 135.8 | 0 |

- **G6 pass** (MPS 10 RPS 3q p95 79.4 ms ≤ 150; CPU is also within the criterion at 135.8). With 0 errors and 503s, the Retry-After path was not exercised (concurrency 8 and 20 RPS do not exceed the `LAYA_MAX_CONCURRENT` default of 16).
- The server processes inferences serially (`ThreadPoolExecutor(max_workers=1)`, laya/serve.py:701; asyncio.Lock gate :863-867). The throughput ceiling is about 50 RPS for MPS 1q, 22.6 RPS for 3q, 19.7 RPS for CPU 1q and 10 RPS for 3q; raising concurrency only increases latency. `/v1/systemone/batch` takes 218 / 848 ms for 16 / 64 states (about 75 states/s).

**D7 ONNX CPU** (all 500 rows of ko_klue_ynat_7, batch 16; this includes the test half, so it is for comparing paths only and not used for the Track B verdict; `results/D/20261003-1347_*_ynat.json`)

| Path | acc | ece | p50 ms (16-row call) |
|---|---|---|---|
| torch CPU (intra 10) | 0.634 | 0.1723 | 302.2 |
| ONNX fp32 | 0.634 | 0.1723 | 455.0 |
| ONNX int8 (per-tensor) | 0.622 | 0.1877 | 525.9 |

- Pinning ORT to intra 10 / inter 1 changes nothing, fp32 457 and int8 499 ms. Files: `laya-multilingual.onnx` + `.onnx.data` (1.29 GB), `.int8.onnx` (925 MB). int8 argmax agreement 0.930 (35 flips), max \|Δp\| 0.646.
- **H10 rejected** (int8 is 1.74x slower than torch, ΔECE +0.0154, Δacc −0.012). On this Apple silicon, torch fp32 is faster and more accurate than ONNX.

**D8 memory** (`results/D/20261003-1307_rss_preload.json`, `-1349_rss_peak_batch.json`): CPU RSS with 1 / 2 / 3 resident 2.07 / 3.63 / 5.23 GiB (multilingual +1.88, english +1.57, typed +1.60). 64-state `predict_batch` peak (relative to after loading): bs16 +2.43, bs16+sort +1.86, all 64 in one forward +5.49 GiB. MPS: RSS 1.1\~1.7 GiB + driver allocation 1.24\~5.25 GiB.

**Verdict summary**: G5 pass · G6 pass · G7 pass · H8 rejected · H9 supported · H10 rejected. Total measurement time 3,509 s (12:49\~13:51).

### Time budget

| Step | Calls (approx.) | Expected wall time | Notes |
|---|---|---|---|
| D1 | 60 settings × 13 | CPU 30\~40 minutes, MPS 10 minutes | dominated by the english 50q CPU calls |
| D2 | 8 settings × 13 | 10 minutes | |
| D3 | 18 processes | 5\~10 minutes | |
| D4 | 2 sets × 2 n × 7 modes × 3 rounds | CPU 30 minutes, MPS 10 minutes | |
| D5 | 4 settings | 5 minutes | reloads on the order of 10 s |
| D6 | 6 modes × 60 s + batch | 15 minutes × 2 devices | |
| D7 | export + 3 runs | 15 minutes | including installing the onnx extra |
| D8 | 5 measurements | 5 minutes | |

## 7. Track B Korean quality

### B1 All sets × all checkpoints + Router auto [step → verification]

```bash
for set in ko_massive_intent_20opt ko_massive_scenario_18 ko_massive_domain_8 ko_klue_ynat_7 ko_klue_nli_3 \
           ko_nsmc_sentiment ko_kmhas_hate ko_3i4k_speechact_7; do   # ko_poc_triage_v1 is on hold (05 §2). en_massive_domain_8 goes in the paired run below
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

- `--batch-size 16` batches only consecutive rows with the same checkpoint and question schema (source: docs/evals.md §Batching and timing). MASSIVE-20 has different options per row, so it is not batched. B's latency column is for reference only; latency is Track D's job.
- `ko_poc_triage_v1` is on hold (until P4 is decided), so it is not in this loop. For `ko_nsmc_sentiment`, which holds two questions, per-question metrics are read with `--slice qid`.
- Verification (H2, second half): the Router auto sends rows containing Hangul 100% to multilingual (`lang.py:43` Hangul range). Rows without Hangul go to the default (english), so "100%" holds only when the data has no non-Hangul rows. Measured 2026-10-02: 7 of the 9 ko sets were 100%; only 3 NSMC rows (1 English sentence, 1 `wjehdlhs;lhlshlsifhow;` typed without switching to the Korean keyboard layout) and 1 K-MHaS type_8 row (English) went to english, and the flips vs the multilingual-pinned run were 2 cases (`results/B/summary_20261002.md` §4).
- typed-decisions is an English fine-tune, so on Korean it is expected to be similar to english or worse. Used as a control only.

### B2 Supplementary metrics [step → verification]

```bash
python scripts/metrics_extra.py results/B/*.json --bootstrap 1000 --seed 13 \
  --out results/B/summary_$(date +%Y%m%d).md
```

Per set × checkpoint: accuracy (CI), macro-F1, Brier, ECE (CI), mean_conf, majority, random, Δ(acc − majority), acc@50%cov. Verification: each set's `choice_accuracy` matches the overall value in the report JSON (self-check of the computation path).

### B3 Instructions language ablation [step → verification]

For YNAT-7 and domain_8, run variant files in which only the instructions are changed to Korean (`*_ko-instr.jsonl` of 04 §4, builder `--instructions ko`; no ko-instr variant was built for MASSIVE-20) and `*_en-desc.jsonl` with the descriptions changed to English (key rendering for scenario_18) with multilingual, on the dev half only. The criteria descriptions are Korean in both variants. Since `questions_sha256` changes, these are separate experiments and not `compare` targets (source: docs/evals.md §Run identity). Verification: McNemar p and the accuracy difference. The better one is fixed as the PoC schema language.

### B4 State format ablation [step → verification]

On YNAT-7, run multilingual with the state changed to (a) a string, (b) `{"title": text}`, (c) `{"utterance": text}`. When the instructions point to a field name in backticks and it does not match the state key, the model ends up looking at a field that does not exist, which is a trap (laya/presets.py `state_field` comment). Verification: McNemar. The state format of the PoC schema in 04 is finalized from this result.

### B5 Analysis table and checkpoint selection rule

| Set | Options | majority | english | multilingual | typed-decisions | Router | Expected range (hypothesis) |
|---|---|---|---|---|---|---|---|
| ko_massive_intent_20opt | 20 | to measure | 0.110 (upstream) | 0.470 (upstream) | to measure | to measure | A2 reproduction value |
| ko_massive_scenario_18 | 18 | to measure | to measure | to measure | to measure | to measure | P0c preview 0.52 (0.66 with play/music merged, `results/poc/P0c_20261002.md`; upstream non-English scenario mean 0.439: BENCHMARKS.md §English vs the rest) |
| ko_massive_domain_8 (PoC main task) | 8 | to measure | to measure | to measure | to measure | to measure | estimated to rise from scenario_18's 0.52 to 0.66 or more through the merge (P0c play/music merge 0.66, `results/poc/P0c_20261002.md`). Input for G1 |
| en_massive_domain_8 (the en pair with the same id, multilingual only) | 8 | to measure | n/a | to measure | n/a | n/a | Korean penalty measurement (07 §5 E1: with Korean descriptions ko 52 vs en 62, not significant). Paired McNemar. The english checkpoint truncates this file's Korean descriptions to 22 tokens per option (04 §7 stats), so the penalty is measured with multilingual on both files and the english run is kept as a reference only. scenario_18's head is at 252/256 tokens, so a wording ablation that lengthens the descriptions hits the cap |
| ko_klue_ynat_7 | 7 | to measure | to measure | to measure | to measure | to measure | P0c n=100 preview 0.65 (acc@50%cov 0.86, `results/poc/P0c_20261002.md`) |
| ko_klue_nli_3 | 3 | to measure | to measure | to measure | to measure | to measure | 0.45\~0.65 (Korean is not among the 15 XNLI languages) |
| ko_nsmc_sentiment (noul / A-B) | 2 | to measure | to measure | to measure | to measure | to measure | 0.60\~0.80 |
| ko_kmhas_hate (noul) | 2 | to measure | to measure | to measure | to measure | to measure | 0.55\~0.75 (upstream held-out moderation 0.530: BENCHMARKS.md §Themes) |
| ko_3i4k_speechact_7 | 7 | to measure | to measure | to measure | to measure | to measure | 0.40\~0.60 |
| ko_poc_triage_v1 (on hold, until P4 is decided) | 05 §4.2 schema | to measure | to measure | to measure | to measure | to measure | P0b n=30 probe intent 0.40\~0.50, binary questions at the always-no level |

The expected ranges are estimates and are replaced by measured values. Checkpoint selection rule: highest `ko_massive_domain_8` test-half accuracy → if tied, lowest ECE after the Track E refit → if still tied, lowest D1 latency.

**Measured values (2026-10-02, `results/B/summary_20261002.md`, CPU fp32, 46 runs).** In the order multilingual / english / typed-decisions / Router.

| Set | multilingual (all / dev / test) | english | typed-decisions | Router | Notes |
|---|---|---|---|---|---|
| ko_massive_domain_8 | 0.526 [0.486, 0.568] / 0.560 / **0.492** [0.432, 0.552] | 0.262 | 0.288 | 0.526 | macro-F1 0.518 (test 0.468), ECE 0.229 (test 0.263), majority 0.126. smart_home predicted 140 (gold 63) and general 80 (gold 62) absorb the errors |
| en_massive_domain_8 (same id) | 0.510 / 0.476 / 0.544 | 0.446 (descriptions truncated) | n/a | n/a | Korean penalty Δ(en−ko) −0.016 [−0.054, +0.022], McNemar p=0.47 (b=50, c=42): no penalty under the Korean-description setting |
| ko_klue_ynat_7 | 0.634 / 0.612 / **0.655** [0.600, 0.710] | 0.216 | 0.234 | 0.634 | society recall 0.21; economy absorbs the errors |
| ko_massive_scenario_18 (n=100) | 0.520 / 0.551 / 0.490 | 0.310 | 0.330 | 0.520 | same as P0c |
| ko_massive_intent_20opt | 0.470 | 0.110 | to measure | 0.470 | matches upstream (A) |
| en_massive_intent_20opt | 0.710 | 0.820 | to measure | n/a | matches upstream (A) |
| ko_klue_nli_3 | 0.750 | 0.448 | to measure | 0.750 | |
| ko_nsmc_sentiment | choice 0.774 / noul 0.638 | 0.528 / 0.516 | to measure | same (996/1000 multilingual) | noul has an always-false bias (false predicted 427/500) |
| ko_kmhas_hate | 0.582 | 0.500 | to measure | 0.582 | false predicted 417/500 |
| ko_kmhas_type_8 | 0.394 | 0.146 | to measure | same (499/500) | |
| ko_3i4k_speechact_7 | 0.178 | 0.174 | to measure | 0.178 | majority 0.144, chance level |

Ablations (dev half, multilingual, McNemar vs base): domain_8 ko-instr 0.540 (−0.020, p=0.23), en-desc 0.532 (−0.028, p=0.34); ynat_7 ko-instr 0.608 (p=1.0), en-desc 0.637 (+0.024, p=0.42); scenario_18 en-desc (key rendering) 0.429 (−0.122, p=0.11). No significant effect → router_v1 keeps English instructions + Korean descriptions. Choice: **multilingual pinned + `lang="ko"`** (p ≤ 2.2e-08 vs english and typed-decisions on the test half; the Router gives the same answers on Korean and only adds the english loading path). Preliminary G1 reading: domain_8 test 0.492 is −0.308 from the 0.80 criterion, and even the CI upper bound 0.552 falls short. The dev 0.560 vs test 0.492 gap comes from the difference in scenario composition under the index-parity split (test has 1 alarm row, calendar 0/16). With Korean-only traffic the Router auto should equal multilingual pinned; with English mixed in, decide together with the D5 reload cost.

## 8. Track C robustness

### C1 Option-order flip [step → verification]

```bash
python scripts/probe_option_order.py data/evals/ko_massive_domain_8.jsonl data/evals/ko_klue_ynat_7.jsonl data/evals/ko_massive_scenario_18.jsonl \
  --model multilingual --device cpu --permutations 5 --seed 13 --split dev --splits results/B/B_splits.json \
  --out results/C/C1_option_order_$(date +%Y%m%d).json      # dev half only; the test half is not touched
```

Same method as upstream: for each item, build a dict whose criteria key order is shuffled with `rng.shuffle`, and count a flip when the argmax differs from the original-order answer (source: research/scripts/build_benchmark_nb.py:640-678). Report: mean flip rate per permutation, any-flip rate, accuracy per permutation. Reference values: en 20 options 0.150 (laya)/0.230 (multilingual), 6-label emotion 0.040/0.090, Jev 0.13 (source: BENCHMARKS.md §Option-order robustness); zh CS routing 28%, voice 10.6% (source: BENCHMARKS.md §Community evaluation zh). Verification (H5): 0.10\~0.30 at 7\~20 options. Acceptance for the PoC schema is ≤ 0.10 (00 §6).

**Measured values (2026-10-02, `results/C/C1_option_order_20261002.md`, dev half, 5 permutations, multilingual).** router_v1 (domain_8, n=250): flip 0.270 [0.230, 0.310] per permutation, any-flip 0.512, accuracy 0.528\~0.560. ynat_7 (n=245): 0.168 [0.135, 0.206], any-flip 0.318. scenario_18 (n=49): 0.241, any-flip 0.469. The original-order answers match the Track B reports 100% in argmax. **G4 (≤ 0.10) fail**, H5 supported. 74% of the 337 flips came from items answered incorrectly in the original order, and counting only items with answer_confidence ≥ 0.9 (108/250) the flip is 0.094. A position effect exists (chi2 p=0.0009; slot 1 picked less, 2\~4 more), but the smart_home absorption is 58.6 on average over permutations and still 60 when moved to the end, so it is a semantic phenomenon. The suspected first-option over-prediction is rejected (productivity is under-predicted).

**Schema v2 probe (`results/C/C_schema_v2_20261002.md`, 250 domain_8 dev rows).** vs v1 0.560: v2a strengthened descriptions 0.536, v2b general removed (7 options, 220 rows) 0.545, v2c example sentences added 0.540 (option tokens 418 > limit 240, so all were truncated to 30 tokens; the head 512 diagnostic run gave 0.408), v2d reordered 0.516, v2e 5 classes 0.536. **No variant beats v1**. general rows are not filtered out by the gate (in v2b, 23 of the 30 general rows went to smart_home, median confidence 0.76). As an alternative that changes the contract, summing the v1 probabilities into 5 classes gives dev 0.682 (p=3.8e-4 vs v2e 0.536).

### C2 Wording ladder [step → verification]

```bash
python scripts/probe_wording_ladder.py data/evals/ko_poc_triage_v1.jsonl --model multilingual --device cpu \
  --out results/C/$(date +%Y%m%d-%H%M)_wording_ladder.json
```

Replicate the zh ladder in Korean on the PoC schema: for choice, criteria-only → +scenario sentence → +JSON state; for noul, plain (`poc/schema/triage_v1.json`, no criteria) → +criteria (`poc/schema/triage_v1b.json`, Korean `true`/`false` descriptions, 05 §4.1) → +scenario → +JSON state. Per step: accuracy, macro-F1, noul always-true rate (share with p ≥ 0.5), mean/SD conf. Reference values: zh choice 0.722 → 0.778 → 0.667, noul 0.667 → 0.458 → 0.472 → 0.417, i.e. once criteria were attached every noul collapsed to true (source: research/benchmarks/zh_short_commands/README.md). Verification: McNemar per step. The best step is fixed as the PoC schema wording and reflected in 04/05. Early signal: Korean instructions gave Δ0 on YNAT and scenario-18 (n=100, `results/poc/P0c_20261002.md`), and in the triage probe (P0b, `results/poc/P0b_20261002.md`) there was a small effect (+1) only on is_urgent.

### C3 noul vs 2-choice with neutral keys [step → verification]

Run NSMC's noul variant, its A/B 2-choice variant (04), and a variant with the `labels: {"true": "A", "false": "B"}` override on noul (source: README §Honest limits) with english/multilingual. Verification (H6): McNemar, since the items are the same. Based on the result, decide whether the PoC's binary questions stay noul or become 2-choice. P0b early signal (n=30, `results/poc/P0b_20261002.md`): `labels` A/B has no effect (93/120 = baseline), A/B 2-choice collapses to A (68/120), criteria are mixed per question (churn_risk 28/30, refund_requested false positives). H6 ("noul < 2-choice with neutral keys") points the opposite way from the probe, and this C3 on NSMC n=500 decides it.

### C4 Negation [step → verification]

Run `data/evals/ko_negation_probe.jsonl` (built as pairs) with the two checkpoints. Accuracy on the affirmative/negated halves, the probability distribution of "cancel"-type labels on the negated half, paired McNemar. Reference #377: english sent 4/4 negated requests to cancel_account, multilingual 2/4 (source: README §Honest limits). Verification (H7). On failure, this becomes a design input that the PoC must filter negation patterns with rules rather than confidence.

### C5 Boolean-word labels [step → verification]

Render one PoC binary question with the keys `yes`/`no`, with semantic keys (e.g. `refund`/`no_refund`) and with opaque keys `A`/`B`, and compare accuracy. Upstream recommends avoiding boolean-word keys (source: README §Honest limits). Verification: McNemar among the three variants; the best key style is reflected in 04.

### C6 High cardinality [step → verification]

Run `ko_massive_intent_full60.jsonl` (a single question over about 60 intents) with three settings.

```bash
# (a) default budget
laya-evals run data/evals/ko_massive_intent_full60.jsonl --model multilingual --device cpu \
  --json results/C/$(date +%Y%m%d-%H%M)_full60_default.json
# (b) head_max_len 512 / max_len 1024, (c) predict_shortlist k=20: the harness has no flags for these, so a short python snippet
python - <<'EOF'
import json, laya
from laya.evals import Dataset, evaluate
from laya.evals_shortlist import evaluate_shortlist
from laya.shortlist import embed_fn_from_agent
agent = laya.load("models/laya-multilingual", device="cpu")
ds = Dataset.from_jsonl("data/evals/ko_massive_intent_full60.jsonl")
agent.cfg["head_max_len"], agent.cfg["max_len"] = 512, 1024
json.dump(evaluate(agent, ds).to_json(), open("results/C/full60_head512.json", "w"))   # caution: see the defect note below
agent.cfg["head_max_len"], agent.cfg["max_len"] = 256, 1024
rep = evaluate_shortlist(agent, ds, embed_fn_from_agent(agent), k=20,
                         checkpoint_id="laya-multilingual@55cf4c4", embedder_id="laya-multilingual-meanpool@55cf4c4",
                         dataset_path="data/evals/ko_massive_intent_full60.jsonl")
json.dump(rep.to_json(), open("results/C/full60_shortlist20.json", "w"))
EOF

**Defect found before running; needs fixing.** `evaluate()` calls the runner's `predict(..., model=...)` (laya/evals.py:704), but `Agent.predict` has no `model` argument (laya/agent.py:1704). Passing an `Agent` as is, as in the snippet above, raises a TypeError. Either pass a `Router` (in which case the `cfg` change must be made on the agent held by the Router) or use a thin runner wrapper that drops the `model` keyword (the approach used in the head 512 diagnostic run of Track C: `results/C/C_schema_v2_20261002.md`).
```

`EvalReport.to_json()` returns a `{config, overall, slices, cases}` dict (source: laya/evals.py:376-379). Report: accuracy per setting, and for (c) `shortlist_recall_at_k` and the `retrieval_miss`/`decision_miss` distribution (source: docs/evals.md §Attributing shortlist errors). Verification: the default budget should collapse, stuck at the floor of `max(4, (256-16)//60) = 4` tokens per option (banking77 with 77 labels 0.425, the same on both: source BENCHMARKS.md §On the public datasets); the 512 budget should improve it (English MASSIVE 58 labels 24/58 → 34/58 at 384: source README §Command line); and the shortlist should move in the direction of the reporter's figures 54.3 → 60.8% (source README §Honest limits, not re-measured upstream).

### C7 score first-level bias [step → verification]

From the score question `frustration` of ko_poc_triage_v1 (05 §4.1), draw 50 items whose gold is the lowest level and 50 at the highest level, and compare the first-level selection rate of multilingual and english with the gold proportion. Reference #131: multilingual almost never picks the first level, in any language (source: README §Honest limits). Verification: if the first-level selection rate is below half of the gold proportion, the bias is confirmed. Skipped if the PoC schema has no score question.

### C8 Long context, indicative [step → verification]

Run `scripts/bench_long_context_ko.py`, a copy of the upstream script with only the 20 `REQUESTS` and the `FILLER` changed to Korean (the only code change is those two constants), with `--device mps` (pads 0/1000/2000/4000/7000, the default limit and `max_len=8192`). Position sensitivity only at 4,000 tokens, with 5 positions. n=20 gives a ±0.22 CI per cell, so it is reported as indicative only (source: research/README.md §Headline findings). Latency reference: a 4,000-token input takes about 1.7 s on an Apple GPU (source: README §Installation). Verification: accuracy should drop at pad ≥ 1000 with the default limit and recover at 8192.

### C9 Device parity [step → verification]

In addition to A5, run the sets whose rows share a question (YNAT-7, NSMC) with `--device mps --batch-size 16` and compare case by case with B's CPU reports (`python scripts/metrics_extra.py parity <cpu_report> <mps_report>`). Add 1 more run with fp32 forced via `LAYA_MPS_AMP_MIN_ROWS=100000`. Verification criterion §3.4. If it passes, the remaining sets of B can be run on MPS to save time.

### C10 Routing robustness [step → verification]

Rerun the 46-case battery of `results/korean_support/part3_routing_battery.md` (pure Korean, mixed text with a Latin majority, short Korean inside an English wrapper, romanization, jamo, emoji, mixed Hanja, NFD) with `scripts/probe_routing.py`, adding NFD/NFC pairs and sentences from the PoC sets. Uses only `Router().route()` and `laya.lang.analyse()`, without loading a model. Report: `model` and `reason` per input type, the difference between `default="english"` and `"multilingual"`, and the results when `lang="ko"` is set explicitly. Baseline: the 2026-10-02 battery was 28 correct / 4 harmless / 4 default-dependent / 10 failures, and the failure types F1\~F6 are in `07_korean_support_audit.md` §4. Verification: record any failure type that newly appears outside the list of 07 §4; with `lang="ko"` set explicitly, all 46 cases must go to multilingual.

## 9. Track E calibration

### E1 as-shipped [step → verification]

From the B reports, ECE per set × checkpoint and a 15-bin reliability table (metrics_extra; figures optional). multilingual ships without a fitted temperature, and english is over-confident (source: README §Calibration). Upstream refit effect: laya 0.466 → 0.081, multilingual 0.314 → 0.106 (source: BENCHMARKS.md §Calibration). There is also a report that on a routing task it was under-confident instead, so no direction is assumed (source: BENCHMARKS.md §Calibration on a routing task). Verification (H4, first half): whether ECE > 0.25 on at least half of the ko sets.

### E2 refit [step → verification]

```bash
python scripts/calibrate_ko.py --model models/laya-multilingual --device cpu \
  --sets data/evals/ko_massive_domain_8.jsonl,data/evals/ko_klue_ynat_7.jsonl \
  --splits results/B/B_splits.json --pooled --per-task --min-bucket-n 100 \
  --out-payload poc/calibration/ko_v1.json --out results/E/$(date +%Y%m%d-%H%M)_calibration_multilingual.json
```

- No new split is made; `results/B/B_splits.json` is used as is (§3.2). A new hash50 split would mix the test rows used for G1 into the fit. On the fit half (dev), build (qtype, logits, target, k) records with `records_from_labeled(agent, pairs)` and run `fit_temperature_map(records, compute_ece=True, seed=13)` (laya/calibrate.py:211, :261).
- **Upstream defect (issue candidate).** `records_from_labeled` has no `@torch.no_grad()`, so calling it with a real `Agent` raises `RuntimeError: Can't call numpy() on Tensor that requires grad` (laya/calibrate.py:286 → agent.py:1177; `predict_batch` does have the decorator, agent.py:1248; the upstream tests use a stub forward and do not exercise this path, tests/test_calibrate.py:425-466). `scripts/calibrate_ko.py:93` wraps the call in `torch.no_grad()`. This is the same execution condition as predict_batch, so it is not a workaround that changes the numbers (confirmed by argmax 500/500 agreement with the B reports at T=1).
- Buckets are `temp_bucket(qtype, k)`: choice:3-5, choice:6-10, choice:11+, noul:2, score:3-5, etc. A per-bucket temperature is recorded only with `MIN_BUCKET_N = 2000` or more (calibrate.py:205); below that, only the type scalar (`MIN_TYPE_N = 10`) remains (constants at the top of laya/calibrate.py and the module docstring). With 250\~500 items per set no bucket temperature comes out, so report both (i) the official map (type scalar) and (ii) a low-floor (min_n 100) version that calls `fit_one_temperature` (laya/calibrate.py:71) per bucket directly, and choose the one used as the payload by held-out performance. If the records fall into a single bucket (choice:6-10), the two values are the same. Pooling sets is itself a design decision and is recorded.
- Cross-apply pooled (4 sets combined) vs per-task (per set) fits to each held-out half to check transferability. Whether a T fitted on YNAT also lowers ECE on the PoC set is the key point for running the PoC.
- Report: raw T per bucket, whether it was clamped (`[0.5, 5.0]`), held-out ECE/NLL before → after. If, as in the zh case, the noul:2 raw T exceeds 5 (10.23 → 5.00, ECE 0.180 → 0.098: source BENCHMARKS.md §Community evaluation zh §3), record the fact that the clamp limits the calibration range.
- Verification (H4, second half): held-out ECE ≤ 0.10.

**Measured values (2026-10-02, `results/E/E_summary_20261002.md`, dev fit → test evaluation, multilingual).** T (choice:6-10, no clamping): domain_8 2.0245, ynat_7 1.8149, pooled 1.9161. test ECE before → after: domain_8 0.263 → 0.098 (pooled) / 0.123 (per-task), ynat_7 0.148 → 0.063 (pooled). NLL improved everywhere (domain_8 1.727 → 1.37\~1.39). The adopted fit is pooled (pre-registered rule: "only if pooled lowers the domain_8 test ECE by more than 0.02"; actual 0.025). G3 passes on the point estimate but is borderline (moving T over 1.8\~2.2 gives 0.077\~0.119). The remaining overconfidence comes from the dev → test accuracy gap (0.560 → 0.492).

### E3 Coverage curves and min_confidence sweep [step → verification]

From the (pre/post-calibration) probabilities of the held-out half, metrics_extra computes coverage (share with answer_confidence ≥ T) and covered accuracy at T ∈ {0.50, 0.55, ..., 0.95}. As a cross-check, run `laya-evals run ... --min-confidence 0.8` and see whether the abstained share in the `abstention` field matches 1 − coverage(0.8) of our curve (source: docs/evals.md §The abstention gate). The torch-path harness does not take a calibration payload (laya/evals_cli.py:325 only builds `Router(device, preload=False, **pins)`), so the post-calibration curve is computed by `scripts/calibrate_ko.py`, which has the logits (`metrics_extra.py coverage` has only the report's probabilities rounded to 4 digits and gives only the pre-calibration curve). Re-verifying `--calibration` on the ONNX path and the `--min-confidence` cross-check were outside the scope of the 2026-10-02 runs. Verification: the coverage of the two paths agrees within ±0.01.

**Measured values (2026-10-02, domain_8 test, T chosen on dev).** Error budget 5%: as-shipped T 0.9941 → test coverage 0.232 / error 0.069 (exceeded), refit pooled T 0.8799 → 0.224 / 0.036. 10%: 0.300 / 0.093 → 0.308 / 0.091. 15%: 0.392 / 0.173 → 0.400 / 0.160. Calibration changes the gate scale (0.994 → 0.880) and ECE, but barely changes the maximum coverage per budget (5%: 0.216 → 0.228) or the AUROC (0.840 → 0.841). The premise that a scalar T does not change the ranking between rows holds exactly only for k=2; for k=8, 2.3% of row pairs change, but the effect on the frontier is within ±0.03. Per-domain T gives dev coverage 0.180 → 0.316 but exceeds both the 5% and 10% budgets on test, so it is **rejected** (overfitting on 12\~66 dev rows per domain). With the single T, general routes 0/40, so it is effectively always FALLBACK. At accuracy a, the upper bound of coverage with error e or less is a/(1−e) = 0.518, so G2 (0.70) is unreachable by definition without improving G1.

### E4 Payload persistence [step → verification]

Write `poc/calibration/ko_v1.json` with `calibration_payload(...)`; the PoC applies it with `laya.load("models/laya-multilingual", calibration="poc/calibration/ko_v1.json")` (the `calibration` argument, laya/agent.py:1875) or `apply_calibration_payload(agent, payload)` (laya/calibrate.py:393). Verification: rerun the held-out half with the calibrated agent; ECE within ±0.005 of E2's after value. The payload's config-identity warning (laya/calibrate.py `_warn_if_identity_mismatch`, :330-337) compares only the path string and the config, not the weight SHA. Loading via the realpath raises a UserWarning even for the same checkpoint, so the service loads with the string `models/laya-multilingual` and the SHA is pinned separately in the ADR. The warning is neither a necessary nor a sufficient condition for a SHA change.

**Measured values (2026-10-02).** `poc/calibration/ko_v1.json` = pooled fit, temperature [1.9161, 1, 1] (type-scalar form), sha256 a217cb5d…. domain_8 test ECE rescored with `laya.load(calibration=)` 0.0980 (|Δ| 0 vs the E2 value); applying `apply_calibration_payload` to a fresh agent gives identical answers 250/250. Pending decision: the type-scalar form also applies T=1.92 to other choice questions that were not validated (k=2, 3-5, 11+), so the ADR chooses between it and the form restricted to `{"choice:6-10": 1.9161}` (for router_v1 both forms give the same output).

### E5 Acceptance

00_README.md §6: held-out ECE ≤ 0.10 after refit, and coverage ≥ 0.70 at error ≤ 5% on the `ko_massive_domain_8` test. If not met, hand over to the gating policy of 05 (abstain → LLM fallback) and to a review of P4 fine-tuning. The threshold is a policy set by 05; here only the curves are supplied.

**Verdict (2026-10-02).** G3 pass (borderline, pooled 0.098; 0.123 with per-task, which fails). G2 **fail** (0.224 vs 0.70; upper bound 0.518). With alternative budgets, 0.308 at 10% and 0.400 at 15%.

### E6 noul decision threshold [step → verification]

multilingual's noul has p(true) pushed below 0.5 regardless of language, yet it reads the state in terms of ranking (AUROC 0.76\~0.92) (`07_korean_support_audit.md` §5 E4). Temperature cannot move the 0.5 boundary of a 2-class softmax, so this is a matter of the decision threshold, not of calibration. For each noul question, draw the ROC from the dev-half p(true) and gold labels, pick the Youden J maximum (or the point of maximum recall that satisfies a 5% error budget) as `T_noul[qid]`, then compare accuracy, positive rate and precision/recall on the test half between the 0.5 cutoff and the `T_noul` cutoff. It is applied not in laya but in the policy layer of 05 (`T_NOUL` in `decide()`). Verification: accepted if, on the test half, the accuracy with `T_noul` beats the always-no base rate and the positive rate falls within ±5pt of the expected value. The results are recorded in `results/E/*_noul_threshold.json` and the ADR.

**Measured values (2026-10-02, NSMC noul, `results/E/20261002-1733_calibration_multilingual_noul_threshold.json`).** AUROC dev 0.860 / test 0.822. dev Youden threshold p(true) ≥ 0.0073 (the extreme tail relative to the dev median of 0.0099). test accuracy 0.725 (0.5 cutoff 0.641, always-no 0.522, semantic-key 2-choice 0.773), predicted positive rate 0.506 (gold 0.478), which meets the acceptance criterion. It is, however, below 2-choice and has to be re-chosen if the wording or the checkpoint changes.

## 10. Track F baselines

### F1 majority / random [step → verification]

metrics_extra computes them from the expected labels: majority = share of the most frequent label, random = 1/k (noul 0.5). Multi-question sets keep a separate majority per question (the per-question majority method of upstream typed-decisions, 0.461: source BENCHMARKS.md §typed-decisions). Verification: reported together with a label-distribution table per set.

### F2 LLM zero-shot, optional [step → verification] (not run: no API key provided, as of 2026-10-06)

```bash
python scripts/llm_baseline.py data/evals/ko_poc_triage_v1.jsonl data/evals/ko_klue_ynat_7.jsonl \
  --model claude-haiku-4-5-20251001 --n 300 --seed 13 --concurrency 4 \
  --cache data/raw/llm_cache --prompts-out results/F/prompts \
  --out results/F/$(date +%Y%m%d-%H%M)_llm_haiku.json
```

- Requires `ANTHROPIC_API_KEY` in `.env` (never committed). The prompt renders the instructions and criteria text of the laya question as is and asks for JSON containing only the label. temperature 0, 3 retries, responses cached in `data/raw/llm_cache/*.jsonl` (not included in the public repository), so reruns cost 0.
- Record: input/output tokens, wall-clock p50/p95, invalid-output rate. Cost is the token count × the unit price on the official pricing page (looked up at run time, with the unit price and date recorded in the run card). Unit prices are not hardcoded.
- State the asymmetry in the table: the LLM takes 1\~3 s per call and is billed, while Laya's marginal cost ≈ 0. The LLM gives no probabilities, so there is no ECE/coverage comparison; only accuracy and latency/cost are compared.
- Verification: Laya is also rerun on the same 300 items for a paired McNemar test.

### F3 Supervised reference values

Looked up in the literature when the report is written, noting the source, model, split and metric: KLUE YNAT macro-F1 and KLUE NLI accuracy (KLUE leaderboard/paper), NSMC accuracy (0.89\~0.90 for fine-tuned BERT-family models is common wisdom, to be verified), and the original papers' figures for 3i4K and K-MHaS. The column header says "supervised ceiling", and these values are not compared directly with zero-shot.

### F4 Published Jev figures

| Source | Figures |
|---|---|
| AbdelStark/jev-benchmarks | AG News 0.910, Banking77 0.870 (72 labels), DAIR Emotion 0.480, p50 236\~246 ms |
| nibzard/decision-model-benchmark | ECE 0.246, banking77 0.763, option-order flip 13%, p50 264\~276 ms |

(source: research/README.md §On comparisons with Jev, BENCHMARKS.md §Headline). There are no published Korean Jev figures, and the only Korean values we measured are the n=24 manual sample of F5. These are 3rd-party measurements with different samples and prompts, not a controlled comparison.

### F5 Manual Jev comparison (done 2026-10-06)

With no official API key, a small-sample manual comparison was done through the public 3rd-party playground https://jevplayground.com (`results/F/jev_playground_manual_20261006.md`, run card `results/F/F_jev_20261006.md`).

- Protocol: from the `ko_massive_domain_8` test half, after excluding 16 rows that overlap with train, 3 rows per domain drawn with `random.Random(13)`, 24 rows in total (`results/F/jev_sample_24.jsonl`). Question "Which domain should handle this request?", with the 8 options entered as `key: Korean description` (the same strings and order as router_v1). 25 requests (1 of them a 502), gap ≥ 21 s, the English-key-only pass 2 skipped. Laya values were looked up for the same rows in the Track B and P4 reports.
- Results: Jev 20/24 (0.833 [0.641, 0.933]), Laya zero-shot 10/24 (0.417), ft-v1 22/24 (0.917). Jev vs zero-shot b=10 c=0 p=0.002, Jev vs ft-v1 b=0 c=2 p=0.5. Median displayed latency 249.5 ms (browser POST 497.5 ms) vs the local P2 round trip 20.1 ms. Jev's 4 errors had low confidence, with top probabilities of 41\~86%, and 2 of them were "게임" (game) utterances not covered by the media description.
- Caveats: n=24 single pass, the playground (model version not shown, 1-field label format), run only within the free site's usage limits. Whether Jev or ft-v1 is better cannot be decided from this sample.

## 11. Execution order and time estimates

Assumptions: multilingual CPU, 20 options, 1 question ≈ 0.2\~0.4 s (adjusted from EPYC 4-core 3 options 193 ms), english ≈ 3x, MPS 1 question ≈ 30\~60 ms. All to be replaced by measurements.

| Order | Track | Prerequisites | Expected wall time | Outputs |
|---|---|---|---|---|
| 1 | A reproduction | 02 done, ko_massive_intent_20opt of 04 | 30 minutes (including debugging) | results/A/*, gate verdict |
| 2 | D performance | A passed | 2\~3 h | results/D/*, input for the device choice |
| 3 | B quality | all sets of 04, time re-estimated from D1 | CPU 2.5\~3 h (8 sets × 3+1 runs × \~400) | results/B/*, summary.md |
| 4 | C robustness | B, the probe sets of 04 | 2\~3 h (dominated by the ×5 permutations) | results/C/* |
| 5 | E calibration | B, C9 | 30 minutes | poc/calibration/ko_v1.json, results/E/* |
| 6 | F baselines | B items fixed, API key (optional) | 30 minutes | results/F/* |
| 7 | Report | all | half a day | results/REPORT.md |
| 8 | Dashboard | all report JSONs, `verdicts.json` and `go_no_go.json` filled in | 15 minutes | results/dashboard/index.html |

About 1.5\~2 working days in total. If C9 parity passes, B/C can be run on MPS to cut this to half or less, but the PoC sets and MASSIVE-20 must keep CPU reference values. 05 P4 fine-tuning is extra work outside this table: probe 721 s (1,000 rows), main training run estimated at 3.1\~3.2 h with GPU contention / 1\~1.5 h when idle, evaluation about 10 minutes (`results/P4/P4_probe_20261002.md`). Measured (2026-10-03, run `full_20261003-1156`, GPU idle): training 2,150 s (35.8 minutes, 15.6 items/s, 11,094 rows × 3 epochs), 44 minutes in total including evaluation and the flip probe (`results/P4/full_20261003-1156_timing.json`, `results/P4/full_run_status.log`). Measured durations (2026-10-02): B 46 runs 22 minutes, C 4.9 minutes, E 3.4 minutes (model time). **Track D must run alone**: while B/C/E were running, another heavy process (an experiment from another project) shared the machine, so the latency column of the B reports is not interpreted.

## 12. Report structure

`results/REPORT.md` fills in the template of 06_templates.md §2. Required contents:
1. Environment and pins (env_*.json summary, checkpoint SHA, versions).
2. Track A reproduction table (upstream vs measured, difference, verdict).
3. Track D latency/throughput/memory tables and a device recommendation.
4. Track B set × checkpoint table (§7 B5 layout) and the checkpoint choice.
5. Track C robustness tables (flip, ladder, noul/choice, negation, cardinality, parity).
6. Track E ECE before/after calibration, coverage curves, adopted payload.
7. Track F baseline table (with fairness notes).
8. Hypothesis verdict table: for each of H1\~H10, supported/rejected/unresolved, the path of the evidence result file, and the CI. The source of truth is `results/verdicts.json` (maintained by hand: for each of H1\~H10 `{"verdict": "지지|기각|미결", "run_ids": [...], "note": "..."}`, the Korean verdict values meaning supported|rejected|unresolved), and REPORT.md §3 transcribes that file.
9. Fill in the 00_README.md §6 Go/No-Go (measured value and pass/fail per item). The source of truth is `results/go_no_go.json` (for each of G0\~G7 `{"value": ..., "pass": true|false|null, "run_ids": [...]}`; items computable from the report JSONs are filled in by `build_dashboard.py`, the rest by hand), and REPORT.md §4 transcribes that file.
10. Design inputs handed to 05_poc_plan.md (checkpoint, device, schema wording, gating policy, handling of negation, need for fine-tuning).
11. Generate `results/dashboard/index.html`: `python scripts/build_dashboard.py --results results/ --out results/dashboard/index.html --open`. It is generated from the same JSON as REPORT.md, so if the figures of the two outputs differ, the JSON is authoritative. Sections: (1) summary (environment versions, SHA and device, a one-line verdict, number of source run_ids) (2) Track A reproduction: upstream vs measured table (ko/en × english/multilingual, acc and ECE, colored by the ±0.03 verdict) (3) Track D performance: median/p95 bars per checkpoint × device × number of questions, thread-sweep lines, batch speedup bars, cold load and RSS tables (4) Track B quality: set × checkpoint accuracy table (with majority and CI) and ECE table, Router `model` slice (5) Track C robustness: flip-rate bars (per set, upstream reference lines 0.150/0.230), wording-ladder lines (accuracy, always-true rate), accuracy on negation pairs, bars for the 3 high-cardinality settings, parity table (6) Track E calibration: reliability diagram (15 bins, before/after), coverage@accuracy curves (before/after, with a 5% error-rate line), table of T per bucket (7) Track F baselines: per-set bars of laya vs majority vs LLM (if available), latency and cost table (8) hypothesis H1\~H10 verdict table (`verdicts.json`) (9) Go/No-Go matrix (`go_no_go.json`, with the 00 §6 criteria alongside) (10) list of run_ids and relative links to the result files. If it needs to be shared, the single generated HTML file can be published as an artifact or similar.

## 13. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| MPS numerical drift (fp16, per-shape kernels) | contaminates accuracy comparisons | §3.4 parity gate; CPU fp32 reference values must be kept |
| Dataset access/licensing (script-based datasets incompatible, 401) | missing sets | 04 provides a raw download path; missing sets are marked "not run" in the report |
| Label quality (hand-written PoC labels) | distorts the H3/D1 verdicts | finalize the label policy first; report the agreement rate on a double-labeled sample of 50 |
| CPU time blow-up (english 50q calls take tens of seconds) | schedule overrun | run D1 first and rescale B/C; option to shrink the sets to 300 |
| Thermal throttling (laptop-class SoC) | latency figures fluctuate | AC power, re-measure 10 minutes apart, check that the median is within 10% |
| HF online/offline switching, cache re-downloads | a different revision gets loaded | `LAYA_REVISION=reviewed`, check `revisions` in the report, `HF_HUB_OFFLINE=1` for pinned runs |
| Upstream version drift (frequent 0.3.x releases) | not reproducible | pin everything: laya 0.3.23, torch 2.14.1, transformers 5.18.0, checkpoint SHAs |
| Over-interpreting n=100 | wrong checkpoint/policy choice | report CIs; rank only on sets with n ≥ 400 |
| Env variable name clash (`LAYA_MODELS`) | laya-serve interprets a directory path as a checkpoint name and fails | resolved: env.sh exports only `LAYA_MODELS_DIR`; research scripts get `LAYA_MODELS="$LAYA_MODELS_DIR"` inline (02 §2.8) |
| Routing failures on mixed text | mixed text with a Latin majority and short Korean inside an English wrapper go to english, contaminating the Korean-set figures | Korean sets are run with `--model multilingual` pinned or `lang="ko"`; Router auto runs check the routing result via the `model` slice (C10, 07 §4) |
| NFD input | 3.09x more tokens; fragmentation into jamo and bytes contaminates accuracy and budgets (07 §3) | the eval-set builder saves NFC (the common rule of 04 §5 does not normalize, so if a source is NFD this is recorded in MANIFEST); the PoC applies NFC before inference |
| Other load running concurrently (2026-10-02: an experiment from another project) | contaminates latency figures | the accuracy tracks (A/B/C/E) are deterministic and unaffected. Track D is run alone when the machine is quiet, recording `pmset` and the load state in the run card |

## Open questions / assumptions

1. (Confirmed) The `laya-evals run --json` report keeps the full answer dict, including probabilities, in `cases[].answer` (laya/evals.py:728-744). metrics_extra does not call the model again.
2. Whether the ko ECE 0.680/0.311 at BENCHMARKS.md:71 are post-clamp values was inferred from the macro ECE (0.5709) in the table header. If A2 lands outside ±0.05, interpret it first as a regime difference.
3. Assumes that the row order of mteb/amazon_massive_intent is the same as at the time of the upstream sweep. Checked via `id` in A2.
4. (Confirmed) The Korean-instructions variant of B3 is `*_ko-instr.jsonl` of 04 §4 (builder `--instructions ko`).
5. C7 is meaningful only if the PoC schema has a score question. Decided after the 05 schema is finalized.
6. (Confirmed) The ONNX int8 output file name is `<stem>.int8.onnx` (scripts/export_onnx.py `int8_output_path`), and `EvalReport` is serialized with `to_json()` (laya/evals.py:376).
7. The LLM baseline is run only with an API key and cost approval. The model is assumed to be claude-haiku-4-5-20251001 and can be changed.
8. (Resolved) The `LAYA_MODELS` name clash is solved by the convention of 02 §2.8: env.sh exports only `LAYA_MODELS_DIR`, upstream research scripts (research/scripts/bench_local.py:39) get `LAYA_MODELS="$LAYA_MODELS_DIR"` inline, and laya-serve's `LAYA_MODELS` is given as a list of names on the server command line.
9. The assumption that 10 CPU threads (P-cores) is optimal is settled by D2.
10. The supervised reference values are filled in by a literature lookup at report time; the "0.89\~0.90 (NSMC)" in this document is unverified common wisdom.
11. The M4 Pro estimates in the D1 table (CPU 80\~500 ms, MPS 20\~80 ms) are hypotheses extrapolated from the EPYC/T4 figures, with no supporting measurement.

**English** | [한국어](03_benchmark_plan.ko.md)
