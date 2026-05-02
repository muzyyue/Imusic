# -*- coding: utf-8 -*-
"""
编辑器配置和预设管理单元测试
"""

import json
import pytest
from pathlib import Path

from auto_tag.editor.config import (
    EditorConfig,
    NormalizeConfig,
    TrimConfig,
    TrimMode,
)
from auto_tag.editor.presets import PresetManager, BUILTIN_PRESETS
from auto_tag.converter.config import OutputFormat, QualityPreset


class TestTrimConfig:
    """裁剪配置测试"""

    def test_manual_mode_valid(self):
        """手动模式有效配置"""
        config = TrimConfig(
            mode=TrimMode.MANUAL,
            start_time=10.0,
            end_time=180.0,
        )
        valid, error = config.validate()
        assert valid is True
        assert error == ""

    def test_auto_mode_valid(self):
        """自动模式有效配置"""
        config = TrimConfig(mode=TrimMode.AUTO, silence_threshold=-50.0)
        valid, error = config.validate()
        assert valid is True

    def test_duration_mode_valid(self):
        """时长模式有效配置"""
        config = TrimConfig(mode=TrimMode.DURATION, duration=30.0, start_time=5.0)
        valid, error = config.validate()
        assert valid is True

    def test_invalid_negative_start_time(self):
        """负数开始时间"""
        config = TrimConfig(mode=TrimMode.MANUAL, start_time=-1.0, end_time=60.0)
        valid, error = config.validate()
        assert valid is False
        assert "不能为负数" in error

    def test_invalid_end_before_start(self):
        """结束时间早于开始时间"""
        config = TrimConfig(mode=TrimMode.MANUAL, start_time=100.0, end_time=50.0)
        valid, error = config.validate()
        assert valid is False
        assert "大于开始时间" in error

    def test_invalid_zero_duration(self):
        """零时长"""
        config = TrimConfig(mode=TrimMode.DURATION, duration=0.0)
        valid, error = config.validate()
        assert valid is False
        assert "大于0" in error

    def test_serialization_roundtrip(self):
        """序列化和反序列化往返测试"""
        original = TrimConfig(
            mode=TrimMode.MANUAL,
            start_time=10.0,
            end_time=180.0,
            fade_in=0.5,
            fade_out=1.0,
        )
        data = original.to_dict()
        restored = TrimConfig.from_dict(data)

        assert restored.mode == original.mode
        assert restored.start_time == original.start_time
        assert restored.end_time == original.end_time
        assert restored.fade_in == original.fade_in
        assert restored.fade_out == original.fade_out


class TestNormalizeConfig:
    """音量标准化配置测试"""

    def test_default_values(self):
        """默认值正确"""
        config = NormalizeConfig()
        assert config.target_loudness == -16.0
        assert config.true_peak == -1.5
        assert config.lra == 11.0

    def test_to_ffmpeg_filter(self):
        """FFmpeg 滤镜字符串生成正确"""
        config = NormalizeConfig(target_loudness=-14.0, true_peak=-2.0, lra=8.0)
        filter_str = config.to_ffmpeg_filter()

        assert "I=-14.0" in filter_str
        assert "TP=-2.0" in filter_str
        assert "LRA=8.0" in filter_str


class TestEditorConfig:
    """编辑器主配置测试"""

    def test_default_config_valid(self):
        """默认配置有效"""
        config = EditorConfig()
        valid, error = config.validate()
        assert valid is True

    def test_custom_config_valid(self):
        """自定义配置有效"""
        config = EditorConfig(
            trim=TrimConfig(mode=TrimMode.MANUAL, start_time=5.0, end_time=120.0),
            normalize=NormalizeConfig(target_loudness=-14.0),
            output_format=OutputFormat.FLAC,
            quality_preset=QualityPreset.LOSSLESS,
        )
        valid, error = config.validate()
        assert valid is True

    def test_invalid_loudness_range(self):
        """无效的响度范围"""
        config = EditorConfig(normalize=NormalizeConfig(target_loudness=0.0))
        valid, error = config.validate()
        assert valid is False
        assert "响度范围" in error

    def test_json_serialization(self):
        """JSON 序列化/反序列化往返"""
        original = EditorConfig(
            trim=TrimConfig(mode=TrimMode.DURATION, duration=30.0),
            normalize=NormalizeConfig(target_loudness=-14.0),
            output_format=OutputFormat.M4A,
            quality_preset=QualityPreset.HIGH,
            overwrite_original=True,
        )

        json_str = original.to_json()
        restored = EditorConfig.from_json(json_str)

        assert restored.trim.mode == original.trim.mode
        assert restored.trim.duration == original.trim.duration
        assert restored.normalize.target_loudness == original.normalize.target_loudness
        assert restored.output_format == original.output_format
        assert restored.overwrite_original == original.overwrite_original


class TestPresetManager:
    """预设管理器测试"""

    def test_get_builtin_presets_returns_all(self):
        """获取所有内置预设"""
        manager = PresetManager()
        presets = manager.get_builtin_presets()

        assert len(presets) == 5
        assert "ringtone" in presets
        assert "car_audio" in presets
        assert "hifi_archive" in presets
        assert "podcast" in presets
        assert "music_share" in presets

    def test_get_preset_by_valid_name(self):
        """通过名称获取预设"""
        manager = PresetManager()
        preset = manager.get_preset("ringtone")

        assert preset is not None
        assert "name" in preset
        assert "config" in preset
        assert "icon" in preset

    def test_get_preset_by_invalid_name_returns_none(self):
        """无效名称返回 None"""
        manager = PresetManager()
        preset = manager.get_preset("nonexistent_preset")
        assert preset is None

    def test_get_all_presets_includes_builtin_and_custom(self):
        """获取所有预设包含内置和自定义"""
        manager = PresetManager()
        all_presets = manager.get_all_presets()

        assert len(all_presets) >= 5  # 至少包含5个内置预设

    def test_validate_preset_valid_config(self):
        """有效预设验证通过"""
        manager = PresetManager()
        ringtone_preset = BUILTIN_PRESETS["ringtone"]
        valid, error = manager.validate_preset(ringtone_preset)
        assert valid is True
        assert error == ""

    def test_validate_preset_missing_required_field(self):
        """缺少必需字段验证失败"""
        manager = PresetManager()
        invalid_preset = {"name": {"zh": "Test"}, "icon": "🎵"}
        valid, error = manager.validate_preset(invalid_preset)
        assert valid is False
        assert "缺少必需字段" in error

    def test_create_custom_preset_success(self, tmp_path):
        """成功创建自定义预设"""
        manager = PresetManager(custom_presets_file=str(tmp_path / "custom.json"))
        config = EditorConfig(trim=TrimConfig(mode=TrimMode.DURATION, duration=15.0))

        success, error = manager.create_custom_preset(
            name="custom_short",
            config=config,
            icon="✂️",
            description_zh="短铃声",
            description_en="Short ringtone",
        )
        assert success is True
        assert error == ""

        retrieved = manager.get_preset("custom_short")
        assert retrieved is not None
        assert retrieved["is_custom"] is True

    def test_create_custom_preset_cannot_override_builtin(self, tmp_path):
        """不能覆盖内置预设"""
        manager = PresetManager(custom_presets_file=str(tmp_path / "custom.json"))
        config = EditorConfig()

        success, error = manager.create_custom_preset(name="ringtone", config=config)
        assert success is False
        assert "不能覆盖内置预设" in error

    def test_delete_custom_preset(self, tmp_path):
        """删除自定义预设"""
        manager = PresetManager(custom_presets_file=str(tmp_path / "custom.json"))
        config = EditorConfig()

        manager.create_custom_preset("to_delete", config=config)
        success, error = manager.delete_custom_preset("to_delete")

        assert success is True
        assert manager.get_preset("to_delete") is None

    def test_delete_nonexistent_preset(self, tmp_path):
        """删除不存在的自定义预设"""
        manager = PresetManager(custom_presets_file=str(tmp_path / "custom.json"))
        success, error = manager.delete_custom_preset("ghost_preset")
        assert success is False
        assert "不存在" in error

    def test_get_preset_for_language_zh(self):
        """获取中文本地化预设信息"""
        localized = PresetManager.get_preset_for_language("ringtone", "zh")
        assert localized is not None
        assert "手机铃声" in localized["display_name"]

    def test_get_preset_for_language_en(self):
        """获取英文本地化预设信息"""
        localized = PresetManager.get_preset_for_language("car_audio", "en")
        assert localized is not None
        assert "Car Audio" in localized["display_name"]

    def test_get_preset_names_returns_list(self):
        """获取预设名称列表返回列表"""
        names = PresetManager.get_preset_names()
        assert isinstance(names, list)
        assert len(names) == 5
        assert "ringtone" in names
