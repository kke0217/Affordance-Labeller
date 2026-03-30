---
title: Phase 4 완료사항
status: in_progress
created: 2026-03-30
project: Affordance-Labeller
---

# Phase 4 완료사항

## Phase 4 목표

Physics-Verified Affordance Label Extraction — Isaac Sim에서 로봇 손 파지 시 contact/pose/stability를 자동 추출하여 기존 스키마로 저장.

## 3단계 구조

| 단계 | 목표 | 상태 |
|------|------|------|
| P4-A | Physics extraction (VR 없이) | **진행 예정** |
| P4-B | VR demonstration 연동 | 미착수 |
| P4-C | Dataset export + downstream 검증 | 미착수 |

---

## P4-A: Physics-Assisted Label Extraction

### 사전 조사

- [ ] Isaac Sim 설치 + 기본 환경 구성
- [ ] PhysX ContactReporter API 문서 확인
- [ ] 로봇 손 모델 선정 (Allegro / LEAP / Shadow)
- [ ] Isaac Sim에서 YCB mug USD 로드 PoC
- [ ] 스키마 v0.2 설계 (episode_id, robot_config 등)

### 핵심 구현

- [ ] Isaac Sim에서 robot hand + YCB 객체 씬 구성
- [ ] PhysX ContactReporter → 접촉 vertex 추출
- [ ] Hand pose (position + quaternion) 캡처
- [ ] Lift test 자동화 (파지 → 들어올리기 → 성공/실패)
- [ ] Omniverse Extension 기본 구조
- [ ] 기존 io_handler로 JSON + .npy 저장
- [ ] Trame UI에서 생성된 라벨 Load + 검수

### 완료 기준

- [ ] 최소 1개 객체에서 contact + pose + confidence 자동 추출
- [ ] 기존 JSON+.npy 스키마로 저장 성공
- [ ] Trame UI에서 Load + 색상 오버레이 + 검수 가능

---

## P4-B: VR Demonstration (P4-A 완료 후)

(미착수)

---

## P4-C: Dataset Export + Downstream (P4-B 완료 후)

(미착수)

---

## 관련 문서

- [Phase4_실행계획.md](Phase4_실행계획.md) — 상세 아키텍처 + 스키마 확장 + 논문 전략
- [Phase3 완료사항](../Phase3/Phase_3_완료사항.md) — Phase 3 결과
