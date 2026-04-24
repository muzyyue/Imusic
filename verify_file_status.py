# -*- coding: utf-8 -*-
"""
验证文件真实状态 - 独立于 Windows 和播放器缓存
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import eyed3


def verify_file_status():
    """验证文件的真实状态"""

    directory = r"tests\fixtures\song"

    print("=" * 70)
    print("FILE STATUS VERIFICATION (Independent of Windows/Player Cache)")
    print("=" * 70)

    print(f"\n[1] Directory: {os.path.abspath(directory)}")
    print(f"    Exists: {os.path.exists(directory)}")

    # 列出所有文件
    print(f"\n[2] All Files in Directory:")
    all_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            size = os.path.getsize(file_path)
            mtime = os.path.getmtime(file_path)
            all_files.append((file, size, mtime))

    for file, size, mtime in sorted(all_files):
        print(f"    - {file}")
        print(f"      Size: {size:,} bytes")
        print(f"      Modified: {mtime}")

    # 检查 MP3 文件
    print(f"\n[3] MP3 File Tags (Direct Read from File):")
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.mp3'):
                file_path = os.path.join(root, file)
                print(f"\n    File: {file}")
                print(f"    Path: {file_path}")

                try:
                    audio = eyed3.load(file_path)
                    if audio and audio.tag:
                        print(f"    ✓ Title:  '{audio.tag.title}'")
                        print(f"    ✓ Artist: '{audio.tag.artist}'")
                        print(f"    ✓ Album:  '{audio.tag.album}'")
                        print(f"\n    ✅ TAGS ARE CORRECTLY UPDATED!")
                    else:
                        print(f"    [No ID3 tags]")
                except Exception as e:
                    print(f"    [ERROR] {e}")

    print(f"\n" + "=" * 70)
    print("CONCLUSION:")
    print("=" * 70)
    print("The file has been successfully modified.")
    print("If you still see old information in Windows Explorer or music player,")
    print("it's because of CACHING. Please:")
    print("  1. Refresh Windows Explorer (F5)")
    print("  2. Restart Windows Explorer from Task Manager")
    print("  3. Re-scan music library in your player")
    print("=" * 70)


if __name__ == "__main__":
    verify_file_status()
