# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1647_multilingual_ko_massive_scenario_18.json results/B/20261002-1650_multilingual_ko_massive_scenario_18_en-desc_dev.json --split dev --out results/B/metrics/paired_ablation_ko_massive_scenario_18_en-desc.md --json results/B/metrics/paired_ablation_ko_massive_scenario_18_en-desc.json` (2026-10-02T17:05:34+0900)

A = `results/B/20261002-1647_multilingual_ko_massive_scenario_18.json`, B = `results/B/20261002-1650_multilingual_ko_massive_scenario_18_en-desc_dev.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| scenario | dev | 49 | 0.551 | 0.429 | -0.122 [-0.244, -0.001] | 8 | 2 | 0.1094 | 0.633 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1647_multilingual_ko_massive_scenario_18.json | multilingual | 0.3.23 | 28694e08bfed61ee6e4cf5a02bb024c33ffb7c3228012267d4a022f3de0ac03e | 7bf1c9b1b314f6bdd03e49cbcd471106c2a7209c06407698e82bcdb182f30a44 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 51, "dev": 49} |
| results/B/20261002-1650_multilingual_ko_massive_scenario_18_en-desc_dev.json | multilingual | 0.3.23 | fbd46b83f67a2f981121c3dcf6d258a825593d0f8a2eb149ce7708335c3f6715 | 233520130f429820bf54b950d333db61a991e637addf592f3925b18c0245e85e | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 49} |
