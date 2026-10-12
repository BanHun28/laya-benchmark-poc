# Laya 한국어 지원 감사: 문서 · 토크나이저 · 라우팅

| 항목 | 값 |
|---|---|
| 날짜 / wall time | 2026-10-02 (KST), 15:05–15:34 (약 29분. 그중 실행 시간: 토크나이저 스크립트 약 1분, 나머지 스크립트 각 수 초) |
| 범위 | 문서 증거, 토크나이저 효율, 라우팅 결정. **모델 forward 없음** (tokenizer와 `laya.lang.analyse` / `Router().route`만 사용) |
| 대상 | upstream `third_party/laya` @4aa6761(공개 저장소에는 포함하지 않음. https://github.com/NandhaKishorM/laya 를 커밋 4aa6761로 clone해 재현), 설치본 laya 0.3.23 (`lang.py`는 upstream과 byte 동일. `router.py`는 `resolve_model_spec` 헬퍼와 그 `Tuple` import만 다르고 라우팅 분기는 동일하며, 설치본 줄 번호가 −16 밀려 있음. `common.py`는 byte 동일) |
| 체크포인트 | `models/laya*`(공개 저장소에는 포함하지 않음) → `convaiinnovations/laya@55cf4c4` 번들. `multilingual/` 하위 폴더의 `model.safetensors`(sha256 `9d628fd9…`)와 `tokenizer.json`(`609d8f4c…`)은 단독 repo `convaiinnovations/laya-multilingual@e4e9ddf`와 동일 (`cards/*/api_model_blobs*.json`). 따라서 단독 카드가 이 가중치를 설명함 |
| 환경 | Python 3.12.12, transformers 5.18.0, tokenizers 0.23.2, datasets 5.0.1 |
| 산출물 | 이 문서 + 스크립트 5개 + JSON/로그 (§5) |

## 0. 결론 요약

| 층위 | 판정 | 근거 강도 |
|---|---|---|
| **문서상 명시** | `laya-multilingual` 카드의 `language:` 태그에 `ko`가 있지만, 이 50개 코드 목록은 MASSIVE 평가 언어 목록과 정확히 같다. "지원/학습 언어" 문장은 "100+ languages"뿐이다. 한국어 근거는 **zero-shot MASSIVE 수치**(0.45–0.49, n=100/300)와 **presentation check**(ko 10문장, 비원어민 작성)가 전부다. **한국어 의사결정 학습 데이터는 어디에도 문서화되어 있지 않다.** upstream은 "Neither checkpoint trained on … MASSIVE or XNLI"라고 명시한다 | 평가: 중간 (n 작음, 출처 혼재) / 학습: 근거 없음 |
| **토크나이저** | multilingual(mmBERT = Gemma 2, 256k)은 한국어를 **사실상 음절 단위**로 자른다. 음절당 0.98 token, UNK 0, byte-fallback 0.1%. 같은 의미의 영어 대비 토큰 수 1.5배(중앙값). english(ModernBERT 50k)는 음절당 2.3 token이고 토큰의 91%가 글자 미만의 byte 조각이라 한국어를 읽을 수 없다. 단, NFD 입력은 multilingual에서 토큰이 3.1배로 늘어난다 | 강함 (직접 측정, P0 `state_tokens` 34 / `input_tokens` 661 재현) |
| **라우팅** | 순수 한국어, 1음절, 자모(ㅋㅋ/ㅠㅠ/ㅇㅋ), 한자 혼용, 이모지, NFD는 모두 multilingual로 간다. 반면 **라틴 문자가 다수인 혼합문**(API/제품명/URL/에러 붙여넣기)과 **영어 래퍼 안의 짧은 한국어**(10음절 미만)는 english로 간다. 46개 입력 중 10개 실패: 4개는 default와 무관하게 실패, 6개는 stock `default="english"`에서만 실패 | 강함 (결정적 규칙, 코드 줄 인용) |

---

## PART 1. 문서 증거

### 1.1 Hugging Face 모델 카드 (`cards/`)

수집: `bash results/korean_support/fetch_cards.sh` (`hf download <repo> README.md` + `https://huggingface.co/api/models/<repo>?full=true`).

| repo (sha, lastModified) | `language:` 필드 | `ko` 포함 | 본문의 한국어 언급 |
|---|---|---|---|
| `convaiinnovations/laya-multilingual` (e4e9ddf, 2026-09-24) | 51개 (`multilingual` + 50개 코드) | **예** (태그 67개 중) | L116–118 한 문장 |
| `convaiinnovations/laya` (55cf4c4, 2026-09-24; = 로컬 `models/laya/README.md` byte 동일) | **필드 없음** (태그 17개, 언어 태그 0개) | 아니오 | 없음 |
| `convaiinnovations/laya-typed-decisions` (1a793eb) | `[en]` | 아니오 | 없음 |
| `jhu-clsp/mmBERT-base` (c595503) | 1,811개 ISO 639-3 | **예** (`kor`, README L775) | 없음 (front matter만) |

- `laya-multilingual` 카드의 50개 언어 코드는 BENCHMARKS.md의 MASSIVE 51개 locale(zh-CN/zh-TW를 zh로 합치면 50개)과 **양방향 차집합이 모두 공집합**이다(`part1_docs_evidence.json` `benchmarks_51.card_language_codes_vs_massive`). 즉 이 태그는 "평가한 언어" 목록이다. "학습/지원 보증" 목록이 아니다.
- 카드의 언어 관련 문장(`cards/convaiinnovations_laya-multilingual/README.md`):
  - L5: `language: [multilingual, en, de, … ja, ko, zh, …]`
  - L15: "Non-autoregressive **System 1 decision model** covering 100+ languages."
  - L20–21: "**use this checkpoint for anything that is not English.**"
  - L116–118: "Per-language, this checkpoint turns near-random into usable: Arabic 0.110 → **0.400**, … Hindi 0.100 → **0.387**, Korean 0.110 → **0.490**, Turkish 0.140 → **0.437**."
  - L146: "Trained from scratch with RLCD: 15,987 updates, 4 epochs, \~4.97 h." (데이터, 언어 언급 없음)
  - L150–153: "**Ships uncalibrated.** `temperature = [1.0, 1.0, 1.0]` …"
  - L161: "Low-resource languages are weak, not fixed: Swahili 0.210, Tamil 0.250, Amharic 0.110."
- 번들 카드(`cards/convaiinnovations_laya/README.md`):
  - L10: "… across 100+ languages."
  - L58: "The same call works in any of 100+ languages. The `Router` detects the script and language and sends non-English text to `laya-multilingual`"
  - L289–291: Training 절은 RLCD 방법만 설명하고 데이터나 언어는 언급하지 않는다.
  - L373: "**English only on root:** Use `laya-multilingual` for anything outside English."
- **카드의 한국어 수치는 출처가 섞여 있다.** "Korean 0.110 → 0.490"에서 0.110은 CPU 51개 언어 sweep의 english 값(n=100, `research/results/cpu_51_language_sweep.json`)이고, 0.490은 T4 Colab run의 multilingual 값(n=300, `research/results/t4_colab_benchmark.json` `suites["massive_intent.ko"]`)이다. 같은 run의 쌍이 아니다. Turkish(0.140 CPU / 0.437 T4)와 Hindi(0.387 T4)도 같은 패턴이다. 현재 공식 수치는 BENCHMARKS.md:71의 refreshed **0.470**(n=100)이다. 한국어 multilingual 정확도는 run에 따라 0.45(committed, 재현 안 됨) / 0.47(refreshed) / 0.49(T4)로 세 가지가 존재한다.
- 카드 어디에도 한국어 평가셋, 한국어 학습 데이터, 한국어 전용 한계 서술은 없다.

### 1.2 인코더: mmBERT-base

**로컬 config** (`models/laya-multilingual/encoder/config.json`, `rl_agent_config.json`):

| 항목 | laya-multilingual | laya (english) |
|---|---|---|
| `model_type` | `modernbert` (config L55) | `modernbert` |
| `_name_or_path` | **없음** (필드 부재). 출처는 `rl_agent_config.json` L2 `"encoder": "jhu-clsp/mmBERT-base"` | `answerdotai/ModernBERT-large` |
| `vocab_size` | 256,000 (L78) | 50,368 |
| `max_position_embeddings` | 8,192 (L52) | 8,192 |
| hidden / layers | 768 / 22 | 1,024 / 28 |
| `max_len` / `head_max_len` | 1,024 / 256 (rl L4–5) | 512 / 192 |
| temperature | `[1.0, 1.0, 1.0]` (미보정) | 적합값 |
| training | updates 15,987, epochs 4, 4.97 h, `fine_tuned_from_checkpoint: false` (rl L19–25) | 7,313 / 1 / 1.96 h |

**mmBERT 카드** (`cards/jhu-clsp_mmBERT-base/README.md`):
- L775: ` - kor` (언어 목록)
- L1833: "> TL;DR: A state-of-the-art multilingual encoder trained on 3T+ tokens across 1800+ languages …"
- L1884: "**Progressive Language Addition**: Start with 60 high-resource languages, expand to 110 mid-resource languages, then include all 1833 languages in decay phase."
- L1905: "| Pre-training P1 | … | 2.3T | 60 languages, foundational training |"
- L1911: "… FineWeb2-HQ (20 high-resource languages) …"
- L1925: "| Tokenizer | Gemma 2 | Gemma 2 |"
- 카드에 벤치마크 수치는 없고 한국어 언급도 없다.

**mmBERT 논문** arXiv:2509.06888 v1 (2025-09-08; `cards/mmbert_paper/`, 텍스트 변환본 `.txt`):
- 초록: "We introduce mmBERT, an encoder-only language model pretrained on 3T tokens of multilingual text in over 1800 languages."
- txt L220: "We use an identical architecture to ModernBERT, but employ the Gemma 2 tokenizer"
- txt L232: "We start with a set of 60 languages (as well as code) … We then increase this to 110 languages, covering more "mid-resource" languages … Finally, we include all languages/scripts included in FineWeb2 (1833 languages …)."
- txt L238: "We use just 60 languages (plus code languages) in this stage of training"
- **Table 9 `kor` 행** (txt L1340): Pretrain **28.4B (1.43%)** / Mid 11.1B (1.84%) / Decay-Eng 1.5B (1.39%) / Decay-Cont 1.5B (1.47%) / Decay-All 1.5B (1.31%) / Total **43.9B**.
  - pre-training 단계는 60개 언어만 쓰므로, 여기에 28.4B 토큰이 있다는 것은 **한국어가 1단계 60개 "high-resource" 언어에 속한다**는 뜻이다.
  - Table 9의 89개 언어 중 pre-training 토큰 기준 **13위**다(eng, rus, cmn, spa, deu, fra, jpn, ita, por, nld, pol, ind 다음).
- **FineWeb2-HQ(20개 언어)에는 한국어가 없다.** `cards/epfml__FineWeb2-HQ/api_dataset.json`의 `language` 목록은 ru, zh, de, ja, es, fr, it, pt, pl, nl, id, tr, cs, vi, sv, fa, ar, el, da, hu다. 따라서 mid/decay 단계에서 한국어는 품질 필터를 거친 HQ가 아니라 일반 FineWeb2 데이터로 들어간다(일본어와 중국어는 HQ로 들어감).
- 논문 본문에 "Korean"은 한 번도 나오지 않는다. 언어별 결과표(Table 7)의 열은 ar, de, en, es, fr, hi, ja, ru, tr, vi, zh이고 ko는 없다. **한국어 전용 벤치마크 수치는 없다.**

**토크나이저 출처 검증** (`part1b_tokenizer_origin.py` → `part1b_tokenizer_origin.json`):
- laya-multilingual `tokenizer.json`과 `jhu-clsp/mmBERT-base@c595503`은 vocab(256,000)과 merges(580,604)가 동일하다.
- normalizer와 added tokens도 동일하고, 둘 다 `byte_fallback: true`다.
- pre_tokenizer는 직렬화 형식만 다르다(`add_prefix_space: true` vs `prepend_scheme: "always", split: true`).
- MASSIVE ko 300문장에서 토큰 id가 **300/300 일치**한다.

### 1.3 upstream 저장소의 한국어 근거

`grep -rniE "korean|hangul|한국|[가-힣]"` 결과는 11개 파일이다(`part1_docs_evidence.json` `upstream_grep`).

| 파일:줄 | 내용 |
|---|---|
| `BENCHMARKS.md:71` | `ko` 행: laya 0.110 / laya-multilingual 0.470 / Δ +0.360 / laya ECE 0.680 / multilingual ECE 0.311 (51개 언어 표, 언어당 100건) |
| `laya/lang.py:4-6` | "English checkpoint collapsing to near-random on non-Latin scripts (Hindi 0.100, Korean 0.103, …)" (T4, n=300) |
| `laya/lang.py:43` | `("hangul", ((0x1100, 0x11FF), (0x3130, 0x318F), (0xAC00, 0xD7AF))),` |
| `laya/router.py:21-22` | "on 20-option MASSIVE intent it scores 0.100 on Hindi and 0.103 on Korean" |
| `research/eval/README.md:290-298, 308-313` | presentation check `--lang ja,ko,hi,tr`. **ko: `score_slot0_identical` −0.570 FAIL (4개 언어 중 최악), `score_first_slot_permuted` 0.050 FAIL** |
| `research/eval/README.md:336-348` | choice control: ko K=4 +0.096 PASS. "Korean is closest to the gate, and below 0 at 3 options." |
| `research/eval/README.md:383-385` | "The Korean, Hindi and Turkish states and levels were written by a non-native speaker" |
| `research/eval/presentation_checks.py:133-146` | 한국어 고정 상태 10문장과 긴급도 레벨 |
| `tests/test_router.py:47, 355, 360, 366-368, 1114, 1143` | Hangul 감지, 브랜드 혼합, 영어 턴 뒤 한국어(16음절), Jamo Ext-A 회귀 테스트 |
| `tests/test_local_e2e.py:59`, `examples/21_routing_without_running.py:34` | 한국어 1문장 라우팅 예시 |
| `laya-ts/src/lang.ts:26`, `laya-ts/tests/tokenizer-parity.test.ts:70` | TS 포트의 hangul 범위. "a Hangul syllable … outside the 256k vocab reached the model as <unk> here" (TS 토크나이저 byte_fallback 버그 회고) |

**51개 언어 표에서 한국어 위치** (`part1_docs_evidence.py`가 BENCHMARKS.md 표를 파싱해 계산):

| 지표 | 한국어 | 51개 언어 중위수 | macro | 순위 |
|---|---|---|---|---|
| multilingual 정확도 | **0.470** | 0.400 | 0.4008 (BENCHMARKS.md:59) | **18/51** (nl과 동률, 상위 17개) |
| multilingual ECE (낮을수록 좋음) | **0.311** | 0.397 | 0.3911 (:60) | **10/51** |
| Δ (multilingual − english) | +0.360 | | | 4/51 (hi와 동률) |

- ko/en 비율: 0.470 / 0.710(multilingual on en) = **0.662**. english 체크포인트의 en 성능 0.820 대비로는 0.573이다.
- 랜덤(0.05) 대비 9.4배다. n=100 Wilson 95% CI는 [0.375, 0.567]로 넓다.
- CJK 이웃 언어: ja 0.640, zh-CN 0.650, zh-TW 0.610. 한국어가 0.14–0.18 낮지만, n=100끼리의 비교라 순위는 지시적이다.
- 그 밖의 한국어 수치(T4 JSON, n=300):
  - intent: english 0.103 (mean confidence 0.953), multilingual 0.490 (ECE 0.308)
  - scenario: 0.127 / 0.423
  - multilingual temperature refit(T=2.07, n_heldout 150) 후 ECE 0.320 → 0.101 (`calibration_repair`)

**lang.py가 다루는 locale** (`lang.py:57-168`, `20-46`):
- 불용어 목록: az, bn(로마자 벵골어), de, en, es, fr, it, nl, pt, ro, sv. **로마자 한국어 목록은 없다.**
- script 범위: 25개(greek … hangul, kana, han)와 나머지 `other`.
- 비라틴 script는 `language`를 항상 `None`으로 돌려준다(`lang.py:581-584`). 즉 한국어는 "hangul" script로만 식별되고 `language="ko"`는 나오지 않는다. 한자만 쓴 한국어는 중국어와 똑같이 `han`이 된다.

**언어별 데이터셋** (research):
- 중국어: `research/evals/zh_decision_bench.jsonl`(224행, BENCHMARKS.md:435-450), `research/benchmarks/feishu_zh`, `research/benchmarks/zh_short_commands`, 그리고 BENCHMARKS.md:422 "## Community evaluation: zh-CN / zh-TW".
- 스페인어: `research/benchmarks/es_phone_turns`.
- **한국어 데이터셋, 벤치마크, 커뮤니티 평가는 없다.**

### 1.4 RLCD 학습 데이터 (언어 구성)

- 학습 방법만 문서화되어 있다. 번들 카드 L289–291(RLCD, proper scoring rule, GRPO 식 REINFORCE)과 multilingual 카드 L146(updates/epochs/시간)이 전부다.
- **학습 데이터의 언어 구성은 어디에도 없다.**
- 문서에서 "in training"으로 표시된 출처는 모두 영어 데이터셋이다:
  - AG News, BoolQ (README.md:1352-1353 "in training mix")
  - enron spam, phishing emails, MS MARCO relevance, customer-support-tickets queue (BENCHMARKS.md:138-148, `research/scripts/bench_apps.py:94,155,168,185,239`. 벤치마크는 `language == "en"`행만 사용, :146)
  - 영어 체크포인트의 13개 task family (`models/laya/eval/results.md`)
- 명시적 배제(`research/results/t4_colab_benchmark.json:4309`, `research/scripts/build_benchmark_nb.py:760-762`): "ag_news and boolq were in Laya's training mix … **Neither checkpoint trained on typed-decisions, MASSIVE or XNLI.**"
- **판정: 한국어 의사결정(RLCD) 학습 데이터는 문서화되어 있지 않다.** 공개된 한국어 수치(MASSIVE)는 학습에서 명시적으로 빠진 데이터로 잰 것이다. 따라서 한국어 성능은 mmBERT 사전학습과 (문서상 영어 중심인) RLCD 학습에서 온 **cross-lingual zero-shot 전이**로 해석해야 한다.

**PART 1 판정.**
- 한국어는 "평가된 언어"로만 문서화되어 있다(카드 태그 1개, 본문 1문장, BENCHMARKS 1행, presentation check 1세트).
- "학습/보증 언어"로는 문서화되어 있지 않다.
- 인코더 수준의 근거는 강하다. mmBERT에서 한국어는 1단계 60개 high-resource 언어에 속하고, 데이터량 13위(28.4B pre-training 토큰)다. 다만 FineWeb2-HQ에는 없다.
- laya 수준의 한국어 근거는 zero-shot MASSIVE intent(0.45–0.49, n=100/300, 출처 혼재)와 비원어민이 쓴 10문장 presentation check(score 위치 편향 FAIL, 4개 언어 중 최악)가 전부다.
- 중국어처럼 별도 평가셋이나 커뮤니티 평가가 없다.
- 근거 강도: 인코더 사전학습 **강함** / laya 평가 **약함\~중간** / laya 학습 **없음**.

---

## PART 2. 토크나이저 효율 (forward 없음)

### 2.1 설정과 정의 (가정 명시)

**데이터**
- MASSIVE: `mteb/amazon_massive_intent` rev `940fd47a…` test split의 `ko` 첫 300행(파일 순서)을 `id`로 `en`과 조인했다. 300쌍 모두 `id`와 `label_text`가 일치한다(assert).
- P0 probe: `results/poc/P0_probe_sentences.jsonl`의 `state.message` 30문장.
- KLUE YNAT: `P0c_build.build_ynat()`를 import해 재사용했고, 결과 100개 헤드라인이 `P0c_ynat100.jsonl`과 같음을 assert로 확인했다.

**측정 방식**
- 토크나이저는 `laya.agent`와 같은 경로로 `AutoTokenizer.from_pretrained(<ckpt>/tokenizer)`를 쓰고 `add_special_tokens=False`로 인코딩했다.
- chars = `len(text)`(공백 포함). `tok/char*`는 공백을 뺀 값이다.
- words = 공백 분리 개수. MASSIVE ko에는 "시 에"처럼 조사가 띄어진 표기 artifact가 있어 tokens/word는 보조 지표로만 본다.

**토큰 범주** (`convert_ids_to_tokens`; english는 ByteLevel 문자를 원래 byte로 되돌려 해석)

| 범주 | 정의 |
|---|---|
| `hangul_full` | 완전한 음절(U+AC00–D7A3)을 하나 이상 포함 |
| `byte_fallback` | `<0xNN>` |
| `byte_piece` | 단독으로 UTF-8이 안 되는 byte 조각 |
| `jamo` | 자모만 포함 |
| `space` | `▁` 단독 |
| `han` | 한자 |
| `other` | 그 밖의 토큰 |

- **frag %** = (`byte_fallback` + `byte_piece` + `jamo`) / 전체 토큰. 음절 미만 조각의 비율이다.
- 지시문을 문자 그대로 읽은 정의("완전한 음절이 아닌 모든 토큰")는 `not_full_syllable_share`로 따로 기록했다(`part2_tokenizer_stats.json`).

**재현 검증.** laya의 `serialize_state`, `build_sequence`, `state_room`을 multilingual 토크나이저로 돌리면 P0 메시지의 `state_tokens`가 **34**, 7문항 `input_tokens`가 **661**로 P0 실측(`results/poc/P0_20261002.md:75`)과 정확히 같다. 짧은 메시지는 19로, CLI 실측과 같다.

### 2.2 결과 표 (`part2_tokenizer_stats.json` `aggregate`)

| tokenizer / set | n | tok/char | tok/char* | tok/word | tok/음절 | frag % | UNK |
|---|---|---|---|---|---|---|---|
| **multilingual / MASSIVE ko** | 300 | **0.726** | 0.972 | **2.208** | **0.983** | **0.10%** (`<0x..>` 3개 = 음절 1개 '딨') | **0** |
| multilingual / MASSIVE en | 300 | 0.215 | 0.258 | 1.073 | – | 0 | 0 |
| multilingual / P0 probe ko | 30 | 0.682 | 0.879 | 2.827 | 0.945 | 0.17% (입력에 있는 'ㅠㅠ' 자모 2개, byte-fallback 0) | 0 |
| multilingual / KLUE YNAT | 100 | 0.794 | 0.998 | 3.304 | 1.105 (한자, 문장부호 포함) | 0.00% | 0 |
| english / MASSIVE ko | 300 | 1.698 | 2.273 | 5.163 | **2.299** | **90.61%** | 0 |
| english / MASSIVE en | 300 | 0.221 | 0.266 | 1.107 | – | 0 | 0 |
| english / P0 probe ko | 30 | 1.528 | 1.969 | 6.332 | 2.117 | 82.07% | 0 |
| english / KLUE YNAT | 100 | 1.775 | 2.229 | 7.382 | 2.469 | 91.17% | 0 |

**MASSIVE 쌍별 토큰 비율 (ko / en)**

| 조합 | 중앙값 | p90 | p10 | 합계 비 |
|---|---|---|---|---|
| multilingual로 ko와 en 모두 | **1.50** | **2.20** | 1.00 | 1.46 |
| english로 ko와 en 모두 | 3.43 | 5.00 | 2.14 | 3.31 |
| 라우팅된 실제 조합 (ko→multilingual, en→english) | 1.50 | 2.00 | 0.99 | 1.42 |

**multilingual 토큰 범주 내역 (MASSIVE ko, 2,872 토큰)**
- `hangul_full` 2,678 / `space` 170 (5.9%) / `other` 21 / `byte_fallback` 3.
- 문자 그대로의 "완전 음절이 아닌 토큰" 비율은 6.8%다. 대부분 `▁`+음절 조합이 vocab에 없어 생기는 단독 `▁` 토큰이고, 이는 단편화가 아니라 공백 비용이다.

### 2.3 Vocab 관점: 왜 음절 단위인가 (`tokenizers.*.vocab`, `syllable_coverage`)

| | multilingual (Gemma 2, 256k) | english (ModernBERT, 50k) |
|---|---|---|
| 단일 토큰인 음절 (전체 11,172개 중) | 1,597 | 22 |
| 단일 토큰인 KS X 1001 음절 (2,350개 중) | **1,551 (66.0%)** | 22 (0.9%) |
| 순수 한글 다음절 vocab 항목 | **369** | 1 |
| 완전 음절을 포함한 vocab 항목 | 2,295 (vocab의 0.9%) | 25 |
| 미등재 음절 처리 | byte fallback, 음절당 `<0xNN>` 3개 | byte-level BPE |

**multilingual**
- 다음절 한국어 토큰이 369개뿐이라 한국어는 거의 음절당 1토큰이다. 완전 음절 토큰 하나가 평균 1.09음절을 담는다.
- KS X 1001 상용 음절의 34%(799개, 예: 갉 갊 궂 깠 …)는 vocab에 없어 3 byte 토큰으로 쪼개진다.
- 그러나 실제 텍스트에서는 드물다. MASSIVE 2,922음절 중 1개(딨), P0 1,262음절과 YNAT 1,958음절 중에는 0개다.
- **UNK는 사실상 불가능하다.** byte 토큰 256개 중 `<0x09>`(tab) 하나만 없고, 한글의 UTF-8 byte(0xEA–0xED, 0x80–0xBF)는 모두 있다.

**english**
- 음절의 99%가 byte 조각이다. **UNK가 0인 이유는 byte-level BPE가 구조적으로 UNK를 내지 않기 때문이다.** 따라서 UNK 0은 읽을 수 있다는 증거가 아니다.
- 실제 신호는 단편화다. 토큰의 91%가 글자 미만 byte 조각이고 음절당 2.3토큰이다. 의미 단위 토큰이 없으니 사전학습된 표상도 없다.
- upstream 측정값과 맞는다: MASSIVE ko에서 english 0.103(n=300, confidence 0.95), 랜덤 0.05.

**NFD 입력 (주의점).** multilingual 토크나이저의 normalizer는 `Replace(" " → "▁")`뿐이고 NFC가 없다(`part1b_tokenizer_origin.json`). laya 패키지에도 `unicodedata.normalize` 호출이 없다(grep 0건).
- 같은 MASSIVE ko를 NFD(조합형 자모)로 넣으면 토큰이 2,872 → 8,866(**×3.09**)으로 늘고, 대부분 `jamo`(6,734)와 `byte_fallback`(822)이 된다.
- english 토크나이저는 NFC normalizer가 있어 변화가 없다(×1.00).
- 라우팅은 NFD도 hangul로 정상 감지한다(PART 3 #5). 그래서 **macOS 파일명이나 일부 클립보드에서 온 NFD 텍스트는 아무 경고 없이 multilingual에 자모 조각으로 들어간다.**

### 2.4 토큰 예산 (`budget_p0_7_questions`)

- 시퀀스는 질문마다 따로 만들어진다(`third_party/laya/laya/common.py:136-193` `build_sequence`, `:250-259` `state_room`. 설치본과 byte 동일). state 예산은 `max_len - len(head) - 1`이다.
- 따라서 7문항이라고 예산이 7등분되지 않는다. **head가 가장 긴 질문이 잘림을 결정**하고, 계산량은 7 rows로 늘어난다.
- P0 7문항(triage_v1 + gateway_v1, 한국어 criteria)에서 multilingual의 질문별 state room:

| intent | is_urgent | frustration | refund_requested | churn_risk | needs_llm | complexity |
|---|---|---|---|---|---|---|
| **896** (binding) | 987 | 956 | 990 | 983 | 979 | 954 |

- 검산: head 합 416 + 7×(34+1) = 661.

| 체크포인트 / 텍스트 | binding room (tokens) | tok/char | **들어가는 문자 수** (JSON 래퍼 5토큰 제외) |
|---|---|---|---|
| multilingual 1024 / 한국어 (MASSIVE) | 896 | 0.726 | **≈1,227자** |
| multilingual 1024 / 한국어 (P0 메시지: 41자 = 29토큰) | 896 | 0.707 | ≈1,259자 |
| multilingual 1024 / 한국어 (YNAT, P0 probe) | 896 | 0.794 / 0.682 | ≈1,121 / 1,306자 |
| multilingual 1024 / 영어 (MASSIVE en) | 896 | 0.215 | ≈4,152자 |
| multilingual `max_len=8192` (카드 L29) / 한국어 | 8,064 | 0.726 | ≈11,100자 |
| english 512 / 영어 (MASSIVE en) | 326 | 0.221 | ≈1,449자 |
| english 512 / 한국어 (오라우팅 시) | 326 | 1.698 | ≈189자 |

- 한국어는 기본 1,024에서 **약 1,100–1,300자**(공백 포함)까지 잘림 없이 들어간다. 문자 수로는 영어의 약 30%다.
- 다만 의미량 기준으로는 쌍별 토큰 비 1.46(합계) 때문에 **같은 내용 기준 영어의 약 68%**다.
- english 체크포인트는 한국어 criteria 자체가 byte로 쪼개진다. 그래서 intent head가 185토큰(multilingual은 127)으로 커지고 room이 326으로 줄어든다.

**PART 2 판정.**
- **multilingual 토크나이저는 한국어를 지원한다.** UNK 0, 음절 미만 단편화 ≤0.2%, 음절당 약 1토큰이다. 다만 압축률은 낮다. 다음절 vocab이 369개뿐이라 영어 대비 1.5배(p90 2.2배) 토큰을 쓰고, 기본 1,024 예산에서 약 1.2k자까지 들어간다. 짧은 CS 메시지(P0: 34토큰)에는 문제가 없다.
- 위험 요소는 두 가지다. **NFD 입력**(×3.1, NFC 정규화 없음)과 **KS X 1001 음절의 34% 미등재**(희귀 음절 byte fallback)다.
- **english 토크나이저는 한국어를 읽을 수 없다.** 토큰의 91%가 byte 조각이고 음절당 2.3토큰이다. UNK 0은 착시다.
- 근거 강도 **강함**: 토크나이저 직접 측정이고, P0의 34 / 661을 재현했다.

---

## PART 3. 라우팅 견고성 (모델 로드 없음)

### 3.1 결정 규칙과 임계값 (`third_party/laya/laya/lang.py`, 설치본과 byte 동일)

```python
# lang.py:364-371
NON_LATIN_FRACTION = 0.2
NON_LATIN_MIN_FRACTION = 0.1
NON_LATIN_MIN_LETTERS = 10
```

```python
# lang.py:573-576  (_analyse_text): 라틴이 최다 script일 때만 적용되는 비라틴 override
if script == "latin" and _non_latin_words(text) and (
        non_latin >= NON_LATIN_FRACTION or (
            non_latin >= NON_LATIN_MIN_FRACTION and n_non_latin >= NON_LATIN_MIN_LETTERS)):
    script = max((s for s in prof if s != "latin"), key=prof.get)
```

**규칙 요약**
- `lang.py:297-320`: letter 수는 `isalpha()`인 문자만 센다. **한글 1음절 = 1 letter**이고 라틴 1글자 = 1 letter다. 숫자, 이모지, 문장부호는 무시한다. 범위 밖 문자는 `other`로 센다.
- `lang.py:323-326`: 최다 script를 고르고, 동률이면 비라틴이 이긴다.
- `lang.py:385-407` `_non_latin_words`: 같은 script가 **2글자 이상 연속(`len(w) >= 2`)** 이고 대문자로 시작하지 않아야 한다. 단음절 한국어 단어는 증거가 되지 못한다.
- `lang.py:577-584`: `unknown`(letter 없음)은 `is_english=True`가 된다. 비라틴 script는 `language=None, is_english=False`가 된다.
- `lang.py:599-641` `_leaf_non_english` (구조화 state 전용): 각 필드 문자열이 7자 이상(`:620`)이고 **비라틴 letter가 10개 이상**(`:631-633`)이어야 한다.
- `lang.py:658-679`: 줄/필드 단위 segment 스캔은 라틴 언어 이름만 붙일 수 있다(`_named_prose_language` → `latin_profile`). **plain string은 leaf 검사 없이 곧바로 반환된다**(`:678`).
- 라우터(`third_party/laya/laya/router.py:833-865`, 설치본 `:817-849`)의 분기:
  - `unknown` → `self.default`
  - 비라틴 → multilingual
  - 라틴이면서 비영어 → multilingual
  - 라틴이고 language undecided → `self.default`
  - 그 외 → english
- stock `Router(default="english")`(`router.py:519`, 설치본 `:503`)이다. `LAYA_DEFAULT_MODEL`은 `laya-serve`만 읽는다(`laya/serve.py:354`).

### 3.2 배터리 (46개 입력; `part3_routing.py` → `part3_routing_battery.{json,md}`)

- `want`는 결정에 필요한 텍스트를 읽을 수 있는 체크포인트에 대한 이 감사의 판단이다.
- `default=multilingual` 열은 `Router(default="multilingual")`로 같은 입력을 라우팅한 결과다.

| # | group | input | script | lang | is_en | hangul/letters | route (default english) | reason | default=multilingual | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | pure_ko | 같은 달 요금이 두 번 빠져나갔어요. 중복 결제된 금액 환불 부탁드립니다. | hangul | - | False | 29/29 (1.00) | **multilingual** | non-Latin script (hangul, 100% of letters) | multilingual | ok |
| 2 | pure_ko | 앱이 자꾸 튕겨요 | hangul | - | False | 7/7 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 3 | pure_ko | 로그인이 안 돼요. 비밀번호를 바꿨는데도 계속 오류가 납니다. | hangul | - | False | 25/25 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 4 | pure_ko | {"message": "다음 달부터 요금제를 해지하고 싶습니다."} | hangul | - | False | 17/17 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 5 | pure_ko | 환불해 주세요 (NFD, 조합형 자모 14개) | hangul | - | False | 14/14 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 6 | ko_en_terms | 결제 API가 500 에러를 냅니다 | hangul | - | False | 9/12 (0.75) | **multilingual** | non-Latin script (hangul, 75%) | multilingual | ok |
| 7 | ko_en_terms | 로그인 시 OAuth redirect_uri mismatch 에러가 발생합니다 | hangul | - | False | 12/36 (0.33) | **multilingual** | non-Latin script (hangul, 33%) | multilingual | ok |
| 8 | ko_en_terms | Stripe webhook이 timeout 나요 | latin | - | True | 3/23 (0.13) | **english** | Latin script, language not identified …; using default (english) | multilingual | FAIL (stock default) |
| 9 | ko_en_terms | Kubernetes pod가 CrashLoopBackOff 상태예요 | latin | - | True | 5/34 (0.15) | **english** | … using default (english) | multilingual | FAIL (stock default) |
| 10 | ko_en_terms | AWS S3 bucket policy 설정 문의드립니다 | hangul | - | False | 8/24 (0.33) | **multilingual** | non-Latin script (hangul, 33%) | multilingual | ok |
| 11 | ko_en_terms | iPhone 15 Pro Max 환불 | latin | - | True | 2/14 (0.14) | **english** | … using default (english) | multilingual | FAIL (stock default) |
| 12 | ko_en_terms | Samsung Galaxy 주문이 아직 안 왔어요 (upstream 테스트) | hangul | - | False | 9/22 (0.41) | **multilingual** | non-Latin script (hangul, 41%) | multilingual | ok |
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
| 29 | emoji_chat | 😡😡😡 (대조) | unknown | - | True | 0/0 | **english** | no letters detected in state; using default (english) | multilingual | default-dependent |
| 30 | very_short | 환불 | hangul | - | False | 2/2 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 31 | very_short | ㅇㅋ | hangul | - | False | 2/2 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 32 | very_short | 네 | hangul | - | False | 1/1 (1.00) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 33 | very_short | 네 OK | latin | - | True | 1/3 (0.33) | **english** | … using default (english) | multilingual | FAIL (stock default) |
| 34 | very_short | OK 감사 (2:2 동률) | hangul | - | False | 2/4 (0.50) | **multilingual** | non-Latin script (hangul, 50%) | multilingual | ok |
| 35 | hanja_mixed | 北 미사일 발사에 美 강력 규탄 | hangul | - | False | 10/12 (0.83) | **multilingual** | non-Latin script (hangul, 100% of letters) | multilingual | ok |
| 36 | hanja_mixed | 與野, 추경 합의 불발 | hangul | - | False | 6/8 (0.75) | **multilingual** | non-Latin script (hangul, 100%) | multilingual | ok |
| 37 | hanja_mixed | 大韓民國 憲法 第1條 | han | - | False | 0/8 | **multilingual** | non-Latin script (han, 100%) | multilingual | ok (script는 han) |
| 38 | structured | dict: 영어 ticket 필드들 + `"message": "환불해 주세요"` (5음절) | latin | en | True | 6/72 (0.08) | **english** | English Latin text | **english** | **FAIL** |
| 39 | structured | dict: 같은 래퍼 + 19음절 메시지 | hangul | - | False | 19/85 (0.22) | **multilingual** | non-Latin script (hangul, 22%) | multilingual | ok |
| 40 | structured | turns: 영어 agent 턴 + user "환불 부탁드려요" (7음절) | latin | en | True | 7/66 (0.11) | **english** | English Latin text | **english** | **FAIL** |
| 41 | structured | plain string: 긴 영어 템플릿(229 letters) + 19음절 한국어 메시지 | latin | en | True | 19/248 (0.08) | **english** | English Latin text | **english** | **FAIL** |
| 42 | structured | 41과 같은 내용을 dict로 | latin | - | False | 19/248 (0.08) | **multilingual** | "Latin script, language not identified but 0% non-English letters; …" (사유 문구가 Hangul을 언급하지 않음) | multilingual | ok |
| 43 | structured | {"고객_메시지": "Please cancel my plan"} (key는 무시) | latin | en | True | 0/18 | **english** | English Latin text | english | ok |
| 44 | control | 二重に請求されました。返金をお願いします。 | kana | - | False | 0/19 | **multilingual** | non-Latin script (kana, 100%) | multilingual | ok |
| 45 | control | 客户被重复扣款要求退款 | han | - | False | 0/11 | **multilingual** | non-Latin script (han, 100%) | multilingual | ok |
| 46 | control | I was charged twice, please refund the duplicate. | latin | en | True | 0/40 | **english** | English Latin text | english | ok |

**집계**

| verdict | 건수 |
|---|---|
| ok | 28 |
| ok (either) | 4 |
| default-dependent | 4 (로마자 3, 이모지만 1) |
| FAIL (stock default에서만) | 6 (#8 9 11 17 18 33) |
| FAIL (default와 무관) | 4 (#13 38 40 41) |

- 한국어 `analyse()`는 `language`를 항상 `None`으로 낸다(`lang.py:581-584`). 한자만 쓴 한국어(#37)는 `han`이 된다.
- 셀의 hangul/letters 값은 `lang._script_counts`로 계산했다.

### 3.3 실패 유형

**F1. 라틴 다수 혼합문 (#8, 9, 11, 13, 17, 18)**
- override는 letter 비율로 판정한다. 비라틴 비율 ≥0.2, 또는 ≥0.1이면서 ≥10 letter여야 한다(`lang.py:364-371, 573-576`).
- 한글은 1음절이 1 letter다. MASSIVE 300쌍에서 같은 의미를 영어로 쓰면 **한국어 1음절당 영어 2.59 letter**가 필요하다(`letters_per_meaning_massive`). 따라서 한국어 요청은 정보량 대비 약 2.6배 과소 계산된다.
- 결과 1 (#8, 9, 11, 17, 18): 기술 용어, 제품명, URL이 붙은 짧은 한국어 요청은 라틴 script로 판정된다. 불용어가 없으면 "undecided"(`router.py:853-860`)를 거쳐 stock default인 **english**로 간다.
- 결과 2 (#13): 영어 불용어가 하나라도 있으면(`of`) `language="en"`이 되어 default와 무관하게 english로 간다.
- upstream도 이 위험을 의도로 명시해 두었다: `lang.py:364-368` "a brand name or order code outvotes the CJK request around it letter for letter, though one CJK character carries far more than a letter." 그러나 임계값은 여전히 letter 단위다.
- 임계 sweep (plain string, `plain_string_sweep`):

| 라틴 letter | 11 | 20 | 44 | 83 | 160 | 320 |
|---|---|---|---|---|---|---|
| multilingual로 가는 최소 한글 음절 | 3 | 5 | 10 | 10 | 18 | 36 |

  영어 문맥이 40 letter를 넘으면 한글이 전체 letter의 **≥10%이면서 ≥10음절**이어야 한다.

**F2. 영어 래퍼 안의 짧은 한국어 필드/턴 (#38, 40)**
- 구조화 state의 필드별 구제 경로(`_leaf_non_english`, `lang.py:631-633`)는 비라틴 letter가 **10개 이상**이어야 한다.
- "환불해 주세요"(5음절)나 "환불 부탁드려요"(7음절)는 완결된 요청인데도 기준에 못 미쳐 english로 간다. upstream 테스트(`tests/test_router.py:366-368`)는 16음절 문장이라 통과한다.
- 같은 래퍼라도 19음절 메시지(#39)는 multilingual로 간다.

**F3. state 형태 의존 (#41 vs #42)**
- 같은 내용이라도 **plain string이면 english, dict면 multilingual**이다.
- plain string은 `analyse`가 leaf 검사 전에 반환한다(`lang.py:678`). 줄 단위 segment 스캔은 라틴 언어만 이름 붙일 수 있다(`lang.py:517-536, 658-675`).
- #42의 사유 문구 "0% non-English letters"는 실제 결정 이유(Hangul 필드)를 드러내지 않는다. 진단 품질 문제다.

**F4. 단음절 한국어 + 라틴 (#33 "네 OK")**
- `_non_latin_words`가 길이 2 이상의 연속만 증거로 인정한다(`lang.py:407`). 1음절 "네"는 override를 못 하고, undecided를 거쳐 default english로 간다.
- 반면 동률인 "OK 감사"(#34)는 비라틴 우선 규칙(`lang.py:323-326`, `_script_counts` docstring `:290-292`)으로 multilingual로 간다.

**F5. 로마자 한국어 (#23–25)**
- `_STOP`(`lang.py:57-168`)에 로마자 벵골어(`bn`)는 있지만 로마자 한국어는 없다. undecided를 거쳐 default로 간다.
- 어느 체크포인트도 로마자 한국어를 읽는다는 근거가 없으므로 판정은 default-dependent로 두었다.

**F6. 이모지만 있는 입력 (#29)**
- `unknown`이 되어 default로 간다(`router.py:834-836`). 테스트로 고정된 의도된 동작이다(`tests/test_router.py:1128-1134`).

**실패하지 않는 영역**
- 순수 한국어(1음절 "네" 포함), 자모 채팅(ㅋㅋ/ㅠㅠ/ㅇㅋ)
- 한국어 + 숫자/전화번호/이메일
- 한글이 최다인 API 용어 혼합(#6, 7, 10, 12)
- 한자 혼용 헤드라인, NFD, 이모지 혼합
- 영어 래퍼 안의 10음절 이상 한국어 필드

**참고.** `env.sh:12`의 주석 "한글은 항상 감지되므로 한국어에는 무관"은 F1(#8, 9, 11, 17, 18)과 F4(#33)에서 성립하지 않는다. 이 경우 `default`가 한국어 입력의 체크포인트를 결정한다. 이 감사에서 env.sh는 수정하지 않았다.

### 3.4 완화 수단 (모두 기존 API)

| 수단 | 해결되는 것 | 해결되지 않는 것 |
|---|---|---|
| `Router().route(state, lang="ko")` 또는 `lang_guess=`(`router.py:811-831`) | 모든 경우 (#8 → multilingual, 로마자 → multilingual 확인) | – |
| `Router(default="multilingual")` (serve에서는 `LAYA_DEFAULT_MODEL=multilingual`) | F1의 undecided(#8, 9, 11, 17, 18), F4, F5, F6 | **F1-en(#13), F2(#38, 40), F3(#41)**: `is_english=True`라 default 경로를 타지 않음 |
| 결정 대상 한국어 메시지를 별도 dict 필드로, 10음절 이상으로 | F3, 일부 F2 | 짧은 한국어 |

**PART 3 판정.**
- **한국어 텍스트가 letter 기준으로 우세하면 라우팅은 신뢰할 만하다.** 순수 한국어, 짧은 한국어, 자모, 한자 혼용, NFD 모두 multilingual로 간다. 근거는 코드 줄 수준으로 확인했다.
- 실패는 모두 같은 원인에서 나온다. **임계값이 letter 수 기준(음절 1 = 글자 1)이고, 구조화 state의 필드 하한이 10 letter**이기 때문이다.
- 그 결과 라틴 용어가 많은 기술지원 문의, URL/에러 붙여넣기, 영어 템플릿에 감싼 짧은 고객 메시지가 english로 간다. english는 한국어 토큰의 91%를 byte 조각으로 보는 체크포인트다.
- 그중 4건은 `default="multilingual"`로도 막을 수 없다.
- 한국어 트래픽이 주력이면 **`lang="ko"`(또는 LID 기반 `lang_guess`)를 명시**하는 것이 유일하게 완전한 해법이다.
- 근거 강도 **강함**: 결정적 규칙을 재현했고 46건과 sweep으로 확인했다.

---

## 4. 재현 명령 (프로젝트 루트, `source env.sh` 후. `.venv/`는 공개 저장소에는 포함하지 않음)

```bash
bash results/korean_support/fetch_cards.sh                         # 카드/API/논문/FineWeb2-HQ → cards/
.venv/bin/python results/korean_support/part1_docs_evidence.py     # → part1_docs_evidence.json (+ cards/mmbert_paper/*.txt)
.venv/bin/python results/korean_support/part2_tokenizer.py         # → part2_tokenizer_stats.json, part2_massive_pairs.jsonl (~1 min)
.venv/bin/python results/korean_support/part1b_tokenizer_origin.py # → part1b_tokenizer_origin.json (part2 결과 필요)
.venv/bin/python results/korean_support/part3_routing.py           # → part3_routing_battery.json / .md
```

로그: `part1_docs_evidence.log`, `part1b_tokenizer_origin.log`, `part2_tokenizer.log`, `part3_routing.log`.

## 5. 산출물

| 경로 | 내용 |
|---|---|
| `results/korean_support/audit_docs_tokenizer_routing.md` | 이 문서 |
| `results/korean_support/fetch_cards.sh` | PART 1 원자료 수집 |
| `results/korean_support/part1_docs_evidence.py` / `.json` / `.log` | 카드 태그, 본문 한국어 줄, config, mmBERT Table 9, FineWeb2-HQ, BENCHMARKS 순위, 수치 출처, upstream grep, lang.py 범위 |
| `results/korean_support/part1b_tokenizer_origin.py` / `.json` / `.log` | laya-multilingual ↔ mmBERT 토크나이저 동일성 |
| `results/korean_support/part2_tokenizer.py` / `part2_tokenizer_stats.json` / `part2_massive_pairs.jsonl` / `.log` | PART 2 전체 지표, 쌍별 토큰 수, 예산 |
| `results/korean_support/part3_routing.py` / `part3_routing_battery.json` / `.md` / `.log` | PART 3 배터리, sweep, 완화 확인 |
| `results/korean_support/cards/` | 원본 카드 4개와 API JSON(`?full=true`, `?blobs=true`), mmBERT 논문(API xml, abs html, full html, txt), FineWeb2-HQ 카드와 API |

[English](audit_docs_tokenizer_routing.md) | **한국어**
