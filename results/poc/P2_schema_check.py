"""P2 schema check: poc/schema/router_v1.json vs its copy source and the eval set (05 §4.1, §6 P1 7번).

    .venv/bin/python results/poc/P2_schema_check.py | tee results/poc/P2_schema_check.log

(1) poc/schema/router_v1.json is byte-identical to results/C/schemas_v2/router_v1.json.
(2) state_key is "utterance" and the only question is `domain`.
(3) every row of data/evals/ko_massive_domain_8.jsonl carries the same `domain` question: same keys in the same order
    at every level (type, instructions, criteria keys, criteria descriptions) -- compared as compact JSON, which keeps
    insertion order, so one differing character or a swapped option fails.
(4) laya.evals.questions_fingerprint of the schema equals the dataset's and data/evals/MANIFEST.json's.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from laya import evals  # noqa: E402
from poc.service.hooks import fingerprint  # noqa: E402

SCHEMA = ROOT / "poc/schema/router_v1.json"
SOURCE = ROOT / "results/C/schemas_v2/router_v1.json"
DATA = ROOT / "data/evals/ko_massive_domain_8.jsonl"
MANIFEST = ROOT / "data/evals/MANIFEST.json"


def compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def main():
    raw = SCHEMA.read_bytes()
    assert raw == SOURCE.read_bytes(), "byte mismatch with %s" % SOURCE
    schema = json.loads(raw)
    assert list(schema) == ["state_key", "questions"] and schema["state_key"] == "utterance", list(schema)
    assert list(schema["questions"]) == ["domain"], list(schema["questions"])
    want = compact(schema["questions"]["domain"])
    rows = 0
    for lineno, line in enumerate(DATA.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        questions = json.loads(line)["questions"]
        assert list(questions) == ["domain"] and compact(questions["domain"]) == want, "%s:%d differs" % (DATA, lineno)
        rows += 1
    fp_schema = fingerprint(schema["questions"])
    fp_data = evals.questions_fingerprint(evals.Dataset.from_jsonl(str(DATA)))
    fp_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"][DATA.name]["questions_sha256"]
    assert fp_schema == fp_data == fp_manifest, (fp_schema, fp_data, fp_manifest)
    d = schema["questions"]["domain"]
    print("OK (1) byte-identical to %s (%d bytes)" % (SOURCE.relative_to(ROOT), len(raw)))
    print("OK (2) state_key=%s, questions=%s" % (schema["state_key"], list(schema["questions"])))
    print("OK (3) %d rows of %s: domain question identical (type=%s, instructions=%r, %d criteria in order %s)"
          % (rows, DATA.relative_to(ROOT), d["type"], d["instructions"], len(d["criteria"]), list(d["criteria"])))
    print("OK (4) questions_sha256 schema = dataset = MANIFEST = %s" % fp_schema)


if __name__ == "__main__":
    main()
