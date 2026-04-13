# -*- coding: utf-8 -*-
"""
auto_tag.gui.pages.settings_page 模块

提供应用程序设置页面，支持语言和主题切换。

功能：
    - 语言切换（English/中文）
    - 主题切换（Light/Dark/Follow System）
    - 配置持久化存储
    - 实时语言切换

使用示例：
    from auto_tag.gui.pages import SettingsPage

    settings_page = SettingsPage()
    settings_page.language_changed.connect(on_language_changed)
    settings_page.theme_changed.connect(on_theme_changed)
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal
from qfluentwidgets import (
    BodyLabel,
    SubtitleLabel,
    ComboBox,
    FluentIcon as FIF,
    setTheme,
    Theme,
)
from auto_tag.gui.i18n import tr, translator
from auto_tag.gui.config import config


class SettingsPage(QWidget):
    """
    设置页面组件

    提供语言和主题切换功能，支持配置持久化。

    Signals:
        language_changed (str): 语言切换信号，参数为语言代码（"en" 或 "zh"）
        theme_changed (str): 主题切换信号，参数为主题名称（"light"、"dark" 或 "auto"）

    Attributes:
        language_combo (ComboBox): 语言选择下拉框
        theme_combo (ComboBox): 主题选择下拉框

    Example:
        >>> page = SettingsPage()
        >>> page.language_changed.connect(lambda lang: print(f"语言切换为: {lang}"))
        >>> page.theme_changed.connect(lambda theme: print(f"主题切换为: {theme}"))
    """

    # 定义信号
    language_changed = Signal(str)  # 语言切换信号
    theme_changed = Signal(str)  # 主题切换信号

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        初始化设置页面

        Args:
            parent: 父组件，默认为 None

        初始化流程：
            1. 调用父类构造函数
            2. 构建 UI 布局
            3. 从 config 加载当前设置
            4. 连接信号槽
        """
        super().__init__(parent)

        # 初始化组件引用
        self.language_combo: ComboBox | None = None
        self.theme_combo: ComboBox | None = None

        # 构建 UI
        self._setup_ui()

        # 连接信号槽
        self._connect_signals()

    def _setup_ui(self) -> None:
        """
        构建 UI 布局

        创建页面标题、语言设置区域和主题设置区域。
        使用 QVBoxLayout 进行垂直布局，设置合理的边距和间距。
        """
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)  # 设置边距
        layout.setSpacing(24)  # 设置组件间距

        # 添加页面标题
        title_label = SubtitleLabel(tr("settings"))
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)

        # 添加语言设置区域
        language_label = BodyLabel(tr("language"))
        layout.addWidget(language_label)

        # 创建语言选择下拉框
        self.language_combo = ComboBox()
        self.language_combo.addItems(["English", "中文"])
        self.language_combo.setFixedHeight(40)

        # 根据当前配置设置语言下拉框的当前索引
        current_lang = config.language
        lang_index = 0 if current_lang == "en" else 1
        self.language_combo.setCurrentIndex(lang_index)

        layout.addWidget(self.language_combo)

        # 添加主题设置区域
        theme_label = BodyLabel(tr("theme"))
        layout.addWidget(theme_label)

        # 创建主题选择下拉框
        self.theme_combo = ComboBox()
        self.theme_combo.addItems([
            tr("theme_light"),
            tr("theme_dark"),
            tr("theme_auto")
        ])
        self.theme_combo.setFixedHeight(40)

        # 根据当前配置设置主题下拉框的当前索引
        current_theme = config.theme
        theme_map = {"light": 0, "dark": 1, "auto": 2}
        theme_index = theme_map.get(current_theme, 2)  # 默认为 auto
        self.theme_combo.setCurrentIndex(theme_index)

        layout.addWidget(self.theme_combo)

        # 添加弹性空间，使内容顶部对齐
        layout.addStretch(1)

    def _connect_signals(self) -> None:
        """
        连接信号槽

        将语言和主题下拉框的 currentIndexChanged 信号
        连接到对应的回调函数。
        """
        if self.language_combo:
            self.language_combo.currentIndexChanged.connect(
                self._on_language_changed
            )

        if self.theme_combo:
            self.theme_combo.currentIndexChanged.connect(
                self._on_theme_changed
            )

    def _on_language_changed(self, index: int) -> None:
        """
        语言切换回调函数

        根据下拉框索引确定语言代码，更新翻译器和配置，
        并发射语言切换信号。

        Args:
            index: 下拉框当前索引
                   - 0: English ("en")
                   - 1: 中文 ("zh")

        处理流程：
            1. 根据索引确定语言代码
            2. 调用 translator.load_language() 加载新语言
            3. 调用 config.set_language() 保存配置
            4. 发射 language_changed 信号通知主窗口
        """
        # 索引到语言代码的映射
        lang_map = {0: "en", 1: "zh"}
        lang_code = lang_map.get(index, "en")

        # 加载新语言
        translator.load_language(lang_code)

        # 保存配置
        config.set_language(lang_code)

        # 发射信号
        self.language_changed.emit(lang_code)

    def _on_theme_changed(self, index: int) -> None:
        """
        主题切换回调函数

        根据下拉框索引确定主题，更新应用程序主题和配置，
        并发射主题切换信号。

        Args:
            index: 下拉框当前索引
                   - 0: Light ("light")
                   - 1: Dark ("dark")
                   - 2: Follow System ("auto")

        处理流程：
            1. 根据索引确定主题名称
            2. 调用 setTheme() 更新应用程序主题
            3. 调用 config.set_theme() 保存配置
            4. 发射 theme_changed 信号通知主窗口
        """
        # 索引到主题的映射
        theme_map = {0: "light", 1: "dark", 2: "auto"}
        theme_name = theme_map.get(index, "auto")

        # 主题名称到 Theme 枚举的映射
        theme_enum_map = {
            "light": Theme.LIGHT,
            "dark": Theme.DARK,
            "auto": Theme.AUTO
        }

        # 设置应用程序主题
        theme_enum = theme_enum_map.get(theme_name, Theme.AUTO)
        setTheme(theme_enum)

        # 保存配置
        config.set_theme(theme_name)

        # 发射信号
        self.theme_changed.emit(theme_name)
