# Laya 다국어 System-1 결정 엔진의 한국어 적용성: zero-shot 벤치마크, 파인튜닝, 그리고 도메인 라우팅 PoC

**작성** 2026-10-06 · **환경** Apple M4 Pro(10P+4E CPU, 20코어 GPU/MPS, 48 GB), macOS 26.6.2 · **대상** laya 0.3.23(upstream 커밋 4aa6761), 체크포인트 번들 `convaiinnovations/laya` @ 55cf4c4 · **근거 파일** `results/`(리포트 `results/REPORT.md`, 판정 `results/go_no_go.json`, `results/verdicts.json`)

## 초록

Laya는 encoder 한 번의 forward pass로 typed decision(choice, score, noul)의 확률 분포를 내는 non-autoregressive 결정 엔진이며, 100개 이상 언어를 표방하지만 한국어 적용성은 MASSIVE intent 한 줄(0.470) 외에 검증된 바가 없다. 본 연구는 단일 Apple M4 Pro에서 (1) upstream 수치 재현, (2) 한국어 지원 수준 감사, (3) 공개 한국어 데이터 19종으로 만든 zero-shot 품질·견고성·보정 벤치마크, (4) 서빙 성능, (5) 라벨 데이터 파인튜닝, (6) 호스팅 결정 모델 Jev와의 소표본 비교를 수행하고, 그 결과로 한국어 8도메인 라우터 PoC를 서비스와 데모 UI까지 구현하였다. 핵심 결과는 다음과 같다. ① upstream의 한국어·영어 MASSIVE 수치 4칸이 Δ0.000으로 재현되었다. ② zero-shot 한국어 8도메인 라우팅 정확도는 test 절반 0.492로 스키마 문구·보정·임계값 어느 것으로도 0.6을 넘지 못했고, 같은 문장을 영어로 넣어도 한국어 서술형 설명 스키마에서는 페널티가 없어(0.526 vs 0.510, p=0.47) 한계는 언어가 아니라 체크포인트의 zero-shot 능력에 있었다. ③ MASSIVE ko train 11,094행으로 36분 파인튜닝한 ft-v1은 같은 test 절반에서 0.900, 전체 test 2,917행에서 0.913, ECE 0.053, 옵션 순서 flip 0.037을 기록하였다. ④ multilingual 체크포인트의 3문항 호출 p95는 MPS 22.6 ms, CPU 57.8 ms이고 HTTP 서버는 10 RPS에서 p95 79.4 ms였다. ⑤ 24항목 수동 비교에서 Jev는 Laya zero-shot을 앞섰고(0.833 vs 0.417, p=0.002) 파인튜닝한 ft-v1과는 구분되지 않았다(0.917, p=0.5). 결론적으로 Laya는 한국어에서 "zero-shot 결정 엔진"이 아니라 "빠르게 전문화할 수 있는 base"이며, 파인튜닝 파이프라인을 전제로 사전 정의한 게이트 G0\~G7을 모두 통과하였다(Conditional Go).

## 1. 서론

### 1.1 배경

Laya[1]는 ModernBERT-large(영어, 421M) 또는 mmBERT-base(다국어, 322M) encoder 위에 decision head를 얹어, 상태(state)와 typed question 묶음을 한 번의 forward pass로 평가한다. 질문 유형은 닫힌 라벨 집합에서 하나를 고르는 `choice`, 순서형 레벨의 기대값을 내는 `score`, 진술이 참일 확률을 내는 `noul`이며, 텍스트 생성이 없으므로 파싱 실패나 hallucination이 없다. 학습은 strictly proper scoring rule을 보상으로 쓰는 강화학습(RLCD)으로 하여 확률이 보정되어 있다고 주장하고, Router가 입력의 script·언어를 감지해 체크포인트를 고른다. upstream은 Tesla T4에서 1문항 32.8 ms, 51개 언어 MASSIVE intent 벤치마크(한국어 0.470), 그리고 호스팅 결정 API Jev 대비 우위를 제시한다[1].

### 1.2 문제

한국어에 대해 upstream이 제시한 수치는 20옵션 MASSIVE intent 100행뿐이며, 한국어가 학습 데이터에 포함되었는지, 토크나이저와 라우팅이 한국어 입력을 올바르게 처리하는지, 보정된 확률이 한국어에서도 성립하는지는 문서화되어 있지 않다. upstream 스스로 "base 체크포인트는 zero-shot 결정 엔진이 아니라 전문화를 위한 빠른 base"라고 적고 있어[1], 한국어 서비스에 도입하려면 zero-shot 상한과 파인튜닝 효과를 직접 측정해야 한다.

### 1.3 연구 질문

- RQ1. Laya는 한국어를 어느 수준으로 지원하는가(문서, 토크나이저, 라우팅, 모델)?
- RQ2. zero-shot 한국어 품질·견고성·보정은 어느 수준이며 스키마 설계로 개선되는가?
- RQ3. 로컬(Apple silicon) 서빙 성능은 사전 정의한 기준을 만족하는가?
- RQ4. 라벨 데이터 파인튜닝은 한국어 과제에서 얼마나 효과가 있는가?
- RQ5. 호스팅 결정 모델 Jev와 비교하면 어떤가?

### 1.4 기여

(1) upstream 수치의 완전한 재현(Δ0.000)과 결정적 평가 파이프라인. (2) 공개 한국어 소스 6종으로 만든 laya-evals 형식 평가셋 19종과 결정적 빌더(`scripts/build_ko_evalsets.py`). (3) 한국어 지원 감사(문서·토크나이저·라우팅·동일 문장 한영 비교). (4) zero-shot 상한을 확정한 벤치마크(Track A\~F)와 파인튜닝 결과(0.492 → 0.900). (5) 파인튜닝 체크포인트를 올린 라우터 서비스와 Laya Playground 데모 UI. (6) 측정 과정에서 발견한 upstream 결함·불일치 6건.

## 2. 배경 및 관련 연구

**Laya의 구조.** 각 질문은 `"<type> question: <instructions>"`와 옵션 렌더링(head), 그리고 state로 이루어진 시퀀스 한 행이 되고, 한 호출의 질문들은 같은 state를 반복한 행들로 배치를 이룬다. head 상한 `head_max_len`(multilingual 256, english 192)을 옵션들이 나눠 쓰므로 옵션당 토큰은 `max(4, (head_max_len − 16) // k)`로 줄어들고, 20옵션을 넘기면 라벨이 구분되지 않는다(upstream의 banking77 0.425)[1]. 로드 시 temperature는 [0.5, 5.0]으로 clamp되며, 답마다 `confidence`(1 − 정규화 엔트로피)와 `answer_confidence`(보고된 답의 확률, 보정 대상)가 함께 나온다. 체크포인트는 english(ModernBERT-large), multilingual(mmBERT-base, 컨텍스트 1,024, RoPE로 8,192까지), typed-decisions(영어 파인튠) 세 가지이며, Router는 hangul 범위(`laya/lang.py:43`)를 감지해 multilingual로 보낸다.

**mmBERT-base.** Marone et al.[2]은 ModernBERT 구조에 Gemma 2 토크나이저(256k vocab)를 쓰고 1,800개 이상 언어, 3T 토큰으로 사전학습한 encoder를 제안하였다. 한국어는 사전학습 단계의 60개 high-resource 언어에 포함되며 Table 9 기준 28.4B 토큰(1.43%), 89개 언어 중 13위다. 다만 FineWeb2-HQ 20개 언어에 한국어는 없다(`results/korean_support/audit_docs_tokenizer_routing.md`).

**평가 하네스.** `laya-evals`는 JSONL 라벨셋을 받아 choice_accuracy, noul_accuracy, score_mae, ECE(15 bins, `answer_confidence` 기준), mean_confidence, latency를 계산하고, 리포트 `config`에 dataset_sha256·questions_sha256·체크포인트 revision을 기록해 run identity를 보장한다[1]. 본 연구는 여기에 macro-F1, Brier, bootstrap CI, exact McNemar, coverage 곡선을 계산하는 `scripts/metrics_extra.py`를 추가하였다.

**Jev.** TypeSafe의 호스팅 결정 API로, Laya의 HTTP 서버는 같은 `POST /v1/systemone` 프로토콜을 제공한다. upstream이 인용하는 Jev 수치는 제3자 공개치(AG News 0.910, Banking77 0.870, Emotion 0.480, p50 236\~276 ms, ECE 0.246, 옵션 순서 flip 0.13)이며 직접 측정이 아니다[1][8]. 한국어 Jev 수치는 공개된 것이 없다.

**데이터.** MASSIVE[3]는 51개 로케일 병렬 음성비서 발화 코퍼스로 intent 60종(ko test 59종)과 scenario 18종 라벨을 가진다. KLUE[4]의 YNAT(뉴스 제목 7토픽)와 NLI, NSMC[5](영화 리뷰 감성), K-MHaS[6](다중 라벨 혐오 표현), 3i4K[7](화행 7종)를 함께 사용하였다.

## 3. 실험 설계

### 3.1 가설과 게이트

연구 질문을 가설 H1\~H10과 PoC 도입 게이트 G0\~G7로 구체화하였다(표 1). 게이트 기준값은 upstream 수치에서 외삽한 제안값이며 실행 전에 고정하였다(`docs/00_README.md` §6).

표 1. 게이트 정의

| 게이트 | 기준 |
|---|---|
| G0 재현 | upstream 공개 수치 ±0.03 |
| G1 정확도 | PoC 과제 test 절반 ≥ 0.80(LLM 베이스라인 미실행 시 절대 기준) |
| G2 선택적 자동화 | 오류율 ≤ 5%에서 coverage ≥ 0.70(보정 후) |
| G3 보정 | refit 후 held-out ECE ≤ 0.10 |
| G4 견고성 | 옵션 순서 permutation flip rate ≤ 0.10 |
| G5 in-process 지연 | 3문항 호출 p95 ≤ 100 ms(MPS) / ≤ 500 ms(CPU 10 threads) |
| G6 서빙 지연 | laya-serve 10 RPS에서 p95 ≤ 150 ms(MPS) |
| G7 배치 동치성 | predict vs predict_batch(sort_by_length) argmax flip 0, max \|Δp\| ≤ 0.01 |

### 3.2 데이터

표 2. 평가셋(`data/evals/`, `scripts/build_ko_evalsets.py`, seed 13)

| 세트 | 소스 | 과제 / 옵션 | n | 용도 |
|---|---|---|---|---|
| ko/en_massive_intent_20opt | MASSIVE ko·en test, upstream 충실 구성(첫 100행, 정답 + 19 distractor) | intent / 20 | 100 | Track A 재현 |
| ko_massive_intent_full60 | 같은 100행, 전체 intent | 59 | 100 | 고카디널리티 probe(미실행) |
| ko_massive_scenario_18 | 같은 100행, scenario 파생 | 18 | 100 | Track B |
| ko/en_massive_domain_8 | MASSIVE ko test 전체(중복·2자 미만 제거 후 2,917) 층화 500 + 같은 id의 en 쌍 | 8도메인 라우팅 | 500(전체 2,917) | PoC 주 과제, 한국어 페널티 |
| ko_klue_ynat_7 | KLUE YNAT validation | 뉴스 토픽 / 7 | 500 | Track B, PoC 보조 |
| ko_klue_nli_3 | KLUE NLI validation | NLI / 3 | 500 | Track B |
| ko_nsmc_sentiment | NSMC ratings_test | 감성 noul + 2-choice | 500 | Track B, C3, E6 |
| ko_kmhas_hate, ko_kmhas_type_8 | K-MHaS test | 혐오 여부 noul / 유형 8 | 500 / 500 | Track B |
| ko_3i4k_speechact_7 | 3i4K fci_test | 화행 / 7 | 500 | Track B |
| ablation 변형 5종 | 위 세트의 instructions 한국어화 / 설명 영어화 | | | Track B3 |

8도메인 taxonomy는 MASSIVE scenario 18종을 겹치지 않게 병합한 것이다(productivity ← alarm·calendar·datetime·lists, media ← music·play·audio, smart_home ← iot, info_qa ← qa·weather·news, communication ← email·social, lifestyle ← takeaway·cooking·recommendation, transport, general). 질문은 `"Which domain should handle the request in \`utterance\`?"`, 옵션은 ASCII key와 한국어 서술형 설명이다. dev/test 분할은 `results/B/B_splits.json`에 고정하였다(쌍 MASSIVE 세트는 행 index parity, 나머지는 state의 sha256 홀짝). ablation은 dev 절반에서만, test 절반은 고정된 스키마 버전당 한 번만 채점하였다. train 발화와 동일한 test 발화(500행 중 33, test 절반 16, 전체 2,917행 중 155; 라벨 동일)는 제외한 수치를 병기한다.

### 3.3 모델과 환경

체크포인트는 Hub revision 55cf4c4에 고정하고(`LAYA_REVISION=reviewed`), Python 3.12.12, laya 0.3.23, torch 2.14.1, transformers 5.18.0, onnxruntime 1.30.0을 사용하였다(`results/env/env_20261002-1333.json`). 품질 수치는 전부 CPU fp32(intra-op 10, inter-op 1)로 측정하였고 MPS는 지연 측정에 썼다. MPS는 5행 이상 호출에서만 fp16 autocast가 켜지며, P0에서 7문항 argmax 7/7 일치, max |Δp| 0.0017을 확인하였다(`results/poc/P0_20261002.md`).

### 3.4 프로토콜

정확도는 결정적 단일 패스, 지연은 warm-up 3회 후 10회 반복의 median·p95다. 정확도·ECE에는 percentile bootstrap 1,000회(seed 13) 95% CI, 비율에는 Wilson CI, 같은 항목의 A/B 비교에는 exact McNemar를 사용하였다. 모든 리포트는 dataset_sha256·questions_sha256·revision을 기록하며, 빌더와 스크립트는 같은 입력에 byte-identical 출력을 낸다.

### 3.5 스키마 설계 규칙

choice key는 ASCII snake_case(불리언 단어 금지), 설명은 한국어 서술형, instructions는 영어(upstream 관례; 한국어 instructions는 ablation), 옵션은 20개 이하, noul criteria는 정확히 `true`/`false` key, state 필드는 백틱으로 지칭한다. instructions·criteria는 questions_sha256으로 fingerprint되므로 문구를 바꾸면 새 버전 파일로 둔다.

## 4. 결과

### 4.1 재현(Track A)

표 3. upstream 충실 구성 MASSIVE intent-20(n=100, CPU fp32; `results/A/README.md`, `results/korean_support/K2_analysis.md`)

| 입력 | 체크포인트 | 측정 acc | upstream acc | Δ | ECE 측정 / upstream |
|---|---|---|---|---|---|
| ko | multilingual | 0.470 | 0.470 | 0.000 | 0.3108 / 0.3108 |
| en | multilingual | 0.710 | 0.710 | 0.000 | 0.2333 / 0.2333 |
| en | english | 0.820 | 0.820 | 0.000 | 0.1383 / 0.1382 |
| ko | english | 0.110 | 0.110 | 0.000 | 0.6804 / 0.6804 |

upstream은 logits를 packed forward로 뽑고 우리는 laya-evals의 행별 forward를 썼으나 이 해상도에서 차이가 없었다. fixture 12행의 5개 지표도 docs/evals.md 기대값과 4자리 일치하였다(`results/env/smoke_fixture_english_cpu.json`). H1은 지지된다.

### 4.2 한국어 지원 감사(RQ1)

표 4. 층위별 판정(`docs/07_korean_support_audit.md`)

| 층위 | 판정 | 근거 |
|---|---|---|
| 문서 | 한국어는 MASSIVE 평가 언어 50개 중 하나로만 문서화. RLCD 결정 학습 데이터에 한국어 기록 없음. 모델 카드의 "Korean 0.490"은 T4 n=300 값으로 공식 표 0.470(n=100)과 다른 run의 혼합 | 카드·BENCHMARKS.md |
| 인코더 | mmBERT 사전학습에서 한국어 28.4B 토큰(1.43%, 13위), 1단계 high-resource 언어 | [2] Table 9 |
| 토크나이저 | UNK 0, 조각화 0.2% 이하, 음절당 0.98 토큰. 같은 의미 문장의 토큰 수는 영어의 1.50배(중앙값, p90 2.20). english 토크나이저는 한국어 토큰의 91%가 글자 미만 byte 조각 | `audit_docs_tokenizer_routing.md` Part 2 |
| 유니코드 | NFC 정규화가 없어 NFD 입력은 토큰이 3.09배로 폭증 | 같은 파일 |
| 라우팅 | 46건 배터리 중 정상 28, 무방 4, default 의존 4, 실패 10. 라틴 문자가 다수인 혼합문과 영어 래퍼 속 10음절 미만 한국어가 english로 감. `lang="ko"` 명시만 전부 해결 | `part3_routing_battery.md`, `lang.py:364-371` |

upstream 51개 언어 표에서 한국어 0.470은 18위(중위수 0.400), ECE 0.311은 10위이며 ko/en 비율은 0.662다. 토큰 예산으로 보면 multilingual `max_len=1024`에서 7문항 스키마의 state 공간은 한국어 약 1,120\~1,310자, 영어 약 4,150자로 같은 내용 기준 한국어가 영어의 약 68%다.

**동일 문장 한영 비교.** MASSIVE 병렬 쌍으로 같은 내용의 한국어와 영어를 넣었다(표 5).

표 5. 한국어 페널티(multilingual; `results/korean_support/paired_ko_en_audit.md`, `results/B/summary_20261002.md`)

| 과제 | 옵션 텍스트 | n | ko | en | en − ko | McNemar p |
|---|---|---|---|---|---|---|
| intent-20 | 영어 key 렌더링(upstream 구성) | 100 | 0.47 | 0.71 | +0.24 [+0.13, +0.35] | 1.2e-04 |
| scenario-18 | 영어 key 렌더링 | 100 | 0.35 | 0.56 | +0.21 [+0.12, +0.30] | 4.9e-05 |
| scenario-18 | 한국어 서술형 설명 | 100 | 0.52 | 0.62 | +0.10 [−0.02, +0.22] | 0.143 |
| domain-8 | 한국어 서술형 설명 | 500 | 0.526 | 0.510 | −0.016 [−0.054, +0.022] | 0.47 |

페널티의 크기는 옵션 텍스트의 언어에 좌우된다. 영어 발화가 영어 key와 글자로 겹치는 효과를 빼도 격차는 남지만(key 겹침 행 +14/44 vs 비겹침 행 +10/56, p=0.04), 한국어 서술형 설명 스키마에서는 n=500에서 페널티가 사라졌다. 한영 임베딩 정렬(`embed_fn_from_agent`, 100쌍)은 P@1 0.19/0.31로 부분적이었다(chance 0.01). 30문장 프로브를 영어로 번역해 같은 7문항을 물었을 때 noul 4문항의 "no" 편향(always-no 93/120 대비 KO 93, EN 94)과 frustration 레벨 0 회피(0/30, 2/30)는 영어에서도 동일했으므로 이 약점은 한국어 특유가 아니라 multilingual 체크포인트의 성질이다. 같은 영어 문장을 english 체크포인트는 107/120 맞혔다.

### 4.3 zero-shot 품질(Track B, RQ2)

표 6. 세트 × 러너 정확도(CPU fp32; `results/B/summary_20261002.md`)

| 세트 | 옵션 | majority | english | multilingual | typed-decisions | Router auto |
|---|---|---|---|---|---|---|
| ko_massive_domain_8 (all / dev / test) | 8 | 0.126 | 0.262 | 0.526 / 0.560 / **0.492** [0.432, 0.552] | 0.288 | 0.526 |
| ko_klue_ynat_7 (all / test) | 7 | 0.144 | 0.216 | 0.634 / 0.655 | 0.234 | 0.634 |
| ko_massive_scenario_18 (n=100) | 18 | 0.210 | 0.310 | 0.520 | 0.330 | 0.520 |
| ko_massive_intent_20opt (n=100) | 20 | 0.170 | 0.110 | 0.470 | 측정 | 0.470 |
| ko_klue_nli_3 | 3 | 0.334 | 0.448 | 0.750 | 측정 | 동일 |
| ko_nsmc_sentiment choice / noul | 2 | 0.500 | 0.528 / 0.516 | 0.774 / 0.638 | 측정 | 동일 |
| ko_kmhas_hate (noul) / type_8 | 2 / 8 | 0.500 / 0.144 | 0.500 / 0.146 | 0.582 / 0.394 | 측정 | 동일 |
| ko_3i4k_speechact_7 | 7 | 0.144 | 0.174 | 0.178 | 측정 | 동일 |

multilingual은 모든 한국어 세트에서 유일하게 쓸 수 있는 체크포인트였고(H2 부분 지지: 10문항 중 7개에서 english 대비 ≥ +0.20), Router auto는 한글이 있는 행을 100% multilingual로 보냈다. domain_8 오답은 smart_home(gold 63, 예측 140)과 general(62, 80)이 흡수하였다. instructions 한국어화(Δ −0.020 / −0.004)와 설명 영어화(Δ −0.028 / +0.024)는 dev 절반에서 모두 비유의였다.

**사전 프로브.** 시나리오 선택 전 30문장 자가 라벨 프로브(CS triage 7문항)에서 intent 정확도는 0.40, criteria 없는 noul은 거의 항상 "no"(confidence 0.9 이상), frustration 레벨 0 선택은 0/30이었다(`results/poc/P0_20261002.md`). 스키마 변형 8종(noul criteria, labels A/B, 2-choice A/B·의미 key, 한국어 instructions, 의도 4개 축소, 영어 설명, 문자열 state, 조합)에서 intent 최고는 0.50, binary 4문항 합계는 어떤 형태도 always-no 기저 93/120을 넘지 못했으며 2-choice A/B는 A로 붕괴(68/120)하였다(`results/poc/P0b_ablation_summary.md`). 반면 100행 미리보기에서 YNAT 7토픽 0.65(상위 50% coverage에서 0.86), 18도메인 0.52가 나와 도메인 라우팅(시나리오 C)을 PoC 과제로 택하였다(`results/poc/P0c_20261002.md`). domain_8 스키마 v2 변형 6종(설명 강화, general 제거, 예시 문장 추가, 순서 변경, 5클래스 축소)은 전부 v1(dev 0.560) 이하였다(`results/C/C_schema_v2_20261002.md`).

### 4.4 견고성(Track C)

옵션 순서를 5회 무작위 치환했을 때 zero-shot 순열당 flip rate는 domain_8 0.270 [0.230, 0.310](any-flip 0.512), YNAT 0.168, scenario-18 0.241로 H5(10\~30%)를 지지하며 G4 기준 0.10에는 미달이었다. flip 337건 중 74%가 원 순서에서 이미 오답인 행에서 나왔고, confidence 0.9 이상 결정만 보면 0.094였다. 슬롯 위치 효과는 존재하지만(χ² p=0.0009) smart_home 흡수는 순서를 바꿔도 유지되어 의미적 원인으로 판정하였다(`results/C/C1_option_order_20261002.md`). NSMC에서 의미 key 2-choice 0.774는 noul 0.638보다 높았다(p=6.5e-10).

### 4.5 보정과 게이팅(Track E)

표 7. zero-shot multilingual 보정(`results/E/E_summary_20261002.md`)

| 항목 | 값 |
|---|---|
| as-shipped ECE(domain_8 dev / test, YNAT dev / test) | 0.200 / 0.263, 0.202 / 0.148, 모두 over-confident |
| fitted T(choice:6-10, clamp 미발동) | domain_8 2.0245, YNAT 1.8149, pooled 1.9161 |
| test ECE 전 → 후 | domain_8 0.263 → 0.098 [0.081, 0.162] (pooled) / 0.123(per-task); YNAT 0.148 → 0.063 |
| coverage @ 오류 ≤ 5% / ≤ 10%(domain_8 test, dev에서 고른 T) | 0.224 / 0.308 |
| 도메인별 T | dev coverage 0.180 → 0.316이나 test에서 예산 초과(과적합) → 기각 |
| E6 NSMC noul 임계값 | AUROC test 0.822, dev Youden 임계값 p(true) ≥ 0.0073 → test 정확도 0.725(0.5 기준 0.641) |

refit은 ECE를 절반 이하로 낮추고 세트 간에 전이되었으나(H4 후반부 경계 지지), coverage는 거의 바뀌지 않았다. 정확도 a에서 오류 e 이하로 덮을 수 있는 coverage의 상한은 a/(1 − e)이므로 0.492에서는 0.518이며, 보정으로는 G2를 넘을 수 없다. 2-class softmax에서 scalar temperature는 0.5 경계를 옮기지 못하므로 noul의 "no" 편향은 보정이 아니라 결정 임계값의 문제이고, E6에서 임계값만 옮겨도 0.641 → 0.725가 되었다.

### 4.6 성능(Track D, RQ3)

표 8. in-process 지연(median ms, 3q는 p95 병기; `results/D/D_summary_20261003.md`)

| 체크포인트 · state | CPU 1q / 3q (p95) / 10q | MPS 1q / 3q (p95) / 10q |
|---|---|---|
| multilingual · short 59 tok | 37.7 / 56.4 (57.8) / 121.4 | 13.8 / 22.5 (22.6) / 62.4 |
| multilingual · long 433 tok | 81.8 / 195.8 (247.8) / 596.5 | 35.1 / 92.2 (92.5) / 284.8 |
| english · short 123 tok | 86.6 / 184.4 (186.5) / 472.8 | 31.8 / 79.6 (80.0) / 232.3 |
| english · long (512 절단) | 204.5 / 515.1 (529.5) / 1658.1 | 85.6 / 242.1 (242.8) / 747.4 |

MPS는 CPU 10 threads 대비 1문항에서 2.33\~2.80배 빨랐고 문항 수가 늘어도 이점은 1.9\~2.8배로 일정했다(H8 기각). fp16 autocast 이득은 최대 8%였고, 호출 사이 100 ms 이상 쉬면 MPS가 2.2\~3.6배 느려졌다. intra-op 10 스레드가 최적이었고(14는 2\~22% 느림), 콜드 로드는 multilingual 3.45\~3.67 s(tokenizer 파싱 약 1.0 s), english 2.82\~2.97 s였다.

표 9. 배치·HTTP·ONNX·메모리

| 측정 | 결과 |
|---|---|
| predict_batch CPU n=256(bs 8/16/32) | 정렬 없는 batch는 loop의 0.62\~0.83배로 느림; sort_by_length는 unsorted 대비 1.67 / 1.83 / 2.08배, loop 대비 1.39 / 1.42 / 1.29배; flip 0, max \|Δp\| 0.0001(G7 통과, H9 지지). MPS 배치 이득은 1.21\~1.25배 |
| Router ko/en 교차 32건 | 체크포인트 전환 1회 0.130 s(CPU) / 0.206 s(MPS); max_loaded=2에서 reload 0회 |
| laya-serve MPS, 3문항 | open-loop 10 RPS p50 63.5 / p95 79.4 / p99 85.1 ms, 오류 0, 503 0(G6 통과); closed-loop 포화 처리량 1문항 50 RPS, 3문항 22.6 RPS(추론 직렬 처리) |
| laya-serve CPU, 3문항 | c=1 p95 103.5 ms, 10 RPS p95 135.8 ms, 포화 10 RPS |
| /v1/systemone/batch | 16 / 64 states 218 / 848 ms(약 75 states/s) |
| ONNX CPU(YNAT 500, batch 16) | torch 0.634 / ECE 0.1723 / p50 302.2 ms; fp32 export 동일 정확도, 455.0 ms; int8 0.622 / 0.1877 / 525.9 ms(1.74배 느림, argmax 일치 0.930) → H10 기각 |
| 메모리(CPU) | 상주 1 / 2 / 3 체크포인트 RSS 2.07 / 3.63 / 5.23 GiB; 64-state batch peak +1.86\~+5.49 GiB |

G5(3문항 p95 MPS 22.6 ms, CPU 57.8 ms), G6(79.4 ms), G7(flip 0)은 모두 통과하였다.

### 4.7 파인튜닝(P4, RQ4)

MASSIVE ko train 11,514행을 중복·길이 필터로 11,094행, validation 2,033행을 2,012행으로 정리하고 8도메인 라벨을 부여하였다. upstream의 Apple Silicon 학습 스크립트(`notebooks/laya_finetune_typed_decisions_mps.py`)를 그대로 쓰되 데이터 어댑터를 작성하였고(gold는 criteria key 기반 `{"probabilities": {key: 1.0}}`), 스크립트에 없는 옵션 순서 셔플 증강을 학습 아이템에 추가하였다(11,093/11,094행 재배열, validation은 원 순서). 하이퍼파라미터는 스크립트 기본(AdamW encoder 2.5e-5 / head 1e-4, weight decay 0.01, cosine, RLCD σ 0.4 → 0.1 + soft CE, fp32)에 micro-batch 8 × grad-accum 4, 3 epoch(1,041 step), gradient checkpointing 끔, validation 400행으로 temperature 보정이다. 유휴 MPS에서 학습 2,150 s(35.8분), 평가 약 10분, MPS peak 약 8 GB였다. 1,000행 1 epoch 프로브만으로 test 절반 0.492 → 0.720이었다(`results/P4/P4_probe_20261002.md`).

표 10. 파인튜닝 결과(`results/P4/metrics/full_20261003-1156_summary.md`, `full_20261003-1156_coverage_*.md`, `full_20261003-1156_option_order_dev.md`)

| 평가 | base multilingual | ft-v1 | 중복 제외(train 동일 발화 제외) |
|---|---|---|---|
| domain_8 500행 all / dev / test | 0.526 / 0.560 / 0.492 | 0.894 / 0.888 / **0.900** [0.860, 0.936] | test 0.893 (n=234) |
| domain_8 전체 test 2,917행 | 0.475 | **0.913** [0.902, 0.923] | 0.908 (n=2,762) |
| validation 2,012행, epoch 1 / 2 / 3 | 0.462 | 0.892 / 0.916 / 0.918 | 0.914 |
| macro-F1 (500 / 2,917) | 0.518 / 0.491 | 0.891 / 0.893 | |
| ECE test 절반 / 2,917 | 0.263 / 0.253 | 0.053 / 0.057 | |
| YNAT dev 245(망각 검사) | 0.612 | 0.633 | |
| 옵션 순서 flip(dev 250, 순열 5) | 0.270 | 0.037(any-flip 0.084) | |
| coverage @ 오류 ≤ 5% | 0.224 | test 절반 사후 T 0.756(T 0.938); 2,917행 dev T 0.907 적용 0.923(오류 0.042) | |

epoch 2와 3의 차이는 비유의하여 최종 export(epoch 3)를 v1으로 채택하였다. 남은 혼동은 general ↔ info_qa(2,012행 기준 25 / 20건)다. 셔플 증강 덕에 flip rate는 7분의 1로 줄었다.

### 4.8 Jev 대비(RQ5)

표 11. 공개 플레이그라운드 수동 비교(n=24, 2026-10-06; `results/F/jev_playground_manual_20261006.md`)

| 시스템 | 맞힌 수 | 정확도 | Wilson 95% |
|---|---|---|---|
| Jev(typesafe-ai/jev, 플레이그라운드) | 20/24 | 0.833 | [0.641, 0.933] |
| Laya zero-shot(multilingual) | 10/24 | 0.417 | [0.245, 0.612] |
| Laya ft-v1 | 22/24 | 0.917 | [0.742, 0.977] |

표본은 domain_8 test 절반에서 train과 겹치는 행을 뺀 234행 중 도메인별 3행이며, Jev에는 Laya와 같은 질문과 같은 순서의 8옵션을 `key: 한국어 설명` 형식으로 주었다. Jev vs zero-shot은 b=10, c=0, p=0.002로 Jev가 확실히 앞섰고, Jev vs ft-v1은 b=0, c=2, p=0.5로 구분되지 않았다(ft-v1이 22/24라 Jev가 24/24여도 p=0.5인 구조). Jev 오답 4건 중 2건은 "게임 열어"류로 우리 media 설명에 "게임"이 없어 생긴 공백이며, Jev는 틀릴 때 확신하지 않았다(오답 top 확률 41\~86%, 정답 평균 96.5%; 90% 컷에서 18/24 수용, 18/18 정답). 플레이그라운드 표시 지연 중앙값은 249.5 ms(203\~570; 제3자 공개 p50 236\~276 ms 범위 안), 브라우저 실측 POST 중앙값 497.5 ms로, 로컬 ft-v1 왕복 20.1 ms와의 배수(12\~36배)는 호스팅과 로컬의 차이에 네트워크가 섞인 값이다. Jev는 호출당 약 255 출력 토큰을 생성하여 생성형 디코딩으로 추정된다. 총 25회 요청(502 1회 포함)으로 무료 사이트의 사용량 제한 안에서 수행하였다.

### 4.9 PoC 서비스와 최종 판정

ft-v1을 `Router(models={"multilingual": ckpt_domain8_v1, "english": models/laya})`로 올리고(`poc/finetune/ckpt_domain8_v1/`과 `models/`는 공개 저장소에는 포함하지 않음) `laya.serve.create_app(router)`에 주입한 서비스(`poc/service/app.py`)에 `/poc/decide`, `/poc/shadow`, `/poc/meta`, 정적 `/poc/ui/`(Laya Playground)를 추가하였다. 훅은 NFC 정규화와 이메일·전화·카드번호 마스킹, shadow JSONL 기록, 카운터를 담당하고, 정책은 `answer_confidence ≥ T` 이면 ROUTE, 아니면 FALLBACK이며 T=0.907(2,917행 dev-1459에서 오류 5% 이하 최대 coverage; test-1458 적용 시 coverage 0.923, 오류 0.042)이다. 수용 점검 11/11 통과, `/poc/decide` 왕복 p50 20.1 / p95 21.1 ms, in-process CPU와 서버 MPS 답 일치 9/9였다(`results/poc/P2_20261003.md`).

표 12. Go/No-Go 매트릭스(`results/go_no_go.json`)

| 게이트 | 기준 | zero-shot | ft-v1 | 판정 |
|---|---|---|---|---|
| G0 | ±0.03 | Δ0.000 | 동일 | 통과 |
| G1 | ≥ 0.80 | 0.492 | 0.900(중복 제외 0.893, 2,917행 0.913) | 통과 |
| G2 | coverage ≥ 0.70 @ 오류 ≤ 5% | 0.224 | 2,917행 0.923(dev T 0.907); 250행 사후 T 0.756 | 통과(조건부) |
| G3 | ECE ≤ 0.10 | 0.098(refit) | 0.053 | 통과 |
| G4 | flip ≤ 0.10 | 0.270 | 0.037 | 통과 |
| G5 | p95 ≤ 100 / 500 ms | | MPS 22.6 / CPU 57.8 ms | 통과 |
| G6 | 10 RPS p95 ≤ 150 ms | | 79.4 ms | 통과 |
| G7 | flip 0, \|Δp\| ≤ 0.01 | | flip 0, 0.0001 | 통과 |

최종 판정은 **Conditional Go(파인튜닝 파이프라인 전제)**다. zero-shot은 G1·G2·G4 미달로 No-Go이고, 파인튜닝 ft-v1은 모든 게이트를 통과하였다.

## 5. 고찰

**핵심 함의.** ① upstream의 "fast base to specialise"는 한국어에서도 성립한다. 공개 라벨 데이터 1.1만 행과 36분의 로컬 학습으로 8도메인 라우팅 정확도가 0.49에서 0.90으로 올랐고 YNAT 망각은 없었다. ② 한국어 페널티는 옵션 텍스트의 언어에 좌우되며 한국어 서술형 설명에서는 사라지므로, 한국어 zero-shot의 한계는 언어 처리가 아니라 체크포인트의 zero-shot 결정 능력 자체다. ③ noul의 "no" 편향과 score 레벨 0 회피는 영어 입력에서도 같아 체크포인트 성질이며, 순위 정보(AUROC 0.76\~0.92)는 있으므로 임계값 조정으로 부분 회복된다. ④ 혼합문 라우팅 실패와 NFD 입력은 애플리케이션에서 `lang="ko"` 명시와 NFC 정규화로 보완해야 한다. ⑤ Apple silicon에서 MPS 이득은 2\~3배에 그치고 ONNX int8은 이득이 없으며, laya-serve의 직렬 추론은 프로세스당 처리량 상한(MPS 3문항 22.6 RPS)을 만든다. ⑥ 파인튜닝 후 Laya는 Jev와 동급 정확도를 로컬 20 ms 왕복으로 제공한다.

**발견한 upstream 결함·불일치.** (a) `laya.calibrate.records_from_labeled`에 `@torch.no_grad()`가 없어 실제 Agent에서 예외가 난다(calibrate.py:286 → agent.py:1177). (b) `laya.evals.evaluate`가 `predict(..., model=)`을 호출해 `Agent.predict`와 호환되지 않는다. (c) `hf download`의 agent 모드 출력 접두어로 문서의 심링크 명령이 깨진다(`--quiet` 필요). (d) 모델 카드의 "Korean 0.490"은 T4 n=300 값이고 공식 표는 0.470이다. (e) "multilingual의 criteria-less noul은 state를 읽는다"는 README 주장이 한국어와 영어 번역 모두에서 성립하지 않았다. (f) MASSIVE HF 미러의 license 태그(apache-2.0)와 원 저장소(CC BY 4.0)가 다르다. 부가적으로 examples/README.md의 MPS 첫 호출 13 s는 이 머신에서 0.1 s였다.

**한계와 타당성 위협.** 표본 크기(test 절반 n=250, 재현 n=100, 프로브 n=30 자가 라벨)로 인해 작은 차이는 판정하지 않았다. G2의 T는 dev 절반에서 골랐으며 250행 test 절반에서는 선택 방식에 따라 오류 7.9%(dev T) 또는 coverage 0.756(사후 T)으로 갈리고, 2,917행에서는 dev T로 오류 4.2%였다. train/test 동일 발화 155행은 제외 수치로 보완하였으나 라벨 분포 차이는 남는다. 품질 수치는 CPU fp32로만 쟀고 MPS fp16은 |Δp| ≤ 0.0085였다. 단일 머신·단일 세션 측정이며 간헐 호출 둔화의 원인은 분리하지 않았다. Jev 비교는 공식 API가 아닌 공개 플레이그라운드의 단일 패스(n=24)로 모델 버전이 표기되지 않고 옵션은 라벨 1칸으로만 전달되었다. 부정문(C4), 고카디널리티(C6), 장문(C8), LLM 베이스라인(F2)은 미실행이다.

## 6. 결론 및 향후 과제

Laya의 다국어 체크포인트는 한국어 입력을 토크나이저·라우팅·모델 수준에서 정상 처리하고 upstream 수치가 그대로 재현되지만, 한국어 다중 클래스 라우팅의 zero-shot 상한은 0.5\~0.65로 production 기준에 미치지 못한다. 라벨 데이터로 36분 파인튜닝하면 정확도 0.90\~0.91, ECE 0.053, flip 0.037, 오류 5% 이하 coverage 0.92(2,917행)를 달성하여 사전 정의한 게이트를 모두 통과하였고, 24항목 비교에서 호스팅 모델 Jev와 동급이었다. 향후 과제는 Jev API를 이용한 500행 paired 정식 비교, LLM zero-shot 베이스라인, 부정문 프로브, CS triage(시나리오 A) 파인튜닝, 실제 트래픽 세트에서의 운영 임계값 재선정, 그리고 발견한 결함의 upstream 보고다.

## 참고문헌

[1] NandhaKishorM, *laya* (v0.3.23, 커밋 4aa6761), [github.com/NandhaKishorM/laya](https://github.com/NandhaKishorM/laya), README.md, BENCHMARKS.md, docs/. 체크포인트 [huggingface.co/convaiinnovations/laya](https://huggingface.co/convaiinnovations/laya) (revision 55cf4c4).
[2] M. Marone, O. Weller, W. Fleshman, E. Yang, D. Lawrie, B. Van Durme, "mmBERT: A Modern Multilingual Encoder with Annealed Language Learning," arXiv:2509.06888, 2025.
[3] J. FitzGerald et al., "MASSIVE: A 1M-Example Multilingual Natural Language Understanding Dataset with 51 Typologically-Diverse Languages," arXiv:2204.08582, 2022. HF 미러 `mteb/amazon_massive_intent`.
[4] S. Park et al., "KLUE: Korean Language Understanding Evaluation," arXiv:2105.09680, 2021. HF `klue/klue`(ynat, nli).
[5] L. Park, *Naver Sentiment Movie Corpus v1.0* (NSMC), [github.com/e9t/nsmc](https://github.com/e9t/nsmc), 2015.
[6] J. Lee et al., "K-MHaS: A Multi-label Hate Speech Detection Dataset in Korean Online News Comment," COLING 2022. HF `jeanlee/kmhas_korean_hate_speech`.
[7] W. I. Cho et al., 3i4K 코퍼스, [github.com/warnikchow/3i4k](https://github.com/warnikchow/3i4k) (논문: "Speech Intention Understanding in a Head-final Language," arXiv:1811.04231, 2018; 게재지 확인 필요).
[8] AbdelStark, *jev-benchmarks*; nibzard, *decision-model-benchmark* (GitHub, Jev 제3자 측정; upstream BENCHMARKS.md가 인용).
[9] *Jev Playground* (독립 제3자 플레이그라운드), [jevplayground.com](https://jevplayground.com), 2026-10-06 접속. Model ID `typesafe-ai/jev`.

## 부록 A. 재현 절차(`results/REPORT.md` §9)

1. 환경: `docs/02_environment_setup.md` §2(uv venv 3.12, `laya[serve,onnx,structured]==0.3.23`, `hf download convaiinnovations/laya --revision 55cf4c4… --quiet`, `models/` 심링크, `env.sh`), §3 스모크.
2. 평가셋: `.venv/bin/python scripts/build_ko_evalsets.py all --n 500 --seed 13` + ablation 변형.
3. Track A: `laya-evals run data/evals/ko_massive_intent_20opt.jsonl --model multilingual --device cpu` 등 4런.
4. Track B: `results/B/B_run.sh` → `scripts/metrics_extra.py summary|paired`.
5. Track C: `scripts/probe_option_order.py … --permutations 5 --seed 13 --split dev`, `results/C/C_schema_v2_build.py`.
6. Track E: `scripts/calibrate_ko.py --sets … --splits results/B/B_splits.json --pooled --per-task --min-bucket-n 100 --out-payload poc/calibration/ko_v1.json`.
7. Track D: `results/D/D_run.sh`(bench_latency_local.py, bench_batch_local.py, bench_http_local.py, export_onnx + `laya-evals --onnx`).
8. P4: `poc/finetune/make_domain8_items.py rows|items` → `bash poc/finetune/run_full.sh`.
9. P2: `LAYA_DEVICE=mps LAYA_API_KEY=devkey LAYA_HOST=127.0.0.1 .venv/bin/uvicorn poc.service.app:app --host 127.0.0.1 --port 8000` → `http://127.0.0.1:8000/poc/ui/`, `results/poc/P2_acceptance.py`.
10. 대시보드: `python3 scripts/build_dashboard.py --results results/ --out results/dashboard/index.html`.

## 부록 B. 산출물

| 구분 | 경로 |
|---|---|
| 계획 문서 | `docs/00_README.md` \~ `docs/07_korean_support_audit.md` |
| 평가셋·빌더 | `data/evals/*.jsonl`(19종), `data/evals/MANIFEST.json`, `scripts/build_ko_evalsets.py` |
| 측정 스크립트 | `scripts/metrics_extra.py`, `probe_option_order.py`, `calibrate_ko.py`, `bench_latency_local.py`, `bench_batch_local.py`, `bench_http_local.py`, `build_dashboard.py`, `env_report.py` |
| 결과 | `results/A`, `B`, `C`, `D`, `E`, `F`, `P4`, `poc`, `korean_support`, `env`; `results/REPORT.md`; `results/dashboard/index.html`; `results/go_no_go.json`; `results/verdicts.json` |
| 파인튜닝 | `poc/finetune/ckpt_domain8_v1/`(공개 저장소에는 포함하지 않음), `poc/finetune/run_full.sh`, `make_domain8_items.py` |
| 서비스·UI | `poc/service/app.py`, `hooks.py`, `policy.py`, `poc/service/ui/index.html`, `poc/schema/router_v1.json`; 스크린샷 `results/poc/P2_ui_*.png` |

## 부록 C. 가설 판정(`results/verdicts.json`)

| 가설 | 판정 | 근거 |
|---|---|---|
| H1 ko MASSIVE 재현 | 지지 | Δ0.000, `results/A/README.md` |
| H2 multilingual ≫ english, Router 100% | 부분 지지 | 10문항 중 7개 ≥ +0.20; 한글 행 100% multilingual |
| H3 ≤7옵션 과제: majority 위, supervised 아래 | 전반부 지지 / 후반부 미결 | 문헌 supervised 값 미조회; ft-v1 0.913 |
| H4 as-shipped ECE > 0.25, refit ≤ 0.10 | 부분 / 경계 지지 | domain_8 0.263, YNAT 0.148; pooled 0.098 |
| H5 옵션 순서 flip 10\~30% | 지지 | 0.168\~0.270; ft-v1 0.037 |
| H6 noul < 2-choice 중립 key | 미결 | P0b A/B 2-choice 붕괴; 의미 key choice 0.774 > noul 0.638 |
| H7 부정문 zero-shot 실패 | 미결 | C4 미실행(프로브 5행 중 4행 오판) |
| H8 MPS 3\~6배, sub-linear | 기각 | 2.33\~2.80배 |
| H9 sort_by_length ≥ 1.3배, flip 0 | 지지 | 1.67\~2.08배, flip 0 |
| H10 ONNX int8 ≈ 2배, ECE drift ≤ 0.01 | 기각 | 1.74배 느림, ΔECE +0.0154 |

[English](08_paper_ko.md) | **한국어**
