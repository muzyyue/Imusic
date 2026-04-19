# auto_tag/music_library_manager.py
"""
全局 MusicLibrary API 管理器

该模块确保 pymusiclibrary 的 API 实例只在主线程中初始化一次，
并提供全局访问点。所有需要访问 MusicLibrary API 的代码都应该
使用此模块，而不是直接导入和创建实例。

pymusiclibrary 使用 ctypes 调用原生 C 库，其初始化函数不是线程安全的。
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# 全局 API 实例缓存（单例）
_netease_api = None
_kugou_api = None
_initialized = False


def _patch_music_library():
    """
    Monkey Patch 修复 pymusiclibrary 库的 Bug
    
    修复问题：
    1. NeteaseCloudMusicApi.__init__ 失败时没有设置 _destroyed 属性
    2. __del__ 方法尝试访问 _destroyed 导致 AttributeError
    3. 原生 C 库只能初始化一次，重复创建实例会导致 access violation
    
    此函数应该在导入 MusicLibrary 之前或之后立即调用。
    """
    try:
        from MusicLibrary import neteaseCloudMusicApi, kuGouMusicApi
        
        # 保存原始的 __init__ 方法
        _original_netease_init = neteaseCloudMusicApi.NeteaseCloudMusicApi.__init__
        _original_kugou_init = kuGouMusicApi.KuGouMusicApi.__init__
        
        def _patched_netease_init(self, *args, **kwargs):
            """修复 NetEase API 初始化"""
            self._destroyed = True  # 默认设置为 True，防止 __del__ 出错
            try:
                _original_netease_init(self, *args, **kwargs)
                self._destroyed = False  # 初始化成功后设置为 False
            except Exception as e:
                logger.debug(f"[Patch] NetEase API init failed (safe to ignore): {e}")
                # _destroyed 保持 True，__del__ 会安全跳过
                raise
        
        def _patched_kugou_init(self, *args, **kwargs):
            """修复 KuGou API 初始化"""
            self._destroyed = True  # 默认设置为 True，防止 __del__ 出错
            try:
                _original_kugou_init(self, *args, **kwargs)
                self._destroyed = False  # 初始化成功后设置为 False
            except Exception as e:
                logger.debug(f"[Patch] KuGou API init failed (safe to ignore): {e}")
                # _destroyed 保持 True，__del__ 会安全跳过
                raise
        
        # 应用 Patch
        neteaseCloudMusicApi.NeteaseCloudMusicApi.__init__ = _patched_netease_init
        kuGouMusicApi.KuGouMusicApi.__init__ = _patched_kugou_init
        
        logger.info("[MusicLibrary] Monkey patch applied successfully")
        
    except ImportError:
        logger.debug("[MusicLibrary] pymusiclibrary not available for patching")
    except Exception as e:
        logger.warning(f"[MusicLibrary] Failed to apply patch: {e}")


# 在模块加载时就应用 Patch
_patch_music_library()


def initialize() -> None:
    """
    在主线程预初始化 MusicLibrary API 实例
    
    此函数应该在应用启动时在主线程中调用。
    如果已经初始化过，则直接返回（幂等操作）。
    
    Note:
        必须在主线程中调用此函数，否则可能导致线程安全问题。
    """
    global _netease_api, _kugou_api, _initialized
    
    if _initialized:
        return
    
    try:
        from MusicLibrary.neteaseCloudMusicApi import NeteaseCloudMusicApi
        from MusicLibrary.kuGouMusicApi import KuGouMusicApi
        
        try:
            _netease_api = NeteaseCloudMusicApi()
            logger.info("[MusicLibrary] NetEase API initialized")
        except Exception as e:
            logger.warning(f"[MusicLibrary] NetEase API init failed: {e}")
            _netease_api = None
        
        try:
            _kugou_api = KuGouMusicApi()
            logger.info("[MusicLibrary] KuGou API initialized")
        except Exception as e:
            logger.warning(f"[MusicLibrary] KuGou API init failed: {e}")
            _kugou_api = None
        
        _initialized = True
        
    except ImportError as e:
        logger.debug(f"[MusicLibrary] pymusiclibrary not available: {e}")
    except Exception as e:
        logger.error(f"[MusicLibrary] Initialization error: {e}", exc_info=True)


def get_netease_api():
    """
    获取 NetEase API 实例
    
    如果已初始化，返回缓存的实例。
    如果未初始化，返回 None（不尝试懒加载，避免线程安全问题）。
    
    Returns:
        NeteaseCloudMusicApi or None: API 实例或 None
    """
    if not _initialized:
        logger.warning("[MusicLibrary] API not initialized, call initialize() first")
        return None
    return _netease_api


def get_kugou_api():
    """
    获取 KuGou API 实例
    
    如果已初始化，返回缓存的实例。
    如果未初始化，返回 None（不尝试懒加载，避免线程安全问题）。
    
    Returns:
        KuGouMusicApi or None: API 实例或 None
    """
    if not _initialized:
        logger.warning("[MusicLibrary] API not initialized, call initialize() first")
        return None
    return _kugou_api


def is_available() -> bool:
    """
    检查 MusicLibrary 是否可用
    
    Returns:
        bool: 是否已初始化且至少有一个 API 可用
    """
    return _initialized and (_netease_api is not None or _kugou_api is not None)
