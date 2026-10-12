# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1644_typed-decisions_ko_massive_domain_8.json results/B/20261002-1643_multilingual_ko_massive_domain_8.json --out results/B/metrics/paired_ko_massive_domain_8_typed-decisions_vs_ml.md --json results/B/metrics/paired_ko_massive_domain_8_typed-decisions_vs_ml.json` (2026-10-02T17:05:32+0900)

A = `results/B/20261002-1644_typed-decisions_ko_massive_domain_8.json`, B = `results/B/20261002-1643_multilingual_ko_massive_domain_8.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| domain | all | 500 | 0.288 | 0.526 | +0.238 [+0.188, +0.288] | 35 | 154 | 5.2e-19 | 0.272 | 1.00 |
| domain | dev | 250 | 0.288 | 0.560 | +0.272 [+0.200, +0.344] | 18 | 86 | 8.2e-12 | 0.260 | 1.00 |
| domain | test | 250 | 0.288 | 0.492 | +0.204 [+0.136, +0.272] | 17 | 68 | 2.2e-08 | 0.284 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1644_typed-decisions_ko_massive_domain_8.json | typed-decisions | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"typed-decisions": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/B/20261002-1643_multilingual_ko_massive_domain_8.json | multilingual | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
