# -*- coding: utf-8 -*-
"""
自定义文件格式管理模块

提供自定义文件格式的定义、验证和管理功能。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CustomFormat:
    """
    自定义文件格式数据类

    Attributes:
        extension (str): 文件扩展名（不含点号，如 "opus"）
        description (str): 格式描述信息
        is_custom (bool): 是否为用户自定义格式（默认 True）

    Example:
        >>> fmt = CustomFormat(extension="opus", description="Opus Audio")
        >>> fmt.extension
        'opus'
    """

    extension: str
    description: str = ""
    is_custom: bool = True

    def __post_init__(self) -> None:
        """初始化后处理，确保扩展名格式正确"""
        self.extension = self.extension.lower().strip().lstrip('.')
        if not self.description:
            self.description = self.extension.upper()


class CustomFormatManager:
    """
    自定义格式管理器

    管理用户自定义的文件格式，提供增删改查功能，
    并包含格式验证逻辑。

    Attributes:
        custom_formats (list[CustomFormat]): 自定义格式列表
        builtin_formats (set[str]): 内置格式集合（不可删除）

    Example:
        >>> manager = CustomFormatManager()
        >>> manager.add_format("opus", "Opus Audio Format")
        >>> manager.get_all_extensions()
        ['mp3', 'flac', ..., 'opus']
    """

    # 内置格式（预设格式）
    BUILTIN_FORMATS: set[str] = {
        # 音频格式
        "mp3", "flac", "aac", "ogg", "wav", "m4a",
        # 视频格式
        "mp4", "mkv", "avi", "mov", "wmv", "webm"
    }

    # 扩展名正则表达式（只允许字母数字）
    EXTENSION_PATTERN: re.Pattern = re.compile(r'^[a-zA-Z0-9]{1,10}$')

    def __init__(self) -> None:
        """初始化格式管理器"""
        self.custom_formats: list[CustomFormat] = []

    def add_format(self, extension: str, description: str = "") -> tuple[bool, str]:
        """
        添加新的自定义格式

        Args:
            extension (str): 文件扩展名（如 "opus"）
            description (str): 格式描述（可选）

        Returns:
            tuple[bool, str]: (是否成功, 错误消息)

        Example:
            >>> success, error = manager.add_format("opus", "Opus Audio")
            >>> if not success:
            ...     print(error)
        """
        # 验证扩展名格式
        is_valid, error_msg = self._validate_extension(extension)
        if not is_valid:
            return False, error_msg

        # 标准化扩展名
        normalized_ext = extension.lower().strip().lstrip('.')

        # 检查是否为内置格式
        if normalized_ext in self.BUILTIN_FORMATS:
            return False, f"'{normalized_ext}' 是内置格式，无需重复添加"

        # 检查是否已存在
        if self._format_exists(normalized_ext):
            return False, f"格式 '{normalized_ext}' 已存在"

        # 创建并添加格式
        custom_format = CustomFormat(
            extension=normalized_ext,
            description=description or normalized_ext.upper()
        )
        self.custom_formats.append(custom_format)

        return True, ""

    def remove_format(self, extension: str) -> tuple[bool, str]:
        """
        删除自定义格式

        Args:
            extension (str): 要删除的扩展名

        Returns:
            tuple[bool, str]: (是否成功, 错误消息)
        """
        normalized_ext = extension.lower().strip().lstrip('.')

        # 不允许删除内置格式
        if normalized_ext in self.BUILTIN_FORMATS:
            return False, f"无法删除内置格式 '{normalized_ext}'"

        # 查找并删除
        for i, fmt in enumerate(self.custom_formats):
            if fmt.extension == normalized_ext:
                del self.custom_formats[i]
                return True, ""

        return False, f"未找到格式 '{normalized_ext}'"

    def update_format(self, extension: str, new_description: str) -> tuple[bool, str]:
        """
        更新格式的描述信息

        Args:
            extension (str): 扩展名
            new_description (str): 新的描述

        Returns:
            tuple[bool, str]: (是否成功, 错误消息)
        """
        normalized_ext = extension.lower().strip().lstrip('.')

        for fmt in self.custom_formats:
            if fmt.extension == normalized_ext:
                fmt.description = new_description
                return True, ""

        return False, f"未找到格式 '{normalized_ext}'"

    def get_all_extensions(self) -> list[str]:
        """
        获取所有支持的格式扩展名（包括内置和自定义）

        Returns:
            list[str]: 所有扩展名列表
        """
        all_formats = list(self.BUILTIN_FORMATS)
        all_formats.extend(fmt.extension for fmt in self.custom_formats)
        return sorted(all_formats)

    def get_custom_formats(self) -> list[CustomFormat]:
        """
        获取所有自定义格式

        Returns:
            list[CustomFormat]: 自定义格式列表
        """
        return self.custom_formats.copy()

    def get_builtin_formats(self) -> list[str]:
        """
        获取所有内置格式

        Returns:
            list[str]: 内置格式列表
        """
        return sorted(list(self.BUILTIN_FORMATS))

    def clear_custom_formats(self) -> None:
        """清空所有自定义格式"""
        self.custom_formats.clear()

    def _format_exists(self, extension: str) -> bool:
        """
        检查格式是否已存在（仅在自定义格式中查找）

        Args:
            extension (str): 要检查的扩展名

        Returns:
            bool: 是否存在
        """
        return any(fmt.extension == extension for fmt in self.custom_formats)

    @classmethod
    def _validate_extension(cls, extension: str) -> tuple[bool, str]:
        """
        验证扩展名是否符合规范

        验证规则：
        - 不能为空
        - 只能包含字母和数字
        - 长度限制为 1-10 个字符

        Args:
            extension (str): 待验证的扩展名

        Returns:
            tuple[bool, str]: (是否有效, 错误消息)
        """
        if not extension or not extension.strip():
            return False, "扩展名不能为空"

        normalized = extension.strip().lstrip('.')

        # 检查长度
        if len(normalized) < 1:
            return False, "扩展名不能为空"
        if len(normalized) > 10:
            return False, "扩展名长度不能超过 10 个字符"

        # 检查字符
        if not cls.EXTENSION_PATTERN.match(normalized):
            return False, "扩展名只能包含字母和数字"

        return True, ""

    @classmethod
    def is_builtin_format(cls, extension: str) -> bool:
        """
        检查是否为内置格式

        Args:
            extension (str): 扩展名

        Returns:
            bool: 是否为内置格式
        """
        return extension.lower().strip().lstrip('.') in cls.BUILTIN_FORMATS

    def to_dict_list(self) -> list[dict]:
        """
        将自定义格式转换为字典列表（用于序列化）

        Returns:
            list[dict]: 字典列表
        """
        return [
            {
                "extension": fmt.extension,
                "description": fmt.description,
                "is_custom": fmt.is_custom
            }
            for fmt in self.custom_formats
        ]

    @classmethod
    def from_dict_list(cls, data: list[dict]) -> CustomFormatManager:
        """
        从字典列表创建格式管理器（用于反序列化）

        Args:
            data (list[dict]): 字典列表

        Returns:
            CustomFormatManager: 格式管理器实例
        """
        manager = cls()
        for item in data:
            try:
                ext = item.get("extension", "")
                desc = item.get("description", "")
                manager.add_format(ext, desc)
            except Exception:
                continue
        return manager
