"""
viewer.py — 공용 유틸리티: 색상 팔레트 + 자동 분할

Part/Affordance 색상 정의, 커스텀 팔레트, auto segment 함수 제공.
UI 프레임워크(Trame)에 독립적인 로직만 포함.
"""

import numpy as np
import trimesh


# ============================================================
# Part 색상 팔레트
# ============================================================
PART_COLORS = {
    "body":     (150, 150, 200, 200),
    "handle":   (50, 200, 50, 200),
    "rim":      (200, 200, 50, 200),
    "interior": (200, 100, 50, 200),
    "base":     (100, 100, 100, 200),
    "other":    (180, 180, 180, 200),
}

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


# ============================================================
# Affordance 색상
# ============================================================
AFFORDANCE_COLORS = {
    "graspable":       (0, 255, 0, 180),
    "pour_support":    (0, 100, 255, 180),
    "handover_region": (255, 165, 0, 180),
    "placeable":       (128, 0, 128, 180),
    "non_affordance":  (128, 128, 128, 100),
}


# ============================================================
# Auto Segment: 범용 (K-means + 법선)
# ============================================================
def auto_segment_generic(mesh: trimesh.Trimesh, n_clusters: int = 4) -> dict[str, np.ndarray]:
    """범용 기하학 기반 자동 part 분류 (K-means + 법선 방향)

    Args:
        mesh: trimesh 메시
        n_clusters: 분할할 part 수 (기본 4)

    Returns:
        part_name → vertex_indices 배열 딕셔너리
    """
    from sklearn.cluster import KMeans

    verts = mesh.vertices
    if mesh.vertex_normals is not None and len(mesh.vertex_normals) == len(verts):
        normals = mesh.vertex_normals
    else:
        normals = np.zeros_like(verts)

    pos_norm = (verts - verts.mean(axis=0)) / (verts.std() + 1e-8)
    norm_norm = normals / (np.linalg.norm(normals, axis=1, keepdims=True) + 1e-8)
    features = np.hstack([pos_norm * 0.7, norm_norm * 0.3])

    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    labels = kmeans.fit_predict(features)

    parts = {}
    for i in range(n_clusters):
        name = f"region_{i}"
        indices = np.where(labels == i)[0]
        parts[name] = indices
        print(f"  [auto] {name}: {len(indices)} vertices")

    return parts


# ============================================================
# Auto Segment: Mug 전용 (기하학 heuristic)
# ============================================================
def auto_segment_mug(
    mesh: trimesh.Trimesh,
    handle_ratio: float = 1.3,
    rim_ratio: float = 0.06,
    base_ratio: float = 0.03,
) -> dict[str, np.ndarray]:
    """YCB mug 기하학 기반 자동 part 분류

    Args:
        handle_ratio: body 반지름 대비 handle 판정 배수
        rim_ratio: Z축 상위 비율 → rim
        base_ratio: Z축 하위 비율 → base

    Returns:
        part_name → vertex_indices 배열 딕셔너리
    """
    verts = mesh.vertices

    z_min, z_max = verts[:, 2].min(), verts[:, 2].max()
    z_range = z_max - z_min

    x_center = verts[:, 0].mean()
    y_center = verts[:, 1].mean()
    dist_xy = np.sqrt((verts[:, 0] - x_center) ** 2 + (verts[:, 1] - y_center) ** 2)

    body_radius = np.median(dist_xy)

    handle_threshold = body_radius * handle_ratio
    rim_z = z_max - z_range * rim_ratio
    base_z = z_min + z_range * base_ratio

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
