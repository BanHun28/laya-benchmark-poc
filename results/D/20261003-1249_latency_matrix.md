# D1 latency matrix

run_card: `{"started_at": "2026-10-03 12:49:07 +0900", "argv": ["scripts/bench_latency_local.py", "--checkpoints", "english,multilingual,typed-decisions", "--questions", "1,3,5,10,50", "--devices", "cpu,mps", "--states", "short,long", "--repeat", "10", "--out", "results/D/20261003-1249_latency_matrix.json"], "laya": "0.3.23", "torch": "2.14.1", "transformers": "5.18.0", "python": "3.12.12", "platform": "macOS-26.6.2-arm64-arm-64bit", "threads_intra": 10, "threads_interop": 1, "checkpoint_sha": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851", "env_ref": "results/env/env_20261002-1333.json", "env": {"OMP_NUM_THREADS": "10", "LAYA_MPS_AMP_MIN_ROWS": null, "LAYA_CPU_AMP": null, "LAYA_REVISION": "reviewed", "HF_HUB_OFFLINE": null}, "power": "Now drawing from 'AC Power'", "uptime": "12:49  up 1 day,  4:55, 7 users, load averages: 3.35 3.48 3.53", "git_sha": "n/a (not a git repo)", "uptime_after": "13:04  up 1 day,  5:10, 7 users, load averages: 2.39 3.66 4.13"}`

| checkpoint | device | state | state_tok | q | threads | interop | dtype | median ms | p95 ms | min ms | ms/q | ×1q |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| english | cpu | short | 123 | 1 | 10 | 1 | float32 | 86.6 | 88.2 | 86.2 | 86.6 | 1.0 |
| english | cpu | short | 123 | 3 | 10 | 1 | float32 | 184.4 | 186.5 | 182.5 | 61.5 | 2.13 |
| english | cpu | short | 123 | 5 | 10 | 1 | float32 | 266.8 | 270.4 | 265.6 | 53.4 | 3.08 |
| english | cpu | short | 123 | 10 | 10 | 1 | float32 | 472.8 | 481.2 | 469.6 | 47.3 | 5.46 |
| english | cpu | short | 123 | 50 | 10 | 1 | float32 | 2143.7 | 2191.7 | 2125.2 | 42.9 | 24.75 |
| english | cpu | long | 919 | 1 | 10 | 1 | float32 | 204.5 | 206.8 | 203.8 | 204.5 | 1.0 |
| english | cpu | long | 919 | 3 | 10 | 1 | float32 | 515.1 | 529.5 | 513.0 | 171.7 | 2.52 |
| english | cpu | long | 919 | 5 | 10 | 1 | float32 | 843.3 | 849.2 | 835.9 | 168.7 | 4.12 |
| english | cpu | long | 919 | 10 | 10 | 1 | float32 | 1658.1 | 1670.8 | 1644.7 | 165.8 | 8.11 |
| english | cpu | long | 919 | 50 | 10 | 1 | float32 | 8540.0 | 8621.5 | 8367.4 | 170.8 | 41.76 |
| multilingual | cpu | short | 59 | 1 | 10 | 1 | float32 | 37.7 | 37.9 | 37.2 | 37.7 | 1.0 |
| multilingual | cpu | short | 59 | 3 | 10 | 1 | float32 | 56.4 | 57.8 | 55.9 | 18.8 | 1.49 |
| multilingual | cpu | short | 59 | 5 | 10 | 1 | float32 | 77.5 | 79.1 | 75.6 | 15.5 | 2.06 |
| multilingual | cpu | short | 59 | 10 | 10 | 1 | float32 | 121.4 | 123.4 | 120.6 | 12.1 | 3.22 |
| multilingual | cpu | short | 59 | 50 | 10 | 1 | float32 | 529.4 | 539.2 | 526.8 | 10.6 | 14.04 |
| multilingual | cpu | long | 433 | 1 | 10 | 1 | float32 | 81.8 | 84.2 | 81.1 | 81.8 | 1.0 |
| multilingual | cpu | long | 433 | 3 | 10 | 1 | float32 | 195.8 | 247.8 | 194.2 | 65.3 | 2.39 |
| multilingual | cpu | long | 433 | 5 | 10 | 1 | float32 | 310.5 | 314.5 | 308.0 | 62.1 | 3.79 |
| multilingual | cpu | long | 433 | 10 | 10 | 1 | float32 | 596.5 | 604.2 | 592.8 | 59.6 | 7.29 |
| multilingual | cpu | long | 433 | 50 | 10 | 1 | float32 | 3164.0 | 3235.7 | 3129.6 | 63.3 | 38.67 |
| typed-decisions | cpu | short | 123 | 1 | 10 | 1 | float32 | 89.3 | 91.1 | 88.9 | 89.3 | 1.0 |
| typed-decisions | cpu | short | 123 | 3 | 10 | 1 | float32 | 192.0 | 194.4 | 191.2 | 64.0 | 2.15 |
| typed-decisions | cpu | short | 123 | 5 | 10 | 1 | float32 | 287.7 | 290.5 | 286.0 | 57.5 | 3.22 |
| typed-decisions | cpu | short | 123 | 10 | 10 | 1 | float32 | 507.9 | 511.8 | 505.9 | 50.8 | 5.69 |
| typed-decisions | cpu | short | 123 | 50 | 10 | 1 | float32 | 2316.9 | 2359.9 | 2305.4 | 46.3 | 25.96 |
| typed-decisions | cpu | long | 919 | 1 | 10 | 1 | float32 | 399.6 | 401.8 | 393.7 | 399.6 | 1.0 |
| typed-decisions | cpu | long | 919 | 3 | 10 | 1 | float32 | 1143.6 | 1175.7 | 1131.2 | 381.2 | 2.86 |
| typed-decisions | cpu | long | 919 | 5 | 10 | 1 | float32 | 1685.0 | 1714.7 | 1665.4 | 337.0 | 4.22 |
| typed-decisions | cpu | long | 919 | 10 | 10 | 1 | float32 | 3457.3 | 3544.2 | 3369.5 | 345.7 | 8.65 |
| typed-decisions | cpu | long | 919 | 50 | 10 | 1 | float32 | 16938.1 | 17187.7 | 16736.7 | 338.8 | 42.39 |
| english | mps | short | 123 | 1 | 10 | 1 | float32 | 31.8 | 32.1 | 31.3 | 31.8 | 1.0 |
| english | mps | short | 123 | 3 | 10 | 1 | float32 | 79.6 | 80.0 | 78.5 | 26.5 | 2.51 |
| english | mps | short | 123 | 5 | 10 | 1 | float16 | 130.9 | 131.4 | 129.2 | 26.2 | 4.12 |
| english | mps | short | 123 | 10 | 10 | 1 | float16 | 232.3 | 233.2 | 230.9 | 23.2 | 7.31 |
| english | mps | short | 123 | 50 | 10 | 1 | float16 | 1101.8 | 1105.8 | 1100.9 | 22.0 | 34.69 |
| english | mps | long | 919 | 1 | 10 | 1 | float32 | 85.6 | 86.0 | 84.5 | 85.6 | 1.0 |
| english | mps | long | 919 | 3 | 10 | 1 | float32 | 242.1 | 242.8 | 241.4 | 80.7 | 2.83 |
| english | mps | long | 919 | 5 | 10 | 1 | float16 | 377.4 | 378.4 | 376.1 | 75.5 | 4.41 |
| english | mps | long | 919 | 10 | 10 | 1 | float16 | 747.4 | 748.6 | 745.0 | 74.7 | 8.73 |
| english | mps | long | 919 | 50 | 10 | 1 | float16 | 3723.3 | 3724.8 | 3720.3 | 74.5 | 43.48 |
| multilingual | mps | short | 59 | 1 | 10 | 1 | float32 | 13.8 | 14.4 | 13.4 | 13.8 | 1.0 |
| multilingual | mps | short | 59 | 3 | 10 | 1 | float32 | 22.5 | 22.6 | 22.2 | 7.5 | 1.63 |
| multilingual | mps | short | 59 | 5 | 10 | 1 | float16 | 38.1 | 38.3 | 37.4 | 7.6 | 2.76 |
| multilingual | mps | short | 59 | 10 | 10 | 1 | float16 | 62.4 | 62.6 | 61.0 | 6.2 | 4.52 |
| multilingual | mps | short | 59 | 50 | 10 | 1 | float16 | 265.5 | 266.8 | 264.6 | 5.3 | 19.21 |
| multilingual | mps | long | 433 | 1 | 10 | 1 | float32 | 35.1 | 35.3 | 34.9 | 35.1 | 1.0 |
| multilingual | mps | long | 433 | 3 | 10 | 1 | float32 | 92.2 | 92.5 | 91.3 | 30.7 | 2.63 |
| multilingual | mps | long | 433 | 5 | 10 | 1 | float16 | 147.0 | 147.6 | 145.3 | 29.4 | 4.19 |
| multilingual | mps | long | 433 | 10 | 10 | 1 | float16 | 284.8 | 285.7 | 284.3 | 28.5 | 8.11 |
| multilingual | mps | long | 433 | 50 | 10 | 1 | float16 | 1409.7 | 1413.9 | 1408.9 | 28.2 | 40.16 |
| typed-decisions | mps | short | 123 | 1 | 10 | 1 | float32 | 31.9 | 32.0 | 31.2 | 31.9 | 1.0 |
| typed-decisions | mps | short | 123 | 3 | 10 | 1 | float32 | 79.8 | 80.2 | 78.6 | 26.6 | 2.5 |
| typed-decisions | mps | short | 123 | 5 | 10 | 1 | float16 | 130.8 | 131.8 | 130.2 | 26.2 | 4.11 |
| typed-decisions | mps | short | 123 | 10 | 10 | 1 | float16 | 231.8 | 232.6 | 231.1 | 23.2 | 7.28 |
| typed-decisions | mps | short | 123 | 50 | 10 | 1 | float16 | 1103.2 | 1104.3 | 1101.8 | 22.1 | 34.64 |
| typed-decisions | mps | long | 919 | 1 | 10 | 1 | float32 | 163.1 | 163.6 | 162.6 | 163.1 | 1.0 |
| typed-decisions | mps | long | 919 | 3 | 10 | 1 | float32 | 484.6 | 485.0 | 483.5 | 161.5 | 2.97 |
| typed-decisions | mps | long | 919 | 5 | 10 | 1 | float16 | 740.7 | 741.6 | 738.8 | 148.1 | 4.54 |
| typed-decisions | mps | long | 919 | 10 | 10 | 1 | float16 | 1475.4 | 1480.6 | 1474.4 | 147.5 | 9.05 |
| typed-decisions | mps | long | 919 | 50 | 10 | 1 | float16 | 7753.3 | 7759.6 | 7751.2 | 155.1 | 47.53 |
