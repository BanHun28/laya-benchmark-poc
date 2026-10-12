# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1650_multilingual_ko_massive_intent_20opt.json results/B/20261002-1651_multilingual_en_massive_intent_20opt.json --out results/B/metrics/paired_penalty20_ko-ml_en-ml.md --json results/B/metrics/paired_penalty20_ko-ml_en-ml.json` (2026-10-02T17:05:32+0900)

A = `results/B/20261002-1650_multilingual_ko_massive_intent_20opt.json`, B = `results/B/20261002-1651_multilingual_en_massive_intent_20opt.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| intent | all | 100 | 0.470 | 0.710 | +0.240 [+0.129, +0.351] | 7 | 31 | 1.2e-04 | 0.470 | 0.00 |
| intent | dev | 50 | 0.480 | 0.640 | +0.160 [-0.000, +0.320] | 5 | 13 | 0.0963 | 0.460 | 0.00 |
| intent | test | 50 | 0.460 | 0.780 | +0.320 [+0.169, +0.471] | 2 | 18 | 4.0e-04 | 0.480 | 0.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1650_multilingual_ko_massive_intent_20opt.json | multilingual | 0.3.23 | 4e936ea663ba6072e8e7ab0cc5a4f22784824378ce74cb1266a8f955b4efb596 | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
| results/B/20261002-1651_multilingual_en_massive_intent_20opt.json | multilingual | 0.3.23 | de461b875166c454792aba5b13ba553fdf20c8514f8acb4f2ec9e93b7a427b9a | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
