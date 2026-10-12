# Run 20261006-1029_jev-playground_S1b (T2_ag_news_40 determinism 10 + option order 20)

| Item | Value |
|---|---|
| run_id | 20261006-1029_jev-playground_S1b (Track F, Laya vs Jev comparison S1b: determinism and option-order flip from `docs/09_laya_vs_jev_plan.md` §5) |
| Date / start time | 2026-10-06 (KST). Page load 10:29:33, first click 10:29:46.183, last click 10:38:18.926, browser closed 10:38:30, analysis and write-up until \~10:45 |
| Track / PoC phase | F (S1b as directed, right after S1) |
| Hypothesis | None applies. There are two questions: Is Jev's answer reproduced on the same input? Does the argmax of Jev and Laya change when only the option order changes? |
| Purpose (one line) | Measure determinism by rerunning 10 T2 rows and flips by running 20 rows permuted, comparing against Laya with the same permutations as its probe |
| Commands | Selection and expected values: `.venv/bin/python results/F/jev_cmp/jev_cmp.py expect T2_ag_news_40 --rows 2,7,11,13,15,20,24,29,33,37`, `… expect T2_ag_news_40 --rows 0,3,4,6,8,9,12,14,17,18,21,22,25,26,28,30,31,34,35,38 --probe`. Browser: Playwright MCP, Single question / Choice, same instrumentation as S1 (passive listeners + `/api/evaluate` fetch wrapper) → `browser_fill_form` (state, plus the 4 choice fields for permuted rows) → `window.__jev.ready('<sha12>')` → `button.run-button` → `window.__jev.dump()` → `raw/rNN_*.json` (not included in the public repository). Record: `jev_cmp.py record S1b T2_ag_news_40 <run> <dump> --row R --phase determinism` or `--phase option_order --probe`. Analysis: `jev_cmp.py stability S1 S1b T2_ag_news_40` |
| Environment record | No local model run. Playwright MCP Chromium. The Laya comparison uses the existing probe JSON (`T2_option_order_k1_{english,multilingual}.json`, CPU) |
| Checkpoint | Jev `typesafe-ai/jev` 30/30 (no version shown). Laya english / multilingual revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` (the probe is at parity with the S0 reports, 40/40) |
| Dataset | `data/evals/jev_cmp/T2_ag_news_40.jsonl` (the T2 files are not included in the public repository), dataset_sha256 `555c7cd7d38c78d183fe884c62e1bbb102d040871bf6e66a8911269eba20fd21`, questions_sha256 `c472cb1cb971dab3d01c811ccc0f997d39516555fd43f513a8c59654e0457be1`. Form `T2_ag_news_40_playground.json` sha256 `1da0f5494068650edbcc6a23bf26f46790ef6592339f28f46d922f32370191d9` |
| Device / precision / threads | Jev hosted, unknown. Laya probe CPU fp32 |
| Parameters | Question ``What is the topic of `article`?``, 4 choices (label strings as in S1). The 10 determinism rows use the original order; the 20 flip rows use the probe's per-row order. Selection rule and permutation source in `S1b_summary.md` §1 |
| Repetitions / warm-up | 1 per row. Each determinism row is paired with the same row in S1 (about 15\~30 min after S1, in a different page load) |
| Duration | Browser session about 9 min (evaluation window 8 min 33 s). Whole task about 20 min |

## Results

| Metric | Value | Upstream reference (source) | Difference | Notes |
|---|---|---|---|---|
| Determinism: same label | 10/10 | Laya english rerun fully identical (`results/F/jev_cmp/laya_summary.md` §5) | n/a | |
| Determinism: same probability vector (2-decimal display) | 9/10, max \|Δp\| 0.01 (Jev's per-item outputs are omitted in the public repository) | Same source | n/a | confidence also differs only on that same 1 case, by 0.01. Token counts identical 10/10 |
| Determinism: latencyMs | Median on the same rows S1 221.3 → S1b 233.2 ms; per-row \|Δ\| median 26.7 ms | n/a | n/a | |
| Option-order flip, Jev | 0/20 = 0.000, Wilson 95% [0.000, 0.161] | Jev 3rd-party 0.13 (`docs/09_laya_vs_jev_plan.md` §1) | −0.13 | P(0/20 \| 0.13) = 0.062, cannot be ruled out |
| Option-order flip, Laya english / multilingual (same 20 rows, same order) | 0/20 / 0/20 | T2 probe, 40 rows: 0.000 / 0.000 (`results/F/jev_cmp/T2_option_order_k1_{english,multilingual}.md`) | 0 | |
| choice_accuracy (20 flip rows) | Jev original order 19/20, permuted 19/20 | n/a | n/a | Wrong: 1 |
| noul_accuracy / score_mae / ece | n/a | n/a | n/a | choice task, small sample |
| mean_confidence | Mean change of top p in the permuted runs 0.007, max 0.08 | n/a | n/a | |
| latency (Jev displayed / browser POST / click→complete) | 223 (165\~646) / 457.5 (381\~873) / 460 (383\~875) ms, n=30 | Jev 3rd-party p50 236\~276 ms | Near the range | displayed = latencyMs rounded half-up 30/30 |
| Tokens | Input 424.5 (410\~534), output 68 (66\~71) | n/a | n/a | |

## §7.2 Session fields

| Item | Value |
|---|---|
| Site status check | 10:29:33 page loaded normally. The first request (10:29:46) returned 200 |
| Request count | `POST /api/evaluate` 30 times: success 30, 5xx 0, 4xx 0, retries 0. The browser network list also shows POST 30 (all 200), GET 46 (static 25, RSC prefetch 20, document 1) |
| Gaps | min 17.3 s, median 17.5 s, max 20.5 s |
| Model ID / token range | `typesafe-ai/jev` 30/30, input 410\~534, output 66\~71, `rounding` {2, 2}, `warnings` [] |
| Input hash check | sha12 before the request matched 30/30; byte comparison of the request body after the request matched 30/30. For permuted rows the expected values were built in the probe order, and the analysis step re-checked that the recorded `perm` equals the probe order 20/20 |
| Parse failures | 0. Screen display = response 30/30 |
| Error messages | None. Console errors 0, warnings 192 (all CSS preload notices) |
| Laya counterpart | Determinism: `results/F/jev_cmp/laya/T1_typed_decisions_40_english_rerun.json` (Laya determinism baseline). flip: `results/F/jev_cmp/T2_option_order_k1_{english,multilingual}.json` |
| Cumulative site usage today | pilot 25 + availability checks 2 + S1 41 + S1b 30 = 98 (cap 100) |

## Outputs

- `results/F/jev_cmp/sessions/S1b_20261006/S1b_summary.md`
- `results/F/jev_cmp/sessions/S1b_20261006/S1b_requests.jsonl` (30 lines), `results/F/jev_cmp/jev_runs_all.jsonl` (master, 71 lines) (the two files are not included in the public repository)
- `results/F/jev_cmp/sessions/S1b_20261006/raw/` (30 dumps, `network_requests.txt`, `console.log`, 34 `mcp/` snapshots; none of these is included in the public repository)
- `results/F/jev_cmp/sessions/S1b_20261006/shots/S1b_run01_det_row02.png`, `S1b_run11_perm_row00.png`, `S1b_run30_perm_row38.png` (not included in the public repository)
- `results/F/jev_cmp/jev_cmp.py` (`--probe` and `stability` added)

## Anomalies / notes

- 8 of the 10 determinism rows displayed 100%, which leaves little room to observe probability changes. The only change occurred on 1 lower-probability row.
- Most of the 20 flip rows are high-confidence items in S1 (13/20 displayed 100%). 0/20 means "flips are rare under this condition", and the difference from the published 0.13 is not significant.
- The Playwright MCP output directory (34 snapshots, console log) was copied to `raw/mcp/` and then deleted.

## Next actions

- Order sensitivity would be more informative if measured again on tasks with more options and lower confidence (T3 emotion, 6 options; T4·T7, 10 options). The same permutations as the Laya probe should be used there as well.
- 2 requests of site budget remain today. The next session is postponed to tomorrow.

**English** | [한국어](S1b_run_card.ko.md)
