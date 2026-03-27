"""Contact Masks 패널 — part 기반 patch A/B 할당

Patch A/B를 별도 paint 모드 없이, 기존 정의된 part를 선택하여 할당한다.
세밀한 접촉 영역이 필요하면 Parts에서 part를 더 세분화한 후 여기서 할당.
"""

from state import AppState
from helpers import format_masks, apply_mask_overlay, apply_affordance_overlay


def setup(state: AppState):
    server = state.server

    with server.gui.add_folder("Contact Masks"):
        gui_mask_type = server.gui.add_dropdown(
            "Mask Type",
            options=["handle_pinch", "body_power", "rim_control", "custom"],
            initial_value="handle_pinch",
        )

        server.gui.add_markdown("**Patch A 설정**")
        gui_patch_a_part = server.gui.add_dropdown(
            "Patch A → Part",
            options=["(none)"] + [p["name"] for p in state.label.get("parts", [])],
            initial_value="(none)",
        )
        gui_patch_a_role = server.gui.add_dropdown(
            "Patch A (finger)",
            options=["thumb", "index", "index_middle", "palm", "all_fingers"],
            initial_value="thumb",
        )

        server.gui.add_markdown("**Patch B 설정**")
        gui_patch_b_part = server.gui.add_dropdown(
            "Patch B → Part",
            options=["(none)"] + [p["name"] for p in state.label.get("parts", [])],
            initial_value="(none)",
        )
        gui_patch_b_role = server.gui.add_dropdown(
            "Patch B (finger)",
            options=["thumb", "index", "index_middle", "palm", "all_fingers"],
            initial_value="index_middle",
        )

        assign_btn = server.gui.add_button("Assign Contact Mask")
        remove_btn = server.gui.add_button("Remove Last Mask")

        server.gui.add_markdown(
            "*Part를 세분화하여 정밀한 접촉 영역을 지정하세요.*\n"
            "*예: handle_thumb, handle_finger 두 part를 만들고 각각 Patch A/B에 할당*"
        )

        state.gui_mask_info = server.gui.add_markdown(
            format_masks(state.label.get("contact_region_masks", []))
        )

        def _refresh_options():
            part_names = [p["name"] for p in state.label.get("parts", [])]
            opts = ["(none)"] + part_names
            gui_patch_a_part.options = opts
            gui_patch_b_part.options = opts

        state.register_refresh("parts_changed", _refresh_options)

        @assign_btn.on_click
        def on_assign(_):
            a_part_name = gui_patch_a_part.value
            b_part_name = gui_patch_b_part.value

            if a_part_name == "(none)" and b_part_name == "(none)":
                state.set_status("**Error**: Patch A 또는 B에 part를 선택하세요")
                return

            # part 찾기
            a_part = next((p for p in state.label["parts"] if p["name"] == a_part_name), None)
            b_part = next((p for p in state.label["parts"] if p["name"] == b_part_name), None)

            a_vertices = a_part.get("vertex_indices", []) if a_part else []
            b_vertices = b_part.get("vertex_indices", []) if b_part else []

            mask_type = gui_mask_type.value
            # part_ref: 가장 관련 있는 part (A 우선)
            part_ref = a_part["part_id"] if a_part else (b_part["part_id"] if b_part else "")
            mask_id = f"mask_{mask_type}_{a_part_name}_{b_part_name}"

            existing = next((m for m in state.label["contact_region_masks"] if m["mask_id"] == mask_id), None)
            if existing:
                existing["patch_a"]["finger_role"] = gui_patch_a_role.value
                existing["patch_a"]["vertex_indices"] = a_vertices
                existing["patch_b"]["finger_role"] = gui_patch_b_role.value
                existing["patch_b"]["vertex_indices"] = b_vertices
            else:
                state.label["contact_region_masks"].append({
                    "mask_id": mask_id, "mask_type": mask_type, "part_ref": part_ref,
                    "patch_a": {"vertex_indices": a_vertices, "face_indices": [], "finger_role": gui_patch_a_role.value},
                    "patch_b": {"vertex_indices": b_vertices, "face_indices": [], "finger_role": gui_patch_b_role.value},
                    "comment": "",
                })

            apply_mask_overlay(state)
            state.gui_mask_info.content = format_masks(state.label["contact_region_masks"])
            state.refresh("masks_changed")
            state.set_status(f"**Mask**: {mask_type} — A:{a_part_name} / B:{b_part_name}")

        @remove_btn.on_click
        def on_remove(_):
            if state.label["contact_region_masks"]:
                removed = state.label["contact_region_masks"].pop()
                apply_affordance_overlay(state)
                state.gui_mask_info.content = format_masks(state.label["contact_region_masks"])
                state.set_status(f"**Removed**: {removed['mask_id']}")
            else:
                state.set_status("**Error**: 삭제할 mask가 없습니다")
