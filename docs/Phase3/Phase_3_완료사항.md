---
title: Phase 3 완료사항
status: in_progress
created: 2026-03-27
project: Affordance-Labeller
---

# Phase 3 완료사항

## Sprint A — 기반 결정 + 무결성 (완료)

### P3-000b 오브젝트 네이밍 정리 ✅
- `/object/mug` → `/object/mesh` 일반화
- 코드 내 mug 하드코딩 제거 (함수명 `auto_segment_mug`은 mug 전용임을 명시하여 유지)
- 커밋: `b220d36`

### P3-004 Bundle Manifest 정의 ✅
- `manifest.json` 자동 생성 (save_label 시)
- 필드: manifest_version, created_at, file_count, files (상대경로 + size + sha256)
- npy_dir/manifest.json에 저장
- 커밋: `2860152`

### P3-005 Save 무결성 검사 ✅
- 저장 직전 참조 `.npy` 존재 확인
- 고아 `.npy` 파일 감지 (manifest에 없는 파일)
- JSON 내 `vertex_indices_file` 참조 ↔ 실제 파일 대조
- 커밋: `2860152`

### P3-006 Load Bundle Validation ✅
- manifest 기반 파일 존재 + checksum 확인
- `.npy` 파일 누락 시 에러 로그
- v0.1 인라인 JSON 하위 호환 유지
- 커밋: `2860152`

### P3-000 프레임워크 전환 PoC ✅
- **결정: PyVista+Trame으로 전환 Go**
- `main_trame.py` 전체 앱 구현
- Custom VTK InteractorStyle (`PaintInteractorStyle`):
  - 왼쪽 클릭/드래그 = vertex painting (orbit 차단 없음)
  - 오른쪽 클릭/드래그 = vertex 지우기 (eraser)
  - Ctrl+드래그 = full orbit 회전 (yaw만이 아닌 full trackball)
  - 드래그 중 연속 painting 가능 (Viser에서 불가능했던 기능)
- VtkRemoteView 서버 사이드 렌더링
- Vuetify3 사이드패널 (VRow/VCol 레이아웃)
- 커밋: `eec79f7`

---

## Sprint A 이후 추가 구현 사항

### 우클릭 지우기 (Eraser) ✅
- Paint 모드에서 오른쪽 클릭/드래그 → 해당 영역 vertex를 모든 part에서 제거
- 회색(기본색)으로 복원
- 커밋: `24de0dc`

### Pose 배치 (클릭 → RGB 좌표축) ✅
- **Place Pose** → 객체 표면 클릭 → 클릭 위치에 RGB 좌표축 화살표 생성
  - 빨강=X, 초록=Y, 파랑=Z + 중심 흰색 구체
- 연속 배치 가능 (자동 이름 증가: grasp_00, grasp_01, ...)
- **Stop** 버튼으로 배치 모드 종료
- **Remove Last** → pose 데이터 + 3D 마커 동시 삭제

### Pose 회전 편집 (Euler 슬라이더) ✅
- **Select Pose** 드롭다운에서 기존 pose 선택
- **Roll / Pitch / Yaw 슬라이더** (-180°~180°, 5° 단위)
- 슬라이더 조절 시 3D 좌표축 화살표가 **실시간 회전**
- 내부적으로 euler → quaternion 변환하여 `rotation_xyzw`에 저장

---

## 현재 Trame 버전 기능 현황

| 기능 | 조작 | 상태 |
|---|---|---|
| Part painting | 좌클릭/드래그 | ✅ |
| Part 지우기 | 우클릭/드래그 | ✅ |
| Orbit 회전 | Ctrl+드래그 | ✅ |
| Auto Segment (mug) | 버튼 | ✅ |
| Affordance 할당 | 드롭다운 → Assign | ✅ |
| Contact Mask | Part 기반 할당 | ✅ |
| Pose 배치 | Place Pose → 표면 클릭 | ✅ |
| Pose 회전 편집 | Select → Roll/Pitch/Yaw 슬라이더 | ✅ |
| Pose 삭제 | Remove Last (마커 동시 삭제) | ✅ |
| Save/Load | 버튼 (bundle manifest 포함) | ✅ |

## Viser 대비 개선 사항

| 항목 | Viser (Phase 2) | Trame (Phase 3) |
|---|---|---|
| Painting 중 orbit | 불가 (Start/Stop 토글) | **Ctrl+드래그로 동시 가능** |
| 드래그 연속 painting | 불가 (click 1회씩) | **드래그로 연속 painting** |
| 지우기 | 없음 | **우클릭/드래그** |
| Modifier 키 | 감지 불가 | **Ctrl/Shift 감지 가능** |
| Pose 배치 | 기즈모 (Place → Confirm) | **표면 클릭 → 즉시 생성** |
| Pose 회전 | 기즈모 드래그 | **Euler 슬라이더 + 실시간 시각화** |
| 메시 색상 갱신 | remove+re-add (깜빡임) | **point_data 직접 갱신** |

## 미결 사항

- **Pose 축 컨벤션**: RGB 축이 approach/grip/palm 중 어디에 대응하는지 미정의. 로봇 플랫폼 확정 후 결정 예정.
- **Pose gizmo 드래그 회전**: 화살표 끝점 드래그로 직접 회전 편집은 구현 복잡도 대비 효용이 낮아 보류.

---

## 실행 명령

```bash
# Trame 버전 (신규)
cd src/
python app/main_trame.py --mesh assets/ycb/025_mug/google_512k/nontextured.ply --server

# Viser 버전 (이전, 유지)
python app/main.py --mesh assets/ycb/025_mug/google_512k/nontextured.ply
```

## 관련 커밋

| 커밋 | 내용 |
|------|------|
| `b220d36` | P3-000b 네이밍 정리 |
| `2860152` | P3-004/005/006 bundle manifest + 무결성 검증 |
| `eec79f7` | P3-000 PyVista+Trame 전환 |
| `24de0dc` | 우클릭 지우기 + 클릭 pose 배치 |
