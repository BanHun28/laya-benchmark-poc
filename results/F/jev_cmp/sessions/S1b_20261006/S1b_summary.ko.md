# S1b 요약: T2 결정성 10 + 옵션 순서 flip 20 (2026-10-06)

**판정.**
1. **결정성.** 같은 payload를 약 25분 뒤 다시 보낸 10건에서 라벨은 10/10 같았다. 확률 벡터는 9/10이 같았고, 나머지 1건은 0.01 차이였다(Jev의 항목별 출력은 공개 저장소에서 생략). provider confidence도 같은 1건만 0.01 달랐고, 입출력 토큰 수는 10/10 같았다. 결과는 사실상 결정적이지만 비트 단위로 같지는 않다. 반면 `latencyMs`는 run마다 다르다(중앙 |Δ| 26.7 ms).
2. **옵션 순서.** Laya probe와 같은 순열로 20건을 보냈고 Jev flip은 **0/20**(0.000, Wilson 95% [0.000, 0.161])이었다. 같은 20행·같은 순서에서 Laya english와 multilingual도 각각 0/20이다. AG News 4옵션 조건에서는 두 시스템 모두 순서 민감도를 보이지 않았다.
3. 다만 제3자 공개치 0.13은 이 표본으로 배제할 수 없다. p = 0.13일 때 0/20이 나올 확률은 0.062다.

플레이그라운드 경유이며 API가 아니다. 모델 버전은 표기되지 않고(`typesafe-ai/jev` 30/30), 소표본이다.

## 1. 설계

| 항목 | 규칙 |
|---|---|
| 기준 | S1(같은 날 10:05\~10:17)의 T2 응답. S1b 요청은 10:29:46\~10:38:19 |
| 결정성 대상 10행 | S1에서 Jev가 맞힌 행과 틀린 행이 모두 들어가도록 뽑았다(Jev의 항목별 출력은 공개 저장소에서 생략) → rows 2, 7, 11, 13, 15, 20, 24, 29, 33, 37. payload는 S1과 바이트 단위로 같다 |
| flip 대상 20행 | 결정성 10행을 뺀 30행에서 순열이 항등인 row 39를 제외했다(row 13도 항등이지만 이미 결정성 대상). 남은 29행에서 중앙점 등간격(`xs[int((i + 0.5)·n/k)]`)으로 20행을 뽑았다 → 0, 3, 4, 6, 8, 9, 12, 14, 17, 18, 21, 22, 25, 26, 28, 30, 31, 34, 35, 38 |
| 순열 | Laya probe(`results/F/jev_cmp/T2_option_order_k1_english.json`)가 각 row에 쓴 순서를 그대로 썼다. 이 순서는 `random.Random(13)`을 40행에 item-major로 1회씩 소비한 stream이고, 같은 방식으로 다시 생성해 40/40 일치를 확인했다(`scripts/probe_option_order.py` `probe_file`). multilingual probe도 같은 순서다. 그래서 Jev와 Laya가 받은 순열 입력은 같다 |
| flip 정의 | 순열 실행의 argmax 라벨(key)이 S1 원 순서 실행의 라벨과 다르면 flip. probe와 같은 per-permutation 정의다 |
| 입력 검증 | 요청 전 sha12 precheck, 요청 후 request body 바이트 대조(30/30). 순열 행은 `jev_cmp.py record --probe`가 probe의 순서로 기대 payload를 만든다 |

## 2. 결정성 (같은 payload, S1 대비)

| row | gold | S1 (top %) | S1b (top %) | 같은 라벨 | max abs Δp | latencyMs S1 / S1b | confidence S1 / S1b | 토큰 in/out S1 / S1b |
|---|---|---|---|---|---|---|---|---|
| 2 | sports | — | — | — | — | — | — | — |
| 7 | business | — | — | — | — | — | — | — |
| 11 | sports | — | — | — | — | — | — | — |
| 13 | world | — | — | — | — | — | — | — |
| 15 | world | — | — | — | — | — | — | — |
| 20 | sports | — | — | — | — | — | — | — |
| 24 | world | — | — | — | — | — | — | — |
| 29 | world | — | — | — | — | — | — | — |
| 33 | world | — | — | — | — | — | — | — |
| 37 | world | — | — | — | — | — | — | — |

요약:

| 지표 | 값 |
|---|---|
| 같은 라벨 | 10/10 |
| 확률 벡터 일치 | 9/10, 최대 \|Δp\| 0.01 |
| confidence 일치 | 9/10, 최대 \|Δ\| 0.01 |
| 토큰 수 일치 | 10/10 |
| latencyMs 중앙값 | S1 221.3 ms, S1b 233.2 ms |
| run 간 latencyMs \|Δ\| 중앙 | 26.7 ms |

표시값은 2자리로 반올림돼 있어 0.005 미만의 차이는 관측할 수 없다. 표본 10건 중 8건이 100% 표시여서 결정성 검정력은 낮다. 변동이 나온 1건은 확률이 낮은 쪽 항목이었다. 비교 기준으로 Laya english는 T1 200 decisions 재실행에서 답이 완전히 같았다(`results/F/jev_cmp/laya_summary.md` §5).

## 3. 옵션 순서 flip (20행, probe와 같은 순서)

| row | gold | 보낸 순서 | Jev 원 순서 (top %) | Jev 순열 (top %) | flip | 순열에서 원 라벨 p | 고른 slot | Laya en 원 → 순열 | Laya ml 원 → 순열 |
|---|---|---|---|---|---|---|---|---|---|
| 0 | sci_tech | sci_tech / world / sports / business | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 3 | sci_tech | sci_tech / business / world / sports | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 4 | sports | sci_tech / sports / world / business | — | — | — | — | — | sports → sports | sports → sports |
| 6 | sports | sports / sci_tech / world / business | — | — | — | — | — | sports → sports | sports → sports |
| 8 | sports | world / business / sci_tech / sports | — | — | — | — | — | sports → sports | sports → sports |
| 9 | world | world / business / sci_tech / sports | — | — | — | — | — | world → world | world → world |
| 12 | business | sports / world / business / sci_tech | — | — | — | — | — | business → business | business → business |
| 14 | sci_tech | business / world / sci_tech / sports | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 17 | business | world / sports / sci_tech / business | — | — | — | — | — | business → business | business → business |
| 18 | business | business / sports / world / sci_tech | — | — | — | — | — | business → business | business → business |
| 21 | world | business / sci_tech / world / sports | — | — | — | — | — | world → world | world → world |
| 22 | sports | business / world / sports / sci_tech | — | — | — | — | — | sports → sports | sports → sports |
| 25 | business | sci_tech / sports / world / business | — | — | — | — | — | business → business | business → business |
| 26 | sports | sci_tech / world / sports / business | — | — | — | — | — | sports → sports | sports → sports |
| 28 | sci_tech | world / sci_tech / business / sports | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 30 | sci_tech | sci_tech / business / sports / world | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 31 | sci_tech | business / world / sci_tech / sports | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 34 | business | sports / world / business / sci_tech | — | — | — | — | — | business → business | business → business |
| 35 | sci_tech | business / world / sports / sci_tech | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |
| 38 | sci_tech | sports / world / sci_tech / business | — | — | — | — | — | sci_tech → sci_tech | sci_tech → sci_tech |

| 시스템 (같은 20행, 같은 순서) | flip / 20 | 비율 [Wilson 95%] | 참고치 |
|---|---|---|---|
| Jev (플레이그라운드) | 0 | 0.000 [0.000, 0.161] | 제3자 공개 Jev per-permutation flip 0.13 (`T2_option_order_k1_english.md` 참고표, `docs/09_laya_vs_jev_plan.md` §1). P(0/20 \| p = 0.13) = 0.062 |
| Laya english | 0 | 0.000 [0.000, 0.161] | T2 probe 전체 40행 0.000 (`results/F/jev_cmp/T2_option_order_k1_english.md`) |
| Laya multilingual | 0 | 0.000 [0.000, 0.161] | T2 probe 전체 40행 0.000 (`T2_option_order_k1_multilingual.md`) |

- 이 20행에서 Jev 정확도는 원 순서와 순열 모두 19/20이다. 오답 1건은 두 순서에서 라벨이 같았다.
- top 확률은 평균 0.007 움직였다. 가장 큰 변화는 0.08이었고 라벨은 유지됐다.
- 고른 slot 분포는 0: 6, 1: 3, 2: 7, 3: 4로, n = 20에서는 위치 편향의 신호가 아니다.
- 공개치 0.13이 어떤 과제·옵션 수에서 측정된 값인지는 이번 세션에서 확인하지 않았다(확인 필요). 이 결과는 "AG News 4옵션, 확신도 높은 항목 위주"라는 조건에 한정된다.

## 4. 지연·토큰 (S1b 30회)

| 측정 | median / min / max |
|---|---|
| 표시 "server + network" (= latencyMs 반올림, half-up) | 223 / 165 / 646 ms |
| 브라우저 POST (resource timing) | 457.5 / 381 / 873 ms |
| 클릭 → 완료 | 460 / 383 / 875 ms |
| 입력 / 출력 토큰 | 424.5 (410\~534) / 68 (66\~71) |

S1(234 / 468 ms)과 같은 수준이다. 브라우저 POST − latencyMs의 중앙값은 233.8 ms로 S1(232 ms)과 같다. 순열은 토큰 수를 바꾸지 않았다(같은 라벨 문자열이고 순서만 다르다).

## 5. 요청과 예산

| 항목 | 값 |
|---|---|
| S1b 요청 | `POST /api/evaluate` 30회, 모두 HTTP 200. 5xx·429·제한 문구·captcha 0, 재시도 0 |
| 간격 | 최소 17.3 s, 중앙 17.5 s, 최대 20.5 s (규칙 ≥ 10 s) |
| 오늘 누적 | 파일럿 25 + 가용성 확인 2 + S1 41 + S1b 30 = **98** (하루 상한 100, 남은 2) |
| master 로그 | `results/F/jev_cmp/jev_runs_all.jsonl` 71줄 (S1 41 + S1b 30, `session` 필드. 공개 저장소에는 포함하지 않음) |

## 6. 파일

| 파일 | 내용 |
|---|---|
| `results/F/jev_cmp/sessions/S1b_20261006/S1b_requests.jsonl`(공개 저장소에는 포함하지 않음) | 30줄 (`phase`: determinism / option_order, `perm`: 보낸 순서) |
| `results/F/jev_cmp/sessions/S1b_20261006/raw/r01_det_row02.json` … `r30_perm_row38.json`(공개 저장소에는 포함하지 않음) | 요청별 dump (request body, 응답 text, DOM, resource timing, 상태 로그) |
| `results/F/jev_cmp/sessions/S1b_20261006/raw/network_requests.txt`, `console.log`, `mcp/` | POST 30 / GET 46, 콘솔(오류 0), MCP snapshot 34(세 항목 모두 공개 저장소에는 포함하지 않음) |
| `results/F/jev_cmp/sessions/S1b_20261006/shots/`(공개 저장소에는 포함하지 않음) | run 1(결정성), 11(첫 순열), 30(마지막) |
| `results/F/jev_cmp/jev_cmp.py` | `expect/record --probe`, `stability S1 S1b T2_ag_news_40` (이 문서의 표) |
| `results/F/jev_cmp/sessions/S1b_20261006/S1b_run_card.md` | run card |

[English](S1b_summary.md) | **한국어**
