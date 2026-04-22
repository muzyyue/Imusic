#!/usr/bin/env python
"""
调试脚本：诊断特定歌曲搜索失败的原因
"""
import asyncio
import sys
import os
import json
import urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_tag.audio_recognize import (
    _build_search_keyword_from_filename,
    _search_netease_rest,
)


async def debug_specific_files():
    """调试搜索失败的特定文件"""
    print("\n" + "="*70)
    print("[DEBUG] Diagnosing Failed Search Cases")
    print("="*70)

    # 用户报告的失败案例
    failed_files = [
        "C:/CloudMusic/松本文紀 - 夢の歩みを見上げて.mp3",
        "C:/CloudMusic/松本文紀 - 心象の中の光.mp3",
    ]

    # 成功案例（用于对比）
    success_files = [
        "C:/CloudMusic/松本文紀 - 美しい音色で世界が鳴った.mp3",
        "C:/CloudMusic/松本文紀 - 舞い上がる因果交流のいかり.mp3",
    ]

    print("\n【Step 1】Keyword Extraction Test")
    print("-"*70)

    all_files = failed_files + success_files
    for file_path in all_files:
        filename = os.path.basename(file_path)
        keyword = _build_search_keyword_from_filename(file_path)

        status = "❌ FAILED" if file_path in failed_files else "✅ SUCCESS"
        print(f"\n{status} {filename}")
        print(f"   Extracted Keyword: '{keyword}'")
        print(f"   Keyword Length: {len(keyword)} chars")
        print(f"   URL Encoded: {urllib.parse.quote(keyword)}")

    print("\n\n【Step 2】Direct API Call Test")
    print("-"*70)

    for file_path in all_files:
        filename = os.path.basename(file_path)
        keyword = _build_search_keyword_from_filename(file_path)
        is_failed_case = file_path in failed_files

        print(f"\n{'❌' if is_failed_case else '✅'} Testing: {filename}")
        print(f"   Keyword: '{keyword}'")

        if not keyword:
            print(f"   ⚠️ ERROR: Empty keyword!")
            continue

        try:
            results = await _search_netease_rest(keyword, limit=5)

            if results:
                print(f"   🎉 Found {len(results)} results:")
                for i, result in enumerate(results[:3], 1):
                    print(f"      {i}. {result.title} - {result.artist}")
                    print(f"         Album: {result.album}")

                if is_failed_case:
                    print(f"   ⚠️ UNEXPECTED: This should have failed but succeeded!")
            else:
                print(f"   💔 No results found (this is the problem!)")

                # 尝试使用更短的关键词
                short_keyword = keyword.split()[0] if keyword else ""
                if short_keyword and len(short_keyword) < len(keyword):
                    print(f"\n   🔍 Trying shorter keyword: '{short_keyword}'")
                    short_results = await _search_netease_rest(short_keyword, limit=5)
                    if short_results:
                        print(f"   ✅ Shorter keyword works! Found {len(short_results)} results:")
                        for i, result in enumerate(short_results[:3], 1):
                            print(f"      {i}. {result.title} - {result.artist}")
                    else:
                        print(f"   ❌ Shorter keyword also failed")

        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()

    print("\n\n【Step 3】Manual URL Construction Test")
    print("-"*70)
    print("Testing raw HTTP request with different encodings...")

    test_keywords = [
        "夢の歩みを見上げて",
        "心象の中の光",
        "松本文紀 夢の歩みを見上げて",
        "松本文紀 心象の中の光",
    ]

    for kw in test_keywords:
        print(f"\n🔍 Testing: '{kw}'")

        try:
            import ssl
            import http.client
            from urllib.request import Request, urlopen
            from urllib.parse import urlencode

            params = urlencode({
                's': kw,
                'type': 1,
                'offset': 0,
                'total': 'true',
                'limit': 3
            })

            url = f'https://music.163.com/api/search/get/web?{params}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://music.163.com/',
            }

            req = Request(url, headers=headers)
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                songs = data.get('result', {}).get('songs', [])

                if songs:
                    print(f"   ✅ Found {len(songs)} results")
                    for song in songs[:2]:
                        print(f"      - {song['name']} - {song['artists'][0]['name']}")
                else:
                    print(f"   ❌ No results")
                    print(f"   API Response Code: {data.get('code')}")
                    if data.get('msg'):
                        print(f"   API Message: {data.get('msg')}")

        except Exception as e:
            print(f"   ❌ Error: {e}")


async def main():
    await debug_specific_files()

    print("\n\n" + "="*70)
    print("[DEBUG COMPLETE] Check output above for diagnosis")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
