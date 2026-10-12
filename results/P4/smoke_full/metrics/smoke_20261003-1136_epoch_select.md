Epoch choice on dev only: each epoch copy vs the final export `results/P4/smoke_full/smoke_20261003-1136_ft-smoke_domain8_dev.json` on the same 2012 rows. b = epoch right and final wrong, c = the reverse, exact two-sided McNemar.

| epoch report | acc | Δ vs final | b | c | McNemar p | argmax agreement |
|---|---|---|---|---|---|---|
| results/P4/smoke_full/smoke_20261003-1136_ft-smoke-ep1_domain8_dev.json | 0.5696 | +0.0000 | 0 | 0 | 1 | 1.0000 |

decision: v1 = final export (dev acc 0.5696); no epoch is more accurate on dev with p < 0.05
