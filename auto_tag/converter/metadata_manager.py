# auto_tag/converter/metadata_manager.py
"""
元数据管理器模块
提供音频文件元数据的读取、写入、批量编辑等功能
支持 MP3（ID3）和 OGG（Vorbis/Opus）格式
"""

from __future__ import annotations

import base64
import logging
import os
import re
from typing import Any

import eyed3
from mutagen import File
from mutagen.flac import Picture
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis


class MetadataManager:
    """
    音频文件元数据管理器
    
    支持格式：
    - MP3（ID3 标签）
    - OGG（Vorbis/Opus 标签）
    
    功能：
    - 读取/写入元数据
    - 从文件名解析元数据
    - 批量编辑元数据
    - 封面图片管理
    """
    
    def __init__(self):
        """初始化元数据管理器，配置日志"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def read_metadata(self, file_path: str) -> dict[str, Any]:
        """
        读取音频文件的元数据
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            dict: 包含元数据的字典，格式为：
                {
                    'title': str,      # 歌曲标题
                    'artist': str,     # 艺术家
                    'album': str,      # 专辑名
                    'year': str,       # 发行年份
                    'genre': str,      # 音乐类型
                    'cover': bytes     # 封面图片数据（可选）
                }
                
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.mp3':
            return self._read_mp3_metadata(file_path)
        elif ext == '.ogg':
            return self._read_ogg_metadata(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    def _read_mp3_metadata(self, file_path: str) -> dict[str, Any]:
        """
        读取 MP3 文件的 ID3 标签
        
        Args:
            file_path: MP3 文件路径
            
        Returns:
            dict: 元数据字典
        """
        metadata = {
            'title': '',
            'artist': '',
            'album': '',
            'year': '',
            'genre': '',
            'cover': None
        }
        
        try:
            audio = eyed3.load(file_path)
            if audio is None or audio.tag is None:
                self.logger.warning(f"MP3 文件无标签: {file_path}")
                return metadata
            
            tag = audio.tag
            metadata['title'] = tag.title or ''
            metadata['artist'] = tag.artist or ''
            metadata['album'] = tag.album or ''
            metadata['year'] = str(tag.recording_date) if tag.recording_date else ''
            metadata['genre'] = tag.genre.name if tag.genre else ''
            
            # 读取封面图片
            if tag.images:
                for img in tag.images:
                    if img.picture_type == 3:  # Front cover
                        metadata['cover'] = img.image_data
                        break
            
            self.logger.info(f"成功读取 MP3 元数据: {file_path}")
            
        except Exception as e:
            self.logger.error(f"读取 MP3 元数据失败: {file_path}, 错误: {e}")
        
        return metadata
    
    def _read_ogg_metadata(self, file_path: str) -> dict[str, Any]:
        """
        读取 OGG 文件的 Vorbis/Opus 标签
        
        Args:
            file_path: OGG 文件路径
            
        Returns:
            dict: 元数据字典
        """
        metadata = {
            'title': '',
            'artist': '',
            'album': '',
            'year': '',
            'genre': '',
            'cover': None
        }
        
        try:
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
                return metadata
            
            # 读取标签
            metadata['title'] = audio.get('TITLE', [''])[0]
            metadata['artist'] = audio.get('ARTIST', [''])[0]
            metadata['album'] = audio.get('ALBUM', [''])[0]
            metadata['year'] = audio.get('DATE', [''])[0]
            metadata['genre'] = audio.get('GENRE', [''])[0]
            
            # 读取封面图片
            if 'METADATA_BLOCK_PICTURE' in audio:
                pic_data = audio['METADATA_BLOCK_PICTURE'][0]
                pic = Picture()
                pic.data = base64.b64decode(pic_data)
                metadata['cover'] = pic.data
            
            self.logger.info(f"成功读取 OGG 元数据: {file_path}")
            
        except Exception as e:
            self.logger.error(f"读取 OGG 元数据失败: {file_path}, 错误: {e}")
        
        return metadata
    
    def write_metadata(self, file_path: str, metadata: dict[str, Any]) -> bool:
        """
        写入元数据到音频文件
        
        Args:
            file_path: 音频文件路径
            metadata: 元数据字典，可包含以下键：
                - title: 歌曲标题
                - artist: 艺术家
                - album: 专辑名
                - year: 发行年份
                - genre: 音乐类型
                
        Returns:
            bool: 写入成功返回 True，失败返回 False
        """
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return False
        
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.mp3':
                return self._write_mp3_metadata(file_path, metadata)
            elif ext == '.ogg':
                return self._write_ogg_metadata(file_path, metadata)
            else:
                self.logger.error(f"不支持的文件格式: {ext}")
                return False
        except Exception as e:
            self.logger.error(f"写入元数据失败: {file_path}, 错误: {e}")
            return False
    
    def _write_mp3_metadata(self, file_path: str, metadata: dict[str, Any]) -> bool:
        """
        写入 MP3 文件的 ID3 标签
        
        Args:
            file_path: MP3 文件路径
            metadata: 元数据字典
            
        Returns:
            bool: 写入成功返回 True
        """
        audio = eyed3.load(file_path)
        if audio is None:
            self.logger.error(f"无法加载 MP3 文件: {file_path}")
            return False
        
        if audio.tag is None:
            audio.initTag()
        
        # 写入标签
        if 'title' in metadata:
            audio.tag.title = metadata['title']
        if 'artist' in metadata:
            audio.tag.artist = metadata['artist']
        if 'album' in metadata:
            audio.tag.album = metadata['album']
        if 'year' in metadata:
            try:
                audio.tag.recording_date = int(metadata['year'])
            except (ValueError, TypeError):
                pass
        if 'genre' in metadata:
            audio.tag.genre = metadata['genre']
        
        audio.tag.save()
        self.logger.info(f"成功写入 MP3 元数据: {file_path}")
        return True
    
    def _write_ogg_metadata(self, file_path: str, metadata: dict[str, Any]) -> bool:
        """
        写入 OGG 文件的 Vorbis/Opus 标签
        
        Args:
            file_path: OGG 文件路径
            metadata: 元数据字典
            
        Returns:
            bool: 写入成功返回 True
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
            self.logger.error(f"无法识别的 OGG 格式: {file_path}")
            return False
        
        # 写入标签
        if 'title' in metadata:
            audio['TITLE'] = [metadata['title']]
        if 'artist' in metadata:
            audio['ARTIST'] = [metadata['artist']]
        if 'album' in metadata:
            audio['ALBUM'] = [metadata['album']]
        if 'year' in metadata:
            audio['DATE'] = [metadata['year']]
        if 'genre' in metadata:
            audio['GENRE'] = [metadata['genre']]
        
        audio.save()
        self.logger.info(f"成功写入 OGG 元数据: {file_path}")
        return True
    
    def parse_filename(self, filename: str) -> dict[str, str]:
        """
        从文件名解析元数据
        
        支持格式：
        - "Artist - Title" 或 "Artist - Title - Album"
        - "Title - Artist" 或 "Title - Artist - Album"
        
        Args:
            filename: 文件名（不含扩展名）
            
        Returns:
            dict: 包含解析出的元数据，格式为：
                {
                    'title': str,
                    'artist': str,
                    'album': str
                }
        """
        result = {
            'title': '',
            'artist': '',
            'album': ''
        }
        
        # 移除文件扩展名
        name = os.path.splitext(filename)[0]
        
        # 尝试匹配 "Artist - Title - Album" 格式
        pattern_three = r'^(.+?)\s*-\s*(.+?)\s*-\s*(.+?)$'
        match = re.match(pattern_three, name)
        if match:
            result['artist'] = match.group(1).strip()
            result['title'] = match.group(2).strip()
            result['album'] = match.group(3).strip()
            self.logger.info(f"解析文件名成功（三段式）: {filename}")
            return result
        
        # 尝试匹配 "Artist - Title" 格式
        pattern_two = r'^(.+?)\s*-\s*(.+?)$'
        match = re.match(pattern_two, name)
        if match:
            result['artist'] = match.group(1).strip()
            result['title'] = match.group(2).strip()
            self.logger.info(f"解析文件名成功（两段式）: {filename}")
            return result
        
        # 无法解析，将整个文件名作为标题
        result['title'] = name.strip()
        self.logger.warning(f"无法解析文件名格式，使用文件名作为标题: {filename}")
        
        return result
    
    def batch_edit(
        self, 
        file_paths: list[str], 
        metadata: dict[str, Any]
    ) -> dict[str, bool]:
        """
        批量编辑多个音频文件的元数据
        
        Args:
            file_paths: 文件路径列表
            metadata: 要写入的元数据字典
            
        Returns:
            dict[str, bool]: 文件路径到操作结果的映射，True 表示成功
        """
        results = {}
        
        for file_path in file_paths:
            try:
                success = self.write_metadata(file_path, metadata)
                results[file_path] = success
            except Exception as e:
                self.logger.error(f"批量编辑失败: {file_path}, 错误: {e}")
                results[file_path] = False
        
        success_count = sum(1 for v in results.values() if v)
        self.logger.info(
            f"批量编辑完成: 成功 {success_count}/{len(file_paths)}"
        )
        
        return results
    
    def get_cover(self, file_path: str) -> bytes | None:
        """
        获取音频文件的封面图片数据
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            bytes | None: 封面图片数据，无封面则返回 None
        """
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return None
        
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.mp3':
                return self._get_mp3_cover(file_path)
            elif ext == '.ogg':
                return self._get_ogg_cover(file_path)
            else:
                self.logger.error(f"不支持的文件格式: {ext}")
                return None
        except Exception as e:
            self.logger.error(f"获取封面失败: {file_path}, 错误: {e}")
            return None
    
    def _get_mp3_cover(self, file_path: str) -> bytes | None:
        """
        获取 MP3 文件的封面图片
        
        Args:
            file_path: MP3 文件路径
            
        Returns:
            bytes | None: 封面图片数据
        """
        audio = eyed3.load(file_path)
        if audio is None or audio.tag is None:
            return None
        
        if audio.tag.images:
            for img in audio.tag.images:
                if img.picture_type == 3:  # Front cover
                    return img.image_data
        
        return None
    
    def _get_ogg_cover(self, file_path: str) -> bytes | None:
        """
        获取 OGG 文件的封面图片
        
        Args:
            file_path: OGG 文件路径
            
        Returns:
            bytes | None: 封面图片数据
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
            return None
        
        if 'METADATA_BLOCK_PICTURE' in audio:
            pic_data = audio['METADATA_BLOCK_PICTURE'][0]
            pic = Picture()
            pic.data = base64.b64decode(pic_data)
            return pic.data
        
        return None
    
    def set_cover(self, file_path: str, cover_data: bytes) -> bool:
        """
        设置音频文件的封面图片
        
        Args:
            file_path: 音频文件路径
            cover_data: 封面图片数据（JPEG 或 PNG 格式）
            
        Returns:
            bool: 设置成功返回 True，失败返回 False
        """
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return False
        
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.mp3':
                return self._set_mp3_cover(file_path, cover_data)
            elif ext == '.ogg':
                return self._set_ogg_cover(file_path, cover_data)
            else:
                self.logger.error(f"不支持的文件格式: {ext}")
                return False
        except Exception as e:
            self.logger.error(f"设置封面失败: {file_path}, 错误: {e}")
            return False
    
    def _set_mp3_cover(self, file_path: str, cover_data: bytes) -> bool:
        """
        设置 MP3 文件的封面图片
        
        Args:
            file_path: MP3 文件路径
            cover_data: 封面图片数据
            
        Returns:
            bool: 设置成功返回 True
        """
        audio = eyed3.load(file_path)
        if audio is None:
            self.logger.error(f"无法加载 MP3 文件: {file_path}")
            return False
        
        if audio.tag is None:
            audio.initTag()
        
        # 判断图片类型
        mime_type = 'image/jpeg'
        if cover_data[:8] == b'\x89PNG\r\n\x1a\n':
            mime_type = 'image/png'
        
        # 设置封面图片（picture_type=3 表示 Front cover）
        audio.tag.images.set(3, cover_data, mime_type, 'cover')
        audio.tag.save()
        
        self.logger.info(f"成功设置 MP3 封面: {file_path}")
        return True
    
    def _set_ogg_cover(self, file_path: str, cover_data: bytes) -> bool:
        """
        设置 OGG 文件的封面图片
        
        Args:
            file_path: OGG 文件路径
            cover_data: 封面图片数据
            
        Returns:
            bool: 设置成功返回 True
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
            self.logger.error(f"无法识别的 OGG 格式: {file_path}")
            return False
        
        # 判断图片类型
        mime_type = 'image/jpeg'
        if cover_data[:8] == b'\x89PNG\r\n\x1a\n':
            mime_type = 'image/png'
        
        # 创建 FLAC Picture 对象并编码
        pic = Picture()
        pic.data = cover_data
        pic.type = 3  # Front cover
        pic.mime = mime_type
        pic.width = pic.height = pic.depth = pic.colors = 0
        
        # Base64 编码
        pic_data = base64.b64encode(pic.write()).decode('ascii')
        audio['METADATA_BLOCK_PICTURE'] = [pic_data]
        audio.save()
        
        self.logger.info(f"成功设置 OGG 封面: {file_path}")
        return True
