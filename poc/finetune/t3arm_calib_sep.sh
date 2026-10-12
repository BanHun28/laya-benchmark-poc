#!/usr/bin/env bash
# T3arm calibration-separation column "vanilla + task T" (results/T3arm/PREP_20261008.md, user decision 3): per task the
# V1 zero-step export (base weights, temperature fit on the task's calibration rows) on the task's Jev and ext sets.
#   bash poc/finetune/t3arm_calib_sep.sh              T1..T10
#   TASKS="T8" bash poc/finetune/t3arm_calib_sep.sh   only these tasks
# Per task, in results/T3arm/calib_sep/<task>/: export (run_ft.py --zero-step --epochs 0, MPS; items and calibration count
#   as in run_all_tasks.sh) -> export_diff.json (every tensor vs the base, both files' sha256, fitted temperature, config
#   diff) -> jev_<stem>.json / ext_<stem>.json (eval_ckpt.py, CPU fp32, batch 8, threads 10) -> same_<stem>.json against
#   the vanilla report of the same file (run_all_tasks.sh vanilla_of): the argmax must agree on every decision -> the
#   export poc/finetune/ckpt_calib_sep/<task>/ is deleted.
# Status: results/T3arm/calib_sep/status.log gets `STEP <task>:<step> OK|FAILED` and ends with `CALIB_SEP FINISHED` or
#   `CALIB_SEP FAILED` (exit != 0).
set -euo pipefail
cd "$(dirname "$0")/../.."
TS=$(date +%Y%m%d-%H%M)
TASKS=${TASKS:-"T1 T2 T3 T4 T5 T6 T7 T8 T9 T10"}
D=poc/finetune/data/t3arm; R=results/T3arm/calib_sep; CKR=poc/finetune/ckpt_calib_sep
STATUS=$R/status.log; LOG=$R/calib_sep_${TS}.log
mkdir -p "$R" "$CKR"
exec 3>&1

CUR=setup
log() { echo "$(date '+%F %T') $*" | tee -a "$LOG" >&3; }
finish() {
  local rc=$?
  if [ "$rc" = 0 ]; then
    echo "CALIB_SEP FINISHED" >> "$STATUS"; log "CALIB_SEP FINISHED $TS"
  else
    echo "STEP $CUR FAILED" >> "$STATUS"; echo "CALIB_SEP FAILED" >> "$STATUS"; log "CALIB_SEP FAILED $TS at $CUR (rc $rc), see $LOG"
  fi
}
trap finish EXIT
trap 'exit 130' INT TERM HUP
step() {
  CUR=$1; shift
  local t0=$SECONDS
  log "STEP $CUR ..."
  "$@" >> "$LOG" 2>&1
  echo "STEP $CUR OK" >> "$STATUS"; log "STEP $CUR OK ($((SECONDS - t0)) s)"
}
echo "CALIB_SEP START $TS TASKS=$TASKS" >> "$STATUS"
log "CALIB_SEP START $TS tasks: $TASKS; results $R; exports $CKR"

source env.sh
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
caffeinate -i -w $$ &
PY=.venv/bin/python; M="$PY poc/finetune/t3arm_metrics.py"
EV="$PY poc/finetune/eval_ckpt.py run --batch-size 8 --threads 10"
RUNFT="$PY poc/finetune/run_ft.py --script poc/finetune/laya_finetune_mps_patched.py --seed 13"
SHA=55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851
# run_all_tasks.sh's rules, full mode
base_of() { if [ "$1" = T7 ]; then echo multilingual; else echo english; fi; }
base_dir() { if [ "$1" = multilingual ]; then echo models/laya-multilingual; else echo models/laya; fi; }
jev_sets() {
  case $1 in
    T1) echo data/evals/jev_cmp/T1_typed_decisions_40.jsonl ;;
    T7) for l in en de ja zh-CN ko; do echo data/evals/jev_cmp/T7_massive_intent_10opt_${l}_20.jsonl; done ;;
    *) ls data/evals/jev_cmp/$1_*.jsonl | grep -v "_v0.jsonl" ;;
  esac
}
ext_sets() { ls data/evals/jev_cmp_ext/$1_*.jsonl; }
vanilla_of() {
  local stem; stem=$(basename "$1" .jsonl)
  case $1 in
    data/evals/jev_cmp/T9_*|data/evals/jev_cmp/T10_*|data/evals/jev_cmp_ext/*) echo results/T3arm/vanilla/${stem}_$2.json ;;
    *) echo results/F/jev_cmp/laya/${stem}_$2.json ;;
  esac
}

export_diff() {  # CK BASE OUT (V1's comparison)
  $PY - "$@" <<'PYEOF'
import hashlib, json, sys, torch
from pathlib import Path
from safetensors.torch import load_file
ck, base, out = map(Path, sys.argv[1:])
a, b = load_file(str(base / "model.safetensors")), load_file(str(ck / "model.safetensors"))
ca, cb = (json.loads((p / "rl_agent_config.json").read_text()) for p in (base, ck))
res = {"tensors": len(a), "same_names": sorted(a) == sorted(b),
       "values_equal": sum(torch.equal(a[k].float(), b[k].float()) for k in a if k in b),
       "dtype_changed": {k: [str(a[k].dtype), str(b[k].dtype)] for k in a if k in b and a[k].dtype != b[k].dtype},
       "weights_sha256": {"base": hashlib.sha256((base / "model.safetensors").read_bytes()).hexdigest(),
                          "export": hashlib.sha256((ck / "model.safetensors").read_bytes()).hexdigest()},
       "fitted_temperature": cb.get("temperature"),
       "config_diff": {k: {"base": ca.get(k), "export": cb.get(k)} for k in sorted(set(ca) | set(cb)) if ca.get(k) != cb.get(k)}}
out.write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps(res))
# the script saves every tensor as fp16 and the base keeps its temperature buffer in fp32, so the files' sha256 differ (V1)
assert res["same_names"] and res["values_equal"] == res["tensors"] and set(res["dtype_changed"]) <= {"temperature"}, res
PYEOF
}
same_argmax() {  # REF OTHER OUT: the argmax must agree on every decision
  $M same "$1" "$2" --json "$3"
  $PY - "$@" <<'PYEOF'
import json, sys
ref, other, out = sys.argv[1:]
# reports round probabilities to 4 decimals and a refit temperature can turn a near-tie into a tie there (T6 ext row 67:
# vanilla 0.3849 < 0.385, refit 0.2862 = 0.2862), so a tie agrees with any of its options
def top(a):
    if a["type"] == "choice":
        return {a["choice"]}
    if a["type"] == "noul":
        return {True, False} if a["noul"] == 0.5 else {a["noul"] > 0.5}
    m = max(a["probabilities"].values())
    return {k for k, v in a["probabilities"].items() if v == m}
ca, cb = (json.load(open(p))["cases"] for p in (ref, other))
res = json.load(open(out))
res["argmax_agreement_ties_agree"] = sum(bool(top(x["answer"]) & top(y["answer"])) for x, y in zip(ca, cb))
open(out, "w").write(json.dumps(res, indent=1) + "\n")
print(json.dumps({k: res[k] for k in ("decisions", "argmax_agreement", "argmax_agreement_ties_agree")}))
sys.exit(res["argmax_agreement_ties_agree"] != res["decisions"])
PYEOF
}

for t in $TASKS; do
  CUR=$t:setup
  base=$(base_of "$t"); items=$D/${t}_${base}.pt; rt=$R/$t; ck=$CKR/$t
  calib=$($PY -c 'import json, sys; print(json.load(open(sys.argv[1]))["n_calib"])' "${items%.pt}.provenance.json")
  jevs=$(jev_sets "$t"); exts=$(ext_sets "$t")
  mkdir -p "$rt"
  rm -rf "$ck"
  step "$t:export" $RUNFT --zero-step --report "$rt/export_timing.json" -- "$(base_dir "$base")" "$ck" --items "$items" \
    --calib-max "$calib" --epochs 0 --micro-batch 8 --grad-accum 4 --no-checkpointing --device mps
  step "$t:export_diff" export_diff "$ck" "$(base_dir "$base")" "$rt/export_diff.json"
  for s in $jevs $exts; do
    stem=$(basename "$s" .jsonl); out=$rt/ext_$stem
    case $s in data/evals/jev_cmp/*) out=$rt/jev_$stem ;; esac
    step "$t:$(basename "$out")" $EV --ckpt "$ck" --name "calib-sep-$t" --revision "local:$ck (zero-step export of base $SHA)" \
      --dataset "$s" --out "$out"
    step "$t:same_$stem" same_argmax "$(vanilla_of "$s" "$base")" "$out.json" "$rt/same_$stem.json"
  done
  step "$t:cleanup" rm -rf "$ck"
done
