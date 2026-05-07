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

    def test_clear_data_resets_cover(self, qapp):
        """
        测试清除数据时封面是否正确重置

        验证 _on_clear_data 调用后：
        1. _current_cover_data 被清空
        2. cover_label 显示默认状态
        """
        from auto_tag.gui.pages import MusicManagerPage
        from PySide6.QtGui import QPixmap
        from PySide6.QtCore import Qt

        page = MusicManagerPage()

        # 模拟设置一个封面（使用 _display_cover）
        fake_cover_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        page._display_cover(fake_cover_data)

        # 验证封面数据已设置
        assert page._current_cover_data is not None
        assert page.cover_label.pixmap() is not None

        # 添加文件到列表（_on_clear_data 会检查 files 是否为空）
        page.files.append("/fake/path/song.mp3")
        page.file_table.insertRow(0)

        # Mock 确认对话框，用户点击"确定"
        with patch.object(page, 'files', ["/fake/path/song.mp3"]):
            with patch("auto_tag.gui.pages.music_manager_page.MessageBox") as mock_msgbox:
                mock_msgbox.return_value.exec.return_value = 1  # 用户确认

                # 调用清除数据
                page._on_clear_data()

        # 验证封面数据已被清空
        assert page._current_cover_data is None

        # 验证 cover_label 仍然有 pixmap（因为 _set_default_cover 设置了灰色默认图）
        assert page.cover_label.pixmap() is not None

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

    def test_supported_audio_formats_completeness(self, qapp):
        """
        测试支持的音频格式列表完整性

        验证 MusicManagerPage._scan_audio_files 支持所有预期的音频格式，
        包括新增的 wma/opus/aac 等格式。
        """
        import os
        import tempfile
        from unittest.mock import patch
        from auto_tag.gui.pages import MusicManagerPage

        page = MusicManagerPage()

        # 预期的完整格式列表（与 CustomFormatManager 保持一致）
        expected_formats = {
            '.mp3', '.flac', '.ogg', '.wav', '.m4a',
            '.aac', '.wma', '.opus'
        }

        # 创建临时目录并添加各格式的测试文件
        with tempfile.TemporaryDirectory() as tmpdir:
            for ext in expected_formats:
                test_file = os.path.join(tmpdir, f"test_song{ext}")
                with open(test_file, 'w') as f:
                    f.write("fake audio data")

            # 调用扫描方法
            page._scan_audio_files(tmpdir)

            # 验证所有格式的文件都被识别
            assert len(page.files) == len(expected_formats), \
                f"期望识别 {len(expected_formats)} 个文件，实际识别 {len(page.files)} 个"

            # 验证文件表格行数
            assert page.file_table.rowCount() == len(expected_formats), \
                f"期望表格有 {len(expected_formats)} 行，实际 {page.file_table.rowCount()} 行"

            # 验证每种格式都出现在文件列表中
            file_exts = {os.path.splitext(f)[1].lower() for f in page.files}
            assert file_exts == expected_formats, \
                f"格式不匹配：期望 {expected_formats}，实际 {file_exts}"

    def test_audio_recognize_default_extensions(self, qapp):
        """
        测试 audio_recognize 模块的默认扩展名参数

        验证 find_and_recognize_audio_files 的默认 extensions 参数
        包含所有支持的音频格式。
        """
        import inspect
        from auto_tag import audio_recognize
        import auto_tag.audio_recognize as ar_module

        # 获取源代码中的默认值（避免 mock 影响）
        source = inspect.getsource(ar_module)
        # 查找 extensions 参数的默认值
        import re
        match = re.search(
            r'extensions:\s*list\[str\]\s*\|\s*tuple\[str,\s*\.\.\.\]\s*=\s*\(([^)]+)\)',
            source
        )

        assert match, "未找到 extensions 参数定义"

        default_extensions_str = match.group(1)
        # 解析扩展名列表
        default_extensions = [ext.strip().strip('"\'') for ext in default_extensions_str.split(',')]

        # 预期的完整格式列表
        expected_extensions = [
            "mp3", "ogg", "flac", "wav", "m4a", "aac", "wma", "opus"
        ]

        # 验证默认值包含所有预期格式
        assert set(default_extensions) == set(expected_extensions), \
            f"audio_recognize 默认扩展名不匹配：期望 {set(expected_extensions)}，实际 {set(default_extensions)}"
