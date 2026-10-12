| set | model | n | accuracy [Wilson 95%] | macro-F1 | Brier | ECE | NLL | mean conf | extra |
|---|---|---|---|---|---|---|---|---|---|
| T1_dev | english | 600 | 219/600 = 0.365 [0.327, 0.404] | - | 0.761 | 0.172 | 1.380 | 0.537 | score_mae_expected_level 0.837; within_1_level 0.625 |
| T1_dev | t3arm-T1-ep1 | 600 | 400/600 = 0.667 [0.628, 0.703] | - | 0.490 | 0.173 | 0.861 | 0.493 | score_mae_expected_level 0.600; within_1_level 0.800 |
| T1_dev | t3arm-T1-final | 600 | 410/600 = 0.683 [0.645, 0.719] | - | 0.440 | 0.122 | 0.763 | 0.573 | score_mae_expected_level 0.580; within_1_level 0.833 |
| T1_typed_decisions_test400 | t3arm-T1 | 2000 | 1373/2000 = 0.686 [0.666, 0.706] | - | 0.434 | 0.112 | 0.744 | 0.574 | accuracy_vs_upstream_label 0.690; soft_accuracy 0.463; brier_vs_soft 0.099; score_mae 0.359; within_1_level 0.931 |
| T1_typed_decisions_40 | t3arm-T1 | 200 | 137/200 = 0.685 [0.618, 0.745] | - | 0.426 | 0.121 | 0.738 | 0.572 | accuracy_vs_upstream_label 0.680; soft_accuracy 0.458; brier_vs_soft 0.113; score_mae 0.368; within_1_level 0.912 |
