"""P4 training/dev rows for the router task `domain_8`, and the fine-tune script's items built from them.

    source env.sh
    .venv/bin/python poc/finetune/make_domain8_items.py rows
    .venv/bin/python poc/finetune/make_domain8_items.py items --train-n 1000 --calib-n 100 --shuffle-options none \
        --out poc/finetune/data/items_probe.pt

`rows`: MASSIVE ko train (11,514) and validation (2,033) through the builder's own scenario->domain map,
`domain` question and pool filters (scripts/build_ko_evalsets.py) into laya-evals JSONL. The test split, which
feeds data/evals/ko_massive_domain_8.jsonl, is read only to count exact-utterance overlap with it.

`items` (the adapter): rows become items through the upstream script's own `build_training_item`, with gold
{"probabilities": {<expected key>: 1.0}} -- a choice target is read by criteria key, not by index. The script
carves its calibration slice out of the items file by position (random.Random(20260922), n = min(--calib-max,
N // 10)), so the validation rows are laid exactly onto those positions: the unmodified script then trains on
the train rows and fits its temperature on the validation rows. No `<items>.meta.json` is written, so the
script takes the file as a legacy cache; a sidecar with any other key would make it re-download
LocalLLaMA/typed-decisions over this file, and so would --force-preprocess (never pass it).

Option order: the script renders options in the criteria order it is given and has no order augmentation
(zero-shot flip 0.270, results/C/C1_option_order_20261002.md). With --shuffle-options all (default) each train
row's criteria keys are permuted by random.Random(seed + row index) before `build_training_item`, so the rendered
options, target and label follow the permutation while every key keeps its description and the gold key is
unchanged. Validation rows (the calibration slice) keep the canonical order. Every item is decoded back through
the tokenizer to check the rendered order, each option's text, and that the target's gold slot holds the gold key.
"""
import argparse
import hashlib
import importlib.util
import json
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_ko_evalsets as bk  # noqa: E402  (sets HF_HOME to the pinned data/raw/hf cache before datasets loads)
import datasets  # noqa: E402
from laya.evals import Dataset, questions_fingerprint  # noqa: E402

DATA = ROOT / "poc/finetune/data"
EVAL = ROOT / "data/evals/ko_massive_domain_8.jsonl"
FT_SCRIPT = ROOT / "third_party/laya/notebooks/laya_finetune_typed_decisions_mps.py"
FILES = {"train": DATA / "domain8_train.jsonl", "validation": DATA / "domain8_dev.jsonl"}
STATS = ROOT / "results/P4/domain8_rows_stats.json"
HEADER = "# make_domain8_items "
SPLIT_SEED = 20260922
SPLIT_LINES = ("random.Random(20260922).shuffle(order)",  # the hold-out `items` relies on, read from the source
               "n_calib = min(args.calib_max, len(all_items) // 10)",
               "calib_items = [all_items[i] for i in sorted(order[:n_calib])]",
               "train_items = [all_items[i] for i in sorted(order[n_calib:])]")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def router_question():
    q = bk.question(bk.DOMAIN_Q, argparse.Namespace(instructions="en"), "ko")
    ref = bk.read_rows(EVAL)[0]["questions"]["domain"]
    assert json.dumps(q, ensure_ascii=False) == json.dumps(ref, ensure_ascii=False), "question differs from %s" % EVAL
    return q


def pool(split):
    to_domain = {s: k for k, (scenarios, _, _) in bk.DOMAINS.items() for s in scenarios}
    d = datasets.load_dataset(bk.MASSIVE["dataset"], "ko", split=split, revision=bk.MASSIVE["revision"])
    items = [{"id": int(r["id"]), "state": {"utterance": r["text"]}, "scenario": bk.scenario_of(r["label_text"]),
              "label": to_domain[bk.scenario_of(r["label_text"])]} for r in d]
    return bk.pool_of(items)


def rows(args):
    q = router_question()
    texts = {"eval500": {r["state"]["utterance"] for r in bk.read_rows(EVAL)},
             "test_pool": {it["state"]["utterance"] for it in pool("test")[0]}}
    stats = {}
    for split, path in FILES.items():
        items, info = pool(split)
        dist = Counter(it["label"] for it in items)
        meta = {"builder": "poc/finetune/make_domain8_items.py", "created": "2026-10-02",
                "source": bk.hf_source({**bk.MASSIVE, "split": split}, "ko"), "license": bk.LICENSE["massive"],
                "question": "scripts/build_ko_evalsets.py DOMAIN_Q, instructions en, descriptions ko "
                            "(asserted equal to data/evals/ko_massive_domain_8.jsonl)",
                "pool": info, "label_distribution": dict(sorted(dist.items(), key=lambda kv: (-kv[1], kv[0])))}
        lines = [HEADER + json.dumps(meta, ensure_ascii=False), "# split: %s" % ("train" if split == "train" else "dev")]
        lines += [json.dumps(bk.row(it["state"], {"domain": q}, {"domain": it["label"]},
                                    ["massive", "domain8", "split:" + split, "scenario:" + it["scenario"]]),
                             ensure_ascii=False) for it in items]
        data = ("\n".join(lines) + "\n").encode("utf-8")
        path.write_bytes(data)
        check = subprocess.run([str(bk.LAYA_EVALS), "validate", str(path)], capture_output=True, text=True)
        assert check.returncode == 0, check.stdout + check.stderr
        own = {it["state"]["utterance"] for it in items}
        stats[split] = {"path": bk.rel(path), "rows": len(items), "pool": info, "sha256": sha256(data),
                        "questions_sha256": questions_fingerprint(Dataset.from_jsonl(str(path))),
                        "label_distribution": meta["label_distribution"],
                        "scenario_distribution": dict(Counter(it["scenario"] for it in items).most_common()),
                        "utterance_overlap": {k: len(own & v) for k, v in texts.items()}, "_texts": own}
        print("%-20s rows=%d dropped=%s sha256=%s questions_sha256=%s | %s" % (
            path.name, len(items), info["dropped"], stats[split]["sha256"][:12], stats[split]["questions_sha256"][:12],
            check.stdout.strip()))
    ref_qsha = questions_fingerprint(Dataset.from_jsonl(str(EVAL)))
    assert all(s["questions_sha256"] == ref_qsha for s in stats.values()), "questions_sha256 differs from %s" % EVAL
    stats["train"]["utterance_overlap"]["validation"] = len(stats["train"]["_texts"] & stats["validation"]["_texts"])
    for s in stats.values():
        s.pop("_texts")
    STATS.parent.mkdir(parents=True, exist_ok=True)
    STATS.write_text(json.dumps({"eval_questions_sha256": ref_qsha, **stats}, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
    for split, s in stats.items():
        print("%-10s labels %s | exact-utterance overlap %s" % (split, s["label_distribution"], s["utterance_overlap"]))


def load_ft():
    src = FT_SCRIPT.read_text(encoding="utf-8")
    missing = [line for line in SPLIT_LINES if line not in src]
    assert not missing, "upstream calibration hold-out changed, the position layout is void: %s" % missing
    spec = importlib.util.spec_from_file_location("laya_ft_mps", FT_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, sha256(src.encode("utf-8"))


def rendered_keys(tok, it, criteria):
    """Option keys in the order the item's ids render them, decoded back; each option must read `<key>: <description>`."""
    bounds = it["markers"] + [it["ids"].index(tok.sep_token_id, it["markers"][-1])]
    keys = []
    for a, b in zip(bounds, bounds[1:]):
        text = tok.decode(it["ids"][a + 1:b]).strip()
        keys.append(text.split(":")[0])
        assert text == "%s: %s" % (keys[-1], criteria[keys[-1]]), (it["src"], text)
    return keys


def sample(rows_, n, seed):
    """Row indices: all, or the builder's stratifier (equal quota per domain, seed 13), in row order."""
    if not n:
        return list(range(len(rows_)))
    picked, _ = bk.stratify([{"id": i, "label": r["expected"]["domain"]} for i, r in enumerate(rows_)],
                            list(bk.DOMAINS), n, seed)
    return [it["id"] for it in picked]


def items(args):
    import torch
    from transformers import AutoTokenizer
    from laya.agent import Agent
    from laya.common import build_sequence

    ft, ft_sha = load_ft()
    model_dir = Path(args.model_dir).resolve()
    cfg = json.loads((model_dir / "rl_agent_config.json").read_text())
    budget = {"max_len": cfg.get("max_len", 1024), "head_max_len": cfg.get("head_max_len", 256)}  # as prepare_items
    tok = AutoTokenizer.from_pretrained(model_dir / "tokenizer")
    src = {split: bk.read_rows(path) for split, path in FILES.items()}
    picks = {"train": sample(src["train"], args.train_n, args.seed),
             "validation": sample(src["validation"], args.calib_n, args.seed)}

    def make(split, i):
        row = src[split][i]
        (qid, q), = row["questions"].items()
        gold = row["expected"][qid]
        if split == "train" and args.shuffle_options == "all":
            keys = list(q["criteria"])
            random.Random(args.seed + i).shuffle(keys)
            q = {**q, "criteria": {k: q["criteria"][k] for k in keys}}
        it = ft.build_training_item(tok, {**cfg, **budget}, row["state"], q, {"probabilities": {gold: 1.0}})
        assert it is not None and list(q["criteria"])[it["label"]] == gold and it["target"][it["label"]] == 1.0
        it["src"] = "%s:%d" % (split, i)  # extra key: collate() reads only ids/markers/target/qtype
        return it

    built = {split: [make(split, i) for i in idx] for split, idx in picks.items()}
    moved, gold_slot = Counter(), {split: Counter() for split in built}
    for split in built:
        for k, it in enumerate(built[split]):
            row = src[split][int(it["src"].split(":")[1])]
            q, gold = row["questions"]["domain"], row["expected"]["domain"]
            keys = rendered_keys(tok, it, q["criteria"])
            assert sorted(keys) == sorted(q["criteria"]) and keys[it["label"]] == gold, it["src"]
            moved[split] += keys != list(q["criteria"])
            gold_slot[split][it["label"]] += 1
            # training sequence == inference sequence for that order (Agent._encode_state builds through the same function)
            if k < 20:
                ids, markers = build_sequence(tok, row["state"], Agent._to_internal(
                    {**q, "criteria": {key: q["criteria"][key] for key in keys}}), budget["max_len"], budget["head_max_len"])
                assert (ids, markers) == (it["ids"], it["markers"]), it["src"]
    assert moved["validation"] == 0, "calibration rows must keep the canonical option order"
    assert moved["train"] >= 0.9 * len(built["train"]) if args.shuffle_options == "all" else moved["train"] == 0, moved
    ex = built["train"][0]
    ex_row = src["train"][int(ex["src"].split(":")[1])]
    example = {"src": ex["src"], "gold": ex_row["expected"]["domain"], "label": ex["label"],
               "rendered_keys": rendered_keys(tok, ex, ex_row["questions"]["domain"]["criteria"])}
    train, calib = built["train"], built["validation"]
    n = len(train) + len(calib)
    assert len(calib) <= n // 10, "--calib-n %d > N // 10 = %d: the script would hold out fewer rows" % (len(calib), n // 10)
    order = list(range(n))
    random.Random(SPLIT_SEED).shuffle(order)
    slots = [None] * n
    for pos, it in zip(sorted(order[:len(calib)]), calib):
        slots[pos] = it
    for pos, it in zip(sorted(order[len(calib):]), train):
        slots[pos] = it
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(slots, out)
    lens = sorted(len(it["ids"]) for it in slots)
    prov = {"items": bk.rel(out), "items_sha256": sha256(out.read_bytes()), "script": bk.rel(FT_SCRIPT),
            "script_sha256": ft_sha, "model_dir": bk.rel(model_dir), "budget": budget, "seed": args.seed,
            "calib_max": len(calib), "n_items": n, "n_train": len(train), "n_calib": len(calib),
            "sources": {split: {"path": bk.rel(FILES[split]), "sha256": sha256(FILES[split].read_bytes()),
                                "rows": len(src[split]), "picked": len(picks[split]),
                                "label_distribution": dict(Counter(src[split][i]["expected"]["domain"]
                                                                   for i in picks[split]).most_common())}
                        for split in FILES},
            "calib_rows": picks["validation"],
            "shuffle_options": args.shuffle_options,
            "option_order": {"train": "random.Random(%d + row index).shuffle(criteria keys)" % args.seed
                             if args.shuffle_options == "all" else "canonical", "validation": "canonical"},
            "options_reordered": {split: moved[split] for split in built},
            "gold_slot": {split: dict(sorted(c.items())) for split, c in gold_slot.items()},
            "decoded_example": example,
            "seq_len": {"min": lens[0], "p50": lens[n // 2], "max": lens[-1], "distinct": len(set(lens))},
            "run_with": "--items %s --calib-max %d (never --force-preprocess)" % (bk.rel(out), len(calib))}
    out.with_suffix(".provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1) + "\n",
                                                   encoding="utf-8")
    print("%s: %d items (train %d + calibration %d), seq_len %s, sha256 %s; run with %s" % (
        bk.rel(out), n, len(train), len(calib), prov["seq_len"], prov["items_sha256"][:12], prov["run_with"]))
    print("option order (--shuffle-options %s): reordered train %d/%d, validation %d/%d; gold slot %s" % (
        args.shuffle_options, moved["train"], len(train), moved["validation"], len(calib), prov["gold_slot"]))
    print("decoded %s (gold %s -> slot %d of %s): %s" % (example["src"], example["gold"], example["label"],
                                                       example["rendered_keys"], tok.decode(ex["ids"])))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rows")
    s = sub.add_parser("items")
    s.add_argument("--train-n", type=int, default=0, help="stratified train rows, 0 = all")
    s.add_argument("--calib-n", type=int, required=True, help="stratified validation rows for the temperature fit")
    s.add_argument("--seed", type=int, default=13)
    s.add_argument("--shuffle-options", choices=("none", "all"), default="all",
                   help="option-order shuffle of the train items (validation keeps the canonical order)")
    s.add_argument("--model-dir", default=str(ROOT / "models/laya-multilingual"))
    s.add_argument("--out", required=True)
    args = p.parse_args()
    datasets.disable_progress_bars()
    {"rows": rows, "items": items}[args.cmd](args)


if __name__ == "__main__":
    main()
