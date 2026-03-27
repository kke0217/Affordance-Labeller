# Affordance Labeller 사용자 가이드 (v3.0 — PyVista+Trame)

> 이 문서는 Affordance Labeller를 처음 사용하는 사람이 **설치부터 라벨 저장까지** 독립적으로 수행할 수 있도록 작성되었습니다.

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

---

## 2. 3D 뷰포트 조작

| 조작 | 동작 |
|------|------|
| **Ctrl+왼쪽 드래그** | orbit 회전 |
| **오른쪽 드래그** | 이동 (pan) — Paint 모드가 아닐 때 |
| **스크롤** | 줌 인/아웃 |

> **핵심**: orbit 회전은 항상 **Ctrl+드래그**입니다. 일반 드래그는 painting에 사용됩니다.

---

## 3. 라벨링 워크플로우

```
Part 정의 → Affordance 할당 → Contact Mask → Pose 배치 → 저장
```

### Step 1: Part 정의

#### 방법 A: Auto Segment (mug 전용)
1. 사이드패널 **Auto Segment (mug)** 클릭
2. body(보라), handle(초록), rim(노랑), base(회색) 자동 분류

#### 방법 B: 수동 Part 정의 (범용)
1. **Part Name** 에 이름 입력 (자유 텍스트: grip, trigger, chuck 등)
2. **Add** 클릭
3. **Paint** 클릭 → painting 모드 진입
4. 3D 뷰에서 **왼쪽 클릭/드래그** → 해당 part 색상으로 칠해짐
5. **오른쪽 클릭/드래그** → 칠한 영역 지우기 (회색 복원)
6. **Ctrl+드래그** → orbit 회전 (painting 중에도 가능)
7. **Stop** → painting 모드 종료
8. 다른 part를 추가하려면 Part Name 변경 후 반복

**팁**:
- 한 vertex는 하나의 part에만 속합니다
- Brush 슬라이더로 브러시 크기 조정
- Contact Mask 세분화가 필요하면 `handle_thumb`, `handle_finger` 등으로 part를 나눠 정의

### Step 2: Affordance 할당
1. **Target Part** → **Class** → **Tag** 선택
2. **Assign Affordance** 클릭

| Class | 의미 |
|-------|------|
| graspable | 파지 가능 |
| pour_support | 따르기 지지 |
| handover_region | 전달 영역 |
| placeable | 놓기 가능 |
| non_affordance | 비기능 |

| Tag | 의미 |
|-----|------|
| pick_up | 들어올리기 |
| pour_ready | 따르기 |
| handover_ready | 전달 |
| reposition_only | 재배치 |
| place_down | 내려놓기 |
| tilt | 기울이기 |

### Step 3: Contact Mask 지정
1. **Mask Type** 선택
2. **Patch A Part** + **A finger** 선택 (엄지 쪽)
3. **Patch B Part** + **B finger** 선택 (나머지 손가락 쪽)
4. **Assign Mask** 클릭

접촉 영역을 세분화하려면 Step 1에서 part를 미리 나눠 정의하세요.

### Step 4: Pose 배치
1. Pose Name, Grasp Type, Hand, Link Affordance/Mask 설정
2. **Place Pose** 클릭 → pose 배치 모드
3. **객체 표면 클릭** → 클릭 위치에 RGB 좌표축 화살표 생성
   - 빨강=X, 초록=Y, 파랑=Z
   - 연속 클릭으로 여러 pose 배치 가능 (자동 번호 증가)
4. **Stop** → pose 배치 모드 종료

#### Pose 회전 편집
1. **Select Pose** 드롭다운에서 편집할 pose 선택
2. **Roll / Pitch / Yaw** 슬라이더 조절 (-180°~180°)
3. 좌표축 화살표가 **실시간으로 회전** → 원하는 파지 방향 설정

#### Pose 삭제
- **Remove Last** → 마지막 pose + 3D 마커 동시 삭제

### Step 5: 저장
1. Object ID, Annotator, Review Status 확인
2. **Save** 클릭 → JSON + .npy + manifest.json 자동 생성
3. **Load** → Object ID 기준으로 기존 라벨 로드

---

## 4. 지원 객체

| 객체 | 실행 예시 |
|------|---------|
| YCB Mug | `--mesh assets/ycb/025_mug/google_512k/nontextured.ply` |
| YCB Mustard Bottle | `--mesh assets/ycb/006_mustard_bottle/google_512k/nontextured.ply` |
| YCB Power Drill | `--mesh assets/ycb/035_power_drill/google_512k/nontextured.ply` |
| YCB Banana | `--mesh assets/ycb/011_banana/google_512k/nontextured.ply` |
| 임의 mesh | `--mesh /path/to/object.ply` |

---

## 5. 색상 범례

| 색상 | 의미 |
|------|------|
| 회색 | 미할당 vertex |
| 빨강/초록/파랑/노랑/마젠타/시안/주황/보라 | Part별 자동 할당 색상 (8색 팔레트) |
| 빨강 (Patch) | Contact Mask Patch A (엄지 쪽) |
| 파랑 (Patch) | Contact Mask Patch B (손가락 쪽) |
| RGB 화살표 | Pose 좌표축 (빨=X, 초=Y, 파=Z) |

---

## 6. 저장 구조

```
labels/
├── ycb_025_mug.json              ← 메타데이터 (< 10KB)
└── ycb_025_mug_vertices/
    ├── manifest.json              ← 파일 목록 + checksum
    ├── part_body.npy
    ├── part_handle.npy
    └── ...
```

---

## 7. FAQ

**Q: painting 중 orbit이 안 됩니다.**
A: **Ctrl 키를 누른 상태에서** 드래그하세요.

**Q: 칠한 영역을 지우고 싶습니다.**
A: Paint 모드에서 **오른쪽 클릭/드래그**하면 지워집니다.

**Q: Pose 좌표축을 회전하고 싶습니다.**
A: Stop으로 배치 종료 → **Select Pose** 에서 선택 → Roll/Pitch/Yaw 슬라이더 조절.

**Q: 서버 종료는?**
A: 터미널에서 `Ctrl+C` 또는 `kill $(lsof -ti:8080)`.

---

## 빠른 참조

```
□ python app/main.py --mesh ... --server
□ http://localhost:8080 접속
□ Parts: Add → Paint → 좌클릭=칠하기, 우클릭=지우기, Ctrl+드래그=orbit → Stop
□ Affordances: Target Part → Class + Tag → Assign
□ Contact Masks: Patch A/B Part 선택 → Assign
□ Poses: Place Pose → 표면 클릭 → Stop → Select → Roll/Pitch/Yaw 편집
□ Save
```

---

*Affordance Labeller v3.0 (Phase 3, PyVista+Trame, 2026-03-27)*
