# Contains code derived from notebooks/laya_finetune_typed_decisions_mps.py of Laya (https://github.com/NandhaKishorM/laya)
# at commit 4aa6761, Apache License 2.0. Modified by this project: `calibrate` re-runs the script's calibration hold-out
# and per-type temperature fit on an epoch checkpoint instead of at the end of training.
"""Trained-Laya arm (T3arm): the fine-tune script's items for any task, and the script's calibration for an epoch copy.

    source env.sh
    .venv/bin/python poc/finetune/ft_task.py items --task T3 --base english --out poc/finetune/data/t3arm/T3_english.pt
    .venv/bin/python poc/finetune/ft_task.py calibrate --ckpt CK/epoch_1 --items X.pt --out CK_sel --device mps

`items`: rows from scripts/build_train_sets.py (poc/finetune/data/t3arm/<task>_{train,calib}.jsonl) become items
through the fine-tune script's own `build_training_item` (poc/finetune/laya_finetune_mps_patched.py; the T3arm patch
does not touch it), at the base checkpoint's max_len / head_max_len. Gold, read by key as the script does: choice
{"probabilities": {expected: 1.0}}, noul {"true": p, "false": 1 - p}, score {"<level>": 1.0}; T1 the dataset's teacher
distributions (row["gold"]). Train items of choice questions get their criteria keys permuted by
random.Random(seed + item index) (P4's option-order augmentation: rendered options, target and label follow the
permutation, key descriptions and gold key unchanged); score levels and noul false/true keep their order, and
calibration items keep the canonical order. `--permute-labels` (V3 control) shuffles the train rows' expected labels
with random.Random(seed) before anything else. The calibration rows are laid onto the slots the script holds out
(random.Random(20260922), n = min(--calib-max, N // 10)); no `<items>.meta.json` is written (the script then reads the
file as a legacy cache; never pass --force-preprocess). V4: the first 20 train items and 5 calibration items are
rebuilt through `Agent._encode_state` (laya's inference path) and must be identical; every item's options are
decoded back and its target checked against the gold key in rendered order.
`calibrate`: the script's post-training step (calibration forward over the held-out slots, `fit_temperature` per
question type, 1.2 for a type with no sample, config update and `temperature_by_options` dropped) applied to an epoch
copy, written as a new checkpoint directory. Logits come from the stored fp16 weights; the script's own final export
fits on the in-memory fp32 weights of the last epoch.
"""
import argparse
import hashlib
import importlib.util
import inspect
import json
import random
import shutil
import statistics
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
ROWS = ROOT / "poc/finetune/data/t3arm"
FT_SCRIPT = ROOT / "poc/finetune/laya_finetune_mps_patched.py"
UPSTREAM = ROOT / "third_party/laya/notebooks/laya_finetune_typed_decisions_mps.py"
BASES = {"english": ROOT / "models/laya", "multilingual": ROOT / "models/laya-multilingual"}
SPLIT_SEED = 20260922
SPLIT_LINES = ("random.Random(20260922).shuffle(order)",
               "n_calib = min(args.calib_max, len(all_items) // 10)",
               "calib_items = [all_items[i] for i in sorted(order[:n_calib])]",
               "train_items = [all_items[i] for i in sorted(order[n_calib:])]")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def rel(path):
    p = Path(path).resolve()
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").split("\n")
            if line.strip() and not line.startswith("#")]


def load_ft():
    """The patched script as a module; its hold-out lines and build_training_item must be upstream's."""
    src = FT_SCRIPT.read_text(encoding="utf-8")
    missing = [line for line in SPLIT_LINES if line not in src]
    assert not missing, "calibration hold-out changed, the slot layout is void: %s" % missing
    mods = []
    for path, name in ((FT_SCRIPT, "laya_ft_patched"), (UPSTREAM, "laya_ft_upstream")):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mods.append(mod)
    ft, up = mods
    for fn in ("build_training_item", "collate", "fit_temperature"):
        assert inspect.getsource(getattr(ft, fn)) == inspect.getsource(getattr(up, fn)), fn
    return ft, sha256(src.encode("utf-8"))


def gold_of(task, row, qid):
    q, exp = row["questions"][qid], row["expected"][qid]
    if task == "T1":
        return row["gold"][qid]
    if q["type"] == "choice":
        return {"probabilities": {exp: 1.0}}
    if q["type"] == "noul":
        return {"probabilities": {"true": float(bool(exp)), "false": 1.0 - float(bool(exp))}}
    return {"probabilities": {str(int(exp)): 1.0}}


def option_texts(tok, it):
    """Option strings in the order the item's ids render them, decoded back."""
    bounds = it["markers"] + [it["ids"].index(tok.sep_token_id, it["markers"][-1])]
    return [tok.decode(it["ids"][a + 1:b]).strip() for a, b in zip(bounds, bounds[1:])]


def subset(rows, n, seed, per_row):
    """Deterministic random rows (row order kept) until they hold n items; all rows when n is 0."""
    if not n:
        return list(range(len(rows)))
    idx = list(range(len(rows)))
    random.Random(seed).shuffle(idx)
    out, total = [], 0
    for i in idx:
        if total >= n:
            break
        out.append(i)
        total += per_row(rows[i])
    return sorted(out)


def cmd_items(a):
    import torch
    from transformers import AutoTokenizer
    from laya.agent import Agent
    from laya.common import render_options

    ft, ft_sha = load_ft()
    base = BASES[a.base]
    cfg = json.loads((base / "rl_agent_config.json").read_text())
    budget = {"max_len": cfg.get("max_len", 1024), "head_max_len": cfg.get("head_max_len", 256)}  # as the patched train()
    tok = AutoTokenizer.from_pretrained(base / "tokenizer")
    fake_agent = SimpleNamespace(tok=tok, cfg={**cfg, **budget})
    paths = {s: ROWS / ("%s_%s.jsonl" % (a.task, s)) for s in ("train", "calib")}
    src = {s: read_rows(p) for s, p in paths.items()}
    per_row = lambda r: len(r["expected"])  # noqa: E731
    pick = {"train": subset(src["train"], a.n_train, a.seed, per_row), "calib": subset(src["calib"], a.n_calib, a.seed, per_row)}
    rows = {s: [src[s][i] for i in pick[s]] for s in pick}
    permuted = None
    if a.permute_labels:
        assert all(len(r["expected"]) == 1 for r in rows["train"]) and a.task != "T1", "label permutation: single-question tasks"
        labels = [next(iter(r["expected"].values())) for r in rows["train"]]
        perm = list(labels)
        random.Random(a.seed).shuffle(perm)
        permuted = sum(x != y for x, y in zip(labels, perm))
        rows["train"] = [dict(r, expected={next(iter(r["expected"])): y}) for r, y in zip(rows["train"], perm)]

    built, k = {"train": [], "calib": []}, 0
    moved, gold_slot, v4 = Counter(), Counter(), {"checked": 0, "identical": 0}
    for split in ("train", "calib"):
        for ri, row in zip(pick[split], rows[split]):
            for qid, q in row["questions"].items():
                if split == "train" and a.shuffle_options == "all" and q["type"] == "choice":
                    keys = list(q["criteria"])
                    random.Random(a.seed + k).shuffle(keys)
                    q_used = {**q, "criteria": {key: q["criteria"][key] for key in keys}}
                else:
                    q_used = q
                gold = gold_of(a.task, row, qid)
                it = ft.build_training_item(tok, {**cfg, **budget}, row["state"], q_used, gold)
                assert it is not None, (split, ri, qid)
                internal = Agent._to_internal(q_used)
                opts = option_texts(tok, it)
                assert opts == render_options(internal), (split, ri, qid, opts)
                exp = row["expected"][qid]
                if q["type"] == "choice":
                    order = list(q_used["criteria"])
                    want = [float(gold["probabilities"].get(key, 0.0)) for key in order]
                    if a.task != "T1":
                        assert order[it["label"]] == exp and it["target"][it["label"]] == 1.0, (split, ri, qid)
                    moved[split] += order != list(q["criteria"])
                elif q["type"] == "noul":
                    want = [float(gold["probabilities"].get("false", 0.5)), float(gold["probabilities"].get("true", 0.5))]
                    if a.task != "T1":
                        assert it["label"] == int(bool(exp)), (split, ri, qid)
                else:
                    want = [float(gold["probabilities"].get(str(i), 0.0)) for i in range(len(q["criteria"]))]
                    if a.task != "T1":
                        assert it["label"] == int(exp), (split, ri, qid)
                s = sum(want)
                assert max(abs(x - y / s) for x, y in zip(it["target"], want)) < 1e-12, (split, ri, qid)
                gold_slot["%s:%s:%d" % (split, q["type"], it["label"])] += 1
                if (split == "train" and len(built["train"]) < 20) or (split == "calib" and len(built["calib"]) < 5):
                    enc, = Agent._encode_state(fake_agent, row["state"], [qid], {qid: internal})
                    v4["checked"] += 1
                    v4["identical"] += (enc["ids"], enc["markers"], enc["qtype"]) == (it["ids"], it["markers"], it["qtype"])
                it["src"] = "%s:%d:%s" % (split, ri, qid)  # extra key: collate() reads ids/markers/target/qtype only
                built[split].append(it)
                k += 1
    assert v4["checked"] == v4["identical"], "V4: a training item differs from laya's inference sequence: %s" % v4
    if a.shuffle_options == "none" or not any(q["type"] == "choice" for r in rows["train"] for q in r["questions"].values()):
        assert moved["train"] == 0
    assert moved["calib"] == 0, "calibration items must keep the canonical option order"

    train, calib = built["train"], built["calib"]
    n = len(train) + len(calib)
    assert len(calib) <= n // 10, "calibration %d > N // 10 = %d: the script would hold out fewer items" % (len(calib), n // 10)
    order = list(range(n))
    random.Random(SPLIT_SEED).shuffle(order)
    slots = [None] * n
    for pos, it in zip(sorted(order[:len(calib)]), calib):
        slots[pos] = it
    for pos, it in zip(sorted(order[len(calib):]), train):
        slots[pos] = it
    # the script's own split of this file (min(calib_max, N // 10) with calib_max = len(calib)) must give these back
    n_cal = min(len(calib), n // 10)
    assert [slots[i]["src"] for i in sorted(order[:n_cal])] == [it["src"] for it in calib]
    assert [slots[i]["src"] for i in sorted(order[n_cal:])] == [it["src"] for it in train]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(slots, out)
    lens = sorted(len(it["ids"]) for it in train)
    ex = train[0]
    prov = {"items": rel(out), "items_sha256": sha256(out.read_bytes()), "task": a.task, "base": a.base, "base_dir": rel(base),
            "script": rel(FT_SCRIPT), "script_sha256": ft_sha, "budget": budget, "seed": a.seed,
            "n_items": n, "n_train": len(train), "n_calib": len(calib), "calib_max": len(calib),
            "rows": {s: {"path": rel(p), "sha256": sha256(p.read_bytes()), "rows_total": len(src[s]), "rows_used": len(pick[s])}
                     for s, p in paths.items()},
            "subset": {"n_train": a.n_train, "n_calib": a.n_calib,
                       "rule": "random.Random(seed).shuffle(row indices), rows taken until n items, row order kept"},
            "shuffle_options": a.shuffle_options,
            "option_order": {"train": "choice: random.Random(%d + item index).shuffle(criteria keys); score/noul fixed" % a.seed
                             if a.shuffle_options == "all" else "canonical", "calib": "canonical"},
            "options_reordered": dict(moved), "gold_slot": dict(sorted((k, v) for k, v in gold_slot.items() if v)),
            "permute_labels": {"rule": "random.Random(%d).shuffle(train expected labels)" % a.seed, "changed": permuted}
            if a.permute_labels else None,
            "v4_inference_identity": v4,
            "seq_len_train": {"min": lens[0], "p50": lens[len(lens) // 2], "p90": lens[int(0.9 * (len(lens) - 1))],
                              "max": lens[-1], "mean": round(statistics.mean(lens), 1), "sum": sum(lens)},
            "decoded_example": {"src": ex["src"], "label": ex["label"], "options": option_texts(tok, ex),
                                "text": tok.decode(ex["ids"])[:1500]},
            "run_with": "--items %s --calib-max %d (never --force-preprocess)" % (rel(out), len(calib))}
    out.with_suffix(".provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("%s: %d items (train %d + calibration %d), seq_len %s, sha256 %s; V4 %d/%d identical; reordered %s; run with %s" % (
        rel(out), n, len(train), len(calib), prov["seq_len_train"], prov["items_sha256"][:12], v4["identical"], v4["checked"],
        dict(moved), prov["run_with"]))


def cmd_calibrate(a):
    import torch
    from safetensors.torch import load_file
    from transformers import AutoTokenizer

    ft, _ = load_ft()
    ck = Path(a.ckpt)
    cfg = json.loads((ck / "rl_agent_config.json").read_text())
    t0 = time.perf_counter()
    device = torch.device(a.device)
    tokenizer = AutoTokenizer.from_pretrained(ck / "tokenizer")
    model = ft.build_model(cfg, encoder_dir=ck / "encoder")
    model.load_state_dict(load_file(str(ck / "model.safetensors")), strict=True)
    model.float().to(device).eval()
    all_items = torch.load(a.items, map_location="cpu", weights_only=False)
    order = list(range(len(all_items)))
    random.Random(SPLIT_SEED).shuffle(order)
    n_calib = min(a.calib_max, len(all_items) // 10)
    calib_items = [all_items[i] for i in sorted(order[:n_calib])]
    samples = [[] for _ in range(3)]
    with torch.no_grad():
        for start in range(0, len(calib_items), a.micro_batch):
            chunk = calib_items[start:start + a.micro_batch]
            ids, attention, positions, mask, target, qtype = ft.collate(chunk, tokenizer.pad_token_id)
            logits, _ = model(ids.to(device), attention.to(device), positions.to(device), mask.to(device), qtype.to(device))
            for i, item in enumerate(chunk):
                samples[item["qtype"]].append((logits[i, :len(item["markers"])].cpu(), item["target"]))
    temperatures = [ft.fit_temperature(group) if group else 1.2 for group in samples]
    out = Path(a.out)
    shutil.copytree(ck, out)
    cfg.update({"fine_tuned": True, "model_name": cfg.get("model_name", "laya-typed-decisions"), "temperature": temperatures})
    cfg.pop("temperature_by_options", None)
    (out / "rl_agent_config.json").write_text(json.dumps(cfg, indent=2))
    meta = json.loads((out / "checkpoint_meta.json").read_text())
    meta.update(calibrated_by="poc/finetune/ft_task.py calibrate", calibrated_from=rel(ck), calibration_items=n_calib,
                samples_per_type=[len(g) for g in samples])
    (out / "checkpoint_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps({"ckpt": rel(out), "from": rel(ck), "temperatures": temperatures, "calibration_items": n_calib,
                      "samples_per_type": [len(g) for g in samples], "seconds": round(time.perf_counter() - t0, 1)}))


def cmd_devsub(a):
    """A seeded random subset of <task>_dev.jsonl (row order and header kept): the option-order flip probe's rows."""
    src = ROWS / ("%s_dev.jsonl" % a.task)
    lines = src.read_text(encoding="utf-8").split("\n")
    head = [line for line in lines if line.startswith("#")]
    body = [line for line in lines if line.strip() and not line.startswith("#")]
    idx = sorted(random.Random(a.seed).sample(range(len(body)), min(a.n, len(body))))
    out = ROWS / ("%s_dev%d.jsonl" % (a.task, a.n))
    note = "# subset: %d of the %d rows of %s (sha256 %s), random.Random(%d).sample, row order kept" % (
        len(idx), len(body), rel(src), sha256(src.read_bytes()), a.seed)
    out.write_text("\n".join(head + [note] + [body[i] for i in idx]) + "\n", encoding="utf-8")
    print("%s: %d rows, sha256 %s" % (rel(out), len(idx), sha256(out.read_bytes())))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("items")
    s.add_argument("--task", required=True)
    s.add_argument("--base", choices=sorted(BASES), required=True)
    s.add_argument("--n-train", type=int, default=0, help="items from a seeded random subset of train rows, 0 = all")
    s.add_argument("--n-calib", type=int, default=0, help="calibration items from a seeded subset, 0 = all")
    s.add_argument("--seed", type=int, default=13)
    s.add_argument("--shuffle-options", choices=("none", "all"), default="all")
    s.add_argument("--permute-labels", action="store_true", help="V3 control: permute the train rows' labels")
    s.add_argument("--out", required=True)
    s = sub.add_parser("calibrate")
    s.add_argument("--ckpt", required=True)
    s.add_argument("--items", required=True)
    s.add_argument("--calib-max", type=int, required=True)
    s.add_argument("--micro-batch", type=int, default=8)
    s.add_argument("--device", default="mps")
    s.add_argument("--out", required=True)
    s = sub.add_parser("devsub")
    s.add_argument("--task", required=True)
    s.add_argument("--n", type=int, default=40)
    s.add_argument("--seed", type=int, default=13)
    a = p.parse_args()
    {"items": cmd_items, "calibrate": cmd_calibrate, "devsub": cmd_devsub}[a.cmd](a)


if __name__ == "__main__":
    main()
