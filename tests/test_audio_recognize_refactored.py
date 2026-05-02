# -*- coding: utf-8 -*-
"""
audio_recognize.py 中期重构验证测试

目的:
- 验证 _flatten_shazam_metadata() 数据标准化函数正确性
- 验证 _safe_filename() 文件名生成函数（含可选 unidecode 转换）
- 确保重构后的行为与旧版一致（或明确记录差异）
- 为未来维护提供安全网

运行方式:
    uv run pytest tests/test_audio_recognize_refactored.py -v
"""

import sys
import pytest

# Mock shazamio 模块以避免导入依赖
if 'shazamio' not in sys.modules:
    sys.modules['shazamio'] = type(sys)('shazamio')
    sys.modules['shazamio'].Shazam = type('Shazam', (), {})

from auto_tag.audio_recognize import (
    _flatten_shazam_metadata,
    _safe_filename,
)


class TestFlattenShazamMetadata:
    """_flatten_shazam_metadata() 数据标准化函数测试"""

    def test_standard_shazam_format(self):
        """
        测试标准 Shazam API 返回格式

        输入: 典型的 Shazam track 结构，包含 sections > metadata > {title, text}
        预期: 扁平化为小写键名的字典
        """
        track = {
            "title": "Test Song",
            "subtitle": "Test Artist",
            "sections": [{
                "metadata": [
                    {"title": "Album", "text": "Test Album"},
                    {"title": "Genre", "text": "Pop"},
                    {"title": "Year", "text": "2024"}
                ]
            }]
        }

        result = _flatten_shazam_metadata(track)

        assert result["album"] == "Test Album"
        assert result["genre"] == "Pop"
        assert result["year"] == "2024"
        assert len(result) == 3

    def test_empty_sections(self):
        """
        测试空 sections 字段

        边界情况: Shazam 返回的 sections 为空列表或不存在
        预期: 返回空字典
        """
        track = {"title": "Song", "sections": []}

        result = _flatten_shazam_metadata(track)

        assert result == {}

    def test_missing_sections_key(self):
        """
        测试缺少 sections 键

        边界情况: track 字典中没有 sections 键
        预期: 返回空字典（不抛出异常）
        """
        track = {"title": "Song"}

        result = _flatten_shazam_metadata(track)

        assert result == {}

    def test_empty_metadata_in_section(self):
        """
        测试 section 中 metadata 为空

        边缘情况: sections 存在但 metadata 为空列表
        预期: 返回空字典
        """
        track = {
            "sections": [
                {"type": "SONG", "metadata": []},
                {"type": "ARTIST", "metadata": []}
            ]
        }

        result = _flatten_shazam_metadata(track)

        assert result == {}

    def test_multiple_sections_with_duplicates(self):
        """
        测试多个 section 包含相同键名

        场景: 不同 section 都有 "Album" 信息
        预期: 保留第一个出现的值（不覆盖）
        """
        track = {
            "sections": [
                {
                    "metadata": [
                        {"title": "Album", "text": "First Album"}
                    ]
                },
                {
                    "metadata": [
                        {"title": "Album", "text": "Second Album"}
                    ]
                }
            ]
        }

        result = _flatten_shazam_metadata(track)

        # 应保留第一个值
        assert result["album"] == "First Album"
        assert len(result) == 1

    def test_case_insensitive_keys(self):
        """
        测试键名统一转换为小写

        输入: metadata 中 title 为混合大小写 (如 "Album", "GENRE")
        预期: 所有键名转为小写 ("album", "genre")
        """
        track = {
            "sections": [{
                "metadata": [
                    {"title": "Album", "text": "Value1"},
                    {"title": "GENRE", "text": "Value2"},
                    {"title": "Year", "text": "Value3"}
                ]
            }]
        }

        result = _flatten_shazam_metadata(track)

        assert "album" in result
        assert "genre" in result
        assert "year" in result
        # 确认没有大写键
        assert all(k.islower() for k in result.keys())

    def test_whitespace_trimming(self):
        """
        测试键名和值的空白字符清理

        输入: title 或 text 包含前后空格
        预期: 自动 strip() 清理
        """
        track = {
            "sections": [{
                "metadata": [
                    {"title": "  Album  ", "text": "  Test Value  "},
                    {"title": "Genre", "text": ""}
                ]
            }]
        }

        result = _flatten_shazam_metadata(track)

        assert result["album"] == "Test Value"  # 值被 trim
        assert "genre" not in result  # 空值被跳过


class TestSafeFilename:
    """_safe_filename() 文件名生成函数测试"""

    def test_basic_sanitization(self):
        """
        测试基本字符串清理功能

        使用新版 sanitize() 的默认行为：
        - 移除控制字符
        - 标准化空白字符
        - None/空字符串返回 "Unknown"
        """
        # 正常文本
        assert _safe_filename("Hello World") == "Hello World"

        # 控制字符应被移除
        assert "\x00" not in _safe_filename("Hello\x00World")

        # None 返回 "Unknown"
        assert _safe_filename(None) == "Unknown"

        # 空字符串返回 "Unknown"
        assert _safe_filename("") == "Unknown"

    def test_unicode_preservation_by_default(self):
        """
        测试默认行为：保留 Unicode 字符（不使用 unidecode）

        这是重构的关键改进点：
        - 旧版 (_legacy_sanitize): 默认使用 unidecode 转换
        - 新版 (_safe_filename): 默认保留原始字符
        """
        japanese_text = "日本語テスト"
        chinese_text = "中文测试"

        # 默认 ascii_only=False，应保留原样
        assert _safe_filename(japanese_text) == japanese_text
        assert _safe_filename(chinese_text) == chinese_text

    def test_ascii_only_conversion(self):
        """
        测试 ASCII-only 模式（使用 unidecode）

        当 ascii_only=True 时：
        - 应调用 unidecode 将非 ASCII 字符转换
        - 日文 → 罗马音近似音译
        - 特殊字符 → 最接近的 ASCII 等价形式
        """
        japanese_text = "日本語"

        result = _safe_filename(japanese_text, ascii_only=True)

        # 应转换为 ASCII（具体结果取决于 unidecode 库）
        assert result.isascii(), f"ascii_only=True 应产生纯ASCII: {result}"
        assert result != japanese_text, "应发生转换"

    def test_mixed_content_handling(self):
        """
        测试混合内容处理（Unicode + 特殊字符 + 数字）

        复杂场景测试，确保各种输入都能正确处理。
        """
        test_cases = [
            ("Artist - Song [feat. Guest]", False),
            ("RADWIMPS feat. Toko Miura", True),
            ("01. Intro Track", False),
            ("Café Restaurant", True),
        ]

        for text, use_ascii in test_cases:
            result = _safe_filename(text, use_ascii)
            
            # 不应为空（除非输入为空）
            assert result, f"输入 '{text}' 不应产生空输出"
            
            if use_ascii:
                assert result.isascii(), f"ascii_only 模式应为纯ASCII: {result}"


class TestRefactoringIntegration:
    """集成测试：验证重构后的完整流程"""

    def test_no_legacy_imports_in_audio_recognize(self):
        """
        验证 audio_recognize.py 不再直接导入旧版 API

        这是 CI lint 规则的补充检查，
        确保重构彻底移除了对 _legacy_utils 的依赖。
        """
        import ast
        import inspect

        source = inspect.getsource(__import__('auto_tag.audio_recognize', fromlist=['']))

        # 检查是否包含旧版导入模式
        legacy_patterns = [
            '_legacy_find_deepest_metadata_key',
            '_legacy_sanitize',
            'from auto_tag._legacy_utils',
        ]

        for pattern in legacy_patterns:
            assert pattern not in source, \
                f"audio_recognize.py 不应包含 '{pattern}'（重构未完成）"

    def test_new_helper_functions_exist(self):
        """
        验证新增的辅助函数存在且可调用
        """
        from auto_tag.audio_recognize import (
            _flatten_shazam_metadata,
            _safe_filename,
        )

        # 函数应该可调用
        assert callable(_flatten_shazam_metadata)
        assert callable(_safe_filename)

        # 应该有 docstring
        assert _flatten_shazam_metadata.__doc__
        assert _safe_filename.__doc__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
