"""PART 2 of the Korean-support audit: tokenizer efficiency, tokenizer only (no model forward).

    source env.sh && .venv/bin/python results/korean_support/part2_tokenizer.py

Writes results/korean_support/part2_tokenizer_stats.json and part2_massive_pairs.jsonl.

Tokenizers are loaded exactly as `laya.agent` loads them (AutoTokenizer.from_pretrained(<ckpt>/tokenizer)).
Token categories (per token, from `convert_ids_to_tokens`):
  hangul_full   decodes to text holding >= 1 complete Hangul syllable (U+AC00-U+D7A3)
  byte_fallback multilingual `<0xNN>` token (a character missing from the 256k vocab, spelled as UTF-8 bytes)
  byte_piece    english ByteLevel token whose bytes are not valid UTF-8 on their own (splits a character)
  jamo          decodes to Hangul jamo only (no complete syllable)
  han           CJK ideographs, no Hangul
  space         whitespace / metaspace only
  other         Latin, digits, punctuation, emoji ...
"fragment" = byte_fallback + byte_piece + jamo (tokens below syllable level).
"""
import json
import re
import statistics
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import datasets
import tokenizers
import transformers
from datasets import load_dataset
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "results" / "poc"))
from P0c_build import build_ynat  # noqa: E402  (reuse the P0c loader: same 100 headlines)

from laya.agent import Agent  # noqa: E402  (static `_to_internal` only; no checkpoint is loaded)
from laya.common import build_sequence, encode_text, serialize_state, state_room  # noqa: E402

MASSIVE = {"dataset": "mteb/amazon_massive_intent", "split": "test",
           "revision": "940fd47a81eaa7f2cc7b129674d945d618ac38c2"}
N_PAIRS = 300
TOK_DIRS = {"multilingual": ROOT / "models/laya-multilingual/tokenizer",
            "english": ROOT / "models/laya/tokenizer"}
CKPT_CFG = {"multilingual": ROOT / "models/laya-multilingual/rl_agent_config.json",
            "english": ROOT / "models/laya/rl_agent_config.json"}

BYTE_TOKEN = re.compile(r"<0x[0-9A-Fa-f]{2}>")


def _bytes_to_unicode():
    # GPT-2 / ByteLevel table: byte -> printable unicode char used in the vocab strings.
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return {chr(c): b for b, c in zip(bs, cs)}


BYTELEVEL_DECODE = _bytes_to_unicode()


def is_syllable(ch):
    return 0xAC00 <= ord(ch) <= 0xD7A3


def is_jamo(ch):
    cp = ord(ch)
    return 0x1100 <= cp <= 0x11FF or 0x3130 <= cp <= 0x318F or 0xA960 <= cp <= 0xA97F or 0xD7B0 <= cp <= 0xD7FF


def is_han(ch):
    cp = ord(ch)
    return 0x3400 <= cp <= 0x4DBF or 0x4E00 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF


def token_text(kind, tok_str):
    """Decoded text of one vocab token, or None when the token is a sub-character byte piece."""
    if kind == "multilingual":
        if BYTE_TOKEN.fullmatch(tok_str):
            return None
        return tok_str.replace("▁", " ")
    raw = bytes(BYTELEVEL_DECODE[c] for c in tok_str) if all(c in BYTELEVEL_DECODE for c in tok_str) else tok_str.encode()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def categorise(kind, tok_str):
    text = token_text(kind, tok_str)
    if text is None:
        return "byte_fallback" if kind == "multilingual" else "byte_piece"
    if any(is_syllable(c) for c in text):
        return "hangul_full"
    if any(is_jamo(c) for c in text):
        return "jamo"
    if any(is_han(c) for c in text):
        return "han"
    if not text.strip():
        return "space"
    return "other"


def measure(tok, kind, text):
    ids = encode_text(tok, text, add_special_tokens=False)["input_ids"]
    toks = tok.convert_ids_to_tokens(ids)
    cats = Counter(categorise(kind, t) for t in toks)
    syll = [c for c in text if is_syllable(c)]
    row = {
        "tokens": len(ids),
        "chars": len(text),
        "chars_nospace": sum(1 for c in text if not c.isspace()),
        "words": len(text.split()),
        "hangul_syllables": len(syll),
        "unk": sum(1 for i in ids if i == tok.unk_token_id),
        "cats": dict(cats),
    }
    if kind == "multilingual":
        vocab = tok.get_vocab()
        # A character missing from the vocab cannot take part in any merge, so it is exactly the set
        # the BPE model spells as `<0xNN>` bytes.
        row["byte_fallback_syllables"] = sum(1 for c in syll if c not in vocab)
        row["byte_fallback_syllable_types"] = sorted({c for c in syll if c not in vocab})
    return row, toks


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def aggregate(rows):
    tot = Counter()
    cats = Counter()
    for r in rows:
        for k in ("tokens", "chars", "chars_nospace", "words", "hangul_syllables", "unk",
                  "byte_fallback_syllables"):
            tot[k] += r.get(k, 0)
        cats.update(r["cats"])
    frag = cats["byte_fallback"] + cats["byte_piece"] + cats["jamo"]
    hangul_tokens = cats["hangul_full"] + frag
    out = {
        "n": len(rows),
        "sum_tokens": tot["tokens"], "sum_chars": tot["chars"], "sum_chars_nospace": tot["chars_nospace"],
        "sum_words": tot["words"], "sum_hangul_syllables": tot["hangul_syllables"],
        "tokens_per_char": tot["tokens"] / tot["chars"],
        "tokens_per_char_nospace": tot["tokens"] / tot["chars_nospace"],
        "tokens_per_word": tot["tokens"] / tot["words"],
        "median_tokens_per_char": statistics.median(r["tokens"] / r["chars"] for r in rows),
        "median_tokens_per_word": statistics.median(r["tokens"] / r["words"] for r in rows),
        "median_tokens": statistics.median(r["tokens"] for r in rows),
        "categories": dict(sorted(cats.items())),
        "category_share": {k: v / tot["tokens"] for k, v in sorted(cats.items())},
        "fragment_tokens": frag,
        "fragment_share_of_all_tokens": frag / tot["tokens"],
        "fragment_share_of_hangul_tokens": (frag / hangul_tokens) if hangul_tokens else None,
        # literal reading of the brief: every token that is not >= 1 full syllable
        "not_full_syllable_share_of_all_tokens": 1 - cats["hangul_full"] / tot["tokens"],
        "unk_tokens": tot["unk"], "unk_rate": tot["unk"] / tot["tokens"],
        "tokens_per_hangul_syllable": (tot["tokens"] / tot["hangul_syllables"]) if tot["hangul_syllables"] else None,
        "hangul_syllables_per_hangul_full_token": (tot["hangul_syllables"] / cats["hangul_full"]) if cats["hangul_full"] else None,
    }
    if any("byte_fallback_syllables" in r for r in rows):
        out["byte_fallback_syllables"] = tot["byte_fallback_syllables"]
        out["byte_fallback_syllable_share"] = (tot["byte_fallback_syllables"] / tot["hangul_syllables"]
                                               if tot["hangul_syllables"] else None)
        out["byte_fallback_syllable_types"] = sorted({c for r in rows for c in r.get("byte_fallback_syllable_types", [])})
    return out


def vocab_profile(tok, kind):
    """How much Korean the vocab holds at all (decoded, so ByteLevel entries are read as bytes)."""
    full, single, multi, jamo = 0, set(), 0, 0
    for s in tok.get_vocab():
        text = token_text(kind, s)
        if text is None:
            continue
        body = text.strip()
        if any(is_syllable(c) for c in body):
            full += 1
            if len(body) == 1:
                single.add(body)
            elif all(is_syllable(c) for c in body):
                multi += 1
        elif body and all(is_jamo(c) for c in body):
            jamo += 1
    return {"entries_with_full_syllable": full, "distinct_single_syllables": len(single),
            "multi_syllable_pure_hangul_entries": multi, "jamo_only_entries": jamo,
            "vocab_size": len(tok.get_vocab())}


def syllable_coverage(tok, kind):
    """Which precomposed syllables are one vocab entry: all 11,172, and the 2,350 of KS X 1001 (EUC-KR)."""
    vocab = tok.get_vocab()
    inv = {v: k for k, v in BYTELEVEL_DECODE.items()}

    def single(s):
        if kind == "multilingual":
            return s in vocab
        return "".join(inv[b] for b in s.encode("utf-8")) in vocab

    allsyl = [chr(c) for c in range(0xAC00, 0xD7A4)]
    # KS X 1001 syllables are the 2-byte EUC-KR code points; CPython spells the other 8,822 as
    # 8-byte jamo composition sequences, so the length is what separates the two.
    ksx = [s for s in allsyl if len(s.encode("euc-kr")) == 2]
    miss = [s for s in ksx if not single(s)]
    return {"all_11172_single_token": sum(map(single, allsyl)), "ksx1001_total": len(ksx),
            "ksx1001_single_token": len(ksx) - len(miss), "ksx1001_single_token_share": 1 - len(miss) / len(ksx),
            "ksx1001_missing_examples": "".join(miss[:60])}


def load_massive_pairs():
    ko = load_dataset(MASSIVE["dataset"], "ko", split=MASSIVE["split"], revision=MASSIVE["revision"])
    en = load_dataset(MASSIVE["dataset"], "en", split=MASSIVE["split"], revision=MASSIVE["revision"])
    en_by_id = {r["id"]: r for r in en}
    pairs = []
    for r in ko.select(range(N_PAIRS)):
        e = en_by_id[r["id"]]
        assert e["id"] == r["id"] and e["label_text"] == r["label_text"], (r, e)
        pairs.append({"id": r["id"], "label_text": r["label_text"], "ko": r["text"], "en": e["text"]})
    return pairs


def load_p0():
    rows = []
    for line in (ROOT / "results/poc/P0_probe_sentences.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            rows.append(json.loads(line)["state"]["message"])
    assert len(rows) == 30, len(rows)
    return rows


def load_ynat():
    items, _ = build_ynat()
    heads = [state["headline"] for state, _, _ in items]
    frozen = [json.loads(l)["state"]["headline"] for l in
              (ROOT / "results/poc/P0c_ynat100.jsonl").read_text(encoding="utf-8").splitlines()
              if l.strip() and not l.startswith("#")]
    assert heads == frozen, "P0c loader no longer reproduces P0c_ynat100.jsonl"
    return heads


def budget(toks):
    """Token budget for the P0 7-question call, from laya's own sequence builder (tokenizer only)."""
    schema = {}
    for name in ("triage_v1.json", "gateway_v1.json"):
        schema.update(json.loads((ROOT / "poc/schema" / name).read_text(encoding="utf-8"))["questions"])
    msgs = {"P0_long": "지난달 요금이 두 번 결제됐어요. 오늘 안에 환불 안 되면 해지하겠습니다.",
            "P0_short": "지난달 요금이 두 번 결제됐어요."}
    out = {"questions": list(schema)}
    for kind, tok in toks.items():
        cfg = json.loads(CKPT_CFG[kind].read_text())
        max_len, head_max_len = cfg["max_len"], cfg["head_max_len"]
        internal = {qid: Agent._to_internal(q) for qid, q in schema.items()}
        rooms = {qid: state_room(tok, q, max_len, head_max_len) for qid, q in internal.items()}
        res = {"max_len": max_len, "head_max_len": head_max_len, "state_room_per_question": rooms,
               "binding_room": min(rooms.values()), "binding_question": min(rooms, key=rooms.get)}
        for label, msg in msgs.items():
            state = {"message": msg}
            sids = encode_text(tok, serialize_state(state), add_special_tokens=False)["input_ids"]
            seqs = [build_sequence(tok, state, internal[q], max_len, head_max_len, state_ids=sids)[0] for q in schema]
            bare = len(encode_text(tok, msg, add_special_tokens=False)["input_ids"])
            res[label] = {"chars": len(msg), "state_tokens": len(sids), "message_only_tokens": bare,
                          "json_wrapper_tokens": len(sids) - bare,
                          "input_tokens_7q": sum(len(s) for s in seqs)}
        out[kind] = res
    return out


def main():
    toks = {k: AutoTokenizer.from_pretrained(str(d)) for k, d in TOK_DIRS.items()}
    pairs = load_massive_pairs()
    sets = {"massive_ko": [p["ko"] for p in pairs], "massive_en": [p["en"] for p in pairs],
            "p0_probe_ko": load_p0(), "klue_ynat_ko": load_ynat()}

    per = {}  # (tokenizer, set) -> rows
    samples = {}
    for kind, tok in toks.items():
        for name, texts in sets.items():
            rows = []
            for t in texts:
                r, tk = measure(tok, kind, t)
                rows.append(r)
            per[(kind, name)] = rows
            samples["%s/%s" % (kind, name)] = [{"text": texts[i], "tokens": measure(tok, kind, texts[i])[1]}
                                               for i in range(3)]

    stats = {"sources": {"massive": dict(MASSIVE, n_pairs=N_PAIRS, configs=["ko", "en"], join="id",
                                         selection="first 300 ko test rows in file order"),
                         "p0_probe": "results/poc/P0_probe_sentences.jsonl state.message (n=30)",
                         "klue_ynat": "results/poc/P0c_build.py build_ynat() (n=100), asserted equal to P0c_ynat100.jsonl"},
             "versions": {"transformers": transformers.__version__, "tokenizers": tokenizers.__version__,
                          "datasets": datasets.__version__},
             "tokenizers": {k: {"dir": str(d.relative_to(ROOT)), "class": type(toks[k]).__name__,
                                "vocab": vocab_profile(toks[k], k),
                                "syllable_coverage": syllable_coverage(toks[k], k)} for k, d in TOK_DIRS.items()},
             "aggregate": {"%s/%s" % key: aggregate(rows) for key, rows in per.items()}}

    # parallel pairs: same tokenizer on both sides, and the routed pairing (ko->multilingual, en->english)
    pair_stats = {}
    for label, ko_kind, en_kind in (("multilingual_ko_vs_multilingual_en", "multilingual", "multilingual"),
                                    ("english_ko_vs_english_en", "english", "english"),
                                    ("routed_multilingual_ko_vs_english_en", "multilingual", "english")):
        ratios = [k["tokens"] / e["tokens"] for k, e in zip(per[(ko_kind, "massive_ko")], per[(en_kind, "massive_en")])]
        pair_stats[label] = {"median": statistics.median(ratios), "p10": pct(ratios, 0.10), "p90": pct(ratios, 0.90),
                             "mean": statistics.fmean(ratios), "min": min(ratios), "max": max(ratios),
                             "sum_ratio": sum(k["tokens"] for k in per[(ko_kind, "massive_ko")]) /
                                          sum(e["tokens"] for e in per[(en_kind, "massive_en")])}
    stats["massive_pair_token_ratio_ko_over_en"] = pair_stats

    # NFD robustness: the Gemma tokenizer has no NFC normalizer (Replace " " -> "▁" only), ModernBERT's is NFC.
    nfd = {}
    for kind, tok in toks.items():
        rows = [measure(tok, kind, unicodedata.normalize("NFD", t))[0] for t in sets["massive_ko"]]
        a = aggregate(rows)
        base = stats["aggregate"]["%s/massive_ko" % kind]
        nfd[kind] = {"sum_tokens_nfd": a["sum_tokens"], "sum_tokens_nfc": base["sum_tokens"],
                     "inflation": a["sum_tokens"] / base["sum_tokens"], "categories_nfd": a["categories"],
                     "unk_rate_nfd": a["unk_rate"]}
    stats["nfd_input_massive_ko"] = nfd
    stats["normalizers"] = {k: json.loads(t.backend_tokenizer.to_str())["normalizer"] for k, t in toks.items()}

    b = budget(toks)
    agg = stats["aggregate"]
    est = {}
    for kind, sets_ in (("multilingual", ("massive_ko", "p0_probe_ko", "klue_ynat_ko", "massive_en")),
                        ("english", ("massive_ko", "massive_en"))):
        wrapper = b[kind]["P0_long"]["json_wrapper_tokens"]
        for limit in ((b[kind]["max_len"], 8192) if kind == "multilingual" else (b[kind]["max_len"],)):
            room = b[kind]["binding_room"] + (limit - b[kind]["max_len"])
            for s in sets_:
                tpc = agg["%s/%s" % (kind, s)]["tokens_per_char"]
                est["%s/max_len=%d/%s" % (kind, limit, s)] = {
                    "binding_room_tokens": room, "tokens_per_char": tpc,
                    "chars_that_fit": int((room - wrapper) / tpc)}
        p0 = b[kind]["P0_long"]
        est["%s/max_len=%d/P0_message_rate" % (kind, b[kind]["max_len"])] = {
            "binding_room_tokens": b[kind]["binding_room"],
            "tokens_per_char": p0["message_only_tokens"] / p0["chars"],
            "chars_that_fit": int((b[kind]["binding_room"] - p0["json_wrapper_tokens"]) * p0["chars"] / p0["message_only_tokens"])}
    b["chars_that_fit"] = est
    stats["budget_p0_7_questions"] = b

    # How much text one "letter" stands for: Hangul syllables vs English letters for the same MASSIVE utterance.
    ko_syl = sum(sum(1 for c in p["ko"] if is_syllable(c)) for p in pairs)
    en_let = sum(sum(1 for c in p["en"] if c.isalpha()) for p in pairs)
    stats["letters_per_meaning_massive"] = {"ko_hangul_syllables": ko_syl, "en_letters": en_let,
                                            "en_letters_per_ko_syllable": en_let / ko_syl}
    stats["token_samples"] = samples

    with open(OUT / "part2_massive_pairs.jsonl", "w", encoding="utf-8") as f:
        for p, mk, me, ek, ee in zip(pairs, per[("multilingual", "massive_ko")], per[("multilingual", "massive_en")],
                                     per[("english", "massive_ko")], per[("english", "massive_en")]):
            f.write(json.dumps({"id": p["id"], "label_text": p["label_text"], "ko": p["ko"], "en": p["en"],
                                "ml_ko": mk["tokens"], "ml_en": me["tokens"], "en_ko": ek["tokens"], "en_en": ee["tokens"],
                                "ko_chars": mk["chars"], "en_chars": me["chars"], "ko_words": mk["words"],
                                "en_words": me["words"]}, ensure_ascii=False) + "\n")
    (OUT / "part2_tokenizer_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    hdr = "%-34s %6s %7s %7s %7s %7s %7s %6s" % ("tokenizer/set", "n", "tok/ch", "tok/ch*", "tok/wd", "frag%", "tok/syl", "unk")
    print(hdr)
    for key, a in stats["aggregate"].items():
        print("%-34s %6d %7.3f %7.3f %7.3f %7.2f %7s %6d" % (
            key, a["n"], a["tokens_per_char"], a["tokens_per_char_nospace"], a["tokens_per_word"],
            100 * a["fragment_share_of_all_tokens"],
            "%.3f" % a["tokens_per_hangul_syllable"] if a["tokens_per_hangul_syllable"] else "-", a["unk_tokens"]))
    print(json.dumps(pair_stats, indent=1))
    print(json.dumps(nfd, ensure_ascii=False, indent=1))
    print(json.dumps(stats["budget_p0_7_questions"], ensure_ascii=False, indent=1))
    print(json.dumps(stats["tokenizers"], indent=1))


if __name__ == "__main__":
    main()
