# Laya benchmark and PoC results report

Written 2026-10-03; the controlled Laya vs Jev comparison (§0a) added 2026-10-07. Subject: NandhaKishorM/laya 0.3.23 (upstream commit 4aa6761, checkpoint bundle 55cf4c4). All numbers are taken from files under `results/`, and each table gives its path. The source of the hypothesis verdicts is `results/verdicts.json` and that of Go/No-Go is `results/go_no_go.json`; this document transcribes the two. The source of the Laya vs Jev numbers is `results/F/jev_cmp/summary.json` (human-readable `summary.md`). Dashboard: `results/dashboard/index.html`.

## 0. Summary

1. **Laya vs Jev (main result, §0a)**: 8 tasks (T1\~T8) were compared with the same state, question and option strings. Zero-shot, Jev is more accurate than Laya (of the 8 tasks, Laya significantly better on 0, Jev significantly better on 2 after Holm), and the gap is especially large on instruction-style and multilingual tasks. Laya is competitive in local execution, latency and cost, and in that fine-tuning can close the gap. The 8-task macro accuracy is Jev 0.828 vs Laya Router 0.661, and on T1 the typed-decisions fine-tuned checkpoint scores 104/120, equal to Jev (`results/F/jev_cmp/summary.md`).
2. **Laya vs Jev operations**: Jev's displayed playground latency has a median of 226 ms (browser POST 465 ms, including the internet round trip), while Laya locally takes 13.8\~86.6 ms in-process and 20.1\~50.7 ms over localhost HTTP for 1 question. The deployments differ, so this is not a comparison of model speed. Jev costs $0.0197 per 1,000 decisions (unit price quoted from a 3rd party, to be verified), and Laya has no token charges.
3. **Korean PoC case study, quality**: Korean zero-shot is not usable. 8-domain routing 0.492 (test half), 7-topic 0.655, CS triage 0.40\~0.50, and none of schema wording, calibration or thresholds got past the 0.6 line. In contrast, ft-v1, fine-tuned for 36 minutes on 11,094 rows of MASSIVE ko train, reaches **0.900** on the same test half (0.913 on the full test of 2,917 rows), ECE 0.053, option-order flip 0.037.
4. **Korean PoC case study, speed and operations**: multilingual 3-question in-process p95 is 22.6 ms on MPS and 57.8 ms on CPU with 10 threads, and laya-serve has p95 79.4 ms at 10 RPS on MPS. The server processes inference serially, so per-process throughput is capped at about 22.6 RPS for 3 questions on MPS and 10 RPS on CPU. ONNX int8 is 1.74× slower than torch on this Apple silicon and changes 7% of decisions.
5. **Korean PoC case study, verdict**: **Conditional Go (premised on a fine-tuning pipeline)**. Zero-shot is No-Go, failing G1/G2/G4; the fine-tuned ft-v1 passes all of G0\~G7. The key evidence is `ko_massive_domain_8` test half 0.492 → 0.900 (`results/P4/metrics/full_20261003-1156_summary.md`).
6. **Korean pilot against Jev (n=24, manual, 2026-10-06)**: Jev is clearly ahead of Laya zero-shot (0.833 vs 0.417, p=0.002) and indistinguishable from the fine-tuned ft-v1 (0.917, p=0.5). Latency: hosted Jev displayed value 249.5 ms vs local ft-v1 round trip 20.1 ms (`results/F/jev_playground_manual_20261006.md`).
7. **3-arm comparison (§0b)**: Laya fine-tuned on task labels (about 6,400 per task) has no task on the Jev items where it is significantly below Jev after Holm, in either run (seed 13·14), and the gaps on T1·T7, where Jev led zero-shot, have also disappeared. The training gain concentrates on tasks upstream did not train on (ext trained − vanilla: in-mix category +0.017, held-out category +0.252). Only verdicts on which both runs agree are confirmed: 27 of 30 are confirmed and 3 (T4·T8 Jev items) are inconsistent (`results/T3arm/summary.md` §7).

## 0a. Laya vs Jev comparison (main result)

The source is `results/F/jev_cmp/summary.md` and `summary.json` (S6, 2026-10-07), and all numbers in this section are transcribed from there. The plan and the per-session results are in `docs/09_laya_vs_jev_plan.md` §7\~§10, and the raw records in `results/F/jev_cmp/sessions/` and the master request log `results/F/jev_cmp/jev_runs_all.jsonl` (411 lines; the raw records and the master log are not included in the public repository). The "Laya vs Jev (main result)" section of the dashboard `results/dashboard/index.html` reads the same JSON.

**Setup.** Both systems received the same state bytes (the JSON-serialized string Laya reads), the same question sentence, and the same option strings in the same order. The request body was byte-identical to the form payload for 411/411 requests. Jev was called at human pace through `POST /api/evaluate` of the independent 3rd-party playground jevplayground.com (Model ID `typesafe-ai/jev`, version not shown, probabilities rounded to the second decimal place). Laya ran 0.3.23 zero-shot english, multilingual and Router on CPU fp32. The tasks are T1\~T8 with n=40 per task. T1 is 120 comparable decisions from 40 cases, and T7 is 100 rows: the same 20 ids × 5 languages. Site requests numbered 438 over 2026-10-06\~07 (411 in the master log + 27 before the tooling), with 2 HTTP 502 responses and 0 429 responses. The main verdict compares, per task, Jev with that task's best zero-shot Laya runner using the exact McNemar test (two-sided, α 0.05), with Holm correction over the 8 tests.

**Verdict.** Zero-shot, Jev is more accurate than Laya (of the 8 tasks, Laya significantly better on 0, Jev significantly better on 2 after Holm), and the gap is especially large on instruction-style and multilingual tasks. Laya is competitive in local execution, latency and cost, and in that fine-tuning can close the gap.

| Task | n | Jev [Wilson 95%] | Laya english / multilingual / Router | vs best Laya b/c, p (Holm p) | Verdict (after Holm) |
|---|---|---|---|---|---|
| T1 typed-decisions | 120 (40 cases) | 0.867 [0.794, 0.916] | 0.383 / 0.367 / 0.383 | english 66/8, 1.8e-12 (1.4e-11) | Jev significantly better (Jev significantly better) |
| T2 AG News | 40 | 0.875 [0.739, 0.945] | 0.975 / 0.925 / 0.975 | english 0/4, 0.1250 (0.3750) | n.s. (n.s.) |
| T3 DAIR Emotion | 40 | 0.700 [0.546, 0.819] | 0.750 / 0.625 / 0.750 | english 2/4, 0.6875 (1.0000) | n.s. (n.s.) |
| T4 Banking77-10 | 40 | 0.925 [0.801, 0.974] | 0.725 / 0.750 / 0.725 | multilingual 8/1, 0.0391 (0.1953) | Jev significantly better (n.s.) |
| T5 BoolQ | 40 | 0.925 [0.801, 0.974] | 0.725 / 0.600 / 0.725 | english 9/1, 0.0215 (0.1289) | Jev significantly better (n.s.) |
| T6 SST-5 | 40 | 0.650 [0.495, 0.779] | 0.425 / 0.325 / 0.425 | english 15/6, 0.0784 (0.3134) | n.s. (n.s.) |
| T7 MASSIVE intent-10 × 5 languages | 100 (20 ids) | 0.910 [0.838, 0.952] | 0.410 / 0.620 / 0.580 | multilingual 36/7, 9.0e-06 (6.3e-05) | Jev significantly better (Jev significantly better) |
| T8 prompt-injections | 40 | 0.775 [0.625, 0.877] | 0.775 / 0.575 / 0.725 | english 5/5, 1.0000 (1.0000) | n.s. (n.s.) |

b is the number of items only Jev got right, and c the number only Laya got right. By upstream's labeling, the only tasks in Laya's training mix are T2·T5 (retention), and the other six tasks are held out. T4 Banking77 is held out, and neither checkpoint was trained on T1 typed-decisions or T7 MASSIVE (`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`, `summary.md` §2.1; `third_party/` is not included in the public repository, recreate it by cloning https://github.com/NandhaKishorM/laya at commit 4aa6761). So of the 4 tasks where Jev is significantly better, T1·T4·T7 are data neither checkpoint was trained on (including T1·T7, which remain after Holm), and only T5 is a training-mix task. The tasks where Laya is equal or ahead are T2, in the training mix, and T3·T8, held out.

- **Verdict tally** (Jev significantly better / n.s. / Laya significantly better): 4 / 4 / 0 before correction, 2 / 6 / 0 after Holm correction. After Holm, only T1 and T7 are significant.
- **macro accuracy**: Jev 0.828, Laya english 0.646, multilingual 0.598, Router 0.661. In an 8-task bootstrap (10,000 resamples), Jev − Router is +0.167 [+0.044, +0.293] and Jev − per-task best Laya is +0.153 [+0.031, +0.281]. These are descriptive statistics over 8 heterogeneous tasks. Without T1, Jev is 0.823 and the best Laya 0.717.
- **Pooled over the 240 independent single questions** (T2·T3·T4·T5·T6·T8): Jev 194, per-task best Laya 176, b/c 39/21, exact McNemar p=0.0273. With a fixed runner: english p=0.0204, multilingual p=9.7e-07, Router p=0.0111.
- **Cluster bootstrap** (10,000 resamples): T1 (case clusters) Jev − english +0.483 [+0.371, +0.597], T7 (id clusters) Jev − multilingual +0.290 [+0.100, +0.470].
- **Per-task features**: T5 differs not only in accuracy but also in ranking quality (AUROC Jev 0.988 vs english 0.810, difference +0.177 [+0.043, +0.326]). On T6 the main metric is not significant, but the E[level] MAE is 0.432 vs 0.888 (difference −0.456 [−0.711, −0.207]). T8 has equal accuracy but a different error structure: Jev missed role-instruction injections, and Laya english missed German override sentences.

**Calibration and robustness.** The meaning of Jev's probabilities differs by question format. On single choice, 65% of the answers are shown as 100%, and 59% of the wrong answers have top ≥ 0.90. On Boolean, 0 answers are shown as 100%, and the right place for the threshold differs by task. Multi-question (T1) is underconfident: the mean top of 0.733 is below the accuracy of 0.867. The best Laya runners, grouped by format, are all overconfident. For either system, thresholds must be fitted on per-task held-out samples before confidence can define the range of automatic handling. On resending the same payload (16\~23 minutes later), Jev gave the same labels 10/10 and the same probability vectors 9/10. On T7, the ids with the same label in all 5 languages are Jev 18/20, Laya english 0/20, multilingual 5/20, Router 4/20 (`summary.md` §5, §6).

**Latency and cost.** Jev's displayed value ('server + network') has a median of 226 ms, and the browser POST a median of 465 ms (410 requests). For 1 question, Laya takes 13.8\~86.6 ms in-process (by checkpoint and device), 20.1\~50.7 ms over localhost HTTP, and 49.2\~76.2 ms for intermittent calls at 1 s intervals. The deployments differ, so this is not a comparison of model speed. Jev uses a mean of 469.4 tokens per decision, which at the 3rd-party unit price of $0.042/1M tokens quoted in the upstream README is $0.0197 per 1,000 decisions (unit price to be verified). Laya has no token charges, only local compute (`summary.md` §7).

**Fine-tuning reference lines (not zero-shot).** On T1, the typed-decisions fine-tuned checkpoint scores 104/120 = 0.867, equal to Jev (b/c 10/10, p=1.0000). The Korean domain-routing ft-v1 scores 22/24 = 0.917 on the 24 pilot rows, at or above Jev's 20/24 = 0.833 (b/c 0/2, p=0.5000). Both lines are in-domain results trained on train data from the same distribution, which favors them in a comparison with zero-shot Jev (`summary.md` §3).

![Accuracy by task with Wilson 95% CI](F/jev_cmp/figs/accuracy_by_task.png)

![T7 accuracy by language](F/jev_cmp/figs/t7_languages.png)

![Latency by deployment (log axis)](F/jev_cmp/figs/latency.png)

**Caveats.**
- This goes through an independent playground, not the API. The model version is not shown, and probabilities are rounded to the second decimal place.
- With n=40 per task, the Wilson 95% half-width is about ±0.15, and T7 has n=20 per language. The pre-correction verdict tally 4 / 4 / 0 is read as an exploratory summary.
- The per-task best Laya runner is a post-hoc choice made after seeing the results, which favors Laya. With fixed runners the direction is the same.
- For T1, the relation between the teacher and Jev could not be checked, and Jev evaluated 2\~4 questions of a case together in one request. For T3, the seed 13 sample was easier than the one behind the published figures.
- Because of the playground input constraints (no description field for Boolean, Score fixed at 5 levels, choice 80 characters), only 120 of the 200 T1 decisions were compared, and T4 was rebuilt with key-only rendering (`docs/09_laya_vs_jev_plan.md` §2, `summary.md` §9).

## 0b. Three-arm comparison (3-arm): Jev vs vanilla Laya vs trained Laya

The source is `results/T3arm/summary.md` and `summary.json` (S3, rebuilt 2026-10-09 00:23; rebuilt 2026-10-12 for the public release with English figure text, release notes and the per-item Jev fields removed, numbers unchanged, `results/T3arm/summary.md:1`), and all numbers in this section are transcribed from there. The plan and a summary of the results are in `docs/11_three_arm_plan.md` (§9), the preparation and validation run card is `results/T3arm/PREP_20261008.md`, and the T9·T10 Jev session is `results/F/jev_cmp/sessions/S7_20261008/`. The "3-arm" section of the dashboard `results/dashboard/index.html` reads the same JSON.

**Setup.** For Jev, the T9·T10 80 requests of session S7 (2026-10-08) were added to the §0a records (T1-T8). On the Laya side, a calibration-separation column (vanilla + task T) was added to the two arms vanilla and trained. vanilla uses the base the Router picks (english for English tasks, multilingual for T7) without training, and vanilla + task T only adds a temperature fitted on the task's calib. trained fine-tunes the same base on the task labels, separately for each task (train up to 5,000 items × 2 epochs, MPS fp32, epoch selected on dev, temperature fitted on calib). So the trained comparison is a specialization comparison, not zero-shot. The tasks are the 8 of §0a plus T9 Enron spam and T10 customer-support ticket queue, both in Laya's training mix, 10 in total, and the categories are included in upstream's training mix (in-mix: T2·T5·T9·T10) or excluded from it (held-out: T1·T3·T4·T6·T7·T8). Evaluation has two layers: the Jev items (the same inputs as §0a, 40 per task, T1 120 decisions, T7 100 rows) and the extended set ext (mostly 500 per task, T1 2,000 decisions, T8 116). The main training run (S2) finished 2026-10-08 10:57-15:01 with 148 STEPs OK, FAILED 0 (`results/T3arm/run_all_status.log`).

**Verdict.** Laya trained on task labels shows no significant difference from Jev after Holm correction on all 10 tasks of the Jev items (based on run 1; in run 2, trained is significantly better on T8 only). Before correction, trained is significantly better on T3 (0.950 vs 0.700) and T8 (0.975 vs 0.775), and there is no task where Jev is significantly ahead. The gaps on T1·T7, where Jev was significantly better after Holm in the zero-shot comparison, disappeared after training (T7 0.910 vs 0.910, T1 0.792 vs 0.867, cluster bootstrap −0.075 [−0.185, +0.025]). The training gain concentrates on tasks upstream did not train on. trained below is run 1. Only verdicts on which the seed 14 replicate run (run 2) reaches the same conclusion were confirmed: 27 of 30 are confirmed and 3 are inconsistent (see "Replicate run" below).

| Task | Category | n | Jev [Wilson 95%] | vanilla [Wilson 95%] | trained [Wilson 95%] | trained vs Jev: b/c, p (Holm p) | trained vs vanilla: b/c, p (Holm p) | Verdict (after Holm): trained vs Jev / trained vs vanilla |
|---|---|---|---|---|---|---|---|---|
| T1 typed-decisions | held-out | 120 (40 cases) | 0.867 [0.794, 0.916] | 0.383 [0.301, 0.473] | 0.792 [0.711, 0.855] | 10/19, 0.1360 (0.9523) | 56/7, 1.4e-10 (1.4e-09) | n.s. (n.s.) / trained significantly better (trained significantly better) |
| T2 AG News | in-mix | 40 | 0.875 [0.739, 0.945] | 0.975 [0.871, 0.996] | 0.950 [0.835, 0.986] | 3/0, 0.2500 (1.0000) | 0/1, 1.0000 (1.0000) | n.s. (n.s.) / n.s. (n.s.) |
| T3 DAIR Emotion | held-out | 40 | 0.700 [0.546, 0.819] | 0.750 [0.598, 0.858] | 0.950 [0.835, 0.986] | 11/1, 0.0063 (0.0635) | 10/2, 0.0386 (0.2314) | trained significantly better (n.s.) / trained significantly better (n.s.) |
| T4 Banking77-10 | held-out | 40 | 0.925 [0.801, 0.974] | 0.725 [0.572, 0.839] | 0.950 [0.835, 0.986] | 3/2, 1.0000 (1.0000) | 9/0, 0.0039 (0.0312) | n.s. (n.s.) / trained significantly better (trained significantly better) |
| T5 BoolQ | in-mix | 40 | 0.925 [0.801, 0.974] | 0.725 [0.572, 0.839] | 0.775 [0.625, 0.877] | 2/8, 0.1094 (0.8750) | 2/0, 0.5000 (1.0000) | n.s. (n.s.) / n.s. (n.s.) |
| T6 SST-5 | held-out | 40 | 0.650 [0.495, 0.779] | 0.425 [0.285, 0.578] | 0.675 [0.520, 0.799] | 6/5, 1.0000 (1.0000) | 16/6, 0.0525 (0.2624) | n.s. (n.s.) / n.s. (n.s.) |
| T7 MASSIVE intent-10 | held-out | 100 (20 ids) | 0.910 [0.838, 0.952] | 0.620 [0.522, 0.709] | 0.910 [0.838, 0.952] | 7/7, 1.0000 (1.0000) | 32/3, 4.2e-07 (3.8e-06) | n.s. (n.s.) / trained significantly better (trained significantly better) |
| T8 prompt-injections | held-out | 40 | 0.775 [0.625, 0.877] | 0.775 [0.625, 0.877] | 0.975 [0.871, 0.996] | 9/1, 0.0215 (0.1934) | 9/1, 0.0215 (0.1504) | trained significantly better (n.s.) / trained significantly better (n.s.) |
| T9 Enron spam | in-mix | 40 | 1.000 [0.912, 1.000] | 1.000 [0.912, 1.000] | 0.975 [0.871, 0.996] | 0/1, 1.0000 (1.0000) | 0/1, 1.0000 (1.0000) | n.s. (n.s.) / n.s. (n.s.) |
| T10 support tickets | in-mix | 40 | 0.250 [0.142, 0.402] | 0.300 [0.181, 0.454] | 0.300 [0.181, 0.454] | 5/3, 0.7266 (1.0000) | 1/1, 1.0000 (1.0000) | n.s. (n.s.) / n.s. (n.s.) |

b is the number of items only the first arm got right, c the number only the second arm got right, and p is from the exact McNemar test (two-sided). Holm was applied separately per family (trained vs Jev 10 tasks, trained vs vanilla 10 tasks). With the Jev results for T9·T10 added, the trained vs Jev family grew from 8 to 10 tasks, and the post-Holm verdicts of T1-T8 did not change. For T1 (case) and T7 (id) the decisions are clustered, so item-level tests are optimistic (`summary.md` §1.1, §1.4).

**ext: vanilla vs trained.** The 6 held-out tasks all improve significantly after Holm, and among the in-mix tasks only T10 improves significantly (T2·T5·T9 n.s.).

| Task | Category | n | vanilla | trained | trained − vanilla [bootstrap 95%] | b/c, p (Holm p) | Verdict (after Holm) |
|---|---|---|---|---|---|---|---|
| T1 typed-decisions | held-out | 2,000 (400 cases) | 0.363 | 0.686 | +0.323 [+0.290, +0.355] | 818/172, 2.8e-101 (2.8e-100) | trained significantly better (trained significantly better) |
| T2 AG News | in-mix | 500 | 0.940 | 0.946 | +0.006 [−0.014, +0.026] | 14/11, 0.6900 (1.0000) | n.s. (n.s.) |
| T3 DAIR Emotion | held-out | 500 | 0.488 | 0.886 | +0.398 [+0.352, +0.446] | 209/10, 1.4e-49 (1.3e-48) | trained significantly better (trained significantly better) |
| T4 Banking77-10 | held-out | 500 | 0.876 | 0.964 | +0.088 [+0.062, +0.116] | 47/3, 3.7e-11 (2.2e-10) | trained significantly better (trained significantly better) |
| T5 BoolQ | in-mix | 500 | 0.834 | 0.832 | −0.002 [−0.024, +0.020] | 16/17, 1.0000 (1.0000) | n.s. (n.s.) |
| T6 SST-5 | held-out | 500 | 0.338 | 0.590 | +0.252 [+0.200, +0.304] | 172/46, 2.6e-18 (2.1e-17) | trained significantly better (trained significantly better) |
| T7 MASSIVE intent-10 | held-out | 500 (100 ids) | 0.692 | 0.878 | +0.186 [+0.124, +0.248] | 110/17, 7.4e-18 (5.2e-17) | trained significantly better (trained significantly better) |
| T8 prompt-injections | held-out | 116 | 0.698 | 0.966 | +0.267 [+0.181, +0.353] | 33/2, 3.7e-08 (1.8e-07) | trained significantly better (trained significantly better) |
| T9 Enron spam | in-mix | 500 | 0.992 | 0.988 | −0.004 [−0.012, +0.004] | 1/3, 0.6250 (1.0000) | n.s. (n.s.) |
| T10 support tickets | in-mix | 500 | 0.264 | 0.332 | +0.068 [+0.028, +0.106] | 68/34, 0.0010 (0.0039) | trained significantly better (trained significantly better) |

Differences and intervals are from a paired bootstrap on the same items (10,000 resamples), resampling cases as clusters for T1 and ids for T7. Holm was applied over the 10 tasks (`summary.md` §2.1).

**Category aggregates (Q1).** On ext, trained − vanilla is +0.017 for the in-mix category and +0.252 for the held-out category, and the difference-in-differences (DiD) is +0.235 [+0.147, +0.316]. The small gain on the in-mix tasks is consistent with a retention ceiling, since vanilla has already seen that data. The Q1 DiD on the Jev items (Jev − vanilla) is +0.179 [−0.008, +0.356]: the same direction, but the interval barely includes 0 (in-mix category T2·T5·T9·T10).

| Basis | Difference | in-mix mean [95%] | held-out mean [95%] | held-out − in-mix [95%] |
|---|---|---|---|---|
| Jev items | Jev − vanilla | +0.013 [−0.075, +0.138] | +0.191 [+0.054, +0.330] | +0.179 [−0.008, +0.356] |
| Jev items | trained − vanilla | +0.000 [−0.025, +0.031] | +0.262 [+0.212, +0.327] | +0.262 [+0.202, +0.333] |
| Jev items | trained − Jev | −0.013 [−0.100, +0.062] | +0.071 [−0.017, +0.163] | +0.083 [−0.035, +0.215] |
| ext | trained − vanilla | +0.017 [−0.003, +0.051] | +0.252 [+0.171, +0.328] | +0.235 [+0.147, +0.316] |

A category mean is the simple mean of the per-task accuracies, and its interval is the percentile interval from resampling tasks within the category (10,000 resamples). With 2-6 tasks per category, these are read as descriptive statistics (`summary.md` §3).

- **Cost (Q3)**: 6,400 labels per task (train 5,000 + calib 400 + dev 1,000; T1 6,000, T6 6,100, T8 544), M4 Pro MPS fp32 training loop 7.5-43.3 minutes per task (T8, with 444 items, 1.4 minutes), checkpoints english 0.85 GB, multilingual 0.68 GB. Jev and vanilla need no labels and no training (`summary.md` §5).
- **Training validation (Q4)**: V1·V2·V4·V5·V6 pass. V3 (label-shuffle) passes on the difference criterion per the owner's verdict (2026-10-08) (real labels epoch 1 0.864 − permuted 0.385 = +0.479 ≥ 0.30). It misses the strict criterion (permuted ≤ majority + 0.05 = 0.346) by +0.039, which was recorded as a deviation from the plan (`summary.md` §6.2, §6.3).
- **The 3 training-failure flags** (T5·T9·T10) are none of them pipeline failures. T5 is dev-baseline contamination (dev comes from the BoolQ train split, so vanilla dev 0.986 vs validation ext 0.834), T9 is a ceiling effect (a 1-row difference out of 1,000 dev rows), and T10 is a dev label-distribution mismatch (dev has the natural distribution, while train·ext are close to balanced) (`summary.md` §6.1, the "Found during the main training run" sections of `PREP_20261008.md`).
- **Calibration separation**: the answers of vanilla + task T are the same as vanilla's (correctness agrees on 6,736/6,736), so the accuracy comparison is unchanged and only Brier and ECE differ. On ext, for ECE the refit effect is larger than the training effect on T1·T2·T3·T6·T7·T10 (e.g., T3 −0.336 vs +0.002), while for Brier the training effect lowers it more on all 6 held-out tasks (e.g., T8 −0.087 vs −0.382). T5's worse calibration comes from the refit (ext ECE refit +0.055, training −0.010). For T1·T8 the fitted T is clipped to laya's load range (T1 choice 7.613 → 5.000, noul 10.000 → 5.000, T8 noul 10.000 → 5.000) (`summary.md` §4.3).
- **T9·T10 Jev (S7)**: on T9, Jev and vanilla both score 40/40. On T10, Jev 0.250 and vanilla english 0.300, n.s. (b/c 3/5, p=0.7266). On T10, all four systems (Jev, vanilla english, vanilla multilingual, trained) are wrong on 18/40 rows, so the label quality is suspect and needs a manual check (`summary.md` §1.1, §1.6).

**Replicate run (seed 14).** run 2 used the same settings as the main training run with only the torch seed changed to 14, and all 10 tasks finished. Of the 30 verdicts (10 tasks × 3 comparisons), 27 are confirmed and 3 inconsistent. The inconsistent ones are T4 Jev items trained vs vanilla (run 1 significant 0.0312, run 2 n.s. 0.0547), T8 Jev items trained vs Jev (run 1 n.s. 0.1934, run 2 trained significantly better 0.0391) and T8 Jev items trained vs vanilla (run 1 n.s. 0.1504, run 2 significant 0.0312); all are n=40 Jev-item comparisons with a Holm p near 0.05. ext trained vs vanilla is confirmed on all 10 tasks, and run 2's ext DiD, +0.238 [+0.144, +0.325], is almost the same as run 1's (+0.235). In run 2, before correction, Jev was significantly better on T5 (b/c 1/10, p=0.0117, n.s. after Holm) (§8, `summary.md` §7).

| Task | Category | Jev-item accuracy: run 1 / run 2 | ext accuracy: run 1 / run 2 | ext run 1 vs run 2: b/c, p | Decision agreement: trained vs Jev / trained vs vanilla / ext |
|---|---|---|---|---|---|
| T1 typed-decisions | held-out | 0.792 / 0.858 | 0.686 / 0.735 | 117/214, 1.1e-07 | confirmed / confirmed / confirmed |
| T2 AG News | in-mix | 0.950 / 0.975 | 0.946 / 0.942 | 12/10, 0.8318 | confirmed / confirmed / confirmed |
| T3 DAIR Emotion | held-out | 0.950 / 0.925 | 0.886 / 0.886 | 11/11, 1.0000 | confirmed / confirmed / confirmed |
| T4 Banking77-10 | held-out | 0.950 / 0.925 | 0.964 / 0.962 | 9/8, 1.0000 | confirmed / inconsistent / confirmed |
| T5 BoolQ | in-mix | 0.775 / 0.700 | 0.832 / 0.838 | 21/24, 0.7660 | confirmed / confirmed / confirmed |
| T6 SST-5 | held-out | 0.675 / 0.725 | 0.590 / 0.578 | 38/32, 0.5504 | confirmed / confirmed / confirmed |
| T7 MASSIVE intent-10 | held-out | 0.910 / 0.870 | 0.878 / 0.882 | 16/18, 0.8642 | confirmed / confirmed / confirmed |
| T8 prompt-injections | held-out | 0.975 / 1.000 | 0.966 / 0.957 | 2/1, 1.0000 | inconsistent / inconsistent / confirmed |
| T9 Enron spam | in-mix | 0.975 / 0.975 | 0.988 / 0.988 | 2/2, 1.0000 | confirmed / confirmed / confirmed |
| T10 support tickets | in-mix | 0.300 / 0.425 | 0.332 / 0.340 | 33/37, 0.7202 | confirmed / confirmed / confirmed |

![3-arm accuracy by task (Jev items)](T3arm/figs/accuracy_3arm.png)

![ext: trained − vanilla](T3arm/figs/ext_trained_minus_vanilla.png)

**Caveats.**
- trained is one training run per task. Retraining T1 with the same settings gave diverging results: test 0.747 vs 0.690 (against label), paired b/c 217/98, p=1.7e-11 (MPS nondeterminism, §8). Differences smaller than this spread can flip depending on the run. The results of the seed 14 replicate run are in "Replicate run" above, and on T1 the main training run is the lowest of the three runs (V2(b) 0.747, run 1 0.690, run 2 0.735, `summary.md` §7.4).
- The raw comparison of calibration metrics (trained − vanilla) mixes in the temperature refit effect (V1: refit alone, without training, takes ECE english 0.083 → 0.064, multilingual 0.365 → 0.179). The training effect is read from the training column of the calibration separation (`summary.md` §4.3).
- The Jev items have n=40 per task, so small trained vs Jev differences cannot be judged. No significant difference after Holm does not mean equivalence.
- Diagnostics to watch: T10 has a high option-order flip of 0.175, and T6 a large train − dev gap of 0.142 (`summary.md` §6.1).

## 1. Environment

- Machine: Apple M4 Pro (10P+4E CPU, 20-core GPU/MPS), 48 GB, macOS 26.6.2. Python 3.12.12, laya 0.3.23, torch 2.14.1, transformers 5.18.0, onnxruntime 1.30.0 (`results/env/env_20261002-1333.json`).
- Checkpoints: `convaiinnovations/laya` bundle @ `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` (english / multilingual / typed-decisions), upstream checkout `4aa6761`. Fine-tuning output `poc/finetune/ckpt_domain8_v1/` (run `full_20261003-1156`, not included in the public repository).
- Device roles: all quality numbers are CPU fp32; latency is measured on CPU (intra-op 10 / inter-op 1) and MPS. parity: P0 7 questions MPS fp16 vs CPU fp32 argmax 7/7, max |Δp| 0.0017 (`results/poc/P0_20261002.md`); Track D4 predict vs predict_batch flip 0 (`results/D/20261003-1314_batch.json`).
- Data: 19 files in `data/evals/` (`scripts/build_ko_evalsets.py`, `data/evals/MANIFEST.json`). The dev/test split is `results/B/B_splits.json` (row-index parity for the paired MASSIVE sets, odd/even of the state sha256 for the rest).

## 2. Results by track

### Track A reproduction (`results/A/README.md`, `results/korean_support/K2_analysis.md` E2)

| Set | Checkpoint | measured acc | upstream acc | Δ | ECE measured / upstream |
|---|---|---|---|---|---|
| ko intent-20 | multilingual | 0.470 | 0.470 (BENCHMARKS.md:71) | 0.000 | 0.3108 / 0.3108 |
| en intent-20 | multilingual | 0.710 | 0.710 | 0.000 | 0.2333 / 0.2333 |
| en intent-20 | english | 0.820 | 0.820 | 0.000 | 0.1383 / 0.1382 |
| ko intent-20 | english | 0.110 | 0.110 | 0.000 | 0.6804 / 0.6804 |

The 5 fixture metrics also match the docs/evals.md expected values to 4 digits (`results/env/smoke_fixture_english_cpu.json`). The harness path (laya-evals, per-row forward) and the upstream packed path gave the same values. A3 builder file identity passed (`results/B/summary_20261002.md` §9).

### Track B Korean quality (`results/B/summary_20261002.md`, `results/B/metrics/`, CPU fp32)

| Set | Options | majority | english | multilingual | typed-decisions | Router auto |
|---|---|---|---|---|---|---|
| ko_massive_domain_8 (all / dev / test) | 8 | 0.126 | 0.262 | 0.526 / 0.560 / **0.492** | 0.288 | 0.526 |
| ko_klue_ynat_7 (all / test) | 7 | 0.144 | 0.216 | 0.634 / 0.655 | 0.234 | 0.634 |
| ko_massive_scenario_18 (n=100) | 18 | 0.210 | 0.310 | 0.520 | 0.330 | 0.520 |
| ko_massive_intent_20opt (n=100) | 20 | 0.170 | 0.110 | 0.470 | measured (summary) | 0.470 |
| ko_klue_nli_3 | 3 | 0.334 | 0.448 | 0.750 | measured | same |
| ko_nsmc_sentiment choice / noul | 2 | 0.500 | 0.528 / 0.516 | 0.774 / 0.638 | measured | same |
| ko_kmhas_hate (noul) / type_8 | 2 / 8 | 0.500 / 0.144 | 0.500 / 0.146 | 0.582 / 0.394 | measured | same |
| ko_3i4k_speechact_7 | 7 | 0.144 | 0.174 | 0.178 | measured | same |
| en_massive_domain_8 (ko pair, multilingual) | 8 | 0.126 | 0.446 | 0.510 | | |

- Korean penalty: on the same 500 ids, ko 0.526 vs en 0.510 (McNemar p=0.47); with a schema of descriptive Korean explanations there is no penalty. With English key rendering (intent-20), ko→en +0.24 (p=1.2e-04).
- ablation (dev half, multilingual): Korean instructions Δ −0.020 / −0.004, English descriptions Δ −0.028 / +0.024, all n.s.
- Router auto sent 100% of the Hangul rows to multilingual (only the 4 rows without Hangul went to default).
- domain_8 error pattern: smart_home (gold 63, predicted 140) and general (62, 80) act as sinks. Checkpoint choice: fixed multilingual + `lang="ko"`.

### Track C robustness (`results/C/C1_option_order_20261002.md`, `results/C/C_schema_v2_20261002.md`, `results/P4/metrics/full_20261003-1156_option_order_dev.md`)

| Probe | Measurement | upstream reference |
|---|---|---|
| C1 option-order flip, router_v1 domain_8 (dev 250, 5 permutations) | zero-shot per permutation **0.270** [0.230, 0.310], any-flip 0.512; decisions with confidence ≥ 0.9 only 0.094 → **ft-v1 0.037**, any-flip 0.084 | massive_intent.en 0.150 / 0.230, Jev 0.13, zh CS 0.28 |
| C1 ynat_7 / scenario_18 (zero-shot) | 0.168 / 0.241 | |
| C2 schema v2, 6 variants (dev) | all −0.020\~−0.050 vs v1 0.560, none significant; removing `general` + replacing it with a gate rejected (AUROC 0.574); v1 probabilities summed into 5 classes 0.682 (contract change) | |
| Position bias | first option underpredicted (productivity 12 vs gold 30); the smart_home absorption is semantic → rejected | |
| C3 noul vs 2-choice (NSMC, Track B) | choice 0.774 vs noul 0.638 (p=6.5e-10, semantic keys) | |
| C4 negation, C6 high cardinality, C8 long text | not run | |

### Track D performance (`results/D/D_summary_20261003.md`, Apple M4 Pro, running alone)

| Configuration | p50 | p95 | Throughput | File |
|---|---|---|---|---|
| multilingual 3q in-process, MPS (short 59 tok) | 22.5 ms | 22.6 ms | | 20261003-1249_latency_matrix |
| multilingual 3q in-process, CPU 10 threads | 56.4 ms | 57.8 ms | | same |
| multilingual 1q / 10q, MPS vs CPU | 13.8 / 62.4 vs 37.7 / 121.4 ms | | CPU÷MPS 1q 2.73x | same |
| laya-serve MPS, open-loop 10 RPS, 3q | 63.5 ms | 79.4 ms (p99 85.1) | 503 0 | 20261003-1330_http_mps |
| laya-serve CPU, 10 RPS, 3q | 99.9 ms | 135.8 ms | | 20261003-1343_http_cpu |
| laya-serve closed-loop saturation | | | MPS 1q 50 / 3q 22.6 RPS, CPU 3q 10 RPS | same |
| predict_batch CPU n=256, bs 8 sort vs unsorted | | | 1.67x (1.39x vs loop), flip 0 | 20261003-1314_batch |
| cold load (warm cache) | multilingual 3.45\~3.67 s, english 2.82\~2.97 s | | | 20261003-1306_coldload |
| ONNX int8 vs torch CPU (ynat 500, batch 16) | 525.9 vs 302.2 ms | | acc 0.622 vs 0.634, ECE +0.0154 | 20261003-1347_*_ynat |
| Resident RSS, 1 / 2 / 3 checkpoints (CPU) | 2.07 / 3.63 / 5.23 GiB | | | 20261003-1307_rss_preload |

Additional observations: MPS fp16 autocast gain ≤ 8%; with intermittent calls (idle ≥ 100 ms) MPS slows down 2.2\~3.6×; intra-op 10 is optimal (14 is 2\~22% slower); checkpoint switching 0.13\~0.21 s (local paths).

### Track E calibration (`results/E/E_summary_20261002.md`, zero-shot multilingual; ft-v1 in `results/P4/metrics/full_20261003-1156_coverage_*.md`)

| Checkpoint | Bucket / T | ECE before → after (domain_8 test) | coverage @ error ≤ 5% | @ ≤ 10% |
|---|---|---|---|---|
| zero-shot, pooled refit | choice:6-10, T 1.9161 | 0.263 → 0.098 [0.081, 0.162] | 0.224 (upper bound a/(1−e) 0.518) | 0.308 |
| zero-shot, per-task refit | T 2.0245 | 0.263 → 0.123 | | |
| ft-v1 (the script's own calibration) | single T | 0.053 (2,917 rows 0.057) | test half, post-hoc T 0.756; 2,917 rows with dev T 0.907 applied 0.923 (error 0.042) | 1.000 |

Per-domain T rejected because it overfits dev. E6: NSMC noul AUROC test 0.822, dev Youden threshold 0.0073 → test accuracy 0.725 (0.641 at 0.5, 2-choice 0.773). The payload `poc/calibration/ko_v1.json` is for the zero-shot checkpoint only.

### Track F baselines

| Baseline | Set | Value | vs laya | Source |
|---|---|---|---|---|
| majority / random | domain_8 | 0.126 / 0.125 | zero-shot +0.40, ft-v1 +0.77 | `data/evals/MANIFEST.json` |
| majority / random | ynat_7 | 0.144 / 0.143 | +0.49 | same |
| majority / random | nli_3, nsmc, kmhas_hate, 3i4k | 0.334, 0.500, 0.500, 0.144 | +0.42, +0.27/+0.14, +0.08, +0.03 | same |
| Jev (3rd-party published, English) | AG News / Banking77 / Emotion | 0.910 / 0.870 / 0.480, p50 236\~276 ms, ECE 0.246, flip 0.13 | no Korean figures | BENCHMARKS.md §Headline, research/README.md |
| LLM zero-shot (claude-haiku-4-5) | | **not run** (no API key provided) → G1 uses the absolute criterion 0.80 | | |
| Jev (manual comparison pilot, Korean) | domain_8 test half, 24 rows | 0.833 (20/24), median displayed latency 249.5 ms | higher than zero-shot 0.417 (p=0.002), indistinguishable from ft-v1 0.917 (p=0.5) | `results/F/jev_playground_manual_20261006.md` |

#### Jev manual comparison pilot (public playground, n=24, 2026-10-06)

This section is a Korean pilot done before the controlled comparison. The main result, which compares 8 tasks under the same input rules, is in §0a.

`results/F/jev_playground_manual_20261006.md`, run card `results/F/F_jev_20261006.md`, raw records `results/F/jev_runs_raw.jsonl` (25 requests, not included in the public repository), sample `results/F/jev_sample_24.jsonl`, screenshots `results/F/jev_shots/` (not included in the public repository).

- Protocol: from the `ko_massive_domain_8` test half minus the 16 rows that overlap train (234 rows), 3 rows per domain were drawn with `random.Random(13)`, 24 rows in total. Jev was given the same information as Laya: the question "Which domain should handle this request?" and the 8 options in the same `key: Korean description` format as Laya's rendering, in the same order (`poc/schema/router_v1.json`). Run at manual pace on the public site https://jevplayground.com (25 requests in total, including 1 HTTP 502, gaps ≥ 21 s); pass 2 with English keys only was skipped. The Laya numbers were looked up for the same rows in the Track B·P4 reports, without rerunning.

| System | Correct | Accuracy | Wilson 95% |
|---|---|---|---|
| Jev (typesafe-ai/jev, playground) | 20/24 | 0.833 | [0.641, 0.933] |
| Laya zero-shot (multilingual) | 10/24 | 0.417 | [0.245, 0.612] |
| Laya ft-v1 (fine-tuned) | 22/24 | 0.917 | [0.742, 0.977] |

- Agreement and McNemar: Jev vs zero-shot, same label 10/24, b=10, c=0, p=0.002 (Jev also got every row zero-shot got right). Jev vs ft-v1, same label 20/24, b=0, c=2, p=0.5 (ft-v1 also got every row Jev got right). With ft-v1 at 22/24, p would be 0.5 even if Jev scored 24/24, so this sample cannot decide whether Jev is better or worse than ft-v1.
- Correct answers per domain (Jev / zero-shot / ft-v1, 3 rows each): productivity 3/0/3, media 1/0/3, smart_home 3/3/3, info_qa 3/0/3, communication 3/2/3, lifestyle 3/2/3, transport 3/3/3, general 1/0/1.
- Latency: median playground displayed value ("server + network") 249.5 ms (203\~570, within the 3rd-party published p50 range of 236\~276 ms), median POST measured in the browser 497.5 ms. Our local values are the P2 round trip p50 20.1 ms (`results/poc/P2_20261003.md`) and Track D in-process 13.8 ms (`results/D/D_summary_20261003.md`). The ratio (12\~36×) mixes the difference between a hosted service and local execution with the internet round trip, so it is not a comparison of the models' own speed.
- Calibration observation: Jev was not confident when it was wrong (top probability 41\~86% on the 4 wrong answers, mean 96.5% on correct ones). Cutting at 90% accepts 18/24 with 18/18 correct; ft-v1 at T 0.907 accepts 22 rows with 21/22 correct. The playground rounds probabilities to the second decimal place, so 14 of the 24 calls were shown as 100%.
- Hypothesis: 2 of Jev's 4 wrong answers are of the "게임 열어" ("open the game") type (gold media); our media description does not contain "게임" (game), so Jev got them wrong, while ft-v1 learned this rule from the training data (Jev's per-item outputs are omitted in the public repository). Whether adding "게임" to the description changes this was not tested.
- Caveats: n=24, single pass, the playground rather than the official API (model version not shown, Model ID `typesafe-ai/jev`, about 716 input / about 255 output tokens per call), options as a 1-field label (no description field), run only within the usage limits of a free 3rd-party site.
- **Pilot verdict: Jev is clearly ahead of Laya zero-shot (it handles Korean input too) and is indistinguishable from the fine-tuned ft-v1 on this sample (Jev 0.833 vs ft-v1 0.917, p=0.5).**

## 3. Preliminary experiments and Korean support audit (`results/poc/`, `results/korean_support/`, `docs/07_korean_support_audit.md`)

- P0 smoke: environment, parity and latency passed. In a 30-sentence self-labeled probe, CS triage intent 0.40, noul without criteria almost always "no" (confidence 0.9+), frustration level 0 chosen 0/30.
- P0b schema ablation, 8 variants: intent best 0.50 (English descriptions); for the 4 binary questions combined, no form beat the always-no baseline (93/120); 2-choice A/B collapsed to A; labels A/B had no effect.
- P0c topic-routing preview (n=100): YNAT 7 topics 0.65 (top-50% coverage 0.86), MASSIVE 18 domains 0.52.
- Korean support audit: Korean is high-resource in mmBERT pretraining (1.43%) and an evaluation language of laya (MASSIVE ko 0.470, 18th of 51), but it is undocumented in the RLCD training data; tokenizer UNK 0, fragmentation ≤ 0.2%, 1.5× the tokens of English, NFD input blows up 3.1× (NFC normalization needed); routing is correct for pure Hangul, while Latin-majority mixed sentences and Korean under 10 syllables go to english (`lang="ko"` must be set explicitly); the ko vs en penalty on the same sentences is 0.21\~0.24 with English key options and 0.10 with Korean descriptions (n.s.); the noul no-bias and the avoidance of score level 0 are the same with English input (a property of the checkpoint, noul AUROC 0.76\~0.92).

## 4. P4 fine-tuning (`results/P4/P4_probe_20261002.md`, `results/P4/metrics/full_20261003-1156_summary.md`, `results/P4/full_20261003-1156_driver.log`)

- Data: MASSIVE ko train 11,514 → 11,094 rows (duplicate and length filters), validation 2,033 → 2,012 rows, natural distribution over the 8 domains. Option-order shuffle augmentation on the training items (11,093/11,094 reordered), calibration on 400 validation rows.
- Settings: mb 8 × ga 4 (effective 32), 3 epochs (1,041 steps), fp32, gradient checkpointing off, MPS on an idle GPU. Training 2,150 s (35.8 minutes), evaluation about 10 minutes. MPS peak about 8 GB.
- Probe (1,000 rows, 1 epoch): test half 0.492 → 0.720.

| Evaluation | base multilingual | ft-v1 | deduplicated (excluding utterances identical to train) |
|---|---|---|---|
| domain_8 500 rows all / dev / test | 0.526 / 0.560 / 0.492 | 0.894 / 0.888 / **0.900** [0.860, 0.936] | test 0.893 (n=234) |
| domain_8 full test, 2,917 rows | 0.475 | **0.913** [0.902, 0.923] | 0.908 (n=2,762) |
| validation 2,012 rows (epoch 1 / 2 / 3) | 0.462 | 0.892 / 0.916 / 0.918 | 0.914 |
| ECE test / 2,917 | 0.263 / 0.253 | 0.053 / 0.057 | |
| YNAT dev 245 (forgetting check) | 0.612 | 0.633 | |
| option-order flip (dev 250, 5 permutations) | 0.270 | 0.037 (any-flip 0.084) | |
| coverage @ error ≤ 5% (test half / 2,917) | 0.224 | 0.756 (post-hoc T) / 0.923 (dev T 0.907) | |

The remaining confusion is general ↔ info_qa (on the 2,012 rows, general→info_qa 25, info_qa→general 20). Epoch 3 vs epoch 2 is n.s., so the final export (epoch 3) was adopted as v1.

## 5. P2 service and demo UI (`results/poc/P2_20261003.md`, `results/poc/P2_ui_check.md`)

The service with the ft-v1 checkpoint loaded and the Laya Playground passed the acceptance checks 11/11. `poc/service/app.py` (142 lines) builds `Router(models={"multilingual": "poc/finetune/ckpt_domain8_v1", "english": "models/laya"})`, injects it into `laya.serve.create_app(router)`, and adds `/poc/decide`, `/poc/shadow`, `/poc/meta` and a static `/poc/ui/`. The hooks are NFC normalization + masking of e-mail, phone and card numbers, shadow JSONL logging, and counters (`hooks.py`, 123 lines). The policy T is 0.907 (maximum coverage with error ≤ 5% on dev-1459 of the 2,917 rows; applied to test-1458, coverage 0.923 and error 0.042, `policy.py:4`).

| Check | Result |
|---|---|
| Authentication | no key or wrong key 401, valid key 200. `/health` is liveness only |
| `/poc/meta` cross-check | questions_sha256 a7f2f6b8…, rl_agent_config sha 3270d480…, weights sha b0609f54…, all matching the P4 report and MANIFEST |
| 8-domain examples + documentation example | 9/9 ROUTE, correct domain 9/9, p 0.924\~0.957, routing reason explicit lang='ko' |
| FALLBACK | meaningless string p 0.222, multiple intents p 0.669 → FALLBACK; `min_confidence` 1.0 → abstained |
| PII | only `[email]`·`[phone]`·`[card]` recorded in shadow, 0 raw values |
| General mode `/v1/systemone` | 3-option question 200, technical 0.985 |
| shadow counters | 50 = total, ROUTE 44 + FALLBACK 5 = sum over domains |
| in-process cross-check | CPU ft-v1 vs server MPS: 0 differences in 9 requests, max probability difference 0.0000 |
| Browser check | all 10 items of 05 §6 + 5-second refresh ✔; screenshots `results/poc/P2_ui_1.png` (empty state), `P2_ui_2.png` (router example ROUTE) \~ `P2_ui_8_server_down.png` |
| `/poc/decide` round trip (1 question, 30 consecutive calls) | p50 20.1 / p95 21.1 ms (server processing 19.5 / 20.4, HTTP overhead p95 0.7 ms) |

Caveats: calling from the browser every few seconds raises server processing to 44\~51 ms (the same as the Track D intermittent-call penalty). The p values of the 9 examples cluster at 0.92\~0.96, leaving a margin of only 0.017\~0.05 above T 0.907. General-mode questions are also answered by ft-v1, and their quality was not measured. Load measurement was substituted by Track D6 (base checkpoint, same structure), and 503·Retry-After and 413 were not reproduced in the UI. The CLI `laya --model ml` uses the Hub base checkpoint, so the ft-v1 cross-check was done as an in-process comparison.

## 6. Hypothesis verdicts (`results/verdicts.json`)

| Hypothesis | Verdict | Evidence | One-line interpretation |
|---|---|---|---|
| H1 ko MASSIVE reproduction | supported | K2 E2, Δ0 | the upstream numbers reproduce exactly in the harness |
| H2 multilingual ≫ english, Router 100% | partly supported | Track B: 7 of 10 questions ≥ +0.20 | exceptions NSMC noul, K-MHaS, 3i4K |
| H3 tasks with ≤7 options: above majority, below supervised | first half supported / second half open | Track B; supervised literature values not looked up | ft-v1 0.913 is in the supervised range |
| H4 as-shipped ECE > 0.25, refit ≤ 0.10 | partly / borderline supported | domain_8 0.263 yes, ynat 0.148 no; refit 0.098 | depends on the pooled fit |
| H5 option-order flip 10\~30% | supported | 0.17\~0.27 | 0.037 after fine-tuning |
| H6 noul < 2-choice with neutral keys | open | P0b A/B 2-choice collapse (68/120), NSMC semantic-key choice 0.774 > noul 0.638 | the neutral-key condition was not measured |
| H7 negation fails zero-shot | open | C4 not run; P0 probe wrong on 4 of 5 rows | |
| H8 MPS 3\~6x, sub-linear | rejected | D1 2.33\~2.80x, 10q/1q 4.5\~9.1x | fp16 gain ≤ 8%, slowdown with intermittent calls |
| H9 sort_by_length ≥ 1.3x, flip 0 | supported | D4 1.67\~2.08x, flip 0 | unsorted CPU batching is slower than a loop |
| H10 ONNX int8 ≈ 2x, ECE drift ≤ 0.01 | rejected | D7 1.74x slower, ΔECE +0.0154 | torch fp32 is better on Apple silicon |

## 7. Go/No-Go matrix (`results/go_no_go.json`, criteria are the values proposed in 00_README.md §6)

| Gate | Criterion | zero-shot (2026-10-02) | fine-tuned ft-v1 (2026-10-03) | Verdict |
|---|---|---|---|---|
| G0 reproduction | ±0.03 | Δ0 | same | pass |
| G1 accuracy | ≥ 0.80 (no LLM baseline) | 0.492 | 0.900 (deduplicated 0.893, 2,917 rows 0.913) | pass |
| G2 coverage @ error ≤ 5% | ≥ 0.70 | 0.224 | 2,917 rows 0.923 (dev T 0.907, error 0.042); 250 rows, post-hoc T 0.756 | pass (conditional) |
| G3 ECE after refit | ≤ 0.10 | 0.098 | 0.053 | pass |
| G4 option-order flip | ≤ 0.10 | 0.270 | 0.037 | pass |
| G5 in-process 3q p95 | ≤ 100 ms MPS / ≤ 500 ms CPU | | MPS 22.6 / CPU 57.8 ms (short), 92.5 / 247.8 (long) | pass |
| G6 laya-serve 10 RPS p95 | ≤ 150 ms | | 79.4 ms (MPS), 135.8 (CPU) | pass |
| G7 predict vs predict_batch(sort) | flip 0, abs(Δp) ≤ 0.01 | P0 device parity 0.0017 | D4 flip 0, 0.0001 | pass |

**Final verdict: Conditional Go (premised on a fine-tuning pipeline).** The conditions are those of `docs/05_poc_plan.md` §6 P5: (1) maintain labeled data per taxonomy and retrain (36 minutes), rerunning Track B·C1·E for every new checkpoint; (2) force `lang="ko"`, NFC normalization, a single T 0.907, FALLBACK for low-confidence and general-like requests, fixed option order; (3) replicate processes to match the per-process throughput cap (MPS 22.6 RPS for 3 questions, CPU 10 RPS); (4) recheck coverage and error rate with real traffic in the shadow stage.

## 8. Limitations and caveats

- Sample sizes: test half n=250 (95% CI about ±0.04 at 0.9, ±0.06 at 0.5), MASSIVE reproduction n=100 (±0.10), P0 probe n=30 self-labeled (indicative). The full 2,917-row test is the most precise.
- The T of G2 was chosen on the dev half; on the 250-row test half, depending on how it is chosen, the result is either error 7.9% (dev T) or coverage 0.756 (post-hoc T). On the 2,917 rows, dev T gave an error of 4.2%.
- Utterances identical between train and test: 155/2,917 rows (same labels); the deduplicated figure 0.908 is given alongside.
- MPS fp16 is enabled only for 5 or more rows, with |Δp| ≤ 0.0085; all quality numbers are CPU fp32. MPS slows down 2.2\~3.6× with intermittent calls.
- laya-serve processes inference serially, so concurrency only adds latency. The 503·Retry-After path could not be verified because the load never exceeded `LAYA_MAX_CONCURRENT` (16).
- ONNX (fp32·int8) was slower than torch on this platform (the same with ORT pinned to 10 threads). It may differ on other CPUs.
- C4 negation, C6 high cardinality, C8 long text and the F2 LLM baseline were not run.
- The Jev Korean pilot is an n=24 manual sample (public playground, single pass), so it only checks direction. This n cannot decide whether Jev is better or worse than ft-v1 (p=0.5 even if Jev scored 24/24); a conclusion needs the official API and a 500-row paired comparison.
- The controlled Laya vs Jev comparison (§0a) also goes through the playground, with n=40 per task. Only T1·T7 are significant after Holm correction, the best Laya runner is a post-hoc choice, and the Jev unit price was not verified. The training-mix labeling (Laya trained only on T2·T5, the rest held out) is upstream's self-report; the training data itself was not checked (`results/F/jev_cmp/summary.md` §9, `third_party/laya/research/scripts/build_benchmark_nb.py:760-762`).
- The trained arm of the 3-arm comparison (§0b) is a sample of one training run per task. MPS training is not bit-level deterministic: two T1 runs with the same script, items, seed and arguments diverged: test 0.747 vs 0.690 (against label), paired b/c 217/98, p=1.7e-11. The micro-batch losses first diverge at micro-batch 12. Evaluation is deterministic, so re-evaluating a kept checkpoint gives the same numbers, but retraining gives a different model. Which operation is nondeterministic was not determined (follow-up: once the GPU is free, a short run with `torch.use_deterministic_algorithms(True, warn_only=True)`). In the replicate run with a different seed (seed 14), T1 is 0.735, not significantly different from V2(b) (b/c 118/96, p=0.1510), so the main-run T1 is the lowest of the three runs (`results/T3arm/summary.md` §6.4, §7.4, the "Found during the main training run" sections of `results/T3arm/PREP_20261008.md`).
- For in-mix tasks, if dev is split off from the train split, the epoch 0 dev is not a valid vanilla baseline. For T5 BoolQ, vanilla scores 0.986 on dev (train split) vs 0.834 on validation ext because it remembers rows seen in upstream's training, which inflated the dev baseline; so it was flagged as "training failure" even though it simply has no training gain (ext 0.834 vs 0.832). Care is also needed when using the epoch 0 dev as the baseline for T2·T9, which have the same structure, and for T10, which has only one public split (T2 shows no gap, with dev 0.936 and ext 0.940). Epoch selection compares trained epochs with each other, so the impact is small (`results/T3arm/summary.md` §6.1, the "Found during the main training run" sections of `results/T3arm/PREP_20261008.md`).
- In the 3-arm comparison, on T10 (customer-support ticket queue) all four systems (Jev, vanilla english, vanilla multilingual, trained) are wrong on 18/40 of the 40 Jev-item rows. The S7 analysis read that for many wrong answers the gold queue does not match the queue description given in the question (interpretation). The label quality is suspect and needs a manual check; until then, T10 accuracy is not read as routing ability (`results/T3arm/summary.md` §1.6, `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md`).
- The 3-arm replicate run (seed 14) ran into cotenant contention. It overlapped with 7 experiments of another project, swap filled up and T9 training stalled, so only the replicate-run queue was stopped at 2026-10-08 19:37. The watcher `poc/finetune/autostart_rep_t9t10.sh` restarted T9·T10 at 22:58:42 after the contention ended, and they finished with rc 0 at 2026-10-09 00:23:20 (no contention, `results/T3arm/rep_s14/autostart.log`). The computation does not depend on timing, so all run 2 results are valid, and the cost figures (§0b) use the run 1 numbers (`results/T3arm/PREP_20261008.md` "Replicate run: T9 stop and automatic restart").
- The 3 inconsistencies of the replicate run (T4 Jev items trained vs vanilla, T8 Jev items trained vs Jev and trained vs vanilla) are all n=40 Jev-item comparisons with a Holm p near 0.05. In an interim tally in which run 2 had an 8-task family, T6 was inconsistent and became confirmed with the 10-task family, while T4 changed the other way. Such borderline verdicts are sensitive to the seed and to the size of the Holm family, so only verdicts on which both runs agree were confirmed (`results/T3arm/summary.md` §7.2).
- Tool defect (follow-up): the smartypants step of the Markdown→PDF renderer used for PDF rendering replaces HTML tags with placeholders and then applies the URL pattern `/\bhttps?:\/\/\S+/g` (the renderer's `src/smartypants.ts:23`). When a link text is a URL, `\S+` swallows the `</a>` placeholder right after it and the restore runs only once, so the placeholder string (`SMARTPANTS_PRESERVED_N`) shows up in the text, `</a>` disappears, and the whole rest of the document becomes one link. Workaround: drop the URL scheme from link texts (`[github.com/x](https://github.com/x)`, no bare URLs). Separately, GFM renders the text between two `~` within one paragraph or table cell as strikethrough, so the range notation `~` is escaped as `\~`. Both workarounds were applied to `docs/08_paper_ko.pdf` and `docs/10_paper_laya_vs_jev.pdf` (PDFs are not included in the public repository) (2026-10-07). The em dash rule of the same file, `/(\w|\s)--(\w|\s)/g` (`src/smartypants.ts:81`), also changes CLI flags in the body text, so `laya-evals --onnx` at `docs/08_paper_ko.md:282` is printed with an em dash in the PDF (no workaround applied; wrapping the flag in a code span avoids it; not fixed because of the instruction not to change the content of 08). This is a workaround; fixing the renderer or filing an issue with the renderer is still open (`docs/09_laya_vs_jev_plan.md` open question 11).
- Defects and inconsistencies found upstream: `@torch.no_grad()` missing in `laya.calibrate.records_from_labeled` (raises an exception with a real Agent, calibrate.py:286 → agent.py:1177); `laya.evals.evaluate` calls `predict(..., model=)`, which is incompatible with `Agent.predict` (a Router or a wrapper is needed); the agent-mode output prefix of `hf download` breaks the documented commands (`--quiet` needed); "Korean 0.490" in the model card is the T4 n=300 value, while the official table says 0.470; the README claim that "multilingual's criteria-less noul reads the state" does not hold in either the Korean or the English translation; the license tag of the MASSIVE HF mirror is apache-2.0 vs CC BY 4.0 in the original repository; the 13 s first MPS call in `examples/README.md` is 0.1 s on this machine.

## 9. How to reproduce

1. Environment: `docs/02_environment_setup.md` §2 (uv venv 3.12, `laya[serve,onnx,structured]==0.3.23`, `hf download convaiinnovations/laya --revision 55cf4c4… --quiet`, `models/` symlinks, `env.sh`) → §3 smoke (`laya-evals run third_party/laya/research/evals/fixture.jsonl --model english --device cpu`).
2. Evaluation sets: `.venv/bin/python scripts/build_ko_evalsets.py all --n 500 --seed 13` + ablation variants (04 §6).
3. Track A: `results/korean_support/K2_build.py` + laya-evals (ko/en intent-20) or `laya-evals run data/evals/ko_massive_intent_20opt.jsonl --model multilingual --device cpu`.
4. Track B: `results/B/B_run.sh` (46 runs) → `scripts/metrics_extra.py summary|paired` → `results/B/B_summary.py`.
5. Track C: `scripts/probe_option_order.py … --permutations 5 --seed 13 --split dev`, `results/C/C_schema_v2_build.py` + laya-evals.
6. Track E: `scripts/calibrate_ko.py --sets … --splits results/B/B_splits.json --pooled --per-task --min-bucket-n 100 --out-payload poc/calibration/ko_v1.json`.
7. Track D: `results/D/D_run.sh` (scripts/bench_latency_local.py, bench_batch_local.py, bench_http_local.py, export_onnx + laya-evals --onnx).
8. P4: `.venv/bin/python poc/finetune/make_domain8_items.py rows|items`, `bash poc/finetune/run_full.sh` (11,094 rows × 3 epochs, including evaluation).
9. P2 service: `LAYA_DEVICE=mps LAYA_API_KEY=devkey LAYA_HOST=127.0.0.1 .venv/bin/uvicorn poc.service.app:app --host 127.0.0.1 --port 8000` → `open http://127.0.0.1:8000/poc/ui/` (acceptance checks: `.venv/bin/python results/poc/P2_acceptance.py`).
10. Dashboard: `python3 scripts/build_dashboard.py --results results/ --out results/dashboard/index.html`.
11. Laya vs Jev comparison: sets `scripts/build_jev_cmp_sets.py all`, Laya `bash results/F/jev_cmp/run_laya.sh`, analysis of the Jev records `results/F/jev_cmp/jev_cmp.py analyze`, synthesis `results/F/jev_cmp/s6_summary.py build` followed by `verify` (full commands in `results/F/jev_cmp/summary.md` §10). The analysis reads only the recorded jsonl. Rerunning the Jev sessions requires requests to the public site and follows the operating rules of `docs/09_laya_vs_jev_plan.md` §2.
12. 3-arm comparison: the preparation and validation (S0·S1) commands are in the "Commands" section of `results/T3arm/PREP_20261008.md`. Main training run (S2) `bash poc/finetune/run_all_tasks.sh` (gate `poc/finetune/READY_T3ARM`; check with `PREFLIGHT_ONLY=1 bash poc/finetune/run_all_tasks.sh` before starting), synthesis (S3) `nice -n 10 .venv/bin/python results/T3arm/t3arm_summary.py build --root results/T3arm --out results/T3arm` followed by `verify` with the same arguments. The calibration-separation column (vanilla + task T) is `bash poc/finetune/t3arm_calib_sep.sh` (results in `results/T3arm/calib_sep/`, last line of the status log `CALIB_SEP FINISHED`), and the replicate run is `SEED=14 RUN_TAG=rep_s14 bash poc/finetune/run_all_tasks.sh` (results in `results/T3arm/rep_s14/`). The restart watcher used after the T9 stop is `nohup perl -MPOSIX -e 'setsid; exec @ARGV' bash poc/finetune/autostart_rep_t9t10.sh >/dev/null 2>&1 &`, which runs `SEED=14 RUN_TAG=rep_s14 TASKS="T9 T10" bash poc/finetune/run_all_tasks.sh` once its conditions hold (status in `results/T3arm/rep_s14/autostart.log`). The analysis of the T9·T10 Jev records is `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S7 T9_enron_spam_40` (for T10 `T10_support_tickets_queue_40`), and the collection procedure, which requires site requests, is in `results/F/jev_cmp/sessions/S7_20261008/S7_run_card.md`. The synthesis reads only the recorded reports and does no model loading or evaluation. Because of MPS nondeterminism, training does not reproduce bit for bit even with the same commands (§8).

## 10. Appendix

- Full list of run_ids with file links: `results/dashboard/index.html` §10 (report JSON files: B 47, C 2+9, D 19, E 2, P4 21, poc 32, korean_support 19).
- Run cards: `results/env/smoke_20261002.md`, `results/poc/P0_20261002.md`, `P0b_20261002.md`, `P0c_20261002.md`, `results/korean_support/K2_20261002.md`, `results/B/B_20261002.md`, `results/C/C_20261002.md`, `results/E/E_20261002.md`, `results/D/D_20261003.md`, `results/P4/P4_probe_20261002.md`.
- Laya vs Jev run cards: `results/F/jev_cmp/S0_20261006.md` (Laya side), `results/F/jev_cmp/sessions/S{1,1b,2,3,4,5}_*/S*_run_card.md` (Jev sessions), `results/F/jev_cmp/S6_20261007.md` (synthesis).
- Decision records: 00_README.md §5 (choice of scenario C, P4 go-ahead), 05 §2·§6 P5 (verdict and conditions), 07 §6 (Korean operating decisions). No ADR files (docs/decisions/) were written.

**English** | [한국어](REPORT.ko.md)
