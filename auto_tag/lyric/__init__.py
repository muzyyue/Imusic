# auto_tag/lyric/__init__.py
"""
歌词处理模块
提供歌词的获取、嵌入、提取和格式转换功能
"""

from .manager import LyricManager
from .provider import (
    LyricProvider,
    PROVIDERS,
    get_provider,
    get_provider_api,
    list_providers
)

__all__ = [
    'LyricManager',
    'LyricProvider',
    'PROVIDERS',
    'get_provider',
    'get_provider_api',
    'list_providers'
]
