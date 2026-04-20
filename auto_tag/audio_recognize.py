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
import logging
import os
import shutil
import tempfile
from typing import Any
from urllib.request import urlopen

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

# 导入全局 MusicLibrary 管理器
from auto_tag.music_library_manager import (
    get_thread_local_netease_api,
    get_thread_local_kugou_api,
    is_permanently_failed,
)


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
    异步搜索网易云音乐

    Args:
        keyword: 搜索关键词
        limit: 返回结果数量

    Returns:
        list[SearchResult]: 搜索结果列表
    """
    # 快速检查：如果原生库已永久失败，直接返回空列表
    if is_permanently_failed():
        logger.info(f"[NetEase] Skipping search (native library disabled): {keyword}")
        return []
    
    try:
        def _do_search() -> list[SearchResult]:
            # 再次检查（线程安全）
            if is_permanently_failed():
                return []
            
            try:
                api = get_thread_local_netease_api()
                if api is None:
                    logger.warning("[NetEase] Thread-local API not available")
                    return []
                    
                logger.info(f"[NetEase] Searching: {keyword}")
                response = api.search(keyword, limit=limit)
                result = _extract_response_data(response)

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
            future = executor.submit(_do_search.__wrapped__ if hasattr(_do_search, '__wrapped__') else _do_search())
            return future.result(timeout=30)
    except Exception as e:
        logger.error(f"[NetEase] Async error: {e}", exc_info=True)
        return []


async def _search_kugou(keyword: str, limit: int = 5) -> list[SearchResult]:
    """
    异步搜索酷狗音乐

    Args:
        keyword: 搜索关键词
        limit: 返回结果数量

    Returns:
        list[SearchResult]: 搜索结果列表
    """
    # 快速检查：如果原生库已永久失败，直接返回空列表
    if is_permanently_failed():
        logger.info(f"[KuGou] Skipping search (native library disabled): {keyword}")
        return []
    
    try:
        def _do_search_kugou() -> list[SearchResult]:
            # 再次检查（线程安全）
            if is_permanently_failed():
                return []
            
            try:
                api = get_thread_local_kugou_api()
                if api is None:
                    logger.warning("[KuGou] Thread-local API not available")
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

    # 如果原生库已永久失败，直接返回（只使用 Shazam 结果）
    if is_permanently_failed():
        logger.info("[MultiSource] Native library permanently failed, skipping NetEase/KuGou")
        return all_results

    # 并发搜索网易云和酷狗
    logger.info(f"[MultiSource] Launching concurrent searches for NetEase and KuGou...")
    netease_task = asyncio.create_task(_search_netease(keyword, limit))
    kugou_task = asyncio.create_task(_search_kugou(keyword, limit))

    # 等待两个平台搜索完成（优雅降级：失败的返回空列表）
    netease_results, kugou_results = await asyncio.gather(
        netease_task, kugou_task, return_exceptions=True
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

    if isinstance(kugou_results, Exception):
        logger.error(f"[MultiSource] KuGou search exception: {kugou_results}", exc_info=True)
        kugou_results = []
    elif isinstance(kugou_results, list):
        logger.info(f"[MultiSource] KuGou returned {len(kugou_results)} results")
    else:
        logger.warning(f"[MultiSource] KuGou returned unexpected type: {type(kugou_results)}")
        kugou_results = []

    all_results.extend(netease_results)  # type: ignore[arg-type]
    all_results.extend(kugou_results)  # type: ignore[arg-type]

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
    # 注意：pymusiclibrary 原生 C 库在子线程中使用会导致 access violation 崩溃
    # 因此不再预初始化 MusicLibrary，多平台搜索功能依赖 Crash Protection 机制
    if is_permanently_failed():
        logger.info("[MusicLibrary] Native library permanently disabled, using Shazam only")
    
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
            print(f"Shazam failed: {file_path}")
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
