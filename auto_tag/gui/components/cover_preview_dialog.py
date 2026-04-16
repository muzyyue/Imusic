# -*- coding: utf-8 -*-
"""
封面预览对话框模块

该模块提供封面图片的放大预览功能，支持平滑动画效果、
键盘/鼠标交互和响应式设计。

@module cover_preview_dialog
@version 1.0.0
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    QSize,
    QPoint,
    Property,
)
from PySide6.QtGui import QPixmap, QCursor, QPainter, QColor, QBrush, QPen
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QGraphicsDropShadowEffect,
    QApplication,
)


class CoverPreviewDialog(QWidget):
    """
    封面图片放大预览对话框

    提供全屏半透明遮罩层上的高分辨率封面预览功能，
    支持淡入淡出动画、缩放动画和多种关闭方式。

    Attributes:
        _pixmap (QPixmap | None): 当前显示的图片
        _animation (QPropertyAnimation | None): 当前运行的动画
        _overlay (QWidget | None): 遮罩层组件
        _image_label (QLabel | None): 图片显示标签

    Example:
        >>> dialog = CoverPreviewDialog(parent)
        >>> dialog.show_preview(cover_data_bytes)
        >>> # 用户点击外部或按 ESC 后自动关闭
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        初始化预览对话框

        Args:
            parent (QWidget | None): 父窗口组件，用于定位和样式继承
        """
        super().__init__(parent)

        # 设置窗口属性：无边框、置顶、透明背景
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # 状态变量
        self._pixmap: Optional[QPixmap] = None
        self._animation: Optional[QPropertyAnimation] = None
        self._current_opacity: float = 0.0
        self._scale_factor_value: float = 0.9

        # 构建 UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        构建预览对话框 UI 布局

        创建全屏遮罩层和居中的图片显示区域。
        """
        # 主布局（占满整个屏幕）
        from PySide6.QtWidgets import QVBoxLayout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 遮罩层（捕获点击事件）
        self._overlay = QWidget()
        self._overlay.setObjectName("preview_overlay")
        self._overlay.setStyleSheet("""
            QWidget#preview_overlay {
                background-color: rgba(0, 0, 0, 0.7);
            }
        """)
        self._overlay.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout.addWidget(self._overlay)

        # 图片显示标签
        self._image_label = QLabel(self._overlay)
        self._image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter |
            Qt.AlignmentFlag.AlignVCenter
        )
        self._image_label.setScaledContents(False)

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 10)
        self._image_label.setGraphicsEffect(shadow)

        # 设置圆角容器
        self._image_container = QWidget(self._overlay)
        self._image_container.setObjectName("image_container")
        self._image_container.setStyleSheet("""
            QWidget#image_container {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        container_layout = QVBoxLayout(self._image_container)
        container_layout.setContentsMargins(4, 4, 4, 4)
        container_layout.addWidget(self._image_label)

    def show_preview(self, image_data: bytes) -> None:
        """
        显示封面预览

        加载并显示高分辨率封面图片，带淡入和缩放动画效果。

        Args:
            image_data (bytes): 封面图片的二进制数据
        """
        if not image_data:
            return

        # 加载图片
        from PySide6.QtGui import QImage
        image = QImage()
        image.loadFromData(image_data)

        if image.isNull():
            return

        self._pixmap = QPixmap.fromImage(image)

        # 计算预览窗口大小（基于屏幕尺寸）
        screen_geometry = QApplication.primaryScreen().geometry()
        max_size = min(
            screen_geometry.width() * 0.8,
            screen_geometry.height() * 0.8,
            800  # 最大限制
        )
        min_size = 400  # 最小限制

        # 保持宽高比计算实际显示尺寸
        pixmap_size = self._pixmap.size()
        aspect_ratio = pixmap_size.width() / pixmap_size.height()

        if aspect_ratio > 1:  # 横图
            display_width = max(min_size, min(max_size, max_size))
            display_width = int(display_width)
            display_height = int(display_width / aspect_ratio)
            if display_height > max_size:
                display_height = int(max_size)
                display_width = int(display_height * aspect_ratio)
        else:  # 竖图或正方形
            display_height = max(min_size, min(max_size, max_size))
            display_height = int(display_height)
            display_width = int(display_height * aspect_ratio)
            if display_width > max_size:
                display_width = int(max_size)
                display_height = int(display_width / aspect_ratio)

        # 设置图片和容器大小
        scaled_pixmap = self._pixmap.scaled(
            QSize(display_width, display_height),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._image_label.setPixmap(scaled_pixmap)
        self._image_container.setFixedSize(
            display_width + 8,
            display_height + 8
        )

        # 设置遮罩层为全屏
        screen_rect = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_rect)
        self._overlay.setGeometry(self.rect())

        # 居中图片容器
        container_x = (screen_rect.width() - self._image_container.width()) // 2
        container_y = (screen_rect.height() - self._image_container.height()) // 2
        self._image_container.move(container_x, container_y)

        # 重置动画状态
        self._current_opacity = 0.0
        self._scale_factor_value = 0.9

        # 应用初始状态
        self._apply_opacity(0.0)
        self._apply_scale(0.9, container_x, container_y)

        # 显示窗口
        self.show()
        self.raise_()
        self.activateWindow()

        # 播放入场动画
        self._play_enter_animation(container_x, container_y)

    def _play_enter_animation(self, center_x: int, center_y: int) -> None:
        """
        播放入场动画

        同时执行淡入和缩放动画，创造流畅的视觉效果。

        Args:
            center_x (int): 图片容器的水平中心位置
            center_y (int): 图片容器的垂直中心位置
        """
        from PySide6.QtCore import QParallelAnimationGroup
        
        animation_group = QParallelAnimationGroup(self)

        # 淡入动画
        opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        opacity_animation.setDuration(250)
        opacity_animation.setStartValue(0.0)
        opacity_animation.setEndValue(1.0)
        opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation_group.addAnimation(opacity_animation)

        # 缩放动画（使用自定义属性）
        scale_animation = QPropertyAnimation(self, b"scale_factor")
        scale_animation.setDuration(250)
        scale_animation.setStartValue(0.9)
        scale_animation.setEndValue(1.0)
        scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 连接缩放动画的值变化来更新界面
        scale_animation.valueChanged.connect(
            lambda value: self._on_scale_changed(value, center_x, center_y)
        )
        animation_group.addAnimation(scale_animation)

        self._animation = animation_group
        animation_group.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _play_exit_animation(self) -> None:
        """
        播放退场动画

        执行淡出和缩小动画，完成后关闭窗口。
        """
        try:
            if self._animation and self._animation.state() == QPropertyAnimation.State.Running:
                return
        except RuntimeError:
            self._animation = None

        if self._animation is None:
            self._do_close()
            return

        # 获取当前位置
        geometry = self._image_container.geometry()
        center_x = geometry.x()
        center_y = geometry.y()

        # 并行动画组
        from PySide6.QtCore import QParallelAnimationGroup

        animation_group = QParallelAnimationGroup(self)

        # 淡出动画
        opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        opacity_animation.setDuration(200)
        opacity_animation.setStartValue(1.0)
        opacity_animation.setEndValue(0.0)
        opacity_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        animation_group.addAnimation(opacity_animation)

        # 缩小动画
        scale_animation = QPropertyAnimation(self, b"scale_factor")
        scale_animation.setDuration(200)
        scale_animation.setStartValue(1.0)
        scale_animation.setEndValue(0.9)
        scale_animation.setEasingCurve(QEasingCurve.Type.InCubic)

        # 连接缩放动画的值变化来更新界面
        scale_animation.valueChanged.connect(
            lambda value: self._on_scale_changed(value, center_x, center_y)
        )
        animation_group.addAnimation(scale_animation)

        # 动画完成后关闭
        animation_group.finished.connect(self._do_close)

        self._animation = animation_group
        animation_group.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _do_close(self) -> None:
        """
        执行关闭操作

        安全地关闭窗口并清理资源。
        """
        self._animation = None
        self.close()

    def _on_scale_changed(self, value: float, center_x: int, center_y: int) -> None:
        """
        缩放值变化回调

        当缩放动画的值变化时更新图片容器大小。

        Args:
            value (float): 新的缩放值
            center_x (int): 缩放中心的 X 坐标
            center_y (int): 缩放中心的 Y 坐标
        """
        self._apply_scale(value, center_x, center_y)

    def _on_animation_updated(self, center_x: int, center_y: int) -> None:
        """
        动画帧更新回调（保留兼容性）

        根据当前动画值更新界面显示效果。

        Args:
            center_x (int): 图片容器的水平中心位置
            center_y (int): 图片容器的垂直中心位置
        """
        self._apply_scale(self._scale_factor_value, center_x, center_y)

    def _apply_opacity(self, opacity: float) -> None:
        """
        应用透明度

        Args:
            opacity (float): 透明度值（0.0-1.0）
        """
        self._current_opacity = opacity
        self.setWindowOpacity(opacity)

    def _apply_scale(self, scale: float, center_x: int, center_y: int) -> None:
        """
        应用缩放变换

        以图片容器中心为原点进行缩放。

        Args:
            scale (float): 缩放比例（0.0-1.0+）
            center_x (int): 缩放中心的 X 坐标
            center_y (int): 缩放中心的 Y 坐标
        """
        self._scale_factor_value = scale

        original_size = self._image_container.size()
        new_width = int(original_size.width() * scale)
        new_height = int(original_size.height() * scale)

        new_x = center_x + (original_size.width() - new_width) // 2
        new_y = center_y + (original_size.height() - new_height) // 2

        self._image_container.setGeometry(new_x, new_y, new_width, new_height)

    def mousePressEvent(self, event) -> None:
        """
        鼠标点击事件处理

        点击遮罩层（图片外部区域）时触发关闭动画。

        Args:
            event (QMouseEvent): 鼠标事件对象
        """
        # 只响应左键点击
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击在图片容器外
            if not self._image_container.geometry().contains(event.pos()):
                try:
                    self._play_exit_animation()
                except RuntimeError:
                    self._do_close()

        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        """
        键盘按键事件处理

        按 ESC 键时触发关闭动画。

        Args:
            event (QKeyEvent): 键盘事件对象
        """
        if event.key() == Qt.Key.Key_Escape:
            self._play_exit_animation()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event) -> None:
        """
        绘制事件处理

        自定义绘制半透明背景。
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制半透明背景
        background_color = QColor(0, 0, 0, int(180 * self._current_opacity))
        painter.fillRect(self.rect(), QBrush(background_color))

        super().paintEvent(event)

    def closeEvent(self, event) -> None:
        """
        关闭事件处理

        清理资源并接受关闭事件。
        """
        # 停止正在运行的动画
        try:
            if self._animation and self._animation.state() == QPropertyAnimation.State.Running:
                self._animation.stop()
        except RuntimeError:
            pass

        # 释放资源
        self._animation = None
        self._pixmap = None

        super().closeEvent(event)

    def get_scale_factor(self) -> float:
        """
        获取当前缩放因子

        Returns:
            float: 当前缩放值
        """
        return self._scale_factor_value

    def set_scale_factor(self, scale: float) -> None:
        """
        设置缩放因子

        Args:
            scale (float): 新的缩放值
        """
        self._scale_factor_value = scale

    # 定义 Qt 属性，供 QPropertyAnimation 使用
    scale_factor = Property(float, get_scale_factor, set_scale_factor)
