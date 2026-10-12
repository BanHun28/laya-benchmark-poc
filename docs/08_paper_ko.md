# Korean Applicability of the Laya Multilingual System-1 Decision Engine: Zero-shot Benchmark, Fine-tuning, and a Domain-Routing PoC

**Written** 2026-10-06 · **Environment** Apple M4 Pro (10P+4E CPU, 20-core GPU/MPS, 48 GB), macOS 26.6.2 · **Subject** laya 0.3.23 (upstream commit 4aa6761), checkpoint bundle `convaiinnovations/laya` @ 55cf4c4 · **Evidence files** `results/` (report `results/REPORT.md`, verdicts `results/go_no_go.json`, `results/verdicts.json`)

## Abstract

Laya is a non-autoregressive decision engine that produces probability distributions over typed decisions (choice, score, noul) in a single encoder forward pass; it claims to cover more than 100 languages, but its applicability to Korean has not been verified beyond a single MASSIVE intent row (0.470). On a single Apple M4 Pro, this study performs (1) a reproduction of upstream figures, (2) an audit of the level of Korean support, (3) a zero-shot quality, robustness, and calibration benchmark built on 19 sets of public Korean data, (4) serving-performance measurements, (5) fine-tuning on labeled data, and (6) a small-sample comparison with the hosted decision model Jev, and on the basis of the results implements a Korean 8-domain router PoC through to a service and a demo UI. The key results are as follows. ① Upstream's 4 Korean and English MASSIVE cells were reproduced with Δ0.000. ② Zero-shot Korean 8-domain routing accuracy is 0.492 on the test half and could not exceed 0.6 with schema wording, calibration, or thresholds; with the schema of descriptive Korean descriptions there is no penalty even when the same sentences are given in English (0.526 vs 0.510, p=0.47), so the limit lay not in the language but in the zero-shot ability of the checkpoint. ③ ft-v1, fine-tuned for 36 minutes on 11,094 rows of MASSIVE ko train, recorded 0.900 on the same test half, 0.913 on the full test set of 2,917 rows, ECE 0.053, and an option-order flip of 0.037. ④ The p95 of a 3-question call to the multilingual checkpoint is MPS 22.6 ms and CPU 57.8 ms, and the HTTP server had p95 79.4 ms at 10 RPS. ⑤ In a 24-item manual comparison, Jev outperformed zero-shot Laya (0.833 vs 0.417, p=0.002) and was indistinguishable from the fine-tuned ft-v1 (0.917, p=0.5). In conclusion, for Korean, Laya is not a "zero-shot decision engine" but a "base that can be specialized quickly", and, premised on a fine-tuning pipeline, it passed all of the predefined gates G0\~G7 (Conditional Go).

## 1. Introduction

### 1.1 Background

Laya[1] places a decision head on a ModernBERT-large (English, 421M) or mmBERT-base (multilingual, 322M) encoder and evaluates a state together with a bundle of typed questions in a single forward pass. The question types are `choice`, which picks one label from a closed label set, `score`, which outputs the expected value over ordinal levels, and `noul`, which outputs the probability that a statement is true; since there is no text generation, there are no parsing failures or hallucinations. Training uses reinforcement learning with a strictly proper scoring rule as the reward (RLCD), on which upstream bases its claim that the probabilities are calibrated, and the Router detects the script and language of the input to choose a checkpoint. Upstream presents 32.8 ms for a 1-question call on a Tesla T4, a MASSIVE intent benchmark over 51 languages (Korean 0.470), and an advantage over the hosted decision API Jev [1].

### 1.2 Problem

For Korean, the only figure upstream presents is MASSIVE intent with 20 options on 100 rows; whether Korean is included in the training data, whether the tokenizer and routing handle Korean input correctly, and whether the calibrated probabilities also hold for Korean are not documented. Upstream itself writes that "the base checkpoints are not a zero-shot decision engine but a fast base for specialization" [1], so adopting Laya for a Korean service requires measuring the zero-shot ceiling and the effect of fine-tuning directly.

### 1.3 Research questions

- RQ1. To what level does Laya support Korean (documentation, tokenizer, routing, model)?
- RQ2. What level do zero-shot Korean quality, robustness, and calibration reach, and does schema design improve them?
- RQ3. Does local (Apple silicon) serving performance meet the predefined criteria?
- RQ4. How effective is fine-tuning on labeled data for Korean tasks?
- RQ5. How does Laya compare with the hosted decision model Jev?

### 1.4 Contributions

(1) A complete reproduction of upstream figures (Δ0.000) and a deterministic evaluation pipeline. (2) 19 evaluation sets in laya-evals format built from 6 public Korean sources, with a deterministic builder (`scripts/build_ko_evalsets.py`). (3) A Korean support audit (documentation, tokenizer, routing, same-sentence Korean-English comparison). (4) A benchmark that establishes the zero-shot ceiling (Tracks A\~F) and fine-tuning results (0.492 → 0.900). (5) A router service serving the fine-tuned checkpoint and the Laya Playground demo UI. (6) 6 upstream defects and inconsistencies found in the course of measurement.

## 2. Background and related work

**Laya's architecture.** Each question becomes one sequence row consisting of `"<type> question: <instructions>"`, the option rendering (head), and the state, and the questions of one call form a batch of rows that repeat the same state. The options share the head limit `head_max_len` (multilingual 256, english 192), so the tokens per option shrink to `max(4, (head_max_len − 16) // k)`, and beyond 20 options the labels can no longer be told apart (upstream's banking77 0.425) [1]. On load, the temperature is clamped to [0.5, 5.0], and each answer comes with a `confidence` (1 − normalized entropy) and an `answer_confidence` (the probability of the reported answer, the target of calibration). There are three checkpoints, english (ModernBERT-large), multilingual (mmBERT-base, context 1,024, up to 8,192 with RoPE), and typed-decisions (English fine-tune), and the Router detects the hangul range (`laya/lang.py:43`) and sends such input to multilingual.

**mmBERT-base.** Marone et al.[2] proposed an encoder that uses the ModernBERT architecture with the Gemma 2 tokenizer (256k vocab), pretrained on 3T tokens in more than 1,800 languages. Korean is among the 60 high-resource languages of the pretraining stage, with 28.4B tokens (1.43%) according to Table 9, ranking 13th of 89 languages. However, Korean is not among the 20 languages of FineWeb2-HQ (`results/korean_support/audit_docs_tokenizer_routing.md`).

**Evaluation harness.** `laya-evals` takes a JSONL label set, computes choice_accuracy, noul_accuracy, score_mae, ECE (15 bins, on `answer_confidence`), mean_confidence, and latency, and records dataset_sha256·questions_sha256·the checkpoint revision in the report's `config` to guarantee run identity [1]. This study added `scripts/metrics_extra.py`, which computes macro-F1, Brier, bootstrap CIs, exact McNemar, and coverage curves.

**Jev.** Jev is TypeSafe's hosted decision API, and Laya's HTTP server offers the same `POST /v1/systemone` protocol. The Jev figures cited by upstream are third-party published values (AG News 0.910, Banking77 0.870, Emotion 0.480, p50 236\~276 ms, ECE 0.246, option-order flip 0.13), not direct measurements [1][8]. No Korean Jev figures have been published.

**Data.** MASSIVE[3] is a corpus of parallel voice-assistant utterances in 51 locales with labels for 60 intents (59 in ko test) and 18 scenarios. We also used YNAT (news headlines, 7 topics) and NLI from KLUE[4], NSMC[5] (movie-review sentiment), K-MHaS[6] (multi-label hate speech), and 3i4K[7] (7 speech acts).

## 3. Experimental design

### 3.1 Hypotheses and gates

The research questions were made concrete as hypotheses H1\~H10 and PoC adoption gates G0\~G7 (Table 1). The gate thresholds are proposed values extrapolated from upstream figures and were fixed before execution (`docs/00_README.md` §6).

Table 1. Gate definitions

| Gate | Criterion |
|---|---|
| G0 reproduction | upstream published figures ±0.03 |
| G1 accuracy | PoC task test half ≥ 0.80 (absolute criterion when the LLM baseline is not run) |
| G2 selective automation | coverage ≥ 0.70 at error rate ≤ 5% (after calibration) |
| G3 calibration | held-out ECE ≤ 0.10 after refit |
| G4 robustness | option-order permutation flip rate ≤ 0.10 |
| G5 in-process latency | 3-question call p95 ≤ 100 ms (MPS) / ≤ 500 ms (CPU 10 threads) |
| G6 serving latency | laya-serve p95 ≤ 150 ms at 10 RPS (MPS) |
| G7 batch equivalence | predict vs predict_batch(sort_by_length) argmax flip 0, max \|Δp\| ≤ 0.01 |

### 3.2 Data

Table 2. Evaluation sets (`data/evals/`, `scripts/build_ko_evalsets.py`, seed 13)

| Set | Source | Task / options | n | Use |
|---|---|---|---|---|
| ko/en_massive_intent_20opt | MASSIVE ko·en test, upstream-faithful construction (first 100 rows, gold + 19 distractors) | intent / 20 | 100 | Track A reproduction |
| ko_massive_intent_full60 | the same 100 rows, all intents | 59 | 100 | high-cardinality probe (not run) |
| ko_massive_scenario_18 | the same 100 rows, derived from scenario | 18 | 100 | Track B |
| ko/en_massive_domain_8 | full MASSIVE ko test (2,917 after removing duplicates and utterances under 2 characters), stratified 500 + en pairs with the same ids | 8-domain routing | 500 (full 2,917) | main PoC task, Korean penalty |
| ko_klue_ynat_7 | KLUE YNAT validation | news topic / 7 | 500 | Track B, PoC auxiliary |
| ko_klue_nli_3 | KLUE NLI validation | NLI / 3 | 500 | Track B |
| ko_nsmc_sentiment | NSMC ratings_test | sentiment noul + 2-choice | 500 | Track B, C3, E6 |
| ko_kmhas_hate, ko_kmhas_type_8 | K-MHaS test | hate or not (noul) / type 8 | 500 / 500 | Track B |
| ko_3i4k_speechact_7 | 3i4K fci_test | speech act / 7 | 500 | Track B |
| 5 ablation variants | the sets above with Korean instructions / English descriptions | | | Track B3 |

The 8-domain taxonomy merges the 18 MASSIVE scenarios without overlap (productivity ← alarm·calendar·datetime·lists, media ← music·play·audio, smart_home ← iot, info_qa ← qa·weather·news, communication ← email·social, lifestyle ← takeaway·cooking·recommendation, transport, general). The question is `"Which domain should handle the request in \`utterance\`?"`, and the options are ASCII keys with descriptive Korean descriptions. The dev/test split is fixed in `results/B/B_splits.json` (row-index parity for the paired MASSIVE sets, parity of the state's sha256 for the others). Ablations were scored only on the dev half, and the test half was scored only once per frozen schema version. Figures excluding test utterances identical to train utterances (33 of 500 rows, 16 in the test half, 155 of all 2,917 rows; labels identical) are given alongside.

### 3.3 Models and environment

The checkpoints were pinned to Hub revision 55cf4c4 (`LAYA_REVISION=reviewed`), with Python 3.12.12, laya 0.3.23, torch 2.14.1, transformers 5.18.0, and onnxruntime 1.30.0 (`results/env/env_20261002-1333.json`). All quality figures were measured on CPU fp32 (intra-op 10, inter-op 1), and MPS was used for latency measurements. On MPS, fp16 autocast turns on only for calls with 5 or more rows; in P0 we confirmed argmax agreement 7/7 on 7 questions and max |Δp| 0.0017 (`results/poc/P0_20261002.md`).

### 3.4 Protocol

Accuracy comes from a deterministic single pass, and latency is the median·p95 of 10 repetitions after 3 warm-up runs. We used percentile bootstrap 95% CIs with 1,000 resamples (seed 13) for accuracy and ECE, Wilson CIs for proportions, and the exact McNemar test for A/B comparisons on the same items. Every report records dataset_sha256·questions_sha256·revision, and the builders and scripts produce byte-identical output for the same input.

### 3.5 Schema design rules

Choice keys are ASCII snake_case (no Boolean words), descriptions are descriptive Korean, instructions are in English (upstream convention; Korean instructions only as an ablation), there are at most 20 options, noul criteria have exactly the keys `true`/`false`, and state fields are referred to in backticks. Instructions and criteria are fingerprinted by questions_sha256, so a wording change goes into a new version file.

## 4. Results

### 4.1 Reproduction (Track A)

Table 3. Upstream-faithful MASSIVE intent-20 (n=100, CPU fp32; `results/A/README.md`, `results/korean_support/K2_analysis.md`)

| Input | Checkpoint | Measured acc | upstream acc | Δ | ECE measured / upstream |
|---|---|---|---|---|---|
| ko | multilingual | 0.470 | 0.470 | 0.000 | 0.3108 / 0.3108 |
| en | multilingual | 0.710 | 0.710 | 0.000 | 0.2333 / 0.2333 |
| en | english | 0.820 | 0.820 | 0.000 | 0.1383 / 0.1382 |
| ko | english | 0.110 | 0.110 | 0.000 | 0.6804 / 0.6804 |

Upstream extracts the logits with a packed forward while we used laya-evals' per-row forward, but there was no difference at this resolution. The 5 metrics on the 12 fixture rows also matched the expected values in docs/evals.md to 4 digits (`results/env/smoke_fixture_english_cpu.json`). H1 is supported.

### 4.2 Korean support audit (RQ1)

Table 4. Verdicts by layer (`docs/07_korean_support_audit.md`)

| Layer | Verdict | Evidence |
|---|---|---|
| Documentation | Korean is documented only as one of the 50 MASSIVE evaluation languages. No record of Korean in the RLCD decision training data. The model card's "Korean 0.490" is a T4 n=300 value, mixed in from a run different from the official table's 0.470 (n=100) | card·BENCHMARKS.md |
| Encoder | Korean has 28.4B tokens in mmBERT pretraining (1.43%, rank 13), a stage-1 high-resource language | [2] Table 9 |
| Tokenizer | UNK 0, fragmentation 0.2% or less, 0.98 tokens per syllable. A sentence with the same meaning takes 1.50 times as many tokens as in English (median, p90 2.20). With the english tokenizer, 91% of Korean tokens are sub-character byte fragments | `audit_docs_tokenizer_routing.md` Part 2 |
| Unicode | No NFC normalization, so NFD input blows up to 3.09 times as many tokens | same file |
| Routing | Of a 46-case battery: correct 28, harmless 4, default-dependent 4, failures 10. Mixed text with a majority of Latin characters and Korean under 10 syllables inside an English wrapper go to english. Only an explicit `lang="ko"` fixes all of them | `part3_routing_battery.md`, `lang.py:364-371` |

In upstream's 51-language table, Korean's 0.470 ranks 18th (median 0.400) and its ECE of 0.311 ranks 10th, and the ko/en ratio is 0.662. In terms of the token budget, the state space of a 7-question schema at multilingual `max_len=1024` is about 1,120\~1,310 characters in Korean and about 4,150 in English, so for the same content Korean gets about 68% of English's capacity.

**Same-sentence Korean-English comparison.** Using MASSIVE parallel pairs, we fed in Korean and English with the same content (Table 5).

Table 5. Korean penalty (multilingual; `results/korean_support/paired_ko_en_audit.md`, `results/B/summary_20261002.md`)

| Task | Option text | n | ko | en | en − ko | McNemar p |
|---|---|---|---|---|---|---|
| intent-20 | English key rendering (upstream construction) | 100 | 0.47 | 0.71 | +0.24 [+0.13, +0.35] | 1.2e-04 |
| scenario-18 | English key rendering | 100 | 0.35 | 0.56 | +0.21 [+0.12, +0.30] | 4.9e-05 |
| scenario-18 | descriptive Korean descriptions | 100 | 0.52 | 0.62 | +0.10 [−0.02, +0.22] | 0.143 |
| domain-8 | descriptive Korean descriptions | 500 | 0.526 | 0.510 | −0.016 [−0.054, +0.022] | 0.47 |

The size of the penalty depends on the language of the option text. A gap remains even after removing the effect of English utterances overlapping English keys character by character (key-overlap rows +14/44 vs non-overlap rows +10/56, p=0.04), but with the schema of descriptive Korean descriptions the penalty disappeared at n=500. Korean-English embedding alignment (`embed_fn_from_agent`, 100 pairs) was partial, with P@1 0.19/0.31 (chance 0.01). When the 30-sentence probe was translated into English and asked the same 7 questions, the "no" bias of the 4 noul questions (KO 93, EN 94 vs always-no 93/120) and the avoidance of frustration level 0 (0/30, 2/30) were the same in English, so this weakness is not specific to Korean but a property of the multilingual checkpoint. The english checkpoint got 107/120 right on the same English sentences.

### 4.3 Zero-shot quality (Track B, RQ2)

Table 6. Accuracy by set × runner (CPU fp32; `results/B/summary_20261002.md`)

| Set | Options | majority | english | multilingual | typed-decisions | Router auto |
|---|---|---|---|---|---|---|
| ko_massive_domain_8 (all / dev / test) | 8 | 0.126 | 0.262 | 0.526 / 0.560 / **0.492** [0.432, 0.552] | 0.288 | 0.526 |
| ko_klue_ynat_7 (all / test) | 7 | 0.144 | 0.216 | 0.634 / 0.655 | 0.234 | 0.634 |
| ko_massive_scenario_18 (n=100) | 18 | 0.210 | 0.310 | 0.520 | 0.330 | 0.520 |
| ko_massive_intent_20opt (n=100) | 20 | 0.170 | 0.110 | 0.470 | measured | 0.470 |
| ko_klue_nli_3 | 3 | 0.334 | 0.448 | 0.750 | measured | same |
| ko_nsmc_sentiment choice / noul | 2 | 0.500 | 0.528 / 0.516 | 0.774 / 0.638 | measured | same |
| ko_kmhas_hate (noul) / type_8 | 2 / 8 | 0.500 / 0.144 | 0.500 / 0.146 | 0.582 / 0.394 | measured | same |
| ko_3i4k_speechact_7 | 7 | 0.144 | 0.174 | 0.178 | measured | same |

multilingual was the only usable checkpoint on every Korean set (H2 partially supported: ≥ +0.20 over english on 7 of 10 questions), and Router auto sent 100% of the rows containing Hangul to multilingual. The domain_8 errors were absorbed by smart_home (gold 63, predicted 140) and general (62, 80). Korean instructions (Δ −0.020 / −0.004) and English descriptions (Δ −0.028 / +0.024) were both not significant on the dev half.

**Preliminary probes.** In a 30-sentence self-labeled probe before the scenario was chosen (CS triage, 7 questions), intent accuracy was 0.40, noul without criteria almost always answered "no" (confidence 0.9 or above), and frustration level 0 was chosen 0/30 times (`results/poc/P0_20261002.md`). Across 8 schema variants (noul criteria, labels A/B, 2-choice A/B·meaningful keys, Korean instructions, intents reduced to 4, English descriptions, string state, combinations), the best intent accuracy was 0.50, no form brought the total of the 4 binary questions above the always-no baseline of 93/120, and the 2-choice A/B collapsed to A (68/120) (`results/poc/P0b_ablation_summary.md`). In contrast, a 100-row preview gave YNAT 7 topics 0.65 (0.86 at the top 50% coverage) and 18 domains 0.52, so domain routing (scenario C) was chosen as the PoC task (`results/poc/P0c_20261002.md`). All 6 domain_8 schema v2 variants (stronger descriptions, general removed, example sentences added, reordering, reduction to 5 classes) were at or below v1 (dev 0.560) (`results/C/C_schema_v2_20261002.md`).

### 4.4 Robustness (Track C)

With 5 random permutations of the option order, the zero-shot per-permutation flip rate was domain_8 0.270 [0.230, 0.310] (any-flip 0.512), YNAT 0.168, and scenario-18 0.241, supporting H5 (10\~30%) but missing the G4 criterion of 0.10. Of the 337 flips, 74% came from rows that were already wrong in the original order, and among decisions with confidence 0.9 or above alone the rate was 0.094. A slot-position effect exists (χ² p=0.0009), but the smart_home absorption persisted under reordering, so it was judged to have a semantic cause (`results/C/C1_option_order_20261002.md`). On NSMC, the 2-choice with meaningful keys (0.774) was higher than noul (0.638) (p=6.5e-10).

### 4.5 Calibration and gating (Track E)

Table 7. Zero-shot multilingual calibration (`results/E/E_summary_20261002.md`)

| Item | Value |
|---|---|
| as-shipped ECE (domain_8 dev / test, YNAT dev / test) | 0.200 / 0.263, 0.202 / 0.148, all over-confident |
| fitted T (choice:6-10, clamp not triggered) | domain_8 2.0245, YNAT 1.8149, pooled 1.9161 |
| test ECE before → after | domain_8 0.263 → 0.098 [0.081, 0.162] (pooled) / 0.123 (per-task); YNAT 0.148 → 0.063 |
| coverage @ error ≤ 5% / ≤ 10% (domain_8 test, T chosen on dev) | 0.224 / 0.308 |
| per-domain T | dev coverage 0.180 → 0.316, but exceeds the budget on test (overfitting) → rejected |
| E6 NSMC noul threshold | AUROC test 0.822, dev Youden threshold p(true) ≥ 0.0073 → test accuracy 0.725 (0.641 at 0.5) |

The refit cut ECE by half or more and transferred across sets (second half of H4 supported at the boundary), but coverage barely changed. At accuracy a, the upper bound on the coverage achievable with error at most e is a/(1 − e), i.e., 0.518 at 0.492, so calibration cannot pass G2. In a 2-class softmax, a scalar temperature cannot move the 0.5 boundary, so noul's "no" bias is a matter of the decision threshold, not of calibration; in E6, merely moving the threshold took accuracy from 0.641 → 0.725.

### 4.6 Performance (Track D, RQ3)

Table 8. In-process latency (median ms; p95 also given for 3q; `results/D/D_summary_20261003.md`)

| Checkpoint · state | CPU 1q / 3q (p95) / 10q | MPS 1q / 3q (p95) / 10q |
|---|---|---|
| multilingual · short 59 tok | 37.7 / 56.4 (57.8) / 121.4 | 13.8 / 22.5 (22.6) / 62.4 |
| multilingual · long 433 tok | 81.8 / 195.8 (247.8) / 596.5 | 35.1 / 92.2 (92.5) / 284.8 |
| english · short 123 tok | 86.6 / 184.4 (186.5) / 472.8 | 31.8 / 79.6 (80.0) / 232.3 |
| english · long (truncated at 512) | 204.5 / 515.1 (529.5) / 1658.1 | 85.6 / 242.1 (242.8) / 747.4 |

MPS was 2.33\~2.80 times as fast as CPU with 10 threads for 1 question, and the advantage stayed constant at 1.9\~2.8 times as the number of questions grew (H8 rejected). The gain from fp16 autocast was at most 8%, and with pauses of 100 ms or more between calls MPS became 2.2\~3.6 times slower. 10 intra-op threads were optimal (14 was 2\~22% slower), and the cold load took 3.45\~3.67 s for multilingual (tokenizer parsing about 1.0 s) and 2.82\~2.97 s for english.

Table 9. Batch·HTTP·ONNX·memory

| Measurement | Result |
|---|---|
| predict_batch CPU n=256 (bs 8/16/32) | an unsorted batch is slower, at 0.62\~0.83 times the speed of the loop; sort_by_length is 1.67 / 1.83 / 2.08 times as fast as unsorted and 1.39 / 1.42 / 1.29 times as fast as the loop; flip 0, max \|Δp\| 0.0001 (G7 passed, H9 supported). The MPS batch gain is 1.21\~1.25 times |
| Router ko/en alternation, 32 calls | 1 checkpoint switch 0.130 s (CPU) / 0.206 s (MPS); 0 reloads with max_loaded=2 |
| laya-serve MPS, 3 questions | open-loop 10 RPS p50 63.5 / p95 79.4 / p99 85.1 ms, errors 0, 503 0 (G6 passed); closed-loop saturation throughput 50 RPS for 1 question and 22.6 RPS for 3 questions (inference processed serially) |
| laya-serve CPU, 3 questions | c=1 p95 103.5 ms, 10 RPS p95 135.8 ms, saturation 10 RPS |
| /v1/systemone/batch | 16 / 64 states 218 / 848 ms (about 75 states/s) |
| ONNX CPU (YNAT 500, batch 16) | torch 0.634 / ECE 0.1723 / p50 302.2 ms; fp32 export same accuracy, 455.0 ms; int8 0.622 / 0.1877 / 525.9 ms (1.74 times slower, argmax agreement 0.930) → H10 rejected |
| Memory (CPU) | RSS with 1 / 2 / 3 resident checkpoints 2.07 / 3.63 / 5.23 GiB; 64-state batch peak +1.86\~+5.49 GiB |

G5 (3-question p95 MPS 22.6 ms, CPU 57.8 ms), G6 (79.4 ms), and G7 (flip 0) all passed.

### 4.7 Fine-tuning (P4, RQ4)

MASSIVE ko train was cleaned from 11,514 to 11,094 rows with deduplication and length filters, and validation from 2,033 to 2,012 rows, and the 8-domain labels were assigned. Upstream's Apple Silicon training script (`notebooks/laya_finetune_typed_decisions_mps.py`) was used as is with a data adapter written for it (gold is criteria-key based, `{"probabilities": {key: 1.0}}`), and option-order shuffle augmentation, which the script lacks, was added to the training items (11,093/11,094 rows reordered; validation in the original order). The hyperparameters are the script defaults (AdamW encoder 2.5e-5 / head 1e-4, weight decay 0.01, cosine, RLCD σ 0.4 → 0.1 + soft CE, fp32) with micro-batch 8 × grad-accum 4, 3 epochs (1,041 steps), gradient checkpointing off, and temperature calibration on 400 validation rows. On an idle MPS, training took 2,150 s (35.8 minutes), evaluation about 10 minutes, and the MPS peak was about 8 GB. A probe of just 1,000 rows for 1 epoch already took the test half from 0.492 → 0.720 (`results/P4/P4_probe_20261002.md`).

Table 10. Fine-tuning results (`results/P4/metrics/full_20261003-1156_summary.md`, `full_20261003-1156_coverage_*.md`, `full_20261003-1156_option_order_dev.md`)

| Evaluation | base multilingual | ft-v1 | Deduplicated (utterances identical to train excluded) |
|---|---|---|---|
| domain_8 500 rows all / dev / test | 0.526 / 0.560 / 0.492 | 0.894 / 0.888 / **0.900** [0.860, 0.936] | test 0.893 (n=234) |
| domain_8 full test, 2,917 rows | 0.475 | **0.913** [0.902, 0.923] | 0.908 (n=2,762) |
| validation 2,012 rows, epoch 1 / 2 / 3 | 0.462 | 0.892 / 0.916 / 0.918 | 0.914 |
| macro-F1 (500 / 2,917) | 0.518 / 0.491 | 0.891 / 0.893 | |
| ECE test half / 2,917 | 0.263 / 0.253 | 0.053 / 0.057 | |
| YNAT dev 245 (forgetting check) | 0.612 | 0.633 | |
| option-order flip (dev 250, 5 permutations) | 0.270 | 0.037 (any-flip 0.084) | |
| coverage @ error ≤ 5% | 0.224 | test half with post hoc T 0.756 (T 0.938); 2,917 rows with dev T 0.907 applied 0.923 (error 0.042) | |

The difference between epochs 2 and 3 was not significant, so the final export (epoch 3) was adopted as v1. The remaining confusion is general ↔ info_qa (25 / 20 cases on the 2,012 rows). Thanks to the shuffle augmentation, the flip rate dropped to 1/7.

### 4.8 Comparison with Jev (RQ5)

Table 11. Manual comparison on the public playground (n=24, 2026-10-06; `results/F/jev_playground_manual_20261006.md`)

| System | Correct | Accuracy | Wilson 95% |
|---|---|---|---|
| Jev (typesafe-ai/jev, playground) | 20/24 | 0.833 | [0.641, 0.933] |
| Laya zero-shot (multilingual) | 10/24 | 0.417 | [0.245, 0.612] |
| Laya ft-v1 | 22/24 | 0.917 | [0.742, 0.977] |

The sample consists of 3 rows per domain from the 234 rows of the domain_8 test half that do not overlap with train, and Jev was given the same questions as Laya and the same 8 options in the same order, in the form `key: Korean description`. Jev vs zero-shot gave b=10, c=0, p=0.002, a clear lead for Jev, while Jev vs ft-v1 gave b=0, c=2, p=0.5, indistinguishable (with ft-v1 at 22/24, p would be 0.5 even if Jev scored 24/24). 2 of Jev's 4 errors were of the "게임 열어" ("open the game") type, a gap caused by the absence of "게임" ("game") from our media description, and Jev was not confident when wrong (top probability of errors 41\~86%, mean for correct answers 96.5%; at a 90% cutoff, 18/24 accepted and 18/18 correct). The median latency displayed by the playground was 249.5 ms (203\~570; within the third-party published p50 range of 236\~276 ms), and the median POST measured in the browser was 497.5 ms, so the ratio to the local ft-v1 round trip of 20.1 ms (12\~36 times) mixes the hosted-vs-local difference with the network. Jev generates about 255 output tokens per call, which suggests generative decoding. The comparison took 25 requests in total (including 1 HTTP 502) and stayed within the usage limits of the free site.

### 4.9 PoC service and final verdict

ft-v1 was loaded as `Router(models={"multilingual": ckpt_domain8_v1, "english": models/laya})` (`poc/finetune/ckpt_domain8_v1/` and `models/` are not included in the public repository) and injected into `laya.serve.create_app(router)`, and the resulting service (`poc/service/app.py`) gained `/poc/decide`, `/poc/shadow`, `/poc/meta`, and a static `/poc/ui/` (Laya Playground). The hooks handle NFC normalization, masking of email addresses, phone numbers, and card numbers, shadow JSONL logging, and counters; the policy is ROUTE if `answer_confidence ≥ T` and FALLBACK otherwise, with T=0.907 (the maximum coverage at error ≤ 5% on dev-1459 of the 2,917 rows; applied to test-1458, coverage 0.923 and error 0.042). The acceptance checks passed 11/11, the `/poc/decide` round trip was p50 20.1 / p95 21.1 ms, and in-process CPU and server MPS answers agreed 9/9 (`results/poc/P2_20261003.md`).

Table 12. Go/No-Go matrix (`results/go_no_go.json`)

| Gate | Criterion | zero-shot | ft-v1 | Verdict |
|---|---|---|---|---|
| G0 | ±0.03 | Δ0.000 | same | pass |
| G1 | ≥ 0.80 | 0.492 | 0.900 (deduplicated 0.893, 2,917 rows 0.913) | pass |
| G2 | coverage ≥ 0.70 @ error ≤ 5% | 0.224 | 2,917 rows 0.923 (dev T 0.907); 250 rows with post hoc T 0.756 | pass (conditional) |
| G3 | ECE ≤ 0.10 | 0.098 (refit) | 0.053 | pass |
| G4 | flip ≤ 0.10 | 0.270 | 0.037 | pass |
| G5 | p95 ≤ 100 / 500 ms | | MPS 22.6 / CPU 57.8 ms | pass |
| G6 | 10 RPS p95 ≤ 150 ms | | 79.4 ms | pass |
| G7 | flip 0, \|Δp\| ≤ 0.01 | | flip 0, 0.0001 | pass |

The final verdict is **Conditional Go (premised on a fine-tuning pipeline)**. Zero-shot is No-Go, failing G1·G2·G4, and the fine-tuned ft-v1 passed every gate.

## 5. Discussion

**Key implications.** ① Upstream's "fast base to specialise" holds for Korean as well: with 11,000 rows of public labeled data and 36 minutes of local training, 8-domain routing accuracy rose from 0.49 to 0.90, with no forgetting on YNAT. ② The Korean penalty depends on the language of the option text and disappears with descriptive Korean descriptions, so the limit of Korean zero-shot lies not in language processing but in the zero-shot decision ability of the checkpoint itself. ③ The "no" bias of noul and the avoidance of score level 0 are the same with English input and are thus properties of the checkpoint; since ranking information is present (AUROC 0.76\~0.92), they are partly recoverable by threshold tuning. ④ Routing failures on mixed text and NFD input must be compensated for in the application with an explicit `lang="ko"` and NFC normalization. ⑤ On Apple silicon, the MPS gain is only 2\~3 times, ONNX int8 brings no gain, and laya-serve's serial inference sets a per-process throughput ceiling (MPS 22.6 RPS for 3 questions). ⑥ After fine-tuning, Laya delivers accuracy on par with Jev at a local round trip of 20 ms.

**Upstream defects and inconsistencies found.** (a) `laya.calibrate.records_from_labeled` lacks `@torch.no_grad()` and raises an exception on a real Agent (calibrate.py:286 → agent.py:1177). (b) `laya.evals.evaluate` calls `predict(..., model=)` and is incompatible with `Agent.predict`. (c) The output prefix of `hf download` in agent mode breaks the documented symlink command (`--quiet` needed). (d) The model card's "Korean 0.490" is a T4 n=300 value; the official table gives 0.470. (e) The README claim that "multilingual criteria-less noul reads the state" did not hold for Korean or for its English translation. (f) The license tag of the MASSIVE HF mirror (apache-2.0) differs from the original repository (CC BY 4.0). In addition, the 13 s MPS first call in examples/README.md took 0.1 s on this machine.

**Limitations and threats to validity.** Because of the sample sizes (test half n=250, reproduction n=100, probe n=30 with self-assigned labels), small differences were not judged. The T for G2 was chosen on the dev half; on the 250-row test half the result splits by selection method into error 7.9% (dev T) or coverage 0.756 (post hoc T), and on the 2,917 rows the error with dev T was 4.2%. The 155 rows of utterances identical between train and test were compensated for with deduplicated figures, but differences in label distribution remain. Quality figures were measured on CPU fp32 only, and MPS fp16 gave |Δp| ≤ 0.0085. The measurements come from a single machine and a single session, and the cause of the slowdown under intermittent calls was not isolated. The Jev comparison is a single pass (n=24) on the public playground, not the official API; the model version is not shown, and each option was passed in 1 label field only. Negation (C4), high cardinality (C6), long text (C8), and the LLM baseline (F2) were not run.

## 6. Conclusion and future work

Laya's multilingual checkpoint handles Korean input correctly at the tokenizer, routing, and model levels, and upstream's figures reproduce exactly, but the zero-shot ceiling for Korean multi-class routing is 0.5\~0.65, short of a production standard. Fine-tuning on labeled data for 36 minutes achieved accuracy 0.90\~0.91, ECE 0.053, flip 0.037, and coverage 0.92 at error ≤ 5% (2,917 rows), passing all of the predefined gates, and in the 24-item comparison the result was on par with the hosted model Jev. Future work comprises a formal 500-row paired comparison using the Jev API, an LLM zero-shot baseline, a negation probe, fine-tuning for CS triage (scenario A), re-selection of the operating threshold on a real-traffic set, and reporting the defects found to upstream.

## References

[1] NandhaKishorM, *laya* (v0.3.23, commit 4aa6761), [github.com/NandhaKishorM/laya](https://github.com/NandhaKishorM/laya), README.md, BENCHMARKS.md, docs/. Checkpoints: [huggingface.co/convaiinnovations/laya](https://huggingface.co/convaiinnovations/laya) (revision 55cf4c4).
[2] M. Marone, O. Weller, W. Fleshman, E. Yang, D. Lawrie, B. Van Durme, "mmBERT: A Modern Multilingual Encoder with Annealed Language Learning," arXiv:2509.06888, 2025.
[3] J. FitzGerald et al., "MASSIVE: A 1M-Example Multilingual Natural Language Understanding Dataset with 51 Typologically-Diverse Languages," arXiv:2204.08582, 2022. HF mirror `mteb/amazon_massive_intent`.
[4] S. Park et al., "KLUE: Korean Language Understanding Evaluation," arXiv:2105.09680, 2021. HF `klue/klue`(ynat, nli).
[5] L. Park, *Naver Sentiment Movie Corpus v1.0* (NSMC), [github.com/e9t/nsmc](https://github.com/e9t/nsmc), 2015.
[6] J. Lee et al., "K-MHaS: A Multi-label Hate Speech Detection Dataset in Korean Online News Comment," COLING 2022. HF `jeanlee/kmhas_korean_hate_speech`.
[7] W. I. Cho et al., 3i4K corpus, [github.com/warnikchow/3i4k](https://github.com/warnikchow/3i4k) (paper: "Speech Intention Understanding in a Head-final Language," arXiv:1811.04231, 2018; venue to be verified).
[8] AbdelStark, *jev-benchmarks*; nibzard, *decision-model-benchmark* (GitHub, third-party measurements of Jev; cited by upstream BENCHMARKS.md).
[9] *Jev Playground* (independent third-party playground), [jevplayground.com](https://jevplayground.com), accessed 2026-10-06. Model ID `typesafe-ai/jev`.

## Appendix A. Reproduction procedure (`results/REPORT.md` §9)

1. Environment: `docs/02_environment_setup.md` §2 (uv venv 3.12, `laya[serve,onnx,structured]==0.3.23`, `hf download convaiinnovations/laya --revision 55cf4c4… --quiet`, `models/` symlink, `env.sh`), §3 smoke test.
2. Evaluation sets: `.venv/bin/python scripts/build_ko_evalsets.py all --n 500 --seed 13` + ablation variants.
3. Track A: `laya-evals run data/evals/ko_massive_intent_20opt.jsonl --model multilingual --device cpu` and others, 4 runs.
4. Track B: `results/B/B_run.sh` → `scripts/metrics_extra.py summary|paired`.
5. Track C: `scripts/probe_option_order.py … --permutations 5 --seed 13 --split dev`, `results/C/C_schema_v2_build.py`.
6. Track E: `scripts/calibrate_ko.py --sets … --splits results/B/B_splits.json --pooled --per-task --min-bucket-n 100 --out-payload poc/calibration/ko_v1.json`.
7. Track D: `results/D/D_run.sh`(bench_latency_local.py, bench_batch_local.py, bench_http_local.py, export_onnx + `laya-evals --onnx`).
8. P4: `poc/finetune/make_domain8_items.py rows|items` → `bash poc/finetune/run_full.sh`.
9. P2: `LAYA_DEVICE=mps LAYA_API_KEY=devkey LAYA_HOST=127.0.0.1 .venv/bin/uvicorn poc.service.app:app --host 127.0.0.1 --port 8000` → `http://127.0.0.1:8000/poc/ui/`, `results/poc/P2_acceptance.py`.
10. Dashboard: `python3 scripts/build_dashboard.py --results results/ --out results/dashboard/index.html`.

## Appendix B. Outputs

| Category | Path |
|---|---|
| Planning documents | `docs/00_README.md` \~ `docs/07_korean_support_audit.md` |
| Evaluation sets·builder | `data/evals/*.jsonl` (19 sets), `data/evals/MANIFEST.json`, `scripts/build_ko_evalsets.py` |
| Measurement scripts | `scripts/metrics_extra.py`, `probe_option_order.py`, `calibrate_ko.py`, `bench_latency_local.py`, `bench_batch_local.py`, `bench_http_local.py`, `build_dashboard.py`, `env_report.py` |
| Results | `results/A`, `B`, `C`, `D`, `E`, `F`, `P4`, `poc`, `korean_support`, `env`; `results/REPORT.md`; `results/dashboard/index.html`; `results/go_no_go.json`; `results/verdicts.json` |
| Fine-tuning | `poc/finetune/ckpt_domain8_v1/` (not included in the public repository), `poc/finetune/run_full.sh`, `make_domain8_items.py` |
| Service·UI | `poc/service/app.py`, `hooks.py`, `policy.py`, `poc/service/ui/index.html`, `poc/schema/router_v1.json`; screenshots `results/poc/P2_ui_*.png` |

## Appendix C. Hypothesis verdicts (`results/verdicts.json`)

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1 ko MASSIVE reproduction | supported | Δ0.000, `results/A/README.md` |
| H2 multilingual ≫ english, Router 100% | partially supported | 7 of 10 questions ≥ +0.20; Hangul rows 100% multilingual |
| H3 tasks with ≤7 options: above majority, below supervised | first half supported / second half undecided | supervised values from the literature not looked up; ft-v1 0.913 |
| H4 as-shipped ECE > 0.25, refit ≤ 0.10 | partial / boundary support | domain_8 0.263, YNAT 0.148; pooled 0.098 |
| H5 option-order flip 10\~30% | supported | 0.168\~0.270; ft-v1 0.037 |
| H6 noul < 2-choice with neutral keys | undecided | P0b A/B 2-choice collapse; meaningful-key choice 0.774 > noul 0.638 |
| H7 zero-shot failure on negation | undecided | C4 not run (4 of 5 probe rows misjudged) |
| H8 MPS 3\~6 times, sub-linear | rejected | 2.33\~2.80 times |
| H9 sort_by_length ≥ 1.3 times, flip 0 | supported | 1.67\~2.08 times, flip 0 |
| H10 ONNX int8 ≈ 2 times, ECE drift ≤ 0.01 | rejected | 1.74 times slower, ΔECE +0.0154 |

**English** | [한국어](08_paper_ko.ko.md)
