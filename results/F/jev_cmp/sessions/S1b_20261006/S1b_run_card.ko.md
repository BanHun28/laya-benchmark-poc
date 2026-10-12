# Run 20261006-1029_jev-playground_S1b (T2_ag_news_40 결정성 10 + 옵션 순서 20)

| 항목 | 값 |
|---|---|
| run_id | 20261006-1029_jev-playground_S1b (Track F, Laya vs Jev 비교 S1b: `docs/09_laya_vs_jev_plan.md` §5의 결정성·옵션 순서 flip) |
| 날짜 / 시작 시각 | 2026-10-06 (KST). 페이지 로드 10:29:33, 첫 클릭 10:29:46.183, 마지막 클릭 10:38:18.926, 브라우저 종료 10:38:30, 분석·문서 \~10:45 |
| 트랙 / PoC phase | F (지시에 따른 S1b, S1 직후) |
| 가설 | 해당 없음. 질문은 두 가지다. 같은 입력에서 Jev 답이 재현되는가. 옵션 순서만 바꿨을 때 Jev와 Laya의 argmax가 바뀌는가 |
| 목적 (한 줄) | T2 10행 재실행으로 결정성을, 20행 순열 실행으로 flip을 측정하고 Laya probe와 같은 순열로 대조한다 |
| 명령어 | 선택·기대값: `.venv/bin/python results/F/jev_cmp/jev_cmp.py expect T2_ag_news_40 --rows 2,7,11,13,15,20,24,29,33,37`, `… expect T2_ag_news_40 --rows 0,3,4,6,8,9,12,14,17,18,21,22,25,26,28,30,31,34,35,38 --probe`. 브라우저: Playwright MCP, Single question / Choice, S1과 같은 계측(passive listener + `/api/evaluate` fetch wrapper) → `browser_fill_form`(state, 순열 행은 choice 4칸도) → `window.__jev.ready('<sha12>')` → `button.run-button` → `window.__jev.dump()` → `raw/rNN_*.json`(공개 저장소에는 포함하지 않음). 기록: `jev_cmp.py record S1b T2_ag_news_40 <run> <dump> --row R --phase determinism` 또는 `--phase option_order --probe`. 분석: `jev_cmp.py stability S1 S1b T2_ag_news_40` |
| 환경 기록 | 로컬 모델 실행 없음. Playwright MCP Chromium. Laya 대조는 기존 probe JSON(`T2_option_order_k1_{english,multilingual}.json`, CPU) |
| 체크포인트 | Jev `typesafe-ai/jev` 30/30(버전 미표기). Laya english / multilingual revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`(probe가 S0 리포트와 parity 40/40) |
| 데이터셋 | `data/evals/jev_cmp/T2_ag_news_40.jsonl`(T2 파일은 공개 저장소에는 포함하지 않음), dataset_sha256 `555c7cd7d38c78d183fe884c62e1bbb102d040871bf6e66a8911269eba20fd21`, questions_sha256 `c472cb1cb971dab3d01c811ccc0f997d39516555fd43f513a8c59654e0457be1`. 폼 `T2_ag_news_40_playground.json` sha256 `1da0f5494068650edbcc6a23bf26f46790ef6592339f28f46d922f32370191d9` |
| 디바이스 / 정밀도 / 스레드 | Jev hosted, 미상. Laya probe CPU fp32 |
| 파라미터 | Question ``What is the topic of `article`?``, choices 4개(라벨 문자열은 S1과 같음). 결정성 10행은 원 순서, flip 20행은 probe의 행별 순서. 선택 규칙과 순열 출처는 `S1b_summary.md` §1 |
| 반복 / warm-up | 행당 1회. 결정성은 S1의 같은 행과 짝을 이룬다(S1과 약 15\~30분 간격, 다른 페이지 로드) |
| 소요 시간 | 브라우저 세션 약 9분(평가 구간 8분 33초). 작업 전체 약 20분 |

## 결과

| 지표 | 값 | upstream 참고치 (출처) | 차이 | 비고 |
|---|---|---|---|---|
| 결정성: 같은 라벨 | 10/10 | Laya english 재실행 완전 일치 (`results/F/jev_cmp/laya_summary.md` §5) | n/a | |
| 결정성: 같은 확률 벡터 (2자리 표시) | 9/10, 최대 \|Δp\| 0.01 (Jev의 항목별 출력은 공개 저장소에서 생략) | 같은 곳 | n/a | confidence도 같은 1건만 0.01 차이. 토큰 수 10/10 같음 |
| 결정성: latencyMs | 같은 행 중앙 S1 221.3 → S1b 233.2 ms, 행별 \|Δ\| 중앙 26.7 ms | n/a | n/a | |
| 옵션 순서 flip, Jev | 0/20 = 0.000, Wilson 95% [0.000, 0.161] | Jev 제3자 0.13 (`docs/09_laya_vs_jev_plan.md` §1) | −0.13 | P(0/20 \| 0.13) = 0.062, 배제 못 함 |
| 옵션 순서 flip, Laya english / multilingual (같은 20행·같은 순서) | 0/20 / 0/20 | T2 probe 40행 0.000 / 0.000 (`results/F/jev_cmp/T2_option_order_k1_{english,multilingual}.md`) | 0 | |
| choice_accuracy (flip 20행) | Jev 원 순서 19/20, 순열 19/20 | n/a | n/a | 오답 1건 |
| noul_accuracy / score_mae / ece | n/a | n/a | n/a | choice 과제, 소표본 |
| mean_confidence | 순열 실행 top p 평균 변화 0.007, 최대 0.08 | n/a | n/a | |
| latency (Jev 표시 / 브라우저 POST / 클릭→완료) | 223 (165\~646) / 457.5 (381\~873) / 460 (383\~875) ms, n=30 | Jev 제3자 p50 236\~276 ms | 범위 근처 | 표시 = latencyMs half-up 반올림 30/30 |
| 토큰 | 입력 424.5 (410\~534), 출력 68 (66\~71) | n/a | n/a | |

## §7.2 세션 필드

| 항목 | 값 |
|---|---|
| 사이트 상태 확인 | 10:29:33 페이지 정상 로드. 첫 요청(10:29:46)이 200으로 끝났다 |
| 요청 수 | `POST /api/evaluate` 30회: 성공 30, 5xx 0, 4xx 0, 재시도 0. 브라우저 네트워크 목록도 POST 30(모두 200), GET 46(정적 25, RSC prefetch 20, 문서 1) |
| 간격 | 최소 17.3 s, 중앙 17.5 s, 최대 20.5 s |
| Model ID / 토큰 범위 | `typesafe-ai/jev` 30/30, 입력 410\~534, 출력 66\~71, `rounding` {2, 2}, `warnings` [] |
| 입력 해시 대조 | 요청 전 sha12 30/30 일치, 요청 후 request body 바이트 대조 30/30 일치. 순열 행은 probe 순서로 기대값을 만들었고, 분석 단계에서 기록된 `perm`이 probe 순서와 같은지 20/20 다시 확인했다 |
| 파싱 실패 | 0. 화면 표시 = 응답 30/30 |
| 오류 문구 | 없음. 콘솔 오류 0, 경고 192(모두 CSS preload 안내) |
| Laya 대응 | 결정성: `results/F/jev_cmp/laya/T1_typed_decisions_40_english_rerun.json`(Laya 결정성 기준). flip: `results/F/jev_cmp/T2_option_order_k1_{english,multilingual}.json` |
| 오늘 누적 사이트 사용량 | 파일럿 25 + 가용성 확인 2 + S1 41 + S1b 30 = 98 (상한 100) |

## 산출물

- `results/F/jev_cmp/sessions/S1b_20261006/S1b_summary.md`
- `results/F/jev_cmp/sessions/S1b_20261006/S1b_requests.jsonl` (30줄), `results/F/jev_cmp/jev_runs_all.jsonl` (master 71줄) (두 파일은 공개 저장소에는 포함하지 않음)
- `results/F/jev_cmp/sessions/S1b_20261006/raw/` (dump 30, `network_requests.txt`, `console.log`, `mcp/` snapshot 34; 모두 공개 저장소에는 포함하지 않음)
- `results/F/jev_cmp/sessions/S1b_20261006/shots/S1b_run01_det_row02.png`, `S1b_run11_perm_row00.png`, `S1b_run30_perm_row38.png`(공개 저장소에는 포함하지 않음)
- `results/F/jev_cmp/jev_cmp.py` (`--probe`, `stability` 추가)

## 이상 / 주석

- 결정성 대상 10행 중 8행이 100% 표시라 확률 변동을 볼 여지가 작다. 변동은 확률이 낮은 행 1건에서만 나왔다.
- flip 20행은 S1 기준 확신도가 높은 항목이 대부분이다(100% 표시 13/20). 0/20은 "이 조건에서 flip이 드물다"는 뜻이고 공개치 0.13과의 차이는 유의하지 않다.
- Playwright MCP 출력 디렉터리(snapshot 34, 콘솔 로그)는 `raw/mcp/`로 복사한 뒤 삭제했다.

## 다음 액션

- 순서 민감도는 옵션이 많고 확신도가 낮은 과제(T3 emotion 6옵션, T4·T7 10옵션)에서 다시 측정하는 편이 정보량이 크다. 그 경우에도 Laya probe와 같은 순열을 쓴다.
- 오늘 남은 사이트 예산은 2회다. 다음 세션은 내일로 미룬다.

[English](S1b_run_card.md) | **한국어**
