# 02. 환경 구성

**목적**: 이 머신(Apple M4 Pro)에서 laya 0.3.23 을 재현 가능한 상태로 설치하고, 벤치마크·PoC 가 공유하는 디렉토리 레이아웃·환경 변수·스모크 테스트·기록 규약을 고정한다.
**선행 문서**: `00_README.md`(진행 순서), `01_laya_analysis.md`(무엇을 측정하는지).
**산출물**: `.venv/`, `third_party/laya` @ `4aa6761`, `models/` 심링크 3개(앞의 세 항목은 공개 저장소에는 포함하지 않음), `env.sh`, `results/env/env_*.json`, `results/env/smoke_*.{json,md}`.

모든 명령은 프로젝트 루트 `.` 를 cwd 로 가정한다. 각 단계는 [단계 → 검증] 쌍이며, 검증이 통과하지 않으면 다음 단계로 가지 않는다.

---

## 1. 대상 머신과 제약

| 항목 | 값 | 벤치마크·PoC 에 미치는 영향 |
|---|---|---|
| SoC | Apple M4 Pro, CPU 14코어(성능 10 + 효율 4), GPU 20코어, Metal 4 | CPU 레퍼런스는 intra-op 10 스레드로 pin. GPU 는 MPS 백엔드만 가능 |
| 메모리 | 48 GB 통합 메모리 | 3개 체크포인트 동시 상주 가능. safetensors 가 421M 파라미터에 842.6 MB 이므로 2 byte/param 저장(bf16 계열)이고 CPU/MPS 에서는 fp32 로 돌아 체크포인트당 약 1.3 \~ 1.7 GB 로 추정. 업스트림은 5개 체크포인트 동시 상주 시 최대 RSS 9.3 GiB 를 기록 (출처: BENCHMARKS.md §Server CPU) |
| OS | macOS 26.6.2 (Darwin 25.6.0) | Docker 는 Linux VM 위에서 돌아 MPS 가 전달되지 않음. 컨테이너 경로는 CPU 전용 (출처: docs/docker.md "Apple MPS ... are outside this quickstart") |
| Python | Homebrew 3.11.15 / 3.12.12 / 3.14.5, 기본 `python3` = 3.14 | **3.12 를 쓴다.** torch 2.14.1 의 `cp312 macosx_14_0_arm64` 휠이 확인됐고, 3.14 는 업스트림이 Windows 에서 모델 생성 크래시(#123)를 겪은 이력이 있다 (출처: README.md "Installation details") |
| 도구 | uv 0.9.26, pipx 1.8.0, Docker 28.5.1, node 22.23.2, gh 2.85.0, hf 1.18.0 | `huggingface-cli` 는 deprecated 로 동작하지 않으며 `hf` 를 쓴다(로컬 확인). conda 없음 |
| 디스크 | 여유 84 GB, `~/.cache/huggingface` 가 이미 99 GB(다른 프로젝트) | 체크포인트 2.37 GB 추가는 문제 없음. 캐시를 옮기려면 `HF_HOME` (§5.5) |
| 가속 경로 | CUDA 없음 | `laya[fast]`(TileLang) 불가, `compile=True` 의 CUDA graph 이점 없음, bf16 autocast 경로 없음. MPS 는 5행 이상 호출에서만 fp16 autocast (출처: README.md "Automated Confidence Gating") |

업스트림 공개 레이턴시(T4, GB10, EPYC, Ryzen)는 이 머신을 예측하지 못한다. "The T4 figures do not predict CPU or cold-load time" (출처: docs/benchmarks.md). 따라서 속도 수치는 전부 자체 측정하고, 정확도·ECE 만 업스트림 수치와 비교한다(CPU fp32 는 결정적이므로 수치가 일치해야 한다. 근거는 §3.3).

---

## 2. 설치 [단계 → 검증]

### 2.1 디렉토리와 버전 관리

```bash
mkdir -p docs third_party models data/raw data/evals data/handwritten scripts results/env poc
git init                                     # 선택. 결과·문서·스크립트를 diff 로 남기기 위함
cat > .gitignore <<'EOF'
.venv/
.env
models/
third_party/
data/raw/
__pycache__/
*.pyc
.DS_Store
EOF
```

`third_party/`·`models/`·`data/raw/` 는 재생성 가능하므로 커밋하지 않는다. `data/evals/`(우리 JSONL), `results/`(리포트 JSON·MD), `scripts/`, `docs/` 는 커밋한다. 체크포인트와 업스트림 커밋은 이 문서에 SHA 로 고정되어 있으므로 서브모듈은 쓰지 않는다.

→ **검증**: `ls -d docs third_party models data/evals data/handwritten scripts results/env poc` 가 8개 디렉토리를 출력한다.

### 2.2 가상환경 (Python 3.12)

```bash
uv venv --python 3.12 .venv
.venv/bin/python --version
```

→ **검증**: `Python 3.12.x` 가 출력된다. 3.14 가 나오면 `--python 3.12` 가 Homebrew 3.12 를 찾지 못한 것이므로 `uv venv --python /opt/homebrew/bin/python3.12 .venv` 로 재시도.

### 2.3 패키지 설치

```bash
uv pip install --python .venv/bin/python \
  "laya[serve,onnx,structured]==0.3.23" \
  datasets pandas scikit-learn psutil matplotlib
```

`serve` = laya-serve(FastAPI/uvicorn), `onnx` = ONNX Runtime + onnxscript(export), `structured` = pydantic (출처: pyproject.toml `[project.optional-dependencies]`). `datasets`·`pandas` 는 업스트림 research 스크립트가 import 하며 laya 의존성에 없다 (출처: research/scripts/bench_local.py:165, bench_apps.py:79). `scikit-learn` 은 베이스라인·bootstrap, `psutil` 은 메모리 측정(`bench_length_batching.py --memory-mode`), `matplotlib` 은 결과 플롯용이다.

조사 시점 PyPI 최신: torch 2.14.1, transformers 5.18.0, onnxruntime 1.30.0. laya 의 하한은 torch>=2.0, transformers>=4.48, huggingface_hub>=0.20, numpy>=1.20, safetensors>=0.4 (출처: pyproject.toml). 실제 resolve 된 버전은 2.10 에서 기록한다.

→ **검증**: 설치가 에러 없이 끝나고 `uv pip list --python .venv/bin/python | grep -E '^(laya|torch|transformers|onnxruntime|datasets) '` 에 5줄이 보인다.

### 2.4 버전 확인

```bash
.venv/bin/python -I -c "import laya; print(laya.__version__)"
```

`-I` 는 현재 디렉토리를 import 경로에서 빼 로컬 소스가 설치 누락을 가리는 일을 막는다 (출처: README.md "Installation details").

→ **검증**: `0.3.23` 이 출력된다. 체크포인트는 내려받지 않는다.

### 2.5 업스트림 소스 고정 (research 스크립트·예제용)

```bash
git clone https://github.com/NandhaKishorM/laya.git third_party/laya
git -C third_party/laya checkout 4aa6761be8173de4ce6d92c31b3e40b6eaf59a7c
git -C third_party/laya log -1 --format='%H %cd'
```

전체 clone 이 가장 단순하다. 용량을 아끼려면 `git clone --filter=blob:none ...` 뒤에 같은 checkout 을 해도 된다(`--depth 1` 은 임의 SHA checkout 이 불가). 이 커밋은 PyPI 0.3.23 과 같은 날(2026-10-01)의 `main` 이며, 패키지 코드는 `.venv` 의 PyPI 배포본을 쓰고 체크아웃은 `research/`, `examples/`, `verify/`, `scripts/` 만 쓴다. 두 소스가 어긋나면 안 되므로 `third_party/laya` 를 `pip install -e` 하지 않는다.

→ **검증**: 출력 첫 토큰이 `4aa6761be8173de4ce6d92c31b3e40b6eaf59a7c` 이고 날짜가 `Oct 1 2026` 이다.

### 2.6 체크포인트 다운로드 (revision 고정)

```bash
hf download convaiinnovations/laya --revision 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 --quiet \
  | tee results/env/snapshot_path.txt
```

`--quiet` 는 필수다. hf 1.18 은 출력 모드에 따라 경로 앞에 `path=` 또는 `  path:` 접두어를 붙이고(agent 모드·human 모드), 경로만 그대로 내는 것은 `--quiet` 뿐이다(huggingface_hub/cli/_output.py). 접두어가 붙은 채로 2.7 로 가면 깨진 심링크가 만들어진다(Phase 0 실행에서 확인, 2026-10-02).

번들 리포 하나에 세 체크포인트가 들어 있다: 루트 = english(`model.safetensors` 842.6 MB), `multilingual/`(643.8 MB + `tokenizer.json` 34.4 MB), `typed-decisions/`(842.6 MB), 합계 2.37 GB (HF API `?blobs=true` 조회). `55cf4c4...` 는 `laya/revisions.py` 의 `PINNED_REVISIONS["convaiinnovations/laya"]` 와 같고, 업스트림 EPYC 측정이 쓴 revision 이기도 하다 (출처: BENCHMARKS.md §Server CPU). 독립 리포의 pin 은 `laya-multilingual` = `e4e9ddf21a7b1903b7acffd8814ad4307bf63a67`, `laya-typed-decisions` = `1a793eb568e6718f15941d08f85432581df534e3` 이지만 우리는 번들만 쓴다.

→ **검증**: 마지막 줄이 `.../hub/models--convaiinnovations--laya/snapshots/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` 이고, `du -shL "$(tail -1 results/env/snapshot_path.txt)"` 가 약 2.4 GB 다.

### 2.7 `models/` 심링크

```bash
SNAP="$(tail -1 results/env/snapshot_path.txt)"
ln -sfn "$SNAP"                 models/laya
ln -sfn "$SNAP/multilingual"    models/laya-multilingual
ln -sfn "$SNAP/typed-decisions" models/laya-typed-decisions
ln -sfn ../../models            third_party/laya/models
ls -l models/ third_party/laya/models
```

`laya.load(path)` 는 디렉토리에서 `rl_agent_config.json`, `model.safetensors`, `tokenizer/`, `encoder/` 만 읽으므로 (출처: laya/agent.py:577-619) 루트에 `multilingual/` 등 하위 디렉토리가 있어도 무해하다. 업스트림 research 스크립트는 `LAYA_MODELS` 아래 `laya/`, `laya-multilingual/`, `laya-typed-decisions/` 를 기대하고 (출처: research/README.md "Running the harnesses"), `examples/_common.py:42-51` 과 `examples/01_first_call_minimal.py` 는 체크아웃 안의 `models/laya` 를 찾는다. 두 경로를 모두 같은 스냅샷으로 묶었으므로 다운로드는 한 번이고, `Router()` 가 Hub 캐시에서 읽는 파일과도 동일 바이트다.

→ **검증**: `for d in models/*; do test -f "$d/model.safetensors" && test -f "$d/rl_agent_config.json" && echo "ok $d"; done` 이 `ok` 3줄을 낸다.

### 2.8 `env.sh`

```bash
cat > env.sh <<'EOF'
# 프로젝트 루트에서:  source env.sh
export PROJECT_ROOT="$PWD"
export USE_TF=0                               # transformers 의 TF 탐지로 인한 abseil deadlock 회피 (research/README.md)
export USE_TORCH=1
export TOKENIZERS_PARALLELISM=false
export LAYA_MODELS_DIR="$PROJECT_ROOT/models" # research 스크립트용 체크포인트 루트. LAYA_MODELS 자체는 export하지 않는다: laya-serve가 같은 이름을 체크포인트 이름 목록으로 읽기 때문(laya/serve.py:667-668). research 스크립트는 LAYA_MODELS="$LAYA_MODELS_DIR" 를 인라인으로 준다(§2.9)
export LAYA_REVISION=reviewed                 # Hub 로드를 PINNED_REVISIONS 로 pin (laya/revisions.py). 로컬 경로 로드에는 영향 없음
export OMP_NUM_THREADS=10                     # 성능 코어 수
# export HF_HUB_OFFLINE=1                     # 체크포인트·데이터셋 다운로드가 모두 끝난 뒤에만. 데이터셋 받을 때는 unset
# export LAYA_MPS_AMP_MIN_ROWS=100000         # parity 점검용: MPS 를 fp32 로 강제 (기본 5 = 5행 이상 fp16 autocast)
# export LAYA_CPU_AMP=bf16                    # 선택: CPU bf16. 기본 fp32 가 레퍼런스
# export LAYA_DEFAULT_MODEL=multilingual      # 언어 증거 없는 라틴 문자 텍스트의 라우팅 fallback. 순수 한글은 항상 감지되지만 라틴 문자가 다수인 혼합문과 영어 래퍼 속 짧은 한국어는 english로 갈 수 있다(docs/07 §4). PoC는 lang='ko'를 명시한다
EOF
source env.sh
```

`LAYA_REVISION=reviewed` 는 `Router()`·`laya-evals` 가 번들 리포를 로드할 때 `55cf4c4` 로 해석되며(캐시 히트), `models/...` 같은 로컬 경로 로드에는 적용되지 않는다 (출처: laya/revisions.py `resolve_revision`). 순수 한글은 `laya/lang.py:43` 의 `hangul` 스크립트 범위로 감지되어 `LAYA_DEFAULT_MODEL` 과 무관하게 multilingual 로 가지만, 라틴 문자가 다수인 혼합문(예: "Stripe webhook이 timeout 나요")과 영어 래퍼 속 10음절 미만 한국어는 english 로 갈 수 있다 (`07_korean_support_audit.md` §4, 46건 배터리). PoC 는 한국어 채널에 `lang="ko"` 를 명시한다.

→ **검증**: `source env.sh && echo "$LAYA_MODELS_DIR" && .venv/bin/python -c "import os; print(os.environ['LAYA_REVISION'], os.environ.get('LAYA_MODELS'))"` 가 프로젝트 경로, `reviewed`, `None` 을 출력한다(`LAYA_MODELS` 는 비어 있어야 한다).

### 2.9 research 스크립트 의존성 확인

```bash
.venv/bin/python -c "import datasets, pandas, pyarrow, psutil, sklearn; print('research deps ok')"
```

`bench_local.py` Part B 는 체크아웃에 없는 로컬 parquet(`typed-decisions/all/...`)을 기대하므로 (출처: research/scripts/bench_local.py `build_typed_decisions`) 항상 `--skip-b` 로 Part A 만 돌린다. 51개 언어 전체는 CPU 에서 수 시간이 걸린다.

```bash
# 참고용 전체 재현 명령. 실제 ko 전용 실행 설계는 03_benchmark_plan.md Track A 와 04_korean_evalset_spec.md 에 있다.
LAYA_MODELS="$LAYA_MODELS_DIR" USE_TF=0 .venv/bin/python third_party/laya/research/scripts/bench_local.py --langs 0 --per-lang 100 --skip-b
```

`bench_local.py` 는 언어를 이름으로 고르는 옵션이 없고 정렬된 목록을 `--langs N` 으로 자를 뿐이다 (출처: research/scripts/bench_local.py:314-316). ko 만 돌리는 방법은 03/04 문서가 정한다.

→ **검증**: `research deps ok` 출력.

### 2.10 환경 기록 스크립트 `scripts/env_report.py`

모든 실행이 참조할 환경 스냅샷을 JSON 으로 남긴다. 사양:

```python
# scripts/env_report.py  --  .venv/bin/python scripts/env_report.py [data/evals/*.jsonl ...]
import hashlib, json, os, platform, sys, time
os.environ.setdefault("USE_TF", "0")
import torch, transformers, laya
from laya.revisions import snapshot_revision
try:
    import onnxruntime; ort = onnxruntime.__version__
except ImportError:
    ort = None

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

rec = {
    "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "platform": platform.platform(), "machine": platform.machine(),
    "python": sys.version.split()[0],
    "versions": {"laya": laya.__version__, "torch": torch.__version__,
                 "transformers": transformers.__version__, "onnxruntime": ort},
    "mps_available": torch.backends.mps.is_available(),
    "torch_threads": torch.get_num_threads(), "torch_interop_threads": torch.get_num_interop_threads(),
    "env": {k: os.environ.get(k) for k in ("LAYA_MODELS_DIR", "LAYA_MODELS", "LAYA_REVISION", "OMP_NUM_THREADS",
            "HF_HUB_OFFLINE", "LAYA_MPS_AMP_MIN_ROWS", "LAYA_CPU_AMP", "LAYA_DEFAULT_MODEL")},
    # snapshot_revision 은 realpath 가 snapshots/<sha> 로 끝날 때만 sha 를 돌려준다. models/laya 만 그 모양이고
    # 두 하위 폴더는 snapshots/<sha>/multilingual 꼴이라 부모 디렉토리로 다시 묻는다. 셋은 같은 번들 sha 를 공유한다.
    "checkpoints": {n: {"realpath": os.path.realpath(f"models/{n}"),
                        "snapshot_sha": snapshot_revision(os.path.realpath(f"models/{n}"))
                                        or snapshot_revision(os.path.dirname(os.path.realpath(f"models/{n}"))),
                        "weights_sha256": sha256(f"models/{n}/model.safetensors")}
                    for n in ("laya", "laya-multilingual", "laya-typed-decisions")},
    "datasets": {p: sha256(p) for p in sys.argv[1:]},
}
out = f"results/env/env_{time.strftime('%Y%m%d-%H%M')}.json"
json.dump(rec, open(out, "w"), indent=2, ensure_ascii=False)
print(out)
```

`snapshot_revision` 은 심링크를 realpath 로 풀어 마지막 디렉토리가 `snapshots/<sha>` 일 때만 sha 를 돌려준다 (출처: laya/revisions.py `snapshot_revision`). `multilingual/`·`typed-decisions/` 하위 경로는 `snapshots/<sha>/<sub>` 이므로 그대로는 `None` 이 나오고, 위 코드처럼 부모 디렉토리로 다시 물어 같은 번들 sha(`55cf4c4...`)를 기록한다. 세 체크포인트의 `snapshot_sha` 는 반드시 같아야 한다.

```bash
.venv/bin/python scripts/env_report.py
```

→ **검증**: `results/env/env_<YYYYMMDD-HHMM>.json` 경로가 출력되고, 파일 안 `checkpoints.laya.snapshot_sha` 가 `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`, `versions.laya` 가 `0.3.23`, `mps_available` 이 `true` 다.

---

## 3. 스모크 테스트 [단계 → 검증]

실행 전 `source env.sh`. `HF_HUB_OFFLINE` 은 아직 설정하지 않는다(`laya-evals` 가 번들 리포 메타데이터를 조회할 수 있어야 한다. 3.3 통과 뒤 설정해도 된다).

### 3.1 라우팅만 (모델 로드 없음)

```bash
.venv/bin/laya "결제가 두 번 됐어요, 환불해주세요"
```

라우팅은 체크포인트를 내려받지 않고 밀리초에 끝난다 (출처: README.md "Command line").

→ **검증**: 출력에 `model` 이 `multilingual` 이고 `reason` 이 non-Latin script / hangul 을 언급한다. `english` 가 나오면 `laya/lang.py` 감지가 깨진 것이므로 중단.

### 3.2 프리셋 예측 (CLI)

```bash
.venv/bin/laya "결제가 두 번 됐어요, 환불해주세요" --preset triage        # --preset 이 --predict 를 포함한다
```

`triage` 프리셋은 상태의 `message` 필드를 읽도록 쓰여 있고 CLI 가 텍스트를 그 키 아래에 넣는다 (출처: laya/presets.py `state_field`, laya/cli.py:52). 2.6 을 마쳤으면 다운로드 없이 캐시에서 로드한다.

→ **검증**: `intent`, `is_urgent`, `frustration`, `refund_requested`, `churn_risk` 5줄이 출력되고(`frustration` 은 확률이 아니라 score 기대 레벨, 나머지는 확률) 라우팅이 multilingual 이다. 값은 Run Card 에 기록만 하고 여기서 판정하지 않는다(품질은 Track A 이후).

### 3.3 평가 하네스 fixture (정확도 수치 일치 확인)

```bash
.venv/bin/laya-evals validate third_party/laya/research/evals/fixture.jsonl
.venv/bin/laya-evals run third_party/laya/research/evals/fixture.jsonl --model english --device cpu \
  --json results/env/smoke_fixture_english_cpu.json --markdown results/env/smoke_fixture_english_cpu.md
```

→ **검증**: 아래 품질 지표가 **정확히** 일치해야 한다. 하네스는 고정 revision 에서 결정적이고 (출처: docs/evals.md "Baseline and CI gate"), 업스트림이 같은 fixture 를 English 체크포인트·CPU 로 돌린 수치가 공개되어 있다 (출처: docs/evals.md "Evaluating an ONNX export" 표).

| 지표 | 기대값 (upstream, torch Router, CPU) | 불일치 시 의심 지점 |
|---|---|---|
| `choice_accuracy` | 0.75 | revision 불일치, 다른 체크포인트로 라우팅 |
| `noul_accuracy` | 1.00 | 같음 |
| `score_mae` | 1.3418 | 정밀도(CPU bf16 이 켜졌는지 `LAYA_CPU_AMP`) |
| `ece` | 0.1596 | temperature 경고 **문구** 변화. english·typed-decisions 는 정상 상태에서도 `choice:11+=0.1006 -> 0.5` clamp 경고를 한 건 내므로(실측), 경고 유무가 아니라 문구가 같은지를 본다 |
| `mean_confidence` | 0.7304 | 같음 |
| `latency_p50_ms` | 116.8 (참고만, 이 머신 수치로 대체) | 비교 대상 아님 |

JSON 의 `config.revisions` 에 `55cf4c4...` 가, `config.laya_version` 에 `0.3.23` 이 기록되어 있어야 한다. 품질 지표가 어긋나면 환경 문제이므로 벤치마크로 넘어가지 않는다.

### 3.4 최소 예제 (로컬 경로 로드)

```bash
.venv/bin/python third_party/laya/examples/01_first_call_minimal.py
```

이 예제는 체크아웃의 `models/laya` 를 직접 로드한다 (출처: examples/01_first_call_minimal.py). 2.7 의 `third_party/laya/models` 링크가 없으면 실패한다.

→ **검증**: `P(refund requested) = 0.xxxx (confidence 0.xxxx)` 한 줄. 디바이스는 `device=None` 이라 MPS 가 선택되며 첫 호출이 10초 이상 걸릴 수 있다(§4).

### 3.5 CPU 와 MPS 가 같은 답을 내는지

```bash
.venv/bin/python third_party/laya/examples/35_device_selection_and_latency.py
```

→ **검증**: 스크립트가 두 디바이스의 중앙값 ms 를 출력하고 마지막 줄 `answers agree after JSON serialisation: True` 가 찍힌다. 이 스크립트는 assert 하지 않고 출력만 하므로(exit 는 항상 0) 그 줄의 `True` 를 직접 확인한다(examples/35_device_selection_and_latency.py:76). `False` 면 §4 의 parity 절차로 원인을 분리한다.

### 3.6 업스트림 스모크 스크립트

```bash
.venv/bin/python third_party/laya/verify/laya_smoke_test.py --models ./models --device cpu --repeat 3
.venv/bin/python third_party/laya/verify/laya_smoke_test.py --models ./models --device mps --repeat 3
```

라우팅, 세 체크포인트, 세 프리미티브, 프리셋을 실제 가중치로 돌리고 체크포인트별 레이턴시를 출력하며 실패 시 non-zero 로 끝난다 (출처: verify/laya_smoke_test.py 헤더). CUDA 를 요구하지 않는다. 주의: 이 스크립트는 `sys.path.insert(0, ROOT)` 로 체크아웃의 `laya/` 를 import 하므로(verify/laya_smoke_test.py:24) 결과는 PyPI 설치본이 아니라 4aa6761 체크아웃 코드에 대한 것이다. 두 코드는 세 파일(agent.py 별칭 로드, router.py `resolve_model_spec`, serve.py batch surrogate 가드)이 다르다(Phase 0 실행에서 확인).

→ **검증**: 두 실행 모두 exit code 0 (`echo $?`). 출력된 레이턴시는 Run Card 에 "참고" 로만 적는다(정식 측정은 Track D).

### 3.7 HTTP 서버 `laya-serve`

```bash
# 터미널 1. 여기의 LAYA_MODELS 는 laya-serve 의 의미(preload 할 체크포인트 이름 목록)다. env.sh 는 LAYA_MODELS 를 export 하지 않는다(§2.8)
LAYA_HOST=127.0.0.1 LAYA_PORT=8000 LAYA_MODELS=multilingual LAYA_DEVICE=mps LAYA_THREADS=10 .venv/bin/laya-serve
```

```bash
# 터미널 2
curl -s localhost:8000/health | python3 -m json.tool
curl -s localhost:8000/v1/systemone -H 'content-type: application/json' -d '{
  "state": {"body": "3월 요금이 두 번 결제됐어요. 중복 결제분 환불해주세요."},
  "questions": {"dept": {"type": "choice", "instructions": "Which team should handle `body`?",
                "criteria": {"billing": "refunds, invoices, payments", "technical": "bugs, outages", "other": "everything else"}}}
}' | python3 -m json.tool
```

`laya-serve` 는 `LAYA_MODELS` 를 쉼표로 나눈 체크포인트 이름 목록으로 읽고, 모르는 이름이면 설정 오류로 종료한다 (출처: laya/serve.py:667-668 및 모듈 docstring). research 스크립트가 같은 이름을 디렉토리 경로로 읽기 때문에 env.sh 는 `LAYA_MODELS_DIR` 만 export 하고 `LAYA_MODELS` 는 각 명령 줄에서 그 명령의 의미로 준다(§2.8, §2.9). `LAYA_PRELOAD` 기본값은 1 이다.

→ **검증**: `/health` 가 `status: ok`, `loaded` 에 `multilingual`, `revisions` 에 `55cf4c4...`, `device` 가 `mps` 를 담는다(`LAYA_API_KEY` 를 설정하지 않았으므로 내부 정보가 보인다. 출처: README.md "What's new in 0.3.23"). `/v1/systemone` 응답에 `answers.dept.choice`, `answers.dept.answer_confidence`, `routing.model == "multilingual"`, `usage.input_tokens` 가 있다.

### 3.8 웹 GUI 플레이그라운드

```bash
# 3.7 의 서버를 먼저 끈다. 둘 다 기본 포트 8000 이다
.venv/bin/python third_party/laya/examples/server.py --device mps --no-preload --port 8000
```

→ **검증**: 브라우저에서 `http://127.0.0.1:8000` 에 두 패널 플레이그라운드가 열리고 한국어 요청을 Ctrl+Enter 로 실행하면 분포와 confidence 가 보인다 (출처: README.md "Try it locally: web GUI + JSON API"). PoC 데모·질문 스키마 설계(05) 에 쓴다.

---

## 4. 디바이스·정밀도·스레드 설정

**MPS.**
- upstream 은 새 (batch, length) 형태의 첫 호출에 Metal 커널 컴파일로 약 13 초가 든다고 적었지만 (출처: examples/README.md "Before you start"), 이 머신(torch 2.14.1, macOS 26.6.2) 실측에서는 첫 MPS 호출이 0.17 s 로 재현되지 않았다 (`results/poc/P0_20261002.md`). 그래도 warm-up 은 유지한다. 모든 측정은 warm-up 1회 이상을 버리고 중앙값을 쓴다(`examples/_common.py:126` 의 `timed` 가 그 패턴이다).
- `agent.dtype` 은 autocast 타깃이라 MPS 에서는 `float16` 으로 보이지만, 호출 행 수가 `mps_amp_min_rows`(기본 5) 미만이면 fp32 로 돈다. 실제 정밀도는 `agent.dtype_for(rows)` 로 읽는다 (출처: README.md "Automated Confidence Gating", laya/agent.py:278-290). 질문 1 \~ 4 개짜리 호출은 fp32, 5개 이상·`predict_batch` 는 fp16 이라는 뜻이며, 레이턴시 표를 읽을 때 이 경계를 표기한다.
- `LAYA_MPS_AMP_MIN_ROWS=100000` 으로 MPS 전체를 fp32 로 강제할 수 있다. parity 점검과 "정밀도 때문에 답이 바뀌었나" 분리에만 쓴다.

**CPU (레퍼런스).**
- fp32 기본. 정확도·ECE 의 기준값은 항상 CPU fp32 로 뽑는다.
- 스레드: `torch.set_num_threads(10)` + `torch.set_num_interop_threads(1)`. 업스트림은 inter-op 를 1로 고정해 12배, intra-op 는 물리 코어 수 근처가 최적임을 측정했다 (출처: BENCHMARKS.md §Laptop CPU). `laya-serve` 는 `LAYA_THREADS=10`. 4/8/10/14 스레드 스윕은 Track D 에서 수행한다(`03_benchmark_plan.md`).

**디바이스 지정 방법.**

| 경로 | 지정 |
|---|---|
| SDK | `laya.load(path, device="cpu"|"mps")`, `Router(device=...)`. `None` 이면 CUDA → MPS → CPU 순 |
| `laya-evals run` | `--device cpu|mps` (`--onnx` 경로에서는 무시됨. 출처: docs/evals.md) |
| `laya-serve` | `LAYA_DEVICE=cpu|mps` |
| `examples/*.py` | `_common.load(name, device=...)`, `server.py --device` |
| research 스크립트 | 대부분 `device="cpu"` 하드코딩(`bench_local.py:152`). MPS 로 돌리려면 우리 스크립트에서 감싼다 |

**parity 점검 절차** (`python scripts/metrics_extra.py parity <cpu_report.json> <mps_report.json>`, 서브커맨드 방식. 03_benchmark_plan.md §3.8·A5·C9. Track D 사전 단계).
1. 입력: 같은 JSONL(04 문서의 `ko_poc_triage_v1` 또는 질문을 공유하는 `ko_klue_ynat_7`)을 `laya-evals run --model multilingual --json ...` 으로 두 번 돌린 리포트. 한 번은 `--device cpu`, 한 번은 `--device mps`.
2. `metrics_extra.py --parity` 가 두 리포트의 per-case `answer`(argmax 와 `probabilities`, laya/evals.py:728-744)를 케이스 단위로 짝지어 비교한다.
3. MPS 쪽은 두 번 돈다: (a) `LAYA_MPS_AMP_MIN_ROWS=100000`(MPS fp32) (b) 기본값(5행 이상 fp16, `--batch-size 16` 으로 fp16 경로를 밟게 함).
4. 지표: argmax flip 수, 전 옵션에 대한 max |Δp|.
5. 합격: (a) 에서 flip 0, max |Δp| ≤ 0.01. (b) 는 기록만 하되 업스트림 참고치와 비교한다: fp32 대비 bf16 은 최대 0.073, 864개 중 3개 flip, fp16 은 0.019 이내·flip 0 (출처: README.md "Automated Confidence Gating"; 방법론은 benchmarks/parity_fast.py 와 BENCHMARKS.md §GPU fast path "Same answers").
6. (a) 가 실패하면 MPS 를 레이턴시 측정에만 쓰고 모든 품질 수치는 CPU 로 뽑는다. 이는 우회가 아니라 디바이스별 역할 분리이며 Run Card 에 명시한다.

---

## 5. 선택 구성

### 5.1 ONNX export 와 INT8 (CPU 배포 시나리오)

```bash
mkdir -p models/onnx
.venv/bin/python third_party/laya/scripts/export_onnx.py --model models/laya-multilingual \
  --output models/onnx/laya-multilingual.onnx --quantize
.venv/bin/laya-evals run data/evals/<set>.jsonl --onnx models/onnx/laya-multilingual.int8.onnx \
  --model models/laya-multilingual --json results/D/<run-id>.json
```

`--quantize` 는 0.3.23 부터 per-tensor 가 기본이다. per-channel 은 결정 모델을 eager 대비 32 % 일치로 붕괴시켰다 (출처: README.md "What's new in 0.3.23" ONNX 항목). INT8 파일은 `--output` 옆에 `<stem>.int8.onnx` 로 쓰인다(`int8_output_path`: `laya.onnx` → `laya.int8.onnx`, 출처: scripts/export_onnx.py). `--onnx` 경로의 `--model` 은 Router 단축명이 아니라 export 원본의 경로·Hub id 여야 하고 `--device` 는 적용되지 않는다 (출처: docs/evals.md "Evaluating an ONNX export"). 업스트림 fixture 기준으로 fp32 export 는 torch 수치를 그대로 재현하고 int8 은 `score_mae` +0.009, `ece` +0.006 이동했다(같은 출처). 실제 측정은 Track D7(03_benchmark_plan.md).

→ **검증**: `.onnx` 와 `.int8.onnx` 두 파일이 생기고, fp32 export 의 `laya-evals` 품질 지표가 torch CPU 실행과 같다.

### 5.2 Docker (Linux CPU 배포 미러)

```bash
cd third_party/laya && docker compose run --build --rm laya; cd -
```

CPU 이미지, RAM 8 GB·디스크 10 GB 필요, 가중치는 named volume 에 남는다 (출처: docs/docker.md). 이 머신에서는 GPU 전달이 없으므로 "리눅스 CPU 서버에 올리면 어떻게 되나" 를 미리 보는 용도다. 서버 모드와 환경 변수 표는 docs/docker.md §Configuration.

→ **검증**: 샘플 요청의 JSON 이 `choice`/`score`/`noul` 답을 담아 출력된다.

### 5.3 LLM 베이스라인 API 키

```bash
cat > .env <<'EOF'
ANTHROPIC_API_KEY=sk-ant-...
EOF
set -a; source .env; set +a
```

`.env` 는 `.gitignore` 에 있다(2.1). 베이스라인 모델 id 는 `claude-haiku-4-5-20251001`, 호출 설계·비용 상한·프롬프트는 `03_benchmark_plan.md` 가 정한다. 실행 전 예산 상한(예: 요청 수 × 평균 토큰)을 Run Card 에 적고, 초과 시 중단한다.

→ **검증**: `.venv/bin/python -c "import os; print(bool(os.environ.get('ANTHROPIC_API_KEY')))"` 가 `True`.

### 5.4 CUDA 서버를 쓸 수 있는 경우

이 머신 밖의 NVIDIA 호스트에서 같은 벤치를 돌릴 때만 해당한다.
- `LAYA_DEVICE=cuda`, `LAYA_PRELOAD=1`. compute capability 8 이상에서는 체크포인트의 `amp_dtype`(세 체크포인트 모두 bf16)로 autocast 한다.
- bf16 은 fp32 대비 확률을 최대 0.073 움직이고 864개 argmax 중 3개를 뒤집었으며 fp16 은 0.019 이내·flip 0 이었으므로 `LAYA_CUDA_AMP=fp16` 을 기본 후보로 둔다 (출처: README.md "Automated Confidence Gating").
- `pip install laya[fast]` + `laya.load(..., fast=True)` 의 TileLang 경로, `compile=True` + `agent.warmup()` 은 CUDA 전용이다 (출처: README.md "GPU Fast Path", "Warm-up before serving").
- slim 이미지나 C 컴파일러 없는 호스트에서 `Failed to find C compiler` 가 나면 `TORCH_DISABLE_NATIVE_JIT=1` (출처: docs/docker.md "NVIDIA GPU / CUDA").

### 5.5 Hugging Face 캐시 위치

기존 `~/.cache/huggingface` 가 99 GB 이지만 다른 프로젝트 자산이므로 건드리지 않는다. 데이터셋만 프로젝트 안에 두고 싶으면 `export HF_HOME="$PWD/data/raw/hf"` 를 env.sh 에 추가하되, 그 경우 체크포인트도 그 아래에 다시 받히므로 2.6 \~ 2.7 을 그 설정으로 다시 한다(스냅샷 경로가 바뀐다). 업스트림도 체크아웃 내부 `HF_HOME` 을 권한다 (출처: research/README.md "Running the harnesses").

---

## 6. 트러블슈팅

| 증상 | 원인 | 조치 | 출처 |
|---|---|---|---|
| `ModuleNotFoundError: No module named 'laya'` | 설치한 인터프리터와 실행 인터프리터가 다름(기본 `python3` 는 3.14) | 항상 `.venv/bin/python`, `.venv/bin/laya*` 로 실행 | README.md "Installation details" |
| `Incompatible model: ... does not contain 'rl_agent_config.json'` | 리포 루트나 `third_party/laya` 를 모델 경로로 넘김 | `models/laya` 등 체크포인트 디렉토리를 넘긴다 | README.md 같은 절, laya/agent.py:577-580 |
| 첫 `--predict`·`Router()` 가 네트워크 오류 | 캐시 미스 상태에서 `HF_HUB_OFFLINE=1` | 변수 unset 후 2.6 재실행 | README.md "Command line" |
| `load_dataset` 실패 | `HF_HUB_OFFLINE=1` | 데이터셋 수집 중에는 unset | research/README.md |
| 모델 생성 중 멈춤(macOS) | TensorFlow 설치 시 abseil 런타임 deadlock | `USE_TF=0`(env.sh 에 포함) | research/README.md |
| `could not patch .../tokenizer_config.json` 경고 또는 PermissionError | `_fix_tokenizer_config` 가 스냅샷 디렉토리에 임시 파일을 쓰고 `os.replace` 함. 읽기 전용 마운트에서는 실패 | 쓰기 가능한 경로를 쓴다. 심링크된 HF 캐시 스냅샷은 쓰기 가능이라 정상 | laya/agent.py:56-108 |
| MPS 첫 호출이 10 초 이상 | Metal 커널 컴파일 | warm-up 후 측정. 형태(batch, length)가 바뀌면 다시 발생 | examples/README.md |
| torch 설치 실패·import 오류 | Python 3.14 환경 | 3.12 venv 로 재생성(2.2) | README.md "Windows + Python 3.14" 항목 |
| `laya-serve` 가 503 과 `Retry-After` 를 반환 | `LAYA_MAX_CONCURRENT` 초과 | 클라이언트 재시도, 동시성 조정 | README.md "What's new in 0.3.21" |
| `/health` 에 `loaded`·`revisions` 가 없음 | `LAYA_API_KEY` 가 설정되어 내부 정보가 bearer 뒤로 감 | `-H 'Authorization: Bearer <key>'` | README.md "What's new in 0.3.23" |
| `address already in use` :8000 | `laya-serve` 와 `examples/server.py` 동시 실행 | `LAYA_PORT` 또는 `--port` 변경 | README.md "Try it locally" |
| `laya-serve` 가 체크포인트 이름 오류로 즉시 종료 | 쉘에 `LAYA_MODELS=<경로>` 가 export 되어 있어 serve 가 이름 목록으로 해석(env.sh 는 export 하지 않지만 수동 export 시 발생) | `unset LAYA_MODELS` 또는 서버 실행 줄에 `LAYA_MODELS=multilingual` | laya/serve.py:667-668 |
| CPU 추론이 질문 1개에 수 초 | inter-op/intra-op 스레드 과점유 | `set_num_threads(10)`, `set_num_interop_threads(1)`, `LAYA_THREADS=10` | BENCHMARKS.md §Laptop CPU |
| MPS 에서 `agent.dtype` 가 `float16` 인데 fp32 를 기대 | `dtype` 는 autocast 타깃. 5행 미만은 fp32 | `agent.dtype_for(rows)` 로 확인, 필요 시 `LAYA_MPS_AMP_MIN_ROWS` | README.md "Automated Confidence Gating" |
| `huggingface-cli: deprecated and no longer works` | CLI 이름 변경 | `hf download ...` | 로컬 확인(hf 1.18.0) |
| `laya-evals run` 이 `baseline is not comparable: dataset_sha256` 로 실패 | 데이터셋 바이트가 baseline 과 다름 | 같은 파일로 재실행하거나 baseline 을 갱신하고 ADR 에 기록 | docs/evals.md "Baseline and CI gate" |

---

## 7. 환경 기록 규약

모든 벤치마크·PoC 실행은 다음을 남긴다. 양식은 `06_templates.md` §1 "실험 실행 기록 (Run Card)" 이다.

| 항목 | 출처 |
|---|---|
| `results/env/env_<YYYYMMDD-HHMM>.json` 경로 | 2.10 스크립트. 패키지 버전·스레드·`HF_HUB_OFFLINE` 등 env 가 바뀌면 다시 생성 |
| 체크포인트 revision | `laya-evals` 리포트의 `config.revisions`, 또는 env JSON 의 `checkpoints.*.snapshot_sha` |
| 데이터셋 정체성 | 리포트의 `config.dataset_sha256`, `config.questions_sha256` (출처: docs/evals.md "Run identity") |
| 디바이스·정밀도·스레드 | `--device`, `agent.dtype_for(rows)`, `torch.get_num_threads()` |
| 실행 명령 전체 | 복사 가능한 한 줄 |
| warm-up·반복 수 | 버린 호출 수, 측정 호출 수, 집계(중앙값/p95) |
| 결과 파일 | `results/<track>/<YYYYMMDD-HHMM>_<model>_<dataset>.json` 과 `.md` |
| 열·전원 상태 | 전원 연결 여부, 동시 실행 중이던 부하(`06_templates.md` §5 체크리스트) |

`laya-evals compare` 는 `*_ms` 지표를 tolerance 로 지정하지 않으면 무시하므로 레이턴시 노이즈가 baseline 비교를 깨지 않는다 (출처: docs/evals.md "Batching and timing"). 레이턴시 회귀는 별도 표로 비교한다.

---

## 열린 질문 / 가정

1. **가정**: `.venv` 의 PyPI 0.3.23 과 `third_party/laya` @ `4aa6761` 의 패키지 코드가 동일하다고 본다. 둘 다 2026-10-01 자이지만 바이트 동일성은 확인하지 않았다. 의심되면 `diff -r third_party/laya/laya .venv/lib/python3.12/site-packages/laya` 로 확인한다.
2. **가정**: 2.3 의 `uv pip install` 이 torch 2.14.1 arm64 휠을 선택한다. 다른 버전이 resolve 되면 2.10 의 기록으로 충분하며 강제 pin 은 하지 않는다. transformers 5.x 와 laya 0.3.23 의 조합은 업스트림 EPYC 측정(transformers 5.17.0)으로 검증되어 있다 (출처: BENCHMARKS.md §Server CPU).
3. **열린 질문**: MPS fp16(5행 이상) 과 CPU fp32 가 한국어 입력에서 argmax 를 뒤집는 빈도. §4 parity 결과에 따라 Track D 이후 품질 수치를 MPS 로도 뽑을지 결정한다.
4. **열린 질문**: 3.3 fixture 수치가 transformers 5.18.0 에서도 바이트 단위로 일치하는지. 소수점 넷째 자리 차이가 나면 tokenizer 패치 경고를 먼저 확인하고, 그래도 다르면 `04`/`03` 의 baseline 을 우리 환경 수치로 다시 잡는다(ADR 기록).
5. **가정**: ONNX·Docker·LLM 베이스라인·CUDA 는 선택이다. 기본 경로(§2 \~ §4)만으로 Track A \~ E 와 PoC Phase 1 \~ 2 를 진행할 수 있다.
6. **열린 질문**: 데이터셋 캐시를 기본 `~/.cache/huggingface` 에 둘지 `HF_HOME` 으로 분리할지. 기본값으로 시작하고, 디스크 여유가 20 GB 아래로 내려가면 §5.5 로 전환한다.

[English](02_environment_setup.md) | **한국어**
