# Laya benchmark and PoC

An independent benchmark and proof of concept (PoC) of [Laya](https://github.com/NandhaKishorM/laya) 0.3.23 (upstream commit 4aa6761, checkpoint bundle `convaiinnovations/laya` @ 55cf4c4), an open-source non-autoregressive "System-1" decision engine that returns probability distributions over typed decisions (choice, score, noul) in a single encoder forward pass. The repository holds a Korean applicability study with a Korean domain-routing PoC (Tracks A–F, stages P0–P4, a fine-tuned router and a PoC service), a controlled comparison with Jev, TypeSafe's hosted decision API, on tasks T1–T10, and a 3-arm study (Jev vs vanilla Laya vs per-task fine-tuned Laya) with a seed-14 replicate run. All Laya runs used one Apple M4 Pro (48 GB, macOS 26.6.2).

> **Disclaimer.** This is an independent project, not affiliated with Laya's authors (Convai Innovations) or with TypeSafe. Jev was measured through the independent public playground [jevplayground.com](https://jevplayground.com), not through the Jev API; the model version is not shown, probabilities are rounded to the second decimal place, and the samples are small (n=40 per task in the controlled comparison).

## Key results

- **Zero-shot, Jev is more accurate.** On the same state, question and option strings, Jev was significantly ahead on 4 of the 8 tasks T1\~T8 by exact McNemar test (2 after Holm correction, T1 and T7), and Laya on none; the gap is especially large on instruction-style and multilingual tasks. Macro accuracy: Jev 0.828, Laya english 0.646, multilingual 0.598, Router 0.661 (`docs/10_paper_laya_vs_jev.md` Abstract, `results/REPORT.md` §0).
- **Latency and cost reflect different deployments.** Jev's displayed playground latency has a median of 226 ms (browser POST 465 ms, including the internet round trip), while local Laya takes 13.8\~86.6 ms in-process and 20.1\~50.7 ms over localhost HTTP for 1 question; this is not a comparison of model speed. Jev costs $0.0197 per 1,000 decisions (unit price quoted from a 3rd party, to be verified), and Laya has no token charges (`results/REPORT.md` §0).
- **Confidence thresholds must be fitted per task.** The meaning of Jev's probabilities differs by question format (single choice: 59% of errors have top ≥ 0.90; multi-question T1: underconfident; T10: ECE 0.623). For both systems, the thresholds of confidence-based automation must be refitted per task on held-out data (`docs/10_paper_laya_vs_jev.md` Abstract, §4.3).
- **With per-task fine-tuning, Laya is not significantly behind Jev.** Laya fine-tuned on about 6,400 labels per task (7.5\~43.3 minutes of M4 Pro MPS training; T8 1.4 minutes) showed no significant difference from Jev on any of the 10 tasks after Holm correction in main training run 1, and was significantly better on T8 only in replicate run 2; in neither run was Jev significantly ahead after Holm correction. This compares a specialized Laya with zero-shot Jev (`docs/10_paper_laya_vs_jev.md` Abstract).
- **The training gain concentrates on tasks outside Laya's training mix.** On the extended evaluation set (ext), trained − vanilla is +0.017 for the 4 in-mix tasks (in Laya's training mix as disclosed by upstream) and +0.252 for the 6 held-out tasks, a difference-in-differences of +0.235 [+0.147, +0.316] in run 1 (run 2: +0.020, +0.257, +0.238 [+0.144, +0.325]) (`docs/10_paper_laya_vs_jev.md` Abstract).
- **Verdicts are confirmed only when both training runs agree.** Of 30 verdicts (10 tasks × 3 comparisons), 27 are confirmed and 3 are inconsistent, all n=40 Jev-item comparisons with Holm p near 0.05. MPS training is not bit-for-bit deterministic: three T1 runs of the same pipeline gave 0.747 / 0.690 / 0.735 (`docs/11_three_arm_plan.md` §9).
- **Korean domain routing needs fine-tuning.** Zero-shot 8-domain routing scores 0.492 on the test half. ft-v1, fine-tuned for 36 minutes on 11,094 rows of MASSIVE ko train, reaches 0.900 on the same test half (0.913 on the full test of 2,917 rows), ECE 0.053 and option-order flip 0.037; the PoC verdict is Conditional Go, premised on a fine-tuning pipeline (`results/REPORT.md` §0).

## Documents

Reading order:

1. [`results/REPORT.md`](results/REPORT.md): the results report for every track, with the Laya vs Jev comparison (§0a) and the 3-arm comparison (§0b).
2. [`docs/10_paper_laya_vs_jev.md`](docs/10_paper_laya_vs_jev.md): the paper (v3), covering the zero-shot comparison and the 3-arm study.
3. [`docs/11_three_arm_plan.md`](docs/11_three_arm_plan.md): the 3-arm plan, with its results in §9.
4. [`docs/00_README.md`](docs/00_README.md): the index of the plans (scope, document map, execution order, Go/No-Go matrix).

| Document | Title |
|---|---|
| [`docs/00_README.md`](docs/00_README.md) | Laya benchmarking · PoC execution guide |
| [`docs/01_laya_analysis.md`](docs/01_laya_analysis.md) | Laya analysis: architecture, API, published numbers, limits |
| [`docs/02_environment_setup.md`](docs/02_environment_setup.md) | Environment setup |
| [`docs/03_benchmark_plan.md`](docs/03_benchmark_plan.md) | Laya benchmark plan |
| [`docs/04_korean_evalset_spec.md`](docs/04_korean_evalset_spec.md) | Korean evaluation set build specification |
| [`docs/05_poc_plan.md`](docs/05_poc_plan.md) | PoC plan: Korean domain router (scenario C) |
| [`docs/06_templates.md`](docs/06_templates.md) | Record templates |
| [`docs/07_korean_support_audit.md`](docs/07_korean_support_audit.md) | Korean support audit: results and design implications |
| [`docs/08_paper_ko.md`](docs/08_paper_ko.md) | Paper: Korean Applicability of the Laya Multilingual System-1 Decision Engine: Zero-shot Benchmark, Fine-tuning, and a Domain-Routing PoC |
| [`docs/09_laya_vs_jev_plan.md`](docs/09_laya_vs_jev_plan.md) | Laya vs Jev small-sample comparison plan |
| [`docs/10_paper_laya_vs_jev.md`](docs/10_paper_laya_vs_jev.md) | Paper (v3): A Controlled 3-arm Comparison of Jev, vanilla Laya, and trained Laya: Zero-shot Accuracy of a Non-autoregressive Decision Engine and the Effect of Per-task Fine-tuning |
| [`docs/10_paper_laya_vs_jev_v2.md`](docs/10_paper_laya_vs_jev_v2.md) | Paper (v2, superseded by v3): A Controlled Comparison of Laya and Jev: Zero-shot Accuracy, Calibration, Multilingual Consistency, and Latency of a Non-autoregressive Decision Engine |
| [`docs/11_three_arm_plan.md`](docs/11_three_arm_plan.md) | 3-arm extension plan: Jev vs vanilla Laya vs trained Laya |

Languages:

- Each document is in English as `X.md`, with a Korean version `X.ko.md` next to it. The two are line-aligned, so a `file:line` citation holds in both.
- The Korean versions of the script-generated reports (such as `results/F/jev_cmp/summary.ko.md` and `results/T3arm/summary.ko.md`) are written by their scripts; their English versions are static translations, and regenerating a report rewrites only the Korean file.
- The PoC UI (`poc/service/ui/`), the results dashboard (`results/dashboard/index.html`) and some code comments are in Korean.

## Repository layout

| Directory | Contents |
|---|---|
| `docs/` | Plans, specifications, the Korean support audit and the papers (00–11) |
| `data/` | Evaluation sets in laya-evals JSONL with `MANIFEST.json` files (`data/evals/`): the Korean sets, the Laya vs Jev sets with their playground forms (`jev_cmp/`) and the extended sets (`jev_cmp_ext/`). Raw downloads (`data/raw/`) are not included |
| `scripts/` | Set builders, the option-order probe, latency, batch and HTTP benchmarks, calibration, metrics, the environment report and the dashboard builder |
| `results/` | Run cards, reports and metrics: Tracks `A`–`F`, `korean_support/`, `poc/` (P0–P2), `P4/`, `F/jev_cmp/` (Laya vs Jev), `T3arm/` (3-arm), `env/`, `dashboard/`, and `REPORT.md` |
| `poc/` | The PoC service (`service/`, demo UI in `service/ui/`), question schemas, the calibration payload, the shadow log, and the fine-tuning pipeline with its training rows (`finetune/`) |
| `models/` | Not included: symlinks to the downloaded checkpoints (`docs/02_environment_setup.md` §2.7) |
| `third_party/` | Not included: the upstream Laya clone at commit 4aa6761 (`docs/02_environment_setup.md` §2.5) |

Root files: `env.sh` (environment variables, `docs/02_environment_setup.md` §2.8), `LICENSE`, `NOTICE` and `DATA_LICENSES.md`.

## Reproducing

### Environment

Setup, version pins and smoke tests are in `docs/02_environment_setup.md`. The measurements used Python 3.12.12, laya 0.3.23, torch 2.14.1 and transformers 5.18.0 (`results/env/env_20261002-1333.json`), the upstream clone at commit 4aa6761 and the checkpoint bundle at revision 55cf4c4. Quality numbers are CPU fp32; fine-tuning ran on MPS.

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python "laya[serve,onnx,structured]==0.3.23" datasets pandas scikit-learn psutil matplotlib
git clone https://github.com/NandhaKishorM/laya.git third_party/laya
git -C third_party/laya checkout 4aa6761be8173de4ce6d92c31b3e40b6eaf59a7c
hf download convaiinnovations/laya --revision 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 --quiet | tee results/env/snapshot_path.txt
# models/ symlinks: docs/02_environment_setup.md §2.7. Then, in every new shell:
source env.sh
```

### Not included

The exact list is in `.gitignore`.

- Fine-tuned checkpoints, `poc/finetune/ckpt_*/` (about 20 GB). Training regenerates them, but not bit for bit (see below).
- Downloaded models (`models/`: Laya checkpoints and ONNX exports), the upstream clone (`third_party/`) and raw dataset downloads (`data/raw/`). The setup commands above and the builders below fetch the checkpoints, the clone and the datasets again at pinned revisions; the ONNX exports come from Track D (`results/D/D_run.sh`).
- PDF renderings of the documents (`*.pdf`); the Markdown files are the sources.
- Jev playground captures (screenshots, page and accessibility snapshots, network and console logs, injected scripts), Jev raw records (per-request responses, request logs, master logs, per-request timing) and Jev's per-item outputs; see "How Jev was measured" below.
- AG News-derived files: the T2 evaluation sets, the T2 training files and the S1·S1b playground records. They are excluded because of the corpus terms (`DATA_LICENSES.md`).

### Regenerating

The builders read the source datasets at pinned revisions or checksums (downloaded into `data/raw/`) and refuse to overwrite an existing set file with different bytes unless `--force` is given. To rebuild the evaluation and training sets, including the excluded T2 files:

```bash
source env.sh && export HF_HOME=$PWD/data/raw/hf && unset HF_HUB_OFFLINE
.venv/bin/python scripts/build_ko_evalsets.py all --n 500 --seed 13   # Korean sets in data/evals/ (ablation variants: docs/04 §6)
.venv/bin/python scripts/build_jev_cmp_sets.py all                    # T1-T10 sets and playground forms in data/evals/jev_cmp/
.venv/bin/python scripts/build_train_sets.py all                      # ext sets and per-task train/dev/calib rows
.venv/bin/python poc/finetune/ft_task.py items --task T2 --base english --out poc/finetune/data/t3arm/T2_english.pt
.venv/bin/python poc/finetune/ft_task.py devsub --task T2 --n 40      # T2 dev subset for the option-order probe
```

The other tasks' training items and the P4 rows and items (`poc/finetune/make_domain8_items.py rows|items`) are included. Training regenerates the checkpoints on MPS; check the 3-arm gate (`poc/finetune/READY_T3ARM`) with `PREFLIGHT_ONLY=1` first:

```bash
bash poc/finetune/run_full.sh                                # P4 ft-v1 -> poc/finetune/ckpt_domain8_v1/
PREFLIGHT_ONLY=1 bash poc/finetune/run_all_tasks.sh          # 3-arm gate check only
bash poc/finetune/run_all_tasks.sh                           # 3-arm main training run 1 -> poc/finetune/ckpt_t3arm/<task>/
SEED=14 RUN_TAG=rep_s14 bash poc/finetune/run_all_tasks.sh   # replicate run 2 (seed 14) -> poc/finetune/ckpt_t3arm_rep_s14/
```

The full command list for every track, the PoC and both comparisons is in `results/REPORT.md` §9, and the 3-arm preparation and validation commands are in `results/T3arm/PREP_20261008.md` ("Commands"). MPS training is not bit-for-bit deterministic, so retrained checkpoints differ from the measured ones; evaluating a kept checkpoint is deterministic (`results/REPORT.md` §8).

### Not runnable from a fresh clone

These read inputs that are not published:

- `results/F/jev_cmp/s6_summary.py build|verify` and `results/T3arm/t3arm_summary.py build|verify`: the Jev raw records and the T2 set; the 3-arm summary also reads the checkpoint directories for their sizes.
- The Jev session tools `results/F/jev_cmp/jev_cmp.py record|analyze|stability|t1`, the per-session `results/F/jev_cmp/sessions/*/s*_record.py` scripts and `results/F/jev_f.py record|analyze`: the per-request records and browser dumps.
- `results/poc/P2_offline_check.py` and the PoC service `poc/service/app.py`: the ft-v1 checkpoint `poc/finetune/ckpt_domain8_v1/`. The service also refuses to start when the hash of the checkpoint's `rl_agent_config.json` differs from the one its threshold T 0.907 was chosen for (`poc/service/policy.py`, `docs/05_poc_plan.md` §5).

The published outputs of both syntheses (`summary.json` and `summary.ko.md`) were built from the full local inputs, and the documents record 0 `verify` mismatches (`docs/09_laya_vs_jev_plan.md` §8, `docs/11_three_arm_plan.md` §9).

## How Jev was measured

Jev was called only through the playground's own endpoint (`POST /api/evaluate` of jevplayground.com, Model ID `typesafe-ai/jev`, version not shown), at human pace, with the same state bytes, question and option strings that Laya reads. The Korean pilot (n=24) was run by hand; sessions S1, S1b, S2–S5 and S7 used browser automation (Playwright MCP, Chromium) that filled the form from the playground form files and clicked Run only when the payload hash matched. Operating rules (`docs/09_laya_vs_jev_plan.md` §2):

- at least 10 s between requests (the smallest observed gap was 12.1 s);
- per-session request caps, and a daily cap of 100 requests until the owner lifted it on 2026-10-07;
- on a 5xx, one retry of that item after 60 s; on a 429, a limit message or a captcha, an immediate stop of the session;
- every request, successful or not, written to the request logs; in the automated sessions the sent body was compared byte for byte with the form payload (411/411 and 80/80 identical).

In total the site received 518 requests between 2026-10-06 and 2026-10-08, including the 25 of the pilot and 2 status checks (`docs/09_laya_vs_jev_plan.md` §7.2); 2 returned HTTP 502 and none returned HTTP 429 (§9 of the same document).

Jev's raw records (per-request responses, request logs and timing), the playground captures and Jev's per-item outputs are not published (owner decision 2026-10-12). The documents keep the aggregated results and the method, and each session's procedure is in its run card (`results/F/jev_cmp/sessions/S*/S*_run_card.md`; for the pilot, `results/F/F_jev_20261006.md`).

## License

Code and documents are licensed under Apache-2.0 (`LICENSE`); `NOTICE` records the files derived from Laya (Convai Innovations, Apache-2.0). Data files derived from public datasets, and the other third-party material listed in `DATA_LICENSES.md`, keep their original licenses, which the Apache-2.0 grant does not cover; some are ShareAlike (CC BY-SA) or NonCommercial (CC BY-NC 4.0). AG News-derived files are not included.

**English** | [한국어](README.ko.md)
