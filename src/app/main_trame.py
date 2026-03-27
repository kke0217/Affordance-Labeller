"""
main_trame.py — Affordance Labeller (PyVista+Trame 버전)

Ctrl+드래그=orbit, 일반 클릭/드래그=painting

실행: python app/main_trame.py --mesh assets/ycb/025_mug/google_512k/nontextured.ply --server
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pyvista as pv
import trimesh
import vtk

from trame.app import get_server
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3, vtk as vtk_widgets

from io_handler import (
    create_empty_label, save_label, load_label,
    validate_label, print_validation_report, LABELS_DIR,
)
from viewer import auto_segment_mug, PART_COLORS, get_part_color, AFFORDANCE_COLORS


# ============================================================
# PyVista mesh 관리
# ============================================================
class TrameMeshViewer:
    """PyVista 기반 mesh 관리"""

    def __init__(self, plotter: pv.Plotter):
        self.plotter = plotter
        self.pv_mesh = None
        self.tri_mesh = None

    def load_mesh(self, mesh_path: str) -> bool:
        path = Path(mesh_path)
        if not path.exists():
            print(f"[viewer] 파일 없음: {path}")
            return False
        loaded = trimesh.load(str(path))
        if isinstance(loaded, trimesh.Scene):
            self.tri_mesh = loaded.dump(concatenate=True)
        else:
            self.tri_mesh = loaded
        # trimesh → PyVista
        faces = np.hstack([
            np.full((len(self.tri_mesh.faces), 1), 3, dtype=np.int32),
            self.tri_mesh.faces.astype(np.int32),
        ]).ravel()
        self.pv_mesh = pv.PolyData(
            self.tri_mesh.vertices.astype(np.float64), faces
        )
        colors = np.full((self.pv_mesh.n_points, 3), 180, dtype=np.uint8)
        self.pv_mesh.point_data["colors"] = colors
        self.plotter.add_mesh(self.pv_mesh, scalars="colors", rgb=True)
        self.plotter.reset_camera()
        print(f"[viewer] 로드: {path.name} ({self.pv_mesh.n_points} vertices)")
        return True

    def update_colors(self, label: dict):
        """label의 parts/affordances/masks 기준으로 vertex 색상 갱신"""
        if self.pv_mesh is None:
            return
        colors = np.full((self.pv_mesh.n_points, 3), 180, dtype=np.uint8)
        for part in label.get("parts", []):
            indices = part.get("vertex_indices", [])
            if indices:
                c = get_part_color(part["name"])
                colors[indices] = c[:3]
        for aff in label.get("affordances", []):
            indices = aff.get("vertex_indices", [])
            if indices:
                c = AFFORDANCE_COLORS.get(aff["label"], (128, 128, 128, 100))
                colors[indices] = c[:3]
        PATCH_A = [255, 80, 80]
        PATCH_B = [80, 80, 255]
        for mask in label.get("contact_region_masks", []):
            a_idx = mask.get("patch_a", {}).get("vertex_indices", [])
            b_idx = mask.get("patch_b", {}).get("vertex_indices", [])
            if a_idx:
                colors[a_idx] = PATCH_A
            if b_idx:
                colors[b_idx] = PATCH_B
        self.pv_mesh.point_data["colors"] = colors


# ============================================================
# Custom Interactor Style (Ctrl+orbit, 일반=painting)
# ============================================================
class PaintInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, app):
        self.app = app
        self.AddObserver("LeftButtonPressEvent", self.on_left_press)
        self.AddObserver("LeftButtonReleaseEvent", self.on_left_release)
        self.AddObserver("MouseMoveEvent", self.on_mouse_move)
        self._press_pos = None
        self._dragging = False

    def on_left_press(self, obj, event):
        iren = self.GetInteractor()
        ctrl = iren.GetControlKey()
        if ctrl:
            iren.SetControlKey(0)
            self.OnLeftButtonDown()
            iren.SetControlKey(1)
            return
        if not self.app["paint_active"]:
            self.OnLeftButtonDown()
            return
        self._press_pos = iren.GetEventPosition()
        self._dragging = False

    def on_left_release(self, obj, event):
        iren = self.GetInteractor()
        ctrl = iren.GetControlKey()
        if ctrl:
            iren.SetControlKey(0)
            self.OnLeftButtonUp()
            iren.SetControlKey(1)
            return
        if not self.app["paint_active"]:
            self.OnLeftButtonUp()
            return
        if not self._dragging and self._press_pos:
            self._do_pick(self._press_pos)
        self._press_pos = None
        self._dragging = False

    def on_mouse_move(self, obj, event):
        iren = self.GetInteractor()
        ctrl = iren.GetControlKey()
        if ctrl:
            iren.SetControlKey(0)
            self.OnMouseMove()
            iren.SetControlKey(1)
            return
        if self._press_pos is not None:
            cur = iren.GetEventPosition()
            if abs(cur[0] - self._press_pos[0]) > 3 or abs(cur[1] - self._press_pos[1]) > 3:
                self._dragging = True
                self._do_pick(cur)
            return
        self.OnMouseMove()

    def _do_pick(self, pos):
        iren = self.GetInteractor()
        renderer = iren.GetRenderWindow().GetRenderers().GetFirstRenderer()
        picker = vtk.vtkCellPicker()
        picker.SetTolerance(0.005)
        picker.Pick(pos[0], pos[1], 0, renderer)
        if picker.GetCellId() < 0:
            return
        hit = np.array(picker.GetPickPosition())
        self.app.paint_at(hit)


# ============================================================
# 메인 앱
# ============================================================
class AffordanceApp:
    def __init__(self, mesh_path, label_path=None, object_id="ycb_025_mug", port=8080):
        self.server = get_server("affordance_labeller")
        self.state = self.server.state
        self.ctrl = self.server.controller

        # PyVista
        pv.OFF_SCREEN = True
        self.plotter = pv.Plotter()
        self.viewer = TrameMeshViewer(self.plotter)

        # 라벨
        if label_path and Path(label_path).exists():
            self.label = load_label(label_path)
            print(f"[main] 라벨 로드: {label_path}")
        else:
            self.label = create_empty_label(object_id, "mesh", "고광은")

        # mesh 로드
        if mesh_path:
            self.viewer.load_mesh(mesh_path)
            if self.label.get("parts"):
                self.viewer.update_colors(self.label)

        # 상태 초기화
        self.state.paint_active = False
        self.state.current_part = "body"
        self.state.brush_radius = 0.01
        self.state.object_id = self.label.get("object_id", object_id)
        self.state.annotator = self.label.get("annotator", "고광은")
        self.state.review_status = self.label.get("review_status", "draft")
        self.state.status_msg = "Ctrl+드래그=orbit | Start Painting 후 클릭/드래그=칠하기"
        self.state.parts_text = self._fmt_parts()
        self.state.aff_text = self._fmt_affs()
        self.state.mask_text = self._fmt_masks()
        self.state.pose_text = self._fmt_poses()

        # Interactor style
        style = PaintInteractorStyle(self)
        self.plotter.iren.interactor.SetInteractorStyle(style)

        self._build_ui()
        self.port = port

    def __getitem__(self, key):
        return getattr(self.state, key)

    # === Painting ===
    def paint_at(self, hit_point):
        part_name = self.state.current_part
        part = next((p for p in self.label["parts"] if p["name"] == part_name), None)
        if part is None:
            return
        mesh = self.viewer.pv_mesh
        radius = self.state.brush_radius
        dists = np.linalg.norm(mesh.points - hit_point, axis=1)
        nearby = set(np.where(dists < radius)[0].tolist())
        if not nearby:
            return
        for p in self.label["parts"]:
            if p["name"] != part_name:
                p["vertex_indices"] = [v for v in p["vertex_indices"] if v not in nearby]
        current = set(part["vertex_indices"])
        current.update(nearby)
        part["vertex_indices"] = sorted(current)
        self.viewer.update_colors(self.label)
        self.ctrl.view_update()
        self.state.parts_text = self._fmt_parts()
        self.state.status_msg = f"painted {len(nearby)}v → {part_name}"

    # === Actions ===
    def toggle_paint(self, active):
        self.state.paint_active = active
        if active:
            self.state.status_msg = f"Painting: '{self.state.current_part}' — 클릭/드래그=칠하기, Ctrl+드래그=orbit"
        else:
            self.state.status_msg = "orbit 모드"

    def add_part(self):
        name = self.state.current_part.strip()
        if not name:
            return
        if any(p["part_id"] == f"part_{name}" for p in self.label["parts"]):
            self.state.status_msg = f"'{name}' 이미 존재"
            return
        color = get_part_color(name)
        self.label["parts"].append({
            "part_id": f"part_{name}", "name": name,
            "vertex_indices": [], "face_indices": [],
            "visible": True, "color": [c / 255.0 for c in color], "comment": "",
        })
        self.state.parts_text = self._fmt_parts()
        self._refresh_dropdowns()
        self.state.status_msg = f"Part 추가: {name}"

    def clear_parts(self):
        self.label["parts"] = []
        if self.viewer.pv_mesh:
            self.viewer.pv_mesh.point_data["colors"] = np.full(
                (self.viewer.pv_mesh.n_points, 3), 180, dtype=np.uint8
            )
            self.ctrl.view_update()
        self.state.parts_text = self._fmt_parts()
        self._refresh_dropdowns()
        self.state.status_msg = "Parts 초기화"

    def auto_segment(self):
        if self.viewer.tri_mesh is None:
            return
        parts = auto_segment_mug(self.viewer.tri_mesh)
        self.label["parts"] = []
        for name, indices in parts.items():
            color = get_part_color(name)
            self.label["parts"].append({
                "part_id": f"part_{name}", "name": name,
                "vertex_indices": indices.tolist(), "face_indices": [],
                "visible": True, "color": [c / 255.0 for c in color], "comment": "",
            })
        self.viewer.update_colors(self.label)
        self.ctrl.view_update()
        self.state.parts_text = self._fmt_parts()
        self._refresh_dropdowns()
        self.state.status_msg = "Auto Segment 완료 (mug)"

    def assign_affordance(self):
        part_name = self.state.aff_part
        if part_name == "(none)":
            return
        part = next((p for p in self.label["parts"] if p["name"] == part_name), None)
        if not part:
            return
        aff_class = self.state.aff_class
        tag = self.state.aff_tag
        aff_id = f"aff_{part_name}_{aff_class}"
        existing = next((a for a in self.label["affordances"] if a["affordance_id"] == aff_id), None)
        if existing:
            if tag not in existing["semantic_tags"]:
                existing["semantic_tags"].append(tag)
        else:
            self.label["affordances"].append({
                "affordance_id": aff_id, "label": aff_class,
                "part_ref": part["part_id"],
                "vertex_indices": part.get("vertex_indices", []),
                "face_indices": [], "semantic_tags": [tag],
                "source_type": "manual", "confidence": 1.0, "comment": "",
            })
        self.viewer.update_colors(self.label)
        self.ctrl.view_update()
        self.state.aff_text = self._fmt_affs()
        self._refresh_dropdowns()
        self.state.status_msg = f"Affordance: {aff_class} → {part_name} [{tag}]"

    def assign_mask(self):
        a_part = self.state.mask_patch_a_part
        b_part = self.state.mask_patch_b_part
        if a_part == "(none)" and b_part == "(none)":
            return
        a = next((p for p in self.label["parts"] if p["name"] == a_part), None)
        b = next((p for p in self.label["parts"] if p["name"] == b_part), None)
        mask_type = self.state.mask_type
        mask_id = f"mask_{mask_type}_{a_part}_{b_part}"
        self.label["contact_region_masks"].append({
            "mask_id": mask_id, "mask_type": mask_type,
            "part_ref": (a["part_id"] if a else (b["part_id"] if b else "")),
            "patch_a": {"vertex_indices": a.get("vertex_indices", []) if a else [], "face_indices": [], "finger_role": self.state.patch_a_role},
            "patch_b": {"vertex_indices": b.get("vertex_indices", []) if b else [], "face_indices": [], "finger_role": self.state.patch_b_role},
            "comment": "",
        })
        self.viewer.update_colors(self.label)
        self.ctrl.view_update()
        self.state.mask_text = self._fmt_masks()
        self._refresh_dropdowns()
        self.state.status_msg = f"Mask: {mask_type} A:{a_part} B:{b_part}"

    def add_pose(self):
        name = self.state.pose_name.strip()
        if not name:
            return
        self.label["candidate_poses"].append({
            "pose_id": f"pose_{name}", "name": name,
            "translation": [0.0, 0.0, 0.04],
            "rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
            "linked_affordance_id": self.state.pose_aff_link if self.state.pose_aff_link != "(none)" else "",
            "linked_mask_id": self.state.pose_mask_link if self.state.pose_mask_link != "(none)" else "",
            "semantic_tags": [], "grasp_type": self.state.pose_grasp_type,
            "hand_role": self.state.pose_hand, "confidence": 1.0,
            "approved": False, "comment": "",
        })
        self.state.pose_text = self._fmt_poses()
        self.state.status_msg = f"Pose 추가: {name}"

    def do_save(self):
        self.label["object_id"] = self.state.object_id
        self.label["annotator"] = self.state.annotator
        self.label["review_status"] = self.state.review_status
        try:
            path = save_label(self.label)
            issues = validate_label(self.label)
            print_validation_report(issues)
            if issues:
                errs = sum(1 for i in issues if i["level"] == "error")
                warns = sum(1 for i in issues if i["level"] == "warning")
                self.state.status_msg = f"Saved: {Path(path).name} ({errs}E {warns}W)"
            else:
                self.state.status_msg = f"Saved: {Path(path).name} ✓"
        except Exception as e:
            self.state.status_msg = f"Error: {e}"

    def do_load(self):
        oid = self.state.object_id
        filepath = LABELS_DIR / f"{oid}.json"
        try:
            self.label = load_label(str(filepath))
            self.state.annotator = self.label.get("annotator", "")
            self.state.review_status = self.label.get("review_status", "draft")
            self.viewer.update_colors(self.label)
            self.ctrl.view_update()
            self.state.parts_text = self._fmt_parts()
            self.state.aff_text = self._fmt_affs()
            self.state.mask_text = self._fmt_masks()
            self.state.pose_text = self._fmt_poses()
            self._refresh_dropdowns()
            self.state.status_msg = f"Loaded: {filepath.name}"
        except FileNotFoundError:
            self.state.status_msg = f"Not Found: {filepath.name}"

    # === Helpers ===
    def _part_names(self):
        return ["(none)"] + [p["name"] for p in self.label.get("parts", [])]

    def _aff_ids(self):
        return ["(none)"] + [a["affordance_id"] for a in self.label.get("affordances", [])]

    def _mask_ids(self):
        return ["(none)"] + [m["mask_id"] for m in self.label.get("contact_region_masks", [])]

    def _refresh_dropdowns(self):
        self.state.part_options = self._part_names()
        self.state.aff_link_options = self._aff_ids()
        self.state.mask_link_options = self._mask_ids()

    def _fmt_parts(self):
        if not self.label.get("parts"):
            return "No parts"
        return " | ".join(f"{p['name']}({len(p.get('vertex_indices',[]))}v)" for p in self.label["parts"])

    def _fmt_affs(self):
        if not self.label.get("affordances"):
            return "No affordances"
        return " | ".join(f"{a['label']}→{a.get('part_ref','?')}" for a in self.label["affordances"])

    def _fmt_masks(self):
        if not self.label.get("contact_region_masks"):
            return "No masks"
        return " | ".join(f"{m['mask_type']}" for m in self.label["contact_region_masks"])

    def _fmt_poses(self):
        if not self.label.get("candidate_poses"):
            return "No poses"
        return " | ".join(f"{p['name']}({p.get('grasp_type','?')})" for p in self.label["candidate_poses"])

    # === UI ===
    def _build_ui(self):
        self.state.part_options = self._part_names()
        self.state.aff_part = "(none)"
        self.state.aff_class = "graspable"
        self.state.aff_tag = "pick_up"
        self.state.mask_type = "handle_pinch"
        self.state.mask_patch_a_part = "(none)"
        self.state.mask_patch_b_part = "(none)"
        self.state.patch_a_role = "thumb"
        self.state.patch_b_role = "index_middle"
        self.state.pose_name = "grasp_01"
        self.state.pose_grasp_type = "pinch"
        self.state.pose_hand = "right"
        self.state.pose_aff_link = "(none)"
        self.state.pose_mask_link = "(none)"
        self.state.aff_link_options = self._aff_ids()
        self.state.mask_link_options = self._mask_ids()

        with SinglePageLayout(self.server, full_height=True) as layout:
            layout.title.set_text("Affordance Labeller (Trame)")

            with layout.content:
                with vuetify3.VRow(classes="fill-height ma-0", style="height: calc(100vh - 48px);"):

                    # === 사이드패널 (왼쪽 스크롤) ===
                    with vuetify3.VCol(cols=3, style="overflow-y: auto; max-height: calc(100vh - 48px); background: #fafafa;"):

                        # --- Object Info ---
                        vuetify3.VCardTitle("Object Info", class_="text-subtitle-2 pa-1")
                        vuetify3.VTextField(v_model=("object_id",), label="Object ID", density="compact", class_="mx-2", hide_details=True)
                        vuetify3.VTextField(v_model=("annotator",), label="Annotator", density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VSelect(v_model=("review_status",), label="Review", items=("['draft','in_review','reviewed','approved']",), density="compact", class_="mx-2 mt-1", hide_details=True)

                        vuetify3.VDivider(class_="my-2")

                        # --- Parts ---
                        vuetify3.VCardTitle("Parts", class_="text-subtitle-2 pa-1")
                        vuetify3.VBtn("Auto Segment (mug)", click=self.auto_segment, color="purple", size="small", block=True, class_="mx-2")
                        vuetify3.VTextField(v_model=("current_part",), label="Part Name", density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VSlider(v_model=("brush_radius",), label="Brush", min=0.002, max=0.05, step=0.001, hide_details=True, class_="mx-2")
                        with vuetify3.VRow(class_="mx-1", no_gutters=True):
                            with vuetify3.VCol(cols=4):
                                vuetify3.VBtn("Add", click=self.add_part, size="x-small", block=True)
                            with vuetify3.VCol(cols=4):
                                vuetify3.VBtn("Paint", click=(self.toggle_paint, "[true]"), color="green", size="x-small", block=True)
                            with vuetify3.VCol(cols=4):
                                vuetify3.VBtn("Stop", click=(self.toggle_paint, "[false]"), color="red", size="x-small", block=True)
                        vuetify3.VBtn("Clear All", click=self.clear_parts, size="x-small", class_="mx-2 mt-1", block=True)
                        vuetify3.VCardText("{{ parts_text }}", class_="text-caption pa-1")

                        vuetify3.VDivider(class_="my-2")

                        # --- Affordances ---
                        vuetify3.VCardTitle("Affordances", class_="text-subtitle-2 pa-1")
                        vuetify3.VSelect(v_model=("aff_part",), label="Target Part", items=("part_options",), density="compact", class_="mx-2", hide_details=True)
                        vuetify3.VSelect(v_model=("aff_class",), label="Class", items=("['graspable','pour_support','handover_region','placeable','non_affordance']",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VSelect(v_model=("aff_tag",), label="Tag", items=("['pick_up','pour_ready','handover_ready','reposition_only','place_down','tilt']",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VBtn("Assign Affordance", click=self.assign_affordance, size="small", block=True, class_="mx-2 mt-1")
                        vuetify3.VCardText("{{ aff_text }}", class_="text-caption pa-1")

                        vuetify3.VDivider(class_="my-2")

                        # --- Contact Masks ---
                        vuetify3.VCardTitle("Contact Masks", class_="text-subtitle-2 pa-1")
                        vuetify3.VSelect(v_model=("mask_type",), label="Mask Type", items=("['handle_pinch','body_power','rim_control','custom']",), density="compact", class_="mx-2", hide_details=True)
                        vuetify3.VSelect(v_model=("mask_patch_a_part",), label="Patch A Part", items=("part_options",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VSelect(v_model=("patch_a_role",), label="A finger", items=("['thumb','index','index_middle','palm','all_fingers']",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VSelect(v_model=("mask_patch_b_part",), label="Patch B Part", items=("part_options",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VSelect(v_model=("patch_b_role",), label="B finger", items=("['thumb','index','index_middle','palm','all_fingers']",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VBtn("Assign Mask", click=self.assign_mask, size="small", block=True, class_="mx-2 mt-1")
                        vuetify3.VCardText("{{ mask_text }}", class_="text-caption pa-1")

                        vuetify3.VDivider(class_="my-2")

                        # --- Poses ---
                        vuetify3.VCardTitle("Poses", class_="text-subtitle-2 pa-1")
                        vuetify3.VTextField(v_model=("pose_name",), label="Name", density="compact", class_="mx-2", hide_details=True)
                        vuetify3.VSelect(v_model=("pose_grasp_type",), label="Grasp", items=("['pinch','power','lateral','hook','precision','custom']",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VSelect(v_model=("pose_hand",), label="Hand", items=("['left','right','either']",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VSelect(v_model=("pose_aff_link",), label="Link Aff", items=("aff_link_options",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VSelect(v_model=("pose_mask_link",), label="Link Mask", items=("mask_link_options",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VBtn("Add Pose", click=self.add_pose, size="small", block=True, class_="mx-2 mt-1")
                        vuetify3.VCardText("{{ pose_text }}", class_="text-caption pa-1")

                        vuetify3.VDivider(class_="my-2")

                        # --- File ---
                        with vuetify3.VRow(class_="mx-1 mb-2", no_gutters=True):
                            with vuetify3.VCol(cols=6):
                                vuetify3.VBtn("Save", click=self.do_save, color="blue", size="small", block=True)
                            with vuetify3.VCol(cols=6):
                                vuetify3.VBtn("Load", click=self.do_load, size="small", block=True)

                    # === 3D 뷰포트 (오른쪽) ===
                    with vuetify3.VCol(cols=9, classes="pa-0"):
                        view = vtk_widgets.VtkRemoteView(
                            self.plotter.ren_win,
                            interactive_ratio=1,
                        )
                        self.ctrl.view_update = view.update
                        self.ctrl.on_server_ready.add(self.ctrl.view_update)

            with layout.footer:
                vuetify3.VCardText("{{ status_msg }}", class_="pa-1 text-caption")

    def run(self):
        print(f"\n{'='*50}")
        print(f" Affordance Labeller (PyVista+Trame)")
        print(f" http://localhost:{self.port}")
        print(f"{'='*50}")
        print(f"  클릭/드래그 = 칠하기 (Start Painting 후)")
        print(f"  Ctrl+드래그 = orbit 회전")
        print()
        self.server.start(port=self.port)


# ============================================================
# 진입점
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Affordance Labeller (Trame)")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--mesh", type=str, default=None)
    parser.add_argument("--label", type=str, default=None)
    parser.add_argument("--object-id", type=str, default="ycb_025_mug")
    parser.add_argument("--server", action="store_true")
    args = parser.parse_args()

    app = AffordanceApp(
        mesh_path=args.mesh,
        label_path=args.label,
        object_id=args.object_id,
        port=args.port,
    )
    app.run()


if __name__ == "__main__":
    main()
