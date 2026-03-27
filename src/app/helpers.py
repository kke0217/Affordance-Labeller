"""
helpers.py — 포맷 헬퍼 + 색상 오버레이 헬퍼
"""

import numpy as np
import trimesh

from state import AppState
from viewer import PART_COLORS, AFFORDANCE_COLORS


# ============================================================
# 포맷 헬퍼
# ============================================================
def format_parts(parts: list) -> str:
    if not parts:
        return "*No parts defined*"
    return "\n".join(
        f"- **{p['name']}** ({p['part_id']}) — {len(p.get('vertex_indices', []))} vertices"
        for p in parts
    )


def format_affordances(affordances: list) -> str:
    if not affordances:
        return "*No affordances defined*"
    return "\n".join(
        f"- **{a['label']}** → {a.get('part_ref', '?')} [{', '.join(a.get('semantic_tags', []))}]"
        for a in affordances
    )


def format_masks(masks: list) -> str:
    if not masks:
        return "*No contact masks defined*"
    lines = []
    for m in masks:
        a_count = len(m.get("patch_a", {}).get("vertex_indices", []))
        b_count = len(m.get("patch_b", {}).get("vertex_indices", []))
        a_role = m.get("patch_a", {}).get("finger_role", "?")
        b_role = m.get("patch_b", {}).get("finger_role", "?")
        lines.append(
            f"- **{m['mask_type']}** → {m.get('part_ref', '?')} "
            f"[A:{a_role}({a_count}v) / B:{b_role}({b_count}v)]"
        )
    return "\n".join(lines)


def format_poses(poses: list) -> str:
    if not poses:
        return "*No poses defined*"
    lines = []
    for p in poses:
        pos = p.get("translation", [0, 0, 0])
        rot = p.get("rotation_xyzw", [0, 0, 0, 1])
        is_identity = rot == [0.0, 0.0, 0.0, 1.0]
        rot_str = "" if is_identity else f" rot[{rot[0]:.2f},{rot[1]:.2f},{rot[2]:.2f},{rot[3]:.2f}]"
        lines.append(
            f"- **{p['name']}** ({p.get('grasp_type', '?')}) "
            f"@ [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]{rot_str}"
        )
    return "\n".join(lines)


# ============================================================
# 색상 오버레이 헬퍼
# ============================================================
PATCH_A_COLOR = (255, 80, 80, 220)
PATCH_B_COLOR = (80, 80, 255, 220)


def apply_affordance_overlay(state: AppState):
    """part + affordance 색상 오버레이 적용"""
    if state.viewer.loaded_mesh is None:
        return
    mesh = state.viewer.loaded_mesh
    colors = np.full((len(mesh.vertices), 4), [180, 180, 180, 255], dtype=np.uint8)
    for part in state.label.get("parts", []):
        indices = part.get("vertex_indices", [])
        if indices:
            colors[indices] = PART_COLORS.get(part["name"], PART_COLORS["other"])
    for aff in state.label.get("affordances", []):
        indices = aff.get("vertex_indices", [])
        if indices:
            colors[indices] = AFFORDANCE_COLORS.get(aff["label"], (128, 128, 128, 100))
    mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh, vertex_colors=colors)
    if state.viewer.mesh_handle:
        state.viewer.mesh_handle.remove()
    state.viewer.mesh_handle = state.server.scene.add_mesh_trimesh(
        name="/object/mug", mesh=mesh,
    )


def apply_mask_overlay(state: AppState):
    """contact mask patch A/B 색상 오버레이"""
    if state.viewer.loaded_mesh is None:
        return
    apply_affordance_overlay(state)
    mesh = state.viewer.loaded_mesh
    colors = np.array(mesh.visual.vertex_colors, dtype=np.uint8)
    for mask in state.label.get("contact_region_masks", []):
        a_indices = mask.get("patch_a", {}).get("vertex_indices", [])
        b_indices = mask.get("patch_b", {}).get("vertex_indices", [])
        if a_indices:
            colors[a_indices] = PATCH_A_COLOR
        if b_indices:
            colors[b_indices] = PATCH_B_COLOR
    mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh, vertex_colors=colors)
    if state.viewer.mesh_handle:
        state.viewer.mesh_handle.remove()
    state.viewer.mesh_handle = state.server.scene.add_mesh_trimesh(
        name="/object/mug", mesh=mesh,
    )
