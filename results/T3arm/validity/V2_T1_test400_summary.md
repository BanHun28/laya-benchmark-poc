| set | model | n | accuracy [Wilson 95%] | macro-F1 | Brier | ECE | NLL | mean conf | extra |
|---|---|---|---|---|---|---|---|---|---|
| T1_typed_decisions_test400 | typed-decisions | 2000 | 1534/2000 = 0.767 [0.748, 0.785] | - | 0.400 | 0.214 | 0.708 | 0.553 | accuracy_vs_upstream_label 0.766; soft_accuracy 0.471; brier_vs_soft 0.061; score_mae 0.242; within_1_level 0.995 |
| T1_typed_decisions_test400 | english | 2000 | 727/2000 = 0.363 [0.343, 0.385] | - | 0.749 | 0.173 | 1.330 | 0.536 | accuracy_vs_upstream_label 0.361; soft_accuracy 0.331; brier_vs_soft 0.316; score_mae 0.694; within_1_level 0.752 |
| T1_typed_decisions_test400 | multilingual | 2000 | 702/2000 = 0.351 [0.330, 0.372] | - | 0.893 | 0.316 | 1.877 | 0.663 | accuracy_vs_upstream_label 0.352; soft_accuracy 0.328; brier_vs_soft 0.463; score_mae 0.760; within_1_level 0.700 |
| T1_typed_decisions_test400 | v2-T1-ep1 | 2000 | 1409/2000 = 0.705 [0.684, 0.724] | - | 0.451 | 0.182 | 0.792 | 0.522 | accuracy_vs_upstream_label 0.705; soft_accuracy 0.442; brier_vs_soft 0.090; score_mae 0.325; within_1_level 0.976 |
| T1_typed_decisions_test400 | v2-T1 | 2000 | 1492/2000 = 0.746 [0.726, 0.765] | - | 0.381 | 0.148 | 0.666 | 0.599 | accuracy_vs_upstream_label 0.747; soft_accuracy 0.495; brier_vs_soft 0.059; score_mae 0.253; within_1_level 0.991 |
