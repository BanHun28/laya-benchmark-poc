#!/usr/bin/env bash
# Track B metrics (no model call). Every number in summary_<date>.md comes from these metrics_extra outputs.
#   cd /Users/banhun/banhun28/lab/benchmarkforLaya && bash results/B/B_metrics.sh
set -eu
source env.sh
R=results/B; M=$R/metrics; mkdir -p $M
X=".venv/bin/python scripts/metrics_extra.py"
rep() { ls -1 $R/*_"$1"_"$2".json 2>/dev/null | grep -v _FAILED | tail -1; }
KO="ko_massive_domain_8 ko_klue_ynat_7 ko_massive_scenario_18 ko_massive_intent_20opt ko_klue_nli_3 ko_nsmc_sentiment
    ko_kmhas_hate ko_kmhas_type_8 ko_3i4k_speechact_7"

# B2: every report, per split, bootstrap 1000 seed 13
$X summary $(ls -1 $R/2026*.json | grep -v _FAILED) --bootstrap 1000 --seed 13 --out $M/summary_all.md --json $M/summary_all.json

# Korean penalty on the same MASSIVE ids (index parity split on both files)
$X paired "$(rep multilingual ko_massive_domain_8)" "$(rep multilingual en_massive_domain_8)" --out $M/paired_penalty_ko-ml_en-ml.md --json $M/paired_penalty_ko-ml_en-ml.json
$X paired "$(rep english ko_massive_domain_8)" "$(rep english en_massive_domain_8)" --out $M/paired_penalty_ko-en_en-en.md --json $M/paired_penalty_ko-en_en-en.json
$X paired "$(rep multilingual en_massive_domain_8)" "$(rep english en_massive_domain_8)" --out $M/paired_ref_en-ml_en-en.md --json $M/paired_ref_en-ml_en-en.json
$X paired "$(rep multilingual ko_massive_domain_8)" "$(rep english en_massive_domain_8)" --out $M/paired_ref_ko-ml_en-en.md --json $M/paired_ref_ko-ml_en-en.json
if [ -n "$(rep multilingual en_massive_intent_20opt)" ]; then
  $X paired "$(rep multilingual ko_massive_intent_20opt)" "$(rep multilingual en_massive_intent_20opt)" --out $M/paired_penalty20_ko-ml_en-ml.md --json $M/paired_penalty20_ko-ml_en-ml.json
fi

# checkpoints on the same rows: english / typed-decisions vs multilingual (H2), Router vs multilingual parity
for set in $KO; do
  [ -n "$(rep multilingual $set)" ] || continue
  for m in english typed-decisions; do
    [ -n "$(rep $m $set)" ] && $X paired "$(rep $m $set)" "$(rep multilingual $set)" --out $M/paired_${set}_${m}_vs_ml.md --json $M/paired_${set}_${m}_vs_ml.json
  done
  [ -n "$(rep router $set)" ] && $X parity "$(rep multilingual $set)" "$(rep router $set)" --out $M/parity_${set}_router.md --json $M/parity_${set}_router.json
done

# ablations: base (full run, its dev half) vs dev-only variant copies, multilingual
for v in ko_massive_domain_8:ko-instr ko_massive_domain_8:en-desc ko_klue_ynat_7:ko-instr ko_klue_ynat_7:en-desc ko_massive_scenario_18:en-desc; do
  base=${v%%:*}; var=${v##*:}
  [ -n "$(rep multilingual ${base}_${var}_dev)" ] && $X paired "$(rep multilingual $base)" "$(rep multilingual ${base}_${var}_dev)" --split dev \
    --out $M/paired_ablation_${base}_${var}.md --json $M/paired_ablation_${base}_${var}.json
done

# A3 harness identity: the builder file through this harness vs the K2 runs that reproduced upstream
for m in multilingual english; do
  [ -n "$(rep $m ko_massive_intent_20opt)" ] && $X parity results/korean_support/K2_intent20_ko_$m.json "$(rep $m ko_massive_intent_20opt)" \
    --out $M/parity_a3_$m.md --json $M/parity_a3_$m.json
done
for m in multilingual english; do
  [ -n "$(rep $m en_massive_intent_20opt)" ] && $X parity results/korean_support/K2_intent20_en_$m.json "$(rep $m en_massive_intent_20opt)" \
    --out $M/parity_a3_en_$m.md --json $M/parity_a3_en_$m.json
done

# coverage vs covered accuracy, as shipped (no refit), multilingual, PoC sets
$X coverage "$(rep multilingual ko_massive_domain_8)" "$(rep multilingual ko_klue_ynat_7)" --out $M/coverage_ml_poc.md --json $M/coverage_ml_poc.json
echo done
