# -*- coding: utf-8 -*-
"""
AudioConverter 类的单元测试
"""

import os
import tempfile
from pathlib import Path

import pytest

from auto_tag.converter import AudioConverter, ConverterConfig
from auto_tag.converter.config import OutputFormat, QualityPreset


class TestAudioConverter:
    """AudioConverter 类测试"""
    
    @pytest.fixture
    def converter(self):
        """创建 AudioConverter 实例"""
        return AudioConverter()
    
    @pytest.fixture
    def config(self):
        """创建默认配置"""
        return ConverterConfig()
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_supported_formats(self, converter):
        """测试支持的格式列表"""
        # 检查输入格式
        assert "mp3" in converter.SUPPORTED_INPUT_FORMATS
        assert "flac" in converter.SUPPORTED_INPUT_FORMATS
        assert "mp4" in converter.SUPPORTED_INPUT_FORMATS
        assert "mkv" in converter.SUPPORTED_INPUT_FORMATS
        
        # 检查输出格式
        assert "mp3" in converter.SUPPORTED_OUTPUT_FORMATS
        assert "flac" in converter.SUPPORTED_OUTPUT_FORMATS
        assert "mp4" not in converter.SUPPORTED_OUTPUT_FORMATS
    
    def test_detect_format_nonexistent_file(self, converter):
        """测试检测不存在的文件格式"""
        result = converter.detect_format("nonexistent_file.mp3")
        assert result is None
    
    def test_convert_file_nonexistent_input(self, converter, config, temp_dir):
        """测试转换不存在的文件"""
        output_path = os.path.join(temp_dir, "output.mp3")
        result = converter.convert_file("nonexistent.mp3", output_path, config)
        assert result is False
    
    def test_convert_file_unsupported_output_format(self, converter, config, temp_dir):
        """测试不支持的输出格式"""
        # 创建一个临时测试文件
        input_path = os.path.join(temp_dir, "test.txt")
        Path(input_path).touch()
        
        output_path = os.path.join(temp_dir, "output.mp3")
        
        # 由于文件格式不支持，应该返回 False
        result = converter.convert_file(input_path, output_path, config)
        assert result is False
    
    def test_parse_ffmpeg_args(self, converter):
        """测试解析 FFmpeg 参数"""
        args = ['-c:a', 'libmp3lame', '-b:a', '320k', '-ar', '48000']
        result = converter._parse_ffmpeg_args(args)
        
        assert result['c:a'] == 'libmp3lame'
        assert result['b:a'] == '320k'
        assert result['ar'] == '48000'
    
    def test_config_get_ffmpeg_args(self, config):
        """测试配置获取 FFmpeg 参数"""
        args = config.get_ffmpeg_args()
        
        # 默认配置是 MP3 格式
        assert '-c:a' in args
        assert 'libmp3lame' in args
        assert '-b:a' in args
    
    def test_config_set_output_format(self, config):
        """测试设置输出格式"""
        config.set_output_format("flac", QualityPreset.LOSSLESS)
        
        assert config.output_format.format == OutputFormat.FLAC
        assert config.output_format.codec == "flac"
    
    def test_config_get_output_extension(self, config):
        """测试获取输出扩展名"""
        config.set_output_format("mp3")
        assert config.get_output_extension() == ".mp3"
        
        config.set_output_format("flac")
        assert config.get_output_extension() == ".flac"
    
    def test_convert_batch_empty_list(self, converter, config, temp_dir):
        """测试批量转换空列表"""
        results = converter.convert_batch([], temp_dir, config)
        assert results == {}
    
    def test_convert_batch_nonexistent_files(self, converter, config, temp_dir):
        """测试批量转换不存在的文件"""
        files = ["nonexistent1.mp3", "nonexistent2.mp3"]
        results = converter.convert_batch(files, temp_dir, config)
        
        assert len(results) == 2
        assert all(not success for success in results.values())
    
    def test_progress_callback(self, converter, config, temp_dir):
        """测试进度回调功能"""
        # 创建一个临时测试文件
        input_path = os.path.join(temp_dir, "test.txt")
        Path(input_path).touch()
        
        output_path = os.path.join(temp_dir, "output.mp3")
        
        progress_values = []
        
        def callback(progress: float):
            progress_values.append(progress)
        
        # 由于文件格式不支持，转换会失败，但不会抛出异常
        result = converter.convert_file(input_path, output_path, config, callback)
        assert result is False


class TestConverterConfig:
    """ConverterConfig 类测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = ConverterConfig()
        
        assert config.output_format.format == OutputFormat.MP3
        assert config.quality_preset == QualityPreset.HIGH
        assert config.preserve_metadata is True
        assert config.overwrite_existing is False
    
    def test_quality_presets(self):
        """测试质量预设"""
        config = ConverterConfig()
        
        # 测试 LOW 预设
        config.set_output_format("mp3", QualityPreset.LOW)
        assert config.output_format.bitrate == 128
        
        # 测试 MEDIUM 预设
        config.set_output_format("mp3", QualityPreset.MEDIUM)
        assert config.output_format.bitrate == 192
        
        # 测试 HIGH 预设
        config.set_output_format("mp3", QualityPreset.HIGH)
        assert config.output_format.bitrate == 320
    
    def test_flac_config(self):
        """测试 FLAC 格式配置"""
        config = ConverterConfig()
        config.set_output_format("flac", QualityPreset.LOSSLESS)
        
        assert config.output_format.format == OutputFormat.FLAC
        assert config.output_format.codec == "flac"
        assert config.output_format.bitrate is None  # FLAC 无损，无比特率
    
    def test_unsupported_format(self):
        """测试不支持的格式"""
        config = ConverterConfig()
        
        with pytest.raises(ValueError, match="不支持的输出格式"):
            config.set_output_format("xyz")
