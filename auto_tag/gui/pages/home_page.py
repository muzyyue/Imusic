# -*- coding: utf-8 -*-
"""
音频识别主页面模块

该模块提供音频识别功能的主页面界面，包括目录选择、文件识别、
进度显示、多平台搜索结果展示和批量操作等功能。
"""

from __future__ import annotations

import os
import shutil
import time
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    LineEdit,
    MessageBox,
    ProgressBar,
    PushButton,
    SubtitleLabel,
    SwitchButton,
    TableWidget,
)
from qfluentwidgets import FluentIcon as FIF

if TYPE_CHECKING:
    from auto_tag.gui.workers.recognize_worker import RecognizeWorker

from auto_tag.audio_recognize import (
    update_mp3_cover_art,
    update_mp3_tags,
    update_ogg_tags,
)
from auto_tag.gui.i18n import tr
from auto_tag.gui.workers import RecognizeWorker


# 平台名称映射
_PLATFORM_NAME_MAP = {
    "shazam": "source_shazam",
    "netease": "source_netease",
    "kugou": "source_kugou",
}


class HomePage(QWidget):
    """
    音频识别主页面

    提供音频文件识别和标签更新的用户界面。

    Attributes:
        dir_var (str): 输入目录路径
        copy_enabled (bool): 是否启用复制到目录
        copy_dir (str): 复制目标目录路径
        tag_only (bool): 是否仅更新标签
        data (list[dict]): 识别结果数据列表
        worker (RecognizeWorker | None): 当前工作线程实例
        search_results_map (dict): 文件路径到搜索结果列表的映射
        _selected_results (dict): 用户为每个文件选择的搜索结果索引
    """

    def __init__(self, parent=None) -> None:
        """
        初始化主页面

        Args:
            parent (QWidget | None): 父窗口组件
        """
        super().__init__(parent)

        # 状态变量
        self.dir_var = ""
        self.copy_enabled = False
        self.copy_dir = ""
        self.tag_only = False
        self.data: list[dict] = []
        self.worker: RecognizeWorker | None = None

        # 多平台搜索结果存储
        self.search_results_map: dict[str, list[dict]] = {}
        self._selected_results: dict[str, int] = {}

        # 构建 UI
        self._setup_ui()

        # 连接信号槽
        self._connect_signals()

    def _setup_ui(self) -> None:
        """
        构建主页面 UI 布局

        创建所有界面组件并使用布局管理器组织它们，
        包括输入区域、进度区域、结果表格和操作按钮。
        """
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        # === 输入区域 ===
        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)

        # 目录选择
        self.dir_label = BodyLabel(tr("input_directory"))
        input_layout.addWidget(self.dir_label)

        self.dir_entry = LineEdit()
        self.dir_entry.setPlaceholderText(tr("select_directory"))
        self.dir_entry.setFixedHeight(36)
        input_layout.addWidget(self.dir_entry)

        self.browse_btn = PushButton(tr("browse"))
        self.browse_btn.setFixedHeight(36)
        self.browse_btn.clicked.connect(self._on_browse)
        input_layout.addWidget(self.browse_btn)

        # 复制到开关和目录
        self.copy_switch = SwitchButton()
        self.copy_switch.setFixedSize(50, 28)
        self.copy_switch.setChecked(False)
        self.copy_switch.setOffText("")
        self.copy_switch.setOnText("")
        input_layout.addWidget(self.copy_switch)

        self.copy_to_label = BodyLabel(tr("copy_to"))
        input_layout.addWidget(self.copy_to_label)

        self.copy_dir_entry = LineEdit()
        self.copy_dir_entry.setPlaceholderText(tr("select_directory"))
        self.copy_dir_entry.setFixedHeight(36)
        self.copy_dir_entry.setEnabled(False)
        input_layout.addWidget(self.copy_dir_entry)

        self.copy_browse_btn = PushButton(tr("browse"))
        self.copy_browse_btn.setFixedHeight(36)
        self.copy_browse_btn.clicked.connect(self._on_browse_copy)
        self.copy_browse_btn.setEnabled(False)
        input_layout.addWidget(self.copy_browse_btn)

        # 仅标签开关
        self.tag_switch = SwitchButton()
        self.tag_switch.setFixedSize(50, 28)
        self.tag_switch.setChecked(False)
        self.tag_switch.setOffText("")
        self.tag_switch.setOnText("")
        input_layout.addWidget(self.tag_switch)

        self.tags_only_label = BodyLabel(tr("tags_only"))
        input_layout.addWidget(self.tags_only_label)

        layout.addLayout(input_layout)

        # === 进度区域 ===
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(12)

        self.progress_bar = ProgressBar()
        self.progress_bar.setFixedHeight(8)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = BodyLabel(
            tr("progress_format", done=0, total=0, remaining=0)
        )
        progress_layout.addWidget(self.status_label)

        layout.addLayout(progress_layout)

        # === 搜索结果表格 ===
        self.table_title = SubtitleLabel(tr("search_results"))
        layout.addWidget(self.table_title)

        self.result_table = TableWidget()
        self.result_table.setColumnCount(7)
        self.result_table.setHorizontalHeaderLabels([
            tr("apply"),
            tr("source_platform"),
            tr("old_name"),
            tr("title"),
            tr("artist"),
            tr("album"),
            tr("duration"),
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        self.result_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self.result_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.result_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.result_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        self.result_table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.Stretch
        )
        self.result_table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.Fixed
        )
        self.result_table.setColumnWidth(0, 60)
        self.result_table.setColumnWidth(1, 100)
        self.result_table.setColumnWidth(6, 70)
        self.result_table.setMinimumHeight(300)
        layout.addWidget(self.result_table)

        # === 操作按钮区域 ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.check_all_btn = PushButton(tr("check_all"))
        self.check_all_btn.clicked.connect(self._on_check_all)
        btn_layout.addWidget(self.check_all_btn)

        self.uncheck_all_btn = PushButton(tr("uncheck_all"))
        self.uncheck_all_btn.clicked.connect(self._on_uncheck_all)
        btn_layout.addWidget(self.uncheck_all_btn)

        self.apply_btn = PushButton(FIF.ACCEPT, tr("apply"))
        self.apply_btn.clicked.connect(lambda: self._on_apply())
        btn_layout.addWidget(self.apply_btn)

        self.apply_plex_btn = PushButton(FIF.FOLDER, tr("apply_plex"))
        self.apply_plex_btn.clicked.connect(lambda: self._on_apply(plex=True))
        btn_layout.addWidget(self.apply_plex_btn)

        layout.addLayout(btn_layout)

    def _connect_signals(self) -> None:
        """
        连接信号槽

        将 UI 组件的信号连接到对应的处理方法。
        """
        # 复制到开关状态变化
        self.copy_switch.checkedChanged.connect(self._on_copy_switch_changed)

        # 仅标签开关状态变化
        self.tag_switch.checkedChanged.connect(self._on_tag_switch_changed)

    def _on_copy_switch_changed(self, checked: bool) -> None:
        """
        复制到开关切换回调

        Args:
            checked (bool): 开关是否选中
        """
        self.copy_enabled = checked
        self.copy_dir_entry.setEnabled(checked)
        self.copy_browse_btn.setEnabled(checked)

    def _on_tag_switch_changed(self, checked: bool) -> None:
        """
        仅标签开关切换回调

        Args:
            checked (bool): 开关是否选中
        """
        self.tag_only = checked

    def _on_browse(self) -> None:
        """
        浏览按钮点击处理

        打开文件夹选择对话框，选择后启动识别任务。
        """
        directory = QFileDialog.getExistingDirectory(
            self,
            tr("select_directory"),
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if directory:
            self.dir_var = directory
            self.dir_entry.setText(directory)
            self._start_recognition(directory)

    def _on_browse_copy(self) -> None:
        """
        复制目标目录浏览按钮处理

        打开文件夹选择对话框，选择复制目标目录。
        """
        directory = QFileDialog.getExistingDirectory(
            self,
            tr("select_directory"),
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if directory:
            self.copy_dir = directory
            self.copy_dir_entry.setText(directory)

    def _start_recognition(self, directory: str) -> None:
        """
        启动识别任务

        在后台线程中执行音频文件识别。

        Args:
            directory (str): 要识别的目录路径
        """
        # 清空之前的结果
        self.data.clear()
        self.search_results_map.clear()
        self._selected_results.clear()
        self.result_table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.status_label.setText(
            tr("progress_format", done=0, total=0, remaining=0)
        )

        # 创建工作线程
        self.worker = RecognizeWorker(
            directory=directory,
            copy_dir=self.copy_dir if self.copy_enabled else None,
            tag_only=self.tag_only
        )

        # 连接信号
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.file_processed.connect(self._on_file_processed)
        self.worker.finished_all.connect(self._on_finished_all)
        self.worker.error_occurred.connect(self._on_error_occurred)

        # 启动线程
        self.worker.start()

    def _on_progress_updated(self, done: int, total: int, remaining: int) -> None:
        """
        进度更新回调

        更新进度条和状态文本显示当前识别进度。

        Args:
            done (int): 已完成文件数
            total (int): 总文件数
            remaining (int): 预计剩余时间（秒）
        """
        if total > 0:
            value = int(done / total * 100)
            self.progress_bar.setValue(value)
        self.status_label.setText(
            tr("progress_format", done=done, total=total, remaining=remaining)
        )

    def _format_duration(self, seconds: int) -> str:
        """
        格式化时长显示

        Args:
            seconds (int): 时长（秒）

        Returns:
            str: 格式化后的时长字符串
        """
        if not seconds:
            return "--"
        minutes = seconds // 60
        secs = seconds % 60
        if minutes > 0:
            return tr("minutes_seconds_format", minutes=minutes, seconds=secs)
        return tr("seconds_format", seconds=secs)

    def _get_platform_display_name(self, source: str) -> str:
        """
        获取平台显示名称

        Args:
            source (str): 平台标识

        Returns:
            str: 翻译后的平台名称
        """
        key = _PLATFORM_NAME_MAP.get(source, source)
        return tr(key)

    def _on_file_processed(self, result: dict) -> None:
        """
        单个文件处理完成回调

        将识别结果和多平台搜索结果添加到表格中显示。

        Args:
            result (dict): 单个文件的识别结果字典
        """
        self.data.append(result)
        file_path = result.get("file_path", "")
        search_results = result.get("search_results", [])

        # 存储搜索结果
        self.search_results_map[file_path] = search_results
        # 默认选择第一个（置信度最高的）结果
        self._selected_results[file_path] = 0

        # 为每个平台结果添加一行
        if search_results:
            for sr in search_results:
                self._add_result_row(result, sr)
        else:
            # 没有搜索结果，只显示基本识别信息
            self._add_result_row(result, None)

    def _add_result_row(self, entry: dict, search_result: dict | None) -> None:
        """
        添加一行结果到表格

        Args:
            entry (dict): 文件识别结果条目
            search_result (dict | None): 平台搜索结果，None 表示使用默认 Shazam 结果
        """
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)

        file_path = entry.get("file_path", "")
        has_error = "error" in entry

        # 获取显示数据
        if search_result:
            source = search_result.get("source", "shazam")
            title = search_result.get("title", "")
            artist = search_result.get("artist", "")
            album = search_result.get("album", "")
            duration = search_result.get("duration", 0)
            source_display = self._get_platform_display_name(source)
            row_data_key = file_path
        else:
            source = "shazam"
            title = entry.get("title", "")
            artist = entry.get("author", "")
            album = entry.get("album", "")
            duration = 0
            source_display = self._get_platform_display_name("shazam")
            row_data_key = file_path

        # 勾选框列
        checkbox_item = QTableWidgetItem()
        checkbox_item.setFlags(
            Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
        )
        if not has_error:
            checkbox_item.setCheckState(Qt.CheckState.Checked)
            checkbox_item.setForeground(Qt.GlobalColor.green)
        else:
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
            checkbox_item.setForeground(Qt.GlobalColor.red)
        self.result_table.setItem(row, 0, checkbox_item)

        # 平台来源列
        source_item = QTableWidgetItem(source_display)
        source_item.setFlags(source_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.result_table.setItem(row, 1, source_item)

        # 原文件名列
        display_name = os.path.basename(file_path) if file_path else ""
        old_name_item = QTableWidgetItem(display_name)
        old_name_item.setFlags(old_name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        old_name_item.setToolTip(file_path)
        self.result_table.setItem(row, 2, old_name_item)

        # 标题列
        title_item = QTableWidgetItem(title)
        title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.result_table.setItem(row, 3, title_item)

        # 艺术家列
        artist_item = QTableWidgetItem(artist)
        artist_item.setFlags(artist_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.result_table.setItem(row, 4, artist_item)

        # 专辑列
        album_item = QTableWidgetItem(album)
        album_item.setFlags(album_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.result_table.setItem(row, 5, album_item)

        # 时长列
        duration_text = self._format_duration(duration)
        duration_item = QTableWidgetItem(duration_text)
        duration_item.setFlags(duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.result_table.setItem(row, 6, duration_item)

    def _on_finished_all(self, results: list) -> None:
        """
        所有文件处理完成回调

        更新最终状态，如果没有找到音频文件则显示提示消息。

        Args:
            results (list): 所有文件的识别结果列表
        """
        self.progress_bar.setValue(100)
        if not results:
            MessageBox(
                "Info",
                tr("no_audio_files"),
                self
            ).exec()

    def _on_error_occurred(self, error_msg: str) -> None:
        """
        错误发生回调

        显示错误消息对话框。

        Args:
            error_msg (str): 错误信息文本
        """
        MessageBox("Error", error_msg, self).exec()

    def _on_check_all(self) -> None:
        """全选：将所有结果的勾选状态设为选中"""
        for row in range(self.result_table.rowCount()):
            item = self.result_table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def _on_uncheck_all(self) -> None:
        """全不选：将所有结果的勾选状态设为未选中"""
        for row in range(self.result_table.rowCount()):
            item = self.result_table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def _on_apply(self, plex: bool = False) -> None:
        """
        应用更改

        对所有勾选的识别结果执行重命名或标签更新操作。

        Args:
            plex (bool): 是否按 Plex 结构组织文件
        """
        errors: list[str] = []

        for entry in self.data:
            if not entry.get("apply"):
                continue

            src = entry.get("file_path")
            file_path = entry.get("file_path", "")

            if not src:
                continue

            # 获取用户选择的结果（如果有的话）
            selected_idx = self._selected_results.get(file_path, 0)
            search_results = self.search_results_map.get(file_path, [])

            # 使用选中的搜索结果，如果没有则使用默认 Shazam 结果
            if search_results and 0 <= selected_idx < len(search_results):
                selected = search_results[selected_idx]
                title = selected.get("title", entry.get("title", ""))
                artist = selected.get("artist", entry.get("author", ""))
                album = selected.get("album", entry.get("album", ""))
                cover_link = selected.get("cover_link", entry.get("cover_link", ""))
            else:
                title = entry.get("title", "")
                artist = entry.get("author", "")
                album = entry.get("album", "")
                cover_link = entry.get("cover_link", "")

            # 生成新文件名
            from auto_tag.utils import sanitize
            s_title = sanitize(title, False)
            s_artist = sanitize(artist, False)
            s_album = sanitize(album, False)

            ext = os.path.splitext(src)[1].lower()
            if plex:
                new_name = f"{s_title}{ext}"
            else:
                new_name = f"{s_title} - {s_artist} - {s_album}{ext}"

            try:
                if self.tag_only:
                    if src.lower().endswith(".mp3"):
                        update_mp3_tags(src, s_title, s_artist, s_album)
                        update_mp3_cover_art(
                            src, cover_link, trace=False
                        )
                    elif src.lower().endswith(".ogg"):
                        update_ogg_tags(
                            src, s_title, s_artist, s_album,
                            cover_link,
                            trace=False
                        )
                else:
                    root_dir = self.copy_dir if (self.copy_enabled and self.copy_dir) else os.path.dirname(src)
                    if plex:
                        root_dir = os.path.join(root_dir, s_artist, s_album)
                    os.makedirs(root_dir, exist_ok=True)

                    new_path = os.path.join(root_dir, new_name)
                    count = 1
                    while os.path.exists(new_path) and new_path != src:
                        stem, e2 = os.path.splitext(new_path)
                        new_path = f"{stem} ({count}){e2}"
                        count += 1

                    if self.copy_enabled and self.copy_dir:
                        shutil.copy2(src, new_path)
                    else:
                        os.rename(src, new_path)

                    if ext == ".mp3":
                        update_mp3_tags(new_path, s_title, s_artist, s_album)
                        update_mp3_cover_art(
                            new_path, cover_link, trace=False
                        )
                    elif ext == ".ogg":
                        update_ogg_tags(
                            new_path, s_title, s_artist, s_album,
                            cover_link,
                            trace=False
                        )
            except Exception as exc:
                errors.append(f"{src}: {exc}")

        if errors:
            MessageBox(
                tr("errors_occurred"),
                "\n".join(errors),
                self,
            ).exec()
        else:
            checked_count = sum(
                1 for row in range(self.result_table.rowCount())
                if self.result_table.item(row, 0) and
                self.result_table.item(row, 0).checkState() == Qt.CheckState.Checked
            )

            if checked_count == 0:
                MessageBox(
                    "Info",
                    tr("no_files_processed"),
                    self,
                ).exec()
            else:
                MessageBox(
                    tr("success"),
                    tr("changes_applied"),
                    self,
                ).exec()

    def refresh_texts(self) -> None:
        """
        刷新页面文本

        当语言切换时调用此方法，更新所有 UI 文本为当前语言的翻译。
        """
        # 更新占位符文本
        self.dir_entry.setPlaceholderText(tr("select_directory"))
        self.copy_dir_entry.setPlaceholderText(tr("select_directory"))

        # 更新输入区域标签文本
        self.dir_label.setText(tr("input_directory"))
        self.copy_to_label.setText(tr("copy_to"))
        self.tags_only_label.setText(tr("tags_only"))

        # 更新状态文本
        if self.result_table.rowCount() == 0:
            self.status_label.setText(
                tr("progress_format", done=0, total=0, remaining=0)
            )

        # 更新表头
        self.result_table.setHorizontalHeaderLabels([
            tr("apply"),
            tr("source_platform"),
            tr("old_name"),
            tr("title"),
            tr("artist"),
            tr("album"),
            tr("duration"),
        ])

        # 更新标题
        self.table_title.setText(tr("search_results"))

        # 更新按钮文本
        self.browse_btn.setText(tr("browse"))
        self.copy_browse_btn.setText(tr("browse"))
        self.check_all_btn.setText(tr("check_all"))
        self.uncheck_all_btn.setText(tr("uncheck_all"))
        self.apply_btn.setText(tr("apply"))
        self.apply_plex_btn.setText(tr("apply_plex"))
