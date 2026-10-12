"""D7b: run `laya-evals` with ONNX Runtime pinned to intra-op 10 / inter-op 1 (ONNXAgent leaves ORT at its
default, which uses every core incl. E-cores). Usage: python results/D/ort_threads_prelude.py run <laya-evals args>"""
import sys

import onnxruntime as ort

_SessionOptions = ort.SessionOptions


def pinned():
    so = _SessionOptions()
    so.intra_op_num_threads, so.inter_op_num_threads = 10, 1
    return so


ort.SessionOptions = pinned  # laya/onnx_agent.py builds its session with `ort.SessionOptions()`
from laya.evals_cli import main  # noqa: E402

sys.exit(main(sys.argv[1:]))
