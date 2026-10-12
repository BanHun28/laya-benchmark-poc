# metrics_extra paired

`scripts/metrics_extra.py paired results/P4/20261002-2014_multilingual_domain8_dev.json results/P4/20261002-2014_ft-probe_domain8_dev.json --out results/P4/metrics/probe_20261002-2014_paired_domain8_dev.md --json results/P4/metrics/probe_20261002-2014_paired_domain8_dev.json` (2026-10-02T20:19:28+0900)

A = `results/P4/20261002-2014_multilingual_domain8_dev.json`, B = `results/P4/20261002-2014_ft-probe_domain8_dev.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| domain | all | 2012 | 0.462 | 0.716 | +0.254 [+0.232, +0.277] | 84 | 596 | 5.7e-96 | 0.528 | 1.00 |
| domain | dev | 2012 | 0.462 | 0.716 | +0.254 [+0.232, +0.277] | 84 | 596 | 5.7e-96 | 0.528 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/P4/20261002-2014_multilingual_domain8_dev.json | multilingual | 0.3.23 | 957359aa686f099d04df0e9996150f3e75133252da40fed2bd1eb9818b993907 | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 2012} |
| results/P4/20261002-2014_ft-probe_domain8_dev.json | ft-probe | 0.3.23 | 957359aa686f099d04df0e9996150f3e75133252da40fed2bd1eb9818b993907 | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"ft-probe": "local:poc/finetune/ckpt_probe (base 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851)"} | pre-split copy (dev) | {"dev": 2012} |
