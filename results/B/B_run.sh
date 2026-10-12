#!/usr/bin/env bash
# Track B / PoC P1 runs, sequential, CPU fp32, accuracy only (another heavy process shares the machine:
# latency columns are not claims). Phases follow the priority order; cumulative model time is summed
# from the times log and a phase stops starting runs once it passes 90 min.
#   cd /Users/banhun/banhun28/lab/benchmarkforLaya && bash results/B/B_run.sh 1   (then 2, 3)
set -u
source env.sh
R=results/B; L=$R/logs; T=$L/B_run_times.log
BUDGET=5400
touch "$T"

used() { grep -o 'secs=[0-9]*' "$T" | cut -d= -f2 | awk '{s+=$1} END {print s+0}'; }

run() {  # model set dataset
  local model=$1 set=$2 path=$3
  if [ "$(used)" -ge "$BUDGET" ]; then echo "$(date '+%F %T') SKIP(budget) ${model}_${set}" >> "$T"; return; fi
  local ts id; ts=$(date +%Y%m%d-%H%M); id="${ts}_${model}_${set}"
  local args=(--device cpu --batch-size 16 --slice qid --slice tag)
  if [ "$model" = router ]; then args+=(--slice model); else args=(--model "$model" "${args[@]}"); fi
  echo "$(date '+%F %T') start $id :: laya-evals run $path ${args[*]} --json $R/$id.json --markdown $R/$id.md" >> "$T"
  local t0 t1 rc; t0=$(date +%s)
  .venv/bin/laya-evals run "$path" "${args[@]}" --json "$R/$id.json" --markdown "$R/$id.md" > "$L/$id.log" 2>&1
  rc=$?; t1=$(date +%s)
  if [ $rc -ne 0 ]; then
    for ext in json md; do [ -f "$R/$id.$ext" ] && mv "$R/$id.$ext" "$R/${id}_FAILED.$ext"; done
    mv "$L/$id.log" "$L/${id}_FAILED.log"
  fi
  echo "$(date '+%F %T') end   $id exit=$rc secs=$((t1 - t0)) cumulative=$(( $(used) + t1 - t0 ))" >> "$T"
}

case "${1:-}" in
  1)  # C sets x four runners, then the paired en run
    for set in ko_massive_domain_8 ko_klue_ynat_7 ko_massive_scenario_18; do
      for m in multilingual english typed-decisions router; do run $m $set data/evals/$set.jsonl; done
    done
    for m in multilingual english; do run $m en_massive_domain_8 data/evals/en_massive_domain_8.jsonl; done ;;
  2)  # ablations, multilingual, dev-only copies
    for v in ko_massive_domain_8_ko-instr ko_massive_domain_8_en-desc ko_klue_ynat_7_ko-instr ko_klue_ynat_7_en-desc \
             ko_massive_scenario_18_en-desc; do
      run multilingual "${v}_dev" "$R/dev/$v.jsonl"
    done ;;
  3)  # remaining Track B sets (ko_massive_intent_full60 belongs to Track C6)
    for m in multilingual english typed-decisions router; do run $m ko_massive_intent_20opt data/evals/ko_massive_intent_20opt.jsonl; done
    for m in multilingual english typed-decisions; do run $m en_massive_intent_20opt data/evals/en_massive_intent_20opt.jsonl; done
    for set in ko_klue_nli_3 ko_nsmc_sentiment ko_kmhas_hate ko_kmhas_type_8 ko_3i4k_speechact_7; do
      for m in multilingual english typed-decisions router; do run $m $set data/evals/$set.jsonl; done
    done ;;
  *) echo "usage: $0 1|2|3" >&2; exit 2 ;;
esac
