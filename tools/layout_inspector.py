# -*- coding: utf-8 -*-
"""
布局间距检查器

在程序运行时按 Ctrl+C 停止，会输出所有布局的详细信息，
帮助你找出哪些区域的间距设置有问题。
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLayout
from PySide6.QtCore import QObject


def analyze_layout(layout, path="", depth=0):
    """
    分析布局的详细信息
    
    Args:
        layout: QLayout 对象
        path: 布局路径（用于追踪层级）
        depth: 当前深度
    """
    if not layout:
        return
    
    layout_name = layout.__class__.__name__
    indent = "│   " * depth
    
    print(f"\n{indent}┌─ {layout_name}")
    print(f"{indent}│  路径：{path}")
    print(f"{indent}│")
    print(f"{indent}├─ 间距设置:")
    print(f"{indent}│   • Spacing: {layout.spacing()}px")
    
    margins = layout.contentsMargins()
    print(f"{indent}│   • ContentsMargins:")
    print(f"{indent}│      上：{margins.top()}px")
    print(f"{indent}│      下：{margins.bottom()}px")
    print(f"{indent}│      左：{margins.left()}px")
    print(f"{indent}│      右：{margins.right()}px")
    
    # 分析子项
    item_count = layout.count()
    if item_count > 0:
        print(f"{indent}│")
        print(f"{indent}├─ 子项数量：{item_count}")
        print(f"{indent}│")
        print(f"{indent}└─ 子项详情:")
        
        for i in range(item_count):
            item = layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget_name = widget.__class__.__name__
                    object_name = widget.objectName() or "无名称"
                    print(f"{indent}      [{i}] Widget: {widget_name} - {object_name}")
                    
                    # 递归分析子布局
                    child_layout = widget.layout()
                    if child_layout:
                        analyze_layout(child_layout, f"{path}/{object_name}", depth + 1)
                else:
                    child_layout = item.layout()
                    if child_layout:
                        print(f"{indent}      [{i}] Layout: {child_layout.__class__.__name__}")
                        analyze_layout(child_layout, f"{path}/[{i}]", depth + 1)


def find_layouts_by_path(layout, target_path_keywords):
    """
    根据路径关键词查找布局
    
    Args:
        layout: 起始布局
        target_path_keywords: 目标路径关键词列表
        
    Returns:
        匹配的布局列表
    """
    results = []
    
    def search_recursive(current_layout, current_path, depth):
        if not current_layout:
            return
        
        # 检查是否匹配关键词
        if any(keyword.lower() in current_path.lower() for keyword in target_path_keywords):
            results.append((current_layout, current_path, depth))
        
        # 递归搜索子布局
        item_count = current_layout.count()
        for i in range(item_count):
            item = current_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    child_layout = widget.layout()
                    if child_layout:
                        object_name = widget.objectName() or widget.__class__.__name__
                        search_recursive(child_layout, f"{current_path}/{object_name}", depth + 1)
                else:
                    child_layout = item.layout()
                    if child_layout:
                        search_recursive(child_layout, f"{current_path}/[{i}]", depth + 1)
    
    search_recursive(layout, "root", 0)
    return results


def main():
    """
    主函数：启动应用并分析布局
    """
    print("=" * 80)
    print("Qt 布局间距检查器")
    print("=" * 80)
    print()
    print(" 这个工具会：")
    print("   1. 启动应用程序")
    print("   2. 当你按 Ctrl+C 时，输出所有布局的详细信息")
    print("   3. 帮助你找出间距设置不当的区域")
    print()
    print("💡 使用建议:")
    print("   • 重点关注进度条、按钮、卡片等区域的间距")
    print("   • 查看 ContentsMargins 和 Spacing 的值")
    print("   • 对比不同区域的设置找出问题")
    print()
    
    from auto_tag.gui import launch_gui
    
    try:
        launch_gui()
    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("开始分析布局...")
        print("=" * 80)
        
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                if widget.isVisible():
                    print(f"\n📦 分析窗口：{widget.windowTitle()}")
                    print("=" * 80)
                    
                    layout = widget.layout()
                    if layout:
                        analyze_layout(layout, widget.windowTitle() or "MainWindow")
                    else:
                        print("  ⚠️  窗口没有主布局")
        else:
            print("❌ 未找到 QApplication 实例")


if __name__ == '__main__':
    main()
