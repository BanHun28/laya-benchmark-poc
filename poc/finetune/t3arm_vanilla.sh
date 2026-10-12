#!/usr/bin/env bash
# T3arm D: vanilla Laya on CPU fp32, intra-op 10 / inter-op 1, batch 8 (results/T3arm/vanilla/).
#   bash poc/finetune/t3arm_vanilla.sh repro     every english/multilingual report of results/F/jev_cmp/laya/ rerun through
#                                                poc/finetune/eval_ckpt.py (the trained arm's eval path) on its own dataset;
#                                                answers must be byte-identical (t3arm_metrics.py same --require-identical)
#   bash poc/finetune/t3arm_vanilla.sh measure   T9/T10 Jev-format sets and every data/evals/jev_cmp_ext set x english,
#                                                multilingual (eval_ckpt.py on models/laya, models/laya-multilingual) and the
#                                                Router (laya-evals run, no --model, as results/F/jev_cmp/run_laya.sh)
#   bash poc/finetune/t3arm_vanilla.sh summary   t3arm_metrics.py summary over the measure reports
set -euo pipefail
cd "$(dirname "$0")/../.."
source env.sh
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.venv/bin/python; O=results/T3arm/vanilla; F=results/F/jev_cmp/laya
EV="$PY poc/finetune/eval_ckpt.py run --batch-size 8 --threads 10"; M="$PY poc/finetune/t3arm_metrics.py"
SHA=55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851
LAYA_EVALS='import sys, torch; torch.set_num_threads(10); torch.set_num_interop_threads(1)
from laya.evals_cli import main; sys.argv[0] = "laya-evals"; sys.exit(main())'
mkdir -p "$O/repro" "$O/logs"
ckpt_of() { [ "$1" = multilingual ] && echo models/laya-multilingual || echo models/laya; }
timed() { local t0=$SECONDS; "$@"; echo "$(date '+%F %T') $((SECONDS - t0))s $*" >> "$O/logs/run_times.log"; }

repro() {
  local f model set out n=0 bad=0
  for f in "$F"/T*_english.json "$F"/T*_multilingual.json; do
    model=${f##*_}; model=${model%.json}
    # the dataset whose bytes the report scored: its own path, or for the archived T4 v0 reports (path since rebuilt
    # key-only) the _v0 copy with the recorded sha256
    set=$($PY -c 'import hashlib, json, sys; from pathlib import Path
c = json.load(open(sys.argv[1]))["config"]; p = Path(c["dataset"])
for q in (p, p.with_name(p.stem + "_v0.jsonl")):
    if q.exists() and hashlib.sha256(q.read_bytes()).hexdigest() == c["dataset_sha256"]:
        print(q); break
else:
    sys.exit("no file with the sha256 of " + sys.argv[1])' "$f")
    out="$O/repro/$(basename "$f" .json)"
    timed $EV --ckpt "$(ckpt_of $model)" --name "$model" --revision $SHA --dataset "$set" --out "$out" > "$O/logs/repro_$(basename "$f" .json).log" 2>&1
    n=$((n + 1))
    $M same "$f" "$out.json" --json "$out.same.json" --require-identical > /dev/null || { bad=$((bad + 1)); echo "NOT IDENTICAL: $f"; }
  done
  echo "repro: $n reports, $bad not identical" | tee "$O/repro/REPRO_RESULT.txt"
  [ "$bad" = 0 ]
}

sets() {
  echo data/evals/jev_cmp/T9_enron_spam_40.jsonl data/evals/jev_cmp/T10_support_tickets_queue_40.jsonl
  ls data/evals/jev_cmp_ext/T*.jsonl
}

measure() {
  local s name m
  for s in $(sets); do
    name=$(basename "$s" .jsonl)
    for m in english multilingual; do
      [ -s "$O/${name}_$m.json" ] && continue
      timed $EV --ckpt "$(ckpt_of $m)" --name $m --revision $SHA --dataset "$s" --out "$O/${name}_$m" > "$O/logs/${name}_$m.log" 2>&1
    done
    [ -s "$O/${name}_router.json" ] && continue
    timed $PY -c "$LAYA_EVALS" run "$s" --device cpu --batch-size 8 --slice qid --slice model \
      --json "$O/${name}_router.json" --markdown "$O/${name}_router.md" > "$O/logs/${name}_router.log" 2>&1
  done
}

summary() {
  $M summary $(ls "$O"/T*_{english,multilingual,router}.json | sort) --out "$O/vanilla_summary.md" --json "$O/vanilla_summary.json" > /dev/null
  echo "$O/vanilla_summary.md"
}

"$@"
