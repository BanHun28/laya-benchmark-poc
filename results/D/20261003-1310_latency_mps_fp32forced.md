# D1 latency matrix

run_card: `{"started_at": "2026-10-03 13:10:09 +0900", "argv": ["scripts/bench_latency_local.py", "--checkpoints", "multilingual,english", "--questions", "1,3,5,10,50", "--devices", "mps", "--states", "short,long", "--repeat", "10", "--out", "results/D/20261003-1310_latency_mps_fp32forced.json"], "laya": "0.3.23", "torch": "2.14.1", "transformers": "5.18.0", "python": "3.12.12", "platform": "macOS-26.6.2-arm64-arm-64bit", "threads_intra": 10, "threads_interop": 1, "checkpoint_sha": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "env_ref": "results/env/env_20261002-1333.json", "env": {"OMP_NUM_THREADS": "10", "LAYA_MPS_AMP_MIN_ROWS": "100000", "LAYA_CPU_AMP": null, "LAYA_REVISION": "reviewed", "HF_HUB_OFFLINE": null}, "power": "Now drawing from 'AC Power'", "uptime": "13:10  up 1 day,  5:16, 7 users, load averages: 2.25 3.42 3.94", "git_sha": "n/a (not a git repo)", "uptime_after": "13:12  up 1 day,  5:18, 7 users, load averages: 1.68 2.83 3.62"}`

| checkpoint | device | state | state_tok | q | threads | interop | gap ms | dtype | median ms | p95 ms | min ms | ms/q | ×1q |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multilingual | mps | short | 59 | 1 | 10 | 1 | 0 | float32 | 13.5 | 13.8 | 12.9 | 13.5 | 1.0 |
| multilingual | mps | short | 59 | 3 | 10 | 1 | 0 | float32 | 22.2 | 22.4 | 22.0 | 7.4 | 1.65 |
| multilingual | mps | short | 59 | 5 | 10 | 1 | 0 | float32 | 32.9 | 33.4 | 32.5 | 6.6 | 2.44 |
| multilingual | mps | short | 59 | 10 | 10 | 1 | 0 | float32 | 56.9 | 57.3 | 56.0 | 5.7 | 4.22 |
| multilingual | mps | short | 59 | 50 | 10 | 1 | 0 | float32 | 266.3 | 266.7 | 266.0 | 5.3 | 19.76 |
| multilingual | mps | long | 433 | 1 | 10 | 1 | 0 | float32 | 34.9 | 35.1 | 34.6 | 34.9 | 1.0 |
| multilingual | mps | long | 433 | 3 | 10 | 1 | 0 | float32 | 91.3 | 91.8 | 90.4 | 30.4 | 2.62 |
| multilingual | mps | long | 433 | 5 | 10 | 1 | 0 | float32 | 148.5 | 149.0 | 148.1 | 29.7 | 4.26 |
| multilingual | mps | long | 433 | 10 | 10 | 1 | 0 | float32 | 294.6 | 295.7 | 293.8 | 29.5 | 8.45 |
| multilingual | mps | long | 433 | 50 | 10 | 1 | 0 | float32 | 1478.4 | 1480.3 | 1477.2 | 29.6 | 42.37 |
| english | mps | short | 123 | 1 | 10 | 1 | 0 | float32 | 31.6 | 32.2 | 31.2 | 31.6 | 1.0 |
| english | mps | short | 123 | 3 | 10 | 1 | 0 | float32 | 79.5 | 80.0 | 78.7 | 26.5 | 2.51 |
| english | mps | short | 123 | 5 | 10 | 1 | 0 | float32 | 123.4 | 124.0 | 122.9 | 24.7 | 3.9 |
| english | mps | short | 123 | 10 | 10 | 1 | 0 | float32 | 234.8 | 236.4 | 234.0 | 23.5 | 7.42 |
| english | mps | short | 123 | 50 | 10 | 1 | 0 | float32 | 1171.4 | 1172.8 | 1169.8 | 23.4 | 37.01 |
| english | mps | long | 919 | 1 | 10 | 1 | 0 | float32 | 84.9 | 89.4 | 84.3 | 84.9 | 1.0 |
| english | mps | long | 919 | 3 | 10 | 1 | 0 | float32 | 241.2 | 242.1 | 240.1 | 80.4 | 2.84 |
| english | mps | long | 919 | 5 | 10 | 1 | 0 | float32 | 396.4 | 397.3 | 395.6 | 79.3 | 4.67 |
| english | mps | long | 919 | 10 | 10 | 1 | 0 | float32 | 799.7 | 803.1 | 798.5 | 80.0 | 9.42 |
| english | mps | long | 919 | 50 | 10 | 1 | 0 | float32 | 4025.7 | 4041.7 | 4024.3 | 80.5 | 47.42 |
