# -*- coding: utf-8 -*-
"""
auto_tag.gui.pages 模块

提供应用程序的各个页面组件。

导出组件：
- HomePage: 主页面
- SettingsPage: 设置页面

使用示例：
    from auto_tag.gui.pages import HomePage, SettingsPage

    home = HomePage()
    settings = SettingsPage()
"""

from .home_page import HomePage
from .settings_page import SettingsPage

__all__ = ['HomePage', 'SettingsPage']
