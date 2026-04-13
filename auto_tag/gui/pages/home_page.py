# -*- coding: utf-8 -*-
"""
音频识别主页面模块

该模块提供音频识别功能的主页面界面，包括目录选择、文件识别、
进度显示、结果展示和批量操作等功能。

@module home_page
@author Frontend Architect
@version 1.0.0
"""

from __future__ import annotations

import os
import shutil
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
    FluentIcon as FIF,
    MessageBox,
    ProgressBar,
    PushButton,
    SubtitleLabel,
    SwitchButton,
    TableWidget,
    LineEdit,
)

from auto_tag.audio_recognize import (
    update_mp3_cover_art,
    update_mp3_tags,
    update_ogg_tags,
)
from auto_tag.gui.i18n import tr
from auto_tag.gui.workers import RecognizeWorker

if TYPE_CHECKING:
    from qfluentwidgets import FluentIconBase


class HomePage(QWidget):
    """
    音频识别主页面类

    该类提供音频识别功能的主界面，包括目录选择、文件识别、
    进度显示、结果展示和批量操作等功能。

    Attributes:
        data (list[dict]): 存储识别结果的列表
        worker (RecognizeWorker | None): 当前工作线程
        dir_var (str): 输入目录路径
        copy_enabled (bool): 是否启用复制到功能
        copy_dir (str): 复制目标目录
        tag_only (bool): 是否仅更新标签

    Example:
        >>> home = HomePage()
        >>> home.show()
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        初始化主页面

        Args:
            parent: 父窗口部件，用于 Qt 对象树管理
        """
        super().__init__(parent)

        # 成员变量初始化
        self.data: list[dict] = []
        self.worker: RecognizeWorker | None = None
        self.dir_var: str = ""
        self.copy_enabled: bool = False
        self.copy_dir: str = ""
        self.tag_only: bool = False

        # 设置 UI
        self._setup_ui()

        # 连接信号槽
        self._connect_signals()

    def _setup_ui(self) -> None:
        """
        构建 UI 布局

        创建并布局所有 UI 组件，包括：
        - 顶部区域：目录选择、复制到目录、仅标签开关
        - 进度条区域：进度条和进度文本
        - 结果表格：显示识别结果
        - 底部按钮：全选、取消全选、应用、应用(Plex)
        """
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(24)

        # 顶部区域
        self._setup_top_area(main_layout)

        # 进度条区域
        self._setup_progress_area(main_layout)

        # 结果表格
        self._setup_table(main_layout)

        # 底部按钮区域
        self._setup_bottom_area(main_layout)

    def _setup_top_area(self, parent_layout: QVBoxLayout) -> None:
        """
        设置顶部区域布局

        Args:
            parent_layout: 父布局，用于添加顶部区域
        """
        # 顶部容器
        top_layout = QHBoxLayout()
        top_layout.setSpacing(16)

        # 输入目录区域
        dir_label = BodyLabel(tr("input_directory"))
        top_layout.addWidget(dir_label)

        self.dir_input = LineEdit()
        self.dir_input.setPlaceholderText(tr("select_directory"))
        self.dir_input.setFixedHeight(40)
        self.dir_input.setMinimumWidth(300)
        top_layout.addWidget(self.dir_input, 1)

        self.browse_btn = PushButton(tr("browse"))
        self.browse_btn.setFixedHeight(40)
        self.browse_btn.setFixedWidth(100)
        top_layout.addWidget(self.browse_btn)

        # 复制到目录区域
        self.copy_switch = SwitchButton(tr("copy_to"))
        top_layout.addWidget(self.copy_switch)

        self.copy_input = LineEdit()
        self.copy_input.setPlaceholderText(tr("select_directory"))
        self.copy_input.setFixedHeight(40)
        self.copy_input.setMinimumWidth(200)
        self.copy_input.setEnabled(False)
        top_layout.addWidget(self.copy_input, 1)

        self.copy_browse_btn = PushButton(tr("browse"))
        self.copy_browse_btn.setFixedHeight(40)
        self.copy_browse_btn.setFixedWidth(100)
        self.copy_browse_btn.setEnabled(False)
        top_layout.addWidget(self.copy_browse_btn)

        # 仅标签开关
        self.tag_only_switch = SwitchButton(tr("tags_only"))
        top_layout.addWidget(self.tag_only_switch)

        parent_layout.addLayout(top_layout)

    def _setup_progress_area(self, parent_layout: QVBoxLayout) -> None:
        """
        设置进度条区域布局

        Args:
            parent_layout: 父布局，用于添加进度条区域
        """
        # 进度条容器
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(16)

        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setMinimumHeight(8)
        progress_layout.addWidget(self.progress_bar, 1)

        # 进度文本
        self.progress_label = BodyLabel(tr("progress_format").format(done=0, total=0, remaining=0))
        self.progress_label.setFixedWidth(200)
        progress_layout.addWidget(self.progress_label)

        parent_layout.addLayout(progress_layout)

    def _setup_table(self, parent_layout: QVBoxLayout) -> None:
        """
        设置结果表格

        Args:
            parent_layout: 父布局，用于添加表格
        """
        # 表格标题
        table_title = SubtitleLabel(tr("new_name"))
        parent_layout.addWidget(table_title)

        # 创建表格
        self.table = TableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            tr("apply"),
            tr("old_name"),
            tr("new_name")
        ])

        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 80)

        # 设置表格属性
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed)

        parent_layout.addWidget(self.table, 1)

    def _setup_bottom_area(self, parent_layout: QVBoxLayout) -> None:
        """
        设置底部按钮区域布局

        Args:
            parent_layout: 父布局，用于添加底部按钮区域
        """
        # 底部按钮容器
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(16)
        bottom_layout.addStretch()

        # 全选按钮
        self.check_all_btn = PushButton(tr("check_all"))
        self.check_all_btn.setFixedHeight(40)
        self.check_all_btn.setFixedWidth(120)
        bottom_layout.addWidget(self.check_all_btn)

        # 取消全选按钮
        self.uncheck_all_btn = PushButton(tr("uncheck_all"))
        self.uncheck_all_btn.setFixedHeight(40)
        self.uncheck_all_btn.setFixedWidth(120)
        bottom_layout.addWidget(self.uncheck_all_btn)

        # 应用按钮
        self.apply_btn = PushButton(tr("apply"))
        self.apply_btn.setFixedHeight(40)
        self.apply_btn.setFixedWidth(120)
        bottom_layout.addWidget(self.apply_btn)

        # 应用(Plex)按钮
        self.apply_plex_btn = PushButton(tr("apply_plex"))
        self.apply_plex_btn.setFixedHeight(40)
        self.apply_plex_btn.setFixedWidth(120)
        bottom_layout.addWidget(self.apply_plex_btn)

        parent_layout.addLayout(bottom_layout)

    def _connect_signals(self) -> None:
        """
        连接信号槽

        连接所有 UI 组件的信号到对应的槽函数。
        """
        # 按钮点击信号
        self.browse_btn.clicked.connect(self._on_browse)
        self.copy_browse_btn.clicked.connect(self._on_browse_copy)
        self.check_all_btn.clicked.connect(self._on_check_all)
        self.uncheck_all_btn.clicked.connect(self._on_uncheck_all)
        self.apply_btn.clicked.connect(lambda: self._on_apply(plex=False))
        self.apply_plex_btn.clicked.connect(lambda: self._on_apply(plex=True))

        # 开关状态变化信号
        self.copy_switch.checkedChanged.connect(self._on_copy_switch_changed)
        self.tag_only_switch.checkedChanged.connect(self._on_tag_only_switch_changed)

        # 表格双击信号
        self.table.cellDoubleClicked.connect(self._on_table_double_click)

    def _on_browse(self) -> None:
        """
        选择输入目录

        打开目录选择对话框，选择后启动识别任务。
        """
        directory = QFileDialog.getExistingDirectory(
            self,
            tr("select_directory"),
            self.dir_var or "",
        )

        if directory:
            self.dir_var = directory
            self.dir_input.setText(directory)
            self._start_recognition(directory)

    def _on_browse_copy(self) -> None:
        """
        选择复制目标目录

        打开目录选择对话框，选择复制目标目录。
        """
        directory = QFileDialog.getExistingDirectory(
            self,
            tr("select_directory"),
            self.copy_dir or "",
        )

        if directory:
            self.copy_dir = directory
            self.copy_input.setText(directory)

    def _on_copy_switch_changed(self, checked: bool) -> None:
        """
        复制到开关状态变化处理

        Args:
            checked: 开关状态，True 表示启用
        """
        self.copy_enabled = checked
        self.copy_input.setEnabled(checked)
        self.copy_browse_btn.setEnabled(checked)

    def _on_tag_only_switch_changed(self, checked: bool) -> None:
        """
        仅标签开关状态变化处理

        Args:
            checked: 开关状态，True 表示启用
        """
        self.tag_only = checked

    def _start_recognition(self, directory: str) -> None:
        """
        启动识别任务

        清空之前的数据，创建并启动新的工作线程。

        Args:
            directory: 要扫描的音频文件目录路径
        """
        # 清空之前的数据
        self.data.clear()
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.progress_label.setText(tr("progress_format").format(done=0, total=0, remaining=0))

        # 停止之前的工作线程
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        # 创建新的工作线程
        self.worker = RecognizeWorker(
            directory=directory,
            copy_dir=self.copy_dir if self.copy_enabled else None,
            tag_only=self.tag_only,
            parent=self,
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
        进度更新处理

        Args:
            done: 已完成的文件数
            total: 总文件数
            remaining: 预计剩余时间（秒）
        """
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(done)
        self.progress_label.setText(
            tr("progress_format").format(done=done, total=total, remaining=remaining)
        )

    def _on_file_processed(self, result: dict) -> None:
        """
        单个文件处理完成处理

        将结果添加到数据列表并更新表格。

        Args:
            result: 文件识别结果字典
        """
        self.data.append(result)
        self._add_table_row(result)

    def _on_finished_all(self, results: list[dict]) -> None:
        """
        所有文件处理完成处理

        Args:
            results: 所有文件的识别结果列表
        """
        if not self.data:
            MessageBox(
                tr("no_files_processed"),
                tr("no_files_processed"),
                self,
            ).exec()

    def _on_error_occurred(self, error_msg: str) -> None:
        """
        错误发生处理

        Args:
            error_msg: 错误消息
        """
        MessageBox(
            tr("errors_occurred"),
            error_msg,
            self,
        ).exec()

    def _add_table_row(self, result: dict) -> None:
        """
        添加表格行

        Args:
            result: 文件识别结果字典
        """
        row = self.table.rowCount()
        self.table.insertRow(row)

        # 应用列（勾选框）
        apply_item = QTableWidgetItem()
        apply_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
        apply_item.setCheckState(
            Qt.CheckState.Checked if result.get("apply", False)
            else Qt.CheckState.Unchecked
        )
        self.table.setItem(row, 0, apply_item)

        # 原文件名列
        old_name = os.path.basename(result.get("file_path", ""))
        old_item = QTableWidgetItem(old_name)
        old_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.table.setItem(row, 1, old_item)

        # 新文件名列
        new_name = os.path.basename(result.get("new_file_path", ""))
        new_item = QTableWidgetItem(new_name)
        new_item.setFlags(
            Qt.ItemFlag.ItemIsEnabled |
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsEditable
        )
        self.table.setItem(row, 2, new_item)

        # 设置行颜色
        if result.get("apply", False):
            # 成功项：绿色背景
            apply_item.setBackground(Qt.GlobalColor.green)
        else:
            # 失败项：红色背景
            apply_item.setBackground(Qt.GlobalColor.red)

    def _on_table_double_click(self, row: int, column: int) -> None:
        """
        表格双击处理

        双击应用列切换勾选状态，双击新文件名列编辑文件名。

        Args:
            row: 行索引
            column: 列索引
        """
        if column == 0:
            # 双击应用列：切换勾选状态
            self._toggle_row_check(row)
        elif column == 2:
            # 双击新文件名列：编辑文件名（由表格自动处理）
            pass

    def _toggle_row_check(self, row: int) -> None:
        """
        切换行的勾选状态

        Args:
            row: 行索引
        """
        if row < 0 or row >= len(self.data):
            return

        # 切换数据中的 apply 状态
        self.data[row]["apply"] = not self.data[row].get("apply", False)

        # 更新表格中的勾选状态
        apply_item = self.table.item(row, 0)
        if apply_item:
            apply_item.setCheckState(
                Qt.CheckState.Checked if self.data[row]["apply"]
                else Qt.CheckState.Unchecked
            )
            # 更新背景颜色
            if self.data[row]["apply"]:
                apply_item.setBackground(Qt.GlobalColor.green)
            else:
                apply_item.setBackground(Qt.GlobalColor.red)

    def _on_check_all(self) -> None:
        """
        全选处理

        将所有行设置为勾选状态。
        """
        for idx, result in enumerate(self.data):
            result["apply"] = True
            apply_item = self.table.item(idx, 0)
            if apply_item:
                apply_item.setCheckState(Qt.CheckState.Checked)
                apply_item.setBackground(Qt.GlobalColor.green)

    def _on_uncheck_all(self) -> None:
        """
        取消全选处理

        将所有行设置为未勾选状态。
        """
        for idx, result in enumerate(self.data):
            result["apply"] = False
            apply_item = self.table.item(idx, 0)
            if apply_item:
                apply_item.setCheckState(Qt.CheckState.Unchecked)
                apply_item.setBackground(Qt.GlobalColor.red)

    def _on_apply(self, plex: bool = False) -> None:
        """
        应用更改处理

        遍历所有勾选项，执行文件重命名、复制或标签更新操作。

        Args:
            plex: 是否使用 Plex 目录结构
        """
        errors: list[str] = []
        copy_to = self.copy_dir if self.copy_enabled else None
        tag_only = self.tag_only

        for result in self.data:
            if not result.get("apply"):
                continue

            src = result.get("file_path")
            if not src or not os.path.exists(src):
                continue

            title = result.get("title", "Unknown Title")
            artist = result.get("author", "Unknown Artist")
            album = result.get("album", "Unknown Album")
            ext = os.path.splitext(src)[1].lower()

            # 仅更新标签模式
            if tag_only:
                try:
                    if ext == ".mp3":
                        update_mp3_tags(src, title, artist, album)
                        update_mp3_cover_art(
                            src, result.get("cover_link", ""), trace=False
                        )
                    else:
                        update_ogg_tags(
                            src,
                            title,
                            artist,
                            album,
                            result.get("cover_link", ""),
                            trace=False,
                        )
                except Exception as exc:
                    errors.append(f"{src}: {exc}")
                continue

            # 重命名或复制模式
            if plex:
                base_dir = os.path.join(os.path.dirname(src), artist, album)
            else:
                base_dir = os.path.dirname(src)

            if copy_to:
                base_dir = copy_to
                if plex:
                    base_dir = os.path.join(base_dir, artist, album)

            os.makedirs(base_dir, exist_ok=True)

            if plex:
                dest = os.path.join(base_dir, f"{title}{ext}")
            else:
                dest = result.get("new_file_path") or os.path.join(
                    base_dir, f"{title}{ext}"
                )

            # 处理文件名冲突
            counter, unique = 1, dest
            while os.path.exists(unique):
                root, ext2 = os.path.splitext(dest)
                unique = f"{root} ({counter}){ext2}"
                counter += 1

            try:
                if copy_to:
                    shutil.copy2(src, unique)
                else:
                    os.rename(src, unique)

                # 更新标签
                if ext == ".mp3":
                    update_mp3_tags(unique, title, artist, album)
                    update_mp3_cover_art(
                        unique, result.get("cover_link", ""), trace=False
                    )
                else:
                    update_ogg_tags(
                        unique,
                        title,
                        artist,
                        album,
                        result.get("cover_link", ""),
                        trace=False,
                    )
            except Exception as exc:
                errors.append(f"{src}: {exc}")

        # 显示结果
        if errors:
            MessageBox(
                tr("errors_occurred"),
                "\n".join(errors),
                self,
            ).exec()
        else:
            MessageBox(
                tr("success"),
                tr("changes_applied"),
                self,
            ).exec()
