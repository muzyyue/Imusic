# -*- coding: utf-8 -*-
"""
配置管理模块

该模块提供应用程序配置的加载、保存和管理功能。
配置文件存储在用户主目录下的 .mp3shazamautotag/config.json 文件中。

功能：
    - 语言设置管理
    - 主题设置管理
    - 配置持久化存储

使用示例：
    from auto_tag.gui.config import config

    # 获取当前语言
    print(config.language)

    # 设置语言
    config.set_language("zh")

    # 设置主题
    config.set_theme("dark")
"""

import json
import os
from pathlib import Path
from typing import Literal


class AppConfig:
    """
    应用程序配置管理类

    该类负责管理应用程序的配置信息，包括语言、主题和转换设置。
    配置以 JSON 格式存储在用户主目录下。

    Attributes:
        language (str): 语言代码，默认为 "zh"
        theme (str): 主题设置，可选值为 "light"、"dark"、"auto"，默认为 "auto"
        output_format (str): 默认输出格式，默认为 "mp3"
        quality_preset (str): 质量预设，默认为 "high"

    Example:
        >>> config = AppConfig()
        >>> config.language
        'zh'
        >>> config.set_language('en')
        >>> config.language
        'en'
    """

    # 主题可选值类型
    ThemeType = Literal["light", "dark", "auto"]

    # 默认配置
    DEFAULT_LANGUAGE: str = "zh"
    DEFAULT_THEME: str = "auto"
    DEFAULT_OUTPUT_FORMAT: str = "mp3"
    DEFAULT_QUALITY_PRESET: str = "high"

    # 有效主题值
    VALID_THEMES: tuple[str, ...] = ("light", "dark", "auto")
    
    # 有效输出格式
    VALID_OUTPUT_FORMATS: tuple[str, ...] = (
        "mp3", "flac", "aac", "ogg", "wav", "m4a"
    )
    
    # 有效质量预设
    VALID_QUALITY_PRESETS: tuple[str, ...] = (
        "low", "medium", "high", "lossless"
    )

    def __init__(self) -> None:
        """
        初始化配置管理器

        尝试从配置文件加载配置，如果文件不存在或加载失败，则使用默认值。
        配置文件路径为 ~/.mp3shazamautotag/config.json
        """
        # 获取配置文件路径
        self._config_dir: Path = Path.home() / ".mp3shazamautotag"
        self._config_file: Path = self._config_dir / "config.json"

        # 初始化配置属性
        self._language: str = self.DEFAULT_LANGUAGE
        self._theme: str = self.DEFAULT_THEME
        self._output_format: str = self.DEFAULT_OUTPUT_FORMAT
        self._quality_preset: str = self.DEFAULT_QUALITY_PRESET

        # 加载配置文件
        self._load_config()

    def _load_config(self) -> None:
        """
        从配置文件加载配置

        如果配置文件存在且格式正确，则加载配置；
        否则保持默认值。加载失败时不会抛出异常。
        """
        try:
            # 检查配置文件是否存在
            if not self._config_file.exists():
                return

            # 读取并解析 JSON 文件
            with open(self._config_file, "r", encoding="utf-8") as f:
                config_data: dict = json.load(f)

            # 更新配置属性（使用 get 方法提供默认值）
            self._language = config_data.get("language", self.DEFAULT_LANGUAGE)
            self._theme = config_data.get("theme", self.DEFAULT_THEME)
            self._output_format = config_data.get(
                "output_format", self.DEFAULT_OUTPUT_FORMAT
            )
            self._quality_preset = config_data.get(
                "quality_preset", self.DEFAULT_QUALITY_PRESET
            )

            # 验证主题值是否有效
            if self._theme not in self.VALID_THEMES:
                self._theme = self.DEFAULT_THEME

            # 验证输出格式是否有效
            if self._output_format not in self.VALID_OUTPUT_FORMATS:
                self._output_format = self.DEFAULT_OUTPUT_FORMAT

            # 验证质量预设是否有效
            if self._quality_preset not in self.VALID_QUALITY_PRESETS:
                self._quality_preset = self.DEFAULT_QUALITY_PRESET

        except (json.JSONDecodeError, IOError, KeyError):
            # 配置文件损坏或读取失败，使用默认值
            self._language = self.DEFAULT_LANGUAGE
            self._theme = self.DEFAULT_THEME
            self._output_format = self.DEFAULT_OUTPUT_FORMAT
            self._quality_preset = self.DEFAULT_QUALITY_PRESET

    def save(self) -> None:
        """
        保存配置到文件

        将当前配置以 JSON 格式保存到配置文件中。
        如果配置目录不存在，会自动创建。
        """
        try:
            # 确保配置目录存在
            self._config_dir.mkdir(parents=True, exist_ok=True)

            # 准备配置数据
            config_data: dict = {
                "language": self._language,
                "theme": self._theme,
                "output_format": self._output_format,
                "quality_preset": self._quality_preset
            }

            # 写入配置文件
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)

        except IOError as e:
            # 写入失败时打印错误信息（实际项目中应该使用日志）
            print(f"保存配置文件失败: {e}")

    @property
    def language(self) -> str:
        """
        获取当前语言设置

        Returns:
            str: 当前语言代码
        """
        return self._language

    @property
    def theme(self) -> str:
        """
        获取当前主题设置

        Returns:
            str: 当前主题名称
        """
        return self._theme

    def set_language(self, lang: str) -> None:
        """
        设置语言并保存

        Args:
            lang (str): 语言代码，如 "en"、"zh"、"ja" 等

        Example:
            >>> config.set_language("zh")
        """
        self._language = lang
        self.save()

    def set_theme(self, theme: str) -> None:
        """
        设置主题并保存

        Args:
            theme (str): 主题名称，必须是 "light"、"dark" 或 "auto" 之一

        Raises:
            ValueError: 当主题值无效时抛出

        Example:
            >>> config.set_theme("dark")
        """
        # 验证主题值
        if theme not in self.VALID_THEMES:
            raise ValueError(
                f"无效的主题值: {theme}。"
                f"有效值为: {', '.join(self.VALID_THEMES)}"
            )

        self._theme = theme
        self.save()

    @property
    def output_format(self) -> str:
        """
        获取当前输出格式设置

        Returns:
            str: 当前输出格式名称
        """
        return self._output_format

    @property
    def quality_preset(self) -> str:
        """
        获取当前质量预设设置

        Returns:
            str: 当前质量预设名称
        """
        return self._quality_preset

    def set_output_format(self, output_format: str) -> None:
        """
        设置输出格式并保存

        Args:
            output_format (str): 输出格式名称，必须是 "mp3"、"flac"、"aac"、
                                "ogg"、"wav" 或 "m4a" 之一

        Raises:
            ValueError: 当输出格式值无效时抛出

        Example:
            >>> config.set_output_format("flac")
        """
        # 验证输出格式值
        if output_format not in self.VALID_OUTPUT_FORMATS:
            raise ValueError(
                f"无效的输出格式: {output_format}。"
                f"有效值为: {', '.join(self.VALID_OUTPUT_FORMATS)}"
            )

        self._output_format = output_format
        self.save()

    def set_quality_preset(self, quality_preset: str) -> None:
        """
        设置质量预设并保存

        Args:
            quality_preset (str): 质量预设名称，必须是 "low"、"medium"、
                                 "high" 或 "lossless" 之一

        Raises:
            ValueError: 当质量预设值无效时抛出

        Example:
            >>> config.set_quality_preset("high")
        """
        # 验证质量预设值
        if quality_preset not in self.VALID_QUALITY_PRESETS:
            raise ValueError(
                f"无效的质量预设: {quality_preset}。"
                f"有效值为: {', '.join(self.VALID_QUALITY_PRESETS)}"
            )

        self._quality_preset = quality_preset
        self.save()

    def __repr__(self) -> str:
        """
        返回配置对象的字符串表示

        Returns:
            str: 配置对象的字符串表示
        """
        return (
            f"AppConfig(language={self._language!r}, "
            f"theme={self._theme!r}, "
            f"output_format={self._output_format!r}, "
            f"quality_preset={self._quality_preset!r}, "
            f"config_file={str(self._config_file)!r})"
        )


# 全局单例实例
config: AppConfig = AppConfig()
