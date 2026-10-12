# Run 20261006-1004_jev-playground_S1 (T1 탐색 1 + T2_ag_news_40)

| 항목 | 값 |
|---|---|
| run_id | 20261006-1004_jev-playground_S1 (Track F, Laya vs Jev 비교 세션 S1: Multiple questions 탐색 + Step 2b 대체 실행 T2 AG News) |
| 날짜 / 시작 시각 | 2026-10-06 (KST). 자료 읽기 약 09:50, 페이지 로드 09:54:55, 첫 평가 클릭 10:04:18.760, 마지막 평가 클릭 10:17:27.517, 브라우저 종료 10:17:43, 분석·문서 \~10:30 |
| 트랙 / PoC phase | F (`docs/09_laya_vs_jev_plan.md` §7 S1, Step 2b 대체) |
| 가설 | 해당 없음. H1\~H10에 Jev 직접 비교 가설이 없다. 질문은 "같은 입력에서 Jev와 Laya(english / multilingual / router)의 정답·확률·지연이 어떻게 다른가"이다 |
| 목적 (한 줄) | Multiple questions 모드가 T1을 그대로 실을 수 있는지 확인하고, 불가하면 T2 AG News 40을 같은 입력으로 Jev에 보내 Laya와 짝 비교한다 |
| 명령어 | 기대 payload: `.venv/bin/python results/F/jev_cmp/jev_cmp.py expect T2_ag_news_40` (T1: `expect T1_typed_decisions_40 --rows 30 --qids credential_compromise,disposition,severity,true_positive`). 브라우저: Playwright MCP로 https://jevplayground.com/ → passive listener와 `/api/evaluate` fetch wrapper 설치 → 폼 입력(`browser_fill_form`, id selector) → `window.__jev.ready('<sha12>')`(12 s 간격 대기 + 해시 대조) → `button.run-button` 클릭 → `window.__jev.dump()`를 `raw/rNN_*.json`(공개 저장소에는 포함하지 않음)으로 저장. 기록: `.venv/bin/python results/F/jev_cmp/jev_cmp.py record S1 T2_ag_news_40 <run> raw/rNN_T2_rowRR.json --row RR`. 분석: `jev_cmp.py analyze S1 T2_ag_news_40` |
| 환경 기록 | 로컬 모델 실행 없음. 브라우저는 Playwright MCP Chromium(UA Chrome/154, macOS). 대상은 Next.js 사이트 jevplayground.com의 `POST /api/evaluate`. Laya 수치는 S0 리포트(CPU fp32, intra-op 10)에서 읽었다 |
| 체크포인트 | Jev: 페이지 "TypeSafe Jev", 응답 `model`과 details Model ID `typesafe-ai/jev`(41/41), 버전 미표기. Laya: english / multilingual revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`(리포트 config.revisions) |
| 데이터셋 | T2: `data/evals/jev_cmp/T2_ag_news_40.jsonl`(T2 파일은 공개 저장소에는 포함하지 않음), n=40, dataset_sha256 `555c7cd7d38c78d183fe884c62e1bbb102d040871bf6e66a8911269eba20fd21`, questions_sha256 `c472cb1cb971dab3d01c811ccc0f997d39516555fd43f513a8c59654e0457be1`(Laya 리포트 config에서 복사). 폼 `T2_ag_news_40_playground.json` sha256 `1da0f5494068650edbcc6a23bf26f46790ef6592339f28f46d922f32370191d9`. T1 탐색: `T1_typed_decisions_40.jsonl` dataset_sha256 `45806a15aa17863895d5a3e2be24f06ac4d39b751de76eea4f2dcaefc227ba85`, questions_sha256 `d46ef26a6ec2f2f8c6fc0cfa1e81715751dda05f173cd028ae3eaaa4b9d519cb`(세션 중 09:55:26 재빌드, 아래 이상 항목) |
| 디바이스 / 정밀도 / 스레드 | Jev: hosted, 미상. Laya: 원 리포트 기준 CPU fp32, intra-op 10 / inter-op 1, batch 8 |
| 파라미터 | T2: Single question, Decision type Choice, Question ``What is the topic of `article`?``, choices 4개 고정 순서 `world: world news and international politics` / `sports: sports` / `business: business and economy` / `sci_tech: science and technology`, State = 폼 `state_text`(JSON 문자열). T1 탐색: Multiple questions, row 30, 4문항(boolean, choice 4, score 5레벨, boolean), urgency(4레벨) 생략. 운영 규칙: Run 간격 ≥ 10 s(실제 ≥ 17 s), 5xx 시 60 s 후 1회 재시도, 429·제한 문구·captcha 즉시 중단 |
| 반복 / warm-up | 단일 패스, warm-up 없음, 항목당 1회 성공 |
| 소요 시간 | 브라우저 세션 약 23분(평가 구간 13분 9초). 전체 작업 약 40분 |

## 결과

| 지표 | 값 | upstream 참고치 (출처) | 차이 | 비고 |
|---|---|---|---|---|
| choice_accuracy, Jev (T2) | 35/40 = 0.875, Wilson 95% [0.739, 0.945] | Jev AG News 0.910 (`docs/09_laya_vs_jev_plan.md` §1, 제3자 공개치) | −0.035 | CI 안 |
| choice_accuracy, Laya english / router (같은 40) | 39/40 = 0.975 [0.871, 0.996] | 0.947 (T4) / 0.950 (apps) (`results/F/jev_cmp/laya_summary.md` §1) | +0.025\~0.028 | router는 40/40 english |
| choice_accuracy, Laya multilingual (같은 40) | 37/40 = 0.925 [0.801, 0.974] | 0.937 / 0.930 (같은 곳) | −0.005\~−0.012 | |
| Jev vs Laya english | 같은 라벨 36/40, b=0, c=4, exact McNemar p=0.125 | n/a | Jev −0.100 | 유의하지 않음 |
| Jev vs Laya multilingual | 같은 라벨 38/40, b=0, c=2, p=0.500 | n/a | Jev −0.050 | 유의하지 않음 |
| noul_accuracy | n/a (T2는 choice). T1 탐색 row 30 boolean — (Jev의 항목별 출력은 공개 저장소에서 생략) | n/a | n/a | 1 case, 지표로 쓰지 않음 |
| score_mae | n/a. T1 탐색 severity |score − teacher| = — | Jev typed-decisions MAE 0.391 | n/a | 1 decision |
| ece | Jev 0.118 / Laya english 0.083 / multilingual 0.058 (15 bins) | Jev 0.246 (nibzard, 09 §1) | n/a | Jev는 2자리 반올림 확률이라 참고용 |
| Brier | Jev 0.220 / Laya english 0.053 / multilingual 0.107 | n/a | n/a | Jev 오답 4/5가 top ≥ 93% |
| mean_confidence | Jev 표시 top 0.977(정답 0.985 / 오답 0.922), 100% 표시 29/40 | n/a | n/a | provider confidence 0.980 / 0.894 |
| latency (Jev 표시 "server + network" = latencyMs) | median 234, min 188, max 448 ms (n=40) | Jev 제3자 p50 236\~276 ms (09 §1) | 범위 안 | |
| latency (Jev 브라우저 POST / 클릭→완료) | median 468 (415\~749) / 470.5 (417\~751) ms | n/a (하드웨어·네트워크 다름) | n/a | Laya: P2 왕복 20.1 ms (`results/poc/P2_20261003.md:67`), D1 english CPU 1q 86.6 ms (`results/D/D_summary_20261003.md:34`) |
| 토큰 (Jev details) | T2 입력 중앙 425 (402\~534), 출력 중앙 68 (66\~71). T1 탐색 4문항 — / — | n/a | n/a | |

## §7.2 세션 필드

| 항목 | 값 |
|---|---|
| 사이트 상태 확인 | 09:54:55 페이지 정상 로드. 예산 절약을 위해 기본 예시는 실행하지 않았고, 첫 요청(탐색, 10:04:18.760)이 200으로 끝나 상태 확인을 겸했다 |
| 요청 수 | `POST /api/evaluate` 41회: 성공 41, 5xx 0, 4xx 0, 재시도 0. 세션 예산 50 중 41. 브라우저 네트워크 목록도 POST 41(모두 200), GET 104(정적 59, Next.js RSC prefetch 44, 문서 1) |
| 요청 없는 클릭 | Run 1회(10:04:00.602)가 클라이언트 검증(4레벨 rubric, 레벨 4 빈칸)에서 막혔다. wrapper 기록 0, resource timing 0 |
| 간격 | 평가 클릭 간 최소 17.0 s, 중앙 17.4 s, 최대 94.5 s(T1 탐색 → T2 전환). 탐색 요청은 검증 probe 클릭 후 18.2 s |
| Model ID / 토큰 범위 | `typesafe-ai/jev` 41/41. 입력 402\~803, 출력 66\~162. `rounding` {2, 2}, `warnings` [] |
| 입력 해시 대조 | 요청 전: 페이지에서 폼 값으로 만든 payload의 sha12가 폼 파일 기대값과 41/41 일치. 요청 후: 캡처한 request body가 기대 payload와 바이트 단위로 41/41 일치 |
| 파싱 실패 | 0. 응답 DECISION이 입력 라벨 중 하나와 정확히 같음 40/40(T2), 화면 표시와 응답 일치 41/41 |
| 오류 문구 | 없음(5xx·"temporarily unavailable"·429·rate-limit·captcha 0). 콘솔 오류 0, 경고 185건 모두 CSS preload 안내 |
| Laya 대응 리포트 | `results/F/jev_cmp/laya/T2_ag_news_40_{english,multilingual,router}.json` (questions_sha256 `c472cb1cb971dab3…`), T1 탐색 비교는 `T1_typed_decisions_40_{english,multilingual,router,typed-decisions}.json` (`d46ef26a6ec2f2f8…`) |
| 비용 | n/a. Jev 단가는 이번 세션에서 확인하지 않았다. T2 40회 토큰 합계는 입력 17,182 / 출력 2,739 |

## 산출물

- `results/F/jev_cmp/sessions/S1_20261006/multi_question_mode.md`: 모드 탐색, 레시피, 한계, T1 선택지
- `results/F/jev_cmp/sessions/S1_20261006/S1_summary.md`: T2 결과, 확신도, 지연, 관찰, 남은 예산
- `results/F/jev_cmp/sessions/S1_20261006/S1_requests.jsonl`, `results/F/jev_cmp/jev_runs_all.jsonl`(master, 41줄) (두 파일은 공개 저장소에는 포함하지 않음)
- `results/F/jev_cmp/sessions/S1_20261006/raw/`: `r01_T1_row30_multi.json`, `r02_T2_row00.json` … `r41_T2_row39.json`, `explore_js_{hits,payload,schema}.json`(클라이언트 번들 발췌), `network_requests.txt`, `console.log`, `mcp/`(MCP 자동 snapshot 63개와 콘솔 로그 사본) (이 디렉터리의 파일은 공개 저장소에는 포함하지 않음)
- `results/F/jev_cmp/sessions/S1_20261006/shots/`(공개 저장소에는 포함하지 않음): `explore01~04_*.png`, `T2_run01_row00.png`, `T2_run20_row19.png`, `T2_run40_row39.png`
- `results/F/jev_cmp/jev_cmp.py`: expect / record / analyze

## 이상 / 주석

- **T1 Step 2a 불가.** Score 루브릭이 정확히 5레벨이라 4레벨 score 70 decisions를 같은 입력으로 보낼 수 없다(Single 모드도 같은 검증). 규칙대로 Step 2b(T2)로 바꿨다. T1 진행안(A/B/C)은 `multi_question_mode.md` §3에 있다.
- **세션 중 데이터 재빌드.** 09:55:26에 `data/evals/jev_cmp/*`가 다시 써졌다(T1에 `jev_excluded` 표시, T4 key-only 재빌드, MANIFEST 갱신). T1 dataset_sha256이 `fb70f4cb…`에서 `45806a15…`로 바뀌었고 questions_sha256 `d46ef26a…`는 그대로다. Laya T1 리포트도 09:56\~09:58에 새 sha로 다시 써졌다. 탐색 요청(10:04)과 T2 요청은 모두 재빌드 이후 파일로 만든 payload와 대조했다. T2 파일 sha는 바뀌지 않았다. `docs/09_laya_vs_jev_plan.md`도 10:05에 갱신됐다(80자 결정 반영). 이 세션은 docs와 data를 편집하지 않았다.
- **계측 변경(파일럿 대비).** 파일럿의 passive listener에 더해 `/api/evaluate`만 감싸는 fetch wrapper를 넣어 request body와 응답 text를 기록했다. 요청 인자는 그대로 전달되고 추가 요청은 없다. 클라이언트 검증 규칙을 읽으려고 이미 로드된 JS chunk를 `cache: 'force-cache'`로 3번 다시 읽었다(정적 GET, API 요청 아님).
- **지연 표기 정의.** Jev 표시 지연(`latencyMs`)은 플레이그라운드 서버가 잰 값으로 보이며 정의는 공개되지 않았다. 브라우저 POST와의 차이(중앙 232 ms)는 파일럿과 같은 크기다.
- **Playwright MCP 출력 정리.** 세션 중 레포 루트에 생긴 Playwright MCP 출력 디렉터리(snapshot 63개와 콘솔 로그)는 `raw/mcp/`로 복사한 뒤 삭제했다.

## 다음 액션

- T1 진행안 결정(A: multi 39 요청 / B: 루브릭 덧대기 변형 / C: single 120 요청). 안 A면 row 30의 run 1을 재사용할 수 있다(payload 동일).
- T6 비교 규칙 고정: argmax 레벨 정확도 + E[level] MAE(Jev `score`가 E[level]이다).
- 오늘 남은 사이트 예산 32회(파일럿 25 + 확인 2 + S1 41 = 68). S2a 후보: T2 순열 프로브 20 + 결정성 10.

[English](S1_run_card.md) | **한국어**
