# C1 option-order flip probe (2026-10-08)

`scripts/probe_option_order.py poc/finetune/data/t3arm/T4_dev40.jsonl --model poc/finetune/ckpt_t3arm/T4_run --device cpu --permutations 5 --seed 13 --split all --splits  --out results/T3arm/T4/flip_dev40.json` — 2026-10-08T12:33:00+0900

flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (1000, seed 13). G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1).

| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] | perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T4_dev40 | all | 40 | 10 | 0.950 | 0.035 [0.000, 0.095] | 0.025–0.050 | 0.050 [0.000, 0.125] | 0.985 (0.975–1.000) | 0.007 | pass | no | - |

Upstream references (per-permutation definition):

| reference | flip rate |
|---|---|
| massive_intent.en, 20 options | 0.150 (laya) / 0.230 (multilingual) |
| en.emotion, 6 options | 0.040 / 0.090 |
| xnli.en, 3 options | 0.000 / 0.015 |
| Jev (third party) | 0.13 |
| zh CS routing / voice routing (multilingual) | 0.28 / 0.106 |

## T4_dev40 (all, n=40, 10 options)

- per-permutation flip by permutation: 0.050, 0.025, 0.025, 0.025, 0.050
- accuracy by permutation: 1.000, 0.975, 0.975, 0.975, 1.000 (original 0.950)
- identity permutations drawn: 0 of 200
- predicted labels, original: virtual card not working 3, top up failed 3, exchange via app 2, contactless not working 2, card payment fee charged 2, top up by card charge 2, card linking 1, exchange rate 1, pending cash withdrawal 1, fiat currency support 1, lost or stolen card 1, pending top up 1, cancel transfer 1, top up limits 1, balance not updated after bank transfer 1, supported cards and currencies 1, getting virtual card 1, disposable card limits 1, lost or stolen phone 1, card swallowed 1, verify source of funds 1, transfer timing 1, reverted card payment? 1, change pin 1, beneficiary not allowed 1, failed transfer 1, transfer into account 1, order physical card 1, get disposable virtual card 1, cash withdrawal not recognised 1, wrong amount of cash received 1, activate my card 1
- predicted labels, mean per permutation: virtual card not working 3.0, top up failed 3.0, exchange via app 2.0, contactless not working 2.0, card payment fee charged 2.0, cash withdrawal not recognised 2.0, top up by card charge 2.0, card linking 1.0, exchange rate 1.0, pending cash withdrawal 1.0, fiat currency support 1.0, lost or stolen card 1.0, pending top up 1.0, cancel transfer 1.0, top up limits 1.0, supported cards and currencies 1.0, getting virtual card 1.0, disposable card limits 1.0, lost or stolen phone 1.0, card swallowed 1.0, verify source of funds 1.0, transfer timing 1.0, reverted card payment? 1.0, change pin 1.0, beneficiary not allowed 1.0, failed transfer 1.0, transfer into account 1.0, order physical card 1.0, get disposable virtual card 1.0, activate my card 1.0, balance not updated after bank transfer 0.6, transfer not received by recipient 0.4
- chosen slot share under permutation (uniform 0.100): 0.105, 0.090, 0.085, 0.100, 0.090, 0.095, 0.095, 0.095, 0.140, 0.105; chi2 4.3, df 9, p 0.89
- accuracy by gold slot under permutation (slot: acc/n): 0: 0.952/21, 1: 1.000/18, 2: 1.000/17, 3: 1.000/19, 4: 1.000/18, 5: 0.950/20, 6: 0.950/20, 7: 1.000/19, 8: 1.000/28, 9: 1.000/20

| gold class | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| cash withdrawal not recognised | 2 | 0.500 | 0.500 | 0.500 | 1.000 |
| transfer not received by recipient | 1 | 0.400 | 1.000 | 0.000 | 0.400 |
| activate my card | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| beneficiary not allowed | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| cancel transfer | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| card linking | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| card payment fee charged | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| card swallowed | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| change pin | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| contactless not working | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| disposable card limits | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| exchange rate | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| exchange via app | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| failed transfer | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| fiat currency support | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| get disposable virtual card | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| getting virtual card | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| lost or stolen card | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| lost or stolen phone | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| order physical card | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| pending cash withdrawal | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| pending top up | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| reverted card payment? | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| supported cards and currencies | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| top up by card charge | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| top up failed | 3 | 0.000 | 0.000 | 1.000 | 1.000 |
| top up limits | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| transfer into account | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| transfer timing | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| verify source of funds | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| virtual card not working | 3 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order prediction | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| wrong amount of cash received | 1 | 1.000 | 1.000 | 0.000 | 1.000 |
| balance not updated after bank transfer | 1 | 0.400 | 1.000 | 0.000 | 0.400 |
| activate my card | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| beneficiary not allowed | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| cancel transfer | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| card linking | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| card payment fee charged | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| card swallowed | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| cash withdrawal not recognised | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| change pin | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| contactless not working | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| disposable card limits | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| exchange rate | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| exchange via app | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| failed transfer | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| fiat currency support | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| get disposable virtual card | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| getting virtual card | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| lost or stolen card | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| lost or stolen phone | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| order physical card | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| pending cash withdrawal | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| pending top up | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| reverted card payment? | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| supported cards and currencies | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| top up by card charge | 2 | 0.000 | 0.000 | 1.000 | 1.000 |
| top up failed | 3 | 0.000 | 0.000 | 1.000 | 1.000 |
| top up limits | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| transfer into account | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| transfer timing | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| verify source of funds | 1 | 0.000 | 0.000 | 1.000 | 1.000 |
| virtual card not working | 3 | 0.000 | 0.000 | 1.000 | 1.000 |

| original-order answer_confidence | n | per-perm flip | any-flip | orig acc | perm acc |
|---|---|---|---|---|---|
| [0.5, 0.7) | 1 | 1.000 | 1.000 | 0.000 | 1.000 |
| [0.9, 1.0] | 39 | 0.010 | 0.026 | 0.974 | 0.985 |

## run_card

| field | value |
|---|---|
| tool | scripts/probe_option_order.py |
| started_at | 2026-10-08T12:33:00+0900 |
| laya_version | 0.3.23 |
| torch | 2.14.1 |
| transformers | 5.18.0 |
| device | cpu |
| dtype | torch.float32 |
| amp_enabled | false |
| threads_intra_inter | [10, 1] |
| checkpoint | {"path": "poc/finetune/ckpt_t3arm/T4_run", "realpath": "/Users/banhun/banhun28/lab/benchmarkforLaya/poc/finetune/ckpt_t3arm/T4_run", "snapshot_sha": null, "weights_blob": null, "head_max_len": 192, "max_len": 512} |
| power | Now drawing from 'AC Power' \|  -InternalBattery-0 (id=22085731)	100%; charged; 0:00 remaining present: true |
| git_sha | null |
| load_seconds | 2.3 |
| warnings | [] |
| finished_at | 2026-10-08T12:33:19+0900 |
| total_seconds | 18.5 |
| dataset poc/finetune/data/t3arm/T4_dev40.jsonl | sha256 54210ef34b9ea0e45dcd235451f4d0349c15577a5614e6b2560e0bc478a930a0, questions_sha256 d0312cf7fce7ec7b285a3e542eeea97a1e79efa6ee7da7b37331364fbfa3e007, split rule state sha256 % 2, check null, 16s |
