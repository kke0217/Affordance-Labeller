"""Contact Masks 패널 — mask type + patch A/B 지정 + click-to-paint 편집"""

import numpy as np

from state import AppState
from helpers import format_masks, apply_mask_overlay, apply_affordance_overlay


def _ray_mesh_intersection(state: AppState, ray_origin, ray_direction):
    """ray와 mesh의 교차점에서 가장 가까운 vertex index를 반환"""
    mesh = state.viewer.loaded_mesh
    if mesh is None:
        return None, None

    origin = np.array(ray_origin)
    direction = np.array(ray_direction)
    direction = direction / np.linalg.norm(direction)

    # trimesh ray intersection
    locations, index_ray, index_tri = mesh.ray.intersects_location(
        ray_origins=[origin],
        ray_directions=[direction],
    )

    if len(locations) == 0:
        return None, None

    # 가장 가까운 교차점
    dists = np.linalg.norm(locations - origin, axis=1)
    closest = np.argmin(dists)
    hit_point = locations[closest]

    return hit_point, index_tri[closest]


def _get_nearby_vertices(mesh, hit_point, radius):
    """hit_point 주변 반지름 내의 vertex indices를 반환"""
    dists = np.linalg.norm(mesh.vertices - hit_point, axis=1)
    return np.where(dists < radius)[0].tolist()


def setup(state: AppState):
    server = state.server

    # 편집 상태
    edit_state = {
        "active_mask_idx": -1,  # 현재 편집 중인 mask 인덱스
        "paint_target": "a",    # "a" 또는 "b"
        "editing": False,       # 편집 모드 활성 여부
    }

    with server.gui.add_folder("Contact Masks"):
        gui_mask_part = server.gui.add_dropdown(
            "Target Part",
            options=["(none)"] + [p["name"] for p in state.label.get("parts", [])],
            initial_value="(none)",
        )
        gui_mask_type = server.gui.add_dropdown(
            "Mask Type",
            options=["handle_pinch", "body_power", "rim_control", "custom"],
            initial_value="handle_pinch",
        )
        gui_patch_a = server.gui.add_dropdown(
            "Patch A (finger)",
            options=["thumb", "index", "index_middle", "palm", "all_fingers"],
            initial_value="thumb",
        )
        gui_patch_b = server.gui.add_dropdown(
            "Patch B (finger)",
            options=["thumb", "index", "index_middle", "palm", "all_fingers"],
            initial_value="index_middle",
        )
        assign_btn = server.gui.add_button("Assign Contact Mask")
        remove_btn = server.gui.add_button("Remove Last Mask")

        # === Patch 편집 UI ===
        server.gui.add_markdown("---\n**Patch 편집 (click-to-paint)**")
        gui_paint_target = server.gui.add_dropdown(
            "Paint Target",
            options=["Patch A (red)", "Patch B (blue)"],
            initial_value="Patch A (red)",
        )
        gui_brush_radius = server.gui.add_slider(
            "Brush Radius", min=0.002, max=0.03, step=0.001, initial_value=0.008,
        )
        edit_btn = server.gui.add_button("Start Editing")
        stop_btn = server.gui.add_button("Stop Editing")

        state.gui_mask_info = server.gui.add_markdown(
            format_masks(state.label.get("contact_region_masks", []))
        )

        def _refresh_options():
            part_names = [p["name"] for p in state.label.get("parts", [])]
            gui_mask_part.options = ["(none)"] + part_names

        state.register_refresh("parts_changed", _refresh_options)

        @assign_btn.on_click
        def on_assign(_):
            part_name = gui_mask_part.value
            if part_name == "(none)":
                state.set_status("**Error**: part를 먼저 선택하세요")
                return
            part = next((p for p in state.label["parts"] if p["name"] == part_name), None)
            if part is None:
                state.set_status(f"**Error**: '{part_name}' part를 찾을 수 없습니다")
                return
            mask_type = gui_mask_type.value
            mask_id = f"mask_{part_name}_{mask_type}"
            vertex_indices = part.get("vertex_indices", [])
            half = len(vertex_indices) // 2
            existing = next((m for m in state.label["contact_region_masks"] if m["mask_id"] == mask_id), None)
            if existing:
                existing["patch_a"]["finger_role"] = gui_patch_a.value
                existing["patch_b"]["finger_role"] = gui_patch_b.value
            else:
                state.label["contact_region_masks"].append({
                    "mask_id": mask_id, "mask_type": mask_type, "part_ref": part["part_id"],
                    "patch_a": {"vertex_indices": vertex_indices[:half], "face_indices": [], "finger_role": gui_patch_a.value},
                    "patch_b": {"vertex_indices": vertex_indices[half:], "face_indices": [], "finger_role": gui_patch_b.value},
                    "comment": "",
                })
            # 편집 대상을 마지막 mask로 설정
            edit_state["active_mask_idx"] = len(state.label["contact_region_masks"]) - 1
            apply_mask_overlay(state)
            state.gui_mask_info.content = format_masks(state.label["contact_region_masks"])
            state.refresh("masks_changed")
            state.set_status(f"**Mask**: {mask_type} → {part_name} (편집하려면 Start Editing)")

        @remove_btn.on_click
        def on_remove(_):
            if state.label["contact_region_masks"]:
                removed = state.label["contact_region_masks"].pop()
                edit_state["active_mask_idx"] = -1
                edit_state["editing"] = False
                apply_affordance_overlay(state)
                state.gui_mask_info.content = format_masks(state.label["contact_region_masks"])
                state.set_status(f"**Removed**: {removed['mask_id']}")
            else:
                state.set_status("**Error**: 삭제할 mask가 없습니다")

        @edit_btn.on_click
        def on_start_edit(_):
            if not state.label["contact_region_masks"]:
                state.set_status("**Error**: mask를 먼저 Assign하세요")
                return
            edit_state["editing"] = True
            edit_state["active_mask_idx"] = len(state.label["contact_region_masks"]) - 1
            mask = state.label["contact_region_masks"][edit_state["active_mask_idx"]]
            state.set_status(f"**Editing**: {mask['mask_id']} — 3D 뷰에서 클릭하여 patch를 칠하세요")

        @stop_btn.on_click
        def on_stop_edit(_):
            edit_state["editing"] = False
            state.set_status("**Editing 종료**")

        @gui_paint_target.on_update
        def on_paint_target_change(_):
            edit_state["paint_target"] = "a" if "A" in gui_paint_target.value else "b"

    # === Click-to-paint: scene pointer event ===
    @server.scene.on_pointer_event("click")
    def on_click(event):
        if not edit_state["editing"]:
            return
        if event.ray_origin is None or event.ray_direction is None:
            return

        hit_point, _ = _ray_mesh_intersection(state, event.ray_origin, event.ray_direction)
        if hit_point is None:
            return

        mask_idx = edit_state["active_mask_idx"]
        if mask_idx < 0 or mask_idx >= len(state.label["contact_region_masks"]):
            return

        mask = state.label["contact_region_masks"][mask_idx]
        radius = gui_brush_radius.value
        nearby = _get_nearby_vertices(state.viewer.loaded_mesh, hit_point, radius)

        if not nearby:
            return

        target = edit_state["paint_target"]
        other = "b" if target == "a" else "a"
        target_key = f"patch_{target}"
        other_key = f"patch_{other}"

        # 대상 patch에 추가, 반대쪽에서 제거
        current_set = set(mask[target_key]["vertex_indices"])
        other_set = set(mask[other_key]["vertex_indices"])
        current_set.update(nearby)
        other_set -= set(nearby)
        mask[target_key]["vertex_indices"] = sorted(current_set)
        mask[other_key]["vertex_indices"] = sorted(other_set)

        # 시각화 갱신
        apply_mask_overlay(state)
        state.gui_mask_info.content = format_masks(state.label["contact_region_masks"])
