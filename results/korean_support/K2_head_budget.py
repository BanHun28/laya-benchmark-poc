"""Head-budget check (tokenizer only, no forward): does a checkpoint see every option of the K2
questions intact? The head is state-independent, so ko and en twins share it; this only matters for
reading the english-checkpoint reference rows. Same method as results/poc/P0c_analyze.py §4.

    source env.sh && .venv/bin/python results/korean_support/K2_head_budget.py > results/korean_support/K2_head_budget.md
"""
import json
from pathlib import Path

from laya.agent import Agent, _load_tokenizer
from laya.common import build_head, encode_text, render_options

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FILES = ["K2_scen18_kodesc_en.jsonl", "K2_scen18_keydesc_en.jsonl", "K2_intent20_en.jsonl", "probe_en.jsonl"]


def main():
    print("| file (questions shared by ko/en twins) | ckpt (head_max_len) | qid | k | rows | raw tokens/option max | cap | rows with ≥1 option cut | max options cut | rows with indistinct options |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for ckpt in ("multilingual", "english"):
        d = (ROOT / ("models/laya-multilingual" if ckpt == "multilingual" else "models/laya")).resolve()
        cfg = json.loads((d / "rl_agent_config.json").read_text(encoding="utf-8"))
        tok, hml = _load_tokenizer(str(d / "tokenizer"), cfg), cfg["head_max_len"]
        for f in FILES:
            rows = [json.loads(l) for l in (HERE / f).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
            for qid in rows[0]["questions"]:
                stats_rows = []
                for r in rows:
                    iq = Agent._to_internal(r["questions"][qid])
                    _, _, st = build_head(tok, iq, hml)
                    raw = [1 + len(encode_text(tok, " " + o, add_special_tokens=False, truncation=True, max_length=48)["input_ids"]) for o in render_options(iq)]
                    cap = st["tokens_per_option"]
                    stats_rows.append((len(raw), max(raw), cap, sum(x > cap for x in raw) if cap else 0, st["options_distinct"] < st["options"]))
                caps = {s[2] for s in stats_rows}
                print("| %s | %s (%d) | %s | %d | %d | %d | %s | %d | %d | %d |" % (
                    f, ckpt, hml, qid, stats_rows[0][0], len(rows), max(s[1] for s in stats_rows), ",".join(str(c) for c in sorted(caps, key=str)),
                    sum(s[3] > 0 for s in stats_rows), max(s[3] for s in stats_rows), sum(s[4] for s in stats_rows)))


if __name__ == "__main__":
    main()
