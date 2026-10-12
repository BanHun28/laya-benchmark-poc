# Jev, vanilla Laya, trained Laya의 3-arm 통제 비교: 비자동회귀 결정 엔진의 zero-shot 정확도와 과제별 파인튜닝 효과

**작성** 2026-10-07(v2), 개정 2026-10-09(v3, 3-arm 확장) · **환경** Apple M4 Pro(10P+4E CPU, 20코어 GPU/MPS, 48 GB), macOS 26.6.2, Python 3.12.12, torch 2.14.1, transformers 5.18.0(`results/env/env_20261002-1333.json`, 3-arm 학습은 `results/env/env_20261008-0940.json`) · **Laya** 0.3.23(upstream 커밋 4aa6761), 체크포인트 번들 `convaiinnovations/laya` @ 55cf4c4, 품질 측정은 CPU fp32 · **trained Laya** 과제별 파인튜닝 10개, M4 Pro MPS fp32, 본 학습 run 1은 2026-10-08 10:57\~15:01, 드라이버 STEP FAILED 0(`results/T3arm/run_all_status.log`). 반복 학습 run 2(seed 14)는 10과제 완료(2026-10-09 00:23, `results/T3arm/rep_s14/run_all_status.log`) · **Jev** 독립 제3자 공개 플레이그라운드 jevplayground.com 경유(T1\~T8은 2026-10-06\~07, T9·T10은 2026-10-08 세션 S7), Model ID `typesafe-ai/jev`(버전 미표기) · **근거 파일** zero-shot 축은 `results/F/jev_cmp/summary.md`, `summary.json`(S6 종합, 세션 요약 대조 수치 불일치 0건, `results/F/jev_cmp/S6_20261007.md:45`)과 `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md`, 3-arm 축은 `results/T3arm/summary.md`, `summary.json`(S3 종합, 2026-10-09 00:23 빌드, 공개용으로 2026-10-12 재빌드: 그림 영어 문구, 공개 주석, Jev 항목별 필드 제거, 수치 동일, `results/T3arm/summary.md:1`. `t3arm_summary.py verify` 불일치 0건) · **이전 판** v2(zero-shot 비교)는 `docs/10_paper_laya_vs_jev_v2.md`(영어)와 `docs/10_paper_laya_vs_jev_v2.ko.md`(한국어, 공개용 수정 반영)에 보존. PDF는 공개 저장소에는 포함하지 않음

## 초록

Laya는 encoder 한 번의 forward pass로 typed decision(choice, score, noul)의 확률 분포를 내는 오픈소스 비자동회귀 결정 엔진이고, Jev는 같은 형식의 결정을 호스팅 API로 제공하는 상용 모델이다. upstream은 두 시스템을 제3자가 서로 다른 표본으로 잰 공개 수치로만 비교해 왔고, Laya base 체크포인트를 zero-shot 엔진이 아니라 과제별로 전문화할 base로 규정한다. 본 연구는 같은 state 바이트, 같은 질문 문장, 같은 옵션 문자열을 세 arm에 넣는 통제 비교를 수행했다. 세 arm은 Jev(zero-shot, 공개 플레이그라운드), vanilla Laya(학습 없는 base), trained Laya(같은 base를 과제 라벨로 과제마다 파인튜닝)다. 과제는 10개이고, upstream이 밝힌 Laya 학습 믹스에 들어 있는 4개(포함 범주)와 없는 6개(제외 범주)로 나눴다. Jev는 v2에서 8개 과제를 438회 호출로 쟀고(요청 body와 사전 생성 payload의 바이트 일치 411/411), 3-arm 확장에서 T9·T10을 같은 규칙의 80회 호출로 더 쟀다(바이트 일치 80/80, 사이트 누적 518회).

zero-shot 축에서 Jev는 T1\~T8 중 4개 과제에서 exact McNemar로 유의하게 앞섰고(Holm 후 T1, T7의 2개) Laya가 유의하게 앞선 과제는 없었다. T9는 Jev와 vanilla가 모두 40/40이고, T10은 Jev 0.250, vanilla english 0.300, multilingual 0.450으로 모두 비유의다. T1\~T8 macro 정확도는 Jev 0.828, Laya english 0.646, multilingual 0.598, Router 0.661이다. trained는 과제당 라벨 약 6,400개(train 최대 5,000 items x 2 epoch)와 M4 Pro MPS 학습 7.5\~43.3분(T8 1.4분)으로 만들었다. 본 학습 run 1에서 trained vs Jev는 10과제 모두 Holm 보정 후 유의차가 없었고, 보정 전에는 T3(0.950 대 0.700)와 T8(0.975 대 0.775)에서 trained가 유의하게 앞섰다. zero-shot에서 Jev가 Holm 후에도 앞섰던 두 과제 중 T7은 0.910으로 같아졌고, T1은 0.792 대 0.867로 군집 bootstrap 구간이 0을 포함한다. seed만 바꾼 반복 run 2도 10과제를 마쳤다. 두 run을 함께 보면 Holm 보정 후 Jev가 trained보다 유의하게 앞선 비교는 없다. 보정 전 기준으로는 run 2의 T5에서 Jev가 유의하게 앞섰지만(b/c 1/10, p=0.0117), Holm 보정 후에는 0.1055로 비유의다. 확장 세트(ext)의 trained vs vanilla는 10과제 모두 두 run의 판정이 같다. 학습 제외 6과제와 T10의 trained 우세는 두 run 모두 Holm 보정 후 유의했고, 포함 과제 T2·T5·T9는 두 run 모두 비유의였다. 30개 비교(10과제 x 3종) 가운데 27개는 두 run의 판정이 같아 확정됐고 3개는 불일치했다. 불일치는 모두 n=40 Jev 항목 비교이고 Holm p가 0.05 근처다(T4 trained vs vanilla는 run 1만 유의, T8 trained vs Jev와 T8 trained vs vanilla는 run 2만 trained 유의 우세). ext의 범주 평균은 run 1에서 포함 +0.017, 제외 +0.252, difference-in-differences +0.235 [+0.147, +0.316]이고 run 2에서 +0.020, +0.257, +0.238 [+0.144, +0.325]라, 학습 이득은 upstream이 학습하지 않은 과제에 몰린다. temperature만 다시 맞춘 보정 분리 열로 보면, ext에서 trained의 ECE 개선은 T1·T3·T6·T10에서 사실상 refit 효과이고 T4·T8에서는 학습 효과다. 학습 검증 V1\~V6은 모두 통과했다(V3는 차이 기준, 프로젝트 책임자 판정). 같은 설정의 T1 재학습은 MPS 비결정성 때문에 test 정확도 0.747 대 0.690을 냈고, seed 14 반복 run은 0.735여서 본 학습 run 1의 0.690이 세 run 중 이탈값이다. 로컬 Laya의 1문항 지연(13.8\~86.6 ms)은 Jev 인터넷 왕복(브라우저 POST 중앙 465 ms)보다 짧았지만, 배포 형태가 달라 모델 속도 비교는 아니다.

- zero-shot 정확도: T1\~T8에서 Jev 유의 우세 4 / 비유의 4 / Laya 유의 우세 0(Holm 후 2 / 6 / 0). 독립 단일 문항 240개 합산 exact McNemar는 Jev 194 vs 과제별 최고 Laya 176, b/c 39/21, p=0.0273. macro 차이는 Jev − Router +0.167 [+0.044, +0.293](과제 bootstrap, 기술통계). S7의 T9·T10은 둘 다 비유의다.
- 3-arm 정확도(두 run 기준): Holm 보정 후 trained vs Jev는 run 1에서 trained 유의 우세 0 / 비유의 10 / Jev 유의 우세 0, run 2에서 1(T8) / 9 / 0이다. 보정 전에는 run 2의 T5만 Jev 유의 우세다(Holm 보정 후 0.1055로 비유의). ext의 trained vs vanilla는 10과제 모두 두 run의 판정이 같다(학습 제외 6과제와 T10은 유의, T2·T5·T9는 비유의). 30개 비교 중 확정 27, 불일치 3.
- 범주(Q1): ext의 trained − vanilla DiD +0.235 [+0.147, +0.316]. Jev 항목의 Jev − vanilla DiD는 +0.179 [−0.008, +0.356]으로 방향은 같지만 구간이 0을 포함한다.
- 다국어 일관성: zero-shot T7에서 Jev 평균 언어 페널티 +0.012, Laya english −0.362, multilingual −0.287. trained는 5개 언어 모두 0.850\~0.950이다.
- 보정: Jev 확률의 의미는 문항 형식마다 다르다(단일 choice는 오답의 59%가 top ≥ 0.90, 다문항 T1은 과소확신, T10은 ECE 0.623). ext에서 trained의 ECE 개선은 T1·T3·T6·T10에서 사실상 temperature refit이고 T4·T8에서는 학습 효과다. Brier 개선은 대부분 학습 쪽이다.
- 비용과 검증: 과제당 라벨 약 6,400개, 학습 7.5\~43.3분, 체크포인트 0.85 GB(multilingual 0.68 GB). V2에서 upstream 체크포인트는 공개치 0.766을 재현했고, 같은 파이프라인의 T1 세 run은 0.747 / 0.690 / 0.735였다.
- T10 라벨: Jev, vanilla english, vanilla multilingual, trained가 모두 틀린 행이 18/40이라 gold 라벨 품질이 의심된다(수작업 확인 필요).
- 파인튜닝 참고선: T1에서 Laya typed-decisions 체크포인트 104/120 = Jev 104/120, 한국어 도메인 라우팅에서 Laya ft-v1 22/24 vs Jev 20/24.

## 1. 서론

### 1.1 동기

Laya upstream README는 "Laya (with routing) vs Jev" 표에서 typed-decisions 0.766 vs 0.727, AG News 0.950 vs 0.910, DAIR Emotion 0.595 vs 0.480, Banking77 0.425 vs 0.870, p50 지연 32.8 ms vs 236\~276 ms를 제시한다(`third_party/laya/README.md:1274-1291`; `third_party/laya/`(공개 저장소에는 포함하지 않음)는 https://github.com/NandhaKishorM/laya 를 커밋 4aa6761로 clone해 재현한다). 그러나 같은 문서와 BENCHMARKS.md는 Jev 수치가 "third-party published, never measured here"이고 표본과 프롬프트가 다르다고 명시한다(`third_party/laya/README.md:1276-1278`, `third_party/laya/BENCHMARKS.md:3`). 즉 두 시스템을 같은 입력으로 잰 통제 비교는 존재하지 않았다. 표본, 질문 문장, 옵션 렌더링이 다르면 정확도 차이를 시스템 차이로 읽을 수 없다.

v2(2026-10-07)는 이 공백을 zero-shot 통제 비교로 메웠고 Jev의 우위를 확인했다. 그러나 두 질문이 남았다. 첫째, upstream은 base 체크포인트를 "a fast base to specialise, not as a zero-shot decision engine"이라고 규정한다(`third_party/laya/README.md:1530`). 그러므로 배포 판단에는 과제별로 전문화한 Laya와의 비교가 필요하다. v2의 파인튜닝 근거는 T1의 upstream 체크포인트와 한국어 ft-v1 두 참고선뿐이었다. 둘째, vanilla Laya의 열세에는 학습 때 본 과제의 유지(retention)와 처음 보는 과제의 일반화가 섞여 있다. v3는 같은 base를 과제 데이터로 파인튜닝한 trained arm을 10개 과제 모두에 더하고, 과제를 Laya 학습 믹스 기준 범주로 나눠 두 요인을 구분한다(`docs/11_three_arm_plan.md` §1, §2).

### 1.2 연구 질문

zero-shot 축(v2와 같음):

- RQ1. 같은 입력에서 zero-shot 정확도는 어떻게 다른가?
- RQ2. 두 시스템의 확률은 보정되어 있고, 확신도로 자동 처리 여부를 가를 수 있는가?
- RQ3. 결정성, 옵션 순서, 언어를 바꿨을 때 결정은 얼마나 안정적인가?
- RQ4. 지연과 비용은 어떤 구조로 다른가?

3-arm 축(v3 추가, 괄호는 `docs/11_three_arm_plan.md` §1의 질문 번호):

- RQ5. 과제 데이터로 파인튜닝한 Laya(trained)는 Jev에 도달하거나 넘어서는가(Q2)? v2의 RQ5("Laya의 zero-shot 열세는 파인튜닝으로 닫히는가")를 모든 과제의 trained arm으로 넓혔다.
- RQ6. vanilla Laya의 Jev 대비 열세와 학습 이득은 Laya 학습 믹스에 포함된 과제와 제외된 과제에서 다른가(Q1)?
- RQ7. 전문화 비용(라벨 수, 학습 시간, 체크포인트 크기)은 얼마인가(Q3)?
- RQ8. Laya가 제대로 학습되었는가(Q4)?

### 1.3 기여

(1) 8개 과제, 8개 공개 데이터셋, 5개 언어에서 입력 바이트를 맞춘 Laya vs Jev 통제 비교. upstream 문서와 그것이 인용한 제3자 벤치마크에는 이런 비교가 없다. (2) 같은 base와 같은 평가 경로로 맞춘 vanilla와 trained를 더한 3-arm 설계. 학습 믹스 포함 과제 T9·T10을 더한 10개 과제를 Laya 학습 믹스 기준 범주로 나눠 retention과 일반화를 구분하고, Jev 항목과 확장 세트(ext)의 두 층으로 평가했다. (3) 재현 가능한 하네스: 과제별 플레이그라운드 폼 파일, 클릭 전 payload 해시와 클릭 후 요청 body 바이트 대조, 마스터 요청 로그 491건(v2 411건 + S7 80건), 학습 시작 게이트(sha256)와 단계별 상태 로그. (4) 학습 검증 V1\~V6(zero-step identity, upstream 재현, label-shuffle, 형식 동일성, smoke, 누수), 같은 설정 재학습 편차와 seed 반복의 정량화, temperature refit과 학습 효과를 나눈 보정 분리. (5) 다중 비교 보정(Holm), 과제 bootstrap, 독립 항목 합산 McNemar, 군집 bootstrap, 범주 difference-in-differences를 함께 쓴 통계 처리. (6) 문항 형식별 확신도 분석과 자동화 임계값에 대한 함의. (7) 파인튜닝 참고선과 한국어 도메인 라우팅 PoC 사례. (8) 연구 중 발견한 upstream 결함과 문서 불일치 7건.

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

표본은 공개 split에서 seed 13으로 결정적으로 뽑았다. 단일 문항 과제는 중복·길이 규칙을 적용한 뒤 레이블로 층화했고, T1은 workflow로 층화했으며, T7은 5개 언어에 모두 있는 첫 20개 test id를 쓰고 오답 옵션 9개를 seed로 뽑았다(`data/evals/jev_cmp/MANIFEST.json`, `scripts/build_jev_cmp_sets.py`). T9·T10은 같은 빌더에 더한 과제로, 라벨 층화 40행이다(`results/T3arm/PREP_20261008.md` §1).

| 과제 | 소스 @revision | split | n | 형식 / 옵션 | 범주 (Laya 학습 믹스) |
|---|---|---|---|---|---|
| T1 typed-decisions | `LocalLLaMA/typed-decisions` all @d0e2f0c | test | 40 case, 비교 가능 decision 120 | Multiple questions: choice 50, Boolean 60, 5레벨 score 10 | 제외 (no) |
| T2 AG News | `fancyzhx/ag_news` @eb185aa | test | 40 | choice 4 | 포함 (yes) |
| T3 DAIR Emotion | `dair-ai/emotion` split @cab853a | test | 40 | choice 6 | 제외 (no) |
| T4 Banking77-10 | `mteb/banking77` @18072d2 | test | 40 | choice 10(정답 + 오답 9, key-only 렌더링) | 제외 (held out) |
| T5 BoolQ | `google/boolq` @35b264d | validation | 40 | Boolean | 포함 (yes) |
| T6 SST-5 | `SetFit/sst5` @e51bdcd | test | 40 | score 5레벨 | 제외 (no) |
| T7 MASSIVE intent-10 | `mteb/amazon_massive_intent` en·de·ja·zh-CN·ko @940fd47 | test | 같은 20 id x 5개 언어 = 100 | choice 10(영어 key, 정답 + 오답 9, upstream 20옵션에서 축소) | 제외 (held out) |
| T8 prompt-injections | `deepset/prompt-injections` @4f61ecb | test | 40 | Boolean | 제외 (no) |
| T9 Enron spam | `SetFit/enron_spam` @1916f66 | test | 40 | Boolean(criteria 없음) | 포함 (yes) |
| T10 support tickets | `Tobi-Bueck/customer-support-tickets` @ddf1c81 | train의 hash test 몫 | 40 | choice 10(큐 10개, upstream 큐 설명) | 포함 (yes) |

학습 믹스는 MANIFEST의 `in_training_mix`다. upstream은 T1\~T8 가운데 AG News(T2)와 BoolQ(T5)만 Laya 학습 믹스에 넣었고(일반화가 아니라 retention), Emotion·prompt-injections·Banking77·SST-5는 held out, typed-decisions·MASSIVE는 두 체크포인트 모두 학습하지 않았다고 적는다(`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`, `results/F/jev_cmp/summary.md` §2.1). 3-arm 확장에서 더한 T9·T10은 upstream Themes 벤치마크가 in training으로 표기한 과제다(`third_party/laya/BENCHMARKS.md:142`, `:147`). 표의 no와 held out은 모두 학습 믹스에 없다는 뜻이고, 이 표기로 포함 범주(T2, T5, T9, T10)와 제외 범주(T1, T3, T4, T6, T7, T8)를 나눈다(§3.5). Jev의 학습 데이터는 알 수 없고 모든 소스가 공개 데이터셋이다.

T9·T10의 문구는 upstream Themes 벤치마크를 그대로 따른다. T9의 state는 `laya.email_state(subject, message[:3000])`이고 질문은 "Is this email unsolicited spam or bulk marketing?"이다(`third_party/laya/research/scripts/bench_apps.py:159-168`). T10은 language가 en이고 10개 큐에 속하며 body가 있는 행이다. state는 subject와 body[:3000], 질문은 "Which support queue should handle this ticket?", criteria는 upstream의 큐 설명 10개다(`bench_apps.py:130-155`). T10은 공개 split이 train 하나뿐이다. 그래서 정규화 state 텍스트의 sha256을 10으로 나눈 나머지로 test(0\~1), dev(2), train(3\~9) 몫을 나눴고, 같은 텍스트는 항상 같은 몫에 들어가 몫 사이 중복이 0이다(`results/T3arm/PREP_20261008.md` §1). 두 과제의 Jev 측정은 세션 S7에서 했다(§3.3).

### 3.2 입력 동일성

- **state**: Laya가 실제로 읽는 JSON 직렬화 문자열(`state_text`)을 Jev의 State 칸에 그대로 넣었다. 질문 문장은 upstream 벤치마크 스크립트의 문장을, T1은 데이터셋 자체 질문을 그대로 썼다(MANIFEST `question_source`).
- **옵션**: choice는 Laya가 실제로 렌더링하는 옵션 문자열(과제에 따라 `key: 설명` 또는 key 단독)을 같은 순서로 넣었다. 플레이그라운드의 80자 제한 때문에 T4는 upstream 방식의 key 단독 렌더링으로 두 시스템 모두 다시 만들었다(이전 렌더링은 `_v0`로 보관). T1에서 80자를 넘는 옵션을 가진 decision 10개는 비교에서 뺐다.
- **Score**: 플레이그라운드가 5레벨만 받으므로 T1의 4레벨 score 70개를 뺐다. 그 결과 T1의 비교 대상은 200개 중 120개다.
- **Boolean**: Jev Boolean에는 설명 칸이 없다. 공정성 점검으로 Laya에서 noul의 true/false 설명(criteria)을 뺀 변형을 따로 쟀고 정확도 변화는 유의하지 않았다(english 0.467 → 0.517, p=0.549; `results/F/jev_cmp/laya_summary.md` §2b). T5·T8의 noul은 원래 criteria가 없다.
- **검증**: 매 요청 전에 폼 파일로 만든 payload의 해시를 대조하고, 요청 후 실제 body를 바이트 단위로 대조했다(411/411 일치). 화면 표시와 응답 JSON도 410/410 일치했다(`results/F/jev_cmp/summary.md` §1).
- **3-arm**: vanilla와 trained는 Jev 형식 세트를 같은 파일로 평가한다. 학습 item도 같은 행 빌더로 만들어 질문 문구, criteria, 옵션 렌더링, state 직렬화가 평가와 같다(§3.6, V4).

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
| S7 | 2026-10-08 15:22\~15:43 | T9 40 + T10 40 (3-arm 확장) | 80 | 15.0 s |

사이트 상태 확인 2회를 더해 총 438회다(`results/F/jev_cmp/summary.md` §1). 운영 규칙은 클릭 간격 10초 이상, 5xx는 60초 뒤 1회 재시도, 429·제한 문구·captcha는 즉시 중단이었다. 처음에는 하루 요청 수에 자체 상한을 두었다. 사이트가 수치 한도를 공개하지 않고 해제 전 178회 동안 429와 제한 문구가 0회였으므로, 2026-10-07 프로젝트 책임자 결정으로 상한을 해제하고 간격·중단 규칙은 유지했다. 해제 뒤 S3\~S5 260회를 포함해 그날 340회 동안 429, 제한 문구, captcha는 나오지 않았다(`docs/09_laya_vs_jev_plan.md:48`). T1의 row 30은 S1 탐색 요청의 payload가 본 실행과 같아 재사용했다.

3-arm 확장에서 T1\~T8은 이 기록을 그대로 쓰고, T9·T10은 프로젝트 책임자 승인(`results/T3arm/PREP_20261008.md` "프로젝트 책임자 결정" 5번)에 따라 세션 S7에서 같은 운영 규칙(클릭 간격 10초 이상, 실제 가드 15 s, 5xx는 65 s 뒤 1회 재시도, 429·제한 문구·captcha는 즉시 중단)으로 80회 요청해 쟀다. 80회 모두 HTTP 200이었고 5xx, 429, 제한 문구, captcha는 0건이었으며 재시도도 없었다. 요청 body는 폼 payload와 80/80 바이트 일치했고 Model ID는 `typesafe-ai/jev` 80/80이다. 최소 간격은 15.009 s다. 사이트 누적 요청은 518회(438 + 80), 마스터 로그는 491줄이다(`results/F/jev_cmp/sessions/S7_20261008/S7_run_card.md`, `S7_summary.md` §1).

### 3.4 Laya 측정

Laya는 Jev 폼을 만든 것과 같은 세트 파일(laya-evals JSONL)로 CPU fp32(intra-op 10, inter-op 1), batch 8에서 english, multilingual, Router 세 러너를 모두 쟀다(`results/F/jev_cmp/run_laya.sh`, `results/F/jev_cmp/S0_20261006.md`). T1에는 upstream 파인튜닝 체크포인트 typed-decisions를 참고선으로 추가했다. T1 english를 다시 실행한 답이 200/200 같아 결정적임을 확인했다(`results/F/jev_cmp/laya_summary.md` §5). 3-arm의 vanilla와 trained도 같은 평가 경로(CPU fp32, intra-op 10 / inter-op 1, batch 8)를 쓴다. 이 경로로 v2의 english·multilingual 리포트 28개(1,280 decision)를 다시 돌린 답은 바이트 단위로 같았다(max |Δp| 0, `results/T3arm/PREP_20261008.md` §5).

### 3.5 3-arm 설계와 범주

**arm 정의.**

- **Jev**: §3.3의 플레이그라운드 기록(`results/F/jev_cmp/jev_runs_all.jsonl`(공개 저장소에는 포함하지 않음), T1\~T8은 v2 세션, T9·T10은 S7)을 그대로 쓴다.
- **vanilla Laya**: trained와 같은 base를 학습 없이 쓴다. base는 Router가 고르는 체크포인트로, 영어 과제는 english, T7은 multilingual이다(프로젝트 책임자 결정, `docs/11_three_arm_plan.md` §1). base를 맞춰야 trained − vanilla가 학습 효과가 된다. T1\~T8의 vanilla는 §4의 english 열(T7은 multilingual 열)과 같다.
- **trained Laya**: 과제마다 base 하나를 그 과제 라벨로 따로 파인튜닝한다. T7은 5개 언어를 함께 학습한 multilingual 모델 하나다. 라벨을 쓰므로 zero-shot 비교가 아니라 전문화 비교이고, 라벨 수와 학습 시간을 함께 보고한다(§5.5). 본 학습 run 1(torch seed 13)이 주 결과이고, seed만 14로 바꾼 반복 학습 run 2도 10과제를 마쳤다(§5.7).
- **보정 분리 열(vanilla + 과제 T)**: base 가중치를 그대로 두고 그 과제의 calib로 temperature만 다시 맞춘 0-step export다(V1과 같은 절차, `results/T3arm/calib_sep/<task>/`). 답은 vanilla와 같고 확률만 달라 보정 지표에만 쓴다(§5.4). 네 번째 arm이 아니라 trained의 보정 개선을 refit 효과와 학습 효과로 나누는 기준선이다.

**범주와 3x2 설계.** 범주는 upstream이 밝힌 Laya 학습 믹스 기준이다(§3.1). 범주는 Laya 기준으로만 정의되며, Jev가 같은 공개 데이터셋을 학습했는지는 알 수 없다.

| arm / 범주 | 학습 믹스 포함 (T2, T5, T9, T10) | 학습 믹스 제외 (T1, T3, T4, T6, T7, T8) |
|---|---|---|
| Jev (zero-shot, 플레이그라운드) | 측정(T9·T10은 S7) | 측정 |
| vanilla Laya (zero-shot) | 측정 | 측정 |
| trained Laya (과제별 파인튜닝) | 측정 | 측정 |

**평가 층.**

| 층 | 용도 | 구성 |
|---|---|---|
| Jev 항목 | 3-arm 직접 비교(Jev와 같은 바이트의 입력) | §3.1의 세트. 과제당 40, T1은 40 case(Jev 비교 120 decision, Laya arm 전체 200), T7은 20 id x 5개 언어 = 100 |
| 확장 세트(ext) | vanilla vs trained의 좁은 구간(Jev 없음) | T2\~T6·T9·T10 각 500(평가 split에서 층화, seed 13, 학습 행과 겹침 제외), T1 test 전체 400 case = 2,000 decision, T7 100 id x 5개 언어 = 500, T8 test 전체 116 |

ext의 평가 split은 대부분 test이고 T5는 validation, T10은 hash test 몫이다. 표본은 대부분 라벨 층화라 upstream 공개치와 분포가 다르다(`results/T3arm/PREP_20261008.md` §5).

### 3.6 학습 파이프라인

**스크립트.** upstream 파인튜닝 스크립트(`third_party/laya/notebooks/laya_finetune_typed_decisions_mps.py`)의 사본에 두 곳만 패치했다(`poc/finetune/laya_finetune_mps_patched.py`, diff `results/T3arm/finetune_script.diff`). (1) 원본은 `max_len`·`head_max_len`을 1024/256으로 덮어쓴다(`:240`). 패치는 base config 값(english 512/192, multilingual 1024/256)을 유지한다. (2) 원본은 export의 `model_name`을 "laya-typed-decisions"로 덮어쓴다(`:358`). 패치는 base의 이름을 유지한다. 손실(RLCD + soft CE), optimizer, 스케줄은 그대로다. 패치한 export가 base를 보존하는지는 V1(§3.7)이 확인한다.

**설정.** MPS fp32(autocast 없음), micro-batch 8 x grad-accum 4(effective 32), `--no-checkpointing`, AdamW encoder 2.5e-5 / head 1e-4, cosine → 1e-6, RLCD σ 0.4 → 0.1, torch seed 13이다. 하이퍼파라미터는 스크립트 기본값을 모든 과제에 썼다(`results/T3arm/PREP_20261008.md` 머리 표).

**데이터.** 과제마다 train 최대 5,000 items x 2 epoch, dev 최대 1,000행, calib 400행이다(프로젝트 책임자 예산, `docs/11_three_arm_plan.md` §1). 학습 item은 평가 세트와 같은 행 빌더(`scripts/build_jev_cmp_sets.py`의 `row()`, 질문 상수, 라벨 맵, 옵션 샘플러)로 만들고 라벨로 층화했다. T1은 case 단위로 뽑은 5,000 decision이고, T7은 언어당 1,000행이다. choice 질문은 행마다 옵션 순서를 섞어 증강했다(score와 noul은 섞지 않음). dev와 calib는 validation이 있으면 거기서(T3, T6, T7), 없으면 train에서 먼저 떼어 냈고(T1, T2, T4, T5, T8, T9), T10은 hash dev 몫에서 뽑았다. train, dev, calib는 정규화 텍스트 기준으로 서로소다. 평가 항목(Jev 항목과 ext)과 state 텍스트가 같은 학습 후보 행은 미리 뺐다(`results/T3arm/PREP_20261008.md` §1, §2). T8은 train split이 546행(필터 뒤 544행)뿐이라 dev 60과 calib 40을 떼고 남은 444행 전량을 학습했다.

**epoch 선택과 보정.** dev는 epoch 선택에만, calib는 temperature fit에만 쓴다. dev 정확도가 가장 높은 epoch을 고르고 동률이면 앞 epoch을 고른다. 마지막이 아닌 epoch을 고르면 같은 calib로 temperature를 다시 맞춘다. 모든 epoch의 dev가 epoch 0(vanilla)보다 낮으면 그 과제에 "학습 실패"를 표시하고, 형식, 라벨, lr 순으로 원인을 추적한다(`docs/11_three_arm_plan.md` §4).

**실행.** 드라이버 `poc/finetune/run_all_tasks.sh`가 T1\~T10을 차례로 학습하고, epoch별 dev 평가, epoch 선택, Jev 항목·ext 평가, 진단 기록, 정리까지 처리한 뒤 선택 체크포인트 하나만 남긴다. 시작 게이트 `poc/finetune/READY_T3ARM`은 items 10개, 행 파일 30개, 패치 스크립트의 sha256을 담는다. 본 학습은 2026-10-08 10:57:15\~15:01:31(약 4.1시간)에 무인으로 돌았고, 상태 로그는 STEP OK 148, FAILED 0으로 `RUN_ALL FINISHED`에서 끝났다(`results/T3arm/run_all_status.log`, `results/T3arm/run_all_20261008-1057_driver.log`).

**적용한 기본값과 프로젝트 책임자 결정.** 본 학습은 프로젝트 책임자 확인 전에 다음 기본값으로 시작했다(`results/T3arm/PREP_20261008.md` "본 학습 시작 시 적용한 기본값" 절). T8은 hold-out(dev 60 + calib 40 + train 444)을 유지하고 프로젝트 책임자 예산에 맞춰 2 epoch로 학습했다. V3는 판정을 보류하고 수치만 냈다. 보정 분리 열은 넣지 않았고, 반복 학습 run과 T9·T10의 Jev 측정은 하지 않았다. 2026-10-08 15:25 프로젝트 책임자 결정으로 T8 설정은 확정됐고, V3는 차이 기준으로 통과 판정을 받았다. 추가하기로 한 세 항목은 모두 끝나 이 판에 반영했다. 보정 분리 열은 §5.4, T9·T10 Jev 측정은 §5.1에 있다. 반복 학습 1회(seed 14, 10과제, `env SEED=14 RUN_TAG=rep_s14 bash poc/finetune/run_all_tasks.sh`)는 §5.7에 있다. 이 가운데 T9는 다른 프로젝트 실험과의 자원 경합으로 학습이 멈춰 한 번 중지했고, 감시자가 경합이 없을 때 T9·T10을 다시 돌려 2026-10-09 00:23에 끝났다(§7.7, 같은 문서 "프로젝트 책임자 결정" 절과 마지막 두 절).

### 3.7 학습 검증 V1\~V6

| ID | 검증 | 방법 | 통과 기준 |
|---|---|---|---|
| V1 | zero-step identity | 패치한 파이프라인으로 optimizer step 0인 export(`--epochs 0`)를 base별로 만들어 base와 비교하고 세트 하나를 평가 | 가중치 값 일치, argmax 100% 일치, base temperature로 되돌린 평가의 확률 일치 |
| V2 | upstream 재현 | (a) upstream `laya-typed-decisions`를 T1 test 2,000 decision으로 평가. (b) 우리 파이프라인으로 english base를 T1 train 5,000 decision x 2 epoch 학습해 같은 2,000으로 평가 | (a) 공개 0.766의 ±0.02 안. (b) 0.562(vanilla english 0.362 + 0.20) 이상이고 majority 0.461 초과 |
| V3 | label-shuffle 대조 | T3 Emotion, english base, 5,000 items의 라벨을 seed 13으로 섞어 1 epoch 학습 | 엄격 기준: dev 정확도 ≤ majority + 0.05. 차이 기준: 실제 라벨 학습의 epoch 1 dev보다 0.30 이상 낮음 |
| V4 | 형식 동일성 | 과제마다 학습 item을 decode해 같은 state·질문의 추론 시퀀스와 비교 | 토큰 단위 일치 100%(셔플 item은 셔플된 순서 기준) |
| V5 | smoke | base별 200 items x 1 epoch 학습, export, `laya.load`, 평가. 드라이버 `SMOKE=1`로 10과제 전 단계 | 모든 STEP OK |
| V6 | 누수 | train·dev·calib와 평가 항목(Jev 항목, ext)의 교집합 | 정확 일치와 정규화 일치 모두 0 |

출처: `docs/11_three_arm_plan.md` §4, `results/T3arm/PREP_20261008.md` §3.

**계획과의 편차(V3).** 엄격 기준은 학습이 base를 chance 수준으로 무너뜨린다고 가정한다. zero-shot이 강한 base(이 dev에서 0.612)에서는 permuted 라벨 학습이 vanilla 아래로 내려갔지만 majority 근처까지는 무너지지 않아, 엄격 기준을 +0.039 차이로 충족하지 못했다(§5.6). 프로젝트 책임자는 차이 기준과 대안 기준(permuted < vanilla zero-shot dev, 그리고 차이 기준)을 근거로 V3를 통과로 판정했다(2026-10-08 15:25). 이 판은 그 판정을 따르고, 엄격 기준 미달을 계획과의 편차로 기록한다.

### 3.8 통계

정확도 구간은 Wilson 95%, 같은 항목의 두 시스템 비교는 exact McNemar(양측)를 썼다. b는 Jev만 정답, c는 Laya만 정답인 항목 수다. 과제마다 Jev와 비교할 Laya는 세 러너 중 정확도가 가장 높은 러너이며, 결과를 보고 고른 사후 선택이라 Laya에 유리하다. 8개 과제 검정에는 Holm 보정을 적용했다. 과제 macro 평균의 차이는 과제 8개를 복원 재표본한 paired bootstrap(10,000회)으로, 독립 단일 문항(T2·T3·T4·T5·T6·T8, 240개)은 합산 exact McNemar로, 군집이 있는 T1(case 40)과 T7(id 20)은 군집 bootstrap으로 따로 봤다. Boolean은 AUROC(항목 재표본 2,000회), 보정은 Brier와 ECE(15 bins, top 확률 기준), score는 MAE of E[level]를 함께 보고한다(`results/F/jev_cmp/summary.md` §2, §4).

3-arm 비교도 같은 판정 규칙을 쓴다. 같은 항목의 두 arm을 exact McNemar(양측)로 비교하고, b는 앞 arm만 정답, c는 뒤 arm만 정답인 항목 수다. p < 0.05이고 b > c면 앞 arm 유의 우세, c > b면 뒤 arm 유의 우세, 아니면 비유의다. Holm은 비교마다 family를 따로 잡았다. trained vs Jev와 Jev vs vanilla는 S7로 T9·T10이 들어와 8과제에서 10과제가 됐고, trained vs vanilla는 10과제다(Jev 항목과 ext 각각). family를 넓혀도 T1\~T8의 Holm 후 판정은 바뀌지 않았고 Holm p만 바뀌었다. Jev vs vanilla는 v2의 검정을 base 러너(T7 multilingual, 나머지 english)로 다시 묶은 것이라, 과제별 최고 Laya를 쓴 §4와는 T4의 b/c가 다르다. T9·T10은 S7 기록에서 같은 함수로 계산했다. ext의 trained − vanilla 구간은 같은 항목의 paired bootstrap(10,000회, seed 13)이고, T1은 case, T7은 id를 군집으로 재표본한다. Jev 항목의 T1과 T7에는 군집 bootstrap을 함께 낸다. 범주 집계는 과제별 정확도(T1은 Jev 비교 decision, T7은 언어 합산)를 같은 가중치로 평균한 macro다. 구간은 범주 안에서 과제를 복원 재표본(10,000회)한 percentile이다. Q1의 difference-in-differences(DiD)는 제외 범주의 평균 차이에서 포함 범주의 평균 차이를 뺀 값이고, 두 범주를 따로 재표본해 구간을 낸다. 범주당 과제가 4\~6개라 범주 집계는 모집단 추론이 아니라 기술통계다(`results/T3arm/summary.md` §1\~§3). 보정 분리에서 refit 효과는 (vanilla + 과제 T) − vanilla, 학습 효과는 trained − (vanilla + 과제 T)이고, 둘의 합이 trained − vanilla다. 반복 학습은 run 1과 run 2의 Holm 후 판정이 같을 때만 그 판정을 확정한다(run 2의 Holm도 run 1과 같은 10과제 family다, `results/T3arm/summary.md` §4.3, §7).

### 3.9 위협 요약

플레이그라운드는 API가 아니고 모델 버전이 표기되지 않는다. 과제당 n=40이라 Wilson 반폭이 약 ±0.15다. T1의 정답은 데이터셋 teacher 분포의 argmax이고 teacher의 정체는 확인하지 못했다. trained는 과제당 학습 run 두 개이고 MPS 학습은 비트 단위로 결정적이지 않다(§5.6, §5.7). T10은 gold 라벨 품질이 의심된다(§5.1). 상세는 §7.7에 둔다.

## 4. 결과 I: zero-shot 비교

이 절은 v2의 zero-shot 결과(T1\~T8)를 그대로 싣는다. Laya는 학습 없는 base 세 러너(english, multilingual, Router)이고, §5의 vanilla는 영어 과제의 english 열, T7의 multilingual 열과 같다. 이 절의 Holm은 v2의 8과제 family다. 3-arm 확장의 세션 S7에서 잰 T9·T10의 zero-shot 결과는 다음과 같고, 3-arm 표는 §5.1에 있다. T9는 Jev와 Laya 세 러너가 모두 40/40 = 1.000이다. T10은 Jev 10/40 = 0.250, Laya english(= Router) 0.300, multilingual 0.450이고, exact McNemar는 vs english 3/5(p=0.7266), vs multilingual 4/12(p=0.0768)로 모두 비유의다. T10의 Jev는 ECE 0.623으로 크게 과대확신이고 정답 옵션을 0%로 표시한 행이 20/40이다(`results/F/jev_cmp/sessions/S7_20261008/S7_summary.md` §2, §3).

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

## 5. 결과 II: 3-arm 비교

§5.1\~§5.6의 trained 수치는 본 학습 run 1(seed 13)이다. seed 14 반복 학습 run 2도 10과제를 마쳤다. 두 run의 비교와 판정 확정은 §5.7에 있다(30개 비교 중 확정 27, 불일치 3). 수치 출처는 `results/T3arm/summary.md`(2026-10-09 00:23 빌드, 공개용으로 2026-10-12 재빌드: 그림 영어 문구, 공개 주석, Jev 항목별 필드 제거, 수치 동일, `results/T3arm/summary.md:1`. 이하 3-arm 종합)이고 같은 값이 `results/T3arm/summary.json`에 있다.

### 5.1 3-arm 정확도: Jev 항목 (RQ5)

| 과제 (n, 범주) | Jev | vanilla | trained | trained vs Jev: b/c, p (Holm p) | trained vs vanilla: b/c, p (Holm p) |
|---|---|---|---|---|---|
| T1 typed-decisions (120, 제외) | 0.867 | 0.383 | 95/120 = 0.792 | 10/19, 0.1360 (0.9523) | 56/7, 1.4e-10 (1.4e-09) |
| T2 AG News (40, 포함) | 0.875 | 0.975 | 38/40 = 0.950 | 3/0, 0.2500 (1.0000) | 0/1, 1.0000 (1.0000) |
| T3 DAIR Emotion (40, 제외) | 0.700 | 0.750 | 38/40 = 0.950 | 11/1, 0.0063 (0.0635) | 10/2, 0.0386 (0.2314) |
| T4 Banking77-10 (40, 제외) | 0.925 | 0.725 | 38/40 = 0.950 | 3/2, 1.0000 (1.0000) | 9/0, 0.0039 (0.0312) |
| T5 BoolQ (40, 포함) | 0.925 | 0.725 | 31/40 = 0.775 | 2/8, 0.1094 (0.8750) | 2/0, 0.5000 (1.0000) |
| T6 SST-5 (40, 제외) | 0.650 | 0.425 | 27/40 = 0.675 | 6/5, 1.0000 (1.0000) | 16/6, 0.0525 (0.2624) |
| T7 MASSIVE-10 (100, 제외) | 0.910 | 0.620 | 91/100 = 0.910 | 7/7, 1.0000 (1.0000) | 32/3, 4.2e-07 (3.8e-06) |
| T8 prompt-injections (40, 제외) | 0.775 | 0.775 | 39/40 = 0.975 | 9/1, 0.0215 (0.1934) | 9/1, 0.0215 (0.1504) |
| T9 Enron spam (40, 포함) | 1.000 | 1.000 | 39/40 = 0.975 | 0/1, 1.0000 (1.0000) | 0/1, 1.0000 (1.0000) |
| T10 support tickets (40, 포함) | 0.250 | 0.300 | 12/40 = 0.300 | 5/3, 0.7266 (1.0000) | 1/1, 1.0000 (1.0000) |

출처: 3-arm 종합 §1.1. b는 앞 arm만 정답, c는 뒤 arm만 정답인 항목 수다. Holm은 trained vs Jev 10과제, trained vs vanilla 10과제에 따로 적용했다. T9·T10의 Jev(S7)가 들어와 trained vs Jev family가 8과제에서 10과제로 넓어졌고, T1\~T8의 Holm 후 판정은 바뀌지 않았다. 정확도의 Wilson 95% 구간은 그림 4와 3-arm 종합 §1.1에 있다. T1과 T7은 군집 때문에 item 단위 p가 낙관적이다(아래 군집 bootstrap).

| 비교 (과제 수) | 기준 | 앞 arm 유의 우세 | 비유의 | 뒤 arm 유의 우세 |
|---|---|---|---|---|
| trained vs Jev (10) | exact McNemar, 보정 전 α 0.05 | 2 (T3, T8) | 8 | 0 |
| trained vs Jev (10) | Holm 보정 | 0 | 10 | 0 |
| trained vs vanilla (10) | exact McNemar, 보정 전 α 0.05 | 5 (T1, T3, T4, T7, T8) | 5 | 0 |
| trained vs vanilla (10) | Holm 보정 | 3 (T1, T4, T7) | 7 | 0 |
| Jev vs vanilla (10) | exact McNemar, 보정 전 α 0.05 | 4 (T1, T4, T5, T7) | 6 | 0 |
| Jev vs vanilla (10) | Holm 보정 | 2 (T1, T7) | 8 | 0 |

trained vs Jev는 run 1 기준으로 Holm 보정 후 10과제 모두 비유의다. 보정 전에는 T3(b/c 11/1, p=0.0063, Holm 0.0635)와 T8(9/1, p=0.0215, Holm 0.1934)에서 trained가 유의하게 앞섰고, run 1에서는 Jev가 유의하게 앞선 과제가 보정 전에도 없다. Jev가 수치상 앞선 과제는 T1(0.867 대 0.792), T5(0.925 대 0.775, b/c 2/8, p=0.1094), T9(1.000 대 0.975)다. zero-shot에서 Jev가 Holm 후에도 유의하게 앞섰던 T1과 T7에서는 격차가 사라졌다. T1은 반복 run 2에서 103/120 = 0.858로 Jev(104/120)와 b/c 11/12였다(§5.6). run 2에서는 T8만 Holm 보정 후 trained 유의 우세였고(9/0, Holm 0.0391), 보정 전에는 T5에서 Jev가 앞섰다(1/10, p=0.0117). run 2 T5의 Holm 보정 후 p는 10과제 family에서 0.1055로 비유의다. 그래서 Jev가 trained보다 유의하게 앞선 경우는 Holm 보정 후 기준으로 두 run 모두 없고, 보정 전 기준으로는 run 2의 T5 하나다(§5.7). Jev 항목의 trained vs vanilla는 n이 작아 Holm 후 3과제만 유의하므로, 학습 효과의 주 근거는 §5.2의 ext로 둔다.

| 과제 | 비교 | 정확도 차이 | 군집 bootstrap 95% | 군집 / decision |
|---|---|---|---|---|
| T1 | trained − Jev | −0.075 | [−0.185, +0.025] | 40 / 120 |
| T1 | trained − vanilla | +0.408 | [+0.304, +0.516] | 40 / 120 |
| T1 | Jev − vanilla | +0.483 | [+0.371, +0.597] | 40 / 120 |
| T7 | trained − Jev | +0.000 | [−0.100, +0.110] | 20 / 100 |
| T7 | trained − vanilla | +0.290 | [+0.150, +0.440] | 20 / 100 |
| T7 | Jev − vanilla | +0.290 | [+0.100, +0.470] | 20 / 100 |

출처: 3-arm 종합 §1.4. 군집을 복원 재표본(10,000회, seed 13)했고, Jev − vanilla는 §4.2와 같은 값이다.

- **T1**: 타입별로 trained는 choice 38/50, noul 50/60, score 7/10이고 Jev는 42/50, 56/60, 6/10이다. teacher 분포 기준 지표(soft acc / Brier vs soft / score MAE)는 Jev 0.590 / 0.077 / 0.390, vanilla 0.361 / 0.333 / 0.584, trained 0.515 / 0.104 / 0.254다. Laya arm이 평가하는 전체 200 decision에서는 trained 137/200 = 0.685, vanilla 66/200 = 0.330이다(b/c 85/14, p=1.4e-13; 3-arm 종합 §1.2).
- **T7**: 언어별 정확도는 아래와 같다. 언어당 n=20이라 방향 신호다. trained는 vanilla가 가장 약했던 de(0.400 → 0.850)와 ko(0.450 → 0.900)에서 크게 올라 Jev와 비슷해졌다.

| arm | en | de | ja | zh-CN | ko | 합산 |
|---|---|---|---|---|---|---|
| Jev | 0.900 | 0.900 | 0.950 | 0.900 | 0.900 | 0.910 |
| vanilla (multilingual) | 0.850 | 0.400 | 0.800 | 0.600 | 0.450 | 0.620 |
| trained | 0.950 | 0.850 | 0.950 | 0.900 | 0.900 | 0.910 |

- **보조 지표**: T5 AUROC는 Jev 0.988, vanilla 0.810, trained 0.831로 순위 품질의 차이가 남는다. T6 MAE of E[level]은 Jev 0.432, vanilla 0.888, trained 0.472이고, T8 AUROC는 1.000, 0.929, 1.000이다. T9는 Jev, vanilla, trained 모두 AUROC 1.000이다(3-arm 종합 §1.5).
- **T10 (라벨 점검)**: Jev 10/40, vanilla english 12/40, trained 12/40이고 참고 러너 multilingual은 18/40이다. 네 시스템이 모두 틀린 행이 18/40이고, Customer Service와 Human Resources는 네 시스템 모두 0/4다. S7 기록을 읽은 바로는 오답 다수에서 gold 큐가 질문에 준 큐 설명과 맞지 않는다(해석). 그래서 T10의 gold 라벨 품질이 의심되고 수작업 확인이 필요하다. run 2의 trained는 17/40(0.425)이었다(§5.7). 확인 전까지 T10 정확도를 라우팅 능력으로 읽지 않는다(3-arm 종합 §1.6, `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md` §3.6).

![과제별 3-arm 정확도: Jev vs vanilla Laya vs trained Laya, Jev 항목](../results/T3arm/figs/accuracy_3arm.png)

**그림 4.** 과제별 3-arm 정확도(막대)와 Wilson 95% 구간(가는 선), Jev 항목. T9·T10의 Jev는 세션 S7 기록이다. 오른쪽 주석은 trained(run 1) 대비 exact McNemar(b/c, p, Holm p)다(`results/T3arm/figs/accuracy_3arm.png`).

### 5.2 확장 세트: vanilla vs trained

| 과제 (범주) | n | vanilla | trained | trained − vanilla [95%] | b/c, p (Holm p) |
|---|---|---|---|---|---|
| T1 typed-decisions (제외) | 2,000 | 0.363 | 0.686 | +0.323 [+0.290, +0.355] | 818/172, 2.8e-101 (2.8e-100) |
| T2 AG News (포함) | 500 | 0.940 | 0.946 | +0.006 [−0.014, +0.026] | 14/11, 0.6900 (1.0000) |
| T3 DAIR Emotion (제외) | 500 | 0.488 | 0.886 | +0.398 [+0.352, +0.446] | 209/10, 1.4e-49 (1.3e-48) |
| T4 Banking77-10 (제외) | 500 | 0.876 | 0.964 | +0.088 [+0.062, +0.116] | 47/3, 3.7e-11 (2.2e-10) |
| T5 BoolQ (포함) | 500 | 0.834 | 0.832 | −0.002 [−0.024, +0.020] | 16/17, 1.0000 (1.0000) |
| T6 SST-5 (제외) | 500 | 0.338 | 0.590 | +0.252 [+0.200, +0.304] | 172/46, 2.6e-18 (2.1e-17) |
| T7 MASSIVE intent-10 (제외) | 500 | 0.692 | 0.878 | +0.186 [+0.124, +0.248] | 110/17, 7.4e-18 (5.2e-17) |
| T8 prompt-injections (제외) | 116 | 0.698 | 0.966 | +0.267 [+0.181, +0.353] | 33/2, 3.7e-08 (1.8e-07) |
| T9 Enron spam (포함) | 500 | 0.992 | 0.988 | −0.004 [−0.012, +0.004] | 1/3, 0.6250 (1.0000) |
| T10 support tickets (포함) | 500 | 0.264 | 0.332 | +0.068 [+0.028, +0.106] | 68/34, 0.0010 (0.0039) |

출처: 3-arm 종합 §2.1. b는 trained만 정답, c는 vanilla만 정답인 항목 수이고 Holm은 10과제에 적용했다. 차이의 구간은 paired bootstrap(T1은 case, T7은 id 군집)이다. T1 정확도는 argmax gold 기준이다(upstream 정의인 dataset label 기준은 아래 표).

학습 제외 6과제는 Holm 후 모두 유의하게 올랐다(+0.088\~+0.398). 포함 과제는 T2, T5, T9가 비유의이고 T10만 유의하게 올랐다(+0.068, Holm p=0.0039). 비유의인 포함 과제 셋은 vanilla가 이미 높거나(T2 0.940, T9 0.992) vanilla가 학습 split을 기억하는 과제(T5, §5.6)다. T10은 vanilla가 0.264로 낮은 예외이고, 같은 데이터셋의 gold 라벨 품질이 의심된다(§5.1, §7.4). run 2에서도 학습 제외 6과제는 Holm 후 모두 유의하게 올랐고(+0.086\~+0.398), 포함 과제는 T2·T5·T9가 비유의(+0.002, +0.004, −0.004), T10이 유의(+0.076)였다. 10과제 모두 두 run의 ext 판정이 같다(§5.7).

| T1 test 2,000 decision | accuracy (dataset label) | soft acc | Brier vs soft | ECE | score MAE |
|---|---|---|---|---|---|
| upstream `laya-typed-decisions` (V2 a) | 0.766 | 0.471 | 0.061 | 0.214 | 0.242 |
| V2(b): 같은 파이프라인의 준비 run | 0.747 | 0.495 | 0.059 | 0.148 | 0.253 |
| vanilla english | 0.361 | 0.331 | 0.316 | 0.173 | 0.694 |
| trained (본 학습 T1, run 1) | 0.690 | 0.463 | 0.099 | 0.112 | 0.359 |

출처: 3-arm 종합 §2.2. V2(b)와 본 학습 T1은 스크립트, items, seed, 인자가 같은 run이다. seed 14 run 2는 0.735였다(세 run의 비교는 §5.6).

![ext 세트: trained − vanilla 정확도 차이와 paired bootstrap 95% 구간](../results/T3arm/figs/ext_trained_minus_vanilla.png)

**그림 5.** ext 세트에서 trained − vanilla 정확도 차이(점)와 paired bootstrap 95% 구간(가는 선). 채운 점은 run 1(seed 13)이고, 속이 빈 점은 반복 학습 run 2(seed 14)다. 오른쪽 주석은 run 1의 차이와 구간, b/c, exact McNemar p, Holm p이고 괄호 안은 run 2의 차이다(`results/T3arm/figs/ext_trained_minus_vanilla.png`).

### 5.3 범주 집계 (RQ6)

범주는 §3.5의 Laya 학습 믹스 기준이다. S7로 T9·T10의 Jev가 들어와 모든 집계의 포함 범주가 T2·T5·T9·T10이다.

| 기준 | arm | 포함 macro [95%] | 포함 과제 | 제외 macro [95%] |
|---|---|---|---|---|
| Jev 항목 | Jev | 0.762 [0.419, 0.969] | T2·T5·T9·T10 | 0.804 [0.721, 0.885] |
| Jev 항목 | vanilla | 0.750 [0.469, 0.988] | T2·T5·T9·T10 | 0.613 [0.491, 0.732] |
| Jev 항목 | trained | 0.750 [0.462, 0.963] | T2·T5·T9·T10 | 0.875 [0.784, 0.952] |
| ext | vanilla | 0.758 [0.433, 0.966] | T2·T5·T9·T10 | 0.576 [0.428, 0.730] |
| ext | trained | 0.774 [0.485, 0.967] | T2·T5·T9·T10 | 0.828 [0.716, 0.937] |

| 기준 | 차이 | 포함 평균 [95%] | 제외 평균 [95%] | 제외 − 포함 (DiD) [95%] |
|---|---|---|---|---|
| Jev 항목 | Jev − vanilla (Q1) | +0.013 [−0.075, +0.138] | +0.191 [+0.054, +0.330] | +0.179 [−0.008, +0.356] |
| Jev 항목 | trained − vanilla | +0.000 [−0.025, +0.031] | +0.262 [+0.212, +0.327] | +0.262 [+0.202, +0.333] |
| Jev 항목 | trained − Jev | −0.013 [−0.100, +0.062] | +0.071 [−0.017, +0.163] | +0.083 [−0.035, +0.215] |
| ext | trained − vanilla | +0.017 [−0.003, +0.051] | +0.252 [+0.171, +0.328] | +0.235 [+0.147, +0.316] |

출처: 3-arm 종합 §3. 포함 과제는 모든 줄에서 T2·T5·T9·T10, 제외 과제는 T1·T3·T4·T6·T7·T8이다. trained는 run 1이다. run 2의 범주 집계는 §5.7에 있다.

- **학습 이득**: ext의 trained − vanilla는 포함 범주 +0.017, 제외 범주 +0.252이고, DiD +0.235 [+0.147, +0.316]의 구간이 0을 포함하지 않는다. 학습 이득은 upstream이 학습하지 않은 과제에 몰린다. 포함 과제에서는 vanilla가 이미 그 데이터를 봐 이득의 상한이 낮다(retention 상한). Jev 항목에서도 방향이 같다(DiD +0.262 [+0.202, +0.333]).
- **Q1(Jev − vanilla)**: vanilla의 Jev 대비 열세는 제외 범주에서 +0.191 [+0.054, +0.330]으로 구간이 0을 벗어나고, 포함 범주에서는 +0.013 [−0.075, +0.138]이다. DiD는 +0.179 [−0.008, +0.356]으로 "열세가 학습 제외 과제에서 더 크다"는 방향이지만 구간 하한이 0 바로 아래라 판정하지 않는다. 포함 범주 네 과제 중 T9는 세 arm 모두 천장 근처이고 T10은 라벨 품질이 의심되므로(§5.1), 포함 범주의 평균은 이 두 과제의 성질에 크게 좌우된다.
- **trained − Jev**: 제외 범주 +0.071 [−0.017, +0.163], 포함 범주 −0.013 [−0.100, +0.062]로 둘 다 구간이 0을 포함한다.

![범주별 arm macro 정확도: 위는 Jev 항목, 아래는 ext](../results/T3arm/figs/category_macro.png)

**그림 6.** Laya 학습 믹스 범주별 arm macro 정확도(막대)와 범주 안 과제 재표본 bootstrap 95% 구간(가는 선). 위는 Jev 항목의 세 arm(Jev의 T9·T10은 S7), 아래는 ext의 vanilla와 trained(run 1)이고, 오른쪽 주석은 평균에 들어간 과제다(`results/T3arm/figs/category_macro.png`).

### 5.4 보정

temperature 출처가 arm마다 다르다. trained는 과제 calib(400행, T8 40행)로 형식별 temperature를 다시 맞췄고, vanilla english는 upstream이 맞춘 형식별·옵션 수 구간별 값을, vanilla multilingual(T7)은 기본값 1.0을 쓴다. 그래서 trained − vanilla의 보정 차이에는 temperature refit 효과가 섞인다. V1에서는 학습 없이 refit만 해도 ECE가 english 0.083 → 0.064, multilingual 0.365 → 0.179로 바뀌었다(§5.6). 보정 분리 열 vanilla + 과제 T(§3.5)가 이 효과를 떼는 기준선이다. 그 답은 vanilla와 같다. argmax는 6,736 decision 중 6,735개가 일치했고(반올림 동률을 같은 답으로 보면 6,736개), 정답 여부는 6,736개 모두 일치했다. 그래서 정확도와 정확도 검정은 vanilla 그대로이고 Brier·ECE·coverage만 달라진다(3-arm 종합 §4.3).

| Jev 항목 (Brier / ECE) | Jev | vanilla | vanilla + 과제 T | trained |
|---|---|---|---|---|
| T1 | 0.237 / 0.181 | 0.724 / 0.205 | 0.656 / 0.129 | 0.353 / 0.180 |
| T2 | 0.220 / 0.118 | 0.053 / 0.083 | 0.051 / 0.064 | 0.095 / 0.011 |
| T3 | 0.537 / 0.278 | 0.429 / 0.174 | 0.428 / 0.209 | 0.093 / 0.074 |
| T4 | 0.114 / 0.069 | 0.349 / 0.150 | 0.337 / 0.155 | 0.072 / 0.012 |
| T5 | 0.098 / 0.103 | 0.393 / 0.190 | 0.447 / 0.229 | 0.411 / 0.190 |
| T6 | 0.502 / 0.184 | 0.770 / 0.239 | 0.687 / 0.112 | 0.461 / 0.153 |
| T7 | 0.140 / 0.068 | 0.584 / 0.216 | 0.525 / 0.083 | 0.173 / 0.074 |
| T8 | 0.307 / 0.194 | 0.401 / 0.223 | 0.337 / 0.168 | 0.035 / 0.021 |
| T9 | 0.019 / 0.060 | 0.005 / 0.014 | 0.001 / 0.004 | 0.029 / 0.026 |
| T10 | 1.319 / 0.623 | 0.775 / 0.253 | 0.733 / 0.162 | 0.752 / 0.184 |

| ext (Brier / ECE) | vanilla | vanilla + 과제 T | trained |
|---|---|---|---|
| T1 | 0.749 / 0.173 | 0.685 / 0.035 | 0.434 / 0.112 |
| T2 | 0.096 / 0.032 | 0.096 / 0.020 | 0.097 / 0.013 |
| T3 | 0.894 / 0.411 | 0.666 / 0.074 | 0.196 / 0.077 |
| T4 | 0.211 / 0.074 | 0.212 / 0.077 | 0.061 / 0.015 |
| T5 | 0.256 / 0.083 | 0.291 / 0.137 | 0.295 / 0.128 |
| T6 | 0.863 / 0.313 | 0.724 / 0.087 | 0.530 / 0.074 |
| T7 | 0.490 / 0.187 | 0.436 / 0.094 | 0.196 / 0.050 |
| T8 | 0.526 / 0.262 | 0.439 / 0.207 | 0.057 / 0.034 |
| T9 | 0.014 / 0.006 | 0.014 / 0.006 | 0.018 / 0.005 |
| T10 | 0.851 / 0.201 | 0.801 / 0.088 | 0.757 / 0.054 |

| 보정 분리 (refit / 학습) | ext ECE | ext Brier | Jev 항목 ECE | Jev 항목 Brier |
|---|---|---|---|---|
| T1 | −0.138 / +0.077 | −0.064 / −0.250 | −0.076 / +0.051 | −0.067 / −0.303 |
| T2 | −0.012 / −0.006 | −0.000 / +0.001 | −0.019 / −0.052 | −0.002 / +0.043 |
| T3 | −0.336 / +0.002 | −0.228 / −0.470 | +0.034 / −0.135 | −0.002 / −0.334 |
| T4 | +0.004 / −0.063 | +0.001 / −0.151 | +0.005 / −0.143 | −0.012 / −0.265 |
| T5 | +0.055 / −0.010 | +0.035 / +0.003 | +0.039 / −0.039 | +0.054 / −0.036 |
| T6 | −0.226 / −0.013 | −0.139 / −0.194 | −0.127 / +0.041 | −0.084 / −0.226 |
| T7 | −0.093 / −0.045 | −0.054 / −0.240 | −0.133 / −0.009 | −0.060 / −0.352 |
| T8 | −0.055 / −0.173 | −0.087 / −0.382 | −0.055 / −0.147 | −0.065 / −0.302 |
| T9 | +0.000 / −0.001 | +0.000 / +0.003 | −0.010 / +0.022 | −0.004 / +0.029 |
| T10 | −0.113 / −0.034 | −0.050 / −0.045 | −0.091 / +0.022 | −0.042 / +0.019 |

출처: 3-arm 종합 §4.1\~§4.3. refit 효과는 (vanilla + 과제 T) − vanilla, 학습 효과는 trained − (vanilla + 과제 T)이고, 둘의 합이 trained − vanilla다. 음수면 그 지표가 낮아진(좋아진) 것이다. T1의 Jev 항목은 Jev와 비교 가능한 120 decision이다. Brier는 옵션 전체의 제곱 오차 합을 행마다 낸 평균, ECE는 15 bins top 확률 기준이다. Jev 확률은 소수 둘째 자리 반올림이라 Brier·ECE에 약 ±0.005의 하한 오차가 있다.

과제별 분리는 표본이 큰 ext(과제당 116\~2,000 decision)를 주 근거로 읽는다.

- **ECE 개선이 사실상 refit인 과제**: T1(refit −0.138, 학습 +0.077), T3(−0.336, +0.002), T6(−0.226, −0.013), T10(−0.113, −0.034). 이 과제들에서 trained의 ECE가 vanilla보다 낮은 것은 학습이 아니라 과제 calib로 temperature를 다시 맞춘 효과다. T1에서는 학습이 오히려 ECE를 올렸다.
- **ECE 개선이 학습 효과인 과제**: T4(+0.004, −0.063)와 T8(−0.055, −0.173). T7은 둘이 섞인다(−0.093, −0.045).
- **변화가 작거나 나빠진 과제**: T2(−0.012, −0.006)와 T9(+0.000, −0.001)는 vanilla가 이미 잘 보정돼 있어 변화가 작다. T5는 refit이 ECE를 +0.055 올렸다. calib 행이 BoolQ train split에서 왔고, vanilla는 그 split의 행을 기억하는 신호를 보인다(§5.6). 그 행에 맞춘 temperature는 validation 기반 ext에 맞지 않는다. T5의 coverage@오류 5%는 vanilla 0.462, vanilla + 과제 T 0.460, trained 0.174로 학습 쪽에서 떨어졌다.
- **Brier**: Brier는 정확도 변화를 함께 반영하므로 개선의 대부분이 학습 효과다. ext의 학습 효과는 T1 −0.250, T3 −0.470, T4 −0.151, T6 −0.194, T7 −0.240, T8 −0.382이고, refit 효과는 T3 −0.228과 T6 −0.139를 빼면 절댓값 0.09 이하다.
- **Jev 항목(n=40)**: 분리 결과가 ext와 다른 과제가 있다. T3는 ext에서 refit이지만 Jev 항목에서는 학습 효과로 나온다(+0.034, −0.135). 표본이 작아 과제별 판단은 ext를 따른다.
- **clamp**: T1과 T8의 vanilla + 과제 T는 fitted temperature가 laya의 로드 범위 [0.5, 5]에서 잘렸다. T1은 choice 7.613 → 5.000, noul 10.000 → 5.000이고, T8은 noul 10.000 → 5.000이다. 10.000은 학습 스크립트의 fit 상한이다. 그래서 두 과제의 vanilla + 과제 T는 calib에 맞는 temperature에 못 미쳤을 수 있고, refit 효과는 작게, 학습 효과는 크게 잡혔을 수 있다. trained의 fitted temperature는 모든 과제에서 범위 안이다(§5.6).
- **Jev**: Jev 항목의 Jev 보정은 과제마다 크게 다르다. T9는 ECE 0.060이지만 T10은 Brier 1.319, ECE 0.623으로 네 열 중 가장 나쁘다. T10의 Jev는 정답 옵션을 0%로 표시한 행이 20/40이다(§4 서두).

그래서 이 판은 trained의 ECE 개선을 학습 효과로 읽는 범위를 T4·T8(그리고 T7의 일부)로 한정한다. 정확도 비교는 temperature의 영향을 받지 않는다(temperature는 argmax를 바꾸지 않는다).

### 5.5 전문화 비용 (RQ7)

| 과제 | 라벨 (train + calib + dev) | 학습 item-pass | train loop (분) | MPS allocated / driver peak (GB) | 체크포인트 (GB) |
|---|---|---|---|---|---|
| T1 | 6,000 (5,000 + 400 + 600) | 10,000 | 39.9 | 20.7 / 30.2 | 0.85 |
| T2 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 14.4 | 15.2 / 21.6 | 0.85 |
| T3 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 10.1 | 8.8 / 16.2 | 0.85 |
| T4 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 11.6 | 9.7 / 18.4 | 0.85 |
| T5 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 28.3 | 20.7 / 26.2 | 0.85 |
| T6 | 6,100 (5,000 + 400 + 700) | 10,000 | 11.4 | 9.1 / 17.7 | 0.85 |
| T7 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 7.5 | 6.7 / 15.9 | 0.68 |
| T8 | 544 (444 + 40 + 60) | 888 | 1.4 | 20.8 / 26.0 | 0.85 |
| T9 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 43.3 | 20.7 / 32.3 | 0.85 |
| T10 | 6,400 (5,000 + 400 + 1,000) | 10,000 | 26.8 | 18.1 / 22.7 | 0.85 |

출처: 3-arm 종합 §5. base는 T7만 multilingual이고 나머지는 english다. 라벨 합계는 train + calib(temperature fit) + dev(epoch 선택)다. 시간과 메모리는 run_ft 리포트(`results/T3arm/<task>/train_timing.json`, MPS fp32)의 값이고, 체크포인트는 `poc/finetune/ckpt_t3arm/<task>/`(공개 저장소에는 포함하지 않음)의 파일 크기 합(십진 GB)이다. Jev와 vanilla는 라벨과 학습이 없다.

trained의 비용은 과제당 라벨 약 6,400개(T8은 train split 546행 중 필터를 통과한 544개 전부)와 M4 Pro MPS 학습 loop 7.5\~43.3분(T8 1.4분)이다. 입력이 긴 과제(T1, T5, T9, T10)가 26.8\~43.3분으로 오래 걸렸고, 짧은 과제는 7.5\~14.4분이었다. 10과제의 학습 loop 합은 194.8분(3.25시간)으로 준비 단계의 예측 3.22시간과 거의 같았다(`results/T3arm/PREP_20261008.md` §7). 평가와 정리를 포함한 본 학습 전체는 10:57\~15:01(약 4.1시간)이었다. 체크포인트는 과제마다 따로 남아 english 0.85 GB, multilingual 0.68 GB이고 10과제 합은 8.29 GB다. 반복 학습 run 2는 다른 프로젝트 실험과 겹친 구간에서 과제 소요 시간이 늘었다(T6 20분 대 run 1 13.5분, T7 15분 대 11.4분, T8 8분 대 2.4분. `results/T3arm/PREP_20261008.md` 마지막 절의 기록이며 표의 train loop와 기준이 다르다). 그래서 비용은 run 1 값으로 보고한다. trained 체크포인트는 base와 구조와 시퀀스 예산이 같다(V1). 그래서 추론 지연은 §4.5의 Laya 구조를 따를 것으로 보지만, trained로는 지연을 따로 재지 않았다.

### 5.6 학습 검증 (RQ8)

| ID | 검증 | 핵심 수치 | 판정 |
|---|---|---|---|
| V1 | zero-step identity | 가중치 텐서 값 english 206/206, multilingual 170/170 동일. argmax 40/40, 20/20 일치. base temperature로 되돌린 답 40/40, 20/20 동일. refit만으로 ECE english 0.083 → 0.064, multilingual 0.365 → 0.179 | 통과 |
| V2 | upstream 재현 | (a) upstream 체크포인트 0.766(공개 0.766, 기준 ±0.02). (b) 우리 파이프라인의 준비 run 0.747(기준 ≥ 0.562, majority 0.461) | 통과 |
| V3 | label-shuffle | permuted 0.385, 실제 라벨(본 학습 T3 epoch 1) 0.864, vanilla 0.612, majority 0.296. 엄격 기준 0.346 대비 +0.039 미달, 차이 0.479 ≥ 0.30 | 통과(차이 기준, 프로젝트 책임자 판정) |
| V4 | 형식 동일성 | 10과제, 추론 시퀀스와 토큰 일치 250/250, 옵션 decode와 target 점검 49,084 items | 통과 |
| V5 | smoke | english 3.95 items/s, multilingual 20.14 items/s. 드라이버 SMOKE STEP OK 163, FAILED 0 | 통과 |
| V6 | 누수 | 10과제 train·dev·calib와 평가 텍스트의 교집합 정확 0 / 정규화 0. 추출 전 제거 T3 1, T7 24 | 통과 |

출처: 3-arm 종합 §6.2, §6.3, `results/T3arm/validity/`. V3 판정은 프로젝트 책임자 판정이고 3-arm 종합 §6.3과 `results/T3arm/PREP_20261008.md` "프로젝트 책임자 결정" 1번에 있다. V1 export의 가중치 파일에서 바뀐 것은 temperature 버퍼의 dtype뿐이고(값은 그대로) 그래서 파일 sha256은 다르다. config에서는 temperature가 calib로 다시 맞춰지고 `temperature_by_options`가 지워진다. V3의 permuted 학습은 train 정확도가 chance(0.15\~0.21)에 머물렀고, 남은 정답은 vanilla가 맞힌 항목에 몰렸다(0.475 대 0.242). 그래서 majority를 넘는 부분은 누수가 아니라 사전학습 순위가 남은 것으로 본다(`results/T3arm/PREP_20261008.md` §3).

| 과제 | dev: epoch 0 (vanilla) → 1 → 2 | 선택 epoch | train − dev | flip dev40 [95%] | 학습 실패 표시 |
|---|---|---|---|---|---|
| T1 | 0.365 → 0.667 → 0.683 | 2 | +0.054 | 0.031 [0.000, 0.069] | 아니오 |
| T2 | 0.936 → 0.934 → 0.937 | 2 | +0.027 | 0.005 [0.000, 0.015] | 아니오 |
| T3 | 0.612 → 0.864 → 0.897 | 2 | +0.034 | 0.015 [0.000, 0.040] | 아니오 |
| T4 | 0.842 → 0.922 → 0.946 | 2 | +0.013 | 0.035 [0.000, 0.095] | 아니오 |
| T5 | 0.986 → 0.955 → 0.971 | 2 | +0.009 | - | 예 (dev 기준선 오염) |
| T6 | 0.360 → 0.490 → 0.506 | 2 | +0.142 | - | 아니오 |
| T7 | 0.671 → 0.854 → 0.868 | 2 | +0.069 | 0.010 [0.000, 0.025] | 아니오 |
| T8 | 0.683 → 0.967 → 0.950 | 1 (재보정) | +0.033 | - | 아니오 |
| T9 | 0.996 → 0.995 → 0.995 | 1 (재보정) | −0.001 | - | 예 (천장 효과) |
| T10 | 0.419 → 0.367 → 0.385 | 2 | +0.083 | 0.175 [0.105, 0.250] | 예 (dev 라벨 분포 불일치) |

출처: 3-arm 종합 §6.1. train − dev는 마지막 창의 train 정확도(dropout을 켠 학습 forward)에서 선택 epoch의 dev 정확도를 뺀 값이다. flip은 choice 과제 dev 앞 40행의 옵션 순서를 바꾼 순열당 답 변경 비율이다(T1은 choice 58문항). 학습 실패는 모든 epoch의 dev가 epoch 0(vanilla)보다 낮다는 뜻이다.

![과제별 dev 정확도: epoch 0(vanilla)에서 epoch 2까지](../results/T3arm/figs/dev_curves.png)

**그림 7.** 과제별 dev 정확도의 epoch 0(vanilla) → 1 → 2 곡선. 테두리 원은 선택 epoch이고, 마지막 점은 최종 export(마지막 epoch + fitted temperature)다(`results/T3arm/figs/dev_curves.png`).

학습 실패 표시 3건은 모두 파이프라인 실패가 아니다(`results/T3arm/PREP_20261008.md` "본 학습 중 발견" 절).

- **T5 (dev 기준선 오염)**: dev가 BoolQ train split에서 왔고, BoolQ는 upstream 학습 믹스에 있다. vanilla는 같은 분포에서 train 행 dev 0.986, validation ext 0.834를 보여 train 행을 기억하는 신호가 있다. 학습이 그 기억을 조금 깎아 dev가 내려갔고, validation 기반 ext에서는 vanilla와 trained가 같다(0.834 대 0.832). 형식은 V4에서 일치했고 train − dev는 0.009라 라벨이나 lr 문제로 보이지 않는다.
- **T9 (천장 효과)**: vanilla가 이미 dev 0.996, ext 0.992이고, 표시는 dev 1,000행 중 1행 차이에서 나왔다. vanilla의 dev와 ext가 거의 같아 T5 같은 기억 신호는 없다.
- **T10 (dev 라벨 분포 불일치)**: dev는 자연 분포라 Technical Support 몫(0.262)이 가장 크고, train과 ext는 균등에 가깝다. vanilla는 이 큐로 예측이 쏠려 있어 자연 분포 dev에서 유리하다. trained는 dev에 있는 8개 큐 중 7개에서 recall이 올랐고 dev macro recall도 0.347에서 0.403으로 올랐다. 균등 분포 ext에서는 +0.068이다.

**주의할 점.** T10은 학습 뒤에도 옵션 순서 flip이 0.175 [0.105, 0.250]으로 다른 choice 과제(0.005\~0.035)보다 높아, 결정이 옵션 순서에 민감하다. T6은 train − dev가 +0.142로 10과제 중 가장 크다(다른 과제는 +0.083 이하). 추가 epoch이나 정규화 비교를 하지 않았으므로 과적합 여부는 판정하지 않는다.

**같은 설정 T1 재학습 편차와 seed 반복.** 준비 단계의 V2(b)와 본 학습 run 1은 스크립트 sha256, items sha256, seed 13, 스크립트 인자가 모두 같지만 결과가 다르다. seed만 14로 바꾼 반복 학습 run 2도 T1을 마쳤다(3-arm 종합 §6.4, §7.4).

| 지표 | V2(b) (준비, seed 13) | 본 학습 run 1 (seed 13) | run 2 (seed 14) |
|---|---|---|---|
| dev epoch 1 / 2 | 0.708 / 0.738 | 0.667 / 0.683 | 0.702 / 0.750 |
| test accuracy (dataset label) | 0.747 | 0.690 | 0.735 |
| test soft acc / Brier vs soft / score MAE | 0.495 / 0.059 / 0.253 | 0.463 / 0.099 / 0.359 | 0.491 / 0.063 / 0.262 |
| test ECE | 0.148 | 0.112 | 0.144 |
| calibration 행 정확도 | 0.718 | 0.685 | 0.720 |

| 짝 비교 (test 2,000 decision) | b/c | exact McNemar p | 정확도 차이 (argmax gold) | case 군집 bootstrap 95% |
|---|---|---|---|---|
| V2(b) vs run 1 | 217/98 | 1.7e-11 | +0.059 | [+0.040, +0.081] |
| V2(b) vs run 2 | 118/96 | 0.1510 | +0.011 | [−0.003, +0.025] |
| run 1 vs run 2 | 117/214 | 1.1e-07 | −0.049 | [−0.069, −0.028] |

b는 앞 run만, c는 뒤 run만 맞힌 decision 수이고, 차이는 앞 run − 뒤 run이다. 군집 bootstrap은 case 400개를 복원 재표본(10,000회, seed 13)했다.

세 run의 test 정확도는 0.747 / 0.690 / 0.735다. V2(b)와 run 2는 구분되지 않고(p=0.1510), 본 학습 run 1만 다른 두 run과 유의하게 다르다. 그래서 run 1의 0.690이 세 run 중 이탈값이고, §5.1\~§5.4의 T1 trained 수치(run 1)는 T1의 학습 효과를 낮게 잡았을 수 있다. run 2의 T1은 Jev 항목에서 103/120 = 0.858(Jev 104/120과 b/c 11/12, p=1.0000), ext에서 0.735(vanilla 대비 +0.371)였다.

V2(b)와 run 1의 micro-batch 손실은 0\~11번이 소수 다섯째 자리까지 같아 데이터 순서, 초기 가중치, RLCD 노이즈가 같다. 손실은 12번에서 처음 갈라지고(1.20023 대 1.20035), 평균 절대 차이는 epoch 2 구간(625\~1249번)에서 0.0823까지 커진다. 원인은 MPS 학습이 비트 단위로 결정적이지 않은 데 있다. 어느 연산이 비결정적인지는 확인하지 않았다. 평가는 결정적이라(vanilla 28/28 비트 재현) 보존한 체크포인트를 다시 평가하면 같은 수치가 나오지만, 다시 학습하면 다른 모델이 나온다.

seed를 바꾼 run 2의 과제별 결과와 두 run의 판정 확정은 §5.7에 있다.

### 5.7 반복 학습과 판정 확정 (두 run)

run 2는 본 학습과 같은 설정에서 torch seed만 14로 바꾼 반복 학습이다(`results/T3arm/rep_s14/<task>/`, 프로젝트 책임자 결정 4번). 데이터 순서는 같고 seed는 dropout과 RLCD 노이즈를 바꾼다. run 2는 10과제를 모두 마쳤다. T9는 다른 프로젝트 실험과의 자원 경합으로 학습이 멈춰 한 번 중지했고, 감시자가 경합이 없을 때 T9·T10을 다시 돌려 2026-10-09 00:23에 끝났다(§7.7, `results/T3arm/PREP_20261008.md` 마지막 두 절). 판정은 두 run의 Holm 후 결론이 같을 때만 확정한다. run 2의 Holm도 run 1과 같은 10과제 family다. vanilla, Jev, vanilla + 과제 T는 학습이 없어 두 run에 같다(3-arm 종합 §7).

| 과제 (범주) | Jev 항목 정확도: run 1 / run 2 / 평균 | ext 정확도: run 1 / run 2 / 평균 | ext run 1 vs run 2: b/c, p | 선택 epoch: run 1 / run 2 |
|---|---|---|---|---|
| T1 typed-decisions (제외) | 0.792 / 0.858 / 0.825 | 0.686 / 0.735 / 0.711 | 117/214, 1.1e-07; 군집 bootstrap −0.049 [−0.069, −0.028] | 2 / 2 |
| T2 AG News (포함) | 0.950 / 0.975 / 0.962 | 0.946 / 0.942 / 0.944 | 12/10, 0.8318 | 2 / 1 |
| T3 DAIR Emotion (제외) | 0.950 / 0.925 / 0.938 | 0.886 / 0.886 / 0.886 | 11/11, 1.0000 | 2 / 2 |
| T4 Banking77-10 (제외) | 0.950 / 0.925 / 0.938 | 0.964 / 0.962 / 0.963 | 9/8, 1.0000 | 2 / 2 |
| T5 BoolQ (포함) | 0.775 / 0.700 / 0.738 | 0.832 / 0.838 / 0.835 | 21/24, 0.7660 | 2 / 2 |
| T6 SST-5 (제외) | 0.675 / 0.725 / 0.700 | 0.590 / 0.578 / 0.584 | 38/32, 0.5504 | 2 / 2 |
| T7 MASSIVE intent-10 (제외) | 0.910 / 0.870 / 0.890 | 0.878 / 0.882 / 0.880 | 16/18, 0.8642; 군집 bootstrap −0.004 [−0.032, +0.024] | 2 / 2 |
| T8 prompt-injections (제외) | 0.975 / 1.000 / 0.988 | 0.966 / 0.957 / 0.961 | 2/1, 1.0000 | 1 / 2 |
| T9 Enron spam (포함) | 0.975 / 0.975 / 0.975 | 0.988 / 0.988 / 0.988 | 2/2, 1.0000 | 1 / 2 |
| T10 support tickets (포함) | 0.300 / 0.425 / 0.362 | 0.332 / 0.340 / 0.336 | 33/37, 0.7202 | 2 / 2 |

출처: 3-arm 종합 §7.1. 정확도는 trained의 정확도이고 평균은 두 run의 단순 평균이다. b는 run 1만, c는 run 2만 맞힌 ext 항목 수다. T1과 T7은 run 1 − run 2 정확도 차이의 군집 bootstrap(10,000회)을 함께 둔다.

| 과제 | Jev 항목 trained vs Jev | Jev 항목 trained vs vanilla | ext trained vs vanilla |
|---|---|---|---|
| T1 | 확정: 비유의 | 확정: trained 우세 | 확정: trained 우세 |
| T2 | 확정: 비유의 | 확정: 비유의 | 확정: 비유의 |
| T3 | 확정: 비유의 | 확정: 비유의 | 확정: trained 우세 |
| T4 | 확정: 비유의 | 불일치: trained 우세 → 비유의 | 확정: trained 우세 |
| T5 | 확정: 비유의 | 확정: 비유의 | 확정: 비유의 |
| T6 | 확정: 비유의 | 확정: 비유의 | 확정: trained 우세 |
| T7 | 확정: 비유의 | 확정: trained 우세 | 확정: trained 우세 |
| T8 | 불일치: 비유의 → trained 우세 | 불일치: 비유의 → trained 우세 | 확정: trained 우세 |
| T9 | 확정: 비유의 | 확정: 비유의 | 확정: 비유의 |
| T10 | 확정: 비유의 | 확정: 비유의 | 확정: trained 우세 |

출처: 3-arm 종합 §7.2. 판정은 Holm 보정 후이고, "trained 우세"는 trained 유의 우세다. 불일치 칸은 run 1 → run 2 판정이다.

30개 비교(10과제 x 3종) 가운데 확정 27, 불일치 3이다. 불일치 셋은 모두 n=40 Jev 항목 비교이고 Holm p가 0.05 근처다. T4 trained vs vanilla는 run 1에서 유의(Holm p 0.0312), run 2에서 비유의(0.0547)다. T8 trained vs Jev(0.1934, 0.0391)와 T8 trained vs vanilla(0.1504, 0.0312)는 run 1에서 비유의, run 2에서 trained 유의 우세다. run 2가 8과제만 끝났던 시점에는 T6 trained vs vanilla가 불일치였지만, family가 10과제가 되자 run 2도 비유의(0.0709)가 되어 확정됐고 대신 T4가 불일치가 됐다. 경계 근처의 Jev 항목 판정은 run과 family 크기에 따라 바뀐다.

두 run에서 확정된 결론은 다음과 같다.

- **Jev 대비**: Holm 보정 후 Jev가 trained보다 유의하게 앞선 비교는 두 run 모두 없다. T8을 뺀 9과제의 trained vs Jev는 두 run 모두 비유의로 확정됐다. 보정 전에는 run 2의 T5가 Jev 우세였고(b/c 1/10, p=0.0117), 10과제 family의 Holm 보정 후에는 0.1055로 비유의다.
- **ext 학습 효과**: ext의 trained vs vanilla는 10과제 모두 두 run의 판정이 같다. 학습 제외 6과제(T1, T3, T4, T6, T7, T8)와 T10의 trained 우세는 두 run 모두 Holm 보정 후 유의하고, 포함 과제 T2·T5·T9는 두 run 모두 비유의다. 두 run의 ext 정확도는 T1을 빼면 차이가 0.012 이하이고, run 1 vs run 2 짝 비교도 T1을 빼면 모두 p ≥ 0.55다.
- **Jev 항목 학습 효과**: T1·T7의 trained 우세와 T2·T3·T5·T6·T9·T10의 비유의가 확정됐다. T4와 T8은 불일치다.

| run | 포함 평균 [95%] | 포함 과제 | 제외 평균 [95%] | 제외 − 포함 (DiD) [95%] |
|---|---|---|---|---|
| run 1 (seed 13) | +0.017 [−0.003, +0.051] | T2·T5·T9·T10 | +0.252 [+0.171, +0.328] | +0.235 [+0.147, +0.316] |
| run 2 (seed 14) | +0.020 [−0.002, +0.058] | T2·T5·T9·T10 | +0.257 [+0.169, +0.340] | +0.238 [+0.144, +0.325] |

출처: 3-arm 종합 §7.3. ext의 trained − vanilla를 §5.3과 같은 방식으로 범주별로 평균했다. 두 run의 과제 구성은 같다(제외 과제는 T1·T3·T4·T6·T7·T8). run 2의 포함 +0.020, 제외 +0.257, DiD +0.238은 run 1과 거의 같고, 두 run 모두 DiD 구간이 0을 포함하지 않는다.

T1의 세 run(준비 V2(b), run 1, run 2) 비교는 §5.6에 있다. run 1이 이탈값이고, run 2의 T1은 Jev 항목에서 Jev(0.867)에 가까운 0.858이었다.

### 5.8 파인튜닝 참고선 (v2의 RQ5)

| 참고선 (zero-shot 아님) | 과제·표본 | Laya | Jev | 비교 |
|---|---|---|---|---|
| Laya typed-decisions (typed-decisions train으로 파인튜닝) | T1, 같은 120 decision | 104/120 = 0.867 | 104/120 = 0.867 | b/c 10/10, p=1.0 |
| Laya ft-v1 (한국어 domain_8 train 11,094행) | 한국어 도메인 라우팅 파일럿 24행 | 22/24 = 0.917 [0.742, 0.977] | 20/24 = 0.833 [0.641, 0.933] | b/c 0/2, p=0.5 |
| Laya ft-v1 | ko_massive_domain_8 test 절반 250행 | 0.900 [0.860, 0.936] (zero-shot 0.492) | 미측정 | - |

출처: `results/F/jev_cmp/summary.md` §3, `results/F/jev_playground_manual_20261006.md`, `results/P4/metrics/full_20261003-1156_summary.md`. 두 파인튜닝 선은 같은 분포의 학습 데이터를 쓴 in-domain 결과라 학습 데이터 없이 답하는 Jev와 조건이 다르다. ft-v1 학습은 M4 Pro MPS에서 3 epoch, 2,150 s(35.8분)가 걸렸다(`results/REPORT.md` §4). 파일럿에서 Jev가 ft-v1에 진 2행은 MASSIVE `play` 시나리오의 게임 실행 문장을 media로 묶는 관례 때문이었다. 이 관례는 라벨 설명에 없고, ft-v1은 학습 데이터에서 이를 배웠다(`results/F/jev_playground_manual_20261006.md` §4).

3-arm의 trained T1과 비교하면, 같은 120 decision에서 upstream typed-decisions 체크포인트는 104/120, trained는 95/120(run 1)과 103/120(run 2)이다. test 2,000 decision에서는 upstream 0.766 대 run 1 0.690, run 2 0.735다(§5.2, §5.6). 우리 예산은 upstream의 약 45%(10,000 item-pass 대 22,400)이고, context는 절반(512 대 1,024), 정밀도는 fp32(upstream fp16 autocast)다(`results/T3arm/PREP_20261008.md` §4). 같은 파이프라인의 세 run이 0.690\~0.747로 갈렸으므로 이 차이에는 예산 차이와 run 간 편차가 함께 들어 있다.

## 6. 사례 연구: 한국어 도메인 라우팅 PoC

본 비교에 앞서 같은 프로젝트에서 Laya를 한국어 도메인 라우터로 도입할 수 있는지 PoC를 수행했다(`results/REPORT.md`). 이 사례는 RQ5의 근거이자 운영 관점의 참고다.

- **zero-shot 한계**: MASSIVE ko의 시나리오를 8개 도메인으로 묶은 `ko_massive_domain_8`에서 multilingual zero-shot은 test 절반 0.492였다. 스키마 문구 변형 6종(dev에서 모두 v1 대비 −0.020\~−0.050), temperature 보정, 임계값 조정 어느 것으로도 0.6 선을 넘지 못했다(`results/REPORT.md` §0, §2).
- **파인튜닝**: MASSIVE ko train 11,094행(옵션 순서 셔플 증강)으로 학습한 ft-v1은 test 절반 0.900, 전체 test 2,917행 0.913, ECE 0.053, 옵션 순서 flip 0.037이었다. YNAT dev 정확도는 0.612에서 0.633으로 유지되어 망각이 보이지 않았다(`results/REPORT.md` §4).
- **Go/No-Go**: 사전에 정한 8개 게이트(G0\~G7) 중 zero-shot은 정확도(G1), coverage(G2), 옵션 순서(G4)에서 미달했다. ft-v1은 8개를 모두 통과했고(G2는 조건부), 판정은 "파인튜닝 파이프라인 전제의 Conditional Go"였다(`results/REPORT.md` §7).
- **서비스**: ft-v1을 올린 laya-serve 기반 라우터와 데모 UI가 수용 점검 11/11을 통과했고, 1문항 결정의 로컬 HTTP 왕복은 p50 20.1 ms, p95 21.1 ms였다(`results/REPORT.md` §5).
- **한국어 지원 감사**: 한국어는 Laya의 평가 언어이고(MASSIVE ko intent-20 multilingual 0.470, upstream 수치와 Δ 0.000으로 재현, `results/A/README.md`) mmBERT 사전학습의 high-resource 언어지만, 결정 학습 데이터에는 문서화되지 않았다. 토크나이저 UNK는 0이고 영어 대비 토큰이 1.5배다. 라틴 문자가 다수인 혼합문과 10음절 미만 한국어는 english로 라우팅되므로 `lang="ko"` 명시가 필요하다(`results/REPORT.md` §3, `docs/07_korean_support_audit.md` §1).

이 사례에서 zero-shot Laya는 Jev에 뒤졌지만(파일럿 0.417 vs 0.833, p=0.0020), 약 36분 학습한 ft-v1은 Jev와 구분되지 않으면서 수치상 앞섰고(0.917 vs 0.833, p=0.5000) 로컬 서빙의 지연·비용 이점을 유지했다.

## 7. 고찰

### 7.1 Jev가 앞서는 곳

zero-shot에서 Jev의 우위는 학습 분포 밖의 형식과 지시 따르기에서 크게 나타났다. typed-decisions(T1), key 단독 라벨의 Banking77-10(T4), BoolQ(T5), 다국어 의도(T7)가 그렇다. 5레벨 감성 척도(T6)는 주 지표인 argmax 정확도로는 비유의지만 MAE 차이의 구간이 0을 벗어난다. 특히 T5는 Laya 학습 믹스 과제인데도 순위 품질 자체가 달랐다(AUROC 0.988 vs 0.810). 학습 믹스로 나누면(§3.1) 유의 우세 4개 중 T1·T4·T7은 두 Laya 체크포인트가 학습하지 않은 데이터이고, Holm 보정 뒤에도 남는 T1·T7도 여기에 속한다. 학습 믹스 과제에서 Jev가 앞선 것은 T5 하나다. T7에서 Jev는 언어를 바꿔도 같은 결정을 냈고 Laya는 같은 id에서도 언어에 따라 결정이 갈렸다. 라벨 이름의 의미를 활용하는 능력, 다국어 표현의 정렬, 척도 전체를 쓰는 보정에서 차이가 난다고 해석할 수 있지만, Jev 내부를 알 수 없으므로 원인은 가설이다.

이 우위는 "라벨 없이 바로"라는 조건에 묶여 있다. 과제 라벨로 학습하면 Holm 보정 후 Jev가 유의하게 앞서는 비교가 두 run 모두 없다(§5.1, §5.7). run 1에서 Jev가 수치상 앞선 곳은 T1(0.867 대 0.792), T5(0.925 대 0.775), T9(1.000 대 0.975)다. T1의 차이는 반복 run 2에서 104/120 대 103/120으로 거의 없었다(§5.6). T5는 run 2에서 0.700으로 차이가 더 커져 보정 전 Jev 우세였다(b/c 1/10, p=0.0117, Holm 보정 후 0.1055로 비유의). T5는 AUROC도 Jev 0.988, trained 0.831이다. ext에서도 AUROC는 vanilla 0.913, trained 0.898이고 정확도 이득은 −0.002였다. upstream 학습 믹스에 있는 BoolQ에서는 과제 라벨 5,000개로도 Laya의 순위 품질이 오르지 않았다. T1은 teacher 분포 기준 soft acc도 Jev가 높지만(0.590 대 0.515) score MAE는 trained가 낮다(0.254 대 0.390).

### 7.2 zero-shot에서 비슷한 곳

AG News(T2)는 Laya 쪽 방향(b/c 0/4)이지만 비유의이고 Laya 학습 믹스 과제다. Emotion(T3)은 b/c 2/4다. prompt-injections(T8)는 정확도가 같지만 오류 구조가 다르다. Jev는 역할·작업 지시형 주입 5개를 p(true) 0.17\~0.40으로 놓쳤고, Laya english는 명시적 무시·덮어쓰기 지시 5개를 놓쳤으며 그중 4개가 독일어 문장이었다(`results/F/jev_cmp/sessions/S5_20261007/S5_summary.md` §4.3). Laya가 같거나 앞선 과제는 이 셋뿐이고, 그중 학습 믹스 과제는 T2이며 T3·T8은 held out이다.

S7의 T9·T10도 zero-shot에서 비유의다. T9는 Jev와 Laya 세 러너가 모두 40/40이라 이 표본으로는 변별력이 없다. T10은 Jev 0.250, Laya english 0.300, multilingual 0.450으로 모두 낮고, gold 라벨 품질이 의심된다(§4 서두, §5.1). T10에서 Laya가 앞선 큐(Billing and Payments)는 가격 문의를 Billing으로 보내는 데이터셋 관례와 맞는 쪽이었다(해석, `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md` §3.6).

### 7.3 trained가 따라잡거나 넘는 곳

- **넘는 곳**: T3 Emotion(0.950 대 0.700)과 T8 prompt-injections(0.975 대 0.775)는 run 1에서 보정 전 trained 유의 우세다. run 2에서도 T3는 보정 전 우세(b/c 11/2, p=0.0225)였고, T8은 Holm 후에도 우세(9/0, Holm 0.0391)였지만 run 1과 판정이 달라 불일치로 남는다(§5.7). 둘 다 Laya 학습 제외 과제이고, zero-shot에서는 vanilla가 Jev와 비슷했던 과제다(0.750 대 0.700, 0.775 대 0.775). 두 과제는 라벨 경계가 데이터셋 고유의 정의(감정 6분류, 데이터셋이 정한 주입 기준)에 달려 있어, 라벨 이름만 보고 답하는 zero-shot보다 과제 라벨에서 배운 경계가 유리했을 수 있다. Jev 내부를 알 수 없으므로 원인은 가설이다. T8에서 Jev의 오류 9개는 모두 미탐이었고(§4.1) trained는 39/40이다.
- **따라잡는 곳**: zero-shot에서 Holm 후에도 Jev 우세였던 T7은 trained가 91/100으로 Jev와 같고, 5개 언어 모두 0.850 이상이다(vanilla는 de 0.400, ko 0.450). 언어당 1,000행의 학습으로 다국어 정렬의 격차가 닫혔다. T1은 0.383에서 0.792로 올라 Jev와의 차이가 군집 bootstrap 구간 안으로 들어왔다. T4(0.950 대 0.925)와 T6(0.675 대 0.650, MAE 0.472 대 0.432)도 Jev 수준이다.
- **한정**: trained vs Jev는 run 1에서 Holm 후 모두 비유의, run 2에서는 T8만 trained 우세였고, Jev 항목은 n=40(T1 120 decision, T7 100)이다. 같은 파이프라인의 T1 세 run은 test 0.747 / 0.690 / 0.735로 갈렸다(§5.6). "넘는다"는 판정은 두 run이 모두 Holm 후 trained 우세일 때만 쓰는데, trained vs Jev에서 그런 과제는 아직 없다.

### 7.4 포함 과제의 retention 상한

학습 믹스 포함 과제에서 trained − vanilla는 작았다(ext 평균 run 1 +0.017, run 2 +0.020). T2(0.940)와 T9(0.992)는 vanilla가 이미 천장 가까이에 있다. T5는 vanilla가 train split 행을 기억해(dev 0.986, validation 0.834) 같은 분포의 라벨을 다시 배워도 validation이 오르지 않았다. 그래서 학습 이득은 범주별로 읽어야 한다. 10개 과제를 한데 평균하면 포함 과제의 작은 이득이 학습 효과를 희석한다. 반대로 포함 과제라고 늘 vanilla가 강한 것은 아니다. T10은 upstream이 학습 믹스로 표기한 과제지만 vanilla english가 ext 0.264로 낮다. 우리 ext는 큐마다 균등이고 upstream Themes는 영어 앞 400행의 자연 분포라 분포가 다르며, vanilla english는 예측이 Technical Support로 쏠린다. Router가 고른 english base보다 multilingual이 ext에서 0.454로 높다(`results/T3arm/PREP_20261008.md` §5, "이상 / 주석" 14번). T10의 trained는 +0.068 올랐지만 0.332에 그쳤다. T10은 Jev 항목에서 네 시스템이 모두 틀린 행이 18/40이라, 낮은 정확도의 일부는 gold 라벨 문제일 수 있다(§5.1). 따라서 retention 상한은 "포함 과제에서 vanilla가 이미 강할 때"의 상한이고, 포함 표기만으로 vanilla의 성능을 가정할 수는 없다. Q1의 Jev − vanilla DiD(+0.179 [−0.008, +0.356])도 같은 방향이지만 구간이 0을 포함한다. S7로 Jev가 있는 포함 과제가 네 개가 됐어도, T9는 세 arm 모두 천장 근처이고 T10은 라벨 품질이 의심된다. 그래서 포함 범주에서 retention과 일반화를 가르는 정보는 아직 T2·T5에 몰려 있다.

### 7.5 전문화 비용

trained Laya의 정확도는 과제당 라벨 약 6,400개와 M4 Pro 한 대의 학습 1.4\~43.3분으로 얻었다. 이 비용은 과제마다 반복된다. 이번 10과제에는 라벨 57,444개, 학습 loop 194.8분, 체크포인트 10개 8.29 GB가 들었고, 과제를 더할 때마다 데이터 구축, 학습, V1\~V6에 해당하는 점검이 다시 필요하다. 과제마다 체크포인트가 따로라 여러 과제를 한 서버에서 처리하려면 체크포인트를 바꿔 가며 올리거나 함께 올려야 한다. 멀티태스크 단일 모델은 이번 범위에서 만들지 않았다(`docs/11_three_arm_plan.md` 열린 질문 8). Jev는 라벨과 학습이 필요 없지만 토큰 과금(인용 단가 기준 1,000 decision당 약 $0.0197, 단가 확인 필요)과 데이터 외부 전송이 따른다(§4.5). 라벨 몇 개면 Jev에 도달하는지는 이번에 재지 않았다(§8).

### 7.6 Laya의 레버

- **파인튜닝**: Holm 보정 후 Jev가 과제별 trained보다 유의하게 앞선 비교는 두 run 모두 없었고(보정 전에는 run 2의 T5 하나, §5.1, §5.7), 두 참고선도 zero-shot 격차를 닫았다(§5.8). upstream의 자기 규정(fast base to specialise)과 일치한다.
- **러너 선택**: english와 multilingual의 차이가 과제마다 크고 방향도 바뀐다(T5 0.725 vs 0.600, T7 ja 0.450 vs 0.800). Router는 언어로만 고르므로 T7 de처럼 배정이 섞이고(multilingual 15, english 5) 정확도도 0.350에 그친다.
- **옵션 렌더링**: 같은 T4 40행에서 옵션 렌더링을 `key: key spaced`에서 key 단독으로 바꾸기만 해도 english는 0.825에서 0.725로(이전 렌더링에서만 정답 4행, key 단독에서만 정답 0행, p=0.1250), multilingual은 0.575에서 0.750으로(0행 / 7행, p=0.0156) 움직였다(`results/F/jev_cmp/laya_summary.md` §4b). 비교에서는 두 시스템에 같은 문자열을 넣어 통제했지만 배포에서는 렌더링도 검증 대상이다.
- **운영**: 로컬 실행, 지연, 토큰 과금 없음, 결정성, 데이터 외부 전송 없음.

### 7.7 타당성 위협

- **플레이그라운드 ≠ API**: 모델 버전 미표기, 확률 2자리 반올림, 서버 측 래핑 가능성, 표시 지연 정의 미공개.
- **소표본**: 과제당 n=40(Wilson 반폭 약 ±0.15), T7은 언어당 20(반폭 약 ±0.2)이다. 차이가 약 0.2보다 작으면 대부분 구분되지 않는다. trained vs Jev도 같은 Jev 항목을 쓰므로 같은 한계를 가진다. T10은 큐당 4행이라 큐별 수치는 방향 신호다. 좁은 구간의 ext는 vanilla vs trained에만 쓴다.
- **다중 비교**: zero-shot 비교는 Holm 보정 후 T1·T7만 유의하다. 보정 전 4/4/0은 탐색적 요약이다. trained vs Jev도 Holm 후 10과제 모두 비유의이고, 보정 전 2/8/0은 탐색적 요약이다.
- **표본 쉬움**: seed 13 표본에서 T3 Jev 0.700 구간은 제3자 공개치 0.480을 포함하지 않고 Laya english 0.750도 upstream 0.573보다 높다. 짝 비교에는 유효하지만 공개치로 일반화하지 않는다.
- **T1 teacher**: 정답은 teacher 분포의 argmax이고 teacher와 Jev의 관계를 확인하지 못했다. Jev의 T1 0.867은 공개치 0.727(2,000 decision, 다른 문항 구성)보다 높아 teacher 정렬 효과를 배제할 수 없다.
- **다문항 공동 평가**: T1에서 Jev는 case의 2\~4문항을 한 요청에서 함께 평가했고 Laya는 질문마다 독립 평가했다.
- **학습 오염**: upstream 표기로 Laya 학습 믹스에 들어간 과제는 T1\~T8 중 T2·T5뿐이고, 3-arm에서 더한 T9·T10도 포함 과제다. 나머지 여섯 과제는 held out이다(`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`, `third_party/laya/BENCHMARKS.md:142`, `:147`). 이 표기는 upstream의 자기 보고이며 학습 데이터 자체는 확인하지 않았다. 포함 과제는 upstream 학습 split과 우리 평가 항목의 중복도 확인할 수 없다(V6의 한계).
- **러너 사후 선택**: 과제별 최고 Laya는 Laya에 유리한 선택이며, 고정 러너 기준 합산도 같은 방향이다(§4.2).
- **입력 표현 제약**: Boolean 설명 없음, Score 5레벨, choice 80자 때문에 T1은 120/200만 비교했고 T4는 key 단독으로 다시 만들었다.
- **파일럿 프로토콜 차이**: 한국어 파일럿은 state로 원문 발화를 넣었고, 질문 문장이 Laya와 약간 다르며, 옵션의 key와 설명을 문자열 하나로 넣었다(Laya는 따로 받는다). 그래서 8과제 종합에서 제외했다(`results/F/jev_playground_manual_20261006.md` §1.2, §5).
- **trained는 run 두 개의 표본**: 같은 설정의 T1 재학습이 test 0.747 대 0.690(b/c 217/98, p=1.7e-11)을 냈고, seed 14 run 2는 0.735였다. 세 run 중 본 학습 run 1이 이탈값이라 T1의 run 1 수치는 학습 효과를 낮게 잡았을 수 있다. 두 run의 판정은 30개 비교 중 27개가 같고 3개가 다르다(모두 n=40 Jev 항목, Holm p 0.05 근처, §5.7). run 2가 8과제만 끝났던 시점에는 T6이 불일치였지만, 10과제 family에서는 T6이 확정(비유의)되고 T4가 불일치가 됐다. 경계 근처의 Jev 항목 판정은 run과 family 크기에 따라 바뀐다. run이 두 개라 run 간 분산은 추정하지 못한다.
- **반복 학습 중 자원 경합**: run 2의 T9는 다른 프로젝트의 실험 프로세스 7개와 겹쳐, 스왑 thrashing으로 시작 뒤 38분 동안 첫 진행 줄을 쓰지 못했다(스왑 32.0 / 32.8 GB, 메모리 여유 11%). 반복 학습 큐만 19:37에 중지했다. 감시자는 조건(그 실험이 3분 연속 없음, 메모리 여유 30% 이상, 디스크 여유 20 GB 이상)이 맞은 2026-10-08 22:58에 T9·T10을 다시 시작했고, 2026-10-09 00:23에 경합 없이 끝났다(T9 첫 진행 줄 209초, run 1 214초). 앞 과제 T6\~T8도 느려졌지만 계산은 타이밍과 무관해 T1\~T8 run 2 결과는 유효하다고 본다. 비용 표는 run 1 값이다(`results/T3arm/PREP_20261008.md` 마지막 두 절, `results/T3arm/rep_s14/autostart.log`).
- **MPS 비결정성**: 데이터 순서, 초기 가중치, RLCD 노이즈가 같아도 MPS 학습은 세 번째 optimizer step 뒤 갈라졌다. 어느 연산이 원인인지 확인하지 않았다(후속 추적: GPU가 빈 뒤 `torch.use_deterministic_algorithms(True, warn_only=True)`로 짧은 run을 돌려 경고 연산 목록 확보).
- **Jev 학습 데이터 미상**: 범주는 Laya 기준으로만 정의된다. Jev가 같은 공개 데이터셋을 학습했다면 Jev의 "zero-shot"이 실제로는 retention일 수 있다.
- **T10 split 겹침 가능성**: T10은 공개 split이 하나뿐이라 hash로 나눈 우리 test 몫이 upstream 학습 데이터에 들어갔을 수 있다. 설계상 확인할 수 없다.
- **보정 refit 혼입**: trained의 temperature는 과제 calib로 다시 맞춘 값이라 trained − vanilla의 보정 차이에 refit 효과가 섞인다(V1). 보정 분리 열로 떼어 보면 ext ECE 개선의 상당 부분이 refit이었다(§5.4). 다만 T1·T8의 분리 기준선은 fitted temperature가 로드 범위 [0.5, 5]에서 잘려, 두 과제의 refit 효과는 작게 잡혔을 수 있다.
- **T10 라벨 품질 의심**: Jev 항목 40행에서 네 시스템(Jev, vanilla english, vanilla multilingual, trained)이 모두 틀린 행이 18/40이고, Customer Service와 Human Resources는 네 시스템 모두 0/4다. 오답 다수에서 gold 큐가 질문에 준 큐 설명과 맞지 않는다는 판단은 티켓을 읽고 내린 해석이다. 라벨 품질이 의심되므로 수작업 확인이 필요하고, 그 전까지 T10 결과를 라우팅 능력으로 읽지 않는다(3-arm 종합 §1.6, `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md` §3.6).
- **dev 기준선 오염**: 학습 믹스 포함 과제 중 dev를 train split에서 뗀 과제(T2, T5, T9)와 split이 하나뿐인 T10에서는 epoch 0 dev가 유효한 vanilla 기준선이 아니다. T5의 학습 실패 표시와 보정 악화가 그 예다. epoch 선택은 trained epoch끼리의 비교라 영향이 작다.
- **V3 엄격 기준 미달**: permuted 0.385가 엄격 기준 0.346을 +0.039 넘었다. 프로젝트 책임자 판정으로 통과(차이 기준)이지만 계획과의 편차다(§3.7).
- **하이퍼파라미터 고정과 예산 축소**: 스크립트 기본값을 모든 과제에 썼고, 예산은 upstream T1 학습의 약 45%다. T6의 train − dev 차이(+0.142)와 T10의 높은 flip(0.175)은 과제별 조정 여지를 시사한다.

### 7.8 연구 중 발견한 upstream 결함과 불일치

`results/REPORT.md` §8에 기록한 7건이다. (1) `laya.calibrate.records_from_labeled`에 `@torch.no_grad()`가 없어 실제 Agent에서 예외가 난다. (2) `laya.evals.evaluate`가 `predict(..., model=)`을 호출해 `Agent.predict`와 호환되지 않는다. (3) `hf download`의 agent 모드 출력 접두어로 문서의 다운로드 명령이 깨진다(`--quiet` 필요). (4) 모델 카드의 한국어 0.490은 다른 실행(T4, n=300)의 값이고 공식 표는 0.470이다. (5) "multilingual의 criteria 없는 noul은 state를 읽는다"는 README 주장이 한국어와 그 영어 번역 모두에서 성립하지 않았다. (6) MASSIVE HF 미러의 license 태그(apache-2.0)가 원 저장소(CC BY 4.0)와 다르다. (7) examples 문서의 MPS 첫 호출 13 s는 이 머신에서 0.1 s였다.

## 8. 결론 및 향후 과제

같은 입력으로 비교하면, 학습 없이 바로 쓸 때의 정확도와 다국어 일관성은 Jev가 앞선다. Jev는 T1\~T8 중 4개 과제에서 유의하게 앞섰고(Holm 후 2개), 나머지 4개에서는 구분되지 않았으며, Laya가 유의하게 앞선 과제는 없었다. S7의 T9는 모두 천장이고 T10은 모두 낮아 비유의다. 과제 라벨로 Laya를 과제마다 파인튜닝하면 이 격차는 사라진다. 두 run 기준으로 Holm 보정 후 Jev가 trained보다 유의하게 앞선 비교는 없다(보정 전에는 run 2의 T5에서 Jev가 앞섰다, b/c 1/10, p=0.0117). trained vs Jev는 T8을 뺀 9과제에서 두 run 모두 비유의로 확정됐고, T8은 run 1 비유의, run 2 trained 우세로 불일치한다. 30개 비교 가운데 확정 27, 불일치 3이고, 불일치는 모두 Holm p가 0.05 근처인 n=40 Jev 항목 비교다. 학습 이득은 upstream이 학습하지 않은 과제에 몰렸다(ext 제외 범주 +0.252, 포함 범주 +0.017, run 2는 +0.257과 +0.020). 학습 제외 6과제의 ext 이득은 두 run 모두 유의했고, 포함 과제에서는 vanilla가 이미 그 분포를 봐 이득의 상한이 낮다. 보정은 정확도와 따로 읽어야 한다. ext에서 trained의 ECE 개선 상당 부분은 과제 calib로 temperature만 다시 맞춘 효과였고, 학습 효과로 읽을 수 있는 과제는 T4·T8이다. 전문화 비용은 과제당 라벨 약 6,400개, M4 Pro 학습 1.4\~43.3분, 체크포인트 0.68\~0.85 GB이고, 학습 파이프라인은 검증 V1\~V6을 통과했다(V3는 차이 기준). 다만 같은 파이프라인의 T1 세 run이 0.690\~0.747로 갈려 trained 수치의 run 간 편차가 작지 않다. 따라서 선택 기준은 v2와 같은 축에서 더 구체적이 된다. "학습 데이터 없이 즉시 넓은 형식을 다뤄야 하는가"는 Jev에 유리하고, "과제마다 라벨 수천 개를 만들 수 있고 지연·비용·데이터 경계가 중요한가"는 trained Laya에 유리하다. 어느 쪽이든 확신도 임계값은 과제별로 다시 맞춰야 한다.

**프로젝트 책임자 결정(2026-10-08 15:25)과 진행 상황.** 본 학습은 기본값(프로젝트 책임자 확인 전)으로 시작했다(§3.6). 그 뒤 프로젝트 책임자가 다섯 항목을 결정했다(`results/T3arm/PREP_20261008.md` "프로젝트 책임자 결정" 절).

- 확정: V3는 차이 기준으로 통과다. 엄격 기준 미달은 계획과의 편차로 남긴다(§3.7).
- 확정: T8은 hold-out(dev 60 + calib 40 + train 444)을 유지하고 2 epoch로 학습한다. 이 판의 수치가 그 설정이다.
- 완료: 보정 분리 열(vanilla + 과제 temperature, `results/T3arm/calib_sep/`). 결과는 §5.4다. ECE 개선을 학습 효과로 읽는 범위는 T4·T8(그리고 T7의 일부)로 한정한다.
- 완료: T9·T10의 Jev 측정(80 요청, 세션 S7, `results/F/jev_cmp/sessions/S7_20261008/`). 결과는 §4 서두와 §5.1이다. Q1 DiD는 +0.179 [−0.008, +0.356]으로 아직 판정하지 않는다.
- 완료: 반복 학습 1회(seed 14, 10과제, `results/T3arm/rep_s14/`). 30개 비교 중 27개가 두 run에서 같은 판정으로 확정됐고 3개가 불일치다(§5.7). T1에서는 본 학습 run 1이 이탈값으로 드러났다. T9는 자원 경합으로 한 번 중지했다가 경합이 없을 때 다시 돌렸다(§7.7).

향후 과제는 다음과 같다. (1) Jev 공식 API로 표본을 키운 동일 프로토콜 재측정과 확정 단가 기반 비용 비교. 한국어 라우팅에서 ft-v1과의 우열은 500행 규모 paired 비교가 있어야 판정된다(`results/REPORT.md` §8). (2) 언어와 과제 형식 확대(부정문, 고카디널리티, 장문 등 미실행 형식). (3) LLM zero-shot 베이스라인 추가. (4) 과제별 라벨 수 곡선(과제당 500 / 2,000 / 5,000 라벨)으로 몇 개의 라벨이면 Jev에 도달하는지 정량화(`docs/11_three_arm_plan.md` 열린 질문 7). (5) T1 teacher의 정체와 Jev와의 관계 확인. (6) MPS 학습의 비결정 연산 식별과 결정적 학습 경로 확보. (7) upstream 수준 예산(약 22,400 item-pass, context 1,024)으로 T1 0.766 재현(같은 문서 열린 질문 5). (8) T10 gold 라벨의 수작업 점검과 큐 라벨 생성 방식 확인(S7에서 네 시스템이 모두 틀린 행 18/40).

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
17. V. Metsis, I. Androutsopoulos, G. Paliouras. Spam Filtering with Naive Bayes – Which Naive Bayes? CEAS 2006(Enron-Spam). HF `SetFit/enron_spam`(원 코퍼스와의 관계 확인 필요).
18. Tobi-Bueck, *customer-support-tickets* 데이터셋. Hugging Face Hub, revision ddf1c81. 서지와 라이선스 확인 필요.

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

3-arm 확장은 다음 순서로 재현한다. 준비와 학습 검증(S0·S1)의 전체 명령은 `results/T3arm/PREP_20261008.md` "명령어" 절에 실행 순서대로 있다.

```bash
source env.sh
# S2 본 학습 (MPS GPU, 약 4시간). 시작 게이트는 poc/finetune/READY_T3ARM의 sha256
PREFLIGHT_ONLY=1 bash poc/finetune/run_all_tasks.sh   # 게이트 점검만 (READY sha256, 남은 체크포인트, vanilla 리포트, 디스크)
SMOKE=1 bash poc/finetune/run_all_tasks.sh            # 10과제 전 단계, 과제당 64 items x 1 epoch, 임시 디렉터리
bash poc/finetune/run_all_tasks.sh                    # T1-T10 학습, epoch 선택, Jev 항목·ext 평가, 진단, 정리
# S3 종합 (모델 로드 없음, 리포트와 로그만 읽음)
nice -n 10 .venv/bin/python results/T3arm/t3arm_summary.py build --root results/T3arm --out results/T3arm
nice -n 10 .venv/bin/python results/T3arm/t3arm_summary.py verify --root results/T3arm --out results/T3arm
# 보정 분리 열 (0-step export와 평가, 학습 없음)
bash poc/finetune/t3arm_calib_sep.sh
# 반복 학습 run 2 (seed 14, 결과는 results/T3arm/rep_s14/)
env SEED=14 RUN_TAG=rep_s14 bash poc/finetune/run_all_tasks.sh
# run 2의 T9·T10 재시작 (감시자 poc/finetune/autostart_rep_t9t10.sh가 2026-10-08 22:58에 실행)
SEED=14 RUN_TAG=rep_s14 TASKS="T9 T10" bash poc/finetune/run_all_tasks.sh
# S7 Jev 세션 분석 (사이트 요청 없음, 기록만 읽음)
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S7 T9_enron_spam_40
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S7 T10_support_tickets_queue_40
```

S2의 결과는 `results/T3arm/<task>/`와 `results/T3arm/run_all_status.log`에 쌓이고 선택 체크포인트는 `poc/finetune/ckpt_t3arm/<task>/`(공개 저장소에는 포함하지 않음)에 남는다. MPS 학습은 비트 단위로 결정적이지 않아 S2를 다시 돌리면 다른 trained 모델이 나온다(§5.6). 보존한 체크포인트의 평가와 S3는 결정적이다.

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

3-arm 확장(2026-10-08)의 Jev 요청은 세션 S7의 80회(T9 40 + T10 40)이고 모두 HTTP 200이었다. 5xx, 429, 제한 문구, captcha와 재시도는 0건이고, 요청 body = 폼 payload 80/80, Model ID `typesafe-ai/jev` 80/80이다. 사이트 누적은 518회(438 + 80), 마스터 로그는 491줄이다(`results/F/jev_cmp/sessions/S7_20261008/S7_run_card.md`).

## 부록 D. 08 문서와의 관계

`docs/08_paper_ko.md`는 같은 프로젝트의 앞선 보고서로, 질문을 "Laya를 한국어 서비스에 쓸 수 있는가"로 두고 한국어 적용성(재현, 한국어 지원 감사, zero-shot 품질, 파인튜닝, PoC)을 다뤘다. 그 문서의 Jev 비교는 n=24 한국어 파일럿 하나였다(08 §4.8). Laya와 Jev의 성능 비교라는 질문에 대해서는 본 문서가 08을 대체하며, 08의 한국어 결과는 본 문서 §6의 사례 연구로 요약해 포함했다.

[English](10_paper_laya_vs_jev.md) | **한국어**
