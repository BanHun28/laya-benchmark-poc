# Laya Korean support audit: documentation · tokenizer · routing

| Field | Value |
|---|---|
| Date / wall time | 2026-10-02 (KST), 15:05–15:34 (about 29 min; execution time within it: tokenizer script about 1 min, the other scripts a few seconds each) |
| Scope | Documentation evidence, tokenizer efficiency, routing decisions. **No model forward** (only the tokenizer and `laya.lang.analyse` / `Router().route` are used) |
| Target | upstream `third_party/laya` @4aa6761 (not included in the public repository; recreate it by cloning https://github.com/NandhaKishorM/laya at commit 4aa6761), installed laya 0.3.23 (`lang.py` is byte-identical to upstream. `router.py` differs only in the `resolve_model_spec` helper and its `Tuple` import; the routing branches are identical, and the installed copy's line numbers are shifted by −16. `common.py` is byte-identical) |
| Checkpoints | `models/laya*` (not included in the public repository) → the `convaiinnovations/laya@55cf4c4` bundle. The `model.safetensors` (sha256 `9d628fd9…`) and `tokenizer.json` (`609d8f4c…`) of the `multilingual/` subfolder are identical to the standalone repo `convaiinnovations/laya-multilingual@e4e9ddf` (`cards/*/api_model_blobs*.json`), so the standalone card describes these weights |
| Environment | Python 3.12.12, transformers 5.18.0, tokenizers 0.23.2, datasets 5.0.1 |
| Outputs | This document + 5 scripts + JSON/logs (§5) |

## 0. Summary of conclusions

| Layer | Verdict | Strength of evidence |
|---|---|---|
| **Stated in the docs** | The `language:` tag of the `laya-multilingual` card contains `ko`, but this list of 50 codes is exactly the list of MASSIVE evaluation languages. The only "supported/trained languages" statement is "100+ languages". The Korean evidence consists entirely of **zero-shot MASSIVE numbers** (0.45–0.49, n=100/300) and a **presentation check** (10 ko sentences, written by a non-native speaker). **Korean decision-training data is not documented anywhere.** upstream states explicitly "Neither checkpoint trained on … MASSIVE or XNLI" | Evaluation: moderate (small n, mixed sources) / training: no evidence |
| **Tokenizer** | multilingual (mmBERT = Gemma 2, 256k) splits Korean **essentially into syllables**: 0.98 tokens per syllable, UNK 0, byte-fallback 0.1%, and 1.5x the token count of English with the same meaning (median). english (ModernBERT 50k) uses 2.3 tokens per syllable, and 91% of its tokens are sub-character byte fragments, so it cannot read Korean. However, NFD input increases the multilingual token count 3.1x | Strong (direct measurement; reproduces P0 `state_tokens` 34 / `input_tokens` 661) |
| **Routing** | Pure Korean, 1 syllable, jamo (ㅋㅋ/ㅠㅠ/ㅇㅋ), mixed Hanja, emoji and NFD all go to multilingual. In contrast, **mixed text with a Latin majority** (pasted API/product names/URLs/errors) and **short Korean inside an English wrapper** (under 10 syllables) go to english. 10 of the 46 inputs fail: 4 fail regardless of default, 6 fail only with the stock `default="english"` | Strong (deterministic rule, code lines cited) |

---

## PART 1. Documentation evidence

### 1.1 Hugging Face model cards (`cards/`)

Collection: `bash results/korean_support/fetch_cards.sh` (`hf download <repo> README.md` + `https://huggingface.co/api/models/<repo>?full=true`).

| repo (sha, lastModified) | `language:` field | Contains `ko` | Korean mentions in the body |
|---|---|---|---|
| `convaiinnovations/laya-multilingual` (e4e9ddf, 2026-09-24) | 51 (`multilingual` + 50 codes) | **Yes** (among 67 tags) | One sentence, L116–118 |
| `convaiinnovations/laya` (55cf4c4, 2026-09-24; byte-identical to the local `models/laya/README.md`) | **No field** (17 tags, 0 language tags) | No | None |
| `convaiinnovations/laya-typed-decisions` (1a793eb) | `[en]` | No | None |
| `jhu-clsp/mmBERT-base` (c595503) | 1,811 ISO 639-3 codes | **Yes** (`kor`, README L775) | None (front matter only) |

- The 50 language codes of the `laya-multilingual` card and the 51 MASSIVE locales of BENCHMARKS.md (50 when zh-CN/zh-TW are merged into zh) have **empty set differences in both directions** (`part1_docs_evidence.json` `benchmarks_51.card_language_codes_vs_massive`). So this tag is a list of "evaluated languages", not a list of "trained/guaranteed" languages.
- Language-related sentences in the card (`cards/convaiinnovations_laya-multilingual/README.md`):
  - L5: `language: [multilingual, en, de, … ja, ko, zh, …]`
  - L15: "Non-autoregressive **System 1 decision model** covering 100+ languages."
  - L20–21: "**use this checkpoint for anything that is not English.**"
  - L116–118: "Per-language, this checkpoint turns near-random into usable: Arabic 0.110 → **0.400**, … Hindi 0.100 → **0.387**, Korean 0.110 → **0.490**, Turkish 0.140 → **0.437**."
  - L146: "Trained from scratch with RLCD: 15,987 updates, 4 epochs, \~4.97 h." (no mention of data or languages)
  - L150–153: "**Ships uncalibrated.** `temperature = [1.0, 1.0, 1.0]` …"
  - L161: "Low-resource languages are weak, not fixed: Swahili 0.210, Tamil 0.250, Amharic 0.110."
- The bundle card (`cards/convaiinnovations_laya/README.md`):
  - L10: "… across 100+ languages."
  - L58: "The same call works in any of 100+ languages. The `Router` detects the script and language and sends non-English text to `laya-multilingual`"
  - L289–291: the Training section describes only the RLCD method and does not mention data or languages.
  - L373: "**English only on root:** Use `laya-multilingual` for anything outside English."
- **The card's Korean numbers come from mixed sources.** In "Korean 0.110 → 0.490", 0.110 is the english value of the CPU 51-language sweep (n=100, `research/results/cpu_51_language_sweep.json`), while 0.490 is the multilingual value of the T4 Colab run (n=300, `research/results/t4_colab_benchmark.json` `suites["massive_intent.ko"]`). They are not a pair from the same run. Turkish (0.140 CPU / 0.437 T4) and Hindi (0.387 T4) follow the same pattern. The current official number is the refreshed **0.470** at BENCHMARKS.md:71 (n=100). Depending on the run, three values exist for the Korean multilingual accuracy: 0.45 (committed, not reproduced) / 0.47 (refreshed) / 0.49 (T4).
- Nowhere in the cards is there a Korean evaluation set, Korean training data, or a statement of Korean-specific limitations.

### 1.2 Encoder: mmBERT-base

**Local config** (`models/laya-multilingual/encoder/config.json`, `rl_agent_config.json`):

| Item | laya-multilingual | laya (english) |
|---|---|---|
| `model_type` | `modernbert` (config L55) | `modernbert` |
| `_name_or_path` | **None** (field absent). The source is `rl_agent_config.json` L2 `"encoder": "jhu-clsp/mmBERT-base"` | `answerdotai/ModernBERT-large` |
| `vocab_size` | 256,000 (L78) | 50,368 |
| `max_position_embeddings` | 8,192 (L52) | 8,192 |
| hidden / layers | 768 / 22 | 1,024 / 28 |
| `max_len` / `head_max_len` | 1,024 / 256 (rl L4–5) | 512 / 192 |
| temperature | `[1.0, 1.0, 1.0]` (uncalibrated) | Fitted values |
| training | updates 15,987, epochs 4, 4.97 h, `fine_tuned_from_checkpoint: false` (rl L19–25) | 7,313 / 1 / 1.96 h |

**mmBERT card** (`cards/jhu-clsp_mmBERT-base/README.md`):
- L775: ` - kor` (language list)
- L1833: "> TL;DR: A state-of-the-art multilingual encoder trained on 3T+ tokens across 1800+ languages …"
- L1884: "**Progressive Language Addition**: Start with 60 high-resource languages, expand to 110 mid-resource languages, then include all 1833 languages in decay phase."
- L1905: "| Pre-training P1 | … | 2.3T | 60 languages, foundational training |"
- L1911: "… FineWeb2-HQ (20 high-resource languages) …"
- L1925: "| Tokenizer | Gemma 2 | Gemma 2 |"
- The card has no benchmark numbers and no mention of Korean.

**mmBERT paper** arXiv:2509.06888 v1 (2025-09-08; `cards/mmbert_paper/`, text conversion `.txt`):
- Abstract: "We introduce mmBERT, an encoder-only language model pretrained on 3T tokens of multilingual text in over 1800 languages."
- txt L220: "We use an identical architecture to ModernBERT, but employ the Gemma 2 tokenizer"
- txt L232: "We start with a set of 60 languages (as well as code) … We then increase this to 110 languages, covering more "mid-resource" languages … Finally, we include all languages/scripts included in FineWeb2 (1833 languages …)."
- txt L238: "We use just 60 languages (plus code languages) in this stage of training"
- **Table 9 `kor` row** (txt L1340): Pretrain **28.4B (1.43%)** / Mid 11.1B (1.84%) / Decay-Eng 1.5B (1.39%) / Decay-Cont 1.5B (1.47%) / Decay-All 1.5B (1.31%) / Total **43.9B**.
  - The pre-training stage uses only 60 languages, so having 28.4B tokens here means that **Korean belongs to the 60 "high-resource" languages of stage 1**.
  - Among the 89 languages of Table 9, it ranks **13th** by pre-training tokens (after eng, rus, cmn, spa, deu, fra, jpn, ita, por, nld, pol, ind).
- **FineWeb2-HQ (20 languages) does not include Korean.** The `language` list of `cards/epfml__FineWeb2-HQ/api_dataset.json` is ru, zh, de, ja, es, fr, it, pt, pl, nl, id, tr, cs, vi, sv, fa, ar, el, da, hu. So in the mid/decay stages, Korean enters as general FineWeb2 data, not as quality-filtered HQ data (Japanese and Chinese enter as HQ).
- "Korean" never appears in the body of the paper. The columns of the per-language results table (Table 7) are ar, de, en, es, fr, hi, ja, ru, tr, vi, zh, without ko. **There are no Korean-specific benchmark numbers.**

**Tokenizer provenance check** (`part1b_tokenizer_origin.py` → `part1b_tokenizer_origin.json`):
- The laya-multilingual `tokenizer.json` and `jhu-clsp/mmBERT-base@c595503` have identical vocab (256,000) and merges (580,604).
- The normalizer and the added tokens are also identical, and both have `byte_fallback: true`.
- The pre_tokenizer differs only in its serialization format (`add_prefix_space: true` vs `prepend_scheme: "always", split: true`).
- On 300 MASSIVE ko sentences, the token ids **match on 300/300**.

### 1.3 Korean evidence in the upstream repository

`grep -rniE "korean|hangul|한국|[가-힣]"` matches 11 files (`part1_docs_evidence.json` `upstream_grep`).

| File:line | Content |
|---|---|
| `BENCHMARKS.md:71` | `ko` row: laya 0.110 / laya-multilingual 0.470 / Δ +0.360 / laya ECE 0.680 / multilingual ECE 0.311 (51-language table, 100 cases per language) |
| `laya/lang.py:4-6` | "English checkpoint collapsing to near-random on non-Latin scripts (Hindi 0.100, Korean 0.103, …)" (T4, n=300) |
| `laya/lang.py:43` | `("hangul", ((0x1100, 0x11FF), (0x3130, 0x318F), (0xAC00, 0xD7AF))),` |
| `laya/router.py:21-22` | "on 20-option MASSIVE intent it scores 0.100 on Hindi and 0.103 on Korean" |
| `research/eval/README.md:290-298, 308-313` | presentation check `--lang ja,ko,hi,tr`. **ko: `score_slot0_identical` −0.570 FAIL (worst of the 4 languages), `score_first_slot_permuted` 0.050 FAIL** |
| `research/eval/README.md:336-348` | choice control: ko K=4 +0.096 PASS. "Korean is closest to the gate, and below 0 at 3 options." |
| `research/eval/README.md:383-385` | "The Korean, Hindi and Turkish states and levels were written by a non-native speaker" |
| `research/eval/presentation_checks.py:133-146` | 10 fixed Korean state sentences and urgency levels |
| `tests/test_router.py:47, 355, 360, 366-368, 1114, 1143` | Hangul detection, brand mixing, Korean after an English turn (16 syllables), Jamo Ext-A regression tests |
| `tests/test_local_e2e.py:59`, `examples/21_routing_without_running.py:34` | Routing example with 1 Korean sentence |
| `laya-ts/src/lang.ts:26`, `laya-ts/tests/tokenizer-parity.test.ts:70` | Hangul ranges of the TS port. "a Hangul syllable … outside the 256k vocab reached the model as <unk> here" (retrospective on a byte_fallback bug in the TS tokenizer) |

**Position of Korean in the 51-language table** (computed by `part1_docs_evidence.py` by parsing the BENCHMARKS.md table):

| Metric | Korean | Median of 51 languages | macro | Rank |
|---|---|---|---|---|
| multilingual accuracy | **0.470** | 0.400 | 0.4008 (BENCHMARKS.md:59) | **18/51** (tied with nl; 17 languages above) |
| multilingual ECE (lower is better) | **0.311** | 0.397 | 0.3911 (:60) | **10/51** |
| Δ (multilingual − english) | +0.360 | | | 4/51 (tied with hi) |

- ko/en ratio: 0.470 / 0.710 (multilingual on en) = **0.662**. Relative to the english checkpoint's en performance of 0.820, it is 0.573.
- 9.4x random (0.05). The n=100 Wilson 95% CI is wide, [0.375, 0.567].
- Neighboring CJK languages: ja 0.640, zh-CN 0.650, zh-TW 0.610. Korean is 0.14–0.18 lower, but this compares n=100 sets, so the ranking is indicative.
- Other Korean numbers (T4 JSON, n=300):
  - intent: english 0.103 (mean confidence 0.953), multilingual 0.490 (ECE 0.308)
  - scenario: 0.127 / 0.423
  - After a multilingual temperature refit (T=2.07, n_heldout 150), ECE 0.320 → 0.101 (`calibration_repair`)

**Locales covered by lang.py** (`lang.py:57-168`, `20-46`):
- Stopword lists: az, bn (romanized Bengali), de, en, es, fr, it, nl, pt, ro, sv. **There is no romanized Korean list.**
- Script ranges: 25 (greek … hangul, kana, han), plus `other` for the rest.
- For non-Latin scripts, `language` is always returned as `None` (`lang.py:581-584`). So Korean is identified only as the "hangul" script, and `language="ko"` never comes out. Korean written only in Hanja becomes `han`, exactly like Chinese.

**Per-language datasets** (research):
- Chinese: `research/evals/zh_decision_bench.jsonl` (224 rows, BENCHMARKS.md:435-450), `research/benchmarks/feishu_zh`, `research/benchmarks/zh_short_commands`, and BENCHMARKS.md:422 "## Community evaluation: zh-CN / zh-TW".
- Spanish: `research/benchmarks/es_phone_turns`.
- **There is no Korean dataset, benchmark or community evaluation.**

### 1.4 RLCD training data (language composition)

- Only the training method is documented: the bundle card L289–291 (RLCD, proper scoring rule, GRPO-style REINFORCE) and the multilingual card L146 (updates/epochs/time) are all there is.
- **The language composition of the training data is given nowhere.**
- The sources marked "in training" in the docs are all English datasets:
  - AG News, BoolQ (README.md:1352-1353 "in training mix")
  - enron spam, phishing emails, MS MARCO relevance, customer-support-tickets queue (BENCHMARKS.md:138-148, `research/scripts/bench_apps.py:94,155,168,185,239`; the benchmark uses only the `language == "en"` rows, :146)
  - The 13 task families of the English checkpoint (`models/laya/eval/results.md`)
- Explicit exclusion (`research/results/t4_colab_benchmark.json:4309`, `research/scripts/build_benchmark_nb.py:760-762`): "ag_news and boolq were in Laya's training mix … **Neither checkpoint trained on typed-decisions, MASSIVE or XNLI.**"
- **Verdict: Korean decision (RLCD) training data is not documented.** The published Korean numbers (MASSIVE) were measured on data explicitly excluded from training. So Korean performance must be interpreted as **cross-lingual zero-shot transfer** from the mmBERT pre-training and the (by the docs, English-centered) RLCD training.

**PART 1 verdict.**
- Korean is documented only as an "evaluated language" (1 card tag, 1 sentence in the body, 1 BENCHMARKS row, 1 presentation-check set).
- It is not documented as a "trained/guaranteed language".
- The encoder-level evidence is strong: in mmBERT, Korean belongs to the 60 high-resource languages of stage 1 and ranks 13th by data volume (28.4B pre-training tokens). It is, however, absent from FineWeb2-HQ.
- The laya-level Korean evidence consists only of zero-shot MASSIVE intent (0.45–0.49, n=100/300, mixed sources) and a 10-sentence presentation check written by a non-native speaker (score position bias FAIL, worst of the 4 languages).
- Unlike Chinese, there is no separate evaluation set or community evaluation.
- Strength of evidence: encoder pre-training **strong** / laya evaluation **weak\~moderate** / laya training **none**.

---

## PART 2. Tokenizer efficiency (no forward)

### 2.1 Setup and definitions (assumptions stated)

**Data**
- MASSIVE: the first 300 `ko` rows (file order) of the test split of `mteb/amazon_massive_intent` rev `940fd47a…`, joined with `en` by `id`. All 300 pairs agree in `id` and `label_text` (assert).
- P0 probe: the 30 `state.message` sentences of `results/poc/P0_probe_sentences.jsonl`.
- KLUE YNAT: `P0c_build.build_ynat()` was imported and reused, and an assert confirmed that the resulting 100 headlines equal `P0c_ynat100.jsonl`.

**Measurement**
- The tokenizer is loaded the same way as in `laya.agent`, with `AutoTokenizer.from_pretrained(<ckpt>/tokenizer)`, and encodes with `add_special_tokens=False`.
- chars = `len(text)` (including spaces). `tok/char*` excludes spaces.
- words = the number of whitespace-separated pieces. MASSIVE ko has spelling artifacts in which particles are split off by a space, as in "시 에", so tokens/word is used only as an auxiliary metric.

**Token categories** (`convert_ids_to_tokens`; for english, ByteLevel characters are mapped back to the original bytes before interpretation)

| Category | Definition |
|---|---|
| `hangul_full` | Contains at least one complete syllable (U+AC00–D7A3) |
| `byte_fallback` | `<0xNN>` |
| `byte_piece` | A byte fragment that is not valid UTF-8 on its own |
| `jamo` | Contains only jamo |
| `space` | `▁` alone |
| `han` | Hanja |
| `other` | Any other token |

- **frag %** = (`byte_fallback` + `byte_piece` + `jamo`) / all tokens, i.e. the share of sub-syllable fragments.
- The definition from a literal reading of the instructions ("every token that is not a complete syllable") is recorded separately as `not_full_syllable_share` (`part2_tokenizer_stats.json`).

**Reproduction check.** Running laya's `serialize_state`, `build_sequence` and `state_room` with the multilingual tokenizer gives `state_tokens` **34** for the P0 message and `input_tokens` **661** for the 7 questions, exactly the P0 measurement (`results/poc/P0_20261002.md:75`). The short message gives 19, the same as the CLI measurement.

### 2.2 Results table (`part2_tokenizer_stats.json` `aggregate`)

| tokenizer / set | n | tok/char | tok/char* | tok/word | tok/syllable | frag % | UNK |
|---|---|---|---|---|---|---|---|
| **multilingual / MASSIVE ko** | 300 | **0.726** | 0.972 | **2.208** | **0.983** | **0.10%** (3 `<0x..>` = 1 syllable '딨') | **0** |
| multilingual / MASSIVE en | 300 | 0.215 | 0.258 | 1.073 | – | 0 | 0 |
| multilingual / P0 probe ko | 30 | 0.682 | 0.879 | 2.827 | 0.945 | 0.17% (the 2 jamo of 'ㅠㅠ' in the input, byte-fallback 0) | 0 |
| multilingual / KLUE YNAT | 100 | 0.794 | 0.998 | 3.304 | 1.105 (including Hanja and punctuation) | 0.00% | 0 |
| english / MASSIVE ko | 300 | 1.698 | 2.273 | 5.163 | **2.299** | **90.61%** | 0 |
| english / MASSIVE en | 300 | 0.221 | 0.266 | 1.107 | – | 0 | 0 |
| english / P0 probe ko | 30 | 1.528 | 1.969 | 6.332 | 2.117 | 82.07% | 0 |
| english / KLUE YNAT | 100 | 1.775 | 2.229 | 7.382 | 2.469 | 91.17% | 0 |

**MASSIVE per-pair token ratio (ko / en)**

| Combination | Median | p90 | p10 | Ratio of totals |
|---|---|---|---|---|
| multilingual for both ko and en | **1.50** | **2.20** | 1.00 | 1.46 |
| english for both ko and en | 3.43 | 5.00 | 2.14 | 3.31 |
| Actual routed combination (ko→multilingual, en→english) | 1.50 | 2.00 | 0.99 | 1.42 |

**multilingual token category breakdown (MASSIVE ko, 2,872 tokens)**
- `hangul_full` 2,678 / `space` 170 (5.9%) / `other` 21 / `byte_fallback` 3.
- The share of "tokens that are not complete syllables" in the literal sense is 6.8%. Most of these are standalone `▁` tokens that arise because the `▁`+syllable combination is not in the vocab; this is a whitespace cost, not fragmentation.

### 2.3 The vocab view: why syllable units (`tokenizers.*.vocab`, `syllable_coverage`)

| | multilingual (Gemma 2, 256k) | english (ModernBERT, 50k) |
|---|---|---|
| Syllables that are single tokens (of all 11,172) | 1,597 | 22 |
| KS X 1001 syllables that are single tokens (of 2,350) | **1,551 (66.0%)** | 22 (0.9%) |
| Pure-Hangul multi-syllable vocab entries | **369** | 1 |
| Vocab entries containing a complete syllable | 2,295 (0.9% of the vocab) | 25 |
| Handling of syllables not in the vocab | byte fallback, 3 `<0xNN>` per syllable | byte-level BPE |

**multilingual**
- With only 369 multi-syllable Korean tokens, Korean is almost 1 token per syllable. A complete-syllable token holds 1.09 syllables on average.
- 34% of the common KS X 1001 syllables (799, e.g., 갉 갊 궂 깠 …) are not in the vocab and are split into 3 byte tokens.
- They are rare in real text, though: 1 (딨) of the 2,922 MASSIVE syllables, and 0 among the 1,262 P0 syllables and the 1,958 YNAT syllables.
- **UNK is practically impossible.** Of the 256 byte tokens, only `<0x09>` (tab) is missing, and all the UTF-8 bytes of Hangul (0xEA–0xED, 0x80–0xBF) are present.

**english**
- 99% of syllables become byte fragments. **UNK is 0 because byte-level BPE structurally never emits UNK.** So UNK 0 is not evidence that Korean can be read.
- The real signal is fragmentation: 91% of the tokens are sub-character byte fragments, at 2.3 tokens per syllable. There are no meaning-bearing tokens, so there are no pre-trained representations either.
- This matches the upstream measurement: english 0.103 on MASSIVE ko (n=300, confidence 0.95), random 0.05.

**NFD input (caveat).** The normalizer of the multilingual tokenizer is only `Replace(" " → "▁")`, with no NFC (`part1b_tokenizer_origin.json`). The laya package has no `unicodedata.normalize` call either (grep: 0 hits).
- Feeding the same MASSIVE ko as NFD (conjoining jamo) increases the tokens 2,872 → 8,866 (**×3.09**), mostly `jamo` (6,734) and `byte_fallback` (822).
- The english tokenizer has an NFC normalizer, so nothing changes (×1.00).
- Routing detects NFD correctly as hangul too (PART 3 #5). So **NFD text from macOS file names or some clipboards enters multilingual as jamo fragments without any warning.**

### 2.4 Token budget (`budget_p0_7_questions`)

- A sequence is built separately for each question (`third_party/laya/laya/common.py:136-193` `build_sequence`, `:250-259` `state_room`; byte-identical to the installed copy). The state budget is `max_len - len(head) - 1`.
- So 7 questions do not split the budget into 7 parts. **The question with the longest head decides the truncation**, and the compute grows to 7 rows.
- Per-question state room of multilingual for the 7 P0 questions (triage_v1 + gateway_v1, Korean criteria):

| intent | is_urgent | frustration | refund_requested | churn_risk | needs_llm | complexity |
|---|---|---|---|---|---|---|
| **896** (binding) | 987 | 956 | 990 | 983 | 979 | 954 |

- Check: head total 416 + 7×(34+1) = 661.

| Checkpoint / text | binding room (tokens) | tok/char | **Characters that fit** (excluding the 5-token JSON wrapper) |
|---|---|---|---|
| multilingual 1024 / Korean (MASSIVE) | 896 | 0.726 | **≈1,227 chars** |
| multilingual 1024 / Korean (P0 message: 41 chars = 29 tokens) | 896 | 0.707 | ≈1,259 chars |
| multilingual 1024 / Korean (YNAT, P0 probe) | 896 | 0.794 / 0.682 | ≈1,121 / 1,306 chars |
| multilingual 1024 / English (MASSIVE en) | 896 | 0.215 | ≈4,152 chars |
| multilingual `max_len=8192` (card L29) / Korean | 8,064 | 0.726 | ≈11,100 chars |
| english 512 / English (MASSIVE en) | 326 | 0.221 | ≈1,449 chars |
| english 512 / Korean (when misrouted) | 326 | 1.698 | ≈189 chars |

- At the default 1,024, Korean fits **about 1,100–1,300 characters** (including spaces) without truncation, about 30% of English by character count.
- In terms of meaning, however, the per-pair token ratio of 1.46 (totals) makes it **about 68% of English for the same content**.
- For the english checkpoint, the Korean criteria themselves are split into bytes, so the intent head grows to 185 tokens (multilingual: 127) and the room shrinks to 326.

**PART 2 verdict.**
- **The multilingual tokenizer supports Korean**: UNK 0, sub-syllable fragmentation ≤0.2%, about 1 token per syllable. Its compression is low, though: with only 369 multi-syllable vocab entries, it uses 1.5x (p90 2.2x) the tokens of English, and about 1.2k characters fit in the default 1,024 budget. Short CS messages (P0: 34 tokens) are no problem.
- There are two risk factors: **NFD input** (×3.1, no NFC normalization) and **34% of KS X 1001 syllables missing from the vocab** (byte fallback for rare syllables).
- **The english tokenizer cannot read Korean.** 91% of its tokens are byte fragments, at 2.3 tokens per syllable. UNK 0 is an illusion.
- Strength of evidence **strong**: direct tokenizer measurement, reproducing P0's 34 / 661.

---

## PART 3. Routing robustness (no model load)

### 3.1 Decision rule and thresholds (`third_party/laya/laya/lang.py`, byte-identical to the installed copy)

```python
# lang.py:364-371
NON_LATIN_FRACTION = 0.2
NON_LATIN_MIN_FRACTION = 0.1
NON_LATIN_MIN_LETTERS = 10
```

```python
# lang.py:573-576  (_analyse_text): non-Latin override, applied only when Latin is the most frequent script
if script == "latin" and _non_latin_words(text) and (
        non_latin >= NON_LATIN_FRACTION or (
            non_latin >= NON_LATIN_MIN_FRACTION and n_non_latin >= NON_LATIN_MIN_LETTERS)):
    script = max((s for s in prof if s != "latin"), key=prof.get)
```

**Rule summary**
- `lang.py:297-320`: the letter count includes only characters for which `isalpha()` holds. **1 Hangul syllable = 1 letter**, and 1 Latin character = 1 letter. Digits, emoji and punctuation are ignored. Characters outside the ranges count as `other`.
- `lang.py:323-326`: the most frequent script is chosen; on a tie, non-Latin wins.
- `lang.py:385-407` `_non_latin_words`: the same script must form **a run of 2 or more characters (`len(w) >= 2`)** that does not start with an uppercase letter. Single-syllable Korean words cannot serve as evidence.
- `lang.py:577-584`: `unknown` (no letters) becomes `is_english=True`. A non-Latin script becomes `language=None, is_english=False`.
- `lang.py:599-641` `_leaf_non_english` (structured states only): each field string must have 7 or more characters (`:620`) and **10 or more non-Latin letters** (`:631-633`).
- `lang.py:658-679`: the per-line/per-field segment scan can name only Latin languages (`_named_prose_language` → `latin_profile`). **A plain string is returned right away, without the leaf check** (`:678`).
- Branches of the router (`third_party/laya/laya/router.py:833-865`, installed copy `:817-849`):
  - `unknown` → `self.default`
  - non-Latin → multilingual
  - Latin and non-English → multilingual
  - Latin with language undecided → `self.default`
  - otherwise → english
- The stock router is `Router(default="english")` (`router.py:519`, installed copy `:503`). `LAYA_DEFAULT_MODEL` is read only by `laya-serve` (`laya/serve.py:354`).

### 3.2 Battery (46 inputs; `part3_routing.py` → `part3_routing_battery.{json,md}`)

- `want` is this audit's judgment of which checkpoint can read the text needed for the decision.
- The `default=multilingual` column is the result of routing the same input with `Router(default="multilingual")`.

| # | group | input | script | lang | is_en | hangul/letters | route (default english) | reason | default=multilingual | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | pure_ko | 같은 달 요금이 두 번 빠져나갔어요. 중복 결제된 금액 환불 부탁드립니다. | hangul | - | False | 29/29 (1.00) | **multilingual** | non-Latin script (hangul, 100% of letters) | multilingual | ok |
| 2 | pure_ko | 앱이 자꾸 튕겨요 | hangul | - | False | 7/7 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 3 | pure_ko | 로그인이 안 돼요. 비밀번호를 바꿨는데도 계속 오류가 납니다. | hangul | - | False | 25/25 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 4 | pure_ko | {"message": "다음 달부터 요금제를 해지하고 싶습니다."} | hangul | - | False | 17/17 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 5 | pure_ko | 환불해 주세요 (NFD, 14 conjoining jamo) | hangul | - | False | 14/14 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 6 | ko_en_terms | 결제 API가 500 에러를 냅니다 | hangul | - | False | 9/12 (0.75) | **multilingual** | non-Latin script (hangul, 75%) | multilingual | ok |
| 7 | ko_en_terms | 로그인 시 OAuth redirect_uri mismatch 에러가 발생합니다 | hangul | - | False | 12/36 (0.33) | **multilingual** | non-Latin script (hangul, 33%) | multilingual | ok |
| 8 | ko_en_terms | Stripe webhook이 timeout 나요 | latin | - | True | 3/23 (0.13) | **english** | Latin script, language not identified …; using default (english) | multilingual | FAIL (stock default) |
| 9 | ko_en_terms | Kubernetes pod가 CrashLoopBackOff 상태예요 | latin | - | True | 5/34 (0.15) | **english** | … using default (english) | multilingual | FAIL (stock default) |
| 10 | ko_en_terms | AWS S3 bucket policy 설정 문의드립니다 | hangul | - | False | 8/24 (0.33) | **multilingual** | non-Latin script (hangul, 33%) | multilingual | ok |
| 11 | ko_en_terms | iPhone 15 Pro Max 환불 | latin | - | True | 2/14 (0.14) | **english** | … using default (english) | multilingual | FAIL (stock default) |
| 12 | ko_en_terms | Samsung Galaxy 주문이 아직 안 왔어요 (upstream test) | hangul | - | False | 9/22 (0.41) | **multilingual** | non-Latin script (hangul, 41%) | multilingual | ok |
| 13 | ko_en_terms | TypeError: Cannot read properties of undefined (reading 'map') 이 에러 왜 나요? | latin | en | True | 6/56 (0.11) | **english** | English Latin text | **english** | **FAIL** |
| 14 | ko_num_email_url | 주문번호 20231005-77 확인 부탁드려요 | hangul | - | False | 11/11 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 15 | ko_num_email_url | 010-1234-5678로 연락 주세요 | hangul | - | False | 6/6 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 16 | ko_num_email_url | kim.minsu@example.co.kr 로 영수증 보내주세요 | hangul | - | False | 9/28 (0.32) | **multilingual** | non-Latin script (hangul, 32%) | multilingual | ok |
| 17 | ko_num_email_url | 영수증: https://billing.example.com/invoices/INV-2024-000123/download?format=pdf | latin | - | True | 3/53 (0.06) | **english** | … using default (english) | multilingual | FAIL (stock default) |
| 18 | ko_num_email_url | 환불 요청: https://shop.example.com/orders/ABCD-1234?ref=newsletter | latin | - | True | 4/46 (0.09) | **english** | … using default (english) | multilingual | FAIL (stock default) |
| 19 | mostly_en | Please check my order, 감사합니다 | hangul | - | False | 5/23 (0.22) | **multilingual** | non-Latin script (hangul, 22%) | multilingual | ok (either) |
| 20 | mostly_en | I was charged twice for my subscription, 환불 please | latin | en | True | 2/41 (0.05) | **english** | English Latin text | english | ok (either) |
| 21 | mostly_en | Hi team, the 정산 report for March is wrong | latin | en | True | 2/32 (0.06) | **english** | English Latin text | english | ok (either) |
| 22 | mostly_en | The 결제 failed again | latin | en | True | 2/16 (0.12) | **english** | English Latin text | english | ok (either) |
| 23 | romanized | gyeoljega du beon dwaesseoyo | latin | - | True | 0/25 | **english** | … using default (english) | multilingual | default-dependent |
| 24 | romanized | hwanbul hae juseyo | latin | - | True | 0/16 | **english** | … using default (english) | multilingual | default-dependent |
| 25 | romanized | annyeonghaseyo, jumun beonho hwagin buthakdeuryeoyo | latin | - | True | 0/46 | **english** | … using default (english) | multilingual | default-dependent |
| 26 | emoji_chat | 환불해주세요 😡😡 | hangul | - | False | 6/6 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 27 | emoji_chat | ㅠㅠ | hangul | - | False | 2/2 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 28 | emoji_chat | ㅋㅋㅋ ok | hangul | - | False | 3/5 (0.60) | **multilingual** | non-Latin script (hangul, 60%) | multilingual | ok |
| 29 | emoji_chat | 😡😡😡 (control) | unknown | - | True | 0/0 | **english** | no letters detected in state; using default (english) | multilingual | default-dependent |
| 30 | very_short | 환불 | hangul | - | False | 2/2 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 31 | very_short | ㅇㅋ | hangul | - | False | 2/2 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 32 | very_short | 네 | hangul | - | False | 1/1 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 33 | very_short | 네 OK | latin | - | True | 1/3 (0.33) | **english** | … using default (english) | multilingual | FAIL (stock default) |
| 34 | very_short | OK 감사 (2:2 tie) | hangul | - | False | 2/4 (0.50) | **multilingual** | non-Latin script (hangul, 50%) | multilingual | ok |
| 35 | hanja_mixed | 北 미사일 발사에 美 강력 규탄 | hangul | - | False | 10/12 (0.83) | **multilingual** | non-Latin script (hangul, 100% of letters) | multilingual | ok |
| 36 | hanja_mixed | 與野, 추경 합의 불발 | hangul | - | False | 6/8 (0.75) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 37 | hanja_mixed | 大韓民國 憲法 第1條 | han | - | False | 0/8 | **multilingual** | non-Latin script (han, 100%) | multilingual | ok (script is han) |
| 38 | structured | dict: English ticket fields + `"message": "환불해 주세요"` (5 syllables) | latin | en | True | 6/72 (0.08) | **english** | English Latin text | **english** | **FAIL** |
| 39 | structured | dict: same wrapper + 19-syllable message | hangul | - | False | 19/85 (0.22) | **multilingual** | non-Latin script (hangul, 22%) | multilingual | ok |
| 40 | structured | turns: English agent turn + user "환불 부탁드려요" (7 syllables) | latin | en | True | 7/66 (0.11) | **english** | English Latin text | **english** | **FAIL** |
| 41 | structured | plain string: long English template (229 letters) + 19-syllable Korean message | latin | en | True | 19/248 (0.08) | **english** | English Latin text | **english** | **FAIL** |
| 42 | structured | same content as 41, as a dict | latin | - | False | 19/248 (0.08) | **multilingual** | "Latin script, language not identified but 0% non-English letters; …" (the reason text does not mention Hangul) | multilingual | ok |
| 43 | structured | {"고객_메시지": "Please cancel my plan"} (the key is ignored) | latin | en | True | 0/18 | **english** | English Latin text | english | ok |
| 44 | control | 二重に請求されました。返金をお願いします。 | kana | - | False | 0/19 | **multilingual** | non-Latin script (kana, 100%) | multilingual | ok |
| 45 | control | 客户被重复扣款要求退款 | han | - | False | 0/11 | **multilingual** | non-Latin script (han, 100%) | multilingual | ok |
| 46 | control | I was charged twice, please refund the duplicate. | latin | en | True | 0/40 | **english** | English Latin text | english | ok |

**Tally**

| verdict | Count |
|---|---|
| ok | 28 |
| ok (either) | 4 |
| default-dependent | 4 (3 romanized, 1 emoji-only) |
| FAIL (only with the stock default) | 6 (#8 9 11 17 18 33) |
| FAIL (regardless of default) | 4 (#13 38 40 41) |

- For Korean, `analyse()` always outputs `language` as `None` (`lang.py:581-584`). Korean written only in Hanja (#37) becomes `han`.
- The hangul/letters values in the cells were computed with `lang._script_counts`.

### 3.3 Failure types

**F1. Mixed text with a Latin majority (#8, 9, 11, 13, 17, 18)**
- The override is decided by letter ratio: the non-Latin share must be ≥0.2, or ≥0.1 with ≥10 letters (`lang.py:364-371, 573-576`).
- In Hangul, 1 syllable is 1 letter. Over the 300 MASSIVE pairs, writing the same meaning in English takes **2.59 English letters per 1 Korean syllable** (`letters_per_meaning_massive`). So a Korean request is undercounted by about 2.6x relative to its information content.
- Consequence 1 (#8, 9, 11, 17, 18): short Korean requests with technical terms, product names or URLs attached are judged to be Latin script. Without stopwords, they go through "undecided" (`router.py:853-860`) to the stock default, **english**.
- Consequence 2 (#13): with even a single English stopword (`of`), `language="en"` is set and the input goes to english regardless of default.
- upstream also states this risk as intended behavior: `lang.py:364-368` "a brand name or order code outvotes the CJK request around it letter for letter, though one CJK character carries far more than a letter." Yet the thresholds are still in letter units.
- Threshold sweep (plain string, `plain_string_sweep`):

| Latin letters | 11 | 20 | 44 | 83 | 160 | 320 |
|---|---|---|---|---|---|---|
| Minimum Hangul syllables to go to multilingual | 3 | 5 | 10 | 10 | 18 | 36 |

  Once the English context exceeds 40 letters, Hangul must be **≥10% of all letters and ≥10 syllables**.

**F2. Short Korean fields/turns inside an English wrapper (#38, 40)**
- The per-field rescue path for structured states (`_leaf_non_english`, `lang.py:631-633`) requires **10 or more** non-Latin letters.
- "환불해 주세요" (please refund; 5 syllables) and "환불 부탁드려요" (a refund, please; 7 syllables) are complete requests, yet they fall short of the threshold and go to english. The upstream test (`tests/test_router.py:366-368`) uses a 16-syllable sentence, so it passes.
- With the same wrapper, a 19-syllable message (#39) goes to multilingual.

**F3. Dependence on the state form (#41 vs #42)**
- With the same content, **a plain string goes to english and a dict to multilingual**.
- For a plain string, `analyse` returns before the leaf check (`lang.py:678`). The per-line segment scan can name only Latin languages (`lang.py:517-536, 658-675`).
- The reason text of #42, "0% non-English letters", does not reveal the actual reason for the decision (the Hangul field). This is a diagnostics-quality problem.

**F4. Single-syllable Korean + Latin (#33 "네 OK")**
- `_non_latin_words` accepts only runs of length 2 or more as evidence (`lang.py:407`). The 1-syllable "네" (yes) cannot trigger the override and goes through undecided to the default, english.
- In contrast, the tied "OK 감사" (#34) goes to multilingual by the non-Latin-first rule (`lang.py:323-326`, `_script_counts` docstring `:290-292`).

**F5. Romanized Korean (#23–25)**
- `_STOP` (`lang.py:57-168`) has romanized Bengali (`bn`) but no romanized Korean. Such input goes through undecided to the default.
- There is no evidence that either checkpoint reads romanized Korean, so the verdict is left as default-dependent.

**F6. Emoji-only input (#29)**
- It becomes `unknown` and goes to the default (`router.py:834-836`). This is intended behavior, pinned by a test (`tests/test_router.py:1128-1134`).

**Areas that do not fail**
- Pure Korean (including the 1-syllable "네"), jamo chat (ㅋㅋ/ㅠㅠ/ㅇㅋ)
- Korean + digits/phone numbers/e-mail addresses
- Mixes with API terms in which Hangul is the majority (#6, 7, 10, 12)
- Headlines with mixed Hanja, NFD, mixed emoji
- Korean fields of 10 or more syllables inside an English wrapper

**Note.** The comment at `env.sh:12`, "한글은 항상 감지되므로 한국어에는 무관" (Hangul is always detected, so this does not matter for Korean), does not hold for F1 (#8, 9, 11, 17, 18) and F4 (#33). In these cases `default` decides the checkpoint for Korean input. env.sh was not modified in this audit.

### 3.4 Mitigations (all existing APIs)

| Means | What it fixes | What it does not fix |
|---|---|---|
| `Router().route(state, lang="ko")` or `lang_guess=` (`router.py:811-831`) | All cases (confirmed: #8 → multilingual, romanized → multilingual) | – |
| `Router(default="multilingual")` (in serve, `LAYA_DEFAULT_MODEL=multilingual`) | The undecided cases of F1 (#8, 9, 11, 17, 18), F4, F5, F6 | **F1-en (#13), F2 (#38, 40), F3 (#41)**: `is_english=True`, so they do not take the default path |
| Put the Korean message to be decided in a separate dict field, with 10 or more syllables | F3, part of F2 | Short Korean |

**PART 3 verdict.**
- **When Korean text dominates by letter count, routing is reliable.** Pure Korean, short Korean, jamo, mixed Hanja and NFD all go to multilingual. The evidence was confirmed at the code-line level.
- All failures have the same cause: **the thresholds are based on letter counts (1 syllable = 1 character), and the field minimum for structured states is 10 letters**.
- As a result, tech-support inquiries with many Latin terms, pasted URLs/errors, and short customer messages wrapped in English templates go to english, a checkpoint that sees 91% of Korean tokens as byte fragments.
- 4 of these cannot be prevented even with `default="multilingual"`.
- If Korean is the main traffic, **explicitly passing `lang="ko"` (or an LID-based `lang_guess`)** is the only complete solution.
- Strength of evidence **strong**: the deterministic rule was reproduced and confirmed with the 46 cases and the sweep.

---

## 4. Reproduction commands (project root, after `source env.sh`; `.venv/` is not included in the public repository)

```bash
bash results/korean_support/fetch_cards.sh                         # cards/API/paper/FineWeb2-HQ → cards/
.venv/bin/python results/korean_support/part1_docs_evidence.py     # → part1_docs_evidence.json (+ cards/mmbert_paper/*.txt)
.venv/bin/python results/korean_support/part2_tokenizer.py         # → part2_tokenizer_stats.json, part2_massive_pairs.jsonl (~1 min)
.venv/bin/python results/korean_support/part1b_tokenizer_origin.py # → part1b_tokenizer_origin.json (needs the part2 results)
.venv/bin/python results/korean_support/part3_routing.py           # → part3_routing_battery.json / .md
```

Logs: `part1_docs_evidence.log`, `part1b_tokenizer_origin.log`, `part2_tokenizer.log`, `part3_routing.log`.

## 5. Outputs

| Path | Content |
|---|---|
| `results/korean_support/audit_docs_tokenizer_routing.md` | This document |
| `results/korean_support/fetch_cards.sh` | Collects the PART 1 source material |
| `results/korean_support/part1_docs_evidence.py` / `.json` / `.log` | Card tags, Korean lines in the card bodies, config, mmBERT Table 9, FineWeb2-HQ, BENCHMARKS ranks, provenance of the numbers, upstream grep, lang.py ranges |
| `results/korean_support/part1b_tokenizer_origin.py` / `.json` / `.log` | Tokenizer identity laya-multilingual ↔ mmBERT |
| `results/korean_support/part2_tokenizer.py` / `part2_tokenizer_stats.json` / `part2_massive_pairs.jsonl` / `.log` | All PART 2 metrics, per-pair token counts, budget |
| `results/korean_support/part3_routing.py` / `part3_routing_battery.json` / `.md` / `.log` | PART 3 battery, sweep, mitigation checks |
| `results/korean_support/cards/` | The 4 original cards and their API JSON (`?full=true`, `?blobs=true`), the mmBERT paper (API xml, abs html, full html, txt), the FineWeb2-HQ card and API |

**English** | [한국어](audit_docs_tokenizer_routing.ko.md)
