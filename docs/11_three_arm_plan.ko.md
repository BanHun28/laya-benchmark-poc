# 11. 3-arm 확장 계획: Jev vs vanilla Laya vs trained Laya

**목적**: 09의 Laya vs Jev 비교에서 vanilla Laya의 열세에는 두 요인이 섞여 있다. 하나는 Laya가 학습 때 본 과제의 유지(retention)이고, 다른 하나는 처음 보는 과제의 zero-shot 일반화다. 이 둘을 Laya 학습 믹스 기준의 과제 범주로 나눈다. 과제 데이터로 파인튜닝한 Laya(trained)를 세 번째 arm으로 더해 "학습시키면 Jev를 따라잡는가"와 "Laya가 제대로 학습되었는가"를 측정으로 답한다.

**선행 문서**: `09_laya_vs_jev_plan.md` §3-§5와 §10(과제 T1-T8, 프로토콜 동일성, 지표, 결론), `05_poc_plan.md` §6 P4(파인튜닝 파이프라인과 한국어 ft-v1 결과), `03_benchmark_plan.md` §3-§4(공통 프로토콜, 지표 정의), `06_templates.md` §1(run card). 근거 결과는 `results/F/jev_cmp/summary.md`, `results/P4/P4_probe_20261002.md`, `results/P4/full_20261003-1156_timing.json`이다.

**산출물**:
- 학습 스크립트: 길이 패치한 `poc/finetune/laya_finetune_mps_patched.py`. upstream과의 diff는 `results/T3arm/finetune_script.diff`.
- 학습 데이터: 빌더 `scripts/build_train_sets.py`와 `poc/finetune/data/`의 과제별 train/dev/calib.
- 평가 세트: T9·T10 Jev 형식 세트(`data/evals/jev_cmp/`에 새 파일만 추가)와 확장 평가셋 `data/evals/jev_cmp_ext/`.
- 본 학습: 드라이버 `poc/finetune/run_all_tasks.sh`, 게이트 `poc/finetune/READY_T3ARM`, 과제별 선택 체크포인트 `poc/finetune/ckpt_t3arm/<task>/`(공개 저장소에는 포함하지 않음).
- 결과: `results/T3arm/`(준비 run card, validity/, vanilla/, 과제별 리포트, summary.md·json, 그림)와 갱신된 `results/REPORT.md`·대시보드·소논문 v3.

---

## 1. 목적과 질문

**프로젝트 책임자 결정(2026-10-08).**
- 학습 base는 Router가 고르는 base다. 영어 과제는 english, T7은 multilingual이다.
- 과제당 예산은 최대 5,000 items × 2 epoch다.
- Laya 학습 믹스에 들어 있던 과제 2개(T9, T10)를 더한다.
- Jev는 T1-T8 데이터가 이미 있으므로 **다시 돌리지 않는다**. T9·T10의 Jev 측정(80 요청)은 Laya 결과를 본 뒤 정한다. (2026-10-08 실행: T9·T10은 세션 S7에서 측정, §9 참고)

T8은 dev 60과 calib 40을 train에서 떼어 두고(hold-out) 나머지 444행 전량을 2 epoch로 학습했다. 본 학습 시작 때 기본값으로 적용했고 프로젝트 책임자가 확정했다(2026-10-08, 열린 질문 2·10).

| 질문 | 내용 | 판정 근거 |
|---|---|---|
| Q1 | vanilla Laya의 Jev 대비 열세는 학습 제외 과제에서만 나타나는가 | 범주별 (Jev − vanilla)와 두 범주의 차이(difference-in-differences) |
| Q2 | 과제 데이터로 파인튜닝하면 두 범주 모두에서 Jev에 도달하거나 넘어서는가 | Jev 항목에서 trained vs Jev paired exact McNemar, 범주별 macro |
| Q3 | 전문화(specialisation) 비용은 얼마인가 | 과제별 라벨 수, M4 Pro 학습 시간(분), 체크포인트 크기 |
| Q4 | Laya가 제대로 학습되었는가 | §4 학습 검증 V1-V6 통과 여부와 학습 진단 |

현재 상태(학습 없음)는 아래와 같다(`results/F/jev_cmp/summary.md` §2). vanilla는 영어 과제에서 english, T7에서 multilingual이다. T1은 Jev와 비교 가능한 120 decisions 기준이다.

| arm | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 |
|---|---|---|---|---|---|---|---|---|
| Jev | 0.867 | 0.875 | 0.700 | 0.925 | 0.925 | 0.650 | 0.910 | 0.775 |
| vanilla | 0.383 | 0.975 | 0.750 | 0.725 | 0.725 | 0.425 | 0.620 | 0.775 |

지금은 학습 믹스 포함 과제가 T2·T5 두 개뿐이라 Q1의 범주가 불균형하다. T9·T10을 더하면 포함 4개 대 제외 6개가 된다.

## 2. 설계

**범주.** upstream이 밝힌 학습 믹스로 나눈다.

| 범주 | 과제 | 근거 |
|---|---|---|
| Laya 학습 믹스 포함 | T2 AG News, T5 BoolQ, **T9 Enron spam(신규, noul)**, **T10 고객지원 티켓 큐 라우팅(신규, 10-way choice)** | `third_party/laya/research/scripts/build_benchmark_nb.py:760`, `third_party/laya/BENCHMARKS.md:142`(Email spam, in training), `:147`(Support triage, in training). `third_party/laya/`는 upstream clone이다(공개 저장소에는 포함하지 않음, https://github.com/NandhaKishorM/laya 를 commit 4aa6761로 clone해 재현) |
| Laya 학습 제외(held out) | T1 typed-decisions, T3 Emotion, T4 Banking77-10, T6 SST-5, T7 MASSIVE intent-10 × 5개 언어, T8 prompt-injections | `build_benchmark_nb.py:761-762` "sst5, emotion, prompt_injections, banking77 were held out. Neither checkpoint trained on typed-decisions, MASSIVE or XNLI." |

**신규 과제 정의.** 두 과제 모두 upstream Themes 벤치마크의 문구를 그대로 쓴다.
- T9는 `SetFit/enron_spam`이다. state는 `laya.email_state(subject, message[:3000])`이고 noul 질문은 "Is this email unsolicited spam or bulk marketing?"이다(`third_party/laya/research/scripts/bench_apps.py:159-168`).
- T10은 `Tobi-Bueck/customer-support-tickets`에서 language가 en이고 10개 큐에 속하며 body가 있는 행이다. state는 subject와 body[:3000]이다. choice 질문은 "Which support queue should handle this ticket?"이고 criteria는 upstream의 큐 설명 10개다(`bench_apps.py:130-155`).

**3×2 설계.**

| arm \ 범주 | 학습 믹스 포함 (T2, T5, T9, T10) | 학습 제외 (T1, T3, T4, T6, T7, T8) |
|---|---|---|
| Jev (zero-shot, 플레이그라운드) | T2·T5 측정됨, T9·T10 미측정(결정 대기) (2026-10-08 실행: T9·T10은 세션 S7에서 측정, §9 참고) | 측정됨 |
| vanilla Laya (zero-shot) | T2·T5 측정됨, T9·T10 신규 측정 | 측정됨 |
| trained Laya (과제별 파인튜닝) | 신규 | 신규 |

**arm 정의.**
- **Jev.** 09의 플레이그라운드 결과(`results/F/jev_cmp/jev_runs_all.jsonl`, 공개 저장소에는 포함하지 않음)를 그대로 쓴다. 새 요청은 없다. (2026-10-08 실행: T9·T10은 세션 S7의 새 요청 80회, §9 참고)
- **vanilla Laya.** trained와 같은 base를 학습 없이 쓴다. base를 맞춰야 trained − vanilla가 순수한 학습 효과가 된다. Router와 반대쪽 base는 참고 열로 보고한다. T1-T6은 Router가 전부 english를 골라 Router 열이 vanilla 열과 같다. T7은 en 20행과 de 5행을 english로, 나머지 75행을 multilingual로 보낸다. T8은 14/40행을 multilingual로 보낸다. 그래서 T7·T8의 Router 열은 vanilla와 다르다(`results/F/jev_cmp/summary.md:44`).
- **trained Laya.** 과제마다 base 하나를 따로 파인튜닝한다. T7은 5개 언어를 함께 학습한 multilingual 모델 하나다. 평가 경로는 vanilla와 같다(CPU fp32, intra-op 10 / inter-op 1, batch 8).

**평가 항목.** 두 층으로 나눈다.

| 층 | 용도 | 구성 |
|---|---|---|
| Jev 항목 | 3-arm 직접 비교(Jev와 같은 바이트의 입력) | T1 40 case / 200 decisions(Jev 비교는 120), T2-T6·T8 각 40, T7 20 id × 5개 언어 = 100. T9·T10은 같은 규칙의 Jev 형식 40개와 플레이그라운드 폼만 만들고 요청은 하지 않음 (2026-10-08 실행: 세션 S7에서 요청, §9 참고) |
| 확장 세트(ext) | vanilla vs trained의 좁은 CI | T2-T6·T9·T10 각 500(평가 split에서 층화, seed 13, 학습 행과 겹침 제외), T1 typed-decisions test 전체 400 case / 2,000 decisions, T7 100 id × 5개 언어 = 500(언어 간 같은 id), T8 test 전체 116 |

평가 split은 대부분 test다. T5는 test split이 없어 validation을 쓴다. T10은 hash로 나눈 test 몫을 쓴다.

## 3. 학습 데이터 구성

**형식 동일성.** 학습 item은 평가 세트와 같은 질문 문구, criteria 텍스트, 옵션 렌더링, state 직렬화로 만든다(`scripts/build_jev_cmp_sets.py`의 과제별 함수를 재사용). T4와 T7은 평가처럼 gold + 9 distractor를 행마다 뽑은 10 옵션이다. T4는 key-only, T7은 `key: key spaced` 렌더링이다.

upstream `build_training_item`(`third_party/laya/notebooks/laya_finetune_typed_decisions_mps.py:58-101`)은 모든 형식의 gold를 `{"probabilities": {...}}` 분포로 받는다. key는 choice가 옵션 key, noul이 "false"/"true", score가 "0".."n-1"이다. T1은 데이터셋의 teacher 분포를 그대로 쓰고, 나머지 과제는 one-hot이다. 스크립트는 marker 수가 옵션 수와 다른 item을 조용히 버린다(`:91-92`). 그래서 빌더가 버려진 수를 과제별로 기록한다.

행 수는 `data/raw/hf` 캐시(공개 저장소에는 포함하지 않음)의 dataset_info 기준이다. dev와 calib는 서로소다. validation split이 있으면 거기서 뽑고, 없으면 train에서 떼어 낸 held-out 조각에서 뽑는다. dev는 epoch 선택에만, calib는 temperature fit에만 쓴다.

| 과제 | train 소스(행) | train items | dev(최대 1,000) | calib(400) |
|---|---|---|---|---|
| T1 | `LocalLLaMA/typed-decisions` all train(1,200 case) | dev·calib case를 뗀 뒤 최대 5,000 decisions(case 단위) | train case 일부 | train case 일부 |
| T2 | `fancyzhx/ag_news` train(120,000) | 5,000(라벨 층화) | train 잔여 | train 잔여 |
| T3 | `dair-ai/emotion` split train(16,000) | 5,000(라벨 층화) | validation(2,000) | validation |
| T4 | `mteb/banking77` train(9,993) | 5,000(77 라벨 층화, 10 옵션) | train 잔여 | train 잔여 |
| T5 | `google/boolq` train(9,427) | 5,000(라벨 층화) | train 잔여(validation은 평가 소스) | train 잔여 |
| T6 | `SetFit/sst5` train(8,544) | 5,000(레벨 층화) | validation(1,101) | validation |
| T7 | `mteb/amazon_massive_intent` en·de·ja·zh-CN·ko train | 언어당 1,000 = 5,000(10 옵션) | validation | validation |
| T8 | `deepset/prompt-injections` train(546) | dev·calib를 뺀 전량(444) × 2 epoch | train 일부(60) | train 일부(40, min(400, N//10) 이하) |
| T9 | `SetFit/enron_spam` train(31,716) | 5,000(라벨 층화) | train 잔여 | train 잔여 |
| T10 | `Tobi-Bueck/customer-support-tickets` train(61,765, 전 언어) | 영어·10개 큐 행을 hash로 train/dev/test로 나눈 뒤 train 몫에서 5,000 | dev 몫 | dev 몫(dev와 서로소) |

**옵션 순서 셔플 증강.** train item은 P4와 같이 행마다 criteria 순서를 섞는다(`poc/finetune/make_domain8_items.py`의 `--shuffle-options all`). 섞는 대상은 choice 질문뿐이다. score는 레벨 순서 자체가 의미이고 noul은 옵션이 고정이다. dev와 calib는 원래 순서다. P4에서 이 방식으로 dev flip이 zero-shot 0.270(`results/C/C1_option_order_20261002.md:9`)에서 0.037(`results/P4/metrics/full_20261003-1156_option_order_dev.md:9`)로 줄었다.

**calib 배치.** 스크립트는 items를 `random.Random(20260922)`로 섞고, 섞인 순서의 앞 `min(--calib-max, N//10)`개를 calib로 쓴다(`:258-261`). P4 어댑터처럼 calib 행을 그 위치에 미리 놓아 train 행이 calib에 쓰이지 않게 한다.

**누수 제거.** train·dev·calib 행 가운데 평가 항목(Jev 항목과 ext 전체)과 state 텍스트가 같은 행을 제거한다. 정확 일치와 공백·대소문자 정규화 후 일치를 모두 본다. 과제별 제거 수를 기록한다. P4에서는 MASSIVE ko 2,917행 평가 세트 중 155행이 학습 파일의 state와 글자 그대로 겹쳤고, 그 행의 ft-v1 정확도는 0.994였다(`results/P4/metrics/full_20261003-1156_overlap.md`).

## 4. 학습 검증 (Q4: 제대로 학습했는가)

| ID | 검증 | 방법 | 통과 기준 |
|---|---|---|---|
| V1 | zero-step identity | 패치한 파이프라인으로 optimizer step 0인 export를 base별로 만든다(epochs 0이나 lr 0, 불가하면 가장 가까운 방법과 이유를 기록). 가중치를 base와 비교하고 세트 하나를 평가한다 | 가중치 bit 일치(base가 fp16이고 export도 `.half()`, `:225`). argmax 100% 일치. config 차이를 목록으로 기록. base temperature로 되돌린 평가에서 확률도 일치 |
| V2 | upstream 재현 | (a) `models/laya-typed-decisions`(공개 저장소에는 포함하지 않음)를 T1 ext 2,000 decisions로 평가. (b) 우리 파이프라인으로 english base를 T1 train 최대 5,000 decisions × 2 epoch 학습해 같은 2,000으로 평가 | (a) 정확도가 공개 0.766의 ±0.02 안. soft acc 0.471, Brier 0.061, score MAE 0.242와의 차이도 기록(`BENCHMARKS.md:172`). (b) 0.562(vanilla english 0.362 + 0.20, `:173`) 이상이고 majority 0.461(`:187`) 초과 |
| V3 | label-shuffle 대조 | T3 Emotion, english base, 5,000 items의 라벨을 seed 13으로 섞어 1 epoch 학습 | dev 정확도가 majority + 0.05 이하. 실제 라벨 T3 학습의 epoch 1 dev 정확도보다 0.30 이상 낮음 |
| V4 | 형식 동일성 | 과제마다 train item 20개를 tokenizer로 decode해 같은 state·질문의 추론 시퀀스(`build_sequence`)와 비교 | 원래 순서 item은 토큰 단위 일치, 셔플 item은 옵션 집합과 gold slot 일치. 둘 다 100% |
| V5 | smoke | base별(english, multilingual) 200 items × 1 epoch를 학습, export, `laya.load`, 평가까지 돌린다. `run_all_tasks.sh`는 `SMOKE=1`(과제당 64 items, 1 epoch, 임시 디렉토리)로 10과제 전부 | 모든 STEP OK. base별 item/s를 기록해 §6 시간 추정을 갱신 |
| V6 | 누수 | §3 규칙 적용 뒤 train·dev·calib와 평가 항목의 교집합 | 정확 일치·정규화 일치 모두 0. 학습 믹스 포함 과제는 upstream 학습 split과의 중복을 확인할 수 없다는 점을 따로 표기 |

**V1이 잡는 차이.** export는 다음 네 가지를 바꾼다. 이것이 trained − vanilla에 섞이면 안 된다.
- `max_len`·`head_max_len`: 패치 전에는 1024/256으로 하드코딩된다(`:240`). english base 값은 512/192다(`models/laya/rl_agent_config.json`).
- `model_name`: "laya-typed-decisions"로 하드코딩된다(`:358`).
- `temperature`: 과제 calib로 형식별 값을 다시 맞춘다. calib에 없는 형식은 1.2가 된다(`:354-359`).
- `temperature_by_options`: 삭제된다(`:361`). vanilla english는 형식별 값과 옵션 수 구간별 값을 싣고, multilingual은 전부 1.0이다.

temperature는 질문 하나의 argmax를 바꾸지 않으므로 정확도 비교는 영향을 받지 않는다. 보정 비교에는 영향이 있다(§5).

**V2 해석.** (a)는 우리 평가 경로가 upstream 수치를 재현하는지 본다. (b)는 재현이 아니라 줄인 예산에서 학습이 작동하는지 본다. upstream은 약 30k questions × 4 epoch로 학습했다(`third_party/laya/README.md:1532`). 그래서 (a)와 (b)의 차이는 예산 차이로 읽고 수치로 기록한다.

**학습 진단.** 과제마다 다음을 기록한다.
- 손실 창(window) 곡선과 train 정확도 창 곡선.
- dev 정확도: epoch 0(= vanilla), 1, 2.
- 선택 epoch과 train−dev 차이(과적합).
- temperature fit 값과 clamp 도달 여부. fit은 학습 스크립트 `:218`에서 [0.1, 10]으로 자르고, 추론은 checkpoint 로드 때 [0.5, 5]로 자른다(`third_party/laya/laya/common.py:706-707`, `:765-766`).
- dev 40개의 옵션 순서 flip(`scripts/probe_option_order.py`).
- 클래스별 recall 변화.

epoch은 dev 정확도로 고르고, 동률이면 앞 epoch을 고른다. epoch 사본에는 base temperature와 `temperature_by_options`가 그대로 남아 있다(P4 `poc/finetune/ckpt_domain8_v1/epoch_1`(공개 저장소에는 포함하지 않음) 확인). 그래서 마지막이 아닌 epoch을 고르면 같은 calib로 temperature를 다시 맞춘다. dev가 두 epoch 모두 vanilla보다 낮으면 그 과제를 "학습 실패"로 표기한다. 형식, 라벨, lr 순으로 원인을 추적한 뒤 재학습 여부를 정한다.

## 5. 지표와 통계

- **3-arm 직접 비교(Jev 항목).**
  - 과제별 정확도와 Wilson 95% CI를 낸다.
  - paired exact McNemar로 trained vs Jev와 trained vs vanilla를 비교한다. vanilla vs Jev는 09 결과를 재사용한다.
  - T1(40 case)과 T7(20 id)은 항목이 독립이 아니므로 cluster bootstrap CI를 함께 낸다.
  - 보조 지표는 09와 같다. T1은 soft accuracy·Brier·score MAE(`results/F/jev_cmp/laya_summary.py`), T5·T8·T9는 AUROC, T6은 MAE다.
- **vanilla vs trained(ext).** 과제별 정확도 차이의 paired bootstrap CI(10,000회)와 exact McNemar를 낸다. T1은 2,000 decisions에서 V2와 같은 지표를 함께 낸다.
- **다중비교.** trained vs Jev 8과제와 trained vs vanilla 10과제에 각각 Holm을 적용한다. (2026-10-08 실행: T9·T10 Jev가 들어와 trained vs Jev와 Jev vs vanilla도 10과제, §9 참고)
- **범주 집계.**
  - arm별·범주별 macro 정확도를 낸다.
  - Q1의 difference-in-differences는 제외 범주의 평균 (Jev − vanilla)에서 포함 범주의 평균을 뺀 값이다. 과제 재표본 bootstrap CI를 붙인다.
  - (trained − vanilla)와 (trained − Jev)도 범주별로 낸다.
  - 포함 범주의 학습 이득은 vanilla가 이미 데이터를 본 만큼 작게 나올 수 있다(retention 상한).
  - Jev가 없는 T9·T10이 Jev 집계에서 빠진다는 점을 표에 표기한다. (2026-10-08 실행: S7로 T9·T10이 Jev 집계에 들어감, §9 참고)
- **보정.** arm별로 Brier, ECE(15 bins), coverage@오류 5%·10%를 낸다. trained의 temperature는 과제 calib로 다시 맞춘 값이다. vanilla english는 upstream이 맞춘 값이고 multilingual은 1.0이다. 그래서 보정 개선에는 temperature refit 효과가 섞인다는 점을 표기한다(열린 질문 4). (2026-10-08 실행: 보정 분리 열로 refit 효과와 학습 효과를 나눔, §9 참고)
- **비용(Q3).** 과제별 라벨 수, 학습 시간(분), item/s, MPS 최대 메모리, 체크포인트 크기를 낸다.
- **학습 진단(Q4).** §4 항목을 과제별 리포트와 summary에 싣는다.

## 6. 실행 순서와 예산

| 단계 | 내용 | GPU | 산출물 |
|---|---|---|---|
| S0 준비 | 학습 스크립트 길이 패치(`max_len`·`head_max_len`·`model_name`을 base config에서 읽기). 학습 데이터, T9·T10 Jev 형식 세트, ext 세트 빌드. vanilla 측정(T9·T10과 모든 ext, english·multilingual·Router). 기존 T1-T8 vanilla 수치를 새 평가 경로로 비트 단위 재현 | 없음(CPU 평가) | `poc/finetune/laya_finetune_mps_patched.py`, `scripts/build_train_sets.py`, `data/evals/jev_cmp_ext/`, `results/T3arm/vanilla/` |
| S1 검증 | V4, V6, V5(두 base), V1, V2(a), V2(b) T1 학습, V3 셔플 라벨 학습, `run_all_tasks.sh` `SMOKE=1` | 약 0.8-1.7시간 | `results/T3arm/validity/`, `results/T3arm/PREP_<date>.md`, `poc/finetune/READY_T3ARM` |
| S2 본 학습 | `run_all_tasks.sh`가 T1-T10을 순서대로 처리. 과제마다 학습, epoch별 dev 평가와 epoch 선택, Jev 항목·ext 평가, 진단 기록, 선택 체크포인트만 보존 | 약 3.4-8시간(평가 포함) | `poc/finetune/ckpt_t3arm/<task>/`, `results/T3arm/<task>/`, `results/T3arm/run_all_status.log` |
| S3 종합 | 3×2 표, 통계, 진단, 그림, REPORT·대시보드·소논문 v3 | 없음 | `results/T3arm/summary.md`, `results/T3arm/summary.json`, `results/T3arm/figs/` |

**실행 게이트.** S1이 끝나면 items sha256 목록을 담은 `poc/finetune/READY_T3ARM`을 만든다. S2는 이 파일이 있고 GPU가 비어 있을 때 시작한다(P4의 `poc/finetune/autostart_when_gpu_free.sh`와 같은 감시 방식). 드라이버는 `STEP <task>:<step> OK|FAILED`를 `results/T3arm/run_all_status.log`에 남긴다. 마지막 줄은 `RUN_ALL FINISHED` 또는 `RUN_ALL FAILED`다.

**처리량 가정.**
- P4 본 학습은 GPU 유휴 상태에서 multilingual로 11,094 items × 3 epoch를 2,150 s에 마쳤다. train loop 기준 15.58 item-pass/s다(`results/P4/full_20261003-1156_timing.json`). 그때 시퀀스는 207-266 토큰이었다(`results/P4/P4_probe_20261002.md:57`).
- english encoder는 층 수가 28 대 22로 1.3배다. 층 구성으로 계산한 비임베딩 파라미터는 약 343M 대 110M으로 3.1배다(`models/laya/encoder/config.json`, `models/laya-multilingual/encoder/config.json`).
- 그래서 같은 길이에서 english는 1.3-3.1배 느리다고 본다(5-12 item/s). 입력이 최대 512 토큰인 과제는 그 절반으로 둔다.
- 하한은 프로젝트 책임자 선택지와 지시서의 2-3.5시간과 맞는다. 상한은 그 두 배를 넘는다.
- V5가 base별 item/s를 재면 S2 시작 전에 아래 표를 갱신한다.

| 항목 | item-pass | 처리량 가정(item/s) | 예상 |
|---|---|---|---|
| 짧은 입력 영어 과제(T2, T3, T4, T6) | 과제당 10,000 | 5-12 | 과제당 14-33분 |
| 긴 입력 영어 과제(T1, T5, T9, T10) | 과제당 10,000 | 2.6-6.3 | 과제당 26-64분 |
| T7(multilingual) | 10,000 | 약 15.6(P4 측정) | 약 11분 |
| T8(english) | 약 1,300-1,640 | 5-12 | 2-6분 |
| S1의 V2(b), V3, smoke | 10,000 + 5,000 + 소량 | 위와 같음 | 약 0.8-1.7시간 |
| 평가(CPU, 과제당 dev 2회 + Jev 항목 + ext) | | | 과제당 3-8분 |
| 합계 | | | S1 약 0.8-1.7시간, S2 약 3.4-8시간 |

**디스크.** 2026-10-08 여유 공간은 54 GB다.
- 학습 중 english 과제 하나는 최종본, `checkpoint_latest`, epoch 사본 2개로 약 3.4 GB까지 쓴다. english 가중치는 843 MB이고, P4 multilingual은 3 epoch에서 3.2 GB를 썼다.
- 과제 평가가 끝나면 epoch 사본과 `checkpoint_latest`의 sha256을 기록하고 지운다. 선택 체크포인트 하나만 남긴다(english 약 0.85 GB, multilingual 약 0.68 GB). 남는 총량은 약 8.3 GB다.
- V1 export와 V2(b)·V3 모델은 수치를 기록한 뒤 지운다.
- 준비 단계는 여유 25 GB 이상을 지킨다. 드라이버는 과제 시작 전 여유가 15 GB 미만이면 멈춘다.

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `poc/finetune/laya_finetune_mps_patched.py`, `results/T3arm/finetune_script.diff` | upstream 스크립트 사본과 최소 diff(길이·model_name을 base config에서 읽음) |
| `scripts/build_train_sets.py`, `poc/finetune/data/` | 과제별 train/dev/calib JSONL, items `.pt`, provenance, 누수 제거 기록 |
| `data/evals/jev_cmp/` T9·T10 새 파일 | Jev 형식 40개 세트, `_playground.json` 폼, MANIFEST 항목(기존 항목 sha256 불변 확인) |
| `data/evals/jev_cmp_ext/` | 과제별 ext 세트와 MANIFEST |
| `poc/finetune/run_all_tasks.sh`, `poc/finetune/READY_T3ARM` | 본 학습·평가·정리 드라이버(`SMOKE=1` 지원)와 실행 게이트 |
| `poc/finetune/ckpt_t3arm/<task>/` | 과제별 선택 체크포인트(공개 저장소에는 포함하지 않음) |
| `results/T3arm/` | `PREP_<date>.md`, validity/, vanilla/, `<task>/`(학습 로그, dev 곡선, 리포트), `run_all_status.log`, summary.md·json, figs/ |
| `results/REPORT.md`, `results/dashboard/index.html`, 소논문 v3 | 3×2 결과 반영 |

## 8. 리스크와 해석상 주의

| 리스크 | 영향 | 대응 |
|---|---|---|
| Jev의 학습 데이터를 알 수 없음 | Jev가 같은 공개 데이터셋을 봤다면 "Jev zero-shot"이 실제로는 retention일 수 있음 | 범주는 Laya 기준으로만 정의된다고 명시 |
| trained arm은 라벨을 씀 | zero-shot 비교가 아니라 전문화 비교 | 표와 문장에 "라벨 N개 + M분 학습"을 붙임 |
| 포함 과제는 vanilla가 이미 데이터를 봄 | trained − vanilla가 작게 나올 수 있음(retention 상한) | Q1·Q2를 범주별로 읽음 |
| T10은 train split만 있음 | 우리 평가 몫이 upstream 학습 데이터와 겹칠 수 있음(설계상) | hash 분할 규칙과 이 한계를 결과에 표기 |
| Jev 항목은 과제당 n=40 | trained vs Jev의 작은 차이는 판정 불가 | Holm 보정과 cluster bootstrap. ext는 vanilla vs trained에만 사용 |
| base 선택 | T8은 Router가 14/40행을 multilingual로 보내지만 trained는 english 하나로 학습 | Router 기준 고정. 반대 base와 Router는 참고 열 |
| 하이퍼파라미터 고정(스크립트 기본값) | 과제에 따라 과소·과대 학습 | dev 곡선으로 epoch 선택. 실패 과제는 원인 추적 후 재학습 결정(§4) |
| 보정 비교에 temperature 효과가 섞임 | trained의 ECE 개선을 학습 효과로 과대 해석 | 정확도와 보정을 나눠 보고하고 refit 효과를 표기(§5) |
| 시간 추정의 폭이 넓음 | S2가 8시간까지 갈 수 있음 | V5 item/s로 갱신. 무인 실행이라 결과에는 영향 없음 |

## 9. 결과 (S2·S3, 2026-10-08)

S2 본 학습은 2026-10-08 10:57-15:01(약 4.1시간)에 무인으로 돌았다. `results/T3arm/run_all_status.log`는 STEP 148개가 모두 OK이고 FAILED 0이며 마지막 줄이 `RUN_ALL FINISHED`다. 그 뒤 T9·T10의 Jev 80 요청(세션 S7), 보정 분리 열(`results/T3arm/calib_sep/`), seed 14 반복 학습이 끝났고, S3 종합(`results/T3arm/summary.md`·`summary.json`·`figs/`)은 반복 학습이 끝난 뒤 2026-10-09 00:23에 다시 build했다(`t3arm_summary.py verify` 불일치 0). 이 절의 수치는 모두 `summary.json`에서 옮겼고 세부 표는 `summary.md`에 있다. 아래 trained는 run 1(본 학습)이다. 판정은 seed 14 반복 학습(run 2)과 결론이 같은 것만 확정이고, 30개 중 27개가 확정, 3개가 불일치다(아래 "반복 학습").

**Q2. 학습시키면 Jev에 도달하는가.** 유의차 기준으로는 도달한다. trained vs Jev는 10과제 모두 Holm 보정 후 유의차가 없다. T9·T10이 들어와 Holm family가 8과제에서 10과제가 됐고, T1-T8의 Holm 후 판정은 바뀌지 않았다. 보정 전에는 T3(0.950 대 0.700)와 T8(0.975 대 0.775)에서 trained가 유의 우세이고, Jev가 유의하게 앞선 과제는 없다. zero-shot에서 Jev가 Holm 후 유의 우세였던 T1·T7의 격차는 학습 뒤 사라졌다. T7은 0.910으로 같고, T1은 0.792 대 0.867이며 군집 bootstrap 차이 −0.075 [−0.185, +0.025]가 0을 포함한다. 포함 범주의 T5는 0.775 대 0.925로 수치상 Jev가 높다(b/c 2/8, p=0.1094). 범주 평균 trained − Jev는 포함 −0.013 [−0.100, +0.062], 제외 +0.071 [−0.017, +0.163]이다. 과제당 n=40이라 작은 차이는 판정할 수 없다(`results/T3arm/summary.md` §1.1, §1.4, §3.2). 반복 학습까지 보면 trained vs Jev는 9과제가 확정(비유의)이고 T8만 run 2에서 trained 유의 우세라 불일치다. Jev가 Holm 후 유의하게 앞선 과제는 두 run 모두 없다(아래 "반복 학습").

| 과제 | 범주 | Jev | vanilla | trained | trained vs Jev: b/c, p (Holm p) | 판정 (Holm 후) |
|---|---|---|---|---|---|---|
| T1 typed-decisions | 제외 | 0.867 | 0.383 | 0.792 | 10/19, 0.1360 (0.9523) | 비유의 (비유의) |
| T2 AG News | 포함 | 0.875 | 0.975 | 0.950 | 3/0, 0.2500 (1.0000) | 비유의 (비유의) |
| T3 DAIR Emotion | 제외 | 0.700 | 0.750 | 0.950 | 11/1, 0.0063 (0.0635) | trained 유의 우세 (비유의) |
| T4 Banking77-10 | 제외 | 0.925 | 0.725 | 0.950 | 3/2, 1.0000 (1.0000) | 비유의 (비유의) |
| T5 BoolQ | 포함 | 0.925 | 0.725 | 0.775 | 2/8, 0.1094 (0.8750) | 비유의 (비유의) |
| T6 SST-5 | 제외 | 0.650 | 0.425 | 0.675 | 6/5, 1.0000 (1.0000) | 비유의 (비유의) |
| T7 MASSIVE intent-10 | 제외 | 0.910 | 0.620 | 0.910 | 7/7, 1.0000 (1.0000) | 비유의 (비유의) |
| T8 prompt-injections | 제외 | 0.775 | 0.775 | 0.975 | 9/1, 0.0215 (0.1934) | trained 유의 우세 (비유의) |
| T9 Enron spam | 포함 | 1.000 | 1.000 | 0.975 | 0/1, 1.0000 (1.0000) | 비유의 (비유의) |
| T10 support tickets | 포함 | 0.250 | 0.300 | 0.300 | 5/3, 0.7266 (1.0000) | 비유의 (비유의) |

T10은 네 시스템(Jev, vanilla english, vanilla multilingual, trained)이 모두 틀린 행이 18/40이다. 라벨 품질이 의심되어 수작업 확인이 필요하다(`results/T3arm/summary.md` §1.6, 열린 질문 12).

**Q1. vanilla의 열세는 학습 제외 과제에서만 나타나는가.** 방향은 그렇지만 Jev 항목의 구간은 0을 겨우 포함한다. Jev − vanilla는 포함 범주(T2·T5·T9·T10) +0.013, 제외 범주 +0.191이고, difference-in-differences는 +0.179 [−0.008, +0.356]이다. 학습 이득(ext의 trained − vanilla)은 범주 차이가 뚜렷하다. 포함 범주 +0.017, 제외 범주 +0.252, 차이의 차이 +0.235 [+0.147, +0.316]이다. 학습 제외 6과제는 Holm 후 모두 유의하게 오르고, 포함 과제는 T10만 유의하게 오른다(T2·T5·T9 비유의). 이득은 upstream이 학습하지 않은 과제에 몰리고, 포함 과제의 작은 이득은 retention 상한(§2, §5)과 맞는다(`results/T3arm/summary.md` §2.1, §3).

| 기준 | 차이 | 포함 평균 [95%] | 제외 평균 [95%] | 제외 − 포함 [95%] |
|---|---|---|---|---|
| Jev 항목 | Jev − vanilla | +0.013 [−0.075, +0.138] | +0.191 [+0.054, +0.330] | +0.179 [−0.008, +0.356] |
| Jev 항목 | trained − vanilla | +0.000 [−0.025, +0.031] | +0.262 [+0.212, +0.327] | +0.262 [+0.202, +0.333] |
| Jev 항목 | trained − Jev | −0.013 [−0.100, +0.062] | +0.071 [−0.017, +0.163] | +0.083 [−0.035, +0.215] |
| ext | trained − vanilla | +0.017 [−0.003, +0.051] | +0.252 [+0.171, +0.328] | +0.235 [+0.147, +0.316] |

**Q3. 전문화 비용.** 과제당 라벨은 6,400개다(train 5,000 + calib 400 + dev 1,000). T1은 6,000(dev 600), T6은 6,100(dev 700), T8은 544(train 444 + calib 40 + dev 60)다. M4 Pro MPS fp32 학습 loop는 train 5,000 items 과제에서 7.5분(T7)-43.3분(T9)이고 T8(444 items)은 1.4분이다. 체크포인트는 english 0.85 GB, multilingual 0.68 GB다. Jev와 vanilla는 라벨과 학습이 없다(`results/T3arm/summary.md` §5).

**Q4. 제대로 학습했는가.** V1-V6 모두 통과다. V3는 프로젝트 책임자 판정(2026-10-08)에 따라 차이 기준으로 통과이고, `summary.md` §6.2·§6.3에도 프로젝트 책임자 판정으로 들어갔다(`results/T3arm/summary.md` §6.2, §6.3).

| 검증 | 판정 | 핵심 수치 |
|---|---|---|
| V1 zero-step identity | 통과 | 텐서 값 english 206/206, multilingual 170/170 동일. refit만으로 ECE english 0.083 → 0.064, multilingual 0.365 → 0.179 |
| V2 upstream 재현 | 통과 | (a) upstream 체크포인트 0.766(공개 0.766, ±0.02) (b) 우리 학습 0.747(기준 ≥ 0.562, majority 0.461) |
| V3 label-shuffle | 통과(차이 기준, 프로젝트 책임자 판정 2026-10-08) | 실제 라벨 epoch 1 0.864 − permuted 0.385 = +0.479 ≥ 0.30, 대안 기준(permuted < vanilla 0.612)도 충족. 엄격 기준(permuted ≤ majority + 0.05 = 0.346)은 +0.039 미달이라 계획과의 편차로 기록 |
| V4 형식 동일성 | 통과 | 10과제, 추론 시퀀스·토큰 일치 250/250 |
| V5 smoke | 통과 | 드라이버 SMOKE STEP OK 163, FAILED 0 |
| V6 누수 | 통과 | 10과제 train·dev·calib와 평가 텍스트의 교집합 정확 0 / 정규화 0 |

- 학습 실패 표시(§4, 모든 epoch의 dev가 epoch 0보다 낮음)는 T5·T9·T10에 붙었고 셋 다 파이프라인 실패가 아니다. T5는 dev 기준선 오염이다. dev가 upstream 학습 믹스인 BoolQ의 train split이라 vanilla dev 0.986이 validation ext 0.834보다 부풀었다. T9는 천장 효과다(vanilla dev 0.996, 차이는 1,000행 중 1행). T10은 dev 라벨 분포 불일치다(dev는 자연 분포, train·ext는 균등에 가깝다)(`results/T3arm/summary.md` §6.1, `results/T3arm/PREP_20261008.md` "본 학습 중 발견" 절).
- 주의할 진단은 둘이다. T10의 옵션 순서 flip이 0.175 [0.105, 0.250]로 높고, T6의 train − dev 차이가 0.142로 크다(`results/T3arm/summary.md` §6.1).
- 같은 설정(스크립트·items·seed·인자 동일)의 T1 두 run이 test에서 0.747 대 0.690(label 기준)으로 갈렸다. 짝 비교 b/c 217/98, exact McNemar p=1.7e-11이다. 원인은 MPS 학습의 비결정성이다(micro-batch 손실이 12번에서 처음 갈라진다). 그래서 trained 수치는 과제당 run 하나의 표본이다. seed를 바꾼 반복 학습 결과는 아래 "반복 학습"에 있다(`results/T3arm/summary.md` §6.4, §7).

**보정 분리.** vanilla + 과제 T(base 가중치에 그 과제 calib로 맞춘 temperature만 넣은 0-step export)로 trained − vanilla의 보정 차이를 refit 효과와 학습 효과로 나눴다. 답이 vanilla와 같아(정답 여부 6,736/6,736 일치) 정확도 비교는 그대로다. ext에서 ECE는 T1·T2·T3·T6·T7·T10에서 refit 효과가 학습 효과보다 크다(예: T3 −0.336 대 +0.002). Brier는 학습 제외 6과제 모두에서 학습 효과가 refit 효과보다 크게 낮춘다(예: T8 −0.087 대 −0.382). T5의 보정 악화는 refit에서 온다(ext ECE refit +0.055, 학습 −0.010). calib 행이 upstream 학습 믹스인 BoolQ의 train split이라 맞춘 temperature가 validation에 맞지 않는 것으로 본다(해석). T1·T8은 fitted T가 laya 로드 범위에서 잘린다(T1 choice 7.613 → 5.000, noul 10.000 → 5.000, T8 noul 10.000 → 5.000)(`results/T3arm/summary.md` §4.3).

| 과제 | Jev 항목 ECE: refit / 학습 | Jev 항목 Brier: refit / 학습 | ext ECE: refit / 학습 | ext Brier: refit / 학습 |
|---|---|---|---|---|
| T1 typed-decisions | −0.076 / +0.051 | −0.067 / −0.303 | −0.138 / +0.077 | −0.064 / −0.250 |
| T2 AG News | −0.019 / −0.052 | −0.002 / +0.043 | −0.012 / −0.006 | −0.000 / +0.001 |
| T3 DAIR Emotion | +0.034 / −0.135 | −0.002 / −0.334 | −0.336 / +0.002 | −0.228 / −0.470 |
| T4 Banking77-10 | +0.005 / −0.143 | −0.012 / −0.265 | +0.004 / −0.063 | +0.001 / −0.151 |
| T5 BoolQ | +0.039 / −0.039 | +0.054 / −0.036 | +0.055 / −0.010 | +0.035 / +0.003 |
| T6 SST-5 | −0.127 / +0.041 | −0.084 / −0.226 | −0.226 / −0.013 | −0.139 / −0.194 |
| T7 MASSIVE intent-10 | −0.133 / −0.009 | −0.060 / −0.352 | −0.093 / −0.045 | −0.054 / −0.240 |
| T8 prompt-injections | −0.055 / −0.147 | −0.065 / −0.302 | −0.055 / −0.173 | −0.087 / −0.382 |
| T9 Enron spam | −0.010 / +0.022 | −0.004 / +0.029 | +0.000 / −0.001 | +0.000 / +0.003 |
| T10 support tickets | −0.091 / +0.022 | −0.042 / +0.019 | −0.113 / −0.034 | −0.050 / −0.045 |

**반복 학습(seed 14).** run 2는 본 학습과 같은 설정에 torch seed만 14로 바꾼 학습이고 10과제가 모두 끝났다. T9·T10은 다른 프로젝트와의 메모리 경합으로 중지했다가, 감시자가 2026-10-08 22:58:42에 다시 시작해 2026-10-09 00:23:20에 rc 0으로 끝냈다(경합 없음, 열린 질문 11). 판정 30개(과제 10개 × 비교 3종) 가운데 확정 27, 불일치 3이다. 불일치는 T4 Jev 항목 trained vs vanilla(run 1 유의 0.0312, run 2 비유의 0.0547), T8 Jev 항목 trained vs Jev(run 1 비유의 0.1934, run 2 trained 유의 우세 0.0391), T8 Jev 항목 trained vs vanilla(run 1 비유의 0.1504, run 2 유의 0.0312)다. ext trained vs vanilla는 10과제 모두 확정이다. run 2에서는 보정 전 T5에서 Jev가 유의 우세였다(b/c 1/10, p=0.0117, Holm 후 0.1055로 비유의). ext 정확도의 run 간 차이는 T1에서만 유의하고(b/c 117/214, p=1.1e-07), 나머지 9과제는 p ≥ 0.55다(`results/T3arm/summary.md` §7.1, §7.2).

| 과제 | 범주 | Jev 항목 정확도: run 1 / run 2 | ext 정확도: run 1 / run 2 | ext run 1 vs run 2: b/c, p | 판정 일치: trained vs Jev / trained vs vanilla / ext |
|---|---|---|---|---|---|
| T1 typed-decisions | 제외 | 0.792 / 0.858 | 0.686 / 0.735 | 117/214, 1.1e-07 | 확정 / 확정 / 확정 |
| T2 AG News | 포함 | 0.950 / 0.975 | 0.946 / 0.942 | 12/10, 0.8318 | 확정 / 확정 / 확정 |
| T3 DAIR Emotion | 제외 | 0.950 / 0.925 | 0.886 / 0.886 | 11/11, 1.0000 | 확정 / 확정 / 확정 |
| T4 Banking77-10 | 제외 | 0.950 / 0.925 | 0.964 / 0.962 | 9/8, 1.0000 | 확정 / 불일치 / 확정 |
| T5 BoolQ | 포함 | 0.775 / 0.700 | 0.832 / 0.838 | 21/24, 0.7660 | 확정 / 확정 / 확정 |
| T6 SST-5 | 제외 | 0.675 / 0.725 | 0.590 / 0.578 | 38/32, 0.5504 | 확정 / 확정 / 확정 |
| T7 MASSIVE intent-10 | 제외 | 0.910 / 0.870 | 0.878 / 0.882 | 16/18, 0.8642 | 확정 / 확정 / 확정 |
| T8 prompt-injections | 제외 | 0.975 / 1.000 | 0.966 / 0.957 | 2/1, 1.0000 | 불일치 / 불일치 / 확정 |
| T9 Enron spam | 포함 | 0.975 / 0.975 | 0.988 / 0.988 | 2/2, 1.0000 | 확정 / 확정 / 확정 |
| T10 support tickets | 포함 | 0.300 / 0.425 | 0.332 / 0.340 | 33/37, 0.7202 | 확정 / 확정 / 확정 |

- **불일치 3개의 성격.** 셋 모두 n=40 Jev 항목 비교이고 Holm p가 0.05 근처다. run 2가 8과제 family였던 중간 집계에서는 T6 Jev 항목 trained vs vanilla가 불일치였다가 10과제 family에서 확정이 됐고, T4는 반대로 확정에서 불일치가 됐다. 이런 경계 판정은 seed와 Holm family 크기에 민감하므로, 프로젝트 책임자 결정대로 두 run이 같은 판정만 확정한다.
- run 2의 ext trained − vanilla는 포함 범주 +0.020, 제외 범주 +0.257, 차이의 차이 +0.238 [+0.144, +0.325]로 run 1(+0.235 [+0.147, +0.316])과 거의 같다(`results/T3arm/summary.md` §7.3).
- T1 세 run의 test 정확도(label 기준)는 준비 V2(b) 0.747, 본 학습 run 1 0.690, run 2 0.735다. run 2는 V2(b)와 유의차가 없고(b/c 118/96, p=0.1510), run 1보다 높다(본 학습 vs run 2 b/c 117/214, p=1.1e-07, 차이 −0.049 [−0.069, −0.028]). 세 run 중 본 학습 T1이 가장 낮다(`results/T3arm/summary.md` §7.4).

**후속 작업.** 보정 분리 열(`results/T3arm/calib_sep/`), T9·T10 Jev 측정(`results/F/jev_cmp/sessions/S7_20261008/`), seed 14 반복 학습(`results/T3arm/rep_s14/`)이 모두 끝났다. 판정은 두 run이 같은 27개만 확정하고 불일치 3개는 확정하지 않는다. 남은 일은 T10 라벨의 수작업 확인이다(열린 질문 12).

---

## 열린 질문 / 가정

1. **T9·T10의 Jev 측정(80 요청, 세션 상한 100 안).** Laya 결과를 본 뒤 정한다. 측정하지 않으면 Jev 범주 집계의 포함 과제는 T2·T5 두 개로 남는다.
   - **해결(2026-10-08).** 세션 S7(`results/F/jev_cmp/sessions/S7_20261008/`)에서 80 요청이 모두 성공했다(5xx·429 0, 사이트 누적 518). T9는 Jev·vanilla 모두 40/40이고, T10은 Jev 0.250, vanilla english 0.300, multilingual 0.450이며 모두 비유의다. Jev 포함 범주가 T2·T5·T9·T10이 됐다(§9 Q1).
2. **T8 × 3 epoch.** 프로젝트 책임자가 고른 선택지는 "과제당 최대 5천 건 × 2 epoch"이다. T8은 train이 546행뿐이라 3 epoch여도 item-pass가 다른 과제의 6분의 1 이하다. 다만 epoch 상한을 넘으므로 엄격히 읽으면 2 epoch로 바꾼다.
   - **해결(2026-10-08).** 본 학습 시작 때 T8도 2 epoch로 바꿔 적용했고(`poc/finetune/run_all_tasks.sh`의 `epochs_of`), 프로젝트 책임자가 2 epoch를 확정했다(`results/T3arm/PREP_20261008.md` "본 학습 시작 시 적용한 기본값", "프로젝트 책임자 결정" 절).
3. **S2 소요 시간.** V5 측정으로 S2 예상이 5시간을 넘으면 프로젝트 책임자에게 알린다. 기본은 설정 그대로 무인 실행이다. 대안은 긴 입력 과제 4개의 train을 2,500 items로 줄이는 것이다.
   - **해결(2026-10-08).** S2는 10:57-15:01, 약 4.1시간 걸려 5시간 기준 안에서 설정 그대로 무인 실행했다(`results/T3arm/run_all_20261008-1057_driver.log`).
4. **보정 분리 열.** trained의 보정 개선에서 temperature refit 효과를 떼려면 과제별 zero-step export를 참고 열(vanilla + 과제 temperature)로 더한다. 학습 없이 calib만 돌리므로 과제당 약 1분이다. 기본은 넣지 않고 V1 결과로 크기만 확인한다.
   - **해결(2026-10-08).** 프로젝트 책임자 결정으로 추가했다. 과제마다 V1과 같은 0-step export(base 가중치 + 그 과제 calib로 맞춘 temperature)를 Jev 항목과 ext로 평가해 `results/T3arm/calib_sep/`에 냈다(`CALIB_SEP FINISHED`). refit 효과와 학습 효과는 §9 "보정 분리"와 `results/T3arm/summary.md` §4.3에 있다.
5. **T1 전체 예산 재현.** upstream 수준(약 30k questions × 4 epoch, 2xT4에서 4-5시간)으로 0.766을 재현할지 정해야 한다. 기본은 V2(a)와 V2(b)까지다.
   - **기본값 적용.** V2(a)·V2(b)까지만 했고 둘 다 통과다(§9 Q4). 전체 예산 재현은 하지 않았다.
6. **소논문 v3 위치.** `docs/10_paper_laya_vs_jev.md`를 개정할지 새 파일로 낼지 정해야 한다. 기본은 10 개정이다.
   - **기본값 적용.** 10 개정으로 진행하며, 이 결과 반영(§9, REPORT, 대시보드)과는 별도 작업이다.
7. **라벨 수 곡선.** "라벨 몇 개면 Jev를 따라잡나"를 보려면 과제당 500 / 2,000 / 5,000 세 단계 학습이 필요하다. 이번 범위에는 넣지 않았다.
   - **기본값 적용.** 이번 결과는 과제당 라벨 6,400개(T1 6,000, T6 6,100, T8 544) 한 점이다(§9 Q3).
8. **가정.**
   - 스크립트 기본 하이퍼파라미터를 모든 과제에 쓴다. encoder 2.5e-5, head 1e-4(`:266`), cosine schedule, RLCD + soft CE다.
   - 길이 패치는 시퀀스 형식만 바꾸고 손실과 optimizer는 그대로 둔다.
   - 과제마다 모델 하나를 학습한다. 멀티태스크 모델은 만들지 않는다.
   - Laya 평가는 모든 arm에서 CPU fp32 경로다.
   - **유지(2026-10-08).** 네 가정 그대로 S2를 돌렸다. 길이 패치는 시퀀스 예산과 `model_name` 두 곳만 바꾼다(`results/T3arm/finetune_script.diff`).
9. **V3 판정.** label-shuffle의 엄격 기준(permuted ≤ majority + 0.05)은 학습이 base를 chance로 무너뜨린다고 가정해, zero-shot이 강한 base에는 맞지 않을 수 있다. 그래서 판정을 프로젝트 책임자에게 맡겼다.
   - **해결(프로젝트 책임자 판정 2026-10-08).** 통과(차이 기준)다. 본 학습 T3 epoch 1 dev 0.864 − permuted 0.385 = 0.479 ≥ 0.30이고, 대안 기준(permuted < vanilla 0.612)도 충족한다. 엄격 기준(0.346)은 +0.039 미달이라 계획과의 편차로 기록한다. `results/T3arm/summary.md` §6.2·§6.3에도 프로젝트 책임자 판정으로 들어갔다.
10. **T8 분할.** validation이 없어 train 546행(필터 뒤 544)에서 dev 60 + calib 40을 떼는 hold-out과, 전량 학습 + temperature 1.2(calibration 없음) 중 하나를 골라야 했다.
    - **해결(프로젝트 책임자 결정 2026-10-08).** hold-out(train 444 + dev 60 + calib 40)을 유지하고 2 epoch로 확정했다. 본 학습에 적용한 그대로라 재학습은 없다.
11. **반복 학습 run.** 같은 설정의 T1 재학습이 test 0.747 대 0.690(label 기준)으로 갈렸다(MPS 비결정성, §9 Q4). 그래서 trained 수치는 과제당 run 하나의 표본이다.
    - **해결(2026-10-09).** 본 학습과 같은 설정에 torch seed만 14로 바꿔 10과제를 한 번 더 학습했다(`results/T3arm/rep_s14/`, 체크포인트 `poc/finetune/ckpt_t3arm_rep_s14/`(공개 저장소에는 포함하지 않음)). 판정 30개 중 확정 27, 불일치 3이다(§9 "반복 학습"). T9는 다른 프로젝트 실험과의 메모리 경합으로 2026-10-08 19:37에 중지했고, 감시자 `poc/finetune/autostart_rep_t9t10.sh`가 22:58:42에 T9·T10을 다시 시작해 2026-10-09 00:23:20에 rc 0으로 끝냈다(경합 없음, `results/T3arm/rep_s14/autostart.log`, `results/T3arm/PREP_20261008.md` "반복 학습 T9 중지와 자동 재시작"). 판정은 두 run의 결론이 같을 때만 확정하므로 불일치 3개는 확정하지 않는다.
12. **T10 라벨 품질.** Jev 항목 40행 중 네 시스템(Jev, vanilla english, vanilla multilingual, trained)이 모두 틀린 행이 18/40이다. S7 분석은 오답 다수에서 gold 큐가 질문에 준 큐 설명과 맞지 않는다고 읽었다(해석).
    - **대기(수작업 확인 필요).** 해당 행을 사람이 다시 확인하기 전에는 T10 정확도를 라우팅 능력으로 읽지 않는다(`results/T3arm/summary.md` §1.6, `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md`).

[English](11_three_arm_plan.md) | **한국어**
