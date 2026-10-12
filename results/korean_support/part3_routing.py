"""PART 3 of the Korean-support audit: routing robustness. No checkpoint is loaded:
only `laya.lang.analyse` and `laya.Router().route` (which never loads or runs a model).

    source env.sh && .venv/bin/python results/korean_support/part3_routing.py

Writes results/korean_support/part3_routing_battery.json and part3_routing_battery.md.
`want` is this audit's judgement of the checkpoint that can read the decision-relevant text:
"multilingual" when that text is Korean, "english" for the English control, "either" when the
content is English with a stray Korean word, or nothing a checkpoint is known to read.
"""
import json
import unicodedata
from pathlib import Path

import laya
from laya import lang

OUT = Path(__file__).resolve().parent

EN_TEMPLATE = ("Ticket #4411\nChannel: web chat\nAgent notes: Customer asked about a delayed order. Please check "
               "the shipping status with the carrier, confirm the delivery address on file, and reply to the "
               "customer within 24 hours with the tracking number and a short apology for the delay.\n"
               "Customer message: ")
KO_MSG_MED = "주문한 지 2주가 지났는데 아직 배송이 안 됐어요"

CASES = [
    # (group, label, state, want)
    ("pure_ko", "long request", "같은 달 요금이 두 번 빠져나갔어요. 중복 결제된 금액 환불 부탁드립니다.", "multilingual"),
    ("pure_ko", "short complaint", "앱이 자꾸 튕겨요", "multilingual"),
    ("pure_ko", "login", "로그인이 안 돼요. 비밀번호를 바꿨는데도 계속 오류가 납니다.", "multilingual"),
    ("pure_ko", "dict state", {"message": "다음 달부터 요금제를 해지하고 싶습니다."}, "multilingual"),
    ("pure_ko", "NFD (decomposed jamo)", unicodedata.normalize("NFD", "환불해 주세요"), "multilingual"),
    ("ko_en_terms", "API + status code", "결제 API가 500 에러를 냅니다", "multilingual"),
    ("ko_en_terms", "OAuth error", "로그인 시 OAuth redirect_uri mismatch 에러가 발생합니다", "multilingual"),
    ("ko_en_terms", "Stripe webhook", "Stripe webhook이 timeout 나요", "multilingual"),
    ("ko_en_terms", "Kubernetes", "Kubernetes pod가 CrashLoopBackOff 상태예요", "multilingual"),
    ("ko_en_terms", "AWS S3", "AWS S3 bucket policy 설정 문의드립니다", "multilingual"),
    ("ko_en_terms", "product name", "iPhone 15 Pro Max 환불", "multilingual"),
    ("ko_en_terms", "brand (upstream test)", "Samsung Galaxy 주문이 아직 안 왔어요", "multilingual"),
    ("ko_en_terms", "pasted JS error", "TypeError: Cannot read properties of undefined (reading 'map') 이 에러 왜 나요?",
     "multilingual"),
    ("ko_num_email_url", "order number", "주문번호 20231005-77 확인 부탁드려요", "multilingual"),
    ("ko_num_email_url", "phone number", "010-1234-5678로 연락 주세요", "multilingual"),
    ("ko_num_email_url", "email address", "kim.minsu@example.co.kr 로 영수증 보내주세요", "multilingual"),
    ("ko_num_email_url", "receipt URL", "영수증: https://billing.example.com/invoices/INV-2024-000123/download?format=pdf",
     "multilingual"),
    ("ko_num_email_url", "refund + URL", "환불 요청: https://shop.example.com/orders/ABCD-1234?ref=newsletter",
     "multilingual"),
    ("mostly_en", "thanks in Korean", "Please check my order, 감사합니다", "either"),
    ("mostly_en", "one Korean noun", "I was charged twice for my subscription, 환불 please", "either"),
    ("mostly_en", "Korean key term", "Hi team, the 정산 report for March is wrong", "either"),
    ("mostly_en", "one Korean word, short", "The 결제 failed again", "either"),
    ("romanized", "romanized 1", "gyeoljega du beon dwaesseoyo", "either"),
    ("romanized", "romanized 2", "hwanbul hae juseyo", "either"),
    ("romanized", "romanized 3", "annyeonghaseyo, jumun beonho hwagin buthakdeuryeoyo", "either"),
    ("emoji_chat", "Korean + emoji", "환불해주세요 😡😡", "multilingual"),
    ("emoji_chat", "jamo crying", "ㅠㅠ", "multilingual"),
    ("emoji_chat", "jamo laugh + ok", "ㅋㅋㅋ ok", "multilingual"),
    ("emoji_chat", "emoji only (control)", "😡😡😡", "either"),
    ("very_short", "two syllables", "환불", "multilingual"),
    ("very_short", "jamo abbreviation", "ㅇㅋ", "multilingual"),
    ("very_short", "one syllable", "네", "multilingual"),
    ("very_short", "one syllable + OK", "네 OK", "multilingual"),
    ("very_short", "OK + two syllables (tie)", "OK 감사", "multilingual"),
    ("hanja_mixed", "headline, 2 Hanja", "北 미사일 발사에 美 강력 규탄", "multilingual"),
    ("hanja_mixed", "headline, Hanja abbreviations", "與野, 추경 합의 불발", "multilingual"),
    ("hanja_mixed", "Hanja only (Korean)", "大韓民國 憲法 第1條", "multilingual"),
    ("structured", "dict: EN wrapper + 5-syllable message",
     {"ticket_id": "TCK-88213", "channel": "web chat",
      "agent_notes": "Customer asked about a delayed order. Please check shipping status.",
      "message": "환불해 주세요"}, "multilingual"),
    ("structured", "dict: EN wrapper + 19-syllable message",
     {"ticket_id": "TCK-88213", "channel": "web chat",
      "agent_notes": "Customer asked about a delayed order. Please check shipping status.",
      "message": KO_MSG_MED}, "multilingual"),
    ("structured", "turns: EN agent + short KO user",
     [{"role": "agent", "text": "Hello! Thanks for contacting support. How can I help you today?"},
      {"role": "user", "text": "환불 부탁드려요"}], "multilingual"),
    ("structured", "plain string: long EN template + 19-syllable KO", EN_TEMPLATE + KO_MSG_MED, "multilingual"),
    ("structured", "same content as dict", {"ticket": EN_TEMPLATE.rstrip(": \n"), "customer_message": KO_MSG_MED},
     "multilingual"),
    ("structured", "Korean keys, English values", {"고객_메시지": "Please cancel my plan"}, "english"),
    ("control", "Japanese", "二重に請求されました。返金をお願いします。", "multilingual"),
    ("control", "Chinese", "客户被重复扣款要求退款", "multilingual"),
    ("control", "English", "I was charged twice, please refund the duplicate.", "english"),
]


def letters(state):
    text = lang.state_text(state)
    counts = lang._script_counts(text)
    total = sum(counts.values())
    return {"hangul_letters": counts.get("hangul", 0), "latin_letters": counts.get("latin", 0),
            "han_letters": counts.get("han", 0), "all_letters": total,
            "hangul_share": round(counts.get("hangul", 0) / total, 4) if total else 0.0,
            "non_latin_words": lang._non_latin_words(text)}


def run_case(group, label, state, want, routers):
    det = lang.analyse(state)
    row = {"group": group, "label": label, "state": state, "want": want,
           "analyse": {k: det[k] for k in ("script", "language", "is_english", "language_undecided",
                                           "non_latin_fraction", "mixed_segment")},
           "letters": letters(state)}
    for name, r in routers.items():
        d = r.route(state)
        row["route_" + name] = {"model": d["model"], "reason": d["reason"]}
    got = row["route_default_english"]["model"]
    alt = row["route_default_multilingual"]["model"]
    if want == "either":
        row["verdict"] = "ok (either)" if got == alt else "default-dependent"
    elif got == want:
        row["verdict"] = "ok" if alt == want else "ok only with default=english"
    else:
        row["verdict"] = "FAIL" if alt != want else "FAIL with stock default (ok with default=multilingual)"
    return row


def sweep():
    """Smallest number of Hangul syllables that moves an English plain string to multilingual."""
    en_words = ("please check the status of the order for this account and tell me what happened with the "
                "payment that was made last week because it has not arrived yet and we are waiting").split()
    ko = "중복결제된금액을오늘안에환불해주시기바랍니다확인부탁드립니다감사합니다그리고영수증도다시보내주세요빠른답변기다리겠습니다정말감사합니다"
    r = laya.Router()
    out = []
    for target in (10, 20, 40, 80, 160, 320):
        words, n = [], 0
        while n < target:
            w = en_words[len(words) % len(en_words)]
            words.append(w)
            n += len(w)
        en = " ".join(words)
        L = sum(ch.isalpha() for ch in en)
        flip = None
        for h in range(1, len(ko) + 1):
            s = en + " " + ko[:h]
            if r.route(s)["model"] == "multilingual":
                flip = h
                break
        out.append({"latin_letters": L, "min_hangul_syllables_to_route_multilingual": flip,
                    "hangul_share_at_flip": round(flip / (L + flip), 4) if flip else None})
    return out


def main():
    routers = {"default_english": laya.Router(), "default_multilingual": laya.Router(default="multilingual")}
    rows = [run_case(*c, routers=routers) for c in CASES]
    mitigation = {name: laya.Router().route(state, lang="ko")["model"] for name, state in
                  (("romanized 1", "gyeoljega du beon dwaesseoyo"), ("Stripe webhook", "Stripe webhook이 timeout 나요"))}
    res = {"laya_version": laya.__version__, "n_cases": len(rows), "rows": rows, "plain_string_sweep": sweep(),
           "mitigation_lang_ko": mitigation,
           "thresholds": {"NON_LATIN_FRACTION": lang.NON_LATIN_FRACTION,
                          "NON_LATIN_MIN_FRACTION": lang.NON_LATIN_MIN_FRACTION,
                          "NON_LATIN_MIN_LETTERS": lang.NON_LATIN_MIN_LETTERS}}
    (OUT / "part3_routing_battery.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n",
                                                    encoding="utf-8")

    def show(state):
        s = json.dumps(state, ensure_ascii=False) if not isinstance(state, str) else state
        s = s.replace("\n", "⏎").replace("|", "\\|")
        return s if len(s) <= 70 else s[:67] + "..."

    md = ["| # | group | input | script | lang | is_en | hangul/letters | route (default english) | reason | default=multilingual | verdict |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        a, lt = r["analyse"], r["letters"]
        md.append("| %d | %s | %s | %s | %s | %s | %d/%d (%.2f) | **%s** | %s | %s | %s |" % (
            i, r["group"], show(r["state"]), a["script"], a["language"] or "-", a["is_english"],
            lt["hangul_letters"], lt["all_letters"], lt["hangul_share"], r["route_default_english"]["model"],
            r["route_default_english"]["reason"].replace("|", "\\|")[:110], r["route_default_multilingual"]["model"],
            r["verdict"]))
    (OUT / "part3_routing_battery.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(json.dumps(res["plain_string_sweep"], indent=1))
    print(json.dumps(mitigation))


if __name__ == "__main__":
    main()
