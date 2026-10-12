# metrics_extra summary

`scripts/metrics_extra.py summary results/C/schemas_v2/20261002-1732_multilingual_router_v1_dev.json --bootstrap 1000 --seed 13 --out results/C/schemas_v2/metrics/summary_v1.md --json results/C/schemas_v2/metrics/summary_v1.json` (2026-10-02T17:35:25+0900)

| set | model | qid | split | n | accuracy [95% CI] | macro-F1 ∪ | macro-F1 gold | Brier | ECE [95% CI] | mean conf | acc@50%cov | majority | random | Δ vs majority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| router_v1_dev | multilingual | domain | all | 250 | 0.560 [0.500, 0.620] | 0.555 | 0.555 | 0.634 | 0.200 [0.161, 0.261] | 0.756 | 0.792 | 0.148 | 0.125 | +0.412 |
| router_v1_dev | multilingual | domain | dev | 250 | 0.560 [0.500, 0.620] | 0.555 | 0.555 | 0.634 | 0.200 [0.161, 0.261] | 0.756 | 0.792 | 0.148 | 0.125 | +0.412 |

## Per-class detail (split = all; dev/test in the JSON)

### router_v1_dev/multilingual / domain

- recall: communication 19/30, general 11/30, info_qa 10/31, lifestyle 14/27, media 20/37, productivity 10/33, smart_home 25/30, transport 31/32
- predicted: smart_home 66, general 40, transport 38, communication 28, lifestyle 26, media 21, info_qa 19, productivity 12
- first listed option (most common: `productivity`): gold 33, predicted 12
- top confusions: general→smart_home ×12, info_qa→general ×11, media→smart_home ×10, productivity→smart_home ×9, productivity→communication ×6
- answering model (cases): multilingual 250

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/C/schemas_v2/20261002-1732_multilingual_router_v1_dev.json | multilingual | 0.3.23 | a8223a39cd879c94a60eb0bd9c30fa56813065d255a3ddd54593debab3102536 | a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 250} |
