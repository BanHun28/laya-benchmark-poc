# metrics_extra parity

`scripts/metrics_extra.py parity results/B/20261002-1645_multilingual_ko_klue_ynat_7.json results/B/20261002-1647_router_ko_klue_ynat_7.json --out results/B/metrics/parity_ko_klue_ynat_7_router.md --json results/B/metrics/parity_ko_klue_ynat_7_router.json` (2026-10-02T17:05:32+0900)

Reference `results/B/20261002-1645_multilingual_ko_klue_ynat_7.json`. Δp over every option probability (noul: p(true)).

| other | n | argmax agreement | flips | max abs Δp | mean abs Δ answer_confidence |
|---|---|---|---|---|---|
| results/B/20261002-1647_router_ko_klue_ynat_7.json | 500 | 1.0000 | 0 | 0.0000 | 0.0000 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1645_multilingual_ko_klue_ynat_7.json | multilingual | 0.3.23 | 52c1af160c0433405763a919c593afea3d4f62c51c3d893a84b6ea2610da991f | 2eec39b823fd3a6eec8d54cb1bfb8caafccd93375fe2ef33c608d232ad37f260 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 255, "dev": 245} |
| results/B/20261002-1647_router_ko_klue_ynat_7.json | router (auto) | 0.3.23 | 52c1af160c0433405763a919c593afea3d4f62c51c3d893a84b6ea2610da991f | 2eec39b823fd3a6eec8d54cb1bfb8caafccd93375fe2ef33c608d232ad37f260 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 255, "dev": 245} |
