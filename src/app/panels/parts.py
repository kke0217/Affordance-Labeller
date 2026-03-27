"""Parts 패널 — Auto Segment + threshold 슬라이더"""

from state import AppState
from viewer import auto_segment_mug
from helpers import format_parts


def setup(state: AppState):
    server = state.server

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
            state.set_status("**Parts**: 자동 분류 완료")
