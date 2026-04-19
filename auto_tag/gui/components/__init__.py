# -*- coding: utf-8 -*-
"""
GUI 组件模块

提供可复用的 UI 组件，包括对话框、预览窗口等。
"""

from auto_tag.gui.components.cover_preview_dialog import CoverPreviewDialog
from auto_tag.gui.components.song_search_dialog import SongSearchResultDialog
from auto_tag.gui.components.song_result_card import SongResultCard, PlatformResultWidget

__all__ = ['CoverPreviewDialog', 'SongSearchResultDialog', 'SongResultCard', 'PlatformResultWidget']
