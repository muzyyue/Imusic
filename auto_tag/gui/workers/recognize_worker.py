# -*- coding: utf-8 -*-
"""
音频识别工作线程模块

该模块提供基于 QThread 的音频识别工作线程，用于在后台执行音频文件识别任务，
并通过信号机制与主线程通信，实现进度更新和结果传递。

@module recognize_worker
@author Backend Architect
@version 1.0.0
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import TYPE_CHECKING

from PySide6.QtCore import QThread, Signal

from auto_tag.audio_recognize import recognize_and_rename_file

if TYPE_CHECKING:
    from shazamio import Shazam


class RecognizeWorker(QThread):
    """
    音频识别工作线程类

    该类继承自 QThread，用于在后台线程中执行音频文件识别任务。
    通过信号机制向主线程报告进度和结果，避免阻塞 UI 线程。

    Attributes:
        progress_updated (Signal): 进度更新信号，参数为 (已完成数, 总数, 剩余秒数)
        file_processed (Signal): 单个文件处理完成信号，参数为识别结果字典
        finished_all (Signal): 所有文件处理完成信号，参数为结果列表
        error_occurred (Signal): 错误发生信号，参数为错误消息字符串

    Example:
        >>> worker = RecognizeWorker(
        ...     directory="/path/to/music",
        ...     copy_dir="/path/to/backup",
        ...     tag_only=False
        ... )
        >>> worker.progress_updated.connect(on_progress)
        >>> worker.finished_all.connect(on_finished)
        >>> worker.start()
    """

    # 信号定义
    progress_updated = Signal(int, int, int)  # 已完成数, 总数, 剩余秒数
    file_processed = Signal(dict)  # 单个文件识别结果
    finished_all = Signal(list)  # 所有结果列表
    error_occurred = Signal(str)  # 错误消息

    def __init__(
        self,
        directory: str,
        copy_dir: str | None,
        tag_only: bool,
        parent=None,
    ) -> None:
        """
        初始化识别工作线程

        Args:
            directory: 要扫描的音频文件目录路径
            copy_dir: 复制文件的目标目录，为 None 时不复制
            tag_only: 是否仅更新标签而不重命名文件
            parent: 父对象，用于 Qt 对象树管理
        """
        super().__init__(parent)
        self.directory = directory
        self.copy_dir = copy_dir
        self.tag_only = tag_only
        self.start_time: float | None = None

    def run(self) -> None:
        """
        重写 QThread.run 方法，执行异步识别任务

        该方法在后台线程中执行，通过 asyncio.run() 运行异步处理方法。
        完成后自动发射 finished_all 信号。

        Note:
            该方法由 Qt 框架自动调用，不应手动调用。
            使用 start() 方法启动线程。
        """
        try:
            results = asyncio.run(self._process_files())
            self.finished_all.emit(results)
        except Exception as e:
            self.error_occurred.emit(f"识别过程发生错误: {str(e)}")

    async def _process_files(self) -> list[dict]:
        """
        异步处理所有音频文件

        遍历目录收集音频文件，对每个文件调用 Shazam API 进行识别，
        并发射进度信号通知主线程。同时在 Shazam 识别成功后，
        并发向网易云音乐和酷狗音乐搜索补充信息。

        Returns:
            list[dict]: 所有文件的识别结果列表，每个元素为包含以下键的字典：
                - file_path: 原始文件路径
                - new_file_path: 新文件路径
                - title: 歌曲标题
                - author: 艺术家
                - album: 专辑名
                - cover_link: 封面 URL
                - search_results: 多平台搜索结果列表
                - error: 错误信息（可选）
                - apply: 是否可应用（无错误时为 True）

        Note:
            该方法会跳过名称包含 "test" 的目录。
        """
        # 收集音频文件
        audio_files: list[str] = []
        for rootdir, _, names in os.walk(self.directory):
            # 跳过 test 目录
            if "test" in os.path.basename(rootdir).lower():
                continue
            for name in names:
                if name.lower().endswith((".mp3", ".ogg")):
                    audio_files.append(os.path.join(rootdir, name))

        total_files = len(audio_files)
        if total_files == 0:
            self.error_occurred.emit("未找到音频文件")
            return []

        # 初始化计时器
        self.start_time = time.time()

        # 动态导入 Shazam（避免在模块顶层导入）
        from shazamio import Shazam

        shazam = Shazam()
        results: list[dict] = []

        # 处理每个文件
        for idx, file_path in enumerate(audio_files, start=1):
            try:
                # 调用识别函数
                result = await recognize_and_rename_file(
                    file_path=file_path,
                    shazam=shazam,
                    modify=False,  # 仅预览，不实际修改
                    delay=10,
                    nbr_retry=3,
                    trace=False,
                    output_dir=None,
                    plex_structure=False,
                    copy_to=self.copy_dir,
                    tag_only=self.tag_only,
                )
                # 标记是否可应用（无错误）
                result["apply"] = "error" not in result
            except Exception as exc:
                # 捕获异常并构造错误结果
                result = {
                    "file_path": file_path,
                    "new_file_path": str(exc),
                    "apply": False,
                    "error": str(exc),
                    "search_results": [],
                }

            results.append(result)

            # 发射单个文件处理完成信号
            self.file_processed.emit(result)

            # 计算剩余时间
            elapsed = time.time() - self.start_time
            remaining = int(elapsed / idx * (total_files - idx))

            # 发射进度更新信号
            self.progress_updated.emit(idx, total_files, remaining)

        return results
