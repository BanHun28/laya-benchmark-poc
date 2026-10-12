#!/usr/bin/env bash
# P4 step 1 probe, as run on 2026-10-02 (run card: results/P4/P4_probe_20261002.md). Re-running writes new
# timestamped results and needs poc/finetune/ckpt_probe* moved away first (the script exports in place).
#   cd /Users/banhun/banhun28/lab/benchmarkforLaya && bash poc/finetune/run_probe.sh [probe|aux|eval]
set -euo pipefail
cd "$(dirname "$0")/../.."
source env.sh
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1  # items are prebuilt; the script must never download
PY=.venv/bin/python; R=results/P4; D=poc/finetune/data
BASE=models/laya-multilingual; SHA=55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851
TS=$(date +%Y%m%d-%H%M)

data() {
  $PY poc/finetune/make_domain8_items.py rows
  $PY poc/finetune/make_domain8_items.py items --train-n 1000 --calib-n 100 --shuffle-options none --out $D/items_probe.pt
  $PY poc/finetune/make_domain8_items.py items --train-n 200 --calib-n 20 --shuffle-options none --out $D/items_probe200.pt
}

probe() {  # 1,000 stratified train rows, 1 epoch, script defaults (micro-batch 2, grad-accum 16, checkpointing on)
  data
  $PY poc/finetune/run_ft.py --report $R/probe_${TS}_timing.json -- $BASE poc/finetune/ckpt_probe \
    --items $D/items_probe.pt --calib-max 100 --epochs 1 --micro-batch 2 --grad-accum 16 --device mps \
    > $R/probe_${TS}.log 2>&1
}

aux() {  # 200 rows: no gradient checkpointing; micro-batch 8 x grad-accum 4 (same effective batch 32)
  $PY poc/finetune/run_ft.py --report $R/probe200-nockpt_${TS}_timing.json -- $BASE poc/finetune/ckpt_probe200_nockpt \
    --items $D/items_probe200.pt --calib-max 20 --epochs 1 --micro-batch 2 --grad-accum 16 --device mps --no-checkpointing \
    > $R/probe200-nockpt_${TS}.log 2>&1
  $PY poc/finetune/run_ft.py --report $R/probe200-mb8_${TS}_timing.json -- $BASE poc/finetune/ckpt_probe200_mb8 \
    --items $D/items_probe200.pt --calib-max 20 --epochs 1 --micro-batch 8 --grad-accum 4 --device mps \
    > $R/probe200-mb8_${TS}.log 2>&1
}

aux2() {  # 200 rows: the combination the two aux runs point to
  $PY poc/finetune/run_ft.py --report $R/probe200-mb8-nockpt_${TS}_timing.json -- $BASE poc/finetune/ckpt_probe200_mb8_nockpt \
    --items $D/items_probe200.pt --calib-max 20 --epochs 1 --micro-batch 8 --grad-accum 4 --device mps --no-checkpointing \
    > $R/probe200-mb8-nockpt_${TS}.log 2>&1
}

eval_() {  # CPU fp32; base through the same wrapper reproduces the Track B number (apples to apples)
  ev() { $PY poc/finetune/eval_ckpt.py run --ckpt "$1" --name "$2" --revision "$3" --dataset "$4" --out "$R/${TS}_$2_$5"; }
  FT="local:poc/finetune/ckpt_probe (base $SHA)"
  $PY poc/finetune/eval_ckpt.py devcopy data/evals/ko_klue_ynat_7.jsonl --out-dir $R/dev
  ev $BASE multilingual $SHA data/evals/ko_massive_domain_8.jsonl ko_massive_domain_8
  ev poc/finetune/ckpt_probe ft-probe "$FT" data/evals/ko_massive_domain_8.jsonl ko_massive_domain_8
  ev poc/finetune/ckpt_probe ft-probe "$FT" $D/domain8_dev.jsonl domain8_dev
  ev $BASE multilingual $SHA $D/domain8_dev.jsonl domain8_dev
  ev $BASE multilingual $SHA $R/dev/ko_klue_ynat_7.jsonl ko_klue_ynat_7_dev
  ev poc/finetune/ckpt_probe ft-probe "$FT" $R/dev/ko_klue_ynat_7.jsonl ko_klue_ynat_7_dev
  X="$PY scripts/metrics_extra.py"; M=$R/metrics; mkdir -p $M
  $X summary $R/${TS}_*.json --out $M/probe_${TS}_summary.md --json $M/probe_${TS}_summary.json
  $X parity results/B/20261002-1643_multilingual_ko_massive_domain_8.json $R/${TS}_multilingual_ko_massive_domain_8.json \
    --out $M/probe_${TS}_parity_base_vs_B.md --json $M/probe_${TS}_parity_base_vs_B.json
  for s in ko_massive_domain_8 domain8_dev ko_klue_ynat_7_dev; do
    $X paired $R/${TS}_multilingual_$s.json $R/${TS}_ft-probe_$s.json --out $M/probe_${TS}_paired_$s.md --json $M/probe_${TS}_paired_$s.json
  done
  $PY poc/finetune/eval_ckpt.py overlap $R/${TS}_*_ko_massive_domain_8.json $R/${TS}_*_domain8_dev.json \
    --train $D/domain8_train.jsonl --out $M/probe_${TS}_overlap.md
}

case "${1:-}" in
  probe) probe ;;
  aux) aux ;;
  aux2) aux2 ;;
  eval) eval_ ;;
  *) echo "usage: $0 probe|aux|aux2|eval" >&2; exit 2 ;;
esac
