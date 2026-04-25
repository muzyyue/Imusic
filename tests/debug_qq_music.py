#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug QQ Music search issue"""
import sys
import os
import json
import http.client
from urllib.parse import urlencode

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_raw_api():
    """Test QQ Music raw API (Unified Gateway)"""
    print("=" * 60)
    print("[DEBUG] Testing QQ Music Raw API (Unified Gateway: u.y.qq.com)")
    print("=" * 60)

    keyword = "周杰伦 晴天"
    print(f"\nKeyword: {keyword}")

    try:
        # 构建请求体（统一网关格式）
        request_body = json.dumps({
            "comm": {
                "ct": 24,
                "cv": 1000000,
            },
            "search": {
                "method": "DoSearchForQQMusicLite",
                "module": "music.search.SearchCgiService",
                "param": {
                    "query": keyword,
                    "page_num": 1,
                    "num_per_page": 3,
                    "search_type": 0,
                }
            }
        }, ensure_ascii=False).encode('utf-8')

        print(f"Request Body: {request_body[:200]}...")

        # 使用 HTTPS POST 请求
        conn = http.client.HTTPSConnection('u.y.qq.com', timeout=10)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://y.qq.com/',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        conn.request('POST', '/cgi-bin/musicu.fcg', body=request_body, headers=headers)
        response = conn.getresponse()
        status = response.status
        raw_data = response.read().decode('utf-8')
        conn.close()

        print(f"\nHTTP Status: {status}")
        print(f"Response Length: {len(raw_data)} chars")
        print(f"\nRaw Response:")
        print(raw_data[:1500] if len(raw_data) > 1500 else raw_data)

        data = json.loads(raw_data)
        print(f"\nAPI Result Code: {data.get('code')}")

        if data.get('code') == 0:
            # 提取歌曲列表（统一网关路径）
            search_obj = data.get('search', {})
            data_obj = search_obj.get('data', {})
            body = data_obj.get('body', {})
            songs = body.get('item_song', [])
            meta = body.get('meta', {})

            print(f"Total Results (meta): {meta.get('estimate_sum', 'N/A')}")
            print(f"[OK] Found {len(songs)} songs in item_song!")

            for song in songs:
                name = song.get('name', 'Unknown')
                singer = song.get('singer', [{}])[0].get('name', 'Unknown') if song.get('singer') else 'Unknown'
                album = song.get('album', {}).get('name', 'Unknown') if isinstance(song.get('album'), dict) else 'Unknown'
                print(f"  - {name} - {singer} ({album})")
        else:
            error_msg = data.get('msg', 'Unknown error')
            print(f"[ERROR] API Error: {error_msg}")

    except Exception as e:
        print(f"[ERROR] Request Failed: {e}")
        import traceback
        traceback.print_exc()

def test_parse_function():
    """Test parse function with new API format"""
    print("\n" + "=" * 60)
    print("[DEBUG] Testing _parse_qqmusic_result function (New Format)")
    print("=" * 60)

    from auto_tag.audio_recognize import _parse_qqmusic_result

    # 使用新接口的字段格式（嵌套 album 对象）
    test_song = {
        'id': 123456,
        'mid': 'xxxxxxxxxxxx',
        'name': '晴天',
        'singer': [{'id': 1, 'mid': 'yyy', 'name': '周杰伦'}],
        'album': {'id': 789, 'mid': 'yyyyyyyyyyyy', 'name': '叶惠美'},
        'interval': '249',
    }

    print("\nInput Data (New Official API Format):")
    print(json.dumps(test_song, ensure_ascii=False, indent=2))

    result = _parse_qqmusic_result(test_song)
    print(f"\nParsed Result:")
    print(f"  source: {result.source}")
    print(f"  title: {result.title}")
    print(f"  artist: {result.artist}")
    print(f"  album: {result.album}")
    print(f"  duration: {result.duration}")
    print(f"  cover_link: {result.cover_link[:80]}...")
    print(f"  confidence: {result.confidence}")

def test_search_function():
    """Test full search function"""
    print("\n" + "=" * 60)
    print("[DEBUG] Testing _do_qqmusic_search function")
    print("=" * 60)

    from auto_tag.audio_recognize import _do_qqmusic_search

    results = _do_qqmusic_search("周杰伦 晴天", limit=3)
    print(f"\nReturned Results: {len(results)}")

    for r in results:
        print(f"  - [{r.source}] {r.title} - {r.artist} ({r.album})")

if __name__ == '__main__':
    test_raw_api()
    test_parse_function()
    test_search_function()

    print("\n" + "=" * 60)
    print("[DONE] Debug Test Complete")
    print("=" * 60)
