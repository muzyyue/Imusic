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

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from auto_tag.gui.pages import SettingsPage
from auto_tag.gui.config import config
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
    def setup(self, qapp):
        """每个测试前的设置"""
        self.settings_page = SettingsPage()
        yield
        # 清理
        self.settings_page.deleteLater()

    def test_initialization(self):
        """测试页面初始化"""
        assert self.settings_page is not None
        assert self.settings_page.language_combo is not None
        assert self.settings_page.theme_combo is not None

    def test_language_combo_items(self):
        """测试语言下拉框内容"""
        assert self.settings_page.language_combo.count() == 2
        assert self.settings_page.language_combo.itemText(0) == "English"
        assert self.settings_page.language_combo.itemText(1) == "中文"

    def test_theme_combo_items(self):
        """测试主题下拉框内容"""
        assert self.settings_page.theme_combo.count() == 3
        # 注意：这里使用翻译后的文本
        assert "Light" in self.settings_page.theme_combo.itemText(0)
        assert "Dark" in self.settings_page.theme_combo.itemText(1)
        assert "System" in self.settings_page.theme_combo.itemText(2)

    def test_language_change_signal(self, qapp):
        """测试语言切换信号"""
        # 记录信号是否被发射
        signal_received = []
        
        def on_language_changed(lang):
            signal_received.append(lang)
        
        self.settings_page.language_changed.connect(on_language_changed)
        
        # 获取当前索引，然后切换到不同的索引
        current_index = self.settings_page.language_combo.currentIndex()
        new_index = 1 if current_index == 0 else 0
        
        # 切换语言
        self.settings_page.language_combo.setCurrentIndex(new_index)
        
        # 验证信号被发射
        assert len(signal_received) == 1
        expected_lang = "zh" if new_index == 1 else "en"
        assert signal_received[0] == expected_lang

    def test_theme_change_signal(self, qapp):
        """测试主题切换信号"""
        # 记录信号是否被发射
        signal_received = []
        
        def on_theme_changed(theme):
            signal_received.append(theme)
        
        self.settings_page.theme_changed.connect(on_theme_changed)
        
        # 切换主题
        self.settings_page.theme_combo.setCurrentIndex(0)
        
        # 验证信号被发射
        assert len(signal_received) == 1
        assert signal_received[0] == "light"

    def test_language_persistence(self):
        """测试语言配置持久化"""
        # 切换语言
        self.settings_page.language_combo.setCurrentIndex(1)

        # 验证配置已更新
        assert config.language == "zh"

        # 切换回英文
        self.settings_page.language_combo.setCurrentIndex(0)
        assert config.language == "en"

    def test_theme_persistence(self):
        """测试主题配置持久化"""
        # 切换主题
        self.settings_page.theme_combo.setCurrentIndex(1)

        # 验证配置已更新
        assert config.theme == "dark"

        # 切换回自动
        self.settings_page.theme_combo.setCurrentIndex(2)
        assert config.theme == "auto"

    def test_translator_language_change(self):
        """测试翻译器语言切换"""
        # 切换到中文
        self.settings_page.language_combo.setCurrentIndex(1)
        assert translator.current_language == "zh"

        # 切换到英文
        self.settings_page.language_combo.setCurrentIndex(0)
        assert translator.current_language == "en"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
