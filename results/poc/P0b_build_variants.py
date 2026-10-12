"""P0b zero-shot schema ablation (throwaway): build the variant schemas and derived JSONLs.

    .venv/bin/python results/poc/P0b_build_variants.py --write-gateway-v1b   # once: poc/schema/gateway_v1b.json
    .venv/bin/python results/poc/P0b_build_variants.py > results/poc/P0b_build.log

Every derived row reuses the 30 states, expected values, tags and language of
results/poc/P0_probe_sentences.jsonl. Only `questions` changes, plus the explicit remaps the task
allows (V3a/V3b: binary expected -> choice key; V5: intent -> 4 classes) and V7's plain-string state.
Writes results/poc/schemas_ablation/<name>.json and results/poc/P0b_<name>.jsonl.
"""
import copy
import json
import re
import sys
from pathlib import Path

from laya import evals
from laya.agent import Agent
from laya.common import render_options

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "results/poc/P0_probe_sentences.jsonl"
SCHEMA = ROOT / "poc/schema"
OUT_SCHEMA = ROOT / "results/poc/schemas_ablation"
OUT_JSONL = ROOT / "results/poc"
DOC05 = ROOT / "docs/05_poc_plan.md"

NOULS = ["is_urgent", "refund_requested", "churn_risk", "needs_llm"]

# V3a/V3b descriptions. is_urgent is the task's literal example text, which omits "서비스 중단" from
# triage_v1b (05:242); the other three are the triage_v1b / gateway_v1b criteria verbatim.
BINARY_DESC = {
    "is_urgent": ("기한, 마감, 즉시 처리 요구 등 시간 압박이 있음", "시간 압박이 없음"),
    "refund_requested": ("돈을 돌려달라고 명시적으로 요구함", "환불 요구가 없음"),
    "churn_risk": ("해지, 타사 이동, 거래 중단 의사나 위협이 드러남", "이탈 신호가 없음"),
    "needs_llm": ("개별 상황 설명, 설득, 복합 질의처럼 생성형 답변이 필요함",
                  "정형 액션(큐 배정, 템플릿 답변, 상태 조회)으로 처리 가능함"),
}
SEMANTIC_KEYS = {
    "is_urgent": ("urgent", "not_urgent"),
    "refund_requested": ("refund_requested", "no_refund_request"),
    "churn_risk": ("churn_risk", "no_churn_risk"),
    "needs_llm": ("needs_llm", "templated_ok"),
}
KO_INSTRUCTIONS = {
    "intent": "`message`에서 고객이 원하는 것은 무엇인가요?",
    "is_urgent": "`message`에 시간 압박이나 기한이 드러나 있나요?",
    "frustration": "`message`에서 고객이 얼마나 짜증 난 것으로 느껴지나요?",
    "refund_requested": "고객이 돈을 돌려달라고 요청하나요?",
    "churn_risk": "`message`에 고객이 경쟁사로 옮기거나 해지할 수 있다는 신호가 있나요?",
    "needs_llm": "`message`에 답하려면 템플릿 액션이 아니라 자유 형식으로 생성한 답변이 필요한가요?",
    "complexity": "`message`의 요청은 얼마나 복잡한가요?",
}
INTENT4 = {
    "billing": "환불, 중복 결제, 청구서, 요금제, 결제 수단 등 돈과 관련된 요청",
    "technical": "오류, 장애, 접속 불가, 연동 문제",
    "cancellation": "해지, 탈퇴, 다운그레이드",
    "other": "정보 문의, 사용 방법, 감사 인사, 그 외",
}
INTENT6_TO_4 = {"refund": "billing", "billing_question": "billing", "technical_help": "technical",
                "cancellation": "cancellation", "information": "other", "other": "other"}
EN_DESCRIPTIONS = {
    "intent": {
        "refund": "request for a refund, a payment cancellation, or reimbursement of a duplicate charge",
        "technical_help": "request for technical help with bugs, errors, access failures, or integration problems",
        "billing_question": "question about invoices, pricing plans, payment methods, or amounts charged",
        "information": "question about general information, prices, or how to use the product",
        "cancellation": "request to cancel, close the account, or downgrade",
        "other": "none of the above applies",
    },
    "complexity": {
        "canned": "greetings, standard FAQs, simple status checks",
        "structured": "a request that can be handled deterministically with an API or a template",
        "complex": "a request that needs a generated reply, multi-step reasoning, or compound analysis",
    },
}
PLAIN_INSTRUCTIONS = {
    "intent": "What does the customer want?",
    "is_urgent": "Does the message communicate time pressure or a deadline?",
    "frustration": "How frustrated does the customer sound?",
    "refund_requested": "Does the customer ask for money back?",
    "churn_risk": "Does the message suggest the customer may leave for a competitor or cancel?",
    "needs_llm": "Does answering the message require a free-form generated reply rather than a templated action?",
    "complexity": "How complex is the request?",
}



def v8_combo(out):
    """Pieces chosen by P0b_ablation_analyze.select_v8 on the V0..V7 multilingual runs
    (results/poc/P0b_ablation_summary.md, "V8 rationale"): R1 binary form V2 (noul + labels A/B, no criteria),
    R2 intent 6 classes with V6's English descriptions, R3 complexity Korean descriptions (V0),
    R4 English instructions everywhere (V0), R5 {"message": ...} state."""
    qs = copy.deepcopy(out["V2_labels_ab"][0])
    qs["intent"] = copy.deepcopy(out["V6_en_descriptions"][0]["intent"])
    v0 = out["V0_v1"][0]
    assert all(qs[q] == v0[q] for q in ("frustration", "complexity"))
    return qs, False, {}


# V8 is filled in only after V1..V7 were measured.
V8_PIECES = v8_combo


def load_json(name):
    return json.loads((SCHEMA / name).read_text(encoding="utf-8"))


def gateway_v1b_text():
    """gateway_v1.json text with the 05_poc_plan.md:268 needs_llm criteria, in triage_v1b's layout."""
    line = next(l for l in DOC05.read_text(encoding="utf-8").split("\n") if l.startswith("`needs_llm`도 같은 정책으로"))
    crit = json.loads(re.search(r'`"criteria": (\{[^`]*\})`', line).group(1))
    assert list(crit) == ["true", "false"], crit
    text = (SCHEMA / "gateway_v1.json").read_text(encoding="utf-8")
    ins = json.loads(text)["questions"]["needs_llm"]["instructions"]
    old = '      "instructions": %s\n    }' % json.dumps(ins, ensure_ascii=False)
    assert text.count(old) == 1
    new = ('      "instructions": %s,\n      "criteria": {\n        "true": %s,\n        "false": %s\n      }\n    }'
           % (json.dumps(ins, ensure_ascii=False), json.dumps(crit["true"], ensure_ascii=False),
              json.dumps(crit["false"], ensure_ascii=False)))
    return text.replace(old, new), crit


def to_choice(q, qid, keys):
    yes, no = BINARY_DESC[qid]
    return {"type": "choice", "instructions": q["instructions"], "criteria": {keys[0]: yes, keys[1]: no}}


def variants(v0, v1):
    """name -> (questions, plain_state, expected remap per qid)."""
    out = {"V0_v1": (v0, False, {}), "V1_criteria": (v1, False, {})}

    v2 = copy.deepcopy(v0)
    for qid in NOULS:
        v2[qid]["labels"] = {"true": "A", "false": "B"}
    out["V2_labels_ab"] = (v2, False, {})

    for name, keyset in (("V3a_choice_ab", {q: ("A", "B") for q in NOULS}), ("V3b_choice_semantic", SEMANTIC_KEYS)):
        qs = copy.deepcopy(v0)
        remap = {}
        for qid in NOULS:
            qs[qid] = to_choice(v0[qid], qid, keyset[qid])
            remap[qid] = {True: keyset[qid][0], False: keyset[qid][1]}
        out[name] = (qs, False, remap)

    v4 = copy.deepcopy(v0)
    for qid, ins in KO_INSTRUCTIONS.items():
        v4[qid]["instructions"] = ins
    out["V4_ko_instructions"] = (v4, False, {})

    v5 = copy.deepcopy(v0)
    v5["intent"]["criteria"] = dict(INTENT4)
    out["V5_intent4"] = (v5, False, {"intent": INTENT6_TO_4})

    v6 = copy.deepcopy(v0)
    for qid, crit in EN_DESCRIPTIONS.items():
        assert list(crit) == list(v0[qid]["criteria"])
        v6[qid]["criteria"] = dict(crit)
    out["V6_en_descriptions"] = (v6, False, {})

    v7 = copy.deepcopy(v0)
    for qid, ins in PLAIN_INSTRUCTIONS.items():
        v7[qid]["instructions"] = ins
    out["V7_plain_state"] = (v7, True, {})

    if V8_PIECES is not None:
        out["V8_combo"] = V8_PIECES(out)
    return out


def check_row(questions, row, where):
    for qid, exp in row["expected"].items():
        q = questions[qid]
        if q["type"] == "choice":
            assert isinstance(exp, str) and exp in q["criteria"], (where, qid, exp)
        elif q["type"] == "noul":
            assert isinstance(exp, bool), (where, qid, exp)
        else:
            assert isinstance(exp, int) and not isinstance(exp, bool) and 0 <= exp < len(q["criteria"]), (where, qid, exp)


def main(argv):
    if "--write-gateway-v1b" in argv:
        text, _ = gateway_v1b_text()
        (SCHEMA / "gateway_v1b.json").write_text(text, encoding="utf-8")
        print("wrote", SCHEMA / "gateway_v1b.json")
    text, crit = gateway_v1b_text()
    assert (SCHEMA / "gateway_v1b.json").read_text(encoding="utf-8") == text, "gateway_v1b.json drifted from 05:268"
    print("gateway_v1b.json == gateway_v1.json + 05_poc_plan.md:268 needs_llm criteria", crit)

    lines = SRC.read_text(encoding="utf-8").split("\n")
    header = lines[0]
    assert header.startswith("# ") and lines[-1] == ""
    rows = [json.loads(l) for l in lines[1:] if l.strip()]
    assert len(rows) == 30

    tri, gw, tri_b, gw_b = (load_json(n) for n in ("triage_v1.json", "gateway_v1.json", "triage_v1b.json", "gateway_v1b.json"))
    v0 = {**tri["questions"], **gw["questions"]}
    v1 = {**tri_b["questions"], **gw_b["questions"]}
    assert all(json.dumps(r["questions"], ensure_ascii=False) == json.dumps(v0, ensure_ascii=False) for r in rows)
    assert [q for q in v1 if v1[q] != v0[q]] == NOULS and all("criteria" in v1[q] for q in NOULS)

    OUT_SCHEMA.mkdir(parents=True, exist_ok=True)
    for name, (questions, plain, remap) in variants(v0, v1).items():
        assert list(questions) == list(v0)
        schema = {"questions": questions} if plain else {"state_key": "message", "questions": questions}
        (OUT_SCHEMA / ("%s.json" % name)).write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        out_lines = [header, "# derived from P0_probe_sentences.jsonl, variant %s" % name]
        for i, row in enumerate(rows):
            new = {"state": row["state"]["message"] if plain else row["state"],
                   "questions": questions,
                   "expected": {qid: remap[qid][e] if qid in remap else e for qid, e in row["expected"].items()},
                   "tags": row["tags"], "language": row["language"]}
            assert list(new["expected"]) == list(row["expected"])
            check_row(questions, new, "%s row %d" % (name, i))
            out_lines.append(json.dumps(new, ensure_ascii=False))
        path = OUT_JSONL / ("P0b_%s.jsonl" % name)
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

        ds = evals.Dataset.from_jsonl(str(path))
        assert len(ds) == 30
        print("\n## %s -> %s, questions_sha256=%s, state=%s"
              % (name, path.relative_to(ROOT), evals.questions_fingerprint(ds), "plain str" if plain else '{"message": ...}'))
        for qid, q in questions.items():
            internal = Agent._to_internal(q)
            print("  %-16s %-6s ins=%r" % (qid, q["type"], internal["ins"]))
            print("  %-16s        options=%s" % ("", render_options(internal)))


if __name__ == "__main__":
    main(sys.argv[1:])
