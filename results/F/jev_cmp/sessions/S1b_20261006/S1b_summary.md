# S1b summary: T2 determinism 10 + option-order flip 20 (2026-10-06)

**Verdict.**
1. **Determinism.** In the 10 cases where the same payload was resent about 25 minutes later, the label was the same 10/10. The probability vector was the same in 9/10, and the remaining 1 case differed by 0.01 (Jev's per-item outputs are omitted in the public repository). Provider confidence also differed only for that same 1 case (by 0.01), and input and output token counts were the same 10/10. The results are effectively deterministic but not bit-identical. `latencyMs`, by contrast, varies from run to run (median |Δ| 26.7 ms).
2. **Option order.** 20 cases were sent with the same permutations as the Laya probe, and Jev flipped **0/20** (0.000, Wilson 95% [0.000, 0.161]). On the same 20 rows in the same order, Laya english and multilingual are also 0/20 each. Under the AG News 4-option condition, neither system showed order sensitivity.
3. However, the 3rd-party published value of 0.13 cannot be ruled out with this sample: at p = 0.13, the probability of observing 0/20 is 0.062.

Via the playground, not the API. The model version is not shown (`typesafe-ai/jev` 30/30), and the sample is small.

## 1. Design

| Item | Rule |
|---|---|
| Baseline | The T2 responses of S1 (same day, 10:05\~10:17). S1b requests at 10:29:46\~10:38:19 |
| 10 determinism rows | Drawn so as to include both rows Jev got right in S1 and rows it got wrong (Jev's per-item outputs are omitted in the public repository) → rows 2, 7, 11, 13, 15, 20, 24, 29, 33, 37. The payloads are byte-identical to S1 |
| 20 flip rows | From the 30 rows left after removing the 10 determinism rows, row 39, whose permutation is the identity, was excluded (row 13 is also the identity but is already a determinism row). From the remaining 29 rows, 20 were drawn at equally spaced midpoints (`xs[int((i + 0.5)·n/k)]`) → 0, 3, 4, 6, 8, 9, 12, 14, 17, 18, 21, 22, 25, 26, 28, 30, 31, 34, 35, 38 |
| Permutation | The order that the Laya probe (`results/F/jev_cmp/T2_option_order_k1_english.json`) used for each row was reused as is. That order is the stream obtained by consuming `random.Random(13)` 1 time per row, item-major, over the 40 rows; regenerating it the same way matched 40/40 (`scripts/probe_option_order.py` `probe_file`). The multilingual probe uses the same order. Jev and Laya therefore received the same permuted inputs |
| flip definition | A flip is when the argmax label (key) of the permuted run differs from the label of the S1 original-order run. Same per-permutation definition as the probe |
| Input check | sha12 precheck before the request, byte comparison of the request body after it (30/30). For permuted rows, `jev_cmp.py record --probe` builds the expected payload in the probe's order |

## 2. Determinism (same payload, vs S1)

| row | gold | S1 (top %) | S1b (top %) | same label | max abs Δp | latencyMs S1 / S1b | confidence S1 / S1b | tokens in/out S1 / S1b |
|---|---|---|---|---|---|---|---|---|
| 2 | sports | — | — | — | — | — | — | — |
| 7 | business | — | — | — | — | — | — | — |
| 11 | sports | — | — | — | — | — | — | — |
| 13 | world | — | — | — | — | — | — | — |
| 15 | world | — | — | — | — | — | — | — |
| 20 | sports | — | — | — | — | — | — | — |
| 24 | world | — | — | — | — | — | — | — |
| 29 | world | — | — | — | — | — | — | — |
| 33 | world | — | — | — | — | — | — | — |
| 37 | world | — | — | — | — | — | — | — |

Summary:

| Metric | Value |
|---|---|
| same label | 10/10 |
| probability vector identical | 9/10, max \|Δp\| 0.01 |
| confidence identical | 9/10, max \|Δ\| 0.01 |
| token counts identical | 10/10 |
| latencyMs median | S1 221.3 ms, S1b 233.2 ms |
| median run-to-run latencyMs \|Δ\| | 26.7 ms |

Displayed values are rounded to 2 decimals, so differences below 0.005 cannot be observed. 8 of the 10 sampled cases displayed 100%, so the power of the determinism check is low. The 1 case where the change appeared was a lower-probability item. As a reference, Laya english gave exactly the same answers when the 200 T1 decisions were rerun (`results/F/jev_cmp/laya_summary.md` §5).

## 3. Option-order flip (20 rows, same order as the probe)

| row | gold | order sent | Jev original order (top %) | Jev permuted (top %) | flip | p of the original label when permuted | slot chosen | Laya en original → permuted | Laya ml original → permuted |
|---|---|---|---|---|---|---|---|---|---|
| 0 | sci_tech | sci_tech / world / sports / business | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 3 | sci_tech | sci_tech / business / world / sports | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 4 | sports | sci_tech / sports / world / business | — | — | — | — | — | sports → sports | sports → sports |
| 6 | sports | sports / sci_tech / world / business | — | — | — | — | — | sports → sports | sports → sports |
| 8 | sports | world / business / sci_tech / sports | — | — | — | — | — | sports → sports | sports → sports |
| 9 | world | world / business / sci_tech / sports | — | — | — | — | — | world → world | world → world |
| 12 | business | sports / world / business / sci_tech | — | — | — | — | — | business → business | business → business |
| 14 | sci_tech | business / world / sci_tech / sports | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 17 | business | world / sports / sci_tech / business | — | — | — | — | — | business → business | business → business |
| 18 | business | business / sports / world / sci_tech | — | — | — | — | — | business → business | business → business |
| 21 | world | business / sci_tech / world / sports | — | — | — | — | — | world → world | world → world |
| 22 | sports | business / world / sports / sci_tech | — | — | — | — | — | sports → sports | sports → sports |
| 25 | business | sci_tech / sports / world / business | — | — | — | — | — | business → business | business → business |
| 26 | sports | sci_tech / world / sports / business | — | — | — | — | — | sports → sports | sports → sports |
| 28 | sci_tech | world / sci_tech / business / sports | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 30 | sci_tech | sci_tech / business / sports / world | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 31 | sci_tech | business / world / sci_tech / sports | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 34 | business | sports / world / business / sci_tech | — | — | — | — | — | business → business | business → business |
| 35 | sci_tech | business / world / sports / sci_tech | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 38 | sci_tech | sports / world / sci_tech / business | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |

| System (same 20 rows, same order) | flip / 20 | rate [Wilson 95%] | Reference |
|---|---|---|---|
| Jev (playground) | 0 | 0.000 [0.000, 0.161] | 3rd-party published Jev per-permutation flip 0.13 (reference table in `T2_option_order_k1_english.md`, `docs/09_laya_vs_jev_plan.md` §1). P(0/20 \| p = 0.13) = 0.062 |
| Laya english | 0 | 0.000 [0.000, 0.161] | T2 probe, all 40 rows: 0.000 (`results/F/jev_cmp/T2_option_order_k1_english.md`) |
| Laya multilingual | 0 | 0.000 [0.000, 0.161] | T2 probe, all 40 rows: 0.000 (`T2_option_order_k1_multilingual.md`) |

- On these 20 rows Jev's accuracy is 19/20 in both the original and the permuted order. The 1 wrong answer had the same label in both orders.
- The top probability moved by 0.007 on average. The largest move was 0.08, with the label unchanged.
- The distribution of chosen slots is 0: 6, 1: 3, 2: 7, 3: 4, which at n = 20 is no sign of a position bias.
- Which task and number of options the published 0.13 was measured on was not checked in this session (to be verified). This result is limited to the condition "AG News, 4 options, mostly high-confidence items".

## 4. Latency and tokens (30 S1b runs)

| Measurement | median / min / max |
|---|---|
| displayed "server + network" (= latencyMs rounded, half-up) | 223 / 165 / 646 ms |
| browser POST (resource timing) | 457.5 / 381 / 873 ms |
| click → complete | 460 / 383 / 875 ms |
| input / output tokens | 424.5 (410\~534) / 68 (66\~71) |

Same level as S1 (234 / 468 ms). The median of browser POST − latencyMs is 233.8 ms, the same as S1 (232 ms). Permutation did not change the token counts (same label strings; only the order differs).

## 5. Requests and budget

| Item | Value |
|---|---|
| S1b requests | `POST /api/evaluate` 30 times, all HTTP 200. 5xx, 429, limit messages, captcha: 0; retries 0 |
| Gaps | min 17.3 s, median 17.5 s, max 20.5 s (rule ≥ 10 s) |
| Cumulative today | pilot 25 + availability checks 2 + S1 41 + S1b 30 = **98** (daily cap 100, 2 left) |
| master log | `results/F/jev_cmp/jev_runs_all.jsonl` 71 lines (S1 41 + S1b 30, `session` field; not included in the public repository) |

## 6. Files

| File | Contents |
|---|---|
| `results/F/jev_cmp/sessions/S1b_20261006/S1b_requests.jsonl` (not included in the public repository) | 30 lines (`phase`: determinism / option_order, `perm`: order sent) |
| `results/F/jev_cmp/sessions/S1b_20261006/raw/r01_det_row02.json` … `r30_perm_row38.json` (not included in the public repository) | per-request dump (request body, response text, DOM, resource timing, status log) |
| `results/F/jev_cmp/sessions/S1b_20261006/raw/network_requests.txt`, `console.log`, `mcp/` | POST 30 / GET 46, console (0 errors), 34 MCP snapshots (none of the three is included in the public repository) |
| `results/F/jev_cmp/sessions/S1b_20261006/shots/` (not included in the public repository) | runs 1 (determinism), 11 (first permutation), 30 (last) |
| `results/F/jev_cmp/jev_cmp.py` | `expect/record --probe`, `stability S1 S1b T2_ag_news_40` (the tables in this document) |
| `results/F/jev_cmp/sessions/S1b_20261006/S1b_run_card.md` | run card |

**English** | [한국어](S1b_summary.ko.md)
