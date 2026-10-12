"""Build the Laya-vs-Jev comparison sets T1-T8 (docs/09_laya_vs_jev_plan.md §3), and T9/T10 (trained-Laya arm,
2026-10-08: Laya-in-training-mix tasks, no Jev run yet) into data/evals/jev_cmp/.

    source env.sh && export HF_HOME=$PWD/data/raw/hf && unset HF_HUB_OFFLINE
    .venv/bin/python scripts/build_jev_cmp_sets.py all        # every set, its playground forms, MANIFEST.json
    .venv/bin/python scripts/build_jev_cmp_sets.py manifest   # MANIFEST.json only, from the files on disk

Per set: `<name>.jsonl` (laya-evals rows behind one `# build_jev_cmp_sets {...}` header) and
`<name>_playground.json`, one form per decision with the exact text Laya reads (serialized state, instructions,
rendered option strings), so the Jev playground (<= 10 choices, state <= 8,000 chars) gets the same bytes.
Question wording and criteria are upstream's (research/scripts/bench_apps.py, build_benchmark_nb.py,
bench_local.py), so the Laya numbers stay comparable to the published ones. T1 also writes its teacher
distributions to results/F/jev_cmp/t1_gold_dists.json for soft accuracy / Brier / score MAE.
Sampling, dedup and length rules are scripts/build_ko_evalsets.py's (`pool_of`, `stratify`).
A decision the playground cannot take as Laya saw it -- a choice option longer than the choice input, a score
question without exactly the playground's 5 levels -- is marked `"jev": {qid: {"jev_excluded": true, "reason": ...}}`
on its row and with the same two keys on its form; MANIFEST counts the rest as `jev_comparable_n` (coordinator
decisions, 2026-10-06; only T1 has such decisions: customer_service/action and the 4-level score questions).
`t1_noulnocrit` is a comparison-only T1 variant: the 60 noul questions with their true/false criteria removed, the
input the playground's Boolean type (no description fields) can carry.
T9 (Enron spam) and T10 (support-ticket queue routing) never hold a text that also occurs, exactly or after
whitespace/case normalization, in that dataset's training data: T9 drops such test rows, T10 takes its items from the
test part of a stable text-hash partition of the one-split ticket dataset (`t10_part`, shared with
scripts/build_train_sets.py).
"""
import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_ko_evalsets as bk  # noqa: E402  (sets HF_HOME before datasets is imported)

import datasets  # noqa: E402
import laya  # noqa: E402
from laya.agent import Agent  # noqa: E402
from laya.common import render_options, serialize_state  # noqa: E402
from laya.evals import Dataset, questions_fingerprint  # noqa: E402

BUILDER = "scripts/build_jev_cmp_sets.py 0.1.0"
CREATED = "2026-10-06"  # a constant: a rebuild must stay byte-identical
HEADER = "# build_jev_cmp_sets "
SEED, N = 13, 40
MAX_OPTIONS = 10            # playground "8 of 10" choice counter (results/F/jev_raw/p1_01.snapshot.yml:83)
MAX_STATE_CHARS = 8000      # playground State counter "14 / 8,000" (results/F/jev_raw/p1_01.snapshot.yml:60)
CHOICE_INPUT_CHARS = 80     # playground choice input maxlength (results/F/jev_playground_manual_20261006.md:34)
SCORE_LEVELS = 5            # playground Score takes 5 levels only (coordinator, 2026-10-06 S1 check)
JEV_EXCLUSION_RULE = ("score 레벨 수 ≠ %d 제외, 옵션 > %d자 제외 (playground Score는 %d레벨만, choice 입력 maxlength %d; "
                      "coordinator 결정 2026-10-06)" % (SCORE_LEVELS, CHOICE_INPUT_CHARS, SCORE_LEVELS, CHOICE_INPUT_CHARS))
OUT = ROOT / "data/evals/jev_cmp"
GOLD_DISTS = ROOT / "results/F/jev_cmp/t1_gold_dists.json"

# HfApi().dataset_info(repo).sha on 2026-10-06, pinned so a rebuild reads the same bytes.
SRC = {
    "T1": {"dataset": "LocalLLaMA/typed-decisions", "config": "all", "split": "test",
           "revision": "d0e2f0c42fef86cc15d1688d25a19f5ba7c85b18"},
    "T2": {"dataset": "fancyzhx/ag_news", "config": None, "split": "test",
           "revision": "eb185aade064a813bc0b7f42de02595523103ca4"},
    "T3": {"dataset": "dair-ai/emotion", "config": "split", "split": "test",
           "revision": "cab853a1dbdf4c42c2b3ef2173804746df8825fe"},
    "T4": {"dataset": "mteb/banking77", "config": None, "split": "test",
           "revision": "18072d2685ea682290f7b8924d94c62acc19c0b2"},
    "T5": {"dataset": "google/boolq", "config": None, "split": "validation",  # the repo ships no test split
           "revision": "35b264d03638db9f4ce671b711558bf7ff0f80d5"},
    "T6": {"dataset": "SetFit/sst5", "config": None, "split": "test",
           "revision": "e51bdcd8cd3a30da231967c1a249ba59361279a3"},
    "T7": {**bk.MASSIVE, "config": ["en", "de", "ja", "zh-CN", "ko"]},
    "T8": {"dataset": "deepset/prompt-injections", "config": None, "split": "test",
           "revision": "4f61ecb038e9c3fb77e21034b22511b523772cdd"},
    # 2026-10-08 (HfApi().dataset_info(repo).sha that day)
    "T9": {"dataset": "SetFit/enron_spam", "config": None, "split": "test",
           "revision": "1916f66c89d52221ae33eb57d44498b4f3a5df22"},
    "T10": {"dataset": "Tobi-Bueck/customer-support-tickets", "config": None, "split": "train",  # its only split
            "revision": "ddf1c81a5475992c4fa6752bf1e8b4e31f07bbeb"},
}
LICENSE = {
    "T1": "apache-2.0 (HF card license field) (확인 필요)",
    "T2": "unknown (HF card license field) (확인 필요)",
    "T3": "other (HF card license field; research/educational use) (확인 필요)",
    "T4": "mit (HF card license field of the mteb mirror; PolyAI original CC BY 4.0) (확인 필요)",
    "T5": "cc-by-sa-3.0 (HF card license field) (확인 필요)",
    "T6": "HF card has no license field (확인 필요)",
    "T7": bk.LICENSE["massive"],
    "T8": "apache-2.0 (HF card license field) (확인 필요)",
    "T9": "HF card has no metadata block / license field (확인 필요)",
    "T10": "cc-by-nc-4.0 (HF card license field) (확인 필요)",
}
# (in_training_mix, evidence). Upstream says it in README.md "English tasks" and the notebook's
# training_overlap caveat; BENCHMARKS.md's Themes table lists none of these sources.
TRAINING = {
    "T1": ("no", "english/multilingual: 'Neither checkpoint trained on typed-decisions' (research/scripts/"
                 "build_benchmark_nb.py:762). laya-typed-decisions is fine-tuned on this benchmark's train split "
                 "(BENCHMARKS.md:332), so its line is not zero-shot"),
    "T2": ("yes", "README.md:1352 'in training mix'; build_benchmark_nb.py:760; bench_apps.py:94 in_training=True"),
    "T3": ("no", "README.md:1354 'held out'; build_benchmark_nb.py:761; bench_apps.py:110 in_training=False"),
    "T4": ("held out (upstream build_benchmark_nb.py:760-762)",
           "build_benchmark_nb.py:761 'sst5, emotion, prompt_injections, banking77 were held out'; bench_apps.py:126 "
           "in_training=False. Was 'unknown' until 2026-10-07; the frozen jsonl headers keep that build-time value"),
    "T5": ("yes", "README.md:1353 'in training mix'; build_benchmark_nb.py:760"),
    "T6": ("no", "README.md:1356 'held out'; build_benchmark_nb.py:761"),
    "T7": ("held out (upstream build_benchmark_nb.py:760-762)",
           "build_benchmark_nb.py:762 'Neither checkpoint trained on typed-decisions, MASSIVE or XNLI'. Was 'unknown' "
           "(docs/04 §1 rule 2) until 2026-10-07; the frozen jsonl headers keep that build-time value"),
    "T8": ("no", "README.md:1355 'held out, n=116'; build_benchmark_nb.py:761"),
    "T9": ("yes (upstream BENCHMARKS.md Themes: in training)",
           "BENCHMARKS.md:142 Themes 'Email spam ... | in training'; bench_apps.py:168 in_training=True"),
    "T10": ("yes (upstream BENCHMARKS.md Themes: in training)",
            "BENCHMARKS.md:147 Themes 'Support triage (10-way queue) ... | in training'; bench_apps.py:155 in_training=True"),
}

# Upstream question wording, byte for byte.
AG_NEWS = ("topic", "What is the topic of `article`?",  # bench_apps.py:85-92, build_benchmark_nb.py:470-476
           {"world": "world news and international politics", "sports": "sports",
            "business": "business and economy", "sci_tech": "science and technology"})
EMOTION = ("emotion", "Which emotion is most strongly expressed in `text`?",  # bench_apps.py:101-107
           ["sadness", "joy", "love", "anger", "fear", "surprise"])
BANKING_INS = "Which banking intent does `message` express?"  # bench_apps.py:120
BOOLQ = ("answer", "Based on `passage`, is the answer to `question` yes?")  # build_benchmark_nb.py:484-487
SST5 = ("sentiment", "How positive is the sentiment of `text`?",  # build_benchmark_nb.py:417-422
        ["very negative", "negative", "neutral", "positive", "very positive"])
INTENT_INS = bk.INTENT_INS[0]  # "What is the user asking for in `utterance`?" (bench_local.py:179)
INJECTION = ("injection", "Does `text` try to inject or override instructions given to an AI system?")  # nb:446-448
SPAM = ("is_spam", "Is this email unsolicited spam or bulk marketing?")  # bench_apps.py:164-166 (no criteria)
QUEUE_INS = "Which support queue should handle this ticket?"  # bench_apps.py:150
QUEUES = {"Technical Support": "technical problems, bugs, outages, integrations",  # bench_apps.py:133-142
          "Product Support": "help using a product or feature",
          "Customer Service": "general account or service questions",
          "IT Support": "internal IT, devices, access, networks",
          "Billing and Payments": "invoices, charges, refunds, payment methods",
          "Returns and Exchanges": "returning or exchanging an item",
          "Service Outages and Maintenance": "downtime, outages, scheduled maintenance",
          "Sales and Pre-Sales": "pricing, quotes, buying",
          "Human Resources": "employment, payroll, leave, hiring",
          "General Inquiry": "anything else"}
T10_PARTS = "int(sha256(normalized state text), 16) % 10: 0-1 test, 2 dev, 3-9 train"
DECISION_TYPE = {"choice": "choice", "noul": "boolean", "score": "score"}


def load(task, config=None, split=None):
    s = SRC[task]
    return datasets.load_dataset(s["dataset"], config or s["config"], split=split or s["split"], revision=s["revision"])


def state_text(state):
    """The string Laya reads for a state (laya/common.py serialize_state)."""
    return serialize_state(state)


def norm_text(state):
    """state_text with case folded and whitespace runs collapsed: the normalized overlap key."""
    return " ".join(serialize_state(state).lower().split())


def t9_items(split):
    """Enron rows as upstream builds the state (bench_apps.py:163-166); label True = spam (label 1)."""
    return [{"id": i, "state": laya.email_state(r.get("subject") or "", (r.get("message") or "")[:3000]),
             "label": int(r["label"]) == 1, "tags": ["enron_spam", "id:%d" % i]} for i, r in enumerate(load("T9", split=split))]


def t10_part(state):
    """Stable train/dev/test part of a ticket by its normalized text, so equal texts always share a part."""
    h = int(hashlib.sha256(norm_text(state).encode("utf-8")).hexdigest(), 16) % 10
    return "test" if h < 2 else "dev" if h < 3 else "train"


def t10_items():
    """English tickets of the 10 upstream queues, state as bench_apps.py:146-148, with their hash part."""
    out = []
    for i, r in enumerate(load("T10")):
        if r.get("language") != "en" or r.get("queue") not in QUEUES or not r.get("body"):
            continue
        state = {"subject": r["subject"] or "", "body": r["body"].replace("\\n", "\n")[:3000]}
        out.append({"id": i, "state": state, "label": r["queue"], "part": t10_part(state),
                    "tags": ["support_tickets", "id:%d" % i]})
    return out


def source(task):
    s = SRC[task]
    return {"dataset": s["dataset"], "config": s["config"], "split": s["split"], "revision": s["revision"]}


def row(state, questions, expected, tags, lang):
    r = {"state": state, "questions": questions, "expected": expected, "tags": tags}
    if lang:  # T8 mixes English and German with no language column, so its rows carry none
        r["language"] = lang
    return r


def expected_ok(q, exp):
    if q["type"] == "choice":
        return exp in q["criteria"]
    if q["type"] == "score":
        return type(exp) is int and 0 <= exp < len(q["criteria"])
    return isinstance(exp, bool)


def write_set(args, name, rows, meta):
    """bk.write_set with score labels allowed (bk asserts a bool for every non-choice question,
    build_ko_evalsets.py:242) and the playground limits checked; validate, then replace only with --force."""
    for r in rows:
        assert len(serialize_state(r["state"])) <= MAX_STATE_CHARS, (name, r["tags"])
        for qid, exp in r["expected"].items():
            q = r["questions"][qid]
            assert expected_ok(q, exp), (name, qid, exp)
            assert len(q.get("criteria") or ()) <= MAX_OPTIONS, (name, qid)
    assert bk.count_duplicates(rows) == 0, name
    for r in rows:
        for qid, q in r["questions"].items():
            reason = jev_exclusion(q)
            if reason:
                r.setdefault("jev", {})[qid] = {"jev_excluded": True, "reason": reason}
    if any("jev" in r for r in rows):
        meta = {**meta, "jev_exclusion_rule": JEV_EXCLUSION_RULE}
    header = HEADER + json.dumps({"builder": BUILDER, "created": CREATED, **meta}, ensure_ascii=False)
    data = ("\n".join([header] + [json.dumps(r, ensure_ascii=False) for r in rows]) + "\n").encode("utf-8")
    path = OUT / (name + ".jsonl")
    write_bytes(args, path, data, validate=True)
    playground(args, name, rows, bk.sha256(data))


def jev_exclusion(q):
    """Why the playground cannot take this question as Laya saw it, or None."""
    if q["type"] == "choice" and any(len(o) > CHOICE_INPUT_CHARS for o in render_options(Agent._to_internal(q))):
        return "option > %d chars" % CHOICE_INPUT_CHARS
    if q["type"] == "score" and len(q["criteria"]) != SCORE_LEVELS:
        return "score levels != %d" % SCORE_LEVELS
    return None


def write_bytes(args, path, data, validate=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    if validate:
        check = subprocess.run([str(bk.LAYA_EVALS), "validate", str(tmp)], capture_output=True, text=True)
        if check.returncode:
            tmp.unlink()
            sys.exit("%s: laya-evals validate failed\n%s%s" % (path.name, check.stdout, check.stderr))
    old, new = (bk.sha256(path.read_bytes()) if path.exists() else None), bk.sha256(data)
    if old not in (None, new) and not args.force:
        tmp.unlink()
        sys.exit("%s exists with sha256 %s but this build gives %s; a frozen file changes only with --force"
                 % (bk.rel(path), old, new))
    os.replace(tmp, path)
    print("%-44s sha256=%s %s" % (path.name, new[:12], "unchanged" if old == new else "replaced" if old else "written"))


def playground(args, name, rows, dataset_sha256):
    """One form per decision: the strings Laya's head and state are built from (laya/common.py render_options,
    serialize_state), typed verbatim into the playground. Options of a noul/score question are listed for the
    record; the playground's Boolean/Score inputs may not take them."""
    items = []
    for i, r in enumerate(rows):
        sid = next(t[3:] for t in r["tags"] if t.startswith("id:"))
        for qid, q in r["questions"].items():
            opts = render_options(Agent._to_internal(q))
            exp = r["expected"][qid]
            item = {"id": "%s/%s/%s" % (name, sid, qid), "row": i, "qid": qid, "state_text": serialize_state(r["state"]),
                    "question": q["instructions"], "decision_type": DECISION_TYPE[q["type"]], "options": opts,
                    "gold": exp}
            if q["type"] == "choice":
                item["gold_option"] = opts[list(q["criteria"]).index(exp)]
                long = [o for o in opts if len(o) > CHOICE_INPUT_CHARS]
                if long:
                    item["options_over_choice_input_chars"] = long
            item.update(r.get("jev", {}).get(qid, {}))
            items.append(item)
    doc = {"set": name + ".jsonl", "dataset_sha256": dataset_sha256,
           "questions_sha256": questions_fingerprint(Dataset.from_jsonl(str(OUT / (name + ".jsonl")))),
           "limits": {"options": MAX_OPTIONS, "state_chars": MAX_STATE_CHARS, "choice_input_chars": CHOICE_INPUT_CHARS},
           "items": items}
    write_bytes(args, OUT / (name + "_playground.json"), (json.dumps(doc, ensure_ascii=False, indent=1) + "\n").encode())


def meta_of(task, name, build_args, pool=None, **extra):
    m = {"set": name, "task": task, "source": source(task), "license": LICENSE[task],
         "in_training_mix": TRAINING[task][0], "in_training_mix_evidence": TRAINING[task][1],
         "build_args": {"seed": SEED, **build_args}}
    if pool is not None:
        m["pool"] = pool
    return {**m, **extra}


def single(args, task, name, items, labels, qid, q, lang="en", question_source=None, build_args=None):
    """bk.pool_of + bk.stratify over one-question items, then write."""
    pool, info = bk.pool_of(items)
    picked, info["sample"] = bk.stratify(pool, labels, N, SEED)
    rows = [row(it["state"], {qid: q}, {qid: it["label"]}, it["tags"], lang) for it in picked]
    write_set(args, name, rows, meta_of(task, name, {"n": N, **(build_args or {})}, info,
                                        question_source=question_source))


# ---------------------------------------------------------------- sets
def t1(args):
    """40 cases, 10 per workflow, every question of a case kept; expected = argmax of the teacher distribution."""
    d = load("T1")
    cases, excluded = [], []
    for r in d:
        qs, gold, state = json.loads(r["questions"]), json.loads(r["gold"]), r["state"]
        try:  # upstream: research/scripts/bench_local.py:232-236
            state = json.loads(state)
        except ValueError:
            pass
        wide = [qid for qid, q in qs.items() if len(q.get("criteria") or ()) > MAX_OPTIONS]
        if wide:  # no case of the 2026-10-06 revision has one (max 5 options); kept for a future revision
            excluded.append({"id": r["id"], "questions": wide})
            continue
        cases.append({"id": r["id"], "label": r["workflow"], "state": state, "questions": qs, "gold": gold})
    cases.sort(key=lambda c: c["id"])  # stratify draws from each group in pool order; bk.pool_of hands it id order
    assert len({json.dumps(c["state"], sort_keys=True) for c in cases}) == len(cases)  # no duplicate state to drop
    workflows = sorted({c["label"] for c in cases})
    picked, sample = bk.stratify(cases, workflows, N, SEED)
    rows, dists = [], []
    for i, c in enumerate(picked):
        expected = {}
        for qid, q in c["questions"].items():
            g = c["gold"][qid]
            probs = g.get("probabilities", {})
            if q["type"] == "choice":
                opts = list(q["criteria"])
                soft = [float(probs.get(k, 0.0)) for k in opts]
                arg = max(range(len(opts)), key=soft.__getitem__)  # first maximum, as np.argmax
                exp, label_idx = opts[arg], opts.index(str(g["label"]))
            elif q["type"] == "score":
                opts = [str(k) for k in range(len(q["criteria"]))]
                soft = [float(probs.get(k, 0.0)) for k in opts]
                arg = max(range(len(opts)), key=soft.__getitem__)
                exp, label_idx = arg, int(g["label"])
            else:
                opts = ["false", "true"]
                pt = float(probs.get("true", g.get("noul", 0.5)))  # bench_local.py:245
                soft, arg = [1 - pt, pt], int(pt >= 0.5)
                exp, label_idx = pt >= 0.5, int(str(g["label"]).lower() == "true")
            expected[qid] = exp
            rec = {"row": i, "case_id": c["id"], "workflow": c["label"], "qid": qid, "type": q["type"],
                   "options": opts, "soft": soft, "expected": exp, "argmax_idx": arg,
                   "label_upstream": str(g["label"]), "label_idx": label_idx, "label_ne_argmax": label_idx != arg,
                   "tie": sorted(soft)[-1] == sorted(soft)[-2]}
            if q["type"] == "score":
                rec["gold_score"] = float(g.get("score", float(g["label"])))  # bench_local.py:251
            dists.append(rec)
        rows.append(row(c["state"], c["questions"], expected, ["typed_decisions", "workflow:" + c["label"], "id:" + c["id"]],
                        "en"))
    name = "T1_typed_decisions_40"
    pool = {"source_rows": len(d), "excluded_over_%d_options" % MAX_OPTIONS: excluded, "sample": sample}
    write_set(args, name, rows, meta_of("T1", name, {"n_cases": N, "stratify_by": "workflow",
                                                     "expected": "choice/score: argmax of the teacher distribution "
                                                                 "(first maximum); noul: p(true) >= 0.5"}, pool,
                                        question_source="dataset's own questions (research/scripts/bench_local.py:225-253)"))
    doc = {"set": "data/evals/jev_cmp/%s.jsonl" % name, "source": source("T1"),
           "note": "soft = teacher distribution in option order (choice: criteria order, score: level order, "
                   "noul: [false, true]); label_upstream/label_idx = the dataset's `label`, which upstream scores "
                   "against (bench_local.py:242-251); argmax_idx/expected = what the laya-evals file expects",
           "label_ne_argmax": sum(x["label_ne_argmax"] for x in dists), "ties": sum(x["tie"] for x in dists),
           "decisions": dists}
    write_bytes(args, GOLD_DISTS, (json.dumps(doc, ensure_ascii=False, indent=1) + "\n").encode())


def t1_noulnocrit(args):
    """Comparison only: T1's noul questions (all 60) with `criteria` removed, everything else as in the T1 file."""
    src = OUT / "T1_typed_decisions_40.jsonl"
    meta = read_header(src)
    rows = []
    for r in bk.read_rows(src):
        qs = {qid: {k: v for k, v in q.items() if k != "criteria"} for qid, q in r["questions"].items() if q["type"] == "noul"}
        rows.append(row(r["state"], qs, {qid: r["expected"][qid] for qid in qs}, r["tags"], r.get("language")))
    name = "T1_typed_decisions_40_noulnocrit"
    write_set(args, name, rows, {**{k: meta[k] for k in ("task", "source", "license", "in_training_mix",
                                                          "in_training_mix_evidence")},
                                 "set": name, "comparison_only": True,
                                 "derived_from": {"path": bk.rel(src), "sha256": bk.sha256(src.read_bytes())},
                                 "variant": "the 60 noul questions only, `criteria` (true/false descriptions) removed; "
                                            "20 of them (duplicate, credential_compromise) had none already",
                                 "build_args": {"command": "t1_noulnocrit"}})


def t2(args):
    d = load("T2")
    assert d.features["label"].names == ["World", "Sports", "Business", "Sci/Tech"], d.features["label"]
    qid, ins, crit = AG_NEWS
    keys = list(crit)  # upstream maps label index i to keys[i] (bench_apps.py:93)
    items = [{"id": i, "state": {"article": r["text"]}, "label": keys[r["label"]], "tags": ["ag_news", "id:%d" % i]}
             for i, r in enumerate(d)]
    single(args, "T2", "T2_ag_news_40", items, keys, qid, {"type": "choice", "instructions": ins, "criteria": dict(crit)},
           question_source="research/scripts/bench_apps.py:85-92")


def t3(args):
    d = load("T3")
    qid, ins, names = EMOTION
    assert d.features["label"].names == names, d.features["label"]
    items = [{"id": i, "state": {"text": r["text"]}, "label": names[r["label"]], "tags": ["emotion", "id:%d" % i]}
             for i, r in enumerate(d)]
    single(args, "T3", "T3_emotion_40", items, names, qid,
           {"type": "choice", "instructions": ins, "criteria": {n: None for n in names}},
           question_source="research/scripts/bench_apps.py:101-107 (criteria values None: options are the bare keys)")


def t4(args):
    d = load("T4")
    labels = sorted(set(d["label_text"]))
    items = [{"id": i, "state": {"message": r["text"]}, "label": r["label_text"], "tags": ["banking77", "id:%d" % i]}
             for i, r in enumerate(d)]
    pool, info = bk.pool_of(items)
    # n=40 < 77 labels: stratify gives one row to each of the first 40 labels, so their order is seeded, not alphabetical
    order = list(labels)
    random.Random(SEED).shuffle(order)
    picked, info["sample"] = bk.stratify(pool, order, N, SEED)
    rng = random.Random(SEED)  # one distractor stream over the rows in id order, as bench_local.py:171-176 per language
    assert len({k.replace("_", " ") for k in labels}) == len(labels)
    rows = []
    for it in picked:
        keys = [it["label"]] + rng.sample([k for k in labels if k != it["label"]], MAX_OPTIONS - 1)
        rng.shuffle(keys)
        # upstream's key-only rendering (bench_apps.py:120-122, build_benchmark_nb.py:460): the spaced label is the
        # option key and its whole text (<= 48 chars); v0's `key: key spaced` reached 98 chars
        q = {"type": "choice", "instructions": BANKING_INS, "criteria": {k.replace("_", " "): None for k in keys}}
        rows.append(row(it["state"], {"intent": q}, {"intent": it["label"].replace("_", " ")}, it["tags"], "en"))
    name = "T4_banking77_10opt_40"
    write_set(args, name, rows, meta_of("T4", name, {"n": N, "labels": len(labels), "options": MAX_OPTIONS,
                                                     "label_order": "random.Random(13).shuffle(sorted labels)",
                                                     "distractors": "random.Random(13), one stream in row order: "
                                                                    "sample 9 of the other labels, shuffle"}, info,
                                        question_source="research/scripts/bench_apps.py:116-122 (instructions and "
                                                        "key-only option rendering)",
                                        options_rendering="key-only",
                                        rebuild_reason="v0 rendered each option as `key: key spaced`; "
                                                       "balance_not_updated_after_cheque_or_cash_deposit became 98 chars "
                                                       "and 8 of 40 items could not be typed into the playground's 80-char "
                                                       "choice input. Coordinator decision (b) 2026-10-06: upstream key-only "
                                                       "rendering k.replace('_', ' '), max 48 chars. Same rows, options and "
                                                       "option order as v0; only the option text and expected key changed",
                                        previous_version={"path": "data/evals/jev_cmp/T4_banking77_10opt_40_v0.jsonl",
                                                          "sha256": "df700caa098332eaaf6bd6fc4c0609413db85656fc96dd13bb5f43fda804786c"}))


def t5(args):
    d = load("T5")
    qid, ins = BOOLQ
    items = [{"id": i, "state": {"passage": r["passage"], "question": r["question"]}, "label": bool(r["answer"]),
              "tags": ["boolq", "id:%d" % i]} for i, r in enumerate(d)]
    single(args, "T5", "T5_boolq_40", items, [True, False], qid, {"type": "noul", "instructions": ins},
           question_source="research/scripts/build_benchmark_nb.py:484-487 (no criteria)")


def t6(args):
    d = load("T6")
    qid, ins, levels = SST5
    assert all(levels[r["label"]] == r["label_text"] for r in d)
    items = [{"id": i, "state": {"text": r["text"]}, "label": int(r["label"]), "tags": ["sst5", "id:%d" % i]}
             for i, r in enumerate(d)]
    single(args, "T6", "T6_sst5_40", items, list(range(len(levels))), qid,
           {"type": "score", "instructions": ins, "criteria": list(levels)},
           question_source="research/scripts/build_benchmark_nb.py:417-422")


def t7(args):
    """The first 20 test ids present in all five configs, one 10-option question per id shared by every language."""
    langs = SRC["T7"]["config"]
    data, labels = {}, None
    for lang in langs:
        d = load("T7", lang)
        data[lang] = {int(r["id"]): r for r in d}
        got = sorted(set(d["label_text"]))
        assert labels in (None, got), lang
        labels = got
    ids = sorted(set.intersection(*(set(v) for v in data.values())))[:20]
    for i in ids:
        assert len({data[lang][i]["label_text"] for lang in langs}) == 1, i  # parallel corpus: same intent per id
    rng = random.Random(SEED)  # once, over the ids: every language gets the same options for an id
    crit = {}
    for i in ids:
        gold = data["en"][i]["label_text"]
        keys = [gold] + rng.sample([k for k in labels if k != gold], MAX_OPTIONS - 1)
        rng.shuffle(keys)
        crit[i] = {k: bk.render_key(k) for k in keys}  # bench_local.py:180
    for lang in langs:
        rows = [row({"utterance": data[lang][i]["text"]},
                    {"intent": {"type": "choice", "instructions": INTENT_INS, "criteria": crit[i]}},
                    {"intent": data[lang][i]["label_text"]},
                    ["massive", "intent10", "scenario:" + bk.scenario_of(data[lang][i]["label_text"]), "id:%d" % i], lang)
                for i in ids]
        name = "T7_massive_intent_10opt_%s_20" % lang
        write_set(args, name, rows, meta_of("T7", name, {"n": len(ids), "options": MAX_OPTIONS, "labels": len(labels),
                                                         "ids": ids, "distractors": "random.Random(13), one stream over "
                                                         "the ids: sample 9 of the other labels, shuffle"},
                                            {"selection": "first 20 test ids present in en, de, ja, zh-CN, ko"},
                                            source={**source("T7"), "config": lang},
                                            question_source="research/scripts/bench_local.py:173-180 (9 distractors, not 19)"))


def t8(args):
    d = load("T8")
    qid, ins = INJECTION
    items = [{"id": i, "state": {"text": r["text"]}, "label": r["label"] == 1, "tags": ["prompt_injections", "id:%d" % i]}
             for i, r in enumerate(d)]
    single(args, "T8", "T8_prompt_injections_40", items, [True, False], qid, {"type": "noul", "instructions": ins},
           lang=None, question_source="research/scripts/build_benchmark_nb.py:446-448 (no criteria)")


def t9(args):
    """40 test emails (20 spam / 20 ham) whose text is not in the train split, exact or normalized."""
    qid, ins = SPAM
    train = {norm_text(it["state"]) for it in t9_items("train")}
    pool, info = bk.pool_of(t9_items("test"))
    keep = [it for it in pool if norm_text(it["state"]) not in train]
    info["train_overlap_excluded"] = len(pool) - len(keep)
    picked, info["sample"] = bk.stratify(keep, [True, False], N, SEED)
    rows = [row(it["state"], {qid: {"type": "noul", "instructions": ins}}, {qid: it["label"]}, it["tags"], "en")
            for it in picked]
    name = "T9_enron_spam_40"
    write_set(args, name, rows, meta_of("T9", name, {"n": N}, info,
                                        question_source="research/scripts/bench_apps.py:163-166 (state laya.email_state("
                                                        "subject, message[:3000]); no criteria)",
                                        train_overlap_rule="test rows whose normalized state text equals a train row's "
                                                           "are excluded before sampling"))


def t10(args):
    """40 tickets (4 per queue) from the test part of the hash partition of the English tickets."""
    pool, info = bk.pool_of([it for it in t10_items() if it["part"] == "test"])
    picked, info["sample"] = bk.stratify(pool, list(QUEUES), N, SEED)
    q = {"type": "choice", "instructions": QUEUE_INS, "criteria": dict(QUEUES)}
    rows = [row(it["state"], {"queue": q}, {"queue": it["label"]}, it["tags"], "en") for it in picked]
    name = "T10_support_tickets_queue_40"
    write_set(args, name, rows, meta_of("T10", name, {"n": N, "partition": T10_PARTS}, info,
                                        question_source="research/scripts/bench_apps.py:130-152 (language en, the 10 "
                                                        "queues, state subject + body[:3000])",
                                        partition={"rule": T10_PARTS, "part": "test",
                                                   "why": "the dataset ships one split; parts are disjoint by text"}))


# ---------------------------------------------------------------- manifest
def read_header(path):
    with open(path, encoding="utf-8") as f:
        first = f.readline()
    return json.loads(first[len(HEADER):]) if first.startswith(HEADER) else {}


def manifest(args):
    files = {}
    for path in sorted(OUT.glob("*.jsonl")):
        meta, rows = read_header(path), bk.read_rows(path)
        dist = {}
        for r in rows:
            for qid, exp in r["expected"].items():
                dist.setdefault(qid, Counter())[exp if isinstance(exp, str) else json.dumps(exp)] += 1
        dist = {qid: dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))) for qid, c in dist.items()}
        majority = {qid: round(max(c.values()) / sum(c.values()), 4) for qid, c in dist.items()}
        one = len(dist) == 1
        pg_path = path.with_name(path.stem + "_playground.json")
        pg = json.loads(pg_path.read_text(encoding="utf-8"))
        qs = [q for r in rows for q in r["questions"].values()]
        # the rule itself, so the archived T4 v0 (built before the marks existed) is counted the same way
        excluded = [it["id"] for it in pg["items"] if it.get("jev_excluded") or "options_over_choice_input_chars" in it]
        extra = {k: meta[k] for k in ("options_rendering", "rebuild_reason", "previous_version", "jev_exclusion_rule",
                                      "comparison_only", "derived_from", "variant") if k in meta}
        if path.stem.endswith("_v0"):
            extra.update(status="superseded", superseded_by=path.stem[:-3] + ".jsonl")
        files[path.name] = {
            "path": bk.rel(path), "sha256": bk.sha256(path.read_bytes()),
            "questions_sha256": questions_fingerprint(Dataset.from_jsonl(str(path))), "n": len(rows),
            "decisions": sum(len(r["expected"]) for r in rows), "task": meta.get("task"), "source": meta.get("source"),
            # TRAINING, not the header: the label is a claim about upstream's training data, and relabelling it
            # must not change a frozen file's bytes
            "license": meta.get("license"), "in_training_mix": TRAINING[meta["task"]][0],
            "in_training_mix_evidence": TRAINING[meta["task"]][1],
            "question_source": meta.get("question_source"), "build_args": meta.get("build_args"),
            "pool": meta.get("pool"),
            "label_distribution": next(iter(dist.values())) if one else dist,
            "majority_rate": next(iter(majority.values())) if one else majority,
            "duplicates": bk.count_duplicates(rows),
            "limits": {"options_max": max(len(q.get("criteria") or ("false", "true")) for q in qs),
                       "state_chars_max": max(len(serialize_state(r["state"])) for r in rows),
                       "choice_items_with_option_over_%d_chars" % CHOICE_INPUT_CHARS:
                           sum("options_over_choice_input_chars" in it for it in pg["items"])},
            "playground": {"path": bk.rel(pg_path), "sha256": bk.sha256(pg_path.read_bytes()), "items": len(pg["items"]),
                           "dataset_sha256_matches": pg["dataset_sha256"] == bk.sha256(path.read_bytes())},
            "jev_comparable_n": len(pg["items"]) - len(excluded),
            "jev_excluded": excluded,
            **extra,
        }
    doc = {"version": 1, "builder": BUILDER, "laya_version": laya.__version__,
           "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
           "limits": {"options": MAX_OPTIONS, "state_chars": MAX_STATE_CHARS, "choice_input_chars": CHOICE_INPUT_CHARS},
           "files": files}
    (OUT / "MANIFEST.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("MANIFEST.json: %d files" % len(files))


def build_all(args):
    for build in (t1, t1_noulnocrit, t2, t3, t4, t5, t6, t7, t8, t9, t10, manifest):
        build(args)


COMMANDS = {"all": build_all, "manifest": manifest, "t1": t1, "t1_noulnocrit": t1_noulnocrit, "t2": t2, "t3": t3, "t4": t4, "t5": t5, "t6": t6,
            "t7": t7, "t8": t8, "t9": t9, "t10": t10}


def main():
    p = argparse.ArgumentParser(description="Build the Laya-vs-Jev comparison sets (docs/09_laya_vs_jev_plan.md).")
    p.add_argument("command", choices=list(COMMANDS))
    p.add_argument("--force", action="store_true", help="replace an existing output whose bytes differ")
    args = p.parse_args()
    datasets.disable_progress_bars()
    COMMANDS[args.command](args)


if __name__ == "__main__":
    main()
