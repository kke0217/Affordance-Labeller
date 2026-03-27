"""Candidate Poses 패널 — pose 추가/삭제 + 연결"""

from state import AppState
from helpers import format_poses


def setup(state: AppState):
    server = state.server

    with server.gui.add_folder("Candidate Poses"):
        gui_name = server.gui.add_text("Pose Name", initial_value="grasp_01")
        gui_pos = server.gui.add_vector3(
            "Position", initial_value=(0.0, 0.05, 0.04), step=0.005,
        )
        gui_grasp = server.gui.add_dropdown(
            "Grasp Type",
            options=["pinch", "power", "lateral", "hook", "precision", "custom"],
            initial_value="pinch",
        )
        gui_hand = server.gui.add_dropdown(
            "Hand Role", options=["left", "right", "either"], initial_value="right",
        )
        gui_aff_link = server.gui.add_dropdown(
            "Link Affordance",
            options=["(none)"] + [a["affordance_id"] for a in state.label.get("affordances", [])],
            initial_value="(none)",
        )
        gui_mask_link = server.gui.add_dropdown(
            "Link Mask",
            options=["(none)"] + [m["mask_id"] for m in state.label.get("contact_region_masks", [])],
            initial_value="(none)",
        )
        add_btn = server.gui.add_button("Add Pose")
        remove_btn = server.gui.add_button("Remove Last Pose")
        state.gui_pose_info = server.gui.add_markdown(
            format_poses(state.label.get("candidate_poses", []))
        )

        def _refresh_link_options():
            gui_aff_link.options = ["(none)"] + [
                a["affordance_id"] for a in state.label.get("affordances", [])
            ]
            gui_mask_link.options = ["(none)"] + [
                m["mask_id"] for m in state.label.get("contact_region_masks", [])
            ]

        state.register_refresh("parts_changed", _refresh_link_options)
        state.register_refresh("affordances_changed", _refresh_link_options)
        state.register_refresh("masks_changed", _refresh_link_options)

        @add_btn.on_click
        def on_add(_):
            name = gui_name.value.strip()
            if not name:
                state.set_status("**Error**: pose 이름을 입력하세요")
                return
            pos = list(gui_pos.value)
            pose_data = {
                "pose_id": f"pose_{name}", "name": name,
                "translation": pos, "rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
                "linked_affordance_id": gui_aff_link.value if gui_aff_link.value != "(none)" else "",
                "linked_mask_id": gui_mask_link.value if gui_mask_link.value != "(none)" else "",
                "semantic_tags": [], "grasp_type": gui_grasp.value,
                "hand_role": gui_hand.value, "confidence": 1.0,
                "approved": False, "comment": "",
            }
            state.label["candidate_poses"].append(pose_data)
            state.viewer.display_pose(pose_data)
            state.gui_pose_info.content = format_poses(state.label["candidate_poses"])
            state.set_status(f"**Pose**: {name} @ [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]")

        @remove_btn.on_click
        def on_remove(_):
            if state.label["candidate_poses"]:
                removed = state.label["candidate_poses"].pop()
                state.viewer.clear_poses()
                for pose in state.label["candidate_poses"]:
                    state.viewer.display_pose(pose)
                state.gui_pose_info.content = format_poses(state.label["candidate_poses"])
                state.set_status(f"**Removed**: {removed['pose_id']}")
            else:
                state.set_status("**Error**: 삭제할 pose가 없습니다")
