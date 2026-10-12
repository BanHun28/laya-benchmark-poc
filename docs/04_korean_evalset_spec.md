# 04. Korean evaluation set build specification

**Purpose**: Fixes the definitions, conversion rules, build-script specification, quality checks and freeze procedure of the Korean `laya-evals` JSONL sets shared by the Laya benchmark (03_benchmark_plan.md) and the PoC (05_poc_plan.md). This document is the requirements specification for `scripts/build_ko_evalsets.py`.

**Prerequisite documents**: 00_README.md (execution order), 01_laya_analysis.md (primitives, token budget, Honest limits), 02_environment_setup.md (uv venv Python 3.12, laya 0.3.23, `datasets`·`pandas`, `models/` symlinks, `third_party/laya` @ `4aa6761`; `models/` and `third_party/laya` are not included in the public repository, and upstream is recreated by cloning https://github.com/NandhaKishorM/laya at commit 4aa6761).

**Outputs**: 12 kinds of `data/evals/*.jsonl` + `data/evals/MANIFEST.json`, `data/handwritten/` (handwritten sources), `scripts/build_ko_evalsets.py` (implemented to the specification in §6 of this document; the implementation is a separate task).

---

## 1. Purpose and principles

The only Korean figure upstream publishes is one line for MASSIVE intent 20-option: `laya` 0.110 / `laya-multilingual` 0.470, ECE 0.680 / 0.311 (source: BENCHMARKS.md:71). Figures of the kind needed for a Korean PoC adoption decision ("ticket classification, sentiment, NLI, hate detection, speech-act classification") do not exist, so we build them. The sets have three roles.

| Role | Sets | Track using them |
|---|---|---|
| Upstream reproduction (sanity) | `ko_massive_intent_20opt`, `en_massive_intent_20opt` | Track A |
| Measuring transfer to Korean tasks | YNAT, NLI, NSMC, K-MHaS, 3i4K, scenario_18 | Track B |
| Probing known weaknesses | `ko_massive_intent_full60`, `ko_negation_probe` | Track C |
| PoC domain sets | `ko_massive_domain_8` (+ the `en_massive_domain_8` pair), auxiliary `ko_klue_ynat_7` | Track B / E / PoC |
| On hold (scenario A) | `ko_poc_triage_v1` | After the P4 decision |

The principles are as follows; each is taken from upstream's evaluation design.

1. **Freeze the label policy first.** For the handwritten sets (5.7, 5.8), the label-policy document is written and its sha256 recorded before any model is run even once. Upstream's zh_short_commands and es_phone_turns benches use the same rule (source: research/benchmarks/zh_short_commands/README.md "label policy fixed before any model was run").
2. **held-out.** Public sets use only the test or validation split. Whether a source is in the training mix is written into the MANIFEST `in_training_mix` field according to upstream evidence and read together with the results (source: BENCHMARKS.md "Themes", the *held out* labeling convention). Upstream writes "Neither checkpoint trained on typed-decisions, MASSIVE or XNLI", so the MASSIVE-derived sets are held out for the base checkpoints (source: research/scripts/build_benchmark_nb.py:760-762). ft-v1 was trained on MASSIVE ko train (`results/P4/`). Sources upstream does not mention (KLUE, NSMC, K-MHaS, 3i4K) are left as "unknown".
3. **Deterministic build.** Fixed seed 13 (upstream `SEED = 13`), sampling after sorting, byte-identical output for the same input. Identity is proven with sha256.
4. **Byte-stable question schema.** `questions_sha256` fingerprints the full instructions and criteria strings, so changing even one character makes it a different experiment (source: docs/evals.md "Run identity").
5. **Record licenses.** The license and URL of every source go into the MANIFEST and the §8 table; unconfirmed ones are left as "to be verified".
6. **Size is set by CPU time.** The main sets' N=500 is a size that finishes within a few minutes on the M4 Pro CPU with the multilingual checkpoint (adjusted with the measurements in 02_environment_setup.md). A full build with `--n 0` is also kept possible.
7. **No PII.** Handwritten sentences are edited or invented and contain no real customer data, real names, contact details or order numbers.

---

## 2. laya-evals JSONL format

One JSON object per line. Empty lines and lines starting with `#` are ignored (source: docs/evals.md "Dataset format", research/evals/README.md "Format").

| Field | Required | Type | Meaning |
|---|---|---|---|
| `state` | yes | str / dict / list | What is judged. For a dict, the instructions refer to fields in backticks |
| `questions` | yes | dict | The question dict exactly as `Router.predict` takes it |
| `expected` | yes | dict | question id → gold label |
| `tags` | no | list[str] | Unit for `--slice tag` |
| `language` | no | str | Unit for `--slice language`. The sets in this document use `"ko"` or `"en"` |
| `model` | no | str | Pins the checkpoint per row. `--model` takes precedence |

The type rules for `expected` are set by the evaluator implementation (source: laya/evals.py:255-280, 331-337).

| Primitive | expected type | Scoring rule |
|---|---|---|
| `choice` | **criteria key** string | `answer["choice"] == expected` (ChoiceAccuracy) |
| `score` | number, **0-based level index** | `abs(answer["score"] - expected)` (ScoreMAE), tolerance via `--score-within` |
| `noul` | JSON `true` / `false` | `(p >= 0.5) == expected` (NoulAccuracy) |

The `score` answer is an "expected ordinal level" (e.g. 1.84 / 2.0), so expected must also be an index on the same scale. With 4 levels, expected ∈ {0,1,2,3}. A 3-line example (choice, score, noul, in that order):

```json
{"state": {"message": "결제가 두 번 됐어요. 중복 결제 환불해 주세요."}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불이나 중복 결제 환급을 요구", "technical_help": "버그나 오류에 대한 기술 지원 요청", "other": "그 외"}}}, "expected": {"intent": "refund"}, "tags": ["example"], "language": "ko"}
{"state": {"message": "서비스가 두 시간째 안 되고 있습니다. 지금 매출 손실이 나고 있어요."}, "questions": {"frustration": {"type": "score", "instructions": "How frustrated does the customer sound in `message`?", "criteria": ["차분하고 중립적", "걱정하지만 정중함", "분명히 짜증남", "매우 화남 또는 강한 표현 사용"]}}, "expected": {"frustration": 2}, "tags": ["example"], "language": "ko"}
{"state": {"message": "환불 안 해주면 다른 서비스로 갈아탈 겁니다."}, "questions": {"churn_risk": {"type": "noul", "instructions": "Does `message` suggest the customer may leave for a competitor or cancel?"}}, "expected": {"churn_risk": true}, "tags": ["example"], "language": "ko"}
```

Check the format only, without a model:

```bash
.venv/bin/laya-evals validate data/evals/ko_klue_ynat_7.jsonl
```

---

## 3. Question schema design rules

A checklist followed by both the builder and the authors of the handwritten sets. Each item rests on measurements reported in the upstream documentation.

- [ ] **choice keys are ASCII snake_case semantic labels or opaque labels (A/B).** The criteria key is itself option text the model reads, and boolean-word keys such as `true/false/yes/no` have been reported to fail by following the label instead of the description (source: README.md "Honest limits" "Avoid boolean-word labels"). Korean keys are not used: their tokenizer budget (tokens per option) is worse than for English snake_case, and they blur the axis of comparison with the upstream figures.
- [ ] **criteria descriptions (values) are descriptive Korean by default.** What the model reads is the state (Korean) and the descriptions. Descriptive Korean descriptions are the default in every set, including scenario_18 and the PoC sets; English key rendering is used only in the two sets that follow the upstream construction exactly, `*_massive_intent_20opt.jsonl` (Track A reproduction) and `ko_massive_intent_full60.jsonl` (Track C6, same rendering as 20opt). For those two sets the ablation is `--descriptions ko` (`_ko-desc`, needs `data/handwritten/massive_intent_ko_desc.json`, which does not exist yet); for the other sets it is `--descriptions en` (`_en-desc`). Rationale: in P0c (n=100, `results/poc/P0c_20261002.md`), scenario-18 scored 0.52 with Korean descriptions vs 0.35 with upstream key rendering (McNemar p<0.001), and Korean instructions gave Δ0 on both sets, YNAT and scenario.
- [ ] **instructions are English by default; `--instructions ko` is the ablation.** Upstream's MASSIVE construction and presets all use English instructions (source: research/scripts/bench_local.py:175-177, laya/presets.py). Whether Korean instructions are better is measured by the Track B ablation.
- [ ] **Refer to state fields in backticks.** E.g. "What is the user asking for in `utterance`?". presets use this convention to trace the state key back (source: laya/presets.py `state_field`, `_STATE_FIELD_RE`). Questions that refer to two fields (NLI) are allowed; only the presets helper returns `None`, and inference is not affected.
- [ ] **At most 20 choice options.** The options share the `head_max_len` budget (multilingual 256, english 192), and the tokens per option are `max(4, (head_max_len - 16) // k)`, with a floor of 4. Banking77 (77 options) collapsed to exactly 0.425 on both checkpoints (source: README.md "Honest limits", BENCHMARKS.md "On the public datasets where Jev numbers exist"). The only exception is the `full60` probe in 5.1.
- [ ] **noul `criteria` keys are exactly `true`/`false`.** Other keys (`yes`/`no`) are rejected. To change the option pair the model reads, use `labels` (e.g. `{"true": "A", "false": "B"}`) (source: README.md "Honest limits" noul item, #156).
- [ ] **State per set whether noul has criteria.** A noul without criteria answers "no" on the english checkpoint regardless of the state, but multilingual reads the state (source: README.md "Honest limits"). Conversely, in the Chinese measurements, the more criteria, scenario and JSON state were added to noul, the more every question converged to "true" and accuracy dropped (source: research/benchmarks/zh_short_commands/README.md "The ladder"). Korean is routed to multilingual by the Hangul script (laya/lang.py:43), so both results may apply. The noul of the handwritten sets therefore defaults to **no criteria** in v1, as in presets, and criteria are added at run time in the wording-ladder ablation of 03. However, in the 2026-10-02 P0 probe (n=30, `results/poc/P0_20261002.md`) the criteria-less noul of multilingual almost always answered "no" on Korean input, so before the handwritten sets are frozen, `triage_v1b.json` (+criteria) and a 2-choice neutral-key variant are compared first and the v1 default is decided again. Sets where "what counts as true" is bound to the dataset definition, such as NSMC and K-MHaS, include criteria, and this is stated in §5. In the P0b ablation (n=30, `results/poc/P0b_20261002.md`), no binary form beat the always-no base rate (93/120) in total (V0 no criteria 93 = V2 labels A/B 93 = V8 combination 93, V1 criteria 87, V3a A/B 2-choice 68, collapsing toward A); only per question did churn_risk + Korean criteria 28/30 (6/6 positives correct) and is_urgent + Korean instructions 26/30 beat the base rate. The noul form of the PoC sets is therefore decided per question before freezing.
- [ ] **score criteria are a list of level descriptions; expected is an index.** A `null` level is rejected with 422 (source: README.md "Self-Hosting" "Score levels").
- [ ] **instructions and criteria strings do not change after freezing.** Even a single space changes `questions_sha256` (source: docs/evals.md "Run identity"). If the wording changes, make a v2 file.
- [ ] **Several questions on one state still take a single forward pass.** This is why NSMC's noul and choice variants go into one row. Adding questions, however, grows the head tokens and shrinks the room left for the state, so check with `--stats`.

---

## 4. Summary of the sets

| File (`data/evals/`) | Source | Task / primitive | Options | N | Track | Hypothesis |
|---|---|---|---|---|---|---|
| `ko_massive_intent_20opt.jsonl` | mteb/amazon_massive_intent `ko` test | intent classification / choice | 20 | 100 | A | multilingual 0.470 ± reproduction noise |
| `en_massive_intent_20opt.jsonl` | same source, `en` test | intent classification / choice | 20 | 100 | A | reproduce english 0.820, multilingual 0.710 |
| `ko_massive_intent_full60.jsonl` | the same 100 rows | high cardinality / choice | 59 (nominal 60) | 100 | C | collapses at the default budget, recovers with head 512 |
| `ko_massive_scenario_18.jsonl` | the same 100 rows, derived from the prefixes | domain classification / choice | 18 | 100 | B | higher than 20opt (similar number of options, larger semantic distance) |
| `ko_massive_domain_8.jsonl` | stratified sample from the whole mteb/amazon_massive_intent `ko` test split (2,974 rows) | **PoC main task** domain routing / choice | 8 | 500 (`--n 0` = 2,917 rows, after removing 55 exact-duplicate rows and 2 rows shorter than 2 characters) | B + PoC | higher than scenario_18 (P0c 0.52); PoC G1 input. Question dict byte-identical to `poc/schema/router_v1.json` (05 §4.1) |
| `en_massive_domain_8.jsonl` | `en` pair with the same ids | Korean penalty measurement / choice | 8 | same as the ko file | B (07 §5 method) | English ahead of ko by about 0.10 (Korean descriptions, 07 §5 E1) |
| `ko_klue_ynat_7.jsonl` | klue/klue `ynat` validation | news topic / choice | 7 | 500 | B | zero-shot 0.5\~0.7 (compare with the KLUE fine-tuned reference, macro-F1 0.85+) |
| `ko_klue_nli_3.jsonl` | klue/klue `nli` validation | NLI / choice | 3 | 500 | B | around XNLI non-English 0.731 (source: BENCHMARKS.md "English vs the rest") |
| `ko_nsmc_sentiment.jsonl` | e9t/nsmc ratings_test.txt | sentiment / noul + 2-choice | 2 | 500 | B | choice ≥ noul (noul label-following weakness) |
| `ko_kmhas_hate.jsonl` | jeanlee/kmhas test | hate or not / noul | 2 | 500 | B | reconfirm the weakness at the level of moderation held-out 0.53 |
| `ko_kmhas_type_8.jsonl` | same source, single-label hate rows | hate type / choice | 8 | 500 | B | measure confusion between types |
| `ko_3i4k_speechact_7.jsonl` | warnikchow/3i4k fci_test.txt | speech act / choice | 7 | 500 | B | high on telling questions from commands, low on the rhetorical types |
| `ko_negation_probe.jsonl` | handwritten (pairs) | negation / 2-choice + noul | 2 | 100 (50 pairs) | C | sharp accuracy drop on negated rows (reproducing #377) |
| `ko_poc_triage_v1.jsonl` | manual labels | **on hold** (scenario A fine-tuning candidate; labeling after the P4 decision) triage + gateway / 7 questions | 6·4·2·3 | 200\~300 | (P4) | excluded from the G1 input by the 05 §2 decision |

Derived files (generated by builder flags, with `derived_from` recorded in the MANIFEST; as of 2026-10-02 the `derived_from` of the 5 ablation variants is null and the builder is to be completed): `ko_nsmc_sentiment_noul.jsonl`, `ko_nsmc_sentiment_choice.jsonl` (`--split-variants`), `ko_3i4k_speechact_6.jsonl` (`--drop-fragments`), each set's `*_ko-instr.jsonl` (`--instructions ko`), `*_ko-desc.jsonl` (`--descriptions ko`, 20opt and full60 only), `*_en-desc.jsonl` (`--descriptions en`). Note: `_en-desc` means different things in different sets. The `_en-desc` of scenario_18 is upstream key rendering (`k.replace("_", " ")`), meant to reproduce P0c's 0.52 vs 0.35, while the `_en-desc` of domain_8 and YNAT is natural-language English descriptions. A natural-language English variant of scenario_18 needs a separate dict and was not built (`scripts/build_ko_evalsets.py:178` `variant`).

---

## 5. Per-source conversion specification

Common: **no** text normalization (not even NFC; source bytes as they are). Deduplication is on exact text matches. The upstream-faithful MASSIVE sets (20opt, full60, scenario_18, "first 100 rows" rule), however, are exempt from deduplication (the first 100 rows of ko test contain 3 exact-duplicate pairs, and upstream keeps them; `results/poc/P0c_20261002.md`); in that case the number of `duplicates` is recorded in the MANIFEST. Length filter: drop texts shorter than 2 characters (3i4K is the exception) and longer than 2,000 characters. Sampling is stratified: every label gets the quota `N // k`, and the first `N mod k` labels in criteria order get 1 more row each (total exactly N; e.g. YNAT 72/72/72/71×4, domain_8 63×4/62×4; `scripts/build_ko_evalsets.py:218` `stratify`). If a label falls short of its allocation, N is made up from the remaining pool with `random.Random(13)`. The actual distribution is recorded in the MANIFEST.

### 5.1 MASSIVE ko / en

**Source** `mteb/amazon_massive_intent`, configs `ko` and `en`, split `test`. Features `id`, `label`, `label_text` (e.g. `alarm_set`), `text` (e.g. "이번 주 오전 다섯 시 에 깨워줘"), `lang`. License CC BY 4.0 (per `NOTICE.md` of the original repository alexa/massive, checked 2026-10-12; the apache-2.0 in the `license` field of the HF mirror cards `mteb/amazon_massive_intent` and `_scenario` (checked 2026-10-02) is the mirror's own label; details in `DATA_LICENSES.md`).

**(a) `*_massive_intent_20opt.jsonl`: faithful upstream reproduction.** Follows the construction rules byte for byte (source: research/scripts/bench_local.py:165-183).

```python
d = load_dataset("mteb/amazon_massive_intent", lang, split="test")
labels = sorted(set(d["label_text"]))          # full intent set (59 on ko test; cooking_query is only in train; the full set is computed from the data), sorted
rng = random.Random(13)                         # created only once per language
for r in list(d)[:100]:                         # "first 100 rows" of the test split, no shuffle
    pool = [x for x in labels if x != r["label_text"]]
    keys = [r["label_text"]] + rng.sample(pool, 19)
    rng.shuffle(keys)
    criteria = {k: k.replace("_", " ").replace(".", ": ") for k in keys}
```

- state: `{"utterance": text}`; question id `intent`; instructions `"What is the user asking for in `utterance`?"`; criteria are the conversion above (English). Only with `--descriptions ko` are they replaced by `data/handwritten/massive_intent_ko_desc.json` (all intents; at build time `assert set(desc.keys()) == set(labels)`).
- expected: `{"intent": label_text}`. tags `["massive", "20opt", "scenario:<prefix>"]`, language `ko`/`en`.
- Figures to reproduce: ko 0.110 / 0.470, en 0.820 / 0.710 (source: BENCHMARKS.md:71 and the `en` row). Upstream extracted the logits directly with its own `score_cases` and applied the temperature, so there can be small differences from the `laya-evals` path (batch shape, dtype). The tolerance is set by Track A of 03_benchmark_plan.md.
- The sample selection rule is "first 100 rows", so there is no stratification. The gold label is always among the 20 options, so random baseline = 0.050.

```json
{"state": {"utterance": "이번 주 오전 다섯 시 에 깨워줘"}, "questions": {"intent": {"type": "choice", "instructions": "What is the user asking for in `utterance`?", "criteria": {"alarm_set": "alarm set", "weather_query": "weather query", "play_music": "play music", "calendar_remove": "calendar remove"}}}, "expected": {"intent": "alarm_set"}, "tags": ["massive", "20opt", "scenario:alarm"], "language": "ko"}
```

(For space, the example above lists only 4 options. The actual file always has 20.)

**(b) `ko_massive_intent_full60.jsonl`: high-cardinality probe.** For the same 100 rows, the whole `labels` set (fixed sorted order) is given as the options of a single question (the 60 in the name is nominal; the actual number of options is the number of intents in the data = 59 on ko test). The default criteria are the same English key rendering as 20opt, and `--descriptions ko` (`_ko-desc`) works only when `data/handwritten/massive_intent_ko_desc.json` exists (one entry per intent in the data, 59 on ko test; at build time `assert set(desc.keys()) == set(labels)`). That file does not exist yet (optional). tags `["massive", "high_cardinality"]`. Expectation: at the default `head_max_len=256`, the tokens per option are `max(4, (256-16)//59) = 4`, the labels become indistinguishable, and accuracy collapses. Track C of 03 reruns the same file with `head_max_len=512, max_len=1024` and with `predict_shortlist(k=20)` (source: README.md "Honest limits" high-cardinality item). The option order is kept fixed and sorted to separate the order effect from Track C's option-order probe.

**(c) `ko_massive_scenario_18.jsonl`: domain classification.** The scenario is derived as the prefix before the first `_` of `label_text`. Prefix set: alarm, audio, calendar, cooking, datetime, email, general, iot, lists, music, news, play, qa, recommendation, social, takeaway, transport, weather. The builder asserts `len(set(prefixes)) == 18` and, on a mismatch, corrects the mapping table against the scenario field of `mteb/amazon_massive_scenario`. Same 100 rows, 18 options in fixed sorted order, descriptions in Korean (table below). Question id `scenario`, instructions `"Which domain does `utterance` belong to?"`, tags `["massive", "scenario18"]`. The `_en-desc` variant of this set is not natural-language English descriptions but upstream key rendering (`k.replace("_", " ")`). It serves to reproduce P0c's comparison of Korean descriptions 0.52 vs key rendering 0.35, and it mixes the language effect with the effect of description richness. A natural-language English description variant needs a separate dict and was not built.

| key | Korean description | key | Korean description |
|---|---|---|---|
| alarm | 알람 설정, 해제, 조회 | music | 음악 취향, 재생 설정 |
| audio | 음량 조절, 음소거 | news | 뉴스 조회 |
| calendar | 일정 등록, 조회, 삭제 | play | 음악, 라디오, 팟캐스트, 오디오북, 게임 재생 |
| cooking | 요리법, 조리 질문 | qa | 사실, 정의, 수학, 환율, 주식 질문 |
| datetime | 날짜와 시간 질문, 시간대 변환 | recommendation | 장소, 이벤트, 영화 추천 |
| email | 이메일 확인, 전송, 연락처 | social | 소셜 미디어 게시, 조회 |
| general | 잡담, 농담, 일반적인 대화 | takeaway | 음식 주문, 배달 조회 |
| iot | 조명, 커피머신, 청소기 등 스마트홈 기기 제어 | transport | 교통, 택시, 티켓, 길 안내 |
| lists | 목록 만들기, 항목 추가, 삭제, 조회 | weather | 날씨 질문 |

**(d) `ko_massive_domain_8.jsonl` / `en_massive_domain_8.jsonl`: PoC main task, 8-domain routing.** The 18 scenarios are merged into 8 non-overlapping domains, because in P0c most errors among the 18 domains came from pairs whose definitions overlap or are adjacent, such as play↔music (14/17), audio→general and iot→alarm, and merging only play/music already took accuracy from 0.52 → 0.66 (`results/poc/P0c_20261002.md`). The canonical copy of the question dict is `poc/schema/router_v1.json` (05 §4.1). The builder asserts a byte match if that file exists, and otherwise only warns and proceeds (the file did not exist at build time).

| key | Merged scenarios | Korean description |
|---|---|---|
| productivity | alarm, calendar, datetime, lists | 알람, 일정, 날짜와 시간, 할 일과 쇼핑 목록 |
| media | music, play, audio | 음악, 라디오, 팟캐스트, 오디오북 재생과 음량 조절 |
| smart_home | iot | 조명, 커피머신, 청소기, 플러그 등 스마트홈 기기 제어 |
| info_qa | qa, weather, news | 사실, 정의, 계산, 환율, 날씨, 뉴스 등 정보 질문 |
| communication | email, social | 이메일, 연락처, 소셜 미디어 게시와 확인 |
| lifestyle | takeaway, cooking, recommendation | 음식 주문과 배달, 요리법, 장소·이벤트·영화 추천 |
| transport | transport | 교통, 택시, 티켓, 길 안내 |
| general | general | 인사, 잡담, 농담, 위 어디에도 속하지 않는 일반 대화 |

- Source: config `ko`, split `test` **in full** (2,974 rows; not the "first 100 rows" rule of (a)\~(c)). Exact-duplicate texts (55 rows) and texts shorter than 2 characters (2 rows, '랩'·'락') are removed before sampling (this set is not exempt from deduplication). Stratified with a per-domain quota of 62 plus 1 row each for the first 4 domains (63×4, 62×4), seed 13, sorted by `id`. With `--n 0`, all 2,917 rows (`scripts/build_ko_evalsets.py:367` `massive_domain`).
- en pair: the `en` test rows with **the same `id`** as the rows in the ko file are used with the same question and the same expected (MASSIVE is a parallel corpus across locales). The builder asserts for every pair that `label_text` matches. `language: "en"`. Used for the Korean penalty measurement of 07 §5 E1 (paired McNemar).
- Non-overlap check: the builder prints the intersection of the word (eojeol) sets of the 8 descriptions (as of 2026-10-02 not implemented in `scripts/build_ko_evalsets.py`; checked by hand). Particles, bound nouns (e.g. "등", "etc.") and comma tokens are excluded from the count. The current intersection is only the "등" shared by smart_home and info_qa, so the check passes. If content words overlap without an exclusion rule, a `router_v2.json` with revised descriptions is made and the set is regenerated as well. `massive --split train` (for P4 training data) is not implemented (TODO).
- Question id `domain`, instructions `"Which domain should handle the request in `utterance`?"`, criteria order fixed to the order of the table above (C1 measures permutation flips). state `{"utterance": text}`, expected = the merged key, tags `["massive", "domain8", "scenario:<original scenario>"]`.
- Question dict:

```json
{
  "domain": {
    "type": "choice",
    "instructions": "Which domain should handle the request in `utterance`?",
    "criteria": {
      "productivity": "알람, 일정, 날짜와 시간, 할 일과 쇼핑 목록",
      "media": "음악, 라디오, 팟캐스트, 오디오북 재생과 음량 조절",
      "smart_home": "조명, 커피머신, 청소기, 플러그 등 스마트홈 기기 제어",
      "info_qa": "사실, 정의, 계산, 환율, 날씨, 뉴스 등 정보 질문",
      "communication": "이메일, 연락처, 소셜 미디어 게시와 확인",
      "lifestyle": "음식 주문과 배달, 요리법, 장소·이벤트·영화 추천",
      "transport": "교통, 택시, 티켓, 길 안내",
      "general": "인사, 잡담, 농담, 위 어디에도 속하지 않는 일반 대화"
    }
  }
}
```

```json
{"state": {"utterance": "이번 주 오전 다섯 시 에 깨워줘"}, "questions": {"domain": {"type": "choice", "instructions": "Which domain should handle the request in `utterance`?", "criteria": {"productivity": "알람, 일정, 날짜와 시간, 할 일과 쇼핑 목록", "media": "음악, 라디오, 팟캐스트, 오디오북 재생과 음량 조절", "smart_home": "조명, 커피머신, 청소기, 플러그 등 스마트홈 기기 제어", "info_qa": "사실, 정의, 계산, 환율, 날씨, 뉴스 등 정보 질문", "communication": "이메일, 연락처, 소셜 미디어 게시와 확인", "lifestyle": "음식 주문과 배달, 요리법, 장소·이벤트·영화 추천", "transport": "교통, 택시, 티켓, 길 안내", "general": "인사, 잡담, 농담, 위 어디에도 속하지 않는 일반 대화"}}}, "expected": {"domain": "productivity"}, "tags": ["massive", "domain8", "scenario:alarm"], "language": "ko"}
```

### 5.2 KLUE YNAT (news topic 7)

**Source** `klue/klue` config `ynat`, split `validation` (9,107 rows; test is not public). Features `guid`, `title`, `label` ClassLabel `["IT과학","경제","사회","생활문화","세계","스포츠","정치"]`. License CC BY-SA 4.0 (KLUE GitHub README and HF card YAML, checked 2026-10-12).

- Sampling N=500, cap of 72 per label, seed 13.
- state `{"headline": title}`. Titles are short news headlines of 20\~40 characters on average, so the token budget is no problem. Note: this task is "topic classification of short headlines", and its distribution differs from customer inquiries. In Track B it is read only as an indicator of "general Korean classification ability".
- Mapping:

| label idx | Original label | key | Korean description |
|---|---|---|---|
| 0 | IT과학 | it_science | IT, 과학, 기술, 통신, 인터넷 |
| 1 | 경제 | economy | 경제, 금융, 산업, 기업, 부동산 |
| 2 | 사회 | society | 사회, 사건사고, 교육, 노동, 복지 |
| 3 | 생활문화 | culture_life | 생활, 문화, 예술, 건강, 여행, 음식 |
| 4 | 세계 | world | 국제, 해외 뉴스, 외교 |
| 5 | 스포츠 | sports | 스포츠, 경기, 선수 |
| 6 | 정치 | politics | 정치, 국회, 정당, 선거, 정부 |

```json
{"state": {"headline": "5억원 무이자 융자는 되고 7천만원 이사비는 안된다"}, "questions": {"topic": {"type": "choice", "instructions": "Which news section does `headline` belong to?", "criteria": {"it_science": "IT, 과학, 기술, 통신, 인터넷", "economy": "경제, 금융, 산업, 기업, 부동산", "society": "사회, 사건사고, 교육, 노동, 복지", "culture_life": "생활, 문화, 예술, 건강, 여행, 음식", "world": "국제, 해외 뉴스, 외교", "sports": "스포츠, 경기, 선수", "politics": "정치, 국회, 정당, 선거, 정부"}}}, "expected": {"topic": "society"}, "tags": ["klue", "ynat"], "language": "ko"}
```

### 5.3 KLUE NLI (3-way)

**Source** `klue/klue` config `nli`, split `validation` (3,000 rows). Features `guid`, `source`, `premise`, `hypothesis`, `label` `["entailment","neutral","contradiction"]`. Alternative source: `kakaobrain/kor_nli` config `xnli` (validation/test, same labels), used only if KLUE is unavailable. License CC BY-SA 4.0 (KLUE GitHub README and HF card YAML, checked 2026-10-12).

- Sampling N=500, cap of 167 per label. `source:<airbnb|...>` goes into the tags to allow per-domain slicing.
- state `{"premise": ..., "hypothesis": ...}`. The instructions refer to both fields. The two sentences are not concatenated into one string because the model is designed to read a JSON-serialized dict state (source: README.md "Quickstart: Route Mode" description of state), and the field boundary must be preserved for the wording ablation to be possible.
- Upstream's XNLI figure (non-English multilingual 0.731) was measured as a 3-way choice, so the same primitive is used.

```json
{"state": {"premise": "흡연자분들은 발코니가 있는 방이면 발코니에서 흡연이 가능합니다.", "hypothesis": "어떤 방에서도 흡연은 금지됩니다."}, "questions": {"relation": {"type": "choice", "instructions": "Given `premise`, how does `hypothesis` relate to it?", "criteria": {"entailment": "전제가 참이면 가설도 반드시 참이다", "neutral": "전제만으로는 가설의 참 거짓을 알 수 없다", "contradiction": "전제가 참이면 가설은 거짓이다"}}}, "expected": {"relation": "contradiction"}, "tags": ["klue", "nli", "source:airbnb"], "language": "ko"}
```

### 5.4 NSMC (movie review sentiment)

**Source** HF `e9t/nsmc` is a script-based dataset, so datasets-server returns 501 and loading is unstable in `datasets` 4.x. The original TSV is downloaded directly: `https://raw.githubusercontent.com/e9t/nsmc/master/ratings_test.txt` (50,000 rows, header `id\tdocument\tlabel`, label 1 = positive). It is saved to `data/raw/nsmc/ratings_test.txt` (not included in the public repository), and its sha256 is recorded in the MANIFEST. License CC0 1.0 (e9t/nsmc README, checked 2026-10-12).

- Preprocessing: drop rows whose `document` is empty or NaN, drop texts shorter than 2 characters (e.g. "굳 ㅋ" is 3 characters and is kept), remove exact duplicates. N=500, balanced 250/250.
- **Two questions per row.** `sentiment_noul` (noul) and `sentiment_choice` (2-choice) go into the same `questions`, so a single forward pass compares the two primitives. `laya-evals --slice qid` gives per-question metrics. Default hypothesis: if the noul label following reported for the English checkpoint (#156) also shows up for multilingual and Korean, `sentiment_choice` accuracy is higher (source: README.md "Honest limits" noul item).
- noul gets criteria: the definition of "positive" is bound to the dataset, and the keys must be exactly `true`/`false`. The `--opaque-labels` flag is an ablation that adds `labels: {"true": "A", "false": "B"}`.
- The choice keys are `positive`/`negative` (semantic labels, not boolean words). `--opaque-keys` is an ablation that changes them to `A`/`B` (the workaround the README recommends).
- `--split-variants` derives two single-question files (`ko_nsmc_sentiment_noul.jsonl`, `ko_nsmc_sentiment_choice.jsonl`). Purpose: when per-primitive baseline files are gated independently with `--baseline`, `questions_sha256` stays clean. The canonical file is the two-question version.

```json
{"state": {"document": "지루하지는 않은데 완전 막장임... 돈주고 보기에는...."}, "questions": {"sentiment_noul": {"type": "noul", "instructions": "Is the movie review in `document` positive?", "criteria": {"true": "영화를 긍정적으로 평가한다", "false": "영화를 부정적으로 평가한다"}}, "sentiment_choice": {"type": "choice", "instructions": "What is the sentiment of the movie review in `document`?", "criteria": {"positive": "영화를 긍정적으로 평가한다", "negative": "영화를 부정적으로 평가한다"}}}, "expected": {"sentiment_noul": false, "sentiment_choice": "negative"}, "tags": ["nsmc"], "language": "ko"}
```

### 5.5 K-MHaS (Korean hate speech)

**Source** `jeanlee/kmhas_korean_hate_speech`, split `test`. Features `text`, `label` = Sequence of ClassLabel `["origin","physical","politics","profanity","age","gender","race","religion","not_hate_speech"]` (idx 8 = not hate, multi-label). Loading caveat: the main branch is script-based, so datasets 5.x refuses it with "Dataset scripts are no longer supported". The builder loads `default/test/0000.parquet` of the Hub parquet export `refs/convert/parquet @5df3b7429d68f0ffc89dfbd0159cc72f29fad63c` (21,939 rows, same names for the 9 ClassLabels; `scripts/build_ko_evalsets.py:44-48`). Alternative source: `smilegate-ai/kor_unsmile` (`문장` + 10 label columns + `clean`), only mentioned in this document. License CC BY-SA 4.0 (stated only on the HF card, checked 2026-10-12; the paper and the GitHub repository state no license).

**(a) `ko_kmhas_hate.jsonl`: hate-or-not noul.** `is_hate = (8 not in label)`. N=500, balanced 250/250. Multi-label rows are included as they are (no effect on the yes/no decision). Criteria are included because the scope of "hate" is bound to the dataset guidelines. Upstream's held-out moderation scored 0.530 (macro-F1 0.400), close to chance (source: BENCHMARKS.md "Themes"); the hypothesis is whether the same weakness reproduces in Korean. tags `["kmhas", "hate"|"clean", "multi_label"(if applicable)]`.

```json
{"state": {"comment": "그만큼 길예르모가 잘했다고 보면되겠지 기대되네 셰이프 오브 워터"}, "questions": {"is_hate": {"type": "noul", "instructions": "Does `comment` contain hate speech or abusive language toward a person or group?", "criteria": {"true": "출신, 외모, 정치 성향, 욕설, 연령, 성별, 인종, 종교를 근거로 비하하거나 공격한다", "false": "비하나 공격이 없는 일반적인 댓글이다"}}}, "expected": {"is_hate": false}, "tags": ["kmhas", "clean"], "language": "ko"}
```

**(b) `ko_kmhas_type_8.jsonl`: hate-type choice.** Only rows whose `label` has length 1 and a value in 0..7 are used (multi-label rows have two gold labels and do not fit a choice). N=500, per-label quota 62 (+1 row for the first 4); types that fall short contribute everything available. Question id `hate_type`, instructions `"Which kind of hate speech does `comment` express?"`, tags `["kmhas", "hate_type"]`. Actual distribution: test has only 27 single-label `race` rows, so race 27 plus top-ups from the remaining pool fill the 500 rows (politics 72, origin 70, profanity 69, physical 68, gender 66, age 65, religion 63, race 27; `data/evals/MANIFEST.json`).

| idx | key | Korean description | idx | key | Korean description |
|---|---|---|---|---|---|
| 0 | origin | 출신 지역이나 국가를 근거로 비하 | 4 | age | 나이, 세대를 근거로 비하 |
| 1 | physical | 외모, 신체를 근거로 비하 | 5 | gender | 성별을 근거로 비하 |
| 2 | politics | 정치 성향, 정치인을 근거로 비하 | 6 | race | 인종, 민족을 근거로 비하 |
| 3 | profanity | 대상 없는 욕설, 저속한 표현 | 7 | religion | 종교를 근거로 비하 |

### 5.6 3i4K (speech act 7)

**Source** HF `kor_3i4k` is script-based, and datasets-server returns 404. The original is downloaded directly: `https://raw.githubusercontent.com/warnikchow/3i4k/master/data/train_val_test/fci_test.txt` (format `label\ttext`, label 0..6). License CC BY-SA 4.0 (repository LICENSE file; README "We updated our LICENSE to CC-BY-SA-4.0"; checked 2026-10-12).

| label | key | Korean description |
|---|---|---|
| 0 | fragment | 문장이 아닌 단어나 구 조각 |
| 1 | statement | 사실이나 의견을 전달하는 서술 |
| 2 | question | 정보를 요구하는 질문 |
| 3 | command | 행동을 요구하는 명령이나 요청 |
| 4 | rhetorical_question | 대답을 기대하지 않는 수사적 질문 |
| 5 | rhetorical_command | 실제 행동을 요구하지 않는 수사적 명령 |
| 6 | intonation_dependent | 억양에 따라 의미가 달라지는 발화 |

- **Decision: keep 7-way; fragment rows get `fragment` in `tags`.** The file name `_7` is already referenced in other documents, the set must be comparable with 3i4K's published reference (7-way F1), and telling "fragment or not" is itself a meaningful decision in voice front-end routing. Unlike the README's problem that "short Latin text carries no language signal", a one-word state in Hangul is routed to multilingual by the script alone, so there is no routing failure. If 6-way is needed, `ko_3i4k_speechact_6.jsonl` is derived with `--drop-fragments`. It is derived as the subset of the 7-way 500 rows without the `fragment` rows (no resampling) and recorded in MANIFEST `derived_from`.
- 3i4K does not apply the shorter-than-2-characters filter (one-character fragments are valid data). N=500, cap of 72 per label.
- state `{"utterance": text}`, question id `speech_act`, instructions `"What kind of speech act is `utterance`?"`.

```json
{"state": {"utterance": "오늘 회의 몇 시에 시작해요"}, "questions": {"speech_act": {"type": "choice", "instructions": "What kind of speech act is `utterance`?", "criteria": {"fragment": "문장이 아닌 단어나 구 조각", "statement": "사실이나 의견을 전달하는 서술", "question": "정보를 요구하는 질문", "command": "행동을 요구하는 명령이나 요청", "rhetorical_question": "대답을 기대하지 않는 수사적 질문", "rhetorical_command": "실제 행동을 요구하지 않는 수사적 명령", "intonation_dependent": "억양에 따라 의미가 달라지는 발화"}}}, "expected": {"speech_act": "question"}, "tags": ["3i4k"], "language": "ko"}
```

(The example sentence is invented for illustration; the actual file contains only source rows.)

### 5.7 Negation probe (`ko_negation_probe.jsonl`)

**Source** Handwritten. The builder validates and copies `data/handwritten/negation_pairs.jsonl`. The README reports that on the 5 cancellation examples of #377 all 4 negated requests were classified as `cancel_account`, one of them with probability 0.9998 (source: README.md "Honest limits" "Semantic choice labels do not make negation safe"). Korean negation comes in many forms, such as "\~하고 싶지 않다", "\~하지는 않을게요" and "\~만 빼고", so we measure whether the English result carries over as it is.

- Composition: 5 domains (cancellation, refund, data deletion, notification opt-out, plan change) × 10 pairs = 50 pairs, 100 rows. Each pair keeps the same core verb and is written as an affirmative request and an explicitly negated request. At least half of the negated rows take the form "does not want + asks for an alternative" (to check whether the model reads the alternative).
- Two questions: `action` (2-choice, a semantic key pair per domain, e.g. `cancel_account`/`keep_account`) and `wants_cancel` (noul, no criteria). The key pair per domain is determined by the `domain` field of `negation_pairs.jsonl`, and the builder holds them as a table.
- tags `["negation", "positive"|"negated", "pair:<nn>", "domain:<name>"]`. The analysis script of 03 uses the `pair:` tag to compute pair-level consistency (both correct).
- Label policy: affirmative rows expected = action key / `true`, negated rows = non-action key / `false`. Ambiguous sentences (conditional requests etc.) are not included.

```json
{"state": {"message": "계정을 해지하고 싶어요. 절차 알려주세요."}, "questions": {"action": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"cancel_account": "계정이나 서비스 해지를 원한다", "keep_account": "해지를 원하지 않는다. 유지하거나 다른 조치를 원한다"}}, "wants_cancel": {"type": "noul", "instructions": "Does the customer in `message` want to cancel the account?"}}, "expected": {"action": "cancel_account", "wants_cancel": true}, "tags": ["negation", "positive", "pair:01", "domain:cancellation"], "language": "ko"}
{"state": {"message": "계정을 해지하고 싶지는 않아요. 요금제만 더 싼 걸로 바꿔주세요."}, "questions": {"action": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"cancel_account": "계정이나 서비스 해지를 원한다", "keep_account": "해지를 원하지 않는다. 유지하거나 다른 조치를 원한다"}}, "wants_cancel": {"type": "noul", "instructions": "Does the customer in `message` want to cancel the account?"}}, "expected": {"action": "keep_account", "wants_cancel": false}, "tags": ["negation", "negated", "pair:01", "domain:cancellation"], "language": "ko"}
```

### 5.8 PoC triage set (`ko_poc_triage_v1.jsonl`)

**On hold (2026-10-02): with scenario C chosen (05 §2), this set is built only after P4 fine-tuning is decided.** The specification below is kept for that case.

**Source** Manual labels. At least 200 rows of Korean customer inquiries, target 300 rows. The sentences are invented or paraphrased from public Korean CS-style text; no real customer data or PII is used. The schema must be identical to the PoC v1 schema of 05_poc_plan.md §4 (down to the question ids, keys and description strings). The canonical copies are `poc/schema/triage_v1.json` + `poc/schema/gateway_v1.json` (05 §4), and the strings in this section must be byte-identical to them. The builder's `poc` subcommand reads the two files to build the `questions` dict and asserts there is no diff with the dict in this section. This section specifies that schema as `laya.presets.triage_questions` with Korean descriptions attached (source: laya/presets.py `triage_questions`) plus 2 gateway questions (docs/use-cases.md §1). If 05 changes, this section and the set are regenerated as v2.

- **Freeze the label policy first.** Write `data/handwritten/poc_triage_label_policy_v1.md` first with the template of 06_templates.md §4, record its sha256 in the MANIFEST's `label_policy_sha256`, and only then start labeling. Either 2 labelers label independently and the disagreements are adjudicated, or 1 labeler labels + a separate adjudication pass. The disagreement rate (Cohen's κ or simple agreement rate) is recorded in the MANIFEST.
- state `{"message": text}`. presets refer to the `message` field, so it is used as it is.
- The 7 questions (triage 5 + gateway 2) and their expected rules:

| Question id | type | expected | Notes |
|---|---|---|---|
| `intent` | choice (6) | key string | With several intents, the single one "the customer wants resolved first" |
| `is_urgent` | noul | true/false | true only when there is an explicit expression of time pressure, such as a deadline, "immediately" or "urgent" |
| `frustration` | score (4) | 0..3 | 0 calm, 1 worried/polite, 2 clearly annoyed, 3 very angry/strong language |
| `refund_requested` | noul | true/false | Explicitly asks for money back |
| `churn_risk` | noul | true/false | Mentions cancellation, leaving or a competitor |
| `needs_llm` | noul | true/false | true if a templated action (queue assignment, canned reply, status lookup) is not enough and a generated reply is needed, e.g. explaining an individual situation, persuasion or a compound query (05 §4.2 gateway) |
| `complexity` | choice (3) | key string | canned: greetings, standard FAQ, simple status checks / structured: deterministically handled by an API or template / complex: generated reply, multi-step reasoning, compound analysis (source: docs/use-cases.md §1) |

- The full `questions` dict (Korean descriptions, English instructions, noul without criteria as in presets; byte-identical to the merged `questions` of `poc/schema/triage_v1.json` and `gateway_v1.json`):

```json
{"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}, "is_urgent": {"type": "noul", "instructions": "Does `message` communicate time pressure or a deadline?"}, "frustration": {"type": "score", "instructions": "How frustrated does the customer sound in `message`?", "criteria": ["차분하고 중립적", "걱정하지만 정중함", "분명히 짜증남", "매우 화남 또는 강한 표현 사용"]}, "refund_requested": {"type": "noul", "instructions": "Does the customer ask for money back?"}, "churn_risk": {"type": "noul", "instructions": "Does `message` suggest the customer may leave for a competitor or cancel?"}, "needs_llm": {"type": "noul", "instructions": "Does answering `message` require a free-form generated reply rather than a templated action?"}, "complexity": {"type": "choice", "instructions": "How complex is the request in `message`?", "criteria": {"canned": "인사, 표준 FAQ, 단순 상태 확인", "structured": "API나 템플릿으로 결정적으로 처리 가능한 요청", "complex": "생성형 답변, 다단계 추론, 복합 분석이 필요한 요청"}}}
```

- tags `["poc", "intent:<key>", "channel:<chat|email|voice>"]`, language `ko`. At least 25 rows per intent, and at least 25 rows for `other` as well (thank-you messages, misdirected inquiries, etc.).
- 6 example rows (1 row per intent, with all seven expected values; for space, `questions` lists only `intent`, while the actual file holds the whole dict above. The 6 rows below are therefore illustrative and are rejected if fed to `laya-evals validate` as they are; see the note below):

```json
{"state": {"message": "지난달에 결제가 두 번 됐어요. 중복 결제된 건 오늘 중으로 환불해 주세요. 안 그러면 다른 서비스로 옮길 겁니다."}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}}, "expected": {"intent": "refund", "is_urgent": true, "frustration": 2, "refund_requested": true, "churn_risk": true, "needs_llm": false, "complexity": "structured"}, "tags": ["poc", "intent:refund", "channel:chat"], "language": "ko"}
{"state": {"message": "앱에서 사진을 업로드하면 매번 튕깁니다. 어제 업데이트 이후부터 그래요."}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}}, "expected": {"intent": "technical_help", "is_urgent": false, "frustration": 1, "refund_requested": false, "churn_risk": false, "needs_llm": true, "complexity": "complex"}, "tags": ["poc", "intent:technical_help", "channel:chat"], "language": "ko"}
{"state": {"message": "이번 달 청구서에 부가세가 따로 붙었는데, 요금제 가격에 포함된 게 아닌가요?"}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}}, "expected": {"intent": "billing_question", "is_urgent": false, "frustration": 0, "refund_requested": false, "churn_risk": false, "needs_llm": true, "complexity": "structured"}, "tags": ["poc", "intent:billing_question", "channel:email"], "language": "ko"}
{"state": {"message": "팀 플랜으로 바꾸면 사용자를 몇 명까지 추가할 수 있나요?"}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}}, "expected": {"intent": "information", "is_urgent": false, "frustration": 0, "refund_requested": false, "churn_risk": false, "needs_llm": false, "complexity": "canned"}, "tags": ["poc", "intent:information", "channel:chat"], "language": "ko"}
{"state": {"message": "다음 달부터 서비스 해지하려고 합니다. 해지 절차 안내해 주세요."}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}}, "expected": {"intent": "cancellation", "is_urgent": false, "frustration": 0, "refund_requested": false, "churn_risk": true, "needs_llm": false, "complexity": "structured"}, "tags": ["poc", "intent:cancellation", "channel:email"], "language": "ko"}
{"state": {"message": "담당자분이 친절하게 응대해 주셔서 감사합니다. 좋은 하루 보내세요."}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}}, "expected": {"intent": "other", "is_urgent": false, "frustration": 0, "refund_requested": false, "churn_risk": false, "needs_llm": false, "complexity": "canned"}, "tags": ["poc", "intent:other", "channel:chat"], "language": "ko"}
```

Note: the `questions` of the 6 rows above list only `intent`. The actual file must contain all seven questions for all seven `expected` keys to be scored. `laya-evals validate` rejects `expected` keys missing from `questions` with "'expected' names unknown question(s)" (source: laya/evals.py:92-94), so putting the examples above into a file as they are makes validate fail. The builder's `poc` subcommand checks the presence and types of the 7 keys itself before that.

---

## 6. Build-script specification

`scripts/build_ko_evalsets.py`, a single file, depending only on the standard library + `datasets` + `pandas` + `laya` (for validate and fingerprint). Always run with the venv's Python.

**Subcommands**

| Subcommand | Output | Notes |
|---|---|---|
| `all` | Everything except the handwritten sets + MANIFEST (including the ko·en pair of `massive --mode domain`) | `negation`, `poc` are included only when their sources exist |
| `massive --lang ko\|en --mode 20opt\|full\|scenario\|domain [--split test\|train]` | 5.1 (a)(b)(c)(d) | `--lang en` is allowed for `20opt` and `domain` (`domain` builds the pair with the same ids as the ko file). `--split train` is for `domain` only, for P4 fine-tuning training data |
| `ynat`, `nli`, `nsmc`, `kmhas`, `i4k` | 5.2\~5.6 | `kmhas` writes both files together |
| `negation` | 5.7 | Validates and copies `data/handwritten/negation_pairs.jsonl` |
| `poc` | 5.8 | Validates and converts `data/handwritten/poc_triage_v1.csv` or `.jsonl`. Checks that the label-policy file exists and its sha256 |
| `manifest` | Recomputes `MANIFEST.json` | Does not touch the files |
| `stats FILE...` | Token length and distribution report | §7 |

**Common flags** `--n N` (0 = all), `--seed 13`, `--instructions en|ko`, `--descriptions ko|en`, `--out data/evals/`, `--raw data/raw/`, `--force`, `--split-variants` (nsmc), `--drop-fragments` (i4k), `--opaque-keys`·`--opaque-labels` (nsmc). When an ablation flag is on, a suffix (`_ko-instr`, `_ko-desc`, `_en-desc`, `_opaque-keys`, `_opaque-labels`, `_6`) is added to the output file name so the canonical file is not overwritten.

**Behavior contract**

1. Deterministic: the same input, flags and source sha256 give the same output bytes. Labels are sorted, and sampling uses a single `random.Random(seed)` created at the start of each set.
2. Idempotent: if the output file exists with the same sha256, it is skipped. If it differs, the build stops unless `--force` is given and prints both sha256 values (protecting frozen files).
3. `laya-evals validate` is run as a subprocess on every output, and the build fails unless it exits 0.
4. `questions_sha256` is computed with `laya.evals.questions_fingerprint(laya.evals.Dataset.from_jsonl(path))` (source: docs/evals.md "Run identity", public API).
5. Originals are saved in `data/raw/<source>/` (not included in the public repository), and their sha256 is recorded. For HF datasets, setting `HF_HOME` to `data/raw/hf` keeps the cache inside the project.
6. Network: HF dataset and GitHub raw downloads are needed, so `HF_HUB_OFFLINE` is unset during the build. No checkpoint is loaded (only `stats` reads the tokenizer from the local `models/laya-multilingual/tokenizer` (not included in the public repository)).
7. The first line of each file records the source, build arguments and creation date as a `#` comment (the zh_decision_bench.jsonl convention; source: research/evals/zh_decision_bench.jsonl lines 1\~3). The creation date is not the actual time but a constant `CREATED` fixed per set version (`scripts/build_ko_evalsets.py:34`); only then does the byte-identical rebuild of rule 1 hold. The actual creation time is recorded only in the MANIFEST's `created_at`.

**MANIFEST.json schema** (per-file entries, one example):

```json
{"version": 1, "builder_version": "0.1.0", "laya_version": "0.3.23", "created_at": "2026-10-02T00:00:00+09:00", "files": {"ko_klue_ynat_7.jsonl": {"path": "data/evals/ko_klue_ynat_7.jsonl", "sha256": "<64 hex>", "questions_sha256": "<hex>", "n": 500, "source": {"dataset": "klue/klue", "config": "ynat", "split": "validation", "revision": "<hf dataset sha>"}, "license": "CC BY-SA 4.0 (확인 필요)", "in_training_mix": "unknown", "build_args": {"n": 500, "seed": 13, "instructions": "en", "descriptions": "ko"}, "label_distribution": {"it_science": 72, "economy": 72, "society": 72, "culture_life": 71, "world": 71, "sports": 71, "politics": 71}, "majority_rate": 0.144, "derived_from": null, "label_policy_sha256": null}}}
```

`in_training_mix` is filled in by `manifest`: the value in the header if there is one, otherwise the per-source-dataset table `TRAINING_MIX` (`scripts/build_ko_evalsets.py:56-59`), and "unknown" if neither has one. For the MASSIVE-derived sets (ko·en) it is "held out (upstream build_benchmark_nb.py:760-762; base checkpoints. ft-v1 was trained on MASSIVE ko train, see results/P4)", and for sources without upstream evidence, like KLUE in the example above, it is "unknown". This value does not depend on the bytes of the set files (MANIFEST regenerated on 2026-10-07, set sha256 unchanged). Handwritten sets additionally fill the `label_policy_sha256`, `labellers` and `agreement` (agreement rate or κ) fields. `majority_rate` is the majority-class baseline of Track F. A file with two questions (`ko_nsmc_sentiment.jsonl`) records `label_distribution` and `majority_rate` as dicts keyed by question id.

**Commands**

```bash
cd .
export HF_HOME=$PWD/data/raw/hf
unset HF_HUB_OFFLINE

# full build (public sources) + MANIFEST
.venv/bin/python scripts/build_ko_evalsets.py all --n 500 --seed 13

# single set, ablation variants
.venv/bin/python scripts/build_ko_evalsets.py massive --lang ko --mode 20opt
.venv/bin/python scripts/build_ko_evalsets.py massive --lang ko --mode domain --n 500     # PoC main task
.venv/bin/python scripts/build_ko_evalsets.py massive --lang en --mode domain --n 500     # en pair with the same ids
.venv/bin/python scripts/build_ko_evalsets.py ynat --instructions ko
.venv/bin/python scripts/build_ko_evalsets.py nsmc --split-variants

# apply the handwritten sets, recompute MANIFEST
.venv/bin/python scripts/build_ko_evalsets.py negation
.venv/bin/python scripts/build_ko_evalsets.py poc
.venv/bin/python scripts/build_ko_evalsets.py manifest
```

---

## 7. Quality checks and freezing

| Check | Criterion | Method |
|---|---|---|
| Format | `laya-evals validate` exit 0 | Run automatically by the builder |
| Label distribution | Matches the cap rule, no extreme imbalance | Check MANIFEST `label_distribution` |
| majority rate | Recorded | MANIFEST `majority_rate` |
| Duplicates | 0 exact duplicates within a set (the faithful MASSIVE sets are exempt; only the number of `duplicates` is recorded) | Builder assert |
| Token length | state token p99 < actual room | `stats` subcommand |
| Eyeball check | Labels of 10 random rows per set are valid | Manual; note the result in the run card |
| Handwritten sets | Policy sha256 recorded, agreement rate recorded | Enforced by the `poc`/`negation` subcommands |

The token-length criterion follows the README formula. The actual room for the state is `room = max_len - head_len - 1`, where `head_len` is the head length the questions actually produce (source: README.md "Honest limits" token-budget item). At the multilingual default `max_len=1024`, the head of a 7-option question with Korean descriptions is roughly 45\~80 tokens, so the room is about 940 or more. YNAT headlines, NSMC reviews (at most about 140 characters) and K-MHaS comments all fit within it, and the NLI and PoC sets do not exceed a few hundred tokens either. `stats` uses laya's `build_head`/`encode_text` to compute the distribution of state token counts (p50/p95/p99/max), the question head length and the room (`scripts/build_ko_evalsets.py:517`). Sets that will also run on the English checkpoint (`max_len=512`, `head_max_len=192`) (en_massive) are rechecked against that budget.

Measured `stats` of the 2026-10-02 build: on multilingual, the state-token p99 of every set is 140 or less (max 227, K-MHaS) and the room is at least 769, so no row is truncated. The head of scenario_18 is 252/256, with the options taking 236 tokens, leaving only 4 tokens of slack; even slightly longer descriptions hit the cap, so the wording ablation has to take this into account. The head of domain_8 is 199 (`_ko-instr` 205, `_en-desc` 153). full60 hits the cap of 4 tokens per option, so only 47 of the 59 options are distinguishable (as the Track C6 hypothesis predicts). On the english checkpoint, the Korean descriptions of `en_massive_domain_8` are truncated to 22 tokens per option (the 8 options remain distinguishable), and `en_massive_intent_20opt` hits the cap of 8 tokens per option on some rows, so on the worst row only 17 of 20 are distinguishable (a property of the upstream instrument itself).

```bash
.venv/bin/laya-evals validate data/evals/ko_nsmc_sentiment.jsonl
.venv/bin/python scripts/build_ko_evalsets.py stats data/evals/*.jsonl
```

**Freeze procedure**

1. Once all the checks above pass, run `manifest` to record sha256 and questions_sha256.
2. Write the file names and sha256 used into the run card of 06_templates.md. The `laya-evals run --json` report also records `config.dataset_sha256` and `config.questions_sha256` itself, so check that both values match the MANIFEST (source: docs/evals.md "Run identity").
3. Frozen files are not modified. To change wording, labels or rows, make a `_v2` file and add a new entry to the MANIFEST. The builder's `--force` protection enforces this.
4. Label-policy documents are versioned up by the same rule.

---

## 8. License and source table

| Source | Access path | License (as recorded) | What to check |
|---|---|---|---|
| Amazon MASSIVE | `mteb/amazon_massive_intent` (HF, config `ko`/`en`) | CC BY 4.0 (per `NOTICE.md` of the original repository alexa/massive; the apache-2.0 in the `license` field of the HF mirror cards `mteb/amazon_massive_intent` and `_scenario` (checked 2026-10-02) is the mirror's own label) | Checked (2026-10-12): the CC BY 4.0 of the original data applies |
| KLUE (YNAT, NLI) | `klue/klue` (HF) | CC BY-SA 4.0 (KLUE GitHub README, HF card YAML) | Checked (2026-10-12). SA clause: the derived sets are distributed under CC BY-SA 4.0 (also if contributed upstream) |
| NSMC | GitHub raw `e9t/nsmc` | CC0 1.0 (repository README) | Checked (2026-10-12) |
| K-MHaS | `jeanlee/kmhas_korean_hate_speech` (HF) | CC BY-SA 4.0 (stated only on the HF card) | Checked (2026-10-12): the paper (COLING 2022) and the GitHub repository state no license. The SA clause applies |
| 3i4K | GitHub raw `warnikchow/3i4k` | CC BY-SA 4.0 (repository LICENSE file; README "We updated our LICENSE to CC-BY-SA-4.0") | Checked (2026-10-12). The SA clause applies |
| kor_nli (alternative) | `kakaobrain/kor_nli` (HF) | CC BY-SA 4.0 **to be verified** | Not used (not checked) |
| kor_unsmile (alternative) | `smilegate-ai/kor_unsmile` (HF) | **to be verified** | Not used (not checked) |
| Handwritten sets | `data/handwritten/` | Owned by the project | Passes the no-PII checklist |

The "to be verified" label means that as of 2026-10-02 only the HF API metadata was checked and the license field of the dataset cards was not read directly. The licenses of the sources used (MASSIVE, KLUE, NSMC, K-MHaS, 3i4K) were checked at their primary sources on 2026-10-12, and kor_nli and kor_unsmile were not used. The builder records `source.revision` (the HF dataset commit sha) in the MANIFEST so that later license changes can be tracked. The sets derived from sources with an SA clause (KLUE, K-MHaS, 3i4K) are published under CC BY-SA 4.0 (also if contributed upstream). Per-source details are in `DATA_LICENSES.md`.

---

## Open questions / assumptions

1. **Default language of instructions.** Assumed English by default with Korean as the ablation (comparable with the upstream construction). If Korean instructions are consistently better in the Track B results, the default changes in v2.
2. **noul criteria policy.** Split as no criteria for the handwritten sets and criteria for the sets bound to a dataset definition (NSMC, K-MHaS). The Chinese measurements (criteria pushed noul to always-true) and the English measurements (a noul without criteria is always-no on the english checkpoint) point in opposite directions, so which way Korean goes is answered by the wording ladder of 03.
3. **3i4K fragment.** Decided: keep 7-way + the `fragment` tag. If 6-way is judged a more appropriate basis for comparison, the `--drop-fragments` derived file is promoted to canonical.
4. **PoC set size and labelers.** The target was 300 rows labeled by 2 people, but the available staff is undecided. The fallback is to start with labels by 1 person + an adjudication pass and to estimate the agreement rate later from a 2-person sample (50 rows).
5. **MASSIVE reproduction tolerance.** Upstream measured with its own scorer and we use `laya-evals`, so differences in the second decimal place are possible. The tolerance is the responsibility of Track A in 03_benchmark_plan.md.
6. (Resolved, 2026-10-07) **Training-mix membership.** It is not in the model card, but the upstream benchmark notebook states "Neither checkpoint trained on typed-decisions, MASSIVE or XNLI" (research/scripts/build_benchmark_nb.py:762). The `in_training_mix` of the MASSIVE-derived sets was changed from "unknown" to held out (for the base checkpoints; ft-v1 was trained on MASSIVE ko train). The remaining public sources without evidence stay "unknown".
7. **Upstream contribution.** Whether to send the Korean sets as a PR to `research/evals/`, like zh_decision_bench.jsonl, is decided after checking the licenses (SA clause). The licenses were checked on 2026-10-12 (`DATA_LICENSES.md`): even in a PR, the sets derived from KLUE·K-MHaS·3i4K stay under CC BY-SA 4.0. A PR would exclude the PoC set and contain only the sets derived from public sources.
8. (Confirmed) **Handling of keys that exist only in `expected`.** `laya-evals validate` rejects `expected` keys missing from `questions` with `EvalError("'expected' names unknown question(s)")` (laya/evals.py:92-94). The 6-row example in §5.8 is illustrative, and the builder's `poc` subcommand checks the 7 keys first.

**English** | [한국어](04_korean_evalset_spec.ko.md)
