# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1656_typed-decisions_ko_nsmc_sentiment.json results/B/20261002-1654_multilingual_ko_nsmc_sentiment.json --out results/B/metrics/paired_ko_nsmc_sentiment_typed-decisions_vs_ml.md --json results/B/metrics/paired_ko_nsmc_sentiment_typed-decisions_vs_ml.json` (2026-10-02T17:05:33+0900)

A = `results/B/20261002-1656_typed-decisions_ko_nsmc_sentiment.json`, B = `results/B/20261002-1654_multilingual_ko_nsmc_sentiment.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| sentiment_noul | all | 500 | 0.532 | 0.638 | +0.106 [+0.056, +0.156] | 57 | 110 | 5.0e-05 | 0.666 | 1.00 |
| sentiment_noul | dev | 249 | 0.538 | 0.635 | +0.096 [+0.024, +0.168] | 31 | 55 | 0.0127 | 0.655 | 1.00 |
| sentiment_noul | test | 251 | 0.526 | 0.641 | +0.116 [+0.047, +0.184] | 26 | 55 | 0.0017 | 0.677 | 1.00 |
| sentiment_choice | all | 500 | 0.506 | 0.774 | +0.268 [+0.208, +0.328] | 68 | 202 | 1.3e-16 | 0.460 | 1.00 |
| sentiment_choice | dev | 249 | 0.522 | 0.775 | +0.253 [+0.169, +0.337] | 34 | 97 | 3.3e-08 | 0.474 | 1.00 |
| sentiment_choice | test | 251 | 0.490 | 0.773 | +0.283 [+0.198, +0.368] | 34 | 105 | 1.3e-09 | 0.446 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1656_typed-decisions_ko_nsmc_sentiment.json | typed-decisions | 0.3.23 | 68efeccdcbcc93d8856be721af93e4275e344293b00ef8eb6646b12e40639f1d | c76e85a04f5bbbc4d45f27a81ec2d7a6bdf76cfc958d27be0ef78c0f07668a98 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 251, "dev": 249} |
| results/B/20261002-1654_multilingual_ko_nsmc_sentiment.json | multilingual | 0.3.23 | 68efeccdcbcc93d8856be721af93e4275e344293b00ef8eb6646b12e40639f1d | c76e85a04f5bbbc4d45f27a81ec2d7a6bdf76cfc958d27be0ef78c0f07668a98 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 251, "dev": 249} |
