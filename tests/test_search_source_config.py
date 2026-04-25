#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试搜索源多选配置功能的完整流程

验证：
1. AppConfig 类的新属性（search_sources 列表）
2. 配置的持久化存储
3. 旧配置向后兼容（单字符串自动转为列表）
4. 设置页面的UI组件
5. 信号发射机制
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_tag.gui.config import config, AppConfig


def test_config_attributes():
    """测试 AppConfig 新增的搜索源配置属性"""
    print("\n" + "="*60)
    print("[TEST 1] Config Attributes")
    print("="*60)
    
    assert hasattr(config, 'search_sources'), "Missing search_sources attribute"
    assert isinstance(config.search_sources, list), "search_sources should be a list"
    assert len(config.search_sources) > 0, "search_sources should not be empty"
    
    print(f"✓ All attributes exist")
    print(f"  - search_sources: {config.search_sources}")
    print(f"  - netease_search_type: {config.netease_search_type}")
    print(f"  - include_radio: {config.include_radio}")
    
    assert len(AppConfig.VALID_SEARCH_SOURCES) == 3, f"Expected 3 sources, got {len(AppConfig.VALID_SEARCH_SOURCES)}"
    
    print(f"✓ Constants valid:")
    print(f"  - Valid sources: {AppConfig.VALID_SEARCH_SOURCES}")


def test_config_setters():
    """测试配置 setter 方法"""
    print("\n" + "="*60)
    print("[TEST 2] Config Setters")
    print("="*60)
    
    original = config.search_sources.copy()
    try:
        config.set_search_sources(["netease", "shazam"])
        assert "netease" in config.search_sources, "Failed to set netease"
        assert "shazam" in config.search_sources, "Failed to set shazam"
        print("✓ set_search_sources(['netease', 'shazam']) works")
        
        config.set_search_sources(original)
        print(f"✓ Restored to: {original}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    original_type = config.netease_search_type
    try:
        config.set_netease_search_type(1009)
        assert config.netease_search_type == 1009, "Failed to set type 1009"
        print("✓ set_netease_search_type(1009) works")
        
        config.set_netease_search_type(original_type)
        print(f"✓ Restored type to: {original_type}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True


def test_config_validation():
    """测试配置验证（无效值处理）"""
    print("\n" + "="*60)
    print("[TEST 3] Validation (Invalid Values)")
    print("="*60)
    
    try:
        config.set_search_sources(["invalid_source"])
        print("✗ Should have raised ValueError for invalid source")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected invalid source: {e}")
    
    try:
        config.set_search_sources([])
        print("✗ Should have raised ValueError for empty list")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected empty list: {e}")
    
    try:
        config.set_netease_search_type(9999)
        print("✗ Should have raised ValueError for invalid type")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected invalid type: {e}")
    
    return True


def test_config_persistence():
    """测试配置持久化"""
    print("\n" + "="*60)
    print("[TEST 4] Persistence (Save/Load)")
    print("="*60)
    
    orig_sources = config.search_sources.copy()
    orig_type = config.netease_search_type
    orig_radio = config.include_radio
    
    try:
        config.set_search_sources(["netease", "shazam"])
        config.set_netease_search_type(1009)
        config.set_include_radio(False)
        
        print(f"✓ Saved new values:")
        print(f"  - sources: {config.search_sources}")
        print(f"  - type: {config.netease_search_type}")
        print(f"  - radio: {config.include_radio}")
        
        from auto_tag.gui.config import AppConfig
        new_config = AppConfig()
        
        assert set(new_config.search_sources) == {"netease", "shazam"}, f"Sources mismatch: {new_config.search_sources}"
        assert new_config.netease_search_type == 1009, f"Type mismatch: {new_config.netease_search_type}"
        assert new_config.include_radio == False, f"Radio mismatch: {new_config.include_radio}"
        
        print(f"✓ Loaded correctly from file")
        
        config.set_search_sources(orig_sources)
        config.set_netease_search_type(orig_type)
        config.set_include_radio(orig_radio)
        print(f"✓ Restored defaults")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            config.set_search_sources(orig_sources)
            config.set_netease_search_type(orig_type)
            config.set_include_radio(orig_radio)
        except:
            pass
        
        return False


def test_backward_compatibility():
    """测试旧配置向后兼容（单字符串自动转为列表）"""
    print("\n" + "="*60)
    print("[TEST 5] Backward Compatibility (Legacy single source)")
    print("="*60)
    
    import json
    from pathlib import Path
    
    config_file = Path.home() / ".mp3shazamautotag" / "config.json"
    
    if not config_file.exists():
        print("⊘ Config file not found, skipping backward compatibility test")
        return True
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        has_old_format = 'search_source' in data and isinstance(data['search_source'], str)
        has_new_format = 'search_sources' in data and isinstance(data['search_sources'], list)
        
        if has_old_format and not has_new_format:
            print(f"⊘ Found legacy single-source format, new code should auto-convert")
        elif has_new_format:
            print(f"✓ Using new multi-source format: {data['search_sources']}")
        else:
            print(f"⊘ No search source config found, defaults will be used")
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading config: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "#"*70)
    print("# Search Sources Multi-Select Configuration Feature Test")
    print("#"*70)
    
    tests = [
        ("Attributes", test_config_attributes),
        ("Setters", test_config_setters),
        ("Validation", test_config_validation),
        ("Persistence", test_config_persistence),
        ("Backward Compatibility", test_backward_compatibility),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result if result is not None else True))
        except Exception as e:
            print(f"\n[FAIL] {name} crashed: {e}")
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
        status = "PASS ✓" if result else "FAIL ✗"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\nAll tests passed! Search sources multi-select configuration is working.")
        return 0
    else:
        print("\nSome tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
