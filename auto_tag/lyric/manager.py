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
    - MP3（ID3 标签）
    - FLAC
    - M4A
    - OGG（Vorbis/Opus）
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

    def fetch_lyrics(
        self,
        file_path: str,
        provider: str = 'netease'
    ) -> dict[str, Any] | None:
        """
        从指定提供商获取歌词

        Args:
            file_path: 音频文件路径
            provider: 提供商名称（'netease', 'kugou', 'lrclib', 'applemusic', 'musixmatch'）

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
            ValueError: 不支持的提供商

        Example:
            >>> manager = LyricManager()
            >>> lyrics = manager.fetch_lyrics('song.mp3', 'netease')
            >>> if lyrics:
            ...     print(lyrics['synced_lyrics'])
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 验证提供商
        provider_config = get_provider(provider)
        if not provider_config:
            raise ValueError(f"不支持的提供商: {provider}")

        # 根据提供商类型选择不同的处理方式
        if provider in ['netease', 'kugou']:
            return self._fetch_lyrics_from_music_api(file_path, provider)
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
            # 导入 MusicLibrary
            from MusicLibrary.neteaseCloudMusicApi import NeteaseCloudMusicApi
            from MusicLibrary.kuGouMusicApi import KuGouMusicApi

            # 根据提供商创建对应的 API 客户端
            if provider == 'netease':
                api = NeteaseCloudMusicApi()
            else:
                api = KuGouMusicApi()

            # 从音频文件提取元数据
            metadata = self._extract_audio_metadata(file_path)
            if not metadata:
                self.logger.error(f"无法提取音频元数据: {file_path}")
                return []

            # 搜索歌曲
            keyword = f"{metadata['artist']} {metadata['title']}"
            search_result = api.search(keyword)

            if not search_result or not hasattr(search_result, 'body'):
                self.logger.warning(f"搜索歌曲失败: {keyword}")
                return []

            # 解析并返回搜索结果
            songs = self._parse_search_result(search_result.body, provider)
            self.logger.info(f"搜索完成: {keyword}, 找到 {len(songs)} 首歌曲")

            return songs

        except ImportError as e:
            self.logger.error(f"导入 MusicLibrary 库失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"搜索歌曲失败: {file_path}, 错误: {e}")
            return []

    def fetch_lyric_by_id(
        self,
        song_id: int | str,
        provider: str = 'netease'
    ) -> dict[str, Any] | None:
        """
        根据歌曲 ID 获取歌词

        Args:
            song_id: 歌曲 ID
            provider: 提供商名称

        Returns:
            dict | None: 歌词数据字典
        """
        try:
            # 导入 MusicLibrary
            from MusicLibrary.neteaseCloudMusicApi import NeteaseCloudMusicApi
            from MusicLibrary.kuGouMusicApi import KuGouMusicApi

            # 根据提供商创建对应的 API 客户端
            if provider == 'netease':
                api = NeteaseCloudMusicApi()
            else:
                api = KuGouMusicApi()

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
                synced_lyrics = lrc_data.get('lyric', '') if isinstance(lrc_data, dict) else ''
                plain_lyrics = tlyric_data.get('lyric', '') if isinstance(tlyric_data, dict) else ''
            else:
                synced_lyrics = body.get('lyrics', '')

            if not (synced_lyrics or plain_lyrics):
                return None

            # 构建返回数据
            result = {
                'synced_lyrics': synced_lyrics,
                'plain_lyrics': plain_lyrics,
                'provider': provider,
                'track_name': '',
                'artist_name': '',
                'album_name': '',
                'duration': 0
            }

            self.logger.info(f"成功获取歌词 (ID: {song_id}), 提供商: {provider}")
            return result

        except ImportError as e:
            self.logger.error(f"导入 MusicLibrary 库失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取歌词失败 (ID: {song_id}), 错误: {e}")
            return None

    def _fetch_lyrics_from_music_api(
        self,
        file_path: str,
        provider: str
    ) -> dict[str, Any] | None:
        """
        从网易云音乐或酷狗音乐获取歌词

        Args:
            file_path: 音频文件路径
            provider: 提供商名称（'netease' 或 'kugou'）

        Returns:
            dict | None: 歌词数据字典
        """
        try:
            # 导入 MusicLibrary
            from MusicLibrary.neteaseCloudMusicApi import NeteaseCloudMusicApi
            from MusicLibrary.kuGouMusicApi import KuGouMusicApi

            # 根据提供商创建对应的 API 客户端
            if provider == 'netease':
                api = NeteaseCloudMusicApi()
            else:
                api = KuGouMusicApi()

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
                        synced_lyrics = lrc_data.get('lyric', '') if isinstance(lrc_data, dict) else ''
                        plain_lyrics = tlyric_data.get('lyric', '') if isinstance(tlyric_data, dict) else ''
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
        format: str = 'lrc'
    ) -> bool:
        """
        将歌词嵌入到音频文件

        Args:
            file_path: 音频文件路径
            lyrics: 歌词内容（LRC、TTML、SRT 或 JSON 格式）
            format: 歌词格式（'lrc', 'ttml', 'srt', 'json'）

        Returns:
            bool: 嵌入成功返回 True，失败返回 False

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的歌词格式

        Example:
            >>> manager = LyricManager()
            >>> lyrics = "[00:00.00]第一行歌词\\n[00:05.00]第二行歌词"
            >>> success = manager.embed_lyrics('song.mp3', lyrics, 'lrc')
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 验证格式
        supported_formats = ['lrc', 'ttml', 'srt', 'json']
        if format.lower() not in supported_formats:
            raise ValueError(
                f"不支持的歌词格式: {format}, 支持的格式: {supported_formats}"
            )

        ext = os.path.splitext(file_path)[1].lower()

        try:
            # 首先尝试使用 eyed3 直接嵌入（不依赖 lrxy）
            if ext == '.mp3':
                return self._embed_mp3_lyrics(file_path, lyrics, format)
            elif ext in ['.flac', '.m4a', '.ogg']:
                return self._embed_generic_lyrics(file_path, lyrics, format)
            else:
                self.logger.warning(f"不支持的文件格式: {ext}")
                return False

        except Exception as e:
            self.logger.error(f"嵌入歌词失败: {file_path}, 错误: {e}")
            return False

    def _embed_mp3_lyrics(self, file_path: str, lyrics: str, format: str) -> bool:
        """
        使用 eyed3 将歌词嵌入到 MP3 文件，并生成独立的 LRC 文件

        Args:
            file_path: MP3 文件路径
            lyrics: 歌词内容
            format: 歌词格式

        Returns:
            bool: 成功返回 True

        Note:
            网易云音乐不支持读取 ID3v2 的 USLT 帧，因此需要生成独立的 LRC 文件。
            LRC 文件要求：
            1. 文件名与 MP3 文件完全相同（除扩展名）
            2. 编码必须是 UTF-8 无 BOM
            3. 与 MP3 文件位于同一目录
        """
        audio = eyed3.load(file_path)
        if audio is None:
            self.logger.error(f"无法加载 MP3 文件: {file_path}")
            return False

        if audio.tag is None:
            audio.initTag()

        tag = audio.tag

        # 嵌入同步歌词（USLT 帧 - 其他播放器识别此格式，但网易云音乐不支持）
        # 使用 USLT (Unsynchronized Lyrics) 格式，这是最广泛支持的格式
        try:
            # eyed3 要求歌词内容为字符串
            tag.lyrics.set(lyrics, lang=b'eng', description=b'')
        except (TypeError, AttributeError):
            # 某些版本的 eyed3 可能需要不同的参数格式
            try:
                # 尝试使用字符串参数
                tag.lyrics.set(lyrics, lang='eng', description='')
            except Exception as e:
                self.logger.warning(f"使用备用方法嵌入歌词: {e}")
                # 最后的备用方案：使用 user_text_frames
                try:
                    tag.user_text_frames.set(lyrics, description='LYRICS')
                except Exception:
                    pass

        # 同时保存为 TXXX 帧（某些播放器支持）
        try:
            tag.user_text_frames.set(lyrics, description='SYNCEDLYRICS')
        except Exception:
            pass

        # 保存文件 - 使用 tag.save() 而不是 audio.save()
        try:
            tag.save()
        except AttributeError:
            # 某些版本的 eyed3 可能使用不同的保存方法
            try:
                audio.save()
            except AttributeError:
                # 最后尝试直接写入文件
                with open(file_path, 'r+b') as f:
                    tag.save(f)

        # 生成独立的 LRC 文件（网易云音乐需要）
        lrc_success = self._generate_lrc_file(file_path, lyrics)
        
        if lrc_success:
            self.logger.info(f"成功嵌入歌词到 MP3 并生成 LRC 文件: {file_path}")
        else:
            self.logger.warning(f"成功嵌入歌词到 MP3，但 LRC 文件生成失败: {file_path}")
        
        return True

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

    def _embed_generic_lyrics(self, file_path: str, lyrics: str, format: str) -> bool:
        """
        将歌词嵌入到通用音频文件（FLAC/M4A/OGG）

        Args:
            file_path: 音频文件路径
            lyrics: 歌词内容
            format: 歌词格式

        Returns:
            bool: 成功返回 True
        """
        audio = File(file_path, easy=True)
        if audio is None:
            self.logger.error(f"无法加载音频文件: {file_path}")
            return False

        # 保存同步歌词
        audio['LYRICS'] = lyrics
        audio['SYNCEDLYRICS'] = lyrics

        # 保存文件
        audio.save()

        self.logger.info(f"成功嵌入歌词: {file_path}")
        return True

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
        format: str = 'lrc'
    ) -> dict[str, bool]:
        """
        批量嵌入歌词

        Args:
            file_lyrics_pairs: 文件路径和歌词内容的元组列表
            format: 歌词格式

        Returns:
            dict[str, bool]: 文件路径到操作结果的映射

        Example:
            >>> manager = LyricManager()
            >>> results = manager.batch_embed_lyrics([
            ...     ('song1.mp3', '[00:00.00]歌词1'),
            ...     ('song2.flac', '[00:00.00]歌词2')
            ... ], format='lrc')
        """
        results = {}

        for file_path, lyrics in file_lyrics_pairs:
            try:
                success = self.embed_lyrics(file_path, lyrics, format)
                results[file_path] = success
            except Exception as e:
                self.logger.error(f"批量嵌入歌词失败: {file_path}, 错误: {e}")
                results[file_path] = False

        success_count = sum(1 for v in results.values() if v)
        self.logger.info(
            f"批量嵌入歌词完成: 成功 {success_count}/{len(file_lyrics_pairs)}"
        )

        return results
