# 06. 기록 템플릿

**목적**: 벤치마크·PoC 의 모든 실행과 결정이 같은 양식으로 남아, 업스트림 수치와의 비교·재현·Go/No-Go 판정이 문서만으로 가능하게 한다.
**선행 문서**: `02_environment_setup.md` §7(기록 규약), `03_benchmark_plan.md`(트랙 A \~ F), `04_korean_evalset_spec.md`(데이터셋), `05_poc_plan.md`(PoC phase).
**산출물**: `results/<track>/<run-id>.md`(Run Card), `results/REPORT.md`, `docs/decisions/ADR-<n>.md`, `data/handwritten/<set>_label_policy_v<n>.md`.

템플릿은 그대로 복사해 채운다. 비어 있는 항목은 지우지 말고 `n/a` 와 이유를 쓴다. 숫자는 표 안에만 둔다.

---

## 1. 실험 실행 기록 (Run Card)

파일명: `results/<track>/<YYYYMMDD-HHMM>_<model>_<dataset>.md`. 같은 이름의 `.json`(`laya-evals --json` 또는 우리 스크립트 출력)과 짝을 이룬다. `<track>` 은 `A`\~`F` 또는 `poc`.

```markdown
# Run <YYYYMMDD-HHMM>_<model>_<dataset>

| 항목 | 값 |
|---|---|
| run_id | <YYYYMMDD-HHMM>_<model>_<dataset> |
| 날짜 / 시작 시각 | YYYY-MM-DD HH:MM (KST) |
| 트랙 / PoC phase | A~F 또는 poc-phase-N |
| 가설 | H<n> (01_laya_analysis.md 의 번호) |
| 목적 (한 줄) | 무엇을 확인하려는가 |
| 명령어 | `source env.sh && .venv/bin/laya-evals run ... --json results/<track>/<run-id>.json` (실행한 그대로. `.venv/`는 공개 저장소에는 포함하지 않음) |
| 환경 기록 | results/env/env_<YYYYMMDD-HHMM>.json |
| 체크포인트 | english / multilingual / typed-decisions, revision 55cf4c4... (리포트 config.revisions 또는 env JSON checkpoints.*.snapshot_sha) |
| 데이터셋 | data/evals/<set>.jsonl, n=<rows>, dataset_sha256=<리포트 config.dataset_sha256>, questions_sha256=<config.questions_sha256> |
| 디바이스 / 정밀도 / 스레드 | cpu fp32 또는 mps (dtype_for(rows)=fp32|fp16), intra-op N, inter-op 1 |
| 파라미터 | batch_size=, sort_by_length=, min_confidence=, max_len=, head_max_len=, 기타 |
| 반복 / warm-up | warm-up <k>회 버림, 측정 <n>회, 집계 중앙값/p95 |
| 소요 시간 | 로드 <s>, 실행 <s> |

## 결과

| 지표 | 값 | upstream 참고치 (출처) | 차이 | 비고 |
|---|---|---|---|---|
| choice_accuracy | | | | |
| noul_accuracy | | | | |
| score_mae | | | | |
| ece | | | | |
| mean_confidence | | | | |
| latency_p50_ms / p95 | | n/a (하드웨어 다름) | | |
| (트랙 고유 지표) | | | | |

## 산출물
- results/<track>/<run-id>.json
- results/<track>/<run-id>.md (laya-evals --markdown 이 썼다면 그 파일)
- 플롯·로그 경로

## 이상 / 주석
- 경고 메시지(temperature clamp, tokenizer 패치, CPU fallback) 유무와 원문
- 예상과 다른 점, 재실행 여부와 이유

## 다음 액션
- 이 결과가 바꾸는 계획(03/05 의 어느 항목), 추가 실행 run_id
```

작성 규칙: `upstream 참고치` 는 숫자와 출처를 함께 적는다(예: `0.470 (BENCHMARKS.md §Languages, ko 행)`). 레이턴시는 하드웨어가 달라 비교 대상이 아니므로 `n/a` 로 두고, 우리 머신의 이전 run_id 와만 비교한다. 데이터셋 해시 두 값은 반드시 리포트 JSON 에서 복사한다. 손으로 계산하지 않는다 (출처: docs/evals.md "Run identity").

---

## 2. 결과 리포트 (REPORT.md)

파일: `results/REPORT.md`. 트랙이 끝날 때마다 갱신하고 커밋한다. 모든 숫자 셀은 근거 run_id 를 각주나 괄호로 단다.

```markdown
# Laya 벤치마크·PoC 결과 리포트

## 0. 요약 (3줄)
1. 품질: ...
2. 속도·운영: ...
3. 판정: Go / Conditional Go / No-Go, 핵심 근거 1개

## 1. 환경
- 머신, OS, Python, laya/torch/transformers 버전 (results/env/env_*.json)
- 체크포인트 revision, 업스트림 커밋 4aa6761
- 디바이스 역할: CPU fp32 = 품질 기준, MPS = 레이턴시 (parity run_id)

## 2. 트랙별 결과
### Track A 재현 | 세트 | 지표 | 측정 | upstream | run_id |
### Track B 한국어 품질 | 세트 | 체크포인트 | 지표 | 값 | majority | run_id |
### Track C 견고성 | 프로브 | 값 | upstream 참고 | run_id |
### Track D 성능 | 구성 | p50 | p95 | 처리량 | run_id |
### Track E 캘리브레이션 | 버킷 | ECE 전/후 | coverage@acc | run_id |
### Track F 베이스라인 | 베이스라인 | 지표 | 값 | laya 대비 | run_id |

## 3. 가설 판정
| 가설 | 판정 (지지/기각/미결) | 근거 run_id | 한 줄 해석 |
|---|---|---|---|
| H1 | | | |
| ... H10 | | | |

## 4. Go/No-Go 매트릭스
00_README.md §6 의 기준표를 복사해 각 기준에 측정값·판정·run_id 를 채운다.

## 5. 한계와 주의
- 정밀도: MPS fp16(5행 이상) 과 CPU fp32 의 차이 (parity 결과)
- 표본 크기: n=100 에서 정확도 0.5 근처의 95 % 신뢰구간은 약 ±0.10. 단일 수치 비교 대신 bootstrap CI 또는 같은 항목에 대한 paired test(업스트림은 McNemar 를 썼다. 출처: research/README.md "Headline findings")
- 데이터 유출 가능성: 업스트림 training mix 에 포함된 소스 여부 (BENCHMARKS.md §Themes 의 held out 표기)
- 옵션 순서·문구 민감도 (Track C 수치)

## 6. 재현 방법
- 02 문서 §2 ~ §3 를 마친 뒤 실행할 명령 목록(run_id 순)

## 7. 부록
- run_id 전체 목록과 파일 경로
- ADR 목록
```

**대시보드.** `results/dashboard/index.html` 은 REPORT.md 와 같은 결과 JSON 에서 `scripts/build_dashboard.py` 가 생성한다(`03_benchmark_plan.md` §12 항목 11). 가설 판정은 `results/verdicts.json`, Go/No-Go 는 `results/go_no_go.json` 에만 기록하고, REPORT.md 의 §3·§4 는 그 두 파일을 옮겨 적는다. 같은 판정을 두 곳에 손으로 따로 적지 않는다. 항목 형식:

```json
{"H1": {"verdict": "지지", "run_ids": ["20261010-0930_multilingual_ko_massive20"], "note": "ko 0.47 재현, en 0.71"}}
```

```json
{"G0": {"value": 0.47, "pass": true, "run_ids": ["20261010-0930_multilingual_ko_massive20"]}, "G5": {"value": null, "pass": null, "run_ids": []}}
```

`pass: null` 은 "아직 측정 안 됨" 이고 대시보드는 그 칸을 회색으로 둔다. `build_dashboard.py` 가 리포트 JSON 에서 계산할 수 있는 G 항목은 스크립트가 채우고, 나머지는 손으로 채운다.

---

## 3. 결정 기록 (ADR-lite)

파일: `docs/decisions/ADR-<nnn>-<slug>.md`. 트레이드오프가 있는 선택(디바이스 역할, baseline 갱신, 데이터셋 교체, PoC 시나리오 확정, 스코프 축소)마다 하나.

```markdown
# ADR-<nnn>: <제목>

- 날짜: YYYY-MM-DD
- 상태: 제안 / 채택 / 폐기 / 대체됨(ADR-<n>)
- 관련: 트랙/phase, 가설 H<n>, run_id

## 맥락
어떤 측정·제약이 이 결정을 요구했는가. 숫자는 run_id 와 함께.

## 선택지
| 선택지 | 장점 | 단점 / 비용 | 되돌리기 난이도 |
|---|---|---|---|
| A | | | |
| B | | | |

## 결정
한 문장.

## 근거
왜 이 선택지가 다른 것보다 나은가. 가정이 있으면 명시.

## 결과 / 후속
- 바뀌는 문서·스크립트
- 재검토 트리거(어떤 수치가 나오면 다시 본다)
```

---

## 4. 라벨 정책 문서 (Label Policy)

파일: `data/handwritten/<set>_label_policy_v<n>.md` (예: `data/handwritten/poc_triage_label_policy_v1.md`, 04_korean_evalset_spec.md §5.8). 손으로 라벨링하는 PoC 세트(`ko_poc_triage_v1.jsonl`, 정의는 `04_korean_evalset_spec.md`)마다 모델을 돌리기 **전에** 작성하고 해시를 고정한다. 업스트림의 스페인어·중국어 커뮤니티 벤치가 같은 원칙("label policy fixed before any model ran")을 썼다 (출처: README.md "What's new in 0.3.23" Research 항목, research/benchmarks/zh_short_commands/README.md).

```markdown
# Label Policy: <set> v<n>

## 태스크 정의
- 입력 단위(문장/티켓/이메일), 질문 id 와 type (choice / score / noul)
- 결정이 쓰이는 맥락(어떤 액션으로 이어지는가)

## 라벨 집합
| 라벨 | 포함 기준 | 제외 기준 | 경계 예시 1 | 경계 예시 2 |
|---|---|---|---|---|
| <label_a> | | | | |
| <label_b> | | | | |
| other / unknown | 위 어느 것에도 확실히 속하지 않음 | | | |

## 모호 케이스 규칙
- 둘 이상 해당: 우선순위 <a> > <b> > ... (이유)
- 정보 부족: `unknown` 버킷. 정확도 계산에서 제외하지 않고 별도 슬라이스(tag=ambiguous)로 보고
- 부정문·조건문·인용문 처리 규칙 (01_laya_analysis.md 의 negation 한계와 연결)
- score: 레벨 경계를 예시로 고정. expected 는 0 기반 레벨 인덱스(laya-evals 규약. 출처: research/evals/fixture.jsonl, laya/evals.py ScoreMAE)

## 라벨링 절차
- 라벨러 2인 독립 라벨 → 불일치 목록 → adjudication 기록(최종 라벨, 이유)
- 라벨러 간 일치율(Cohen's kappa) 기록. 0.6 미만이면 기준을 고치고 재라벨
- 라벨러는 모델 출력을 보지 않는다

## 고정
- 모델 실행 전 해시: `shasum -a 256 data/evals/<set>.jsonl` → <sha>
- 이 정책 문서의 sha256 을 `data/evals/MANIFEST.json` 의 `label_policy_sha256` 에 기록(04_korean_evalset_spec.md §6)
- `laya-evals validate data/evals/<set>.jsonl` 통과 여부
- 고정 일시, 담당

## 변경 이력
| 버전 | 날짜 | 변경 | 영향 받는 run_id |
|---|---|---|---|
| v1 | | 최초 | |
```

고정 뒤 라벨을 고치면 버전을 올리고(`v2`) 기존 run 은 그대로 둔다. `questions_sha256` 가 바뀌는 질문 문구 변경도 새 실험이다 (출처: docs/evals.md "Run identity").

---

## 5. 체크리스트

**벤치 실행 전**
- [ ] `source env.sh` 했고 `echo $LAYA_MODELS_DIR $LAYA_REVISION` 이 기대값이다(`LAYA_MODELS` 는 비어 있어야 한다, 02 §2.8)
- [ ] `HF_HUB_OFFLINE` 상태를 의도대로 두었다(다운로드 필요 시 unset)
- [ ] 최신 `results/env/env_*.json` 이 현재 패키지·스레드 설정과 일치한다(아니면 재생성)
- [ ] warm-up 횟수와 측정 횟수를 정했고 Run Card 에 적었다
- [ ] 다른 부하 프로세스(브라우저 다수 탭, 다른 학습, Docker)를 종료했다
- [ ] 전원 어댑터 연결, 저전력 모드 해제. Apple silicon 은 열·전원 상태에 따라 클럭이 변하므로 긴 레이턴시 스윕은 식힌 뒤 같은 조건에서 돈다
- [ ] 데이터셋 해시가 라벨 정책의 고정 해시와 같다(`shasum -a 256`)
- [ ] Run Card 를 먼저 만들었다(목적·가설·명령어까지)

**실행 후**
- [ ] `.json` 과 `.md` 가 `results/<track>/` 에 저장됐다
- [ ] Run Card 의 결과 표와 해시 두 값을 리포트 JSON 에서 채웠다
- [ ] upstream 참고치와 차이를 적고, 임계 이상 차이는 원인 후보를 적었다
- [ ] 경고·fallback·이상 현상을 기록했다
- [ ] `results/REPORT.md` 의 해당 트랙 표와 가설 판정표를 갱신했다
- [ ] `python scripts/build_dashboard.py` 로 대시보드를 재생성하고 바뀐 칸을 확인했다
- [ ] 커밋했다(`results/`, `docs/`, `scripts/` 변경)

**PoC 단계 전환 전**
- [ ] 이전 phase 의 acceptance(05_poc_plan.md) 를 수치로 충족했고 run_id 가 있다
- [ ] 미충족 항목이 있으면 ADR 로 스코프 조정을 기록했다
- [ ] 다음 phase 가 의존하는 산출물(데이터셋, 질문 스키마, 임계값)이 고정·해시되어 있다

---

## 열린 질문 / 가정

1. **가정**: Run Card 는 `laya-evals` 리포트 JSON 의 `config` 블록(`revisions`, `dataset_sha256`, `questions_sha256`, `thresholds`, `timing`)이 존재한다는 전제로 쓰였다. 우리 자체 스크립트(Track C/D) 출력에는 같은 키를 같은 이름으로 넣는다.
2. **열린 질문**: 라벨러 2인을 확보할 수 없을 때의 대안. 1인 라벨 + 일주일 뒤 자기 재라벨(intra-rater) 로 대체하고 kappa 를 같은 칸에 적는 방식을 임시안으로 둔다.
3. **열린 질문**: REPORT.md 의 Go/No-Go 기준표는 `00_README.md` §6 을 따른다. 그 문서가 기준을 바꾸면 §2 템플릿의 "4. Go/No-Go 매트릭스" 절은 수정 없이 참조만 유지한다.
4. **가정**: 레이턴시는 이 머신 안에서만 비교한다. 업스트림 T4/EPYC 수치는 리포트 §5 에 맥락으로만 인용한다.

[English](06_templates.md) | **한국어**
