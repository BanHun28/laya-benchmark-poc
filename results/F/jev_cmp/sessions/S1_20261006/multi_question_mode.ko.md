# S1 탐색: jevplayground.com "Multiple questions" 모드 (2026-10-06)

**판정.** Multiple questions 모드는 타입 혼합(choice·boolean·score), 질문 2\~5개, 공유 State를 지원하고 질문별 DECISION과 확률을 돌려준다. 하지만 **Score는 정확히 5개 레벨(0\~4)만 받는다.** T1의 score decision 80개 중 70개가 4레벨이고 urgency(4레벨)가 모든 workflow에 있어서, **40 case 중 어느 것도 5문항 전체를 그대로 넣을 수 없다.** 지시된 규칙("cannot carry a T1 case faithfully → FALL BACK to Step 2b")에 따라 S1 본 실행은 T2 AG News로 바꿨다. 탐색에 쓴 평가는 1회다(row 30, 표현 가능한 4문항).

출처: 화면 관찰, 클라이언트 번들 `https://jevplayground.com/_next/static/immutable/chunks/2zf_0ui8glm88.js`(module 94827: schema·payload·resultView, module 84725: Playground UI. 발췌 `raw/explore_js_schema.json`, `raw/explore_js_payload.json`), 실행 기록 `raw/r01_T1_row30_multi.json`, `S1_requests.jsonl` run 1(발췌와 실행 기록은 공개 저장소에는 포함하지 않음).

## 1. 확인한 사실

| 항목 | 결과 | 근거 |
|---|---|---|
| 모드 전환 | group "Playground mode"의 버튼 "Multiple questions"(aria-pressed). 전환하면 예시 "Agent Action Gate (3 questions)"가 로드된다 | 화면 |
| State | `textarea#state` 하나, maxlength 8000. 문구 "Shared by every question below.", "All questions evaluate the same State in one Jev request." | 화면, DOM |
| 질문 수 | 2\~5. "+ Add question"은 5개에서 disabled("5 of 5 questions"), 질문이 2개면 제거 불가(`canRemove: questions.length > 2`). schema: "Add at least 2 questions." / "Use at most 5 questions." | 화면, 번들 |
| 질문별 타입 | 질문마다 group "Decision type for question k" → Choice / Boolean / Score. 한 요청에 섞을 수 있다(run 1: boolean, choice, score, boolean) | 화면, run 1 |
| Choice | 질문마다 별도 옵션 2\~10개(`#mq-{k}-c-{i}`, "+ Add choice", "N of 10"). 라벨은 trim 후 1\~80자, 대소문자 무시 중복 금지("Use a unique label.") | 번들 |
| Boolean | 입력은 질문 문장뿐. 라벨·설명 칸이 없다. "Jev returns P(true). The probability of “No” is its complement." | 화면, 번들 `d()` |
| Score | 루브릭 입력 `#mq-{k}-r-{0..4}`("Rubric level i", maxlength 80)가 **5칸 고정**이고 추가·삭제 버튼이 없다. 기본값 "No urgency / Low / Moderate / High / Critical". schema: "Use exactly five ordered levels (0–4)." 빈 칸은 "Enter a label." | 화면, 번들 |
| 80자 제한 | choice와 rubric 모두 `maxLength:80`. 89자 옵션(`request_information: …`)을 fill하면 **오류 없이 80자로 잘린다**("…before anything can"). 잘린 라벨로 요청이 나갈 수 있어 사전 제외가 필요하다 | DOM probe |
| 클라이언트 검증 | 제출 시 zod 검증. 실패하면 요청을 보내지 않고 status "Check the highlighted fields and try again." + 필드 오류를 표시한다. 4레벨 urgency(레벨 4 빈칸)로 Run을 눌렀더니 `questions.4.rubric.4-error` "Enter a label.", `/api/evaluate` 요청 0건(fetch wrapper 0, resource timing 0) | `shots/explore02_*.png`(스크린샷은 공개 저장소에는 포함하지 않음) |
| Single 모드 | 같은 label·rubric 규칙(`validateDraft`도 같은 `o()` 검사)이라 **4레벨 score는 Single 모드에서도 불가**다 | 번들 |
| 요청 형식 | `POST /api/evaluate`, body `{"state": …, "questions": {"q1": {"instructions": …, "type": "boolean"}, "q2": {"instructions": …, "type": "choice", "criteria": {"<label>": "<label>", …}}, "q3": {"instructions": …, "type": "score", "criteria": ["<level 0>", …, "<level 4>"]}}}`. Single 모드는 `{"questions": {"decision": {…}}}`. 라벨·질문은 trim, state는 그대로. timeout 40 s | 번들 `toMultiPayload`/`toPayload`, run 1 request body |
| 응답 형식 | `{"ok": true, "model": "typesafe-ai/jev", "latencyMs": —, "result": {"answers": {"q1": {"type": "boolean", "probability": —}, "q2": {"type": "choice", "choice": "<label>", "probabilities": {…}}, "q3": {"type": "score", "score": —, "probabilities": {"0": —, "1": —, …}}}, "usage": {…}, "rounding": {"probabilityDecimals": 2, "scoreDecimals": 2}, "confidence": {"q2": —, "q3": —}, "warnings": []}}` (Jev의 항목별 출력은 공개 저장소에서 생략) | run 1 response body |
| 결과 표시 | status "Evaluation complete. 4 answers returned." → "MULTIPLE DECISIONS / 4 answers in one call / Jev evaluated these questions together against the same State." → 질문마다 카드 "Question k / BOOLEAN·CHOICE·SCORE / 질문 문장 / DECISION(score는 SCORE) / 값 / 설명 / Probability distribution / 라벨·%" | `shots/explore04_*.png` |
| Boolean 표시 | DECISION "Yes"/"No"(p = 0.5면 "Equally likely"), 막대 Yes = P(true), No = 1 − P(true) | 번들 `resultView` |
| Score 표시 | SCORE = `rubric[round(score)]`, "— / 4", "Nearest rubric level. Jev returned an interpolated score."(정수면 "Level on your submitted rubric."), 막대 "s — <레벨 문구>" | run 1 |
| Score 의미 | `score` = Σ s·p_s, 2자리 반올림. 표시 레벨은 기대값의 최근접 레벨이라 **argmax 레벨과 다를 수 있다** | run 1 |
| % 표기 | `${Number((100·p).toFixed(2))}%`. API가 확률을 소수 둘째 자리로 반올림(`probabilityDecimals: 2`)하므로 정수 %로 보인다 | 번들, 41/41 |
| 지연 표기 | "N ms · server + network" = round(`latencyMs`) (41/41 일치). 브라우저 POST보다 짧다 | `S1_requests.jsonl` |
| View details | `<details>`: Model ID `typesafe-ai/jev`, Input tokens, Output tokens, "Normalized result. Confidence, when returned, is a separate provider statistic." + result JSON 전체 | run 1 |
| confidence | choice·score 질문에만 온다(`q2`, `q3`). boolean에는 없다 | run 1 |
| 토큰 | run 1(4문항): 입력 —, 출력 —. T2 single(4옵션): 입력 중앙 425, 출력 중앙 68 | `S1_requests.jsonl` |

## 2. 조작 레시피 (Playwright MCP, 이번 세션에서 쓴 그대로)

1. `browser_navigate https://jevplayground.com/` → `browser_evaluate`로 passive listener 설치: capture 단계 click listener(버튼 텍스트 "Run Jev"), `[role="status"]` MutationObserver, `/api/evaluate`만 감싸는 fetch wrapper(요청 body·응답 text·시각 기록, 요청 자체는 그대로 전달). 함수 `window.__jev.form/payload/precheck/ready/dump`.
2. 모드: `[role="group"][aria-label="Playground mode"] button` (첫째 Single, 둘째 Multiple).
3. 질문 수 맞추기: "+ Add question" / `button[aria-label="Remove question k"]`. 타입: `getByRole('group', {name: 'Decision type for question k'}).getByRole('button', {name: 'Score'})`.
4. Choice 옵션 수: 질문 카드 안 "+ Add choice"(Boolean에서 Choice로 바꾸면 옵션 0개로 시작, 새 질문은 빈 칸 2개).
5. 값 입력: `browser_fill_form`에 id selector. `#state`, `#mq-{k}-question`, `#mq-{k}-c-{i}`, `#mq-{k}-r-{0..4}`. Single 모드는 `#state`, `#question`, `#choice-{i}`, `#rubric-{0..4}`, 타입 group은 `[role="group"][aria-labelledby="mode-label"]`.
6. precheck: `window.__jev.ready('<sha12>')`가 마지막 클릭 뒤 12 s를 기다린 뒤 폼 값으로 클라이언트와 같은 payload를 만들어 SHA-256 앞 12자리를 대조한다. 기대값은 `.venv/bin/python results/F/jev_cmp/jev_cmp.py expect <SET> [--rows R --qids a,b]`.
7. `button.run-button` 클릭 → `browser_evaluate window.__jev.dump()`를 `filename=results/F/jev_cmp/sessions/S1_20261006/raw/rNN_*.json`으로 저장(완료 status까지 대기 포함).
8. `jev_cmp.py record S1 <SET> <run> <dump> --row R [--qids …]`: 캡처한 request body가 폼 파일에서 만든 payload와 **바이트 단위로 같은지** 확인하고, 화면 값이 응답과 같은지 대조한 뒤 세션 JSONL과 master JSONL에 한 줄씩 추가한다(오류면 exit 2).

## 3. T1을 이 모드에 넣을 때의 손실

| 원인 | 영향 decision | 비고 |
|---|---|---|
| Score 루브릭 5레벨 고정 | 70 / 80 score (risk 10, churn_risk 10, discrepancy_severity 10, urgency 40) | 40 case 전부에 1개 이상. 5번째 레벨을 덧대면 척도(0\~3 → 0\~4)와 기대값이 바뀌어 같은 입력이 아니다 |
| choice 라벨 80자 | 10 / 60 choice (customer_service/action, `jev_excluded`) | maxlength가 조용히 잘라 다른 라벨이 전송된다 |
| Boolean 라벨 없음 | 60 / 60 boolean의 false/true 설명문 | 질문 문장은 같다. Laya는 `false: …`/`true: …` 설명을 읽고 Jev는 못 읽는다(정보 비대칭, 부분 손실) |

그대로 보낼 수 있는 decision은 **120 / 200**(choice 50, boolean 60, 5레벨 score 10)이다. case당 질문 수는 agent_trace 3(action, needs_review, outcome), customer_service 2(category, needs_human), invoice 3(disposition, duplicate, matches_order), security 4(credential_compromise, disposition, severity, true_positive)이고 모두 Multiple questions의 최소 2개를 만족한다.

T1 진행 선택지(결정 필요):

| 안 | 내용 | Jev 요청 | 대가 |
|---|---|---|---|
| A | Multiple questions, case당 1회, 표현 가능한 문항만(2\~4개) | 40. row 30은 run 1과 payload가 같으므로 39 | score가 10개뿐이라 score MAE가 사실상 빠진다. 문항 구성이 upstream typed-decisions(Jev 0.727)와 달라 대표성 대조가 약해진다 |
| B | 4레벨 질문에 5번째 레벨을 덧대 전부 실행 | 40 | 입력이 Laya와 달라진다(척도 변경). 별도 변형으로만 보고 가능 |
| C | Single 모드, 표현 가능한 decision마다 1회 | 120 | A와 같은 120 decisions인데 요청이 3배다. 질문을 따로 평가하는 Laya와 조건은 더 비슷하다(Jev multi는 "together" 평가) |

계획서 7.1의 "Single로 질문별 실행 시 약 200 요청"은 4레벨 score가 Single에서도 막히므로 **최대 120 요청**으로 바뀐다.

## 4. 탐색 실행 1회: T1 row 30 (security_incidents_000017), 4문항

payload sha12 `5a9e5492744b`(2,077 B, 폼 파일과 바이트 일치). urgency(4레벨)는 생략했다(`omitted` 기록).

| 질문 | gold | Jev | Laya english | Laya multilingual | teacher soft |
|---|---|---|---|---|---|
| credential_compromise (boolean) | true | — | true (0.79) | true (0.99) | [0.37, 0.63] |
| disposition (choice) | investigate | — | X close_benign (0.35) | X monitor (0.92) | investigate 0.67 |
| severity (score, 5레벨) | 2 (teacher score 1.62) | — | E[level] 1.62 | E[level] 1.02 | [0.07, 0.37, 0.45, 0.11, 0.01] |
| true_positive (boolean) | true | — | true (0.65) | true (0.99) | [0.22, 0.78] |

argmax 레벨과 최근접 레벨의 정오가 갈릴 수 있으므로, score 질문의 비교 규칙(argmax 레벨 정확도 + E[level] MAE)을 T6·T1에 미리 고정해야 한다. 1 case라 정확도 수치로 쓰지 않는다. Model ID `typesafe-ai/jev`.

## 5. 다른 과제에 대한 함의

- T6 SST-5는 5레벨이라 Score 루브릭에 그대로 맞는다(옵션 최대 22자). T6 비교 규칙: argmax 레벨 정확도, MAE는 Jev `score`(= E[level])와 Laya E[level] 대 gold 레벨.
- T3·T4·T7(choice, 최대 50자), T5·T8(boolean, Laya도 criteria 없음)은 Single 모드 제약에 걸리지 않는다(폼 파일 전수 점검: 80자 초과 0, 10옵션 초과 0).
- Multiple questions는 4문항 요청도 single 1문항(중앙 234 ms·68 토큰)과 지연이 비슷하다. 한 요청으로 여러 decision을 받는 비용 이점은 있지만 T1 외 과제는 문항이 하나라 해당 없다.

## 6. 스크린샷 (공개 저장소에는 포함하지 않음)

- `shots/explore01_form_row30_all5q_urgency_4levels.png`: row 30의 5문항을 모두 넣은 폼(urgency 레벨 4 빈칸).
- `shots/explore02_validation_blocked_4level_rubric_no_request.png`: Run 클릭 후 클라이언트 검증 차단 화면(요청 없음).
- `shots/explore03_form_row30_4q_representable.png`: urgency 제거 후 4문항 폼(precheck 일치).
- `shots/explore04_result_row30_4q_details_open.png`: 4문항 결과와 View details.

[English](multi_question_mode.md) | **한국어**
