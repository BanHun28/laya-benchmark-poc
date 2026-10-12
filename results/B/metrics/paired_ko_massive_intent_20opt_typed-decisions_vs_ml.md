# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1650_typed-decisions_ko_massive_intent_20opt.json results/B/20261002-1650_multilingual_ko_massive_intent_20opt.json --out results/B/metrics/paired_ko_massive_intent_20opt_typed-decisions_vs_ml.md --json results/B/metrics/paired_ko_massive_intent_20opt_typed-decisions_vs_ml.json` (2026-10-02T17:05:33+0900)

A = `results/B/20261002-1650_typed-decisions_ko_massive_intent_20opt.json`, B = `results/B/20261002-1650_multilingual_ko_massive_intent_20opt.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| intent | all | 100 | 0.060 | 0.470 | +0.410 [+0.299, +0.521] | 4 | 45 | 8.2e-10 | 0.120 | 1.00 |
| intent | dev | 50 | 0.020 | 0.480 | +0.460 [+0.322, +0.598] | 0 | 23 | 2.4e-07 | 0.120 | 1.00 |
| intent | test | 50 | 0.100 | 0.460 | +0.360 [+0.187, +0.533] | 4 | 22 | 5.3e-04 | 0.120 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1650_typed-decisions_ko_massive_intent_20opt.json | typed-decisions | 0.3.23 | 4e936ea663ba6072e8e7ab0cc5a4f22784824378ce74cb1266a8f955b4efb596 | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
| results/B/20261002-1650_multilingual_ko_massive_intent_20opt.json | multilingual | 0.3.23 | 4e936ea663ba6072e8e7ab0cc5a4f22784824378ce74cb1266a8f955b4efb596 | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 50, "test": 50} |
