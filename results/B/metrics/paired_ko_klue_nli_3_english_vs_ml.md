# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1652_english_ko_klue_nli_3.json results/B/20261002-1652_multilingual_ko_klue_nli_3.json --out results/B/metrics/paired_ko_klue_nli_3_english_vs_ml.md --json results/B/metrics/paired_ko_klue_nli_3_english_vs_ml.json` (2026-10-02T17:05:33+0900)

A = `results/B/20261002-1652_english_ko_klue_nli_3.json`, B = `results/B/20261002-1652_multilingual_ko_klue_nli_3.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| relation | all | 500 | 0.448 | 0.750 | +0.302 [+0.250, +0.354] | 35 | 186 | 4.6e-26 | 0.504 | 1.00 |
| relation | dev | 263 | 0.456 | 0.760 | +0.304 [+0.234, +0.374] | 16 | 96 | 4.4e-15 | 0.510 | 1.00 |
| relation | test | 237 | 0.439 | 0.738 | +0.300 [+0.222, +0.377] | 19 | 90 | 3.1e-12 | 0.498 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1652_english_ko_klue_nli_3.json | english | 0.3.23 | ae2787b1350acfe99e75d33e713004b72f30435bab8edb37f24e160f842086ff | 3f131f442bc7f0fd83b45e1c06454dc27b432b063dd8af7f374cffcd823986ec | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 263, "test": 237} |
| results/B/20261002-1652_multilingual_ko_klue_nli_3.json | multilingual | 0.3.23 | ae2787b1350acfe99e75d33e713004b72f30435bab8edb37f24e160f842086ff | 3f131f442bc7f0fd83b45e1c06454dc27b432b063dd8af7f374cffcd823986ec | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"dev": 263, "test": 237} |
