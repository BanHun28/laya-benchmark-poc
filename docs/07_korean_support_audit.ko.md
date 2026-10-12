# 07. 한국어 지원 감사 결과와 설계 함의

**목적**: Laya 0.3.23(체크포인트 55cf4c4)이 한국어를 "제대로" 지원하는지를 문서 근거, 토크나이저·인코더, 라우팅, 모델 실측의 네 층위로 판정하고, 그 결과를 03(벤치마크)과 05(PoC) 설계에 반영할 결정으로 정리한다.
**선행 문서**: `01_laya_analysis.md`(아키텍처·Router), `02_environment_setup.md`(환경), `05_poc_plan.md`(PoC 스키마·게이트), P0 run card(`results/poc/P0_20261002.md`, `P0b_20261002.md`, `P0c_20261002.md`).
**산출물**: `results/korean_support/audit_docs_tokenizer_routing.md`(문서·토크나이저·라우팅 감사), `results/korean_support/paired_ko_en_audit.md`와 `K2_20261002.md`(한국어 vs 영어 실측), `results/korean_support/part3_routing_battery.md`(라우팅 46건 배터리), 원본 모델 카드·논문 `results/korean_support/cards/`.

측정일 2026-10-02. 실측은 전부 CPU fp32, n은 표마다 명시한다. n=100이면 95% CI 폭이 약 ±0.10, n=30이면 약 ±0.17이다.

## 1. 판정 요약

한국어는 Laya에서 **지원되는 평가 언어**이지 **학습·보증 언어**는 아니다. 순수 한국어 입력은 토크나이저(UNK 0, 조각화 0.2% 이하), 라우팅(hangul 스크립트 감지), 모델 모두 정상 동작하고, upstream이 공개한 한국어 수치(MASSIVE ko intent-20: multilingual 0.470, english 0.110)는 우리 하네스에서 Δ0으로 재현된다. 같은 내용을 한국어와 영어로 넣었을 때 영어 대비 페널티는 옵션 텍스트가 영어 key면 0.21\~0.24(유의), 한국어 서술형 설명이면 0.10(n=100에서 비유의, `play` 클래스 한 곳에 집중)이다. P0에서 본 noul의 "no" 편향과 score 레벨 0 회피는 같은 문장의 영어 번역에서도 동일하게 나타나므로 한국어 문제가 아니라 multilingual 체크포인트의 성질이다. 라틴 문자가 다수인 혼합문의 라우팅과 NFD 입력은 애플리케이션 측에서 보완해야 한다.

| 층위 | 판정 | 근거 강도 |
|---|---|---|
| 문서 근거 | 한국어는 MASSIVE 평가 언어 50개의 하나로만 문서화됨. 인코더(mmBERT) 사전학습에는 1단계 high-resource 언어로 포함. Laya의 RLCD 결정 학습 데이터에 한국어가 있다는 기록은 없음 | 인코더: 강함(논문 Table 9). Laya 평가: 약함\~중간(n=100/300, 카드 수치 출처 혼재). Laya 학습: 기록 없음 |
| 토크나이저·인코더 | multilingual 토크나이저는 한국어를 음절 단위로 정상 처리(UNK 0). 영어 대비 토큰 1.5배. NFD 입력과 희귀 음절이 약점 | 강함(P0 토큰 수 34/661 정확 재현) |
| 라우팅 | 순수 한글은 신뢰 가능. 라틴 다수 혼합문, 영어 래퍼 속 짧은 한국어는 english로 가는 구조적 실패 | 강함(결정적 규칙, lang.py 줄 단위 인용, 46건 배터리) |
| 모델 실측 | upstream 수치 Δ0 재현. 영어 대비 페널티 0.10\~0.24(옵션 텍스트 언어에 좌우). noul·score 약점은 언어 무관 | 중간(n=100 쌍 2종, n=30 번역 프로브) |

## 2. 문서 근거

출처는 `results/korean_support/audit_docs_tokenizer_routing.md` Part 1과 `results/korean_support/cards/`의 원본이다.

| 항목 | 확인 내용 | 출처 |
|---|---|---|
| `ko` 언어 태그 | `convaiinnovations/laya-multilingual` 카드에 있음. 태그 50개는 MASSIVE 평가 언어 집합과 양방향 차집합 0으로 정확히 일치. 즉 "평가한 언어" 목록 | `cards/convaiinnovations_laya-multilingual/README.md:5`, `part1_docs_evidence.json` |
| 지원 언어 표현 | "covering 100+ languages" 한 구절뿐 | 같은 카드 L15 |
| 번들 카드 (`convaiinnovations/laya`) | `language:` 필드 없음. "English only on root" | 번들 카드 L373 |
| 본문의 한국어 언급 | "Korean 0.110 → 0.490" 한 문장. 0.110은 CPU sweep의 english 값(n=100), 0.490은 T4 run의 multilingual 값(n=300, `research/results/t4_colab_benchmark.json`)으로 서로 다른 run의 혼합. 현재 공식값은 `BENCHMARKS.md:71`의 0.470(n=100, ECE laya 0.680 / multilingual 0.311) | multilingual 카드 L116-118 |
| 인코더 | `jhu-clsp/mmBERT-base`. model type modernbert, vocab 256,000, max position 8,192. `_name_or_path`는 없고 `rl_agent_config.json`의 `encoder` 필드가 출처 | `models/laya-multilingual/encoder/config.json:55,78,52`(공개 저장소에는 포함하지 않음), `rl_agent_config.json:2` |
| mmBERT 사전학습의 한국어 | 카드에 `kor` 명시, Gemma 2 tokenizer, "60 high-resource → 110 → 1833" 3단계 커리큘럼. 논문 Table 9: 한국어 pre-training 28.4B 토큰(1.43%), 총 43.9B, 89개 언어 중 13위. pre-training 단계가 60개 언어만 쓰므로 한국어는 1단계 high-resource 언어. 단 FineWeb2-HQ 20개 언어에는 한국어가 없다(ja, zh는 포함). 한국어 전용 벤치마크 수치는 카드·논문 어디에도 없음 | mmBERT 카드 L775, L1925, L1884. arXiv 2509.06888 Table 9 |
| 토크나이저 동일성 | laya 토크나이저는 mmBERT 토크나이저와 vocab·merges(580,604)가 같고, MASSIVE ko 300문장에서 토큰 id 300/300 일치 | `part1b_tokenizer_origin.json` |
| 51개 언어 표에서 한국어 위치 | accuracy 0.470은 51개 중 18위(nl과 동률), 중위수 0.400, macro 0.4008. ECE 0.311은 10위, 중위수 0.397, macro 0.391. ko/en = 0.470/0.710 = 0.662. n=100이라 CI [0.375, 0.567]. ja 0.64, zh 0.65보다 낮음 | `BENCHMARKS.md` §Languages 표 |
| upstream의 다른 한국어 근거 | presentation check에서 ko가 −0.570 FAIL로 4개 언어 중 최악. 테스트 문장은 비원어민 작성. 그 밖에는 `lang.py:43`의 hangul 범위와 테스트 몇 줄뿐. 중국어는 `research/evals/zh_decision_bench.jsonl`과 `BENCHMARKS.md:422` 섹션이 있지만 한국어 데이터셋은 없음 | `research/eval/README.md:308-313, 383-385` |
| 언어 감지의 한국어 | 불용어 목록은 az, bn, de, en, es, fr, it, nl, pt, ro, sv 11개뿐. 비라틴 문자는 `language=None`을 돌려주므로 "ko" 코드는 나오지 않고 script "hangul"로만 식별 | `laya/lang.py:57-168`, `:581-584` |
| 학습 데이터 | 문서에 학습 출처로 나오는 데이터셋은 전부 영어. "Neither checkpoint trained on typed-decisions, MASSIVE or XNLI". 한국어 RLCD 학습 데이터는 문서화되어 있지 않음. 한국어 수치는 zero-shot 전이로 읽어야 함 | `README.md:1352-1353`, `BENCHMARKS.md:138-148`, `research/results/t4_colab_benchmark.json:4309` |

## 3. 토크나이저와 토큰 예산

출처: `results/korean_support/audit_docs_tokenizer_routing.md` Part 2, `part2_tokenizer_stats.json`, `part2_massive_pairs.jsonl`. 토크나이저만 실행했고 모델 forward는 없다.

| tokenizer / 세트 | tok/char | tok/word | 음절당 tok | 조각화 % | UNK |
|---|---|---|---|---|---|
| multilingual / MASSIVE ko (300) | 0.726 | 2.21 | 0.98 | 0.10 (음절 1개 '딨') | 0 |
| multilingual / MASSIVE en (300) | 0.215 | 1.07 | n/a | 0 | 0 |
| multilingual / P0 ko (30) | 0.682 | 2.83 | 0.95 | 0.17 ('ㅠㅠ') | 0 |
| multilingual / KLUE YNAT (100) | 0.794 | 3.30 | 1.11 | 0 | 0 |
| english / MASSIVE ko (300) | 1.698 | 5.16 | 2.30 | 90.6 | 0 |
| english / MASSIVE en (300) | 0.221 | 1.11 | n/a | 0 | 0 |
| english / P0 ko, YNAT | 1.53 / 1.78 | 6.33 / 7.38 | 2.12 / 2.47 | 82.1 / 91.2 | 0 |

- 같은 의미 문장 쌍의 토큰 비율(ko/en): multilingual로 양쪽 모두 재면 중앙값 1.50, p90 2.20. english로 재면 중앙값 3.43, p90 5.0.
- multilingual은 사실상 음절 단위로 자른다. vocab에 여러 음절짜리 한글 항목은 369개뿐이고, KS X 1001 상용 음절 2,350개 중 1,551개(66%)만 단일 토큰이다. 나머지는 음절당 byte 토큰 3개로 쪼개지지만 실제 텍스트에서는 드물다.
- english 토크나이저의 UNK 0은 읽을 수 있다는 뜻이 아니다. byte-level BPE는 구조적으로 UNK를 내지 않고, 실제로는 토큰의 91%가 글자 미만의 byte 조각이다. 이것이 english 체크포인트가 한국어를 못 읽는 기계적 이유다.
- **NFD 입력 위험(새로 발견)**: multilingual 토크나이저의 normalizer는 공백 치환뿐이고 NFC 정규화가 없다. laya 코드에도 `unicodedata.normalize` 호출이 없다. NFD로 분해된 한국어는 토큰이 3.09배로 늘고 자모와 byte 조각이 된다. macOS 파일명이나 일부 클라이언트가 NFD를 보내므로 추론 전에 `unicodedata.normalize("NFC", text)`를 적용한다(05 RedactHook 또는 별도 전처리 훅).

**토큰 예산.** laya의 `build_sequence`로 P0의 `state_tokens` 34와 `input_tokens` 661을 정확히 재현했다. state 공간은 질문마다 따로 잡히며 7문항이라고 7등분되지 않고, head가 가장 긴 질문이 한도를 정한다(P0에서는 intent 질문의 896토큰).

| 조건 | 들어가는 state 분량 |
|---|---|
| multilingual, `max_len=1024`, 7문항 v1 head, 한국어 | 약 1,120\~1,310자 (MASSIVE 기준 1,227자, P0 메시지 비율 기준 1,259자) |
| 같은 조건, 영어 | 약 4,150자 (같은 내용 기준 한국어는 영어의 약 68%) |
| multilingual, `max_len=8192`, 한국어 | 약 11,100자 |
| english 체크포인트로 잘못 라우팅된 한국어 | 약 190자 |

## 4. 라우팅

출처: `results/korean_support/part3_routing_battery.md`, `part3_routing_battery.json`, `laya/lang.py`(설치본은 upstream @4aa6761과 byte 동일). 모델 로드 없이 `Router().route()`와 `laya.lang.analyse()`만 썼다.

**규칙(lang.py)**

| 줄 | 규칙 |
|---|---|
| `:364-371` | `NON_LATIN_FRACTION=0.2`, `NON_LATIN_MIN_FRACTION=0.1`, `NON_LATIN_MIN_LETTERS=10` |
| `:573-576`, `:407` | 라틴 문자가 다수일 때, 비라틴 문자가 2글자 이상 연속으로 있고(`len(w) >= 2`) 비율이 0.2 이상이거나, 0.1 이상이면서 10글자 이상이면 비라틴으로 뒤집는다 |
| `:297-320` | 글자 수는 한글 1음절 = 1글자로 센다 |
| `:631-633` | dict·대화 턴 같은 구조화 입력은 필드 하나에 비라틴 글자가 10개 이상이어야 따로 잡힌다 |
| `:678` | plain string은 필드별 검사를 건너뛴다 |
| `router.py:833-865`, `:519` | 라우터 분기, 기본값 `default="english"` |

**배터리 결과(46건)**: 정상 28, 영어/한국어 어느 쪽이든 무방 4, `default` 설정에 따라 갈림 4, 실패 10. 정상으로 처리된 것: 순수 한국어, "네" 1음절, 자모(ㅋㅋ/ㅠㅠ/ㅇㅋ), 한자 혼용 헤드라인, NFD 입력, 이모지 섞인 한국어, 이메일·전화번호 섞인 한국어, 한글이 다수인 API 용어 혼합.

| 실패 유형 | 예 | 경로 | 원인 |
|---|---|---|---|
| F1 라틴 다수 혼합문 | "Stripe webhook이 timeout 나요", "Kubernetes pod가 ...", "iPhone 15 Pro Max 환불", URL이 붙은 요청 2건 | 언어 미결정 → `default`(english). 영어 에러 메시지를 붙여넣은 질문(`TypeError ...`)은 `language=en`으로 판정되어 default를 바꿔도 english | MASSIVE에서 같은 의미일 때 한글 1음절 ≈ 영어 2.59글자인데 둘 다 1글자로 세어 한국어 내용이 약 2.6배 과소평가됨. 영어 문맥이 40글자를 넘으면 한글이 전체 글자의 10% 이상이면서 10음절 이상이어야 multilingual |
| F2 영어 래퍼 안의 짧은 한국어 | dict 필드 "환불해 주세요"(5음절), 대화 턴 "환불 부탁드려요"(7음절) | english. default와 무관 | `:631-633`의 10글자 하한 |
| F3 입력 형태 의존 | 긴 영어 템플릿 + 19음절 한국어 | plain string이면 english, dict면 multilingual. dict 경로의 reason은 "0% non-English letters"로 실제 이유를 드러내지 않음 | `:678` plain string은 필드별 검사 생략 |
| F4 단음절 + 라틴 | "네 OK" | `default` | 비라틴 연속 2글자 조건 미달 |
| F5 로마자 한국어 | "gyeoljega du beon dwaesseoyo" | `default` | 불용어 목록 없음 |
| F6 이모지만 | 이모지 단독 | `default` | upstream 테스트로 고정된 의도된 동작 |

| 완화 수단 | 해결 범위 |
|---|---|
| `predict(..., lang="ko")` 또는 `lang_guess` (`router.py:811-831`) | 전부 해결(배터리로 확인) |
| `Router(default="multilingual")` / `LAYA_DEFAULT_MODEL=multilingual` | F1의 언어 미결정 케이스와 F4\~F6만. 영어 에러 붙여넣기, F2, F3은 해결 못 함 |
| env.sh 주석 "한글은 항상 감지되므로 한국어에는 무관" | 틀림(F1, F4). 정정함 |

한국어 트래픽이 주력이라면 채널·로케일 메타데이터로 `lang="ko"`를 명시하는 것이 유일하게 완전한 해법이다.

## 5. 모델 실측: 한국어 vs 영어

출처: `results/korean_support/paired_ko_en_audit.md`, `K2_analysis.md`, run card `K2_20261002.md`. MASSIVE는 로케일 간 병렬 코퍼스이므로 같은 `id`의 ko/en 쌍은 같은 내용이다(첫 100쌍의 label_text 전부 일치, `K2_build.py` assert). 모든 실행은 `laya-evals --device cpu --batch-size 8 --slice qid`, revision 55cf4c4, 13런 모두 exit 0.

### E1 scenario-18 (multilingual, n=100 쌍)

| 질문 형태 | ko | en | en − ko (95% CI) | McNemar p (b/c) | english 체크포인트, en |
|---|---|---|---|---|---|
| 한국어 서술형 설명 (P0c base) | 52 | 62 | +0.10 (−0.02..+0.22) | 0.143 (14/24) | 50 (옵션이 9토큰으로 잘려 상한이 아님) |
| upstream key 렌더링 | 35 | 56 | +0.21 (+0.12..+0.30) | 4.9e-05 (3/24) | 65 (p=0.023 vs multilingual) |

- ko 두 런은 P0c와 argmax 100/100 일치한다.
- 주의: english 체크포인트는 `head_max_len=192`라 한국어 설명을 옵션당 22토큰(domain_8 기준, 04 §7 stats)으로 자른다. 그래서 한국어 페널티 측정은 두 파일 모두 multilingual로 하고, english 열은 참고치다.
- 한국어 설명은 ko를 +0.17(p=4.9e-04) 올리고 en은 −0.06(비유의) 내린다. 영어 우위의 크기는 옵션 텍스트 언어에 달려 있다.
- 사후 분해: 한국어 설명 형태의 차이 10건은 전부 `play` 17행에서 나왔다(ko 1 vs en 11). 나머지 83행은 51 vs 51(p=1.0). en 정답 11건은 모두 발화에 "play"라는 단어가 그대로 들어 있다.
- ECE / mean confidence: ko 0.250 / 0.747, en 0.168 / 0.772. macro-F1(정답에 등장한 10개 클래스 기준): ko 0.550, en 0.646.

### E2 intent-20, upstream 충실 구성 (n=100 쌍)

| | ko / multilingual | en / multilingual | en / english | ko / english |
|---|---|---|---|---|
| 정확도 (x/100) | 47 | 71 | 82 | 11 |
| upstream 공개값 | 0.470 | 0.710 | 0.820 | 0.110 |
| ECE 측정 / upstream | 0.3108 / 0.3108 | 0.2333 / 0.2333 | 0.1383 / 0.1382 | 0.6804 / 0.6804 |

- ko vs en(multilingual): +0.24 (+0.13..+0.35), McNemar p=1.2e-04 (7/31). en에서 english vs multilingual: +0.11, p=0.035.
- **Track A 재현**: 네 칸 모두 Δ 0.000으로 ±0.03 이내. mean confidence와 acc@50%cov도 일치. H1(01 §9)이 이 경로에서 성립한다. 옵션 구성은 upstream `laya_eval.build_suite`와 ko·en 모두 같다(`K2_build.py:196` assert).
- 점수 방식은 다르다. laya-evals는 100행을 모두 단독 forward로 처리했고(rows_alone=100), upstream은 packed forward를 쓴다. 이 해상도에서는 차이가 드러나지 않았다.
- 페널티의 상당 부분은 영어 발화가 영어 옵션 key와 글자로 겹치는 효과다. key 단어가 발화에 겹치는 행은 en이 +14/44, 겹치지 않는 행은 +10/56(p=0.04)으로, 겹침을 빼도 이해 격차는 남는다.
- english 체크포인트에서 intent-20은 75/100행의 옵션이 잘리고 50행은 `iot_hue_light*` 옵션끼리 구분이 사라진다. upstream의 0.82도 같은 조건이다.

### E3 임베딩 정렬 (`embed_fn_from_agent`, n=100 쌍, chance P@1 0.01)

| 체크포인트 | P@1 ko→en / en→ko | P@5 ko→en / en→ko | 평균 cos 참 쌍 / 무작위 쌍 |
|---|---|---|---|
| multilingual | 0.19 / 0.31 | 0.43 / 0.45 | 0.737 / 0.642 (차이 0.7 sd) |
| english | 0.03 / 0.01 | 0.07 / 0.07 | 0.800 / 0.794 |

multilingual은 한국어와 영어를 부분적으로만 같은 공간에 놓고, english는 chance 수준이다. mmBERT는 문장 임베딩용으로 학습되지 않았으므로 정렬 지표일 뿐 검색 벤치마크가 아니다.

### E4 프로브 30행: 한국어 state vs 영어 번역 state (같은 7문항, questions_sha256 일치)

영어 번역은 이 프로젝트에서 작성한 참조 번역이다(`results/korean_support/probe_en.jsonl`).

| qid | KO / multilingual | EN / multilingual | EN / english |
|---|---|---|---|
| intent | 12/30 | 16/30 (p=0.29) | 14/30 (옵션 잘림) |
| is_urgent | 25/30, 양성 0/5, conf 0.957 | 26/30, 양성 1/5, conf 0.981 | 28/30, 양성 3/5 |
| refund_requested | 25/30, 양성 5/6, conf 0.905 | 25/30, 양성 3/6, conf 0.898 | 30/30, 양성 6/6 |
| churn_risk | 24/30, 양성 2/6, conf 0.947 | 25/30, 양성 3/6, conf 0.945 | 29/30, 양성 5/6 |
| needs_llm | 19/30, 양성 3/10, conf 0.887 | 18/30, 양성 4/10, conf 0.899 | 20/30, 양성 0/10 |
| binary 합계 (always-no 93/120) | 93 | 94 | 107 |
| noul 평균 AUROC | 0.76 | 0.74 | 0.91 |
| frustration 레벨 0 선택 (argmax / 반올림, 기대 18) | 0 / 0, MAE 1.084 | 2 / 0, MAE 1.207 | 10 / 0, MAE 0.975 |

- multilingual에서 noul 4개의 KO vs EN McNemar는 모두 p=1.000이다.
- v1b(criteria 포함)도 KO 87 / EN 85로 같은 양상이고, refund_requested가 양성 18 / 19로 true 쪽으로 무너지는 것도 같다. P0b의 "churn_risk + 한국어 criteria" 신호(28/30)는 영어 state에서 25/30으로 줄었다(p=0.375).
- 부정문 행 7, 11, 29의 intent 오류도 영어에서 그대로다.

**결론: noul 붕괴는 한국어 특유가 아니다.** 같은 영어 문장을 english 체크포인트는 107/120 맞히므로 질문 자체는 답할 수 있는 질문이다. multilingual은 is_urgent·refund·churn에서 언어와 상관없이 AUROC 0.80\~0.92로 state를 순위로는 읽지만, p(true)가 0.5 아래로 눌려 있다. 이것은 한국어 문장을 다듬어서 해결되는 문제가 아니라 결정 임계값과 체크포인트의 문제다.

**추가 확인(Track E6, n=500 NSMC noul, `results/E/E_summary_20261002.md`).** AUROC test 0.822, dev Youden 임계값 p(true) ≥ 0.0073(dev 중앙값 0.0099), test 정확도 0.725(0.5 기준 0.641, always-no 0.522). 순위는 정보가 있고 p(true)가 눌려 있다는 위 결론을 n=500에서 재확인한다. 다만 의미 key 2-choice(0.773)보다는 낮다.

**추가 확인(Track B, n=500 쌍, `results/B/summary_20261002.md`).** 한국어 설명 스키마(domain_8)에서 ko 0.526 vs en 0.510, McNemar p=0.47로 페널티가 없다. E1의 "한국어 서술형 설명이면 페널티 0.10(비유의)"을 n=500에서 더 강하게 확인한 셈이고, 영어 key 옵션(intent-20)의 +0.24는 그대로다.

## 6. 설계·운영 함의

03과 05에 반영한(또는 반영할) 결정이다. 번호는 00 §5 항목 8이 가리킨다.

1. **라우팅은 명시한다.** 한국어 채널 요청은 채널·로케일 메타데이터로 `predict(..., lang="ko")`(또는 `lang_guess`)를 고정하고, 메타데이터가 없을 때만 감지에 맡긴다. `default="multilingual"`만으로는 F1의 영어 에러 붙여넣기, F2, F3을 막지 못한다(§4).
2. **추론 전 NFC 정규화.** `unicodedata.normalize("NFC", text)`를 RedactHook 또는 별도 전처리 훅에서 수행한다. NFD 입력은 토큰이 3.09배로 늘어 예산과 품질을 동시에 해친다(§3).
3. **옵션 설명은 한국어 서술형.** key 렌더링 대비 scenario-18에서 +0.17(§5 E1). 어휘가 겹치는 옵션(play/music)은 분리해 다시 쓰거나 병합한다. P0c에서 play/music 병합 시 0.52 → 0.66이었다. 단, Track B의 8도메인 병합 세트는 n=500에서 0.526(test 0.492)에 그쳤고 설명 문구 변형으로는 개선되지 않았다(`results/C/C_schema_v2_20261002.md`). 한국어 페널티는 없어졌지만(0.526 vs 0.510) 과제 자체의 zero-shot 상한이 낮다.
4. **noul 결정 임계값은 0.5 고정이 아니다.** 질문별 임계값을 dev set의 ROC(또는 오류 예산)로 고른다. temperature 보정은 2-class softmax의 0.5 경계를 옮기지 못하므로(logit 차 0에서 p=0.5는 모든 T에서 같다) 이것은 보정이 아니라 임계값 문제다. AUROC 0.76\~0.92(§5 E4)는 임계값만 옮겨도 회복 여지가 있음을 뜻한다. 03 Track E에 E6으로, 05 §5·P3에 반영했고, E6 실측(NSMC: 0.641 → 0.725)으로 확인했다.
5. **score(frustration)는 보조 신호.** 레벨 0 회피는 언어 무관이며 `frustration >= 2.5` 규칙은 zero-shot에서 발화하지 않는다(P0b 점수 범위 0.91\~2.37). 자동 액션에 단독으로 쓰지 않는다.
6. **대안 경로 "MT → english 체크포인트".** 참조 번역 기준 상한은 intent +0.35, noul +14/120(§5 E4의 EN/english 열)이다. 실제 MT 비용·지연·오역을 포함해 P1 세트에서 측정할지는 결정 사항이다.
7. **영어 혼입 트래픽.** `lang="ko"`를 명시하면 영어 요청도 multilingual로 가므로, 영어 비중이 크면 D5(03 §6)의 reload 비용과 english 체크포인트 우위(E2에서 en 0.82 vs 0.71)를 함께 판단한다.

## 7. 03/05/02에 반영한 위치

| 결정 (§6) | 반영 문서와 위치 | 내용 |
|---|---|---|
| 1 라우팅 명시 | `05_poc_plan.md` §3 구성요소 표 Router 행, app.py 스케치 주석; `02_environment_setup.md` §2.8 env.sh 주석과 설명 문단; `01_laya_analysis.md` §3 Router 불릿, §9 H2 | 한국어 채널은 `lang="ko"` 고정, 감지는 메타데이터가 없을 때만. "한글은 항상 감지" 표현을 F1·F2 예외로 정정 |
| 2 NFC 정규화 | `05_poc_plan.md` §3 Router 행·app.py 주석, §9 리스크 표; `03_benchmark_plan.md` §13 리스크 표 | RedactHook 또는 서버 입구에서 `unicodedata.normalize("NFC")`. 평가셋은 소스가 NFD면 MANIFEST에 기록 |
| 3 한국어 서술형 설명 | `04_korean_evalset_spec.md` §3(P0c 반영분), `03_benchmark_plan.md` §7 B5 기대 범위 | 이미 P0c 결과로 반영됨. 본 감사의 E1이 같은 방향을 재확인 |
| 4 noul 결정 임계값 | `05_poc_plan.md` §5(`T_NOUL`, 정책 코드와 표), P3 단계; `03_benchmark_plan.md` Track E6 | 질문별 ROC 기준 임계값, 정책 레이어에서 적용 |
| 5 score 보조 신호 | `05_poc_plan.md` §5(P0b 반영분) | 변경 없음, E4가 언어 무관임을 추가 확인 |
| 6 MT → english 경로 | 본 문서 §6, 열린 질문 2 | 미반영. 채택 여부는 결정 사항 |
| 7 영어 혼입 트래픽 | `03_benchmark_plan.md` §6 D5 | 변경 없음, 판단 근거로 E2의 en 0.82 vs 0.71 추가 |
| 라우팅 견고성 측정 | `03_benchmark_plan.md` Track C10 | 46건 배터리를 `scripts/probe_routing.py`로 재실행, NFD 쌍 추가 |
| 진입점 | `00_README.md` §2 문서 맵, §5 항목 8 | 07 추가, 결정 항목으로 기재 |

## 열린 질문 / 가정

1. **표본 한계.** E1\~E3은 n=100(CI ±0.10), E4는 n=30(CI ±0.17)이다. 방향은 일관되지만 크기는 Track B(n=500)와 PoC P1 세트에서 다시 잰다.
2. **참조 번역.** E4의 영어 문장은 이 프로젝트에서 쓴 번역이라 실제 MT 출력과 다르다. "MT → english" 경로를 채택하려면 실제 MT로 재측정해야 한다.
3. **카드 수치 불일치.** multilingual 카드의 "Korean 0.110 → 0.490"은 run이 섞인 표기다. upstream에 이슈로 알릴지는 00 §5 항목 6(결과 공개 범위)과 함께 결정한다.
4. **한국어 학습 데이터 유무.** 문서에 없다는 것과 실제로 없다는 것은 다르다. 메인테이너에게 RLCD 학습 믹스의 언어 구성을 확인할지 결정한다.
5. **라우팅 임계값 변경 제안.** F1의 원인(음절을 1글자로 세는 규칙)은 upstream에 가중치 제안으로 낼 수 있으나, 우리 PoC는 `lang="ko"` 명시로 우회하므로 선택 사항이다.
6. **NFD 처리 위치.** 훅에서 할지 서버 입구에서 할지는 P2 구현 시 정한다. 어느 쪽이든 shadow 로그에는 정규화 후 텍스트만 남긴다.

[English](07_korean_support_audit.md) | **한국어**
