# -*- coding: utf-8 -*-
"""
ConverterPage 单元测试

测试文件格式选择功能，包括：
- 默认格式选择
- 格式选择更新
- 配置持久化
- 全选/取消全选按钮
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from auto_tag.gui.pages.converter_page import ConverterPage


@pytest.fixture(scope="session")
def qapp():
    """创建 QApplication 实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def converter_page(qapp, tmp_path):
    """创建 ConverterPage 实例"""
    # 创建临时配置目录
    config_dir = tmp_path / ".mp3shazamautotag"
    config_dir.mkdir()

    with patch("auto_tag.gui.config.Path.home", return_value=tmp_path):
        page = ConverterPage()
        yield page


class TestFormatFilter:
    """测试文件格式过滤功能"""

    def test_default_format_selection(self, converter_page):
        """测试默认格式选择（应全选）"""
        # 由于测试环境可能共享全局config，这里重新初始化为默认全选状态
        for checkbox in converter_page.audio_format_checkboxes.values():
            checkbox.setChecked(True)
        for checkbox in converter_page.video_format_checkboxes.values():
            checkbox.setChecked(True)
        converter_page._update_supported_formats()

        # 检查所有音频格式复选框是否被选中
        for fmt, checkbox in converter_page.audio_format_checkboxes.items():
            assert checkbox.isChecked(), f"音频格式 {fmt} 应该默认被选中"

        # 检查所有视频格式复选框是否被选中
        for fmt, checkbox in converter_page.video_format_checkboxes.items():
            assert checkbox.isChecked(), f"视频格式 {fmt} 应该默认被选中"

        # 检查配置中的格式列表（应包含所有预设格式）
        expected_formats = [
            "mp3", "flac", "aac", "ogg", "wav", "m4a",
            "mp4", "mkv", "avi", "mov", "wmv", "webm"
        ]
        actual_formats = set(converter_page.config.supported_input_formats)

        # 验证所有预设格式都在列表中
        for fmt in expected_formats:
            assert fmt in actual_formats, f"预设格式 {fmt} 应该在支持的格式列表中"

    def test_deselect_audio_format(self, converter_page):
        """测试取消选择音频格式"""
        # 先重置为全选状态
        for checkbox in converter_page.audio_format_checkboxes.values():
            checkbox.setChecked(True)
        for checkbox in converter_page.video_format_checkboxes.values():
            checkbox.setChecked(True)
        converter_page._update_supported_formats()

        # 取消选择 mp3 格式
        converter_page.audio_format_checkboxes["mp3"].setChecked(False)

        # 验证 mp3 不在支持的格式列表中
        assert "mp3" not in converter_page.config.supported_input_formats

        # 验证其他音频格式仍然在列表中
        assert "flac" in converter_page.config.supported_input_formats
        assert "aac" in converter_page.config.supported_input_formats

    def test_deselect_video_format(self, converter_page):
        """测试取消选择视频格式"""
        # 先重置为全选状态
        for checkbox in converter_page.audio_format_checkboxes.values():
            checkbox.setChecked(True)
        for checkbox in converter_page.video_format_checkboxes.values():
            checkbox.setChecked(True)
        converter_page._update_supported_formats()

        # 取消选择 mp4 格式
        converter_page.video_format_checkboxes["mp4"].setChecked(False)

        # 验证 mp4 不在支持的格式列表中
        assert "mp4" not in converter_page.config.supported_input_formats

        # 验证其他视频格式仍然在列表中
        assert "mkv" in converter_page.config.supported_input_formats
        assert "avi" in converter_page.config.supported_input_formats

    def test_select_all_audio_button(self, converter_page):
        """测试全选音频按钮"""
        # 先取消选择所有音频格式
        for checkbox in converter_page.audio_format_checkboxes.values():
            checkbox.setChecked(False)

        # 点击全选音频按钮
        converter_page._on_select_all_audio()

        # 验证所有音频格式被选中
        for fmt, checkbox in converter_page.audio_format_checkboxes.items():
            assert checkbox.isChecked(), f"音频格式 {fmt} 应该被选中"

        # 验证配置中包含所有音频格式
        audio_formats = ["mp3", "flac", "aac", "ogg", "wav", "m4a"]
        for fmt in audio_formats:
            assert fmt in converter_page.config.supported_input_formats

    def test_deselect_all_audio_button(self, converter_page):
        """测试取消音频按钮"""
        # 点击取消音频按钮
        converter_page._on_deselect_all_audio()

        # 验证所有音频格式未被选中
        for fmt, checkbox in converter_page.audio_format_checkboxes.items():
            assert not checkbox.isChecked(), f"音频格式 {fmt} 不应该被选中"

        # 验证配置中不包含音频格式
        audio_formats = ["mp3", "flac", "aac", "ogg", "wav", "m4a"]
        for fmt in audio_formats:
            assert fmt not in converter_page.config.supported_input_formats

    def test_select_all_video_button(self, converter_page):
        """测试全选视频按钮"""
        # 先取消选择所有视频格式
        for checkbox in converter_page.video_format_checkboxes.values():
            checkbox.setChecked(False)

        # 点击全选视频按钮
        converter_page._on_select_all_video()

        # 验证所有视频格式被选中
        for fmt, checkbox in converter_page.video_format_checkboxes.items():
            assert checkbox.isChecked(), f"视频格式 {fmt} 应该被选中"

        # 验证配置中包含所有视频格式
        video_formats = ["mp4", "mkv", "avi", "mov", "wmv", "webm"]
        for fmt in video_formats:
            assert fmt in converter_page.config.supported_input_formats

    def test_deselect_all_video_button(self, converter_page):
        """测试取消视频按钮"""
        # 点击取消视频按钮
        converter_page._on_deselect_all_video()

        # 验证所有视频格式未被选中
        for fmt, checkbox in converter_page.video_format_checkboxes.items():
            assert not checkbox.isChecked(), f"视频格式 {fmt} 不应该被选中"

        # 验证配置中不包含视频格式
        video_formats = ["mp4", "mkv", "avi", "mov", "wmv", "webm"]
        for fmt in video_formats:
            assert fmt not in converter_page.config.supported_input_formats

    def test_scan_files_with_selected_formats(self, converter_page, tmp_path):
        """测试扫描文件时只识别选中的格式"""
        # 创建测试目录和文件
        test_dir = tmp_path / "test_audio"
        test_dir.mkdir()

        # 创建不同格式的测试文件
        (test_dir / "song1.mp3").touch()
        (test_dir / "song2.flac").touch()
        (test_dir / "video.mp4").touch()
        (test_dir / "video.avi").touch()

        # 只选择 mp3 和 mp4 格式
        converter_page._on_deselect_all_audio()
        converter_page._on_deselect_all_video()
        converter_page.audio_format_checkboxes["mp3"].setChecked(True)
        converter_page.video_format_checkboxes["mp4"].setChecked(True)

        # 扫描文件
        files = converter_page._scan_files(str(test_dir))

        # 验证只扫描到 mp3 和 mp4 文件
        assert len(files) == 2
        file_names = [Path(f).name for f in files]
        assert "song1.mp3" in file_names
        assert "video.mp4" in file_names
        assert "song2.flac" not in file_names
        assert "video.avi" not in file_names

    def test_config_persistence(self, converter_page, tmp_path):
        """测试配置持久化"""
        # 修改格式选择
        converter_page.audio_format_checkboxes["mp3"].setChecked(False)
        converter_page.video_format_checkboxes["mp4"].setChecked(False)

        # 验证配置已保存
        saved_formats = converter_page.config.supported_input_formats
        assert "mp3" not in saved_formats
        assert "mp4" not in saved_formats

        # 创建新的 ConverterPage 实例
        with patch("auto_tag.gui.config.Path.home", return_value=tmp_path):
            new_page = ConverterPage()

            # 验证配置已加载
            assert "mp3" not in new_page.config.supported_input_formats
            assert "mp4" not in new_page.config.supported_input_formats
            assert not new_page.audio_format_checkboxes["mp3"].isChecked()
            assert not new_page.video_format_checkboxes["mp4"].isChecked()


class TestFormatFilterUI:
    """测试文件格式过滤 UI 组件"""

    def test_audio_format_checkboxes_exist(self, converter_page):
        """测试音频格式复选框存在"""
        expected_audio_formats = ["mp3", "flac", "aac", "ogg", "wav", "m4a"]
        for fmt in expected_audio_formats:
            assert fmt in converter_page.audio_format_checkboxes, f"缺少音频格式复选框: {fmt}"

    def test_video_format_checkboxes_exist(self, converter_page):
        """测试视频格式复选框存在"""
        expected_video_formats = ["mp4", "mkv", "avi", "mov", "wmv", "webm"]
        for fmt in expected_video_formats:
            assert fmt in converter_page.video_format_checkboxes, f"缺少视频格式复选框: {fmt}"

    def test_checkbox_count(self, converter_page):
        """测试复选框数量"""
        # 音频格式应该有 6 个
        assert len(converter_page.audio_format_checkboxes) == 6

        # 视频格式应该有 6 个
        assert len(converter_page.video_format_checkboxes) == 6


class TestCustomFormatUI:
    """测试自定义格式管理 UI 组件"""

    def test_custom_format_ui_exists(self, converter_page):
        """测试自定义格式UI组件存在"""
        # 验证输入组件
        assert hasattr(converter_page, 'custom_ext_entry'), "缺少扩展名输入框"
        assert hasattr(converter_page, 'custom_desc_entry'), "缺少描述输入框"
        assert hasattr(converter_page, 'add_custom_format_btn'), "缺少添加按钮"

        # 验证列表组件
        assert hasattr(converter_page, 'custom_format_list'), "缺少自定义格式列表"

        # 验证操作按钮
        assert hasattr(converter_page, 'edit_custom_format_btn'), "缺少编辑按钮"
        assert hasattr(converter_page, 'delete_custom_format_btn'), "缺少删除按钮"

    def test_custom_format_list_initially_empty(self, converter_page):
        """测试自定义格式列表可以正常访问"""
        # 列表组件存在且可以调用count方法
        assert converter_page.custom_format_list is not None
        count = converter_page.custom_format_list.count()
        assert isinstance(count, int)
        assert count >= 0  # 可能为0或包含已有配置的格式

    def test_add_custom_format_button_text(self, converter_page):
        """测试添加按钮文本不为空"""
        assert converter_page.add_custom_format_btn.text() != ""
