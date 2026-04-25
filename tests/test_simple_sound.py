#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""简单测试声音搜索"""
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode

keyword = "周杰伦"
params = urlencode({'keywords': keyword, 'type': 2000, 'limit': 2})
url = f'https://music.163.com/cloudsearch?{params}'

print(f"URL: {url}")
print(f"Testing sound search for: {keyword}\n")

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://music.163.com/',
}

req = Request(url, headers=headers)

try:
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Code: {data.get('code')}")
        
        if data.get('code') == 200:
            result = data.get('result', {})
            print(f"Result keys: {list(result.keys())}")
            print(f"Count: {result.get('count', 0)}")
            
            sounds = result.get('sounds', [])
            print(f"\nFound {len(sounds)} sounds:")
            
            if sounds:
                for i, s in enumerate(sounds[:2], 1):
                    print(f"\n--- Sound {i} ---")
                    print(json.dumps(s, ensure_ascii=False, indent=2)[:800])
                    
                # Save full response
                with open('test_sound_response.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print("\n✅ Saved to test_sound_response.json")
        else:
            print(f"Error: {data}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
