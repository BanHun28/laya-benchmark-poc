"""Track C / PoC P1 wording round (05 §6 P1 step 7): router schema v2 variants on the ko_massive_domain_8 DEV half.

No model call. Writes results/C/schemas_v2/router_<v>_dev[_general].jsonl (original header + one `# split: dev`
line; v1 data lines byte-identical to the source, variants re-serialized with only `questions` and, for v2e,
`expected` changed), router_<v>.json schema files (poc/schema layout), BUILD.json (hashes, row counts, v2c example
overlap check, head budget), and prints a Markdown build note.

    source env.sh && .venv/bin/python results/C/C_schema_v2_build.py > results/C/schemas_v2/BUILD.md
"""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from metrics_extra import read_dataset, row_splits  # noqa: E402
from laya.agent import Agent, _load_tokenizer  # noqa: E402
from laya.common import build_head, encode_text, render_options  # noqa: E402
from laya.evals import Dataset, questions_fingerprint  # noqa: E402

SRC = ROOT / "data/evals/ko_massive_domain_8.jsonl"
OUT = ROOT / "results/C/schemas_v2"
QID = "domain"
V2A = {"productivity": "알람·타이머 설정, 일정 등록·조회, 날짜·시간 질문, 할 일·쇼핑 목록 관리",
       "media": "음악·라디오·팟캐스트·오디오북 재생과 음량·음소거 같은 오디오 조절",
       "smart_home": "조명, 커피머신, 청소기, 플러그 등 집안 기기를 켜고 끄거나 설정 변경 (오디오 재생·음량은 제외)",
       "info_qa": "날씨, 뉴스, 사실·정의·계산·환율 같은 정보를 묻는 질문",
       "communication": "이메일 보내기·확인, 연락처, 소셜 미디어 게시·확인",
       "lifestyle": "음식 주문·배달, 요리법, 장소·이벤트·영화 추천",
       "transport": "교통, 택시 호출, 기차·항공 티켓, 길 안내",
       "general": "인사, 농담, 안부, 잡담처럼 특정 작업을 요청하지 않는 대화"}
# written before looking at any row; checked for exact overlap with the dev states (and counted on the whole file).
# info_qa's first example was '오늘 서울 날씨 어때' (contains the dev utterance '서울', row 340, transport), then
# '이번 주말 날씨 알려줘' (shares '알려줘' with the lifestyle example); both replaced before any model run
EXAMPLES = {"productivity": ("내일 아침 7시에 깨워줘", "장보기 목록에 우유 추가"),
            "media": ("아이유 노래 틀어줘", "소리 좀 줄여줘"),
            "smart_home": ("거실 불 꺼줘", "로봇청소기 돌려줘"),
            "info_qa": ("이번 주말 날씨 어때", "달러 환율 얼마야"),
            "communication": ("김 과장한테 메일 보내줘", "페이스북 새 소식 보여줘"),
            "lifestyle": ("치킨 배달 시켜줘", "김치찌개 끓이는 법 알려줘"),
            "transport": ("강남역까지 택시 불러줘", "부산 가는 KTX 예매해줘"),
            "general": ("안녕 잘 지냈어", "재미있는 농담 하나 해줘")}
COARSE = {"productivity": "assistant_tasks", "communication": "assistant_tasks", "media": "media",
          "smart_home": "smart_home", "info_qa": "info_qa", "lifestyle": "daily_life", "transport": "daily_life"}
V2E = {"assistant_tasks": "알람·일정·시간·목록·이메일·소셜 등 비서 작업", "media": V2A["media"],
       "smart_home": V2A["smart_home"], "info_qa": V2A["info_qa"], "daily_life": "음식·요리·추천·교통·이동"}
ORDER_V2D = ["general"] + [k for k in V2A if k not in ("general", "smart_home")] + ["smart_home"]
VARIANTS = {  # name: (criteria, expected map or None, drop general rows into a separate unscored file, note)
    "v1": (None, None, False, "baseline router_v1 (questions byte-identical to data/evals/ko_massive_domain_8.jsonl)"),
    "v2a": (V2A, None, False, "sharpened descriptions, same 8 keys, same order"),
    "v2b": ({k: v for k, v in V2A.items() if k != "general"}, None, True, "v2a without general (7 options)"),
    "v2c": ({k: "%s 예: '%s', '%s'" % (v, *EXAMPLES[k]) for k, v in V2A.items()}, None, False,
            "v2a + 2 example utterances per description"),
    "v2d": ({k: V2A[k] for k in ORDER_V2D}, None, False, "v2a reordered: general first, smart_home last"),
    "v2e": (V2E, COARSE, True, "5-class coarse taxonomy (assistant_tasks, media, smart_home, info_qa, daily_life)"),
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def norm(s):
    return re.sub(r"[\s.,!?~'\"]", "", s)


def words(s):
    return set(re.findall(r"[가-힣A-Za-z0-9]+", s)) - {"예"}  # "예" is v2c's example marker


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [l for l in SRC.read_text(encoding="utf-8").splitlines() if l.strip()]
    head = [l for l in lines if l.strip().startswith("#")]
    body = [l for l in lines if not l.strip().startswith("#")]
    rows, header = read_dataset(SRC)
    splits, rule = row_splits(rows, header, "auto", SRC.name)
    ref = json.loads((ROOT / "results/B/B_splits.json").read_text(encoding="utf-8"))["splits"][SRC.stem]
    dev = [i for i, s in enumerate(splits) if s == "dev"]
    dist = {QID: dict(sorted(Counter(rows[i]["expected"][QID] for i in dev).items()))}
    assert rule == ref["rule"] == "index parity" and len(dev) == ref["dev"] == 250 and dist == ref["label_distribution"]["dev"]
    assert all(json.dumps(r, ensure_ascii=False) == b for r, b in zip(rows, body)), "source lines are not json.dumps(row)"
    v1 = rows[0]["questions"][QID]
    assert all(r["questions"] == {QID: v1} for r in rows)
    src_note = "source: data/evals/ko_massive_domain_8.jsonl sha256 %s" % sha(SRC)
    build = {"source": str(SRC.relative_to(ROOT)), "source_sha256": sha(SRC), "split_rule": rule, "dev_rows": len(dev),
             "dev_label_distribution": dist[QID], "files": {}, "schemas": {}}
    print("# router schema v2 build (dev half of ko_massive_domain_8, %d rows; %s)\n" % (len(dev), src_note))
    print("| variant | file | rows | options | dataset sha256 | questions_sha256 | note |\n|---|---|---|---|---|---|---|")
    for name, (crit, emap, split_general, note) in VARIANTS.items():
        q = v1 if crit is None else {"type": v1["type"], "instructions": v1["instructions"], "criteria": crit}
        schema = OUT / ("router_%s.json" % name)
        schema.write_text(json.dumps({"state_key": "utterance", "questions": {QID: q}}, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
        build["schemas"][name] = {"path": str(schema.relative_to(ROOT)), "sha256": sha(schema), "options": list(q["criteria"])}
        parts = {"": [], "_general": []}
        for i in dev:
            r = rows[i]
            gold = r["expected"][QID]
            if crit is None:
                line = body[i]
            else:
                new = dict(r, questions={QID: q}, expected={QID: emap.get(gold, gold) if emap else gold})
                line = json.dumps(new, ensure_ascii=False)
            parts["_general" if split_general and gold == "general" else ""].append(line)
        for suffix, keep in parts.items():
            if not keep:
                continue
            path = OUT / ("router_%s_dev%s.jsonl" % (name, suffix))
            extra = " | gold general is outside this schema: unscorable rows, for the confidence-gate analysis only" if suffix else ""
            note_line = "# split: dev | rule: index parity (even data-row index -> dev, odd -> test) | %s | rows %d/%d | variant %s: %s%s | Track C 2026-10-02 (results/C/C_schema_v2_build.py)" % (
                src_note, len(keep), len(body), name, note, extra)
            path.write_text("\n".join(head + [note_line] + keep) + "\n", encoding="utf-8")
            qs = questions_fingerprint(Dataset.from_jsonl(str(path)))
            key = name + suffix
            build["files"][key] = {"path": str(path.relative_to(ROOT)), "rows": len(keep), "sha256": sha(path), "questions_sha256": qs}
            print("| %s | %s | %d | %d | %s | %s | %s |" % (key, path.relative_to(ROOT), len(keep), len(q["criteria"]), sha(path), qs,
                                                          note + extra))
    # v2c examples: exact overlap (whitespace/punctuation-insensitive) with dev states; whole-file count only
    dev_states = {norm(rows[i]["state"]["utterance"]): rows[i]["state"]["utterance"] for i in dev}
    all_states = {norm(r["state"]["utterance"]) for r in rows}
    ex = [e for pair in EXAMPLES.values() for e in pair]
    build["v2c_examples_overlap"] = {"examples": len(ex), "dev_exact": [dev_states[norm(e)] for e in ex if norm(e) in dev_states],
                                     "whole_file_exact_count": sum(norm(e) in all_states for e in ex),
                                     "dev_substring": [[e, dev_states[s]] for e in ex for s in dev_states if norm(e) in s or s in norm(e)]}
    print("\nv2c examples vs states (normalized: whitespace and .,!?~'\" removed): %d examples, exact matches with dev states %s, "
          "exact matches anywhere in the 500-row file %d, dev substring containments %s"
          % (len(ex), build["v2c_examples_overlap"]["dev_exact"] or "none", build["v2c_examples_overlap"]["whole_file_exact_count"],
             build["v2c_examples_overlap"]["dev_substring"] or "none"))
    # head budget (multilingual): does the model see each option intact?
    d = (ROOT / "models/laya-multilingual").resolve()
    cfg = json.loads((d / "rl_agent_config.json").read_text(encoding="utf-8"))
    tok = _load_tokenizer(str(d / "tokenizer"), cfg)
    print("\n## head budget (multilingual, tokenizer only)\n\nPer option: 1 [MASK] + tokens of ' key: description', each capped at 48 "
          "by the tokenizer (laya/common.py build_head). If the options exceed head_max_len - 16, every option is cut to "
          "max(4, (head_max_len - 16) // k) tokens.\n")
    print("| variant | head_max_len | tokens per option (uncapped) | sum | per-option cap applied | head length | options as the model sees them |\n|---|---|---|---|---|---|---|")
    build["head_budget"] = {}
    for name, (crit, _, _, _) in VARIANTS.items():
        q = Agent._to_internal(v1 if crit is None else {"type": "choice", "instructions": v1["instructions"], "criteria": crit})
        for hml in ([cfg["head_max_len"], 512] if name == "v2c" else [cfg["head_max_len"]]):
            ids, markers, st = build_head(tok, q, hml)
            raw = [1 + len(encode_text(tok, " " + o, add_special_tokens=False)["input_ids"]) for o in render_options(q)]
            ends = list(markers[1:]) + [len(ids) - 1]
            kept = [tok.decode(ids[a + 1:b]).strip() for a, b in zip(markers, ends)]
            build["head_budget"]["%s@%d" % (name, hml)] = {"raw": raw, "sum": sum(raw), "cap": st["tokens_per_option"],
                                                            "head_len": len(ids), "kept": kept}
            print("| %s | %d | %s | %d | %s | %d | %s |" % (name, hml, raw, sum(raw), st["tokens_per_option"], len(ids),
                                                          " / ".join(kept).replace("|", "\\|")))
    # vocabulary shared by two options' descriptions (04 §5.1 (d) asks for disjoint descriptions)
    print("\n## words shared across options (regex [가-힣A-Za-z0-9]+, no stemming: josa-attached forms count as different words)\n")
    for name, (crit, _, _, _) in VARIANTS.items():
        c = v1["criteria"] if crit is None else crit
        shared = {"%s ∩ %s" % (a, b): sorted(words(c[a]) & words(c[b])) for i, a in enumerate(c) for b in list(c)[i + 1:]
                  if words(c[a]) & words(c[b])}
        build.setdefault("shared_words", {})[name] = shared
        print("- %s: %s" % (name, "; ".join("%s: %s" % (k, ", ".join(v)) for k, v in shared.items()) or "none"))
    (OUT / "BUILD.json").write_text(json.dumps(build, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
