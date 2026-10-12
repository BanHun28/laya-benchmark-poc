#!/usr/bin/env bash
# seed 14 반복 학습의 T9·T10 재시작 감시자 (2026-10-08). 첫 시도는 다른 프로젝트(metastable-ood) 실험 7개와 겹쳐 스왑이
# 가득 차고 T9가 멈춰 중지했다(results/T3arm/PREP_20261008.md "반복 학습 T9 중지"). 그 실험이 3분 연속 보이지 않고,
# 메모리 여유 30% 이상, 디스크 여유 20 GB 이상이면 T9·T10을 이어 돌린다. 상태는 results/T3arm/rep_s14/autostart.log.
#   nohup perl -MPOSIX -e 'setsid; exec @ARGV' bash poc/finetune/autostart_rep_t9t10.sh >/dev/null 2>&1 &
cd "$(dirname "$0")/../.."
LOG=results/T3arm/rep_s14/autostart.log
echo "$(date '+%F %T') WATCHER_START pid=$$" >> "$LOG"
quiet=0
deadline=$(( $(date +%s) + 12*3600 ))
while true; do
  busy=$(ps -Ao args | grep -E 'metastable-ood/\.venv/bin/python3? experiments/' | grep -v grep | wc -l | tr -d ' ')
  mem=$(memory_pressure | awk '/free percentage/ {gsub("%", "", $NF); print $NF}')
  disk=$(df -k . | awk 'NR == 2 {printf "%d", $4 / 1024 / 1024}')
  if [ "$busy" = 0 ] && [ "${mem:-0}" -ge 30 ] && [ "$disk" -ge 20 ]; then quiet=$((quiet + 1)); else quiet=0; fi
  echo "$(date '+%F %T') waiting busy=$busy mem_free=${mem}% disk_gb=$disk quiet=$quiet" >> "$LOG"
  if [ "$quiet" -ge 3 ]; then
    echo "$(date '+%F %T') STARTED T9 T10" >> "$LOG"
    if SEED=14 RUN_TAG=rep_s14 TASKS="T9 T10" bash poc/finetune/run_all_tasks.sh > results/T3arm/rep_s14/autostart_console.log 2>&1; then
      echo "$(date '+%F %T') FINISHED rc=0" >> "$LOG"; exit 0
    else
      rc=$?; echo "$(date '+%F %T') FAILED rc=$rc (see results/T3arm/rep_s14/autostart_console.log)" >> "$LOG"; exit $rc
    fi
  fi
  if [ "$(date +%s)" -ge "$deadline" ]; then
    echo "$(date '+%F %T') TIMEOUT 12h without a start window (busy=$busy mem_free=${mem}% disk_gb=$disk)" >> "$LOG"; exit 2
  fi
  sleep 60
done
