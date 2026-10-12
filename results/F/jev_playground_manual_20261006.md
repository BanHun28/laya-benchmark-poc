# Jev playground manual head-to-head: Korean domain routing, 24 rows (2026-10-06)

**Verdict.** On the same 24 Korean routing items, Jev beats Laya zero-shot but does not beat ft-v1. With n = 24 and a single pass, both results are indicative only.

- Jev 20/24 = 0.833 vs zero-shot 10/24 = 0.417. b = 10, c = 0, exact McNemar p = 0.002.
- ft-v1 22/24 = 0.917 vs Jev. b = 0, c = 2, p = 0.5. The difference is not significant, but it points toward ft-v1, and ft-v1 also got right every row that Jev got right.

| Item | Value |
|---|---|
| Accuracy (Wilson 95%) | Jev 20/24 = 0.833 [0.641, 0.933], Laya zero-shot 10/24 = 0.417 [0.245, 0.612], Laya ft-v1 22/24 = 0.917 [0.742, 0.977] |
| Jev runs sent to the site | `POST /api/evaluate` 25 times. Session 1: 2 (200: 1, 502: 1); session 2: 23 (all 200) |
| Session 2 budget | 23 of 46 used |
| Retries | The 60 s retry rule fired 0 times. Row 37 was run again when resuming after the session 1 502 (attempt 2) |
| pacing | Minimum gap between clicks within one page load 21.6 s (rule ≥ 3 s) |
| pass 2 (key-only labels) | Skipped (decided at resumption, option c) |
| Browser sessions (KST) | Session 1 08:07:14\~08:13 (stopped by a 502 at run 2). Session 2 08:24:18\~08:34 (runs 2\~24) |

## 1. Method

### 1.1 Sample (no model run, `results/F/jev_f.py sample`)

- Source: `data/evals/ko_massive_domain_8.jsonl`, 500 rows. dataset_sha256 `edf33079033640fa9656c3b583a422c1ededc4bcd75eaafbfb84c5adf613f46b`, questions_sha256 `a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54`.
- Test half: 250 rows by the index-parity rule of `results/B/B_splits.json` (a data row with an odd index is test; `scripts/metrics_extra.py` `row_splits`).
- Train duplicates removed: the 16 rows whose utterance appears verbatim in `poc/finetune/data/domain8_train.jsonl` (11,094 rows) were dropped, leaving 234 rows. This matches the 16 test duplicates recorded in the P4 document.
- Selection rule (our interpretation, stated explicitly): sort the candidates by ascending row index. Go through the domains in schema order (productivity, media, smart_home, info_qa, communication, lifestyle, transport, general) and draw `rng.sample(candidates, 3)` with a single `random.Random(13)` instance. The 24 drawn rows, sorted by row index, give the run order. Candidates per domain: 28/24/30/28/32/33/27/32.
- Laya predictions: read from `cases[row_index]` of `results/B/20261002-1643_multilingual_ko_massive_domain_8.json` for zero-shot and of `results/P4/full_20261003-1156_ft-v1_ko_massive_domain_8.json` for ft-v1. p is `answer.answer_confidence`. For both reports we assert that dataset_sha256 matches and that cases align with rows on expected and tags.
- Representativeness: on the 24 rows, zero-shot 0.417 / ft-v1 0.917. On the 234 clean test rows, 0.496 / 0.893, and with equal domain weights 0.491 / 0.898. The sample is domain-balanced (3 rows per domain).

### 1.2 Jev protocol (the same information Laya received)

- https://jevplayground.com/ , "Single question", Decision type "Choice".
- State: the original Korean utterance, verbatim.
- Question: `Which domain should handle this request?`. Laya's instructions are ``Which domain should handle the request in `utterance`?``. The wording differs slightly because Jev's state is the raw text, not a dict.
- Choices: 8, fixed in schema order. Each is `key: Korean description`, with the strings taken verbatim from the criteria in `poc/schema/router_v1.json`. In both sessions we clicked "+ Add choice" 4 times and confirmed that the counter read "8 of 10". The choice input's maxlength is 80 characters; the longest label is 43 characters.
- Error rules:
  - Session 1: stop immediately on any error.
  - Session 2 (decided at resumption): on a 5xx or "temporarily unavailable", retry only that row, 1 time, after 60 s, and stop if the retry also fails. Stop immediately on a 429, a rate-limit message or a captcha. Failed requests count toward the request total.

### 1.3 Instrumentation and verification (read-only devices that add no site requests)

- Pre-Run precheck: in the browser, compute the SHA-256 of the State, Question and Choices values and compare it with the value Python computed from the sample file. Also check the "8 of 10" counter and the pressed state of "Single question" and "Choice". Run was clicked only after all 25 had passed.
- Passive listeners were placed on the page: a capture-phase click listener records the Run click time, and a MutationObserver records status-text changes. This confirms that the result read is the final state after the last click ("Evaluation complete" or an error). Editing State resets the result panel, so there is also no risk of re-reading an earlier result.
- Reading results: the DOM of the result region is saved to `results/F/jev_raw/p1_NN.json` (not included in the public repository). It holds the innerText, the collapsed "View details" JSON, the form values, and the POST status and duration from PerformanceResourceTiming. `jev_f.py record` parses and validates it and appends it to `jev_runs_raw.jsonl` (not included in the public repository). Within the same record it was also cross-checked against the accessibility snapshot (including the result; not included in the public repository) that Playwright MCP saved right after the click. The DECISION heading, the probability list, ms and state were compared, and all 24 successful runs matched.
- Record checks:
  - state equals the sample utterance; choices and question match exactly.
  - The click count of this page load equals the number of records made in that load + 1 (no duplicate clicks).
  - The gap from the previous click is at least 3 s.
  - Exactly 1 `POST /api/evaluate` followed that click.
  - Successful runs are additionally checked for the following:
    - The displayed decision, the choice in the details JSON and the status text agree.
    - The displayed % equals round(details probability × 100).
    - The decision is the argmax of the displayed probabilities.
- Records have an `attempt` field. `attempt: 1` was added afterwards to the 2 records of session 1. Rebuilding those 2 records from the saved evidence (dump, snapshot) reproduces the updated file byte for byte.

## 2. Run log

- **Session 1.**
  - Run 1 (row 1) was normal: click at 08:09:33.548, POST 200 (Jev's per-item outputs are omitted in the public repository).
  - Run 2 (row 37): after the click at 08:11:43.600, "Jev is temporarily unavailable." / "Unable to evaluate" appeared. The console logged `Failed to load resource: the server responded with a status of 502 () @ https://jevplayground.com/api/evaluate`.
  - Per the rule in force at the time, we stopped without retrying, collected only the evidence, and closed the browser.
- **Recovery check.** At 08:20 the default example was confirmed to have recovered. This run was a separate check run, so it is not included in the counts below. The same applies to the 1 pre-check at 08:01.
- **Session 2.**
  - At 08:24:18 the page was opened fresh and the same settings (Question, 8 choices, "8 of 10") were entered again. The passive listeners were also reinstalled.
  - Runs 2\~24 (23 rows) were executed. All 23 returned 200, with 0 console errors (all 98 warnings were CSS preload notices).
  - The 60 s retry rule never fired. 23 of the remaining budget of 46 were used.
- **HTTP requests recorded by the browser.**
  - Session 1, 36 requests: static 20, Next.js RSC prefetch GET 14, `POST /api/evaluate` 2 (200, 502).
  - Session 2, 57 requests: static 20, RSC prefetch 14, `POST /api/evaluate` 23 (all 200).
  - Source: `results/F/jev_raw/network_requests_session{,2}.txt` (not included in the public repository).
- **Protocol screenshots** (not included in the public repository):
  - `results/F/jev_shots/p1_run01_row001.png`: run 1.
  - `results/F/jev_shots/p1_run02_row037_error502.png`: the 502 screen of run 2 in session 1.
  - `results/F/jev_shots/p1_run12_row239.png`: run 12.
  - `results/F/jev_shots/p1_run24_row459.png`: run 24.

## 3. Result tables (output of `.venv/bin/python results/F/jev_f.py analyze`)

### Per-row (O = gold, X = wrong; Jev p = displayed %, Laya p = answer_confidence)

| # | row | utterance | gold | Jev pass 1 (key: ko-description) | Laya zero-shot | Laya ft-v1 |
|---|---|---|---|---|---|---|
| 1 | 1 | 내 화면 밝기 현황 알려줘 | general | — | X smart_home (0.81) | X smart_home (0.94) |
| 2 | 37 | 아들 방 불 꺼 줘 | smart_home | — [attempt 2] | O smart_home (0.99) | O smart_home (0.95) |
| 3 | 39 | 도미노피자에서 소세지 피자 주문해줘 | lifestyle | — | O lifestyle (1.00) | O lifestyle (0.94) |
| 4 | 61 | 올리야 집 컬러 밝은 거에서 어두운 색으로 바꿔 | smart_home | — | O smart_home (0.99) | O smart_home (0.93) |
| 5 | 71 | 이 동네 최신 뉴스 | info_qa | — | X media (0.32) | O info_qa (0.95) |
| 6 | 77 | 스피커 볼륨 무음으로 해줘 | media | — | X smart_home (0.81) | O media (0.95) |
| 7 | 117 | 진공 청소기 켜서 사용해 | smart_home | — | O smart_home (0.93) | O smart_home (0.96) |
| 8 | 181 | 올리 내 하루에 대해 너에게 말해야만 해 | general | — | X info_qa (0.57) | O general (0.92) |
| 9 | 201 | 휴가 스포츠 | general | — | X smart_home (0.92) | X media (0.36) |
| 10 | 207 | 내일 서울 회의 리마인더 추가해 | productivity | — | X general (0.95) | O productivity (0.96) |
| 11 | 209 | 이번 주말에 시내에 일정 있어 | productivity | — | X info_qa (0.46) | O productivity (0.94) |
| 12 | 239 | 유월 이십이일에 현수 생일이라고 표시해줘 | productivity | — | X general (0.43) | O productivity (0.94) |
| 13 | 259 | 채소 라자냐 만드는 데 얼마나 걸려 | lifestyle | — | O lifestyle (1.00) | O lifestyle (0.93) |
| 14 | 269 | 오븐에 굽는 거랑 직화에 굽는 거랑 뭐가 달라 | lifestyle | — | X smart_home (0.66) | O lifestyle (0.93) |
| 15 | 277 | 사가 열어 | media | — | X smart_home (0.99) | O media (0.90) |
| 16 | 279 | 게임들 열어 | media | — | X smart_home (0.38) | O media (0.94) |
| 17 | 335 | 부산에서 울산 가는 다음 기차 언제야 | transport | — | O transport (1.00) | O transport (0.95) |
| 18 | 357 | 장소 가는 택시 한 대 예약해 | transport | — | O transport (1.00) | O transport (0.96) |
| 19 | 383 | 청주 에 기차 몇 시에 도착하지 | transport | — | O transport (1.00) | O transport (0.94) |
| 20 | 411 | 달러 에서 유로 로 | info_qa | — | X transport (0.35) | O info_qa (0.95) |
| 21 | 435 | 삼성 t.v. 에 관한 설명 찾아줘 | info_qa | — | X transport (0.64) | O info_qa (0.95) |
| 22 | 445 | 트위터 열어서 메시지 보내 | communication | — | O communication (0.54) | O communication (0.96) |
| 23 | 453 | 유플러스에 불만 트윗 해 | communication | — | X general (0.64) | O communication (0.96) |
| 24 | 459 | 민호에게 보낼 이메일 작성해줘 | communication | — | O communication (1.00) | O communication (0.96) |

### Accuracy

| system | rows | correct | accuracy | Wilson 95% CI |
|---|---|---|---|---|
| Jev pass 1 (key: ko-description) | 24 | 20/24 | 0.833 | [0.641, 0.933] |
| Laya zero-shot multilingual | 24 | 10/24 | 0.417 | [0.245, 0.612] |
| Laya ft-v1 | 24 | 22/24 | 0.917 | [0.742, 0.977] |

### Agreement and exact McNemar (paired rows only; b = Jev right & Laya wrong, c = Jev wrong & Laya right)

| pair | n | same label | b | c | exact McNemar p |
|---|---|---|---|---|---|
| Jev pass 1 vs zero-shot | 24 | 10 | 10 | 0 | 0.0020 |
| Jev pass 1 vs ft-v1 | 24 | 20 | 0 | 2 | 0.5000 |

### Jev confidence behaviour (displayed %; the playground rounds probabilities to 2 decimals)

| pass | runs | top = 100% | runs with any 0% option | 0% cells / all cells | mean top % | mean top % right / wrong | wrong with top >= 90% | mean provider confidence |
|---|---|---|---|---|---|---|---|---|
| 1 | 24 | 14 | 23 | 145/192 | 91.3 | 96.5 / 65.5 | 0/4 | 0.899 (n=24) |

### Jev latency (ms, successful runs)

| pass | runs | displayed 'server + network' median / min / max | browser POST /api/evaluate median / min / max | click -> 'Evaluation complete' median / min / max |
|---|---|---|---|---|
| 1 | 24 | 249.5 / 203 / 570 | 497.5 / 444 / 913 | 502.5 / 446 / 916 |

### Jev model and token usage (details panel)

| pass | runs | model_id values | input tokens median / min / max | output tokens median / min / max |
|---|---|---|---|---|
| 1 | 24 | `typesafe-ai/jev` x24 | 716 / 708 / 727 | 255 / 249 / 262 |

### Per-domain correct

| gold domain | rows | Jev pass 1 (key: ko-description) | Laya zero-shot | Laya ft-v1 |
|---|---|---|---|---|
| productivity | 3 | 3/3 | 0/3 | 3/3 |
| media | 3 | 1/3 | 0/3 | 3/3 |
| smart_home | 3 | 3/3 | 3/3 | 3/3 |
| info_qa | 3 | 3/3 | 0/3 | 3/3 |
| communication | 3 | 3/3 | 2/3 | 3/3 |
| lifestyle | 3 | 3/3 | 2/3 | 3/3 |
| transport | 3 | 3/3 | 3/3 | 3/3 |
| general | 3 | 1/3 | 0/3 | 1/3 |

### Requests sent to jevplayground.com /api/evaluate

Total 25: HTTP 200 24, other 1; retries (attempt > 1) 1; smallest gap between consecutive clicks in one page load 21.6 s.

| pass | run | attempt | row | KST click time | gap from previous click (s) | HTTP | displayed ms | outcome |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | — | — | — | — | — |
| 1 | 2 | 1 | 37 | — | — | — | — | — |
| 1 | 2 | 2 | 37 | — | — | — | — | — |
| 1 | 3 | 1 | 39 | — | — | — | — | — |
| 1 | 4 | 1 | 61 | — | — | — | — | — |
| 1 | 5 | 1 | 71 | — | — | — | — | — |
| 1 | 6 | 1 | 77 | — | — | — | — | — |
| 1 | 7 | 1 | 117 | — | — | — | — | — |
| 1 | 8 | 1 | 181 | — | — | — | — | — |
| 1 | 9 | 1 | 201 | — | — | — | — | — |
| 1 | 10 | 1 | 207 | — | — | — | — | — |
| 1 | 11 | 1 | 209 | — | — | — | — | — |
| 1 | 12 | 1 | 239 | — | — | — | — | — |
| 1 | 13 | 1 | 259 | — | — | — | — | — |
| 1 | 14 | 1 | 269 | — | — | — | — | — |
| 1 | 15 | 1 | 277 | — | — | — | — | — |
| 1 | 16 | 1 | 279 | — | — | — | — | — |
| 1 | 17 | 1 | 335 | — | — | — | — | — |
| 1 | 18 | 1 | 357 | — | — | — | — | — |
| 1 | 19 | 1 | 383 | — | — | — | — | — |
| 1 | 20 | 1 | 411 | — | — | — | — | — |
| 1 | 21 | 1 | 435 | — | — | — | — | — |
| 1 | 22 | 1 | 445 | — | — | — | — | — |
| 1 | 23 | 1 | 453 | — | — | — | — | — |
| 1 | 24 | 1 | 459 | — | — | — | — | — |

Notes:
- The "retries (attempt > 1) 1" in the request table is row 37 being run again on resumption. Retries under the 60 s retry rule: 0.
- The first click of session 2 (row 37, attempt 2) was the first click of a new page load, so its gap cell is empty. It came 798 s after the last click of session 1.
- Sample power: on this sample Jev could never have beaten ft-v1 significantly. With ft-v1 at 22/24, even Jev at 24/24 would give only b = 2, c = 0, p = 0.5.

## 4. Observations

1. **Error structure: the two rows Jev lost to ft-v1 follow a MASSIVE convention that the descriptions do not state.**
   - 2 of the 4 rows Jev got wrong are ambiguous `scenario:general` sentences, and ft-v1 and zero-shot also got both wrong.
   - The other 2 rows are game-launch sentences from `scenario:play`.
   - This dataset's domain mapping groups the MASSIVE `play` scenario under `media`, but our `media` description ("음악, 라디오, 팟캐스트, 오디오북 재생과 음량 조절", i.e. music, radio, podcast and audiobook playback and volume control) does not mention games. ft-v1 learned this convention from its training data (0.90 / 0.94), and zero-shot Laya also got both wrong (`smart_home`).
   - The gap to ft-v1 therefore more likely comes from information missing from the label descriptions than from model capability. Whether adding "게임" (games) to the description would change these two rows for the zero-shot systems is an untested hypothesis.
   - Meanwhile, of the 14 rows zero-shot Laya got wrong, Jev got 10 right: productivity and info_qa went 0/3 → 3/3, media 0/3 → 1/3.
2. **Confidence: Jev was not confident in its wrong answers.**
   - 14 of the 24 runs displayed 100%, and 145 of the 192 cells were 0%. Because the playground rounds to two decimal places, values of 0.995 and above show as 100% and values below 0.005 as 0%.
   - The top probabilities of the 4 wrong answers were 41\~86% (mean 65.5%), all below 90%. The mean for correct answers is 96.5%.
   - Cutting at 90%, Jev accepts 18 of the 24 rows and gets 18/18 right. Cutting ft-v1 at the P2 policy threshold T = 0.907, it accepts 22 rows and gets 21/22 right; the accepted wrong answer is row 1 (0.94).
   - The separate provider `confidence.decision` in the details averaged 0.958 on correct answers and 0.603 on wrong ones.
   - With n = 24 this is indicative only.
3. **Latency and cost structure: a hosted generative call versus a local encoder.**
   - Jev's displayed value ("server + network") has a median of 249.5 ms (203\~570). Measured in the browser, the same requests have a POST median of 497.5 ms (444\~913). The displayed value is not the client round trip.
   - According to the details, 1 decision takes about 716 input tokens and about 255 output tokens (249\~262). This appears to be generative decoding (inferred).
   - Local Laya reference values:
     - P2 `/poc/decide` round trip p50 20.1 ms (ft-v1, MPS, loopback; `results/poc/P2_20261003.md:67`).
     - Track D in-process 13.8 ms (multilingual MPS, 1 question; `results/D/D_summary_20261003.md:42`).
   - Ratios: 12.4× / 18.1× on the displayed value, 24.8× / 36.1× on the browser measurement.
   - These ratios include the difference between an internet round trip to a hosted service (Jev) and local loopback or in-process calls (Laya), so they are not a model-speed comparison.
   - The median displayed value lies within the 3rd-party published Jev p50 range of 236\~276 ms (`docs/03_benchmark_plan.md` §10 F4).

**Other facts:**
- The Model ID in the details was `typesafe-ai/jev` in all 24 runs, with no version shown.
- `rounding.probabilityDecimals` was always 2 and `warnings` was always empty.
- The key order of the probabilities in the response JSON differed from the input choice order. Whether the playground or the API reorders them is unknown.
- Availability: session 1 hit a 502 1 time; about 13 minutes later, all 23 runs of session 2 were normal.

## 5. Caveats

- **n**: n = 24, single pass. The accuracy, McNemar and confidence figures are all indicative only. The sample is domain-balanced, so its accuracy differs from accuracy on the natural distribution.
- **The playground is not the API**:
  - The site is an independent 3rd-party tool ("not affiliated with or endorsed by TypeSafe AI").
  - The model version is unknown: the page says only "TypeSafe Jev", and the details show only Model ID `typesafe-ai/jev`.
  - Responses pass through the playground's normalization (probabilities rounded to 2 decimals) and its own backend.
  - "Real model execution. No simulated answers." is the page's claim and cannot be verified.
  - The two sessions are different page loads about 13 minutes apart. The Model ID was the same.
- **Option representation**: Jev choices have no description field, so `key: description` was entered as a single label string. Laya receives the key and the description separately in the criteria dict. The question wording also differs slightly (§1.2). Because the key-only labels (pass 2) were skipped, how much Jev uses the Korean descriptions was not measured.
- **Jev's Korean support** is not documented (unverified).
- **Laya side**: the figures were read from existing reports (CPU fp32, 2026-10-02/03) and not rerun this time. ft-v1 was trained on train data from the same MASSIVE distribution (exact duplicate utterances excluded), so against Jev, a zero-shot system, it has an in-domain advantage. The `play` → `media` convention in §4.1 is an example.
- **Reproducibility**: whether Jev's output is deterministic was not checked. No row was run successfully twice.

## 6. Decisions and resumption log

- Session 1 stopped at the 502 of run 2, per the stop rule.
- After recovery was confirmed at 08:20, the following was decided:
  1. Run the remaining 23 rows with the same 8 choices.
  2. On a 5xx or "temporarily unavailable", retry 1 time after 60 s and stop if it fails again. Keep total requests within 46.
  3. Skip pass 2 (option c).
  4. Delete the Playwright MCP output directory, including files left by other runs.
- Session 2 ended after 23 runs, leaving 23 in the budget.
- Code changes: `jev_f.py record` now records both successes and errors (exit 2 on an error) and attaches `attempt`. `record_error`, the command name used in session 1, was kept as an alias. `analyze` drops passes that were not run from its tables.

## 7. Files

| File | Contents |
|---|---|
| `results/F/jev_f.py` | sample / record (record_error alias) / analyze. No model calls |
| `results/F/jev_sample_24.jsonl` | 24 rows: utterance, gold, laya_zs, laya_zs_p, laya_ft, laya_ft_p, row_index |
| `results/F/jev_runs_raw.jsonl` (not included in the public repository) | 25 Jev requests (24 successes, 1 502 on the 1st attempt of row 37) |
| `results/F/jev_raw/` | 25 pairs of per-request DOM dumps (`p1_NN.json`, `p1_02_error.json`) and accessibility snapshots (`*.snapshot.yml`), `network_requests_session{,2}.txt`, `console_session{,2}.log` (the DOM dumps, accessibility snapshots, network lists and console logs are not included in the public repository) |
| `results/F/jev_shots/` (not included in the public repository) | `p1_run01_row001.png`, `p1_run02_row037_error502.png`, `p1_run12_row239.png`, `p1_run24_row459.png` |
| `results/F/F_jev_20261006.md` | Run Card (`docs/06_templates.md` §1) |

**English** | [한국어](jev_playground_manual_20261006.ko.md)
