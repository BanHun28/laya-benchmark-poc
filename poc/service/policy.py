"""05 §5 정책 레이어: 단일 T로 ROUTE / FALLBACK. 도메인별 T는 E3에서 과적합으로 기각돼 두지 않는다."""
from laya.confidence import answer_confidence_value

T = 0.907
# T의 출처와 유효 범위. 체크포인트나 질문 스키마가 바뀌면 T는 무효이므로(05 §5) app.py가 기동 시 대조한다.
T_SOURCE = {
    "report": "results/P4/metrics/full_20261003-1156_coverage_2917.md",
    "rule": "dev-1459에서 오류 <= 0.05인 최대 coverage(0.901) 지점 T = 0.907; test-1458에 적용 시 coverage 0.923, 오류 0.042",
    "checkpoint": "poc/finetune/ckpt_domain8_v1",
    "rl_agent_config_sha256": "3270d480d05a68454004022b90e80f422c8b364ba1bd90ce43b004cde3ab9638",
    "weights_sha256": "b0609f547a2b097bdff54fc44bb9822852e49e147271c21f0a2b3ac21dce4446",
    "questions_sha256": "a7f2f6b88db01ec297afb64da2434f0b2376fa46d341b2c8fec18998b719ec54",
}
CALIBRATED_MODEL = "multilingual"   # app.py가 ft-v1을 올리는 Router 슬롯. 다른 체크포인트의 확률에는 T가 맞지 않는다
HANDLER = {"productivity": "calendar-svc", "media": "media-svc", "smart_home": "iot-svc", "info_qa": "qa-svc",
           "communication": "comm-svc", "lifestyle": "lifestyle-svc", "transport": "transport-svc",
           "general": "chat-svc"}


def route(answers, model):
    """`answers`는 router_v1 응답의 answers, `model`은 routing.model. (action, detail)을 돌려준다."""
    d = answers["domain"]
    p, top, gate = answer_confidence_value(d), d.get("choice"), d.get("abstention")
    if model != CALIBRATED_MODEL:
        return "FALLBACK", {"domain": top, "handler": None, "p": p, "reason": "T not valid for %s" % model}
    if gate not in (None, "passed"):   # abstained / unevaluated를 통과로 읽지 않는다
        return "FALLBACK", {"domain": top, "handler": None, "p": p, "reason": gate}
    if p is None or p < T:             # min_confidence 없이 온 NaN은 answer_confidence_value가 None으로 준다
        return "FALLBACK", {"domain": top, "handler": None, "p": p,
                            "reason": "below T" if p is not None else "unevaluated"}
    return "ROUTE", {"domain": top, "handler": HANDLER[top], "p": p, "reason": "passed"}
