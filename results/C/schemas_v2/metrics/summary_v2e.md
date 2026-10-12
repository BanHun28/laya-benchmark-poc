# metrics_extra summary

`scripts/metrics_extra.py summary results/C/schemas_v2/20261002-1734_multilingual_router_v2e_dev.json --bootstrap 1000 --seed 13 --out results/C/schemas_v2/metrics/summary_v2e.md --json results/C/schemas_v2/metrics/summary_v2e.json` (2026-10-02T17:35:26+0900)

| set | model | qid | split | n | accuracy [95% CI] | macro-F1 ∪ | macro-F1 gold | Brier | ECE [95% CI] | mean conf | acc@50%cov | majority | random | Δ vs majority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| router_v2e_dev | multilingual | domain | all | 220 | 0.536 [0.468, 0.605] | 0.553 | 0.553 | 0.664 | 0.213 [0.171, 0.286] | 0.742 | 0.664 | 0.286 | 0.200 | +0.250 |
| router_v2e_dev | multilingual | domain | dev | 220 | 0.536 [0.468, 0.605] | 0.553 | 0.553 | 0.664 | 0.213 [0.171, 0.286] | 0.742 | 0.664 | 0.286 | 0.200 | +0.250 |

## Per-class detail (split = all; dev/test in the JSON)

### router_v2e_dev/multilingual / domain

- recall: assistant_tasks 30/63, daily_life 19/59, info_qa 18/31, media 24/37, smart_home 27/30
- predicted: smart_home 78, assistant_tasks 42, daily_life 40, info_qa 32, media 28
- first listed option (most common: `assistant_tasks`): gold 63, predicted 42
- top confusions: daily_life→smart_home ×26, assistant_tasks→smart_home ×11, assistant_tasks→daily_life ×10, assistant_tasks→info_qa ×10, media→smart_home ×9
- answering model (cases): multilingual 220

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/C/schemas_v2/20261002-1734_multilingual_router_v2e_dev.json | multilingual | 0.3.23 | 8cabdc1523e3d25b95191de7478e6280df44491e82bef41ba3c4761e68502a4d | 4eeb2f06eb82ccc71fc85556d74857e5b79473586e73f50f3050f4c36d957866 | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 220} |
