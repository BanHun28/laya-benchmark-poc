"""Build the Korean laya-evals sets of docs/04_korean_evalset_spec.md into data/evals/.

    source env.sh && export HF_HOME=$PWD/data/raw/hf && unset HF_HUB_OFFLINE
    .venv/bin/python scripts/build_ko_evalsets.py all --n 500 --seed 13
    .venv/bin/python scripts/build_ko_evalsets.py massive --lang ko --mode domain --instructions ko
    .venv/bin/python scripts/build_ko_evalsets.py stats data/evals/*.jsonl

Every output starts with one `# build_ko_evalsets {...}` line (source, license, build args, created);
`manifest` rebuilds MANIFEST.json from those lines and the rows without touching the files.
Beyond 04 as first written: `massive --mode domain` folds the 18 MASSIVE scenarios into 8 domains.
"""
import argparse
import hashlib
import json
import os
import random
import statistics
import subprocess
import sys
import urllib.request
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(ROOT / "data/raw/hf"))  # 04 §6 rule 5; read when datasets is imported

import datasets  # noqa: E402
import laya  # noqa: E402
from laya.evals import Dataset, questions_fingerprint  # noqa: E402

BUILDER_VERSION = "0.1.0"
CREATED = "2026-10-02"  # a constant, not today's date: a rebuild must stay byte-identical (04 §6 rule 1)
FIRST_N = 100           # upstream's "first 100 test rows" (research/scripts/bench_local.py:170)
MAX_CHARS = 2000
HEADER = "# build_ko_evalsets "
LAYA_EVALS = Path(sys.executable).parent / "laya-evals"

# HF revisions: HfApi().dataset_info(repo).sha on 2026-10-02, pinned so a rebuild reads the same bytes.
MASSIVE = {"dataset": "mteb/amazon_massive_intent", "split": "test",
           "revision": "940fd47a81eaa7f2cc7b129674d945d618ac38c2"}
KLUE = {"dataset": "klue/klue", "split": "validation", "revision": "349481ec73fff722f88e0453ca05c77a447d967c"}
# main (c657d15) holds only a loading script, which datasets >= 4 refuses to run; the Hub's own parquet
# export of that script (refs/convert/parquet) keeps the features, ClassLabel names included.
KMHAS = {"dataset": "jeanlee/kmhas_korean_hate_speech", "config": "default", "split": "test",
         "revision": "5df3b7429d68f0ffc89dfbd0159cc72f29fad63c", "data_files": "default/test/0000.parquet",
         "script_revision": "c657d15baf277c48d467f0625f7d33c50d4352ef"}
# GitHub raw files (04 §5.4, §5.6): sha256 of the 2026-10-02 download; commit = repo HEAD that day.
NSMC = {"url": "https://raw.githubusercontent.com/e9t/nsmc/master/ratings_test.txt",
        "sha256": "8ac9f64052f11dbf6ae0acb5e038f03d90a76f0eda7820cfb3a92d02edfcebda",
        "commit": "cc0670e872d4ac27bfe36c87456783004b39ef6c", "path": "nsmc/ratings_test.txt"}
I4K = {"url": "https://raw.githubusercontent.com/warnikchow/3i4k/master/data/train_val_test/fci_test.txt",
       "sha256": "d74c5b376c7d231bd4d5a94de855e47b6e70c96abeeaaf75cffbdb8506a87ff2",
       "commit": "cfa90c15f808becafca2d8ef8649b8b71f6bbe71", "path": "3i4k/fci_test.txt"}
# in_training_mix by source dataset when the file header has none. Upstream: "Neither checkpoint trained on
# typed-decisions, MASSIVE or XNLI" (research/scripts/build_benchmark_nb.py:762); sources it does not name stay unknown.
TRAINING_MIX = {MASSIVE["dataset"]: "held out (upstream build_benchmark_nb.py:760-762; base checkpoints. "
                                    "ft-v1 was trained on MASSIVE ko train, see results/P4)"}
LICENSE = {  # 04 §8
    "massive": "CC BY 4.0 (원 저장소 alexa/massive 기준; HF 미러 mteb/amazon_massive_intent·_scenario 카드의 "
               "license 필드는 apache-2.0, 2026-10-02 확인) (확인 필요)",
    "klue": "CC BY-SA 4.0 (확인 필요)",
    "nsmc": "CC0 1.0 (확인 필요)",
    "kmhas": "CC BY-SA 4.0 (확인 필요)",
    "3i4k": "CC BY-SA 4.0 (확인 필요)",
    "handwritten": "프로젝트 소유",
}


def render_key(k):  # upstream's option text for a MASSIVE label (bench_local.py:180)
    return k.replace("_", " ").replace(".", ": ")


# Question specs: (type, question id, (instructions en, instructions ko), {key: (ko description, en description)}).
# Korean descriptions are 04's; English ones and Korean instructions exist only for the ablation flags.
INTENT_INS = ("What is the user asking for in `utterance`?", "`utterance`에서 사용자는 무엇을 요청하나요?")
SCENARIO_KO = {  # 04 §5.1(c)
    "alarm": "알람 설정, 해제, 조회",
    "audio": "음량 조절, 음소거",
    "calendar": "일정 등록, 조회, 삭제",
    "cooking": "요리법, 조리 질문",
    "datetime": "날짜와 시간 질문, 시간대 변환",
    "email": "이메일 확인, 전송, 연락처",
    "general": "잡담, 농담, 일반적인 대화",
    "iot": "조명, 커피머신, 청소기 등 스마트홈 기기 제어",
    "lists": "목록 만들기, 항목 추가, 삭제, 조회",
    "music": "음악 취향, 재생 설정",
    "news": "뉴스 조회",
    "play": "음악, 라디오, 팟캐스트, 오디오북, 게임 재생",
    "qa": "사실, 정의, 수학, 환율, 주식 질문",
    "recommendation": "장소, 이벤트, 영화 추천",
    "social": "소셜 미디어 게시, 조회",
    "takeaway": "음식 주문, 배달 조회",
    "transport": "교통, 택시, 티켓, 길 안내",
    "weather": "날씨 질문",
}
# en descriptions = upstream's key rendering, the variant P0c measured against the Korean table
SCENARIO_Q = ("choice", "scenario", ("Which domain does `utterance` belong to?", "`utterance`는 어느 도메인에 속하나요?"),
              {k: (v, render_key(k)) for k, v in SCENARIO_KO.items()})
DOMAINS = {  # key: (MASSIVE scenarios, ko description, en description), in criteria order
    "productivity": (("alarm", "calendar", "datetime", "lists"), "알람, 일정, 날짜와 시간, 할 일과 쇼핑 목록",
                     "alarms, calendar, date and time, to-do and shopping lists"),
    "media": (("music", "play", "audio"), "음악, 라디오, 팟캐스트, 오디오북 재생과 음량 조절",
              "playing music, radio, podcasts and audiobooks, and volume control"),
    "smart_home": (("iot",), "조명, 커피머신, 청소기, 플러그 등 스마트홈 기기 제어",
                   "controlling smart home devices such as lights, coffee machines, vacuum cleaners and plugs"),
    "info_qa": (("qa", "weather", "news"), "사실, 정의, 계산, 환율, 날씨, 뉴스 등 정보 질문",
                "questions for information such as facts, definitions, calculations, exchange rates, weather and news"),
    "communication": (("email", "social"), "이메일, 연락처, 소셜 미디어 게시와 확인",
                      "email, contacts, and posting to or checking social media"),
    "lifestyle": (("takeaway", "cooking", "recommendation"), "음식 주문과 배달, 요리법, 장소·이벤트·영화 추천",
                  "food ordering and delivery, recipes, and recommendations for places, events and movies"),
    "transport": (("transport",), "교통, 택시, 티켓, 길 안내", "transport, taxis, tickets and directions"),
    "general": (("general",), "인사, 잡담, 농담, 위 어디에도 속하지 않는 일반 대화",
                "greetings, small talk, jokes, and general conversation that fits none of the above"),
}
DOMAIN_Q = ("choice", "domain", ("Which domain should handle the request in `utterance`?",
                                 "`utterance`의 요청은 어느 도메인이 처리해야 하나요?"),
            {k: (ko, en) for k, (_, ko, en) in DOMAINS.items()})
YNAT_NAMES = ["IT과학", "경제", "사회", "생활문화", "세계", "스포츠", "정치"]
YNAT_Q = ("choice", "topic", ("Which news section does `headline` belong to?", "`headline`은 어느 뉴스 섹션에 속하나요?"), {
    "it_science": ("IT, 과학, 기술, 통신, 인터넷", "IT, science, technology, telecommunications, internet"),
    "economy": ("경제, 금융, 산업, 기업, 부동산", "economy, finance, industry, companies, real estate"),
    "society": ("사회, 사건사고, 교육, 노동, 복지", "society, incidents and accidents, education, labor, welfare"),
    "culture_life": ("생활, 문화, 예술, 건강, 여행, 음식", "lifestyle, culture, arts, health, travel, food"),
    "world": ("국제, 해외 뉴스, 외교", "international, foreign news, diplomacy"),
    "sports": ("스포츠, 경기, 선수", "sports, matches, athletes"),
    "politics": ("정치, 국회, 정당, 선거, 정부", "politics, National Assembly, political parties, elections, government"),
})
NLI_Q = ("choice", "relation", ("Given `premise`, how does `hypothesis` relate to it?",
                                "`premise`가 주어졌을 때 `hypothesis`는 그것과 어떤 관계인가요?"), {
    "entailment": ("전제가 참이면 가설도 반드시 참이다", "if the premise is true, the hypothesis must also be true"),
    "neutral": ("전제만으로는 가설의 참 거짓을 알 수 없다", "the premise alone does not tell whether the hypothesis is true or false"),
    "contradiction": ("전제가 참이면 가설은 거짓이다", "if the premise is true, the hypothesis is false"),
})
SENTIMENT = {"positive": ("영화를 긍정적으로 평가한다", "rates the movie positively"),
             "negative": ("영화를 부정적으로 평가한다", "rates the movie negatively")}
NSMC_NOUL_Q = ("noul", "sentiment_noul", ("Is the movie review in `document` positive?", "`document`의 영화 리뷰는 긍정적인가요?"),
               {"true": SENTIMENT["positive"], "false": SENTIMENT["negative"]})
NSMC_CHOICE_Q = ("choice", "sentiment_choice", ("What is the sentiment of the movie review in `document`?",
                                                "`document`의 영화 리뷰는 어떤 감성인가요?"), SENTIMENT)
KMHAS_NAMES = ["origin", "physical", "politics", "profanity", "age", "gender", "race", "religion", "not_hate_speech"]
HATE_Q = ("noul", "is_hate", ("Does `comment` contain hate speech or abusive language toward a person or group?",
                              "`comment`에 사람이나 집단을 향한 혐오 표현이나 욕설이 있나요?"), {
    "true": ("출신, 외모, 정치 성향, 욕설, 연령, 성별, 인종, 종교를 근거로 비하하거나 공격한다",
             "demeans or attacks someone based on origin, appearance, political leaning, profanity, age, gender, "
             "race or religion"),
    "false": ("비하나 공격이 없는 일반적인 댓글이다", "an ordinary comment with no demeaning or attacking language"),
})
HATE_TYPE_Q = ("choice", "hate_type", ("Which kind of hate speech does `comment` express?",
                                       "`comment`는 어떤 종류의 혐오 표현인가요?"), {
    "origin": ("출신 지역이나 국가를 근거로 비하", "demeaning based on regional or national origin"),
    "physical": ("외모, 신체를 근거로 비하", "demeaning based on appearance or body"),
    "politics": ("정치 성향, 정치인을 근거로 비하", "demeaning based on political leaning or politicians"),
    "profanity": ("대상 없는 욕설, 저속한 표현", "untargeted swearing or vulgar language"),
    "age": ("나이, 세대를 근거로 비하", "demeaning based on age or generation"),
    "gender": ("성별을 근거로 비하", "demeaning based on gender"),
    "race": ("인종, 민족을 근거로 비하", "demeaning based on race or ethnicity"),
    "religion": ("종교를 근거로 비하", "demeaning based on religion"),
})
I4K_Q = ("choice", "speech_act", ("What kind of speech act is `utterance`?", "`utterance`는 어떤 화행인가요?"), {
    "fragment": ("문장이 아닌 단어나 구 조각", "a word or phrase fragment, not a sentence"),
    "statement": ("사실이나 의견을 전달하는 서술", "a statement that conveys a fact or opinion"),
    "question": ("정보를 요구하는 질문", "a question asking for information"),
    "command": ("행동을 요구하는 명령이나 요청", "a command or request asking for an action"),
    "rhetorical_question": ("대답을 기대하지 않는 수사적 질문", "a rhetorical question that expects no answer"),
    "rhetorical_command": ("실제 행동을 요구하지 않는 수사적 명령", "a rhetorical command that asks for no actual action"),
    "intonation_dependent": ("억양에 따라 의미가 달라지는 발화", "an utterance whose meaning depends on intonation"),
})


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def rel(path):
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def variant(args, default_desc="ko"):
    """Description language and the filename suffix the ablation flags give (04 §6)."""
    desc = args.descriptions or default_desc
    return desc, ("_ko-instr" if args.instructions == "ko" else "") + ("" if desc == default_desc else "_%s-desc" % desc)


def question(spec, args, desc):
    qtype, _, ins, crit = spec
    return {"type": qtype, "instructions": ins[args.instructions == "ko"],
            "criteria": {k: v[desc == "en"] for k, v in crit.items()}}


def row(state, questions, expected, tags, lang="ko"):
    return {"state": state, "questions": questions, "expected": expected, "tags": tags, "language": lang}


def build_args(args, command, desc, **extra):
    return {"command": command, "n": args.n, "seed": args.seed, "instructions": args.instructions,
            "descriptions": desc, **extra}


def count_duplicates(rows):
    return len(rows) - len({json.dumps(r["state"], ensure_ascii=False, sort_keys=True) for r in rows})


def pool_of(items, min_chars=2):
    """04 §5 candidates in id order: every state field min_chars..2000 chars, exact-duplicate states dropped (first kept)."""
    seen, pool, dropped = set(), [], Counter()
    for it in sorted(items, key=lambda it: it["id"]):
        key = json.dumps(it["state"], ensure_ascii=False, sort_keys=True)
        if not all(min_chars <= len(v) <= MAX_CHARS for v in it["state"].values()):
            dropped["length"] += 1
        elif key in seen:
            dropped["duplicate"] += 1
        else:
            seen.add(key)
            pool.append(it)
    return pool, {"source_rows": len(items), "pool_rows": len(pool), "dropped": dict(sorted(dropped.items()))}


def stratify(pool, labels, n, seed):
    """04 §5: quota ceil(n/k) per label (the first n mod k labels take the extra row), a short label gives
    what it has and one random.Random(seed) tops up from the rest. Rows come back in id order."""
    if n == 0:
        return pool, {"all": len(pool)}
    rng = random.Random(seed)
    base, extra = divmod(n, len(labels))
    picked, per_label = [], {}
    for i, label in enumerate(labels):
        group = [it for it in pool if it["label"] == label]
        take = rng.sample(group, min(base + (i < extra), len(group)))
        picked += take
        per_label[label] = len(take)
    taken = {it["id"] for it in picked}
    rest = [it for it in pool if it["id"] not in taken]
    top_up = rng.sample(rest, min(n - len(picked), len(rest)))
    return sorted(picked + top_up, key=lambda it: it["id"]), {"per_label": per_label, "top_up": len(top_up)}


def write_set(args, name, rows, meta, exempt_dups=False):
    """Write header + rows, run `laya-evals validate`, and never replace different bytes without --force."""
    for r in rows:
        for qid, exp in r["expected"].items():
            q = r["questions"][qid]
            assert (exp in q["criteria"]) if q["type"] == "choice" else isinstance(exp, bool), (name, qid, exp)
    dups = count_duplicates(rows)
    assert exempt_dups or dups == 0, (name, dups)  # 04 §7: only the upstream-faithful MASSIVE sets keep duplicates
    header = HEADER + json.dumps({"builder": "scripts/build_ko_evalsets.py " + BUILDER_VERSION, "created": CREATED,
                                  **meta}, ensure_ascii=False)
    data = ("\n".join([header] + [json.dumps(r, ensure_ascii=False) for r in rows]) + "\n").encode("utf-8")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    path, tmp = out / (name + ".jsonl"), out / (name + ".jsonl.tmp")
    # validate before replacing, so a broken build never lands on (and then blocks) the real file
    tmp.write_bytes(data)
    check = subprocess.run([str(LAYA_EVALS), "validate", str(tmp)], capture_output=True, text=True)
    old, new = (sha256(path.read_bytes()) if path.exists() else None), sha256(data)
    if check.returncode:
        tmp.unlink()
        sys.exit("%s: laya-evals validate failed\n%s%s" % (name, check.stdout, check.stderr))
    if old not in (None, new) and not args.force:
        tmp.unlink()
        sys.exit("%s exists with sha256 %s but this build gives %s; a frozen file changes only with --force"
                 % (rel(path), old, new))
    os.replace(tmp, path)
    print("%-44s n=%-4d dup=%d sha256=%s questions_sha256=%s %-9s | %s" % (
        path.name, len(rows), dups, new[:12], questions_fingerprint(Dataset.from_jsonl(str(path)))[:12],
        "unchanged" if old == new else "replaced" if old else "written", check.stdout.strip()))


def read_rows(path):
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    return [json.loads(line) for line in lines if line.strip() and not line.startswith("#")]


def read_header(path):
    with open(path, encoding="utf-8") as f:
        first = f.readline()
    return json.loads(first[len(HEADER):]) if first.startswith(HEADER) else {}


def hf_source(src, config):
    return {"dataset": src["dataset"], "config": config, "split": src["split"], "revision": src["revision"]}


def fetch_tsv(args, src):
    """Rows of a GitHub raw TSV under --raw (downloaded once, always checked against the pinned sha256) and its source record."""
    path = Path(args.raw) / src["path"]
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(urllib.request.urlopen(src["url"], timeout=60).read())
    got = sha256(path.read_bytes())
    if got != src["sha256"]:
        sys.exit("%s: sha256 %s, pinned %s; upstream changed and the sets built from it would too"
                 % (rel(path), got, src["sha256"]))
    source = {"url": src["url"], "sha256": got, "commit": src["commit"], "path": rel(path)}
    # read_text's universal newlines turn 3i4K's CRLF into "\n"; no source holds a bare "\r" or U+2028
    return [line.split("\t") for line in path.read_text(encoding="utf-8").split("\n") if line], source


def sampled_set(args, name, command, spec, items, labels, meta, min_chars=2):
    """Filter, deduplicate, stratify and write a one-question set; returns what a derived file needs."""
    pool, info = pool_of(items, min_chars)
    picked, info["sample"] = stratify(pool, labels, args.n, args.seed)
    desc, suffix = variant(args)
    q = question(spec, args, desc)
    rows = [row(it["state"], {spec[1]: q}, {spec[1]: it["label"]}, it["tags"]) for it in picked]
    meta = {**meta, "build_args": build_args(args, command, desc), "pool": info}
    write_set(args, name + suffix, rows, meta)
    return rows, meta, suffix


@lru_cache(maxsize=None)
def load_massive(lang):
    return datasets.load_dataset(MASSIVE["dataset"], lang, split=MASSIVE["split"], revision=MASSIVE["revision"])


def scenario_of(label_text):
    return label_text.split("_", 1)[0]


def intent_descriptions(labels):
    path = ROOT / "data/handwritten/massive_intent_ko_desc.json"
    if not path.exists():
        sys.exit("--descriptions ko for the MASSIVE intent sets needs %s (04 §5.1(a))" % rel(path))
    desc = json.loads(path.read_text(encoding="utf-8"))
    assert set(desc) == set(labels), sorted(set(desc) ^ set(labels))
    return desc


def massive(args):
    if args.lang == "en" and args.mode not in ("20opt", "domain"):
        sys.exit("massive --lang en builds only the en twins of --mode 20opt and --mode domain")
    d = load_massive(args.lang)
    meta = {"source": hf_source(MASSIVE, args.lang), "license": LICENSE["massive"]}
    if args.mode == "domain":
        return massive_domain(args, meta)
    first = d.select(range(FIRST_N))  # upstream rule: first 100 test rows, no shuffle, duplicates kept
    meta["pool"] = {"selection": "first %d %s test rows in file order" % (FIRST_N, args.lang)}
    if args.mode == "scenario":
        assert sorted({scenario_of(t) for t in d["label_text"]}) == list(SCENARIO_KO)  # the 18 prefixes of 04 §5.1(c)
        desc, suffix = variant(args)
        q = question(SCENARIO_Q, args, desc)
        rows = [row({"utterance": r["text"]}, {"scenario": q}, {"scenario": scenario_of(r["label_text"])},
                    ["massive", "scenario18"]) for r in first]
        name = "ko_massive_scenario_18"
    else:
        labels = sorted(set(d["label_text"]))  # computed: the test splits hold 59 (cooking_query is train-only)
        desc, suffix = variant(args, default_desc="en")
        text = intent_descriptions(labels) if desc == "ko" else {k: render_key(k) for k in labels}
        ins = INTENT_INS[args.instructions == "ko"]
        if args.mode == "20opt":  # port of research/scripts/bench_local.py:165-183
            rng = random.Random(args.seed)  # once per language, as upstream
            rows = []
            for r in first:
                keys = [r["label_text"]] + rng.sample([k for k in labels if k != r["label_text"]], 19)
                rng.shuffle(keys)
                q = {"type": "choice", "instructions": ins, "criteria": {k: text[k] for k in keys}}
                rows.append(row({"utterance": r["text"]}, {"intent": q}, {"intent": r["label_text"]},
                                ["massive", "20opt", "scenario:" + scenario_of(r["label_text"])], args.lang))
        else:  # one question over the whole sorted label set; the name's 60 is nominal
            q = {"type": "choice", "instructions": ins, "criteria": {k: text[k] for k in labels}}
            rows = [row({"utterance": r["text"]}, {"intent": q}, {"intent": r["label_text"]},
                        ["massive", "high_cardinality"]) for r in first]
        name = "%s_massive_intent_%s" % (args.lang, "20opt" if args.mode == "20opt" else "full60")
    meta["build_args"] = build_args(args, "massive", desc, lang=args.lang, mode=args.mode, n=FIRST_N)
    write_set(args, name + suffix, rows, meta, exempt_dups=True)


def massive_domain(args, meta):
    """8 routing domains over the whole ko test split; the en file is the same ids' en twins."""
    ko = load_massive("ko")
    to_domain = {s: k for k, (scenarios, _, _) in DOMAINS.items() for s in scenarios}
    assert sum(len(v[0]) for v in DOMAINS.values()) == len(to_domain) == 18  # no scenario in two domains
    assert set(to_domain) == {scenario_of(t) for t in ko["label_text"]}     # and every scenario has one
    items = [{"id": int(r["id"]), "state": {"utterance": r["text"]}, "label_text": r["label_text"],
              "label": to_domain[scenario_of(r["label_text"])]} for r in ko]
    pool, info = pool_of(items)
    picked, info["sample"] = stratify(pool, list(DOMAINS), args.n, args.seed)
    desc, suffix = variant(args)
    q = question(DOMAIN_Q, args, desc)
    by_id = {int(r["id"]): r for r in load_massive(args.lang)}
    rows = []
    for it in picked:
        r = by_id[it["id"]]
        assert r["label_text"] == it["label_text"], (it["id"], it["label_text"], r["label_text"])
        rows.append(row({"utterance": r["text"]}, {"domain": q}, {"domain": it["label"]},
                        ["massive", "domain8", "scenario:" + scenario_of(r["label_text"])], args.lang))
    if args.lang == "en":
        info["selection"] = "en rows with the ids of ko_massive_domain_8%s.jsonl, same order" % suffix
    meta.update(build_args=build_args(args, "massive", desc, lang=args.lang, mode="domain"), pool=info)
    # the en twin follows the ko ids, so en-side duplicates are recorded rather than removed
    write_set(args, "%s_massive_domain_8%s" % (args.lang, suffix), rows, meta, exempt_dups=args.lang == "en")


def ynat(args):
    d = datasets.load_dataset(KLUE["dataset"], "ynat", split=KLUE["split"], revision=KLUE["revision"])
    assert d.features["label"].names == YNAT_NAMES, d.features["label"].names
    keys = list(YNAT_Q[3])
    items = [{"id": r["guid"], "state": {"headline": r["title"]}, "label": keys[r["label"]], "tags": ["klue", "ynat"]}
             for r in d]
    sampled_set(args, "ko_klue_ynat_7", "ynat", YNAT_Q, items, keys,
                {"source": hf_source(KLUE, "ynat"), "license": LICENSE["klue"]})


def nli(args):
    d = datasets.load_dataset(KLUE["dataset"], "nli", split=KLUE["split"], revision=KLUE["revision"])
    keys = list(NLI_Q[3])
    assert d.features["label"].names == keys, d.features["label"].names
    items = [{"id": r["guid"], "state": {"premise": r["premise"], "hypothesis": r["hypothesis"]},
              "label": keys[r["label"]], "tags": ["klue", "nli", "source:" + r["source"]]} for r in d]
    sampled_set(args, "ko_klue_nli_3", "nli", NLI_Q, items, keys,
                {"source": hf_source(KLUE, "nli"), "license": LICENSE["klue"]})


def nsmc(args):
    lines, source = fetch_tsv(args, NSMC)
    assert lines[0] == ["id", "document", "label"] and all(len(line) == 3 for line in lines), "unexpected NSMC layout"
    items = [{"id": int(i), "state": {"document": doc}, "label": label == "1"} for i, doc, label in lines[1:]]
    pool, info = pool_of(items)
    picked, info["sample"] = stratify(pool, [True, False], args.n, args.seed)
    desc, suffix = variant(args)
    noul, choice = question(NSMC_NOUL_Q, args, desc), question(NSMC_CHOICE_Q, args, desc)
    keys = {True: "positive", False: "negative"}
    if args.opaque_labels:
        noul["labels"] = {"true": "A", "false": "B"}
        suffix += "_opaque-labels"
    if args.opaque_keys:
        keys = {True: "A", False: "B"}
        choice["criteria"] = dict(zip("AB", choice["criteria"].values()))
        suffix += "_opaque-keys"
    rows = [row(it["state"], {"sentiment_noul": noul, "sentiment_choice": choice},
                {"sentiment_noul": it["label"], "sentiment_choice": keys[it["label"]]}, ["nsmc"]) for it in picked]
    name = "ko_nsmc_sentiment" + suffix
    meta = {"source": source, "license": LICENSE["nsmc"],
            "build_args": build_args(args, "nsmc", desc, opaque_keys=args.opaque_keys, opaque_labels=args.opaque_labels),
            "pool": info}
    write_set(args, name, rows, meta)
    if args.split_variants:  # one question per file, so each primitive gets its own questions_sha256
        for qid in ("sentiment_noul", "sentiment_choice"):
            part = [row(r["state"], {qid: r["questions"][qid]}, {qid: r["expected"][qid]}, r["tags"]) for r in rows]
            write_set(args, "ko_nsmc_%s%s" % (qid, suffix), part, {**meta, "derived_from": name + ".jsonl"})


def kmhas(args):
    d = datasets.load_dataset(KMHAS["dataset"], revision=KMHAS["revision"], split=KMHAS["split"],
                              data_files={KMHAS["split"]: KMHAS["data_files"]})
    assert d.features["label"].feature.names == KMHAS_NAMES, d.features["label"]
    meta = {"source": KMHAS, "license": LICENSE["kmhas"]}
    hate = [{"id": i, "state": {"comment": r["text"]}, "label": 8 not in r["label"],
             "tags": ["kmhas", "clean" if 8 in r["label"] else "hate"] + (["multi_label"] if len(r["label"]) > 1 else [])}
            for i, r in enumerate(d)]
    sampled_set(args, "ko_kmhas_hate", "kmhas", HATE_Q, hate, [True, False], meta)
    types = list(HATE_TYPE_Q[3])
    # single-label hate rows only: a multi-label row has two right answers
    typed = [{"id": i, "state": {"comment": r["text"]}, "label": types[r["label"][0]], "tags": ["kmhas", "hate_type"]}
             for i, r in enumerate(d) if len(r["label"]) == 1 and r["label"][0] < 8]
    sampled_set(args, "ko_kmhas_type_8", "kmhas", HATE_TYPE_Q, typed, types, meta)


def i4k(args):
    lines, source = fetch_tsv(args, I4K)
    assert all(len(line) == 2 for line in lines), "unexpected 3i4K layout"
    keys = list(I4K_Q[3])
    items = [{"id": i, "state": {"utterance": text}, "label": keys[int(label)],
              "tags": ["3i4k"] + (["fragment"] if label == "0" else [])} for i, (label, text) in enumerate(lines)]
    # no 2-character floor: one-syllable fragments are regular 3i4K data (04 §5.6)
    rows, meta, suffix = sampled_set(args, "ko_3i4k_speechact_7", "i4k", I4K_Q, items, keys,
                                     {"source": source, "license": LICENSE["3i4k"]}, min_chars=0)
    if args.drop_fragments:  # the 7-way rows minus fragments, with the fragment option removed
        q = dict(rows[0]["questions"]["speech_act"])
        q["criteria"] = {k: v for k, v in q["criteria"].items() if k != "fragment"}
        rows6 = [row(r["state"], {"speech_act": q}, r["expected"], r["tags"])
                 for r in rows if r["expected"]["speech_act"] != "fragment"]
        write_set(args, "ko_3i4k_speechact_6" + suffix, rows6,
                  {**meta, "derived_from": "ko_3i4k_speechact_7%s.jsonl" % suffix})


def negation(args):
    src = ROOT / "data/handwritten/negation_pairs.jsonl"
    if not src.exists():
        print("negation: %s 없음, 건너뜀 (수작업 원본이 생기면 다시 실행)" % rel(src))
        return
    meta = {"source": {"path": rel(src), "sha256": sha256(src.read_bytes())}, "license": LICENSE["handwritten"],
            "in_training_mix": "no", "build_args": {"command": "negation"}}
    write_set(args, "ko_negation_probe", read_rows(src), meta)


def poc(args):
    print("poc: 보류, 건너뜀 (ko_poc_triage_v1은 레이블 정책과 수작업 레이블이 준비된 뒤 구현, 04 §5.8)")


def manifest(args):
    out, files = Path(args.out), {}
    for path in sorted(out.glob("*.jsonl")):
        meta, rows = read_header(path), read_rows(path)
        dist = {}
        for r in rows:
            for qid, exp in r["expected"].items():
                dist.setdefault(qid, Counter())[exp if isinstance(exp, str) else json.dumps(exp)] += 1
        dist = {qid: dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))) for qid, c in dist.items()}
        majority = {qid: round(max(c.values()) / sum(c.values()), 4) for qid, c in dist.items()}
        one = len(dist) == 1  # one question: flat, as in 04 §6; NSMC's two questions: keyed by question id
        files[path.name] = {
            "path": rel(path), "sha256": sha256(path.read_bytes()),
            "questions_sha256": questions_fingerprint(Dataset.from_jsonl(str(path))), "n": len(rows),
            "source": meta.get("source"), "license": meta.get("license"),
            "in_training_mix": meta.get("in_training_mix") or TRAINING_MIX.get((meta.get("source") or {}).get("dataset"),
                                                                                "unknown"),
            "build_args": meta.get("build_args"),
            "label_distribution": next(iter(dist.values())) if one else dist,
            "majority_rate": next(iter(majority.values())) if one else majority,
            "duplicates": count_duplicates(rows), "derived_from": meta.get("derived_from"),
            "label_policy_sha256": meta.get("label_policy_sha256"),
        }
    doc = {"version": 1, "builder_version": BUILDER_VERSION, "laya_version": laya.__version__,
           "created_at": datetime.now().astimezone().isoformat(timespec="seconds"), "files": files}
    (out / "MANIFEST.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("MANIFEST.json: %d files" % len(files))


def stats(args):
    """04 §7: state token lengths and per-question head/room, as laya's own sequence builder counts them."""
    from transformers import AutoTokenizer
    from laya.agent import Agent
    from laya.common import build_head, encode_text, serialize_state
    loaded = {}
    for f in args.files:
        path = Path(f)
        rows = read_rows(path)
        for ckpt in ("laya-multilingual", "laya") if path.name.startswith("en_") else ("laya-multilingual",):
            if ckpt not in loaded:
                cfg = json.loads((ROOT / "models" / ckpt / "rl_agent_config.json").read_text())
                tok = AutoTokenizer.from_pretrained(str(ROOT / "models" / ckpt / "tokenizer"))
                loaded[ckpt] = (tok, cfg["max_len"], cfg["head_max_len"])
            tok, max_len, head_max_len = loaded[ckpt]
            heads, per_q, lens, over = {}, {}, [], 0
            for r in rows:
                state = serialize_state(r["state"]).replace(tok.mask_token, " ")
                lens.append(len(encode_text(tok, state, add_special_tokens=False)["input_ids"]))
                room = max_len
                for qid, q in r["questions"].items():
                    key = json.dumps([qid, q], ensure_ascii=False)
                    if key not in heads:
                        ids, _, info = build_head(tok, Agent._to_internal(q), head_max_len)
                        heads[key] = (len(ids), info)
                    per_q.setdefault(qid, []).append(heads[key])
                    room = min(room, max_len - heads[key][0] - 1)  # -1: the [SEP] closing the state
                over += lens[-1] > room
            p = statistics.quantiles(lens, n=100, method="inclusive")
            room = min(max_len - h - 1 for hs in per_q.values() for h, _ in hs)
            notes = []
            for qid, hs in per_q.items():
                lo, hi = min(h for h, _ in hs), max(h for h, _ in hs)
                note = "%s head=%s" % (qid, lo if lo == hi else "%d-%d" % (lo, hi))
                capped = [info for _, info in hs if info["tokens_per_option"]]
                if capped:
                    note += " cap=%d tok/opt distinct=%d/%d" % (capped[0]["tokens_per_option"],
                                                              min(i["options_distinct"] for i in capped), capped[0]["options"])
                notes.append(note)
            print("%-44s %-17s n=%-4d state p50/p95/p99/max=%.0f/%.0f/%.0f/%d room=%d p99<room=%s over_room=%d | %s" % (
                path.name, ckpt, len(rows), p[49], p[94], p[98], max(lens), room, p[98] < room, over, "; ".join(notes)))


def build_all(args):
    for lang, mode in (("ko", "20opt"), ("en", "20opt"), ("ko", "full"), ("ko", "scenario"), ("ko", "domain"),
                       ("en", "domain")):
        massive(argparse.Namespace(**{**vars(args), "lang": lang, "mode": mode}))
    ynat(args)
    nli(args)
    nsmc(argparse.Namespace(**{**vars(args), "split_variants": True}))
    for build in (kmhas, i4k, negation, poc, manifest):
        build(args)


COMMANDS = {"all": build_all, "massive": massive, "ynat": ynat, "nli": nli, "nsmc": nsmc, "kmhas": kmhas, "i4k": i4k,
            "negation": negation, "poc": poc, "manifest": manifest, "stats": stats}


def main():
    p = argparse.ArgumentParser(description="Build the Korean laya-evals sets (docs/04_korean_evalset_spec.md).")
    p.add_argument("command", choices=list(COMMANDS))
    p.add_argument("files", nargs="*", help="stats: eval files to measure")
    p.add_argument("--n", type=int, default=500, help="rows per sampled set, 0 = all (MASSIVE 20opt/full/scenario: always 100)")
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--instructions", choices=("en", "ko"), default="en")
    p.add_argument("--descriptions", choices=("ko", "en"), help="default ko; en for the MASSIVE intent sets")
    p.add_argument("--out", default=str(ROOT / "data/evals"))
    p.add_argument("--raw", default=str(ROOT / "data/raw"), help="GitHub raw downloads (HF caches follow HF_HOME)")
    p.add_argument("--force", action="store_true", help="replace an existing output whose bytes differ")
    p.add_argument("--lang", choices=("ko", "en"), default="ko", help="massive")
    p.add_argument("--mode", choices=("20opt", "full", "scenario", "domain"), default="20opt", help="massive")
    p.add_argument("--split-variants", action="store_true", help="nsmc: also one file per question")
    p.add_argument("--opaque-keys", action="store_true", help="nsmc: choice keys A/B")
    p.add_argument("--opaque-labels", action="store_true", help="nsmc: noul labels A/B")
    p.add_argument("--drop-fragments", action="store_true", help="i4k: also the 6-way set without fragment rows")
    args = p.parse_args()
    if args.files and args.command != "stats":
        p.error("file arguments belong to stats")
    datasets.disable_progress_bars()
    COMMANDS[args.command](args)


if __name__ == "__main__":
    main()
