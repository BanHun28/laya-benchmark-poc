#!/usr/bin/env bash
# Track D driver: bash results/D/D_run.sh <step...>   (steps: d1 d2 d3 d8rss d1b d1c d4 d5 d8peak d6mps d6cpu d7 d7b)
# Every step logs `uptime` and the top CPU processes before it starts (load context, 03 §3.3).
set -euo pipefail
cd "$(dirname "$0")/../.."
source env.sh
PY=.venv/bin/python
LOG=results/D/logs/D_driver.log
mkdir -p results/D/logs

ctx() {
  echo "$(date '+%F %T') STEP $1 start | $(uptime | sed 's/.*load/load/') | $(pmset -g batt | head -1)" >> "$LOG"
  ps -Ao pcpu,comm -r | sed -n 2,4p | tr -s ' ' | paste -sd ';' - | sed 's/^/    top: /' >> "$LOG"
}
done_() { echo "$(date '+%F %T') STEP $1 done rc=$2 ($(( $(date +%s) - $3 )) s)" >> "$LOG"; }

step() {
  local name=$1; shift
  ctx "$name"; local t0; t0=$(date +%s)
  echo "$(date '+%F %T')   cmd: $*" >> "$LOG"
  set +e; "$@" > "results/D/logs/${name}.log" 2>&1; local rc=$?; set -e
  done_ "$name" "$rc" "$t0"
  return 0
}

for s in "$@"; do
  ts=$(date +%Y%m%d-%H%M)
  case $s in
    d1) step d1 $PY scripts/bench_latency_local.py --checkpoints english,multilingual,typed-decisions \
          --questions 1,3,5,10,50 --devices cpu,mps --states short,long --repeat 10 \
          --out results/D/${ts}_latency_matrix.json ;;
    d2) step d2 $PY scripts/bench_latency_local.py --checkpoints multilingual --questions 1,10 --devices cpu \
          --states short,long --threads 4,8,10,14 --interop 1,default --repeat 10 \
          --out results/D/${ts}_threads.json ;;
    d3) step d3 $PY scripts/bench_latency_local.py --cold 3 --checkpoints english,multilingual,typed-decisions \
          --devices cpu,mps --out results/D/${ts}_coldload.json ;;
    d8rss) step d8rss $PY scripts/bench_latency_local.py --rss --devices cpu,mps --out results/D/${ts}_rss_preload.json ;;
    d1b) step d1b env LAYA_MPS_AMP_MIN_ROWS=100000 $PY scripts/bench_latency_local.py --checkpoints multilingual,english \
          --questions 1,3,5,10,50 --devices mps --states short,long --repeat 10 \
          --out results/D/${ts}_latency_mps_fp32forced.json ;;
    d1c) step d1c $PY scripts/bench_latency_local.py --checkpoints multilingual --questions 1,3 --devices cpu,mps \
          --states short --repeat 20 --gap-ms 0,100,200,1000 --out results/D/${ts}_latency_paced.json ;;
    d4) step d4 $PY scripts/bench_batch_local.py --checkpoint multilingual \
          --states data/evals/ko_nsmc_sentiment.jsonl,data/evals/ko_klue_ynat_7.jsonl --n 64,256 \
          --batch-size 8,16,32 --sort-by-length both --devices cpu,mps --rounds 3 --interleave \
          --out results/D/${ts}_batch.json ;;
    d5) step d5 $PY scripts/bench_batch_local.py --router --n 32 --devices cpu,mps \
          --out results/D/${ts}_router_batch.json ;;
    d8peak) step d8peak $PY scripts/bench_batch_local.py --memory --n 64 --devices cpu,mps \
          --out results/D/${ts}_rss_peak_batch.json ;;
    d6mps|d6cpu)
      dev=${s#d6}
      if [ "$dev" = mps ]; then args=(--closed 1,4,8 --open 5,10,20 --batch-states 16,64); else args=(--closed 1 --open 10 --batch-states ""); fi
      ctx "serve-$dev"
      LAYA_MODELS=multilingual LAYA_DEVICE=$dev LAYA_PRELOAD=1 LAYA_HOST=127.0.0.1 LAYA_PORT=8000 LAYA_THREADS=10 \
        .venv/bin/laya-serve > "results/D/logs/serve_${dev}.log" 2>&1 &
      spid=$!
      for i in $(seq 1 180); do curl -sf http://127.0.0.1:8000/health > /dev/null && break; sleep 1; done
      echo "$(date '+%F %T')   serve $dev pid $spid healthy after ${i}s: $(curl -s http://127.0.0.1:8000/health)" >> "$LOG"
      step "d6$dev" $PY scripts/bench_http_local.py --url http://127.0.0.1:8000 --questions 1,3 "${args[@]}" \
          --duration 60 --label "LAYA_DEVICE=$dev LAYA_THREADS=10" --out "results/D/${ts}_http_${dev}.json"
      kill "$spid"; wait "$spid" 2>/dev/null || true
      sleep 2
      echo "$(date '+%F %T')   serve $dev stopped; port 8000 $(lsof -nP -iTCP:8000 -sTCP:LISTEN > /dev/null && echo BUSY || echo free)" >> "$LOG" ;;
    d7)
      mkdir -p models/onnx
      step d7export $PY third_party/laya/scripts/export_onnx.py --model models/laya-multilingual \
          --output models/onnx/laya-multilingual.onnx --quantize
      ls -la models/onnx | sed 's/^/    /' >> "$LOG"
      step d7onnx_fp32 .venv/bin/laya-evals run data/evals/ko_klue_ynat_7.jsonl --model models/laya-multilingual \
          --onnx models/onnx/laya-multilingual.onnx --batch-size 16 \
          --json results/D/${ts}_onnx_fp32_ynat.json --markdown results/D/${ts}_onnx_fp32_ynat.md
      step d7onnx_int8 .venv/bin/laya-evals run data/evals/ko_klue_ynat_7.jsonl --model models/laya-multilingual \
          --onnx models/onnx/laya-multilingual.int8.onnx --batch-size 16 \
          --json results/D/${ts}_onnx_int8_ynat.json --markdown results/D/${ts}_onnx_int8_ynat.md
      step d7torch .venv/bin/laya-evals run data/evals/ko_klue_ynat_7.jsonl --model multilingual --device cpu \
          --batch-size 16 --json results/D/${ts}_torch_cpu_ynat.json --markdown results/D/${ts}_torch_cpu_ynat.md ;;
    d7b)
      for kind in fp32 int8; do
        f=models/onnx/laya-multilingual.onnx; [ "$kind" = int8 ] && f=models/onnx/laya-multilingual.int8.onnx
        step "d7b_$kind" $PY results/D/ort_threads_prelude.py run data/evals/ko_klue_ynat_7.jsonl --model models/laya-multilingual \
            --onnx "$f" --batch-size 16 --json "results/D/${ts}_onnx_${kind}_t10_ynat.json" --markdown "results/D/${ts}_onnx_${kind}_t10_ynat.md"
      done ;;
    *) echo "unknown step $s" >&2; exit 2 ;;
  esac
done
