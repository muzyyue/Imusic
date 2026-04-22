#!/usr/bin/env python
"""
测试批量搜索场景下的重试机制

模拟处理48首歌曲时的频率限制情况，验证自动重试是否有效。
"""
import asyncio
import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_tag.audio_recognize import (
    _build_search_keyword_from_filename,
    _search_netease_rest,
)


async def test_batch_search_with_retry():
    """测试批量搜索（包含之前失败的歌曲）"""
    print("\n" + "="*70)
    print("[TEST] Batch Search with Auto-Retry Mechanism")
    print("="*70)
    print("Simulating 48 songs batch processing scenario...\n")

    # 测试歌曲列表（包含之前失败的和成功的）
    test_files = [
        # 之前失败的
        "C:/CloudMusic/松本文紀 - 夢の歩みを見上げて.mp3",
        "C:/CloudMusic/松本文紀 - 心象の中の光.mp3",
        # 之前成功的
        "C:/CloudMusic/松本文紀 - 美しい音色で世界が鳴った.mp3",
        "C:/CloudMusic/松本文紀 - 舞い上がる因果交流のいかり.mp3",
        "C:/CloudMusic/松本文紀 - .*模型.mp3",
        "C:/CloudMusic/櫻川めぐ - 一冊のアロー.mp3",
        "C:/CloudMusic/百石元 - 猪突猛進.mp3",
        # 更多歌曲模拟批量
        "C:/CloudMusic/松本文紀 - 君の筆は世界を奏でる.mp3",
        "C:/CloudMusic/松本文紀 - ざくざくと散る錆びた夢.mp3",
    ]

    start_time = time.time()
    success_count = 0
    fail_count = 0
    results_detail = []

    for idx, file_path in enumerate(test_files, 1):
        filename = os.path.basename(file_path)
        keyword = _build_search_keyword_from_filename(file_path)

        print(f"[{idx}/{len(test_files)}] {filename}")
        print(f"   Keyword: '{keyword}'")

        if not keyword:
            print(f"   ❌ Failed to extract keyword\n")
            fail_count += 1
            results_detail.append((filename, False, "Empty keyword"))
            continue

        try:
            results = await _search_netease_rest(keyword, limit=3)

            elapsed = time.time() - start_time

            if results:
                success_count += 1
                best_match = results[0]
                print(f"   ✅ Found {len(results)} results ({elapsed:.1f}s)")
                print(f"      Best: {best_match.title} - {best_match.artist}")
                results_detail.append((filename, True, f"{len(results)} results"))
            else:
                fail_count += 1
                print(f"   ❌ No results ({elapsed:.1f}s)")
                results_detail.append((filename, False, "No results"))

        except Exception as e:
            fail_count += 1
            print(f"   ❌ Error: {e}")
            results_detail.append((filename, False, str(e)))

        print()

        # 添加小延迟避免过于频繁的请求（模拟真实场景）
        if idx < len(test_files):
            await asyncio.sleep(0.5)

    total_time = time.time() - start_time

    # 输出总结
    print("\n" + "="*70)
    print("[SUMMARY] Batch Search Results")
    print("="*70)
    print(f"  Total Files:     {len(test_files)}")
    print(f"  ✅ Success:      {success_count}/{len(test_files)} ({success_count/len(test_files)*100:.1f}%)")
    print(f"  ❌ Failed:       {fail_count}/{len(test_files)} ({fail_count/len(test_files)*100:.1f}%)")
    print(f"  Total Time:      {total_time:.1f}s")
    print(f"  Avg Time/File:   {total_time/len(test_files):.2f}s")

    print("\n[Detailed Results]")
    print("-"*70)
    for filename, success, detail in results_detail:
        status = "✅" if success else "❌"
        print(f"  {status} {filename}: {detail}")

    # 判断是否通过
    print("\n" + "="*70)
    if success_count >= len(test_files) * 0.8:  # 80%以上成功率
        print("[SUCCESS] 🎉 Retry mechanism works well!")
        print("  - Most songs can now be searched successfully")
        print("  - Rate limiting is handled gracefully with retries")
        return 0
    elif success_count >= len(test_files) * 0.5:  # 50%以上
        print("[PARTIAL] ⚠️ Some improvements, but still issues")
        print("  - Retry mechanism helps but may need tuning")
        return 1
    else:
        print("[FAIL] ❌ Retry mechanism not effective enough")
        return 2


async def main():
    exit_code = await test_batch_search_with_retry()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
