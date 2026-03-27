"""Candidate Poses 패널 — pose 추가/삭제 + 연결 + rotation 편집"""

import numpy as np
from scipy.spatial.transform import Rotation

from state import AppState
from helpers import format_poses


def _euler_to_xyzw(roll_deg, pitch_deg, yaw_deg):
    """Euler 각도(deg) → quaternion [x, y, z, w]"""
    r = Rotation.from_euler("xyz", [roll_deg, pitch_deg, yaw_deg], degrees=True)
    xyzw = r.as_quat()  # scipy: [x, y, z, w]
    return xyzw.tolist()


def _xyzw_to_euler(xyzw):
    """quaternion [x, y, z, w] → Euler 각도(deg)"""
    r = Rotation.from_quat(xyzw)
    return r.as_euler("xyz", degrees=True).tolist()


def setup(state: AppState):
    server = state.server

    with server.gui.add_folder("Candidate Poses"):
        gui_name = server.gui.add_text("Pose Name", initial_value="grasp_01")
        gui_pos = server.gui.add_vector3(
            "Position", initial_value=(0.0, 0.05, 0.04), step=0.005,
        )
        gui_rot = server.gui.add_vector3(
            "Rotation (deg)", initial_value=(0.0, 0.0, 0.0), step=5.0,
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
            rot_deg = list(gui_rot.value)
            rotation_xyzw = _euler_to_xyzw(*rot_deg)

            pose_data = {
                "pose_id": f"pose_{name}", "name": name,
                "translation": pos, "rotation_xyzw": rotation_xyzw,
                "linked_affordance_id": gui_aff_link.value if gui_aff_link.value != "(none)" else "",
                "linked_mask_id": gui_mask_link.value if gui_mask_link.value != "(none)" else "",
                "semantic_tags": [], "grasp_type": gui_grasp.value,
                "hand_role": gui_hand.value, "confidence": 1.0,
                "approved": False, "comment": "",
            }
            state.label["candidate_poses"].append(pose_data)
            state.viewer.display_pose(pose_data)
            state.gui_pose_info.content = format_poses(state.label["candidate_poses"])
            state.set_status(
                f"**Pose**: {name} @ [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}] "
                f"rot [{rot_deg[0]:.0f}, {rot_deg[1]:.0f}, {rot_deg[2]:.0f}]°"
            )

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
