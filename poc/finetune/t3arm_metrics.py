"""T3arm metrics over laya-evals-format reports (poc/finetune/eval_ckpt.py run, or `laya-evals run --json`). No model call.

    .venv/bin/python poc/finetune/t3arm_metrics.py summary REPORT... --out X.md --json X.json
    .venv/bin/python poc/finetune/t3arm_metrics.py same REF OTHER --json X.json     # answer-level identity (D, V1)
    .venv/bin/python poc/finetune/t3arm_metrics.py paired A B --json X.json         # B vs A on the same decisions
    .venv/bin/python poc/finetune/t3arm_metrics.py select DEV_REPORT... --json X.json  # epoch choice by dev accuracy
    .venv/bin/python poc/finetune/t3arm_metrics.py diag --task T3 --timing R.json --select S.json --selected-ckpt DIR --out X.json
    .venv/bin/python poc/finetune/t3arm_metrics.py estimate --english R... --multilingual R... --task T1:ITEMS.pt:2 ... --out X.json

`summary` is results/F/jev_cmp/laya_summary.py's port of research/scripts/bench_local.py `metrics` over every decision
(score included): accuracy (noul p(true) >= 0.5) with Wilson 95% CI, macro-F1, Brier, ECE (15 bins), NLL, mean
confidence; T1 files with a teacher-distribution file add Part B's soft accuracy, Brier vs soft, score MAE and
accuracy against the dataset `label` (what upstream's 0.766 / 0.362 count); score questions add MAE |E[level] - gold|.
Reports of the same T7 language family and model are also pooled (`<prefix>_ALL`).
`same`: identical answer dicts, argmax agreement and max |dp| per decision, overall metrics without timing.
`paired`: exact McNemar on decision correctness, accuracy delta B - A.
`select`: the dev report with the highest accuracy; a tie goes to the earlier epoch (docs/11 §4; the driver lists the epoch
copies in order and the final export, = last epoch + fitted temperature, last).
"""
import argparse
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from metrics_extra import mcnemar_exact  # noqa: E402

_spec = importlib.util.spec_from_file_location("laya_summary", ROOT / "results/F/jev_cmp/laya_summary.py")
LS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(LS)
GOLD = {"data/evals/jev_cmp/T1_typed_decisions_40.jsonl": ROOT / "results/F/jev_cmp/t1_gold_dists.json",
        "data/evals/jev_cmp_ext/T1_typed_decisions_test400.jsonl":
            ROOT / "data/evals/jev_cmp_ext/T1_typed_decisions_test400_gold_dists.json"}
T7 = re.compile(r"^(T7_massive_intent_10opt)_(en|de|ja|zh-CN|ko)_(.*)$")


def one(path):
    rep, ds = LS.decisions(Path(path))
    m = LS.metrics(ds)
    m.update(report=str(Path(path).resolve().relative_to(ROOT)) if Path(path).resolve().is_relative_to(ROOT) else str(path),
             dataset=rep["config"]["dataset"], dataset_sha256=rep["config"]["dataset_sha256"],
             model=rep["config"].get("model") or "router", answered_by=dict(_count(d["model"] for d in ds)),
             by_type={t: LS.metrics([d for d in ds if d["type"] == t])["accuracy"] for t in sorted({d["type"] for d in ds})})
    if rep["config"]["dataset"] in GOLD:
        gold = json.loads(GOLD[rep["config"]["dataset"]].read_text(encoding="utf-8"))["decisions"]
        m.update({k: v for k, v in LS.t1_extra(ds, gold).items() if k not in ("by_workflow",)})
    sc = [d for d in ds if d["type"] == "score"]
    if sc and rep["config"]["dataset"] not in GOLD:
        e = [abs(float((np.arange(len(d["p"])) * np.asarray(d["p"])).sum()) - d["gold"]) for d in sc]
        m.update(score_mae_expected_level=float(np.mean(e)), within_1_level=float(np.mean([x <= 1 for x in e])))
        if "score_mae" in rep["overall"]:
            m["laya_evals_score_mae"] = rep["overall"]["score_mae"]
    return rep, ds, m


def _count(xs):
    out = defaultdict(int)
    for x in xs:
        out[x] += 1
    return out


def cmd_summary(a):
    res, fam = [], defaultdict(list)
    for path in a.reports:
        rep, ds, m = one(path)
        res.append(m)
        g = T7.match(Path(rep["config"]["dataset"]).stem)
        if g:
            fam["%s_ALL_%s|%s" % (g.group(1), g.group(3), m["model"])].append(ds)
    for key, groups in fam.items():
        if len(groups) > 1:
            ds = [d for g in groups for d in g]
            m = LS.metrics(ds)
            m.update(report="pooled %d files" % len(groups), dataset=key.split("|")[0], model=key.split("|")[1])
            res.append(m)
    f = lambda x: "-" if x is None else "%.3f" % x  # noqa: E731
    L = ["| set | model | n | accuracy [Wilson 95%] | macro-F1 | Brier | ECE | NLL | mean conf | extra |", "|" + "---|" * 10]
    for m in res:
        extra = []
        for k in ("accuracy_vs_upstream_label", "soft_accuracy", "brier_vs_soft", "score_mae", "score_mae_expected_level",
                  "within_1_level"):
            if m.get(k) is not None:
                extra.append("%s %.3f" % (k, m[k]))
        L.append("| %s | %s | %d | %d/%d = %.3f [%.3f, %.3f] | %s | %.3f | %.3f | %.3f | %.3f | %s |" % (
            Path(m["dataset"]).stem, m["model"], m["n"], m["correct"], m["n"], m["accuracy"], *m["wilson"], f(m["macro_f1"]),
            m["brier"], m["ece"], m["nll"], m["mean_confidence"], "; ".join(extra)))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8")
    print("\n".join(L))


def _answer_view(c):
    """(argmax label, probabilities in a fixed order) of one report case, from the case alone."""
    a = c["answer"]
    if a["type"] == "noul":
        return a["noul"] >= 0.5, [1 - a["noul"], a["noul"]]
    probs = a["probabilities"]
    keys = list(probs)
    pred = a["choice"] if a["type"] == "choice" else int(max(range(len(keys)), key=lambda i: probs[keys[i]]))
    return pred, [probs[k] for k in keys]


def cmd_same(a):
    """Case-by-case identity of two reports on the same dataset bytes (no dataset read: an archived report's path may
    now hold other bytes, e.g. results/F/jev_cmp/laya/T4_banking77_10opt_40_v0_*.json)."""
    ra, rb = (json.loads(Path(p).read_text(encoding="utf-8")) for p in (a.ref, a.other))
    ca, cb = ra["cases"], rb["cases"]
    assert ra["config"]["dataset_sha256"] == rb["config"]["dataset_sha256"] and len(ca) == len(cb)
    assert all((x["qid"], x["expected"]) == (y["qid"], y["expected"]) for x, y in zip(ca, cb))
    va, vb = [_answer_view(c) for c in ca], [_answer_view(c) for c in cb]
    dp = [max(abs(x - y) for x, y in zip(pa, pb)) for (_, pa), (_, pb) in zip(va, vb)]
    strip = lambda o: {k: v for k, v in o.items() if not k.endswith("_ms")}  # noqa: E731
    out = {"ref": a.ref, "other": a.other, "dataset_sha256": ra["config"]["dataset_sha256"], "decisions": len(ca),
           "answers_identical": sum(x["answer"] == y["answer"] for x, y in zip(ca, cb)),
           "argmax_agreement": sum(x[0] == y[0] for x, y in zip(va, vb)),
           "correct_identical": sum(x["correct"] == y["correct"] for x, y in zip(ca, cb)),
           "max_abs_dp": max(dp), "mean_abs_dp": float(np.mean(dp)),
           "overall_identical_except_timing": strip(ra["overall"]) == strip(rb["overall"]),
           # argmax accuracy (score answers carry correct=None in laya-evals reports)
           "accuracy": [float(np.mean([v[0] == c["expected"] for v, c in zip(vs, ca)])) for vs in (va, vb)],
           "ece": [ra["overall"].get("ece"), rb["overall"].get("ece")]}
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out))
    if a.require_identical and out["answers_identical"] != out["decisions"]:
        sys.exit(1)


def cmd_paired(a):
    _, da = LS.decisions(Path(a.a))
    _, db = LS.decisions(Path(a.b))
    assert [(d["row"], d["qid"]) for d in da] == [(d["row"], d["qid"]) for d in db]
    ok_a = [d["pred"] == d["gold"] for d in da]
    ok_b = [d["pred"] == d["gold"] for d in db]
    b = sum(y and not x for x, y in zip(ok_a, ok_b))
    c = sum(x and not y for x, y in zip(ok_a, ok_b))
    out = {"a": a.a, "b": a.b, "n": len(da), "acc_a": float(np.mean(ok_a)), "acc_b": float(np.mean(ok_b)),
           "delta_b_minus_a": float(np.mean(ok_b) - np.mean(ok_a)), "b_only": b, "a_only": c, "mcnemar_p": mcnemar_exact(b, c)}
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out))


def cmd_select(a):
    accs = []
    for path in a.reports:
        _, ds = LS.decisions(Path(path))
        accs.append(LS.metrics(ds)["accuracy"])
    best = max(range(len(accs)), key=lambda i: (accs[i], -i))
    out = {"reports": a.reports, "dev_accuracy": accs, "selected": a.reports[best], "selected_index": best,
           "rule": "highest dev accuracy; a tie goes to the earlier epoch (docs/11 §4)"}
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out))


def cmd_diag(a):
    """Training diagnostics of one task: loss/acc windows, dev per epoch and the choice, train-vs-dev gap, temperatures,
    option-order flip on the 40 dev rows, run_ft throughput and memory."""
    t = json.loads(Path(a.timing).read_text(encoding="utf-8"))
    sel = json.loads(Path(a.select).read_text(encoding="utf-8"))
    cfg = json.loads((Path(a.selected_ckpt) / "rl_agent_config.json").read_text())
    dev_sel = sel["dev_accuracy"][sel["selected_index"]]
    _, ds0 = LS.decisions(Path(a.ep0))
    _, dss = LS.decisions(Path(sel["selected"]))
    acc0 = LS.metrics(ds0)["accuracy"]

    def recall(ds):
        tot, ok = defaultdict(int), defaultdict(int)
        for d in ds:
            key = "%s=%s" % (d["qid"], d["gold"]) if len({x["qid"] for x in ds}) > 1 else str(d["gold"])
            tot[key] += 1
            ok[key] += d["pred"] == d["gold"]
        return {k: round(ok[k] / tot[k], 4) for k in sorted(tot)}
    raw = cfg.get("temperature") or []
    out = {"task": a.task, "timing_report": a.timing, "status": t.get("status"),
           "throughput": t.get("throughput"), "phases_s": t.get("phases_s"), "memory_gb": t.get("memory_gb"),
           "optimizer_steps": t.get("optimizer_steps"), "n_train_items": t.get("n_train_items"),
           "loss_log_script": t.get("loss_log_script"), "train_ce_windows": t.get("train_ce_windows"),
           "train_acc_windows": t.get("train_acc_windows"), "calibration_rows": t.get("calibration_rows"),
           "temperature_fits_script": t.get("temperature_fits"),
           "dev": {"epoch0_vanilla": {"report": a.ep0, "accuracy": acc0}, "reports": sel["reports"],
                   "accuracy": sel["dev_accuracy"], "selected": sel["selected"], "rule": sel["rule"]},
           "training_failed": all(x < acc0 for x in sel["dev_accuracy"]),
           "class_recall_dev": {"epoch0_vanilla": recall(ds0), "selected": recall(dss)},
           "train_vs_dev_gap": {"train_acc_last_window": (t.get("train_acc_windows") or [None])[-1], "dev_acc_selected": dev_sel,
                                "gap": None if not t.get("train_acc_windows") else round(t["train_acc_windows"][-1] - dev_sel, 4),
                                "note": "train acc = argmax vs target on each micro-batch's training forward (dropout on), last 10%"},
           "selected_ckpt": a.selected_ckpt, "selected_temperature": cfg.get("temperature"),
           "temperature_clamp": {"script_fit_range": [0.1, 10.0], "load_range": [0.5, 5.0],
                                 "outside_load_range": [t for t in raw if not 0.5 <= t <= 5.0],
                                 "at_script_bound": [t for t in raw if t in (0.1, 10.0)],
                                 "default_1.2_for_types_without_calibration_rows": [i for i, t in enumerate(raw) if t == 1.2]},
           "selected_temperature_by_options": cfg.get("temperature_by_options"),
           "selected_max_len": [cfg.get("max_len"), cfg.get("head_max_len")]}
    if a.calibrate_json and Path(a.calibrate_json).exists():
        out["recalibrated_epoch"] = json.loads(Path(a.calibrate_json).read_text(encoding="utf-8").strip().splitlines()[-1])
    if a.flip and Path(a.flip).exists():
        f = json.loads(Path(a.flip).read_text(encoding="utf-8"))
        m = f["sets"][0]["metrics"]
        out["option_order_flip_dev40"] = {k: m[k] for k in ("n_items", "n_options", "orig_accuracy", "flip_rate_per_perm",
                                                            "flip_rate_per_perm_ci", "any_flip_rate", "perm_accuracy_mean")}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("task", "dev", "training_failed", "train_vs_dev_gap", "selected_temperature")},
                     default=float))


def _micro_batches(lens, n_calib, epochs, micro_batch=8, grad_accum=4):
    """The script's train loop over item lengths (slot order): per micro-batch (rows, padded length, optimizer step?)."""
    import random as _r
    order = list(range(len(lens)))
    _r.Random(20260922).shuffle(order)
    train = [lens[i] for i in sorted(order[n_calib:])]
    out = []
    for epoch in range(epochs):
        _r.Random(42 + epoch).shuffle(train)
        n = 0
        for start in range(0, len(train), micro_batch):
            chunk = train[start:start + micro_batch]
            n += 1
            out.append((len(chunk), max(chunk), n % grad_accum == 0 or start + micro_batch >= len(train)))
    return out


def cmd_estimate(a):
    """Train-loop time per task from a least-squares fit of measured micro-batch durations (run_ft micro_batch_trace):
    d = c0 + c1 * rows * padded_len + c2 * [optimizer step], first-shape micro-batches left out; one fit per base."""
    import torch
    fits = {}
    for base, reports in (("english", a.english), ("multilingual", a.multilingual)):
        X, y = [], []
        for rp in reports:
            r = json.loads(Path(rp).read_text(encoding="utf-8"))
            mb, grad_accum, n_train, micro = r["micro_batch_trace"], r["grad_accum"], r["n_train_items"], r["micro_batch"]
            per_epoch = -(-n_train // micro)
            seen = set()
            for i, (t, rows, L, dur, ce, acc) in enumerate(mb):
                key = (rows, L)
                first = key not in seen
                seen.add(key)
                k = i % per_epoch + 1
                step = k % grad_accum == 0 or k == per_epoch
                if not first and dur is not None:
                    X.append([1.0, rows * L, float(step)])
                    y.append(dur)
        coef = np.linalg.lstsq(np.array(X), np.array(y), rcond=None)[0]
        pred = np.array(X) @ coef
        fits[base] = {"reports": reports, "n_micro_batches": len(y), "c0_s": float(coef[0]), "c1_s_per_token": float(coef[1]),
                      "c2_step_s": float(coef[2]), "r2": float(1 - ((np.array(y) - pred) ** 2).sum() / ((np.array(y) - np.mean(y)) ** 2).sum())}
    tasks = {}
    for spec in a.task:
        task, items_path, epochs = spec.split(":")
        prov = json.loads(Path(items_path).with_suffix(".provenance.json").read_text(encoding="utf-8"))
        lens = [len(it["ids"]) for it in torch.load(items_path, map_location="cpu", weights_only=False)]
        f = fits[prov["base"]]
        mbs = _micro_batches(lens, prov["n_calib"], int(epochs))
        loop = sum(f["c0_s"] + f["c1_s_per_token"] * rows * L + f["c2_step_s"] * st for rows, L, st in mbs)
        tasks[task] = {"base": prov["base"], "items": items_path, "n_train": prov["n_train"], "epochs": int(epochs),
                       "micro_batches": len(mbs), "padded_tokens": sum(rows * L for rows, L, _ in mbs),
                       "train_loop_h": round(loop / 3600, 3)}
    out = {"fits": fits, "tasks": tasks, "train_loop_total_h": round(sum(t["train_loop_h"] for t in tasks.values()), 2)}
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"fits": {b: {k: round(v, 6) if isinstance(v, float) else v for k, v in f.items() if k != "reports"}
                               for b, f in fits.items()},
                      "tasks": {t: v["train_loop_h"] for t, v in tasks.items()}, "total_h": out["train_loop_total_h"]}))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("summary")
    s.add_argument("reports", nargs="+")
    s.add_argument("--out")
    s.add_argument("--json")
    s = sub.add_parser("same")
    s.add_argument("ref")
    s.add_argument("other")
    s.add_argument("--json")
    s.add_argument("--require-identical", action="store_true")
    s = sub.add_parser("paired")
    s.add_argument("a")
    s.add_argument("b")
    s.add_argument("--json")
    s = sub.add_parser("select")
    s.add_argument("reports", nargs="+")
    s.add_argument("--json")
    s = sub.add_parser("diag")
    s.add_argument("--task", required=True)
    s.add_argument("--timing", required=True)
    s.add_argument("--select", required=True)
    s.add_argument("--ep0", required=True, help="dev report of the untrained base (epoch 0 = vanilla)")
    s.add_argument("--selected-ckpt", required=True)
    s.add_argument("--calibrate-json")
    s.add_argument("--flip")
    s.add_argument("--out", required=True)
    s = sub.add_parser("estimate")
    s.add_argument("--english", nargs="+", required=True, help="run_ft timing reports of english-base runs")
    s.add_argument("--multilingual", nargs="+", required=True)
    s.add_argument("--task", action="append", required=True, help="TASK:ITEMS.pt:EPOCHS")
    s.add_argument("--out", required=True)
    a = p.parse_args()
    {"summary": cmd_summary, "same": cmd_same, "paired": cmd_paired, "select": cmd_select, "diag": cmd_diag,
     "estimate": cmd_estimate}[a.cmd](a)


if __name__ == "__main__":
    main()
