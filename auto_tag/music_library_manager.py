# auto_tag/music_library_manager.py
"""
MusicLibrary API 管理器（线程安全版本）

该模块提供 pymusiclibrary API 的线程安全访问方式。

重要说明（来自官方文档）：
- KuGouMusicApi, NeteaseCloudMusicApi 等接口对象 **均不能跨线程使用**
- 如果需要多线程使用，**必须为每个线程创建独立实例**

解决方案：使用 threading.local() 为每个线程维护独立的 API 实例，
确保符合官方的线程安全要求。

⚠️ 安全警告：
pymusiclibrary 的原生 C 库（QuickJS 引擎）在某些 Windows 环境中
会导致 access violation 崩溃。这是 C 级别错误，Python try-except 无法捕获。
因此，默认禁用 pymusiclibrary，仅使用 Shazam 识别。
"""

from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

# 全局状态
_initialized = False

# ⚠️ 默认禁用 pymusiclibrary 以防止 access violation 崩溃
# 原因：QuickJS C 引擎在某些 Windows 环境中不稳定
# 如需启用，请将此值改为 False（风险自负）
_init_permanently_failed = True

# 线程本地存储：每个线程拥有独立的 API 实例
_thread_local = threading.local()


def _patch_music_library():
    """
    Monkey Patch 修复 pymusiclibrary 库的 Bug
    
    修复问题：
    1. NeteaseCloudMusicApi.__init__ 失败时没有设置 _destroyed 属性
    2. __del__ 方法尝试访问 _destroyed 导致 AttributeError
    
    此函数应该在导入 MusicLibrary 之前或之后立即调用。
    """
    try:
        from MusicLibrary import neteaseCloudMusicApi, kuGouMusicApi
        
        _original_netease_init = neteaseCloudMusicApi.NeteaseCloudMusicApi.__init__
        _original_kugou_init = kuGouMusicApi.KuGouMusicApi.__init__
        
        def _patched_netease_init(self, *args, **kwargs):
            self._destroyed = True
            try:
                _original_netease_init(self, *args, **kwargs)
                self._destroyed = False
            except Exception as e:
                logger.debug(f"[Patch] NetEase API init failed: {e}")
                raise
        
        def _patched_kugou_init(self, *args, **kwargs):
            self._destroyed = True
            try:
                _original_kugou_init(self, *args, **kwargs)
                self._destroyed = False
            except Exception as e:
                logger.debug(f"[Patch] KuGou API init failed: {e}")
                raise
        
        neteaseCloudMusicApi.NeteaseCloudMusicApi.__init__ = _patched_netease_init
        kuGouMusicApi.KuGouMusicApi.__init__ = _patched_kugou_init
        logger.info("[MusicLibrary] Monkey patch applied")
        
    except ImportError:
        logger.debug("[MusicLibrary] pymusiclibrary not available for patching")
    except Exception as e:
        logger.warning(f"[MusicLibrary] Failed to apply patch: {e}")


_patch_music_library()


def get_thread_local_netease_api():
    """
    获取当前线程的 NetEase API 实例（线程安全）
    
    首次调用时在当前线程中创建实例，后续调用返回缓存。
    符合官方 "为每个线程创建实例" 的要求。
    
    Returns:
        NeteaseCloudMusicApi or None: 当前线程的 API 实例或 None
    """
    global _init_permanently_failed
    
    if _init_permanently_failed:
        return None
    
    if hasattr(_thread_local, 'netease_api'):
        return _thread_local.netease_api
    
    thread_name = threading.current_thread().name
    
    try:
        from MusicLibrary.neteaseCloudMusicApi import NeteaseCloudMusicApi
        api = NeteaseCloudMusicApi()
        _thread_local.netease_api = api
        logger.info(f"[MusicLibrary] NetEase API created for thread '{thread_name}'")
        return api
    except Exception as e:
        error_msg = str(e).lower()
        if "access violation" in error_msg or "0x" in error_msg:
            logger.error(
                f"[MusicLibrary] NetEase native library CRASHED in thread "
                f"'{thread_name}': {e}"
            )
            logger.warning(
                "[MusicLibrary] Disabling all native library usage permanently"
            )
            _init_permanently_failed = True
        else:
            logger.warning(
                f"[MusicLibrary] NetEase API init failed in thread "
                f"'{thread_name}': {e}"
            )
        _thread_local.netease_api = None
        return None


def get_thread_local_kugou_api():
    """
    获取当前线程的 KuGou API 实例（线程安全）
    
    首次调用时在当前线程中创建实例，后续调用返回缓存。
    
    Returns:
        KuGouMusicApi or None: 当前线程的 API 实例或 None
    """
    global _init_permanently_failed
    
    if _init_permanently_failed:
        return None
    
    if hasattr(_thread_local, 'kugou_api'):
        return _thread_local.kugou_api
    
    thread_name = threading.current_thread().name
    
    try:
        from MusicLibrary.kuGouMusicApi import KuGouMusicApi
        api = KuGouMusicApi()
        _thread_local.kugou_api = api
        logger.info(f"[MusicLibrary] KuGou API created for thread '{thread_name}'")
        return api
    except Exception as e:
        error_msg = str(e).lower()
        if "access violation" in error_msg or "0x" in error_msg:
            logger.error(
                f"[MusicLibrary] KuGou native library CRASHED in thread "
                f"'{thread_name}': {e}"
            )
            logger.warning(
                "[MusicLibrary] Disabling all native library usage permanently"
            )
            _init_permanently_failed = True
        else:
            logger.warning(
                f"[MusicLibrary] KuGou API init failed in thread "
                f"'{thread_name}': {e}"
            )
        _thread_local.kugou_api = None
        return None


def initialize() -> None:
    """
    在当前线程预初始化 MusicLibrary API 实例（可选）
    
    此函数主要用于主线程预热。子线程应使用 get_thread_local_*_api()
    自动创建线程本地实例。
    """
    global _initialized, _init_permanently_failed
    
    if _initialized or _init_permanently_failed:
        return
    
    get_thread_local_netease_api()
    get_thread_local_kugou_api()
    _initialized = True


def is_available() -> bool:
    """
    检查 MusicLibrary 是否可用
    
    Returns:
        bool: 是否未被永久禁用
    """
    return not _init_permanently_failed


def is_permanently_failed() -> bool:
    """
    检查原生库是否已标记为永久失败
    
    Returns:
        bool: 是否已永久失败
    """
    return _init_permanently_failed
