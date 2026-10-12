# metrics_extra parity

`scripts/metrics_extra.py parity results/B/20261002-1650_multilingual_ko_massive_intent_20opt.json results/B/20261002-1651_router_ko_massive_intent_20opt.json --out results/B/metrics/parity_ko_massive_intent_20opt_router.md --json results/B/metrics/parity_ko_massive_intent_20opt_router.json` (2026-10-02T17:05:33+0900)

Reference `results/B/20261002-1650_multilingual_ko_massive_intent_20opt.json`. Δp over every option probability (noul: p(true)).

| other | n | argmax agreement | flips | max abs Δp | mean abs Δ answer_confidence |
|---|---|---|---|---|---|
| results/B/20261002-1651_router_ko_massive_intent_20opt.json | 100 | 1.0000 | 0 | 0.0000 | 0.0000 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1650_multilingual_ko_massive_intent_20opt.json | multilingual | 0.3.23 | 4e936ea663ba6072e8e7ab0cc5a4f22784824378ce74cb1266a8f955b4efb596 | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
| results/B/20261002-1651_router_ko_massive_intent_20opt.json | router (auto) | 0.3.23 | 4e936ea663ba6072e8e7ab0cc5a4f22784824378ce74cb1266a8f955b4efb596 | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
