# metrics_extra parity

`scripts/metrics_extra.py parity results/B/20261002-1700_multilingual_ko_kmhas_type_8.json results/B/20261002-1703_router_ko_kmhas_type_8.json --out results/B/metrics/parity_ko_kmhas_type_8_router.md --json results/B/metrics/parity_ko_kmhas_type_8_router.json` (2026-10-02T17:05:34+0900)

Reference `results/B/20261002-1700_multilingual_ko_kmhas_type_8.json`. Δp over every option probability (noul: p(true)).

| other | n | argmax agreement | flips | max abs Δp | mean abs Δ answer_confidence |
|---|---|---|---|---|---|
| results/B/20261002-1703_router_ko_kmhas_type_8.json | 500 | 1.0000 | 0 | 0.0270 | 0.0001 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1700_multilingual_ko_kmhas_type_8.json | multilingual | 0.3.23 | 5791b97163144d6ce806a790895c804bcc1031ec02ddfdbd0884eab5db4ce16c | 3d6d4f200328097ff59f023c0f4d94823aa970a1543a20ed40676c5e8759772e | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 244, "test": 256} |
| results/B/20261002-1703_router_ko_kmhas_type_8.json | router (auto) | 0.3.23 | 5791b97163144d6ce806a790895c804bcc1031ec02ddfdbd0884eab5db4ce16c | 3d6d4f200328097ff59f023c0f4d94823aa970a1543a20ed40676c5e8759772e | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 244, "test": 256} |
