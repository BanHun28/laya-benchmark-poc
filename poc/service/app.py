"""P2 서비스: laya-serve 앱(create_app) + 파인튜닝 체크포인트 ft-v1 + hooks + /poc/* 라우트 (05 §3·§5, 열린 질문 16).

    source env.sh   # 저장소 루트에서 실행: Router 모델 경로가 루트 기준 상대 경로다
    LAYA_DEVICE=mps LAYA_API_KEY=devkey LAYA_HOST=127.0.0.1 \
      .venv/bin/uvicorn poc.service.app:app --host 127.0.0.1 --port 8000

laya-serve의 LAYA_MODELS는 체크포인트 이름만 받으므로(laya/serve.py:667-668) ft-v1은 여기서 Router의 "multilingual"
슬롯에 경로로 올린다. ft-v1은 rl_agent_config.json에 자체 fitted temperature가 있어 poc/calibration/ko_v1.json
(zero-shot base용 payload)을 적용하지 않는다. LAYA_MODELS·LAYA_DEFAULT_MODEL·LAYA_MAX_LOADED·LAYA_THREADS는 읽지 않는다.
"""
import hashlib
import hmac
import json
import os
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Optional

from fastapi import Body, Header, HTTPException, Query
from fastapi.staticfiles import StaticFiles

import laya
from laya import Router
from laya.serve import _check_request_limits, _validate_language_param, _validate_min_confidence, create_app
from poc.service.hooks import MetricsHook, NfcRedactHook, ShadowAuditHook, fingerprint, percentile
from poc.service.policy import CALIBRATED_MODEL, HANDLER, T, T_SOURCE, route

ROOT = Path(__file__).resolve().parents[2]
FT_PATH = "poc/finetune/ckpt_domain8_v1"
BASE = "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"   # models/laya 스냅샷(02 §2.6), ft-v1의 출발점
SCHEMA_PATH = "poc/schema/router_v1.json"
SHADOW_LOG = ROOT / "poc/logs/shadow.jsonl"

QUESTIONS = json.loads((ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))["questions"]
QSHA = fingerprint(QUESTIONS)
CHECKPOINT = {"path": FT_PATH,
              "sha256_of_rl_agent_config": hashlib.sha256((ROOT / FT_PATH / "rl_agent_config.json").read_bytes()).hexdigest(),
              "base": BASE}
if (CHECKPOINT["sha256_of_rl_agent_config"], QSHA) != (T_SOURCE["rl_agent_config_sha256"], T_SOURCE["questions_sha256"]):
    raise SystemExit("policy.T=%s는 rl_agent_config %s / questions_sha256 %s에서 고른 값인데 지금은 %s / %s다. "
                     "T를 다시 정한 뒤 기동할 것(05 §5)." % (T, T_SOURCE["rl_agent_config_sha256"][:12],
                                                  T_SOURCE["questions_sha256"][:12],
                                                  CHECKPOINT["sha256_of_rl_agent_config"][:12], QSHA[:12]))

METRICS = MetricsHook()
ROUTER = Router(
    # "./": 저장소 루트가 아닌 곳에서 띄우면 Hub 다운로드를 시도하는 대신 "Local model path not found"로 멈춘다
    models={"multilingual": "./" + FT_PATH, "english": "./models/laya"},
    default="multilingual",
    device=os.environ.get("LAYA_DEVICE", "mps"),
    max_loaded=2,
    hooks=[NfcRedactHook(),
           ShadowAuditHook(SHADOW_LOG, {"multilingual": CHECKPOINT["sha256_of_rl_agent_config"], "english": BASE},
                           route, QSHA),
           METRICS],
)
ROUTER.preload(["multilingual"])   # english는 첫 요청 때 lazy 로드
app = create_app(router=ROUTER)

# laya.serve의 bearer 검사는 create_app 안의 클로저라 import할 수 없어 같은 규칙(bytes 비교, 401)을 옮겼다.
API_KEY = os.environ.get("LAYA_API_KEY") or None
EXPECTED_AUTH = ("Bearer " + API_KEY).encode("utf-8", "surrogateescape") if API_KEY else b""


def check_bearer(authorization):
    supplied = (authorization or "").encode("utf-8", "surrogateescape")
    if API_KEY and not hmac.compare_digest(supplied, EXPECTED_AUTH):
        raise HTTPException(status_code=401, detail="invalid or missing bearer token")


INFER_LOCK = threading.Lock()   # /poc/decide끼리 직렬화. /v1/systemone은 create_app의 단일 worker를 쓴다


@app.post("/poc/decide")
def poc_decide(body: dict = Body(...), authorization: Optional[str] = Header(default=None)):
    check_bearer(authorization)
    text = body.get("utterance")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=422, detail="'utterance' must be a non-empty string")
    state = {"utterance": text}
    _check_request_limits(state, QUESTIONS)
    min_confidence = _validate_min_confidence(body)
    lang = _validate_language_param(body, "lang") if "lang" in body else "ko"   # 한국어 채널 고정, null이면 감지(07 §4)
    model = body.get("model") or "auto"
    if model not in ("auto", "multilingual", "english"):
        raise HTTPException(status_code=422, detail="model must be auto, multilingual or english")
    t0 = time.perf_counter()
    with INFER_LOCK:
        result = ROUTER.predict(state, QUESTIONS, lang=lang, model=None if model == "auto" else model,
                                min_confidence=T if min_confidence is None else min_confidence)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    action, detail = route(result["answers"], result["routing"]["model"])
    return {"answers": result["answers"], "routing": result["routing"], "usage": result["usage"],
            "policy": {"action": action, **detail}, "thresholds": {"T": T}, "elapsed_ms": round(elapsed_ms, 1),
            "checkpoint": CHECKPOINT if result["routing"]["model"] == CALIBRATED_MODEL
            else {"path": "models/laya", "base": BASE},
            "questions_sha256": QSHA, "schema_version": "router_v1"}


def read_shadow():
    records = []
    if SHADOW_LOG.exists():
        for line in SHADOW_LOG.read_text(encoding="utf-8").splitlines():
            try:
                records.append(json.loads(line))
            except ValueError:   # 다른 스레드가 append 중인 마지막 줄
                pass
    return records


@app.get("/poc/shadow")
def poc_shadow(limit: int = Query(50, ge=1, le=500), authorization: Optional[str] = Header(default=None)):
    check_bearer(authorization)
    records = read_shadow()
    decided = [r["policy"] for r in records if r.get("policy")]
    actions = Counter(p["action"] for p in decided)
    gates = Counter(a["abstention"] for r in records for a in (r.get("answers") or {}).values() if a.get("abstention"))
    elapsed = sorted(r["elapsed_ms"] for r in records if r.get("elapsed_ms") is not None)
    return {"records": records[-limit:],
            "counters": {"total": len(records),
                         "errors": sum(1 for r in records if r.get("error")),
                         "actions": {"ROUTE": actions["ROUTE"], "FALLBACK": actions["FALLBACK"]},
                         "fallback_rate": round(actions["FALLBACK"] / len(decided), 4) if decided else None,
                         "abstained": {"count": gates["abstained"],
                                       "rate": round(gates["abstained"] / sum(gates.values()), 4) if gates else None},
                         "by_domain": dict(Counter(p["domain"] for p in decided)),
                         "elapsed_ms": {"p50": percentile(elapsed, 0.5), "p95": percentile(elapsed, 0.95)}}}


@app.get("/poc/meta")
def poc_meta(authorization: Optional[str] = Header(default=None)):
    check_bearer(authorization)
    return {"laya_version": laya.__version__, "schema_version": "router_v1", "schema_path": SCHEMA_PATH,
            "questions_sha256": QSHA, "checkpoint": CHECKPOINT,
            "checkpoints": {"multilingual": FT_PATH + " (ft-v1)", "english": "models/laya (base %s)" % BASE[:7]},
            "thresholds": {"T": T, "source": T_SOURCE}, "handlers": HANDLER,
            "models_loaded": ROUTER.loaded, "metrics": METRICS.snapshot()}


app.mount("/poc/ui", StaticFiles(directory=ROOT / "poc/service/ui", html=True), name="poc-ui")
