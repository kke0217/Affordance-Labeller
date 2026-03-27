---
title: Phase 3 옵시디언 실전 운영안
date: 2026-03-27
tags:
  - affordance-labeling
  - phase3
  - obsidian
  - task-management
  - robot-learning
status: active
project: Affordance-Labeller
source_repo: https://github.com/kke0217/Affordance-Labeller
source_doc: https://github.com/kke0217/Affordance-Labeller/blob/main/docs/Phase3_%EA%B0%9C%EB%B0%9C%EC%9A%B0%EC%84%A0%EC%88%9C%EC%9C%84_Jira%ED%8B%B0%EC%BC%93%EC%84%B8%ED%8A%B8.md
related:
  - "[[00_프로젝트_개요]]"
  - "[[01_MVP_수정본_실행계획안]]"
  - "[[05_데이터_스키마_초안]]"
  - "[[06_Phase3_개발우선순위_Jira티켓세트]]"
---

# Phase 3 옵시디언 실전 운영안

## 1. 문서 목적

이 문서는 기존의 `Phase 3 개발 우선순위 + Jira 티켓 세트` 문서를 **Jira 없이 Obsidian만으로 운영 가능한 형태**로 바꾼 실전 운영안이다.

핵심은 단순하다. 굳이 Jira를 억지로 붙여서 관리 포인트를 늘리지 말고, **지금 이미 잘 굴러가는 Obsidian 볼트 안에서 Phase 3를 끝까지 밀 수 있게 구조를 재정리하는 것**이다. 즉, Epic / Ticket / Sprint / Review 같은 개념은 유지하되, 도구만 Jira에서 Obsidian으로 바꿔 담는다. 원본 문서가 제시한 Phase 3 핵심은 유지한다: **프레임워크 전환 검토, 반자동 제안, 저장 무결성, 품질 검증, RLDS/LeRobot export**. [Source](https://github.com/kke0217/Affordance-Labeller/blob/main/docs/Phase3_%EA%B0%9C%EB%B0%9C%EC%9A%B0%EC%84%A0%EC%88%9C%EC%9C%84_Jira%ED%8B%B0%EC%BC%93%EC%84%B8%ED%8A%B8.md)

---

## 2. 왜 Jira 대신 Obsidian으로 가는가

솔직히 말하면, 현재 단계의 Affordance-Labeller는 대규모 협업 제품 개발이 아니라 **연구개발형 소프트웨어 프로젝트**에 가깝다. 이런 경우 Jira는 이슈 상태 관리엔 강하지만, 설계 의도, 실패 이유, 실험 메모, 우회 결정, 비교 근거 같은 연구 맥락을 담기엔 둔하다. 반대로 Obsidian은 맥락 보존에 강하고, 이미 현재 운영 기반이 마련되어 있다.

즉 Phase 3에서는 **Jira식 구조를 흉내 내되, Jira 자체는 쓰지 않는다.** 대신 아래처럼 번역한다.

- Jira Epic → Obsidian **작업축(Workstream) 문서**
- Jira Ticket → Obsidian **작업 카드(Task Note)**
- Sprint Board → Obsidian **주간 실행 보드**
- Review / Status Transition → Obsidian **frontmatter + 체크리스트 + 주간점검 문서**

이 방식이면 복잡도는 덜고, 추적 가능성은 유지할 수 있다.

---

## 3. Phase 3 운영 원칙

### 원칙 1. 문서와 작업을 분리하지 않는다

설계 문서 따로, 실행 이슈 따로, 회의 메모 따로 흩어지면 금방 흐트러진다. Obsidian에서는 하나의 작업 카드 안에 아래를 같이 둔다.

- 왜 이 작업이 필요한지
- 어떤 파일을 건드리는지
- 완료조건이 뭔지
- 막힌 이유가 뭔지
- 다음 액션이 뭔지

### 원칙 2. 상태는 단순하게 유지한다

Status는 아래 6개만 쓴다.

- `idea`
- `todo`
- `doing`
- `blocked`
- `review`
- `done`

괜히 상태를 늘리면 Jira 없이도 Jira처럼 피곤해진다.

### 원칙 3. 작업 크기는 3~5일 안에 끝나는 수준으로 쪼갠다

한 노트가 2주 이상 끌리면 작업 단위가 너무 크다. 그건 Epic이지 Task가 아니다.

### 원칙 4. 주간점검 문서가 최종 진실이다

개별 작업 노트는 흩어질 수 있다. 그래서 매주 1회, 주간점검 문서에서

- 이번 주 완료
- 진행 중
- 막힘
- 다음 주 우선순위

를 반드시 요약한다.

---

## 4. 추천 볼트 구조

아래 폴더 구조를 추천한다.

```text
Phase3/
  00_운영문서/
    00_Phase3_옵시디언_실전운영안.md
    01_Phase3_마스터_대시보드.md
    02_Phase3_주간점검표.md
    03_Phase3_회의록_템플릿.md
  10_작업축/
    WS00_프레임워크전환검토.md
    WS01_반자동어노테이션보조.md
    WS02_데이터무결성_검증.md
    WS03_Downstream_Export.md
    WS04_품질평가_리뷰.md
    WS05_성능개선_리팩토링.md
  20_작업카드/
    P3-000_프레임워크전환PoC.md
    P3-000b_오브젝트네이밍하드코딩제거.md
    P3-001_파트제안PoC.md
    ...
  30_주간로그/
    2026-W13_주간점검.md
    2026-W14_주간점검.md
    ...
  40_회의록/
    2026-03-27_Phase3_킥오프.md
  50_실험로그/
    2026-03-29_PyVista_Trame_PoC.md
    2026-04-02_SAM_멀티뷰_세그멘테이션_메모.md
```

핵심은 세 가지다.

- **작업축 문서**: 큰 흐름 관리
- **작업카드 문서**: 실제 실행 관리
- **주간로그 문서**: 리뷰와 우선순위 재정렬

---

## 5. 문서 타입별 역할

## 5.1 마스터 대시보드

`01_Phase3_마스터_대시보드.md`는 전체 현황판이다. 여기에는 아래만 요약한다.

- 현재 Phase 목표
- 이번 주 우선순위 3개
- blocked 작업
- 진행률 요약
- 작업축 링크
- 최근 주간점검 링크

이 문서를 열면 박사님이 바로 “지금 뭐가 제일 급한지” 보이게 해야 한다.

## 5.2 작업축(Workstream) 문서

Jira Epic에 대응하는 문서다. 예:

- `WS00_프레임워크전환검토`
- `WS01_반자동어노테이션보조`
- `WS02_데이터무결성_검증`
- `WS03_Downstream_Export`
- `WS04_품질평가_리뷰`
- `WS05_성능개선_리팩토링`

이 문서에는 개요, 목표, 포함 작업카드, 의존성, 리스크만 적는다.

## 5.3 작업카드(Task Note)

Jira Ticket 대신 쓰는 핵심 문서다. 하나의 작업카드는 하나의 완료조건을 가진다. 이 문서가 사실상 Jira 이슈 카드 역할을 한다.

## 5.4 주간점검 문서

한 주의 상태를 강제로 정리하는 문서다. 이게 없으면 Obsidian도 그냥 메모장이 된다.

## 5.5 실험로그 문서

PoC, 실패 기록, 비교 실험, 성능 측정은 별도 실험로그로 뺀다. 작업카드에는 핵심 결론만 링크한다.

---

## 6. 작업카드 템플릿

아래 템플릿을 그대로 복사해서 `20_작업카드/` 아래에 저장하면 된다.

```md
---
id: P3-000
status: todo
priority: P0
owner: 박사님
workstream: "[[WS00_프레임워크전환검토]]"
sprint: Sprint-A
due:
points: 13
dependencies: []
related_files: []
related_notes: []
review_status: draft
---

# P3-000 프레임워크 전환 PoC

## 목적
현재 Viser 상호작용 한계가 실제 라벨링 UX 병목인지 검증하고, PyVista+Trame 전환 여부를 결정한다.

## 배경
- painting 중 orbit 불가
- drag painting 불가
- modifier key 감지 불가
- remove + re-add 렌더링 갱신 깜빡임

## 완료조건(DoD)
- [ ] PyVista+Trame에서 mesh 로드 성공
- [ ] click painting + orbit 동시 동작 확인
- [ ] pose gizmo 대체 가능성 확인
- [ ] Viser 대비 장단점 문서화
- [ ] Go / No-Go 결정 기록

## 실행 항목
- [ ] PoC 환경 구성
- [ ] mug mesh 로드 테스트
- [ ] vertex painting 테스트
- [ ] orbit + paint 동시 UX 기록
- [ ] 비교표 작성

## 메모
- 

## 막힘 / 리스크
- 

## 결과
- 

## 다음 액션
- 
```

핵심은 frontmatter다. 나중에 Dataview나 Tasks 플러그인을 쓰면 이게 거의 Jira 필드처럼 작동한다.

---

## 7. 상태 전이 규칙

Jira workflow를 간단히 Obsidian식으로 옮기면 아래와 같다.

### `idea`
아직 착수하지 않은 아이디어. 우선순위 없음.

### `todo`
이번 Phase 범위에 들어왔고, 작업 정의가 끝난 상태.

### `doing`
실제로 손대는 중. 실험로그나 커밋 링크가 최소 하나 있어야 한다.

### `blocked`
외부 의존성, 기술 불확실성, 우선순위 변경으로 멈춘 상태.

### `review`
구현은 끝났고, 스스로 검토하거나 데모/재현 테스트 중.

### `done`
완료조건을 만족했고, 결과가 문서화된 상태.

**규칙:** `done`으로 가기 전에 반드시 아래 3개가 있어야 한다.

- 완료조건 체크 완료
- 결과 요약 3~5줄
- 관련 파일 또는 실험로그 링크 1개 이상

---

## 8. Phase 3 작업축 재편

기존 Jira Epic 구조를 Obsidian 작업축으로 바꾸면 아래와 같다.

## WS00. 프레임워크 전환 검토 + 즉시 수정

목표: Viser 유지 또는 PyVista+Trame 전환을 결정하고, 하드코딩 같은 즉시 수정 가능 항목을 정리한다.

포함 작업:
- `[[P3-000_프레임워크전환PoC]]`
- `[[P3-000b_오브젝트네이밍하드코딩제거]]`

## WS01. 반자동 어노테이션 보조

목표: part / patch 라벨링의 수동 부담을 줄인다.

포함 작업:
- `[[P3-001_파트제안PoC]]`
- `[[P3-002_contact_patch_자동제안PoC]]`
- `[[P3-003_suggestion_provenance_저장]]`

## WS02. 데이터 무결성 + 검증

목표: JSON + `.npy` 구조를 실제 운영 가능한 데이터 묶음으로 만든다.

포함 작업:
- `[[P3-004_bundle_manifest_정의]]`
- `[[P3-005_save_무결성검사]]`
- `[[P3-006_load_bundle_validation]]`
- `[[P3-007_one_click_bundle_export_import]]`

## WS03. Downstream Export

목표: RLDS / LeRobot export 초안을 만든다.

포함 작업:
- `[[P3-008_internalJSON_export_mapping]]`
- `[[P3-009_RLDS_export_stub]]`
- `[[P3-010_LeRobot_export_stub]]`

## WS04. 품질평가 + 리뷰

목표: validation, confidence, review 상태를 강화한다.

포함 작업:
- `[[P3-011_validation_규칙확장]]`
- `[[P3-012_confidence_heuristic_v0]]`
- `[[P3-013_review_workflow_개선]]`

## WS05. 성능개선 + 리팩토링

목표: 렌더링 병목과 패널 구조를 정리한다.

포함 작업:
- `[[P3-014_overlay_렌더링_경량화]]`
- `[[P3-015_panel_책임분리_리팩토링]]`

---

## 9. Jira 티켓을 Obsidian 작업카드로 변환한 목록

아래는 기존 Jira 티켓 세트를 Obsidian 작업카드로 옮긴 표준 목록이다.

### Sprint A

- `P3-000` 프레임워크 전환 PoC
- `P3-000b` 오브젝트 네이밍 하드코딩 제거
- `P3-004` bundle manifest 정의
- `P3-005` save 시 bundle 무결성 검사
- `P3-006` load 시 bundle validation

### Sprint B

- `P3-001` part suggestion PoC
- `P3-002` contact patch 자동 제안 PoC
- `P3-003` suggestion provenance 저장
- `P3-011` validation 규칙 확장

### Sprint C

- `P3-008` internal JSON → export mapping 정의
- `P3-009` RLDS export stub
- `P3-010` LeRobot export stub
- `P3-007` one-click bundle export/import
- `P3-013` review workflow 개선

### Sprint D

- `P3-012` confidence heuristic v0
- `P3-014` overlay 렌더링 경량화
- `P3-015` panel 책임 분리 리팩토링
- `Phase 3 데모 세트 정리`

---

## 10. 주간 운영 루틴

Jira 없이 Obsidian만으로 굴리려면 주간 루틴이 더 중요하다.

## 월요일 20분
- 이번 주 `todo` 중 최우선 3개를 `doing`으로 올림
- blocked 작업이 있으면 원인 한 줄 기록
- 이번 주 종료 목표를 주간점검 문서에 적음

## 수요일 10분
- `doing` 작업이 실제로 진행 중인지 확인
- 3일 넘게 진척 없는 카드가 있으면 쪼개거나 blocked 처리

## 금요일 20분
- 완료된 카드 `done` 처리
- 결과 요약 기록
- 다음 주 넘길 카드 재정리
- 주간점검 문서 작성

이 루틴이 없으면 Jira 안 쓰는 대신 **기억력으로 관리하게 된다.** 그건 위험하다.

---

## 11. 주간점검 문서 템플릿

```md
---
week: 2026-W14
status: active
project: Affordance-Labeller
---

# 2026-W14 Phase 3 주간점검

## 이번 주 목표
- [ ] P3-000 프레임워크 전환 PoC 비교 완료
- [ ] P3-004 manifest 초안 작성
- [ ] P3-005 save 무결성 검사 1차 구현

## 완료
- 

## 진행 중
- 

## 막힘
- 

## 결정사항
- 

## 다음 주 우선순위
1. 
2. 
3. 

## 링크
- 관련 작업축:
- 관련 작업카드:
- 관련 실험로그:
```

---

## 12. 마스터 대시보드 예시

`01_Phase3_마스터_대시보드.md`는 아래처럼 단순해야 한다.

```md
# Phase 3 마스터 대시보드

## 이번 주 최우선
- [[P3-000_프레임워크전환PoC]]
- [[P3-004_bundle_manifest_정의]]
- [[P3-005_save_무결성검사]]

## 작업축
- [[WS00_프레임워크전환검토]]
- [[WS01_반자동어노테이션보조]]
- [[WS02_데이터무결성_검증]]
- [[WS03_Downstream_Export]]
- [[WS04_품질평가_리뷰]]
- [[WS05_성능개선_리팩토링]]

## Blocked
- 

## 최근 주간점검
- [[2026-W14_주간점검]]
```

---

## 13. 플러그인 사용 여부

Obsidian만으로도 운영은 가능하지만, 아래 플러그인은 있으면 편하다.

### 필수는 아님
- **Tasks**: 체크박스 기반 할 일 조회
- **Dataview**: frontmatter 기반 작업 리스트/대시보드
- **Kanban**: 상태별 카드 시각화

하지만 솔직히 말하면, 플러그인부터 늘리면 또 도구 관리가 일이 된다. 처음 2주 정도는 **플러그인 없이 plain markdown + 내부 링크 + 체크리스트**만으로 운영해보고, 그 다음 필요할 때 붙이는 게 낫다.

---

## 14. 지금 당장 하지 말아야 할 것

- Obsidian을 Jira처럼 완전히 흉내 내기
- 상태값 10개 넘게 만들기
- 카드 하나에 작업 여러 개 섞기
- 매일 보드 꾸미기
- Dataview 쿼리 짜느라 시간 쓰기
- 문서 구조보다 플러그인 설정에 시간 쓰기

진짜 중요한 건 시스템이 아니라 **작업이 끝나는 것**이다.

---

## 15. Phase 3 실제 운영 시작 절차

박사님이 지금 바로 시작하려면 이 순서로 가면 된다.

1. `Phase3/` 폴더 생성
2. 이 문서를 `00_운영문서/`에 넣기
3. `WS00~WS05` 작업축 문서 6개 생성
4. Sprint A 작업카드 5개 먼저 생성
5. `01_Phase3_마스터_대시보드.md` 작성
6. 이번 주 주간점검 문서 1개 생성
7. 월/수/금 루틴만 지키기

처음부터 모든 카드 만들 필요 없다. **Sprint A만 먼저 만들고 굴리면서 늘리는 게 맞다.**

---

## 16. 대외/보고용 한 줄 정리

> Phase 3는 Obsidian 기반 운영 체계로 전환하여, 프레임워크 결정·반자동 제안·데이터 무결성·품질 검증·downstream export를 작업축과 주간점검 중심으로 관리한다.

---

## 17. 참고 자료

- 원본 문서: [Phase 3 개발 우선순위 + Jira 티켓 세트](https://github.com/kke0217/Affordance-Labeller/blob/main/docs/Phase3_%EA%B0%9C%EB%B0%9C%EC%9A%B0%EC%84%A0%EC%88%9C%EC%9C%84_Jira%ED%8B%B0%EC%BC%93%EC%84%B8%ED%8A%B8.md)
- Repository: [Affordance-Labeller](https://github.com/kke0217/Affordance-Labeller)
- User Guide: [USER_GUIDE.md](https://github.com/kke0217/Affordance-Labeller/blob/main/docs/USER_GUIDE.md)
- Schema: [label_v0.1.json](https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/schemas/label_v0.1.json)

---

## 18. 결론

박사님 경우엔 지금 Jira를 억지로 붙이는 것보다, **Jira 문서를 Obsidian식 운영 구조로 재해석하는 게 더 현실적**이다. Phase 3에서 필요한 건 더 화려한 관리도구가 아니라, **작업축-작업카드-주간점검** 이 세 축이 흔들리지 않는 운영 리듬이다. 그 리듬만 잡히면 Jira 없이도 충분히 굴릴 수 있다.
