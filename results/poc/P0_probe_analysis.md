# P0 zero-shot probe analysis (n=30, self-labelled, no CI, indicative only)

dataset_sha256=c734fef59cb64f6cabf5d581a1b9d5743e5ed05bd7f31af152f06dd05546406d questions_sha256=6b8bdadc8f9c718ed40f2510134caf52079a5dc0260e142d93d2132bee722c8a revisions={'multilingual': '55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851'} / english revisions={'english': '55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851'}

## Per-question (multilingual vs english control)

baseline: majority-class accuracy for choice, always-no accuracy for noul, always-level-0 MAE for score.

| qid | metric | multilingual | english | baseline / expected rate | ml mean answer_confidence | en mean answer_confidence |
|---|---|---|---|---|---|---|
| intent | choice_accuracy | 0.400 | 0.233 | majority 0.167 | 0.825 | 0.338 |
| is_urgent | noul_accuracy | 0.833 | 0.867 | always-no 0.833 | 0.957 | 0.851 |
| is_urgent | positive rate (p>=0.5) | 0.000 | 0.100 | expected 0.167 | | |
| frustration | score_mae | 1.084 | 0.880 | always-0 0.700 | 0.461 | 0.561 |
| frustration | exact level (argmax) | 0.167 | 0.533 | - | | |
| frustration | exact level (round(score)) | 0.167 | 0.300 | - | | |
| frustration | level-0 pick rate (argmax) | 0.000 | 0.867 | 0.600 | | |
| frustration | level-0 pick rate (round(score)) | 0.000 | 0.133 | 0.600 | | |
| refund_requested | noul_accuracy | 0.833 | 0.733 | always-no 0.800 | 0.905 | 0.930 |
| refund_requested | positive rate (p>=0.5) | 0.167 | 0.067 | expected 0.200 | | |
| churn_risk | noul_accuracy | 0.800 | 0.733 | always-no 0.800 | 0.947 | 0.845 |
| churn_risk | positive rate (p>=0.5) | 0.067 | 0.200 | expected 0.200 | | |
| needs_llm | noul_accuracy | 0.633 | 0.500 | always-no 0.667 | 0.887 | 0.867 |
| needs_llm | positive rate (p>=0.5) | 0.100 | 0.567 | expected 0.333 | | |
| complexity | choice_accuracy | 0.433 | 0.433 | majority 0.400 | 0.681 | 0.407 |

## Intent confusion, multilingual (rows = expected, cols = predicted)

| expected \ predicted | refund | technical_help | billing_question | information | cancellation | other |
|---|---|---|---|---|---|---|
| refund | 1 | 0 | 3 | 0 | 1 | 0 |
| technical_help | 1 | 2 | 1 | 0 | 1 | 0 |
| billing_question | 1 | 1 | 3 | 0 | 0 | 0 |
| information | 0 | 3 | 0 | 2 | 0 | 0 |
| cancellation | 1 | 0 | 0 | 0 | 4 | 0 |
| other | 1 | 1 | 1 | 1 | 1 | 0 |

## Intent confusion, english control

| expected \ predicted | refund | technical_help | billing_question | information | cancellation | other |
|---|---|---|---|---|---|---|
| refund | 4 | 0 | 0 | 0 | 0 | 1 |
| technical_help | 2 | 1 | 0 | 0 | 1 | 1 |
| billing_question | 3 | 0 | 0 | 0 | 2 | 0 |
| information | 2 | 0 | 0 | 0 | 1 | 2 |
| cancellation | 2 | 0 | 0 | 0 | 1 | 2 |
| other | 1 | 0 | 0 | 0 | 3 | 1 |

## Policy action distribution (05 §5 decide(), T initial, gate min_confidence=0.70), multilingual

| action | multilingual | if answers were the expected labels (reference) |
|---|---|---|
| HUMAN_REVIEW | 12 | 0 |
| FORWARD_LLM | 3 | 10 |
| ESCALATE | 0 | 3 |
| AUTO_ROUTE | 15 | 17 |

intent answer_confidence >= gate 0.70: 23/30; >= T_intent 0.80: 18/30
rows past the intent gate: 18; of those with wrong intent: 8 -> [(0, 'refund', 'billing_question', 0.9557, 'AUTO_ROUTE'), (3, 'refund', 'cancellation', 0.9502, 'AUTO_ROUTE'), (6, 'technical_help', 'refund', 0.8901, 'FORWARD_LLM'), (11, 'billing_question', 'refund', 0.9979, 'AUTO_ROUTE'), (16, 'information', 'technical_help', 0.9843, 'AUTO_ROUTE'), (18, 'information', 'technical_help', 0.9413, 'AUTO_ROUTE'), (27, 'other', 'technical_help', 0.8424, 'AUTO_ROUTE'), (29, 'other', 'cancellation', 0.9805, 'AUTO_ROUTE')]
AUTO_ROUTE/ESCALATE queues/tags: Counter({('AUTO_ROUTE', 'tech', ()): 5, ('AUTO_ROUTE', 'retention', ()): 4, ('AUTO_ROUTE', 'billing', ()): 3, ('AUTO_ROUTE', 'billing', ('refund',)): 1, ('AUTO_ROUTE', 'retention', ('refund',)): 1, ('AUTO_ROUTE', 'faq', ()): 1})

## Per-row answers, multilingual (exp -> pred; noul as p_true; frustration as score/argmax level)

| # | message | intent | urgent | frustr | refund | churn | needs_llm | complexity | action |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 같은 달 요금이 두 번 빠져나간 것 같아 걱정돼서 연락드려요. 확인해… | refund→billing_question (0.96) | F→0.00 | 1→1.59/1 | T→0.89 | F→0.01 | F→0.03 | structured→canned (0.51) | AUTO_ROUTE billing refund |
| 1 | 어제 실수로 연간 플랜을 결제했어요ㅠㅠ 아직 한 번도 안 썼는데 결제… | refund→refund (0.97) | F→0.00 | 1→1.48/1 | T→0.09 | F→0.01 | F→0.08 | structured→canned (0.57) | AUTO_ROUTE billing - |
| 2 | 장난하세요? 분명히 해지했는데 이번 달 요금이 또 결제됐잖아요. 오늘… | refund→billing_question (0.53) | T→0.03 | 3→1.79/1 | T→0.07 | T→0.06 | T→0.02 | structured→canned (0.68) | HUMAN_REVIEW |
| 3 | 안녕하세요. 지난주 화요일부터 사흘간 이어진 서비스 장애로 업무에 지… | refund→cancellation (0.95) | F→0.00 | 1→1.57/1 | T→0.89 | F→0.00 | T→0.10 | complex→canned (0.79) | AUTO_ROUTE retention refund |
| 4 | 서비스는 앞으로도 계속 쓸 거예요. 다만 지난달에 잘못 청구된 추가 … | refund→billing_question (0.72) | F→0.05 | 0→1.77/2 | T→0.81 | F→0.13 | F→0.20 | structured→structured (0.85) | HUMAN_REVIEW |
| 5 | 비밀번호 재설정 메일이 안 오는데 어떻게 해야 하나요? | technical_help→billing_question (0.59) | F→0.01 | 0→1.32/1 | F→0.00 | F→0.00 | F→0.06 | canned→canned (0.55) | HUMAN_REVIEW |
| 6 | 결제 API가 30분째 500 에러만 반환하고 있습니다. 지금 저희 … | technical_help→refund (0.89) | T→0.20 | 2→1.66/1 | F→0.46 | F→0.86 | T→0.96 | complex→structured (1.00) | FORWARD_LLM |
| 7 | 해지할 생각은 없는데요, 요즘 앱이 하루에도 몇 번씩 저절로 로그아웃… | technical_help→cancellation (0.48) | F→0.02 | 1→1.56/1 | F→0.01 | F→0.03 | T→0.04 | complex→canned (0.48) | HUMAN_REVIEW |
| 8 | 안녕하세요. 슬랙 연동을 설정했는데 알림이 채널로 전송되지 않습니다.… | technical_help→technical_help (0.90) | F→0.00 | 0→1.61/1 | F→0.00 | F→0.00 | T→0.19 | complex→canned (0.60) | AUTO_ROUTE tech - |
| 9 | 업데이트하고 나서 또 동기화가 안 되네요. 벌써 세 번째예요. 계속 … | technical_help→technical_help (0.94) | F→0.00 | 2→1.60/1 | F→0.03 | T→0.03 | T→0.15 | complex→canned (0.76) | AUTO_ROUTE tech - |
| 10 | 해지하고 싶지는 않고 요금제만 바꾸고 싶어요. 월 결제에서 연 결제로… | billing_question→billing_question (0.56) | F→0.00 | 0→1.15/1 | F→0.51 | F→0.01 | F→0.24 | canned→canned (0.49) | HUMAN_REVIEW |
| 11 | 환불은 필요 없고요, 다음 결제부터는 다른 카드로 나가게 바꾸고 싶어… | billing_question→refund (1.00) | F→0.00 | 0→1.47/1 | F→0.65 | F→0.00 | F→0.23 | canned→structured (0.47) | AUTO_ROUTE billing - |
| 12 | 이번 달 청구 금액이 평소보다 2만 원 넘게 더 나왔는데 이유를 설명… | billing_question→billing_question (1.00) | F→0.00 | 1→1.99/3 | F→0.06 | F→0.00 | T→0.01 | structured→canned (0.71) | AUTO_ROUTE billing - |
| 13 | 세금계산서 발행 요청드립니다. 사업자등록증은 첨부 파일로 보내드렸고,… | billing_question→billing_question (0.98) | T→0.46 | 0→1.15/1 | F→0.28 | F→0.00 | F→0.72 | structured→structured (0.55) | FORWARD_LLM |
| 14 | 결제 수단을 등록하려는데 카드가 계속 거절된다고 나와요. 다른 데서는… | billing_question→technical_help (0.66) | F→0.00 | 2→2.21/3 | F→0.00 | F→0.02 | F→0.04 | canned→canned (0.88) | HUMAN_REVIEW |
| 15 | 프로 플랜이랑 팀 플랜 차이가 뭔가요? 가격도 같이 알려주세요. | information→information (1.00) | F→0.01 | 0→1.63/1 | F→0.00 | F→0.01 | F→0.01 | canned→canned (0.60) | AUTO_ROUTE faq - |
| 16 | 모바일 앱에서도 PDF로 내보내기가 되나요? | information→technical_help (0.98) | F→0.00 | 0→1.81/1 | F→0.00 | F→0.00 | F→0.02 | canned→structured (0.95) | AUTO_ROUTE tech - |
| 17 | 안녕하세요. 저희 회사에서 도입을 검토 중인데, 데이터가 국내 리전에… | information→technical_help (0.77) | F→0.00 | 0→1.64/1 | F→0.00 | F→0.00 | T→0.00 | complex→canned (0.88) | HUMAN_REVIEW |
| 18 | 내일 오전에 고객사 데모가 있는데, 화면 공유하면서 실시간 공동 편집… | information→technical_help (0.94) | T→0.00 | 0→1.58/1 | F→0.00 | F→0.00 | F→0.25 | canned→structured (0.47) | AUTO_ROUTE tech - |
| 19 | 고객센터 운영 시간이 어떻게 되나요? 주말에도 상담 가능한가요? | information→information (0.57) | F→0.01 | 0→1.34/1 | F→0.00 | F→0.00 | F→0.04 | canned→canned (0.86) | HUMAN_REVIEW |
| 20 | 다음 달부터는 안 쓸 것 같아서요. 구독 해지는 어디서 하나요? | cancellation→cancellation (1.00) | F→0.21 | 0→1.75/1 | F→0.00 | T→0.02 | F→0.04 | structured→canned (0.54) | AUTO_ROUTE retention - |
| 21 | 솔직히 가격 대비 너무 별로네요. 경쟁사는 반값인데 굳이 여기를 쓸 … | cancellation→cancellation (0.92) | F→0.00 | 2→1.94/3 | F→0.09 | T→0.32 | T→0.04 | complex→canned (0.79) | AUTO_ROUTE retention - |
| 22 | 프로 플랜에서 무료 플랜으로 다운그레이드하고 싶습니다. 기존에 만든 … | cancellation→refund (0.74) | F→0.00 | 0→1.48/1 | F→0.00 | F→0.00 | F→0.40 | structured→structured (0.84) | HUMAN_REVIEW |
| 23 | 탈퇴하려는데 탈퇴 버튼이 어디에도 없네요. 오늘이 결제일이라 오늘 안… | cancellation→cancellation (1.00) | T→0.06 | 2→1.31/1 | F→0.01 | T→0.42 | F→0.62 | structured→canned (0.59) | FORWARD_LLM |
| 24 | 안녕하세요. 회사 사정으로 이번 달 말일자로 계약을 종료하려고 합니다… | cancellation→cancellation (1.00) | F→0.18 | 0→1.27/1 | T→0.46 | T→0.67 | F→0.05 | structured→structured (0.49) | AUTO_ROUTE retention - |
| 25 | 상담원분이 끝까지 친절하게 도와주셔서 문제 잘 해결됐어요. 감사합니다! | other→refund (0.79) | F→0.00 | 0→1.40/1 | F→0.00 | F→0.00 | F→0.00 | canned→canned (0.94) | HUMAN_REVIEW |
| 26 | 채용 공고 보고 연락드렸는데, 지원서는 어디로 보내면 되나요? | other→billing_question (0.34) | F→0.04 | 0→1.01/1 | F→0.00 | F→0.00 | F→0.10 | canned→canned (0.65) | HUMAN_REVIEW |
| 27 | 어제 통화한 상담원 태도 진짜 최악이었어요. 사람 말 끊고 비웃기까지… | other→technical_help (0.84) | F→0.00 | 3→2.37/3 | F→0.03 | F→0.01 | T→0.01 | complex→canned (0.59) | AUTO_ROUTE tech - |
| 28 | 제휴 마케팅 관련해서 제안드리고 싶은데 담당 부서 연락처를 알 수 있… | other→information (0.78) | F→0.01 | 0→1.08/1 | F→0.00 | F→0.00 | F→0.18 | canned→canned (0.85) | HUMAN_REVIEW |
| 29 | 해지 문의는 아니고요, 지난번에 요청드린 기능이 이번 업데이트에 들어… | other→cancellation (0.98) | F→0.00 | 0→1.35/1 | F→0.00 | F→0.00 | F→0.13 | canned→canned (0.48) | AUTO_ROUTE retention - |
