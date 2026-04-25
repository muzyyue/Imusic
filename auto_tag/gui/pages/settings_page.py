# -*- coding: utf-8 -*-
"""
设置页面模块

该模块提供应用程序的设置界面，包括语言、主题、**搜索源配置**等选项。
使用 QFluentWidgets 库实现现代化的 Fluent Design 风格界面。

功能：
    - 语言切换
    - 主题切换（浅色/深色/跟随系统）
    - **搜索源选择与配置**
    - 设置持久化存储

依赖：
    - PySide6: GUI 框架
    - qfluentwidgets: Fluent Design 风格组件库
    - auto_tag.gui.config: 配置管理
    - auto_tag.gui.i18n: 国际化支持

Example:
    >>> from auto_tag.gui.pages.settings_page import SettingsPage
    >>> page = SettingsPage()
    >>> page.show()
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt, Signal, QEvent, QObject
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)

from qfluentwidgets import (
    ComboBox,
    BodyLabel,
    SubtitleLabel,
    SwitchButton,
    setTheme,
    Theme,
    isDarkTheme,
    CheckBox,
)

from auto_tag.gui.config import config, AppConfig
from auto_tag.gui.i18n import tr


logger = logging.getLogger(__name__)


class SettingsPage(QWidget):
    """
    设置页面类

    提供应用程序设置界面，支持语言、主题和**搜索源**切换。

    Signals:
        language_changed (str): 语言变更信号，参数为语言代码
        theme_changed (str): 主题变更信号，参数为主题名称
        search_config_changed: 搜索配置变更信号（无参数）

    Example:
        >>> page = SettingsPage()
        >>> page.language_changed.connect(lambda lang: print(f"Language changed to {lang}"))
        >>> page.search_config_changed.connect(on_search_settings_updated)
    """

    # 定义信号
    language_changed = Signal(str)
    theme_changed = Signal(str)
    search_config_changed = Signal()  # 新增：搜索配置变更信号

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        初始化设置页面

        Args:
            parent: 父窗口，默认为 None
        """
        super().__init__(parent)

        # 创建主布局
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(40, 30, 40, 30)
        self._layout.setSpacing(20)

        # 页面标题
        self._title_label = SubtitleLabel(tr("settings_page.title"))
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self._title_label.setFont(font)
        self._layout.addWidget(self._title_label)

        # 常规设置分组标题
        general_section = SubtitleLabel(tr("settings_page.general_section"))
        font_general = QFont()
        font_general.setPointSize(14)
        general_section.setFont(font_general)
        self._layout.addWidget(general_section)

        # 语言设置
        language_layout = QHBoxLayout()
        self._language_label = BodyLabel(tr("settings_page.language_label"))
        self._language_combo = ComboBox()
        self._language_combo.addItems([tr("settings_page.languages.zh"), tr("settings_page.languages.en")])
        self._language_combo.setMinimumWidth(200)
        
        # 设置当前语言
        current_lang_index = 0 if config.language == "zh" else 1
        self._language_combo.setCurrentIndex(current_lang_index)
        
        # 连接信号
        self._language_combo.currentIndexChanged.connect(self._on_language_changed)
        
        language_layout.addWidget(self._language_label)
        language_layout.addStretch()
        language_layout.addWidget(self._language_combo)
        self._layout.addLayout(language_layout)

        # 主题设置
        theme_layout = QHBoxLayout()
        self._theme_label = BodyLabel(tr("settings_page.theme_label"))
        self._theme_combo = ComboBox()
        self._theme_combo.addItems([
            tr("settings_page.themes.light"),
            tr("settings_page.themes.dark"),
            tr("settings_page.themes.auto")
        ])
        self._theme_combo.setMinimumWidth(200)
        
        # 设置当前主题
        current_theme_index = {"light": 0, "dark": 1, "auto": 2}.get(config.theme, 2)
        self._theme_combo.setCurrentIndex(current_theme_index)
        
        # 连接信号
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        
        theme_layout.addWidget(self._theme_label)
        theme_layout.addStretch()
        theme_layout.addWidget(self._theme_combo)
        self._layout.addLayout(theme_layout)

        # ===== 新增：搜索设置分组 =====
        search_section = SubtitleLabel(tr("settings_page.search_settings_section"))
        search_section.setFont(font_general)
        self._layout.addWidget(search_section)

        # 搜索源多选 - 左右行布局（标签左，控件右），与"语言"/"主题"完全一致
        sources_row = QHBoxLayout()
        self._sources_label = BodyLabel(tr("settings_page.search_source_label"))
        sources_row.addWidget(self._sources_label)
        sources_row.addSpacing(40)

        # 右侧垂直排列 CheckBox
        cb_container = QVBoxLayout()
        cb_container.setSpacing(4)
        cb_container.setContentsMargins(0, 0, 0, 0)
        self._source_checkboxes: dict[str, CheckBox] = {}
        source_order = ["shazam", "netease", "kugou"]
        for source_key in source_order:
            cb = CheckBox(tr(f"settings_page.sources.{source_key}"))
            self._source_checkboxes[source_key] = cb
            cb.stateChanged.connect(self._on_search_sources_changed)
            cb_container.addWidget(cb)

        # 设置当前选中状态
        current_sources = config.search_sources
        for source_key, cb in self._source_checkboxes.items():
            cb.setChecked(source_key in current_sources)
        self._ensure_at_least_one_source_checked()

        sources_row.addLayout(cb_container)
        sources_row.addStretch()
        self._layout.addLayout(sources_row)

        logger.debug("Settings page initialized with search source configuration")

    def _on_language_changed(self, index: int) -> None:
        """
        语言切换回调

        Args:
            index: 下拉框选中索引 (0=中文, 1=英文)
        """
        lang_code_map = {0: "zh", 1: "en"}
        lang_code = lang_code_map.get(index, "zh")

        from auto_tag.gui.i18n import translator
        translator.load_language(lang_code)

        config.set_language(lang_code)
        logger.info(f"Language changed to: {lang_code}")

        self.language_changed.emit(lang_code)
        self.refresh_texts()

    def _on_theme_changed(self, index: int) -> None:
        """
        主题切换回调

        Args:
            index: 下拉框选中索引 (0=浅色, 1=深色, 2=跟随系统)
        """
        theme_name_map = {0: "light", 1: "dark", 2: "auto"}
        theme_name = theme_name_map.get(index, "auto")

        theme_enum_map = {
            "light": Theme.LIGHT,
            "dark": Theme.DARK,
            "auto": Theme.AUTO
        }
        theme_enum = theme_enum_map.get(theme_name, Theme.AUTO)

        setTheme(theme_enum)
        config.set_theme(theme_name)
        
        logger.info(f"Theme changed to: {theme_name}")
        self.theme_changed.emit(theme_name)

    def _on_search_sources_changed(self) -> None:
        """
        搜索源多选变更回调
        
        当用户勾选/取消勾选搜索源时：
        1. 收集所有选中的源
        2. 确保至少有一个源被选中
        3. 更新配置
        4. 记录日志
        """
        selected = [
            key for key, cb in self._source_checkboxes.items()
            if cb.isChecked()
        ]
        
        if not selected:
            self._ensure_at_least_one_source_checked()
            return
        
        try:
            config.set_search_sources(selected)
            logger.info(f"Search sources changed to: {selected}")
            self.search_config_changed.emit()
        except Exception as e:
            logger.error(f"Failed to change search sources: {e}")
    
    def _ensure_at_least_one_source_checked(self) -> None:
        """
        确保至少有一个搜索源被选中
        
        如果所有 CheckBox 都未选中，默认勾选 Shazam
        """
        has_checked = any(cb.isChecked() for cb in self._source_checkboxes.values())
        if not has_checked:
            self._source_checkboxes["shazam"].setChecked(True)
            logger.info("Ensured at least one source (shazam) is checked")
    
    def _on_language_changed(self, index: int) -> None:
        """
        语言切换回调

        Args:
            index: 下拉框选中索引 (0=中文, 1=英文)
        """
        lang_code_map = {0: "zh", 1: "en"}
        lang_code = lang_code_map.get(index, "zh")

        from auto_tag.gui.i18n import translator
        translator.load_language(lang_code)

        config.set_language(lang_code)
        logger.info(f"Language changed to: {lang_code}")

        self.language_changed.emit(lang_code)
        self.refresh_texts()

    def refresh_texts(self) -> None:
        """
        刷新页面文本

        当语言切换时调用此方法，更新所有 UI 文本为当前语言的翻译。
        """
        # 保存当前选中状态
        lang_idx = self._language_combo.currentIndex()
        theme_idx = self._theme_combo.currentIndex()
        current_sources = config.search_sources

        # 阻止信号触发
        self._language_combo.blockSignals(True)
        self._theme_combo.blockSignals(True)
        for cb in self._source_checkboxes.values():
            cb.blockSignals(True)

        # 更新标题和分组标题
        self._title_label.setText(tr("settings_page.title"))

        # 更新常规设置标签
        self._language_label.setText(tr("settings_page.language_label"))
        self._theme_label.setText(tr("settings_page.theme_label"))
        
        # 更新搜索设置标签
        self._sources_label.setText(tr("settings_page.search_source_label"))

        # 清空并重新填充语言下拉框
        self._language_combo.clear()
        self._language_combo.addItems([tr("settings_page.languages.zh"), tr("settings_page.languages.en")])
        self._language_combo.setCurrentIndex(lang_idx)

        # 清空并重新填充主题下拉框
        self._theme_combo.clear()
        self._theme_combo.addItems([
            tr("settings_page.themes.light"),
            tr("settings_page.themes.dark"),
            tr("settings_page.themes.auto")
        ])
        self._theme_combo.setCurrentIndex(theme_idx)
        
        # 更新搜索源 CheckBox 文本并恢复选中状态
        source_order = ["shazam", "netease", "kugou"]
        for source_key in source_order:
            cb = self._source_checkboxes[source_key]
            cb.setText(tr(f"settings_page.sources.{source_key}"))
            cb.setChecked(source_key in current_sources)

        # 恢复信号连接
        self._language_combo.blockSignals(False)
        self._theme_combo.blockSignals(False)
        for cb in self._source_checkboxes.values():
            cb.blockSignals(False)

        self._ensure_at_least_one_source_checked()

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
            self._language_combo,
            self._theme_combo,
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
