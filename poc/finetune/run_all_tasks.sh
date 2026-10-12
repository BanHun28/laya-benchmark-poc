#!/usr/bin/env bash
# T3arm long run: the trained-Laya arm, T1..T10 in order (user decisions 2026-10-08). Prepared, not started, by the prep run.
#   bash poc/finetune/run_all_tasks.sh               full run (gate: poc/finetune/READY_T3ARM, items sha256 per task)
#   SMOKE=1 bash poc/finetune/run_all_tasks.sh       every step with 64 train items x 1 epoch per task; checkpoints and
#                                                    items in a temp dir, eval files cut to their first rows and paired
#                                                    with vanilla runs on the same cut copies
#   PREFLIGHT_ONLY=1 bash poc/finetune/run_all_tasks.sh   the full run's gate checks only (READY sha256 per task, no
#                                                    leftover poc/finetune/ckpt_t3arm/<task>, vanilla reports, disk)
#   TASKS="T3 T5" bash poc/finetune/run_all_tasks.sh only these tasks
#   SEED=14 RUN_TAG=rep_s14 bash poc/finetune/run_all_tasks.sh   torch seed 14 (default 13); full-mode results in
#                                                    results/T3arm/rep_s14/, checkpoints in poc/finetune/ckpt_t3arm_rep_s14/
# Per task: train (poc/finetune/laya_finetune_mps_patched.py through run_ft.py: MPS fp32, seed 13, micro-batch 8 x
#   grad-accum 4, --no-checkpointing, 2 epochs, temperature fitted on the reserved calibration rows, every epoch
#   kept) -> dev accuracy of the base (epoch 0 = vanilla) and of every epoch (eval_ckpt.py, CPU fp32, threads 10/1,
#   batch 8) -> selection (docs/11 §4): highest dev accuracy, a tie goes to the earlier epoch; the final export is the last
#   epoch + fitted temperature, an earlier epoch is recalibrated on the same calibration rows by ft_task.py calibrate
#   -> the selected model on the Jev-format set(s) (T1: the 200-decision file; T7: the five language
#   files) and the ext set(s) -> paired with vanilla on the same files -> diagnostics (loss/acc windows, train-vs-dev gap,
#   temperatures, option-order flip on the 40 dev rows of choice tasks with scripts/probe_option_order.py) -> epoch
#   copies, checkpoint_latest and an unselected final export deleted after their sha256 is recorded; the selected model is
#   kept as poc/finetune/ckpt_t3arm/<task>/.
# Status: results/T3arm/run_all_status.log gets `STEP <task>:<step> OK|FAILED` and ends with `RUN_ALL FINISHED` or
#   `RUN_ALL FAILED` (exit != 0); SMOKE writes them to results/T3arm/smoke_<ts>/run_all_status.log.
# Disk: free space is checked before each task; under 15 GB the run stops (FAILED).
set -euo pipefail
cd "$(dirname "$0")/../.."
TS=$(date +%Y%m%d-%H%M)
TASKS=${TASKS:-"T1 T2 T3 T4 T5 T6 T7 T8 T9 T10"}
D=poc/finetune/data/t3arm; CKR=poc/finetune/ckpt_t3arm${RUN_TAG:+_$RUN_TAG}; READY=poc/finetune/READY_T3ARM; MIN_FREE_GB=15
if [ "${SMOKE:-0}" = 1 ]; then
  R=results/T3arm/smoke_$TS; TMP=$(mktemp -d "${TMPDIR:-/tmp}/t3arm_smoke.XXXXXX"); CKD=$TMP/ckpt
elif [ "${PREFLIGHT_ONLY:-0}" = 1 ]; then
  R=results/T3arm/preflight_$TS; TMP=; CKD=$CKR
else
  R=results/T3arm${RUN_TAG:+/$RUN_TAG}; TMP=; CKD=$CKR
fi
STATUS=$R/run_all_status.log; LOG=$R/run_all_${TS}_driver.log
mkdir -p "$R" "$CKD"
exec 3>&1  # the console: a failing step's EXIT trap still runs inside that step's `>> $LOG` redirection

CUR=setup
log() { echo "$(date '+%F %T') $*" | tee -a "$LOG" >&3; }
finish() {
  local rc=$?
  if [ "$rc" = 0 ]; then
    echo "RUN_ALL FINISHED" >> "$STATUS"; log "RUN_ALL FINISHED $TS"
  else
    echo "STEP $CUR FAILED" >> "$STATUS"; echo "RUN_ALL FAILED" >> "$STATUS"; log "RUN_ALL FAILED $TS at $CUR (rc $rc), see $LOG"
  fi
  if [ -n "$TMP" ]; then rm -rf "$TMP"; fi
}
trap finish EXIT
trap 'exit 130' INT TERM HUP
step() {  # step NAME CMD...: output to the driver log; a failing command ends the run (set -e), the EXIT trap records it
  CUR=$1; shift
  local t0=$SECONDS
  log "STEP $CUR ..."
  "$@" >> "$LOG" 2>&1
  echo "STEP $CUR OK" >> "$STATUS"; log "STEP $CUR OK ($((SECONDS - t0)) s)"
}
echo "RUN_ALL START $TS SMOKE=${SMOKE:-0} TASKS=$TASKS" >> "$STATUS"
log "RUN_ALL START $TS (SMOKE=${SMOKE:-0}) tasks: $TASKS; results $R; checkpoints $CKD"

source env.sh
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1  # every input is local
caffeinate -i -w $$ &  # no idle sleep while this script runs
PY=.venv/bin/python; M="$PY poc/finetune/t3arm_metrics.py"
EV="$PY poc/finetune/eval_ckpt.py run --batch-size 8 --threads 10"
RUNFT="$PY poc/finetune/run_ft.py --script poc/finetune/laya_finetune_mps_patched.py --seed ${SEED:-13}"
SHA=55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851
base_of() { if [ "$1" = T7 ]; then echo multilingual; else echo english; fi; }
base_dir() { if [ "$1" = multilingual ]; then echo models/laya-multilingual; else echo models/laya; fi; }
epochs_of() { if [ "${SMOKE:-0}" = 1 ]; then echo 1; else echo 2; fi; }  # T8 too: the user's budget is 2 epochs per task (docs/11 §1)
is_choice_task() { case $1 in T1|T2|T3|T4|T7|T10) return 0 ;; *) return 1 ;; esac; }
jev_sets() {
  case $1 in
    T1) echo data/evals/jev_cmp/T1_typed_decisions_40.jsonl ;;
    T7) for l in en de ja zh-CN ko; do echo data/evals/jev_cmp/T7_massive_intent_10opt_${l}_20.jsonl; done ;;
    *) ls data/evals/jev_cmp/$1_*.jsonl | grep -v "_v0.jsonl" ;;
  esac
}
ext_sets() { ls data/evals/jev_cmp_ext/$1_*.jsonl; }
vanilla_of() {  # vanilla report of the same file and base: F's for the T1-T8 Jev sets, results/T3arm/vanilla otherwise
  local stem; stem=$(basename "$1" .jsonl)
  if [ "${SMOKE:-0}" = 1 ]; then echo "$R/$3/vanilla_$stem.json"; return; fi  # SMOKE: the cut copy's own vanilla run
  case $1 in
    data/evals/jev_cmp/T9_*|data/evals/jev_cmp/T10_*|data/evals/jev_cmp_ext/*) echo results/T3arm/vanilla/${stem}_$2.json ;;
    *) echo results/F/jev_cmp/laya/${stem}_$2.json ;;
  esac
}
cut_copy() {  # SRC N DST: header lines + the first N rows (SMOKE eval files)
  $PY - "$@" <<'PYEOF'
import sys
from pathlib import Path
src, n, dst = sys.argv[1], int(sys.argv[2]), Path(sys.argv[3])
lines = Path(src).read_text(encoding="utf-8").split("\n")
head = [l for l in lines if l.startswith("#")]
body = [l for l in lines if l.strip() and not l.startswith("#")]
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text("\n".join(head + ["# smoke copy: first %d of %d rows of %s" % (min(n, len(body)), len(body), src)] + body[:n]) + "\n",
               encoding="utf-8")
PYEOF
}
free_gb() { df -k . | awk 'NR == 2 {printf "%d", $4 / 1024 / 1024}'; }

global_preflight() {
  local f
  for f in "$(base_dir english)/model.safetensors" "$(base_dir multilingual)/model.safetensors" \
           poc/finetune/laya_finetune_mps_patched.py poc/finetune/ft_task.py poc/finetune/eval_ckpt.py; do
    [ -s "$f" ] || { echo "missing input: $f"; return 1; }
  done
  if [ "${SMOKE:-0}" != 1 ]; then
    [ -s "$READY" ] || { echo "missing $READY: the prep run has not signed off"; return 1; }
    local t s
    for t in $TASKS; do  # the vanilla reports each task is paired with, so a run cannot fail after its training
      for s in $(jev_sets "$t") $(ext_sets "$t"); do
        f=$(vanilla_of "$s" "$(base_of "$t")" "$t")
        [ -s "$f" ] || { echo "missing vanilla report: $f"; return 1; }
      done
    done
  fi
}
step global:preflight global_preflight
if [ "${PREFLIGHT_ONLY:-0}" = 1 ]; then
  task_gate() {
    local t=$1 items want got
    items=$D/${t}_$(base_of "$t").pt
    want=$(awk -v t="$t" '$1 == "items_sha256" && $2 == t {print $4}' "$READY")
    got=$(shasum -a 256 "$items" | cut -d' ' -f1)
    [ -n "$want" ] && [ "$got" = "$want" ] || { echo "$items sha256 $got is not READY's ($want)"; return 1; }
    [ ! -e "$CKR/$t" ] && [ ! -e "$CKR/${t}_run" ] && [ ! -e "$CKR/${t}_sel" ] || { echo "$CKR/$t* exists"; return 1; }
  }
  for t in $TASKS; do step "$t:gate" task_gate "$t"; done
  log "PREFLIGHT OK: $(free_gb) GB free (>= $MIN_FREE_GB GB needed before each task)"
  exit 0
fi
if [ "${SMOKE:-0}" != 1 ] && [ -s results/T3arm/time_estimate.json ]; then
  log "expected train loop (fit on the prep runs' micro-batch traces): $($PY -c 'import json, sys
e = json.load(open(sys.argv[1])); t = sys.argv[2].split()
print("%.2f h for %s (%s)" % (sum(e["tasks"][k]["train_loop_h"] for k in t), " ".join(t),
      ", ".join("%s %.2f h" % (k, e["tasks"][k]["train_loop_h"]) for k in t)))' results/T3arm/time_estimate.json "$TASKS") + evaluation (see results/T3arm/PREP_*.md)"
fi

run_task() {
  local t=$1 base ep rt ck sel items calib dev dev40 n_calib k s stem e
  base=$(base_of "$t"); ep=$(epochs_of "$t"); rt=$R/$t; ck=$CKD/${t}_run; sel=$ck
  mkdir -p "$rt"
  CUR=$t:disk
  if [ "$(free_gb)" -lt $MIN_FREE_GB ]; then log "free disk $(free_gb) GB < $MIN_FREE_GB GB before $t: stop"; return 1; fi
  echo "STEP $t:disk OK ($(free_gb) GB free)" >> "$STATUS"
  dev=$D/${t}_dev.jsonl; dev40=$D/${t}_dev40.jsonl
  local jevs exts
  jevs=$(jev_sets "$t"); exts=$(ext_sets "$t")
  if [ "${SMOKE:-0}" = 1 ]; then
    items=$TMP/${t}_items.pt; n_calib=7; [ "$t" = T1 ] && n_calib=5
    step "$t:items" $PY poc/finetune/ft_task.py items --task "$t" --base "$base" --n-train 64 --n-calib $n_calib --out "$items"
    local sd=$TMP/evals/$t j="" x=""
    cut_copy "$dev" 16 "$sd/$(basename "$dev")"; dev=$sd/$(basename "$dev")
    if is_choice_task "$t"; then cut_copy "$dev40" 8 "$sd/$(basename "$dev40")"; dev40=$sd/$(basename "$dev40"); fi
    for s in $jevs; do cut_copy "$s" 8 "$sd/jev/$(basename "$s")"; j="$j $sd/jev/$(basename "$s")"; done
    for s in $exts; do cut_copy "$s" 8 "$sd/ext/$(basename "$s")"; x="$x $sd/ext/$(basename "$s")"; done
    jevs=$j; exts=$x
  else
    items=$D/${t}_${base}.pt
    CUR=$t:ready
    local want got
    want=$(awk -v t="$t" '$1 == "items_sha256" && $2 == t {print $4}' "$READY")
    got=$(shasum -a 256 "$items" | cut -d' ' -f1)
    [ -n "$want" ] && [ "$got" = "$want" ] || { log "$items sha256 $got is not READY's ($want)"; return 1; }
    [ ! -e "$CKR/$t" ] || { log "$CKR/$t exists: move the previous selected model away first"; return 1; }
    echo "STEP $t:ready OK" >> "$STATUS"
  fi
  calib=$($PY -c 'import json, sys; print(json.load(open(sys.argv[1]))["n_calib"])' "${items%.pt}.provenance.json")
  step "$t:preflight" mkdir "$ck"  # fails if it exists: the script exports in place

  train() {
    $RUNFT --report "$rt/train_timing.json" --keep-epoch-checkpoints -- "$(base_dir "$base")" "$ck" --items "$items" \
      --calib-max "$calib" --epochs "$ep" --micro-batch 8 --grad-accum 4 --no-checkpointing --device mps > "$rt/train.log" 2>&1
  }
  step "$t:train" train
  step "$t:dev_ep0" $EV --ckpt "$(base_dir "$base")" --name "$base" --revision "$SHA" --dataset "$dev" --out "$rt/dev_ep0"
  local devs=()
  for ((e = 1; e < ep; e++)); do  # not seq: BSD `seq 1 0` counts down
    step "$t:dev_ep$e" $EV --ckpt "$ck/epoch_$e" --name "t3arm-$t-ep$e" --revision "local:$ck/epoch_$e (base $SHA)" \
      --dataset "$dev" --out "$rt/dev_ep$e"
    devs+=("$rt/dev_ep$e.json")
  done
  step "$t:dev_final" $EV --ckpt "$ck" --name "t3arm-$t-final" --revision "local:$ck (base $SHA)" --dataset "$dev" --out "$rt/dev_final"
  devs+=("$rt/dev_final.json")
  step "$t:select" $M select "${devs[@]}" --json "$rt/select.json"
  k=$($PY -c 'import json, sys; print(json.load(open(sys.argv[1]))["selected_index"])' "$rt/select.json")
  if [ "$k" -lt $((ep - 1)) ]; then  # an earlier epoch: the script's calibration applied to it
    sel=$CKD/${t}_sel
    recal() { $PY poc/finetune/ft_task.py calibrate --ckpt "$ck/epoch_$((k + 1))" --items "$items" --calib-max "$calib" \
                --out "$sel" --device mps > "$rt/recalibrate.json"; }
    step "$t:recalibrate_epoch$((k + 1))" recal
  fi
  for s in $jevs; do
    stem=$(basename "$s" .jsonl)
    step "$t:jev_$stem" $EV --ckpt "$sel" --name "t3arm-$t" --revision "local:$sel (base $SHA)" --dataset "$s" --out "$rt/jev_$stem"
  done
  for s in $exts; do
    stem=$(basename "$s" .jsonl)
    step "$t:ext_$stem" $EV --ckpt "$sel" --name "t3arm-$t" --revision "local:$sel (base $SHA)" --dataset "$s" --out "$rt/ext_$stem"
  done
  if [ "${SMOKE:-0}" = 1 ]; then  # vanilla on the same cut copies, so the pairing step runs in the smoke too
    for s in $jevs $exts; do
      stem=$(basename "$s" .jsonl)
      step "$t:vanilla_$stem" $EV --ckpt "$(base_dir "$base")" --name "$base" --revision "$SHA" --dataset "$s" --out "$rt/vanilla_$stem"
    done
  fi
  local flip=""
  if is_choice_task "$t"; then
    step "$t:flip_dev40" $PY scripts/probe_option_order.py "$dev40" --model "$sel" --device cpu --permutations 5 --seed 13 \
      --split all --splits "" --out "$rt/flip_dev40.json"
    flip="--flip $rt/flip_dev40.json"
  fi
  local calj=""; [ -s "$rt/recalibrate.json" ] && calj="--calibrate-json $rt/recalibrate.json"
  step "$t:diagnostics" $M diag --task "$t" --timing "$rt/train_timing.json" --select "$rt/select.json" --ep0 "$rt/dev_ep0.json" \
    --selected-ckpt "$sel" \
    $calj $flip --out "$rt/diagnostics.json"
  metrics() {
    $M summary "$rt/dev_ep0.json" "${devs[@]}" $(ls "$rt"/jev_*.json "$rt"/ext_*.json) --out "$rt/summary.md" \
      --json "$rt/summary.json"
    for s in $jevs $exts; do
      stem=$(basename "$s" .jsonl)
      local r=$rt/ext_$stem.json
      if [ -s "$rt/jev_$stem.json" ]; then r=$rt/jev_$stem.json; fi
      $M paired "$(vanilla_of "$s" "$base" "$t")" "$r" --json "$rt/paired_${stem}.json"
    done
  }
  step "$t:metrics" metrics
  cleanup() {  # sha256 of every weights file that is not the selected model, then delete; keep the selected model
    find "$ck" "$sel" -name model.safetensors 2>/dev/null | sort -u | while read -r f; do
      echo "$(shasum -a 256 "$f" | cut -d' ' -f1) $f$([ "$f" = "$sel/model.safetensors" ] && echo " (selected, kept)")"
    done > "$rt/weights_sha256.txt"
    rm -rf "$ck"/epoch_* "$ck/checkpoint_latest"
    if [ "$sel" != "$ck" ]; then rm -rf "$ck"; fi
    if [ "${SMOKE:-0}" = 1 ]; then rm -rf "$sel"; else mv "$sel" "$CKR/$t"; fi
  }
  step "$t:cleanup" cleanup
}

for t in $TASKS; do
  run_task "$t"
done
if [ "${SMOKE:-0}" != 1 ]; then
  CUR=global:summary
  step global:summary $M summary $(ls "$R"/T*/jev_*.json "$R"/T*/ext_*.json) --out "$R/run_all_${TS}_summary.md" \
    --json "$R/run_all_${TS}_summary.json"
fi
