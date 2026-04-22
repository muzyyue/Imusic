# -*- coding: utf-8 -*-
"""测试 REST API 搜索功能"""
from auto_tag.lyric.manager import LyricManager
import json

manager = LyricManager()

print('=' * 60)
print('测试1: 搜索日文歌曲 "松本文紀"')
print('=' * 60)
test_keyword = '松本文紀'
results = manager._search_netease_rest_api(test_keyword, limit=5)
print(f'搜索关键词: {test_keyword}')
print(f'结果数量: {len(results)}')
if results:
    for i, song in enumerate(results[:3], 1):
        print(f'  {i}. {song["name"]} - {song["artist"]} ({song["album"]})')
else:
    print('  无结果')

print()
print('=' * 60)
print('测试2: 搜索 "山下航生"')
print('=' * 60)
test_keyword2 = '山下航生'
results2 = manager._search_netease_rest_api(test_keyword2, limit=5)
print(f'搜索关键词: {test_keyword2}')
print(f'结果数量: {len(results2)}')
if results2:
    for i, song in enumerate(results2[:3], 1):
        print(f'  {i}. {song["name"]} - {song["artist"]} ({song["album"]})')
else:
    print('  无结果')

print()
print('=' * 60)
print('测试3: 关键词构建策略')
print('=' * 60)
test_cases = [
    ('D.a.l.main Theme', 'Go Sakabe'),
    ('Dango Dai Kazoku', 'Chata'),
    ('夢の歩みを見上げて', '松本文紀'),
]
for title, artist in test_cases:
    keyword = manager._build_search_keyword(title, artist)
    print(f'  title="{title}", artist="{artist}" -> keyword="{keyword}"')

print()
print('✅ 所有测试完成！')
