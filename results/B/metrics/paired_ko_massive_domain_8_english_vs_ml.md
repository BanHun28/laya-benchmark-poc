# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1643_english_ko_massive_domain_8.json results/B/20261002-1643_multilingual_ko_massive_domain_8.json --out results/B/metrics/paired_ko_massive_domain_8_english_vs_ml.md --json results/B/metrics/paired_ko_massive_domain_8_english_vs_ml.json` (2026-10-02T17:05:32+0900)

A = `results/B/20261002-1643_english_ko_massive_domain_8.json`, B = `results/B/20261002-1643_multilingual_ko_massive_domain_8.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| domain | all | 500 | 0.262 | 0.526 | +0.264 [+0.215, +0.313] | 31 | 163 | 7.9e-23 | 0.226 | 1.00 |
| domain | dev | 250 | 0.248 | 0.560 | +0.312 [+0.241, +0.383] | 14 | 92 | 3.1e-15 | 0.216 | 1.00 |
| domain | test | 250 | 0.276 | 0.492 | +0.216 [+0.148, +0.284] | 17 | 71 | 5.2e-09 | 0.236 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1643_english_ko_massive_domain_8.json | english | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/B/20261002-1643_multilingual_ko_massive_domain_8.json | multilingual | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
