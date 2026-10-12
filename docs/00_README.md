# Laya benchmarking · PoC execution guide (00_README)

**Purpose**: Entry point to the document set for benchmarking [NandhaKishorM/laya](https://github.com/NandhaKishorM/laya) 0.3.23 on this Mac and carrying the work through to a Korean PoC. It keeps in one place what to read and run in which order, which assumptions the work rests on, and what the final Go/No-Go decision is based on.
**Prerequisite documents**: none (this document is the entry point).
**Outputs**: document map, Phase 0\~4 execution order, list of assumptions to be verified, Go/No-Go decision matrix, glossary.

## 1. Purpose and scope

The target is laya 0.3.23 (PyPI release 2026-10-01), upstream commit `4aa6761be8173de4ce6d92c31b3e40b6eaf59a7c` (2026-10-01). Laya is a non-autoregressive decision engine that answers three kinds of typed question (choice / score / noul) in a single encoder forward pass; it provides three checkpoints (english, multilingual, typed-decisions) and a Router that picks the checkpoint matching the input language. Detailed analysis: `01_laya_analysis.md`.

**In scope**
1. Reproduce those upstream published figures that are reproducible on this Mac (Korean MASSIVE intent, latency scaling, batch equivalence) to validate the measurement pipeline itself (Track A, D).
2. Measure Korean quality on public datasets that upstream did not measure (KLUE-YNAT, KLUE-NLI, NSMC, K-MHaS, 3i4K) and on our own label sets (Track B).
3. Probe whether the limitations upstream itself reports (option-order instability, noul label following, negation, budget collapse at high cardinality, over-confidence) also hold for Korean (Track C, E).
4. Compare against baselines (majority/random, optionally an LLM zero-shot) to map out "the area where it can be used zero-shot" (Track F).
5. Pick one scenario, build a PoC in the form of a real service (based on `laya-serve`), validate it through load, calibration and threshold policy, and then decide whether to adopt it (`05_poc_plan.md`). The results are left in a form that can be checked directly in a browser demo UI (`/poc/ui/`) and a results dashboard (`results/dashboard/index.html`).
6. Laya vs Jev small-sample comparison: give both systems the same state, question and option text and compare accuracy, calibration, robustness, latency and cost. The only access is the public playground, so the comparison runs on a small sample at manual speed (`09_laya_vs_jev_plan.md`). **Done (2026-10-07)**: zero-shot, Jev is more accurate than Laya (of 8 tasks, Laya significantly better on 0, Jev significantly better on 2 after Holm correction), with the largest gaps on instruction-style and multilingual tasks. Macro accuracy over the 8 tasks is Jev 0.828, Laya Router 0.661 (`results/F/jev_cmp/summary.md`).
7. 3-arm extension (Jev vs vanilla Laya vs trained Laya): split the tasks into those in Laya's training mix (in-mix: T2, T5, new T9·T10) and those outside it (held-out: T1, T3, T4, T6, T7, T8), and add Laya fine-tuned on the task data as a third arm. Jev is not run again, and training checks V1-V6 also decide whether Laya was trained properly (`11_three_arm_plan.md`). **Done (2026-10-09, including the replicate run)**: Laya fine-tuned on task labels (about 6,400 per task) has no task, in either run, where it is significantly below Jev on the Jev items after Holm correction, and the training gain is concentrated on the tasks upstream did not train on (ext trained − vanilla: in-mix category +0.017, held-out category +0.252). Only verdicts whose conclusion matches the seed 14 replicate run are confirmed: 27 of 30 are confirmed and 3 (T4·T8 Jev items) are inconsistent. The calibration-separation column and the Jev measurement of T9·T10 (session S7) are also done (`results/T3arm/summary.md`, `11_three_arm_plan.md` §9).

**Out of scope**
- No direct measurement of the TypeSafe Jev API. Without API access we cite 3rd-party published figures as upstream does; instead, we ran a 24-item manual comparison on the public playground (2026-10-06, `results/F/jev_playground_manual_20261006.md`: Jev 0.833 / zero-shot 0.417 / ft-v1 0.917) and then completed an 8-task controlled comparison (2026-10-07, item 6) (source: BENCHMARKS.md intro, research/README.md "On comparisons with Jev").
- (Scope change) Fine-tuning was at first only an optional PoC step, P4, but P4 was carried out (2026-10-03, Korean domain router), and the 3-arm extension (item 7, 2026-10-08) brought per-task fine-tuning formally into scope. The upstream fine-tuning script is still not modified; changes are made only in a copy (`poc/finetune/laya_finetune_mps_patched.py`).
- Other hardware. Measurements run on this Mac (Apple M4 Pro, 48GB) with CPU fp32 and MPS. If a CUDA server becomes available, the scope is extended by adding columns to Track D.
- Modifying upstream code. The scripts we need are written as our own in `scripts/`, and upstream is kept read-only in `third_party/laya` (not included in the public repository; recreate it by cloning https://github.com/NandhaKishorM/laya at commit 4aa6761).

## 2. Document map

| File | Role | When to read | Outputs |
|---|---|---|---|
| `00_README.md` | Entry point. Execution order, assumptions, Go/No-Go, terminology | First, and at each Phase transition | Decision-matrix check |
| `01_laya_analysis.md` | Analysis of Laya's architecture, API, published figures and Honest limits; hypotheses H1\~H10 | Once before Phase 0. When the interpretation of a figure is unclear | Benchmark hypotheses |
| `02_environment_setup.md` | uv + Python 3.12 environment, checkpoint download, revision pin, symlinks, smoke test | Phase 0 | `.venv/`, `third_party/laya`, `models/` (these three are not included in the public repository), smoke-test pass log |
| `03_benchmark_plan.md` | Definitions of Track A\~F, protocol, metrics, run commands, pass criteria | Phase 2 | `results/<track>/*.json, *.md`, `results/dashboard/index.html` |
| `04_korean_evalset_spec.md` | Korean evaluation sets: sources, conversion rules, label policy, file names | Phase 1 | `data/evals/ko_*.jsonl` + sha256 |
| `05_poc_plan.md` | PoC scenarios A/B/C, stages P0\~P4, success criteria | Phase 3 | `poc/` service + Laya Playground demo UI (`/poc/ui/`, jevplayground layout), load measurement, threshold policy |
| `06_templates.md` | Templates for the experiment record, the results report and the Go/No-Go report | At every measurement; Phase 4 | Filled-in reports |
| `07_korean_support_audit.md` | Korean-support audit results (documentation, tokenizer, routing, measurements) and design implications | Before choosing the scenario; when designing schemas and routing | `results/korean_support/` |
| `09_laya_vs_jev_plan.md` | Laya vs Jev small-sample comparison plan and per-session results (via the public playground, tasks T1\~T8, operating rules, metrics, session order, §10 conclusion). Done; results in `results/F/jev_cmp/summary.md` | When interpreting or reproducing the Jev comparison results | `data/evals/jev_cmp/`, `results/F/jev_cmp/`, paper v2 |
| `11_three_arm_plan.md` | 3-arm extension plan: Jev vs vanilla Laya vs trained Laya, categories in Laya's training mix (T2, T5, T9, T10) and outside it (T1, T3, T4, T6, T7, T8), training-data composition, training checks V1-V6, statistics, execution order and budget. No Jev rerun | When preparing trained-Laya training and evaluation, or interpreting the 3-arm results | `data/evals/jev_cmp_ext/`, `poc/finetune/ckpt_t3arm/` (not included in the public repository), `results/T3arm/`, paper v3 |

## 3. Execution order

| Phase | Document | Inputs | Outputs | Verification criteria | Expected duration |
|---|---|---|---|---|---|
| 0 Environment | 02 | This Mac, network | `.venv` (py3.12, laya 0.3.23), `third_party/laya@4aa6761`, 3 `models/` symlinks | `import laya` version 0.3.23, `laya-evals validate` fixture exit 0, `route()` of a Korean sentence gives `multilingual`, 1 successful predict each on CPU and MPS | Half a day (including the 2.37GB checkpoint download) |
| 1 Datasets | 04 | Public HF/GitHub data (manual labels optional) | 14 kinds of `data/evals/*.jsonl` (04 §4 table, including the PoC main-task pair `ko_massive_domain_8` + `en_massive_domain_8`) + MANIFEST.json, sha256 list | Every file passes `laya-evals validate`, class distribution and majority recorded, label policy frozen before any model run | 1\~2 days (including ≥200 manual labels) |
| 2 Benchmark | 03 | Outputs of Phase 0, 1 | `results/<track>/` reports, per-Track summary md | Track A passes (dependency below); each Track meets its pass criteria or the reason for failure is recorded | 2\~3 days |
| 3 PoC | 05 | Phase 2 results, confirmed scenario | `poc/` service, demo UI (`/poc/ui/`), load measurement, refit temperature, threshold-policy document | Each stage P0\~P3 passes verification; Go/No-Go matrix inputs filled in. P2 done 2026-10-03: ft-v1 service + Laya Playground acceptance check 11/11 ✔ (`results/poc/P2_20261003.md`), `/poc/decide` round trip p95 21.1 ms | 3\~5 days (P4 measured: training on 11,094 rows × 3 epochs 35.8 min + evaluation 10 min, with the GPU idle) |
| 4 Report | 06 | Phase 2, 3 results | Final report `results/REPORT.md` (written 2026-10-03), dashboard (`results/dashboard/index.html`), Go/No-Go decision (`results/go_no_go.json`) | Measured value, verdict and rationale entered for every matrix item | 1 day (actual: Track D 1.3 h + half a day for the report) |

The Track execution order is A → D → B → C → E → F. A goes first to validate the measurement pipeline, and D comes early because it is the cheapest and lets us predict the run time of the later Tracks.

**Dependency**: in Track A, the multilingual accuracy of `ko_massive_intent_20opt.jsonl` run on CPU fp32 must fall within ±0.03 of the upstream published figure 0.470 (source: BENCHMARKS.md §Languages, `ko` row). If it does not, the problem lies in the data conversion (option sampling seed 13, first 100 test rows) or the environment (dtype, revision), and Track B/C/E results obtained before this is resolved are not trusted.

## 4. Directory layout

```text
benchmarkforLaya/
├── docs/                 # this document set (00~06)
├── third_party/laya/     # upstream clone @ 4aa6761, read-only. research/scripts, examples, verify are used
│   └── models -> ../../models   # path where examples/_common.py looks for local checkpoints
├── models/               # symlinks to the HF snapshots: laya/, laya-multilingual/, laya-typed-decisions/ (LAYA_MODELS_DIR=$PWD/models; set LAYA_MODELS="$LAYA_MODELS_DIR" inline when running research scripts)
├── data/
│   ├── raw/              # original data (HF datasets cache or GitHub raw downloads)
│   ├── handwritten/      # handwritten sources (negation pairs, PoC labels, label policy)
│   └── evals/            # laya-evals JSONL (ko_*.jsonl) + MANIFEST.json(sha256)
├── scripts/              # our scripts: data conversion, probes, latency, load, plots
├── results/
│   ├── <track>/          # <YYYYMMDD-HHMM>_<model>_<dataset>.json / .md (including laya-evals --json/--markdown output)
│   ├── dashboard/        # HTML produced by build_dashboard.py (index.html)
│   └── verdicts.json / go_no_go.json  # manual records of hypothesis verdicts and Go/No-Go (06 §2)
├── poc/                  # PoC service code, configuration, load tests
│   └── service/ui/       # Laya Playground demo UI (index.html, examples.json, served at /poc/ui/)
├── .venv/                # uv venv (Python 3.12)
└── env.sh                # environment variables (02 §2.8)
```

In `.gitignore` (not included in the public repository): `models/`, `third_party/`, `data/raw/`, `.venv/`, `.env`. Whether `results/**/*.json` is committed is decided by size, but `.md` summaries are always committed. `git init` is an optional step of Phase 0 (`02_environment_setup.md`).

## 5. Key assumptions and items to be verified

Each item means "proceed with the default". To go another way, change it before the corresponding Phase starts.

1. **PoC scenario**: **Decided (2026-10-02): C, topic/domain router.** Main task MASSIVE ko 8 domains (`ko_massive_domain_8`; the Korean penalty is measured with the English pair of the same ids), auxiliary KLUE YNAT 7 topics (`ko_klue_ynat_7`). A (CS triage + gateway) failed G1 zero-shot (P0/P0b) and is held back as a P4 fine-tuning candidate; B is excluded because upstream's held-out guardrails score 0.708\~0.762 and moderation 0.530 (source: BENCHMARKS.md §Themes). Rationale and taxonomy: `05_poc_plan.md` §2, §4.
2. **LLM baseline**: whether to use `claude-haiku-4-5-20251001` zero-shot classification as a Track F baseline, and whether an API key is available. **Default: optional. Without a key, proceed with majority/random and the published figures only**, and judge Go/No-Go G1 on the absolute value (≥ 0.80).
3. **Hardware scope**: this Mac only vs adding a CUDA server. **Default: Mac only.** If CUDA is available, columns are added to Track D, and the TileLang fast path and `compile=True` also come into the measurement scope.
4. **Korean labeling resources**: with C chosen, the G1 verdict needs no manual labels (public MASSIVE and KLUE labels). The only candidate for review is an optional set of 100 "real queries" for the confirmed taxonomy (05 §Open questions, item 3); labeling ≥200 items of `ko_poc_triage_v1.jsonl` is needed again only if A is revived in P4 (default then: labels by 1 person + label policy frozen in advance; record Cohen's kappa if cross-labeling by 2 people is possible).
5. **Jev access**: whether a TypeSafe Jev API key is available. **Decision (2026-10-06): no key. Replaced by citing published figures + a manual small sample on the public playground (n=24)** (`results/F/jev_playground_manual_20261006.md`). A formal paired comparison would follow once an API key is obtained.
6. **Publication scope of results**: whether to contribute the Korean results upstream as an issue/PR (as with the zh community bench). **Default: internal report. Contribution is decided separately after Phase 4.** If contribution is in view, data licenses (CC BY 4.0 etc.) and preservation of raw predictions must be observed from Phase 1. **Owner decision (2026-10-12): public release as a GitHub repository.** Data are published with a per-source license table (`DATA_LICENSES.md`), except the AG News-derived files. The Jev raw records and playground captures, the PDFs and the checkpoints are not published.
7. **Time budget**: Phase 0\~4 in total about 8\~12 business days (excluding P4 fine-tuning). **Default: P4 is not done within this budget.**
8. **Applying the Korean-support verdict (decided, 2026-10-02)**: the Korean channel sets `lang="ko"` explicitly, applies NFC normalization before inference, and picks the noul decision threshold per question on a dev set instead of fixing it at 0.5. Rationale and details: `07_korean_support_audit.md` §6. This item was settled by evidence, not an open question.

## 6. Go/No-Go decision matrix

All thresholds are **proposed values** and need confirmation by the project owner. Measured values and verdicts are recorded in the Go/No-Go report of `06_templates.md`.

| # | Criterion | Measuring Track | Threshold (proposed) | Rationale |
|---|---|---|---|---|
| G0 | Reproduction gate | A | `ko_massive_intent_20opt` multilingual accuracy 0.470 ± 0.03 (CPU fp32) | Upstream published figure (source: BENCHMARKS.md §Languages). B/C/E results are invalid until it passes |
| G1 | PoC task accuracy | PoC P1 (Track B, `ko_massive_domain_8` test half; `ko_klue_ynat_7` auxiliary) | Within -5pt of the LLM zero-shot baseline. Without an LLM, absolute ≥ 0.80 | Upstream zh community bench: 6-domain voice routing 0.883, CS routing 0.640 (source: BENCHMARKS.md §Community evaluation). The PoC schema has ≤ 8 options (router_v1 has 8), so the head_max_len budget should have no effect |
| G2 | Coverage after gating | E | Coverage ≥ 0.70 at an error rate ≤ 5% with refit temperature + `min_confidence` (depends on G1: at accuracy a the upper bound is a/(1−e)) | Jev 3rd-party published coverage_at_5pct_error AG News 0.830 (source: research/scripts/bench_apps.py `JEV_PUBLISHED`). The principle in docs/staged-adoption.md that "thresholds are a policy chosen on held-out data" |
| G3 | Calibration | E | Held-out ECE ≤ 0.10 after refit | Upstream refit goes 0.466 → 0.081 (laya), 0.314 → 0.106 (multilingual) (source: BENCHMARKS.md §Calibration). multilingual ships without a temperature |
| G4 | Option-order robustness | C | Flip rate per permutation on the PoC schema (mean of 5 permutations) ≤ 0.10; as a secondary measure, flips of the gate-passing decision | Upstream 20-option flip 0.150 / 0.230, Jev 0.13 (source: BENCHMARKS.md §Option-order robustness). Hypothesis that it should be lower with ≤7 options |
| G5 | In-process latency | D | 3-question call p95 ≤ 100 ms (MPS), ≤ 500 ms (CPU 10 threads) | T4 1q 32.8 ms, EPYC 4-core multilingual 1q 193 ms, 5q 912 ms (source: BENCHMARKS.md §Speed, §Server CPU). M4 Pro figures are hypotheses, to be confirmed in Track D |
| G6 | Serving latency | D, PoC P2 | p95 ≤ 150 ms at 10 RPS on `laya-serve` (MPS, preload) | Of GB10's 1q p50 of 100 ms over HTTP, \~93 ms is fixed overhead (source: BENCHMARKS.md §Other hardware). HTTP overhead can dominate, so this is kept separate from G5 |
| G7 | Batch equivalence | D, C | `predict` vs `predict_batch(sort_by_length=True)`: 0 argmax mismatches, max \|Δp\| ≤ 0.01 | Upstream: 0 decision changes over 10,000 cases, numeric difference ≤ 0.0001 (source: research/README.md "Length batching"). ONNX: 0 decision changes over 80 cases (source: README.md "Batch Mode") |

Decision rule (proposed): if G0 does not pass, the verdict is deferred. If any of G1·G2·G5 falls short: No-Go, or "re-evaluate after fine-tuning (P4)". A shortfall in G3·G4·G6·G7 is treated as a conditional Go (with added operational guards).

**Current verdict (final, 2026-10-03).** Zero-shot router_v1 + multilingual (2026-10-02): G0 pass (Δ0) · G1 fail 0.492 · G2 fail 0.224 · G3 borderline pass 0.098 · G4 fail 0.270 → **zero-shot is No-Go**. Fine-tuned ft-v1 (run `full_20261003-1156`, 35.8 min of training, MASSIVE ko train 11,094 rows): G0 pass · G1 **pass** 0.900 (0.893 excluding duplicates, 0.913 on the full test set of 2,917 rows) · G2 **pass** coverage 0.923 (error 0.042) with the dev T applied on 2,917 rows, 0.756 with a post-hoc T on the 250-row test half · G3 **pass** 0.053 · G4 **pass** 0.037 · G5 **pass** 3-question p95 MPS 22.6 / CPU 57.8 ms · G6 **pass** laya-serve 10 RPS 3-question p95 79.4 ms · G7 **pass** predict vs predict_batch(sort) flip 0, max \|Δp\| 0.0001 → **G0\~G7 all pass, Conditional Go (premised on the fine-tuning pipeline)**. Evidence: `results/go_no_go.json`, `results/REPORT.md`.

**Current conclusion (Laya vs Jev, 2026-10-07).** Zero-shot, Jev is more accurate than Laya (of 8 tasks, Laya significantly better on 0, Jev significantly better on 2 after Holm correction), with the largest gaps on instruction-style and multilingual tasks. Laya is competitive in local execution, latency and cost, and in that fine-tuning can close the gap. This conclusion does not change the G0\~G7 verdicts above (which are for the Korean routing PoC). Evidence: `results/F/jev_cmp/summary.md`, `results/REPORT.md` §0a.

## 7. Glossary

| Term | Meaning |
|---|---|
| System 1 decision engine | A model that produces a probability distribution over typed decisions in a single forward pass without generating text. With no free generation, there is no parsing and no hallucination |
| non-autoregressive | Does not generate tokens sequentially. Latency is not proportional to output length and depends only on input length and the number of questions |
| state | The input to be judged. `str`, `dict` and `list` (conversation turns) are all accepted; a dict is rendered as JSON |
| question / instructions / criteria | One question = `type` + `instructions` (the prompt sentence) + `criteria` (for choice, label→description; for score, a list of level descriptions; for noul, optional true/false descriptions) |
| choice | Picks one label from a closed label set. Returns `choice` and `probabilities` |
| score | Ordinal levels. Returns the expected value (`score`) on a 0-based level-index scale; `legend` maps index→description |
| noul | The probability P(true) that a statement holds. The `noul` field is that probability |
| Router | Entry point that picks the checkpoint by script and language detection. Hangul always goes to multilingual |
| checkpoint english / multilingual / typed-decisions | Respectively: ModernBERT-large English, mmBERT-base for 100+ languages, an English typed-decisions fine-tune |
| max_len / head_max_len | Token budget of the whole sequence / upper limit for the question+options head. Room left for the state = `max_len - head_len - 1` |
| RLCD | RL training that uses a strictly proper scoring rule as the reward. Pushes the probabilities toward calibration |
| temperature / ECE | Scalar that divides the logits (per bucket, clamped to [0.5, 5.0]) / Expected Calibration Error, lower is better; laya-evals uses 15 bins |
| confidence vs answer_confidence | The former is 1 - normalized entropy (sensitive to the number of options); the latter is the probability of the reported answer, max p (the target of calibration). Gating uses the latter |
| min_confidence / abstention | When a threshold is given at call time, answers whose `answer_confidence` falls short are marked with `low_confidence` and `abstention` (passed / abstained / unevaluated) |
| predict_batch / sort_by_length | Batches several states into one forward pass for the same question set / puts states of similar length into the same pass to reduce padding waste |
| predict_long | Scans a state longer than `max_len` with overlapping windows and aggregates per question (noul takes the max, choice/score the window with the highest confidence) |
| laya-evals run identity | `dataset_sha256`, `questions_sha256`, `revisions`, `laya_version` in the report's `config`. The keys that decide whether a run is comparable with a baseline |
| Jev | TypeSafe's hosted decision API. `laya-serve` provides the same `POST /v1/systemone` protocol. Only 3rd-party published figures exist |

## Open questions / assumptions

- Items 1\~7 of §5 are all open questions, and work proceeds on their defaults. In particular, item 1 (scenario) and item 2 (whether there is an LLM baseline) change how G1 is judged.
- The latency thresholds of G5·G6 are hypotheses extrapolated from the upstream T4/EPYC figures. After the first Track D measurement, readjust them to realistic values, and record in the `06_templates.md` report that they were readjusted and why.
- Of the Korean public datasets, NSMC and 3i4K no longer open with the HF `datasets` script loader, so the GitHub raw files are used. Licenses are checked in `04_korean_evalset_spec.md`.
- The quality of the manual label set (≥200 items) sets the upper bound of the G1 verdict. If labeled by 1 person, state the label noise in the report.
- The multilingual column of the upstream 51-language table holds "refreshed" rerun values (the committed file does not reproduce; source: BENCHMARKS.md intro, #208). The ko 0.470 we compare against is also a refreshed value.

**English** | [한국어](00_README.ko.md)
