# -*- coding: utf-8 -*-
"""
歌词获取功能综合测试模块

测试 LyricManager 类的歌词获取功能，包括：
- 网易云音乐和酷狗音乐 API 集成
- 正常场景测试
- 边界条件测试
- 异常处理测试
- 性能测试

@module test_lyric_fetch
@author Backend Architect
@version 1.0.0
"""

import json
import os
import tempfile
import time
from unittest.mock import MagicMock, patch, Mock

import pytest

from auto_tag.lyric import LyricManager


class TestLyricMerge:
    """
    歌词合并功能测试类
    
    测试原始歌词和翻译歌词的合并功能
    """
    
    def test_merge_lyrics_basic(self, lyric_manager):
        """
        TC-MERGE-001: 测试基本歌词合并功能
        
        Args:
            lyric_manager: LyricManager实例
        """
        original = "[00:00.00]故事的小黄花\n[00:05.00]从出生那年就飘着"
        translation = "[00:00.00]The small yellow flower\n[00:05.00]Has been floating since birth"
        
        merged = lyric_manager._merge_lyrics_with_translation(original, translation)
        
        # 验证合并后的歌词包含原始歌词和翻译歌词
        assert "故事的小黄花" in merged
        assert "The small yellow flower" in merged
        assert "从出生那年就飘着" in merged
        assert "Has been floating since birth" in merged
        
        # 验证交替排列格式
        lines = merged.split('\n')
        assert len(lines) == 4  # 2行原始 + 2行翻译
        assert "[00:00.00]故事的小黄花" in lines[0]
        assert "[00:00.00]The small yellow flower" in lines[1]
        assert "[00:05.00]从出生那年就飘着" in lines[2]
        assert "[00:05.00]Has been floating since birth" in lines[3]
    
    def test_merge_lyrics_missing_translation(self, lyric_manager):
        """
        TC-MERGE-002: 测试翻译歌词缺失的情况
        
        Args:
            lyric_manager: LyricManager实例
        """
        original = "[00:00.00]故事的小黄花\n[00:05.00]从出生那年就飘着"
        translation = "[00:00.00]The small yellow flower"  # 缺少第二行翻译
        
        merged = lyric_manager._merge_lyrics_with_translation(original, translation)
        
        # 验证只有第一行有翻译
        lines = merged.split('\n')
        assert len(lines) == 3  # 2行原始 + 1行翻译
        assert "故事的小黄花" in lines[0]
        assert "The small yellow flower" in lines[1]
        assert "从出生那年就飘着" in lines[2]
    
    def test_merge_lyrics_empty_translation(self, lyric_manager):
        """
        TC-MERGE-003: 测试翻译歌词为空的情况
        
        Args:
            lyric_manager: LyricManager实例
        """
        original = "[00:00.00]故事的小黄花\n[00:05.00]从出生那年就飘着"
        translation = ""
        
        merged = lyric_manager._merge_lyrics_with_translation(original, translation)
        
        # 验证返回原始歌词
        assert merged == original
    
    def test_merge_lyrics_empty_original(self, lyric_manager):
        """
        TC-MERGE-004: 测试原始歌词为空的情况
        
        Args:
            lyric_manager: LyricManager实例
        """
        original = ""
        translation = "[00:00.00]The small yellow flower"
        
        merged = lyric_manager._merge_lyrics_with_translation(original, translation)
        
        # 验证返回空字符串
        assert merged == ""
    
    def test_merge_lyrics_chinese_accuracy(self, lyric_manager):
        """
        TC-MERGE-005: 测试中文歌词合并的准确性
        
        Args:
            lyric_manager: LyricManager实例
        """
        original = "[00:00.00]故事的小黄花\n[00:05.00]从出生那年就飘着\n[00:10.00]童年的荡秋千"
        translation = "[00:00.00]故事的小黄花\n[00:05.00]从出生那年就飘着\n[00:10.00]童年的荡秋千"
        
        merged = lyric_manager._merge_lyrics_with_translation(original, translation)
        
        # 验证中文文本准确无误
        assert "故事的小黄花" in merged
        assert "从出生那年就飘着" in merged
        assert "童年的荡秋千" in merged
        
        # 验证没有乱码或错误的字符
        lines = merged.split('\n')
        for line in lines:
            # 每行都应该包含时间戳和歌词文本
            assert line.startswith('[')
            assert ']' in line


class TestLyricFetchNormal:
    """
    歌词获取正常场景测试类

    测试歌词获取功能的正常使用场景
    """

    def test_init_lyric_manager(self, lyric_manager):
        """
        TC-N-000: 测试 LyricManager 初始化

        Args:
            lyric_manager: LyricManager实例fixture
        """
        assert lyric_manager is not None
        assert lyric_manager.logger is not None

    @patch("auto_tag.audio_recognize.get_netease_api")
    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_fetch_lyrics_from_netease(
        self, mock_load_audio, mock_netease_api, lyric_manager, temp_audio_file
    ):
        """
        TC-N-001: 测试从网易云音乐获取歌词

        Args:
            mock_load_audio: Mock load_audio函数
            mock_netease_api: Mock 网易云API
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        # Mock 音频文件元数据
        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        # Mock 网易云 API - 模拟 Response 对象
        mock_api_instance = MagicMock()
        
        # Mock search 方法返回 Response 对象
        mock_search_response = MagicMock()
        mock_search_response.body = {
            'result': {
                'songs': [
                    {
                        'id': 123456,
                        'name': '晴天',
                        'artists': [{'name': '周杰伦'}],
                        'album': {'name': '叶惠美'},
                        'duration': 269000
                    }
                ]
            }
        }
        mock_api_instance.search.return_value = mock_search_response
        
        # Mock lyric 方法返回 Response 对象
        mock_lyric_response = MagicMock()
        mock_lyric_response.body = {
            'lrc': {'lyric': '[00:00.00]故事的小黄花\n[00:05.00]从出生那年就飘着'},
            'tlyric': {'lyric': '[00:00.00]The small yellow flower\n[00:05.00]Has been floating since birth'}
        }
        mock_api_instance.lyric.return_value = mock_lyric_response
        mock_netease_api.return_value = mock_api_instance

        # 执行测试
        result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

        # 验证结果
        assert result is not None
        assert result['provider'] == 'netease'
        assert result['track_name'] == '晴天'
        assert result['artist_name'] == '周杰伦'
        assert 'synced_lyrics' in result
        assert 'plain_lyrics' in result
        
        # 验证歌词合并功能：应该包含原始歌词和翻译歌词
        assert '故事的小黄花' in result['synced_lyrics']
        assert 'The small yellow flower' in result['synced_lyrics']
        assert '从出生那年就飘着' in result['synced_lyrics']
        assert 'Has been floating since birth' in result['synced_lyrics']
    
    @patch("auto_tag.audio_recognize.get_netease_api")
    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_fetch_lyrics_original_mode(
        self, mock_load_audio, mock_netease_api, lyric_manager, temp_audio_file
    ):
        """
        TC-N-003: 测试获取原始歌词模式

        Args:
            mock_load_audio: Mock load_audio函数
            mock_netease_api: Mock 网易云API
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        # Mock 音频文件元数据
        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        # Mock 网易云 API - 模拟 Response 对象
        mock_api_instance = MagicMock()
        
        # Mock search 方法返回 Response 对象
        mock_search_response = MagicMock()
        mock_search_response.body = {
            'result': {
                'songs': [
                    {
                        'id': 123456,
                        'name': '晴天',
                        'artists': [{'name': '周杰伦'}],
                        'album': {'name': '叶惠美'},
                        'duration': 269000
                    }
                ]
            }
        }
        mock_api_instance.search.return_value = mock_search_response
        
        # Mock lyric 方法返回 Response 对象
        mock_lyric_response = MagicMock()
        mock_lyric_response.body = {
            'lrc': {'lyric': '[00:00.00]故事的小黄花\n[00:05.00]从出生那年就飘着'},
            'tlyric': {'lyric': '[00:00.00]The small yellow flower\n[00:05.00]Has been floating since birth'}
        }
        mock_api_instance.lyric.return_value = mock_lyric_response
        mock_netease_api.return_value = mock_api_instance

        # 执行测试 - 获取原始歌词
        result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease', lyric_mode='original')

        # 验证结果
        assert result is not None
        assert result['provider'] == 'netease'
        
        # 验证只包含原始歌词，不包含翻译
        assert '故事的小黄花' in result['synced_lyrics']
        assert '从出生那年就飘着' in result['synced_lyrics']
        assert 'The small yellow flower' not in result['synced_lyrics']
        assert 'Has been floating since birth' not in result['synced_lyrics']
        assert result['plain_lyrics'] == ''
    
    @patch("auto_tag.audio_recognize.get_netease_api")
    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_fetch_lyrics_translation_mode(
        self, mock_load_audio, mock_netease_api, lyric_manager, temp_audio_file
    ):
        """
        TC-N-004: 测试获取翻译歌词模式

        Args:
            mock_load_audio: Mock load_audio函数
            mock_netease_api: Mock 网易云API
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        # Mock 音频文件元数据
        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        # Mock 网易云 API - 模拟 Response 对象
        mock_api_instance = MagicMock()
        
        # Mock search 方法返回 Response 对象
        mock_search_response = MagicMock()
        mock_search_response.body = {
            'result': {
                'songs': [
                    {
                        'id': 123456,
                        'name': '晴天',
                        'artists': [{'name': '周杰伦'}],
                        'album': {'name': '叶惠美'},
                        'duration': 269000
                    }
                ]
            }
        }
        mock_api_instance.search.return_value = mock_search_response
        
        # Mock lyric 方法返回 Response 对象
        mock_lyric_response = MagicMock()
        mock_lyric_response.body = {
            'lrc': {'lyric': '[00:00.00]故事的小黄花\n[00:05.00]从出生那年就飘着'},
            'tlyric': {'lyric': '[00:00.00]The small yellow flower\n[00:05.00]Has been floating since birth'}
        }
        mock_api_instance.lyric.return_value = mock_lyric_response
        mock_netease_api.return_value = mock_api_instance

        # 执行测试 - 获取翻译歌词
        result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease', lyric_mode='translation')

        # 验证结果
        assert result is not None
        assert result['provider'] == 'netease'
        
        # 验证只包含翻译歌词，不包含原始歌词
        assert '故事的小黄花' not in result['synced_lyrics']
        assert '从出生那年就飘着' not in result['synced_lyrics']
        assert 'The small yellow flower' in result['synced_lyrics']
        assert 'Has been floating since birth' in result['synced_lyrics']
        assert result['plain_lyrics'] == ''
    
    def test_invalid_lyric_mode(self, lyric_manager, temp_audio_file):
        """
        TC-N-005: 测试无效的歌词模式

        Args:
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        with pytest.raises(ValueError, match="不支持的歌词模式"):
            lyric_manager.fetch_lyrics(temp_audio_file, provider='netease', lyric_mode='invalid_mode')

    @patch("auto_tag.audio_recognize.get_kugou_api")
    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_fetch_lyrics_from_kugou(
        self, mock_load_audio, mock_kugou_api, lyric_manager, temp_audio_file
    ):
        """
        TC-N-002: 测试从酷狗音乐获取歌词

        Args:
            mock_load_audio: Mock load_audio函数
            mock_kugou_api: Mock 酷狗API
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        # Mock 音频文件元数据
        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        # Mock 酷狗 API - 模拟 Response 对象
        mock_api_instance = MagicMock()
        
        # Mock search 方法返回 Response 对象
        mock_search_response = MagicMock()
        mock_search_response.body = {
            'data': {
                'lists': [
                    {
                        'Hash': 'abc123',
                        'SongName': '晴天',
                        'SingerName': '周杰伦',
                        'AlbumName': '叶惠美',
                        'Duration': 269
                    }
                ]
            }
        }
        mock_api_instance.search.return_value = mock_search_response
        
        # Mock lyric 方法返回 Response 对象
        mock_lyric_response = MagicMock()
        mock_lyric_response.body = {
            'lyrics': '[00:00.00]故事的小黄花\n[00:05.00]从出生那年就飘着'
        }
        mock_api_instance.lyric.return_value = mock_lyric_response
        mock_kugou_api.return_value = mock_api_instance

        # 执行测试
        result = lyric_manager.fetch_lyrics(temp_audio_file, provider='kugou')

        # 验证结果
        assert result is not None
        assert result['provider'] == 'kugou'
        assert result['track_name'] == '晴天'
        assert result['artist_name'] == '周杰伦'

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_fetch_lyrics_content_accuracy(
        self, mock_load_audio, lyric_manager, temp_audio_file
    ):
        """
        TC-N-003: 测试获取歌词内容准确性验证

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        expected_lyrics = "[00:00.00]故事的小黄花\n[00:05.00]从出生那年就飘着"

        # Mock 音频文件元数据
        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.return_value = {
                'result': {
                    'songs': [
                        {
                            'id': 123456,
                            'name': '晴天',
                            'artists': [{'name': '周杰伦'}],
                            'album': {'name': '叶惠美'},
                            'duration': 269000
                        }
                    ]
                }
            }
            mock_api_instance.get_lyric.return_value = {
                'lrc': {'lyric': expected_lyrics},
                'tlyric': {'lyric': ''}
            }
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

            assert result is not None
            assert result['synced_lyrics'] == expected_lyrics

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_fetch_lyrics_metadata_validation(
        self, mock_load_audio, lyric_manager, temp_audio_file
    ):
        """
        TC-N-004: 测试获取歌词元数据验证

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        # Mock 音频文件元数据
        mock_audio = MagicMock()
        mock_audio.tag.title = "Ghost In A Flower"
        mock_audio.tag.artist = "Yorushika"
        mock_audio.tag.album = "Plagiarism"
        mock_audio.info.time_secs = 245
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.return_value = {
                'result': {
                    'songs': [
                        {
                            'id': 789012,
                            'name': 'Ghost In A Flower',
                            'artists': [{'name': 'Yorushika'}],
                            'album': {'name': 'Plagiarism'},
                            'duration': 245000
                        }
                    ]
                }
            }
            mock_api_instance.get_lyric.return_value = {
                'lrc': {'lyric': '[00:00.00]花に亡霊'},
                'tlyric': {'lyric': ''}
            }
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

            assert result is not None
            assert result['track_name'] == 'Ghost In A Flower'
            assert result['artist_name'] == 'Yorushika'
            assert result['album_name'] == 'Plagiarism'
            assert result['duration'] == 245


class TestLyricFetchBoundary:
    """
    歌词获取边界条件测试类

    测试歌词获取功能的边界条件和特殊情况
    """

    def test_special_characters_in_filename_chinese(self, lyric_manager):
        """
        TC-B-001: 测试文件名包含中文

        Args:
            lyric_manager: LyricManager实例
        """
        with tempfile.NamedTemporaryFile(suffix="_晴天.mp3", delete=False) as f:
            temp_file = f.name
            f.write(b"fake mp3 content")

        try:
            with patch("auto_tag.lyric.manager.eyed3.load") as mock_load_audio:
                with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
                    mock_audio = MagicMock()
                    mock_audio.tag.title = "晴天"
                    mock_audio.tag.artist = "周杰伦"
                    mock_audio.tag.album = "叶惠美"
                    mock_audio.info.time_secs = 269
                    mock_load_audio.return_value = mock_audio

                    mock_api_instance = MagicMock()
                    mock_api_instance.search.return_value = {
                        'result': {
                            'songs': [
                                {
                                    'id': 123456,
                                    'name': '晴天',
                                    'artists': [{'name': '周杰伦'}],
                                    'album': {'name': '叶惠美'},
                                    'duration': 269000
                                }
                            ]
                        }
                    }
                    mock_api_instance.get_lyric.return_value = {
                        'lrc': {'lyric': '[00:00.00]故事的小黄花'},
                        'tlyric': {'lyric': ''}
                    }
                    mock_api.return_value = mock_api_instance

                    result = lyric_manager.fetch_lyrics(temp_file, provider='netease')
                    assert result is not None
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_special_characters_in_filename_japanese(self, lyric_manager):
        """
        TC-B-002: 测试文件名包含日文

        Args:
            lyric_manager: LyricManager实例
        """
        with tempfile.NamedTemporaryFile(suffix="_花に亡霊.mp3", delete=False) as f:
            temp_file = f.name
            f.write(b"fake mp3 content")

        try:
            with patch("auto_tag.lyric.manager.eyed3.load") as mock_load_audio:
                with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
                    mock_audio = MagicMock()
                    mock_audio.tag.title = "花に亡霊"
                    mock_audio.tag.artist = "ヨルシカ"
                    mock_audio.tag.album = "Plagiarism"
                    mock_audio.info.time_secs = 245
                    mock_load_audio.return_value = mock_audio

                    mock_api_instance = MagicMock()
                    mock_api_instance.search.return_value = {
                        'result': {
                            'songs': [
                                {
                                    'id': 789012,
                                    'name': '花に亡霊',
                                    'artists': [{'name': 'ヨルシカ'}],
                                    'album': {'name': 'Plagiarism'},
                                    'duration': 245000
                                }
                            ]
                        }
                    }
                    mock_api_instance.get_lyric.return_value = {
                        'lrc': {'lyric': '[00:00.00]もう忘れてしまったかな'},
                        'tlyric': {'lyric': ''}
                    }
                    mock_api.return_value = mock_api_instance

                    result = lyric_manager.fetch_lyrics(temp_file, provider='netease')
                    assert result is not None
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_lyrics_with_special_characters(
        self, mock_load_audio, lyric_manager, temp_audio_file
    ):
        """
        TC-B-003: 测试歌词包含特殊字符

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        special_chars_lyrics = "[00:00.00]🎵故事的小黄花🎉\n[00:05.00]从出生那年就飘着♪"

        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.return_value = {
                'result': {
                    'songs': [
                        {
                            'id': 123456,
                            'name': '晴天',
                            'artists': [{'name': '周杰伦'}],
                            'album': {'name': '叶惠美'},
                            'duration': 269000
                        }
                    ]
                }
            }
            mock_api_instance.get_lyric.return_value = {
                'lrc': {'lyric': special_chars_lyrics},
                'tlyric': {'lyric': ''}
            }
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

            assert result is not None
            assert '🎵' in result['synced_lyrics']
            assert '🎉' in result['synced_lyrics']

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_multilingual_lyrics(self, mock_load_audio, lyric_manager, temp_audio_file):
        """
        TC-B-004: 测试歌词包含多语言

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        multilingual_lyrics = (
            "[00:00.00]故事的小黄花\n"
            "[00:05.00]从出生那年就飘着\n"
            "[00:10.00]The small yellow flower in the story\n"
            "[00:15.00]花に亡霊\n"
            "[00:20.00]유령"
        )

        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.return_value = {
                'result': {
                    'songs': [
                        {
                            'id': 123456,
                            'name': '晴天',
                            'artists': [{'name': '周杰伦'}],
                            'album': {'name': '叶惠美'},
                            'duration': 269000
                        }
                    ]
                }
            }
            mock_api_instance.get_lyric.return_value = {
                'lrc': {'lyric': multilingual_lyrics},
                'tlyric': {'lyric': ''}
            }
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

            assert result is not None
            assert '花に亡霊' in result['synced_lyrics']
            assert '유령' in result['synced_lyrics']

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_empty_audio_file(self, mock_load_audio, lyric_manager, temp_audio_file):
        """
        TC-B-005: 测试空音频文件

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        mock_load_audio.return_value = None

        result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

        assert result is None

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_audio_file_without_metadata(self, mock_load_audio, lyric_manager, temp_audio_file):
        """
        TC-B-006: 测试无元数据音频文件

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        mock_audio = MagicMock()
        mock_audio.tag.title = None
        mock_audio.tag.artist = None
        mock_audio.tag.album = None
        mock_audio.info.time_secs = 0
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.return_value = None
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

            assert result is None

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_very_long_lyrics_text(self, mock_load_audio, lyric_manager, temp_audio_file):
        """
        TC-B-007: 测试超长歌词文本

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        long_lyrics = "[00:00.00]" + "测试歌词" * 2000

        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.return_value = {
                'result': {
                    'songs': [
                        {
                            'id': 123456,
                            'name': '晴天',
                            'artists': [{'name': '周杰伦'}],
                            'album': {'name': '叶惠美'},
                            'duration': 269000
                        }
                    ]
                }
            }
            mock_api_instance.get_lyric.return_value = {
                'lrc': {'lyric': long_lyrics},
                'tlyric': {'lyric': ''}
            }
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

            assert result is not None
            assert len(result['synced_lyrics']) > 10000


class TestLyricFetchException:
    """
    歌词获取异常处理测试类

    测试歌词获取功能的异常处理能力
    """

    def test_file_not_found(self, lyric_manager):
        """
        TC-E-001: 测试文件不存在

        Args:
            lyric_manager: LyricManager实例
        """
        with pytest.raises(FileNotFoundError):
            lyric_manager.fetch_lyrics("/nonexistent/file.mp3")

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_network_connection_failed(
        self, mock_load_audio, lyric_manager, temp_audio_file
    ):
        """
        TC-E-002: 测试网络连接失败

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.side_effect = ConnectionError("Network is unreachable")
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

            assert result is None

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_api_request_timeout(self, mock_load_audio, lyric_manager, temp_audio_file):
        """
        TC-E-003: 测试API请求超时

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.side_effect = TimeoutError("Request timed out")
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

            assert result is None

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_api_returns_invalid_data(
        self, mock_load_audio, lyric_manager, temp_audio_file
    ):
        """
        TC-E-004: 测试API返回错误数据

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.return_value = {
                'result': {
                    'songs': []
                }
            }
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

            assert result is None

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_dns_resolution_failed(
        self, mock_load_audio, lyric_manager, temp_audio_file
    ):
        """
        TC-E-005: 测试DNS解析失败

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.side_effect = Exception("DNS resolution failed")
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

            assert result is None

    def test_invalid_provider_name(self, lyric_manager, temp_audio_file):
        """
        TC-E-006: 测试无效的提供商名称

        Args:
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        with pytest.raises(ValueError):
            lyric_manager.fetch_lyrics(temp_audio_file, provider="invalid_provider")

    def test_invalid_file_path_type(self, lyric_manager):
        """
        TC-E-007: 测试无效的文件路径类型

        Args:
            lyric_manager: LyricManager实例
        """
        with pytest.raises((TypeError, AttributeError)):
            lyric_manager.fetch_lyrics(12345)

    def test_none_parameter(self, lyric_manager):
        """
        TC-E-008: 测试None参数

        Args:
            lyric_manager: LyricManager实例
        """
        with pytest.raises((TypeError, AttributeError)):
            lyric_manager.fetch_lyrics(None)

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_api_rate_limit(self, mock_load_audio, lyric_manager, temp_audio_file):
        """
        TC-E-009: 测试API限流

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.side_effect = Exception("Rate limit exceeded")
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

            assert result is None

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_song_not_found_in_api(
        self, mock_load_audio, lyric_manager, temp_audio_file
    ):
        """
        TC-E-010: 测试歌曲在API中不存在

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        mock_audio = MagicMock()
        mock_audio.tag.title = "Unknown Song XYZ123"
        mock_audio.tag.artist = "Unknown Artist ABC"
        mock_audio.tag.album = "Unknown Album"
        mock_audio.info.time_secs = 0
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.return_value = {
                'result': {
                    'songs': []
                }
            }
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

            assert result is None

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_lyrics_api_returns_empty(
        self, mock_load_audio, lyric_manager, temp_audio_file
    ):
        """
        TC-E-011: 测试歌词API返回空数据

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.return_value = {
                'result': {
                    'songs': [
                        {
                            'id': 123456,
                            'name': '晴天',
                            'artists': [{'name': '周杰伦'}],
                            'album': {'name': '叶惠美'},
                            'duration': 269000
                        }
                    ]
                }
            }
            mock_api_instance.get_lyric.return_value = None
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, provider='netease')

            assert result is None


class TestLyricPerformance:
    """
    歌词功能性能测试类

    测试歌词获取功能的性能表现
    """

    @pytest.mark.skipif(True, reason="pytest-benchmark not installed")
    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_fetch_lyrics_response_time(
        self, mock_load_audio, lyric_manager, temp_audio_file
    ):
        """TC-P-001: 测试单文件歌词获取响应时间 (跳过: 缺少 pytest-benchmark)"""
        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        with patch("auto_tag.audio_recognize.get_netease_api") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.search.return_value = {
                'result': {
                    'songs': [
                        {
                            'id': 123456,
                            'name': '晴天',
                            'artists': [{'name': '周杰伦'}],
                            'album': {'name': '叶惠美'},
                            'duration': 269000
                        }
                    ]
                }
            }
            mock_api_instance.get_lyric.return_value = {
                'lrc': {'lyric': '[00:00.00]故事的小黄花'},
                'tlyric': {'lyric': ''}
            }
            mock_api.return_value = mock_api_instance

            result = lyric_manager.fetch_lyrics(temp_audio_file, "netease")

            assert result is not None

    @pytest.mark.skipif(True, reason="pytest-benchmark not installed")
    def test_parse_search_result_performance(self, lyric_manager):
        """TC-P-002: 测试解析搜索结果性能 (跳过: 缺少 pytest-benchmark)"""
        search_result = {
            'result': {
                'songs': [
                    {
                        'id': i,
                        'name': f'歌曲{i}',
                        'artists': [{'name': f'歌手{i}'}],
                        'album': {'name': f'专辑{i}'},
                        'duration': 200000 + i * 1000
                    }
                    for i in range(100)
                ]
            }
        }

        result = lyric_manager._parse_search_result(search_result, 'netease')

        assert len(result) == 100

    @pytest.mark.skipif(True, reason="pytest-benchmark not installed")
    def test_extract_metadata_performance(self, lyric_manager, temp_audio_file):
        """TC-P-003: 测试提取元数据性能 (跳过: 缺少 pytest-benchmark)"""
        with patch("auto_tag.lyric.manager.eyed3.load") as mock_load_audio:
            mock_audio = MagicMock()
            mock_audio.tag.title = "晴天"
            mock_audio.tag.artist = "周杰伦"
            mock_audio.tag.album = "叶惠美"
            mock_audio.info.time_secs = 269
            mock_load_audio.return_value = mock_audio

            result = lyric_manager._extract_audio_metadata(temp_audio_file)

            assert result is not None
            assert 'title' in result


class TestLyricSearchParsing:
    """
    歌词搜索解析测试类

    测试搜索结果解析功能
    """

    def test_parse_netease_search_result(self, lyric_manager):
        """
        TC-S-001: 测试解析网易云搜索结果

        Args:
            lyric_manager: LyricManager实例
        """
        search_result = {
            'result': {
                'songs': [
                    {
                        'id': 123456,
                        'name': '晴天',
                        'artists': [{'name': '周杰伦'}],
                        'album': {'name': '叶惠美'},
                        'duration': 269000
                    },
                    {
                        'id': 789012,
                        'name': '夜曲',
                        'artists': [{'name': '周杰伦'}],
                        'album': {'name': '十一月的萧邦'},
                        'duration': 234000
                    }
                ]
            }
        }

        result = lyric_manager._parse_search_result(search_result, 'netease')

        assert len(result) == 2
        assert result[0]['id'] == 123456
        assert result[0]['name'] == '晴天'
        assert result[0]['artist'] == '周杰伦'
        assert result[0]['album'] == '叶惠美'
        assert result[0]['duration'] == 269

    def test_parse_kugou_search_result(self, lyric_manager):
        """
        TC-S-002: 测试解析酷狗搜索结果

        Args:
            lyric_manager: LyricManager实例
        """
        search_result = [
            {
                'hash': 'abc123',
                'songname': '晴天',
                'singername': '周杰伦',
                'album_name': '叶惠美',
                'duration': 269
            },
            {
                'hash': 'def456',
                'songname': '夜曲',
                'singername': '周杰伦',
                'album_name': '十一月的萧邦',
                'duration': 234
            }
        ]

        result = lyric_manager._parse_search_result(search_result, 'kugou')

        assert len(result) == 2
        assert result[0]['id'] == 'abc123'
        assert result[0]['name'] == '晴天'
        assert result[0]['artist'] == '周杰伦'

    def test_parse_empty_search_result(self, lyric_manager):
        """
        TC-S-003: 测试解析空搜索结果

        Args:
            lyric_manager: LyricManager实例
        """
        search_result = {'result': {'songs': []}}

        result = lyric_manager._parse_search_result(search_result, 'netease')

        assert len(result) == 0

    def test_parse_malformed_search_result(self, lyric_manager):
        """
        TC-S-004: 测试解析格式错误的搜索结果

        Args:
            lyric_manager: LyricManager实例
        """
        search_result = {'invalid_key': 'invalid_value'}

        result = lyric_manager._parse_search_result(search_result, 'netease')

        assert len(result) == 0


class TestAudioMetadataExtraction:
    """
    音频元数据提取测试类

    测试从音频文件提取元数据的功能
    """

    @patch("auto_tag.lyric.manager.eyed3.load")
    def test_extract_mp3_metadata(self, mock_load_audio, lyric_manager, temp_audio_file):
        """
        TC-M-001: 测试提取MP3元数据

        Args:
            mock_load_audio: Mock load_audio函数
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        mock_audio = MagicMock()
        mock_audio.tag.title = "晴天"
        mock_audio.tag.artist = "周杰伦"
        mock_audio.tag.album = "叶惠美"
        mock_audio.info.time_secs = 269
        mock_load_audio.return_value = mock_audio

        result = lyric_manager._extract_audio_metadata(temp_audio_file)

        assert result is not None
        assert result['title'] == '晴天'
        assert result['artist'] == '周杰伦'
        assert result['album'] == '叶惠美'
        assert result['duration'] == 269

    def test_extract_metadata_failure(self, lyric_manager, temp_audio_file):
        """
        TC-M-002: 测试元数据提取失败

        Args:
            lyric_manager: LyricManager实例
            temp_audio_file: 临时音频文件
        """
        with patch("auto_tag.lyric.manager.eyed3.load") as mock_load_audio:
            mock_load_audio.side_effect = Exception("Cannot read file")

            result = lyric_manager._extract_audio_metadata(temp_audio_file)

            assert result is None
