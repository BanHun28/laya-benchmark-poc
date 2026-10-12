# A Controlled Comparison of Laya and Jev: Zero-shot Accuracy, Calibration, Multilingual Consistency, and Latency of a Non-autoregressive Decision Engine

**Written** 2026-10-07 · **Environment** Apple M4 Pro (10P+4E CPU, 20-core GPU/MPS, 48 GB), macOS 26.6.2, Python 3.12.12, torch 2.14.1, transformers 5.18.0 (`results/env/env_20261002-1333.json`) · **Laya** 0.3.23 (upstream commit 4aa6761), checkpoint bundle `convaiinnovations/laya` @ 55cf4c4, quality measured on CPU fp32 · **Jev** via the independent third-party public playground jevplayground.com (2026-10-06\~07), Model ID `typesafe-ai/jev` (version not shown) · **Evidence files** `results/F/jev_cmp/summary.md`, `summary.json` (S6 synthesis, 0 numeric mismatches against the session summaries, `results/F/jev_cmp/S6_20261007.md:45`)

## Abstract

Laya is an open-source non-autoregressive decision engine that produces probability distributions over typed decisions (choice, score, noul) in a single encoder forward pass; Jev is a commercial model that offers decisions of the same form through a hosted API. Upstream has compared the two systems only through published figures measured by third parties on different samples. This study runs a controlled comparison that feeds the same state bytes, the same question text, and the same option strings to both systems on 8 tasks (8 public datasets; 5 languages for the multilingual task). Jev was called 438 times through the public playground, and in 411/411 cases the request body was confirmed to be byte-identical to the pre-generated payload. In per-task exact McNemar tests, Jev was significantly ahead on 4 tasks (T1, T4, T5, T7), 4 were not significant, and there was no task on which Laya was significantly ahead. After Holm correction, only T1 and T7 are significant. The 8-task macro accuracy is Jev 0.828, Laya english 0.646, multilingual 0.598, and Router 0.661. In multilingual intent classification, Jev is at 0.900 or above in all 5 languages (best 0.950), and for 18/20 ids all 5 languages received the same label, versus 5/20 or fewer for Laya. Conversely, Laya fine-tuned on training data from the same distribution matched or numerically exceeded Jev on two tasks (the latter not significant). Local Laya's 1-question latency (13.8\~86.6 ms) was shorter than Jev's internet round trip (median browser POST 465 ms), but the deployment forms differ, so this is not a model-speed comparison.

- Accuracy: Jev significantly better 4 / n.s. 4 / Laya significantly better 0 (after Holm correction 2 / 6 / 0). Pooled exact McNemar over the 240 independent single-question items: Jev 194 vs per-task best Laya 176, b/c 39/21, p=0.0273.
- Macro difference: Jev − Router +0.167 [+0.044, +0.293], Jev − per-task best Laya +0.153 [+0.031, +0.281] (task bootstrap, descriptive statistics).
- Multilingual consistency: on T7, the mean language penalty is Jev +0.012, Laya english −0.362, multilingual −0.287.
- Calibration: the meaning of Jev's probabilities differs by question format (single choice: 59% of errors have top ≥ 0.90; multi-question T1: underconfident).
- Fine-tuning reference points: on T1, the Laya typed-decisions checkpoint 104/120 = Jev 104/120; on Korean domain routing, Laya ft-v1 22/24 vs Jev 20/24.

## 1. Introduction

### 1.1 Motivation

The Laya upstream README presents, in its "Laya (with routing) vs Jev" table, typed-decisions 0.766 vs 0.727, AG News 0.950 vs 0.910, DAIR Emotion 0.595 vs 0.480, Banking77 0.425 vs 0.870, and p50 latency 32.8 ms vs 236\~276 ms (`third_party/laya/README.md:1274-1291`; `third_party/laya/` (not included in the public repository) is recreated by cloning https://github.com/NandhaKishorM/laya at commit 4aa6761). However, the same document and BENCHMARKS.md state that the Jev figures are "third-party published, never measured here" and that the samples and prompts differ (`third_party/laya/README.md:1276-1278`, `third_party/laya/BENCHMARKS.md:3`). In other words, no controlled comparison measuring the two systems on the same inputs existed. When the samples, question text, and option rendering differ, an accuracy difference cannot be read as a system difference.

### 1.2 Research questions

- RQ1. How does zero-shot accuracy differ on the same inputs?
- RQ2. Are the two systems' probabilities calibrated, and can confidence decide whether an item is processed automatically?
- RQ3. How stable are the decisions with respect to determinism, option order, and language changes?
- RQ4. How do latency and cost differ structurally?
- RQ5. Is Laya's zero-shot deficit closed by fine-tuning?

### 1.3 Contributions

(1) A controlled Laya vs Jev comparison with matched input bytes over 8 tasks, 8 public datasets, and 5 languages; neither the upstream documents nor the third-party benchmarks they cite contain such a comparison. (2) A reproducible harness: per-task playground form files, pre-click payload hashes and post-click byte comparison of the request bodies, and a master request log of 411 entries. (3) Statistical treatment combining multiple-comparison correction (Holm), task bootstrap, pooled McNemar over independent items, and cluster bootstrap. (4) A confidence analysis per question format and its implications for automation thresholds. (5) Fine-tuning reference points and the Korean domain-routing PoC case. (6) 7 upstream defects and documentation inconsistencies found during the study.

## 2. Background

### 2.1 Laya

Laya evaluates typed questions (`choice`, `score`, `noul`) over a state (text, email, JSON document) in "a single forward pass" (`third_party/laya/README.md:129`). There are three checkpoints: english (ModernBERT-large, 421M, context 512), multilingual (mmBERT-base, 322M, 1,024, up to 8,192), and typed-decisions (ModernBERT-large, fine-tuned on the typed-decisions workflows) (`third_party/laya/README.md:135-137`). The Router picks english or multilingual from the script and language of the input (`third_party/laya/README.md:385`). Questions and options share the head token budget (`head_max_len`, english 192), and the state uses the remaining budget (`third_party/laya/README.md:1390`). A dict state is serialized with `json.dumps(state, ensure_ascii=False)`, so non-Latin characters enter the model as they are (`.venv/lib/python3.12/site-packages/laya/common.py:78`, not included in the public repository). Upstream itself defines the base checkpoints as "a fast base to specialise, not as a zero-shot decision engine" (`third_party/laya/README.md:1530`).

### 2.2 Jev and the playground

Jev is TypeSafe AI's hosted decision model; it takes a state and typed questions and returns decisions with probabilities attached (`docs/09_laya_vs_jev_plan.md:11`). jevplayground.com is an independent third-party UI that calls Jev, and it states that it is not affiliated with TypeSafe AI (`results/F/jev_playground_manual_20261006.md:224`). The site says only "Free to try · Usage limits apply" and does not publish numeric limits (`docs/09_laya_vs_jev_plan.md:48`). The constraints confirmed on the playground are as follows (`results/F/jev_cmp/sessions/S1_20261006/multi_question_mode.md` §1).

- There are Single question and Multiple questions modes; the latter supports 2\~5 questions, mixed types, and a shared state.
- Choice takes 2\~10 options, and label input is truncated at 80 characters without an error.
- Score accepts exactly 5 levels (0\~4) only.
- Boolean has no label or description fields.
- Probabilities are rounded to the second decimal place.
- "View details" shows the Model ID and the input/output token counts, and choice/score questions carry a separate confidence.

The median number of output tokens per request is Boolean 20, score 17, and choice 61\~150, varying with the format and options; this suggests a decoding step in response generation, but it has not been confirmed (`results/F/jev_cmp/summary.md` §7.3, `results/F/jev_playground_manual_20261006.md` §4). The model version, the training data, and whether the server wraps the prompt are unknown.

### 2.3 Existing comparison figures

The Jev figures cited by upstream come from third-party benchmarks (AbdelStark/jev-benchmarks, nibzard/decision-model-benchmark) (`third_party/laya/README.md:1268-1272`). The Jev column of the comparison table is labeled Jev 1.13.0 (`third_party/laya/README.md:1281`). On typed-decisions (400 cases, 2,000 decisions), Jev 1.13.0 is cited at accuracy 0.727, soft 0.580, Brier 0.148, ECE 0.144, and score MAE 0.391 (`third_party/laya/README.md:1304-1313`). Calibration is presented as ECE Jev 0.246 vs Laya 0.081, where the Laya value is after per-domain temperature fitting (`third_party/laya/README.md:1287`, `:1300`). The option-order flip of Jev is reported as 0.13 (`third_party/laya/BENCHMARKS.md:213`). Because these figures come from samples different from this study's, they are used only as context.

## 3. Methods

### 3.1 Tasks and data

Samples were drawn deterministically from public splits with seed 13. Single-question tasks were stratified by label after applying the deduplication and length rules, T1 was stratified by workflow, and T7 uses the first 20 test ids present in all 5 languages, with 9 wrong options drawn by seed (`data/evals/jev_cmp/MANIFEST.json`, `scripts/build_jev_cmp_sets.py`).

| Task | Source @revision | split | n | Format / options | Laya training mix |
|---|---|---|---|---|---|
| T1 typed-decisions | `LocalLLaMA/typed-decisions` all @d0e2f0c | test | 40 cases, 120 comparable decisions | Multiple questions: choice 50, Boolean 60, 5-level score 10 | no |
| T2 AG News | `fancyzhx/ag_news` @eb185aa | test | 40 | choice 4 | yes |
| T3 DAIR Emotion | `dair-ai/emotion` split @cab853a | test | 40 | choice 6 | no |
| T4 Banking77-10 | `mteb/banking77` @18072d2 | test | 40 | choice 10 (gold + 9 wrong options, key-only rendering) | held out |
| T5 BoolQ | `google/boolq` @35b264d | validation | 40 | Boolean | yes |
| T6 SST-5 | `SetFit/sst5` @e51bdcd | test | 40 | score, 5 levels | no |
| T7 MASSIVE intent-10 | `mteb/amazon_massive_intent` en·de·ja·zh-CN·ko @940fd47 | test | the same 20 ids x 5 languages = 100 | choice 10 (English keys, gold + 9 wrong options, reduced from upstream's 20 options) | held out |
| T8 prompt-injections | `deepset/prompt-injections` @4f61ecb | test | 40 | Boolean | no |

The training mix is MANIFEST's `in_training_mix`. Upstream states that only AG News (T2) and BoolQ (T5) were put in Laya's training mix (so retention, not generalization), that Emotion·prompt-injections·Banking77·SST-5 were held out, and that neither checkpoint was trained on typed-decisions·MASSIVE (`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`, `results/F/jev_cmp/summary.md` §2.1). In the table, both no and held out mean not in the training mix. Jev's training data are unknown, and all sources are public datasets.

### 3.2 Input identity

- **state**: the JSON-serialized string that Laya actually reads (`state_text`) was put verbatim into Jev's State field. The question text is the sentence from the upstream benchmark scripts, and for T1 the dataset's own questions, used verbatim (MANIFEST `question_source`).
- **Options**: for choice, the option strings that Laya actually renders (`key: description` or the key alone, depending on the task) were entered in the same order. Because of the playground's 80-character limit, T4 was rebuilt for both systems with upstream-style key-only rendering (the previous rendering is kept as `_v0`). In T1, 10 decisions with options longer than 80 characters were excluded from the comparison.
- **Score**: since the playground accepts only 5 levels, the 70 4-level score questions of T1 were excluded. As a result, T1 compares 120 of 200 decisions.
- **Boolean**: Jev's Boolean has no description fields. As a fairness check, a Laya variant without the noul true/false descriptions (criteria) was measured separately, and the accuracy change was not significant (english 0.467 → 0.517, p=0.549; `results/F/jev_cmp/laya_summary.md` §2b). The noul questions of T5·T8 have no criteria to begin with.
- **Verification**: before every request, the hash of the payload built from the form file was checked, and after the request the actual body was compared byte by byte (411/411 match). The on-screen display and the response JSON also matched 410/410 (`results/F/jev_cmp/summary.md` §1).

### 3.3 Jev runs

| Session | Date (KST) | Content | Requests | Minimum gap |
|---|---|---|---|---|
| Pilot | 2026-10-06 08:09\~08:33 | Korean domain routing, 24 rows | 25 (1 HTTP 502) | 21.6 s |
| S1 | 2026-10-06 10:04\~10:17 | exploration 1 + T2 40 | 41 | 17.0 s |
| S1b | 2026-10-06 10:29\~10:38 | determinism 10 + option permutation 20 (T2) | 30 | 17.3 s |
| S2 | 2026-10-07 08:49\~09:12 | T1 39 cases + T3 40 | 80 (1 HTTP 502, retry succeeded) | 12.1 s |
| S3 | 2026-10-07 13:36\~13:56 | T4 40 + T5 40 | 80 | 15.0 s |
| S4 | 2026-10-07 14:16\~14:36 | T6 40 + T7 en·de 40 | 80 | 15.0 s |
| S5 | 2026-10-07 14:53\~15:18 | T7 ja·zh-CN·ko 60 + T8 40 | 100 | 15.0 s |

With 2 site status checks added, the total is 438 requests (`results/F/jev_cmp/summary.md` §1). The operating rules were a click gap of at least 10 seconds, 1 retry after 60 seconds on 5xx, and an immediate stop on 429, a limit message, or a captcha. At first we imposed our own cap on the number of requests per day. Because the site publishes no numeric limit and there were 0 occurrences of 429 or limit messages in the 178 requests before the cap was lifted, the cap was lifted by owner decision on 2026-10-07, while the gap and stop rules were kept. After the cap was lifted, no 429, limit message, or captcha appeared in the 340 requests of that day, including the 260 of S3\~S5 (`docs/09_laya_vs_jev_plan.md:48`). Row 30 of T1 reused the S1 exploration request, whose payload was identical to the main run.

### 3.4 Laya measurement

Laya was measured with all three runners, english, multilingual, and Router, on the same set files (laya-evals JSONL) from which the Jev forms were built, on CPU fp32 (intra-op 10, inter-op 1) with batch 8 (`results/F/jev_cmp/run_laya.sh`, `results/F/jev_cmp/S0_20261006.md`). For T1, the upstream fine-tuned checkpoint typed-decisions was added as a reference point. A rerun of T1 english gave identical answers 200/200, confirming determinism (`results/F/jev_cmp/laya_summary.md` §5).

### 3.5 Statistics

Accuracy intervals are Wilson 95%, and two systems on the same items are compared with the exact McNemar test (two-sided). b is the number of items only Jev gets right, and c the number only Laya gets right. For each task, the Laya compared with Jev is the most accurate of the three runners; this is a post hoc choice made after seeing the results and favors Laya. Holm correction was applied to the 8 task-level tests. The difference in task macro means was examined with a paired bootstrap (10,000 resamples) that resamples the 8 tasks with replacement; separately, the independent single-question items (T2·T3·T4·T5·T6·T8, 240 items) were examined with a pooled exact McNemar test, and the clustered T1 (40 cases) and T7 (20 ids) with a cluster bootstrap. We also report AUROC for Boolean (2,000 item resamples), Brier and ECE for calibration (15 bins, on the top probability), and the MAE of E[level] for score (`results/F/jev_cmp/summary.md` §2, §4).

### 3.6 Summary of threats

The playground is not an API, and the model version is not shown. With n=40 per task, the Wilson half-width is about ±0.15. The T1 gold label is the argmax of the dataset's teacher distribution, and the identity of the teacher could not be confirmed. Details are in §6.4.

## 4. Results

### 4.1 Accuracy (RQ1)

| Task | Jev | Laya english | Laya multilingual | Laya Router | Jev vs best Laya: b/c, p (Holm p) | Verdict (after Holm) |
|---|---|---|---|---|---|---|
| T1 typed-decisions (120) | 104/120 = 0.867 [0.794, 0.916] | 0.383 | 0.367 | 0.383 | english 66/8, 1.8e-12 (1.4e-11) | Jev better (Jev better) |
| T2 AG News (40) | 35/40 = 0.875 [0.739, 0.945] | 0.975 | 0.925 | 0.975 | english 0/4, 0.1250 (0.3750) | n.s. (n.s.) |
| T3 DAIR Emotion (40) | 28/40 = 0.700 [0.546, 0.819] | 0.750 | 0.625 | 0.750 | english 2/4, 0.6875 (1.0000) | n.s. (n.s.) |
| T4 Banking77-10 (40) | 37/40 = 0.925 [0.801, 0.974] | 0.725 | 0.750 | 0.725 | multilingual 8/1, 0.0391 (0.1953) | Jev better (n.s.) |
| T5 BoolQ (40) | 37/40 = 0.925 [0.801, 0.974] | 0.725 | 0.600 | 0.725 | english 9/1, 0.0215 (0.1289) | Jev better (n.s.) |
| T6 SST-5 (40) | 26/40 = 0.650 [0.495, 0.779] | 0.425 | 0.325 | 0.425 | english 15/6, 0.0784 (0.3134) | n.s. (n.s.) |
| T7 MASSIVE-10 (100) | 91/100 = 0.910 [0.838, 0.952] | 0.410 | 0.620 | 0.580 | multilingual 36/7, 9.0e-06 (6.3e-05) | Jev better (Jev better) |
| T8 prompt-injections (40) | 31/40 = 0.775 [0.625, 0.877] | 0.775 | 0.575 | 0.725 | english 5/5, 1.0000 (1.0000) | n.s. (n.s.) |

Source: `results/F/jev_cmp/summary.md` §2.1. For T1 and T7, the item-level intervals and p-values are optimistic because of clustering (see the cluster bootstrap in §4.2).

![Accuracy by task: Jev vs Laya english vs Laya multilingual, Wilson 95% intervals](../results/F/jev_cmp/figs/accuracy_by_task.png)

**Figure 1.** Accuracy by task (bars) with Wilson 95% intervals (thin lines). The annotations on the right are exact McNemar verdicts against the best zero-shot Laya runner; Router appears only in the table (`results/F/jev_cmp/figs/accuracy_by_task.png`).

By task, the results are as follows.

- **T1**: by type, Jev scores choice 42/50, noul 56/60, and score 6/10, and Laya english 14/50, 28/60, and 4/10. Against english, the choice and noul differences are both significant at b/c 31/3 (p=7.7e-07), while the 10 score questions are indistinguishable at b/c 4/2 (p=0.6875). With the descriptions removed from the same inputs, Laya's noul shows the same gap: english 31/60 (b/c 27/2), multilingual 25/60 (b/c 34/3). The per-question majority baseline on these 120 decisions is 0.575, and all three Laya base runners fall below it (`results/F/jev_cmp/summary.md` §2.2).
- **T5·T8 (Boolean)**: on T5, AUROC is Jev 0.988 [0.955, 1.000] and Laya english 0.810 [0.662, 0.942], a difference of +0.177 [+0.043, +0.326]. Jev and the three Laya runners predict true 18\~21 times, close to the 20 gold trues, so the gap appears to be a difference in discriminative power rather than in threshold placement. On T8 the accuracy at the 0.5 threshold is the same (0.775), but Jev separates these 40 rows perfectly (AUROC 1.000, degenerate interval) and all 9 of its errors are misses (false negatives). Laya english AUROC is 0.929 [0.840, 0.997] (`results/F/jev_cmp/summary.md` §2.3).
- **T6 (score)**: the primary metric, argmax level accuracy, is 0.650 vs 0.425, not significant (p=0.0784), but rounded E[level] accuracy gives b/c 15/4, p=0.0192, and MAE is 0.432 vs 0.888, a difference of −0.456 [−0.711, −0.207]. Laya english never chose level 4, and multilingual output level 0·1 on all 40 rows. Scale compression is Laya's main failure (`results/F/jev_cmp/summary.md` §2.4).

### 4.2 Aggregate (RQ1)

| Criterion | Jev significantly better | Not significant | Laya significantly better |
|---|---|---|---|
| exact McNemar, uncorrected α 0.05 | 4 (T1, T4, T5, T7) | 4 (T2, T3, T6, T8) | 0 |
| Holm correction (8 tests) | 2 (T1, T7) | 6 | 0 |

| Compared system | Macro accuracy | Jev − system [task bootstrap 95%] | Macro over the 7 tasks excluding T1 |
|---|---|---|---|
| Jev | 0.828 | - | 0.823 |
| Laya english | 0.646 | +0.182 [+0.041, +0.325] | 0.684 |
| Laya multilingual | 0.598 | +0.230 [+0.121, +0.339] | 0.631 |
| Laya Router | 0.661 | +0.167 [+0.044, +0.293] | 0.701 |
| Per-task best Laya (post hoc) | 0.675 | +0.153 [+0.031, +0.281] | 0.717 |

| Pooled over 240 independent single-question items | Jev correct | Laya correct | b / c | exact p |
|---|---|---|---|---|
| Per-task best Laya | 194 | 176 | 39 / 21 | 0.0273 |
| english fixed | 194 | 175 | 40 / 21 | 0.0204 |
| multilingual fixed | 194 | 152 | 58 / 16 | 9.7e-07 |
| Router fixed | 194 | 173 | 42 / 21 | 0.0111 |

In the cluster bootstrap (10,000 resamples), Jev − Laya is T1 english +0.483 [+0.371, +0.597], T7 multilingual +0.290 [+0.100, +0.470], and T7 english +0.500 [+0.370, +0.640]; no interval includes 0 (`results/F/jev_cmp/summary.md` §4). The macro difference is a descriptive statistic averaging 8 heterogeneous tasks, and Jev leads even without T1.

### 4.3 Calibration and confidence (RQ2)

| Task | Jev Brier / ECE | Best Laya Brier / ECE | Jev mean top − accuracy | Laya mean top − accuracy |
|---|---|---|---|---|
| T1 | 0.237 / 0.181 | 0.724 / 0.205 | −0.134 | +0.152 |
| T2 | 0.220 / 0.118 | 0.053 / 0.083 | +0.102 | −0.045 |
| T3 | 0.537 / 0.278 | 0.429 / 0.174 | +0.201 | +0.150 |
| T4 | 0.114 / 0.069 | 0.478 / 0.262 | +0.048 | +0.082 |
| T5 | 0.098 / 0.103 | 0.393 / 0.190 | −0.012 | +0.172 |
| T6 | 0.502 / 0.184 | 0.770 / 0.239 | +0.101 | +0.229 |
| T7 | 0.140 / 0.068 | 0.584 / 0.216 | +0.037 | +0.212 |
| T8 | 0.307 / 0.194 | 0.401 / 0.223 | +0.146 | +0.187 |

Because Jev's probabilities are rounded to the second decimal place, Brier·ECE carry a floor error of about ±0.005 (`results/F/jev_cmp/summary.md` §5.1). The character of Jev's confidence differed by question format.

| Jev format | Tasks | n | Accuracy | Mean top | Shown as 100% | Errors with top ≥ 0.90 |
|---|---|---|---|---|---|---|
| Single choice | T2·T3·T4·T7 | 220 | 0.868 | 0.949 | 144 (65%) | 17/29 (59%) |
| Single Boolean | T5·T8 | 80 | 0.850 | 0.917 | 0 (0%) | 2/12 (17%) |
| Single score | T6 | 40 | 0.650 | 0.751 | 0 (0%) | 0/14 (0%) |
| Multiple questions | T1 | 120 | 0.867 | 0.733 | 9 (8%) | 1/16 (6%) |

In single choice, 100% displays are common and most errors are at 0.90 or above, so a top-probability threshold can hardly filter out the errors. On T3, 7/40 rows showed the gold option as 0%. Boolean has no 100% displays, but the right threshold position differs by task. On T5, 0.5 is nearly optimal, while on T8 every gold-false item has p(true) of 0.04 or less, so on the same 40 rows a threshold above 0.04 and at most 0.08 gives 40/40 (descriptive statistics). In the multi-question T1, Jev is underconfident, and a low top probability signals an error. The best Laya runner, grouped by format, is overconfident in every format (single choice +0.130, Boolean +0.180, score +0.229, T1 +0.152; `results/F/jev_cmp/summary.md` §5.2\~§5.3). In conclusion, for both systems the thresholds of confidence-based automation must be refitted on held-out data per task (format, number of options, language).

### 4.4 Robustness (RQ3)

- **Determinism**: when 10 rows of T2 were resent with the same payloads 16\~23 minutes later, Jev returned the same labels 10/10, the same probability vectors 9/10 (max |Δp| 0.01), and the same token counts 10/10. Laya english gave exactly the same answers when the 200 T1 decisions were rerun.
- **Option order**: when 20 rows of T2 were shuffled with 1 permutation, the same as in the Laya probe, the flip rate was Jev 0/20 [0.000, 0.161] and 0/20 for both Laya english and multilingual. Since these are mostly high-confidence 4-option rows, the information content is low, and the third-party published Jev flip of 0.13 cannot be ruled out either (the probability of observing 0/20 at that value is 0.062; `results/F/jev_cmp/summary.md` §6).
- **Cross-language consistency (T7)**: the options were fixed to 10 English keys, and only the utterance was varied across 5 languages.

| system | en | de | ja | zh-CN | ko | Same label in all 5 languages | Mean pairwise-language agreement | Mean language penalty |
|---|---|---|---|---|---|---|---|---|
| Jev | 0.900 | 0.900 | 0.950 | 0.900 | 0.900 | 18/20 | 0.935 | +0.012 |
| Laya english | 0.700 | 0.350 | 0.450 | 0.450 | 0.100 | 0/20 | 0.325 | −0.362 |
| Laya multilingual | 0.850 | 0.400 | 0.800 | 0.600 | 0.450 | 5/20 | 0.545 | −0.287 |
| Laya Router | 0.700 | 0.350 | 0.800 | 0.600 | 0.450 | 4/20 | 0.485 | −0.150 |

With n=20 per language, the per-language magnitudes are directional signals. The 2 ids for which Jev changed its label across languages are cases where the content of the translated sentences differed between languages (`results/F/jev_cmp/summary.md` §6.1).

![T7 accuracy by language](../results/F/jev_cmp/figs/t7_languages.png)

**Figure 2.** Accuracy by language on T7 MASSIVE intent-10 with Wilson 95% intervals (the same 20 ids, 10 options with English keys). The annotations on the right are per-language exact McNemar tests (`results/F/jev_cmp/figs/t7_languages.png`).

### 4.5 Latency and cost (RQ4)

The two values come from different deployment forms. Jev is an internet round trip from the browser through the playground server to Jev, whereas Laya is an in-process call or localhost HTTP within the same M4 Pro. The differences below are not a model-speed comparison.

| Path | Condition | 1-question median | Source |
|---|---|---|---|
| Jev displayed value "server + network" | all 410 requests | 226 ms (p5 184, p95 325.6) | `results/F/jev_cmp/summary.md` §7.1 |
| Jev browser POST round trip | all 410 requests | 465 ms (p5 414, p95 616.2) | same |
| Laya in-process back-to-back (multilingual) | MPS / CPU 10 threads | 13.8 / 37.7 ms | `results/D/D_summary_20261003.md:42`, `:36` |
| Laya in-process back-to-back (english) | MPS / CPU 10 threads | 31.8 / 86.6 ms | `results/D/D_summary_20261003.md:40`, `:34` |
| Laya in-process intermittent calls at 1 s intervals (multilingual) | MPS / CPU | 49.2 / 76.2 ms | `results/D/D_summary_20261003.md:89`, `:87` |
| Laya laya-serve HTTP back-to-back (multilingual) | MPS / CPU | 20.3 / 50.7 ms | `results/D/D_summary_20261003.md:203`, `:222` |
| Laya PoC `/poc/decide` HTTP (ft-v1) | MPS, p50 | 20.1 ms | `results/poc/P2_20261003.md:67` |

Jev's displayed median of 226 ms is slightly below the third-party published p50 of 236\~276 ms (`third_party/laya/README.md:1288`), and the displayed value excludes the leg between the browser and the playground (median about 232 ms). Jev requests were at least 12.1 s apart (per-session median 15.1 s or more), so the matching condition on the Laya side is intermittent calls (multilingual MPS 49.2 ms, CPU 76.2 ms).

![Latency by deployment form, log axis](../results/F/jev_cmp/figs/latency.png)

**Figure 3.** 1-question latency by deployment form (log axis). Dots are medians, thin lines the p5\~p95 of the Jev requests, and the gray band the third-party published Jev p50 range (`results/F/jev_cmp/figs/latency.png`).

Cost was computed from the token records. The 490 decisions total 193,982 input and 36,012 output tokens, an average of 469.4 tokens per decision. Applying the unit price of $0.042 / 1M tokens cited in the upstream README (`third_party/laya/README.md:1291`, a third-party citation, **unit price to be verified**) gives about $0.0197 per 1,000 decisions (formula: total tokens ÷ number of decisions x 1,000 x $0.042 ÷ 1,000,000). By task, this ranges from T1 $0.0131 (multi-question requests share the state tokens) to T7 $0.0292. Laya's marginal cost is local computation with no token billing; the 1-question throughput of a single-process laya-serve is MPS 48.4 RPS and CPU 19.65 RPS, i.e., about 20.7 s and 50.9 s of machine time per 1,000 decisions, respectively (`results/F/jev_cmp/summary.md` §7.3). Power and equipment depreciation were not measured.

### 4.6 Fine-tuning reference points (RQ5)

| Reference point (not zero-shot) | Task·sample | Laya | Jev | Comparison |
|---|---|---|---|---|
| Laya typed-decisions (fine-tuned on typed-decisions train) | T1, the same 120 decisions | 104/120 = 0.867 | 104/120 = 0.867 | b/c 10/10, p=1.0 |
| Laya ft-v1 (Korean domain_8 train, 11,094 rows) | Korean domain-routing pilot, 24 rows | 22/24 = 0.917 [0.742, 0.977] | 20/24 = 0.833 [0.641, 0.933] | b/c 0/2, p=0.5 |
| Laya ft-v1 | ko_massive_domain_8 test half, 250 rows | 0.900 [0.860, 0.936] (zero-shot 0.492) | not measured | - |

Source: `results/F/jev_cmp/summary.md` §3, `results/F/jev_playground_manual_20261006.md`, `results/P4/metrics/full_20261003-1156_summary.md`. Both fine-tuning lines are in-domain results that use training data from the same distribution, so their conditions differ from Jev's, which answers without training data. Training ft-v1 took 3 epochs, 2,150 s (35.8 minutes), on M4 Pro MPS (`results/REPORT.md` §4). The 2 pilot rows on which Jev lost to ft-v1 were due to the MASSIVE convention of grouping game-launch utterances of the `play` scenario under media. This convention is not in the label descriptions, and ft-v1 learned it from the training data (`results/F/jev_playground_manual_20261006.md` §4).

## 5. Case study: Korean domain-routing PoC

Before this comparison, the same project ran a PoC on whether Laya could be adopted as a Korean domain router (`results/REPORT.md`). This case is evidence for RQ5 and a reference from an operational perspective.

- **Zero-shot limit**: on `ko_massive_domain_8`, which groups the MASSIVE ko scenarios into 8 domains, multilingual zero-shot scored 0.492 on the test half. None of the 6 schema-wording variants (all −0.020\~−0.050 vs v1 on dev), temperature calibration, or threshold tuning got past the 0.6 line (`results/REPORT.md` §0, §2).
- **Fine-tuning**: ft-v1, trained on 11,094 rows of MASSIVE ko train (with option-order shuffle augmentation), scored 0.900 on the test half and 0.913 on the full test set of 2,917 rows, with ECE 0.053 and option-order flip 0.037. YNAT dev accuracy held (0.612 to 0.633), showing no forgetting (`results/REPORT.md` §4).
- **Go/No-Go**: of the 8 predefined gates (G0\~G7), zero-shot failed accuracy (G1), coverage (G2), and option order (G4). ft-v1 passed all 8 (G2 conditionally), and the verdict was "Conditional Go, premised on a fine-tuning pipeline" (`results/REPORT.md` §7).
- **Service**: the laya-serve-based router serving ft-v1 and its demo UI passed the acceptance checks 11/11, and the local HTTP round trip of a 1-question decision was p50 20.1 ms, p95 21.1 ms (`results/REPORT.md` §5).
- **Korean support audit**: Korean is one of Laya's evaluation languages (MASSIVE ko intent-20 multilingual 0.470, reproduced with Δ 0.000 against upstream's figure, `results/A/README.md`) and a high-resource language in mmBERT pretraining, but it is not documented in the decision training data. Tokenizer UNK is 0, and Korean takes 1.5 times as many tokens as English. Mixed text with a majority of Latin characters and Korean under 10 syllables are routed to english, so `lang="ko"` must be specified explicitly (`results/REPORT.md` §3, `docs/07_korean_support_audit.md` §1).

In this case, zero-shot Laya trailed Jev (pilot 0.417 vs 0.833, p=0.0020), whereas ft-v1, trained for about 36 minutes, was indistinguishable from Jev while numerically ahead (0.917 vs 0.833, p=0.5000) and kept the latency and cost advantages of local serving.

## 6. Discussion

### 6.1 Where Jev leads

Jev's advantage was large on formats outside the training distribution and on instruction following: typed-decisions (T1), Banking77-10 with key-only labels (T4), BoolQ (T5), and multilingual intent (T7). On the 5-level sentiment scale (T6), the primary metric, argmax accuracy, is not significant, but the interval of the MAE difference excludes 0. Notably, on T5 the ranking quality itself differed even though it is a task in Laya's training mix (AUROC 0.988 vs 0.810). Split by training mix (§3.1), of the 4 significant leads, T1·T4·T7 are data that neither Laya checkpoint was trained on, and T1·T7, which remain after Holm correction, also belong to this group. Among the tasks in the training mix, Jev led only on T5. On T7, Jev made the same decision when the language changed, whereas Laya's decisions split by language even for the same id. The differences can be interpreted as lying in the ability to exploit the meaning of label names, the alignment of multilingual representations, and calibration that uses the whole scale, but since Jev's internals are unknown, the causes are hypotheses.

### 6.2 Where they are similar

AG News (T2) leans toward Laya (b/c 0/4) but is not significant, and it is a task in Laya's training mix. Emotion (T3) is b/c 2/4. prompt-injections (T8) has equal accuracy but a different error structure: Jev missed 5 role- or task-instruction-style injections with p(true) 0.17\~0.40, while Laya english missed 5 explicit ignore/overwrite instructions, 4 of which were German sentences (`results/F/jev_cmp/sessions/S5_20261007/S5_summary.md` §4.3). These three are the only tasks on which Laya is equal or ahead; among them, T2 is in the training mix, and T3·T8 are held out.

### 6.3 Laya's levers

- **Fine-tuning**: both reference points closed the zero-shot gap (§4.6). This is consistent with upstream's own characterization (fast base to specialise).
- **Runner choice**: the difference between english and multilingual is large and changes direction across tasks (T5 0.725 vs 0.600, T7 ja 0.450 vs 0.800). Because the Router chooses by language only, assignments get mixed as on T7 de (multilingual 15, english 5), and accuracy stays at 0.350.
- **Option rendering**: on the same 40 T4 rows, merely changing the option rendering from `key: key spaced` to the key alone moved english from 0.825 to 0.725 (4 rows correct only with the old rendering, 0 rows correct only with the key alone, p=0.1250) and multilingual from 0.575 to 0.750 (0 rows / 7 rows, p=0.0156) (`results/F/jev_cmp/laya_summary.md` §4b). The comparison controlled for this by feeding the same strings to both systems, but in deployment the rendering also needs validation.
- **Operations**: local execution, latency, no token billing, determinism, no external data transfer.

### 6.4 Threats to validity

- **Playground ≠ API**: model version not shown, probabilities rounded to 2 decimal places, possible server-side wrapping, undisclosed definition of the displayed latency.
- **Small samples**: n=40 per task (Wilson half-width about ±0.15), and 20 per language for T7 (half-width about ±0.2). Differences smaller than about 0.2 are mostly indistinguishable.
- **Multiple comparisons**: after Holm correction, only T1·T7 are significant; the uncorrected 4/4/0 is an exploratory summary.
- **Easy samples**: in the seed 13 sample, the interval of T3 Jev 0.700 does not include the third-party published 0.480, and Laya english 0.750 is also higher than upstream's 0.573. The samples are valid for paired comparison, but the results are not generalized to the published figures.
- **T1 teacher**: the gold label is the argmax of the teacher distribution, and the relationship between the teacher and Jev could not be confirmed. Jev's T1 0.867 is higher than the published 0.727 (2,000 decisions, different item composition), so a teacher-alignment effect cannot be ruled out.
- **Joint multi-question evaluation**: on T1, Jev evaluated the 2\~4 questions of a case together in one request, whereas Laya evaluated each question independently.
- **Training contamination**: by upstream's labeling, the only tasks in Laya's training mix are T2·T5, and the remaining six tasks are held out (`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`). This labeling is upstream's self-report, and the training data themselves were not checked. Jev's training data are unknown.
- **Post hoc runner selection**: the per-task best Laya is a choice that favors Laya, and the pooled results with fixed runners point the same way (§4.2).
- **Input representation constraints**: because Boolean has no descriptions, Score takes 5 levels, and choice is limited to 80 characters, T1 compared only 120/200, and T4 was rebuilt with key-only rendering.
- **Pilot protocol differences**: the Korean pilot used the raw utterance as the state, its question text differs slightly from Laya's, and each option's key and description were entered as one string (Laya takes them separately). It was therefore excluded from the 8-task synthesis (`results/F/jev_playground_manual_20261006.md` §1.2, §5).

### 6.5 Upstream defects and inconsistencies found during the study

These are the 7 items recorded in `results/REPORT.md` §8. (1) `laya.calibrate.records_from_labeled` lacks `@torch.no_grad()` and raises an exception on a real Agent. (2) `laya.evals.evaluate` calls `predict(..., model=)` and is incompatible with `Agent.predict`. (3) The output prefix of `hf download` in agent mode breaks the documented download command (`--quiet` needed). (4) The Korean 0.490 on the model card is a value from a different run (T4, n=300); the official table gives 0.470. (5) The README claim that "multilingual noul without criteria reads the state" did not hold in Korean or in its English translation. (6) The license tag of the MASSIVE HF mirror (apache-2.0) differs from the original repository (CC BY 4.0). (7) The 13 s MPS first call in the examples documentation took 0.1 s on this machine.

## 7. Conclusion and future work

Compared on the same inputs, Jev leads in accuracy and multilingual consistency when used right away without training. Jev was significantly ahead on 4 of the 8 tasks (2 after Holm correction) and indistinguishable on the other 4, and there was no task on which Laya was significantly ahead. Laya, on the other hand, reached the same accuracy as Jev (T1) or a numerically higher one (Korean pilot, not significant) when fine-tuned on training data from the same distribution, and with local execution it has structural advantages in latency, cost, and data control. The selection criteria are therefore "Must a broad range of formats be handled immediately, without training data?" (favors Jev) and "Can labeled data be built per task, and do latency, cost, and data boundaries matter?" (favors fine-tuned Laya). Either way, the confidence thresholds must be refitted per task.

Future work is as follows. (1) Re-measurement with the same protocol and larger samples through Jev's official API, and a cost comparison based on a confirmed unit price; which is better on Korean routing, Jev or ft-v1, can be decided only with a paired comparison at the scale of 500 rows (`results/REPORT.md` §8). (2) More languages and task formats (formats not run, such as negation, high cardinality, and long text). (3) Adding an LLM zero-shot baseline. (4) Quantifying how many labels it takes to reach Jev with per-task Laya fine-tuning curves (accuracy vs number of labels). (5) Establishing the identity of the T1 teacher and its relationship with Jev.

## References

1. NandhaKishorM, *laya*: multilingual non-autoregressive System 1 decision engine. GitHub repository, commit 4aa6761 (2026-10-01). Cites README.md and BENCHMARKS.md. [github.com/NandhaKishorM/laya](https://github.com/NandhaKishorM/laya)
2. TypeSafe AI, Jev (hosted decision model). Bibliographic details of the official documentation to be verified. The playground labels it only "TypeSafe Jev" and does not state the version; the Jev figures in the upstream comparison table refer to Jev 1.13.0 (`third_party/laya/README.md:1281`).
3. Jev Playground (independent third-party tool, not affiliated with TypeSafe AI). [jevplayground.com](https://jevplayground.com), accessed 2026-10-02\~07.
4. Third-party Jev benchmarks: AbdelStark/jev-benchmarks, nibzard/decision-model-benchmark. Cited via upstream `README.md:1268-1272` and `research/README.md:174-177`; originals to be verified.
5. LocalLLaMA, *typed-decisions* dataset. Hugging Face Hub, revision d0e2f0c. Author and publication details to be verified.
6. X. Zhang, J. Zhao, Y. LeCun. Character-level Convolutional Networks for Text Classification. NeurIPS 2015 (AG News). HF `fancyzhx/ag_news`.
7. E. Saravia et al. CARER: Contextualized Affect Representations for Emotion Recognition. EMNLP 2018 (DAIR Emotion). HF `dair-ai/emotion`.
8. I. Casanueva et al. Efficient Intent Detection with Dual Sentence Encoders. NLP4ConvAI 2020 (Banking77). HF `mteb/banking77`.
9. C. Clark et al. BoolQ: Exploring the Surprising Difficulty of Natural Yes/No Questions. NAACL 2019. HF `google/boolq`.
10. R. Socher et al. Recursive Deep Models for Semantic Compositionality Over a Sentiment Treebank. EMNLP 2013 (SST-5). HF `SetFit/sst5`.
11. J. FitzGerald et al. MASSIVE: A 1M-Example Multilingual Natural Language Understanding Dataset with 51 Typologically-Diverse Languages. ACL 2023 (publication details to be verified). HF `mteb/amazon_massive_intent`.
12. deepset, *prompt-injections* dataset. Hugging Face Hub, revision 4f61ecb. Bibliographic details to be verified.
13. M. Marone, O. Weller, W. Fleshman, E. Yang, D. Lawrie, B. Van Durme. mmBERT: A Modern Multilingual Encoder with Annealed Language Learning. arXiv:2509.06888, 2025.
14. Q. McNemar. Note on the sampling error of the difference between correlated proportions or percentages. Psychometrika, 1947.
15. S. Holm. A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics, 1979.
16. E. B. Wilson. Probable inference, the law of succession, and statistical inference. JASA, 1927.

## Appendix A. Reproduction

```bash
source env.sh
# Build the sets and measure Laya (no Jev requests)
export HF_HOME=$PWD/data/raw/hf && .venv/bin/python scripts/build_jev_cmp_sets.py all
bash results/F/jev_cmp/run_laya.sh && .venv/bin/python results/F/jev_cmp/laya_summary.py
# Analyze the recorded Jev sessions (no site requests; reads the jsonl only)
.venv/bin/python results/F/jev_cmp/jev_cmp.py t1 S1,S2
.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S1 T2_ag_news_40
.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S3 T5_boolq_40
.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S4,S5 T7_massive_intent_10opt_en_20,T7_massive_intent_10opt_de_20,T7_massive_intent_10opt_ja_20,T7_massive_intent_10opt_zh-CN_20,T7_massive_intent_10opt_ko_20
# S6 synthesis and cross-check
.venv/bin/python results/F/jev_cmp/s6_summary.py build
.venv/bin/python results/F/jev_cmp/s6_summary.py verify
```

The Jev sessions themselves were carried out by operating the playground UI in a browser; the procedures are preserved in each session's run card (`results/F/jev_cmp/sessions/S*/S*_run_card.md`) and in the recording tools (`jev_cmp.py record`; for S2\~S5, `s*_prep.py` and `s*_record.py` in the session folders). The full command list is in `results/F/jev_cmp/summary.md` §10.

## Appendix B. Per-task details

**T1 accuracy by workflow** (`results/F/jev_cmp/sessions/S2_20261007/S2_summary.md` §2.4)

| workflow | Decisions compared | Jev | Laya english | Reference: Laya typed-decisions |
|---|---|---|---|---|
| agent_trace_observability | 30 | 25/30 = 0.833 | 14/30 = 0.467 | 24/30 |
| customer_service | 20 | 19/20 = 0.950 | 11/20 = 0.550 | 18/20 |
| invoice_processing | 30 | 29/30 = 0.967 | 4/30 = 0.133 | 27/30 |
| security_incidents | 40 | 31/40 = 0.775 | 17/40 = 0.425 | 35/40 |

Laya base scored 0/10 on the duplicate question of invoice_processing and 2/10 on matches_order.

**T6 predicted level distribution** (argmax; gold has 8 rows per level; `results/F/jev_cmp/summary.md` §2.4)

| system | Level 0 / 1 / 2 / 3 / 4 | Mean E − gold | Within ±1 level |
|---|---|---|---|
| Jev | 4 / 13 / 6 / 12 / 5 | −0.014 | 0.875 |
| Laya english | 10 / 15 / 10 / 5 / 0 | −0.687 | 0.650 |
| Laya multilingual | 11 / 29 / 0 / 0 / 0 | −1.280 | 0.400 |

**T7 per-language McNemar (Jev vs Laya multilingual, b/c, p)** (`results/F/jev_cmp/summary.md` §2.5)

| en | de | ja | zh-CN | ko |
|---|---|---|---|---|
| 3/2, 1.0000 | 11/1, 0.0063 | 3/0, 0.2500 | 8/2, 0.1094 | 11/2, 0.0225 |

**T5·T8 Boolean details** (`results/F/jev_cmp/summary.md` §2.3)

| Task | system | Predicted true (gold 20) | FN / FP | AUROC |
|---|---|---|---|---|
| T5 | Jev | 21 | 1 / 2 | 0.988 |
| T5 | Laya english | 19 | 6 / 5 | 0.810 |
| T8 | Jev | 11 | 9 / 0 | 1.000 (degenerate interval) |
| T8 | Laya english | 11 | 9 / 0 | 0.929 |

## Appendix C. Request log summary

| Item | Value |
|---|---|
| Total requests | 438 = master log 411 (S1 41, S1b 30, S2 80, S3 80, S4 80, S5 100) + 27 before tooling (pilot 25, status checks 2) |
| By date | 2026-10-06 98, 2026-10-07 340 |
| Errors | HTTP 502 2 times (pilot: 1, run stopped and resumed; S2: 1, retry succeeded after 73.7 s), 429·limit message·captcha 0 times |
| Input check | request body = form payload 411/411, screen = response 410/410, Model ID `typesafe-ai/jev` 410/410 |
| Gap | minimum 12.1 s (S2), per-session median 15.1\~17.5 s, rule ≥ 10 s |
| Logs | `results/F/jev_cmp/jev_runs_all.jsonl`, per-session `S*_requests.jsonl`, pilot `results/F/jev_runs_raw.jsonl` (none of the three logs is included in the public repository) |

Source: `results/F/jev_cmp/summary.md` §1.

## Appendix D. Relation to document 08

`docs/08_paper_ko.md` is an earlier report from the same project; it posed the question "Can Laya be used for a Korean service?" and covered Korean applicability (reproduction, Korean support audit, zero-shot quality, fine-tuning, PoC). Its Jev comparison was a single Korean pilot with n=24 (08 §4.8). For the question of comparing the performance of Laya and Jev, this document supersedes 08, and the Korean results of 08 are summarized and included as the case study in §5 of this document.

**English** | [한국어](10_paper_laya_vs_jev_v2.ko.md)
