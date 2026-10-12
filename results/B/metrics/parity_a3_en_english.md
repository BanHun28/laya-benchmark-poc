# metrics_extra parity

`scripts/metrics_extra.py parity results/korean_support/K2_intent20_en_english.json results/B/20261002-1651_english_en_massive_intent_20opt.json --out results/B/metrics/parity_a3_en_english.md --json results/B/metrics/parity_a3_en_english.json` (2026-10-02T17:05:35+0900)

Reference `results/korean_support/K2_intent20_en_english.json`. Δp over every option probability (noul: p(true)).

| other | n | argmax agreement | flips | max abs Δp | mean abs Δ answer_confidence |
|---|---|---|---|---|---|
| results/B/20261002-1651_english_en_massive_intent_20opt.json | 100 | 1.0000 | 0 | 0.0000 | 0.0000 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/korean_support/K2_intent20_en_english.json | english | 0.3.23 | acd1722ca2b0b8b61bdc60e6a079e1119b0d7363ada98d288e4d1769138ccf49 | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 47, "dev": 53} |
| results/B/20261002-1651_english_en_massive_intent_20opt.json | english | 0.3.23 | de461b875166c454792aba5b13ba553fdf20c8514f8acb4f2ec9e93b7a427b9a | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
