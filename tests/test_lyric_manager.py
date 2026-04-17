# -*- coding: utf-8 -*-
"""
歌词管理器测试模块

测试 LyricManager 类的功能，包括歌词获取、嵌入、提取和格式转换。

@module test_lyric_manager
@author Backend Architect
@version 1.0.0
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestLyricManager:
    """
    歌词管理器测试类

    测试 LyricManager 的各项功能。
    """

    def test_init(self):
        """
        测试 LyricManager 初始化
        """
        from auto_tag.lyric import LyricManager
        
        manager = LyricManager()
        assert manager is not None
        assert manager.logger is not None

    def test_fetch_lyrics_file_not_found(self):
        """
        测试获取歌词时文件不存在的情况
        """
        from auto_tag.lyric import LyricManager
        
        manager = LyricManager()
        
        with pytest.raises(FileNotFoundError):
            manager.fetch_lyrics("/nonexistent/file.mp3")

    def test_fetch_lyrics_invalid_provider(self):
        """
        测试获取歌词时提供商无效的情况
        """
        from auto_tag.lyric import LyricManager
        
        manager = LyricManager()
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_file = f.name
            f.write(b"fake mp3 content")
        
        try:
            with pytest.raises(ValueError):
                manager.fetch_lyrics(temp_file, provider="invalid_provider")
        finally:
            os.unlink(temp_file)

    @patch("auto_tag.lyric.manager.LyricManager._extract_audio_metadata")
    @patch("MusicLibrary.neteaseCloudMusicApi.NeteaseCloudMusicApi")
    def test_fetch_lyrics_success(self, mock_netease_api, mock_extract_metadata):
        """
        测试成功获取歌词（网易云）
        """
        from auto_tag.lyric import LyricManager
        
        # Mock 元数据提取
        mock_extract_metadata.return_value = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'duration': 180
        }
        
        # Mock API 客户端
        mock_api_instance = MagicMock()
        mock_netease_api.return_value = mock_api_instance
        
        # Mock 搜索结果（Response 对象）
        mock_search_response = MagicMock()
        mock_search_response.body = {
            'result': {
                'songs': [{
                    'id': 123456,
                    'name': 'Test Song',
                    'artists': [{'name': 'Test Artist'}],
                    'album': {'name': 'Test Album'},
                    'duration': 180000
                }]
            }
        }
        mock_api_instance.search.return_value = mock_search_response
        
        # Mock 歌词结果（Response 对象）
        mock_lyric_response = MagicMock()
        mock_lyric_response.body = {
            'lrc': {'lyric': '[00:00.00]Test lyrics'},
            'tlyric': {'lyric': ''}
        }
        mock_api_instance.lyric.return_value = mock_lyric_response
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_file = f.name
            f.write(b"fake mp3 content")
        
        try:
            manager = LyricManager()
            result = manager.fetch_lyrics(temp_file, provider="netease")
            
            assert result is not None
            assert result['synced_lyrics'] == '[00:00.00]Test lyrics'
            assert result['provider'] == 'netease'
        finally:
            os.unlink(temp_file)

    def test_embed_lyrics_file_not_found(self):
        """
        测试嵌入歌词时文件不存在的情况
        """
        from auto_tag.lyric import LyricManager
        
        manager = LyricManager()
        
        with pytest.raises(FileNotFoundError):
            manager.embed_lyrics("/nonexistent/file.mp3", "lyrics")

    def test_embed_lyrics_invalid_format(self):
        """
        测试嵌入歌词时格式无效的情况
        """
        from auto_tag.lyric import LyricManager
        
        manager = LyricManager()
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_file = f.name
            f.write(b"fake mp3 content")
        
        try:
            with pytest.raises(ValueError):
                manager.embed_lyrics(temp_file, "lyrics", format="invalid_format")
        finally:
            os.unlink(temp_file)

    def test_extract_lyrics_file_not_found(self):
        """
        测试提取歌词时文件不存在的情况
        """
        from auto_tag.lyric import LyricManager
        
        manager = LyricManager()
        
        with pytest.raises(FileNotFoundError):
            manager.extract_lyrics("/nonexistent/file.mp3")

    def test_convert_lyrics_same_format(self):
        """
        测试转换歌词时源格式和目标格式相同
        """
        from auto_tag.lyric import LyricManager
        
        manager = LyricManager()
        lyrics = "[00:00.00]Test lyrics"
        
        result = manager.convert_lyrics(lyrics, "lrc", "lrc")
        assert result == lyrics

    def test_convert_lyrics_invalid_from_format(self):
        """
        测试转换歌词时源格式无效
        """
        from auto_tag.lyric import LyricManager
        
        manager = LyricManager()
        
        with pytest.raises(ValueError):
            manager.convert_lyrics("lyrics", "invalid", "lrc")

    def test_convert_lyrics_invalid_to_format(self):
        """
        测试转换歌词时目标格式无效
        """
        from auto_tag.lyric import LyricManager
        
        manager = LyricManager()
        
        with pytest.raises(ValueError):
            manager.convert_lyrics("lyrics", "lrc", "invalid")


class TestLyricProvider:
    """
    歌词提供商测试类

    测试提供商配置和 API 获取功能。
    """

    def test_get_provider_valid(self):
        """
        测试获取有效的提供商配置
        """
        from auto_tag.lyric import get_provider, PROVIDERS
        
        provider = get_provider("lrclib")
        assert provider is not None
        assert provider.name == "lrclib"
        assert provider.display_name == "LRCLib"

    def test_get_provider_invalid(self):
        """
        测试获取无效的提供商配置
        """
        from auto_tag.lyric import get_provider
        
        provider = get_provider("invalid_provider")
        assert provider is None

    def test_list_providers(self):
        """
        测试获取所有提供商列表
        """
        from auto_tag.lyric import list_providers
        
        providers = list_providers()
        assert "lrclib" in providers
        assert "applemusic" in providers
        assert "musixmatch" in providers

    def test_providers_config(self):
        """
        测试提供商配置完整性
        """
        from auto_tag.lyric import PROVIDERS
        
        for name, provider in PROVIDERS.items():
            assert provider.name == name
            assert provider.display_name
            assert provider.description
            assert provider.api_module
