"""K2 throwaway builder: paired MASSIVE ko/en sets (scenario-18, intent-20) and the English
translation of the P0 probe. Writes only under results/korean_support/.

    source env.sh && .venv/bin/python results/korean_support/K2_build.py > results/korean_support/K2_build.log 2>&1

NOT scripts/build_ko_evalsets.py and NOT a frozen 04 evalset.
- scenario-18: 04 §5.1(c) instrument, constants imported from results/poc/P0c_build.py.
- intent-20: port of research/scripts/bench_local.py:165-183, cross-checked option-for-option
  against third_party/laya/research/eval/laya_eval.py build_suite (the harness behind the
  refreshed BENCHMARKS numbers).
- probe: 30 English translations written by the K2 executor; questions = poc/schema v1 / v1b.
"""
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

from datasets import load_dataset
from laya.evals import Dataset, questions_fingerprint

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "results/poc"))
import P0c_build as p0c  # noqa: E402  (constants only; its main() is not run)

N, SEED, N_OPTS, BUILT = 100, 13, 20, "2026-10-02"
REV = p0c.MASSIVE_SRC["revision"]  # mteb/amazon_massive_intent revision is repo-wide (ko and en)
SCEN_Q = {"ko-desc": p0c.SCEN_DESC_KO, "key-desc": p0c.SCEN_DESC_EN}
SCEN_INS = p0c.SETS["massive_scenario18_100"]["instructions"]["en"]
INTENT_INS = "What is the user asking for in `utterance`?"

# English renderings of results/poc/P0_probe_sentences.jsonl rows 0-29 (K2 executor, 2026-10-02).
# Meaning, tone and every negation kept; the Korean source is asserted row by row below.
PROBE_EN = [
    ("같은 달 요금이 두 번 빠져나간 것 같아",
     "I'm reaching out because I'm worried I was charged twice for the same month. Could you please check and refund the duplicate payment?"),
    ("어제 실수로 연간 플랜을 결제했어요",
     "I accidentally paid for the annual plan yesterday :( I haven't used it even once yet. Can I cancel the payment and get a refund?"),
    ("장난하세요? 분명히 해지했는데",
     "Are you kidding me? I definitely cancelled, and you charged me again this month. If you don't refund me by the end of today, I'm reporting you to the consumer protection agency."),
    ("안녕하세요. 지난주 화요일부터 사흘간",
     "Hello. The service outage that lasted three days starting last Tuesday seriously disrupted our work. We would like to get back a prorated share of the fee for the outage period. Please let us know whether this is possible."),
    ("서비스는 앞으로도 계속 쓸 거예요.",
     "I'm going to keep using the service. However, I'd like a refund for the extra usage fee that was wrongly charged last month."),
    ("비밀번호 재설정 메일이 안 오는데",
     "I'm not receiving the password reset email. What should I do?"),
    ("결제 API가 30분째 500 에러만",
     "The payment API has been returning nothing but 500 errors for 30 minutes. All orders on our online store are blocked right now. Please look into this immediately!!"),
    ("해지할 생각은 없는데요,",
     "I'm not planning to cancel, but lately the app logs me out on its own several times a day, which is really inconvenient. Is there any way to fix this?"),
    ("안녕하세요. 슬랙 연동을 설정했는데",
     "Hello. I set up the Slack integration, but notifications are not being sent to the channel. The webhook URL appears to be registered correctly. Are there any other settings I should check?"),
    ("업데이트하고 나서 또 동기화가 안 되네요.",
     "Sync stopped working again after the update. This is already the third time. If it keeps going like this, I'm switching to another service."),
    ("해지하고 싶지는 않고 요금제만 바꾸고 싶어요.",
     "I don't want to cancel, I just want to change my plan. If I switch from monthly to annual billing, do I get a discount?"),
    ("환불은 필요 없고요,",
     "I don't need a refund. I just want future payments to go to a different card starting with the next billing. Where do I change that?"),
    ("이번 달 청구 금액이 평소보다 2만 원",
     "This month's bill is more than 20,000 won higher than usual. Could you explain why? I don't think my usage went up."),
    ("세금계산서 발행 요청드립니다.",
     "I'd like to request a tax invoice. I've sent our business registration certificate as an attachment. We need to receive it by this Friday to complete our settlement, so please process it before the deadline."),
    ("결제 수단을 등록하려는데 카드가 계속 거절된다고",
     "I'm trying to add a payment method, but it keeps saying my card was declined. The card works fine everywhere else. This is really annoying."),
    ("프로 플랜이랑 팀 플랜 차이가 뭔가요?",
     "What's the difference between the Pro plan and the Team plan? Please tell me the prices too."),
    ("모바일 앱에서도 PDF로 내보내기가 되나요?",
     "Can I export to PDF from the mobile app too?"),
    ("안녕하세요. 저희 회사에서 도입을 검토 중인데,",
     "Hello. Our company is considering adopting your service, and we'd like to know whether data is stored in a region inside Korea and whether you are ISMS certified. If you have any materials for a security review, please share them as well."),
    ("내일 오전에 고객사 데모가 있는데,",
     "We have a demo for a client tomorrow morning. Is real-time co-editing possible while screen sharing? Please reply by the end of today."),
    ("고객센터 운영 시간이 어떻게 되나요?",
     "What are your customer service hours? Is support available on weekends too?"),
    ("다음 달부터는 안 쓸 것 같아서요.",
     "I don't think I'll be using it from next month. Where do I cancel my subscription?"),
    ("솔직히 가격 대비 너무 별로네요.",
     "Honestly, it's really not worth the price. Your competitor costs half as much, so there's no reason to stay here. I'll use it until the end of this month and then cancel."),
    ("프로 플랜에서 무료 플랜으로 다운그레이드하고 싶습니다.",
     "I'd like to downgrade from the Pro plan to the free plan. Will the documents I've already created be kept?"),
    ("탈퇴하려는데 탈퇴 버튼이 어디에도 없네요.",
     "I'm trying to delete my account, but there's no delete-account button anywhere. Today is my billing date, so this has to be done today. If not, I'll ask my card company to stop the payment."),
    ("안녕하세요. 회사 사정으로 이번 달 말일자로",
     "Hello. Due to internal circumstances, we plan to end our contract as of the last day of this month. Please also let us know whether we can get a refund of the fee for the remaining period."),
    ("상담원분이 끝까지 친절하게 도와주셔서",
     "The support agent kindly helped me all the way through, and the problem got resolved. Thank you!"),
    ("채용 공고 보고 연락드렸는데,",
     "I saw your job posting and wanted to get in touch. Where should I send my application?"),
    ("어제 통화한 상담원 태도 진짜 최악이었어요.",
     "The attitude of the agent I spoke with on the phone yesterday was absolutely the worst. They kept cutting me off and even laughed at me. Is this how you treat customers? I'm filing a formal complaint."),
    ("제휴 마케팅 관련해서 제안드리고 싶은데",
     "I'd like to make a proposal regarding affiliate marketing. Could I get the contact information for the department in charge?"),
    ("해지 문의는 아니고요,",
     "This isn't about cancelling. The feature I requested last time was included in this update, so I'm just leaving a note to say thank you."),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(name, header, rows):
    path = HERE / name
    lines = header + [json.dumps(r, ensure_ascii=False) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ds = Dataset.from_jsonl(str(path))
    assert len(ds) == len(rows), (name, len(ds))
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path),
            "questions_sha256": questions_fingerprint(ds), "n": len(rows)}


def jsonl_rows(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def load_upstream_harness():
    """third_party/laya/research/eval/laya_eval.py, loaded by path. Its top-level imports are stdlib
    only; it prepends third_party/laya to sys.path, so laya is already imported above and stays the
    installed package (asserted)."""
    import laya
    before = laya.__file__
    spec = importlib.util.spec_from_file_location("laya_eval_upstream", ROOT / "third_party/laya/research/eval/laya_eval.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert sys.modules["laya"].__file__ == before and ".venv" in before, before
    return mod


def build_massive(meta):
    ko = load_dataset("mteb/amazon_massive_intent", "ko", split="test", revision=REV)
    en = load_dataset("mteb/amazon_massive_intent", "en", split="test", revision=REV)
    en_by_id = {r["id"]: r for r in en}
    first = list(ko)[:N]
    pairs = []
    for r in first:
        t = en_by_id[r["id"]]
        assert t["label_text"] == r["label_text"], (r["id"], r["label_text"], t["label_text"])
        pairs.append((r, t))
    labels_ko, labels_en = sorted(set(ko["label_text"])), sorted(set(en["label_text"]))
    meta["massive"] = {
        "source": {"dataset": "mteb/amazon_massive_intent", "configs": ["ko", "en"], "split": "test", "revision": REV},
        "cache_files": [ko.cache_files[0]["filename"], en.cache_files[0]["filename"]],
        "rows": {"ko": len(ko), "en": len(en)},
        "same_id_order_full_split": ko["id"] == en["id"],
        "en_first_100_are_the_ko_twins": [r["id"] for r in first] == en["id"][:N],
        "label_text_equal_all_100_pairs": True,
        "labels": {"ko": len(labels_ko), "en": len(labels_en), "identical_sets": labels_ko == labels_en},
        "exact_duplicate_ko_texts_in_first_100": sorted({r["text"] for r in first if sum(x["text"] == r["text"] for x in first) > 1}),
        "exact_duplicate_en_texts_in_twins": sorted({t["text"] for _, t in pairs if sum(y["text"] == t["text"] for _, y in pairs) > 1}),
        "row_ids": [r["id"] for r in first],
    }
    return pairs, labels_ko, ko, en


def build_scenario(pairs, meta):
    prefixes = sorted({r["label_text"].split("_", 1)[0] for r, _ in pairs} | set(p0c.SCEN_DESC_KO))
    assert prefixes == list(p0c.SCEN_DESC_KO), prefixes
    p0c_rows = {"ko-desc": jsonl_rows(ROOT / "results/poc/P0c_massive_scenario18_100.jsonl"),
                "key-desc": jsonl_rows(ROOT / "results/poc/P0c_massive_scenario18_100_en-desc.jsonl")}
    for desc, crit in SCEN_Q.items():
        question = {"type": "choice", "instructions": SCEN_INS, "criteria": dict(crit)}
        for lang in ("ko", "en"):
            rows = []
            for i, (r, t) in enumerate(pairs):
                src = r if lang == "ko" else t
                row = {"state": {"utterance": src["text"]}, "questions": {"scenario": question},
                       "expected": {"scenario": r["label_text"].split("_", 1)[0]},
                       "tags": ["massive", "scenario18", "k2_paired", "id:%s" % r["id"]], "language": lang}
                if lang == "ko":  # same instrument and rows as the P0c run it should reproduce
                    ref = p0c_rows[desc][i]
                    assert (ref["state"], ref["questions"], ref["expected"]) == (row["state"], row["questions"], row["expected"]), i
                rows.append(row)
            name = "K2_scen18_%s_%s.jsonl" % (desc.replace("-", ""), lang)
            header = ["# K2 throwaway paired set (not a frozen 04 evalset). MASSIVE scenario-18, %s descriptions, %s utterances; "
                      "rows = first 100 ko test rows + en twins joined on id; mteb/amazon_massive_intent test @%s" % (desc, lang, REV),
                      "# build: results/korean_support/K2_build.py; question = 04 §5.1(c) via results/poc/P0c_build.py constants; built %s" % BUILT]
            meta["files"][name] = write_jsonl(name, header, rows)


def build_intent20(pairs, labels, ko, en, meta):
    # Port of research/scripts/bench_local.py:165-183 for ko; the en twin reuses the ko row's keys.
    rng = random.Random(SEED)
    keys_per_row = []
    for r, _ in pairs:
        pool = [x for x in labels if x != r["label_text"]]
        keys = [r["label_text"]] + rng.sample(pool, min(N_OPTS - 1, len(pool)))
        rng.shuffle(keys)
        keys_per_row.append(keys)
    # Cross-check 1: upstream harness build_suite, per language with its own fresh rng and label set.
    up = load_upstream_harness()
    for lang, d in (("ko", ko), ("en", en)):
        rows = [{"text": x["text"], "label_text": x["label_text"]} for x in d]
        cases, gold, option_keys = up.build_suite(rows, sorted({x["label_text"] for x in rows}), N, N_OPTS, SEED)
        assert option_keys == keys_per_row, lang
        assert [c[0]["utterance"] for c in cases] == [(r if lang == "ko" else t)["text"] for r, t in pairs], lang
        assert [c[1]["intent"]["criteria"] for c in cases] == [{k: up.render_label(k) for k in ks} for ks in keys_per_row]
    meta["intent20_construction"] = {
        "port_of": "research/scripts/bench_local.py:165-183",
        "criteria_render": 'k.replace("_", " ").replace(".", ": ")  (bench_local.py:180, laya_eval.render_label)',
        "identical_to_upstream_laya_eval_build_suite": {"ko": True, "en": True},
        "note": "ko and en test splits share id order and the 59-label set, so upstream's per-language fresh "
                "random.Random(13) draws the same 19 distractors and shuffle for each twin",
    }
    for lang in ("ko", "en"):
        rows = []
        for (r, t), keys in zip(pairs, keys_per_row):
            src = r if lang == "ko" else t
            rows.append({"state": {"utterance": src["text"]},
                         "questions": {"intent": {"type": "choice", "instructions": INTENT_INS,
                                                  "criteria": {k: k.replace("_", " ").replace(".", ": ") for k in keys}}},
                         "expected": {"intent": r["label_text"]},
                         "tags": ["massive", "20opt", "scenario:%s" % r["label_text"].split("_", 1)[0], "k2_paired", "id:%s" % r["id"]],
                         "language": lang})
        name = "K2_intent20_%s.jsonl" % lang
        header = ["# K2 throwaway paired set (not a frozen 04 evalset). MASSIVE intent-20, upstream-faithful (04 §5.1(a)), %s utterances; "
                  "rows = first 100 ko test rows + en twins joined on id; mteb/amazon_massive_intent test @%s" % (lang, REV),
                  "# build: results/korean_support/K2_build.py; option sets identical per twin and to laya_eval.build_suite; built %s" % BUILT]
        meta["files"][name] = write_jsonl(name, header, rows)


def build_probe(meta):
    src_path = ROOT / "results/poc/P0_probe_sentences.jsonl"
    ko_rows = jsonl_rows(src_path)
    assert len(ko_rows) == len(PROBE_EN) == 30
    schema = {n: json.loads((ROOT / "poc/schema" / n).read_text(encoding="utf-8"))["questions"]
              for n in ("triage_v1.json", "gateway_v1.json", "triage_v1b.json", "gateway_v1b.json")}
    v1 = {**schema["triage_v1.json"], **schema["gateway_v1.json"]}
    v1b = {**schema["triage_v1b.json"], **schema["gateway_v1b.json"]}
    assert all(r["questions"] == v1 for r in ko_rows)
    v1b_ko = jsonl_rows(ROOT / "results/poc/P0b_V1_criteria.jsonl")
    assert all(r["questions"] == v1b for r in v1b_ko) and [r["state"] for r in v1b_ko] == [r["state"] for r in ko_rows]
    src_sha = sha(src_path)
    for name, questions, label in (("probe_en.jsonl", v1, "v1 (poc/schema/triage_v1.json + gateway_v1.json)"),
                                   ("K2_probe_en_v1b.jsonl", v1b, "v1b (poc/schema/triage_v1b.json + gateway_v1b.json)")):
        rows = []
        for (prefix, text), r in zip(PROBE_EN, ko_rows):
            assert r["state"]["message"].startswith(prefix), (prefix, r["state"]["message"])
            rows.append({"state": {"message": text}, "questions": questions, "expected": r["expected"],
                         "tags": ["p0_probe_en"], "language": "en"})
        header = ["# English translation (by the K2 executor, 2026-10-02) of the throwaway P0 probe results/poc/P0_probe_sentences.jsonl "
                  "(sha256 %s): same 30 rows in the same order, `expected` copied unchanged. Inherits its caveats: ad-hoc self-labelled "
                  "by one labeller, NOT a label policy, NEVER to be reused in ko_poc_triage_v1 or any eval set, indicative only." % src_sha,
                  "# questions = %s; build: results/korean_support/K2_build.py" % label]
        meta["files"][name] = write_jsonl(name, header, rows)
    meta["probe"] = {"source": str(src_path.relative_to(ROOT)), "source_sha256": src_sha, "translator": "K2 executor (LLM agent), single pass, not back-translated"}


def main():
    meta = {"builder": "results/korean_support/K2_build.py", "built": BUILT, "files": {}}
    pairs, labels, ko, en = build_massive(meta)
    build_scenario(pairs, meta)
    build_intent20(pairs, labels, ko, en, meta)
    build_probe(meta)
    # paired files must share the question fingerprint (identical instrument per twin)
    f = meta["files"]
    for a, b in (("K2_scen18_kodesc_ko.jsonl", "K2_scen18_kodesc_en.jsonl"), ("K2_scen18_keydesc_ko.jsonl", "K2_scen18_keydesc_en.jsonl"),
                 ("K2_intent20_ko.jsonl", "K2_intent20_en.jsonl")):
        assert f[a]["questions_sha256"] == f[b]["questions_sha256"], (a, b)
    (HERE / "K2_build_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for name, e in f.items():
        print("%-28s n=%d sha256=%s questions_sha256=%s" % (name, e["n"], e["sha256"], e["questions_sha256"]))
    print(json.dumps({k: v for k, v in meta["massive"].items() if k != "row_ids"}, ensure_ascii=False))
    print(json.dumps(meta["intent20_construction"], ensure_ascii=False))


if __name__ == "__main__":
    main()
