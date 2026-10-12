# metrics_extra parity

`scripts/metrics_extra.py parity results/B/20261002-1652_multilingual_ko_klue_nli_3.json results/B/20261002-1654_router_ko_klue_nli_3.json --out results/B/metrics/parity_ko_klue_nli_3_router.md --json results/B/metrics/parity_ko_klue_nli_3_router.json` (2026-10-02T17:05:33+0900)

Reference `results/B/20261002-1652_multilingual_ko_klue_nli_3.json`. Δp over every option probability (noul: p(true)).

| other | n | argmax agreement | flips | max abs Δp | mean abs Δ answer_confidence |
|---|---|---|---|---|---|
| results/B/20261002-1654_router_ko_klue_nli_3.json | 500 | 1.0000 | 0 | 0.0000 | 0.0000 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1652_multilingual_ko_klue_nli_3.json | multilingual | 0.3.23 | ae2787b1350acfe99e75d33e713004b72f30435bab8edb37f24e160f842086ff | 3f131f442bc7f0fd83b45e1c06454dc27b432b063dd8af7f374cffcd823986ec | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 263, "test": 237} |
| results/B/20261002-1654_router_ko_klue_nli_3.json | router (auto) | 0.3.23 | ae2787b1350acfe99e75d33e713004b72f30435bab8edb37f24e160f842086ff | 3f131f442bc7f0fd83b45e1c06454dc27b432b063dd8af7f374cffcd823986ec | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 263, "test": 237} |
