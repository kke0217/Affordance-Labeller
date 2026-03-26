#!/usr/bin/env python3
"""
YCB Object Dataset 다운로드 스크립트
- 025_mug를 기본으로 다운로드
- 추후 다른 객체도 추가 가능

실행: python scripts/download_ycb.py
"""

import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path

# YCB 객체 목록 (필요시 추가)
YCB_OBJECTS = {
    "025_mug": {
        "url": "http://ycb-benchmarks.s3-website-us-east-1.amazonaws.com/data/google/025_mug_google_512k.tgz",
        "description": "YCB Mug - 기본 테스트 객체",
    },
}

# 대체 소스: YCB 공식 사이트가 안 될 경우
YCB_ALTERNATIVE_URLS = {
    "025_mug": [
        "https://ycb-benchmarks.s3.amazonaws.com/data/google/025_mug_google_512k.tgz",
    ]
}

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "ycb"


def download_file(url: str, dest: Path) -> bool:
    """URL에서 파일 다운로드"""
    try:
        print(f"  다운로드 중: {url}")
        print(f"  저장 위치: {dest}")
        urllib.request.urlretrieve(url, str(dest), reporthook=_progress_hook)
        print()  # 줄바꿈
        return True
    except Exception as e:
        print(f"\n  다운로드 실패: {e}")
        return False


def _progress_hook(block_num, block_size, total_size):
    """다운로드 진행률 표시"""
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100, downloaded * 100 / total_size)
        mb_downloaded = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        sys.stdout.write(f"\r  [{percent:5.1f}%] {mb_downloaded:.1f} / {mb_total:.1f} MB")
    else:
        mb_downloaded = downloaded / (1024 * 1024)
        sys.stdout.write(f"\r  {mb_downloaded:.1f} MB 다운로드됨")
    sys.stdout.flush()


def extract_tgz(archive_path: Path, dest_dir: Path):
    """tgz 파일 압축 해제"""
    import tarfile
    print(f"  압축 해제 중: {archive_path}")
    with tarfile.open(str(archive_path), "r:gz") as tar:
        tar.extractall(path=str(dest_dir))
    print(f"  압축 해제 완료: {dest_dir}")


def download_ycb_object(object_id: str):
    """단일 YCB 객체 다운로드"""
    if object_id not in YCB_OBJECTS:
        print(f"  알 수 없는 객체: {object_id}")
        return False

    obj_info = YCB_OBJECTS[object_id]
    obj_dir = ASSETS_DIR / object_id

    # 이미 존재하는지 확인
    if obj_dir.exists() and any(obj_dir.iterdir()):
        print(f"  이미 존재함: {obj_dir}")
        return True

    obj_dir.mkdir(parents=True, exist_ok=True)

    # 다운로드 시도
    archive_name = obj_info["url"].split("/")[-1]
    archive_path = ASSETS_DIR / archive_name

    success = download_file(obj_info["url"], archive_path)

    # 기본 URL 실패 시 대체 URL 시도
    if not success and object_id in YCB_ALTERNATIVE_URLS:
        for alt_url in YCB_ALTERNATIVE_URLS[object_id]:
            print(f"  대체 URL 시도 중...")
            success = download_file(alt_url, archive_path)
            if success:
                break

    if not success:
        print(f"\n  === 자동 다운로드 실패 ===")
        print(f"  수동 다운로드 안내:")
        print(f"  1. https://www.ycbbenchmarks.com/object-models/ 접속")
        print(f"  2. '{object_id}' 검색")
        print(f"  3. Google 512k 버전 다운로드")
        print(f"  4. 압축 해제 후 {obj_dir}/ 에 배치")
        print(f"")
        print(f"  또는 아래 대체 방법 사용:")
        print(f"  pip install ycb-tools  (가능한 경우)")
        print(f"  python -c \"from ycb_tools import fetch; fetch('{object_id}')\"")
        return False

    # 압축 해제
    try:
        extract_tgz(archive_path, obj_dir)
        archive_path.unlink()  # 압축 파일 삭제
    except Exception as e:
        print(f"  압축 해제 실패: {e}")
        print(f"  수동으로 {archive_path}를 {obj_dir}에 압축 해제해주세요.")
        return False

    return True


def verify_assets(object_id: str) -> bool:
    """다운로드된 에셋 검증"""
    obj_dir = ASSETS_DIR / object_id

    # 일반적인 YCB 파일 구조 확인
    expected_patterns = ["*.obj", "*.ply", "*.stl", "*.off", "*.pcd"]

    found_files = []
    for pattern in expected_patterns:
        found_files.extend(list(obj_dir.rglob(pattern)))

    if found_files:
        print(f"  검증 성공: {len(found_files)}개 3D 파일 발견")
        for f in found_files[:5]:
            print(f"    - {f.name}")
        return True
    else:
        print(f"  경고: 3D 파일을 찾을 수 없음. 디렉토리 내용:")
        for f in obj_dir.rglob("*"):
            if f.is_file():
                print(f"    - {f.relative_to(obj_dir)}")
        return False


def main():
    print("==========================================")
    print(" YCB Object 다운로드")
    print("==========================================")

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    for object_id, obj_info in YCB_OBJECTS.items():
        print(f"\n[{object_id}] {obj_info['description']}")
        print("-" * 40)

        success = download_ycb_object(object_id)
        if success:
            verify_assets(object_id)
        print()

    print("==========================================")
    print(" 다운로드 완료!")
    print("==========================================")
    print(f"\n에셋 위치: {ASSETS_DIR.resolve()}")
    print("\n다음 단계:")
    print("  python app/main.py")


if __name__ == "__main__":
    main()
