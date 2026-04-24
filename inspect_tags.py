# -*- coding: utf-8 -*-
"""
检查 MP3 文件的完整标签状态
验证标签是否被正确覆盖
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import eyed3


def inspect_mp3_tags(file_path: str):
    """
    检查 MP3 文件的所有标签信息

    Args:
        file_path (str): MP3 文件路径
    """
    print("=" * 70)
    print(f"MP3 Tag Inspector: {os.path.basename(file_path)}")
    print("=" * 70)

    if not os.path.exists(file_path):
        print(f"\n[ERROR] File not found: {file_path}")
        return

    print(f"\n[1] File Info")
    print(f"    Path: {file_path}")
    print(f"    Size: {os.path.getsize(file_path):,} bytes")

    # 加载文件
    audio = eyed3.load(file_path)

    if not audio:
        print(f"\n[ERROR] Cannot load MP3 file")
        return

    print(f"\n[2] Audio Info")
    print(f"    Duration: {audio.info.time_secs:.1f}s" if audio.info else "    Duration: N/A")
    print(f"    Bitrate: {audio.info.bit_rate_str}" if audio.info else "    Bitrate: N/A")

    print(f"\n[3] Tag Status")
    if audio.tag is None:
        print(f"    No ID3 tag found")
        return

    tag = audio.tag

    print(f"    Tag version: ID3v{tag.version[0]}.{tag.version[1]}.{tag.version[2]}")

    print(f"\n[4] Basic Tags")
    print(f"    Title:  '{tag.title or '(empty)'}'")
    print(f"    Artist: '{tag.artist or '(empty)'}'")
    print(f"    Album:  '{tag.album or '(empty)'}'")
    print(f"    Year:   {tag.year or '(empty)'}")
    print(f"    Track:  {tag.track_num or '(empty)'}")

    print(f"\n[5] All Frames")
    for frame in tag.frame_set:
        print(f"    {frame}: {tag.frame_set[frame]}")

    print(f"\n[6] Comments")
    if tag.comments:
        for comment in tag.comments:
            print(f"    [{comment.lang}] {comment.text}")
    else:
        print(f"    (no comments)")

    print(f"\n[7] Images")
    if tag.images:
        for img in tag.images:
            print(f"    Type: {img.picture_type}, MIME: {img.mime_type}, Size: {len(img.image_data)} bytes")
    else:
        print(f"    (no images)")


def test_tag_overwrite():
    """测试标签覆盖行为"""

    test_file = r"tests\fixtures\song\Hua Niwang Ling - Yorushika - Hua Niwang Ling.mp3"

    print("\n" + "=" * 70)
    print("TEST: Tag Overwrite Behavior")
    print("=" * 70)

    if not os.path.exists(test_file):
        print(f"\n[ERROR] Test file not found")
        return

    # 读取原始标签
    print(f"\n[1] Original Tags")
    audio = eyed3.load(test_file)
    if audio and audio.tag:
        orig_title = audio.tag.title
        orig_artist = audio.tag.artist
        orig_album = audio.tag.album
        print(f"    Title:  '{orig_title}'")
        print(f"    Artist: '{orig_artist}'")
        print(f"    Album:  '{orig_album}'")

    # 写入新标签
    print(f"\n[2] Writing New Tags")
    new_title = "TEST_TITLE_OVERWRITE"
    new_artist = "TEST_ARTIST_OVERWRITE"
    new_album = "TEST_ALBUM_OVERWRITE"

    print(f"    Title:  '{new_title}'")
    print(f"    Artist: '{new_artist}'")
    print(f"    Album:  '{new_album}'")

    audio.tag.title = new_title
    audio.tag.artist = new_artist
    audio.tag.album = new_album
    audio.tag.save()

    # 重新加载验证
    print(f"\n[3] Verify After Write")
    audio2 = eyed3.load(test_file)
    if audio2 and audio2.tag:
        verify_title = audio2.tag.title
        verify_artist = audio2.tag.artist
        verify_album = audio2.tag.album
        print(f"    Title:  '{verify_title}'")
        print(f"    Artist: '{verify_artist}'")
        print(f"    Album:  '{verify_album}'")

        # 检查是否完全覆盖
        if verify_title == new_title and verify_artist == new_artist and verify_album == new_album:
            print(f"\n[SUCCESS] Tags correctly overwritten!")
        else:
            print(f"\n[FAIL] Tags not correctly overwritten!")

    # 恢复原始标签
    print(f"\n[4] Restoring Original Tags")
    audio2.tag.title = orig_title
    audio2.tag.artist = orig_artist
    audio2.tag.album = orig_album
    audio2.tag.save()
    print(f"    Restored: '{orig_title}' / '{orig_artist}' / '{orig_album}'")


if __name__ == "__main__":
    # 检查测试文件
    test_file = r"tests\fixtures\song\Hua Niwang Ling - Yorushika - Hua Niwang Ling.mp3"
    inspect_mp3_tags(test_file)

    # 测试覆盖行为
    test_tag_overwrite()
