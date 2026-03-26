# Affordance Labeller 사용자 가이드 (v0.1)

> 이 문서는 Affordance Labeller MVP를 처음 사용하는 사람이 **설치부터 라벨 저장까지** 독립적으로 수행할 수 있도록 작성되었습니다.
> 현재 버전은 **YCB 025_mug (머그컵) 단일 객체** 전용입니다.

---

## 목차

1. [설치 및 실행](#1-설치-및-실행)
2. [화면 구성](#2-화면-구성)
3. [라벨링 워크플로우](#3-라벨링-워크플로우)
   - [Step 1: Part 자동 분류](#step-1-part-자동-분류)
   - [Step 2: Affordance 할당](#step-2-affordance-할당)
   - [Step 3: Contact Mask 지정](#step-3-contact-mask-지정)
   - [Step 4: Candidate Pose 추가](#step-4-candidate-pose-추가)
   - [Step 5: 저장](#step-5-저장)
4. [기존 라벨 로드 및 검수](#4-기존-라벨-로드-및-검수)
5. [용어 사전](#5-용어-사전)
6. [색상 범례](#6-색상-범례)
7. [FAQ / 문제 해결](#7-faq--문제-해결)
8. [현재 버전의 제한 사항](#8-현재-버전의-제한-사항)

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

# YCB mug 에셋 다운로드 (~62MB)
python scripts/download_ycb.py
```

### 1.3 서버 실행

```bash
cd src/
python app/main.py --mesh assets/ycb/025_mug/google_512k/nontextured.ply
```

실행하면 아래와 같은 메시지가 나옵니다:

```
==================================================
 Affordance Labeller
 http://localhost:8080
==================================================
[main] 서버 실행 중... (Ctrl+C로 종료)
```

### 1.4 브라우저 접속

웹 브라우저에서 **http://localhost:8080** 에 접속합니다.
- 3D 뷰포트에 회색 머그컵 메시가 표시됩니다.
- 오른쪽 사이드패널에 라벨링 UI가 표시됩니다.

### 1.5 3D 뷰포트 조작

| 조작 | 동작 |
|------|------|
| 마우스 왼쪽 드래그 | 회전 (orbit) |
| 마우스 오른쪽 드래그 | 이동 (pan) |
| 스크롤 | 줌 인/아웃 |

### 1.6 서버 종료

- 브라우저 사이드패널 **File → Quit Server** 버튼 클릭
- 또는 다른 터미널에서: `kill $(lsof -ti:8080)`

> **참고**: Ctrl+C는 Viser 서버 특성상 동작하지 않을 수 있습니다.

---

## 2. 화면 구성

브라우저 접속 시 화면은 크게 두 영역으로 나뉩니다:

```
┌─────────────────────────────┬──────────────────┐
│                             │  사이드패널 (UI)  │
│     3D 뷰포트               │                  │
│     (머그컵 메시)            │  ┌─ Object Info  │
│                             │  ├─ Canonical Frame│
│                             │  ├─ Parts         │
│                             │  ├─ Affordances   │
│                             │  ├─ Contact Masks │
│                             │  ├─ Candidate Poses│
│                             │  └─ File          │
└─────────────────────────────┴──────────────────┘
```

### 사이드패널 폴더 설명

| 폴더 | 역할 |
|------|------|
| **Object Info** | 객체 ID, 입력 유형, 작성자, 검수 상태 |
| **Canonical Frame** | 정규 좌표계 원점 설정 |
| **Parts** | 메시를 의미 단위(body, handle, rim, base)로 분류 |
| **Affordances** | 각 part에 "이 부분으로 무엇을 할 수 있는가" 라벨 부여 |
| **Contact Masks** | 로봇 손가락이 닿는 접촉 영역 지정 |
| **Candidate Poses** | 파지/조작 시 로봇 손의 6D 위치 추가 |
| **File** | 저장 / 로드 / 검증 / 서버 종료 |

---

## 3. 라벨링 워크플로우

라벨링은 아래 5단계를 **순서대로** 진행합니다.

```
Step 1         Step 2           Step 3            Step 4          Step 5
Part 분류  →  Affordance 할당  →  Contact Mask  →  Pose 추가  →  저장
```

---

### Step 1: Part 자동 분류

**목적**: 머그컵 메시를 의미 있는 부위(body, handle, rim, base)로 나눕니다.

**조작 방법**:

1. 사이드패널에서 **Parts** 폴더를 엽니다.
2. (선택) 슬라이더로 분류 기준을 조정합니다:
   - **Handle Ratio** (기본 1.3): 값이 클수록 handle 영역이 줄어듭니다.
   - **Rim %** (기본 0.06): 값이 클수록 rim 영역이 넓어집니다.
   - **Base %** (기본 0.03): 값이 클수록 base 영역이 넓어집니다.
3. **Auto Segment (geometry)** 버튼을 클릭합니다.
4. 메시가 4가지 색상으로 칠해집니다:

| Part | 색상 | 설명 |
|------|------|------|
| body | 보라 | 컵 몸체 |
| handle | 초록 | 손잡이 |
| rim | 노랑 | 입구 테두리 |
| base | 회색 | 바닥면 |

5. Parts 폴더 하단에 각 part의 vertex 수가 표시됩니다.

**팁**: 슬라이더를 조정한 후 **Auto Segment** 를 다시 누르면 새 기준으로 재분류됩니다.

> **중요**: 이후 모든 라벨링(Affordance, Contact Mask)은 이 Part 분류 결과를 기반으로 합니다. Part 분류를 먼저 수행하세요.

---

### Step 2: Affordance 할당

**목적**: 각 part에 "이 부분이 어떤 조작을 지원하는가" (affordance)를 부여합니다.

**조작 방법**:

1. **Affordances** 폴더를 엽니다.
2. **Target Part** 드롭다운에서 대상 part를 선택합니다 (예: `handle`).
3. **Affordance Class** 드롭다운에서 어포던스 유형을 선택합니다.
4. **Semantic Tag** 드롭다운에서 구체적인 동작 태그를 선택합니다.
5. **Assign Affordance** 버튼을 클릭합니다.
6. 해당 part 영역의 색상이 변경되며, 하단에 할당 정보가 표시됩니다.

**Affordance Class 종류**:

| Class | 의미 | 색상 | 주로 사용되는 Part |
|-------|------|------|-------------------|
| graspable | 파지 가능한 영역 | 초록 | handle |
| pour_support | 따르기 동작 지지 영역 | 파랑 | rim |
| handover_region | 핸드오버(전달) 영역 | 주황 | body |
| placeable | 놓기 가능한 영역 | 보라 | base |
| non_affordance | 비기능 영역 | 회색 | - |

**Semantic Tag 종류**:

| Tag | 의미 |
|-----|------|
| pick_up | 들어올리기 |
| pour_ready | 따르기 준비 |
| handover_ready | 전달 준비 |
| reposition_only | 위치 재조정만 |
| place_down | 내려놓기 |
| tilt | 기울이기 |

**복수 태그 추가**: 동일한 part + class 조합에 다른 tag를 선택하고 다시 **Assign** 하면 태그가 누적됩니다.

예시: handle에 graspable을 할당한 후, tag를 `handover_ready`로 바꾸고 다시 Assign하면 `[pick_up, handover_ready]` 2개 태그가 됩니다.

**삭제**: **Remove Last Affordance** 버튼으로 마지막에 추가한 affordance를 제거합니다.

---

### Step 3: Contact Mask 지정

**목적**: 로봇 손가락이 닿는 접촉 영역(Patch A, Patch B)을 지정합니다.

**조작 방법**:

1. **Contact Masks** 폴더를 엽니다.
2. **Target Part** 드롭다운에서 대상 part를 선택합니다.
3. **Mask Type** 을 선택합니다.
4. **Patch A (finger)**: 한쪽 접촉 영역의 손가락 역할을 선택합니다.
5. **Patch B (finger)**: 반대쪽 접촉 영역의 손가락 역할을 선택합니다.
6. **Assign Contact Mask** 버튼을 클릭합니다.
7. 해당 part가 빨강/파랑 두 영역으로 표시됩니다.

**Mask Type 종류**:

| Type | 의미 | 권장 Part |
|------|------|----------|
| handle_pinch | 손잡이 핀치 그립 | handle |
| body_power | 몸체 파워 그립 | body |
| rim_control | 림 컨트롤 그립 | rim |
| custom | 사용자 정의 | 모든 part |

**Finger Role 종류**:

| Role | 의미 |
|------|------|
| thumb | 엄지 |
| index | 검지 |
| index_middle | 검지~중지 |
| palm | 손바닥 |
| all_fingers | 모든 손가락 |

**색상 의미**:
- **빨강 (Patch A)**: 주로 엄지 쪽 접촉 영역
- **파랑 (Patch B)**: 주로 나머지 손가락 쪽 접촉 영역

> **참고**: 현재 버전에서는 Patch A/B가 해당 part의 vertex를 절반씩 자동 분할합니다. 정밀한 접촉 영역 편집은 다음 버전에서 지원 예정입니다.

---

### Step 4: Candidate Pose 추가

**목적**: 로봇 손이 객체를 잡거나 조작할 때의 3D 위치(pose)를 지정합니다.

**조작 방법**:

1. **Candidate Poses** 폴더를 엽니다.
2. **Pose Name**: 의미 있는 이름을 입력합니다 (예: `handle_top_pinch`).
3. **Position**: x, y, z 좌표를 입력합니다 (단위: 미터).
   - 3D 뷰포트의 좌표축 프레임을 참고하여 위치를 설정합니다.
   - 화살표 버튼 또는 직접 입력으로 조정합니다.
4. **Grasp Type**: 파지 유형을 선택합니다.
5. **Hand Role**: 어느 손인지 선택합니다.
6. **Link Affordance**: 이 pose와 연결할 affordance를 선택합니다.
7. **Link Mask**: 이 pose와 연결할 contact mask를 선택합니다.
8. **Add Pose** 버튼을 클릭합니다.
9. 3D 뷰포트에 좌표축 프레임(RGB 축)이 표시됩니다.

**Grasp Type 종류**:

| Type | 의미 | 설명 |
|------|------|------|
| pinch | 핀치 그립 | 엄지+검지로 집기 |
| power | 파워 그립 | 손 전체로 감싸 잡기 |
| lateral | 측면 그립 | 엄지 측면으로 잡기 |
| hook | 훅 그립 | 손가락을 걸어 잡기 |
| precision | 정밀 그립 | 손가락 끝으로 잡기 |
| custom | 사용자 정의 | - |

**Hand Role**:
- `right`: 오른손
- `left`: 왼손
- `either`: 양손 어느 쪽이든 가능

> **참고**: 현재 버전에서는 pose의 회전(orientation)은 기본값(identity)으로 고정됩니다. 회전 편집은 다음 버전에서 지원 예정입니다.

---

### Step 5: 저장

**조작 방법**:

1. **Object Info** 폴더에서 아래 정보를 확인/수정합니다:
   - **Object ID**: 객체 식별자 (예: `ycb_025_mug`) — 이 값이 파일명이 됩니다.
   - **Annotator**: 작성자 이름
   - **Review Status**: `draft` (초안) → 라벨링 완료 후 `reviewed`로 변경
2. **File** 폴더에서 **Save Label** 버튼을 클릭합니다.
3. 저장 결과가 File 섹션 하단에 표시됩니다:
   - **Saved: ycb_025_mug.json ✓** — 정상 저장 + validation 통과
   - **Saved: ... ⚠ N errors, M warnings** — 저장은 되었지만 경고 있음

**저장 위치**: `src/labels/{object_id}.json`

**Validate 버튼**: 저장 없이 현재 라벨의 유효성만 검사합니다.

---

## 4. 기존 라벨 로드 및 검수

### 4.1 서버 시작 시 라벨 로드

```bash
python app/main.py \
  --mesh assets/ycb/025_mug/google_512k/nontextured.ply \
  --label labels/sample_handle_grasp.json
```

`--label` 옵션으로 기존 라벨을 지정하면, 서버 시작 시 자동으로:
- Part 색상 오버레이 적용
- Affordance 색상 오버레이 적용
- Candidate Pose 좌표축 표시
- 사이드패널에 라벨 정보 반영

### 4.2 실행 중 라벨 로드

1. **Object Info → Object ID** 에 로드할 라벨의 object_id를 입력합니다.
2. **File → Load Label** 버튼을 클릭합니다.
3. 해당 `labels/{object_id}.json` 파일이 로드되고 UI에 반영됩니다.

### 4.3 검수 (Review)

1. 라벨을 로드합니다.
2. 3D 뷰포트에서 색상 오버레이와 pose 위치를 시각적으로 확인합니다.
3. **File → Validate** 버튼으로 데이터 무결성을 검사합니다.
4. 문제가 없으면 **Object Info → Review Status** 를 `reviewed` 또는 `approved`로 변경합니다.
5. **Save Label** 로 저장합니다.

### 4.4 제공된 샘플 라벨

| 파일명 | 내용 |
|--------|------|
| `sample_handle_grasp.json` | handle → graspable [pick_up] + handle_pinch mask + pinch pose |
| `sample_rim_pour.json` | rim → pour_support [pour_ready] + rim_control mask + power pose |
| `sample_body_handover.json` | body → handover_region [handover_ready] + body_power mask + power pose |

---

## 5. 용어 사전

| 용어 | 영문 | 설명 |
|------|------|------|
| 어포던스 | Affordance | 객체의 특정 부위가 제공하는 조작 가능성. "이 부분으로 무엇을 할 수 있는가" |
| 파트 | Part | 객체를 구성하는 의미 단위 (body, handle, rim, base) |
| 접촉 마스크 | Contact Mask | 로봇 손가락이 닿는 표면 영역. Patch A와 Patch B로 구분 |
| 후보 포즈 | Candidate Pose | 파지 또는 조작 동작 시 로봇 손/그리퍼의 6D 위치와 방향 |
| 시맨틱 태그 | Semantic Tag | 어포던스에 부여하는 구체적 동작 의미 (pick_up, pour_ready 등) |
| 파지 유형 | Grasp Type | 잡는 방식의 분류 (pinch, power, lateral 등) |
| 정규 좌표계 | Canonical Frame | 객체 고유의 기준 좌표계. 원점과 축 방향을 정의 |
| 정점 | Vertex | 3D 메시를 구성하는 점. 머그컵은 약 262,000개의 정점으로 구성 |
| 검수 상태 | Review Status | 라벨의 완성도 단계: draft → in_review → reviewed → approved |

---

## 6. 색상 범례

### Part 색상 (Auto Segment 후)

| 색상 | Part | RGB |
|------|------|-----|
| 보라 | body | (150, 150, 200) |
| 초록 | handle | (50, 200, 50) |
| 노랑 | rim | (200, 200, 50) |
| 회색 | base | (100, 100, 100) |

### Affordance 색상 (Assign 후)

| 색상 | Class | RGB |
|------|-------|-----|
| 초록 | graspable | (0, 255, 0) |
| 파랑 | pour_support | (0, 100, 255) |
| 주황 | handover_region | (255, 165, 0) |
| 보라 | placeable | (128, 0, 128) |
| 회색 | non_affordance | (128, 128, 128) |

### Contact Mask 색상 (Assign 후)

| 색상 | 영역 | RGB |
|------|------|-----|
| 빨강 | Patch A (보통 엄지 쪽) | (255, 80, 80) |
| 파랑 | Patch B (보통 나머지 손가락 쪽) | (80, 80, 255) |

### Candidate Pose 좌표축

3D 뷰포트에 표시되는 작은 RGB 좌표축:
- **빨강 축**: X 방향
- **초록 축**: Y 방향
- **파랑 축**: Z 방향

---

## 7. FAQ / 문제 해결

### Q: Auto Segment 버튼을 눌러도 아무 변화가 없습니다.
**A**: 메시가 로드되지 않았을 수 있습니다. 서버 실행 시 `--mesh` 옵션이 올바른지 확인하세요.

### Q: Affordance의 Target Part 드롭다운에 (none)만 있습니다.
**A**: **Parts → Auto Segment** 를 먼저 실행해야 합니다. Part 분류가 완료되어야 드롭다운에 part 목록이 나타납니다.

### Q: Save 했는데 파일이 어디에 저장되었나요?
**A**: `src/labels/{object_id}.json` 경로에 저장됩니다. Object ID 필드의 값이 파일명이 됩니다.

### Q: Load 시 "Not Found" 에러가 뜹니다.
**A**: Object ID 필드에 입력한 이름과 일치하는 JSON 파일이 `src/labels/` 폴더에 있는지 확인하세요.

### Q: 브라우저를 새로고침하면 라벨이 사라집니다.
**A**: 라벨은 서버 메모리에 있으므로, 브라우저 새로고침 시 UI는 초기화됩니다. **반드시 Save를 먼저 한 후**, Load로 다시 불러오세요.

### Q: 서버가 종료되지 않습니다.
**A**: File 폴더의 **Quit Server** 버튼을 사용하거나, 다른 터미널에서 `kill $(lsof -ti:8080)` 을 실행하세요.

### Q: 포트 8080이 이미 사용 중입니다.
**A**: `--port` 옵션으로 다른 포트를 지정하세요: `python app/main.py --port 9090 --mesh ...`

### Q: 색상이 겹쳐서 구분이 어렵습니다.
**A**: 색상은 레이어 순서로 덮어씌워집니다: Part 색상 → Affordance 색상 → Contact Mask 색상. 가장 마지막에 적용된 색상이 보입니다.

---

## 8. 현재 버전의 제한 사항

이 문서는 **v0.1 (MVP)** 기준이며, 아래 제한 사항이 있습니다:

| 항목 | 현재 상태 | 다음 버전 예정 |
|------|----------|---------------|
| 대상 객체 | YCB 025_mug만 지원 | 범용 객체 확장 |
| Part 분류 | 머그컵 전용 기하학 규칙 | SAM 등 범용 분할 |
| Affordance 선택 | Part 단위 할당만 가능 | Vertex 단위 브러시/클릭 선택 |
| Contact Patch A/B | Vertex 절반 자동 분할 | 수동 영역 선택/편집 |
| Pose 회전 | Identity quaternion 고정 | 드래그 회전 편집 |
| JSON 크기 | vertex_indices 포함 시 4~9MB | 바이너리 분리 저장 |
| 동시 편집 | 단일 사용자만 지원 | 다중 annotator |
| Export | JSON v0.1만 지원 | RLDS / LeRobot 변환 |

---

## 빠른 참조: 전체 라벨링 5분 체크리스트

```
□ 서버 실행 (python app/main.py --mesh ...)
□ 브라우저 접속 (http://localhost:8080)
□ Parts → 슬라이더 조정 (선택) → Auto Segment 클릭
□ Affordances → Target Part 선택 → Class + Tag 선택 → Assign
  (필요시 다른 part/class/tag 조합으로 반복)
□ Contact Masks → Target Part 선택 → Mask Type + Patch A/B role → Assign
□ Candidate Poses → 이름 + 위치 입력 → Link Affordance/Mask 선택 → Add Pose
□ Object Info → Annotator 이름 확인, Review Status 설정
□ File → Save Label
□ File → Quit Server
```

---

*이 가이드는 Affordance Labeller v0.1 (2026-03-26) 기준으로 작성되었습니다.*
*다음 페이즈 업데이트 시 본 문서도 함께 갱신됩니다.*
