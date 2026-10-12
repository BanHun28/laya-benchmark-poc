#!/usr/bin/env bash
# Track C1 option-order probe + router schema v2 dev round. CPU fp32, accuracy only (another heavy process shares
# the machine: latency columns are not claims). Torch threads 10 / interop 1 everywhere: the probe sets them itself,
# laya-evals goes through laya.evals_cli.main behind a two-call prelude because the CLI exposes neither knob.
#   cd /Users/banhun/banhun28/lab/benchmarkforLaya && bash results/C/C_run.sh 1   (then 2, 3)
set -u
source env.sh
R=results/C; S=$R/schemas_v2; L=$R/logs; T=$L/C_run_times.log
D=20261002
mkdir -p $L $S/metrics
touch "$T"

laya_evals() {
  .venv/bin/python -c 'import sys, torch; torch.set_num_threads(10); torch.set_num_interop_threads(1); from laya.evals_cli import main; sys.argv[0] = "laya-evals"; sys.exit(main())' "$@"
}

timed() {  # id cmd...
  local id=$1; shift
  echo "$(date '+%F %T') start $id :: $*" >> "$T"
  local t0 t1 rc; t0=$(date +%s)
  "$@" > "$L/$id.log" 2>&1
  rc=$?; t1=$(date +%s)
  echo "$(date '+%F %T') end   $id exit=$rc secs=$((t1 - t0))" >> "$T"
  return $rc
}

case "${1:-}" in
  1)  # C1 option-order flips, dev halves, original + 5 permutations per item in one process
    timed C1_option_order .venv/bin/python scripts/probe_option_order.py \
      data/evals/ko_massive_domain_8.jsonl data/evals/ko_klue_ynat_7.jsonl data/evals/ko_massive_scenario_18.jsonl \
      --model models/laya-multilingual --device cpu --permutations 5 --seed 13 --split dev --splits results/B/B_splits.json \
      --reference results/B/20261002-1643_multilingual_ko_massive_domain_8.json \
      --reference results/B/20261002-1645_multilingual_ko_klue_ynat_7.json \
      --reference results/B/20261002-1647_multilingual_ko_massive_scenario_18.json \
      --out $R/C1_option_order_$D.json ;;
  2)  # schema variants through laya-evals (multilingual), then v2c at head_max_len 512 as a diagnostic
    for v in v1 v2a v2b v2b_general v2c v2d v2e v2e_general; do
      f=$S/router_${v%_general}_dev; [ "$v" != "${v%_general}" ] && f=${f}_general; f=$f.jsonl
      id="$(date +%Y%m%d-%H%M)_multilingual_$(basename $f .jsonl)"
      timed "$id" laya_evals run "$f" --model multilingual --device cpu --batch-size 16 --slice qid --slice tag \
        --json $S/$id.json --markdown $S/$id.md
    done
    id="$(date +%Y%m%d-%H%M)_multilingual_router_v2c_dev_h512"
    timed "$id" .venv/bin/python - $S/router_v2c_dev.jsonl $S/$id <<'EOF'
# v2c with head_max_len 512 per request: the laya-evals harness (laya.evals.evaluate) over the same torch Router the
# CLI builds, with each request carrying the budget override (Router.predict_batch per-request head_max_len).
import json, sys, torch
torch.set_num_threads(10); torch.set_num_interop_threads(1)
import laya
from laya.evals import Dataset, evaluate, file_fingerprint
from laya.evals_cli import RouterRunner
path, out = sys.argv[1], sys.argv[2]
class Runner(RouterRunner):
    def predict(self, state, questions, model=None):
        return self.router.predict(state, questions, model=model, head_max_len=512)
    def predict_batch(self, states, questions, model=None, batch_size=None, sort_by_length=False):
        return self.router.predict_batch([{"state": s, "questions": questions, "model": model, "head_max_len": 512}
                                          for s in states], batch_size=batch_size, sort_by_length=sort_by_length)
ds = Dataset.from_jsonl(path)
for e in ds.examples:
    e.model = "multilingual"
router = laya.Router(device="cpu", preload=False)
rep = evaluate(Runner(router), ds, batch_size=16, config={"dataset": path, "model": "multilingual", "device": "cpu",
               "dataset_sha256": file_fingerprint(path), "head_max_len": 512})
rep.config = dict(rep.config, revisions=getattr(router, "loaded_revisions", {}))
json.dump(rep.to_json(), open(out + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=2, sort_keys=True)
open(out + ".md", "w", encoding="utf-8").write(rep.to_markdown())
print({k: round(v, 4) for k, v in rep.overall.items()})
EOF
    ;;
  3)  # metrics (no model call): metrics_extra summary per scored variant, paired v1 vs same-row variants, analysis
    rep() { ls -1 $S/*_multilingual_router_"$1".json 2>/dev/null | tail -1; }
    X=".venv/bin/python scripts/metrics_extra.py"
    for v in v1 v2a v2b v2c v2c_h512 v2d v2e; do
      n=${v%_h512}; f=$(rep "${n}_dev${v#$n}")
      timed metrics_summary_$v $X summary "$f" --bootstrap 1000 --seed 13 --out $S/metrics/summary_$v.md --json $S/metrics/summary_$v.json
    done
    for v in v2a v2c v2c_h512 v2d; do
      n=${v%_h512}; f=$(rep "${n}_dev${v#$n}")
      timed metrics_paired_v1_$v $X paired "$(rep v1_dev)" "$f" --split dev --out $S/metrics/paired_v1_$v.md --json $S/metrics/paired_v1_$v.json
    done
    timed metrics_paired_v2a_v2d $X paired "$(rep v2a_dev)" "$(rep v2d_dev)" --split dev --out $S/metrics/paired_v2a_v2d.md --json $S/metrics/paired_v2a_v2d.json
    timed C_schema_v2_analyze .venv/bin/python $R/C_schema_v2_analyze.py $D ;;
  *) echo "usage: $0 1|2|3" >&2; exit 2 ;;
esac
