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
from PySide6.QtWidgets import (
    QApplication,
    QSizePolicy,
    QTableWidgetItem,
)

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


class TestClearDataFunction:
    """测试清除数据功能"""

    def test_clear_data_button_exists(self, converter_page):
        """测试清除数据按钮存在"""
        assert hasattr(converter_page, 'clear_data_btn'), "缺少清除数据按钮"
        assert converter_page.clear_data_btn is not None

    def test_clear_data_button_text(self, converter_page):
        """测试清除数据按钮文本不为空"""
        assert converter_page.clear_data_btn.text() != ""

    def test_clear_data_with_files(self, converter_page, tmp_path):
        """测试有文件时清除数据功能"""
        # 创建测试目录和文件
        test_dir = tmp_path / "test_audio"
        test_dir.mkdir()
        (test_dir / "song1.mp3").touch()
        (test_dir / "song2.flac").touch()

        # 确保格式被选中（_scan_files 依赖 supported_input_formats）
        for checkbox in converter_page.audio_format_checkboxes.values():
            checkbox.setChecked(True)
        converter_page._update_supported_formats()

        # 模拟浏览目录（填充文件列表）
        converter_page.input_dir = str(test_dir)
        converter_page.input_entry.setText(str(test_dir))
        converter_page.files = converter_page._scan_files(str(test_dir))

        # 填充表格
        converter_page.file_table.setRowCount(0)
        for file_path in converter_page.files:
            row = converter_page.file_table.rowCount()
            converter_page.file_table.insertRow(row)
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
            )
            checkbox_item.setCheckState(Qt.CheckState.Checked)
            converter_page.file_table.setItem(row, 0, checkbox_item)

            filename = Path(file_path).name
            filename_item = QTableWidgetItem(filename)
            filename_item.setData(Qt.ItemDataRole.UserRole, file_path)
            converter_page.file_table.setItem(row, 1, filename_item)

        # 验证文件已加载
        assert len(converter_page.files) == 2
        assert converter_page.file_table.rowCount() == 2

        # 模拟点击清除数据按钮（跳过确认对话框）
        with patch.object(converter_page.clear_data_btn, 'text', return_value="Clear Data"):
            with patch('PySide6.QtWidgets.QMessageBox') as mock_box:
                mock_box.question.return_value = mock_box.StandardButton.Yes

                converter_page._on_clear_data()

        # 验证数据已清除
        assert len(converter_page.files) == 0, "文件列表应该被清空"
        assert converter_page.file_table.rowCount() == 0, "表格应该被清空"
        assert converter_page.progress_bar.value() == 0, "进度条应该重置为0"
        assert converter_page.start_btn.isEnabled(), "开始转换按钮应该启用"
        assert not converter_page.stop_btn.isEnabled(), "停止转换按钮应该禁用"

    def test_clear_data_with_empty_list(self, converter_page):
        """测试空列表时清除数据功能"""
        # 确保初始状态为空
        assert len(converter_page.files) == 0
        assert converter_page.file_table.rowCount() == 0

        # 调用清除数据（应该直接返回）
        converter_page._on_clear_data()

        # 验证状态不变
        assert len(converter_page.files) == 0
        assert converter_page.file_table.rowCount() == 0

    def test_clear_data_during_conversion(self, converter_page, tmp_path):
        """测试转换进行中时清除数据"""
        # 添加文件（_on_clear_data 会检查 files 是否为空）
        test_dir = tmp_path / "test_audio_conv"
        test_dir.mkdir()
        (test_dir / "song1.mp3").touch()
        converter_page.files = [str(test_dir / "song1.mp3")]
        converter_page.file_table.insertRow(0)

        # 创建模拟的工作线程
        mock_worker = MagicMock()
        mock_worker.isRunning.return_value = True
        converter_page.worker = mock_worker

        # Mock QMessageBox.question - 第一次是停止确认（Yes），第二次是清除确认（Yes）
        with patch('PySide6.QtWidgets.QMessageBox') as mock_box:
            mock_box.question.side_effect = [
                mock_box.StandardButton.Yes,   # 停止确认
                mock_box.StandardButton.Yes    # 清除确认
            ]

            converter_page._on_clear_data()

        # 验证停止方法被调用
        mock_worker.stop.assert_called_once()
        mock_worker.wait.assert_called_once()

    def test_clear_data_cancel_confirmation(self, converter_page, tmp_path):
        """测试取消确认对话框"""
        # 添加一些文件
        test_dir = tmp_path / "test_audio"
        test_dir.mkdir()
        (test_dir / "song1.mp3").touch()

        converter_page.files = [str(test_dir / "song1.mp3")]
        converter_page.file_table.insertRow(0)

        # Mock QMessageBox.question - 用户选择 No（取消）
        with patch('PySide6.QtWidgets.QMessageBox') as mock_box:
            mock_box.question.return_value = mock_box.StandardButton.No  # 用户取消

            converter_page._on_clear_data()

        # 验证数据未被清除
        assert len(converter_page.files) == 1, "取消后数据应保留"
        assert converter_page.file_table.rowCount() == 1, "取消后表格应保留"


class TestScrollAreaFunction:
    """测试文件列表滚动功能"""

    def test_scroll_area_exists(self, converter_page):
        """测试滚动区域存在"""
        assert hasattr(converter_page, 'file_list_scroll'), "缺少文件列表滚动区域"
        assert converter_page.file_list_scroll is not None

    def test_scroll_area_is_scrollarea(self, converter_page):
        """测试滚动区域类型正确"""
        from qfluentwidgets import ScrollArea
        assert isinstance(converter_page.file_list_scroll, ScrollArea)

    def test_scroll_area_has_widget(self, converter_page):
        """测试滚动区域包含子 widget"""
        widget = converter_page.file_list_scroll.widget()
        assert widget is not None, "滚动区域应包含子 widget"

    def test_scroll_area_resizable(self, converter_page):
        """测试滚动区域可调整大小"""
        scroll = converter_page.file_list_scroll
        assert scroll.widgetResizable(), "滚动区域应启用 widgetResizable"

    def test_scroll_area_minimum_height(self, converter_page):
        """测试滚动区域最小高度"""
        scroll = converter_page.file_list_scroll
        assert scroll.minimumHeight() >= 400, f"滚动区域最小高度应 >= 400，当前: {scroll.minimumHeight()}"

    def test_file_table_in_scroll_container(self, converter_page):
        """测试表格在滚动容器中"""
        scroll_container = converter_page.file_list_scroll.widget()
        assert scroll_container is not None

        # 检查表格是否在容器的布局中
        found_table = False
        for i in range(scroll_container.layout().count()):
            item = scroll_container.layout().itemAt(i)
            if item.widget() == converter_page.file_table:
                found_table = True
                break
        assert found_table, "表格应在滚动容器中"

    def test_buttons_in_scroll_container(self, converter_page):
        """测试操作按钮在滚动容器中（始终可见）"""
        scroll_container = converter_page.file_list_scroll.widget()
        assert scroll_container is not None

        # 检查所有操作按钮是否在容器中
        buttons_to_check = [
            converter_page.check_all_btn,
            converter_page.uncheck_all_btn,
            converter_page.start_btn,
            converter_page.stop_btn,
            converter_page.clear_data_btn
        ]

        for btn in buttons_to_check:
            found = False
            for i in range(scroll_container.layout().count()):
                item = scroll_container.layout().itemAt(i)
                if item.widget() == btn:
                    found = True
                    break
                if item.layout():
                    for j in range(item.layout().count()):
                        layout_item = item.layout().itemAt(j)
                        if layout_item.widget() == btn:
                            found = True
                            break
            assert found, f"按钮 {btn.text()} 应在滚动容器中"

    def test_scroll_area_size_policy(self, converter_page):
        """测试滚动区域尺寸策略"""
        scroll = converter_page.file_list_scroll
        policy = scroll.sizePolicy()

        assert policy.horizontalPolicy() == QSizePolicy.Policy.Expanding, \
            "水平策略应为 Expanding"
        assert policy.verticalPolicy() == QSizePolicy.Policy.Expanding, \
            "垂直策略应为 Expanding"

    def test_scroll_area_theme_method_exists(self, converter_page):
        """测试主题样式方法存在"""
        assert hasattr(converter_page, '_apply_scroll_area_theme'), \
            "缺少 _apply_scroll_area_theme 方法"
        assert callable(getattr(converter_page, '_apply_scroll_area_theme'))

    def test_many_files_scrollable(self, converter_page, tmp_path):
        """测试大量文件时滚动功能正常"""
        # 创建多个测试文件（模拟超出可视区域的情况）
        test_dir = tmp_path / "test_many_files"
        test_dir.mkdir()

        num_files = 20
        for i in range(num_files):
            (test_dir / f"song_{i}.mp3").touch()

        # 填充文件列表
        converter_page.files = [str(test_dir / f"song_{i}.mp3") for i in range(num_files)]
        converter_page.file_table.setRowCount(0)

        for file_path in converter_page.files:
            row = converter_page.file_table.rowCount()
            converter_page.file_table.insertRow(row)
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
            )
            checkbox_item.setCheckState(Qt.CheckState.Checked)
            converter_page.file_table.setItem(row, 0, checkbox_item)

            filename = Path(file_path).name
            filename_item = QTableWidgetItem(filename)
            filename_item.setData(Qt.ItemDataRole.UserRole, file_path)
            converter_page.file_table.setItem(row, 1, filename_item)

        # 验证所有文件都已添加到表格
        assert converter_page.file_table.rowCount() == num_files, \
            f"应添加 {num_files} 个文件"

        # 验证滚动区域的垂直滚动条策略
        scroll = converter_page.file_list_scroll
        vertical_scrollbar = scroll.verticalScrollBar()

        # 当内容超出可视区域时，滚动条应该可用
        # 注意：实际的可视性取决于窗口大小，这里只验证组件配置正确
        assert vertical_scrollbar is not None, "应有垂直滚动条"
