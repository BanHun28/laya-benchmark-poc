# A Controlled 3-arm Comparison of Jev, vanilla Laya, and trained Laya: Zero-shot Accuracy of a Non-autoregressive Decision Engine and the Effect of Per-task Fine-tuning

**Written** 2026-10-07 (v2), revised 2026-10-09 (v3, 3-arm extension) · **Environment** Apple M4 Pro (10P+4E CPU, 20-core GPU/MPS, 48 GB), macOS 26.6.2, Python 3.12.12, torch 2.14.1, transformers 5.18.0 (`results/env/env_20261002-1333.json`; for 3-arm training, `results/env/env_20261008-0940.json`) · **Laya** 0.3.23 (upstream commit 4aa6761), checkpoint bundle `convaiinnovations/laya` @ 55cf4c4, quality measured on CPU fp32 · **trained Laya** 10 per-task fine-tunings, M4 Pro MPS fp32; main training run 1 on 2026-10-08 10:57\~15:01, driver STEP FAILED 0 (`results/T3arm/run_all_status.log`). Replicate run 2 (seed 14) completed all 10 tasks (2026-10-09 00:23, `results/T3arm/rep_s14/run_all_status.log`) · **Jev** via the independent third-party public playground jevplayground.com (T1\~T8 on 2026-10-06\~07, T9·T10 on 2026-10-08 in session S7), Model ID `typesafe-ai/jev` (version not shown) · **Evidence files** for the zero-shot axis, `results/F/jev_cmp/summary.md` and `summary.json` (S6 synthesis, 0 numeric mismatches against the session summaries, `results/F/jev_cmp/S6_20261007.md:45`) and `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md`; for the 3-arm axis, `results/T3arm/summary.md` and `summary.json` (S3 synthesis, built 2026-10-09 00:23, rebuilt 2026-10-12 for the public release with English figure text, release notes and the per-item Jev fields removed, numbers unchanged, `results/T3arm/summary.md:1`; 0 mismatches in `t3arm_summary.py verify`) · **Previous version** v2 (zero-shot comparison) is preserved in `docs/10_paper_laya_vs_jev_v2.md` (English) and `docs/10_paper_laya_vs_jev_v2.ko.md` (Korean, with the public-release corrections); PDFs are not included in the public repository

## Abstract

Laya is an open-source non-autoregressive decision engine that produces probability distributions over typed decisions (choice, score, noul) in a single encoder forward pass; Jev is a commercial model that offers decisions of the same form through a hosted API. Upstream has compared the two systems only through published figures measured by third parties on different samples, and it defines the Laya base checkpoints not as a zero-shot engine but as a base to be specialized per task. This study runs a controlled comparison that feeds the same state bytes, the same question text, and the same option strings to three arms: Jev (zero-shot, public playground), vanilla Laya (the base without training), and trained Laya (the same base fine-tuned per task on task labels). There are 10 tasks, split into the 4 that are in Laya's training mix as disclosed by upstream (in-mix category) and the 6 that are not (held-out category). v2 measured Jev on 8 tasks with 438 calls (byte match between request body and pre-generated payload 411/411), and the 3-arm extension additionally measured T9·T10 with 80 calls under the same rules (byte match 80/80, 518 site requests in total).

On the zero-shot axis, Jev was significantly ahead by exact McNemar on 4 of the tasks T1\~T8 (2 after Holm correction, T1 and T7), and there was no task on which Laya was significantly ahead. On T9, Jev and vanilla both score 40/40; on T10, Jev scores 0.250, vanilla english 0.300, and multilingual 0.450, all not significant. The T1\~T8 macro accuracy is Jev 0.828, Laya english 0.646, multilingual 0.598, and Router 0.661. Trained Laya was built with about 6,400 labels per task (train up to 5,000 items x 2 epochs) and 7.5\~43.3 minutes of M4 Pro MPS training (T8 1.4 minutes). In main training run 1, trained vs Jev showed no significant difference on any of the 10 tasks after Holm correction; before correction, trained was significantly ahead on T3 (0.950 vs 0.700) and T8 (0.975 vs 0.775). Of the two tasks on which Jev was ahead in zero-shot even after Holm correction, T7 became a tie at 0.910, and on T1 (0.792 vs 0.867) the cluster bootstrap interval includes 0. Replicate run 2, which changes only the seed, also completed all 10 tasks. Taking the two runs together, there is no comparison in which Jev is significantly ahead of trained after Holm correction. Before correction, Jev was significantly ahead on T5 in run 2 (b/c 1/10, p=0.0117), but after Holm correction it is 0.1055, not significant. On the extended set (ext), the trained vs vanilla verdicts of the two runs agree on all 10 tasks. Trained's advantage on the 6 held-out tasks and T10 was significant after Holm correction in both runs, and the in-mix tasks T2·T5·T9 were not significant in both runs. Of 30 comparisons (10 tasks x 3 kinds), 27 were confirmed because the verdicts of the two runs agree, and 3 were inconsistent. All inconsistencies are n=40 Jev-item comparisons with Holm p near 0.05 (T4 trained vs vanilla significant only in run 1; T8 trained vs Jev and T8 trained vs vanilla significantly in favor of trained only in run 2). The ext category means are in-mix +0.017, held-out +0.252, and difference-in-differences +0.235 [+0.147, +0.316] in run 1, and +0.020, +0.257, +0.238 [+0.144, +0.325] in run 2, so the training gain concentrates on the tasks upstream did not train on. Judged by the calibration-separation column, which refits only the temperature, trained's ECE improvement on ext is in effect a refit effect on T1·T3·T6·T10 and a training effect on T4·T8. Training validations V1\~V6 all passed (V3 on the difference criterion, owner verdict). Retraining T1 with the same settings gave test accuracy 0.747 vs 0.690 because of MPS nondeterminism, and the seed 14 replicate run gave 0.735, so the 0.690 of main training run 1 is the outlier among the three runs. Local Laya's 1-question latency (13.8\~86.6 ms) was shorter than Jev's internet round trip (median browser POST 465 ms), but the deployment forms differ, so this is not a model-speed comparison.

- Zero-shot accuracy: on T1\~T8, Jev significantly better 4 / n.s. 4 / Laya significantly better 0 (after Holm correction 2 / 6 / 0). Pooled exact McNemar over the 240 independent single-question items: Jev 194 vs per-task best Laya 176, b/c 39/21, p=0.0273. Macro difference Jev − Router +0.167 [+0.044, +0.293] (task bootstrap, descriptive statistics). T9·T10 in S7 are both not significant.
- 3-arm accuracy (both runs): after Holm correction, trained vs Jev is trained significantly better 0 / n.s. 10 / Jev significantly better 0 in run 1, and 1 (T8) / 9 / 0 in run 2. Before correction, only T5 in run 2 is significantly in favor of Jev (0.1055 after Holm correction, n.s.). On ext, the trained vs vanilla verdicts of the two runs agree on all 10 tasks (significant on the 6 held-out tasks and T10; n.s. on T2·T5·T9). Of 30 comparisons, 27 confirmed and 3 inconsistent.
- Categories (Q1): on ext, trained − vanilla DiD +0.235 [+0.147, +0.316]. On the Jev items, the Jev − vanilla DiD is +0.179 [−0.008, +0.356], in the same direction, but the interval includes 0.
- Multilingual consistency: on zero-shot T7, the mean language penalty is Jev +0.012, Laya english −0.362, multilingual −0.287. Trained scores 0.850\~0.950 in all 5 languages.
- Calibration: the meaning of Jev's probabilities differs by question format (single choice: 59% of errors have top ≥ 0.90; multi-question T1: underconfident; T10: ECE 0.623). On ext, trained's ECE improvement is in effect a temperature refit on T1·T3·T6·T10 and a training effect on T4·T8. Most of the Brier improvement comes from training.
- Cost and validation: about 6,400 labels per task, 7.5\~43.3 minutes of training, 0.85 GB checkpoint (multilingual 0.68 GB). In V2 the upstream checkpoint reproduced the published 0.766, and three T1 runs of the same pipeline gave 0.747 / 0.690 / 0.735.
- T10 labels: in 18/40 rows Jev, vanilla english, vanilla multilingual, and trained are all wrong, so the gold-label quality is suspect (to be verified manually).
- Fine-tuning reference points: on T1, the Laya typed-decisions checkpoint 104/120 = Jev 104/120; on Korean domain routing, Laya ft-v1 22/24 vs Jev 20/24.

## 1. Introduction

### 1.1 Motivation

The Laya upstream README presents, in its "Laya (with routing) vs Jev" table, typed-decisions 0.766 vs 0.727, AG News 0.950 vs 0.910, DAIR Emotion 0.595 vs 0.480, Banking77 0.425 vs 0.870, and p50 latency 32.8 ms vs 236\~276 ms (`third_party/laya/README.md:1274-1291`; `third_party/laya/` (not included in the public repository) is recreated by cloning https://github.com/NandhaKishorM/laya at commit 4aa6761). However, the same document and BENCHMARKS.md state that the Jev figures are "third-party published, never measured here" and that the samples and prompts differ (`third_party/laya/README.md:1276-1278`, `third_party/laya/BENCHMARKS.md:3`). In other words, no controlled comparison measuring the two systems on the same inputs existed. When the samples, question text, and option rendering differ, an accuracy difference cannot be read as a system difference.

v2 (2026-10-07) filled this gap with a controlled zero-shot comparison and confirmed Jev's lead. Two questions remained, however. First, upstream defines the base checkpoints as "a fast base to specialise, not as a zero-shot decision engine" (`third_party/laya/README.md:1530`). A deployment decision therefore needs a comparison with Laya specialized per task, whereas v2's fine-tuning evidence consisted only of two reference points, the upstream T1 checkpoint and the Korean ft-v1. Second, vanilla Laya's deficit mixes the retention of tasks seen in training with generalization to unseen tasks. v3 adds a trained arm, the same base fine-tuned on task data, for all 10 tasks, and separates the two factors by splitting the tasks into categories based on Laya's training mix (`docs/11_three_arm_plan.md` §1, §2).

### 1.2 Research questions

Zero-shot axis (same as v2):

- RQ1. How does zero-shot accuracy differ on the same inputs?
- RQ2. Are the two systems' probabilities calibrated, and can confidence decide whether an item is processed automatically?
- RQ3. How stable are the decisions with respect to determinism, option order, and language changes?
- RQ4. How do latency and cost differ structurally?

3-arm axis (added in v3; the parentheses give the question numbers of `docs/11_three_arm_plan.md` §1):

- RQ5. Does Laya fine-tuned on task data (trained) reach or surpass Jev (Q2)? This broadens v2's RQ5 ("Is Laya's zero-shot deficit closed by fine-tuning?") to a trained arm on every task.
- RQ6. Do vanilla Laya's deficit relative to Jev and the training gain differ between tasks included in and excluded from Laya's training mix (Q1)?
- RQ7. What is the cost of specialization (number of labels, training time, checkpoint size) (Q3)?
- RQ8. Was Laya trained correctly (Q4)?

### 1.3 Contributions

(1) A controlled Laya vs Jev comparison with matched input bytes over 8 tasks, 8 public datasets, and 5 languages; neither the upstream documents nor the third-party benchmarks they cite contain such a comparison. (2) A 3-arm design that adds vanilla and trained, aligned on the same base and the same evaluation path. The 10 tasks, including the in-mix tasks T9·T10, are split into categories based on Laya's training mix to separate retention from generalization, and are evaluated on two layers, the Jev items and the extended set (ext). (3) A reproducible harness: per-task playground form files, pre-click payload hashes and post-click byte comparison of the request bodies, a master request log of 491 entries (v2 411 + S7 80), a training start gate (sha256), and per-step status logs. (4) Training validations V1\~V6 (zero-step identity, upstream reproduction, label-shuffle, format identity, smoke, leakage), quantification of the same-setting retraining spread and of seed replication, and a calibration separation that splits temperature refit from the training effect. (5) Statistical treatment combining multiple-comparison correction (Holm), task bootstrap, pooled McNemar over independent items, cluster bootstrap, and category difference-in-differences. (6) A confidence analysis per question format and its implications for automation thresholds. (7) Fine-tuning reference points and the Korean domain-routing PoC case. (8) 7 upstream defects and documentation inconsistencies found during the study.

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

Samples were drawn deterministically from public splits with seed 13. Single-question tasks were stratified by label after applying the deduplication and length rules, T1 was stratified by workflow, and T7 uses the first 20 test ids present in all 5 languages, with 9 wrong options drawn by seed (`data/evals/jev_cmp/MANIFEST.json`, `scripts/build_jev_cmp_sets.py`). T9·T10 are tasks added to the same builder, with 40 label-stratified rows (`results/T3arm/PREP_20261008.md` §1).

| Task | Source @revision | split | n | Format / options | Category (Laya training mix) |
|---|---|---|---|---|---|
| T1 typed-decisions | `LocalLLaMA/typed-decisions` all @d0e2f0c | test | 40 cases, 120 comparable decisions | Multiple questions: choice 50, Boolean 60, 5-level score 10 | held-out (no) |
| T2 AG News | `fancyzhx/ag_news` @eb185aa | test | 40 | choice 4 | in-mix (yes) |
| T3 DAIR Emotion | `dair-ai/emotion` split @cab853a | test | 40 | choice 6 | held-out (no) |
| T4 Banking77-10 | `mteb/banking77` @18072d2 | test | 40 | choice 10 (gold + 9 wrong options, key-only rendering) | held-out (held out) |
| T5 BoolQ | `google/boolq` @35b264d | validation | 40 | Boolean | in-mix (yes) |
| T6 SST-5 | `SetFit/sst5` @e51bdcd | test | 40 | score, 5 levels | held-out (no) |
| T7 MASSIVE intent-10 | `mteb/amazon_massive_intent` en·de·ja·zh-CN·ko @940fd47 | test | the same 20 ids x 5 languages = 100 | choice 10 (English keys, gold + 9 wrong options, reduced from upstream's 20 options) | held-out (held out) |
| T8 prompt-injections | `deepset/prompt-injections` @4f61ecb | test | 40 | Boolean | held-out (no) |
| T9 Enron spam | `SetFit/enron_spam` @1916f66 | test | 40 | Boolean (no criteria) | in-mix (yes) |
| T10 support tickets | `Tobi-Bueck/customer-support-tickets` @ddf1c81 | hash test share of train | 40 | choice 10 (10 queues, upstream queue descriptions) | in-mix (yes) |

The training mix is MANIFEST's `in_training_mix`. Upstream states that, among T1\~T8, only AG News (T2) and BoolQ (T5) were put in Laya's training mix (so retention, not generalization), that Emotion·prompt-injections·Banking77·SST-5 were held out, and that neither checkpoint was trained on typed-decisions·MASSIVE (`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`, `results/F/jev_cmp/summary.md` §2.1). T9·T10, added in the 3-arm extension, are tasks that the upstream Themes benchmark marks as in training (`third_party/laya/BENCHMARKS.md:142`, `:147`). In the table, both no and held out mean not in the training mix, and this labeling splits the tasks into the in-mix category (T2, T5, T9, T10) and the held-out category (T1, T3, T4, T6, T7, T8) (§3.5). Jev's training data are unknown, and all sources are public datasets.

The wording of T9·T10 follows the upstream Themes benchmark exactly. The T9 state is `laya.email_state(subject, message[:3000])`, and the question is "Is this email unsolicited spam or bulk marketing?" (`third_party/laya/research/scripts/bench_apps.py:159-168`). T10 uses rows whose language is en, that belong to the 10 queues, and that have a body; the state is subject and body[:3000], the question is "Which support queue should handle this ticket?", and the criteria are upstream's 10 queue descriptions (`bench_apps.py:130-155`). T10 has only one public split, train. We therefore split it into test (0\~1), dev (2), and train (3\~9) shares by the sha256 of the normalized state text modulo 10; identical texts always fall into the same share, so the overlap between shares is 0 (`results/T3arm/PREP_20261008.md` §1). Jev was measured on both tasks in session S7 (§3.3).

### 3.2 Input identity

- **state**: the JSON-serialized string that Laya actually reads (`state_text`) was put verbatim into Jev's State field. The question text is the sentence from the upstream benchmark scripts, and for T1 the dataset's own questions, used verbatim (MANIFEST `question_source`).
- **Options**: for choice, the option strings that Laya actually renders (`key: description` or the key alone, depending on the task) were entered in the same order. Because of the playground's 80-character limit, T4 was rebuilt for both systems with upstream-style key-only rendering (the previous rendering is kept as `_v0`). In T1, 10 decisions with options longer than 80 characters were excluded from the comparison.
- **Score**: since the playground accepts only 5 levels, the 70 4-level score questions of T1 were excluded. As a result, T1 compares 120 of 200 decisions.
- **Boolean**: Jev's Boolean has no description fields. As a fairness check, a Laya variant without the noul true/false descriptions (criteria) was measured separately, and the accuracy change was not significant (english 0.467 → 0.517, p=0.549; `results/F/jev_cmp/laya_summary.md` §2b). The noul questions of T5·T8 have no criteria to begin with.
- **Verification**: before every request, the hash of the payload built from the form file was checked, and after the request the actual body was compared byte by byte (411/411 match). The on-screen display and the response JSON also matched 410/410 (`results/F/jev_cmp/summary.md` §1).
- **3-arm**: vanilla and trained are evaluated on the same files as the Jev-format sets. The training items are built with the same row builder, so the question wording, criteria, option rendering, and state serialization are the same as in evaluation (§3.6, V4).

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
| S7 | 2026-10-08 15:22\~15:43 | T9 40 + T10 40 (3-arm extension) | 80 | 15.0 s |

With 2 site status checks added, the total is 438 requests (`results/F/jev_cmp/summary.md` §1). The operating rules were a click gap of at least 10 seconds, 1 retry after 60 seconds on 5xx, and an immediate stop on 429, a limit message, or a captcha. At first we imposed our own cap on the number of requests per day. Because the site publishes no numeric limit and there were 0 occurrences of 429 or limit messages in the 178 requests before the cap was lifted, the cap was lifted by owner decision on 2026-10-07, while the gap and stop rules were kept. After the cap was lifted, no 429, limit message, or captcha appeared in the 340 requests of that day, including the 260 of S3\~S5 (`docs/09_laya_vs_jev_plan.md:48`). Row 30 of T1 reused the S1 exploration request, whose payload was identical to the main run.

The 3-arm extension uses these records as they are for T1\~T8; T9·T10 were measured, with owner approval (`results/T3arm/PREP_20261008.md` "Owner decision" item 5), with 80 requests in session S7 under the same operating rules (click gap of at least 10 seconds, actual guard 15 s, 1 retry after 65 s on 5xx, immediate stop on 429, a limit message, or a captcha). All 80 requests returned HTTP 200; there were 0 cases of 5xx, 429, limit messages, or captchas, and no retries. The request bodies matched the form payloads byte for byte 80/80, and the Model ID was `typesafe-ai/jev` 80/80. The minimum gap was 15.009 s. Cumulative site requests are 518 (438 + 80), and the master log has 491 lines (`results/F/jev_cmp/sessions/S7_20261008/S7_run_card.md`, `S7_summary.md` §1).

### 3.4 Laya measurement

Laya was measured with all three runners, english, multilingual, and Router, on the same set files (laya-evals JSONL) from which the Jev forms were built, on CPU fp32 (intra-op 10, inter-op 1) with batch 8 (`results/F/jev_cmp/run_laya.sh`, `results/F/jev_cmp/S0_20261006.md`). For T1, the upstream fine-tuned checkpoint typed-decisions was added as a reference point. A rerun of T1 english gave identical answers 200/200, confirming determinism (`results/F/jev_cmp/laya_summary.md` §5). The 3-arm vanilla and trained use the same evaluation path (CPU fp32, intra-op 10 / inter-op 1, batch 8). Rerunning the 28 english·multilingual reports of v2 (1,280 decisions) on this path gave byte-identical answers (max |Δp| 0, `results/T3arm/PREP_20261008.md` §5).

### 3.5 3-arm design and categories

**Arm definitions.**

- **Jev**: the playground records of §3.3 (`results/F/jev_cmp/jev_runs_all.jsonl` (not included in the public repository); T1\~T8 from the v2 sessions, T9·T10 from S7) are used as they are.
- **vanilla Laya**: the same base as trained, without training. The base is the checkpoint the Router selects: english for the English tasks and multilingual for T7 (owner decision, `docs/11_three_arm_plan.md` §1). Only with matched bases does trained − vanilla become the training effect. The vanilla of T1\~T8 equals the english column of §4 (the multilingual column for T7).
- **trained Laya**: for each task, one base is fine-tuned separately on that task's labels. T7 is a single multilingual model trained on the 5 languages together. Because labels are used, this is a specialization comparison, not a zero-shot one, and the number of labels and the training time are reported alongside (§5.5). Main training run 1 (torch seed 13) is the primary result, and replicate run 2, which changes only the seed to 14, also completed all 10 tasks (§5.7).
- **Calibration-separation column (vanilla + task T)**: a 0-step export that keeps the base weights and refits only the temperature on that task's calib (the same procedure as V1, `results/T3arm/calib_sep/<task>/`). Its answers are identical to vanilla's and only its probabilities differ, so it is used only for calibration metrics (§5.4). It is not a fourth arm but a baseline that splits trained's calibration improvement into the refit effect and the training effect.

**Categories and the 3x2 design.** The categories are based on Laya's training mix as disclosed by upstream (§3.1). They are defined with respect to Laya only; whether Jev was trained on the same public datasets is unknown.

| Arm / category | In the training mix (T2, T5, T9, T10) | Held out of the training mix (T1, T3, T4, T6, T7, T8) |
|---|---|---|
| Jev (zero-shot, playground) | measured (T9·T10 in S7) | measured |
| vanilla Laya (zero-shot) | measured | measured |
| trained Laya (per-task fine-tuning) | measured | measured |

**Evaluation layers.**

| Layer | Purpose | Composition |
|---|---|---|
| Jev items | direct 3-arm comparison (inputs byte-identical to Jev's) | the sets of §3.1: 40 per task; T1 has 40 cases (120 decisions compared with Jev, 200 in total for the Laya arms); T7 has 20 ids x 5 languages = 100 |
| Extended set (ext) | narrow intervals for vanilla vs trained (no Jev) | T2\~T6·T9·T10 500 each (stratified from the evaluation split, seed 13, excluding overlap with training rows); T1 full test set of 400 cases = 2,000 decisions; T7 100 ids x 5 languages = 500; T8 full test set of 116 |

The evaluation split of ext is test for most tasks, validation for T5, and the hash test share for T10. Most samples are label-stratified, so their distribution differs from that of upstream's published figures (`results/T3arm/PREP_20261008.md` §5).

### 3.6 Training pipeline

**Script.** A copy of the upstream fine-tuning script (`third_party/laya/notebooks/laya_finetune_typed_decisions_mps.py`) was patched in only two places (`poc/finetune/laya_finetune_mps_patched.py`, diff `results/T3arm/finetune_script.diff`). (1) The original overwrites `max_len`·`head_max_len` with 1024/256 (`:240`); the patch keeps the base config values (english 512/192, multilingual 1024/256). (2) The original overwrites the export's `model_name` with "laya-typed-decisions" (`:358`); the patch keeps the base's name. The loss (RLCD + soft CE), optimizer, and schedule are unchanged. V1 (§3.7) checks that the patched export preserves the base.

**Settings.** MPS fp32 (no autocast), micro-batch 8 x grad-accum 4 (effective 32), `--no-checkpointing`, AdamW encoder 2.5e-5 / head 1e-4, cosine → 1e-6, RLCD σ 0.4 → 0.1, torch seed 13. The script's default hyperparameters were used for all tasks (`results/T3arm/PREP_20261008.md` header table).

**Data.** Per task, train has up to 5,000 items x 2 epochs, dev up to 1,000 rows, and calib 400 rows (owner budget, `docs/11_three_arm_plan.md` §1). Training items were built with the same row builder as the evaluation sets (`row()` in `scripts/build_jev_cmp_sets.py`, the question constants, label maps, and option sampler) and stratified by label. T1 has 5,000 decisions sampled by case, and T7 has 1,000 rows per language. Choice questions were augmented by shuffling the option order per row (score and noul were not shuffled). Dev and calib were taken from validation where it exists (T3, T6, T7) and otherwise split off train first (T1, T2, T4, T5, T8, T9); for T10 they were drawn from the hash dev share. Train, dev, and calib are disjoint on normalized text. Candidate training rows whose state text equals that of an evaluation item (Jev items and ext) were removed beforehand (`results/T3arm/PREP_20261008.md` §1, §2). T8's train split has only 546 rows (544 after filtering), so dev 60 and calib 40 were split off and all of the remaining 444 rows were used for training.

**Epoch selection and calibration.** Dev is used only for epoch selection, and calib only for the temperature fit. The epoch with the highest dev accuracy is selected, the earlier one on a tie. If a non-final epoch is selected, the temperature is refitted on the same calib. If the dev accuracy of every epoch is below that of epoch 0 (vanilla), the task gets a "training failure" flag, and the cause is traced in the order format, labels, lr (`docs/11_three_arm_plan.md` §4).

**Execution.** The driver `poc/finetune/run_all_tasks.sh` trains T1\~T10 in turn, handles per-epoch dev evaluation, epoch selection, Jev-item and ext evaluation, diagnostic records, and cleanup, and keeps only the selected checkpoint. The start gate `poc/finetune/READY_T3ARM` holds the sha256 of the 10 items files, the 30 row files, and the patched script. The main training run ran unattended on 2026-10-08 10:57:15\~15:01:31 (about 4.1 hours), and the status log ended at `RUN_ALL FINISHED` with STEP OK 148, FAILED 0 (`results/T3arm/run_all_status.log`, `results/T3arm/run_all_20261008-1057_driver.log`).

**Defaults applied and owner decisions.** The main training run started with the following defaults before the project owner's confirmation (`results/T3arm/PREP_20261008.md`, section "Defaults applied at the start of the main training run"). T8 kept its hold-out (dev 60 + calib 40 + train 444) and was trained for 2 epochs within the owner budget. V3 was reported as numbers only, with the verdict deferred. The calibration-separation column was not included, and neither the replicate run nor the Jev measurement of T9·T10 was performed. By owner decision at 2026-10-08 15:25, the T8 setting was confirmed and V3 was judged a pass on the difference criterion. The three items that were to be added are all done and included in this version: the calibration-separation column is in §5.4 and the T9·T10 Jev measurement in §5.1. The replicate training (1 run; seed 14, 10 tasks, `env SEED=14 RUN_TAG=rep_s14 bash poc/finetune/run_all_tasks.sh`) is in §5.7. Within it, T9 stalled because of resource contention with another project's experiments and was stopped once; a watcher reran T9·T10 when there was no contention, finishing at 2026-10-09 00:23 (§7.7, and the "Owner decision" section and the last two sections of the same document).

### 3.7 Training validation V1\~V6

| ID | Check | Method | Pass criterion |
|---|---|---|---|
| V1 | zero-step identity | with the patched pipeline, build an export with 0 optimizer steps (`--epochs 0`) for each base, compare it with the base, and evaluate one set | identical weight values, 100% argmax agreement, identical probabilities when evaluated with the base temperature restored |
| V2 | upstream reproduction | (a) evaluate upstream `laya-typed-decisions` on the T1 test set of 2,000 decisions. (b) train the english base with our pipeline on T1 train, 5,000 decisions x 2 epochs, and evaluate on the same 2,000 | (a) within ±0.02 of the published 0.766. (b) at least 0.562 (vanilla english 0.362 + 0.20) and above majority 0.461 |
| V3 | label-shuffle control | T3 Emotion, english base, 5,000 items with labels shuffled by seed 13, trained for 1 epoch | strict criterion: dev accuracy ≤ majority + 0.05. difference criterion: at least 0.30 below the epoch 1 dev of training on the real labels |
| V4 | format identity | per task, decode training items and compare them with the inference sequences of the same state and question | 100% token-level match (for shuffled items, against the shuffled order) |
| V5 | smoke | per base, train 200 items x 1 epoch, export, `laya.load`, evaluate; all stages for 10 tasks with the driver's `SMOKE=1` | every STEP OK |
| V6 | leakage | intersection of train·dev·calib with the evaluation items (Jev items, ext) | 0 for both exact and normalized matches |

Source: `docs/11_three_arm_plan.md` §4, `results/T3arm/PREP_20261008.md` §3.

**Deviation from the plan (V3).** The strict criterion assumes that training collapses the base to chance level. On a base with strong zero-shot ability (0.612 on this dev), permuted-label training went below vanilla but did not collapse to near majority, so the strict criterion was missed by +0.039 (§5.6). The project owner judged V3 a pass on the basis of the difference criterion and an alternative criterion (permuted < vanilla zero-shot dev, plus the difference criterion) (2026-10-08 15:25). This version follows that verdict and records the strict-criterion miss as a deviation from the plan.

### 3.8 Statistics

Accuracy intervals are Wilson 95%, and two systems on the same items are compared with the exact McNemar test (two-sided). b is the number of items only Jev gets right, and c the number only Laya gets right. For each task, the Laya compared with Jev is the most accurate of the three runners; this is a post hoc choice made after seeing the results and favors Laya. Holm correction was applied to the 8 task-level tests. The difference in task macro means was examined with a paired bootstrap (10,000 resamples) that resamples the 8 tasks with replacement; separately, the independent single-question items (T2·T3·T4·T5·T6·T8, 240 items) were examined with a pooled exact McNemar test, and the clustered T1 (40 cases) and T7 (20 ids) with a cluster bootstrap. We also report AUROC for Boolean (2,000 item resamples), Brier and ECE for calibration (15 bins, on the top probability), and the MAE of E[level] for score (`results/F/jev_cmp/summary.md` §2, §4).

The 3-arm comparison uses the same decision rule. Two arms on the same items are compared with the exact McNemar test (two-sided); b is the number of items only the first arm gets right, and c the number only the second arm gets right. If p < 0.05 and b > c, the first arm is significantly better; if c > b, the second arm is significantly better; otherwise the result is not significant. Holm correction uses a separate family for each comparison. For trained vs Jev and Jev vs vanilla, the family grew from 8 tasks to 10 when S7 added T9·T10, and trained vs vanilla has 10 tasks (for the Jev items and ext separately). Widening the family did not change the post-Holm verdicts of T1\~T8; only the Holm p-values changed. Jev vs vanilla regroups the v2 tests by base runner (T7 multilingual, the rest english), so its T4 b/c differs from §4, which uses the per-task best Laya. T9·T10 were computed with the same function from the S7 records. The ext trained − vanilla intervals are paired bootstraps over the same items (10,000 resamples, seed 13), resampling cases as clusters for T1 and ids for T7. For the Jev items, cluster bootstraps are also reported for T1 and T7. Category aggregates are macro means with equal weights over the per-task accuracies (for T1 the decisions compared with Jev, for T7 pooled over languages). Intervals are percentiles from resampling tasks with replacement within each category (10,000 resamples). The difference-in-differences (DiD) of Q1 is the mean difference in the held-out category minus the mean difference in the in-mix category, with intervals obtained by resampling the two categories separately. With 4\~6 tasks per category, the category aggregates are descriptive statistics, not population inference (`results/T3arm/summary.md` §1\~§3). In the calibration separation, the refit effect is (vanilla + task T) − vanilla and the training effect is trained − (vanilla + task T); their sum is trained − vanilla. For the replicate run, a verdict is confirmed only when the post-Holm verdicts of run 1 and run 2 agree (the Holm family of run 2 is the same 10 tasks as that of run 1, `results/T3arm/summary.md` §4.3, §7).

### 3.9 Summary of threats

The playground is not an API, and the model version is not shown. With n=40 per task, the Wilson half-width is about ±0.15. The T1 gold label is the argmax of the dataset's teacher distribution, and the identity of the teacher could not be confirmed. Trained has two training runs per task, and MPS training is not bitwise deterministic (§5.6, §5.7). The gold-label quality of T10 is suspect (§5.1). Details are in §7.7.

## 4. Results I: zero-shot comparison

This section reproduces the zero-shot results of v2 (T1\~T8) as they are. Laya here means the three untrained base runners (english, multilingual, Router); the vanilla of §5 equals the english column for the English tasks and the multilingual column for T7. The Holm correction in this section uses the 8-task family of v2. The zero-shot results for T9·T10, measured in session S7 of the 3-arm extension, are as follows; the 3-arm table is in §5.1. On T9, Jev and all three Laya runners score 40/40 = 1.000. On T10, Jev scores 10/40 = 0.250, Laya english (= Router) 0.300, and multilingual 0.450; exact McNemar gives 3/5 vs english (p=0.7266) and 4/12 vs multilingual (p=0.0768), all not significant. Jev on T10 is strongly overconfident with ECE 0.623, and in 20/40 rows it shows the gold option as 0% (`results/F/jev_cmp/sessions/S7_20261008/S7_summary.md` §2, §3).

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

## 5. Results II: 3-arm comparison

The trained figures in §5.1\~§5.6 are from main training run 1 (seed 13). Replicate run 2 with seed 14 also completed all 10 tasks. The comparison of the two runs and the confirmation of verdicts are in §5.7 (of 30 comparisons, 27 confirmed and 3 inconsistent). The figures come from `results/T3arm/summary.md` (built 2026-10-09 00:23, rebuilt 2026-10-12 for the public release with English figure text, release notes and the per-item Jev fields removed, numbers unchanged, `results/T3arm/summary.md:1`; hereafter the 3-arm synthesis), and the same values are in `results/T3arm/summary.json`.

### 5.1 3-arm accuracy: Jev items (RQ5)

| Task (n, category) | Jev | vanilla | trained | trained vs Jev: b/c, p (Holm p) | trained vs vanilla: b/c, p (Holm p) |
|---|---|---|---|---|---|
| T1 typed-decisions (120, held-out) | 0.867 | 0.383 | 95/120 = 0.792 | 10/19, 0.1360 (0.9523) | 56/7, 1.4e-10 (1.4e-09) |
| T2 AG News (40, in-mix) | 0.875 | 0.975 | 38/40 = 0.950 | 3/0, 0.2500 (1.0000) | 0/1, 1.0000 (1.0000) |
| T3 DAIR Emotion (40, held-out) | 0.700 | 0.750 | 38/40 = 0.950 | 11/1, 0.0063 (0.0635) | 10/2, 0.0386 (0.2314) |
| T4 Banking77-10 (40, held-out) | 0.925 | 0.725 | 38/40 = 0.950 | 3/2, 1.0000 (1.0000) | 9/0, 0.0039 (0.0312) |
| T5 BoolQ (40, in-mix) | 0.925 | 0.725 | 31/40 = 0.775 | 2/8, 0.1094 (0.8750) | 2/0, 0.5000 (1.0000) |
| T6 SST-5 (40, held-out) | 0.650 | 0.425 | 27/40 = 0.675 | 6/5, 1.0000 (1.0000) | 16/6, 0.0525 (0.2624) |
| T7 MASSIVE-10 (100, held-out) | 0.910 | 0.620 | 91/100 = 0.910 | 7/7, 1.0000 (1.0000) | 32/3, 4.2e-07 (3.8e-06) |
| T8 prompt-injections (40, held-out) | 0.775 | 0.775 | 39/40 = 0.975 | 9/1, 0.0215 (0.1934) | 9/1, 0.0215 (0.1504) |
| T9 Enron spam (40, in-mix) | 1.000 | 1.000 | 39/40 = 0.975 | 0/1, 1.0000 (1.0000) | 0/1, 1.0000 (1.0000) |
| T10 support tickets (40, in-mix) | 0.250 | 0.300 | 12/40 = 0.300 | 5/3, 0.7266 (1.0000) | 1/1, 1.0000 (1.0000) |

Source: 3-arm synthesis §1.1. b is the number of items only the first arm gets right, and c the number only the second arm gets right. Holm correction was applied separately to the 10 tasks of trained vs Jev and the 10 tasks of trained vs vanilla. With Jev on T9·T10 (S7) added, the trained vs Jev family widened from 8 tasks to 10, and the post-Holm verdicts of T1\~T8 did not change. Wilson 95% intervals for the accuracies are in Figure 4 and 3-arm synthesis §1.1. For T1 and T7, the item-level p-values are optimistic because of clustering (cluster bootstrap below).

| Comparison (number of tasks) | Criterion | First arm significantly better | Not significant | Second arm significantly better |
|---|---|---|---|---|
| trained vs Jev (10) | exact McNemar, uncorrected α 0.05 | 2 (T3, T8) | 8 | 0 |
| trained vs Jev (10) | Holm correction | 0 | 10 | 0 |
| trained vs vanilla (10) | exact McNemar, uncorrected α 0.05 | 5 (T1, T3, T4, T7, T8) | 5 | 0 |
| trained vs vanilla (10) | Holm correction | 3 (T1, T4, T7) | 7 | 0 |
| Jev vs vanilla (10) | exact McNemar, uncorrected α 0.05 | 4 (T1, T4, T5, T7) | 6 | 0 |
| Jev vs vanilla (10) | Holm correction | 2 (T1, T7) | 8 | 0 |

For trained vs Jev in run 1, all 10 tasks are not significant after Holm correction. Before correction, trained was significantly ahead on T3 (b/c 11/1, p=0.0063, Holm 0.0635) and T8 (9/1, p=0.0215, Holm 0.1934), and in run 1 there is no task on which Jev is significantly ahead even before correction. The tasks on which Jev is numerically ahead are T1 (0.867 vs 0.792), T5 (0.925 vs 0.775, b/c 2/8, p=0.1094), and T9 (1.000 vs 0.975). On T1 and T7, where Jev was significantly ahead in zero-shot even after Holm correction, the gap disappeared. On T1, replicate run 2 scored 103/120 = 0.858, b/c 11/12 against Jev (104/120) (§5.6). In run 2, only T8 was significantly in favor of trained after Holm correction (9/0, Holm 0.0391), and before correction Jev was ahead on T5 (1/10, p=0.0117). The post-Holm p of run 2 T5 in the 10-task family is 0.1055, not significant. Hence, after Holm correction there is no case in either run in which Jev is significantly ahead of trained, and before correction there is one, T5 of run 2 (§5.7). Since trained vs vanilla on the Jev items is significant after Holm correction for only 3 tasks because of the small n, the main evidence for the training effect is the ext of §5.2.

| Task | Comparison | Accuracy difference | Cluster bootstrap 95% | Clusters / decisions |
|---|---|---|---|---|
| T1 | trained − Jev | −0.075 | [−0.185, +0.025] | 40 / 120 |
| T1 | trained − vanilla | +0.408 | [+0.304, +0.516] | 40 / 120 |
| T1 | Jev − vanilla | +0.483 | [+0.371, +0.597] | 40 / 120 |
| T7 | trained − Jev | +0.000 | [−0.100, +0.110] | 20 / 100 |
| T7 | trained − vanilla | +0.290 | [+0.150, +0.440] | 20 / 100 |
| T7 | Jev − vanilla | +0.290 | [+0.100, +0.470] | 20 / 100 |

Source: 3-arm synthesis §1.4. Clusters were resampled with replacement (10,000 resamples, seed 13); Jev − vanilla has the same values as in §4.2.

- **T1**: by type, trained scores choice 38/50, noul 50/60, and score 7/10, and Jev 42/50, 56/60, and 6/10. The metrics against the teacher distribution (soft acc / Brier vs soft / score MAE) are Jev 0.590 / 0.077 / 0.390, vanilla 0.361 / 0.333 / 0.584, and trained 0.515 / 0.104 / 0.254. On all 200 decisions that the Laya arms evaluate, trained scores 137/200 = 0.685 and vanilla 66/200 = 0.330 (b/c 85/14, p=1.4e-13; 3-arm synthesis §1.2).
- **T7**: the per-language accuracies are below. With n=20 per language, they are directional signals. Trained rose sharply on de (0.400 → 0.850) and ko (0.450 → 0.900), where vanilla was weakest, and became similar to Jev.

| arm | en | de | ja | zh-CN | ko | Pooled |
|---|---|---|---|---|---|---|
| Jev | 0.900 | 0.900 | 0.950 | 0.900 | 0.900 | 0.910 |
| vanilla (multilingual) | 0.850 | 0.400 | 0.800 | 0.600 | 0.450 | 0.620 |
| trained | 0.950 | 0.850 | 0.950 | 0.900 | 0.900 | 0.910 |

- **Secondary metrics**: T5 AUROC is Jev 0.988, vanilla 0.810, and trained 0.831, so a difference in ranking quality remains. T6 MAE of E[level] is Jev 0.432, vanilla 0.888, and trained 0.472, and T8 AUROC is 1.000, 0.929, and 1.000. On T9, Jev, vanilla, and trained all have AUROC 1.000 (3-arm synthesis §1.5).
- **T10 (label check)**: Jev 10/40, vanilla english 12/40, trained 12/40, and the reference runner multilingual 18/40. In 18/40 rows all four systems are wrong, and on Customer Service and Human Resources all four systems score 0/4. From reading the S7 records, in most of the errors the gold queue does not match the queue descriptions given in the question (interpretation). The gold-label quality of T10 is therefore suspect and needs manual verification. Trained in run 2 scored 17/40 (0.425) (§5.7). Until verified, T10 accuracy is not read as routing ability (3-arm synthesis §1.6, `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md` §3.6).

![3-arm accuracy by task: Jev vs vanilla Laya vs trained Laya, Jev items](../results/T3arm/figs/accuracy_3arm.png)

**Figure 4.** 3-arm accuracy by task (bars) with Wilson 95% intervals (thin lines), Jev items. Jev on T9·T10 is from the session S7 records. The annotations on the right are exact McNemar tests against trained (run 1) (b/c, p, Holm p) (`results/T3arm/figs/accuracy_3arm.png`).

### 5.2 Extended set: vanilla vs trained

| Task (category) | n | vanilla | trained | trained − vanilla [95%] | b/c, p (Holm p) |
|---|---|---|---|---|---|
| T1 typed-decisions (held-out) | 2,000 | 0.363 | 0.686 | +0.323 [+0.290, +0.355] | 818/172, 2.8e-101 (2.8e-100) |
| T2 AG News (in-mix) | 500 | 0.940 | 0.946 | +0.006 [−0.014, +0.026] | 14/11, 0.6900 (1.0000) |
| T3 DAIR Emotion (held-out) | 500 | 0.488 | 0.886 | +0.398 [+0.352, +0.446] | 209/10, 1.4e-49 (1.3e-48) |
| T4 Banking77-10 (held-out) | 500 | 0.876 | 0.964 | +0.088 [+0.062, +0.116] | 47/3, 3.7e-11 (2.2e-10) |
| T5 BoolQ (in-mix) | 500 | 0.834 | 0.832 | −0.002 [−0.024, +0.020] | 16/17, 1.0000 (1.0000) |
| T6 SST-5 (held-out) | 500 | 0.338 | 0.590 | +0.252 [+0.200, +0.304] | 172/46, 2.6e-18 (2.1e-17) |
| T7 MASSIVE intent-10 (held-out) | 500 | 0.692 | 0.878 | +0.186 [+0.124, +0.248] | 110/17, 7.4e-18 (5.2e-17) |
| T8 prompt-injections (held-out) | 116 | 0.698 | 0.966 | +0.267 [+0.181, +0.353] | 33/2, 3.7e-08 (1.8e-07) |
| T9 Enron spam (in-mix) | 500 | 0.992 | 0.988 | −0.004 [−0.012, +0.004] | 1/3, 0.6250 (1.0000) |
| T10 support tickets (in-mix) | 500 | 0.264 | 0.332 | +0.068 [+0.028, +0.106] | 68/34, 0.0010 (0.0039) |

Source: 3-arm synthesis §2.1. b is the number of items only trained gets right and c the number only vanilla gets right; Holm correction was applied over the 10 tasks. The intervals of the differences are paired bootstraps (clusters: cases for T1, ids for T7). T1 accuracy is against the argmax gold (the table below uses the dataset label, upstream's definition).

All 6 held-out tasks rose significantly after Holm correction (+0.088\~+0.398). Among the in-mix tasks, T2, T5, and T9 are not significant, and only T10 rose significantly (+0.068, Holm p=0.0039). The three non-significant in-mix tasks are those where vanilla is already high (T2 0.940, T9 0.992) or where vanilla remembers the training split (T5, §5.6). T10 is the exception, with a low vanilla of 0.264, and the gold-label quality of the same dataset is suspect (§5.1, §7.4). In run 2 as well, all 6 held-out tasks rose significantly after Holm correction (+0.086\~+0.398), and among the in-mix tasks T2·T5·T9 were not significant (+0.002, +0.004, −0.004) and T10 was significant (+0.076). The ext verdicts of the two runs agree on all 10 tasks (§5.7).

| T1 test 2,000 decision | accuracy (dataset label) | soft acc | Brier vs soft | ECE | score MAE |
|---|---|---|---|---|---|
| upstream `laya-typed-decisions` (V2 a) | 0.766 | 0.471 | 0.061 | 0.214 | 0.242 |
| V2(b): preparation run of the same pipeline | 0.747 | 0.495 | 0.059 | 0.148 | 0.253 |
| vanilla english | 0.361 | 0.331 | 0.316 | 0.173 | 0.694 |
| trained (main training T1, run 1) | 0.690 | 0.463 | 0.099 | 0.112 | 0.359 |

Source: 3-arm synthesis §2.2. V2(b) and main training T1 are runs with the same script, items, seed, and arguments. Run 2 with seed 14 gave 0.735 (comparison of the three runs in §5.6).

![ext set: trained − vanilla accuracy difference with paired bootstrap 95% intervals](../results/T3arm/figs/ext_trained_minus_vanilla.png)

**Figure 5.** trained − vanilla accuracy difference on the ext set (dots) with paired bootstrap 95% intervals (thin lines). Filled dots are run 1 (seed 13), and hollow dots replicate run 2 (seed 14). The annotations on the right give run 1's difference and interval, b/c, exact McNemar p, and Holm p, with run 2's difference in parentheses (`results/T3arm/figs/ext_trained_minus_vanilla.png`).

### 5.3 Category aggregates (RQ6)

The categories follow Laya's training mix as in §3.5. With Jev on T9·T10 added by S7, the in-mix category of every aggregate is T2·T5·T9·T10.

| Basis | arm | In-mix macro [95%] | In-mix tasks | Held-out macro [95%] |
|---|---|---|---|---|
| Jev items | Jev | 0.762 [0.419, 0.969] | T2·T5·T9·T10 | 0.804 [0.721, 0.885] |
| Jev items | vanilla | 0.750 [0.469, 0.988] | T2·T5·T9·T10 | 0.613 [0.491, 0.732] |
| Jev items | trained | 0.750 [0.462, 0.963] | T2·T5·T9·T10 | 0.875 [0.784, 0.952] |
| ext | vanilla | 0.758 [0.433, 0.966] | T2·T5·T9·T10 | 0.576 [0.428, 0.730] |
| ext | trained | 0.774 [0.485, 0.967] | T2·T5·T9·T10 | 0.828 [0.716, 0.937] |

| Basis | Difference | In-mix mean [95%] | Held-out mean [95%] | Held-out − in-mix (DiD) [95%] |
|---|---|---|---|---|
| Jev items | Jev − vanilla (Q1) | +0.013 [−0.075, +0.138] | +0.191 [+0.054, +0.330] | +0.179 [−0.008, +0.356] |
| Jev items | trained − vanilla | +0.000 [−0.025, +0.031] | +0.262 [+0.212, +0.327] | +0.262 [+0.202, +0.333] |
| Jev items | trained − Jev | −0.013 [−0.100, +0.062] | +0.071 [−0.017, +0.163] | +0.083 [−0.035, +0.215] |
| ext | trained − vanilla | +0.017 [−0.003, +0.051] | +0.252 [+0.171, +0.328] | +0.235 [+0.147, +0.316] |

Source: 3-arm synthesis §3. The in-mix tasks are T2·T5·T9·T10 in every row, and the held-out tasks are T1·T3·T4·T6·T7·T8. Trained is run 1. The category aggregates of run 2 are in §5.7.

- **Training gain**: on ext, trained − vanilla is +0.017 in the in-mix category and +0.252 in the held-out category, and the interval of the DiD, +0.235 [+0.147, +0.316], does not include 0. The training gain concentrates on the tasks upstream did not train on. On the in-mix tasks, vanilla has already seen the data, so the ceiling on the gain is low (retention ceiling). The direction is the same on the Jev items (DiD +0.262 [+0.202, +0.333]).
- **Q1 (Jev − vanilla)**: vanilla's deficit relative to Jev is +0.191 [+0.054, +0.330] in the held-out category, an interval that excludes 0, and +0.013 [−0.075, +0.138] in the in-mix category. The DiD is +0.179 [−0.008, +0.356], pointing in the direction "the deficit is larger on held-out tasks", but its lower bound lies just below 0, so no verdict is drawn. Of the four in-mix tasks, T9 is near the ceiling for all three arms and T10 has suspect label quality (§5.1), so the in-mix mean depends heavily on the nature of these two tasks.
- **trained − Jev**: held-out category +0.071 [−0.017, +0.163], in-mix category −0.013 [−0.100, +0.062]; both intervals include 0.

![Arm macro accuracy by category: Jev items on top, ext below](../results/T3arm/figs/category_macro.png)

**Figure 6.** Arm macro accuracy by Laya training-mix category (bars) with bootstrap 95% intervals from resampling tasks within each category (thin lines). The top panel shows the three arms on the Jev items (Jev's T9·T10 from S7), the bottom panel vanilla and trained (run 1) on ext; the annotations on the right list the tasks included in each mean (`results/T3arm/figs/category_macro.png`).

### 5.4 Calibration

The source of the temperature differs by arm. Trained refitted per-format temperatures on the task calib (400 rows, T8 40 rows); vanilla english uses the values upstream fitted per format and per option-count bucket, and vanilla multilingual (T7) uses the default 1.0. The calibration difference trained − vanilla therefore includes a temperature refit effect. In V1, refitting alone, without training, changed ECE from 0.083 → 0.064 for english and from 0.365 → 0.179 for multilingual (§5.6). The calibration-separation column vanilla + task T (§3.5) is the baseline that removes this effect. Its answers are the same as vanilla's: argmax agreed on 6,735 of 6,736 decisions (6,736 if rounding ties count as the same answer), and correctness agreed on all 6,736. Accuracy and the accuracy tests are therefore those of vanilla, and only Brier·ECE·coverage change (3-arm synthesis §4.3).

| Jev items (Brier / ECE) | Jev | vanilla | vanilla + task T | trained |
|---|---|---|---|---|
| T1 | 0.237 / 0.181 | 0.724 / 0.205 | 0.656 / 0.129 | 0.353 / 0.180 |
| T2 | 0.220 / 0.118 | 0.053 / 0.083 | 0.051 / 0.064 | 0.095 / 0.011 |
| T3 | 0.537 / 0.278 | 0.429 / 0.174 | 0.428 / 0.209 | 0.093 / 0.074 |
| T4 | 0.114 / 0.069 | 0.349 / 0.150 | 0.337 / 0.155 | 0.072 / 0.012 |
| T5 | 0.098 / 0.103 | 0.393 / 0.190 | 0.447 / 0.229 | 0.411 / 0.190 |
| T6 | 0.502 / 0.184 | 0.770 / 0.239 | 0.687 / 0.112 | 0.461 / 0.153 |
| T7 | 0.140 / 0.068 | 0.584 / 0.216 | 0.525 / 0.083 | 0.173 / 0.074 |
| T8 | 0.307 / 0.194 | 0.401 / 0.223 | 0.337 / 0.168 | 0.035 / 0.021 |
| T9 | 0.019 / 0.060 | 0.005 / 0.014 | 0.001 / 0.004 | 0.029 / 0.026 |
| T10 | 1.319 / 0.623 | 0.775 / 0.253 | 0.733 / 0.162 | 0.752 / 0.184 |

| ext (Brier / ECE) | vanilla | vanilla + task T | trained |
|---|---|---|---|
| T1 | 0.749 / 0.173 | 0.685 / 0.035 | 0.434 / 0.112 |
| T2 | 0.096 / 0.032 | 0.096 / 0.020 | 0.097 / 0.013 |
| T3 | 0.894 / 0.411 | 0.666 / 0.074 | 0.196 / 0.077 |
| T4 | 0.211 / 0.074 | 0.212 / 0.077 | 0.061 / 0.015 |
| T5 | 0.256 / 0.083 | 0.291 / 0.137 | 0.295 / 0.128 |
| T6 | 0.863 / 0.313 | 0.724 / 0.087 | 0.530 / 0.074 |
| T7 | 0.490 / 0.187 | 0.436 / 0.094 | 0.196 / 0.050 |
| T8 | 0.526 / 0.262 | 0.439 / 0.207 | 0.057 / 0.034 |
| T9 | 0.014 / 0.006 | 0.014 / 0.006 | 0.018 / 0.005 |
| T10 | 0.851 / 0.201 | 0.801 / 0.088 | 0.757 / 0.054 |

| Calibration separation (refit / training) | ext ECE | ext Brier | Jev items ECE | Jev items Brier |
|---|---|---|---|---|
| T1 | −0.138 / +0.077 | −0.064 / −0.250 | −0.076 / +0.051 | −0.067 / −0.303 |
| T2 | −0.012 / −0.006 | −0.000 / +0.001 | −0.019 / −0.052 | −0.002 / +0.043 |
| T3 | −0.336 / +0.002 | −0.228 / −0.470 | +0.034 / −0.135 | −0.002 / −0.334 |
| T4 | +0.004 / −0.063 | +0.001 / −0.151 | +0.005 / −0.143 | −0.012 / −0.265 |
| T5 | +0.055 / −0.010 | +0.035 / +0.003 | +0.039 / −0.039 | +0.054 / −0.036 |
| T6 | −0.226 / −0.013 | −0.139 / −0.194 | −0.127 / +0.041 | −0.084 / −0.226 |
| T7 | −0.093 / −0.045 | −0.054 / −0.240 | −0.133 / −0.009 | −0.060 / −0.352 |
| T8 | −0.055 / −0.173 | −0.087 / −0.382 | −0.055 / −0.147 | −0.065 / −0.302 |
| T9 | +0.000 / −0.001 | +0.000 / +0.003 | −0.010 / +0.022 | −0.004 / +0.029 |
| T10 | −0.113 / −0.034 | −0.050 / −0.045 | −0.091 / +0.022 | −0.042 / +0.019 |

Source: 3-arm synthesis §4.1\~§4.3. The refit effect is (vanilla + task T) − vanilla and the training effect is trained − (vanilla + task T); their sum is trained − vanilla. A negative value means the metric decreased (improved). The Jev items of T1 are the 120 decisions comparable with Jev. Brier is the mean over rows of the squared error summed over all options, and ECE uses 15 bins on the top probability. Because Jev's probabilities are rounded to the second decimal place, Brier·ECE carry a floor error of about ±0.005.

The per-task separation is read primarily from ext, which has larger samples (116\~2,000 decisions per task).

- **Tasks where the ECE improvement is in effect a refit**: T1 (refit −0.138, training +0.077), T3 (−0.336, +0.002), T6 (−0.226, −0.013), T10 (−0.113, −0.034). On these tasks, trained's lower ECE than vanilla's is the effect of refitting the temperature on the task calib, not of training. On T1, training actually raised ECE.
- **Tasks where the ECE improvement is a training effect**: T4 (+0.004, −0.063) and T8 (−0.055, −0.173). T7 mixes the two (−0.093, −0.045).
- **Tasks with small or adverse changes**: T2 (−0.012, −0.006) and T9 (+0.000, −0.001) change little because vanilla is already well calibrated. On T5, the refit raised ECE by +0.055. The calib rows came from the BoolQ train split, and vanilla shows signs of remembering that split's rows (§5.6); a temperature fitted on those rows does not suit the validation-based ext. T5's coverage@5% error is vanilla 0.462, vanilla + task T 0.460, and trained 0.174, a drop on the training side.
- **Brier**: because Brier also reflects the accuracy change, most of its improvement is a training effect. The ext training effects are T1 −0.250, T3 −0.470, T4 −0.151, T6 −0.194, T7 −0.240, and T8 −0.382, and the refit effects are 0.09 or less in absolute value except for T3 −0.228 and T6 −0.139.
- **Jev items (n=40)**: on some tasks the separation differs from ext. T3 is a refit on ext but comes out as a training effect on the Jev items (+0.034, −0.135). Because the samples are small, per-task judgments follow ext.
- **clamp**: for T1 and T8, the fitted temperature of vanilla + task T was clipped to laya's load range [0.5, 5]: T1 choice 7.613 → 5.000 and noul 10.000 → 5.000, and T8 noul 10.000 → 5.000. 10.000 is the fit cap of the training script. The vanilla + task T of these two tasks may therefore fall short of the temperature that fits the calib, so the refit effect may be underestimated and the training effect overestimated. Trained's fitted temperatures are within the range on every task (§5.6).
- **Jev**: Jev's calibration on the Jev items varies greatly by task. T9 has ECE 0.060, but T10, with Brier 1.319 and ECE 0.623, is the worst of the four columns. On T10, Jev shows the gold option as 0% in 20/40 rows (opening of §4).

This version therefore limits the reading of trained's ECE improvement as a training effect to T4·T8 (and part of T7). Accuracy comparisons are unaffected by the temperature (temperature does not change the argmax).

### 5.5 Specialization cost (RQ7)

| Task | Labels (train + calib + dev) | Training item-passes | train loop (min) | MPS allocated / driver peak (GB) | Checkpoint (GB) |
|---|---|---|---|---|---|
| T1 | 6,000 (5,000 + 400 + 600) | 10,000 | 39.9 | 20.7 / 30.2 | 0.85 |
| T2 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 14.4 | 15.2 / 21.6 | 0.85 |
| T3 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 10.1 | 8.8 / 16.2 | 0.85 |
| T4 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 11.6 | 9.7 / 18.4 | 0.85 |
| T5 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 28.3 | 20.7 / 26.2 | 0.85 |
| T6 | 6,100 (5,000 + 400 + 700) | 10,000 | 11.4 | 9.1 / 17.7 | 0.85 |
| T7 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 7.5 | 6.7 / 15.9 | 0.68 |
| T8 | 544 (444 + 40 + 60) | 888 | 1.4 | 20.8 / 26.0 | 0.85 |
| T9 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 43.3 | 20.7 / 32.3 | 0.85 |
| T10 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 26.8 | 18.1 / 22.7 | 0.85 |

Source: 3-arm synthesis §5. The base is multilingual only for T7 and english for the rest. The label total is train + calib (temperature fit) + dev (epoch selection). Time and memory are the values from the run_ft reports (`results/T3arm/<task>/train_timing.json`, MPS fp32), and the checkpoint size is the summed file size (decimal GB) of `poc/finetune/ckpt_t3arm/<task>/` (not included in the public repository). Jev and vanilla involve no labels or training.

Trained costs about 6,400 labels per task (for T8, all 544 rows that passed the filter out of the 546 in the train split) and an M4 Pro MPS training loop of 7.5\~43.3 minutes (T8 1.4 minutes). Tasks with long inputs (T1, T5, T9, T10) took longer, 26.8\~43.3 minutes, and short ones 7.5\~14.4 minutes. The training loops of the 10 tasks sum to 194.8 minutes (3.25 hours), nearly equal to the 3.22 hours predicted in the preparation stage (`results/T3arm/PREP_20261008.md` §7). The whole main training run, including evaluation and cleanup, took 10:57\~15:01 (about 4.1 hours). A separate checkpoint remains for each task, 0.85 GB for english and 0.68 GB for multilingual, 8.29 GB in total for the 10 tasks. In replicate run 2, task durations grew in the period that overlapped with another project's experiments (T6 20 minutes vs 13.5 minutes in run 1, T7 15 vs 11.4 minutes, T8 8 vs 2.4 minutes; these come from the record in the last section of `results/T3arm/PREP_20261008.md` and are measured on a different basis from the train loop in the table). Costs are therefore reported with the run 1 values. Trained checkpoints have the same architecture and sequence budget as the base (V1), so inference latency is expected to follow the Laya structure of §4.5, but latency was not measured separately for trained.

### 5.6 Training validation (RQ8)

| ID | Check | Key figures | Verdict |
|---|---|---|---|
| V1 | zero-step identity | weight tensor values identical, english 206/206, multilingual 170/170. argmax agreement 40/40, 20/20. answers with the base temperature restored identical 40/40, 20/20. refit alone: ECE english 0.083 → 0.064, multilingual 0.365 → 0.179 | pass |
| V2 | upstream reproduction | (a) upstream checkpoint 0.766 (published 0.766, criterion ±0.02). (b) preparation run of our pipeline 0.747 (criterion ≥ 0.562, majority 0.461) | pass |
| V3 | label-shuffle | permuted 0.385, real labels (main training T3 epoch 1) 0.864, vanilla 0.612, majority 0.296. misses the strict criterion 0.346 by +0.039; difference 0.479 ≥ 0.30 | pass (difference criterion, owner verdict) |
| V4 | format identity | 10 tasks, token match with the inference sequences 250/250, option decode and target checks on 49,084 items | pass |
| V5 | smoke | english 3.95 items/s, multilingual 20.14 items/s. driver SMOKE STEP OK 163, FAILED 0 | pass |
| V6 | leakage | intersection of train·dev·calib with the evaluation texts over the 10 tasks: exact 0 / normalized 0. removed before sampling: T3 1, T7 24 | pass |

Source: 3-arm synthesis §6.2, §6.3, `results/T3arm/validity/`. The V3 verdict is the owner's and is recorded in 3-arm synthesis §6.3 and in `results/T3arm/PREP_20261008.md` "Owner decision" item 1. The only change in the weight file of the V1 export is the dtype of the temperature buffer (the values are unchanged), which is why the file sha256 differs. In the config, the temperature is refitted on calib and `temperature_by_options` is removed. In V3's permuted training, train accuracy stayed at chance (0.15\~0.21), and the remaining correct answers concentrated on items vanilla got right (0.475 vs 0.242). The part above majority is therefore interpreted as residual pretrained ranking, not leakage (`results/T3arm/PREP_20261008.md` §3).

| Task | dev: epoch 0 (vanilla) → 1 → 2 | Selected epoch | train − dev | flip dev40 [95%] | Training-failure flag |
|---|---|---|---|---|---|
| T1 | 0.365 → 0.667 → 0.683 | 2 | +0.054 | 0.031 [0.000, 0.069] | no |
| T2 | 0.936 → 0.934 → 0.937 | 2 | +0.027 | 0.005 [0.000, 0.015] | no |
| T3 | 0.612 → 0.864 → 0.897 | 2 | +0.034 | 0.015 [0.000, 0.040] | no |
| T4 | 0.842 → 0.922 → 0.946 | 2 | +0.013 | 0.035 [0.000, 0.095] | no |
| T5 | 0.986 → 0.955 → 0.971 | 2 | +0.009 | - | yes (dev baseline contamination) |
| T6 | 0.360 → 0.490 → 0.506 | 2 | +0.142 | - | no |
| T7 | 0.671 → 0.854 → 0.868 | 2 | +0.069 | 0.010 [0.000, 0.025] | no |
| T8 | 0.683 → 0.967 → 0.950 | 1 (recalibrated) | +0.033 | - | no |
| T9 | 0.996 → 0.995 → 0.995 | 1 (recalibrated) | −0.001 | - | yes (ceiling effect) |
| T10 | 0.419 → 0.367 → 0.385 | 2 | +0.083 | 0.175 [0.105, 0.250] | yes (dev label-distribution mismatch) |

Source: 3-arm synthesis §6.1. train − dev is the train accuracy of the last window (training forward with dropout on) minus the dev accuracy of the selected epoch. flip is the per-permutation rate of answer changes when the option order of the first 40 dev rows of a choice task is permuted (for T1, 58 choice questions). A training failure means that the dev accuracy of every epoch is below that of epoch 0 (vanilla).

![Dev accuracy by task: from epoch 0 (vanilla) to epoch 2](../results/T3arm/figs/dev_curves.png)

**Figure 7.** Per-task dev accuracy curves over epoch 0 (vanilla) → 1 → 2. Outlined circles mark the selected epoch, and the last point is the final export (last epoch + fitted temperature) (`results/T3arm/figs/dev_curves.png`).

None of the 3 training-failure flags is a pipeline failure (`results/T3arm/PREP_20261008.md`, the "Found during the main training run" sections).

- **T5 (dev baseline contamination)**: dev came from the BoolQ train split, and BoolQ is in upstream's training mix. From the same distribution, vanilla shows 0.986 on the train-row dev and 0.834 on the validation ext, a sign that it remembers the train rows. Training wore that memory down slightly and dev went down, while on the validation-based ext vanilla and trained are equal (0.834 vs 0.832). The format matched in V4 and train − dev is 0.009, so it does not look like a label or lr problem.
- **T9 (ceiling effect)**: vanilla is already at dev 0.996 and ext 0.992, and the flag came from a difference of 1 row out of 1,000 dev rows. Vanilla's dev and ext are nearly equal, so there is no memory signal like T5's.
- **T10 (dev label-distribution mismatch)**: dev follows the natural distribution, in which the Technical Support share (0.262) is the largest, while train and ext are close to uniform. Vanilla's predictions are skewed toward this queue, which favors it on the natural-distribution dev. Trained improved recall on 7 of the 8 queues present in dev, and dev macro recall also rose from 0.347 to 0.403. On the uniform ext it gains +0.068.

**Caveats.** Even after training, T10's option-order flip is 0.175 [0.105, 0.250], higher than on the other choice tasks (0.005\~0.035), so its decisions are sensitive to option order. T6 has the largest train − dev of the 10 tasks, +0.142 (the others are +0.083 or less). Since no additional epochs or regularization comparisons were run, no verdict on overfitting is drawn.

**Same-setting T1 retraining spread and seed replication.** V2(b) from the preparation stage and main training run 1 have the same script sha256, items sha256, seed 13, and script arguments, yet their results differ. Replicate run 2, which changes only the seed to 14, also completed T1 (3-arm synthesis §6.4, §7.4).

| Metric | V2(b) (preparation, seed 13) | Main training run 1 (seed 13) | run 2 (seed 14) |
|---|---|---|---|
| dev epoch 1 / 2 | 0.708 / 0.738 | 0.667 / 0.683 | 0.702 / 0.750 |
| test accuracy (dataset label) | 0.747 | 0.690 | 0.735 |
| test soft acc / Brier vs soft / score MAE | 0.495 / 0.059 / 0.253 | 0.463 / 0.099 / 0.359 | 0.491 / 0.063 / 0.262 |
| test ECE | 0.148 | 0.112 | 0.144 |
| calibration-row accuracy | 0.718 | 0.685 | 0.720 |

| Paired comparison (test 2,000 decisions) | b/c | exact McNemar p | Accuracy difference (argmax gold) | Case-cluster bootstrap 95% |
|---|---|---|---|---|
| V2(b) vs run 1 | 217/98 | 1.7e-11 | +0.059 | [+0.040, +0.081] |
| V2(b) vs run 2 | 118/96 | 0.1510 | +0.011 | [−0.003, +0.025] |
| run 1 vs run 2 | 117/214 | 1.1e-07 | −0.049 | [−0.069, −0.028] |

b is the number of decisions only the first run gets right and c the number only the second run gets right; the difference is first run − second run. The cluster bootstrap resampled the 400 cases with replacement (10,000 resamples, seed 13).

The test accuracies of the three runs are 0.747 / 0.690 / 0.735. V2(b) and run 2 are indistinguishable (p=0.1510), and only main training run 1 differs significantly from the other two. The 0.690 of run 1 is therefore the outlier among the three runs, and the T1 trained figures of §5.1\~§5.4 (run 1) may underestimate T1's training effect. Run 2's T1 scored 103/120 = 0.858 on the Jev items (b/c 11/12 against Jev's 104/120, p=1.0000) and 0.735 on ext (+0.371 over vanilla).

The micro-batch losses of V2(b) and run 1 are identical to the fifth decimal place for micro-batches 0\~11, so the data order, initial weights, and RLCD noise are the same. The losses first diverge at micro-batch 12 (1.20023 vs 1.20035), and the mean absolute difference grows to 0.0823 over the epoch 2 span (micro-batches 625\~1249). The cause is that MPS training is not bitwise deterministic; which operation is nondeterministic was not identified. Evaluation is deterministic (vanilla bit-reproduced 28/28), so re-evaluating a preserved checkpoint gives the same figures, but retraining produces a different model.

The per-task results of run 2 with the changed seed and the confirmation of verdicts across the two runs are in §5.7.

### 5.7 Replicate run and verdict confirmation (two runs)

Run 2 is a replicate run with the same settings as the main training run except that only the torch seed is changed to 14 (`results/T3arm/rep_s14/<task>/`, owner decision item 4). The data order is the same; the seed changes dropout and the RLCD noise. Run 2 completed all 10 tasks. T9 stalled because of resource contention with another project's experiments and was stopped once; a watcher reran T9·T10 when there was no contention, finishing at 2026-10-09 00:23 (§7.7, the last two sections of `results/T3arm/PREP_20261008.md`). A verdict is confirmed only when the post-Holm conclusions of the two runs agree. The Holm family of run 2 is the same 10 tasks as that of run 1. Vanilla, Jev, and vanilla + task T involve no training and are therefore the same in both runs (3-arm synthesis §7).

| Task (category) | Jev-item accuracy: run 1 / run 2 / mean | ext accuracy: run 1 / run 2 / mean | ext run 1 vs run 2: b/c, p | Selected epoch: run 1 / run 2 |
|---|---|---|---|---|
| T1 typed-decisions (held-out) | 0.792 / 0.858 / 0.825 | 0.686 / 0.735 / 0.711 | 117/214, 1.1e-07; cluster bootstrap −0.049 [−0.069, −0.028] | 2 / 2 |
| T2 AG News (in-mix) | 0.950 / 0.975 / 0.962 | 0.946 / 0.942 / 0.944 | 12/10, 0.8318 | 2 / 1 |
| T3 DAIR Emotion (held-out) | 0.950 / 0.925 / 0.938 | 0.886 / 0.886 / 0.886 | 11/11, 1.0000 | 2 / 2 |
| T4 Banking77-10 (held-out) | 0.950 / 0.925 / 0.938 | 0.964 / 0.962 / 0.963 | 9/8, 1.0000 | 2 / 2 |
| T5 BoolQ (in-mix) | 0.775 / 0.700 / 0.738 | 0.832 / 0.838 / 0.835 | 21/24, 0.7660 | 2 / 2 |
| T6 SST-5 (held-out) | 0.675 / 0.725 / 0.700 | 0.590 / 0.578 / 0.584 | 38/32, 0.5504 | 2 / 2 |
| T7 MASSIVE intent-10 (held-out) | 0.910 / 0.870 / 0.890 | 0.878 / 0.882 / 0.880 | 16/18, 0.8642; cluster bootstrap −0.004 [−0.032, +0.024] | 2 / 2 |
| T8 prompt-injections (held-out) | 0.975 / 1.000 / 0.988 | 0.966 / 0.957 / 0.961 | 2/1, 1.0000 | 1 / 2 |
| T9 Enron spam (in-mix) | 0.975 / 0.975 / 0.975 | 0.988 / 0.988 / 0.988 | 2/2, 1.0000 | 1 / 2 |
| T10 support tickets (in-mix) | 0.300 / 0.425 / 0.362 | 0.332 / 0.340 / 0.336 | 33/37, 0.7202 | 2 / 2 |

Source: 3-arm synthesis §7.1. Accuracies are those of trained, and the mean is the simple mean of the two runs. b is the number of ext items only run 1 gets right and c the number only run 2 gets right. For T1 and T7, the cluster bootstrap (10,000 resamples) of the run 1 − run 2 accuracy difference is also given.

| Task | Jev items trained vs Jev | Jev items trained vs vanilla | ext trained vs vanilla |
|---|---|---|---|
| T1 | confirmed: n.s. | confirmed: trained better | confirmed: trained better |
| T2 | confirmed: n.s. | confirmed: n.s. | confirmed: n.s. |
| T3 | confirmed: n.s. | confirmed: n.s. | confirmed: trained better |
| T4 | confirmed: n.s. | inconsistent: trained better → n.s. | confirmed: trained better |
| T5 | confirmed: n.s. | confirmed: n.s. | confirmed: n.s. |
| T6 | confirmed: n.s. | confirmed: n.s. | confirmed: trained better |
| T7 | confirmed: n.s. | confirmed: trained better | confirmed: trained better |
| T8 | inconsistent: n.s. → trained better | inconsistent: n.s. → trained better | confirmed: trained better |
| T9 | confirmed: n.s. | confirmed: n.s. | confirmed: n.s. |
| T10 | confirmed: n.s. | confirmed: n.s. | confirmed: trained better |

Source: 3-arm synthesis §7.2. Verdicts are after Holm correction, and "trained better" means that trained is significantly better. Inconsistent cells show the run 1 → run 2 verdicts.

Of 30 comparisons (10 tasks x 3 kinds), 27 are confirmed and 3 inconsistent. All three inconsistencies are n=40 Jev-item comparisons with Holm p near 0.05. T4 trained vs vanilla is significant in run 1 (Holm p 0.0312) and not significant in run 2 (0.0547). T8 trained vs Jev (0.1934, 0.0391) and T8 trained vs vanilla (0.1504, 0.0312) are not significant in run 1 and significantly in favor of trained in run 2. When run 2 had finished only 8 tasks, T6 trained vs vanilla was inconsistent, but once the family became 10 tasks, run 2 also became not significant (0.0709) and the verdict was confirmed, while T4 became inconsistent instead. Jev-item verdicts near the boundary change with the run and the family size.

The conclusions confirmed across the two runs are as follows.

- **Against Jev**: in neither run is there a comparison in which Jev is significantly ahead of trained after Holm correction. Trained vs Jev on the 9 tasks other than T8 was confirmed as not significant in both runs. Before correction, T5 of run 2 favored Jev (b/c 1/10, p=0.0117); after Holm correction in the 10-task family it is 0.1055, not significant.
- **ext training effect**: on ext, the trained vs vanilla verdicts of the two runs agree on all 10 tasks. Trained's advantage on the 6 held-out tasks (T1, T3, T4, T6, T7, T8) and T10 is significant after Holm correction in both runs, and the in-mix tasks T2·T5·T9 are not significant in both runs. Apart from T1, the ext accuracies of the two runs differ by 0.012 or less, and apart from T1 all run 1 vs run 2 paired comparisons have p ≥ 0.55.
- **Jev-item training effect**: trained's advantage on T1·T7 and the non-significance on T2·T3·T5·T6·T9·T10 were confirmed. T4 and T8 are inconsistent.

| run | In-mix mean [95%] | In-mix tasks | Held-out mean [95%] | Held-out − in-mix (DiD) [95%] |
|---|---|---|---|---|
| run 1 (seed 13) | +0.017 [−0.003, +0.051] | T2·T5·T9·T10 | +0.252 [+0.171, +0.328] | +0.235 [+0.147, +0.316] |
| run 2 (seed 14) | +0.020 [−0.002, +0.058] | T2·T5·T9·T10 | +0.257 [+0.169, +0.340] | +0.238 [+0.144, +0.325] |

Source: 3-arm synthesis §7.3. The ext trained − vanilla was averaged by category in the same way as in §5.3. The task composition is the same in both runs (held-out tasks T1·T3·T4·T6·T7·T8). Run 2's in-mix +0.020, held-out +0.257, and DiD +0.238 are nearly the same as run 1's, and in both runs the DiD interval does not include 0.

The comparison of the three T1 runs (preparation V2(b), run 1, run 2) is in §5.6. Run 1 is the outlier, and run 2's T1 scored 0.858 on the Jev items, close to Jev (0.867).

### 5.8 Fine-tuning reference points (RQ5 of v2)

| Reference point (not zero-shot) | Task·sample | Laya | Jev | Comparison |
|---|---|---|---|---|
| Laya typed-decisions (fine-tuned on typed-decisions train) | T1, the same 120 decisions | 104/120 = 0.867 | 104/120 = 0.867 | b/c 10/10, p=1.0 |
| Laya ft-v1 (Korean domain_8 train, 11,094 rows) | Korean domain-routing pilot, 24 rows | 22/24 = 0.917 [0.742, 0.977] | 20/24 = 0.833 [0.641, 0.933] | b/c 0/2, p=0.5 |
| Laya ft-v1 | ko_massive_domain_8 test half, 250 rows | 0.900 [0.860, 0.936] (zero-shot 0.492) | not measured | - |

Source: `results/F/jev_cmp/summary.md` §3, `results/F/jev_playground_manual_20261006.md`, `results/P4/metrics/full_20261003-1156_summary.md`. Both fine-tuning lines are in-domain results that use training data from the same distribution, so their conditions differ from Jev's, which answers without training data. Training ft-v1 took 3 epochs, 2,150 s (35.8 minutes), on M4 Pro MPS (`results/REPORT.md` §4). The 2 pilot rows on which Jev lost to ft-v1 were due to the MASSIVE convention of grouping game-launch utterances of the `play` scenario under media. This convention is not in the label descriptions, and ft-v1 learned it from the training data (`results/F/jev_playground_manual_20261006.md` §4).

Compared with the 3-arm trained T1: on the same 120 decisions, the upstream typed-decisions checkpoint scores 104/120 and trained 95/120 (run 1) and 103/120 (run 2). On the 2,000 test decisions, upstream scores 0.766 vs run 1 0.690 and run 2 0.735 (§5.2, §5.6). Our budget is about 45% of upstream's (10,000 item-passes vs 22,400), the context is half as long (512 vs 1,024), and the precision is fp32 (upstream: fp16 autocast) (`results/T3arm/PREP_20261008.md` §4). Since three runs of the same pipeline spread over 0.690\~0.747, this difference contains both the budget difference and the run-to-run spread.

## 6. Case study: Korean domain-routing PoC

Before this comparison, the same project ran a PoC on whether Laya could be adopted as a Korean domain router (`results/REPORT.md`). This case is evidence for RQ5 and a reference from an operational perspective.

- **Zero-shot limit**: on `ko_massive_domain_8`, which groups the MASSIVE ko scenarios into 8 domains, multilingual zero-shot scored 0.492 on the test half. None of the 6 schema-wording variants (all −0.020\~−0.050 vs v1 on dev), temperature calibration, or threshold tuning got past the 0.6 line (`results/REPORT.md` §0, §2).
- **Fine-tuning**: ft-v1, trained on 11,094 rows of MASSIVE ko train (with option-order shuffle augmentation), scored 0.900 on the test half and 0.913 on the full test set of 2,917 rows, with ECE 0.053 and option-order flip 0.037. YNAT dev accuracy held (0.612 to 0.633), showing no forgetting (`results/REPORT.md` §4).
- **Go/No-Go**: of the 8 predefined gates (G0\~G7), zero-shot failed accuracy (G1), coverage (G2), and option order (G4). ft-v1 passed all 8 (G2 conditionally), and the verdict was "Conditional Go, premised on a fine-tuning pipeline" (`results/REPORT.md` §7).
- **Service**: the laya-serve-based router serving ft-v1 and its demo UI passed the acceptance checks 11/11, and the local HTTP round trip of a 1-question decision was p50 20.1 ms, p95 21.1 ms (`results/REPORT.md` §5).
- **Korean support audit**: Korean is one of Laya's evaluation languages (MASSIVE ko intent-20 multilingual 0.470, reproduced with Δ 0.000 against upstream's figure, `results/A/README.md`) and a high-resource language in mmBERT pretraining, but it is not documented in the decision training data. Tokenizer UNK is 0, and Korean takes 1.5 times as many tokens as English. Mixed text with a majority of Latin characters and Korean under 10 syllables are routed to english, so `lang="ko"` must be specified explicitly (`results/REPORT.md` §3, `docs/07_korean_support_audit.md` §1).

In this case, zero-shot Laya trailed Jev (pilot 0.417 vs 0.833, p=0.0020), whereas ft-v1, trained for about 36 minutes, was indistinguishable from Jev while numerically ahead (0.917 vs 0.833, p=0.5000) and kept the latency and cost advantages of local serving.

## 7. Discussion

### 7.1 Where Jev leads

In zero-shot, Jev's advantage was large on formats outside the training distribution and on instruction following: typed-decisions (T1), Banking77-10 with key-only labels (T4), BoolQ (T5), and multilingual intent (T7). On the 5-level sentiment scale (T6), the primary metric, argmax accuracy, is not significant, but the interval of the MAE difference excludes 0. Notably, on T5 the ranking quality itself differed even though it is a task in Laya's training mix (AUROC 0.988 vs 0.810). Split by training mix (§3.1), of the 4 significant leads, T1·T4·T7 are data that neither Laya checkpoint was trained on, and T1·T7, which remain after Holm correction, also belong to this group. Among the in-mix tasks, Jev led only on T5. On T7, Jev made the same decision when the language changed, whereas Laya's decisions split by language even for the same id. The differences can be interpreted as lying in the ability to exploit the meaning of label names, the alignment of multilingual representations, and calibration that uses the whole scale, but since Jev's internals are unknown, the causes are hypotheses.

This advantage is tied to the condition "right away, without labels". With training on task labels, neither run has a comparison in which Jev is significantly ahead after Holm correction (§5.1, §5.7). In run 1, Jev is numerically ahead on T1 (0.867 vs 0.792), T5 (0.925 vs 0.775), and T9 (1.000 vs 0.975). The T1 difference nearly vanished in replicate run 2, at 104/120 vs 103/120 (§5.6). On T5, run 2 dropped to 0.700, widening the gap into an uncorrected Jev advantage (b/c 1/10, p=0.0117; 0.1055 after Holm correction, n.s.). On T5, AUROC is also Jev 0.988 vs trained 0.831; on ext as well, AUROC is vanilla 0.913 vs trained 0.898, and the accuracy gain was −0.002. On BoolQ, which is in upstream's training mix, even 5,000 task labels did not raise Laya's ranking quality. On T1, Jev is also higher in soft acc against the teacher distribution (0.590 vs 0.515), but trained has the lower score MAE (0.254 vs 0.390).

### 7.2 Where they are similar in zero-shot

AG News (T2) leans toward Laya (b/c 0/4) but is not significant, and it is a task in Laya's training mix. Emotion (T3) is b/c 2/4. prompt-injections (T8) has equal accuracy but a different error structure: Jev missed 5 role- or task-instruction-style injections with p(true) 0.17\~0.40, while Laya english missed 5 explicit ignore/overwrite instructions, 4 of which were German sentences (`results/F/jev_cmp/sessions/S5_20261007/S5_summary.md` §4.3). These three are the only tasks on which Laya is equal or ahead; among them, T2 is in the training mix, and T3·T8 are held out.

T9·T10 of S7 are also not significant in zero-shot. On T9, Jev and all three Laya runners score 40/40, so this sample has no discriminative power. On T10, Jev 0.250, Laya english 0.300, and multilingual 0.450 are all low, and the gold-label quality is suspect (opening of §4, §5.1). The queue on which Laya led on T10 (Billing and Payments) was the one consistent with the dataset's convention of sending pricing inquiries to Billing (interpretation, `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md` §3.6).

### 7.3 Where trained catches up or surpasses

- **Surpasses**: T3 Emotion (0.950 vs 0.700) and T8 prompt-injections (0.975 vs 0.775) are significantly in favor of trained before correction in run 1. In run 2, T3 was again ahead before correction (b/c 11/2, p=0.0225), and T8 was ahead even after Holm correction (9/0, Holm 0.0391), but its verdict differs from run 1, so it remains inconsistent (§5.7). Both are tasks held out of Laya's training mix, and tasks on which vanilla was similar to Jev in zero-shot (0.750 vs 0.700, 0.775 vs 0.775). In both tasks the label boundaries depend on dataset-specific definitions (6 emotion classes, the injection criterion set by the dataset), so boundaries learned from task labels may have had an advantage over zero-shot answering from the label names alone. Since Jev's internals are unknown, the causes are hypotheses. On T8, all 9 of Jev's errors were misses (§4.1), and trained scores 39/40.
- **Catches up**: on T7, where Jev was ahead in zero-shot even after Holm correction, trained scores 91/100, the same as Jev, and is at 0.850 or above in all 5 languages (vanilla: de 0.400, ko 0.450). Training on 1,000 rows per language closed the multilingual alignment gap. T1 rose from 0.383 to 0.792, bringing the difference from Jev within the cluster bootstrap interval. T4 (0.950 vs 0.925) and T6 (0.675 vs 0.650, MAE 0.472 vs 0.432) are also at Jev's level.
- **Qualifications**: trained vs Jev is not significant on any task after Holm correction in run 1, and in run 2 only T8 favored trained; the Jev items have n=40 (T1 120 decisions, T7 100). Three T1 runs of the same pipeline spread over test 0.747 / 0.690 / 0.735 (§5.6). The verdict "surpasses" is used only when both runs favor trained after Holm correction, and no task in trained vs Jev meets that yet.

### 7.4 The retention ceiling of in-mix tasks

On the in-mix tasks, trained − vanilla was small (ext mean run 1 +0.017, run 2 +0.020). On T2 (0.940) and T9 (0.992), vanilla is already near the ceiling. On T5, vanilla remembers the train-split rows (dev 0.986, validation 0.834), so relearning labels from the same distribution did not raise validation. The training gain must therefore be read per category: averaging all 10 tasks together lets the small gains of the in-mix tasks dilute the training effect. Conversely, vanilla is not always strong on in-mix tasks. T10 is a task upstream marks as in the training mix, yet vanilla english is low at ext 0.264. Our ext is uniform across queues, whereas upstream Themes uses the natural distribution of the first 400 English rows, so the distributions differ, and vanilla english's predictions are skewed toward Technical Support. Multilingual is higher on ext, at 0.454, than the english base the Router picks (`results/T3arm/PREP_20261008.md` §5, "Anomalies / notes" item 14). Trained on T10 rose by +0.068 but only reached 0.332. On T10, all four systems are wrong on 18/40 Jev-item rows, so part of the low accuracy may be a gold-label problem (§5.1). The retention ceiling is thus the ceiling "when vanilla is already strong on an in-mix task", and vanilla's performance cannot be assumed from the in-mix label alone. Q1's Jev − vanilla DiD (+0.179 [−0.008, +0.356]) points the same way, but its interval includes 0. Even though S7 brought the number of in-mix tasks with Jev to four, T9 is near the ceiling for all three arms and T10 has suspect label quality. The information that separates retention from generalization in the in-mix category is therefore still concentrated in T2·T5.

### 7.5 Specialization cost

Trained Laya's accuracy was obtained with about 6,400 labels per task and 1.4\~43.3 minutes of training on a single M4 Pro. This cost recurs for every task. These 10 tasks took 57,444 labels, 194.8 minutes of training loop, and 10 checkpoints totaling 8.29 GB, and every added task again requires data construction, training, and checks equivalent to V1\~V6. Because each task has its own checkpoint, serving several tasks from one server requires swapping checkpoints in and out or loading them together. A single multitask model was not built within this scope (`docs/11_three_arm_plan.md` open question 8). Jev needs no labels or training, but it entails token billing (about $0.0197 per 1,000 decisions at the cited unit price, unit price to be verified) and sending data outside (§4.5). How many labels it takes to reach Jev was not measured this time (§8).

### 7.6 Laya's levers

- **Fine-tuning**: in neither run was there a comparison in which Jev was significantly ahead of per-task trained after Holm correction (before correction, one: T5 of run 2, §5.1, §5.7), and both reference points also closed the zero-shot gap (§5.8). This is consistent with upstream's own characterization (fast base to specialise).
- **Runner choice**: the difference between english and multilingual is large and changes direction across tasks (T5 0.725 vs 0.600, T7 ja 0.450 vs 0.800). Because the Router chooses by language only, assignments get mixed as on T7 de (multilingual 15, english 5), and accuracy stays at 0.350.
- **Option rendering**: on the same 40 T4 rows, merely changing the option rendering from `key: key spaced` to the key alone moved english from 0.825 to 0.725 (4 rows correct only with the old rendering, 0 rows correct only with the key alone, p=0.1250) and multilingual from 0.575 to 0.750 (0 rows / 7 rows, p=0.0156) (`results/F/jev_cmp/laya_summary.md` §4b). The comparison controlled for this by feeding the same strings to both systems, but in deployment the rendering also needs validation.
- **Operations**: local execution, latency, no token billing, determinism, no external data transfer.

### 7.7 Threats to validity

- **Playground ≠ API**: model version not shown, probabilities rounded to 2 decimal places, possible server-side wrapping, undisclosed definition of the displayed latency.
- **Small samples**: n=40 per task (Wilson half-width about ±0.15), and 20 per language for T7 (half-width about ±0.2). Differences smaller than about 0.2 are mostly indistinguishable. Trained vs Jev uses the same Jev items and has the same limitation. T10 has 4 rows per queue, so per-queue figures are directional signals. The narrow-interval ext is used only for vanilla vs trained.
- **Multiple comparisons**: in the zero-shot comparison, only T1·T7 are significant after Holm correction; the uncorrected 4/4/0 is an exploratory summary. Trained vs Jev is also not significant on all 10 tasks after Holm correction, and the uncorrected 2/8/0 is an exploratory summary.
- **Easy samples**: in the seed 13 sample, the interval of T3 Jev 0.700 does not include the third-party published 0.480, and Laya english 0.750 is also higher than upstream's 0.573. The samples are valid for paired comparison, but the results are not generalized to the published figures.
- **T1 teacher**: the gold label is the argmax of the teacher distribution, and the relationship between the teacher and Jev could not be confirmed. Jev's T1 0.867 is higher than the published 0.727 (2,000 decisions, different item composition), so a teacher-alignment effect cannot be ruled out.
- **Joint multi-question evaluation**: on T1, Jev evaluated the 2\~4 questions of a case together in one request, whereas Laya evaluated each question independently.
- **Training contamination**: by upstream's labeling, the only tasks among T1\~T8 in Laya's training mix are T2·T5, and T9·T10, added in the 3-arm extension, are also in-mix tasks. The remaining six tasks are held out (`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`, `third_party/laya/BENCHMARKS.md:142`, `:147`). This labeling is upstream's self-report, and the training data themselves were not checked. For the in-mix tasks, the overlap between upstream's training split and our evaluation items cannot be checked either (a limitation of V6).
- **Post hoc runner selection**: the per-task best Laya is a choice that favors Laya, and the pooled results with fixed runners point the same way (§4.2).
- **Input representation constraints**: because Boolean has no descriptions, Score takes 5 levels, and choice is limited to 80 characters, T1 compared only 120/200, and T4 was rebuilt with key-only rendering.
- **Pilot protocol differences**: the Korean pilot used the raw utterance as the state, its question text differs slightly from Laya's, and each option's key and description were entered as one string (Laya takes them separately). It was therefore excluded from the 8-task synthesis (`results/F/jev_playground_manual_20261006.md` §1.2, §5).
- **Trained is a sample of two runs**: retraining T1 with the same settings gave test 0.747 vs 0.690 (b/c 217/98, p=1.7e-11), and seed 14 run 2 gave 0.735. Of the three runs, main training run 1 is the outlier, so the run 1 figures for T1 may underestimate the training effect. The verdicts of the two runs agree on 27 of 30 comparisons and differ on 3 (all n=40 Jev items, Holm p near 0.05, §5.7). When run 2 had finished only 8 tasks, T6 was inconsistent, but in the 10-task family T6 was confirmed (n.s.) and T4 became inconsistent. Jev-item verdicts near the boundary change with the run and the family size. With two runs, the between-run variance cannot be estimated.
- **Resource contention during the replicate run**: run 2's T9 overlapped with 7 experiment processes of another project, and swap thrashing kept it from writing its first progress line for 38 minutes after the start (swap 32.0 / 32.8 GB, 11% free memory). Only the replicate-run queue was stopped, at 19:37. The watcher restarted T9·T10 at 2026-10-08 22:58, when its conditions were met (that experiment absent for 3 consecutive minutes, at least 30% free memory, at least 20 GB free disk), and they finished without contention at 2026-10-09 00:23 (first progress line of T9 after 209 seconds, vs 214 seconds in run 1). The preceding tasks T6\~T8 also slowed down, but the computation does not depend on timing, so the T1\~T8 run 2 results are considered valid. The cost table uses the run 1 values (the last two sections of `results/T3arm/PREP_20261008.md`, `results/T3arm/rep_s14/autostart.log`).
- **MPS nondeterminism**: even with the same data order, initial weights, and RLCD noise, MPS training diverged after the third optimizer step. Which operation causes this was not identified (follow-up: once the GPU is free, run a short training with `torch.use_deterministic_algorithms(True, warn_only=True)` to collect the list of operations that raise warnings).
- **Jev's training data unknown**: the categories are defined with respect to Laya only. If Jev was trained on the same public datasets, Jev's "zero-shot" may in fact be retention.
- **Possible T10 split overlap**: T10 has only one public split, so our hash-split test share may have been in upstream's training data. This cannot be checked by design.
- **Calibration refit confound**: trained's temperature is refitted on the task calib, so the calibration difference trained − vanilla includes a refit effect (V1). Separated with the calibration-separation column, a large part of the ext ECE improvement was refit (§5.4). However, for T1·T8 the fitted temperature of the separation baseline was clipped to the load range [0.5, 5], so the refit effect of these two tasks may be underestimated.
- **Suspect T10 label quality**: on the 40 Jev-item rows, all four systems (Jev, vanilla english, vanilla multilingual, trained) are wrong on 18/40, and on Customer Service and Human Resources all four systems score 0/4. The judgment that in most errors the gold queue does not match the queue descriptions given in the question is an interpretation made from reading the tickets. Because the label quality is suspect, manual verification is needed, and until then T10 results are not read as routing ability (3-arm synthesis §1.6, `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md` §3.6).
- **Dev baseline contamination**: for the in-mix tasks whose dev was split off the train split (T2, T5, T9) and for T10, which has only one split, the epoch 0 dev is not a valid vanilla baseline. T5's training-failure flag and calibration degradation are examples. Epoch selection compares trained epochs with each other, so it is little affected.
- **V3 misses the strict criterion**: permuted 0.385 exceeded the strict criterion 0.346 by +0.039. It passed by owner verdict (difference criterion), but this is a deviation from the plan (§3.7).
- **Fixed hyperparameters and reduced budget**: the script defaults were used for all tasks, and the budget is about 45% of upstream's T1 training. T6's train − dev gap (+0.142) and T10's high flip (0.175) suggest room for per-task tuning.

### 7.8 Upstream defects and inconsistencies found during the study

These are the 7 items recorded in `results/REPORT.md` §8. (1) `laya.calibrate.records_from_labeled` lacks `@torch.no_grad()` and raises an exception on a real Agent. (2) `laya.evals.evaluate` calls `predict(..., model=)` and is incompatible with `Agent.predict`. (3) The output prefix of `hf download` in agent mode breaks the documented download command (`--quiet` needed). (4) The Korean 0.490 on the model card is a value from a different run (T4, n=300); the official table gives 0.470. (5) The README claim that "multilingual noul without criteria reads the state" did not hold in Korean or in its English translation. (6) The license tag of the MASSIVE HF mirror (apache-2.0) differs from the original repository (CC BY 4.0). (7) The 13 s MPS first call in the examples documentation took 0.1 s on this machine.

## 8. Conclusion and future work

Compared on the same inputs, Jev leads in accuracy and multilingual consistency when used right away without training. Jev was significantly ahead on 4 of the tasks T1\~T8 (2 after Holm correction) and indistinguishable on the other 4, and there was no task on which Laya was significantly ahead. In S7, T9 is at the ceiling for all systems and T10 is low for all, so both are not significant. When Laya is fine-tuned per task on task labels, this gap disappears. Across both runs, there is no comparison in which Jev is significantly ahead of trained after Holm correction (before correction, Jev was ahead on T5 of run 2, b/c 1/10, p=0.0117). Trained vs Jev was confirmed as not significant in both runs on the 9 tasks other than T8, and T8 is inconsistent, not significant in run 1 and in favor of trained in run 2. Of 30 comparisons, 27 are confirmed and 3 inconsistent, and all inconsistencies are n=40 Jev-item comparisons with Holm p near 0.05. The training gain concentrated on the tasks upstream did not train on (ext held-out category +0.252, in-mix category +0.017; run 2 +0.257 and +0.020). The ext gain on the 6 held-out tasks was significant in both runs, while on the in-mix tasks vanilla has already seen the distribution, so the ceiling on the gain is low. Calibration must be read separately from accuracy: much of trained's ECE improvement on ext came from merely refitting the temperature on the task calib, and the tasks on which it can be read as a training effect are T4·T8. The specialization cost is about 6,400 labels per task, 1.4\~43.3 minutes of training on an M4 Pro, and 0.68\~0.85 GB per checkpoint, and the training pipeline passed validations V1\~V6 (V3 on the difference criterion). However, three T1 runs of the same pipeline spread over 0.690\~0.747, so the run-to-run spread of the trained figures is not small. The selection criteria therefore become more concrete along the same axes as in v2. "Must a broad range of formats be handled immediately, without training data?" favors Jev, and "Can thousands of labels be built per task, and do latency, cost, and data boundaries matter?" favors trained Laya. Either way, the confidence thresholds must be refitted per task.

**Owner decisions (2026-10-08 15:25) and progress.** The main training run started with defaults (before the project owner's confirmation) (§3.6). The project owner then decided five items (`results/T3arm/PREP_20261008.md`, "Owner decision" section).

- Confirmed: V3 passes on the difference criterion. The strict-criterion miss stays on record as a deviation from the plan (§3.7).
- Confirmed: T8 keeps its hold-out (dev 60 + calib 40 + train 444) and is trained for 2 epochs. The figures in this version use that setting.
- Done: the calibration-separation column (vanilla + task temperature, `results/T3arm/calib_sep/`). The results are in §5.4. The reading of the ECE improvement as a training effect is limited to T4·T8 (and part of T7).
- Done: the Jev measurement of T9·T10 (80 requests, session S7, `results/F/jev_cmp/sessions/S7_20261008/`). The results are in the opening of §4 and in §5.1. The Q1 DiD is +0.179 [−0.008, +0.356], and no verdict is drawn yet.
- Done: the replicate training, 1 run (seed 14, 10 tasks, `results/T3arm/rep_s14/`). 27 of 30 comparisons were confirmed with the same verdict in both runs, and 3 are inconsistent (§5.7). On T1, main training run 1 turned out to be the outlier. T9 was stopped once because of resource contention and rerun when there was no contention (§7.7).

Future work is as follows. (1) Re-measurement with the same protocol and larger samples through Jev's official API, and a cost comparison based on a confirmed unit price; which is better on Korean routing, Jev or ft-v1, can be decided only with a paired comparison at the scale of 500 rows (`results/REPORT.md` §8). (2) More languages and task formats (formats not run, such as negation, high cardinality, and long text). (3) Adding an LLM zero-shot baseline. (4) Quantifying how many labels it takes to reach Jev with per-task label-count curves (500 / 2,000 / 5,000 labels per task) (`docs/11_three_arm_plan.md` open question 7). (5) Establishing the identity of the T1 teacher and its relationship with Jev. (6) Identifying the nondeterministic operations in MPS training and securing a deterministic training path. (7) Reproducing T1 0.766 with an upstream-level budget (about 22,400 item-passes, context 1,024) (open question 5 of the same document). (8) Manual inspection of the T10 gold labels and checking how the queue labels were generated (in S7, 18/40 rows on which all four systems were wrong).

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
17. V. Metsis, I. Androutsopoulos, G. Paliouras. Spam Filtering with Naive Bayes – Which Naive Bayes? CEAS 2006 (Enron-Spam). HF `SetFit/enron_spam` (relationship to the original corpus to be verified).
18. Tobi-Bueck, *customer-support-tickets* dataset. Hugging Face Hub, revision ddf1c81. Bibliographic details and license to be verified.

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

The 3-arm extension is reproduced in the following order. The full commands for preparation and training validation (S0·S1) are listed in execution order in the "Commands" section of `results/T3arm/PREP_20261008.md`.

```bash
source env.sh
# S2 main training run (MPS GPU, about 4 hours). The start gate is the sha256 in poc/finetune/READY_T3ARM
PREFLIGHT_ONLY=1 bash poc/finetune/run_all_tasks.sh   # gate check only (READY sha256, leftover checkpoints, vanilla reports, disk)
SMOKE=1 bash poc/finetune/run_all_tasks.sh            # all stages for 10 tasks, 64 items x 1 epoch per task, temporary directory
bash poc/finetune/run_all_tasks.sh                    # T1-T10 training, epoch selection, Jev-item and ext evaluation, diagnostics, cleanup
# S3 synthesis (no model loading; reads reports and logs only)
nice -n 10 .venv/bin/python results/T3arm/t3arm_summary.py build --root results/T3arm --out results/T3arm
nice -n 10 .venv/bin/python results/T3arm/t3arm_summary.py verify --root results/T3arm --out results/T3arm
# Calibration-separation column (0-step export and evaluation, no training)
bash poc/finetune/t3arm_calib_sep.sh
# Replicate run 2 (seed 14, results in results/T3arm/rep_s14/)
env SEED=14 RUN_TAG=rep_s14 bash poc/finetune/run_all_tasks.sh
# Restart of T9·T10 in run 2 (run by the watcher poc/finetune/autostart_rep_t9t10.sh at 2026-10-08 22:58)
SEED=14 RUN_TAG=rep_s14 TASKS="T9 T10" bash poc/finetune/run_all_tasks.sh
# S7 Jev session analysis (no site requests; reads the records only)
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S7 T9_enron_spam_40
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S7 T10_support_tickets_queue_40
```

The results of S2 accumulate in `results/T3arm/<task>/` and `results/T3arm/run_all_status.log`, and the selected checkpoints remain in `poc/finetune/ckpt_t3arm/<task>/` (not included in the public repository). MPS training is not bitwise deterministic, so rerunning S2 yields different trained models (§5.6). Evaluation of the preserved checkpoints and S3 are deterministic.

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

The Jev requests of the 3-arm extension (2026-10-08) are the 80 requests of session S7 (T9 40 + T10 40), all of which returned HTTP 200. There were 0 cases of 5xx, 429, limit messages, captchas, or retries; request body = form payload 80/80, and Model ID `typesafe-ai/jev` 80/80. The cumulative site total is 518 (438 + 80), and the master log has 491 lines (`results/F/jev_cmp/sessions/S7_20261008/S7_run_card.md`).

## Appendix D. Relation to document 08

`docs/08_paper_ko.md` is an earlier report from the same project; it posed the question "Can Laya be used for a Korean service?" and covered Korean applicability (reproduction, Korean support audit, zero-shot quality, fine-tuning, PoC). Its Jev comparison was a single Korean pilot with n=24 (08 §4.8). For the question of comparing the performance of Laya and Jev, this document supersedes 08, and the Korean results of 08 are summarized and included as the case study in §6 of this document.

**English** | [한국어](10_paper_laya_vs_jev.ko.md)
