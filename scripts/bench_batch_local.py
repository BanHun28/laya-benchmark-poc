#!/usr/bin/env python
"""Track D batching (03 §6): D4 predict loop vs predict_batch, D5 Router heterogeneous batch, D8 peak RSS.

  D4 --checkpoint multilingual --states data/evals/ko_nsmc_sentiment.jsonl,data/evals/ko_klue_ynat_7.jsonl
     --n 64,256 --batch-size 8,16,32 --sort-by-length both --devices cpu,mps --rounds 3 --interleave
  D5 --router --n 32 --devices cpu,mps       ko/en interleaved, Router(max_loaded=1|2), on_load/on_evict counts
  D8 --memory --n 64 --devices cpu,mps       peak RSS (psutil, 10 ms) during one predict_batch, fresh process per mode
Mixed-length states follow research/scripts/bench_length_batching.py `states_for(mixed)`: each state is one
row plus 0-16 extra rows (seed 13). The question is router_v1 (data/evals/ko_massive_domain_8.jsonl).
Parity follows benchmarks/bench_predict_batch.py `consistency`: argmax flips and max |dp| vs the predict loop.
"""
import argparse
import gc
import json
import os
import random
import statistics
import subprocess
import sys
import threading
import time

from bench_latency_local import CKPTS, ROOT, evals_rows, run_card, sh, sha

EXTRA = [0, 0, 0, 1, 2, 4, 8, 16]


def router_q(lang="ko"):
    return evals_rows("%s_massive_domain_8" % lang)[0]["questions"]


def mixed_states(paths, n):
    texts = [[next(iter(r["state"].values())) for r in evals_rows(os.path.basename(p)[:-6])] for p in paths]
    pool = [t for group in zip(*texts) for t in group]
    rng = random.Random(13)
    return [{"utterance": " ".join([pool[i]] + [pool[rng.randrange(len(pool))] for _ in range(rng.choice(EXTRA))])}
            for i in range(n)]


def parity(ref, other):
    flips, maxd = 0, 0.0
    for a, b in zip(ref, other):
        for qid, x in a["answers"].items():
            y = b["answers"][qid]
            if x["type"] == "noul":
                flips += (x["noul"] >= 0.5) != (y["noul"] >= 0.5)
                maxd = max(maxd, abs(x["noul"] - y["noul"]))
            else:
                px, py = x["probabilities"], y["probabilities"]
                flips += max(px, key=px.get) != max(py, key=py.get)
                maxd = max([maxd] + [abs(px[k] - py[k]) for k in px])
    return {"argmax_flips": int(flips), "max_abs_dp": round(maxd, 6), "compared": len(ref)}


def run_mode(agent, states, q, mode):
    if mode == "loop":
        return [agent.predict(s, q) for s in states]
    bs = int(mode[1:].rstrip("s"))
    return agent.predict_batch(states, q, batch_size=bs, sort_by_length=mode.endswith("s"))


def d4(args, q):
    import laya
    import torch
    modes = ["loop"] + ["b%d%s" % (bs, s) for bs in args.batch_size for s in args.sorts]
    out, cpu_loop = [], {}
    for dev in args.devices:
        agent = laya.load(os.path.join(ROOT, CKPTS[args.checkpoint]), device=dev)
        assert agent.device.type == dev, agent.device
        fwd, slots = agent._forward, {"n": 0}
        def counted(b, _fwd=fwd):
            slots["n"] += b["input_ids"].numel()
            return _fwd(b)
        agent._forward = counted
        for n in args.n:
            states = mixed_states(args.states, n)
            times, results, padded = {m: [] for m in modes}, {}, {}
            for r in range(args.rounds + 1):  # round 0 = warm-up (every MPS shape compiled once), discarded
                order = modes if (r % 2 == 0 or not args.interleave) else modes[::-1]
                for m in order:
                    slots["n"] = 0
                    t = time.perf_counter()
                    res = run_mode(agent, states, q, m)
                    dt = time.perf_counter() - t
                    if r:
                        times[m].append(dt)
                    results[m], padded[m] = res, slots["n"]
                print(dev, n, "round", r, {m: round(times[m][-1], 2) for m in modes if times[m]}, flush=True)
            toks = [res["usage"].get("state_tokens", 0) for res in results["loop"]]
            if dev == "cpu":
                cpu_loop[n] = results["loop"]
            for m in modes:
                row = {"device": dev, "n": n, "mode": m, "median_s": round(statistics.median(times[m]), 3),
                       "times_s": [round(t, 3) for t in times[m]], "padded_slots": padded[m],
                       "states_per_s": round(n / statistics.median(times[m]), 1),
                       "paired_speedup_vs_loop": round(statistics.median(a / b for a, b in zip(times["loop"], times[m])), 3),
                       "dtype": str(agent.dtype_for(1 if m == "loop" else int(m[1:].rstrip("s")))).replace("torch.", "")}
                if m.endswith("s"):
                    row["paired_speedup_sorted_vs_unsorted"] = round(statistics.median(
                        a / b for a, b in zip(times[m[:-1]], times[m])), 3)
                if m != "loop":
                    row["parity_vs_loop"] = parity(results["loop"], results[m])
                if dev != "cpu" and n in cpu_loop:
                    row["parity_vs_cpu_loop"] = parity(cpu_loop[n], results[m])
                row["state_tokens"] = {"min": min(toks), "median": statistics.median(toks), "max": max(toks)}
                out.append(row)
        del agent
        gc.collect()
        if dev == "mps":
            torch.mps.empty_cache()
    return out


class Lifecycle:
    def __init__(self):
        self.loads, self.evicts = [], []

    def on_load(self, ctx):
        self.loads.append(ctx.model)

    def on_evict(self, ctx):
        self.evicts.append(ctx.model)


def d5(args):
    from laya.router import Router
    ko, en = evals_rows("ko_massive_domain_8"), evals_rows("en_massive_domain_8")
    reqs = [{"state": (ko if i % 2 == 0 else en)[i // 2]["state"], "questions": (ko if i % 2 == 0 else en)[0]["questions"]}
            for i in range(args.n[0])]
    out = []
    for dev in args.devices:
        for max_loaded in (1, 2):
            for mode in ("loop", "batch"):
                hook = Lifecycle()
                router = Router(models={k: os.path.join(ROOT, v) for k, v in CKPTS.items()}, device=dev,
                                max_loaded=max_loaded, hooks=[hook])
                for p in (1, 2):  # pass 1 includes the initial loads; pass 2 is steady state
                    n_load, n_evict = len(hook.loads), len(hook.evicts)
                    t = time.perf_counter()
                    res = ([router.predict(r["state"], r["questions"]) for r in reqs] if mode == "loop"
                           else router.predict_batch(reqs))
                    row = {"device": dev, "max_loaded": max_loaded, "mode": mode, "pass": p,
                           "total_s": round(time.perf_counter() - t, 3), "loads": len(hook.loads) - n_load,
                           "evicts": len(hook.evicts) - n_evict,
                           "models": sorted({x["routing"]["model"] for x in res if "routing" in x})}
                    out.append(row)
                    print(json.dumps(row), flush=True)
                router.unload()
                del router
                gc.collect()
    return out


def memory_child(dev, mode, args, q):
    import psutil
    import laya
    import torch
    torch.set_num_threads(10)
    torch.set_num_interop_threads(1)
    agent = laya.load(os.path.join(ROOT, CKPTS[args.checkpoint]), device=dev)
    states = mixed_states(args.states, args.n[0])
    bs = None if mode == "all" else int(mode[1:].rstrip("s"))
    gc.collect()
    proc, gib = psutil.Process(), 1024 ** 3
    mps = lambda: round(torch.mps.driver_allocated_memory() / gib, 3) if dev == "mps" else None
    row = {"device": dev, "mode": mode, "n": len(states), "rss_after_load_gib": round(proc.memory_info().rss / gib, 3),
           "mps_driver_after_load_gib": mps()}
    for call in (1, 2):  # call 1 grows the allocator from the post-load baseline; call 2 runs on what it kept
        samples, stop = [proc.memory_info().rss], threading.Event()
        def sample():
            while not stop.wait(0.01):
                samples.append(proc.memory_info().rss)
        th = threading.Thread(target=sample, daemon=True)
        th.start()
        agent.predict_batch(states, q, batch_size=bs, sort_by_length=mode.endswith("s"))
        samples.append(proc.memory_info().rss)
        stop.set()
        th.join()
        row.update({"call%d_start_rss_gib" % call: round(samples[0] / gib, 3),
                    "call%d_peak_rss_gib" % call: round(max(samples) / gib, 3),
                    "call%d_mps_driver_gib" % call: mps(), "call%d_samples" % call: len(samples)})
    row["peak_minus_load_gib"] = round(max(row["call1_peak_rss_gib"], row["call2_peak_rss_gib"]) - row["rss_after_load_gib"], 3)
    print(json.dumps(row))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    csv = lambda s: [x.strip() for x in s.split(",") if x.strip()]
    ints = lambda s: [int(x) for x in csv(s)]
    p.add_argument("--checkpoint", default="multilingual")
    p.add_argument("--states", type=csv, default=["data/evals/ko_nsmc_sentiment.jsonl", "data/evals/ko_klue_ynat_7.jsonl"])
    p.add_argument("--n", type=ints, default=[64, 256])
    p.add_argument("--batch-size", type=ints, default=[8, 16, 32])
    p.add_argument("--sort-by-length", choices=["false", "true", "both"], default="both")
    p.add_argument("--devices", type=csv, default=["cpu", "mps"])
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--interleave", action="store_true")
    p.add_argument("--router", action="store_true")
    p.add_argument("--memory", action="store_true")
    p.add_argument("--memory-modes", type=csv, default=["b16", "b16s", "all"])
    p.add_argument("--child", nargs=2, help=argparse.SUPPRESS)
    p.add_argument("--out")
    args = p.parse_args()
    args.sorts = {"false": [""], "true": ["s"], "both": ["", "s"]}[args.sort_by_length]
    q = router_q()
    if args.child:
        return memory_child(args.child[0], args.child[1], args, q)
    import torch
    torch.set_num_threads(10)
    torch.set_num_interop_threads(1)
    res = {"run_card": run_card(), "question_sha256": sha(q), "states_sha256": {n: sha(mixed_states(args.states, n)) for n in args.n}}
    t = time.perf_counter()
    if args.router:
        res["title"], res["rows"] = "D5 Router heterogeneous batch", d5(args)
    elif args.memory:
        res["title"], res["rows"] = "D8 peak RSS during predict_batch", []
        for dev in args.devices:
            for mode in args.memory_modes:
                argv = [sys.executable, os.path.abspath(__file__), "--child", dev, mode, "--n", str(args.n[0]),
                        "--checkpoint", args.checkpoint, "--states", ",".join(args.states)]
                proc = subprocess.run(argv, capture_output=True, text=True)
                if proc.returncode:
                    raise RuntimeError(proc.stderr[-2000:])
                row = json.loads([x for x in proc.stdout.splitlines() if x.startswith("{")][-1])
                res["rows"].append(row)
                print(json.dumps(row), flush=True)
    else:
        res["title"], res["rows"] = "D4 state batching", d4(args, q)
    res["wall_s"] = round(time.perf_counter() - t, 1)
    res["run_card"]["uptime_after"] = sh("uptime")
    json.dump(res, open(args.out, "w"), ensure_ascii=False, indent=1)
    keys = [k for k in dict.fromkeys(k for r in res["rows"] for k in r) if k != "times_s"]
    md = ["# " + res["title"], "", "run_card: `%s`" % json.dumps(res["run_card"], ensure_ascii=False), "",
          "| " + " | ".join(keys) + " |", "|" + "---|" * len(keys)]
    md += ["| " + " | ".join(json.dumps(r.get(k), ensure_ascii=False) for k in keys) + " |" for r in res["rows"]]
    open(args.out[:-5] + ".md", "w").write("\n".join(md) + "\n")
    print("wrote", args.out)


if __name__ == "__main__":
    sys.exit(main())
