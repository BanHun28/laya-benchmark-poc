# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1645_multilingual_ko_klue_ynat_7.json results/B/20261002-1650_multilingual_ko_klue_ynat_7_en-desc_dev.json --split dev --out results/B/metrics/paired_ablation_ko_klue_ynat_7_en-desc.md --json results/B/metrics/paired_ablation_ko_klue_ynat_7_en-desc.json` (2026-10-02T17:05:34+0900)

A = `results/B/20261002-1645_multilingual_ko_klue_ynat_7.json`, B = `results/B/20261002-1650_multilingual_ko_klue_ynat_7_en-desc_dev.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| topic | dev | 245 | 0.612 | 0.637 | +0.024 [-0.025, +0.074] | 16 | 22 | 0.4177 | 0.780 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1645_multilingual_ko_klue_ynat_7.json | multilingual | 0.3.23 | 52c1af160c0433405763a919c593afea3d4f62c51c3d893a84b6ea2610da991f | 2eec39b823fd3a6eec8d54cb1bfb8caafccd93375fe2ef33c608d232ad37f260 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 255, "dev": 245} |
| results/B/20261002-1650_multilingual_ko_klue_ynat_7_en-desc_dev.json | multilingual | 0.3.23 | 8b8735f1fbbb4353a7bab7f2f9ed379ff6e86a6757807c35527be3deeea0d099 | 76a972f1309983a590e9a2c459a4645dea8fd9b34d86a9f4956d2114d741d1f9 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 245} |
