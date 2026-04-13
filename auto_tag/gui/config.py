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

    该类负责管理应用程序的配置信息，包括语言和主题设置。
    配置以 JSON 格式存储在用户主目录下。

    Attributes:
        language (str): 语言代码，默认为 "en"
        theme (str): 主题设置，可选值为 "light"、"dark"、"auto"，默认为 "auto"

    Example:
        >>> config = AppConfig()
        >>> config.language
        'en'
        >>> config.set_language('zh')
        >>> config.language
        'zh'
    """

    # 主题可选值类型
    ThemeType = Literal["light", "dark", "auto"]

    # 默认配置
    DEFAULT_LANGUAGE: str = "en"
    DEFAULT_THEME: str = "auto"

    # 有效主题值
    VALID_THEMES: tuple[str, ...] = ("light", "dark", "auto")

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

            # 验证主题值是否有效
            if self._theme not in self.VALID_THEMES:
                self._theme = self.DEFAULT_THEME

        except (json.JSONDecodeError, IOError, KeyError):
            # 配置文件损坏或读取失败，使用默认值
            self._language = self.DEFAULT_LANGUAGE
            self._theme = self.DEFAULT_THEME

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
                "theme": self._theme
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

    def __repr__(self) -> str:
        """
        返回配置对象的字符串表示

        Returns:
            str: 配置对象的字符串表示
        """
        return (
            f"AppConfig(language={self._language!r}, "
            f"theme={self._theme!r}, "
            f"config_file={str(self._config_file)!r})"
        )


# 全局单例实例
config: AppConfig = AppConfig()
