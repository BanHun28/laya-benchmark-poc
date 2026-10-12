#!/usr/bin/env bash
# T3arm training-validity checks (results/T3arm/validity/). Each subcommand is one check; run from anywhere.
#   bash poc/finetune/t3arm_validity.sh v5   200-item 1-epoch smoke per base: train (MPS) -> export -> laya.load -> eval
#   bash poc/finetune/t3arm_validity.sh v1   zero-step export per base (--epochs 0) -> eval -> must match vanilla argmax
#   bash poc/finetune/t3arm_validity.sh v2   upstream laya-typed-decisions + our T1 run (5,000 decisions x 2) on the
#                                            full typed-decisions test (2,000 decisions)
#   bash poc/finetune/t3arm_validity.sh v3   T3 emotion, 5,000 items x 1 epoch, labels permuted vs real labels -> dev
# Training: poc/finetune/run_ft.py --script poc/finetune/laya_finetune_mps_patched.py, seed 13, MPS fp32, micro-batch 8 x
# grad-accum 4, --no-checkpointing (P4 configuration). Eval: poc/finetune/eval_ckpt.py, CPU fp32, threads 10/1, batch 8
# (the batch size of the vanilla reports in results/F/jev_cmp/laya/). Checkpoints made here are deleted after their
# weights' sha256 is recorded (results/T3arm/validity/deleted_ckpt_sha256.txt).
set -euo pipefail
cd "$(dirname "$0")/../.."
source env.sh
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.venv/bin/python; V=results/T3arm/validity; D=poc/finetune/data/t3arm; CKR=poc/finetune/ckpt_t3arm
EV="$PY poc/finetune/eval_ckpt.py run --batch-size 8 --threads 10"; M="$PY poc/finetune/t3arm_metrics.py"
RUNFT="$PY poc/finetune/run_ft.py --script poc/finetune/laya_finetune_mps_patched.py --seed 13"
TRAIN_ARGS="--micro-batch 8 --grad-accum 4 --no-checkpointing --device mps"
base_dir() { [ "$1" = multilingual ] && echo models/laya-multilingual || echo models/laya; }  # bash 3.2: no assoc arrays
mkdir -p "$V" "$CKR"
log() { echo "$(date '+%F %T') $*" | tee -a "$V/validity_status.log"; }
forget() {  # record weights sha256 of every model.safetensors under $1, then delete $1
  find "$1" -name model.safetensors | sort | while read -r f; do
    echo "$(date '+%F %T') $(shasum -a 256 "$f" | cut -d' ' -f1) $f" >> "$V/deleted_ckpt_sha256.txt"; done
  rm -rf "$1"
}

v5() {
  for base in english multilingual; do
    local task=T1; [ $base = multilingual ] && task=T7
    local items=$V/V5_${base}_items.pt ck=$CKR/_v5_$base set
    set=data/evals/jev_cmp/T1_typed_decisions_40.jsonl; [ $base = multilingual ] && set=data/evals/jev_cmp/T7_massive_intent_10opt_ko_20.jsonl
    log "V5 $base: items ($task, 200 train + 20 calibration)"
    $PY poc/finetune/ft_task.py items --task $task --base $base --n-train 200 --n-calib 20 --out "$items" > "$V/V5_${base}_items.log" 2>&1
    rm -rf "$ck"
    log "V5 $base: train 1 epoch"
    $RUNFT --report "$V/V5_${base}_timing.json" --keep-epoch-checkpoints -- "$(base_dir $base)" "$ck" --items "$items" \
      --calib-max 20 --epochs 1 $TRAIN_ARGS > "$V/V5_${base}_train.log" 2>&1
    log "V5 $base: laya.load + eval $(basename $set)"
    $EV --ckpt "$ck" --name "v5-$base" --dataset "$set" --out "$V/V5_${base}_$(basename $set .jsonl)" > "$V/V5_${base}_eval.log" 2>&1
    cp "$ck/rl_agent_config.json" "$V/V5_${base}_rl_agent_config.json"
    forget "$ck"
    log "V5 $base OK"
  done
}

v1() {
  for base in english multilingual; do
    local task=T2 set=data/evals/jev_cmp/T2_ag_news_40.jsonl ref=results/F/jev_cmp/laya/T2_ag_news_40_english.json
    if [ $base = multilingual ]; then
      task=T7; set=data/evals/jev_cmp/T7_massive_intent_10opt_ko_20.jsonl
      ref=results/F/jev_cmp/laya/T7_massive_intent_10opt_ko_20_multilingual.json
    fi
    local ck=$CKR/_v1_$base
    rm -rf "$ck"
    log "V1 $base: zero-step export ($task items: its 400 calibration items fit the temperature)"
    $RUNFT --zero-step --report "$V/V1_${base}_timing.json" -- "$(base_dir $base)" "$ck" --items "$D/${task}_${base}.pt" \
      --calib-max 400 --epochs 0 $TRAIN_ARGS > "$V/V1_${base}_export.log" 2>&1
    $PY - "$ck" "$(base_dir $base)" "$V/V1_${base}_export_diff.json" <<'EOF'
import hashlib, json, sys, torch
from pathlib import Path
from safetensors.torch import load_file
ck, base, out = map(Path, sys.argv[1:])
a, b = load_file(str(base / "model.safetensors")), load_file(str(ck / "model.safetensors"))
ca, cb = (json.loads((p / "rl_agent_config.json").read_text()) for p in (base, ck))
diff = {k: {"base": ca.get(k), "export": cb.get(k)} for k in sorted(set(ca) | set(cb)) if ca.get(k) != cb.get(k)}
res = {"tensors": len(a), "same_names": sorted(a) == sorted(b),
       "values_equal": sum(torch.equal(a[k].float(), b[k].float()) for k in a),
       "dtype_changed": {k: [str(a[k].dtype), str(b[k].dtype)] for k in a if a[k].dtype != b[k].dtype},
       "weights_sha256": {"base": hashlib.sha256((base / "model.safetensors").read_bytes()).hexdigest(),
                          "export": hashlib.sha256((ck / "model.safetensors").read_bytes()).hexdigest()},
       "config_diff": diff,
       "files": {"base": sorted(str(p.relative_to(base.resolve())) for p in base.resolve().rglob("*") if p.is_file()),
                 "export": sorted(str(p.relative_to(ck)) for p in ck.rglob("*") if p.is_file())}}
out.write_text(json.dumps(res, indent=1, default=str) + "\n")
print(json.dumps({k: res[k] for k in ("tensors", "same_names", "values_equal", "dtype_changed")}), "config diff keys:", sorted(diff))
EOF
    log "V1 $base: eval $(basename $set) vs vanilla $ref"
    $EV --ckpt "$ck" --name "v1-zero-step-$base" --dataset "$set" --out "$V/V1_${base}_$(basename $set .jsonl)" > "$V/V1_${base}_eval.log" 2>&1
    $M same "$ref" "$V/V1_${base}_$(basename $set .jsonl).json" --json "$V/V1_${base}_same.json"
    # the same export with the base's temperature fields put back: every answer must equal vanilla's, byte for byte
    cp -R "$ck" "${ck}_basetemp"
    $PY - "${ck}_basetemp" "$(base_dir $base)" <<'PYEOF'
import json, sys
from pathlib import Path
ck, base = map(Path, sys.argv[1:])
cfg, ref = (json.loads((p / "rl_agent_config.json").read_text()) for p in (ck, base))
cfg["temperature"] = ref["temperature"]
if "temperature_by_options" in ref:
    cfg["temperature_by_options"] = ref["temperature_by_options"]
(ck / "rl_agent_config.json").write_text(json.dumps(cfg, indent=2))
PYEOF
    $EV --ckpt "${ck}_basetemp" --name "v1-zero-step-basetemp-$base" --dataset "$set" \
      --out "$V/V1_${base}_basetemp_$(basename $set .jsonl)" > "$V/V1_${base}_basetemp_eval.log" 2>&1
    $M same "$ref" "$V/V1_${base}_basetemp_$(basename $set .jsonl).json" --json "$V/V1_${base}_basetemp_same.json" \
      --require-identical
    forget "${ck}_basetemp"
    forget "$ck"
    log "V1 $base OK"
  done
}

v2() {
  local ext=data/evals/jev_cmp_ext/T1_typed_decisions_test400.jsonl ck=$CKR/_v2_T1
  rm -rf "$ck"
  log "V2: train T1 (english, 5,000 decisions x 2 epochs)"
  $RUNFT --report "$V/V2_T1_timing.json" --keep-epoch-checkpoints -- models/laya "$ck" --items "$D/T1_english.pt" \
    --calib-max 400 --epochs 2 $TRAIN_ARGS > "$V/V2_T1_train.log" 2>&1
  log "V2: upstream laya-typed-decisions on $ext"
  $EV --ckpt models/laya-typed-decisions --name typed-decisions --revision 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 \
    --dataset "$ext" --out "$V/V2_typed-decisions_T1_test400" > "$V/V2_typed-decisions_eval.log" 2>&1
  log "V2: dev (600 decisions) per epoch"
  $EV --ckpt "$ck/epoch_1" --name v2-T1-ep1 --dataset $D/T1_dev.jsonl --out "$V/V2_T1-ep1_dev" > "$V/V2_eval_dev1.log" 2>&1
  $EV --ckpt "$ck" --name v2-T1 --dataset $D/T1_dev.jsonl --out "$V/V2_T1_dev" > "$V/V2_eval_dev2.log" 2>&1
  log "V2: ours on $ext (final export = epoch 2 + fitted T; epoch 1 too)"
  $EV --ckpt "$ck" --name v2-T1 --dataset "$ext" --out "$V/V2_T1_T1_test400" > "$V/V2_eval_test.log" 2>&1
  $EV --ckpt "$ck/epoch_1" --name v2-T1-ep1 --dataset "$ext" --out "$V/V2_T1-ep1_T1_test400" > "$V/V2_eval_test1.log" 2>&1
  cp "$ck/rl_agent_config.json" "$V/V2_T1_rl_agent_config.json"
  shasum -a 256 "$ck/model.safetensors" "$ck/epoch_2/model.safetensors" > "$V/V2_final_vs_epoch2_sha256.txt"
  forget "$ck"
  log "V2 OK"
}

v3() {
  local ck dev=$D/T3_dev.jsonl
  log "V3: items with permuted labels"
  $PY poc/finetune/ft_task.py items --task T3 --base english --permute-labels --out "$V/V3_T3_permuted.pt" > "$V/V3_items.log" 2>&1
  for arm in permuted real; do
    ck=$CKR/_v3_$arm
    local items=$V/V3_T3_permuted.pt; [ $arm = real ] && items=$D/T3_english.pt
    rm -rf "$ck"
    log "V3 $arm: train 1 epoch"
    $RUNFT --report "$V/V3_${arm}_timing.json" -- models/laya "$ck" --items "$items" --calib-max 400 --epochs 1 $TRAIN_ARGS \
      > "$V/V3_${arm}_train.log" 2>&1
    $EV --ckpt "$ck" --name "v3-$arm" --dataset "$dev" --out "$V/V3_${arm}_T3_dev" > "$V/V3_${arm}_eval.log" 2>&1
    forget "$ck"
    log "V3 $arm OK"
  done
}

v3e2() {  # supporting control: the same permuted-label items for 2 epochs (does the excess over majority shrink?)
  local ck=$CKR/_v3_permuted_e2
  rm -rf "$ck"
  log "V3 permuted, 2 epochs: train"
  $RUNFT --report "$V/V3_permuted_e2_timing.json" --keep-epoch-checkpoints -- models/laya "$ck" --items "$V/V3_T3_permuted.pt" \
    --calib-max 400 --epochs 2 $TRAIN_ARGS > "$V/V3_permuted_e2_train.log" 2>&1
  $EV --ckpt "$ck/epoch_1" --name v3-permuted-e2-ep1 --dataset $D/T3_dev.jsonl --out "$V/V3_permuted_e2-ep1_T3_dev" > "$V/V3_permuted_e2_eval1.log" 2>&1
  $EV --ckpt "$ck" --name v3-permuted-e2 --dataset $D/T3_dev.jsonl --out "$V/V3_permuted_e2_T3_dev" > "$V/V3_permuted_e2_eval.log" 2>&1
  forget "$ck"
  log "V3 permuted, 2 epochs OK"
}

v3report() {  # V3 verdict (docs/11 §4: dev <= majority + 0.05 and >= 0.30 below the real-label epoch-1 dev) + diagnosis
  [ -s "$V/V3_vanilla_english_T3_dev.json" ] || $EV --ckpt models/laya --name english --revision 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851 \
    --dataset $D/T3_dev.jsonl --out "$V/V3_vanilla_english_T3_dev" > "$V/V3_vanilla_eval.log" 2>&1
  $PY - <<'PYEOF'
import json
from collections import Counter
from pathlib import Path
V = Path("results/T3arm/validity")
rep = {k: json.loads((V / ("V3_%s_T3_dev.json" % k)).read_text()) for k in ("permuted", "real", "vanilla_english")}
acc = {k: sum(c["correct"] for c in r["cases"]) / len(r["cases"]) for k, r in rep.items()}
gold = Counter(c["expected"] for c in rep["real"]["cases"])
majority = max(gold.values()) / sum(gold.values())
perm, van = rep["permuted"]["cases"], rep["vanilla_english"]["cases"]
both = lambda f: sum(1 for p, v in zip(perm, van) if f(p, v))  # noqa: E731
vc = [v["correct"] for v in van]
timing = {k: json.loads((V / ("V3_%s_timing.json" % k)).read_text()) for k in ("permuted", "real")}
out = {"dev": "poc/finetune/data/t3arm/T3_dev.jsonl", "n": len(perm), "gold_distribution": dict(gold.most_common()),
       "majority": majority, "chance": 1 / 6, "dev_accuracy": acc,
       "mean_confidence": {k: r["overall"]["mean_confidence"] for k, r in rep.items()},
       "permuted_pred_distribution": dict(Counter(c["answer"]["choice"] for c in perm).most_common()),
       "permuted_majority_class_share": max(Counter(c["answer"]["choice"] for c in perm).values()) / len(perm),
       "residual_prior": {"P(permuted right | vanilla right)": both(lambda p, v: p["correct"] and v["correct"]) / max(1, sum(vc)),
                          "P(permuted right | vanilla wrong)": both(lambda p, v: p["correct"] and not v["correct"]) / max(1, len(vc) - sum(vc)),
                          "argmax_agreement_permuted_vs_vanilla": both(lambda p, v: p["answer"]["choice"] == v["answer"]["choice"]) / len(perm)},
       "train_windows": {k: {"ce": t["train_ce_windows"], "acc": t["train_acc_windows"]} for k, t in timing.items()},
       "throughput": {k: t["throughput"] for k, t in timing.items()},
       "criteria": {"permuted <= majority + 0.05": acc["permuted"] <= majority + 0.05,
                    "real - permuted >= 0.30": acc["real"] - acc["permuted"] >= 0.30},
       "note": "real = the same 5,000 T3 items with their labels, 1 epoch (cosine over 1 epoch); the F run's epoch 1 of 2 "
               "is the docs/11 reference and replaces it once run_all_tasks.sh has run"}
(V / "V3_label_shuffle.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps({k: out[k] for k in ("majority", "dev_accuracy", "mean_confidence", "residual_prior", "criteria")}))
PYEOF
}

v2report() {  # V2: bench_local Part B metrics on the 2,000 test decisions vs BENCHMARKS.md:170-178
  $M summary "$V/V2_typed-decisions_T1_test400.json" results/T3arm/vanilla/T1_typed_decisions_test400_english.json \
    results/T3arm/vanilla/T1_typed_decisions_test400_multilingual.json "$V/V2_T1-ep1_T1_test400.json" "$V/V2_T1_T1_test400.json" \
    --out "$V/V2_T1_test400_summary.md" --json "$V/V2_T1_test400_summary.json" > /dev/null
  $PY - <<'PYEOF'
import json
from pathlib import Path
V = Path("results/T3arm/validity")
res = json.loads((V / "V2_T1_test400_summary.json").read_text())
pub = {"typed-decisions": (0.766, 0.471, 0.061, 0.213, 0.242), "english": (0.362, 0.332, 0.316, 0.175, 0.694),
       "multilingual": (0.352, 0.328, 0.463, 0.314, 0.760)}  # BENCHMARKS.md:172-174: acc, soft, Brier, ECE, score MAE
rows = {}
for m in res:
    rows[m["model"]] = {"n": m["n"], "accuracy_vs_label (upstream's)": m["accuracy_vs_upstream_label"],
                        "accuracy_vs_argmax_gold": m["accuracy"], "soft_accuracy": m["soft_accuracy"],
                        "brier_vs_soft": m["brier_vs_soft"], "ece": m["ece"], "score_mae": m["score_mae"],
                        "by_question_type": m["by_type"], "published": pub.get(m["model"])}
td, ours = rows["typed-decisions"], rows["v2-T1"]
out = {"set": "data/evals/jev_cmp_ext/T1_typed_decisions_test400.jsonl (400 cases / 2,000 decisions)", "models": rows,
       "criteria": {"(a) |typed-decisions acc - 0.766| <= 0.02": abs(td["accuracy_vs_label (upstream's)"] - 0.766) <= 0.02,
                    "(b) ours >= 0.562": ours["accuracy_vs_label (upstream's)"] >= 0.562,
                    "(b) ours > majority 0.461": ours["accuracy_vs_label (upstream's)"] > 0.461},
       "gap_ours_minus_upstream_ckpt": {k: ours[k] - td[k] for k in ("accuracy_vs_label (upstream's)", "accuracy_vs_argmax_gold",
                                                                    "soft_accuracy", "brier_vs_soft", "ece", "score_mae")},
       "budget": {"upstream": "Kaggle 2xT4 notebook: all 6,000 train decisions minus 400 calibration = 5,600 x 4 epochs = "
                              "22,400 item-passes, effective batch 64 (350 steps), fp16 autocast, max_len 1024 / head 256",
                  "ours": "5,000 decisions x 2 epochs = 10,000 item-passes, effective batch 32 (313 steps), MPS fp32, "
                          "max_len 512 / head 192 (english base budget), option-order shuffle on choice questions"}}
(V / "V2_upstream_repro.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps({"criteria": out["criteria"], "gap": out["gap_ours_minus_upstream_ckpt"],
                  "acc": {k: v["accuracy_vs_label (upstream's)"] for k, v in rows.items()}}))
PYEOF
}

v4() {  # collect the per-task format-identity checks ft_task.py items asserted (and build_train_sets.py check_format)
  $PY - <<'PYEOF'
import json
from pathlib import Path
V, D = Path("results/T3arm/validity"), Path("poc/finetune/data/t3arm")
st = json.loads(Path("results/T3arm/data_stats.json").read_text())["tasks"]
out = {}
for t in ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"):
    base = "multilingual" if t == "T7" else "english"
    p = json.loads((D / ("%s_%s.provenance.json" % (t, base))).read_text())
    out[t] = {"items": p["items"], "items_sha256": p["items_sha256"], "base": base, "budget": p["budget"],
              "v4_inference_identity": p["v4_inference_identity"],
              "all_items_options_decoded_and_targets_checked": p["n_items"],
              "jev_rows_reproduced_by_row_builder": st[t]["jev_rows_reproduced"],
              "options_reordered": p["options_reordered"], "decoded_example": p["decoded_example"]["options"]}
    assert p["v4_inference_identity"]["checked"] == p["v4_inference_identity"]["identical"] == 25, t
(V / "V4_format_identity.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
print("V4:", {t: "%d/%d identical, %d items decoded, %d Jev rows rebuilt" % (
    v["v4_inference_identity"]["identical"], v["v4_inference_identity"]["checked"],
    v["all_items_options_decoded_and_targets_checked"], v["jev_rows_reproduced_by_row_builder"]) for t, v in out.items()})
PYEOF
}

v6() {  # leakage: B's removal counts, and a fresh check of the written rows against every evaluation row
  $PY - <<'PYEOF'
import json, sys
from pathlib import Path
sys.path.insert(0, "scripts")
from laya.common import serialize_state
norm = lambda s: " ".join(serialize_state(s).lower().split())
read = lambda p: [json.loads(l) for l in Path(p).read_text(encoding="utf-8").split("\n") if l.strip() and not l.startswith("#")]
evals = sorted(list(Path("data/evals/jev_cmp").glob("T*.jsonl")) + list(Path("data/evals/jev_cmp_ext").glob("T*.jsonl")))
ex = {serialize_state(r["state"]) for p in evals for r in read(p)}
nm = {norm(r["state"]) for p in evals for r in read(p)}
st = json.loads(Path("results/T3arm/data_stats.json").read_text())
out = {"eval_files": len(evals), "eval_texts": {"exact": len(ex), "normalized": len(nm)}, "tasks": {}}
for t, v in st["tasks"].items():
    rec = {"removed_before_sampling": v["overlap_removed_total"],
           "removed_detail": {tag: {**x["eval_overlap_removed"],
                                    "train_pool_removed_as_dev_calib_twin": x["train_pool_removed_as_dev_calib_twin"]}
                              for tag, x in v["sampling"].items()},
           "ext_excluded_train_overlap": {k: x.get("train_overlap_excluded", x.get("train_overlap_excluded_ids", x.get("train_overlap_normalized")))
                                          for k, x in st["ext"][t].items()},
           "split_disjoint_normalized": v["split_disjoint"]}
    for split in ("train", "dev", "calib"):
        rows = read("poc/finetune/data/t3arm/%s_%s.jsonl" % (t, split))
        rec["%s_rows_matching_any_eval_item" % split] = {"exact": sum(serialize_state(r["state"]) in ex for r in rows),
                                                          "normalized": sum(norm(r["state"]) in nm for r in rows)}
        assert rec["%s_rows_matching_any_eval_item" % split] == {"exact": 0, "normalized": 0}, (t, split)
    out["tasks"][t] = rec
Path("results/T3arm/validity/V6_leakage.json").write_text(json.dumps(out, indent=1) + "\n")
print("V6:", {t: (r["removed_before_sampling"], r["ext_excluded_train_overlap"]) for t, r in out["tasks"].items()})
PYEOF
}

"$@"
