"""P0 schema check (throwaway): 05 §4 schema files vs the doc blocks and the 04 §5.8 dict.

    .venv/bin/python results/poc/P0_schema_check.py           # verify only
    .venv/bin/python results/poc/P0_schema_check.py --write   # (re)write poc/schema/*.json from the doc blocks, then verify

Verifies: (1) poc/schema/triage_v1.json and gateway_v1.json are the 05 §4.1/§4.2 code blocks byte for byte,
(2) merging their `questions` equals the 04 §5.8 dict (json equality, key order, compact serialisation),
(3) triage_v1b.json is triage_v1.json plus the 05 §4.1 true/false criteria on the three nouls and nothing else.
Then writes a one-row JSONL and prints laya.evals.questions_fingerprint of the merged 7-question dict.
"""
import json
import re
import sys
from pathlib import Path

from laya import evals

ROOT = Path(__file__).resolve().parents[2]
DOC05 = ROOT / "docs/05_poc_plan.md"
DOC04 = ROOT / "docs/04_korean_evalset_spec.md"
SCHEMA = ROOT / "poc/schema"
TMP = ROOT / "results/poc/P0_questions_fingerprint_tmp.jsonl"

# 05_poc_plan.md:239 (prose) and :242 (is_urgent JSON example). Asserted against the doc text below.
V1B_CRITERIA = {
    "refund_requested": {"true": "돈을 돌려달라고 명시적으로 요구함", "false": "환불 요구가 없음"},
    "churn_risk": {"true": "해지, 타사 이동, 거래 중단 의사나 위협이 드러남", "false": "이탈 신호가 없음"},
}


def json_blocks(path, header):
    """```json blocks inside the section that starts with `header`, as (first content line, text)."""
    lines = path.read_text(encoding="utf-8").split("\n")
    in_fence, start, level, blocks, block_start = False, None, None, [], None
    for i, line in enumerate(lines):
        if line.startswith("```"):
            if not in_fence and start is not None and line.strip() == "```json":
                block_start = i + 1
            elif in_fence and block_start is not None:
                blocks.append((block_start + 1, "\n".join(lines[block_start:i])))
                block_start = None
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#+) ", line)
        if m and start is None and line.startswith(header):
            start, level = i, len(m.group(1))
        elif m and start is not None and len(m.group(1)) <= level:
            break
    assert start is not None, "header not found: %s" % header
    return blocks, lines


def main(write):
    b41, lines05 = json_blocks(DOC05, "### 4.1 ")
    b42, _ = json_blocks(DOC05, "### 4.2 ")
    b58, lines04 = json_blocks(DOC04, "### 5.8 ")
    (l_tri, tri_text), (l_v1b, v1b_example_text) = b41
    (l_gw, gw_text), = b42
    # the full dict is the block right after the "전체 `questions` dict" bullet, not the 6 example rows
    full = [(ln, t) for ln, t in b58 if "전체 `questions` dict" in "\n".join(lines04[ln - 6:ln - 1])]
    assert len(full) == 1, full
    l_full, full_text = full[0]

    v1b_example = json.loads(v1b_example_text)
    prose = lines05[l_v1b - 4]          # the 05:239 paragraph
    for qid, crit in V1B_CRITERIA.items():
        for value in crit.values():
            assert '"%s"' % value in prose, (qid, value)
    v1b_criteria = {"is_urgent": v1b_example["is_urgent"]["criteria"], **V1B_CRITERIA}

    v1b_text = tri_text
    tri = json.loads(tri_text)
    for qid, crit in v1b_criteria.items():
        old = '      "instructions": %s\n    }' % json.dumps(tri["questions"][qid]["instructions"], ensure_ascii=False)
        assert v1b_text.count(old) == 1, qid
        new = ('      "instructions": %s,\n      "criteria": {\n        "true": %s,\n        "false": %s\n      }\n    }'
               % (json.dumps(tri["questions"][qid]["instructions"], ensure_ascii=False),
                  json.dumps(crit["true"], ensure_ascii=False), json.dumps(crit["false"], ensure_ascii=False)))
        v1b_text = v1b_text.replace(old, new)

    targets = {"triage_v1.json": tri_text, "gateway_v1.json": gw_text, "triage_v1b.json": v1b_text}
    if write:
        SCHEMA.mkdir(parents=True, exist_ok=True)
        for name, text in targets.items():
            (SCHEMA / name).write_text(text + "\n", encoding="utf-8")
            print("wrote", SCHEMA / name)

    for name, text in targets.items():
        on_disk = (SCHEMA / name).read_text(encoding="utf-8")
        assert on_disk == text + "\n", "%s differs from the doc-derived text" % name
    print("files == doc blocks: triage_v1 <- 05_poc_plan.md:%d, gateway_v1 <- 05_poc_plan.md:%d, "
          "triage_v1b <- 05:%d block + 05:%d criteria" % (l_tri, l_gw, l_tri, l_v1b))

    tri = json.load(open(SCHEMA / "triage_v1.json", encoding="utf-8"))
    gw = json.load(open(SCHEMA / "gateway_v1.json", encoding="utf-8"))
    v1b = json.load(open(SCHEMA / "triage_v1b.json", encoding="utf-8"))
    merged = {**tri["questions"], **gw["questions"]}
    ref = json.loads(full_text)
    assert tri["state_key"] == gw["state_key"] == v1b["state_key"] == "message"
    eq = merged == ref
    order = list(merged) == list(ref) and all(
        list(merged[q].get("criteria", [])) == list(ref[q].get("criteria", [])) for q in ref)
    compact = json.dumps(merged, ensure_ascii=False) == full_text.strip()
    print("merged(7) == 04_korean_evalset_spec.md:%d dict: json_equal=%s key_order_equal=%s compact_bytes_equal=%s"
          % (l_full, eq, order, compact))
    assert eq and order and compact

    expect_v1b = json.loads(json.dumps(tri))
    for qid, crit in v1b_criteria.items():
        expect_v1b["questions"][qid]["criteria"] = crit
    assert v1b == expect_v1b and list(v1b["questions"]) == list(tri["questions"])
    diff = [q for q in tri["questions"] if tri["questions"][q] != v1b["questions"][q]]
    print("triage_v1b == triage_v1 + true/false criteria on", diff)

    TMP.write_text(json.dumps({"state": {"message": "dummy"}, "questions": merged,
                               "expected": {"intent": "other"}}, ensure_ascii=False) + "\n", encoding="utf-8")
    sha = evals.questions_fingerprint(evals.Dataset.from_jsonl(str(TMP)))
    print("questions_sha256(merged triage_v1 + gateway_v1) =", sha, "(via", TMP.relative_to(ROOT), ")")


if __name__ == "__main__":
    main("--write" in sys.argv[1:])
