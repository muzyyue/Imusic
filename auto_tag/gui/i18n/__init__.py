# -*- coding: utf-8 -*-
"""
auto_tag.gui.i18n 模块

提供国际化（i18n）支持，包括多语言翻译功能。

导出组件：
- translator: 全局翻译器单例
- tr: 便捷翻译函数
- Translator: 翻译器类

使用示例：
    from auto_tag.gui.i18n import tr, translator

    # 使用便捷函数
    text = tr('app_title')

    # 切换语言
    translator.load_language('zh')
    text = tr('app_title')  # 返回中文翻译
"""

from .translator import Translator, translator, tr

__all__ = ['Translator', 'translator', 'tr']
