#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""简单测试声音搜索"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_tag.audio_recognize import _do_radio_search


def test_radio_search():
    """测试电台搜索"""
    print("Testing radio search for: 故事")
    
    radios = _do_radio_search("故事", limit=3)
    
    print(f"Found {len(radios)} radios:")
    
    for i, r in enumerate(radios, 1):
        print(f"\n{i}. {r.title}")
        print(f"   Source: {r.source}")
        print(f"   Artist: {r.artist}")
        print(f"   Album (Category): {r.album}")
        print(f"   Cover: {'Yes' if r.cover_link else 'No'}")
        
        if r.raw_data:
            print(f"   Raw keys: {list(r.raw_data.keys())[:8]}")
    
    return len(radios) > 0


if __name__ == "__main__":
    ok = test_radio_search()
    print(f"\n{'PASS' if ok else 'FAIL'}")
