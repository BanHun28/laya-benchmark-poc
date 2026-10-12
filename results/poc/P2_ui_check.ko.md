# P2-UI 점검 (2026-10-03, Laya Playground `/poc/ui/`)

05 §6 P2-UI 검증 (1)\~(10)(docs/05_poc_plan.md:464)을 그대로 따랐다. 브라우저는 Playwright MCP(Chromium), 서버는 `results/poc/P2_20261003.md`의 옵션 1 서버(ft-v1, MPS, `LAYA_API_KEY=devkey`)다. 1280×900에서 점검했고 (10)만 820×1100이다. UI 조작은 실제 클릭·키 입력으로 했고, 예시 10종 일괄 실행만 페이지의 `loadExample()`·`run()`을 순서대로 불렀다(칩·버튼 클릭 핸들러와 같은 함수).

| # | 검증 항목 | 결과 | 근거 |
|---|---|---|---|
| 1 | 단일 5종 + 다중 4종 예시가 모두 응답, router_v1 예시는 라우팅 결과 카드에 ROUTE/FALLBACK | ✔ | 10/10 응답(아래 표, YNAT 토글 포함), 오류 상자 0. router_v1: ROUTE productivity p 0.924 ≥ T 0.907 → calendar-svc (`P2_ui_2.png`) |
| 2 | `domain` argmax가 CLI 결과·"curl 복사" 재실행 결과와 일치 | ✔ (curl·Python, in-process) / ✘ (문서 그대로의 CLI) | C 카드 `media` 칩 → UI `media` 0.9441. "curl 복사" 버튼으로 복사된 문자열(아래)을 `LAYA_API_KEY=devkey`로 셸에서 실행 → `media` 0.9441, "Python 복사" 실행 → `media` 0.9441. 문서의 `laya ... --model ml --lang ko`는 Hub base multilingual을 쓰므로 같은 체크포인트가 아니다(router_v1 예시에서 CLI `smart_home` 0.9949 vs ft-v1 `productivity` 0.9236). 대신 `laya.load(ft-v1)` in-process(CPU)와 비교해 9/9 argmax 일치, max abs Δp 0.0000(`P2_acceptance.json` `inprocess_parity`). UI의 "CLI 복사"는 이 차이를 주석 첫 줄에 적는다 |
| 3 | `min_confidence` 슬라이더로 `abstention` 배지가 passed / abstained 사이에서 바뀜 | ✔ | 고급 펼침 → 체크 → 슬라이더 End(0.95) → `abstained`, 정책 카드 FALLBACK(reason abstained, `P2_ui_3_fallback.png`. 정책 카드는 T 0.907, 답 카드는 0.95 표시선). Home(0.5) → `passed`, ROUTE. 같은 발화 p 0.9236 |
| 4 | shadow 레코드에 PII 원문 없음 | ✔ | 전화·이메일·카드번호 문장의 shadow state는 `김민수 팀장님([email], [phone])한테 카드 [card] 영수증 메일로 보내줘`, 최종 `poc/logs/shadow.jsonl` 76줄에서 원문 조각 grep 0건. 표에도 마스킹된 텍스트만 보인다(`P2_ui_6_shadow.png`) |
| 5 | 브라우저 round-trip과 서버 `elapsed_ms` 차이가 수십 ms 이내 | ✔ | UI 메타 행 기준 차이 1.1\~5.4 ms(예: 서버 47.5 / 왕복 50.3, 28.7 / 30.3, 97.7 / 101.4 ms). 스크립트 30회 기준 p95 0.7 ms |
| 6 | `LAYA_API_KEY` 설정 상태에서 키 없는 호출은 401/403, 키를 넣으면 200 | ✔ | 키를 지우고 실행 → "결정이 생성되지 않았습니다. 입력은 유지됩니다." + `HTTP 401 · POST /poc/decide` / `invalid or missing bearer token` + 키 안내. 키 입력(Enter로 저장) 후 실행 → 200. 헤더 배지도 "API 키 필요" ↔ 메타 값으로 바뀜 |
| 7 | 선택지 21개에서 경고 배지, Ctrl+Enter로 실행 | ✔ | "+ 선택지 추가"로 21개 → 카운터 `21 / 20`, 배지 "⚠ head_max_len 예산 초과 가능(README Honest limits), 03 Track C6 참고 · 서버 한도 100 초과는 413", 문제 목록에도 경고(차단 아님). Ctrl+Enter → 200, 확률 21개, `billing` 0.8738, 입력 토큰 206, truncated false (`P2_ui_4_warn21.png`) |
| 8 | 서버를 내리고 실행하면 오류 문구가 보이고 입력이 지워지지 않음 | ✔ | uvicorn 종료 후 Ctrl+Enter → "결정이 생성되지 않았습니다. 입력은 유지됩니다." + "서버에 연결할 수 없습니다: TypeError: Failed to fetch". textarea·질문 그대로, Run 버튼 다시 활성 (`P2_ui_8_server_down.png`) |
| 9 | `GET /poc/meta`의 `checkpoint_sha`·`questions_sha256`이 run card와 같음 | ✔ | questions_sha256 `a7f2f6b8…` = P4 리포트 = MANIFEST, sha256(rl_agent_config) `3270d480…` = P4 리포트, base 55cf4c4. UI "문서와 상태" 섹션과 헤더 배지에 같은 값 표시(`P2_ui_7_full.png`). 응답 필드명은 문서의 `checkpoint_sha` 대신 `checkpoint.{path, sha256_of_rl_agent_config, base}`다 |
| 10 | 900px 미만 폭에서 1단 렌더 | ✔ | 820px: `.workbench` grid `786px` 1열, OUTPUT이 INPUT 아래, 시나리오 카드 1열, 가로 스크롤 없음(`P2_ui_5_narrow.png`) |
| 단계 5 | 하단 shadow 테이블·카운터가 5초 안에 갱신 | ✔ | 상태 줄 `14시 2분 13초` → 6 s 뒤 `14시 2분 18초`. 최신 행이 직전 실행과 같음. 카운터: total 75, ROUTE/FALLBACK 54/9, fallback 14.3%, abstention 14.1% |

## 예시 실행 결과 (브라우저, 1의 근거)

모든 일반 모드 질문도 `multilingual` 슬롯 = ft-v1이 답했다(`routing.reason` = `non-Latin script (hangul …)`).

| 예시 | 엔드포인트 | 답 (answer_confidence) | 서버 / 왕복 ms |
|---|---|---|---|
| 도메인 라우팅 (POC) | /poc/decide | ROUTE productivity (0.9236) | 47.5 / 50.3 |
| 고객 문의 라우팅 CHOICE | /v1/systemone | billing (0.9753) | 160.3 / 165.7 |
| 환불 요청 확인 NOUL | /v1/systemone | P(true) 0.722 → 참 | 112.5 / 113.6 (Ctrl+Enter 재실행 46.2 / 48.2) |
| 장애 긴급도 SCORE | /v1/systemone | score 2.31 / 3 (0.4494) | 40.5 / 41.7 |
| 에이전트 다음 행동 CHOICE (JSON state) | /v1/systemone | click (0.9586), 기대 type | 28.7 / 30.3 |
| CS triage + gateway 7문항 (보류 A) | /v1/systemone | intent refund 0.9613, is_urgent P(true) 0.0119, frustration 1.59, refund_requested 0.1832, churn_risk 0.1265, needs_llm 0.0003, complexity canned 0.4642 | 97.7 / 101.4 |
| 이메일 분류 | /v1/systemone | category billing 0.6272, urgency 1.72, needs_reply P(true) 0.1128 | 50.4 / 54.5 |
| 프롬프트 가드레일 | /v1/systemone | jailbreak P(true) 0.8417, prompt_injection 0.1404, sensitive_data 0.5989, harm_severity 1.32, topic coding 0.2242 | 45.4 / 49.4 |
| 모델 라우터 | /v1/systemone | difficulty 1.56, domain code 0.3554, needs_tools 0.4127, is_sensitive 0.0 | 43.0 / 47.1 |
| YNAT 7토픽 (C 카드 토글) | /v1/systemone | it_science (0.9172) | 85.3 / 86.4 |

에이전트 다음 행동(기대 type → click)과 A 시나리오 noul(오늘 안에 → is_urgent 0.012)은 오답이다. 기능 점검이라 기준은 응답 여부뿐이지만, A가 보류된 이유(G1 미달, noul 약점)와 같은 방향이다.

## "curl 복사"로 복사된 문자열 (2의 근거, 그대로)

```bash
curl -s 'http://127.0.0.1:8000/poc/decide' \
  -H "Authorization: Bearer $LAYA_API_KEY" -H 'content-type: application/json' \
  -d '{"utterance":"출근길에 들을 만한 잔잔한 재즈 좀 틀어줘","lang":"ko"}'
```

"CLI 복사" 결과:

```bash
# 주의: laya CLI의 --model은 이름만 받아 Hub base 체크포인트(55cf4c4)를 쓴다. 이 서버의 multilingual 슬롯은 ft-v1이라 답이 다를 수 있다.
laya '출근길에 들을 만한 잔잔한 재즈 좀 틀어줘' --lang 'ko' --questions poc/schema/router_v1.json --json
```

## 스크린샷

| 파일 | 내용 |
|---|---|
| `P2_ui_1.png` | 첫 화면(router_v1 예시 로드, OUTPUT 빈 상태 `[ · ]`) |
| `P2_ui_2.png` | router_v1 실행 후: ROUTE 카드, 답 카드(passed), 확률 막대, 메타 행, 도구 버튼 |
| `P2_ui_3_fallback.png` | min_confidence 0.95: abstained, FALLBACK 카드 |
| `P2_ui_4_warn21.png` | 선택지 21개 경고 배지 |
| `P2_ui_5_narrow.png` | 820px 1단 렌더 |
| `P2_ui_6_shadow.png` | Shadow 로그 카운터·도메인 분포·테이블 |
| `P2_ui_7_full.png` | 전체 페이지(시나리오 3카드, 문서와 상태 포함) |
| `P2_ui_8_server_down.png` | 서버 종료 후 오류 상태와 유지된 입력 |

## 사람이 브라우저에서 확인할 항목 (자동 점검으로 판단하지 않은 것)

- 시각 톤이 jevplayground와 충분히 닮았는지(밝은 배경, 흰 패널, 모노스페이스 대문자 소제목, 파란 포인트 1색), 한국어 문구가 자연스러운지.
- 클립보드: 페이지의 `navigator.clipboard.writeText`가 성공("✓ curl 복사됨")했고 같은 문자열을 셸에서 실행해 확인했다. 사람이 실제 터미널에 붙여 넣는 동작은 하지 않았다.
- 실기기·다른 브라우저: Chromium(Playwright)만 확인했다. 폰 폭(390px 안팎)과 Safari·Firefox는 보지 않았다.
- 503 + `Retry-After` 표시 경로(과부하가 필요)와 선택지 101개 이상의 413 경로는 UI에서 재현하지 않았다. `/poc/decide`의 413(발화 50,001자)은 오프라인 점검에서만 확인했다.
- 문서 00\~07은 서버가 `docs/`를 서빙하지 않아 경로 복사로만 제공된다. 이 방식이 검토 용도에 충분한지.
- 정적 파일 캐시: UI를 고친 직후에는 Chrome이 이전 `index.html`을 보여 줄 수 있다(Starlette `StaticFiles`에 `Cache-Control` 없음). 강력 새로고침으로 확인할 것.

[English](P2_ui_check.md) | **한국어**
