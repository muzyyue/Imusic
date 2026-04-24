# -*- coding: utf-8 -*-
"""
音频转换器模块

提供音频和视频文件的格式转换功能，支持多种输入输出格式。
使用 ffmpeg-python 库进行底层转换操作。
"""

import logging
import os
import re
from pathlib import Path
from typing import Callable

import ffmpeg

from auto_tag.converter.config import ConverterConfig, OutputFormat

# 配置日志记录器
logger = logging.getLogger(__name__)


class AudioConverter:
    """
    音频转换器类
    
    支持多种音频和视频格式的转换，提供格式检测、单文件转换和批量转换功能。
    
    Attributes:
        SUPPORTED_INPUT_FORMATS: 支持的输入格式集合
        SUPPORTED_OUTPUT_FORMATS: 支持的输出格式集合
    
    Example:
        >>> converter = AudioConverter()
        >>> format_name = converter.detect_format("song.mp3")
        >>> config = ConverterConfig()
        >>> success = converter.convert_file("input.mp3", "output.flac", config)
    """
    
    # 支持的输入格式（音频 + 视频）
    SUPPORTED_INPUT_FORMATS = {
        # 音频格式
        "mp3", "flac", "aac", "ogg", "wav", "m4a",
        # 视频格式
        "mp4", "mkv", "avi", "mov", "wmv", "webm"
    }
    
    # 支持的输出格式（仅音频）
    SUPPORTED_OUTPUT_FORMATS = {
        "mp3", "flac", "aac", "ogg", "wav", "m4a"
    }
    
    def __init__(self):
        """
        初始化音频转换器
        
        检查 FFmpeg 是否可用。
        """
        self._check_ffmpeg_available()
    
    def _check_ffmpeg_available(self) -> None:
        """
        检查 FFmpeg 是否已安装并可用
        
        Raises:
            RuntimeError: 如果 FFmpeg 未安装或不可用
        """
        try:
            # 尝试运行 ffmpeg -version 来检查是否可用
            ffmpeg.run(ffmpeg.probe("dummy"), quiet=True, overwrite_output=True)
        except ffmpeg.Error:
            # 这是预期的，因为 "dummy" 文件不存在
            # 但如果 ffmpeg 可执行文件不存在，会抛出不同的异常
            pass
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg 未安装或不在系统 PATH 中。请安装 FFmpeg 后重试。\n"
                "Windows: 从 https://ffmpeg.org/download.html 下载并添加到 PATH\n"
                "Linux: sudo apt install ffmpeg\n"
                "macOS: brew install ffmpeg"
            )
    
    def detect_format(self, file_path: str) -> str | None:
        """
        检测文件的音频/视频格式
        
        使用 FFprobe 检测文件的真实格式，而不是仅依赖文件扩展名。
        
        Args:
            file_path: 文件路径
        
        Returns:
            str | None: 检测到的格式名称（如 'mp3', 'mp4'），如果检测失败返回 None
        
        Example:
            >>> converter = AudioConverter()
            >>> format_name = converter.detect_format("song.mp3")
            >>> print(format_name)  # 输出: 'mp3'
        """
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None
        
        try:
            # 使用 ffprobe 获取文件信息
            probe = ffmpeg.probe(file_path)
            
            # 获取格式名称
            format_name = probe.get('format', {}).get('format_name', '')
            
            if not format_name:
                logger.warning(f"无法获取文件格式: {file_path}")
                return None
            
            # FFprobe 可能返回多个格式名称（如 'mov,mp4,m4a,3gp,3g2,mj2'）
            # 取第一个作为主要格式
            primary_format = format_name.split(',')[0].lower()
            
            logger.debug(f"检测到文件格式: {file_path} -> {primary_format}")
            return primary_format
            
        except ffmpeg.Error as e:
            logger.error(f"FFprobe 检测失败: {file_path}, 错误: {e.stderr.decode() if e.stderr else str(e)}")
            return None
        except Exception as e:
            logger.error(f"检测文件格式时发生未知错误: {file_path}, 错误: {str(e)}")
            return None
    
    def get_source_bitrate(self, file_path: str) -> int | None:
        """
        获取源文件的音频码率（kbps）
        
        Args:
            file_path: 文件路径
        
        Returns:
            int | None: 码率（kbps），如果无法获取返回 None
        
        Example:
            >>> converter = AudioConverter()
            >>> bitrate = converter.get_source_bitrate("song.mp3")
            >>> print(bitrate)  # 输出: 128 或 320 等
        """
        try:
            probe = ffmpeg.probe(file_path)
            
            # 从音频流中获取码率
            streams = probe.get('streams', [])
            for stream in streams:
                if stream.get('codec_type') == 'audio':
                    bitrate = stream.get('bit_rate')
                    if bitrate:
                        # 转换为 kbps
                        return int(bitrate) // 1000
            
            # 如果流中没有码率，尝试从 format 获取
            format_info = probe.get('format', {})
            bitrate = format_info.get('bit_rate')
            if bitrate:
                return int(bitrate) // 1000
            
            return None
            
        except Exception as e:
            logger.debug(f"获取源文件码率失败: {file_path}, 错误: {str(e)}")
            return None
    
    def convert_file(
        self,
        input_path: str,
        output_path: str,
        config: ConverterConfig,
        progress_callback: Callable[[float], None] | None = None
    ) -> bool:
        """
        转换单个音频/视频文件
        
        将输入文件转换为指定的输出格式，支持进度回调。
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            config: 转换配置对象
            progress_callback: 进度回调函数，接收 0.0-1.0 之间的进度值
        
        Returns:
            bool: 转换成功返回 True，失败返回 False
        
        Example:
            >>> converter = AudioConverter()
            >>> config = ConverterConfig()
            >>> success = converter.convert_file(
            ...     "input.mp4",
            ...     "output.mp3",
            ...     config,
            ...     lambda p: print(f"进度: {p*100:.1f}%")
            ... )
        """
        # 1. 检查输入文件是否存在
        if not os.path.exists(input_path):
            logger.error(f"输入文件不存在: {input_path}")
            return False
        
        # 2. 检测输入格式
        input_format = self.detect_format(input_path)
        if not input_format:
            logger.error(f"无法检测输入文件格式: {input_path}")
            return False
        
        # 3. 检查输入格式是否支持
        if input_format not in self.SUPPORTED_INPUT_FORMATS:
            logger.error(f"不支持的输入格式: {input_format} (文件: {input_path})")
            return False
        
        # 4. 检查输出格式是否支持
        output_format = config.output_format.format.value
        if output_format not in self.SUPPORTED_OUTPUT_FORMATS:
            logger.error(f"不支持的输出格式: {output_format}")
            return False
        
        # 5. 检查输出目录是否存在，不存在则创建
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"创建输出目录: {output_dir}")
            except OSError as e:
                logger.error(f"创建输出目录失败: {output_dir}, 错误: {str(e)}")
                return False
        
        # 6. 检查输出文件是否已存在
        if os.path.exists(output_path) and not config.overwrite_existing:
            logger.error(f"输出文件已存在且未启用覆盖: {output_path}")
            return False
        
        try:
            logger.info(f"开始转换: {input_path} -> {output_path}")
            
            # 保存原始码率，用于后续恢复
            original_bitrate = config.output_format.bitrate
            smart_bitrate_applied = False
            
            # 智能码率检测：如果启用 smart_bitrate，根据源文件码率调整
            if config.output_format.smart_bitrate and config.output_format.bitrate:
                source_bitrate = self.get_source_bitrate(input_path)
                if source_bitrate:
                    # 计算自适应码率：不超过源文件码率的 1.2 倍
                    adaptive_bitrate = min(config.output_format.bitrate, int(source_bitrate * 1.2))
                    # 确保码率不低于最低标准（64kbps）
                    adaptive_bitrate = max(64, adaptive_bitrate)
                    logger.info(f"智能码率调整: {source_bitrate}kbps -> {adaptive_bitrate}kbps (上限: {config.output_format.bitrate}kbps)")
                    
                    # 临时修改配置中的码率
                    config.output_format.bitrate = adaptive_bitrate
                    smart_bitrate_applied = True
            
            # 构建 FFmpeg 输入流
            input_stream = ffmpeg.input(input_path)
            
            # 获取 FFmpeg 参数
            ffmpeg_args = config.get_ffmpeg_args()
            
            # 构建输出流
            # 对于视频文件，只提取音频（-vn 禁用视频）
            output_stream = input_stream.audio.output(
                output_path,
                **self._parse_ffmpeg_args(ffmpeg_args)
            )
            
            # 如果需要进度回调，使用异步执行
            if progress_callback:
                success = self._run_with_progress(
                    output_stream,
                    input_path,
                    progress_callback
                )
            else:
                # 同步执行
                output_stream.run(overwrite_output=True)
                success = True
            
            # 恢复原始码率配置（如果使用了智能码率）
            if smart_bitrate_applied and original_bitrate is not None:
                config.output_format.bitrate = original_bitrate
            
            if success:
                logger.info(f"转换成功: {output_path}")
            else:
                logger.error(f"转换失败: {input_path}")
            
            return success
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpeg 转换错误: {input_path}, 错误: {error_msg}")
            return False
        except Exception as e:
            logger.error(f"转换过程中发生未知错误: {input_path}, 错误: {str(e)}")
            return False
    
    def convert_batch(
        self,
        files: list[str],
        output_dir: str,
        config: ConverterConfig,
        progress_callback: Callable[[int, int, str], None] | None = None
    ) -> dict[str, bool]:
        """
        批量转换音频/视频文件
        
        将多个文件转换为指定格式，支持进度回调。
        
        Args:
            files: 输入文件路径列表
            output_dir: 输出目录路径
            config: 转换配置对象
            progress_callback: 进度回调函数，参数为 (当前索引, 总数, 当前文件路径)
        
        Returns:
            dict[str, bool]: 转换结果字典，键为输入文件路径，值为转换是否成功
        
        Example:
            >>> converter = AudioConverter()
            >>> config = ConverterConfig()
            >>> files = ["song1.mp4", "song2.avi"]
            >>> results = converter.convert_batch(
            ...     files,
            ...     "output/",
            ...     config,
            ...     lambda i, total, f: print(f"处理 {i}/{total}: {f}")
            ... )
        """
        results: dict[str, bool] = {}
        total_files = len(files)
        
        # 检查输出目录是否存在，不存在则创建
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"创建输出目录: {output_dir}")
            except OSError as e:
                logger.error(f"创建输出目录失败: {output_dir}, 错误: {str(e)}")
                # 所有文件都标记为失败
                for file_path in files:
                    results[file_path] = False
                return results
        
        # 遍历文件列表进行转换
        for index, input_path in enumerate(files, start=1):
            # 调用进度回调
            if progress_callback:
                progress_callback(index, total_files, input_path)
            
            # 生成输出文件路径
            input_filename = os.path.basename(input_path)
            input_name = os.path.splitext(input_filename)[0]
            output_extension = config.get_output_extension()
            output_path = os.path.join(output_dir, f"{input_name}{output_extension}")
            
            # 执行单文件转换
            success = self.convert_file(input_path, output_path, config)
            results[input_path] = success
            
            # 记录转换结果
            if success:
                logger.info(f"批量转换进度: {index}/{total_files} - 成功: {input_path}")
            else:
                logger.warning(f"批量转换进度: {index}/{total_files} - 失败: {input_path}")
        
        # 统计转换结果
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"批量转换完成: 成功 {success_count}/{total_files}")
        
        return results
    
    def _parse_ffmpeg_args(self, args: list[str]) -> dict[str, str]:
        """
        解析 FFmpeg 参数列表为字典格式
        
        将 ['-c:a', 'libmp3lame', '-b:a', '320k'] 转换为 {'c:a': 'libmp3lame', 'b:a': '320k'}
        
        Args:
            args: FFmpeg 参数列表
        
        Returns:
            dict[str, str]: 参数字典
        """
        kwargs = {}
        i = 0
        while i < len(args) - 1:
            if args[i].startswith('-'):
                key = args[i][1:]  # 移除前导 '-'
                value = args[i + 1]
                kwargs[key] = value
                i += 2
            else:
                i += 1
        return kwargs
    
    def _run_with_progress(
        self,
        output_stream,
        input_path: str,
        progress_callback: Callable[[float], None]
    ) -> bool:
        """
        使用进度回调运行 FFmpeg 转换
        
        解析 FFmpeg 的 stderr 输出以获取转换进度。
        
        Args:
            output_stream: FFmpeg 输出流对象
            input_path: 输入文件路径（用于获取时长）
            progress_callback: 进度回调函数
        
        Returns:
            bool: 转换成功返回 True，失败返回 False
        """
        try:
            # 获取输入文件的总时长
            duration = self._get_duration(input_path)
            
            if duration is None:
                # 无法获取时长，直接执行不报告进度
                logger.warning(f"无法获取文件时长，将不报告进度: {input_path}")
                output_stream.run(overwrite_output=True)
                progress_callback(1.0)
                return True
            
            # 异步运行 FFmpeg
            process = output_stream.run_async(pipe_stderr=True, overwrite_output=True)
            
            # 解析 stderr 获取进度
            progress_pattern = re.compile(r'time=(\d+):(\d+):(\d+\.?\d*)')
            
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                
                line_str = line.decode('utf-8', errors='ignore')
                
                # 查找时间进度
                match = progress_pattern.search(line_str)
                if match:
                    hours = float(match.group(1))
                    minutes = float(match.group(2))
                    seconds = float(match.group(3))
                    current_time = hours * 3600 + minutes * 60 + seconds
                    
                    # 计算进度百分比
                    progress = min(current_time / duration, 1.0)
                    progress_callback(progress)
            
            # 等待进程结束
            process.wait()
            
            # 检查返回码
            if process.returncode == 0:
                progress_callback(1.0)
                return True
            else:
                logger.error(f"FFmpeg 进程返回非零退出码: {process.returncode}")
                return False
                
        except Exception as e:
            logger.error(f"执行带进度的转换时发生错误: {str(e)}")
            return False
    
    def _get_duration(self, file_path: str) -> float | None:
        """
        获取音频/视频文件的时长（秒）
        
        Args:
            file_path: 文件路径
        
        Returns:
            float | None: 时长（秒），如果无法获取返回 None
        """
        try:
            probe = ffmpeg.probe(file_path)
            
            # 尝试从 format 中获取时长
            duration = probe.get('format', {}).get('duration')
            if duration:
                return float(duration)
            
            # 尝试从 streams 中获取时长
            streams = probe.get('streams', [])
            for stream in streams:
                if 'duration' in stream:
                    return float(stream['duration'])
            
            return None
            
        except Exception as e:
            logger.debug(f"获取文件时长失败: {file_path}, 错误: {str(e)}")
            return None
