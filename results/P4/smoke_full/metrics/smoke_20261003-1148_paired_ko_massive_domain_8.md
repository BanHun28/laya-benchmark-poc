# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1643_multilingual_ko_massive_domain_8.json results/P4/smoke_full/smoke_20261003-1148_ft-smoke_ko_massive_domain_8.json --out results/P4/smoke_full/metrics/smoke_20261003-1148_paired_ko_massive_domain_8.md --json results/P4/smoke_full/metrics/smoke_20261003-1148_paired_ko_massive_domain_8.json` (2026-10-03T11:54:57+0900)

A = `results/B/20261002-1643_multilingual_ko_massive_domain_8.json`, B = `results/P4/smoke_full/smoke_20261003-1148_ft-smoke_ko_massive_domain_8.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| domain | all | 500 | 0.526 | 0.586 | +0.060 [+0.030, +0.090] | 16 | 46 | 1.8e-04 | 0.736 | 1.00 |
| domain | dev | 250 | 0.560 | 0.592 | +0.032 [-0.009, +0.073] | 10 | 18 | 0.1849 | 0.752 | 1.00 |
| domain | test | 250 | 0.492 | 0.580 | +0.088 [+0.044, +0.132] | 6 | 28 | 2.0e-04 | 0.720 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1643_multilingual_ko_massive_domain_8.json | multilingual | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/P4/smoke_full/smoke_20261003-1148_ft-smoke_ko_massive_domain_8.json | ft-smoke | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"ft-smoke": "local:results/P4/smoke_full/ckpt_20261003-1148 (base 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851)"} | index parity | {"dev": 250, "test": 250} |
