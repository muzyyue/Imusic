# -*- coding: utf-8 -*-
"""
音频识别主页面模块

该模块提供音频识别功能的主页面界面，包括目录选择、文件识别、
进度显示、结果展示和批量操作等功能。
"""

from __future__ import annotations

import os
import shutil
import time
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QTableWidget,
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
        dir_label = BodyLabel(tr("input_directory"))
        input_layout.addWidget(dir_label)

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
        input_layout.addWidget(self.copy_switch)

        copy_to_label = BodyLabel(tr("copy_to"))
        input_layout.addWidget(copy_to_label)

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
        input_layout.addWidget(self.tag_switch)

        tags_only_label = BodyLabel(tr("tags_only"))
        input_layout.addWidget(tags_only_label)

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

        # === 结果表格 ===
        self.table_title = SubtitleLabel(tr("new_name"))
        layout.addWidget(self.table_title)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels([
            tr("apply"), tr("old_name"), tr("new_name")
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        self.result_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.result_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.result_table.setColumnWidth(0, 60)
        self.result_table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked | 
            QTableWidget.EditTrigger.EditKeyPressed
        )
        self.result_table.cellChanged.connect(self._on_cell_changed)
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

    def _on_file_processed(self, result: dict) -> None:
        """
        单个文件处理完成回调

        将识别结果添加到表格中显示。

        Args:
            result (dict): 单个文件的识别结果字典
        """
        self.data.append(result)
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)

        # 勾选框列
        checkbox_item = QTableWidgetItem()
        checkbox_item.setFlags(
            Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
        )
        if result.get("success"):
            checkbox_item.setCheckState(Qt.CheckState.Checked)
            checkbox_item.setForeground(Qt.GlobalColor.green)
        else:
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
            checkbox_item.setForeground(Qt.GlobalColor.red)
        self.result_table.setItem(row, 0, checkbox_item)

        # 原文件名列
        old_name_item = QTableWidgetItem(result.get("old_name", ""))
        old_name_item.setFlags(old_name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.result_table.setItem(row, 1, old_name_item)

        # 新文件名编辑列
        new_name_item = QTableWidgetItem(result.get("new_name", ""))
        new_name_item.setFlags(
            new_name_item.flags() | Qt.ItemFlag.ItemIsEditable
        )
        self.result_table.setItem(row, 2, new_name_item)

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

    def _on_cell_changed(self, row: int, column: int) -> None:
        """
        表格单元格内容变更回调

        当用户新文件名编辑完成后更新内部数据。

        Args:
            row (int): 变更的行索引
            column (int): 变更的列索引
        """
        if column == 2 and row < len(self.data):
            item = self.result_table.item(row, column)
            if item:
                self.data[row]["new_name"] = item.text()

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
            if not entry.get("success"):
                continue

            src = entry.get("old_name")
            unique = entry.get("unique_name")

            if not src or not unique:
                continue

            try:
                if self.tag_only:
                    result_data = entry.get("result_data", {})
                    title = result_data.get("title", "")
                    artist = result_data.get("subtitle", "")
                    album = result_data.get("album", "")

                    if src.lower().endswith(".mp3"):
                        update_mp3_tags(unique, title, artist, album)
                        update_mp3_cover_art(
                            unique, result_data.get("cover_link", ""), trace=False
                        )
                    elif src.lower().endswith(".ogg"):
                        update_ogg_tags(
                            unique, title, artist, album,
                            result_data.get("cover_link", ""),
                            trace=False
                        )
                else:
                    target_dir = ""
                    if plex:
                        result_data = entry.get("result_data", {})
                        artist = result_data.get("subtitle", "Unknown Artist")
                        album = result_data.get("album", "Unknown Album")
                        artist = "".join(c for c in artist if c.isalnum() or c in (" ", "_")).strip()
                        album = "".join(c for c in album if c.isalnum() or c in (" ", "_")).strip()
                        target_dir = os.path.join(os.path.dirname(src), artist, album)
                        os.makedirs(target_dir, exist_ok=True)

                    if self.copy_enabled and self.copy_dir:
                        dest_path = os.path.join(self.copy_dir, os.path.basename(unique))
                        shutil.copy2(src, dest_path)
                        if not self.tag_only:
                            os.rename(dest_path, os.path.join(self.copy_dir, unique))
                    elif plex and target_dir:
                        dest_path = os.path.join(target_dir, unique)
                        shutil.move(src, dest_path)
                    else:
                        dirname = os.path.dirname(src)
                        os.rename(src, os.path.join(dirname, unique))

                    if not self.tag_only:
                        result_data = entry.get("result_data", {})
                        title = result_data.get("title", "")
                        artist = result_data.get("subtitle", "")
                        album = result_data.get("album", "")

                        final_path = ""
                        if self.copy_enabled and self.copy_dir:
                            final_path = os.path.join(self.copy_dir, unique)
                        elif plex and target_dir:
                            final_path = os.path.join(target_dir, unique)
                        else:
                            final_path = os.path.join(os.path.dirname(src), unique)

                        if final_path.lower().endswith(".mp3"):
                            update_mp3_tags(final_path, title, artist, album)
                            update_mp3_cover_art(
                                final_path, result_data.get("cover_link", ""), trace=False
                            )
                        elif final_path.lower().endswith(".ogg"):
                            update_ogg_tags(
                                final_path, title, artist, album,
                                result_data.get("cover_link", ""),
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
                1 for d in self.data
                if d.get("success") and any(
                    self.result_table.item(i, 0).checkState() == Qt.CheckState.Checked
                    for i in range(min(self.result_table.rowCount(), len(self.data)))
                    if i < self.result_table.rowCount() and
                       self.result_table.item(i, 0) is not None
                )
            ) if self.result_table.rowCount() > 0 else 0

            if checked_count == 0 or not any(d.get("success") for d in self.data):
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

        # 更新状态文本
        if self.result_table.rowCount() == 0:
            self.status_label.setText(
                tr("progress_format", done=0, total=0, remaining=0)
            )

        # 更新表头
        self.result_table.setHorizontalHeaderLabels([
            tr("apply"), tr("old_name"), tr("new_name")
        ])

        # 更新标题
        self.table_title.setText(tr("new_name"))

        # 更新按钮文本
        self.browse_btn.setText(tr("browse"))
        self.copy_browse_btn.setText(tr("browse"))
        self.check_all_btn.setText(tr("check_all"))
        self.uncheck_all_btn.setText(tr("uncheck_all"))
        self.apply_btn.setText(tr("apply"))
        self.apply_plex_btn.setText(tr("apply_plex"))
