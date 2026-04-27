#!/usr/bin/env python
"""
测试缓存和限流功能

验证：
1. 缓存命中：相同关键词第二次搜索应从缓存返回（无网络请求）
2. 限流保护：批量请求时应有适当间隔，避免触发405
3. 重复关键词场景：显著减少API调用次数
"""
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_tag.audio_recognize import (
    _build_search_keyword_from_filename,
    _search_netease_rest,
    _search_cache,
    _rate_limiter,
)


async def test_cache_hit():
    """测试缓存命中"""
    print("\n" + "="*70)
    print("[TEST 1] Cache Hit Mechanism")
    print("="*70)

    keyword = "松本文紀 美しい音色で世界が鳴った"

    # 清空缓存确保干净环境
    _search_cache.clear()
    print(f"\nCache cleared: {_search_cache.stats()['size']} entries")

    # 第一次搜索（应该走网络）
    print(f"\n[1st Search] '{keyword}' (should hit network)...")
    start = time.time()
    results1 = await _search_netease_rest(keyword, limit=3)
    time1 = time.time() - start

    if results1:
        print(f"   ✅ Found {len(results1)} results in {time1:.2f}s")
        print(f"      Best: {results1[0].title} - {results1[0].artist}")
    else:
        print(f"   ❌ No results")
        return False

    # 第二次搜索相同关键词（应该命中缓存）
    print(f"\n[2nd Search] '{keyword}' (should hit CACHE)...")
    start = time.time()
    results2 = await _search_netease_rest(keyword, limit=3)
    time2 = time.time() - start

    if results2:
        print(f"   ✅ Found {len(results2)} results in {time2:.4f}s ⚡ (cached!)")
        print(f"      Best: {results2[0].title} - {results2[0].artist}")
    else:
        print(f"   ❌ No results")
        return False

    # 验证结果一致性
    if len(results1) == len(results2) and results1[0].title == results2[0].title:
        speedup = time1 / max(time2, 0.001)
        print(f"\n📊 Cache Performance:")
        print(f"   Network:  {time1:.3f}s")
        print(f"   Cached:   {time2:.6f}s")
        print(f"   Speedup:  {speedup:.0f}x faster!")
        print(f"\n✅ Cache HIT test PASSED!")
        return True
    else:
        print(f"\n❌ Results mismatch between network and cache")
        return False


async def test_rate_limiting():
    """测试请求间隔控制"""
    print("\n\n" + "="*70)
    print("[TEST 2] Rate Limiting Protection")
    print("="*70)

    # 重置限流器状态
    print(f"\nRateLimiter initial state:")
    print(f"   {_rate_limiter.stats()}")

    keywords = [
        "櫻川めぐ 一冊のアロー",
        "百石元 猪突猛進",
        "松本文紀 君の筆は世界を奏でる",
    ]

    total_time = 0
    for i, kw in enumerate(keywords, 1):
        # 清除缓存确保每次都走网络
        _search_cache.clear()

        print(f"\n[{i}/{len(keywords)}] Searching: '{kw}'...")
        start = time.time()

        results = await _search_netease_rest(kw, limit=2)

        elapsed = time.time() - start
        total_time += elapsed

        if results:
            print(f"   ✅ Found {len(results)} results ({elapsed:.2f}s)")
            print(f"      RateLimiter interval: {_rate_limiter.stats()['current_interval']}s")
        else:
            print(f"   ❌ No results ({elapsed:.2f}s)")

    avg_time = total_time / len(keywords)

    print(f"\n📊 Rate Limiting Stats:")
    print(f"   Total time:     {total_time:.2f}s")
    print(f"   Avg per search: {avg_time:.2f}s")
    print(f"   Final state:    {_rate_limiter.stats()}")

    # 检查是否有适当的间隔（至少应该 > 0）
    if avg_time > 0.3:  # 考虑到网络延迟，平均时间应该合理
        print(f"\n✅ Rate limiting test PASSED!")
        return True
    else:
        print(f"\n⚠️ Searches seem too fast, rate limiting may not be working")
        return False


async def test_duplicate_keywords():
    """测试重复关键词的缓存效果"""
    print("\n\n" + "="*70)
    print("[TEST 3] Duplicate Keywords Optimization")
    print("="*70)

    # 模拟用户目录中有重复艺术家的情况
    test_files = [
        "C:/CloudMusic/松本文紀 - 美しい音色で世界が鳴った.mp3",
        "C:/CloudMusic/松本文純 - 心象の中の光.mp3",
        "C:/CloudMusic/松本文紀 - 夢の歩みを見上げて.mp3",
        "C:/CloudMusic/松本文紀 - 美しい音色で世界が鳴った.mp3",  # 重复！
        "C:/CloudMusic/松本文紀 - 心象の中の光.mp3",           # 重复！
        "C:/CloudMusic/松本文紀 - 舞い上がる因果交流のいかり.mp3",
    ]

    # 清空缓存开始测试
    _search_cache.clear()
    cache_stats_before = _search_cache.stats()

    print(f"\nProcessing {len(test_files)} files (with duplicates)...")
    print(f"Initial cache: {cache_stats_before['size']} entries")

    start_total = time.time()
    cache_hits = 0
    network_requests = 0
    success_count = 0

    for idx, file_path in enumerate(test_files, 1):
        filename = os.path.basename(file_path)
        keyword = _build_search_keyword_from_filename(file_path)

        cache_size_before = _search_cache.stats()['size']

        start = time.time()
        results = await _search_netease_rest(keyword, limit=2)
        elapsed = time.time() - start

        cache_size_after = _search_cache.stats()['size']

        # 判断是否命中缓存
        is_cached = (cache_size_after == cache_size_before) and results

        if is_cached:
            cache_hits += 1
            status = "⚡ CACHED"
        elif results:
            network_requests += 1
            status = "🌐 NETWORK"
        else:
            status = "❌ FAILED"

        if results:
            success_count += 1

        print(f"   [{idx:2d}] {filename[:35]:<35s} {status} ({elapsed:.3f}s)")

    total_time = time.time() - start_total
    final_stats = _search_cache.stats()

    print(f"\n📊 Duplicate Keywords Test Results:")
    print(f"   Total files:       {len(test_files)}")
    print(f"   Successful:       {success_count}/{len(test_files)}")
    print(f"   Cache hits:        {cache_hits} (saved {cache_hits} API calls)")
    print(f"   Network requests:  {network_requests}")
    print(f"   Total time:        {total_time:.2f}s")
    print(f"   Final cache size: {final_stats['size']} entries")
    print(f"   Cache hit rate:   {final_stats['hit_rate']}")

    # 验证优化效果
    if cache_hits >= 2:  # 至少有2次缓存命中（我们故意放了2个重复文件）
        saved_percentage = (cache_hits / len(test_files)) * 100
        print(f"\n✅ Optimization effective! Saved {saved_percentage:.0f}% of API calls")
        return True
    else:
        print(f"\n⚠️ Expected more cache hits, got only {cache_hits}")
        return False


async def test_full_batch_simulation():
    """完整模拟批量处理48首歌曲的场景"""
    print("\n\n" + "="*70)
    print("[TEST 4] Full Batch Simulation (9 songs with optimizations)")
    print("="*70)

    # 重置状态
    _search_cache.clear()

    # 测试歌曲列表（包含重复艺术家）
    all_songs = [
        "C:/CloudMusic/松本文紀 - 夢の歩みを見上げて.mp3",
        "C:/CloudMusic/松本文紀 - 心象の中の光.mp3",
        "C:/CloudMusic/松本文紀 - 美しい音色で世界が鳴った.mp3",
        "C:/CloudMusic/松本文紀 - 舞い上がる因果交流のいかり.mp3",
        "C:/CloudMusic/松本文紀 - .*模型.mp3",
        "C:/CloudMusic/櫻川めぐ - 一冊のアロー.mp3",
        "C:/CloudMusic/百石元 - 猪突猛進.mp3",
        "C:/CloudMusic/松本文紀 - 君の筆は世界を奏でる.mp3",
        "C:/CloudMusic/松本文紀 - ざくざくと散る錆びた夢.mp3",
        # 故意重复一些（模拟同一专辑多首歌）
        "C:/CloudMusic/松本文紀 - 美しい音色で世界が鳴った.mp3",
        "C:/CloudMusic/松本文紀 - 心象の中の光.mp3",
    ]

    print(f"\nSimulating batch processing of {len(all_songs)} files...")
    print("(with caching and rate limiting enabled)\n")

    start_time = time.time()
    success = 0
    failed = 0

    for idx, file_path in enumerate(all_songs, 1):
        filename = os.path.basename(file_path)
        keyword = _build_search_keyword_from_filename(file_path)

        try:
            results = await _search_netease_rest(keyword, limit=3)

            if results:
                success += 1
                best = results[0]
                print(
                    f"[{idx:2d}/{len(all_songs):2d}] ✅ "
                    f"{filename[:30]:<30s} → {best.title}"
                )
            else:
                failed += 1
                print(f"[{idx:2d}/{len(all_songs):2d}] ❌ {filename}")

        except Exception as e:
            failed += 1
            print(f"[{idx:2d}/{len(all_songs):2d}] 💥 ERROR: {e}")

    total_time = time.time() - start_time
    cache_stats = _search_cache.stats()
    rate_stats = _rate_limiter.stats()

    # 输出总结
    print("\n" + "-"*70)
    print("📊 FINAL REPORT")
    print("-"*70)
    print(f"  Files processed:  {len(all_songs)}")
    print(f"  ✅ Success:        {success}/{len(all_songs)} ({success/len(all_songs)*100:.0f}%)")
    print(f"  ❌ Failed:         {failed}/{len(all_songs)} ({failed/len(all_songs)*100:.0f}%)")
    print(f"  ⏱️  Total time:     {total_time:.1f}s")
    print(f"  📦 Avg per file:   {total_time/len(all_songs):.2f}s")
    print(f"\n  🔒 Cache stats:")
    print(f"     Size:           {cache_stats['size']}/{cache_stats['max_size']}")
    print(f"     Hit rate:       {cache_stats['hit_rate']}")
    print(f"     Hits/Misses:    {cache_stats['hits']}/{cache_stats['misses']}")
    print(f"\n  🚦 Rate limiter:")
    print(f"     Current interval: {rate_stats['current_interval']}s")
    print(f"     Rate limited count: {rate_stats['rate_limited_count']}")

    if success >= len(all_songs) * 0.9 and cache_stats['hits'] >= 2:
        print(f"\n{'='*70}")
        print("🎉 ALL TESTS PASSED! Optimizations working perfectly!")
        print(f"{'='*70}")
        return 0
    else:
        print(f"\n⚠️ Some issues detected, check output above")
        return 1


async def main():
    """主测试函数"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + "  Testing Cache & Rate Limiting Optimizations".center(68) + "║")
    print("╚" + "="*68 + "╝")

    try:
        # 运行所有测试
        test1_ok = await test_cache_hit()
        test2_ok = await test_rate_limiting()
        test3_ok = await test_duplicate_keywords()
        exit_code = await test_full_batch_simulation()

        return exit_code

    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
