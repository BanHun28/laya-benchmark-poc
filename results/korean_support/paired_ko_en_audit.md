# K2 Korean-penalty audit: ko vs en on the same content (paired)

> A controlled measurement for the Korean PoC decision. It uses the same MASSIVE ids (ko utterances and their en originals) and the same questions, and measures the accuracy difference with the same checkpoint while changing only the language.
> **The sets are not frozen evaluation sets.** They were made with a throwaway builder (`K2_build.py`), not the 04 §6 builder, and live outside `data/evals/` (in `results/korean_support/`). n=100 (MASSIVE), n=30 (probe). The 95% CI width is about ±0.10 at n=100 and about ±0.17 at n=30. Read the results as counts (x/100, x/30).
> The run card is in `results/korean_support/K2_20261002.md`. All tables are copied from `K2_analysis.md`, which `K2_analyze.py` recomputes from the `cases[*]` of the report JSONs (E3 from `K2_E3_embed_align.json`, the head budget from `K2_head_budget.md`).

## 0. Summary: Korean penalty (multilingual checkpoint, same content, same questions)

| Measurement | ko | en | en − ko (95% paired Wald CI) | McNemar exact p (b only ko / c only en) | Assessment |
|---|---|---|---|---|---|
| E1 scenario-18, Korean prose descriptions (P0c base questions, PoC schema form) | 52/100 | 62/100 | +0.10 (−0.02..+0.22) | 0.143 (14 / 24) | Not distinguishable at n=100. All 10 cases of the difference come from the 17 `play` rows (ko 1 vs en 11). The other 83 rows are 51 vs 51 (p=1.0) |
| E1 scenario-18, upstream key-rendering descriptions (`iot: iot`) | 35/100 | 56/100 | +0.21 (+0.12..+0.30) | 4.9e-05 (3 / 24) | Significant. `play` 0 vs 10, the other 83 rows 35 vs 46 (p=0.013) |
| E2 intent-20, upstream-faithful construction | 47/100 | 71/100 | +0.24 (+0.13..+0.35) | 1.2e-04 (7 / 31) | Significant. Exactly equal to the upstream published values 0.470 / 0.710 |
| E3 embedding alignment P@1 (ko→en / en→ko, chance 0.01) | - | - | 0.19 / 0.31 (P@5 0.43 / 0.45) | - | Partial alignment. The english checkpoint is at chance level with 0.03 / 0.01 |
| E4 probe, total of the 4 noul questions (always-no 93) | 93/120 | 94/120 | +1 | p=1.000 for each of the 4 questions | The noul collapse is not specific to Korean. Reading the same English sentences with the english checkpoint gives 107/120 |
| E4 frustration level 0 chosen (argmax, expected 18/30) | 0/30 | 2/30 | - | - | Avoiding level 0 (#131) is likewise a checkpoint trait unrelated to language |

One-line conclusion: in the upstream format (options rendered from English keys), the Korean penalty is large and significant at 0.21–0.24. With Korean prose descriptions, the scenario-18 penalty shrinks to 0.10 (n.s.), and the remaining difference also comes from a single class whose English utterances contain the key word (`play`) literally. In contrast, the always-no bias of noul and the avoidance of frustration level 0 appear just the same in English. This is not a Korean problem but a property of the multilingual checkpoint.

## 1. Design and methods

### 1.1 Data (MASSIVE paired)

| Check | Result | Evidence |
|---|---|---|
| Source | `mteb/amazon_massive_intent` config `ko`, `en`, split `test`, revision `940fd47a81eaa7f2cc7b129674d945d618ac38c2` (the value pinned in P0c; it is a repository-level revision, so it is shared by both configs) | K2_build_meta.json `massive.source` |
| Row count / label set | ko 2,974 / en 2,974, 59 intents, the two sets identical | `massive.rows`, `massive.labels` |
| id order | ko and en have the same id order over the whole split, so the first 100 en rows are exactly the twins of the first 100 ko rows | `same_id_order_full_split=true`, `en_first_100_are_the_ko_twins=true` |
| Pairing | The first 100 ko test rows (the same rows as P0c) + the en rows joined by `id`. All 100 pairs have the same `label_text` (builder assert) | `label_text_equal_all_100_pairs=true`, `row_ids` |
| Duplicates | 3 exact-duplicate pairs in the first 100 ko rows ("청소기 작동 시켜줘", "내일 비가 올까", "화장실 불 꺼 줘"). Their en twins are all distinct sentences ("start a vacuum cleaner" / "turn on the vacuum cleaner", etc.) | `exact_duplicate_*` |
| Limits of parallelism | MASSIVE ko is a localization, not a literal translation. Some pairs have different entities (0-based row numbers: 54 "임영웅 플레이리스트 재생" (play a Lim Young-woong playlist) ↔ "play a nirvana playlist", row 89 "싸이 노래 틀어" (play a PSY song) ↔ "open bad religion folder"). The labels are the same by construction, but the surface content is only "nearly parallel" | E1 `play` row dump (§2.3) |
| Training exposure | upstream states "Neither checkpoint trained on typed-decisions, MASSIVE or XNLI" | third_party/laya/research/results/t4_colab_benchmark.json `caveats.training_overlap` (`third_party/laya` is not included in the public repository; recreate it by cloning https://github.com/NandhaKishorM/laya at commit 4aa6761) |

### 1.2 Questions

| Experiment | Files (ko / en) | Questions | questions_sha256 (shared by ko·en) |
|---|---|---|---|
| E1 kodesc | K2_scen18_kodesc_{ko,en}.jsonl | id `scenario`, instructions "Which domain does \`utterance\` belong to?", 18 options in a fixed sorted order, the Korean descriptions of 04 §5.1(c). The `P0c_build.py` constants were imported. The (state, questions, expected) of the ko file equal the P0c base file row by row (builder assert) | 7bf1c9b1b314f6bdd03e49cbcd471106c2a7209c06407698e82bcdb182f30a44 (= P0c base) |
| E1 keydesc | K2_scen18_keydesc_{ko,en}.jsonl | The same instructions; description = the key as is (the rendering of upstream build_benchmark_nb.py:316). The ko file equals the P0c `_en-desc` file | 233520130f429820bf54b950d333db61a991e637addf592f3925b18c0245e85e (= P0c en-desc) |
| E2 | K2_intent20_{ko,en}.jsonl | Port of research/scripts/bench_local.py:165-183: `labels = sorted(set(label_text))` over the whole test split, `random.Random(13)` created 1 time, for each of the first 100 rows gold + `rng.sample(pool, 19)` then `rng.shuffle`, criteria `k.replace("_", " ").replace(".", ": ")`, instructions "What is the user asking for in \`utterance\`?". Each en twin uses the same key list as its ko row | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 |
| E4 v1 | probe_en.jsonl | The 7 merged questions of poc/schema/triage_v1.json + gateway_v1.json as they are (including the Korean criteria). state `{"message": <English>}`, expected copied from the original, tags `["p0_probe_en"]`, language `en`, and the `#` header states that this is a throwaway probe translation | 6b8bdadc8f9c718ed40f2510134caf52079a5dc0260e142d93d2132bee722c8a (= P0/P0b V0) |
| E4 v1b | K2_probe_en_v1b.jsonl | triage_v1b.json + gateway_v1b.json (Korean true/false criteria on the 4 noul questions) | 8ea18279f62ef606f642930f91c81350e5c2c0a20713a6fb5fc3b60660100819 (= P0b V1) |

E2 construction check: the port was compared option by option, for ko and en separately, with `build_suite` of the upstream harness `third_party/laya/research/eval/laya_eval.py` (the code that produced the refreshed numbers in BENCHMARKS), and equality was asserted. Since ko and en share the id order and the label set, the `Random(13)` that upstream creates anew for each language also draws the same 19 distractors and the same shuffle for every twin. In other words, this en file is exactly upstream's en construction.

1 deviation from the instructions: the instructions wrote the criteria conversion as `.replace("."," : ")`, but the upstream code (bench_local.py:180, laya_eval.render_label) uses `.replace(".", ": ")`. MASSIVE intent labels contain no `.`, so either way the result is the same, of the form `alarm set`. The code was followed.

E4 translation: the 30 sentences were translated by an LLM in a single pass, preserving meaning, tone and negation (row 7 "I'm not planning to cancel", 10 "I don't want to cancel", 11 "I don't need a refund", 29 "This isn't about cancelling"). No back-translation and no 2nd review were done. The builder asserts, row by row, the pairing of the start of each original with its translation (`PROBE_EN`). "소비자원" was rendered as "the consumer protection agency", and "2만 원" as "20,000 won".

### 1.3 Statistics

- Accuracy: x/n with a 95% Wilson CI (`P0c_analyze.wilson`).
- Paired comparison: exact two-sided McNemar (`P0c_analyze.mcnemar_exact`). b = only A correct, c = only B correct. Δ is shown additionally with a paired Wald 95% CI (inaccurate when b+c is small).
- macro-F1: over the classes present in gold only (the "present classes" of the instructions), plus gold∪pred for reference. upstream's macro-F1 is based on option position indices (bench_local.py:126-133; the shuffled position is the class), so it is not compared with these values.
- noul: the `p >= 0.5` accuracy, the number of positives, and separately the AUROC of p(true) (Mann–Whitney, ties 0.5). AUROC asks, independently of the threshold, "does p move in the label's direction depending on the state?". With 5–10 expected positives, the AUROC uncertainty is also large (on the order of ±0.2).
- ECE and mean_confidence are the report's `overall` values (15 bins, based on answer_confidence). The analyzer asserts that the accuracy·mean_confidence recomputed from `cases` equal `overall`.

### 1.4 Execution

- All model runs are `laya-evals run --device cpu --batch-size 8 --slice qid` (CPU fp32), revision 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851. The torch threads of the laya-evals processes are at the defaults (intra 10 = `OMP_NUM_THREADS`, inter-op 14), and the custom E3 script uses `torch.set_num_threads(10)`, `set_num_interop_threads(1)`.
- scenario-18 has the same questions on every row, so rows were grouped by 8 (13 chunks). intent-20 has a different option set on every row, so all 100 rows get a standalone forward (`timing.rows_alone=100`). upstream `laya_eval.py` packs the 100 rows into a single collated forward to score them.
- Another job (a tokenizer/routing check) ran concurrently on the same machine. The metrics are accuracy and calibration only; the latency fields of the reports are not cited.

## 2. E1: MASSIVE scenario-18, ko vs en

Sanity check: the two ko runs equal the P0c runs, with argmax 100/100 and a maximum answer_confidence difference of 0.0000 (same questions and rows, CPU fp32 determinism).

### 2.1 Accuracy and calibration (n=100)

| Questions | Utterances | Checkpoint | Correct (acc) | 95% Wilson CI | macro-F1 (10 gold classes) | macro-F1 (gold∪pred) | mean answer_confidence | ECE | acc@50%cov |
|---|---|---|---|---|---|---|---|---|---|
| Korean descriptions | ko | multilingual | 52/100 (0.52) | 0.42-0.62 | 0.550 | 0.367 | 0.747 | 0.250 | 0.76 |
| Korean descriptions | en | multilingual | 62/100 (0.62) | 0.52-0.71 | 0.646 | 0.431 | 0.772 | 0.168 | 0.88 |
| Korean descriptions | en | english (reference) | 50/100 (0.50) | 0.40-0.60 | 0.506 | 0.337 | 0.888 | 0.388 | 0.70 |
| key rendering | ko | multilingual | 35/100 (0.35) | 0.26-0.45 | 0.357 | 0.255 | 0.816 | 0.466 | 0.50 |
| key rendering | en | multilingual | 56/100 (0.56) | 0.46-0.65 | 0.576 | 0.412 | 0.856 | 0.311 | 0.92 |
| key rendering | en | english (reference) | 65/100 (0.65) | 0.55-0.74 | 0.634 | 0.453 | 0.953 | 0.326 | 0.82 |

Reference (P0c, same questions and rows): english checkpoint with ko utterances + Korean descriptions = 31/100 (results/poc/P0c_20261002.md R1).

### 2.2 Paired comparisons (same 100 ids)

| Comparison | A | B | A correct | B correct | Both | b (only A) | c (only B) | Δ = B−A (95% CI) | McNemar p | argmax agreement |
|---|---|---|---|---|---|---|---|---|---|---|
| Korean descriptions: ko vs en (ml) | ko/ml | en/ml | 52 | 62 | 38 | 14 | 24 | +0.10 (-0.02..+0.22) | 0.1433 | 50/100 |
| Korean descriptions: en, ml vs english | en/ml | en/english | 62 | 50 | 46 | 16 | 4 | -0.12 (-0.20..-0.04) | 0.0118 | 62/100 |
| key rendering: ko vs en (ml) | ko/ml | en/ml | 35 | 56 | 32 | 3 | 24 | +0.21 (+0.12..+0.30) | 4.9e-05 | 53/100 |
| key rendering: en, ml vs english | en/ml | en/english | 56 | 65 | 54 | 2 | 11 | +0.09 (+0.02..+0.16) | 0.0225 | 71/100 |
| ko: Korean descriptions vs key rendering (ml) | ko/kodesc | ko/keydesc | 52 | 35 | 32 | 20 | 3 | -0.17 (-0.26..-0.08) | 4.9e-04 | 58/100 |
| en: Korean descriptions vs key rendering (ml) | en/kodesc | en/keydesc | 62 | 56 | 51 | 11 | 5 | -0.06 (-0.14..+0.02) | 0.2101 | 68/100 |
| en: Korean descriptions vs key rendering (english) | en/kodesc | en/keydesc | 50 | 65 | 50 | 0 | 15 | +0.15 (+0.08..+0.22) | 6.1e-05 | 76/100 |

"Does the en advantage change with the questions?": it does. With key rendering (English options), en − ko = +0.21 (p<0.001); with Korean descriptions, +0.10 (n.s.). Korean descriptions raise ko by +0.17 (p<0.001) and lower en by −0.06 (n.s.). The difference-in-differences is +0.11, but this design does not test it (indicative). The description language and the amount of information change together (the same confound as noted for P0c), so this must not be read as a "language-match effect" alone.

The english reference runs have different conditions when read as an "upper bound". On the Korean-description questions, the english checkpoint truncates the options to 9 tokens because of its head budget of 192 (18/18 options, 100/100 rows; §6.3 head-budget table). So en/english 0.50 is not an upper bound but the value under a condition in which the options cannot be read. Only the key-rendering questions have no truncation, and there english beats multilingual (0.65 vs 0.56, p=0.023).

### 2.3 Where the difference comes from

Correct answers per gold class (multilingual ko | en | reference en/english):

| gold | n | Korean descriptions ko | Korean descriptions en | Korean descriptions en/english | key rendering ko | key rendering en | key rendering en/english |
|---|---|---|---|---|---|---|---|
| iot | 21 | 8 | 5 | 1 | 3 | 2 | 6 |
| play | 17 | 1 | 11 | 3 | 0 | 10 | 11 |
| weather | 13 | 10 | 13 | 13 | 10 | 13 | 13 |
| datetime | 9 | 6 | 7 | 8 | 5 | 7 | 9 |
| news | 9 | 6 | 6 | 7 | 6 | 7 | 8 |
| alarm | 7 | 6 | 7 | 7 | 5 | 7 | 7 |
| audio | 7 | 1 | 4 | 5 | 0 | 2 | 5 |
| general | 7 | 5 | 2 | 0 | 0 | 1 | 0 |
| takeaway | 6 | 5 | 3 | 3 | 2 | 3 | 3 |
| music | 4 | 4 | 4 | 3 | 4 | 4 | 3 |

Post-hoc breakdown, multilingual:

| Questions | Subset | n | ko correct | en correct | b (only ko) | c (only en) | McNemar p |
|---|---|---|---|---|---|---|---|
| Korean descriptions | gold = play | 17 | 1 | 11 | 1 | 11 | 0.0063 |
| Korean descriptions | gold ≠ play | 83 | 51 | 51 | 13 | 13 | 1.0000 |
| key rendering | gold = play | 17 | 0 | 10 | 0 | 10 | 0.0020 |
| key rendering | gold ≠ play | 83 | 35 | 46 | 3 | 14 | 0.0127 |

All 11 correct en answers on the `play` rows contain the word "play" verbatim in the utterance ("play my rock playlist", "play a nirvana playlist", etc.). 14 of the 17 en `play` rows contain that word, and none of the rows without it was answered correctly. The ko utterances of the same rows ("내 락 플레이리스트 재생" (play my rock playlist), "이승환 노래 무엇이든 재생해줘" (play any Lee Seung-hwan song)) get caught on '재생/음악' ('play/music'), which the music description ("음악 취향, 재생 설정": music taste, playback settings) and the play description ("음악, 라디오, … 재생": music, radio, … play) share, and 14 of them went to music (answer_confidence 0.43–1.00, 12 of the 14 at 0.74 or above). So the penalty on the Korean-description questions is a single-class lexical-anchoring effect, "the English utterance overlaps the option key literally", and on the other 83 rows ko and en are the same (51 vs 51, with 13 differing cases each way). This breakdown was chosen after seeing the results, so it is not confirmatory.

## 3. E2: MASSIVE intent-20 (upstream-faithful), ko vs en + Track A reproduction

### 3.1 Accuracy and calibration (n=100, 20 options, random 0.05)

| Utterances | Checkpoint | Correct (acc) | 95% Wilson CI | macro-F1 (gold classes) | macro-F1 (gold∪pred) | mean answer_confidence | ECE | acc@50%cov |
|---|---|---|---|---|---|---|---|---|
| ko | multilingual | 47/100 (0.47) | 0.38-0.57 | 0.374 | 0.304 | 0.777 | 0.311 | 0.68 |
| en | multilingual | 71/100 (0.71) | 0.61-0.79 | 0.658 | 0.503 | 0.888 | 0.233 | 0.92 |
| en | english (reference) | 82/100 (0.82) | 0.73-0.88 | 0.752 | 0.674 | 0.958 | 0.138 | 0.98 |
| ko | english (reference) | 11/100 (0.11) | 0.06-0.19 | 0.068 | 0.041 | 0.790 | 0.680 | 0.14 |

### 3.2 Paired comparisons

| Comparison | A | B | A correct | B correct | Both | b (only A) | c (only B) | Δ = B−A (95% CI) | McNemar p | argmax agreement |
|---|---|---|---|---|---|---|---|---|---|---|
| ko vs en (multilingual) | ko/ml | en/ml | 47 | 71 | 40 | 7 | 31 | +0.24 (+0.13..+0.35) | 1.2e-04 | 47/100 |
| en: multilingual vs english | en/ml | en/english | 71 | 82 | 65 | 6 | 17 | +0.11 (+0.02..+0.20) | 0.0347 | 69/100 |
| ko: english vs multilingual | ko/english | ko/ml | 11 | 47 | 2 | 9 | 45 | +0.36 (+0.23..+0.49) | 7.3e-07 | 11/100 |

### 3.3 Against upstream (Track A reproduction check, laya-evals path)

The upstream accuracy·ECE are BENCHMARKS.md:71 (ko) and :117 (en). mean_confidence and acc@50%cov were taken from `refreshed_clamped` in research/results/cpu_51_language_sweep_refreshed.json (laya 0.3.20, x86 CPU, `research/eval/laya_eval.py`).

| Utterances | Checkpoint | Measured acc | upstream acc | Δ | Within ±0.03 | Measured ECE / upstream | Measured mean conf / upstream | Measured acc@50%cov / upstream |
|---|---|---|---|---|---|---|---|---|
| ko | multilingual | 0.470 | 0.470 | +0.000 | Yes | 0.3108 / 0.3108 | 0.7773 / 0.7773 | 0.68 / 0.68 |
| en | multilingual | 0.710 | 0.710 | +0.000 | Yes | 0.2333 / 0.2333 | 0.8876 / 0.8876 | 0.92 / 0.92 |
| en | english | 0.820 | 0.820 | +0.000 | Yes | 0.1383 / 0.1382 | 0.9583 / 0.9582 | 0.98 / 0.98 |
| ko | english | 0.110 | 0.110 | +0.000 | Yes | 0.6804 / 0.6804 | 0.7904 / 0.7904 | 0.14 / 0.14 |

- In all 4 cells the accuracy is exactly the same, and ECE·mean confidence agree to the fourth decimal place (the 0.0001 difference for english/en is of a size consistent with laya-evals rounding the probabilities in the report to 4 decimals; the cause was not verified). H1 (01_laya_analysis.md:262, multilingual 0.470 ± 0.03, english 0.110 ± 0.03) holds on this path.
- The scoring method differs: laya-evals ran a standalone forward per row with `Router.predict` (rows_alone 100), while upstream padded the 100 rows and extracted the logits in one packed forward. At this aggregate resolution the difference did not show. A row-level logit comparison was not possible because upstream did not commit its per-case outputs.
- The confidence of the english checkpoint is the "as served" value after laya's temperature clamp (`choice:11+` 0.1006 → 0.5). This is the same condition as upstream's `refreshed_clamped`, so the comparison holds (BENCHMARKS.md:13-25).
- upstream 300-row reference values (T4, options shuffled per row; third_party/laya/research/results/t4_colab_benchmark.json `suites.massive_intent.*`, laya version not recorded): multilingual ko 0.490 / en 0.657 (en − ko +0.167). For scenario, ko 0.423 / en 0.560 (+0.137). These lie within our n=100 Δ CIs (intent +0.13..+0.35, scenario key rendering +0.12..+0.30). They share the first 100 rows, so this is not an independent reproduction.

### 3.4 Where the difference comes from

| scenario family (gold intent prefix) | n | ko correct | en correct | en − ko |
|---|---|---|---|---|
| iot | 21 | 8 | 11 | +3 |
| play | 17 | 10 | 13 | +3 |
| weather | 13 | 9 | 13 | +4 |
| datetime | 9 | 2 | 7 | +5 |
| news | 9 | 6 | 5 | -1 |
| alarm | 7 | 4 | 7 | +3 |
| audio | 7 | 4 | 5 | +1 |
| general | 7 | 3 | 6 | +3 |
| takeaway | 6 | 1 | 3 | +2 |
| music | 4 | 0 | 1 | +1 |

Post-hoc breakdown: split by whether the en utterance contains a word of the gold intent key (3 or more characters, e.g., "alarm"/"set" of `alarm_set`) as a substring.

| Subset | n | ko correct | en correct | b (only ko) | c (only en) | McNemar p |
|---|---|---|---|---|---|---|
| en utterance contains a gold key word | 44 | 27 | 41 | 2 | 16 | 0.0013 |
| en utterance contains no gold key word | 56 | 20 | 30 | 5 | 15 | 0.0414 |

Unlike scenario, the intent-20 penalty is not concentrated in one class but spread across the families (en ≥ ko in 9 of the 10 families). The gap is larger on rows where a key word overlaps (+14/44) and remains on rows without overlap (+10/56). This is a crude post-hoc indicator, but it points toward lexical anchoring on the English option text coexisting with some other comprehension gap. The mean answer_confidence when correct / when wrong is ko/ml 0.912 / 0.658 and en/ml 0.925 / 0.796.

## 4. E3: cross-lingual embedding alignment (an indicator, not a retrieval benchmark)

Method: the 100 ko sentences and their 100 en twins were embedded with `laya.embed_fn_from_agent(agent)` (defaults max_length 512, batch 32, mean pool excluding padding; the function upstream uses for its shortlist). After L2 normalization, a cosine matrix S (ko × en) was built, and for each query the 100 items of the other language were ranked to find the rank of the twin. Ties go to the lower index. dup-aware also counts, for the 3 ko duplicate pairs (6 queries), the other twin of the same ko sentence as correct. **mmBERT is not a model trained for sentence embeddings.** The multilingual encoder is from the mmBERT-base family (ModernBERT architecture, hidden 768, 22 layers, vocab 256,000) and the english one from the ModernBERT-large family (hidden 1024, 28 layers, vocab 50,368) (each `encoder/config.json`). Both train a decision head on top of an MLM encoder, without contrastive training for sentence embeddings. upstream also notes in this function's docstring that a dedicated bi-encoder is usually better (laya/shortlist.py:129-131). So these values are only an indicator of how close the two languages' representations are, not a claim about retrieval performance.

| Checkpoint | ko→en P@1 (strict / dup-aware) | ko→en P@5 | en→ko P@1 (strict / dup-aware) | en→ko P@5 | twin median rank ko→en / en→ko | mean cos, true pairs | mean cos, random pairs (sd) | difference (in random sd units) | within-language off-diagonal mean cos ko / en | tokens per utterance ko / en |
|---|---|---|---|---|---|---|---|---|---|---|
| multilingual | 0.19 / 0.19 | 0.43 | 0.31 / 0.32 | 0.45 | 9 / 8 | 0.737 | 0.642 (0.135) | +0.095 (0.7) | 0.705 / 0.635 | 8.7 / 6.0 |
| english | 0.03 / 0.03 | 0.07 | 0.01 / 0.01 | 0.07 | 46 / 46 | 0.800 | 0.794 (0.072) | +0.005 (0.1) | 0.936 / 0.802 | 20.4 / 6.0 |

- multilingual: P@1 is 19–31x chance (0.01), and the median rank of the twin is 8th–9th out of 100. The true pair is the maximum of both its row and its column in 15/100 cases. The two language spaces are only partially aligned. The cos difference between true and random pairs is only 0.7x the sd of the random-pair distribution. ko→en (0.19) is lower than en→ko (0.31), which goes together with the higher mean cos among Korean embeddings (0.705 vs 0.635), i.e., the ko space is more clustered (observed only; the cause was not verified).
- english: at chance level (P@1 0.03 / 0.01, difference +0.005). Korean utterances are split at the byte level into 20.4 tokens per utterance (multilingual 8.7), and the mean cos among Korean sentences is 0.936: the Korean sentences collapse almost to a single point.
- This weak alignment points in the same direction as the Korean penalty of E1/E2, but it is not evidence that it causes the accuracy difference (correlation only; no intervention experiment).

## 5. E4: is the noul collapse specific to Korean? (P0 probe, 30 rows, Korean vs English state)

The comparison is as follows: the Korean side is the existing reports (results/poc/P0b_V0_v1_multilingual.json, P0b_V0_v1_english.json, P0b_V1_criteria_multilingual.json), and the English side is this run. The question bytes are identical (questions_sha256 match; analyzer assert). The 4 noul questions have only English instructions and no criteria, so the question side is fully English and the only thing that changes is the state language. intent·complexity·frustration keep their Korean criteria, so the English-state side is a mixed condition of English state and Korean options.

### 5.1 Per question (v1 schema)

Cell notation: choice/noul `correct/30`. noul additionally gives `predicted positives / expected positives`, the AUROC of p(true) (0.5 = no ranking information), and the p(true) min–max. frustration gives the MAE, the exact level (argmax), level 0 chosen by argmax / round(score) (expected 18/30), and the score range.

| qid | Baseline | KO / multilingual (P0b V0) | EN / multilingual | KO / english (P0b V0) | EN / english |
|---|---|---|---|---|---|
| intent | majority 5/30 | 12/30 | 16/30 | 7/30 | 14/30 |
| is_urgent | always-no 25/30 | 25/30, pos 0 / 5, AUROC 0.86, p 0.00–0.46 | 26/30, pos 1 / 5, AUROC 0.85, p 0.00–0.94 | 26/30, pos 3 / 5, AUROC 0.81, p 0.03–0.69 | 28/30, pos 3 / 5, AUROC 1.00, p 0.00–0.83 |
| refund_requested | always-no 24/30 | 25/30, pos 5 / 6, AUROC 0.91, p 0.00–0.89 | 25/30, pos 3 / 6, AUROC 0.90, p 0.00–0.96 | 22/30, pos 2 / 6, AUROC 0.61, p 0.00–0.91 | 30/30, pos 6 / 6, AUROC 1.00, p 0.00–0.96 |
| churn_risk | always-no 24/30 | 24/30, pos 2 / 6, AUROC 0.92, p 0.00–0.86 | 25/30, pos 3 / 6, AUROC 0.80, p 0.00–0.98 | 22/30, pos 6 / 6, AUROC 0.68, p 0.01–0.91 | 29/30, pos 5 / 6, AUROC 0.99, p 0.00–0.91 |
| needs_llm | always-no 20/30 | 19/30, pos 3 / 10, AUROC 0.37, p 0.00–0.96 | 18/30, pos 4 / 10, AUROC 0.41, p 0.00–0.98 | 15/30, pos 17 / 10, AUROC 0.65, p 0.02–1.00 | 20/30, pos 0 / 10, AUROC 0.65, p 0.00–0.43 |
| frustration | always-0 MAE 0.700 | MAE 1.084, exact 5/30, L0 0 / 0, score 1.01–2.37 | MAE 1.207, exact 7/30, L0 2 / 0, score 0.66–2.39 | MAE 0.880, exact 16/30, L0 26 / 4, score 0.31–1.57 | MAE 0.975, exact 14/30, L0 10 / 0, score 0.70–1.74 |
| complexity | majority 12/30 | 13/30 | 11/30 | 13/30 | 11/30 |
| binary total /120 | always-no 93 | 93 | 94 | 85 | 107 |
| noul mean AUROC | 0.50 | 0.76 | 0.74 | 0.69 | 0.91 |

Mean answer_confidence:

| qid | KO/ml | EN/ml | KO/english | EN/english |
|---|---|---|---|---|
| intent | 0.825 | 0.780 | 0.338 | 0.606 |
| is_urgent | 0.957 | 0.981 | 0.851 | 0.891 |
| frustration | 0.461 | 0.457 | 0.561 | 0.442 |
| refund_requested | 0.905 | 0.898 | 0.930 | 0.865 |
| churn_risk | 0.947 | 0.945 | 0.845 | 0.842 |
| needs_llm | 0.887 | 0.899 | 0.867 | 0.947 |
| complexity | 0.681 | 0.682 | 0.407 | 0.479 |

### 5.2 Paired comparisons (exact McNemar, n=30; for frustration, the exact level by argmax)

| Checkpoint | qid | KO correct | EN correct | b (only KO) | c (only EN) | p |
|---|---|---|---|---|---|---|
| multilingual | intent | 12 | 16 | 2 | 6 | 0.289 |
| multilingual | is_urgent | 25 | 26 | 0 | 1 | 1.000 |
| multilingual | frustration | 5 | 7 | 1 | 3 | 0.625 |
| multilingual | refund_requested | 25 | 25 | 1 | 1 | 1.000 |
| multilingual | churn_risk | 24 | 25 | 1 | 2 | 1.000 |
| multilingual | needs_llm | 19 | 18 | 2 | 1 | 1.000 |
| multilingual | complexity | 13 | 11 | 5 | 3 | 0.727 |
| english | intent | 7 | 14 | 4 | 11 | 0.118 |
| english | is_urgent | 26 | 28 | 1 | 3 | 0.625 |
| english | frustration | 16 | 14 | 8 | 6 | 0.791 |
| english | refund_requested | 22 | 30 | 0 | 8 | 0.008 |
| english | churn_risk | 22 | 29 | 1 | 8 | 0.039 |
| english | needs_llm | 15 | 20 | 6 | 11 | 0.332 |
| english | complexity | 13 | 11 | 6 | 4 | 0.754 |

### 5.3 With criteria (v1b), multilingual

| qid | Expected positives | KO/ml v1 | EN/ml v1 | KO/ml v1b (P0b V1) | EN/ml v1b |
|---|---|---|---|---|---|
| is_urgent | 5 | 25/30, pos 0 (TP 0, FP 0), AUROC 0.86 | 26/30, pos 1 (TP 1, FP 0), AUROC 0.85 | 26/30, pos 1 (TP 1, FP 0), AUROC 0.78 | 26/30, pos 3 (TP 2, FP 1), AUROC 0.82 |
| refund_requested | 6 | 25/30, pos 5 (TP 3, FP 2), AUROC 0.91 | 25/30, pos 3 (TP 2, FP 1), AUROC 0.90 | 18/30, pos 18 (TP 6, FP 12), AUROC 0.90 | 17/30, pos 19 (TP 6, FP 13), AUROC 0.88 |
| churn_risk | 6 | 24/30, pos 2 (TP 1, FP 1), AUROC 0.92 | 25/30, pos 3 (TP 2, FP 1), AUROC 0.80 | 28/30, pos 8 (TP 6, FP 2), AUROC 0.96 | 25/30, pos 9 (TP 5, FP 4), AUROC 0.78 |
| needs_llm | 10 | 19/30, pos 3 (TP 1, FP 2), AUROC 0.37 | 18/30, pos 4 (TP 1, FP 3), AUROC 0.41 | 15/30, pos 15 (TP 5, FP 10), AUROC 0.51 | 17/30, pos 11 (TP 4, FP 7), AUROC 0.50 |
| binary total /120 (always-no 93) | | 93 | 94 | 87 | 85 |
| noul mean AUROC | | 0.76 | 0.74 | 0.79 | 0.74 |

KO vs EN McNemar for v1b (per question): is_urgent p=1.000, refund_requested 1.000, churn_risk 0.375 (KO 28 vs EN 25), needs_llm 0.754. With the (Korean) criteria attached, the collapse of refund_requested toward true (positives 18 → 19) and the FP increase of needs_llm are the same with an English state. "churn_risk + Korean criteria", the only binary that clearly beat always-no in P0b (KO 28/30, baseline +4), dropped to 25/30 with an English state (baseline +1, TP 5 / FP 4) (McNemar p=0.375). This signal cannot be considered stable at n=30.

### 5.4 Negation rows (P0 rows 4, 7, 10, 11, 29)

| Row | Negated target | Expected intent | KO/ml p / intent | EN/ml p / intent | EN/english p / intent | KO/ml v1b p | EN/ml v1b p |
|---|---|---|---|---|---|---|---|
| 4 | churn_risk | refund | 0.13 / billing_question | 0.01 / refund | 0.26 / refund | 0.66 | 0.13 |
| 7 | churn_risk | technical_help | 0.03 / cancellation | 0.01 / cancellation | 0.31 / cancellation | 0.22 | 0.22 |
| 10 | churn_risk | billing_question | 0.01 / billing_question | 0.02 / cancellation | 0.49 / cancellation | 0.35 | 0.34 |
| 11 | refund_requested | billing_question | 0.65 / refund | 0.84 / refund | 0.24 / billing_question | 0.87 | 0.76 |
| 29 | churn_risk | other | 0.00 / cancellation | 0.01 / cancellation | 0.21 / cancellation | 0.03 | 0.23 |

The intent errors toward the negated target (rows 7, 11, 29) remain with an English state (EN/ml row 7 cancellation, 11 refund + refund_requested 0.84, 29 cancellation). Row 10 even newly went to cancellation in English. H7 (negation failure) is not specific to Korean on these 5 rows either (only 5 rows, so indicative). The intent of the english checkpoint runs under a condition where the Korean criteria are truncated and unreadable (§6.3), so it is not interpreted here.

### 5.5 Answer: is the noul collapse specific to Korean?

No (n=30, indicative).
1. With the same checkpoint (multilingual), giving an English state moves the noul total only from 93 to 94/120, and the per-question McNemar is p=1.000 for all 4. The positive prediction counts are is_urgent 0 → 1, refund 5 → 3, churn 2 → 3, needs_llm 3 → 4 (expected 5/6/6/10): in English too they pile up on no.
2. Giving the same English sentences to the english checkpoint yields 107/120 (refund 30/30, churn 29/30, is_urgent 28/30) with a mean AUROC of 0.91. So the noul questions of this probe are answerable, and the no bias is a property of the multilingual checkpoint.
3. Ranking information exists in multilingual too, regardless of language: the AUROC of is_urgent·refund·churn is KO 0.86/0.91/0.92 and EN 0.85/0.90/0.80. p(true) just hardly ever exceeds 0.5 (the maximum for KO is_urgent is 0.46). It is closer to "reads the state but is pressed below the 0.5 threshold" than to "cannot read the state". The exception is needs_llm, with AUROC 0.37–0.41 in both languages, so even its ranking is reversed (consistent with the P0 note that the question definition itself is ambiguous). With 5–10 expected positives, the AUROC CI is about ±0.2.
4. The avoidance of frustration level 0 is also unrelated to language: L0 argmax 0/30 → 2/30, MAE 1.084 → 1.207 (English is worse).

## 6. Key observations, limitations, next steps

### 6.1 Observations

1. The Korean penalty is real, but its size depends on the language of the option text. In the upstream format (English key rendering), en − ko = +0.21 (scenario) and +0.24 (intent), both with p ≤ 1.2e-04. In the PoC format (Korean prose descriptions), scenario is +0.10 (p=0.14), and the whole difference comes from the single class `play`, where the English utterances contain the key word "play" literally; on the other 83 rows ko and en are the same. In intent-20 too, the gap is larger on rows where a key word overlaps. Lexical anchoring on English options is a large share of the penalty, and Korean descriptions close part of it. A comprehension gap remains (20/56 vs 30/56 even on rows without a key word, p=0.04).
2. The Track A reproduction holds exactly on the laya-evals path: the 4 cells ko/en × multilingual/english have Δ 0.000, and the ECE·mean confidence differences are within 0.0001. The difference between the standalone per-row forward and upstream's packed forward does not show at this resolution. Korean numbers measured with our harness can be compared with upstream numbers on the same scale.
3. The no bias of noul, the negation errors (5 rows) and the avoidance of frustration level 0 are properties of the multilingual checkpoint, not specific to Korean. They were unchanged with the same English content, and the english checkpoint got 107/120 on the noul questions for the same English sentences. In the Korean PoC, these weaknesses will not be solved by "writing better Korean"; they are a matter of thresholds·calibration (Track E) or of the choice of checkpoint·path.

### 6.2 Limitations

- n=100 and n=30. At n=100, the CI of Δ 0.10 includes 0. The probe has ad-hoc labels from 1 annotator and a translation from 1 translator.
- The post-hoc breakdowns (§2.3 `play`, §3.4 key-word indicator) were chosen after seeing the results, so they serve only to generate hypotheses.
- Although the E1/E2 comparisons are "same content", MASSIVE's localization means some pairs differ in entities and phrasing (§1.1).
- Only one fixed option order was examined. upstream reported an option-order flip rate of 0.23 for multilingual MASSIVE intent en (t4_colab_benchmark.json `option_order_robustness`). Whether the ko/en gap persists when the order changes was not measured (Track C1).
- english checkpoint reference runs: the options are truncated on the Korean-description questions (scenario, 100/100 rows) and on the probe intent (30/30 rows). In intent-20 too, 75/100 rows are truncated, and in 50/100 rows the `iot_hue_light*` options become indistinguishable (10 of these rows include the gold label). upstream's english 0.82 is under the same condition.

### 6.3 Head budget (tokenizer only, `K2_head_budget.md`)

| File (questions shared by the ko/en twins) | Checkpoint (head_max_len) | qid | Options | Cap per option | Truncated rows | Indistinguishable rows |
|---|---|---|---|---|---|---|
| K2_scen18_kodesc | multilingual (256) | scenario | 18 | None | 0 | 0 |
| K2_scen18_keydesc | multilingual (256) | scenario | 18 | None | 0 | 0 |
| K2_intent20 | multilingual (256) | intent | 20 | None | 0 | 0 |
| probe_en (7 questions) | multilingual (256) | all | 2–6 | None | 0 | 0 |
| K2_scen18_kodesc | english (192) | scenario | 18 | 9 | 100 (all 18 options) | 0 |
| K2_scen18_keydesc | english (192) | scenario | 18 | None | 0 | 0 |
| K2_intent20 | english (192) | intent | 20 | 8 (none on some rows) | 75 | 50 |
| probe_en | english (192) | intent | 6 | 29 | 30 | 0 |
| probe_en | english (192) | the 4 noul·frustration·complexity | 2–4 | None | 0 | 0 |

multilingual read all the questions in this audit without truncation. Therefore the multilingual ko vs en comparisons have identical head conditions (the head does not depend on the state, and the ko and en question bytes are the same).

### 6.4 Proposed next steps (for the project owner to decide)

- Schema: there is one more reason to keep "Korean prose descriptions by default" of 04:76 (ko +0.17, p<0.001; en −0.06, n.s.). However, options whose descriptions share vocabulary ('재생' (play) in play/music) break down especially in Korean, so remove the overlap at the domain-definition stage (the same as the P0c recommendation).
- Track E: multilingual noul has AUROC 0.8–0.9 but collapses at the 0.5 threshold. Try fitting per-question thresholds or a noul:2 temperature refit on the P1 label set (N ≥ 200). Do not fit them on the 30-row probe.
- Path alternative (hypothesis): on this data, en/english beat ko/ml by +0.35 on intent-20, +0.30 on scenario key rendering and +14/120 on the probe noul. The English is MASSIVE's original text and the probe English is a human-level translation, so these values are only an upper bound for a "ko→en translation + english checkpoint (English criteria)" path. A comparison that includes real MT quality and latency is worth measuring separately on the P1 set.
- Track A: the intent-20 ko/en reproduction can be recorded as passed (based on the throwaway files; the formal record should be made once more with the 04 builder output).
- Track C1: check the ko/en gap under option permutations and the `iot→alarm` first-position bias (7–9 cases in en as well).

## 7. Commands (cwd = project root, all run after `source env.sh`)

| Step | Command (`.venv/` is not included in the public repository) |
|---|---|
| Build | `.venv/bin/python results/korean_support/K2_build.py > results/korean_support/K2_build.log 2>&1` |
| Validate | `.venv/bin/laya-evals validate results/korean_support/<file>.jsonl` × 8 → results/korean_support/K2_validate.log (all exit 0) |
| 13 model runs | `bash results/korean_support/K2_run.sh`. Each line is `.venv/bin/laya-evals run <jsonl> --model <multilingual\|english> --device cpu --batch-size 8 --slice qid --json results/korean_support/<id>.json --markdown results/korean_support/<id>.md > results/korean_support/<id>.log 2>&1` |
| E3 | `.venv/bin/python results/korean_support/K2_embed_align.py > results/korean_support/K2_E3_embed_align.log 2>&1` |
| Head budget | `.venv/bin/python results/korean_support/K2_head_budget.py > results/korean_support/K2_head_budget.md` |
| Analysis | `.venv/bin/python results/korean_support/K2_analyze.py` → results/korean_support/K2_analysis.md |

## 8. Outputs (all in results/korean_support/)

- Builder·run·analysis scripts: K2_build.py, K2_run.sh, K2_embed_align.py, K2_head_budget.py, K2_analyze.py
- JSONL: K2_scen18_{kodesc,keydesc}_{ko,en}.jsonl, K2_intent20_{ko,en}.jsonl, probe_en.jsonl, K2_probe_en_v1b.jsonl, and K2_build_meta.json (sha256, questions_sha256, row_ids, pair-check results)
- Reports (.json/.md/.log): K2_scen18-{kodesc,keydesc}_ko_multilingual, K2_scen18-{kodesc,keydesc}_en_{multilingual,english}, K2_intent20_{ko,en}_{multilingual,english}, K2_probe-en-v1_{multilingual,english}, K2_probe-en-v1b_multilingual
- Logs·analysis: K2_build.log, K2_validate.log, K2_run_times.log, K2_times.log, K2_E3_embed_align.{json,log}, K2_head_budget.md, K2_analysis.md
- run card: K2_20261002.md
- `cards/`, `fetch_cards.sh` and `part2_*` in the same directory are outputs of another job (not touched).

**English** | [한국어](paired_ko_en_audit.ko.md)
