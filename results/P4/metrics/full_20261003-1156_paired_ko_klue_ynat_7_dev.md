# metrics_extra paired

`scripts/metrics_extra.py paired results/P4/20261002-2014_multilingual_ko_klue_ynat_7_dev.json results/P4/full_20261003-1156_ft-v1_ko_klue_ynat_7_dev.json --split all --out results/P4/metrics/full_20261003-1156_paired_ko_klue_ynat_7_dev.md --json results/P4/metrics/full_20261003-1156_paired_ko_klue_ynat_7_dev.json` (2026-10-03T12:40:28+0900)

A = `results/P4/20261002-2014_multilingual_ko_klue_ynat_7_dev.json`, B = `results/P4/full_20261003-1156_ft-v1_ko_klue_ynat_7_dev.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| topic | all | 245 | 0.612 | 0.633 | +0.020 [-0.031, +0.072] | 18 | 23 | 0.5327 | 0.759 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/P4/20261002-2014_multilingual_ko_klue_ynat_7_dev.json | multilingual | 0.3.23 | e47494226f0464463ec0dfbf8352bf6884a8297581b5283efd3803c8769d16ae | 2eec39b823fd3a6eec8d54cb1bfb8caafccd93375fe2ef33c608d232ad37f260 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 245} |
| results/P4/full_20261003-1156_ft-v1_ko_klue_ynat_7_dev.json | ft-v1 | 0.3.23 | e47494226f0464463ec0dfbf8352bf6884a8297581b5283efd3803c8769d16ae | 2eec39b823fd3a6eec8d54cb1bfb8caafccd93375fe2ef33c608d232ad37f260 | {"ft-v1": "local:poc/finetune/ckpt_domain8_v1 (base 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851)"} | pre-split copy (dev) | {"dev": 245} |
