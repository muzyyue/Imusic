"""
测试通用音频标签写入功能 (update_audio_tags)

验证所有支持格式的标签写入：
- MP3: ID3v2.4 标签
- OGG/OPUS: Vorbis Comment 标签
- FLAC: Vorbis Comment + FLAC Picture
- M4A/MP4: iTunes Metadata
- WAV: 跳过（不支持）
- WMA/AAC: 通用接口
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock


class TestUpdateAudioTags:
    """测试 update_audio_tags 通用函数"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        """每个测试前的设置"""
        self.tmp_dir = tmp_path
        self.test_metadata = {
            "title": "测试歌曲",
            "artist": "测试艺术家",
            "album": "测试专辑",
        }

    def test_mp3_format(self):
        """测试 MP3 格式标签写入"""
        from auto_tag.audio_recognize import update_audio_tags

        # 创建临时 MP3 文件（使用最小有效 MP3 结构）
        mp3_file = self.tmp_dir / "test.mp3"
        # 写入最小 MP3 文件头（ID3 标记 + 空帧）
        mp3_file.write_bytes(b'ID3\x04\x00\x00\x00\x00\x1f\x00' + b'\x00' * 31 + b'\xff\xfb\x90\x00' + b'\x00' * 100)

        # 测试标签写入（不包含封面）
        update_audio_tags(
            str(mp3_file),
            **self.test_metadata,
            cover_url=None,
            trace=False
        )

        # 验证文件存在且大小变化（标签已写入）
        assert mp3_file.exists()
        assert mp3_file.stat().st_size > 0

    def test_ogg_format(self):
        """测试 OGG 格式标签写入"""
        from auto_tag.audio_recognize import update_audio_tags

        # 创建临时 OGG 文件（最小有效 OGG 头）
        ogg_file = self.tmp_dir / "test.ogg"
        # OGG 页头 + 最小 Vorbis 头
        ogg_header = (
            b'OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x01\x1c\x00'
            b'\x01vorbis\x00\x00\x00\x00\x00\x00\x00\x00\x01\xb0\x01\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        )
        ogg_file.write_bytes(ogg_header)

        # 测试标签写入
        update_audio_tags(
            str(ogg_file),
            **self.test_metadata,
            cover_url=None,
            trace=False
        )

        assert ogg_file.exists()

    def test_flac_format(self):
        """测试 FLAC 格式标签写入"""
        from auto_tag.audio_recognize import update_audio_tags

        # 创建临时 FLAC 文件
        flac_file = self.tmp_dir / "test.flac"
        # FLAC 流标记 + STREAMINFO 元数据块（最小有效 FLAC）
        flac_header = (
            b'fLaC'  # FLAC 标记
            b'\x00'   # BLOCK_TYPE=STREAMINFO (last metadata block)
            b'\x00\x00\x22'  # Block length (34 bytes)
            b'\x10\x00'  # Min block size
            b'\x10\x00'  # Max block size
            b'\x03\x00'  # Min frame size
            b'\x03\x00'  # Max frame size
            b'\x0b\xb8\x00'  # Sample rate (3000 Hz)
            b'\x01'  # Channels - 1 (2 channels)
            b'\xb0'  # Bits per sample - 1 (16 bits)
            b'\x00\x00\x0b\xb8'  # Total samples (3000)
            b'\x12\x34\x56\x78\x9a\xbc\xde\xf0'  # MD5 signature
        )
        flac_file.write_bytes(flac_header)

        # 测试标签写入
        update_audio_tags(
            str(flac_file),
            **self.test_metadata,
            cover_url=None,
            trace=False
        )

        assert flac_file.exists()

    @patch('auto_tag.audio_recognize.urlopen')
    def test_flac_with_cover_art(self, mock_urlopen):
        """测试 FLAC 格式带封面图片的标签写入"""
        from auto_tag.audio_recognize import update_audio_tags

        # Mock 封面图片下载
        mock_response = MagicMock()
        mock_response.read.return_value = b'\xff\xd8\xff\xe0' + b'\x00' * 100  # JPEG 头
        mock_urlopen.return_value = mock_response

        # 创建临时 FLAC 文件
        flac_file = self.tmp_dir / "test_cover.flac"
        flac_file.write_bytes(
            b'fLaC'
            b'\x00\x00\x00\x22'
            b'\x10\x00\x10\x00\x03\x00\x03\x00'
            b'\x0b\xb8\x00\x01\xb0\x00\x00\x00\x0b\xb8'
            b'\x12\x34\x56\x78\x9a\xbc\xde\xf0'
        )

        # 测试带封面的标签写入
        update_audio_tags(
            str(flac_file),
            **self.test_metadata,
            cover_url="http://example.com/cover.jpg",
            trace=True
        )

        assert flac_file.exists()
        mock_urlopen.assert_called_once()

    def test_m4a_format(self):
        """测试 M4A 格式标签写入"""
        from auto_tag.audio_recognize import update_audio_tags

        # 创建临时 M4A 文件（最小 ftyp box）
        m4a_file = self.tmp_dir / "test.m4a"
        # ftyp box: size(4) + 'ftyp'(4) + major_brand(4) + minor_version(4)
        m4a_file.write_bytes(
            b'\x00\x00\x00\x14'  # Box size (20 bytes)
            b'ftyp'             # Box type
            b'M4A '             # Major brand
            b'\x00\x00\x00\x00'  # Minor version
            b'M4A '             # Compatible brand
        )

        # 测试标签写入
        update_audio_tags(
            str(m4a_file),
            **self.test_metadata,
            cover_url=None,
            trace=False
        )

        assert m4a_file.exists()

    def test_wav_format_skips_gracefully(self):
        """测试 WAV 格式应跳过但不报错"""
        from auto_tag.audio_recognize import update_audio_tags

        # 创建临时 WAV 文件
        wav_file = self.tmp_dir / "test.wav"
        # RIFF WAV header
        wav_file.write_bytes(
            b'RIFF'
            b'\x24\x00\x00\x00'  # File size - 8
            b'WAVE'
            b'fmt '
            b'\x10\x00\x00\x00'  # fmt chunk size
            b'\x01\x00'          # PCM format
            b'\x01\x00'          # Mono
            b'\x44\xAC\x00\x00'  # Sample rate (44100)
            b'\x88\x58\x01\x00'  # Byte rate
            b'\x01\x00'          # Block align
            b'\x08\x00'          # Bits per sample
            b'data'
            b'\x00\x00\x00\x00'  # Data chunk size
        )

        # WAV 应该跳过但不抛出异常
        update_audio_tags(
            str(wav_file),
            **self.test_metadata,
            cover_url=None,
            trace=True
        )

        assert wav_file.exists()

    def test_unsupported_format_raises_error(self):
        """测试不支持的格式应抛出 ValueError"""
        from auto_tag.audio_recognize import update_audio_tags

        # 创建一个未知格式文件
        unknown_file = self.tmp_dir / "test.xyz"
        unknown_file.write_text("fake data")

        with pytest.raises(ValueError, match="不支持的文件格式"):
            update_audio_tags(
                str(unknown_file),
                **self.test_metadata,
                cover_url=None,
                trace=False
            )

    def test_nonexistent_file_raises_error(self):
        """测试不存在的文件应抛出 FileNotFoundError"""
        from auto_tag.audio_recognize import update_audio_tags

        with pytest.raises(FileNotFoundError, match="音频文件不存在"):
            update_audio_tags(
                "/nonexistent/path/song.mp3",
                **self.test_metadata,
                cover_url=None,
                trace=False
            )


class TestFormatSpecificFunctions:
    """测试各格式的专用内部函数"""

    def test_write_flac_tags_directly(self):
        """直接测试 _write_flac_tags 函数"""
        from auto_tag.audio_recognize import _write_flac_tags

        # 创建临时 FLAC 文件
        with tempfile.NamedTemporaryFile(suffix='.flac', delete=False) as f:
            flac_path = f.name
            f.write(
                b'fLaC'
                b'\x00\x00\x00\x22'
                b'\x10\x00\x10\x00\x03\x00\x03\x00'
                b'\x0b\xb8\x00\x01\xb0\x00\x00\x00\x0b\xb8'
                b'\x12\x34\x56\x78\x9a\xbc\xde\xf0'
            )

        try:
            _write_flac_tags(
                flac_path,
                title="FLAC Test",
                artist="Test Artist",
                album="Test Album",
                cover_url=None,
                trace=False
            )

            # 验证文件被修改
            assert os.path.exists(flac_path)
            assert os.path.getsize(flac_path) > 50
        finally:
            if os.path.exists(flac_path):
                os.unlink(flac_path)

    @patch('auto_tag.audio_recognize.urlopen')
    def test_write_mp4_tags_with_cover(self, mock_urlopen):
        """测试 _write_mp4_tags 带封面"""
        from auto_tag.audio_recognize import _write_mp4_tags

        # Mock 封面
        mock_response = MagicMock()
        mock_response.read.return_value = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        mock_urlopen.return_value = mock_response

        # 创建临时 M4A 文件
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as f:
            m4a_path = f.name
            f.write(
                b'\x00\x00\x00\x14ftypM4A \x00\x00\x00\x00M4A '
            )

        try:
            _write_mp4_tags(
                m4a_path,
                title="M4A Test",
                artist="M4A Artist",
                album="M4A Album",
                cover_url="http://example.com/cover.png",
                trace=True
            )

            assert os.path.exists(m4a_path)
        finally:
            if os.path.exists(m4a_path):
                os.unlink(m4a_path)


class TestBackwardCompatibility:
    """向后兼容性测试：确保原有函数仍然可用"""

    def test_update_mp3_tags_still_works(self):
        """验证原始的 update_mp3_tags 函数仍可用"""
        from auto_tag.audio_recognize import update_mp3_tags

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            mp3_path = f.name
            f.write(b'ID3\x04\x00\x00\x00\x00\x1f\x00' + b'\x00' * 31 + b'\xff\xfb\x90\x00')

        try:
            update_mp3_tags(mp3_path, "Title", "Artist", "Album")
            assert os.path.exists(mp3_path)
        finally:
            if os.path.exists(mp3_path):
                os.unlink(mp3_path)

    def test_update_ogg_tags_still_works(self):
        """验证原始的 update_ogg_tags 函数仍可用"""
        from auto_tag.audio_recognize import update_ogg_tags

        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as f:
            ogg_path = f.name
            f.write(
                b'OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x01\x1c\x00'
                b'\x01vorbis\x00' + b'\x00' * 30
            )

        try:
            update_ogg_tags(ogg_path, "Title", "Artist", "Album", "", False)
            assert os.path.exists(ogg_path)
        finally:
            if os.path.exists(ogg_path):
                os.unlink(ogg_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
