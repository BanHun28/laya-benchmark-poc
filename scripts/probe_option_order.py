#!/usr/bin/env python
"""Track C1 option-order flip probe (03 §8 C1, §3.8, §4): permute each item's choice criteria and count how
often the argmax label moves against the original order, original and permutations in one process.

Method (upstream research/scripts/build_benchmark_nb.py:640-678): per item, a `random.Random(seed)` stream
shuffles the criteria key order into a new dict; every other byte of the question is unchanged. One stream
per input file, consumed item-major over the selected split (item 1: perm 1..k, item 2: ...); each order is
stored in the JSON. Original and permuted copies go through the same call shape,
`Agent.predict_batch([state], {qid: question})` (one state per forward pass), so option order is the only
difference between an original and a permuted answer.

flip(i, j) = argmax label of permutation j != argmax label of the original order on item i.
per-permutation flip rate = mean over items and permutations; any-flip = share of items with >= 1 flip.
95% CIs: percentile bootstrap over items.

  source env.sh && .venv/bin/python scripts/probe_option_order.py data/evals/ko_massive_domain_8.jsonl ... \
      --model models/laya-multilingual --device cpu --permutations 5 --seed 13 --split dev \
      --splits results/B/B_splits.json --reference results/B/<run>.json ... --out results/C/C1_option_order_<date>.json
"""
import argparse
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from metrics_extra import load_report, read_dataset, row_splits  # noqa: E402

CONF_EDGES = (0.5, 0.7, 0.9)  # original-order answer_confidence buckets
# BENCHMARKS.md:211-221 (one permutation per item, n=200, en) and :450 (zh-decision-bench)
UPSTREAM = [("massive_intent.en, 20 options", "0.150 (laya) / 0.230 (multilingual)"),
            ("en.emotion, 6 options", "0.040 / 0.090"), ("xnli.en, 3 options", "0.000 / 0.015"),
            ("Jev (third party)", "0.13"), ("zh CS routing / voice routing (multilingual)", "0.28 / 0.106")]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_card(args, model_dir, agent, started_at):
    import laya
    import torch
    import transformers
    real = Path(model_dir).resolve()
    snap = re.search(r"snapshots/([0-9a-f]{40})", str(real))
    weights = real / "model.safetensors"
    batt = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True).stdout.splitlines()
    return {"tool": "scripts/probe_option_order.py", "argv": sys.argv[1:],
            "started_at": started_at, "laya_version": laya.__version__,
            "torch": torch.__version__, "transformers": transformers.__version__, "device": args.device,
            "dtype": str(getattr(agent, "dtype", None)), "amp_enabled": getattr(agent, "amp_enabled", None),
            "threads_intra_inter": [torch.get_num_threads(), torch.get_num_interop_threads()],
            "checkpoint": {"path": str(model_dir), "realpath": str(real), "snapshot_sha": snap and snap.group(1),
                           "weights_blob": Path(os.readlink(weights)).name if weights.is_symlink() else None,
                           "head_max_len": agent.cfg.get("head_max_len"), "max_len": agent.cfg.get("max_len")},
            "power": " | ".join(batt[:2]), "git_sha": None}


def probe_file(agent, path, args, split_ref):
    rows, header = read_dataset(path)
    name = Path(path).stem
    splits, rule = row_splits(rows, header, "auto", Path(path).name)
    idx = [i for i, s in enumerate(splits) if args.split == "all" or s == args.split]
    check = None
    if name in split_ref and args.split != "all":
        ref = split_ref[name]
        dist = {q: dict(sorted(Counter(str(rows[i]["expected"][q]) for i in idx).items())) for q in rows[idx[0]]["expected"]}
        check = {"rule": ref["rule"], "rows": ref[args.split], "label_distribution_match": dist == ref["label_distribution"][args.split]}
        assert ref["rule"] == rule and ref[args.split] == len(idx) and check["label_distribution_match"], (name, check)
    rng = random.Random(args.seed)
    items, t0 = [], time.time()
    for n_done, i in enumerate(idx, 1):
        row = rows[i]
        for qid, q in row["questions"].items():
            if q.get("type") != "choice" or qid not in row["expected"]:
                continue
            keys = list(q["criteria"])

            def ask(question):
                a = agent.predict_batch([row["state"]], {qid: question})[0]["answers"][qid]
                return {"pred": a["choice"], "conf": a["answer_confidence"], "probs": a["probabilities"]}

            orig, perms = ask(q), []
            for _ in range(args.permutations):
                order = list(range(len(keys)))
                rng.shuffle(order)
                p = ask({**q, "criteria": {keys[o]: q["criteria"][keys[o]] for o in order}})
                perms.append({"order": [keys[o] for o in order], **p})
            items.append({"row": i, "qid": qid, "gold": row["expected"][qid], "options": keys,
                          "tags": row.get("tags", []), "orig": orig, "perms": perms})
        if n_done % 50 == 0:
            print("  %s %d/%d (%.0fs)" % (name, n_done, len(idx), time.time() - t0), file=sys.stderr, flush=True)
    return {"file": str(path), "set": name, "dataset_sha256": sha256(path), "split": args.split, "split_rule": rule,
            "split_check": check, "seconds": round(time.time() - t0, 1), "items": items}


def rates(items):
    flips = np.array([[p["pred"] != it["orig"]["pred"] for p in it["perms"]] for it in items], float)
    return flips.mean(1), flips.max(1)


def group(items, key):
    out = defaultdict(list)
    for it in items:
        out[key(it)].append(it)
    res = {}
    for lab, v in sorted(out.items()):
        per, anyf = rates(v)
        res[lab] = {"n": len(v), "flip_rate_per_perm": float(per.mean()), "any_flip_rate": float(anyf.mean()),
                    "orig_accuracy": float(np.mean([it["orig"]["pred"] == it["gold"] for it in v])),
                    "perm_accuracy": float(np.mean([p["pred"] == it["gold"] for it in v for p in it["perms"]]))}
    return res


def bucket(conf):
    lo = max([0.0] + [e for e in CONF_EDGES if conf >= e])
    hi = min([e for e in CONF_EDGES if e > lo] + [1.0])
    return "[%.1f, %.1f%s" % (lo, hi, "]" if hi == 1.0 else ")")


def analyse(res, args):
    from scipy.stats import chi2
    items = res["items"]
    n, k = len(items), args.permutations
    per, anyf = rates(items)
    boot = np.random.default_rng(args.seed).integers(0, n, size=(args.bootstrap, n))
    ci = lambda v: [float(x) for x in np.percentile(v[boot].mean(1), [2.5, 97.5])]  # noqa: E731
    corr = np.array([[p["pred"] == it["gold"] for p in it["perms"]] for it in items], float)
    flips_j = np.array([[p["pred"] != it["orig"]["pred"] for p in it["perms"]] for it in items], float).mean(0)
    m = {"n_items": n, "n_options": len(items[0]["options"]), "permutations": k,
         "identity_permutations": sum(p["order"] == it["options"] for it in items for p in it["perms"]),
         "orig_accuracy": float(np.mean([it["orig"]["pred"] == it["gold"] for it in items])),
         "flip_rate_per_perm": float(per.mean()), "flip_rate_per_perm_ci": ci(per),
         "flip_rate_by_perm": [float(x) for x in flips_j], "any_flip_rate": float(anyf.mean()), "any_flip_rate_ci": ci(anyf),
         "accuracy_by_perm": [float(x) for x in corr.mean(0)], "perm_accuracy_mean": float(corr.mean()),
         "perm_accuracy_min": float(corr.mean(0).min()), "perm_accuracy_max": float(corr.mean(0).max()),
         "mean_abs_delta_answer_confidence": float(np.mean([abs(p["conf"] - it["orig"]["conf"]) for it in items for p in it["perms"]]))}
    # position: under random orders the chosen option's slot is uniform unless the model prefers slots
    n_opt = m["n_options"]
    chosen = Counter(p["order"].index(p["pred"]) for it in items for p in it["perms"])
    obs = np.array([chosen.get(s, 0) for s in range(n_opt)], float)
    exp = obs.sum() / n_opt
    stat = float(((obs - exp) ** 2 / exp).sum())
    gold_slot = defaultdict(list)
    for it in items:
        for p in it["perms"]:
            gold_slot[p["order"].index(it["gold"])].append(p["pred"] == it["gold"])
    m["slots"] = {"chosen_slot_share": [float(x) for x in obs / obs.sum()], "uniform": 1 / n_opt,
                  "chi2": stat, "df": n_opt - 1, "p": float(chi2.sf(stat, n_opt - 1)),
                  "accuracy_by_gold_slot": [[float(np.mean(gold_slot[s])) if gold_slot[s] else None, len(gold_slot[s])]
                                            for s in range(n_opt)]}
    m["pred_counts_orig"] = dict(Counter(it["orig"]["pred"] for it in items).most_common())
    m["pred_counts_perm_mean"] = {lab: c / k for lab, c in Counter(p["pred"] for it in items for p in it["perms"]).most_common()}
    m["gold_counts"] = dict(Counter(it["gold"] for it in items).most_common())
    m["by_gold"] = group(items, lambda it: it["gold"])
    m["by_orig_pred"] = group(items, lambda it: it["orig"]["pred"])
    m["by_orig_conf"] = group(items, lambda it: bucket(it["orig"]["conf"]))
    if any(t.startswith("scenario:") for it in items for t in it["tags"]):
        m["by_scenario"] = group(items, lambda it: next(t[9:] for t in it["tags"] if t.startswith("scenario:")))
    return m


def parity(res, ref_path):
    """Original-order answers here vs the same rows in a laya-evals report (metrics_extra.load_report)."""
    r = load_report(ref_path)
    assert r["run_card"]["dataset_sha256"] == res["dataset_sha256"], ref_path
    ref = {(c["row"], c["qid"]): c for c in r["cases"]}
    pairs = [(it, ref[(it["row"], it["qid"])]) for it in res["items"]]
    return {"report": str(ref_path), "n": len(pairs), "argmax_agreement": sum(it["orig"]["pred"] == c["pred"] for it, c in pairs),
            "max_abs_dp": max(abs(float(it["orig"]["probs"][o]) - c["probs"][o]) for it, c in pairs for o in c["probs"]),
            "ref_accuracy": float(np.mean([c["correct"] for _, c in pairs]))}


def f3(x):
    return "-" if x is None else "%.3f" % x


def markdown(out):
    L = ["# C1 option-order flip probe (%s)" % out["run_card"]["started_at"][:10], "",
         "`%s` — %s" % (" ".join(["scripts/probe_option_order.py"] + out["run_card"]["argv"]), out["run_card"]["started_at"]), "",
         "flip(i, j) = argmax label of permutation j differs from the original-order argmax on item i (03 §4). "
         "Per-permutation flip = mean over items × permutations (upstream-comparable: upstream draws one permutation per item). "
         "any-flip = share of items with ≥ 1 flip in k permutations. CIs: percentile bootstrap over items (%d, seed %d). "
         "G4 threshold 0.10 (00 §6 G4, 05 §1), H5 range 0.10–0.30 (03 §1)." % (out["params"]["bootstrap"], out["params"]["seed"]), "",
         "| set | split | n | options | orig acc | per-perm flip [95% CI] | per-perm flip min–max over k | any-flip [95% CI] "
         "| perm acc mean (min–max) | mean abs Δ answer_confidence | ≤ 0.10 (G4) | in 0.10–0.30 (H5) | parity vs laya-evals report |",
         "|" + "---|" * 13]
    for s in out["sets"]:
        m, p = s["metrics"], s.get("reference_parity")
        par = "%d/%d argmax, max abs Δp %.4f" % (p["argmax_agreement"], p["n"], p["max_abs_dp"]) if p else "-"
        L.append("| %s | %s | %d | %d | %s | %s [%s, %s] | %s–%s | %s [%s, %s] | %s (%s–%s) | %s | %s | %s | %s |" % (
            s["set"], s["split"], m["n_items"], m["n_options"], f3(m["orig_accuracy"]), f3(m["flip_rate_per_perm"]),
            *map(f3, m["flip_rate_per_perm_ci"]), f3(min(m["flip_rate_by_perm"])), f3(max(m["flip_rate_by_perm"])),
            f3(m["any_flip_rate"]), *map(f3, m["any_flip_rate_ci"]), f3(m["perm_accuracy_mean"]),
            f3(m["perm_accuracy_min"]), f3(m["perm_accuracy_max"]), f3(m["mean_abs_delta_answer_confidence"]),
            "pass" if m["flip_rate_per_perm"] <= 0.10 else "fail", "yes" if 0.10 <= m["flip_rate_per_perm"] <= 0.30 else "no", par))
    L += ["", "Upstream references (per-permutation definition):", "", "| reference | flip rate |", "|---|---|"]
    L += ["| %s | %s |" % r for r in UPSTREAM]
    for s in out["sets"]:
        m = s["metrics"]
        L += ["", "## %s (%s, n=%d, %d options)" % (s["set"], s["split"], m["n_items"], m["n_options"]), "",
              "- per-permutation flip by permutation: " + ", ".join(map(f3, m["flip_rate_by_perm"])),
              "- accuracy by permutation: " + ", ".join(map(f3, m["accuracy_by_perm"])) + " (original %s)" % f3(m["orig_accuracy"]),
              "- identity permutations drawn: %d of %d" % (m["identity_permutations"], m["n_items"] * m["permutations"]),
              "- predicted labels, original: " + ", ".join("%s %d" % kv for kv in m["pred_counts_orig"].items()),
              "- predicted labels, mean per permutation: " + ", ".join("%s %.1f" % kv for kv in m["pred_counts_perm_mean"].items()),
              "- chosen slot share under permutation (uniform %.3f): %s; chi2 %.1f, df %d, p %.2g" % (
                  m["slots"]["uniform"], ", ".join(f3(x) for x in m["slots"]["chosen_slot_share"]), m["slots"]["chi2"],
                  m["slots"]["df"], m["slots"]["p"]),
              "- accuracy by gold slot under permutation (slot: acc/n): " + ", ".join(
                  "%d: %s/%d" % (i, f3(a), c) for i, (a, c) in enumerate(m["slots"]["accuracy_by_gold_slot"])), ""]
        for title, key in (("gold class", "by_gold"), ("original-order prediction", "by_orig_pred"),
                           ("original-order answer_confidence", "by_orig_conf"), ("MASSIVE scenario (gold)", "by_scenario")):
            if key not in m:
                continue
            L += ["| %s | n | per-perm flip | any-flip | orig acc | perm acc |" % title, "|---|---|---|---|---|---|"]
            rows = sorted(m[key].items(), key=lambda kv: -kv[1]["flip_rate_per_perm"]) if key != "by_orig_conf" else m[key].items()
            L += ["| %s | %d | %s | %s | %s | %s |" % (lab, v["n"], f3(v["flip_rate_per_perm"]), f3(v["any_flip_rate"]),
                                                       f3(v["orig_accuracy"]), f3(v["perm_accuracy"])) for lab, v in rows]
            L.append("")
    rc = out["run_card"]
    L += ["## run_card", "", "| field | value |", "|---|---|"]
    L += ["| %s | %s |" % (k, (json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v).replace("|", "\\|"))
          for k, v in rc.items() if k != "argv"]
    L += ["| dataset %s | sha256 %s, questions_sha256 %s, split rule %s, check %s, %.0fs |" % (
        s["file"], s["dataset_sha256"], s["questions_sha256"], s["split_rule"], json.dumps(s["split_check"], ensure_ascii=False),
        s["seconds"]) for s in out["sets"]]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--model", default="models/laya-multilingual", help="checkpoint dir, or a name under $LAYA_MODELS_DIR/laya-<name>")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--permutations", type=int, default=5)
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--split", choices=("dev", "test", "all"), default="dev")
    ap.add_argument("--splits", default="results/B/B_splits.json", help="Track B split record to assert counts against")
    ap.add_argument("--reference", action="append", default=[], help="laya-evals report on the same file (parity check)")
    ap.add_argument("--bootstrap", type=int, default=1000)
    ap.add_argument("--threads", type=int, default=10)
    ap.add_argument("--interop", type=int, default=1)
    ap.add_argument("--out", required=True, help="JSON output; Markdown goes next to it (.md)")
    a = ap.parse_args(argv)
    import torch
    torch.set_num_threads(a.threads)
    torch.set_num_interop_threads(a.interop)
    import laya
    from laya.evals import Dataset, questions_fingerprint
    model_dir = Path(a.model) if Path(a.model).exists() else Path(os.environ.get("LAYA_MODELS_DIR", ROOT / "models")) / ("laya-" + a.model)
    split_ref = json.loads(Path(a.splits).read_text(encoding="utf-8"))["splits"] if a.splits else {}
    t0, started_at = time.time(), time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("default")
        agent = laya.load(str(model_dir), device=a.device)
        out = {"run_card": run_card(a, model_dir, agent, started_at), "params": vars(a), "sets": []}
        out["run_card"]["load_seconds"] = round(time.time() - t0, 1)
        for f in a.files:
            res = probe_file(agent, f, a, split_ref)
            res["questions_sha256"] = questions_fingerprint(Dataset.from_jsonl(f))
            res["metrics"] = analyse(res, a)
            refs = [r for r in a.reference if Path(json.loads(Path(r).read_text(encoding="utf-8"))["config"]["dataset"]).name == Path(f).name]
            if refs:
                res["reference_parity"] = parity(res, refs[0])
            out["sets"].append(res)
            m = res["metrics"]
            print("%s: n=%d per-perm flip %.3f any-flip %.3f orig acc %.3f perm acc %.3f (%.0fs)" % (
                res["set"], m["n_items"], m["flip_rate_per_perm"], m["any_flip_rate"], m["orig_accuracy"],
                m["perm_accuracy_mean"], res["seconds"]), file=sys.stderr, flush=True)
    out["run_card"]["warnings"] = sorted({"%s:%s: %s: %s" % (w.filename, w.lineno, w.category.__name__, w.message) for w in caught})
    out["run_card"]["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    out["run_card"]["total_seconds"] = round(time.time() - t0, 1)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    Path(a.out).with_suffix(".md").write_text(markdown(out), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
