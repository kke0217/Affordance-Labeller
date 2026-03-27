---
title: Phase 3 개발 우선순위 + Jira 티켓 세트
date: 2026-03-27
tags:
  - affordance-labeling
  - phase3
  - jira
  - robot-learning
status: draft
project: Affordance-Labeller
source_repo: https://github.com/kke0217/Affordance-Labeller
related:
  - "[[00_프로젝트_개요]]"
  - "[[01_Phase_1_계획안]]"
  - "[[02_Phase_2_계획안]]"
  - "[[03_데이터_스키마_초안]]"
---

# Phase 3 개발 우선순위 + Jira 티켓 세트

## 1. 문서 목적

이 문서는 Phase 2 완료 상태를 기준으로, **다음 단계에서 실제로 투자할 가치가 있는 개발 항목만 추려서** Phase 3 우선순위와 Jira 티켓으로 정리한 실행 문서다.

Phase 2는 **"범용 3D 객체를 대상으로 한 수동 중심 어포던스 라벨링 도구"**까지 올라왔다. Phase 3의 핵심은 UI를 더 예쁘게 만드는 게 아니라, **이 툴을 데이터 시스템으로 끌어올리는 것 + 상호작용 프레임워크의 근본적 한계를 해결하는 것**이다.

---

## 2. Phase 2 최종 현황 (정확한 상태 반영)

### 구현된 것

- 임의 mesh 형식 로드: `.ply`, `.obj`, `.stl`, `.off`, `.glb`, `.gltf`
- YCB 4종 지원 (mug, mustard_bottle, power_drill, banana) + 임의 mesh
- **click-to-paint 기반 수동 part 정의** (Part Name 자유 텍스트 입력, 8색 팔레트 자동 할당)
- **part 기반 contact mask 할당** (Patch A/B에 기존 정의된 part를 할당하는 방식)
- **TransformControls 기즈모 기반 6D candidate pose** (드래그로 위치+회전 직접 조작)
- 경량 저장: JSON 메타데이터 (< 10KB) + `.npy` vertex 바이너리 분리
- AppState 클래스 + 패널별 모듈 분리 (main.py 90줄)
- jsonschema 검증 + 비즈니스 로직 검증 (참조 무결성, 필수 필드, 연결 관계 등 10개+ 규칙)
- Save 시 자동 validation + 경고 표시
- Auto Segment (mug 전용 기하학 heuristic)

### 확인된 한계

- **Viser 프레임워크 상호작용 한계** (Phase 3의 최대 기술 결정):
  - painting 중 orbit 회전 불가 (pointer event가 orbit을 차단)
  - 드래그 연속 페인팅 불가 (click 1회씩만)
  - modifier 키(Ctrl/Shift) 감지 불가
  - mesh 색상 in-place 업데이트 불가 (remove + re-add 필수, 깜빡임)
- SAM 등 반자동 분할 없음
- confidence / stability 실질적 계산 없음
- RLDS / LeRobot export 미구현
- `.json + .npy` 묶음의 무결성 검증 / 배포 편의성 약함
- `/object/mug` 등 mug 전용 하드코딩 잔재
- schema에서 part name enum 제거되었으나, 스키마 버전 미갱신

---

## 3. Phase 3의 핵심 목표

Phase 3는 5개 축이다:

1. **프레임워크 전환 검토 (Viser → PyVista+Trame)** — 상호작용 UX의 근본적 개선
2. **수동 라벨링 부담을 줄이는 반자동 보조 기능 추가**
3. **저장 포맷을 실제 데이터셋 운영 가능한 수준으로 정리**
4. **라벨 품질 검증 규칙과 최소 정량지표 추가**
5. **RLDS/LeRobot 연동을 위한 export 기반 마련**

---

## 4. 개발 우선순위

## P0. 반드시 해야 하는 것

### P0-0. 프레임워크 전환 검토 (Viser → PyVista+Trame)

Phase 2에서 확인된 가장 심각한 UX 한계는 Viser 프레임워크 자체에서 온다. painting 중 orbit 불가, 드래그 페인팅 불가, modifier 키 미지원은 렌더링 최적화로 해결할 수 없는 구조적 문제다. PyVista+Trame은 VTK 기반으로 이 모든 것을 지원하며, 웹 UI를 유지할 수 있다.

**결정이 필요한 항목**:
- PyVista+Trame PoC를 Sprint A에서 수행할지, 전체 전환을 Phase 3 범위에 넣을지
- 전환 시 AppState, io_handler, viewer 로직은 재사용 가능하나, **UI 패널 코드는 전면 재작성** 필요
- 전환하지 않는다면, Viser 한계를 수용하고 현재 Start/Stop 토글 UX를 유지

### P0-1. 반자동 파트 제안 PoC

가장 큰 라벨링 병목은 사람이 매번 vertex를 클릭으로 칠해야 한다는 점이다. SAM류 반자동 분할은 mesh → 멀티뷰 렌더링 → 2D segmentation → 3D vertex 매핑 파이프라인이 필요하여 난이도가 높다. **초기 후보 제시 + 사용자 수정** 수준이면 충분하다.

### P0-2. 저장 묶음(bundle) 무결성 검증

JSON + `.npy` 분리 저장은 실용적이지만 파일이 깨지기 쉽다. **manifest 생성, 참조 파일 존재 확인, bundle import/export, checksum 검증**이 필요하다.

### P0-3. 라벨 품질 검증 규칙 강화

현재 `io_handler.py`에 jsonschema 검증 + 참조 무결성 + 비즈니스 로직 10개+ 규칙이 **이미 구현되어 있다**. Phase 3에서는 이 위에 추가할 항목:
- semantic tag와 grasp_type 조합 비상식성 warning
- part coverage 비율 경고 (전체 vertex 대비 part 할당률이 너무 낮으면)
- mask patch A/B가 비어 있으면 경고
- canonical frame 누락 시 export 차단

### P0-4. RLDS / LeRobot export 초안

완전 호환이 아닌 **export stub** 수준:
- episode-level metadata placeholder
- object / affordance / pose → flattened export mapping
- downstream_export_ready flag 체크

---

## P1. 있으면 좋은 것

### P1-1. confidence 스코어 초안

- manual = 1.0 고정이 아니라 편집 횟수/수정량 반영
- auto proposal acceptance ratio 반영
- part coverage / patch coherence 기반 rule score

### P1-2. multi-object preset / taxonomy 정리

bottle, bowl, pan, tool, box류별 기본 part scaffold template가 있으면 라벨링 속도가 올라간다.

### P1-3. object naming 하드코딩 정리

`/object/mug` 같은 mug 전용 경로를 범용 `/{object_id}` 로 정리. 즉시 수정 가능한 수준이므로 Sprint A 초기에 처리.

---

## P2. 다음 단계로 미뤄도 되는 것

### P2-1. Isaac Sim lift test

중요하지만 범위가 크다. PoC 수준 설계만 하고 본 구현은 Phase 4로.

### P2-2. 완전 자동 affordance generation

별도 연구 과제 수준. Phase 3에서는 보조 제안까지만.

### P2-3. DB / multi-user / 협업 워크플로

단일 사용자 기준이면 후순위. 로컬 bundle + export가 먼저.

---

## 5. Phase 3 추천 개발 순서

### Sprint A — 기반 결정 + 무결성
- 프레임워크 전환 PoC (Viser vs PyVista+Trame 비교) 또는 Viser 유지 결정
- `/object/mug` 하드코딩 제거 (즉시)
- bundle manifest 구조 정의
- bundle 무결성 검사 (save/load)
- validation 규칙 추가 (기존 10개+ 위에 확장)

### Sprint B — 반자동 보조
- 반자동 part 제안 PoC (SAM 또는 기하학 기반)
- suggestion accept/reject UI
- provenance 메타데이터 저장

### Sprint C — Export + Review
- RLDS/LeRobot export stub
- internal JSON → export mapping 정의
- review workflow 개선 (draft/reviewed/rejected 전환 규칙)

### Sprint D — 품질 + 최적화
- confidence heuristic v0
- 렌더링 경량화 (프레임워크 전환 시 자동 해결 가능)
- 문서화 정리 + Phase 3 데모 세트

---

## 6. Jira Epic 구조

### EPIC-00. Framework Decision & Quick Fixes
목표: Viser 유지 또는 PyVista+Trame 전환을 결정하고, 즉시 수정 가능한 하드코딩을 정리한다.

### EPIC-01. Semi-Automatic Annotation Assist
목표: 수동 칠하기 부담을 줄이고 편집 시간을 줄인다.

### EPIC-02. Data Bundle Integrity & Validation
목표: JSON + `.npy` 저장 구조를 실제 운영 가능한 데이터 묶음으로 만든다.

### EPIC-03. Downstream Export Foundation
목표: RLDS / LeRobot 연동을 위한 최소 export 파이프라인을 만든다.

### EPIC-04. Quality Scoring & Rule-Based Review
목표: confidence, warning, review workflow의 최소 버전을 만든다.

### EPIC-05. Performance & Refactoring
목표: 커지는 mesh/객체 수에 대비한 구조 개선을 한다.

---

## 7. Jira 티켓 세트

## EPIC-00. Framework Decision & Quick Fixes

### AL-P3-000. Viser vs PyVista+Trame 전환 PoC
- **유형**: Spike
- **우선순위**: Highest
- **스토리 포인트**: 13
- **설명**: PyVista+Trame으로 현재 mesh 로드 + vertex painting + pose gizmo 핵심 기능을 PoC 구현하고 Viser와 비교한다. 전환 여부를 결정하는 게이트 역할.
- **비교 기준**: drag painting 가능 여부, orbit 동시 사용, modifier 키, 렌더 성능
- **완료조건(DoD)**:
  - PyVista+Trame에서 mesh 로드 + click painting + orbit 동시 동작 확인
  - Viser 대비 장단점 문서화
  - 전환 Go/No-Go 결정
- **의존성**: 없음

### AL-P3-000b. object naming 하드코딩 제거
- **유형**: Bug Fix
- **우선순위**: Highest
- **스토리 포인트**: 2
- **설명**: `/object/mug` 등 mug 전용 하드코딩을 `/{object_id}` 로 일반화한다.
- **완료조건(DoD)**:
  - mug 외 객체에서도 정상 동작
  - 코드 내 "mug" 문자열 검색 시 주석/설명 외 하드코딩 없음
- **의존성**: 없음

## EPIC-01. Semi-Automatic Annotation Assist

### AL-P3-001. part suggestion PoC 인터페이스 추가
- **유형**: Story
- **우선순위**: Highest
- **스토리 포인트**: 13
- **설명**: mesh → 멀티뷰 렌더링 → SAM 2D segmentation → 3D vertex 매핑, 또는 기하학 기반 클러스터링으로 초기 part 후보를 제안한다. 사용자가 수락/거절/수정 가능한 suggestion flow.
- **산출물**: Suggest button, candidate overlay, accept/reject action
- **완료조건(DoD)**:
  - 사용자가 제안 결과를 보고 수락/거절 가능
  - 기존 수동 페인팅과 충돌 없이 공존
  - 저장 시 최종 선택 결과만 반영
- **의존성**: 없음
- **참고**: SAM 파이프라인은 난이도가 높아 기하학 기반 fallback 포함 권장

### AL-P3-002. contact patch 자동 분할 제안 PoC
- **유형**: Story
- **우선순위**: High
- **스토리 포인트**: 8
- **설명**: 현재 contact mask는 **part 기반 할당 방식** (Part A → Patch A, Part B → Patch B). 이 위에 part의 vertex를 기하학적으로 분석하여 thumb/finger 접촉면 후보를 자동 제안한다. 예: 법선 방향 기반 양면 분할, 또는 curvature 기반 분리.
- **완료조건(DoD)**:
  - 기존 part를 입력으로 받아 Patch A/B 후보 제시
  - accept/reject 후 수동 수정 가능
  - 최소 1개 샘플 object에서 동작 검증
- **의존성**: 없음

### AL-P3-003. suggestion provenance 저장
- **유형**: Task
- **우선순위**: High
- **스토리 포인트**: 3
- **설명**: 라벨이 manual인지, suggestion 기반 수정인지 provenance 메타데이터를 schema에 기록한다.
- **완료조건(DoD)**:
  - JSON에 annotation_source 필드 저장
  - UI에서 provenance 확인 가능
- **의존성**: AL-P3-001, AL-P3-002

## EPIC-02. Data Bundle Integrity & Validation

### AL-P3-004. bundle manifest 스키마 정의
- **유형**: Task
- **우선순위**: Highest
- **스토리 포인트**: 5
- **설명**: JSON 본문과 `.npy` 파일 목록, 버전, 상대경로, checksum을 관리하는 manifest 구조를 정의한다.
- **완료조건(DoD)**:
  - manifest 예시 파일 작성
  - 최소 필수 필드 정의
  - bundle 구조 문서화
- **의존성**: 없음

### AL-P3-005. save 시 bundle 무결성 검사 추가
- **유형**: Story
- **우선순위**: Highest
- **스토리 포인트**: 5
- **설명**: 저장 직전 참조 `.npy` 존재 여부, index 비어 있음, 경로 누락 등을 검사한다. 고아 `.npy` 파일도 감지.
- **완료조건(DoD)**:
  - 누락 파일 탐지 시 저장 차단 또는 강한 warning
  - 고아 파일 감지 + 정리 제안
  - 저장 결과 로그 표시
- **의존성**: AL-P3-004

### AL-P3-006. load 시 bundle validation 추가
- **유형**: Story
- **우선순위**: Highest
- **스토리 포인트**: 5
- **설명**: load 단계에서 JSON 스키마 검증 외에 bundle 단위 참조 무결성을 함께 검사한다.
- **완료조건(DoD)**:
  - JSON OK라도 `.npy` 깨지면 경고/실패 처리
  - 검증 결과를 UI status로 노출
- **의존성**: AL-P3-004

### AL-P3-007. one-click bundle export/import
- **유형**: Story
- **우선순위**: High
- **스토리 포인트**: 5
- **설명**: JSON + `.npy` + manifest를 .zip 또는 폴더째 묶어서 export/import 가능한 기능.
- **완료조건(DoD)**:
  - 단일 명령 또는 UI 액션으로 bundle 저장
  - 재로딩 성공 테스트 포함
- **의존성**: AL-P3-004, AL-P3-005, AL-P3-006

## EPIC-03. Downstream Export Foundation

### AL-P3-008. internal JSON → export mapping 정의
- **유형**: Task
- **우선순위**: Highest
- **스토리 포인트**: 5
- **설명**: 현재 label schema와 RLDS/LeRobot의 episode/step/action/observation 구조 간 매핑 테이블을 정의한다. 누락 필드(episode_id, frame_index, camera_config 등)를 명시.
- **완료조건(DoD)**:
  - field-by-field mapping 문서 존재
  - 누락 필드/placeholder 명시
  - 스키마 확장 필드 제안
- **의존성**: 없음

### AL-P3-009. RLDS export stub 구현
- **유형**: Story
- **우선순위**: High
- **스토리 포인트**: 13
- **설명**: object-level label bundle을 episode-like structure로 감싸는 export 초안. 완전 호환이 아닌 stub.
- **완료조건(DoD)**:
  - 샘플 1건 export 성공
  - metadata placeholder 포함
  - 실패 시 원인 로그 출력
- **의존성**: AL-P3-008

### AL-P3-010. LeRobot export stub 구현
- **유형**: Story
- **우선순위**: High
- **스토리 포인트**: 13
- **설명**: affordance, patch, pose, tag를 downstream friendly table/record 형태로 추출하는 export 초안.
- **완료조건(DoD)**:
  - 샘플 1건 export 성공
  - downstream_export_ready 플래그 반영
- **의존성**: AL-P3-008

## EPIC-04. Quality Scoring & Rule-Based Review

### AL-P3-011. validation 규칙 확장
- **유형**: Story
- **우선순위**: High
- **스토리 포인트**: 5
- **설명**: 기존 io_handler.py의 10개+ 검증 규칙 위에 추가 규칙을 도입한다. 기존 규칙은 이미 jsonschema + part-affordance-mask-pose 참조 무결성 + annotator 체크를 포함.
- **추가할 규칙**:
  - semantic tag + grasp_type 조합 비상식성 warning
  - part coverage 비율 경고 (할당률 < 5%)
  - canonical frame 누락 시 export 차단
  - pose가 mesh bounding box 밖에 있으면 warning
- **완료조건(DoD)**:
  - 기존 규칙과 통합
  - error / warning / info 레벨 분리 (기존 구조 확장)
  - 저장 전 + Validate 버튼에서 모두 수행
- **의존성**: 없음

### AL-P3-012. confidence heuristic v0 구현
- **유형**: Story
- **우선순위**: Medium
- **스토리 포인트**: 5
- **설명**: provenance, 수정량, patch completeness 등을 바탕으로 confidence 초안을 계산한다.
- **완료조건(DoD)**:
  - affordance 또는 pose 단위 confidence 출력
  - 산식 문서화
- **의존성**: AL-P3-003, AL-P3-011

### AL-P3-013. review workflow 개선
- **유형**: Task
- **우선순위**: Medium
- **스토리 포인트**: 3
- **설명**: draft / reviewed / rejected 상태 전환 규칙, reviewer 메타데이터 추가.
- **완료조건(DoD)**:
  - review_status 전환 가능
  - reviewer 메타데이터 저장 가능
- **의존성**: AL-P3-011

## EPIC-05. Performance & Refactoring

### AL-P3-014. overlay 렌더링 경량화
- **유형**: Task
- **우선순위**: Medium
- **스토리 포인트**: 5
- **설명**: mesh remove + re-add 방식의 갱신 구조를 개선한다. 프레임워크 전환(AL-P3-000) 시 자동 해결될 수 있으므로, 전환 결정 후 필요 여부를 재평가.
- **완료조건(DoD)**:
  - 기존 대비 체감 갱신 속도 개선
  - 대형 mesh 1종에서 smoke test
- **의존성**: AL-P3-000 (결정에 따라 불필요할 수 있음)

### AL-P3-015. panel 책임 분리 리팩토링
- **유형**: Story
- **우선순위**: Medium
- **스토리 포인트**: 5
- **설명**: panel 간 refresh 콜백 의존 관계를 정리하고, 이벤트 흐름을 문서화한다.
- **완료조건(DoD)**:
  - 패널 간 refresh 흐름 다이어그램
  - 불필요한 cross-panel 의존 제거
- **의존성**: 없음

---

## 8. 추천 스프린트 배치안

### Sprint A (가장 먼저)
- AL-P3-000 (프레임워크 전환 PoC + 결정)
- AL-P3-000b (하드코딩 제거)
- AL-P3-004 (bundle manifest)
- AL-P3-005, AL-P3-006 (bundle 무결성)

이유: **프레임워크 결정 + 데이터 안 깨지게** 만드는 것이 먼저. 전환 결정이 이후 모든 Sprint에 영향.

### Sprint B
- AL-P3-001 (part suggestion PoC)
- AL-P3-002 (contact patch 자동 분할 제안)
- AL-P3-003 (provenance 저장)
- AL-P3-011 (validation 규칙 확장)

이유: 무결성이 확보된 후 수동 작업량을 줄인다.

### Sprint C
- AL-P3-008 (export mapping)
- AL-P3-009 (RLDS export stub)
- AL-P3-010 (LeRobot export stub)
- AL-P3-007 (bundle export/import)
- AL-P3-013 (review workflow)

이유: 내보내기 구조와 review를 묶어야 downstream 설명이 쉬워진다.

### Sprint D
- AL-P3-012 (confidence heuristic)
- AL-P3-014 (렌더링 최적화 — 전환 여부에 따라 스킵 가능)
- AL-P3-015 (panel 리팩토링)
- 문서화 정리 + Phase 3 데모 세트

이유: scoring과 리팩토링은 앞선 뼈대가 생긴 다음이 낫다.

---

## 9. 당장 하지 말아야 할 것

- 자동 affordance 전부 생성하겠다고 범위 키우기
- Isaac Sim full integration을 Phase 3 핵심으로 잡기
- DB / multi-user / auth부터 붙이기
- UI 미세 꾸미기에 시간 쓰기
- RLDS/LeRobot 완전 호환을 초기 목표로 잡기
- **Viser 한계를 무시하고 workaround만 쌓기** — 근본 원인(프레임워크)을 먼저 결정해야 한다

---

## 10. 대외/보고용 한 줄 정리

> Phase 3에서는 상호작용 프레임워크 전환 검토, 반자동 라벨 제안, 저장 묶음 무결성 검증, 규칙 기반 품질 평가, downstream export 초안 구현을 통해 Affordance-Labeller를 수동 중심 라벨링 프로토타입에서 데이터 생산 시스템으로 확장한다.

---

## 11. 참고 자료

- Repository: [Affordance-Labeller](https://github.com/kke0217/Affordance-Labeller)
- User Guide: [USER_GUIDE.md](https://github.com/kke0217/Affordance-Labeller/blob/main/docs/USER_GUIDE.md)
- Phase 1 계획: [[01_Phase_1_계획안]]
- Phase 2 계획: [[02_Phase_2_계획안]]
- 갭 분석: [[목표시스템_vs_현재구현판(v1.0)_비교]]
- Schema: [label_v0.1.json](https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/schemas/label_v0.1.json)

---

## 12. 결론

Phase 3의 첫 번째 결정은 **Viser를 유지할지 PyVista+Trame으로 전환할지**다. 이 결정이 이후 모든 UI 작업의 방향을 정한다. 그 다음은 **무결성 → 반자동 → export → 품질** 순서로 축을 세운다. 그래야 이 툴이 단순한 3D 라벨링 UI에서 끝나지 않고, 실제로 학습 데이터와 실험 파이프라인으로 이어질 수 있다.
