# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1643_multilingual_ko_massive_domain_8.json results/B/20261002-1649_multilingual_ko_massive_domain_8_en-desc_dev.json --split dev --out results/B/metrics/paired_ablation_ko_massive_domain_8_en-desc.md --json results/B/metrics/paired_ablation_ko_massive_domain_8_en-desc.json` (2026-10-02T17:05:34+0900)

A = `results/B/20261002-1643_multilingual_ko_massive_domain_8.json`, B = `results/B/20261002-1649_multilingual_ko_massive_domain_8_en-desc_dev.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| domain | dev | 250 | 0.560 | 0.532 | -0.028 [-0.077, +0.021] | 23 | 16 | 0.3368 | 0.692 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1643_multilingual_ko_massive_domain_8.json | multilingual | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/B/20261002-1649_multilingual_ko_massive_domain_8_en-desc_dev.json | multilingual | 0.3.23 | 4be87d318fe5a933eb08f35c6c667541e68a8ebb0ab8ec3fd1944196715ecd77 | c3ab76c59d099b54016d035d4a6092ccdf81af32802542b368d7bf7121784264 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 250} |
