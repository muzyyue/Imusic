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
    for section in track.get("sections", []):
        if section.get("type") == "SONG":
            duration = section.get("metadata", {}).get("duration", 0) or 0
            break

    return SearchResult(
        source="shazam",
        title=title,
        artist=artist,
        album=album,
        cover_link=cover,
        duration=duration,
        confidence=1.0,  # Shazam 基于音频指纹，置信度最高
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


async def _search_netease(keyword: str, limit: int = 5) -> list[SearchResult]:
    """
    异步搜索网易云音乐

    Args:
        keyword: 搜索关键词
        limit: 返回结果数量

    Returns:
        list[SearchResult]: 搜索结果列表
    """
    try:
        # 使用 run_in_executor 在线程池中执行阻塞的 API 调用
        loop = asyncio.get_event_loop()

        def _do_search() -> list[SearchResult]:
            try:
                from MusicLibrary.neteaseCloudMusicApi import NeteaseCloudMusicApi

                api = NeteaseCloudMusicApi()
                result = api.search(keyword, limit=limit)

                if not result or "result" not in result:
                    return []

                songs = result["result"].get("songs", [])
                return [_parse_netease_result(song) for song in songs[:limit]]
            except ImportError:
                return []
            except Exception:
                return []

        return await loop.run_in_executor(None, _do_search)
    except Exception:
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
    try:
        loop = asyncio.get_event_loop()

        def _do_search() -> list[SearchResult]:
            try:
                from MusicLibrary.kuGouMusicApi import KuGouMusicApi

                api = KuGouMusicApi()
                result = api.search(keyword, limit=limit)

                if not result or "data" not in result:
                    return []

                songs = result["data"].get("lists", []) if isinstance(result["data"], dict) else []
                return [_parse_kugou_result(song) for song in songs[:limit]]
            except ImportError:
                return []
            except Exception:
                return []

        return await loop.run_in_executor(None, _do_search)
    except Exception:
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

    # 如果已有 Shazam 结果，直接解析
    if shazam_result and "track" in shazam_result:
        shazam_result_obj = _parse_shazam_result(shazam_result["track"])
        all_results.append(shazam_result_obj)

    # 并发搜索网易云和酷狗
    netease_task = asyncio.create_task(_search_netease(keyword, limit))
    kugou_task = asyncio.create_task(_search_kugou(keyword, limit))

    # 等待两个平台搜索完成（优雅降级：失败的返回空列表）
    netease_results, kugou_results = await asyncio.gather(
        netease_task, kugou_task, return_exceptions=True
    )

    # 处理异常结果
    if isinstance(netease_results, Exception):
        netease_results = []
    if isinstance(kugou_results, Exception):
        kugou_results = []

    all_results.extend(netease_results)  # type: ignore[arg-type]
    all_results.extend(kugou_results)  # type: ignore[arg-type]

    # 按置信度降序排序
    all_results.sort(key=lambda x: x.confidence, reverse=True)

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
