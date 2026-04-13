# -*- coding: utf-8 -*-
"""
音频转换工作线程模块

该模块提供基于 QThread 的音频转换工作线程，用于在后台执行音频文件转换任务，
并通过信号机制与主线程通信，实现进度更新和结果传递。

@module converter_worker
@author Backend Architect
@version 1.0.0
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from PySide6.QtCore import QThread, Signal

from auto_tag.converter.config import ConverterConfig
from auto_tag.converter.converter import AudioConverter

if TYPE_CHECKING:
    pass

# 配置日志记录器
logger = logging.getLogger(__name__)


class ConverterWorker(QThread):
    """
    音频转换工作线程类

    该类继承自 QThread，用于在后台线程中执行音频文件转换任务。
    通过信号机制向主线程报告进度和结果，避免阻塞 UI 线程。

    Attributes:
        progress_updated (Signal): 进度更新信号，参数为 (当前索引, 总数, 当前文件名)
        file_converted (Signal): 单文件转换完成信号，参数为 (文件路径, 是否成功, 错误信息)
        finished_all (Signal): 所有文件转换完成信号，参数为结果列表
        error_occurred (Signal): 错误发生信号，参数为错误消息字符串

    Example:
        >>> from auto_tag.converter.config import ConverterConfig
        >>> config = ConverterConfig()
        >>> worker = ConverterWorker(
        ...     files=["/path/to/file1.mp4", "/path/to/file2.avi"],
        ...     output_dir="/path/to/output",
        ...     config=config
        ... )
        >>> worker.progress_updated.connect(on_progress)
        >>> worker.file_converted.connect(on_file_done)
        >>> worker.finished_all.connect(on_finished)
        >>> worker.start()
    """

    # 信号定义
    progress_updated = Signal(int, int, str)  # 当前索引, 总数, 当前文件名
    file_converted = Signal(str, bool, str)  # 文件路径, 是否成功, 错误信息
    finished_all = Signal(list)  # 所有结果列表
    error_occurred = Signal(str)  # 错误消息

    def __init__(
        self,
        files: list[str],
        output_dir: str,
        config: ConverterConfig,
        parent=None,
    ) -> None:
        """
        初始化转换工作线程

        Args:
            files: 要转换的文件路径列表
            output_dir: 输出目录路径
            config: 转换配置对象
            parent: 父对象，用于 Qt 对象树管理
        """
        super().__init__(parent)
        self._files = files
        self._output_dir = output_dir
        self._config = config
        self._is_stopped = False
        self._converter: AudioConverter | None = None

    def run(self) -> None:
        """
        重写 QThread.run 方法，执行转换任务

        该方法在后台线程中执行，遍历文件列表进行转换，
        并发射进度信号通知主线程。

        Note:
            该方法由 Qt 框架自动调用，不应手动调用。
            使用 start() 方法启动线程。
        """
        try:
            # 检查文件列表是否为空
            if not self._files:
                self.error_occurred.emit("文件列表为空")
                return

            # 检查输出目录是否存在，不存在则创建
            if not os.path.exists(self._output_dir):
                try:
                    os.makedirs(self._output_dir, exist_ok=True)
                    logger.info(f"创建输出目录: {self._output_dir}")
                except OSError as e:
                    error_msg = f"创建输出目录失败: {self._output_dir}, 错误: {str(e)}"
                    logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    return

            # 创建 AudioConverter 实例
            try:
                self._converter = AudioConverter()
            except RuntimeError as e:
                error_msg = f"初始化音频转换器失败: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return

            # 执行转换
            results = self._convert_files()

            # 发射完成信号
            self.finished_all.emit(results)

        except Exception as e:
            error_msg = f"转换过程发生错误: {str(e)}"
            logger.exception(error_msg)
            self.error_occurred.emit(error_msg)

    def stop(self) -> None:
        """
        停止转换操作

        设置停止标志，线程会在当前文件转换完成后退出。
        """
        logger.info("收到停止信号，将在当前文件转换完成后退出")
        self._is_stopped = True

    def _convert_files(self) -> list[dict]:
        """
        转换所有文件

        遍历文件列表，对每个文件调用 convert_file() 进行转换，
        并发射进度信号通知主线程。

        Returns:
            list[dict]: 所有文件的转换结果列表，每个元素为包含以下键的字典：
                - file_path: 原始文件路径
                - output_path: 输出文件路径
                - success: 是否成功
                - error: 错误信息（可选）

        Note:
            该方法会检查 _is_stopped 标志，如果为 True 则提前退出。
        """
        total_files = len(self._files)
        results: list[dict] = []

        logger.info(f"开始转换 {total_files} 个文件")

        # 遍历文件列表进行转换
        for index, input_path in enumerate(self._files, start=1):
            # 检查是否被停止
            if self._is_stopped:
                logger.info("转换已取消")
                break

            # 检查文件是否存在
            if not os.path.exists(input_path):
                error_msg = f"文件不存在: {input_path}"
                logger.error(error_msg)
                result = {
                    "file_path": input_path,
                    "output_path": "",
                    "success": False,
                    "error": error_msg,
                }
                results.append(result)
                self.file_converted.emit(input_path, False, error_msg)
                continue

            # 生成输出文件路径
            input_filename = os.path.basename(input_path)
            input_name = os.path.splitext(input_filename)[0]
            output_extension = self._config.get_output_extension()
            output_path = os.path.join(self._output_dir, f"{input_name}{output_extension}")

            # 发射进度更新信号
            self.progress_updated.emit(index, total_files, input_filename)

            # 执行转换
            try:
                logger.info(f"转换文件 {index}/{total_files}: {input_path}")

                # 调用 AudioConverter.convert_file() 进行转换
                success = self._converter.convert_file(
                    input_path=input_path,
                    output_path=output_path,
                    config=self._config,
                )

                if success:
                    logger.info(f"转换成功: {input_path} -> {output_path}")
                    result = {
                        "file_path": input_path,
                        "output_path": output_path,
                        "success": True,
                        "error": None,
                    }
                    self.file_converted.emit(input_path, True, "")
                else:
                    error_msg = f"转换失败: {input_path}"
                    logger.error(error_msg)
                    result = {
                        "file_path": input_path,
                        "output_path": output_path,
                        "success": False,
                        "error": error_msg,
                    }
                    self.file_converted.emit(input_path, False, error_msg)

            except Exception as e:
                error_msg = f"转换文件时发生异常: {input_path}, 错误: {str(e)}"
                logger.exception(error_msg)
                result = {
                    "file_path": input_path,
                    "output_path": output_path,
                    "success": False,
                    "error": str(e),
                }
                self.file_converted.emit(input_path, False, str(e))

            results.append(result)

        # 统计转换结果
        success_count = sum(1 for r in results if r["success"])
        logger.info(f"转换完成: 成功 {success_count}/{len(results)}")

        return results
