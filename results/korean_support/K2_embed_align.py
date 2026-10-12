"""E3 cross-lingual alignment indicator (throwaway). Mean-pooled encoder embeddings from
laya.embed_fn_from_agent (the helper upstream offers for shortlisting) on the 100 MASSIVE ko
utterances and their 100 en twins; cosine matrix, retrieval P@1/P@5 both directions, mean cosine of
true vs random pairs. mmBERT/ModernBERT encoders are not trained as sentence embedders, so this is an
alignment indicator, not a retrieval benchmark.

    source env.sh && .venv/bin/python results/korean_support/K2_embed_align.py > results/korean_support/K2_E3_embed_align.log 2>&1
"""
import json
import time
import warnings
from pathlib import Path

import numpy as np
import torch

torch.set_num_threads(10)
torch.set_num_interop_threads(1)

import laya  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CKPTS = {"multilingual": ROOT / "models/laya-multilingual", "english": ROOT / "models/laya"}


def rows(name):
    return [json.loads(l) for l in (HERE / name).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def retrieval(S, accept):
    """S[q, c] similarity; accept[q] = set of candidate indices counted as a hit. Ties keep the lower index."""
    order = np.argsort(-S, axis=1, kind="stable")
    p1 = float(np.mean([order[q, 0] in accept[q] for q in range(len(S))]))
    p5 = float(np.mean([bool(set(order[q, :5]) & accept[q]) for q in range(len(S))]))
    rank = [int(min(np.where(np.isin(order[q], list(accept[q])))[0])) + 1 for q in range(len(S))]
    return {"p_at_1": p1, "p_at_5": p5, "median_rank": float(np.median(rank)), "top1": order[:, 0].tolist()}


def main():
    ko, en = rows("K2_scen18_kodesc_ko.jsonl"), rows("K2_scen18_kodesc_en.jsonl")
    ids = [r["tags"][-1] for r in ko]
    assert ids == [r["tags"][-1] for r in en] and all(i.startswith("id:") for i in ids)
    ko_txt = [r["state"]["utterance"] for r in ko]
    en_txt = [r["state"]["utterance"] for r in en]
    n = len(ko_txt)
    strict = [{q} for q in range(n)]
    # the first 100 ko rows hold 3 exact-duplicate pairs (distinct en twins): accept any twin of the same ko text
    dup = [{j for j in range(n) if ko_txt[j] == ko_txt[q]} for q in range(n)]
    out = {"n": n, "texts": "state.utterance of results/korean_support/K2_scen18_kodesc_{ko,en}.jsonl (MASSIVE ko test first 100 + en twins)",
           "embed_fn": "laya.embed_fn_from_agent(agent) defaults: max_length=512, batch_size=32, mean pool over non-pad tokens",
           "torch_threads": [torch.get_num_threads(), torch.get_num_interop_threads()],
           "duplicate_ko_queries": sum(len(d) > 1 for d in dup), "by_checkpoint": {}}
    for name, path in CKPTS.items():
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            t0 = time.time()
            agent = laya.load(str(path), device="cpu")
            load_s = time.time() - t0
        embed = laya.embed_fn_from_agent(agent)
        t0 = time.time()
        Ek, Ee = embed(ko_txt), embed(en_txt)
        embed_s = time.time() - t0
        assert Ek.shape == Ee.shape == (n, Ek.shape[1]) and np.isfinite(Ek).all() and np.isfinite(Ee).all()
        Kn = Ek / np.linalg.norm(Ek, axis=1, keepdims=True)
        En = Ee / np.linalg.norm(Ee, axis=1, keepdims=True)
        S = Kn @ En.T
        off = ~np.eye(n, dtype=bool)
        true_cos, rand_cos = np.diag(S), S[off]
        tok = agent.tok
        unk = tok.unk_token_id
        tok_stats = {}
        for lang, txt in (("ko", ko_txt), ("en", en_txt)):
            ids_ = [tok(t, add_special_tokens=False)["input_ids"] for t in txt]
            tok_stats[lang] = {"mean_tokens": float(np.mean([len(x) for x in ids_])),
                               "unk_share": float(np.mean([np.mean([i == unk for i in x]) if x else 0.0 for x in ids_])) if unk is not None else None}
        res = {"checkpoint_dir": str(path.relative_to(ROOT)), "resolved": str(path.resolve()), "dim": int(Ek.shape[1]),
               "load_s": round(load_s, 2), "embed_s": round(embed_s, 2),
               "warnings": ["%s:%s: %s: %s" % (w.filename, w.lineno, w.category.__name__, w.message) for w in caught],
               "mean_cos_true_pairs": float(true_cos.mean()), "mean_cos_random_pairs": float(rand_cos.mean()),
               "std_cos_random_pairs": float(rand_cos.std()),
               "gap_true_minus_random": float(true_cos.mean() - rand_cos.mean()),
               "gap_in_random_sd": float((true_cos.mean() - rand_cos.mean()) / rand_cos.std()),
               "true_pair_beats_all_its_row_and_column": int(sum((S[q, q] >= S[q, :]).all() and (S[q, q] >= S[:, q]).all() for q in range(n))),
               "mean_cos_ko_ko_offdiag": float((Kn @ Kn.T)[off].mean()), "mean_cos_en_en_offdiag": float((En @ En.T)[off].mean()),
               "tokens": tok_stats,
               "ko_to_en": {"strict": retrieval(S, strict), "dup_aware": retrieval(S, dup)},
               "en_to_ko": {"strict": retrieval(S.T, strict), "dup_aware": retrieval(S.T, dup)}}
        out["by_checkpoint"][name] = res
        del agent
    (HERE / "K2_E3_embed_align.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("| checkpoint | ko→en P@1 strict / dup-aware | ko→en P@5 | en→ko P@1 strict / dup-aware | en→ko P@5 | median rank ko→en / en→ko "
          "| mean cos true | mean cos random (sd) | gap (in random sd) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, r in out["by_checkpoint"].items():
        ke, ek = r["ko_to_en"], r["en_to_ko"]
        print("| %s | %.2f / %.2f | %.2f | %.2f / %.2f | %.2f | %.0f / %.0f | %.3f | %.3f (%.3f) | %.3f (%.1f) |" % (
            name, ke["strict"]["p_at_1"], ke["dup_aware"]["p_at_1"], ke["strict"]["p_at_5"], ek["strict"]["p_at_1"],
            ek["dup_aware"]["p_at_1"], ek["strict"]["p_at_5"], ke["strict"]["median_rank"], ek["strict"]["median_rank"],
            r["mean_cos_true_pairs"], r["mean_cos_random_pairs"], r["std_cos_random_pairs"], r["gap_true_minus_random"], r["gap_in_random_sd"]))
    for name, r in out["by_checkpoint"].items():
        print(name, "dim", r["dim"], "load_s", r["load_s"], "embed_s", r["embed_s"], "tokens", json.dumps(r["tokens"]),
              "ko-ko offdiag %.3f en-en offdiag %.3f" % (r["mean_cos_ko_ko_offdiag"], r["mean_cos_en_en_offdiag"]),
              "P@5 dup-aware ko→en %.2f en→ko %.2f" % (r["ko_to_en"]["dup_aware"]["p_at_5"], r["en_to_ko"]["dup_aware"]["p_at_5"]),
              "true pair is row+col max: %d/%d" % (r["true_pair_beats_all_its_row_and_column"], n))
        for w in r["warnings"]:
            print("WARNING", name, w)


if __name__ == "__main__":
    main()
