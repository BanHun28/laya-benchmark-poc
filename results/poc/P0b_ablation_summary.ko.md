# P0b zero-shot 스키마 ablation 요약 (multilingual, n=30, 자체 라벨, CI 없음)

> 03 §8 C2/C3/C5 와 B3/B4 일부를 P0 프로브 30문장으로 앞당겨 본 지시용 측정이다. 판정이 아니다.
> 라벨은 P0 프로브의 1인 ad-hoc 라벨(`results/poc/P0_probe_sentences.jsonl`, 재사용 금지 헤더 유지)이고 n=30 이라 1\~2건 차이는 노이즈 수준이다. 수치는 건수(x/30, binary 합계는 x/120)로 읽는다. CI·검정 없음.
> 실행: 모든 변형 `laya-evals run --model multilingual --device cpu --batch-size 8 --slice qid` (CPU fp32). english 대조군은 V0·V8 만. 레이턴시는 측정하지 않았다(같은 머신에서 다른 실험이 동시 진행).
> §2 표는 `.venv/bin/python results/poc/P0b_ablation_analyze.py`(`.venv/`는 공개 저장소에는 포함하지 않음) 출력을 손대지 않고 붙였다(제목 수준만 한 단계 내림). 실행 기록(명령어, 해시, 경고 원문)은 `results/poc/P0b_20261002.md`.

## 0. 한 줄 결론

intent 는 어떤 변형도 0.70 에 못 미쳤다(6-class 최고 15/30, 4-class 환산 최고 20/30). binary 4문항은 어떤 형태도 합계로 always-no(93/120)를 넘지 못했다. 신호는 질문 단위로만 보인다: churn_risk + 한국어 criteria(V1) 28/30, is_urgent + 한국어 instructions(V4) 26/30 에 양성 5건(기대 5건). frustration 레벨 0 선택은 multilingual 10개 실행 모두 0/30.

## 1. 변형 정의

모델이 실제로 읽은 instructions·옵션 텍스트는 `results/poc/P0b_build.log` 에 변형별로 남겼다(`laya.common.render_options` 출력).

| 변형 | V0 대비 바꾼 것 | expected 재매핑 |
|---|---|---|
| V0_v1 | 없음. `triage_v1.json` + `gateway_v1.json` 병합 7문항, questions_sha256 이 P0 와 같음(6b8bdadc…) | 없음 |
| V1_criteria | noul 4개에 한국어 `true`/`false` criteria. `triage_v1b.json` + 새 `poc/schema/gateway_v1b.json`(needs_llm criteria 는 05_poc_plan.md:268 문구 그대로) | 없음 |
| V2_labels_ab | noul 4개에 `"labels": {"true": "A", "false": "B"}`. criteria 가 없어서 모델이 읽는 옵션은 `B: no, the statement does not hold` / `A: yes, the statement holds` (label 토큰만 바뀜) | 없음 |
| V3a_choice_ab | noul 4개를 2-choice 로 바꿈. key `A`(예 의미) / `B`(아니오 의미), 설명은 한국어. A 가 첫 옵션(noul 은 항상 false 옵션이 먼저) | true→`A`, false→`B` |
| V3b_choice_semantic | V3a 와 같은 설명에 의미 key: `urgent`/`not_urgent`, `refund_requested`/`no_refund_request`, `churn_risk`/`no_churn_risk`, `needs_llm`/`templated_ok` | true→첫 key, false→둘째 key |
| V4_ko_instructions | instructions 7개를 한국어로 바꿈(백틱 `message` 유지. `refund_requested` 는 원문에 필드 지칭이 없어 그대로 없음). criteria 그대로 | 없음 |
| V5_intent4 | intent 를 4옵션으로 줄임: billing / technical / cancellation / other (지시받은 한국어 설명) | refund·billing_question→billing, technical_help→technical, cancellation→cancellation, information·other→other |
| V6_en_descriptions | intent·complexity criteria 설명을 영어로(한국어 설명 직역) | 없음 |
| V7_plain_state | state 를 `{"message": ...}` 대신 문자열로. instructions 에서 백틱 필드 제거("What does the customer want?", "Does the message communicate …" 등) | 없음 |
| V8_combo | V1..V7 측정 뒤 §4 규칙으로 고른 조합 = V2 의 binary 형태 + V6 의 intent 영어 설명. 나머지(complexity·frustration·instructions·state)는 V0 | 없음 |

V3a/V3b 설명 문구: is_urgent 는 A = "기한, 마감, 즉시 처리 요구 등 시간 압박이 있음"(지시문 예시 문구 그대로. triage_v1b 와 05:242 의 "서비스 중단"이 빠져 있음, §5-1), B = "시간 압박이 없음". refund_requested·churn_risk·needs_llm 은 triage_v1b / gateway_v1b criteria 문구 그대로.

## 2. 결과 표 (analyzer 출력 그대로)

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

## 3. 변형별 노트 (multilingual, 근거는 §2 표)

- **V0_v1**: P0 재실행. 210/210 case 의 answer 가 P0 리포트와 같고 questions_sha256 도 같다(CPU fp32 결정론 확인). binary 합계 93/120 은 always-no 와 정확히 같다(is_urgent 양성 0, refund 5, churn 2, needs_llm 3).
- **V1_criteria**: binary 87/120 (always-no 보다 6건 낮음). 하지만 판별 신호는 가장 크다(사후 balanced accuracy 0.702, 최고). churn_risk 28/30 (TP 6/6, FP 2, 양성 8 vs 기대 6)는 이 ablation 에서 always-no 를 분명히 넘은 유일한 binary 다(+4). 반면 refund_requested 는 양성 18/30 (TP 6/6, FP 12), needs_llm 은 양성 15/30 (TP 5/10, FP 10)으로 true 쪽 붕괴, is_urgent 는 양성 1/30 으로 여전히 no 편향이다. zh 사다리의 "criteria 를 붙이면 always-true"는 한국어에서 질문별로 갈렸다. binary answer_confidence 는 내려갔다(refund 0.905→0.751, needs_llm 0.887→0.621). 부정문 행 오탐 2/5 (row 4 churn 0.66, row 11 refund 0.87).
- **V2_labels_ab**: binary 93/120 으로 V0 와 같고, 차이는 is_urgent TP +1(row 13), refund 양성 5→6, churn 양성 2→4 정도다. criteria 가 없는 noul 에서는 label 토큰(false/true → B/A)만 바뀌고 옵션 본문은 그대로라서, README #156 의 우회(third_party/laya/README.md:1440-1445, 공개 저장소에는 포함하지 않음. https://github.com/NandhaKishorM/laya 를 커밋 4aa6761로 clone하면 재현된다)가 한국어 multilingual 의 no 편향을 풀지 못했다.
- **V3a_choice_ab**: binary 68/120 (always-no −25). 네 질문 모두 A 쪽으로 붕괴했다(양성 is_urgent 14·FP 10, refund 9·FP 7, churn 18·FP 13, needs_llm 14·FP 10). answer_confidence 0.64\~0.74. README 의 중립 key 2-choice 우회(README.md:1453-1458)가 여기서는 가장 나빴다. 다만 A(예)가 첫 옵션이라는 위치 차이와 is_urgent 문구 차이(§5-1)가 겹쳐 있어서, 원인을 key 와 위치로 나누지 못했다.
- **V3b_choice_semantic**: binary 88/120. 양성 수는 기대에 가장 가깝지만(mean abs(pos−exp) 3.00, 최소) always-no 를 넘으면서 양성 수도 맞은 질문은 없다(refund 25/30 이지만 양성 3 vs 기대 6, needs_llm 양성 16·FP 10). 같은 설명에서 key 만 A/B → 의미 key 로 바꿨더니 68 → 88 이 됐다. choice key 는 모델이 읽는 옵션 텍스트라는 04_korean_evalset_spec.md:75 의 전제를 그대로 보여준다.
- **V4_ko_instructions**: binary 89/120 (−4)이지만 판별력은 V1 다음이다(balanced 0.681). is_urgent 26/30 에 양성 5 = 기대 5 (TP 3, FP 2)로, 양성 수가 기대와 맞은 유일한 is_urgent 변형이다. needs_llm 은 TP 8/10 이지만 FP 10, refund 는 TP 4/6·FP 7. intent 12/30 (2건 변경: row 7 수정, row 19 깨짐), complexity 12/30 (−1), frustration MAE 1.104.
- **V5_intent4**: intent 17/30 (4-class, 최빈 기저 10/30). V0 의 6-class 답을 같은 4-class 로 접어도 17/30, V6 를 접으면 20/30 이다. 4-class 로 다시 묻는 것은 사후 병합보다 나을 게 없었다. 4-class 기준으로 V0 와 9/30 이 다른데 순증은 0. 주요 혼동은 other→technical ×4. 나머지 6문항은 V0 와 답이 같다.
- **V6_en_descriptions**: intent 15/30 (+3), 4-class 환산 20/30 (전체 최고). 대신 14/30 이 바뀌었다: 6건 수정(rows 2, 3, 4, 7, 27, 29), 3건 깨짐(1, 13, 21), 5건은 다른 오답으로 이동. 변동이 큰 레버라 n=30 의 +3 은 약한 근거다. 부정문 행 intent 는 4/5 (V0 1/5): row 7 "해지할 생각은 없는데요" → technical_help, row 29 "해지 문의는 아니고요" → other 로 맞았다. row 11 "환불은 필요 없고요" 는 여전히 refund. intent mean answer_confidence 0.825 → 0.742. complexity 는 영어 설명으로도 13/30 그대로다.
- **V7_plain_state**: intent 13/30 (+1, 11/30 변경), complexity 11/30 (−2), binary 91/120 (−2, churn 양성 0), frustration MAE 1.221 (악화). intent+complexity+binary 합 115 vs V0 118. state 형식은 답을 많이 바꾸지만 순효과는 마이너스다.
- **V8_combo**: §4. multilingual 결과(intent 15, complexity 13, binary 93 = 26/24/24/19, frustration 1.084, 레벨 0 0/30)는 부품 실행에서 미리 계산한 값과 정확히 같다.
- **english 대조군**: V0 en 은 P0 english 와 210/210 같다(intent 7/30, binary 85/120, frustration MAE 0.880, 레벨 0 선택 26/30). V8 en 은 intent 3/30 으로 더 나빠졌다. 영어 설명을 주자 한글을 읽지 못하는 체크포인트가 `other` 로 몰렸다(information→other ×5, cancellation→other ×4, refund→other ×4). binary 84/120.
- **공통**: frustration 레벨 0 선택이 multilingual 10개 실행 모두 0/30 (argmax·round 둘 다, 기대 18/30)이고 MAE 는 항상 ≥ 1.084 로 always-0 기저 0.700 보다 나쁘다. instructions 언어·state 형식을 바꿔도 #131 편향이 그대로다. complexity 는 11\~13/30 으로 최빈 기저 12/30 수준이다.
- **질문 row 독립성**: 같은 모델·같은 state 형식에서 질문 정의가 같으면 변형이 달라도 답이 같았다(78개 (실행 쌍, 질문) 조합, argmax flip 0, max abs(Δp) 0.0001). 한 predict 호출 안의 질문끼리는 서로 영향을 주지 않으므로, 질문별 스키마 결정은 다른 질문과의 상호작용 없이 따로 내려도 된다(이 체크포인트, CPU fp32, batch 8 에서 관찰).

## 4. V8 구성과 근거

**규칙**: V1..V7 결과를 읽기 전에 analyzer 코드(`select_v8`, 모듈 docstring)로 고정했다. MARGIN 2건은 n=30 에 대한 휴리스틱이고 검정이 아니다.

| 단계 | 규칙 | 적용 결과 | 선택 |
|---|---|---|---|
| R1 binary 형태 | V0/V1/V2/V3a/V3b 중 binary 합계 최대. 최대에서 2건 이내는 동률로 보고 mean abs(pos−exp) 최소 | 합계 V0 93, V1 87, V2 93, V3a 68, V3b 88 → 동률 V0·V2, abs(pos−exp) 4.25 vs 3.25 | **V2** (noul + labels A/B) |
| R2 intent | 영어 설명(V6)은 V0 +2 이상일 때만. 4-class(V5)는 고른 6-class 실행을 4-class 로 접은 값 +2 이상일 때만 | V6 15 ≥ V0 12+2 → 영어 설명. V5 17 < V6 접은 값 20+2 → 6-class 유지 | **V6 intent** (6-class, 영어 설명) |
| R3 complexity | 영어 설명은 V0 +2 이상일 때만 | V6 13 = V0 13 | 한국어 설명(V0) |
| R4 한국어 instructions | family 별로: intent·complexity +2, binary 합계 +2 이면서 abs(pos−exp) 악화 없음, frustration MAE −0.10 | intent 12 vs 12, complexity 12 vs 13, binary 89 vs 93, MAE 1.104 vs 1.084 | 채택 없음(영어 유지) |
| R5 plain state | V7 의 intent+complexity+binary 합이 V0 +3 이상이고 MAE 악화 0.10 이하 | 115 vs 118 (−3), MAE 1.221 | `{"message": ...}` 유지 |

**결과**: V8 = V2 의 binary 4문항 + V6 의 intent + V0 의 complexity·frustration. 질문 row 가 독립이므로 multilingual 결과는 실행 전에 부품에서 정확히 예측됐고(intent 15/30, complexity 13/30, binary 93/120, frustration 1.084), 실행 결과도 같았다. V8 은 조합 효과가 없는 "부품의 합"이다.

**한계와 해석**:
- 같은 30문장으로 고르고 같은 30문장으로 잰 값이라 낙관 편향(winner's curse)이 있다. 독립 추정치가 아니다.
- R1 이 지시대로 accuracy 우선이어서 always-no 와 같은 93/120 인 V2 가 뽑혔다. 사후 balanced accuracy 로 보면 V1 0.702 > V4 0.681 > V2 0.603 > V0 0.568 이고, always-no 를 넘은 질문은 V1 churn_risk 와 V4 is_urgent 에 있다. 그러니 V8 을 그대로 P1 스키마로 가져가면 안 된다. 05_poc_plan.md:502 도 P1 에서 "질문별로 우세 형태 채택"을 계획하고 있어서 family 단위인 이 규칙과 단위가 다르다.
- 참고(측정 아님, 선택 편향 상한): 이미 실행한 dict-state 정의 중 질문별 최선(is_urgent V4, refund_requested V0, churn_risk V1, needs_llm V0)을 묶으면 row 독립성 때문에 이 30문장에서의 값이 26+25+28+19 = 98/120 으로 계산된다(always-no 93). 같은 데이터로 네 번 고른 값이라 P1 에서 검증할 후보일 뿐이다.

## 5. 문서·지시와 어긋난 점

1. 지시문의 V3a is_urgent 예시 문구 "기한, 마감, 즉시 처리 요구 등 시간 압박이 있음"은 05_poc_plan.md:242 / `triage_v1b.json` 의 "기한, 마감, 즉시 처리 요구, 서비스 중단 등 시간 압박이 있음"에서 "서비스 중단"이 빠져 있다. 지시문을 그대로 따랐으므로 V1 ↔ V3a/V3b 의 is_urgent 비교에는 형태 차이에 문구 차이가 섞여 있다(row 6 "결제 API … 500 에러" 같은 장애 문장에 영향 가능).
2. `results/poc/P0_20261002.md:184`, `:187` 은 "needs_llm 의 v1b criteria 는 문서에 정의가 없다(05:268)"고 적었지만, 현재 05_poc_plan.md:268 에는 정의가 있다(05 수정 시각 14:07:49 > P0 카드 14:05:54). `gateway_v1b.json` 은 05:268 문구로 만들었다. P0 카드의 해당 항목은 stale 이다(P0_* 파일은 수정하지 않음).
3. probe 번호 교차참조가 어긋난다. 05_poc_plan.md:275 는 `labels: {"true":"A","false":"B"}` 변형을 C5 로 적었지만 03_benchmark_plan.md:395 는 그것을 C3 에 두고, 03:403 의 C5 는 choice key 를 `yes`/`no`·의미 key·`A`/`B` 로 바꾸는 비교다. 05_poc_plan.md:502 는 noul vs 2-choice 비교를 "Track C4/C5"로 적었는데, 03 에서는 C3(03:393)이고 C4 는 부정문(03:397)이다. 03:403 의 `yes`/`no` key 변형은 이번 지시 범위에 없어 돌리지 않았다.
4. upstream 근거와 측정이 다르다. third_party/laya/README.md:1450-1451("multilingual 의 criteria-less noul 은 state 를 읽는다"), :1440-1445(labels A/B 우회), :1453-1458(중립 key 2-choice 우회)는 한국어 multilingual 에서 재현되지 않았다. V0·V2 binary 는 always-no 와 같은 93/120, V3a 는 A 로 붕괴(68/120)했다. 05:239·04:81 은 P0 결과로 이미 단서를 달았으므로, 고칠 곳은 03:395(C3)·05:275 의 기대치다.

[English](P0b_ablation_summary.md) | **한국어**
