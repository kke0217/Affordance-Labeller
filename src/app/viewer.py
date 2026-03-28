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

# 커스텀 part 이름용 색상 팔레트 (순환 사용)
CUSTOM_PART_COLORS = [
    (255, 100, 100, 220),   # 빨강
    (100, 255, 100, 220),   # 초록
    (100, 100, 255, 220),   # 파랑
    (255, 200, 50, 220),    # 노랑
    (255, 100, 255, 220),   # 마젠타
    (100, 255, 255, 220),   # 시안
    (255, 160, 50, 220),    # 주황
    (160, 100, 255, 220),   # 보라
]

_custom_color_index = {}

def get_part_color(name: str) -> tuple:
    """part 이름에 맞는 색상 반환. 미리 정의된 이름이 없으면 팔레트에서 순환 할당"""
    if name in PART_COLORS:
        return PART_COLORS[name]
    if name not in _custom_color_index:
        _custom_color_index[name] = len(_custom_color_index) % len(CUSTOM_PART_COLORS)
    return CUSTOM_PART_COLORS[_custom_color_index[name]]

def auto_segment_generic(mesh: trimesh.Trimesh, n_clusters: int = 4) -> dict[str, np.ndarray]:
    """범용 기하학 기반 자동 part 분류 (K-means + 법선 방향)

    vertex 위치와 법선 벡터를 결합하여 K-means 클러스터링을 수행한다.
    mug 이외 임의 객체에 사용 가능.

    Args:
        mesh: trimesh 메시
        n_clusters: 분할할 part 수 (기본 4)

    Returns:
        part_name → vertex_indices 배열 딕셔너리
    """
    from sklearn.cluster import KMeans

    verts = mesh.vertices
    # 법선 벡터 계산
    if mesh.vertex_normals is not None and len(mesh.vertex_normals) == len(verts):
        normals = mesh.vertex_normals
    else:
        normals = np.zeros_like(verts)

    # vertex 위치 + 법선을 결합한 feature (위치 0.7 + 법선 0.3 가중)
    pos_norm = (verts - verts.mean(axis=0)) / (verts.std() + 1e-8)
    norm_norm = normals / (np.linalg.norm(normals, axis=1, keepdims=True) + 1e-8)
    features = np.hstack([pos_norm * 0.7, norm_norm * 0.3])

    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    labels = kmeans.fit_predict(features)

    part_names = [f"region_{i}" for i in range(n_clusters)]
    parts = {}
    for i, name in enumerate(part_names):
        indices = np.where(labels == i)[0]
        parts[name] = indices
        print(f"  [auto] {name}: {len(indices)} vertices")

    return parts


# Affordance별 색상
AFFORDANCE_COLORS = {
    "graspable":       (0, 255, 0, 180),
    "pour_support":    (0, 100, 255, 180),
    "handover_region": (255, 165, 0, 180),
    "placeable":       (128, 0, 128, 180),
    "non_affordance":  (128, 128, 128, 100),
}


def auto_segment_mug(
    mesh: trimesh.Trimesh,
    handle_ratio: float = 1.3,
    rim_ratio: float = 0.06,
    base_ratio: float = 0.03,
) -> dict[str, np.ndarray]:
    """YCB mug 기하학 기반 자동 part 분류

    원통형 body에서 돌출된 handle, 상단 rim, 하단 base를 분리한다.

    Args:
        handle_ratio: body 반지름 대비 handle 판정 배수 (기본 1.3)
        rim_ratio: Z축 상위 비율 → rim (기본 0.06 = 6%)
        base_ratio: Z축 하위 비율 → base (기본 0.03 = 3%)

    Returns:
        part_name → vertex_indices 배열 딕셔너리
    """
    verts = mesh.vertices
    n = len(verts)

    # 바운딩 박스 기준값
    z_min, z_max = verts[:, 2].min(), verts[:, 2].max()
    z_range = z_max - z_min

    # 중심축 (body 원통의 XY 중심)
    x_center = verts[:, 0].mean()
    y_center = verts[:, 1].mean()
    dist_xy = np.sqrt((verts[:, 0] - x_center) ** 2 + (verts[:, 1] - y_center) ** 2)

    # body 반지름 추정 (XY 거리 중앙값)
    body_radius = np.median(dist_xy)

    # 분류 기준 (파라미터로 조정 가능)
    handle_threshold = body_radius * handle_ratio
    rim_z = z_max - z_range * rim_ratio
    base_z = z_min + z_range * base_ratio

    # 분류
    is_handle = dist_xy > handle_threshold
    is_rim = (verts[:, 2] > rim_z) & ~is_handle
    is_base = (verts[:, 2] < base_z) & ~is_handle
    is_body = ~is_handle & ~is_rim & ~is_base

    parts = {
        "body": np.where(is_body)[0],
        "handle": np.where(is_handle)[0],
        "rim": np.where(is_rim)[0],
        "base": np.where(is_base)[0],
    }

    for name, indices in parts.items():
        print(f"  [part] {name}: {len(indices)} vertices")

    return parts


class MeshViewer:
    """Viser 기반 3D 메시 뷰어"""

    def __init__(self, server: "viser.ViserServer"):
        self.server = server
        self.loaded_mesh: Optional[trimesh.Trimesh] = None
        self.mesh_handle = None
        self.frame_handles = {}
        self.part_handles = {}
        self.pose_handles = {}
        self.part_vertex_indices: dict[str, np.ndarray] = {}

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
        """로드된 메시를 Viser scene에 표시 (add_mesh_trimesh 사용)"""
        if self.loaded_mesh is None:
            print("[viewer] 표시할 메시가 없습니다. load_mesh()를 먼저 호출하세요.")
            return

        mesh = self.loaded_mesh

        # TextureVisuals → ColorVisuals 변환 (기본 회색)
        if not hasattr(mesh.visual, 'vertex_colors'):
            mesh.visual = trimesh.visual.ColorVisuals(
                mesh=mesh,
                vertex_colors=np.full((len(mesh.vertices), 4), [180, 180, 180, 255], dtype=np.uint8),
            )

        # Viser에 trimesh 객체 직접 전달
        self.mesh_handle = self.server.scene.add_mesh_trimesh(
            name=f"/object/{name}",
            mesh=mesh,
        )
        print(f"[viewer] 메시 표시: /object/{name}")

    def apply_part_colors(self, part_vertex_indices: dict[str, np.ndarray]):
        """part별 vertex color를 적용하여 메시 재표시"""
        if self.loaded_mesh is None:
            return

        self.part_vertex_indices = part_vertex_indices
        mesh = self.loaded_mesh
        colors = np.full((len(mesh.vertices), 4), [180, 180, 180, 255], dtype=np.uint8)

        for part_name, indices in part_vertex_indices.items():
            color = get_part_color(part_name)
            colors[indices] = color

        mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh, vertex_colors=colors)

        # 기존 메시 제거 후 재표시
        if self.mesh_handle:
            self.mesh_handle.remove()
        self.mesh_handle = self.server.scene.add_mesh_trimesh(
            name="/object/mesh",
            mesh=mesh,
        )
        print("[viewer] part 색상 오버레이 적용")

    def generate_parts_data(self, part_vertex_indices: dict[str, np.ndarray]) -> list[dict]:
        """part_vertex_indices를 JSON parts 리스트로 변환"""
        parts = []
        for name, indices in part_vertex_indices.items():
            color = get_part_color(name)
            parts.append({
                "part_id": f"part_{name}",
                "name": name,
                "vertex_indices": indices.tolist(),
                "face_indices": [],
                "visible": True,
                "color": [c / 255.0 for c in color],
                "comment": "",
            })
        return parts

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
