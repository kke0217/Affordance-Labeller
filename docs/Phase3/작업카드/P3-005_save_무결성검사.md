---
id: P3-005
status: todo
priority: P0
owner: 고광은
workstream: WS02
sprint: Sprint-A
points: 5
dependencies:
  - P3-004
---

# P3-005 Save 시 Bundle 무결성 검사

## 목적
저장 직전 참조 `.npy` 존재 여부, index 비어 있음, 경로 누락, 고아 파일을 검사한다.

## 완료조건(DoD)
- [ ] 누락 .npy 파일 탐지 시 저장 차단 또는 강한 warning
- [ ] 고아 .npy 파일 감지 + 정리 제안
- [ ] 저장 결과 로그를 UI status에 표시
- [ ] manifest와 실제 파일 목록 일치 확인

## 실행 항목
- [ ] io_handler.py save_label에 무결성 검사 추가
- [ ] 고아 파일 탐지 로직 구현
- [ ] UI status에 경고 표시 연동

## 메모


## 결과

