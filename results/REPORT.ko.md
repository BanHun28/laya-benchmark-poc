# Laya 벤치마크·PoC 결과 리포트

작성 2026-10-03, Laya vs Jev 통제 비교(§0a) 반영 2026-10-07. 대상: NandhaKishorM/laya 0.3.23 (upstream 커밋 4aa6761, 체크포인트 번들 55cf4c4). 모든 수치는 `results/` 아래 파일에서 가져왔고 각 표에 경로를 적었다. 가설 판정은 `results/verdicts.json`, Go/No-Go는 `results/go_no_go.json`이 원본이며 이 문서는 그 둘을 옮겨 적는다. Laya vs Jev 수치의 원본은 `results/F/jev_cmp/summary.json`(사람용 `summary.md`)이다. 대시보드: `results/dashboard/index.html`.

## 0. 요약

1. **Laya vs Jev (주 결과, §0a)**: 같은 state·질문·옵션 문자열로 8과제(T1\~T8)를 비교했다. zero-shot에서는 Jev가 Laya보다 정확하고(8과제 중 Laya 유의 우세 0, Holm 후 Jev 유의 우세 2), 특히 지시형·다국어 과제에서 격차가 크다. Laya는 로컬 실행·지연·비용과 파인튜닝으로 격차를 메울 수 있다는 점에서 경쟁력이 있다. 8과제 macro 정확도는 Jev 0.828, Laya Router 0.661이고, T1에서 typed-decisions 파인튜닝 체크포인트는 104/120으로 Jev와 같다(`results/F/jev_cmp/summary.md`).
2. **Laya vs Jev 운영**: Jev 플레이그라운드 표시 지연은 중앙 226 ms(브라우저 POST 465 ms, 인터넷 왕복 포함)이고 Laya 로컬 1문항은 in-process 13.8\~86.6 ms, localhost HTTP 20.1\~50.7 ms다. 배포 형태가 달라 모델 속도 비교가 아니다. Jev 비용은 1,000 decision당 $0.0197(제3자 인용 단가, 확인 필요)이고 Laya는 토큰 과금이 없다.
3. **한국어 PoC 사례 연구, 품질**: 한국어 zero-shot은 쓸 수 없다. 8도메인 라우팅 0.492(test 절반), 7토픽 0.655, CS triage 0.40\~0.50이고 스키마 문구·보정·임계값 어느 것으로도 0.6 선을 넘지 못했다. 반면 MASSIVE ko train 11,094행으로 36분 파인튜닝한 ft-v1은 같은 test 절반에서 **0.900**(전체 test 2,917행 0.913), ECE 0.053, 옵션 순서 flip 0.037이다.
4. **한국어 PoC 사례 연구, 속도·운영**: multilingual 3문항 in-process p95는 MPS 22.6 ms, CPU 10 threads 57.8 ms이고 laya-serve는 MPS 10 RPS에서 p95 79.4 ms다. 서버가 추론을 직렬 처리해 프로세스당 처리량은 MPS 3문항 약 22.6 RPS, CPU 10 RPS가 상한이다. ONNX int8은 이 Apple silicon에서 torch보다 1.74배 느리고 결정 7%를 바꾼다.
5. **한국어 PoC 사례 연구, 판정**: **Conditional Go(파인튜닝 파이프라인 전제)**. zero-shot은 G1/G2/G4 미달로 No-Go, 파인튜닝 ft-v1은 G0\~G7 모두 통과. 핵심 근거는 `ko_massive_domain_8` test 절반 0.492 → 0.900(`results/P4/metrics/full_20261003-1156_summary.md`).
6. **Jev 대비 한국어 파일럿(n=24 수동, 2026-10-06)**: Jev는 Laya zero-shot을 확실히 앞서고(0.833 vs 0.417, p=0.002) 파인튜닝한 ft-v1과는 구분되지 않는다(0.917, p=0.5). 지연은 호스팅 Jev 표시값 249.5 ms vs 로컬 ft-v1 왕복 20.1 ms(`results/F/jev_playground_manual_20261006.md`).
7. **3-arm 비교 (§0b)**: 과제 라벨(과제당 약 6,400개)로 파인튜닝한 Laya는 Jev 항목에서 Jev보다 Holm 후 유의하게 낮은 과제가 두 run(seed 13·14) 모두 없고, zero-shot에서 Jev가 앞섰던 T1·T7의 격차도 사라졌다. 학습 이득은 upstream이 학습하지 않은 과제에 몰린다(ext trained − vanilla 포함 범주 +0.017, 제외 범주 +0.252). 판정은 두 run의 결론이 같은 것만 확정해 30개 중 27개가 확정이고 3개(T4·T8 Jev 항목)는 불일치다(`results/T3arm/summary.md` §7).

## 0a. Laya vs Jev 비교 (주 결과)

원본은 `results/F/jev_cmp/summary.md`와 `summary.json`(S6, 2026-10-07)이고 이 절의 수치는 모두 거기서 옮겼다. 계획과 세션별 결과는 `docs/09_laya_vs_jev_plan.md` §7\~§10, 원기록은 `results/F/jev_cmp/sessions/`와 마스터 로그 `results/F/jev_cmp/jev_runs_all.jsonl`(411줄. 원기록과 마스터 로그는 공개 저장소에는 포함하지 않음)에 있다. 대시보드 `results/dashboard/index.html`의 "Laya vs Jev (주 결과)" 절이 같은 JSON을 읽는다.

**설정.** 두 시스템에 같은 state 바이트(Laya가 읽는 JSON 직렬화 문자열), 같은 질문 문장, 같은 옵션 문자열과 순서를 넣었다. 요청 body가 폼 payload와 바이트 단위로 같았던 요청은 411/411이다. Jev는 독립 제3자 플레이그라운드 jevplayground.com의 `POST /api/evaluate`를 사람 속도로 호출했다(Model ID `typesafe-ai/jev`, 버전 미표기, 확률 소수 둘째 자리 반올림). Laya는 0.3.23 zero-shot english, multilingual, Router를 CPU fp32로 돌렸다. 과제는 T1\~T8이고 과제당 n=40이다. T1은 40 case의 비교 가능 decision 120개, T7은 같은 20 id × 5개 언어 100행이다. 사이트 요청은 2026-10-06\~07에 438회(마스터 로그 411 + 도구화 이전 27)였고 HTTP 502는 2회, 429는 0회였다. 주 판정은 과제마다 Jev와 그 과제의 최고 zero-shot Laya 러너를 exact McNemar(양측, α 0.05)로 비교하고, 8개 검정에 Holm 보정을 한 결과다.

**판정.** zero-shot에서는 Jev가 Laya보다 정확하고(8과제 중 Laya 유의 우세 0, Holm 후 Jev 유의 우세 2), 특히 지시형·다국어 과제에서 격차가 크다. Laya는 로컬 실행·지연·비용과 파인튜닝으로 격차를 메울 수 있다는 점에서 경쟁력이 있다.

| 과제 | n | Jev [Wilson 95%] | Laya english / multilingual / Router | 최고 Laya 대비 b/c, p (Holm p) | 판정 (Holm 후) |
|---|---|---|---|---|---|
| T1 typed-decisions | 120 (40 case) | 0.867 [0.794, 0.916] | 0.383 / 0.367 / 0.383 | english 66/8, 1.8e-12 (1.4e-11) | Jev 유의 우세 (Jev 유의 우세) |
| T2 AG News | 40 | 0.875 [0.739, 0.945] | 0.975 / 0.925 / 0.975 | english 0/4, 0.1250 (0.3750) | 비유의 (비유의) |
| T3 DAIR Emotion | 40 | 0.700 [0.546, 0.819] | 0.750 / 0.625 / 0.750 | english 2/4, 0.6875 (1.0000) | 비유의 (비유의) |
| T4 Banking77-10 | 40 | 0.925 [0.801, 0.974] | 0.725 / 0.750 / 0.725 | multilingual 8/1, 0.0391 (0.1953) | Jev 유의 우세 (비유의) |
| T5 BoolQ | 40 | 0.925 [0.801, 0.974] | 0.725 / 0.600 / 0.725 | english 9/1, 0.0215 (0.1289) | Jev 유의 우세 (비유의) |
| T6 SST-5 | 40 | 0.650 [0.495, 0.779] | 0.425 / 0.325 / 0.425 | english 15/6, 0.0784 (0.3134) | 비유의 (비유의) |
| T7 MASSIVE intent-10 × 5개 언어 | 100 (20 id) | 0.910 [0.838, 0.952] | 0.410 / 0.620 / 0.580 | multilingual 36/7, 9.0e-06 (6.3e-05) | Jev 유의 우세 (Jev 유의 우세) |
| T8 prompt-injections | 40 | 0.775 [0.625, 0.877] | 0.775 / 0.575 / 0.725 | english 5/5, 1.0000 (1.0000) | 비유의 (비유의) |

b는 Jev만 정답, c는 Laya만 정답인 항목 수다. upstream 표기로 Laya 학습 믹스에 들어간 과제는 T2·T5(retention)뿐이고 나머지 여섯 과제는 held out이다. T4 Banking77은 held out, T1 typed-decisions와 T7 MASSIVE는 두 체크포인트 모두 학습하지 않았다(`third_party/laya/research/scripts/build_benchmark_nb.py:760-762`, `summary.md` §2.1. `third_party/`는 공개 저장소에는 포함하지 않음, https://github.com/NandhaKishorM/laya 를 커밋 4aa6761 기준으로 clone해 재현). 그래서 Jev 유의 우세 4개 중 T1·T4·T7은 두 체크포인트가 학습하지 않은 데이터이고(Holm 후 남는 T1·T7 포함) 학습 믹스 과제는 T5 하나다. Laya가 같거나 앞선 과제는 학습 믹스인 T2와 held out인 T3·T8이다.

- **판정 집계**(Jev 유의 우세 / 비유의 / Laya 유의 우세): 보정 전 4 / 4 / 0, Holm 보정 후 2 / 6 / 0이다. Holm 후에는 T1과 T7만 유의하다.
- **macro 정확도**: Jev 0.828, Laya english 0.646, multilingual 0.598, Router 0.661이다. 8과제 bootstrap(10,000회)에서 Jev − Router는 +0.167 [+0.044, +0.293], Jev − 과제별 최고 Laya는 +0.153 [+0.031, +0.281]다. 이질적인 8과제의 기술통계다. T1을 빼도 Jev 0.823, 최고 Laya 0.717이다.
- **독립 단일 문항 240개 합산**(T2·T3·T4·T5·T6·T8): Jev 194, 과제별 최고 Laya 176이고 b/c 39/21, exact McNemar p=0.0273이다. 러너를 고정해도 english p=0.0204, multilingual p=9.7e-07, Router p=0.0111이다.
- **군집 bootstrap**(10,000회): T1(case 군집) Jev − english +0.483 [+0.371, +0.597], T7(id 군집) Jev − multilingual +0.290 [+0.100, +0.470]이다.
- **과제별 특징**: T5는 정확도뿐 아니라 순위 품질도 다르다(AUROC Jev 0.988 vs english 0.810, 차이 +0.177 [+0.043, +0.326]). T6은 주 지표가 비유의이지만 E[level] MAE가 0.432 vs 0.888이다(차이 −0.456 [−0.711, −0.207]). T8은 정확도가 같고 오류 구조가 다르다. Jev는 역할 지시형 주입을, Laya english는 독일어 덮어쓰기 문장을 놓쳤다.

**보정과 견고성.** Jev 확률의 의미는 문항 형식마다 다르다. 단일 choice는 100% 표시가 65%이고 오답의 59%가 top ≥ 0.90이다. Boolean은 100% 표시가 0건이고 임계값의 적정 위치가 과제마다 다르다. 다문항(T1)은 평균 top 0.733이 정확도 0.867보다 낮은 과소확신이다. 최고 Laya 러너는 형식별로 묶으면 모두 과대확신이다. 두 시스템 모두 과제별 held-out 표본으로 임계값을 맞춰야 확신도로 자동 처리 범위를 정할 수 있다. Jev는 같은 payload 재전송(16\~23분 뒤)에서 라벨 10/10, 확률 벡터 9/10이 같았다. T7에서 5개 언어 모두 같은 라벨을 낸 id는 Jev 18/20, Laya english 0/20, multilingual 5/20, Router 4/20이다(`summary.md` §5, §6).

**지연과 비용.** Jev 표시값('server + network')은 중앙 226 ms, 브라우저 POST는 중앙 465 ms다(410건). Laya 1문항은 in-process 13.8\~86.6 ms(체크포인트·장치별), localhost HTTP 20.1\~50.7 ms, 1 s 간격 간헐 호출 49.2\~76.2 ms다. 배포 형태가 달라 모델 속도 비교가 아니다. Jev는 decision당 평균 469.4 토큰이고, upstream README가 인용한 제3자 단가 $0.042/1M 토큰으로 1,000 decision당 $0.0197이다(단가 확인 필요). Laya는 토큰 과금 없이 로컬 연산만 든다(`summary.md` §7).

**파인튜닝 참고선(zero-shot 아님).** T1에서 typed-decisions 파인튜닝 체크포인트는 104/120 = 0.867로 Jev와 같다(b/c 10/10, p=1.0000). 한국어 도메인 라우팅 ft-v1은 파일럿 24행에서 22/24 = 0.917로 Jev 20/24 = 0.833 이상이다(b/c 0/2, p=0.5000). 두 선 모두 같은 분포의 train으로 학습한 in-domain 결과라 zero-shot Jev와의 비교에서 유리하다(`summary.md` §3).

![과제별 정확도와 Wilson 95% CI](F/jev_cmp/figs/accuracy_by_task.png)

![T7 언어별 정확도](F/jev_cmp/figs/t7_languages.png)

![배포 형태별 지연 (로그 축)](F/jev_cmp/figs/latency.png)

**주의.**
- 독립 플레이그라운드 경유이며 API가 아니다. 모델 버전이 표기되지 않고 확률이 소수 둘째 자리로 반올림된다.
- 과제당 n=40이라 Wilson 95% 반폭이 약 ±0.15이고 T7은 언어당 n=20이다. 보정 전 판정 4 / 4 / 0은 탐색적 요약으로 읽는다.
- 과제별 최고 Laya 러너는 결과를 보고 고른 사후 선택이라 Laya에 유리하다. 고정 러너 기준도 같은 방향이다.
- T1은 teacher와 Jev의 관계를 확인하지 못했고, Jev는 case의 질문 2\~4개를 한 요청에서 함께 평가했다. T3는 seed 13 표본이 공개치보다 쉬웠다.
- 플레이그라운드 입력 제약(Boolean 설명 칸 없음, Score 5레벨 고정, choice 80자) 때문에 T1은 200개 중 120개만 비교했고 T4는 key-only 렌더링으로 다시 만들었다(`docs/09_laya_vs_jev_plan.md` §2, `summary.md` §9).

## 0b. 3-arm 비교: Jev vs vanilla Laya vs trained Laya

원본은 `results/T3arm/summary.md`와 `summary.json`(S3, 2026-10-09 00:23 재빌드, 공개용으로 2026-10-12 재빌드: 그림 영어 문구, 공개 주석, Jev 항목별 필드 제거, 수치 동일, `results/T3arm/summary.md:1`)이고 이 절의 수치는 모두 거기서 옮겼다. 계획과 결과 요약은 `docs/11_three_arm_plan.md`(§9), 준비·검증 run card는 `results/T3arm/PREP_20261008.md`, T9·T10 Jev 세션은 `results/F/jev_cmp/sessions/S7_20261008/`다. 대시보드 `results/dashboard/index.html`의 "3-arm" 절이 같은 JSON을 읽는다.

**설정.** Jev는 §0a의 기록(T1-T8)에 세션 S7(2026-10-08)의 T9·T10 80 요청을 더했다. Laya 쪽은 vanilla와 trained 두 arm에 보정 분리 열(vanilla + 과제 T)을 더했다. vanilla는 Router가 고르는 base(영어 과제 english, T7 multilingual)를 학습 없이 쓰고, vanilla + 과제 T는 여기에 과제 calib로 맞춘 temperature만 넣는다. trained는 같은 base를 과제 라벨로 과제마다 따로 파인튜닝한다(train 최대 5,000 items × 2 epoch, MPS fp32, dev로 epoch 선택, calib로 temperature fit). 그래서 trained 비교는 zero-shot이 아니라 전문화 비교다. 과제는 §0a의 8개에 Laya 학습 믹스 과제 T9 Enron spam과 T10 고객지원 티켓 큐를 더한 10개이고, 범주는 upstream 학습 믹스 포함(T2·T5·T9·T10)과 제외(T1·T3·T4·T6·T7·T8)다. 평가는 Jev 항목(§0a와 같은 입력, 과제당 40, T1 120 decision, T7 100행)과 확장 세트 ext(대부분 과제당 500, T1 2,000 decision, T8 116)의 두 층이다. 본 학습(S2)은 2026-10-08 10:57-15:01에 STEP 148개 OK, FAILED 0으로 끝났다(`results/T3arm/run_all_status.log`).

**판정.** 과제 라벨로 학습한 Laya는 Jev 항목 10과제 모두에서 Holm 보정 후 Jev와 유의차가 없다(run 1 기준. run 2에서는 T8만 trained 유의 우세). 보정 전에는 T3(0.950 대 0.700)와 T8(0.975 대 0.775)에서 trained가 유의 우세이고 Jev가 유의하게 앞선 과제는 없다. zero-shot에서 Jev가 Holm 후 유의 우세였던 T1·T7의 격차는 학습 뒤 사라졌다(T7 0.910 대 0.910, T1 0.792 대 0.867, 군집 bootstrap −0.075 [−0.185, +0.025]). 학습 이득은 upstream이 학습하지 않은 과제에 몰린다. 아래 trained는 run 1이다. 판정은 seed 14 반복 학습(run 2)과 결론이 같은 것만 확정했고, 30개 중 27개가 확정, 3개가 불일치다(아래 "반복 학습").

| 과제 | 범주 | n | Jev [Wilson 95%] | vanilla [Wilson 95%] | trained [Wilson 95%] | trained vs Jev: b/c, p (Holm p) | trained vs vanilla: b/c, p (Holm p) | 판정 (Holm 후): trained vs Jev / trained vs vanilla |
|---|---|---|---|---|---|---|---|---|
| T1 typed-decisions | 제외 | 120 (40 case) | 0.867 [0.794, 0.916] | 0.383 [0.301, 0.473] | 0.792 [0.711, 0.855] | 10/19, 0.1360 (0.9523) | 56/7, 1.4e-10 (1.4e-09) | 비유의 (비유의) / trained 유의 우세 (trained 유의 우세) |
| T2 AG News | 포함 | 40 | 0.875 [0.739, 0.945] | 0.975 [0.871, 0.996] | 0.950 [0.835, 0.986] | 3/0, 0.2500 (1.0000) | 0/1, 1.0000 (1.0000) | 비유의 (비유의) / 비유의 (비유의) |
| T3 DAIR Emotion | 제외 | 40 | 0.700 [0.546, 0.819] | 0.750 [0.598, 0.858] | 0.950 [0.835, 0.986] | 11/1, 0.0063 (0.0635) | 10/2, 0.0386 (0.2314) | trained 유의 우세 (비유의) / trained 유의 우세 (비유의) |
| T4 Banking77-10 | 제외 | 40 | 0.925 [0.801, 0.974] | 0.725 [0.572, 0.839] | 0.950 [0.835, 0.986] | 3/2, 1.0000 (1.0000) | 9/0, 0.0039 (0.0312) | 비유의 (비유의) / trained 유의 우세 (trained 유의 우세) |
| T5 BoolQ | 포함 | 40 | 0.925 [0.801, 0.974] | 0.725 [0.572, 0.839] | 0.775 [0.625, 0.877] | 2/8, 0.1094 (0.8750) | 2/0, 0.5000 (1.0000) | 비유의 (비유의) / 비유의 (비유의) |
| T6 SST-5 | 제외 | 40 | 0.650 [0.495, 0.779] | 0.425 [0.285, 0.578] | 0.675 [0.520, 0.799] | 6/5, 1.0000 (1.0000) | 16/6, 0.0525 (0.2624) | 비유의 (비유의) / 비유의 (비유의) |
| T7 MASSIVE intent-10 | 제외 | 100 (20 id) | 0.910 [0.838, 0.952] | 0.620 [0.522, 0.709] | 0.910 [0.838, 0.952] | 7/7, 1.0000 (1.0000) | 32/3, 4.2e-07 (3.8e-06) | 비유의 (비유의) / trained 유의 우세 (trained 유의 우세) |
| T8 prompt-injections | 제외 | 40 | 0.775 [0.625, 0.877] | 0.775 [0.625, 0.877] | 0.975 [0.871, 0.996] | 9/1, 0.0215 (0.1934) | 9/1, 0.0215 (0.1504) | trained 유의 우세 (비유의) / trained 유의 우세 (비유의) |
| T9 Enron spam | 포함 | 40 | 1.000 [0.912, 1.000] | 1.000 [0.912, 1.000] | 0.975 [0.871, 0.996] | 0/1, 1.0000 (1.0000) | 0/1, 1.0000 (1.0000) | 비유의 (비유의) / 비유의 (비유의) |
| T10 support tickets | 포함 | 40 | 0.250 [0.142, 0.402] | 0.300 [0.181, 0.454] | 0.300 [0.181, 0.454] | 5/3, 0.7266 (1.0000) | 1/1, 1.0000 (1.0000) | 비유의 (비유의) / 비유의 (비유의) |

b는 앞 arm만 정답, c는 뒤 arm만 정답인 항목 수이고 p는 exact McNemar(양측)다. Holm은 family마다 따로 적용했다(trained vs Jev 10과제, trained vs vanilla 10과제). T9·T10의 Jev가 들어와 trained vs Jev family가 8과제에서 10과제가 됐고, T1-T8의 Holm 후 판정은 바뀌지 않았다. T1(case)과 T7(id)은 decision이 군집이라 item 단위 검정이 낙관적이다(`summary.md` §1.1, §1.4).

**ext: vanilla vs trained.** 학습 제외 6과제는 Holm 후 모두 유의하게 오르고, 포함 과제는 T10만 유의하게 오른다(T2·T5·T9 비유의).

| 과제 | 범주 | n | vanilla | trained | trained − vanilla [bootstrap 95%] | b/c, p (Holm p) | 판정 (Holm 후) |
|---|---|---|---|---|---|---|---|
| T1 typed-decisions | 제외 | 2,000 (400 case) | 0.363 | 0.686 | +0.323 [+0.290, +0.355] | 818/172, 2.8e-101 (2.8e-100) | trained 유의 우세 (trained 유의 우세) |
| T2 AG News | 포함 | 500 | 0.940 | 0.946 | +0.006 [−0.014, +0.026] | 14/11, 0.6900 (1.0000) | 비유의 (비유의) |
| T3 DAIR Emotion | 제외 | 500 | 0.488 | 0.886 | +0.398 [+0.352, +0.446] | 209/10, 1.4e-49 (1.3e-48) | trained 유의 우세 (trained 유의 우세) |
| T4 Banking77-10 | 제외 | 500 | 0.876 | 0.964 | +0.088 [+0.062, +0.116] | 47/3, 3.7e-11 (2.2e-10) | trained 유의 우세 (trained 유의 우세) |
| T5 BoolQ | 포함 | 500 | 0.834 | 0.832 | −0.002 [−0.024, +0.020] | 16/17, 1.0000 (1.0000) | 비유의 (비유의) |
| T6 SST-5 | 제외 | 500 | 0.338 | 0.590 | +0.252 [+0.200, +0.304] | 172/46, 2.6e-18 (2.1e-17) | trained 유의 우세 (trained 유의 우세) |
| T7 MASSIVE intent-10 | 제외 | 500 (100 id) | 0.692 | 0.878 | +0.186 [+0.124, +0.248] | 110/17, 7.4e-18 (5.2e-17) | trained 유의 우세 (trained 유의 우세) |
| T8 prompt-injections | 제외 | 116 | 0.698 | 0.966 | +0.267 [+0.181, +0.353] | 33/2, 3.7e-08 (1.8e-07) | trained 유의 우세 (trained 유의 우세) |
| T9 Enron spam | 포함 | 500 | 0.992 | 0.988 | −0.004 [−0.012, +0.004] | 1/3, 0.6250 (1.0000) | 비유의 (비유의) |
| T10 support tickets | 포함 | 500 | 0.264 | 0.332 | +0.068 [+0.028, +0.106] | 68/34, 0.0010 (0.0039) | trained 유의 우세 (trained 유의 우세) |

차이와 구간은 같은 항목의 paired bootstrap(10,000회)이고 T1은 case, T7은 id를 군집으로 재표본했다. Holm은 10과제에 적용했다(`summary.md` §2.1).

**범주 집계(Q1).** ext에서 trained − vanilla는 포함 범주 +0.017, 제외 범주 +0.252이고 차이의 차이(DiD)는 +0.235 [+0.147, +0.316]이다. 포함 과제의 작은 이득은 vanilla가 이미 그 데이터를 본 만큼의 retention 상한과 맞는다. Jev 항목의 Q1 DiD(Jev − vanilla)는 +0.179 [−0.008, +0.356]로 방향은 같지만 구간이 0을 겨우 포함한다(포함 범주 T2·T5·T9·T10).

| 기준 | 차이 | 포함 평균 [95%] | 제외 평균 [95%] | 제외 − 포함 [95%] |
|---|---|---|---|---|
| Jev 항목 | Jev − vanilla | +0.013 [−0.075, +0.138] | +0.191 [+0.054, +0.330] | +0.179 [−0.008, +0.356] |
| Jev 항목 | trained − vanilla | +0.000 [−0.025, +0.031] | +0.262 [+0.212, +0.327] | +0.262 [+0.202, +0.333] |
| Jev 항목 | trained − Jev | −0.013 [−0.100, +0.062] | +0.071 [−0.017, +0.163] | +0.083 [−0.035, +0.215] |
| ext | trained − vanilla | +0.017 [−0.003, +0.051] | +0.252 [+0.171, +0.328] | +0.235 [+0.147, +0.316] |

범주 평균은 과제별 정확도의 단순 평균이고 구간은 범주 안 과제 재표본(10,000회)의 percentile이다. 범주당 과제가 2-6개라 기술통계로 읽는다(`summary.md` §3).

- **비용(Q3)**: 과제당 라벨 6,400개(train 5,000 + calib 400 + dev 1,000. T1 6,000, T6 6,100, T8 544), M4 Pro MPS fp32 학습 loop 과제당 7.5-43.3분(T8은 444 items라 1.4분), 체크포인트 english 0.85 GB, multilingual 0.68 GB다. Jev와 vanilla는 라벨과 학습이 없다(`summary.md` §5).
- **학습 검증(Q4)**: V1·V2·V4·V5·V6 통과. V3(label-shuffle)는 프로젝트 책임자 판정(2026-10-08)에 따라 차이 기준으로 통과다(실제 라벨 epoch 1 0.864 − permuted 0.385 = +0.479 ≥ 0.30). 엄격 기준(permuted ≤ majority + 0.05 = 0.346)은 +0.039 미달이라 계획과의 편차로 기록했다(`summary.md` §6.2, §6.3).
- **학습 실패 표시 3건**(T5·T9·T10)은 모두 파이프라인 실패가 아니다. T5는 dev 기준선 오염(dev가 BoolQ train split이라 vanilla dev 0.986, validation ext 0.834), T9는 천장 효과(dev 1,000행 중 1행 차이), T10은 dev 라벨 분포 불일치(dev는 자연 분포, train·ext는 균등에 가까움)다(`summary.md` §6.1, `PREP_20261008.md` "본 학습 중 발견" 절).
- **보정 분리**: vanilla + 과제 T의 답은 vanilla와 같아(정답 여부 6,736/6,736 일치) 정확도 비교는 그대로이고 Brier·ECE만 달라진다. ext에서 ECE는 T1·T2·T3·T6·T7·T10에서 refit 효과가 학습 효과보다 크고(예: T3 −0.336 대 +0.002), Brier는 학습 제외 6과제 모두에서 학습 효과가 더 크게 낮춘다(예: T8 −0.087 대 −0.382). T5의 보정 악화는 refit에서 온다(ext ECE refit +0.055, 학습 −0.010). T1·T8은 fitted T가 laya 로드 범위에서 잘린다(T1 choice 7.613 → 5.000, noul 10.000 → 5.000, T8 noul 10.000 → 5.000)(`summary.md` §4.3).
- **T9·T10 Jev(S7)**: T9는 Jev·vanilla 모두 40/40이다. T10은 Jev 0.250, vanilla english 0.300이고 비유의다(b/c 3/5, p=0.7266). T10은 네 시스템(Jev, vanilla english, vanilla multilingual, trained)이 모두 틀린 행이 18/40이라 라벨 품질 의심, 수작업 확인 필요다(`summary.md` §1.1, §1.6).

**반복 학습(seed 14).** run 2는 본 학습과 같은 설정에 torch seed만 14로 바꿨고 10과제가 모두 끝났다. 판정 30개(과제 10개 × 비교 3종) 가운데 확정 27, 불일치 3이다. 불일치는 T4 Jev 항목 trained vs vanilla(run 1 유의 0.0312, run 2 비유의 0.0547), T8 Jev 항목 trained vs Jev(run 1 비유의 0.1934, run 2 trained 유의 우세 0.0391), T8 Jev 항목 trained vs vanilla(run 1 비유의 0.1504, run 2 유의 0.0312)로, 모두 n=40 Jev 항목 비교이고 Holm p가 0.05 근처다. ext trained vs vanilla는 10과제 모두 확정이고, run 2의 ext DiD도 +0.238 [+0.144, +0.325]로 run 1(+0.235)과 거의 같다. run 2에서는 보정 전 T5에서 Jev가 유의 우세였다(b/c 1/10, p=0.0117, Holm 후 비유의)(§8, `summary.md` §7).

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

![과제별 3-arm 정확도 (Jev 항목)](T3arm/figs/accuracy_3arm.png)

![ext: trained − vanilla](T3arm/figs/ext_trained_minus_vanilla.png)

**주의.**
- trained는 과제당 학습 run 하나다. 같은 설정의 T1 재학습이 test 0.747 대 0.690(label 기준), 짝 비교 b/c 217/98, p=1.7e-11로 갈렸다(MPS 비결정성, §8). 이 편차보다 작은 차이는 run에 따라 뒤집힐 수 있다. seed 14 반복 학습 결과는 위 "반복 학습"에 있고, T1은 세 run 중 본 학습이 가장 낮다(V2(b) 0.747, run 1 0.690, run 2 0.735, `summary.md` §7.4).
- 보정 지표의 원값 비교(trained − vanilla)에는 temperature refit 효과가 섞인다(V1: 학습 없이 refit만으로 ECE english 0.083 → 0.064, multilingual 0.365 → 0.179). 학습 효과는 보정 분리의 학습 열로 읽는다(`summary.md` §4.3).
- Jev 항목은 과제당 n=40이라 trained vs Jev의 작은 차이는 판정할 수 없다. Holm 후 유의차 없음은 동등을 뜻하지 않는다.
- 주의할 진단: T10은 옵션 순서 flip이 0.175로 높고, T6은 train − dev 차이가 0.142로 크다(`summary.md` §6.1).

## 1. 환경

- 머신: Apple M4 Pro(10P+4E CPU, 20코어 GPU/MPS), 48 GB, macOS 26.6.2. Python 3.12.12, laya 0.3.23, torch 2.14.1, transformers 5.18.0, onnxruntime 1.30.0 (`results/env/env_20261002-1333.json`).
- 체크포인트: `convaiinnovations/laya` 번들 @ `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`(english / multilingual / typed-decisions), upstream 체크아웃 `4aa6761`. 파인튜닝 결과 `poc/finetune/ckpt_domain8_v1/`(run `full_20261003-1156`, 공개 저장소에는 포함하지 않음).
- 디바이스 역할: 품질 수치는 전부 CPU fp32, 레이턴시는 CPU(intra-op 10 / inter-op 1)와 MPS. parity: P0 7문항 MPS fp16 vs CPU fp32 argmax 7/7, max |Δp| 0.0017 (`results/poc/P0_20261002.md`); Track D4 predict vs predict_batch flip 0 (`results/D/20261003-1314_batch.json`).
- 데이터: `data/evals/` 19개 파일(`scripts/build_ko_evalsets.py`, `data/evals/MANIFEST.json`). dev/test 분할은 `results/B/B_splits.json`(쌍 MASSIVE 세트는 행 index parity, 나머지는 state sha256 홀짝).

## 2. 트랙별 결과

### Track A 재현 (`results/A/README.md`, `results/korean_support/K2_analysis.md` E2)

| 세트 | 체크포인트 | 측정 acc | upstream acc | Δ | ECE 측정 / upstream |
|---|---|---|---|---|---|
| ko intent-20 | multilingual | 0.470 | 0.470 (BENCHMARKS.md:71) | 0.000 | 0.3108 / 0.3108 |
| en intent-20 | multilingual | 0.710 | 0.710 | 0.000 | 0.2333 / 0.2333 |
| en intent-20 | english | 0.820 | 0.820 | 0.000 | 0.1383 / 0.1382 |
| ko intent-20 | english | 0.110 | 0.110 | 0.000 | 0.6804 / 0.6804 |

fixture 5개 지표도 docs/evals.md 기대값과 4자리 일치(`results/env/smoke_fixture_english_cpu.json`). 하네스 경로(laya-evals, 행별 forward)와 upstream packed 경로가 같은 값을 냈다. A3 빌더 파일 동일성 통과(`results/B/summary_20261002.md` §9).

### Track B 한국어 품질 (`results/B/summary_20261002.md`, `results/B/metrics/`, CPU fp32)

| 세트 | 옵션 | majority | english | multilingual | typed-decisions | Router auto |
|---|---|---|---|---|---|---|
| ko_massive_domain_8 (all / dev / test) | 8 | 0.126 | 0.262 | 0.526 / 0.560 / **0.492** | 0.288 | 0.526 |
| ko_klue_ynat_7 (all / test) | 7 | 0.144 | 0.216 | 0.634 / 0.655 | 0.234 | 0.634 |
| ko_massive_scenario_18 (n=100) | 18 | 0.210 | 0.310 | 0.520 | 0.330 | 0.520 |
| ko_massive_intent_20opt (n=100) | 20 | 0.170 | 0.110 | 0.470 | 측정됨(summary) | 0.470 |
| ko_klue_nli_3 | 3 | 0.334 | 0.448 | 0.750 | 측정됨 | 동일 |
| ko_nsmc_sentiment choice / noul | 2 | 0.500 | 0.528 / 0.516 | 0.774 / 0.638 | 측정됨 | 동일 |
| ko_kmhas_hate (noul) / type_8 | 2 / 8 | 0.500 / 0.144 | 0.500 / 0.146 | 0.582 / 0.394 | 측정됨 | 동일 |
| ko_3i4k_speechact_7 | 7 | 0.144 | 0.174 | 0.178 | 측정됨 | 동일 |
| en_massive_domain_8 (ko 쌍, multilingual) | 8 | 0.126 | 0.446 | 0.510 | | |

- 한국어 페널티: 같은 500개 id에서 ko 0.526 vs en 0.510(McNemar p=0.47), 한국어 서술형 설명 스키마에서는 페널티가 없다. 영어 key 렌더링(intent-20)에서는 ko→en +0.24(p=1.2e-04).
- ablation(dev 절반, multilingual): 한국어 instructions Δ −0.020 / −0.004, 영어 설명 Δ −0.028 / +0.024, 모두 비유의.
- Router auto는 한글 행을 100% multilingual로 보냈다(한글 없는 행 4개만 default).
- domain_8 오답 패턴: smart_home(gold 63, 예측 140)과 general(62, 80)이 흡수원. 체크포인트 선택: multilingual 고정 + `lang="ko"`.

### Track C 견고성 (`results/C/C1_option_order_20261002.md`, `results/C/C_schema_v2_20261002.md`, `results/P4/metrics/full_20261003-1156_option_order_dev.md`)

| 프로브 | 측정 | upstream 참고 |
|---|---|---|
| C1 옵션 순서 flip, router_v1 domain_8 (dev 250, 순열 5) | zero-shot 순열당 **0.270** [0.230, 0.310], any-flip 0.512; confidence ≥ 0.9 결정만 0.094 → **ft-v1 0.037**, any-flip 0.084 | massive_intent.en 0.150 / 0.230, Jev 0.13, zh CS 0.28 |
| C1 ynat_7 / scenario_18 (zero-shot) | 0.168 / 0.241 | |
| C2 스키마 v2 변형 6종 (dev) | v1 0.560 대비 전부 −0.020\~−0.050, 유의 없음; `general` 제거+게이트 대체 기각(AUROC 0.574); v1 확률 5클래스 합산 0.682(계약 변경) | |
| 위치 편향 | 첫 옵션 과소예측(productivity 12 vs gold 30), smart_home 흡수는 의미적 → 기각 | |
| C3 noul vs 2-choice (NSMC, Track B) | choice 0.774 vs noul 0.638 (p=6.5e-10, 의미 key) | |
| C4 부정문, C6 고카디널리티, C8 장문 | 미실행 | |

### Track D 성능 (`results/D/D_summary_20261003.md`, Apple M4 Pro 단독 실행)

| 구성 | p50 | p95 | 처리량 | 파일 |
|---|---|---|---|---|
| multilingual 3q in-process, MPS (short 59 tok) | 22.5 ms | 22.6 ms | | 20261003-1249_latency_matrix |
| multilingual 3q in-process, CPU 10 threads | 56.4 ms | 57.8 ms | | 같음 |
| multilingual 1q / 10q, MPS vs CPU | 13.8 / 62.4 vs 37.7 / 121.4 ms | | CPU÷MPS 1q 2.73x | 같음 |
| laya-serve MPS, open-loop 10 RPS, 3q | 63.5 ms | 79.4 ms (p99 85.1) | 503 0 | 20261003-1330_http_mps |
| laya-serve CPU, 10 RPS, 3q | 99.9 ms | 135.8 ms | | 20261003-1343_http_cpu |
| laya-serve closed-loop 포화 | | | MPS 1q 50 / 3q 22.6 RPS, CPU 3q 10 RPS | 같음 |
| predict_batch CPU n=256, bs 8 sort vs unsorted | | | 1.67x (loop 대비 1.39x), flip 0 | 20261003-1314_batch |
| cold load (캐시 warm) | multilingual 3.45\~3.67 s, english 2.82\~2.97 s | | | 20261003-1306_coldload |
| ONNX int8 vs torch CPU (ynat 500, batch 16) | 525.9 vs 302.2 ms | | acc 0.622 vs 0.634, ECE +0.0154 | 20261003-1347_*_ynat |
| RSS 상주 1 / 2 / 3 체크포인트 (CPU) | 2.07 / 3.63 / 5.23 GiB | | | 20261003-1307_rss_preload |

추가 관찰: MPS fp16 autocast 이득 ≤ 8%; 간헐 호출(idle ≥ 100 ms)에서 MPS 2.2\~3.6배 둔화; intra-op 10이 최적(14는 2\~22% 느림); 체크포인트 전환 0.13\~0.21 s(로컬 경로).

### Track E 캘리브레이션 (`results/E/E_summary_20261002.md`, zero-shot multilingual; ft-v1은 `results/P4/metrics/full_20261003-1156_coverage_*.md`)

| 체크포인트 | 버킷 / T | ECE 전 → 후 (domain_8 test) | coverage @ 오류 ≤ 5% | @ ≤ 10% |
|---|---|---|---|---|
| zero-shot, pooled refit | choice:6-10, T 1.9161 | 0.263 → 0.098 [0.081, 0.162] | 0.224 (상한 a/(1−e) 0.518) | 0.308 |
| zero-shot, per-task refit | T 2.0245 | 0.263 → 0.123 | | |
| ft-v1 (스크립트 자체 보정) | 단일 T | 0.053 (2,917행 0.057) | test 절반 사후 T 0.756; 2,917행 dev T 0.907 적용 0.923(오류 0.042) | 1.000 |

도메인별 T는 dev 과적합으로 기각. E6: NSMC noul AUROC test 0.822, dev Youden 임계값 0.0073 → test 정확도 0.725(0.5 기준 0.641, 2-choice 0.773). payload `poc/calibration/ko_v1.json`은 zero-shot 체크포인트 전용.

### Track F 베이스라인

| 베이스라인 | 세트 | 값 | laya 대비 | 출처 |
|---|---|---|---|---|
| majority / random | domain_8 | 0.126 / 0.125 | zero-shot +0.40, ft-v1 +0.77 | `data/evals/MANIFEST.json` |
| majority / random | ynat_7 | 0.144 / 0.143 | +0.49 | 같음 |
| majority / random | nli_3, nsmc, kmhas_hate, 3i4k | 0.334, 0.500, 0.500, 0.144 | +0.42, +0.27/+0.14, +0.08, +0.03 | 같음 |
| Jev (제3자 공개, 영어) | AG News / Banking77 / Emotion | 0.910 / 0.870 / 0.480, p50 236\~276 ms, ECE 0.246, flip 0.13 | 한국어 수치 없음 | BENCHMARKS.md §Headline, research/README.md |
| LLM zero-shot (claude-haiku-4-5) | | **미실행**(API 키 미제공) → G1은 절대 기준 0.80 적용 | | |
| Jev (수동 비교 파일럿, 한국어) | domain_8 test 절반 24행 | 0.833 (20/24), 표시 지연 중앙값 249.5 ms | zero-shot 0.417보다 높고(p=0.002) ft-v1 0.917과는 구분 불가(p=0.5) | `results/F/jev_playground_manual_20261006.md` |

#### Jev 수동 비교 파일럿 (공개 플레이그라운드, n=24, 2026-10-06)

이 절은 통제 비교 전에 한 한국어 파일럿이다. 같은 입력 규칙으로 8과제를 비교한 본 결과는 §0a에 있다.

`results/F/jev_playground_manual_20261006.md`, run card `results/F/F_jev_20261006.md`, 원기록 `results/F/jev_runs_raw.jsonl`(25건, 공개 저장소에는 포함하지 않음), 표본 `results/F/jev_sample_24.jsonl`, 스크린샷 `results/F/jev_shots/`(공개 저장소에는 포함하지 않음).

- 프로토콜: `ko_massive_domain_8` test 절반에서 train과 겹치는 16행을 뺀 234행 중 도메인별 3행씩 `random.Random(13)`으로 24행. Jev에는 Laya와 같은 정보를 줬다: 질문 "Which domain should handle this request?", 선택지 8개를 Laya 렌더링과 같은 `key: 한국어 설명` 형식으로 같은 순서(`poc/schema/router_v1.json`). 공개 사이트 https://jevplayground.com 에서 수동 속도로 실행(총 25회 요청, 502 1회 포함, 간격 ≥ 21 s), 영어 key 전용 pass 2는 생략. Laya 수치는 재실행 없이 Track B·P4 리포트에서 같은 행을 조회했다.

| 시스템 | 맞힌 수 | 정확도 | Wilson 95% |
|---|---|---|---|
| Jev (typesafe-ai/jev, 플레이그라운드) | 20/24 | 0.833 | [0.641, 0.933] |
| Laya zero-shot (multilingual) | 10/24 | 0.417 | [0.245, 0.612] |
| Laya ft-v1 (파인튜닝) | 22/24 | 0.917 | [0.742, 0.977] |

- 일치도·McNemar: Jev vs zero-shot 같은 라벨 10/24, b=10, c=0, p=0.002(zero-shot이 맞힌 행은 Jev도 전부 맞힘). Jev vs ft-v1 같은 라벨 20/24, b=0, c=2, p=0.5(Jev가 맞힌 행은 ft-v1도 전부 맞힘). ft-v1이 22/24라 Jev가 24/24여도 p=0.5인 구조이므로 ft-v1 대비 우열은 이 표본으로 판정 불가.
- 도메인별 정답 수(Jev / zero-shot / ft-v1, 각 3행): productivity 3/0/3, media 1/0/3, smart_home 3/3/3, info_qa 3/0/3, communication 3/2/3, lifestyle 3/2/3, transport 3/3/3, general 1/0/1.
- 지연: 플레이그라운드 표시값("server + network") 중앙값 249.5 ms(203\~570, 제3자 공개 p50 236\~276 ms 범위 안), 브라우저에서 잰 POST 중앙값 497.5 ms. 우리 로컬 값은 P2 왕복 p50 20.1 ms(`results/poc/P2_20261003.md`), Track D in-process 13.8 ms(`results/D/D_summary_20261003.md`). 배수(12\~36배)는 호스팅 서비스와 로컬 실행의 차이에 인터넷 왕복이 섞인 값이라 모델 자체의 속도 비교가 아니다.
- 보정 관찰: Jev는 틀릴 때 확신하지 않았다(오답 4건 top 확률 41\~86%, 정답 평균 96.5%). 90%에서 자르면 18/24를 받아 18/18 정답, ft-v1은 T 0.907에서 22행을 받아 21/22 정답. 플레이그라운드는 확률을 소수 둘째 자리로 반올림해 24회 중 14회가 100%로 표시됐다.
- 가설: Jev 오답 4건 중 2건은 "게임 열어"류(정답 media)로, 우리 media 설명에 "게임"이 없어 Jev가 틀렸고 ft-v1은 학습 데이터에서 이 규칙을 배웠다(Jev의 항목별 출력은 공개 저장소에서 생략). 설명에 "게임"을 넣으면 바뀌는지는 검증하지 않았다.
- 주의: n=24 단일 패스, 공식 API가 아닌 플레이그라운드(모델 버전 미표기, Model ID `typesafe-ai/jev`, 호출당 입력 약 716 / 출력 약 255 토큰), 선택지는 라벨 1칸(설명 필드 없음), 무료 제3자 사이트의 사용량 제한 범위 안에서만 실행.
- **파일럿 판정: Jev는 Laya zero-shot을 확실히 앞서고(한국어 입력도 처리함), 파인튜닝한 ft-v1과는 이 표본에서 구분되지 않는다(Jev 0.833 vs ft-v1 0.917, p=0.5).**

## 3. 사전 실험과 한국어 지원 감사 (`results/poc/`, `results/korean_support/`, `docs/07_korean_support_audit.md`)

- P0 스모크: 환경·parity·레이턴시 통과. 30문장 자가 라벨 프로브에서 CS triage intent 0.40, criteria 없는 noul은 거의 항상 "no"(confidence 0.9+), frustration 레벨 0 선택 0/30.
- P0b 스키마 ablation 8종: intent 최고 0.50(영어 설명), binary 4문항 합계는 어떤 형태도 always-no 기저(93/120)를 넘지 못함, 2-choice A/B는 A로 붕괴, labels A/B 무효과.
- P0c 토픽 라우팅 미리보기(n=100): YNAT 7토픽 0.65(상위 50% coverage 0.86), MASSIVE 18도메인 0.52.
- 한국어 지원 감사: 한국어는 mmBERT 사전학습 high-resource(1.43%)이자 laya 평가 언어(MASSIVE ko 0.470, 51개 중 18위)이지만 RLCD 학습 데이터에는 미문서화; 토크나이저 UNK 0, 조각화 0.2% 이하, 영어 대비 토큰 1.5배, NFD 입력 3.1배 폭증(NFC 정규화 필요); 라우팅은 순수 한글 정상, 라틴 다수 혼합문·10음절 미만 한국어는 english로 감(`lang="ko"` 명시 필요); 같은 문장 ko vs en 페널티는 영어 key 옵션 0.21\~0.24, 한국어 설명 0.10(비유의); noul no-편향·score 레벨 0 회피는 영어 입력에서도 동일(체크포인트 성질, noul AUROC 0.76\~0.92).

## 4. P4 파인튜닝 (`results/P4/P4_probe_20261002.md`, `results/P4/metrics/full_20261003-1156_summary.md`, `results/P4/full_20261003-1156_driver.log`)

- 데이터: MASSIVE ko train 11,514 → 11,094행(중복·길이 필터), validation 2,033 → 2,012행, 도메인 8개 자연 분포. 학습 아이템에 옵션 순서 셔플 증강(11,093/11,094 재배열), validation 400행으로 보정.
- 설정: mb 8 × ga 4(effective 32), 3 epoch(1,041 step), fp32, gradient checkpointing 끔, MPS 유휴 GPU. 학습 2,150 s(35.8분), 평가 약 10분. MPS peak 약 8 GB.
- 프로브(1,000행 1 epoch): test 절반 0.492 → 0.720.

| 평가 | base multilingual | ft-v1 | 중복 제외 (train 동일 발화 제외) |
|---|---|---|---|
| domain_8 500행 all / dev / test | 0.526 / 0.560 / 0.492 | 0.894 / 0.888 / **0.900** [0.860, 0.936] | test 0.893 (n=234) |
| domain_8 전체 test 2,917행 | 0.475 | **0.913** [0.902, 0.923] | 0.908 (n=2,762) |
| validation 2,012행 (epoch 1 / 2 / 3) | 0.462 | 0.892 / 0.916 / 0.918 | 0.914 |
| ECE test / 2,917 | 0.263 / 0.253 | 0.053 / 0.057 | |
| YNAT dev 245 (망각 검사) | 0.612 | 0.633 | |
| 옵션 순서 flip (dev 250, 순열 5) | 0.270 | 0.037 (any-flip 0.084) | |
| coverage @ 오류 ≤ 5% (test 절반 / 2,917) | 0.224 | 0.756 (사후 T) / 0.923 (dev T 0.907) | |

남은 혼동은 general ↔ info_qa(2,012행 기준 general→info_qa 25, info_qa→general 20). epoch 2 대비 3은 비유의라 최종 export(epoch 3)를 v1으로 채택.

## 5. P2 서비스·데모 UI (`results/poc/P2_20261003.md`, `results/poc/P2_ui_check.md`)

ft-v1 체크포인트를 올린 서비스와 Laya Playground가 수용 점검 11/11을 통과했다. `poc/service/app.py`(142줄)가 `Router(models={"multilingual": "poc/finetune/ckpt_domain8_v1", "english": "models/laya"})`를 만들어 `laya.serve.create_app(router)`에 주입하고 `/poc/decide`, `/poc/shadow`, `/poc/meta`, 정적 `/poc/ui/`를 덧붙인다. 훅은 NFC 정규화 + 이메일·전화·카드번호 마스킹, shadow JSONL 기록, 카운터(`hooks.py` 123줄). 정책 T는 0.907(2,917행 dev-1459에서 오류 5% 이하 최대 coverage, test-1458 적용 시 coverage 0.923·오류 0.042, `policy.py:4`).

| 점검 | 결과 |
|---|---|
| 인증 | 키 없음·틀린 키 401, 키 있음 200. `/health`는 liveness만 |
| `/poc/meta` 대조 | questions_sha256 a7f2f6b8…, rl_agent_config sha 3270d480…, weights sha b0609f54… 모두 P4 리포트·MANIFEST와 일치 |
| 8도메인 예시 + 문서 예시 | 9/9 ROUTE, 정답 도메인 9/9, p 0.924\~0.957, 라우팅 사유 explicit lang='ko' |
| FALLBACK | 무의미 문자열 p 0.222, 다중 의도 p 0.669 → FALLBACK; `min_confidence` 1.0 → abstained |
| PII | shadow에 `[email]`·`[phone]`·`[card]`만 기록, 원문 0건 |
| 일반 모드 `/v1/systemone` | 3지선다 200, technical 0.985 |
| shadow 카운터 | 50건 = total, ROUTE 44 + FALLBACK 5 = 도메인별 합 |
| in-process 대조 | CPU ft-v1 vs 서버 MPS 9건 중 차이 0, 확률 차 최대 0.0000 |
| 브라우저 점검 | 05 §6 10개 항목 + 5초 갱신 전부 ✔; 스크린샷 `results/poc/P2_ui_1.png`(빈 상태), `P2_ui_2.png`(router 예시 ROUTE) \~ `P2_ui_8_server_down.png` |
| `/poc/decide` 왕복 (1문항 30회 연속) | p50 20.1 / p95 21.1 ms (서버 처리 19.5 / 20.4, HTTP 오버헤드 p95 0.7 ms) |

주의: 브라우저에서 몇 초 간격으로 호출하면 서버 처리가 44\~51 ms로 늘어난다(Track D 간헐 호출 페널티와 동일). 예시 9건의 p가 0.92\~0.96에 몰려 T 0.907까지 여유가 0.017\~0.05뿐이다. 일반 모드 질문도 ft-v1이 답하며 품질은 미측정. 부하 측정은 Track D6(base 체크포인트, 같은 구조)로 갈음했고, 503·Retry-After와 413은 UI에서 재현하지 않았다. CLI `laya --model ml`은 Hub base 체크포인트를 쓰므로 ft-v1 대조는 in-process 비교로 수행했다.

## 6. 가설 판정 (`results/verdicts.json`)

| 가설 | 판정 | 근거 | 한 줄 해석 |
|---|---|---|---|
| H1 ko MASSIVE 재현 | 지지 | K2 E2, Δ0 | upstream 수치가 하네스에서 그대로 재현 |
| H2 multilingual ≫ english, Router 100% | 부분 지지 | Track B 10문항 중 7개 ≥ +0.20 | 예외 NSMC noul, K-MHaS, 3i4K |
| H3 ≤7옵션 과제: majority 위, supervised 아래 | 전반부 지지 / 후반부 미결 | Track B; supervised 문헌값 미조회 | ft-v1 0.913은 supervised 범위 |
| H4 as-shipped ECE > 0.25, refit ≤ 0.10 | 부분 / 경계 지지 | domain_8 0.263 yes, ynat 0.148 no; refit 0.098 | pooled fit에 의존 |
| H5 옵션 순서 flip 10\~30% | 지지 | 0.17\~0.27 | 파인튜닝 후 0.037 |
| H6 noul < 2-choice 중립 키 | 미결 | P0b A/B 2-choice 붕괴(68/120), NSMC 의미 key choice 0.774 > noul 0.638 | 중립 key 조건은 미측정 |
| H7 부정문 zero-shot 실패 | 미결 | C4 미실행; P0 프로브 5행 중 4행 오판 | |
| H8 MPS 3\~6x, sub-linear | 기각 | D1 2.33\~2.80x, 10q/1q 4.5\~9.1x | fp16 이득 ≤ 8%, 간헐 호출 둔화 |
| H9 sort_by_length ≥ 1.3x, flip 0 | 지지 | D4 1.67\~2.08x, flip 0 | 정렬 없는 CPU 배치는 loop보다 느림 |
| H10 ONNX int8 ≈ 2x, ECE drift ≤ 0.01 | 기각 | D7 1.74x 느림, ΔECE +0.0154 | Apple silicon에서는 torch fp32가 우세 |

## 7. Go/No-Go 매트릭스 (`results/go_no_go.json`, 기준은 00_README.md §6 제안값)

| 게이트 | 기준 | zero-shot (2026-10-02) | 파인튜닝 ft-v1 (2026-10-03) | 판정 |
|---|---|---|---|---|
| G0 재현 | ±0.03 | Δ0 | 동일 | 통과 |
| G1 정확도 | ≥ 0.80 (LLM 베이스라인 없음) | 0.492 | 0.900 (중복 제외 0.893, 2,917행 0.913) | 통과 |
| G2 coverage @ 오류 ≤ 5% | ≥ 0.70 | 0.224 | 2,917행 0.923(dev T 0.907, 오류 0.042); 250행 사후 T 0.756 | 통과(조건부) |
| G3 refit 후 ECE | ≤ 0.10 | 0.098 | 0.053 | 통과 |
| G4 옵션 순서 flip | ≤ 0.10 | 0.270 | 0.037 | 통과 |
| G5 in-process 3q p95 | ≤ 100 ms MPS / ≤ 500 ms CPU | | MPS 22.6 / CPU 57.8 ms (short), 92.5 / 247.8 (long) | 통과 |
| G6 laya-serve 10 RPS p95 | ≤ 150 ms | | 79.4 ms (MPS), 135.8 (CPU) | 통과 |
| G7 predict vs predict_batch(sort) | flip 0, abs(Δp) ≤ 0.01 | P0 device parity 0.0017 | D4 flip 0, 0.0001 | 통과 |

**최종 판정: Conditional Go(파인튜닝 파이프라인 전제).** 조건은 `docs/05_poc_plan.md` §6 P5: (1) taxonomy별 라벨 데이터 유지와 재학습(36분), 새 체크포인트마다 Track B·C1·E 재실행; (2) `lang="ko"` 강제, NFC 정규화, 단일 T 0.907, 저신뢰·general 유사 요청 FALLBACK, 옵션 순서 고정; (3) 프로세스당 처리량 상한(MPS 3문항 22.6 RPS, CPU 10 RPS)에 맞춘 프로세스 복제; (4) shadow 단계에서 실제 트래픽으로 coverage·오류율 재확인.

## 8. 한계와 주의

- 표본 크기: test 절반 n=250(95% CI 약 ±0.04 at 0.9, ±0.06 at 0.5), MASSIVE 재현 n=100(±0.10), P0 프로브 n=30 자가 라벨(지표성). 2,917행 전체 test가 가장 정밀하다.
- G2의 T는 dev 절반에서 골랐고 250행 test 절반에서는 선택 방식에 따라 오류 7.9%(dev T) 또는 coverage 0.756(사후 T)으로 갈린다. 2,917행에서는 dev T로 오류 4.2%였다.
- train/test 동일 발화 155/2,917행(라벨 동일): 제외 수치 0.908을 병기했다.
- MPS fp16은 5행 이상에서만 켜지며 |Δp| ≤ 0.0085; 품질 수치는 전부 CPU fp32다. MPS는 간헐 호출에서 2.2\~3.6배 느려진다.
- laya-serve는 추론을 직렬 처리하므로 동시성은 지연만 늘린다. 503·Retry-After 경로는 부하가 `LAYA_MAX_CONCURRENT`(16)를 넘지 않아 검증하지 못했다.
- ONNX(fp32·int8)는 이 플랫폼에서 torch보다 느렸다(ORT 10스레드 고정에도 동일). 다른 CPU에서는 다를 수 있다.
- C4 부정문, C6 고카디널리티, C8 장문, F2 LLM 베이스라인은 미실행이다.
- Jev 한국어 파일럿은 n=24 수동 표본(공개 플레이그라운드, 단일 패스)이라 방향성 확인용이다. ft-v1 대비 우열은 이 n으로는 판정할 수 없고(Jev 24/24여도 p=0.5), 공식 API와 500행 paired 비교가 있어야 결론이 난다.
- Laya vs Jev 통제 비교(§0a)도 플레이그라운드 경유이고 과제당 n=40이다. Holm 보정 후 유의한 과제는 T1·T7뿐이고, 최고 Laya 러너는 사후 선택이며, Jev 단가는 확인하지 않았다. 학습 믹스 표기(Laya는 T2·T5만 학습, 나머지 held out)는 upstream의 자기 보고이고 학습 데이터 자체는 확인하지 않았다(`results/F/jev_cmp/summary.md` §9, `third_party/laya/research/scripts/build_benchmark_nb.py:760-762`).
- 3-arm(§0b)의 trained arm은 과제당 학습 run 하나의 표본이다. MPS 학습이 비트 단위로 결정적이지 않아, 스크립트·items·seed·인자가 같은 T1 두 run이 test 0.747 대 0.690(label 기준), 짝 비교 b/c 217/98, p=1.7e-11로 갈렸다. micro-batch 손실은 12번에서 처음 갈라진다. 평가는 결정적이라 보존한 체크포인트를 다시 평가하면 같은 수치가 나오지만, 다시 학습하면 다른 모델이 나온다. 어느 연산이 비결정적인지는 확인하지 않았다(후속 추적: GPU가 빈 뒤 `torch.use_deterministic_algorithms(True, warn_only=True)`로 짧은 run). seed를 바꾼 반복 학습(seed 14)의 T1은 0.735로 V2(b)와 유의차가 없어(b/c 118/96, p=0.1510) 본 학습 T1이 세 run 중 가장 낮다(`results/T3arm/summary.md` §6.4, §7.4, `results/T3arm/PREP_20261008.md` "본 학습 중 발견" 절).
- 학습 믹스 포함 과제에서 dev를 train split에서 떼면 epoch 0 dev가 유효한 vanilla 기준선이 아니다. T5 BoolQ는 vanilla가 dev(train split) 0.986, validation ext 0.834로 upstream 학습에서 본 행을 기억해 dev 기준선이 부풀었고, 그래서 학습 이득이 없는데도(ext 0.834 대 0.832) "학습 실패"로 표시됐다. 같은 구조인 T2·T9와 공개 split이 하나뿐인 T10도 epoch 0 dev를 기준선으로 쓸 때 주의한다(T2는 dev 0.936, ext 0.940으로 차이가 없다). epoch 선택은 trained epoch끼리의 비교라 영향이 작다(`results/T3arm/summary.md` §6.1, `results/T3arm/PREP_20261008.md` "본 학습 중 발견" 절).
- 3-arm의 T10(고객지원 티켓 큐)은 Jev 항목 40행 중 네 시스템(Jev, vanilla english, vanilla multilingual, trained)이 모두 틀린 행이 18/40이다. S7 분석은 오답 다수에서 gold 큐가 질문에 준 큐 설명과 맞지 않는다고 읽었다(해석). 라벨 품질 의심, 수작업 확인 필요이고, 확인 전에는 T10 정확도를 라우팅 능력으로 읽지 않는다(`results/T3arm/summary.md` §1.6, `results/F/jev_cmp/sessions/S7_20261008/S7_summary.md`).
- 3-arm 반복 학습(seed 14)에서 cotenant 경합이 있었다. 다른 프로젝트의 실험 7개와 겹쳐 스왑이 가득 차 T9 학습이 멈췄고, 2026-10-08 19:37에 반복 학습 큐만 중지했다. 감시자 `poc/finetune/autostart_rep_t9t10.sh`가 경합이 끝난 뒤 22:58:42에 T9·T10을 다시 시작했고 2026-10-09 00:23:20에 rc 0으로 끝났다(경합 없음, `results/T3arm/rep_s14/autostart.log`). 계산은 타이밍과 무관해 run 2 결과는 모두 유효하고, 비용(§0b)은 run 1 수치를 쓴다(`results/T3arm/PREP_20261008.md` "반복 학습 T9 중지와 자동 재시작").
- 반복 학습의 불일치 3개(T4 Jev 항목 trained vs vanilla, T8 Jev 항목 trained vs Jev·trained vs vanilla)는 모두 n=40 Jev 항목 비교이고 Holm p가 0.05 근처다. run 2가 8과제 family였던 중간 집계에서는 T6이 불일치였다가 10과제 family에서 확정이 됐고 T4는 반대로 바뀌었다. 이런 경계 판정은 seed와 Holm family 크기에 민감하므로 두 run이 같은 판정만 확정했다(`results/T3arm/summary.md` §7.2).
- 도구 결함(후속 추적): PDF 렌더링에 쓴 Markdown→PDF 렌더러의 smartypants는 HTML 태그를 placeholder로 바꾼 뒤 URL 패턴 `/\bhttps?:\/\/\S+/g`(렌더러의 `src/smartypants.ts:23`)을 적용한다. 링크 텍스트가 URL이면 `\S+`가 바로 뒤의 `</a>` placeholder까지 삼키고 복원은 한 번만 돌아, placeholder 문자열(`SMARTPANTS_PRESERVED_N`)이 본문에 노출되고 `</a>`가 사라져 그 뒤 문서 전체가 링크로 이어진다. 우회: 링크 텍스트에서 URL scheme을 뺀다(`[github.com/x](https://github.com/x)`, 맨 URL 금지). 별도로 GFM은 한 문단·표 칸 안의 `~` 두 개 사이를 취소선으로 렌더링하므로 범위 표기 `~`는 `\~`로 이스케이프한다. 두 우회를 `docs/08_paper_ko.pdf`와 `docs/10_paper_laya_vs_jev.pdf`(PDF는 공개 저장소에는 포함하지 않음)에 적용했다(2026-10-07). 같은 파일의 em dash 규칙 `/(\w|\s)--(\w|\s)/g`(`src/smartypants.ts:81`)은 본문의 CLI 플래그도 바꿔, `docs/08_paper_ko.md:282`의 `laya-evals --onnx`가 PDF에서 em dash로 찍힌다(우회 없음, 플래그를 코드 스팬으로 감싸면 피한다. 08 내용 변경 금지 지시로 미수정). 우회이며 렌더러 수정 또는 렌더러 쪽 이슈 등록은 미결이다(`docs/09_laya_vs_jev_plan.md` 열린 질문 11).
- upstream에서 발견한 결함·불일치: `laya.calibrate.records_from_labeled`에 `@torch.no_grad()` 누락(실제 Agent에서 예외, calibrate.py:286 → agent.py:1177); `laya.evals.evaluate`가 `predict(..., model=)`을 호출해 `Agent.predict`와 호환되지 않음(Router 또는 래퍼 필요); `hf download`의 agent 모드 출력 접두어로 문서 명령이 깨짐(`--quiet` 필요); 모델 카드 "Korean 0.490"은 T4 n=300 값이고 공식 표는 0.470; "multilingual의 criteria-less noul은 state를 읽는다"는 README 주장이 한국어·영어 번역 모두에서 성립하지 않음; MASSIVE HF 미러의 license 태그 apache-2.0 vs 원 저장소 CC BY 4.0; `examples/README.md`의 MPS 첫 호출 13 s는 이 머신에서 0.1 s.

## 9. 재현 방법

1. 환경: `docs/02_environment_setup.md` §2(uv venv 3.12, `laya[serve,onnx,structured]==0.3.23`, `hf download convaiinnovations/laya --revision 55cf4c4… --quiet`, `models/` 심링크, `env.sh`) → §3 스모크(`laya-evals run third_party/laya/research/evals/fixture.jsonl --model english --device cpu`).
2. 평가셋: `.venv/bin/python scripts/build_ko_evalsets.py all --n 500 --seed 13` + ablation 변형(04 §6).
3. Track A: `results/korean_support/K2_build.py` + laya-evals(ko/en intent-20) 또는 `laya-evals run data/evals/ko_massive_intent_20opt.jsonl --model multilingual --device cpu`.
4. Track B: `results/B/B_run.sh`(46런) → `scripts/metrics_extra.py summary|paired` → `results/B/B_summary.py`.
5. Track C: `scripts/probe_option_order.py … --permutations 5 --seed 13 --split dev`, `results/C/C_schema_v2_build.py` + laya-evals.
6. Track E: `scripts/calibrate_ko.py --sets … --splits results/B/B_splits.json --pooled --per-task --min-bucket-n 100 --out-payload poc/calibration/ko_v1.json`.
7. Track D: `results/D/D_run.sh`(scripts/bench_latency_local.py, bench_batch_local.py, bench_http_local.py, export_onnx + laya-evals --onnx).
8. P4: `.venv/bin/python poc/finetune/make_domain8_items.py rows|items`, `bash poc/finetune/run_full.sh`(11,094행 × 3 epoch, 평가 포함).
9. P2 서비스: `LAYA_DEVICE=mps LAYA_API_KEY=devkey LAYA_HOST=127.0.0.1 .venv/bin/uvicorn poc.service.app:app --host 127.0.0.1 --port 8000` → `open http://127.0.0.1:8000/poc/ui/` (수용 점검: `.venv/bin/python results/poc/P2_acceptance.py`).
10. 대시보드: `python3 scripts/build_dashboard.py --results results/ --out results/dashboard/index.html`.
11. Laya vs Jev 비교: 세트 `scripts/build_jev_cmp_sets.py all`, Laya `bash results/F/jev_cmp/run_laya.sh`, Jev 기록 분석 `results/F/jev_cmp/jev_cmp.py analyze`, 종합 `results/F/jev_cmp/s6_summary.py build` 후 `verify`(전체 명령은 `results/F/jev_cmp/summary.md` §10). 분석은 기록된 jsonl만 읽는다. Jev 세션을 다시 돌리려면 공개 사이트 요청이 필요하고 `docs/09_laya_vs_jev_plan.md` §2 운영 규칙을 따른다.
12. 3-arm 비교: 준비·검증(S0·S1) 명령은 `results/T3arm/PREP_20261008.md` "명령어" 절. 본 학습(S2) `bash poc/finetune/run_all_tasks.sh`(게이트 `poc/finetune/READY_T3ARM`, 시작 전 `PREFLIGHT_ONLY=1 bash poc/finetune/run_all_tasks.sh`로 점검), 종합(S3) `nice -n 10 .venv/bin/python results/T3arm/t3arm_summary.py build --root results/T3arm --out results/T3arm` 후 같은 인자로 `verify`. 보정 분리 열(vanilla + 과제 T)은 `bash poc/finetune/t3arm_calib_sep.sh`(결과 `results/T3arm/calib_sep/`, 상태 로그 끝 줄 `CALIB_SEP FINISHED`), 반복 학습은 `SEED=14 RUN_TAG=rep_s14 bash poc/finetune/run_all_tasks.sh`(결과 `results/T3arm/rep_s14/`)다. T9 중지 뒤의 재시작 감시자는 `nohup perl -MPOSIX -e 'setsid; exec @ARGV' bash poc/finetune/autostart_rep_t9t10.sh >/dev/null 2>&1 &`이고, 조건이 맞으면 `SEED=14 RUN_TAG=rep_s14 TASKS="T9 T10" bash poc/finetune/run_all_tasks.sh`를 돌린다(상태 `results/T3arm/rep_s14/autostart.log`). T9·T10 Jev 기록 분석은 `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S7 T9_enron_spam_40`(T10은 `T10_support_tickets_queue_40`)이고, 사이트 요청이 필요한 수집 절차는 `results/F/jev_cmp/sessions/S7_20261008/S7_run_card.md`에 있다. 종합은 기록된 리포트만 읽고 모델 로드와 평가를 하지 않는다. 학습은 MPS 비결정성 때문에 같은 명령으로도 비트 단위로 재현되지 않는다(§8).

## 10. 부록

- run_id 전체 목록과 파일 링크: `results/dashboard/index.html` §10 (B 47, C 2+9, D 19, E 2, P4 21, poc 32, korean_support 19개 리포트 JSON).
- 런 카드: `results/env/smoke_20261002.md`, `results/poc/P0_20261002.md`, `P0b_20261002.md`, `P0c_20261002.md`, `results/korean_support/K2_20261002.md`, `results/B/B_20261002.md`, `results/C/C_20261002.md`, `results/E/E_20261002.md`, `results/D/D_20261003.md`, `results/P4/P4_probe_20261002.md`.
- Laya vs Jev 런 카드: `results/F/jev_cmp/S0_20261006.md`(Laya 측), `results/F/jev_cmp/sessions/S{1,1b,2,3,4,5}_*/S*_run_card.md`(Jev 세션), `results/F/jev_cmp/S6_20261007.md`(종합).
- 결정 기록: 00_README.md §5(시나리오 C 선택, P4 진행), 05 §2·§6 P5(판정과 조건), 07 §6(한국어 운영 결정). ADR 파일(docs/decisions/)은 작성하지 않았다.

[English](REPORT.md) | **한국어**
