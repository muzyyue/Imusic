#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试网易云音乐声音类型搜索（type=2000）

根据 API 文档，/cloudsearch 接口支持以下 type 值：
- 1: 单曲
- 10: 专辑
- 100: 歌手
- 1000: 歌单
- 1002: 用户
- 1004: MV
- 1006: 歌词
- 1009: 电台
- 1014: 视频
- 1018: 综合
- **2000: 声音(返回字段格式会不一样)** ← 目标

本脚本用于测试 type=2000 的返回数据结构。
"""
import json
import sys
import os
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_sound_search(keyword: str, search_type: int = 2000, limit: int = 5):
    """
    测试指定类型的搜索

    Args:
        keyword: 搜索关键词
        search_type: 搜索类型（2000=声音）
        limit: 返回数量
    """
    print(f"\n{'='*60}")
    print(f"[TEST] 搜索类型: {search_type}")
    print(f"[TEST] 关键词: {keyword}")
    print(f"{'='*60}")

    try:
        # 使用 /cloudsearch 接口（新接口）
        params = urlencode({
            'keywords': keyword,
            'type': search_type,
            'offset': 0,
            'limit': limit
        })
        
        # 尝试两个接口
        endpoints = [
            f'https://music.163.com/cloudsearch?{params}',  # 新接口
            f'https://music.163.com/api/search/get/web?{params}',  # 旧接口
        ]
        
        for url in endpoints:
            print(f"\n[INFO] 尝试接口: {url[:80]}...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://music.163.com/',
            }
            
            req = Request(url, headers=headers)
            
            try:
                with urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    
                    if data.get('code') == 200:
                        result = data.get('result', {})
                        print(f"\n[SUCCESS] 搜索成功！")
                        print(f"[INFO] 返回 code: {data.get('code')}")
                        print(f"[INFO] 结果数量: {result.get('count', 0)}")
                        
                        # 分析数据结构
                        if search_type == 2000:
                            # 声音类型的特殊处理
                            sounds = result.get('sounds', [])
                            print(f"\n[INFO] 声音结果字段: {list(result.keys())}")
                            
                            if sounds:
                                print(f"\n[INFO] 找到 {len(sounds)} 条声音结果:")
                                for i, sound in enumerate(sounds[:3], 1):
                                    print(f"\n  --- 声音 {i} ---")
                                    print(f"  字段列表: {list(sound.keys())}")
                                    
                                    # 提取关键字段
                                    print(f"  name: {sound.get('name', 'N/A')}")
                                    print(f"  id: {sound.get('id', 'N/A')}")
                                    print(f"  type: {sound.get('type', 'N/A')}")
                                    print(f"  duration: {sound.get('duration', 'N/A')}")
                                    print(f"  program: {sound.get('program', {}).get('name', 'N/A') if sound.get('program') else 'N/A'}")
                                    print(f"  radio: {sound.get('radio', {}).get('name', 'N/A') if sound.get('radio') else 'N/A'}")
                                    print(f"  完整数据（前500字符）:")
                                    print(f"  {json.dumps(sound, ensure_ascii=False)[:500]}...")
                                
                                return True, data
                            else:
                                print("[WARN] 无声音结果")
                                return False, None
                        else:
                            # 其他类型的通用处理
                            songs = result.get('songs', [])
                            print(f"\n[INFO] 找到 {len(songs)} 条结果:")
                            for i, song in enumerate(songs[:3], 1):
                                print(f"  {i}. {song.get('name')} - {song.get('artists', [{}])[0].get('name', '') if song.get('artists') else ''}")
                            
                            return True, data
                    else:
                        print(f"[FAIL] API 返回错误: code={data.get('code')}, msg={data.get('msg', '')}")
                        continue
                        
            except HTTPError as e:
                print(f"[ERROR] HTTP {e.code}: {e.reason}")
                continue
            except URLError as e:
                print(f"[ERROR] URL Error: {e.reason}")
                continue
                
    except Exception as e:
        print(f"[ERROR] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False, None
    
    print("[FAIL] 所有接口都失败了")
    return False, None


def main():
    """主测试函数"""
    print("\n" + "🔍"*30)
    print("网易云音乐声音类型搜索测试 (type=2000)")
    print("🔍"*30)
    
    # 测试关键词列表
    test_cases = [
        ("周杰伦", "知名歌手"),
        ("故事", "常见关键词"),
        ("晚安", "情感类声音"),
        ("白噪音", "功能性声音"),
    ]
    
    results_summary = []
    
    for keyword, desc in test_cases:
        print(f"\n\n{'#'*60}")
        print(f"# 测试用例: {keyword} ({desc})")
        print(f"{'#'*60}")
        
        success, data = test_sound_search(keyword, search_type=2000, limit=3)
        results_summary.append((keyword, success))
        
        if success and data:
            # 保存第一个成功的完整响应到文件，便于分析
            if not os.path.exists('test_sound_response.json'):
                with open('test_sound_response.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"\n[SAVE] 已保存完整响应对 test_sound_response.json")
    
    # 测试对比：普通歌曲 vs 声音
    print(f"\n\n{'#'*60}")
    print("# 对比测试: 同一关键词的歌曲搜索 vs 声音搜索")
    print(f"{'#'*60}")
    
    compare_keyword = "周杰伦"
    
    print(f"\n>>> 普通歌曲搜索 (type=1):")
    test_sound_search(compare_keyword, search_type=1, limit=2)
    
    print(f"\n>>> 声音搜索 (type=2000):")
    test_sound_search(compare_keyword, search_type=2000, limit=2)
    
    # 总结
    print(f"\n\n{'='*60}")
    print("[SUMMARY] 测试结果总结")
    print(f"{'='*60}")
    
    success_count = sum(1 for _, s in results_summary if s)
    total_count = len(results_summary)
    
    for keyword, success in results_summary:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {keyword}: {status}")
    
    print(f"\n总计: {success_count}/{total_count} 个测试通过")
    
    if success_count > 0:
        print("\n[SUCCESS] 声音类型搜索功能可用！可以开始集成到项目中。")
        return 0
    else:
        print("\n[FAIL] 所有声音搜索都失败，需要检查 API 或网络。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
