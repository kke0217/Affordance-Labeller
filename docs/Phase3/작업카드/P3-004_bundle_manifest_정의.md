---
id: P3-004
status: todo
priority: P0
owner: 고광은
workstream: WS02
sprint: Sprint-A
points: 5
dependencies: []
---

# P3-004 Bundle Manifest 스키마 정의

## 목적
JSON 본문과 `.npy` 파일 목록, 버전, 상대경로, checksum을 관리하는 manifest 구조를 정의한다.

## 배경
Phase 2에서 vertex_indices를 `.npy`로 분리했으나, JSON과 .npy 간 참조가 깨지기 쉽다. 고아 파일이 남거나, .npy가 누락되어도 감지하지 못한다.

## 완료조건(DoD)
- [ ] manifest.json 예시 파일 작성
- [ ] 최소 필수 필드 정의 (version, files, checksums)
- [ ] bundle 디렉토리 구조 문서화
- [ ] 기존 샘플 라벨에 manifest 생성 테스트

## 실행 항목
- [ ] manifest 스키마 설계
- [ ] io_handler.py에 manifest 생성 함수 추가
- [ ] 기존 save_label에 manifest 자동 생성 연동

## 메모


## 결과

