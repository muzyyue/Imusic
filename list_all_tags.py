# -*- coding: utf-8 -*-
"""
列出目录下所有 MP3 文件及其标签信息
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import eyed3


def list_all_mp3_tags(directory: str):
    """
    列出目录下所有 MP3 文件的标签信息

    Args:
        directory (str): 目录路径
    """
    print("=" * 70)
    print(f"MP3 Files in: {directory}")
    print("=" * 70)

    if not os.path.exists(directory):
        print(f"\n[ERROR] Directory not found: {directory}")
        return

    mp3_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.mp3'):
                mp3_files.append(os.path.join(root, file))

    if not mp3_files:
        print(f"\n[INFO] No MP3 files found")
        return

    print(f"\n[Total: {len(mp3_files)} MP3 files]\n")

    for idx, file_path in enumerate(mp3_files, 1):
        print(f"[{idx}] {os.path.basename(file_path)}")
        print(f"    Size: {os.path.getsize(file_path):,} bytes")

        try:
            audio = eyed3.load(file_path)
            if audio and audio.tag:
                print(f"    Title:  '{audio.tag.title or '(empty)'}'")
                print(f"    Artist: '{audio.tag.artist or '(empty)'}'")
                print(f"    Album:  '{audio.tag.album or '(empty)'}'")
            else:
                print(f"    [No ID3 tags]")
        except Exception as e:
            print(f"    [ERROR] {e}")

        print()


if __name__ == "__main__":
    list_all_mp3_tags(r"tests\fixtures\song")
