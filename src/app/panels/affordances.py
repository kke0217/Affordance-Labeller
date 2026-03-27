"""Affordances 패널 — affordance class + semantic tag 할당"""

from state import AppState
from helpers import format_affordances, apply_affordance_overlay


def setup(state: AppState):
    server = state.server

    with server.gui.add_folder("Affordances"):
        gui_aff_part = server.gui.add_dropdown(
            "Target Part",
            options=["(none)"] + [p["name"] for p in state.label.get("parts", [])],
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
        assign_btn = server.gui.add_button("Assign Affordance")
        remove_btn = server.gui.add_button("Remove Last Affordance")
        state.gui_aff_info = server.gui.add_markdown(
            format_affordances(state.label.get("affordances", []))
        )

        def _refresh_options():
            part_names = [p["name"] for p in state.label.get("parts", [])]
            gui_aff_part.options = ["(none)"] + part_names

        # 패널 간 통신: parts 변경 시 드롭다운 갱신
        state.register_refresh("parts_changed", _refresh_options)

        @assign_btn.on_click
        def on_assign(_):
            part_name = gui_aff_part.value
            if part_name == "(none)":
                state.set_status("**Error**: part를 먼저 선택하세요")
                return
            part = next((p for p in state.label["parts"] if p["name"] == part_name), None)
            if part is None:
                state.set_status(f"**Error**: '{part_name}' part를 찾을 수 없습니다")
                return
            aff_class = gui_aff_class.value
            tag = gui_aff_tags.value
            aff_id = f"aff_{part_name}_{aff_class}"
            existing = next((a for a in state.label["affordances"] if a["affordance_id"] == aff_id), None)
            if existing:
                if tag not in existing["semantic_tags"]:
                    existing["semantic_tags"].append(tag)
            else:
                state.label["affordances"].append({
                    "affordance_id": aff_id, "label": aff_class,
                    "part_ref": part["part_id"],
                    "vertex_indices": part.get("vertex_indices", []),
                    "face_indices": [], "semantic_tags": [tag],
                    "source_type": "manual", "confidence": 1.0, "comment": "",
                })
            apply_affordance_overlay(state)
            state.gui_aff_info.content = format_affordances(state.label["affordances"])
            state.refresh("affordances_changed")
            state.set_status(f"**Affordance**: {aff_class} → {part_name} [{tag}]")

        @remove_btn.on_click
        def on_remove(_):
            if state.label["affordances"]:
                removed = state.label["affordances"].pop()
                apply_affordance_overlay(state)
                state.gui_aff_info.content = format_affordances(state.label["affordances"])
                state.set_status(f"**Removed**: {removed['affordance_id']}")
            else:
                state.set_status("**Error**: 삭제할 affordance가 없습니다")
