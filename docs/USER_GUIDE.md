# Affordance Labeller 사용자 가이드 (v2.0)

> 이 문서는 Affordance Labeller를 처음 사용하는 사람이 **설치부터 라벨 저장까지** 독립적으로 수행할 수 있도록 작성되었습니다.
> v2.0에서는 **YCB 다종 객체 지원**, **click-to-paint 접촉 영역 편집**, **6D pose rotation 편집**이 추가되었습니다.

---

## 목차

1. [설치 및 실행](#1-설치-및-실행)
2. [화면 구성](#2-화면-구성)
3. [라벨링 워크플로우](#3-라벨링-워크플로우)
   - [Step 1: Part 정의](#step-1-part-정의)
   - [Step 2: Affordance 할당](#step-2-affordance-할당)
   - [Step 3: Contact Mask 지정 + 편집](#step-3-contact-mask-지정--편집)
   - [Step 4: Candidate Pose 추가](#step-4-candidate-pose-추가)
   - [Step 5: 저장](#step-5-저장)
4. [기존 라벨 로드 및 검수](#4-기존-라벨-로드-및-검수)
5. [지원 객체](#5-지원-객체)
6. [용어 사전](#6-용어-사전)
7. [색상 범례](#7-색상-범례)
8. [FAQ / 문제 해결](#8-faq--문제-해결)
9. [현재 버전의 제한 사항](#9-현재-버전의-제한-사항)

---

## 1. 설치 및 실행

### 1.1 사전 요구사항

- macOS 또는 Linux (Windows는 미테스트)
- Python 3.10 이상
- conda 또는 python venv
- 웹 브라우저 (Chrome 권장)

### 1.2 설치

```bash
# 저장소 클론
git clone https://github.com/kke0217/Affordance-Labeller.git
cd Affordance-Labeller/src

# 환경 설치 (conda 환경 생성 + 패키지 설치)
bash scripts/setup_env.sh

# conda 환경 활성화
conda activate affordance_labeller

# YCB 에셋 다운로드 (mug, mustard bottle, power drill, banana)
python scripts/download_ycb.py
```

### 1.3 서버 실행

```bash
cd src/

# YCB mug
python app/main.py --mesh assets/ycb/025_mug/google_512k/nontextured.ply

# YCB mustard bottle
python app/main.py --mesh assets/ycb/006_mustard_bottle/google_512k/nontextured.ply --object-id ycb_006_mustard_bottle

# YCB power drill
python app/main.py --mesh assets/ycb/035_power_drill/google_512k/nontextured.ply --object-id ycb_035_power_drill

# 임의 mesh 파일
python app/main.py --mesh /path/to/your/object.ply --object-id my_object
```

### 1.4 브라우저 접속

웹 브라우저에서 **http://localhost:8080** 에 접속합니다.

### 1.5 3D 뷰포트 조작

| 조작 | 동작 |
|------|------|
| 마우스 왼쪽 드래그 | 회전 (orbit) |
| 마우스 오른쪽 드래그 | 이동 (pan) |
| 스크롤 | 줌 인/아웃 |

### 1.6 서버 종료

- 브라우저 사이드패널 **File → Quit Server** 버튼 클릭
- 또는 다른 터미널에서: `kill $(lsof -ti:8080)`

---

## 2. 화면 구성

```
┌─────────────────────────────┬──────────────────┐
│                             │  사이드패널 (UI)  │
│     3D 뷰포트               │                  │
│     (객체 메시)              │  ┌─ Object Info  │
│                             │  ├─ Canonical Frame│
│                             │  ├─ Parts         │
│                             │  ├─ Affordances   │
│                             │  ├─ Contact Masks │
│                             │  ├─ Candidate Poses│
│                             │  └─ File          │
└─────────────────────────────┴──────────────────┘
```

| 폴더 | 역할 |
|------|------|
| **Object Info** | 객체 ID, 입력 유형, 작성자, 검수 상태 |
| **Canonical Frame** | 정규 좌표계 원점 설정 |
| **Parts** | Auto Segment (mug 전용) 또는 수동 part 정의 (범용) |
| **Affordances** | 각 part에 affordance class + semantic tag 부여 |
| **Contact Masks** | 접촉 영역 지정 + **click-to-paint 편집** |
| **Candidate Poses** | 6D pose 추가 (위치 + **회전** 편집) |
| **File** | 저장 / 로드 / 검증 / 서버 종료 |

---

## 3. 라벨링 워크플로우

```
Step 1         Step 2           Step 3              Step 4          Step 5
Part 정의  →  Affordance 할당  →  Contact Mask 편집  →  Pose 추가  →  저장
```

---

### Step 1: Part 정의

**목적**: 메시를 의미 있는 부위로 나눕니다.

#### 방법 A: Auto Segment (mug 전용)

머그컵일 경우 기하학 기반 자동 분류를 사용합니다.

1. **Parts** 폴더를 엽니다.
2. (선택) Handle Ratio / Rim % / Base % 슬라이더를 조정합니다.
3. **Auto Segment (mug)** 버튼을 클릭합니다.
4. 메시가 4가지 색상 (body=보라, handle=초록, rim=노랑, base=회색)으로 칠해집니다.

#### 방법 B: 수동 Part 정의 (범용 — 모든 객체)

mug 이외 객체, 또는 더 정밀한 part 정의가 필요할 때 사용합니다.

1. **Parts** 폴더에서 **Part Name** 드롭다운으로 part 이름을 선택합니다.
   - body, handle, rim, interior, base, other 중 선택
2. **Add Empty Part** 버튼을 클릭합니다 — 빈 part가 생성됩니다.
3. **Brush Radius** 슬라이더로 브러시 크기를 설정합니다.
4. **Start Painting Part** 버튼을 클릭합니다.
5. **3D 뷰포트에서 메시를 클릭**합니다 — 클릭 위치 주변의 vertex가 해당 part에 할당됩니다.
6. 원하는 영역을 모두 칠한 후 **Stop Painting** 을 클릭합니다.
7. 다른 part를 추가하려면 1~6을 반복합니다.

**팁**:
- 한 vertex는 하나의 part에만 속합니다. 새 part로 칠하면 기존 part에서 자동 제거됩니다.
- **Clear All Parts** 로 전체 part를 초기화할 수 있습니다.
- 브러시 크기가 작을수록 정밀하게 칠할 수 있습니다 (기본 0.008m).

> **중요**: Part 정의가 완료되어야 Affordance, Contact Mask를 할당할 수 있습니다.

---

### Step 2: Affordance 할당

v0.1과 동일합니다.

1. **Affordances** 폴더를 엽니다.
2. **Target Part** → **Affordance Class** → **Semantic Tag** 선택
3. **Assign Affordance** 클릭
4. 복수 태그: 같은 part+class에 다른 tag로 다시 Assign하면 누적

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
| pour_ready | 따르기 준비 |
| handover_ready | 전달 준비 |
| reposition_only | 위치 재조정 |
| place_down | 내려놓기 |
| tilt | 기울이기 |

---

### Step 3: Contact Mask 지정 + 편집

**목적**: 로봇 손가락이 닿는 접촉 영역(Patch A, Patch B)을 지정하고, **click-to-paint로 정밀 편집**합니다.

#### 3-1: 초기 Assign

1. **Contact Masks** 폴더를 엽니다.
2. **Target Part** → **Mask Type** → **Patch A/B finger role** 선택
3. **Assign Contact Mask** 클릭
4. 해당 part가 빨강(Patch A)/파랑(Patch B) 두 영역으로 표시됩니다.
   - 초기값은 part vertex를 절반씩 분할한 상태입니다.

#### 3-2: Click-to-Paint 편집 (v2.0 신규)

Assign 후 접촉 영역을 정밀하게 수정합니다.

1. **Paint Target** 드롭다운에서 칠할 대상을 선택합니다:
   - **Patch A (red)**: 빨강으로 칠하기 (보통 엄지 쪽)
   - **Patch B (blue)**: 파랑으로 칠하기 (보통 나머지 손가락 쪽)
2. **Brush Radius** 슬라이더로 브러시 크기를 조정합니다.
3. **Start Editing** 버튼을 클릭합니다.
4. **3D 뷰포트에서 메시를 클릭**합니다:
   - 클릭 위치 주변의 vertex가 선택한 Patch로 할당됩니다.
   - 반대쪽 Patch에서는 자동으로 제거됩니다.
5. 원하는 영역을 모두 칠한 후 **Stop Editing** 을 클릭합니다.

**팁**:
- Paint Target을 전환하면서 번갈아 칠하면 경계를 정밀하게 조정할 수 있습니다.
- 브러시가 작을수록 (0.002~0.005) 세밀한 편집이 가능합니다.

| Mask Type | 의미 | 권장 Part |
|-----------|------|----------|
| handle_pinch | 손잡이 핀치 그립 | handle |
| body_power | 몸체 파워 그립 | body |
| rim_control | 림 컨트롤 그립 | rim |
| custom | 사용자 정의 | 모든 part |

| Finger Role | 의미 |
|-------------|------|
| thumb | 엄지 |
| index | 검지 |
| index_middle | 검지~중지 |
| palm | 손바닥 |
| all_fingers | 모든 손가락 |

---

### Step 4: Candidate Pose 추가

**목적**: 로봇 손의 6D 위치와 **방향(회전)**을 지정합니다.

1. **Candidate Poses** 폴더를 엽니다.
2. **Pose Name**: 의미 있는 이름 입력 (예: `handle_top_pinch`)
3. **Position**: x, y, z 좌표 입력 (단위: 미터)
4. **Rotation (deg)** (v2.0 신규): roll, pitch, yaw 각도 입력 (단위: 도)
   - (0, 0, 0)이면 회전 없음 (기본값)
   - 예: (45, 0, 90) → X축 45° 회전 후 Z축 90° 회전
5. **Grasp Type** / **Hand Role** 선택
6. **Link Affordance** / **Link Mask** 로 연결 관계 설정
7. **Add Pose** 클릭
8. 3D 뷰포트에 **회전된 좌표축 프레임**이 표시됩니다.

| Grasp Type | 의미 |
|------------|------|
| pinch | 핀치 그립 (엄지+검지) |
| power | 파워 그립 (손 전체) |
| lateral | 측면 그립 |
| hook | 훅 그립 |
| precision | 정밀 그립 |
| custom | 사용자 정의 |

| Hand Role | 의미 |
|-----------|------|
| right | 오른손 |
| left | 왼손 |
| either | 양손 가능 |

---

### Step 5: 저장

1. **Object Info** 에서 Object ID, Annotator, Review Status 확인
2. **File → Save Label** 클릭
3. 저장 결과 + 자동 validation 결과가 표시됩니다

**저장 구조** (v2.0):
```
labels/
├── ycb_025_mug.json              # 메타데이터 (< 10KB)
└── ycb_025_mug_vertices/         # vertex_indices 바이너리
    ├── part_body.npy
    ├── part_handle.npy
    ├── aff_handle_graspable.npy
    └── mask_handle_pinch_patch_a.npy
```

JSON은 가볍게 유지되고, 대용량 vertex 데이터는 `.npy` 바이너리로 분리됩니다.

---

## 4. 기존 라벨 로드 및 검수

### 4.1 서버 시작 시 라벨 로드

```bash
python app/main.py \
  --mesh assets/ycb/025_mug/google_512k/nontextured.ply \
  --label labels/sample_handle_grasp.json
```

### 4.2 실행 중 라벨 로드

1. **Object Info → Object ID** 에 object_id 입력
2. **File → Load Label** 클릭

### 4.3 검수 (Review)

1. 라벨 로드 → 3D 뷰포트에서 시각적 확인
2. **File → Validate** 로 무결성 검사
3. **Review Status** → `reviewed` 또는 `approved` 변경
4. **Save Label**

### 4.4 제공된 샘플 라벨

| 파일명 | 내용 |
|--------|------|
| `sample_handle_grasp.json` | handle → graspable [pick_up] + handle_pinch mask + pinch pose |
| `sample_rim_pour.json` | rim → pour_support [pour_ready] + rim_control mask + power pose |
| `sample_body_handover.json` | body → handover_region [handover_ready] + body_power mask + power pose |

---

## 5. 지원 객체

### 기본 제공 (download_ycb.py)

| 객체 | ID | Part 분류 방법 |
|------|-----|---------------|
| YCB Mug | `ycb_025_mug` | Auto Segment (mug) 또는 수동 |
| YCB Mustard Bottle | `ycb_006_mustard_bottle` | 수동 Part 정의 |
| YCB Power Drill | `ycb_035_power_drill` | 수동 Part 정의 |
| YCB Banana | `ycb_011_banana` | 수동 Part 정의 |

### 사용자 객체

`.ply`, `.obj`, `.stl`, `.off`, `.glb`, `.gltf` 포맷의 mesh 파일을 `--mesh` 인자로 지정하면 됩니다:

```bash
python app/main.py --mesh /path/to/your/object.ply --object-id my_custom_object
```

수동 Part 정의 (Add Empty Part → Start Painting)로 part를 지정하세요.

---

## 6. 용어 사전

| 용어 | 영문 | 설명 |
|------|------|------|
| 어포던스 | Affordance | 객체의 특정 부위가 제공하는 조작 가능성 |
| 파트 | Part | 객체를 구성하는 의미 단위 (body, handle, rim, base 등) |
| 접촉 마스크 | Contact Mask | 로봇 손가락이 닿는 표면 영역. Patch A/B로 구분 |
| 후보 포즈 | Candidate Pose | 파지 시 로봇 손의 6D 위치(position)와 방향(rotation) |
| 시맨틱 태그 | Semantic Tag | 어포던스의 구체적 동작 의미 (pick_up, pour_ready 등) |
| 파지 유형 | Grasp Type | 잡는 방식 (pinch, power, lateral 등) |
| 정규 좌표계 | Canonical Frame | 객체 고유의 기준 좌표계 |
| 정점 | Vertex | 3D 메시를 구성하는 점 |
| 검수 상태 | Review Status | 라벨 완성도: draft → in_review → reviewed → approved |
| 브러시 | Brush | click-to-paint 시 클릭 위치 주변 반지름 내 vertex 선택 영역 |

---

## 7. 색상 범례

### Part 색상

| 색상 | Part | RGB |
|------|------|-----|
| 보라 | body | (150, 150, 200) |
| 초록 | handle | (50, 200, 50) |
| 노랑 | rim | (200, 200, 50) |
| 주황 | interior | (200, 100, 50) |
| 회색 | base | (100, 100, 100) |

### Affordance 색상

| 색상 | Class | RGB |
|------|-------|-----|
| 초록 | graspable | (0, 255, 0) |
| 파랑 | pour_support | (0, 100, 255) |
| 주황 | handover_region | (255, 165, 0) |
| 보라 | placeable | (128, 0, 128) |
| 회색 | non_affordance | (128, 128, 128) |

### Contact Mask 색상

| 색상 | 영역 | RGB |
|------|------|-----|
| 빨강 | Patch A (보통 엄지 쪽) | (255, 80, 80) |
| 파랑 | Patch B (보통 나머지 손가락 쪽) | (80, 80, 255) |

### Candidate Pose 좌표축

- **빨강 축**: X 방향
- **초록 축**: Y 방향
- **파랑 축**: Z 방향
- 회전이 적용되면 축 방향이 변경됩니다.

---

## 8. FAQ / 문제 해결

### Q: mug이 아닌 객체에서 Auto Segment를 누르면?
**A**: Auto Segment (mug)는 머그컵 전용입니다. 다른 객체에서는 **수동 Part 정의** (Add Empty Part → Start Painting)를 사용하세요.

### Q: Painting 중 회전/줌이 안 됩니다.
**A**: Painting 모드에서는 클릭이 vertex 선택으로 사용됩니다. **Stop Painting** 또는 **Stop Editing** 으로 편집 모드를 종료한 후 조작하세요.

### Q: Contact Mask의 빨강/파랑 경계를 조정하고 싶습니다.
**A**: Assign 후 **Start Editing** → **Paint Target** 을 전환하면서 3D 뷰에서 클릭하면 경계를 수정할 수 있습니다.

### Q: Pose의 좌표축이 기울어져 보입니다.
**A**: **Rotation (deg)** 에 값을 입력했기 때문입니다. (0, 0, 0)으로 설정하면 기본 방향으로 돌아갑니다.

### Q: 저장된 파일 구조가 이전과 다릅니다.
**A**: v2.0에서 vertex_indices가 `.npy` 바이너리로 분리되었습니다. JSON에는 `vertex_indices_file` 참조만 남습니다. Load 시 자동으로 복원됩니다. v0.1 JSON도 하위 호환으로 로드 가능합니다.

### Q: Auto Segment 버튼을 눌러도 아무 변화가 없습니다.
**A**: 메시가 로드되지 않았을 수 있습니다. `--mesh` 옵션을 확인하세요.

### Q: 서버가 종료되지 않습니다.
**A**: **File → Quit Server** 버튼 또는 `kill $(lsof -ti:8080)` 을 사용하세요.

### Q: 포트 8080이 이미 사용 중입니다.
**A**: `--port 9090` 옵션으로 다른 포트를 지정하세요.

---

## 9. 현재 버전의 제한 사항

| 항목 | v0.1 (Phase 1) | v2.0 (Phase 2) | 다음 버전 (Phase 3) |
|------|---------------|----------------|-------------------|
| 대상 객체 | mug만 | **mug + 3개 + 임의 mesh** | 동일 |
| Part 분류 | mug 전용 auto segment만 | **수동 click-to-paint 추가** | SAM 연동 PoC |
| Contact Patch | 절반 자동 분할 | **click-to-paint 수동 편집** | 동일 |
| Pose 회전 | identity 고정 | **Euler 각도 입력** | TransformControls 드래그 |
| JSON 크기 | 4~9MB | **2~10KB (.npy 분리)** | 동일 |
| 코드 구조 | 전역 변수 + 단일 함수 | **AppState + 모듈 분리** | 동일 |
| Confidence | 없음 | 없음 | 자동 산출 |
| Physics 검증 | 없음 | 없음 | Isaac Sim lift test |
| Export | JSON v0.1만 | JSON v0.1만 | RLDS / LeRobot |

---

## 빠른 참조: 전체 라벨링 체크리스트

```
□ 서버 실행 (python app/main.py --mesh ... --object-id ...)
□ 브라우저 접속 (http://localhost:8080)
□ Parts:
  - mug → Auto Segment (mug) 클릭
  - 기타 → Add Empty Part → Start Painting → 3D 클릭 → Stop Painting
□ Affordances → Target Part → Class + Tag → Assign
□ Contact Masks → Target Part → Mask Type + Roles → Assign
  → (선택) Start Editing → Paint Target 선택 → 3D 클릭으로 경계 수정 → Stop Editing
□ Candidate Poses → 이름 + Position + Rotation(deg) + Grasp Type → Link → Add Pose
□ Object Info → Annotator, Review Status 확인
□ File → Save Label
□ File → Quit Server
```

---

*이 가이드는 Affordance Labeller v2.0 (Phase 2, 2026-03-27) 기준으로 작성되었습니다.*
*Phase 3 업데이트 시 본 문서도 함께 갱신됩니다.*
