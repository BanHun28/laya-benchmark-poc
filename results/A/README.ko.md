# Track A 재현 기록 (2026-10-02)

Track A(03_benchmark_plan.md §5)의 A2/A3에 해당하는 측정은 한국어 지원 감사 K2의 E2 실험이 먼저 수행했다. 구성은 04 §5.1(a)의 upstream 충실 규칙(첫 100행, `random.Random(13)` 19개 distractor + shuffle, criteria `key.replace("_", " ").replace(".", ": ")`)이며 `laya-evals run --device cpu --batch-size 8` 경로로 측정했다. 원본 파일은 `results/korean_support/`에 있다.

| 데이터 | 체크포인트 | 측정 acc | upstream acc | Δ | ECE 측정 / upstream | 리포트 |
|---|---|---|---|---|---|---|
| ko intent-20 | multilingual | 0.470 | 0.470 (BENCHMARKS.md:71) | 0.000 | 0.3108 / 0.3108 | `results/korean_support/K2_intent20_ko_multilingual.json` |
| en intent-20 | multilingual | 0.710 | 0.710 (BENCHMARKS.md §Languages en 행) | 0.000 | 0.2333 / 0.2333 | `results/korean_support/K2_intent20_en_multilingual.json` |
| en intent-20 | english | 0.820 | 0.820 | 0.000 | 0.1383 / 0.1382 | `results/korean_support/K2_intent20_en_english.json` |
| ko intent-20 | english | 0.110 | 0.110 | 0.000 | 0.6804 / 0.6804 | `results/korean_support/K2_intent20_ko_english.json` |

- 판정: A2/A3 게이트 통과(±0.03 이내, 실제 Δ 0.000). 가설 H1 지지. mean_confidence와 acc@50%cov도 upstream `cpu_51_language_sweep_refreshed.json`과 일치(`results/korean_support/K2_analysis.md` E2-c).
- 차이점: upstream은 packed forward(`score_cases`), 우리는 행별 단독 forward(`rows_alone=100`). 이 해상도에서는 차이가 없었다.
- A1 fixture: `results/env/smoke_fixture_english_cpu.json` (02 §3.3, 5개 지표 4자리 일치).
- A4(zh 앵커), A5(MPS parity on this set)는 미실행. MPS parity는 PoC P0에서 7문항 argmax 7/7, max |Δp| 0.0017로 확인(`results/poc/P0_20261002.md`).
- 주의: `data/evals/ko_massive_intent_20opt.jsonl`(빌더 산출물)은 K2의 `K2_intent20_ko.jsonl`과 같은 규칙으로 만들어지므로 빌더 완성 후 두 파일의 `questions_sha256`과 행 일치를 한 번 확인한다(A3 하네스 동일성).

[English](README.md) | **한국어**
