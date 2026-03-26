---
title: Claude Code 이관 가이드
tags:
  - claude-code
  - setup
status: active
created: 2026-03-26
---

# Claude Code 이관 가이드

## 이관 준비물
이 프로젝트는 Cowork 모드에서 기본 구조가 만들어졌으며, Claude Code에서 실제 개발을 이어서 진행합니다.

## Step 1: 프로젝트 폴더로 이동
```bash
# 터미널에서 프로젝트 폴더로 이동
cd /path/to/Affordance_Labeller
```

## Step 2: Claude Code 시작
```bash
# Claude Code 실행 (프로젝트 루트에서)
claude

# 또는 특정 디렉토리 지정
claude --directory /path/to/Affordance_Labeller
```

Claude Code가 시작되면 **CLAUDE.md**를 자동으로 읽어서 프로젝트 컨텍스트를 파악합니다.

## Step 3: 첫 번째 명령어
Claude Code에 진입하면 아래 순서로 작업을 요청하세요:

### 3-1. 환경 설치
```
src/ 폴더로 가서 setup_env.sh를 실행해서 환경을 설치해줘
```

### 3-2. YCB 다운로드
```
download_ycb.py를 실행해서 YCB mug 에셋을 받아줘
```

### 3-3. 첫 실행 테스트
```
main.py를 실행해서 Viser 서버가 정상 동작하는지 확인해줘
```

### 3-4. Day별 작업 진행
```
docs/06_1인_일별_실행계획.md를 참고해서 오늘(Day X) 작업을 진행해줘
```

## Step 4: 일상적 작업 패턴

### 새 기능 구현 시
```
[기능 설명]을 구현해줘. 06_1인_일별_실행계획.md의 Day X에 해당하는 작업이야.
```

### 버그 수정 시
```
[문제 상황]이 발생해. src/app/[파일명].py를 확인해서 수정해줘.
```

### 게이트 체크 시
```
Gate [번호] 체크를 해줘. 판정 기준은 06_1인_일별_실행계획.md에 있어.
```

### JSON 스키마 관련
```
schemas/label_v0.1.json 스키마를 확인해서 [작업]해줘.
주의: 스키마 필드 변경은 주간 리뷰에서만 허용이야.
```

## CLAUDE.md의 역할
프로젝트 루트의 `CLAUDE.md`는 Claude Code가 자동으로 읽는 컨텍스트 파일입니다.

이 파일에는 다음이 포함되어 있습니다:
- 프로젝트 개요 및 기술 스택
- 디렉토리 구조
- 빌드/실행 명령어
- JSON 스키마 핵심 구조
- 4주 게이트 일정
- 현재 진행 상태 (주기적으로 업데이트 필요)
- 코딩 컨벤션
- 제외 범위

**진행 상태가 바뀔 때마다** CLAUDE.md의 "현재 진행 상태" 섹션을 업데이트하세요:
```
CLAUDE.md의 현재 진행 상태를 업데이트해줘. Gate 1을 통과했어.
```

## 파일 구조 요약

| 경로 | 역할 | Claude Code에서 하는 일 |
|------|------|------------------------|
| `CLAUDE.md` | 프로젝트 컨텍스트 | 자동 로드 (수정 가능) |
| `docs/06_1인_일별_실행계획.md` | 일별 작업 계획 | 참조 (진행 체크) |
| `src/app/main.py` | 메인 진입점 | 기능 추가/수정 |
| `src/app/viewer.py` | 3D 뷰어 | mesh 표시/인터랙션 구현 |
| `src/app/io_handler.py` | JSON I/O | 저장/로드/검증 |
| `src/schemas/label_v0.1.json` | 스키마 정의 | 참조 (주간 리뷰에서만 수정) |
| `src/labels/` | 라벨 저장소 | Save 결과 확인 |
| `src/assets/ycb/` | 3D 에셋 | 다운로드 후 사용 |
| `src/scripts/` | 유틸 스크립트 | 환경설정/다운로드 실행 |

## 연결 문서
- [[00_프로젝트_개요]]
- [[06_1인_일별_실행계획]]
