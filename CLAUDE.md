# Affordance Labeller — 프로젝트 컨텍스트

## 프로젝트 한줄 요약
휴머노이드 로봇 양손 파지(bimanual grasping)를 위한 어포던스 라벨링 툴 MVP. YCB mug 1개를 끝까지 라벨링하고 저장·재로드·검수할 수 있는 체계를 1개월 내 구축한다.

## 개발자
- 1인 개발 (고광은 박사, 로보틱스/컴퓨터비전 연구자)
- 시작일: 2026-03-26
- 마감일: 2026-04-24

## 기술 스택
- **언어**: Python 3.10+
- **프론트엔드**: Viser (웹 기반 3D 뷰어, https://viser.studio/)
- **백엔드**: Open3D + trimesh (3D 처리)
- **저장**: JSON v0.1 (자체 스키마)
- **대상 데이터**: YCB Object Dataset (기본: 025_mug)

## 디렉토리 구조
```
Affordance_Labeller/
├── CLAUDE.md              ← 이 파일 (Claude Code 컨텍스트)
├── docs/                  ← 연구 계획 문서 (Obsidian)
│   ├── 00_프로젝트_개요.md
│   ├── 01_MVP_수정본_실행계획안.md
│   ├── 02_Phase_2_계획안.md    ← Phase 2 실행계획
│   ├── 03_데이터_스키마_초안.md
│   ├── Phase_1_일별_실행기록.md ← Phase 1 실행 기록
│   └── Claude_Code_이관_가이드.md
└── src/                   ← 소스 코드
    ├── app/
    │   ├── main.py        # Viser 서버 진입점 + UI
    │   ├── viewer.py      # 3D 뷰어 래퍼 (mesh 로드/표시/포즈)
    │   ├── io_handler.py  # JSON 저장/로드/검증
    │   └── __init__.py
    ├── assets/ycb/        # YCB 에셋 (git에서 제외, 다운로드 필요)
    ├── labels/            # 라벨 JSON 저장소
    ├── schemas/
    │   └── label_v0.1.json  # JSON 스키마 정의
    ├── scripts/
    │   ├── setup_env.sh     # 환경 설치 스크립트
    │   └── download_ycb.py  # YCB 에셋 다운로드
    ├── tests/
    ├── requirements.txt
    └── .gitignore
```

## 빌드 및 실행
```bash
cd src/
bash scripts/setup_env.sh                   # 환경 설치
python scripts/download_ycb.py              # YCB mug 다운로드
python app/main.py --mesh assets/ycb/025_mug/google_512k/nontextured.ply  # 실행
```

## JSON 스키마 핵심 구조 (v0.1)
최상위 필드: `object_id`, `input_type`, `canonical_frame`, `parts`, `affordances`, `contact_region_masks`, `candidate_poses`, `annotator`, `review_status`, `updated_at`

연결 관계:
- `part` → `affordance` (part_ref로 연결)
- `affordance` → `contact_region_mask` (part_ref 공유)
- `candidate_pose` → `affordance` (linked_affordance_id)
- `candidate_pose` → `mask` (linked_mask_id)

## 4주 게이트 일정
| 게이트 | 내용 | 목표일 | 판정 기준 |
|--------|------|--------|-----------|
| Gate 1 | mug 로드 + JSON 저장/재로드 | 03/29 | Save→Load 시 데이터 보존 |
| Gate 2 | affordance + semantic tag 저장 | 04/04 | handle graspable 라벨 저장/복원 |
| Gate 3 | contact mask + pose 저장 | 04/11 | mask+pose 저장/복원 |
| Gate 4 | 검수 포함 전체 데모 | 04/24 | 5분 이내 데모 성공 |

## 현재 진행 상태
- [x] 프로젝트 구조 생성
- [x] 기본 코드 boilerplate (main.py, viewer.py, io_handler.py)
- [x] JSON 스키마 v0.1 정의
- [x] 샘플 라벨 JSON 작성
- [x] 환경 설치 / YCB 다운로드 스크립트
- [x] **환경 설치 실행** — conda `affordance_labeller`, viser 1.0.24, open3d 0.19.0, trimesh 4.11.5
- [x] **YCB mug 다운로드** — 262k vertices / 524k faces (URL 패턴 수정 완료)
- [x] Viser에서 mug 3D 표시 확인 — add_mesh_trimesh 사용
- [x] Save/Load 동작 테스트 — **Gate 1 통과** (전체 필드 round-trip 보존)
- [x] jsonschema 기반 검증 연동
- [x] canonical frame 설정 UI (origin vector3 + show/hide)
- [x] part 자동 분류 + 색상 오버레이 (auto_segment_mug + threshold 슬라이더)
- [x] affordance 편집 UI (part 기반 할당 + class/tag 드롭다운)
- [x] affordance 색상 오버레이 + Save/Load 복원
- [x] **Gate 2 통과** — handle graspable [pick_up, handover_ready] 저장/복원
- [x] `--label` 시작 시 기존 라벨 색상 복원
- [x] Quit Server 버튼 (kill -9)
- [x] contact mask UI (patch A/B 빨강/파랑 시각화 + Save/Load 복원)
- [x] candidate pose UI (위치/grasp_type/hand_role + 6D 좌표축 표시)
- [x] pose ↔ affordance ↔ mask 연결 드롭다운
- [x] **Gate 3 통과** — mask + pose 저장/복원 + 연결 관계 보존
- [x] Save 시 자동 validation 경고 표시
- [x] 샘플 라벨 3개 완성 + 프리뷰 이미지
- [x] README.md 작성
- [x] **Gate 4 통과** — 전체 데모 가능 (12/12 체크리스트, 4 게이트 모두 통과)

## 코딩 컨벤션
- 한글 주석, 영문 코드 (함수명/변수명은 영어)
- 커밋 메시지: `feat:`, `fix:`, `docs:`, `data:` 접두사
- 에러 메시지는 한글
- `print(f"[모듈명] ...")` 형태로 로그

## 제외 범위 (이번 달에 하지 않는 것)
- 자동 affordance 추출 (SAM 등은 4주차 선택 PoC만)
- Isaac Sim 연동
- RLDS/LeRobot 완전 export (매핑 테이블 정리까지만)
- 다중 사용자 / DB 백엔드
- 실로봇 연동

## 핵심 참조 링크
- YCB Objects: https://www.ycbbenchmarks.com/object-models/
- Viser 문서: https://viser.studio/
- RLDS: https://github.com/google-research/rlds
- LeRobot: https://github.com/huggingface/lerobot

## Claude Code에게
- `docs/02_Phase_2_계획안.md`를 참조하여 현재 Phase에 해당하는 작업을 진행
- 4시간 이상 막히면 우회로를 제안
- Viser API가 불확실하면 https://viser.studio/ 문서를 먼저 확인
- 코드 작성 시 `src/` 디렉토리 안에서 작업
- JSON 스키마 변경은 주간 리뷰에서만 (함부로 필드 추가/삭제 금지)
