# metrics_extra paired

`scripts/metrics_extra.py paired results/C/schemas_v2/20261002-1733_multilingual_router_v2a_dev.json results/C/schemas_v2/20261002-1734_multilingual_router_v2d_dev.json --split dev --out results/C/schemas_v2/metrics/paired_v2a_v2d.md --json results/C/schemas_v2/metrics/paired_v2a_v2d.json` (2026-10-02T17:35:26+0900)

A = `results/C/schemas_v2/20261002-1733_multilingual_router_v2a_dev.json`, B = `results/C/schemas_v2/20261002-1734_multilingual_router_v2d_dev.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| domain | dev | 250 | 0.536 | 0.516 | -0.020 [-0.066, +0.026] | 20 | 15 | 0.4996 | 0.704 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/C/schemas_v2/20261002-1733_multilingual_router_v2a_dev.json | multilingual | 0.3.23 | bc18386eecd77d08d99c246d67d7c09d1fd9fcac2225ac55da487a6b18298b81 | c8b97badf47449eb3891c31f0d55e9633406ff5d34673b6edbe69024c9b65702 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 250} |
| results/C/schemas_v2/20261002-1734_multilingual_router_v2d_dev.json | multilingual | 0.3.23 | da73a646a05a92a211f823c73dfb936a774ce8cdbbc7356527685507c43a0147 | 5bdac5b744e7fc4bffdb32e9856f8f52f116f8a51a8bdb4c62c8500ea94283e6 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 250} |
