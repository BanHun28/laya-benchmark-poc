# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1646_typed-decisions_ko_klue_ynat_7.json results/B/20261002-1645_multilingual_ko_klue_ynat_7.json --out results/B/metrics/paired_ko_klue_ynat_7_typed-decisions_vs_ml.md --json results/B/metrics/paired_ko_klue_ynat_7_typed-decisions_vs_ml.json` (2026-10-02T17:05:32+0900)

A = `results/B/20261002-1646_typed-decisions_ko_klue_ynat_7.json`, B = `results/B/20261002-1645_multilingual_ko_klue_ynat_7.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| topic | all | 500 | 0.234 | 0.634 | +0.400 [+0.348, +0.452] | 28 | 228 | 3.8e-40 | 0.264 | 1.00 |
| topic | dev | 245 | 0.241 | 0.612 | +0.371 [+0.295, +0.448] | 17 | 108 | 2.2e-17 | 0.257 | 1.00 |
| topic | test | 255 | 0.227 | 0.655 | +0.427 [+0.357, +0.498] | 11 | 120 | 2.6e-24 | 0.271 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1646_typed-decisions_ko_klue_ynat_7.json | typed-decisions | 0.3.23 | 52c1af160c0433405763a919c593afea3d4f62c51c3d893a84b6ea2610da991f | 2eec39b823fd3a6eec8d54cb1bfb8caafccd93375fe2ef33c608d232ad37f260 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 255, "dev": 245} |
| results/B/20261002-1645_multilingual_ko_klue_ynat_7.json | multilingual | 0.3.23 | 52c1af160c0433405763a919c593afea3d4f62c51c3d893a84b6ea2610da991f | 2eec39b823fd3a6eec8d54cb1bfb8caafccd93375fe2ef33c608d232ad37f260 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 255, "dev": 245} |
