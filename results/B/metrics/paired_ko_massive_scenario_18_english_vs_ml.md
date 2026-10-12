# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1648_english_ko_massive_scenario_18.json results/B/20261002-1647_multilingual_ko_massive_scenario_18.json --out results/B/metrics/paired_ko_massive_scenario_18_english_vs_ml.md --json results/B/metrics/paired_ko_massive_scenario_18_english_vs_ml.json` (2026-10-02T17:05:32+0900)

A = `results/B/20261002-1648_english_ko_massive_scenario_18.json`, B = `results/B/20261002-1647_multilingual_ko_massive_scenario_18.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| scenario | all | 100 | 0.310 | 0.520 | +0.210 [+0.085, +0.335] | 12 | 33 | 0.0025 | 0.220 | 1.00 |
| scenario | dev | 49 | 0.347 | 0.551 | +0.204 [+0.008, +0.400] | 8 | 18 | 0.0755 | 0.204 | 1.00 |
| scenario | test | 51 | 0.275 | 0.490 | +0.216 [+0.059, +0.372] | 4 | 15 | 0.0192 | 0.235 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1648_english_ko_massive_scenario_18.json | english | 0.3.23 | 28694e08bfed61ee6e4cf5a02bb024c33ffb7c3228012267d4a022f3de0ac03e | 7bf1c9b1b314f6bdd03e49cbcd471106c2a7209c06407698e82bcdb182f30a44 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 51, "dev": 49} |
| results/B/20261002-1647_multilingual_ko_massive_scenario_18.json | multilingual | 0.3.23 | 28694e08bfed61ee6e4cf5a02bb024c33ffb7c3228012267d4a022f3de0ac03e | 7bf1c9b1b314f6bdd03e49cbcd471106c2a7209c06407698e82bcdb182f30a44 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 51, "dev": 49} |
