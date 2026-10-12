"""Head-budget check for the Track B files (tokenizer only, no forward): does each checkpoint see every
option intact? Same method as results/korean_support/K2_head_budget.py and results/poc/P0c_analyze.py §4.

    source env.sh && .venv/bin/python results/B/B_head_budget.py > results/B/B_head_budget.md
"""
import json
from pathlib import Path

import torch
from laya.agent import Agent, _load_tokenizer
from laya.common import build_head, encode_text, render_options

torch.set_num_threads(10)
torch.set_num_interop_threads(1)
ROOT = Path(__file__).resolve().parents[2]
FILES = ["data/evals/ko_massive_domain_8.jsonl", "data/evals/ko_massive_domain_8_ko-instr.jsonl",
         "data/evals/ko_massive_domain_8_en-desc.jsonl", "data/evals/ko_klue_ynat_7.jsonl",
         "data/evals/ko_klue_ynat_7_en-desc.jsonl", "data/evals/ko_massive_scenario_18.jsonl",
         "data/evals/ko_massive_intent_20opt.jsonl", "data/evals/ko_klue_nli_3.jsonl", "data/evals/ko_nsmc_sentiment.jsonl",
         "data/evals/ko_kmhas_hate.jsonl", "data/evals/ko_kmhas_type_8.jsonl", "data/evals/ko_3i4k_speechact_7.jsonl"]
CKPTS = {"multilingual": "models/laya-multilingual", "english": "models/laya", "typed-decisions": "models/laya-typed-decisions"}


def main():
    print("| file | ckpt (head_max_len) | qid | k | distinct question dicts | raw tokens/option max | cap | rows with ≥1 option cut "
          "| max options cut | rows with indistinct options | domain_8: options as kept (decoded), first distinct question |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for ckpt, rel in CKPTS.items():
        d = (ROOT / rel).resolve()
        cfg = json.loads((d / "rl_agent_config.json").read_text(encoding="utf-8"))
        tok, hml = _load_tokenizer(str(d / "tokenizer"), cfg), cfg["head_max_len"]
        for f in FILES:
            rows = [json.loads(l) for l in (ROOT / f).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
            for qid in rows[0]["questions"]:
                seen, stats, kept = {}, [], ""
                for r in rows:
                    key = json.dumps(r["questions"][qid], ensure_ascii=False)
                    if key not in seen:
                        iq = Agent._to_internal(r["questions"][qid])
                        ids, markers, st = build_head(tok, iq, hml)
                        opts = render_options(iq)
                        raw = [1 + len(encode_text(tok, " " + o, add_special_tokens=False, truncation=True, max_length=64)["input_ids"]) for o in opts]
                        cap = st["tokens_per_option"]
                        seen[key] = (len(raw), max(raw), cap, sum(x > cap for x in raw) if cap else 0, st["options_distinct"] < st["options"])
                        if "domain_8" in f and not kept:
                            ends = list(markers[1:]) + [len(ids) - 1]
                            kept = " / ".join(tok.decode(ids[a + 1:b]).strip() for a, b in zip(markers, ends)).replace("|", "\\|")
                    stats.append(seen[key])
                caps = {s[2] for s in stats}
                print("| %s | %s (%d) | %s | %d | %d | %d | %s | %d | %d | %d | %s |" % (
                    Path(f).name, ckpt, hml, qid, stats[0][0], len(seen), max(s[1] for s in stats),
                    ",".join(str(c) for c in sorted(caps, key=str)), sum(s[3] > 0 for s in stats), max(s[3] for s in stats),
                    sum(s[4] for s in stats), kept or ""))


if __name__ == "__main__":
    main()
