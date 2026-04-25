#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试声音搜索 - 修复版"""
import json
import sys
import io
from urllib.request import Request, urlopen
from urllib.parse import quote

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://music.163.com/',
}

def test_api(url: str, label: str):
    """测试单个 API"""
    print(f"\n{'='*50}")
    print(f"[{label}]")
    print(f"URL: {url[:100]}...")
    
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as resp:
            raw = resp.read()
            if not raw:
                print("[EMPTY] No response")
                return
            
            text = raw.decode('utf-8')
            data = json.loads(text)
            code = data.get('code', -1)
            
            if code == 200:
                result = data.get('result', {})
                keys = list(result.keys()) if result else []
                count = result.get('count', 0) if result else 0
                
                print(f"[OK] code=200")
                print(f"     Keys: {keys}")
                print(f"     Count: {count}")
                
                # 检查各种可能的结果字段
                for field in ['sounds', 'songs', 'djRadios', 'radios', 'programs']:
                    items = result.get(field, [])
                    if items:
                        print(f"\n     Found {len(items)} '{field}':")
                        item = items[0]
                        print(f"     Fields: {list(item.keys())[:12]}")
                        name = (item.get('name') or 
                               item.get('songName') or 
                               item.get('mainTitle') or 
                               item.get('title') or 'N/A')
                        print(f"     Name: {name}")
                        
                        # 保存第一个成功的
                        with open('test_sound_found.json', 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        print(f"     [SAVED] test_sound_found.json")
                        break
                else:
                    print("     [WARN] No data fields found")
            else:
                msg = data.get('msg', '')[:150]
                print(f"[FAIL] code={code}, msg={msg}")
                
    except Exception as e:
        err_type = type(e).__name__
        err_msg = str(e)[:100]
        print(f"[ERROR] {err_type}: {err_msg}")

# 测试用例
tests = [
    # (URL, label)
    (
        f'https://music.163.com/api/search/get/web?s={quote("晚安")}&type=2000&limit=3',
        'Type 2000 (Sound)'
    ),
    (
        f'https://music.163.com/api/search/get/web?s={quote("故事")}&type=1009&limit=3',
        'Type 1009 (Radio)'
    ),
    (
        f'https://music.163.com/api/search/get/web?s={quote("白噪音")}&type=1&limit=3',
        'Type 1 (Song) for comparison'
    ),
]

for url, label in tests:
    test_api(url, label)

print("\n\n[DONE] All tests completed")
