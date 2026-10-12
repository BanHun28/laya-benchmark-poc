| set | model | n | accuracy [Wilson 95%] | macro-F1 | Brier | ECE | NLL | mean conf | extra |
|---|---|---|---|---|---|---|---|---|---|
| T6_dev | english | 16 | 5/16 = 0.312 [0.142, 0.556] | 0.266 | 0.869 | 0.402 | 1.683 | 0.676 | score_mae_expected_level 0.735; within_1_level 0.750 |
| T6_dev | t3arm-T6-final | 16 | 6/16 = 0.375 [0.185, 0.614] | 0.336 | 0.793 | 0.342 | 1.441 | 0.593 | score_mae_expected_level 0.707; within_1_level 0.625 |
| T6_sst5_ext500 | t3arm-T6 | 8 | 4/8 = 0.500 [0.215, 0.785] | 0.448 | 0.398 | 0.261 | 0.659 | 0.576 | score_mae_expected_level 0.364; within_1_level 1.000 |
| T6_sst5_40 | t3arm-T6 | 8 | 6/8 = 0.750 [0.409, 0.929] | 0.638 | 0.378 | 0.291 | 0.683 | 0.551 | score_mae_expected_level 0.412; within_1_level 1.000 |
