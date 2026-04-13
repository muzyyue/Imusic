# -*- coding: utf-8 -*-
"""
音频转换模块

提供音频格式转换和元数据管理功能。

模块组件：
    - AudioConverter: 音频格式转换核心类
    - MetadataManager: 元数据管理器
    - ConverterConfig: 转换配置类
    - ConverterWorker: 异步转换工作线程
"""

from auto_tag.converter.config import ConverterConfig
from auto_tag.converter.converter import AudioConverter
from auto_tag.converter.metadata_manager import MetadataManager

__all__ = [
    "AudioConverter",
    "MetadataManager",
    "ConverterConfig",
]
