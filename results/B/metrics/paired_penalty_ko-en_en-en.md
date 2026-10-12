# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1643_english_ko_massive_domain_8.json results/B/20261002-1648_english_en_massive_domain_8.json --out results/B/metrics/paired_penalty_ko-en_en-en.md --json results/B/metrics/paired_penalty_ko-en_en-en.json` (2026-10-02T17:05:31+0900)

A = `results/B/20261002-1643_english_ko_massive_domain_8.json`, B = `results/B/20261002-1648_english_en_massive_domain_8.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| domain | all | 500 | 0.262 | 0.446 | +0.184 [+0.131, +0.237] | 53 | 145 | 4.5e-11 | 0.286 | 0.00 |
| domain | dev | 250 | 0.248 | 0.428 | +0.180 [+0.106, +0.254] | 26 | 71 | 5.5e-06 | 0.276 | 0.00 |
| domain | test | 250 | 0.276 | 0.464 | +0.188 [+0.113, +0.263] | 27 | 74 | 3.2e-06 | 0.296 | 0.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1643_english_ko_massive_domain_8.json | english | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/B/20261002-1648_english_en_massive_domain_8.json | english | 0.3.23 | c52a5f4ef33ee2eca77424de6e6b466c175910e8096f3b095f249c6180362b0a | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
