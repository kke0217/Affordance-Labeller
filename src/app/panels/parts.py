"""Parts 패널 — Auto Segment (mug 전용) + 수동 part 정의 (범용)"""

import numpy as np

from state import AppState
from viewer import auto_segment_mug, PART_COLORS
from helpers import format_parts


def _ray_mesh_nearest(state, ray_origin, ray_direction):
    """ray-mesh intersection으로 hit point 반환"""
    mesh = state.viewer.loaded_mesh
    if mesh is None:
        return None
    origin = np.array(ray_origin)
    direction = np.array(ray_direction)
    direction = direction / np.linalg.norm(direction)
    locations, _, _ = mesh.ray.intersects_location(
        ray_origins=[origin], ray_directions=[direction],
    )
    if len(locations) == 0:
        return None
    dists = np.linalg.norm(locations - origin, axis=1)
    return locations[np.argmin(dists)]


def setup(state: AppState):
    server = state.server

    # 편집 상태
    paint_state = {"editing": False, "target_part": ""}

    with server.gui.add_folder("Parts"):
        # === Auto Segment (mug 전용) ===
        server.gui.add_markdown("**Auto Segment (mug 전용)**")
        gui_handle_ratio = server.gui.add_slider(
            "Handle Ratio", min=1.0, max=2.0, step=0.05, initial_value=1.3,
        )
        gui_rim_ratio = server.gui.add_slider(
            "Rim %", min=0.01, max=0.20, step=0.01, initial_value=0.06,
        )
        gui_base_ratio = server.gui.add_slider(
            "Base %", min=0.01, max=0.20, step=0.01, initial_value=0.03,
        )
        auto_segment_btn = server.gui.add_button("Auto Segment (mug)")

        # === 수동 Part 정의 (범용) ===
        server.gui.add_markdown("---\n**수동 Part 정의 (범용)**")
        gui_part_name = server.gui.add_dropdown(
            "Part Name",
            options=["body", "handle", "rim", "interior", "base", "other"],
            initial_value="body",
        )
        gui_part_brush = server.gui.add_slider(
            "Brush Radius", min=0.002, max=0.03, step=0.001, initial_value=0.008,
        )
        add_part_btn = server.gui.add_button("Add Empty Part")
        paint_part_btn = server.gui.add_button("Start Painting Part")
        stop_paint_btn = server.gui.add_button("Stop Painting")
        clear_parts_btn = server.gui.add_button("Clear All Parts")

        state.gui_parts_info = server.gui.add_markdown(
            format_parts(state.label.get("parts", []))
        )

        @auto_segment_btn.on_click
        def on_auto_segment(_):
            if state.viewer.loaded_mesh is None:
                state.set_status("**Error**: 메시를 먼저 로드하세요")
                return
            part_indices = auto_segment_mug(
                state.viewer.loaded_mesh,
                handle_ratio=gui_handle_ratio.value,
                rim_ratio=gui_rim_ratio.value,
                base_ratio=gui_base_ratio.value,
            )
            state.viewer.apply_part_colors(part_indices)
            state.label["parts"] = state.viewer.generate_parts_data(part_indices)
            state.gui_parts_info.content = format_parts(state.label["parts"])
            state.refresh("parts_changed")
            state.set_status("**Parts**: 자동 분류 완료 (mug 전용)")

        @add_part_btn.on_click
        def on_add_part(_):
            name = gui_part_name.value
            part_id = f"part_{name}"
            # 이미 존재하면 무시
            if any(p["part_id"] == part_id for p in state.label["parts"]):
                state.set_status(f"**Error**: '{name}' part가 이미 존재합니다")
                return
            color = PART_COLORS.get(name, PART_COLORS["other"])
            state.label["parts"].append({
                "part_id": part_id, "name": name,
                "vertex_indices": [], "face_indices": [],
                "visible": True, "color": [c / 255.0 for c in color], "comment": "",
            })
            state.gui_parts_info.content = format_parts(state.label["parts"])
            state.refresh("parts_changed")
            state.set_status(f"**Part 추가**: {name} (빈 상태 — Painting으로 vertex 추가)")

        @paint_part_btn.on_click
        def on_start_paint(_):
            name = gui_part_name.value
            part = next((p for p in state.label["parts"] if p["name"] == name), None)
            if part is None:
                state.set_status(f"**Error**: '{name}' part를 먼저 Add하세요")
                return
            paint_state["editing"] = True
            paint_state["target_part"] = name
            state.set_status(f"**Painting**: {name} — 3D 뷰에서 클릭하여 vertex 추가")

        @stop_paint_btn.on_click
        def on_stop_paint(_):
            paint_state["editing"] = False
            state.set_status("**Painting 종료**")

        @clear_parts_btn.on_click
        def on_clear_parts(_):
            state.label["parts"] = []
            state.gui_parts_info.content = format_parts([])
            state.refresh("parts_changed")
            # 기본 색상으로 복원
            if state.viewer.loaded_mesh is not None:
                import trimesh
                mesh = state.viewer.loaded_mesh
                mesh.visual = trimesh.visual.ColorVisuals(
                    mesh=mesh,
                    vertex_colors=np.full((len(mesh.vertices), 4), [180, 180, 180, 255], dtype=np.uint8),
                )
                if state.viewer.mesh_handle:
                    state.viewer.mesh_handle.remove()
                state.viewer.mesh_handle = server.scene.add_mesh_trimesh(
                    name="/object/mug", mesh=mesh,
                )
            state.set_status("**Parts**: 전부 삭제됨")

    # === Click-to-paint part: scene pointer event ===
    @server.scene.on_pointer_event("click")
    def on_click_part(event):
        if not paint_state["editing"]:
            return
        if event.ray_origin is None or event.ray_direction is None:
            return

        hit_point = _ray_mesh_nearest(state, event.ray_origin, event.ray_direction)
        if hit_point is None:
            return

        target_name = paint_state["target_part"]
        part = next((p for p in state.label["parts"] if p["name"] == target_name), None)
        if part is None:
            return

        mesh = state.viewer.loaded_mesh
        radius = gui_part_brush.value
        dists = np.linalg.norm(mesh.vertices - hit_point, axis=1)
        nearby = np.where(dists < radius)[0].tolist()
        if not nearby:
            return

        # 다른 part에서 제거, 대상 part에 추가
        nearby_set = set(nearby)
        for p in state.label["parts"]:
            if p["name"] != target_name:
                p["vertex_indices"] = [v for v in p["vertex_indices"] if v not in nearby_set]

        current_set = set(part["vertex_indices"])
        current_set.update(nearby)
        part["vertex_indices"] = sorted(current_set)

        # 색상 갱신
        colors = np.full((len(mesh.vertices), 4), [180, 180, 180, 255], dtype=np.uint8)
        for p in state.label["parts"]:
            indices = p.get("vertex_indices", [])
            if indices:
                colors[indices] = PART_COLORS.get(p["name"], PART_COLORS["other"])

        import trimesh as tm
        mesh.visual = tm.visual.ColorVisuals(mesh=mesh, vertex_colors=colors)
        if state.viewer.mesh_handle:
            state.viewer.mesh_handle.remove()
        state.viewer.mesh_handle = server.scene.add_mesh_trimesh(
            name="/object/mug", mesh=mesh,
        )
        state.gui_parts_info.content = format_parts(state.label["parts"])
