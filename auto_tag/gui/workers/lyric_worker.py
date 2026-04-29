# -*- coding: utf-8 -*-
"""
歌词获取工作线程模块

该模块提供基于 QThread 的歌词获取工作线程，用于在后台执行歌词获取任务，
并通过信号机制与主线程通信，实现进度更新和结果传递。

@module lyric_worker
@author Backend Architect
@version 1.0.0
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any

from PySide6.QtCore import QThread, Signal

from auto_tag.lyric import LyricManager


class LyricWorker(QThread):
    """
    歌词获取工作线程类

    该类继承自 QThread，用于在后台线程中执行歌词获取任务。
    通过信号机制向主线程报告进度和结果，避免阻塞 UI 线程。

    Attributes:
        progress_updated (Signal): 进度更新信号，参数为 (已完成数, 总数, 剩余秒数)
        lyric_fetched (Signal): 单个文件歌词获取完成信号，参数为 (文件路径, 歌词数据)
        finished_all (Signal): 所有文件处理完成信号，参数为结果字典
        error_occurred (Signal): 错误发生信号，参数为错误消息字符串

    Example:
        >>> worker = LyricWorker(
        ...     file_paths=["/path/to/song1.mp3", "/path/to/song2.flac"],
        ...     provider="lrclib"
        ... )
        >>> worker.progress_updated.connect(on_progress)
        >>> worker.finished_all.connect(on_finished)
        >>> worker.start()
    """

    progress_updated = Signal(int, int, int)  # 已完成数, 总数, 剩余秒数
    lyric_fetched = Signal(str, object)  # 文件路径, 歌词数据或 None
    finished_all = Signal(dict)  # 结果字典 {文件路径: 歌词数据}
    error_occurred = Signal(str)  # 错误消息

    def __init__(
        self,
        file_paths: list[str],
        provider: str = "lrclib",
        song_id: int | str | None = None,
        parent=None,
    ) -> None:
        """
        初始化歌词获取工作线程

        Args:
            file_paths: 要获取歌词的音频文件路径列表
            provider: 歌词提供商名称（'lrclib', 'applemusic', 'musixmatch', 'netease', 'kugou'）
            song_id: 指定的歌曲 ID（用于网易云/酷狗音乐）
            parent: 父对象，用于 Qt 对象树管理
        """
        super().__init__(parent)
        self.file_paths = file_paths
        self.provider = provider
        self.song_id = song_id  # 指定的歌曲 ID
        self.start_time: float | None = None
        self._manager: LyricManager | None = None
        self.logger = logging.getLogger(__name__)

    def run(self) -> None:
        """
        重写 QThread.run 方法，执行歌词获取任务

        该方法在后台线程中执行，遍历文件列表获取歌词。
        完成后自动发射 finished_all 信号。

        Note:
            该方法由 Qt 框架自动调用，不应手动调用。
            使用 start() 方法启动线程。
        """
        try:
            self._manager = LyricManager()
            results = self._process_files()
            self.finished_all.emit(results)
        except Exception as e:
            self.error_occurred.emit(f"歌词获取过程发生错误: {str(e)}")

    def _process_files(self) -> dict[str, dict[str, Any] | None]:
        """
        处理所有音频文件，获取歌词

        遍历文件列表，对每个文件调用歌词管理器获取歌词，
        并发射进度信号通知主线程。

        Returns:
            dict[str, dict | None]: 文件路径到歌词数据的映射
        """
        total_files = len(self.file_paths)
        if total_files == 0:
            self.error_occurred.emit("未选择任何文件")
            return {}

        self.start_time = time.time()
        results: dict[str, dict[str, Any] | None] = {}

        for idx, file_path in enumerate(self.file_paths, start=1):
            try:
                if not os.path.exists(file_path):
                    self.logger.warning(f"文件不存在: {file_path}")
                    results[file_path] = None
                    self.lyric_fetched.emit(file_path, None)
                else:
                    self.logger.info(
                        f"[Batch] 处理第 {idx}/{len(self.file_paths)} 个文件: "
                        f"{os.path.basename(file_path)}"
                    )

                    # 如果指定了歌曲 ID，使用 fetch_lyric_by_id
                    if self.song_id and self.provider in ['netease', 'kugou']:
                        lyrics = self._manager.fetch_lyric_by_id(self.song_id, self.provider)
                        # 补充文件元数据信息
                        if lyrics:
                            metadata = self._manager._extract_audio_metadata(file_path)
                            if metadata:
                                lyrics['track_name'] = metadata.get('title', '')
                                lyrics['artist_name'] = metadata.get('artist', '')
                                lyrics['album_name'] = metadata.get('album', '')
                                lyrics['duration'] = metadata.get('duration', 0)
                    else:
                        lyrics = self._manager.fetch_lyrics(file_path, self.provider)

                    if lyrics:
                        self.logger.info(
                            f"[Batch] ✓ 获取歌词成功 ({idx}/{len(self.file_paths)}): "
                            f"{os.path.basename(file_path)}"
                        )
                        results[file_path] = lyrics
                        self.lyric_fetched.emit(file_path, lyrics)
                    else:
                        self.logger.warning(
                            f"[Batch] ✗ 获取歌词返回空 ({idx}/{len(self.file_paths)}): "
                            f"{os.path.basename(file_path)}"
                        )
                        results[file_path] = None
                        self.lyric_fetched.emit(file_path, None)
            except Exception as exc:
                self.logger.error(
                    f"[Batch] ✗ 获取歌词异常 ({idx}/{len(self.file_paths)}): "
                    f"{os.path.basename(file_path)}, 错误: {type(exc).__name__}: {exc}",
                    exc_info=True
                )
                results[file_path] = None
                self.lyric_fetched.emit(file_path, None)

            elapsed = time.time() - self.start_time
            remaining = int(elapsed / idx * (total_files - idx)) if idx > 0 else 0
            self.progress_updated.emit(idx, total_files, remaining)

        return results


class LyricEmbedWorker(QThread):
    """
    歌词嵌入工作线程类

    该类继承自 QThread，用于在后台线程中执行歌词嵌入任务。
    通过信号机制向主线程报告进度和结果。

    Attributes:
        progress_updated (Signal): 进度更新信号，参数为 (已完成数, 总数, 剩余秒数)
        lyric_embedded (Signal): 单个文件歌词嵌入完成信号，参数为 (文件路径, 成功标志)
        finished_all (Signal): 所有文件处理完成信号，参数为结果字典
        error_occurred (Signal): 错误发生信号，参数为错误消息字符串

    Example:
        >>> worker = LyricEmbedWorker(
        ...     file_lyrics_pairs=[
        ...         ("/path/to/song.mp3", "[00:00.00]歌词内容"),
        ...     ],
        ...     format="lrc"
        ... )
        >>> worker.start()
    """

    progress_updated = Signal(int, int, int)  # 已完成数, 总数, 剩余秒数
    lyric_embedded = Signal(str, bool)  # 文件路径, 成功标志
    finished_all = Signal(dict)  # 结果字典 {文件路径: 成功标志}
    error_occurred = Signal(str)  # 错误消息

    def __init__(
        self,
        file_lyrics_pairs: list[tuple[str, str]],
        format: str = "lrc",
        parent=None,
    ) -> None:
        """
        初始化歌词嵌入工作线程

        Args:
            file_lyrics_pairs: 文件路径和歌词内容的元组列表
            format: 歌词格式（'lrc', 'ttml', 'srt', 'json'）
            parent: 父对象，用于 Qt 对象树管理
        """
        super().__init__(parent)
        self.file_lyrics_pairs = file_lyrics_pairs
        self.format = format
        self.start_time: float | None = None
        self._manager: LyricManager | None = None

    def run(self) -> None:
        """
        重写 QThread.run 方法，执行歌词嵌入任务
        """
        try:
            self._manager = LyricManager()
            results = self._process_files()
            self.finished_all.emit(results)
        except Exception as e:
            self.error_occurred.emit(f"歌词嵌入过程发生错误: {str(e)}")

    def _process_files(self) -> dict[str, bool]:
        """
        处理所有音频文件，嵌入歌词

        Returns:
            dict[str, bool]: 文件路径到成功标志的映射
        """
        total_files = len(self.file_lyrics_pairs)
        if total_files == 0:
            self.error_occurred.emit("未选择任何文件")
            return {}

        self.start_time = time.time()
        results: dict[str, bool] = {}

        for idx, (file_path, lyrics) in enumerate(self.file_lyrics_pairs, start=1):
            try:
                success = self._manager.embed_lyrics(file_path, lyrics, self.format)
                results[file_path] = success
                self.lyric_embedded.emit(file_path, success)
            except Exception:
                results[file_path] = False
                self.lyric_embedded.emit(file_path, False)

            elapsed = time.time() - self.start_time
            remaining = int(elapsed / idx * (total_files - idx)) if idx > 0 else 0
            self.progress_updated.emit(idx, total_files, remaining)

        return results
