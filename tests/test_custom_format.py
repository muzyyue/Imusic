# -*- coding: utf-8 -*-
"""
CustomFormatManager 单元测试

测试自定义文件格式的增删改查功能，包括：
- 格式添加与验证
- 格式删除
- 格式编辑
- 配置持久化
- 与ConverterPage的集成
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from auto_tag.converter.custom_format import CustomFormat, CustomFormatManager


class TestCustomFormat:
    """测试 CustomFormat 数据类"""

    def test_init_with_defaults(self):
        """测试默认初始化"""
        fmt = CustomFormat(extension="opus")
        assert fmt.extension == "opus"
        assert fmt.description == "OPUS"
        assert fmt.is_custom is True

    def test_init_with_description(self):
        """测试带描述的初始化"""
        fmt = CustomFormat(extension="flac", description="Free Lossless Audio Codec")
        assert fmt.extension == "flac"
        assert fmt.description == "Free Lossless Audio Codec"

    def test_post_init_normalization(self):
        """测试后处理：扩展名标准化"""
        fmt = CustomFormat(extension="  .MP3  ")
        assert fmt.extension == "mp3"


class TestCustomFormatManager:
    """测试 CustomFormatManager 管理器"""

    @pytest.fixture
    def manager(self):
        """创建格式管理器实例"""
        return CustomFormatManager()

    def test_add_valid_format(self, manager):
        """测试添加有效格式"""
        success, error = manager.add_format("opus", "Opus Audio")
        assert success is True
        assert error == ""
        assert len(manager.custom_formats) == 1
        assert manager.custom_formats[0].extension == "opus"

    def test_add_empty_extension(self, manager):
        """测试添加空扩展名"""
        success, error = manager.add_format("", "Test")
        assert success is False
        assert "不能为空" in error

    def test_add_invalid_characters(self, manager):
        """测试包含非法字符的扩展名"""
        success, error = manager.add_format("mp@3", "Test")
        assert success is False
        assert "只能包含" in error

    def test_add_too_long_extension(self, manager):
        """测试过长的扩展名"""
        long_ext = "a" * 11
        success, error = manager.add_format(long_ext, "Test")
        assert success is False
        assert "长度" in error or "10" in error

    def test_add_builtin_format(self, manager):
        """尝试添加内置格式（应失败）"""
        success, error = manager.add_format("mp3", "MP3 Format")
        assert success is False
        assert "内置" in error

    def test_duplicate_format(self, manager):
        """测试重复添加格式"""
        manager.add_format("opus", "Opus")
        success, error = manager.add_format("opus", "Another Opus")
        assert success is False
        assert "已存在" in error

    def test_remove_custom_format(self, manager):
        """测试删除自定义格式"""
        manager.add_format("opus", "Opus")
        success, error = manager.remove_format("opus")
        assert success is True
        assert len(manager.custom_formats) == 0

    def test_remove_builtin_format(self, manager):
        """尝试删除内置格式（应失败）"""
        success, error = manager.remove_format("mp3")
        assert success is False
        assert "无法删除" in error or "内置" in error

    def test_remove_nonexistent_format(self, manager):
        """测试删除不存在的格式"""
        success, error = manager.remove_format("xyz")
        assert success is False
        assert "未找到" in error

    def test_update_format(self, manager):
        """测试更新格式描述"""
        manager.add_format("opus", "Opus")
        success, error = manager.update_format("opus", "Updated Opus Description")
        assert success is True
        assert manager.custom_formats[0].description == "Updated Opus Description"

    def test_update_nonexistent_format(self, manager):
        """测试更新不存在的格式"""
        success, error = manager.update_format("xyz", "New Desc")
        assert success is False
        assert "未找到" in error

    def test_get_all_extensions(self, manager):
        """测试获取所有扩展名（包括内置）"""
        manager.add_format("opus", "Opus")
        all_exts = manager.get_all_extensions()

        # 应该包含内置格式
        assert "mp3" in all_exts
        assert "opus" in all_exts

        # 应该是排序的
        assert all_exts == sorted(all_exts)

    def test_get_custom_formats(self, manager):
        """测试获取自定义格式列表"""
        manager.add_format("opus", "Opus")
        manager.add_format("wma", "WMA Audio")

        custom = manager.get_custom_formats()
        assert len(custom) == 2
        assert all(fmt.is_custom for fmt in custom)

    def test_get_builtin_formats(self, manager):
        """测试获取内置格式列表"""
        builtin = manager.get_builtin_formats()
        assert "mp3" in builtin
        assert "mp4" in builtin
        # 不应该包含自定义格式
        assert "opus" not in builtin

    def test_clear_custom_formats(self, manager):
        """测试清空自定义格式"""
        manager.add_format("opus", "Opus")
        manager.add_format("wma", "WMA Audio")
        assert len(manager.custom_formats) == 2

        manager.clear_custom_formats()
        assert len(manager.custom_formats) == 0

    def test_is_builtin_format(self):
        """测试判断是否为内置格式"""
        assert CustomFormatManager.is_builtin_format("mp3") is True
        assert CustomFormatManager.is_builtin_format("MP3") is True
        assert CustomFormatManager.is_builtin_format(".mp3") is True
        assert CustomFormatManager.is_builtin_format("opus") is False

    def test_to_dict_list(self, manager):
        """测试序列化为字典列表"""
        manager.add_format("opus", "Opus")
        data = manager.to_dict_list()

        assert len(data) == 1
        assert data[0]["extension"] == "opus"
        assert data[0]["description"] == "Opus"
        assert data[0]["is_custom"] is True

    def test_from_dict_list(self):
        """测试从字典列表反序列化"""
        data = [
            {"extension": "opus", "description": "Opus Audio"},
            {"extension": "wma", "description": "WMA Audio"}
        ]

        manager = CustomFormatManager.from_dict_list(data)
        assert len(manager.custom_formats) == 2
        assert manager.custom_formats[0].extension == "opus"
        assert manager.custom_formats[1].extension == "wma"

    def test_from_dict_list_invalid_data(self):
        """测试从无效数据反序列化（应跳过错误项）"""
        data = [
            {"extension": "opus", "description": "Valid"},
            {},  # 无效项
            {"no_extension": "test"}  # 缺少 extension 字段
        ]

        manager = CustomFormatManager.from_dict_list(data)
        # 只应该成功加载一个有效项
        assert len(manager.custom_formats) >= 1


class TestCustomFormatIntegration:
    """测试自定义格式与 ConverterPage 的集成"""

    def test_custom_format_in_scan_files(self, tmp_path):
        """测试自定义格式能被扫描到"""
        from auto_tag.converter.config import ConverterConfig
        from auto_tag.gui.pages.converter_page import ConverterPage
        from PySide6.QtWidgets import QApplication
        import os

        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        with patch("auto_tag.gui.config.Path.home", return_value=tmp_path):
            page = ConverterPage()

            # 添加自定义格式
            from auto_tag.gui.config import config as global_config

            global_config.custom_formats_manager.add_format("opus", "Opus")

            # 更新页面支持的格式列表
            page._update_supported_formats()

            # 创建测试文件
            test_dir = tmp_path / "test_custom"
            test_dir.mkdir()
            (test_dir / "song.opus").touch()

            # 扫描文件
            files = page._scan_files(str(test_dir))

            # 验证自定义格式被识别
            file_names = [Path(f).name for f in files]
            assert "song.opus" in file_names

    def test_config_persistence_for_custom_formats(self, tmp_path):
        """测试自定义格式配置持久化"""
        from auto_tag.gui.config import AppConfig

        with patch("auto_tag.gui.config.Path.home", return_value=tmp_path):
            cfg = AppConfig()

            # 添加自定义格式
            cfg.custom_formats_manager.add_format("opus", "Opus Audio")
            cfg.save()

            # 创建新实例
            cfg2 = AppConfig()

            # 验证配置已加载
            custom_formats = cfg2.custom_formats_manager.get_custom_formats()
            assert len(custom_formats) == 1
            assert custom_formats[0].extension == "opus"
            assert custom_formats[0].description == "Opus Audio"
