"""PART 1 of the Korean-support audit: documentary evidence (no model, no tokenizer).

    source env.sh && bash results/korean_support/fetch_cards.sh      # raw cards/papers -> cards/
    .venv/bin/python results/korean_support/part1_docs_evidence.py   # -> part1_docs_evidence.json

Reads only fetched files under results/korean_support/cards/, the local checkpoints under models/,
and the upstream checkout third_party/laya (@4aa6761).
"""
import json
import re
import statistics
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import laya.lang as lang

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CARDS = OUT / "cards"
UP = ROOT / "third_party/laya"
KO_LINE = re.compile(r"korean|hangul|한국|\bko\b|\bkor\b|[가-힣]", re.I)


def card_facts(repo):
    d = CARDS / repo.replace("/", "_")
    api = json.loads((d / "api_model_full.json").read_text())
    langs = (api.get("cardData") or {}).get("language")
    readme = (d / "README.md").read_text(encoding="utf-8").splitlines()
    end = next((i for i, l in enumerate(readme[1:], 2) if l.strip() == "---"), 0)  # front matter end (1-based)
    hits = [(i, l.strip()) for i, l in enumerate(readme, 1) if i > end and KO_LINE.search(l)]
    return {"sha": api.get("sha"), "lastModified": api.get("lastModified"),
            "n_tags": len(api.get("tags", [])), "ko_in_tags": "ko" in api.get("tags", []) or "kor" in api.get("tags", []),
            "cardData_language_n": len(langs) if isinstance(langs, list) else langs,
            "ko_in_cardData_language": isinstance(langs, list) and ("ko" in langs or "kor" in langs),
            "front_matter_lines": end, "korean_lines_in_body": hits}


def html_to_text(src):
    class P(HTMLParser):
        def __init__(self):
            super().__init__()
            self.out, self.skip = [], 0

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style", "math"):
                self.skip += 1
            if tag in ("p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "section", "table", "figcaption", "br"):
                self.out.append("\n")
            if tag in ("td", "th"):
                self.out.append(" | ")

        def handle_endtag(self, tag):
            if tag in ("script", "style", "math"):
                self.skip -= 1

        def handle_data(self, data):
            if not self.skip:
                self.out.append(data)

    p = P()
    p.feed(src)
    txt = re.sub(r"[ \t]+", " ", "".join(p.out))
    return re.sub(r"\n\s*\n+", "\n", txt)


def mmbert_paper():
    pdir = CARDS / "mmbert_paper"
    txt = html_to_text((pdir / "arxiv_html_2509.06888.html").read_text(encoding="utf-8"))
    (pdir / "arxiv_html_2509.06888.txt").write_text(txt, encoding="utf-8")
    lines = txt.split("\n")
    start = next(i for i, l in enumerate(lines) if l.strip() == "Appendix D Language Distributions")
    cells = []
    for l in lines[start:]:
        if l.startswith("Table 9"):
            break
        if l.strip().startswith("|"):
            cells.append(l.strip()[1:].strip())
    first = cells.index("eng")
    rows = [cells[first + i:first + i + 12] for i in range(0, len(cells) - first, 12)]
    rows = [r for r in rows if len(r) == 12 and r[0] not in ("Total",)]
    cols = ["pretrain_B", "pretrain_pct", "mid_B", "mid_pct", "decay_eng_B", "decay_eng_pct",
            "decay_cont_B", "decay_cont_pct", "decay_all_B", "decay_all_pct", "total_B"]
    table = {r[0]: dict(zip(cols, r[1:])) for r in rows}
    langs_only = [k for k in table if k != "code"]
    by_pre = sorted(langs_only, key=lambda k: -float(table[k]["pretrain_B"]))
    by_tot = sorted(langs_only, key=lambda k: -float(table[k]["total_B"]))
    quotes = [l.strip() for l in lines if re.search(r"Gemma 2 tokenizer|just 60 languages|set of 60 languages|"
                                                       r"20 langauges from FineWeb2|We start with a set of 60", l)]
    return {"table9_rows": len(rows), "kor": table.get("kor"),
            "kor_rank_by_pretrain_tokens": by_pre.index("kor") + 1,
            "kor_rank_by_total_tokens": by_tot.index("kor") + 1, "languages_in_table9": len(langs_only),
            "top15_by_pretrain": by_pre[:15], "quotes": quotes,
            "korean_mentions_in_text": [l.strip()[:200] for l in lines if re.search(r"korean", l, re.I)]}


def benchmarks_table():
    rows = {}
    for l in (UP / "BENCHMARKS.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| `([a-zA-Z-]+)` \| ([0-9.]+) \| ([0-9.]+) \| ([+-][0-9.]+) \| ([0-9.]+) \| ([0-9.]+) \|", l)
        if m:
            rows[m.group(1)] = {"laya": float(m.group(2)), "ml": float(m.group(3)), "delta": float(m.group(4)),
                                "laya_ece": float(m.group(5)), "ml_ece": float(m.group(6))}
    assert len(rows) == 51, len(rows)
    ko, en = rows["ko"], rows["en"]
    api = json.loads((CARDS / "convaiinnovations_laya-multilingual/api_model_full.json").read_text())
    card_codes = set(api["cardData"]["language"]) - {"multilingual"}
    massive_codes = {c.split("-")[0] for c in rows}

    def rank(key, value, higher_better):
        better = sum(1 for r in rows.values() if (r[key] > value if higher_better else r[key] < value))
        ties = sum(1 for r in rows.values() if r[key] == value) - 1
        return {"rank": better + 1, "ties_with": ties, "of": len(rows)}

    vals = lambda k: [r[k] for r in rows.values()]  # noqa: E731
    non_en = [r for c, r in rows.items() if c != "en"]
    return {
        "ko": ko, "en": en,
        "ko_rank_ml_accuracy": rank("ml", ko["ml"], True),
        "ko_rank_ml_ece_lower_better": rank("ml_ece", ko["ml_ece"], False),
        "ko_rank_delta": rank("delta", ko["delta"], True),
        "ml_accuracy_median": statistics.median(vals("ml")), "ml_accuracy_macro": statistics.fmean(vals("ml")),
        "ml_ece_median": statistics.median(vals("ml_ece")), "ml_ece_macro": statistics.fmean(vals("ml_ece")),
        "ml_accuracy_macro_non_en": statistics.fmean(r["ml"] for r in non_en),
        "ko_over_en_ml_accuracy": ko["ml"] / en["ml"],
        "ko_over_en_english_checkpoint_on_en": ko["ml"] / en["laya"],
        "random_baseline": 0.05, "ko_over_random": ko["ml"] / 0.05,
        "cases_per_language": 100,
        "ko_95ci_wilson": wilson(round(ko["ml"] * 100), 100),
        "cjk_neighbours": {c: rows[c] for c in ("ja", "zh-CN", "zh-TW")},
        # Is the multilingual card's `language:` list just the MASSIVE evaluation set?
        "card_language_codes_vs_massive": {"card": len(card_codes), "massive_51_locales_as_codes": len(massive_codes),
                                           "card_minus_massive": sorted(card_codes - massive_codes),
                                           "massive_minus_card": sorted(massive_codes - card_codes)},
    }


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return [round(centre - half, 3), round(centre + half, 3)]


def korean_numbers_provenance():
    t4 = json.loads((UP / "research/results/t4_colab_benchmark.json").read_text())
    cpu = json.loads((UP / "research/results/cpu_51_language_sweep.json").read_text())
    ref = json.loads((UP / "research/results/cpu_51_language_sweep_refreshed.json").read_text())
    out = {}
    for suite in ("massive_intent.ko", "massive_scenario.ko"):
        s = t4["suites"][suite]
        out["t4_" + suite] = {m: {k: s[m]["calibrated"][k] for k in ("n", "accuracy", "ece", "mean_confidence")}
                              for m in ("laya", "laya-multilingual")}
    out["cpu_committed_laya0.2.0"] = {m: cpu["part_a"]["by_model"][m]["per_language"]["ko"] for m in ("english", "multilingual")}
    out["cpu_refreshed_laya0.3.20"] = {m: ref["by_model"][m]["per_language"]["ko"]["refreshed_clamped"]
                                       for m in ("english", "multilingual")}
    out["calibration_repair_ko"] = {m: t4["calibration_repair"][m]["per_suite"]["massive_intent.ko"]
                                    for m in ("laya", "laya-multilingual")}
    return out


def upstream_grep():
    cmd = ["grep", "-rn", "-I", "-i", "-E", r"korean|hangul|한국|[가-힣]", "--exclude-dir=.git", "."]
    res = subprocess.run(cmd, cwd=UP, capture_output=True, text=True)
    hits = [l for l in res.stdout.splitlines()]
    by_file = {}
    for h in hits:
        f = h.split(":", 1)[0]
        by_file.setdefault(f, 0)
        by_file[f] += 1
    code_ko = subprocess.run(["grep", "-rn", "-E", r"`ko`|\"ko\"|'ko'|\bko\b", "BENCHMARKS.md", "README.md", "docs",
                              "research/README.md", "research/eval/README.md", "research/evals/README.md"],
                             cwd=UP, capture_output=True, text=True).stdout.splitlines()
    return {"files_with_korean_or_hangul": by_file, "ko_code_lines_in_docs": code_ko,
            "lang_bench_dirs": sorted(p.name for p in (UP / "research/benchmarks").iterdir() if p.is_dir()),
            "research_evals_files": sorted(p.name for p in (UP / "research/evals").iterdir() if p.is_file())}


def encoder_facts():
    out = {}
    for name in ("laya-multilingual", "laya", "laya-typed-decisions"):
        cfg = json.loads((ROOT / "models" / name / "encoder/config.json").read_text())
        rl = json.loads((ROOT / "models" / name / "rl_agent_config.json").read_text())
        out[name] = {"model_type": cfg["model_type"], "_name_or_path": cfg.get("_name_or_path"),
                     "architectures": cfg.get("architectures"), "vocab_size": cfg["vocab_size"],
                     "max_position_embeddings": cfg["max_position_embeddings"], "hidden_size": cfg["hidden_size"],
                     "num_hidden_layers": cfg["num_hidden_layers"], "rl_encoder": rl["encoder"],
                     "max_len": rl["max_len"], "head_max_len": rl["head_max_len"], "temperature": rl.get("temperature"),
                     "training": rl.get("training")}
    blobs = json.loads((CARDS / "convaiinnovations_laya-multilingual/api_model_blobs.json").read_text())
    bundle = json.loads((CARDS / "convaiinnovations_laya/api_model_blobs_55cf4c4.json").read_text())
    sha = lambda d, f: next(((s.get("lfs") or {}).get("sha256") or s.get("blobId")  # noqa: E731
                             for s in d["siblings"] if s["rfilename"] == f), None)
    out["standalone_vs_bundle_multilingual"] = {
        f: {"standalone": sha(blobs, f), "bundle_55cf4c4": sha(bundle, "multilingual/" + f),
            "identical": sha(blobs, f) == sha(bundle, "multilingual/" + f)}
        for f in ("model.safetensors", "tokenizer/tokenizer.json", "encoder/config.json", "rl_agent_config.json",
                  "tokenizer/tokenizer_config.json")}
    return out


def fineweb2_hq():
    api = json.loads((CARDS / "epfml__FineWeb2-HQ/api_dataset.json").read_text())
    langs = (api.get("cardData") or {}).get("language")
    return {"sha": api.get("sha"), "languages": langs, "ko_included": "ko" in (langs or [])}


def lang_py_coverage():
    return {"stopword_languages": sorted(lang._STOP), "script_ranges": [n for n, _ in lang._SCRIPT_RANGES],
            "hangul_ranges": [[hex(a), hex(b)] for a, b in dict(lang._SCRIPT_RANGES)["hangul"]],
            "NON_LATIN_FRACTION": lang.NON_LATIN_FRACTION, "NON_LATIN_MIN_FRACTION": lang.NON_LATIN_MIN_FRACTION,
            "NON_LATIN_MIN_LETTERS": lang.NON_LATIN_MIN_LETTERS}


def main():
    ev = {
        "cards": {r: card_facts(r) for r in ("convaiinnovations/laya-multilingual", "convaiinnovations/laya",
                                             "convaiinnovations/laya-typed-decisions", "jhu-clsp/mmBERT-base")},
        "encoders": encoder_facts(),
        "mmbert_paper": mmbert_paper(),
        "fineweb2_hq": fineweb2_hq(),
        "benchmarks_51": benchmarks_table(),
        "korean_numbers_provenance": korean_numbers_provenance(),
        "upstream_grep": upstream_grep(),
        "lang_py": lang_py_coverage(),
    }
    (OUT / "part1_docs_evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for r, c in ev["cards"].items():
        print(r, {k: v for k, v in c.items() if k != "korean_lines_in_body"})
        for i, l in c["korean_lines_in_body"]:
            print("   L%d: %s" % (i, l[:160]))
    print(json.dumps({k: ev[k] for k in ("encoders", "fineweb2_hq", "benchmarks_51", "lang_py")}, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in ev["mmbert_paper"].items() if k != "quotes"}, ensure_ascii=False, indent=1))
    for q in ev["mmbert_paper"]["quotes"]:
        print("  Q:", q[:300])
    print(json.dumps(ev["korean_numbers_provenance"], indent=1))
    print(json.dumps(ev["upstream_grep"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
