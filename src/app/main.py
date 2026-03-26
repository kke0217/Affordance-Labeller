"""
main.py — Affordance Labeller 메인 진입점

Viser 서버를 시작하고 라벨링 UI를 제공합니다.

실행: python app/main.py [--port 8080] [--mesh assets/ycb/025_mug/...]
"""

import argparse
import json
import time
from pathlib import Path

try:
    import viser
except ImportError:
    raise ImportError("viser가 필요합니다: pip install viser")

from viewer import MeshViewer
from io_handler import (
    create_empty_label,
    save_label,
    load_label,
    validate_label,
    print_validation_report,
    LABELS_DIR,
)

# ============================================================
# 전역 상태
# ============================================================
current_label: dict = {}
current_mesh_path: str = ""
viewer: MeshViewer = None


def setup_ui(server: viser.ViserServer):
    """사이드패널 UI 구성"""
    global current_label, viewer

    # === 객체 정보 섹션 ===
    with server.gui.add_folder("Object Info"):
        gui_object_id = server.gui.add_text(
            "Object ID",
            initial_value=current_label.get("object_id", ""),
        )
        gui_input_type = server.gui.add_dropdown(
            "Input Type",
            options=["mesh", "pointcloud", "rgbd", "rgb", "depth"],
            initial_value=current_label.get("input_type", "mesh"),
        )
        gui_annotator = server.gui.add_text(
            "Annotator",
            initial_value=current_label.get("annotator", ""),
        )
        gui_review_status = server.gui.add_dropdown(
            "Review Status",
            options=["draft", "in_review", "reviewed", "approved"],
            initial_value=current_label.get("review_status", "draft"),
        )

    # === 파트 정보 섹션 ===
    with server.gui.add_folder("Parts"):
        parts_info = server.gui.add_markdown(
            _format_parts_info(current_label.get("parts", []))
        )

    # === Affordance 섹션 ===
    with server.gui.add_folder("Affordances"):
        aff_info = server.gui.add_markdown(
            _format_affordances_info(current_label.get("affordances", []))
        )

    # === Candidate Poses 섹션 ===
    with server.gui.add_folder("Candidate Poses"):
        pose_info = server.gui.add_markdown(
            _format_poses_info(current_label.get("candidate_poses", []))
        )

    # === 저장/로드 섹션 ===
    with server.gui.add_folder("File"):
        save_button = server.gui.add_button("Save Label")
        load_button = server.gui.add_button("Load Label")
        validate_button = server.gui.add_button("Validate")
        gui_status = server.gui.add_markdown("*Ready*")

    # === 이벤트 핸들러 ===
    @save_button.on_click
    def on_save(_):
        nonlocal gui_status
        current_label["object_id"] = gui_object_id.value
        current_label["input_type"] = gui_input_type.value
        current_label["annotator"] = gui_annotator.value
        current_label["review_status"] = gui_review_status.value

        try:
            path = save_label(current_label)
            gui_status.content = f"**Saved**: {Path(path).name}"
        except Exception as e:
            gui_status.content = f"**Error**: {e}"

    @load_button.on_click
    def on_load(_):
        nonlocal gui_status
        object_id = gui_object_id.value or current_label.get("object_id", "")
        filepath = LABELS_DIR / f"{object_id}.json"

        try:
            loaded = load_label(str(filepath))
            current_label.update(loaded)

            # UI 갱신
            gui_object_id.value = loaded.get("object_id", "")
            gui_input_type.value = loaded.get("input_type", "mesh")
            gui_annotator.value = loaded.get("annotator", "")
            gui_review_status.value = loaded.get("review_status", "draft")
            parts_info.content = _format_parts_info(loaded.get("parts", []))
            aff_info.content = _format_affordances_info(loaded.get("affordances", []))
            pose_info.content = _format_poses_info(loaded.get("candidate_poses", []))

            # pose 시각화 갱신
            viewer.clear_poses()
            for pose in loaded.get("candidate_poses", []):
                viewer.display_pose(pose)

            # canonical frame 갱신
            if "canonical_frame" in loaded:
                viewer.display_canonical_frame(loaded["canonical_frame"])

            gui_status.content = f"**Loaded**: {filepath.name}"
        except FileNotFoundError:
            gui_status.content = f"**Not Found**: {filepath.name}"
        except Exception as e:
            gui_status.content = f"**Error**: {e}"

    @validate_button.on_click
    def on_validate(_):
        nonlocal gui_status
        issues = validate_label(current_label)
        print_validation_report(issues)

        if not issues:
            gui_status.content = "**Validation**: All clear!"
        else:
            errors = sum(1 for i in issues if i["level"] == "error")
            warnings = sum(1 for i in issues if i["level"] == "warning")
            msgs = [f"- {i['message']}" for i in issues[:5]]
            gui_status.content = (
                f"**Validation**: {errors} errors, {warnings} warnings\n\n"
                + "\n".join(msgs)
            )


def _format_parts_info(parts: list) -> str:
    if not parts:
        return "*No parts defined*"
    lines = []
    for p in parts:
        n_verts = len(p.get("vertex_indices", []))
        lines.append(f"- **{p['name']}** ({p['part_id']}) — {n_verts} vertices")
    return "\n".join(lines)


def _format_affordances_info(affordances: list) -> str:
    if not affordances:
        return "*No affordances defined*"
    lines = []
    for a in affordances:
        tags = ", ".join(a.get("semantic_tags", []))
        lines.append(f"- **{a['label']}** → {a.get('part_ref', '?')} [{tags}]")
    return "\n".join(lines)


def _format_poses_info(poses: list) -> str:
    if not poses:
        return "*No poses defined*"
    lines = []
    for p in poses:
        pos = p.get("translation", [0, 0, 0])
        lines.append(
            f"- **{p['name']}** ({p.get('grasp_type', '?')}) "
            f"@ [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Affordance Labeller")
    parser.add_argument("--port", type=int, default=8080, help="Viser 서버 포트")
    parser.add_argument("--mesh", type=str, default=None, help="초기 로드할 mesh 파일 경로")
    parser.add_argument("--label", type=str, default=None, help="초기 로드할 label JSON 경로")
    parser.add_argument("--object-id", type=str, default="ycb_025_mug", help="객체 ID")
    args = parser.parse_args()

    global current_label, current_mesh_path, viewer

    # 라벨 초기화
    if args.label and Path(args.label).exists():
        current_label = load_label(args.label)
        print(f"[main] 라벨 로드: {args.label}")
    else:
        current_label = create_empty_label(args.object_id, "mesh", "고박사")
        print(f"[main] 빈 라벨 생성: {args.object_id}")

    # Viser 서버 시작
    server = viser.ViserServer(host="0.0.0.0", port=args.port)
    print(f"\n{'='*50}")
    print(f" Affordance Labeller")
    print(f" http://localhost:{args.port}")
    print(f"{'='*50}\n")

    # 뷰어 초기화
    viewer = MeshViewer(server)

    # mesh 로드 및 표시
    if args.mesh:
        current_mesh_path = args.mesh
        if viewer.load_mesh(args.mesh):
            viewer.display_mesh("mug")
            viewer.display_canonical_frame(current_label.get("canonical_frame", {}))

            # 기존 pose 표시
            for pose in current_label.get("candidate_poses", []):
                viewer.display_pose(pose)

    # UI 구성
    setup_ui(server)

    # 서버 유지
    print("[main] 서버 실행 중... (Ctrl+C로 종료)")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[main] 서버 종료")


if __name__ == "__main__":
    main()
