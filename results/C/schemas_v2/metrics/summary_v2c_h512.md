# metrics_extra summary

`scripts/metrics_extra.py summary results/C/schemas_v2/20261002-1734_multilingual_router_v2c_dev_h512.json --bootstrap 1000 --seed 13 --out results/C/schemas_v2/metrics/summary_v2c_h512.md --json results/C/schemas_v2/metrics/summary_v2c_h512.json` (2026-10-02T17:35:26+0900)

| set | model | qid | split | n | accuracy [95% CI] | macro-F1 ∪ | macro-F1 gold | Brier | ECE [95% CI] | mean conf | acc@50%cov | majority | random | Δ vs majority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| router_v2c_dev | multilingual | domain | all | 250 | 0.408 [0.348, 0.464] | 0.379 | 0.379 | 0.832 | 0.333 [0.279, 0.385] | 0.741 | 0.608 | 0.148 | 0.125 | +0.260 |
| router_v2c_dev | multilingual | domain | dev | 250 | 0.408 [0.348, 0.464] | 0.379 | 0.379 | 0.832 | 0.333 [0.279, 0.385] | 0.741 | 0.608 | 0.148 | 0.125 | +0.260 |

## Per-class detail (split = all; dev/test in the JSON)

### router_v2c_dev/multilingual / domain

- recall: communication 17/30, general 3/30, info_qa 2/31, lifestyle 7/27, media 12/37, productivity 6/33, smart_home 25/30, transport 30/32
- predicted: smart_home 114, transport 49, communication 23, productivity 22, media 14, general 13, lifestyle 12, info_qa 3
- first listed option (most common: `productivity`): gold 33, predicted 22
- top confusions: general→smart_home ×20, info_qa→smart_home ×20, productivity→smart_home ×18, media→smart_home ×14, lifestyle→smart_home ×10
- answering model (cases): multilingual 250

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/C/schemas_v2/20261002-1734_multilingual_router_v2c_dev_h512.json | multilingual | 0.3.23 | 4c1a473e414e59cb683d8c36f5289147c4932f1658b788ec71b5ff72b95f38b4 | c26e216fda3fd2057ae3ed4baaf68a885267d65ad57a21a00e98a3dccf95a073 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 250} |
