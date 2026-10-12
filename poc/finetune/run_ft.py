"""Run the upstream MPS fine-tune script unmodified, in-process, and record what it does not print: per-phase
wall time, per-micro-batch time/shape/CE, peak RSS and MPS memory, GPU utilisation, the co-tenant's CPU, an MPS
matmul reference before/after, and which items reached training vs calibration.

    source env.sh && HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 .venv/bin/python poc/finetune/run_ft.py \
        --report results/P4/x_timing.json -- models/laya-multilingual poc/finetune/ckpt_probe \
        --items poc/finetune/data/items_probe.pt --calib-max 100 --epochs 1 --device mps

Everything after `--` goes to the script's own argparse. Instrumentation only wraps module-level functions the
script looks up at call time (print, collate, build_model, save_checkpoint, fit_temperature, prepare_*, train)
and seeds torch (the script never does: its RL noise and head dropout are otherwise unseeded).
`--script` runs another copy of the script (T3arm: poc/finetune/laya_finetune_mps_patched.py). `--zero-step` (T3arm V1)
is for `--epochs 0`: no optimizer step, so the script calibrates and exports the base weights, then writes its final
config into `checkpoint_latest/` too, which only an epoch creates; the runner creates that empty directory first.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import re
import resource
import shutil
import statistics
import subprocess
import sys
import threading
import time
import traceback
from collections import Counter
from pathlib import Path

import psutil
import torch

ROOT = Path(__file__).resolve().parents[2]
FT_SCRIPT = ROOT / "third_party/laya/notebooks/laya_finetune_typed_decisions_mps.py"
COTENANT = re.compile(r"experiments/\S+\.py")  # the other project's GPU jobs (kt1_h3, kt2_*, kt_scores, ...)
T0 = time.perf_counter()
_print = print


def now():
    return time.perf_counter() - T0


def gpu_util():
    out = subprocess.run(["ioreg", "-r", "-d", "1", "-w", "0", "-c", "IOAccelerator"], capture_output=True, text=True).stdout
    m = re.search(r'"Device Utilization %"=(\d+)', out)
    return int(m.group(1)) if m else None


def matmul_tflops(n=4096, k=10):
    """fp32 MPS matmul throughput: a reference for how much of the GPU this process gets right now."""
    a, b = torch.randn(n, n, device="mps"), torch.randn(n, n, device="mps")
    for _ in range(2):
        a @ b
    torch.mps.synchronize()
    t = time.perf_counter()
    for _ in range(k):
        a @ b
    torch.mps.synchronize()
    tf = 2 * n ** 3 * k / (time.perf_counter() - t) / 1e12
    del a, b
    torch.mps.empty_cache()
    return round(tf, 2)


class Recorder:
    def __init__(self):
        self.events, self.calls, self.micro, self.series = [], {}, [], []
        self.srcs = {"train": Counter(), "calibration": Counter()}
        self.pending = None   # (phase, target, mask) of the last collated chunk, waiting for its logits
        self.logits = None
        self.calib = []       # (CE sum, correct count, rows) per calibration chunk
        self.peak = {"rss": 0, "mps_alloc": 0, "mps_driver": 0}
        self.lock = threading.Lock()

    def flush(self):
        """Score the previous chunk from its stashed logits; by now the script's loss.item() has synced."""
        if self.pending is None or self.logits is None:
            self.pending = self.logits = None
            return
        phase, target, mask = self.pending
        logits = self.logits.float().cpu()
        ce = float(-(target * torch.log_softmax(logits.masked_fill(~mask, -1e4), -1)).sum(-1).mean())
        acc = (logits.argmax(-1) == target.argmax(-1)).float()
        if phase == "train":
            self.micro[-1].update(ce=round(ce, 5), acc=float(acc.mean()))
        else:
            self.calib.append((ce * len(acc), float(acc.sum()), len(acc)))
        self.pending = self.logits = None


def instrument(ft, rec, keep_epochs=False):
    def timed(name, fn, info=None):
        def wrapper(*a, **k):
            start = now()
            try:
                return fn(*a, **k)
            finally:
                rec.calls.setdefault(name, []).append(
                    {"start": round(start, 3), "end": round(now(), 3), **(info(a, k) if info else {})})
        return wrapper

    def tprint(*a, **k):
        msg = " ".join(str(x) for x in a)
        t = now()
        rec.flush()  # every script print comes after a loss.item() sync or outside the loops
        rec.events.append((round(t, 3), msg))
        _print("[%8.1fs] %s" % (t, msg), flush=True)

    collate = ft.collate

    def wcollate(items, pad_id):
        t = now()
        rec.flush()
        out = collate(items, pad_id)
        phase = "train" if torch.is_grad_enabled() else "calibration"
        rec.srcs[phase].update(str(it.get("src", "?")).split(":")[0] for it in items)
        rec.pending = (phase, out[4], out[3])
        if phase == "train":
            rec.micro.append({"t": round(t, 4), "rows": len(items), "seq_len": int(out[0].shape[1])})
        return out

    build_model = ft.build_model

    def wbuild_model(*a, **k):
        model = build_model(*a, **k)

        def hook(module, inputs, output):
            rec.logits = output[0].detach()
        model.register_forward_hook(hook)
        return model

    ft.print = tprint
    ft.collate = wcollate
    ft.build_model = timed("build_model", wbuild_model)
    save = timed("save_checkpoint", ft.save_checkpoint, lambda a, k: {"final": bool(k.get("final"))})
    # checkpoint_latest/ is overwritten every epoch and the script has no early stopping: keep a copy per epoch
    keep = timed("keep_epoch_copy", lambda out, epoch: shutil.copytree(Path(out) / "checkpoint_latest",
                                                                       Path(out) / ("epoch_%d" % epoch), dirs_exist_ok=True))

    def wsave(model, tokenizer, cfg, output_dir, epoch, final=False):
        save(model, tokenizer, cfg, output_dir, epoch, final=final)
        if keep_epochs and not final:
            keep(output_dir, epoch)

    ft.save_checkpoint = wsave
    ft.fit_temperature = timed("fit_temperature", ft.fit_temperature, lambda a, k: {"samples": len(a[0])})
    for name in ("prepare_model", "prepare_items", "train"):
        setattr(ft, name, timed(name, getattr(ft, name)))


def sampler(stop, rec, interval=1.0):
    proc = psutil.Process()
    others = [p for p in psutil.process_iter(["pid", "cmdline"]) if COTENANT.search(" ".join(p.info["cmdline"] or []))]
    for p in others:
        p.cpu_percent(None)
    psutil.cpu_percent(None)
    k = 0
    while not stop.wait(interval):
        cur = {"rss": proc.memory_info().rss, "mps_alloc": torch.mps.current_allocated_memory(),
               "mps_driver": torch.mps.driver_allocated_memory()}
        with rec.lock:
            for key, v in cur.items():
                rec.peak[key] = max(rec.peak[key], v)
        if k % 10 == 0:
            other = []
            for p in others:
                try:
                    other.append({"pid": p.pid, "cpu_pct": p.cpu_percent(None),
                                  "rss_gb": round(p.memory_info().rss / 1e9, 2)})
                except psutil.Error:
                    other.append({"pid": p.pid, "gone": True})
            rec.series.append({"t": round(now(), 1), **{key + "_gb": round(v / 1e9, 3) for key, v in cur.items()},
                               "gpu_util_pct": gpu_util(), "sys_cpu_pct": psutil.cpu_percent(None),
                               "sys_mem_used_gb": round(psutil.virtual_memory().used / 1e9, 1), "cotenant": other})
        k += 1


def summarize(rec, args_line, cotenant_found):
    m = re.search(r"micro_batch=(\d+); grad_accum=(\d+); epochs=(\d+)", " ".join(e[1] for e in rec.events))
    micro_batch, grad_accum, epochs = (int(x) for x in m.groups()) if m else (None, None, None)
    n_train = int(re.search(r"Training items: (\d+)", " ".join(e[1] for e in rec.events)).group(1))
    ends = [t for t, msg in rec.events if re.match(r"Epoch \d+/\d+ complete", msg)]
    # micro-batch durations: to the next collate, the last one of an epoch to that epoch's "complete" line
    mb = rec.micro
    per_epoch = math.ceil(n_train / micro_batch)
    for i, x in enumerate(mb):
        e = i // per_epoch
        last = (i + 1) % per_epoch == 0 or i == len(mb) - 1
        x["dur"] = round((ends[e] if last else mb[i + 1]["t"]) - x["t"], 4)
        x["step"] = (i % per_epoch + 1) % grad_accum == 0 or last
    seen, steady, first = set(), [], []
    if not mb:  # --zero-step: no micro-batch ran
        calib_n = sum(n for _, _, n in rec.calib)
        return {"script_args": args_line, "n_train_items": n_train, "micro_batches": 0, "optimizer_steps": 0,
                "calibration_rows": {"n": calib_n, "accuracy": round(sum(a for _, a, _ in rec.calib) / calib_n, 4)
                                     if calib_n else None},
                "temperature_fits": rec.calls.get("fit_temperature", []),
                "item_sources": {k: dict(v) for k, v in rec.srcs.items()}}
    for x in mb:
        key = (x["rows"], x["seq_len"])
        (steady if key in seen else first).append(x)
        seen.add(key)
    med = lambda xs: round(statistics.median(xs), 4) if xs else None  # noqa: E731
    loop_s = sum(x["dur"] for x in mb)
    steps = epochs * math.ceil(per_epoch / grad_accum)
    call = lambda name: rec.calls.get(name, [])  # noqa: E731
    saves = call("save_checkpoint")
    final = [c for c in saves if c["final"]]
    calib_start = next((t for t, msg in rec.events if msg.startswith("Running temperature calibration")), None)
    saved = next((t for t, msg in rec.events if msg.startswith("Model saved")), None)
    train_call = call("train")[0]
    nonstep_steady = [x["dur"] for x in steady if not x["step"]]
    step_steady = [x["dur"] for x in steady if x["step"]]
    phases = {
        "prepare_model": round(sum(c["end"] - c["start"] for c in call("prepare_model")), 2),
        "prepare_items (script; items prebuilt by make_domain8_items.py)":
            round(sum(c["end"] - c["start"] for c in call("prepare_items")), 2),
        "setup (config, tokenizer, build+load model, load items, optimizer)": round(mb[0]["t"] - train_call["start"], 2),
        "train_loop": round(loop_s, 2),
        "epoch_checkpoint_saves": round(sum(c["end"] - c["start"] for c in saves if not c["final"]), 2),
        "epoch_copies (runner --keep-epoch-checkpoints)": round(sum(c["end"] - c["start"] for c in call("keep_epoch_copy")), 2),
        "calibration (forward + fit_temperature)": round(final[0]["start"] - calib_start, 2) if final and calib_start else None,
        "export (final save + configs)": round(saved - final[0]["start"], 2) if final and saved else None,
        "train() total": round(train_call["end"] - train_call["start"], 2),
    }
    ce = [x["ce"] for x in mb if "ce" in x]
    window = max(1, len(ce) // 10)
    calib_n = sum(n for _, _, n in rec.calib)
    return {
        "script_args": args_line, "micro_batch": micro_batch, "grad_accum": grad_accum, "epochs": epochs,
        "n_train_items": n_train, "micro_batches": len(mb), "optimizer_steps": steps, "phases_s": phases,
        "throughput": {"train_items_per_s": round(n_train * epochs / loop_s, 3),
                       "s_per_optimizer_step": round(loop_s / steps, 3),
                       "s_per_micro_batch_mean": round(loop_s / len(mb), 4)},
        "micro_batch_s": {"median_all": med([x["dur"] for x in mb]),
                          "median_repeat_shape_no_step": med(nonstep_steady),
                          "median_repeat_shape_with_step": med(step_steady),
                          "optimizer_step_overhead": round(med(step_steady) - med(nonstep_steady), 4)
                          if step_steady and nonstep_steady else None,
                          "median_first_shape": med([x["dur"] for x in first]),
                          "first_shape_count": len(first), "repeat_shape_count": len(steady),
                          "first_shape_extra_total_s": round(sum(x["dur"] for x in first)
                                                             - len(first) * (med([x["dur"] for x in steady]) or 0), 1)},
        "memory_gb": {"ru_maxrss": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9, 2),
                      "rss_peak_sampled": round(rec.peak["rss"] / 1e9, 2),
                      "mps_current_allocated_peak": round(rec.peak["mps_alloc"] / 1e9, 2),
                      "mps_driver_allocated_peak": round(rec.peak["mps_driver"] / 1e9, 2),
                      "mps_recommended_max": round(torch.mps.recommended_max_memory() / 1e9, 1)},
        "loss_log_script": [msg for _, msg in rec.events if msg.startswith(("epoch ", "Epoch "))],
        "train_ce_windows": [round(statistics.mean(ce[i:i + window]), 4) for i in range(0, len(ce), window)],
        "train_acc_windows": [round(statistics.mean(x["acc"] for x in mb[i:i + window] if "acc" in x), 3)
                              for i in range(0, len(mb), window)],
        "calibration_rows": {"n": calib_n, "ce_before_T": round(sum(c for c, _, _ in rec.calib) / calib_n, 4) if calib_n else None,
                             "accuracy": round(sum(a for _, a, _ in rec.calib) / calib_n, 4) if calib_n else None},
        "temperature_fits": call("fit_temperature"),
        "item_sources": {k: dict(v) for k, v in rec.srcs.items()},
        "cotenant_found": cotenant_found,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--report", required=True)
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--keep-epoch-checkpoints", action="store_true", help="copy checkpoint_latest to epoch_<k> after each epoch")
    p.add_argument("--script", default=str(FT_SCRIPT), help="fine-tune script to run (default: upstream, unmodified)")
    p.add_argument("--zero-step", action="store_true", help="--epochs 0 export of the base weights (see the docstring)")
    p.add_argument("script_args", nargs=argparse.REMAINDER)
    a = p.parse_args()
    script_args = a.script_args[1:] if a.script_args[:1] == ["--"] else a.script_args
    script = Path(a.script).resolve()
    if a.zero_step:
        assert script_args[script_args.index("--epochs") + 1] == "0", "--zero-step needs --epochs 0"
        (Path(script_args[1]) / "checkpoint_latest").mkdir(parents=True, exist_ok=True)
    report = {"script": str(script.relative_to(ROOT)), "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
              "zero_step": a.zero_step, "script_args": script_args, "seed": a.seed,
              "keep_epoch_checkpoints": a.keep_epoch_checkpoints,
              "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "versions": {"torch": torch.__version__, "python": sys.version.split()[0]},
              "threads": {"intra": torch.get_num_threads(), "interop": torch.get_num_interop_threads()}}
    import laya
    report["versions"]["laya"] = laya.__version__
    cotenant = [" ".join(p.info["cmdline"] or []) for p in psutil.process_iter(["cmdline"])
                if COTENANT.search(" ".join(p.info["cmdline"] or []))]
    report["load_before"] = {"gpu_util_pct": gpu_util(), "mps_fp32_matmul_tflops": matmul_tflops(),
                             "cotenant": cotenant, "sys_mem_used_gb": round(psutil.virtual_memory().used / 1e9, 1)}
    _print("load before: %s" % json.dumps(report["load_before"], ensure_ascii=False), flush=True)
    spec = importlib.util.spec_from_file_location("laya_ft_mps", script)
    ft = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ft)
    rec = Recorder()
    instrument(ft, rec, a.keep_epoch_checkpoints)
    torch.manual_seed(a.seed)
    stop = threading.Event()
    th = threading.Thread(target=sampler, args=(stop, rec), daemon=True)
    th.start()
    sys.argv = [str(script)] + script_args
    status = "ok"
    try:
        ft.main()
        rec.flush()
    except BaseException:
        status = "failed"
        report["traceback"] = traceback.format_exc()
        _print(report["traceback"], flush=True)
    finally:
        stop.set()
        th.join()
    report["status"] = status
    report["wall_s"] = round(now(), 2)
    report["load_after"] = {"gpu_util_pct": gpu_util(), "mps_fp32_matmul_tflops": matmul_tflops()}
    if status == "ok":
        report.update(summarize(rec, script_args, bool(cotenant)))
    report["load_series"] = rec.series
    report["events"] = rec.events
    report["micro_batch_trace"] = [[x["t"], x["rows"], x["seq_len"], x.get("dur"), x.get("ce"), x.get("acc")]
                                   for x in rec.micro]
    out = Path(a.report if status == "ok" else a.report.replace(".json", "_FAILED.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    keys = ("phases_s", "throughput", "micro_batch_s", "memory_gb", "calibration_rows", "item_sources")
    _print(json.dumps({k: report.get(k) for k in keys}, ensure_ascii=False, indent=1), flush=True)
    _print("report: %s (wall %.1fs, status %s)" % (out, report["wall_s"], status), flush=True)
    sys.exit(0 if status == "ok" else 1)


if __name__ == "__main__":
    main()
