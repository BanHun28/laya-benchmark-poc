"""Router schema v2 dev round: cross-variant tables from the laya-evals reports in results/C/schemas_v2 (no model call).

Every number comes from the reports through scripts/metrics_extra.py (load_report re-checks each report against its
dataset bytes and its own overall block). Rows are aligned across variants by state (unique in this set).

    source env.sh && .venv/bin/python results/C/C_schema_v2_analyze.py 20261002
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from metrics_extra import group_metrics, load_report, mcnemar_exact  # noqa: E402

S = ROOT / "results/C/schemas_v2"
B_REF = ROOT / "results/B/20261002-1643_multilingual_ko_massive_domain_8.json"
VARIANTS = ["v1", "v2a", "v2b", "v2c", "v2c_h512", "v2d", "v2e"]
SAME_CONTRACT = ["v2a", "v2c", "v2d"]  # 8 options, default head budget: eligible as router_v2 without other changes
COARSE = {"productivity": "assistant_tasks", "communication": "assistant_tasks", "media": "media", "smart_home": "smart_home",
          "info_qa": "info_qa", "lifestyle": "daily_life", "transport": "daily_life"}
DOMAINS = ["productivity", "media", "smart_home", "info_qa", "communication", "lifestyle", "transport", "general"]
GATE_T = (0.5, 0.6, 0.7, 0.8, 0.9, 0.95)


def path_of(tag):
    paths = sorted(p for p in S.glob("*_multilingual_router_%s.json" % tag))
    assert paths, tag
    return paths[-1]


def tag_of(v, general=False):
    base = v.replace("_h512", "")
    return base + "_dev" + ("_general" if general else "") + ("_h512" if v.endswith("_h512") else "")


def f3(x):
    return "-" if x is None else "%.3f" % x


def fp(p):
    return "%.4f" % p if p >= 0.001 else "%.1e" % p


def scen(c):
    return next(t[9:] for t in c["tags"] if t.startswith("scenario:"))


def paired(a, b):
    """a, b: aligned case lists. b_ = a right & b wrong, c_ = a wrong & b right."""
    b_ = sum(x["correct"] and not y["correct"] for x, y in zip(a, b))
    c_ = sum(y["correct"] and not x["correct"] for x, y in zip(a, b))
    return b_, c_, mcnemar_exact(b_, c_)


def posthoc(c, coarse=False):
    """Decode-time comparator from an 8-option run: drop `general`, optionally sum probabilities into coarse classes."""
    probs = Counter()
    for k, v in c["probs"].items():
        if k != "general":
            probs[COARSE[k] if coarse else k] += v
    gold = COARSE[c["gold"]] if coarse else c["gold"]
    pred = max(probs, key=probs.get)
    return dict(c, gold=gold, pred=pred, correct=pred == gold)


def auroc_low_conf(pos, neg):
    """P(conf of a gold-general row < conf of a non-general row), ties half: how well low confidence flags general."""
    pos, neg = np.asarray(pos)[:, None], np.asarray(neg)[None, :]
    return float((pos < neg).mean() + 0.5 * (pos == neg).mean())


def dist(x):
    q = np.percentile(x, [0, 25, 50, 75, 100])
    return {"mean": float(np.mean(x)), "min": q[0], "p25": q[1], "median": q[2], "p75": q[3], "max": q[4]}


def main(date):
    R = {v: load_report(path_of(tag_of(v))) for v in VARIANTS}
    G = {v: load_report(path_of(tag_of(v, True))) for v in ("v2b", "v2e")}
    build = json.loads((S / "BUILD.json").read_text(encoding="utf-8"))
    for r in list(R.values()) + list(G.values()):
        assert {c["split"] for c in r["cases"]} == {"dev"} and len({c["skey"] for c in r["cases"]}) == len(r["cases"])
    v1 = {c["skey"]: c for c in R["v1"]["cases"]}
    v2a = {c["skey"]: c for c in R["v2a"]["cases"]}
    out = {"reports": {v: r["path"] for v, r in {**R, **{v + "_general": g for v, g in G.items()}}.items()}, "variants": {}}
    L = ["# Router schema v2: dev 라운드 (ko_massive_domain_8 dev 250행, multilingual, CPU fp32) (%s)" % date, "",
         "생성: `results/C/C_schema_v2_analyze.py` (표). 원천: `results/C/schemas_v2/*_multilingual_router_*.json` (laya-evals 리포트), "
         "지표는 `scripts/metrics_extra.py`의 `load_report`/`group_metrics`/`mcnemar_exact`. 변형 정의·해시·head budget은 "
         "`results/C/schemas_v2/BUILD.md`. 런 카드 `results/C/C_%s.md`." % date, "",
         "**주의: 선택과 측정이 모두 같은 dev 절반(n=250)에서 이뤄졌다.** 여러 변형 중 최고를 고르면 그 변형의 dev 수치는 "
         "낙관적으로 편향된다(winner's curse). n=250의 accuracy 95% CI 폭은 약 ±0.06이라 0.05 미만 차이는 구분하지 못한다. "
         "test 절반(250행)은 열지 않았고, 고른 router_v2를 나중에 한 번만 잰다(05 §6 P1 절차 7).", ""]

    # ---- 1. main table
    L += ["## 1. 변형별 요약", "",
          "Δ와 McNemar는 v1과 같은 행(state)끼리. v2b·v2e는 gold general 30행을 빼고 220행만 채점하므로 v1도 그 220행으로 맞춘다. "
          "v2e는 5-class라 정답 정의가 다르다(공정 비교는 §2). b = v1 정답 & 변형 오답, c = v1 오답 & 변형 정답.", "",
          "| variant | 옵션 | n scored | accuracy [95% CI] | macro-F1 (gold) | v1 acc (같은 행) | Δ vs v1 | McNemar b/c, p | "
          "smart_home 예측 (gold) | general 예측 (gold) | 오답 평균 conf | 정답 평균 conf | ECE | argmax = v1 |",
          "|" + "---|" * 14]
    for v in VARIANTS:
        cs = R[v]["cases"]
        m = group_metrics(cs, 1000, 13)
        base = [v1[c["skey"]] for c in cs]
        acc1 = float(np.mean([c["correct"] for c in base]))
        b_, c_, p = paired(base, cs)
        wrong = [c["conf"] for c in cs if not c["correct"]]
        right = [c["conf"] for c in cs if c["correct"]]
        pc, gc = Counter(c["pred"] for c in cs), Counter(c["gold"] for c in cs)
        agree = float(np.mean([c["pred"] == x["pred"] for c, x in zip(cs, base)])) if v != "v2e" else None
        row = {"options": len(cs[0]["opts"]), "n": len(cs), "accuracy": m["accuracy"], "accuracy_ci": m["accuracy_ci"],
               "macro_f1_gold": m["macro_f1_gold"], "v1_accuracy_same_rows": acc1, "delta_vs_v1": m["accuracy"] - acc1,
               "mcnemar_vs_v1": [b_, c_, p], "pred_counts": dict(pc.most_common()), "gold_counts": dict(gc),
               "wrong_mean_conf": float(np.mean(wrong)), "right_mean_conf": float(np.mean(right)), "ece": m["ece"],
               "argmax_agreement_v1": agree, "recall": m["recall"], "confusions_top5": m["confusions_top5"]}
        out["variants"][v] = row
        L.append("| %s | %d | %d | %s [%s, %s] | %s | %s | %+.3f | %d/%d, %s | %d (%d) | %s | %s | %s | %s | %s |" % (
            v, row["options"], row["n"], f3(m["accuracy"]), *map(f3, m["accuracy_ci"]), f3(m["macro_f1_gold"]), f3(acc1),
            row["delta_vs_v1"], b_, c_, fp(p), pc.get("smart_home", 0), gc.get("smart_home", 0),
            "%d (%d)" % (pc.get("general", 0), gc.get("general", 0)) if "general" in cs[0]["opts"] else "옵션 없음",
            f3(row["wrong_mean_conf"]), f3(row["right_mean_conf"]), f3(m["ece"]), f3(agree)))
    L += ["", "- v2c는 기본 head budget(256)에서 옵션당 30토큰으로 잘린다(예시 대부분과 smart_home의 \"(오디오 재생·음량은 제외)\"가 "
          "모델에 보이지 않음, BUILD.md). v2c_h512는 같은 파일을 요청별 `head_max_len=512`로 돌린 진단 런이다(배포 설정 변경이 "
          "필요하므로 router_v2 후보 자격 없음). 512에서도 토크나이저 단계의 옵션당 48토큰 상한 때문에 smart_home 예시와 "
          "productivity 둘째 예시는 잘린다.", ""]

    # ---- 2. decode-time comparators for the schemas that drop general / merge classes
    L += ["## 2. v2b·v2e의 공정 비교: 같은 220행에서 8옵션 런을 디코드 단계에서 바꾼 것과 비교", "",
          "스키마에서 general을 빼거나 클래스를 합치면 정답률은 정의상 오른다. 그 상승이 스키마 변경 덕인지 보려면 8옵션 런의 확률에서 "
          "general을 지우고 argmax(= mask)하거나, 남은 확률을 coarse 클래스별로 더해 argmax(= coarse 합산)한 값과 비교해야 한다. "
          "확률은 리포트의 소수 4자리 값이다.", "",
          "| 스키마 런 | 비교 대상 (같은 220행) | acc 스키마 | acc 비교 대상 | Δ (스키마 − 비교) | McNemar b/c, p (b = 비교 정답 & 스키마 오답) |",
          "|---|---|---|---|---|---|"]
    out["posthoc"] = {}
    for v, coarse in (("v2b", False), ("v2e", True)):
        cs = R[v]["cases"]
        for src_name, src in (("v2a", v2a), ("v1", v1)):
            comp = [posthoc(src[c["skey"]], coarse) for c in cs]
            assert all(x["gold"] == c["gold"] for x, c in zip(comp, cs))
            b_, c_, p = paired(comp, cs)
            a_s, a_c = float(np.mean([c["correct"] for c in cs])), float(np.mean([c["correct"] for c in comp]))
            label = "%s %s" % (src_name, "coarse 합산 (general 제외)" if coarse else "general mask")
            out["posthoc"]["%s~%s" % (v, label)] = {"acc_schema": a_s, "acc_posthoc": a_c, "b": b_, "c": c_, "p": p,
                                                   "recall_posthoc": group_metrics(comp)["recall"]}
            L.append("| %s | %s | %s | %s | %+.3f | %d/%d, %s |" % (v, label, f3(a_s), f3(a_c), a_s - a_c, b_, c_, fp(p)))
    L.append("")

    # ---- 3. gold-general rows when the schema has no general option
    L += ["## 3. gold general 30행: general 옵션이 없을 때 confidence 게이트가 잡는가", "",
          "general 파일은 채점 불가 행이다(정답 옵션이 없으므로 리포트의 정확도 0은 구성상 값). 게이트 표: T 미만이면 FALLBACK. "
          "`general 잡힘` = gold general 행 중 conf < T 비율, `비general 정답 보류` = 채점 220행 중 정답인데 conf < T(잃는 coverage), "
          "`비general 오답 보류` = 오답 중 conf < T(걸러지는 오류), `ROUTE 정확도` = conf ≥ T인 비general 행의 정확도. "
          "AUROC = gold general 행의 conf가 비general 행보다 낮을 확률(0.5 = 구분 못함).", ""]
    out["general_rows"] = {}
    for v in ("v2b", "v2e"):
        g = G[v]["cases"]
        cs = R[v]["cases"]
        gconf = np.array([c["conf"] for c in g])
        ok = np.array([c["conf"] for c in cs if c["correct"]])
        bad = np.array([c["conf"] for c in cs if not c["correct"]])
        allc = np.array([c["conf"] for c in cs])
        corr = np.array([c["correct"] for c in cs], float)
        d_g, d_ok, d_bad = dist(gconf), dist(ok), dist(bad)
        c1 = np.array([c["conf"] for c in R["v1"]["cases"]])
        k1 = np.array([c["correct"] for c in R["v1"]["cases"]], float)
        gate = [{"T": t, "general_caught": float((gconf < t).mean()), "correct_deferred": float((ok < t).mean()),
                 "wrong_deferred": float((bad < t).mean()), "routed_n": int((allc >= t).sum()),
                 "routed_accuracy": float(corr[allc >= t].mean()) if (allc >= t).any() else None,
                 # all 250 dev rows: uncaught gold-general rows are routed to a wrong handler
                 "routed_n_all": int((allc >= t).sum() + (gconf >= t).sum()),
                 "routed_accuracy_all": float(corr[allc >= t].sum() / max(1, (allc >= t).sum() + (gconf >= t).sum())),
                 "v1_routed_n": int((c1 >= t).sum()), "v1_routed_accuracy": float(k1[c1 >= t].mean())} for t in GATE_T]
        au = auroc_low_conf(gconf, allc)
        out["general_rows"][v] = {"n": len(g), "pred_counts": dict(Counter(c["pred"] for c in g).most_common()),
                                  "conf_general": d_g, "conf_nongeneral_correct": d_ok, "conf_nongeneral_wrong": d_bad,
                                  "gate": gate, "auroc_low_conf": au}
        L += ["### %s (gold general %d행)" % (v, len(g)), "",
              "- 예측 클래스: " + ", ".join("%s %d" % kv for kv in out["general_rows"][v]["pred_counts"].items()),
              "- answer_confidence (mean / min / p25 / median / p75 / max): general 행 %s; 비general 정답 %s; 비general 오답 %s" % tuple(
                  " / ".join(f3(d[k]) for k in ("mean", "min", "p25", "median", "p75", "max")) for d in (d_g, d_ok, d_bad)),
              "- AUROC(낮은 conf로 general 식별): %.3f" % au, "",
              "| T | general 잡힘 | 비general 정답 보류 | 비general 오답 보류 | ROUTE n (220 중) | ROUTE 정확도 (220) "
              "| ROUTE n / 정확도 (250, 놓친 general 포함) | 참고: v1 같은 T ROUTE n / 정확도 (250) |", "|---|---|---|---|---|---|---|---|"]
        L += ["| %.2f | %s | %s | %s | %d | %s | %d / %s | %d / %s |" % (
            x["T"], f3(x["general_caught"]), f3(x["correct_deferred"]), f3(x["wrong_deferred"]), x["routed_n"],
            f3(x["routed_accuracy"]), x["routed_n_all"], f3(x["routed_accuracy_all"]), x["v1_routed_n"],
            f3(x["v1_routed_accuracy"])) for x in gate]
        L.append("")
    gen8 = {v: [c for c in R[v]["cases"] if c["gold"] == "general"] for v in ("v1", "v2a", "v2c", "v2d")}
    L += ["비교: general 옵션이 있는 변형에서 gold general 30행의 recall과 예측: " + "; ".join(
        "%s %d/%d (%s)" % (v, sum(c["correct"] for c in cs), len(cs), ", ".join("%s %d" % kv for kv in Counter(c["pred"] for c in cs).most_common(4)))
        for v, cs in gen8.items()), ""]

    # ---- 4. per-class recall
    L += ["## 4. 클래스별 recall (dev)", "", "| gold | n | " + " | ".join(v for v in VARIANTS if v != "v2e") + " |",
          "|---|---|" + "---|" * (len(VARIANTS) - 1)]
    for d in DOMAINS:
        cells = []
        for v in VARIANTS:
            if v == "v2e":
                continue
            rec = out["variants"][v]["recall"].get(d)
            cells.append("%d/%d (%s)" % (rec[0], rec[1], f3(rec[0] / rec[1])) if rec else "-")
        n = out["variants"]["v1"]["recall"][d][1]
        L.append("| %s | %d | %s |" % (d, n, " | ".join(cells)))
    L += ["", "v2e 5-class recall과 비교 대상(같은 220행, coarse 정답):", "",
          "| coarse gold | n | v2e | v2a coarse 합산 | v1 coarse 합산 |", "|---|---|---|---|---|"]
    rv = out["variants"]["v2e"]["recall"]
    ra, r1 = out["posthoc"]["v2e~v2a coarse 합산 (general 제외)"]["recall_posthoc"], out["posthoc"]["v2e~v1 coarse 합산 (general 제외)"]["recall_posthoc"]
    for k in rv:
        L.append("| %s | %d | %s | %s | %s |" % (k, rv[k][1], *("%d/%d (%s)" % (r[k][0], r[k][1], f3(r[k][0] / r[k][1])) for r in (rv, ra, r1))))
    L.append("")

    # ---- 5. per-scenario accuracy
    scenarios = sorted({scen(c) for c in R["v1"]["cases"]}, key=lambda s: (np.mean([c["correct"] for c in R["v1"]["cases"] if scen(c) == s]), s))
    L += ["## 5. 원 MASSIVE scenario별 정확도 (dev; Track B §5의 실패 패턴 추적)", "",
          "v2b는 general 행이 없고, v2e는 coarse 정답 기준이다. 오른쪽 열은 v1 → v2a에서 가장 많이 간 오답 도메인.", "",
          "| scenario | 도메인 | n | " + " | ".join(VARIANTS) + " | v2a 오답 예측 |", "|---|---|---|" + "---|" * (len(VARIANTS) + 1)]
    out["by_scenario"] = {}
    for s in scenarios:
        row, cells = {}, []
        for v in VARIANTS:
            cs = [c for c in R[v]["cases"] if scen(c) == s]
            row[v] = [sum(c["correct"] for c in cs), len(cs)]
            cells.append("%d/%d" % tuple(row[v]) if cs else "-")
        wrong = Counter(c["pred"] for c in R["v2a"]["cases"] if scen(c) == s and not c["correct"])
        out["by_scenario"][s] = row
        dom = next(c["gold"] for c in R["v1"]["cases"] if scen(c) == s)
        L.append("| %s | %s | %d | %s | %s |" % (s, dom, row["v1"][1], " | ".join(cells), ", ".join("%s %d" % kv for kv in wrong.most_common(3)) or "-"))
    L.append("")

    # ---- 6. confusions
    L += ["## 6. top 혼동 (gold→pred ×n)", ""]
    L += ["- %s: %s" % (v, ", ".join("%s→%s ×%d" % tuple(x) for x in out["variants"][v]["confusions_top5"])) for v in VARIANTS]
    L += ["", "smart_home 흡수원 추적: smart_home으로 간 오답(gold별)과 audio scenario 행의 예측", "",
          "| variant | →smart_home 오답 합계 | gold별 | audio 행 예측 |", "|---|---|---|---|"]
    for v in VARIANTS:
        sink = Counter(c["gold"] for c in R[v]["cases"] if c["pred"] == "smart_home" and not c["correct"])
        audio = Counter(c["pred"] for c in R[v]["cases"] if scen(c) == "audio")
        out["variants"][v]["smart_home_sink"] = dict(sink.most_common())
        L.append("| %s | %d | %s | %s |" % (v, sum(sink.values()), ", ".join("%s %d" % kv for kv in sink.most_common()),
                                           ", ".join("%s %d" % kv for kv in audio.most_common())))
    L.append("")

    # ---- 7. order effect v2a -> v2d
    a, d = R["v2a"]["cases"], R["v2d"]["cases"]
    assert [c["skey"] for c in a] == [c["skey"] for c in d]
    b_, c_, p = paired(a, d)
    ca, cd = Counter(c["pred"] for c in a), Counter(c["pred"] for c in d)
    moved = Counter((x["pred"], y["pred"]) for x, y in zip(a, d) if x["pred"] != y["pred"])
    out["order_effect"] = {"agreement": float(np.mean([x["pred"] == y["pred"] for x, y in zip(a, d)])), "b": b_, "c": c_, "p": p,
                           "pred_v2a": dict(ca), "pred_v2d": dict(cd), "moved": [[x, y, k] for (x, y), k in moved.most_common()]}
    L += ["## 7. 순서 효과: v2a → v2d (같은 설명, general 맨 앞·smart_home 맨 뒤)", "",
          "- argmax 일치 %s, McNemar b/c = %d/%d (b = v2a 정답 & v2d 오답), p = %s" % (f3(out["order_effect"]["agreement"]), b_, c_, fp(p)),
          "- 예측 수 v2a → v2d: " + ", ".join("%s %d→%d" % (k, ca.get(k, 0), cd.get(k, 0)) for k in DOMAINS),
          "- 바뀐 예측 (v2a→v2d ×n): " + (", ".join("%s→%s ×%d" % (x, y, k) for (x, y), k in moved.most_common(8)) or "없음"),
          "- 옵션 순서 자체의 효과는 C1(`results/C/C1_option_order_%s.md`)의 slot 분석이 같은 질문을 순열 전체에서 본다." % date, ""]

    # ---- 8. parity of the v1 rerun with Track B
    ref = load_report(B_REF)
    refd = {c["skey"]: c for c in ref["cases"] if c["split"] == "dev"}
    pairs = [(c, refd[c["skey"]]) for c in R["v1"]["cases"]]
    agree = sum(x["pred"] == y["pred"] for x, y in pairs)
    dp = max(abs(x["probs"][k] - y["probs"][k]) for x, y in pairs for k in y["probs"])
    out["v1_parity_trackB"] = {"reference": str(B_REF.relative_to(ROOT)), "n": len(pairs), "argmax_agreement": agree, "max_abs_dp": dp,
                               "acc_ref": float(np.mean([y["correct"] for _, y in pairs]))}
    L += ["## 8. v1 재실행 vs Track B 리포트 dev 절반", "",
          "- `%s` dev 250행 대비: argmax %d/%d 일치, max abs Δp %.4f, Track B dev acc %s vs 재실행 %s. "
          "배치 구성이 다르다(Track B는 전체 파일의 연속 16행, 여기는 dev 행끼리 16행)." % (
              out["v1_parity_trackB"]["reference"], agree, len(pairs), dp, f3(out["v1_parity_trackB"]["acc_ref"]),
              f3(out["variants"]["v1"]["accuracy"])), ""]

    # ---- 9. selection rule (declared before the runs, applied mechanically)
    elig = sorted(SAME_CONTRACT, key=lambda v: (-out["variants"][v]["accuracy"], -out["variants"][v]["macro_f1_gold"]))
    best = elig[0] if out["variants"][elig[0]]["delta_vs_v1"] >= 0 else "v1"
    bv = out["variants"][best]
    out["selection"] = {"rule": "highest dev accuracy among v2a/v2c/v2d (8 options, default budget), tie -> macro-F1; "
                                "must not be below v1; v2b/v2e only if they beat their decode-time comparators (§2)",
                        "ranking": elig, "best": best}
    L += ["## 9. 선택 규칙 적용 (런 전에 정한 규칙)", "",
          "규칙: v1과 같은 계약(8옵션, general 포함, 기본 head budget)인 v2a·v2c·v2d 중 dev accuracy 최고, 동률이면 macro-F1. "
          "v1보다 낮으면 채택하지 않는다. v2b·v2e는 계약이 바뀌므로(general은 게이트가, coarse는 하위 라우팅이 맡음) §2의 디코드 단계 "
          "비교 대상을 이길 때만 대안으로 올린다. v2c_h512는 진단이다.", "",
          "- 순위: " + " > ".join("%s %s" % (v, f3(out["variants"][v]["accuracy"])) for v in elig),
          "- 최고: **%s** (dev acc %s [%s, %s], macro-F1 %s, v1 대비 %+.3f, McNemar b/c %d/%d p=%s)" % (
              best, f3(bv["accuracy"]), *map(f3, bv["accuracy_ci"]), f3(bv["macro_f1_gold"]), bv["delta_vs_v1"],
              bv["mcnemar_vs_v1"][0], bv["mcnemar_vs_v1"][1], fp(bv["mcnemar_vs_v1"][2])),
          "- %s 클래스별 recall: %s" % (best, ", ".join("%s %d/%d" % (k, *x) for k, x in bv["recall"].items())), ""]
    L += ["## 입력 파일", "", "| variant | report | dataset | dataset_sha256 | questions_sha256 |", "|---|---|---|---|---|"]
    for v, r in list(R.items()) + [(k + "_general", g) for k, g in G.items()]:
        rc = r["run_card"]
        L.append("| %s | %s | %s | %s | %s |" % (v, Path(r["path"]).relative_to(ROOT), rc["dataset"], rc["dataset_sha256"], rc["questions_sha256"]))
    out["build"] = {k: build[k] for k in ("source", "source_sha256", "files", "v2c_examples_overlap")}
    (ROOT / ("results/C/C_schema_v2_%s.ko.md" % date)).write_text("\n".join(L) + "\n", encoding="utf-8")
    (ROOT / ("results/C/C_schema_v2_%s.json" % date)).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("best", best, f3(bv["accuracy"]))


if __name__ == "__main__":
    main(sys.argv[1])
