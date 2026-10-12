#!/usr/bin/env python3
"""Benchmark results dashboard (docs/03_benchmark_plan.md §3.8, §12 item 11).

Reads laya-evals reports (recognised by their `config` + `overall` blocks), our scripts' JSON by known keys
(metrics_extra, C1, schema v2, E, P4) and results/{verdicts,go_no_go}.json, and writes one self-contained HTML
file. Tables are plain HTML so the page reads offline; charts are Chart.js (cdnjs) fed by one inline JSON blob.
Same inputs give the same bytes: the only time-dependent line is the footer that --stamp adds.

    python scripts/build_dashboard.py --results results/ --out results/dashboard/index.html [--open] [--stamp]
"""
import argparse
import bisect
import collections
import datetime
import html
import json
import math
import os
import re
import webbrowser
from pathlib import Path

CHART_JS = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"
REPORT_RE = re.compile(r"^(?:(?:full|smoke)_)?(\d{8}-\d{4})_([^_]+)_(.+)$")  # <ts>_<model>_<set>; models carry no "_"
SKIP_DIRS = {"metrics", "logs", "dev", "dashboard", "smoke_full", "evalsets_full", "__pycache__"}
RUNNERS = ["english", "multilingual", "typed-decisions", "router"]
SPLIT_SETS = {"ko_massive_domain_8", "ko_klue_ynat_7", "ko_massive_scenario_18"}
HARD_GATES = ("G1", "G2", "G5")  # 00 §6 판정 규칙: 하나라도 미달이면 No-Go 또는 P4 후 재평가
TRACK_A = {("ko", "multilingual"): "korean_support/K2_intent20_ko_multilingual.json",
           ("ko", "english"): "korean_support/K2_intent20_ko_english.json",
           ("en", "multilingual"): "korean_support/K2_intent20_en_multilingual.json",
           ("en", "english"): "korean_support/K2_intent20_en_english.json"}
# (accuracy, ECE), third_party/laya/BENCHMARKS.md §Languages: ko row :71, en row :117
UPSTREAM_A = {("ko", "multilingual"): (0.470, 0.311), ("ko", "english"): (0.110, 0.680),
              ("en", "multilingual"): (0.710, 0.233), ("en", "english"): (0.820, 0.138)}
# per-permutation flip, BENCHMARKS.md §Option-order robustness (massive_intent.en, 20 options); G4 from 00 §6
FLIP_REFS = [(0.10, "G4 기준 0.10"), (0.13, "Jev 0.13"), (0.150, "upstream en 0.150"), (0.230, "upstream ml 0.230")]
BINS = 15
# 3-arm "학습 실패" 표시(docs/11 §4)의 원인 추적. results/T3arm/PREP_20261008.md "본 학습 중 발견" 절, 셋 다 파이프라인 실패가 아니다
T3ARM_FAIL_CAUSE = {"T5": "dev 기준선 오염: dev가 upstream 학습 믹스인 BoolQ의 train split이라 vanilla dev가 부풀었다",
                    "T9": "천장 효과: vanilla가 이미 천장이고 dev 차이는 1,000행 중 1행",
                    "T10": "dev 라벨 분포 불일치: dev는 자연 분포, train·ext는 균등에 가깝다"}
# 3-arm 사용자 결정(2026-10-08 15:25, PREP_20261008.md "사용자 결정" 절, docs/11 열린 질문 1·2·4·9-11): (항목, 결정, 상태, 결과, 출력).
# 상태가 바뀌면 docs/11과 함께 고친다.
T3ARM_DECISIONS = (
    ("V3 판정", "통과(차이 기준). 엄격 기준 미달은 계획과의 편차로 기록", "해결", "학습 검증 표에 반영", None),
    ("T8 분할", "hold-out(dev·calib를 train에서 뗌) 유지, 2 epoch", "해결", "본 학습에 적용", None),
    ("보정 분리 열 (vanilla + 과제 T)", "추가. 과제마다 0-step export(base 가중치 + 과제 calib T)를 Jev 항목과 ext로 평가", "해결",
     "보정 분리 표에 반영", "results/T3arm/calib_sep/"),
    ("반복 학습", "seed 14로 10과제를 1회 더. 판정은 두 run의 결론이 같을 때만 확정", "해결", "판정 일치표에 반영",
     "results/T3arm/rep_s14/"),
    ("T9·T10 Jev 측정 (80 요청)", "승인. 기존 플레이그라운드 운영 규칙", "해결", "세션 S7, Jev 칸에 반영", "results/F/jev_cmp/sessions/S7_20261008/"))
E = html.escape


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def dig(x, *keys):
    for k in keys:
        try:
            x = x[k]
        except (KeyError, IndexError, TypeError):
            return None
    return x


def fnum(x, d=3, sign=False):
    x = 0.0 if round(x, d) == 0 else x  # no "-0.000"
    return f"{x:+.{d}f}" if sign else f"{x:.{d}f}"


def num(x, d=3, ci=None, sign=False):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x):
        return '<td class="na">—</td>'
    tail = f" [{fnum(ci[0], d, sign)}, {fnum(ci[1], d, sign)}]" if ci else ""
    return f'<td class="num">{fnum(x, d, sign)}{tail}</td>'


def vfmt(x):
    """Hand-entered gate values keep their own precision (0.0017 stays 4 places), at least 3 places."""
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        return None
    places = len(repr(float(x)).split(".")[1]) if "e" not in repr(float(x)) else 4
    return fnum(x, min(max(3, places), 4))


def vnum(x):
    s = vfmt(x)
    return f'<td class="num">{s}</td>' if s else num(None)


def f4(x):
    return "—" if x is None else f"{x:.4f}"


def pnum(p):
    return num(p, 4) if not isinstance(p, float) or p >= 1e-3 else f'<td class="num">{p:.1e}</td>'


def td(content, cls=None, raw=False):
    body = content if raw else E(str(content))
    return f'<td class="{cls}">{body}</td>' if cls else f"<td>{body}</td>"


def table(head, rows):
    th = "".join(f"<th>{E(h)}</th>" for h in head)
    tr = "".join("<tr>" + "".join(r) + "</tr>" for r in rows)
    return f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def chip(state, label):
    icon = {"good": "✓", "bad": "✗", "part": "◐", "none": "–"}[state]
    return f'<span class="chip {state}"><i aria-hidden="true">{icon}</i>{E(label)}</span>'


def verdict_state(v):
    v = v or ""
    if "미측정" in v:
        return "none"
    if "기각" in v:
        return "bad"
    if any(k in v for k in ("부분", "전반부", "후반부")):
        return "part"
    return "good" if "지지" in v else "none"


def gate_chip(p):
    return chip({True: "good", False: "bad"}.get(p, "none"), {True: "통과", False: "미달"}.get(p, "대기"))


def md_cells(line):
    """Cells of one markdown table row; `\\|` is a literal pipe inside a cell."""
    # the docs escape prose tildes as `\~` against GitHub strikethrough; the page shows plain "~"
    return [c.strip().replace("\\|", "|").replace("\\~", "~") for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]


def md_inline(s):
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", E(s.replace("**", "")))


def reliability(recs, temp):
    """15-bin reliability of answer_confidence at temperature `temp`: the calibrate_ko.score rounding (4 places)
    and the metrics_extra.ece_bins edges ([0, 1/15], then (lo, hi])."""
    edges = [i / BINS for i in range(BINS + 1)]
    agg = collections.defaultdict(lambda: [0, 0.0, 0.0])
    for r in recs:
        z = [v / temp for v in r["logits"]]
        top = max(z)
        ex = [math.exp(v - top) for v in z]
        j = max(range(len(ex)), key=ex.__getitem__)
        conf = round(min(max(ex[j] / sum(ex), 0.0), 1.0), 4)
        a = agg[min(max(bisect.bisect_left(edges, conf) - 1, 0), BINS - 1)]
        a[0], a[1], a[2] = a[0] + 1, a[1] + conf, a[2] + float(j == r["y"])
    bins = [{"i": b, "n": n, "conf": sc / n, "acc": sa / n} for b, (n, sc, sa) in sorted(agg.items())]
    return bins, sum(abs(sc - sa) for _, sc, sa in agg.values()) / max(len(recs), 1)


def device_parity(a, b):
    """(questions, argmax flips, max |Δp|) between two P0 SDK answer sets; noul compares p(true)."""
    flips, dp, qa, qb = 0, 0.0, dig(a, "result", "answers") or {}, dig(b, "result", "answers") or {}
    for q, x in qa.items():
        px = x.get("probabilities") or {"true": x.get("noul")}
        py = qb[q].get("probabilities") or {"true": qb[q].get("noul")}
        dp = max([dp] + [abs(px[k] - py[k]) for k in px])
        top = (lambda p: max(p, key=p.get)) if len(px) > 1 else (lambda p: p["true"] >= 0.5)
        flips += top(px) != top(py)
    return len(qa), flips, dp


class Dash:
    def __init__(self, root, out):
        self.root, self.out = Path(root), Path(out)
        self.proj = self.root.resolve().parent
        self.used, self.cache, self.charts = {}, {}, []
        self.reps = self.discover()

    # ------------------------------------------------------------------ inputs
    def pr(self, rel):
        """Project-relative display path of a file under the results root."""
        return os.path.relpath(self.root.resolve() / rel, self.proj)

    def read(self, rel):
        if rel not in self.cache:
            self.cache[rel] = load(self.root / rel)
            self.used.setdefault(self.pr(rel), self.cache[rel] is not None)
        return self.cache[rel]

    def text(self, rel, proj=False):
        path = (self.proj if proj else self.root) / rel
        try:
            s = path.read_text(encoding="utf-8")
        except OSError:
            s = None
        self.used.setdefault(rel if proj else self.pr(rel), s is not None)
        return s or ""

    def newest(self, pattern):
        hits = sorted(self.root.glob(pattern))
        if not hits:
            self.used.setdefault(self.pr(pattern), False)
            return pattern, None
        rel = hits[-1].relative_to(self.root).as_posix()
        return rel, self.read(rel)

    def discover(self):
        reps = {}
        for p in sorted(self.root.glob("*/*.json")) + sorted(self.root.glob("*/*/*.json")):
            rel = p.relative_to(self.root)
            if SKIP_DIRS & set(rel.parts[:-1]):
                continue
            d = load(p)
            if not (isinstance(d, dict) and isinstance(d.get("overall"), dict) and "dataset_sha256" in (d.get("config") or {})):
                continue
            c, m, cases = d["config"], REPORT_RE.match(p.stem), d.get("cases") or []
            reps[rel.as_posix()] = {
                "rel": rel.as_posix(), "run_id": p.stem, "dir": rel.parts[0], "config": c, "overall": d["overall"],
                "runner": m.group(2) if m else str(c.get("model")),
                "set": m.group(3) if m else Path(str(c.get("dataset"))).stem, "n": len(cases),
                "models": collections.Counter(str(x.get("model")) for x in cases)}
        return reps

    def doc_rows(self, rel, pattern):
        return [md_cells(ln) for ln in self.text(rel, proj=True).splitlines() if re.match(pattern, ln)]

    # ------------------------------------------------------------------ html bits
    def a(self, projrel, label=None):
        href = os.path.relpath(self.proj / projrel, self.out.parent.resolve())
        return f'<a href="{E(href)}">{E(label or projrel)}</a>'

    def link(self, rel, label=None):
        return self.a(self.pr(rel), label or rel)

    def missing(self, rel):
        return f'<p class="missing">데이터 없음: <code>{E(self.pr(rel))}</code></p>'

    def chart(self, cid, spec, caption, aria):
        self.charts.append(dict(id=cid, **spec))
        return (f'<figure class="chart"><div class="chart-box"><canvas id="{cid}" role="img" aria-label="{E(aria)}">'
                f'</canvas></div><figcaption>{caption}</figcaption></figure>')

    def sources(self, paths, run_ids=()):
        s = " · ".join(self.a(p, p) if (self.proj / p).exists() else E(p) + " (없음)" for p in paths)
        if run_ids:
            s += f'<details><summary>run_id {len(run_ids)}개</summary>{E(", ".join(run_ids))}</details>'
        return s

    # ------------------------------------------------------------------ derived values
    def summary_rows(self):
        s = self.read("B/metrics/summary_all.json")
        return {(r["set"], r["qid"], r["model"], r["split"]): r for r in (s or {}).get("results", [])}

    @staticmethod
    def base_keys(idx):
        """(set, qid) in summary order, Korean sets before the en controls; ablation variants (a "-" in the name) left out."""
        keys = list(dict.fromkeys((s, q) for s, q, _, _ in idx if "-" not in s))
        return sorted(keys, key=lambda k: k[0].startswith("en_"))

    def auto_gates(self):
        """Gate values recomputable from result JSON, shown beside the hand-kept go_no_go.json values."""
        b = self.summary_rows()
        _, e = self.newest("E/*_calibration_multilingual.json")
        _, c1 = self.newest("C/*option_order*.json")
        d8 = next((s for s in (c1 or {}).get("sets", []) if s.get("set") == "ko_massive_domain_8"), None)
        mps, cpu = self.read("poc/P0_sdk_mps.json"), self.read("poc/P0_sdk_cpu.json")
        return {"G0": dig(self.reps.get(TRACK_A[("ko", "multilingual")]), "overall", "choice_accuracy"),
                "G1": dig(b.get(("ko_massive_domain_8", "domain", "multilingual", "test")), "accuracy"),
                "G2": dig(e, "e3", "ko_massive_domain_8", "refit:pooled", "dev_chosen", "0.05", "test", "coverage"),
                "G3": dig(e, "e2", "fits", "pooled", "eval", "ko_massive_domain_8", "test", "official", "ece"),
                "G4": dig(d8, "metrics", "flip_rate_per_perm"),
                "G7": device_parity(mps, cpu)[2] if mps and cpu else None}

    # ------------------------------------------------------------------ sections
    def sec_summary(self, gates, crit):
        rel, env = self.newest("env/env_*.json")
        if env:
            rows = [
                ("기록", f"{env.get('recorded_at')} · {self.pr(rel)}"),
                ("플랫폼", f"{env.get('platform')} · Python {env.get('python')}"),
                ("버전", " · ".join(f"{k} {x}" for k, x in env.get("versions", {}).items())),
                ("디바이스", f"MPS 가능 {env.get('mps_available')} · torch 스레드 intra {env.get('torch_threads')} / "
                          f"inter {env.get('torch_interop_threads')} (스냅샷 시점 기본값)"),
                ("LAYA_REVISION", str(dig(env, "env", "LAYA_REVISION") or "미설정"))]
            rows += [(f"체크포인트 {k}", f"snapshot {str(c.get('snapshot_sha'))[:12]} · weights sha256 "
                                     f"{str(c.get('weights_sha256'))[:12]}") for k, c in env.get("checkpoints", {}).items()]
            envt = ('<div class="tw"><table><tbody>' + "".join(
                f'<tr><th scope="row">{E(k)}</th><td>{E(x)}</td></tr>' for k, x in rows) + "</tbody></table></div>")
        else:
            envt = self.missing(rel)
        st = {k: x.get("pass") for k, x in gates.items()}
        fails, waits = [k for k, p in st.items() if p is False], [k for k, p in st.items() if p is None]
        if st.get("G0") is not True:
            head = "판정 보류 (G0 재현 게이트 미통과)"
        elif any(k in fails for k in HARD_GATES):
            head = "No-Go 또는 파인튜닝(P4) 후 재평가"
        elif any(k in waits for k in HARD_GATES):
            head = "판정 대기"
        else:
            head = "조건부 Go (운영 가드 추가)" if fails else "Go"
        line = (f'<p class="verdict"><b>{E(head)}</b> — 미달 {E(", ".join(fails) or "없음")} · 대기 '
                f'{E(", ".join(waits) or "없음")} <span class="note">(00 §6 판정 규칙을 results/go_no_go.json에 적용)</span></p>'
                if gates else self.missing("go_no_go.json"))
        tiles = "".join(f'<div class="kpi"><div class="k">{E(k)} {E(dig(crit, k, 1) or "")}</div>'
                        f'<div class="v">{vfmt(x.get("value")) or "—"}</div>{gate_chip(x.get("pass"))}</div>'
                        for k, x in gates.items())
        per_dir = collections.Counter(r["dir"] for r in self.reps.values())
        counts = (f"<p>laya-evals 리포트 {len(self.reps)}개 (" + " · ".join(f"{E(k)} {n}" for k, n in sorted(per_dir.items()))
                  + ") · 그 밖의 입력 파일은 10절 목록. smoke_full·metrics·dev 하위는 리포트 목록에서 제외.</p>")
        return line + f'<div class="kpis">{tiles}</div>' + counts + "<h3>환경과 pin</h3>" + envt

    def sec_a(self):
        rows = []
        for (lang, ck), rel in TRACK_A.items():
            r = self.reps.get(rel)
            self.used.setdefault(self.pr(rel), r is not None)
            cells = [td(lang), td(ck)]
            for up, m in zip(UPSTREAM_A[(lang, ck)], (dig(r, "overall", "choice_accuracy"), dig(r, "overall", "ece"))):
                d = None if m is None else m - up
                ok = chip("none", "데이터 없음") if d is None else chip("good", "±0.03 이내") if abs(d) <= 0.03 + 1e-9 \
                    else chip("bad", "±0.03 밖")
                cells += [num(up), num(m), num(d, sign=True), td(ok, raw=True)]
            rows.append(cells + [td(self.link(rel, r["run_id"]) if r else "데이터 없음: " + self.pr(rel), raw=bool(r))])
        return (table(["언어", "체크포인트", "upstream acc", "측정 acc", "Δ acc", "판정", "upstream ECE", "측정 ECE",
                       "Δ ECE", "판정", "리포트"], rows)
                + '<p class="note">MASSIVE intent 20옵션, 첫 100행, seed 13, CPU fp32 (03 §5 A2/A3). upstream: '
                + self.a("third_party/laya/BENCHMARKS.md", "BENCHMARKS.md") + " §Languages (ko :71, en :117). 기록 "
                + self.link("A/README.md") + ". A1 fixture: " + self.link("env/smoke_fixture_english_cpu.json") + ".</p>")

    def sec_d(self):
        rows = []
        for dev, ms in re.findall(r"^\s*(cpu|mps)\s+->\s+loaded on \w+\s+dtype=\S+\s+median\s+([\d.]+) ms/call",
                                  self.text("env/smoke_35_example35.log"), re.M):
            rows.append([td("스모크 3.5 example 35"), td("multilingual"), num(3, 0), td(dev.upper()), num(float(ms), 1),
                         td("median of 3, warm-up 1")])
        for dev in ("cpu", "mps"):
            for ck, ms in re.findall(r"^\s+(english|multilingual|typed-decisions)\s+(\d+) ms$",
                                     self.text(f"env/smoke_36_upstream_{dev}.log"), re.M):
                rows.append([td("스모크 3.6 upstream smoke"), td(ck), num(4, 0), td(dev.upper()), num(int(ms), 0),
                             td("median of 3, 스레드 10/14")])
        for name, label in (("mps", "MPS fp16"), ("mps_fp32", "MPS fp32 대조"), ("cpu", "CPU fp32")):
            d = self.read(f"poc/P0_sdk_{name}.json")
            if d:
                rows.append([td("P0 SDK"), td(f"multilingual · {label}"), num(7, 0), td(str(d.get("device")).upper()),
                             num(d.get("median_ms"), 2), td(f"min–max {d.get('min_ms')}–{d.get('max_ms')} ms, "
                                                           f"n={len(d.get('timed_ms') or [])}, warm-up 3")])
        smoke = sorted(self.root.glob("env/smoke_2*.ko.md"))
        m = re.search(r"laya-serve `/v1/systemone`.*?중앙값 ([\d.]+) ms",
                      self.text(smoke[-1].relative_to(self.root).as_posix() if smoke else "env/smoke_2*.ko.md"))
        if m:
            rows.append([td("스모크 3.7 laya-serve"), td("HTTP /v1/systemone, preload"), num(1, 0), td("MPS"),
                         num(float(m.group(1)), 1), td("curl time_total, 이후 5회 중앙값")])
        body = (f'<p>{chip("none", "미측정")} D1~D8(지연 행렬, 스레드 스윕, cold load, 배칭, HTTP 부하, ONNX, 메모리)은 '
                "머신 단독 조건이 갖춰질 때까지 대기다. 아래는 스모크·P0 참고값이며 정식 측정(≥10회, p95)이 아니므로 "
                "G5·G6·H8~H10 판정에 쓰지 않는다.</p>")
        return body + (table(["출처", "구성", "질문 수", "디바이스", "median ms", "비고"], rows) if rows
                       else self.missing("env/smoke_*.log"))

    def sec_b(self):
        idx = self.summary_rows()
        if not idx:
            return self.missing("B/metrics/summary_all.json")
        keys = self.base_keys(idx)

        def cell(k, model, split="all", key="accuracy"):
            r = idx.get(k + (model, split))
            return num(dig(r, key), ci=dig(r, key + "_ci"))

        acc = [[td(s), td(q), num(dig(idx.get((s, q, "multilingual", "all")), "n"), 0),
                num(dig(idx.get((s, q, "multilingual", "all")), "majority"))]
               + [cell((s, q), m) for m in RUNNERS]
               + [cell((s, q), "multilingual", sp) if s in SPLIT_SETS else num(None) for sp in ("dev", "test")]
               for s, q in keys]
        ece = [[td(s), td(q)] + [cell((s, q), m, key="ece") for m in RUNNERS] for s, q in keys]
        router = []
        for r in sorted(self.reps.values(), key=lambda r: r["rel"]):
            if r["dir"] == "B" and r["runner"] == "router":
                tot, p = sum(r["models"].values()), dig(self.read(f"B/metrics/parity_{r['set']}_router.json"), "results", 0)
                router.append([td(r["set"]), num(tot, 0), td(", ".join(f"{m} {n}" for m, n in sorted(r["models"].items()))),
                               num(r["models"].get("multilingual", 0) / tot if tot else None), num(dig(p, "flips"), 0),
                               num(dig(p, "max_abs_dp"), 4)])
        pen = []
        for rel, label in (("B/metrics/paired_penalty_ko-ml_en-ml.json", "domain_8 ko → en"),
                           ("B/metrics/paired_penalty20_ko-ml_en-ml.json", "intent-20 ko → en (n=100, 참고)")):
            for x in (self.read(rel) or {}).get("results", []):
                pen.append([td(label), td(x["split"]), num(x["n"], 0), num(x["acc_a"]), num(x["acc_b"]),
                            num(x["delta"], ci=x["delta_ci"], sign=True), pnum(x["p"])])
        return ("<h3>세트 × 러너 정확도 [95% bootstrap CI], split all</h3>"
                + table(["세트", "qid", "n", "majority", "english", "multilingual", "typed-decisions", "Router",
                         "multilingual dev", "multilingual test"], acc)
                + '<p class="note">CPU fp32, 1000 resample. dev/test는 index parity 또는 state sha256 분할(results/B/B_splits.json). '
                  "G1 입력은 ko_massive_domain_8 test. english·typed-decisions의 한국어 설명은 옵션당 22~30토큰에서 잘린다"
                  "(B_head_budget.md). ablation 변형(dev 전용)은 10절 목록.</p>"
                + "<h3>ECE (15 bins, as-shipped) [CI]</h3>" + table(["세트", "qid", "english", "multilingual", "typed-decisions", "Router"], ece)
                + '<p class="note">ECE percentile CI는 위로 편향되어 점추정이 하한 아래에 놓일 수 있다(지표성).</p>'
                + "<h3>Router auto: 답한 체크포인트(case 기준)와 multilingual 고정 대비 parity</h3>"
                + (table(["세트", "cases", "체크포인트 분포", "multilingual 비율", "flips", "max |Δp|"], router)
                   if router else self.missing("B/*_router_*.json"))
                + "<h3>한국어 페널티: 같은 MASSIVE id의 ko vs en (multilingual)</h3>"
                + (table(["비교", "split", "n", "acc ko", "acc en", "Δ = en − ko [95% Wald]", "McNemar p"], pen)
                   if pen else self.missing("B/metrics/paired_penalty_ko-ml_en-ml.json"))
                + '<p class="note">Δ가 0 근처면 페널티 없음. 한국어 서술형 설명(domain_8)에서는 페널티가 없고, '
                  "영어 key 렌더링(intent-20)에서 크다.</p>")

    def sec_c(self):
        rel, c1 = self.newest("C/*option_order*.json")
        out = []
        if not c1:
            out.append(self.missing(rel))
        else:
            sets = c1.get("sets", [])
            ms = [s["metrics"] for s in sets]
            ymax = math.ceil(max([m["any_flip_rate"] for m in ms] + [0.23]) * 10 + 0.5) / 10
            spec = {"type": "bar", "labels": [f"{s['set'].removeprefix('ko_')} · {s['metrics']['n_options']}옵션" for s in sets],
                    "series": [{"name": "per-permutation flip", "slot": 1, "data": [round(m["flip_rate_per_perm"], 4) for m in ms]},
                               {"name": "any-flip (5순열 중 ≥ 1)", "slot": 2, "data": [round(m["any_flip_rate"], 4) for m in ms]}],
                    "x": {}, "y": {"min": 0, "max": ymax, "title": "flip rate"},
                    "refs": [{"axis": "y", "value": v, "label": lb} for v, lb in FLIP_REFS]}
            out.append(self.chart("c-flip", spec, "router_v1 dev 절반, multilingual CPU fp32, 5순열(seed 13). 참고선은 "
                                  "per-permutation 정의(upstream 20옵션, Jev 제3자)와 비교한다. 출처 " + self.link(rel),
                                  "세트별 옵션 순서 flip rate 막대 차트"))
            rows = []
            for s in sets:
                m, hi = s["metrics"], dig(s, "metrics", "by_orig_conf", "[0.9, 1.0]") or {}
                f = m["flip_rate_per_perm"]
                rows.append([td(s["set"]), td(s.get("split", "")), num(m["n_items"], 0), num(m["n_options"], 0),
                             num(m["orig_accuracy"]), num(f, ci=m["flip_rate_per_perm_ci"]),
                             num(m["any_flip_rate"], ci=m["any_flip_rate_ci"]), num(hi.get("flip_rate_per_perm")),
                             num(hi.get("n"), 0), td(chip("good", "≤ 0.10") if f <= 0.10 else chip("bad", "> 0.10"), raw=True),
                             td(chip("good", "범위 안") if 0.10 <= f <= 0.30 else chip("bad", "범위 밖"), raw=True)])
            out.append(table(["세트", "split", "n", "옵션", "원 순서 acc", "per-perm flip [CI]", "any-flip [CI]",
                              "conf ≥ 0.9 flip", "conf ≥ 0.9 n", "G4", "H5 (0.10–0.30)"], rows))
        rel2, sv = self.newest("C/C_schema_v2_*.json")
        if sv:
            rows = [[td(k), num(v.get("options"), 0), num(v.get("n"), 0), num(v.get("accuracy"), ci=v.get("accuracy_ci")),
                     num(v.get("delta_vs_v1"), sign=True), pnum(dig(v, "mcnemar_vs_v1", 2)),
                     td(f"{dig(v, 'pred_counts', 'smart_home')} ({dig(v, 'gold_counts', 'smart_home')})"), num(v.get("ece"))]
                    for k, v in sv.get("variants", {}).items()]
            out.append("<h3>router schema v2 (domain_8 dev 250, v1 대비 같은 행)</h3>"
                       + table(["변형", "옵션", "n", "accuracy [CI]", "Δ vs v1", "McNemar p", "smart_home 예측 (gold)", "ECE"], rows)
                       + f'<p class="note">선택: <b>{E(str(dig(sv, "selection", "best")))}</b> 유지 (dev 순위 '
                         f'{E(", ".join(dig(sv, "selection", "ranking") or []))}, v1을 넘는 변형 없음). v2b·v2e는 general 제외 220행. '
                       + "선택과 측정이 같은 dev 절반이라 낙관 편향. 출처 " + self.link(rel2) + "</p>")
        else:
            out.append(self.missing(rel2))
        par = [[td(f"단일 state predict_batch vs laya-evals batch 16 · {s['set']}"), num(dig(s, "reference_parity", "n"), 0),
                td(f"{dig(s, 'reference_parity', 'argmax_agreement')}/{dig(s, 'reference_parity', 'n')}"),
                num(dig(s, "reference_parity", "max_abs_dp"), 4), td(self.link(rel, "C1"), raw=True)]
               for s in (c1 or {}).get("sets", [])]
        cpu = self.read("poc/P0_sdk_cpu.json")
        for name, label in (("mps", "MPS fp16 vs CPU fp32 (P0 한 문장)"), ("mps_fp32", "MPS fp32 vs CPU fp32 (P0 한 문장)")):
            other = self.read(f"poc/P0_sdk_{name}.json")
            if other and cpu:
                n, flips, dp = device_parity(other, cpu)
                par.append([td(label), num(n, 0), td(f"{n - flips}/{n}"), num(dp, 4),
                            td(self.link(f"poc/P0_sdk_{name}.json", "P0 SDK"), raw=True)])
        out.append("<h3>parity 근거 (C9 전 세트 디바이스 parity는 미측정)</h3>"
                   + table(["비교", "n (문항)", "argmax 일치", "max |Δp|", "출처"], par))
        out.append(f'<p>{chip("none", "미측정")} C2 wording 사다리 · C3 noul vs 중립 키 2-choice(H6) · C4 부정문(H7, '
                   "ko_negation_probe 미구축) · C6 고카디널리티(intent-60).</p>")
        return "".join(out)

    def sec_e(self):
        rel, e = self.newest("E/*_calibration_multilingual.json")
        if not e:
            return self.missing(rel)
        temp = dig(e, "e2", "fits", "pooled", "official", "temperature", 0)
        tname = f"refit pooled (T={temp:.4f})" if temp else "refit pooled"
        recs = [r for r in e.get("raw_records", []) if r["set"] == "ko_massive_domain_8" and r["split"] == "test"]
        out = []
        if temp and recs:
            (b0, ece0), (b1, ece1) = reliability(recs, 1.0), reliability(recs, temp)
            want0 = next((x["ece"] for x in e.get("e1", []) if (x["set"], x["split"]) == ("ko_massive_domain_8", "test")), None)
            want1 = dig(e, "e2", "fits", "pooled", "eval", "ko_massive_domain_8", "test", "official", "ece")
            agree = all(w is not None and abs(g - w) < 1e-3 for g, w in ((ece0, want0), (ece1, want1)))

            def pts(bins):
                return [{"x": round(b["conf"], 4), "y": round(b["acc"], 4), "n": b["n"]} for b in bins]
            spec = {"type": "scatter", "xName": "conf", "yName": "acc",
                    "x": {"min": 0, "max": 1, "title": "answer_confidence (bin 평균)"}, "y": {"min": 0, "max": 1, "title": "정확도"},
                    "series": [{"name": f"as-shipped (T=1), ECE {ece0:.3f}", "slot": 2, "data": pts(b0)},
                               {"name": f"{tname}, ECE {ece1:.3f}", "slot": 1, "data": pts(b1)},
                               {"name": "완전 보정 y = x", "slot": 0, "dash": True, "points": False, "tip": False,
                                "data": [{"x": 0, "y": 0}, {"x": 1, "y": 1}]}]}
            note = (f"raw_records 로짓(test {len(recs)}행)에 T를 적용해 15 bins를 다시 계산했다. 재계산 ECE 전/후 "
                    f"{ece0:.4f} / {ece1:.4f}, E1·E2 기록값 {f4(want0)} / {f4(want1)} "
                    + ("(일치)" if agree else "(불일치: 기록값이 기준)"))
            out.append("<h3>reliability diagram: ko_massive_domain_8 test</h3>"
                       + self.chart("e-rel", spec, E(note), "보정 전후 reliability diagram"))
            rng = {b: f"({b / BINS:.3f}, {(b + 1) / BINS:.3f}]" for b in range(BINS)}
            by0, by1 = {b["i"]: b for b in b0}, {b["i"]: b for b in b1}
            rows = [[td(rng[i])] + [c for by in (by0, by1) for c in (num(dig(by, i, "n"), 0), num(dig(by, i, "conf")),
                                                                      num(dig(by, i, "acc")))]
                    for i in sorted(set(by0) | set(by1))]
            out.append("<details><summary>표로 보기 (bin별 n / conf / acc)</summary>"
                       + table(["bin", "전 n", "전 conf", "전 acc", "후 n", "후 conf", "후 acc"], rows) + "</details>")
        cur = dig(e, "e3", "ko_massive_domain_8") or {}
        if cur:
            def cpts(key):
                return [{"x": round(p["coverage"], 4), "y": round(p["accuracy"], 4), "T": p["T"], "n": p["n"]}
                        for p in dig(cur, key, "curve_test") or [] if p.get("accuracy") is not None]
            series = [{"name": "as-shipped", "slot": 2, "data": cpts("as-shipped")},
                      {"name": tname, "slot": 1, "data": cpts("refit:pooled")}]
            ymin = min(0.5, math.floor(min([p["y"] for s in series for p in s["data"]] + [0.5]) * 10) / 10)
            spec = {"type": "scatter", "xName": "coverage", "yName": "acc", "series": series,
                    "x": {"min": 0, "max": 1, "title": "coverage (test, answer_confidence ≥ T)"},
                    "y": {"min": ymin, "max": 1, "title": "covered 정확도"},
                    "refs": [{"axis": "y", "value": 0.95, "label": "오류 5%"}, {"axis": "y", "value": 0.90, "label": "오류 10%"},
                             {"axis": "x", "value": 0.70, "label": "G2 coverage 0.70"}]}
            out.append("<h3>coverage@accuracy: ko_massive_domain_8 test</h3>" + self.chart(
                "e-cov", spec, "T 그리드 0.50~0.99의 test 곡선(점 = T). 아래 표는 dev에서 고른 T를 test에 적용한 값(G2의 정직한 수치).",
                "보정 전후 coverage 대 정확도 곡선"))
            curve = {k: {p["T"]: p for p in dig(cur, k, "curve_test") or []} for k in ("as-shipped", "refit:pooled")}
            rows = [[num(t, 2)] + [num(dig(curve, k, t, f)) for k in curve for f in ("coverage", "accuracy")]
                    for t in curve["as-shipped"]]
            out.append("<details><summary>표로 보기 (T별 coverage / covered 정확도)</summary>"
                       + table(["T", "전 coverage", "전 acc", "후 coverage", "후 acc"], rows) + "</details>")
            rows = []
            for cond, key in (("as-shipped", "as-shipped"), ("refit pooled", "refit:pooled")):
                for bud in ("0.05", "0.1", "0.15"):
                    dc, orc = dig(cur, key, "dev_chosen", bud) or {}, dig(cur, key, "oracle_test", bud) or {}
                    rows.append([td(cond), td(f"{float(bud):.0%}"), num(dc.get("T"), 4), num(dig(dc, "dev", "coverage")),
                                 num(dig(dc, "dev", "error")), num(dig(dc, "test", "coverage")), num(dig(dc, "test", "error")),
                                 num(orc.get("coverage")), num(orc.get("T"), 4)])
            out.append(table(["조건", "오류 예산", "T (dev)", "dev cov", "dev err", "test cov", "test err", "test oracle cov",
                              "oracle T"], rows))
        rows = []
        for fit, f in (dig(e, "e2", "fits") or {}).items():
            o = f.get("official", {})
            cells = [td(fit), num(f.get("n_dev"), 0), td(", ".join(f"{k} ({v})" for k, v in o.get("n_by_bucket", {}).items())),
                     num(dig(o, "temperature", 0), 4)]
            for s in ("ko_massive_domain_8", "ko_klue_ynat_7"):
                ev = dig(f, "eval", s, "test") or {}
                cells += [num(dig(ev, "as-shipped", "ece")), num(dig(ev, "official", "ece"), ci=dig(ev, "official", "ece_ci"))]
            rows.append(cells)
        e4 = e.get("e4") or {}
        payload = (f'채택 payload <code>{E(str(e4["payload"]))}</code> (sha256 {E(str(e4.get("payload_sha256"))[:12])}…): '
                   f'재로드 ECE {f4(e4.get("ece_reloaded"))}, E2 대비 ±0.005 '
                   f'{"일치" if e4.get("pass_within_0.005") else "불일치"}. ' if e4.get("payload") else "")
        out.append("<h3>T 표 (dev 절반 fit, test 절반 평가)</h3>"
                   + table(["fit", "dev n", "버킷 (n)", "T (choice)", "domain_8 test ECE 전", "domain_8 test ECE 후 [CI]",
                            "ynat_7 test ECE 전", "ynat_7 test ECE 후 [CI]"], rows)
                   + f'<p class="note">{payload}출처 ' + self.link(rel) + "</p>")
        return "".join(out)

    def sec_p4(self):
        st = self.text("P4/full_run_status.log").strip().splitlines()
        out = [f"<p>본 학습 상태 (<code>{E(self.pr('P4/full_run_status.log'))}</code>): "
               + (E(st[0]) + " … <b>" + E(st[-1]) + "</b>" if st else "파일 없음") + "</p>"]
        reps = [r for r in sorted(self.reps.values(), key=lambda r: r["rel"]) if r["dir"] == "P4"]
        out.append("<h3>P4 리포트 전체 (overall, full run 리포트는 생기는 대로 포함)</h3>" + table(
            ["run_id", "러너", "세트", "n", "choice_accuracy", "ECE"],
            [[td(self.link(r["rel"], r["run_id"]), raw=True), td(r["runner"]), td(r["set"]), num(r["n"], 0),
              num(r["overall"].get("choice_accuracy")), num(r["overall"].get("ece"))] for r in reps]))
        for sp in sorted(self.root.glob("P4/metrics/*_summary.json")):
            prefix = sp.name[: -len("_summary.json")]
            idx = {(r["report"], r["split"]): r for r in (self.read(sp.relative_to(self.root).as_posix()) or {}).get("results", [])}
            rows, g1 = [], None
            for pp in sorted(self.root.glob(f"P4/metrics/{prefix}_paired_*.json")):
                d = self.read(pp.relative_to(self.root).as_posix()) or {}
                m = REPORT_RE.match(Path(str(d.get("b"))).stem)
                label = m.group(3) if m else Path(str(d.get("b"))).stem
                n_all = next((x["n"] for x in d.get("results", []) if x["split"] == "all"), None)
                for x in d.get("results", []):
                    if x["split"] != "all" and x["n"] == n_all:
                        continue  # the whole file is one split: same rows as "all"
                    a, b = idx.get((d["a"], x["split"])), idx.get((d["b"], x["split"]))
                    rows.append([td(label), td(x["split"]), num(x["n"], 0), num(x["acc_a"], ci=dig(a, "accuracy_ci")),
                                 num(x["acc_b"], ci=dig(b, "accuracy_ci")), num(x["delta"], ci=x.get("delta_ci"), sign=True),
                                 pnum(x.get("p")), num(dig(a, "ece")), num(dig(b, "ece"))])
                    if label == "ko_massive_domain_8" and x["split"] == "test":
                        g1 = (x["acc_b"], dig(b, "accuracy_ci"))
            out.append(f"<h3>{E(prefix)}: base vs 파인튜닝 (같은 행 paired)</h3>" + table(
                ["세트", "split", "n", "base acc [CI]", "ft acc [CI]", "Δ [95% Wald]", "McNemar p", "ECE base", "ECE ft"], rows))
            if g1:
                ci = f" [{g1[1][0]:.3f}, {g1[1][1]:.3f}]" if g1[1] else ""
                out.append(f"<p>G1 후보 (domain_8 test, 기준 ≥ 0.80): <b>{g1[0]:.3f}{ci}</b> "
                           f"{chip('good', '기준 충족') if g1[0] >= 0.80 else chip('bad', '기준 미달')}</p>")
        for op in sorted(self.root.glob("P4/metrics/*option_order*.json")):
            for s in (self.read(op.relative_to(self.root).as_posix()) or {}).get("sets", []):
                f = dig(s, "metrics", "flip_rate_per_perm")
                if f is not None:
                    out.append(f"<p>G4 후보 ({E(op.stem)}, {E(s.get('set', ''))} {E(s.get('split', ''))}): per-permutation flip "
                               f"<b>{f:.3f}</b> {chip('good', '≤ 0.10') if f <= 0.10 else chip('bad', '> 0.10')}</p>")
        out.append('<p class="note">프로브: 1,000행 1 epoch, MPS 학습 / CPU fp32 평가. test 수치는 파이프라인 확인용이고 full run의 '
                   "하이퍼파라미터는 dev로만 고른다. 기록 " + self.link("P4/P4_probe_20261002.md") + "</p>")
        return "".join(out)

    def sec_f(self):
        idx = self.summary_rows()
        if not idx:
            return self.missing("B/metrics/summary_all.json")
        rows = [[td(s), td(q), num(r["n"], 0), td(r.get("majority_label", "")), num(r.get("majority")), num(r.get("random")),
                 num(r.get("accuracy")), num(r.get("delta_vs_majority"), sign=True), td("미측정", "na")]
                for s, q in self.base_keys(idx) for r in [idx.get((s, q, "multilingual", "all"))] if r]
        return (table(["세트", "qid", "n", "majority 레이블", "majority", "random", "multilingual", "Δ vs majority",
                       "LLM zero-shot (F2)"], rows)
                + f'<p>{chip("none", "미측정")} F2 LLM zero-shot(API 키·비용 승인 대기) · F3 supervised 문헌값 미조회. '
                  "G1은 LLM 베이스라인이 없어 절대 기준 0.80을 쓴다(00 §6).</p>" + self.sec_f_jev())

    def sec_f_jev(self):
        # F5: Jev 수동 비교(공개 플레이그라운드, n=24). 두 파일이 모두 있을 때만 그린다.
        sample = self.text("F/jev_sample_24.jsonl")
        raw = self.text("F/jev_runs_raw.jsonl")
        if not sample or not raw:
            return self.missing("F/jev_sample_24.jsonl, F/jev_runs_raw.jsonl")
        rows = [json.loads(l) for l in sample.splitlines() if l.strip()]
        jev = {}  # row_index -> 마지막 성공 attempt
        for l in raw.splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("decision_key") is not None:
                jev[r["row_index"]] = r
        n = len(rows)
        counts = [("Jev (typesafe-ai/jev, 플레이그라운드)", sum(1 for r in rows if jev.get(r["row_index"], {}).get("decision_key") == r["gold"])),
                  ("Laya zero-shot (multilingual)", sum(1 for r in rows if r["laya_zs"] == r["gold"])),
                  ("Laya ft-v1", sum(1 for r in rows if r["laya_ft"] == r["gold"]))]
        body = [[td(name), num(c, 0), num(c / n if n else None)] for name, c in counts]
        ms = sorted(r["ms"] for r in jev.values() if isinstance(r.get("ms"), (int, float)))
        med = ms[len(ms) // 2] if len(ms) % 2 else (ms[len(ms) // 2 - 1] + ms[len(ms) // 2]) / 2 if ms else None
        answered = sum(1 for r in rows if r["row_index"] in jev)
        return (f'<h3>F5 Jev 수동 비교 파일럿 (공개 플레이그라운드, n={n})</h3>'
                + table(["시스템", f"정답/{n}", "정확도"], body)
                + f'<p>Jev 응답 {answered}/{n}행, 표시 지연("server + network") 중앙값 {fnum(med, 1) if med is not None else "n/a"} ms. '
                  "단일 패스 수동 표본이라 방향성 확인용. 8과제 통제 비교는 위 Laya vs Jev (주 결과) 절. "
                  "출처 <code>results/F/jev_playground_manual_20261006.md</code>.</p>")

    def sec_jev(self):
        # 주 결과(S6): 같은 state·질문·옵션 문자열로 Jev와 zero-shot Laya를 비교. 값은 summary.json에서만 읽는다.
        rel = "F/jev_cmp/summary.json"
        d = self.read(rel)
        if not d:
            return self.missing(rel)
        st = {"Jev 유의 우세": "bad", "비유의": "none", "Laya 유의 우세": "good"}  # Laya 관점
        rows = []
        for t, x in d["tasks"].items():
            s, best = x["systems"], x["best_laya"]
            m = x["mcnemar"][best]
            rows.append([td(f"{t} {x['name']}"), num(s["jev"]["n"], 0), td(x["in_training_mix"].split(" (")[0]),
                         num(s["jev"]["acc"], ci=s["jev"]["wilson"]),
                         *(num(s[r]["acc"]) for r in ("english", "multilingual", "router")), td(best),
                         td(f"{m['b']} / {m['c']}"), pnum(m["p"]), pnum(x["holm_p"]),
                         td(chip(st[x["verdict"]], x["verdict"]), raw=True),
                         td(chip(st[x["verdict_holm"]], x["verdict_holm"]), raw=True)])
        ag, lat, req = d["aggregate"], d["latency_tokens"]["all"], d["meta"]["requests"]
        mac, pool, ref = ag["macro"], ag["pooled_mcnemar"]["best"], d["references"]["t1_typed_decisions"]
        tally = lambda v: " · ".join(f"{k} {v.get(k, 0)}" for k in st)
        ci = lambda c: f"{fnum(c['diff'], sign=True)} [{fnum(c['ci'][0], sign=True)}, {fnum(c['ci'][1], sign=True)}]"
        holm = ", ".join(t for t, x in d["tasks"].items() if x["verdict_holm"] != "비유의")
        clus = " · ".join(f"{t} Jev − {d['tasks'][t]['best_laya']} {ci(ag['cluster_bootstrap'][t][d['tasks'][t]['best_laya']])}"
                          for t in ("T1", "T7"))
        days = ", ".join(f"{k} {n}" for k, n in req["by_day"].items())
        lines = [
            f"macro 정확도(8과제 단순 평균): Jev {fnum(mac['acc']['jev'])} · english {fnum(mac['acc']['english'])} · "
            f"multilingual {fnum(mac['acc']['multilingual'])} · Router {fnum(mac['acc']['router'])} · 과제별 최고 Laya "
            f"{fnum(mac['acc']['best'])}. Jev − Router {ci(mac['diff']['router'])} (과제 bootstrap {mac['resamples']:,}회, 기술통계)",
            f"독립 단일 문항 {pool['n']}개 합산 exact McNemar(과제별 최고 Laya): Jev {pool['jev_correct']}, Laya "
            f"{pool['laya_correct']}, b/c {pool['b']}/{pool['c']}, p {f4(pool['p'])}",
            f"군집 bootstrap: {clus}",
            f"Jev 지연: 표시값 'server + network' 중앙 {fnum(lat['displayed_ms']['median'], 1)} ms, 브라우저 POST 중앙 "
            f"{fnum(lat['browser_post_ms']['median'], 1)} ms(성공 {lat['requests']}건, 인터넷 왕복 포함). Laya 로컬 지연은 그림 3. "
            f"Jev 비용 1,000 decision당 ${lat['cost_per_1k_dec_usd']:.4f}(제3자 인용 단가, 확인 필요)",
            f"참고선(zero-shot 아님): T1 typed-decisions 파인튜닝 체크포인트 {ref['correct']}/{ref['n']}, Jev 대비 b/c "
            f"{ref['mcnemar_vs_jev']['b']}/{ref['mcnemar_vs_jev']['c']}, p {f4(ref['mcnemar_vs_jev']['p'])}",
            f"사이트 요청 {req['total_site']}회({days}), HTTP 502 {req['http_502_total']}회, 429 {req['http_429_total']}회"]
        imgs = ""
        for f, cap in (("accuracy_by_task", "그림 1. 과제별 정확도와 Wilson 95% CI"), ("t7_languages", "그림 2. T7 언어별 정확도"),
                       ("latency", "그림 3. 배포 형태별 지연 (로그 축)")):
            frel = f"F/jev_cmp/figs/{f}.png"
            path = self.root / frel
            self.used.setdefault(self.pr(frel), path.exists())
            href = os.path.relpath(path.resolve(), self.out.parent.resolve())
            imgs += (f'<figure class="fig"><img src="{E(href)}" alt="{E(cap)}" loading="lazy"><figcaption>{E(cap)}</figcaption></figure>'
                     if path.exists() else self.missing(frel))
        return (f'<p class="verdict"><b>Holm 보정 후: {E(tally(ag["verdicts_holm"]))} (유의 {E(holm or "없음")})</b></p>'
                f'<p>보정 전(과제별 α 0.05): {E(tally(ag["verdicts"]))}</p>'
                + table(["과제", "n", "Laya 학습 믹스", "Jev [Wilson 95%]", "Laya english", "Laya multilingual", "Laya Router", "최고 Laya",
                         "b / c", "McNemar p", "Holm p", "판정", "Holm 후"], rows)
                + "<ul>" + "".join(f"<li>{E(x)}</li>" for x in lines) + "</ul>" + imgs
                + '<p class="note">칩은 Laya 관점이다(✗ Jev 유의 우세, – 비유의, ✓ Laya 유의 우세). b는 Jev만 정답, c는 최고 Laya만 '
                  "정답인 항목 수이고, 판정은 과제별 exact McNemar(양측 α 0.05), Holm 열은 8개 검정 보정이다. 학습 믹스는 upstream "
                  "build_benchmark_nb.py:760-762 기준(no와 held out은 같은 뜻). 독립 플레이그라운드 경유"
                  "(API 아님, 모델 버전 미표기, 확률 2자리 반올림), 과제당 n=40. 출처 " + self.a("results/F/jev_cmp/summary.md") + ".</p>")

    def sec_t3arm(self):
        # 3-arm 확장(S3): Jev vs vanilla Laya vs trained Laya. 수치는 T3arm/summary.json에서만 읽는다.
        rel = "T3arm/summary.json"
        d = self.read(rel)
        if not d:
            return self.missing(rel)
        T, ag, V, meta, rp = d["tasks"], d["aggregate"], d["validity"], d["meta"], d["repeat"]
        cat, na = {"incl": "포함", "excl": "제외"}, td("미측정", "na")
        ci = lambda m, c, s=True: f"{fnum(m, sign=s)} [{fnum(c[0], sign=s)}, {fnum(c[1], sign=s)}]"

        def vchip(v, good):  # Laya 관점: good arm의 유의 우세면 ✓, 상대 arm의 유의 우세면 ✗
            return td(chip("none" if v == "비유의" else "good" if v.startswith(good) else "bad", v), raw=True)

        rows = []
        for t, x in T.items():
            i, ts = x["items"], x["items"]["tests"]
            j = ts.get("trained_vs_jev")
            rows.append([td(f"{t} {x['name']}"), td(cat[x["category"]]), num(i["n"], 0)]
                        + [num(i[a]["acc"], ci=i[a]["wilson"]) if i[a] else na for a in ("jev", "vanilla", "trained")]
                        + ([td(f"{j['b']} / {j['c']}"), pnum(j["p"]), pnum(j["holm_p"]), vchip(j["verdict"], "trained"),
                            vchip(j["verdict_holm"], "trained")] if j else [na] * 5)
                        + [vchip(ts["trained_vs_vanilla"]["verdict_holm"], "trained"),
                           vchip(ts["jev_vs_vanilla"]["verdict_holm"], "vanilla") if "jev_vs_vanilla" in ts else na])
        tj = [x["items"]["tests"]["trained_vs_jev"] for x in T.values() if "trained_vs_jev" in x["items"]["tests"]]
        tally = lambda k: " · ".join(f"{v} {sum(s[k] == v for s in tj)}" for v in ("trained 유의 우세", "비유의", "Jev 유의 우세"))
        pre = ", ".join(t for t, x in T.items() if dig(x, "items", "tests", "trained_vs_jev", "verdict") not in (None, "비유의"))
        ext, up = [], {c: [] for c in cat}
        for t, x in T.items():
            e, s = x["ext"], x["ext"]["test"]
            ext.append([td(f"{t} {x['name']}"), td(cat[x["category"]]), num(e["n"], 0),
                        *(num(e[a]["acc"], ci=e[a]["wilson"]) for a in ("vanilla", "trained")),
                        num(s["boot"]["diff"], ci=s["boot"]["ci"], sign=True), td(f"{s['b']} / {s['c']}"), pnum(s["p"]),
                        pnum(s["holm_p"]), vchip(s["verdict_holm"], "trained")])
            if s["verdict_holm"].startswith("trained"):
                up[x["category"]].append(t)
        ncat = collections.Counter(x["category"] for x in T.values())
        arms = {"jev": "Jev", "vanilla": "vanilla", "trained": "trained"}
        diffs = {"jev-vanilla": "Jev − vanilla", "trained-vanilla": "trained − vanilla", "trained-jev": "trained − Jev"}
        layers = (("items", "Jev 항목"), ("ext", "ext"))
        mac = [[td(ln), td(arms[a]), num(c["incl"]["mean"], ci=c["incl"]["ci"]), td("·".join(c["incl"]["tasks"])),
                num(c["excl"]["mean"], ci=c["excl"]["ci"]), td("·".join(c["excl"]["tasks"]))]
               for k, ln in layers for a, c in ag[k]["macro"].items()]
        dif = [[td(ln), td(diffs[a])] + [num(c[b]["mean"], ci=c[b]["ci"], sign=True) for b in ("incl", "excl")]
               + [num(c["contrast"]["diff"], ci=c["contrast"]["ci"], sign=True)] for k, ln in layers for a, c in ag[k]["diff"].items()]
        v1, v2, v3, v4, v5, v6 = (V[k] for k in ("V1", "V2", "V3", "V4", "V5", "V6"))
        e, m = v1["english"], v1["multilingual"]
        vrows = [
            ("V1 zero-step identity", f"텐서 값 english {e['values_equal']}/{e['tensors']}, multilingual {m['values_equal']}/{m['tensors']} 동일, "
             f"argmax {e['argmax']}/{e['decisions']}, {m['argmax']}/{m['decisions']}. refit만으로 ECE english {fnum(e['ece_base_t'])} → "
             f"{fnum(e['ece_refit_t'])}, multilingual {fnum(m['ece_base_t'])} → {fnum(m['ece_refit_t'])}", v1["met"], "통과"),
            ("V2 upstream 재현", f"(a) upstream 체크포인트 {fnum(v2['upstream']['acc_vs_label'])} (공개 {fnum(v2['published'])}, "
             f"±{fnum(v2['tolerance'], 2)}) (b) 우리 학습 {fnum(v2['ours']['acc_vs_label'])} (기준 ≥ {fnum(v2['min'])}, majority "
             f"{fnum(v2['majority'])})", v2["met"], "통과"),
            ("V3 label-shuffle", f"실제 라벨 epoch 1 {fnum(v3['real_ep1_s2'])} − permuted {fnum(v3['permuted'])} = {fnum(v3['b_diff'], sign=True)} "
             f"(기준 ≥ {fnum(v3['gap'], 2)}), permuted < vanilla {fnum(v3['vanilla_s2'])}. 엄격 기준(permuted ≤ majority + "
             f"{fnum(v3['margin'], 2)} = {fnum(v3['a_threshold'])})은 {fnum(v3['a_excess'], sign=True)} 미달",
             v3["user"]["verdict"] == "통과", f"{v3['user']['verdict']} (사용자 판정 {v3['user']['date']})"),
            ("V4 형식 동일성", f"{v4['tasks']}과제, 추론 시퀀스·토큰 일치 {v4['identical']}/{v4['checked']}, 옵션 decode·target 점검 "
             f"{v4['items_decoded']:,} items", v4["identical"] == v4["checked"], "통과"),
            ("V5 smoke", f"english {fnum(v5['english'], 2)}, multilingual {fnum(v5['multilingual'], 2)} items/s. 드라이버 SMOKE STEP OK "
             f"{v5['smoke_ok']}, FAILED {v5['smoke_failed']}", v5["smoke_failed"] == 0, "통과"),
            ("V6 누수", f"{v6['tasks']}과제 train·dev·calib와 평가 텍스트의 교집합 정확 {v6['exact']} / 정규화 {v6['normalized']}. 추출 전 제거 "
             + ", ".join(f"{k} {n}" for k, n in v6["removed_before_sampling"].items()), v6["exact"] == v6["normalized"] == 0, "통과")]
        val = [[td(k), td(s), td(chip("good", lb) if ok else chip("bad", "미달"), raw=True)] for k, s, ok, lb in vrows]
        dg = []
        for t, x in T.items():
            g, fl = x["diag"], x["diag"]["flip"]
            dg.append([td(f"{t} {x['name']}"), td(x["base"]), *(num(v) for v in g["dev"]),
                       td(f"{g['selected_epoch']}" + (" (재보정)" if g["recalibrated"] else "")), num(g["gap"], sign=True),
                       num(fl["flip_rate_per_perm"], ci=fl["flip_rate_per_perm_ci"]) if fl else td("choice 아님", "na"),
                       td(chip("part", "예"), raw=True) if g["failed"] else td("아니오"),
                       td(T3ARM_FAIL_CAUSE.get(t, "원인 미기록") if g["failed"] else "")])
        ft = max((t for t in T if T[t]["diag"]["flip"]), key=lambda t: T[t]["diag"]["flip"]["flip_rate_per_perm"])
        gt = max(T, key=lambda t: T[t]["diag"]["gap"])
        r = V["T1_rerun"]
        lab = collections.Counter(x["cost"]["labels"] for x in T.values()).most_common(1)[0][0]
        loop = {t: x["cost"]["train_loop_min"] for t, x in T.items()}
        lo, hi = min(loop, key=loop.get), max(loop, key=loop.get)
        ckpt = {x["base"]: x["cost"]["ckpt_gb"] for x in T.values()}
        jv, tv, fx = ag["items"]["diff"]["jev-vanilla"], ag["ext"]["diff"]["trained-vanilla"], T[ft]["diag"]["flip"]
        lines = [
            f"ext trained vs vanilla (Holm 후): 학습 제외 과제 {len(up['excl'])}/{ncat['excl']} 유의 상승, 포함 과제 "
            f"{len(up['incl'])}/{ncat['incl']} 유의 상승({', '.join(up['incl']) or '없음'})",
            f"Q1 difference-in-differences (Jev 항목, Jev − vanilla): {ci(jv['contrast']['diff'], jv['contrast']['ci'])}. ext 학습 이득"
            f"(trained − vanilla)의 제외 − 포함은 {ci(tv['contrast']['diff'], tv['contrast']['ci'])}",
            f"비용(Q3): 과제당 라벨 {lab:,}개("
            + ", ".join(f"{t} {x['cost']['labels']:,}" for t, x in T.items() if x["cost"]["labels"] != lab)
            + f"), M4 Pro MPS fp32 학습 loop 과제당 {fnum(loop[lo], 1)}분({lo})-{fnum(loop[hi], 1)}분({hi}), 체크포인트 "
            + ", ".join(f"{b} {fnum(gb, 2)} GB" for b, gb in ckpt.items()),
            f"같은 설정 T1 재학습 편차: test 정확도(label 기준) 준비 V2(b) {fnum(r['runs']['v2b']['acc_vs_label'])} 대 본 학습 "
            f"{fnum(r['runs']['s2']['acc_vs_label'])}, 짝 비교 b/c {r['test']['b']}/{r['test']['c']}, exact McNemar p {r['test']['p']:.1e}, "
            f"차이(argmax gold) {ci(r['test']['boot']['diff'], r['test']['boot']['ci'])}(case 군집 bootstrap). micro-batch 손실이 "
            f"{r['trace']['first_diff']}번에서 처음 갈라진다(MPS 비결정성). 그래서 trained 수치는 과제당 run 하나의 표본이다",
            f"주의할 진단: 옵션 순서 flip이 가장 높은 과제는 {ft}({ci(fx['flip_rate_per_perm'], fx['flip_rate_per_perm_ci'], False)}), "
            f"train − dev가 가장 큰 과제는 {gt}({fnum(T[gt]['diag']['gap'])})"]
        sysname = {"jev": "Jev", "english": "vanilla english", "multilingual": "vanilla multilingual", "trained": "trained"}
        lines += [f"{t} 라벨 점검: {len(c['systems'])}개 시스템({', '.join(sysname[s] for s in c['systems'])})이 모두 틀린 행 "
                  f"{c['all_wrong']['wrong']}/{c['all_wrong']['n']}. 라벨 품질 의심, 수작업 확인 필요"
                  for t, c in ((t, x["items"]["label_check"]) for t, x in T.items() if "label_check" in x["items"])]
        cal = []
        for t, x in T.items():
            c = x["calib"]
            clamp = ", ".join(f"{q} {fnum(a)} → {fnum(b)}" for q, a, b in zip(("choice", "score", "noul"), c["temperature_raw"],
                                                                                 c["temperature_applied"]) if a != b)
            cal.append([td(f"{t} {x['name']}")] + [td(f"{fnum(c['effect'][k][q]['refit'], sign=True)} / {fnum(c['effect'][k][q]['train'], sign=True)}")
                                                   for k in ("items", "ext") for q in ("ece", "brier")] + [td(clamp or "없음")])
        cs = ag["calib_same"]
        hp = lambda y: f"{y['verdict_holm']} ({fnum(y['holm_p'], 4) if y['holm_p'] >= 1e-3 else format(y['holm_p'], '.1e')})"
        side = lambda z, f: z["ext"]["test"] if f == "ext" else z["items"]["tests"][f]
        agree = []
        for t, x in T.items():
            r = rp["tasks"][t]
            for f, lb in (("trained_vs_jev", "Jev 항목 trained vs Jev"), ("trained_vs_vanilla", "Jev 항목 trained vs vanilla"),
                          ("ext", "ext trained vs vanilla")):
                a = r["agree"][f] if r["done"] else "결과 없음"
                agree.append([td(f"{t} {x['name']}"), td(lb), td(hp(side(x, f))),
                              td(hp(side(r, f))) if r["done"] else td("결과 없음", "na"),
                              td(chip({"확정": "good", "불일치": "bad"}.get(a, "none"), a), raw=True)])
        g2 = rp["agree"]
        dec = [[td(k), td(s), td(chip("good", "해결") if st == "해결" else chip("part", "진행 중(사용자 승인 2026-10-08)"), raw=True),
                td(res), td(f"<code>{E(p)}</code>" if p else "", raw=True)]
               for k, s, st, res, p in T3ARM_DECISIONS]
        nojev = [t for t, x in T.items() if not x["items"]["jev"]]
        imgs = ""
        for k, (f, cap) in enumerate((("accuracy_3arm", "과제별 3-arm 정확도 (Jev 항목)"), ("ext_trained_minus_vanilla", "ext: trained − vanilla"),
                                      ("dev_curves", "과제별 dev 곡선"), ("category_macro", "범주별 arm macro")), 4):
            frel, cap = f"T3arm/figs/{f}.png", f"그림 {k}. {cap}"
            path = self.root / frel
            self.used.setdefault(self.pr(frel), path.exists())
            href = os.path.relpath(path.resolve(), self.out.parent.resolve())
            imgs += (f'<figure class="fig"><img src="{E(href)}" alt="{E(cap)}" loading="lazy"><figcaption>{E(cap)}</figcaption></figure>'
                     if path.exists() else self.missing(frel))
        return (f'<p class="verdict"><b>trained vs Jev, Holm 보정 후: {E(tally("verdict_holm"))} ({len(tj)}과제)</b></p>'
                f'<p>보정 전(과제별 α 0.05): {E(tally("verdict"))} (trained 유의 우세 {E(pre or "없음")}). 아래 trained는 '
                f'run 1(seed {rp["seeds"][0]})이다. 판정은 seed {rp["seeds"][1]} 반복 학습(run 2)과 결론이 같은 것만 확정한다(run 2 결과 '
                f'{len(rp["done"])}/{len(T)}과제: 확정 {rp["agree"]["confirmed"]} · 불일치 {rp["agree"]["disagree"]} · 결과 없음 '
                f'{rp["agree"]["missing"]}, 판정 일치표). 상태 <code>{E(meta["status_last"])}</code> '
                f'({E(meta["status_log"])}), 결과 {len(meta["done"])}/{len(T)}과제, S3 {E(meta["built_kst"])}.</p>'
                + "<h3>Jev 항목 3-arm (Q2)</h3>"
                + table(["과제", "범주", "n", "Jev [Wilson 95%]", "vanilla", "trained", "trained vs Jev b / c", "McNemar p", "Holm p", "판정",
                         "Holm 후", "trained vs vanilla (Holm 후)", "Jev vs vanilla (Holm 후)"], rows)
                + "<h3>ext: vanilla vs trained</h3>"
                + table(["과제", "범주", "n", "vanilla [Wilson 95%]", "trained", "trained − vanilla [bootstrap 95%]", "b / c", "McNemar p",
                         "Holm p", "Holm 후"], ext)
                + "<h3>범주 집계 (Q1)</h3>"
                + table(["기준", "arm", "포함 macro [95%]", "포함 과제", "제외 macro [95%]", "제외 과제"], mac)
                + table(["기준", "차이", "포함 평균 [95%]", "제외 평균 [95%]", "제외 − 포함 [95%]"], dif)
                + "<ul>" + "".join(f"<li>{E(x)}</li>" for x in lines) + "</ul>"
                + "<h3>보정 분리: refit 효과와 학습 효과</h3>"
                + table(["과제", "Jev 항목 ECE: refit / 학습", "Jev 항목 Brier: refit / 학습", "ext ECE: refit / 학습", "ext Brier: refit / 학습",
                         "temperature clamp (fit → 로드)"], cal)
                + f'<p class="note">refit 효과 = (vanilla + 과제 T) − vanilla, 학습 효과 = trained − (vanilla + 과제 T)이고 음수면 그 지표가 '
                  f'낮아진(좋아진) 것이다. vanilla + 과제 T는 base 가중치에 그 과제 calib로 맞춘 temperature만 넣은 0-step export라 답이 '
                  f'vanilla와 같다(argmax 일치 {cs["argmax_agreement"]:,}/{cs["decisions"]:,}, 반올림 동률 포함 {cs["argmax_agreement_ties_agree"]:,}/'
                  f'{cs["decisions"]:,}, 정답 여부 {cs["correct_identical"]:,}/{cs["decisions"]:,}). clamp는 fit 값을 laya가 로드 때 자른 값이다.</p>'
                + "<h3>학습 검증 (Q4)</h3>" + table(["검증", "핵심 수치", "판정"], val)
                + table(["과제", "base", "dev epoch 0 (vanilla)", "epoch 1", "epoch 2", "선택 epoch", "train − dev", "flip dev40 [95%]",
                         "학습 실패 표시", "원인 (파이프라인 실패 아님)"], dg)
                + f"<h3>반복 학습 판정 일치표 (run 1 seed {rp['seeds'][0]}, run 2 seed {rp['seeds'][1]})</h3>"
                + f'<p>run 2 결과 {len(rp["done"])}/{len(T)}과제({E("·".join(rp["done"]) or "없음")}), 상태 <code>{E(str(rp["status_last"]))}</code> '
                  f'({E(rp["status_log"])}). 결론: 확정 {g2["confirmed"]} · 불일치 {g2["disagree"]} · 결과 없음 {g2["missing"]} '
                  f'(비교 {g2["comparisons"]}개).'
                + (f' run 2의 Holm family는 결과 있는 {len(rp["done"])}과제라 run 1({len(T)}과제)보다 보정이 약하고, 남은 과제가 끝나 다시 '
                   "계산하면 판정이 바뀔 수 있다." if rp["missing"] else "") + "</p>"
                + table(["과제", "비교", "run 1 판정 (Holm p)", "run 2 판정 (Holm p)", "결론"], agree)
                + '<p class="note">확정 = 두 run의 Holm 후 판정이 같음. run 2의 Holm은 run 2에 결과 있는 과제끼리 따로 했다. vanilla·Jev·'
                  "vanilla + 과제 T는 학습이 없어 두 run에 같다.</p>"
                + "<h3>사용자 결정과 후속 작업 (2026-10-08 15:25)</h3>"
                + table(["항목", "결정", "상태", "결과", "출력"], dec) + imgs
                + '<p class="note">칩은 Laya arm 관점이다(✓ trained 유의 우세, Jev vs vanilla 열은 vanilla 유의 우세 · – 비유의 · ✗ 상대 arm 유의 '
                  "우세). b는 앞 arm만, c는 뒤 arm만 정답인 항목 수이고 판정은 exact McNemar(양측 α 0.05), Holm은 family마다(trained vs Jev "
                  f"{len(tj)}과제, trained vs vanilla {len(T)}과제, Jev vs vanilla {sum('jev_vs_vanilla' in x['items']['tests'] for x in T.values())}과제). "
                  "ext 차이는 paired bootstrap(T1 case, T7 id 군집). 범주 구간은 과제 재표본이라 "
                  "기술통계다. trained는 과제 라벨로 학습한 전문화 비교이고 ECE·Brier에는 temperature refit 효과가 섞인다(V1, 보정 분리 표). Jev는 "
                  "독립 플레이그라운드 경유이고 "
                  + (f"{'·'.join(nojev)}은 미측정이다" if nojev else f"T9·T10은 세션 S7({meta['s7']['session_dir']}) 기록이다")
                  + ". 학습 실패 표시는 모든 epoch의 dev가 epoch 0보다 낮음(docs/11 §4). "
                  "출처 " + self.a("results/T3arm/summary.md") + " · " + self.a("results/T3arm/PREP_20261008.md") + " · "
                + self.a("docs/11_three_arm_plan.md") + ".</p>")

    def sec_h(self):
        v = self.read("verdicts.json")
        if not v:
            return self.missing("verdicts.json")
        crit = {c[0].split()[0]: c for c in self.doc_rows("docs/03_benchmark_plan.ko.md", r"^\| H\d+ ") if c}
        rows = [[td(md_inline(dig(crit, h, 0) or h), raw=True), td(md_inline(dig(crit, h, 1) or ""), raw=True),
                 td(md_inline(dig(crit, h, 2) or ""), raw=True),
                 td(chip(verdict_state(x.get("verdict")), x.get("verdict") or "—"), raw=True),
                 td(E(x.get("note", "")) + '<div class="src">' + self.sources(x.get("source", []), x.get("run_ids", []))
                    + "</div>", raw=True)] for h, x in v.items() if re.fullmatch(r"H\d+", h)]
        return table(["가설", "트랙", "판정 기준 (03 §1)", "판정", "해석 · 근거"], rows) + (
            '<p class="note">판정 원본은 results/verdicts.json(수동 유지), 기준은 docs/03_benchmark_plan.md §1 표에서 읽었다.</p>')

    def sec_g(self, gates, crit, auto):
        if not gates:
            return self.missing("go_no_go.json")
        rows = []
        for g, x in gates.items():
            calc, val = auto.get(g), x.get("value")
            match = "—" if calc is None or val is None else "✓ 일치" if abs(calc - val) <= 6e-4 else "≠ 불일치"
            rows.append([td(g), td(md_inline(dig(crit, g, 1) or ""), raw=True), td(md_inline(dig(crit, g, 2) or ""), raw=True),
                         td(md_inline(dig(crit, g, 3) or ""), raw=True), vnum(val), td(gate_chip(x.get("pass")), raw=True),
                         num(calc, 4), td(match),
                         td(E(x.get("note", "")) + '<div class="src">' + self.sources(x.get("source", []), x.get("run_ids", []))
                            + "</div>", raw=True)])
        return table(["#", "기준", "트랙", "기준값 (00 §6, 제안값)", "측정값", "판정", "계산값 (리포트 JSON)", "대조",
                      "주석 · 근거"], rows) + (
            '<p class="note">측정값·판정은 results/go_no_go.json(수동 유지, pass null = 대기). 계산값은 이 스크립트가 결과 JSON에서 '
            "다시 읽은 값이다(G0 K2 리포트, G1 B summary, G2·G3 E, G4 C1, G7 P0 SDK). 판정 규칙: G0 미통과면 보류, "
            "G1·G2·G5 미달이면 No-Go 또는 P4 후 재평가, G3·G4·G6·G7 미달이면 조건부 Go.</p>")

    def sec_runs(self):
        rows = []
        for r in sorted(self.reps.values(), key=lambda r: r["rel"]):
            md, c = Path(r["rel"]).with_suffix(".md").as_posix(), r["config"]
            rev = str(next(iter((c.get("revisions") or {}).values()), "") or "")
            links = self.link(r["rel"], r["run_id"]) + (" · " + self.link(md, "md") if (self.root / md).exists() else "")
            rows.append([td(r["dir"]), td(links, raw=True), td(r["runner"]), td(r["set"]), num(r["n"], 0),
                         num(r["overall"].get("choice_accuracy")), num(r["overall"].get("ece")),
                         td(str(c.get("dataset_sha256") or "")[:12], "mono"), td(str(c.get("questions_sha256") or "")[:12], "mono"),
                         td(str(c.get("laya_version") or "")),
                         td(rev[:12] if re.fullmatch(r"[0-9a-f]{40}", rev) else rev, "mono")])
        files = [[td(self.a(p, p) if ok else E(p), raw=True), td("읽음" if ok else "없음")] for p, ok in self.used.items()]
        return ("<h3>laya-evals 리포트 (config 블록으로 탐지)</h3>"
                + table(["트랙", "run_id", "러너", "세트", "n", "choice_accuracy", "ECE", "dataset sha256", "questions sha256", "laya",
                         "revision"], rows)
                + "<h3>이 페이지가 읽은 그 밖의 파일</h3>" + table(["경로", "상태"], files))

    # ------------------------------------------------------------------ page
    def build(self, stamp=None):
        raw_gates = self.read("go_no_go.json") or {}
        gates = {k: v for k, v in raw_gates.items() if isinstance(v, dict) and k[:1] == "G"}
        self.gates_meta = {k: v for k, v in raw_gates.items() if not isinstance(v, dict)}
        crit = {c[0]: c for c in self.doc_rows("docs/00_README.ko.md", r"^\| G\d ") if c}
        auto = self.auto_gates()
        secs = [("summary", "1. 요약", self.sec_summary(gates, crit)), ("jev", "Laya vs Jev (주 결과)", self.sec_jev()),
                ("t3arm", "3-arm: Jev vs vanilla vs trained Laya", self.sec_t3arm()),
                ("track-a", "2. Track A 재현", self.sec_a()),
                ("track-d", "3. Track D 성능", self.sec_d()), ("track-b", "4. Track B 한국어 품질", self.sec_b()),
                ("track-c", "5. Track C 견고성", self.sec_c()), ("track-e", "6. Track E 캘리브레이션", self.sec_e()),
                ("p4", "P4 파인튜닝", self.sec_p4()), ("track-f", "7. Track F 베이스라인", self.sec_f()),
                ("hypotheses", "8. 가설 H1~H10", self.sec_h()), ("gates", "9. Go/No-Go", self.sec_g(gates, crit, auto)),
                ("runs", "10. run_id 목록", self.sec_runs())]
        nav = "".join(f'<a href="#{sid}">{E(t)}</a>' for sid, t, _ in secs)
        body = "".join(f'<section id="{sid}"><h2>{E(t)}</h2>{h}</section>' for sid, t, h in secs)
        data = json.dumps(self.charts, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        foot = "scripts/build_dashboard.py가 results/ JSON에서 생성. REPORT.md와 수치가 다르면 JSON이 기준(03 §12)."
        if stamp:
            foot += f" 생성 시각 {stamp}."
        return (HEAD + '<header><h1>Laya 벤치마크 대시보드: Laya vs Jev · 한국어 PoC</h1><p class="sub">Laya vs Jev · Track A~F · P4 파인튜닝 · 가설 H1~H10 · '
                f'Go/No-Go G0~G7</p><nav>{nav}</nav></header><main>{body}</main><footer><p class="note">{E(foot)}</p></footer>'
                f'<script type="application/json" id="chart-data">{data}</script><script src="{CHART_JS}"></script>'
                f"<script>{JS}</script></body></html>\n")


HEAD = """<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Laya 벤치마크 대시보드</title><style>
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);--s1:#2a78d6;--s2:#eb6834;--good:#0ca30c;--part:#fab219;--bad:#d03b3b;--none:#898781;--link:#256abf}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);--s1:#3987e5;--s2:#d95926;--link:#86b6ef}}
*{box-sizing:border-box}body{margin:0;background:var(--page);color:var(--ink);font:14px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
header,main,footer{max-width:1180px;margin:0 auto;padding:0 16px}header{padding-top:28px}h1{font-size:24px;margin:0 0 4px}
.sub{color:var(--ink2);margin:0 0 10px}nav{display:flex;flex-wrap:wrap;gap:4px 14px;padding:8px 0 12px;border-bottom:1px solid var(--grid)}
nav a{color:var(--ink2);text-decoration:none;font-size:13px}nav a:hover{color:var(--ink);text-decoration:underline}
section{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:18px 20px;margin:18px 0}
h2{font-size:18px;margin:0 0 10px}h3{font-size:14px;margin:20px 0 6px;color:var(--ink2)}p{margin:6px 0}a{color:var(--link)}
code,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}code{background:var(--page);padding:0 4px;border-radius:4px;overflow-wrap:anywhere}
.tw{overflow-x:auto;margin:8px 0}table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:5px 8px;border-bottom:1px solid var(--grid);text-align:left;vertical-align:top}td{overflow-wrap:anywhere}
th{color:var(--ink2);font-weight:600;white-space:nowrap}td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;overflow-wrap:normal}
td.na{color:var(--muted);text-align:right}.note,figcaption,.src,details summary{color:var(--ink2);font-size:12.5px}
.missing{color:var(--ink2);font-style:italic}.src{margin-top:4px}details summary{cursor:pointer}
.chip{display:inline-flex;align-items:center;gap:5px;white-space:nowrap;font-size:12px;padding:1px 8px 1px 6px;border:1px solid var(--border);border-radius:999px;background:var(--page)}
.chip i{font-style:normal;font-weight:700}.chip.good i{color:var(--good)}.chip.bad i{color:var(--bad)}.chip.part i{color:var(--part)}.chip.none i{color:var(--none)}
.verdict{font-size:15px}.kpis{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:12px 0}
.kpi{border:1px solid var(--border);border-radius:8px;padding:8px 10px;background:var(--page)}.kpi .k{font-size:12px;color:var(--ink2)}
.kpi .v{font-size:20px;font-weight:600;margin:2px 0}figure.chart{margin:10px 0 6px}.chart-box{position:relative;height:300px}
.chart-box.offline{height:auto}.chart-box.offline canvas{display:none}
.chart-box.offline::after{content:"차트 라이브러리(cdnjs Chart.js)를 불러오지 못했다. 아래 표가 같은 값을 담는다.";display:block;color:var(--ink2);font-size:12.5px;padding:14px;border:1px dashed var(--axis);border-radius:8px}
.fig{margin:12px 0}.fig img{display:block;max-width:100%;height:auto;border:1px solid var(--border);border-radius:8px;background:#fff}
@media (max-width:600px){section{padding:14px 12px}.chart-box{height:260px}}
</style></head><body>"""

JS = r"""(function () {
  "use strict";
  var specs = JSON.parse(document.getElementById("chart-data").textContent);
  if (!window.Chart) { document.querySelectorAll(".chart-box").forEach(function (b) { b.classList.add("offline"); }); return; }
  var FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif';
  function v(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
  function f(x) { return typeof x === "number" ? x.toFixed(3) : String(x); }
  var refLines = {  // dashed reference lines; y labels sit in the right gutter, pushed down only to avoid overlap
    id: "refLines",
    afterDatasetsDraw: function (chart, args, opts) {
      var ctx = chart.ctx, a = chart.chartArea, lastY = -Infinity;
      (opts.lines || []).slice().sort(function (p, q) { return q.value - p.value; }).forEach(function (l) {
        var px = chart.scales[l.axis].getPixelForValue(l.value);
        ctx.save(); ctx.strokeStyle = v("--muted"); ctx.lineWidth = 1; ctx.setLineDash([4, 3]); ctx.beginPath();
        if (l.axis === "y") { ctx.moveTo(a.left, px); ctx.lineTo(a.right, px); } else { ctx.moveTo(px, a.top); ctx.lineTo(px, a.bottom); }
        ctx.stroke(); ctx.fillStyle = v("--ink2"); ctx.font = "11px " + FONT;
        if (l.axis === "y") { var y = Math.max(px, lastY + 13); lastY = y; ctx.textBaseline = "middle"; ctx.fillText(l.label, a.right + 6, y); }
        else { ctx.textBaseline = "top"; ctx.fillText(l.label, px + 4, a.top + 2); }
        ctx.restore();
      });
    }
  };
  function config(s) {
    var ink2 = v("--ink2"), muted = v("--muted"), bar = s.type === "bar";
    var datasets = s.series.map(function (d) {
      var c = d.slot ? v("--s" + d.slot) : muted;
      return { label: d.name, data: d.data, tip: d.tip !== false, backgroundColor: c, borderColor: c,
        borderWidth: bar ? 0 : 2, borderDash: d.dash ? [4, 3] : [], borderRadius: 4, maxBarThickness: 24, showLine: !bar,
        pointRadius: d.points === false ? 0 : 4, pointHoverRadius: d.points === false ? 0 : 6,
        pointBorderColor: v("--surface"), pointBorderWidth: 2, pointStyle: bar ? "rect" : "circle" };
    });
    function scale(o, isX) {
      return { type: isX && bar ? "category" : "linear", min: o.min, max: o.max,
        title: { display: !!o.title, text: o.title, color: ink2 },
        grid: { color: v("--grid"), lineWidth: 1, drawTicks: false, display: !(isX && bar) },
        border: { color: v("--axis") }, ticks: { color: muted, padding: 6 } };
    }
    var gutter = (s.refs || []).some(function (r) { return r.axis === "y"; }) ? 112 : 8;
    return { type: s.type, data: { labels: s.labels, datasets: datasets }, plugins: [refLines],
      options: { responsive: true, maintainAspectRatio: false, animation: false, layout: { padding: { right: gutter } },
        interaction: bar ? { mode: "index", intersect: false } : { mode: "nearest", intersect: false },
        scales: { x: scale(s.x || {}, true), y: scale(s.y || {}, false) },
        plugins: { legend: { labels: { color: ink2, usePointStyle: true, boxHeight: 8 } },
          tooltip: { filter: function (it) { return it.dataset.tip; }, callbacks: { label: function (c) {
            if (bar) return c.dataset.label + ": " + f(c.parsed.y);
            var r = c.raw, extra = Object.keys(r).filter(function (k) { return k !== "x" && k !== "y"; })
              .map(function (k) { return k + " " + (k === "n" ? r[k] : f(r[k])); }).join(" · ");
            return c.dataset.label + ": " + s.yName + " " + f(r.y) + " · " + s.xName + " " + f(r.x) + (extra ? " · " + extra : "");
          } } },
          refLines: { lines: s.refs || [] } } } };
  }
  var charts = [];
  function draw() {
    charts.forEach(function (c) { c.destroy(); });
    Chart.defaults.font.family = FONT;
    charts = specs.map(function (s) { return new Chart(document.getElementById(s.id), config(s)); });
  }
  draw();
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
})();"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--results", default="results/")
    ap.add_argument("--out", default="results/dashboard/index.html")
    ap.add_argument("--open", action="store_true", help="open the page in the default browser")
    ap.add_argument("--stamp", action="store_true", help="add a generation-time footer line (breaks byte determinism)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    stamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z") if a.stamp else None
    page = Dash(a.results, out).build(stamp)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} ({len(page.encode('utf-8')):,} bytes)")
    if a.open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
