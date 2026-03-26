"""
main.py — Affordance Labeller 메인 진입점

Viser 서버를 시작하고 라벨링 UI를 제공합니다.

실행: python app/main.py [--port 8080] [--mesh assets/ycb/025_mug/...]
"""

import argparse
import os
import signal
import sys
import time
from pathlib import Path

import numpy as np
import trimesh

try:
    import viser
except ImportError:
    raise ImportError("viser가 필요합니다: pip install viser")

from viewer import MeshViewer, auto_segment_mug, PART_COLORS
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

    # === Canonical Frame 섹션 ===
    cf = current_label.get("canonical_frame", {})
    with server.gui.add_folder("Canonical Frame"):
        gui_cf_origin = server.gui.add_vector3(
            "Origin",
            initial_value=tuple(cf.get("origin", [0, 0, 0])),
            step=0.01,
        )
        gui_cf_show = server.gui.add_checkbox("Show Frame", initial_value=True)

        @gui_cf_origin.on_update
        def on_cf_origin_change(_):
            origin = list(gui_cf_origin.value)
            current_label["canonical_frame"]["origin"] = origin
            viewer.display_canonical_frame(current_label["canonical_frame"])

        @gui_cf_show.on_update
        def on_cf_show_change(_):
            if "canonical" in viewer.frame_handles:
                viewer.frame_handles["canonical"].visible = gui_cf_show.value

    # === 파트 정보 섹션 ===
    part_checkboxes = {}
    with server.gui.add_folder("Parts"):
        gui_handle_ratio = server.gui.add_slider(
            "Handle Ratio", min=1.0, max=2.0, step=0.05, initial_value=1.3,
        )
        gui_rim_ratio = server.gui.add_slider(
            "Rim %", min=0.01, max=0.20, step=0.01, initial_value=0.06,
        )
        gui_base_ratio = server.gui.add_slider(
            "Base %", min=0.01, max=0.20, step=0.01, initial_value=0.03,
        )
        auto_segment_btn = server.gui.add_button("Auto Segment (geometry)")
        parts_info = server.gui.add_markdown(
            _format_parts_info(current_label.get("parts", []))
        )

        @auto_segment_btn.on_click
        def on_auto_segment(_):
            nonlocal gui_status
            if viewer.loaded_mesh is None:
                gui_status.content = "**Error**: 메시를 먼저 로드하세요"
                return

            part_indices = auto_segment_mug(
                viewer.loaded_mesh,
                handle_ratio=gui_handle_ratio.value,
                rim_ratio=gui_rim_ratio.value,
                base_ratio=gui_base_ratio.value,
            )
            viewer.apply_part_colors(part_indices)
            current_label["parts"] = viewer.generate_parts_data(part_indices)
            parts_info.content = _format_parts_info(current_label["parts"])
            _refresh_aff_part_options()
            _refresh_mask_part_options()
            gui_status.content = "**Parts**: 자동 분류 완료"

    # === Affordance 편집 섹션 ===
    with server.gui.add_folder("Affordances"):
        # part 선택 → affordance class 부여
        gui_aff_part = server.gui.add_dropdown(
            "Target Part",
            options=["(none)"] + [p["name"] for p in current_label.get("parts", [])],
            initial_value="(none)",
        )
        gui_aff_class = server.gui.add_dropdown(
            "Affordance Class",
            options=["graspable", "pour_support", "handover_region", "placeable", "non_affordance"],
            initial_value="graspable",
        )
        gui_aff_tags = server.gui.add_dropdown(
            "Semantic Tag",
            options=["pick_up", "pour_ready", "handover_ready", "reposition_only", "place_down", "tilt"],
            initial_value="pick_up",
        )
        assign_aff_btn = server.gui.add_button("Assign Affordance")
        remove_aff_btn = server.gui.add_button("Remove Last Affordance")
        aff_info = server.gui.add_markdown(
            _format_affordances_info(current_label.get("affordances", []))
        )

        def _refresh_aff_part_options():
            """parts가 변경되면 드롭다운 옵션 갱신"""
            part_names = [p["name"] for p in current_label.get("parts", [])]
            gui_aff_part.options = ["(none)"] + part_names

        @assign_aff_btn.on_click
        def on_assign_aff(_):
            nonlocal gui_status
            part_name = gui_aff_part.value
            if part_name == "(none)":
                gui_status.content = "**Error**: part를 먼저 선택하세요"
                return

            # 해당 part 찾기
            part = next((p for p in current_label["parts"] if p["name"] == part_name), None)
            if part is None:
                gui_status.content = f"**Error**: '{part_name}' part를 찾을 수 없습니다"
                return

            aff_class = gui_aff_class.value
            tag = gui_aff_tags.value
            aff_id = f"aff_{part_name}_{aff_class}"

            # 기존 동일 affordance 업데이트 또는 새로 추가
            existing = next((a for a in current_label["affordances"] if a["affordance_id"] == aff_id), None)
            if existing:
                if tag not in existing["semantic_tags"]:
                    existing["semantic_tags"].append(tag)
            else:
                current_label["affordances"].append({
                    "affordance_id": aff_id,
                    "label": aff_class,
                    "part_ref": part["part_id"],
                    "vertex_indices": part.get("vertex_indices", []),
                    "face_indices": [],
                    "semantic_tags": [tag],
                    "source_type": "manual",
                    "confidence": 1.0,
                    "comment": "",
                })

            # 색상 오버레이 갱신
            _apply_affordance_overlay()
            aff_info.content = _format_affordances_info(current_label["affordances"])
            _refresh_pose_link_options()
            gui_status.content = f"**Affordance**: {aff_class} → {part_name} [{tag}]"

        @remove_aff_btn.on_click
        def on_remove_aff(_):
            nonlocal gui_status
            if current_label["affordances"]:
                removed = current_label["affordances"].pop()
                _apply_affordance_overlay()
                aff_info.content = _format_affordances_info(current_label["affordances"])
                gui_status.content = f"**Removed**: {removed['affordance_id']}"
            else:
                gui_status.content = "**Error**: 삭제할 affordance가 없습니다"

        def _apply_affordance_overlay():
            """affordance 색상 오버레이 적용"""
            if viewer.loaded_mesh is None:
                return
            from viewer import AFFORDANCE_COLORS
            mesh = viewer.loaded_mesh
            # part 색상 기본값
            colors = np.full((len(mesh.vertices), 4), [180, 180, 180, 255], dtype=np.uint8)
            for part in current_label.get("parts", []):
                indices = part.get("vertex_indices", [])
                if indices:
                    pcolor = PART_COLORS.get(part["name"], PART_COLORS["other"])
                    colors[indices] = pcolor
            # affordance 색상 덮어쓰기
            for aff in current_label.get("affordances", []):
                indices = aff.get("vertex_indices", [])
                if indices:
                    acolor = AFFORDANCE_COLORS.get(aff["label"], (128, 128, 128, 100))
                    colors[indices] = acolor
            mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh, vertex_colors=colors)
            if viewer.mesh_handle:
                viewer.mesh_handle.remove()
            viewer.mesh_handle = viewer.server.scene.add_mesh_trimesh(
                name="/object/mug", mesh=mesh,
            )

    # === Contact Mask 섹션 ===
    with server.gui.add_folder("Contact Masks"):
        gui_mask_part = server.gui.add_dropdown(
            "Target Part",
            options=["(none)"] + [p["name"] for p in current_label.get("parts", [])],
            initial_value="(none)",
        )
        gui_mask_type = server.gui.add_dropdown(
            "Mask Type",
            options=["handle_pinch", "body_power", "rim_control", "custom"],
            initial_value="handle_pinch",
        )
        gui_patch_a_role = server.gui.add_dropdown(
            "Patch A (finger)",
            options=["thumb", "index", "index_middle", "palm", "all_fingers"],
            initial_value="thumb",
        )
        gui_patch_b_role = server.gui.add_dropdown(
            "Patch B (finger)",
            options=["thumb", "index", "index_middle", "palm", "all_fingers"],
            initial_value="index_middle",
        )
        assign_mask_btn = server.gui.add_button("Assign Contact Mask")
        remove_mask_btn = server.gui.add_button("Remove Last Mask")
        mask_info = server.gui.add_markdown(
            _format_masks_info(current_label.get("contact_region_masks", []))
        )

        def _refresh_mask_part_options():
            part_names = [p["name"] for p in current_label.get("parts", [])]
            gui_mask_part.options = ["(none)"] + part_names

        @assign_mask_btn.on_click
        def on_assign_mask(_):
            nonlocal gui_status
            part_name = gui_mask_part.value
            if part_name == "(none)":
                gui_status.content = "**Error**: part를 먼저 선택하세요"
                return

            part = next((p for p in current_label["parts"] if p["name"] == part_name), None)
            if part is None:
                gui_status.content = f"**Error**: '{part_name}' part를 찾을 수 없습니다"
                return

            mask_type = gui_mask_type.value
            mask_id = f"mask_{part_name}_{mask_type}"
            vertex_indices = part.get("vertex_indices", [])

            # patch A/B: vertex_indices를 절반씩 나눔 (초기값, 이후 수동 조정 가능)
            half = len(vertex_indices) // 2
            patch_a_indices = vertex_indices[:half]
            patch_b_indices = vertex_indices[half:]

            # 기존 동일 mask 업데이트 또는 새로 추가
            existing = next((m for m in current_label["contact_region_masks"]
                           if m["mask_id"] == mask_id), None)
            if existing:
                existing["patch_a"]["finger_role"] = gui_patch_a_role.value
                existing["patch_b"]["finger_role"] = gui_patch_b_role.value
            else:
                current_label["contact_region_masks"].append({
                    "mask_id": mask_id,
                    "mask_type": mask_type,
                    "part_ref": part["part_id"],
                    "patch_a": {
                        "vertex_indices": patch_a_indices,
                        "face_indices": [],
                        "finger_role": gui_patch_a_role.value,
                    },
                    "patch_b": {
                        "vertex_indices": patch_b_indices,
                        "face_indices": [],
                        "finger_role": gui_patch_b_role.value,
                    },
                    "comment": "",
                })

            _apply_mask_overlay()
            mask_info.content = _format_masks_info(current_label["contact_region_masks"])
            _refresh_pose_link_options()
            gui_status.content = f"**Mask**: {mask_type} → {part_name}"

        @remove_mask_btn.on_click
        def on_remove_mask(_):
            nonlocal gui_status
            if current_label["contact_region_masks"]:
                removed = current_label["contact_region_masks"].pop()
                _apply_affordance_overlay()  # 기본 색상 복원
                mask_info.content = _format_masks_info(current_label["contact_region_masks"])
                gui_status.content = f"**Removed**: {removed['mask_id']}"
            else:
                gui_status.content = "**Error**: 삭제할 mask가 없습니다"

        def _apply_mask_overlay():
            """contact mask patch A/B 색상 오버레이"""
            if viewer.loaded_mesh is None:
                return
            # 먼저 affordance 오버레이 적용 (베이스)
            _apply_affordance_overlay()
            mesh = viewer.loaded_mesh
            colors = np.array(mesh.visual.vertex_colors, dtype=np.uint8)
            # mask patch A = 빨강, patch B = 파랑
            PATCH_A_COLOR = (255, 80, 80, 220)
            PATCH_B_COLOR = (80, 80, 255, 220)
            for mask in current_label.get("contact_region_masks", []):
                a_indices = mask.get("patch_a", {}).get("vertex_indices", [])
                b_indices = mask.get("patch_b", {}).get("vertex_indices", [])
                if a_indices:
                    colors[a_indices] = PATCH_A_COLOR
                if b_indices:
                    colors[b_indices] = PATCH_B_COLOR
            mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh, vertex_colors=colors)
            if viewer.mesh_handle:
                viewer.mesh_handle.remove()
            viewer.mesh_handle = viewer.server.scene.add_mesh_trimesh(
                name="/object/mug", mesh=mesh,
            )

    # === Candidate Poses 섹션 ===
    with server.gui.add_folder("Candidate Poses"):
        gui_pose_name = server.gui.add_text("Pose Name", initial_value="grasp_01")
        gui_pose_position = server.gui.add_vector3(
            "Position", initial_value=(0.0, 0.05, 0.04), step=0.005,
        )
        gui_pose_grasp_type = server.gui.add_dropdown(
            "Grasp Type",
            options=["pinch", "power", "lateral", "hook", "precision", "custom"],
            initial_value="pinch",
        )
        gui_pose_hand = server.gui.add_dropdown(
            "Hand Role",
            options=["left", "right", "either"],
            initial_value="right",
        )
        # 연결 드롭다운 (affordance / mask)
        gui_pose_aff_link = server.gui.add_dropdown(
            "Link Affordance",
            options=["(none)"] + [a["affordance_id"] for a in current_label.get("affordances", [])],
            initial_value="(none)",
        )
        gui_pose_mask_link = server.gui.add_dropdown(
            "Link Mask",
            options=["(none)"] + [m["mask_id"] for m in current_label.get("contact_region_masks", [])],
            initial_value="(none)",
        )
        add_pose_btn = server.gui.add_button("Add Pose")
        remove_pose_btn = server.gui.add_button("Remove Last Pose")
        pose_info = server.gui.add_markdown(
            _format_poses_info(current_label.get("candidate_poses", []))
        )

        def _refresh_pose_link_options():
            gui_pose_aff_link.options = ["(none)"] + [
                a["affordance_id"] for a in current_label.get("affordances", [])
            ]
            gui_pose_mask_link.options = ["(none)"] + [
                m["mask_id"] for m in current_label.get("contact_region_masks", [])
            ]

        @add_pose_btn.on_click
        def on_add_pose(_):
            nonlocal gui_status
            name = gui_pose_name.value.strip()
            if not name:
                gui_status.content = "**Error**: pose 이름을 입력하세요"
                return

            pose_id = f"pose_{name}"
            pos = list(gui_pose_position.value)

            pose_data = {
                "pose_id": pose_id,
                "name": name,
                "translation": pos,
                "rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
                "linked_affordance_id": gui_pose_aff_link.value if gui_pose_aff_link.value != "(none)" else "",
                "linked_mask_id": gui_pose_mask_link.value if gui_pose_mask_link.value != "(none)" else "",
                "semantic_tags": [],
                "grasp_type": gui_pose_grasp_type.value,
                "hand_role": gui_pose_hand.value,
                "confidence": 1.0,
                "approved": False,
                "comment": "",
            }

            current_label["candidate_poses"].append(pose_data)
            viewer.display_pose(pose_data)
            pose_info.content = _format_poses_info(current_label["candidate_poses"])
            gui_status.content = f"**Pose**: {name} @ [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]"

        @remove_pose_btn.on_click
        def on_remove_pose(_):
            nonlocal gui_status
            if current_label["candidate_poses"]:
                removed = current_label["candidate_poses"].pop()
                viewer.clear_poses()
                for pose in current_label["candidate_poses"]:
                    viewer.display_pose(pose)
                pose_info.content = _format_poses_info(current_label["candidate_poses"])
                gui_status.content = f"**Removed**: {removed['pose_id']}"
            else:
                gui_status.content = "**Error**: 삭제할 pose가 없습니다"

    # === 저장/로드 섹션 ===
    with server.gui.add_folder("File"):
        save_button = server.gui.add_button("Save Label")
        load_button = server.gui.add_button("Load Label")
        validate_button = server.gui.add_button("Validate")
        quit_button = server.gui.add_button("Quit Server", color="red")
        gui_status = server.gui.add_markdown("*Ready*")

    # === 이벤트 핸들러 ===
    @save_button.on_click
    def on_save(_):
        nonlocal gui_status
        current_label["object_id"] = gui_object_id.value
        current_label["input_type"] = gui_input_type.value
        current_label["annotator"] = gui_annotator.value
        current_label["review_status"] = gui_review_status.value
        current_label["canonical_frame"]["origin"] = list(gui_cf_origin.value)

        try:
            path = save_label(current_label)
            # Save 후 자동 validation
            issues = validate_label(current_label)
            if issues:
                errors = sum(1 for i in issues if i["level"] == "error")
                warnings = sum(1 for i in issues if i["level"] == "warning")
                msgs = [f"- {i['message']}" for i in issues[:3]]
                gui_status.content = (
                    f"**Saved**: {Path(path).name}\n\n"
                    f"⚠ {errors} errors, {warnings} warnings\n\n"
                    + "\n".join(msgs)
                )
            else:
                gui_status.content = f"**Saved**: {Path(path).name} ✓"
            print_validation_report(issues)
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
            mask_info.content = _format_masks_info(loaded.get("contact_region_masks", []))
            pose_info.content = _format_poses_info(loaded.get("candidate_poses", []))
            _refresh_aff_part_options()
            _refresh_mask_part_options()
            _refresh_pose_link_options()

            # 색상 오버레이 복원
            if loaded.get("parts") or loaded.get("affordances"):
                _apply_affordance_overlay()
            if loaded.get("contact_region_masks"):
                _apply_mask_overlay()

            # pose 시각화 갱신
            viewer.clear_poses()
            for pose in loaded.get("candidate_poses", []):
                viewer.display_pose(pose)

            # canonical frame 갱신
            if "canonical_frame" in loaded:
                gui_cf_origin.value = tuple(loaded["canonical_frame"].get("origin", [0, 0, 0]))
                viewer.display_canonical_frame(loaded["canonical_frame"])

            gui_status.content = f"**Loaded**: {filepath.name}"
        except FileNotFoundError:
            gui_status.content = f"**Not Found**: {filepath.name}"
        except Exception as e:
            gui_status.content = f"**Error**: {e}"

    @quit_button.on_click
    def on_quit(_):
        print("\n[main] 서버 종료 (UI 버튼)")
        import subprocess
        subprocess.Popen(["kill", "-9", str(os.getpid())])

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


def _format_masks_info(masks: list) -> str:
    if not masks:
        return "*No contact masks defined*"
    lines = []
    for m in masks:
        a_count = len(m.get("patch_a", {}).get("vertex_indices", []))
        b_count = len(m.get("patch_b", {}).get("vertex_indices", []))
        a_role = m.get("patch_a", {}).get("finger_role", "?")
        b_role = m.get("patch_b", {}).get("finger_role", "?")
        lines.append(
            f"- **{m['mask_type']}** → {m.get('part_ref', '?')} "
            f"[A:{a_role}({a_count}v) / B:{b_role}({b_count}v)]"
        )
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

            # 기존 라벨에서 part/affordance 색상 복원
            if current_label.get("parts"):
                from viewer import AFFORDANCE_COLORS
                colors = np.full((len(viewer.loaded_mesh.vertices), 4), [180, 180, 180, 255], dtype=np.uint8)
                for part in current_label["parts"]:
                    indices = part.get("vertex_indices", [])
                    if indices:
                        colors[indices] = PART_COLORS.get(part["name"], PART_COLORS["other"])
                for aff in current_label.get("affordances", []):
                    indices = aff.get("vertex_indices", [])
                    if indices:
                        colors[indices] = AFFORDANCE_COLORS.get(aff["label"], (128, 128, 128, 100))
                viewer.loaded_mesh.visual = trimesh.visual.ColorVisuals(
                    mesh=viewer.loaded_mesh, vertex_colors=colors,
                )
                if viewer.mesh_handle:
                    viewer.mesh_handle.remove()
                viewer.mesh_handle = server.scene.add_mesh_trimesh(
                    name="/object/mug", mesh=viewer.loaded_mesh,
                )
                print("[main] 기존 라벨 색상 오버레이 적용")

            # 기존 pose 표시
            for pose in current_label.get("candidate_poses", []):
                viewer.display_pose(pose)

    # UI 구성
    setup_ui(server)

    # Ctrl+C 시그널 핸들러
    def _shutdown(sig, frame):
        print("\n[main] 서버 종료")
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # 서버 유지
    print("[main] 서버 실행 중... (Ctrl+C로 종료)")
    while True:
        time.sleep(1.0)


if __name__ == "__main__":
    main()
