# metrics_extra parity

`scripts/metrics_extra.py parity results/B/20261002-1657_multilingual_ko_kmhas_hate.json results/B/20261002-1659_router_ko_kmhas_hate.json --out results/B/metrics/parity_ko_kmhas_hate_router.md --json results/B/metrics/parity_ko_kmhas_hate_router.json` (2026-10-02T17:05:33+0900)

Reference `results/B/20261002-1657_multilingual_ko_kmhas_hate.json`. Δp over every option probability (noul: p(true)).

| other | n | argmax agreement | flips | max abs Δp | mean abs Δ answer_confidence |
|---|---|---|---|---|---|
| results/B/20261002-1659_router_ko_kmhas_hate.json | 500 | 1.0000 | 0 | 0.0000 | 0.0000 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1657_multilingual_ko_kmhas_hate.json | multilingual | 0.3.23 | 4e15c044a81e71fcad18f90a4d8cfd3452bdb6921a401f83ba012bc1f45e72c6 | ae97133388aac00d0eb6b8707db941904acf249795e7c0b551c28adf41fec213 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 263, "dev": 237} |
| results/B/20261002-1659_router_ko_kmhas_hate.json | router (auto) | 0.3.23 | 4e15c044a81e71fcad18f90a4d8cfd3452bdb6921a401f83ba012bc1f45e72c6 | ae97133388aac00d0eb6b8707db941904acf249795e7c0b551c28adf41fec213 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 263, "dev": 237} |
