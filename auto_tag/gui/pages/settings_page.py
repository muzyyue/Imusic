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
    - PyQt6: GUI 框架
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

from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QObject
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
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
)

from auto_tag.gui.config import config, AppConfig
from auto_tag.gui.i18n import t


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
    language_changed = pyqtSignal(str)
    theme_changed = pyqtSignal(str)
    search_config_changed = pyqtSignal()  # 新增：搜索配置变更信号

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
        self._title_label = SubtitleLabel(t("settings_page.title"))
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self._title_label.setFont(font)
        self._layout.addWidget(self._title_label)

        # 常规设置分组标题
        general_section = SubtitleLabel(t("settings_page.general_section"))
        font_general = QFont()
        font_general.setPointSize(14)
        general_section.setFont(font_general)
        self._layout.addWidget(general_section)

        # 语言设置
        language_layout = QHBoxLayout()
        self._language_label = BodyLabel(t("settings_page.language_label"))
        self._language_combo = ComboBox()
        self._language_combo.addItems([t("settings_page.languages.zh"), t("settings_page.languages.en")])
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
        self._theme_label = BodyLabel(t("settings_page.theme_label"))
        self._theme_combo = ComboBox()
        self._theme_combo.addItems([
            t("settings_page.themes.light"),
            t("settings_page.themes.dark"),
            t("settings_page.themes.auto")
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
        search_section = SubtitleLabel(t("settings_page.search_settings_section"))
        search_section.setFont(font_general)
        self._layout.addWidget(search_section)

        # 搜索源选择
        source_layout = QHBoxLayout()
        self._source_label = BodyLabel(t("settings_page.search_source_label"))
        self._source_combo = ComboBox()
        self._source_combo.addItems([
            t("settings_page.sources.shazam"),
            t("settings_page.sources.netease"),
            t("settings_page.sources.kugou")
        ])
        self._source_combo.setMinimumWidth(200)
        
        # 设置当前搜索源
        source_map = {
            "shazam": 0,
            "netease": 1,
            "kugou": 2
        }
        current_source_index = source_map.get(config.search_source, 0)
        self._source_combo.setCurrentIndex(current_source_index)
        
        # 连接信号（切换源时更新UI状态）
        self._source_combo.currentIndexChanged.connect(self._on_search_source_changed)
        
        source_layout.addWidget(self._source_label)
        source_layout.addStretch()
        source_layout.addWidget(self._source_combo)
        self._layout.addLayout(source_layout)

        # 网易云搜索类型（条件显示）
        netease_type_layout = QHBoxLayout()
        self._netease_type_label = BodyLabel(t("settings_page.netease_type_label"))
        self._netease_type_combo = ComboBox()
        self._netease_type_combo.setMinimumWidth(300)
        
        # 添加网易云支持的搜索类型选项
        for type_value, type_name in AppConfig.NETEASE_SEARCH_TYPES.items():
            self._netease_type_combo.addItem(type_name, userData=type_value)
        
        # 设置当前类型
        current_type_index = list(AppConfig.NETEASE_SEARCH_TYPES.keys()).index(
            config.netease_search_type
        ) if config.netease_search_type in AppConfig.NETEASE_SEARCH_TYPES else 0
        self._netease_type_combo.setCurrentIndex(current_type_index)
        
        # 连接信号
        self._netease_type_combo.currentIndexChanged.connect(self._on_netease_type_changed)
        
        netease_type_layout.addWidget(self._netease_type_label)
        netease_type_layout.addStretch()
        netease_type_layout.addWidget(self._netease_type_combo)
        self._layout.addLayout(netease_type_layout)

        # 包含电台开关（条件显示）
        radio_layout = QHBoxLayout()
        self._radio_label = BodyLabel(t("settings_page.include_radio_label"))
        self._radio_switch = SwitchButton()
        self._radio_switch.setChecked(config.include_radio)
        
        # 连接信号
        self._radio_switch.checkedChanged.connect(self._on_radio_toggled)
        
        radio_layout.addWidget(self._radio_label)
        radio_layout.addStretch()
        radio_layout.addWidget(self._radio_switch)
        self._layout.addLayout(radio_layout)

        # 弹性空间，将内容推到顶部
        self._layout.addStretch()

        # 根据初始搜索源状态更新UI可见性
        self._update_netease_options_visibility(config.search_source == "netease")

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

    def _on_search_source_changed(self, index: int) -> None:
        """
        搜索源变更回调
        
        当用户切换主搜索源时：
        1. 更新配置
        2. 动态显示/隐藏网易云专用选项
        3. 记录日志
        """
        source_map = {0: "shazam", 1: "netease", 2: "kugou"}
        new_source = source_map.get(index, "shazam")
        
        try:
            config.set_search_source(new_source)
            logger.info(f"Search source changed to: {new_source}")
            
            # 更新网易云选项的可见性
            is_netease = (new_source == "netease")
            self._update_netease_options_visibility(is_netease)
            
            # 发射信号通知其他组件
            self.search_config_changed.emit()
            
        except Exception as e:
            logger.error(f"Failed to change search source: {e}")
    
    def _on_netease_type_changed(self, index: int) -> None:
        """
        网易云搜索类型变更回调
        
        Args:
            index: 下拉框当前选中索引
        """
        type_value = self._netease_type_combo.itemData(index)
        
        if type_value is not None and isinstance(type_value, int):
            try:
                config.set_netease_search_type(type_value)
                logger.info(f"NetEase search type changed to: {type_value} ({AppConfig.NETEASE_SEARCH_TYPES.get(type_value)})")
                
                # 发射信号
                self.search_config_changed.emit()
                
            except Exception as e:
                logger.error(f"Failed to change NetEase search type: {e}")
    
    def _on_radio_toggled(self, checked: bool) -> None:
        """
        电台开关状态变更回调
        
        Args:
            checked: 开关是否开启
        """
        try:
            config.set_include_radio(checked)
            logger.info(f"Include radio toggle changed to: {checked}")
            
            # 发射信号
            self.search_config_changed.emit()
            
        except Exception as e:
            logger.error(f"Failed to change radio toggle: {e}")
    
    def _update_netease_options_visibility(self, visible: bool) -> None:
        """
        更新网易云专用选项的可见性
        
        当主搜索源为网易云音乐时显示，否则隐藏。
        
        Args:
            visible: 是否可见
        """
        # 搜索类型选择器及其标签
        self._netease_type_label.setVisible(visible)
        self._netease_type_combo.setVisible(visible)
        
        # 电台开关及其标签
        self._radio_label.setVisible(visible)
        self._radio_switch.setVisible(visible)
        
        logger.debug(f"NetEase options visibility updated: {'visible' if visible else 'hidden'}")

    def refresh_texts(self) -> None:
        """
        刷新页面文本

        当语言切换时调用此方法，更新所有 UI 文本为当前语言的翻译。
        需要重新设置标签和下拉框选项的文本内容，包括搜索源相关组件。
        """
        # 保存当前选中状态
        lang_idx = self._language_combo.currentIndex()
        theme_idx = self._theme_combo.currentIndex()
        source_idx = self._source_combo.currentIndex()
        netease_type_idx = self._netease_type_combo.currentIndex()
        radio_checked = self._radio_switch.isChecked()

        # 更新标题和分组标题
        self._title_label.setText(t("settings_page.title"))

        # 更新常规设置标签
        self._language_label.setText(t("settings_page.language_label"))
        self._theme_label.setText(t("settings_page.theme_label"))
        
        # 更新搜索设置标签
        self._source_label.setText(t("settings_page.search_source_label"))
        self._netease_type_label.setText(t("settings_page.netease_type_label"))
        self._radio_label.setText(t("settings_page.include_radio_label"))

        # 阻止信号触发
        self._language_combo.blockSignals(True)
        self._theme_combo.blockSignals(True)
        self._source_combo.blockSignals(True)
        self._netease_type_combo.blockSignals(True)
        self._radio_switch.blockSignals(True)

        # 清空并重新填充语言下拉框
        self._language_combo.clear()
        self._language_combo.addItems([t("settings_page.languages.zh"), t("settings_page.languages.en")])
        self._language_combo.setCurrentIndex(lang_idx)

        # 清空并重新填充主题下拉框
        self._theme_combo.clear()
        self._theme_combo.addItems([
            t("settings_page.themes.light"),
            t("settings_page.themes.dark"),
            t("settings_page.themes.auto")
        ])
        self._theme_combo.setCurrentIndex(theme_idx)
        
        # 清空并重新填充搜索源下拉框
        self._source_combo.clear()
        self._source_combo.addItems([
            t("settings_page.sources.shazam"),
            t("settings_page.sources.netease"),
            t("settings_page.sources.kugou")
        ])
        self._source_combo.setCurrentIndex(source_idx)
        
        # 清空并重新填充网易云搜索类型下拉框
        self._netease_type_combo.clear()
        for type_value, type_name in AppConfig.NETEASE_SEARCH_TYPES.items():
            self._netease_type_combo.addItem(type_name, userData=type_value)
        self._netease_type_combo.setCurrentIndex(netease_type_idx)
        
        # 恢复电台开关状态
        self._radio_switch.setChecked(radio_checked)

        # 恢复信号连接
        self._language_combo.blockSignals(False)
        self._theme_combo.blockSignals(False)
        self._source_combo.blockSignals(False)
        self._netease_type_combo.blockSignals(False)
        self._radio_switch.blockSignals(False)

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
            self._source_combo,
            self._netease_type_combo
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
