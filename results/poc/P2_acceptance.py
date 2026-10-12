"""P2 / P2-UI acceptance checks against the running service, no browser (05 §6 P2-UI).

    # server, from the repo root:
    #   source env.sh && LAYA_DEVICE=mps LAYA_API_KEY=devkey LAYA_HOST=127.0.0.1 \
    #     .venv/bin/uvicorn poc.service.app:app --host 127.0.0.1 --port 8000 > results/poc/P2_server.log 2>&1
    source env.sh && .venv/bin/python results/poc/P2_acceptance.py --out results/poc/P2_acceptance.json

Every utterance comes from poc/service/ui/examples.json (hand-written, checked against the eval sets by
P2_offline_check.py) or is synthetic (PII sample, nonsense), so no test-half sentence reaches poc/logs/shadow.jsonl.
The round trip is measured over one keep-alive connection, sequentially (a functional number, not a load test).
"""
import argparse
import http.client
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
KEY = "devkey"
SHADOW = ROOT / "poc/logs/shadow.jsonl"
PII = "김민수 팀장님(minsu.kim@example.com, 010-2345-6789)한테 카드 1234-5678-9012-3456 영수증 메일로 보내줘"
PII_RAW_PARTS = ("minsu.kim", "example.com", "010-2345-6789", "1234-5678-9012-3456")
NONSENSE = ["ㅁㄴㅇㄹ 쀍쀍 zxqv 7#@!", "음악 틀어주고 불도 끄고 내일 날씨랑 메일도 확인해줘"]


class Client:
    def __init__(self, host, port):
        self.conn = http.client.HTTPConnection(host, port, timeout=300)

    def call(self, method, path, body=None, key=KEY):
        headers = {"content-type": "application/json"} if body is not None else {}
        if key:
            headers["Authorization"] = "Bearer " + key
        t0 = time.perf_counter()
        self.conn.request(method, path, body=None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8"),
                          headers=headers)
        resp = self.conn.getresponse()
        raw = resp.read()
        rt_ms = (time.perf_counter() - t0) * 1000.0
        try:
            data = json.loads(raw)
        except ValueError:
            data = None
        return {"status": resp.status, "json": data, "raw": raw, "headers": dict(resp.getheaders()), "rt_ms": rt_ms}


def pct(values, q):
    s = sorted(values)
    return round(s[max(0, math.ceil(q * len(s)) - 1)], 1)


def decide_row(c, text, **extra):
    r = c.call("POST", "/poc/decide", {"utterance": text, **extra})
    assert r["status"] == 200, (r["status"], r["raw"][:300])
    j = r["json"]
    d = j["answers"]["domain"]
    return {"text": text, **extra, "action": j["policy"]["action"], "domain": j["policy"]["domain"], "p": j["policy"]["p"],
            "handler": j["policy"]["handler"], "reason": j["policy"]["reason"], "abstention": d.get("abstention"),
            "routing": j["routing"]["model"], "routing_reason": j["routing"]["reason"], "elapsed_ms": j["elapsed_ms"],
            "rt_ms": round(r["rt_ms"], 1), "input_tokens": j["usage"]["input_tokens"], "probabilities": d["probabilities"]}


def shadow_lines():
    return SHADOW.read_text(encoding="utf-8").splitlines() if SHADOW.exists() else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--latency-n", type=int, default=30)
    a = ap.parse_args()
    c = Client(a.host, a.port)
    out = {"started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "checks": {}}
    chk = out["checks"]
    ex = json.loads((ROOT / "poc/service/ui/examples.json").read_text(encoding="utf-8"))
    router_text = ex["single"][0]["state"]
    shadow_before = len(shadow_lines())

    # health + auth (05 §6 P2-UI 6)
    liveness = c.call("GET", "/health", key=None)["json"]
    health = c.call("GET", "/health")["json"]
    statuses = {"no_key": c.call("POST", "/poc/decide", {"utterance": router_text}, key=None)["status"],
                "wrong_key": c.call("POST", "/poc/decide", {"utterance": router_text}, key="nope")["status"],
                "with_key": c.call("POST", "/poc/decide", {"utterance": router_text})["status"],
                "meta_no_key": c.call("GET", "/poc/meta", key=None)["status"],
                "shadow_no_key": c.call("GET", "/poc/shadow", key=None)["status"],
                "systemone_no_key": c.call("POST", "/v1/systemone", {"state": "x", "questions": {}}, key=None)["status"]}
    chk["auth"] = {"pass": liveness == {"status": "ok"} and statuses["with_key"] == 200
                   and all(v in (401, 403) for k, v in statuses.items() if k != "with_key"),
                   "health_without_key": liveness, "statuses": statuses, "health": health}

    # meta vs run-card values (05 §6 P2-UI 8)
    meta = c.call("GET", "/poc/meta")["json"]
    p4 = json.loads((ROOT / "results/P4/full_20261003-1156_ft-v1_ko_massive_domain_8_full.json").read_text(encoding="utf-8"))["config"]
    manifest = json.loads((ROOT / "data/evals/MANIFEST.json").read_text(encoding="utf-8"))["files"]["ko_massive_domain_8.jsonl"]
    chk["meta"] = {"pass": meta["questions_sha256"] == p4["questions_sha256"] == manifest["questions_sha256"]
                   and meta["checkpoint"]["sha256_of_rl_agent_config"] == p4["checkpoint"]["rl_agent_config_sha256"]
                   and meta["checkpoint"]["base"] in p4["revisions"]["ft-v1"] and meta["thresholds"]["T"] == 0.907,
                   "meta": meta, "p4_report": {"questions_sha256": p4["questions_sha256"],
                                               "rl_agent_config_sha256": p4["checkpoint"]["rl_agent_config_sha256"],
                                               "weights_sha256": p4["checkpoint"]["weights_sha256"],
                                               "revisions": p4["revisions"]}}

    # router_v1 example + 8 domain utterances (05 §6 P2-UI 1)
    rows = [dict(decide_row(c, router_text), expected="productivity")]
    rows += [dict(decide_row(c, u["text"]), expected=u["domain"]) for u in ex["domain_utterances"]]
    chk["domains"] = {"pass": all(r["routing_reason"] == "explicit lang='ko'" and r["abstention"] in ("passed", "abstained")
                                  for r in rows),
                      "route": sum(r["action"] == "ROUTE" for r in rows), "correct_argmax": sum(r["domain"] == r["expected"] for r in rows),
                      "n": len(rows), "rows": rows}

    # FALLBACK: nonsense / multi-intent, a forced abstention, and the "below T" path with min_confidence lowered
    fb = [decide_row(c, t) for t in NONSENSE]
    fb.append(decide_row(c, router_text, min_confidence=1.0))   # p < 1.0이면 반드시 abstained
    low = next((r for r in fb[:len(NONSENSE)] if 0.5 <= r["p"] < 0.907), None)
    if low:
        fb.append(decide_row(c, low["text"], min_confidence=0.5))
    chk["fallback"] = {"pass": fb[len(NONSENSE)]["action"] == "FALLBACK" and fb[len(NONSENSE)]["abstention"] == "abstained"
                       and all(r["action"] == "FALLBACK" for r in fb[len(NONSENSE) + 1:]),
                       "nonsense_fallbacks": sum(r["action"] == "FALLBACK" for r in fb[:len(NONSENSE)]), "rows": fb}

    # english slot: lazy load on first use, policy refuses to apply T to it
    eng = decide_row(c, router_text, model="english")
    loaded = c.call("GET", "/health")["json"]["loaded"]
    chk["english_lazy"] = {"pass": eng["action"] == "FALLBACK" and eng["reason"] == "T not valid for english"
                           and set(loaded) == {"multilingual", "english"}, "row": eng, "loaded_after": loaded}

    # PII masking (05 §6 P2 3, P2-UI 4)
    pii = decide_row(c, PII)
    last = json.loads(shadow_lines()[-1])
    log = SHADOW.read_text(encoding="utf-8")
    chk["pii"] = {"pass": last["state"] == {"utterance": "김민수 팀장님([email], [phone])한테 카드 [card] 영수증 메일로 보내줘"}
                  and not any(part in log for part in PII_RAW_PARTS), "row": pii, "shadow_state": last["state"],
                  "raw_parts_in_log": [part for part in PII_RAW_PARTS if part in log]}

    # general mode /v1/systemone, 3-option choice
    body = {"state": {"message": "로그인할 때마다 500 오류가 나서 대시보드에 들어갈 수가 없어요"},
            "questions": {"team": {"type": "choice", "instructions": "Which team should handle `message`?",
                                   "criteria": {"billing": "결제, 청구서, 환불 관련 문의", "technical": "버그, 오류, 접속·연동 문제",
                                                "sales": "가격 견적, 신규 구매 상담"}}}}
    r = c.call("POST", "/v1/systemone", body)
    team = (r["json"] or {}).get("answers", {}).get("team", {})
    chk["systemone"] = {"pass": r["status"] == 200 and set(team.get("probabilities", {})) == {"billing", "technical", "sales"},
                        "status": r["status"], "answer": team, "routing": (r["json"] or {}).get("routing"),
                        "x_inference_time_ms": r["headers"].get("x-inference-time-ms"), "rt_ms": round(r["rt_ms"], 1)}

    # static UI
    page, exj = c.call("GET", "/poc/ui/", key=None), c.call("GET", "/poc/ui/examples.json", key=None)
    chk["ui_static"] = {"pass": page["status"] == 200 and b"<title>Laya Playground</title>" in page["raw"]
                        and exj["status"] == 200 and exj["json"]["single"][0]["id"] == "router_v1",
                        "content_type": page["headers"].get("content-type"), "bytes": len(page["raw"])}

    # round trip p50/p95 of a 1-question /poc/decide (05 §6 P2-UI 5: browser round trip vs server elapsed_ms)
    texts = [u["text"] for u in ex["domain_utterances"]]
    for t in texts[:3]:
        c.call("POST", "/poc/decide", {"utterance": t})   # warm-up, discarded
    lat = [decide_row(c, texts[i % len(texts)]) for i in range(a.latency_n)]
    rts, els = [r["rt_ms"] for r in lat], [r["elapsed_ms"] for r in lat]
    over = [r["rt_ms"] - r["elapsed_ms"] for r in lat]
    chk["latency"] = {"pass": pct(over, 0.95) < 50, "n": len(lat), "warmup": 3, "connection": "http.client keep-alive",
                      "rt_ms": {"p50": pct(rts, 0.5), "p95": pct(rts, 0.95), "min": round(min(rts), 1), "max": round(max(rts), 1)},
                      "server_elapsed_ms": {"p50": pct(els, 0.5), "p95": pct(els, 0.95)},
                      "rt_minus_elapsed_ms": {"p50": pct(over, 0.5), "p95": pct(over, 0.95)}, "samples_rt_ms": rts}

    # shadow counters after all calls
    sh = c.call("GET", "/poc/shadow?limit=50")["json"]
    lines = shadow_lines()
    recs = [json.loads(line) for line in lines]
    decided = [x["policy"] for x in recs if x.get("policy")]
    cnt = sh["counters"]
    meta_after = c.call("GET", "/poc/meta")["json"]
    chk["shadow"] = {"pass": cnt["total"] == len(lines) and len(sh["records"]) == min(50, len(lines))
                     and cnt["actions"]["ROUTE"] + cnt["actions"]["FALLBACK"] == len(decided) == sum(cnt["by_domain"].values())
                     and all({"run_id", "model", "routing", "answers", "elapsed_ms", "checkpoint_sha", "questions_sha256"} <= set(x)
                             for x in recs),
                     "lines_before": shadow_before, "lines_after": len(lines), "counters": cnt,
                     "metrics_hook": meta_after["metrics"]}

    # CLI-equivalent argmax: the laya CLI cannot load a checkpoint directory (--model takes names only), so the same
    # 9 utterances go through laya.load(ft-v1) in-process on CPU fp32 and are compared with the server's MPS answers.
    import laya
    questions = json.loads((ROOT / "poc/schema/router_v1.json").read_text(encoding="utf-8"))["questions"]
    agent = laya.load("./poc/finetune/ckpt_domain8_v1", device="cpu")
    par = []
    for r in rows:
        local = agent.system_one({"utterance": r["text"]}, questions, lang="ko")["answers"]["domain"]
        par.append({"text": r["text"], "server": r["domain"], "inprocess_cpu": local["choice"],
                    "max_abs_dp": round(max(abs(local["probabilities"][k] - r["probabilities"][k]) for k in local["probabilities"]), 4)})
    chk["inprocess_parity"] = {"pass": all(x["server"] == x["inprocess_cpu"] for x in par) and max(x["max_abs_dp"] for x in par) <= 0.01,
                               "flips": sum(x["server"] != x["inprocess_cpu"] for x in par),
                               "max_abs_dp": max(x["max_abs_dp"] for x in par), "rows": par}

    # what the copied CLI command actually runs: the Hub base multilingual checkpoint, not ft-v1 (offline, cache only)
    cmd = [str(ROOT / ".venv/bin/laya"), router_text, "--model", "ml", "--lang", "ko",
           "--questions", "poc/schema/router_v1.json", "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=dict(os.environ, HF_HUB_OFFLINE="1"))
    base = None
    if proc.returncode == 0:   # agent 경고가 stdout에 print될 수 있어 첫 JSON 객체만 읽는다
        base = json.JSONDecoder().raw_decode(proc.stdout[proc.stdout.index("{"):])[0]["answers"]["domain"]
    chk["cli_base"] = {"note": "informational: laya CLI --model ml = base multilingual 55cf4c4 (zero-shot)",
                       "cmd": " ".join(cmd[1:]), "returncode": proc.returncode,
                       "choice": base and base["choice"], "answer_confidence": base and base["answer_confidence"],
                       "server_ft_v1_choice": rows[0]["domain"], "server_ft_v1_p": rows[0]["p"],
                       "stderr_tail": proc.stderr[-400:]}

    out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for name, v in chk.items():
        print("%-17s %s" % (name, {True: "PASS", False: "FAIL"}.get(v.get("pass"), "info")))
    print("domains: ROUTE %d/%d, argmax = expected %d/%d" % (chk["domains"]["route"], chk["domains"]["n"],
                                                             chk["domains"]["correct_argmax"], chk["domains"]["n"]))
    print("latency: rt p50 %.1f / p95 %.1f ms, server elapsed p50 %.1f / p95 %.1f ms, rt-elapsed p95 %.1f ms" % (
        chk["latency"]["rt_ms"]["p50"], chk["latency"]["rt_ms"]["p95"], chk["latency"]["server_elapsed_ms"]["p50"],
        chk["latency"]["server_elapsed_ms"]["p95"], chk["latency"]["rt_minus_elapsed_ms"]["p95"]))


if __name__ == "__main__":
    main()
