# -*- coding: utf-8 -*-
"""
auto_tag.gui.pages.settings_page 模块

提供应用程序设置页面，支持语言和主题切换。

功能：
    - 语言切换（English/中文）
    - 主题切换（Light/Dark/Follow System）

使用示例：
    from auto_tag.gui.pages.settings_page import SettingsPage

    page = SettingsPage()
"""

from PySide6.QtCore import QEvent, QObject, Signal, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    FluentIcon as FIF,
    SubtitleLabel,
    setTheme,
    Theme,
)

from auto_tag.gui.config import config
from auto_tag.gui.i18n import tr


class SettingsPage(QWidget):
    """
    设置页面

    提供应用程序设置界面，包括语言和主题选项。
    当用户更改设置时，通过信号通知主窗口。

    Attributes:
        language_changed (Signal(str)): 语言切换信号
        theme_changed (Signal(str)): 主题切换信号
        language_combo (ComboBox): 语言选择下拉框
        theme_combo (ComboBox): 主题选择下拉框

    Example:
        >>> settings = SettingsPage(parent=window)
        >>> settings.language_changed.connect(on_language_change)
        >>> settings.theme_changed.connect(on_theme_change)
    """

    # 定义信号：语言切换、主题切换
    language_changed = Signal(str)
    theme_changed = Signal(str)

    def __init__(self, parent=None) -> None:
        """
        初始化设置页面

        创建设置界面 UI 组件，从配置文件加载当前设置，
        并连接信号槽以响应用户操作。
        Args:
            parent (QWidget | None): 父窗口组件
        """
        super().__init__(parent)

        # 初始化 UI
        self._setup_ui()

        # 连接信号槽
        self._connect_signals()

        # 从配置加载初始设置
        self._load_initial_settings()

    def _setup_ui(self) -> None:
        """
        构建设置页面 UI 布局

        使用垂直布局组织所有设置项，包括：
        - 页面标题
        - 语言选择区域
        - 主题选择区域
        """
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        # 页面标题
        title = SubtitleLabel(tr("settings"))
        layout.addWidget(title)

        # 语言设置区域
        self.language_label = BodyLabel(tr("language"))
        layout.addWidget(self.language_label)

        self.language_combo = ComboBox()
        self.language_combo.addItems([tr("english"), tr("chinese")])
        self.language_combo.setFixedHeight(36)
        self.language_combo.installEventFilter(self)
        layout.addWidget(self.language_combo)

        # 主题设置区域
        self.theme_label = BodyLabel(tr("theme"))
        layout.addWidget(self.theme_label)

        self.theme_combo = ComboBox()
        self.theme_combo.addItems([
            tr("theme_light"),
            tr("theme_dark"),
            tr("theme_auto")
        ])
        self.theme_combo.setFixedHeight(36)
        self.theme_combo.installEventFilter(self)
        layout.addWidget(self.theme_combo)

        # 弹性空间
        layout.addStretch()

    def _connect_signals(self) -> None:
        """
        连接信号槽

        将语言和主题下拉框的索引变化信号连接到对应的处理方法。
        """
        self.language_combo.currentIndexChanged.connect(
            self._on_language_changed
        )
        self.theme_combo.currentIndexChanged.connect(
            self._on_theme_changed
        )

    def _load_initial_settings(self) -> None:
        """
        从配置文件加载初始设置

        根据配置文件中保存的语言和主题偏好，
        设置下拉框的当前选中项。
        """
        # 加载语言设置
        lang_index_map = {"en": 0, "zh": 1}
        current_lang_index = lang_index_map.get(config.language, 1)
        self.language_combo.setCurrentIndex(current_lang_index)

        # 加载主题设置
        theme_index_map = {"light": 0, "dark": 1, "auto": 2}
        current_theme_index = theme_index_map.get(config.theme, 2)
        self.theme_combo.setCurrentIndex(current_theme_index)

    def _on_language_changed(self, index: int) -> None:
        """
        语言切换回调处理方法

        根据用户选择的下拉框索引确定目标语言代码，
        更新翻译器并保存到配置文件，最后发射语言切换信号。

        Args:
            index (int): 下拉框选中项的索引
                - 0: English (en)
                - 1: 中文 (zh)
        """
        # 根据索引映射语言代码
        lang_code_map = {0: "en", 1: "zh"}
        lang_code = lang_code_map.get(index, "zh")

        # 更新翻译器语言
        from auto_tag.gui.i18n import translator
        translator.load_language(lang_code)

        # 保存到配置文件
        config.set_language(lang_code)

        # 发射信号通知主窗口
        self.language_changed.emit(lang_code)

        # 刷新当前页面文本
        self.refresh_texts()

    def _on_theme_changed(self, index: int) -> None:
        """
        主题切换回调处理方法

        根据用户选择的下拉框索引确定目标主题名称，
        应用新主题并保存到配置文件，最后发射主题切换信号。

        Args:
            index (int): 下拉框选中项的索引
                - 0: Light (浅色)
                - 1: Dark (深色)
                - 2: Follow System (跟随系统)
        """
        # 根据索引映射主题名称
        theme_name_map = {0: "light", 1: "dark", 2: "auto"}
        theme_name = theme_name_map.get(index, "auto")

        # 映射到 QFluentWidgets 的 Theme 枚举
        theme_enum_map = {
            "light": Theme.LIGHT,
            "dark": Theme.DARK,
            "auto": Theme.AUTO
        }
        theme_enum = theme_enum_map.get(theme_name, Theme.AUTO)

        # 应用主题
        setTheme(theme_enum)

        # 保存到配置文件
        config.set_theme(theme_name)

        # 发射信号
        self.theme_changed.emit(theme_name)

    def refresh_texts(self) -> None:
        """
        刷新页面文本

        当语言切换时调用此方法，更新所有 UI 文本为当前语言的翻译。
        需要重新设置标签和下拉框选项的文本内容。
        """
        # 保存当前选中状态
        lang_idx = self.language_combo.currentIndex()
        theme_idx = self.theme_combo.currentIndex()

        # 更新标签文本
        self.language_label.setText(tr("language"))
        self.theme_label.setText(tr("theme"))

        # 更新标题
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            widget = item.widget()
            if isinstance(widget, SubtitleLabel):
                widget.setText(tr("settings"))
                break

        # 清空并重新填充下拉框选项
        self.language_combo.blockSignals(True)
        self.theme_combo.blockSignals(True)

        self.language_combo.clear()
        self.language_combo.addItems([tr("english"), tr("chinese")])
        self.language_combo.setCurrentIndex(lang_idx)

        self.theme_combo.clear()
        self.theme_combo.addItems([
            tr("theme_light"),
            tr("theme_dark"),
            tr("theme_auto")
        ])
        self.theme_combo.setCurrentIndex(theme_idx)

        self.language_combo.blockSignals(False)
        self.theme_combo.blockSignals(False)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        事件过滤器

        监听 ComboBox 的 Show 事件，在弹出下拉框时修复透明边框问题。
        通过设置弹出窗口为无边框、无阴影来消除额外的边框效果。

        Args:
            obj (QObject): 事件源对象
            event (QEvent): 事件对象

        Returns:
            bool: 是否拦截事件
        """
        if event.type() == QEvent.Type.Show and obj in (
            self.language_combo,
            self.theme_combo
        ):
            try:
                popup = obj.view().window()
                if popup and popup != obj:
                    flags = Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
                    popup.setWindowFlags(flags)
                    popup.setAttribute(
                        Qt.WidgetAttribute.WA_TranslucentBackground,
                        True
                    )
            except Exception:
                pass

        return super().eventFilter(obj, event)
