# metrics_extra summary

`scripts/metrics_extra.py summary results/C/schemas_v2/20261002-1733_multilingual_router_v2b_dev.json --bootstrap 1000 --seed 13 --out results/C/schemas_v2/metrics/summary_v2b.md --json results/C/schemas_v2/metrics/summary_v2b.json` (2026-10-02T17:35:25+0900)

| set | model | qid | split | n | accuracy [95% CI] | macro-F1 ∪ | macro-F1 gold | Brier | ECE [95% CI] | mean conf | acc@50%cov | majority | random | Δ vs majority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| router_v2b_dev | multilingual | domain | all | 220 | 0.545 [0.482, 0.609] | 0.543 | 0.543 | 0.638 | 0.224 [0.174, 0.280] | 0.769 | 0.764 | 0.168 | 0.143 | +0.377 |
| router_v2b_dev | multilingual | domain | dev | 220 | 0.545 [0.482, 0.609] | 0.543 | 0.543 | 0.638 | 0.224 [0.174, 0.280] | 0.769 | 0.764 | 0.168 | 0.143 | +0.377 |

## Per-class detail (split = all; dev/test in the JSON)

### router_v2b_dev/multilingual / domain

- recall: communication 19/30, info_qa 12/31, lifestyle 9/27, media 17/37, productivity 7/33, smart_home 27/30, transport 29/32
- predicted: smart_home 84, transport 35, communication 24, productivity 22, lifestyle 21, media 18, info_qa 16
- first listed option (most common: `productivity`): gold 33, predicted 22
- top confusions: productivity→smart_home ×15, media→smart_home ×13, communication→smart_home ×10, info_qa→smart_home ×9, lifestyle→smart_home ×7
- answering model (cases): multilingual 220

## run_card

| report | model | laya | dataset_sha256 | questions_sha256 | revisions | split rule | rows by split |
|---|---|---|---|---|---|---|---|
| results/C/schemas_v2/20261002-1733_multilingual_router_v2b_dev.json | multilingual | 0.3.23 | 9a553debb9f158b260276a916b89a729b78a022018191f6367d22ed92b7a5bf5 | c38ebc7c16da21e6ed6faa6c1e826ce52bc1e99ea8876c23431325315422a4bd | {"multilingual": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"} | pre-split copy (dev) | {"dev": 220} |
