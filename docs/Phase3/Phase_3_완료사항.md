---
title: Phase 3 완료사항
status: in_progress
created: 2026-03-27
updated: 2026-03-30
project: Affordance-Labeller
---

# Phase 3 완료사항

## Sprint A — 기반 결정 + 무결성 (완료)

### P3-000b 오브젝트 네이밍 정리 ✅
- `/object/mug` → `/object/mesh` 일반화
- 커밋: `b220d36`

### P3-004 Bundle Manifest 정의 ✅
- `manifest.json` 자동 생성 (version, file_count, sha256 checksum)
- 커밋: `2860152`

### P3-005 Save 무결성 검사 ✅
- 참조 `.npy` 존재 확인, 고아 파일 감지
- 커밋: `2860152`

### P3-006 Load Bundle Validation ✅
- manifest 기반 파일 존재 + checksum 확인
- 커밋: `2860152`

### P3-000 프레임워크 전환 PoC ✅
- **결정: PyVista+Trame으로 전환 Go**
- Custom VTK InteractorStyle: 좌클릭=painting, 우클릭=지우기, Ctrl+드래그=orbit
- 커밋: `eec79f7`

---

## Sprint B — 반자동 보조 (완료)

### P3-001 Part Suggestion PoC ✅
- `auto_segment_generic()`: K-means + 법선 방향 기반 범용 자동 분할
- Clusters 슬라이더 (2~8) + Auto Geometric Segment 버튼
- `source_type: "auto"` provenance 기록
- 커밋: `1ab6a44`

### P3-002 Contact Patch 자동 제안 ✅
- `auto_split_patch()`: PCA 주성분 방향으로 part vertex 자동 양분
- Split Part 선택 → Auto Split → A/B 버튼
- 커밋: `1ab6a44`

### P3-003 Suggestion Provenance ✅
- parts/masks에 `source_type` 필드 (`"auto"` vs `"manual"`)
- UI 표시: 🤖=auto, ✋=manual
- 커밋: `1ab6a44`

### P3-011 Validation 규칙 확장 ✅
- semantic tag + grasp_type 비상식 조합 경고
- part coverage 비율 경고 (vertex 0개)
- mask patch A/B 비어있음 경고
- canonical frame origin 기본값 info
- 커밋: `1ab6a44`

---

## Sprint C — Export + Review (완료)

### P3-013 Review Workflow ✅
- 상태 전환 규칙: `draft → in_review → reviewed → approved`
- 유효하지 않은 전환 차단 (예: draft → approved 불가)
- `reviewed`/`approved` 전환 시 warning도 차단 (parts 없으면 전환 불가)
- `review_history` 이력 자동 기록 (from, to, by, at)
- Set Review 버튼으로 명시적 전환
- 커밋: `b557014`, `751f95e`

### P3-007 Bundle Export/Import ✅
- `export_bundle()`: JSON + .npy + manifest → .zip 압축
- `import_bundle()`: .zip → labels/ 디렉토리에 복원
- UI Export Bundle (.zip) 버튼
- round-trip 테스트 통과
- 커밋: `b557014`

### P3-008 Export Mapping Memo ✅
- 내부 JSON ↔ RLDS/LeRobot 필드 매핑 테이블 문서
- 누락 필드 목록 (episode_id, camera_config 등 → Phase 4에서 추가)
- RLDS/LeRobot export stub 구현은 Phase 4로 이월
- 커밋: `b557014`

---

## Sprint C 이후 추가 구현

### Part Rename + 색상 보존 ✅
- Rename Part: From → To + OK 버튼
- rename 시 기존 색상 유지 (팔레트 인덱스 상속)
- affordance/mask의 part_ref 자동 갱신
- `current_part` 자동 갱신
- 커밋: `7f3faec`

### 3D 범례 (Legend) ✅
- 3D 뷰포트 좌측 상단에 실시간 범례
- Part 색상 + 이름 + vertex 수
- Affordance 할당 시 affordance 색상 + class + semantic tags로 변경
- Contact Mask 할당 시 Patch A(빨강)/B(파랑) + finger_role 추가
- parts/affordance/mask 변경 시 자동 갱신
- 커밋: `7f3faec`, `cdd0c49`

### 선택적 지우기 ✅
- 우클릭: 현재 선택된 part에서만 vertex 제거 (다른 part 보존)
- 커밋: `7f3faec`

### UI 개선 ✅
- 사이드패널 섹션 번호 추가: 1. Object Info → 2. Parts → 3. Affordances → 4. Contact Masks → 5. Poses
- Auto Semantic Segment에서 (mug) 제거
- 커밋: 최신

---

## 현재 Trame 버전 기능 현황

| 기능 | 조작 | 상태 |
|---|---|---|
| Part painting | 좌클릭/드래그 | ✅ |
| Part 선택적 지우기 | 우클릭/드래그 | ✅ |
| Orbit 회전 | Ctrl+드래그 | ✅ |
| Auto Semantic Segment | 버튼 (mug 전용) | ✅ |
| Auto Geometric Segment | K-means + Clusters 슬라이더 | ✅ |
| Part Rename | From → To + OK | ✅ |
| 3D 범례 | 좌측 상단 실시간 갱신 | ✅ |
| Affordance 할당 | 드롭다운 → Assign | ✅ |
| Contact Mask 수동 | Part 기반 Patch A/B 할당 | ✅ |
| Contact Mask Auto Split | PCA 기반 자동 양분 | ✅ |
| Pose 배치 | Place Pose → 표면 클릭 → RGB 좌표축 | ✅ |
| Pose 회전 편집 | Select → Roll/Pitch/Yaw 슬라이더 | ✅ |
| Pose 삭제 | Remove Last (마커 동시 삭제) | ✅ |
| Review workflow | 상태 전환 규칙 + validation 차단 + 이력 | ✅ |
| Save/Load | JSON + .npy + manifest | ✅ |
| Export Bundle | .zip 묶기 | ✅ |
| Provenance | source_type auto/manual + UI 아이콘 | ✅ |
| Validation | jsonschema + 참조 무결성 + 확장 규칙 | ✅ |

---

## Phase 3 종료 조건 — 달성

| 조건 | 상태 |
|------|------|
| 임의 객체에 대해 라벨링 가능 | ✅ |
| 검수(review) 워크플로우 가능 | ✅ |
| zip으로 공유 가능 | ✅ |

Sprint C 완료로 Phase 3는 종료. 단, Import Bundle UI 버튼은 후속 개선 가능 (현재 CLI import 지원).

---

## Sprint D — 품질 개선 트랙 (Phase 3 이후, 별도 진행)

| 카드 | 상태 | 비고 |
|---|---|---|
| P3-012 Confidence Heuristic | todo | 편집량/coverage 기반 점수 |
| P3-014 렌더링 경량화 | todo | Trame 전환으로 일부 해결됨 |
| P3-015 Panel 리팩토링 | todo | main.py 700줄 모듈 분리 |

## Phase 4로 이월

| 카드 | 이유 |
|---|---|
| P3-009 RLDS export stub | 실제 학습 파이프라인 연결 시 구현 |
| P3-010 LeRobot export stub | 동일 |

---

## 실행 명령

```bash
cd src/

# PyVista+Trame 버전 (현재 메인)
python app/main.py --mesh assets/ycb/025_mug/google_512k/nontextured.ply --server

# 다른 객체
python app/main.py --mesh assets/ycb/035_power_drill/google_512k/nontextured.ply --object-id ycb_035_power_drill --server

# 기존 라벨 로드
python app/main.py --mesh assets/ycb/025_mug/google_512k/nontextured.ply --label labels/sample_handle_grasp.json --server
```
