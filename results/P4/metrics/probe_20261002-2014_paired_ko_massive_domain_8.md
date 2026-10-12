# metrics_extra paired

`scripts/metrics_extra.py paired results/P4/20261002-2014_multilingual_ko_massive_domain_8.json results/P4/20261002-2014_ft-probe_ko_massive_domain_8.json --out results/P4/metrics/probe_20261002-2014_paired_ko_massive_domain_8.md --json results/P4/metrics/probe_20261002-2014_paired_ko_massive_domain_8.json` (2026-10-02T20:19:27+0900)

A = `results/P4/20261002-2014_multilingual_ko_massive_domain_8.json`, B = `results/P4/20261002-2014_ft-probe_ko_massive_domain_8.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| domain | all | 500 | 0.526 | 0.722 | +0.196 [+0.152, +0.240] | 24 | 122 | 5.3e-17 | 0.576 | 1.00 |
| domain | dev | 250 | 0.560 | 0.724 | +0.164 [+0.100, +0.228] | 16 | 57 | 1.5e-06 | 0.592 | 1.00 |
| domain | test | 250 | 0.492 | 0.720 | +0.228 [+0.167, +0.289] | 8 | 65 | 3.2e-12 | 0.560 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/P4/20261002-2014_multilingual_ko_massive_domain_8.json | multilingual | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/P4/20261002-2014_ft-probe_ko_massive_domain_8.json | ft-probe | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"ft-probe": "local:poc/finetune/ckpt_probe (base 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851)"} | index parity | {"dev": 250, "test": 250} |
