---
title: "Phase 4: VR 기반 Affordance 자동 라벨링 구상"
status: ideation
created: 2026-03-29
project: Affordance-Labeller
---

# Phase 4: VR 기반 Affordance 자동 라벨링 구상

> 이 문서는 아이디어 숙성 단계이며, 구체적 실행 계획은 아직 미확정.

## 한 줄 요약

VR 장비로 Isaac Sim 환경에서 로봇 손으로 객체를 직접 파지하면, 해당 파지의 affordance를 자동으로 라벨링하는 Omniverse Extension.

---

## 핵심 아이디어

현재 시스템(Phase 1~3)은 **사람이 화면을 보며 수동으로 라벨링**한다. Phase 4에서는 **사람이 VR로 직접 잡아보면 라벨이 자동 생성**된다.

```
Phase 1~3: 화면 → 클릭 → 수동 라벨
Phase 4:   VR → 파지 → 자동 라벨
```

---

## 아키텍처

```
VR HMD (Quest / Vive)
    │
    ▼
Isaac Sim (Omniverse)
    ├── USD Stage (YCB / 임의 객체 mesh)
    ├── Robot Hand Model (URDF → USD)
    ├── PhysX 물리 엔진
    │     ├── 접촉 감지 (ContactReporter)
    │     └── Lift Test (안정성 판정)
    │
    ▼
Affordance Auto Labeller (Omniverse Extension)
    ├── 입력 자동 추출:
    │     ├── contact vertices → patch_a / patch_b
    │     ├── hand pose → candidate_pose (position + quaternion)
    │     ├── finger contact → finger_role 매핑
    │     └── grasp type 자동 분류 (손가락 구성에서 추론)
    ├── 품질 자동 산출:
    │     ├── PhysX stability → confidence score
    │     ├── lift test 성공/실패 → approved 필드
    │     └── 파지 지속 시간 → robustness 지표
    ├── 메타데이터:
    │     ├── source_type: "vr_demonstration"
    │     ├── episode_id, timestamp
    │     └── robot_config, camera_config
    │
    ▼
기존 JSON + .npy 스키마 (io_handler 재사용)
    │
    ▼
RLDS / LeRobot export → 모방학습 / 강화학습
```

---

## 현재 시스템과의 연결

### 재사용 가능

| 모듈 | 재사용 여부 |
|------|-----------|
| io_handler.py (save/load/validate/manifest) | **그대로 재사용** |
| JSON 스키마 v0.1 | **확장 사용** (source_type, episode_id 추가) |
| .npy vertex_indices 저장 | **그대로 재사용** |
| viewer.py (색상 팔레트, auto_segment) | 부분 재사용 |
| main.py (Trame UI) | VR에서는 불필요, 검수 시에만 사용 |

### 새로 만들어야 하는 것

| 모듈 | 설명 |
|------|------|
| Omniverse Extension | Isaac Sim 플러그인 본체 |
| VR 입력 처리 | OpenXR → hand pose 캡처 |
| PhysX ContactReporter 연동 | 접촉 vertex 추출 |
| Grasp Type 자동 분류기 | 손가락 구성 → pinch/power/lateral 추론 |
| Lift Test 자동화 | 파지 후 들어올리기 시나리오 |

---

## 데이터 흐름 (1회 파지 세션)

```
1. VR 사용자가 로봇 손으로 객체를 잡음
2. PhysX가 접촉 vertex 기록
3. 손 pose (position + quaternion) 캡처
4. 사용자가 들어올리기 시도
5. Lift test 성공 여부 판정
6. → 자동으로 하나의 candidate_pose + contact_mask 생성
7. → confidence = stability score
8. → source_type = "vr_demonstration"
9. → JSON + .npy 저장
10. 반복 → 다양한 파지 데이터 축적
```

---

## 논문 가능성

### 시스템 논문 (IROS / ICRA)
> "VR-in-the-Loop Affordance Annotation: Physics-Verified Grasp Affordance Labeling via VR Demonstration in Isaac Sim"

### 데이터셋 논문 (CoRL / NeurIPS Datasets)
> "BimanualAffordance: A Large-Scale Bimanual Grasp Affordance Dataset via VR Demonstration"

### 풀 논문 (RSS / CoRL) — 가장 어려움
> "From Human Demonstration to Robot Affordance: Automatic Affordance Extraction with Physics-Based Verification"

### 논문 필수 조건
- downstream 학습 결과: "이 데이터로 학습한 로봇이 실제로 더 잘 잡는다"
- 수동 라벨링 대비 정량 비교 (속도, 정확도, 일관성)
- 다종 객체 (50+) + 다양한 grasp type

---

## 양손 파지 (Bimanual) 차별점

대부분의 기존 연구는 **단일 손 파지**에 집중. 양손 파지 affordance 데이터셋은 매우 희소.

양손 시나리오:
- 한 손으로 잡고 다른 손으로 뚜껑 열기
- 양손으로 큰 객체 들어올리기
- 한 손으로 고정, 다른 손으로 도구 사용

→ `hand_role: left/right` 필드가 이미 스키마에 있으므로 양손 데이터 저장 구조는 준비됨.

---

## 기술적 리스크

| 리스크 | 심각도 | 대응 |
|--------|--------|------|
| Isaac Sim VR 연동 안정성 | 높음 | Omniverse XR 기능 검증 PoC 필요 |
| PhysX contact → mesh vertex 매핑 정확도 | 중 | collision mesh와 visual mesh 해상도 차이 처리 |
| VR 조작의 자연스러움 | 중 | 로봇 손 모델의 자유도에 따라 다름 |
| 대규모 데이터 수집 시 파이프라인 안정성 | 중 | autosave + crash recovery 필요 |
| 시뮬→실제 전이 (sim-to-real gap) | 높음 | 도메인 랜덤화, 다양한 물체 텍스처/물성 |

---

## Phase 4 전에 해야 할 것 (Phase 3 잔여)

- [ ] Sprint C: RLDS / LeRobot export stub (VR 데이터도 이 포맷으로 내보내야 함)
- [ ] Sprint D: confidence heuristic (VR에서는 physics 기반으로 대체)
- [ ] 스키마 확장: episode_id, frame_index, robot_config, camera_config
- [ ] Pose 축 컨벤션 확정 (approach / grip / palm 매핑)

---

## 다음 액션 (아이디어 숙성)

- [ ] Isaac Sim Omniverse XR 문서 조사
- [ ] PhysX ContactReporter API 확인
- [ ] 기존 VR teleoperation 논문 서베이 (RoboTurk, DART, DexMV)
- [ ] 양손 파지 affordance 관련 논문 서베이
- [ ] 로봇 손 모델 선정 (Allegro, LEAP, Shadow 등)
- [ ] PoC 범위 정의: 단일 객체 + 단일 손 → 양손 확장

---

*이 문서는 아이디어 단계이며, 구체적 일정과 실행 계획은 Phase 3 완료 후 수립.*
