# -*- coding: utf-8 -*-
"""
音频编辑配置模块

定义音频编辑的参数配置选项，包括裁剪模式、音量标准化参数、输出格式等。

使用示例：
>>> from auto_tag.editor.config import TrimMode, TrimConfig, EditorConfig
>>> config = EditorConfig(
...     trim=TrimConfig(mode=TrimMode.MANUAL, start_time=10.0, end_time=180.0),
...     output_format=OutputFormat.MP3
... )
"""

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Optional

from auto_tag.converter.config import OutputFormat, QualityPreset


class TrimMode(Enum):
    """裁剪模式枚举"""
    AUTO = "auto"
    MANUAL = "manual"
    DURATION = "duration"


class OutputQuality(Enum):
    """输出质量枚举（控制文件体积与音质平衡）"""
    
    HIGH = "high"
    STANDARD = "standard"
    SMALL = "small"
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        names = {
            OutputQuality.HIGH: "高质量",
            OutputQuality.STANDARD: "标准",
            OutputQuality.SMALL: "小体积",
        }
        return names.get(self, self.value)
    
    @property
    def description(self) -> str:
        """质量描述"""
        descriptions = {
            OutputQuality.HIGH: "最佳音质，文件较大 (VBR q:0-1)",
            OutputQuality.STANDARD: "平衡音质与体积 (VBR q:2) [推荐]",
            OutputQuality.SMALL: "较小体积，适合移动设备 (VBR q:4-6)",
        }
        return descriptions.get(self, "")
    
    def get_vbr_quality(self) -> int:
        """
        获取 VBR 质量参数
        
        Returns:
            int: VBR 质量等级 (0-9, 0=最高质量)
        """
        vbr_map = {
            OutputQuality.HIGH: 0,
            OutputQuality.STANDARD: 2,
            OutputQuality.SMALL: 5,
        }
        return vbr_map.get(self, 2)
    
    def get_max_bitrate(self) -> int:
        """
        获取最大比特率限制 (bps)
        
        用于 AAC 等非 MP3 格式
        
        Returns:
            int: 最大比特率 (bps)
        """
        bitrate_map = {
            OutputQuality.HIGH: 256000,
            OutputQuality.STANDARD: 192000,
            OutputQuality.SMALL: 128000,
        }
        return bitrate_map.get(self, 192000)


@dataclass
class NormalizeConfig:
    """音量标准化配置（基于 EBU R128 loudnorm 滤镜）"""

    target_loudness: float = -16.0
    true_peak: float = -1.5
    lra: float = 11.0

    def to_ffmpeg_filter(self) -> str:
        """转换为 FFmpeg loudnorm 滤镜参数字符串"""
        return (
            f"loudnorm=I={self.target_loudness}:"
            f"TP={self.true_peak}:"
            f"LRA={self.lra}"
        )

    def to_dict(self) -> dict:
        """序列化为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "NormalizeConfig":
        """从字典反序列化"""
        return cls(**data)


@dataclass
class TrimConfig:
    """音频裁剪配置"""

    mode: TrimMode = TrimMode.MANUAL
    start_time: float = 0.0
    end_time: float | None = None
    duration: float | None = None
    silence_threshold: float = -50.0
    min_silence_duration: float = 1.0
    fade_in: float = 0.0
    fade_out: float = 0.0

    def validate(self) -> tuple[bool, str]:
        """
        验证配置有效性

        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        if self.mode == TrimMode.MANUAL:
            if self.start_time < 0:
                return False, "开始时间不能为负数"
            if self.end_time is not None and self.end_time <= self.start_time:
                return False, "结束时间必须大于开始时间"
        elif self.mode == TrimMode.DURATION:
            if self.duration is None or self.duration <= 0:
                return False, "时长必须大于0"
            if self.start_time < 0:
                return False, "开始时间不能为负数"
        return True, ""

    def to_dict(self) -> dict:
        """序列化为字典，处理枚举类型"""
        data = asdict(self)
        data["mode"] = self.mode.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "TrimConfig":
        """从字典反序列化，恢复枚举类型"""
        if isinstance(data.get("mode"), str):
            data["mode"] = TrimMode(data["mode"])
        return cls(**data)


@dataclass
class EditorConfig:
    """编辑器主配置（组合所有编辑参数）"""

    trim: TrimConfig = field(default_factory=TrimConfig)
    normalize: NormalizeConfig = field(default_factory=NormalizeConfig)
    output_format: OutputFormat = OutputFormat.MP3
    quality_preset: QualityPreset = QualityPreset.HIGH
    output_quality: OutputQuality = OutputQuality.STANDARD
    overwrite_original: bool = False

    def validate(self) -> tuple[bool, str]:
        """验证整个配置的有效性"""
        valid, error = self.trim.validate()
        if not valid:
            return False, f"裁剪配置错误: {error}"

        if self.normalize.target_loudness < -70 or self.normalize.target_loudness > -5:
            return False, "目标响度范围应在 -70 到 -5 LUFS 之间"

        return True, ""

    def to_dict(self) -> dict:
        """序列化为字典（用于保存预设或配置文件）"""
        return {
            "trim": self.trim.to_dict(),
            "normalize": self.normalize.to_dict(),
            "output_format": self.output_format.value,
            "quality_preset": self.quality_preset.value,
            "output_quality": self.output_quality.value,
            "overwrite_original": self.overwrite_original,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EditorConfig":
        """从字典反序列化"""
        trim_data = data.get("trim", {})
        normalize_data = data.get("normalize", {})

        return cls(
            trim=TrimConfig.from_dict(trim_data),
            normalize=NormalizeConfig.from_dict(normalize_data),
            output_format=OutputFormat(data.get("output_format", "mp3")),
            quality_preset=QualityPreset(data.get("quality_preset", "high")),
            output_quality=OutputQuality(data.get("output_quality", "standard")),
            overwrite_original=data.get("overwrite_original", False),
        )

    def to_json(self) -> str:
        """序列化为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "EditorConfig":
        """从 JSON 字符串反序列化"""
        data = json.loads(json_str)
        return cls.from_dict(data)
