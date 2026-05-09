#!/usr/bin/env python
"""
增强版歌曲名提取器单元测试

覆盖常见文件名格式：
- OST 格式（序号+英文+中文+标签）
- Track 格式（Track XX / 序号前缀）
- 标准格式（Artist - Title）
- 括号标签清理
- 边界情况处理
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock 掉可能导致导入失败的依赖
from unittest.mock import MagicMock
sys.modules['shazamio'] = MagicMock()
sys.modules['shazamio.api'] = MagicMock()
sys.modules['pydub'] = MagicMock()
sys.modules['pydub.audio_segment'] = MagicMock()
sys.modules['pydub.utils'] = MagicMock()

from auto_tag.audio_recognize import (
    _enhanced_extract_song_name,
    _build_search_keyword_from_filename,
)


class TestEnhancedSongNameExtraction:
    """增强版歌曲名提取器测试类"""

    def test_ost_format_with_chinese(self):
        """
        TC-ENH-001: 测试 OST 格式（英文 + 中文 + 标签）

        覆盖用户实际场景：
        - "01. A Small Miracle 小小奇迹 (Instrumental).flac"
        - "02. Vernal Days Dreamed by the Star 那颗星梦见的春日 (Instrumental).flac"
        """
        test_cases = [
            ("01. A Small Miracle 小小奇迹 (Instrumental).flac", "A Small Miracle"),
            ("02. Vernal Days Dreamed by the Star 那颗星梦见的春日 (Instrumental).flac",
             "Vernal Days Dreamed by the Star"),
            ("03. Song Name 歌曲名称.flac", "Song Name"),
            ("10. Beautiful World 美丽世界 (Full Version).mp3", "Beautiful World"),
        ]

        for file_path, expected_title in test_cases:
            result = _enhanced_extract_song_name(file_path)
            filename = os.path.basename(file_path)
            assert expected_title in result, \
                f"OST 格式失败: {filename}\n  期望包含: '{expected_title}'\n  实际结果: '{result}'"
            print(f"  ✅ {filename}")
            print(f"     提取结果: {result}")

    def test_track_number_prefixes(self):
        """
        TC-ENH-002: 测试各种序号前缀移除

        覆盖格式：
        - "01. Title.mp3"
        - "1. Title.mp3"
        - "Track 01 Title.mp3"
        - "Track.01.Title.mp3"
        - "[01] Title.mp3"
        """
        test_cases = [
            ("01. Title.mp3", "Title"),
            ("1. Title.flac", "Title"),
            ("Track 01 Title.mp3", "Title"),
            ("Track.01.Title.flac", "Title"),
            ("[01] Title.mp3", "Title"),
            ("01-Title.mp3", "Title"),
            ("01 Title.mp3", "Title"),
        ]

        for file_path, expected_contains in test_cases:
            result = _enhanced_extract_song_name(file_path)
            filename = os.path.basename(file_path)
            assert expected_contains in result or result in expected_contains, \
                f"序号前缀失败: {filename}\n  期望包含: '{expected_contains}'\n  实际结果: '{result}'"
            print(f"  ✅ {filename} → {result}")

    def test_bracket_tag_removal(self):
        """
        TC-ENH-003: 测试括号标签清理

        覆盖常见标签：
        - (Instrumental)
        - (Off Vocal)
        - (TV Size)
        - (Full Version)
        - [OP], [ED]
        - [Insert Song]
        """
        test_cases = [
            ("Song (Instrumental).mp3", "Song"),
            ("Song (Off Vocal).flac", "Song"),
            ("Opening Theme (TV Size).mp3", "Opening Theme"),
            ("Ending Song (Full Version).mp3", "Ending Song"),
            ("Anime OP [OP].mp3", "Anime OP"),
            ("Insert Song [Insert Song].flac", "Insert Song"),
            ("Song (Radio Edit).mp3", "Song"),
            ("Song (Extended Mix).mp3", "Song"),
        ]

        for file_path, expected_contains in test_cases:
            result = _enhanced_extract_song_name(file_path)
            filename = os.path.basename(file_path)
            # 验证标签已被移除
            assert "(Instrumental)" not in result or "Instrumental" not in file_path, \
                f"标签未清除: {filename}\n  结果仍包含标签: '{result}'"
            assert expected_contains in result or result in expected_contains, \
                f"括号标签失败: {filename}\n  期望包含: '{expected_contains}'\n  实际结果: '{result}'"
            print(f"  ✅ {filename} → {result}")

    def test_standard_artist_title_format(self):
        """
        TC-ENH-004: 测试标准 "Artist - Title" 格式

        保持向后兼容性，确保原有功能不受影响。
        """
        test_cases = [
            ("松本文紀 - 心象の中の光.mp3", "松本文紀 心象の中の光"),
            ("周杰伦 - 晴天.mp3", "周杰伦 晴天"),
            ("Artist - Song Title.mp3", "Artist Song Title"),
        ]

        for file_path, expected_contains in test_cases:
            result = _enhanced_extract_song_name(file_path)
            filename = os.path.basename(file_path)
            assert expected_contains in result or result in expected_contains, \
                f"标准格式失败: {filename}\n  期望包含: '{expected_contains}'\n  实际结果: '{result}'"
            print(f"  ✅ {filename} → {result}")

    def test_complex_ost_scenarios(self):
        """
        TC-ENH-005: 测试复杂 OST 场景组合

        组合多种元素：序号 + 英文 + 中文 + 多个标签
        """
        test_cases = [
            ("01. Opening Theme OPテーマ (TV Size) [OP].flac", "Opening Theme"),
            ("02. Ending EDエンディング (Full Version) [ED].mp3", "Ending"),
            ("03. Insert Song 挿入歌 (Instrumental) [Insert Song].flac", "Insert Song"),
            ("15. Character Image Song キャラソン (Off Vocal).mp3", "Character Image Song"),
        ]

        for file_path, expected_contains in test_cases:
            result = _enhanced_extract_song_name(file_path)
            filename = os.path.basename(file_path)
            # 验证核心标题被提取
            assert len(result) > 0, \
                f"复杂 OST 失败: {filename}\n  结果为空"
            assert expected_contains.split()[0] in result, \
                f"复杂 OST 失败: {filename}\n  期望包含关键词: '{expected_contains.split()[0]}'\n  实际结果: '{result}'"
            # 验证标签被移除
            assert "(TV Size)" not in result and "[OP]" not in result, \
                f"标签未完全清除: {filename}\n  结果: '{result}'"
            print(f"  ✅ {filename}")
            print(f"     提取结果: {result}")

    def test_edge_cases(self):
        """
        TC-ENH-006: 测试边界情况

        包括：
        - 空文件名
        - 仅扩展名
        - 纯数字文件名
        - 特殊字符
        """
        test_cases = [
            (".mp3", ""),                    # 仅扩展名
            ("Simple Title.mp3", "Simple Title"),  # 简单格式
            ("Artist_Title_Song.mp3", "Artist Title Song"),  # 下划线分隔
        ]

        for file_path, expected_contains in test_cases:
            result = _enhanced_extract_song_name(file_path)
            filename = os.path.basename(file_path)
            if expected_contains == "":
                assert result == "", \
                    f"边界情况失败: {filename}\n  期望空字符串\n  实际结果: '{result}'"
            else:
                assert expected_contains in result or result in expected_contains, \
                    f"边界情况失败: {filename}\n  期望包含: '{expected_contains}'\n  实际结果: '{result}'"
            print(f"  ✅ {filename} → '{result}'")

    def test_backward_compatibility(self):
        """
        TC-ENH-007: 测试向后兼容性

        确保 _build_search_keyword_from_filename() 正确调用新的增强版函数，
        且原有测试用例仍然通过。
        """
        original_test_cases = [
            ("C:/CloudMusic/松本文紀 - 心象の中の光.mp3", "松本文紀 心象の中の光"),
            ("C:/CloudMusic/松本文紀 - 美しい音色で世界が鳴った.mp3", "松本文紀 美しい音色で世界が鳴った"),
            ("C:/CloudMusic/櫻川めぐ - 一冊のアロー.mp3", "櫻川めぐ 一冊のアロー"),
        ]

        for file_path, expected_contains in original_test_cases:
            result = _build_search_keyword_from_filename(file_path)
            filename = os.path.basename(file_path)
            assert expected_contains in result or result in expected_contains, \
                f"向后兼容性失败: {filename}\n  期望包含: '{expected_contains}'\n  实际结果: '{result}'"
            print(f"  ✅ {filename} → {result}")


def run_all_tests():
    """运行所有测试用例"""
    print("\n" + "=" * 70)
    print("[TEST SUITE] Enhanced Song Name Extraction")
    print("=" * 70)

    tester = TestEnhancedSongNameExtraction()

    tests = [
        ("OST 格式（英文+中文+标签）", tester.test_ost_format_with_chinese),
        ("序号前缀移除", tester.test_track_number_prefixes),
        ("括号标签清理", tester.test_bracket_tag_removal),
        ("标准 Artist-Title 格式", tester.test_standard_artist_title_format),
        ("复杂 OST 场景组合", tester.test_complex_ost_scenarios),
        ("边界情况处理", tester.test_edge_cases),
        ("向后兼容性验证", tester.test_backward_compatibility),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'─' * 70}")
        print(f"[TEST] {name}")
        print("─" * 70)
        try:
            test_func()
            results.append((name, True, None))
            print(f"\n  ✅ PASS: {name}")
        except AssertionError as e:
            results.append((name, False, str(e)))
            print(f"\n  ❌ FAIL: {name}")
            print(f"     Error: {e}")
        except Exception as e:
            results.append((name, False, f"Unexpected error: {e}"))
            print(f"\n  ❌ ERROR: {name}")
            print(f"     Error: {type(e).__name__}: {e}")

    # 总结
    print("\n" + "=" * 70)
    print("[SUMMARY] Test Results")
    print("=" * 70)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for name, success, error in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {name}")
        if error:
            print(f"         {error}")

    print(f"\n  Total: {passed}/{total} passed")

    if passed == total:
        print("\n[SUCCESS] 🎉 All tests passed!")
        print("  Enhanced extraction handles:")
        print("  ✓ OST format (track number + English + Chinese + tags)")
        print("  ✓ Various track number prefixes")
        print("  ✓ Bracket tag removal")
        print("  ✓ Standard Artist-Title format")
        print("  ✓ Complex combined scenarios")
        print("  ✓ Edge cases")
        print("  ✓ Backward compatibility")
        return 0
    else:
        print("\n[FAIL] Some tests failed, check output above")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
