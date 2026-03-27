"""File 패널 — Save / Load / Validate / Quit"""

import os
import subprocess
from pathlib import Path

from state import AppState
from helpers import (
    format_parts, format_affordances, format_masks, format_poses,
    apply_affordance_overlay, apply_mask_overlay,
)
from io_handler import (
    save_label, load_label, validate_label, print_validation_report, LABELS_DIR,
)


def setup(state: AppState):
    server = state.server

    with server.gui.add_folder("File"):
        save_btn = server.gui.add_button("Save Label")
        load_btn = server.gui.add_button("Load Label")
        validate_btn = server.gui.add_button("Validate")
        quit_btn = server.gui.add_button("Quit Server", color="red")
        gui_status = server.gui.add_markdown("*Ready*")
        state.gui_status = gui_status

    @save_btn.on_click
    def on_save(_):
        state.label["object_id"] = state.gui_object_id.value
        state.label["input_type"] = state.gui_input_type.value
        state.label["annotator"] = state.gui_annotator.value
        state.label["review_status"] = state.gui_review_status.value
        state.label["canonical_frame"]["origin"] = list(state.gui_cf_origin.value)
        try:
            path = save_label(state.label)
            issues = validate_label(state.label)
            if issues:
                errors = sum(1 for i in issues if i["level"] == "error")
                warnings = sum(1 for i in issues if i["level"] == "warning")
                msgs = [f"- {i['message']}" for i in issues[:3]]
                state.set_status(
                    f"**Saved**: {Path(path).name}\n\n"
                    f"⚠ {errors} errors, {warnings} warnings\n\n"
                    + "\n".join(msgs)
                )
            else:
                state.set_status(f"**Saved**: {Path(path).name} ✓")
            print_validation_report(issues)
        except Exception as e:
            state.set_status(f"**Error**: {e}")

    @load_btn.on_click
    def on_load(_):
        object_id = state.gui_object_id.value or state.label.get("object_id", "")
        filepath = LABELS_DIR / f"{object_id}.json"
        try:
            loaded = load_label(str(filepath))
            state.label.update(loaded)
            # UI 갱신
            state.gui_object_id.value = loaded.get("object_id", "")
            state.gui_input_type.value = loaded.get("input_type", "mesh")
            state.gui_annotator.value = loaded.get("annotator", "")
            state.gui_review_status.value = loaded.get("review_status", "draft")
            state.gui_parts_info.content = format_parts(loaded.get("parts", []))
            state.gui_aff_info.content = format_affordances(loaded.get("affordances", []))
            state.gui_mask_info.content = format_masks(loaded.get("contact_region_masks", []))
            state.gui_pose_info.content = format_poses(loaded.get("candidate_poses", []))
            state.refresh("parts_changed")
            state.refresh("affordances_changed")
            state.refresh("masks_changed")
            # 색상 복원
            if loaded.get("parts") or loaded.get("affordances"):
                apply_affordance_overlay(state)
            if loaded.get("contact_region_masks"):
                apply_mask_overlay(state)
            # pose 복원
            state.viewer.clear_poses()
            for pose in loaded.get("candidate_poses", []):
                state.viewer.display_pose(pose)
            # canonical frame 복원
            if "canonical_frame" in loaded:
                state.gui_cf_origin.value = tuple(loaded["canonical_frame"].get("origin", [0, 0, 0]))
                state.viewer.display_canonical_frame(loaded["canonical_frame"])
            state.set_status(f"**Loaded**: {filepath.name}")
        except FileNotFoundError:
            state.set_status(f"**Not Found**: {filepath.name}")
        except Exception as e:
            state.set_status(f"**Error**: {e}")

    @quit_btn.on_click
    def on_quit(_):
        print("\n[main] 서버 종료 (UI 버튼)")
        subprocess.Popen(["kill", "-9", str(os.getpid())])

    @validate_btn.on_click
    def on_validate(_):
        issues = validate_label(state.label)
        print_validation_report(issues)
        if not issues:
            state.set_status("**Validation**: All clear!")
        else:
            errors = sum(1 for i in issues if i["level"] == "error")
            warnings = sum(1 for i in issues if i["level"] == "warning")
            msgs = [f"- {i['message']}" for i in issues[:5]]
            state.set_status(
                f"**Validation**: {errors} errors, {warnings} warnings\n\n"
                + "\n".join(msgs)
            )
