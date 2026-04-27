#!/usr/bin/env python
"""
测试回退搜索机制

验证 Shazam 失败时，是否能从文件名提取关键词并成功搜索网易云。
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_tag.audio_recognize import (
    _build_search_keyword_from_filename,
    _search_netease_rest,
)


async def test_keyword_extraction():
    """测试关键词提取功能"""
    print("\n" + "="*60)
    print("[TEST] Keyword Extraction from Filename")
    print("="*60)

    test_cases = [
        ("C:/CloudMusic/松本文紀 - 心象の中の光.mp3", "松本文紀 心象の中の光"),
        ("C:/CloudMusic/松本文紀 - 美しい音色で世界が鳴った.mp3", "松本文紀 美しい音色で世界が鳴った"),
        ("C:/CloudMusic/松本文紀 - 舞い上がる因果交流のいかり.mp3", "松本文紀 舞い上がる因果交流のいかり"),
        ("C:/CloudMusic/櫻川めぐ - 一冊のアロー.mp3", "櫻川めぐ 一冊のアロー"),
        ("C:/CloudMusic/百石元 - 猪突猛進.mp3", "百石元 猪突猛進"),
    ]

    all_passed = True
    for file_path, expected_contains in test_cases:
        keyword = _build_search_keyword_from_filename(file_path)
        filename = os.path.basename(file_path)

        if expected_contains in keyword or keyword in expected_contains:
            print(f"  ✅ {filename}")
            print(f"     Keyword: {keyword}")
        else:
            print(f"  ❌ {filename}")
            print(f"     Expected: {expected_contains}")
            print(f"     Got: {keyword}")
            all_passed = False

    return all_passed


async def test_fallback_search():
    """测试回退搜索（模拟 Shazam 失败场景）"""
    print("\n" + "="*60)
    print("[TEST] Fallback Search (Shazam Failed Scenario)")
    print("="*60)

    test_files = [
        "C:/CloudMusic/松本文紀 - 美しい音色で世界が鳴った.mp3",
        "C:/CloudMusic/松本文紀 - 心象の中の光.mp3",
        "C:/CloudMusic/櫻川めぐ - 一冊のアロー.mp3",
    ]

    all_passed = True
    for file_path in test_files:
        filename = os.path.basename(file_path)
        keyword = _build_search_keyword_from_filename(file_path)

        print(f"\n📁 File: {filename}")
        print(f"   Keyword: {keyword}")

        if not keyword:
            print(f"   ❌ Failed to extract keyword")
            all_passed = False
            continue

        try:
            results = await _search_netease_rest(keyword, limit=3)

            if results:
                print(f"   ✅ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"      {i}. {result.title} - {result.artist}")
                    print(f"         Album: {result.album}")
            else:
                print(f"   ⚠️ No results found")
                all_passed = False
        except Exception as e:
            print(f"   ❌ Search error: {e}")
            all_passed = False

    return all_passed


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("[TEST SUITE] Fallback Search Mechanism")
    print("="*60)
    print("Testing the fix for: '未找到匹配的搜索结果' issue")

    # 测试1：关键词提取
    keyword_ok = await test_keyword_extraction()

    # 测试2：回退搜索
    search_ok = await test_fallback_search()

    # 总结
    print("\n" + "="*60)
    print("[SUMMARY] Test Results")
    print("="*60)
    print(f"  Keyword Extraction: {'✅ PASS' if keyword_ok else '❌ FAIL'}")
    print(f"  Fallback Search:     {'✅ PASS' if search_ok else '❌ FAIL'}")

    if keyword_ok and search_ok:
        print("\n[SUCCESS] 🎉 Fallback mechanism works perfectly!")
        print("  - Can extract keywords from Japanese filenames")
        print("  - NetEase REST API returns results for ACG music")
        print("  - UI should now show search results instead of '未找到匹配'")
        return 0
    else:
        print("\n[FAIL] Some tests failed, check output above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
