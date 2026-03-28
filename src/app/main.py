"""
main.py — Affordance Labeller (PyVista+Trame)

Ctrl+드래그=orbit, 왼쪽 클릭/드래그=painting, 오른쪽 클릭/드래그=지우기

실행: python app/main.py --mesh assets/ycb/025_mug/google_512k/nontextured.ply --server
"""

import argparse
from pathlib import Path

import numpy as np
import pyvista as pv
from scipy.spatial.transform import Rotation

from trame.app import get_server
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3, vtk as vtk_widgets

from io_handler import (
    create_empty_label, save_label, load_label,
    validate_label, print_validation_report, LABELS_DIR,
)
from viewer import auto_segment_mug, auto_segment_generic, get_part_color
from viewer_trame import TrameMeshViewer
from interactor import PaintInteractorStyle


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
        self.state.pose_place_mode = False
        self.state.current_part = "body"
        self.state.brush_radius = 0.01
        self.state.n_clusters = 4
        self.state.rename_from = "(none)"
        self.state.rename_to = ""
        self.state.object_id = self.label.get("object_id", object_id)
        self.state.annotator = self.label.get("annotator", "고광은")
        self.state.review_status = self.label.get("review_status", "draft")
        self.state.status_msg = "Ctrl+드래그=orbit | Start Painting 후 클릭/드래그=칠하기"
        self._refresh_parts_ui()
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
        self._refresh_parts_ui()
        self.state.status_msg = f"painted {len(nearby)}v → {part_name}"

    # === Erasing (오른쪽 클릭/드래그) ===
    def erase_at(self, hit_point):
        """hit_point 주변 vertex를 현재 선택된 part에서만 제거"""
        mesh = self.viewer.pv_mesh
        radius = self.state.brush_radius
        dists = np.linalg.norm(mesh.points - hit_point, axis=1)
        nearby = set(np.where(dists < radius)[0].tolist())
        if not nearby:
            return
        part_name = self.state.current_part
        part = next((p for p in self.label["parts"] if p["name"] == part_name), None)
        if part:
            # 선택된 part에서만 제거
            part["vertex_indices"] = [v for v in part["vertex_indices"] if v not in nearby]
        else:
            # part가 없으면 모든 part에서 제거
            for p in self.label["parts"]:
                p["vertex_indices"] = [v for v in p["vertex_indices"] if v not in nearby]
        self.viewer.update_colors(self.label)
        self.ctrl.view_update()
        self._refresh_parts_ui()
        self.state.status_msg = f"erased {len(nearby)}v from '{part_name}'"

    # === Pose 시각화 헬퍼 ===
    def _create_pose_axes(self, name, pos, rotation_xyzw, scale=0.015):
        """RGB 좌표축 화살표를 3D 뷰포트에 추가"""
        rot = Rotation.from_quat(rotation_xyzw)  # xyzw
        mat = rot.as_matrix()
        origin = np.array(pos)
        axes_data = [
            ("x", mat[:, 0], "red"),
            ("y", mat[:, 1], "green"),
            ("z", mat[:, 2], "blue"),
        ]
        for axis_name, direction, color in axes_data:
            arrow = pv.Arrow(
                start=origin,
                direction=direction,
                scale=scale,
                tip_length=0.3,
                tip_radius=0.15,
                shaft_radius=0.05,
            )
            actor_name = f"pose_{name}_{axis_name}"
            self.plotter.add_mesh(arrow, color=color, name=actor_name)
        # 중심에 작은 구체
        sphere = pv.Sphere(radius=scale * 0.12, center=origin)
        self.plotter.add_mesh(sphere, color="white", name=f"pose_{name}_center")

    def _remove_pose_axes(self, name):
        """pose의 좌표축 마커 제거"""
        for suffix in ["x", "y", "z", "center"]:
            actor_name = f"pose_{name}_{suffix}"
            try:
                self.plotter.remove_actor(actor_name)
            except Exception:
                pass

    def _update_pose_axes(self, pose_data):
        """pose의 좌표축을 현재 rotation으로 갱신"""
        name = pose_data["name"]
        self._remove_pose_axes(name)
        self._create_pose_axes(
            name, pose_data["translation"], pose_data["rotation_xyzw"]
        )

    # === Pose 배치 (클릭 위치에 pose 생성) ===
    def place_pose_at(self, hit_point):
        """클릭한 3D 위치에 pose를 배치 — 연속 배치 가능"""
        base_name = self.state.pose_name.strip()
        if not base_name:
            base_name = "grasp"
        idx = len(self.label["candidate_poses"])
        name = f"{base_name}_{idx:02d}"
        while any(p["pose_id"] == f"pose_{name}" for p in self.label["candidate_poses"]):
            idx += 1
            name = f"{base_name}_{idx:02d}"

        pos = [float(hit_point[0]), float(hit_point[1]), float(hit_point[2])]
        pose_data = {
            "pose_id": f"pose_{name}", "name": name,
            "translation": pos,
            "rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
            "linked_affordance_id": self.state.pose_aff_link if self.state.pose_aff_link != "(none)" else "",
            "linked_mask_id": self.state.pose_mask_link if self.state.pose_mask_link != "(none)" else "",
            "semantic_tags": [], "grasp_type": self.state.pose_grasp_type,
            "hand_role": self.state.pose_hand, "confidence": 1.0,
            "approved": False, "comment": "",
        }
        self.label["candidate_poses"].append(pose_data)

        # RGB 좌표축 마커
        self._create_pose_axes(name, pos, [0.0, 0.0, 0.0, 1.0])

        self.state.pose_text = self._fmt_poses()
        self._refresh_pose_select()
        self.ctrl.view_update()
        self.state.status_msg = f"Pose: {name} @ [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]"
        print(f"[pose] {name} at {pos}")

    # === Pose 회전 편집 ===
    def update_selected_pose_rotation(self):
        """선택된 pose의 rotation을 euler 슬라이더 값으로 갱신"""
        sel = self.state.pose_select
        if sel == "(none)":
            return
        pose = next((p for p in self.label["candidate_poses"] if p["name"] == sel), None)
        if pose is None:
            return
        roll = self.state.pose_roll
        pitch = self.state.pose_pitch
        yaw = self.state.pose_yaw
        rot = Rotation.from_euler("xyz", [roll, pitch, yaw], degrees=True)
        pose["rotation_xyzw"] = rot.as_quat().tolist()
        self._update_pose_axes(pose)
        self.ctrl.view_update()
        euler_str = f"[{roll:.0f}, {pitch:.0f}, {yaw:.0f}]°"
        self.state.status_msg = f"Pose '{sel}' rotation: {euler_str}"

    def on_pose_selected(self):
        """pose 선택 시 해당 pose의 euler 값을 슬라이더에 반영"""
        sel = self.state.pose_select
        if sel == "(none)":
            return
        pose = next((p for p in self.label["candidate_poses"] if p["name"] == sel), None)
        if pose is None:
            return
        euler = Rotation.from_quat(pose["rotation_xyzw"]).as_euler("xyz", degrees=True)
        self.state.pose_roll = float(round(euler[0], 1))
        self.state.pose_pitch = float(round(euler[1], 1))
        self.state.pose_yaw = float(round(euler[2], 1))
        self.state.status_msg = f"Selected: {sel}"

    def _refresh_pose_select(self):
        self.state.pose_select_options = ["(none)"] + [
            p["name"] for p in self.label.get("candidate_poses", [])
        ]

    # === Actions ===
    def toggle_paint(self, active):
        self.state.paint_active = active
        self.state.pose_place_mode = False
        if active:
            self.state.status_msg = f"Painting: '{self.state.current_part}' — 좌클릭=칠하기, 우클릭=지우기, Ctrl+드래그=orbit"
        else:
            self.state.status_msg = "orbit 모드"

    def toggle_pose_place(self):
        self.state.pose_place_mode = True
        self.state.paint_active = True
        self.state.status_msg = "Pose 배치 모드: 클릭=pose 생성, Ctrl+드래그=orbit | Stop으로 종료"

    def stop_pose_place(self):
        self.state.pose_place_mode = False
        self.state.paint_active = False
        self.state.status_msg = "Pose 배치 종료"

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
        self._refresh_parts_ui()
        self._refresh_dropdowns()
        self.state.status_msg = f"Part 추가: {name}"

    def clear_parts(self):
        self.label["parts"] = []
        if self.viewer.pv_mesh:
            self.viewer.pv_mesh.point_data["colors"] = np.full(
                (self.viewer.pv_mesh.n_points, 3), 180, dtype=np.uint8
            )
            self.ctrl.view_update()
        self._refresh_parts_ui()
        self._refresh_dropdowns()
        self.state.status_msg = "Parts 초기화"

    def rename_part(self):
        """선택된 part의 이름을 변경"""
        old_name = self.state.rename_from
        new_name = self.state.rename_to.strip()
        if old_name == "(none)" or not new_name:
            self.state.status_msg = "Rename: part와 새 이름을 입력하세요"
            return
        part = next((p for p in self.label["parts"] if p["name"] == old_name), None)
        if part is None:
            self.state.status_msg = f"Rename: '{old_name}' 없음"
            return
        if any(p["name"] == new_name for p in self.label["parts"]):
            self.state.status_msg = f"Rename: '{new_name}' 이미 존재"
            return
        # part 이름 + ID 변경
        old_id = part["part_id"]
        part["name"] = new_name
        part["part_id"] = f"part_{new_name}"
        part["color"] = [c / 255.0 for c in get_part_color(new_name)]
        # affordance, mask의 part_ref도 갱신
        for aff in self.label.get("affordances", []):
            if aff.get("part_ref") == old_id:
                aff["part_ref"] = part["part_id"]
        for mask in self.label.get("contact_region_masks", []):
            if mask.get("part_ref") == old_id:
                mask["part_ref"] = part["part_id"]
        self.viewer.update_colors(self.label)
        self.ctrl.view_update()
        self._refresh_parts_ui()
        self._refresh_dropdowns()
        self.state.status_msg = f"Renamed: {old_name} → {new_name}"

    def auto_segment(self):
        if self.viewer.tri_mesh is None:
            return
        parts = auto_segment_mug(self.viewer.tri_mesh)
        self._apply_segment_result(parts)
        self.state.status_msg = "Auto Segment 완료 (mug 전용)"

    def auto_segment_generic_action(self):
        """범용 기하학 기반 자동 분할 (K-means + 법선)"""
        if self.viewer.tri_mesh is None:
            return
        n_clusters = int(self.state.n_clusters)
        parts = auto_segment_generic(self.viewer.tri_mesh, n_clusters=n_clusters)
        self._apply_segment_result(parts)
        self.state.status_msg = f"Auto Segment 완료 (generic, {n_clusters} clusters)"

    def _refresh_parts_ui(self):
        """parts 텍스트 + legend 동시 갱신"""
        self.state.parts_text = self._fmt_parts()
        self._update_legend()

    def _update_legend(self):
        """3D 뷰포트에 part 색상 범례 표시"""
        if not self.label.get("parts"):
            try:
                self.plotter.remove_legend()
            except Exception:
                pass
            return
        labels = []
        for p in self.label["parts"]:
            c = get_part_color(p["name"])
            color = [c[0] / 255.0, c[1] / 255.0, c[2] / 255.0] if max(c[:3]) > 1 else list(c[:3])
            n = len(p.get("vertex_indices", []))
            labels.append([f"{p['name']} ({n}v)", color])
        if labels:
            self.plotter.add_legend(
                labels=labels,
                bcolor=(1, 1, 1),
                border=True,
                size=(0.2, 0.25),
                loc="upper left",
            )

    def _apply_segment_result(self, parts: dict):
        """분할 결과를 label에 적용 + 시각화"""
        self.label["parts"] = []
        for name, indices in parts.items():
            color = get_part_color(name)
            self.label["parts"].append({
                "part_id": f"part_{name}", "name": name,
                "vertex_indices": indices.tolist(), "face_indices": [],
                "visible": True, "color": [c / 255.0 for c in color], "comment": "",
                "source_type": "auto",
            })
        self.viewer.update_colors(self.label)
        self._update_legend()
        self.ctrl.view_update()
        self._refresh_parts_ui()
        self._refresh_dropdowns()

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

    def auto_split_patch(self):
        """선택한 part를 법선 방향 기반으로 Patch A/B 자동 분할"""
        target = self.state.mask_auto_split_part
        if target == "(none)":
            self.state.status_msg = "Auto Split: part를 선택하세요"
            return
        part = next((p for p in self.label["parts"] if p["name"] == target), None)
        if not part or not part.get("vertex_indices"):
            self.state.status_msg = f"Auto Split: '{target}' vertex 없음"
            return

        mesh = self.viewer.tri_mesh
        indices = np.array(part["vertex_indices"])
        verts = mesh.vertices[indices]

        # 법선 방향 기반 분할: PCA 첫 번째 주성분으로 양분
        centered = verts - verts.mean(axis=0)
        _, _, Vt = np.linalg.svd(centered, full_matrices=False)
        principal = Vt[0]  # 가장 큰 분산 방향
        projections = centered @ principal
        median_proj = np.median(projections)

        a_mask = projections <= median_proj
        b_mask = projections > median_proj

        a_indices = indices[a_mask].tolist()
        b_indices = indices[b_mask].tolist()

        mask_type = self.state.mask_type
        mask_id = f"mask_{mask_type}_{target}_auto"

        self.label["contact_region_masks"].append({
            "mask_id": mask_id, "mask_type": mask_type,
            "part_ref": part["part_id"],
            "patch_a": {"vertex_indices": a_indices, "face_indices": [], "finger_role": self.state.patch_a_role},
            "patch_b": {"vertex_indices": b_indices, "face_indices": [], "finger_role": self.state.patch_b_role},
            "comment": "auto_split (PCA)",
            "source_type": "auto",
        })
        self.viewer.update_colors(self.label)
        self.ctrl.view_update()
        self.state.mask_text = self._fmt_masks()
        self._refresh_dropdowns()
        self.state.status_msg = f"Auto Split: {target} → A({len(a_indices)}v) / B({len(b_indices)}v)"

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

    def remove_last_pose(self):
        if self.label["candidate_poses"]:
            removed = self.label["candidate_poses"].pop()
            self._remove_pose_axes(removed["name"])
            self.ctrl.view_update()
            self.state.pose_text = self._fmt_poses()
            self._refresh_pose_select()
            self.state.status_msg = f"Removed: {removed['pose_id']}"
        else:
            self.state.status_msg = "삭제할 pose 없음"

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
            self._refresh_parts_ui()
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
        def _p(p):
            src = "🤖" if p.get("source_type") == "auto" else "✋"
            return f"{src}{p['name']}({len(p.get('vertex_indices',[]))}v)"
        return " | ".join(_p(p) for p in self.label["parts"])

    def _fmt_affs(self):
        if not self.label.get("affordances"):
            return "No affordances"
        return " | ".join(f"{a['label']}→{a.get('part_ref','?')}" for a in self.label["affordances"])

    def _fmt_masks(self):
        if not self.label.get("contact_region_masks"):
            return "No masks"
        def _m(m):
            src = "🤖" if m.get("source_type") == "auto" else ""
            return f"{src}{m['mask_type']}"
        return " | ".join(_m(m) for m in self.label["contact_region_masks"])

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
        self.state.mask_auto_split_part = "(none)"
        self.state.patch_a_role = "thumb"
        self.state.patch_b_role = "index_middle"
        self.state.pose_name = "grasp_01"
        self.state.pose_grasp_type = "pinch"
        self.state.pose_hand = "right"
        self.state.pose_aff_link = "(none)"
        self.state.pose_mask_link = "(none)"
        self.state.pose_select = "(none)"
        self.state.pose_select_options = ["(none)"]
        self.state.pose_roll = 0
        self.state.pose_pitch = 0
        self.state.pose_yaw = 0
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
                        vuetify3.VBtn("Auto Semantic Segment (mug)", click=self.auto_segment, color="purple", size="small", block=True, class_="mx-2")
                        vuetify3.VSlider(v_model=("n_clusters", 4), label="Clusters", min=2, max=8, step=1, hide_details=True, class_="mx-2")
                        vuetify3.VBtn("Auto Geometric Segment", click=self.auto_segment_generic_action, color="teal", size="small", block=True, class_="mx-2")
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
                        vuetify3.VCardSubtitle("Rename Part", class_="pa-1 mt-1")
                        with vuetify3.VRow(class_="mx-1", no_gutters=True):
                            with vuetify3.VCol(cols=5):
                                vuetify3.VSelect(v_model=("rename_from",), label="From", items=("part_options",), density="compact", hide_details=True)
                            with vuetify3.VCol(cols=5):
                                vuetify3.VTextField(v_model=("rename_to",), label="To", density="compact", hide_details=True)
                            with vuetify3.VCol(cols=2):
                                vuetify3.VBtn("OK", click=self.rename_part, size="x-small", block=True)
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
                        vuetify3.VCardSubtitle("Auto Split (PCA)", class_="pa-1 mt-1")
                        vuetify3.VSelect(v_model=("mask_auto_split_part",), label="Split Part", items=("part_options",), density="compact", class_="mx-2", hide_details=True)
                        vuetify3.VBtn("Auto Split → A/B", click=self.auto_split_patch, color="teal", size="small", block=True, class_="mx-2 mt-1")
                        vuetify3.VCardText("{{ mask_text }}", class_="text-caption pa-1")

                        vuetify3.VDivider(class_="my-2")

                        # --- Poses ---
                        vuetify3.VCardTitle("Poses", class_="text-subtitle-2 pa-1")
                        vuetify3.VTextField(v_model=("pose_name",), label="Name", density="compact", class_="mx-2", hide_details=True)
                        vuetify3.VSelect(v_model=("pose_grasp_type",), label="Grasp", items=("['pinch','power','lateral','hook','precision','custom']",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VSelect(v_model=("pose_hand",), label="Hand", items=("['left','right','either']",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VSelect(v_model=("pose_aff_link",), label="Link Aff", items=("aff_link_options",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        vuetify3.VSelect(v_model=("pose_mask_link",), label="Link Mask", items=("mask_link_options",), density="compact", class_="mx-2 mt-1", hide_details=True)
                        with vuetify3.VRow(class_="mx-1 mt-1", no_gutters=True):
                            with vuetify3.VCol(cols=8):
                                vuetify3.VBtn("Place Pose", click=self.toggle_pose_place, color="orange", size="small", block=True)
                            with vuetify3.VCol(cols=4):
                                vuetify3.VBtn("Stop", click=self.stop_pose_place, color="red", size="small", block=True)
                        vuetify3.VBtn("Remove Last", click=self.remove_last_pose, size="x-small", block=True, class_="mx-2 mt-1")

                        # --- Pose 회전 편집 ---
                        vuetify3.VCardSubtitle("Rotation 편집", class_="pa-1 mt-2")
                        vuetify3.VSelect(
                            v_model=("pose_select",), label="Select Pose",
                            items=("pose_select_options",),
                            density="compact", class_="mx-2", hide_details=True,
                            update_modelValue=(self.on_pose_selected, "[]"),
                        )
                        vuetify3.VSlider(
                            v_model=("pose_roll", 0), label="Roll",
                            min=-180, max=180, step=5,
                            hide_details=True, class_="mx-2",
                            update_modelValue=(self.update_selected_pose_rotation, "[]"),
                        )
                        vuetify3.VSlider(
                            v_model=("pose_pitch", 0), label="Pitch",
                            min=-180, max=180, step=5,
                            hide_details=True, class_="mx-2",
                            update_modelValue=(self.update_selected_pose_rotation, "[]"),
                        )
                        vuetify3.VSlider(
                            v_model=("pose_yaw", 0), label="Yaw",
                            min=-180, max=180, step=5,
                            hide_details=True, class_="mx-2",
                            update_modelValue=(self.update_selected_pose_rotation, "[]"),
                        )

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
