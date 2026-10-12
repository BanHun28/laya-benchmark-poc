# 02. Environment setup

**Purpose**: Install laya 0.3.23 reproducibly on this machine (Apple M4 Pro), and pin down the directory layout, environment variables, smoke tests and recording conventions shared by the benchmark and the PoC.
**Prerequisite documents**: `00_README.md` (order of work), `01_laya_analysis.md` (what is measured).
**Outputs**: `.venv/`, `third_party/laya` @ `4aa6761`, 3 `models/` symlinks (the first three items are not included in the public repository), `env.sh`, `results/env/env_*.json`, `results/env/smoke_*.{json,md}`.

All commands assume the project root `.` as the cwd. Each step is a [step → verification] pair; if the verification does not pass, do not move on to the next step.

---

## 1. Target machine and constraints

| Item | Value | Impact on the benchmark·PoC |
|---|---|---|
| SoC | Apple M4 Pro, 14-core CPU (10 performance + 4 efficiency), 20-core GPU, Metal 4 | The CPU reference is pinned to 10 intra-op threads. The GPU is usable only through the MPS backend |
| Memory | 48 GB unified memory | All 3 checkpoints can be resident at once. The safetensors are 842.6 MB for 421M parameters, so they are stored at 2 bytes/param (bf16 family); on CPU/MPS they run in fp32, estimated at about 1.3-1.7 GB per checkpoint. Upstream recorded a maximum RSS of 9.3 GiB with 5 checkpoints resident at once (source: BENCHMARKS.md §Server CPU) |
| OS | macOS 26.6.2 (Darwin 25.6.0) | Docker runs on a Linux VM, so MPS is not passed through. The container path is CPU-only (source: docs/docker.md "Apple MPS ... are outside this quickstart") |
| Python | Homebrew 3.11.15 / 3.12.12 / 3.14.5, default `python3` = 3.14 | **Use 3.12.** The `cp312 macosx_14_0_arm64` wheel of torch 2.14.1 was confirmed, and with 3.14 upstream has a history of model-creation crashes on Windows (#123) (source: README.md "Installation details") |
| Tools | uv 0.9.26, pipx 1.8.0, Docker 28.5.1, node 22.23.2, gh 2.85.0, hf 1.18.0 | `huggingface-cli` is deprecated and does not work; use `hf` (checked locally). No conda |
| Disk | 84 GB free; `~/.cache/huggingface` already holds 99 GB (other projects) | Adding 2.37 GB of checkpoints is no problem. To move the cache, use `HF_HOME` (§5.5) |
| Acceleration path | No CUDA | `laya[fast]` (TileLang) unavailable, no CUDA graph benefit from `compile=True`, no bf16 autocast path. MPS uses fp16 autocast only for calls with 5 or more rows (source: README.md "Automated Confidence Gating") |

Upstream's published latencies (T4, GB10, EPYC, Ryzen) do not predict this machine. "The T4 figures do not predict CPU or cold-load time" (source: docs/benchmarks.md). So all speed numbers are measured by us, and only accuracy·ECE are compared with upstream's numbers (CPU fp32 is deterministic, so the numbers must match; the rationale is in §3.3).

---

## 2. Installation [step → verification]

### 2.1 Directories and version control

```bash
mkdir -p docs third_party models data/raw data/evals data/handwritten scripts results/env poc
git init                                     # Optional. To keep results·docs·scripts as diffs
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

`third_party/`·`models/`·`data/raw/` can be regenerated, so they are not committed. `data/evals/` (our JSONL), `results/` (report JSON·MD), `scripts/` and `docs/` are committed. The checkpoints and the upstream commit are pinned by SHA in this document, so no submodule is used.

→ **Verification**: `ls -d docs third_party models data/evals data/handwritten scripts results/env poc` prints 8 directories.

### 2.2 Virtual environment (Python 3.12)

```bash
uv venv --python 3.12 .venv
.venv/bin/python --version
```

→ **Verification**: `Python 3.12.x` is printed. If 3.14 appears, `--python 3.12` did not find Homebrew 3.12, so retry with `uv venv --python /opt/homebrew/bin/python3.12 .venv`.

### 2.3 Package installation

```bash
uv pip install --python .venv/bin/python \
  "laya[serve,onnx,structured]==0.3.23" \
  datasets pandas scikit-learn psutil matplotlib
```

`serve` = laya-serve (FastAPI/uvicorn), `onnx` = ONNX Runtime + onnxscript (export), `structured` = pydantic (source: pyproject.toml `[project.optional-dependencies]`). `datasets`·`pandas` are imported by upstream's research scripts and are not laya dependencies (source: research/scripts/bench_local.py:165, bench_apps.py:79). `scikit-learn` is for baselines·bootstrap, `psutil` for memory measurement (`bench_length_batching.py --memory-mode`), and `matplotlib` for plotting results.

Latest on PyPI at the time of the survey: torch 2.14.1, transformers 5.18.0, onnxruntime 1.30.0. laya's lower bounds are torch>=2.0, transformers>=4.48, huggingface_hub>=0.20, numpy>=1.20, safetensors>=0.4 (source: pyproject.toml). The versions actually resolved are recorded in 2.10.

→ **Verification**: The installation finishes without errors, and `uv pip list --python .venv/bin/python | grep -E '^(laya|torch|transformers|onnxruntime|datasets) '` shows 5 lines.

### 2.4 Version check

```bash
.venv/bin/python -I -c "import laya; print(laya.__version__)"
```

`-I` removes the current directory from the import path, which prevents local sources from masking a missing installation (source: README.md "Installation details").

→ **Verification**: `0.3.23` is printed. No checkpoint is downloaded.

### 2.5 Pinning the upstream source (for the research scripts·examples)

```bash
git clone https://github.com/NandhaKishorM/laya.git third_party/laya
git -C third_party/laya checkout 4aa6761be8173de4ce6d92c31b3e40b6eaf59a7c
git -C third_party/laya log -1 --format='%H %cd'
```

A full clone is simplest. To save space, `git clone --filter=blob:none ...` followed by the same checkout also works (`--depth 1` cannot check out an arbitrary SHA). This commit is `main` on the same day as PyPI 0.3.23 (2026-10-01); the package code comes from the PyPI distribution in `.venv`, and only `research/`, `examples/`, `verify/` and `scripts/` of the checkout are used. Since the two sources must not diverge, `third_party/laya` is not installed with `pip install -e`.

→ **Verification**: The first token of the output is `4aa6761be8173de4ce6d92c31b3e40b6eaf59a7c` and the date is `Oct 1 2026`.

### 2.6 Checkpoint download (pinned revision)

```bash
hf download convaiinnovations/laya --revision 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 --quiet \
  | tee results/env/snapshot_path.txt
```

`--quiet` is mandatory. Depending on the output mode, hf 1.18 prefixes the path with `path=` or `  path:` (agent mode·human mode), and only `--quiet` prints the bare path (huggingface_hub/cli/_output.py). Going on to 2.7 with the prefix still attached creates broken symlinks (confirmed in the Phase 0 run, 2026-10-02).

One bundle repo holds the three checkpoints: root = english (`model.safetensors` 842.6 MB), `multilingual/` (643.8 MB + `tokenizer.json` 34.4 MB), `typed-decisions/` (842.6 MB), 2.37 GB in total (HF API `?blobs=true` query). `55cf4c4...` equals `PINNED_REVISIONS["convaiinnovations/laya"]` in `laya/revisions.py` and is also the revision used by upstream's EPYC measurement (source: BENCHMARKS.md §Server CPU). The standalone repos are pinned at `laya-multilingual` = `e4e9ddf21a7b1903b7acffd8814ad4307bf63a67` and `laya-typed-decisions` = `1a793eb568e6718f15941d08f85432581df534e3`, but we use only the bundle.

→ **Verification**: The last line is `.../hub/models--convaiinnovations--laya/snapshots/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`, and `du -shL "$(tail -1 results/env/snapshot_path.txt)"` reports about 2.4 GB.

### 2.7 `models/` symlinks

```bash
SNAP="$(tail -1 results/env/snapshot_path.txt)"
ln -sfn "$SNAP"                 models/laya
ln -sfn "$SNAP/multilingual"    models/laya-multilingual
ln -sfn "$SNAP/typed-decisions" models/laya-typed-decisions
ln -sfn ../../models            third_party/laya/models
ls -l models/ third_party/laya/models
```

`laya.load(path)` reads only `rl_agent_config.json`, `model.safetensors`, `tokenizer/` and `encoder/` from the directory (source: laya/agent.py:577-619), so subdirectories such as `multilingual/` under the root are harmless. Upstream's research scripts expect `laya/`, `laya-multilingual/` and `laya-typed-decisions/` under `LAYA_MODELS` (source: research/README.md "Running the harnesses"), and `examples/_common.py:42-51` and `examples/01_first_call_minimal.py` look for `models/laya` inside the checkout. Both paths are tied to the same snapshot, so there is a single download, and the bytes are identical to the files `Router()` reads from the Hub cache.

→ **Verification**: `for d in models/*; do test -f "$d/model.safetensors" && test -f "$d/rl_agent_config.json" && echo "ok $d"; done` prints 3 `ok` lines.

### 2.8 `env.sh`

```bash
cat > env.sh <<'EOF'
# From the project root:  source env.sh
export PROJECT_ROOT="$PWD"
export USE_TF=0                               # avoids the abseil deadlock caused by transformers' TF detection (research/README.md)
export USE_TORCH=1
export TOKENIZERS_PARALLELISM=false
export LAYA_MODELS_DIR="$PROJECT_ROOT/models" # checkpoint root for the research scripts. LAYA_MODELS itself is not exported, because laya-serve reads the same name as a list of checkpoint names (laya/serve.py:667-668). The research scripts pass LAYA_MODELS="$LAYA_MODELS_DIR" inline (§2.9)
export LAYA_REVISION=reviewed                 # pins Hub loads to PINNED_REVISIONS (laya/revisions.py). No effect on local-path loads
export OMP_NUM_THREADS=10                     # number of performance cores
# export HF_HUB_OFFLINE=1                     # only after all checkpoint·dataset downloads are done. unset while downloading datasets
# export LAYA_MPS_AMP_MIN_ROWS=100000         # for parity checks: forces MPS to fp32 (default 5 = fp16 autocast for 5 or more rows)
# export LAYA_CPU_AMP=bf16                    # optional: CPU bf16. The default fp32 is the reference
# export LAYA_DEFAULT_MODEL=multilingual      # routing fallback for Latin-script text with no language evidence. Pure Hangul is always detected, but mixed text with mostly Latin letters and short Korean inside an English wrapper can go to english (docs/07 §4). The PoC sets lang='ko' explicitly
EOF
source env.sh
```

`LAYA_REVISION=reviewed` resolves to `55cf4c4` when `Router()`·`laya-evals` load the bundle repo (cache hit), and it does not apply to local-path loads such as `models/...` (source: laya/revisions.py `resolve_revision`). Pure Hangul is detected through the `hangul` script range in `laya/lang.py:43` and goes to multilingual regardless of `LAYA_DEFAULT_MODEL`, but mixed text with mostly Latin letters (e.g. "Stripe webhook이 timeout 나요") and Korean of fewer than 10 syllables inside an English wrapper can go to english (`07_korean_support_audit.md` §4, 46-case battery). The PoC sets `lang="ko"` explicitly for the Korean channel.

→ **Verification**: `source env.sh && echo "$LAYA_MODELS_DIR" && .venv/bin/python -c "import os; print(os.environ['LAYA_REVISION'], os.environ.get('LAYA_MODELS'))"` prints the project path, `reviewed` and `None` (`LAYA_MODELS` must be empty).

### 2.9 Checking the research-script dependencies

```bash
.venv/bin/python -c "import datasets, pandas, pyarrow, psutil, sklearn; print('research deps ok')"
```

`bench_local.py` Part B expects a local parquet (`typed-decisions/all/...`) that is not in the checkout (source: research/scripts/bench_local.py `build_typed_decisions`), so only Part A is ever run, with `--skip-b`. All 51 languages take several hours on CPU.

```bash
# Full reproduction command, for reference. The actual ko-only run design is in 03_benchmark_plan.md Track A and 04_korean_evalset_spec.md.
LAYA_MODELS="$LAYA_MODELS_DIR" USE_TF=0 .venv/bin/python third_party/laya/research/scripts/bench_local.py --langs 0 --per-lang 100 --skip-b
```

`bench_local.py` has no option to pick languages by name; it only truncates the sorted list with `--langs N` (source: research/scripts/bench_local.py:314-316). How to run ko alone is defined by the 03/04 documents.

→ **Verification**: `research deps ok` is printed.

### 2.10 Environment recording script `scripts/env_report.py`

Writes, as JSON, the environment snapshot that every run refers to. Specification:

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
    # snapshot_revision returns the sha only when the realpath ends in snapshots/<sha>. Only models/laya has that shape;
    # the two subfolders look like snapshots/<sha>/multilingual, so the parent directory is queried again. All three share the same bundle sha.
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

`snapshot_revision` resolves the symlink to its realpath and returns the sha only when the last directory is `snapshots/<sha>` (source: laya/revisions.py `snapshot_revision`). The `multilingual/`·`typed-decisions/` subpaths are `snapshots/<sha>/<sub>`, so on their own they give `None`; as in the code above, the parent directory is queried again and the same bundle sha (`55cf4c4...`) is recorded. The `snapshot_sha` of the three checkpoints must be identical.

```bash
.venv/bin/python scripts/env_report.py
```

→ **Verification**: The path `results/env/env_<YYYYMMDD-HHMM>.json` is printed, and in the file `checkpoints.laya.snapshot_sha` is `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`, `versions.laya` is `0.3.23` and `mps_available` is `true`.

---

## 3. Smoke tests [step → verification]

Run `source env.sh` first. Do not set `HF_HUB_OFFLINE` yet (`laya-evals` must be able to query the bundle repo's metadata; it may be set after 3.3 passes).

### 3.1 Routing only (no model load)

```bash
.venv/bin/laya "결제가 두 번 됐어요, 환불해주세요"
```

Routing downloads no checkpoint and finishes in milliseconds (source: README.md "Command line").

→ **Verification**: In the output, `model` is `multilingual` and `reason` mentions non-Latin script / hangul. If `english` appears, the `laya/lang.py` detection is broken, so stop.

### 3.2 Preset prediction (CLI)

```bash
.venv/bin/laya "결제가 두 번 됐어요, 환불해주세요" --preset triage        # --preset implies --predict
```

The `triage` preset is written to read the `message` field of the state, and the CLI puts the text under that key (source: laya/presets.py `state_field`, laya/cli.py:52). Once 2.6 is done, it loads from the cache without downloading.

→ **Verification**: 5 lines are printed, `intent`, `is_urgent`, `frustration`, `refund_requested` and `churn_risk` (`frustration` is the expected score level, not a probability; the others are probabilities), and the routing is multilingual. The values are only recorded on the Run Card and not judged here (quality comes from Track A on).

### 3.3 Evaluation harness fixture (checking that the accuracy numbers match)

```bash
.venv/bin/laya-evals validate third_party/laya/research/evals/fixture.jsonl
.venv/bin/laya-evals run third_party/laya/research/evals/fixture.jsonl --model english --device cpu \
  --json results/env/smoke_fixture_english_cpu.json --markdown results/env/smoke_fixture_english_cpu.md
```

→ **Verification**: The quality metrics below must match **exactly**. The harness is deterministic at a pinned revision (source: docs/evals.md "Baseline and CI gate"), and upstream has published its numbers for the same fixture run with the English checkpoint on CPU (source: the table in docs/evals.md "Evaluating an ONNX export").

| Metric | Expected value (upstream, torch Router, CPU) | What to suspect on a mismatch |
|---|---|---|
| `choice_accuracy` | 0.75 | revision mismatch, routing to a different checkpoint |
| `noul_accuracy` | 1.00 | same |
| `score_mae` | 1.3418 | precision (whether CPU bf16 is on, `LAYA_CPU_AMP`) |
| `ece` | 0.1596 | A change in the **wording** of the temperature warning. english·typed-decisions emit one `choice:11+=0.1006 -> 0.5` clamp warning even in the normal state (measured), so check whether the wording is the same, not whether there is a warning |
| `mean_confidence` | 0.7304 | same |
| `latency_p50_ms` | 116.8 (reference only, replaced by this machine's number) | not compared |

The JSON must record `55cf4c4...` in `config.revisions` and `0.3.23` in `config.laya_version`. If the quality metrics disagree, it is an environment problem, so do not proceed to the benchmark.

### 3.4 Minimal example (local-path load)

```bash
.venv/bin/python third_party/laya/examples/01_first_call_minimal.py
```

This example loads the checkout's `models/laya` directly (source: examples/01_first_call_minimal.py). It fails without the `third_party/laya/models` link from 2.7.

→ **Verification**: One line, `P(refund requested) = 0.xxxx (confidence 0.xxxx)`. Since the device is `device=None`, MPS is selected, and the first call may take 10 seconds or more (§4).

### 3.5 Whether CPU and MPS give the same answers

```bash
.venv/bin/python third_party/laya/examples/35_device_selection_and_latency.py
```

→ **Verification**: The script prints the median ms of both devices, and the last line reads `answers agree after JSON serialisation: True`. The script only prints and does not assert (the exit code is always 0), so check the `True` on that line yourself (examples/35_device_selection_and_latency.py:76). If it is `False`, isolate the cause with the parity procedure of §4.

### 3.6 Upstream smoke script

```bash
.venv/bin/python third_party/laya/verify/laya_smoke_test.py --models ./models --device cpu --repeat 3
.venv/bin/python third_party/laya/verify/laya_smoke_test.py --models ./models --device mps --repeat 3
```

It runs routing, the three checkpoints, the three primitives and the presets with real weights, prints per-checkpoint latency, and exits non-zero on failure (source: header of verify/laya_smoke_test.py). It does not require CUDA. Caution: this script imports the checkout's `laya/` via `sys.path.insert(0, ROOT)` (verify/laya_smoke_test.py:24), so the results are for the 4aa6761 checkout code, not the PyPI installation. The two code bases differ in three files (agent.py alias loading, router.py `resolve_model_spec`, the serve.py batch surrogate guard) (confirmed in the Phase 0 run).

→ **Verification**: Both runs have exit code 0 (`echo $?`). The printed latencies go on the Run Card only as "reference" (the formal measurement is Track D).

### 3.7 HTTP server `laya-serve`

```bash
# Terminal 1. LAYA_MODELS here has laya-serve's meaning (a list of checkpoint names to preload). env.sh does not export LAYA_MODELS (§2.8)
LAYA_HOST=127.0.0.1 LAYA_PORT=8000 LAYA_MODELS=multilingual LAYA_DEVICE=mps LAYA_THREADS=10 .venv/bin/laya-serve
```

```bash
# Terminal 2
curl -s localhost:8000/health | python3 -m json.tool
curl -s localhost:8000/v1/systemone -H 'content-type: application/json' -d '{
  "state": {"body": "3월 요금이 두 번 결제됐어요. 중복 결제분 환불해주세요."},
  "questions": {"dept": {"type": "choice", "instructions": "Which team should handle `body`?",
                "criteria": {"billing": "refunds, invoices, payments", "technical": "bugs, outages", "other": "everything else"}}}
}' | python3 -m json.tool
```

`laya-serve` reads `LAYA_MODELS` as a comma-separated list of checkpoint names and exits with a configuration error on an unknown name (source: laya/serve.py:667-668 and the module docstring). Because the research scripts read the same name as a directory path, env.sh exports only `LAYA_MODELS_DIR`, and `LAYA_MODELS` is given on each command line with that command's meaning (§2.8, §2.9). The default of `LAYA_PRELOAD` is 1.

→ **Verification**: `/health` contains `status: ok`, `multilingual` in `loaded`, `55cf4c4...` in `revisions`, and `mps` as `device` (internal information is visible because `LAYA_API_KEY` is not set; source: README.md "What's new in 0.3.23"). The `/v1/systemone` response has `answers.dept.choice`, `answers.dept.answer_confidence`, `routing.model == "multilingual"` and `usage.input_tokens`.

### 3.8 Web GUI playground

```bash
# Stop the 3.7 server first. Both use the default port 8000
.venv/bin/python third_party/laya/examples/server.py --device mps --no-preload --port 8000
```

→ **Verification**: In a browser, a two-panel playground opens at `http://127.0.0.1:8000`, and running a Korean request with Ctrl+Enter shows the distribution and confidence (source: README.md "Try it locally: web GUI + JSON API"). Used for the PoC demo·question schema design (05).

---

## 4. Device·precision·thread settings

**MPS.**
- Upstream writes that the first call of a new (batch, length) shape takes about 13 s for Metal kernel compilation (source: examples/README.md "Before you start"), but on this machine (torch 2.14.1, macOS 26.6.2) the first MPS call measured 0.17 s, so this was not reproduced (`results/poc/P0_20261002.md`). The warm-up is kept anyway. Every measurement discards at least 1 warm-up call and uses the median (`timed` in `examples/_common.py:126` follows that pattern).
- `agent.dtype` is the autocast target, so on MPS it shows `float16`, but a call with fewer rows than `mps_amp_min_rows` (default 5) runs in fp32. Read the actual precision with `agent.dtype_for(rows)` (source: README.md "Automated Confidence Gating", laya/agent.py:278-290). This means calls with 1-4 questions run in fp32 and those with 5 or more·`predict_batch` in fp16; mark this boundary when reading latency tables.
- `LAYA_MPS_AMP_MIN_ROWS=100000` can force all of MPS to fp32. Use it only for parity checks and for isolating "did the answer change because of precision".

**CPU (reference).**
- fp32 by default. Reference values for accuracy·ECE are always produced with CPU fp32.
- Threads: `torch.set_num_threads(10)` + `torch.set_num_interop_threads(1)`. Upstream measured a 12× gain from fixing inter-op to 1, and that intra-op is optimal near the number of physical cores (source: BENCHMARKS.md §Laptop CPU). For `laya-serve`, `LAYA_THREADS=10`. The 4/8/10/14-thread sweep is done in Track D (`03_benchmark_plan.md`).

**How to specify the device.**

| Path | How |
|---|---|
| SDK | `laya.load(path, device="cpu"|"mps")`, `Router(device=...)`. With `None`, the order is CUDA → MPS → CPU |
| `laya-evals run` | `--device cpu|mps` (ignored on the `--onnx` path; source: docs/evals.md) |
| `laya-serve` | `LAYA_DEVICE=cpu|mps` |
| `examples/*.py` | `_common.load(name, device=...)`, `server.py --device` |
| research scripts | Mostly hard-code `device="cpu"` (`bench_local.py:152`). To run on MPS, wrap them in our own scripts |

**Parity check procedure** (`python scripts/metrics_extra.py parity <cpu_report.json> <mps_report.json>`, subcommand style. 03_benchmark_plan.md §3.8·A5·C9. A preliminary step of Track D).
1. Input: reports from running the same JSONL (`ko_poc_triage_v1` of the 04 document, or `ko_klue_ynat_7`, which shares the questions) twice with `laya-evals run --model multilingual --json ...`, once with `--device cpu` and once with `--device mps`.
2. `metrics_extra.py --parity` pairs the per-case `answer` (argmax and `probabilities`, laya/evals.py:728-744) of the two reports case by case and compares them.
3. The MPS side runs twice: (a) `LAYA_MPS_AMP_MIN_ROWS=100000` (MPS fp32) (b) the default (fp16 for 5 or more rows; `--batch-size 16` makes it take the fp16 path).
4. Metrics: number of argmax flips, max |Δp| over all options.
5. Pass: in (a), 0 flips and max |Δp| ≤ 0.01. (b) is only recorded but compared with upstream's reference values: against fp32, bf16 moves up to 0.073 with 3 flips out of 864, and fp16 stays within 0.019 with 0 flips (source: README.md "Automated Confidence Gating"; the methodology is benchmarks/parity_fast.py and BENCHMARKS.md §GPU fast path "Same answers").
6. If (a) fails, MPS is used only for latency measurement and all quality numbers are produced on CPU. This is not a workaround but a division of roles per device, and it is stated on the Run Card.

---

## 5. Optional components

### 5.1 ONNX export and INT8 (CPU deployment scenario)

```bash
mkdir -p models/onnx
.venv/bin/python third_party/laya/scripts/export_onnx.py --model models/laya-multilingual \
  --output models/onnx/laya-multilingual.onnx --quantize
.venv/bin/laya-evals run data/evals/<set>.jsonl --onnx models/onnx/laya-multilingual.int8.onnx \
  --model models/laya-multilingual --json results/D/<run-id>.json
```

Since 0.3.23, `--quantize` defaults to per-tensor. Per-channel collapsed the decision model to 32 % agreement with eager (source: the ONNX item of README.md "What's new in 0.3.23"). The INT8 file is written next to `--output` as `<stem>.int8.onnx` (`int8_output_path`: `laya.onnx` → `laya.int8.onnx`; source: scripts/export_onnx.py). On the `--onnx` path, `--model` must be the path·Hub id of the export source, not a Router short name, and `--device` does not apply (source: docs/evals.md "Evaluating an ONNX export"). On upstream's fixture, the fp32 export reproduces the torch numbers exactly, while int8 moved `score_mae` by +0.009 and `ece` by +0.006 (same source). The actual measurement is Track D7 (03_benchmark_plan.md).

→ **Verification**: The two files `.onnx` and `.int8.onnx` are created, and the `laya-evals` quality metrics of the fp32 export equal those of the torch CPU run.

### 5.2 Docker (mirror of a Linux CPU deployment)

```bash
cd third_party/laya && docker compose run --build --rm laya; cd -
```

A CPU image; it needs 8 GB RAM·10 GB disk, and the weights persist in a named volume (source: docs/docker.md). There is no GPU passthrough on this machine, so this is for previewing "what happens on a Linux CPU server". The server modes and the environment-variable table are in docs/docker.md §Configuration.

→ **Verification**: The JSON of the sample request is printed with `choice`/`score`/`noul` answers.

### 5.3 LLM baseline API key

```bash
cat > .env <<'EOF'
ANTHROPIC_API_KEY=sk-ant-...
EOF
set -a; source .env; set +a
```

`.env` is in `.gitignore` (2.1). The baseline model id is `claude-haiku-4-5-20251001`; the call design·cost cap·prompts are defined in `03_benchmark_plan.md`. Before running, write the budget cap (e.g. number of requests × average tokens) on the Run Card, and stop if it is exceeded.

→ **Verification**: `.venv/bin/python -c "import os; print(bool(os.environ.get('ANTHROPIC_API_KEY')))"` prints `True`.

### 5.4 When a CUDA server is available

This applies only when running the same benchmark on an NVIDIA host outside this machine.
- `LAYA_DEVICE=cuda`, `LAYA_PRELOAD=1`. At compute capability 8 or higher, autocast uses the checkpoint's `amp_dtype` (bf16 for all three checkpoints).
- Against fp32, bf16 moved probabilities by up to 0.073 and flipped 3 of 864 argmaxes, while fp16 stayed within 0.019 with 0 flips, so `LAYA_CUDA_AMP=fp16` is the default candidate (source: README.md "Automated Confidence Gating").
- The TileLang path of `pip install laya[fast]` + `laya.load(..., fast=True)`, and `compile=True` + `agent.warmup()`, are CUDA-only (source: README.md "GPU Fast Path", "Warm-up before serving").
- If `Failed to find C compiler` appears on a slim image or a host without a C compiler, use `TORCH_DISABLE_NATIVE_JIT=1` (source: docs/docker.md "NVIDIA GPU / CUDA").

### 5.5 Hugging Face cache location

The existing `~/.cache/huggingface` is 99 GB, but it holds other projects' assets, so it is left alone. To keep the datasets inside the project, add `export HF_HOME="$PWD/data/raw/hf"` to env.sh; in that case the checkpoints are downloaded again under it as well, so redo 2.6-2.7 with that setting (the snapshot path changes). Upstream also recommends an `HF_HOME` inside the checkout (source: research/README.md "Running the harnesses").

---

## 6. Troubleshooting

| Symptom | Cause | Fix | Source |
|---|---|---|---|
| `ModuleNotFoundError: No module named 'laya'` | The interpreter used to install differs from the one used to run (the default `python3` is 3.14) | Always run with `.venv/bin/python`, `.venv/bin/laya*` | README.md "Installation details" |
| `Incompatible model: ... does not contain 'rl_agent_config.json'` | The repo root or `third_party/laya` was passed as the model path | Pass a checkpoint directory such as `models/laya` | README.md same section, laya/agent.py:577-580 |
| The first `--predict`·`Router()` gives a network error | `HF_HUB_OFFLINE=1` with a cache miss | Unset the variable and rerun 2.6 | README.md "Command line" |
| `load_dataset` fails | `HF_HUB_OFFLINE=1` | Unset it while collecting datasets | research/README.md |
| Hang during model creation (macOS) | abseil runtime deadlock when TensorFlow is installed | `USE_TF=0` (included in env.sh) | research/README.md |
| `could not patch .../tokenizer_config.json` warning or PermissionError | `_fix_tokenizer_config` writes a temporary file into the snapshot directory and calls `os.replace`; this fails on a read-only mount | Use a writable path. The symlinked HF cache snapshot is writable, so it works | laya/agent.py:56-108 |
| First MPS call takes 10 s or more | Metal kernel compilation | Measure after warm-up. It happens again when the shape (batch, length) changes | examples/README.md |
| torch installation failure·import error | Python 3.14 environment | Recreate with a 3.12 venv (2.2) | README.md "Windows + Python 3.14" item |
| `laya-serve` returns 503 with `Retry-After` | `LAYA_MAX_CONCURRENT` exceeded | Client retries, adjust concurrency | README.md "What's new in 0.3.21" |
| `/health` lacks `loaded`·`revisions` | `LAYA_API_KEY` is set, so internal information moved behind the bearer token | `-H 'Authorization: Bearer <key>'` | README.md "What's new in 0.3.23" |
| `address already in use` :8000 | `laya-serve` and `examples/server.py` running at the same time | Change `LAYA_PORT` or `--port` | README.md "Try it locally" |
| `laya-serve` exits immediately with a checkpoint-name error | `LAYA_MODELS=<path>` is exported in the shell, so serve interprets it as a list of names (env.sh does not export it, but it happens after a manual export) | `unset LAYA_MODELS`, or `LAYA_MODELS=multilingual` on the server command line | laya/serve.py:667-668 |
| CPU inference takes seconds for 1 question | inter-op/intra-op thread oversubscription | `set_num_threads(10)`, `set_num_interop_threads(1)`, `LAYA_THREADS=10` | BENCHMARKS.md §Laptop CPU |
| On MPS, `agent.dtype` is `float16` but fp32 was expected | `dtype` is the autocast target. Fewer than 5 rows run in fp32 | Check with `agent.dtype_for(rows)`; if needed, `LAYA_MPS_AMP_MIN_ROWS` | README.md "Automated Confidence Gating" |
| `huggingface-cli: deprecated and no longer works` | The CLI was renamed | `hf download ...` | Checked locally (hf 1.18.0) |
| `laya-evals run` fails with `baseline is not comparable: dataset_sha256` | The dataset bytes differ from the baseline | Rerun with the same file, or update the baseline and record it in an ADR | docs/evals.md "Baseline and CI gate" |

---

## 7. Environment recording conventions

Every benchmark·PoC run records the following. The form is `06_templates.md` §1 "Experiment run record (Run Card)".

| Item | Source |
|---|---|
| `results/env/env_<YYYYMMDD-HHMM>.json` path | The 2.10 script. Regenerate it when the env changes (package versions·threads·`HF_HUB_OFFLINE` etc.) |
| Checkpoint revision | `config.revisions` of the `laya-evals` report, or `checkpoints.*.snapshot_sha` of the env JSON |
| Dataset identity | `config.dataset_sha256`, `config.questions_sha256` of the report (source: docs/evals.md "Run identity") |
| Device·precision·threads | `--device`, `agent.dtype_for(rows)`, `torch.get_num_threads()` |
| Full run command | One copy-pasteable line |
| warm-up·repetitions | Number of discarded calls, number of measured calls, aggregation (median/p95) |
| Result files | `results/<track>/<YYYYMMDD-HHMM>_<model>_<dataset>.json` and `.md` |
| Thermal·power state | Whether on mains power, concurrent load at the time (`06_templates.md` §5 checklist) |

`laya-evals compare` ignores `*_ms` metrics unless they are given a tolerance, so latency noise does not break the baseline comparison (source: docs/evals.md "Batching and timing"). Latency regressions are compared in a separate table.

---

## Open questions / assumptions

1. **Assumption**: The package code of PyPI 0.3.23 in `.venv` and of `third_party/laya` @ `4aa6761` is taken to be identical. Both are dated 2026-10-01, but byte identity has not been checked. If in doubt, check with `diff -r third_party/laya/laya .venv/lib/python3.12/site-packages/laya`.
2. **Assumption**: `uv pip install` in 2.3 picks the torch 2.14.1 arm64 wheel. If another version resolves, the record from 2.10 is sufficient, and no forced pin is applied. The combination of transformers 5.x and laya 0.3.23 is validated by upstream's EPYC measurement (transformers 5.17.0) (source: BENCHMARKS.md §Server CPU).
3. **Open question**: How often MPS fp16 (5 or more rows) and CPU fp32 flip the argmax on Korean input. Based on the §4 parity results, decide whether quality numbers after Track D may also be produced on MPS.
4. **Open question**: Whether the 3.3 fixture numbers also match byte for byte under transformers 5.18.0. If they differ in the fourth decimal place, first check the tokenizer patch warning; if they still differ, re-baseline `04`/`03` on our environment's numbers (recorded in an ADR).
5. **Assumption**: ONNX·Docker·the LLM baseline·CUDA are optional. The default path (§2-§4) alone is enough to carry out Tracks A-E and PoC Phases 1-2.
6. **Open question**: Whether to keep the dataset cache in the default `~/.cache/huggingface` or separate it with `HF_HOME`. Start with the default and switch to §5.5 if free disk space drops below 20 GB.

**English** | [한국어](02_environment_setup.ko.md)
