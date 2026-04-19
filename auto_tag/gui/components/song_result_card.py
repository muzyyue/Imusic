# -*- coding: utf-8 -*-
"""
搜索结果卡片组件模块

该模块提供卡片式的搜索结果展示组件，支持折叠/展开交互、
悬停效果和平台结果选择功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QSpacerItem,
    QSizePolicy,
)
from qfluentwidgets import (
    CardWidget,
    BodyLabel,
    SubtitleLabel,
    PushButton,
    CheckBox,
    IconWidget,
    FluentIcon as FIF,
)

if TYPE_CHECKING:
    pass


class PlatformResultWidget(QFrame):
    """
    平台搜索结果展示组件

    显示单个平台的搜索结果信息，支持选中状态切换。

    Attributes:
        platform (str): 平台标识
        result_data (dict): 搜索结果数据
        is_selected (bool): 是否被选中
    """

    def __init__(
        self,
        platform: str,
        result_data: dict,
        parent=None
    ) -> None:
        """
        初始化平台结果组件

        Args:
            platform (str): 平台标识（shazam/netease/kugou）
            result_data (dict): 搜索结果数据
            parent (QWidget | None): 父组件
        """
        super().__init__(parent)
        self.platform = platform
        self.result_data = result_data
        self.is_selected = False

        self._setup_ui()
        self._setup_style()

    def _setup_ui(self) -> None:
        """构建 UI 布局"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # 平台图标和名称
        icon_layout = QHBoxLayout()
        icon_layout.setSpacing(8)

        platform_icon = IconWidget()
        platform_icon.setFixedSize(24, 24)

        # 根据平台设置不同图标
        if self.platform == "shazam":
            platform_icon.setIcon(FIF.MUSIC)
        elif self.platform == "netease":
            platform_icon.setIcon(FIF.CLOUD)
        elif self.platform == "kugou":
            platform_icon.setIcon(FIF.MUSIC_NOTE)
        else:
            platform_icon.setIcon(FIF.MUSIC)

        icon_layout.addWidget(platform_icon)

        platform_name = BodyLabel(self._get_platform_display_name())
        platform_name.setStyleSheet(
            "color: #7c4dff; font-weight: 500; min-width: 70px;"
        )
        icon_layout.addWidget(platform_name)
        icon_layout.addStretch()

        layout.addLayout(icon_layout, 0)

        # 歌曲信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # 标题
        title = self.result_data.get("title", "Unknown")
        title_label = BodyLabel(title)
        title_label.setStyleSheet("font-weight: 500;")
        title_label.setWordWrap(True)
        info_layout.addWidget(title_label)

        # 艺术家和专辑
        artist = self.result_data.get("artist", "Unknown")
        album = self.result_data.get("album", "Unknown Album")
        meta_label = BodyLabel(f"{artist} · {album}")
        meta_label.setStyleSheet("color: #888888; font-size: 12px;")
        info_layout.addWidget(meta_label)

        layout.addLayout(info_layout, 1)

        # 时长
        duration_layout = QHBoxLayout()
        duration_layout.setSpacing(4)

        duration_icon = IconWidget(FIF.CLOCK)
        duration_icon.setFixedSize(16, 16)
        duration_layout.addWidget(duration_icon)

        duration_text = self._format_duration(
            self.result_data.get("duration", 0)
        )
        duration_label = BodyLabel(duration_text)
        duration_label.setStyleSheet("color: #888888; font-size: 12px;")
        duration_layout.addWidget(duration_label)

        layout.addLayout(duration_layout, 0)

    def _setup_style(self) -> None:
        """设置样式"""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setProperty("class", "PlatformResultWidget")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        self.setMinimumHeight(60)
        self._update_style()

    def _update_style(self) -> None:
        """根据选中状态更新样式"""
        if self.is_selected:
            self.setStyleSheet("""
                QFrame[class="PlatformResultWidget"] {
                    background-color: rgba(124, 77, 255, 0.1);
                    border: 2px solid #7c4dff;
                    border-radius: 8px;
                }
                QFrame[class="PlatformResultWidget"]:hover {
                    background-color: rgba(124, 77, 255, 0.15);
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame[class="PlatformResultWidget"] {
                    background-color: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 8px;
                }
                QFrame[class="PlatformResultWidget"]:hover {
                    background-color: rgba(255, 255, 255, 0.06);
                    border-color: rgba(255, 255, 255, 0.15);
                }
            """)

    def _get_platform_display_name(self) -> str:
        """获取平台显示名称"""
        from auto_tag.gui.i18n import tr

        platform_names = {
            "shazam": "source_shazam",
            "netease": "source_netease",
            "kugou": "source_kugou",
        }
        key = platform_names.get(self.platform, self.platform)
        return tr(key)

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        from auto_tag.gui.i18n import tr

        if not seconds:
            return "--"
        minutes = seconds // 60
        secs = seconds % 60
        if minutes > 0:
            return tr("minutes_seconds_format", minutes=minutes, seconds=secs)
        return tr("seconds_format", seconds=secs)

    def mousePressEvent(self, event) -> None:
        """鼠标点击事件处理"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected(True)

    def set_selected(self, selected: bool) -> None:
        """
        设置选中状态

        Args:
            selected (bool): 是否选中
        """
        self.is_selected = selected
        self._update_style()

    def get_result_data(self) -> dict:
        """获取结果数据"""
        return self.result_data


class SongResultCard(CardWidget):
    """
    歌曲搜索结果卡片组件

    显示单首歌曲的所有平台搜索结果，支持折叠/展开交互。

    Attributes:
        file_path (str): 原始文件路径
        is_expanded (bool): 是否展开
        selected_platform_index (int): 选中的平台结果索引
        on_selection_changed (callable): 选中状态变化回调
    """

    def __init__(
        self,
        file_path: str,
        display_name: str,
        search_results: list[dict],
        default_result: dict | None = None,
        has_error: bool = False,
        parent=None
    ) -> None:
        """
        初始化歌曲结果卡片

        Args:
            file_path (str): 原始文件路径
            display_name (str): 显示的文件名
            search_results (list[dict]): 平台搜索结果列表
            default_result (dict | None): 默认识别结果
            has_error (bool): 是否有错误
            parent (QWidget | None): 父组件
        """
        super().__init__(parent)
        self.file_path = file_path
        self.display_name = display_name
        self.search_results = search_results
        self.default_result = default_result
        self.has_error = has_error
        self.is_expanded = True
        self.selected_platform_index = 0
        self.on_selection_changed = None

        self._setup_ui()
        self._setup_style()

        # 如果有搜索结果，默认选中第一个
        if search_results:
            self._select_platform(0)

    def _setup_ui(self) -> None:
        """构建 UI 布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 卡片头部 ===
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)

        # 勾选框
        self.checkbox = CheckBox()
        self.checkbox.setChecked(not self.has_error)
        header_layout.addWidget(self.checkbox)

        # 文件名
        file_label = SubtitleLabel(self.display_name)
        file_label.setWordWrap(True)
        file_label.setStyleSheet(
            "font-size: 14px; font-weight: 500;"
        )
        header_layout.addWidget(file_label, 1)

        # 结果数量标签
        if self.search_results:
            count_label = BodyLabel(f"{len(self.search_results)} 个结果")
            count_label.setStyleSheet(
                "color: #7c4dff; font-size: 12px; padding: 4px 8px; "
                "background: rgba(124, 77, 255, 0.1); border-radius: 12px;"
            )
            header_layout.addWidget(count_label)

        # 展开/收起按钮
        self.expand_btn = PushButton()
        self.expand_btn.setFixedSize(32, 32)
        self.expand_btn.clicked.connect(self._toggle_expand)
        header_layout.addWidget(self.expand_btn)

        self._update_expand_icon()

        main_layout.addLayout(header_layout)

        # === 搜索结果列表区域 ===
        self.results_container = QFrame()
        self.results_container.setObjectName("resultsContainer")

        results_layout = QVBoxLayout(self.results_container)
        results_layout.setContentsMargins(16, 0, 16, 12)
        results_layout.setSpacing(8)

        # 添加平台结果
        if self.search_results:
            for idx, result in enumerate(self.search_results):
                platform = result.get("source", "shazam")
                platform_widget = PlatformResultWidget(platform, result)
                platform_widget.setObjectName(f"platformResult_{idx}")
                results_layout.addWidget(platform_widget)
        else:
            # 没有搜索结果，显示默认结果
            no_result_label = BodyLabel("未找到匹配的搜索结果")
            no_result_label.setStyleSheet("color: #888888; padding: 8px 0;")
            results_layout.addWidget(no_result_label)

        main_layout.addWidget(self.results_container)

        # 设置滚动区域（当结果过多时）
        self.results_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum
        )

    def _setup_style(self) -> None:
        """设置样式"""
        self.setProperty("class", "SongResultCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_style()

    def _update_style(self) -> None:
        """更新卡片样式"""
        if self.has_error:
            self.setStyleSheet("""
                CardWidget[class="SongResultCard"] {
                    background-color: rgba(255, 82, 82, 0.05);
                    border: 1px solid rgba(255, 82, 82, 0.2);
                    border-radius: 12px;
                }
                CardWidget[class="SongResultCard"]:hover {
                    background-color: rgba(255, 82, 82, 0.08);
                    border-color: rgba(255, 82, 82, 0.3);
                }
            """)
        else:
            self.setStyleSheet("""
                CardWidget[class="SongResultCard"] {
                    background-color: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 12px;
                }
                CardWidget[class="SongResultCard"]:hover {
                    background-color: rgba(255, 255, 255, 0.06);
                    border-color: rgba(255, 255, 255, 0.15);
                }
            """)

    def _toggle_expand(self) -> None:
        """切换展开/收起状态"""
        self.is_expanded = not self.is_expanded
        self._update_expand_icon()
        self.results_container.setVisible(self.is_expanded)

    def _update_expand_icon(self) -> None:
        """更新展开/收起按钮图标"""
        if self.is_expanded:
            self.expand_btn.setIcon(FIF.UP)
        else:
            self.expand_btn.setIcon(FIF.DOWN)

    def _select_platform(self, index: int) -> None:
        """
        选中指定平台结果

        Args:
            index (int): 平台结果索引
        """
        self.selected_platform_index = index

        # 更新所有平台组件的选中状态
        for i in range(self.results_container.layout().count()):
            widget = self.results_container.layout().itemAt(i).widget()
            if isinstance(widget, PlatformResultWidget):
                if i == index:
                    widget.set_selected(True)
                else:
                    widget.set_selected(False)

        # 通知选中状态变化
        if self.on_selection_changed:
            self.on_selection_changed(self.file_path, index)

    def get_selected_result(self) -> dict:
        """
        获取选中的搜索结果

        Returns:
            dict: 选中的搜索结果数据
        """
        if self.search_results and 0 <= self.selected_platform_index < len(
            self.search_results
        ):
            return self.search_results[self.selected_platform_index]
        elif self.default_result:
            return self.default_result
        return {}

    def is_checked(self) -> bool:
        """获取勾选状态"""
        return self.checkbox.isChecked()

    def set_on_selection_changed(self, callback) -> None:
        """
        设置选中状态变化回调

        Args:
            callback (callable): 回调函数 (file_path, index)
        """
        self.on_selection_changed = callback
