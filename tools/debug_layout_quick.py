# -*- coding: utf-8 -*-
"""
布局调试输出工具

在程序启动时自动输出所有布局的详细信息，
无需等待 Ctrl+C，直接查看间距设置。
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def print_layout_info(layout, indent=0, path=""):
    """
    递归打印布局信息
    
    Args:
        layout: QLayout 对象
        indent: 缩进级别
        path: 路径
    """
    if not layout:
        return
    
    spacing = layout.spacing()
    margins = layout.contentsMargins()
    layout_name = layout.__class__.__name__
    prefix = "│   " * indent + "├─ " if indent > 0 else ""
    
    print(f"{prefix}{layout_name}")
    print(f"{prefix}   Spacing: {spacing}px")
    print(f"{prefix}   Margins: 上={margins.top()} 下={margins.bottom()} 左={margins.left()} 右={margins.right()}")
    
    # 遍历子项
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item:
            widget = item.widget()
            if widget:
                widget_name = widget.__class__.__name__
                object_name = widget.objectName() or ""
                print(f"{prefix}   [{i}] {widget_name} - {object_name}")
                
                # 递归子布局
                child_layout = widget.layout()
                if child_layout:
                    print_layout_info(child_layout, indent + 1, f"{path}/{object_name}")
            else:
                child_layout = item.layout()
                if child_layout:
                    print_layout_info(child_layout, indent + 1, f"{path}/[{i}]")


def debug_converter_page_layout():
    """
    调试转换页面的布局
    """
    print("=" * 80)
    print("调试转换器页面布局")
    print("=" * 80)
    print()
    
    # 导入并创建页面
    from auto_tag.gui.pages.converter_page import ConverterPage
    from PySide6.QtWidgets import QApplication
    
    # 创建应用（必需）
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    
    # 创建页面实例
    page = ConverterPage()
    
    # 输出布局信息
    layout = page.layout()
    if layout:
        print("📦 转换器页面主布局:")
        print_layout_info(layout)
    else:
        print("❌ 页面没有布局")
    
    # 保持应用运行以便查看
    print("\n💡 提示：查看上面的布局信息，特别关注:")
    print("   • 进度区域的 Margins 设置")
    print("   • 自定义格式卡片的 Spacing")
    print("   • 各区域之间的间距")
    
    # 清理
    page.deleteLater()


if __name__ == '__main__':
    debug_converter_page_layout()
