# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1654_english_ko_nsmc_sentiment.json results/B/20261002-1654_multilingual_ko_nsmc_sentiment.json --out results/B/metrics/paired_ko_nsmc_sentiment_english_vs_ml.md --json results/B/metrics/paired_ko_nsmc_sentiment_english_vs_ml.json` (2026-10-02T17:05:33+0900)

A = `results/B/20261002-1654_english_ko_nsmc_sentiment.json`, B = `results/B/20261002-1654_multilingual_ko_nsmc_sentiment.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| sentiment_noul | all | 500 | 0.516 | 0.638 | +0.122 [+0.080, +0.164] | 31 | 92 | 3.3e-08 | 0.754 | 1.00 |
| sentiment_noul | dev | 249 | 0.506 | 0.635 | +0.129 [+0.068, +0.189] | 16 | 48 | 7.7e-05 | 0.743 | 1.00 |
| sentiment_noul | test | 251 | 0.526 | 0.641 | +0.116 [+0.057, +0.174] | 15 | 44 | 2.0e-04 | 0.765 | 1.00 |
| sentiment_choice | all | 500 | 0.528 | 0.774 | +0.246 [+0.186, +0.306] | 71 | 194 | 2.2e-14 | 0.470 | 1.00 |
| sentiment_choice | dev | 249 | 0.542 | 0.775 | +0.233 [+0.149, +0.317] | 35 | 93 | 3.0e-07 | 0.486 | 1.00 |
| sentiment_choice | test | 251 | 0.514 | 0.773 | +0.259 [+0.173, +0.345] | 36 | 101 | 2.5e-08 | 0.454 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1654_english_ko_nsmc_sentiment.json | english | 0.3.23 | 68efeccdcbcc93d8856be721af93e4275e344293b00ef8eb6646b12e40639f1d | c76e85a04f5bbbc4d45f27a81ec2d7a6bdf76cfc958d27be0ef78c0f07668a98 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 251, "dev": 249} |
| results/B/20261002-1654_multilingual_ko_nsmc_sentiment.json | multilingual | 0.3.23 | 68efeccdcbcc93d8856be721af93e4275e344293b00ef8eb6646b12e40639f1d | c76e85a04f5bbbc4d45f27a81ec2d7a6bdf76cfc958d27be0ef78c0f07668a98 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 251, "dev": 249} |
