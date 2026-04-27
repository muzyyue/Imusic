#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试网易云音乐声音类型搜索（type=2000）

需网络访问，默认跳过。手动运行: python tests/test_sound_type_search.py
"""
import json
import pytest

@pytest.mark.skip(reason="需要网络访问的集成测试，默认禁用")
def test_sound_search():
    """测试声音搜索 API (手动运行)"""
    from urllib.request import Request, urlopen
    from urllib.parse import urlencode

    params = urlencode({'keywords': '周杰伦', 'type': 2000, 'offset': 0, 'limit': 3})
    url = f'https://music.163.com/cloudsearch?{params}'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://music.163.com/',
    }
    req = Request(url, headers=headers)
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        assert data.get('code') == 200

if __name__ == "__main__":
    test_sound_search()
