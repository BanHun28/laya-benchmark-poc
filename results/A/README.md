# Track A reproduction record (2026-10-02)

The measurements that correspond to A2/A3 of Track A (03_benchmark_plan.md §5) were already performed by experiment E2 of the Korean support audit K2. The construction follows the upstream-faithful rule of 04 §5.1(a) (first 100 rows, 19 `random.Random(13)` distractors + shuffle, criteria `key.replace("_", " ").replace(".", ": ")`), and it was measured through the `laya-evals run --device cpu --batch-size 8` path. The source files are in `results/korean_support/`.

| Data | Checkpoint | Measured acc | upstream acc | Δ | ECE measured / upstream | Report |
|---|---|---|---|---|---|---|
| ko intent-20 | multilingual | 0.470 | 0.470 (BENCHMARKS.md:71) | 0.000 | 0.3108 / 0.3108 | `results/korean_support/K2_intent20_ko_multilingual.json` |
| en intent-20 | multilingual | 0.710 | 0.710 (BENCHMARKS.md §Languages en row) | 0.000 | 0.2333 / 0.2333 | `results/korean_support/K2_intent20_en_multilingual.json` |
| en intent-20 | english | 0.820 | 0.820 | 0.000 | 0.1383 / 0.1382 | `results/korean_support/K2_intent20_en_english.json` |
| ko intent-20 | english | 0.110 | 0.110 | 0.000 | 0.6804 / 0.6804 | `results/korean_support/K2_intent20_ko_english.json` |

- Verdict: A2/A3 gate passed (within ±0.03; actual Δ 0.000). Hypothesis H1 supported. mean_confidence and acc@50%cov also match upstream `cpu_51_language_sweep_refreshed.json` (`results/korean_support/K2_analysis.md` E2-c).
- Difference: upstream scores with a packed forward (`score_cases`); we run a standalone forward per row (`rows_alone=100`). At this resolution there was no difference.
- A1 fixture: `results/env/smoke_fixture_english_cpu.json` (02 §3.3; the 5 metrics match to 4 decimal places).
- A4 (zh anchor) and A5 (MPS parity on this set) were not run. MPS parity was confirmed in PoC P0 with argmax 7/7 on 7 questions and max |Δp| 0.0017 (`results/poc/P0_20261002.md`).
- Note: `data/evals/ko_massive_intent_20opt.jsonl` (builder output) is built with the same rule as K2's `K2_intent20_ko.jsonl`, so once the builder is complete, check once that the two files agree in `questions_sha256` and row by row (A3 harness identity).

**English** | [한국어](README.ko.md)
