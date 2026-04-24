# -*- coding: utf-8 -*-
"""
歌曲搜索工作线程模块

该模块提供基于 QThread 的歌曲搜索工作线程，用于在后台执行
歌词搜索任务，并通过信号机制与主线程通信，避免阻塞 UI 线程。

@module song_search_worker
@author Backend Architect
@version 1.0.0
"""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QThread, Signal

from auto_tag.lyric import LyricManager


class SongSearchWorker(QThread):
    """
    歌曲搜索工作线程类

    该类继承自 QThread，用于在后台线程中执行歌曲搜索任务。
    通过信号机制向主线程报告搜索结果，避免阻塞 UI 线程。

    Attributes:
        search_finished (Signal): 搜索完成信号，参数为搜索结果列表
        search_error (Signal): 搜索错误信号，参数为错误消息字符串

    Example:
        >>> worker = SongSearchWorker(file_path="/path/to/song.mp3", provider="netease")
        >>> worker.search_finished.connect(on_search_done)
        >>> worker.search_error.connect(on_search_error)
        >>> worker.start()
    """

    search_finished = Signal(list)  # 搜索结果列表
    search_error = Signal(str)  # 错误消息

    def __init__(
        self,
        file_path: str,
        provider: str = "netease",
        parent=None,
    ) -> None:
        """
        初始化歌曲搜索工作线程

        Args:
            file_path: 要搜索歌词的音频文件路径
            provider: 歌词提供商名称（'netease', 'kugou'）
            parent: 父对象，用于 Qt 对象树管理
        """
        super().__init__(parent)
        self.file_path = file_path
        self.provider = provider
        self.logger = logging.getLogger(__name__)

    def run(self) -> None:
        """
        重写 QThread.run 方法，执行歌曲搜索任务

        该方法在后台线程中执行，搜索完成后发射 search_finished 信号。
        """
        try:
            manager = LyricManager()
            songs = manager.search_songs(self.file_path, self.provider)

            if songs is not None:
                self.search_finished.emit(songs)
            else:
                self.search_finished.emit([])
        except Exception as e:
            self.logger.error(
                f"歌曲搜索异常: {self.file_path}, "
                f"错误: {type(e).__name__}: {e}",
                exc_info=True,
            )
            self.search_error.emit(f"搜索失败: {str(e)}")
