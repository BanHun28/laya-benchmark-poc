#!/usr/bin/env python
"""Track D in-process latency (03 §6): D1 matrix, D2 thread sweep, D3 cold load, D8 preload RSS.

  D1 --checkpoints english,multilingual,typed-decisions --questions 1,3,5,10,50 --devices cpu,mps --states short,long
  D2 --checkpoints multilingual --questions 1,10 --devices cpu --threads 4,8,10,14 --interop 1,default
  D3 --cold 3 --devices cpu,mps        one fresh process per measurement: import -> laya.load -> first predict
  D8 --rss --devices cpu,mps           RSS after Router.preload of 1/2/3 checkpoints, one process per device
Only `agent.predict()` is inside perf_counter. Questions alternate upstream bench_latency.py
Q_CHOICE / Q_NOUL (`qs(n)`). States: results/D/states_ko.json, built once from data/evals.
"""
import argparse
import gc
import hashlib
import json
import os
import platform
import subprocess
import sys
import time

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_TORCH", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CKPTS = {"english": "models/laya", "multilingual": "models/laya-multilingual",
         "typed-decisions": "models/laya-typed-decisions"}
STATES_FILE = os.path.join(ROOT, "results/D/states_ko.json")
# research/scripts/bench_latency.py; only the noul field reference is changed to our state key.
Q_NOUL = {"type": "noul", "instructions": "Does `text` express urgency?"}
Q_CHOICE = {"type": "choice", "instructions": "Which team should handle this?",
            "criteria": {"billing": "payments", "technical": "bugs and integrations", "sales": "pricing"}}


def qs(n):
    return {"q%d" % i: (Q_NOUL if i % 2 else Q_CHOICE) for i in range(n)}


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def evals_rows(name):
    with open(os.path.join(ROOT, "data/evals", name + ".jsonl"), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip() and not line.startswith("#")]


def build_states():
    """short: first ko MASSIVE utterance of >= 30 tokens plus the following ones until >= 60 tokens;
    long: NSMC / K-MHaS rows interleaved until >= 400 tokens (multilingual tokenizer, JSON state)."""
    from transformers import AutoTokenizer
    toks = {k: AutoTokenizer.from_pretrained(os.path.join(ROOT, CKPTS[k], "tokenizer")) for k in ("multilingual", "english")}
    count = lambda t, k="multilingual": len(toks[k](json.dumps({"text": t}, ensure_ascii=False))["input_ids"])
    def grow(pieces, target):
        text = ""
        for p in pieces:
            text = (text + " " + p).strip()
            if count(text) >= target:
                return text
    utter = [r["state"]["utterance"] for r in evals_rows("ko_massive_domain_8")]
    start = next(i for i, u in enumerate(utter) if count(u) >= 30)
    mix = [x for pair in zip((r["state"]["document"] for r in evals_rows("ko_nsmc_sentiment")),
                             (r["state"]["comment"] for r in evals_rows("ko_kmhas_hate"))) for x in pair]
    states = {"short": {"text": grow(utter[start:], 60)}, "long": {"text": grow(mix, 400)}}
    meta = {k: {"chars": len(v["text"]), "tokens_multilingual": count(v["text"]),
                "tokens_english": count(v["text"], "english")} for k, v in states.items()}
    out = {"states": states, "meta": meta, "source": "ko_massive_domain_8 rows from #%d; ko_nsmc_sentiment + ko_kmhas_hate" % start}
    os.makedirs(os.path.dirname(STATES_FILE), exist_ok=True)
    json.dump(out, open(STATES_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


def load_states():
    return (json.load(open(STATES_FILE, encoding="utf-8")) if os.path.exists(STATES_FILE) else build_states())["states"]


def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception as e:  # noqa: BLE001 - context only
        return "n/a (%s)" % e


def run_card(**extra):
    import laya
    import torch
    import transformers
    snap = os.path.realpath(os.path.join(ROOT, CKPTS["english"]))
    return {"started_at": time.strftime("%Y-%m-%d %H:%M:%S %z"), "argv": sys.argv,
            "laya": laya.__version__, "torch": torch.__version__, "transformers": transformers.__version__,
            "python": platform.python_version(), "platform": platform.platform(),
            "threads_intra": torch.get_num_threads(), "threads_interop": torch.get_num_interop_threads(),
            "checkpoint_sha": os.path.basename(snap), "env_ref": "results/env/env_20261002-1333.json",
            "env": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "LAYA_MPS_AMP_MIN_ROWS", "LAYA_CPU_AMP",
                                                   "LAYA_REVISION", "HF_HUB_OFFLINE")},
            "power": sh("pmset -g batt | head -1"), "uptime": sh("uptime"), "git_sha": "n/a (not a git repo)", **extra}


def pct(ts, q):
    import numpy as np
    return round(float(np.percentile(ts, q)), 2)


def set_threads(intra, interop):
    import torch
    torch.set_num_threads(intra)
    if interop != "default":
        torch.set_num_interop_threads(int(interop))


def measure(agent, state, questions, warmup, repeat, gap_ms=0):
    for _ in range(warmup):
        out = agent.predict(state, questions)
    ts = []
    for _ in range(repeat):
        time.sleep(gap_ms / 1000)  # paced calls (idle gap before each), outside the timed region
        t = time.perf_counter()
        agent.predict(state, questions)
        ts.append((time.perf_counter() - t) * 1000)
    return ts, out


def matrix(args, states):
    import laya
    import torch
    cells = []
    for dev in args.devices:
        for ck in args.checkpoints:
            agent = laya.load(os.path.join(ROOT, CKPTS[ck]), device=dev)
            if agent.device.type != dev:
                raise RuntimeError("device fallback: asked %s, got %s" % (dev, agent.device))
            for intra, gap in [(i, g) for i in args.threads for g in args.gap_ms]:
                torch.set_num_threads(intra)
                for st in args.states:
                    for n in args.questions:
                        warm = args.warmup + (1 if dev == "mps" else 0)  # +1 per new shape on MPS (03 §3.3)
                        ts, out = measure(agent, states[st], qs(n), warm, args.repeat, gap)
                        u = out["usage"]
                        cell = {"checkpoint": ck, "device": dev, "state": st, "questions": n, "threads": intra, "gap_ms": gap,
                                "interop": torch.get_num_interop_threads(), "dtype": str(agent.dtype_for(n)).replace("torch.", ""),
                                "state_tokens": u.get("state_tokens"), "truncated": u.get("truncated"),
                                "median_ms": pct(ts, 50), "p95_ms": pct(ts, 95), "min_ms": round(min(ts), 2),
                                "samples_ms": [round(t, 2) for t in ts]}
                        cell["ms_per_question"] = round(cell["median_ms"] / n, 2)
                        cells.append(cell)
                        print("%-15s %-3s %-5s %2dq t%-2d gap%-4d %-8s med %9.1f p95 %9.1f min %9.1f ms (%.1f ms/q)"
                              % (ck, dev, st, n, intra, gap, cell["dtype"], cell["median_ms"], cell["p95_ms"],
                                 cell["min_ms"], cell["ms_per_question"]), flush=True)
            del agent
            gc.collect()
            if dev == "mps":
                torch.mps.empty_cache()
    for c in cells:  # question-count slope: 10q/1q and 50q/1q from medians of the same config
        base = next((b for b in cells if b["questions"] == 1 and all(b[k] == c[k] for k in
                     ("checkpoint", "device", "state", "threads", "interop", "gap_ms"))), None)
        c["ratio_vs_1q"] = round(c["median_ms"] / base["median_ms"], 2) if base else None
    return cells


def child_json(argv):
    p = subprocess.run([sys.executable, os.path.abspath(__file__)] + argv, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-2000:])
    lines = [line for line in p.stdout.splitlines() if line.startswith("{")]
    return json.loads(lines[-1]), [line for line in p.stderr.splitlines() if "arn" in line][:10]


def cold_child(ck, dev, args):
    t0 = time.perf_counter()
    import laya
    import torch
    set_threads(args.threads[0], args.interop[0])
    t1 = time.perf_counter()
    agent = laya.load(os.path.join(ROOT, CKPTS[ck]), device=dev)
    t2 = time.perf_counter()
    state, q = load_states()["short"], qs(3)
    agent.predict(state, q)
    t3 = time.perf_counter()
    agent.predict(state, q)
    t4 = time.perf_counter()
    from transformers import AutoTokenizer
    AutoTokenizer.from_pretrained(os.path.join(ROOT, CKPTS[ck], "tokenizer"))  # re-parse, file cache warm
    t5 = time.perf_counter()
    print(json.dumps({"checkpoint": ck, "device": str(agent.device), "import_s": round(t1 - t0, 3),
                      "load_s": round(t2 - t1, 3), "first_predict_s": round(t3 - t2, 3),
                      "second_predict_s": round(t4 - t3, 3), "time_to_first_answer_s": round(t3 - t0, 3),
                      "tokenizer_reparse_s": round(t5 - t4, 3), "torch": torch.__version__}))


def rss_child(dev, args):
    import psutil
    import torch
    from laya.router import Router
    set_threads(args.threads[0], args.interop[0])
    proc, gib = psutil.Process(), 1024 ** 3
    mps = lambda: ({"mps_current_gib": round(torch.mps.current_allocated_memory() / gib, 3),
                    "mps_driver_gib": round(torch.mps.driver_allocated_memory() / gib, 3)} if dev == "mps" else {})
    rows = [{"loaded": [], "rss_gib": round(proc.memory_info().rss / gib, 3), **mps()}]
    router = Router(models={k: os.path.join(ROOT, v) for k, v in CKPTS.items()}, device=dev, max_loaded=3)
    names, state = ["multilingual", "english", "typed-decisions"], load_states()["short"]
    for k in range(1, 4):
        router.preload(names[:k])
        row = {"loaded": names[:k], "rss_gib": round(proc.memory_info().rss / gib, 3), **mps()}
        for n in names[:k]:
            router.predict(state, qs(3), model=n)
        row.update({"rss_after_predict_gib": round(proc.memory_info().rss / gib, 3),
                    **{k2 + "_after_predict": v for k2, v in mps().items()}})
        rows.append(row)
    print(json.dumps({"device": dev, "rows": rows}))


def to_md(res):
    lines = ["# %s" % res["title"], "", "run_card: `%s`" % json.dumps(res["run_card"], ensure_ascii=False), ""]
    if res.get("cells"):
        lines += ["| checkpoint | device | state | state_tok | q | threads | interop | gap ms | dtype | median ms | p95 ms | min ms | ms/q | ×1q |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        lines += ["| %(checkpoint)s | %(device)s | %(state)s | %(state_tokens)s | %(questions)d | %(threads)d | %(interop)d | %(gap_ms)g | "
                  "%(dtype)s | %(median_ms).1f | %(p95_ms).1f | %(min_ms).1f | %(ms_per_question).1f | %(ratio_vs_1q)s |" % c
                  for c in res["cells"]]
    for key in ("cold", "rss"):
        for row in res.get(key, []):
            lines.append("- `%s`" % json.dumps(row, ensure_ascii=False))
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    csv = lambda s: [x.strip() for x in s.split(",") if x.strip()]
    p.add_argument("--checkpoints", type=csv, default=list(CKPTS))
    p.add_argument("--questions", type=lambda s: [int(x) for x in csv(s)], default=[1, 3, 5, 10, 50])
    p.add_argument("--devices", type=csv, default=["cpu", "mps"])
    p.add_argument("--states", type=csv, default=["short", "long"])
    p.add_argument("--threads", type=lambda s: [int(x) for x in csv(s)], default=[10])
    p.add_argument("--interop", type=csv, default=["1"])
    p.add_argument("--repeat", type=int, default=10)
    p.add_argument("--warmup", type=int, default=3)
    p.add_argument("--gap-ms", type=lambda s: [float(x) for x in csv(s)], default=[0.0],
                   help="idle gap before each timed call (paced traffic); 0 = back to back")
    p.add_argument("--cold", type=int, default=0, help="D3: repetitions, one fresh process each")
    p.add_argument("--rss", action="store_true", help="D8: RSS after Router.preload of 1/2/3 checkpoints")
    p.add_argument("--build-states", action="store_true")
    p.add_argument("--child", nargs="+", help=argparse.SUPPRESS)
    p.add_argument("--out")
    args = p.parse_args()
    if args.build_states:
        print(json.dumps(build_states()["meta"], ensure_ascii=False))
        return
    if args.child:
        return cold_child(args.child[1], args.child[2], args) if args.child[0] == "cold" else rss_child(args.child[1], args)
    if not args.cold and not args.rss and len(args.interop) > 1:  # interop is fixed per process: one child each
        cells = []
        for io in args.interop:
            tmp = "%s.interop-%s.json" % (args.out, io)
            argv = [a for a in sys.argv[1:]]
            argv[argv.index("--interop") + 1], argv[argv.index("--out") + 1] = io, tmp
            subprocess.run([sys.executable, os.path.abspath(__file__)] + argv, check=True)
            cells += json.load(open(tmp))["cells"]
            os.remove(tmp)
            os.remove(tmp[:-5] + ".md")
        res = {"title": "D2 thread sweep", "run_card": run_card(interop_values=args.interop), "cells": cells}
    else:
        set_threads(args.threads[0], args.interop[0])
        states = load_states()
        res = {"title": "in-process latency", "states_sha256": sha(states), "questions_sha256": sha(qs(max(args.questions))),
               "run_card": run_card()}
        t = time.perf_counter()
        if args.cold:
            res["title"], res["cold"] = "D3 cold load", []
            for rep in range(args.cold):
                for ck in args.checkpoints:
                    for dev in args.devices:
                        s = time.perf_counter()
                        row, warns = child_json(["--child", "cold", ck, dev, "--threads", str(args.threads[0]),
                                                 "--interop", args.interop[0]])
                        row.update({"rep": rep + 1, "process_wall_s": round(time.perf_counter() - s, 3), "warnings": warns})
                        res["cold"].append(row)
                        print(json.dumps(row), flush=True)
        elif args.rss:
            res["title"], res["rss"] = "D8 preload RSS", []
            for dev in args.devices:
                row, warns = child_json(["--child", "rss", dev, "--threads", str(args.threads[0]), "--interop", args.interop[0]])
                res["rss"].append(dict(row, warnings=warns))
                print(json.dumps(row), flush=True)
        else:
            res["title"], res["cells"] = "D1 latency matrix", matrix(args, states)
        res["wall_s"] = round(time.perf_counter() - t, 1)
        res["run_card"]["uptime_after"] = sh("uptime")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json.dump(res, open(args.out, "w"), ensure_ascii=False, indent=1)
    open(args.out[:-5] + ".md", "w").write(to_md(res))
    print("wrote", args.out)


if __name__ == "__main__":
    sys.exit(main())
