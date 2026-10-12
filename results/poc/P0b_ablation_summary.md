# P0b zero-shot schema ablation summary (multilingual, n=30, own labels, no CI)

> An indicative measurement that previews part of 03 §8 C2/C3/C5 and B3/B4 on the 30 P0 probe sentences. It is not a verdict.
> The labels are the 1-person ad-hoc labels of the P0 probe (`results/poc/P0_probe_sentences.jsonl`, with its do-not-reuse header kept), and at n=30 a difference of 1\~2 items is noise. Read the figures as counts (x/30; binary totals x/120). No CI or tests.
> Runs: every variant `laya-evals run --model multilingual --device cpu --batch-size 8 --slice qid` (CPU fp32). The english control only for V0·V8. Latency was not measured (other experiments were running on the same machine at the same time).
> The §2 tables are the output of `.venv/bin/python results/poc/P0b_ablation_analyze.py` (`.venv/` is not included in the public repository) pasted untouched (only the heading levels were lowered by one). The run record (commands, hashes, verbatim warnings) is `results/poc/P0b_20261002.md`.

## 0. One-line conclusion

No variant brought intent up to 0.70 (6-class best 15/30, 4-class-equivalent best 20/30). No form of the 4 binary questions beat always-no (93/120) in total. A signal shows only per question: churn_risk + Korean criteria (V1) 28/30, and is_urgent + Korean instructions (V4) 26/30 with 5 positives (5 expected). frustration level-0 selection was 0/30 in all 10 multilingual runs.

## 1. Variant definitions

The instructions and option text that the model actually read are recorded per variant in `results/poc/P0b_build.log` (output of `laya.common.render_options`).

| Variant | Changed vs V0 | expected remapping |
|---|---|---|
| V0_v1 | None. `triage_v1.json` + `gateway_v1.json` merged into 7 questions; questions_sha256 identical to P0 (6b8bdadc…) | None |
| V1_criteria | Korean `true`/`false` criteria on the 4 noul. `triage_v1b.json` + the new `poc/schema/gateway_v1b.json` (needs_llm criteria in the wording of 05_poc_plan.md:268 verbatim) | None |
| V2_labels_ab | `"labels": {"true": "A", "false": "B"}` on the 4 noul. With no criteria, the options the model reads are `B: no, the statement does not hold` / `A: yes, the statement holds` (only the label tokens change) | None |
| V3a_choice_ab | The 4 noul turned into 2-choice. Keys `A` (meaning yes) / `B` (meaning no), descriptions in Korean. A is the first option (in noul the false option always comes first) | true→`A`, false→`B` |
| V3b_choice_semantic | The same descriptions as V3a with semantic keys: `urgent`/`not_urgent`, `refund_requested`/`no_refund_request`, `churn_risk`/`no_churn_risk`, `needs_llm`/`templated_ok` | true→first key, false→second key |
| V4_ko_instructions | The 7 instructions changed to Korean (backticked `message` kept; `refund_requested` has no field reference in the original, so it still has none). criteria unchanged | None |
| V5_intent4 | intent reduced to 4 options: billing / technical / cancellation / other (Korean descriptions as given in the instructions) | refund·billing_question→billing, technical_help→technical, cancellation→cancellation, information·other→other |
| V6_en_descriptions | intent and complexity criteria descriptions in English (literal translations of the Korean descriptions) | None |
| V7_plain_state | state as a string instead of `{"message": ...}`. Backticked fields removed from the instructions ("What does the customer want?", "Does the message communicate …" etc.) | None |
| V8_combo | The combination chosen by the §4 rules after measuring V1..V7 = the binary form of V2 + the English intent descriptions of V6. Everything else (complexity, frustration, instructions, state) as in V0 | None |

V3a/V3b description wording: for is_urgent, A = "기한, 마감, 즉시 처리 요구 등 시간 압박이 있음" (the example wording of the instructions verbatim; it lacks the "서비스 중단" (service outage) of triage_v1b and 05:242, §5-1), B = "시간 압박이 없음". refund_requested, churn_risk and needs_llm use the triage_v1b / gateway_v1b criteria wording verbatim.

## 2. Result tables (analyzer output as is)

### Summary table (n=30, self-labelled by one ad-hoc labeller, no CI; counts are x/30)

Binary cells: `correct/30 (pred pos k)`. intent of V5 is 4-class (see intent table for the like-for-like collapsed comparison). ml = multilingual, en = english control.

| variant | intent | complexity | is_urgent | refund_requested | churn_risk | needs_llm | binary Σ /120 | mean abs(pos-exp) | frustration MAE | level-0 pick (argmax) |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline / expected | majority 5/30 (4-class 10/30) | majority 12/30 | always-no 25/30 (exp pos 5) | always-no 24/30 (exp pos 6) | always-no 24/30 (exp pos 6) | always-no 20/30 (exp pos 10) | always-no 93 | - | always-0 0.700 | expected 18/30 |
| V0_v1 (ml) | 12/30 | 13/30 | 25/30 (pos 0) | 25/30 (pos 5) | 24/30 (pos 2) | 19/30 (pos 3) | 93 | 4.25 | 1.084 | 0/30 |
| V1_criteria (ml) | 12/30 | 13/30 | 26/30 (pos 1) | 18/30 (pos 18) | 28/30 (pos 8) | 15/30 (pos 15) | 87 | 5.75 | 1.084 | 0/30 |
| V2_labels_ab (ml) | 12/30 | 13/30 | 26/30 (pos 1) | 24/30 (pos 6) | 24/30 (pos 4) | 19/30 (pos 3) | 93 | 3.25 | 1.084 | 0/30 |
| V3a_choice_ab (ml) | 12/30 | 13/30 | 19/30 (pos 14) | 19/30 (pos 9) | 16/30 (pos 18) | 14/30 (pos 14) | 68 | 7.00 | 1.084 | 0/30 |
| V3b_choice_semantic (ml) | 12/30 | 13/30 | 25/30 (pos 4) | 25/30 (pos 3) | 22/30 (pos 4) | 16/30 (pos 16) | 88 | 3.00 | 1.084 | 0/30 |
| V4_ko_instructions (ml) | 12/30 | 12/30 | 26/30 (pos 5) | 21/30 (pos 11) | 24/30 (pos 4) | 18/30 (pos 18) | 89 | 3.75 | 1.104 | 0/30 |
| V5_intent4 (ml) | 17/30 (4-cl) | 13/30 | 25/30 (pos 0) | 25/30 (pos 5) | 24/30 (pos 2) | 19/30 (pos 3) | 93 | 4.25 | 1.084 | 0/30 |
| V6_en_descriptions (ml) | 15/30 | 13/30 | 25/30 (pos 0) | 25/30 (pos 5) | 24/30 (pos 2) | 19/30 (pos 3) | 93 | 4.25 | 1.084 | 0/30 |
| V7_plain_state (ml) | 13/30 | 11/30 | 25/30 (pos 0) | 26/30 (pos 4) | 24/30 (pos 0) | 16/30 (pos 6) | 91 | 4.25 | 1.221 | 0/30 |
| V8_combo (ml) | 15/30 | 13/30 | 26/30 (pos 1) | 24/30 (pos 6) | 24/30 (pos 4) | 19/30 (pos 3) | 93 | 3.25 | 1.084 | 0/30 |
| V0_v1 (en) | 7/30 | 13/30 | 26/30 (pos 3) | 22/30 (pos 2) | 22/30 (pos 6) | 15/30 (pos 17) | 85 | 3.25 | 0.880 | 26/30 |
| V8_combo (en) | 3/30 | 13/30 | 24/30 (pos 3) | 23/30 (pos 1) | 22/30 (pos 4) | 15/30 (pos 17) | 84 | 4.00 | 0.880 | 26/30 |

### Mean answer_confidence per question

| variant | intent | is_urgent | frustration | refund_requested | churn_risk | needs_llm | complexity |
|---|---|---|---|---|---|---|---|
| V0_v1 (ml) | 0.825 | 0.957 | 0.461 | 0.905 | 0.947 | 0.887 | 0.681 |
| V1_criteria (ml) | 0.825 | 0.923 | 0.461 | 0.751 | 0.885 | 0.621 | 0.681 |
| V2_labels_ab (ml) | 0.825 | 0.928 | 0.461 | 0.869 | 0.913 | 0.773 | 0.681 |
| V3a_choice_ab (ml) | 0.825 | 0.735 | 0.461 | 0.707 | 0.741 | 0.643 | 0.681 |
| V3b_choice_semantic (ml) | 0.825 | 0.870 | 0.461 | 0.827 | 0.732 | 0.754 | 0.681 |
| V4_ko_instructions (ml) | 0.827 | 0.923 | 0.479 | 0.885 | 0.882 | 0.680 | 0.675 |
| V5_intent4 (ml) | 0.829 | 0.957 | 0.461 | 0.905 | 0.947 | 0.887 | 0.681 |
| V6_en_descriptions (ml) | 0.742 | 0.957 | 0.461 | 0.905 | 0.947 | 0.887 | 0.680 |
| V7_plain_state (ml) | 0.777 | 0.979 | 0.391 | 0.897 | 0.932 | 0.859 | 0.603 |
| V8_combo (ml) | 0.742 | 0.928 | 0.461 | 0.869 | 0.913 | 0.773 | 0.681 |
| V0_v1 (en) | 0.338 | 0.851 | 0.561 | 0.930 | 0.845 | 0.867 | 0.407 |
| V8_combo (en) | 0.698 | 0.774 | 0.561 | 0.792 | 0.699 | 0.675 | 0.407 |

### Binary detail: TP/FN/FP (expected positives: is_urgent 5, refund_requested 6, churn_risk 6, needs_llm 10)

Post-hoc diagnostics, not part of the V8 rule: balanced accuracy = mean(TPR, TNR), always-no = 0.500. 'above & near' = binaries with accuracy strictly above always-no AND abs(pred pos - exp pos) <= 2 items.

| variant | form | is_urgent | refund_requested | churn_risk | needs_llm | mean balanced acc | above always-no & near expected |
|---|---|---|---|---|---|---|---|
| V0_v1 (ml) | noul | 0/5/0 | 3/3/2 | 1/5/1 | 1/9/2 | 0.568 | refund_requested |
| V1_criteria (ml) | noul | 1/4/0 | 6/0/12 | 6/0/2 | 5/5/10 | 0.702 | churn_risk |
| V2_labels_ab (ml) | noul | 1/4/0 | 3/3/3 | 2/4/2 | 1/9/2 | 0.603 | none |
| V3a_choice_ab (ml) | choice | 4/1/10 | 2/4/7 | 5/1/13 | 4/6/10 | 0.579 | none |
| V3b_choice_semantic (ml) | choice | 2/3/2 | 2/4/1 | 1/5/3 | 6/4/10 | 0.594 | none |
| V4_ko_instructions (ml) | noul | 3/2/2 | 4/2/7 | 2/4/2 | 8/2/10 | 0.681 | is_urgent |
| V5_intent4 (ml) | noul | 0/5/0 | 3/3/2 | 1/5/1 | 1/9/2 | 0.568 | refund_requested |
| V6_en_descriptions (ml) | noul | 0/5/0 | 3/3/2 | 1/5/1 | 1/9/2 | 0.568 | refund_requested |
| V7_plain_state (ml) | noul | 0/5/0 | 3/3/1 | 0/6/0 | 1/9/5 | 0.539 | refund_requested |
| V8_combo (ml) | noul | 1/4/0 | 3/3/3 | 2/4/2 | 1/9/2 | 0.603 | none |
| V0_v1 (en) | noul | 2/3/1 | 0/6/2 | 2/4/4 | 6/4/11 | 0.562 | is_urgent |
| V8_combo (en) | noul | 1/4/2 | 0/6/1 | 1/5/3 | 6/4/11 | 0.521 | none |

### Intent detail

collapsed-4 = the run's answers and labels mapped refund/billing_question->billing, technical_help->technical, information/other->other (V5 is natively 4-class). changed vs V0 = items whose answer differs from the same model's V0 run (V5 compared in the 4-class space).

| variant | intent | collapsed-4 | changed vs V0 | negation rows correct | top-3 confusions (expected→predicted ×n) |
|---|---|---|---|---|---|
| V0_v1 (ml) | 12/30 | 17/30 | 0/30 | 1/5 | information→technical_help ×3, refund→billing_question ×3, billing_question→refund ×1 |
| V1_criteria (ml) | 12/30 | 17/30 | 0/30 | 1/5 | information→technical_help ×3, refund→billing_question ×3, billing_question→refund ×1 |
| V2_labels_ab (ml) | 12/30 | 17/30 | 0/30 | 1/5 | information→technical_help ×3, refund→billing_question ×3, billing_question→refund ×1 |
| V3a_choice_ab (ml) | 12/30 | 17/30 | 0/30 | 1/5 | information→technical_help ×3, refund→billing_question ×3, billing_question→refund ×1 |
| V3b_choice_semantic (ml) | 12/30 | 17/30 | 0/30 | 1/5 | information→technical_help ×3, refund→billing_question ×3, billing_question→refund ×1 |
| V4_ko_instructions (ml) | 12/30 | 17/30 | 2/30 | 2/5 | information→technical_help ×4, refund→billing_question ×3, billing_question→refund ×1 |
| V5_intent4 (ml) | 17/30 | 17/30 | 9/30 | 3/5 | other→technical ×4, cancellation→billing ×2, billing→cancellation ×1 |
| V6_en_descriptions (ml) | 15/30 | 20/30 | 14/30 | 4/5 | information→technical_help ×3, other→information ×3, billing_question→refund ×2 |
| V7_plain_state (ml) | 13/30 | 17/30 | 11/30 | 2/5 | information→technical_help ×4, billing_question→refund ×3, other→cancellation ×3 |
| V8_combo (ml) | 15/30 | 20/30 | 14/30 | 4/5 | information→technical_help ×3, other→information ×3, billing_question→refund ×2 |
| V0_v1 (en) | 7/30 | 12/30 | 0/30 | 1/5 | billing_question→refund ×3, other→cancellation ×3, billing_question→cancellation ×2 |
| V8_combo (en) | 3/30 | 11/30 | 16/30 | 1/5 | information→other ×5, cancellation→other ×4, refund→other ×4 |

### Frustration detail (expected level-0 18/30)

| variant | MAE | exact level (argmax) | level-0 pick argmax | level-0 pick round(score) | score range |
|---|---|---|---|---|---|
| V0_v1 (ml) | 1.084 | 5/30 | 0/30 | 0/30 | 1.01-2.37 |
| V1_criteria (ml) | 1.084 | 5/30 | 0/30 | 0/30 | 1.01-2.37 |
| V2_labels_ab (ml) | 1.084 | 5/30 | 0/30 | 0/30 | 1.01-2.37 |
| V3a_choice_ab (ml) | 1.084 | 5/30 | 0/30 | 0/30 | 1.01-2.37 |
| V3b_choice_semantic (ml) | 1.084 | 5/30 | 0/30 | 0/30 | 1.01-2.37 |
| V4_ko_instructions (ml) | 1.104 | 7/30 | 0/30 | 0/30 | 0.91-2.25 |
| V5_intent4 (ml) | 1.084 | 5/30 | 0/30 | 0/30 | 1.01-2.37 |
| V6_en_descriptions (ml) | 1.084 | 5/30 | 0/30 | 0/30 | 1.01-2.37 |
| V7_plain_state (ml) | 1.221 | 5/30 | 0/30 | 0/30 | 1.24-2.36 |
| V8_combo (ml) | 1.084 | 5/30 | 0/30 | 0/30 | 1.01-2.37 |
| V0_v1 (en) | 0.880 | 16/30 | 26/30 | 4/30 | 0.31-1.57 |
| V8_combo (en) | 0.880 | 16/30 | 26/30 | 4/30 | 0.31-1.57 |

### Negation rows (P0 rows 4, 7, 10, 11, 29): false positive on the negated binary target

| variant | row 4 C | row 7 C | row 10 C | row 11 R | row 29 C | FP total |
|---|---|---|---|---|---|---|
| V0_v1 (ml) | ok 0.13 | ok 0.03 | ok 0.01 | FP 0.65 | ok 0.00 | 1/5 |
| V1_criteria (ml) | FP 0.66 | ok 0.22 | ok 0.35 | FP 0.87 | ok 0.03 | 2/5 |
| V2_labels_ab (ml) | FP 0.50 | ok 0.13 | ok 0.08 | FP 0.67 | ok 0.01 | 2/5 |
| V3a_choice_ab (ml) | FP 0.56 | ok 0.24 | ok 0.17 | ok 0.26 | FP 0.86 | 2/5 |
| V3b_choice_semantic (ml) | ok 0.17 | ok 0.13 | ok 0.20 | ok 0.01 | FP 0.55 | 1/5 |
| V4_ko_instructions (ml) | ok 0.07 | ok 0.03 | ok 0.27 | FP 0.94 | ok 0.02 | 1/5 |
| V5_intent4 (ml) | ok 0.13 | ok 0.03 | ok 0.01 | FP 0.65 | ok 0.00 | 1/5 |
| V6_en_descriptions (ml) | ok 0.13 | ok 0.03 | ok 0.01 | FP 0.65 | ok 0.00 | 1/5 |
| V7_plain_state (ml) | ok 0.45 | ok 0.01 | ok 0.01 | FP 0.67 | ok 0.00 | 1/5 |
| V8_combo (ml) | FP 0.50 | ok 0.13 | ok 0.08 | FP 0.67 | ok 0.01 | 2/5 |
| V0_v1 (en) | FP 0.85 | ok 0.10 | ok 0.18 | ok 0.01 | ok 0.22 | 1/5 |
| V8_combo (en) | FP 0.64 | ok 0.26 | ok 0.27 | ok 0.15 | ok 0.27 | 1/5 |

### Per-row intent answers (✗ = wrong; V5 codes B/T/C/O are 4-class)

| # | message | expected | V0_v1 (ml) | V1_criteria (ml) | V2_labels_ab (ml) | V3a_choice_ab (ml) | V3b_choice_semantic (ml) | V4_ko_instructions (ml) | V5_intent4 (ml) | V6_en_descriptions (ml) | V7_plain_state (ml) | V8_combo (ml) | V0_v1 (en) | V8_combo (en) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 같은 달 요금이 두 번 빠져나간 것 같… | rf | bq✗ | bq✗ | bq✗ | bq✗ | bq✗ | bq✗ | B | ot✗ | rf | ot✗ | rf | ot✗ |
| 1 | 어제 실수로 연간 플랜을 결제했어요ㅠㅠ… | rf | rf | rf | rf | rf | rf | rf | B | ca✗ | rf | ca✗ | ot✗ | ot✗ |
| 2 | 장난하세요? 분명히 해지했는데 이번 달… | rf | bq✗ | bq✗ | bq✗ | bq✗ | bq✗ | bq✗ | B | rf | rf | rf | rf | rf |
| 3 | 안녕하세요. 지난주 화요일부터 사흘간 … | rf | ca✗ | ca✗ | ca✗ | ca✗ | ca✗ | ca✗ | C✗ | rf | ca✗ | rf | rf | ot✗ |
| 4 | 서비스는 앞으로도 계속 쓸 거예요. 다… | rf | bq✗ | bq✗ | bq✗ | bq✗ | bq✗ | bq✗ | O✗ | rf | rf | rf | rf | ot✗ |
| 5 | 비밀번호 재설정 메일이 안 오는데 어떻… | th | bq✗ | bq✗ | bq✗ | bq✗ | bq✗ | bq✗ | O✗ | bq✗ | ca✗ | bq✗ | ot✗ | ot✗ |
| 6 | 결제 API가 30분째 500 에러만 … | th | rf✗ | rf✗ | rf✗ | rf✗ | rf✗ | rf✗ | B✗ | rf✗ | rf✗ | rf✗ | rf✗ | rf✗ |
| 7 | 해지할 생각은 없는데요, 요즘 앱이 하… | th | ca✗ | ca✗ | ca✗ | ca✗ | ca✗ | th | T | th | th | th | ca✗ | ot✗ |
| 8 | 안녕하세요. 슬랙 연동을 설정했는데 알… | th | th | th | th | th | th | th | T | th | th | th | th | ot✗ |
| 9 | 업데이트하고 나서 또 동기화가 안 되네… | th | th | th | th | th | th | th | T | th | th | th | rf✗ | rf✗ |
| 10 | 해지하고 싶지는 않고 요금제만 바꾸고 … | bq | bq | bq | bq | bq | bq | bq | B | bq | rf✗ | bq | ca✗ | ot✗ |
| 11 | 환불은 필요 없고요, 다음 결제부터는 … | bq | rf✗ | rf✗ | rf✗ | rf✗ | rf✗ | rf✗ | B | rf✗ | rf✗ | rf✗ | rf✗ | ot✗ |
| 12 | 이번 달 청구 금액이 평소보다 2만 원… | bq | bq | bq | bq | bq | bq | bq | B | bq | bq | bq | rf✗ | rf✗ |
| 13 | 세금계산서 발행 요청드립니다. 사업자등… | bq | bq | bq | bq | bq | bq | bq | B | rf✗ | rf✗ | rf✗ | rf✗ | rf✗ |
| 14 | 결제 수단을 등록하려는데 카드가 계속 … | bq | th✗ | th✗ | th✗ | th✗ | th✗ | th✗ | T✗ | ot✗ | th✗ | ot✗ | ca✗ | rf✗ |
| 15 | 프로 플랜이랑 팀 플랜 차이가 뭔가요?… | in | in | in | in | in | in | in | B✗ | in | in | in | ca✗ | ot✗ |
| 16 | 모바일 앱에서도 PDF로 내보내기가 되… | in | th✗ | th✗ | th✗ | th✗ | th✗ | th✗ | T✗ | th✗ | th✗ | th✗ | ot✗ | ot✗ |
| 17 | 안녕하세요. 저희 회사에서 도입을 검토… | in | th✗ | th✗ | th✗ | th✗ | th✗ | th✗ | O | th✗ | th✗ | th✗ | rf✗ | ot✗ |
| 18 | 내일 오전에 고객사 데모가 있는데, 화… | in | th✗ | th✗ | th✗ | th✗ | th✗ | th✗ | T✗ | th✗ | th✗ | th✗ | rf✗ | ot✗ |
| 19 | 고객센터 운영 시간이 어떻게 되나요? … | in | in | in | in | in | in | th✗ | T✗ | in | th✗ | in | ot✗ | ot✗ |
| 20 | 다음 달부터는 안 쓸 것 같아서요. 구… | ca | ca | ca | ca | ca | ca | ca | C | ca | ca | ca | ot✗ | ot✗ |
| 21 | 솔직히 가격 대비 너무 별로네요. 경쟁… | ca | ca | ca | ca | ca | ca | ca | B✗ | ot✗ | ca | ot✗ | rf✗ | rf✗ |
| 22 | 프로 플랜에서 무료 플랜으로 다운그레이… | ca | rf✗ | rf✗ | rf✗ | rf✗ | rf✗ | rf✗ | B✗ | ot✗ | th✗ | ot✗ | ca | ot✗ |
| 23 | 탈퇴하려는데 탈퇴 버튼이 어디에도 없네… | ca | ca | ca | ca | ca | ca | ca | C | ca | ca | ca | ot✗ | ot✗ |
| 24 | 안녕하세요. 회사 사정으로 이번 달 말… | ca | ca | ca | ca | ca | ca | ca | C | ca | ca | ca | rf✗ | ot✗ |
| 25 | 상담원분이 끝까지 친절하게 도와주셔서 … | ot | rf✗ | rf✗ | rf✗ | rf✗ | rf✗ | rf✗ | O | in✗ | rf✗ | in✗ | ca✗ | rf✗ |
| 26 | 채용 공고 보고 연락드렸는데, 지원서는… | ot | bq✗ | bq✗ | bq✗ | bq✗ | bq✗ | bq✗ | O | in✗ | ca✗ | in✗ | rf✗ | rf✗ |
| 27 | 어제 통화한 상담원 태도 진짜 최악이었… | ot | th✗ | th✗ | th✗ | th✗ | th✗ | th✗ | T✗ | ot | ca✗ | ot | ot | ot |
| 28 | 제휴 마케팅 관련해서 제안드리고 싶은데… | ot | in✗ | in✗ | in✗ | in✗ | in✗ | in✗ | O | in✗ | in✗ | in✗ | ca✗ | rf✗ |
| 29 | 해지 문의는 아니고요, 지난번에 요청드… | ot | ca✗ | ca✗ | ca✗ | ca✗ | ca✗ | ca✗ | C✗ | ot | ca✗ | ot | ca✗ | ot |

### Per-row binary answers (U=is_urgent R=refund_requested C=churn_risk L=needs_llm; letter = predicted positive)

| # | expected | V0_v1 (ml) | V1_criteria (ml) | V2_labels_ab (ml) | V3a_choice_ab (ml) | V3b_choice_semantic (ml) | V4_ko_instructions (ml) | V5_intent4 (ml) | V6_en_descriptions (ml) | V7_plain_state (ml) | V8_combo (ml) | V0_v1 (en) | V8_combo (en) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | -R-- | -R-- | -R-L | -R-- | -R-L | -R-L | -R-- | -R-- | -R-- | -R-L | -R-- | ---- | ---- |
| 1 | -R-- | ---- | -R-- | ---- | ---L | ---L | ---L | ---- | ---- | ---- | ---- | ---L | ---L |
| 2 | URCL | ---- | -RCL | ---- | U-CL | ---L | ---- | ---- | ---- | ---- | ---- | U--L | ---L |
| 3 | -R-L | -R-- | -R-L | -R-- | URC- | URC- | UR-- | -R-- | -R-- | -R-- | -R-- | ---L | ---L |
| 4 | -R-- | -R-- | -RC- | -RC- | U-C- | ---L | -R-L | -R-- | -R-- | -R-- | -RC- | U-CL | U-CL |
| 5 | ---- | ---- | ---L | ---- | ---L | ---L | ---L | ---- | ---- | ---L | ---- | ---- | ---- |
| 6 | U--L | --CL | -RCL | --CL | URCL | U-CL | UR-L | --CL | --CL | ---L | --CL | UR-- | UR-- |
| 7 | ---L | ---- | ---- | ---- | ---- | ---L | ---L | ---- | ---- | ---- | ---- | ---- | ---- |
| 8 | ---L | ---- | ---- | ---- | URCL | ---L | ---L | ---- | ---- | ---- | ---- | ---- | ---- |
| 9 | --CL | ---- | -RCL | ---- | -RC- | ---- | --CL | ---- | ---- | ---- | ---- | ---L | ---L |
| 10 | ---- | -R-- | -R-L | -R-- | ---- | ---- | -R-L | -R-- | -R-- | ---- | -R-- | ---L | ---L |
| 11 | ---- | -R-- | -R-L | -R-- | --CL | ---- | -RCL | -R-- | -R-- | -R-L | -R-- | ---- | ---- |
| 12 | ---L | ---- | -R-L | ---- | URCL | -R-L | ---L | ---- | ---- | ---- | ---- | ---- | ---- |
| 13 | U--- | ---L | UR-L | UR-L | UR-- | U--- | UR-L | ---L | ---L | ---L | UR-L | -RCL | --CL |
| 14 | ---- | ---- | ---L | ---- | URCL | ---L | -R-- | ---- | ---- | ---- | ---- | ---- | ---- |
| 15 | ---- | ---- | ---- | ---- | --CL | ---L | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 16 | ---- | ---- | ---- | ---- | --CL | ---L | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 17 | ---L | ---- | ---- | ---- | U--- | ---L | --CL | ---- | ---- | ---- | ---- | ---L | ---L |
| 18 | U--- | ---- | ---L | ---- | ---- | ---- | ---L | ---- | ---- | ---- | ---- | ---L | ---L |
| 19 | ---- | ---- | ---- | ---- | ---L | ---- | ---- | ---- | ---- | ---- | ---- | ---L | ---L |
| 20 | --C- | ---- | -RCL | ---- | --C- | --C- | ---- | ---- | ---- | ---- | ---- | --CL | ---L |
| 21 | --CL | ---- | -RC- | ---- | U-C- | ---- | -R-L | ---- | ---- | ---- | ---- | ---L | ---L |
| 22 | ---- | ---- | -R-- | ---- | --C- | ---- | ---L | ---- | ---- | ---- | ---- | ---L | ---L |
| 23 | U-C- | ---L | -RCL | --CL | U--- | ---L | UR-L | ---L | ---L | ---L | --CL | --CL | --CL |
| 24 | -RC- | --C- | -RC- | --C- | U-C- | U--- | URCL | --C- | --C- | ---- | --C- | ---- | ---- |
| 25 | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | U--- |
| 26 | ---- | ---- | -R-L | ---- | URCL | ---L | ---- | ---- | ---- | ---- | ---- | --CL | --CL |
| 27 | ---L | ---- | -R-- | ---- | --C- | ---- | ---L | ---- | ---- | ---- | ---- | --CL | ---L |
| 28 | ---- | ---- | ---- | ---- | U--L | ---L | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 29 | ---- | ---- | ---- | ---- | --C- | --C- | ---- | ---- | ---- | ---- | ---- | ---L | ---L |

### Sanity checks

- V0 (multilingual) answers identical to P0_probe_multilingual.json: 210/210 cases; questions_sha256 equal
- V0 (english) answers identical to P0_probe_english.json: 210/210 cases; questions_sha256 equal
- V1_criteria (ml): questions identical to V0 ['intent', 'frustration', 'complexity'] -> argmax flips 0, max abs(dp) 0.0000
- V2_labels_ab (ml): questions identical to V0 ['intent', 'frustration', 'complexity'] -> argmax flips 0, max abs(dp) 0.0000
- V3a_choice_ab (ml): questions identical to V0 ['intent', 'frustration', 'complexity'] -> argmax flips 0, max abs(dp) 0.0000
- V3b_choice_semantic (ml): questions identical to V0 ['intent', 'frustration', 'complexity'] -> argmax flips 0, max abs(dp) 0.0000
- V4_ko_instructions (ml): questions identical to V0 none -> argmax flips 0, max abs(dp) 0.0000
- V5_intent4 (ml): questions identical to V0 ['is_urgent', 'frustration', 'refund_requested', 'churn_risk', 'needs_llm', 'complexity'] -> argmax flips 0, max abs(dp) 0.0000
- V6_en_descriptions (ml): questions identical to V0 ['is_urgent', 'frustration', 'refund_requested', 'churn_risk', 'needs_llm'] -> argmax flips 0, max abs(dp) 0.0000
- V7_plain_state (ml): state differs from V0 (plain string), no question shared
- V8_combo (ml): questions identical to V0 ['frustration', 'complexity'] -> argmax flips 0, max abs(dp) 0.0000
- V8_combo (en): questions identical to V0 ['frustration', 'complexity'] -> argmax flips 0, max abs(dp) 0.0001
- every pair of runs (same model, same state form) that shares an identical question definition: 78 (run pair, question) combinations, argmax flips 0, max abs(dp) 0.0001
- per-qid accuracy / MAE recomputed from cases == report slices.qid for every run (asserted)

### V8 selection (rule in the analyzer docstring, applied mechanically to the multilingual V0..V7 runs)

- R1 binary form: totals V0_v1 93/120 (|pos-exp| 4.25), V1_criteria 87/120 (|pos-exp| 5.75), V2_labels_ab 93/120 (|pos-exp| 3.25), V3a_choice_ab 68/120 (|pos-exp| 7.00), V3b_choice_semantic 88/120 (|pos-exp| 3.00); max 93, tied (>= 91) ['V0_v1', 'V2_labels_ab'] -> V2_labels_ab
- R2 intent: V0 12/30, V6 15/30 -> en descriptions; V5 17/30 vs V6_en_descriptions collapsed-to-4 20/30 -> 6 classes
- R3 complexity: V0 13/30, V6 13/30 -> ko descriptions
- R4 Korean instructions: intent 12 vs 12, complexity 12 vs 13, binaries 89 vs 93 (|pos-exp| 3.75 vs 4.25), frustration MAE 1.104 vs 1.084 -> adopt for none
- R5 plain state: V7 115 vs V0 118 over intent+complexity+binaries (gain -3), frustration MAE 1.221 -> keep {"message": ...}
- selected: {"binary_form": "V2_labels_ab", "intent_desc": "en", "intent4": false, "complexity_desc": "ko", "ko_instructions": {"intent": false, "complexity": false, "binaries": false, "frustration": false}, "plain_state": false}

### Report `overall` (laya-evals aggregates; choice_accuracy pools every choice question of the run, so it is not comparable across variants whose question types differ; latency fields exist but are not reported)

| run | choice_accuracy | noul_accuracy | score_mae | ece | mean_confidence |
|---|---|---|---|---|---|
| V0_v1 (ml) | 0.4167 | 0.7750 | 1.0839 | 0.2114 | 0.8091 |
| V1_criteria (ml) | 0.4167 | 0.7250 | 1.0839 | 0.1588 | 0.7354 |
| V2_labels_ab (ml) | 0.4167 | 0.7750 | 1.0839 | 0.1933 | 0.7786 |
| V3a_choice_ab (ml) | 0.5167 | n/a (no noul) | 1.0839 | 0.2051 | 0.6846 |
| V3b_choice_semantic (ml) | 0.6278 | n/a (no noul) | 1.0839 | 0.1742 | 0.7359 |
| V4_ko_instructions (ml) | 0.4000 | 0.7417 | 1.1044 | 0.1842 | 0.7645 |
| V5_intent4 (ml) | 0.5000 | 0.7750 | 1.0839 | 0.1905 | 0.8096 |
| V6_en_descriptions (ml) | 0.4667 | 0.7750 | 1.0839 | 0.1919 | 0.7971 |
| V7_plain_state (ml) | 0.4000 | 0.7583 | 1.2211 | 0.2108 | 0.7768 |
| V8_combo (ml) | 0.4667 | 0.7750 | 1.0839 | 0.1665 | 0.7667 |
| V0_v1 (en) | 0.3333 | 0.7083 | 0.8802 | 0.1954 | 0.6856 |
| V8_combo (en) | 0.2667 | 0.7000 | 0.8802 | 0.1622 | 0.6579 |

### Run identity (from each report's config)

| run | report | dataset_sha256 | questions_sha256 | revision |
|---|---|---|---|---|
| V0_v1 (ml) | results/poc/P0b_V0_v1_multilingual.json | b3f4ec50f170555fb7db779b438059116373e3da23b9eca2e61f7658a9f71ef5 | 6b8bdadc8f9c718ed40f2510134caf52079a5dc0260e142d93d2132bee722c8a | 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 |
| V1_criteria (ml) | results/poc/P0b_V1_criteria_multilingual.json | e68b98c84e3e90ae7cc00484647c532b8c6507a34f590c3106ba5da7fc348b28 | 8ea18279f62ef606f642930f91c81350e5c2c0a20713a6fb5fc3b60660100819 | 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 |
| V2_labels_ab (ml) | results/poc/P0b_V2_labels_ab_multilingual.json | 69a0a21765d18d9c4c9f104db93ef619a886449790c3577a2159766de244691e | ca6e10c9909568d4022a31bc16ab3c94bdc9d41bdb77dbba532e44f986b022d9 | 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 |
| V3a_choice_ab (ml) | results/poc/P0b_V3a_choice_ab_multilingual.json | f1f57624c887db2139852abe6cfd13dc6cb24a26efa13e5bb92f7a04a1d15a8c | 186315603eae89574282da0cf56d3922b388eb16d2621929ed0dc6f9b2cb0dba | 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 |
| V3b_choice_semantic (ml) | results/poc/P0b_V3b_choice_semantic_multilingual.json | 69e9f2c56ea4e0d6cf1fadfd21d0064374327a25956597844e8bc29a8362a928 | 0938ff3c86e2665c25e57ccb43bc4003c32f8d49936240f85b84aa961aa2d6f3 | 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 |
| V4_ko_instructions (ml) | results/poc/P0b_V4_ko_instructions_multilingual.json | d6f4e64b2a892c9c7aac0db88b1577e3409a3af7434941c5520e2fc03bb0f293 | 5684b276c8cc174f743fae6f738706cb1c52955d87cdc2023056a94dcb5f538f | 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 |
| V5_intent4 (ml) | results/poc/P0b_V5_intent4_multilingual.json | 446825b142461a82416f9f6659e5f9d6afcfc64f51f12091f384907aaf0a8007 | 7ac4bb26c5abdadc214ca46a74287ffbed1777318bfca6b6fd58fc872756f302 | 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 |
| V6_en_descriptions (ml) | results/poc/P0b_V6_en_descriptions_multilingual.json | fc224d0752ed1803a0830e7827e48766dfc072e883222d59f59a5c17402fc27c | 1ae2d91472069e43eb24ef8e9e07e82c9855097779ad927df5d363e6fb6b9fbd | 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 |
| V7_plain_state (ml) | results/poc/P0b_V7_plain_state_multilingual.json | 6e8fe274b46f4f5282dbed7bb4307788d7e75d42d487582b978ea2ab7b192c73 | 05918e3c81314379e8c1488a1c3a6fc4e5049682b5317ab720877a29880a2df5 | 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 |
| V8_combo (ml) | results/poc/P0b_V8_combo_multilingual.json | 7f02ebe538438ae8ba51f3520ea1fe277e135577b4eef65a344d08083bc681c4 | 0f3536c007f3823e6520831fd5fb86637ff922ad212d4ce48f0ddf71d616d22c | 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 |
| V0_v1 (en) | results/poc/P0b_V0_v1_english.json | b3f4ec50f170555fb7db779b438059116373e3da23b9eca2e61f7658a9f71ef5 | 6b8bdadc8f9c718ed40f2510134caf52079a5dc0260e142d93d2132bee722c8a | 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 |
| V8_combo (en) | results/poc/P0b_V8_combo_english.json | 7f02ebe538438ae8ba51f3520ea1fe277e135577b4eef65a344d08083bc681c4 | 0f3536c007f3823e6520831fd5fb86637ff922ad212d4ce48f0ddf71d616d22c | 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 |

## 3. Notes per variant (multilingual; evidence in the §2 tables)

- **V0_v1**: a re-run of P0. The answers of all 210/210 cases equal the P0 report, and questions_sha256 is also the same (CPU fp32 determinism confirmed). The binary total 93/120 is exactly equal to always-no (is_urgent positives 0, refund 5, churn 2, needs_llm 3).
- **V1_criteria**: binary 87/120 (6 below always-no). But it has the largest discriminative signal (post-hoc balanced accuracy 0.702, the highest). churn_risk 28/30 (TP 6/6, FP 2, positives 8 vs 6 expected) is the only binary in this ablation that clearly beat always-no (+4). In contrast, refund_requested collapsed to the true side with 18/30 positives (TP 6/6, FP 12), and so did needs_llm with 15/30 positives (TP 5/10, FP 10), while is_urgent, with 1/30 positives, is still biased to no. The zh ladder's "adding criteria gives always-true" split by question in Korean. The binary answer_confidence went down (refund 0.905→0.751, needs_llm 0.887→0.621). Negation-row false positives 2/5 (row 4 churn 0.66, row 11 refund 0.87).
- **V2_labels_ab**: binary 93/120, the same as V0; the differences are about is_urgent TP +1 (row 13), refund positives 5→6, churn positives 2→4. For criteria-less noul only the label tokens (false/true → B/A) change and the option text stays the same, so the workaround of README #156 (third_party/laya/README.md:1440-1445, not included in the public repository; recreate it by cloning https://github.com/NandhaKishorM/laya at commit 4aa6761) did not remove the no bias of Korean multilingual.
- **V3a_choice_ab**: binary 68/120 (always-no −25). All four questions collapsed to the A side (positives is_urgent 14·FP 10, refund 9·FP 7, churn 18·FP 13, needs_llm 14·FP 10). answer_confidence 0.64\~0.74. The neutral-key 2-choice workaround of the README (README.md:1453-1458) was the worst here. However, the position difference (A (yes) is the first option) and the is_urgent wording difference (§5-1) overlap, so the cause could not be split between key and position.
- **V3b_choice_semantic**: binary 88/120. Its number of positives is closest to the expected (mean abs(pos−exp) 3.00, the minimum), but no question both beat always-no and matched the expected number of positives (refund 25/30 but positives 3 vs 6 expected, needs_llm positives 16·FP 10). With the same descriptions, changing only the keys from A/B → semantic keys moved 68 → 88. This directly shows the premise at 04_korean_evalset_spec.md:75 that choice keys are option text the model reads.
- **V4_ko_instructions**: binary 89/120 (−4), but its discriminative power is second only to V1 (balanced 0.681). is_urgent 26/30 with 5 positives = 5 expected (TP 3, FP 2), the only is_urgent variant whose number of positives matched the expected. needs_llm has TP 8/10 but FP 10; refund TP 4/6·FP 7. intent 12/30 (2 changed: row 7 fixed, row 19 broken), complexity 12/30 (−1), frustration MAE 1.104.
- **V5_intent4**: intent 17/30 (4-class, most-frequent baseline 10/30). Folding V0's 6-class answers into the same 4 classes also gives 17/30, and folding V6 gives 20/30. Asking again in 4 classes was no better than merging post hoc. In the 4-class space it differs from V0 on 9/30, with a net gain of 0. The main confusion is other→technical ×4. The other 6 questions have the same answers as V0.
- **V6_en_descriptions**: intent 15/30 (+3), 4-class-equivalent 20/30 (best overall). In exchange 14/30 changed: 6 fixed (rows 2, 3, 4, 7, 27, 29), 3 broken (1, 13, 21), 5 moved to a different wrong answer. It is a high-variance lever, so +3 at n=30 is weak evidence. Negation-row intent is 4/5 (V0 1/5): row 7 "해지할 생각은 없는데요" → technical_help and row 29 "해지 문의는 아니고요" → other were correct. row 11 "환불은 필요 없고요" is still refund. intent mean answer_confidence 0.825 → 0.742. complexity stays at 13/30 with English descriptions too.
- **V7_plain_state**: intent 13/30 (+1, 11/30 changed), complexity 11/30 (−2), binary 91/120 (−2, churn positives 0), frustration MAE 1.221 (worse). intent+complexity+binary total 115 vs V0 118. The state format changes many answers, but the net effect is negative.
- **V8_combo**: §4. The multilingual results (intent 15, complexity 13, binary 93 = 26/24/24/19, frustration 1.084, level 0 0/30) are exactly the values pre-computed from the component runs.
- **english control**: V0 en matches P0 english on 210/210 (intent 7/30, binary 85/120, frustration MAE 0.880, level-0 selection 26/30). V8 en got worse, with intent 3/30. Given English descriptions, the checkpoint that cannot read Hangul piled into `other` (information→other ×5, cancellation→other ×4, refund→other ×4). binary 84/120.
- **Common**: frustration level-0 selection is 0/30 in all 10 multilingual runs (both argmax and round, expected 18/30), and MAE is always ≥ 1.084, worse than the always-0 baseline of 0.700. Changing the instructions language or the state format leaves the #131 bias in place. complexity is 11\~13/30, around the most-frequent baseline of 12/30.
- **Independence of question rows**: with the same model and the same state format, identical question definitions gave identical answers even across variants (78 (run pair, question) combinations, argmax flip 0, max abs(Δp) 0.0001). Questions within one predict call do not affect each other, so per-question schema decisions can be made separately, without interactions with other questions (observed for this checkpoint, CPU fp32, batch 8).

## 4. V8 composition and rationale

**Rule**: fixed in the analyzer code (`select_v8`, module docstring) before reading the V1..V7 results. The MARGIN of 2 items is a heuristic for n=30, not a test.

| Step | Rule | Result of applying it | Choice |
|---|---|---|---|
| R1 binary form | Maximum binary total among V0/V1/V2/V3a/V3b. Anything within 2 of the maximum counts as a tie, broken by the minimum mean abs(pos−exp) | totals V0 93, V1 87, V2 93, V3a 68, V3b 88 → tie V0·V2, abs(pos−exp) 4.25 vs 3.25 | **V2** (noul + labels A/B) |
| R2 intent | English descriptions (V6) only if ≥ V0 +2. 4-class (V5) only if ≥ the chosen 6-class run folded to 4 classes +2 | V6 15 ≥ V0 12+2 → English descriptions. V5 17 < V6 folded 20+2 → keep 6-class | **V6 intent** (6-class, English descriptions) |
| R3 complexity | English descriptions only if ≥ V0 +2 | V6 13 = V0 13 | Korean descriptions (V0) |
| R4 Korean instructions | Per family: intent and complexity +2; binary total +2 with no worsening of abs(pos−exp); frustration MAE −0.10 | intent 12 vs 12, complexity 12 vs 13, binary 89 vs 93, MAE 1.104 vs 1.084 | None adopted (English kept) |
| R5 plain state | The intent+complexity+binary total of V7 ≥ V0 +3 and MAE worsening ≤ 0.10 | 115 vs 118 (−3), MAE 1.221 | `{"message": ...}` kept |

**Result**: V8 = the 4 binary questions of V2 + the intent of V6 + the complexity and frustration of V0. Because question rows are independent, the multilingual results were predicted exactly from the components before the run (intent 15/30, complexity 13/30, binary 93/120, frustration 1.084), and the run gave the same. V8 is a "sum of its parts" with no combination effect.

**Limitations and interpretation**:
- The values were chosen on the same 30 sentences and measured on the same 30 sentences, so there is an optimistic bias (winner's curse). They are not independent estimates.
- R1 puts accuracy first, as instructed, so V2 was picked at 93/120, the same as always-no. By post-hoc balanced accuracy the order is V1 0.702 > V4 0.681 > V2 0.603 > V0 0.568, and the questions that beat always-no are V1 churn_risk and V4 is_urgent. So V8 must not be carried into the P1 schema as is. 05_poc_plan.md:502 also plans to "adopt the dominant form per question" in P1, which is a different unit from this per-family rule.
- For reference (not a measurement; an upper bound on selection bias): combining the per-question best of the dict-state definitions already run (is_urgent V4, refund_requested V0, churn_risk V1, needs_llm V0), row independence makes the value on these 30 sentences compute to 26+25+28+19 = 98/120 (always-no 93). It was chosen four times on the same data, so it is only a candidate to validate in P1.

## 5. Discrepancies with the docs and the instructions

1. The V3a is_urgent example wording in the instructions, "기한, 마감, 즉시 처리 요구 등 시간 압박이 있음", lacks the "서비스 중단" (service outage) of "기한, 마감, 즉시 처리 요구, 서비스 중단 등 시간 압박이 있음" in 05_poc_plan.md:242 / `triage_v1b.json`. The instructions were followed as given, so the V1 ↔ V3a/V3b is_urgent comparison mixes the form difference with a wording difference (it may affect outage sentences such as row 6 "결제 API … 500 에러").
2. `results/poc/P0_20261002.md:184` and `:187` state "the v1b criteria for needs_llm are not defined in the docs (05:268)", but 05_poc_plan.md:268 now has a definition (05 modified at 14:07:49 > P0 card 14:05:54). `gateway_v1b.json` was built from the 05:268 wording. That item of the P0 card is stale (the P0_* files are not modified).
3. The probe number cross-references disagree. 05_poc_plan.md:275 lists the `labels: {"true":"A","false":"B"}` variant as C5, but 03_benchmark_plan.md:395 puts it in C3, and C5 at 03:403 is a comparison that changes the choice keys to `yes`/`no`, semantic keys and `A`/`B`. 05_poc_plan.md:502 calls the noul vs 2-choice comparison "Track C4/C5", whereas in 03 it is C3 (03:393) and C4 is negation (03:397). The `yes`/`no` key variant of 03:403 was outside the scope of these instructions and was not run.
4. The upstream evidence and the measurements differ. third_party/laya/README.md:1450-1451 ("criteria-less noul of multilingual read the state"), :1440-1445 (labels A/B workaround) and :1453-1458 (neutral-key 2-choice workaround) were not reproduced on Korean multilingual. V0·V2 binary equal always-no at 93/120, and V3a collapsed to A (68/120). 05:239·04:81 already carry a caveat from the P0 results, so what needs fixing are the expectations at 03:395 (C3)·05:275.

**English** | [한국어](P0b_ablation_summary.ko.md)
