# metrics_extra summary

`scripts/metrics_extra.py summary results/C/schemas_v2/20261002-1734_multilingual_router_v2d_dev.json --bootstrap 1000 --seed 13 --out results/C/schemas_v2/metrics/summary_v2d.md --json results/C/schemas_v2/metrics/summary_v2d.json` (2026-10-02T17:35:26+0900)

| set | model | qid | split | n | accuracy [95% CI] | macro-F1 ∪ | macro-F1 gold | Brier | ECE [95% CI] | mean conf | acc@50%cov | majority | random | Δ vs majority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| router_v2d_dev | multilingual | domain | all | 250 | 0.516 [0.456, 0.576] | 0.502 | 0.502 | 0.683 | 0.211 [0.172, 0.267] | 0.727 | 0.736 | 0.148 | 0.125 | +0.368 |
| router_v2d_dev | multilingual | domain | dev | 250 | 0.516 [0.456, 0.576] | 0.502 | 0.502 | 0.683 | 0.211 [0.172, 0.267] | 0.727 | 0.736 | 0.148 | 0.125 | +0.368 |

## Per-class detail (split = all; dev/test in the JSON)

### router_v2d_dev/multilingual / domain

- recall: communication 19/30, general 7/30, info_qa 12/31, lifestyle 16/27, media 20/37, productivity 5/33, smart_home 20/30, transport 30/32
- predicted: smart_home 60, transport 43, lifestyle 39, communication 27, media 24, general 20, productivity 19, info_qa 18
- first listed option (most common: `general`): gold 30, predicted 20
- top confusions: general→smart_home ×11, productivity→smart_home ×10, media→smart_home ×9, smart_home→productivity ×6, info_qa→general ×6
- answering model (cases): multilingual 250

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/C/schemas_v2/20261002-1734_multilingual_router_v2d_dev.json | multilingual | 0.3.23 | da73a646a05a92a211f823c73dfb936a774ce8cdbbc7356527685507c43a0147 | 5bdac5b744e7fc4bffdb32e9856f8f52f116f8a51a8bdb4c62c8500ea94283e6 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 250} |
