#!/usr/bin/env python
"""Track D HTTP load on a running laya-serve (03 §6 D6). Latency = send -> parsed JSON (03 §3.3).

  python scripts/bench_http_local.py --url http://127.0.0.1:8000 --questions 1,3 --closed 1,4,8 --open 5,10,20 \
      --duration 60 --batch-states 16,64 --out results/D/<ts>_http_mps.json
closed loop: c workers back to back; a 503 makes the worker wait Retry-After before its next request.
open loop: fixed-rate asyncio scheduler, request i is sent at t0 + i/rps whatever the backlog; both
send->parse and schedule->parse latencies are kept (the latter shows queueing the client caused).
Bodies: Korean ko_massive_domain_8 utterances (pool of 64), 1q = router_v1, 3q = router_v1 + upstream noul + choice.
"""
import argparse
import asyncio
import json
import sys
import time

import httpx

from bench_latency_local import Q_CHOICE, evals_rows, pct, run_card, sh, sha

ROWS = evals_rows("ko_massive_domain_8")[:64]
ROUTER_V1 = ROWS[0]["questions"]["domain"]
QSETS = {1: {"domain": ROUTER_V1},
         3: {"domain": ROUTER_V1, "urgent": {"type": "noul", "instructions": "Does `utterance` express urgency?"},
             "team": Q_CHOICE}}


def body(nq, i):
    return {"state": ROWS[i % len(ROWS)]["state"], "questions": QSETS[nq], "lang": "ko"}


async def send(client, path, payload):
    t = time.perf_counter()
    r = await client.post(path, json=payload)
    try:
        data = r.json()
    except ValueError:
        data = {}
    ms = (time.perf_counter() - t) * 1000
    ok = r.status_code == 200 and ("answers" in data or "results" in data)
    return {"ms": ms, "status": r.status_code, "ok": ok, "retry_after": r.headers.get("retry-after"),
            "infer_ms": float(r.headers.get("x-inference-time-ms", "nan"))}


def summary(recs, duration, extra=None):
    ok = [r for r in recs if r["ok"]]
    lat = [r["ms"] for r in ok] or [float("nan")]
    out = {"requests": len(recs), "ok": len(ok), "errors": len(recs) - len(ok),
           "status_503": sum(r["status"] == 503 for r in recs),
           "retry_after_values": sorted({r["retry_after"] for r in recs if r["retry_after"]}),
           "achieved_rps": round(len(ok) / duration, 2), "p50_ms": pct(lat, 50), "p95_ms": pct(lat, 95),
           "p99_ms": pct(lat, 99), "max_ms": round(max(lat), 1),
           "server_infer_p50_ms": pct([r["infer_ms"] for r in ok] or [float("nan")], 50)}
    if extra:
        out.update(extra)
    return out


async def closed_loop(client, nq, conc, duration):
    recs, end, counter = [], time.perf_counter() + duration, iter(range(10 ** 9))
    async def worker():
        while time.perf_counter() < end:
            rec = await send(client, "/v1/systemone", body(nq, next(counter)))
            recs.append(rec)
            if rec["status"] == 503:  # honour Retry-After before the next request
                await asyncio.sleep(float(rec["retry_after"] or 1))
    t0 = time.perf_counter()
    await asyncio.gather(*(worker() for _ in range(conc)))
    return summary(recs, time.perf_counter() - t0)


async def open_loop(client, nq, rps, duration):
    recs, lags, tasks = [], [], []
    async def one(i, target):
        lags.append(time.perf_counter() - target)
        rec = await send(client, "/v1/systemone", body(nq, i))
        rec["sched_ms"] = (time.perf_counter() - target) * 1000
        recs.append(rec)
    t0 = time.perf_counter()
    for i in range(int(rps * duration)):
        target = t0 + i / rps
        await asyncio.sleep(max(0.0, target - time.perf_counter()))
        tasks.append(asyncio.create_task(one(i, target)))
    await asyncio.gather(*tasks)
    sched = [r["sched_ms"] for r in recs if r["ok"]] or [float("nan")]
    return summary(recs, time.perf_counter() - t0, {"target_rps": rps, "sched_p95_ms": pct(sched, 95),
                                                    "max_send_lag_ms": round(max(lags) * 1000, 2)})


async def batch_bench(client, n, repeat):
    payload = {"states": [ROWS[i % len(ROWS)]["state"] for i in range(n)], "questions": QSETS[1], "lang": "ko"}
    for _ in range(2):
        await send(client, "/v1/systemone/batch", payload)
    recs = [await send(client, "/v1/systemone/batch", payload) for _ in range(repeat)]
    s = summary(recs, sum(r["ms"] for r in recs) / 1000)
    s.update(states=n, states_per_s=round(n * s["ok"] / (sum(r["ms"] for r in recs) / 1000), 1))
    return s


async def main_async(args):
    res = {"title": "D6 HTTP laya-serve", "url": args.url, "run_card": run_card(label=args.label),
           "questions_sha256": {k: sha(v) for k, v in QSETS.items()}, "states_sha256": sha([r["state"] for r in ROWS]),
           "rows": []}
    limits = httpx.Limits(max_connections=64, max_keepalive_connections=64)
    async with httpx.AsyncClient(base_url=args.url, timeout=60, limits=limits) as client:
        res["health"] = (await client.get("/health")).json()
        for nq in args.questions:  # warm-up: every body once (each new MPS shape compiles on first use)
            warm = [await send(client, "/v1/systemone", body(nq, i)) for i in range(len(ROWS))]
            assert all(w["ok"] for w in warm), warm[:3]
        for nq in args.questions:
            for c in args.closed:
                row = dict(mode="closed", questions=nq, concurrency=c, **await closed_loop(client, nq, c, args.duration))
                res["rows"].append(row)
                print(json.dumps(row), flush=True)
            for rps in args.open:
                row = dict(mode="open", questions=nq, **await open_loop(client, nq, rps, args.duration))
                res["rows"].append(row)
                print(json.dumps(row), flush=True)
        for n in args.batch_states:
            row = dict(mode="batch", questions=1, **await batch_bench(client, n, args.batch_repeat))
            res["rows"].append(row)
            print(json.dumps(row), flush=True)
    res["run_card"]["uptime_after"] = sh("uptime")
    return res


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ints = lambda s: [int(x) for x in s.split(",") if x.strip()]
    p.add_argument("--url", default="http://127.0.0.1:8000")
    p.add_argument("--questions", type=ints, default=[1, 3])
    p.add_argument("--closed", type=ints, default=[1, 4, 8])
    p.add_argument("--open", type=ints, default=[5, 10, 20])
    p.add_argument("--duration", type=float, default=60)
    p.add_argument("--batch-states", type=ints, default=[16, 64])
    p.add_argument("--batch-repeat", type=int, default=10)
    p.add_argument("--label", default="")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    res = asyncio.run(main_async(args))
    json.dump(res, open(args.out, "w"), ensure_ascii=False, indent=1)
    keys = list(dict.fromkeys(k for r in res["rows"] for k in r))
    md = ["# %s (%s)" % (res["title"], args.label), "", "health: `%s`" % json.dumps(res["health"]), "",
          "run_card: `%s`" % json.dumps(res["run_card"], ensure_ascii=False), "",
          "| " + " | ".join(keys) + " |", "|" + "---|" * len(keys)]
    md += ["| " + " | ".join(json.dumps(r.get(k)) for k in keys) + " |" for r in res["rows"]]
    open(args.out[:-5] + ".md", "w").write("\n".join(md) + "\n")
    print("wrote", args.out)


if __name__ == "__main__":
    sys.exit(main())
