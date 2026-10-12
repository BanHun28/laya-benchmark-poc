Epoch choice on dev only: each epoch copy vs the final export `results/P4/full_20261003-1156_ft-v1_domain8_dev.json` on the same 2012 rows. b = epoch right and final wrong, c = the reverse, exact two-sided McNemar.

| epoch report | acc | Δ vs final | b | c | McNemar p | argmax agreement |
|---|---|---|---|---|---|---|
| results/P4/full_20261003-1156_ft-v1-ep1_domain8_dev.json | 0.8917 | -0.0268 | 34 | 88 | 1.08e-06 | 0.9235 |
| results/P4/full_20261003-1156_ft-v1-ep2_domain8_dev.json | 0.9160 | -0.0025 | 16 | 21 | 0.511 | 0.9742 |
| results/P4/full_20261003-1156_ft-v1-ep3_domain8_dev.json | 0.9185 | +0.0000 | 0 | 0 | 1 | 1.0000 |

decision: v1 = final export (dev acc 0.9185); no epoch is more accurate on dev with p < 0.05
