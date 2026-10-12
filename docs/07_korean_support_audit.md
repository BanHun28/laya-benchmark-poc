# 07. Korean support audit: results and design implications

**Purpose**: Judge whether Laya 0.3.23 (checkpoint 55cf4c4) supports Korean "properly" on four layers (documentary evidence, tokenizer·encoder, routing, measured model behavior), and turn the results into decisions to be reflected in the designs of 03 (benchmark) and 05 (PoC).
**Prerequisite documents**: `01_laya_analysis.md` (architecture·Router), `02_environment_setup.md` (environment), `05_poc_plan.md` (PoC schemas·gates), the P0 run cards (`results/poc/P0_20261002.md`, `P0b_20261002.md`, `P0c_20261002.md`).
**Outputs**: `results/korean_support/audit_docs_tokenizer_routing.md` (audit of the documents·tokenizer·routing), `results/korean_support/paired_ko_en_audit.md` and `K2_20261002.md` (Korean vs English measurements), `results/korean_support/part3_routing_battery.md` (46-case routing battery), and the original model cards·paper in `results/korean_support/cards/`.

Measured on 2026-10-02. All measurements are CPU fp32; n is stated per table. With n=100 the 95% CI spans about ±0.10, and with n=30 about ±0.17.

## 1. Summary of the verdict

In Laya, Korean is a **supported evaluation language**, not a **trained·guaranteed language**. Pure Korean input works normally in the tokenizer (UNK 0, fragmentation at most 0.2%), in routing (hangul script detection) and in the model, and the Korean numbers upstream published (MASSIVE ko intent-20: multilingual 0.470, english 0.110) are reproduced with Δ0 in our harness. When the same content is given in Korean and in English, the penalty relative to English is 0.21-0.24 (significant) when the option text is English keys, and 0.10 when it is Korean descriptive explanations (not significant at n=100, concentrated in the single class `play`). The "no" bias of noul and the avoidance of score level 0 seen in P0 appear identically in the English translations of the same sentences, so they are properties of the multilingual checkpoint, not a Korean problem. Routing of mixed text with mostly Latin letters and NFD input must be handled on the application side.

| Layer | Verdict | Strength of evidence |
|---|---|---|
| Documentary evidence | Korean is documented only as one of the 50 MASSIVE evaluation languages. It is included in the encoder (mmBERT) pre-training as a stage-1 high-resource language. There is no record of Korean in Laya's RLCD decision training data | Encoder: strong (paper Table 9). Laya evaluation: weak-to-medium (n=100/300, mixed sources for the card numbers). Laya training: no record |
| Tokenizer·encoder | The multilingual tokenizer handles Korean normally, syllable by syllable (UNK 0). 1.5× the tokens of English. NFD input and rare syllables are weak points | Strong (exact reproduction of the P0 token counts 34/661) |
| Routing | Pure Hangul is reliable. Mixed text with a Latin majority and short Korean inside an English wrapper fail structurally by going to english | Strong (deterministic rules, line-level citations of lang.py, 46-case battery) |
| Measured model behavior | upstream numbers reproduced with Δ0. Penalty relative to English 0.10-0.24 (depends on the language of the option text). The noul·score weaknesses are language-independent | Medium (2 kinds of n=100 pairs, n=30 translation probe) |

## 2. Documentary evidence

Sources: `results/korean_support/audit_docs_tokenizer_routing.md` Part 1 and the originals in `results/korean_support/cards/`.

| Item | Finding | Source |
|---|---|---|
| `ko` language tag | Present on the `convaiinnovations/laya-multilingual` card. The 50 tags match the set of MASSIVE evaluation languages exactly, with both set differences 0. In other words, a list of "evaluated languages" | `cards/convaiinnovations_laya-multilingual/README.md:5`, `part1_docs_evidence.json` |
| Wording on supported languages | Only the single phrase "covering 100+ languages" | Same card L15 |
| Bundle card (`convaiinnovations/laya`) | No `language:` field. "English only on root" | Bundle card L373 |
| Mentions of Korean in the body | One sentence, "Korean 0.110 → 0.490". 0.110 is the english value from the CPU sweep (n=100) and 0.490 is the multilingual value from the T4 run (n=300, `research/results/t4_colab_benchmark.json`), a mix of different runs. The current official value is 0.470 in `BENCHMARKS.md:71` (n=100, ECE laya 0.680 / multilingual 0.311) | multilingual card L116-118 |
| Encoder | `jhu-clsp/mmBERT-base`. model type modernbert, vocab 256,000, max position 8,192. There is no `_name_or_path`; the source is the `encoder` field of `rl_agent_config.json` | `models/laya-multilingual/encoder/config.json:55,78,52` (not included in the public repository), `rl_agent_config.json:2` |
| Korean in mmBERT pre-training | The card lists `kor`; Gemma 2 tokenizer; a 3-stage curriculum "60 high-resource → 110 → 1833". Paper Table 9: Korean pre-training 28.4B tokens (1.43%) of 43.9B in total, 13th of 89 languages. The pre-training stage uses only 60 languages, so Korean is a stage-1 high-resource language. However, Korean is not among the 20 FineWeb2-HQ languages (ja and zh are). Neither the card nor the paper has any Korean-specific benchmark numbers | mmBERT card L775, L1925, L1884. arXiv 2509.06888 Table 9 |
| Tokenizer identity | The laya tokenizer has the same vocab·merges (580,604) as the mmBERT tokenizer, and on 300 MASSIVE ko sentences the token ids agree 300/300 | `part1b_tokenizer_origin.json` |
| Korean's position in the 51-language table | accuracy 0.470 ranks 18th of 51 (tied with nl); median 0.400, macro 0.4008. ECE 0.311 ranks 10th; median 0.397, macro 0.391. ko/en = 0.470/0.710 = 0.662. With n=100, CI [0.375, 0.567]. Lower than ja 0.64 and zh 0.65 | `BENCHMARKS.md` §Languages table |
| Other Korean evidence in upstream | In the presentation check, ko is the worst of 4 languages, −0.570 FAIL. The test sentences were written by a non-native speaker. Apart from that there is only the hangul range in `lang.py:43` and a few test lines. Chinese has `research/evals/zh_decision_bench.jsonl` and the `BENCHMARKS.md:422` section, but there is no Korean dataset | `research/eval/README.md:308-313, 383-385` |
| Korean in language detection | Stop-word lists exist for only 11 languages: az, bn, de, en, es, fr, it, nl, pt, ro, sv. Non-Latin scripts return `language=None`, so the code "ko" never appears; Korean is identified only as script "hangul" | `laya/lang.py:57-168`, `:581-584` |
| Training data | Every dataset the documents name as a training source is English. "Neither checkpoint trained on typed-decisions, MASSIVE or XNLI". No Korean RLCD training data is documented. The Korean numbers should be read as zero-shot transfer | `README.md:1352-1353`, `BENCHMARKS.md:138-148`, `research/results/t4_colab_benchmark.json:4309` |

## 3. Tokenizer and token budget

Sources: `results/korean_support/audit_docs_tokenizer_routing.md` Part 2, `part2_tokenizer_stats.json`, `part2_massive_pairs.jsonl`. Only the tokenizer was run; there is no model forward.

| tokenizer / set | tok/char | tok/word | tok per syllable | fragmentation % | UNK |
|---|---|---|---|---|---|
| multilingual / MASSIVE ko (300) | 0.726 | 2.21 | 0.98 | 0.10 (1 syllable, '딨') | 0 |
| multilingual / MASSIVE en (300) | 0.215 | 1.07 | n/a | 0 | 0 |
| multilingual / P0 ko (30) | 0.682 | 2.83 | 0.95 | 0.17 ('ㅠㅠ') | 0 |
| multilingual / KLUE YNAT (100) | 0.794 | 3.30 | 1.11 | 0 | 0 |
| english / MASSIVE ko (300) | 1.698 | 5.16 | 2.30 | 90.6 | 0 |
| english / MASSIVE en (300) | 0.221 | 1.11 | n/a | 0 | 0 |
| english / P0 ko, YNAT | 1.53 / 1.78 | 6.33 / 7.38 | 2.12 / 2.47 | 82.1 / 91.2 | 0 |

- Token ratio (ko/en) of sentence pairs with the same meaning: measured with multilingual on both sides, median 1.50, p90 2.20. Measured with english, median 3.43, p90 5.0.
- multilingual effectively splits by syllable. The vocab has only 369 multi-syllable Hangul entries, and only 1,551 (66%) of the 2,350 common KS X 1001 syllables are single tokens. The rest split into 3 byte tokens per syllable, but they are rare in real text.
- UNK 0 for the english tokenizer does not mean it can read Korean. Byte-level BPE structurally never emits UNK, and in practice 91% of the tokens are sub-character byte fragments. This is the mechanical reason the english checkpoint cannot read Korean.
- **NFD input risk (new finding)**: the normalizer of the multilingual tokenizer only replaces whitespace and has no NFC normalization. The laya code has no `unicodedata.normalize` call either. Korean decomposed into NFD grows to 3.09× the tokens and becomes jamo and byte fragments. macOS file names and some clients send NFD, so apply `unicodedata.normalize("NFC", text)` before inference (05 RedactHook or a separate preprocessing hook).

**Token budget.** laya's `build_sequence` reproduced P0's `state_tokens` 34 and `input_tokens` 661 exactly. The state space is allotted per question: 7 questions do not split it into 7 parts; the question with the longest head sets the limit (in P0, 896 tokens for the intent question).

| Condition | State capacity |
|---|---|
| multilingual, `max_len=1024`, 7-question v1 head, Korean | about 1,120-1,310 characters (1,227 by MASSIVE, 1,259 by the P0 message ratio) |
| Same condition, English | about 4,150 characters (for the same content, Korean is about 68% of English) |
| multilingual, `max_len=8192`, Korean | about 11,100 characters |
| Korean misrouted to the english checkpoint | about 190 characters |

## 4. Routing

Sources: `results/korean_support/part3_routing_battery.md`, `part3_routing_battery.json`, `laya/lang.py` (the installed copy is byte-identical to upstream @4aa6761). Only `Router().route()` and `laya.lang.analyse()` were used, without loading a model.

**Rules (lang.py)**

| Line | Rule |
|---|---|
| `:364-371` | `NON_LATIN_FRACTION=0.2`, `NON_LATIN_MIN_FRACTION=0.1`, `NON_LATIN_MIN_LETTERS=10` |
| `:573-576`, `:407` | When Latin letters are the majority, the decision flips to non-Latin if there is a run of at least 2 consecutive non-Latin letters (`len(w) >= 2`) and their share is at least 0.2, or at least 0.1 with at least 10 letters |
| `:297-320` | Letters are counted with 1 Hangul syllable = 1 letter |
| `:631-633` | Structured input such as dicts·conversation turns is detected separately only if a single field has at least 10 non-Latin letters |
| `:678` | A plain string skips the per-field check |
| `router.py:833-865`, `:519` | Router branching, default `default="english"` |

**Battery results (46 cases)**: 28 correct, 4 where either English or Korean is fine, 4 that depend on the `default` setting, 10 failures. Handled correctly: pure Korean, the 1-syllable "네", jamo (ㅋㅋ/ㅠㅠ/ㅇㅋ), headlines mixing in Hanja, NFD input, Korean mixed with emoji, Korean mixed with email addresses·phone numbers, and API-term mixtures with a Hangul majority.

| Failure type | Example | Route | Cause |
|---|---|---|---|
| F1 mixed text with a Latin majority | "Stripe webhook이 timeout 나요", "Kubernetes pod가 ...", "iPhone 15 Pro Max 환불", 2 requests with a URL attached | Language undecided → `default` (english). A question with a pasted English error message (`TypeError ...`) is judged `language=en`, so it goes to english even if default is changed | On MASSIVE, for the same meaning, 1 Hangul syllable ≈ 2.59 English letters, but both count as 1 letter, so Korean content is undercounted by about 2.6×. Once the English context exceeds 40 letters, Hangul must be at least 10% of all letters and at least 10 syllables to reach multilingual |
| F2 short Korean inside an English wrapper | dict field "환불해 주세요" (5 syllables), conversation turn "환불 부탁드려요" (7 syllables) | english, regardless of default | The 10-letter minimum of `:631-633` |
| F3 dependence on input shape | Long English template + 19-syllable Korean | english as a plain string, multilingual as a dict. The reason on the dict path is "0% non-English letters", which does not reveal the actual reason | `:678` a plain string skips the per-field check |
| F4 single syllable + Latin | "네 OK" | `default` | Fails the condition of 2 consecutive non-Latin letters |
| F5 romanized Korean | "gyeoljega du beon dwaesseoyo" | `default` | No stop-word list |
| F6 emoji only | Emoji alone | `default` | Intended behavior, pinned by an upstream test |

| Mitigation | What it fixes |
|---|---|
| `predict(..., lang="ko")` or `lang_guess` (`router.py:811-831`) | Everything (confirmed with the battery) |
| `Router(default="multilingual")` / `LAYA_DEFAULT_MODEL=multilingual` | Only the language-undecided cases of F1 and F4-F6. Does not fix pasted English errors, F2 or F3 |
| env.sh comment "Hangul is always detected, so it does not matter for Korean" | Wrong (F1, F4). Corrected |

If Korean traffic is the main load, setting `lang="ko"` explicitly from channel·locale metadata is the only complete solution.

## 5. Measured model behavior: Korean vs English

Sources: `results/korean_support/paired_ko_en_audit.md`, `K2_analysis.md`, run card `K2_20261002.md`. MASSIVE is a parallel corpus across locales, so a ko/en pair with the same `id` has the same content (the label_text of the first 100 pairs all match; `K2_build.py` assert). Every run used `laya-evals --device cpu --batch-size 8 --slice qid`, revision 55cf4c4; all 13 runs exited 0.

### E1 scenario-18 (multilingual, n=100 pairs)

| Question form | ko | en | en − ko (95% CI) | McNemar p (b/c) | english checkpoint, en |
|---|---|---|---|---|---|
| Korean descriptive explanations (P0c base) | 52 | 62 | +0.10 (−0.02..+0.22) | 0.143 (14/24) | 50 (options truncated to 9 tokens, so not an upper bound) |
| upstream key rendering | 35 | 56 | +0.21 (+0.12..+0.30) | 4.9e-05 (3/24) | 65 (p=0.023 vs multilingual) |

- Both ko runs agree with P0c on argmax 100/100.
- Caution: the english checkpoint has `head_max_len=192`, so it truncates the Korean explanations to 22 tokens per option (for domain_8, 04 §7 stats). So the Korean penalty is measured with multilingual for both files, and the english column is for reference.
- Korean explanations raise ko by +0.17 (p=4.9e-04) and lower en by −0.06 (n.s.). The size of the English advantage depends on the language of the option text.
- Post-hoc breakdown: all 10 differences in the Korean-explanation form came from the 17 `play` rows (ko 1 vs en 11). The remaining 83 rows are 51 vs 51 (p=1.0). All 11 en correct answers contain the word "play" verbatim in the utterance.
- ECE / mean confidence: ko 0.250 / 0.747, en 0.168 / 0.772. macro-F1 (over the 10 classes that occur in the gold labels): ko 0.550, en 0.646.

### E2 intent-20, upstream-faithful setup (n=100 pairs)

| | ko / multilingual | en / multilingual | en / english | ko / english |
|---|---|---|---|---|
| Accuracy (x/100) | 47 | 71 | 82 | 11 |
| upstream published value | 0.470 | 0.710 | 0.820 | 0.110 |
| ECE measured / upstream | 0.3108 / 0.3108 | 0.2333 / 0.2333 | 0.1383 / 0.1382 | 0.6804 / 0.6804 |

- ko vs en (multilingual): +0.24 (+0.13..+0.35), McNemar p=1.2e-04 (7/31). On en, english vs multilingual: +0.11, p=0.035.
- **Track A reproduction**: all four cells have Δ 0.000, within ±0.03. mean confidence and acc@50%cov also match. H1 (01 §9) holds on this path. The option setup is the same as upstream's `laya_eval.build_suite` for both ko and en (`K2_build.py:196` assert).
- The scoring differs: laya-evals processed all 100 rows as standalone forwards (rows_alone=100), while upstream uses a packed forward. At this resolution no difference showed.
- A large part of the penalty is the effect of English utterances overlapping literally with the English option keys. On rows where a key word appears in the utterance en is ahead by +14/44, and on rows without overlap by +10/56 (p=0.04), so a comprehension gap remains even without the overlap.
- On the english checkpoint, intent-20 has its options truncated on 75/100 rows, and on 50 rows the `iot_hue_light*` options become indistinguishable from each other. upstream's 0.82 is under the same condition.

### E3 Embedding alignment (`embed_fn_from_agent`, n=100 pairs, chance P@1 0.01)

| Checkpoint | P@1 ko→en / en→ko | P@5 ko→en / en→ko | Mean cos true pairs / random pairs |
|---|---|---|---|
| multilingual | 0.19 / 0.31 | 0.43 / 0.45 | 0.737 / 0.642 (difference 0.7 sd) |
| english | 0.03 / 0.01 | 0.07 / 0.07 | 0.800 / 0.794 |

multilingual places Korean and English in the same space only partially, and english is at chance level. mmBERT was not trained for sentence embeddings, so this is only an alignment metric, not a retrieval benchmark.

### E4 probe of 30 rows: Korean state vs English-translated state (same 7 questions, questions_sha256 identical)

The English translations are reference translations written for this project (`results/korean_support/probe_en.jsonl`).

| qid | KO / multilingual | EN / multilingual | EN / english |
|---|---|---|---|
| intent | 12/30 | 16/30 (p=0.29) | 14/30 (options truncated) |
| is_urgent | 25/30, positives 0/5, conf 0.957 | 26/30, positives 1/5, conf 0.981 | 28/30, positives 3/5 |
| refund_requested | 25/30, positives 5/6, conf 0.905 | 25/30, positives 3/6, conf 0.898 | 30/30, positives 6/6 |
| churn_risk | 24/30, positives 2/6, conf 0.947 | 25/30, positives 3/6, conf 0.945 | 29/30, positives 5/6 |
| needs_llm | 19/30, positives 3/10, conf 0.887 | 18/30, positives 4/10, conf 0.899 | 20/30, positives 0/10 |
| binary total (always-no 93/120) | 93 | 94 | 107 |
| noul mean AUROC | 0.76 | 0.74 | 0.91 |
| frustration level 0 chosen (argmax / rounded, expected 18) | 0 / 0, MAE 1.084 | 2 / 0, MAE 1.207 | 10 / 0, MAE 0.975 |

- On multilingual, the KO vs EN McNemar tests of the 4 noul questions all give p=1.000.
- v1b (with criteria) shows the same pattern, KO 87 / EN 85, and refund_requested collapsing toward true with 18 / 19 positives is also the same. P0b's "churn_risk + Korean criteria" signal (28/30) shrank to 25/30 with the English state (p=0.375).
- The intent errors on the negation rows 7, 11 and 29 also persist in English.

**Conclusion: the noul collapse is not specific to Korean.** The english checkpoint gets 107/120 right on the same English sentences, so the questions themselves are answerable. On is_urgent·refund·churn, multilingual reads the state as a ranking regardless of language (AUROC 0.80-0.92), but p(true) is pushed below 0.5. This is not a problem solved by polishing the Korean sentences; it is a problem of the decision threshold and of the checkpoint.

**Additional check (Track E6, n=500 NSMC noul, `results/E/E_summary_20261002.md`).** AUROC test 0.822, dev Youden threshold p(true) ≥ 0.0073 (dev median 0.0099), test accuracy 0.725 (0.641 at the 0.5 threshold, always-no 0.522). This reconfirms at n=500 the conclusion above that the ranking is informative and p(true) is pushed down. It is, however, lower than the semantic-key 2-choice (0.773).

**Additional check (Track B, n=500 pairs, `results/B/summary_20261002.md`).** On the Korean-explanation schema (domain_8), ko 0.526 vs en 0.510, McNemar p=0.47: no penalty. This confirms more strongly, at n=500, E1's "penalty 0.10 (n.s.) with Korean descriptive explanations", and the +0.24 of the English-key options (intent-20) stands.

## 6. Design·operations implications

These are the decisions reflected (or to be reflected) in 03 and 05. The numbering is what 00 §5 item 8 refers to.

1. **Make routing explicit.** For requests on the Korean channel, fix `predict(..., lang="ko")` (or `lang_guess`) from channel·locale metadata, and leave it to detection only when there is no metadata. `default="multilingual"` alone does not prevent F1's pasted English errors, F2 or F3 (§4).
2. **NFC normalization before inference.** Run `unicodedata.normalize("NFC", text)` in the RedactHook or a separate preprocessing hook. NFD input grows to 3.09× the tokens and hurts both the budget and quality (§3).
3. **Option explanations in Korean descriptive form.** +0.17 over key rendering on scenario-18 (§5 E1). Options with overlapping vocabulary (play/music) are rewritten apart or merged. In P0c, merging play/music gave 0.52 → 0.66. However, Track B's merged 8-domain set stayed at 0.526 (test 0.492) at n=500 and did not improve with variations of the explanation wording (`results/C/C_schema_v2_20261002.md`). The Korean penalty is gone (0.526 vs 0.510), but the task's own zero-shot ceiling is low.
4. **The noul decision threshold is not fixed at 0.5.** Choose a per-question threshold from the dev-set ROC (or an error budget). Temperature calibration cannot move the 0.5 boundary of a 2-class softmax (p=0.5 at a logit difference of 0 holds for every T), so this is a threshold problem, not a calibration problem. AUROC 0.76-0.92 (§5 E4) means there is room for recovery just by moving the threshold. Reflected as E6 in 03 Track E and in 05 §5·P3, and confirmed by the E6 measurement (NSMC: 0.641 → 0.725).
5. **score (frustration) is an auxiliary signal.** The avoidance of level 0 is language-independent, and the `frustration >= 2.5` rule never fires at zero-shot (P0b score range 0.91-2.37). Do not use it alone for automatic actions.
6. **Alternative path "MT → english checkpoint".** With reference translations, the upper bound is intent +0.35, noul +14/120 (the EN/english column of §5 E4). Whether to measure it on the P1 set, including the real MT cost·latency·mistranslations, is a decision still to be made.
7. **Traffic mixed with English.** With `lang="ko"` set explicitly, English requests also go to multilingual, so if the English share is large, weigh the reload cost of D5 (03 §6) together with the english checkpoint's advantage (en 0.82 vs 0.71 in E2).

## 7. Where this was reflected in 03/05/02

| Decision (§6) | Document and location | Content |
|---|---|---|
| 1 explicit routing | `05_poc_plan.md` §3 component table, Router row, app.py sketch comment; `02_environment_setup.md` §2.8 env.sh comment and the explanatory paragraph; `01_laya_analysis.md` §3 Router bullet, §9 H2 | The Korean channel is fixed to `lang="ko"`; detection only when there is no metadata. Corrected the phrase "Hangul is always detected" with the F1·F2 exceptions |
| 2 NFC normalization | `05_poc_plan.md` §3 Router row·app.py comment, §9 risk table; `03_benchmark_plan.md` §13 risk table | `unicodedata.normalize("NFC")` in the RedactHook or at the server entry. For evaluation sets whose source is NFD, record it in the MANIFEST |
| 3 Korean descriptive explanations | `04_korean_evalset_spec.md` §3 (the part reflecting P0c), `03_benchmark_plan.md` §7 B5 expected range | Already reflected from the P0c results. E1 of this audit reconfirms the same direction |
| 4 noul decision threshold | `05_poc_plan.md` §5 (`T_NOUL`, policy code and table), P3 stage; `03_benchmark_plan.md` Track E6 | Per-question ROC-based threshold, applied in the policy layer |
| 5 score as an auxiliary signal | `05_poc_plan.md` §5 (the part reflecting P0b) | No change; E4 additionally confirms it is language-independent |
| 6 MT → english path | This document §6, open question 2 | Not reflected. Adoption is a decision still to be made |
| 7 traffic mixed with English | `03_benchmark_plan.md` §6 D5 | No change; added E2's en 0.82 vs 0.71 as decision evidence |
| Routing robustness measurement | `03_benchmark_plan.md` Track C10 | Rerun the 46-case battery with `scripts/probe_routing.py`, adding NFD pairs |
| Entry point | `00_README.md` §2 document map, §5 item 8 | Added 07, listed as a decision item |

## Open questions / assumptions

1. **Sample limits.** E1-E3 are n=100 (CI ±0.10) and E4 is n=30 (CI ±0.17). The direction is consistent, but the size is measured again in Track B (n=500) and on the PoC P1 set.
2. **Reference translations.** The English sentences of E4 are translations written for this project, so they differ from real MT output. Adopting the "MT → english" path requires remeasuring with real MT.
3. **Card number inconsistency.** The multilingual card's "Korean 0.110 → 0.490" mixes runs. Whether to report it upstream as an issue is decided together with 00 §5 item 6 (scope of publishing results).
4. **Whether Korean training data exist.** Absent from the documents is not the same as actually absent. Decide whether to ask the maintainers about the language composition of the RLCD training mix.
5. **Proposal to change the routing thresholds.** The cause of F1 (the rule counting a syllable as 1 letter) could be submitted upstream as a weighting proposal, but our PoC works around it by setting `lang="ko"` explicitly, so this is optional.
6. **Where to handle NFD.** Whether in the hook or at the server entry is decided during the P2 implementation. Either way, only the normalized text goes into the shadow log.

**English** | [한국어](07_korean_support_audit.ko.md)
