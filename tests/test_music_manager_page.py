# -*- coding: utf-8 -*-
"""
音乐管理页面测试模块

测试 MusicManagerPage 类的功能。

@module test_music_manager_page
@author Backend Architect
@version 1.0.0
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    """
    创建 QApplication 实例

    Qt 组件测试需要 QApplication 实例。
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestMusicManagerPage:
    """
    音乐管理页面测试类

    测试 MusicManagerPage 的各项功能。
    """

    def test_init(self, qapp):
        """
        测试页面初始化
        """
        from auto_tag.gui.pages import MusicManagerPage
        
        page = MusicManagerPage()
        assert page is not None

    def test_ui_components_exist(self, qapp):
        """
        测试 UI 组件是否存在
        """
        from auto_tag.gui.pages import MusicManagerPage
        
        page = MusicManagerPage()
        
        # 检查关键组件是否存在
        assert hasattr(page, 'file_table')
        assert hasattr(page, 'title_edit')
        assert hasattr(page, 'artist_edit')
        assert hasattr(page, 'album_edit')
        assert hasattr(page, 'year_edit')
        assert hasattr(page, 'genre_edit')
        assert hasattr(page, 'cover_label')
        assert hasattr(page, 'lyric_text')
        assert hasattr(page, 'provider_combo')

    def test_refresh_texts(self, qapp):
        """
        测试刷新文本功能
        """
        from auto_tag.gui.pages import MusicManagerPage
        
        page = MusicManagerPage()
        
        # 调用 refresh_texts 不应抛出异常
        page.refresh_texts()

    def test_set_default_cover(self, qapp):
        """
        测试设置默认封面
        """
        from auto_tag.gui.pages import MusicManagerPage
        
        page = MusicManagerPage()
        
        # 调用 _set_default_cover 不应抛出异常
        page._set_default_cover()

    def test_update_selected_files_empty(self, qapp):
        """
        测试更新选中文件（空列表）
        """
        from auto_tag.gui.pages import MusicManagerPage
        
        page = MusicManagerPage()
        
        # 清空选中文件
        page.selected_files = []
        page._update_selected_files()
        
        assert page.selected_files == []

    @patch("auto_tag.gui.pages.music_manager_page.MessageBox")
    def test_on_save_metadata_no_file(self, mock_msgbox, qapp):
        """
        测试保存元数据时未选择文件
        """
        from auto_tag.gui.pages import MusicManagerPage
        
        page = MusicManagerPage()
        page.current_file = None
        
        # 调用 _on_save_metadata 不应抛出异常
        page._on_save_metadata()
        
        # 验证 MessageBox 被调用（提示未选择文件）
        mock_msgbox.assert_called_once()

    @patch("auto_tag.gui.pages.music_manager_page.MessageBox")
    def test_on_get_lyrics_no_file(self, mock_msgbox, qapp):
        """
        测试获取歌词时未选择文件
        """
        from auto_tag.gui.pages import MusicManagerPage
        
        page = MusicManagerPage()
        page.current_file = None
        page.selected_files = []
        
        # 调用 _on_get_lyrics 不应抛出异常
        page._on_get_lyrics()
        
        # 验证 MessageBox 被调用（提示未选择文件）
        mock_msgbox.assert_called_once()

    @patch("auto_tag.gui.pages.music_manager_page.MessageBox")
    def test_on_embed_lyrics_no_lyrics(self, mock_msgbox, qapp):
        """
        测试嵌入歌词时无歌词内容
        """
        from auto_tag.gui.pages import MusicManagerPage
        
        page = MusicManagerPage()
        page.current_lyrics = None
        
        # 调用 _on_embed_lyrics 不应抛出异常
        page._on_embed_lyrics()
        
        # 验证 MessageBox 被调用（提示无歌词）
        mock_msgbox.assert_called()


class TestMusicManagerPageIntegration:
    """
    音乐管理页面集成测试类

    测试页面与其他模块的集成。
    """

    @patch("auto_tag.gui.pages.music_manager_page.MetadataManager")
    @patch("auto_tag.gui.pages.music_manager_page.LyricManager")
    def test_load_file_info(self, mock_lyric_manager, mock_metadata_manager, qapp):
        """
        测试加载文件信息
        """
        from auto_tag.gui.pages import MusicManagerPage
        
        # Mock MetadataManager
        mock_meta_mgr = MagicMock()
        mock_meta_mgr.read_metadata.return_value = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'year': '2024',
            'genre': 'Pop',
            'cover': None
        }
        mock_metadata_manager.return_value = mock_meta_mgr
        
        # Mock LyricManager
        mock_lyric_mgr = MagicMock()
        mock_lyric_mgr.extract_lyrics.return_value = None
        mock_lyric_manager.return_value = mock_lyric_mgr
        
        page = MusicManagerPage()
        page.metadata_manager = mock_meta_mgr
        page.lyric_manager = mock_lyric_mgr
        
        # 调用 _load_file_info
        page._load_file_info("/fake/path/song.mp3")
        
        # 验证元数据被读取
        mock_meta_mgr.read_metadata.assert_called_once_with("/fake/path/song.mp3")

    @patch("auto_tag.gui.pages.music_manager_page.MetadataManager")
    @patch("auto_tag.gui.pages.music_manager_page.LyricManager")
    def test_extract_lyrics_from_file(self, mock_lyric_manager, mock_metadata_manager, qapp):
        """
        测试从文件提取歌词
        """
        from auto_tag.gui.pages import MusicManagerPage
        
        # Mock MetadataManager
        mock_meta_mgr = MagicMock()
        mock_meta_mgr.read_metadata.return_value = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'year': '2024',
            'genre': 'Pop',
            'cover': None
        }
        mock_metadata_manager.return_value = mock_meta_mgr
        
        # Mock LyricManager
        mock_lyric_mgr = MagicMock()
        mock_lyric_mgr.extract_lyrics.return_value = {
            'plain_lyrics': 'Test lyrics',
            'synced_lyrics': '[00:00.00]Test lyrics',
            'format': 'lrc'
        }
        mock_lyric_manager.return_value = mock_lyric_mgr
        
        page = MusicManagerPage()
        page.metadata_manager = mock_meta_mgr
        page.lyric_manager = mock_lyric_mgr
        page.current_file = "/fake/path/song.mp3"
        
        # 调用提取歌词
        page._load_file_info("/fake/path/song.mp3")
        
        # 验证歌词被提取
        mock_lyric_mgr.extract_lyrics.assert_called_once_with("/fake/path/song.mp3")
