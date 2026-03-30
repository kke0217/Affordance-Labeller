---
title: "Phase 4: Physics-Verified Affordance Label Extraction"
status: planning
created: 2026-03-29
updated: 2026-03-30
project: Affordance-Labeller
---

# Phase 4: Physics-Verified Affordance Label Extraction

> 핵심: VR이 아니라 **PhysX contact → 구조화된 라벨 자동 추출**이 본질.
> VR은 입력 채널일 뿐이고, P4-B에서 붙인다.

---

## 한 줄 요약

Isaac Sim에서 로봇 손으로 객체를 파지하면, 접촉점·포즈·안정성이 자동 추출되어 기존 JSON+.npy 스키마로 저장되는 **demonstration-driven label generation** 파이프라인.

---

## Phase 3과의 연결

| Phase 3 자산 | Phase 4 재사용 |
|---|---|
| io_handler.py (save/load/validate/manifest) | **그대로 재사용** |
| JSON 스키마 v0.1 | **확장** (episode_id, robot_config 추가) |
| .npy vertex_indices | **그대로 재사용** |
| bundle export/import (.zip) | **그대로 재사용** |
| review workflow (draft→reviewed→approved) | **VR 생성 라벨 검수에 사용** |
| main.py (Trame UI) | **검수/후편집 전용으로 유지** |

---

## 3단계 실행 계획

### P4-A: Physics-Assisted Label Extraction (VR 없이)

> **목표**: Isaac Sim에서 scripted/teleop grasp → contact patch + pose + stability 자동 추출
> **VR 불필요** — 키보드/마우스 teleop 또는 스크립트로 충분

#### 구현 범위

```
Isaac Sim (Omniverse)
├── USD Stage에 YCB mesh 로드
├── Robot Hand Model (URDF → USD)
├── PhysX Contact Reporter
│   └── 접촉 vertex 추출
├── Scripted Grasp 또는 키보드 Teleop
│   └── hand pose (position + quaternion) 캡처
├── Lift Test
│   └── 파지 후 들어올리기 → 성공/실패 판정
│
▼
Omniverse Extension
├── contact vertices → patch_a / patch_b
├── hand pose → candidate_pose
├── lift result → confidence score
├── source_type: "physics_extraction"
│
▼
기존 io_handler → JSON + .npy + manifest 저장
```

#### 산출물
- Omniverse Extension (Python)
- 스키마 v0.2 (episode_id, robot_config, camera_config 추가)
- 최소 1개 객체에서 contact + pose + confidence 자동 추출 성공
- 기존 Trame UI에서 생성된 라벨을 로드+검수 가능

#### 완료 기준
- [ ] Isaac Sim에서 YCB mug 로드 + robot hand 배치
- [ ] PhysX ContactReporter로 접촉 vertex 추출 성공
- [ ] 파지 pose (position + quaternion) 캡처 성공
- [ ] Lift test 성공/실패 자동 판정
- [ ] JSON + .npy로 저장 → Trame UI에서 Load + 검수 가능

#### 기술 리스크
| 리스크 | 심각도 | 대응 |
|--------|--------|------|
| collision mesh ↔ visual mesh 해상도 차이 | 높음 | 동일 mesh 사용 또는 nearest vertex 매핑 |
| PhysX contact 노이즈 | 중 | 접촉 지속 시간 threshold 필터링 |
| 로봇 손 모델 선정 | 중 | Allegro / LEAP / Shadow 중 URDF 가용성 기준 선택 |

#### 예상 기간: 4~6주

---

### P4-B: VR Demonstration 연동

> **목표**: VR HMD + 컨트롤러로 P4-A의 파지 입력을 대체
> **P4-A가 완료된 후 시작**

#### 구현 범위

```
VR HMD (Quest / Vive)
    │ OpenXR / Omniverse XR
    ▼
P4-A의 Isaac Sim 파이프라인
    │ (기존 Contact Reporter + Lift Test 재사용)
    ▼
추가: VR 세션 관리
    ├── episode_id 자동 부여
    ├── 세션 시작/종료 기록
    ├── 연속 파지 시도 → 다수 라벨 자동 축적
    └── source_type: "vr_demonstration"
```

#### 산출물
- VR 입력 → Isaac Sim hand 매핑
- 연속 파지 세션 → 다수 라벨 자동 축적
- 수동 라벨링 대비 **시간 절감** 정량 비교

#### 완료 기준
- [ ] VR 컨트롤러 → 로봇 손 실시간 매핑
- [ ] VR 세션 1회에서 10+ 파지 라벨 자동 생성
- [ ] 수동 라벨링 대비 속도 비교 (목표: 5배 이상)
- [ ] 생성 라벨의 일관성 평가

#### 예상 기간: 3~4주 (P4-A 완료 후)

---

### P4-C: Dataset Export + Downstream 검증

> **목표**: P4-A/B로 생성한 라벨을 학습 파이프라인에 연결
> **논문의 핵심 contribution 증명 단계**

#### 구현 범위

```
P4-A/B 생성 라벨 (JSON + .npy)
    │
    ├── RLDS export (episode/step 구조)
    ├── LeRobot export (episode/frame 구조)
    │
    ▼
Downstream 학습
    ├── 모방학습: affordance-conditioned policy
    └── 평가: "이 데이터로 학습한 로봇이 더 잘 잡는가?"
```

#### 산출물
- RLDS / LeRobot 변환 스크립트
- 다종 객체 (50+) 데이터셋
- Downstream policy 성능 비교

#### 완료 기준
- [ ] 최소 10개 객체 × 10+ 파지 = 100+ 라벨
- [ ] RLDS 또는 LeRobot 포맷 export 성공
- [ ] Downstream policy 학습 + baseline 대비 성능 비교

#### 예상 기간: 4~6주 (P4-B 완료 후)

---

## 스키마 확장 계획 (v0.1 → v0.2)

P4-A 시작 시 스키마를 확장한다:

| 필드 | 타입 | 용도 | 추가 시점 |
|------|------|------|----------|
| episode_id | string | VR/sim 세션 식별 | P4-A |
| frame_index | int | 에피소드 내 프레임 번호 | P4-B |
| timestamp_offset | float | 에피소드 내 시간 (초) | P4-B |
| robot_config | object | 로봇 모델/URDF 정보 | P4-A |
| camera_config | object | 카메라 파라미터 | P4-C |
| gripper_state | float | 그리퍼 개폐 상태 (0~1) | P4-A |
| lift_success | boolean | lift test 성공 여부 | P4-A |
| stability_score | float | 물리 안정성 점수 (0~1) | P4-A |

---

## 양손 파지 (Bimanual) 전략

현재 스키마에 `hand_role: left/right/either`가 이미 있으므로:

- P4-A: **단일 손**으로 시작 (파이프라인 검증)
- P4-B: 양손 VR 컨트롤러 → **양손 동시 파지**
- P4-C: bimanual affordance 데이터셋 (차별점)

양손 시나리오:
- 한 손으로 잡고 다른 손으로 뚜껑 열기
- 양손으로 큰 객체 들어올리기
- 한 손으로 고정, 다른 손으로 도구 사용

---

## 논문 전략

### 가장 현실적인 경로: 시스템 논문 (IROS / ICRA)

> "Physics-Verified Grasp Affordance Extraction via Demonstration in Isaac Sim"

**필요 조건**:
1. 수동 라벨 대비 **시간 절감** (P4-B에서 측정)
2. 라벨 **일관성/정확도** 비교 (P4-A/B에서 측정)
3. 최소 10개 객체

### 임팩트 확장: 데이터셋 논문 (CoRL / NeurIPS Datasets)

> "BimanualAffordance: Physics-Verified Bimanual Grasp Affordance Dataset"

**추가 필요 조건**:
- 50+ 객체
- Downstream 학습 결과 (P4-C)

### 용어 주의

- ❌ "Auto Labelling" → 과장
- ✅ "Demonstration-Driven Label Generation" 또는 "Physics-Assisted Extraction"

---

## 다음 액션 (P4-A 착수 전)

| 순서 | 항목 | 비고 |
|------|------|------|
| 1 | Isaac Sim Omniverse XR 문서 조사 | P4-B 사전 조사 |
| 2 | PhysX ContactReporter API 확인 | P4-A 핵심 |
| 3 | 로봇 손 모델 선정 (Allegro/LEAP/Shadow) | URDF 가용성 기준 |
| 4 | Isaac Sim에서 YCB mug 로드 PoC | P4-A 첫 단계 |
| 5 | 스키마 v0.2 설계 | P4-A 착수 전 확정 |
| 6 | 기존 VR teleop 논문 서베이 | RoboTurk, DART, DexMV |
| 7 | 양손 파지 affordance 논문 서베이 | AffordPose 등 |

---

## Phase 전체 로드맵

```
Phase 1 (완료)    Phase 2 (완료)    Phase 3 (완료)
수동 MVP       →  코드 정비      →  Trame 전환 + 반자동
                                         │
                                         ▼
                                    Phase 4
                               P4-A: Physics extraction (VR 없이)
                                         │
                                    P4-B: VR demonstration
                                         │
                                    P4-C: Dataset + downstream
```

---

*이 문서는 실행계획 단계이며, P4-A 착수 시 상세 Sprint 계획을 별도 작성.*
