# 04. 한국어 평가셋 구축 스펙

**목적**: Laya 벤치마크(03_benchmark_plan.md)와 PoC(05_poc_plan.md)가 공통으로 사용하는 한국어 `laya-evals` JSONL 세트의 정의, 변환 규칙, 빌드 스크립트 명세, 품질 체크, 동결 절차를 고정한다. 이 문서가 곧 `scripts/build_ko_evalsets.py`의 요구사항이다.

**선행 문서**: 00_README.md(진행 순서), 01_laya_analysis.md(프리미티브·토큰 예산·Honest limits), 02_environment_setup.md(uv venv Python 3.12, laya 0.3.23, `datasets`·`pandas`, `models/` 심링크, `third_party/laya` @ `4aa6761`; `models/`와 `third_party/laya`는 공개 저장소에는 포함하지 않음. upstream은 https://github.com/NandhaKishorM/laya 를 커밋 4aa6761로 클론해 재현).

**산출물**: `data/evals/*.jsonl` 12종 + `data/evals/MANIFEST.json`, `data/handwritten/`(수작업 원본), `scripts/build_ko_evalsets.py`(이 문서 §6의 명세대로 구현, 구현은 별도 작업).

---

## 1. 목적과 원칙

upstream이 공개한 한국어 수치는 MASSIVE intent 20-option 한 줄뿐이다. `laya` 0.110 / `laya-multilingual` 0.470, ECE 0.680 / 0.311 (출처: BENCHMARKS.md:71). 한국어 PoC 도입 결정에 필요한 "티켓 분류·감성·NLI·혐오 탐지·화행 분류" 형태의 수치는 존재하지 않으므로 우리가 만든다. 세트의 역할은 세 가지다.

| 역할 | 세트 | 쓰는 트랙 |
|---|---|---|
| upstream 재현(sanity) | `ko_massive_intent_20opt`, `en_massive_intent_20opt` | Track A |
| 한국어 태스크 전이 측정 | YNAT, NLI, NSMC, K-MHaS, 3i4K, scenario_18 | Track B |
| 알려진 약점 probe | `ko_massive_intent_full60`, `ko_negation_probe` | Track C |
| PoC 도메인 셋 | `ko_massive_domain_8` (+ `en_massive_domain_8` 쌍), 보조 `ko_klue_ynat_7` | Track B / E / PoC |
| 보류(시나리오 A) | `ko_poc_triage_v1` | P4 결정 후 |

원칙은 다음과 같고, 각 원칙은 upstream의 평가 설계에서 따왔다.

1. **레이블 정책 선동결.** 수작업 세트(5.7, 5.8)는 모델을 한 번도 돌리기 전에 레이블 정책 문서를 쓰고 sha256을 기록한다. upstream의 zh_short_commands·es_phone_turns 벤치가 같은 규칙을 쓴다 (출처: research/benchmarks/zh_short_commands/README.md "label policy fixed before any model was run").
2. **held-out.** 공개 세트는 test 또는 validation split만 쓴다. 학습 믹스 포함 여부는 MANIFEST의 `in_training_mix` 필드에 upstream 근거대로 적고 결과 해석 시 함께 읽는다 (출처: BENCHMARKS.md "Themes", *held out* 표기 관행). upstream은 "Neither checkpoint trained on typed-decisions, MASSIVE or XNLI"라고 적으므로 MASSIVE 파생 세트는 base 체크포인트 기준 held out이다 (출처: research/scripts/build_benchmark_nb.py:760-762). ft-v1은 MASSIVE ko train으로 학습했다(`results/P4/`). upstream이 언급하지 않은 소스(KLUE, NSMC, K-MHaS, 3i4K)는 "unknown"으로 둔다.
3. **결정적 빌드.** seed 13 고정(upstream `SEED = 13`), 정렬 후 샘플링, 같은 입력이면 byte-identical 출력. 동일성은 sha256으로 증명한다.
4. **질문 스키마 byte-stable.** `questions_sha256`이 instructions·criteria 문자열 전체를 fingerprint하므로 한 글자만 바뀌어도 다른 실험이 된다 (출처: docs/evals.md "Run identity").
5. **라이선스 기록.** 모든 소스의 라이선스·URL을 MANIFEST와 §8 표에 적고, 미확인은 "확인 필요"로 남긴다.
6. **크기는 CPU 시간으로 결정.** 메인 세트 N=500은 M4 Pro CPU에서 multilingual 체크포인트 기준 수 분 안에 끝나는 크기다(02_environment_setup.md의 측정값으로 보정). `--n 0`으로 전량 빌드도 가능하게 둔다.
7. **PII 없음.** 수작업 문장은 가공·창작하며 실제 고객 데이터·실명·연락처·주문번호를 넣지 않는다.

---

## 2. laya-evals JSONL 포맷

한 줄에 JSON 객체 하나. 빈 줄과 `#`로 시작하는 줄은 무시된다 (출처: docs/evals.md "Dataset format", research/evals/README.md "Format").

| 필드 | 필수 | 타입 | 의미 |
|---|---|---|---|
| `state` | 예 | str / dict / list | 판단 대상. dict면 instructions에서 백틱으로 필드를 지칭한다 |
| `questions` | 예 | dict | `Router.predict`가 받는 질문 dict 그대로 |
| `expected` | 예 | dict | 질문 id → 정답 |
| `tags` | 아니오 | list[str] | `--slice tag` 단위 |
| `language` | 아니오 | str | `--slice language` 단위. 이 문서의 세트는 `"ko"` 또는 `"en"` |
| `model` | 아니오 | str | 행 단위 체크포인트 고정. `--model`이 우선 |

`expected`의 타입 규칙은 평가기 구현이 정한다 (출처: laya/evals.py:255-280, 331-337).

| 프리미티브 | expected 타입 | 채점 규칙 |
|---|---|---|
| `choice` | **criteria의 key** 문자열 | `answer["choice"] == expected` (ChoiceAccuracy) |
| `score` | 숫자, **0-based 레벨 인덱스** | `abs(answer["score"] - expected)` (ScoreMAE), `--score-within` 허용 오차 |
| `noul` | JSON `true` / `false` | `(p >= 0.5) == expected` (NoulAccuracy) |

`score`의 answer는 "기대 서수 레벨"(예: 1.84 / 2.0)이므로 expected도 같은 눈금의 인덱스여야 한다. 레벨 수가 4면 expected ∈ {0,1,2,3}. 3줄 예시(순서대로 choice, score, noul):

```json
{"state": {"message": "결제가 두 번 됐어요. 중복 결제 환불해 주세요."}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불이나 중복 결제 환급을 요구", "technical_help": "버그나 오류에 대한 기술 지원 요청", "other": "그 외"}}}, "expected": {"intent": "refund"}, "tags": ["example"], "language": "ko"}
{"state": {"message": "서비스가 두 시간째 안 되고 있습니다. 지금 매출 손실이 나고 있어요."}, "questions": {"frustration": {"type": "score", "instructions": "How frustrated does the customer sound in `message`?", "criteria": ["차분하고 중립적", "걱정하지만 정중함", "분명히 짜증남", "매우 화남 또는 강한 표현 사용"]}}, "expected": {"frustration": 2}, "tags": ["example"], "language": "ko"}
{"state": {"message": "환불 안 해주면 다른 서비스로 갈아탈 겁니다."}, "questions": {"churn_risk": {"type": "noul", "instructions": "Does `message` suggest the customer may leave for a competitor or cancel?"}}, "expected": {"churn_risk": true}, "tags": ["example"], "language": "ko"}
```

모델 없이 포맷만 검사:

```bash
.venv/bin/laya-evals validate data/evals/ko_klue_ynat_7.jsonl
```

---

## 3. 질문 스키마 설계 규칙

빌더와 수작업 세트 작성자가 공통으로 따르는 체크리스트. 각 항목의 근거는 upstream 문서의 실측이다.

- [ ] **choice key는 ASCII snake_case 의미 레이블 또는 불투명 레이블(A/B).** criteria의 key가 곧 모델이 읽는 옵션 텍스트이고, `true/false/yes/no` 같은 불리언 단어 key는 설명 대신 레이블을 따라가는 실패가 보고됐다 (출처: README.md "Honest limits" "Avoid boolean-word labels"). 한국어 key는 쓰지 않는다. 토크나이저 예산(옵션당 토큰)이 영어 snake_case보다 불리하고, upstream 수치와의 비교축이 흐려진다.
- [ ] **criteria 설명(value)은 한국어 서술형이 기본.** 모델이 읽는 것은 state(한국어)와 설명이다. scenario_18과 PoC 세트를 포함한 모든 세트에서 한국어 서술형 설명이 기본이고, 영어 key 렌더링은 upstream 구성을 그대로 따르는 `*_massive_intent_20opt.jsonl`(Track A 재현)과 `ko_massive_intent_full60.jsonl`(Track C6, 20opt와 같은 렌더링) 두 세트뿐이다. 그 두 세트는 `--descriptions ko`(`_ko-desc`, `data/handwritten/massive_intent_ko_desc.json` 필요, 아직 없음)가, 나머지 세트는 `--descriptions en`(`_en-desc`)이 ablation이다. 근거: P0c(n=100, `results/poc/P0c_20261002.md`)에서 scenario-18은 한국어 설명 0.52 vs upstream key 렌더링 0.35(McNemar p<0.001)였고, 한국어 instructions는 YNAT·scenario 두 세트 모두 Δ0이었다.
- [ ] **instructions는 영어가 기본, `--instructions ko`가 ablation.** upstream의 MASSIVE 구성과 presets가 모두 영어 instructions이다 (출처: research/scripts/bench_local.py:175-177, laya/presets.py). 한국어 instructions가 더 나은지는 Track B의 ablation으로 측정한다.
- [ ] **state 필드를 백틱으로 지칭.** 예: "What is the user asking for in `utterance`?". presets가 이 관례로 state key를 역추적한다 (출처: laya/presets.py `state_field`, `_STATE_FIELD_RE`). 필드 두 개를 지칭하는 질문(NLI)은 허용되며, presets 헬퍼만 `None`을 돌려줄 뿐 추론에는 영향이 없다.
- [ ] **choice 옵션은 20개 이하.** 옵션들이 `head_max_len`(multilingual 256, english 192) 예산을 나눠 쓰고, 옵션당 토큰은 `max(4, (head_max_len - 16) // k)`로 바닥이 4다. Banking77(77 옵션)은 두 체크포인트 모두 정확히 0.425로 붕괴했다 (출처: README.md "Honest limits", BENCHMARKS.md "On the public datasets where Jev numbers exist"). 예외는 5.1의 `full60` probe 하나다.
- [ ] **noul의 `criteria`는 key가 정확히 `true`/`false`.** 다른 key(`yes`/`no`)는 거절된다. 모델이 읽는 옵션 쌍을 바꾸려면 `labels` (예: `{"true": "A", "false": "B"}`)를 쓴다 (출처: README.md "Honest limits" noul 항목, #156).
- [ ] **noul criteria 유무는 세트별로 명시.** criteria 없는 noul은 english 체크포인트에서 state와 무관하게 "no"를 답하지만 multilingual은 state를 읽는다 (출처: README.md "Honest limits"). 반대로 중국어 실측에서는 noul에 criteria·시나리오·JSON state를 더할수록 모든 질문이 "true"로 수렴해 정확도가 떨어졌다 (출처: research/benchmarks/zh_short_commands/README.md "The ladder"). 한국어는 Hangul 스크립트로 multilingual에 라우팅되므로(laya/lang.py:43) 두 결과가 모두 적용 가능하다. 따라서 수작업 세트의 noul은 presets와 같이 **criteria 없음**을 v1 기본으로 하고, criteria 추가는 03의 wording-ladder ablation에서 런타임 생성한다. 단, 2026-10-02 P0 프로브(n=30, `results/poc/P0_20261002.md`)에서 multilingual의 criteria-less noul이 한국어 입력에 거의 항상 "no"를 답했으므로, 수작업 세트를 동결하기 전에 `triage_v1b.json`(+criteria)과 2-choice 중립 키 변형을 먼저 비교해 v1 기본을 다시 정한다. NSMC·K-MHaS처럼 "무엇이 true인가"가 데이터셋 정의에 묶인 세트는 criteria를 넣고, 그 사실을 §5에 적는다. P0b ablation(n=30, `results/poc/P0b_20261002.md`)에서는 어떤 이진 형태도 합계로 always-no 기저(93/120)를 넘지 못했고(V0 criteria 없음 93 = V2 labels A/B 93 = V8 조합 93, V1 criteria 87, V3a A/B 2-choice 68로 A 쪽 붕괴), 질문 단위로만 churn_risk + 한국어 criteria 28/30(양성 6/6 정답), is_urgent + 한국어 instructions 26/30이 기저를 넘었다. 따라서 PoC 세트의 noul 형태는 동결 전에 질문별로 정한다.
- [ ] **score criteria는 레벨 설명 리스트, expected는 인덱스.** `null` 레벨은 422로 거절된다 (출처: README.md "Self-Hosting" "Score levels").
- [ ] **instructions·criteria 문자열은 동결 후 불변.** 공백 하나도 `questions_sha256`을 바꾼다 (출처: docs/evals.md "Run identity"). 문구를 바꾸면 v2 파일을 만든다.
- [ ] **한 state에 여러 질문을 묶어도 forward pass는 한 번.** NSMC의 noul·choice 두 변형을 한 행에 넣는 근거다. 단 질문을 추가하면 head 토큰이 늘어 state 여유 토큰이 줄어드니 `--stats`로 확인한다.

---

## 4. 세트 목록 요약

| 파일 (`data/evals/`) | 소스 | 태스크 / 프리미티브 | 옵션 수 | N | 트랙 | 가설 |
|---|---|---|---|---|---|---|
| `ko_massive_intent_20opt.jsonl` | mteb/amazon_massive_intent `ko` test | 의도 분류 / choice | 20 | 100 | A | multilingual 0.470 ± 재현 노이즈 |
| `en_massive_intent_20opt.jsonl` | 같은 소스 `en` test | 의도 분류 / choice | 20 | 100 | A | english 0.820, multilingual 0.710 재현 |
| `ko_massive_intent_full60.jsonl` | 같은 100행 | 고카디널리티 / choice | 59 (명목 60) | 100 | C | 기본 예산에서 붕괴, head 512로 회복 |
| `ko_massive_scenario_18.jsonl` | 같은 100행, 접두어 파생 | 도메인 분류 / choice | 18 | 100 | B | 20opt보다 높음(옵션 수 비슷, 의미 거리 큼) |
| `ko_massive_domain_8.jsonl` | mteb/amazon_massive_intent `ko` test 전체(2,974행)에서 층화 추출 | **PoC 주 과제** 도메인 라우팅 / choice | 8 | 500 (`--n 0` = 2,917행. 완전 중복 55행과 2자 미만 2행 제거 후) | B + PoC | scenario_18(P0c 0.52)보다 높음, PoC G1 입력. 질문 dict는 `poc/schema/router_v1.json`(05 §4.1)과 byte 일치 |
| `en_massive_domain_8.jsonl` | 같은 id의 `en` 쌍 | 한국어 페널티 측정 / choice | 8 | ko 파일과 동일 | B (07 §5 방법) | ko 대비 영어 우위 0.10 수준(한국어 설명, 07 §5 E1) |
| `ko_klue_ynat_7.jsonl` | klue/klue `ynat` validation | 뉴스 토픽 / choice | 7 | 500 | B | zero-shot 0.5\~0.7 (KLUE fine-tuned 기준치 macro-F1 0.85+와 비교) |
| `ko_klue_nli_3.jsonl` | klue/klue `nli` validation | NLI / choice | 3 | 500 | B | XNLI 비영어 0.731 수준 (출처: BENCHMARKS.md "English vs the rest") |
| `ko_nsmc_sentiment.jsonl` | e9t/nsmc ratings_test.txt | 감성 / noul + 2-choice | 2 | 500 | B | choice ≥ noul (noul 레이블 추종 약점) |
| `ko_kmhas_hate.jsonl` | jeanlee/kmhas test | 혐오 여부 / noul | 2 | 500 | B | moderation held-out 0.53 수준의 약점 재확인 |
| `ko_kmhas_type_8.jsonl` | 같은 소스, 단일 레이블 혐오 행 | 혐오 유형 / choice | 8 | 500 | B | 유형 간 혼동 측정 |
| `ko_3i4k_speechact_7.jsonl` | warnikchow/3i4k fci_test.txt | 화행 / choice | 7 | 500 | B | 질문·명령 구분은 높고 수사적 유형은 낮음 |
| `ko_negation_probe.jsonl` | 수작업 (쌍) | 부정문 / 2-choice + noul | 2 | 100 (50쌍) | C | 부정문 행 정확도 급락 (#377 재현) |
| `ko_poc_triage_v1.jsonl` | 수작업 레이블 | **보류**(시나리오 A 파인튜닝 후보, 라벨링은 P4 결정 후) triage + gateway / 7 질문 | 6·4·2·3 | 200\~300 | (P4) | 05 §2 결정으로 G1 입력에서 제외 |

파생 파일(빌더 플래그로 생성, MANIFEST에 `derived_from` 기록. 2026-10-02 현재 ablation 변형 5개의 `derived_from`은 null이라 빌더 보완 예정): `ko_nsmc_sentiment_noul.jsonl`, `ko_nsmc_sentiment_choice.jsonl` (`--split-variants`), `ko_3i4k_speechact_6.jsonl` (`--drop-fragments`), 각 세트의 `*_ko-instr.jsonl` (`--instructions ko`), `*_ko-desc.jsonl` (`--descriptions ko`, 20opt·full60 전용), `*_en-desc.jsonl` (`--descriptions en`). 주의: `_en-desc`의 뜻이 세트마다 다르다. scenario_18의 `_en-desc`는 upstream key 렌더링(`k.replace("_", " ")`)으로 P0c의 0.52 vs 0.35를 재현하기 위한 것이고, domain_8과 YNAT의 `_en-desc`는 자연어 영어 설명이다. scenario_18의 자연어 영어 변형은 별도 dict가 필요하며 만들지 않았다(`scripts/build_ko_evalsets.py:178` `variant`).

---

## 5. 소스별 변환 스펙

공통: 텍스트 정규화는 **하지 않는다**(NFC 정규화도 하지 않음; 소스 바이트 그대로). 중복 제거는 완전 일치 텍스트 기준. 단, upstream 충실 MASSIVE 세트(20opt·full60·scenario_18, "첫 100행" 규칙)는 중복 제거에서 제외한다(ko test 첫 100행에 완전 중복 3쌍이 있고 upstream도 그대로 둔다. `results/poc/P0c_20261002.md`). 그 경우 MANIFEST에 `duplicates` 수를 기록한다. 길이 필터는 2자 미만 제외(3i4K 예외), 2,000자 초과 제외. 샘플링은 몫 `N // k`를 모든 레이블에 주고 criteria 순서의 앞쪽 `N mod k`개 레이블에 1행씩 더 주는 층화다(합계 정확히 N. 예: YNAT 72/72/72/71×4, domain_8 63×4/62×4. `scripts/build_ko_evalsets.py:218` `stratify`). 할당량에 못 미치는 레이블이 있으면 `random.Random(13)`으로 잔여 풀에서 보충해 N을 맞춘다. 실제 분포는 MANIFEST에 기록한다.

### 5.1 MASSIVE ko / en

**소스** `mteb/amazon_massive_intent`, config `ko` 및 `en`, split `test`. 피처 `id`, `label`, `label_text`(예: `alarm_set`), `text`(예: "이번 주 오전 다섯 시 에 깨워줘"), `lang`. 라이선스 CC BY 4.0 (원 저장소 alexa/massive의 `NOTICE.md` 기준, 2026-10-12 확인. HF 미러 `mteb/amazon_massive_intent`·`_scenario` 카드의 `license` 필드 apache-2.0(2026-10-02 확인)은 미러 자체 표기다. 상세는 `DATA_LICENSES.md`).

**(a) `*_massive_intent_20opt.jsonl`: upstream 충실 재현.** 구성 규칙을 바이트 단위로 따른다 (출처: research/scripts/bench_local.py:165-183).

```python
d = load_dataset("mteb/amazon_massive_intent", lang, split="test")
labels = sorted(set(d["label_text"]))          # 전체 의도 집합(ko test 기준 59개. cooking_query는 train에만 있음. 전체 집합은 데이터에서 계산), 정렬
rng = random.Random(13)                         # 언어당 한 번만 생성
for r in list(d)[:100]:                         # test split의 "첫 100행", 셔플 없음
    pool = [x for x in labels if x != r["label_text"]]
    keys = [r["label_text"]] + rng.sample(pool, 19)
    rng.shuffle(keys)
    criteria = {k: k.replace("_", " ").replace(".", ": ") for k in keys}
```

- state: `{"utterance": text}`; 질문 id `intent`; instructions `"What is the user asking for in `utterance`?"`; criteria는 위 변환(영어). `--descriptions ko`일 때만 `data/handwritten/massive_intent_ko_desc.json`(intent 전체, 빌드 시 `assert set(desc.keys()) == set(labels)`)으로 교체한다.
- expected: `{"intent": label_text}`. tags `["massive", "20opt", "scenario:<접두어>"]`, language `ko`/`en`.
- 재현 대상 수치: ko 0.110 / 0.470, en 0.820 / 0.710 (출처: BENCHMARKS.md:71 및 `en` 행). upstream은 자체 `score_cases`로 logits를 직접 뽑고 temperature를 적용했으므로 `laya-evals` 경로와 미세한 차이(배치 shape, dtype)가 있을 수 있다. 허용 오차는 03_benchmark_plan.md Track A가 정한다.
- 샘플 선택 규칙이 "첫 100행"이므로 층화하지 않는다. 20옵션 중 정답이 항상 포함되므로 random baseline = 0.050.

```json
{"state": {"utterance": "이번 주 오전 다섯 시 에 깨워줘"}, "questions": {"intent": {"type": "choice", "instructions": "What is the user asking for in `utterance`?", "criteria": {"alarm_set": "alarm set", "weather_query": "weather query", "play_music": "play music", "calendar_remove": "calendar remove"}}}, "expected": {"intent": "alarm_set"}, "tags": ["massive", "20opt", "scenario:alarm"], "language": "ko"}
```

(위 예시는 지면상 옵션 4개만 적었다. 실제 파일은 항상 20개.)

**(b) `ko_massive_intent_full60.jsonl`: 고카디널리티 probe.** 같은 100행에 대해 `labels` 전체(정렬 순서 고정)를 한 질문의 옵션으로 넣는다(이름의 60은 명목값, 실제 옵션 수는 데이터의 intent 수 = ko test 59개). criteria 기본값은 20opt와 같은 영어 key 렌더링이고, `--descriptions ko`(`_ko-desc`)는 `data/handwritten/massive_intent_ko_desc.json`(데이터의 intent마다 한 항목, ko test 기준 59개, 빌드 시 `assert set(desc.keys()) == set(labels)`)이 있을 때만 동작한다. 그 파일은 아직 없다(선택). tags `["massive", "high_cardinality"]`. 기대: 기본 `head_max_len=256`에서 옵션당 토큰 `max(4, (256-16)//59) = 4`로 레이블이 구분 불가능해져 붕괴. 03의 Track C가 같은 파일을 `head_max_len=512, max_len=1024` 및 `predict_shortlist(k=20)`로 재실행한다 (출처: README.md "Honest limits" 고카디널리티 항목). 옵션 순서를 고정 정렬로 둔 이유는 순서 효과를 Track C의 option-order probe와 분리하기 위함이다.

**(c) `ko_massive_scenario_18.jsonl`: 도메인 분류.** scenario는 `label_text`의 첫 `_` 앞 접두어로 파생한다. 접두어 집합: alarm, audio, calendar, cooking, datetime, email, general, iot, lists, music, news, play, qa, recommendation, social, takeaway, transport, weather. 빌더는 `len(set(prefixes)) == 18`을 assert하고, 불일치 시 `mteb/amazon_massive_scenario`의 scenario 필드와 대조해 매핑 표를 수정한다. 같은 100행, 옵션 18개 정렬 고정, 설명은 한국어(아래 표). 질문 id `scenario`, instructions `"Which domain does `utterance` belong to?"`, tags `["massive", "scenario18"]`. 이 세트의 `_en-desc` 변형은 자연어 영어 설명이 아니라 upstream key 렌더링(`k.replace("_", " ")`)이다. P0c의 한국어 설명 0.52 vs key 렌더링 0.35 비교를 재현하는 용도이며, 언어 효과와 설명 풍부도 효과가 섞여 있다. 자연어 영어 설명 변형은 별도 dict가 필요하고 만들지 않았다.

| key | 한국어 설명 | key | 한국어 설명 |
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

**(d) `ko_massive_domain_8.jsonl` / `en_massive_domain_8.jsonl`: PoC 주 과제, 8도메인 라우팅.** 18개 scenario를 겹치지 않는 8개 도메인으로 병합한다. P0c에서 18도메인 오답 대부분이 play↔music(14/17), audio→general, iot→alarm처럼 정의가 겹치거나 인접한 쌍에서 나왔고 play/music만 합쳐도 0.52 → 0.66이었기 때문이다(`results/poc/P0c_20261002.md`). 질문 dict는 `poc/schema/router_v1.json`(05 §4.1)이 정규 사본이다. 빌더는 그 파일이 있으면 byte 일치를 assert하고, 없으면 경고만 내고 진행한다(빌드 시점에는 파일이 없었다).

| key | 병합되는 scenario | 한국어 설명 |
|---|---|---|
| productivity | alarm, calendar, datetime, lists | 알람, 일정, 날짜와 시간, 할 일과 쇼핑 목록 |
| media | music, play, audio | 음악, 라디오, 팟캐스트, 오디오북 재생과 음량 조절 |
| smart_home | iot | 조명, 커피머신, 청소기, 플러그 등 스마트홈 기기 제어 |
| info_qa | qa, weather, news | 사실, 정의, 계산, 환율, 날씨, 뉴스 등 정보 질문 |
| communication | email, social | 이메일, 연락처, 소셜 미디어 게시와 확인 |
| lifestyle | takeaway, cooking, recommendation | 음식 주문과 배달, 요리법, 장소·이벤트·영화 추천 |
| transport | transport | 교통, 택시, 티켓, 길 안내 |
| general | general | 인사, 잡담, 농담, 위 어디에도 속하지 않는 일반 대화 |

- 소스: config `ko`, split `test` **전체**(2,974행. (a)\~(c)의 "첫 100행" 규칙이 아니다). 완전 중복 텍스트(55행)와 2자 미만 텍스트(2행, '랩'·'락')는 샘플링 전에 제거한다(이 세트는 중복 제거 면제 대상이 아니다). 도메인별 몫 62에 앞쪽 4개 도메인 1행씩 추가(63×4, 62×4)로 층화, seed 13, 정렬 기준 `id`. `--n 0`이면 2,917행 전부(`scripts/build_ko_evalsets.py:367` `massive_domain`).
- en 쌍: ko 파일에 들어간 행과 **같은 `id`**의 `en` test 행을 같은 질문·같은 expected로 쓴다(MASSIVE는 locale 간 병렬 코퍼스). 빌더는 쌍마다 `label_text` 일치를 assert한다. `language: "en"`. 07 §5 E1의 한국어 페널티 측정(쌍 McNemar)에 쓴다.
- 비중첩 검사: 빌더가 8개 설명의 어절 집합 교집합을 출력한다(2026-10-02 현재 `scripts/build_ko_evalsets.py`에 미구현, 수동 확인). 조사·의존명사(예: "등")와 쉼표 토큰은 제외하고 센다. 현재 교집합은 smart_home과 info_qa의 "등" 하나뿐이라 통과다. 제외 규칙 없이 내용어가 겹치면 설명을 고친 `router_v2.json`을 만들고 세트도 다시 생성한다. `massive --split train`(P4 학습 데이터용)은 미구현(TODO)이다.
- 질문 id `domain`, instructions `"Which domain should handle the request in `utterance`?"`, criteria 순서는 위 표 순서로 고정(C1이 순열 flip을 잰다). state `{"utterance": text}`, expected = 병합된 key, tags `["massive", "domain8", "scenario:<원래 scenario>"]`.
- 질문 dict:

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

### 5.2 KLUE YNAT (뉴스 토픽 7)

**소스** `klue/klue` config `ynat`, split `validation`(9,107행; test는 비공개). 피처 `guid`, `title`, `label` ClassLabel `["IT과학","경제","사회","생활문화","세계","스포츠","정치"]`. 라이선스 CC BY-SA 4.0 (KLUE GitHub README와 HF 카드 YAML, 2026-10-12 확인).

- 샘플링 N=500, 레이블별 상한 72, seed 13.
- state `{"headline": title}`. 제목은 평균 20\~40자의 짧은 뉴스 헤드라인이므로 토큰 예산 문제는 없다. 주의: 이 태스크는 "짧은 헤드라인의 토픽 분류"이며 고객 문의와 분포가 다르다. Track B에서는 "한국어 일반 분류 능력"의 지표로만 읽는다.
- 매핑:

| label idx | 원 레이블 | key | 한국어 설명 |
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

**소스** `klue/klue` config `nli`, split `validation`(3,000행). 피처 `guid`, `source`, `premise`, `hypothesis`, `label` `["entailment","neutral","contradiction"]`. 대안 소스: `kakaobrain/kor_nli` config `xnli`(validation/test, 같은 레이블)이며 KLUE가 불가할 때만 쓴다. 라이선스 CC BY-SA 4.0 (KLUE GitHub README와 HF 카드 YAML, 2026-10-12 확인).

- 샘플링 N=500, 레이블별 상한 167. tags에 `source:<airbnb|...>`를 넣어 도메인별 slice를 가능하게 한다.
- state `{"premise": ..., "hypothesis": ...}`. instructions가 두 필드를 모두 지칭한다. 두 문장을 하나의 문자열로 이어붙이지 않는 이유는 모델이 JSON 직렬화된 dict state를 읽도록 설계되어 있고(출처: README.md "Quickstart: Route Mode" state 설명), 필드 경계를 보존해야 wording ablation이 가능하기 때문이다.
- upstream의 XNLI 수치(비영어 multilingual 0.731)는 3-way choice로 측정됐으므로 같은 프리미티브를 쓴다.

```json
{"state": {"premise": "흡연자분들은 발코니가 있는 방이면 발코니에서 흡연이 가능합니다.", "hypothesis": "어떤 방에서도 흡연은 금지됩니다."}, "questions": {"relation": {"type": "choice", "instructions": "Given `premise`, how does `hypothesis` relate to it?", "criteria": {"entailment": "전제가 참이면 가설도 반드시 참이다", "neutral": "전제만으로는 가설의 참 거짓을 알 수 없다", "contradiction": "전제가 참이면 가설은 거짓이다"}}}, "expected": {"relation": "contradiction"}, "tags": ["klue", "nli", "source:airbnb"], "language": "ko"}
```

### 5.4 NSMC (영화 리뷰 감성)

**소스** HF `e9t/nsmc`는 스크립트 기반 데이터셋이라 datasets-server가 501을 반환하고 `datasets` 4.x에서 로드가 불안정하다. 원본 TSV를 직접 받는다: `https://raw.githubusercontent.com/e9t/nsmc/master/ratings_test.txt` (50,000행, 헤더 `id\tdocument\tlabel`, label 1 = 긍정). `data/raw/nsmc/ratings_test.txt`(공개 저장소에는 포함하지 않음)에 저장하고 sha256을 MANIFEST에 기록한다. 라이선스 CC0 1.0 (e9t/nsmc README, 2026-10-12 확인).

- 전처리: `document`가 비어 있거나 NaN인 행 제외, 2자 미만 제외(예: "굳 ㅋ"는 3자이므로 포함), 완전 중복 제거. N=500, 250/250 균형.
- **한 행에 두 질문.** `sentiment_noul`(noul)과 `sentiment_choice`(2-choice)를 같은 `questions`에 넣어 한 forward pass로 두 프리미티브를 비교한다. `laya-evals --slice qid`가 질문별 지표를 준다. 기본 가설: 영어 체크포인트에서 보고된 noul 레이블 추종(#156)이 multilingual·한국어에서도 나타나면 `sentiment_choice` 정확도가 더 높다 (출처: README.md "Honest limits" noul 항목).
- noul에는 criteria를 넣는다. "긍정"의 정의가 데이터셋에 묶여 있고, key는 정확히 `true`/`false`여야 한다. `--opaque-labels` 플래그는 `labels: {"true": "A", "false": "B"}`를 추가하는 ablation이다.
- choice key는 `positive`/`negative`(불리언 단어가 아닌 의미 레이블). `--opaque-keys`는 `A`/`B`로 바꾸는 ablation(README가 권하는 우회).
- `--split-variants`는 단일 질문 파일 두 개(`ko_nsmc_sentiment_noul.jsonl`, `ko_nsmc_sentiment_choice.jsonl`)를 파생한다. 용도: 프리미티브별 baseline 파일을 `--baseline`으로 독립 게이트할 때 `questions_sha256`이 깔끔해진다. 정규 파일은 두 질문 버전이다.

```json
{"state": {"document": "지루하지는 않은데 완전 막장임... 돈주고 보기에는...."}, "questions": {"sentiment_noul": {"type": "noul", "instructions": "Is the movie review in `document` positive?", "criteria": {"true": "영화를 긍정적으로 평가한다", "false": "영화를 부정적으로 평가한다"}}, "sentiment_choice": {"type": "choice", "instructions": "What is the sentiment of the movie review in `document`?", "criteria": {"positive": "영화를 긍정적으로 평가한다", "negative": "영화를 부정적으로 평가한다"}}}, "expected": {"sentiment_noul": false, "sentiment_choice": "negative"}, "tags": ["nsmc"], "language": "ko"}
```

### 5.5 K-MHaS (한국어 혐오 표현)

**소스** `jeanlee/kmhas_korean_hate_speech`, split `test`. 피처 `text`, `label` = Sequence of ClassLabel `["origin","physical","politics","profanity","age","gender","race","religion","not_hate_speech"]`(idx 8 = 혐오 아님, 다중 레이블). 로딩 주의: main 브랜치는 스크립트 기반이라 datasets 5.x가 "Dataset scripts are no longer supported"로 거부한다. 빌더는 Hub parquet export `refs/convert/parquet @5df3b7429d68f0ffc89dfbd0159cc72f29fad63c`의 `default/test/0000.parquet`을 로드한다(21,939행, ClassLabel 9개 이름 동일. `scripts/build_ko_evalsets.py:44-48`). 대안 소스: `smilegate-ai/kor_unsmile`(`문장` + 10개 레이블 열 + `clean`), 이 문서에서는 언급만 한다. 라이선스 CC BY-SA 4.0 (HF 카드에만 표기, 2026-10-12 확인. 논문과 GitHub 저장소에는 라이선스 표기가 없다).

**(a) `ko_kmhas_hate.jsonl`: 혐오 여부 noul.** `is_hate = (8 not in label)`. N=500, 250/250 균형. 다중 레이블 행도 그대로 포함(여부 판정에는 영향 없음). criteria를 넣는 이유는 "혐오"의 범위가 데이터셋 가이드라인에 묶여 있기 때문이다. upstream의 held-out moderation은 0.530(macro-F1 0.400)으로 거의 chance였다 (출처: BENCHMARKS.md "Themes"); 한국어에서 같은 약점이 재현되는지가 가설이다. tags `["kmhas", "hate"|"clean", "multi_label"(해당 시)]`.

```json
{"state": {"comment": "그만큼 길예르모가 잘했다고 보면되겠지 기대되네 셰이프 오브 워터"}, "questions": {"is_hate": {"type": "noul", "instructions": "Does `comment` contain hate speech or abusive language toward a person or group?", "criteria": {"true": "출신, 외모, 정치 성향, 욕설, 연령, 성별, 인종, 종교를 근거로 비하하거나 공격한다", "false": "비하나 공격이 없는 일반적인 댓글이다"}}}, "expected": {"is_hate": false}, "tags": ["kmhas", "clean"], "language": "ko"}
```

**(b) `ko_kmhas_type_8.jsonl`: 혐오 유형 choice.** `label`의 길이가 1이고 값이 0..7인 행만 사용(다중 레이블 행은 정답이 둘이므로 choice에 부적합). N=500, 레이블별 몫 62(+앞쪽 4개 1행), 부족한 유형은 가용 전량. 질문 id `hate_type`, instructions `"Which kind of hate speech does `comment` express?"`, tags `["kmhas", "hate_type"]`. 실제 분포: test의 단일 레이블 `race` 행이 27개뿐이라 race 27 + 잔여 풀 보충으로 500행을 채웠다(politics 72, origin 70, profanity 69, physical 68, gender 66, age 65, religion 63, race 27. `data/evals/MANIFEST.json`).

| idx | key | 한국어 설명 | idx | key | 한국어 설명 |
|---|---|---|---|---|---|
| 0 | origin | 출신 지역이나 국가를 근거로 비하 | 4 | age | 나이, 세대를 근거로 비하 |
| 1 | physical | 외모, 신체를 근거로 비하 | 5 | gender | 성별을 근거로 비하 |
| 2 | politics | 정치 성향, 정치인을 근거로 비하 | 6 | race | 인종, 민족을 근거로 비하 |
| 3 | profanity | 대상 없는 욕설, 저속한 표현 | 7 | religion | 종교를 근거로 비하 |

### 5.6 3i4K (화행 7)

**소스** HF `kor_3i4k`는 스크립트 기반이며 datasets-server가 404를 반환한다. 원본을 직접 받는다: `https://raw.githubusercontent.com/warnikchow/3i4k/master/data/train_val_test/fci_test.txt` (형식 `label\ttext`, label 0..6). 라이선스 CC BY-SA 4.0 (저장소 LICENSE 파일; README "We updated our LICENSE to CC-BY-SA-4.0"; 2026-10-12 확인).

| label | key | 한국어 설명 |
|---|---|---|
| 0 | fragment | 문장이 아닌 단어나 구 조각 |
| 1 | statement | 사실이나 의견을 전달하는 서술 |
| 2 | question | 정보를 요구하는 질문 |
| 3 | command | 행동을 요구하는 명령이나 요청 |
| 4 | rhetorical_question | 대답을 기대하지 않는 수사적 질문 |
| 5 | rhetorical_command | 실제 행동을 요구하지 않는 수사적 명령 |
| 6 | intonation_dependent | 억양에 따라 의미가 달라지는 발화 |

- **결정: 7-way 유지, fragment 행은 `tags`에 `fragment`를 넣는다.** 파일명 `_7`이 다른 문서들에서 이미 참조되고, 3i4K의 공개 기준치(7-way F1)와 비교 가능해야 하며, 모델이 "조각인지 아닌지"를 구분하는 것 자체도 음성 프런트엔드 라우팅에서 의미 있는 판단이다. 단어 하나짜리 state는 README의 "짧은 Latin 텍스트는 언어 신호가 없다" 문제와 달리 Hangul이면 스크립트만으로 multilingual에 라우팅되므로 라우팅 실패는 없다. 6-way가 필요하면 `--drop-fragments`로 `ko_3i4k_speechact_6.jsonl`을 파생한다. 파생 방식은 7-way 500행에서 `fragment` 행을 뺀 부분집합이며(다시 샘플링하지 않음) MANIFEST `derived_from`에 기록한다.
- 3i4K는 2자 미만 필터를 적용하지 않는다(한 글자 조각이 정상 데이터). N=500, 레이블별 상한 72.
- state `{"utterance": text}`, 질문 id `speech_act`, instructions `"What kind of speech act is `utterance`?"`.

```json
{"state": {"utterance": "오늘 회의 몇 시에 시작해요"}, "questions": {"speech_act": {"type": "choice", "instructions": "What kind of speech act is `utterance`?", "criteria": {"fragment": "문장이 아닌 단어나 구 조각", "statement": "사실이나 의견을 전달하는 서술", "question": "정보를 요구하는 질문", "command": "행동을 요구하는 명령이나 요청", "rhetorical_question": "대답을 기대하지 않는 수사적 질문", "rhetorical_command": "실제 행동을 요구하지 않는 수사적 명령", "intonation_dependent": "억양에 따라 의미가 달라지는 발화"}}}, "expected": {"speech_act": "question"}, "tags": ["3i4k"], "language": "ko"}
```

(예시 문장은 설명용 창작이며 실제 파일은 소스 행만 담는다.)

### 5.7 부정문 probe (`ko_negation_probe.jsonl`)

**소스** 수작업. `data/handwritten/negation_pairs.jsonl`을 빌더가 검증 후 복사한다. README는 #377의 해지 예문 5개에서 부정 요청 4개 전부를 `cancel_account`로 분류했고, 그중 하나는 확률 0.9998이었다고 보고한다 (출처: README.md "Honest limits" "Semantic choice labels do not make negation safe"). 한국어 부정은 "\~하고 싶지 않다", "\~하지는 않을게요", "\~만 빼고" 등 형태가 다양하므로 영어 결과가 그대로 옮겨지는지 측정한다.

- 구성: 5개 도메인(해지, 환불, 데이터 삭제, 알림 해지, 요금제 변경) × 10쌍 = 50쌍 100행. 각 쌍은 같은 핵심 동사를 두고 긍정 요청과 명시적 부정 요청으로 쓴다. 부정 행은 "원하지 않음 + 대안 요청" 형태를 절반 이상 포함한다(모델이 대안을 읽는지 확인).
- 질문 두 개: `action`(2-choice, 도메인별 의미 key 쌍, 예: `cancel_account`/`keep_account`)과 `wants_cancel`(noul, criteria 없음). 도메인별 key 쌍은 `negation_pairs.jsonl`의 `domain` 필드로 결정하며 빌더가 표로 들고 있다.
- tags `["negation", "positive"|"negated", "pair:<nn>", "domain:<name>"]`. `pair:` 태그로 03의 분석 스크립트가 쌍 단위 일관성(둘 다 정답)을 계산한다.
- 레이블 정책: 긍정 행 expected = 행동 key / `true`, 부정 행 = 비행동 key / `false`. 모호한 문장(조건부 요청 등)은 넣지 않는다.

```json
{"state": {"message": "계정을 해지하고 싶어요. 절차 알려주세요."}, "questions": {"action": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"cancel_account": "계정이나 서비스 해지를 원한다", "keep_account": "해지를 원하지 않는다. 유지하거나 다른 조치를 원한다"}}, "wants_cancel": {"type": "noul", "instructions": "Does the customer in `message` want to cancel the account?"}}, "expected": {"action": "cancel_account", "wants_cancel": true}, "tags": ["negation", "positive", "pair:01", "domain:cancellation"], "language": "ko"}
{"state": {"message": "계정을 해지하고 싶지는 않아요. 요금제만 더 싼 걸로 바꿔주세요."}, "questions": {"action": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"cancel_account": "계정이나 서비스 해지를 원한다", "keep_account": "해지를 원하지 않는다. 유지하거나 다른 조치를 원한다"}}, "wants_cancel": {"type": "noul", "instructions": "Does the customer in `message` want to cancel the account?"}}, "expected": {"action": "keep_account", "wants_cancel": false}, "tags": ["negation", "negated", "pair:01", "domain:cancellation"], "language": "ko"}
```

### 5.8 PoC triage 세트 (`ko_poc_triage_v1.jsonl`)

**보류(2026-10-02): 시나리오 C 선택(05 §2)으로 이 세트는 P4 파인튜닝을 결정한 뒤에만 만든다.** 아래 명세는 그때를 위해 유지한다.

**소스** 수작업 레이블. 한국어 고객 문의 200행 이상, 목표 300행. 문장은 창작 또는 공개 한국어 CS 문체 텍스트의 패러프레이즈이며 실제 고객 데이터·PII를 쓰지 않는다. 스키마는 05_poc_plan.md §4의 PoC v1 스키마와 동일해야 한다(질문 id·key·설명 문자열까지). 정규 사본은 `poc/schema/triage_v1.json` + `poc/schema/gateway_v1.json`(05 §4)이며 이 절의 문자열은 그것과 byte-identical해야 한다. 빌더 `poc` 서브커맨드는 두 파일을 읽어 `questions` dict를 만들고 이 절의 dict와 diff가 없음을 assert한다. 이 절은 그 스키마를 `laya.presets.triage_questions`에 한국어 설명을 붙이고(출처: laya/presets.py `triage_questions`) gateway 질문 2개(docs/use-cases.md §1)를 더한 형태로 명세한다. 05가 바뀌면 이 절과 세트를 v2로 재생성한다.

- **레이블 정책 선동결.** 06_templates.md §4의 템플릿으로 `data/handwritten/poc_triage_label_policy_v1.md`를 먼저 쓰고 sha256을 MANIFEST의 `label_policy_sha256`에 기록한 뒤 레이블링을 시작한다. 레이블러 2명이 독립 레이블 후 불일치 adjudication, 또는 1명 레이블 + 별도 adjudication pass. 불일치율(Cohen's κ 또는 단순 일치율)을 MANIFEST에 기록한다.
- state `{"message": text}`. presets가 `message` 필드를 지칭하므로 그대로 쓴다.
- 질문 7개(triage 5 + gateway 2)와 expected 규칙:

| 질문 id | type | expected | 비고 |
|---|---|---|---|
| `intent` | choice (6) | key 문자열 | 복수 의도면 "고객이 가장 먼저 해결을 원하는 것" 하나 |
| `is_urgent` | noul | true/false | 기한·즉시·긴급 등 시간 압박의 명시적 표현이 있을 때만 true |
| `frustration` | score (4) | 0..3 | 0 차분, 1 걱정·정중, 2 분명히 짜증, 3 매우 화남·강한 표현 |
| `refund_requested` | noul | true/false | 금전 반환을 명시적으로 요구 |
| `churn_risk` | noul | true/false | 해지·이탈·경쟁사 언급 |
| `needs_llm` | noul | true/false | 템플릿 액션(큐 배정, 정형 답변, 상태 조회)으로 끝나지 않고 개별 상황 설명·설득·복합 질의 등 생성형 답변이 필요하면 true (05 §4.2 gateway) |
| `complexity` | choice (3) | key 문자열 | canned 인사·표준 FAQ·단순 상태 확인 / structured API·템플릿으로 결정적 처리 가능 / complex 생성형 답변·다단계 추론·복합 분석 (출처: docs/use-cases.md §1) |

- 전체 `questions` dict(한국어 설명, 영어 instructions, noul은 presets처럼 criteria 없음. `poc/schema/triage_v1.json`과 `gateway_v1.json`의 `questions`를 합친 것과 byte-identical):

```json
{"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}, "is_urgent": {"type": "noul", "instructions": "Does `message` communicate time pressure or a deadline?"}, "frustration": {"type": "score", "instructions": "How frustrated does the customer sound in `message`?", "criteria": ["차분하고 중립적", "걱정하지만 정중함", "분명히 짜증남", "매우 화남 또는 강한 표현 사용"]}, "refund_requested": {"type": "noul", "instructions": "Does the customer ask for money back?"}, "churn_risk": {"type": "noul", "instructions": "Does `message` suggest the customer may leave for a competitor or cancel?"}, "needs_llm": {"type": "noul", "instructions": "Does answering `message` require a free-form generated reply rather than a templated action?"}, "complexity": {"type": "choice", "instructions": "How complex is the request in `message`?", "criteria": {"canned": "인사, 표준 FAQ, 단순 상태 확인", "structured": "API나 템플릿으로 결정적으로 처리 가능한 요청", "complex": "생성형 답변, 다단계 추론, 복합 분석이 필요한 요청"}}}
```

- tags `["poc", "intent:<key>", "channel:<chat|email|voice>"]`, language `ko`. 의도별 최소 25행, `other`도 25행 이상(감사 인사·오분류 문의 등).
- 예시 6행(의도별 1행, 일곱 expected 모두 포함; `questions`는 지면상 `intent` 하나만 적었고 실제 파일에는 위 dict 전체가 들어간다. 따라서 아래 6행은 설명용이며 그대로 `laya-evals validate`에 넣으면 거절된다, 아래 주의 참조):

```json
{"state": {"message": "지난달에 결제가 두 번 됐어요. 중복 결제된 건 오늘 중으로 환불해 주세요. 안 그러면 다른 서비스로 옮길 겁니다."}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}}, "expected": {"intent": "refund", "is_urgent": true, "frustration": 2, "refund_requested": true, "churn_risk": true, "needs_llm": false, "complexity": "structured"}, "tags": ["poc", "intent:refund", "channel:chat"], "language": "ko"}
{"state": {"message": "앱에서 사진을 업로드하면 매번 튕깁니다. 어제 업데이트 이후부터 그래요."}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}}, "expected": {"intent": "technical_help", "is_urgent": false, "frustration": 1, "refund_requested": false, "churn_risk": false, "needs_llm": true, "complexity": "complex"}, "tags": ["poc", "intent:technical_help", "channel:chat"], "language": "ko"}
{"state": {"message": "이번 달 청구서에 부가세가 따로 붙었는데, 요금제 가격에 포함된 게 아닌가요?"}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}}, "expected": {"intent": "billing_question", "is_urgent": false, "frustration": 0, "refund_requested": false, "churn_risk": false, "needs_llm": true, "complexity": "structured"}, "tags": ["poc", "intent:billing_question", "channel:email"], "language": "ko"}
{"state": {"message": "팀 플랜으로 바꾸면 사용자를 몇 명까지 추가할 수 있나요?"}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}}, "expected": {"intent": "information", "is_urgent": false, "frustration": 0, "refund_requested": false, "churn_risk": false, "needs_llm": false, "complexity": "canned"}, "tags": ["poc", "intent:information", "channel:chat"], "language": "ko"}
{"state": {"message": "다음 달부터 서비스 해지하려고 합니다. 해지 절차 안내해 주세요."}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}}, "expected": {"intent": "cancellation", "is_urgent": false, "frustration": 0, "refund_requested": false, "churn_risk": true, "needs_llm": false, "complexity": "structured"}, "tags": ["poc", "intent:cancellation", "channel:email"], "language": "ko"}
{"state": {"message": "담당자분이 친절하게 응대해 주셔서 감사합니다. 좋은 하루 보내세요."}, "questions": {"intent": {"type": "choice", "instructions": "What does the customer want in `message`?", "criteria": {"refund": "환불, 결제 취소, 중복 결제 환급을 요구", "technical_help": "버그, 오류, 접속 불가, 연동 문제 등 기술적 도움 요청", "billing_question": "청구서, 요금제, 결제 수단, 금액에 대한 문의", "information": "일반 정보, 가격, 사용 방법 문의", "cancellation": "해지, 탈퇴, 다운그레이드 요청", "other": "위 어느 것에도 해당하지 않음"}}}, "expected": {"intent": "other", "is_urgent": false, "frustration": 0, "refund_requested": false, "churn_risk": false, "needs_llm": false, "complexity": "canned"}, "tags": ["poc", "intent:other", "channel:chat"], "language": "ko"}
```

주의: 위 6행의 `questions`에는 `intent`만 적었다. 실제 파일에는 일곱 질문이 전부 들어가야 `expected`의 일곱 key가 모두 채점된다. `laya-evals validate`는 `questions`에 없는 `expected` key를 "'expected' names unknown question(s)"로 거절하므로(출처: laya/evals.py:92-94) 위 예시를 그대로 파일에 넣으면 validate가 실패한다. 빌더 `poc` 서브커맨드는 그 전에 7개 key 존재와 타입을 자체 검사한다.

---

## 6. 빌드 스크립트 명세

`scripts/build_ko_evalsets.py`, 단일 파일, 표준 라이브러리 + `datasets` + `pandas` + `laya`(validate·fingerprint용)만 의존. 실행은 항상 venv의 Python으로.

**서브커맨드**

| 서브커맨드 | 산출 | 비고 |
|---|---|---|
| `all` | 수작업 세트를 제외한 전부 + MANIFEST (`massive --mode domain`의 ko·en 쌍 포함) | `negation`, `poc`는 원본이 있을 때만 포함 |
| `massive --lang ko\|en --mode 20opt\|full\|scenario\|domain [--split test\|train]` | 5.1 (a)(b)(c)(d) | `--lang en`은 `20opt`와 `domain`에 허용(`domain`은 ko 파일과 같은 id의 쌍을 만든다). `--split train`은 `domain`에만, P4 파인튜닝 학습 데이터용 |
| `ynat`, `nli`, `nsmc`, `kmhas`, `i4k` | 5.2\~5.6 | `kmhas`는 두 파일을 함께 쓴다 |
| `negation` | 5.7 | `data/handwritten/negation_pairs.jsonl` 검증 후 복사 |
| `poc` | 5.8 | `data/handwritten/poc_triage_v1.csv` 또는 `.jsonl` 검증·변환. 레이블 정책 파일 존재와 sha256 확인 |
| `manifest` | `MANIFEST.json` 재계산 | 파일은 건드리지 않음 |
| `stats FILE...` | 토큰 길이·분포 리포트 | §7 |

**공통 플래그** `--n N`(0 = 전량), `--seed 13`, `--instructions en|ko`, `--descriptions ko|en`, `--out data/evals/`, `--raw data/raw/`, `--force`, `--split-variants`(nsmc), `--drop-fragments`(i4k), `--opaque-keys`·`--opaque-labels`(nsmc). ablation 플래그가 켜지면 출력 파일명에 접미어(`_ko-instr`, `_ko-desc`, `_en-desc`, `_opaque-keys`, `_opaque-labels`, `_6`)가 붙어 정규 파일을 덮어쓰지 않는다.

**동작 규약**

1. 결정적: 같은 입력·플래그·소스 sha256이면 출력 바이트가 같다. 레이블 순서는 정렬, 샘플링은 `random.Random(seed)` 하나를 세트 시작에서 생성.
2. 멱등: 출력 파일이 있고 sha256이 같으면 건너뛴다. 다르면 `--force` 없이는 중단하고 두 sha256을 출력한다(동결 파일 보호).
3. 모든 출력에 `laya-evals validate`를 서브프로세스로 실행하고 exit 0이 아니면 실패.
4. `questions_sha256`은 `laya.evals.questions_fingerprint(laya.evals.Dataset.from_jsonl(path))`로 계산한다 (출처: docs/evals.md "Run identity", 공개 API).
5. 원본은 `data/raw/<source>/`(공개 저장소에는 포함하지 않음)에 저장하고 sha256을 기록한다. HF 데이터셋은 `HF_HOME`을 `data/raw/hf`로 두면 캐시가 프로젝트 안에 남는다.
6. 네트워크: HF 데이터셋·GitHub raw 다운로드가 필요하므로 빌드 중에는 `HF_HUB_OFFLINE`을 해제한다. 체크포인트 로드는 하지 않는다(`stats`만 토크나이저를 로컬 `models/laya-multilingual/tokenizer`(공개 저장소에는 포함하지 않음)에서 읽음).
7. 파일 첫 줄에 `#` 주석으로 소스·빌드 인자·생성일을 기록한다(zh_decision_bench.jsonl 관례, 출처: research/evals/zh_decision_bench.jsonl 1\~3행). 생성일은 실제 시각이 아니라 세트 버전에 고정된 상수 `CREATED`(`scripts/build_ko_evalsets.py:34`)다. 그래야 규약 1의 byte-identical 재빌드가 성립한다. 실제 생성 시각은 MANIFEST의 `created_at`에만 기록한다.

**MANIFEST.json 스키마**(파일별 항목, 예시 한 개):

```json
{"version": 1, "builder_version": "0.1.0", "laya_version": "0.3.23", "created_at": "2026-10-02T00:00:00+09:00", "files": {"ko_klue_ynat_7.jsonl": {"path": "data/evals/ko_klue_ynat_7.jsonl", "sha256": "<64 hex>", "questions_sha256": "<hex>", "n": 500, "source": {"dataset": "klue/klue", "config": "ynat", "split": "validation", "revision": "<hf dataset sha>"}, "license": "CC BY-SA 4.0 (확인 필요)", "in_training_mix": "unknown", "build_args": {"n": 500, "seed": 13, "instructions": "en", "descriptions": "ko"}, "label_distribution": {"it_science": 72, "economy": 72, "society": 72, "culture_life": 71, "world": 71, "sports": 71, "politics": 71}, "majority_rate": 0.144, "derived_from": null, "label_policy_sha256": null}}}
```

`in_training_mix`는 `manifest`가 채운다. 헤더에 값이 있으면 그 값, 없으면 소스 데이터셋별 표 `TRAINING_MIX`(`scripts/build_ko_evalsets.py:56-59`), 둘 다 없으면 "unknown"이다. MASSIVE 파생 세트(ko·en)는 "held out (upstream build_benchmark_nb.py:760-762; base checkpoints. ft-v1 was trained on MASSIVE ko train, see results/P4)"이고, 위 예시의 KLUE처럼 upstream 근거가 없는 소스는 "unknown"이다. 이 값은 세트 파일 바이트와 무관하다(2026-10-07 MANIFEST 재생성, 세트 sha256 불변). 수작업 세트는 `label_policy_sha256`, `labellers`, `agreement`(일치율 또는 κ) 필드를 추가로 채운다. `majority_rate`는 Track F의 majority-class baseline이다. 질문이 둘인 파일(`ko_nsmc_sentiment.jsonl`)은 `label_distribution`과 `majority_rate`를 질문 id를 key로 하는 dict로 기록한다.

**실행 명령**

```bash
cd .
export HF_HOME=$PWD/data/raw/hf
unset HF_HUB_OFFLINE

# 전체 빌드(공개 소스) + MANIFEST
.venv/bin/python scripts/build_ko_evalsets.py all --n 500 --seed 13

# 단일 세트, ablation 변형
.venv/bin/python scripts/build_ko_evalsets.py massive --lang ko --mode 20opt
.venv/bin/python scripts/build_ko_evalsets.py massive --lang ko --mode domain --n 500     # PoC 주 과제
.venv/bin/python scripts/build_ko_evalsets.py massive --lang en --mode domain --n 500     # 같은 id의 en 쌍
.venv/bin/python scripts/build_ko_evalsets.py ynat --instructions ko
.venv/bin/python scripts/build_ko_evalsets.py nsmc --split-variants

# 수작업 세트 반영, MANIFEST 재계산
.venv/bin/python scripts/build_ko_evalsets.py negation
.venv/bin/python scripts/build_ko_evalsets.py poc
.venv/bin/python scripts/build_ko_evalsets.py manifest
```

---

## 7. 품질 체크와 동결

| 체크 | 기준 | 방법 |
|---|---|---|
| 포맷 | `laya-evals validate` exit 0 | 빌더가 자동 실행 |
| 레이블 분포 | 상한 규칙과 일치, 극단 불균형 없음 | MANIFEST `label_distribution` 확인 |
| majority rate | 기록됨 | MANIFEST `majority_rate` |
| 중복 | 세트 내 완전 중복 0 (MASSIVE 충실 세트는 예외, `duplicates` 수만 기록) | 빌더 assert |
| 토큰 길이 | state 토큰 p99 < 실제 room | `stats` 서브커맨드 |
| 눈 검사 | 세트당 무작위 10행 레이블 타당 | 수동, 결과를 run card에 메모 |
| 수작업 세트 | 정책 sha256 기록, 일치율 기록 | `poc`/`negation` 서브커맨드가 강제 |

토큰 길이 기준은 README의 공식을 따른다. 실제 state 여유는 `room = max_len - head_len - 1`이고 `head_len`은 질문이 실제로 만든 head 길이다 (출처: README.md "Honest limits" 토큰 예산 항목). multilingual 기본 `max_len=1024`에서 7옵션 한국어 설명 질문의 head는 대략 45\~80 토큰이므로 room은 약 940 이상이다. YNAT 헤드라인, NSMC 리뷰(최대 약 140자), K-MHaS 댓글은 모두 그 안에 들어가고, NLI와 PoC 세트도 수백 토큰을 넘지 않는다. `stats`는 laya의 `build_head`/`encode_text`로 state 토큰 수 분포(p50/p95/p99/max), 질문 head 길이, room을 계산한다(`scripts/build_ko_evalsets.py:517`). 영어 체크포인트(`max_len=512`, `head_max_len=192`)로도 돌릴 세트(en_massive)는 그 예산으로 다시 확인한다.

2026-10-02 빌드의 `stats` 실측: multilingual에서 모든 세트의 state 토큰 p99는 140 이하(최대 227, K-MHaS)이고 room은 최소 769라 잘리는 행이 없다. scenario_18의 head는 252/256으로 옵션이 236토큰을 차지해 여유가 4토큰뿐이다. 설명을 조금만 늘려도 cap에 걸리므로 wording ablation은 이 점을 감안한다. domain_8의 head는 199(`_ko-instr` 205, `_en-desc` 153)다. full60은 옵션당 4토큰 cap에 걸려 59개 중 47개만 구분된다(Track C6 가설대로). english 체크포인트에서는 `en_massive_domain_8`의 한국어 설명이 옵션당 22토큰으로 잘리고(8개 옵션은 구분됨), `en_massive_intent_20opt`는 일부 행에서 옵션당 8토큰 cap에 걸려 최악의 행은 20개 중 17개만 구분된다(upstream 계측 자체의 성질).

```bash
.venv/bin/laya-evals validate data/evals/ko_nsmc_sentiment.jsonl
.venv/bin/python scripts/build_ko_evalsets.py stats data/evals/*.jsonl
```

**동결 절차**

1. 위 체크를 모두 통과한 시점에 `manifest`를 실행해 sha256·questions_sha256을 기록한다.
2. 06_templates.md의 run card에 사용한 파일명과 sha256을 적는다. `laya-evals run --json` 리포트도 `config.dataset_sha256`·`config.questions_sha256`을 자체 기록하므로 두 값이 MANIFEST와 같은지 확인한다 (출처: docs/evals.md "Run identity").
3. 동결된 파일은 수정하지 않는다. 문구·레이블·행을 바꾸려면 `_v2` 파일을 만들고 MANIFEST에 새 항목을 추가한다. 빌더의 `--force` 보호가 이를 강제한다.
4. 레이블 정책 문서도 같은 규칙으로 버전을 올린다.

---

## 8. 라이선스와 출처 표

| 소스 | 접근 경로 | 라이선스(기록 기준) | 확인할 것 |
|---|---|---|---|
| Amazon MASSIVE | `mteb/amazon_massive_intent` (HF, config `ko`/`en`) | CC BY 4.0 (원 저장소 alexa/massive의 `NOTICE.md` 기준; HF 미러 `mteb/amazon_massive_intent`·`_scenario` 카드의 `license` 필드 apache-2.0(2026-10-02 확인)은 미러 자체 표기) | 확인함(2026-10-12): 원 데이터의 CC BY 4.0이 적용된다 |
| KLUE (YNAT, NLI) | `klue/klue` (HF) | CC BY-SA 4.0 (KLUE GitHub README, HF 카드 YAML) | 확인함(2026-10-12). SA 조항: 파생 세트는 CC BY-SA 4.0으로 배포한다(upstream에 기여할 때도 같다) |
| NSMC | GitHub raw `e9t/nsmc` | CC0 1.0 (저장소 README) | 확인함(2026-10-12) |
| K-MHaS | `jeanlee/kmhas_korean_hate_speech` (HF) | CC BY-SA 4.0 (HF 카드에만 표기) | 확인함(2026-10-12): 논문(COLING 2022)과 GitHub 저장소에는 라이선스 표기가 없다. SA 조항 적용 |
| 3i4K | GitHub raw `warnikchow/3i4k` | CC BY-SA 4.0 (저장소 LICENSE 파일; README "We updated our LICENSE to CC-BY-SA-4.0") | 확인함(2026-10-12). SA 조항 적용 |
| kor_nli (대안) | `kakaobrain/kor_nli` (HF) | CC BY-SA 4.0 **확인 필요** | 사용하지 않음(확인하지 않음) |
| kor_unsmile (대안) | `smilegate-ai/kor_unsmile` (HF) | **확인 필요** | 사용하지 않음(확인하지 않음) |
| 수작업 세트 | `data/handwritten/` | 프로젝트 소유 | PII 없음 체크리스트 통과 |

"확인 필요" 표기는 2026-10-02 시점에 HF API 메타데이터만 확인했고 데이터셋 카드의 라이선스 필드를 직접 읽지 않았다는 뜻이다. 사용한 소스(MASSIVE, KLUE, NSMC, K-MHaS, 3i4K)의 라이선스는 2026-10-12에 원 출처에서 확인했고, kor_nli와 kor_unsmile은 사용하지 않았다. 빌더는 `source.revision`(HF 데이터셋 커밋 sha)을 MANIFEST에 기록해 이후 라이선스 변경 추적이 가능하게 한다. SA 조항이 있는 소스(KLUE, K-MHaS, 3i4K)의 파생 세트는 CC BY-SA 4.0으로 공개한다(upstream에 기여할 때도 같다). 출처별 상세는 `DATA_LICENSES.md`에 있다.

---

## 열린 질문 / 가정

1. **instructions 기본 언어.** 영어 기본·한국어 ablation으로 가정했다(upstream 구성과 비교 가능). Track B 결과에서 한국어 instructions가 일관되게 유리하면 v2에서 기본을 바꾼다.
2. **noul criteria 정책.** 수작업 세트는 criteria 없음, 데이터셋 정의에 묶인 세트(NSMC, K-MHaS)는 criteria 있음으로 갈랐다. 중국어 실측(criteria가 noul을 always-true로 밀었다)과 영어 실측(criteria 없는 noul이 english 체크포인트에서 always-no)이 서로 다른 방향이므로, 한국어에서 어느 쪽인지는 03의 wording ladder가 답한다.
3. **3i4K fragment.** 7-way 유지 + `fragment` 태그로 결정했다. 6-way가 비교 기준으로 더 적절하다고 판단되면 `--drop-fragments` 파생 파일을 정규로 승격한다.
4. **PoC 세트 크기와 레이블러.** 300행·2인 레이블을 목표로 했으나 가용 인력은 미정. 1인 레이블 + adjudication pass로 시작하고 일치율은 추후 2인 샘플(50행)로 추정하는 대안을 둔다.
5. **MASSIVE 재현 허용 오차.** upstream은 자체 scorer로 측정했고 우리는 `laya-evals`를 쓰므로 소수점 둘째 자리 차이가 날 수 있다. 허용치는 03_benchmark_plan.md Track A 소관.
6. (해결, 2026-10-07) **학습 믹스 포함 여부.** 모델 카드에는 없지만 upstream 벤치마크 노트북이 "Neither checkpoint trained on typed-decisions, MASSIVE or XNLI"라고 적는다(research/scripts/build_benchmark_nb.py:762). MASSIVE 파생 세트의 `in_training_mix`를 "unknown"에서 held out으로 바꿨다(base 체크포인트 기준, ft-v1은 MASSIVE ko train으로 학습). 근거가 없는 나머지 공개 소스는 "unknown"으로 남는다.
7. **upstream 기여.** zh_decision_bench.jsonl처럼 `research/evals/`에 한국어 세트를 PR할지는 라이선스(SA 조항) 확인 후 결정한다. 라이선스는 2026-10-12에 확인했다(`DATA_LICENSES.md`): PR하더라도 KLUE·K-MHaS·3i4K 파생 세트는 CC BY-SA 4.0으로 남는다. PR 시 PoC 세트는 제외하고 공개 소스 파생 세트만 낸다.
8. (확인 완료) **`expected`에만 있는 key의 처리.** `laya-evals validate`는 `questions`에 없는 `expected` key를 `EvalError("'expected' names unknown question(s)")`로 거절한다(laya/evals.py:92-94). §5.8의 6행 예시는 설명용이며, 빌더 `poc` 서브커맨드가 7개 key를 먼저 검사한다.

[English](04_korean_evalset_spec.md) | **한국어**
