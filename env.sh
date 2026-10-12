# 프로젝트 루트에서:  source env.sh
export PROJECT_ROOT="$PWD"
export USE_TF=0                               # transformers 의 TF 탐지로 인한 abseil deadlock 회피 (research/README.md)
export USE_TORCH=1
export TOKENIZERS_PARALLELISM=false
export LAYA_MODELS_DIR="$PROJECT_ROOT/models" # research 스크립트용 체크포인트 루트. LAYA_MODELS 자체는 export하지 않는다: laya-serve가 같은 이름을 체크포인트 이름 목록으로 읽기 때문(laya/serve.py:667-668). research 스크립트는 LAYA_MODELS="$LAYA_MODELS_DIR" 를 인라인으로 준다(§2.9)
export LAYA_REVISION=reviewed                 # Hub 로드를 PINNED_REVISIONS 로 pin (laya/revisions.py). 로컬 경로 로드에는 영향 없음
export OMP_NUM_THREADS=10                     # 성능 코어 수
# export HF_HUB_OFFLINE=1                     # 체크포인트·데이터셋 다운로드가 모두 끝난 뒤에만. 데이터셋 받을 때는 unset
# export LAYA_MPS_AMP_MIN_ROWS=100000         # parity 점검용: MPS 를 fp32 로 강제 (기본 5 = 5행 이상 fp16 autocast)
# export LAYA_CPU_AMP=bf16                    # 선택: CPU bf16. 기본 fp32 가 레퍼런스
# export LAYA_DEFAULT_MODEL=multilingual      # 언어 증거 없는 라틴 문자 텍스트의 라우팅 fallback. 순수 한글은 항상 감지되지만 라틴 문자가 다수인 혼합문과 영어 래퍼 속 짧은 한국어는 english로 갈 수 있다(docs/07 §4). PoC는 lang='ko'를 명시한다
