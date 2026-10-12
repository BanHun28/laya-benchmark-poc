# 09. Laya vs Jev small-sample comparison plan

**Purpose**: Feed the same state, the same question wording and the same option text to Laya and TypeSafe Jev, and compare accuracy, calibration, robustness, latency and cost under controlled conditions. Upstream could not measure Jev directly and cites only 3rd-party published figures (source: BENCHMARKS.md intro "Jev figures are third-party published, never measured here", research/README.md "On comparisons with Jev"), so this comparison is the core contribution of this benchmark. Language neutrality is the principle (English public datasets first), and multilingual input is covered only as one slice. It is a zero-shot vs zero-shot comparison; Laya fine-tuning (ft-v1) is shown only as a separate line.
**Prerequisite documents**: `00_README.md` (scope, assumptions), `01_laya_analysis.md` (Jev published figures, Honest limits), `03_benchmark_plan.md` §10 Track F (F4 Jev published figures, F5 pilot), `04_korean_evalset_spec.md` (set format, builder conventions), `06_templates.md` (run card). Pilot: `results/F/jev_playground_manual_20261006.md`.
**Outputs**: `data/evals/jev_cmp/*.jsonl` + `*_playground.json` + `MANIFEST.json`, `scripts/build_jev_cmp_sets.py`, playground runner conventions (extending `results/F/jev_f.py`), Laya measurement summary `results/F/jev_cmp/laya_summary.md` (S0), session raw records `results/F/jev_cmp/sessions/S<k>_<date>/`, session run cards `results/F/jev_cmp/S<k>_<date>.md`, master request log `results/F/jev_cmp/jev_runs_all.jsonl` (the session raw records and the master log are not included in the public repository), final comparison summary `results/F/jev_cmp/summary.md` (S6), paper v2 (`docs/10_paper_laya_vs_jev.md` or a revision of `08_paper_ko.md`).

---

## 1. Background and pilot results

Jev is TypeSafe's hosted decision API. Laya's HTTP server provides the same `POST /v1/systemone` protocol as Jev and the same response schema (`choice`/`score`/`noul` answers, probabilities, `usage`) (source: README.md "Self-Hosting: HTTP Server (Jev-compatible)"), so with an API key a fully like-for-like comparison would be possible by sending one request unchanged to both endpoints. This project, however, decided to proceed without an API key (00 §5 item 5), and the only means of access is the public playground https://jevplayground.com, an independent 3rd-party site. The comparison is therefore designed for a small sample at manual speed.

The pilot (2026-10-06, `results/F/jev_playground_manual_20261006.md`) showed the following on 24 Korean domain-routing items.

| System | Correct/24 | Accuracy (Wilson 95%) |
|---|---|---|
| Jev (playground, `key: description` labels) | 20 | 0.833 [0.641, 0.933] |
| Laya zero-shot (multilingual) | 10 | 0.417 [0.245, 0.612] |
| Laya ft-v1 (fine-tuned) | 22 | 0.917 [0.742, 0.977] |

Jev vs zero-shot was significant with b=10, c=0, p=0.002, and Jev vs ft-v1 was not distinguishable with b=0, c=2, p=0.5. Jev's median displayed latency was 249.5 ms (server + network) and the browser round trip about 500 ms, while the local Laya round trip was 20.1 ms (`results/poc/P2_20261003.md`). This pilot covers only one Korean task, which is not enough for a general "Laya vs Jev" conclusion. This plan widens the tasks, centered on English public datasets, and includes multilingual input as one slice.

The 3rd-party Jev figures upstream cites are as follows (source: BENCHMARKS.md §Headline, §On the public datasets where Jev numbers exist, research/scripts/bench_apps.py `JEV_PUBLISHED`): AG News 0.910, Banking77 0.870 (72 labels), DAIR Emotion 0.480 (16% of cases with probability 0 on the gold label), typed-decisions 0.727 (soft 0.580, Brier 0.148, ECE 0.144, score MAE 0.391), ECE 0.246 (nibzard), option-order flip 0.13, p50 236\~276 ms. Whether our Jev sample reproduces these ranges is the criterion for the sample-representativeness check.

---

## 2. Jev access constraints and operating rules

Constraints observed on the playground (viewed 2026-10-02 and 10-06): "Free to try · Usage limits apply", intermittent backend 502s ("Jev is temporarily unavailable"), at most 10 choices, state of 8,000 characters, Single question / Multiple questions modes, output probabilities rounded to two decimal places (100%/0% are common), "View details" showing Model ID `typesafe-ai/jev` (no version), input/output tokens and a separate confidence, and the on-screen "N ms · server + network" is shorter than the browser round trip (pilot: displayed 249.5 ms vs POST 497.5 ms). In addition, **each choice input field is limited to 80 characters** (`results/F/jev_playground_manual_20261006.md:34`, `scripts/build_jev_cmp_sets.py:44` `CHOICE_INPUT_CHARS = 80`).

Decision on the 80-character limit (2026-10-06, after the S0 report): (1) T4 Banking77-10 dropped the v0 `key: key spaced` rendering (up to 98 characters; 8/40 items could not be entered) and was rebuilt **for both systems** with upstream's key-only rendering (`k.replace("_", " ")`, up to 48 characters, bench_apps.py:120-122). v0 is kept as `T4_banking77_10opt_40_v0.jsonl`, and `options_rendering: key-only`, `rebuild_reason` and `previous_version` are recorded in the MANIFEST (`data/evals/jev_cmp/MANIFEST.json`). (2) In T1 typed-decisions, the options of 10 customer_service/action decisions are 87\~89 characters and cannot be entered into Jev with the same bytes, so those 10 were marked `jev_excluded: true, reason: "option > 80 chars"` (in the `jev` metadata of the JSONL rows and in the form items, `build_jev_cmp_sets.py:45, :147`), and the plan was to compare Jev on the remaining 190 decisions; but S1 then confirmed the Score constraint below, so 70 4-level score questions were excluded as well (reason `score levels != 5`). The final **Jev comparison set is 120 decisions** (choice 50, noul 60, 5-level score 10), and the MANIFEST's `jev_comparable_n` is the per-task number compared (T1 120, all n for the others; the two rules are recorded in `jev_exclusion_rule`). Laya figures are also reported on the 120 basis (`results/F/jev_cmp/laya_summary.md` §2).

Multiple questions mode check (S1 2026-10-06, `results/F/jev_cmp/sessions/S1_20261006/multi_question_mode.md`): (1) One run can hold 2\~5 questions, Choice, Boolean and Score can be mixed, and they share one State. The results come out as one card per question (DECISION or SCORE, probability distribution), and "N ms · server + network" is one per run. (2) **Score accepts exactly 5 levels.** Entering 4 levels blocks the request itself with the error "Enter a label.", and Single mode uses the same validation. 70 of the 80 T1 score questions have 4 levels, so the same input cannot be sent in either mode. (3) **Boolean has no label or description fields.** Laya's noul `criteria` (true/false descriptions) do not reach Jev. As a fairness check, a Laya variant without criteria was measured, and noul accuracy did not change significantly (english 0.467 → 0.517, McNemar p=0.549; multilingual 0.433 → 0.417, p=1.0; `laya_summary.md` §2b). (4) choice labels and rubric levels are **truncated at 80 characters without an error**, so a different label is sent. (5) The request format is `{"state", "questions": {"q1": {"instructions", "type", "criteria"}}}`, with choice as `{label: label}`, score as 5 strings and boolean without criteria. (6) The Score shown on screen is the level closest to E[level], so it can differ from the argmax (Jev's per-item outputs are omitted in the public repository). The T1·T6 score rule is therefore fixed as **argmax level accuracy + MAE based on E[level]**.

Operating rules (applied to every session; the number of requests is recorded in the run card):

| Item | Rule |
|---|---|
| Speed | Human speed. Gap between requests of 10 s or more recommended, 3 s minimum |
| Volume | On day 1 and in S2, at most 80 requests per session and at most 100 requests per day. By owner decision on 2026-10-07 the daily cap was lifted, and thereafter at most 100 requests per session (S5 had a hard cap of 110 to leave room for retries). No automated bulk calls |
| Errors | Stop immediately on a 5xx, a limit message or a captcha. Retry only that item, 1 time, after 60 s; if the retry also fails, end the session |
| Records | Per request: input-hash check, DOM/accessibility snapshot, "View details" capture (snapshots, captures and the per-request records are not included in the public repository), displayed latency and browser round trip, Model ID and tokens |
| Disclosure | When sharing results, always state "via an independent playground, not the API, model version not shown, small sample" |
| Duplicates | Resending the same item is allowed only for the determinism check (§5), up to 10 items |

These rules were set based on how the pilot ran (25 requests, minimum gap 21.6 s, 1 HTTP 502, 0 retries) (`results/F/F_jev_20261006.md`).

**Daily cap lifted (2026-10-07, owner decision).** The site does not publish numeric limits (home page "Free to try · Usage limits apply", privacy page "abuse protection and rate limits"). Over the 178 requests before the cap was lifted, 429s and limit messages occurred 0 times. The rules stayed as they were: gap ≥ 10 s (actual guard 15 s, monotonic), on a 5xx 1 retry of only that item after 60 s, and on a 429 or limit message an immediate session stop without retrying. After the cap was lifted, over the 340 requests of 2026-10-07, including the 260 of S3\~S5, no 429, limit message or captcha appeared (§7.1c).

---

## 3. Tasks and samples

Because of the 10-option limit, upstream's Banking77 (77 labels) and MASSIVE 20-option constructions cannot be used as they are. Every task is cut to 10 options or fewer, and Laya gets the same options. The default is n=40 per task. The n below are the actual values built in S0 (`data/evals/jev_cmp/MANIFEST.json`, including source revisions). The Jev run counts assume that T1 is run 1 time per case in Multiple questions mode.

| Task | Source (public test split) | Type / options | n | Jev runs | Published figures to compare | upstream training mix |
|---|---|---|---|---|---|---|
| T1 typed-decisions | `LocalLLaMA/typed-decisions` all/test @d0e2f0c (parquet, `load_dataset` works directly; source: research/scripts/build_benchmark_nb.py:329) | mixed (choice·score·noul), up to 5 options per case | 40 cases / 200 decisions, **Jev comparison 120** (choice 50, noul 60, 5-level score 10; excluded 80 = 4-level score 70 + over 80 characters 10, §2) | 39 (plan A: Multiple questions mode, 1 time per case, 4-level score questions omitted; row 30 completed by the S1 exploration run) | Jev 0.727 / soft 0.580 / Brier 0.148 / ECE 0.144 / MAE 0.391; Laya base 0.362/0.352, ft 0.766 | not included ("Neither checkpoint trained on typed-decisions", research/results/t4_colab_benchmark.json) |
| T2 AG News | `fancyzhx/ag_news` test @eb185aa | choice 4 | 40 (10×4) | 40 (+20 permutation probe) | Jev 0.910, Laya 0.947\~0.953 | in training (README.md:1348-1356) |
| T3 DAIR Emotion | `dair-ai/emotion` split/test @cab853a | choice 6 | 40 (7,7,7,7,6,6) | 40 | Jev 0.480, Laya 0.573\~0.600 | held out (README.md:1354) |
| T4 Banking77-10 | `mteb/banking77` test @18072d2, gold + 9 distractors (seed 13), options in key-only rendering (§2 decision (b)) | choice 10 | 40 (40 distinct gold labels) | 40 | Not directly comparable (Jev 0.870 is on 72 labels, Laya 0.425 on 77 labels). The 10-option condition is a new measurement for both | held out (bench_apps.py `in_training=False`, build_benchmark_nb.py:761) |
| T5 BoolQ | `google/boolq` validation @35b264d (test labels not public) | noul (Boolean) | 40 (20/20) | 40 | Laya 0.830/0.787. No Jev published figure | in training (README.md:1348-1356) |
| T6 SST-5 | `SetFit/sst5` test @e51bdcd | score 5 levels | 40 (8×5) | 40 | Laya 0.372/0.282 (exact level). No Jev published figure | held out |
| T7 MASSIVE intent-10 multilingual | `mteb/amazon_massive_intent` en·de·ja·zh-CN·ko test @940fd47, same ids, gold + 9 (seed 13) | choice 10 | 20 × 5 = 100 | 100 | The number of options differs from the 20-option upstream figures (multilingual ko 0.470 / en 0.710, english en 0.820; BENCHMARKS.md:71, :117), so only the direction is compared | held out (build_benchmark_nb.py:762 "Neither checkpoint trained on typed-decisions, MASSIVE or XNLI") |
| T8 prompt-injections (optional) | `deepset/prompt-injections` test @4f61ecb (source: README.md "English tasks", n=116 held out) | noul | 40 (20/20) | 40 | Laya 0.698/0.578 | held out |

Total: T1\~T7 = 39 + 40 + 40 + 40 + 40 + 40 + 100 = 339 requests; adding the 20 permutation probes and 10 determinism checks gives 369 (71 of them done in S1·S1b). Adding T8 gives 409, split over 5\~6 days under the cap of 100 per day. The evidence for the training-mix labels is not the Themes table of BENCHMARKS.md but README.md:1348-1356 (in training / held out in the "English tasks" table) and research/scripts/build_benchmark_nb.py:760-762.

Sampling follows the common rules of 04 §5: seed 13, label stratification (quota + the remainder to the first labels), exact-duplicate removal, a 2\~2,000-character length filter, deterministic build and sha256 recording. T7 draws the same MASSIVE ids in 5 languages to keep cross-language pairs (the id join of `results/korean_support/K2_build.py`). typed-decisions is sampled by case, and all questions in a case are used.

Caution: T2·T5 are sources upstream labels "in training mix", so they may favor Laya. T4 is held out, and neither checkpoint trained on T7 (MASSIVE) (build_benchmark_nb.py:760-762). This is passed on as it is in the tables, and these tasks are interpreted separately from the held-out tasks (T1, T3, T4, T6, T7, T8).

---

## 4. Protocol parity

Both systems receive byte-for-byte the same information.

| Element | Laya | Jev playground | How parity is ensured |
|---|---|---|---|
| state | The dict state as upstream renders it (e.g. `{"text": ...}`); the model reads the JSON-serialized string | That JSON-serialized string (`state_text`) is entered as it is in the State textarea | Byte-identical. The `state_text` of the form file is the string Laya actually reads (`scripts/build_jev_cmp_sets.py:176` `playground`) |
| Question wording | upstream's original `instructions` as they are (bench_apps.py: AG News·Emotion·Banking77, build_benchmark_nb.py:414-490: BoolQ·SST-5·prompt-injections, bench_local.py:173-180: MASSIVE) | The same sentence in the Question field | The same English sentence. Backtick field references (e.g. `utterance`) are kept as well; the state is the same JSON string, so both systems see the same field names |
| choice options | `criteria` dict `{key: description}` → the model reads `key: description` (source: README.md "Honest limits", laya/common.py render_options) | 1 label-text field × up to 10 | The `key: description` string goes into the Jev label as it is (same as the pilot) |
| noul | `type: noul` (+ criteria true/false if needed) | Decision type Boolean | Same question wording. Laya criteria are not added, following the upstream preset convention (04 §3) |
| score | `criteria` list of level descriptions; the answer is the expected level (a real number) | Decision type Score; whether level descriptions can be entered is to be verified | Check the Jev score output format (integer level or distribution) in S1 and fix the comparison rule |
| Option order | Fixed | Fixed | Same order. The permutation probe covers only 20 items on T2 (k=1) |
| Multiple questions | One call = several question rows | Multiple questions mode | Used for T1 only. If the mode does not support mixed types or the number of questions, run per question in Single mode (5 times the requests, budget readjusted) |

Laya measurements cost nothing per request, so all of them run locally: `laya-evals run` (CPU fp32 as the reference; the english checkpoint for English tasks, both english and multilingual per language for T7, with Router auto alongside), and latency cites the Track D values (`results/D/D_summary_20261003.md`) and the laya-serve local HTTP round trip. ft-v1 is kept as a reference line only on the ko slice of T7 (marked as not a direct comparison, since this is an intent task, not a domain task).

Jev measurement extends the pilot runner (`results/F/jev_f.py`: sample / record / record_error / analyze). It keeps the input-hash check before each request, saving the DOM and snapshot after each request, the "View details" capture, recording the displayed latency and the browser POST time, and recording the attempt number.

### 4.1 Per-task question wording and option rendering

The strings that go into both systems are fixed at set-build time and frozen with `questions_sha256` (source: docs/evals.md "Run identity"). The wording is upstream's original as it is. That way the Laya figures can be read on the same scale as upstream's published figures, and since Jev gets the same JSON-serialized state that Laya reads, both systems see the same thing even when there are backtick field references (S0 decision, `results/F/jev_cmp/S0_20261006.md`).

| Task | Question wording and state (identical for both systems, upstream original) | Laya criteria | Jev labels (up to 10, each at most 80 characters) |
|---|---|---|---|
| T1 | The dataset's original questions, options and state as they are (same as upstream Part B) | Original criteria | `key: description`. There were 0 cases with more than 10 options, and the 10 decisions with options over 80 characters are `jev_excluded` (§2) |
| T2 | The AG News question and dict state of bench_apps.py | upstream label descriptions | 4 `key: description` |
| T3 | The Emotion question and dict state of bench_apps.py | upstream label descriptions | 6 `key: description` |
| T4 | The Banking77 question and dict state of bench_apps.py | gold + 9 distractors, key-only rendering `{k.replace("_"," "): None}` (bench_apps.py:120-122) | 10 key-only (up to 48 characters) |
| T5 | The BoolQ question of build_benchmark_nb.py:414-490, state = passage + question dict | noul, no criteria | Boolean |
| T6 | The SST-5 question of build_benchmark_nb.py:414-490 | 5 level descriptions | Score; settled in S1 depending on whether level descriptions can be entered |
| T7 | bench_local.py:173-180 "What is the user asking for in `utterance`?", state `{"utterance": text}` | gold + 9 distractors, rendering `k.replace("_"," ").replace(".", ": ")` (`render_key`) | 10 key renderings |
| T8 | The prompt-injections question of build_benchmark_nb.py:414-490 | noul | Boolean |

The descriptions for T2·T3·T7 are written in English (the task language is English, or upstream convention), and the English key rendering is kept as it is for T7's non-English utterances. This choice matches upstream's MASSIVE construction (source: research/scripts/bench_local.py:165-183), and the observation of 07 §5 that Korean descriptions helped is reflected by labeling the multilingual slice as the "English-options condition". T1's Score questions remain possibly excluded from Multiple questions mode until the Jev Score format is confirmed.

### 4.2 Jev input conversion rules

`scripts/build_jev_cmp_sets.py` also writes, for each set, the playground input form `data/evals/jev_cmp/<set>_playground.json` (`playground` :176). The item schema is `{"id", "state_text" (the JSON-serialized string Laya reads), "question", "decision_type": "choice"|"boolean"|"score", "options": ["key: description" or key only, ...] (≤ 10, each ≤ 80 characters), "gold", optionally "jev_excluded": true, "reason"}`. The runner enters `state_text` and `options` as they are, checks the input hash before the request, verifies that the DECISION string of the response exactly equals one of the `options`, and maps it back to the key before ":" (or the key alone). If it does not match, the row is recorded as a "parse failure" and excluded from the correct/incorrect verdict. `jev_excluded` items are not sent to Jev.

---

## 5. Metrics

| Metric | Definition | Notes |
|---|---|---|
| accuracy | argmax agreement rate, Wilson 95% CI | Per task, per system |
| macro-F1 | Over the classes in gold∪pred | choice tasks |
| Brier | Mean of the per-option sum of (p − y)² | Jev probabilities are rounded to 2 digits, so state a minimum error of ±0.005 |
| ECE | 15 bins, on the probability of the chosen answer | For Jev, rounding makes the bins sparse, so it is a reference metric |
| coverage@error | Maximum coverage at error ≤ 5% and ≤ 10% | Both systems sorted by top probability |
| Agreement · McNemar | Paired comparison of the two systems' correctness on the same items, exact McNemar | Main test |
| Option-order flip | T2, 20 items, 1 permutation | Directional signal from a small sample. Jev published 0.13, Laya en 20-option 0.150/0.230 |
| Determinism | argmax and probability agreement over 10 items, each sent 2 times | Jev presumed generative (output about 255 tokens, pilot) |
| Failure modes | Jev: gold probability 0%, "Unable to evaluate", 502. Laya: 422/413, empty answer | Counts |
| Latency | Jev displayed value and browser POST; Laya in-process (D1) and laya-serve round trip (D6, P2) | Hosted vs local, so state in the table whether the network is included |
| Cost | Jev: published unit price × tokens (check the price at run time; pilot input about 716 and output about 255 tokens). Laya: hardware and power estimate | Per 1k decisions |
| Multilingual penalty | T7 accuracy per language, Δ vs en | 20 per language, so a directional signal |

T1 follows upstream's Part B definitions: argmax accuracy, soft accuracy (against the teacher distribution), Brier, ECE, score MAE (source: research/scripts/bench_local.py Part B `metrics`).

---

## 6. Statistical limitations

- At n=40 the 95% CI is about ±0.15. A significant verdict is possible only when the two systems differ by 0.2 or more. Smaller differences are reported as "not distinguishable".
- T1 has 200 decisions, so about ±0.07, and T7 has 20 per language, so close to ±0.2. T7 is used only as a directional signal.
- The paired comparison (McNemar) has power only when the two systems err on different items. If, as in the pilot, one side's correct answers include all of the other's, b or c becomes 0 and p stays at 0.5 or above.
- Representativeness check: check whether the AG News, Emotion and typed-decisions accuracy of our Jev sample lies within the CI of the published Jev figures (0.910, 0.480, 0.727). If not, suspect sample bias or a model-version change and write the conclusions conservatively.
- The playground is not the API. Prompt wrapping or the model version may differ from the API, and the version is not shown. Model ID and token counts are recorded per session to track variation between sessions.

---

## 7. Execution order [step → verification]

| Step | Content | Jev requests | Verification |
|---|---|---|---|
| S0 harness and sets (done 2026-10-06) | 12 T1\~T8 sets + forms generated with `scripts/build_jev_cmp_sets.py` (deterministic, validate, MANIFEST), 38 full Laya measurement runs + permutation probe (laya-evals, CPU fp32), including the T4 key-only rebuild and remeasurement (8 runs) | 0 | 12 sets pass validate, offline rebuild byte-identical, `results/F/jev_cmp/S0_20261006.md`, `laya_summary.md` |
| S1 exploration + T2 (done 2026-10-06) | Multiple questions mode check (1 exploration run, T1 row 30); T1 could not be loaded as it is, so per the rules switched to T2 AG News 40 | 41 (all 200) | `sessions/S1_20261006/multi_question_mode.md`, `S1_summary.md`; §7.1 |
| S1b determinism + permutation (done 2026-10-06) | Resend 10 T2 rows; option permutation on 20 T2 rows (the same permutation as the Laya probe) | 30 (all 200) | `sessions/S1b_20261006/S1b_summary.md`; §7.1 |
| S2 | T1-A 39 cases (Multiple questions, 4-level score omitted) + T3 Emotion 40 | 79 | 120 decisions recorded, compared with the published Jev figures (T1 0.727, T3 0.480) |
| S3 | T4 Banking77-10 40, T5 BoolQ 40 | 80 | New measurement of the 10-option condition for both sides |
| S4 | T6 SST-5 40, T7 en·de 40 | 80 | Apply the score rule (argmax + E[level] MAE) |
| S5 | T7 ja·zh-CN·ko 60 (+ T8 40 if within budget; otherwise day 6) | 60\~100 | Per-language table |
| S6 analysis and report | `results/F/jev_cmp/summary.md` (combining the Laya-side `laya_summary.md` and the Jev session records `jev_runs_all.jsonl`), collecting the session run cards, updating dashboard Track F, paper v2 (title "Laya vs Jev", with the Korean study as a case study and appendix) | 0 | Figures agree across REPORT, dashboard and paper |
| S7 (done 2026-10-08, 3-arm extension) | T9 Enron spam 40 + T10 customer-support ticket queue 40 (the Jev arm of `11_three_arm_plan.md`, approved by the project owner 2026-10-08) | 80 (all 200) | `sessions/S7_20261008/S7_summary.md`, `S7_run_card.md`; §7.1d |

Sessions are spread over 4\~6 days at no more than 100 requests per day. Before each session the site status is checked 1 time, and if 502s repeat during a session, work stops for that day.

### 7.0 S0 results (2026-10-06, `results/F/jev_cmp/laya_summary.md`, `S0_20261006.md`)

Laya-side measurements (CPU fp32, intra-op 10 / inter-op 1, Wilson 95% CI, CI width about ±0.15 at n=40). The parentheses in the Router column give the routed checkpoint.

| Task | english | multilingual | Router | upstream published (english / multilingual) |
|---|---|---|---|---|
| T1 typed-decisions, Jev comparison 120 decisions (choice 50 / noul 60 / 5-level score 10) | 0.383 [0.301, 0.473] (choice 0.280, noul 0.467, score 0.400; soft 0.361, Brier 0.333) | 0.367 [0.286, 0.456] (choice 0.320, noul 0.433, score 0.200) | 0.383 (all english) | 0.362 / 0.352 (on 200: 0.330 / 0.305; on 190: 0.347 / 0.311). Per-question majority baseline over the 120: 0.575 |
| T1 typed-decisions checkpoint (fine-tuned, not zero-shot) | 0.867 [0.794, 0.916] (choice 0.800, noul 0.950, score 0.700; soft 0.519 / Brier 0.059; on 200 0.795, on 190 0.811) | - | - | 0.766 (soft 0.471 / Brier 0.061 / MAE 0.242) |
| T2 AG News | 0.975 | 0.925 | 0.975 | 0.947 / 0.950 (Jev 3rd-party 0.910) |
| T3 Emotion | 0.750 [0.598, 0.858] | 0.625 | 0.750 | 0.573 / 0.595 (Jev 3rd-party 0.480) |
| T4 Banking77-10 (key-only) | 0.725 | 0.750 | 0.725 | not comparable (77 options, 0.425) |
| T5 BoolQ | 0.725 | 0.600 | 0.725 | 0.830 / 0.787 |
| T6 SST-5 (argmax level, MAE) | 0.425 (0.888) | 0.325 (1.419) | 0.425 | 0.372 / 0.282 |
| T7 MASSIVE-10 en / de / ja / zh-CN / ko | .70 / .35 / .45 / .45 / .10 | .85 / .40 / .80 / .60 / .45 | .70 / .35 / .80 / .60 / .45 | on 20 options: en 0.820 / 0.710, ko 0.110 / 0.470 |
| T8 prompt-injections | 0.775 | 0.575 | 0.725 (english 26 / multilingual 14 rows) | 0.698 / 0.578 |

- **T4 rendering effect** (same 40 rows, same option set, same order, v0 `key: key spaced` vs key-only; `laya_summary.md` §4b): english 0.825 → 0.725 (correct only with v0: 4 / only with key-only: 0, McNemar p=0.125), multilingual 0.575 → 0.750 (0 / 7, p=0.016). The option-text rendering alone moves accuracy a lot, so giving Jev the same rendering is a premise of the comparison.
- **The T3 sample came out on the easy side for Laya english.** Running the upstream setting (first 600 test rows, same question) through the same pipeline gives 0.5733 / ECE 0.3237, the same as the published 0.5733 / 0.3238 (`research/results/t4_colab_benchmark.json` en.emotion). Our 40 rows drawn with seed 13 give 0.750. They can be used for the paired comparison with Jev, but must not be generalized by comparing them with the published figures.
- **The 80 excluded from T1**: 10 customer_service/action (choice) questions (options of 87\~89 characters; english gets all of them wrong) and 70 4-level score questions (the playground's 5-level Score constraint). This is why the accuracy on the 120 basis (0.383) is higher than on the 200 basis (0.330). For the variant with and without noul criteria (`T1_typed_decisions_40_noulnocrit.jsonl`), see §2.
- Determinism: T1 english, 2 runs, 200 decisions identical. Option-order probe (T2, 1 permutation, 40 rows): flip 0.000 (english·multilingual).

### 7.1 S1·S1b results (2026-10-06, `results/F/jev_cmp/sessions/S1_20261006/S1_summary.md`, `sessions/S1b_20261006/S1b_summary.md`)

**S1**: 41 requests (1 exploration + T2 40), all HTTP 200, 5xx·429·captcha 0, retries 0. For all 41, the body actually sent was byte-identical to the form payload. T1 could not be loaded as it is into Multiple questions mode because of the 5-level Score constraint (§2), so per the rules the session switched to T2.

| System (T2 AG News, same 40 rows) | Correct/n | Accuracy | Wilson 95% |
|---|---|---|---|
| Jev (playground) | 35/40 | 0.875 | [0.739, 0.945] |
| Laya english | 39/40 | 0.975 | [0.871, 0.996] |
| Laya multilingual | 37/40 | 0.925 | [0.801, 0.974] |
| Laya Router (all 40 to english) | 39/40 | 0.975 | [0.871, 0.996] |

- McNemar: Jev vs english, same label 36, b=0 / c=4, p=0.125; Jev vs multilingual, same label 38, b=0 / c=2, p=0.5. The direction is one-sided (Laya right, Jev wrong), but not significant at n=40 (with b=0, c ≥ 6 is needed for p < 0.05).
- Jev confidence: 100% displayed 29/40, 0% cells 109/160. Mean top 98.5% on correct answers and 92.2% on wrong answers; 4 of the 5 wrong answers are at 93% or above, so a 90% threshold does not filter them out. Brier 0.220 (Laya english 0.053). In the pilot (24 Korean rows) all wrong answers were below 90%, so the calibration pattern differs by task.
- All 5 Jev errors are on the business/world side and are sci_tech/world/business boundary cases (for 1 of them the gold label itself is doubtful). This cannot be separated from T2 being in Laya's training mix.
- Latency: displayed median 234 ms (188\~448), matching the rounded response `latencyMs` 41/41. Browser POST 468 ms (415\~749). Laya local reference: P2 round trip 20.1 ms, D1 english CPU 1 question 86.6 ms, MPS 31.8 ms (different hardware and path, so not a model-speed comparison). Median tokens: input 425 / output 68.
- Representativeness: Jev 0.875 lies within the CI of the published 0.910, and Laya english 0.975 within the CI of upstream's 0.947/0.950.

**S1b**: all 30 requests 200, minimum gap 17.3 s. (1) Determinism (10 T2 rows resent with the same payload 16\~23 min later (median 20 min), per the request records, `results/F/jev_cmp/summary.md` §6): labels agree 10/10, probability vectors 9/10 (max |Δp| 0.01), View details confidence 9/10, tokens 10/10, latencyMs median 221 → 233 ms. Effectively deterministic, but not bit-for-bit identical. (2) Option-order flip (20 T2 rows, the same permutation as the Laya probe): Jev 0/20 [0, 0.161], Laya english 0/20, multilingual 0/20. The published 0.13 cannot be ruled out (at a flip rate of 0.13, the probability of 0/20 is 0.062). With 4 options and a high-confidence sample (100% displayed 13/20) the information content is low; order sensitivity is examined again in T3·T4·T7. (3) Day 1 usage: pilot 25 + checks 2 + S1 41 + S1b 30 = 98/100.

### 7.1b S2 results (2026-10-07, `results/F/jev_cmp/sessions/S2_20261007/S2_summary.md`, `S2_run_card.md`)

**Requests and progress**: 80 requests. Part A (T1) 40 = 39 successes + 1 HTTP 502 (run 1, "Jev is temporarily unavailable.", retried 1 time with the same payload 73.7 s later and succeeded); Part B (T3) all 40 succeeded. After that, 5xx·429·limit messages·captcha were 0. Gaps: minimum 12.1 s, median 15.1 s (monotonic; all 79 gaps 10 s or more). The pre-request sha12 check and the post-request body byte check agreed 80/80, and Model ID was `typesafe-ai/jev` 79/79. T1 row 30 was not resent; the S1 exploration run was reused (sha12 `5a9e5492744b` matches the plan-A payload). Each case has 2\~4 comparable questions, so all were sent in Multiple questions mode. Day 2 usage is 80/100 (`S2_run_card.md`).

**T1 typed-decisions, the same 120 decisions (S2 39 runs + S1 row 30)**

| System | Overall | choice 50 | noul 60 | score 10 (argmax) | soft acc | Brier (vs soft) | ECE | score MAE (5 levels, 10 questions) |
|---|---|---|---|---|---|---|---|---|
| Jev (playground) | 104/120 = 0.867 [0.794, 0.916] | 42/50 | 56/60 | 6/10 | 0.590 | 0.077 | 0.181 | 0.389 |
| Laya english | 46/120 = 0.383 [0.301, 0.473] | 14/50 | 28/60 | 4/10 | 0.361 | 0.333 | 0.205 | 0.584 |
| Laya multilingual | 44/120 = 0.367 [0.286, 0.456] | 16/50 | 26/60 | 2/10 | 0.351 | 0.574 | 0.391 | 0.671 |
| Laya Router (all 120 to english) | same as english | | | | | | | |
| Reference: Laya typed-decisions (fine-tuned on this benchmark's train split, not zero-shot) | 104/120 = 0.867 | 40/50 | 57/60 | 7/10 | 0.519 | 0.059 | 0.279 | 0.255 |
| Per-question majority baseline | 0.575 | | | | | | | |

- Exact McNemar (b = only Jev correct, c = only Laya correct): Jev vs Laya english (= Router) 66/8, p < 0.0001 (choice 31/3, noul 31/3, score 4/2 p 0.69). Jev vs multilingual 66/6 (choice 27/1, noul 33/3, score 6/2 p 0.29). Jev vs the fine-tuned checkpoint 10/10, p 1.0.
- Same-input noul comparison: Jev Boolean receives no descriptions, so it is compared with the Laya variant without criteria. Jev 56/60 = 0.933 [0.841, 0.974], Laya english without descriptions 31/60 = 0.517 (b/c 27/2, p < 0.0001), multilingual without descriptions 25/60 = 0.417 (b/c 34/3). Laya with descriptions also scores only 28/60 and 26/60, so the gap is not explained by the description asymmetry.
- By workflow (Jev / Laya english): agent_trace 25/30 vs 14/30, customer_service 19/20 vs 11/20, invoice 29/30 vs 4/30 (Laya base 0/10 on the duplicate questions), security 31/40 vs 17/40.
- Comparison with published figures (context only): the published Jev 0.727 / soft 0.580 / Brier 0.148 / MAE 0.391 are on 2,000 decisions with a different question mix. By the same subset effect, Laya english also rises from 0.330 (on 200) to 0.383 (on 120).

**T3 DAIR Emotion, the same 40 rows**

| System | Correct/40 | Accuracy [Wilson 95%] | Brier | ECE | McNemar vs Jev (b/c, p) |
|---|---|---|---|---|---|
| Jev (playground) | 28 | 0.700 [0.546, 0.819] | 0.537 | 0.278 | - |
| Laya english | 30 | 0.750 [0.598, 0.858] | 0.429 | 0.174 | 2/4, p 0.6875 |
| Laya multilingual | 25 | 0.625 [0.470, 0.758] | 0.631 | 0.313 | 6/3, p 0.508 |
| Laya Router (all english) | 30 | 0.750 | 0.429 | 0.174 | 2/4, p 0.6875 |

- Correct per class (Jev / Laya english): sadness 7/6, joy 5/7, love 3/3, anger 5/6, fear 5/4, surprise 3/4. Jev's errors are 3 love → joy and 4 that went to sadness, and 7 rows are wrong for all three systems.
- Easy-sample caution: this seed-13 sample is easy for both systems. The CI of Jev's 0.700 does not contain the published 0.480, and Laya english's 0.750 is also above upstream's 0.573. It is used only for the paired comparison and is not generalized by comparison with the published figures.

**Calibration and confidence**
- On T1, Jev is underconfident. The mean top p of 0.733 is below the accuracy of 0.867 (correct 0.758, wrong 0.569), and of the 16 wrong answers only 1, a score answer, has top ≥ 0.90. The 4 wrong noul answers had p(true) 0.39\~0.54, and the provider confidence points the same way (correct 0.711 / wrong 0.454). There is room to hold back Jev's wrong answers with a threshold.
- On T3, Jev is overconfident. 100% displayed 15/40, 7 of the 12 wrong answers are at 90% or above, and the rows where the gold option is displayed as 0% are 7/40 (17.5%), close to the published zero-probability failure rate of 16%. Mean top p is 0.918 on correct and 0.861 on wrong answers.
- So the meaning of Jev's probabilities depends on the task format. In T1, under Multiple questions, wrong answers have low confidence, while in the single-choice T2·T3 most wrong answers are displayed at 90\~100%.

**Latency and tokens**
- T1 (2\~4 questions per request): displayed latency median 226 ms (164\~355); displayed latency per question 111 ms with 2 questions, 75 ms with 3, 60 ms with 4. Browser POST 481 ms, median tokens input 760 / output 141.
- T3: displayed latency median 241 ms (170\~713), POST 469 ms, tokens 387.5 / 61.
- Common: the displayed value matches the rounded `latencyMs` 79/79, POST − latencyMs median 235.6 ms, total tokens input 45,616 / output 8,806.

**Limitations and caveats**
- Via the playground, not the API; the model version is not shown; the sample is small.
- The T1 gold label is the argmax of the dataset's teacher distribution. The identity of the teacher and its relation to Jev are unknown (to be verified). The task may favor models similar to the teacher, and the fact that Jev zero-shot scored the same 104/120 as the Laya fine-tuned on this benchmark's train split has to be read in this context (open question 10).
- On T1, Jev evaluated the 2\~4 questions of a case together in one request, while Laya evaluated each question as a separate row. The effect of this difference could not be separated.
- Measurement anomaly: between runs 60 and 61 the host wall clock stepped by +1.98 s, so the dump matching for run 61 timed out (1 actual request, HTTP 200). The dump and the gap guard were switched to monotonic time and the run was re-recorded, with no extra request (`S2_run_card.md`; the timeout dump is `raw/r61_T3_row20_timedout_dump1.json`, not included in the public repository).

### 7.1c S3·S4·S5 results (2026-10-07, `results/F/jev_cmp/sessions/S3_20261007/S3_summary.md`, `S4_20261007/S4_summary.md`, `S5_20261007/S5_summary.md`)

**Operations**: after the daily cap was lifted (§2), the three sessions were run back to back. Requests: S3 80, S4 80, S5 100, all HTTP 200, retries 0, 5xx·429·limit messages·captcha 0. Gaps (monotonic): minimum 15.013 s, per-session median 15.114\~15.125 s. The pre-request payload hash and the post-request body byte check agreed 260/260, and Model ID was `typesafe-ai/jev` 260/260. Up to the last request of that day's cumulative 340 (including S2's 80) there was no limit signal (`S5_run_card.md:51`). The figures are the same as in the S6 synthesis (`results/F/jev_cmp/summary.md` §2).

**T4 Banking77-10 (key-only options, S3, the same 40 rows)**

| System | Accuracy [Wilson 95%] | Brier | ECE | McNemar vs Jev (b/c, p) |
|---|---|---|---|---|
| Jev | 37/40 = 0.925 [0.801, 0.974] | 0.114 | 0.069 | - |
| Laya english (= Router) | 29/40 = 0.725 [0.572, 0.839] | 0.349 | 0.150 | 9/1, 0.0215 |
| Laya multilingual | 30/40 = 0.750 [0.598, 0.858] | 0.478 | 0.262 | 8/1, 0.0391 |

- For 2 of Jev's 3 errors, the three Laya runners were also wrong with the same label. Jev 100% displayed 31/40; among the errors, top ≥ 0.90 in 1/3.

**T5 BoolQ (S3, gold true 20/40)**

| System | Accuracy (p(true) ≥ 0.5) | Predicted true | AUROC [bootstrap 95%] | Brier | McNemar vs Jev (b/c, p) |
|---|---|---|---|---|---|
| Jev | 37/40 = 0.925 [0.801, 0.974] | 21 | 0.988 [0.955, 1.000] | 0.098 | - |
| Laya english (= Router) | 29/40 = 0.725 [0.572, 0.839] | 19 | 0.810 [0.662, 0.942] | 0.393 | 9/1, 0.0215 |
| Laya multilingual | 24/40 = 0.600 [0.446, 0.737] | 18 | 0.682 [0.496, 0.838] | 0.615 | 15/2, 0.0023 |

- The AUROC difference Jev − english is +0.177 [+0.043, +0.326], so this is a difference in ranking quality, not in the threshold. Jev Boolean displayed 100% 0/40, and all 3 errors had top < 0.80.

**T6 SST-5 (S4, 5 levels, 8 gold per level)**

| System | argmax accuracy (main metric) | Rounded E[level] accuracy | MAE of E[level] | Brier | McNemar vs Jev: argmax / rounded E (b/c, p) |
|---|---|---|---|---|---|
| Jev | 26/40 = 0.650 [0.495, 0.779] | 27/40 = 0.675 | 0.432 | 0.502 | - |
| Laya english (= Router) | 17/40 = 0.425 [0.285, 0.578] | 16/40 = 0.400 | 0.888 | 0.770 | 15/6, 0.0784 / 15/4, 0.0192 |
| Laya multilingual | 13/40 = 0.325 [0.201, 0.480] | 13/40 = 0.325 | 1.419 | 1.149 | 18/5, 0.0106 / 19/5, 0.0066 |

- MAE difference Jev − english −0.456 [−0.711, −0.207]. Laya english output level 4 in 0/40 rows, and multilingual put 40/40 rows at levels 0·1 (scale compression). multilingual's avoidance of the first level (#131) did not appear in this sample.

**T7 MASSIVE intent-10 (S4 en·de, S5 ja·zh-CN·ko, the same 20 ids)**

| System | en | de | ja | zh-CN | ko | Pooled 100 |
|---|---|---|---|---|---|---|
| Jev | 0.900 | 0.900 | 0.950 | 0.900 | 0.900 | 91/100 = 0.910 [0.838, 0.952] |
| Laya english | 0.700 | 0.350 | 0.450 | 0.450 | 0.100 | 41/100 = 0.410 [0.319, 0.508] |
| Laya multilingual | 0.850 | 0.400 | 0.800 | 0.600 | 0.450 | 62/100 = 0.620 [0.522, 0.709] |
| Laya Router | 0.700 | 0.350 | 0.800 | 0.600 | 0.450 | 58/100 = 0.580 [0.482, 0.672] |
| Jev vs multilingual (b/c, p) | 3/2, 1.0000 | 11/1, 0.0063 | 3/0, 0.2500 | 8/2, 0.1094 | 11/2, 0.0225 | 36/7, 9.0e-06 (not independent) |

- With n=20 per language, the per-language magnitudes are directional signals. The ids with the same label in all 5 languages are Jev 18/20 (mean agreement over language pairs 0.935), Laya english 0/20, multilingual 5/20, Router 4/20. The mean language penalty vs en is Jev +0.012, english −0.362, multilingual −0.287.

**T8 prompt-injections (S5, gold true 20/40)**

| System | Accuracy (p(true) ≥ 0.5) | Predicted true | FN / FP | AUROC [bootstrap 95%] | Brier | McNemar vs Jev (b/c, p) |
|---|---|---|---|---|---|---|
| Jev | 31/40 = 0.775 [0.625, 0.877] | 11 | 9 / 0 | 1.000 (perfect separation, degenerate CI) | 0.307 | - |
| Laya english | 31/40 = 0.775 [0.625, 0.877] | 11 | 9 / 0 | 0.929 [0.840, 0.997] | 0.401 | 5/5, 1.0000 |
| Laya multilingual | 23/40 = 0.575 [0.422, 0.715] | 9 | 14 / 3 | 0.781 [0.615, 0.919] | 0.692 | 11/3, 0.0574 |
| Laya Router | 29/40 = 0.725 [0.572, 0.839] | 11 | 10 / 1 | 0.868 [0.738, 0.969] | 0.510 | 7/5, 0.7744 |

- Accuracy is the same, but the error structure differs. Jev missed role- and task-instruction-style injections by scoring them low, at p(true) 0.08\~0.40, and with p(true) of 0.01\~0.04 on the benign rows, the optimal threshold for these 40 rows lies above 0.04 and at or below 0.08 (descriptive statistics). Laya english missed 4 explicit overrides written in German (`S5_summary.md` §4).

### 7.1d S7 results (2026-10-08, `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md`, `S7_run_card.md`)

The tasks T9·T10 of the 3-arm extension (`11_three_arm_plan.md`), which are in Laya's training mix, were sent under the same rules (approved by the project owner 2026-10-08). All 80 requests (T9 40 + T10 40) were HTTP 200, with 5xx·429·limit messages·captcha 0 and retries 0. Gaps (monotonic): minimum 15.009 s, median 15.134 s. The pre-request payload hash and the post-request body byte check agreed 80/80, and Model ID was `typesafe-ai/jev` 80/80. The Laya side is the reports in `results/T3arm/vanilla/`, and Router sent all 80 rows to english.

| Task | Jev | Laya english (= Router) | Laya multilingual | McNemar vs Jev: english / multilingual (b/c, p) |
|---|---|---|---|---|
| T9 Enron spam (noul, gold true 20/40) | 40/40 = 1.000 [0.912, 1.000] | 40/40 = 1.000 | 40/40 = 1.000 | 0/0, 1.0000 / 0/0, 1.0000 |
| T10 customer-support ticket queue (10-way choice, 4 per queue) | 10/40 = 0.250 [0.142, 0.402] | 12/40 = 0.300 | 18/40 = 0.450 | 3/5, 0.7266 / 4/12, 0.0768 |

- On T9 all four systems are at the ceiling and cannot be distinguished (AUROC 1.000 for all). Only calibration differs (Brier Jev 0.019, english 0.005, multilingual 0.000).
- On T10, Jev is strongly overconfident: mean top p 0.873 at an accuracy of 0.250, 18 of the 30 wrong answers have top ≥ 0.90, and 20/40 rows display the gold option at 0% (Brier 1.319, ECE 0.623).
- On T10, 18/40 rows are wrong for all three systems, and in many of the errors the gold queue does not match the queue description given in the question (interpretation; to be verified by hand). In the 3-arm synthesis, adding trained leaves the same 18 rows (`results/T3arm/summary.md` §1.6).
- Latency: displayed median 219 ms (T9 214.5, T10 226).

### 7.2 Daily budget table (done 2026-10-07, S7 2026-10-08)

| Date | Session | Tasks | Requests | Cumulative |
|---|---|---|---|---|
| 2026-10-06 (done) | pilot + S1 + S1b | Korean 24 (+502 1), checks 2, exploration 1, T2 40, determinism 10, permutation 20 | 98 | 98 |
| 2026-10-07 (done) | S2 | T1-A 39 (row 30 reused from S1) + 502 retry 1, T3 40 | 80 | 178 |
| 2026-10-07 (done, after the daily cap was lifted) | S3 | T4 40, T5 40 | 80 | 258 |
| 2026-10-07 (done) | S4 | T6 40, T7 en·de 40 | 80 | 338 |
| 2026-10-07 (done) | S5 | T7 ja·zh-CN·ko 60, T8 40 | 100 | 438 |
| 2026-10-08 (done, 3-arm extension) | S7 | T9 40, T10 40 | 80 | 518 |
| Not run (optional) | S5-b | T4 v0 rendering also for Jev +40, T3·T4·T7 permutation probes | 0 | |

T1 was settled on plan A (1 time per case, 4-level score questions omitted, 120 decisions compared, score MAE only on the 10 questions with 5 levels). Alternative C (Single, 1 time per decision) would take 3 times the requests for the same 120, so it is not adopted.

The cumulative count is over all requests to the site (including the pilot's 25 and the 2 checks). The total up to the S6 synthesis is 438, and adding the 80 of S7 from the 3-arm extension gives 518. `results/F/jev_cmp/jev_runs_all.jsonl` holds S1 41 + S1b 30 + S2 80 + S3 80 + S4 80 + S5 100 = 411 rows followed by 80 S7 rows, 491 rows in all (the F synthesis uses only the first 411), and the 27 pilot and check requests are recorded in a separate file (`results/F/jev_runs_raw.jsonl`) (the two logs are not included in the public repository). The daily cap was lifted on 2026-10-07 (§2), so S3\~S5, originally planned for days 3\~5, ran on the same day.

**S3 carry-over rule**: S3 is T4 40 + T5 40 = 80, equal to the session cap, so if a 5xx retry occurs, the last remaining item is carried over to S4 and deducted from the S4 budget. Timing is monotonic from the start (to handle the wall-clock step between S2 runs 60/61, §7.1b). There was no 5xx in S3\~S5, so this rule was not used.

### 7.3 Session run card fields (items added to 06 §1)

- Result of the site status check (time, response to the default example, displayed latency)
- Number of requests (success / 5xx / retries), minimum and median gap, session start and end times
- Model ID and input/output token range ("View details")
- Input-hash check results (before and after the request), number of parse failures
- Original text of error messages and how they were handled (stop, retry, end)
- Path of the corresponding Laya report (the `laya-evals` JSON of the same set) and `questions_sha256`

---

## 8. Outputs

| Path | Contents |
|---|---|
| `data/evals/jev_cmp/T1_typed_decisions_40.jsonl` and the others, 12 for T1\~T8 (+ the archived `T4_banking77_10opt_40_v0.jsonl`) | Sets in laya-evals format (for Laya). The input for Jev is the `*_playground.json` of the same name |
| `data/evals/jev_cmp/MANIFEST.json` | sha256, n, source·split·revision, license, label distribution, questions_sha256, `jev_comparable_n`, `jev_excluded`, T4's `options_rendering`·`previous_version` |
| `scripts/build_jev_cmp_sets.py` | Set builder (reusing the `scripts/build_ko_evalsets.py` helpers) |
| Extended `results/F/jev_f.py` or `scripts/jev_playground_runner.py` | sample / record / analyze, session budget counter, retry rule |
| `results/F/jev_cmp/laya/<set>_<model>.json|.md` | Laya laya-evals reports (S0) |
| `results/F/jev_cmp/laya_summary.md` / `.json` | Laya-side summary (task × checkpoint, T1 on the 190 basis, T4 v0 vs key-only, determinism and permutation) |
| `results/F/jev_cmp/sessions/S<k>_<date>/` | Jev session raw records (per-request JSONL, DOM, snapshots, captures, `multi_question_mode.md`; the per-request JSONL, DOM, snapshots and captures are not included in the public repository) |
| `results/F/jev_cmp/jev_runs_all.jsonl` (not included in the public repository) | Append-only master request log of every Jev request (session id, attempt, result) |
| `results/F/jev_cmp/S<k>_<date>.md` | Per-session run card (06 §1, including request counts, gaps and errors). S0 is `S0_20261006.md` |
| `results/F/jev_cmp/summary.md` / `.json` | Final comparison summary (task × system table, McNemar·Holm, aggregate statistics, calibration, robustness, latency and cost, threats), S6 done. Generated and cross-checked with `s6_summary.py build`/`verify` (0 mismatches) |
| `results/F/jev_cmp/figs/accuracy_by_task.png`, `t7_languages.png`, `latency.png` (+ SVG) | S6 figures (accuracy per task with Wilson CIs, T7 accuracy per language, latency per deployment form) |
| `docs/10_paper_laya_vs_jev.md` (or a revision of 08) | Paper v2 |

---

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Site outage, usage limits | Stop rule and 1 retry. Started by spreading requests at 100 or fewer per day, and the daily cap was lifted by owner decision on 2026-10-07 (§2). In practice there were 2 502s and 0 429s. Tasks not completed are reported as "not run" |
| Model version drift | Record Model ID and tokens per session; track it with a determinism check of 10 identical items across sessions |
| Playground vs API differences | Mark every table "via the playground". Keep the plan to remeasure the same sets via the API if a key becomes available |
| Jev multilingual support undocumented | Report the T7 results only as facts; make no claim about the officially supported range |
| 10-option limit | State that Banking77·MASSIVE are under the 10-option condition; do not compare them directly with upstream's 77- and 20-option figures |
| Small sample | Report CIs alongside, give significant verdicts only for differences of 0.2 or more, representativeness check |
| Training-mix asymmetry | Pass on the in-training labels of T2·T5 (the rest, including T4·T7, are held out, build_benchmark_nb.py:760-762); interpret separately from the held-out tasks (T1, T3, T4, T6, T7, T8) |
| Automation ethics | Human speed, caps, 1 retry, state the source and limitations when publishing |

---

## 10. Conclusion (S6, 2026-10-07, `results/F/jev_cmp/summary.md`, `summary.json`)

**Verdict in one line.** Zero-shot, Jev is more accurate than Laya (of 8 tasks, Laya significantly better on 0, Jev significantly better on 2 after Holm correction), with the largest gaps on instruction-style and multilingual tasks. Laya is competitive in local execution, latency and cost, and in that fine-tuning can close the gap.

| Task | n | Jev | Laya english / multilingual / Router | vs best Laya: b/c, p (Holm p) | Verdict (after Holm) |
|---|---|---|---|---|---|
| T1 typed-decisions | 120 (40 cases) | 0.867 | 0.383 / 0.367 / 0.383 | english 66/8, 1.8e-12 (1.4e-11) | Jev significantly better (Jev significantly better) |
| T2 AG News | 40 | 0.875 | 0.975 / 0.925 / 0.975 | english 0/4, 0.1250 (0.3750) | not significant (not significant) |
| T3 DAIR Emotion | 40 | 0.700 | 0.750 / 0.625 / 0.750 | english 2/4, 0.6875 (1.0000) | not significant (not significant) |
| T4 Banking77-10 | 40 | 0.925 | 0.725 / 0.750 / 0.725 | multilingual 8/1, 0.0391 (0.1953) | Jev significantly better (not significant) |
| T5 BoolQ | 40 | 0.925 | 0.725 / 0.600 / 0.725 | english 9/1, 0.0215 (0.1289) | Jev significantly better (not significant) |
| T6 SST-5 | 40 | 0.650 | 0.425 / 0.325 / 0.425 | english 15/6, 0.0784 (0.3134) | not significant (not significant), MAE 0.432 vs 0.888 |
| T7 MASSIVE intent-10 x5 | 100 (20 ids) | 0.910 | 0.410 / 0.620 / 0.580 | multilingual 36/7, 9.0e-06 (6.3e-05) | Jev significantly better (Jev significantly better) |
| T8 prompt-injections | 40 | 0.775 | 0.775 / 0.575 / 0.725 | english 5/5, 1.0000 (1.0000) | not significant (not significant) |

**Synthesis.**
- Verdict tally (Jev significantly better / not significant / Laya significantly better): before correction 4 / 4 / 0, after Holm correction 2 / 6 / 0 (only T1·T7 significant).
- Macro accuracy: Jev 0.828, Laya english 0.646, multilingual 0.598, Router 0.661. In a task bootstrap (10,000 resamples), Jev − Router is +0.167 [+0.044, +0.293]; this is a descriptive statistic over 8 heterogeneous tasks.
- Pooled exact McNemar over 240 independent single questions (T2·T3·T4·T5·T6·T8): vs the best Laya per task, b/c 39/21, p=0.0273 (Jev 194, Laya 176).
- Cluster bootstrap (10,000 resamples): T1 (case) Jev − english +0.483 [+0.371, +0.597], T7 (id) Jev − multilingual +0.290 [+0.100, +0.470].
- Training mix: by upstream's labels, the only tasks in Laya's training mix are T2·T5 (`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`; `third_party/laya` is not included in the public repository; recreate it by cloning https://github.com/NandhaKishorM/laya at commit 4aa6761). Of the 4 tasks where Jev is significantly better, T1·T4·T7 are data neither checkpoint trained on (including T1·T7, which remain after Holm), and only T5 is an in-mix task. The tasks where Laya is equal or ahead are T2, which is in-mix, and T3·T8, which are held out.

**Calibration.** The meaning of Jev's probabilities differs by question format. For single choice, 65% are displayed at 100%, and 59% of the wrong answers have top ≥ 0.90. Boolean has 0 displayed at 100%, and the right position for the threshold differs by task (around 0.5 for T5, 0.04\~0.08 for T8). Multi-question (T1) is underconfident. The best Laya runners, grouped by format, are all overconfident. To set the scope of automatic handling by confidence, both systems need their thresholds tuned on per-task held-out samples (summary.md §5).

**Robustness.** On resending the same payload, Jev gave the same label 10/10 and the same probability vector 9/10, and Laya is deterministic. The T2 option-order flip is 0/20 for both systems (low information). On T7, the ids with the same label in all 5 languages are Jev 18/20, Laya english 0/20, multilingual 5/20, Router 4/20 (summary.md §6).

**Latency and cost.** Jev displayed value ('server + network') median 226 ms, browser POST median 465 ms (410 requests, including the internet round trip). Laya is 13.8\~86.6 ms in-process (D1, by checkpoint and device) and 20.1\~50.7 ms over localhost HTTP (P2·D6). The deployment forms differ, so this is not a model-speed comparison. Jev cost is $0.0197 per 1,000 decisions (mean 469.4 tokens per decision × the 3rd-party price cited in the README, $0.042/1M tokens; price to be verified), while Laya has no per-token charge and needs only local compute (summary.md §7).

**Fine-tuning reference lines (not zero-shot).** On T1, upstream's typed-decisions fine-tuned checkpoint scores 104/120 = 0.867, the same as Jev (b/c 10/10). The Korean domain-routing ft-v1 scores 22/24 = 0.917 on the 24 pilot rows, at or above Jev's 20/24 = 0.833 (p=0.5), and 0.900 on the ko_massive_domain_8 test half (Jev did not receive these 250 rows). Both lines are in-domain results that used train data from the same distribution (summary.md §3).

**Limitations.** To be read together: via the playground (not the API, model version not shown, probabilities rounded to 2 digits), n=40 per task (CI about ±0.15), the easiness of the seed 13 sample (T3), the unverified T1 teacher, Jev's joint evaluation of multiple questions, training contamination (by upstream's self-report only T2·T5 are in Laya's training mix; unknown for Jev), post-hoc selection of the Laya runner, and multiple comparisons over 8 tests (Holm) (summary.md §9).

**3-arm extension (2026-10-08, `11_three_arm_plan.md` §9, `results/T3arm/summary.md`).** When Laya fine-tuned on task labels (trained; about 6,400 labels per task; M4 Pro training loop 1.4-43.3 min per task) is added on the same Jev items, there is no significant difference from Jev after Holm correction on any of the 10 tasks, including the in-mix tasks T9·T10 (S7, §7.1d). Before correction, trained is significantly better on T3·T8, and there is no task where Jev is significantly ahead. The gaps on T1·T7, where Jev was significantly better after Holm in the table above, disappeared after training (T7 0.910 vs 0.910, T1 0.792 vs 0.867, cluster bootstrap −0.075 [−0.185, +0.025]). Zero-shot Jev vs vanilla on T9·T10 is not significant (T9 1.000 vs 1.000, T10 0.250 vs 0.300), and the label quality of T10 is doubtful. This is a specialization comparison, not zero-shot, so the zero-shot conclusion above does not change. Only verdicts whose conclusion matches the seed 14 replicate run are confirmed. In the replicate run (10 tasks), 27 of 30 verdicts are confirmed and 3 (T4·T8 Jev items, Holm p near 0.05) are inconsistent. trained vs Jev is confirmed (not significant) on 9 tasks, and only T8 shows trained significantly better in run 2.

---

## Open questions / assumptions

1. **(Resolved, S1)** Multiple questions mode supports 2\~5 questions and mixed types, but Score is fixed at 5 levels, so T1 goes with plan A (4-level score omitted, 120 compared) (§2, §7.2).
2. **(Resolved, S1)** The Score comparison rule is fixed as "argmax level accuracy + MAE based on E[level]". The level displayed by the playground is the level closest to E[level], so it can differ from the argmax.
3. **BoolQ·SST-5 source paths** (`google/boolq` validation, `SetFit/sst5`) and licenses are checked at build time. The licenses were checked on 2026-10-12: BoolQ is CC BY-SA 3.0 (google-research-datasets/boolean-questions README, HF card), and SST-5 (`SetFit/sst5`) has no license statement at any primary source, so it is unresolved (to be verified, `DATA_LICENSES.md`).
4. **The Jev unit price** is checked on the official page at run time and written in the run card with the date. The upstream-cited $0.042/1M tokens is a reference value. S6 computed $0.0197 per 1,000 decisions from this cited value, and the official price is still to be verified.
5. **(Resolved, S6)** ft-v1 is not kept as a T7 reference line. T7 is an intent task, a different task from ft-v1 (domain routing) (`results/F/jev_cmp/summary.md` §3).
6. **If an API key becomes available**, remeasure the same sets with `POST /v1/systemone`, report the differences from the playground results, and raise n to 300\~500 per task at that point.
7. **How to restructure the paper**: the default plan is to write a new 10 rather than revise 08, and to keep 08 as the Korean case study.
8. **T4 option rendering** changed Laya's accuracy substantially (§7.0, multilingual +0.175 p=0.016), so decide whether to send both renderings (key only, `key: description`) to Jev as well. Budget +40 requests. Left as the optional item S5-b and not run (§7.2).
9. **Jev Boolean receives no descriptions**, so the T1 noul comparison is limited to the 60 questions without labels. The Laya variant with the criteria removed did not change noul accuracy significantly (§2), which confirmed that this condition does not disadvantage Laya. T5 BoolQ and T8 prompt-injections are under the same condition (no descriptions for Jev).
10. **Verify the identity of the T1 teacher** (LocalLLaMA/typed-decisions data card): the T1 gold label is the argmax of the teacher distribution, so if the teacher is from the Jev family, T1 is a task that favors Jev. The interpretation of Jev zero-shot scoring the same 104/120 in S2 as the Laya checkpoint fine-tuned on this benchmark's train split (§7.1b) depends on this check (to be verified).
11. **Tool defect (follow-up item): Markdown→PDF renderer.** The smartypants step of the Markdown→PDF renderer used for PDF rendering replaces HTML tags with placeholders and then applies the URL pattern `/\bhttps?:\/\/\S+/g` (the renderer's `src/smartypants.ts:23`). When link text is a URL, `\S+` swallows the `</a>` placeholder right after it and restoration runs only once, so the placeholder string (`SMARTPANTS_PRESERVED_N`) is exposed in the body, `</a>` disappears, and the whole rest of the document turns into one link. Workaround: drop the URL scheme from link text (`[github.com/x](https://github.com/x)`, no bare URLs). Separately, GFM renders the text between two `~` within one paragraph or table cell as strikethrough, so the range marker `~` is escaped as `\~`. Both workarounds were applied to the docs/08·docs/10 PDFs (not included in the public repository) (2026-10-07). The em dash rule `/(\w|\s)--(\w|\s)/g` in the same file (`src/smartypants.ts:81`) also changes CLI flags in the body, so the `laya-evals --onnx` of `docs/08_paper_ko.md:282` is printed with an em dash in the PDF (no workaround; wrapping the flag in a code span avoids it; not fixed because of the instruction not to change the content of 08). This is a workaround, and it remains to be decided whether to fix the renderer (make the URL pattern stop at the placeholder boundary) or to file an issue with the renderer.

**English** | [한국어](09_laya_vs_jev_plan.ko.md)
