# metrics_extra parity

`scripts/metrics_extra.py parity results/B/20261002-1703_multilingual_ko_3i4k_speechact_7.json results/B/20261002-1705_router_ko_3i4k_speechact_7.json --out results/B/metrics/parity_ko_3i4k_speechact_7_router.md --json results/B/metrics/parity_ko_3i4k_speechact_7_router.json` (2026-10-02T17:05:34+0900)

Reference `results/B/20261002-1703_multilingual_ko_3i4k_speechact_7.json`. Δp over every option probability (noul: p(true)).

| other | n | argmax agreement | flips | max abs Δp | mean abs Δ answer_confidence |
|---|---|---|---|---|---|
| results/B/20261002-1705_router_ko_3i4k_speechact_7.json | 500 | 1.0000 | 0 | 0.0000 | 0.0000 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1703_multilingual_ko_3i4k_speechact_7.json | multilingual | 0.3.23 | 88e47bec5b3966b5b2747b385744ecb1d738b2e3fb2b7a186755c85d48c6f741 | bc89af6329eca2b09e2ac19c4d6f6deea507e7fb01b964bf5067822f213274e7 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 259, "dev": 241} |
| results/B/20261002-1705_router_ko_3i4k_speechact_7.json | router (auto) | 0.3.23 | 88e47bec5b3966b5b2747b385744ecb1d738b2e3fb2b7a186755c85d48c6f741 | bc89af6329eca2b09e2ac19c4d6f6deea507e7fb01b964bf5067822f213274e7 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 259, "dev": 241} |
