#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 cloudsearch 接口的不同调用方式"""
import json
import sys
import io
import hashlib
import random
from urllib.request import Request, urlopen
from urllib.parse import urlencode

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def encrypt_params(params: dict) -> str:
    """模拟网易云 API 的参数加密"""
    text = json.dumps(params, separators=(',', ':'))
    
    # 简单的模拟加密（实际应该用 AES）
    # 这里只是测试，实际需要完整的加密实现
    return text

keyword = "晚安"

print("="*60)
print("Testing NetEase CloudSearch API")
print(f"Keyword: {keyword}")
print("="*60)

# Test 1: 直接带关键词参数
print("\n[Test 1] Direct keyword parameter:")
try:
    params = {
        'keywords': keyword,
        'type': 2000,
        'offset': 0,
        'limit': 3,
        'total': 'true'
    }
    
    # 尝试 POST 请求
    url = 'https://music.163.com/weapi/cloudsearch/get/web'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://music.163.com/',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    data = urlencode({
        'params': encrypt_params(params),
        'encSecKey': 'test'  # 实际需要正确的加密密钥
    }).encode('utf-8')
    
    req = Request(url, data=data, headers=headers, method='POST')
    
    with urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print(f"Response code: {result.get('code')}")
        if result.get('code') == 200:
            res_data = result.get('result', {})
            print(f"Result keys: {list(res_data.keys())}")
            
            sounds = res_data.get('sounds', [])
            print(f"Sounds count: {len(sounds)}")
            
            if sounds:
                sound = sounds[0]
                print(f"\nFirst sound structure:")
                print(json.dumps(sound, ensure_ascii=False, indent=2)[:600])
                
                with open('test_cloudsearch_sound.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print("\n[SAVED] test_cloudsearch_sound.json")
        else:
            print(f"Error: {result.get('msg', '')[:200]}")

except Exception as e:
    print(f"[ERROR] {e}")

# Test 2: 使用 GET + cookies 模拟浏览器
print("\n[Test 2] GET with browser-like request:")
try:
    url = f'https://music.163.com/api/cloudsearch/get/web?keywords={keyword}&type=2000&limit=3'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://music.163.com/search/m/?s=' + keyword,
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cookie': 'NMTID=xxx; _ntes_nnid=xxx; _ntes_nuid=xxx',
    }
    
    req = Request(url, headers=headers)
    
    with urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print(f"Response code: {result.get('code')}")
        
        if result.get('code') == 200:
            res_data = result.get('result', {})
            print(f"Result keys: {list(res_data.keys())}")
            print(f"Count: {res_data.get('count', 0)}")
        else:
            print(f"Error msg: {result.get('msg', '')[:200]}")

except Exception as e:
    print(f"[ERROR] {e}")

# Test 3: 测试 type=1009 (电台) 是否有数据
print("\n\n[Test 3] Type 1009 (Radio) with keyword '故事':")
try:
    radio_keyword = "故事"
    url = f'https://music.163.com/api/search/get/web?s={radio_keyword}&type=1009&limit=3'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://music.163.com/',
    }
    
    req = Request(url, headers=headers)
    
    with urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        
        if result.get('code') == 200:
            res = result.get('result', {})
            radios = res.get('djRadios', [])
            print(f"Found {len(radios)} radios")
            
            if radios:
                radio = radios[0]
                print(f"\nFirst radio fields: {list(radio.keys())[:15]}")
                print(f"Name: {radio.get('name', 'N/A')}")
                print(f"ID: {radio.get('id', 'N/A')}")
                print(f"Structure preview:")
                print(json.dumps(radio, ensure_ascii=False, indent=2)[:500])

except Exception as e:
    print(f"[ERROR] {e}")

print("\n[DONE]")
