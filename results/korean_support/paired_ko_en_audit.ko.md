# K2 한국어 페널티 감사: 같은 내용의 ko vs en 대조 (paired)

> Korean PoC 결정용 통제 측정이다. 같은 MASSIVE id(ko 발화와 en 원문)와 같은 문항을 쓰고, 같은 체크포인트로 언어만 바꿔 정확도 차이를 잰다.
> **세트는 동결 평가셋이 아니다.** 04 §6 빌더가 아니라 throwaway 빌더(`K2_build.py`)로 만들었고 `data/evals/` 밖(`results/korean_support/`)에 있다. n=100(MASSIVE), n=30(프로브). 95% CI 폭은 n=100에서 약 ±0.10, n=30에서 약 ±0.17이다. 건수(x/100, x/30)로 읽는다.
> 실행 기록(run card)은 `results/korean_support/K2_20261002.md`에 있다. 모든 표는 `K2_analyze.py`가 리포트 JSON의 `cases[*]`에서 다시 계산한 `K2_analysis.md`를 옮긴 것이다(E3은 `K2_E3_embed_align.json`, 헤드 예산은 `K2_head_budget.md`).

## 0. 요약: 한국어 페널티 (multilingual 체크포인트, 같은 내용·같은 문항)

| 측정 | ko | en | en − ko (95% paired Wald CI) | McNemar exact p (b ko만 / c en만) | 판단 |
|---|---|---|---|---|---|
| E1 scenario-18, 한국어 서술형 설명 (P0c base 문항, PoC 스키마 형태) | 52/100 | 62/100 | +0.10 (−0.02..+0.22) | 0.143 (14 / 24) | n=100으로는 구분되지 않는다. 차이 10건이 전부 `play` 17행에서 나왔다(ko 1 vs en 11). 나머지 83행은 51 vs 51 (p=1.0) |
| E1 scenario-18, upstream key 렌더링 설명 (`iot: iot`) | 35/100 | 56/100 | +0.21 (+0.12..+0.30) | 4.9e-05 (3 / 24) | 유의. `play` 0 vs 10, 나머지 83행 35 vs 46 (p=0.013) |
| E2 intent-20, upstream 충실 구성 | 47/100 | 71/100 | +0.24 (+0.13..+0.35) | 1.2e-04 (7 / 31) | 유의. upstream 공개값 0.470 / 0.710과 정확히 같다 |
| E3 임베딩 정렬 P@1 (ko→en / en→ko, chance 0.01) | - | - | 0.19 / 0.31 (P@5 0.43 / 0.45) | - | 부분 정렬. english 체크포인트는 0.03 / 0.01로 chance 수준 |
| E4 프로브 noul 4문항 합계 (always-no 93) | 93/120 | 94/120 | +1 | 질문별 4개 모두 p=1.000 | noul 붕괴는 한국어 고유가 아니다. 같은 영어 문장을 english 체크포인트로 읽으면 107/120 |
| E4 frustration 레벨 0 선택 (argmax, 기대 18/30) | 0/30 | 2/30 | - | - | 레벨 0 회피(#131)도 언어와 무관한 체크포인트 특성이다 |

한 줄 결론: upstream 형식(영어 key 렌더링 옵션)에서 한국어 페널티는 0.21–0.24로 크고 유의하다. 한국어 서술형 설명을 쓰면 scenario-18의 페널티가 0.10(n.s.)으로 줄고, 남은 차이도 영어 발화가 key 단어(`play`)를 글자 그대로 포함하는 한 클래스에서 나온다. 반면 noul의 always-no 편향과 frustration 레벨 0 회피는 영어에서도 똑같이 나타난다. 이것은 한국어 문제가 아니라 multilingual 체크포인트의 성질이다.

## 1. 설계와 방법

### 1.1 데이터 (MASSIVE paired)

| 확인 항목 | 결과 | 근거 |
|---|---|---|
| 소스 | `mteb/amazon_massive_intent` config `ko`, `en`, split `test`, revision `940fd47a81eaa7f2cc7b129674d945d618ac38c2` (P0c에서 pin한 값. 리포 단위 revision이라 두 config에 공통이다) | K2_build_meta.json `massive.source` |
| 행 수 / 레이블 집합 | ko 2,974 / en 2,974, intent 59개, 두 집합 동일 | `massive.rows`, `massive.labels` |
| id 순서 | 전체 split에서 ko와 en의 id 순서가 같다. 따라서 en의 첫 100행이 곧 ko 첫 100행의 twin이다 | `same_id_order_full_split=true`, `en_first_100_are_the_ko_twins=true` |
| 쌍 구성 | ko test 첫 100행(P0c와 같은 행) + `id`로 join한 en 행. 100쌍 모두 `label_text`가 같다(빌더 assert) | `label_text_equal_all_100_pairs=true`, `row_ids` |
| 중복 | ko 첫 100행에 완전 중복 3쌍("청소기 작동 시켜줘", "내일 비가 올까", "화장실 불 꺼 줘"). en twin은 모두 서로 다른 문장("start a vacuum cleaner" / "turn on the vacuum cleaner" 등) | `exact_duplicate_*` |
| 병렬성의 한계 | MASSIVE ko는 직역이 아니라 현지화다. 개체가 바뀐 쌍이 있다(0부터 센 행 번호로 54 "임영웅 플레이리스트 재생" ↔ "play a nirvana playlist", 행 89 "싸이 노래 틀어" ↔ "open bad religion folder"). 레이블은 구성상 같지만 표면 내용은 "거의 병렬"이다 | E1 `play` 행 덤프(§2.3) |
| 학습 노출 | upstream은 "Neither checkpoint trained on typed-decisions, MASSIVE or XNLI"라고 적었다 | third_party/laya/research/results/t4_colab_benchmark.json `caveats.training_overlap` (`third_party/laya`는 공개 저장소에는 포함하지 않음. https://github.com/NandhaKishorM/laya 를 커밋 4aa6761로 clone해 재현) |

### 1.2 문항

| 실험 | 파일 (ko / en) | 문항 | questions_sha256 (ko·en 공통) |
|---|---|---|---|
| E1 kodesc | K2_scen18_kodesc_{ko,en}.jsonl | id `scenario`, instructions "Which domain does \`utterance\` belong to?", 18옵션 정렬 고정, 04 §5.1(c) 한국어 설명. `P0c_build.py` 상수를 import했다. ko 파일의 (state, questions, expected)는 P0c base 파일과 행 단위로 같다(빌더 assert) | 7bf1c9b1b314f6bdd03e49cbcd471106c2a7209c06407698e82bcdb182f30a44 (= P0c base) |
| E1 keydesc | K2_scen18_keydesc_{ko,en}.jsonl | 같은 instructions, 설명 = key 그대로(upstream build_benchmark_nb.py:316 렌더링). ko 파일은 P0c `_en-desc` 파일과 같다 | 233520130f429820bf54b950d333db61a991e637addf592f3925b18c0245e85e (= P0c en-desc) |
| E2 | K2_intent20_{ko,en}.jsonl | research/scripts/bench_local.py:165-183 포팅: test 전체에서 `labels = sorted(set(label_text))`, `random.Random(13)` 1회 생성, 첫 100행마다 gold + `rng.sample(pool, 19)` 후 `rng.shuffle`, criteria `k.replace("_", " ").replace(".", ": ")`, instructions "What is the user asking for in \`utterance\`?". en twin은 ko 행과 같은 key 목록을 쓴다 | 72baa7ba5b4d899bae87ce0b6cb67e9b6dce593e1ff5947e4957005554371e24 |
| E4 v1 | probe_en.jsonl | poc/schema/triage_v1.json + gateway_v1.json 병합 7문항 그대로(한국어 criteria 포함). state `{"message": <영어>}`, expected는 원본에서 복사, tags `["p0_probe_en"]`, language `en`, `#` 헤더에 throwaway 프로브 번역임을 적음 | 6b8bdadc8f9c718ed40f2510134caf52079a5dc0260e142d93d2132bee722c8a (= P0/P0b V0) |
| E4 v1b | K2_probe_en_v1b.jsonl | triage_v1b.json + gateway_v1b.json (noul 4개에 한국어 true/false criteria) | 8ea18279f62ef606f642930f91c81350e5c2c0a20713a6fb5fc3b60660100819 (= P0b V1) |

E2 구성 검증: 포팅 결과를 upstream 하네스 `third_party/laya/research/eval/laya_eval.py`의 `build_suite`(BENCHMARKS의 refreshed 수치를 만든 코드)와 ko·en 각각 옵션 단위로 비교해 같음을 assert했다. ko와 en은 id 순서와 레이블 집합이 같으므로, upstream이 언어마다 새로 만드는 `Random(13)`도 twin마다 같은 19개 distractor와 셔플을 뽑는다. 즉 이 en 파일은 upstream의 en 구성 그대로다.

지시문과 다른 점 1건: 지시문은 criteria 변환을 `.replace("."," : ")`로 적었지만 upstream 코드(bench_local.py:180, laya_eval.render_label)는 `.replace(".", ": ")`다. MASSIVE intent 레이블에는 `.`이 없어서 어느 쪽이든 결과가 `alarm set` 형태로 같다. 코드를 따랐다.

E4 번역: 30문장을 LLM으로 한 번에 번역했다. 의미·어조·부정 표현을 유지했다(행 7 "I'm not planning to cancel", 10 "I don't want to cancel", 11 "I don't need a refund", 29 "This isn't about cancelling"). 역번역과 2차 검수는 하지 않았다. 원문 앞부분과 번역의 짝은 빌더가 행마다 assert한다(`PROBE_EN`). "소비자원"은 "the consumer protection agency", "2만 원"은 "20,000 won"으로 옮겼다.

### 1.3 통계

- 정확도: x/n과 95% Wilson CI(`P0c_analyze.wilson`).
- 쌍 비교: exact two-sided McNemar(`P0c_analyze.mcnemar_exact`). b = A만 정답, c = B만 정답. Δ는 paired Wald 95% CI로 보조 표기했다(b+c가 작으면 부정확하다).
- macro-F1: gold에 등장한 클래스만(지시문의 "present classes") + 참고로 gold∪pred. upstream의 macro-F1은 옵션 위치 인덱스 기준이라(bench_local.py:126-133, 셔플된 위치가 클래스) 이 값과 비교하지 않는다.
- noul: `p >= 0.5` 정확도, 양성 수, 그리고 p(true)의 AUROC(Mann–Whitney, 동점 0.5)를 따로 본다. AUROC는 임계값과 상관없이 "state에 따라 p가 레이블 방향으로 움직이는가"를 본다. 기대 양성이 5–10건이라 AUROC의 불확실성도 크다(±0.2 수준).
- ECE와 mean_confidence는 리포트 `overall` 값이다(15 bins, answer_confidence 기준). analyzer는 `cases`에서 다시 계산한 정확도·mean_confidence가 `overall`과 같음을 assert한다.

### 1.4 실행

- 모델 실행은 모두 `laya-evals run --device cpu --batch-size 8 --slice qid`(CPU fp32), revision 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851이다. laya-evals 프로세스의 torch 스레드는 기본값(intra 10 = `OMP_NUM_THREADS`, inter-op 14)이고, 직접 쓴 E3 스크립트는 `torch.set_num_threads(10)`, `set_num_interop_threads(1)`이다.
- scenario-18은 행마다 문항이 같아서 8행씩 묶였다(13 chunks). intent-20은 행마다 옵션 집합이 달라 100행이 모두 단독 forward다(`timing.rows_alone=100`). upstream `laya_eval.py`는 100행을 한 번의 collated forward로 묶어(packed) 점수를 낸다.
- 같은 머신에서 다른 작업(tokenizer/routing 점검)이 동시에 돌았다. 지표는 정확도·보정뿐이다. 리포트의 latency 필드는 인용하지 않는다.

## 2. E1: MASSIVE scenario-18, ko vs en

Sanity 확인: ko 두 런은 P0c 런과 argmax 100/100, answer_confidence 최대 차이 0.0000으로 같다(같은 문항·행, CPU fp32 결정론).

### 2.1 정확도·보정 (n=100)

| 문항 | 발화 | 체크포인트 | 정답 (acc) | 95% Wilson CI | macro-F1 (gold 클래스 10개) | macro-F1 (gold∪pred) | mean answer_confidence | ECE | acc@50%cov |
|---|---|---|---|---|---|---|---|---|---|
| 한국어 설명 | ko | multilingual | 52/100 (0.52) | 0.42-0.62 | 0.550 | 0.367 | 0.747 | 0.250 | 0.76 |
| 한국어 설명 | en | multilingual | 62/100 (0.62) | 0.52-0.71 | 0.646 | 0.431 | 0.772 | 0.168 | 0.88 |
| 한국어 설명 | en | english (참고) | 50/100 (0.50) | 0.40-0.60 | 0.506 | 0.337 | 0.888 | 0.388 | 0.70 |
| key 렌더링 | ko | multilingual | 35/100 (0.35) | 0.26-0.45 | 0.357 | 0.255 | 0.816 | 0.466 | 0.50 |
| key 렌더링 | en | multilingual | 56/100 (0.56) | 0.46-0.65 | 0.576 | 0.412 | 0.856 | 0.311 | 0.92 |
| key 렌더링 | en | english (참고) | 65/100 (0.65) | 0.55-0.74 | 0.634 | 0.453 | 0.953 | 0.326 | 0.82 |

참고(P0c, 같은 문항·같은 행): english 체크포인트에 ko 발화 + 한국어 설명 = 31/100 (results/poc/P0c_20261002.md R1).

### 2.2 쌍 비교 (같은 100 id)

| 비교 | A | B | A 정답 | B 정답 | 둘 다 | b (A만) | c (B만) | Δ = B−A (95% CI) | McNemar p | argmax 일치 |
|---|---|---|---|---|---|---|---|---|---|---|
| 한국어 설명: ko vs en (ml) | ko/ml | en/ml | 52 | 62 | 38 | 14 | 24 | +0.10 (-0.02..+0.22) | 0.1433 | 50/100 |
| 한국어 설명: en, ml vs english | en/ml | en/english | 62 | 50 | 46 | 16 | 4 | -0.12 (-0.20..-0.04) | 0.0118 | 62/100 |
| key 렌더링: ko vs en (ml) | ko/ml | en/ml | 35 | 56 | 32 | 3 | 24 | +0.21 (+0.12..+0.30) | 4.9e-05 | 53/100 |
| key 렌더링: en, ml vs english | en/ml | en/english | 56 | 65 | 54 | 2 | 11 | +0.09 (+0.02..+0.16) | 0.0225 | 71/100 |
| ko: 한국어 설명 vs key 렌더링 (ml) | ko/kodesc | ko/keydesc | 52 | 35 | 32 | 20 | 3 | -0.17 (-0.26..-0.08) | 4.9e-04 | 58/100 |
| en: 한국어 설명 vs key 렌더링 (ml) | en/kodesc | en/keydesc | 62 | 56 | 51 | 11 | 5 | -0.06 (-0.14..+0.02) | 0.2101 | 68/100 |
| en: 한국어 설명 vs key 렌더링 (english) | en/kodesc | en/keydesc | 50 | 65 | 50 | 0 | 15 | +0.15 (+0.08..+0.22) | 6.1e-05 | 76/100 |

"en 우위가 문항에 따라 바뀌는가": 바뀐다. key 렌더링(영어 옵션)에서는 en − ko = +0.21(p<0.001), 한국어 설명에서는 +0.10(n.s.)이다. 한국어 설명은 ko를 +0.17(p<0.001) 올리고 en은 −0.06(n.s.) 내린다. 차이의 차이는 +0.11이지만 이 설계로는 검정하지 않았다(지시적). 설명 언어와 정보량이 함께 바뀌므로(P0c 주석과 같은 confound), 이것을 "언어 일치 효과"만으로 읽으면 안 된다.

english 참고 런은 "상한"으로 읽을 때 조건이 다르다. 한국어 설명 문항에서 english 체크포인트는 헤드 예산 192 때문에 옵션이 9토큰으로 잘린다(18/18 옵션, 100/100행. §6.3 헤드 예산 표). 그래서 en/english 0.50은 상한이 아니라 옵션을 못 읽는 조건의 값이다. key 렌더링 문항에서만 잘림이 없고, 이때 english가 multilingual보다 높다(0.65 vs 0.56, p=0.023).

### 2.3 어디서 차이가 나는가

gold 클래스별 정답 수 (multilingual ko | en | 참고 en/english):

| gold | n | 한국어 설명 ko | 한국어 설명 en | 한국어 설명 en/english | key 렌더링 ko | key 렌더링 en | key 렌더링 en/english |
|---|---|---|---|---|---|---|---|
| iot | 21 | 8 | 5 | 1 | 3 | 2 | 6 |
| play | 17 | 1 | 11 | 3 | 0 | 10 | 11 |
| weather | 13 | 10 | 13 | 13 | 10 | 13 | 13 |
| datetime | 9 | 6 | 7 | 8 | 5 | 7 | 9 |
| news | 9 | 6 | 6 | 7 | 6 | 7 | 8 |
| alarm | 7 | 6 | 7 | 7 | 5 | 7 | 7 |
| audio | 7 | 1 | 4 | 5 | 0 | 2 | 5 |
| general | 7 | 5 | 2 | 0 | 0 | 1 | 0 |
| takeaway | 6 | 5 | 3 | 3 | 2 | 3 | 3 |
| music | 4 | 4 | 4 | 3 | 4 | 4 | 3 |

사후(post-hoc) 분해, multilingual:

| 문항 | 부분집합 | n | ko 정답 | en 정답 | b (ko만) | c (en만) | McNemar p |
|---|---|---|---|---|---|---|---|
| 한국어 설명 | gold = play | 17 | 1 | 11 | 1 | 11 | 0.0063 |
| 한국어 설명 | gold ≠ play | 83 | 51 | 51 | 13 | 13 | 1.0000 |
| key 렌더링 | gold = play | 17 | 0 | 10 | 0 | 10 | 0.0020 |
| key 렌더링 | gold ≠ play | 83 | 35 | 46 | 3 | 14 | 0.0127 |

`play` 행의 en 정답 11건은 모두 발화에 "play"라는 단어가 그대로 들어 있다("play my rock playlist", "play a nirvana playlist" 등). en `play` 17행 중 14행에 그 단어가 있고, 단어가 없는 행에서는 하나도 맞히지 못했다. 같은 행의 ko 발화("내 락 플레이리스트 재생", "이승환 노래 무엇이든 재생해줘")는 music 설명("음악 취향, 재생 설정")과 play 설명("음악, 라디오, … 재생")이 공유하는 '재생/음악'에 걸려 14건이 music으로 갔다(answer_confidence 0.43–1.00, 14건 중 12건이 0.74 이상). 그러니 한국어 설명 문항의 페널티는 "영어 발화가 옵션 key와 글자로 겹친다"는 한 클래스의 lexical anchoring 효과이고, 그 밖의 83행에서는 ko와 en이 같다(51 vs 51, 서로 다른 13건씩). 이 분해는 결과를 본 뒤에 고른 것이라 확인용이 아니다.

## 3. E2: MASSIVE intent-20 (upstream 충실), ko vs en + Track A 재현

### 3.1 정확도·보정 (n=100, 20옵션, random 0.05)

| 발화 | 체크포인트 | 정답 (acc) | 95% Wilson CI | macro-F1 (gold 클래스) | macro-F1 (gold∪pred) | mean answer_confidence | ECE | acc@50%cov |
|---|---|---|---|---|---|---|---|---|
| ko | multilingual | 47/100 (0.47) | 0.38-0.57 | 0.374 | 0.304 | 0.777 | 0.311 | 0.68 |
| en | multilingual | 71/100 (0.71) | 0.61-0.79 | 0.658 | 0.503 | 0.888 | 0.233 | 0.92 |
| en | english (참고) | 82/100 (0.82) | 0.73-0.88 | 0.752 | 0.674 | 0.958 | 0.138 | 0.98 |
| ko | english (참고) | 11/100 (0.11) | 0.06-0.19 | 0.068 | 0.041 | 0.790 | 0.680 | 0.14 |

### 3.2 쌍 비교

| 비교 | A | B | A 정답 | B 정답 | 둘 다 | b (A만) | c (B만) | Δ = B−A (95% CI) | McNemar p | argmax 일치 |
|---|---|---|---|---|---|---|---|---|---|---|
| ko vs en (multilingual) | ko/ml | en/ml | 47 | 71 | 40 | 7 | 31 | +0.24 (+0.13..+0.35) | 1.2e-04 | 47/100 |
| en: multilingual vs english | en/ml | en/english | 71 | 82 | 65 | 6 | 17 | +0.11 (+0.02..+0.20) | 0.0347 | 69/100 |
| ko: english vs multilingual | ko/english | ko/ml | 11 | 47 | 2 | 9 | 45 | +0.36 (+0.23..+0.49) | 7.3e-07 | 11/100 |

### 3.3 upstream 대비 (Track A 재현 점검, laya-evals 경로)

upstream 정확도·ECE는 BENCHMARKS.md:71(ko), :117(en)이다. mean_confidence와 acc@50%cov는 research/results/cpu_51_language_sweep_refreshed.json의 `refreshed_clamped`(laya 0.3.20, x86 CPU, `research/eval/laya_eval.py`)에서 가져왔다.

| 발화 | 체크포인트 | 측정 acc | upstream acc | Δ | ±0.03 이내 | 측정 ECE / upstream | 측정 mean conf / upstream | 측정 acc@50%cov / upstream |
|---|---|---|---|---|---|---|---|---|
| ko | multilingual | 0.470 | 0.470 | +0.000 | 예 | 0.3108 / 0.3108 | 0.7773 / 0.7773 | 0.68 / 0.68 |
| en | multilingual | 0.710 | 0.710 | +0.000 | 예 | 0.2333 / 0.2333 | 0.8876 / 0.8876 | 0.92 / 0.92 |
| en | english | 0.820 | 0.820 | +0.000 | 예 | 0.1383 / 0.1382 | 0.9583 / 0.9582 | 0.98 / 0.98 |
| ko | english | 0.110 | 0.110 | +0.000 | 예 | 0.6804 / 0.6804 | 0.7904 / 0.7904 | 0.14 / 0.14 |

- 4칸 모두 정확도가 정확히 같고, ECE·mean confidence는 소수 넷째 자리까지 같다(english/en의 0.0001 차이는 laya-evals가 리포트에 확률을 4자리로 반올림해 넣는 것과 일치하는 크기다. 원인은 확인하지 않았다). H1(01_laya_analysis.md:262, multilingual 0.470 ± 0.03, english 0.110 ± 0.03)이 이 경로로 성립한다.
- 점수 방식은 다르다. laya-evals는 `Router.predict`로 행마다 단독 forward를 했고(rows_alone 100), upstream은 100행을 패딩해 한 번에 packed forward로 logits를 뽑았다. 이 집계 해상도에서는 그 차이가 드러나지 않았다. 행 단위 logit 비교는 upstream이 case 출력을 커밋하지 않아 하지 못했다.
- english 체크포인트의 confidence는 laya의 temperature clamp(`choice:11+` 0.1006 → 0.5)를 거친 "as served" 값이다. upstream `refreshed_clamped`와 같은 조건이라 비교가 성립한다(BENCHMARKS.md:13-25).
- upstream 300행 참고값(T4, 행마다 옵션 셔플. third_party/laya/research/results/t4_colab_benchmark.json `suites.massive_intent.*`, laya 버전 미기록): multilingual ko 0.490 / en 0.657 (en − ko +0.167). scenario는 ko 0.423 / en 0.560 (+0.137). 우리 n=100의 Δ CI(intent +0.13..+0.35, scenario key 렌더링 +0.12..+0.30) 안에 있다. 첫 100행을 공유하므로 독립 재현은 아니다.

### 3.4 어디서 차이가 나는가

| scenario 계열 (gold intent 접두어) | n | ko 정답 | en 정답 | en − ko |
|---|---|---|---|---|
| iot | 21 | 8 | 11 | +3 |
| play | 17 | 10 | 13 | +3 |
| weather | 13 | 9 | 13 | +4 |
| datetime | 9 | 2 | 7 | +5 |
| news | 9 | 6 | 5 | -1 |
| alarm | 7 | 4 | 7 | +3 |
| audio | 7 | 4 | 5 | +1 |
| general | 7 | 3 | 6 | +3 |
| takeaway | 6 | 1 | 3 | +2 |
| music | 4 | 0 | 1 | +1 |

사후 분해: en 발화에 gold intent key의 단어(3자 이상, 예: `alarm_set`의 "alarm"/"set")가 부분 문자열로 들어 있는지로 나눴다.

| 부분집합 | n | ko 정답 | en 정답 | b (ko만) | c (en만) | McNemar p |
|---|---|---|---|---|---|---|
| en 발화에 gold key 단어가 있음 | 44 | 27 | 41 | 2 | 16 | 0.0013 |
| en 발화에 gold key 단어가 없음 | 56 | 20 | 30 | 5 | 15 | 0.0414 |

intent-20의 페널티는 scenario와 달리 한 클래스에 몰려 있지 않고 계열 전반에 퍼져 있다(10개 계열 중 9개에서 en ≥ ko). key 단어가 겹치는 행에서 격차가 더 크고(+14/44), 겹치지 않는 행에도 남는다(+10/56). 거친 사후 지표지만, 영어 옵션 텍스트에 기대는 lexical anchoring과 그 밖의 이해 격차가 함께 있다는 쪽을 가리킨다. 정답일 때와 오답일 때의 평균 answer_confidence는 ko/ml 0.912 / 0.658, en/ml 0.925 / 0.796이다.

## 4. E3: 교차언어 임베딩 정렬 (지표용이며 retrieval 벤치마크가 아니다)

방법: `laya.embed_fn_from_agent(agent)`(기본값 max_length 512, batch 32, 패딩을 뺀 mean pool. upstream이 shortlist에 쓰는 함수)로 ko 100문장과 en twin 100문장을 임베딩했다. L2 정규화한 뒤 코사인 행렬 S(ko × en)를 만들었고, 질의마다 상대 언어 100개를 정렬해 twin의 순위를 봤다. 동점은 낮은 인덱스가 앞선다. dup-aware는 ko 중복 3쌍(6개 질의)에서 같은 ko 문장의 다른 twin도 정답으로 센다. **mmBERT는 문장 임베딩용으로 학습된 모델이 아니다.** multilingual의 encoder는 mmBERT-base 계열(ModernBERT 구조, hidden 768, 22층, vocab 256,000)이고 english는 ModernBERT-large 계열(hidden 1024, 28층, vocab 50,368)이다(각 `encoder/config.json`). 둘 다 MLM encoder 위에 결정 헤드를 학습한 것이고, 문장 임베딩용 대조 학습은 거치지 않았다. upstream도 이 함수의 독스트링에서 전용 bi-encoder가 보통 더 낫다고 적었다(laya/shortlist.py:129-131). 그래서 이 값은 두 언어 표현이 얼마나 가까운지를 보는 지표일 뿐, retrieval 성능 주장이 아니다.

| 체크포인트 | ko→en P@1 (strict / dup-aware) | ko→en P@5 | en→ko P@1 (strict / dup-aware) | en→ko P@5 | twin 중앙 순위 ko→en / en→ko | 평균 cos, 참 쌍 | 평균 cos, 무작위 쌍 (sd) | 차이 (무작위 sd 단위) | 언어 내 off-diagonal 평균 cos ko / en | 발화당 토큰 ko / en |
|---|---|---|---|---|---|---|---|---|---|---|
| multilingual | 0.19 / 0.19 | 0.43 | 0.31 / 0.32 | 0.45 | 9 / 8 | 0.737 | 0.642 (0.135) | +0.095 (0.7) | 0.705 / 0.635 | 8.7 / 6.0 |
| english | 0.03 / 0.03 | 0.07 | 0.01 / 0.01 | 0.07 | 46 / 46 | 0.800 | 0.794 (0.072) | +0.005 (0.1) | 0.936 / 0.802 | 20.4 / 6.0 |

- multilingual: P@1이 chance(0.01)의 19–31배이고 twin 중앙 순위는 100개 중 8–9위다. 참 쌍이 행과 열 모두에서 최댓값인 경우는 15/100이다. 두 언어 공간이 부분적으로만 정렬되어 있다. 참 쌍과 무작위 쌍의 cos 차이는 무작위 쌍 분포 sd의 0.7배에 그친다. ko→en(0.19)이 en→ko(0.31)보다 낮다. 한국어 임베딩끼리의 평균 cos가 더 높아서(0.705 vs 0.635) ko 공간이 더 뭉쳐 있는 것과 맞물린다(관찰만 했고 원인은 검증하지 않았다).
- english: chance 수준이다(P@1 0.03 / 0.01, 차이 +0.005). 한국어 발화는 바이트 수준으로 쪼개져 발화당 20.4토큰이 되고(multilingual 8.7), 한국어끼리의 평균 cos가 0.936이다. 한국어 문장들이 거의 한 점으로 모인다.
- 이 정렬 약함은 E1/E2의 한국어 페널티와 방향이 같지만, 정확도 차이의 원인이라는 증거는 아니다(상관만 있고 개입 실험은 없다).

## 5. E4: noul 붕괴는 한국어 고유인가 (P0 프로브 30행, 한국어 vs 영어 state)

비교 대상은 다음과 같다. 한국어 쪽은 기존 리포트(results/poc/P0b_V0_v1_multilingual.json, P0b_V0_v1_english.json, P0b_V1_criteria_multilingual.json), 영어 쪽은 이번 런이다. 문항 바이트가 같다(questions_sha256 일치. analyzer assert). noul 4개는 criteria 없이 영어 instructions뿐이라 질문 쪽이 완전히 영어이고, 바뀌는 것은 state 언어 하나다. intent·complexity·frustration은 한국어 criteria를 그대로 두었으므로, 영어 state 쪽은 영어 state와 한국어 옵션이 섞인 조건이다.

### 5.1 질문별 (v1 스키마)

셀 표기: choice/noul `정답/30`. noul은 `예측 양성 수 / 기대 양성 수`, p(true)의 AUROC(0.5 = 순위 정보 없음), p(true) 최소–최대를 덧붙였다. frustration은 MAE, 정확 레벨(argmax), 레벨 0 선택 argmax / round(score)(기대 18/30), score 범위다.

| qid | 기저 | KO / multilingual (P0b V0) | EN / multilingual | KO / english (P0b V0) | EN / english |
|---|---|---|---|---|---|
| intent | 최빈 5/30 | 12/30 | 16/30 | 7/30 | 14/30 |
| is_urgent | always-no 25/30 | 25/30, 양성 0 / 5, AUROC 0.86, p 0.00–0.46 | 26/30, 양성 1 / 5, AUROC 0.85, p 0.00–0.94 | 26/30, 양성 3 / 5, AUROC 0.81, p 0.03–0.69 | 28/30, 양성 3 / 5, AUROC 1.00, p 0.00–0.83 |
| refund_requested | always-no 24/30 | 25/30, 양성 5 / 6, AUROC 0.91, p 0.00–0.89 | 25/30, 양성 3 / 6, AUROC 0.90, p 0.00–0.96 | 22/30, 양성 2 / 6, AUROC 0.61, p 0.00–0.91 | 30/30, 양성 6 / 6, AUROC 1.00, p 0.00–0.96 |
| churn_risk | always-no 24/30 | 24/30, 양성 2 / 6, AUROC 0.92, p 0.00–0.86 | 25/30, 양성 3 / 6, AUROC 0.80, p 0.00–0.98 | 22/30, 양성 6 / 6, AUROC 0.68, p 0.01–0.91 | 29/30, 양성 5 / 6, AUROC 0.99, p 0.00–0.91 |
| needs_llm | always-no 20/30 | 19/30, 양성 3 / 10, AUROC 0.37, p 0.00–0.96 | 18/30, 양성 4 / 10, AUROC 0.41, p 0.00–0.98 | 15/30, 양성 17 / 10, AUROC 0.65, p 0.02–1.00 | 20/30, 양성 0 / 10, AUROC 0.65, p 0.00–0.43 |
| frustration | always-0 MAE 0.700 | MAE 1.084, 정확 5/30, L0 0 / 0, score 1.01–2.37 | MAE 1.207, 정확 7/30, L0 2 / 0, score 0.66–2.39 | MAE 0.880, 정확 16/30, L0 26 / 4, score 0.31–1.57 | MAE 0.975, 정확 14/30, L0 10 / 0, score 0.70–1.74 |
| complexity | 최빈 12/30 | 13/30 | 11/30 | 13/30 | 11/30 |
| binary 합계 /120 | always-no 93 | 93 | 94 | 85 | 107 |
| noul 평균 AUROC | 0.50 | 0.76 | 0.74 | 0.69 | 0.91 |

평균 answer_confidence:

| qid | KO/ml | EN/ml | KO/english | EN/english |
|---|---|---|---|---|
| intent | 0.825 | 0.780 | 0.338 | 0.606 |
| is_urgent | 0.957 | 0.981 | 0.851 | 0.891 |
| frustration | 0.461 | 0.457 | 0.561 | 0.442 |
| refund_requested | 0.905 | 0.898 | 0.930 | 0.865 |
| churn_risk | 0.947 | 0.945 | 0.845 | 0.842 |
| needs_llm | 0.887 | 0.899 | 0.867 | 0.947 |
| complexity | 0.681 | 0.682 | 0.407 | 0.479 |

### 5.2 쌍 비교 (exact McNemar, n=30, frustration은 정확 레벨 argmax)

| 체크포인트 | qid | KO 정답 | EN 정답 | b (KO만) | c (EN만) | p |
|---|---|---|---|---|---|---|
| multilingual | intent | 12 | 16 | 2 | 6 | 0.289 |
| multilingual | is_urgent | 25 | 26 | 0 | 1 | 1.000 |
| multilingual | frustration | 5 | 7 | 1 | 3 | 0.625 |
| multilingual | refund_requested | 25 | 25 | 1 | 1 | 1.000 |
| multilingual | churn_risk | 24 | 25 | 1 | 2 | 1.000 |
| multilingual | needs_llm | 19 | 18 | 2 | 1 | 1.000 |
| multilingual | complexity | 13 | 11 | 5 | 3 | 0.727 |
| english | intent | 7 | 14 | 4 | 11 | 0.118 |
| english | is_urgent | 26 | 28 | 1 | 3 | 0.625 |
| english | frustration | 16 | 14 | 8 | 6 | 0.791 |
| english | refund_requested | 22 | 30 | 0 | 8 | 0.008 |
| english | churn_risk | 22 | 29 | 1 | 8 | 0.039 |
| english | needs_llm | 15 | 20 | 6 | 11 | 0.332 |
| english | complexity | 13 | 11 | 6 | 4 | 0.754 |

### 5.3 criteria(v1b) 포함, multilingual

| qid | 기대 양성 | KO/ml v1 | EN/ml v1 | KO/ml v1b (P0b V1) | EN/ml v1b |
|---|---|---|---|---|---|
| is_urgent | 5 | 25/30, 양성 0 (TP 0, FP 0), AUROC 0.86 | 26/30, 양성 1 (TP 1, FP 0), AUROC 0.85 | 26/30, 양성 1 (TP 1, FP 0), AUROC 0.78 | 26/30, 양성 3 (TP 2, FP 1), AUROC 0.82 |
| refund_requested | 6 | 25/30, 양성 5 (TP 3, FP 2), AUROC 0.91 | 25/30, 양성 3 (TP 2, FP 1), AUROC 0.90 | 18/30, 양성 18 (TP 6, FP 12), AUROC 0.90 | 17/30, 양성 19 (TP 6, FP 13), AUROC 0.88 |
| churn_risk | 6 | 24/30, 양성 2 (TP 1, FP 1), AUROC 0.92 | 25/30, 양성 3 (TP 2, FP 1), AUROC 0.80 | 28/30, 양성 8 (TP 6, FP 2), AUROC 0.96 | 25/30, 양성 9 (TP 5, FP 4), AUROC 0.78 |
| needs_llm | 10 | 19/30, 양성 3 (TP 1, FP 2), AUROC 0.37 | 18/30, 양성 4 (TP 1, FP 3), AUROC 0.41 | 15/30, 양성 15 (TP 5, FP 10), AUROC 0.51 | 17/30, 양성 11 (TP 4, FP 7), AUROC 0.50 |
| binary 합계 /120 (always-no 93) | | 93 | 94 | 87 | 85 |
| noul 평균 AUROC | | 0.76 | 0.74 | 0.79 | 0.74 |

v1b의 KO vs EN McNemar(질문별): is_urgent p=1.000, refund_requested 1.000, churn_risk 0.375 (KO 28 vs EN 25), needs_llm 0.754. criteria(한국어)를 붙였을 때 refund_requested가 true 쪽으로 붕괴하는 현상(양성 18 → 19)과 needs_llm의 FP 증가는 영어 state에서도 똑같다. P0b에서 always-no를 뚜렷이 넘은 유일한 binary였던 "churn_risk + 한국어 criteria"(KO 28/30, 기저 +4)는 영어 state에서 25/30(기저 +1, TP 5 / FP 4)으로 줄었다(McNemar p=0.375). 이 신호는 n=30에서 안정적이라고 볼 수 없다.

### 5.4 부정문 행 (P0 행 4, 7, 10, 11, 29)

| 행 | 부정된 대상 | 기대 intent | KO/ml p / intent | EN/ml p / intent | EN/english p / intent | KO/ml v1b p | EN/ml v1b p |
|---|---|---|---|---|---|---|---|
| 4 | churn_risk | refund | 0.13 / billing_question | 0.01 / refund | 0.26 / refund | 0.66 | 0.13 |
| 7 | churn_risk | technical_help | 0.03 / cancellation | 0.01 / cancellation | 0.31 / cancellation | 0.22 | 0.22 |
| 10 | churn_risk | billing_question | 0.01 / billing_question | 0.02 / cancellation | 0.49 / cancellation | 0.35 | 0.34 |
| 11 | refund_requested | billing_question | 0.65 / refund | 0.84 / refund | 0.24 / billing_question | 0.87 | 0.76 |
| 29 | churn_risk | other | 0.00 / cancellation | 0.01 / cancellation | 0.21 / cancellation | 0.03 | 0.23 |

부정된 대상 쪽으로 가는 intent 오류(행 7, 11, 29)는 영어 state에서도 그대로다(EN/ml 행 7 cancellation, 11 refund + refund_requested 0.84, 29 cancellation). 행 10은 영어에서 오히려 새로 cancellation으로 갔다. H7(부정문 실패)도 이 5행에서는 한국어 고유가 아니다(5행뿐이라 지시적). english 체크포인트의 intent는 한국어 criteria가 잘리고 읽히지 않는 조건이라(§6.3) 여기서는 해석하지 않는다.

### 5.5 답: noul 붕괴는 한국어 고유인가

아니다(n=30, 지시적).
1. 같은 체크포인트(multilingual)에서 영어 state를 줘도 noul 합계가 93 → 94/120이고, 질문별 McNemar는 4개 모두 p=1.000이다. 양성 예측 수는 is_urgent 0 → 1, refund 5 → 3, churn 2 → 3, needs_llm 3 → 4(기대 5/6/6/10)로, 영어에서도 no 쪽에 몰린다.
2. 같은 영어 문장을 english 체크포인트에 주면 107/120(refund 30/30, churn 29/30, is_urgent 28/30)이고 AUROC 평균은 0.91이다. 즉 이 프로브의 noul 질문은 답할 수 있는 질문이고, no 편향은 multilingual 체크포인트의 성질이다.
3. 순위 정보는 multilingual에서도 언어와 상관없이 있다. is_urgent·refund·churn의 AUROC가 KO 0.86/0.91/0.92, EN 0.85/0.90/0.80이다. p(true)가 0.5를 거의 넘지 않을 뿐이다(KO is_urgent의 최댓값 0.46). "state를 읽지 못한다"기보다는 "읽지만 임계값 0.5 아래로 눌려 있다"에 가깝다. 예외는 needs_llm으로, 두 언어 모두 AUROC 0.37–0.41이라 순위도 반대다(질문 정의 자체가 모호하다는 P0 주석과 일치). 기대 양성이 5–10건이라 AUROC의 CI는 ±0.2 정도다.
4. frustration 레벨 0 회피도 언어와 무관하다: L0 argmax 0/30 → 2/30, MAE 1.084 → 1.207(영어가 더 나쁨).

## 6. 핵심 관찰, 한계, 다음 단계

### 6.1 관찰

1. 한국어 페널티는 실재하지만 크기는 옵션 텍스트의 언어에 달려 있다. upstream 형식(영어 key 렌더링)에서는 en − ko = +0.21(scenario), +0.24(intent)이고 둘 다 p ≤ 1.2e-04다. PoC 형식(한국어 서술형 설명)에서는 scenario가 +0.10(p=0.14)이고, 그 차이가 전부 `play` 한 클래스에서 나온다. 거기서 영어 발화는 key 단어 "play"를 글자 그대로 담고 있고, 그 밖의 83행에서는 ko와 en이 같다. intent-20에서도 key 단어가 겹치는 행에서 격차가 더 크다. 영어 옵션에 대한 lexical anchoring이 페널티의 큰 몫이고, 한국어 설명이 그 일부를 메운다. 이해 격차는 남는다(key 단어가 없는 행에서도 20/56 vs 30/56, p=0.04).
2. Track A 재현이 laya-evals 경로로 정확히 성립한다. ko/en × multilingual/english 4칸이 Δ 0.000이고, ECE·mean confidence 차이는 0.0001 이내다. 행 단독 forward와 upstream의 packed forward 차이는 이 해상도에서 보이지 않는다. 우리 하네스로 잰 한국어 수치를 upstream 수치와 같은 눈금에서 비교할 수 있다.
3. noul의 no 편향, 부정문 오류(5행), frustration 레벨 0 회피는 multilingual 체크포인트의 성질이고 한국어 고유가 아니다. 같은 영어 내용에서도 그대로였고, english 체크포인트는 같은 영어 문장의 noul을 107/120으로 맞혔다. 한국어 PoC에서 이 약점은 "한국어를 더 잘 쓰는 법"으로는 풀리지 않는다. 임계값·보정(Track E)이나 체크포인트·경로 선택의 문제다.

### 6.2 한계

- n=100과 n=30이다. n=100에서 Δ 0.10은 CI가 0을 포함한다. 프로브는 1인 ad-hoc 라벨에 1인 번역이다.
- 사후 분해(§2.3 `play`, §3.4 key 단어 지표)는 결과를 본 뒤에 고른 것이라 가설 생성용이다.
- E1/E2 비교는 "같은 내용"이라고 해도 MASSIVE 현지화로 개체·표현이 다른 쌍이 있다(§1.1).
- 옵션 순서 고정 한 가지만 봤다. upstream은 multilingual MASSIVE intent en의 옵션 순서 flip rate를 0.23으로 보고했다(t4_colab_benchmark.json `option_order_robustness`). 순서를 바꿨을 때 ko/en 격차가 유지되는지는 측정하지 않았다(Track C1).
- english 체크포인트 참고 런: 한국어 설명 문항(scenario 100/100행)과 프로브 intent(30/30행)에서 옵션이 잘린다. intent-20에서도 75/100행이 잘리고, 50/100행은 `iot_hue_light*` 옵션끼리 구분이 사라진다(10행은 gold 포함). upstream의 english 0.82도 같은 조건이다.

### 6.3 헤드 예산 (tokenizer만, `K2_head_budget.md`)

| 파일 (ko/en twin 공통 문항) | 체크포인트 (head_max_len) | qid | 옵션 수 | 옵션당 cap | 잘린 행 | 구분 불가 행 |
|---|---|---|---|---|---|---|
| K2_scen18_kodesc | multilingual (256) | scenario | 18 | 없음 | 0 | 0 |
| K2_scen18_keydesc | multilingual (256) | scenario | 18 | 없음 | 0 | 0 |
| K2_intent20 | multilingual (256) | intent | 20 | 없음 | 0 | 0 |
| probe_en (7문항) | multilingual (256) | 전부 | 2–6 | 없음 | 0 | 0 |
| K2_scen18_kodesc | english (192) | scenario | 18 | 9 | 100 (18옵션 모두) | 0 |
| K2_scen18_keydesc | english (192) | scenario | 18 | 없음 | 0 | 0 |
| K2_intent20 | english (192) | intent | 20 | 8 (일부 행 없음) | 75 | 50 |
| probe_en | english (192) | intent | 6 | 29 | 30 | 0 |
| probe_en | english (192) | noul 4개·frustration·complexity | 2–4 | 없음 | 0 | 0 |

multilingual은 이번 모든 문항을 잘림 없이 읽었다. 그러므로 multilingual의 ko vs en 비교는 헤드 조건이 같다(헤드는 state와 무관하고, ko와 en의 문항 바이트가 같다).

### 6.4 다음 단계 제안 (결정은 프로젝트 책임자)

- 스키마: 04:76의 "한국어 서술형 설명 기본"을 유지할 근거가 하나 더 생겼다(ko +0.17, p<0.001. en은 −0.06 n.s.). 단, 설명끼리 어휘를 공유하는 옵션(play/music의 '재생')은 한국어에서 특히 깨지므로 도메인 정의 단계에서 겹침을 없앤다(P0c 권고와 같다).
- Track E: multilingual noul은 AUROC 0.8–0.9인데 0.5 임계값에서 붕괴한다. 질문별 임계값이나 noul:2 temperature refit을 P1 라벨셋(N ≥ 200)으로 맞춰 본다. 30행 프로브로는 맞추지 않는다.
- 경로 대안(가설): 이 데이터에서 en/english가 ko/ml보다 intent-20 +0.35, scenario key 렌더링 +0.30, 프로브 noul +14/120 높았다. 영어는 MASSIVE의 원문이고 프로브 영어는 사람 수준 번역이므로, 이 값은 "ko→en 번역 + english 체크포인트(영어 criteria)" 경로의 상한일 뿐이다. 실제 MT 품질과 레이턴시를 넣은 비교를 P1 세트에서 따로 측정할 가치가 있다.
- Track A: intent-20 ko/en 재현을 통과로 기록할 수 있다(throwaway 파일 기준. 정식 기록은 04 빌더 산출물로 다시 한 번).
- Track C1: 옵션 순열에서 ko/en 격차와 `iot→alarm` 첫 위치 편향(en에서도 7–9건)을 확인한다.

## 7. 명령어 (cwd = 프로젝트 루트, 모두 `source env.sh` 후 실행)

| 단계 | 명령어 (`.venv/`는 공개 저장소에는 포함하지 않음) |
|---|---|
| 빌드 | `.venv/bin/python results/korean_support/K2_build.py > results/korean_support/K2_build.log 2>&1` |
| 검증 | `.venv/bin/laya-evals validate results/korean_support/<file>.jsonl` × 8 → results/korean_support/K2_validate.log (모두 exit 0) |
| 모델 실행 13회 | `bash results/korean_support/K2_run.sh`. 각 줄은 `.venv/bin/laya-evals run <jsonl> --model <multilingual\|english> --device cpu --batch-size 8 --slice qid --json results/korean_support/<id>.json --markdown results/korean_support/<id>.md > results/korean_support/<id>.log 2>&1` |
| E3 | `.venv/bin/python results/korean_support/K2_embed_align.py > results/korean_support/K2_E3_embed_align.log 2>&1` |
| 헤드 예산 | `.venv/bin/python results/korean_support/K2_head_budget.py > results/korean_support/K2_head_budget.md` |
| 분석 | `.venv/bin/python results/korean_support/K2_analyze.py` → results/korean_support/K2_analysis.md |

## 8. 산출물 (모두 results/korean_support/)

- 빌더·실행·분석 스크립트: K2_build.py, K2_run.sh, K2_embed_align.py, K2_head_budget.py, K2_analyze.py
- JSONL: K2_scen18_{kodesc,keydesc}_{ko,en}.jsonl, K2_intent20_{ko,en}.jsonl, probe_en.jsonl, K2_probe_en_v1b.jsonl, 그리고 K2_build_meta.json(sha256, questions_sha256, row_ids, 쌍 검증 결과)
- 리포트(.json/.md/.log): K2_scen18-{kodesc,keydesc}_ko_multilingual, K2_scen18-{kodesc,keydesc}_en_{multilingual,english}, K2_intent20_{ko,en}_{multilingual,english}, K2_probe-en-v1_{multilingual,english}, K2_probe-en-v1b_multilingual
- 로그·분석: K2_build.log, K2_validate.log, K2_run_times.log, K2_times.log, K2_E3_embed_align.{json,log}, K2_head_budget.md, K2_analysis.md
- run card: K2_20261002.md
- 같은 디렉터리의 `cards/`, `fetch_cards.sh`, `part2_*`는 다른 작업의 산출물이다(건드리지 않음).

[English](paired_ko_en_audit.md) | **한국어**
