"""P2 offline check: everything that can be verified without loading a checkpoint or starting a server.

    source env.sh && .venv/bin/python results/poc/P2_offline_check.py | tee results/poc/P2_offline_check.log

1. py_compile of the new Python files.
2. JSON validity of poc/schema/router_v1.json and poc/service/ui/examples.json; every question dict embedded in
   examples.json equals its source (router_v1.json, triage_v1 + gateway_v1, laya.presets, the YNAT eval question).
3. Label hygiene (05 §3 rule 1): no example state equals (after whitespace/punctuation normalisation) a state in
   data/evals/*.jsonl, the full MASSIVE ko test pool or the fine-tuning train/validation files.
4. HTML sanity with html.parser (balanced tags, ids, no external resources), `node --check` on the inline script and
   node unit tests of its DOM-free functions (question round trip, request bodies, problems, shell/Python snippets).
5. Every endpoint the JS calls is a route of the real app with the same HTTP method.
6. In-process integration through fastapi.testclient with the real Router.predict / hooks / confidence gate / routes
   and a fake forward pass (FakeAgent): auth, /poc/decide policy cases and 422s, PII + NFC redaction in what the model
   sees and in shadow.jsonl, /v1/systemone, /poc/shadow counters, /poc/meta identity, static UI.
"""
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
UI = ROOT / "poc/service/ui"
NEW_PY = ["poc/service/app.py", "poc/service/hooks.py", "poc/service/policy.py", "results/poc/P2_schema_check.py",
          "results/poc/P2_offline_check.py", "results/poc/P2_acceptance.py"]
RESULTS = []


def ok(name, detail=""):
    RESULTS.append(name)
    print("OK  %s%s" % (name, (" | " + detail) if detail else ""))


def norm(text):
    return re.sub(r"[\s.,!?~'\"]+", "", unicodedata.normalize("NFC", text))


# 1 ------------------------------------------------------------------------------------------------------------
def check_compile():
    present = [p for p in NEW_PY if (ROOT / p).exists()]
    for p in present:
        py_compile.compile(str(ROOT / p), doraise=True)
    ok("1 py_compile", ", ".join(present))


# 2 ------------------------------------------------------------------------------------------------------------
def check_json():
    from laya import presets
    schema = json.loads((ROOT / "poc/schema/router_v1.json").read_text(encoding="utf-8"))
    ex = json.loads((UI / "examples.json").read_text(encoding="utf-8"))
    triage = json.loads((ROOT / "poc/schema/triage_v1.json").read_text(encoding="utf-8"))["questions"]
    gateway = json.loads((ROOT / "poc/schema/gateway_v1.json").read_text(encoding="utf-8"))["questions"]
    ynat_line = next(line for line in (ROOT / "data/evals/ko_klue_ynat_7.jsonl").read_text(encoding="utf-8").splitlines()
                     if line.strip() and not line.startswith("#"))
    dump = lambda o: json.dumps(o, ensure_ascii=False)  # noqa: E731 -- order-sensitive comparison
    by_id = {e["id"]: e for e in ex["single"] + ex["multi"] + [ex["ynat"]]}
    sources = {"router_v1": schema["questions"], "triage_a": {**triage, **gateway},
               "email": presets.email_questions(), "guard": presets.guard_questions(),
               "model_router": presets.router_questions(), "ynat_7": json.loads(ynat_line)["questions"]}
    for eid, want in sources.items():
        assert dump(by_id[eid]["questions"]) == dump(want), eid
    assert len(ex["single"]) == 5 and len(ex["multi"]) == 4 and len(ex["domain_utterances"]) == 8
    assert {u["domain"] for u in ex["domain_utterances"]} == set(schema["questions"]["domain"]["criteria"])
    assert [e["id"] for e in ex["multi"] if e.get("held")] == ["triage_a"]
    for e in by_id.values():
        assert e["state_format"] in ("text", "json") and (e["state_format"] == "json") == isinstance(e["state"], dict)
    ok("2 JSON validity + embedded questions = sources",
       "single %d, multi %d (held: triage_a), domain utterances %d, sources %s"
       % (len(ex["single"]), len(ex["multi"]), len(ex["domain_utterances"]), sorted(sources)))
    return ex


# 3 ------------------------------------------------------------------------------------------------------------
def check_hygiene(ex):
    files = sorted(ROOT.glob("data/evals/*.jsonl")) + [ROOT / "results/P4/evalsets_full/ko_massive_domain_8.jsonl",
                                                        ROOT / "poc/finetune/data/domain8_train.jsonl",
                                                        ROOT / "poc/finetune/data/domain8_dev.jsonl"]
    pool = {}
    for f in files:
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            state = json.loads(line)["state"]
            for value in ([state] if isinstance(state, str) else
                          [v for v in state.values() if isinstance(v, str)] if isinstance(state, dict) else []):
                pool.setdefault(norm(value), str(f.relative_to(ROOT)))
    texts = [u["text"] for u in ex["domain_utterances"]]
    for e in ex["single"] + ex["multi"] + [ex["ynat"]]:
        texts += [e["state"]] if isinstance(e["state"], str) else [v for v in e["state"].values() if isinstance(v, str)]
    hits = {t: pool[norm(t)] for t in texts if norm(t) in pool}
    assert not hits, hits
    ok("3 label hygiene", "%d example texts vs %d distinct states in %d files: 0 matches" % (len(texts), len(pool), len(files)))


# 4 ------------------------------------------------------------------------------------------------------------
VOID = {"meta", "link", "input", "br", "hr", "img", "source", "wbr", "area", "base", "col", "embed", "param", "track"}


class Sanity(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.ids, self.errors, self.tags, self.scripts = [], set(), [], {}, []
        self.in_script, self.title, self.in_title = False, "", False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags[tag] = self.tags.get(tag, 0) + 1
        if "id" in a:
            if a["id"] in self.ids:
                self.errors.append("duplicate id %s" % a["id"])
            self.ids.add(a["id"])
        for attr in ("src", "href"):
            if re.match(r"(https?:)?//", a.get(attr) or ""):
                self.errors.append("external %s=%s" % (attr, a[attr]))
        if tag == "script":
            self.in_script = True
            if "src" in a:
                self.errors.append("script src")
        if tag == "link" and a.get("rel") == "stylesheet":
            self.errors.append("external stylesheet")
        self.in_title = tag == "title"
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append("unbalanced </%s> (open: %s)" % (tag, self.stack[-3:]))
            return
        self.stack.pop()
        self.in_script = self.in_script and tag != "script"
        self.in_title = False

    def handle_data(self, data):
        if self.in_script:
            self.scripts.append(data)
        if self.in_title:
            self.title += data


NODE_TESTS = r"""
const assert = require('assert');
const { execFileSync } = require('child_process');
const ex = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const all = ex.single.concat(ex.multi, [ex.ynat]);
for (const e of all) {
  const list = Object.entries(e.questions).map(([id, d]) => questionFromDef(id, d));
  assert.strictEqual(JSON.stringify(questionsFromList(list)), JSON.stringify(e.questions), 'round trip ' + e.id);
}
const base = { mode: 'single', poc: false, stateFormat: 'text', stateKey: 'message', stateText: 'x',
               adv: { model: 'auto', mcOn: false, mc: 0.9, lang: '', langGuess: '', maxLen: '', headMaxLen: '' } };
const router = ex.single.find(e => e.poc);
const poc = Object.assign({}, base, { poc: true, stateText: router.state, stateKey: 'utterance',
  questions: Object.entries(router.questions).map(([i, d]) => questionFromDef(i, d)), adv: Object.assign({}, base.adv, { lang: 'ko' }) });
assert.deepStrictEqual(buildRequest(poc), { path: '/poc/decide', body: { utterance: router.state, lang: 'ko' } });
poc.adv = Object.assign({}, poc.adv, { lang: '', mcOn: true, mc: 0.95, model: 'multilingual' });
assert.deepStrictEqual(buildRequest(poc).body, { utterance: router.state, lang: null, min_confidence: 0.95, model: 'multilingual' });
const support = ex.single.find(e => e.id === 'support_routing');
const gen = Object.assign({}, base, { stateText: support.state, questions: Object.entries(support.questions).map(([i, d]) => questionFromDef(i, d)) });
assert.deepStrictEqual(buildRequest(gen), { path: '/v1/systemone', body: { state: { message: support.state }, questions: support.questions } });
const triage = ex.multi.find(e => e.held);
const multi = Object.assign({}, base, { mode: 'multi', questions: Object.entries(triage.questions).map(([i, d]) => questionFromDef(i, d)) });
assert.strictEqual(Object.keys(buildRequest(multi).body.questions).length, 7);
multi.mode = 'single';
assert.deepStrictEqual(Object.keys(buildRequest(multi).body.questions), ['intent']);
const agent = ex.single.find(e => e.state_format === 'json');
const js = Object.assign({}, base, { stateFormat: 'json', stateText: JSON.stringify(agent.state), questions: Object.entries(agent.questions).map(([i, d]) => questionFromDef(i, d)) });
assert.deepStrictEqual(buildRequest(js).body.state, agent.state);
// problems
const many = Object.assign({}, gen, { questions: [Object.assign(questionFromDef('q1', support.questions.team), {
  options: Array.from({ length: 21 }, (_, i) => ({ key: 'opt' + i, desc: '' })) })] });
const p21 = findProblems(many);
assert.strictEqual(p21.errs.length, 0); assert.ok(p21.warns.some(w => w.includes('head_max_len')), '21 options warn');
const twenty = Object.assign({}, many, { questions: [Object.assign({}, many.questions[0], { options: many.questions[0].options.slice(0, 20) })] });
assert.ok(!findProblems(twenty).warns.some(w => w.includes('head_max_len')), '20 options no warn');
const dup = Object.assign({}, gen, { questions: [blankQuestion('a'), blankQuestion('a')] });
assert.ok(findProblems(dup).errs.some(e => e.includes('중복')));
assert.ok(findProblems(Object.assign({}, js, { stateText: '{bad' })).errs.some(e => e.includes('JSON')));
assert.ok(findProblems(Object.assign({}, gen, { stateText: '  ' })).errs.length > 0);
assert.strictEqual(findProblems(Object.assign({}, poc, { questions: [] })).errs.length, 0);
// snippets: shell quoting survives bash, CLI form, Python literal printed for the caller to check
for (const s of ["it's", "a'b'c", '"q" $HOME `x` \\n 내일', '']) {
  assert.strictEqual(execFileSync('bash', ['-c', 'printf %s ' + shq(s)]).toString(), s, 'shq ' + s);
}
const preq = buildRequest(Object.assign({}, poc, { adv: Object.assign({}, poc.adv, { lang: 'ko', mcOn: false, model: 'auto' }) }));
const curl = curlSnippet(preq, 'http://127.0.0.1:8000');
assert.ok(curl.startsWith("curl -s 'http://127.0.0.1:8000/poc/decide'"));
const cli = cliSnippet(preq);
assert.ok(cli.split('\n')[1].endsWith("--lang 'ko' --questions poc/schema/router_v1.json --json"), cli);
assert.ok(cliSnippet(buildRequest(js)).startsWith('# laya CLI는 state를'));
assert.ok(cliSnippet(buildRequest(gen)).includes('/tmp/laya_questions.json'));
assert.strictEqual(textPreview({ utterance: 'a'.repeat(50) }, 40), 'a'.repeat(40) + '…');
assert.strictEqual(textPreview({ goal: 'g', x: 1 }, 40), 'g');
console.log(JSON.stringify({ curl, python: pythonSnippet(preq, 'http://127.0.0.1:8000'), body: preq.body }));
"""


def check_html():
    html = (UI / "index.html").read_text(encoding="utf-8")
    p = Sanity()
    p.feed(html)
    p.close()
    need = {"chips", "state", "statekey", "qlist", "run", "out", "out-badge", "banner", "poclock", "problems", "adv-mc",
            "cards", "counters", "shadow-rows", "doclist", "health", "meta", "hbadge", "apikey", "mode-single", "mode-multi"}
    assert not p.errors and not p.stack, (p.errors, p.stack)
    assert need <= p.ids, need - p.ids
    assert p.title == "Laya Playground" and re.search(r'<html lang="ko">', html) and 'name="viewport"' in html
    assert p.tags.get("script") == 1 and p.tags.get("style") == 1 and "@media (max-width: 899px)" in html
    for text in ("결정이 생성되지 않았습니다. 입력은 유지됩니다.", "[ · ]", "Run Laya ↗", "실제 로컬 모델 실행. 시뮬레이션 없음.",
                 "내부 PoC 검토 도구. 운영 배포 대상 아님. 액션을 실행하지 않음(docs/staged-adoption.md)",
                 "head_max_len 예산 초과 가능(README Honest limits), 03 Track C6 참고", "5000"):
        assert text in html, text
    script = "".join(p.scripts)
    with tempfile.TemporaryDirectory() as tmp:
        full = Path(tmp) / "ui.js"
        full.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(full)], check=True)
        pure = script[script.index("/* pure:start"):script.index("/* pure:end */")]
        test = Path(tmp) / "pure_test.js"
        test.write_text(pure + NODE_TESTS, encoding="utf-8")
        out = subprocess.run(["node", str(test), str(UI / "examples.json")], check=True, capture_output=True, text=True).stdout
    snippets = json.loads(out)
    py = snippets["python"].splitlines()
    scope = {}
    exec("\n".join(py[:3]), scope)  # import + body = json.loads(<literal>): the copied Python rebuilds the same body
    assert scope["body"] == snippets["body"], scope["body"]
    ok("4 HTML sanity + node --check + DOM-free JS unit tests",
       "%d tags, %d ids, title=%r, round trip of %d example question sets, 21-option warning, shell/Python quoting"
       % (sum(p.tags.values()), len(p.ids), p.title, 10))
    return script


# 5/6 ----------------------------------------------------------------------------------------------------------
FAKE = {"내일 아침 7시에 깨워줘": ("productivity", 0.97), "애매한 요청": ("general", 0.62)}


class FakeAgent:
    """Router.predict, hooks, abstention gate and routes stay real; only Agent.system_one is replaced."""

    device = "cpu"

    def __init__(self):
        self.seen = []

    def system_one(self, state, questions, lang=None, **_):
        self.seen.append(state)
        utter = state.get("utterance") if isinstance(state, dict) else None
        answers = {}
        for qid, q in questions.items():
            act = {"act_probability": 0.1}
            if q["type"] == "choice":
                keys = list(q["criteria"])
                top, p = FAKE.get(utter, (keys[0], 0.6))
                probs = {k: round(p if k == top else (1 - p) / (len(keys) - 1), 4) for k in keys}
                answers[qid] = {"type": "choice", "choice": top, "probabilities": probs, "confidence": 0.5,
                                "answer_confidence": p, "action": act}
            elif q["type"] == "score":
                n = len(q["criteria"])
                answers[qid] = {"type": "score", "score": (n - 1) / 2, "legend": {str(i): c for i, c in enumerate(q["criteria"])},
                                "probabilities": {str(i): round(1 / n, 4) for i in range(n)}, "confidence": 0.1,
                                "answer_confidence": round(1 / n, 4), "action": act}
            else:
                answers[qid] = {"type": "noul", "noul": 0.7, "confidence": 0.7, "answer_confidence": 0.7, "action": act}
        return {"model": "laya-rl-agent", "answers": answers, "usage": {"input_tokens": 100, "output_tokens": 0}}


def import_app_with_fake_router(shadow):
    import laya
    from laya.router import Router, normalise_name

    class FakeRouter(Router):
        def load(self, name):
            key = normalise_name(name)
            with self._lock:
                if key not in self._agents:
                    self._agents[key] = FakeAgent()
                    self._order.append(key)
                self._touch(key)
                return self._agents[key]

    laya.Router = FakeRouter
    os.environ["LAYA_API_KEY"] = "offline-key"
    import poc.service.app as svc
    from poc.service.hooks import ShadowAuditHook
    svc.SHADOW_LOG = shadow
    for hook in svc.ROUTER.hooks:
        if isinstance(hook, ShadowAuditHook):
            hook.path = shadow
    return svc


def check_routes(svc, script):
    from fastapi.routing import APIRoute
    from starlette.routing import Mount
    methods = {r.path: r.methods for r in svc.app.routes if isinstance(r, APIRoute)}
    mounts = [r.path for r in svc.app.routes if isinstance(r, Mount)]
    routes_js = dict(re.findall(r"(\w+): '(/[^']*)'", re.search(r"const ROUTES = \{(.*?)\};", script).group(1)))
    expected = {"decide": "POST", "shadow": "GET", "meta": "GET", "systemone": "POST", "health": "GET"}
    assert set(routes_js) == set(expected), routes_js
    for name, path in routes_js.items():
        assert expected[name] in methods.get(path, set()), (name, path, methods.get(path))
    fetches = set(re.findall(r"fetch\(([^,)]+)", script))
    assert fetches == {"BASE + path", "'examples.json'"}, fetches
    calls = set(re.findall(r"api\('(GET|POST)', ([^,)]+)", script))
    assert calls == {("POST", "req.path"), ("GET", "ROUTES.shadow + '?limit=50'"), ("GET", "ROUTES.meta"),
                     ("GET", "ROUTES.health")}, calls
    assert "/poc/ui" in mounts and (UI / "examples.json").exists()
    ok("5 JS endpoints = app routes",
       "%s; fetch only via api() and 'examples.json' (static mount /poc/ui)" %
       ", ".join("%s %s" % (expected[n], p) for n, p in sorted(routes_js.items())))


def check_integration(svc, shadow):
    from fastapi.testclient import TestClient
    from poc.service.hooks import scrub
    key = {"Authorization": "Bearer offline-key"}
    calls = 0
    with TestClient(svc.app) as c:
        # auth
        for r in (c.post("/poc/decide", json={"utterance": "x"}), c.get("/poc/shadow"), c.get("/poc/meta"),
                  c.post("/v1/systemone", json={"state": "x", "questions": {}})):
            assert r.status_code == 401, (r.request.url, r.status_code)
        assert c.post("/poc/decide", json={"utterance": "x"}, headers={"Authorization": "Bearer wrong"}).status_code == 401
        assert c.get("/health").json() == {"status": "ok"} and c.get("/health", headers=key).json()["loaded"] == ["multilingual"]
        meta = c.get("/poc/meta", headers=key).json()
        assert meta["questions_sha256"] == "a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54"
        assert meta["checkpoint"] == {"path": "poc/finetune/ckpt_domain8_v1", "base": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851",
                                      "sha256_of_rl_agent_config": "3270d480d05a68454004022b90e80f422c8b364ba1bd90ce43b004cde3ab9638"}
        assert meta["thresholds"]["T"] == 0.907 and meta["schema_version"] == "router_v1"
        # policy cases
        r = c.post("/poc/decide", json={"utterance": "내일 아침 7시에 깨워줘"}, headers=key).json()
        calls += 1
        d = r["answers"]["domain"]
        assert r["policy"] == {"action": "ROUTE", "domain": "productivity", "handler": "calendar-svc", "p": 0.97, "reason": "passed"}, r["policy"]
        assert d["abstention"] == "passed" and d["abstention_threshold"] == 0.907 and r["routing"]["reason"] == "explicit lang='ko'"
        assert r["routing"]["repo"] == "./poc/finetune/ckpt_domain8_v1" and r["schema_version"] == "router_v1"
        assert r["checkpoint"]["sha256_of_rl_agent_config"].startswith("3270d480") and r["thresholds"] == {"T": 0.907}
        r = c.post("/poc/decide", json={"utterance": "애매한 요청"}, headers=key).json()
        calls += 1
        assert r["policy"]["action"] == "FALLBACK" and r["policy"]["reason"] == "abstained" and r["policy"]["handler"] is None
        r = c.post("/poc/decide", json={"utterance": "애매한 요청", "min_confidence": 0.5}, headers=key).json()
        calls += 1
        assert r["answers"]["domain"]["abstention"] == "passed" and r["policy"]["reason"] == "below T"
        r = c.post("/poc/decide", json={"utterance": "내일 아침 7시에 깨워줘", "min_confidence": 0.99}, headers=key).json()
        calls += 1
        assert r["answers"]["domain"]["abstention"] == "abstained" and r["policy"]["action"] == "FALLBACK"
        r = c.post("/poc/decide", json={"utterance": "내일 아침 7시에 깨워줘", "model": "english"}, headers=key).json()
        calls += 1
        assert r["policy"]["reason"] == "T not valid for english" and r["checkpoint"] == {"path": "models/laya", "base": svc.BASE}
        r = c.post("/poc/decide", json={"utterance": "내일 아침 7시에 깨워줘", "lang": None}, headers=key).json()
        calls += 1
        assert r["routing"]["model"] == "multilingual" and "explicit" not in r["routing"]["reason"], r["routing"]
        for bad in ({}, {"utterance": " "}, {"utterance": 3}, {"utterance": "a", "min_confidence": 1.5},
                    {"utterance": "a", "lang": 5}, {"utterance": "a", "model": "typed-decisions"}):
            assert c.post("/poc/decide", json=bad, headers=key).status_code == 422, bad
        assert c.post("/poc/decide", json={"utterance": "가" * 50001}, headers=key).status_code == 413
        # PII + NFC: what the model sees and what the shadow log keeps
        raw = "김민수 팀장님(minsu.kim@example.com, 010-2345-6789)한테 카드 1234-5678-9012-3456 영수증 메일로 보내줘"
        r = c.post("/poc/decide", json={"utterance": unicodedata.normalize("NFD", raw)}, headers=key)
        calls += 1
        seen = svc.ROUTER._agents["multilingual"].seen[-1]["utterance"]
        assert seen == "김민수 팀장님([email], [phone])한테 카드 [card] 영수증 메일로 보내줘", seen
        assert unicodedata.is_normalized("NFC", seen)
        # general mode, 3-option choice
        body = {"state": {"message": "로그인하면 계속 500 오류가 나요"}, "questions": {"team": {
            "type": "choice", "instructions": "Which team should handle `message`?",
            "criteria": {"billing": "결제·환불", "technical": "오류·접속 문제", "sales": "구매 상담"}}}}
        r = c.post("/v1/systemone", json=body, headers=key)
        calls += 1
        assert r.status_code == 200 and set(r.json()["answers"]["team"]["probabilities"]) == {"billing", "technical", "sales"}
        assert "X-Inference-Time-Ms" in r.headers
        # shadow log + counters
        log = shadow.read_text(encoding="utf-8")
        for secret in ("minsu.kim", "010-2345-6789", "1234-5678-9012-3456", unicodedata.normalize("NFD", "김민수")):
            assert secret not in log, secret
        records = [json.loads(line) for line in log.splitlines()]
        assert len(records) == calls
        assert all(set(rec) >= {"run_id", "model", "routing", "answers", "elapsed_ms", "checkpoint_sha", "questions_sha256", "policy", "state"}
                   for rec in records)
        assert records[-1]["policy"] is None and records[0]["policy"]["action"] == "ROUTE"
        assert records[0]["checkpoint_sha"].startswith("3270d480") and records[4]["checkpoint_sha"] == svc.BASE
        sh = c.get("/poc/shadow?limit=3", headers=key).json()
        cnt = sh["counters"]
        decided = [rec["policy"] for rec in records if rec["policy"]]
        assert len(sh["records"]) == 3 and cnt["total"] == calls and cnt["errors"] == 0
        assert cnt["actions"]["ROUTE"] + cnt["actions"]["FALLBACK"] == len(decided) == sum(cnt["by_domain"].values())
        assert cnt["actions"]["ROUTE"] == 2 and cnt["fallback_rate"] == round(cnt["actions"]["FALLBACK"] / len(decided), 4)
        assert cnt["elapsed_ms"]["p50"] is not None and cnt["abstained"]["count"] >= 2
        assert c.get("/poc/meta", headers=key).json()["metrics"]["calls"] == calls
        assert c.get("/poc/shadow?limit=0", headers=key).status_code == 422
        # static UI
        page = c.get("/poc/ui/")
        assert page.status_code == 200 and "text/html" in page.headers["content-type"] and "Laya Playground" in page.text
        assert c.get("/poc/ui/examples.json").json()["single"][0]["id"] == "router_v1"
    assert scrub(scrub(raw)) == scrub(raw)
    for text, want in (("2026-10-03 오후 3시 15000원", "2026-10-03 오후 3시 15000원"), ("번호010-1234-5678로", "번호[phone]로"),
                       ("02-123-4567", "[phone]"), ("+82 10-1234-5678", "[phone]"), ("카드1234567890123456", "카드[card]"),
                       ({"a": ["x@y.co"], "b": 1}, {"a": ["[email]"], "b": 1})):
        assert scrub(text) == want, (text, scrub(text))
    ok("6 in-process integration (fake forward pass)",
       "%d predict calls → shadow %d lines, counters %s; 401×5, 422×7, 413; PII/NFC masked before the model and in the log"
       % (calls, len(records), json.dumps(cnt["actions"])))


def main():
    check_compile()
    ex = check_json()
    check_hygiene(ex)
    script = check_html()
    with tempfile.TemporaryDirectory() as tmp:
        shadow = Path(tmp) / "shadow.jsonl"
        svc = import_app_with_fake_router(shadow)
        check_routes(svc, script)
        check_integration(svc, shadow)
    print("ALL OK: %d checks" % len(RESULTS))


if __name__ == "__main__":
    main()
