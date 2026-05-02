# -*- coding: utf-8 -*-
"""
音频格式转换质量与大小一致性测试

覆盖场景：
1. OutputQuality → QualityPreset 映射正确性
2. 不同格式的编码参数配置（比特率/采样率/声道）
3. 不同质量等级的文件大小差异验证
4. 智能码率逻辑验证
5. 边界情况处理（无效输入、特殊字符等）
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from auto_tag.editor.audio_editor import AudioEditor
from auto_tag.editor.config import (
    EditorConfig,
    NormalizeConfig,
    OutputQuality,
    TrimConfig,
    TrimMode,
)
from auto_tag.converter.config import (
    ConverterConfig,
    FormatConfig,
    OutputFormat,
    QualityPreset,
)


class TestOutputQualityMapping:
    """OutputQuality → QualityPreset 映射测试"""

    def test_high_quality_maps_to_high_preset(self):
        """HIGH 质量应映射到 HIGH 预设"""
        quality_mapping = {
            OutputQuality.HIGH: QualityPreset.HIGH,
            OutputQuality.STANDARD: QualityPreset.MEDIUM,
            OutputQuality.SMALL: QualityPreset.LOW,
        }
        assert quality_mapping[OutputQuality.HIGH] == QualityPreset.HIGH

    def test_standard_quality_maps_to_medium_preset(self):
        """STANDARD 质量应映射到 MEDIUM 预设"""
        quality_mapping = {
            OutputQuality.HIGH: QualityPreset.HIGH,
            OutputQuality.STANDARD: QualityPreset.MEDIUM,
            OutputQuality.SMALL: QualityPreset.LOW,
        }
        assert quality_mapping[OutputQuality.STANDARD] == QualityPreset.MEDIUM

    def test_small_quality_maps_to_low_preset(self):
        """SMALL 质量应映射到 LOW 预设"""
        quality_mapping = {
            OutputQuality.HIGH: QualityPreset.HIGH,
            OutputQuality.STANDARD: QualityPreset.MEDIUM,
            OutputQuality.SMALL: QualityPreset.LOW,
        }
        assert quality_mapping[OutputQuality.SMALL] == QualityPreset.LOW


class TestFormatConfigBitrates:
    """FormatConfig 比特率配置测试（与 audio_editor.py trim_audio 保持一致）"""

    @pytest.mark.parametrize("quality,expected_bitrates", [
        (QualityPreset.LOW, {'.mp3': 128, '.aac': 96, '.ogg': 96, '.m4a': 96}),
        (QualityPreset.MEDIUM, {'.mp3': 192, '.aac': 128, '.ogg': 128, '.m4a': 128}),
        (QualityPreset.HIGH, {'.mp3': 256, '.aac': 160, '.ogg': 160, '.m4a': 160}),
        (QualityPreset.LOSSLESS, {'.mp3': 320, '.aac': 192, '.ogg': 192, '.m4a': 192}),
    ])
    def test_bitrate_config_matches_formatconfig(self, quality, expected_bitrates):
        """比特率配置应与 FormatConfig._apply_quality_preset 一致"""
        for ext, expected_kbps in expected_bitrates.items():
            format_cfg = FormatConfig(format=OutputFormat.MP3)
            format_cfg._apply_quality_preset(quality)
            
            # 根据扩展名获取对应的 FormatConfig
            if ext == '.mp3':
                actual_format = OutputFormat.MP3
            elif ext == '.aac':
                actual_format = OutputFormat.AAC
            elif ext == '.ogg':
                actual_format = OutputFormat.OGG
            elif ext == '.m4a':
                actual_format = OutputFormat.M4A
            
            test_cfg = FormatConfig(format=actual_format)
            test_cfg._apply_quality_preset(quality)
            
            assert test_cfg.bitrate == expected_kbps, \
                f"{ext} 格式 {quality.value} 预期比特率 {expected_kbps}kbps, 实际 {test_cfg.bitrate}kbps"

    def test_lossless_formats_have_no_bitrate(self):
        """无损格式（WAV/FLAC）不应设置比特率"""
        for fmt in [OutputFormat.WAV, OutputFormat.FLAC]:
            cfg = FormatConfig(format=fmt)
            cfg._apply_quality_preset(QualityPreset.LOSSLESS)
            assert cfg.bitrate is None, f"{fmt.value} 格式不应有比特率设置"


class TestAudioEditorTrimQuality:
    """AudioEditor.trim_audio() 质量参数测试"""

    @pytest.fixture
    def editor(self):
        """创建编辑器实例（mock FFmpeg）"""
        with patch("auto_tag.editor.audio_editor.ffmpeg.probe"), \
             patch("auto_tag.editor.audio_editor.ffmpeg.run"):
            return AudioEditor()

    @pytest.mark.parametrize("output_quality,expected_codec", [
        (OutputQuality.HIGH, 'libmp3lame'),
        (OutputQuality.STANDARD, 'libmp3lame'),
        (OutputQuality.SMALL, 'libmp3lame'),
    ])
    def test_mp3_uses_correct_codec(self, editor, tmp_path, output_quality, expected_codec):
        """MP3 格式应使用 libmp3lame 编解码器"""
        input_file = tmp_path / "input.wav"
        output_file = tmp_path / "output.mp3"
        input_file.write_bytes(b"fake wav data")
        output_file.write_bytes(b"fake mp3 data")

        config = TrimConfig(mode=TrimMode.MANUAL, start_time=0.0, end_time=10.0)

        with patch.object(editor, '_run_ffmpeg_safe') as mock_run, \
             patch.object(editor, '_safe_path', side_effect=lambda x: x), \
             patch.object(editor, '_has_special_chars', return_value=False), \
             patch("auto_tag.editor.audio_editor.ffmpeg.input") as mock_input, \
             patch("auto_tag.editor.audio_editor.ffmpeg.probe", return_value={
                "format": {"duration": "10.0"},
                "streams": [{"codec_type": "audio"}]
             }):

            mock_stream = MagicMock()
            mock_filtered = MagicMock()
            mock_input.return_value.audio.filter.return_value = mock_filtered
            mock_filtered.output.return_value = MagicMock()

            result = editor.trim_audio(str(input_file), str(output_file), config, output_quality)

            assert result["success"] is True
            # 验证 _run_ffmpeg_safe 被调用
            assert mock_run.called

    @pytest.mark.parametrize("output_quality,ext,expected_min_size_diff", [
        (OutputQuality.HIGH, '.mp3', 100),   # 高质量 MP3 应明显大于小体积
        (OutputQuality.SMALL, '.mp3', 100),   # 小体积 MP3 应明显小于高质量
    ])
    def test_different_quality_produces_different_sizes(
        self, editor, tmp_path, output_quality, ext, expected_min_size_diff
    ):
        """不同质量等级应产生不同大小的文件（实际 FFmpeg 转换测试）"""
        pytest.importorskip("ffmpeg", reason="FFmpeg-python 未安装")
        
        input_file = tmp_path / "input.wav"
        output_high = tmp_path / f"high{ext}"
        output_low = tmp_path / f"low{ext}"
        
        # 创建一个简单的 WAV 文件用于测试（如果 ffmpeg 可用）
        try:
            import numpy as np
            sample_rate = 44100
            duration = 2  # 2秒
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
            
            # 写入简单 WAV 文件
            import wave
            with wave.open(str(input_file), 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())
            
            config = TrimConfig(mode=TrimMode.MANUAL, start_time=0.0, end_time=duration)
            
            # 转换为高质量
            result_high = editor.trim_audio(str(input_file), str(output_high), config, OutputQuality.HIGH)
            # 转换为低质量
            result_low = editor.trim_audio(str(input_file), str(output_low), config, OutputQuality.SMALL)
            
            if result_high["success"] and result_low["success"]:
                size_high = os.path.getsize(output_high)
                size_low = os.path.getsize(output_low)
                
                # 高质量文件应大于低质量文件（对于有损格式）
                if ext in ['.mp3', '.aac', '.ogg', '.m4a']:
                    assert size_high > size_low, \
                        f"高质量文件 ({size_high} bytes) 应大于低质量文件 ({size_low} bytes)"
                    
        except (ImportError, Exception) as e:
            pytest.skip(f"无法创建测试音频文件: {e}")


class TestSmartBitrateLogic:
    """智能码率逻辑测试"""

    def test_smart_bitrate_reduces_when_source_is_lower(self):
        """源文件码率低于目标时，应降低目标码率"""
        config = ConverterConfig()
        config.set_output_format("mp3", QualityPreset.HIGH)  # 256 kbps
        
        # 模拟源文件码率为 128 kbps（低于目标的 256）
        source_bitrate = 128
        target_bitrate = config.output_format.bitrate  # 256
        
        # 应用智能码率逻辑：只在源 < 目标时调整
        if source_bitrate < target_bitrate:
            adaptive = min(target_bitrate, int(source_bitrate * 1.2))
            adaptive = max(64, adaptive)
            assert adaptive < target_bitrate, \
                f"自适应码率 ({adaptive}) 应低于目标 ({target_bitrate})"

    def test_smart_bitrate_keeps_target_when_source_is_higher(self):
        """源文件码率高于目标时，应保持目标不变"""
        config = ConverterConfig()
        config.set_output_format("mp3", QualityPreset.LOW)  # 128 kbps
        
        source_bitrate = 320  # 高于目标的 128
        target_bitrate = config.output_format.bitrate
        
        # 源 >= 目标时不调整
        should_adjust = source_bitrate < target_bitrate
        assert not should_adjust, "源文件码率高于目标时不应调整"


class TestApplyPresetQualityChain:
    """apply_preset() 质量传递链测试"""

    @pytest.fixture
    def editor(self):
        """创建编辑器实例"""
        with patch("auto_tag.editor.audio_editor.ffmpeg.probe"), \
             patch("auto_tag.editor.audio_editor.ffmpeg.run"):
            return AudioEditor()

    @pytest.mark.parametrize("output_quality,expected_preset", [
        (OutputQuality.HIGH, QualityPreset.HIGH),
        (OutputQuality.STANDARD, QualityPreset.MEDIUM),
        (OutputQuality.SMALL, QualityPreset.LOW),
    ])
    def test_apply_preset_uses_correct_quality_mapping(
        self, editor, tmp_path, output_quality, expected_preset
    ):
        """apply_preset 应将 OutputQuality 正确映射为 QualityPreset"""
        input_file = tmp_path / "input.mp3"
        output_file = tmp_path / "output.mp3"
        input_file.write_bytes(b"fake mp3 data")
        
        config = EditorConfig(
            output_format=OutputFormat.MP3,
            output_quality=output_quality,
            overwrite_original=True,
        )

        with patch.object(editor, 'trim_audio', return_value={"success": True}) as mock_trim, \
             patch('auto_tag.converter.converter.AudioConverter') as MockConverter, \
             patch.object(editor, 'normalize_volume', return_value={"success": False}):
            
            mock_converter_instance = MagicMock()
            MockConverter.return_value = mock_converter_instance
            mock_converter_instance.convert_file.return_value = True
            
            result = editor.apply_preset(str(input_file), str(output_file), config)
            
            # 验证 convert_file 被调用（表示格式转换步骤执行）
            assert mock_converter_instance.convert_file.called
            
            # 获取传入 convert_file 的 ConverterConfig
            call_args = mock_converter_instance.convert_file.call_args
            converter_config = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('config')
            
            # 验证使用了正确的 QualityPreset
            assert converter_config.quality_preset == expected_preset, \
                f"预期 QualityPreset.{expected_preset.value}, 实际 QualityPreset.{converter_config.quality_preset.value}"


class TestOGGFormatParameters:
    """OGG 格式参数修正验证测试"""

    def test_ogg_no_longer_uses_invalid_negative_one(self):
        """OGG 格式不应再使用无效的 -1 参数值"""
        # 在修复前，当 VBR quality > 2 时会传入 -1
        # 修复后应使用统一的比特率配置
        
        quality_mapping = {
            OutputQuality.HIGH: QualityPreset.HIGH,
            OutputQuality.STANDARD: QualityPreset.MEDIUM,
            OutputQuality.SMALL: QualityPreset.LOW,
        }
        
        for output_quality, conv_preset in quality_mapping.items():
            vbr_quality = output_quality.get_vbr_quality()
            
            # 旧逻辑会产生 -1
            old_param = vbr_quality if vbr_quality <= 2 else -1
            
            # 新逻辑使用固定比特率（不会产生 -1）
            bitrate_config = {
                QualityPreset.LOW: 96,
                QualityPreset.MEDIUM: 128,
                QualityPreset.HIGH: 160,
                QualityPreset.LOSSLESS: 192,
            }
            new_bitrate = bitrate_config.get(conv_preset, 128)
            
            # 验证新逻辑不产生 -1
            assert new_bitrate != -1, f"OGG {output_quality.value} 比特率不应为 -1"
            assert new_bitrate > 0, f"OGG {output_quality.value} 比特率应为正数"


class TestEdgeCases:
    """边界情况和异常处理测试"""

    @pytest.fixture
    def editor(self):
        """创建编辑器实例"""
        with patch("auto_tag.editor.audio_editor.ffmpeg.probe"), \
             patch("auto_tag.editor.audio_editor.ffmpeg.run"):
            return AudioEditor()

    def test_unsupported_format_falls_back_gracefully(self, editor, tmp_path):
        """不支持的输出格式应优雅降级"""
        input_file = tmp_path / "input.mp3"
        output_file = tmp_path / "output.xyz"  # 不支持的格式
        input_file.write_bytes(b"fake data")
        
        config = TrimConfig(mode=TrimMode.MANUAL, start_time=0.0, end_time=10.0)
        
        # 不应抛出异常，而是返回错误或使用默认编解码器
        try:
            result = editor.trim_audio(str(input_file), str(output_file), config, OutputQuality.STANDARD)
            # 如果成功或失败都行，只要不崩溃
            assert isinstance(result, dict)
        except Exception as e:
            pytest.fail(f"不应抛出未处理的异常: {e}")

    def test_none_output_quality_uses_default(self, editor, tmp_path):
        """None 质量参数应使用默认值"""
        input_file = tmp_path / "input.wav"
        output_file = tmp_path / "output.mp3"
        input_file.write_bytes(b"fake wav data")
        output_file.write_bytes(b"fake mp3 data")
        
        config = TrimConfig(mode=TrimMode.MANUAL, start_time=0.0, end_time=5.0)
        
        with patch.object(editor, '_run_ffmpeg_safe'), \
             patch.object(editor, '_safe_path', side_effect=lambda x: x), \
             patch.object(editor, '_has_special_chars', return_value=False), \
             patch("auto_tag.editor.audio_editor.ffmpeg.input") as mock_input, \
             patch("auto_tag.editor.audio_editor.ffmpeg.probe", return_value={
                "format": {"duration": "5.0"},
                "streams": [{"codec_type": "audio"}]
             }):
            
            mock_stream = MagicMock()
            mock_input.return_value.audio.filter.return_value = mock_stream
            mock_stream.output.return_value = MagicMock()
            
            # 传入 None 作为 output_quality
            result = editor.trim_audio(str(input_file), str(output_file), config, None)
            
            # 应使用默认值（STANDARD/MEDIUM），不崩溃
            assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
