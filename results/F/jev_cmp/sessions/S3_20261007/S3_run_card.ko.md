# Run 20261007-1336_jev-playground_S3 (T4_banking77_10opt_40 + T5_boolq_40)

| 항목 | 값 |
|---|---|
| run_id | 20261007-1336_jev-playground_S3 (Track F, Laya vs Jev 비교 세션 S3: T4 Banking77-10 key-only 40 + T5 BoolQ 40) |
| 날짜 / 시작 시각 | 2026-10-07 (KST). 자료 읽기 약 13:27(시작 시각 미기록, 추정), 스크립트 생성 13:34\~13:35, 페이지 로드 13:35:43, 첫 평가 클릭 13:36:13.671, Part A 마지막 13:46:24.494, Part B 첫 클릭 13:46:47.317, 마지막 평가 클릭 13:56:39.010, 브라우저 종료 13:57:22, 분석·문서 13:57\~14:08 |
| 트랙 / PoC phase | F (`docs/09_laya_vs_jev_plan.md` §7 S3, §7.2 3일차) |
| 가설 | 해당 없음. H1\~H10에 Jev 직접 비교 가설이 없다. 질문은 "같은 입력에서 Jev와 Laya(english / multilingual / Router)의 정답·확률·지연이 어떻게 다른가"이다 |
| 목적 (한 줄) | T4 Banking77-10(key-only 10옵션)과 T5 BoolQ를 Laya와 바이트 동일한 입력으로 Jev에 보내 같은 40행씩 짝 비교한다 |
| 명령어 | 계획·입력 스크립트: `.venv/bin/python results/F/jev_cmp/sessions/S3_20261007/s3_prep.py`(`jev_cmp.py` `payload`로 sha12를 만들고 항목별 `raw/js/iNN_*.js`와 무클릭 `dry_i01_*`, `dry_i41_*`를 생성(`raw/js/`는 공개 저장소에는 포함하지 않음). 폼 파일과 Laya JSONL의 state·question·옵션 순서 동일성, 옵션 10개·80자 이하, noul criteria 없음을 assert). 브라우저: Playwright MCP `browser_navigate https://jevplayground.com/` → `browser_run_code_unsafe raw/js/instrument.js`(passive listener, `/api/evaluate`만 관찰하는 fetch wrapper, monotonic 시계) → 항목마다 `browser_run_code_unsafe raw/js/iNN_*.js`(폼 입력 → `window.__jev.ready(sha12, 15000)` → 해시가 맞을 때만 `button.run-button` 클릭) → `browser_evaluate window.__jev.dump()`를 `raw/rNN_<T>_rowRR.json`(공개 저장소에는 포함하지 않음)으로 저장 → `.venv/bin/python …/s3_record.py RUN ITEM`(= `jev_cmp.py record S3 <SET> RUN DUMP --row R` + 중단 조건 분류). 분석: `.venv/bin/python results/F/jev_cmp/jev_cmp.py analyze S3 T4_banking77_10opt_40`, `… analyze S3 T5_boolq_40` |
| 환경 기록 | 로컬 모델 실행 없음. 브라우저는 Playwright MCP Chromium. 대상은 jevplayground.com `POST /api/evaluate`. Laya 수치는 S0 리포트(`results/F/jev_cmp/laya/`, laya 0.3.23, device cpu)에서 읽었다 |
| 체크포인트 | Jev: 응답 `model`과 View details Model ID `typesafe-ai/jev` 80/80, 버전 미표기. Laya english / multilingual revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`(리포트 config.revisions). Router는 T4·T5 각 40행 모두 english |
| 데이터셋 | T4: `data/evals/jev_cmp/T4_banking77_10opt_40.jsonl`, n=40, dataset_sha256 `b124b7fb685abe85de45689984013d9b012c7e0e361d1b29ee55eb12dd2d23bc`, questions_sha256 `3c4b9b99f9cc5adcd3a2930f1fd99613bd115873234f06d8e5b6176ab5bc7074`(리포트 config), 폼 `T4_banking77_10opt_40_playground.json` sha256 `f91e53ca31e0ae9351bc9ed8d6f45a5002dfb4bf10174333a4bfabafd69549e3`. T5: `T5_boolq_40.jsonl`, n=40(true 20 / false 20), dataset_sha256 `2b140a293790121b93dce29fb5c2804054570ee23238618b43a7915a6fe0786a`, questions_sha256 `d8699dd37a63aa7bfbc74dd05ad250872384751ff635e5aeaaaf84cc5d69cebe`, 폼 sha256 `5512be765fe3407b087c05c1501c75af6b2c469cad5efd04a285e9de19de2425`. 세 Laya 리포트 모두 폼 파일과 두 해시가 같다 |
| 디바이스 / 정밀도 / 스레드 | Jev: hosted, 미상. Laya: S0 리포트 기준 CPU fp32, intra-op 10 / inter-op 1, batch 8 |
| 파라미터 | Part A: Single question / Choice. 옵션 10개(key-only, 최대 48자)를 폼 순서대로 넣었고, Question `` Which banking intent does `message` express? ``, State = 폼 `state_text`. Part B: Single question / Boolean. Question `` Based on `passage`, is the answer to `question` yes? ``, State = 폼 `state_text`(최대 1,194자). 운영: 처음부터 monotonic 기준 Run 간격 가드 15 s. 5xx면 65 s 뒤 같은 항목 1회 재시도(`next_gap`), 재시도도 실패하면 종료. 429·제한 문구·captcha는 재시도 없이 즉시 세션 중단. 세션 상한 100(계획 80) |
| 반복 / warm-up | 단일 패스, warm-up 없음. 항목당 1회, 재시도 0(run 번호 = 항목 번호) |
| 소요 시간 | 브라우저 세션 21분 39초(13:35:43\~13:57:22), 평가 구간 20분 25초. 작업 전체 약 41분(자료 읽기·준비 약 8분, 브라우저 22분, 분석·문서 약 11분) |

## 결과

| 지표 | 값 | upstream 참고치 (출처) | 차이 | 비고 |
|---|---|---|---|---|
| choice_accuracy (T4, 같은 40행) | Jev 37/40 = 0.925 [0.801, 0.974]; Laya english·Router 0.725 [0.572, 0.839], multilingual 0.750 [0.598, 0.858] | Jev Banking77 0.870 (72 라벨, 제3자; `docs/09_laya_vs_jev_plan.md` §1), Laya 0.425 (77 옵션, BENCHMARKS.md:162) | 비교 불가 | 옵션 수가 다르다. 맥락: Laya v0(`key: key spaced`) english 0.825 / multilingual 0.575(`laya_summary.md` §4b), Jev에는 v0를 보내지 않았다 |
| noul_accuracy (T5, 같은 40행) | Jev 37/40 = 0.925 [0.801, 0.974]; Laya english·Router 0.725 [0.572, 0.839], multilingual 0.600 [0.446, 0.737] | Laya english 0.830 / multilingual 0.787 (README.md:1353, N=600, in training mix). Jev 공개치 없음 | english −0.105, multilingual −0.187 | english CI는 0.830을 포함하고 multilingual CI는 0.787을 포함하지 않는다 |
| McNemar (exact) | T4 Jev vs english·Router b=9 / c=1 p=0.0215, vs multilingual 8 / 1 p=0.0391. T5 vs english·Router 9 / 1 p=0.0215, vs multilingual 15 / 2 p=0.0023 | n/a | | 같은 라벨/예측: T4 30·31/40, T5 30·23/40 |
| AUROC p(true) (T5) | Jev 0.988 [0.955, 1.000], english 0.810 [0.662, 0.942], multilingual 0.682 [0.496, 0.838] | n/a | Jev − english +0.177 [+0.043, +0.326], − multilingual +0.305 [+0.152, +0.486] | bootstrap 2,000회(seed 13), 동점 0.5. 예측 true 21 / 19 / 18 (gold 20) |
| score_mae | n/a | n/a | | score 과제 없음 |
| Brier | T4 Jev 0.114, english 0.349, multilingual 0.478; T5 Jev 0.098, english 0.393, multilingual 0.615 | n/a | | Σ(p − onehot)², T4는 행별 옵션 10개, T5는 {false, true} 2칸. Jev 확률 2자리 반올림 |
| ece | T4 Jev 0.069 (english 0.150, multilingual 0.262); T5 Jev 0.103 (0.190, 0.294) | Jev typed-decisions 0.144, nibzard 0.246 (09 §1) | | 15 bins, max p 기준 |
| mean_confidence (Jev 표시 top p) | T4 0.973 (정답 0.984 / 오답 0.847), 100% 표시 31/40, 오답 중 ≥ 0.90 1/3, 정답 옵션 0% 0/40. T5 0.913 (0.931 / 0.697), 100% 표시 0/40, 오답 중 ≥ 0.90 0/3 | n/a | | T5 top ≥ 0.80이면 34/40을 남기고 오류 0(같은 40행 기술통계) |
| latency (Jev 표시 "server + network" = latencyMs) | T4 median 227.5 (181\~417) ms, T5 200.5 (172\~363) ms | Jev 제3자 p50 236\~276 ms (09 §1) | 범위 안 또는 약간 아래 | 표시 = latencyMs half-up 80/80 |
| latency (브라우저 POST / 클릭→완료) | T4 470.5 / 472.5 ms, T5 442 / 443 ms (median) | n/a (하드웨어·네트워크 다름) | | POST − latencyMs 중앙 233.8 ms |
| 토큰 (View details) | T4 입력 476 (455\~546) / 출력 116.5 (107\~125); T5 402.5 (330\~545) / 20 (20) | n/a | | 합계 입력 35,756 / 출력 5,460 |

## §7.3 세션 필드

| 항목 | 값 |
|---|---|
| 사이트 상태 확인 | 13:35:43 페이지 정상 로드. UI·DOM id가 S2와 같다(기본 Single question, 예시 "Support Routing" Choice 4칸). 계측 설치 시 페이지 본문의 제한 문구 검사 결과는 없음이었다. 예산 때문에 기본 예시는 실행하지 않았다 |
| 요청 수 | `POST /api/evaluate` 80회 = Part A 40 + Part B 40, 모두 200. 5xx 0, 4xx 0(429 0), 재시도 0. 세션 상한 100 중 80. 네트워크 목록: POST 80(전부 `/api/evaluate`, 200), GET 70(문서 1, 정적 34, Next.js RSC prefetch 35, 모두 200) |
| 요청 없는 클릭 | 0. 무클릭 dry run 2회(Part A 첫 항목, Part B 첫 항목)는 폼 입력과 해시 대조만 했다. View details 펼치기 클릭 6회(스크린샷용)는 Run 버튼이 아니며 요청을 만들지 않았다 |
| 간격 | monotonic 기준 79개 간격: 최소 15.024 s, 중앙 15.125 s, 최대 28.862 s(run 4). Part A 15.025 / 15.126 / 28.862, Part B 15.024 / 15.125 / 22.823. resource timing 시작 간격도 같다. Date.now() 기준 간격도 같은 값이고, wall − mono 오프셋은 0 → 15 ms로 서서히 늘었다(스텝 없음) |
| Model ID / 토큰 범위 | `typesafe-ai/jev` 80/80. 입력 330\~546, 출력 20\~125. `rounding` {probabilityDecimals 2, scoreDecimals 2}, `warnings` [] 80/80. provider `confidence`는 T4 40/40(`decision`), T5 0/40 |
| 입력 해시 대조 | 요청 전 sha12 80/80 일치. 요청 후 request body가 폼 파일 payload와 바이트 단위로 80/80 같다 |
| 파싱 실패 | 0. T4 choice 답 40개는 모두 입력 라벨 중 하나와 정확히 같고, 확률 키 집합이 옵션 10개와 같다(40/40, 합계 1.00). T5 Boolean 40개는 `probability` 하나를 돌려주었다(0.02\~0.99). 화면 = 응답 80/80 |
| 오류 문구 | 없음. 429·제한 문구·captcha·"temporarily unavailable" 0건. 콘솔은 경고 193건(CSS preload)이고 오류는 0건이다 |
| Laya 대응 리포트 | `results/F/jev_cmp/laya/T4_banking77_10opt_40_{english,multilingual,router}.json`(questions_sha256 `3c4b9b99…`), `T5_boolq_40_{english,multilingual,router}.json`(`d8699dd3…`) |
| 오늘 누적 사이트 사용량 | 160 = S2 80 + S3 80(`jev_runs_all.jsonl`의 2026-10-07 행). 하루 100 자체 상한은 2026-10-07 프로젝트 책임자 결정으로 해제했다. 101번째 요청은 S3 run 21(13:41:37.352)이었고, 이후 run 80까지 제한 신호가 없었다 |
| 비용 | n/a. Jev 단가는 확인하지 않았다. 토큰 합계 입력 35,756 / 출력 5,460 |

## 산출물

- `results/F/jev_cmp/sessions/S3_20261007/S3_summary.md`: T4·T5 결과, McNemar, AUROC·bootstrap, 보정·확신도, 오답 분석, 지연·토큰, 관찰과 한계
- `results/F/jev_cmp/sessions/S3_20261007/S3_requests.jsonl`(80줄), `results/F/jev_cmp/jev_runs_all.jsonl`(master 231줄. 앞 151줄은 S3 전 사본과 바이트 동일) (두 파일은 공개 저장소에는 포함하지 않음)
- `results/F/jev_cmp/sessions/S3_20261007/raw/`: dump 80, `run_plan.json`, `js/`(instrument, 항목 스크립트 80, dry run 2), `evaluate_timing_all.json`, `network_requests.txt`, `network_requests_all.txt`, `console.log`, `mcp/`(snapshot 2, MCP 콘솔 로그) (`run_plan.json` 외에는 공개 저장소에는 포함하지 않음)
- `results/F/jev_cmp/sessions/S3_20261007/shots/`(공개 저장소에는 포함하지 않음): Part A 1·20·40번째, Part B 1·20·40번째 항목(View details 열림, full page)
- `results/F/jev_cmp/sessions/S3_20261007/s3_prep.py`, `s3_record.py`
- `results/F/jev_cmp/jev_cmp.py`: `analyze` 확장(아래)

## 이상 / 주석

- **오류 없음.** S2 첫 요청의 502 같은 일시 장애가 이번에는 없었다. 그래서 `docs/09` §7.2의 "S3 이월 규칙"(5xx 재시도 시 마지막 항목을 S4로)은 쓰지 않았다. 프로젝트 책임자 결정(세션 상한 100)으로 재시도 여유도 20회 있었다.
- **계측(S2 대비).** 처음부터 모든 시각을 하나의 monotonic 축(`performance.timeOrigin + performance.now()`)에 기록했다. 클릭, fetch wrapper, status log, resource timing이 모두 같은 축이다. 그래서 S3 기록의 `click_epoch_ms`·`click_kst`는 Date.now()가 아니라 이 축의 값이다(wall과의 차이 ≤ 15 ms). dump에는 `clicks_wall`(Date.now())과 `wall_minus_mono_ms`를 함께 남겼다. 간격 가드는 마지막 Run 클릭과 마지막 `/api/evaluate` resource entry 중 늦은 쪽을 기준으로 잰다(`raw/js/instrument.js:104-114`).
- **기록 래퍼(`s3_record.py`).** 기존 `jev_cmp.py record`를 호출한다. 그 전에 dump의 클릭이 이미 기록된 마지막 클릭보다 새로운지 확인한다(`s3_record.py:30-34`). 같은 payload를 재시도할 때 오래된 dump가 body 대조를 통과하는 경우를 막기 위한 것이고, 이번에는 발동하지 않았다. 종료 코드: 0 기록 성공, 1 미기록, 2 5xx(60 s 넘게 대기 후 1회 재시도), 4 429 또는 제한 문구·captcha(즉시 중단), 5 기타 오류(중단), 3 성공했지만 중단 문구가 보임(`:52-65`).
- **`jev_cmp.py` 변경(최소).**
  1. `analyze`의 Brier를 행별 옵션으로 계산한다(`jev_cmp.py:328-329`, `:341-342`). 기존 코드는 0번 행의 옵션 집합으로 모든 행을 계산해서 행마다 옵션이 다른 T4(T7도 같다)에서 틀린 값을 냈다. 수정 전 T4 출력은 Jev 0.000, Laya english 0.019였다. 수정 후 Laya 값은 `laya_summary.md`와 같다(0.349 / 0.478). 옵션이 행마다 다르면 클래스별 표와 혼동 행렬 대신 오답 gold → pred 목록을 낸다(`:367-391`).
  2. Boolean 세트용 분기 `boolean_lines`를 추가했다(`:333-336`, `:461-515`). 정확도(p(true) ≥ 0.5), 예측 양성률, 2칸 Brier, ECE, AUROC와 항목 bootstrap CI, paired AUROC 차이, 같은 표본 최적 임계값, 확신도, 행별 표를 낸다. `auroc`(`:455-458`)는 `scripts/calibrate_ko.py` auroc와 같은 정의(동점 0.5)다.
  3. 지연 표와 요청 줄은 `latency_lines`·`request_lines` 함수로 옮겼다(`:433-452`). 출력은 같다.
  4. 회귀 확인: 변경 전후 `analyze S1 T2_ag_news_40`, `analyze S2 T3_emotion_40` 출력이 바이트 단위로 같다. `t1 S1,S2`도 그대로 실행된다.
- **간격 최대 28.9 s(run 4).** run 3과 4 사이에 기록 래퍼를 고친 시간이다. 사이트와는 무관하다. Part B 최대 22.8 s(run 41)는 Part B dry run과 스크린샷 시간이다.
- **해석이 들어간 판단(확인 필요).** T4에서 네 시스템이 모두 틀린 2행을 라벨 경계가 애매한 사례로 본 것, T5에서 세 시스템이 모두 틀린 1행의 gold가 애매하다고 본 것은 지문을 읽고 내린 판단이다. 데이터셋 라벨은 그대로 채점했다.
- `docs/`와 `data/evals/`는 편집하지 않았다. Laya 모델은 실행하지 않았다. Playwright MCP 출력 디렉터리(snapshot 2, 콘솔 로그 1)는 `raw/mcp/`로 복사한 뒤 레포 루트에서 삭제했다.

## 다음 액션

- `docs/09_laya_vs_jev_plan.md` §7.1\~7.2에 S3 결과 반영(별도 작업. 이 세션은 docs를 편집하지 않았다). 3일차 누적은 사이트 전체 기준 258(1일차 98 + 2일차 80 + 3일차 80)이다.
- S4: T6 SST-5 40(Score 5레벨) + T7 en·de 40. T7은 행마다 옵션이 달라서 이번 `analyze` Brier 수정이 그대로 적용된다.
- 선택(예산 +40): T4 v0(`key: key spaced`) 렌더링을 Jev에도 보내 렌더링 민감도를 비교한다(열린 질문 8, §7.2 S5-b).
- Boolean 보류 임계값(top ≥ 0.80에서 오류 0)은 같은 40행 기술통계다. 쓰려면 별도 표본(T8 또는 다른 BoolQ 추출)에서 미리 고정해 검증해야 한다.

[English](S3_run_card.md) | **한국어**
