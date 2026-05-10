# -*- coding: utf-8 -*-
"""
主窗口模块

该模块提供应用程序的主窗口，基于 QFluentWidgets 的 FluentWindow 实现。
包含侧边导航栏，支持在主页和设置页面之间切换。

功能：
    - Fluent Design 风格主窗口
    - 侧边导航栏
    - 主题切换支持
    - 语言切换支持

使用示例：
    from auto_tag.gui.main_window import MainWindow

    window = MainWindow()
    window.show()
"""

import os
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from qfluentwidgets import (
    FluentWindow,
    FluentIcon as FIF,
    setTheme,
    Theme,
    NavigationItemPosition,
)

from auto_tag.gui.pages import HomePage, SettingsPage, ConverterPage, MusicManagerPage, EditorPage, AboutPage
from auto_tag.gui.i18n import tr, translator
from auto_tag.gui.config import config


def _base_dir() -> str:
    """
    获取项目根目录或 PyInstaller 临时目录

    Returns:
        str: 项目根目录路径
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, os.pardir, os.pardir))


class MainWindow(FluentWindow):
    """
    应用程序主窗口

    继承自 FluentWindow，提供 Fluent Design 风格的用户界面。
    包含侧边导航栏，支持在主页和设置页面之间切换。

    Attributes:
        home_page (HomePage): 主页面实例
        converter_page (ConverterPage): 转换页面实例
        music_manager_page (MusicManagerPage): 音乐管理页面实例
        settings_page (SettingsPage): 设置页面实例

    Example:
        >>> window = MainWindow()
        >>> window.show()
    """

    def __init__(self) -> None:
        """
        初始化主窗口

        创建主窗口，设置窗口属性，
        先从配置加载语言，再创建页面和导航项，
        确保所有 tr() 调用都能获取正确的翻译。
        """
        super().__init__()

        # 设置窗口属性（应用名称固定，不随语言切换）
        self.setWindowTitle("Imusic")
        # 窗口尺寸：适中大小，高度不超过屏幕 70%
        self.resize(1200, 880)
        # 允许手动调整窗口大小
        self.setMinimumSize(900, 500)
        self.setMaximumSize(1920, 1080)

        # 先从配置加载语言，确保后续 tr() 调用使用正确的语言
        self._load_language()

        # 再加载主题
        self._apply_theme_from_config()

        # 创建页面并设置 objectName（QFluentWidgets 要求）
        self.home_page = HomePage(self)
        self.home_page.setObjectName("home_page")

        self.converter_page = ConverterPage(self)
        self.converter_page.setObjectName("converter_page")

        self.music_manager_page = MusicManagerPage(self)
        self.music_manager_page.setObjectName("music_manager_page")

        self.editor_page = EditorPage(self)
        self.editor_page.setObjectName("editor_page")

        self.settings_page = SettingsPage(self)
        self.settings_page.setObjectName("settings_page")

        self.about_page = AboutPage(self)
        self.about_page.setObjectName("about_page")

        # 添加导航项
        self._setup_navigation()

        # 连接设置页面信号
        self._connect_signals()

        # 隐藏返回按钮（FluentWindow 默认显示）
        self.navigationInterface.setReturnButtonVisible(False)

        # 设置窗口图标
        self._setup_icon()

    def _setup_navigation(self) -> None:
        """
        设置导航项

        在侧边导航栏中添加主页、转换、音乐管理和设置页面的导航项。
        """
        # 添加主页导航项
        self.addSubInterface(
            self.home_page,
            FIF.HOME,
            tr("home")
        )

        # 添加转换导航项
        self.addSubInterface(
            self.converter_page,
            FIF.MUSIC,
            tr("navigation.converter")
        )

        # 添加音乐管理导航项
        self.addSubInterface(
            self.music_manager_page,
            FIF.EDIT,
            tr("navigation.music_manager")
        )

        # 添加音频编辑导航项
        self.addSubInterface(
            self.editor_page,
            FIF.VOLUME,
            tr("navigation.editor")
        )

        # 添加关于导航项（底部）
        self.addSubInterface(
            self.about_page,
            FIF.INFO,
            tr("about"),
            position=NavigationItemPosition.BOTTOM
        )

        # 添加设置导航项（底部）
        self.addSubInterface(
            self.settings_page,
            FIF.SETTING,
            tr("settings"),
            position=NavigationItemPosition.BOTTOM
        )

    def _apply_theme_from_config(self) -> None:
        """
        从配置文件应用主题设置

        根据配置文件中的主题设置，应用对应的主题。
        """
        theme_map = {
            "light": Theme.LIGHT,
            "dark": Theme.DARK,
            "auto": Theme.AUTO
        }
        theme = theme_map.get(config.theme, Theme.AUTO)
        setTheme(theme)

    def _load_language(self) -> None:
        """
        从配置文件加载语言翻译

        仅加载语言文件，不刷新 UI。
        """
        translator.load_language(config.language)

    def _apply_language_from_config(self) -> None:
        """
        刷新所有页面和导航项的文本为当前语言

        仅在各页面和导航项已创建后调用。
        """
        # 刷新导航项文本
        nav_keys = ["home_page", "converter_page", "music_manager_page", "editor_page", "about_page", "settings_page"]
        tr_keys = ["home", "navigation.converter", "navigation.music_manager", "navigation.editor", "about", "settings"]
        for nav_key, tr_key in zip(nav_keys, tr_keys):
            nav_item = self.navigationInterface.widget(nav_key)
            if nav_item is not None:
                nav_item.setText(tr(tr_key))

        # 刷新各页面文本
        if hasattr(self.home_page, 'refresh_texts'):
            self.home_page.refresh_texts()
        if hasattr(self.converter_page, 'refresh_texts'):
            self.converter_page.refresh_texts()
        if hasattr(self.music_manager_page, 'refresh_texts'):
            self.music_manager_page.refresh_texts()
        if hasattr(self.editor_page, 'refresh_texts'):
            self.editor_page.refresh_texts()
        if hasattr(self.about_page, 'refresh_texts'):
            self.about_page.refresh_texts()
        if hasattr(self.settings_page, 'refresh_texts'):
            self.settings_page.refresh_texts()

    def _connect_signals(self) -> None:
        """
        连接信号槽

        连接设置页面的语言切换和主题切换信号到对应的回调函数。
        """
        self.settings_page.language_changed.connect(self._on_language_changed)
        self.settings_page.theme_changed.connect(self._on_theme_changed)

    def _setup_icon(self) -> None:
        """
        设置窗口图标

        尝试从 assets 目录加载应用图标。
        """
        try:
            icon_path = os.path.join(_base_dir(), "assets", "imusic.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

    def _on_language_changed(self, lang: str) -> None:
        """
        语言切换回调

        当用户在设置页面切换语言时，
        通知所有页面刷新文本（应用名称保持不变）。

        Args:
            lang (str): 新的语言代码，如 "en" 或 "zh"
        """
        # 更新侧边栏导航项文本
        nav_keys = ["home_page", "converter_page", "music_manager_page", "editor_page", "about_page", "settings_page"]
        tr_keys = ["home", "navigation.converter", "navigation.music_manager", "navigation.editor", "about", "settings"]
        for nav_key, tr_key in zip(nav_keys, tr_keys):
            nav_item = self.navigationInterface.widget(nav_key)
            if nav_item is not None:
                nav_item.setText(tr(tr_key))

        # 通知各页面刷新文本
        if hasattr(self.home_page, 'refresh_texts'):
            self.home_page.refresh_texts()
        if hasattr(self.converter_page, 'refresh_texts'):
            self.converter_page.refresh_texts()
        if hasattr(self.music_manager_page, 'refresh_texts'):
            self.music_manager_page.refresh_texts()
        if hasattr(self.editor_page, 'refresh_texts'):
            self.editor_page.refresh_texts()
        if hasattr(self.about_page, 'refresh_texts'):
            self.about_page.refresh_texts()
        if hasattr(self.settings_page, 'refresh_texts'):
            self.settings_page.refresh_texts()

    def _on_theme_changed(self, theme: str) -> None:
        """
        主题切换回调

        当用户在设置页面切换主题时，应用新的主题设置。

        Args:
            theme (str): 新的主题名称，如 "light"、"dark" 或 "auto"
        """
        theme_map = {
            "light": Theme.LIGHT,
            "dark": Theme.DARK,
            "auto": Theme.AUTO
        }
        new_theme = theme_map.get(theme, Theme.AUTO)
        setTheme(new_theme)
