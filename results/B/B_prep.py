"""Track B prep (throwaway, no model call): dev/test split assignment and counts, ko/en and variant row
alignment asserts, dev-only copies of the ablation variants, A3 harness identity check (file level).

    source env.sh && .venv/bin/python results/B/B_prep.py > results/B/logs/B_prep.log
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from metrics_extra import read_dataset, row_splits, state_key  # noqa: E402
from laya.evals import Dataset, questions_fingerprint  # noqa: E402  (torch-free)

EV = ROOT / "data/evals"
BASE = ["ko_massive_domain_8", "en_massive_domain_8", "ko_klue_ynat_7", "ko_massive_scenario_18",
        "ko_massive_intent_20opt", "en_massive_intent_20opt", "ko_klue_nli_3", "ko_nsmc_sentiment",
        "ko_kmhas_hate", "ko_kmhas_type_8", "ko_3i4k_speechact_7"]
ABLATIONS = {"ko_massive_domain_8_ko-instr": "ko_massive_domain_8", "ko_massive_domain_8_en-desc": "ko_massive_domain_8",
             "ko_klue_ynat_7_ko-instr": "ko_klue_ynat_7", "ko_klue_ynat_7_en-desc": "ko_klue_ynat_7",
             "ko_massive_scenario_18_en-desc": "ko_massive_scenario_18"}
PAIRS = [("ko_massive_domain_8", "en_massive_domain_8"), ("ko_massive_intent_20opt", "en_massive_intent_20opt")]
RULE_TEXT = {"index parity": "index parity (even data-row index -> dev, odd -> test)",
             "state sha256 % 2": "int(sha256(json.dumps(state, ensure_ascii=False, sort_keys=True)), 16) % 2 (0 -> dev, 1 -> test)"}


def scen(row):
    return [t for t in row.get("tags", []) if t.startswith("scenario:")]


def gold(row):
    return json.dumps(row["expected"], sort_keys=True)


def main():
    out = {"splits": {}, "pairs": {}, "variants": {}, "dev_copies": {}, "a3": {}}
    data = {}
    for name in BASE + list(ABLATIONS):
        rows, header = read_dataset(EV / (name + ".jsonl"))
        # variants follow the rule of their base file (same rows, same order: asserted below)
        splits, rule = row_splits(rows, header, "auto", ABLATIONS.get(name, name) + ".jsonl")
        data[name] = (rows, header, splits, rule)
        qids = list(rows[0]["expected"])
        dist = {sp: {q: dict(sorted(Counter(str(r["expected"][q]) for r, s in zip(rows, splits) if s == sp).items()))
                     for q in qids} for sp in ("dev", "test")}
        out["splits"][name] = {"rule": rule, "rows": len(rows), "dev": splits.count("dev"), "test": splits.count("test"),
                               "label_distribution": dist}
        print("%-34s rule=%-16s rows=%d dev=%d test=%d" % (name, rule, len(rows), splits.count("dev"), splits.count("test")))
    for ko, en in PAIRS:
        a, b = data[ko][0], data[en][0]
        assert len(a) == len(b)
        bad = [i for i, (x, y) in enumerate(zip(a, b)) if gold(x) != gold(y) or scen(x) != scen(y)]
        assert not bad, (ko, en, bad[:5])
        assert data[ko][2] == data[en][2]
        out["pairs"]["%s~%s" % (ko, en)] = {"rows": len(a), "expected_and_scenario_tag_match": len(a) - len(bad),
                                            "same_state": sum(state_key(x["state"]) == state_key(y["state"]) for x, y in zip(a, b))}
        print("pair %s ~ %s: %d/%d rows match expected + scenario tag" % (ko, en, len(a) - len(bad), len(a)))
    for var, base in ABLATIONS.items():
        a, b = data[base][0], data[var][0]
        assert len(a) == len(b) and all(state_key(x["state"]) == state_key(y["state"]) and gold(x) == gold(y)
                                        for x, y in zip(a, b)), var
        assert data[base][2] == data[var][2], var
        qa, qb = (json.dumps(r[0]["questions"], ensure_ascii=False) for r in (a, b))
        out["variants"][var] = {"base": base, "rows": len(a), "same_state_and_expected_in_order": True,
                                "questions_differ": qa != qb}
        print("variant %s: same %d states + expected in order as %s; questions differ: %s" % (var, len(a), base, qa != qb))
        # dev-only copy: original header, one split line, the dev data lines byte-identical to the source
        src = EV / (var + ".jsonl")
        lines = [l for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
        head = [l for l in lines if l.strip().startswith("#")]
        body = [l for l in lines if not l.strip().startswith("#")]
        assert len(body) == len(b)
        keep = [l for l, s in zip(body, data[var][2]) if s == "dev"]
        note = "# split: dev | rule: %s | source: data/evals/%s.jsonl sha256 %s | rows %d/%d | Track B 2026-10-02 (results/B/B_prep.py)" % (
            RULE_TEXT[data[var][3]], var, hashlib.sha256(src.read_bytes()).hexdigest(), len(keep), len(body))
        dst = ROOT / "results/B/dev" / (var + ".jsonl")
        dst.write_text("\n".join(head + [note] + keep) + "\n", encoding="utf-8")
        out["dev_copies"][var] = {"path": str(dst.relative_to(ROOT)), "rows": len(keep),
                                  "sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
                                  "questions_sha256": questions_fingerprint(Dataset.from_jsonl(str(dst)))}
        print("  dev copy %s rows=%d sha256=%s" % (dst.relative_to(ROOT), len(keep), out["dev_copies"][var]["sha256"]))
    # A3 harness identity, file level: builder output vs the K2 file that reproduced upstream
    new, k2 = EV / "ko_massive_intent_20opt.jsonl", ROOT / "results/korean_support/K2_intent20_ko.jsonl"
    a, b = read_dataset(new)[0], read_dataset(k2)[0]
    field_eq = {f: sum(x.get(f) == y.get(f) for x, y in zip(a, b)) for f in ("state", "questions", "expected", "language")}
    tag_extra = Counter(t for x, y in zip(a, b) for t in set(y.get("tags", [])) - set(x.get("tags", [])))
    tag_missing = Counter(t for x, y in zip(a, b) for t in set(x.get("tags", [])) - set(y.get("tags", [])))
    qs = {str(p.relative_to(ROOT)): questions_fingerprint(Dataset.from_jsonl(str(p))) for p in (new, k2)}
    manifest = json.loads((EV / "MANIFEST.json").read_text(encoding="utf-8"))["files"]["ko_massive_intent_20opt.jsonl"]
    out["a3"] = {"rows": [len(a), len(b)], "field_equal_rows": field_eq, "tags_only_in_k2": sorted(set(tag_extra)) if
                 len(tag_extra) <= 5 else "%d distinct (id:<n>, k2_paired)" % len(tag_extra),
                 "tags_only_in_builder": dict(tag_missing), "questions_sha256": qs,
                 "manifest_questions_sha256": manifest["questions_sha256"],
                 "dataset_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (new, k2)}}
    print("A3 file identity:", json.dumps(out["a3"], ensure_ascii=False))
    (ROOT / "results/B/B_splits.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
