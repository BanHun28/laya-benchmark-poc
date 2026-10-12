# scripts/env_report.py  --  .venv/bin/python scripts/env_report.py [data/evals/*.jsonl ...]
import hashlib, json, os, platform, sys, time
os.environ.setdefault("USE_TF", "0")
import torch, transformers, laya
from laya.revisions import snapshot_revision
try:
    import onnxruntime; ort = onnxruntime.__version__
except ImportError:
    ort = None

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

rec = {
    "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "platform": platform.platform(), "machine": platform.machine(),
    "python": sys.version.split()[0],
    "versions": {"laya": laya.__version__, "torch": torch.__version__,
                 "transformers": transformers.__version__, "onnxruntime": ort},
    "mps_available": torch.backends.mps.is_available(),
    "torch_threads": torch.get_num_threads(), "torch_interop_threads": torch.get_num_interop_threads(),
    "env": {k: os.environ.get(k) for k in ("LAYA_MODELS_DIR", "LAYA_MODELS", "LAYA_REVISION", "OMP_NUM_THREADS",
            "HF_HUB_OFFLINE", "LAYA_MPS_AMP_MIN_ROWS", "LAYA_CPU_AMP", "LAYA_DEFAULT_MODEL")},
    # snapshot_revision 은 realpath 가 snapshots/<sha> 로 끝날 때만 sha 를 돌려준다. models/laya 만 그 모양이고
    # 두 하위 폴더는 snapshots/<sha>/multilingual 꼴이라 부모 디렉토리로 다시 묻는다. 셋은 같은 번들 sha 를 공유한다.
    "checkpoints": {n: {"realpath": os.path.realpath(f"models/{n}"),
                        "snapshot_sha": snapshot_revision(os.path.realpath(f"models/{n}"))
                                        or snapshot_revision(os.path.dirname(os.path.realpath(f"models/{n}"))),
                        "weights_sha256": sha256(f"models/{n}/model.safetensors")}
                    for n in ("laya", "laya-multilingual", "laya-typed-decisions")},
    "datasets": {p: sha256(p) for p in sys.argv[1:]},
}
out = f"results/env/env_{time.strftime('%Y%m%d-%H%M')}.json"
json.dump(rec, open(out, "w"), indent=2, ensure_ascii=False)
print(out)
