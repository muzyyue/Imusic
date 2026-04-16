# -*- coding: utf-8 -*-
"""
封面预览对话框测试模块

测试 CoverPreviewDialog 类的功能，包括动画、事件处理和响应式布局。

@module test_cover_preview_dialog
@version 1.0.0
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage


@pytest.fixture(scope="module")
def qapp():
    """
    创建 QApplication 实例

    Qt 组件测试需要 QApplication 实例。
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def sample_image_data():
    """
    生成示例图片数据

    Returns:
        bytes: 一个简单的红色 100x100 PNG 图片的二进制数据
    """
    from PySide6.QtCore import QBuffer
    
    image = QImage(100, 100, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.red)
    
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return buffer.data().data()


class TestCoverPreviewDialog:
    """
    封面预览对话框测试类

    测试 CoverPreviewDialog 的各项功能。
    """

    def test_init(self, qapp):
        """
        测试预览对话框初始化

        验证对话框能够正确创建且属性初始化正确。
        """
        from auto_tag.gui.components import CoverPreviewDialog
        
        dialog = CoverPreviewDialog()
        
        # 验证基本属性
        assert dialog is not None
        assert dialog._pixmap is None
        assert dialog._animation is None
        assert dialog._current_opacity == 0.0
        assert dialog._scale_factor_value == 0.9

    def test_window_flags(self, qapp):
        """
        测试窗口标志设置

        验证窗口具有正确的无边框、置顶等属性。
        """
        from auto_tag.gui.components import CoverPreviewDialog
        
        dialog = CoverPreviewDialog()
        flags = dialog.windowFlags()
        
        # 检查是否设置了必要的窗口标志
        assert flags & Qt.WindowType.FramelessWindowHint
        assert flags & Qt.WindowType.WindowStaysOnTopHint

    def test_show_preview_with_valid_data(self, qapp, sample_image_data):
        """
        测试显示有效图片数据

        验证传入有效图片数据时能正确加载并显示。
        """
        from auto_tag.gui.components import CoverPreviewDialog
        
        dialog = CoverPreviewDialog()
        dialog.show_preview(sample_image_data)
        
        # 验证图片已加载
        assert dialog._pixmap is not None
        assert not dialog._pixmap.isNull()

    def test_show_preview_with_invalid_data(self, qapp):
        """
        测试显示无效图片数据

        验证传入无效数据时不会崩溃，且不显示图片。
        """
        from auto_tag.gui.components import CoverPreviewDialog
        
        dialog = CoverPreviewDialog()
        
        # 传入无效的图片数据（不是有效的图片格式）
        invalid_data = b"this is not an image"
        dialog.show_preview(invalid_data)
        
        # 验证没有加载图片
        assert dialog._pixmap is None

    def test_show_preview_with_empty_data(self, qapp):
        """
        测试显示空数据

        验证传入空数据时不会崩溃。
        """
        from auto_tag.gui.components import CoverPreviewDialog
        
        dialog = CoverPreviewDialog()
        dialog.show_preview(b"")
        
        # 验证没有加载图片
        assert dialog._pixmap is None

    def test_scale_factor_property(self, qapp):
        """
        测试缩放因子属性

        验证缩放因子的 getter 和 setter 工作正常。
        """
        from auto_tag.gui.components import CoverPreviewDialog
        
        dialog = CoverPreviewDialog()
        
        # 测试初始值
        assert dialog.get_scale_factor() == 0.9
        
        # 测试设置新值
        dialog.set_scale_factor(1.0)
        assert dialog.get_scale_factor() == 1.0
        
        # 测试通过 property 访问
        dialog._scale_factor = 1.2
        assert dialog._scale_factor == 1.2

    def test_responsive_size_calculation(self, qapp, sample_image_data):
        """
        测试响应式尺寸计算

        验证不同屏幕尺寸下预览窗口大小自适应正确。
        """
        from auto_tag.gui.components import CoverPreviewDialog
        from PySide6.QtWidgets import QApplication
        
        dialog = CoverPreviewDialog()
        dialog.show_preview(sample_image_data)
        
        # 获取屏幕尺寸
        screen_geometry = QApplication.primaryScreen().geometry()
        max_expected_size = min(
            screen_geometry.width() * 0.8,
            screen_geometry.height() * 0.8,
            800
        )
        
        # 验证容器大小在合理范围内
        container_size = dialog._image_container.size()
        assert container_size.width() <= max_expected_size + 8  # +8 for padding
        assert container_size.height() <= max_expected_size + 8
        assert container_size.width() >= 400  # 最小尺寸
        assert container_size.height() >= 400

    def test_close_event_cleanup(self, qapp, sample_image_data):
        """
        测试关闭事件清理资源

        验证关闭对话框时会释放图片资源。
        """
        from auto_tag.gui.components import CoverPreviewDialog
        
        dialog = CoverPreviewDialog()
        dialog.show_preview(sample_image_data)
        
        # 确认图片已加载
        assert dialog._pixmap is not None
        
        # 模拟关闭
        dialog.close()
        
        # 验证资源已释放
        assert dialog._pixmap is None


class TestCoverIntegration:
    """
    封面预览集成测试类

    测试预览功能与 MusicManagerPage 的集成。
    """

    def test_cover_click_opens_preview(self, qapp, sample_image_data):
        """
        测试点击封面打开预览

        验证点击封面图片时能触发预览对话框显示。
        """
        from auto_tag.gui.pages import MusicManagerPage
        from unittest.mock import Mock, patch
        
        page = MusicManagerPage()
        
        # 设置封面数据
        page._current_cover_data = sample_image_data
        
        # 模拟鼠标点击事件
        mock_event = Mock()
        mock_event.button.return_value = Qt.MouseButton.LeftButton
        
        # 调用点击处理方法
        page._on_cover_clicked(mock_event)
        
        # 验证预览对话框已创建
        assert page._preview_dialog is not None

    def test_cover_click_without_data(self, qapp):
        """
        测试无封面数据时不打开预览

        验证当没有封面数据时点击封面不会打开预览。
        """
        from auto_tag.gui.pages import MusicManagerPage
        from unittest.mock import Mock
        
        page = MusicManagerPage()
        
        # 不设置封面数据
        page._current_cover_data = None
        
        # 模拟鼠标点击事件
        mock_event = Mock()
        mock_event.button.return_value = Qt.MouseButton.LeftButton
        
        # 调用点击处理方法
        page._on_cover_clicked(mock_event)
        
        # 验证预览对话框未创建
        assert page._preview_dialog is None

    def test_right_click_ignored(self, qapp, sample_image_data):
        """
        测试右键点击被忽略

        验证右键点击封面不会触发预览。
        """
        from auto_tag.gui.pages import MusicManagerPage
        from unittest.mock import Mock
        
        page = MusicManagerPage()
        page._current_cover_data = sample_image_data
        
        # 模拟右键点击事件
        mock_event = Mock()
        mock_event.button.return_value = Qt.MouseButton.RightButton
        
        # 调用点击处理方法
        page._on_cover_clicked(mock_event)
        
        # 验证预览对话框未创建
        assert page._preview_dialog is None

    def test_display_cover_caches_data(self, qapp, sample_image_data):
        """
        测试显示封面时缓存数据

        验证 _display_cover 方法会缓存原始图片数据用于预览。
        """
        from auto_tag.gui.pages import MusicManagerPage
        
        page = MusicManagerPage()
        
        # 初始状态无数据
        assert page._current_cover_data is None
        
        # 显示封面
        page._display_cover(sample_image_data)
        
        # 验证数据已被缓存
        assert page._current_cover_data is not None
        assert page._current_cover_data == sample_image_data

    def test_set_default_cover_clears_cache(self, qapp):
        """
        测试设置默认封面清除缓存

        验证设置默认封面时会清空缓存数据。
        """
        from auto_tag.gui.pages import MusicManagerPage
        
        page = MusicManagerPage()
        
        # 先设置一些假数据
        page._current_cover_data = b"fake data"
        
        # 设置默认封面
        page._set_default_cover()
        
        # 验证缓存已清空
        assert page._current_cover_data is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
