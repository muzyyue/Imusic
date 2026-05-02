# -*- coding: utf-8 -*-
"""
Qt UI 调试工具 - 专门针对编辑器页面的布局分析
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import QTimer, QObject

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def dump_layout_hierarchy(layout, prefix="", max_depth=8):
    """递归输出布局层次结构，包含间距、边距和子组件信息"""
    if not layout or max_depth <= 0:
        return
    
    layout_type = layout.__class__.__name__
    spacing = layout.spacing()
    margins = layout.contentsMargins()
    
    print(f"{prefix}Layout: {layout_type}")
    print(f"{prefix}  spacing={spacing}px")
    print(f"{prefix}  margins: top={margins.top()}, bottom={margins.bottom()}, left={margins.left()}, right={margins.right()}")
    
    # 遍历子元素
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item:
            child_widget = item.widget()
            child_layout = item.layout()
            spacer = item.spacerItem()
            
            if child_widget:
                widget_info = f"{child_widget.__class__.__name__}"
                if hasattr(child_widget, 'objectName') and child_widget.objectName():
                    widget_info += f" (name='{child_widget.objectName()}')"
                if hasattr(child_widget, 'text') and hasattr(child_widget.text, '__call__'):
                    text = child_widget.text()
                    if text:
                        widget_info += f" text='{text[:30]}'"
                if hasattr(child_widget, 'minimumHeight'):
                    widget_info += f" minHeight={child_widget.minimumHeight()}"
                if hasattr(child_widget, 'height'):
                    widget_info += f" height={child_widget.height()}"
                if hasattr(child_widget, 'minimumSizeHint'):
                    hint = child_widget.minimumSizeHint()
                    widget_info += f" minSizeHint={hint.width()}x{hint.height()}"
                print(f"{prefix}  [{i}] Widget: {widget_info}")
                
                if child_widget.layout():
                    dump_layout_hierarchy(child_widget.layout(), prefix + "    ", max_depth - 1)
            
            elif child_layout:
                print(f"{prefix}  [{i}] SubLayout:")
                dump_layout_hierarchy(child_layout, prefix + "    ", max_depth - 1)
            
            elif spacer:
                size = spacer.sizeHint()
                print(f"{prefix}  [{i}] Spacer: {size.width()}x{size.height()}")


def analyze_editor_page(page):
    """分析编辑器页面的所有卡片布局"""
    print("\n" + "=" * 80)
    print("EDITOR PAGE LAYOUT ANALYSIS")
    print("=" * 80)
    
    content_widget = None
    if hasattr(page, 'content_widget'):
        content_widget = page.content_widget
    
    if not content_widget:
        print("ERROR: content_widget not found")
        return
    
    print(f"\ncontent_widget: {content_widget.__class__.__name__}")
    if hasattr(content_widget, 'layout'):
        content_layout = content_widget.layout()
        if content_layout:
            print(f"   Layout type: {content_layout.__class__.__name__}")
            print(f"   spacing: {content_layout.spacing()}")
            cm = content_layout.contentsMargins()
            print(f"   margins: top={cm.top()}, bottom={cm.bottom()}, left={cm.left()}, right={cm.right()}")
    
    print(f"\n{'='*60}")
    print("Analyzing child widgets (cards) in content_layout")
    print("=" * 60)
    
    if hasattr(content_widget, 'layout'):
        content_layout = content_widget.layout()
        if content_layout:
            for i in range(content_layout.count()):
                item = content_layout.itemAt(i)
                if item:
                    child_widget = item.widget()
                    child_layout = item.layout()
                    spacer = item.spacerItem()
                    
                    if child_widget:
                        widget_type = child_widget.__class__.__name__
                        print(f"\n--- [{i}] {widget_type} ---")
                        
                        if hasattr(child_widget, 'minimumHeight'):
                            print(f"    minHeight={child_widget.minimumHeight()}")
                        if hasattr(child_widget, 'height'):
                            print(f"    height={child_widget.height()}")
                        
                        if child_widget.layout():
                            sub_layout = child_widget.layout()
                            if sub_layout.count() > 0:
                                first_item = sub_layout.itemAt(0)
                                if first_item and first_item.widget():
                                    first_widget = first_item.widget()
                                    if hasattr(first_widget, 'text'):
                                        title = first_widget.text()
                                        if title:
                                            print(f"    Title: {title}")
                        
                        dump_layout_hierarchy(child_widget.layout(), prefix="    ")
                    
                    elif spacer:
                        size = spacer.sizeHint()
                        print(f"\n--- [{i}] Spacer --- size: {size.width()}x{size.height()}")
    
    # 检查具体的 ComboBox
    print(f"\n{'='*60}")
    print("ComboBox Component Details")
    print("=" * 60)
    
    for attr_name in ['preset_combo', 'quality_combo']:
        combo = getattr(page, attr_name, None)
        if combo:
            print(f"\n>>> {attr_name}:")
            print(f"  Class: {combo.__class__.__name__}")
            print(f"  height: {combo.height()}px")
            print(f"  minimumHeight: {combo.minimumHeight()}px")
            hint = combo.minimumSizeHint()
            print(f"  minimumSizeHint: {hint.width()}x{hint.height()}")
            print(f"  sizePolicy: H={combo.sizePolicy().horizontalPolicy()}, V={combo.sizePolicy().verticalPolicy()}")


def main():
    """主函数：启动编辑器页面并分析布局"""
    print("=" * 80)
    print("Qt UI Debug Tool - Editor Page Layout Analysis")
    print("=" * 80)
    
    app = QApplication(sys.argv)
    
    from auto_tag.gui.pages.editor_page import EditorPage
    
    print("\n[DEBUG] Creating EditorPage...")
    page = EditorPage()
    
    # 设置窗口大小以便布局计算
    page.resize(900, 700)
    page.show()
    
    def on_layout_ready():
        """布局完成后进行分析"""
        print("\n" + "=" * 40)
        print("Starting layout analysis...")
        print("=" * 40)
        
        analyze_editor_page(page)
        
        print("\n" + "=" * 40)
        print("Analysis complete!")
        print("=" * 40)
        
        # 分析完成后退出
        QTimer.singleShot(500, app.quit)
    
    # 等待布局完成
    QTimer.singleShot(200, on_layout_ready)
    
    app.exec()


if __name__ == '__main__':
    main()
