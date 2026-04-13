# -*- coding: utf-8 -*-
"""
auto_tag.gui.i18n.translator 模块

提供国际化翻译功能的核心实现。

主要组件：
- Translator: 翻译器类，负责加载和管理语言翻译
- translator: 全局翻译器单例
- tr(): 便捷翻译函数

使用示例：
    from auto_tag.gui.i18n import tr

    # 获取翻译文本
    text = tr('app_title')  # 返回 "MP3 Shazam Auto Tag" 或 "MP3 Shazam 自动标签"

    # 带格式化参数
    progress = tr('progress_format', done=5, total=10, remaining=30)
    # 返回 "5/10，剩余 30 秒"
"""

import json
import pkgutil
from typing import Dict, Optional


class Translator:
    """
    翻译器类，负责加载和管理多语言翻译。

    Attributes:
        current_language (str): 当前语言代码，如 'en', 'zh'
        _translations (Dict[str, str]): 当前语言的翻译字典

    Example:
        >>> t = Translator()
        >>> t.load_language('zh')
        >>> t.get('app_title')
        'MP3 Shazam 自动标签'
    """

    __slots__ = ('_current_language', '_translations')

    def __init__(self, default_language: str = 'zh') -> None:
        """
        初始化翻译器，加载默认语言。

        Args:
            default_language: 默认语言代码，默认为 'zh'
        """
        self._current_language: str = ''
        self._translations: Dict[str, str] = {}
        self.load_language(default_language)

    @property
    def current_language(self) -> str:
        """
        获取当前语言代码。

        Returns:
            str: 当前语言代码
        """
        return self._current_language

    def load_language(self, lang_code: str) -> bool:
        """
        加载指定语言的翻译文件。

        尝试从 locales 目录加载对应的 JSON 翻译文件。
        如果加载失败，保持原有翻译不变。

        Args:
            lang_code: 语言代码，如 'en', 'zh'

        Returns:
            bool: 加载成功返回 True，失败返回 False

        Example:
            >>> translator.load_language('zh')
            True
        """
        try:
            # 使用 pkgutil.get_data 加载包内资源文件
            # 兼容 Python 3.6+ 和打包后的环境
            data = pkgutil.get_data(
                'auto_tag.gui.i18n.locales',
                f'{lang_code}.json'
            )
            if data is None:
                return False

            # 解码 JSON 数据
            content = data.decode('utf-8')
            self._translations = json.loads(content)
            self._current_language = lang_code
            return True

        except (FileNotFoundError, json.JSONDecodeError, ImportError):
            # 加载失败时保持原有翻译
            return False

    def get(self, key: str, **kwargs) -> str:
        """
        获取翻译文本，支持格式化参数。

        如果翻译键不存在，返回键名本身作为 fallback。
        如果提供了格式化参数，使用 str.format() 进行替换。

        Args:
            key: 翻译键名
            **kwargs: 格式化参数，用于替换文本中的占位符

        Returns:
            str: 翻译后的文本，或键名本身（如果不存在）

        Example:
            >>> translator.get('app_title')
            'MP3 Shazam Auto Tag'

            >>> translator.get('progress_format', done=5, total=10, remaining=30)
            '5/10, Remaining 30 s'
        """
        # 获取翻译文本，不存在则返回键名
        text = self._translations.get(key, key)

        # 如果有格式化参数，进行替换
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError):
                # 格式化失败时返回原始文本
                return text

        return text


# 全局翻译器单例
translator = Translator()


def tr(key: str, **kwargs) -> str:
    """
    便捷翻译函数，调用全局翻译器的 get 方法。

    这是一个简化的接口，用于快速获取翻译文本。

    Args:
        key: 翻译键名
        **kwargs: 格式化参数

    Returns:
        str: 翻译后的文本

    Example:
        >>> from auto_tag.gui.i18n import tr
        >>> tr('app_title')
        'MP3 Shazam Auto Tag'
        >>> tr('progress_format', done=5, total=10, remaining=30)
        '5/10, Remaining 30 s'
    """
    return translator.get(key, **kwargs)
