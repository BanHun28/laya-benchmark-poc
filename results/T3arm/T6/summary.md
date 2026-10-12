| set | model | n | accuracy [Wilson 95%] | macro-F1 | Brier | ECE | NLL | mean conf | extra |
|---|---|---|---|---|---|---|---|---|---|
| T6_dev | english | 700 | 252/700 = 0.360 [0.325, 0.396] | 0.304 | 0.846 | 0.265 | 1.801 | 0.625 | score_mae_expected_level 0.886; within_1_level 0.634 |
| T6_dev | t3arm-T6-ep1 | 700 | 343/700 = 0.490 [0.453, 0.527] | 0.488 | 0.621 | 0.112 | 1.088 | 0.557 | score_mae_expected_level 0.559; within_1_level 0.854 |
| T6_dev | t3arm-T6-final | 700 | 354/700 = 0.506 [0.469, 0.543] | 0.501 | 0.594 | 0.059 | 1.043 | 0.535 | score_mae_expected_level 0.529; within_1_level 0.884 |
| T6_sst5_ext500 | t3arm-T6 | 500 | 295/500 = 0.590 [0.546, 0.632] | 0.592 | 0.530 | 0.074 | 0.936 | 0.551 | score_mae_expected_level 0.546; within_1_level 0.860 |
| T6_sst5_40 | t3arm-T6 | 40 | 27/40 = 0.675 [0.520, 0.799] | 0.675 | 0.461 | 0.153 | 0.824 | 0.534 | score_mae_expected_level 0.472; within_1_level 0.900 |
