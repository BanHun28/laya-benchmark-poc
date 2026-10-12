# metrics_extra parity

`scripts/metrics_extra.py parity results/B/20261002-1647_multilingual_ko_massive_scenario_18.json results/B/20261002-1648_router_ko_massive_scenario_18.json --out results/B/metrics/parity_ko_massive_scenario_18_router.md --json results/B/metrics/parity_ko_massive_scenario_18_router.json` (2026-10-02T17:05:32+0900)

Reference `results/B/20261002-1647_multilingual_ko_massive_scenario_18.json`. Δp over every option probability (noul: p(true)).

| other | n | argmax agreement | flips | max abs Δp | mean abs Δ answer_confidence |
|---|---|---|---|---|---|
| results/B/20261002-1648_router_ko_massive_scenario_18.json | 100 | 1.0000 | 0 | 0.0000 | 0.0000 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1647_multilingual_ko_massive_scenario_18.json | multilingual | 0.3.23 | 28694e08bfed61ee6e4cf5a02bb024c33ffb7c3228012267d4a022f3de0ac03e | 7bf1c9b1b314f6bdd03e49cbcd471106c2a7209c06407698e82bcdb182f30a44 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 51, "dev": 49} |
| results/B/20261002-1648_router_ko_massive_scenario_18.json | router (auto) | 0.3.23 | 28694e08bfed61ee6e4cf5a02bb024c33ffb7c3228012267d4a022f3de0ac03e | 7bf1c9b1b314f6bdd03e49cbcd471106c2a7209c06407698e82bcdb182f30a44 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 51, "dev": 49} |
