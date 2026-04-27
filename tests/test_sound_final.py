#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试声音搜索 API (需网络访问，已禁用)"""
import json
import pytest
from urllib.request import Request, urlopen
from urllib.parse import quote

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://music.163.com/',
}

@pytest.mark.skip(reason="需要网络访问的集成测试，默认禁用")
def test_api():
    """测试声音搜索 API (手动运行: python tests/test_sound_final.py)"""
    url = f'https://music.163.com/api/search/get/web?s={quote("晚安")}&type=2000&limit=3'
    req = Request(url, headers=headers)
    with urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        assert data.get('code') == 200

if __name__ == "__main__":
    test_api()
