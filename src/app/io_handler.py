"""
io_handler.py — JSON 저장/로드 및 검증 모듈

역할:
- affordance label JSON 저장 (save_label)
- affordance label JSON 로드 (load_label)
- 필수 필드 검증 (validate_label)
- 빈 라벨 템플릿 생성 (create_empty_label)
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import jsonschema

# JSON 스키마 위치
SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "label_v0.1.json"
LABELS_DIR = Path(__file__).parent.parent / "labels"


def create_empty_label(
    object_id: str,
    input_type: str = "mesh",
    annotator: str = "unknown",
) -> dict:
    """빈 라벨 템플릿 생성

    Args:
        object_id: 객체 ID (예: ycb_025_mug)
        input_type: 입력 유형 (mesh, pointcloud, rgbd 등)
        annotator: 작성자 이름

    Returns:
        기본값이 채워진 라벨 딕셔너리
    """
    now = datetime.now(timezone.utc).isoformat()

    return {
        "schema_version": "0.1",
        "object_id": object_id,
        "asset_version": "",
        "input_type": input_type,
        "input_file": "",
        "canonical_frame": {
            "origin": [0.0, 0.0, 0.0],
            "axis_x": [1.0, 0.0, 0.0],
            "axis_y": [0.0, 1.0, 0.0],
            "axis_z": [0.0, 0.0, 1.0],
        },
        "parts": [],
        "affordances": [],
        "contact_region_masks": [],
        "candidate_poses": [],
        "annotator": annotator,
        "review_status": "draft",
        "updated_at": now,
    }


def _extract_vertices_to_npy(label_data: dict, npy_dir: Path) -> dict:
    """vertex_indices 배열을 .npy 파일로 분리하고 참조로 치환한 사본을 반환"""
    import copy
    data = copy.deepcopy(label_data)
    npy_dir.mkdir(parents=True, exist_ok=True)

    def _save_array(key_prefix: str, indices: list) -> str:
        """배열을 .npy로 저장하고 상대 경로 반환"""
        filename = f"{key_prefix}.npy"
        np.save(str(npy_dir / filename), np.array(indices, dtype=np.int32))
        return f"{npy_dir.name}/{filename}"

    # parts
    for part in data.get("parts", []):
        vi = part.get("vertex_indices", [])
        if vi:
            part["vertex_indices_file"] = _save_array(part["part_id"], vi)
            part["vertex_indices"] = []

    # affordances
    for aff in data.get("affordances", []):
        vi = aff.get("vertex_indices", [])
        if vi:
            aff["vertex_indices_file"] = _save_array(aff["affordance_id"], vi)
            aff["vertex_indices"] = []

    # contact_region_masks
    for mask in data.get("contact_region_masks", []):
        for patch_key in ("patch_a", "patch_b"):
            patch = mask.get(patch_key, {})
            vi = patch.get("vertex_indices", [])
            if vi:
                patch["vertex_indices_file"] = _save_array(
                    f"{mask['mask_id']}_{patch_key}", vi
                )
                patch["vertex_indices"] = []

    return data


def save_label(label_data: dict, filepath: Optional[str] = None) -> str:
    """라벨 데이터를 JSON + .npy 파일로 저장

    vertex_indices는 .npy 바이너리로 분리하여 JSON 크기를 줄인다.

    Args:
        label_data: 라벨 딕셔너리
        filepath: 저장 경로 (None이면 자동 생성)

    Returns:
        저장된 파일 경로
    """
    # updated_at 갱신
    label_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # 파일 경로 결정
    if filepath is None:
        LABELS_DIR.mkdir(parents=True, exist_ok=True)
        object_id = label_data.get("object_id", "unknown")
        filepath = str(LABELS_DIR / f"{object_id}.json")

    # 디렉토리 확인
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

    # vertex_indices를 .npy로 분리
    json_path = Path(filepath)
    npy_dir = json_path.parent / f"{json_path.stem}_vertices"
    save_data = _extract_vertices_to_npy(label_data, npy_dir)

    # JSON 저장 (vertex_indices가 빈 배열 + _file 참조)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)

    print(f"[save] 저장 완료: {filepath} + {npy_dir.name}/")
    return filepath


def _restore_vertices_from_npy(data: dict, base_dir: Path) -> dict:
    """vertex_indices_file 참조를 .npy에서 읽어 vertex_indices로 복원"""

    def _load_array(ref_path: str) -> list:
        full_path = base_dir / ref_path
        if full_path.exists():
            return np.load(str(full_path)).tolist()
        print(f"[load] .npy 파일 없음: {full_path}")
        return []

    for part in data.get("parts", []):
        if "vertex_indices_file" in part:
            part["vertex_indices"] = _load_array(part.pop("vertex_indices_file"))

    for aff in data.get("affordances", []):
        if "vertex_indices_file" in aff:
            aff["vertex_indices"] = _load_array(aff.pop("vertex_indices_file"))

    for mask in data.get("contact_region_masks", []):
        for patch_key in ("patch_a", "patch_b"):
            patch = mask.get(patch_key, {})
            if "vertex_indices_file" in patch:
                patch["vertex_indices"] = _load_array(patch.pop("vertex_indices_file"))

    return data


def load_label(filepath: str) -> dict:
    """JSON + .npy 파일에서 라벨 데이터 로드

    vertex_indices_file 참조가 있으면 .npy에서 복원한다.
    참조가 없으면 기존 인라인 방식으로 동작한다 (하위 호환).

    Args:
        filepath: JSON 파일 경로

    Returns:
        라벨 딕셔너리

    Raises:
        FileNotFoundError: 파일이 없는 경우
        json.JSONDecodeError: JSON 파싱 실패
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"라벨 파일을 찾을 수 없습니다: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # .npy 참조 복원
    base_dir = Path(filepath).parent
    data = _restore_vertices_from_npy(data, base_dir)

    print(f"[load] 로드 완료: {filepath}")
    return data


def _load_schema() -> dict | None:
    """JSON 스키마 파일 로드 (캐싱)"""
    if not SCHEMA_PATH.exists():
        print(f"[validate] 스키마 파일 없음: {SCHEMA_PATH}")
        return None
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_label(label_data: dict) -> list[dict]:
    """라벨 데이터 검증 (jsonschema + 비즈니스 로직)

    Args:
        label_data: 라벨 딕셔너리

    Returns:
        경고/오류 리스트. 각 항목은 {"level": "error"|"warning", "message": str}
    """
    issues = []

    # === 1단계: JSON Schema 검증 ===
    schema = _load_schema()
    if schema:
        validator = jsonschema.Draft7Validator(schema)
        for error in validator.iter_errors(label_data):
            path = ".".join(str(p) for p in error.absolute_path) or "(root)"
            issues.append({
                "level": "error",
                "field": path,
                "message": f"스키마 위반 [{path}]: {error.message}",
            })
        if issues:
            return issues

    # === 2단계: 필수 필드 존재 확인 (스키마 없을 때 fallback) ===
    required_fields = [
        "schema_version", "object_id", "input_type",
        "canonical_frame", "parts", "affordances",
        "annotator", "review_status", "updated_at"
    ]

    for field in required_fields:
        if field not in label_data:
            issues.append({
                "level": "error",
                "field": field,
                "message": f"필수 필드 누락: {field}",
            })

    if any(i["level"] == "error" for i in issues):
        return issues

    # === 3단계: 스키마 버전 확인 ===
    if label_data.get("schema_version") != "0.1":
        issues.append({
            "level": "warning",
            "field": "schema_version",
            "message": f"스키마 버전 불일치: {label_data.get('schema_version')} (기대: 0.1)",
        })

    # === parts 검증 ===
    if len(label_data.get("parts", [])) == 0:
        issues.append({
            "level": "warning",
            "field": "parts",
            "message": "parts가 비어있습니다. 최소 1개 파트를 정의하세요.",
        })

    part_ids = {p["part_id"] for p in label_data.get("parts", []) if "part_id" in p}

    # === affordances 검증 ===
    for aff in label_data.get("affordances", []):
        if aff.get("part_ref") and aff["part_ref"] not in part_ids:
            issues.append({
                "level": "error",
                "field": "affordances",
                "message": f"affordance '{aff.get('affordance_id')}' "
                           f"참조하는 part_ref '{aff['part_ref']}'가 존재하지 않습니다.",
            })

        if not aff.get("semantic_tags"):
            issues.append({
                "level": "warning",
                "field": "affordances",
                "message": f"affordance '{aff.get('affordance_id')}'에 semantic_tags가 없습니다.",
            })

    # === contact mask 검증 ===
    affordance_ids = {
        a["affordance_id"] for a in label_data.get("affordances", [])
        if "affordance_id" in a
    }

    for mask in label_data.get("contact_region_masks", []):
        if mask.get("part_ref") and mask["part_ref"] not in part_ids:
            issues.append({
                "level": "error",
                "field": "contact_region_masks",
                "message": f"mask '{mask.get('mask_id')}' 참조하는 part_ref가 존재하지 않습니다.",
            })

    # === candidate poses 검증 ===
    mask_ids = {
        m["mask_id"] for m in label_data.get("contact_region_masks", [])
        if "mask_id" in m
    }

    for pose in label_data.get("candidate_poses", []):
        if pose.get("linked_affordance_id") and \
           pose["linked_affordance_id"] not in affordance_ids:
            issues.append({
                "level": "warning",
                "field": "candidate_poses",
                "message": f"pose '{pose.get('pose_id')}' "
                           f"연결된 affordance '{pose['linked_affordance_id']}'가 없습니다.",
            })

        if pose.get("linked_mask_id") and \
           pose["linked_mask_id"] not in mask_ids:
            issues.append({
                "level": "warning",
                "field": "candidate_poses",
                "message": f"pose '{pose.get('pose_id')}' "
                           f"연결된 mask '{pose['linked_mask_id']}'가 없습니다.",
            })

    # === affordance 있는데 contact mask 없음 경고 ===
    if label_data.get("affordances") and not label_data.get("contact_region_masks"):
        issues.append({
            "level": "warning",
            "field": "contact_region_masks",
            "message": "affordance는 있지만 contact_region_masks가 비어있습니다.",
        })

    # === pose 있는데 affordance 연결 없음 경고 ===
    for pose in label_data.get("candidate_poses", []):
        if not pose.get("linked_affordance_id"):
            issues.append({
                "level": "warning",
                "field": "candidate_poses",
                "message": f"pose '{pose.get('pose_id')}'에 linked_affordance_id가 없습니다.",
            })

    # === annotator 확인 ===
    if not label_data.get("annotator") or label_data["annotator"] == "unknown":
        issues.append({
            "level": "warning",
            "field": "annotator",
            "message": "annotator가 설정되지 않았습니다.",
        })

    return issues


def print_validation_report(issues: list[dict]):
    """검증 결과를 콘솔에 출력"""
    if not issues:
        print("[validate] 검증 통과: 문제 없음")
        return

    errors = [i for i in issues if i["level"] == "error"]
    warnings = [i for i in issues if i["level"] == "warning"]

    print(f"[validate] 검증 결과: {len(errors)} 오류, {len(warnings)} 경고")

    for issue in errors:
        print(f"  [ERROR]   {issue['message']}")

    for issue in warnings:
        print(f"  [WARNING] {issue['message']}")


# === CLI 테스트 ===
if __name__ == "__main__":
    # 빈 라벨 생성 테스트
    label = create_empty_label("ycb_025_mug", "mesh", "고박사")
    print("--- 빈 라벨 생성 ---")
    print(json.dumps(label, indent=2, ensure_ascii=False)[:500])

    # 저장 테스트
    path = save_label(label)

    # 로드 테스트
    loaded = load_label(path)
    assert loaded["object_id"] == "ycb_025_mug"
    print("--- 로드 성공 ---")

    # 검증 테스트
    issues = validate_label(loaded)
    print_validation_report(issues)

    # 샘플 라벨 검증
    sample_path = LABELS_DIR / "ycb_025_mug_sample.json"
    if sample_path.exists():
        sample = load_label(str(sample_path))
        sample_issues = validate_label(sample)
        print("\n--- 샘플 라벨 검증 ---")
        print_validation_report(sample_issues)
