# auto_tag/lyric/provider.py
"""
歌词提供商配置模块
定义支持的歌词提供商及其配置信息
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class LyricProvider:
    """
    歌词提供商配置数据类

    Attributes:
        name: 提供商名称（如 'lrclib'）
        display_name: 显示名称（如 'LRCLib'）
        description: 提供商描述
        api_module: API 模块路径（如 'lrxy.providers.lrclib_api'）
        supports_synced: 是否支持同步歌词
        supports_plain: 是否支持纯文本歌词
    """

    name: str
    display_name: str
    description: str
    api_module: str
    supports_synced: bool = True
    supports_plain: bool = True


# 歌词提供商配置字典
PROVIDERS: dict[str, LyricProvider] = {
    'netease': LyricProvider(
        name='netease',
        display_name='网易云音乐',
        description='网易云音乐歌词提供商，支持同步歌词和翻译',
        api_module='pymusiclibrary.NeteseCloudMusicApi',
        supports_synced=True,
        supports_plain=True
    ),
    'kugou': LyricProvider(
        name='kugou',
        display_name='酷狗音乐',
        description='酷狗音乐歌词提供商，支持同步歌词',
        api_module='pymusiclibrary.KuGouMusicApi',
        supports_synced=True,
        supports_plain=True
    ),
    'lrclib': LyricProvider(
        name='lrclib',
        display_name='LRCLib',
        description='简单可靠的 LRC 歌词提供商，支持同步歌词',
        api_module='lrxy.providers.lrclib_api',
        supports_synced=True,
        supports_plain=True
    ),
    'applemusic': LyricProvider(
        name='applemusic',
        display_name='Apple Music',
        description='Apple Music 歌词提供商，支持逐字歌词',
        api_module='lrxy.providers.applemusic_api',
        supports_synced=True,
        supports_plain=True
    ),
    'musixmatch': LyricProvider(
        name='musixmatch',
        display_name='MusixMatch',
        description='大型歌词数据库，被大多数流媒体服务使用',
        api_module='lrxy.providers.musixmatch_api',
        supports_synced=True,
        supports_plain=True
    )
}


def get_provider(name: str) -> LyricProvider | None:
    """
    根据名称获取歌词提供商配置

    Args:
        name: 提供商名称（如 'lrclib'）

    Returns:
        LyricProvider | None: 提供商配置对象，不存在则返回 None

    Example:
        >>> provider = get_provider('lrclib')
        >>> print(provider.display_name)
        'LRCLib'
    """
    return PROVIDERS.get(name.lower())


def get_provider_api(name: str) -> Any | None:
    """
    根据名称获取歌词提供商 API 对象

    Args:
        name: 提供商名称（如 'lrclib'）

    Returns:
        Any | None: 提供商 API 对象，不存在或导入失败则返回 None

    Example:
        >>> api = get_provider_api('lrclib')
        >>> # 使用 API 获取歌词
    """
    provider = get_provider(name)
    if not provider:
        return None

    try:
        # 动态导入提供商 API 模块
        import importlib
        module_path = provider.api_module
        module = importlib.import_module(module_path)
        return module
    except ImportError as e:
        import logging
        logging.getLogger(__name__).error(
            f"无法导入提供商 API: {provider.api_module}, 错误: {e}"
        )
        return None


def list_providers() -> list[str]:
    """
    获取所有支持的提供商名称列表

    Returns:
        list[str]: 提供商名称列表

    Example:
        >>> providers = list_providers()
        >>> print(providers)
        ['lrclib', 'applemusic', 'musixmatch']
    """
    return list(PROVIDERS.keys())
