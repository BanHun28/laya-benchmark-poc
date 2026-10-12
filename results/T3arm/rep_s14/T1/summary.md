| set | model | n | accuracy [Wilson 95%] | macro-F1 | Brier | ECE | NLL | mean conf | extra |
|---|---|---|---|---|---|---|---|---|---|
| T1_dev | english | 600 | 219/600 = 0.365 [0.327, 0.404] | - | 0.761 | 0.172 | 1.380 | 0.537 | score_mae_expected_level 0.837; within_1_level 0.625 |
| T1_dev | t3arm-T1-ep1 | 600 | 421/600 = 0.702 [0.664, 0.737] | - | 0.472 | 0.194 | 0.826 | 0.508 | score_mae_expected_level 0.581; within_1_level 0.879 |
| T1_dev | t3arm-T1-final | 600 | 450/600 = 0.750 [0.714, 0.783] | - | 0.407 | 0.155 | 0.716 | 0.595 | score_mae_expected_level 0.505; within_1_level 0.900 |
| T1_typed_decisions_test400 | t3arm-T1 | 2000 | 1470/2000 = 0.735 [0.715, 0.754] | - | 0.391 | 0.144 | 0.677 | 0.592 | accuracy_vs_upstream_label 0.735; soft_accuracy 0.491; brier_vs_soft 0.063; score_mae 0.262; within_1_level 0.995 |
| T1_typed_decisions_40 | t3arm-T1 | 200 | 156/200 = 0.780 [0.718, 0.832] | - | 0.370 | 0.190 | 0.652 | 0.596 | accuracy_vs_upstream_label 0.775; soft_accuracy 0.497; brier_vs_soft 0.060; score_mae 0.241; within_1_level 1.000 |
