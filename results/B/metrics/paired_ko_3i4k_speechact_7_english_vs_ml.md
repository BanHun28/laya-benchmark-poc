# metrics_extra paired

`scripts/metrics_extra.py paired results/B/20261002-1703_english_ko_3i4k_speechact_7.json results/B/20261002-1703_multilingual_ko_3i4k_speechact_7.json --out results/B/metrics/paired_ko_3i4k_speechact_7_english_vs_ml.md --json results/B/metrics/paired_ko_3i4k_speechact_7_english_vs_ml.json` (2026-10-02T17:05:34+0900)

A = `results/B/20261002-1703_english_ko_3i4k_speechact_7.json`, B = `results/B/20261002-1703_multilingual_ko_3i4k_speechact_7.json`. b = A right & B wrong, c = A wrong & B right; Δ = acc B − acc A; 95% Wald CI for the paired difference; exact two-sided McNemar.

| qid | split | n | acc A | acc B | Δ (B−A) [95% CI] | b | c | McNemar p | argmax agreement | same state |
|---|---|---|---|---|---|---|---|---|---|---|
| speech_act | all | 500 | 0.174 | 0.178 | +0.004 [-0.042, +0.050] | 69 | 71 | 0.9327 | 0.216 | 1.00 |
| speech_act | dev | 241 | 0.174 | 0.195 | +0.021 [-0.048, +0.089] | 33 | 38 | 0.6353 | 0.212 | 1.00 |
| speech_act | test | 259 | 0.174 | 0.162 | -0.012 [-0.074, +0.051] | 36 | 33 | 0.8099 | 0.220 | 1.00 |

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/B/20261002-1703_english_ko_3i4k_speechact_7.json | english | 0.3.23 | 88e47bec5b3966b5b2747b385744ecb1d738b2e3fb2b7a186755c85d48c6f741 | bc89af6329eca2b09e2ac19c4d6f6deea507e7fb01b964bf5067822f213274e7 | {"english": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 259, "dev": 241} |
| results/B/20261002-1703_multilingual_ko_3i4k_speechact_7.json | multilingual | 0.3.23 | 88e47bec5b3966b5b2747b385744ecb1d738b2e3fb2b7a186755c85d48c6f741 | bc89af6329eca2b09e2ac19c4d6f6deea507e7fb01b964bf5067822f213274e7 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | state sha256 % 2 | {"test": 259, "dev": 241} |
