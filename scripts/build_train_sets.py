"""Trained-Laya arm (T3arm, 2026-10-08): per-task training / dev / calibration rows and the Laya-only extended
evaluation sets, all in the evaluation format of data/evals/jev_cmp (docs/09_laya_vs_jev_plan.md §3-§4).

    source env.sh && export HF_HOME=$PWD/data/raw/hf HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1
    .venv/bin/python scripts/build_train_sets.py all        # ext sets + their MANIFEST, then train/dev/calib rows + stats
    .venv/bin/python scripts/build_train_sets.py ext        # data/evals/jev_cmp_ext/ only
    .venv/bin/python scripts/build_train_sets.py rows       # poc/finetune/data/t3arm/ only (needs the ext sets)

Rendering is scripts/build_jev_cmp_sets.py's: its row(), question constants, label maps and option samplers, and
`check_format` asserts that the row builders here reproduce every Jev-set row from the same source item (T4/T7
options are sampled per row, so there the instructions, rendering rule and label universe are asserted instead).
Sampling, dedup and length rules are build_ko_evalsets.py's (pool_of: exact-state dedup, every state field 2-2000
chars; stratify: equal quota per label, seed 13). Every sample here is stratified, train included.

Ext sets (data/evals/jev_cmp_ext/): test split (T5: validation, T10: hash-test part), rows whose normalized state text
also occurs in the train split dropped, n=500 stratified (T1: the whole 400-case test; T8: all 116 test rows; T7:
100 ids x 5 languages, the same ids and options in every language).
Rows (poc/finetune/data/t3arm/<task>_{train,dev,calib}.jsonl): train <= 5,000 rows (T1: 1,000 cases = 5,000
decisions; T7: 1,000 per language; T8: every row left after the hold-out); dev <= 1,000 and calib 400 from the
validation split where one exists (T3, T6, T7), else held out of train first (T10: the hash-dev part). A train/dev/calib
candidate whose state text equals, exactly or after case/whitespace normalization, any evaluation item (every
data/evals/jev_cmp and data/evals/jev_cmp_ext row of any task) is removed before sampling; the counts go to
results/T3arm/data_stats.json. T1 rows carry the dataset's teacher `gold` per question (soft training targets);
`expected` is the argmax, as in the eval files.
"""
import argparse
import hashlib
import json
import random
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_jev_cmp_sets as jb  # noqa: E402  (imports build_ko_evalsets, which pins HF_HOME)

import datasets  # noqa: E402
import laya  # noqa: E402
from laya.evals import Dataset, questions_fingerprint  # noqa: E402

bk = jb.bk
BUILDER = "scripts/build_train_sets.py 0.1.0"
CREATED = "2026-10-08"
HEADER = "# build_train_sets "
SEED = 13
N_TRAIN, N_DEV, N_CALIB, N_EXT = 5000, 1000, 400, 500
T1_CASES = {"calib": 80, "dev": 120, "train": 1000}           # x 5 decisions each
T7_PER_LANG = {"calib": 80, "dev": 200, "train": 1000, "ext_ids": 100}
T8_HOLDOUT = {"calib": 40, "dev": 60}                          # 546 train rows, no validation split
EXT = ROOT / "data/evals/jev_cmp_ext"
ROWS = ROOT / "poc/finetune/data/t3arm"
STATS = ROOT / "results/T3arm/data_stats.json"
LANGS = jb.SRC["T7"]["config"]
TASKS = ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10")
BASE = {t: "multilingual" if t == "T7" else "english" for t in TASKS}  # the Router's base per task (user, 2026-10-08)


# ---------------------------------------------------------------- source items ({id, state, label, tags})
def items(task, split, lang=None):
    if task == "T1":
        out = []
        for r in jb.load("T1", split=split):
            state = r["state"]
            try:  # bench_local.py:232-236, as jb.t1
                state = json.loads(state)
            except ValueError:
                pass
            out.append({"id": r["id"], "label": r["workflow"], "state": state, "questions": json.loads(r["questions"]),
                        "gold": json.loads(r["gold"]), "tags": ["typed_decisions", "workflow:" + r["workflow"], "id:" + r["id"]]})
        return out
    if task == "T7":
        return [{"id": int(r["id"]), "state": {"utterance": r["text"]}, "label": r["label_text"],
                 "tags": ["massive", "intent10", "scenario:" + bk.scenario_of(r["label_text"]), "id:%d" % int(r["id"])],
                 "lang": lang} for r in jb.load("T7", lang, split=split)]
    if task == "T9":
        return jb.t9_items(split)
    if task == "T10":
        return [it for it in jb.t10_items() if it["part"] == split]
    d = jb.load(task, split=split)
    if task == "T2":
        keys = list(jb.AG_NEWS[2])
        return [{"id": i, "state": {"article": r["text"]}, "label": keys[r["label"]], "tags": ["ag_news", "id:%d" % i]}
                for i, r in enumerate(d)]
    if task == "T3":
        names = jb.EMOTION[2]
        assert d.features["label"].names == names
        return [{"id": i, "state": {"text": r["text"]}, "label": names[r["label"]], "tags": ["emotion", "id:%d" % i]}
                for i, r in enumerate(d)]
    if task == "T4":
        return [{"id": i, "state": {"message": r["text"]}, "label": r["label_text"], "tags": ["banking77", "id:%d" % i]}
                for i, r in enumerate(d)]
    if task == "T5":
        return [{"id": i, "state": {"passage": r["passage"], "question": r["question"]}, "label": bool(r["answer"]),
                 "tags": ["boolq", "id:%d" % i]} for i, r in enumerate(d)]
    if task == "T6":
        levels = jb.SST5[2]
        assert all(levels[r["label"]] == r["label_text"] for r in d)
        return [{"id": i, "state": {"text": r["text"]}, "label": int(r["label"]), "tags": ["sst5", "id:%d" % i]}
                for i, r in enumerate(d)]
    if task == "T8":
        return [{"id": i, "state": {"text": r["text"]}, "label": r["label"] == 1, "tags": ["prompt_injections", "id:%d" % i]}
                for i, r in enumerate(d)]
    raise KeyError(task)


# split names per task: ext source, the split holding train rows, and where dev/calib come from
SPLITS = {"T1": ("test", "train", "train"), "T2": ("test", "train", "train"), "T3": ("test", "train", "validation"),
          "T4": ("test", "train", "train"), "T5": ("validation", "train", "train"), "T6": ("test", "train", "validation"),
          "T7": ("test", "train", "validation"), "T8": ("test", "train", "train"), "T9": ("test", "train", "train"),
          "T10": ("test", "train", "dev")}


# ---------------------------------------------------------------- rows in the jev_cmp format
def labels_of(task):
    """Label universe (stratification order) of a task, as the Jev builder uses it."""
    if task == "T1":
        return sorted({it["label"] for it in items("T1", "test")})
    if task == "T2":
        return list(jb.AG_NEWS[2])
    if task == "T3":
        return list(jb.EMOTION[2])
    if task == "T4":
        order = sorted(set(jb.load("T4")["label_text"]))
        random.Random(SEED).shuffle(order)  # as jb.t4
        return order
    if task in ("T5", "T8", "T9"):
        return [True, False]
    if task == "T6":
        return list(range(len(jb.SST5[2])))
    if task == "T7":
        labs = None
        for lang in LANGS:
            got = sorted(set(jb.load("T7", lang)["label_text"]))
            assert labs in (None, got), lang
            labs = got
        return labs
    if task == "T10":
        return list(jb.QUEUES)
    raise KeyError(task)


def fixed_question(task):
    """(qid, question) of the tasks whose question does not depend on the row."""
    if task == "T2":
        qid, ins, crit = jb.AG_NEWS
        return qid, {"type": "choice", "instructions": ins, "criteria": dict(crit)}
    if task == "T3":
        qid, ins, names = jb.EMOTION
        return qid, {"type": "choice", "instructions": ins, "criteria": {n: None for n in names}}
    if task == "T5":
        qid, ins = jb.BOOLQ
        return qid, {"type": "noul", "instructions": ins}
    if task == "T6":
        qid, ins, levels = jb.SST5
        return qid, {"type": "score", "instructions": ins, "criteria": list(levels)}
    if task == "T8":
        qid, ins = jb.INJECTION
        return qid, {"type": "noul", "instructions": ins}
    if task == "T9":
        qid, ins = jb.SPAM
        return qid, {"type": "noul", "instructions": ins}
    if task == "T10":
        return "queue", {"type": "choice", "instructions": jb.QUEUE_INS, "criteria": dict(jb.QUEUES)}
    return None


def t1_row(c, i):
    """jb.t1's per-case row and teacher-distribution records (expected = argmax, first maximum; noul p(true) >= 0.5)."""
    expected, dists = {}, []
    for qid, q in c["questions"].items():
        g = c["gold"][qid]
        probs = g.get("probabilities", {})
        if q["type"] == "choice":
            opts = list(q["criteria"])
            soft = [float(probs.get(k, 0.0)) for k in opts]
            arg = max(range(len(opts)), key=soft.__getitem__)
            exp, label_idx = opts[arg], opts.index(str(g["label"]))
        elif q["type"] == "score":
            opts = [str(k) for k in range(len(q["criteria"]))]
            soft = [float(probs.get(k, 0.0)) for k in opts]
            arg = max(range(len(opts)), key=soft.__getitem__)
            exp, label_idx = arg, int(g["label"])
        else:
            opts = ["false", "true"]
            pt = float(probs.get("true", g.get("noul", 0.5)))
            soft, arg = [1 - pt, pt], int(pt >= 0.5)
            exp, label_idx = pt >= 0.5, int(str(g["label"]).lower() == "true")
        expected[qid] = exp
        rec = {"row": i, "case_id": c["id"], "workflow": c["label"], "qid": qid, "type": q["type"], "options": opts,
               "soft": soft, "expected": exp, "argmax_idx": arg, "label_upstream": str(g["label"]), "label_idx": label_idx,
               "label_ne_argmax": label_idx != arg, "tie": sorted(soft)[-1] == sorted(soft)[-2]}
        if q["type"] == "score":
            rec["gold_score"] = float(g.get("score", float(g["label"])))
        dists.append(rec)
    return jb.row(c["state"], c["questions"], expected, c["tags"], "en"), dists


class RowMaker:
    """Builds jev_cmp-format rows for one task; T4/T7 draw options from one random.Random(13) stream per maker,
    consumed in row order (as jb.t4 / jb.t7 do over their rows)."""

    def __init__(self, task, labels):
        self.task, self.labels, self.rng = task, labels, random.Random(SEED)
        self.fixed = fixed_question(task)

    def options(self, gold):
        assert gold in self.labels, (self.task, gold)
        keys = [gold] + self.rng.sample([k for k in self.labels if k != gold], jb.MAX_OPTIONS - 1)
        self.rng.shuffle(keys)
        return keys

    def __call__(self, it, extra_tags=()):
        tags = list(it["tags"]) + list(extra_tags)
        t = self.task
        if t == "T1":
            r, _ = t1_row({**it, "tags": tags}, 0)
            return r
        if self.fixed:
            qid, q = self.fixed
            return jb.row(it["state"], {qid: q}, {qid: it["label"]}, tags, None if t == "T8" else "en")
        if t == "T4":
            keys = self.options(it["label"])
            q = {"type": "choice", "instructions": jb.BANKING_INS, "criteria": {k.replace("_", " "): None for k in keys}}
            return jb.row(it["state"], {"intent": q}, {"intent": it["label"].replace("_", " ")}, tags, "en")
        if t == "T7":
            keys = self.options(it["label"])
            q = {"type": "choice", "instructions": jb.INTENT_INS, "criteria": {k: bk.render_key(k) for k in keys}}
            return jb.row(it["state"], {"intent": q}, {"intent": it["label"]}, tags, it["lang"])
        raise KeyError(t)


def jev_files(task):
    if task == "T7":
        return [jb.OUT / ("T7_massive_intent_10opt_%s_20.jsonl" % lang) for lang in LANGS]
    return sorted(p for p in jb.OUT.glob("%s_*.jsonl" % task) if not p.stem.endswith("_v0") and "noulnocrit" not in p.stem)


def check_format(task, labels):
    """The row builders reproduce the Jev rows from their own source items (T4/T7: question template only)."""
    n = 0
    for path in jev_files(task):
        for r in bk.read_rows(path):
            sid = next(t[3:] for t in r["tags"] if t.startswith("id:"))
            if task in ("T4", "T7"):
                (qid, q), = r["questions"].items()
                assert q["instructions"] == (jb.BANKING_INS if task == "T4" else jb.INTENT_INS), path
                if task == "T4":
                    assert all(v is None for v in q["criteria"].values()), path
                    assert set(q["criteria"]) <= {k.replace("_", " ") for k in labels}, path
                else:
                    assert q["criteria"] == {k: bk.render_key(k) for k in q["criteria"]} and set(q["criteria"]) <= set(labels)
                n += 1
                continue
            src = _source_index(task)[sid]
            mine = {k: v for k, v in RowMaker(task, labels)(src).items()}
            theirs = {k: v for k, v in r.items() if k != "jev"}
            assert json.dumps(mine, ensure_ascii=False) == json.dumps(theirs, ensure_ascii=False), (path, sid)
            n += 1
    return n


_SRC_CACHE = {}


def _source_index(task):
    if task not in _SRC_CACHE:
        split = jb.SRC[task]["split"] if task != "T10" else "test"
        _SRC_CACHE[task] = {str(it["id"]): it for it in items(task, split)}
    return _SRC_CACHE[task]


# ---------------------------------------------------------------- overlap keys
def keys(state):
    return jb.state_text(state), jb.norm_text(state)


def eval_keys():
    """Exact and normalized state texts of every evaluation row: data/evals/jev_cmp and data/evals/jev_cmp_ext."""
    exact, norm, per_file = set(), set(), {}
    for path in sorted(list(jb.OUT.glob("T*.jsonl")) + list(EXT.glob("T*.jsonl"))):
        rows = bk.read_rows(path)
        for r in rows:
            e, n = keys(r["state"])
            exact.add(e)
            norm.add(n)
        per_file[bk.rel(path)] = len(rows)
    return exact, norm, per_file


def drop_overlap(pool, exact, norm):
    keep, hit = [], Counter()
    for it in pool:
        e, n = keys(it["state"])
        if e in exact:
            hit["exact"] += 1
        elif n in norm:
            hit["normalized_only"] += 1
        else:
            keep.append(it)
    return keep, {"exact": hit["exact"], "normalized_only": hit["normalized_only"]}


def take(pool, labels, n, seed=SEED):
    """bk.stratify, and the rest of the pool (pool order kept)."""
    picked, info = bk.stratify(pool, labels, n, seed)
    got = {it["id"] for it in picked}
    return picked, [it for it in pool if it["id"] not in got], info


# ---------------------------------------------------------------- writing
def sha256(data):
    return hashlib.sha256(data).hexdigest()


def dumps(obj):
    """json.dumps(ensure_ascii=False) with U+0085/U+2028/U+2029 escaped: same JSON value, but str.splitlines()
    (scripts/metrics_extra.py read_dataset) no longer breaks a row at an Enron NEL character."""
    return json.dumps(obj, ensure_ascii=False).replace("\x85", "\\u0085").replace("\u2028", "\\u2028").replace(
        "\u2029", "\\u2029")


def write_jsonl(args, path, rows, meta):
    header = HEADER + dumps({"builder": BUILDER, "created": CREATED, **meta})
    data = ("\n".join([header] + [dumps(r) for r in rows]) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    check = subprocess.run([str(bk.LAYA_EVALS), "validate", str(tmp)], capture_output=True, text=True)
    if check.returncode:
        tmp.unlink()
        sys.exit("%s: laya-evals validate failed\n%s%s" % (path.name, check.stdout, check.stderr))
    old, new = (sha256(path.read_bytes()) if path.exists() else None), sha256(data)
    if old not in (None, new) and not args.force:
        tmp.unlink()
        sys.exit("%s exists with sha256 %s but this build gives %s; it changes only with --force" % (bk.rel(path), old, new))
    tmp.replace(path)
    print("%-48s n=%-5d sha256=%s %s" % (bk.rel(path), len(rows), new[:12], "unchanged" if old == new else "written"))
    return new


def meta_of(task, name, **extra):
    s = jb.SRC[task]
    return {"set": name, "task": task, "source": {"dataset": s["dataset"], "config": s["config"], "revision": s["revision"]},
            "license": jb.LICENSE[task], "in_training_mix": jb.TRAINING[task][0], **extra}


# ---------------------------------------------------------------- ext sets
def train_norm(task):
    """Normalized state texts of every row of the task's training data (all languages for T7)."""
    if task == "T7":
        return {lang: {jb.norm_text(it["state"]) for it in items("T7", "train", lang)} for lang in LANGS}
    if task == "T10":
        return {jb.norm_text(it["state"]) for it in jb.t10_items() if it["part"] != "test"}
    return {jb.norm_text(it["state"]) for it in items(task, "train")}


def ext_task(args, task):
    split = SPLITS[task][0]
    labels = labels_of(task)
    out = {}
    if task == "T1":
        cases = sorted(items("T1", split), key=lambda c: c["id"])
        tr = train_norm("T1")
        ov = sum(jb.norm_text(c["state"]) in tr for c in cases)
        rows, dists = [], []
        for i, c in enumerate(cases):
            r, d = t1_row(c, i)
            rows.append(r)
            dists += d
        name = "T1_typed_decisions_test400"
        sha = write_jsonl(args, EXT / (name + ".jsonl"), rows, meta_of(
            "T1", name, split=split, selection="the whole test split, case id order (bench_local.py Part B: 400 cases / "
            "2,000 decisions)", expected="choice/score: argmax of the teacher distribution (first maximum); noul: p(true) >= 0.5",
            train_overlap={"normalized_matches": ov, "rule": "kept (the full test split is the published benchmark)"}))
        doc = {"set": bk.rel(EXT / (name + ".jsonl")), "set_sha256": sha, "source": jb.source("T1") | {"split": split},
               "note": "same fields as results/F/jev_cmp/t1_gold_dists.json (scripts/build_jev_cmp_sets.py t1)",
               "label_ne_argmax": sum(x["label_ne_argmax"] for x in dists), "ties": sum(x["tie"] for x in dists),
               "decisions": dists}
        (EXT / (name + "_gold_dists.json")).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        out[name] = {"n": len(rows), "decisions": len(dists), "train_overlap_normalized": ov}
        return out
    if task == "T7":
        tr = train_norm("T7")
        data = {lang: {it["id"]: it for it in items("T7", split, lang)} for lang in LANGS}
        ids = sorted(set.intersection(*(set(v) for v in data.values())))
        bad = {i for i in ids for lang in LANGS if jb.norm_text(data[lang][i]["state"]) in tr[lang]}
        cand = [{"id": i, "label": data["en"][i]["label"]} for i in ids if i not in bad]
        for c in cand:
            assert len({data[lang][c["id"]]["label"] for lang in LANGS}) == 1
        picked, info = bk.stratify(cand, labels, T7_PER_LANG["ext_ids"], SEED)
        maker = RowMaker("T7", labels)
        crit = {}
        for c in picked:  # one option stream over the ids: every language gets the same options for an id
            keys_ = maker.options(c["label"])
            crit[c["id"]] = {"type": "choice", "instructions": jb.INTENT_INS,
                             "criteria": {k: bk.render_key(k) for k in keys_}}
        for lang in LANGS:
            rows = [jb.row(data[lang][c["id"]]["state"], {"intent": crit[c["id"]]}, {"intent": c["label"]},
                           data[lang][c["id"]]["tags"], lang) for c in picked]
            name = "T7_massive_intent_10opt_%s_ext100" % lang
            write_jsonl(args, EXT / (name + ".jsonl"), rows, meta_of(
                "T7", name, split=split, config=lang, ids=[c["id"] for c in picked],
                pool={"ids_in_all_languages": len(ids), "ids_dropped_train_overlap_any_language": len(bad),
                      "sample": info}, options="random.Random(13), one stream over the ids: 9 other labels, shuffle"))
            out[name] = {"n": len(rows), "train_overlap_excluded_ids": len(bad), "sample": info}
        return out
    tr = train_norm(task)
    pool, info = bk.pool_of(items(task, split))
    keep = [it for it in pool if jb.norm_text(it["state"]) not in tr]
    info["train_overlap_excluded"] = len(pool) - len(keep)
    if task == "T8":
        assert info["pool_rows"] == info["source_rows"] == 116, info
        if info["train_overlap_excluded"]:  # all 116 stay: the train rows that match them are removed instead
            info["train_overlap_kept_in_ext"] = info.pop("train_overlap_excluded")
        picked, info["sample"] = pool, {"all": len(pool)}
        name = "T8_prompt_injections_test116"
    else:
        picked, info["sample"] = bk.stratify(keep, labels, N_EXT, SEED)
        name = {"T2": "T2_ag_news_ext500", "T3": "T3_emotion_ext500", "T4": "T4_banking77_10opt_ext500",
                "T5": "T5_boolq_ext500", "T6": "T6_sst5_ext500", "T9": "T9_enron_spam_ext500",
                "T10": "T10_support_tickets_queue_ext500"}[task]
    maker = RowMaker(task, labels)
    rows = [maker(it) for it in picked]
    write_jsonl(args, EXT / (name + ".jsonl"), rows, meta_of(task, name, split=split, pool=info,
                                                             stratify_labels=[str(x) for x in labels]))
    out[name] = {"n": len(rows), **{k: info.get(k) for k in ("source_rows", "pool_rows", "dropped", "train_overlap_excluded",
                                                             "train_overlap_kept_in_ext")}}
    return out


def ext_manifest():
    files = {}
    jev_norm = {}
    for path in jb.OUT.glob("T*.jsonl"):
        for r in bk.read_rows(path):
            jev_norm.setdefault(path.name[:3].rstrip("_"), set()).add(jb.norm_text(r["state"]))
    for path in sorted(EXT.glob("T*.jsonl")):
        meta, rows = _header(path), bk.read_rows(path)
        dist = {}
        for r in rows:
            for qid, exp in r["expected"].items():
                dist.setdefault(qid, Counter())[exp if isinstance(exp, str) else json.dumps(exp)] += 1
        task = meta["task"]
        files[path.name] = {
            "path": bk.rel(path), "sha256": sha256(path.read_bytes()),
            "questions_sha256": questions_fingerprint(Dataset.from_jsonl(str(path))), "n": len(rows),
            "decisions": sum(len(r["expected"]) for r in rows), "task": task, "source": meta.get("source"),
            "split": meta.get("split"), "license": meta.get("license"), "in_training_mix": jb.TRAINING[task][0],
            "base_for_trained_arm": BASE[task], "pool": meta.get("pool"),
            "label_distribution": {q: dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))) for q, c in dist.items()},
            "majority_rate": {q: round(max(c.values()) / sum(c.values()), 4) for q, c in dist.items()},
            "duplicates": bk.count_duplicates(rows),
            "rows_also_in_jev_cmp_set": sum(jb.norm_text(r["state"]) in jev_norm.get(task, set()) for r in rows),
        }
    gold = EXT / "T1_typed_decisions_test400_gold_dists.json"
    doc = {"version": 1, "builder": BUILDER, "laya_version": laya.__version__,
           "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
           "purpose": "Laya-only extended evaluation sets for the vanilla vs trained Laya comparison (T3arm); never sent to Jev",
           "t1_gold_dists": {"path": bk.rel(gold), "sha256": sha256(gold.read_bytes())} if gold.exists() else None,
           "files": files}
    (EXT / "MANIFEST.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("jev_cmp_ext/MANIFEST.json: %d files" % len(files))


def _header(path):
    with open(path, encoding="utf-8") as f:
        first = f.readline()
    return json.loads(first[len(HEADER):])


# ---------------------------------------------------------------- train / dev / calib rows
def rows_task(args, task, ex, nm):
    labels = labels_of(task)
    st = {"task": task, "base": BASE[task], "jev_rows_reproduced": check_format(task, labels)}
    _, train_split, hold_split = SPLITS[task]
    langs = LANGS if task == "T7" else [None]
    out = {"train": [], "dev": [], "calib": []}
    info = {}
    for lang in langs:
        tag = lang or "all"
        src = items(task, train_split, lang)
        if task == "T1":
            assert len({json.dumps(c["state"], sort_keys=True) for c in src}) == len(src)
            pool, pinfo = sorted(src, key=lambda c: c["id"]), {"source_rows": len(src), "pool_rows": len(src), "dropped": {}}
        else:
            pool, pinfo = bk.pool_of(src)
        if task == "T7":
            out_of_universe = [it for it in pool if it["label"] not in labels]
            pool = [it for it in pool if it["label"] in labels]
            pinfo["dropped_label_not_in_eval_set"] = len(out_of_universe)
        pool, removed = drop_overlap(pool, ex, nm)
        info[tag] = {"train_split": train_split, "pool": pinfo, "eval_overlap_removed": {"train_pool": removed}}
        if hold_split == train_split:  # dev/calib held out of the train split first
            hpool = pool
        else:
            hsrc = items(task, hold_split, lang)
            hpool, hinfo = bk.pool_of(hsrc)
            if task == "T7":
                hpool = [it for it in hpool if it["label"] in labels]
            hpool, hremoved = drop_overlap(hpool, ex, nm)
            info[tag].update(holdout_split=hold_split, holdout_pool=hinfo)
            info[tag]["eval_overlap_removed"]["holdout_pool"] = hremoved
        sizes = (T1_CASES if task == "T1" else T7_PER_LANG if task == "T7" else
                 {"calib": T8_HOLDOUT["calib"], "dev": T8_HOLDOUT["dev"]} if task == "T8" else
                 {"calib": N_CALIB, "dev": N_DEV, "train": N_TRAIN})
        calib, hrest, i_c = take(hpool, labels, sizes["calib"])
        dev, hrest, i_d = take(hrest, labels, sizes["dev"])
        trpool = hrest if hold_split == train_split else pool
        held = {jb.norm_text(it["state"]) for it in calib + dev}  # normalized twins of dev/calib rows stay out of train
        n0 = len(trpool)
        trpool = [it for it in trpool if jb.norm_text(it["state"]) not in held]
        info[tag]["train_pool_removed_as_dev_calib_twin"] = n0 - len(trpool)
        if task == "T8":  # all that is left
            train, i_t = sorted(trpool, key=lambda it: it["id"]), {"all": len(trpool)}
        else:
            train, _, i_t = take(trpool, labels, sizes["train"])
        info[tag]["sample"] = {"calib": i_c, "dev": i_d, "train": i_t}
        for split, picked in (("train", train), ("dev", dev), ("calib", calib)):
            out[split] += [dict(it, _split=split) for it in picked]
    files = {}
    for split in ("train", "dev", "calib"):
        maker = RowMaker(task, labels)  # one option stream per output file, in row order
        rows = []
        for it in out[split]:
            r = maker(it, extra_tags=["t3arm:%s" % split])
            if task == "T1":
                r["gold"] = it["gold"]  # teacher distributions: the soft targets of the training items
            rows.append(r)
        path = ROWS / ("%s_%s.jsonl" % (task, split))
        sha = write_jsonl(args, path, rows, meta_of(task, "%s_%s" % (task, split), t3arm_split=split, base=BASE[task],
                                                    sampling=info))
        dist = Counter(str(v) for r in rows for v in r["expected"].values())
        files[split] = {"path": bk.rel(path), "sha256": sha, "rows": len(rows),
                        "decisions": sum(len(r["expected"]) for r in rows),
                        "questions_sha256": questions_fingerprint(Dataset.from_jsonl(str(path))) if task not in ("T4", "T7") else None,
                        "label_distribution": dict(sorted(dist.items(), key=lambda kv: (-kv[1], kv[0])))}
    # nothing left in the sampled rows that equals an eval item, and train/dev/calib disjoint
    texts = {s: {jb.norm_text(r["state"]) for r in bk.read_rows(ROWS / ("%s_%s.jsonl" % (task, s)))} for s in files}
    assert not any(t & nm for t in texts.values()), task
    st["split_disjoint"] = {"train&dev": len(texts["train"] & texts["dev"]), "train&calib": len(texts["train"] & texts["calib"]),
                            "dev&calib": len(texts["dev"] & texts["calib"])}
    assert not any(st["split_disjoint"].values()), (task, st["split_disjoint"])
    st["files"], st["sampling"] = files, info
    st["overlap_removed_total"] = {k: sum(v["eval_overlap_removed"][p][k] for v in info.values()
                                          for p in v["eval_overlap_removed"]) for k in ("exact", "normalized_only")}
    return st


def build_ext(args):
    stats = {}
    for task in TASKS:
        stats[task] = ext_task(args, task)
    ext_manifest()
    return stats


def build_rows(args):
    ex, nm, per_file = eval_keys()
    stats = {"created": CREATED, "builder": BUILDER, "eval_items": {"files": per_file, "exact_texts": len(ex),
                                                                    "normalized_texts": len(nm)}, "tasks": {}}
    for task in TASKS:
        stats["tasks"][task] = rows_task(args, task, ex, nm)
        s = stats["tasks"][task]
        print("%-4s base %-12s train %5d dev %4d calib %3d | overlap removed exact %d + normalized %d | jev rows checked %d" % (
            task, s["base"], s["files"]["train"]["decisions"], s["files"]["dev"]["decisions"], s["files"]["calib"]["decisions"],
            s["overlap_removed_total"]["exact"], s["overlap_removed_total"]["normalized_only"], s["jev_rows_reproduced"]))
    if STATS.exists():
        old = json.loads(STATS.read_text(encoding="utf-8"))
        stats["ext"] = old.get("ext")
    STATS.parent.mkdir(parents=True, exist_ok=True)
    STATS.write_text(json.dumps(stats, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("command", choices=("all", "ext", "rows", "manifest"))
    p.add_argument("--force", action="store_true", help="replace an existing output whose bytes differ")
    args = p.parse_args()
    datasets.disable_progress_bars()
    if args.command in ("all", "ext"):
        ext = build_ext(args)
        STATS.parent.mkdir(parents=True, exist_ok=True)
        old = json.loads(STATS.read_text(encoding="utf-8")) if STATS.exists() else {}
        old["ext"] = ext
        STATS.write_text(json.dumps(old, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    if args.command == "manifest":
        ext_manifest()
    if args.command in ("all", "rows"):
        build_rows(args)


if __name__ == "__main__":
    main()
