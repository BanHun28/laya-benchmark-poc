# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1659_typed-decisions_ko_kmhas_hate.json results/B/20261002-1657_multilingual_ko_kmhas_hate.json --out results/B/metrics/paired_ko_kmhas_hate_typed-decisions_vs_ml.md --json results/B/metrics/paired_ko_kmhas_hate_typed-decisions_vs_ml.json` (2026-10-02T17:05:33+0900)

A = `results/B/20261002-1659_typed-decisions_ko_kmhas_hate.json`, B = `results/B/20261002-1657_multilingual_ko_kmhas_hate.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| is_hate | all | 500 | 0.500 | 0.582 | +0.082 [+0.047, +0.117] | 21 | 62 | 7.5e-06 | 0.834 | 1.00 |
| is_hate | dev | 237 | 0.502 | 0.582 | +0.080 [+0.027, +0.133] | 12 | 31 | 0.0054 | 0.819 | 1.00 |
| is_hate | test | 263 | 0.498 | 0.582 | +0.084 [+0.038, +0.130] | 9 | 31 | 6.8e-04 | 0.848 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1659_typed-decisions_ko_kmhas_hate.json | typed-decisions | 0.3.23 | 4e15c044a81e71fcad18f90a4d8cfd3452bdb6921a401f83ba012bc1f45e72c6 | ae97133388aac00d0eb6b8707db941904acf249795e7c0b551c28adf41fec213 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 263, "dev": 237} |
| results/B/20261002-1657_multilingual_ko_kmhas_hate.json | multilingual | 0.3.23 | 4e15c044a81e71fcad18f90a4d8cfd3452bdb6921a401f83ba012bc1f45e72c6 | ae97133388aac00d0eb6b8707db941904acf249795e7c0b551c28adf41fec213 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 263, "dev": 237} |
