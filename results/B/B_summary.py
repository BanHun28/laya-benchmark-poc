"""Track B summary composer (throwaway, no model call): reads results/B/metrics/*.json (metrics_extra outputs),
B_splits.json, the run-time log and the run logs, writes results/B/summary_<YYYYMMDD>.ko.md (tables only;
the interpretation paragraphs are added by hand below each generated table block).

    source env.sh && .venv/bin/python results/B/B_summary.py 20261002
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from metrics_extra import load_report  # noqa: E402

B = ROOT / "results/B"
M = B / "metrics"
DATE = sys.argv[1]
CKPTS = ["english", "multilingual", "typed-decisions", "router"]
C_SETS = ["ko_massive_domain_8", "ko_klue_ynat_7", "ko_massive_scenario_18"]
B5 = [("ko_massive_intent_20opt", 20, "A2 재현값 (english 0.110 / multilingual 0.470 upstream)"),
      ("en_massive_intent_20opt", 20, "english 0.820 / multilingual 0.710 (upstream)"),
      ("ko_massive_scenario_18", 18, "P0c 0.52 (n=100)"), ("ko_massive_domain_8", 8, "≥ 0.66 추정 (P0c 병합), G1 입력"),
      ("en_massive_domain_8", 8, "한국어 페널티 쌍 (07 §5 E1: ko 0.52 vs en 0.62)"), ("ko_klue_ynat_7", 7, "P0c 0.65 (n=100)"),
      ("ko_klue_nli_3", 3, "0.45~0.65"), ("ko_nsmc_sentiment", 2, "0.60~0.80"), ("ko_kmhas_hate", 2, "0.55~0.75"),
      ("ko_kmhas_type_8", 8, "유형 간 혼동 측정"), ("ko_3i4k_speechact_7", 7, "0.40~0.60")]
KO_SETS = [s for s, _, _ in B5 if s.startswith("ko_")]
S = json.loads((M / "summary_all.json").read_text(encoding="utf-8"))["results"]
IDX = {(r["set"], r["model"], r["qid"], r["split"]): r for r in S}
out = []


def p(*lines):
    out.extend(lines)


def jl(name):
    f = M / (name + ".json")
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def f3(x):
    return "-" if x is None else "%.3f" % x


def fp(x):
    return "%.4f" % x if x >= 0.001 else "%.1e" % x


def acc_ci(r):
    return "-" if r is None else "%.3f [%.3f, %.3f]" % (r["accuracy"], *r["accuracy_ci"])


def qids(s):
    return list(dict.fromkeys(k[2] for k in IDX if k[0] == s))


def get(s, m, q, sp="all"):
    return IDX.get((s, m, q, sp))


def paired_rows(name, label):
    d = jl(name)
    return [] if d is None else ["| %s | %s | %d | %.3f | %.3f | %+.3f [%+.3f, %+.3f] | %d | %d | %s | %.3f |" % (
        label, r["split"], r["n"], r["acc_a"], r["acc_b"], r["delta"], *r["delta_ci"], r["b"], r["c"], fp(r["p"]),
        r["agreement"]) for r in d["results"]]


PAIR_HDR = ["| 비교 (A → B) | split | n | acc A | acc B | Δ = B − A [95% Wald] | b | c | McNemar p | argmax 일치 |",
            "|---|---|---|---|---|---|---|---|---|---|"]

# ---------------------------------------------------------------- 0. splits
sp = json.loads((B / "B_splits.json").read_text(encoding="utf-8"))
p("# Track B 한국어 품질 + PoC P1(시나리오 C) 요약 (%s)" % DATE, "",
  "생성: `results/B/B_summary.py` (표), 해석 문단은 수기. 모든 수치는 `results/B/metrics/*.json`(scripts/metrics_extra.py 출력)에서 온다. "
  "CPU fp32, laya 0.3.23, 체크포인트 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851. 95% CI는 bootstrap 1000회(seed 13, percentile).", "",
  "## 0. dev/test 분할", "",
  "규칙: ko/en 쌍 MASSIVE 파일(`*_massive_domain_8`, `*_massive_intent_20opt`, 그리고 같은 행 순서의 domain_8 변형)은 데이터 행 index 짝수 → dev, 홀수 → test. "
  "그 외는 `int(sha256(json.dumps(state, ensure_ascii=False, sort_keys=True)), 16) % 2` (0 → dev). ablation 변형은 dev 절반만 `results/B/dev/`에 복사해 실행.", "",
  "| 파일 | 규칙 | 행 | dev | test |", "|---|---|---|---|---|")
for name, v in sp["splits"].items():
    p("| %s | %s | %d | %d | %d |" % (name, v["rule"], v["rows"], v["dev"], v["test"]))
p("", "ko/en 정렬 검사: " + "; ".join("%s %d/%d행 expected·scenario 태그 일치" % (k, v["expected_and_scenario_tag_match"], v["rows"])
                                    for k, v in sp["pairs"].items()) + ".")

# ---------------------------------------------------------------- 1. B5 table
p("", "## 1. B5 표: 세트 × 체크포인트 accuracy [95% CI]", "",
  "| 세트 | qid | 옵션 | split | majority | english | multilingual | typed-decisions | Router (auto) | 기대 범위 (03 B5) |",
  "|---|---|---|---|---|---|---|---|---|---|")
for s, k, exp in B5:
    for q in qids(s):
        for split in (("all", "dev", "test") if s in C_SETS + ["en_massive_domain_8"] else ("all",)):
            any_r = next((get(s, m, q, split) for m in CKPTS if get(s, m, q, split)), None)
            if any_r is None:
                continue
            p("| %s | %s | %d | %s | %.3f | %s | %s | %s | %s | %s |" % (
                s, q, k, split, any_r["majority"], *[acc_ci(get(s, m, q, split)) for m in CKPTS], exp if split == "all" else ""))
p("", "### 1b. 보조 지표 (macro-F1 ∪ = gold∪pred 클래스, gold = gold에 있는 클래스; Brier = Σ_o (p_o − y_o)²; ECE 15-bin answer_confidence)", "",
  "| 세트 | qid | ckpt | split | n | acc [CI] | macro-F1 ∪ | macro-F1 gold | Brier | ECE [CI] | mean conf | acc@50%cov | majority | Δ vs majority |",
  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for s, _, _ in B5:
    for q in qids(s):
        for m in CKPTS:
            for split in (("all", "dev", "test") if s in C_SETS + ["en_massive_domain_8"] else ("all",)):
                r = get(s, m, q, split)
                if r:
                    p("| %s | %s | %s | %s | %d | %s | %.3f | %.3f | %.3f | %.3f [%.3f, %.3f] | %.3f | %.3f | %.3f | %+.3f |" % (
                        s, q, m, split, r["n"], acc_ci(r), r["macro_f1_union"], r["macro_f1_gold"], r["brier"], r["ece"],
                        *r["ece_ci"], r["mean_confidence"], r["acc_at_50_coverage"], r["majority"], r["delta_vs_majority"]))

# ---------------------------------------------------------------- 2. Korean penalty
p("", "## 2. 한국어 페널티: 같은 MASSIVE id의 ko vs en (domain_8, index parity 분할)", "", *PAIR_HDR)
for name, label in (("paired_penalty_ko-ml_en-ml", "ko/multilingual → en/multilingual (페널티)"),
                    ("paired_penalty_ko-en_en-en", "ko/english → en/english (english 체크포인트 페널티)"),
                    ("paired_ref_en-ml_en-en", "en/multilingual → en/english (영어 기준점)"),
                    ("paired_ref_ko-ml_en-en", "ko/multilingual → en/english"),
                    ("paired_penalty20_ko-ml_en-ml", "intent-20 ko/ml → en/ml (참고, n=100)")):
    p(*paired_rows(name, label))

# ---------------------------------------------------------------- 3. ablations
p("", "## 3. ablation (multilingual, dev 절반만; base = 전체 런의 dev 절반)", "", *PAIR_HDR)
for base, var in (("ko_massive_domain_8", "ko-instr"), ("ko_massive_domain_8", "en-desc"), ("ko_klue_ynat_7", "ko-instr"),
                  ("ko_klue_ynat_7", "en-desc"), ("ko_massive_scenario_18", "en-desc")):
    p(*paired_rows("paired_ablation_%s_%s" % (base, var), "%s: base → %s" % (base, var)))

# ---------------------------------------------------------------- 4. Router share
p("", "## 4. Router auto `model` 분포 (H2 후반: 한국어 세트 100% multilingual 기대)", "",
  "| 세트 | cases | 답한 체크포인트 (cases) | multilingual 비율 | parity vs multilingual 고정: flips / max abs Δp |", "|---|---|---|---|---|")
for s in KO_SETS:
    rs = [get(s, "router", q) for q in qids(s) if get(s, "router", q)]
    if not rs:
        continue
    cnt = Counter()
    for r in rs:
        cnt.update(r["models"])
    par = jl("parity_%s_router" % s)
    pr = par["results"][0] if par else None
    p("| %s | %d | %s | %.3f | %s |" % (s, sum(cnt.values()), ", ".join("%s %d" % kv for kv in cnt.items()),
                                        cnt["multilingual"] / sum(cnt.values()), "%d / %.4f" % (pr["flips"], pr["max_abs_dp"]) if pr else "-"))

# ---------------------------------------------------------------- 5. per-class
for s in ("ko_massive_domain_8", "ko_klue_ynat_7"):
    q = qids(s)[0]
    p("", "## 5. %s: 클래스별 recall과 예측 분포" % s, "",
      "| gold 클래스 | n | ml recall (all) | ml dev | ml test | ml 예측 수 | 예측/gold | english recall | typed recall | Router recall |",
      "|---|---|---|---|---|---|---|---|---|---|")
    ml = get(s, "multilingual", q)
    for g, (tp, n) in ml["recall"].items():
        rr = [get(s, m, q, x) for m, x in (("multilingual", "dev"), ("multilingual", "test"), ("english", "all"),
                                            ("typed-decisions", "all"), ("router", "all"))]
        cell = lambda r: "-" if r is None else "%d/%d (%.2f)" % (r["recall"][g][0], r["recall"][g][1], r["recall"][g][0] / r["recall"][g][1])
        pc = ml["pred_counts"].get(g, 0)
        p("| %s | %d | %d/%d (%.2f) | %s | %s | %d | %.2f | %s | %s | %s |" % (g, n, tp, n, tp / n, cell(rr[0]), cell(rr[1]), pc, pc / n,
                                                                             cell(rr[2]), cell(rr[3]), cell(rr[4])))
    fo = ml["first_option"]
    p("", "- multilingual top 혼동 (gold→pred): " + ", ".join("%s→%s ×%d" % tuple(x) for x in ml["confusions_top5"]),
      "- 첫 옵션 `%s`: gold %d, 예측 %d (multilingual). english: 예측 %d, typed: 예측 %d" % (
          fo["label"], fo["gold_n"], fo["pred_n"], get(s, "english", q)["first_option"]["pred_n"],
          get(s, "typed-decisions", q)["first_option"]["pred_n"]),
      "- 예측 분포 multilingual: " + ", ".join("%s %d" % kv for kv in ml["pred_counts"].items()),
      "- 예측 분포 english: " + ", ".join("%s %d" % kv for kv in get(s, "english", q)["pred_counts"].items()),
      "- 예측 분포 typed-decisions: " + ", ".join("%s %d" % kv for kv in get(s, "typed-decisions", q)["pred_counts"].items()))
    if s == "ko_massive_domain_8":
        rep = load_report(ml["report"])
        by = defaultdict(list)
        for c in rep["cases"]:
            by[next(t for t in c["tags"] if t.startswith("scenario:"))[9:]].append(c)
        p("", "원래 MASSIVE scenario별 (multilingual, all): 정답 도메인, n, 정확도, 최다 오답 도메인", "",
          "| scenario | → 도메인 | n | accuracy | 오답 예측 분포 | 평균 conf (오답) |", "|---|---|---|---|---|---|")
        for sc, cs in sorted(by.items(), key=lambda kv: sum(c["correct"] for c in kv[1]) / len(kv[1])):
            wrong = [c for c in cs if not c["correct"]]
            p("| %s | %s | %d | %.3f | %s | %s |" % (sc, cs[0]["gold"], len(cs), sum(c["correct"] for c in cs) / len(cs),
                                                    ", ".join("%s %d" % kv for kv in Counter(c["pred"] for c in wrong).most_common(3)),
                                                    f3(sum(c["conf"] for c in wrong) / len(wrong)) if wrong else "-"))

# ---------------------------------------------------------------- 6/7. checkpoint choice, G1
p("", "## 6. 체크포인트 선택 입력: ko_massive_domain_8 test 절반", "",
  "| ckpt | test acc [CI] | test ECE [CI] (as-shipped) | test macro-F1 gold | multilingual 대비 paired (test): Δ = ml − ckpt, p |", "|---|---|---|---|---|")
for m in CKPTS:
    r = get("ko_massive_domain_8", m, "domain", "test")
    d = jl("paired_ko_massive_domain_8_%s_vs_ml" % m)
    t = next((x for x in d["results"] if x["split"] == "test"), None) if d else None
    p("| %s | %s | %.3f [%.3f, %.3f] | %.3f | %s |" % (m, acc_ci(r), r["ece"], *r["ece_ci"], r["macro_f1_gold"],
                                                     "%+.3f, p=%s (b=%d, c=%d)" % (t["delta"], fp(t["p"]), t["b"], t["c"]) if t else
                                                     ("parity: flips %d" % jl("parity_ko_massive_domain_8_router")["results"][0]["flips"]
                                                      if m == "router" and jl("parity_ko_massive_domain_8_router") else "-")))
p("", "## 7. G1 사전 판독 (00 §6: LLM 베이스라인 없으면 절대 ≥ 0.80) + 게이트 미리보기 (as-shipped, refit 전)", "",
  "| 세트 | split | multilingual acc [CI] | 0.80 대비 | CI 상한 < 0.80? | 오류 ≤5%: 최대 coverage (T) | 오류 ≤10%: 최대 coverage (T) |",
  "|---|---|---|---|---|---|---|")
cov = {(Path(x["report"]).stem.split("_", 2)[2], x["split"]): x for x in jl("coverage_ml_poc")["results"]}
for s in ("ko_massive_domain_8", "ko_klue_ynat_7"):
    for split in ("dev", "test", "all"):
        r = get(s, "multilingual", qids(s)[0], split)
        c = cov[(s, split)]["max_coverage"]
        p("| %s | %s | %s | %+.3f | %s | %.3f (T=%s) | %.3f (T=%s) |" % (
            s, split, acc_ci(r), r["accuracy"] - 0.80, "예" if r["accuracy_ci"][1] < 0.80 else "아니오",
            c["0.05"]["coverage"], f3(c["0.05"]["T"]), c["0.1"]["coverage"], f3(c["0.1"]["T"])))

# ---------------------------------------------------------------- 8. H2/H3
p("", "## 8. H2 / H3 입력", "", "H2: multilingual − english ≥ +0.20 (모든 ko 세트), 같은 행 paired.", "",
  "| 세트 | qid | multilingual | english | Δ (ml − english) [95% Wald] | McNemar p | ≥ +0.20 |", "|---|---|---|---|---|---|---|")
for s in KO_SETS:
    d = jl("paired_%s_english_vs_ml" % s)
    for r in (d["results"] if d else []):
        if r["split"] == "all":
            p("| %s | %s | %.3f | %.3f | %+.3f [%+.3f, %+.3f] | %s | %s |" % (s, r["qid"], r["acc_b"], r["acc_a"], r["delta"],
                                                                         *r["delta_ci"], fp(r["p"]), "예" if r["delta"] >= 0.20 else "아니오"))
p("", "H3: 정확도 ≥ majority + 0.20 (≤7옵션 과제 중심; supervised 상한은 Track F3 문헌값 미기입이라 후반 조건은 미결).", "",
  "| 세트 | qid | 옵션 | multilingual acc | majority | acc − majority | ≥ +0.20 |", "|---|---|---|---|---|---|---|")
for s, k, _ in B5:
    for q in qids(s):
        r = get(s, "multilingual", q)
        if r:
            p("| %s | %s | %d | %.3f | %.3f | %+.3f | %s |" % (s, q, k, r["accuracy"], r["majority"], r["delta_vs_majority"],
                                                         "예" if r["delta_vs_majority"] >= 0.20 else "아니오"))

# ---------------------------------------------------------------- 9. A3
a3 = sp["a3"]
p("", "## 9. A3 하네스 동일성 (`ko_massive_intent_20opt.jsonl` vs `results/korean_support/K2_intent20_ko.jsonl`)", "",
  "- 파일 수준: 행 %d/%d, state·questions·expected·language 일치 행 %s. 차이는 K2 파일의 추가 태그(`k2_paired`, `id:<n>`)뿐 → dataset_sha256은 다름 (%s)." % (
      *a3["rows"], json.dumps(a3["field_equal_rows"]), ", ".join("%s %s…" % (k, v[:12]) for k, v in a3["dataset_sha256"].items())),
  "- questions_sha256: builder %s = K2 %s = MANIFEST %s." % tuple(v[:16] for v in list(a3["questions_sha256"].values()) + [a3["manifest_questions_sha256"]]),
  "", "| 비교 (기준 = K2 리포트) | n | argmax 일치 | flips | max abs Δp | mean abs Δ conf |", "|---|---|---|---|---|---|")
for name in ("parity_a3_multilingual", "parity_a3_english", "parity_a3_en_multilingual", "parity_a3_en_english"):
    d = jl(name)
    for r in (d["results"] if d else []):
        p("| %s vs %s | %d | %.4f | %d | %.4f | %.4f |" % (Path(d["reference"]).name, Path(r["other"]).name, r["n"], r["agreement"],
                                                         r["flips"], r["max_abs_dp"], r["mean_abs_dconf"]))

# ---------------------------------------------------------------- 10. time + warnings
p("", "## 10. 런별 소요 시간 (프로세스 wall, 체크포인트 로드 포함; 다른 무거운 프로세스와 머신 공유 → 지연 비교 불가)", "",
  "| run_id | exit | 초 |", "|---|---|---|")
tot = 0
for line in (B / "logs/B_run_times.log").read_text(encoding="utf-8").splitlines():
    m = re.search(r"end\s+(\S+) exit=(\d+) secs=(\d+)", line)
    if m:
        tot += int(m.group(3))
        p("| %s | %s | %s |" % m.groups())
    elif "SKIP" in line:
        p("| %s | skipped (budget) | - |" % line.split()[-1])
p("", "합계 모델 시간: %d초 (%.1f분)." % (tot, tot / 60), "", "### 경고 원문 (로그별 중복 제거)", "")
warn = defaultdict(list)
for log in sorted((B / "logs").glob("2026*.log")):
    for w in dict.fromkeys(l.strip() for l in re.split(r"[\r\n]", log.read_text(encoding="utf-8")) if "Warning" in l or "warning" in l):
        warn[w].append(log.stem)
for w, runs in warn.items():
    p("- `%s`" % re.sub(r"\S*/(?=\.venv/)", "", w), "  - 런 (%d): %s" % (len(runs), ", ".join(runs)))  # run logs record absolute paths; show them repository-relative
if not warn:
    p("- 경고 없음")
(B / ("summary_%s.ko.md" % DATE)).write_text("\n".join(out) + "\n", encoding="utf-8")
print("wrote results/B/summary_%s.ko.md (%d lines)" % (DATE, len(out)))
