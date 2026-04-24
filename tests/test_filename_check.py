import pytest
from auto_tag.audio_recognize import _is_filename_like_song_name


class TestIsFilenameLikeSongName:
    """测试文件名是否像歌曲名的判断逻辑"""

    def test_random_id_filename(self):
        """测试随机ID类文件名（如 32671414_da3-1-30216.mp3）"""
        assert _is_filename_like_song_name("32671414_da3-1-30216.mp3") is False
        assert _is_filename_like_song_name("/path/to/12345_abc-67890.mp3") is False

    def test_numeric_filename(self):
        """测试纯数字或数字主导的文件名"""
        assert _is_filename_like_song_name("123456789.mp3") is False
        assert _is_filename_like_song_name("9876543210.mp3") is False
        assert _is_filename_like_song_name("12345-67890-11111.mp3") is False

    def test_meaningless_keywords(self):
        """测试包含无意义关键词的文件名"""
        assert _is_filename_like_song_name("download_music.mp3") is False
        assert _is_filename_like_song_name("temp_audio_file.mp3") is False
        assert _is_filename_like_song_name("recording_001.mp3") is False
        assert _is_filename_like_song_name("新建文件.mp3") is False
        assert _is_filename_like_song_name("未命名录音.mp3") is False

    def test_too_long_filename(self):
        """测试过长且无分隔符的文件名"""
        long_name = "a" * 60
        assert _is_filename_like_song_name(f"{long_name}.mp3") is False

    def test_special_chars_only(self):
        """测试仅包含特殊字符的文件名"""
        assert _is_filename_like_song_name("!!!@@@###.mp3") is False
        assert _is_filename_like_song_name("---___...mp3") is False

    def test_valid_song_filename_chinese(self):
        """测试有效的中文歌曲文件名"""
        assert _is_filename_like_song_name("周杰伦 - 晴天.mp3") is True
        assert _is_filename_like_song_name("晴天 - 周杰伦.mp3") is True
        assert _is_filename_like_song_name("晴天.mp3") is True

    def test_valid_song_filename_english(self):
        """测试有效的英文歌曲文件名"""
        assert _is_filename_like_song_name("Bohemian Rhapsody - Queen.mp3") is True
        assert _is_filename_like_song_name("Hotel California.mp3") is True
        assert _is_filename_like_song_name("Imagine.mp3") is True

    def test_valid_song_filename_japanese(self):
        """测试有效的日文歌曲文件名"""
        assert _is_filename_like_song_name("花に亡霊 - ヨルシカ.mp3") is True
        assert _is_filename_like_song_name("残酷な天使のテーゼ.mp3") is True

    def test_valid_song_filename_korean(self):
        """测试有效的韩文歌曲文件名"""
        assert _is_filename_like_song_name("Gangnam Style - PSY.mp3") is True
        assert _is_filename_like_song_name("아름다운강산.mp3") is True

    def test_mixed_valid_filename(self):
        """测试混合语言的有效文件名"""
        assert _is_filename_like_song_name("Spring Day - BTS.mp3") is True
        assert _is_filename_like_song_name("Love Story - Taylor Swift.mp3") is True

    def test_empty_filename(self):
        """测试空文件名"""
        assert _is_filename_like_song_name(".mp3") is False

    def test_numbers_in_valid_context(self):
        """测试数字在有效上下文中（如年份、专辑号）"""
        assert _is_filename_like_song_name("2024 New Song.mp3") is True
        assert _is_filename_like_song_name("Track 01 - My Song.mp3") is True
        assert _is_filename_like_song_name("Vol.2 - Best Hits.mp3") is True
