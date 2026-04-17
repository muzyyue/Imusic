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
        provider: str = 'lrclib'
    ) -> dict[str, Any] | None:
        """
        从指定提供商获取歌词

        Args:
            file_path: 音频文件路径
            provider: 提供商名称（'lrclib', 'applemusic', 'musixmatch'）

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
            >>> lyrics = manager.fetch_lyrics('song.mp3', 'lrclib')
            >>> if lyrics:
            ...     print(lyrics['synced_lyrics'])
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 验证提供商
        provider_config = get_provider(provider)
        if not provider_config:
            raise ValueError(f"不支持的提供商: {provider}")

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
        使用 eyed3 将歌词嵌入到 MP3 文件

        Args:
            file_path: MP3 文件路径
            lyrics: 歌词内容
            format: 歌词格式

        Returns:
            bool: 成功返回 True
        """
        audio = eyed3.load(file_path)
        if audio is None:
            self.logger.error(f"无法加载 MP3 文件: {file_path}")
            return False

        if audio.tag is None:
            audio.initTag()

        tag = audio.tag

        # 嵌入同步歌词（USLT 帧 - 网易云音乐等播放器识别此格式）
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

        self.logger.info(f"成功嵌入歌词到 MP3: {file_path}")
        return True

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
            # 导入 lrxy.converter 模块
            from lrxy import converter

            # 获取解析器和生成器
            parser_module = getattr(converter, from_format.lower())
            generator_module = getattr(converter, to_format.lower())

            # 解析歌词为结构化数据
            if from_format.lower() == 'json':
                import json
                data = json.loads(lyrics)
            else:
                data = parser_module.parse(lyrics)

            # 生成目标格式
            if to_format.lower() == 'json':
                import json
                return json.dumps(data, ensure_ascii=False, indent=2)
            else:
                return generator_module.generate(data)

        except ImportError as e:
            self.logger.error(f"导入 lrxy.converter 模块失败: {e}")
            return None
        except Exception as e:
            self.logger.error(
                f"转换歌词格式失败: {from_format} -> {to_format}, 错误: {e}"
            )
            return None

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
