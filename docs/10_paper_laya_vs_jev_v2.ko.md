# Laya와 Jev의 통제된 비교: 비자동회귀 결정 엔진의 zero-shot 정확도, 보정, 다국어 일관성, 지연

**작성** 2026-10-07 · **환경** Apple M4 Pro(10P+4E CPU, 20코어 GPU/MPS, 48 GB), macOS 26.6.2, Python 3.12.12, torch 2.14.1, transformers 5.18.0(`results/env/env_20261002-1333.json`) · **Laya** 0.3.23(upstream 커밋 4aa6761), 체크포인트 번들 `convaiinnovations/laya` @ 55cf4c4, 품질 측정은 CPU fp32 · **Jev** 독립 제3자 공개 플레이그라운드 jevplayground.com 경유(2026-10-06\~07), Model ID `typesafe-ai/jev`(버전 미표기) · **근거 파일** `results/F/jev_cmp/summary.md`, `summary.json`(S6 종합, 세션 요약 대조 수치 불일치 0건, `results/F/jev_cmp/S6_20261007.md:45`)

## 초록

Laya는 encoder 한 번의 forward pass로 typed decision(choice, score, noul)의 확률 분포를 내는 오픈소스 비자동회귀 결정 엔진이고, Jev는 같은 형식의 결정을 호스팅 API로 제공하는 상용 모델이다. upstream은 두 시스템을 제3자가 서로 다른 표본으로 잰 공개 수치로만 비교해 왔다. 본 연구는 같은 state 바이트, 같은 질문 문장, 같은 옵션 문자열을 두 시스템에 넣는 통제 비교를 8개 과제(8개 공개 데이터셋, 다국어 과제는 5개 언어)에서 수행했다. Jev는 공개 플레이그라운드로 438회 호출했고 요청 body가 사전 생성한 payload와 바이트 단위로 같은지 411/411건 확인했다. 과제별 exact McNemar에서 Jev가 4개 과제(T1, T4, T5, T7)에서 유의하게 앞섰고 4개는 비유의였으며 Laya가 유의하게 앞선 과제는 없었다. Holm 보정 뒤에는 T1과 T7만 유의하다. 8과제 macro 정확도는 Jev 0.828, Laya english 0.646, multilingual 0.598, Router 0.661이다. 다국어 의도 분류에서 Jev는 5개 언어 모두 0.900 이상(최고 0.950)이고 같은 id에 5개 언어가 같은 라벨을 낸 비율이 18/20인 반면 Laya는 5/20 이하였다. 반대로 같은 분포의 학습 데이터로 파인튜닝한 Laya는 두 과제에서 Jev와 같거나 수치상 앞섰다(후자는 비유의). 로컬 Laya의 1문항 지연(13.8\~86.6 ms)은 Jev 인터넷 왕복(브라우저 POST 중앙 465 ms)보다 짧았지만, 배포 형태가 달라 모델 속도 비교는 아니다.

- 정확도: Jev 유의 우세 4 / 비유의 4 / Laya 유의 우세 0(Holm 후 2 / 6 / 0). 독립 단일 문항 240개 합산 exact McNemar는 Jev 194 vs 과제별 최고 Laya 176, b/c 39/21, p=0.0273.
- macro 차이: Jev − Router +0.167 [+0.044, +0.293], Jev − 과제별 최고 Laya +0.153 [+0.031, +0.281](과제 bootstrap, 기술통계).
- 다국어 일관성: T7에서 Jev 평균 언어 페널티 +0.012, Laya english −0.362, multilingual −0.287.
- 보정: Jev 확률의 의미는 문항 형식마다 다르다(단일 choice는 오답의 59%가 top ≥ 0.90, 다문항 T1은 과소확신).
- 파인튜닝 참고선: T1에서 Laya typed-decisions 체크포인트 104/120 = Jev 104/120, 한국어 도메인 라우팅에서 Laya ft-v1 22/24 vs Jev 20/24.

## 1. 서론

### 1.1 동기

Laya upstream README는 "Laya (with routing) vs Jev" 표에서 typed-decisions 0.766 vs 0.727, AG News 0.950 vs 0.910, DAIR Emotion 0.595 vs 0.480, Banking77 0.425 vs 0.870, p50 지연 32.8 ms vs 236\~276 ms를 제시한다(`third_party/laya/README.md:1274-1291`; `third_party/laya/`(공개 저장소에는 포함하지 않음)는 https://github.com/NandhaKishorM/laya 를 커밋 4aa6761로 clone해 재현한다). 그러나 같은 문서와 BENCHMARKS.md는 Jev 수치가 "third-party published, never measured here"이고 표본과 프롬프트가 다르다고 명시한다(`third_party/laya/README.md:1276-1278`, `third_party/laya/BENCHMARKS.md:3`). 즉 두 시스템을 같은 입력으로 잰 통제 비교는 존재하지 않았다. 표본, 질문 문장, 옵션 렌더링이 다르면 정확도 차이를 시스템 차이로 읽을 수 없다.

### 1.2 연구 질문

- RQ1. 같은 입력에서 zero-shot 정확도는 어떻게 다른가?
- RQ2. 두 시스템의 확률은 보정되어 있고, 확신도로 자동 처리 여부를 가를 수 있는가?
- RQ3. 결정성, 옵션 순서, 언어를 바꿨을 때 결정은 얼마나 안정적인가?
- RQ4. 지연과 비용은 어떤 구조로 다른가?
- RQ5. Laya의 zero-shot 열세는 파인튜닝으로 닫히는가?

### 1.3 기여

(1) 8개 과제, 8개 공개 데이터셋, 5개 언어에서 입력 바이트를 맞춘 Laya vs Jev 통제 비교. upstream 문서와 그것이 인용한 제3자 벤치마크에는 이런 비교가 없다. (2) 재현 가능한 하네스: 과제별 플레이그라운드 폼 파일, 클릭 전 payload 해시와 클릭 후 요청 body 바이트 대조, 411건 마스터 요청 로그. (3) 다중 비교 보정(Holm), 과제 bootstrap, 독립 항목 합산 McNemar, 군집 bootstrap을 함께 쓴 통계 처리. (4) 문항 형식별 확신도 분석과 자동화 임계값에 대한 함의. (5) 파인튜닝 참고선과 한국어 도메인 라우팅 PoC 사례. (6) 연구 중 발견한 upstream 결함과 문서 불일치 7건.

## 2. 배경

### 2.1 Laya

Laya는 typed question(`choice`, `score`, `noul`)을 state(텍스트, 이메일, JSON 문서)에 대해 "a single forward pass"로 평가한다(`third_party/laya/README.md:129`). 체크포인트는 세 개다: english(ModernBERT-large, 421M, 컨텍스트 512), multilingual(mmBERT-base, 322M, 1,024, 최대 8,192), typed-decisions(ModernBERT-large, typed-decisions 워크플로로 파인튜닝)(`third_party/laya/README.md:135-137`). Router는 입력의 문자 체계와 언어로 english와 multilingual 중 하나를 고른다(`third_party/laya/README.md:385`). 질문과 옵션은 head 토큰 예산(`head_max_len`, english 192)을 나눠 쓰고 state는 남은 예산을 쓴다(`third_party/laya/README.md:1390`). dict state는 `json.dumps(state, ensure_ascii=False)`로 직렬화되어 비라틴 문자가 원문 그대로 모델에 들어간다(`.venv/lib/python3.12/site-packages/laya/common.py:78`, 공개 저장소에는 포함하지 않음). upstream은 base 체크포인트를 "a fast base to specialise, not as a zero-shot decision engine"이라고 스스로 규정한다(`third_party/laya/README.md:1530`).

### 2.2 Jev와 플레이그라운드

Jev는 TypeSafe AI의 호스팅 결정 모델로, state와 typed question을 받아 확률이 붙은 결정을 돌려준다(`docs/09_laya_vs_jev_plan.md:11`). jevplayground.com은 Jev를 호출하는 독립 제3자 UI이고 TypeSafe AI와 무관하다고 밝힌다(`results/F/jev_playground_manual_20261006.md:224`). 사이트는 "Free to try · Usage limits apply"라고만 적고 수치 한도는 공개하지 않는다(`docs/09_laya_vs_jev_plan.md:48`). 플레이그라운드에서 확인한 제약은 다음과 같다(`results/F/jev_cmp/sessions/S1_20261006/multi_question_mode.md` §1).

- Single question과 Multiple questions 모드가 있고, 후자는 2\~5문항, 타입 혼합, state 공유를 지원한다.
- Choice 옵션은 2\~10개이고, 라벨 입력은 80자에서 오류 없이 잘린다.
- Score는 정확히 5레벨(0\~4)만 받는다.
- Boolean에는 라벨과 설명 칸이 없다.
- 확률은 소수 둘째 자리로 반올림된다.
- "View details"에 Model ID와 입력·출력 토큰 수가 표시되고, choice·score 질문에는 별도 confidence가 붙는다.

요청당 출력 토큰 중앙값은 Boolean 20, score 17, choice 61\~150으로 형식과 옵션에 따라 달라, 응답 생성에 디코딩 단계가 있는 것으로 추정되지만 확인되지 않았다(`results/F/jev_cmp/summary.md` §7.3, `results/F/jev_playground_manual_20261006.md` §4). 모델 버전, 학습 데이터, 서버 측 프롬프트 래핑 여부는 알 수 없다.

### 2.3 기존 비교 수치

upstream이 인용하는 Jev 수치의 출처는 제3자 벤치마크(AbdelStark/jev-benchmarks, nibzard/decision-model-benchmark)다(`third_party/laya/README.md:1268-1272`). 비교표의 Jev 열은 Jev 1.13.0으로 표기되어 있다(`third_party/laya/README.md:1281`). typed-decisions(400 case, 2,000 decision)에서 Jev 1.13.0은 accuracy 0.727, soft 0.580, Brier 0.148, ECE 0.144, score MAE 0.391로 인용된다(`third_party/laya/README.md:1304-1313`). 보정은 ECE Jev 0.246 대 Laya 0.081로 제시되며, Laya 값은 도메인별 temperature fitting 뒤의 값이다(`third_party/laya/README.md:1287`, `:1300`). 옵션 순서 flip은 Jev 0.13으로 보고됐다(`third_party/laya/BENCHMARKS.md:213`). 이 수치들은 본 연구와 표본이 다르므로 맥락으로만 쓴다.

## 3. 방법

### 3.1 과제와 데이터

표본은 공개 split에서 seed 13으로 결정적으로 뽑았다. 단일 문항 과제는 중복·길이 규칙을 적용한 뒤 레이블로 층화했고, T1은 workflow로 층화했으며, T7은 5개 언어에 모두 있는 첫 20개 test id를 쓰고 오답 옵션 9개를 seed로 뽑았다(`data/evals/jev_cmp/MANIFEST.json`, `scripts/build_jev_cmp_sets.py`).

| 과제 | 소스 @revision | split | n | 형식 / 옵션 | Laya 학습 믹스 |
|---|---|---|---|---|---|
| T1 typed-decisions | `LocalLLaMA/typed-decisions` all @d0e2f0c | test | 40 case, 비교 가능 decision 120 | Multiple questions: choice 50, Boolean 60, 5레벨 score 10 | no |
| T2 AG News | `fancyzhx/ag_news` @eb185aa | test | 40 | choice 4 | yes |
| T3 DAIR Emotion | `dair-ai/emotion` split @cab853a | test | 40 | choice 6 | no |
| T4 Banking77-10 | `mteb/banking77` @18072d2 | test | 40 | choice 10(정답 + 오답 9, key-only 렌더링) | held out |
| T5 BoolQ | `google/boolq` @35b264d | validation | 40 | Boolean | yes |
| T6 SST-5 | `SetFit/sst5` @e51bdcd | test | 40 | score 5레벨 | no |
| T7 MASSIVE intent-10 | `mteb/amazon_massive_intent` en·de·ja·zh-CN·ko @940fd47 | test | 같은 20 id x 5개 언어 = 100 | choice 10(영어 key, 정답 + 오답 9, upstream 20옵션에서 축소) | held out |
| T8 prompt-injections | `deepset/prompt-injections` @4f61ecb | test | 40 | Boolean | no |

학습 믹스는 MANIFEST의 `in_training_mix`다. upstream은 AG News(T2)와 BoolQ(T5)만 Laya 학습 믹스에 넣었고(일반화가 아니라 retention), Emotion·prompt-injections·Banking77·SST-5는 held out, typed-decisions·MASSIVE는 두 체크포인트 모두 학습하지 않았다고 적는다(`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`, `results/F/jev_cmp/summary.md` §2.1). 표의 no와 held out은 모두 학습 믹스에 없다는 뜻이다. Jev의 학습 데이터는 알 수 없고 모든 소스가 공개 데이터셋이다.

### 3.2 입력 동일성

- **state**: Laya가 실제로 읽는 JSON 직렬화 문자열(`state_text`)을 Jev의 State 칸에 그대로 넣었다. 질문 문장은 upstream 벤치마크 스크립트의 문장을, T1은 데이터셋 자체 질문을 그대로 썼다(MANIFEST `question_source`).
- **옵션**: choice는 Laya가 실제로 렌더링하는 옵션 문자열(과제에 따라 `key: 설명` 또는 key 단독)을 같은 순서로 넣었다. 플레이그라운드의 80자 제한 때문에 T4는 upstream 방식의 key 단독 렌더링으로 두 시스템 모두 다시 만들었다(이전 렌더링은 `_v0`로 보관). T1에서 80자를 넘는 옵션을 가진 decision 10개는 비교에서 뺐다.
- **Score**: 플레이그라운드가 5레벨만 받으므로 T1의 4레벨 score 70개를 뺐다. 그 결과 T1의 비교 대상은 200개 중 120개다.
- **Boolean**: Jev Boolean에는 설명 칸이 없다. 공정성 점검으로 Laya에서 noul의 true/false 설명(criteria)을 뺀 변형을 따로 쟀고 정확도 변화는 유의하지 않았다(english 0.467 → 0.517, p=0.549; `results/F/jev_cmp/laya_summary.md` §2b). T5·T8의 noul은 원래 criteria가 없다.
- **검증**: 매 요청 전에 폼 파일로 만든 payload의 해시를 대조하고, 요청 후 실제 body를 바이트 단위로 대조했다(411/411 일치). 화면 표시와 응답 JSON도 410/410 일치했다(`results/F/jev_cmp/summary.md` §1).

### 3.3 Jev 실행

| 세션 | 날짜 (KST) | 내용 | 요청 | 최소 간격 |
|---|---|---|---|---|
| 파일럿 | 2026-10-06 08:09\~08:33 | 한국어 도메인 라우팅 24행 | 25 (502 1회) | 21.6 s |
| S1 | 2026-10-06 10:04\~10:17 | 탐색 1 + T2 40 | 41 | 17.0 s |
| S1b | 2026-10-06 10:29\~10:38 | 결정성 10 + 옵션 순열 20 (T2) | 30 | 17.3 s |
| S2 | 2026-10-07 08:49\~09:12 | T1 39 case + T3 40 | 80 (502 1회, 재시도 성공) | 12.1 s |
| S3 | 2026-10-07 13:36\~13:56 | T4 40 + T5 40 | 80 | 15.0 s |
| S4 | 2026-10-07 14:16\~14:36 | T6 40 + T7 en·de 40 | 80 | 15.0 s |
| S5 | 2026-10-07 14:53\~15:18 | T7 ja·zh-CN·ko 60 + T8 40 | 100 | 15.0 s |

사이트 상태 확인 2회를 더해 총 438회다(`results/F/jev_cmp/summary.md` §1). 운영 규칙은 클릭 간격 10초 이상, 5xx는 60초 뒤 1회 재시도, 429·제한 문구·captcha는 즉시 중단이었다. 처음에는 하루 요청 수에 자체 상한을 두었다. 사이트가 수치 한도를 공개하지 않고 해제 전 178회 동안 429와 제한 문구가 0회였으므로, 2026-10-07 프로젝트 책임자 결정으로 상한을 해제하고 간격·중단 규칙은 유지했다. 해제 뒤 S3\~S5 260회를 포함해 그날 340회 동안 429, 제한 문구, captcha는 나오지 않았다(`docs/09_laya_vs_jev_plan.md:48`). T1의 row 30은 S1 탐색 요청의 payload가 본 실행과 같아 재사용했다.

### 3.4 Laya 측정

Laya는 Jev 폼을 만든 것과 같은 세트 파일(laya-evals JSONL)로 CPU fp32(intra-op 10, inter-op 1), batch 8에서 english, multilingual, Router 세 러너를 모두 쟀다(`results/F/jev_cmp/run_laya.sh`, `results/F/jev_cmp/S0_20261006.md`). T1에는 upstream 파인튜닝 체크포인트 typed-decisions를 참고선으로 추가했다. T1 english를 다시 실행한 답이 200/200 같아 결정적임을 확인했다(`results/F/jev_cmp/laya_summary.md` §5).

### 3.5 통계

정확도 구간은 Wilson 95%, 같은 항목의 두 시스템 비교는 exact McNemar(양측)를 썼다. b는 Jev만 정답, c는 Laya만 정답인 항목 수다. 과제마다 Jev와 비교할 Laya는 세 러너 중 정확도가 가장 높은 러너이며, 결과를 보고 고른 사후 선택이라 Laya에 유리하다. 8개 과제 검정에는 Holm 보정을 적용했다. 과제 macro 평균의 차이는 과제 8개를 복원 재표본한 paired bootstrap(10,000회)으로, 독립 단일 문항(T2·T3·T4·T5·T6·T8, 240개)은 합산 exact McNemar로, 군집이 있는 T1(case 40)과 T7(id 20)은 군집 bootstrap으로 따로 봤다. Boolean은 AUROC(항목 재표본 2,000회), 보정은 Brier와 ECE(15 bins, top 확률 기준), score는 MAE of E[level]를 함께 보고한다(`results/F/jev_cmp/summary.md` §2, §4).

### 3.6 위협 요약

플레이그라운드는 API가 아니고 모델 버전이 표기되지 않는다. 과제당 n=40이라 Wilson 반폭이 약 ±0.15다. T1의 정답은 데이터셋 teacher 분포의 argmax이고 teacher의 정체는 확인하지 못했다. 상세는 §6.4에 둔다.

## 4. 결과

### 4.1 정확도 (RQ1)

| 과제 | Jev | Laya english | Laya multilingual | Laya Router | Jev vs 최고 Laya: b/c, p (Holm p) | 판정 (Holm 후) |
|---|---|---|---|---|---|---|
| T1 typed-decisions (120) | 104/120 = 0.867 [0.794, 0.916] | 0.383 | 0.367 | 0.383 | english 66/8, 1.8e-12 (1.4e-11) | Jev 우세 (Jev 우세) |
| T2 AG News (40) | 35/40 = 0.875 [0.739, 0.945] | 0.975 | 0.925 | 0.975 | english 0/4, 0.1250 (0.3750) | 비유의 (비유의) |
| T3 DAIR Emotion (40) | 28/40 = 0.700 [0.546, 0.819] | 0.750 | 0.625 | 0.750 | english 2/4, 0.6875 (1.0000) | 비유의 (비유의) |
| T4 Banking77-10 (40) | 37/40 = 0.925 [0.801, 0.974] | 0.725 | 0.750 | 0.725 | multilingual 8/1, 0.0391 (0.1953) | Jev 우세 (비유의) |
| T5 BoolQ (40) | 37/40 = 0.925 [0.801, 0.974] | 0.725 | 0.600 | 0.725 | english 9/1, 0.0215 (0.1289) | Jev 우세 (비유의) |
| T6 SST-5 (40) | 26/40 = 0.650 [0.495, 0.779] | 0.425 | 0.325 | 0.425 | english 15/6, 0.0784 (0.3134) | 비유의 (비유의) |
| T7 MASSIVE-10 (100) | 91/100 = 0.910 [0.838, 0.952] | 0.410 | 0.620 | 0.580 | multilingual 36/7, 9.0e-06 (6.3e-05) | Jev 우세 (Jev 우세) |
| T8 prompt-injections (40) | 31/40 = 0.775 [0.625, 0.877] | 0.775 | 0.575 | 0.725 | english 5/5, 1.0000 (1.0000) | 비유의 (비유의) |

출처: `results/F/jev_cmp/summary.md` §2.1. T1과 T7은 군집 때문에 item 단위 구간과 p가 낙관적이다(§4.2의 군집 bootstrap 참조).

![과제별 정확도: Jev vs Laya english vs Laya multilingual, Wilson 95% 구간](../results/F/jev_cmp/figs/accuracy_by_task.png)

**그림 1.** 과제별 정확도(막대)와 Wilson 95% 구간(가는 선). 오른쪽 주석은 최고 zero-shot Laya 러너 대비 exact McNemar 판정이고, Router는 표에만 있다(`results/F/jev_cmp/figs/accuracy_by_task.png`).

과제별로 보면 다음과 같다.

- **T1**: 타입별로 Jev는 choice 42/50, noul 56/60, score 6/10이고 Laya english는 14/50, 28/60, 4/10이다. english 대비 choice와 noul의 차이는 둘 다 b/c 31/3(p=7.7e-07)으로 유의하고, score 10개는 b/c 4/2(p=0.6875)로 구분되지 않는다. 설명을 뺀 같은 입력의 Laya noul도 english 31/60(b/c 27/2), multilingual 25/60(b/c 34/3)으로 차이가 그대로다. 이 120 decision의 문항별 최빈 기준선은 0.575이고 Laya base 세 러너 모두 그보다 낮다(`results/F/jev_cmp/summary.md` §2.2).
- **T5·T8 (Boolean)**: T5에서 AUROC는 Jev 0.988 [0.955, 1.000], Laya english 0.810 [0.662, 0.942]이고 차이 +0.177 [+0.043, +0.326]이다. Jev와 Laya 세 러너의 예측 true 수가 18\~21로 gold 20에 가까워, 격차는 임계값 위치보다 판별력 차이로 보인다. T8은 0.5 기준 정확도가 같지만(0.775) Jev는 이 40행에서 완전 분리(AUROC 1.000, 구간 퇴화)이고 오류 9개가 모두 미탐이다. Laya english AUROC는 0.929 [0.840, 0.997]이다(`results/F/jev_cmp/summary.md` §2.3).
- **T6 (score)**: 주 지표인 argmax 레벨 정확도는 0.650 vs 0.425로 비유의(p=0.0784)지만, 반올림 E[level] 정확도는 b/c 15/4, p=0.0192이고 MAE는 0.432 vs 0.888, 차이 −0.456 [−0.711, −0.207]이다. Laya english는 레벨 4를 한 번도 고르지 않았고 multilingual은 40행 모두 레벨 0·1을 냈다. 척도 압축이 Laya의 주된 실패다(`results/F/jev_cmp/summary.md` §2.4).

### 4.2 종합 (RQ1)

| 기준 | Jev 유의 우세 | 비유의 | Laya 유의 우세 |
|---|---|---|---|
| exact McNemar, 보정 전 α 0.05 | 4 (T1, T4, T5, T7) | 4 (T2, T3, T6, T8) | 0 |
| Holm 보정 (8개 검정) | 2 (T1, T7) | 6 | 0 |

| 비교 대상 | macro 정확도 | Jev − 대상 [과제 bootstrap 95%] | T1 제외 7과제 macro |
|---|---|---|---|
| Jev | 0.828 | - | 0.823 |
| Laya english | 0.646 | +0.182 [+0.041, +0.325] | 0.684 |
| Laya multilingual | 0.598 | +0.230 [+0.121, +0.339] | 0.631 |
| Laya Router | 0.661 | +0.167 [+0.044, +0.293] | 0.701 |
| 과제별 최고 Laya (사후 선택) | 0.675 | +0.153 [+0.031, +0.281] | 0.717 |

| 독립 단일 문항 240개 합산 | Jev 정답 | Laya 정답 | b / c | exact p |
|---|---|---|---|---|
| 과제별 최고 Laya | 194 | 176 | 39 / 21 | 0.0273 |
| english 고정 | 194 | 175 | 40 / 21 | 0.0204 |
| multilingual 고정 | 194 | 152 | 58 / 16 | 9.7e-07 |
| Router 고정 | 194 | 173 | 42 / 21 | 0.0111 |

군집 bootstrap(10,000회)에서 Jev − Laya는 T1 english +0.483 [+0.371, +0.597], T7 multilingual +0.290 [+0.100, +0.470], T7 english +0.500 [+0.370, +0.640]으로 모든 구간이 0을 포함하지 않는다(`results/F/jev_cmp/summary.md` §4). macro 차이는 이질적인 8과제를 평균한 기술통계이고, T1을 빼도 Jev가 앞선다.

### 4.3 보정과 확신도 (RQ2)

| 과제 | Jev Brier / ECE | 최고 Laya Brier / ECE | Jev 평균 top − 정확도 | Laya 평균 top − 정확도 |
|---|---|---|---|---|
| T1 | 0.237 / 0.181 | 0.724 / 0.205 | −0.134 | +0.152 |
| T2 | 0.220 / 0.118 | 0.053 / 0.083 | +0.102 | −0.045 |
| T3 | 0.537 / 0.278 | 0.429 / 0.174 | +0.201 | +0.150 |
| T4 | 0.114 / 0.069 | 0.478 / 0.262 | +0.048 | +0.082 |
| T5 | 0.098 / 0.103 | 0.393 / 0.190 | −0.012 | +0.172 |
| T6 | 0.502 / 0.184 | 0.770 / 0.239 | +0.101 | +0.229 |
| T7 | 0.140 / 0.068 | 0.584 / 0.216 | +0.037 | +0.212 |
| T8 | 0.307 / 0.194 | 0.401 / 0.223 | +0.146 | +0.187 |

Jev 확률은 소수 둘째 자리 반올림이라 Brier·ECE에 약 ±0.005의 하한 오차가 있다(`results/F/jev_cmp/summary.md` §5.1). Jev의 확신도는 문항 형식에 따라 성격이 달랐다.

| Jev 형식 | 과제 | n | 정확도 | 평균 top | 100% 표시 | 오답 중 top ≥ 0.90 |
|---|---|---|---|---|---|---|
| 단일 choice | T2·T3·T4·T7 | 220 | 0.868 | 0.949 | 144 (65%) | 17/29 (59%) |
| 단일 Boolean | T5·T8 | 80 | 0.850 | 0.917 | 0 (0%) | 2/12 (17%) |
| 단일 score | T6 | 40 | 0.650 | 0.751 | 0 (0%) | 0/14 (0%) |
| Multiple questions | T1 | 120 | 0.867 | 0.733 | 9 (8%) | 1/16 (6%) |

단일 choice에서는 100% 표시가 흔하고 오답의 다수가 0.90 이상이어서 top 확률 임계값으로 오답을 거르기 어렵다. T3에서는 정답 옵션을 0%로 표시한 행이 7/40이었다. Boolean은 100% 표시가 없지만 임계값의 적정 위치가 과제마다 다르다. T5는 0.5가 거의 최적이고 T8은 gold false의 p(true)가 모두 0.04 이하라, 같은 40행에서 임계값을 0.04 초과 0.08 이하로 두면 40/40이다(기술통계). 다문항 T1에서는 과소확신이고 낮은 top이 오답 신호가 된다. Laya 최고 러너는 형식별로 묶으면 모두 과대확신이다(단일 choice +0.130, Boolean +0.180, score +0.229, T1 +0.152; `results/F/jev_cmp/summary.md` §5.2\~§5.3). 결론적으로 두 시스템 모두 확신도 기반 자동화의 임계값은 과제(형식, 옵션 수, 언어)별 held-out 데이터로 다시 맞춰야 한다.

### 4.4 견고성 (RQ3)

- **결정성**: T2 10행을 같은 payload로 16\~23분 뒤 다시 보냈을 때 Jev는 라벨 10/10, 확률 벡터 9/10(최대 |Δp| 0.01), 토큰 수 10/10이 같았다. Laya english는 T1 200 decision 재실행 답이 완전히 같았다.
- **옵션 순서**: T2 20행을 Laya probe와 같은 순열 1개로 섞었을 때 flip은 Jev 0/20 [0.000, 0.161], Laya english·multilingual 모두 0/20이었다. 4옵션 고확신 행 위주라 정보량이 낮고, 제3자 공개 Jev flip 0.13도 배제하지 못한다(그 값에서 0/20이 나올 확률 0.062; `results/F/jev_cmp/summary.md` §6).
- **언어 간 일관성(T7)**: 옵션은 10개 영어 key로 고정하고 발화만 5개 언어로 바꿨다.

| system | en | de | ja | zh-CN | ko | 5개 언어 같은 라벨 | 언어쌍 평균 일치 | 평균 언어 페널티 |
|---|---|---|---|---|---|---|---|---|
| Jev | 0.900 | 0.900 | 0.950 | 0.900 | 0.900 | 18/20 | 0.935 | +0.012 |
| Laya english | 0.700 | 0.350 | 0.450 | 0.450 | 0.100 | 0/20 | 0.325 | −0.362 |
| Laya multilingual | 0.850 | 0.400 | 0.800 | 0.600 | 0.450 | 5/20 | 0.545 | −0.287 |
| Laya Router | 0.700 | 0.350 | 0.800 | 0.600 | 0.450 | 4/20 | 0.485 | −0.150 |

언어당 n=20이라 언어별 크기는 방향 신호다. Jev가 언어에 따라 라벨을 바꾼 id 2개는 번역 문장의 내용이 언어마다 달랐던 경우다(`results/F/jev_cmp/summary.md` §6.1).

![T7 언어별 정확도](../results/F/jev_cmp/figs/t7_languages.png)

**그림 2.** T7 MASSIVE intent-10의 언어별 정확도와 Wilson 95% 구간(같은 20 id, 옵션 10개 영어 key). 오른쪽 주석은 언어별 exact McNemar다(`results/F/jev_cmp/figs/t7_languages.png`).

### 4.5 지연과 비용 (RQ4)

두 값은 배포 형태가 다르다. Jev는 브라우저에서 플레이그라운드 서버를 거쳐 Jev로 가는 인터넷 왕복이고 Laya는 같은 M4 Pro 안의 in-process 호출과 localhost HTTP다. 아래 차이는 모델 속도 비교가 아니다.

| 경로 | 조건 | 1문항 중앙값 | 출처 |
|---|---|---|---|
| Jev 표시값 "server + network" | 410건 전체 | 226 ms (p5 184, p95 325.6) | `results/F/jev_cmp/summary.md` §7.1 |
| Jev 브라우저 POST 왕복 | 410건 전체 | 465 ms (p5 414, p95 616.2) | 같은 곳 |
| Laya in-process 연속 (multilingual) | MPS / CPU 10스레드 | 13.8 / 37.7 ms | `results/D/D_summary_20261003.md:42`, `:36` |
| Laya in-process 연속 (english) | MPS / CPU 10스레드 | 31.8 / 86.6 ms | `results/D/D_summary_20261003.md:40`, `:34` |
| Laya in-process 간헐 호출 1 s 간격 (multilingual) | MPS / CPU | 49.2 / 76.2 ms | `results/D/D_summary_20261003.md:89`, `:87` |
| Laya laya-serve HTTP 연속 (multilingual) | MPS / CPU | 20.3 / 50.7 ms | `results/D/D_summary_20261003.md:203`, `:222` |
| Laya PoC `/poc/decide` HTTP (ft-v1) | MPS, p50 | 20.1 ms | `results/poc/P2_20261003.md:67` |

Jev 표시값 중앙 226 ms는 제3자 공개 p50 236\~276 ms(`third_party/laya/README.md:1288`)보다 약간 낮고, 표시값에는 브라우저와 플레이그라운드 사이 구간(중앙 약 232 ms)이 빠져 있다. Jev 요청은 최소 12.1 s 간격(세션별 중앙 15.1 s 이상)이었으므로 Laya 쪽 대응 조건은 간헐 호출(multilingual MPS 49.2 ms, CPU 76.2 ms)이다.

![배포 형태별 지연, 로그 축](../results/F/jev_cmp/figs/latency.png)

**그림 3.** 배포 형태별 1문항 지연(로그 축). 점은 중앙값, 가는 선은 Jev 요청의 p5\~p95, 회색 띠는 제3자 공개 Jev p50 범위다(`results/F/jev_cmp/figs/latency.png`).

비용은 토큰 기록에서 계산했다. 490 decision의 토큰 합계는 입력 193,982, 출력 36,012이고 decision당 평균 469.4 토큰이다. upstream README가 인용한 단가 $0.042 / 1M tokens(`third_party/laya/README.md:1291`, 제3자 인용치, **단가 확인 필요**)를 적용하면 1,000 decision당 약 $0.0197이다(공식: 토큰 합계 ÷ decision 수 x 1,000 x $0.042 ÷ 1,000,000). 과제별로는 T1 $0.0131(다문항 요청이 state 토큰을 공유)부터 T7 $0.0292까지다. Laya의 한계 비용은 토큰 과금이 없는 로컬 연산이며, 단일 프로세스 laya-serve 1문항 처리량은 MPS 48.4 RPS, CPU 19.65 RPS로 1,000 decision에 각각 약 20.7 s, 50.9 s의 머신 시간이 든다(`results/F/jev_cmp/summary.md` §7.3). 전력과 장비 감가상각은 측정하지 않았다.

### 4.6 파인튜닝 참고선 (RQ5)

| 참고선 (zero-shot 아님) | 과제·표본 | Laya | Jev | 비교 |
|---|---|---|---|---|
| Laya typed-decisions (typed-decisions train으로 파인튜닝) | T1, 같은 120 decision | 104/120 = 0.867 | 104/120 = 0.867 | b/c 10/10, p=1.0 |
| Laya ft-v1 (한국어 domain_8 train 11,094행) | 한국어 도메인 라우팅 파일럿 24행 | 22/24 = 0.917 [0.742, 0.977] | 20/24 = 0.833 [0.641, 0.933] | b/c 0/2, p=0.5 |
| Laya ft-v1 | ko_massive_domain_8 test 절반 250행 | 0.900 [0.860, 0.936] (zero-shot 0.492) | 미측정 | - |

출처: `results/F/jev_cmp/summary.md` §3, `results/F/jev_playground_manual_20261006.md`, `results/P4/metrics/full_20261003-1156_summary.md`. 두 파인튜닝 선은 같은 분포의 학습 데이터를 쓴 in-domain 결과라 학습 데이터 없이 답하는 Jev와 조건이 다르다. ft-v1 학습은 M4 Pro MPS에서 3 epoch, 2,150 s(35.8분)가 걸렸다(`results/REPORT.md` §4). 파일럿에서 Jev가 ft-v1에 진 2행은 MASSIVE `play` 시나리오의 게임 실행 문장을 media로 묶는 관례 때문이었다. 이 관례는 라벨 설명에 없고, ft-v1은 학습 데이터에서 이를 배웠다(`results/F/jev_playground_manual_20261006.md` §4).

## 5. 사례 연구: 한국어 도메인 라우팅 PoC

본 비교에 앞서 같은 프로젝트에서 Laya를 한국어 도메인 라우터로 도입할 수 있는지 PoC를 수행했다(`results/REPORT.md`). 이 사례는 RQ5의 근거이자 운영 관점의 참고다.

- **zero-shot 한계**: MASSIVE ko의 시나리오를 8개 도메인으로 묶은 `ko_massive_domain_8`에서 multilingual zero-shot은 test 절반 0.492였다. 스키마 문구 변형 6종(dev에서 모두 v1 대비 −0.020\~−0.050), temperature 보정, 임계값 조정 어느 것으로도 0.6 선을 넘지 못했다(`results/REPORT.md` §0, §2).
- **파인튜닝**: MASSIVE ko train 11,094행(옵션 순서 셔플 증강)으로 학습한 ft-v1은 test 절반 0.900, 전체 test 2,917행 0.913, ECE 0.053, 옵션 순서 flip 0.037이었다. YNAT dev 정확도는 0.612에서 0.633으로 유지되어 망각이 보이지 않았다(`results/REPORT.md` §4).
- **Go/No-Go**: 사전에 정한 8개 게이트(G0\~G7) 중 zero-shot은 정확도(G1), coverage(G2), 옵션 순서(G4)에서 미달했다. ft-v1은 8개를 모두 통과했고(G2는 조건부), 판정은 "파인튜닝 파이프라인 전제의 Conditional Go"였다(`results/REPORT.md` §7).
- **서비스**: ft-v1을 올린 laya-serve 기반 라우터와 데모 UI가 수용 점검 11/11을 통과했고, 1문항 결정의 로컬 HTTP 왕복은 p50 20.1 ms, p95 21.1 ms였다(`results/REPORT.md` §5).
- **한국어 지원 감사**: 한국어는 Laya의 평가 언어이고(MASSIVE ko intent-20 multilingual 0.470, upstream 수치와 Δ 0.000으로 재현, `results/A/README.md`) mmBERT 사전학습의 high-resource 언어지만, 결정 학습 데이터에는 문서화되지 않았다. 토크나이저 UNK는 0이고 영어 대비 토큰이 1.5배다. 라틴 문자가 다수인 혼합문과 10음절 미만 한국어는 english로 라우팅되므로 `lang="ko"` 명시가 필요하다(`results/REPORT.md` §3, `docs/07_korean_support_audit.md` §1).

이 사례에서 zero-shot Laya는 Jev에 뒤졌지만(파일럿 0.417 vs 0.833, p=0.0020), 약 36분 학습한 ft-v1은 Jev와 구분되지 않으면서 수치상 앞섰고(0.917 vs 0.833, p=0.5000) 로컬 서빙의 지연·비용 이점을 유지했다.

## 6. 고찰

### 6.1 Jev가 앞서는 곳

Jev의 우위는 학습 분포 밖의 형식과 지시 따르기에서 크게 나타났다. typed-decisions(T1), key 단독 라벨의 Banking77-10(T4), BoolQ(T5), 다국어 의도(T7)가 그렇다. 5레벨 감성 척도(T6)는 주 지표인 argmax 정확도로는 비유의지만 MAE 차이의 구간이 0을 벗어난다. 특히 T5는 Laya 학습 믹스 과제인데도 순위 품질 자체가 달랐다(AUROC 0.988 vs 0.810). 학습 믹스로 나누면(§3.1) 유의 우세 4개 중 T1·T4·T7은 두 Laya 체크포인트가 학습하지 않은 데이터이고, Holm 보정 뒤에도 남는 T1·T7도 여기에 속한다. 학습 믹스 과제에서 Jev가 앞선 것은 T5 하나다. T7에서 Jev는 언어를 바꿔도 같은 결정을 냈고 Laya는 같은 id에서도 언어에 따라 결정이 갈렸다. 라벨 이름의 의미를 활용하는 능력, 다국어 표현의 정렬, 척도 전체를 쓰는 보정에서 차이가 난다고 해석할 수 있지만, Jev 내부를 알 수 없으므로 원인은 가설이다.

### 6.2 비슷한 곳

AG News(T2)는 Laya 쪽 방향(b/c 0/4)이지만 비유의이고 Laya 학습 믹스 과제다. Emotion(T3)은 b/c 2/4다. prompt-injections(T8)는 정확도가 같지만 오류 구조가 다르다. Jev는 역할·작업 지시형 주입 5개를 p(true) 0.17\~0.40으로 놓쳤고, Laya english는 명시적 무시·덮어쓰기 지시 5개를 놓쳤으며 그중 4개가 독일어 문장이었다(`results/F/jev_cmp/sessions/S5_20261007/S5_summary.md` §4.3). Laya가 같거나 앞선 과제는 이 셋뿐이고, 그중 학습 믹스 과제는 T2이며 T3·T8은 held out이다.

### 6.3 Laya의 레버

- **파인튜닝**: 두 참고선 모두 zero-shot 격차를 닫았다(§4.6). upstream의 자기 규정(fast base to specialise)과 일치한다.
- **러너 선택**: english와 multilingual의 차이가 과제마다 크고 방향도 바뀐다(T5 0.725 vs 0.600, T7 ja 0.450 vs 0.800). Router는 언어로만 고르므로 T7 de처럼 배정이 섞이고(multilingual 15, english 5) 정확도도 0.350에 그친다.
- **옵션 렌더링**: 같은 T4 40행에서 옵션 렌더링을 `key: key spaced`에서 key 단독으로 바꾸기만 해도 english는 0.825에서 0.725로(이전 렌더링에서만 정답 4행, key 단독에서만 정답 0행, p=0.1250), multilingual은 0.575에서 0.750으로(0행 / 7행, p=0.0156) 움직였다(`results/F/jev_cmp/laya_summary.md` §4b). 비교에서는 두 시스템에 같은 문자열을 넣어 통제했지만 배포에서는 렌더링도 검증 대상이다.
- **운영**: 로컬 실행, 지연, 토큰 과금 없음, 결정성, 데이터 외부 전송 없음.

### 6.4 타당성 위협

- **플레이그라운드 ≠ API**: 모델 버전 미표기, 확률 2자리 반올림, 서버 측 래핑 가능성, 표시 지연 정의 미공개.
- **소표본**: 과제당 n=40(Wilson 반폭 약 ±0.15), T7은 언어당 20(반폭 약 ±0.2)이다. 차이가 약 0.2보다 작으면 대부분 구분되지 않는다.
- **다중 비교**: Holm 보정 후에는 T1·T7만 유의하다. 보정 전 4/4/0은 탐색적 요약이다.
- **표본 쉬움**: seed 13 표본에서 T3 Jev 0.700 구간은 제3자 공개치 0.480을 포함하지 않고 Laya english 0.750도 upstream 0.573보다 높다. 짝 비교에는 유효하지만 공개치로 일반화하지 않는다.
- **T1 teacher**: 정답은 teacher 분포의 argmax이고 teacher와 Jev의 관계를 확인하지 못했다. Jev의 T1 0.867은 공개치 0.727(2,000 decision, 다른 문항 구성)보다 높아 teacher 정렬 효과를 배제할 수 없다.
- **다문항 공동 평가**: T1에서 Jev는 case의 2\~4문항을 한 요청에서 함께 평가했고 Laya는 질문마다 독립 평가했다.
- **학습 오염**: upstream 표기로 Laya 학습 믹스에 들어간 과제는 T2·T5뿐이고 나머지 여섯 과제는 held out이다(`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`). 이 표기는 upstream의 자기 보고이며 학습 데이터 자체는 확인하지 않았다. Jev의 학습 데이터는 알 수 없다.
- **러너 사후 선택**: 과제별 최고 Laya는 Laya에 유리한 선택이며, 고정 러너 기준 합산도 같은 방향이다(§4.2).
- **입력 표현 제약**: Boolean 설명 없음, Score 5레벨, choice 80자 때문에 T1은 120/200만 비교했고 T4는 key 단독으로 다시 만들었다.
- **파일럿 프로토콜 차이**: 한국어 파일럿은 state로 원문 발화를 넣었고, 질문 문장이 Laya와 약간 다르며, 옵션의 key와 설명을 문자열 하나로 넣었다(Laya는 따로 받는다). 그래서 8과제 종합에서 제외했다(`results/F/jev_playground_manual_20261006.md` §1.2, §5).

### 6.5 연구 중 발견한 upstream 결함과 불일치

`results/REPORT.md` §8에 기록한 7건이다. (1) `laya.calibrate.records_from_labeled`에 `@torch.no_grad()`가 없어 실제 Agent에서 예외가 난다. (2) `laya.evals.evaluate`가 `predict(..., model=)`을 호출해 `Agent.predict`와 호환되지 않는다. (3) `hf download`의 agent 모드 출력 접두어로 문서의 다운로드 명령이 깨진다(`--quiet` 필요). (4) 모델 카드의 한국어 0.490은 다른 실행(T4, n=300)의 값이고 공식 표는 0.470이다. (5) "multilingual의 criteria 없는 noul은 state를 읽는다"는 README 주장이 한국어와 그 영어 번역 모두에서 성립하지 않았다. (6) MASSIVE HF 미러의 license 태그(apache-2.0)가 원 저장소(CC BY 4.0)와 다르다. (7) examples 문서의 MPS 첫 호출 13 s는 이 머신에서 0.1 s였다.

## 7. 결론 및 향후 과제

같은 입력으로 비교하면, 학습 없이 바로 쓸 때의 정확도와 다국어 일관성은 Jev가 앞선다. Jev는 8개 과제 중 4개에서 유의하게 앞섰고(Holm 후 2개), 나머지 4개에서는 구분되지 않았으며, Laya가 유의하게 앞선 과제는 없었다. 반면 Laya는 같은 분포의 학습 데이터로 파인튜닝하면 Jev와 같은 정확도(T1)나 수치상 높은 정확도(한국어 파일럿, 비유의)에 도달했고, 로컬 실행으로 지연과 비용, 데이터 통제에서 구조적 이점을 가진다. 따라서 선택 기준은 "학습 데이터 없이 즉시 넓은 형식을 다뤄야 하는가"(Jev 유리)와 "과제별 라벨 데이터를 만들 수 있고 지연·비용·데이터 경계가 중요한가"(Laya 파인튜닝 유리)다. 어느 쪽이든 확신도 임계값은 과제별로 다시 맞춰야 한다.

향후 과제는 다음과 같다. (1) Jev 공식 API로 표본을 키운 동일 프로토콜 재측정과 확정 단가 기반 비용 비교. 한국어 라우팅에서 ft-v1과의 우열은 500행 규모 paired 비교가 있어야 판정된다(`results/REPORT.md` §8). (2) 언어와 과제 형식 확대(부정문, 고카디널리티, 장문 등 미실행 형식). (3) LLM zero-shot 베이스라인 추가. (4) 과제별 Laya 파인튜닝 곡선(라벨 수 대비 정확도)으로 몇 개의 라벨이면 Jev에 도달하는지 정량화. (5) T1 teacher의 정체와 Jev와의 관계 확인.

## 참고문헌

1. NandhaKishorM, *laya*: multilingual non-autoregressive System 1 decision engine. GitHub 저장소, 커밋 4aa6761(2026-10-01). README.md, BENCHMARKS.md 인용. [github.com/NandhaKishorM/laya](https://github.com/NandhaKishorM/laya)
2. TypeSafe AI, Jev(호스팅 결정 모델). 공식 문서 서지 확인 필요. 플레이그라운드는 "TypeSafe Jev"로만 표기하고 버전을 밝히지 않으며, upstream 비교표의 Jev 수치는 Jev 1.13.0 기준이다(`third_party/laya/README.md:1281`).
3. Jev Playground(독립 제3자 도구, TypeSafe AI와 무관). [jevplayground.com](https://jevplayground.com), 2026-10-02\~07 열람.
4. 제3자 Jev 벤치마크: AbdelStark/jev-benchmarks, nibzard/decision-model-benchmark. upstream `README.md:1268-1272`, `research/README.md:174-177` 경유 인용, 원문 확인 필요.
5. LocalLLaMA, *typed-decisions* 데이터셋. Hugging Face Hub, revision d0e2f0c. 저자·발표 정보 확인 필요.
6. X. Zhang, J. Zhao, Y. LeCun. Character-level Convolutional Networks for Text Classification. NeurIPS 2015(AG News). HF `fancyzhx/ag_news`.
7. E. Saravia et al. CARER: Contextualized Affect Representations for Emotion Recognition. EMNLP 2018(DAIR Emotion). HF `dair-ai/emotion`.
8. I. Casanueva et al. Efficient Intent Detection with Dual Sentence Encoders. NLP4ConvAI 2020(Banking77). HF `mteb/banking77`.
9. C. Clark et al. BoolQ: Exploring the Surprising Difficulty of Natural Yes/No Questions. NAACL 2019. HF `google/boolq`.
10. R. Socher et al. Recursive Deep Models for Semantic Compositionality Over a Sentiment Treebank. EMNLP 2013(SST-5). HF `SetFit/sst5`.
11. J. FitzGerald et al. MASSIVE: A 1M-Example Multilingual Natural Language Understanding Dataset with 51 Typologically-Diverse Languages. ACL 2023(게재 정보 확인 필요). HF `mteb/amazon_massive_intent`.
12. deepset, *prompt-injections* 데이터셋. Hugging Face Hub, revision 4f61ecb. 서지 확인 필요.
13. M. Marone, O. Weller, W. Fleshman, E. Yang, D. Lawrie, B. Van Durme. mmBERT: A Modern Multilingual Encoder with Annealed Language Learning. arXiv:2509.06888, 2025.
14. Q. McNemar. Note on the sampling error of the difference between correlated proportions or percentages. Psychometrika, 1947.
15. S. Holm. A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics, 1979.
16. E. B. Wilson. Probable inference, the law of succession, and statistical inference. JASA, 1927.

## 부록 A. 재현

```bash
source env.sh
# 세트 빌드와 Laya 측정 (Jev 요청 없음)
export HF_HOME=$PWD/data/raw/hf && .venv/bin/python scripts/build_jev_cmp_sets.py all
bash results/F/jev_cmp/run_laya.sh && .venv/bin/python results/F/jev_cmp/laya_summary.py
# 기록된 Jev 세션 분석 (사이트 요청 없음, jsonl만 읽음)
.venv/bin/python results/F/jev_cmp/jev_cmp.py t1 S1,S2
.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S1 T2_ag_news_40
.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S3 T5_boolq_40
.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S4,S5 T7_massive_intent_10opt_en_20,T7_massive_intent_10opt_de_20,T7_massive_intent_10opt_ja_20,T7_massive_intent_10opt_zh-CN_20,T7_massive_intent_10opt_ko_20
# S6 종합과 대조
.venv/bin/python results/F/jev_cmp/s6_summary.py build
.venv/bin/python results/F/jev_cmp/s6_summary.py verify
```

Jev 세션 자체는 플레이그라운드 UI를 브라우저로 조작해 수행했고, 절차는 각 세션의 run card(`results/F/jev_cmp/sessions/S*/S*_run_card.md`)와 기록 도구(`jev_cmp.py record`, S2\~S5는 세션 폴더의 `s*_prep.py`, `s*_record.py`)에 남아 있다. 전체 명령 목록은 `results/F/jev_cmp/summary.md` §10이다.

## 부록 B. 과제별 상세

**T1 workflow별 정확도** (`results/F/jev_cmp/sessions/S2_20261007/S2_summary.md` §2.4)

| workflow | 비교 decision | Jev | Laya english | 참고: Laya typed-decisions |
|---|---|---|---|---|
| agent_trace_observability | 30 | 25/30 = 0.833 | 14/30 = 0.467 | 24/30 |
| customer_service | 20 | 19/20 = 0.950 | 11/20 = 0.550 | 18/20 |
| invoice_processing | 30 | 29/30 = 0.967 | 4/30 = 0.133 | 27/30 |
| security_incidents | 40 | 31/40 = 0.775 | 17/40 = 0.425 | 35/40 |

Laya base는 invoice_processing의 duplicate 질문에서 0/10, matches_order에서 2/10이었다.

**T6 예측 레벨 분포** (argmax, gold는 레벨마다 8행; `results/F/jev_cmp/summary.md` §2.4)

| system | 레벨 0 / 1 / 2 / 3 / 4 | 평균 E − gold | ±1 레벨 이내 |
|---|---|---|---|
| Jev | 4 / 13 / 6 / 12 / 5 | −0.014 | 0.875 |
| Laya english | 10 / 15 / 10 / 5 / 0 | −0.687 | 0.650 |
| Laya multilingual | 11 / 29 / 0 / 0 / 0 | −1.280 | 0.400 |

**T7 언어별 McNemar (Jev vs Laya multilingual, b/c, p)** (`results/F/jev_cmp/summary.md` §2.5)

| en | de | ja | zh-CN | ko |
|---|---|---|---|---|
| 3/2, 1.0000 | 11/1, 0.0063 | 3/0, 0.2500 | 8/2, 0.1094 | 11/2, 0.0225 |

**T5·T8 Boolean 세부** (`results/F/jev_cmp/summary.md` §2.3)

| 과제 | system | 예측 true (gold 20) | FN / FP | AUROC |
|---|---|---|---|---|
| T5 | Jev | 21 | 1 / 2 | 0.988 |
| T5 | Laya english | 19 | 6 / 5 | 0.810 |
| T8 | Jev | 11 | 9 / 0 | 1.000 (구간 퇴화) |
| T8 | Laya english | 11 | 9 / 0 | 0.929 |

## 부록 C. 요청 로그 요약

| 항목 | 값 |
|---|---|
| 총 요청 | 438 = 마스터 로그 411(S1 41, S1b 30, S2 80, S3 80, S4 80, S5 100) + 도구화 이전 27(파일럿 25, 상태 확인 2) |
| 일자별 | 2026-10-06 98, 2026-10-07 340 |
| 오류 | HTTP 502 2회(파일럿 1회 중단 후 재개, S2 1회 73.7 s 뒤 재시도 성공), 429·제한 문구·captcha 0회 |
| 입력 대조 | 요청 body = 폼 payload 411/411, 화면 = 응답 410/410, Model ID `typesafe-ai/jev` 410/410 |
| 간격 | 최소 12.1 s(S2), 세션별 중앙 15.1\~17.5 s, 규칙 ≥ 10 s |
| 로그 | `results/F/jev_cmp/jev_runs_all.jsonl`, 세션별 `S*_requests.jsonl`, 파일럿 `results/F/jev_runs_raw.jsonl`(세 로그 모두 공개 저장소에는 포함하지 않음) |

출처: `results/F/jev_cmp/summary.md` §1.

## 부록 D. 08 문서와의 관계

`docs/08_paper_ko.md`는 같은 프로젝트의 앞선 보고서로, 질문을 "Laya를 한국어 서비스에 쓸 수 있는가"로 두고 한국어 적용성(재현, 한국어 지원 감사, zero-shot 품질, 파인튜닝, PoC)을 다뤘다. 그 문서의 Jev 비교는 n=24 한국어 파일럿 하나였다(08 §4.8). Laya와 Jev의 성능 비교라는 질문에 대해서는 본 문서가 08을 대체하며, 08의 한국어 결과는 본 문서 §5의 사례 연구로 요약해 포함했다.

[English](10_paper_laya_vs_jev_v2.md) | **한국어**
