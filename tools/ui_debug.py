# -*- coding: utf-8 -*-
"""
Qt UI 调试工具 - 查看 UI 层级结构

这个脚本会启动你的应用程序，并输出完整的 UI 组件树，
帮助你分析布局问题和组件层级关系。
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import QObject


def dump_widget_tree(widget, indent=0, max_depth=10):
    """
    递归输出 Widget 树结构
    
    Args:
        widget: Qt Widget 对象
        indent: 当前缩进级别
        max_depth: 最大递归深度
    """
    if indent > max_depth:
        return
    
    # 获取组件信息
    widget_name = widget.__class__.__name__
    object_name = widget.objectName() or "无对象名"
    
    # 获取布局信息
    layout_info = ""
    layout = widget.layout()
    if layout:
        layout_name = layout.__class__.__name__
        layout_info = f" [布局：{layout_name}]"
    
    # 获取尺寸信息
    size_info = f" ({widget.width()}x{widget.height()})"
    
    # 输出当前组件
    prefix = "│   " * indent + "├─ " if indent > 0 else ""
    print(f"{prefix}{widget_name} - {object_name}{size_info}{layout_info}")
    
    # 递归输出子组件
    for child in widget.children():
        if isinstance(child, QWidget):
            dump_widget_tree(child, indent + 1, max_depth)


def dump_all_widgets():
    """
    输出所有顶级窗口的组件树
    """
    app = QApplication.instance()
    if not app:
        print("❌ 没有运行中的 QApplication 实例")
        return
    
    print("\n" + "=" * 80)
    print("Qt UI 组件树")
    print("=" * 80)
    
    for widget in app.topLevelWidgets():
        print(f"\n📦 顶级窗口：{widget.windowTitle()}")
        print("-" * 80)
        dump_widget_tree(widget)
        print()


def analyze_layout_spacing(widget, target_name=""):
    """
    分析特定组件的布局间距
    
    Args:
        widget: 要分析的 Widget
        target_name: 目标组件名称（可选，为空则分析所有）
    """
    layout = widget.layout()
    if not layout:
        return
    
    print(f"\n 布局分析：{widget.objectName()}")
    print(f"   类型：{layout.__class__.__name__}")
    print(f"   间距 (Spacing): {layout.spacing()}px")
    
    margins = layout.contentsMargins()
    print(f"   边距 (Margins):")
    print(f"      上：{margins.top()}px")
    print(f"      下：{margins.bottom()}px")
    print(f"      左：{margins.left()}px")
    print(f"      右：{margins.right()}px")
    
    # 递归分析子布局
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item:
            child_widget = item.widget()
            if child_widget:
                if not target_name or target_name.lower() in child_widget.objectName().lower():
                    analyze_layout_spacing(child_widget, target_name)


def find_widget_by_name(widget, name):
    """
    根据名称查找 Widget
    
    Args:
        widget: 起始 Widget
        name: 要查找的名称
        
    Returns:
        找到的 Widget 或 None
    """
    if name.lower() in widget.objectName().lower():
        return widget
    
    for child in widget.children():
        if isinstance(child, QWidget):
            result = find_widget_by_name(child, name)
            if result:
                return result
    
    return None


def main():
    """
    主函数：启动应用并分析 UI
    """
    print("=" * 80)
    print("Qt UI 调试工具")
    print("=" * 80)
    print()
    
    # 导入主程序
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    from auto_tag.gui import launch_gui
    
    print("🚀 启动应用程序...")
    print("💡 提示：程序启动后，按 Ctrl+C 停止并查看 UI 分析")
    print()
    
    try:
        # 启动 GUI
        launch_gui()
    except KeyboardInterrupt:
        print("\n\n⏹ 检测到 Ctrl+C，开始分析 UI...")
        dump_all_widgets()


if __name__ == '__main__':
    main()
