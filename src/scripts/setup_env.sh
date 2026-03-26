#!/bin/bash
# ============================================================
# Affordance Labeller - 환경 설정 스크립트
# 실행: bash scripts/setup_env.sh
# ============================================================

set -e

ENV_NAME="affordance_labeller"
PYTHON_VERSION="3.10"

echo "=========================================="
echo " Affordance Labeller 환경 설정 시작"
echo "=========================================="

# 1. Conda 환경 생성 (conda가 있는 경우)
if command -v conda &> /dev/null; then
    echo "[1/4] Conda 환경 생성: $ENV_NAME (Python $PYTHON_VERSION)"
    conda create -n $ENV_NAME python=$PYTHON_VERSION -y
    echo ""
    echo "  활성화 명령: conda activate $ENV_NAME"
    echo ""

    # conda 환경 활성화
    eval "$(conda shell.bash hook)"
    conda activate $ENV_NAME
else
    echo "[1/4] Conda 없음 → venv 사용"
    python3 -m venv .venv
    source .venv/bin/activate
    echo "  활성화 명령: source .venv/bin/activate"
fi

# 2. pip 업그레이드
echo "[2/4] pip 업그레이드"
pip install --upgrade pip

# 3. 핵심 패키지 설치
echo "[3/4] 핵심 패키지 설치"
pip install -r requirements.txt

# 4. 설치 확인
echo "[4/4] 설치 확인"
echo "---"
python -c "import viser; print(f'  viser: {viser.__version__}')"
python -c "import open3d as o3d; print(f'  open3d: {o3d.__version__}')"
python -c "import trimesh; print(f'  trimesh: {trimesh.__version__}')"
python -c "import numpy; print(f'  numpy: {numpy.__version__}')"
echo "---"

echo ""
echo "=========================================="
echo " 환경 설정 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "  1. conda activate $ENV_NAME  (또는 source .venv/bin/activate)"
echo "  2. python scripts/download_ycb.py"
echo "  3. python app/main.py"
