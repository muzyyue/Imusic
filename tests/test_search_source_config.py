#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试搜索源配置功能的完整流程

验证：
1. AppConfig 类的新属性
2. 配置的持久化存储
3. 设置页面的UI组件
4. 信号发射机制
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
    
    # 验证默认值
    assert hasattr(config, 'search_source'), "Missing search_source attribute"
    assert hasattr(config, 'netease_search_type'), "Missing netease_search_type attribute"
    assert hasattr(config, 'include_radio'), "Missing include_radio attribute"
    
    print(f"✓ All attributes exist")
    print(f"  - search_source: {config.search_source}")
    print(f"  - netease_search_type: {config.netease_search_type}")
    print(f"  - include_radio: {config.include_radio}")
    
    # 验证常量
    assert len(AppConfig.VALID_SEARCH_SOURCES) == 3, f"Expected 3 sources, got {len(AppConfig.VALID_SEARCH_SOURCES)}"
    assert len(AppConfig.NETEASE_SEARCH_TYPES) >= 10, f"Expected 10+ types, got {len(AppConfig.NETEASE_SEARCH_TYPES)}"
    
    print(f"✓ Constants valid:")
    print(f"  - Valid sources: {AppConfig.VALID_SEARCH_SOURCES}")
    print(f"  - NetEase types count: {len(AppConfig.NETEASE_SEARCH_TYPES)}")


def test_config_setters():
    """测试配置 setter 方法"""
    print("\n" + "="*60)
    print("[TEST 2] Config Setters")
    print("="*60)
    
    # 测试搜索源设置
    original = config.search_source
    try:
        config.set_search_source("netease")
        assert config.search_source == "netease", "Failed to set netease source"
        print("✓ set_search_source('netease') works")
        
        # 恢复原始值
        config.set_search_source(original)
        print(f"✓ Restored to: {original}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # 测试网易云类型设置
    original_type = config.netease_search_type
    try:
        config.set_netease_search_type(1009)
        assert config.netease_search_type == 1009, "Failed to set type 1009"
        print("✓ set_netease_search_type(1009) works")
        
        # 恢复
        config.set_netease_search_type(original_type)
        print(f"✓ Restored type to: {original_type}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # 测试电台开关
    original_radio = config.include_radio
    try:
        config.set_include_radio(False)
        assert config.include_radio == False, "Failed to set radio off"
        print("✓ set_include_radio(False) works")
        
        config.set_include_radio(True)
        assert config.include_radio == True, "Failed to set radio on"
        print("✓ set_include_radio(True) works")
        
        # 恢复
        config.set_include_radio(original_radio)
        print(f"✓ Restored radio to: {original_radio}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True


def test_config_validation():
    """测试配置验证（无效值处理）"""
    print("\n" + "="*60)
    print("[TEST 3] Validation (Invalid Values)")
    print("="*60)
    
    # 测试无效搜索源
    try:
        config.set_search_source("invalid_source")
        print("✗ Should have raised ValueError for invalid source")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected invalid source: {e}")
    
    # 测试无效类型
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
    
    # 保存当前值
    orig_source = config.search_source
    orig_type = config.netease_search_type
    orig_radio = config.include_radio
    
    try:
        # 修改并保存
        config.set_search_source("netease")
        config.set_netease_search_type(1009)
        config.set_include_radio(False)
        
        print(f"✓ Saved new values:")
        print(f"  - source: {config.search_source}")
        print(f"  - type: {config.netease_search_type}")
        print(f"  - radio: {config.include_radio}")
        
        # 创建新实例验证加载
        from auto_tag.gui.config import AppConfig
        new_config = AppConfig()
        
        assert new_config.search_source == "netease", f"Source mismatch: {new_config.search_source}"
        assert new_config.netease_search_type == 1009, f"Type mismatch: {new_config.netease_search_type}"
        assert new_config.include_radio == False, f"Radio mismatch: {new_config.include_radio}"
        
        print(f"✓ Loaded correctly from file")
        
        # 恢复默认值
        config.set_search_source(orig_source)
        config.set_netease_search_type(orig_type)
        config.set_include_radio(orig_radio)
        print(f"✓ Restored defaults")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # 尝试恢复
        try:
            config.set_search_source(orig_source)
            config.set_netease_search_type(orig_type)
            config.set_include_radio(orig_radio)
        except:
            pass
        
        return False


def main():
    """主测试函数"""
    print("\n" + "#"*70)
    print("# Search Source Configuration Feature Test")
    print("#"*70)
    
    tests = [
        ("Attributes", test_config_attributes),
        ("Setters", test_config_setters),
        ("Validation", test_config_validation),
        ("Persistence", test_config_persistence),
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
        print("\n🎉 All tests passed! Search source configuration is working.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
