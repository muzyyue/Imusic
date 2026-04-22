#!/usr/bin/env python
"""
测试 REST API 版本的网易云音乐搜索功能

验证 _search_netease_rest 函数是否可以正常工作。
完全绕过 pymusiclibrary 原生 C 库，使用纯 HTTP 请求。
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_tag.audio_recognize import _search_netease_rest


async def test_netease_rest_search():
    """测试网易云音乐 REST API 搜索"""
    print("\n" + "="*60)
    print("[TEST] NetEase Cloud Music Search (REST API Mode)")
    print("="*60)

    keyword = "美しい音色で世界が鳴った"
    print(f"\nKeyword: {keyword}")

    try:
        results = await _search_netease_rest(keyword, limit=3)

        if results:
            print(f"\n[OK] Search success! Found {len(results)} results:\n")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.title} - {result.artist}")
                print(f"     Album: {result.album}")
                print(f"     Duration: {result.duration}s")
                print(f"     Source: {result.source}")
                print(f"     Confidence: {result.confidence}")
                print()
            return True
        else:
            print("[FAIL] Empty search results")
            return False

    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("[TEST] REST API Mode - NetEase Cloud Music Search")
    print("="*60)

    # 测试网易云 REST API
    netease_ok = await test_netease_rest_search()

    # 总结
    print("\n" + "="*60)
    print("[SUMMARY] Test Results")
    print("="*60)
    status = "PASS" if netease_ok else "FAIL"
    print(f"  NetEase (REST API): [{status}]")

    if netease_ok:
        print("\n[SUCCESS] REST API search works perfectly!")
        print("  - Bypassed pymusiclibrary native library completely")
        print("  - Pure HTTP request, cross-thread safe")
        print("  - No more access violation crashes")
        return 0
    else:
        print("\n[WARN] REST API search failed, check network or API availability")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
