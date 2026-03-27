"""Contact Masks 패널 — mask type + patch A/B 지정"""

from state import AppState
from helpers import format_masks, apply_mask_overlay, apply_affordance_overlay


def setup(state: AppState):
    server = state.server

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
            apply_mask_overlay(state)
            state.gui_mask_info.content = format_masks(state.label["contact_region_masks"])
            state.refresh("masks_changed")
            state.set_status(f"**Mask**: {mask_type} → {part_name}")

        @remove_btn.on_click
        def on_remove(_):
            if state.label["contact_region_masks"]:
                removed = state.label["contact_region_masks"].pop()
                apply_affordance_overlay(state)
                state.gui_mask_info.content = format_masks(state.label["contact_region_masks"])
                state.set_status(f"**Removed**: {removed['mask_id']}")
            else:
                state.set_status("**Error**: 삭제할 mask가 없습니다")
