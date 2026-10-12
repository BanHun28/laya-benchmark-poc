"""P0c throwaway preview builder: KLUE YNAT-7 and MASSIVE scenario-18, n=100, plus the
instruction/description-language variants (03 §7 B3 preview).

NOT scripts/build_ko_evalsets.py and NOT the frozen 04 evalsets: everything is written under
results/poc/, nothing under data/. Schemas follow 04 §5.2 and §5.1(c) byte for byte.

    source env.sh && .venv/bin/python results/poc/P0c_build.py
"""
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

from datasets import load_dataset
from laya.evals import Dataset, questions_fingerprint

OUT = Path(__file__).resolve().parent
N, SEED, BUILT = 100, 13, "2026-10-02"

# Revisions resolved with HfApi().dataset_info(...).sha on 2026-10-02 and pinned here so a rerun
# loads the same bytes.
YNAT_SRC = {"dataset": "klue/klue", "config": "ynat", "split": "validation",
            "revision": "349481ec73fff722f88e0453ca05c77a447d967c", "license": "cc-by-sa-4.0 (HF card)"}
MASSIVE_SRC = {"dataset": "mteb/amazon_massive_intent", "config": "ko", "split": "test",
               "revision": "940fd47a81eaa7f2cc7b129674d945d618ac38c2", "license": "apache-2.0 (HF card)"}
SCENARIO_SRC = {"dataset": "mteb/amazon_massive_scenario", "config": "ko", "split": "test",
                "revision": "58871793b91addb7c5f7afff26ccf08737fb6697"}

YNAT_NAMES = ["IT과학", "경제", "사회", "생활문화", "세계", "스포츠", "정치"]
# 04 §5.2 table, in ClassLabel index order.
YNAT_DESC_KO = {
    "it_science": "IT, 과학, 기술, 통신, 인터넷",
    "economy": "경제, 금융, 산업, 기업, 부동산",
    "society": "사회, 사건사고, 교육, 노동, 복지",
    "culture_life": "생활, 문화, 예술, 건강, 여행, 음식",
    "world": "국제, 해외 뉴스, 외교",
    "sports": "스포츠, 경기, 선수",
    "politics": "정치, 국회, 정당, 선거, 정부",
}
# P0c's own item-by-item English rendering of the same table (no doc source exists).
YNAT_DESC_EN = {
    "it_science": "IT, science, technology, telecommunications, internet",
    "economy": "economy, finance, industry, companies, real estate",
    "society": "society, incidents and accidents, education, labor, welfare",
    "culture_life": "lifestyle, culture, arts, health, travel, food",
    "world": "international, foreign news, diplomacy",
    "sports": "sports, matches, athletes",
    "politics": "politics, National Assembly, political parties, elections, government",
}
# 04 §5.1(c) table, keys in sorted order.
SCEN_DESC_KO = {
    "alarm": "알람 설정, 해제, 조회",
    "audio": "음량 조절, 음소거",
    "calendar": "일정 등록, 조회, 삭제",
    "cooking": "요리법, 조리 질문",
    "datetime": "날짜와 시간 질문, 시간대 변환",
    "email": "이메일 확인, 전송, 연락처",
    "general": "잡담, 농담, 일반적인 대화",
    "iot": "조명, 커피머신, 청소기 등 스마트홈 기기 제어",
    "lists": "목록 만들기, 항목 추가, 삭제, 조회",
    "music": "음악 취향, 재생 설정",
    "news": "뉴스 조회",
    "play": "음악, 라디오, 팟캐스트, 오디오북, 게임 재생",
    "qa": "사실, 정의, 수학, 환율, 주식 질문",
    "recommendation": "장소, 이벤트, 영화 추천",
    "social": "소셜 미디어 게시, 조회",
    "takeaway": "음식 주문, 배달 조회",
    "transport": "교통, 택시, 티켓, 길 안내",
    "weather": "날씨 질문",
}
# Upstream's rendering (research/scripts/build_benchmark_nb.py:316).
SCEN_DESC_EN = {k: k.replace("_", " ").replace(".", ": ") for k in SCEN_DESC_KO}

SETS = {
    "ynat100": {"qid": "topic", "tags": ["klue", "ynat", "p0c"],
                "instructions": {"en": "Which news section does `headline` belong to?",
                                 "ko": "`headline`은 어느 뉴스 섹션에 속하나요?"},
                "desc": {"ko": YNAT_DESC_KO, "en": YNAT_DESC_EN}},
    "massive_scenario18_100": {"qid": "scenario", "tags": ["massive", "scenario18", "p0c"],
                               "instructions": {"en": "Which domain does `utterance` belong to?",
                                                "ko": "`utterance`는 어느 도메인에 속하나요?"},
                               "desc": {"ko": SCEN_DESC_KO, "en": SCEN_DESC_EN}},
}
# suffix -> (instructions language, descriptions language). "" is the 04 default.
# `_ko-instr_en-desc` completes the 2x2 so both readings of the `_en-desc` request are covered.
VARIANTS = {"": ("en", "ko"), "_ko-instr": ("ko", "ko"), "_en-desc": ("en", "en"),
            "_ko-instr_en-desc": ("ko", "en")}


def build_ynat():
    d = load_dataset(YNAT_SRC["dataset"], YNAT_SRC["config"], split=YNAT_SRC["split"],
                     revision=YNAT_SRC["revision"])
    assert d.features["label"].names == YNAT_NAMES, d.features["label"].names
    keys = list(YNAT_DESC_KO)
    seen, pool, dropped = set(), [], Counter()
    for r in sorted(d, key=lambda r: r["guid"]):
        if not 2 <= len(r["title"]) <= 2000:
            dropped["length"] += 1
        elif r["title"] in seen:
            dropped["duplicate"] += 1
        else:
            seen.add(r["title"])
            pool.append(r)
    base, extra = divmod(N, len(keys))
    # cap ceil(N/k); the first N mod k labels take the extra row, as in the 04:333 MANIFEST example
    quota = [base + (i < extra) for i in range(len(keys))]
    rng = random.Random(SEED)
    picked = []
    for i, q in enumerate(quota):
        group = [r for r in pool if r["label"] == i]
        picked += rng.sample(group, min(q, len(group)))
    if len(picked) < N:  # 04 §5 top-up rule
        taken = {r["guid"] for r in picked}
        picked += rng.sample([r for r in pool if r["guid"] not in taken], N - len(picked))
    picked.sort(key=lambda r: r["guid"])
    items = [({"headline": r["title"]}, keys[r["label"]], r["guid"]) for r in picked]
    note = {"cache_file": d.cache_files[0]["filename"], "source_rows": len(d), "pool_rows": len(pool),
            "dropped": dict(dropped), "quota": dict(zip(keys, quota)),
            "source_label_distribution": {keys[i]: c for i, c in sorted(Counter(d["label"]).items())},
            "sampling": "guid-sorted; per label in ClassLabel order random.Random(13).sample(group, quota); "
                        "rows written in guid order"}
    return items, note


def build_scenario():
    d = load_dataset(MASSIVE_SRC["dataset"], MASSIVE_SRC["config"], split=MASSIVE_SRC["split"],
                     revision=MASSIVE_SRC["revision"])
    prefix = [t.split("_", 1)[0] for t in d["label_text"]]
    found = sorted(set(prefix))
    assert found == list(SCEN_DESC_KO), found  # exactly the 18 keys of 04 §5.1(c)
    # Cross-check the prefix rule against the official scenario labels, joined on id.
    s = load_dataset(SCENARIO_SRC["dataset"], SCENARIO_SRC["config"], split=SCENARIO_SRC["split"],
                     revision=SCENARIO_SRC["revision"])
    official = dict(zip(s["id"], s["label_text"]))
    mismatch = sum(official.get(i) != p for i, p in zip(d["id"], prefix))
    assert mismatch == 0, mismatch
    first = d.select(range(N))  # 04 §5.1: the first 100 rows, no shuffle, no stratification
    items = [({"utterance": r["text"]}, r["label_text"].split("_", 1)[0], r["id"]) for r in first]
    texts = Counter(r["text"] for r in first)
    note = {"cache_file": d.cache_files[0]["filename"], "source_rows": len(d),
            "distinct_intents_in_split": len(set(d["label_text"])),
            "distinct_scenarios_in_split": len(found),
            "prefix_vs_official_scenario_mismatches": mismatch,
            "exact_duplicate_texts_in_first_100": {t: c for t, c in texts.items() if c > 1},
            "sampling": "first 100 rows of the test split in file order"}
    return items, note


def write(name, suffix, items, src, note):
    spec = SETS[name]
    ins_lang, desc_lang = VARIANTS[suffix]
    question = {"type": "choice", "instructions": spec["instructions"][ins_lang],
                "criteria": dict(spec["desc"][desc_lang])}
    path = OUT / ("P0c_%s%s.jsonl" % (name, suffix))
    header = [
        "# P0c PREVIEW, throwaway: not a frozen 04 evalset and not data/evals/. Schema per 04 %s. "
        "source %s config=%s split=%s revision=%s"
        % ("§5.2" if name.startswith("ynat") else "§5.1(c)", src["dataset"], src["config"], src["split"], src["revision"]),
        "# build: results/poc/P0c_build.py n=%d seed=%d instructions=%s descriptions=%s; %s; built %s"
        % (N, SEED, ins_lang, desc_lang, note["sampling"], BUILT),
    ]
    rows = [json.dumps({"state": state, "questions": {spec["qid"]: question}, "expected": {spec["qid"]: key},
                        "tags": spec["tags"], "language": "ko"}, ensure_ascii=False)
            for state, key, _ in items]
    path.write_text("\n".join(header + rows) + "\n", encoding="utf-8")
    dist = Counter(key for _, key, _ in items)
    return {
        "path": str(path.relative_to(OUT.parent.parent)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "questions_sha256": questions_fingerprint(Dataset.from_jsonl(str(path))),
        "n": len(rows),
        "source": {k: src[k] for k in ("dataset", "config", "split", "revision")},
        "license": src["license"],
        "build_args": {"n": N, "seed": SEED, "instructions": ins_lang, "descriptions": desc_lang},
        "label_distribution": dict(sorted(dist.items(), key=lambda kv: (-kv[1], kv[0]))),
        "majority_rate": max(dist.values()) / len(rows),
        "derived_from": None if not suffix else "P0c_%s.jsonl" % name,
        "row_ids": [rid for _, _, rid in items],
    }


def main():
    meta = {"builder": "results/poc/P0c_build.py", "built": BUILT, "files": {}, "notes": {}}
    for name, (items, note), src in (("ynat100", build_ynat(), YNAT_SRC),
                                     ("massive_scenario18_100", build_scenario(), MASSIVE_SRC)):
        meta["notes"][name] = note
        for suffix in VARIANTS:
            entry = write(name, suffix, items, src, note)
            meta["files"][Path(entry["path"]).name] = entry
            print("%-45s n=%d sha256=%s questions_sha256=%s majority=%.2f"
                  % (Path(entry["path"]).name, entry["n"], entry["sha256"][:12], entry["questions_sha256"][:12],
                     entry["majority_rate"]))
        print(name, json.dumps(note, ensure_ascii=False))
    (OUT / "P0c_build_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
