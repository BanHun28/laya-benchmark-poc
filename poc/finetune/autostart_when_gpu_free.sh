#!/usr/bin/env bash
# P4 본 학습 자동 시작 감시자.
# 다른 프로젝트의 GPU 작업(spectral-compression 큐)이 3분 연속 보이지 않고 poc/finetune/READY 가 있으면
# run_full.sh 를 실행한다. 상태는 results/P4/autostart.log 에 한 줄씩 남긴다(STARTED / FINISHED / FAILED / TIMEOUT).
#   nohup bash poc/finetune/autostart_when_gpu_free.sh >/dev/null 2>&1 &
cd "$(dirname "$0")/../.."
LOG=results/P4/autostart.log
mkdir -p results/P4
echo "$(date '+%F %T') WATCHER_START pid=$$" >> "$LOG"
quiet=0
deadline=$(( $(date +%s) + 12*3600 ))      # 12시간 안에 시작 못 하면 포기하고 알린다
while true; do
  busy=$(ps -Ao args | grep -E 'spectral-compression|run_kt_queue|kt_scores\.py|kt2_layer_sensitivity\.py|kt1_h3\.py' \
         | grep -v -E 'grep|pidinfo|autostart_when_gpu_free' | wc -l | tr -d ' ')
  ready=0; [ -f poc/finetune/READY ] && ready=1
  if [ "$busy" = "0" ]; then quiet=$((quiet+1)); else quiet=0; fi
  echo "$(date '+%F %T') waiting busy=$busy quiet=$quiet ready=$ready" >> "$LOG"
  if [ "$quiet" -ge 3 ] && [ "$ready" = "1" ]; then
    echo "$(date '+%F %T') STARTED run_full.sh (gpu quiet ${quiet} min)" >> "$LOG"
    if bash poc/finetune/run_full.sh > results/P4/full_run_console.log 2>&1; then
      echo "$(date '+%F %T') FINISHED rc=0" >> "$LOG"; exit 0
    else
      rc=$?; echo "$(date '+%F %T') FAILED rc=$rc (see results/P4/full_run_console.log)" >> "$LOG"; exit $rc
    fi
  fi
  if [ "$(date +%s)" -ge "$deadline" ]; then
    echo "$(date '+%F %T') TIMEOUT 12h without a start window (busy=$busy ready=$ready)" >> "$LOG"; exit 2
  fi
  sleep 60
done
