# P2-UI check (2026-10-03, Laya Playground `/poc/ui/`)

The 05 §6 P2-UI checks (1)\~(10) (docs/05_poc_plan.md:464) were followed as written. The browser was Playwright MCP (Chromium), and the server was the option 1 server of `results/poc/P2_20261003.md` (ft-v1, MPS, `LAYA_API_KEY=devkey`). Checks were done at 1280×900, only (10) at 820×1100. UI operations were real clicks and key presses; only the batch run of the 10 examples called the page's `loadExample()` and `run()` in sequence (the same functions as the chip and button click handlers).

| # | Check item | Result | Evidence |
|---|---|---|---|
| 1 | All 5 single + 4 multi examples respond; the router_v1 example shows ROUTE/FALLBACK in the routing result card | ✔ | 10/10 responded (table below, including the YNAT toggle), 0 error boxes. router_v1: ROUTE productivity p 0.924 ≥ T 0.907 → calendar-svc (`P2_ui_2.png`) |
| 2 | `domain` argmax matches the CLI result and the result of re-running the "curl 복사" (copy curl) string | ✔ (curl·Python, in-process) / ✘ (CLI exactly as in the doc) | C card `media` chip → UI `media` 0.9441. The string copied by the "curl 복사" button (below), run in a shell with `LAYA_API_KEY=devkey` → `media` 0.9441; running the "Python 복사" (copy Python) output → `media` 0.9441. The doc's `laya ... --model ml --lang ko` uses the Hub base multilingual, so it is not the same checkpoint (for the router_v1 example, CLI `smart_home` 0.9949 vs ft-v1 `productivity` 0.9236). Instead, a comparison with `laya.load(ft-v1)` in-process (CPU) gives 9/9 argmax agreement, max abs Δp 0.0000 (`P2_acceptance.json` `inprocess_parity`). The UI's "CLI 복사" (copy CLI) states this difference in the first comment line |
| 3 | The `min_confidence` slider switches the `abstention` badge between passed / abstained | ✔ | Expand advanced → check → slider End (0.95) → `abstained`, policy card FALLBACK (reason abstained, `P2_ui_3_fallback.png`; the policy card shows T 0.907, the answer card a 0.95 marker line). Home (0.5) → `passed`, ROUTE. Same utterance, p 0.9236 |
| 4 | No raw PII in the shadow records | ✔ | The shadow state of the sentence with a phone number, email and card number is `김민수 팀장님([email], [phone])한테 카드 [card] 영수증 메일로 보내줘`; a grep for fragments of the original finds 0 in the final 76 lines of `poc/logs/shadow.jsonl`. The table also shows only masked text (`P2_ui_6_shadow.png`) |
| 5 | The difference between the browser round trip and the server `elapsed_ms` is within a few tens of ms | ✔ | Per the UI meta row, the difference is 1.1\~5.4 ms (e.g. server 47.5 / round trip 50.3, 28.7 / 30.3, 97.7 / 101.4 ms). Per the 30 script calls, p95 0.7 ms |
| 6 | With `LAYA_API_KEY` set, calls without a key get 401/403 and calls with the key get 200 | ✔ | Run with the key cleared → "결정이 생성되지 않았습니다. 입력은 유지됩니다." (no decision was produced; the input is kept) + `HTTP 401 · POST /poc/decide` / `invalid or missing bearer token` + key guidance. Run after entering the key (saved with Enter) → 200. The header badge also switches between "API 키 필요" (API key required) ↔ the meta values |
| 7 | Warning badge at 21 options, run with Ctrl+Enter | ✔ | 21 options via "+ 선택지 추가" (add option) → counter `21 / 20`, badge "⚠ head_max_len 예산 초과 가능(README Honest limits), 03 Track C6 참고 · 서버 한도 100 초과는 413", and a warning in the problem list too (not blocking). Ctrl+Enter → 200, 21 probabilities, `billing` 0.8738, input tokens 206, truncated false (`P2_ui_4_warn21.png`) |
| 8 | Running with the server down shows an error message and does not clear the input | ✔ | Ctrl+Enter after uvicorn was stopped → "결정이 생성되지 않았습니다. 입력은 유지됩니다." + "서버에 연결할 수 없습니다: TypeError: Failed to fetch" (cannot connect to the server). textarea and questions unchanged, Run button active again (`P2_ui_8_server_down.png`) |
| 9 | `checkpoint_sha` and `questions_sha256` of `GET /poc/meta` equal the run card | ✔ | questions_sha256 `a7f2f6b8…` = P4 report = MANIFEST, sha256(rl_agent_config) `3270d480…` = P4 report, base 55cf4c4. The same values are shown in the UI's "문서와 상태" (docs and status) section and in the header badge (`P2_ui_7_full.png`). The response field name is `checkpoint.{path, sha256_of_rl_agent_config, base}` instead of the doc's `checkpoint_sha` |
| 10 | 1-column render at widths under 900px | ✔ | 820px: `.workbench` grid `786px` 1 column, OUTPUT below INPUT, scenario cards in 1 column, no horizontal scroll (`P2_ui_5_narrow.png`) |
| Step 5 | The bottom shadow table and counters refresh within 5 seconds | ✔ | Status line `14시 2분 13초` → 6 s later `14시 2분 18초`. The latest row matches the previous run. Counters: total 75, ROUTE/FALLBACK 54/9, fallback 14.3%, abstention 14.1% |

## Example run results (browser, evidence for 1)

All general-mode questions were also answered by the `multilingual` slot = ft-v1 (`routing.reason` = `non-Latin script (hangul …)`).

| Example | Endpoint | Answer (answer_confidence) | Server / round trip ms |
|---|---|---|---|
| 도메인 라우팅 (domain routing; POC) | /poc/decide | ROUTE productivity (0.9236) | 47.5 / 50.3 |
| 고객 문의 라우팅 (customer inquiry routing) CHOICE | /v1/systemone | billing (0.9753) | 160.3 / 165.7 |
| 환불 요청 확인 (refund request check) NOUL | /v1/systemone | P(true) 0.722 → 참 (true) | 112.5 / 113.6 (Ctrl+Enter re-run 46.2 / 48.2) |
| 장애 긴급도 (outage urgency) SCORE | /v1/systemone | score 2.31 / 3 (0.4494) | 40.5 / 41.7 |
| 에이전트 다음 행동 (agent next action) CHOICE (JSON state) | /v1/systemone | click (0.9586), expected type | 28.7 / 30.3 |
| CS triage + gateway 7문항 (scenario A, on hold) | /v1/systemone | intent refund 0.9613, is_urgent P(true) 0.0119, frustration 1.59, refund_requested 0.1832, churn_risk 0.1265, needs_llm 0.0003, complexity canned 0.4642 | 97.7 / 101.4 |
| 이메일 분류 (email classification) | /v1/systemone | category billing 0.6272, urgency 1.72, needs_reply P(true) 0.1128 | 50.4 / 54.5 |
| 프롬프트 가드레일 (prompt guardrail) | /v1/systemone | jailbreak P(true) 0.8417, prompt_injection 0.1404, sensitive_data 0.5989, harm_severity 1.32, topic coding 0.2242 | 45.4 / 49.4 |
| 모델 라우터 (model router) | /v1/systemone | difficulty 1.56, domain code 0.3554, needs_tools 0.4127, is_sensitive 0.0 | 43.0 / 47.1 |
| YNAT 7토픽 (C-card toggle) | /v1/systemone | it_science (0.9172) | 85.3 / 86.4 |

The 에이전트 다음 행동 example (expected type → click) and the scenario A noul ("오늘 안에" (by today) → is_urgent 0.012) are wrong answers. This is a functional check, so the only criterion is whether there is a response, but they point the same way as the reasons A was put on hold (G1 not met, noul weakness).

## String copied with "curl 복사" (evidence for 2, verbatim)

```bash
curl -s 'http://127.0.0.1:8000/poc/decide' \
  -H "Authorization: Bearer $LAYA_API_KEY" -H 'content-type: application/json' \
  -d '{"utterance":"출근길에 들을 만한 잔잔한 재즈 좀 틀어줘","lang":"ko"}'
```

"CLI 복사" output:

```bash
# 주의: laya CLI의 --model은 이름만 받아 Hub base 체크포인트(55cf4c4)를 쓴다. 이 서버의 multilingual 슬롯은 ft-v1이라 답이 다를 수 있다.
laya '출근길에 들을 만한 잔잔한 재즈 좀 틀어줘' --lang 'ko' --questions poc/schema/router_v1.json --json
```

## Screenshots

| File | Content |
|---|---|
| `P2_ui_1.png` | First screen (router_v1 example loaded, OUTPUT in its empty state `[ · ]`) |
| `P2_ui_2.png` | After running router_v1: ROUTE card, answer card (passed), probability bars, meta row, tool buttons |
| `P2_ui_3_fallback.png` | min_confidence 0.95: abstained, FALLBACK card |
| `P2_ui_4_warn21.png` | Warning badge at 21 options |
| `P2_ui_5_narrow.png` | 820px 1-column render |
| `P2_ui_6_shadow.png` | Shadow log counters, domain distribution, table |
| `P2_ui_7_full.png` | Full page (including the 3 scenario cards and the docs-and-status section) |
| `P2_ui_8_server_down.png` | Error state after the server was stopped, with the input kept |

## Items for a person to check in the browser (not judged by the automated checks)

- Whether the visual tone resembles jevplayground closely enough (light background, white panels, monospace uppercase subheadings, 1 blue accent color), and whether the Korean wording reads naturally.
- Clipboard: the page's `navigator.clipboard.writeText` succeeded ("✓ curl 복사됨" (curl copied)), and the same string was run in a shell to confirm it. Pasting into an actual terminal by a person was not done.
- Real devices and other browsers: only Chromium (Playwright) was checked. Phone widths (around 390px) and Safari/Firefox were not examined.
- The 503 + `Retry-After` display path (needs an overload) and the 413 path for 101 or more options were not reproduced in the UI. The 413 of `/poc/decide` (a 50,001-character utterance) was confirmed only in the offline checks.
- Docs 00\~07 are provided only as copyable paths, because the server does not serve `docs/`. Whether this is sufficient for review purposes.
- Static file cache: right after a UI edit, Chrome may show the previous `index.html` (no `Cache-Control` in Starlette `StaticFiles`). Check with a hard reload.

**English** | [한국어](P2_ui_check.ko.md)
