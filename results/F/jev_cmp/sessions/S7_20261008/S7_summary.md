# S7 summary: T9 Enron spam 40 + T10 customer-support ticket queue 40 (2026-10-08)

**Verdicts.**
1. **T9 Enron spam cannot separate the systems because all four are at the ceiling.** Jev, Laya english, multilingual and Router all score 40/40 = 1.000 [0.912, 1.000]. Predicted positives are 20/40 for all of them (gold 20), and the exact McNemar test gives b/c 0/0, p=1.0 for all three pairs. The AUROC of p(true) is also 1.000 for all four systems (perfect separation, so the bootstrap CI degenerates to [1.000, 1.000]). Only calibration differs. Brier is Jev 0.019, english 0.005, multilingual 0.000. Jev shows 100% on 0/40, and even its most ambiguous rows, at p(true) 0.58 (gold true) and 0.09 (gold false), stay away from 0.5. T9 is a task in Laya's training mix (BENCHMARKS.md:142 "in training"), at the same level as upstream english 0.993.
2. **On T10 10-way queue routing all three systems are low, and the differences are not significant.** Jev 10/40 = 0.250 [0.142, 0.402], Laya english (= Router) 12/40 = 0.300 [0.181, 0.454], multilingual 18/40 = 0.450 [0.307, 0.602]. The exact McNemar test (b = only Jev correct, c = only Laya correct) gives vs english 3/5 p=0.727 and vs multilingual 4/12 p=0.077. At n=40, even the 0.2 difference (multilingual) did not get below 0.05.
3. **Jev is strongly overconfident on T10.** Its mean top p is 0.873 while its accuracy is 0.250. 18 of its 30 wrong answers have top ≥ 0.90, and it shows the gold option as 0% on 20/40 rows (50%). Even keeping only top ≥ 0.90, 18 of the 24 remaining rows are wrong. Under the same cutoff, Laya english has 0 wrong out of 6 rows and multilingual 0 out of 8. Brier is Jev 1.319, english 0.775, multilingual 0.611, and ECE is 0.623 / 0.253 / 0.215.
4. **T10's low accuracy is mixed with a gold-label problem (interpretation, to be verified).** All three systems are wrong on 18/40 rows. On Human Resources and Customer Service all three systems score 0/4. The ticket contents of these rows often do not match the queue descriptions we gave. Many of Jev's wrong answers read as choices that follow the descriptions (pricing inquiry → Sales and Pre-Sales) (Jev's per-item outputs are omitted in the public repository). Billing and Payments, where Laya is ahead (Laya 4/4, Jev 2/4), matches the dataset convention "pricing inquiry → Billing". T10 is a task in Laya's training mix (BENCHMARKS.md:147).
5. **Operation:** all 80 requests (A 40 + B 40) returned HTTP 200. There were 0 occurrences of 5xx · 4xx (including 429) · limit messages · captcha · error screens, and no retries. Gaps on the monotonic clock: min 15.009 s, median 15.134 s. The pre-request sha12 and post-request body byte checks matched 80/80. The cumulative total for the site is 518 requests.

This goes through the playground, not the API. The model version is not shown (`typesafe-ai/jev` 80/80). n=40 per task. Jev probabilities are rounded to the second decimal place. T9 · T10 are tasks in Laya's training mix, and Jev's training data is unknown.

## 1. Run overview

| Item | Value |
|---|---|
| Requests | `POST /api/evaluate` 80 = Part A (T9) 40 + Part B (T10) 40, all HTTP 200. Plan 80, session cap 90 (retry margin). The instrumentation's `ready()` refused to click once Run clicks reached 90 (`raw/js/instrument.js`, not included in the public repository) |
| Stop conditions | 5xx 0, 4xx 0 (429 0), limit messages 0, captcha 0, error screens 0. On every run, the result panel · status · title · `[role=alert]` · body text were checked against the limit-message regex, and captcha iframes were checked too (`s7_record.py`, dump `page`). All 80: `body_stop_match` null, alerts [], captcha_frames []. Before the runs, it was confirmed that 0 input strings (state · question · options) match this regex (`s7_prep.py` assert) |
| Gaps (between Run clicks) | Guard 15 s (rule ≥ 10 s), on the monotonic clock from the start. 79 gaps: min 15.009 s, median 15.134 s, max 22.770 s (run 2: after the run 1 screenshot). The resource timing start gaps are also 15.008 / 15.134 / 22.768 s |
| Input identity | Before each request: the payload sha12 built from the form values matched the form-file expected value 80/80 (`window.__jev.ready`). After each request: the captured request body was byte-identical to the `jev_cmp.py` payload 80/80 (`payload_exact`). 4 no-click dry runs before the first request (items 1, 21, 29, 41) |
| Input content | T9: Single / Boolean, the question sentence only (no criteria for Laya noul either; the Boolean form has no label · description fields). T10: Single / Choice, 10 options `key: description` (exactly Laya's `render_options` rendering, 30\~73 characters, the same list · order on every row). Every State is the string Laya reads, `json.dumps(state, ensure_ascii=False)`, and before the runs all 80 rows were confirmed to equal `state_text`. T9 body max 1,984 characters (below upstream's 3,000-character truncation), state max 2,117 characters (limit 8,000) |
| dry run results | In all 4: form values = input strings, sha12 matched, no alert · invalid. State counters "712 / 8,000", "1,124 / 8,000", "2,117 / 8,000", "672 / 8,000". The 10 T10 option fields have lengths of 66 · 48 · 54 · 50 · 65 · 54 · 73 · 44 · 51 · 30 characters (maxLength 80), with no truncation. The U+0092 character of item 21 (T9 row 20) was also preserved (`raw/dry_runs.json`) |
| Screen = response | 80/80 (DECISION, bar %). Displayed latency = `latencyMs` half-up 80/80 |
| Model ID / response metadata | `model` and View details both `typesafe-ai/jev` 80/80. `rounding` {2, 2}, `warnings` [] 80/80. provider `confidence.decision` is present for T10 40/40 and absent for the 40 T9 Booleans |

## 2. T9 Enron spam (40 rows, gold true 20 / false 20)

### 2.1 Accuracy · positive rate · ranking quality

| system | correct / n | accuracy [Wilson 95%] | predicted true (gold 20) | Brier | ECE | mean top p | AUROC p(true) [bootstrap 95%] |
|---|---|---|---|---|---|---|---|
| Jev (playground, displayed p, 2 decimals) | 40/40 | **1.000** [0.912, 1.000] | 20 | 0.019 | 0.060 | 0.940 | 1.000 [1.000, 1.000]* |
| Laya english | 40/40 | 1.000 [0.912, 1.000] | 20 | 0.005 | 0.014 | 0.986 | 1.000 [1.000, 1.000]* |
| Laya multilingual | 40/40 | 1.000 [0.912, 1.000] | 20 | 0.000 | 0.000 | 1.000 | 1.000 [1.000, 1.000]* |
| Laya Router (all 40 to english) | 40/40 | 1.000 [0.912, 1.000] | 20 | 0.005 | 0.014 | 0.986 | 1.000 [1.000, 1.000]* |

- The decision rule is p(true) ≥ 0.5 (the laya-evals rule). As in S3 · S5, Brier is Σ(p − onehot)² over the two cells {false, true} (= 2(p − y)²).
- *All four systems separate these 40 rows perfectly. So the AUROC of every bootstrap resample is 1 and the percentile CI degenerated to width 0. This does not mean that the population AUROC is 1.
- The Laya values equal the vanilla T9 Jev-format 40 in `PREP_20261008.md` §5 (1.000 / 1.000 / 1.000, Brier en / ml 0.005 / 0.000, ECE 0.014 / 0.000).

### 2.2 Agreement, exact McNemar test, AUROC difference

| pair | n | same prediction | b | c | McNemar p | AUROC Jev − Laya [paired bootstrap 95%] |
|---|---|---|---|---|---|---|
| Jev vs Laya english | 40 | 40 | 0 | 0 | 1.0000 | +0.000 [+0.000, +0.000] |
| Jev vs Laya multilingual | 40 | 40 | 0 | 0 | 1.0000 | +0.000 [+0.000, +0.000] |
| Jev vs Laya Router | 40 | 40 | 0 | 0 | 1.0000 | +0.000 [+0.000, +0.000] |

### 2.3 Confidence and margin

| system | p(true) ∈ {0, 1} (shown as 100%) | min p(true) on gold true | max p(true) on gold false | distinct p(true) values |
|---|---|---|---|---|
| Jev | 0/40 | 0.58 | 0.09 | 16 |
| Laya english (= Router) | 34/40 | 0.76 (row 23, id 1068) | 0.17 (row 26, id 1163) | 8 |
| Laya multilingual | 39/40 | 1.00 | 0.002 | 3 |

- Jev's p(true) on gold true is 0.58\~0.97 (2 below 0.90), and on gold false 0.01\~0.09.
- The pattern of Jev not showing 100% on Boolean questions is the same as in T5 · T8 (`S5_summary.md` §4.3).

### 2.4 Context

| Figure | Value | Notes |
|---|---|---|
| Laya Enron spam upstream | english 0.993 / multilingual 0.993 (BENCHMARKS.md:142, first 400 test rows, in training) | inside this run's 40-row Wilson CI [0.912, 1.000] |
| Laya vanilla ext500 | english 0.992 / multilingual 0.990 (`PREP_20261008.md` §5) | same test split, stratified sample excluding the 261 rows that overlap the training set |
| Jev spam published figure | none for Enron (the 3rd-party SMS spam 0.930 is different data, bench_apps.py `JEV_PUBLISHED`) | |

## 3. T10 customer-support ticket queue (40 rows, 4 per queue)

### 3.1 Accuracy · calibration

| system | correct / n | accuracy [Wilson 95%] | Brier | ECE | mean top p |
|---|---|---|---|---|---|
| Jev (playground, displayed p, 2 decimals) | 10/40 | **0.250** [0.142, 0.402] | 1.319 | 0.623 | 0.873 |
| Laya english | 12/40 | 0.300 [0.181, 0.454] | 0.775 | 0.253 | 0.504 |
| Laya multilingual | 18/40 | 0.450 [0.307, 0.602] | 0.611 | 0.215 | 0.586 |
| Laya Router (all 40 to english) | 12/40 | 0.300 [0.181, 0.454] | 0.775 | 0.253 | 0.504 |

Brier was computed per row as Σ(p − onehot)² over the 10 options. ECE uses 15 bins, by top p. The Laya values equal the vanilla T10 Jev-format 40 in `PREP_20261008.md` §5 (0.300 / 0.450 / 0.300, Brier 0.775 / 0.611, ECE 0.253 / 0.215).

### 3.2 Agreement and exact McNemar test (b = only Jev correct, c = only Laya correct)

| pair | same label | b | c | p | b rows | c rows |
|---|---|---|---|---|---|---|
| Jev vs Laya english (= Router) | 18 | 3 | 5 | 0.7266 | — | — |
| Jev vs Laya multilingual | 9 | 4 | 12 | 0.0768 | — | — |

All three systems are correct on 5 rows and all wrong on 18 rows. Even the 0.200 difference from multilingual is not significant at n=40 (with b=4, c ≥ 13 would be needed for p < 0.05).

### 3.3 Correct answers per queue (n=4 each)

| gold | Jev | Laya english | Laya multilingual |
|---|---|---|---|
| Technical Support | 1 | 3 | 3 |
| Product Support | 0 | 0 | 2 |
| Customer Service | 0 | 0 | 0 |
| IT Support | 1 | 0 | 2 |
| Billing and Payments | 2 | 4 | 4 |
| Returns and Exchanges | 1 | 1 | 2 |
| Service Outages and Maintenance | 3 | 4 | 3 |
| Sales and Pre-Sales | 1 | 0 | 2 |
| Human Resources | 0 | 0 | 0 |
| General Inquiry | 1 | 0 | 0 |

### 3.4 Prediction distribution (gold is 4 per queue)

| system | predicted label distribution |
|---|---|
| Jev | Technical Support 12, IT Support 9, General Inquiry 6, Sales and Pre-Sales 5, Service Outages 3, Billing 2, Product Support 2, Returns 1, Customer Service 0, Human Resources 0 |
| Laya english | Technical Support 21, Customer Service 5, Billing 4, Service Outages 4, Product Support 3, Returns 1, Sales 1, IT Support 1, General Inquiry 0, Human Resources 0 |
| Laya multilingual | Product Support 10, Technical Support 8, Billing 5, Customer Service 5, IT Support 4, Returns 3, Service Outages 3, Sales 2, General Inquiry 0, Human Resources 0 |

Jev put 21/40 on Technical Support and IT Support, and Laya english put 21/40 on Technical Support (the same direction as the ext500 skew of 281/500 in `PREP_20261008.md` §5). No system chose Human Resources.

### 3.5 Confidence and abstention

| Item | Jev | Laya english | Laya multilingual |
|---|---|---|---|
| mean top p (correct / wrong) | 0.861 / 0.877 | 0.780 / 0.386 | 0.797 / 0.413 |
| top ≥ 0.90 among wrong answers | 18/30 | 0/28 | 0/22 |
| shown as 100% | 8/40 (6 of them wrong) | - | - |
| gold option shown as 0% | 20/40 | - | - |
| provider confidence (correct / wrong) | 0.846 / 0.863 | - | - |

| Keep rule | Jev rows kept / wrong | Laya english rows kept / wrong | Laya multilingual rows kept / wrong |
|---|---|---|---|
| top ≥ 0.80 | 29 / 22 | 8 / 1 | 10 / 0 |
| top ≥ 0.90 | 24 / 18 | 6 / 0 | 8 / 0 |
| top ≥ 0.95 | 19 / 13 | - | - |

- Jev's confidence is the same on correct and wrong answers (0.861 vs 0.877). So confidence-based abstention does not filter out wrong answers. Both Laya checkpoints have low confidence on wrong answers, so keeping only 0.90 or higher leaves 0 wrong answers in this sample (descriptive statistics on the same 40 rows).
- The 50% rate of the gold option shown as 0% is far higher than Jev's 3rd-party Emotion zero-probability failure rate of 16% (bench_apps.py `JEV_PUBLISHED`) and S2 T3's 7/40 (17.5%).
- provider confidence equals top p on 18/40, and its means on correct · wrong answers are almost the same, so it is not a separate signal.

### 3.6 Error structure (interpretation, to be verified)

| Category | rows | Content (summary) |
|---|---|---|
| Jev wrong at 100% | — | Technical Support 4 (gold Sales 1, Returns 2, IT 1), Sales 2 (gold Billing 2) |
| Queues where all three systems score 0/4 | Human Resources / Customer Service | The HR gold tickets are a report of unauthorized access to medical data, an inquiry about a promotion strategy for gaming products, an inquiry about SaaS integration and an inquiry about QuickBooks integration. The CS gold tickets concern system performance degradation, a data breach, declining campaign engagement and an inquiry about a brand growth strategy |
| Only Laya correct (Billing) | — | All three Laya runners sent the pricing · payment-option inquiries to Billing (0.98\~1.00). Jev followed the description "Sales and Pre-Sales: pricing, quotes, buying" and sent them to Sales (100%) |

- The classification above is a judgment made by reading the tickets. Scoring used the dataset labels as they are.
- From our reading, many T10 gold labels do not match the queue descriptions given in the question (the same wording as `QUEUES` in upstream bench_apps.py). On this dataset, accuracy should be read as closer to "agreement with the dataset's labeling convention" than to "routing that fits the descriptions". Upstream marks Laya as trained on this dataset (in training).

### 3.7 Context

| Figure | Value | Notes |
|---|---|---|
| Laya support triage upstream | english 0.502 / multilingual 0.522 (BENCHMARKS.md:147, first 400 English rows, natural distribution, in training) | Not comparable because the queue distributions differ. Our sample is balanced at 4 per queue |
| Laya vanilla ext500 (queue-balanced) | english 0.264 / multilingual 0.454 (`PREP_20261008.md` §5) | Both values lie inside this run's 40-row Wilson CIs ([0.181, 0.454], [0.307, 0.602]) |
| Jev published figure for customer-support queues | none | |

## 4. Latency · tokens

| Part | runs | displayed "server + network" ms median / min / max | browser POST ms median / min / max | click → complete ms median | POST − latencyMs median | input tokens median (min\~max), total | output tokens median (min\~max), total |
|---|---|---|---|---|---|---|---|
| Part A T9 (Boolean) | 40 | 214.5 / 169 / 388 | 481.5 / 388 / 1,243 | 482.5 | 243.2 | 427 (309\~1,059), 19,234 | 20 (20\~20), 800 |
| Part B T10 (Choice 10) | 40 | 226 / 154 / 311 | 495 / 388 / 702 | 496.5 | 239.0 | 681.5 (613\~739), 27,079 | 191 (185\~194), 7,644 |
| S7 overall | 80 | 219 / 154 / 388 | 488.5 / 388 / 1,243 | 491 | 239.0 | 46,313 | 8,444 |

- T9 input tokens correlate with state length at r = 0.964. As in T5 · T8, the Boolean output is a constant 20 tokens. The T10 output of 191 tokens is more than the roughly 150 of S5 T7 (10-option key rendering). This seems to be because the option strings are longer (estimate).
- The browser POST of one T9 run took 1,243 ms (the maximum). The `latencyMs` of the same run was within the displayed-latency range, so the difference is on the network side (the same kind as the S5 case). It is not an error.
- The displayed latency is at the same level as the per-part medians of S1\~S5 (200\~241 ms) and slightly below Jev's 3rd-party p50 of 236\~276 ms (09 §1). Laya's local latency is not compared because the hardware and path differ.

## 5. Observations and limitations

**3 key observations**
1. **T9 has no discriminating power.** All four systems got all of the same 40 rows right, and their rankings are perfect. The only remaining difference is calibration (Jev never outputs 0/1 and stays in the 0.01\~0.97 range, while Laya mostly outputs 0 or 1). Even allowing for this being a task in Laya's training mix, Jev zero-shot reached the same accuracy.
2. **On T10, Jev has the lowest accuracy (0.250) and the worst calibration.** Half of the rows show the gold option as 0%, and there are many high-confidence wrong answers, so confidence-based abstention does not work. The share of wrong answers with top ≥ 0.90 (18/30 = 60%) is at the same level as the single-choice pattern in the S6 synthesis (59% of wrong answers, `docs/09_laya_vs_jev_plan.md` §10 "Calibration"), and the gold-option-at-0% rate (50%) is the highest among the single-choice · score tasks measured so far (T2 1/40, T3 7/40, T4 0/40, T6 1/40, T7 0/100; `analyze` output of each session).
3. **Much of the T10 accuracy is mixed with a problem in the gold-label convention (interpretation).** All three systems are wrong on 18/40 rows, and HR · Customer Service are 0/4 for all. The queue where Laya is ahead (Billing) is the one that matches the dataset convention. Reading the difference between Laya multilingual 0.450 and Jev 0.250 (p=0.077) as a difference in "routing ability" requires checking the gold labels first.

**Limitations**
- This goes through the playground, not the API. The model version is not shown and the prompt wrapping is unknown.
- n=40 per task (95% CI width about ±0.15). T10 has 4 rows per queue, so per-queue numbers are directional signals.
- The bootstrap CI of the T9 AUROC degenerated because of perfect separation. The AUROC differences carry no information either.
- Jev probabilities are rounded to 2 decimals (16 distinct T9 p(true) values).
- By upstream's labeling, T9 · T10 are tasks in Laya's training mix (BENCHMARKS.md:142, :147). Jev's training data is unknown. T10 has only one public split, so our test share may have been part of upstream's training (`PREP_20261008.md` §2).
- The quality of the T10 gold labels was not checked (§3.6 is interpretation).

## 6. Operation log and anomalies

- Site status: 15:21:49 page loaded normally; no body limit message at instrumentation install. UI · DOM ids are the same as in S5. As instructed, the default example was not run.
- Network list: POST 80 (all `/api/evaluate`, 200), GET 58 (1 document, 31 static, 26 Next.js RSC prefetches = 13 paths × 2, all 200). RSC prefetches are requests in which the site fetches the links on the screen in advance; there was no navigation (S5 had 12). resource timing `/api/evaluate` 80 entries = 80 Run clicks, click → fetch start 0\~3 ms.
- Console: 182 warnings (all CSS preload), 0 errors (`raw/console.log`, not included in the public repository).
- Host wall clock: wall − mono offset −1 \~ +1 ms, no steps.
- Clicks without a request: there were only the 80 Run clicks. The 4 no-click dry runs only filled the form and checked hashes · the DOM. For the screenshots, View details was opened without a click by setting `details.open = true` in the DOM.
- The largest gaps come from screenshot time: 22.8 s (run 2) from the run 1 screenshot, 19.0 s (run 42) from the run 41 screenshot, and 18.7 s (run 41) from the part boundary plus the run 40 screenshot.
- During the session, other processes changed `docs/` (00, 09, 10, 11) and `results/F/jev_cmp/__pycache__/s6_summary.cpython-312.pyc`. These are not changes made by this session (`S7_run_card.md` "Anomalies / notes").

## 7. Files

| File | Content |
|---|---|
| `results/F/jev_cmp/sessions/S7_20261008/S7_requests.jsonl` (not included in the public repository) | 80 lines (run = item, no retries). For choice `pred` · `probs` · `top_p` · `shown_pct`, for Boolean `p_true` · `pred`, per run `latency_ms_response` · `displayed_ms` · `fetch_dur_ms` · `click_to_complete_ms` · `usage` · `confidence` · `model_id_details`. `click_epoch_ms` is on the monotonic axis |
| `results/F/jev_cmp/jev_runs_all.jsonl` (not included in the public repository) | master, 491 lines. The first 411 lines (634,031 bytes) are byte-identical to the pre-S7 copy, and the last 80 lines are identical to `S7_requests.jsonl` |
| `raw/rNNN_<T9|T10>_rowRR.json` (not included in the public repository) | 80 per-request dumps |
| `raw/run_plan.json`, `raw/js/`, `raw/dry_runs.json` | plan of the 80 items, instrumentation `instrument.js` (S5 + version tag S7 + session cap 90), per-item input scripts `i001~i080`, the 4 no-click dry runs and their results (`raw/js/` is not included in the public repository) |
| `raw/evaluate_timing_all.json`, `raw/network_requests.txt`, `raw/network_requests_all.txt`, `raw/console.log`, `raw/mcp/` | 80 resource-timing entries and click times (monotonic · wall), network list, console, MCP snapshots (page load, 2 dry-run forms) and MCP console log (none of the five items is included in the public repository) |
| `raw/analyze/` (not included in the public repository) | `T9.md`, `T10.md` (output of `analyze S7 <SET>`) |
| `shots/` | 4 images, the first · last run of each part (View details open, full page, not included in the public repository): `S7_A_item001_run001_T9_row00.png`, `S7_A_item040_run040_T9_row39.png`, `S7_B_item041_run041_T10_row00.png`, `S7_B_item080_run080_T10_row39.png` |
| `s7_prep.py`, `s7_record.py` | generation of the plan · input scripts (asserts agreement with Laya `serialize_state` · `render_options`, T10 `key: description` rendering, T9 noul without criteria, body ≤ 3,000 characters, 0 stop phrases in the inputs), recording wrapper (the same stop-condition classification as S5, rejects stale dumps) |
| `results/F/jev_cmp/jev_cmp.py` | minimal change to read the T9 · T10 Laya reports from `results/T3arm/vanilla/` (`LAYA_DIRS`, `laya_report`). Details in the run card |
| Reproduction | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S7 T9_enron_spam_40`, `… analyze S7 T10_support_tickets_queue_40` |

**English** | [한국어](S7_summary.ko.md)
