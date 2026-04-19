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
import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QScrollArea,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QFrame,
    QSizePolicy,
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
    CardWidget,
    isDarkTheme,
    qconfig,
)
from qfluentwidgets import FluentIcon as FIF

if TYPE_CHECKING:
    from auto_tag.gui.workers.recognize_worker import RecognizeWorker
    from auto_tag.gui.components.song_result_card import SongResultCard

from auto_tag.audio_recognize import (
    update_mp3_cover_art,
    update_mp3_tags,
    update_ogg_tags,
)
from auto_tag.gui.i18n import tr
from auto_tag.gui.workers import RecognizeWorker
from auto_tag.gui.components.song_result_card import SongResultCard

logger = logging.getLogger(__name__)


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
        song_cards (dict): 文件路径到歌曲卡片的映射
    """

    # 自定义信号
    selection_changed = Signal(str, int)

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
        self.song_cards: dict[str, "SongResultCard"] = {}

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

        # === 搜索结果区域 ===
        self.table_title = SubtitleLabel(tr("search_results"))
        layout.addWidget(self.table_title)

        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setMinimumHeight(400)
        self._update_scroll_area_style()

        # 创建内容容器
        self.cards_container = QFrame()
        self.cards_container.setObjectName("cardsContainer")
        self._update_cards_container_style()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area)

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

        # 主题切换
        qconfig.themeChanged.connect(self._on_theme_changed)

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

    def _update_scroll_area_style(self) -> None:
        """更新滚动区域样式以适配当前主题"""
        if isDarkTheme():
            bg_color = "#1e1e1e"
            border_color = "#3d3d3d"
        else:
            bg_color = "#fafafa"
            border_color = "#e0e0e0"

        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {bg_color};
            }}
        """)

    def _update_cards_container_style(self) -> None:
        """更新卡片容器样式以适配当前主题"""
        if isDarkTheme():
            bg_color = "#1e1e1e"
        else:
            bg_color = "#fafafa"

        self.cards_container.setStyleSheet(f"""
            #cardsContainer {{
                background-color: {bg_color};
            }}
        """)

    def _on_theme_changed(self) -> None:
        """主题切换回调，更新所有样式"""
        self._update_scroll_area_style()
        self._update_cards_container_style()

        # 更新所有卡片的主题
        for card in self.song_cards.values():
            card._on_theme_changed()

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
        self.song_cards.clear()

        # 清空卡片容器
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.cards_layout.addStretch()

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

        将识别结果和多平台搜索结果以卡片形式展示。

        Args:
            result (dict): 单个文件的识别结果字典
        """
        try:
            self.data.append(result)
            file_path = result.get("file_path", "")
            search_results = result.get("search_results", [])
            has_error = "error" in result

            # 存储搜索结果
            self.search_results_map[file_path] = search_results

            # 如果没有多平台搜索结果但 Shazam 识别成功，
            # 将 Shazam 结果包装为搜索结果格式，确保卡片能显示信息
            if not search_results and result.get("title"):
                shazam_result = {
                    "platform": "Shazam",
                    "title": result.get("title", ""),
                    "artist": result.get("author", ""),
                    "album": result.get("album", ""),
                    "cover_url": result.get("cover_link", ""),
                }
                search_results = [shazam_result]
                self.search_results_map[file_path] = search_results
                logger.info(f"[HomePage] Wrapped Shazam result for {display_name}")

            # 默认选择第一个（置信度最高的）结果
            self._selected_results[file_path] = 0

            # 显示文件名
            display_name = os.path.basename(file_path) if file_path else "Unknown"

            # 创建歌曲卡片
            card = SongResultCard(
                file_path=file_path,
                display_name=display_name,
                search_results=search_results,
                default_result=result if not search_results else None,
                has_error=has_error,
            )

            # 设置选中变化回调
            card.set_on_selection_changed(self._on_card_selection_changed)

            # 添加到布局（在 stretch 之前插入）
            self.cards_layout.insertWidget(
                self.cards_layout.count() - 1,
                card
            )

            # 保存卡片引用
            self.song_cards[file_path] = card

            logger.info(
                f"[HomePage] Card created for {display_name}, "
                f"results={len(search_results)}, error={has_error}"
            )
        except Exception as e:
            logger.error(
                f"[HomePage] Failed to create card for "
                f"{result.get('file_path', 'unknown')}: {e}",
                exc_info=True
            )

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

    def _on_card_selection_changed(self, file_path: str, index: int) -> None:
        """
        卡片选中平台变化回调

        Args:
            file_path (str): 文件路径
            index (int): 选中的平台结果索引
        """
        self._selected_results[file_path] = index

    def _on_check_all(self) -> None:
        """全选：将所有卡片的勾选状态设为选中"""
        for card in self.song_cards.values():
            card.checkbox.setChecked(True)

    def _on_uncheck_all(self) -> None:
        """全不选：将所有卡片的勾选状态设为未选中"""
        for card in self.song_cards.values():
            card.checkbox.setChecked(False)

    def _on_apply(self, plex: bool = False) -> None:
        """
        应用更改

        对所有勾选的识别结果执行重命名或标签更新操作。

        Args:
            plex (bool): 是否按 Plex 结构组织文件
        """
        errors: list[str] = []

        for entry in self.data:
            file_path = entry.get("file_path", "")
            card = self.song_cards.get(file_path)

            # 检查是否勾选
            if not card or not card.is_checked():
                continue

            src = entry.get("file_path")
            if not src:
                continue

            # 获取用户选择的结果
            selected_result = card.get_selected_result()
            title = selected_result.get("title", entry.get("title", ""))
            artist = selected_result.get("artist", entry.get("author", ""))
            album = selected_result.get("album", entry.get("album", ""))
            cover_link = selected_result.get(
                "cover_link", entry.get("cover_link", "")
            )

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
                1 for card in self.song_cards.values()
                if card.is_checked()
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
        if not self.song_cards:
            self.status_label.setText(
                tr("progress_format", done=0, total=0, remaining=0)
            )

        # 更新标题
        self.table_title.setText(tr("search_results"))

        # 更新按钮文本
        self.browse_btn.setText(tr("browse"))
        self.copy_browse_btn.setText(tr("browse"))
        self.check_all_btn.setText(tr("check_all"))
        self.uncheck_all_btn.setText(tr("uncheck_all"))
        self.apply_btn.setText(tr("apply"))
        self.apply_plex_btn.setText(tr("apply_plex"))

        # 刷新所有卡片的平台名称
        for card in self.song_cards.values():
            for i in range(card.results_container.layout().count()):
                widget = card.results_container.layout().itemAt(i).widget()
                if hasattr(widget, '_get_platform_display_name'):
                    # 需要重新创建平台组件来更新文本
                    # 这里简化处理，仅更新可见部分
                    pass
