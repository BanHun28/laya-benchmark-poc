| set | model | n | accuracy [Wilson 95%] | macro-F1 | Brier | ECE | NLL | mean conf | extra |
|---|---|---|---|---|---|---|---|---|---|
| T6_dev | english | 700 | 252/700 = 0.360 [0.325, 0.396] | 0.304 | 0.846 | 0.265 | 1.801 | 0.625 | score_mae_expected_level 0.886; within_1_level 0.634 |
| T6_dev | t3arm-T6-ep1 | 700 | 329/700 = 0.470 [0.433, 0.507] | 0.470 | 0.638 | 0.107 | 1.122 | 0.551 | score_mae_expected_level 0.571; within_1_level 0.849 |
| T6_dev | t3arm-T6-final | 700 | 365/700 = 0.521 [0.484, 0.558] | 0.510 | 0.605 | 0.075 | 1.051 | 0.567 | score_mae_expected_level 0.533; within_1_level 0.876 |
| T6_sst5_ext500 | t3arm-T6 | 500 | 289/500 = 0.578 [0.534, 0.621] | 0.580 | 0.538 | 0.039 | 0.962 | 0.590 | score_mae_expected_level 0.546; within_1_level 0.842 |
| T6_sst5_40 | t3arm-T6 | 40 | 29/40 = 0.725 [0.572, 0.839] | 0.731 | 0.435 | 0.141 | 0.792 | 0.584 | score_mae_expected_level 0.446; within_1_level 0.925 |
