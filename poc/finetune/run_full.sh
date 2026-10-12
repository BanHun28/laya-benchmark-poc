#!/usr/bin/env bash
# P4 full fine-tune: laya-multilingual (55cf4c4) on MASSIVE ko train -> router task domain_8, then evaluation.
# Non-interactive; poc/finetune/autostart_when_gpu_free.sh starts it once poc/finetune/READY exists.
#   bash poc/finetune/run_full.sh           full run: poc/finetune/ckpt_domain8_v1/, logs results/P4/full_<YYYYmmdd-HHMM>_*
#   SMOKE=1 bash poc/finetune/run_full.sh   every step on 64 train rows x 1 epoch into results/P4/smoke_full/ (ckpt deleted)
# Items (prebuilt 2026-10-03; the run checks their sha256 against READY): poc/finetune/data/items_full.pt = the 11,094
#   train rows with their option order shuffled (make_domain8_items.py --shuffle-options all: random.Random(13 + row
#   index) per row) + 400 stratified validation rows in canonical order on the script's calibration slots. The
#   canonical-order build is kept as items_full_noshuffle.pt.
# Train (MPS fp32, upstream script unmodified, through run_ft.py): 3 epochs, micro-batch 8 x grad-accum 4 (effective 32,
#   1,041 steps), --no-checkpointing, --calib-max 400 (T fitted on the validation rows), every epoch kept as epoch_<k>/.
# Eval (CPU fp32, eval_ckpt.py): dev-2012 for every epoch and the final export; domain_8 500 rows (all/dev/test halves of
#   results/B/B_splits.json) and the 2,917-row ko test split (base and ft), each with and without the rows whose utterance
#   is also in train; YNAT dev-245 (forgetting, 05 §6 P4: drop <= 0.03); option-order flip (G4) on the domain_8 dev half
#   with scripts/probe_option_order.py (same 5 permutations, seed 13, as the zero-shot C1 run).
# Epoch rule: v1 = the final export (epoch-3 weights + fitted T). Epochs are compared on dev-2012 only (epoch_select:
#   exact McNemar against the final export); an earlier epoch more accurate there with p < 0.05 is reported as the v1
#   candidate for the lead to decide. Nothing is swapped automatically: epoch copies carry the base temperature.
# Status: results/P4/full_run_status.log gets `STEP <name> OK|FAILED` per step and the last line `RUN_FULL FINISHED` or
#   `RUN_FULL FAILED` (exit code non-zero). The smoke run writes the same lines to results/P4/smoke_full/full_run_status.log.
# Estimate, printed at start: train loop at probe D's 3.01 items/s (results/P4/probe200-mb8-nockpt_20261002-2012_timing.json,
#   same configuration, GPU co-tenant at ~100%) = 3.1 h; at the smoke run's 8.45 items/s (2026-10-03, idle GPU, 64 rows
#   including first-shape compiles) = 1.1 h. Plus calibration/export ~1 min and evaluation ~9 min (smoke: 6.3 min with
#   one epoch copy on an idle CPU; each further epoch copy adds a ~57 s dev-2012 run).
set -euo pipefail
cd "$(dirname "$0")/../.."
TS=$(date +%Y%m%d-%H%M); D=poc/finetune/data
if [ "${SMOKE:-0}" = 1 ]; then
  OUT=results/P4/smoke_full; RUN=smoke_$TS; CK=$OUT/ckpt_$TS; ITEMS=$OUT/smoke_${TS}_items.pt; EPOCHS=1; CALIB=7; NAME=ft-smoke
else
  OUT=results/P4; RUN=full_$TS; CK=poc/finetune/ckpt_domain8_v1; ITEMS=$D/items_full.pt; EPOCHS=3; CALIB=400; NAME=ft-v1
fi
M=$OUT/metrics; P=$OUT/$RUN; STATUS=$OUT/full_run_status.log; LOG=${P}_driver.log
mkdir -p "$M"
exec 3>&1  # the console: a failed step's EXIT trap still runs inside that step's `>> $LOG` redirection

CUR=setup
log() { echo "$(date '+%F %T') $*" | tee -a "$LOG" >&3; }
finish() {
  local rc=$?
  if [ "$rc" = 0 ]; then
    echo "RUN_FULL FINISHED" >> "$STATUS"; log "RUN_FULL FINISHED $RUN"
  else
    echo "STEP $CUR FAILED" >> "$STATUS"; echo "RUN_FULL FAILED" >> "$STATUS"; log "RUN_FULL FAILED $RUN at $CUR (rc $rc), see $LOG"
  fi
}
trap finish EXIT
trap 'exit 130' INT TERM HUP
step() {  # step NAME CMD...: output to the driver log; a failing command ends the run (set -e) and the EXIT trap logs it
  CUR=$1; shift
  local t0=$SECONDS
  log "STEP $CUR ..."
  "$@" >> "$LOG" 2>&1
  echo "STEP $CUR OK" >> "$STATUS"; log "STEP $CUR OK ($((SECONDS - t0)) s)"
}
echo "RUN_FULL START $RUN $(date '+%F %T')" >> "$STATUS"
log "RUN_FULL START $RUN (SMOKE=${SMOKE:-0}) ckpt $CK items $ITEMS epochs $EPOCHS calib $CALIB"

source env.sh
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1  # every input is local; nothing may download
caffeinate -i -w $$ &  # no idle sleep while this script runs
PY=.venv/bin/python; EV="$PY poc/finetune/eval_ckpt.py"; X="$PY scripts/metrics_extra.py"
BASE=models/laya-multilingual; SHA=55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851
E500=data/evals/ko_massive_domain_8.jsonl; E2917=results/P4/evalsets_full/ko_massive_domain_8.jsonl
DEV=$D/domain8_dev.jsonl; YNAT=results/P4/dev/ko_klue_ynat_7.jsonl; SPLITS=results/B/B_splits.json
B500=results/B/20261002-1643_multilingual_ko_massive_domain_8.json  # base references (the wrapper reproduces B 500/500)
BDEV=results/P4/20261002-2014_multilingual_domain8_dev.json
BYNAT=results/P4/20261002-2014_multilingual_ko_klue_ynat_7_dev.json
PROBE=results/P4/probe200-mb8-nockpt_20261002-2012_timing.json      # probe D: this configuration on 200 rows
IPS_IDLE=8.45; EVAL_MIN=9                                            # smoke run 2026-10-03, idle GPU / CPU

preflight() {
  local f want
  for f in "$BASE/model.safetensors" "$D/domain8_train.jsonl" "$DEV" "$E500" "$E2917" "$YNAT" "$SPLITS" "$B500" "$BDEV" \
           "$BYNAT" "$PROBE"; do
    [ -s "$f" ] || { echo "missing input: $f"; return 1; }
  done
  [ "$(df -k . | awk 'NR == 2 {print $4}')" -gt $((6 * 1024 * 1024)) ] || { echo "less than 6 GB free"; return 1; }
  if [ "${SMOKE:-0}" != 1 ]; then  # train exactly the verified items
    want=$(sed -n 's/^items_sha256=//p' poc/finetune/READY)
    [ "$(shasum -a 256 "$ITEMS" | cut -d' ' -f1)" = "$want" ] || { echo "$ITEMS sha256 is not READY's ($want)"; return 1; }
  fi
  mkdir "$CK"  # fails if it exists: the script exports in place, move an old one away first
}
step preflight preflight
if [ "${SMOKE:-0}" = 1 ]; then
  step items $PY poc/finetune/make_domain8_items.py items --train-n 64 --calib-n $CALIB --out "$ITEMS"
fi

CUR=estimate
NTRAIN=$($PY -c 'import json, sys; print(json.load(open(sys.argv[1]))["n_train"])' "${ITEMS%.pt}.provenance.json")
IPS=$($PY -c 'import json, sys; print(json.load(open(sys.argv[1]))["throughput"]["train_items_per_s"])' "$PROBE")
log "expected: train loop ($NTRAIN rows x $EPOCHS epochs) $(awk -v w=$((NTRAIN * EPOCHS)) -v r="$IPS" -v q="$IPS_IDLE" 'BEGIN {printf "%.2f h at %.2f items/s (probe D, GPU co-tenant at ~100%%), %.2f h at %.2f items/s (smoke, idle GPU)", w / r / 3600, r, w / q / 3600, q}') + calibration/export ~1 min + evaluation ~$EVAL_MIN min"

train() {
  $PY poc/finetune/run_ft.py --report "${P}_timing.json" --keep-epoch-checkpoints -- "$BASE" "$CK" --items "$ITEMS" \
    --calib-max $CALIB --epochs $EPOCHS --micro-batch 8 --grad-accum 4 --no-checkpointing --device mps > "${P}_train.log" 2>&1
}
step train train

ev() { $EV run --ckpt "$1" --name "$2" --revision "$3" --dataset "$4" --out "${P}_$2_$5"; }
FT="local:$CK (base $SHA)"
for e in $(seq 1 $EPOCHS); do
  step eval_dev_epoch$e ev "$CK/epoch_$e" "$NAME-ep$e" "$FT epoch $e" "$DEV" domain8_dev
done
step eval_dev ev "$CK" "$NAME" "$FT" "$DEV" domain8_dev
step epoch_select $EV epochs $(for e in $(seq 1 $EPOCHS); do echo "${P}_$NAME-ep${e}_domain8_dev.json"; done) \
  --final "${P}_${NAME}_domain8_dev.json" --out "$M/${RUN}_epoch_select.md"
step eval_500 ev "$CK" "$NAME" "$FT" "$E500" ko_massive_domain_8
step eval_2917_base ev "$BASE" multilingual "$SHA" "$E2917" ko_massive_domain_8_full
step eval_2917 ev "$CK" "$NAME" "$FT" "$E2917" ko_massive_domain_8_full
step eval_ynat_dev ev "$CK" "$NAME" "$FT" "$YNAT" ko_klue_ynat_7_dev
step flip_dev $PY scripts/probe_option_order.py "$E500" --model "$CK" --device cpu --permutations 5 --seed 13 --split dev \
  --splits "$SPLITS" --reference "${P}_${NAME}_ko_massive_domain_8.json" --out "$M/${RUN}_option_order_dev.json"

metrics() {  # no model call. The 2,917-row file keeps the builder's name, so summary also splits it by index parity: read `all`
  local ft=${P}_${NAME} b2917=${P}_multilingual_ko_massive_domain_8_full.json
  $X summary "${P}_${NAME}"-ep*_domain8_dev.json "${ft}_domain8_dev.json" "$BDEV" "${ft}_ko_massive_domain_8.json" "$B500" \
    "${ft}_ko_massive_domain_8_full.json" "$b2917" "${ft}_ko_klue_ynat_7_dev.json" "$BYNAT" \
    --out "$M/${RUN}_summary.md" --json "$M/${RUN}_summary.json"
  $X paired "$B500" "${ft}_ko_massive_domain_8.json" \
    --out "$M/${RUN}_paired_ko_massive_domain_8.md" --json "$M/${RUN}_paired_ko_massive_domain_8.json"
  $X paired "$b2917" "${ft}_ko_massive_domain_8_full.json" --split all \
    --out "$M/${RUN}_paired_ko_massive_domain_8_full.md" --json "$M/${RUN}_paired_ko_massive_domain_8_full.json"
  $X paired "$BDEV" "${ft}_domain8_dev.json" --split all \
    --out "$M/${RUN}_paired_domain8_dev.md" --json "$M/${RUN}_paired_domain8_dev.json"
  $X paired "$BYNAT" "${ft}_ko_klue_ynat_7_dev.json" --split all \
    --out "$M/${RUN}_paired_ko_klue_ynat_7_dev.md" --json "$M/${RUN}_paired_ko_klue_ynat_7_dev.json"
  $X coverage "${ft}_ko_massive_domain_8.json" --out "$M/${RUN}_coverage.md" --json "$M/${RUN}_coverage.json"
}
step metrics metrics
step overlap $EV overlap "$B500" "${P}_${NAME}_ko_massive_domain_8.json" "${P}_multilingual_ko_massive_domain_8_full.json" \
  "${P}_${NAME}_ko_massive_domain_8_full.json" "$BDEV" "${P}_${NAME}_domain8_dev.json" --train "$D/domain8_train.jsonl" \
  --splits "$SPLITS" --out "$M/${RUN}_overlap.md"
if [ "${SMOKE:-0}" = 1 ]; then
  step cleanup rm -rf "$CK"
fi
CUR=report
cat "$M/${RUN}_overlap.md"
sed -n 's/^decision: /epoch rule: /p' "$M/${RUN}_epoch_select.md"
log "summary $M/${RUN}_summary.md, flip $M/${RUN}_option_order_dev.md, status $STATUS"
