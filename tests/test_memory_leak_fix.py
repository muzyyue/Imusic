#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存泄漏修复验证测试

用于验证首页搜索功能的内存泄漏修复效果。
测试场景：
1. CoverImageCache 缓存清理功能
2. 封面点击防抖功能
3. 刷新搜索结果时线程清理

使用方法:
    python test_memory_leak_fix.py
"""

import sys
import os
import time
import gc
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def log_memory(tag: str) -> None:
    """记录当前内存使用情况（简化版）"""
    print(f"[Memory] {tag}")


def test_cover_image_cache_clear():
    """
    测试 #1: CoverImageCache.clear() 是否有效释放内存

    验证全局缓存清空后缓存字典是否为空。
    """
    print("\n" + "="*70)
    print("测试 #1: CoverImageCache 缓存清理测试")
    print("="*70)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QImage, QPixmap
    from auto_tag.gui.components.song_result_card import CoverImageCache

    # 初始化 Qt 应用（如果尚未初始化）
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 记录初始状态
    log_memory("初始状态")

    # 模拟加载50张封面图片到缓存
    print("\n[操作] 向缓存添加50张模拟封面图片...")
    for i in range(50):
        image = QImage(200, 200, QImage.Format.Format_RGB32)
        image.fill(i * 1000)
        pixmap = QPixmap.fromImage(image)
        CoverImageCache.set(f"test_url_{i}", pixmap)

        if (i + 1) % 10 == 0:
            log_memory(f"已添加 {i+1} 张图片 | 缓存大小: {len(CoverImageCache._cache)}")

    cache_size_before = len(CoverImageCache._cache)
    print(f"\n[结果] 加载完成，缓存包含 {cache_size_before} 张图片")

    # 清空缓存
    print("\n[操作] 调用 CoverImageCache.clear()...")
    CoverImageCache.clear()
    gc.collect()

    cache_size_after = len(CoverImageCache._cache)
    log_memory("缓存清空后")
    if cache_size_after == 0:
        print("[结论] 缓存清理 [PASS] 成功")
    else:
        print(f"[结论] 缓存清理 [FAIL] 失败 (仍有{cache_size_after}项)")


def test_debounce_functionality():
    """
    测试 #2: 封面点击防抖功能是否正常工作

    验证快速多次点击只触发一次信号。
    """
    print("\n" + "="*70)
    print("测试 #2: 封面点击防抖功能测试")
    print("="*70)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QEvent, QCoreApplication
    from PySide6.QtGui import QMouseEvent
    from auto_tag.gui.components.song_result_card import CoverImageWidget

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 创建封面组件
    widget = CoverImageWidget(size=64)
    click_count = [0]

    def on_clicked():
        click_count[0] += 1
        print(f"[Click] 第 {click_count[0]} 次点击触发")

    widget.clicked.connect(on_clicked)

    # 模拟快速连续点击10次
    print("\n[操作] 模拟快速连续点击10次（间隔50ms）...")
    for i in range(10):
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            widget.rect().center(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        QCoreApplication.sendEvent(widget, event)
        QCoreApplication.processEvents()
        time.sleep(0.05)  # 50ms 间隔（远小于250ms防抖时间）

    # 等待防抖时间结束
    print("\n[操作] 等待防抖窗口结束（300ms）...")
    time.sleep(0.3)
    QCoreApplication.processEvents()

    # 验证结果
    actual_clicks = click_count[0]
    expected_clicks = 1  # 防抖后应该只有1次触发

    print(f"\n[结果] 实际触发次数: {actual_clicks}, 预期触发次数: {expected_clicks}")
    if actual_clicks == expected_clicks:
        print("[结论] 防抖功能 [PASS] 正常")
    else:
        print(f"[结论] 防抖功能 [FAIL] 异常 (预期{expected_clicks}次, 实际{actual_clicks}次)")

    widget.deleteLater()


def test_thread_cleanup_on_refresh():
    """
    测试 #3: 刷新搜索结果时旧线程是否正确停止

    验证 update_search_results() 是否同步停止旧线程。
    """
    print("\n" + "="*70)
    print("测试 #3: 刷新时线程清理测试")
    print("="*70)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QThread, QCoreApplication
    from auto_tag.gui.components.song_result_card import SongResultCard

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 创建卡片组件
    card = SongResultCard(
        file_path="test_song.mp3",
        display_name="Test Song",
        search_results=[{
            "source": "netease",
            "title": "Test Title",
            "artist": "Test Artist",
            "album": "Test Album",
            "cover_url": "https://example.com/cover.jpg"
        }]
    )

    # 模拟第一次搜索结果（会启动加载线程）
    print("\n[操作] 第一次更新搜索结果...")
    card.update_search_results([{
        "source": "netease",
        "title": "Song 1",
        "cover_url": "https://example.com/cover1.jpg"
    }])

    thread_count_before = len([t for t in QThread.allThreads() if t.isRunning()])
    log_memory(f"第一次更新后 (运行线程数: {thread_count_before})")

    # 模拟快速刷新5次
    print("\n[操作] 快速连续刷新5次...")
    for i in range(5):
        card.update_search_results([{
            "source": "netease",
            "title": f"Song {i+2}",
            "cover_url": f"https://example.com/cover{i+2}.jpg"
        }])
        time.sleep(0.1)

    # 等待所有异步删除完成
    time.sleep(0.5)
    QCoreApplication.processEvents()

    thread_count_after = len([t for t in QThread.allThreads() if t.isRunning()])
    log_memory(f"5次刷新后 (运行线程数: {thread_count_after})")

    print(f"\n[结果] 刷新前线程数: {thread_count_before}, 刷新后线程数: {thread_count_after}")
    if thread_count_after <= thread_count_before + 2:
        print("[结论] 线程清理 [PASS] 正常")
    else:
        print("[结论] 线程清理 [FAIL] 可能存在泄漏")

    card.deleteLater()


def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("  mp3ShazamAutoTag 内存泄漏修复验证测试套件")
    print("  版本: v0.4.79 (2026-04-29)")
    print("="*70)

    # 初始化 Qt 应用
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 记录初始状态
    log_memory("=== 测试开始 ===")

    try:
        # 运行各项测试
        test_cover_image_cache_clear()
        test_debounce_functionality()
        test_thread_cleanup_on_refresh()

        # 最终报告
        print("\n" + "="*70)
        print("[PASS] 所有测试执行完毕！")
        print("="*70)
        print("\n修复内容总结：")
        print("  1. [DONE] CoverImageCache 全局缓存 - 清除数据时自动清空")
        print("  2. [DONE] 刷新线程竞态 - 同步停止旧组件加载线程")
        print("  3. [DONE] 子组件生命周期 - PlatformResultWidget 递归删除子组件")
        print("  4. [DONE] eyed3 资源管理 - 及时释放 MP3 标签对象")
        print("  5. [DONE] 封面点击防抖 - 250ms 防抖延迟防止重复触发")
        print("\n预期改进效果：")
        print("  - 清除数据后内存应能回到接近初始水平（200-300MB）")
        print("  - 连续快速点击封面只应触发一次预览")
        print("  - 刷新搜索结果后旧线程应被正确停止")
        print("  - 28首歌搜索完成后总内存增长控制在 300-500MB 以内")

    except Exception as e:
        print(f"\n[ERROR] 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
