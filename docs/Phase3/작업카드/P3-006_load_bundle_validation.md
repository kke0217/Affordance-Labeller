---
id: P3-006
status: todo
priority: P0
owner: 고광은
workstream: WS02
sprint: Sprint-A
points: 5
dependencies:
  - P3-004
---

# P3-006 Load 시 Bundle Validation

## 목적
load 단계에서 JSON 스키마 검증 외에 bundle 단위 참조 무결성을 함께 검사한다.

## 완료조건(DoD)
- [ ] JSON OK라도 .npy 깨지면 경고/실패 처리
- [ ] manifest 기반 파일 존재 + checksum 확인
- [ ] 검증 결과를 UI status로 노출
- [ ] v0.1 인라인 JSON(하위 호환)도 정상 로드

## 실행 항목
- [ ] io_handler.py load_label에 bundle validation 추가
- [ ] .npy 파일 손상 감지 (np.load 실패 처리)
- [ ] UI status 연동

## 메모


## 결과

