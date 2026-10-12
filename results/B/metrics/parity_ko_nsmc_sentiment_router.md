# metrics_extra parity

`scripts/metrics_extra.py parity results/B/20261002-1654_multilingual_ko_nsmc_sentiment.json results/B/20261002-1657_router_ko_nsmc_sentiment.json --out results/B/metrics/parity_ko_nsmc_sentiment_router.md --json results/B/metrics/parity_ko_nsmc_sentiment_router.json` (2026-10-02T17:05:33+0900)

Reference `results/B/20261002-1654_multilingual_ko_nsmc_sentiment.json`. Δp over every option probability (noul: p(true)).

| other | n | argmax agreement | flips | max abs Δp | mean abs Δ answer_confidence |
|---|---|---|---|---|---|
| results/B/20261002-1657_router_ko_nsmc_sentiment.json | 1000 | 0.9980 | 2 | 0.9274 | 0.0005 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1654_multilingual_ko_nsmc_sentiment.json | multilingual | 0.3.23 | 68efeccdcbcc93d8856be721af93e4275e344293b00ef8eb6646b12e40639f1d | c76e85a04f5bbbc4d45f27a81ec2d7a6bdf76cfc958d27be0ef78c0f07668a98 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 251, "dev": 249} |
| results/B/20261002-1657_router_ko_nsmc_sentiment.json | router (auto) | 0.3.23 | 68efeccdcbcc93d8856be721af93e4275e344293b00ef8eb6646b12e40639f1d | c76e85a04f5bbbc4d45f27a81ec2d7a6bdf76cfc958d27be0ef78c0f07668a98 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 251, "dev": 249} |
