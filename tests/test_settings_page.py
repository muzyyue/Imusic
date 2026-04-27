# -*- coding: utf-8 -*-
"""
测试设置页面功能

测试内容：
    - SettingsPage 初始化
    - 语言切换功能
    - 主题切换功能
    - 配置持久化
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from auto_tag.gui.pages import SettingsPage
from auto_tag.gui.config import config, AppConfig
from auto_tag.gui.i18n import translator


# 创建 QApplication fixture
@pytest.fixture(scope="session")
def qapp():
    """创建 QApplication 实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # 不退出 QApplication，因为可能其他测试还需要使用


class TestSettingsPage:
    """测试设置页面类"""

    @pytest.fixture(autouse=True)
    def setup(self, qapp, tmp_path):
        """每个测试前的设置"""
        with patch("auto_tag.gui.config.Path.home", return_value=tmp_path):
            self.settings_page = SettingsPage()
            yield
            # 清理
            self.settings_page.deleteLater()

    def test_initialization(self):
        """测试页面初始化"""
        assert self.settings_page is not None
        assert self.settings_page._language_combo is not None
        assert self.settings_page._theme_combo is not None

    def test_language_combo_items(self):
        """测试语言下拉框内容"""
        assert self.settings_page._language_combo.count() == 2
        # settings_page 中 addItems 顺序: [tr("languages.zh"), tr("languages.en")]
        # 所以索引 0 是中文，索引 1 是英文
        assert self.settings_page._language_combo.itemText(0) == "简体中文"
        assert self.settings_page._language_combo.itemText(1) == "English"

    def test_theme_combo_items(self):
        """测试主题下拉框内容"""
        assert self.settings_page._theme_combo.count() == 3
        # 使用翻译后的中文文本（默认语言为 zh）
        assert "浅色" in self.settings_page._theme_combo.itemText(0)
        assert "深色" in self.settings_page._theme_combo.itemText(1)
        assert "系统" in self.settings_page._theme_combo.itemText(2)

    def test_language_change_signal(self, qapp):
        """测试语言切换信号"""
        # 记录信号是否被发射
        signal_received = []

        def on_language_changed(lang):
            signal_received.append(lang)

        self.settings_page.language_changed.connect(on_language_changed)

        # settings_page 中 lang_code_map = {0: "zh", 1: "en"}
        # 默认 config.language == "zh"，所以 current_lang_index = 0
        current_index = self.settings_page._language_combo.currentIndex()
        new_index = 1 if current_index == 0 else 0

        # 切换语言
        self.settings_page._language_combo.setCurrentIndex(new_index)

        # 验证信号被发射
        assert len(signal_received) == 1
        # 索引 0 -> zh, 索引 1 -> en
        expected_lang = "en" if new_index == 1 else "zh"
        assert signal_received[0] == expected_lang

    def test_theme_change_signal(self, qapp):
        """测试主题切换信号"""
        # 记录信号是否被发射
        signal_received = []

        def on_theme_changed(theme):
            signal_received.append(theme)

        self.settings_page.theme_changed.connect(on_theme_changed)

        # 切换主题到索引 0 (light)
        self.settings_page._theme_combo.setCurrentIndex(0)

        # 验证信号被发射
        assert len(signal_received) == 1
        assert signal_received[0] == "light"

    def test_language_persistence(self):
        """测试语言配置持久化"""
        # 切换到索引 1 (en)
        self.settings_page._language_combo.setCurrentIndex(1)

        # 验证配置已更新 (索引 1 -> en)
        assert config.language == "en"

        # 切换回索引 0 (zh)
        self.settings_page._language_combo.setCurrentIndex(0)
        assert config.language == "zh"

    def test_theme_persistence(self):
        """测试主题配置持久化"""
        # 切换主题到索引 1 (dark)
        self.settings_page._theme_combo.setCurrentIndex(1)

        # 验证配置已更新
        assert config.theme == "dark"

        # 切换回索引 2 (auto)
        self.settings_page._theme_combo.setCurrentIndex(2)
        assert config.theme == "auto"

    def test_translator_language_change(self):
        """测试翻译器语言切换"""
        # 切换到索引 1 (en)
        self.settings_page._language_combo.setCurrentIndex(1)
        assert translator.current_language == "en"

        # 切换回索引 0 (zh)
        self.settings_page._language_combo.setCurrentIndex(0)
        assert translator.current_language == "zh"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
