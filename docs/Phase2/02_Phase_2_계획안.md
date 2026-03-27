---
title: "Phase 2: 코드 정비 + 라벨링 정밀도 확보"
tags:
  - phase-2
  - execution-plan
  - refactoring
  - precision
status: planned
created: 2026-03-26
depends_on: Phase 1 (완료)
---

# Phase 2: 코드 정비 + 라벨링 정밀도 확보

> Phase 1에서 MVP 골격을 세웠다. Phase 2에서는 "프로토타입"을 "연구자가 실제로 쓸 수 있는 도구"로 전환한다.

## 문서 목적
Phase 1(수동 라벨링 MVP)의 구조적 한계와 라벨링 정밀도 부족을 해결하여, 다수 객체에 대해 의미 있는 연구 데이터를 생산할 수 있는 수준으로 끌어올린다.

## 한 줄 결론
**코드 구조를 정비하고, vertex 단위 접촉 영역 편집 + pose rotation 편집 + 범용 객체 확장을 구현하여, "mug 전용 데모"에서 "다종 객체 라벨링 도구"로 전환한다.**

## Phase 1에서 넘어온 기술 부채

| 항목 | 현재 상태 | 문제 |
|------|----------|------|
| 전역 상태 관리 | `current_label`, `viewer` 등 전역 변수 | 기능 추가 시 상태 꼬임 |
| main.py 구조 | `setup_ui()` 671줄 단일 함수 | 유지보수 불가 |
| vertex_indices 저장 | JSON 직접 포함 (4~9MB) | Git 부담, 로드 느림 |
| Contact patch 편집 | vertex 절반 자동 분할 | 실제 접촉 의미 없음 |
| Pose rotation | identity quaternion 고정 | 6D pose라 부를 수 없음 |
| 객체 범용성 | YCB mug 1개만 | 도구가 아닌 데모 수준 |
| Part 분할 | `auto_segment_mug()` mug 전용 | 다른 객체에 적용 불가 |

---

## Phase 2 구성

Phase 2는 두 단계로 나눈다.

### Phase 2-A: 기반 정비 (모든 후속 기능의 전제조건)

> **목표**: 코드 구조를 정리하여 Phase 2-B 이후의 기능 추가가 안전하게 가능한 상태로 만든다.

| 순위 | 작업 | 설명 | 완료 기준 |
|------|------|------|----------|
| 1 | AppState 클래스 도입 | 전역 변수 → 단일 상태 객체 | `current_label`, `viewer`, `current_mesh_path`가 AppState 멤버 |
| 2 | main.py 모듈 분리 | setup_ui() → 패널별 모듈 | `panels/object_info.py`, `panels/parts.py`, `panels/affordances.py` 등 |
| 3 | vertex_indices 바이너리 분리 | JSON에서 .npy로 분리 저장 | JSON < 100KB, .npy 별도 참조 |

**Phase 2-A 게이트**: main.py가 200줄 이하이고, 기존 기능(Auto Segment → Affordance → Mask → Pose → Save/Load)이 모두 동작

---

### Phase 2-B: 라벨링 정밀도 확보

> **목표**: annotator가 실제로 의미 있는 연구 데이터를 생산할 수 있는 편집 정밀도를 확보한다.

| 순위 | 작업 | 설명 | 완료 기준 |
|------|------|------|----------|
| 4 | Contact patch vertex 선택/편집 | "절반 나누기" → 실제 영역 선택 | 브러시 또는 rect-select로 patch A/B 지정 가능 |
| 5 | Pose rotation 편집 | identity 고정 → 자유 회전 | euler 입력 또는 Viser TransformControls로 회전 편집 |
| 6 | 범용 객체 확장 | YCB mug 외 2~3개 객체 추가 | YCB banana, YCB scissors 등에서 라벨링 가능 |
| 7 | 범용 part 분할 | mug 전용 → SAM 또는 수동 선택 fallback | 임의 mesh에서 part 정의 가능 |

**Phase 2-B 게이트**: YCB mug 외 최소 1개 객체에서 contact patch 수동 편집 + pose rotation 편집이 포함된 라벨을 저장/재로드할 수 있다

---

## 실행 우선순위와 의존 관계

```
Phase 2-A (기반 정비)
  ├── [1] AppState 클래스
  ├── [2] 모듈 분리 (← [1] 의존)
  └── [3] vertex_indices 바이너리 분리
         │
         ▼
Phase 2-B (라벨링 정밀도)
  ├── [4] Contact patch 편집 (← [1][2] 의존)
  ├── [5] Pose rotation 편집
  ├── [6] 범용 객체 확장 (← [3] 의존)
  └── [7] 범용 part 분할 (← [6] 의존)
```

---

## Phase 2에서 하지 않는 것

아래 항목은 Phase 3 이후로 미룬다.

| 항목 | 이유 |
|------|------|
| Confidence 자동 산출 | physics validation 없이는 의미 없음 |
| Physical stability score / Lift test | Isaac Sim 연동 필요, 별도 인프라 |
| 접촉 후보 자동 샘플링 | Phase 2-B의 수동 편집이 먼저 |
| RLDS / LeRobot export | 스키마 확장 필드 예약만 (Phase 2-A에서) |
| Dataset factory (대량 생성) | 범용 객체 + 자동화가 먼저 |
| 다중 annotator / DB 백엔드 | 현재 1인 개발 |

---

## Phase 2-A 상세 작업

### [1] AppState 클래스 도입

```python
# 목표 구조
class AppState:
    label: dict              # current_label
    mesh_path: str           # current_mesh_path
    viewer: MeshViewer       # viewer
    server: viser.ViserServer
```

- 모든 콜백이 `state.label`, `state.viewer`로 접근
- 전역 변수 완전 제거

### [2] main.py 모듈 분리

```
app/
├── main.py              # 서버 시작 + AppState 초기화 (< 200줄)
├── state.py             # AppState 클래스
├── panels/
│   ├── object_info.py   # Object Info 패널
│   ├── canonical_frame.py
│   ├── parts.py         # Parts 패널 + auto_segment 연동
│   ├── affordances.py   # Affordance 편집 패널
│   ├── contact_masks.py # Contact Mask 편집 패널
│   ├── candidate_poses.py
│   └── file_ops.py      # Save/Load/Validate/Quit
├── viewer.py            # 기존 유지
└── io_handler.py        # 기존 유지
```

### [3] vertex_indices 바이너리 분리

```
labels/
├── ycb_025_mug.json          # 메타데이터만 (< 100KB)
└── ycb_025_mug_vertices/
    ├── part_body.npy          # np.save()
    ├── part_handle.npy
    ├── aff_handle_graspable.npy
    └── mask_handle_pinch_a.npy
```

- JSON의 `vertex_indices` 필드 → `"vertex_indices_file": "ycb_025_mug_vertices/part_body.npy"` 참조
- io_handler.py에 .npy 저장/로드 로직 추가

---

## Phase 2-B 상세 작업

### [4] Contact patch vertex 선택/편집

- Viser `on_pointer_event('rect-select')` 활용
- 또는 sphere brush (3D 위치 + 반지름 → 인접 vertex 선택)
- 선택된 vertex를 Patch A 또는 Patch B에 할당
- 색상 오버레이로 즉시 시각적 피드백

### [5] Pose rotation 편집

옵션 A: Euler 각도 입력 (vector3 UI)
- `gui_pose_rotation = server.gui.add_vector3("Rotation (deg)", ...)`
- euler → quaternion 변환

옵션 B: Viser TransformControls
- `server.scene.add_transform_controls()` 사용
- 드래그로 회전/이동 편집
- 편집 결과를 pose 데이터에 반영

→ **먼저 옵션 A로 구현하고, 옵션 B는 Viser API 안정성 확인 후 전환**

### [6] 범용 객체 확장

- `download_ycb.py`에 YCB 객체 2~3개 추가:
  - `006_mustard_bottle` (병 형태)
  - `035_power_drill` (비대칭 도구)
  - `011_banana` (유기적 형태)
- `--mesh` 인자로 임의 .ply/.obj 로드 가능 (이미 지원)
- 핵심: auto_segment 없이도 수동 part 정의가 가능해야 함

### [7] 범용 part 분할

단계적 접근:
1. **수동 fallback**: rect-select 또는 brush로 vertex 선택 → part로 지정
2. **(선택) SAM 연동**: mesh → 렌더링 이미지 → SAM → 2D mask → 3D vertex 매핑

→ **수동 fallback을 먼저 구현하고, SAM은 PoC로만**

---

## 의사결정 게이트

| 게이트 | 내용 | 판정 기준 |
|--------|------|----------|
| Gate 2-A | 코드 구조 정비 완료 | main.py < 200줄, 기존 기능 모두 동작, vertex_indices .npy 분리 |
| Gate 2-B | 라벨링 정밀도 확보 | mug 외 1개 객체에서 patch 수동 편집 + rotation 편집 포함 라벨 저장/재로드 |

---

## Phase 2 이후 로드맵

```
Phase 1 (완료)     Phase 2 (다음)           Phase 3 (이후)
수동 라벨링 MVP  →  코드 정비 + 정밀도  →  자동화 + 물리검증 + Export
                                           ├── confidence 산출
                                           ├── physics lift test
                                           ├── 자동 contact sampling
                                           ├── RLDS / LeRobot export
                                           └── dataset factory
```

---

## 연결 문서
- [[프로젝트_개요]]
- [[01_Phase_1_계획안]] — Phase 1 (완료)
- [[데이터_스키마_초안]]
- [[Phase_1_일별_실행기록]] — Phase 1 일별 실행 기록
- [[목표시스템_vs_현재구현판(v1.0)_비교]] — 갭 분석
