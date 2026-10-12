# metrics_extra paired

`scripts/metrics_extra.py paired results/C/schemas_v2/20261002-1732_multilingual_router_v1_dev.json results/C/schemas_v2/20261002-1733_multilingual_router_v2c_dev.json --split dev --out results/C/schemas_v2/metrics/paired_v1_v2c.md --json results/C/schemas_v2/metrics/paired_v1_v2c.json` (2026-10-02T17:35:26+0900)

A = `results/C/schemas_v2/20261002-1732_multilingual_router_v1_dev.json`, B = `results/C/schemas_v2/20261002-1733_multilingual_router_v2c_dev.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| domain | dev | 250 | 0.560 | 0.540 | -0.020 [-0.070, +0.030] | 23 | 18 | 0.5327 | 0.684 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/C/schemas_v2/20261002-1732_multilingual_router_v1_dev.json | multilingual | 0.3.23 | a8223a39cd879c94a60eb0bd9c30fa56813065d255a3ddd54593debab3102536 | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 250} |
| results/C/schemas_v2/20261002-1733_multilingual_router_v2c_dev.json | multilingual | 0.3.23 | 4c1a473e414e59cb683d8c36f5289147c4932f1658b788ec71b5ff72b95f38b4 | c26e216fda3fd2057ae3ed4baaf68a885267d65ad57a21a00e98a3dccf95a073 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 250} |
