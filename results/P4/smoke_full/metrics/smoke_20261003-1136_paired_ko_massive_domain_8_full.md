# metrics_extra paired

`scripts/metrics_extra.py paired results/P4/smoke_full/smoke_20261003-1136_multilingual_ko_massive_domain_8_full.json results/P4/smoke_full/smoke_20261003-1136_ft-smoke_ko_massive_domain_8_full.json --split all --out results/P4/smoke_full/metrics/smoke_20261003-1136_paired_ko_massive_domain_8_full.md --json results/P4/smoke_full/metrics/smoke_20261003-1136_paired_ko_massive_domain_8_full.json` (2026-10-03T11:43:34+0900)

A = `results/P4/smoke_full/smoke_20261003-1136_multilingual_ko_massive_domain_8_full.json`, B = `results/P4/smoke_full/smoke_20261003-1136_ft-smoke_ko_massive_domain_8_full.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| domain | all | 2917 | 0.475 | 0.558 | +0.083 [+0.071, +0.096] | 65 | 308 | 6.1e-39 | 0.738 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/P4/smoke_full/smoke_20261003-1136_multilingual_ko_massive_domain_8_full.json | multilingual | 0.3.23 | e5fc26498e836cda5660f73b24d9a10d2eae04193d77ac86a4394c758eb09bf9 | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 1459, "test": 1458} |
| results/P4/smoke_full/smoke_20261003-1136_ft-smoke_ko_massive_domain_8_full.json | ft-smoke | 0.3.23 | e5fc26498e836cda5660f73b24d9a10d2eae04193d77ac86a4394c758eb09bf9 | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"ft-smoke": "local:results/P4/smoke_full/ckpt_20261003-1136 (base 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851)"} | index parity | {"dev": 1459, "test": 1458} |
