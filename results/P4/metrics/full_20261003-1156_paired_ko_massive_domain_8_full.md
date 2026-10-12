# metrics_extra paired

`scripts/metrics_extra.py paired results/P4/full_20261003-1156_multilingual_ko_massive_domain_8_full.json results/P4/full_20261003-1156_ft-v1_ko_massive_domain_8_full.json --split all --out results/P4/metrics/full_20261003-1156_paired_ko_massive_domain_8_full.md --json results/P4/metrics/full_20261003-1156_paired_ko_massive_domain_8_full.json` (2026-10-03T12:40:28+0900)

A = `results/P4/full_20261003-1156_multilingual_ko_massive_domain_8_full.json`, B = `results/P4/full_20261003-1156_ft-v1_ko_massive_domain_8_full.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| domain | all | 2917 | 0.475 | 0.913 | +0.438 [+0.419, +0.457] | 43 | 1320 | 0.0e+00 | 0.492 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/P4/full_20261003-1156_multilingual_ko_massive_domain_8_full.json | multilingual | 0.3.23 | e5fc26498e836cda5660f73b24d9a10d2eae04193d77ac86a4394c758eb09bf9 | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 1459, "test": 1458} |
| results/P4/full_20261003-1156_ft-v1_ko_massive_domain_8_full.json | ft-v1 | 0.3.23 | e5fc26498e836cda5660f73b24d9a10d2eae04193d77ac86a4394c758eb09bf9 | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"ft-v1": "local:poc/finetune/ckpt_domain8_v1 (base 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851)"} | index parity | {"dev": 1459, "test": 1458} |
