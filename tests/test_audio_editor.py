# -*- coding: utf-8 -*-
"""
音频编辑器核心功能单元测试
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from auto_tag.editor.audio_editor import AudioEditor
from auto_tag.editor.config import (
    EditorConfig,
    NormalizeConfig,
    TrimConfig,
    TrimMode,
)
from auto_tag.converter.config import OutputFormat, QualityPreset


class TestAudioEditorInit:
    """AudioEditor 初始化测试"""

    def test_init_with_ffmpeg_available(self):
        """FFmpeg 可用时正常初始化"""
        with patch("auto_tag.editor.audio_editor.ffmpeg.probe"):
            with patch("auto_tag.editor.audio_editor.ffmpeg.run"):
                editor = AudioEditor()
                assert editor is not None

    def test_init_without_ffmpeg_raises_error(self):
        """FFmpeg 不可用时抛出 RuntimeError"""
        with patch("auto_tag.editor.audio_editor.ffmpeg.probe", side_effect=FileNotFoundError):
            with pytest.raises(RuntimeError, match="FFmpeg 未安装"):
                AudioEditor()


class TestTrimAudio:
    """音频裁剪功能测试"""

    @pytest.fixture
    def editor(self):
        """创建编辑器实例（mock FFmpeg）"""
        with patch("auto_tag.editor.audio_editor.ffmpeg.probe"), \
             patch("auto_tag.editor.audio_editor.ffmpeg.run"):
            return AudioEditor()

    def test_trim_audio_manual_mode_success(self, editor, tmp_path):
        """手动模式裁剪成功"""
        input_file = tmp_path / "input.mp3"
        output_file = tmp_path / "output.mp3"
        input_file.write_bytes(b"fake audio data")
        output_file.write_bytes(b"fake output data")

        with patch.object(editor, '_run_ffmpeg_safe'), \
             patch.object(editor, '_safe_path', side_effect=lambda x: x), \
             patch.object(editor, '_has_special_chars', return_value=False), \
             patch("auto_tag.editor.audio_editor.ffmpeg.input") as mock_input, \
             patch("auto_tag.editor.audio_editor.ffmpeg.probe") as mock_probe:

            mock_stream = MagicMock()
            mock_input.return_value.audio.filter.return_value = mock_stream
            mock_stream.filter.return_value.output.return_value = MagicMock()

            mock_probe.return_value = {
                "format": {"duration": "180.0"},
                "streams": [{"codec_type": "audio"}]
            }

            config = TrimConfig(
                mode=TrimMode.MANUAL,
                start_time=10.0,
                end_time=60.0,
            )
            result = editor.trim_audio(str(input_file), str(output_file), config)

            assert result["success"] is True
            assert "duration" in result

    def test_trim_audio_file_not_found(self, editor):
        """文件不存在时返回错误"""
        config = TrimConfig(mode=TrimMode.MANUAL, start_time=0.0, end_time=30.0)
        result = editor.trim_audio("/nonexistent/file.mp3", "/output.mp3", config)

        assert result["success"] is False
        assert "不存在" in result["error"]

    def test_trim_audio_invalid_time_range(self, editor, tmp_path):
        """无效时间范围（结束时间 <= 开始时间）返回错误"""
        input_file = tmp_path / "input.mp3"
        input_file.write_bytes(b"fake audio data")

        config = TrimConfig(
            mode=TrimMode.MANUAL,
            start_time=60.0,
            end_time=10.0,
        )
        result = editor.trim_audio(str(input_file), "/output.mp3", config)

        assert result["success"] is False
        assert "配置验证失败" in result["error"]

    def test_trim_auto_mode(self, editor, tmp_path):
        """自动静音检测模式"""
        input_file = tmp_path / "input.mp3"
        output_file = tmp_path / "output.mp3"
        input_file.write_bytes(b"fake audio data")
        output_file.write_bytes(b"fake output data")

        config = TrimConfig(
            mode=TrimMode.AUTO,
            silence_threshold=-50.0,
            min_silence_duration=1.0,
        )

        with patch.object(editor, '_run_ffmpeg_safe'), \
             patch.object(editor, '_safe_path', side_effect=lambda x: x), \
             patch.object(editor, '_has_special_chars', return_value=False), \
             patch("auto_tag.editor.audio_editor.ffmpeg.input") as mock_input, \
             patch("auto_tag.editor.audio_editor.ffmpeg.probe", return_value={
                "format": {"duration": "180.0"},
                "streams": [{"codec_type": "audio"}]
             }):

            mock_stream = MagicMock()
            mock_input.return_value.audio.filter.return_value = mock_stream
            mock_stream.filter.return_value.output.return_value = MagicMock()

            result = editor.trim_audio(str(input_file), str(output_file), config)
            assert result.get("mode") == "auto"


class TestNormalizeVolume:
    """音量标准化功能测试"""

    @pytest.fixture
    def editor(self):
        """创建编辑器实例"""
        with patch("auto_tag.editor.audio_editor.ffmpeg.probe"), \
             patch("auto_tag.editor.audio_editor.ffmpeg.run"):
            return AudioEditor()

    def test_normalize_volume_success(self, editor, tmp_path):
        """音量标准化成功"""
        input_file = tmp_path / "input.mp3"
        output_file = tmp_path / "output.mp3"
        input_file.write_bytes(b"fake audio data")

        config = NormalizeConfig(target_loudness=-16.0, true_peak=-1.5, lra=11.0)

        with patch.object(editor, '_run_ffmpeg_safe'), \
             patch.object(editor, '_safe_path', side_effect=lambda x: x), \
             patch("auto_tag.editor.audio_editor.ffmpeg.input") as mock_input, \
             patch("auto_tag.editor.audio_editor.ffmpeg.probe") as mock_probe, \
             patch.object(editor, 'get_audio_info', return_value={"success": True, "loudness_i": -23.0}):

            mock_stream = MagicMock()
            mock_input.return_value.audio.filter.return_value = mock_stream
            mock_stream.output.return_value = MagicMock()
            
            mock_probe.return_value = {
                "format": {"duration": "180.0"},
                "streams": [{"codec_type": "audio"}]
            }

            result = editor.normalize_volume(str(input_file), str(output_file), config)

            assert result["success"] is True
            assert "before_loudness" in result or result.get("success")

    def test_normalize_custom_target(self, editor, tmp_path):
        """自定义目标响度"""
        input_file = tmp_path / "input.mp3"
        output_file = tmp_path / "output.mp3"
        input_file.write_bytes(b"fake audio data")

        config = NormalizeConfig(target_loudness=-14.0, true_peak=-2.0, lra=8.0)

        with patch.object(editor, '_run_ffmpeg_safe'), \
             patch.object(editor, '_safe_path', side_effect=lambda x: x), \
             patch("auto_tag.editor.audio_editor.ffmpeg.input"), \
             patch("auto_tag.editor.audio_editor.ffmpeg.probe", return_value={
                "format": {"duration": "180.0"},
                "streams": [{"codec_type": "audio"}]
             }), \
             patch.object(editor, 'get_audio_info', return_value={"success": True}):

            result = editor.normalize_volume(str(input_file), str(output_file), config)
            assert result["success"] is True


class TestGetAudioInfo:
    """获取音频信息测试"""

    @pytest.fixture
    def editor(self):
        with patch("auto_tag.editor.audio_editor.ffmpeg.probe"), \
             patch("auto_tag.editor.audio_editor.ffmpeg.run"):
            return AudioEditor()

    def test_get_audio_info_returns_correct_data(self, editor, tmp_path):
        """正确获取音频信息"""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        mock_probe_result = {
            "format": {
                "duration": "180.5",
                "size": "5120000",
                "bit_rate": "256000",
            },
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "sample_rate": "44100",
                    "channels": "2",
                    "bit_rate": "256000",
                }
            ]
        }

        with patch("auto_tag.editor.audio_editor.ffmpeg.probe", return_value=mock_probe_result):
            result = editor.get_audio_info(str(audio_file))

            assert result["success"] is True
            assert abs(result["duration"] - 180.5) < 0.01
            assert result["sample_rate"] == 44100
            assert result["channels"] == 2
            assert result["codec_name"] == "mp3"

    def test_get_audio_info_file_not_found(self, editor):
        """文件不存在时返回错误"""
        result = editor.get_audio_info("/nonexistent/audio.mp3")
        assert result["success"] is False
        assert "不存在" in result["error"]
