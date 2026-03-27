"""
main.py — Affordance Labeller 메인 진입점

Viser 서버를 시작하고 라벨링 UI를 제공합니다.

실행: python app/main.py [--port 8080] [--mesh assets/ycb/025_mug/...]
"""

import argparse
import signal
import sys
import time
from pathlib import Path

try:
    import viser
except ImportError:
    raise ImportError("viser가 필요합니다: pip install viser")

from state import AppState
from helpers import apply_affordance_overlay
from io_handler import load_label
from panels import object_info, parts, affordances, contact_masks, candidate_poses, file_ops


def setup_ui(state: AppState):
    """사이드패널 UI 구성 — 각 패널 모듈에 위임"""
    object_info.setup(state)
    parts.setup(state)
    affordances.setup(state)
    contact_masks.setup(state)
    candidate_poses.setup(state)
    file_ops.setup(state)


def main():
    parser = argparse.ArgumentParser(description="Affordance Labeller")
    parser.add_argument("--port", type=int, default=8080, help="Viser 서버 포트")
    parser.add_argument("--mesh", type=str, default=None, help="초기 로드할 mesh 파일 경로")
    parser.add_argument("--label", type=str, default=None, help="초기 로드할 label JSON 경로")
    parser.add_argument("--object-id", type=str, default="ycb_025_mug", help="객체 ID")
    args = parser.parse_args()

    # Viser 서버 시작
    server = viser.ViserServer(host="0.0.0.0", port=args.port)
    print(f"\n{'='*50}")
    print(f" Affordance Labeller")
    print(f" http://localhost:{args.port}")
    print(f"{'='*50}\n")

    # 상태 초기화
    state = AppState(server, object_id=args.object_id, annotator="고광은")

    # 기존 라벨 로드
    if args.label and Path(args.label).exists():
        state.label = load_label(args.label)
        print(f"[main] 라벨 로드: {args.label}")

    # mesh 로드 및 표시
    if args.mesh:
        state.mesh_path = args.mesh
        if state.viewer.load_mesh(args.mesh):
            state.viewer.display_mesh("mug")
            state.viewer.display_canonical_frame(state.label.get("canonical_frame", {}))

            if state.label.get("parts"):
                apply_affordance_overlay(state)
                print("[main] 기존 라벨 색상 오버레이 적용")

            for pose in state.label.get("candidate_poses", []):
                state.viewer.display_pose(pose)

    # UI 구성
    setup_ui(state)

    # 시그널 핸들러
    def _shutdown(sig, frame):
        print("\n[main] 서버 종료")
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    print("[main] 서버 실행 중... (Ctrl+C로 종료)")
    while True:
        time.sleep(1.0)


if __name__ == "__main__":
    main()
