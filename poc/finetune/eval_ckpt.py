"""Evaluate a checkpoint directory with laya.evals.evaluate on CPU fp32 (P4), reports in `laya-evals run --json` form.

    source env.sh
    .venv/bin/python poc/finetune/eval_ckpt.py run --ckpt poc/finetune/ckpt_probe --name probe \
        --dataset data/evals/ko_massive_domain_8.jsonl --out results/P4/<ts>_probe_ko_massive_domain_8
    .venv/bin/python poc/finetune/eval_ckpt.py devcopy data/evals/ko_klue_ynat_7.jsonl --out-dir results/P4/dev
    .venv/bin/python poc/finetune/eval_ckpt.py overlap REPORT... --train poc/finetune/data/domain8_train.jsonl --out X.md
    .venv/bin/python poc/finetune/eval_ckpt.py epochs EPOCH_DEV_REPORT... --final FINAL_DEV_REPORT --out X.md

`run`: laya.load(ckpt, device="cpu") wrapped for the harness. evaluate() calls runner.predict(state, questions,
model=...) and Agent.predict has no `model`, so the wrapper drops it; predict_batch passes through. The config
block carries what `laya-evals run --json` writes (dataset, dataset_sha256, model, device, thresholds) plus the
checkpoint's weights sha256, so scripts/metrics_extra.py reads these reports like the Track B ones.
`devcopy`: dev-half copy of an eval file by the B split rule (results/B/B_prep.py convention).
`overlap`: accuracy with and without the rows whose state (the utterance) appears verbatim in the training rows, for
the whole file and, where results/B/B_splits.json defines them for the same file, its dev/test halves.
`epochs`: epoch choice on dev only, each epoch copy against the final export on the same rows (exact McNemar). Rule:
the final export stays v1 unless an epoch is more accurate with p < 0.05.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from metrics_extra import load_report, mcnemar_exact, read_dataset, row_splits, state_key  # noqa: E402


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    p = Path(path).resolve()
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


class AgentRunner:
    def __init__(self, agent):
        self.agent = agent

    def predict(self, state, questions, model=None):
        return self.agent.predict(state, questions)

    def predict_batch(self, states, questions, model=None, batch_size=None, sort_by_length=False):
        return self.agent.predict_batch(states, questions, batch_size=batch_size, sort_by_length=sort_by_length)


def cmd_run(a):
    import torch
    torch.set_num_threads(a.threads)
    torch.set_num_interop_threads(1)  # 03 §3.4
    import laya
    from laya import evals
    t = time.perf_counter()
    agent = laya.load(a.ckpt, device="cpu")
    load_s = time.perf_counter() - t
    ckpt = Path(a.ckpt)
    config = {"dataset": rel(a.dataset), "model": a.name, "device": "cpu",
              "dataset_sha256": evals.file_fingerprint(a.dataset),
              "revisions": {a.name: a.revision},
              "thresholds": {"min": {}, "max": {}, "baseline_tolerance": {}},
              "runner": "poc/finetune/eval_ckpt.py AgentRunner(laya.load(ckpt, device='cpu'))",
              "checkpoint": {"path": rel(ckpt), "realpath": str(ckpt.resolve()),
                             "weights_sha256": sha256(ckpt / "model.safetensors"),
                             "rl_agent_config_sha256": sha256(ckpt / "rl_agent_config.json"),
                             "temperature_raw": agent.temperature_raw, "temperature_applied": agent.temperature,
                             "temperature_by_options": agent.temperature_by_options},
              "threads": {"intra": torch.get_num_threads(), "interop": torch.get_num_interop_threads()},
              "load_s": round(load_s, 2)}
    t = time.perf_counter()
    report = evals.evaluate(AgentRunner(agent), evals.Dataset.from_jsonl(a.dataset), batch_size=a.batch_size,
                            config=config)
    report.config = dict(report.config, eval_s=round(time.perf_counter() - t, 2))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(str(out) + ".json", "w", encoding="utf-8") as f:
        json.dump(report.to_json(), f, ensure_ascii=False, indent=2, sort_keys=True)
    Path(str(out) + ".md").write_text(report.to_markdown(), encoding="utf-8")
    print("%s: %s load %.1fs eval %.1fs" % (rel(str(out) + ".json"), json.dumps(
        {k: round(v, 4) for k, v in report.overall.items() if k in ("choice_accuracy", "ece", "mean_confidence")}),
        load_s, report.config["eval_s"]))


def cmd_devcopy(a):
    src = Path(a.src)
    rows, header = read_dataset(src)
    splits, rule = row_splits(rows, header, "auto", src.name)
    lines = [line for line in src.read_text(encoding="utf-8").splitlines() if line.strip()]
    head = [line for line in lines if line.strip().startswith("#")]
    body = [line for line in lines if not line.strip().startswith("#")]
    assert len(body) == len(rows)
    keep = [line for line, s in zip(body, splits) if s == "dev"]
    note = "# split: dev | rule: %s | source: %s sha256 %s | rows %d/%d | P4 (poc/finetune/eval_ckpt.py devcopy)" % (
        rule, rel(src), sha256(src), len(keep), len(body))
    dst = Path(a.out_dir) / src.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(head + [note] + keep) + "\n", encoding="utf-8")
    print("%s: %d dev rows of %d (%s), sha256 %s" % (rel(dst), len(keep), len(body), rule, sha256(dst)))


def cmd_overlap(a):
    train, _ = read_dataset(a.train)
    seen = {state_key(r["state"]) for r in train}
    halves = json.loads(Path(a.splits).read_text(encoding="utf-8"))["splits"]
    out = ["Rows whose state appears verbatim in `%s` (%d rows) vs the rest; dev/test halves only where `%s` defines "
           "them for the same file." % (rel(a.train), len(train), rel(a.splits)), "",
           "| report | split | n | acc | n overlap | acc overlap | n clean | acc clean |", "|---|---|---|---|---|---|---|---|"]
    res = []
    for path in a.reports:
        r = load_report(path)
        ref, sps = halves.get(r["set"]), ("all",)
        if ref and ref["rows"] == r["run_card"]["rows"]:
            assert ref["rule"] == r["rule"] and all(ref[s] == r["run_card"]["split_rows"][s] for s in ("dev", "test")), path
            sps = ("all", "dev", "test")
        for sp in sps:
            cs = [c for c in r["cases"] if sp == "all" or c["split"] == sp]
            if not cs:
                continue
            ov = [c["correct"] for c in cs if c["skey"] in seen]
            cl = [c["correct"] for c in cs if c["skey"] not in seen]
            m = {"report": rel(path), "split": sp, "n": len(cs), "acc": sum(c["correct"] for c in cs) / len(cs),
                 "n_overlap": len(ov), "acc_overlap": sum(ov) / len(ov) if ov else None,
                 "n_clean": len(cl), "acc_clean": sum(cl) / len(cl) if cl else None}
            res.append(m)
            f = lambda x: "-" if x is None else "%.3f" % x  # noqa: E731
            out.append("| %s | %s | %d | %s | %d | %s | %d | %s |" % (
                m["report"], sp, m["n"], f(m["acc"]), m["n_overlap"], f(m["acc_overlap"]), m["n_clean"], f(m["acc_clean"])))
    Path(a.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    Path(a.out).with_suffix(".json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("\n".join(out))


def cmd_epochs(a):
    final = load_report(a.final)
    n = len(final["cases"])
    acc_final = sum(c["correct"] for c in final["cases"]) / n
    out = ["Epoch choice on dev only: each epoch copy vs the final export `%s` on the same %d rows. b = epoch right and "
           "final wrong, c = the reverse, exact two-sided McNemar." % (rel(a.final), n), "",
           "| epoch report | acc | Δ vs final | b | c | McNemar p | argmax agreement |", "|---|---|---|---|---|---|---|"]
    res = []
    for path in a.epochs:
        r = load_report(path)
        pairs = list(zip(r["cases"], final["cases"]))
        assert len(r["cases"]) == n and all(x["skey"] == y["skey"] for x, y in pairs), path
        b = sum(x["correct"] and not y["correct"] for x, y in pairs)
        c = sum(y["correct"] and not x["correct"] for x, y in pairs)
        m = {"report": rel(path), "acc": sum(x["correct"] for x, _ in pairs) / n, "b": b, "c": c,
             "p": mcnemar_exact(b, c), "agreement": sum(x["pred"] == y["pred"] for x, y in pairs) / n}
        res.append(m)
        out.append("| %s | %.4f | %+.4f | %d | %d | %.3g | %.4f |" % (
            m["report"], m["acc"], m["acc"] - acc_final, b, c, m["p"], m["agreement"]))
    better = [m for m in res if m["acc"] > acc_final and m["p"] < 0.05]
    if better:
        best = max(better, key=lambda m: m["acc"])
        decision = ("dev prefers %s (acc %.4f vs final %.4f, McNemar p %.3g): v1 candidate for the lead's decision; "
                    "the epoch copy carries the base temperature and needs calibration first" % (
                        best["report"], best["acc"], acc_final, best["p"]))
    else:
        decision = "v1 = final export (dev acc %.4f); no epoch is more accurate on dev with p < 0.05" % acc_final
    out += ["", "decision: " + decision]
    Path(a.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    Path(a.out).with_suffix(".json").write_text(json.dumps(
        {"final": rel(a.final), "final_acc": acc_final, "epochs": res, "decision": decision}, ensure_ascii=False,
        indent=1) + "\n", encoding="utf-8")
    print("\n".join(out))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("run")
    s.add_argument("--ckpt", required=True)
    s.add_argument("--name", required=True, help="model label in the report (config.model)")
    s.add_argument("--revision", default="local", help="what config.revisions records for --name")
    s.add_argument("--dataset", required=True)
    s.add_argument("--out", required=True, help="output path without extension (.json and .md are written)")
    s.add_argument("--batch-size", type=int, default=16)
    s.add_argument("--threads", type=int, default=10)
    s = sub.add_parser("devcopy")
    s.add_argument("src")
    s.add_argument("--out-dir", required=True)
    s = sub.add_parser("overlap")
    s.add_argument("reports", nargs="+")
    s.add_argument("--train", required=True)
    s.add_argument("--splits", default=str(ROOT / "results/B/B_splits.json"), help="Track B split record (dev/test halves)")
    s.add_argument("--out", required=True)
    s = sub.add_parser("epochs")
    s.add_argument("epochs", nargs="+", help="dev reports of the epoch copies")
    s.add_argument("--final", required=True, help="dev report of the final export")
    s.add_argument("--out", required=True)
    a = p.parse_args()
    {"run": cmd_run, "devcopy": cmd_devcopy, "overlap": cmd_overlap, "epochs": cmd_epochs}[a.cmd](a)


if __name__ == "__main__":
    main()
