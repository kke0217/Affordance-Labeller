---
title: P3-008 Export Mapping Memo
status: draft
created: 2026-03-29
---

# Export Mapping Memo (내부 JSON ↔ RLDS/LeRobot)

> Lightweight mapping memo. 실제 export stub 구현은 Phase 4에서 진행.

## 현재 내부 스키마 (label_v0.1.json) 필드

| 필드 | 타입 | RLDS 대응 | LeRobot 대응 | 비고 |
|------|------|----------|-------------|------|
| object_id | string | dataset_name | dataset_name | |
| input_type | string | observation.type | - | mesh/pointcloud/rgbd |
| canonical_frame | object | - | - | 객체 로컬 좌표계 |
| parts[].name | string | - | - | part 시맨틱 이름 |
| parts[].vertex_indices | int[] | - | - | .npy 바이너리 |
| affordances[].label | string | action.affordance | affordance_type | graspable 등 |
| affordances[].semantic_tags | string[] | action.semantic_tag | semantic_tags | pick_up 등 |
| affordances[].part_ref | string | - | - | part 연결 |
| contact_region_masks[].patch_a/b | object | observation.contact | contact_patch | vertex + finger_role |
| candidate_poses[].translation | float[3] | action.ee_pos | position | 미터 단위 |
| candidate_poses[].rotation_xyzw | float[4] | action.ee_quat | quaternion | xyzw 순서 |
| candidate_poses[].grasp_type | string | action.grasp_type | grasp_type | pinch/power 등 |
| candidate_poses[].hand_role | string | action.hand | hand | left/right/either |
| candidate_poses[].confidence | float | - | confidence | 0~1 |
| annotator | string | metadata.annotator | annotator | |
| review_status | string | metadata.review | review_status | draft/reviewed/approved |
| updated_at | string | metadata.timestamp | updated_at | ISO 8601 |

## 누락 필드 (확장 필요)

| 필드 | 용도 | 언제 추가 |
|------|------|----------|
| episode_id | 에피소드 단위 묶음 | Phase 4 (VR 시연 시) |
| frame_index | 프레임 번호 | Phase 4 |
| camera_config | 카메라 파라미터 | Phase 4 |
| robot_config | 로봇 모델/URDF 정보 | Phase 4 |
| timestamp_offset | 에피소드 내 시간 | Phase 4 |
| gripper_state | 그리퍼 개폐 상태 | Phase 4 |

## 변환 방향

```
내부 JSON (object-level)
    │
    ├── RLDS: episode { steps [ { observation, action } ] }
    │   - 1 label = 1 episode, 각 pose = 1 step
    │   - observation = mesh + part + affordance
    │   - action = pose + grasp_type + hand_role
    │
    └── LeRobot: dataset { episodes [ { frames [ ] } ] }
        - 유사 구조, LeRobot 고유 metadata 추가
```

## 결론

현재 스키마는 RLDS/LeRobot의 핵심 필드를 대부분 커버한다. 부족한 것은 episode/frame 단위 시간 정보와 로봇/카메라 설정인데, 이는 Phase 4 (VR + Isaac Sim)에서 자연스럽게 추가된다.
