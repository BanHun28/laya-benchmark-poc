# 06. Record templates

**Purpose**: Make every run and decision of the benchmark and PoC leave a record in the same format, so that comparison with upstream figures, reproduction and the Go/No-Go verdict are possible from the documents alone.
**Prerequisite documents**: `02_environment_setup.md` §7 (recording conventions), `03_benchmark_plan.md` (Tracks A \~ F), `04_korean_evalset_spec.md` (datasets), `05_poc_plan.md` (PoC phases).
**Outputs**: `results/<track>/<run-id>.md` (Run Card), `results/REPORT.md`, `docs/decisions/ADR-<n>.md`, `data/handwritten/<set>_label_policy_v<n>.md`.

Copy the templates as they are and fill them in. Do not delete empty items; write `n/a` and the reason. Keep numbers inside tables only.

---

## 1. Experiment run record (Run Card)

File name: `results/<track>/<YYYYMMDD-HHMM>_<model>_<dataset>.md`. It pairs with the `.json` of the same name (`laya-evals --json` or our script output). `<track>` is `A`\~`F` or `poc`.

```markdown
# Run <YYYYMMDD-HHMM>_<model>_<dataset>

| Field | Value |
|---|---|
| run_id | <YYYYMMDD-HHMM>_<model>_<dataset> |
| Date / start time | YYYY-MM-DD HH:MM (KST) |
| Track / PoC phase | A~F or poc-phase-N |
| Hypothesis | H<n> (number in 01_laya_analysis.md) |
| Purpose (one line) | What the run is meant to check |
| Command | `source env.sh && .venv/bin/laya-evals run ... --json results/<track>/<run-id>.json` (exactly as run; `.venv/` is not included in the public repository) |
| Environment record | results/env/env_<YYYYMMDD-HHMM>.json |
| Checkpoint | english / multilingual / typed-decisions, revision 55cf4c4... (report config.revisions or env JSON checkpoints.*.snapshot_sha) |
| Dataset | data/evals/<set>.jsonl, n=<rows>, dataset_sha256=<report config.dataset_sha256>, questions_sha256=<config.questions_sha256> |
| Device / precision / threads | cpu fp32 or mps (dtype_for(rows)=fp32|fp16), intra-op N, inter-op 1 |
| Parameters | batch_size=, sort_by_length=, min_confidence=, max_len=, head_max_len=, other |
| Repeats / warm-up | discard <k> warm-up runs, <n> measured runs, aggregate median/p95 |
| Elapsed time | load <s>, run <s> |

## Results

| Metric | Value | upstream reference (source) | Difference | Notes |
|---|---|---|---|---|
| choice_accuracy | | | | |
| noul_accuracy | | | | |
| score_mae | | | | |
| ece | | | | |
| mean_confidence | | | | |
| latency_p50_ms / p95 | | n/a (different hardware) | | |
| (Track-specific metric) | | | | |

## Outputs
- results/<track>/<run-id>.json
- results/<track>/<run-id>.md (the file written by laya-evals --markdown, if any)
- Paths of plots and logs

## Anomalies / notes
- Whether there were warning messages (temperature clamp, tokenizer patch, CPU fallback), with their original text
- What differed from expectations; whether it was rerun and why

## Next actions
- Plans this result changes (which items of 03/05), run_ids of additional runs
```

Writing rules: write the `upstream reference` with both the number and the source (e.g. `0.470 (BENCHMARKS.md §Languages, ko row)`). Latency is not comparable because the hardware differs, so leave it `n/a` and compare only with earlier run_ids on our machine. Always copy the two dataset hashes from the report JSON; do not compute them by hand (source: docs/evals.md "Run identity").

---

## 2. Results report (REPORT.md)

File: `results/REPORT.md`. Update and commit it whenever a Track finishes. Every numeric cell carries its supporting run_id as a footnote or in parentheses.

```markdown
# Laya benchmark · PoC results report

## 0. Summary (3 lines)
1. Quality: ...
2. Speed and operations: ...
3. Verdict: Go / Conditional Go / No-Go, 1 key reason

## 1. Environment
- Machine, OS, Python, laya/torch/transformers versions (results/env/env_*.json)
- Checkpoint revisions, upstream commit 4aa6761
- Device roles: CPU fp32 = quality reference, MPS = latency (parity run_id)

## 2. Results by Track
### Track A reproduction | Set | Metric | Measured | upstream | run_id |
### Track B Korean quality | Set | Checkpoint | Metric | Value | majority | run_id |
### Track C robustness | Probe | Value | upstream reference | run_id |
### Track D performance | Configuration | p50 | p95 | Throughput | run_id |
### Track E calibration | Bucket | ECE before/after | coverage@acc | run_id |
### Track F baselines | Baseline | Metric | Value | vs laya | run_id |

## 3. Hypothesis verdicts
| Hypothesis | Verdict (supported/rejected/undecided) | Supporting run_id | One-line interpretation |
|---|---|---|---|
| H1 | | | |
| ... H10 | | | |

## 4. Go/No-Go matrix
Copy the criteria table of 00_README.md §6 and fill in the measured value, verdict and run_id for each criterion.

## 5. Limitations and caveats
- Precision: the difference between MPS fp16 (5 rows or more) and CPU fp32 (parity results)
- Sample size: at n=100 the 95 % confidence interval around an accuracy of 0.5 is about ±0.10. Instead of comparing single numbers, use a bootstrap CI or a paired test on the same items (upstream used McNemar; source: research/README.md "Headline findings")
- Possible data leakage: whether a source is in the upstream training mix (the held out labels in BENCHMARKS.md §Themes)
- Sensitivity to option order and wording (Track C figures)

## 6. How to reproduce
- List of commands to run after completing §2 ~ §3 of document 02 (in run_id order)

## 7. Appendix
- Full list of run_ids and file paths
- List of ADRs
```

**Dashboard.** `results/dashboard/index.html` is generated by `scripts/build_dashboard.py` from the same result JSON as REPORT.md (`03_benchmark_plan.md` §12 item 11). Hypothesis verdicts are recorded only in `results/verdicts.json` and Go/No-Go only in `results/go_no_go.json`; §3·§4 of REPORT.md transcribe those two files. Do not write the same verdict by hand in two places. Entry format:

```json
{"H1": {"verdict": "지지", "run_ids": ["20261010-0930_multilingual_ko_massive20"], "note": "ko 0.47 재현, en 0.71"}}
```

```json
{"G0": {"value": 0.47, "pass": true, "run_ids": ["20261010-0930_multilingual_ko_massive20"]}, "G5": {"value": null, "pass": null, "run_ids": []}}
```

`pass: null` means "not measured yet", and the dashboard leaves that cell gray. The G items that `build_dashboard.py` can compute from the report JSON are filled by the script; the rest are filled by hand.

---

## 3. Decision record (ADR-lite)

File: `docs/decisions/ADR-<nnn>-<slug>.md`. One for every choice with trade-offs (device roles, baseline update, dataset replacement, confirming the PoC scenario, scope reduction).

```markdown
# ADR-<nnn>: <title>

- Date: YYYY-MM-DD
- Status: proposed / accepted / discarded / superseded (ADR-<n>)
- Related: Track/phase, hypothesis H<n>, run_id

## Context
Which measurements or constraints called for this decision. Numbers go together with their run_id.

## Options
| Option | Pros | Cons / cost | Difficulty of reverting |
|---|---|---|---|
| A | | | |
| B | | | |

## Decision
One sentence.

## Rationale
Why this option is better than the others. State any assumptions.

## Consequences / follow-up
- Documents and scripts that change
- Review trigger (which figure would make us revisit this)
```

---

## 4. Label policy document (Label Policy)

File: `data/handwritten/<set>_label_policy_v<n>.md` (e.g. `data/handwritten/poc_triage_label_policy_v1.md`, 04_korean_evalset_spec.md §5.8). For every hand-labeled PoC set (`ko_poc_triage_v1.jsonl`, defined in `04_korean_evalset_spec.md`), write it **before** running any model and freeze its hash. Upstream's Spanish and Chinese community benches used the same principle ("label policy fixed before any model ran") (source: README.md "What's new in 0.3.23" Research item, research/benchmarks/zh_short_commands/README.md).

```markdown
# Label Policy: <set> v<n>

## Task definition
- Input unit (sentence/ticket/email), question id and type (choice / score / noul)
- Context in which the decision is used (which action it leads to)

## Label set
| Label | Inclusion criteria | Exclusion criteria | Boundary example 1 | Boundary example 2 |
|---|---|---|---|---|
| <label_a> | | | | |
| <label_b> | | | | |
| other / unknown | Clearly belongs to none of the above | | | |

## Rules for ambiguous cases
- More than one applies: priority <a> > <b> > ... (reason)
- Not enough information: the `unknown` bucket. Not excluded from the accuracy computation; reported as a separate slice (tag=ambiguous)
- Rules for negations, conditionals and quotations (linked to the negation limitation in 01_laya_analysis.md)
- score: fix the level boundaries with examples. expected is a 0-based level index (laya-evals convention; source: research/evals/fixture.jsonl, laya/evals.py ScoreMAE)

## Labeling procedure
- 2 labelers label independently → list of disagreements → adjudication record (final label, reason)
- Record the inter-labeler agreement (Cohen's kappa). Below 0.6, fix the criteria and relabel
- Labelers do not see model outputs

## Freeze
- Hash before any model run: `shasum -a 256 data/evals/<set>.jsonl` → <sha>
- Record the sha256 of this policy document in `label_policy_sha256` of `data/evals/MANIFEST.json` (04_korean_evalset_spec.md §6)
- Whether `laya-evals validate data/evals/<set>.jsonl` passes
- Freeze date and time, person responsible

## Change history
| Version | Date | Change | Affected run_ids |
|---|---|---|---|
| v1 | | Initial | |
```

If labels are corrected after the freeze, bump the version (`v2`) and leave existing runs as they are. A change of question wording that changes `questions_sha256` is also a new experiment (source: docs/evals.md "Run identity").

---

## 5. Checklists

**Before a benchmark run**
- [ ] Ran `source env.sh`, and `echo $LAYA_MODELS_DIR $LAYA_REVISION` shows the expected values (`LAYA_MODELS` must be empty, 02 §2.8)
- [ ] Left `HF_HUB_OFFLINE` as intended (unset when a download is needed)
- [ ] The latest `results/env/env_*.json` matches the current package and thread settings (otherwise regenerate it)
- [ ] Decided the number of warm-up and measured runs and wrote them in the Run Card
- [ ] Closed other load-generating processes (many browser tabs, other training, Docker)
- [ ] Power adapter connected, low-power mode off. Apple silicon changes its clock with thermal and power state, so long latency sweeps run after cooling down and under the same conditions
- [ ] The dataset hash equals the frozen hash in the label policy (`shasum -a 256`)
- [ ] Created the Run Card first (up to purpose, hypothesis and command)

**After the run**
- [ ] The `.json` and `.md` are saved in `results/<track>/`
- [ ] Filled the Run Card's result table and the two hashes from the report JSON
- [ ] Wrote the upstream reference and the difference, and candidate causes for any difference above the threshold
- [ ] Recorded warnings, fallbacks and anomalies
- [ ] Updated the corresponding Track table and the hypothesis verdict table in `results/REPORT.md`
- [ ] Regenerated the dashboard with `python scripts/build_dashboard.py` and checked the cells that changed
- [ ] Committed (changes to `results/`, `docs/`, `scripts/`)

**Before moving to the next PoC stage**
- [ ] The previous phase's acceptance criteria (05_poc_plan.md) are met in numbers, with run_ids
- [ ] Any unmet item has its scope adjustment recorded in an ADR
- [ ] The outputs the next phase depends on (datasets, question schemas, thresholds) are frozen and hashed

---

## Open questions / assumptions

1. **Assumption**: the Run Card was written on the premise that the `laya-evals` report JSON has a `config` block (`revisions`, `dataset_sha256`, `questions_sha256`, `thresholds`, `timing`). Our own scripts (Track C/D) put the same keys under the same names in their output.
2. **Open question**: the fallback when 2 labelers cannot be secured. The interim plan is to substitute labels by 1 person + self-relabeling a week later (intra-rater) and to write that kappa in the same cell.
3. **Open question**: the Go/No-Go criteria table of REPORT.md follows `00_README.md` §6. If that document changes the criteria, the "4. Go/No-Go matrix" section of the §2 template keeps only the reference, without edits.
4. **Assumption**: latency is compared only within this machine. The upstream T4/EPYC figures are cited in §5 of the report only as context.

**English** | [한국어](06_templates.ko.md)
