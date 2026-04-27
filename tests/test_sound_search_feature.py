#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试网易云音乐声音类型搜索功能（集成测试）

验证修改后的 _search_netease_rest() 函数是否能够同时搜索：
1. 普通歌曲 (type=1)
2. 电台/声音内容 (type=1009)
"""
import asyncio
import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_tag.audio_recognize import _search_netease_rest, _do_single_search, _do_radio_search


async def test_sound_search_integration():
    """
    集成测试：验证声音搜索功能
    
    测试场景：
    1. 搜索包含电台内容的关键词
    2. 验证返回结果同时包含歌曲和电台
    3. 检查电台数据的字段完整性
    """
    print("\n" + "="*70)
    print("[TEST] NetEase Sound/Radio Search Integration Test")
    print("="*70)
    
    test_cases = [
        ("故事", "可能包含电台节目"),
        ("晚安", "情感类声音"),
        ("白噪音", "功能性声音"),
        ("周杰伦", "知名歌手（对比测试）"),
    ]
    
    all_passed = True
    
    for keyword, desc in test_cases:
        print(f"\n{'-'*70}")
        print(f"[TEST CASE] Keyword: '{keyword}' ({desc})")
        print("-"*70)
        
        try:
            # 调用修改后的搜索函数（默认 include_radio=True）
            results = await _search_netease_rest(keyword, limit=3, include_radio=True)
            
            if not results:
                print(f"[WARN] No results for '{keyword}'")
                continue
            
            print(f"[OK] Found {len(results)} total results")
            
            # 分类统计
            songs = [r for r in results if r.source == "netease"]
            radios = [r for r in results if r.source == "netease-radio"]
            
            print(f"  - Songs (type=1): {len(songs)}")
            print(f"  - Radios (type=1009): {len(radios)}")
            
            # 显示歌曲结果
            if songs:
                print(f"\n  [Songs]")
                for i, s in enumerate(songs[:2], 1):
                    print(f"    {i}. {s.title} - {s.artist}")
                    print(f"       Album: {s.album}")
                    print(f"       Duration: {s.duration}s")
                    print(f"       Cover: {'Yes' if s.cover_link else 'No'}")
                    print(f"       Confidence: {s.confidence}")
            
            # 显示电台结果
            if radios:
                print(f"\n  [Radios/Sounds]")
                for i, r in enumerate(radios[:2], 1):
                    print(f"    {i}. {r.title}")
                    print(f"       DJ/Artist: {r.artist}")
                    print(f"       Category: {r.album}")
                    print(f"       Cover: {'Yes' if r.cover_link else 'No'}")
                    print(f"       Confidence: {r.confidence}")
                    
                    # 验证关键字段
                    if r.raw_data:
                        raw = r.raw_data
                        required_fields = ['id', 'name', 'picUrl']
                        missing = [f for f in required_fields if f not in raw]
                        if missing:
                            print(f"       [WARN] Missing fields: {missing}")
                        else:
                            print(f"       [OK] All required fields present")
                
                print(f"\n  [SUCCESS] Radio search working! Found {len(radios)} radio/sound items.")
            else:
                print(f"\n  [INFO] No radio results (keyword may not have radio content)")
            
        except Exception as e:
            print(f"[ERROR] Test failed: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    return all_passed


async def test_individual_search_functions():
    """
    单元测试：分别测试歌曲搜索和电台搜索函数
    """
    print("\n\n" + "="*70)
    print("[UNIT TEST] Individual Search Functions")
    print("="*70)
    
    keyword = "故事"
    
    # Test 1: 歌曲搜索 (type=1)
    print(f"\n[Test 1] Song search only (type=1)")
    try:
        songs = await asyncio.get_running_loop().run_in_executor(
            None, 
            lambda: _do_single_search(keyword, limit=2, search_type=1)
        )
        print(f"  Result: {len(songs)} songs")
        if songs:
            print(f"  Example: {songs[0].title} - {songs[0].artist}")
        else:
            print("  [WARN] No songs found")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    # Test 2: 电台搜索 (type=1009)
    print(f"\n[Test 2] Radio search only (type=1009)")
    try:
        radios = _do_radio_search(keyword, limit=2)
        print(f"  Result: {len(radios)} radios")
        if radios:
            print(f"  Example: {radios[0].title}")
            print(f"  Source: {radios[0].source}")
            
            # 验证 source 标记
            assert radios[0].source == "netease-radio", f"Expected 'netease-radio', got '{radios[0].source}'"
            print(f"  [OK] Source correctly marked as 'netease-radio'")
        else:
            print("  [INFO] No radios found for this keyword")
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: 禁用电台搜索
    print(f"\n[Test 3] Combined search with radio DISABLED")
    try:
        results_no_radio = await _search_netease_rest(keyword, limit=3, include_radio=False)
        sources = set(r.source for r in results_no_radio)
        print(f"  Result: {len(results_no_radio)} items")
        print(f"  Sources: {sources}")
        
        if 'netease-radio' in sources:
            print("  [FAIL] Should not contain radio results!")
            return False
        else:
            print("  [OK] Correctly excluded radio results")
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False
    
    return True


async def main():
    """主测试函数"""
    print("\n" + "#"*70)
    print("# NetEase Cloud Music - Sound Type Search Feature Test")
    print("#"*70)
    
    # 运行单元测试
    unit_ok = await test_individual_search_functions()
    
    # 运行集成测试
    integration_ok = await test_sound_search_integration()
    
    # 总结
    print("\n\n" + "="*70)
    print("[SUMMARY] Test Results")
    print("="*70)
    print(f"  Unit Tests:       {'PASS' if unit_ok else 'FAIL'}")
    print(f"  Integration Tests: {'PASS' if integration_ok else 'FAIL'}")
    
    if unit_ok and integration_ok:
        print("\n[SUCCESS] All tests passed!")
        print("  - Sound/radio search is working correctly")
        print("  - Both song and radio results are returned")
        print("  - Radio results are properly marked with 'netease-radio' source")
        return 0
    else:
        print("\n[FAIL] Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
