# -*- coding: utf-8 -*-
"""
MP3 Shazam Auto Tag GUI 模块

提供基于 QFluentWidgets 的 Fluent Design 风格用户界面。

功能：
    - Fluent Design 风格主窗口
    - 国际化支持（英文/中文）
    - 主题切换支持（浅色/深色/跟随系统）
    - 音频文件识别与标签更新

使用示例：
    from auto_tag.gui import launch_gui

    launch_gui()
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from qfluentwidgets import setTheme, Theme

from auto_tag.gui.main_window import MainWindow
from auto_tag.gui.config import config
from auto_tag.gui.i18n import translator


def launch_gui() -> None:
    """
    启动 GUI 应用程序

    创建 QApplication 和主窗口，进入事件循环。
    从配置文件加载主题和语言设置。

    该函数是 GUI 模块的入口点，通常由 main.py 调用。

    Example:
        >>> from auto_tag.gui import launch_gui
        >>> launch_gui()
    """
    # 高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 创建应用
    app = QApplication(sys.argv)

    # 应用配置中的主题
    theme_map = {
        "light": Theme.LIGHT,
        "dark": Theme.DARK,
        "auto": Theme.AUTO
    }
    setTheme(theme_map.get(config.theme, Theme.AUTO))

    # 应用配置中的语言
    translator.load_language(config.language)

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 进入事件循环
    sys.exit(app.exec())


__all__ = ["MainWindow", "launch_gui"]
