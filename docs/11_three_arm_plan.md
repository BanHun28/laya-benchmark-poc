# 11. 3-arm extension plan: Jev vs vanilla Laya vs trained Laya

**Purpose**: In the Laya vs Jev comparison of 09, vanilla Laya's deficit mixes two factors: retention of the tasks Laya saw during training, and zero-shot generalization to tasks it has never seen. We separate the two by task category, defined with respect to Laya's training mix. Adding Laya fine-tuned on task data (trained) as a third arm, we answer two questions by measurement: "Does training let Laya catch up with Jev?" and "Was Laya trained properly?"

**Prerequisite documents**: `09_laya_vs_jev_plan.md` §3-§5 and §10 (tasks T1-T8, protocol parity, metrics, conclusions), `05_poc_plan.md` §6 P4 (fine-tuning pipeline and the Korean ft-v1 results), `03_benchmark_plan.md` §3-§4 (common protocol, metric definitions), `06_templates.md` §1 (run card). The supporting results are `results/F/jev_cmp/summary.md`, `results/P4/P4_probe_20261002.md` and `results/P4/full_20261003-1156_timing.json`.

**Outputs**:
- Training script: the length-patched `poc/finetune/laya_finetune_mps_patched.py`. The diff against upstream is `results/T3arm/finetune_script.diff`.
- Training data: the builder `scripts/build_train_sets.py` and the per-task train/dev/calib in `poc/finetune/data/`.
- Evaluation sets: the T9·T10 Jev-format sets (only new files added to `data/evals/jev_cmp/`) and the extended evaluation set `data/evals/jev_cmp_ext/`.
- Main training run: the driver `poc/finetune/run_all_tasks.sh`, the gate `poc/finetune/READY_T3ARM`, and the selected per-task checkpoints `poc/finetune/ckpt_t3arm/<task>/` (not included in the public repository).
- Results: `results/T3arm/` (preparation run card, validity/, vanilla/, per-task reports, summary.md·json, figures) and the updated `results/REPORT.md`·dashboard·paper v3.

---

## 1. Purpose and questions

**Owner decisions (2026-10-08).**
- The training base is the base the Router picks: english for the English tasks, multilingual for T7.
- The budget per task is at most 5,000 items × 2 epochs.
- Add 2 tasks that were in Laya's training mix (T9, T10).
- Jev is **not rerun**, since its T1-T8 data already exist. The Jev measurement of T9·T10 (80 requests) is decided after seeing the Laya results. (Run on 2026-10-08: T9·T10 measured in session S7; see §9)

T8 held out dev 60 and calib 40 from train (hold-out) and trained on all of the remaining 444 rows for 2 epochs. This was applied as the default at the start of the main training run, and the project owner confirmed it (2026-10-08, open questions 2·10).

| Question | Content | Basis for the verdict |
|---|---|---|
| Q1 | Does vanilla Laya's deficit against Jev appear only on the held-out tasks? | (Jev − vanilla) per category and the difference between the two categories (difference-in-differences) |
| Q2 | Does fine-tuning on task data reach or surpass Jev in both categories? | Paired exact McNemar test of trained vs Jev on the Jev items, per-category macro |
| Q3 | What does specialisation cost? | Number of labels per task, M4 Pro training time (minutes), checkpoint size |
| Q4 | Was Laya trained properly? | Whether the §4 training validation checks V1-V6 pass, and the training diagnostics |

The current state (no training) is as follows (`results/F/jev_cmp/summary.md` §2). vanilla is english on the English tasks and multilingual on T7. T1 is based on the 120 decisions comparable with Jev.

| arm | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 |
|---|---|---|---|---|---|---|---|---|
| Jev | 0.867 | 0.875 | 0.700 | 0.925 | 0.925 | 0.650 | 0.910 | 0.775 |
| vanilla | 0.383 | 0.975 | 0.750 | 0.725 | 0.725 | 0.425 | 0.620 | 0.775 |

Right now only two tasks, T2·T5, are in the training mix, so the Q1 categories are unbalanced. Adding T9·T10 makes it 4 in-mix tasks vs 6 held-out tasks.

## 2. Design

**Categories.** We split by the training mix that upstream disclosed.

| Category | Tasks | Evidence |
|---|---|---|
| In Laya's training mix | T2 AG News, T5 BoolQ, **T9 Enron spam (new, noul)**, **T10 customer-support ticket queue routing (new, 10-way choice)** | `third_party/laya/research/scripts/build_benchmark_nb.py:760`, `third_party/laya/BENCHMARKS.md:142` (Email spam, in training), `:147` (Support triage, in training). `third_party/laya/` is the upstream clone (not included in the public repository; recreate it by cloning https://github.com/NandhaKishorM/laya at commit 4aa6761) |
| Excluded from Laya's training (held out) | T1 typed-decisions, T3 Emotion, T4 Banking77-10, T6 SST-5, T7 MASSIVE intent-10 × 5 languages, T8 prompt-injections | `build_benchmark_nb.py:761-762` "sst5, emotion, prompt_injections, banking77 were held out. Neither checkpoint trained on typed-decisions, MASSIVE or XNLI." |

**New task definitions.** Both tasks use the wording of the upstream Themes benchmark verbatim.
- T9 is `SetFit/enron_spam`. The state is `laya.email_state(subject, message[:3000])` and the noul question is "Is this email unsolicited spam or bulk marketing?" (`third_party/laya/research/scripts/bench_apps.py:159-168`).
- T10 is the rows of `Tobi-Bueck/customer-support-tickets` whose language is en, that belong to the 10 queues and that have a body. The state is subject and body[:3000]. The choice question is "Which support queue should handle this ticket?" and the criteria are upstream's 10 queue descriptions (`bench_apps.py:130-155`).

**3×2 design.**

| arm \ category | In training mix (T2, T5, T9, T10) | Held out (T1, T3, T4, T6, T7, T8) |
|---|---|---|
| Jev (zero-shot, playground) | T2·T5 measured, T9·T10 not measured (decision pending) (Run on 2026-10-08: T9·T10 measured in session S7; see §9) | measured |
| vanilla Laya (zero-shot) | T2·T5 measured, T9·T10 newly measured | measured |
| trained Laya (per-task fine-tuning) | new | new |

**Arm definitions.**
- **Jev.** The playground results of 09 (`results/F/jev_cmp/jev_runs_all.jsonl`, not included in the public repository) are reused as they are. No new requests. (Run on 2026-10-08: T9·T10 took 80 new requests in session S7; see §9)
- **vanilla Laya.** The same base as trained, without training. Only with matching bases is trained − vanilla a pure training effect. The Router and the opposite base are reported as reference columns. For T1-T6 the Router picks english everywhere, so the Router column equals the vanilla column. For T7 it sends the 20 en rows and 5 de rows to english and the remaining 75 rows to multilingual. For T8 it sends 14/40 rows to multilingual. So the Router columns of T7·T8 differ from vanilla (`results/F/jev_cmp/summary.md:44`).
- **trained Laya.** One base is fine-tuned separately for each task. T7 is a single multilingual model trained on the 5 languages together. The evaluation path is the same as vanilla's (CPU fp32, intra-op 10 / inter-op 1, batch 8).

**Evaluation items.** Split into two tiers.

| Tier | Use | Composition |
|---|---|---|
| Jev items | Direct 3-arm comparison (byte-identical inputs to Jev's) | T1 40 cases / 200 decisions (120 for the Jev comparison), T2-T6·T8 40 each, T7 20 ids × 5 languages = 100. For T9·T10 only 40 Jev-format items under the same rules and the playground forms are built; no requests are sent (Run on 2026-10-08: requested in session S7; see §9) |
| Extended set (ext) | Narrow CIs for vanilla vs trained | T2-T6·T9·T10 500 each (stratified from the evaluation split, seed 13, excluding overlaps with training rows), T1 typed-decisions full test 400 cases / 2,000 decisions, T7 100 ids × 5 languages = 500 (same ids across languages), T8 full test 116 |

The evaluation split is test for most tasks. T5 has no test split, so it uses validation. T10 uses the test share of a hash split.

## 3. Training data construction

**Format identity.** Training items are built with the same question wording, criteria text, option rendering and state serialization as the evaluation sets (reusing the per-task functions of `scripts/build_jev_cmp_sets.py`). As in evaluation, T4 and T7 have 10 options drawn per row: the gold + 9 distractors. T4 uses key-only rendering and T7 uses `key: key spaced` rendering.

Upstream `build_training_item` (`third_party/laya/notebooks/laya_finetune_typed_decisions_mps.py:58-101`) takes the gold of every format as a `{"probabilities": {...}}` distribution. The keys are the option keys for choice, "false"/"true" for noul, and "0".."n-1" for score. T1 uses the dataset's teacher distribution as is; the other tasks are one-hot. The script silently drops items whose marker count differs from the option count (`:91-92`). So the builder records the number dropped per task.

Row counts follow the dataset_info of the `data/raw/hf` cache (not included in the public repository). dev and calib are disjoint. They are drawn from the validation split when one exists, otherwise from a held-out slice cut from train. dev is used only for epoch selection and calib only for the temperature fit.

| Task | train source (rows) | train items | dev (at most 1,000) | calib (400) |
|---|---|---|---|---|
| T1 | `LocalLLaMA/typed-decisions` all train (1,200 cases) | up to 5,000 decisions after removing the dev·calib cases (by case) | part of the train cases | part of the train cases |
| T2 | `fancyzhx/ag_news` train (120,000) | 5,000 (label-stratified) | train remainder | train remainder |
| T3 | `dair-ai/emotion` split train (16,000) | 5,000 (label-stratified) | validation (2,000) | validation |
| T4 | `mteb/banking77` train (9,993) | 5,000 (stratified over 77 labels, 10 options) | train remainder | train remainder |
| T5 | `google/boolq` train (9,427) | 5,000 (label-stratified) | train remainder (validation is the evaluation source) | train remainder |
| T6 | `SetFit/sst5` train (8,544) | 5,000 (level-stratified) | validation (1,101) | validation |
| T7 | `mteb/amazon_massive_intent` en·de·ja·zh-CN·ko train | 1,000 per language = 5,000 (10 options) | validation | validation |
| T8 | `deepset/prompt-injections` train (546) | all except dev·calib (444) × 2 epochs | part of train (60) | part of train (40, at most min(400, N//10)) |
| T9 | `SetFit/enron_spam` train (31,716) | 5,000 (label-stratified) | train remainder | train remainder |
| T10 | `Tobi-Bueck/customer-support-tickets` train (61,765, all languages) | English rows of the 10 queues hash-split into train/dev/test, then 5,000 from the train share | dev share | dev share (disjoint from dev) |

**Option-order shuffle augmentation.** As in P4, train items shuffle the criteria order per row (`--shuffle-options all` of `poc/finetune/make_domain8_items.py`). Only choice questions are shuffled: for score the level order itself carries meaning, and noul has fixed options. dev and calib keep the original order. In P4 this approach reduced the dev flip from 0.270 zero-shot (`results/C/C1_option_order_20261002.md:9`) to 0.037 (`results/P4/metrics/full_20261003-1156_option_order_dev.md:9`).

**calib placement.** The script shuffles the items with `random.Random(20260922)` and uses the first `min(--calib-max, N//10)` of the shuffled order as calib (`:258-261`). As with the P4 adapter, the calib rows are placed at those positions in advance so that no train row is used as calib.

**Leakage removal.** Among the train·dev·calib rows, those whose state text equals that of an evaluation item (the Jev items and all of ext) are removed. Both exact matches and matches after whitespace·case normalization are checked. The number removed per task is recorded. In P4, 155 rows of the 2,917-row MASSIVE ko evaluation set overlapped verbatim with states in the training file, and ft-v1's accuracy on those rows was 0.994 (`results/P4/metrics/full_20261003-1156_overlap.md`).

## 4. Training validation (Q4: was it trained properly?)

| ID | Check | Method | Pass criterion |
|---|---|---|---|
| V1 | zero-step identity | With the patched pipeline, build an export with optimizer step 0 for each base (epochs 0 or lr 0; if impossible, record the closest method and the reason). Compare the weights with the base and evaluate one set | Bit-identical weights (the base is fp16 and the export is also `.half()`, `:225`). 100% argmax agreement. List the config differences. With the base temperature restored, the probabilities also match |
| V2 | upstream reproduction | (a) Evaluate `models/laya-typed-decisions` (not included in the public repository) on T1 ext 2,000 decisions. (b) Train the english base with our pipeline on T1 train, up to 5,000 decisions × 2 epochs, and evaluate on the same 2,000 | (a) Accuracy within ±0.02 of the published 0.766. Also record the differences from soft acc 0.471, Brier 0.061 and score MAE 0.242 (`BENCHMARKS.md:172`). (b) At least 0.562 (vanilla english 0.362 + 0.20, `:173`) and above majority 0.461 (`:187`) |
| V3 | label-shuffle control | T3 Emotion, english base, labels of 5,000 items shuffled with seed 13, 1 epoch of training | dev accuracy at most majority + 0.05. At least 0.30 below the epoch 1 dev accuracy of T3 training with the real labels |
| V4 | format identity | For each task, decode 20 train items with the tokenizer and compare them with the inference sequence (`build_sequence`) of the same state and question | Original-order items match token for token; shuffled items match in option set and gold slot. 100% for both |
| V5 | smoke | For each base (english, multilingual), run 200 items × 1 epoch through training, export, `laya.load` and evaluation. `run_all_tasks.sh` runs all 10 tasks with `SMOKE=1` (64 items per task, 1 epoch, temporary directory) | Every STEP OK. Record item/s per base and update the §6 time estimate |
| V6 | leakage | Intersection of train·dev·calib with the evaluation items after the §3 rules are applied | 0 for both exact and normalized matches. For in-mix tasks, note separately that overlap with upstream's training split cannot be checked |

**Differences V1 catches.** The export changes the following four things. These must not leak into trained − vanilla.
- `max_len`·`head_max_len`: hard-coded to 1024/256 before the patch (`:240`). The english base values are 512/192 (`models/laya/rl_agent_config.json`).
- `model_name`: hard-coded to "laya-typed-decisions" (`:358`).
- `temperature`: the per-format values are refit on the task calib. Formats absent from calib get 1.2 (`:354-359`).
- `temperature_by_options`: deleted (`:361`). vanilla english carries per-format values and values per option-count bucket; multilingual is 1.0 throughout.

Temperature does not change the argmax of a single question, so the accuracy comparison is unaffected. The calibration comparison is affected (§5).

**Reading V2.** (a) checks whether our evaluation path reproduces upstream's numbers. (b) is not a reproduction; it checks whether training works on the reduced budget. Upstream trained on about 30k questions × 4 epochs (`third_party/laya/README.md:1532`). So the gap between (a) and (b) is read as a budget difference and recorded as a number.

**Training diagnostics.** For each task we record:
- The windowed loss curve and the windowed train-accuracy curve.
- dev accuracy: epoch 0 (= vanilla), 1, 2.
- The selected epoch and the train−dev gap (overfitting).
- The fitted temperature and whether it reaches the clamp. The fit is clipped to [0.1, 10] in the training script (`:218`), and inference clips it to [0.5, 5] when loading the checkpoint (`third_party/laya/laya/common.py:706-707`, `:765-766`).
- The option-order flip on 40 dev items (`scripts/probe_option_order.py`).
- Per-class recall changes.

The epoch is selected by dev accuracy, with ties going to the earlier epoch. Epoch copies still carry the base temperature and `temperature_by_options` (verified on P4's `poc/finetune/ckpt_domain8_v1/epoch_1`, which is not included in the public repository). So when an epoch other than the last is selected, the temperature is refit on the same calib. If dev is below vanilla in both epochs, the task is flagged "training failure". The cause is traced in the order format, labels, lr, and then retraining is decided.

## 5. Metrics and statistics

- **Direct 3-arm comparison (Jev items).**
  - Per-task accuracy with Wilson 95% CIs.
  - Paired exact McNemar tests compare trained vs Jev and trained vs vanilla. vanilla vs Jev reuses the 09 results.
  - For T1 (40 cases) and T7 (20 ids) the items are not independent, so cluster bootstrap CIs are reported as well.
  - Secondary metrics are as in 09: soft accuracy·Brier·score MAE for T1 (`results/F/jev_cmp/laya_summary.py`), AUROC for T5·T8·T9, MAE for T6.
- **vanilla vs trained (ext).** Paired bootstrap CIs (10,000 resamples) of the per-task accuracy difference, and exact McNemar tests. For T1, the same metrics as V2 are also reported on the 2,000 decisions.
- **Multiple comparisons.** Holm is applied separately to the 8 tasks of trained vs Jev and the 10 tasks of trained vs vanilla. (Run on 2026-10-08: with T9·T10 Jev added, trained vs Jev and Jev vs vanilla also cover 10 tasks; see §9)
- **Category aggregates.**
  - Macro accuracy per arm and per category.
  - Q1's difference-in-differences is the mean (Jev − vanilla) of the held-out category minus that of the in-mix category, with a task-resampling bootstrap CI.
  - (trained − vanilla) and (trained − Jev) are also reported per category.
  - The training gain in the in-mix category may come out small to the extent that vanilla has already seen the data (retention cap).
  - The tables note that T9·T10, which lack Jev, are left out of the Jev aggregates. (Run on 2026-10-08: S7 brought T9·T10 into the Jev aggregates; see §9)
- **Calibration.** Brier, ECE (15 bins) and coverage@error 5%·10% per arm. trained's temperature is refit on the task calib. vanilla english uses upstream's fitted values and multilingual uses 1.0. So we note that calibration improvements include a temperature refit effect (open question 4). (Run on 2026-10-08: the calibration-separation columns split the refit effect from the training effect; see §9)
- **Cost (Q3).** Number of labels per task, training time (minutes), item/s, peak MPS memory, checkpoint size.
- **Training diagnostics (Q4).** The §4 items go into the per-task reports and the summary.

## 6. Execution order and budget

| Stage | Content | GPU | Outputs |
|---|---|---|---|
| S0 preparation | Length patch of the training script (read `max_len`·`head_max_len`·`model_name` from the base config). Build the training data, the T9·T10 Jev-format sets and the ext sets. Measure vanilla (T9·T10 and all ext, english·multilingual·Router). Reproduce the existing T1-T8 vanilla numbers bit for bit on the new evaluation path | none (CPU evaluation) | `poc/finetune/laya_finetune_mps_patched.py`, `scripts/build_train_sets.py`, `data/evals/jev_cmp_ext/`, `results/T3arm/vanilla/` |
| S1 validation | V4, V6, V5 (both bases), V1, V2(a), V2(b) T1 training, V3 shuffled-label training, `run_all_tasks.sh` `SMOKE=1` | about 0.8-1.7 hours | `results/T3arm/validity/`, `results/T3arm/PREP_<date>.md`, `poc/finetune/READY_T3ARM` |
| S2 main training run | `run_all_tasks.sh` processes T1-T10 in order. For each task: training, per-epoch dev evaluation and epoch selection, Jev-item·ext evaluation, diagnostics, keeping only the selected checkpoint | about 3.4-8 hours (including evaluation) | `poc/finetune/ckpt_t3arm/<task>/`, `results/T3arm/<task>/`, `results/T3arm/run_all_status.log` |
| S3 synthesis | 3×2 table, statistics, diagnostics, figures, REPORT·dashboard·paper v3 | none | `results/T3arm/summary.md`, `results/T3arm/summary.json`, `results/T3arm/figs/` |

**Run gate.** When S1 finishes, `poc/finetune/READY_T3ARM` is created with the list of items sha256. S2 starts when this file exists and the GPU is idle (the same watcher approach as P4's `poc/finetune/autostart_when_gpu_free.sh`). The driver writes `STEP <task>:<step> OK|FAILED` to `results/T3arm/run_all_status.log`. The last line is `RUN_ALL FINISHED` or `RUN_ALL FAILED`.

**Throughput assumptions.**
- The P4 main training run, on an idle GPU, finished 11,094 items × 3 epochs with multilingual in 2,150 s, i.e. 15.58 item-pass/s for the train loop (`results/P4/full_20261003-1156_timing.json`). The sequences then were 207-266 tokens (`results/P4/P4_probe_20261002.md:57`).
- The english encoder has 1.3× the layers, 28 vs 22. Its non-embedding parameters, computed from the layer configuration, are about 343M vs 110M, 3.1× (`models/laya/encoder/config.json`, `models/laya-multilingual/encoder/config.json`).
- So at the same length we assume english is 1.3-3.1× slower (5-12 item/s). For tasks whose inputs reach 512 tokens we assume half of that.
- The lower bound matches the 2-3.5 hours in the options offered to the project owner and in the instructions. The upper bound is more than twice that.
- Once V5 measures item/s per base, the table below is updated before S2 starts.

| Item | item-pass | Assumed throughput (item/s) | Estimate |
|---|---|---|---|
| Short-input English tasks (T2, T3, T4, T6) | 10,000 per task | 5-12 | 14-33 min per task |
| Long-input English tasks (T1, T5, T9, T10) | 10,000 per task | 2.6-6.3 | 26-64 min per task |
| T7 (multilingual) | 10,000 | about 15.6 (measured in P4) | about 11 min |
| T8 (english) | about 1,300-1,640 | 5-12 | 2-6 min |
| S1's V2(b), V3, smoke | 10,000 + 5,000 + a small amount | same as above | about 0.8-1.7 hours |
| Evaluation (CPU, per task 2 dev passes + Jev items + ext) | | | 3-8 min per task |
| Total | | | S1 about 0.8-1.7 hours, S2 about 3.4-8 hours |

**Disk.** Free space on 2026-10-08 is 54 GB.
- During training, one english task uses up to about 3.4 GB: the final model, `checkpoint_latest` and 2 epoch copies. The english weights are 843 MB, and P4 multilingual used 3.2 GB at 3 epochs.
- After a task's evaluation, the sha256 of the epoch copies and `checkpoint_latest` is recorded and they are deleted. Only the one selected checkpoint is kept (english about 0.85 GB, multilingual about 0.68 GB). The total kept is about 8.3 GB.
- The V1 export and the V2(b)·V3 models are deleted after their numbers are recorded.
- The preparation stage keeps at least 25 GB free. The driver stops if free space is below 15 GB before a task starts.

## 7. Outputs

| Path | Content |
|---|---|
| `poc/finetune/laya_finetune_mps_patched.py`, `results/T3arm/finetune_script.diff` | Copy of the upstream script and a minimal diff (reads the lengths·model_name from the base config) |
| `scripts/build_train_sets.py`, `poc/finetune/data/` | Per-task train/dev/calib JSONL, items `.pt`, provenance, leakage-removal records |
| `data/evals/jev_cmp/` T9·T10 new files | 40-item Jev-format sets, `_playground.json` forms, MANIFEST entries (existing entries' sha256 confirmed unchanged) |
| `data/evals/jev_cmp_ext/` | Per-task ext sets and MANIFEST |
| `poc/finetune/run_all_tasks.sh`, `poc/finetune/READY_T3ARM` | Driver for the main training run·evaluation·cleanup (supports `SMOKE=1`) and the run gate |
| `poc/finetune/ckpt_t3arm/<task>/` | Selected per-task checkpoints (not included in the public repository) |
| `results/T3arm/` | `PREP_<date>.md`, validity/, vanilla/, `<task>/` (training logs, dev curves, reports), `run_all_status.log`, summary.md·json, figs/ |
| `results/REPORT.md`, `results/dashboard/index.html`, paper v3 | Reflect the 3×2 results |

## 8. Risks and caveats for interpretation

| Risk | Impact | Mitigation |
|---|---|---|
| Jev's training data are unknown | If Jev saw the same public datasets, "Jev zero-shot" may actually be retention | State that the categories are defined only with respect to Laya |
| The trained arm uses labels | A specialisation comparison, not a zero-shot comparison | Attach "N labels + M minutes of training" to tables and sentences |
| vanilla has already seen the data of the in-mix tasks | trained − vanilla may come out small (retention cap) | Read Q1·Q2 per category |
| T10 has only a train split | Our evaluation share may overlap upstream's training data (by design) | Note the hash-split rule and this limitation in the results |
| The Jev items are n=40 per task | Small trained vs Jev differences cannot be decided | Holm correction and cluster bootstrap. ext is used only for vanilla vs trained |
| Base choice | For T8 the Router sends 14/40 rows to multilingual, but trained is trained on english alone | Base fixed by the Router. The opposite base and the Router are reference columns |
| Fixed hyperparameters (script defaults) | Under- or overtraining depending on the task | Select the epoch from the dev curve. For failed tasks, trace the cause, then decide on retraining (§4) |
| The calibration comparison mixes in the temperature effect | Over-reading trained's ECE improvement as a training effect | Report accuracy and calibration separately and note the refit effect (§5) |
| The time estimate is wide | S2 may take up to 8 hours | Update with the V5 item/s. Unattended run, so no effect on the results |

## 9. Results (S2·S3, 2026-10-08)

The S2 main training run ran unattended on 2026-10-08 10:57-15:01 (about 4.1 hours). In `results/T3arm/run_all_status.log` all 148 STEPs are OK, FAILED is 0, and the last line is `RUN_ALL FINISHED`. After that, the 80 Jev requests for T9·T10 (session S7), the calibration-separation columns (`results/T3arm/calib_sep/`) and the seed 14 replicate run were completed, and the S3 synthesis (`results/T3arm/summary.md`·`summary.json`·`figs/`) was rebuilt at 2026-10-09 00:23 after the replicate run finished (`t3arm_summary.py verify` mismatches 0). All numbers in this section are copied from `summary.json`; the detailed tables are in `summary.md`. Below, trained is run 1 (the main training run). A verdict is confirmed only when the seed 14 replicate run (run 2) reaches the same conclusion: of 30, 27 are confirmed and 3 are inconsistent (see "Replicate run" below).

**Q2. Does training reach Jev?** By the significance criterion, yes. trained vs Jev has no significant difference after Holm correction on all 10 tasks. Adding T9·T10 grew the Holm family from 8 tasks to 10, and the after-Holm verdicts of T1-T8 did not change. Before correction, trained is significantly better on T3 (0.950 vs 0.700) and T8 (0.975 vs 0.775), and there is no task on which Jev is significantly ahead. The gaps on T1·T7, where Jev was significantly better after Holm at zero-shot, disappeared after training. T7 ties at 0.910, and T1 is 0.792 vs 0.867, with a cluster bootstrap difference of −0.075 [−0.185, +0.025] that includes 0. In the in-mix category, T5 is numerically higher for Jev, 0.775 vs 0.925 (b/c 2/8, p=0.1094). The category means of trained − Jev are −0.013 [−0.100, +0.062] in-mix and +0.071 [−0.017, +0.163] held-out. With n=40 per task, small differences cannot be decided (`results/T3arm/summary.md` §1.1, §1.4, §3.2). Including the replicate run, trained vs Jev is confirmed (n.s.) on 9 tasks, and only T8 is inconsistent, because trained is significantly better in run 2. In neither run is there a task on which Jev is significantly ahead after Holm (see "Replicate run" below).

| Task | Category | Jev | vanilla | trained | trained vs Jev: b/c, p (Holm p) | Verdict (after Holm) |
|---|---|---|---|---|---|---|
| T1 typed-decisions | held-out | 0.867 | 0.383 | 0.792 | 10/19, 0.1360 (0.9523) | n.s. (n.s.) |
| T2 AG News | in-mix | 0.875 | 0.975 | 0.950 | 3/0, 0.2500 (1.0000) | n.s. (n.s.) |
| T3 DAIR Emotion | held-out | 0.700 | 0.750 | 0.950 | 11/1, 0.0063 (0.0635) | trained significantly better (n.s.) |
| T4 Banking77-10 | held-out | 0.925 | 0.725 | 0.950 | 3/2, 1.0000 (1.0000) | n.s. (n.s.) |
| T5 BoolQ | in-mix | 0.925 | 0.725 | 0.775 | 2/8, 0.1094 (0.8750) | n.s. (n.s.) |
| T6 SST-5 | held-out | 0.650 | 0.425 | 0.675 | 6/5, 1.0000 (1.0000) | n.s. (n.s.) |
| T7 MASSIVE intent-10 | held-out | 0.910 | 0.620 | 0.910 | 7/7, 1.0000 (1.0000) | n.s. (n.s.) |
| T8 prompt-injections | held-out | 0.775 | 0.775 | 0.975 | 9/1, 0.0215 (0.1934) | trained significantly better (n.s.) |
| T9 Enron spam | in-mix | 1.000 | 1.000 | 0.975 | 0/1, 1.0000 (1.0000) | n.s. (n.s.) |
| T10 support tickets | in-mix | 0.250 | 0.300 | 0.300 | 5/3, 0.7266 (1.0000) | n.s. (n.s.) |

On T10, 18/40 rows are wrong for all four systems (Jev, vanilla english, vanilla multilingual, trained). Label quality is suspect and needs manual checking (`results/T3arm/summary.md` §1.6, open question 12).

**Q1. Does vanilla's deficit appear only on the held-out tasks?** The direction says yes, but on the Jev items the interval barely includes 0. Jev − vanilla is +0.013 in the in-mix category (T2·T5·T9·T10) and +0.191 in the held-out category, and the difference-in-differences is +0.179 [−0.008, +0.356]. The training gain (trained − vanilla on ext) differs clearly by category: +0.017 in-mix, +0.252 held-out, difference-in-differences +0.235 [+0.147, +0.316]. All 6 held-out tasks improve significantly after Holm, while among the in-mix tasks only T10 improves significantly (T2·T5·T9 n.s.). The gain concentrates on the tasks upstream did not train on, and the small gain on the in-mix tasks fits the retention cap (§2, §5) (`results/T3arm/summary.md` §2.1, §3).

| Basis | Difference | In-mix mean [95%] | Held-out mean [95%] | Held-out − in-mix [95%] |
|---|---|---|---|---|
| Jev items | Jev − vanilla | +0.013 [−0.075, +0.138] | +0.191 [+0.054, +0.330] | +0.179 [−0.008, +0.356] |
| Jev items | trained − vanilla | +0.000 [−0.025, +0.031] | +0.262 [+0.212, +0.327] | +0.262 [+0.202, +0.333] |
| Jev items | trained − Jev | −0.013 [−0.100, +0.062] | +0.071 [−0.017, +0.163] | +0.083 [−0.035, +0.215] |
| ext | trained − vanilla | +0.017 [−0.003, +0.051] | +0.252 [+0.171, +0.328] | +0.235 [+0.147, +0.316] |

**Q3. Cost of specialisation.** Each task uses 6,400 labels (train 5,000 + calib 400 + dev 1,000). T1 uses 6,000 (dev 600), T6 6,100 (dev 700) and T8 544 (train 444 + calib 40 + dev 60). The M4 Pro MPS fp32 training loop takes 7.5 min (T7)-43.3 min (T9) on the tasks with 5,000 train items, and 1.4 min on T8 (444 items). The checkpoints are 0.85 GB for english and 0.68 GB for multilingual. Jev and vanilla use no labels and no training (`results/T3arm/summary.md` §5).

**Q4. Was it trained properly?** V1-V6 all pass. V3 passes on the difference criterion per the project owner's verdict (2026-10-08), and it also went into `summary.md` §6.2·§6.3 as the owner's verdict (`results/T3arm/summary.md` §6.2, §6.3).

| Check | Verdict | Key numbers |
|---|---|---|
| V1 zero-step identity | pass | Tensor values identical: english 206/206, multilingual 170/170. Refit alone moves ECE english 0.083 → 0.064, multilingual 0.365 → 0.179 |
| V2 upstream reproduction | pass | (a) upstream checkpoint 0.766 (published 0.766, ±0.02) (b) our training 0.747 (criterion ≥ 0.562, majority 0.461) |
| V3 label-shuffle | pass (difference criterion, owner verdict 2026-10-08) | real labels epoch 1 0.864 − permuted 0.385 = +0.479 ≥ 0.30; the alternative criterion (permuted < vanilla 0.612) is also met. The strict criterion (permuted ≤ majority + 0.05 = 0.346) is missed by +0.039, recorded as a deviation from the plan |
| V4 format identity | pass | 10 tasks, inference sequence·token match 250/250 |
| V5 smoke | pass | driver SMOKE STEP OK 163, FAILED 0 |
| V6 leakage | pass | 10 tasks, intersection of train·dev·calib with the evaluation texts: exact 0 / normalized 0 |

- The training-failure flag (§4: dev below epoch 0 in every epoch) was raised on T5·T9·T10, and none of the three is a pipeline failure. T5 is contamination of the dev baseline: dev is the train split of BoolQ, which is in upstream's training mix, so vanilla dev 0.986 is inflated relative to validation ext 0.834. T9 is a ceiling effect (vanilla dev 0.996; the difference is 1 row out of 1,000). T10 is a mismatch in the dev label distribution (dev follows the natural distribution, while train·ext are close to uniform) (`results/T3arm/summary.md` §6.1, the "Found during the main training run" sections of `results/T3arm/PREP_20261008.md`).
- Two diagnostics need attention: T10's option-order flip is high at 0.175 [0.105, 0.250], and T6's train − dev gap is large at 0.142 (`results/T3arm/summary.md` §6.1).
- Two T1 runs with the same setup (identical script·items·seed·arguments) split on test, 0.747 vs 0.690 (by label). The paired comparison is b/c 217/98, exact McNemar p=1.7e-11. The cause is the nondeterminism of MPS training (the micro-batch losses first diverge at micro-batch 12). So the trained numbers are a sample of one run per task. The results of the replicate run with a different seed are under "Replicate run" below (`results/T3arm/summary.md` §6.4, §7).

**Calibration separation.** With vanilla + task T (a 0-step export that puts only the temperature fitted on that task's calib into the base weights), the calibration difference of trained − vanilla was split into a refit effect and a training effect. Its answers are the same as vanilla's (correctness agrees on 6,736/6,736), so the accuracy comparison is unchanged. On ext, the refit effect on ECE is larger than the training effect for T1·T2·T3·T6·T7·T10 (e.g. T3 −0.336 vs +0.002). On Brier, the training effect lowers it more than the refit effect on all 6 held-out tasks (e.g. T8 −0.087 vs −0.382). T5's calibration worsening comes from the refit (ext ECE refit +0.055, training −0.010). We read this as the fitted temperature not fitting validation, because the calib rows are the train split of BoolQ, which is in upstream's training mix (interpretation). For T1·T8 the fitted T is clipped to the laya load range (T1 choice 7.613 → 5.000, noul 10.000 → 5.000, T8 noul 10.000 → 5.000) (`results/T3arm/summary.md` §4.3).

| Task | Jev items ECE: refit / training | Jev items Brier: refit / training | ext ECE: refit / training | ext Brier: refit / training |
|---|---|---|---|---|
| T1 typed-decisions | −0.076 / +0.051 | −0.067 / −0.303 | −0.138 / +0.077 | −0.064 / −0.250 |
| T2 AG News | −0.019 / −0.052 | −0.002 / +0.043 | −0.012 / −0.006 | −0.000 / +0.001 |
| T3 DAIR Emotion | +0.034 / −0.135 | −0.002 / −0.334 | −0.336 / +0.002 | −0.228 / −0.470 |
| T4 Banking77-10 | +0.005 / −0.143 | −0.012 / −0.265 | +0.004 / −0.063 | +0.001 / −0.151 |
| T5 BoolQ | +0.039 / −0.039 | +0.054 / −0.036 | +0.055 / −0.010 | +0.035 / +0.003 |
| T6 SST-5 | −0.127 / +0.041 | −0.084 / −0.226 | −0.226 / −0.013 | −0.139 / −0.194 |
| T7 MASSIVE intent-10 | −0.133 / −0.009 | −0.060 / −0.352 | −0.093 / −0.045 | −0.054 / −0.240 |
| T8 prompt-injections | −0.055 / −0.147 | −0.065 / −0.302 | −0.055 / −0.173 | −0.087 / −0.382 |
| T9 Enron spam | −0.010 / +0.022 | −0.004 / +0.029 | +0.000 / −0.001 | +0.000 / +0.003 |
| T10 support tickets | −0.091 / +0.022 | −0.042 / +0.019 | −0.113 / −0.034 | −0.050 / −0.045 |

**Replicate run (seed 14).** Run 2 is training with the same setup as the main training run, with only the torch seed changed to 14, and all 10 tasks finished. T9·T10 were stopped by memory contention with another project, then restarted by the watcher at 2026-10-08 22:58:42 and finished with rc 0 at 2026-10-09 00:23:20 (no contention; open question 11). Of the 30 verdicts (10 tasks × 3 comparisons), 27 are confirmed and 3 are inconsistent. The inconsistent ones are T4 Jev items trained vs vanilla (run 1 significant 0.0312, run 2 n.s. 0.0547), T8 Jev items trained vs Jev (run 1 n.s. 0.1934, run 2 trained significantly better 0.0391) and T8 Jev items trained vs vanilla (run 1 n.s. 0.1504, run 2 significant 0.0312). ext trained vs vanilla is confirmed on all 10 tasks. In run 2, Jev was significantly better on T5 before correction (b/c 1/10, p=0.0117; 0.1055 after Holm, n.s.). The between-run difference in ext accuracy is significant only on T1 (b/c 117/214, p=1.1e-07); the other 9 tasks have p ≥ 0.55 (`results/T3arm/summary.md` §7.1, §7.2).

| Task | Category | Jev items accuracy: run 1 / run 2 | ext accuracy: run 1 / run 2 | ext run 1 vs run 2: b/c, p | Decision agreement: trained vs Jev / trained vs vanilla / ext |
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

- **Nature of the 3 inconsistent verdicts.** All three are n=40 Jev-item comparisons with Holm p near 0.05. In the interim aggregate, when run 2 had an 8-task family, T6 Jev items trained vs vanilla was inconsistent and then became confirmed with the 10-task family, while T4 went the other way, from confirmed to inconsistent. Such borderline verdicts are sensitive to the seed and the Holm family size, so, per the owner decision, only verdicts on which both runs agree are confirmed.
- Run 2's ext trained − vanilla is +0.020 in-mix, +0.257 held-out, difference-in-differences +0.238 [+0.144, +0.325], almost the same as run 1 (+0.235 [+0.147, +0.316]) (`results/T3arm/summary.md` §7.3).
- The test accuracies (by label) of the three T1 runs are 0.747 for the preparation V2(b), 0.690 for main training run 1 and 0.735 for run 2. Run 2 does not differ significantly from V2(b) (b/c 118/96, p=0.1510) and is higher than run 1 (main training run vs run 2 b/c 117/214, p=1.1e-07, difference −0.049 [−0.069, −0.028]). Of the three runs, the main training run's T1 is the lowest (`results/T3arm/summary.md` §7.4).

**Follow-up work.** The calibration-separation columns (`results/T3arm/calib_sep/`), the T9·T10 Jev measurement (`results/F/jev_cmp/sessions/S7_20261008/`) and the seed 14 replicate run (`results/T3arm/rep_s14/`) are all done. Only the 27 verdicts on which the two runs agree are confirmed; the 3 inconsistent ones are not. What remains is the manual check of the T10 labels (open question 12).

---

## Open questions / assumptions

1. **Jev measurement of T9·T10 (80 requests, within the session cap of 100).** Decided after seeing the Laya results. Without it, the in-mix tasks in the Jev category aggregates remain the two tasks T2·T5.
   - **Resolved (2026-10-08).** In session S7 (`results/F/jev_cmp/sessions/S7_20261008/`) all 80 requests succeeded (5xx·429 0, site cumulative 518). T9 is 40/40 for both Jev and vanilla; T10 is Jev 0.250, vanilla english 0.300 and multilingual 0.450, all n.s. Jev's in-mix category became T2·T5·T9·T10 (§9 Q1).
2. **T8 × 3 epochs.** The option the project owner chose is "up to 5 thousand items per task × 2 epochs". T8 has only 546 train rows, so even at 3 epochs its item-pass count is at most 1/6 of the other tasks'. But it exceeds the epoch cap, so on a strict reading it is changed to 2 epochs.
   - **Resolved (2026-10-08).** At the start of the main training run, T8 was also switched to 2 epochs (`epochs_of` in `poc/finetune/run_all_tasks.sh`), and the project owner confirmed 2 epochs (the "Defaults applied at the start of the main training run" and "Owner decision" sections of `results/T3arm/PREP_20261008.md`).
3. **S2 duration.** If the V5 measurement puts the S2 estimate above 5 hours, the project owner is notified. The default is to run unattended with the settings unchanged. The alternative is to cut train to 2,500 items for the 4 long-input tasks.
   - **Resolved (2026-10-08).** S2 took 10:57-15:01, about 4.1 hours, within the 5-hour threshold, and ran unattended with the settings unchanged (`results/T3arm/run_all_20261008-1057_driver.log`).
4. **Calibration-separation columns.** To separate the temperature refit effect from trained's calibration improvement, add a per-task zero-step export as a reference column (vanilla + task temperature). It only runs calib without training, so about 1 minute per task. The default is not to add it and only to check its size from the V1 results.
   - **Resolved (2026-10-08).** Added by owner decision. For each task, a 0-step export like V1's (base weights + temperature fitted on that task's calib) was evaluated on the Jev items and ext, with the output in `results/T3arm/calib_sep/` (`CALIB_SEP FINISHED`). The refit and training effects are in §9 "Calibration separation" and `results/T3arm/summary.md` §4.3.
5. **T1 full-budget reproduction.** To be decided: whether to reproduce 0.766 at upstream scale (about 30k questions × 4 epochs, 4-5 hours on 2xT4). The default goes up to V2(a) and V2(b).
   - **Default applied.** Only V2(a)·V2(b) were done, and both pass (§9 Q4). The full-budget reproduction was not done.
6. **Location of paper v3.** To be decided: revise `docs/10_paper_laya_vs_jev.md` or publish a new file. The default is to revise 10.
   - **Default applied.** Proceeding with a revision of 10; this is separate work from reflecting these results (§9, REPORT, dashboard).
7. **Label-count curve.** Seeing "how many labels it takes to catch up with Jev" needs training at three levels per task: 500 / 2,000 / 5,000. It is not in this scope.
   - **Default applied.** These results are a single point at 6,400 labels per task (T1 6,000, T6 6,100, T8 544) (§9 Q3).
8. **Assumptions.**
   - The script's default hyperparameters are used for every task: encoder 2.5e-5, head 1e-4 (`:266`), cosine schedule, RLCD + soft CE.
   - The length patch changes only the sequence format and leaves the loss and the optimizer as they are.
   - One model is trained per task. No multitask model is built.
   - Laya evaluation uses the CPU fp32 path in every arm.
   - **Kept (2026-10-08).** S2 ran with the four assumptions unchanged. The length patch changes only two places, the sequence budget and `model_name` (`results/T3arm/finetune_script.diff`).
9. **V3 verdict.** The strict label-shuffle criterion (permuted ≤ majority + 0.05) assumes that training collapses the base to chance, so it may not suit a base with strong zero-shot performance. So the verdict was left to the project owner.
   - **Resolved (owner verdict 2026-10-08).** Pass (difference criterion). Main training run T3 epoch 1 dev 0.864 − permuted 0.385 = 0.479 ≥ 0.30, and the alternative criterion (permuted < vanilla 0.612) is also met. The strict criterion (0.346) is missed by +0.039, recorded as a deviation from the plan. It also went into `results/T3arm/summary.md` §6.2·§6.3 as the owner's verdict.
10. **T8 split.** With no validation split, one of two options had to be chosen: a hold-out that cuts dev 60 + calib 40 from the 546 train rows (544 after filtering), or training on all rows + temperature 1.2 (no calibration).
    - **Resolved (owner decision 2026-10-08).** The hold-out (train 444 + dev 60 + calib 40) is kept, and 2 epochs are confirmed. This is exactly what the main training run applied, so there is no retraining.
11. **Replicate training run.** Retraining T1 with the same setup split on test, 0.747 vs 0.690 (by label) (MPS nondeterminism, §9 Q4). So the trained numbers are a sample of one run per task.
    - **Resolved (2026-10-09).** All 10 tasks were trained once more with the same setup as the main training run, with only the torch seed changed to 14 (`results/T3arm/rep_s14/`, checkpoints `poc/finetune/ckpt_t3arm_rep_s14/` (not included in the public repository)). Of the 30 verdicts, 27 are confirmed and 3 inconsistent (§9 "Replicate run"). T9 was stopped at 2026-10-08 19:37 by memory contention with another project's experiment; the watcher `poc/finetune/autostart_rep_t9t10.sh` restarted T9·T10 at 22:58:42, and they finished with rc 0 at 2026-10-09 00:23:20 (no contention; `results/T3arm/rep_s14/autostart.log`, `results/T3arm/PREP_20261008.md` "Replicate run: T9 stop and automatic restart"). Since a verdict is confirmed only when both runs reach the same conclusion, the 3 inconsistent ones are not confirmed.
12. **T10 label quality.** Of the 40 Jev-item rows, 18/40 are wrong for all four systems (Jev, vanilla english, vanilla multilingual, trained). The S7 analysis read many of the errors as cases where the gold queue does not match the queue descriptions given in the question (interpretation).
    - **Pending (manual check needed).** Until a person rechecks those rows, T10 accuracy is not read as routing ability (`results/T3arm/summary.md` §1.6, `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md`).

**English** | [한국어](11_three_arm_plan.ko.md)
