#!/usr/bin/env bash
# K2 runs, sequential, CPU fp32 (another agent shares the machine; accuracy only, no latency claims).
#   cd /Users/banhun/banhun28/lab/benchmarkforLaya && bash results/korean_support/K2_run.sh
set -u
source env.sh
R=results/korean_support

run() {  # id model jsonl
  echo "$(date '+%F %T') start $1" >> $R/K2_run_times.log
  .venv/bin/laya-evals run "$3" --model "$2" --device cpu --batch-size 8 --slice qid \
    --json "$R/$1.json" --markdown "$R/$1.md" > "$R/$1.log" 2>&1
  local rc=$?
  echo "$(date '+%F %T') end   $1 exit=$rc" >> $R/K2_run_times.log
}

: > $R/K2_run_times.log
# E1 scenario-18, two instruments (Korean descriptions / upstream key-rendered descriptions)
for d in kodesc keydesc; do
  run "K2_scen18-${d}_ko_multilingual" multilingual "$R/K2_scen18_${d}_ko.jsonl"
  run "K2_scen18-${d}_en_multilingual" multilingual "$R/K2_scen18_${d}_en.jsonl"
  run "K2_scen18-${d}_en_english"      english      "$R/K2_scen18_${d}_en.jsonl"
done
# E2 intent-20 (upstream-faithful)
run K2_intent20_ko_multilingual multilingual "$R/K2_intent20_ko.jsonl"
run K2_intent20_en_multilingual multilingual "$R/K2_intent20_en.jsonl"
run K2_intent20_en_english      english      "$R/K2_intent20_en.jsonl"
run K2_intent20_ko_english      english      "$R/K2_intent20_ko.jsonl"
# E4 English probe (v1 on both checkpoints, v1b on multilingual)
run K2_probe-en-v1_multilingual  multilingual "$R/probe_en.jsonl"
run K2_probe-en-v1_english       english      "$R/probe_en.jsonl"
run K2_probe-en-v1b_multilingual multilingual "$R/K2_probe_en_v1b.jsonl"
