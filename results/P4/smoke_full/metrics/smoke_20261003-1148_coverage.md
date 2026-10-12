# metrics_extra coverage

`scripts/metrics_extra.py coverage results/P4/smoke_full/smoke_20261003-1148_ft-smoke_ko_massive_domain_8.json --out results/P4/smoke_full/metrics/smoke_20261003-1148_coverage.md --json results/P4/smoke_full/metrics/smoke_20261003-1148_coverage.json` (2026-10-03T11:54:57+0900)


### ko_massive_domain_8/ft-smoke / domain / all (n=500)

| T | coverage | n covered | covered accuracy |
|---|---|---|---|
| 0.50 | 0.800 | 400 | 0.680 |
| 0.55 | 0.748 | 374 | 0.693 |
| 0.60 | 0.696 | 348 | 0.724 |
| 0.65 | 0.648 | 324 | 0.741 |
| 0.70 | 0.594 | 297 | 0.768 |
| 0.75 | 0.562 | 281 | 0.776 |
| 0.80 | 0.518 | 259 | 0.795 |
| 0.85 | 0.490 | 245 | 0.808 |
| 0.90 | 0.458 | 229 | 0.834 |
| 0.95 | 0.388 | 194 | 0.871 |

- error ≤ 0.05: max coverage 0.204 (n=102) at T = 0.995, covered accuracy 0.951
- error ≤ 0.1: max coverage 0.362 (n=181) at T = 0.961, covered accuracy 0.901

### ko_massive_domain_8/ft-smoke / domain / dev (n=250)

| T | coverage | n covered | covered accuracy |
|---|---|---|---|
| 0.50 | 0.804 | 201 | 0.687 |
| 0.55 | 0.756 | 189 | 0.698 |
| 0.60 | 0.696 | 174 | 0.736 |
| 0.65 | 0.632 | 158 | 0.772 |
| 0.70 | 0.576 | 144 | 0.812 |
| 0.75 | 0.536 | 134 | 0.813 |
| 0.80 | 0.492 | 123 | 0.837 |
| 0.85 | 0.472 | 118 | 0.847 |
| 0.90 | 0.440 | 110 | 0.873 |
| 0.95 | 0.388 | 97 | 0.887 |

- error ≤ 0.05: max coverage 0.276 (n=69) at T = 0.984, covered accuracy 0.957
- error ≤ 0.1: max coverage 0.376 (n=94) at T = 0.957, covered accuracy 0.904

### ko_massive_domain_8/ft-smoke / domain / test (n=250)

| T | coverage | n covered | covered accuracy |
|---|---|---|---|
| 0.50 | 0.796 | 199 | 0.673 |
| 0.55 | 0.740 | 185 | 0.686 |
| 0.60 | 0.696 | 174 | 0.713 |
| 0.65 | 0.664 | 166 | 0.711 |
| 0.70 | 0.612 | 153 | 0.725 |
| 0.75 | 0.588 | 147 | 0.741 |
| 0.80 | 0.544 | 136 | 0.757 |
| 0.85 | 0.508 | 127 | 0.772 |
| 0.90 | 0.476 | 119 | 0.798 |
| 0.95 | 0.388 | 97 | 0.856 |

- error ≤ 0.05: max coverage 0.224 (n=56) at T = 0.995, covered accuracy 0.964
- error ≤ 0.1: max coverage 0.304 (n=76) at T = 0.985, covered accuracy 0.908

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/P4/smoke_full/smoke_20261003-1148_ft-smoke_ko_massive_domain_8.json | ft-smoke | 0.3.23 | edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"ft-smoke": "local:results/P4/smoke_full/ckpt_20261003-1148 (base 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851)"} | index parity | {"dev": 250, "test": 250} |
