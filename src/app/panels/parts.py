"""Parts 패널 — Auto Segment (mug 전용) + 수동 part 정의 (범용)

Painting 모드: 클릭으로 vertex를 part에 할당.
orbit 회전은 Stop Painting 후 가능.
"""

import numpy as np
import trimesh as tm

from state import AppState
from viewer import auto_segment_mug, PART_COLORS, get_part_color
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


def _update_part_colors(state):
    """현재 parts 기준으로 색상 갱신"""
    mesh = state.viewer.loaded_mesh
    if mesh is None:
        return
    colors = np.full((len(mesh.vertices), 4), [180, 180, 180, 255], dtype=np.uint8)
    for p in state.label["parts"]:
        indices = p.get("vertex_indices", [])
        if indices:
            colors[indices] = get_part_color(p["name"])
    mesh.visual = tm.visual.ColorVisuals(mesh=mesh, vertex_colors=colors)
    if state.viewer.mesh_handle:
        state.viewer.mesh_handle.remove()
    state.viewer.mesh_handle = state.server.scene.add_mesh_trimesh(
        name="/object/mug", mesh=mesh,
    )


def setup(state: AppState):
    server = state.server

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
        gui_part_name = server.gui.add_text(
            "Part Name", initial_value="body",
        )
        gui_part_brush = server.gui.add_slider(
            "Brush Radius", min=0.002, max=0.05, step=0.001, initial_value=0.01,
        )
        add_part_btn = server.gui.add_button("Add Empty Part")
        paint_part_btn = server.gui.add_button("Start Painting")
        stop_paint_btn = server.gui.add_button("Stop Painting")
        clear_parts_btn = server.gui.add_button("Clear All Parts")

        server.gui.add_markdown(
            "*Painting 중: 클릭으로 칠하기*\n"
            "*orbit은 Stop Painting 후 가능*\n"
            "*접촉 영역 세분화 팁: handle_thumb, handle_finger 등으로 part를 나누세요*"
        )

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
            name = gui_part_name.value.strip()
            if not name:
                state.set_status("**Error**: part 이름을 입력하세요")
                return
            part_id = f"part_{name}"
            if any(p["part_id"] == part_id for p in state.label["parts"]):
                state.set_status(f"**Error**: '{name}' part가 이미 존재합니다")
                return
            color = get_part_color(name)
            state.label["parts"].append({
                "part_id": part_id, "name": name,
                "vertex_indices": [], "face_indices": [],
                "visible": True, "color": [c / 255.0 for c in color], "comment": "",
            })
            state.gui_parts_info.content = format_parts(state.label["parts"])
            state.refresh("parts_changed")
            state.set_status(f"**Part 추가**: {name}")

        def _on_click_paint(event):
            """click 콜백"""
            print(f"[paint] 클릭 감지 — ray_origin={event.ray_origin is not None}")
            if event.ray_origin is None or event.ray_direction is None:
                print("[paint] ray 정보 없음, 무시")
                return

            hit_point = _ray_mesh_nearest(state, event.ray_origin, event.ray_direction)
            if hit_point is None:
                print("[paint] mesh 교차점 없음")
                return
            print(f"[paint] hit: [{hit_point[0]:.4f}, {hit_point[1]:.4f}, {hit_point[2]:.4f}]")

            target_name = paint_state["target_part"]
            part = next((p for p in state.label["parts"] if p["name"] == target_name), None)
            if part is None:
                return

            mesh = state.viewer.loaded_mesh
            radius = gui_part_brush.value
            dists = np.linalg.norm(mesh.vertices - hit_point, axis=1)
            nearby = set(np.where(dists < radius)[0].tolist())
            if not nearby:
                return

            # 다른 part에서 제거, 대상 part에 추가
            for p in state.label["parts"]:
                if p["name"] != target_name:
                    p["vertex_indices"] = [v for v in p["vertex_indices"] if v not in nearby]
            current_set = set(part["vertex_indices"])
            current_set.update(nearby)
            part["vertex_indices"] = sorted(current_set)

            _update_part_colors(state)
            state.gui_parts_info.content = format_parts(state.label["parts"])

        @paint_part_btn.on_click
        def on_start_paint(_):
            name = gui_part_name.value.strip()
            part = next((p for p in state.label["parts"] if p["name"] == name), None)
            if part is None:
                state.set_status(f"**Error**: '{name}' part를 먼저 Add하세요")
                return
            paint_state["editing"] = True
            paint_state["target_part"] = name
            server.scene.on_pointer_event("click")(_on_click_paint)
            state.set_status(f"**Painting**: {name} — 클릭으로 칠하기 | Stop Painting으로 종료")

        @stop_paint_btn.on_click
        def on_stop_paint(_):
            paint_state["editing"] = False
            server.scene.remove_pointer_callback()
            state.set_status("**Painting 종료** — orbit 조작 복원됨")

        @clear_parts_btn.on_click
        def on_clear_parts(_):
            state.label["parts"] = []
            state.gui_parts_info.content = format_parts([])
            state.refresh("parts_changed")
            if state.viewer.loaded_mesh is not None:
                mesh = state.viewer.loaded_mesh
                mesh.visual = tm.visual.ColorVisuals(
                    mesh=mesh,
                    vertex_colors=np.full((len(mesh.vertices), 4), [180, 180, 180, 255], dtype=np.uint8),
                )
                state.viewer.mesh_handle = server.scene.add_mesh_trimesh(
                    name="/object/mug", mesh=mesh,
                )
            state.set_status("**Parts**: 전부 삭제됨")
