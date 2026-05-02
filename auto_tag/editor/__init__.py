# -*- coding: utf-8 -*-
"""
音频编辑器模块

提供音频裁剪、音量标准化、格式转换增强等编辑功能。
基于 FFmpeg 实现，支持多种编辑模式和预设。

主要组件：
- AudioEditor: 核心编辑器类
- EditorConfig: 编辑配置
- PresetManager: 预设管理器
- EditorWorker: 异步工作线程

使用示例：
>>> from auto_tag.editor import AudioEditor, EditorConfig
>>> editor = AudioEditor()
>>> result = editor.trim_audio("input.mp3", "output.mp3", start_time=10.0)
"""

from auto_tag.editor.audio_editor import AudioEditor
from auto_tag.editor.config import (
    EditorConfig,
    NormalizeConfig,
    TrimConfig,
    TrimMode,
)
from auto_tag.editor.presets import PresetManager

__all__ = [
    "AudioEditor",
    "EditorConfig",
    "NormalizeConfig",
    "PresetManager",
    "TrimConfig",
    "TrimMode",
]
