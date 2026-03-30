# Affordance Labeller 사용자 가이드 (v3.1 — PyVista+Trame)

> 이 문서는 Affordance Labeller를 처음 사용하는 사람이 **설치부터 라벨 저장/공유까지** 독립적으로 수행할 수 있도록 작성되었습니다.

---

## 목차

1. [설치 및 실행](#1-설치-및-실행)
2. [3D 뷰포트 조작](#2-3d-뷰포트-조작)
3. [라벨링 워크플로우](#3-라벨링-워크플로우)
4. [저장 / 로드 / 공유](#4-저장--로드--공유)
5. [검수 (Review Workflow)](#5-검수-review-workflow)
6. [지원 객체](#6-지원-객체)
7. [색상 범례](#7-색상-범례)
8. [저장 구조](#8-저장-구조)
9. [FAQ / 문제 해결](#9-faq--문제-해결)

---

## 1. 설치 및 실행

### 1.1 설치

```bash
git clone https://github.com/kke0217/Affordance-Labeller.git
cd Affordance-Labeller/src
bash scripts/setup_env.sh
conda activate affordance_labeller
python scripts/download_ycb.py
```

### 1.2 실행

```bash
cd src/

# YCB mug
python app/main.py --mesh assets/ycb/025_mug/google_512k/nontextured.ply --server

# YCB power drill
python app/main.py --mesh assets/ycb/035_power_drill/google_512k/nontextured.ply --object-id ycb_035_power_drill --server

# 임의 mesh
python app/main.py --mesh /path/to/object.ply --object-id my_object --server
```

브라우저에서 **http://localhost:8080** 접속.

### 1.3 종료

터미널에서 `Ctrl+C` 또는 `kill $(lsof -ti:8080)`.

---

## 2. 3D 뷰포트 조작

| 조작 | 동작 |
|------|------|
| **좌클릭 / 드래그** | Painting 모드에서 vertex 칠하기 |
| **우클릭 / 드래그** | Painting 모드에서 선택된 part의 vertex 지우기 |
| **Ctrl + 드래그** | Orbit 회전 (항상 가능, painting 중에도) |
| **스크롤** | 줌 인/아웃 |

> **핵심**: orbit 회전은 항상 **Ctrl+드래그**입니다. 일반 클릭/드래그는 painting에 사용됩니다.

---

## 3. 라벨링 워크플로우

사이드패널은 번호 순서대로 진행합니다:

```
1. Object Info → 2. Parts → 3. Affordances → 4. Contact Masks → 5. Poses → Save
```

3D 뷰포트 좌측 상단에 **실시간 색상 범례**가 표시됩니다. part/affordance/mask 변경 시 자동 갱신됩니다.

---

### Step 1: Object Info

- **Object ID**: 객체 식별자 (파일명에 사용됨)
- **Annotator**: 작성자 이름
- **Review**: 검수 상태 (하단 Set Review 버튼으로 전환)

---

### Step 2: Parts 정의

#### 방법 A: Auto Semantic Segment (mug 전용)
의미적 분류 (body/handle/rim/base). mug에서만 동작.

#### 방법 B: Auto Geometric Segment (범용)
1. **Clusters** 슬라이더로 분할 수 조절 (2~8)
2. **Auto Geometric Segment** 클릭
3. K-means + 법선 기반으로 자동 분할 → region_0, region_1, ...
4. **Rename Part**: From 드롭다운에서 region_0 선택 → To에 `grip` 입력 → **OK**
   - 색상 유지, 이름만 변경
   - affordance/mask 참조 자동 갱신

#### 방법 C: 수동 Painting (범용)
1. **Part Name**에 이름 입력 (자유 텍스트: grip, trigger, chuck 등)
2. **Add** 클릭
3. **Paint** 클릭 → painting 모드 진입
4. **좌클릭/드래그** → 해당 part 색상으로 칠해짐
5. **우클릭/드래그** → 현재 part에서만 vertex 지우기 (다른 part 보존)
6. **Ctrl+드래그** → orbit 회전 (painting 중에도 가능)
7. **Stop** → painting 모드 종료
8. 다른 part를 추가하려면 Part Name 변경 후 반복

**팁**:
- 한 vertex는 하나의 part에만 속합니다. 새 part로 칠하면 기존 part에서 자동 제거됩니다.
- **Clear All**로 전체 part 초기화 가능.
- Brush 슬라이더로 브러시 크기 조정 (0.002~0.05m).
- Provenance 표시: 🤖=auto segment, ✋=수동 painting.
- Contact Mask 세분화가 필요하면 `handle_thumb`, `handle_finger` 등으로 part를 나눠 정의하세요.

---

### Step 3: Affordances 할당

1. **Target Part** 드롭다운에서 대상 part 선택
2. **Class** 드롭다운에서 affordance 유형 선택
3. **Tag** 드롭다운에서 시맨틱 태그 선택
4. **Assign Affordance** 클릭
5. 해당 part가 affordance 색상으로 변경 + 범례 갱신

| Class | 의미 | 색상 |
|-------|------|------|
| graspable | 파지 가능 | 초록 |
| pour_support | 따르기 지지 | 파랑 |
| handover_region | 전달 영역 | 주황 |
| placeable | 놓기 가능 | 보라 |
| non_affordance | 비기능 | 회색 |

| Tag | 의미 |
|-----|------|
| pick_up | 들어올리기 |
| pour_ready | 따르기 |
| handover_ready | 전달 |
| reposition_only | 재배치 |
| place_down | 내려놓기 |
| tilt | 기울이기 |

**복수 태그**: 같은 part+class에 다른 tag로 다시 Assign하면 누적됩니다.

---

### Step 4: Contact Masks 지정

로봇 손가락이 닿는 접촉 영역을 지정합니다.

#### 수동 할당
1. **Mask Type** 선택 (handle_pinch, body_power, rim_control, custom)
2. **Patch A Part** 선택 + **A finger** 역할 선택
3. **Patch B Part** 선택 + **B finger** 역할 선택
4. **Assign Mask** 클릭

#### Auto Split (PCA 기반 자동 양분)
1. **Split Part** 드롭다운에서 대상 part 선택
2. **Auto Split → A/B** 클릭
3. PCA 주성분 방향으로 part vertex가 자동 양분됨

| Finger Role | 의미 |
|-------------|------|
| thumb | 엄지 |
| index | 검지 |
| index_middle | 검지~중지 |
| palm | 손바닥 |
| all_fingers | 모든 손가락 |

**참고**:
- 같은 part에 Assign과 Auto Split을 반복하면 기존 mask가 교체됩니다 (중복 누적 없음).
- 여러 part에 mask를 할당하면 **mask별 다른 색상 쌍**으로 표시됩니다.
- PCA split은 기하학적 양분이며, 실제 파지 시맨틱은 반영하지 않습니다.

---

### Step 5: Poses 배치

로봇 손의 6D 위치와 방향을 지정합니다.

#### 배치
1. **Name**, **Grasp Type**, **Hand**, **Link Affordance**, **Link Mask** 설정
2. **Place Pose** 클릭 → pose 배치 모드
3. **객체 표면 클릭** → 클릭 위치에 RGB 좌표축 화살표 생성
   - 빨강=X, 초록=Y, 파랑=Z + 흰색 중심점
   - 연속 클릭으로 여러 pose 배치 가능 (자동 번호 증가)
   - 방금 생성한 pose가 Select Pose에 자동 선택됨
4. **Stop** → pose 배치 모드 종료

#### 회전 편집
1. **Select Pose** 드롭다운에서 편집할 pose 선택 (Place 직후 자동 선택)
2. **Roll / Pitch / Yaw** 슬라이더 조절 (-180°~180°, 5° 단위)
3. 좌표축 화살표가 **실시간으로 회전**

#### 삭제
- **Remove Last** → 마지막 pose + 3D 마커 동시 삭제

| Grasp Type | 의미 |
|------------|------|
| pinch | 핀치 그립 (엄지+검지) |
| power | 파워 그립 (손 전체) |
| lateral | 측면 그립 |
| hook | 훅 그립 |
| precision | 정밀 그립 |
| custom | 사용자 정의 |

---

## 4. 저장 / 로드 / 공유

### Save
- **Save** 클릭 → JSON + .npy + manifest.json 자동 생성
- 저장 후 자동 validation → 경고/에러 표시
- 저장 위치: `src/labels/{object_id}.json`

### Load
- **Object ID** 입력 → **Load** 클릭
- 색상 오버레이 + 범례 + 드롭다운 자동 복원

### Export Bundle
- **Export Bundle (.zip)** 클릭 → JSON + .npy + manifest를 zip으로 묶어 저장
- zip 파일 하나로 라벨 데이터를 공유/백업 가능

### Import Bundle
- **Import zip path** 필드에 zip 경로 입력 (예: `labels/ycb_035_power_drill_bundle.zip`)
- **Import Bundle** 클릭 → labels/ 디렉토리에 복원 + 자동 로드

---

## 5. 검수 (Review Workflow)

라벨의 검수 상태를 단계별로 전환합니다.

### 전환 규칙

```
draft → in_review → reviewed → approved
                  ↘ draft     ↘ draft
```

- Review 드롭다운에서 목표 상태 선택 → **Set Review** 클릭
- **직접 건너뛰기 불가**: draft에서 approved로 바로 전환 불가
- **reviewed/approved 전환 시**: validation warning이 있으면 전환 차단 (예: parts 없음)
- 전환 이력이 `review_history`에 자동 기록 (from, to, by, timestamp)

---

## 6. 지원 객체

| 객체 | Part 분류 방법 |
|------|---------------|
| YCB Mug (025) | Auto Semantic + Auto Geometric + 수동 |
| YCB Mustard Bottle (006) | Auto Geometric + 수동 |
| YCB Power Drill (035) | Auto Geometric + 수동 |
| YCB Banana (011) | Auto Geometric + 수동 |
| 임의 .ply/.obj/.stl | Auto Geometric + 수동 |

---

## 7. 색상 범례

3D 뷰포트 좌측 상단에 실시간 범례가 표시됩니다.

| 색상 | 의미 |
|------|------|
| 회색 | 미할당 vertex |
| 8색 팔레트 (순환) | Part별 자동 할당 색상 |
| 초록 | graspable affordance |
| 파랑 | pour_support affordance |
| 주황 | handover_region affordance |
| 보라 | placeable affordance |
| 핫핑크/시안 (1번째 mask) | Contact Mask Patch A/B |
| 금/보라 (2번째 mask) | Contact Mask Patch A/B |
| 에메랄드/크림슨 (3번째) | Contact Mask Patch A/B |
| RGB 화살표 | Pose 좌표축 (X=빨강, Y=초록, Z=파랑) |

---

## 8. 저장 구조

```
labels/
├── ycb_025_mug.json              ← 메타데이터 (< 10KB)
├── ycb_025_mug_vertices/
│   ├── manifest.json              ← 파일 목록 + SHA256 checksum
│   ├── part_body.npy
│   ├── aff_handle_graspable.npy
│   └── mask_handle_pinch_patch_a.npy
└── ycb_025_mug_bundle.zip        ← Export Bundle 결과
```

- Save 시 manifest.json 자동 생성 (파일 목록 + checksum)
- Load 시 manifest 기반 무결성 검증 (파일 누락/손상 감지)
- v0.1 인라인 JSON (구버전) 하위 호환 유지

---

## 9. FAQ / 문제 해결

### Q: Painting 중 orbit이 안 됩니다.
**A**: **Ctrl** 키를 누른 상태에서 드래그하세요. Painting 모드에서도 Ctrl+드래그로 orbit이 가능합니다.

### Q: 칠한 영역을 지우고 싶습니다.
**A**: Paint 모드에서 **우클릭/드래그**하면 현재 선택된 part에서만 지워집니다.

### Q: Auto Geometric Segment 후 이름을 바꾸고 싶습니다.
**A**: **Rename Part** — From 드롭다운에서 기존 이름 선택, To에 새 이름 입력, OK 클릭. 색상은 유지됩니다.

### Q: Contact Mask가 중복 생성됩니다.
**A**: 같은 part에 Assign/Auto Split을 반복하면 기존 mask가 교체됩니다. 다른 part에 대한 mask는 별도로 추가됩니다.

### Q: Pose 좌표축을 회전하고 싶습니다.
**A**: Place Pose 후 자동으로 Select Pose에 선택됩니다. Roll/Pitch/Yaw 슬라이더를 조절하세요.

### Q: 라벨을 다른 사람에게 공유하고 싶습니다.
**A**: Save → **Export Bundle (.zip)** 클릭. zip 파일 하나로 공유 가능. 수신자는 Import Bundle로 복원.

### Q: Review 상태를 approved로 바꿀 수 없습니다.
**A**: draft → in_review → reviewed → approved 순서로만 전환 가능합니다. 또한 reviewed/approved 전환 시 validation warning이 있으면 차단됩니다 (예: parts가 비어있으면 전환 불가).

### Q: 포트 8080이 이미 사용 중입니다.
**A**: `--port 9090` 옵션을 추가하세요.

---

## 빠른 참조 체크리스트

```
□ python app/main.py --mesh ... --server
□ http://localhost:8080 접속
□ 2. Parts:
  - Auto Geometric Segment → Rename (또는 수동 Add → Paint)
  - 좌클릭=칠하기, 우클릭=지우기, Ctrl+드래그=orbit
□ 3. Affordances: Target Part → Class + Tag → Assign
□ 4. Contact Masks: Auto Split 또는 Patch A/B Part 선택 → Assign
□ 5. Poses: Place Pose → 표면 클릭 → Stop → Roll/Pitch/Yaw 편집
□ 1. Object Info: Annotator, Review Status 확인
□ Save → Export Bundle (.zip)
```

---

*Affordance Labeller v3.1 (Phase 3 완료, 2026-03-30)*
