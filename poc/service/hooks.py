"""P2 서비스의 Router hooks (05 §3). upstream examples/hooks/redact.py·audit.py는 함수형이지만 여기서는
경로·SHA·카운터를 들고 있어야 해서 클래스로 쓴다. hook은 duck-typed라 둘 다 Router(hooks=[...])에 들어간다."""
import json
import math
import re
import threading
import time
import unicodedata
from collections import Counter, deque
from pathlib import Path
from types import SimpleNamespace

from laya.evals import questions_fingerprint

# 순서가 의미 있다: 카드번호(13~19자리)를 전화번호보다 먼저 지운다. 숫자 경계는 \b가 아니라 lookaround로 잡는다.
# 한글도 \w라서 "번호010-1234-5678"처럼 붙여 쓴 숫자 앞에서는 \b가 성립하지 않는다.
PII = [
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[email]"),
    (re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)"), "[card]"),
    (re.compile(r"(?<!\d)(?:\+\d{1,3}[ -]?)?\(?0?\d{1,3}\)?[ -]?\d{3,4}[ -]?\d{4}(?!\d)"), "[phone]"),
]


def scrub(value):
    """NFC 정규화(07 §3) 후 이메일·카드번호·전화번호를 마스킹한다. 문자열, dict 값, list 원소에 재귀 적용, 멱등."""
    if isinstance(value, str):
        value = unicodedata.normalize("NFC", value)
        for pattern, token in PII:
            value = pattern.sub(token, value)
        return value
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


def fingerprint(questions):
    """질문 dict 하나의 questions_sha256 (laya.evals.questions_fingerprint, data/evals/MANIFEST.json과 같은 규약)."""
    return questions_fingerprint(SimpleNamespace(examples=[SimpleNamespace(questions=questions)]))


def percentile(sorted_values, q):
    """nearest-rank 백분위. 빈 목록이면 None."""
    if not sorted_values:
        return None
    return round(sorted_values[max(0, math.ceil(q * len(sorted_values)) - 1)], 2)


class NfcRedactHook:
    def on_predict_start(self, ctx):
        ctx.states = [scrub(state) for state in ctx.states]


class ShadowAuditHook:
    """결정 1건당 JSONL 1줄. state는 기록 직전에 다시 scrub한다(멱등): start hook이 돌기 전에 실패한 호출이어도
    마스킹 전 원문이 로그에 남지 않게 하기 위해서다. 정책 필드는 router_v1 질문일 때만 채운다(감사용 재계산)."""

    KEEP = ("type", "choice", "score", "noul", "answer_confidence", "probabilities", "abstention")

    def __init__(self, path, checkpoint_sha, policy, policy_questions_sha256):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint_sha = checkpoint_sha
        self.policy = policy
        self.policy_qsha = policy_questions_sha256
        self.lock = threading.Lock()

    def on_predict_end(self, ctx):
        qsha = fingerprint(ctx.questions)
        lines = []
        for state, result in zip(ctx.states, ctx.results or [None] * len(ctx.states)):
            result = result or {}
            answers = result.get("answers") or {}
            policy = None
            if qsha == self.policy_qsha and "domain" in answers:
                action, detail = self.policy(answers, ctx.model)
                policy = {"action": action, **detail}
            lines.append(json.dumps({
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "run_id": ctx.run_id,
                "model": ctx.model,
                "routing": result.get("routing") or ctx.decision,
                "state": scrub(state),
                "answers": {qid: {k: a[k] for k in self.KEEP if k in a} for qid, a in answers.items()},
                "policy": policy,
                "elapsed_ms": None if ctx.elapsed_ms is None else round(ctx.elapsed_ms, 2),
                "usage": result.get("usage"),
                "error": None if ctx.error is None else type(ctx.error).__name__,
                "checkpoint_sha": self.checkpoint_sha.get(ctx.model),
                "questions_sha256": qsha,
            }, ensure_ascii=False))
        with self.lock, self.path.open("a", encoding="utf-8") as f:
            f.write("".join(line + "\n" for line in lines))


class MetricsHook:
    """프로세스 수명 동안의 카운터(호출·오류·abstention 상태·최근 1,000건 지연). 503은 create_app의 admission에서
    predict 전에 나므로 hook에 보이지 않는다."""

    def __init__(self):
        self.lock = threading.Lock()
        self.by_model = Counter()
        self.abstention = Counter()
        self.errors = 0
        self.elapsed = deque(maxlen=1000)

    def on_predict_end(self, ctx):
        with self.lock:
            self.by_model[ctx.model or "unrouted"] += 1
            self.errors += ctx.error is not None
            self.abstention.update(a["abstention"] for r in ctx.results or []
                                   for a in (r.get("answers") or {}).values() if "abstention" in a)
            if ctx.elapsed_ms is not None:
                self.elapsed.append(ctx.elapsed_ms)

    def snapshot(self):
        with self.lock:
            elapsed = sorted(self.elapsed)
            return {"calls": sum(self.by_model.values()), "by_model": dict(self.by_model), "errors": self.errors,
                    "abstention": dict(self.abstention),
                    "elapsed_ms": {"n": len(elapsed), "p50": percentile(elapsed, 0.5),
                                   "p95": percentile(elapsed, 0.95)}}
