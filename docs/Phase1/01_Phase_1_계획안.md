---
title: "Phase 1: 수동 라벨링 MVP 구축"
tags:
  - phase-1
  - mvp
  - execution-plan
status: completed
created: 2026-03-26
completed: 2026-03-26
---

# Phase 1: 수동 라벨링 MVP 구축

> **상태: 완료** — Gate 1~4 모두 통과 (2026-03-26)

## 문서 목적
이 문서는 1개월 내 구축 예정인 어포던스 라벨링 툴 및 데이터 관리 시스템의 수정 실행계획을 정리한다. 목표는 자동화 완성이 아니라, 학습용 데이터를 실제로 만들고 저장·재로드·검수할 수 있는 최소 동작 체계를 확보하는 것이다.

## 한 줄 결론
**YCB mug 1개 이상에 대해 RGB-D 또는 mesh 입력 기반으로 affordance / contact region mask / candidate 6D grasp-action pose / semantic action tag를 사람이 라벨링하고, 이를 JSON으로 저장·재로드·검수할 수 있는 최소 동작 시스템을 완성한다.**

## 수정 원칙
### 1) 예쁜 제품보다 라벨 생산 가능 상태
성공 기준은 UI 미관이 아니라 실제 라벨 생성 루프가 돌아가느냐이다.

### 2) 실패 확률이 높은 기술 선택지 제거
- PyQt + Open3D 직접 결합은 피한다
- Viser 기반 웹 UI + Open3D 백엔드 구조로 간다

### 3) 독자 포맷은 허용, 고립 포맷은 금지
- 내부 JSON v0.1 사용
- 단, RLDS / LeRobot 변환 가능성을 전제로 설계

### 4) 자동화는 주인공이 아니다
- 이번 달은 수동 라벨링 + 저장/검수 루프가 핵심
- 자동화는 마지막 주에 작은 PoC만 선택적으로 고려

### 5) 데이터셋 확장은 다음 단계
- 이번 달은 YCB mug 중심
- 다음 단계에서 PartNet-Mobility, GSO 등 검토

## 이번 달 최종 목표
1. YCB mug 1개 이상 로드
2. body / handle / rim / interior 표시 또는 수정
3. affordance 영역 지정 및 semantic tag 부여
4. contact region mask 1개 이상 저장
5. candidate pose 1개 이상 저장
6. JSON 저장 / 재로드 / 검수 상태 관리

## 이번 달 범위
### 반드시 구현
- 입력 로더: RGB / Depth / point cloud / mesh
- canonical frame 저장
- part 정의 및 표시
- affordance 수동 라벨링 UI
- contact region mask 지정 UI
- candidate pose 추가 / 삭제 / 선택 UI
- semantic action tag 부여
- JSON 저장 / 재로드
- annotator / review_status / timestamp 관리
- validation 로직

### 이번 달 제외
- 완전 자동 affordance 추출
- Isaac Sim 연동 및 물리 stability 자동 평가
- RLDS / LeRobot 완전 직출력
- 다중 사용자 협업
- DB 백엔드 구축
- 실로봇 연동
- PartNet-Mobility 통합
- 대규모 데이터셋 브라우저
- 복잡한 undo / redo

## 시스템 구성
### 프론트엔드
- Viser 기반 웹 UI
- 4패널 구조
  - 입력 뷰
  - affordance 편집 뷰
  - contact mask 편집 뷰
  - candidate pose 뷰
- 우측 Inspector
- 하단 validation / save status bar

### 백엔드
- Open3D 기반 파일 로드 및 기하 처리
- point cloud / mesh normalization
- canonical frame 저장
- mask / pose / metadata 직렬화

### 저장 구조
- 내부 JSON v0.1
- RLDS / LeRobot 매핑 가능 필드 예약
- 파일 기반 저장

## 실행 우선순위
### P0
1. 기술 스택 전환
2. YCB mug 입력-표시-저장 루프 완성
3. affordance / contact / pose / tag 수동 편집 가능화
4. JSON 재로드 가능화

### P1
1. validation 경고 체계
2. annotator / review workflow
3. 샘플 2~3개 추가
4. export schema 정리

### P2
1. 자동 마스크 초안 제안 PoC
2. RLDS / LeRobot 변환 스크립트 초안
3. PartNet-Mobility 확장 설계

## 4주 상세 일정
### 1주차 — 기술 스택 고정과 입력 루프 확보
- Viser 개발환경 구축
- YCB mug asset 로드
- RGB-D 또는 mesh viewer 띄우기
- canonical frame 임시 저장
- label JSON v0.1 skeleton 생성
- save / reload 버튼 구현

완료 기준:
- mug 하나를 불러와서 화면에 보인다
- JSON 저장 / 재로드가 된다

### 2주차 — affordance와 part 라벨링 구현
- part 표시 및 수동 수정 기능
- affordance brush 또는 polygon 중 1개 구현
- affordance class selector
- semantic tag selector
- 색상 오버레이 렌더링
- 저장 / 재로드 연결

완료 기준:
- handle 영역을 graspable로 칠하고 저장 가능
- 재로드 시 라벨과 태그 복원 가능

### 3주차 — contact mask와 candidate pose 구현
- contact patch A/B 구조 구현
- mask type 정의
- candidate pose 리스트 UI
- pose 추가 / 삭제 / 선택
- 6D pose 축 시각화
- pose-affordance-mask 연결 필드 저장

완료 기준:
- handle_pinch mask 저장 가능
- pose 1개 추가 및 재로드 가능

### 4주차 — 검수, 안정화, 데모 패키징
- review_status 도입
- annotator / updated_at 표시
- 필수 필드 validation
- 저장 실패 / 누락 경고
- 샘플 1~3개 정리
- 데모 시나리오 문서화
- 선택 사항: 단순 자동 제안 PoC 1개

완료 기준:
- 누락 필드 경고 가능
- JSON 재로드 안정화
- 5분 이내 데모 가능

## 의사결정 게이트
- Gate 1: mug 로드 + JSON 저장/재로드
- Gate 2: affordance + semantic tag 저장
- Gate 3: contact mask + pose 저장
- Gate 4: 검수 상태 포함 데모 성공

## 연결 문서
- [[프로젝트_개요]]
- [[02_Phase_2_계획안]] — 다음 단계
- [[데이터_스키마_초안]]
- [[Phase_1_일별_실행기록]]
