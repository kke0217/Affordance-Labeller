"""Object Info + Canonical Frame 패널"""

from state import AppState


def setup(state: AppState):
    server = state.server

    with server.gui.add_folder("Object Info"):
        state.gui_object_id = server.gui.add_text(
            "Object ID", initial_value=state.label.get("object_id", ""),
        )
        state.gui_input_type = server.gui.add_dropdown(
            "Input Type",
            options=["mesh", "pointcloud", "rgbd", "rgb", "depth"],
            initial_value=state.label.get("input_type", "mesh"),
        )
        state.gui_annotator = server.gui.add_text(
            "Annotator", initial_value=state.label.get("annotator", ""),
        )
        state.gui_review_status = server.gui.add_dropdown(
            "Review Status",
            options=["draft", "in_review", "reviewed", "approved"],
            initial_value=state.label.get("review_status", "draft"),
        )

    cf = state.label.get("canonical_frame", {})
    with server.gui.add_folder("Canonical Frame"):
        state.gui_cf_origin = server.gui.add_vector3(
            "Origin", initial_value=tuple(cf.get("origin", [0, 0, 0])), step=0.01,
        )
        gui_cf_show = server.gui.add_checkbox("Show Frame", initial_value=True)

        @state.gui_cf_origin.on_update
        def on_cf_origin_change(_):
            state.label["canonical_frame"]["origin"] = list(state.gui_cf_origin.value)
            state.viewer.display_canonical_frame(state.label["canonical_frame"])

        @gui_cf_show.on_update
        def on_cf_show_change(_):
            if "canonical" in state.viewer.frame_handles:
                state.viewer.frame_handles["canonical"].visible = gui_cf_show.value
