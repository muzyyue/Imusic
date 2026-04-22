#!/usr/bin/env python
"""
测试 Safe 模式的网易云搜索功能

验证 _search_netease 和 _search_kugou 函数是否可以正常工作。
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_tag.audio_recognize import _search_netease, _search_kugou, _get_safe_netease_api, _get_safe_kugou_api


async def test_netease_search():
    """测试网易云音乐搜索"""
    print("\n" + "="*60)
    print("🎵 测试网易云音乐搜索（Safe 模式）")
    print("="*60)

    keyword = "周杰伦 晴天"
    print(f"\n搜索关键词: {keyword}")

    try:
        results = await _search_netease(keyword, limit=3)

        if results:
            print(f"\n✅ 搜索成功！找到 {len(results)} 条结果:\n")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.title} - {result.artist}")
                print(f"     专辑: {result.album}")
                print(f"     时长: {result.duration}秒")
                print(f"     来源: {result.source}")
                print()
            return True
        else:
            print("❌ 搜索结果为空")
            return False

    except Exception as e:
        print(f"❌ 搜索出错: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_kugou_search():
    """测试酷狗音乐搜索"""
    print("\n" + "="*60)
    print("🎵 测试酷狗音乐搜索（Safe 模式）")
    print("="*60)

    keyword = "周杰伦 晴天"
    print(f"\n搜索关键词: {keyword}")

    try:
        results = await _search_kugou(keyword, limit=3)

        if results:
            print(f"\n✅ 搜索成功！找到 {len(results)} 条结果:\n")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.title} - {result.artist}")
                print(f"     专辑: {result.album}")
                print(f"     时长: {result.duration}秒")
                print(f"     来源: {result.source}")
                print()
            return True
        else:
            print("❌ 搜索结果为空")
            return False

    except Exception as e:
        print(f"❌ 搜索出错: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "🔍"*30)
    print("Safe 模式搜索功能测试")
    print("🔍"*30)

    # 测试网易云
    netease_ok = await test_netease_search()

    # 测试酷狗
    kugou_ok = await test_kugou_search()

    # 总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    print(f"  网易云音乐: {'✅ 通过' if netease_ok else '❌ 失败'}")
    print(f"  酷狗音乐:   {'✅ 通过' if kugou_ok else '❌ 失败'}")

    if netease_ok or kugou_ok:
        print("\n🎉 Safe 模式搜索功能正常工作！")
        return 0
    else:
        print("\n⚠️  所有搜索都失败，请检查 pymusiclibrary 安装")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
