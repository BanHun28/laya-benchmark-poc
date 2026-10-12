# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1700_english_ko_kmhas_type_8.json results/B/20261002-1700_multilingual_ko_kmhas_type_8.json --out results/B/metrics/paired_ko_kmhas_type_8_english_vs_ml.md --json results/B/metrics/paired_ko_kmhas_type_8_english_vs_ml.json` (2026-10-02T17:05:33+0900)

A = `results/B/20261002-1700_english_ko_kmhas_type_8.json`, B = `results/B/20261002-1700_multilingual_ko_kmhas_type_8.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| hate_type | all | 500 | 0.146 | 0.394 | +0.248 [+0.190, +0.306] | 64 | 188 | 2.5e-15 | 0.028 | 1.00 |
| hate_type | dev | 244 | 0.160 | 0.385 | +0.225 [+0.142, +0.309] | 33 | 88 | 5.9e-07 | 0.029 | 1.00 |
| hate_type | test | 256 | 0.133 | 0.402 | +0.270 [+0.188, +0.351] | 31 | 100 | 1.2e-09 | 0.027 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1700_english_ko_kmhas_type_8.json | english | 0.3.23 | 5791b97163144d6ce806a790895c804bcc1031ec02ddfdbd0884eab5db4ce16c | 3d6d4f200328097ff59f023c0f4d94823aa970a1543a20ed40676c5e8759772e | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 244, "test": 256} |
| results/B/20261002-1700_multilingual_ko_kmhas_type_8.json | multilingual | 0.3.23 | 5791b97163144d6ce806a790895c804bcc1031ec02ddfdbd0884eab5db4ce16c | 3d6d4f200328097ff59f023c0f4d94823aa970a1543a20ed40676c5e8759772e | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 244, "test": 256} |
