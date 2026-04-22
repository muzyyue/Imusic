# auto_tag/audio_recognize.py
"""
Recognise audio files with Shazam, optionally rename or copy them,
and update metadata (tags, cover art).  Optionally only tag without renaming.

OGG files are converted to WAV via soundfile/libsndfile (no ffmpeg),
but if conversion or recognition on WAV fails, we fall back to the
original OGG for recognition—so tests with DummyShazam still work.

Multi-source search support for NetEase Cloud Music and KuGou Music.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import shutil
import tempfile
import threading
import time
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

import eyed3
import soundfile as sf
from mutagen import File
from mutagen.flac import Picture
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis
from shazamio import Shazam
from tqdm.asyncio import tqdm

from auto_tag.utils import find_deepest_metadata_key, sanitize

# 配置日志
logger = logging.getLogger(__name__)

# 全局 API 实例缓存（单例模式 - 主线程使用）
# 重要：pymusiclibrary 原生 C 库只能初始化一次，重复创建会导致 access violation！
_netease_api = None
_kugou_api = None
_initialized = False

# 线程本地存储（子线程使用 - 每个线程独立实例）
_thread_local = threading.local()

# Monkey Patch 标志（确保只执行一次）
_monkey_patch_applied = False


def _apply_monkey_patch():
    """
    应用 Monkey Patch 修复 pymusiclibrary 库的 Bug

    修复问题：
    1. NeteaseCloudMusicApi.__init__ 失败时没有设置 _destroyed 属性
    2. KuGouMusicApi.__init__ 失败时没有设置 _destroyed 属性
    3. __del__ 方法尝试访问 _destroyed 导致 AttributeError
    """
    global _monkey_patch_applied

    if _monkey_patch_applied:
        return

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
        _monkey_patch_applied = True
        logger.info("[MusicLibrary] Monkey patch applied successfully")

    except ImportError:
        logger.debug("[MusicLibrary] pymusiclibrary not available for patching")
    except Exception as e:
        logger.warning(f"[MusicLibrary] Failed to apply monkey patch: {e}")


def initialize_music_library():
    """
    在主线程预初始化 MusicLibrary API 实例（全局单例）

    此函数应该在应用启动时调用（在 GUI 主线程中）。
    只创建一次实例，后续所有搜索复用该实例。

    重要：pymusiclibrary 原生 C 库只能初始化一次，
    重复创建实例会导致 access violation 崩溃！
    """
    global _netease_api, _kugou_api, _initialized

    if _initialized:
        return

    _apply_monkey_patch()

    try:
        from MusicLibrary.neteaseCloudMusicApi import NeteaseCloudMusicApi
        try:
            _netease_api = NeteaseCloudMusicApi()
            logger.info("[MusicLibrary] NetEase API initialized (global singleton)")
        except Exception as e:
            logger.warning(f"[MusicLibrary] NetEase API init failed: {e}")
            _netease_api = None
    except ImportError as e:
        logger.debug(f"[MusicLibrary] pymusiclibrary not available: {e}")
        _netease_api = None

    try:
        from MusicLibrary.kuGouMusicApi import KuGouMusicApi
        try:
            _kugou_api = KuGouMusicApi()
            logger.info("[MusicLibrary] KuGou API initialized (global singleton)")
        except Exception as e:
            logger.warning(f"[MusicLibrary] KuGou API init failed: {e}")
            _kugou_api = None
    except ImportError as e:
        logger.debug(f"[MusicLibrary] pymusiclibrary not available: {e}")
        _kugou_api = None

    _initialized = True


def get_netease_api():
    """
    获取 NetEase API 实例（智能模式）

    智能判断当前线程：
    - 主线程：返回全局单例（启动时预初始化）
    - 子线程：返回该线程的独立实例（避免跨线程访问崩溃）

    Returns:
        NeteaseCloudMusicApi or None: API 实例或 None
    """
    current_thread = threading.current_thread()
    thread_name = current_thread.name

    # 主线程：使用全局单例
    if thread_name == 'MainThread':
        if not _initialized:
            logger.warning(f"[MusicLibrary][{thread_name}] API not initialized, call initialize_music_library() first")
            return None
        if _netease_api is None:
            logger.warning(f"[MusicLibrary][{thread_name}] Global NetEase API is None (init failed?)")
            return None
        return _netease_api

    # 子线程：使用线程本地实例（每线程只创建一次）
    if hasattr(_thread_local, 'netease_api'):
        api = _thread_local.netease_api
        if api is not None:
            return api
        else:
            logger.warning(f"[MusicLibrary][{thread_name}] Thread-local NetEase API was set to None (previous init failed)")

    logger.info(f"[MusicLibrary][{thread_name}] Creating new NetEase API instance for this thread...")
    try:
        _apply_monkey_patch()
        from MusicLibrary.neteaseCloudMusicApi import NeteaseCloudMusicApi
        api = NeteaseCloudMusicApi()
        _thread_local.netease_api = api
        logger.info(f"[MusicLibrary][{thread_name}] ✅ NetEase API created successfully!")
        return api
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[MusicLibrary][{thread_name}] ❌ Failed to create NetEase API: {error_msg}")
        if "access violation" in error_msg.lower() or "0x" in error_msg.lower():
            logger.error(f"[MusicLibrary][{thread_name}] ⚠️ This is a native library crash (QuickJS engine)")
        _thread_local.netease_api = None
        return None


def get_kugou_api():
    """
    获取 KuGou API 实例（智能模式）

    智能判断当前线程：
    - 主线程：返回全局单例（启动时预初始化）
    - 子线程：返回该线程的独立实例（避免跨线程访问崩溃）

    Returns:
        KuGouMusicApi or None: API 实例或 None
    """
    current_thread = threading.current_thread()
    thread_name = current_thread.name

    # 主线程：使用全局单例
    if thread_name == 'MainThread':
        if not _initialized:
            logger.warning(f"[MusicLibrary][{thread_name}] API not initialized, call initialize_music_library() first")
            return None
        if _kugou_api is None:
            logger.warning(f"[MusicLibrary][{thread_name}] Global KuGou API is None (init failed?)")
            return None
        return _kugou_api

    # 子线程：使用线程本地实例（每线程只创建一次）
    if hasattr(_thread_local, 'kugou_api'):
        api = _thread_local.kugou_api
        if api is not None:
            return api
        else:
            logger.warning(f"[MusicLibrary][{thread_name}] Thread-local KuGou API was set to None (previous init failed)")

    logger.info(f"[MusicLibrary][{thread_name}] Creating new KuGou API instance for this thread...")
    try:
        _apply_monkey_patch()
        from MusicLibrary.kuGouMusicApi import KuGouMusicApi
        api = KuGouMusicApi()
        _thread_local.kugou_api = api
        logger.info(f"[MusicLibrary][{thread_name}] ✅ KuGou API created successfully!")
        return api
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[MusicLibrary][{thread_name}] ❌ Failed to create KuGou API: {error_msg}")
        if "access violation" in error_msg.lower() or "0x" in error_msg.lower():
            logger.error(f"[MusicLibrary][{thread_name}] ⚠️ This is a native library crash (QuickJS engine)")
        _thread_local.kugou_api = None
        return None


def is_music_library_available() -> bool:
    """
    检查 MusicLibrary 是否可用

    Returns:
        bool: 是否已初始化且至少有一个 API 可用
    """
    # 主线程检查全局状态
    if threading.current_thread().name == 'MainThread':
        return _initialized and (_netease_api is not None or _kugou_api is not None)

    # 子线程检查线程本地状态
    has_netease = hasattr(_thread_local, 'netease_api') and _thread_local.netease_api is not None
    has_kugou = hasattr(_thread_local, 'kugou_api') and _thread_local.kugou_api is not None
    return has_netease or has_kugou


# 多数据源搜索结果数据结构
class SearchResult:
    """
    多平台音乐搜索结果封装类

    Attributes:
        source: 数据来源平台标识（"shazam"|"netease"|"kugou"）
        title: 歌曲标题
        artist: 艺术家
        album: 专辑名
        cover_link: 封面图片URL
        song_id: 平台歌曲ID
        duration: 歌曲时长（秒）
        confidence: 置信度/相关度评分（0-1）
        raw_data: 原始API返回数据
    """

    def __init__(
        self,
        source: str,
        title: str,
        artist: str,
        album: str,
        cover_link: str = "",
        song_id: str = "",
        duration: int = 0,
        confidence: float = 1.0,
        raw_data: dict | None = None,
    ) -> None:
        """
        初始化搜索结果

        Args:
            source: 数据来源平台
            title: 歌曲标题
            artist: 艺术家
            album: 专辑名
            cover_link: 封面URL
            song_id: 歌曲ID
            duration: 时长
            confidence: 置信度
            raw_data: 原始数据
        """
        self.source = source
        self.title = title
        self.artist = artist
        self.album = album
        self.cover_link = cover_link
        self.song_id = song_id
        self.duration = duration
        self.confidence = confidence
        self.raw_data = raw_data or {}

    def to_dict(self) -> dict[str, Any]:
        """
        将搜索结果转换为字典格式

        Returns:
            dict: 包含所有字段信息的字典
        """
        return {
            "source": self.source,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "cover_link": self.cover_link,
            "song_id": self.song_id,
            "duration": self.duration,
            "confidence": self.confidence,
        }


def _parse_shazam_result(track: dict) -> SearchResult:
    """
    解析 Shazam API 返回的歌曲数据

    Args:
        track: Shazam 返回的 track 字典

    Returns:
        SearchResult: 解析后的搜索结果
    """
    title = track.get("title", "Unknown Title")
    artist = track.get("subtitle", "Unknown Artist")
    album = find_deepest_metadata_key(track, "Album") or "Unknown Album"
    cover = track.get("images", {}).get("coverart", "")
    duration = 0

    # 尝试从 sections 中提取时长信息
    # 注意：Shazam API 返回的 metadata 可能是 list 或 dict
    for section in track.get("sections", []):
        if section.get("type") == "SONG":
            metadata = section.get("metadata")
            if isinstance(metadata, dict):
                # 旧版格式：metadata 是字典
                duration = metadata.get("duration", 0) or 0
            elif isinstance(metadata, list):
                # 新版格式：metadata 是列表，需要查找 duration 条目
                for item in metadata:
                    if isinstance(item, dict):
                        # 尝试通过 title 匹配
                        if item.get("title") == "Duration":
                            try:
                                duration = int(item.get("text", 0)) or 0
                            except (ValueError, TypeError):
                                duration = 0
                            break
                        # 或者直接尝试获取 duration 键
                        if "duration" in item:
                            try:
                                duration = int(item["duration"]) or 0
                            except (ValueError, TypeError):
                                duration = 0
                            break
            break

    return SearchResult(
        source="shazam",
        title=title,
        artist=artist,
        album=album,
        cover_link=cover,
        duration=duration,
        confidence=1.0,
        raw_data=track,
    )


def _parse_netease_result(song: dict) -> SearchResult:
    """
    解析网易云音乐 API 返回的歌曲数据

    Args:
        song: 网易云音乐返回的歌曲字典

    Returns:
        SearchResult: 解析后的搜索结果
    """
    title = song.get("name", "Unknown Title")
    artists = song.get("artists", [])
    artist = " / ".join([a.get("name", "Unknown") for a in artists]) if artists else "Unknown Artist"
    album_info = song.get("album", {})
    album = album_info.get("name", "Unknown Album") if album_info else "Unknown Album"
    song_id = str(song.get("id", ""))
    duration_ms = song.get("duration", 0)
    duration = duration_ms // 1000 if duration_ms else 0

    # 获取封面（使用 al.picUrl 或 album.picUrl）
    cover = ""
    if album_info:
        cover = album_info.get("picUrl", "") or album_info.get("blurPicUrl", "")

    return SearchResult(
        source="netease",
        title=title,
        artist=artist,
        album=album,
        cover_link=cover,
        song_id=song_id,
        duration=duration,
        confidence=0.9,
        raw_data=song,
    )


class SearchCache:
    """
    搜索结果缓存（线程安全LRU + TTL）

    特性：
    - LRU淘汰：超出容量时自动移除最久未使用的条目
    - TTL过期：超过时间限制的条目自动失效
    - 线程安全：使用锁保护并发访问
    - 命中统计：记录命中率用于性能分析
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        """
        初始化缓存

        Args:
            max_size: 最大缓存条目数（默认100）
            ttl_seconds: 条目存活时间，秒（默认5分钟）
        """
        self._cache: dict[str, tuple[float, list[SearchResult]]] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, keyword: str) -> list[SearchResult] | None:
        """
        获取缓存结果

        Args:
            keyword: 搜索关键词

        Returns:
            缓存的搜索结果列表，未命中或已过期返回None
        """
        with self._lock:
            if keyword not in self._cache:
                self._misses += 1
                return None

            timestamp, results = self._cache[keyword]
            elapsed = time.time() - timestamp

            if elapsed > self._ttl:
                del self._cache[keyword]
                self._misses += 1
                logger.debug(f"[Cache] EXPIRED '{keyword}' (age={elapsed:.0f}s)")
                return None

            self._hits += 1
            logger.info(f"[Cache] HIT '{keyword}' ({len(results)} results, age={elapsed:.0f}s)")
            return results

    def set(self, keyword: str, results: list[SearchResult]) -> None:
        """
        写入缓存

        Args:
            keyword: 搜索关键词
            results: 搜索结果列表
        """
        with self._lock:
            if len(self._cache) >= self._max_size and keyword not in self._cache:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
                del self._cache[oldest_key]
                logger.debug(f"[Cache] EVICTED '{oldest_key}' (cache full)")

            self._cache[keyword] = (time.time(), results)
            logger.info(f"[Cache] STORED '{keyword}' ({len(results)} results)")

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            size = len(self._cache)
            self._cache.clear()
            logger.info(f"[Cache] CLEARED ({size} entries removed)")

    def stats(self) -> dict:
        """获取缓存统计信息"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.1f}%",
                "ttl_seconds": self._ttl,
            }


class RateLimiter:
    """
    API请求限流器（自适应间隔控制）

    特性：
    - 最小间隔保护：避免请求过于密集触发反爬
    - 自适应调整：遇到限流自动增加间隔，成功后逐渐恢复
    - 最大间隔上限：防止等待时间过长影响体验
    - 线程安全：多线程环境下正确工作
    """

    def __init__(
        self,
        min_interval: float = 1.0,
        max_interval: float = 10.0,
        backoff_factor: float = 2.0,
        recovery_factor: float = 0.8,
    ):
        """
        初始化限流器

        Args:
            min_interval: 最小请求间隔（秒），默认1秒
            max_interval: 最大请求间隔（秒），默认10秒
            backoff_factor: 遇到限流时的退避倍数，默认2倍
            recovery_factor: 成功后的恢复系数，默认0.8（间隔缩短20%）
        """
        self._min_interval = min_interval
        self._max_interval = max_interval
        self._backoff_factor = backoff_factor
        self._recovery_factor = recovery_factor
        self._current_interval = min_interval
        self._last_request_time = 0.0
        self._lock = threading.Lock()
        self._rate_limited_count = 0

    async def wait_if_needed(self) -> float:
        """
        如果距离上次请求太近，则等待适当时间

        Returns:
            实际等待时间（秒），0表示无需等待
        """
        with self._lock:
            elapsed = time.time() - self._last_request_time
            wait_time = max(0, self._current_interval - elapsed)

            if wait_time > 0:
                logger.info(
                    f"[RateLimiter] Waiting {wait_time:.2f}s "
                    f"(interval={self._current_interval:.1f}s, elapsed={elapsed:.2f}s)"
                )

        if wait_time > 0:
            await asyncio.sleep(wait_time)
            return wait_time

        return 0.0

    def record_request(self) -> None:
        """记录一次请求时间戳"""
        with self._lock:
            self._last_request_time = time.time()

    def on_success(self) -> None:
        """
        请求成功时调用

        逐渐恢复默认间隔（但不会低于最小值）
        """
        with self._lock:
            old_interval = self._current_interval
            self._current_interval = max(
                self._min_interval,
                self._current_interval * self._recovery_factor
            )
            logger.debug(
                f"[RateLimiter] Success: {old_interval:.2f}s → {self._current_interval:.2f}s"
            )

    def on_rate_limited(self) -> None:
        """
        遇到频率限制时调用

        增加请求间隔（但不会超过最大值）
        """
        with self._lock:
            old_interval = self._current_interval
            self._current_interval = min(
                self._max_interval,
                self._current_interval * self._backoff_factor
            )
            self._rate_limited_count += 1
            logger.warning(
                f"[RateLimiter] Rate limited! Interval increased: "
                f"{old_interval:.2f}s → {self._current_interval:.2f}s "
                f"(limit count: {self._rate_limited_count})"
            )

    def stats(self) -> dict:
        """获取限流器统计信息"""
        with self._lock:
            return {
                "current_interval": round(self._current_interval, 2),
                "min_interval": self._min_interval,
                "max_interval": self._max_interval,
                "rate_limited_count": self._rate_limited_count,
            }


# 全局单例：搜索缓存和限流器（模块级共享）
_search_cache = SearchCache(max_size=150, ttl_seconds=300)
_rate_limiter = RateLimiter(min_interval=1.0, max_interval=8.0)


async def _search_netease_rest(keyword: str, limit: int = 5, max_retries: int = 3) -> list[SearchResult]:
    """
    纯 REST API 搜索网易云音乐（完全独立，不依赖 pymusiclibrary）

    使用 http.client 直接发起 HTTPS 请求，手动管理 SSL context 和连接，
    完全绕开 pymusiclibrary C 库和 urllib 全局状态。
    跨线程安全，无 access violation 风险。

    优化特性：
    - 内置搜索结果缓存（LRU + TTL），相同关键词直接返回
    - 自适应请求间隔控制，主动避免触发频率限制
    - 指数退避重试机制，自动处理网易云 API 频率限制（HTTP 405）

    API 接口: GET https://music.163.com/api/search/get/web?s=关键词&type=1&limit=N

    Args:
        keyword: 搜索关键词
        limit: 返回结果数量上限
        max_retries: 最大重试次数（遇到频率限制时）

    Returns:
        list[SearchResult]: 搜索结果列表
    """
    global _search_cache, _rate_limiter

    # Step 1: 检查缓存（命中则直接返回，无需网络请求）
    cached_results = _search_cache.get(keyword)
    if cached_results is not None:
        return cached_results

    # Step 2: 请求前等待（避免过于频繁）
    await _rate_limiter.wait_if_needed()

    import random

    for attempt in range(max_retries + 1):
        try:
            # Step 3: 记录请求时间戳
            _rate_limiter.record_request()

            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, _do_single_search, keyword, limit)

            if result:
                # Step 4a: 成功 → 写入缓存 + 恢复默认间隔
                _search_cache.set(keyword, result)
                _rate_limiter.on_success()
                return result

            if attempt < max_retries:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(
                    f"[NetEase-REST] Retry {attempt + 1}/{max_retries} "
                    f"after {wait_time:.1f}s for '{keyword}'"
                )
                await asyncio.sleep(wait_time)

        except RuntimeError:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                _rate_limiter.record_request()
                future = executor.submit(_do_single_search, keyword, limit)
                result = future.result(timeout=30)

                if result:
                    _search_cache.set(keyword, result)
                    _rate_limiter.on_success()
                    return result

                if attempt < max_retries:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"[NetEase-REST] Retry {attempt + 1}/{max_retries} "
                        f"after {wait_time:.1f}s for '{keyword}'"
                    )
                    await asyncio.sleep(wait_time)

        except Exception as e:
            logger.error(f"[NetEase-REST] Error on attempt {attempt + 1}: {e}", exc_info=True)
            if attempt < max_retries:
                await asyncio.sleep(1)

    logger.error(f"[NetEase-REST] All {max_retries} retries failed for '{keyword}'")
    return []


def _do_single_search(keyword: str, limit: int) -> list[SearchResult]:
    """
    执行单次 REST API 搜索请求

    Args:
        keyword: 搜索关键词
        limit: 结果数量限制

    Returns:
        list[SearchResult]: 搜索结果列表，失败返回空列表
    """
    import ssl
    import http.client

    try:
        logger.info(f"[NetEase-REST] Searching: {keyword}")

        params = urlencode({
            's': keyword,
            'type': 1,
            'offset': 0,
            'total': 'true',
            'limit': limit
        })
        path = f'/api/search/get/web?{params}'

        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2

        conn = http.client.HTTPSConnection(
            'music.163.com',
            timeout=15,
            context=ctx,
        )

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://music.163.com/',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }

        conn.request('GET', path, headers=headers)
        response = conn.getresponse()
        status = response.status
        raw_data = response.read().decode('utf-8')
        conn.close()

        if status != 200:
            error_msg = ""
            try:
                error_data = json.loads(raw_data)
                error_msg = error_data.get('msg', '')
            except:
                pass

            if status == 405 and "频繁" in error_msg:
                logger.warning(
                    f"[NetEase-REST] Rate limited (405) for '{keyword}', "
                    f"will retry..."
                )
                _rate_limiter.on_rate_limited()
                return []  # 返回空列表触发重试
            else:
                logger.warning(f"[NetEase-REST] HTTP {status} for '{keyword}': {error_msg}")
                return []

        data = json.loads(raw_data)

        if not data or 'result' not in data:
            logger.warning(
                f"[NetEase-REST] No 'result' key for '{keyword}', "
                f"code={data.get('code')}, msg={data.get('msg', '')[:50]}"
            )
            return []

        songs = data['result'].get('songs', [])
        if not songs:
            logger.warning(f"[NetEase-REST] Empty songs for '{keyword}'")
            return []

        logger.info(f"[NetEase-REST] Found {len(songs)} songs for '{keyword}'")
        parsed = [_parse_netease_result(song) for song in songs[:limit]]
        return parsed

    except Exception as e:
        logger.error(f"[NetEase-REST] Error: {e}", exc_info=True)
        return []


def _parse_kugou_result(song: dict) -> SearchResult:
    """
    解析酷狗音乐 API 返回的歌曲数据

    Args:
        song: 酷狗音乐返回的歌曲字典

    Returns:
        SearchResult: 解析后的搜索结果
    """
    title = song.get("songname", song.get("songname_original", "Unknown Title"))
    artist = song.get("singername", "Unknown Artist")
    album = song.get("album_name", "Unknown Album")
    song_id = str(song.get("hash", song.get("fileid", "")))
    duration = song.get("duration", 0)

    # 获取封面
    cover = song.get("album_pic", "") or song.get("imgurl", "")

    return SearchResult(
        source="kugou",
        title=title,
        artist=artist,
        album=album,
        cover_link=cover,
        song_id=song_id,
        duration=duration,
        confidence=0.85,
        raw_data=song,
    )


def _extract_response_data(response) -> dict | None:
    """
    从API响应中提取数据

    pymusiclibrary 的 API 返回 Response 对象，
    需要从 .data 或 .body 属性提取实际数据。

    Args:
        response: API 响应对象

    Returns:
        dict | None: 提取的数据字典，失败返回None
    """
    if response is None:
        return None
    
    # 尝试不同的属性
    if hasattr(response, 'data') and response.data is not None:
        return response.data if isinstance(response.data, dict) else None
    
    if hasattr(response, 'body') and response.body is not None:
        return response.body if isinstance(response.body, dict) else None
    
    if isinstance(response, dict):
        return response
    
    return None


async def _search_netease(keyword: str, limit: int = 5) -> list[SearchResult]:
    """
    异步搜索网易云音乐（全局单例模式）

    使用预初始化的全局单例 API 实例，
    与旧版本表格布局保持一致。

    Args:
        keyword: 搜索关键词
        limit: 返回结果数量

    Returns:
        list[SearchResult]: 搜索结果列表
    """
    try:
        def _do_search() -> list[SearchResult]:
            try:
                current_thread_name = threading.current_thread().name
                logger.info(f"[NetEase] Getting API for thread: {current_thread_name}")
                
                api = get_netease_api()
                if api is None:
                    logger.warning(f"[NetEase] API not available in thread '{current_thread_name}' - search skipped")
                    return []

                logger.info(f"[NetEase] Searching: {keyword}")
                response = api.search(keyword, limit=limit)

                # 诊断：记录原始响应对象信息
                logger.info(f"[NetEase] Response type: {type(response).__name__}, dir: {[a for a in dir(response) if not a.startswith('_')]}")
                if hasattr(response, 'data'):
                    logger.info(f"[NetEase] response.data type: {type(response.data)}, keys: {list(response.data.keys()) if isinstance(response.data, dict) else 'N/A'}")
                elif hasattr(response, 'body'):
                    logger.info(f"[NetEase] response.body type: {type(response.body)}, keys: {list(response.body.keys()) if isinstance(response.body, dict) else 'N/A'}")
                elif hasattr(response, 'status_code'):
                    logger.info(f"[NetEase] response.status_code: {response.status_code}")

                result = _extract_response_data(response)
                logger.info(f"[NetEase] Extracted data: {'keys=' + str(list(result.keys())) if result else 'None'}")

                if not result:
                    logger.warning(f"[NetEase] No response data for: {keyword}")
                    return []

                if "result" not in result:
                    logger.warning(f"[NetEase] No 'result' key in response for: {keyword}, keys={list(result.keys())}")
                    return []

                songs = result["result"].get("songs", [])
                logger.info(f"[NetEase] Found {len(songs)} songs for: {keyword}")

                if not songs:
                    logger.warning(f"[NetEase] Empty songs list for: {keyword}")
                    return []

                parsed = [_parse_netease_result(song) for song in songs[:limit]]
                logger.info(f"[NetEase] Parsed {len(parsed)} results")
                return parsed

            except OSError as e:
                logger.error(f"[NetEase] Native library init failed: {e}")
                return []
            except Exception as e:
                logger.error(f"[NetEase] Search error: {e}", exc_info=True)
                return []

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _do_search)
    except RuntimeError:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_do_search)
            return future.result(timeout=30)
    except Exception as e:
        logger.error(f"[NetEase] Async error: {e}", exc_info=True)
        return []


async def _search_kugou(keyword: str, limit: int = 5) -> list[SearchResult]:
    """
    异步搜索酷狗音乐（全局单例模式）

    使用预初始化的全局单例 API 实例，
    与旧版本表格布局保持一致。

    Args:
        keyword: 搜索关键词
        limit: 返回结果数量

    Returns:
        list[SearchResult]: 搜索结果列表
    """
    try:
        def _do_search_kugou() -> list[SearchResult]:
            try:
                api = get_kugou_api()
                if api is None:
                    logger.warning("[KuGou] API not available")
                    return []

                logger.info(f"[KuGou] Searching: {keyword}")
                response = api.search(keyword)
                result = _extract_response_data(response)

                if not result:
                    logger.warning(f"[KuGou] No response data for: {keyword}")
                    return []

                if "data" not in result:
                    logger.warning(f"[KuGou] No 'data' key in response for: {keyword}, keys={list(result.keys())}")
                    return []

                songs = result["data"].get("lists", []) if isinstance(result["data"], dict) else []
                logger.info(f"[KuGou] Found {len(songs)} songs for: {keyword}")

                if not songs:
                    logger.warning(f"[KuGou] Empty songs list for: {keyword}")
                    return []

                parsed = [_parse_kugou_result(song) for song in songs[:limit]]
                logger.info(f"[KuGou] Parsed {len(parsed)} results")
                return parsed

            except OSError as e:
                logger.error(f"[KuGou] Native library init failed: {e}")
                return []
            except Exception as e:
                logger.error(f"[KuGou] Search error: {e}", exc_info=True)
                return []

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _do_search_kugou)
    except RuntimeError:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_do_search_kugou)
            return future.result(timeout=30)
    except Exception as e:
        logger.error(f"[KuGou] Async error: {e}", exc_info=True)
        return []


async def multi_source_search(
    keyword: str,
    shazam_result: dict | None = None,
    limit: int = 5,
) -> list[SearchResult]:
    """
    多数据源并发搜索音乐信息

    同时向 Shazam、网易云音乐、酷狗音乐发起查询请求，
    将结果汇总并按置信度排序。

    Args:
        keyword: 搜索关键词（通常为"艺术家 歌曲名"格式）
        shazam_result: 已有的 Shazam 识别结果（如果有）
        limit: 每个平台返回的最大结果数

    Returns:
        list[SearchResult]: 所有平台的搜索结果，按置信度降序排列

    Example:
        >>> results = await multi_source_search("周杰伦 晴天")
        >>> for r in results:
        ...     print(f"{r.source}: {r.title} - {r.artist}")
    """
    all_results: list[SearchResult] = []
    logger.info(f"[MultiSource] Starting search with keyword: {keyword}")

    # 如果已有 Shazam 结果，直接解析
    if shazam_result and "track" in shazam_result:
        try:
            shazam_result_obj = _parse_shazam_result(shazam_result["track"])
            all_results.append(shazam_result_obj)
            logger.info(f"[MultiSource] Shazam result added: {shazam_result_obj.title} - {shazam_result_obj.artist}")
        except Exception as e:
            logger.error(f"[MultiSource] Failed to parse Shazam result: {e}", exc_info=True)

    # 使用纯 REST API 搜索网易云（完全独立，不依赖 pymusiclibrary）
    logger.info("[MultiSource] Using pure REST API for NetEase (no pymusiclibrary dependency)")
    netease_task = asyncio.create_task(_search_netease_rest(keyword, limit))

    # 酷狗暂时禁用（REST API 不可用，原生库不稳定）
    # TODO: 未来可以寻找酷狗的 REST API 或使用第三方服务
    kugou_task = None
    logger.info("[MultiSource] KuGou Music temporarily disabled (no stable REST API available)")

    # 等待网易云搜索完成
    netease_results, = await asyncio.gather(
        netease_task, return_exceptions=True
    )

    # 处理异常结果
    if isinstance(netease_results, Exception):
        logger.error(f"[MultiSource] NetEase search exception: {netease_results}", exc_info=True)
        netease_results = []
    elif isinstance(netease_results, list):
        logger.info(f"[MultiSource] NetEase returned {len(netease_results)} results")
    else:
        logger.warning(f"[MultiSource] NetEase returned unexpected type: {type(netease_results)}")
        netease_results = []

    all_results.extend(netease_results)  # type: ignore[arg-type]

    # 按置信度降序排序
    all_results.sort(key=lambda x: x.confidence, reverse=True)

    logger.info(f"[MultiSource] Total results: {len(all_results)}")
    for r in all_results:
        logger.info(f"  - [{r.source}] {r.title} - {r.artist}")

    return all_results


async def find_and_recognize_audio_files(
    folder_path: str,
    *,
    modify: bool = True,
    delay: int = 10,
    nbr_retry: int = 3,
    trace: bool = False,
    extensions: list[str] | tuple[str, ...] = ("mp3", "ogg"),
    output_dir: str | None = None,
    plex_structure: bool = False,
    copy_to: str | None = None,
    tag_only: bool = False,
) -> None:
    """
    Walk folder_path, recognise each file, then move or copy/tag it.
    - copy_to: if given, base dir to copy files into (instead of moving)
    - tag_only: if True, update tags/cover only on the original file (no rename/move).
    """
    # Safe 模式：API 实例在首次使用时惰性创建，无需预初始化

    exts = {e.lower().lstrip(".") for e in extensions}
    audio_files: list[str] = []
    for root, _, files in os.walk(folder_path):
        if "test" in os.path.basename(root).lower():
            continue
        for fn in files:
            if os.path.splitext(fn)[1].lower().lstrip(".") in exts:
                audio_files.append(os.path.join(root, fn))

    if not audio_files:
        print(f"No files with extensions {exts} found in {folder_path}.")
        return

    shazam = Shazam()
    ok = 0

    for path in tqdm(audio_files, desc="Recognising and renaming"):
        res = await recognize_and_rename_file(
            file_path=path,
            shazam=shazam,
            modify=modify,
            delay=delay,
            nbr_retry=nbr_retry,
            trace=trace,
            output_dir=output_dir,
            plex_structure=plex_structure,
            copy_to=copy_to,
            tag_only=tag_only,
        )
        if "error" in res and trace:
            print(f"[{os.path.basename(path)}] {res['error']}")
        if "error" not in res:
            ok += 1

    print(f"Succeeded {ok}/{len(audio_files)}.")


def _build_search_keyword_from_filename(file_path: str) -> str:
    """
    从文件名提取搜索关键词

    支持的文件名格式：
    - "艺术家 - 歌曲名.mp3" → "艺术家 歌曲名"
    - "歌曲名 - 艺术家.mp3" → "歌曲名 艺术家"
    - "歌曲名.mp3" → "歌曲名"

    Args:
        file_path: 文件完整路径

    Returns:
        str: 提取的关键词（去除扩展名和特殊字符），无法解析时返回空字符串
    """
    filename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(filename)[0]

    if not name_without_ext:
        return ""

    import re

    name = name_without_ext.strip()

    common_separators = [" - ", "-", " – ", "—", "_", "."]
    for sep in common_separators:
        if sep in name:
            parts = name.split(sep, 1)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) >= 2:
                keyword = f"{parts[0]} {parts[1]}"
                logger.info(f"[Keyword] Extracted from filename '{filename}': {keyword}")
                return keyword

    logger.info(f"[Keyword] Using filename as keyword: {name}")
    return name


async def recognize_and_rename_file(
    *,
    file_path: str,
    shazam: Shazam,
    modify: bool,
    delay: int,
    nbr_retry: int,
    trace: bool,
    output_dir: str | None,
    plex_structure: bool,
    copy_to: str | None = None,
    tag_only: bool = False,
) -> dict:
    """
    Recognise file_path with Shazam, then move or copy & tag it.
    Also performs multi-source search (NetEase, KuGou) for additional results.
    - If tag_only is True, only update metadata on the original file_path.
    - Else if copy_to is set, copy; otherwise rename/move.
    """
    ext = os.path.splitext(file_path)[1].lower()
    tmp_wav: str | None = None

    # 1) For OGG, attempt WAV conversion for recognition
    input_path = file_path
    if ext == ".ogg":
        fd, tmp_wav = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            data, sr = sf.read(file_path, dtype="int16")
            sf.write(tmp_wav, data, sr, subtype="PCM_16")
            input_path = tmp_wav
        except Exception as exc:
            if trace:
                print(f"[{os.path.basename(file_path)}] OGG→WAV failed: {exc}")
            input_path = file_path

    # 2) Recognise with retries
    out = None
    for attempt in range(1, nbr_retry + 1):
        try:
            candidate = await shazam.recognize(input_path)
            if candidate:
                out = candidate
                break
        except Exception as exc:
            if trace:
                print(
                    f"[{os.path.basename(file_path)}] attempt {attempt}: {exc}"
                )
        if attempt < nbr_retry:
            await asyncio.sleep(delay)

    # Fallback to original OGG if WAV recognition failed
    if ext == ".ogg" and out is None and input_path != file_path:
        for attempt in range(1, nbr_retry + 1):
            try:
                candidate = await shazam.recognize(file_path)
                if candidate:
                    out = candidate
                    break
            except Exception as exc:
                if trace:
                    print(
                        f"[{os.path.basename(file_path)}] OGG fallback {attempt}: {exc}"
                    )
            if attempt < nbr_retry:
                await asyncio.sleep(delay)

    # cleanup temp WAV
    if tmp_wav and os.path.exists(tmp_wav):
        os.remove(tmp_wav)

    if not out or "track" not in out:
        if trace:
            print(f"Shazam failed: {file_path}, attempting fallback search...")

        fallback_keyword = _build_search_keyword_from_filename(file_path)

        if fallback_keyword:
            logger.info(f"[Fallback] Trying NetEase search with keyword: {fallback_keyword}")
            try:
                fallback_results = await multi_source_search(
                    keyword=fallback_keyword,
                    shazam_result=None,
                    limit=5,
                )

                if fallback_results:
                    best_match = fallback_results[0]
                    s_title = sanitize(best_match.title, trace)
                    s_artist = sanitize(best_match.artist, trace)
                    s_album = sanitize(best_match.album, trace)

                    logger.info(
                        f"[Fallback] Success! Found: {best_match.title} - {best_match.artist}"
                    )

                    return {
                        "file_path": file_path,
                        "new_file_path": file_path,
                        "title": s_title,
                        "author": s_artist,
                        "album": s_album,
                        "cover_link": best_match.cover_link,
                        "search_results": [sr.to_dict() for sr in fallback_results],
                    }
                else:
                    logger.warning(f"[Fallback] No results for keyword: {fallback_keyword}")
            except Exception as fallback_error:
                logger.error(f"[Fallback] Search failed: {fallback_error}", exc_info=True)

        return {
            "file_path": file_path,
            "error": "Recognition failed",
            "search_results": [],
        }

    # 3) Extract & sanitize metadata
    track = out["track"]
    title = track.get("title", "Unknown Title")
    artist = track.get("subtitle", "Unknown Artist")
    album = find_deepest_metadata_key(track, "Album") or "Unknown Album"
    cover = track.get("images", {}).get("coverart", "")

    s_title = sanitize(title, trace)
    s_artist = sanitize(artist, trace)
    s_album = sanitize(album, trace)

    # 3.5) Multi-source search: query NetEase and KuGou concurrently
    keyword = f"{artist} {title}"
    search_results = await multi_source_search(
        keyword=keyword,
        shazam_result=out,
        limit=3,
    )

    # 4) Build final name (if renaming)
    if plex_structure:
        new_name = f"{s_title}{ext}"
    else:
        new_name = f"{s_title} - {s_artist} - {s_album}{ext}"

    # 5) Determine target directory
    root_dir = copy_to or output_dir or os.path.dirname(file_path)
    if plex_structure:
        root_dir = os.path.join(root_dir, s_artist, s_album)
    os.makedirs(root_dir, exist_ok=True)

    # 6) Unique filename
    new_path = os.path.join(root_dir, new_name)
    count = 1
    while os.path.exists(new_path) and new_path != file_path:
        stem, e2 = os.path.splitext(new_path)
        new_path = f"{stem} ({count}){e2}"
        count += 1

    # 7) Tag-only branch: update tags on original file
    if tag_only and modify:
        try:
            if ext == ".mp3":
                update_mp3_tags(file_path, s_title, s_artist, s_album)
                if cover:
                    update_mp3_cover_art(file_path, cover, trace)
            else:
                update_ogg_tags(
                    file_path, s_title, s_artist, s_album, cover, trace
                )
        except Exception as exc:
            return {
                "file_path": file_path,
                "error": f"Tag error: {exc}",
                "search_results": [sr.to_dict() for sr in search_results],
            }
        return {
            "file_path": file_path,
            "new_file_path": file_path,
            "title": s_title,
            "author": s_artist,
            "album": s_album,
            "cover_link": cover,
            "search_results": [sr.to_dict() for sr in search_results],
        }

    # 8) Move or copy & tag
    if modify and not tag_only:
        try:
            if copy_to:
                shutil.copy2(file_path, new_path)
            else:
                os.rename(file_path, new_path)

            if ext == ".mp3":
                update_mp3_tags(new_path, s_title, s_artist, s_album)
                if cover:
                    update_mp3_cover_art(new_path, cover, trace)
            else:
                update_ogg_tags(
                    new_path, s_title, s_artist, s_album, cover, trace
                )
        except Exception as exc:
            return {
                "file_path": file_path,
                "error": f"Tag error: {exc}",
                "search_results": [sr.to_dict() for sr in search_results],
            }

    return {
        "file_path": file_path,
        "new_file_path": new_path,
        "title": s_title,
        "author": s_artist,
        "album": s_album,
        "cover_link": cover,
        "search_results": [sr.to_dict() for sr in search_results],
    }


def update_mp3_cover_art(file_path: str, cover_url: str, trace: bool) -> None:
    if not cover_url:
        if trace:
            print("No cover art:", file_path)
        return
    audio = eyed3.load(file_path)
    if audio.tag is None:
        audio.initTag()
    img = urlopen(cover_url).read()
    audio.tag.images.set(3, img, "image/jpeg", "cover")
    audio.tag.save()


def update_mp3_tags(
    file_path: str, title: str, artist: str, album: str
) -> None:
    audio = eyed3.load(file_path)
    if not audio:
        return
    if audio.tag is None:
        audio.initTag()
    audio.tag.title = title
    audio.tag.artist = artist
    audio.tag.album = album
    audio.tag.save()


def update_ogg_tags(
    file_path: str,
    title: str,
    artist: str,
    album: str,
    cover_url: str,
    trace: bool,
) -> None:
    # Try Vorbis, then Opus, then generic
    try:
        audio = OggVorbis(file_path)
    except Exception:
        try:
            audio = OggOpus(file_path)
        except Exception:
            audio = File(file_path)
            if audio is None:
                raise RuntimeError("Unsupported OGG type for tagging")

    audio["TITLE"] = [title]
    audio["ARTIST"] = [artist]
    audio["ALBUM"] = [album]

    if cover_url:
        try:
            img = urlopen(cover_url).read()
            pic = Picture()
            pic.data = img
            pic.type = 3
            pic.mime = "image/jpeg"
            pic.width = pic.height = pic.depth = pic.colors = 0
            b64 = base64.b64encode(pic.write()).decode("ascii")
            audio["METADATA_BLOCK_PICTURE"] = [b64]
        except Exception as exc:
            if trace:
                print("Cover art error:", exc)
    elif trace:
        print("No cover art for OGG:", file_path)

    audio.save()
