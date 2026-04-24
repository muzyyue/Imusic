# -*- coding: utf-8 -*-
"""
Qt Inspector 启动脚本

使用 PySide6 自带的 Qt Designer 作为 Inspector 调试器，
可以实时查看 UI 组件的层级结构、布局、样式等信息。
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QProcess

def start_qt_inspector():
    """
    启动 Qt Inspector (Qt Designer)
    
    Qt Designer 不仅可以设计界面，还可以作为 Inspector 使用：
    1. 打开已运行的应用程序
    2. 查看组件层级树
    3. 检查布局约束
    4. 查看样式表
    """
    
    # 获取 PySide6 安装路径
    import PySide6
    pyside6_path = os.path.dirname(PySide6.__file__)
    designer_path = os.path.join(pyside6_path, "Designer.exe")
    
    if not os.path.exists(designer_path):
        print(f"❌ 未找到 Qt Designer: {designer_path}")
        print("\n💡 解决方案:")
        print("   1. 使用 pip 安装完整 PySide6:")
        print("      pip install PySide6 --upgrade")
        print("\n   2. 或者使用在线 Inspector 工具:")
        print("      - Qt Inspector (需要 Qt 商业版)")
        print("      - 或使用 PySide6 的调试模式")
        return
    
    print(f"✓ 启动 Qt Designer: {designer_path}")
    print("\n💡 使用技巧:")
    print("   1. 文件 → 打开 → 选择你的应用程序")
    print("   2. 在对象查看器中查看组件层级")
    print("   3. 在属性编辑器中查看组件属性")
    print("   4. 使用布局工具检查间距和约束")
    
    # 启动 Designer
    os.startfile(designer_path)

def enable_qt_debug_mode():
    """
    启用 Qt 调试模式
    
    设置环境变量，让 Qt 输出详细的调试信息
    """
    os.environ['QT_DEBUG_PLUGINS'] = '1'
    os.environ['QT_LOGGING_RULES'] = 'qt.qpa.*=true'
    
    print("✓ Qt 调试模式已启用")
    print("\n💡 调试信息将输出到控制台")

if __name__ == '__main__':
    print("=" * 60)
    print("Qt Inspector 启动工具")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--debug':
        enable_qt_debug_mode()
    else:
        start_qt_inspector()
