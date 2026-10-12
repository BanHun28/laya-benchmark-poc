"""PART 1.2 check: is the laya-multilingual tokenizer the mmBERT-base (Gemma 2) tokenizer?

    source env.sh && .venv/bin/python results/korean_support/part1b_tokenizer_origin.py

Downloads jhu-clsp/mmBERT-base tokenizer files into the HF cache (not the project), compares the
BPE model with models/laya-multilingual/tokenizer, and encodes the 300 MASSIVE ko utterances of
part2_massive_pairs.jsonl with both. Writes part1b_tokenizer_origin.json.
"""
import json
import os
from pathlib import Path

from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REPO, REV = "jhu-clsp/mmBERT-base", "c5955035435e2bf121cde7f3c8863ef52ff35d82"


def main():
    paths = [hf_hub_download(REPO, f, revision=REV) for f in ("tokenizer.json", "tokenizer_config.json",
                                                             "special_tokens_map.json")]
    mm_dir = os.path.dirname(paths[0])
    a = json.load(open(paths[0], encoding="utf-8"))
    b = json.load(open(ROOT / "models/laya-multilingual/tokenizer/tokenizer.json", encoding="utf-8"))
    pairs = lambda ms: [tuple(m.split(" ", 1)) if isinstance(m, str) else tuple(m) for m in ms]  # noqa: E731
    ta, tb = AutoTokenizer.from_pretrained(mm_dir), AutoTokenizer.from_pretrained(str(ROOT / "models/laya-multilingual/tokenizer"))
    texts = [json.loads(l)["ko"] for l in open(OUT / "part2_massive_pairs.jsonl", encoding="utf-8")]
    same = sum(ta(t, add_special_tokens=False)["input_ids"] == tb(t, add_special_tokens=False)["input_ids"] for t in texts)
    res = {"mmbert_repo": REPO, "mmbert_revision": REV,
           "vocab_equal": a["model"]["vocab"] == b["model"]["vocab"], "vocab_size": len(b["model"]["vocab"]),
           "merges_equal": pairs(a["model"]["merges"]) == pairs(b["model"]["merges"]),
           "n_merges": len(b["model"]["merges"]),
           "byte_fallback": [a["model"].get("byte_fallback"), b["model"].get("byte_fallback")],
           "normalizer_equal": a.get("normalizer") == b.get("normalizer"), "normalizer": b.get("normalizer"),
           "pre_tokenizer": {"mmbert": a.get("pre_tokenizer"), "laya": b.get("pre_tokenizer")},
           "added_tokens_equal": [x["content"] for x in a["added_tokens"]] == [x["content"] for x in b["added_tokens"]],
           "identical_ids_on_massive_ko": "%d/%d" % (same, len(texts))}
    (OUT / "part1b_tokenizer_origin.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
