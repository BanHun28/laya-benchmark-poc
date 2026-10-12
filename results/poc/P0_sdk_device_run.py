"""P0 instrumented SDK run: the 05_poc_plan.md:339-348 snippet for one device, plus recording and timing.

    .venv/bin/python results/poc/P0_sdk_device_run.py mps results/poc/P0_sdk_mps.json
    .venv/bin/python results/poc/P0_sdk_device_run.py cpu results/poc/P0_sdk_cpu.json

One process per device so the first call is a cold call for that process. Timing: first call reported
separately, 3 warm-up calls discarded, median of the next 10.
"""
import json
import os
import statistics
import sys
import time
import warnings

import torch

# 02_environment_setup.md:335. set_num_interop_threads must run before any parallel work, hence before the load.
torch.set_num_threads(10)
torch.set_num_interop_threads(1)

import laya  # noqa: E402

dev, out = sys.argv[1], sys.argv[2]
qs = {**json.load(open("poc/schema/triage_v1.json"))["questions"],
      **json.load(open("poc/schema/gateway_v1.json"))["questions"]}
msg = {"message": "지난달 요금이 두 번 결제됐어요. 오늘 안에 환불 안 되면 해지하겠습니다."}

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    t = time.perf_counter()
    a = laya.load("models/laya-multilingual", device=dev)
    load_s = time.perf_counter() - t

    def call():
        t0 = time.perf_counter()
        r = a.predict(msg, qs, min_confidence=0.7)
        return r, (time.perf_counter() - t0) * 1000.0

    first, first_ms = call()
    warm_ms = [call()[1] for _ in range(3)]
    timed = [call() for _ in range(10)]

timed_ms = [ms for _, ms in timed]
record = {
    "device": dev,
    "agent_device": str(a.device),
    "versions": {"torch": torch.__version__, "laya": laya.__version__},
    "threads": {"intra_op": torch.get_num_threads(), "inter_op": torch.get_num_interop_threads(),
                "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS")},
    "agent_dtype": str(a.dtype),
    "dtype_for_7": str(a.dtype_for(7)),
    "mps_amp_min_rows": a.mps_amp_min_rows,
    "LAYA_MPS_AMP_MIN_ROWS": os.environ.get("LAYA_MPS_AMP_MIN_ROWS"),
    "load_s": round(load_s, 3),
    "first_call_ms": round(first_ms, 2),
    "warmup_ms": [round(x, 2) for x in warm_ms],
    "timed_ms": [round(x, 2) for x in timed_ms],
    "median_ms": round(statistics.median(timed_ms), 2),
    "min_ms": round(min(timed_ms), 2),
    "max_ms": round(max(timed_ms), 2),
    "answers_identical_across_calls": all(json.dumps(r["answers"]) == json.dumps(first["answers"]) for r, _ in timed),
    "has_routing_key": "routing" in first,
    "warnings": ["%s: %s" % (w.category.__name__, w.message) for w in caught],
    "result": first,
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(record, fh, ensure_ascii=False, indent=2)
print(json.dumps({k: v for k, v in record.items() if k != "result"}, ensure_ascii=False))
