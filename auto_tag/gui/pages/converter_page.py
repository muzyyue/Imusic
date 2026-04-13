# -*- coding: utf-8 -*-
"""
音频转换页面模块

该模块提供音频转换功能的页面界面，包括目录选择、格式转换、
进度显示、文件列表展示和批量操作等功能。
"""

from __future__ import annotations

import os
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
    ComboBox,
    LineEdit,
    MessageBox,
    ProgressBar,
    PushButton,
    SubtitleLabel,
    TableWidget,
)
from qfluentwidgets import FluentIcon as FIF

if TYPE_CHECKING:
    from auto_tag.converter.workers.converter_worker import ConverterWorker

from auto_tag.converter.config import ConverterConfig, OutputFormat, QualityPreset
from auto_tag.gui.i18n import tr


class ConverterPage(QWidget):
    """
    音频转换页面

    提供音频文件格式转换的用户界面。

    Attributes:
        input_dir (str): 输入目录路径
        output_dir (str): 输出目录路径
        files (list[str]): 待转换的文件列表
        worker (ConverterWorker | None): 当前工作线程实例
        config (ConverterConfig): 转换配置对象
        format_map (dict[str, OutputFormat]): 格式名称到枚举的映射
        quality_map (dict[str, QualityPreset]): 质量名称到枚举的映射
    """

    def __init__(self, parent=None) -> None:
        """
        初始化转换页面

        Args:
            parent (QWidget | None): 父窗口组件
        """
        super().__init__(parent)

        # 状态变量
        self.input_dir = ""
        self.output_dir = ""
        self.files: list[str] = []
        self.worker: ConverterWorker | None = None
        self.config = ConverterConfig()

        # 格式和预设映射
        self.format_map = {
            "MP3": OutputFormat.MP3,
            "FLAC": OutputFormat.FLAC,
            "AAC": OutputFormat.AAC,
            "OGG": OutputFormat.OGG,
            "WAV": OutputFormat.WAV,
            "M4A": OutputFormat.M4A,
        }

        self.quality_map = {
            "Low": QualityPreset.LOW,
            "Medium": QualityPreset.MEDIUM,
            "High": QualityPreset.HIGH,
            "Lossless": QualityPreset.LOSSLESS,
        }

        # 构建 UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        构建转换页面 UI 布局

        创建所有界面组件并使用布局管理器组织它们，
        包括输入区域、格式设置区域、进度区域、文件列表和操作按钮。
        """
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        # === 输入区域 ===
        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)

        # 输入目录选择
        self.input_label = BodyLabel(tr("input_directory"))
        input_layout.addWidget(self.input_label)

        self.input_entry = LineEdit()
        self.input_entry.setPlaceholderText(tr("select_directory"))
        self.input_entry.setFixedHeight(36)
        input_layout.addWidget(self.input_entry)

        self.input_browse_btn = PushButton(tr("browse"))
        self.input_browse_btn.setFixedHeight(36)
        self.input_browse_btn.clicked.connect(self._on_browse)
        input_layout.addWidget(self.input_browse_btn)

        # 输出目录选择
        self.output_label = BodyLabel(tr("output_directory"))
        input_layout.addWidget(self.output_label)

        self.output_entry = LineEdit()
        self.output_entry.setPlaceholderText(tr("select_directory"))
        self.output_entry.setFixedHeight(36)
        input_layout.addWidget(self.output_entry)

        self.output_browse_btn = PushButton(tr("browse"))
        self.output_browse_btn.setFixedHeight(36)
        self.output_browse_btn.clicked.connect(self._on_browse_output)
        input_layout.addWidget(self.output_browse_btn)

        layout.addLayout(input_layout)

        # === 格式设置区域 ===
        format_layout = QHBoxLayout()
        format_layout.setSpacing(12)

        # 输出格式选择
        self.format_label = BodyLabel(tr("output_format"))
        format_layout.addWidget(self.format_label)

        self.format_combo = ComboBox()
        self.format_combo.addItems(list(self.format_map.keys()))
        self.format_combo.setCurrentIndex(0)  # 默认选择 MP3
        self.format_combo.setFixedHeight(36)
        self.format_combo.setFixedWidth(120)
        format_layout.addWidget(self.format_combo)

        # 质量预设选择
        self.quality_label = BodyLabel(tr("quality_preset"))
        format_layout.addWidget(self.quality_label)

        self.quality_combo = ComboBox()
        self.quality_combo.addItems(list(self.quality_map.keys()))
        self.quality_combo.setCurrentIndex(2)  # 默认选择 High
        self.quality_combo.setFixedHeight(36)
        self.quality_combo.setFixedWidth(120)
        format_layout.addWidget(self.quality_combo)

        format_layout.addStretch()

        layout.addLayout(format_layout)

        # === 进度区域 ===
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(12)

        self.progress_bar = ProgressBar()
        self.progress_bar.setFixedHeight(8)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = BodyLabel(tr("conversion_in_progress"))
        progress_layout.addWidget(self.status_label)

        layout.addLayout(progress_layout)

        # === 文件列表 ===
        self.table_title = SubtitleLabel(tr("converter_file_list"))
        layout.addWidget(self.table_title)

        self.file_table = TableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels([
            tr("check"), tr("file_name"), tr("format"), tr("size"), tr("status")
        ])
        # 设置列宽
        self.file_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        self.file_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.file_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self.file_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed
        )
        self.file_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Fixed
        )
        self.file_table.setColumnWidth(0, 60)
        self.file_table.setColumnWidth(2, 80)
        self.file_table.setColumnWidth(3, 100)
        self.file_table.setColumnWidth(4, 100)
        self.file_table.setMinimumHeight(300)
        layout.addWidget(self.file_table)

        # === 操作按钮区域 ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.check_all_btn = PushButton(tr("check_all"))
        self.check_all_btn.clicked.connect(self._on_check_all)
        btn_layout.addWidget(self.check_all_btn)

        self.uncheck_all_btn = PushButton(tr("uncheck_all"))
        self.uncheck_all_btn.clicked.connect(self._on_uncheck_all)
        btn_layout.addWidget(self.uncheck_all_btn)

        self.start_btn = PushButton(FIF.PLAY, tr("start_conversion"))
        self.start_btn.clicked.connect(self._start_conversion)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = PushButton(FIF.CANCEL, tr("stop_conversion"))
        self.stop_btn.clicked.connect(self._stop_conversion)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        layout.addLayout(btn_layout)

    def _scan_files(self, directory: str) -> list[str]:
        """
        扫描目录中的所有支持格式的文件

        Args:
            directory (str): 要扫描的目录路径

        Returns:
            list[str]: 找到的文件路径列表
        """
        files = []

        # 遍历目录
        for root, dirs, filenames in os.walk(directory):
            # 跳过 test 目录
            if 'test' in dirs:
                dirs.remove('test')

            for filename in filenames:
                # 获取文件扩展名
                ext = os.path.splitext(filename)[1].lower().lstrip('.')

                # 检查是否为支持的格式
                if ext in self.config.supported_input_formats:
                    files.append(os.path.join(root, filename))

        return files

    def _format_file_size(self, size_bytes: int) -> str:
        """
        格式化文件大小显示

        Args:
            size_bytes (int): 文件大小（字节）

        Returns:
            str: 格式化后的文件大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _on_browse(self) -> None:
        """
        浏览按钮点击处理

        打开文件夹选择对话框，选择后扫描文件并填充表格。
        """
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择目录",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if directory:
            self.input_dir = directory
            self.input_entry.setText(directory)

            # 扫描文件
            self.files = self._scan_files(directory)

            # 清空表格
            self.file_table.setRowCount(0)

            # 填充表格
            for file_path in self.files:
                row = self.file_table.rowCount()
                self.file_table.insertRow(row)

                # 勾选框列
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
                )
                checkbox_item.setCheckState(Qt.CheckState.Checked)
                self.file_table.setItem(row, 0, checkbox_item)

                # 文件名列
                filename = os.path.basename(file_path)
                filename_item = QTableWidgetItem(filename)
                filename_item.setFlags(filename_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                # 存储完整路径
                filename_item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.file_table.setItem(row, 1, filename_item)

                # 格式列
                ext = os.path.splitext(file_path)[1].upper().lstrip('.')
                format_item = QTableWidgetItem(ext)
                format_item.setFlags(format_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.file_table.setItem(row, 2, format_item)

                # 大小列
                try:
                    size = os.path.getsize(file_path)
                    size_str = self._format_file_size(size)
                except OSError:
                    size_str = "未知"
                size_item = QTableWidgetItem(size_str)
                size_item.setFlags(size_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.file_table.setItem(row, 3, size_item)

                # 状态列
                status_item = QTableWidgetItem("待转换")
                status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                status_item.setForeground(Qt.GlobalColor.gray)
                self.file_table.setItem(row, 4, status_item)

            # 更新状态标签
            if self.files:
                self.status_label.setText(f"找到 {len(self.files)} 个文件")
            else:
                self.status_label.setText("未找到支持的文件")

    def _on_browse_output(self) -> None:
        """
        输出目录浏览按钮处理

        打开文件夹选择对话框，选择输出目录。
        """
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择目录",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if directory:
            self.output_dir = directory
            self.output_entry.setText(directory)

    def _start_conversion(self) -> None:
        """
        开始转换

        创建工作线程并启动转换任务。
        """
        # 检查是否有选中的文件
        selected_files = []
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                filename_item = self.file_table.item(row, 1)
                if filename_item:
                    file_path = filename_item.data(Qt.ItemDataRole.UserRole)
                    selected_files.append(file_path)

        if not selected_files:
            MessageBox(
                "提示",
                "请至少选择一个文件进行转换",
                self
            ).exec()
            return

        # 确定输出目录
        output_dir = self.output_dir if self.output_dir else self.input_dir

        # 获取格式和质量设置
        format_text = self.format_combo.currentText()
        quality_text = self.quality_combo.currentText()

        output_format = self.format_map.get(format_text, OutputFormat.MP3)
        quality_preset = self.quality_map.get(quality_text, QualityPreset.HIGH)

        # 更新配置
        self.config.set_output_format(output_format.value, quality_preset)

        # 重置进度
        self.progress_bar.setValue(0)
        self.status_label.setText("正在转换...")

        # 更新按钮状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # 创建工作线程
        self.worker = ConverterWorker(
            files=selected_files,
            output_dir=output_dir,
            config=self.config
        )

        # 连接信号
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.file_converted.connect(self._on_file_converted)
        self.worker.finished_all.connect(self._on_finished_all)
        self.worker.error_occurred.connect(self._on_error_occurred)

        # 启动线程
        self.worker.start()

    def _stop_conversion(self) -> None:
        """
        停止转换

        停止当前工作线程。
        """
        if self.worker:
            self.worker.stop()
            self.status_label.setText("正在停止...")

    def _on_progress_updated(self, current: int, total: int, filename: str) -> None:
        """
        进度更新回调

        更新进度条和状态文本显示当前转换进度。

        Args:
            current (int): 当前文件索引
            total (int): 总文件数
            filename (str): 当前文件名
        """
        if total > 0:
            value = int(current / total * 100)
            self.progress_bar.setValue(value)

        self.status_label.setText(f"正在转换 {current}/{total}: {filename}")

    def _on_file_converted(self, path: str, success: bool, error: str) -> None:
        """
        单个文件转换完成回调

        更新表格中对应文件的状态。

        Args:
            path (str): 文件路径
            success (bool): 是否成功
            error (str): 错误信息
        """
        # 查找对应的表格行
        for row in range(self.file_table.rowCount()):
            filename_item = self.file_table.item(row, 1)
            if filename_item:
                file_path = filename_item.data(Qt.ItemDataRole.UserRole)
                if file_path == path:
                    # 更新状态列
                    status_item = self.file_table.item(row, 4)
                    if status_item:
                        if success:
                            status_item.setText("成功")
                            status_item.setForeground(Qt.GlobalColor.green)
                        else:
                            status_item.setText("失败")
                            status_item.setForeground(Qt.GlobalColor.red)
                    break

    def _on_finished_all(self, results: list) -> None:
        """
        所有文件转换完成回调

        显示转换结果统计信息。

        Args:
            results (list): 所有文件的转换结果列表
        """
        # 统计结果
        success_count = sum(1 for r in results if r.get("success"))
        total_count = len(results)

        # 更新进度
        self.progress_bar.setValue(100)
        self.status_label.setText(f"转换完成: {success_count}/{total_count} 成功")

        # 更新按钮状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        # 显示完成消息
        if success_count == total_count:
            MessageBox(
                "成功",
                f"所有文件转换完成！共 {total_count} 个文件",
                self
            ).exec()
        else:
            failed_count = total_count - success_count
            MessageBox(
                "完成",
                f"转换完成：成功 {success_count} 个，失败 {failed_count} 个",
                self
            ).exec()

    def _on_error_occurred(self, error_msg: str) -> None:
        """
        错误发生回调

        显示错误消息对话框。

        Args:
            error_msg (str): 错误信息文本
        """
        MessageBox("错误", error_msg, self).exec()

        # 更新按钮状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _on_check_all(self) -> None:
        """全选：将所有文件的勾选状态设为选中"""
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def _on_uncheck_all(self) -> None:
        """取消全选：将所有文件的勾选状态设为未选中"""
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def refresh_texts(self) -> None:
        """
        刷新页面文本

        当语言切换时调用此方法，更新所有 UI 文本为当前语言的翻译。
        """
        # 更新占位符文本
        self.input_entry.setPlaceholderText(tr("select_directory"))
        self.output_entry.setPlaceholderText(tr("select_directory"))

        # 更新输入区域标签文本
        self.input_label.setText(tr("input_directory"))
        self.output_label.setText(tr("output_directory"))

        # 更新格式设置区域标签文本
        self.format_label.setText(tr("output_format"))
        self.quality_label.setText(tr("quality_preset"))

        # 更新表头
        self.file_table.setHorizontalHeaderLabels([
            tr("check"), tr("file_name"), tr("format"), tr("size"), tr("status")
        ])

        # 更新标题
        self.table_title.setText(tr("converter_file_list"))

        # 更新按钮文本
        self.input_browse_btn.setText(tr("browse"))
        self.output_browse_btn.setText(tr("browse"))
        self.check_all_btn.setText(tr("check_all"))
        self.uncheck_all_btn.setText(tr("uncheck_all"))
        self.start_btn.setText(tr("start_conversion"))
        self.stop_btn.setText(tr("stop_conversion"))
