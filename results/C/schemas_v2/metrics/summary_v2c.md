# metrics_extra summary

`scripts/metrics_extra.py summary results/C/schemas_v2/20261002-1733_multilingual_router_v2c_dev.json --bootstrap 1000 --seed 13 --out results/C/schemas_v2/metrics/summary_v2c.md --json results/C/schemas_v2/metrics/summary_v2c.json` (2026-10-02T17:35:26+0900)

| set | model | qid | split | n | accuracy [95% CI] | macro-F1 ∪ | macro-F1 gold | Brier | ECE [95% CI] | mean conf | acc@50%cov | majority | random | Δ vs majority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| router_v2c_dev | multilingual | domain | all | 250 | 0.540 [0.476, 0.600] | 0.525 | 0.525 | 0.672 | 0.199 [0.159, 0.259] | 0.739 | 0.712 | 0.148 | 0.125 | +0.392 |
| router_v2c_dev | multilingual | domain | dev | 250 | 0.540 [0.476, 0.600] | 0.525 | 0.525 | 0.672 | 0.199 [0.159, 0.259] | 0.739 | 0.712 | 0.148 | 0.125 | +0.392 |

## Per-class detail (split = all; dev/test in the JSON)

### router_v2c_dev/multilingual / domain

- recall: communication 21/30, general 10/30, info_qa 11/31, lifestyle 15/27, media 14/37, productivity 11/33, smart_home 22/30, transport 31/32
- predicted: transport 49, smart_home 44, lifestyle 41, communication 32, general 26, productivity 25, info_qa 17, media 16
- first listed option (most common: `productivity`): gold 33, predicted 25
- top confusions: general→smart_home ×8, media→lifestyle ×7, info_qa→lifestyle ×6, lifestyle→transport ×5, info_qa→general ×5
- answering model (cases): multilingual 250

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/C/schemas_v2/20261002-1733_multilingual_router_v2c_dev.json | multilingual | 0.3.23 | 4c1a473e414e59cb683d8c36f5289147c4932f1658b788ec71b5ff72b95f38b4 | c26e216fda3fd2057ae3ed4baaf68a885267d65ad57a21a00e98a3dccf95a073 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 250} |
