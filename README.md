# Affordance Labeller

휴머노이드 로봇 양손 파지(bimanual grasping)를 위한 어포던스 라벨링 툴 MVP.

Viser 기반 웹 UI에서 3D 메시를 보면서 part 분류, affordance 라벨링, contact mask 지정, candidate pose 추가를 수행하고, JSON으로 저장/재로드/검수할 수 있습니다.

> **처음 사용하시나요?** [사용자 가이드 (USER_GUIDE.md)](docs/USER_GUIDE.md)를 참고하세요.

![handle_grasp](src/labels/handle_grasp_preview.png)
![rim_pour](src/labels/rim_pour_preview.png)
![body_handover](src/labels/body_handover_preview.png)

## 빠른 시작

```bash
# 1. 환경 설치
cd src/
bash scripts/setup_env.sh

# 2. conda 환경 활성화
conda activate affordance_labeller

# 3. YCB mug 다운로드
python scripts/download_ycb.py

# 4. 실행
python app/main.py --mesh assets/ycb/025_mug/google_512k/nontextured.ply

# 5. 브라우저에서 접속
# http://localhost:8080
```

기존 라벨을 로드하여 시작:
```bash
python app/main.py --mesh assets/ycb/025_mug/google_512k/nontextured.ply --label labels/sample_handle_grasp.json
```

## 라벨링 워크플로우

1. **Auto Segment** — Parts 폴더에서 버튼 클릭 → body/handle/rim/base 자동 분류
2. **Affordance 할당** — Affordances 폴더에서 part 선택 → class + tag 지정 → Assign
3. **Contact Mask** — Contact Masks 폴더에서 part 선택 → mask type + patch A/B role 지정
4. **Candidate Pose** — Candidate Poses 폴더에서 위치/grasp type 입력 → Add Pose
5. **Save** — File 폴더에서 Save Label (자동 validation 포함)
6. **Load** — Object ID 입력 후 Load Label → 색상 오버레이 + 연결 관계 복원

## 기술 스택

| 구성 요소 | 기술 |
|-----------|------|
| 프론트엔드 | [Viser](https://viser.studio/) (웹 기반 3D 뷰어) |
| 3D 처리 | trimesh + Open3D |
| 저장 | JSON v0.1 (자체 스키마, jsonschema 검증) |
| 대상 데이터 | YCB Object Dataset (025_mug) |

## 프로젝트 구조

```
Affordance_Labeller/
├── CLAUDE.md                  # Claude Code 컨텍스트
├── README.md                  # 이 파일
├── docs/                      # 연구 계획 문서 (Obsidian)
└── src/
    ├── app/
    │   ├── main.py            # Viser 서버 + UI (671줄)
    │   ├── viewer.py          # 3D 뷰어 + part 자동 분류 (271줄)
    │   └── io_handler.py      # JSON 저장/로드/검증 (313줄)
    ├── assets/ycb/            # YCB 에셋 (git 제외)
    ├── labels/                # 라벨 JSON + 프리뷰 이미지
    ├── schemas/
    │   └── label_v0.1.json    # JSON 스키마 정의
    └── scripts/
        ├── setup_env.sh       # 환경 설치
        └── download_ycb.py    # YCB 다운로드
```

## JSON 스키마 (v0.1)

```
object_id → parts → affordances → contact_region_masks → candidate_poses
                     ↑ part_ref     ↑ part_ref            ↑ linked_affordance_id
                                                          ↑ linked_mask_id
```

주요 필드: `object_id`, `input_type`, `canonical_frame`, `parts`, `affordances`, `contact_region_masks`, `candidate_poses`, `annotator`, `review_status`, `updated_at`

## 샘플 라벨

| 샘플 | Affordance | Mask | Pose |
|------|-----------|------|------|
| sample_handle_grasp | handle → graspable [pick_up] | handle_pinch (thumb / index_middle) | pinch, right |
| sample_rim_pour | rim → pour_support [pour_ready] | rim_control (thumb / palm) | power, right |
| sample_body_handover | body → handover_region [handover_ready] | body_power (all_fingers / palm) | power, either |

## 색상 범례

| 색상 | 의미 |
|------|------|
| 보라 | body part |
| 초록 | handle part / graspable affordance |
| 노랑 | rim part |
| 회색 | base part |
| 빨강 | Contact Patch A (thumb 쪽) |
| 파랑 | Contact Patch B (fingers 쪽) |

## 개발자

고광은 박사 (로보틱스/컴퓨터비전 연구자)
