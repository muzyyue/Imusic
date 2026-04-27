#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试不同接口和 type 值"""
import json
import sys
import io
from urllib.request import Request, urlopen
from urllib.parse import urlencode

keyword = "周杰伦"
test_configs = [
    ('/api/search/get/web', 2000, 'old_api_type_2000'),
    ('/api/search/get/web', 1009, 'old_api_type_1009'),
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://music.163.com/',
}

for endpoint, search_type, desc in test_configs:
    print(f"\n{'='*60}")
    print(f"Test: {desc}")
    print(f"Endpoint: {endpoint}, type: {search_type}")
    print('='*60)
    
    params = urlencode({
        's': keyword,
        'type': search_type,
        'offset': 0,
        'limit': 2
    })
    
    url = f'https://music.163.com{endpoint}?{params}'
    
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as resp:
            raw = resp.read().decode('utf-8')
            data = json.loads(raw)
            code = data.get('code')
            
            if code == 200:
                result = data.get('result', {})
                keys = list(result.keys())
                count = result.get('count', 0)
                
                print(f"[OK] Success! code={code}")
                print(f"    Result keys: {keys}")
                print(f"    Count: {count}")
                
                items = result.get('sounds') or result.get('songs') or result.get('radios') or []
                if items:
                    item = items[0]
                    print(f"    First item fields: {list(item.keys())[:15]}")
                    name = item.get('name') or item.get('songName') or item.get('title') or 'N/A'
                    print(f"    Name: {name}")
                    
                    with open('test_sound_success.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"    [SAVED] test_sound_success.json")
                else:
                    print(f"    [WARN] No items found in result")
            else:
                msg = data.get('msg', '')[:100]
                print(f"[FAIL] code={code}, msg={msg}")
                
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)[:100]}")

print("\n[DONE]")
