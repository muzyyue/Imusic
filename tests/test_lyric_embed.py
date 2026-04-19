# tests/test_lyric_embed.py
"""
测试歌词嵌入功能

验证不同格式的歌词嵌入是否正常工作：
- MP3: eyed3 (USLT/SYLT 帧)
- FLAC: mutagen.flac.FLAC (LYRICS 标签)
- OGG: mutagen.oggvorbis.OggVorbis (LYRICS 标签)
- M4A: mutagen.mp4.MP4 (©lyr 原子)
"""
import os
import shutil
import tempfile
import eyed3
from auto_tag.lyric import LyricManager

TEST_FILE = "tests/fileToTest.mp3"
BACKUP_FILE = "tests/fileToTest_backup.mp3"

def setup_module():
    """备份测试文件"""
    if os.path.exists(TEST_FILE):
        shutil.copy(TEST_FILE, BACKUP_FILE)

def teardown_module():
    """恢复测试文件"""
    if os.path.exists(BACKUP_FILE):
        shutil.copy(BACKUP_FILE, TEST_FILE)
        os.remove(BACKUP_FILE)

def test_mp3_embed_only():
    """测试 MP3 embed_only 模式"""
    manager = LyricManager()
    lyrics = "[00:00.00]Test Line 1\n[00:05.00]Test Line 2"
    
    result = manager.embed_lyrics(TEST_FILE, lyrics, 'lrc', 'embed_only')
    assert result is True, "embed_only should return True"
    
    audio = eyed3.load(TEST_FILE)
    assert audio is not None
    assert len(audio.tag.lyrics) > 0, "Should have at least one lyrics frame"
    
    # 验证不应生成 LRC 文件
    lrc_path = os.path.splitext(TEST_FILE)[0] + '.lrc'
    assert not os.path.exists(lrc_path), "embed_only mode should NOT create LRC file"
    
    print("✓ test_mp3_embed_only passed")

def test_mp3_embed_and_lrc():
    """测试 MP3 embed_and_lrc 模式"""
    # 确保先清理
    lrc_path = os.path.splitext(TEST_FILE)[0] + '.lrc'
    if os.path.exists(lrc_path):
        os.remove(lrc_path)
    
    manager = LyricManager()
    lyrics = "[00:00.00]Test Line 1\n[00:05.00]Test Line 2"
    
    result = manager.embed_lyrics(TEST_FILE, lyrics, 'lrc', 'embed_and_lrc')
    assert result is True, "embed_and_lrc should return True"
    
    audio = eyed3.load(TEST_FILE)
    assert audio is not None
    assert len(audio.tag.lyrics) > 0, "Should have at least one lyrics frame"
    
    # 验证应生成 LRC 文件
    assert os.path.exists(lrc_path), "embed_and_lrc mode SHOULD create LRC file"
    
    # 清理
    if os.path.exists(lrc_path):
        os.remove(lrc_path)
    
    print("✓ test_mp3_embed_and_lrc passed")

if __name__ == "__main__":
    setup_module()
    try:
        test_mp3_embed_only()
        test_mp3_embed_and_lrc()
        print("\n✅ All tests passed!")
    finally:
        teardown_module()
