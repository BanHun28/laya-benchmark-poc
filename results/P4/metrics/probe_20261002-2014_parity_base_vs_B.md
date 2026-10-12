# metrics_extra parity

`scripts/metrics_extra.py parity results/B/20261002-1643_multilingual_ko_massive_domain_8.json results/P4/20261002-2014_multilingual_ko_massive_domain_8.json --out results/P4/metrics/probe_20261002-2014_parity_base_vs_B.md --json results/P4/metrics/probe_20261002-2014_parity_base_vs_B.json` (2026-10-02T20:19:27+0900)

Reference `results/B/20261002-1643_multilingual_ko_massive_domain_8.json`. Δp over every option probability (noul: p(true)).

| other | n | argmax agreement | flips | max abs Δp | mean abs Δ answer_confidence |
|---|---|---|---|---|---|
| results/P4/20261002-2014_multilingual_ko_massive_domain_8.json | 500 | 1.0000 | 0 | 0.0000 | 0.0000 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1643_multilingual_ko_massive_domain_8.json | multilingual | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
| results/P4/20261002-2014_multilingual_ko_massive_domain_8.json | multilingual | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | index parity | {"dev": 250, "test": 250} |
