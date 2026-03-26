---
title: 최종 목표 시스템 vs 현재 구현판(v1.0) 비교표
tags:
  - affordance-labeling
  - comparison
  - mvp
  - robotics
status: active
created: 2026-03-26
---

# 최종 목표 시스템 vs 현재 구현판(v1.0) 비교표

## 문서 목적
이 문서는 연구과제의 최종 목표 시스템과, 현재 GitHub에 구현된 1차 개발 결과물(v1.0)을 같은 기준으로 비교하기 위한 문서다.

비교 대상은 아래 두 가지다.
- 최종 목표 시스템: 연구과제 문서의 “물체의 조작 가능 영역과 대응 행동을 매핑하는 어포던스 라벨링 툴과 데이터 수집 시스템 구축” 파트 [Source](https://www.genspark.ai/api/files/s/cgFLDASq)
- 현재 구현판(v1.0): [Affordance-Labeller](https://github.com/kke0217/Affordance-Labeller) GitHub 저장소 [Source](https://github.com/kke0217/Affordance-Labeller)

---

## 한 줄 비교
최종 목표 시스템은 **물리 검증까지 포함한 연구용 어포던스 라벨 생성·데이터 수집 파이프라인**이었고, 현재 구현판은 **YCB mug 1개 기준의 수동 라벨링 MVP UI + JSON 저장도구**다. [Source](https://www.genspark.ai/api/files/s/cgFLDASq) [Source](https://github.com/kke0217/Affordance-Labeller)

솔직히 말하면, 현재 구현판은 최종 목표 시스템의 앞단 일부를 실제로 만져볼 수 있게 만든 첫 프로토타입에 가깝다. 방향은 이어져 있지만, 아직 같은 단계라고 보긴 어렵다.

---

## 1. 핵심 목적 비교

| 항목 | 최종 목표 시스템 | 현재 구현판 |
|---|---|---|
| 목표 | 조작 가능 영역과 대응 행동을 매핑하고 물리 검증 기반 라벨과 데이터셋 구축 | YCB mug 기준으로 part / affordance / contact mask / pose를 입력하고 JSON 저장 |
| 성격 | 연구 파이프라인 + 데이터 수집 시스템 | 수동 라벨링 UI MVP |
| 최종 지향 | 모방학습 / 강화학습 활용 가능한 범용 데이터 생산 | 단일 예제 중심 인터페이스 검증 |
| 자동화 수준 | 접촉 후보 샘플링, primitive 정의, lift test 기반 자동 검증 포함 | 대부분 수동 입력, 일부 mug 전용 auto segment |
| 범용성 | 로봇 독립적 객체 중심 라벨 생성 지향 | 현재는 mug 특화 프로토타입 |

최종 목표 문서는 단순 라벨링 화면이 아니라 사실상 데이터 생성 공정 전체를 말하고 있었고, 현재 구현판은 그중 사람이 직접 개입하는 인터페이스를 먼저 만든 것이다. 이건 축소 방향으로는 맞지만, 최종 목표를 이미 달성했다고 보기는 어렵다. [Source](https://www.genspark.ai/api/files/s/cgFLDASq) [Source](https://github.com/kke0217/Affordance-Labeller)

---

## 2. 입력과 출력 비교

### 최종 목표 시스템
입력은 RGB-D point cloud 또는 CAD/mesh였고, 출력은 아래 항목까지 포함하는 구조였다.
- affordance map
- contact region mask
- candidate 6D grasp/action pose
- confidence
- physical stability score
- semantic action tag [Source](https://www.genspark.ai/api/files/s/cgFLDASq)

### 현재 구현판
README와 코드 기준으로 현재 구현판은 아래를 실제로 다룬다.
- mesh 입력
- part 분할
- affordance 라벨
- contact mask
- candidate pose
- semantic tag
- JSON 저장 / 로드 / validation [Source](https://github.com/kke0217/Affordance-Labeller) [Source](https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/app/io_handler.py)

### 냉정한 차이
현재 구현판에는 confidence와 physical stability score가 사실상 없다. 즉, 지금은 “어디를 어떻게 잡을지 기록하는 툴”이지, “그 포즈가 얼마나 좋은지 정량적으로 평가하는 시스템”은 아니다. [Source](https://www.genspark.ai/api/files/s/cgFLDASq) [Source](https://github.com/kke0217/Affordance-Labeller)

---

## 3. 처리 파이프라인 비교

### 최종 목표 시스템의 흐름
1. RGB-D / CAD / mesh 입력
2. 표면 분석
3. 접촉 후보 샘플링
4. grasp type별 contact primitive 정의
5. 물리 엔진 기반 lift test
6. 성공 라벨 자동 축적
7. 데이터셋 생성 [Source](https://www.genspark.ai/api/files/s/cgFLDASq)

### 현재 구현판의 흐름
1. YCB mug mesh 로드
2. mug 전용 auto segment
3. affordance class + tag 수동 지정
4. contact mask 수동 지정
5. pose 수동 추가
6. JSON 저장 / 로드 [Source](https://github.com/kke0217/Affordance-Labeller) [Source](https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/app/viewer.py)

### 한 줄 평가
현재 구현판은 최종 목표 파이프라인의 “표면 분석 이후~물리 검증 이전” 구간을 사람이 대신 입력하는 수동 인터페이스에 가깝다. 시작점으로는 맞지만, 최종 목표 시스템의 핵심 차별점이던 physics-based filtering은 아직 빠져 있다. [Source](https://www.genspark.ai/api/files/s/cgFLDASq) [Source](https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/app/main.py)

---

## 4. 자동화 수준 비교

| 항목 | 최종 목표 시스템 | 현재 구현판 |
|---|---|---|
| part 분할 | 기하/표면 기반 자동 후보 생성 가능성 내포 | mug 전용 heuristic auto segment |
| contact 후보 | 자동 샘플링 의도 | 사용자가 직접 지정 |
| pose 생성 | primitive + 안정성 검증 기반 후보 생성 | 사용자가 직접 입력 |
| 안정성 평가 | Lift Test로 자동 판정 | 없음 |
| dataset factory | 대량 생성 방향 | 없음 |

여기서 가장 냉정하게 봐야 할 부분은 auto segment다. 현재 코드의 `auto_segment_mug()`는 범용 분할기가 아니라 머그컵 구조에 맞춘 규칙 기반 분할에 가깝다. 손잡이 돌출, 상단 rim, 하단 base 같은 구조가 있는 물체에만 제한적으로 통할 가능성이 높다. [Source](https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/app/viewer.py)

---

## 5. UI 및 도구 관점 비교

### 현재 구현판이 잘한 점
현재 저장소는 최소한 툴다운 형태를 갖췄다.
- [Viser](https://viser.studio/) 기반 웹 UI
- 폴더형 섹션 구성
- 저장 / 로드 버튼
- 색상 오버레이
- sample label 제공 [Source](https://github.com/kke0217/Affordance-Labeller) [Source](https://viser.studio/)

이건 과제 1차 산출물로 설명하기 좋다. 특히 PyQt 대신 Viser로 전환한 점은 기술 리스크를 줄였다는 점에서 올바른 방향이다. [Source](https://github.com/kke0217/Affordance-Labeller) [Source](https://viser.studio/)

### 아직 부족한 점
하지만 현재는 annotator가 오래 쓰기 좋은 수준이라고 보긴 어렵다.
- 상태관리 전역 변수 의존
- contact patch 초기화가 거칠음
- pose rotation 편집이 빈약함
- mug 이외 객체 일반화 불가
- 데이터셋 브라우징 / 리뷰 워크플로우가 약함 [Source](https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/app/main.py)

즉, 보여주기엔 좋지만, 오래 굴릴 도구라고 말하기는 아직 이르다.

---

## 6. 데이터 스키마 비교

### 최종 목표 시스템
최종 목표 시스템은 라벨 하나가 단순 annotation이 아니라 행동 의미, 접촉 의미, 안정성 의미를 모두 담는 구조를 지향했다. [Source](https://www.genspark.ai/api/files/s/cgFLDASq)

### 현재 구현판
현재 `label_v0.1.json`은 아래 필드를 중심으로 간다.
- schema_version
- object_id
- input_type
- canonical_frame
- parts
- affordances
- annotator
- review_status
- updated_at
- 일부 확장 대비 필드: task_label, downstream_export_ready [Source](https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/schemas/label_v0.1.json)

### 냉정한 평가
이건 나쁘지 않은 출발점이다. 다만 아직은 정적인 단일 라벨 파일 구조라서 RLDS/LeRobot의 episode/step/action/observation 체계와는 거리가 있다. 즉, 확장 가능성은 열어놨지만 아직 확장된 것은 아니다. [Source](https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/schemas/label_v0.1.json) [Source](https://github.com/google-research/rlds) [Source](https://github.com/huggingface/lerobot)

---

## 7. 범용성 비교

### 최종 목표 시스템
문서상으로는 로봇 플랫폼 독립적인 객체 중심 표현을 지향한다. 즉, 특정 로봇 손 모델이 아니라 객체 조작 가능 영역과 행동을 먼저 정의하고, 나중에 로봇별 adapter를 붙일 수 있는 구조를 암시한다. [Source](https://www.genspark.ai/api/files/s/cgFLDASq)

### 현재 구현판
현재 구현판은 로봇 독립적이긴 하지만, 동시에 너무 객체 특화적이다. 정확히는 “로봇 일반화 이전에 객체 일반화가 안 된 상태”다. YCB mug 하나로는 도구 개념 검증은 되지만 범용성은 증명되지 않는다. [Source](https://github.com/kke0217/Affordance-Labeller) [Source](https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/app/viewer.py)

---

## 8. 무엇이 이어졌고, 무엇이 아직 안 이어졌나

### 이어진 것
- 입력: mesh 기반 object-centered workflow
- part / affordance / mask / pose 구조
- semantic tag 저장
- JSON 기반 데이터 관리 초안
- YCB mug 예제로 MVP 검증 [Source](https://github.com/kke0217/Affordance-Labeller) [Source](https://www.genspark.ai/api/files/s/cgFLDASq)

### 아직 안 이어진 것
- confidence 계산
- physical stability score
- 자동 contact candidate sampling
- physics-based lift validation
- 대량 데이터 생성
- 범용 객체 확장
- RLDS / LeRobot export
- 실로봇 / 시뮬레이터 연계 [Source](https://www.genspark.ai/api/files/s/cgFLDASq) [Source](https://github.com/kke0217/Affordance-Labeller)

---

## 9. 구현 상태 총평

### 잘한 점
- 계획 수준에서 멈추지 않고 실제 도구를 구현했다
- Viser 기반으로 기술 리스크를 줄였다
- 저장 / 재로드 / validation까지 포함했다
- 샘플 라벨 3종을 확보했다 [Source](https://github.com/kke0217/Affordance-Labeller)

### 부족한 점
- 구조가 아직 전역 상태와 하드코딩에 많이 의존한다
- mug 전용 규칙 기반 로직이 많다
- patch/pose 입력이 거칠다
- 정량 평가와 자동화가 없다
- 범용 데이터셋 공정으로는 아직 부족하다 [Source](https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/app/main.py) [Source](https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/app/viewer.py)

### 최종 판단
현재 구현판은 “성공적인 첫 프로토타입”이라고는 말할 수 있지만, “안정적인 연구 도구” 또는 “최종 목표 시스템의 완성형”이라고 보기는 어렵다. 가장 정확한 표현은 **최종 비전의 수동 라벨링 프런트엔드 프로토타입을 YCB mug 기준으로 구현한 1차 MVP**라는 정도다. [Source](https://www.genspark.ai/api/files/s/cgFLDASq) [Source](https://github.com/kke0217/Affordance-Labeller)

---

## 10. 회의 / 보고서용 추천 표현
다음 문구가 가장 과장도 적고, 지나치게 위축되지도 않는다.

> 최종 목표로 설정된 어포던스 라벨링 및 데이터 수집 시스템의 전체 비전 중, 1차 개발 단계에서는 YCB mug 단일 예제를 대상으로 part, affordance, contact mask, candidate pose, semantic tag의 생성·저장·재로드가 가능한 수동 라벨링 MVP를 구현하였다. 향후 단계에서 물리 안정성 평가, confidence 산출, 자동 후보 생성, 범용 객체 확장 및 학습 포맷 연계를 고도화할 예정이다. [Source](https://www.genspark.ai/api/files/s/cgFLDASq) [Source](https://github.com/kke0217/Affordance-Labeller)

---

## 참고 링크
- 최종 목표 시스템 문서: https://www.genspark.ai/api/files/s/cgFLDASq
- GitHub 저장소: https://github.com/kke0217/Affordance-Labeller
- README: https://github.com/kke0217/Affordance-Labeller
- main.py: https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/app/main.py
- viewer.py: https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/app/viewer.py
- io_handler.py: https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/app/io_handler.py
- schema: https://raw.githubusercontent.com/kke0217/Affordance-Labeller/main/src/schemas/label_v0.1.json
- Viser: https://viser.studio/
- RLDS: https://github.com/google-research/rlds
- LeRobot: https://github.com/huggingface/lerobot
