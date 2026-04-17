# -*- coding: utf-8 -*-
"""
搜索结果选择对话框模块

该模块提供音乐搜索结果的选择功能，支持展示歌曲列表、
预览详细信息、选择目标歌曲等操作。

@module song_search_dialog
@version 1.0.0
"""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import (
    Qt,
    QSize,
    Signal,
)
from PySide6.QtGui import QPixmap, QFont, QColor
from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QHeaderView,
    QLabel,
    QAbstractItemView,
)

from qfluentwidgets import (
    MessageBoxBase,
    SubtitleLabel,
    BodyLabel,
    PrimaryPushButton,
    PushButton,
    FluentIcon as FIF,
    CardWidget,
    SingleDirectionScrollArea,
)


class SongSearchResultDialog(MessageBoxBase):
    """
    搜索结果选择对话框

    展示音乐平台搜索结果，允许用户选择目标歌曲。
    支持双击或按钮确认选择。

    Attributes:
        song_selected (Signal): 歌曲选择信号，参数为 (song_id, song_info)

    Example:
        >>> dialog = SongSearchResultDialog(parent)
        >>> dialog.set_search_results(songs, keyword="周杰伦 晴天")
        >>> if dialog.exec():
        ...     song_id, info = dialog.selected_song
    """

    song_selected = Signal(dict)  # 选中的歌曲信息

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        初始化搜索结果对话框

        Args:
            parent (QWidget | None): 父窗口组件
        """
        super().__init__(parent)

        self._songs: list[dict[str, Any]] = []
        self._selected_song: Optional[dict[str, Any]] = None
        self._keyword: str = ""

        self.titleLabel = SubtitleLabel(tr("search_results"))
        self.keywordLabel = BodyLabel()
        self.resultCountLabel = BodyLabel()

        # 创建搜索结果表格
        self.song_table = self._create_table()

        # 创建按钮区域
        self.confirm_button = PrimaryPushButton(
            tr("select_song"), FIF.CHECKMARK, self
        )
        self.cancel_button = PushButton(tr("cancel"), FIF.CANCEL, self)

        # 构建布局
        self._setup_layout()

        # 连接信号
        self._connect_signals()

        # 设置最小宽度
        self.widget.setMinimumWidth(650)
        self.widget.setMinimumHeight(450)

    def _create_table(self) -> QTableWidget:
        """
        创建搜索结果表格

        Returns:
            QTableWidget: 配置完成的表格组件
        """
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            tr("song_name"),
            tr("artist"),
            tr("album"),
            tr("duration"),
            tr("id")
        ])

        # 设置表格属性
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)

        # 设置列宽模式
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(3, 70)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(4, 80)

        # 隐藏 ID 列（用于内部使用）
        table.setColumnHidden(4, True)

        # 设置行高
        table.verticalHeader().setDefaultSectionSize(40)

        return table

    def _setup_layout(self) -> None:
        """
        构建对话框布局
        """
        layout = QVBoxLayout(self.widget)
        layout.setSpacing(12)

        # 标题区域
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.addWidget(self.titleLabel)
        title_layout.addStretch()
        title_layout.addWidget(self.resultCountLabel)
        layout.addWidget(title_widget)

        # 搜索关键词标签
        self.keywordLabel.setObjectName("keywordLabel")
        self.keywordLabel.setStyleSheet("""
            BodyLabel#keywordLabel {
                color: #00bfa5;
                font-size: 13px;
                padding: 4px 0;
            }
        """)
        layout.addWidget(self.keywordLabel)

        # 表格区域（可滚动）
        scroll_area = SingleDirectionScrollArea()
        scroll_area.setWidget(self.song_table)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(scroll_area, stretch=1)

        # 按钮区域
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 8, 0, 0)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.confirm_button)
        button_layout.addStretch()
        layout.addWidget(button_widget)

    def _connect_signals(self) -> None:
        """
        连接信号和槽函数
        """
        self.confirm_button.clicked.connect(self._on_confirm)
        self.cancel_button.clicked.connect(self.reject)
        self.song_table.cellDoubleClicked.connect(self._on_double_click)

    def set_search_results(
        self,
        songs: list[dict[str, Any]],
        keyword: str = ""
    ) -> None:
        """
        设置搜索结果数据

        Args:
            songs (list[dict]): 搜索结果列表，每个字典包含：
                - id: 歌曲 ID
                - name: 歌曲名称
                - artist: 艺术家名称
                - album: 专辑名称
                - duration: 时长（秒）
            keyword (str): 搜索关键词
        """
        self._songs = songs
        self._keyword = keyword

        # 更新标签文本
        if keyword:
            self.keywordLabel.setText(f"🔍 {tr('search_keyword')}: {keyword}")
        self.resultCountLabel.setText(f"{len(songs)} {tr('results_found')}")

        # 填充表格
        self.song_table.setRowCount(len(songs))

        for row, song in enumerate(songs):
            # 歌曲名
            name_item = QTableWidgetItem(song.get('name', ''))
            name_item.setData(Qt.ItemDataRole.UserRole, song)
            self.song_table.setItem(row, 0, name_item)

            # 艺术家
            artist_item = QTableWidgetItem(song.get('artist', ''))
            self.song_table.setItem(row, 1, artist_item)

            # 专辑
            album_item = QTableWidgetItem(song.get('album', ''))
            self.song_table.setItem(row, 2, album_item)

            # 时长
            duration = song.get('duration', 0)
            duration_str = self._format_duration(duration)
            duration_item = QTableWidgetItem(duration_str)
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.song_table.setItem(row, 3, duration_item)

            # ID（隐藏）
            id_item = QTableWidgetItem(str(song.get('id', '')))
            self.song_table.setItem(row, 4, id_item)

        # 默认选中第一行
        if len(songs) > 0:
            self.song_table.selectRow(0)
            self._selected_song = songs[0]

    def _format_duration(self, seconds: int) -> str:
        """
        格式化时长显示

        Args:
            seconds (int): 时长（秒）

        Returns:
            str: 格式化的时长字符串 (mm:ss)
        """
        if not seconds or seconds <= 0:
            return "--:--"
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def _on_confirm(self) -> None:
        """
        确认按钮点击处理

        获取当前选中的歌曲并关闭对话框。
        """
        current_row = self.song_table.currentRow()
        if current_row < 0 or current_row >= len(self._songs):
            return

        self._selected_song = self._songs[current_row]
        self.accept()

    def _on_double_click(self, row: int, column: int) -> None:
        """
        双击单元格事件处理

        双击任意位置选中该行并确认。

        Args:
            row (int): 行索引
            column (int): 列索引
        """
        if 0 <= row < len(self._songs):
            self._selected_song = self._songs[row]
            self.accept()

    @property
    def selected_song(self) -> Optional[dict[str, Any]]:
        """
        获取选中的歌曲信息

        Returns:
            dict | None: 选中的歌曲字典，未选择返回 None
        """
        return self._selected_song

    @property
    def selected_song_id(self) -> Optional[int]:
        """
        获取选中歌曲的 ID

        Returns:
            int | None: 歌曲 ID，未选择返回 None
        """
        if self._selected_song:
            return self._selected_song.get('id')
        return None
