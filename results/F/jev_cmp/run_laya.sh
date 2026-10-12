#!/usr/bin/env bash
# S0 Laya side of the Laya-vs-Jev comparison (docs/09_laya_vs_jev_plan.md §7 S0), sequential, CPU fp32, accuracy only.
# Every data/evals/jev_cmp set x {english, multilingual, router}; T1 also typed-decisions (fine-tuned on
# typed-decisions train, a separate line). Then the determinism rerun and the T2 option-order probe.
# laya-evals has no thread flag, so its own main() runs under torch intra-op 10 / inter-op 1.
# With set names as arguments only those sets run (archived *_v0 sets are skipped by default).
#   cd /Users/banhun/banhun28/lab/benchmarkforLaya && bash results/F/jev_cmp/run_laya.sh [SET ...]
set -u
source env.sh
D=data/evals/jev_cmp; R=results/F/jev_cmp/laya; L=$R/logs; T=$L/run_times.log
mkdir -p "$L"
PY='import sys, torch; torch.set_num_threads(10); torch.set_num_interop_threads(1)
from laya.evals_cli import main; sys.argv[0] = "laya-evals"; sys.exit(main())'

run() {  # set model [id suffix]
  local set=$1 model=$2 id="$1_$2${3:-}"
  local args=(run "$D/$set.jsonl" --device cpu --batch-size 8 --slice qid --json "$R/$id.json" --markdown "$R/$id.md")
  if [ "$model" = router ]; then args+=(--slice model); else args+=(--model "$model"); fi
  echo "$(date '+%F %T') start $id :: laya-evals ${args[*]}" >> "$T"
  local t0 rc; t0=$(date +%s)
  .venv/bin/python -c "$PY" "${args[@]}" > "$L/$id.log" 2>&1
  rc=$?
  echo "$(date '+%F %T') end   $id exit=$rc secs=$(( $(date +%s) - t0 ))" >> "$T"
}

if [ $# -gt 0 ]; then sets="$*"; else
  sets=""
  for f in "$D"/T*.jsonl; do
    case "$f" in *_v0.jsonl) ;; *) sets="$sets $(basename "$f" .jsonl)" ;; esac
  done
fi
echo "$(date '+%F %T') uptime: $(uptime)" >> "$T"
for set in $sets; do
  case "$set" in
    *_noulnocrit) models="english multilingual" ;;   # comparison-only variant: noul criteria removed
    *) models="english multilingual router" ;;
  esac
  for m in $models; do run "$set" "$m"; done
  case "$set" in T1_typed_decisions_40)
    run "$set" typed-decisions
    run "$set" english _rerun ;;   # determinism: must equal T1_typed_decisions_40_english
  esac
done

# option-order flip probe on T2: one permutation per item, all 40 rows, original and permuted in one process
case " $sets " in *" T2_ag_news_40 "*) probe_models="english multilingual" ;; *) probe_models="" ;; esac
for m in $probe_models; do
  ckpt=$([ $m = english ] && echo models/laya || echo models/laya-multilingual)
  t0=$(date +%s)
  echo "$(date '+%F %T') start probe_$m" >> "$T"
  .venv/bin/python scripts/probe_option_order.py "$D/T2_ag_news_40.jsonl" --model "$ckpt" --device cpu \
      --permutations 1 --seed 13 --split all --splits "" --reference "$R/T2_ag_news_40_$m.json" \
      --out "results/F/jev_cmp/T2_option_order_k1_$m.json" > "$L/probe_$m.log" 2>&1
  rc=$?
  echo "$(date '+%F %T') end   probe_$m exit=$rc secs=$(( $(date +%s) - t0 ))" >> "$T"
done
echo "$(date '+%F %T') uptime: $(uptime)" >> "$T"
