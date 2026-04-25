#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试嵌套分组结构翻译文件

验证：
1. JSON 格式正确
2. 嵌套键访问正常工作
3. 所有模块的翻译都能正确获取
4. 格式化参数正常工作
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_tag.gui.i18n import translator, tr


def test_nested_structure():
    """测试嵌套结构完整性"""
    print("\n" + "="*70)
    print("[TEST 1] Nested Structure Validation")
    print("="*70)
    
    # 加载原始JSON验证结构
    with open('auto_tag/gui/i18n/locales/zh.json', 'r', encoding='utf-8') as f:
        zh = json.load(f)
    
    with open('auto_tag/gui/i18n/locales/en.json', 'r', encoding='utf-8') as f:
        en = json.load(f)
    
    # 验证顶层分组
    expected_groups = [
        'app_name',
        'navigation',
        'home_page',
        'file_list',
        'settings_page',      # ⭐ 新增搜索设置
        'converter',
        'music_manager',
        'lyrics',
        'search',
        'messages'
    ]
    
    for group in expected_groups:
        assert group in zh, f"Missing group: {group} in zh.json"
        assert group in en, f"Missing group: {group} in en.json"
        print(f"  ✓ Group '{group}' exists in both files")
    
    # 统计键数量
    def count_keys(d, prefix=""):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v, f"{prefix}.{k}")
            else:
                count += 1
        return count
    
    zh_keys = count_keys(zh)
    en_keys = count_keys(en)
    
    print(f"\n  ✓ zh.json total keys: {zh_keys}")
    print(f"  ✓ en.json total keys: {en_keys}")
    
    return True


def test_nested_key_access():
    """测试嵌套键访问功能"""
    print("\n" + "="*70)
    print("[TEST 2] Nested Key Access (translator.get())")
    print("="*70)
    
    test_cases = [
        # (嵌套键路径, 期望包含的文本片段)
        ("settings_page.title", "设置"),
        ("settings_page.search_settings_section", "搜索设置"),
        ("settings_page.search_source_label", "搜索源"),
        ("settings_page.sources.shazam", "Shazam"),
        ("settings_page.themes.light", "浅色"),
        
        ("navigation.home", "首页"),
        ("navigation.settings", "设置"),
        
        ("home_page.title", "音频识别"),
        ("home_page.select_files_btn", "选择文件"),
        
        ("file_list.columns.filename", "文件名"),
        ("file_list.status.pending", "等待中"),
        
        ("converter.title", "转换"),
        ("converter.status.completed", "完成"),
        
        ("lyrics.get_lyrics", "获取歌词"),
        ("lyrics.providers.netease", "网易云"),
        
        ("search.results_title", "搜索结果"),
        ("search.sources.shazam", "Shazam"),
        ("search.duration_comparison.excellent_match", "完美匹配"),
        
        ("messages.confirm_clear", "确定要清空"),
        ("messages.info_search_config_updated", "搜索配置已更新"),
    ]
    
    passed = 0
    failed = 0
    
    for key_path, expected_text in test_cases:
        result = tr(key_path)
        if expected_text in result:
            print(f"  ✓ {key_path:45s} → '{result[:30]}...'")
            passed += 1
        else:
            print(f"  ✗ {key_path:45s} → '{result}' (expected '{expected_text}')")
            failed += 1
    
    print(f"\n  Results: {passed}/{len(test_cases)} passed")
    return failed == 0


def test_format_parameters():
    """测试格式化参数在嵌套键中的使用"""
    print("\n" + "="*70)
    print("[TEST 3] Format Parameters with Nested Keys")
    print("="*70)
    
    test_cases = [
        ("converter.progress_format", {"done": 5, "total": 10, "remaining": 30}),
        ("messages.error_file_type", {"format": "mp3"}),
        ("messages.success_apply", {"count": 42}),
        ("lyrics.success_count", {"count": 10}),
        ("search.time_formats.seconds", {"seconds": 120}),
        ("search.time_formats.minutes_seconds", {"minutes": 2, "seconds": 30}),
    ]
    
    all_ok = True
    
    for key, params in test_cases:
        result = tr(key, **params)
        has_params = all(str(v) in result for v in params.values())
        
        status = "✓" if has_params else "✗"
        print(f"  {status} {key:45s} → {result[:50]}...")
        
        if not has_params:
            all_ok = False
    
    return all_ok


def test_settings_page_keys():
    """专门测试设置页面新增的所有翻译键"""
    print("\n" + "="*70)
    print("[TEST 4] Settings Page Keys (New Feature)")
    print("="*70)
    
    settings_keys = [
        "settings_page.title",
        "settings_page.general_section",
        "settings_page.language_label",
        "settings_page.language_hint",
        "settings_page.theme_label",
        "settings_page.theme_hint",
        "settings_page.search_settings_section",
        "settings_page.search_source_label",
        "settings_page.search_source_hint",
        "settings_page.netease_type_label",
        "settings_page.netease_type_hint",
        "settings_page.include_radio_label",
        "settings_page.include_radio_hint",
        "settings_page.sources.shazam",
        "settings_page.sources.netease",
        "settings_page.sources.kugou",
        "settings_page.themes.light",
        "settings_page.themes.dark",
        "settings_page.themes.auto",
        "settings_page.languages.zh",
        "settings_page.languages.en",
    ]
    
    missing = []
    
    for key in settings_keys:
        result = tr(key)
        if result == key:
            # 返回键名本身说明未找到
            missing.append(key)
            print(f"  ✗ {key:45s} → NOT FOUND")
        else:
            print(f"  ✓ {key:45s} → {result[:35]}...")
    
    if missing:
        print(f"\n  [FAIL] Missing {len(missing)} keys:")
        for k in missing:
            print(f"       - {k}")
        return False
    else:
        print(f"\n  [PASS] All {len(settings_keys)} settings page keys found!")
        return True


def main():
    """主测试函数"""
    print("\n" + "#"*70)
    print("# Nested i18n Structure Test Suite")
    print("#"*70)
    
    tests = [
        ("Structure Validation", test_nested_structure),
        ("Nested Key Access", test_nested_key_access),
        ("Format Parameters", test_format_parameters),
        ("Settings Page Keys", test_settings_page_keys),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            ok = test_func()
            results.append((name, ok))
        except Exception as e:
            print(f"\n[CRASH] {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 总结
    print("\n\n" + "="*70)
    print("[SUMMARY]")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Nested structure is working perfectly.")
        print("\n📊 New structure overview:")
        print("   ├── navigation     (3 keys)")
        print("   ├── home_page      (9 keys)")
        print("   ├── file_list      (9 keys)")
        print("   ├── settings_page  (25 keys) ⭐ new search config")
        print("   ├── converter      (40+ keys)")
        print("   ├── music_manager (20+ keys)")
        print("   ├── lyrics         (30+ keys)")
        print("   ├── search         (40+ keys)")
        print("   └── messages       (7 keys)")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
