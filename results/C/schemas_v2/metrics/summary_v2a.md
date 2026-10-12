# metrics_extra summary

`scripts/metrics_extra.py summary results/C/schemas_v2/20261002-1733_multilingual_router_v2a_dev.json --bootstrap 1000 --seed 13 --out results/C/schemas_v2/metrics/summary_v2a.md --json results/C/schemas_v2/metrics/summary_v2a.json` (2026-10-02T17:35:25+0900)

| set | model | qid | split | n | accuracy [95% CI] | macro-F1 ∪ | macro-F1 gold | Brier | ECE [95% CI] | mean conf | acc@50%cov | majority | random | Δ vs majority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| router_v2a_dev | multilingual | domain | all | 250 | 0.536 [0.476, 0.596] | 0.529 | 0.529 | 0.657 | 0.182 [0.145, 0.247] | 0.718 | 0.760 | 0.148 | 0.125 | +0.388 |
| router_v2a_dev | multilingual | domain | dev | 250 | 0.536 [0.476, 0.596] | 0.529 | 0.529 | 0.657 | 0.182 [0.145, 0.247] | 0.718 | 0.760 | 0.148 | 0.125 | +0.388 |

## Per-class detail (split = all; dev/test in the JSON)

### router_v2a_dev/multilingual / domain

- recall: communication 19/30, general 9/30, info_qa 12/31, lifestyle 14/27, media 12/37, productivity 12/33, smart_home 26/30, transport 30/32
- predicted: smart_home 70, transport 47, general 33, communication 27, lifestyle 25, productivity 21, info_qa 14, media 13
- first listed option (most common: `productivity`): gold 33, predicted 21
- top confusions: general→smart_home ×11, media→smart_home ×9, info_qa→general ×7, info_qa→smart_home ×7, productivity→smart_home ×7
- answering model (cases): multilingual 250

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/C/schemas_v2/20261002-1733_multilingual_router_v2a_dev.json | multilingual | 0.3.23 | bc18386eecd77d08d99c246d67d7c09d1fd9fcac2225ac55da487a6b18298b81 | c8b97badf47449eb3891c31f0d55e9633406ff5d34673b6edbe69024c9b65702 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 250} |
