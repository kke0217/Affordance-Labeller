"""Candidate Poses 패널 — TransformControls 기즈모로 6D pose 직접 조작"""

import numpy as np

from state import AppState
from helpers import format_poses


def setup(state: AppState):
    server = state.server

    # 현재 편집 중인 기즈모 핸들
    gizmo_state = {"handle": None, "editing": False}

    with server.gui.add_folder("Candidate Poses"):
        gui_name = server.gui.add_text("Pose Name", initial_value="grasp_01")
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

        server.gui.add_markdown("---\n**Pose 배치 (드래그로 조작)**")
        place_btn = server.gui.add_button("Place Gizmo")
        confirm_btn = server.gui.add_button("Confirm Pose")
        cancel_btn = server.gui.add_button("Cancel")
        remove_btn = server.gui.add_button("Remove Last Pose")

        server.gui.add_markdown(
            "*Place Gizmo → 3D 뷰에서 화살표/링을 드래그하여 위치·회전 조정 → Confirm*"
        )

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

        @place_btn.on_click
        def on_place(_):
            name = gui_name.value.strip()
            if not name:
                state.set_status("**Error**: pose 이름을 입력하세요")
                return
            # 기존 기즈모 제거
            if gizmo_state["handle"] is not None:
                gizmo_state["handle"].remove()

            # 기즈모를 객체 중심 부근에 배치
            init_pos = (0.0, 0.0, 0.04)
            if state.viewer.loaded_mesh is not None:
                center = state.viewer.loaded_mesh.vertices.mean(axis=0)
                init_pos = tuple(center)

            handle = server.scene.add_transform_controls(
                name=f"/gizmo/{name}",
                scale=0.07,
                position=init_pos,
                wxyz=(1.0, 0.0, 0.0, 0.0),
                depth_test=False,
                opacity=0.9,
            )
            gizmo_state["handle"] = handle
            gizmo_state["editing"] = True
            state.set_status(
                f"**Gizmo 배치**: {name}\n\n"
                "화살표=이동, 링=회전 | Confirm으로 확정"
            )

        @confirm_btn.on_click
        def on_confirm(_):
            handle = gizmo_state["handle"]
            if handle is None or not gizmo_state["editing"]:
                state.set_status("**Error**: 먼저 Place Gizmo를 눌러주세요")
                return

            name = gui_name.value.strip()
            pos = list(handle.position)
            wxyz = list(handle.wxyz)
            # wxyz → xyzw 변환 (Viser는 wxyz, 스키마는 xyzw)
            rotation_xyzw = [wxyz[1], wxyz[2], wxyz[3], wxyz[0]]

            pose_data = {
                "pose_id": f"pose_{name}", "name": name,
                "translation": [float(p) for p in pos],
                "rotation_xyzw": [float(r) for r in rotation_xyzw],
                "linked_affordance_id": gui_aff_link.value if gui_aff_link.value != "(none)" else "",
                "linked_mask_id": gui_mask_link.value if gui_mask_link.value != "(none)" else "",
                "semantic_tags": [], "grasp_type": gui_grasp.value,
                "hand_role": gui_hand.value, "confidence": 1.0,
                "approved": False, "comment": "",
            }

            state.label["candidate_poses"].append(pose_data)

            # 기즈모 제거 후 고정 좌표축으로 교체
            handle.remove()
            gizmo_state["handle"] = None
            gizmo_state["editing"] = False
            state.viewer.display_pose(pose_data)

            state.gui_pose_info.content = format_poses(state.label["candidate_poses"])
            state.set_status(
                f"**Pose 확정**: {name} @ "
                f"[{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]"
            )

        @cancel_btn.on_click
        def on_cancel(_):
            if gizmo_state["handle"] is not None:
                gizmo_state["handle"].remove()
                gizmo_state["handle"] = None
                gizmo_state["editing"] = False
                state.set_status("**Gizmo 취소**")

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
