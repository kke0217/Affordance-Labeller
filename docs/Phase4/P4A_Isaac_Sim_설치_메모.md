---
title: P4-A Isaac Sim 설치 메모
status: blocked
created: 2026-03-30
---

# P4-A Isaac Sim 설치 메모

## 환경
- kopoter Windows 워크스테이션
- RTX 4090 24GB, 드라이버 591.44
- WSL Ubuntu 22.04, Python 3.10
- C: 2.3TB 여유

## pip 설치 시도 (실패)

```bash
pip install isaacsim==4.5.0.0
pip install isaacsim-extscache-physics isaacsim-extscache-kit isaacsim-extscache-kit-sdk
```

- 패키지 설치 자체는 성공
- **SimulationApp 초기화 실패**: `isaacsim.simulation_app` 모듈 누락
- `expose_api()` → `glob.glob()` → `IndexError: list index out of range`
- 원인: pip 패키지에 `simulation_app` 확장이 포함되지 않음

## 대안

### A. Omniverse Launcher (권장)
- Windows에 Omniverse Launcher 설치
- Isaac Sim을 Launcher에서 설치 (가장 안정적)
- Windows 네이티브 실행 (WSL 아님)
- 다운로드: https://www.nvidia.com/en-us/omniverse/

### B. Docker (WSL에서 GPU 사용)
```bash
docker pull nvcr.io/nvidia/isaac-sim:4.5.0
docker run --gpus all -it nvcr.io/nvidia/isaac-sim:4.5.0
```
- WSL에서 Docker + NVIDIA Container Toolkit 필요
- headless 모드로 실행 가능

### C. pip 재시도 (NVIDIA 공식 가이드 확인)
- https://docs.omniverse.nvidia.com/isaacsim/latest/installation/install_pip.html
- post-install 단계나 추가 패키지가 있을 수 있음

## Windows Workstation 설치 (성공)

- Omniverse Launcher는 2025-10 폐기됨 → **zip 직접 설치**로 진행
- Isaac Sim 5.1.0 Windows workstation zip 다운로드 → `C:\isaacsim`에 압축 해제
- `post_install.bat` 실행
- `isaac-sim.selector.bat` → **Isaac-sim** 선택 → **START**
- **Isaac Sim Full 5.1.0 정상 로드 확인** (RTX Real-Time, Stage, Content 브라우저)

## 최종 환경

| 항목 | 상태 |
|------|------|
| 서버 | kopoter Windows 11 Pro |
| GPU | RTX 4090 24GB |
| RAM | 32GB |
| Isaac Sim | **5.1.0 (workstation zip)** |
| 설치 경로 | `C:\isaacsim` |
| 실행 방식 | `isaac-sim.selector.bat` → START |

## 다음 액션
- [ ] Isaac Sim에서 YCB mug USD 로드 테스트
- [ ] PhysX ContactReporter API 확인
- [ ] P4-A 스크립트 작성 (Mac에서 코드 → GitHub → Windows에서 실행)
