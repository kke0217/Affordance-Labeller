"""
viewer.py — Viser 기반 3D 뷰어 래퍼

역할:
- 3D mesh / point cloud를 Viser scene에 렌더링
- 파트별 색상 오버레이
- canonical frame 표시
- 기본 인터랙션 (회전, 줌)
"""

import numpy as np
from pathlib import Path
from typing import Optional

try:
    import viser
    import viser.transforms as tf
except ImportError:
    print("[viewer] viser가 설치되지 않았습니다. pip install viser")
    raise

try:
    import trimesh
except ImportError:
    print("[viewer] trimesh가 설치되지 않았습니다. pip install trimesh")
    raise


# 파트별 기본 색상 (RGBA, 0~255)
PART_COLORS = {
    "body":     (150, 150, 200, 200),
    "handle":   (50, 200, 50, 200),
    "rim":      (200, 200, 50, 200),
    "interior": (200, 100, 50, 200),
    "base":     (100, 100, 100, 200),
    "other":    (180, 180, 180, 200),
}

# Affordance별 색상
AFFORDANCE_COLORS = {
    "graspable":       (0, 255, 0, 180),
    "pour_support":    (0, 100, 255, 180),
    "handover_region": (255, 165, 0, 180),
    "placeable":       (128, 0, 128, 180),
    "non_affordance":  (128, 128, 128, 100),
}


class MeshViewer:
    """Viser 기반 3D 메시 뷰어"""

    def __init__(self, server: "viser.ViserServer"):
        self.server = server
        self.loaded_mesh: Optional[trimesh.Trimesh] = None
        self.mesh_handle = None
        self.frame_handles = {}
        self.part_handles = {}
        self.pose_handles = {}

    def load_mesh(self, mesh_path: str) -> bool:
        """3D 메시 파일 로드

        지원 포맷: .obj, .ply, .stl, .off, .glb, .gltf
        """
        mesh_path = Path(mesh_path)
        if not mesh_path.exists():
            print(f"[viewer] 파일을 찾을 수 없습니다: {mesh_path}")
            return False

        try:
            loaded = trimesh.load(str(mesh_path))

            # Scene인 경우 단일 mesh로 병합
            if isinstance(loaded, trimesh.Scene):
                self.loaded_mesh = loaded.dump(concatenate=True)
            else:
                self.loaded_mesh = loaded

            print(f"[viewer] 메시 로드 완료: {mesh_path.name}")
            print(f"  정점: {len(self.loaded_mesh.vertices)}")
            print(f"  면: {len(self.loaded_mesh.faces)}")
            return True

        except Exception as e:
            print(f"[viewer] 메시 로드 실패: {e}")
            return False

    def display_mesh(self, name: str = "object"):
        """로드된 메시를 Viser scene에 표시"""
        if self.loaded_mesh is None:
            print("[viewer] 표시할 메시가 없습니다. load_mesh()를 먼저 호출하세요.")
            return

        mesh = self.loaded_mesh

        # 정점 색상: ColorVisuals가 아니면 기본 회색 사용
        if hasattr(mesh.visual, 'vertex_colors') and mesh.visual.vertex_colors is not None:
            vertex_colors = np.array(mesh.visual.vertex_colors, dtype=np.uint8)
        else:
            vertex_colors = np.full((len(mesh.vertices), 4), 180, dtype=np.uint8)
            vertex_colors[:, 3] = 255

        # Viser에 메시 추가
        self.mesh_handle = self.server.scene.add_mesh_simple(
            name=f"/object/{name}",
            vertices=mesh.vertices.astype(np.float32),
            faces=mesh.faces.astype(np.uint32),
            color=(180, 180, 180),
            wireframe=False,
        )
        print(f"[viewer] 메시 표시: /object/{name}")

    def display_canonical_frame(self, canonical_frame: dict, scale: float = 0.1):
        """정규 좌표계 프레임 표시"""
        origin = np.array(canonical_frame.get("origin", [0, 0, 0]), dtype=np.float32)

        self.frame_handles["canonical"] = self.server.scene.add_frame(
            name="/canonical_frame",
            wxyz=tf.SO3.identity().wxyz,
            position=origin,
            axes_length=scale,
            axes_radius=scale * 0.05,
        )
        print("[viewer] canonical frame 표시")

    def display_pose(self, pose_data: dict, scale: float = 0.08):
        """6D candidate pose를 좌표축으로 표시"""
        pose_id = pose_data.get("pose_id", "unknown")
        translation = np.array(pose_data["translation"], dtype=np.float32)
        rotation_xyzw = np.array(pose_data["rotation_xyzw"], dtype=np.float32)

        # xyzw → wxyz 변환 (Viser 형식)
        wxyz = np.array([
            rotation_xyzw[3],
            rotation_xyzw[0],
            rotation_xyzw[1],
            rotation_xyzw[2],
        ])

        handle = self.server.scene.add_frame(
            name=f"/poses/{pose_id}",
            wxyz=wxyz,
            position=translation,
            axes_length=scale,
            axes_radius=scale * 0.08,
        )

        # 라벨 추가
        self.server.scene.add_label(
            name=f"/poses/{pose_id}/label",
            text=pose_data.get("name", pose_id),
            wxyz=wxyz,
            position=translation + np.array([0, 0, scale * 1.5]),
        )

        self.pose_handles[pose_id] = handle
        print(f"[viewer] pose 표시: {pose_id}")

    def clear_poses(self):
        """모든 pose 시각화 제거"""
        for pose_id, handle in self.pose_handles.items():
            handle.remove()
        self.pose_handles.clear()

    def clear_all(self):
        """모든 시각화 제거"""
        if self.mesh_handle:
            self.mesh_handle.remove()
            self.mesh_handle = None
        for handle in self.frame_handles.values():
            handle.remove()
        self.frame_handles.clear()
        self.clear_poses()
        for handle in self.part_handles.values():
            handle.remove()
        self.part_handles.clear()
