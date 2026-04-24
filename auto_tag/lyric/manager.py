# auto_tag/lyric/manager.py
"""
歌词管理器模块
提供歌词的获取、嵌入、提取和格式转换功能
"""

from __future__ import annotations

import logging
import os
from typing import Any

import eyed3
from mutagen import File
from mutagen.flac import Picture
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

from .provider import get_provider, get_provider_api
from auto_tag.audio_recognize import get_netease_api, get_kugou_api


class LyricManager:
    """
    歌词管理器类

    封装 lrxy 库功能，提供统一的歌词操作接口

    功能：
    - 从多个提供商获取歌词（LRCLib、Apple Music、MusixMatch）
    - 将歌词嵌入到音频文件
    - 从音频文件提取歌词
    - 歌词格式转换（LRC、TTML、SRT、JSON）

    支持的音频格式：
    - MP3：使用 eyed3 处理 ID3 标签（USLT/SYLT 帧）
    - FLAC：使用 mutagen.flac.FLAC（LYRICS Vorbis Comment）
    - M4A：使用 mutagen.mp4.MP4（©lyr iTunes 原子）
    - OGG：使用 mutagen.oggvorbis.OggVorbis（LYRICS Vorbis Comment）
    - OPUS：使用 mutagen.oggopus.OggOpus（LYRICS Vorbis Comment）
    """

    def __init__(self):
        """初始化歌词管理器，配置日志"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # 注意：MusicLibrary 使用 threading.local() 线程本地实例，
        # 不需要预初始化，首次调用时自动创建
        pass
    
    def _get_netease_api(self):
        """
        获取 NetEase API 实例（全局单例）

        Returns:
            NeteaseCloudMusicApi or None: 当前线程的 API 实例
        """
        return get_netease_api()

    def _get_kugou_api(self):
        """
        获取 KuGou API 实例（全局单例）

        Returns:
            KuGouMusicApi or None: 当前线程的 API 实例
        """
        return get_kugou_api()

    def fetch_lyrics(
        self,
        file_path: str,
        provider: str = 'netease',
        lyric_mode: str = 'merged'
    ) -> dict[str, Any] | None:
        """
        从指定提供商获取歌词

        Args:
            file_path: 音频文件路径
            provider: 提供商名称（'netease', 'kugou', 'lrclib', 'applemusic', 'musixmatch'）
            lyric_mode: 歌词模式（仅对网易云音乐有效）
                - 'original': 仅返回原始歌词
                - 'merged': 返回原始歌词和翻译歌词合并（默认）
                - 'translation': 仅返回翻译歌词

        Returns:
            dict | None: 歌词数据字典，格式为：
                {
                    'plain_lyrics': str,      # 纯文本歌词
                    'synced_lyrics': str,     # 同步歌词（LRC 格式）
                    'provider': str,          # 提供商名称
                    'track_name': str,        # 歌曲名称
                    'artist_name': str,       # 艺术家
                    'album_name': str,        # 专辑名
                    'duration': int           # 时长（秒）
                }
            获取失败返回 None

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的提供商或歌词模式

        Example:
            >>> manager = LyricManager()
            >>> # 获取合并歌词（默认）
            >>> lyrics = manager.fetch_lyrics('song.mp3', 'netease')
            >>> # 获取原始歌词
            >>> lyrics = manager.fetch_lyrics('song.mp3', 'netease', lyric_mode='original')
            >>> # 获取翻译歌词
            >>> lyrics = manager.fetch_lyrics('song.mp3', 'netease', lyric_mode='translation')
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 验证提供商
        provider_config = get_provider(provider)
        if not provider_config:
            raise ValueError(f"不支持的提供商: {provider}")
        
        # 验证歌词模式
        valid_modes = ['original', 'merged', 'translation']
        if lyric_mode not in valid_modes:
            raise ValueError(f"不支持的歌词模式: {lyric_mode}, 支持的模式: {valid_modes}")

        # 根据提供商类型选择不同的处理方式
        if provider in ['netease', 'kugou']:
            return self._fetch_lyrics_from_music_api(file_path, provider, lyric_mode)
        else:
            return self._fetch_lyrics_from_lrxy(file_path, provider)

    def search_songs(
        self,
        file_path: str,
        provider: str = 'netease'
    ) -> list[dict[str, Any]]:
        """
        搜索歌曲（仅返回搜索结果列表，不获取歌词）

        Args:
            file_path: 音频文件路径
            provider: 提供商名称（'netease', 'kugou'）

        Returns:
            list[dict]: 搜索结果列表，每个字典包含：
                - id: 歌曲 ID
                - name: 歌曲名称
                - artist: 艺术家名称
                - album: 专辑名称
                - duration: 时长（秒）

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的提供商

        Example:
            >>> manager = LyricManager()
            >>> results = manager.search_songs('song.mp3', 'netease')
            >>> for song in results:
            ...     print(f"{song['name']} - {song['artist']}")
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 验证提供商
        provider_config = get_provider(provider)
        if not provider_config:
            raise ValueError(f"不支持的提供商: {provider}")

        # 只支持 netease 和 kugou 的搜索功能
        if provider not in ['netease', 'kugou']:
            self.logger.warning(f"提供商 {provider} 不支持搜索功能")
            return []

        try:
            # 从音频文件提取元数据
            metadata = self._extract_audio_metadata(file_path)
            if not metadata:
                self.logger.error(f"无法提取音频元数据: {file_path}")
                return []

            # 调试日志：输出提取到的元数据
            self.logger.info(f"[DEBUG] 提取到元数据: {metadata}")

            import re

            title = metadata.get('title', '').strip()
            artist = metadata.get('artist', '').strip()

            # 如果标题和艺术家都为空，尝试从文件名解析
            if not title and not artist:
                filename = os.path.basename(file_path)
                self.logger.warning(f"ID3标签为空，使用文件名: {filename}")
                name_without_ext = os.path.splitext(filename)[0]
                if ' - ' in name_without_ext:
                    parts = name_without_ext.split(' - ', 1)
                    artist = parts[0].strip()
                    title = parts[1].strip() if len(parts) > 1 else ''
                else:
                    title = name_without_ext

            # 构建搜索关键词（优化策略：保留更多原始信息以提高匹配度）
            keyword = self._build_search_keyword(title, artist)
            self.logger.info(f"[DEBUG] 搜索关键词: '{keyword}' (原始title='{title}', 原始artist='{artist}')")

            # 使用 pymusiclibrary 原生库进行搜索（已包含认证信息，最可靠）
            api = self._get_kugou_api() if provider == 'kugou' else self._get_netease_api()
            if api is None:
                self.logger.warning(f"[Search] {provider} API 不可用，尝试 REST API 备用方案")
                # pymusiclibrary 不可用时，直接使用 REST API 搜索
                songs = self._search_netease_rest_api(keyword)
                self.logger.info(f"搜索完成(REST): {keyword}, 找到 {len(songs)} 首歌曲")
                return songs

            try:
                search_result = api.search(keyword)

                if not search_result or not hasattr(search_result, 'body'):
                    self.logger.warning(f"[Search] {provider} API 搜索无返回，尝试 REST API 备用方案")
                    songs = self._search_netease_rest_api(keyword)
                    self.logger.info(f"搜索完成(REST fallback): {keyword}, 找到 {len(songs)} 首歌曲")
                    return songs

                songs = self._parse_search_result(search_result.body, provider)
                self.logger.info(f"搜索完成: {keyword}, 找到 {len(songs)} 首歌曲")

                # 如果 pymusiclibrary 解析后结果为空，尝试 REST API 备用方案
                if not songs and provider == 'netease':
                    self.logger.warning(f"[Search] pymusiclibrary 未返回结果，尝试 REST API 备用方案")
                    songs = self._search_netease_rest_api(keyword)
                    self.logger.info(f"搜索完成(REST fallback): {keyword}, 找到 {len(songs)} 首歌曲")

                return songs
            except Exception as e:
                self.logger.error(f"[Search] pymusiclibrary 搜索异常: {e}，尝试 REST API 备用方案")
                songs = self._search_netease_rest_api(keyword)
                self.logger.info(f"搜索完成(REST fallback): {keyword}, 找到 {len(songs)} 首歌曲")
                return songs

        except ImportError as e:
            self.logger.error(f"导入 MusicLibrary 库失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"搜索歌曲失败: {file_path}, 错误: {e}")
            return []

    def _build_search_keyword(self, title: str, artist: str) -> str:
        """
        构建搜索关键词

        策略：优先使用完整标题（不过度清理），REST API 本身支持模糊匹配
        如果标题为空或太短，则组合艺术家和标题

        Args:
            title (str): 歌曲标题
            artist (str): 艺术家名称

        Returns:
            str: 构建好的搜索关键词
        """
        import re

        if title:
            # 只清理明显的版本后缀，保留核心歌名
            clean_title = re.sub(
                r'\s*[\-–—]\s*(Movie|Piano|Short|Full)\s*Ver\.?\s*$'
                r'|\s*[\(\[]\s*(Live|Acoustic|Remix|Cover|Inst\.?|Instrumental)\s*[\)\]]\s*$',
                '',
                title,
                flags=re.IGNORECASE
            ).strip()

            # 优先使用完整标题（REST API 支持模糊匹配，不需要过度清理）
            if len(clean_title) >= 2:
                return clean_title
            elif artist:
                return f"{artist} {clean_title}".strip()
            return clean_title
        else:
            # 没有标题，使用艺术家
            return artist if artist else ""

    def _search_netease_rest_api(self, keyword: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        使用网易云 REST API 搜索歌曲

        直接调用网易云 Web API，比 pymusiclibrary 更稳定且搜索能力更强。
        无需登录，使用与网易云 app 相同的搜索接口。

        Args:
            keyword (str): 搜索关键词
            limit (int): 返回结果数量上限，默认10

        Returns:
            list[dict]: 搜索结果列表，每个字典包含 id, name, artist, album, duration
        """
        import json
        from urllib.request import Request, urlopen
        from urllib.parse import urlencode
        from urllib.error import URLError, HTTPError

        try:
            params = urlencode({
                's': keyword,
                'type': 1,
                'offset': 0,
                'total': 'true',
                'limit': limit
            })
            url = f'https://music.163.com/api/search/get/web?{params}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://music.163.com/',
            }
            req = Request(url, headers=headers)

            # 使用 urlopen（pymusiclibrary 初始化后会设置必要的 cookie/ssl 配置，
            # urlopen 会自动继承这些配置，使得 API 请求能正常工作）
            with urlopen(req, timeout=15) as resp:
                raw_data = resp.read().decode('utf-8')

            data = json.loads(raw_data)

            # 调试：记录原始响应结构
            if 'result' not in data:
                self.logger.warning(
                    f"[NetEase-REST] API 返回异常 (keyword='{keyword}'):"
                    f" keys={list(data.keys())}, code={data.get('code')}, msg={data.get('msg')}"
                )
                if data.get('code') and data.get('code') != 200:
                    self.logger.error(
                        f"[NetEase-REST] API 错误响应: {raw_data[:500]}"
                    )
                return []

            result_data = data.get('result', {})
            song_list = result_data.get('songs', [])

            songs = []
            for song in song_list:
                songs.append({
                    'id': song.get('id'),
                    'name': song.get('name', ''),
                    'artist': song.get('artists', [{}])[0].get('name', '') if song.get('artists') else '',
                    'album': song.get('album', {}).get('name', ''),
                    'duration': song.get('duration', 0) // 1000
                })

            self.logger.info(f"[NetEase-REST] 搜索 '{keyword}' 返回 {len(songs)} 条结果")
            return songs

        except URLError as e:
            self.logger.warning(f"[NetEase-REST] 网络错误: {e}")
            return []
        except HTTPError as e:
            self.logger.warning(f"[NetEase-REST] HTTP 错误: {e.code} - {e.reason}")
            return []
        except Exception as e:
            self.logger.error(f"[NetEase-REST] 搜索失败: {e}")
            return []

    def check_lyric_exists(
        self,
        song_id: int | str,
        provider: str = 'netease',
        timeout: int = 5
    ) -> bool:
        """
        轻量级检查歌曲是否有歌词（不下载歌词内容）

        使用 REST API 快速检测歌词是否存在，用于搜索结果列表的预览。

        Args:
            song_id: 歌曲 ID
            provider: 提供商名称
            timeout: 请求超时（秒）

        Returns:
            bool: 是否有歌词
        """
        import json
        from urllib.request import Request, urlopen
        from urllib.parse import urlencode
        from urllib.error import URLError, HTTPError

        if provider != 'netease':
            return False

        try:
            params = urlencode({'id': song_id, 'lv': -1, 'tv': -1, 'kv': -1})
            url = f'https://music.163.com/api/song/lyric?{params}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://music.163.com/',
            }
            req = Request(url, headers=headers)

            with urlopen(req, timeout=timeout) as resp:
                raw_data = resp.read().decode('utf-8')

            data = json.loads(raw_data)
            lrc_data = data.get('lrc', {})
            lyric = lrc_data.get('lyric', '') if isinstance(lrc_data, dict) else ''
            has_lyric = bool(lyric and len(lyric.strip()) > 10)

            return has_lyric

        except (URLError, HTTPError):
            return False
        except Exception:
            return False

    def fetch_lyric_by_id(
        self,
        song_id: int | str,
        provider: str = 'netease',
        lyric_mode: str = 'merged'
    ) -> dict[str, Any] | None:
        """
        根据歌曲 ID 获取歌词

        优先使用 pymusiclibrary，失败时自动回退到 REST API。

        Args:
            song_id: 歌曲 ID
            provider: 提供商名称
            lyric_mode: 歌词模式（仅对网易云音乐有效）
                - 'original': 仅返回原始歌词
                - 'merged': 返回原始歌词和翻译歌词合并（默认）
                - 'translation': 仅返回翻译歌词

        Returns:
            dict | None: 歌词数据字典
        """
        # 先尝试使用 pymusiclibrary
        result = self._fetch_lyric_by_id_pymusiclibrary(song_id, provider, lyric_mode)
        if result is not None:
            return result

        # pymusiclibrary 失败时，使用 REST API 备用方案
        if provider == 'netease':
            self.logger.info(f"[FetchLyric] pymusiclibrary 获取失败，尝试 REST API 备用方案 (ID: {song_id})")
            return self._fetch_lyric_by_id_netease_rest(song_id, lyric_mode)

        self.logger.error(f"[FetchLyric] 所有方式均获取歌词失败 (ID: {song_id}), 提供商: {provider}")
        return None

    def _fetch_lyric_by_id_pymusiclibrary(
        self,
        song_id: int | str,
        provider: str,
        lyric_mode: str
    ) -> dict[str, Any] | None:
        """
        使用 pymusiclibrary 获取歌词

        Args:
            song_id: 歌曲 ID
            provider: 提供商名称
            lyric_mode: 歌词模式

        Returns:
            dict | None: 歌词数据字典，失败返回 None
        """
        try:
            # 根据提供商获取对应的 API 客户端
            if provider == 'netease':
                api = self._get_netease_api()
            else:
                api = self._get_kugou_api()

            if api is None:
                self.logger.debug(f"[FetchLyric] pymusiclibrary {provider} API 不可用")
                return None

            # 获取歌词
            lyric_data = api.lyric(id=song_id)

            if not lyric_data or not hasattr(lyric_data, 'body'):
                return None

            body = lyric_data.body

            # 解析歌词数据
            synced_lyrics = ''
            plain_lyrics = ''

            if provider == 'netease':
                lrc_data = body.get('lrc', {})
                tlyric_data = body.get('tlyric', {})
                lrc_lyric = lrc_data.get('lyric', '') if isinstance(lrc_data, dict) else ''
                tlyric_lyric = tlyric_data.get('lyric', '') if isinstance(tlyric_data, dict) else ''

                # 根据歌词模式返回不同的内容
                if lyric_mode == 'original':
                    synced_lyrics = lrc_lyric
                    plain_lyrics = ''
                elif lyric_mode == 'merged':
                    synced_lyrics = self._merge_lyrics_with_translation(lrc_lyric, tlyric_lyric)
                    plain_lyrics = tlyric_lyric
                elif lyric_mode == 'translation':
                    synced_lyrics = tlyric_lyric
                    plain_lyrics = ''
            else:
                synced_lyrics = body.get('lyrics', '')

            if not (synced_lyrics or plain_lyrics):
                return None

            result = {
                'synced_lyrics': synced_lyrics,
                'plain_lyrics': plain_lyrics,
                'provider': provider,
                'track_name': '',
                'artist_name': '',
                'album_name': '',
                'duration': 0
            }

            self.logger.info(f"[FetchLyric] pymusiclibrary 成功获取歌词 (ID: {song_id})")
            return result

        except Exception as e:
            self.logger.debug(f"[FetchLyric] pymusiclibrary 获取歌词失败 (ID: {song_id}): {e}")
            return None

    def _fetch_lyric_by_id_netease_rest(
        self,
        song_id: int | str,
        lyric_mode: str = 'merged'
    ) -> dict[str, Any] | None:
        """
        使用 REST API 获取网易云歌词（备用方案）

        Args:
            song_id: 歌曲 ID
            lyric_mode: 歌词模式

        Returns:
            dict | None: 歌词数据字典，失败返回 None
        """
        import json
        from urllib.request import Request, urlopen
        from urllib.parse import urlencode
        from urllib.error import URLError, HTTPError

        try:
            params = urlencode({'id': song_id, 'lv': -1, 'tv': -1, 'kv': -1})
            url = f'https://music.163.com/api/song/lyric?{params}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://music.163.com/',
            }
            req = Request(url, headers=headers)

            with urlopen(req, timeout=10) as resp:
                raw_data = resp.read().decode('utf-8')

            data = json.loads(raw_data)
            lrc_data = data.get('lrc', {})
            tlyric_data = data.get('tlyric', {})

            lrc_lyric = lrc_data.get('lyric', '') if isinstance(lrc_data, dict) else ''
            tlyric_lyric = tlyric_data.get('lyric', '') if isinstance(tlyric_data, dict) else ''

            synced_lyrics = ''
            plain_lyrics = ''

            if lyric_mode == 'original':
                synced_lyrics = lrc_lyric
                plain_lyrics = ''
            elif lyric_mode == 'merged':
                synced_lyrics = self._merge_lyrics_with_translation(lrc_lyric, tlyric_lyric)
                plain_lyrics = tlyric_lyric
            elif lyric_mode == 'translation':
                synced_lyrics = tlyric_lyric
                plain_lyrics = ''

            if not (synced_lyrics or plain_lyrics):
                return None

            result = {
                'synced_lyrics': synced_lyrics,
                'plain_lyrics': plain_lyrics,
                'provider': 'netease',
                'track_name': '',
                'artist_name': '',
                'album_name': '',
                'duration': 0
            }

            self.logger.info(f"[FetchLyric] REST API 成功获取歌词 (ID: {song_id})")
            return result

        except (URLError, HTTPError) as e:
            self.logger.error(f"[FetchLyric] REST API 歌词请求失败 (ID: {song_id}): {e}")
            return None
        except Exception as e:
            self.logger.error(f"[FetchLyric] REST API 获取歌词失败 (ID: {song_id}): {e}")
            return None

    def _fetch_lyrics_from_music_api(
        self,
        file_path: str,
        provider: str,
        lyric_mode: str = 'merged'
    ) -> dict[str, Any] | None:
        """
        从网易云音乐或酷狗音乐获取歌词

        Args:
            file_path: 音频文件路径
            provider: 提供商名称（'netease' 或 'kugou'）
            lyric_mode: 歌词模式（仅对网易云音乐有效）
                - 'original': 仅返回原始歌词
                - 'merged': 返回原始歌词和翻译歌词合并（默认）
                - 'translation': 仅返回翻译歌词

        Returns:
            dict | None: 歌词数据字典
        """
        try:
            # 根据提供商获取对应的 API 客户端
            if provider == 'netease':
                api = self._get_netease_api()
            else:
                api = self._get_kugou_api()
            
            if api is None:
                self.logger.error(f"无法初始化 {provider} API")
                return None

            # 从音频文件提取元数据
            metadata = self._extract_audio_metadata(file_path)
            if not metadata:
                self.logger.error(f"无法提取音频元数据: {file_path}")
                return None

            # 搜索歌曲
            keyword = f"{metadata['artist']} {metadata['title']}"
            search_result = api.search(keyword)

            if not search_result or not hasattr(search_result, 'body'):
                self.logger.warning(f"搜索歌曲失败: {keyword}")
                return None

            # 解析搜索结果（Response 对象的 body 属性包含实际数据）
            self.logger.debug(f"搜索结果 body 类型: {type(search_result.body)}")
            self.logger.debug(f"搜索结果 body keys: {list(search_result.body.keys()) if isinstance(search_result.body, dict) else 'N/A'}")

            songs = self._parse_search_result(search_result.body, provider)
            self.logger.debug(f"解析后歌曲数: {len(songs)}")

            if not songs:
                self.logger.warning(f"未找到匹配的歌曲: {keyword}")
                # 打印详细的调试信息
                if isinstance(search_result.body, dict):
                    result_data = search_result.body.get('result', {})
                    song_list = result_data.get('songs', [])
                    self.logger.error(f"原始歌曲列表长度: {len(song_list)}")
                    if song_list:
                        self.logger.error(f"第一首歌: {song_list[0]}")
                return None

            # 尝试获取最匹配的歌曲的歌词
            for song in songs[:3]:  # 只尝试前3个结果
                song_id = song['id']
                lyric_data = api.lyric(id=song_id)

                if lyric_data and hasattr(lyric_data, 'body'):
                    # 解析歌词数据（Response 对象的 body 属性包含实际数据）
                    body = lyric_data.body
                    
                    # 解析歌词数据
                    synced_lyrics = ''
                    plain_lyrics = ''

                    if provider == 'netease':
                        # 网易云音乐歌词格式
                        lrc_data = body.get('lrc', {})
                        tlyric_data = body.get('tlyric', {})
                        lrc_lyric = lrc_data.get('lyric', '') if isinstance(lrc_data, dict) else ''
                        tlyric_lyric = tlyric_data.get('lyric', '') if isinstance(tlyric_data, dict) else ''
                        
                        # 根据歌词模式返回不同的内容
                        if lyric_mode == 'original':
                            # 仅返回原始歌词
                            synced_lyrics = lrc_lyric
                            plain_lyrics = ''
                        elif lyric_mode == 'merged':
                            # 合并原始歌词和翻译歌词（一句原始+一句翻译交替排列）
                            synced_lyrics = self._merge_lyrics_with_translation(lrc_lyric, tlyric_lyric)
                            plain_lyrics = tlyric_lyric  # 保留纯翻译歌词
                        elif lyric_mode == 'translation':
                            # 仅返回翻译歌词
                            synced_lyrics = tlyric_lyric
                            plain_lyrics = ''
                    else:
                        # 酷狗音乐歌词格式
                        synced_lyrics = body.get('lyrics', '')

                    if synced_lyrics or plain_lyrics:
                        self.logger.info(
                            f"成功获取歌词: {file_path}, 提供商: {provider}"
                        )
                        return {
                            'plain_lyrics': plain_lyrics,
                            'synced_lyrics': synced_lyrics,
                            'provider': provider,
                            'track_name': song.get('name', metadata['title']),
                            'artist_name': song.get('artist', metadata['artist']),
                            'album_name': song.get('album', metadata['album']),
                            'duration': song.get('duration', metadata['duration'])
                        }

            self.logger.warning(f"未找到歌词: {file_path}")
            return None

        except ImportError as e:
            self.logger.error(f"导入 pymusiclibrary 库失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取歌词失败: {file_path}, 错误: {e}")
            return None

    def _fetch_lyrics_from_lrxy(
        self,
        file_path: str,
        provider: str
    ) -> dict[str, Any] | None:
        """
        从 lrxy 库支持的提供商获取歌词（兼容旧代码）

        Args:
            file_path: 音频文件路径
            provider: 提供商名称

        Returns:
            dict | None: 歌词数据字典
        """
        try:
            # 导入 lrxy 库
            from lrxy.utils import load_audio

            # 加载音频文件
            audio = load_audio(file_path)
            if audio is None:
                self.logger.error(f"无法加载音频文件: {file_path}")
                return None

            # 获取提供商 API 函数
            provider_api = get_provider_api(provider)
            if provider_api is None:
                self.logger.error(f"无法加载提供商 API: {provider}")
                return None

            # 构建元数据
            metadata = {
                'artist': getattr(audio, 'artist_name', '') or getattr(audio, 'artist', ''),
                'title': getattr(audio, 'track_name', '') or getattr(audio, 'title', ''),
                'album': getattr(audio, 'album_name', '') or getattr(audio, 'album', ''),
                'duration': str(int(getattr(audio, 'duration', 0)))
            }

            # 调用 provider API 获取歌词
            result = provider_api(metadata)

            if not result.get('success'):
                error = result.get('error', '未知错误')
                message = result.get('message', '')
                self.logger.warning(f"获取歌词失败: {file_path}, 错误: {error}, 详情: {message}")
                return None

            data = result.get('data', {})
            lyric_data = data.get('lyric', {})

            # 构建返回数据
            lyrics_data = {
                'plain_lyrics': lyric_data.get('plainLyrics', ''),
                'synced_lyrics': lyric_data.get('syncedLyrics', ''),
                'provider': provider,
                'track_name': metadata['title'],
                'artist_name': metadata['artist'],
                'album_name': metadata['album'],
                'duration': int(metadata['duration'])
            }

            self.logger.info(
                f"成功获取歌词: {file_path}, 提供商: {provider}"
            )
            return lyrics_data

        except ImportError as e:
            self.logger.error(f"导入 lrxy 库失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取歌词失败: {file_path}, 错误: {e}")
            return None

    def _merge_lyrics_with_translation(
        self,
        original_lrc: str,
        translation_lrc: str
    ) -> str:
        """
        合并原始歌词和翻译歌词（一句原始+一句翻译交替排列）
        
        Args:
            original_lrc: 原始歌词（LRC格式）
            translation_lrc: 翻译歌词（LRC格式）
        
        Returns:
            str: 合并后的歌词（LRC格式）
        
        Example:
            >>> manager = LyricManager()
            >>> original = "[00:00.00]故事的小黄花\\n[00:05.00]从出生那年就飘着"
            >>> translation = "[00:00.00]The small yellow flower\\n[00:05.00]Has been floating since birth"
            >>> merged = manager._merge_lyrics_with_translation(original, translation)
            >>> print(merged)
            [00:00.00]故事的小黄花
            [00:00.00]The small yellow flower
            [00:05.00]从出生那年就飘着
            [00:05.00]Has been floating since birth
        """
        import re
        
        # 如果没有翻译歌词，直接返回原始歌词
        if not translation_lrc or not translation_lrc.strip():
            return original_lrc
        
        # 如果没有原始歌词，返回空字符串
        if not original_lrc or not original_lrc.strip():
            return ''
        
        # 解析原始歌词为列表 [(时间戳字符串, 歌词文本), ...]
        original_lines = self._parse_lrc_to_list(original_lrc)
        
        # 解析翻译歌词为字典 {时间戳字符串: 歌词文本}
        translation_dict = self._parse_lrc_to_dict(translation_lrc)
        
        # 合并歌词
        merged_lines = []
        for timestamp, text in original_lines:
            # 添加原始歌词行
            merged_lines.append(f"[{timestamp}]{text}")
            
            # 查找对应时间戳的翻译
            if timestamp in translation_dict and translation_dict[timestamp]:
                # 添加翻译歌词行（使用相同的时间戳）
                merged_lines.append(f"[{timestamp}]{translation_dict[timestamp]}")
        
        return '\n'.join(merged_lines)
    
    def _parse_lrc_to_list(self, lrc_content: str) -> list[tuple[str, str]]:
        """
        解析LRC歌词为列表格式
        
        Args:
            lrc_content: LRC格式歌词内容
        
        Returns:
            list[tuple[str, str]]: [(时间戳字符串, 歌词文本), ...]
        
        Example:
            >>> manager = LyricManager()
            >>> lrc = "[00:00.00]第一行\\n[00:05.00]第二行"
            >>> result = manager._parse_lrc_to_list(lrc)
            >>> print(result)
            [('00:00.00', '第一行'), ('00:05.00', '第二行')]
        """
        import re
        
        lines = []
        # LRC格式：[mm:ss.xx]歌词文本 或 [mm:ss.xxx]歌词文本
        pattern = r'\[(\d{2}:\d{2}\.\d{2,3})\](.*)'
        
        for line in lrc_content.split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                timestamp = match.group(1)
                text = match.group(2).strip()
                # 只添加非空歌词行
                if text:
                    lines.append((timestamp, text))
        
        return lines
    
    def _parse_lrc_to_dict(self, lrc_content: str) -> dict[str, str]:
        """
        解析LRC歌词为字典格式
        
        Args:
            lrc_content: LRC格式歌词内容
        
        Returns:
            dict[str, str]: {时间戳字符串: 歌词文本}
        
        Example:
            >>> manager = LyricManager()
            >>> lrc = "[00:00.00]第一行\\n[00:05.00]第二行"
            >>> result = manager._parse_lrc_to_dict(lrc)
            >>> print(result)
            {'00:00.00': '第一行', '00:05.00': '第二行'}
        """
        import re
        
        lrc_dict = {}
        # LRC格式：[mm:ss.xx]歌词文本 或 [mm:ss.xxx]歌词文本
        pattern = r'\[(\d{2}:\d{2}\.\d{2,3})\](.*)'
        
        for line in lrc_content.split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                timestamp = match.group(1)
                text = match.group(2).strip()
                # 只添加非空歌词行
                if text:
                    lrc_dict[timestamp] = text
        
        return lrc_dict

    @staticmethod
    def parse_lrc_duration(lrc_text: str) -> float:
        """
        解析 LRC 歌词文本，提取总时长（秒）

        通过正则表达式匹配所有时间戳 [mm:ss.xx] 或 [mm:ss.xxx]，
        返回最大的时间值作为歌词总时长。

        Args:
            lrc_text (str): LRC 格式的歌词文本

        Returns:
            float: 歌词总时长（秒），无法解析时返回 0.0

        Example:
            >>> lrc = "[00:00.00]故事的小黄花\\n[04:29.65]从出生那年就飘着"
            >>> duration = LyricManager.parse_lrc_duration(lrc)
            >>> print(f"歌词总时长: {duration:.2f} 秒")
            歌词总时长: 269.65 秒
        """
        if not lrc_text or not isinstance(lrc_text, str):
            return 0.0

        import re

        # 匹配 LRC 时间戳格式：[mm:ss.xx] 或 [mm:ss.xxx]
        # 支持毫秒精度为 2 位或 3 位
        pattern = r'\[(\d{1,2}):(\d{2})\.(\d{2,3})\]'
        matches = re.findall(pattern, lrc_text)

        if not matches:
            return 0.0

        max_duration = 0.0
        for minutes, seconds, milliseconds in matches:
            try:
                # 转换为秒
                total_seconds = (
                    int(minutes) * 60 +
                    int(seconds) +
                    int(milliseconds.ljust(3, '0')[:3]) / 1000.0  # 统一为 3 位毫秒
                )
                if total_seconds > max_duration:
                    max_duration = total_seconds
            except (ValueError, IndexError):
                continue

        return round(max_duration, 2)

    @staticmethod
    def calculate_duration_match_ratio(
        song_duration: float,
        lyric_duration: float,
        threshold: float = 0.10
    ) -> dict[str, Any]:
        """
        计算歌曲时长与歌词时长的匹配度

        对比音频文件实际时长和歌词总时长，
        计算差异百分比并判断是否在可接受范围内。

        Args:
            song_duration (float): 歌曲实际时长（秒）
            lyric_duration (float): 歌词总时长（秒）
            threshold (float): 允许的差异阈值（默认 10%）

        Returns:
            dict: 匹配结果字典，包含：
                - song_duration: 歌曲时长（格式化字符串）
                - lyric_duration: 歌词时长（格式化字符串）
                - difference: 差异（秒）
                - ratio: 差异百分比
                - is_match: 是否匹配（布尔值）
                - match_level: 匹配等级 ('excellent' | 'good' | 'warning' | 'mismatch')
                - message: 提示消息

        Example:
            >>> result = LyricManager.calculate_duration_match_ratio(269, 265)
            >>> print(result['match_level'])
            excellent
        """
        if song_duration <= 0 or lyric_duration <= 0:
            return {
                'song_duration': '--:--',
                'lyric_duration': '--:--',
                'difference': 0,
                'ratio': 0,
                'is_match': False,
                'match_level': 'unknown',
                'message': tr('duration_unknown') if 'tr' in dir() else '时长信息未知'
            }

        # 计算差异
        difference = abs(song_duration - lyric_duration)
        ratio = difference / song_duration if song_duration > 0 else 1.0

        # 格式化时长显示
        def format_duration(seconds: float) -> str:
            if seconds <= 0:
                return '--:--'
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins:02d}:{secs:02d}"

        # 判断匹配等级
        if ratio <= 0.03:  # 差异 ≤ 3%
            match_level = 'excellent'
            is_match = True
            message = tr('duration_excellent_match') if 'tr' in dir() else '时长完美匹配'
        elif ratio <= 0.07:  # 差异 ≤ 7%
            match_level = 'good'
            is_match = True
            message = tr('duration_good_match') if 'tr' in dir() else '时长基本匹配'
        elif ratio <= threshold:  # 差异 ≤ 阈值（默认 10%）
            match_level = 'warning'
            is_match = True
            message = tr('duration_warning') if 'tr' in dir() else f'时长差异 {ratio*100:.1f}%，请确认'
        else:  # 差异 > 阈值
            match_level = 'mismatch'
            is_match = False
            message = tr('duration_mismatch') if 'tr' in dir() else f'时长差异过大 ({ratio*100:.1f}%)，可能不匹配'

        return {
            'song_duration': format_duration(song_duration),
            'lyric_duration': format_duration(lyric_duration),
            'difference': round(difference, 2),
            'ratio': round(ratio * 100, 2),
            'is_match': is_match,
            'match_level': match_level,
            'message': message
        }

    def _extract_audio_metadata(self, file_path: str) -> dict[str, Any] | None:
        """
        从音频文件提取元数据

        Args:
            file_path: 音频文件路径

        Returns:
            dict | None: 元数据字典，包含 title, artist, album, duration
        """
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.mp3':
                audio = eyed3.load(file_path)
                if audio and audio.tag:
                    return {
                        'title': audio.tag.title or '',
                        'artist': audio.tag.artist or '',
                        'album': audio.tag.album or '',
                        'duration': int(audio.info.time_secs) if audio.info else 0
                    }
            else:
                audio = File(file_path)
                if audio:
                    return {
                        'title': audio.get('title', [''])[0],
                        'artist': audio.get('artist', [''])[0],
                        'album': audio.get('album', [''])[0],
                        'duration': int(audio.info.length) if audio.info else 0
                    }
        except Exception as e:
            self.logger.error(f"提取元数据失败: {file_path}, 错误: {e}")

        return None

    def _parse_search_result(
        self,
        result: dict[str, Any],
        provider: str
    ) -> list[dict[str, Any]]:
        """
        解析搜索结果

        Args:
            result: API 返回的搜索结果
            provider: 提供商名称

        Returns:
            list[dict]: 标准化的歌曲列表
        """
        songs = []

        try:
            if provider == 'netease':
                # 网易云音乐搜索结果格式
                result_data = result.get('result', {})
                song_list = result_data.get('songs', [])

                for song in song_list:
                    songs.append({
                        'id': song.get('id'),
                        'name': song.get('name', ''),
                        'artist': song.get('artists', [{}])[0].get('name', '') if song.get('artists') else '',
                        'album': song.get('album', {}).get('name', ''),
                        'duration': song.get('duration', 0) // 1000  # 转换为秒
                    })
            else:
                # 酷狗音乐搜索结果格式
                # 格式: {"data": {"lists": [...]}}
                data = result.get('data', {})
                song_list = data.get('lists', [])
                
                for song in song_list:
                    songs.append({
                        'id': song.get('Hash') or song.get('hash'),
                        'name': song.get('SongName') or song.get('songname', ''),
                        'artist': song.get('SingerName') or song.get('singername', ''),
                        'album': song.get('AlbumName') or song.get('album_name', ''),
                        'duration': song.get('Duration', song.get('duration', 0))
                    })

        except Exception as e:
            self.logger.error(f"解析搜索结果失败: {e}")

        return songs

    def embed_lyrics(
        self,
        file_path: str,
        lyrics: str,
        format: str = 'lrc',
        mode: str = 'embed_only'
    ) -> bool:
        """
        将歌词嵌入到音频文件

        Args:
            file_path: 音频文件路径
            lyrics: 歌词内容（LRC、TTML、SRT 或 JSON 格式）
            format: 歌词格式（'lrc', 'ttml', 'srt', 'json'）
            mode: 嵌入模式
                - 'embed_only' (默认): 仅嵌入音频文件，不生成 .lrc 文件
                - 'embed_and_lrc': 嵌入音频文件 + 生成同名 .lrc 文件

        Returns:
            bool: 嵌入成功返回 True，失败返回 False

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的歌词格式或嵌入模式

        Example:
            >>> manager = LyricManager()
            >>> lyrics = "[00:00.00]第一行歌词\\n[00:05.00]第二行歌词"
            >>> success = manager.embed_lyrics('song.mp3', lyrics, 'lrc', 'embed_only')
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        supported_formats = ['lrc', 'ttml', 'srt', 'json']
        if format.lower() not in supported_formats:
            raise ValueError(
                f"不支持的歌词格式: {format}, 支持的格式: {supported_formats}"
            )

        supported_modes = ['embed_only', 'embed_and_lrc']
        if mode not in supported_modes:
            raise ValueError(
                f"不支持的嵌入模式: {mode}, 支持的模式: {supported_modes}"
            )

        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.mp3':
                return self._embed_mp3_lyrics(file_path, lyrics, format, mode)
            elif ext in ['.flac', '.m4a', '.ogg']:
                return self._embed_generic_lyrics(file_path, lyrics, format, mode)
            else:
                self.logger.warning(f"不支持的文件格式: {ext}")
                return False

        except Exception as e:
            self.logger.error(f"嵌入歌词失败: {file_path}, 错误: {e}")
            return False

    def _embed_mp3_lyrics(
        self,
        file_path: str,
        lyrics: str,
        format: str,
        mode: str = 'embed_only'
    ) -> bool:
        """
        使用 eyed3 将歌词嵌入到 MP3 文件

        Args:
            file_path: MP3 文件路径
            lyrics: 歌词内容
            format: 歌词格式
            mode: 嵌入模式 ('embed_only' 或 'embed_and_lrc')

        Returns:
            bool: 成功返回 True

        Note:
            - 优先使用 SYLT 帧（同步歌词帧，如果歌词包含时间戳）
            - 同时写入 USLT 帧（无同步歌词，广泛支持）
            - 同时写入 TXXX 帧，description 设为 'UNSYNCEDLYRICS'（iTunes 兼容）
            - 仅在 mode='embed_and_lrc' 时生成独立 .lrc 文件（网易云音乐需要）
            - **关键修复**：显式使用 ID3v2.3 版本保存（Windows Media Player 兼容性）
            - **关键修复**：USLT 帧 description 设为 'Lyrics'（非空值，播放器识别需要）
        """
        audio = eyed3.load(file_path)
        if audio is None:
            self.logger.error(f"无法加载 MP3 文件: {file_path}")
            return False

        if audio.tag is None:
            audio.initTag(version=(2, 3, 0))

        tag = audio.tag
        lyrics_embedded = False

        has_timestamps = '[' in lyrics and ']' in lyrics

        if has_timestamps:
            try:
                self._embed_synced_lyrics_frame(tag, lyrics)
                lyrics_embedded = True
            except Exception as e:
                self.logger.warning(f"SYLT 帧嵌入失败: {e}")

        try:
            self._embed_unsynced_lyrics_frame(tag, lyrics)
            lyrics_embedded = True
        except Exception as e:
            self.logger.error(f"USLT 帧嵌入失败: {e}")
            return False

        try:
            tag.user_text_frames.set(lyrics, description='UNSYNCEDLYRICS')
        except Exception as e:
            self.logger.debug(f"TXXX 帧写入失败: {e}")

        # 关键修复：显式保存为 ID3v2.3 版本，确保 Windows Media Player 等播放器兼容
        try:
            tag.save(version=eyed3.id3.ID3_V2_3)
            self.logger.debug(f"歌词已保存为 ID3v2.3: {file_path}")
        except Exception as e:
            self.logger.error(f"ID3v2.3 保存失败: {e}")
            # fallback：尝试标准保存
            try:
                tag.save()
            except Exception as e2:
                self.logger.error(f"标准保存也失败: {e2}")
                return False

        if not lyrics_embedded:
            self.logger.error("所有歌词帧都未能成功嵌入")
            return False

        if mode == 'embed_and_lrc':
            lrc_success = self._generate_lrc_file(file_path, lyrics)
            if lrc_success:
                self.logger.info(f"成功嵌入歌词并生成 LRC 文件: {file_path}")
            else:
                self.logger.warning(f"歌词嵌入成功，但 LRC 文件生成失败: {file_path}")
        else:
            self.logger.info(f"成功嵌入歌词到 MP3 (仅嵌入模式): {file_path}")

        return True

    def _embed_synced_lyrics_frame(self, tag, lyrics: str) -> None:
        """
        嵌入同步歌词（SYLT 帧）
        某些播放器（如 Foobar2000）支持此格式。
        """
        try:
            import re
            time_pattern = re.compile(r'\[(\d{2}):(\d{2})\.(\d{2,3})\]')
            matches = time_pattern.findall(lyrics)
            if not matches:
                return

            timestamp_millis = []
            for mm, ss, frac in matches:
                millis = (int(mm) * 60 + int(ss)) * 1000 + int(frac.ljust(3, '0')[:3])
                timestamp_millis.append(millis)

            text_without_tags = time_pattern.sub('', lyrics)
            lines = [line for line in text_without_tags.split('\n') if line.strip()]
            line_count = min(len(lines), len(timestamp_millis))

            if line_count == 0:
                return

            import eyed3.id3
            import struct
            timestamp_format = 1
            content_type = 1

            frame = eyed3.id3.SyltFrame()
            frame.timestamp_format = timestamp_format
            frame.content_type = content_type
            frame.language = b'eng'
            frame.content_descriptor = ''

            text_content = []
            for i in range(line_count):
                text_content.append((lines[i], timestamp_millis[i]))

            frame.text = text_content
            frame.encoding = eyed3.id3.UTF_8_ENCODING

            tag.synchronized_lyrics.set(frame)
            self.logger.debug("成功写入 SYLT 帧")

        except Exception as e:
            self.logger.debug(f"SYLT 帧写入失败（fallback 到 USLT）: {e}")

    def _embed_unsynced_lyrics_frame(self, tag, lyrics: str) -> None:
        """
        嵌入无同步歌词（USLT 帧）
        这是最广泛支持的歌词帧格式。

        Note:
            eyed3 v0.9.9 的 tag.lyrics.set() 要求使用**位置参数**而非关键字参数！
            签名: set(text: str, lang: str, description: bytes)

            **关键修复**：description 必须为非空值（如 b'Lyrics'），
            否则 Windows Media Player、Melosik 等播放器无法识别歌词帧。
        """
        try:
            # description 设为 b'Lyrics'（非空），确保播放器能识别歌词
            # eyed3 v0.9.9 decorator requires positional arguments!
            tag.lyrics.set(lyrics, 'eng', b'Lyrics')
            self.logger.debug("成功写入 USLT 帧 (description='Lyrics')")
        except TypeError:
            # 某些版本的 eyed3 可能要求 description 为 str
            try:
                tag.lyrics.set(lyrics, 'eng', 'Lyrics')
                self.logger.debug("成功写入 USLT 帧 (str description='Lyrics')")
            except Exception as e:
                self.logger.warning(f"USLT 帧写入失败: {e}")
                raise
        except Exception as e:
            self.logger.warning(f"USLT 帧写入失败: {e}")
            raise

    def _generate_lrc_file(self, file_path: str, lyrics: str) -> bool:
        """
        生成独立的 LRC 文件（网易云音乐等播放器需要）

        Args:
            file_path: 音频文件路径
            lyrics: 歌词内容

        Returns:
            bool: 成功返回 True

        Note:
            网易云音乐对 LRC 文件有严格要求：
            1. 文件名必须与音频文件完全相同（除扩展名）
            2. 编码必须是 UTF-8 无 BOM
            3. 必须与音频文件位于同一目录
            4. 时间戳格式必须符合 [mm:ss.xx] 标准
        """
        try:
            # 生成 LRC 文件路径
            lrc_path = os.path.splitext(file_path)[0] + '.lrc'
            
            # 确保 LRC 文件内容是 UTF-8 无 BOM 编码
            # Python 的 open() 函数默认写入 UTF-8，但可能会添加 BOM
            # 使用 utf-8 编码并明确不写入 BOM
            with open(lrc_path, 'w', encoding='utf-8', newline='') as f:
                # 写入歌词内容
                f.write(lyrics)
            
            self.logger.info(f"成功生成 LRC 文件: {lrc_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"生成 LRC 文件失败: {file_path}, 错误: {e}")
            return False

    def _embed_generic_lyrics(
        self,
        file_path: str,
        lyrics: str,
        format: str,
        mode: str = 'embed_only'
    ) -> bool:
        """
        将歌词嵌入到通用音频文件（FLAC/M4A/OGG）
        使用 mutagen 格式特定的 API 进行嵌入。

        Args:
            file_path: 音频文件路径
            lyrics: 歌词内容
            format: 歌词格式
            mode: 嵌入模式 ('embed_only' 或 'embed_and_lrc')

        Returns:
            bool: 成功返回 True
        """
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.flac':
                from mutagen.flac import FLAC
                audio = FLAC(file_path)
                audio['LYRICS'] = lyrics
                audio.save()
                self.logger.debug("FLAC: 使用 mutagen.FLAC 写入 LYRICS 标签")

            elif ext == '.ogg':
                from mutagen.oggvorbis import OggVorbis
                audio = OggVorbis(file_path)
                audio['LYRICS'] = lyrics
                audio.save()
                self.logger.debug("OGG: 使用 mutagen.OggVorbis 写入 LYRICS 标签")

            elif ext == '.opus':
                audio = OggOpus(file_path)
                audio['LYRICS'] = lyrics
                audio.save()
                self.logger.debug("OPUS: 使用 mutagen.OggOpus 写入 LYRICS 标签")

            elif ext in ('.m4a', '.mp4'):
                from mutagen.mp4 import MP4
                audio = MP4(file_path)
                audio['\xa9lyr'] = lyrics
                audio.save()
                self.logger.debug("M4A: 使用 mutagen.MP4 写入 ©lyr 原子")

            else:
                audio = File(file_path)
                if audio is None:
                    self.logger.error(f"无法识别的音频格式: {ext}")
                    return False
                audio['LYRICS'] = lyrics
                audio.save()
                self.logger.debug(f"{ext.upper()}: 使用 mutagen.File 写入 LYRICS 标签")

            if mode == 'embed_and_lrc':
                lrc_success = self._generate_lrc_file(file_path, lyrics)
                if lrc_success:
                    self.logger.info(f"成功嵌入歌词并生成 LRC 文件: {file_path}")
                else:
                    self.logger.warning(f"歌词嵌入成功，但 LRC 文件生成失败: {file_path}")
            else:
                self.logger.info(f"成功嵌入歌词 (仅嵌入模式): {file_path}")

            return True

        except Exception as e:
            self.logger.error(f"使用 mutagen 嵌入歌词失败: {file_path}, 错误: {e}")
            return False

    def extract_lyrics(self, file_path: str) -> dict[str, Any] | None:
        """
        从音频文件提取歌词

        Args:
            file_path: 音频文件路径

        Returns:
            dict | None: 歌词数据字典，格式为：
                {
                    'plain_lyrics': str,      # 纯文本歌词
                    'synced_lyrics': str,     # 同步歌词
                    'format': str             # 歌词格式
                }
            无歌词或提取失败返回 None

        Raises:
            FileNotFoundError: 文件不存在

        Example:
            >>> manager = LyricManager()
            >>> lyrics = manager.extract_lyrics('song.mp3')
            >>> if lyrics:
            ...     print(lyrics['synced_lyrics'])
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.mp3':
                return self._extract_mp3_lyrics(file_path)
            elif ext == '.ogg':
                return self._extract_ogg_lyrics(file_path)
            elif ext in ['.flac', '.m4a']:
                return self._extract_generic_lyrics(file_path)
            else:
                self.logger.warning(f"不支持的文件格式: {ext}")
                return None

        except Exception as e:
            self.logger.error(f"提取歌词失败: {file_path}, 错误: {e}")
            return None

    def _extract_mp3_lyrics(self, file_path: str) -> dict[str, Any] | None:
        """
        从 MP3 文件提取歌词

        Args:
            file_path: MP3 文件路径

        Returns:
            dict | None: 歌词数据字典
        """
        audio = eyed3.load(file_path)
        if audio is None or audio.tag is None:
            self.logger.warning(f"MP3 文件无标签: {file_path}")
            return None

        tag = audio.tag
        synced_lyrics = ''
        plain_lyrics = ''

        # 方法1: 尝试读取 USLT 帧（非同步歌词传输）
        # 这是最常见的歌词存储方式，网易云音乐等播放器使用此格式
        if hasattr(tag, 'lyrics') and tag.lyrics:
            for lyrics_frame in tag.lyrics:
                if lyrics_frame.text:
                    synced_lyrics = lyrics_frame.text
                    break

        # 方法2: 尝试读取 SYLT 帧（同步歌词）
        if not synced_lyrics and hasattr(tag, 'lyrics'):
            try:
                for frame in tag.lyrics:
                    if hasattr(frame, 'text') and frame.text:
                        synced_lyrics = frame.text
                        break
            except Exception:
                pass

        # 方法3: 尝试读取 TXXX 帧（用户定义文本）
        if not synced_lyrics and hasattr(tag, 'user_text_frames'):
            try:
                for frame in tag.user_text_frames:
                    if frame.description in ['LYRICS', 'SYNCEDLYRICS', 'lyrics', 'syncedlyrics']:
                        synced_lyrics = frame.text
                        break
            except Exception:
                pass

        # 方法4: 尝试读取普通文本帧
        if not synced_lyrics and hasattr(tag, 'text'):
            try:
                for text_frame in tag.text:
                    if text_frame.description in ['LYRICS', 'SYNCEDLYRICS', 'lyrics', '']:
                        if text_frame.text:
                            synced_lyrics = text_frame.text
                            break
            except Exception:
                pass

        # 方法5: 尝试读取 comments
        if not synced_lyrics and hasattr(tag, 'comments'):
            try:
                for comment in tag.comments:
                    if comment.description in ['LYRICS', 'lyrics', '']:
                        if comment.text:
                            synced_lyrics = comment.text
                            break
            except Exception:
                pass

        if not synced_lyrics and not plain_lyrics:
            self.logger.info(f"MP3 文件无歌词: {file_path}")
            return None

        self.logger.info(f"成功提取 MP3 歌词: {file_path}")
        return {
            'plain_lyrics': plain_lyrics,
            'synced_lyrics': synced_lyrics,
            'format': 'lrc' if synced_lyrics else 'plain'
        }

    def _extract_ogg_lyrics(self, file_path: str) -> dict[str, Any] | None:
        """
        从 OGG 文件提取歌词

        Args:
            file_path: OGG 文件路径

        Returns:
            dict | None: 歌词数据字典
        """
        # 尝试 Vorbis，然后 Opus，最后通用格式
        audio = None
        try:
            audio = OggVorbis(file_path)
        except Exception:
            try:
                audio = OggOpus(file_path)
            except Exception:
                audio = File(file_path)

        if audio is None:
            self.logger.warning(f"无法识别的 OGG 格式: {file_path}")
            return None

        # 读取歌词标签
        synced_lyrics = audio.get('SYNCEDLYRICS', [''])[0]
        plain_lyrics = audio.get('LYRICS', [''])[0]

        if not synced_lyrics and not plain_lyrics:
            self.logger.info(f"OGG 文件无歌词: {file_path}")
            return None

        self.logger.info(f"成功提取 OGG 歌词: {file_path}")
        return {
            'plain_lyrics': plain_lyrics,
            'synced_lyrics': synced_lyrics,
            'format': 'lrc' if synced_lyrics else 'plain'
        }

    def _extract_generic_lyrics(self, file_path: str) -> dict[str, Any] | None:
        """
        从通用音频文件提取歌词

        Args:
            file_path: 音频文件路径

        Returns:
            dict | None: 歌词数据字典
        """
        audio = File(file_path)
        if audio is None:
            self.logger.warning(f"无法加载音频文件: {file_path}")
            return None

        # 尝试读取歌词标签
        synced_lyrics = audio.get('SYNCEDLYRICS', [''])[0]
        plain_lyrics = audio.get('LYRICS', [''])[0]

        if not synced_lyrics and not plain_lyrics:
            # 尝试其他可能的标签名
            synced_lyrics = audio.get('UNSYNCEDLYRICS', [''])[0]
            plain_lyrics = audio.get('UNSYNCED LYRICS', [''])[0]

        if not synced_lyrics and not plain_lyrics:
            self.logger.info(f"音频文件无歌词: {file_path}")
            return None

        self.logger.info(f"成功提取歌词: {file_path}")
        return {
            'plain_lyrics': plain_lyrics,
            'synced_lyrics': synced_lyrics,
            'format': 'lrc' if synced_lyrics else 'plain'
        }

    def convert_lyrics(
        self,
        lyrics: str,
        from_format: str,
        to_format: str
    ) -> str | None:
        """
        转换歌词格式

        Args:
            lyrics: 歌词内容
            from_format: 源格式（'lrc', 'ttml', 'srt', 'json'）
            to_format: 目标格式（'lrc', 'ttml', 'srt', 'json'）

        Returns:
            str | None: 转换后的歌词内容，失败返回 None

        Raises:
            ValueError: 不支持的格式

        Example:
            >>> manager = LyricManager()
            >>> lrc_lyrics = "[00:00.00]第一行歌词"
            >>> json_lyrics = manager.convert_lyrics(lrc_lyrics, 'lrc', 'json')
        """
        supported_formats = ['lrc', 'ttml', 'srt', 'json']

        if from_format.lower() not in supported_formats:
            raise ValueError(
                f"不支持的源格式: {from_format}, 支持的格式: {supported_formats}"
            )

        if to_format.lower() not in supported_formats:
            raise ValueError(
                f"不支持的目标格式: {to_format}, 支持的格式: {supported_formats}"
            )

        if from_format.lower() == to_format.lower():
            return lyrics

        try:
            # 使用本地转换器
            return self._convert_lyrics_local(lyrics, from_format, to_format)
        except Exception as e:
            self.logger.error(
                f"转换歌词格式失败: {from_format} -> {to_format}, 错误: {e}"
            )
            return None

    def _convert_lyrics_local(
        self,
        lyrics: str,
        from_format: str,
        to_format: str
    ) -> str:
        """
        本地歌词格式转换

        Args:
            lyrics: 歌词内容
            from_format: 源格式
            to_format: 目标格式

        Returns:
            str: 转换后的歌词内容
        """
        # 先解析为统一格式
        parsed_data = self._parse_lyrics(lyrics, from_format)

        # 再生成目标格式
        return self._generate_lyrics(parsed_data, to_format)

    def _parse_lyrics(self, lyrics: str, format: str) -> list[dict]:
        """
        解析歌词为统一格式

        Args:
            lyrics: 歌词内容
            format: 歌词格式

        Returns:
            list[dict]: 解析后的歌词数据，格式为：
                [{'time': 毫秒, 'text': '歌词文本'}, ...]
        """
        import json
        import re

        parsed = []

        if format == 'lrc':
            # 解析 LRC 格式
            # 格式: [mm:ss.xx]歌词文本
            pattern = r'\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)'
            for line in lyrics.split('\n'):
                match = re.match(pattern, line.strip())
                if match:
                    minutes = int(match.group(1))
                    seconds = int(match.group(2))
                    milliseconds = int(match.group(3).ljust(3, '0'))
                    time_ms = (minutes * 60 + seconds) * 1000 + milliseconds
                    text = match.group(4).strip()
                    if text:
                        parsed.append({'time': time_ms, 'text': text})

        elif format == 'json':
            # 解析 JSON 格式
            try:
                data = json.loads(lyrics)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'time' in item and 'text' in item:
                            parsed.append({
                                'time': item['time'],
                                'text': item['text']
                            })
            except json.JSONDecodeError:
                pass

        elif format == 'srt':
            # 解析 SRT 格式
            # 格式:
            # 序号
            # 00:00:00,000 --> 00:00:05,000
            # 歌词文本
            lines = lyrics.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                # 查找时间轴
                if '-->' in line:
                    time_match = re.match(
                        r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
                        line
                    )
                    if time_match:
                        hours = int(time_match.group(1))
                        minutes = int(time_match.group(2))
                        seconds = int(time_match.group(3))
                        milliseconds = int(time_match.group(4))
                        time_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds

                        # 下一行是歌词文本
                        i += 1
                        if i < len(lines):
                            text = lines[i].strip()
                            if text:
                                parsed.append({'time': time_ms, 'text': text})
                i += 1

        elif format == 'ttml':
            # 解析 TTML 格式（简化版）
            # 格式: <p begin="00:00:00.000" end="00:00:05.000">歌词文本</p>
            pattern = r'<p\s+begin="([^"]+)"[^>]*>([^<]+)</p>'
            for match in re.finditer(pattern, lyrics):
                time_str = match.group(1)
                text = match.group(2).strip()

                # 解析时间
                time_parts = time_str.split(':')
                if len(time_parts) == 3:
                    hours, minutes, seconds = time_parts
                    seconds_parts = seconds.split('.')
                    secs = int(seconds_parts[0])
                    ms = int(seconds_parts[1].ljust(3, '0')) if len(seconds_parts) > 1 else 0
                    time_ms = (int(hours) * 3600 + int(minutes) * 60 + secs) * 1000 + ms

                    if text:
                        parsed.append({'time': time_ms, 'text': text})

        return parsed

    def _generate_lyrics(self, data: list[dict], format: str) -> str:
        """
        从统一格式生成歌词

        Args:
            data: 歌词数据
            format: 目标格式

        Returns:
            str: 生成的歌词内容
        """
        import json

        if format == 'lrc':
            # 生成 LRC 格式
            lines = []
            for item in data:
                time_ms = item['time']
                text = item['text']

                minutes = time_ms // 60000
                seconds = (time_ms % 60000) // 1000
                milliseconds = time_ms % 1000

                lines.append(f"[{minutes:02d}:{seconds:02d}.{milliseconds:03d}]{text}")

            return '\n'.join(lines)

        elif format == 'json':
            # 生成 JSON 格式
            return json.dumps(data, ensure_ascii=False, indent=2)

        elif format == 'srt':
            # 生成 SRT 格式
            lines = []
            for i, item in enumerate(data, 1):
                time_ms = item['time']
                text = item['text']

                hours = time_ms // 3600000
                minutes = (time_ms % 3600000) // 60000
                seconds = (time_ms % 60000) // 1000
                milliseconds = time_ms % 1000

                # SRT 时间格式: 00:00:00,000 --> 00:00:05,000
                start_time = f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
                # 假设每行歌词持续5秒
                end_ms = time_ms + 5000
                end_hours = end_ms // 3600000
                end_minutes = (end_ms % 3600000) // 60000
                end_seconds = (end_ms % 60000) // 1000
                end_milliseconds = end_ms % 1000
                end_time = f"{end_hours:02d}:{end_minutes:02d}:{end_seconds:02d},{end_milliseconds:03d}"

                lines.append(str(i))
                lines.append(f"{start_time} --> {end_time}")
                lines.append(text)
                lines.append('')

            return '\n'.join(lines)

        elif format == 'ttml':
            # 生成 TTML 格式
            lines = ['<?xml version="1.0" encoding="UTF-8"?>']
            lines.append('<tt xmlns="http://www.w3.org/ns/ttml" xml:lang="zh">')
            lines.append('  <body>')
            lines.append('    <div>')

            for item in data:
                time_ms = item['time']
                text = item['text']

                hours = time_ms // 3600000
                minutes = (time_ms % 3600000) // 60000
                seconds = (time_ms % 60000) // 1000
                milliseconds = time_ms % 1000

                begin_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

                lines.append(f'      <p begin="{begin_time}">{text}</p>')

            lines.append('    </div>')
            lines.append('  </body>')
            lines.append('</tt>')

            return '\n'.join(lines)

        return ''

    def batch_fetch_lyrics(
        self,
        file_paths: list[str],
        provider: str = 'lrclib'
    ) -> dict[str, dict[str, Any] | None]:
        """
        批量获取歌词

        Args:
            file_paths: 音频文件路径列表
            provider: 提供商名称

        Returns:
            dict[str, dict | None]: 文件路径到歌词数据的映射

        Example:
            >>> manager = LyricManager()
            >>> results = manager.batch_fetch_lyrics(
            ...     ['song1.mp3', 'song2.flac'],
            ...     provider='lrclib'
            ... )
        """
        results = {}

        for file_path in file_paths:
            try:
                lyrics = self.fetch_lyrics(file_path, provider)
                results[file_path] = lyrics
            except Exception as e:
                self.logger.error(f"批量获取歌词失败: {file_path}, 错误: {e}")
                results[file_path] = None

        success_count = sum(1 for v in results.values() if v is not None)
        self.logger.info(
            f"批量获取歌词完成: 成功 {success_count}/{len(file_paths)}"
        )

        return results

    def batch_embed_lyrics(
        self,
        file_lyrics_pairs: list[tuple[str, str]],
        format: str = 'lrc',
        mode: str = 'embed_only'
    ) -> dict[str, bool]:
        """
        批量嵌入歌词

        Args:
            file_lyrics_pairs: 文件路径和歌词内容的元组列表
            format: 歌词格式
            mode: 嵌入模式 ('embed_only' 或 'embed_and_lrc')

        Returns:
            dict[str, bool]: 文件路径到操作结果的映射

        Example:
            >>> manager = LyricManager()
            >>> results = manager.batch_embed_lyrics([
            ...     ('song1.mp3', '[00:00.00]歌词1'),
            ...     ('song2.flac', '[00:00.00]歌词2')
            ... ], format='lrc', mode='embed_only')
        """
        results = {}

        for file_path, lyrics in file_lyrics_pairs:
            try:
                success = self.embed_lyrics(file_path, lyrics, format, mode)
                results[file_path] = success
            except Exception as e:
                self.logger.error(f"批量嵌入歌词失败: {file_path}, 错误: {e}")
                results[file_path] = False

        success_count = sum(1 for v in results.values() if v)
        self.logger.info(
            f"批量嵌入歌词完成: 成功 {success_count}/{len(file_lyrics_pairs)}"
        )

        return results
