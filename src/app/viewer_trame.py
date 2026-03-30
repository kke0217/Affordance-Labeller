"""
viewer_trame.py — PyVista 기반 mesh 관리 + 색상 갱신
"""

from pathlib import Path

import numpy as np
import pyvista as pv
import trimesh

from viewer import get_part_color, AFFORDANCE_COLORS


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
        # mask별 다른 색상 쌍 (A/B)
        MASK_COLOR_PAIRS = [
            ([255, 0, 128], [0, 220, 220]),     # 핫핑크 / 시안
            ([255, 200, 0], [100, 0, 200]),      # 금색 / 보라
            ([0, 200, 100], [200, 0, 80]),        # 에메랄드 / 크림슨
            ([255, 128, 0], [0, 128, 255]),       # 주황 / 코발트
        ]
        for mi, mask in enumerate(label.get("contact_region_masks", [])):
            pair = MASK_COLOR_PAIRS[mi % len(MASK_COLOR_PAIRS)]
            a_idx = mask.get("patch_a", {}).get("vertex_indices", [])
            b_idx = mask.get("patch_b", {}).get("vertex_indices", [])
            if a_idx:
                colors[a_idx] = pair[0]
            if b_idx:
                colors[b_idx] = pair[1]
        self.pv_mesh.point_data["colors"] = colors
