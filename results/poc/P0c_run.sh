#!/usr/bin/env bash
# P0c runs, sequential (another experiment shares the machine; accuracy only, no latency claims).
#   cd /Users/banhun/banhun28/lab/benchmarkforLaya && bash results/poc/P0c_run.sh
set -u
source env.sh
R=results/poc

run() {  # set variant model jsonl
  local id="P0c_$1_$2_$3"
  echo "$(date '+%F %T') start $id" >> $R/P0c_run_times.log
  .venv/bin/laya-evals run "$4" --model "$3" --device cpu --batch-size 8 --slice qid \
    --json "$R/$id.json" --markdown "$R/$id.md" > "$R/$id.log" 2>&1
  local rc=$?
  echo "$(date '+%F %T') end   $id exit=$rc" >> $R/P0c_run_times.log
}

: > $R/P0c_run_times.log
for v in base ko-instr en-desc ko-instr_en-desc; do
  s=""; [ "$v" != base ] && s="_$v"
  run ynat100 "$v" multilingual "$R/P0c_ynat100$s.jsonl"
  run massive-scenario18 "$v" multilingual "$R/P0c_massive_scenario18_100$s.jsonl"
done
run ynat100 base english "$R/P0c_ynat100.jsonl"
run massive-scenario18 base english "$R/P0c_massive_scenario18_100.jsonl"
