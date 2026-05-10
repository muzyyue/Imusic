# -*- coding: utf-8 -*-
"""
关于页面模块

该模块提供应用程序的关于界面，展示项目相关信息。
使用 QFluentWidgets 库实现现代化的 Fluent Design 风格界面。

功能：
    - 应用信息展示（名称、版本号）
    - 检查更新按钮
    - 更新设置（自动检查更新开关）
    - 反馈链接（报告错误、建议功能、讨论区）
    - 其他链接（GitHub 仓库、许可证）

依赖：
    - PySide6: GUI 框架
    - qfluentwidgets: Fluent Design 风格组件库
    - auto_tag.gui.i18n: 国际化支持

Example:
    >>> from auto_tag.gui.pages.about_page import AboutPage
    >>> page = AboutPage()
    >>> page.show()
"""

import os
import sys
from typing import Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QDesktopServices, QCursor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)

from qfluentwidgets import (
    BodyLabel,
    SubtitleLabel,
    PushButton,
    SwitchButton,
    FluentIcon as FIF,
)

from auto_tag.gui.i18n import tr


def _base_dir() -> str:
    """
    获取项目根目录或 PyInstaller 临时目录

    Returns:
        str: 项目根目录路径
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, os.pardir, os.pardir, os.pardir))


def _get_version() -> str:
    """
    从 pyproject.toml 读取版本号

    Returns:
        str: 版本号字符串，读取失败时返回 "unknown"
    """
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            return "unknown"

    pyproject_path = os.path.join(_base_dir(), "pyproject.toml")
    if not os.path.exists(pyproject_path):
        return "unknown"

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return data.get("project", {}).get("version", "unknown")
    except Exception:
        return "unknown"


class AboutPage(QWidget):
    """
    关于页面类

    提供应用程序关于界面，展示项目相关信息和外部链接。

    Example:
        >>> page = AboutPage()
        >>> page.show()
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        初始化关于页面

        Args:
            parent: 父窗口，默认为 None
        """
        super().__init__(parent)

        self._version = _get_version()
        self._github_url = "https://github.com/ling/Imusic"
        self._issues_url = "https://github.com/ling/Imusic/issues"
        self._discussions_url = "https://github.com/ling/Imusic/discussions"
        self._license_url = "https://github.com/ling/Imusic/blob/main/LICENSE"

        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        初始化 UI

        创建关于页面的所有控件和布局。
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        # 页面标题
        self._title_label = SubtitleLabel(tr("about_page.title"))
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self._title_label.setFont(font)
        main_layout.addWidget(self._title_label)

        # 应用信息行：图标 + 名称 + 版本
        app_info_layout = QHBoxLayout()
        app_info_layout.setSpacing(16)

        self._app_icon_label = QLabel()
        self._app_icon_label.setFixedSize(48, 48)
        self._load_app_icon()
        app_info_layout.addWidget(self._app_icon_label)

        app_text_layout = QVBoxLayout()
        app_text_layout.setSpacing(4)

        self._app_name_label = BodyLabel("Imusic")
        name_font = QFont()
        name_font.setPointSize(16)
        name_font.setBold(True)
        self._app_name_label.setFont(name_font)
        app_text_layout.addWidget(self._app_name_label)

        self._version_label = BodyLabel(
            f"{tr('about_page.version_prefix')} {self._version}"
        )
        app_text_layout.addWidget(self._version_label)

        app_info_layout.addLayout(app_text_layout)
        app_info_layout.addStretch()
        main_layout.addLayout(app_info_layout)

        # 检查更新按钮
        self._check_update_button = PushButton(tr("about_page.check_update"))
        self._check_update_button.setFixedHeight(36)
        self._check_update_button.setFixedWidth(120)
        self._check_update_button.clicked.connect(self._on_check_update_clicked)
        main_layout.addWidget(self._check_update_button)

        # 更新设置分组
        self._update_settings_section = SubtitleLabel(tr("about_page.update_settings"))
        section_font = QFont()
        section_font.setPointSize(14)
        self._update_settings_section.setFont(section_font)
        main_layout.addWidget(self._update_settings_section)

        auto_update_layout = QHBoxLayout()
        self._auto_update_icon = QLabel("🔄")
        self._auto_update_icon.setFixedWidth(24)
        auto_update_layout.addWidget(self._auto_update_icon)

        self._auto_update_label = BodyLabel(tr("about_page.auto_check_update"))
        auto_update_layout.addWidget(self._auto_update_label)
        auto_update_layout.addStretch()

        self._auto_update_switch = SwitchButton()
        self._auto_update_switch.setChecked(False)
        auto_update_layout.addWidget(self._auto_update_switch)
        main_layout.addLayout(auto_update_layout)

        # 反馈分组
        self._feedback_section = SubtitleLabel(tr("about_page.feedback"))
        self._feedback_section.setFont(section_font)
        main_layout.addWidget(self._feedback_section)

        self._report_bug_row = self._create_link_row(
            "🐛", tr("about_page.report_bug"), self._issues_url
        )
        main_layout.addWidget(self._report_bug_row)

        self._suggest_feature_row = self._create_link_row(
            "💡", tr("about_page.suggest_feature"), self._issues_url
        )
        main_layout.addWidget(self._suggest_feature_row)

        self._discussions_row = self._create_link_row(
            "💬", tr("about_page.discussions"), self._discussions_url
        )
        main_layout.addWidget(self._discussions_row)

        # 其他链接分组
        self._other_links_section = SubtitleLabel(tr("about_page.other_links"))
        self._other_links_section.setFont(section_font)
        main_layout.addWidget(self._other_links_section)

        self._github_repo_row = self._create_link_row(
            "📦", tr("about_page.github_repo"), self._github_url
        )
        main_layout.addWidget(self._github_repo_row)

        self._license_row = self._create_link_row(
            "📄", tr("about_page.license"), self._license_url
        )
        main_layout.addWidget(self._license_row)

        # 弹性空间
        main_layout.addStretch()

    def _load_app_icon(self) -> None:
        """
        加载应用图标到图标标签

        尝试从 assets 目录加载 imusic.ico，失败则留空。
        """
        try:
            from PySide6.QtGui import QPixmap

            icon_path = os.path.join(_base_dir(), "assets", "imusic.ico")
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        48, 48,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self._app_icon_label.setPixmap(scaled)
        except Exception:
            pass

    def _create_link_row(self, icon_text: str, text: str, url: str) -> QWidget:
        """
        创建可点击的链接行

        Args:
            icon_text: 图标文本（emoji）
            text: 显示的文本
            url: 点击后打开的 URL

        Returns:
            QWidget: 可点击的行控件
        """
        row = QWidget()
        row.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout = QHBoxLayout(row)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        icon_label = QLabel(icon_text)
        icon_label.setFixedWidth(24)
        layout.addWidget(icon_label)

        text_label = BodyLabel(text)
        layout.addWidget(text_label)
        layout.addStretch()

        arrow_label = BodyLabel("↗")
        arrow_label.setStyleSheet("color: gray;")
        layout.addWidget(arrow_label)

        row.mousePressEvent = lambda _event: self._open_url(url)  # type: ignore[method-assign]

        return row

    def _open_url(self, url: str) -> None:
        """
        使用系统默认浏览器打开 URL

        Args:
            url: 要打开的 URL 字符串
        """
        QDesktopServices.openUrl(QUrl(url))

    def _on_check_update_clicked(self) -> None:
        """
        检查更新按钮点击回调

        打开 GitHub Releases 页面检查更新。
        """
        QDesktopServices.openUrl(QUrl(f"{self._github_url}/releases"))

    def refresh_texts(self) -> None:
        """
        刷新页面文本

        当语言切换时调用此方法，更新所有 UI 文本为当前语言的翻译。
        """
        self._title_label.setText(tr("about_page.title"))
        self._version_label.setText(
            f"{tr('about_page.version_prefix')} {self._version}"
        )
        self._check_update_button.setText(tr("about_page.check_update"))
        self._update_settings_section.setText(tr("about_page.update_settings"))
        self._auto_update_label.setText(tr("about_page.auto_check_update"))
        self._feedback_section.setText(tr("about_page.feedback"))
        self._other_links_section.setText(tr("about_page.other_links"))

        # 刷新链接行文本（通过重新创建或查找子控件）
        self._refresh_link_row_text(self._report_bug_row, "🐛", tr("about_page.report_bug"))
        self._refresh_link_row_text(self._suggest_feature_row, "💡", tr("about_page.suggest_feature"))
        self._refresh_link_row_text(self._discussions_row, "💬", tr("about_page.discussions"))
        self._refresh_link_row_text(self._github_repo_row, "📦", tr("about_page.github_repo"))
        self._refresh_link_row_text(self._license_row, "📄", tr("about_page.license"))

    def _refresh_link_row_text(self, row: QWidget, icon_text: str, text: str) -> None:
        """
        刷新链接行的文本标签

        Args:
            row: 链接行控件
            icon_text: 图标文本
            text: 新的显示文本
        """
        labels = row.findChildren(BodyLabel)
        if labels:
            labels[0].setText(text)
