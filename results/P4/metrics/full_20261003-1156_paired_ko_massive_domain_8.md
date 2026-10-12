# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1643_multilingual_ko_massive_domain_8.json results/P4/full_20261003-1156_ft-v1_ko_massive_domain_8.json --out results/P4/metrics/full_20261003-1156_paired_ko_massive_domain_8.md --json results/P4/metrics/full_20261003-1156_paired_ko_massive_domain_8.json` (2026-10-03T12:40:28+0900)

A = `results/B/20261002-1643_multilingual_ko_massive_domain_8.json`, B = `results/P4/full_20261003-1156_ft-v1_ko_massive_domain_8.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| domain | all | 500 | 0.526 | 0.894 | +0.368 [+0.323, +0.413] | 7 | 191 | 1.1e-47 | 0.550 | 1.00 |
| domain | dev | 250 | 0.560 | 0.888 | +0.328 [+0.264, +0.392] | 6 | 88 | 8.8e-20 | 0.552 | 1.00 |
| domain | test | 250 | 0.492 | 0.900 | +0.408 [+0.346, +0.470] | 1 | 103 | 1.0e-29 | 0.548 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1643_multilingual_ko_massive_domain_8.json | multilingual | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/P4/full_20261003-1156_ft-v1_ko_massive_domain_8.json | ft-v1 | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"ft-v1": "local:poc/finetune/ckpt_domain8_v1 (base 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851)"} | index parity | {"dev": 250, "test": 250} |
