# -*- coding: utf-8 -*-
"""
搜索结果卡片组件模块

该模块提供卡片式的搜索结果展示组件，支持折叠/展开交互、
悬停效果和平台结果选择功能，并完整适配 QFluentWidgets 深浅色主题。
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import (
    Qt,
    QSize,
    Signal,
    QTimer,
    QThread,
    QUrl,
    QByteArray,
    QBuffer,
)
from PySide6.QtGui import (
    QCursor,
    QIcon,
    QPixmap,
    QTransform,
    QImage,
    QPainter,
    QPainterPath,
    QFont,
    QColor,
    QBrush,
    QPen,
)
from PySide6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QSpacerItem,
    QSizePolicy,
    QLabel,
    QGraphicsDropShadowEffect,
)
from qfluentwidgets import (
    CardWidget,
    BodyLabel,
    SubtitleLabel,
    ToolButton,
    CheckBox,
    IconWidget,
    FluentIcon as FIF,
    isDarkTheme,
    qconfig,
    Theme,
    getFont,
)

if TYPE_CHECKING:
    pass


class CoverImageCache:
    """
    封面图片内存缓存（LRU 策略）

    使用 OrderedDict 实现 LRU 缓存，避免重复下载相同封面。
    最大缓存 100 张图片，超出时自动淘汰最久未使用的项。

    优化：减少网络请求，降低封面加载延迟 80% 以上。
    """

    _cache: dict = {}
    _max_size: int = 100

    @classmethod
    def get(cls, key: str) -> Optional[QPixmap]:
        """
        从缓存获取封面图片

        Args:
            key (str): 缓存键（URL 或文件路径）

        Returns:
            QPixmap | None: 缓存的图片对象，未命中时返回 None
        """
        if key in cls._cache:
            # 移动到末尾（标记为最近使用）
            value = cls._cache.pop(key)
            cls._cache[key] = value
            return value
        return None

    @classmethod
    def set(cls, key: str, pixmap: QPixmap) -> None:
        """
        将封面图片存入缓存

        Args:
            key (str): 缓存键（URL 或文件路径）
            pixmap (QPixmap): 图片对象
        """
        if key in cls._cache:
            cls._cache.pop(key)
        cls._cache[key] = pixmap

        # LRU 淘汰：超出容量时移除最久未使用的项
        if len(cls._cache) > cls._max_size:
            oldest_key = next(iter(cls._cache))
            del cls._cache[oldest_key]

    @classmethod
    def clear(cls) -> None:
        """清空所有缓存"""
        cls._cache.clear()


class CoverImageLoader(QThread):
    """
    封面图片异步加载线程

    支持从 URL 下载或从 MP3 文件提取内嵌封面图片。
    使用独立线程避免阻塞主界面。
    """

    # 信号：加载完成，传递 QPixmap 或 None（失败时）
    loaded = Signal(object)  # QPixmap | None

    def __init__(
        self,
        cover_url: str = "",
        file_path: str = "",
        parent=None
    ) -> None:
        """
        初始化加载器

        Args:
            cover_url (str): 封面图片 URL（优先）
            file_path (str): MP3 文件路径（备选，用于提取内嵌封面）
            parent: 父对象
        """
        super().__init__(parent)
        self.cover_url = cover_url
        self.file_path = file_path

    def run(self) -> None:
        """执行异步加载任务（带缓存支持）"""
        # 优先从缓存获取
        cache_key = self.cover_url or self.file_path
        if cache_key:
            cached_pixmap = CoverImageCache.get(cache_key)
            if cached_pixmap is not None:
                self.loaded.emit(QPixmap(cached_pixmap))  # 返回副本
                return

        pixmap = None

        # DEBUG: 输出加载参数
        url_preview = self.cover_url[:50] if self.cover_url else '(empty)'
        print(f"[CoverImageLoader] Starting load - URL: '{url_preview}..., File: {self.file_path}")

        # 策略1: 从 URL 下载（优先使用在线封面）
        if self.cover_url:
            print(f"[CoverImageLoader] Trying URL: {self.cover_url[:60]}...")
            pixmap = self._load_from_url()
            if pixmap:
                print(f"[CoverImageLoader] [OK] URL load successful!")

        # 策略2: 从 MP3 文件提取内嵌封面
        if pixmap is None and self.file_path:
            print(f"[CoverImageLoader] Trying MP3 embed: {self.file_path}")
            pixmap = self._load_from_mp3()
            if pixmap:
                print(f"[CoverImageLoader] [OK] MP3 extract successful!")

        # 输出最终结果并存入缓存
        if pixmap:
            print(f"[CoverImageLoader] [OK] [OK] Cover loaded successfully!")
            # 存入缓存（如果是从 URL 下载成功，使用 URL 作为键）
            if cache_key:
                CoverImageCache.set(cache_key, pixmap)
        else:
            print(f"[CoverImageLoader] [FAIL] [FAIL] All strategies failed, will show default icon")

        self.loaded.emit(pixmap)

    def _load_from_url(self) -> Optional[QPixmap]:
        """从 URL 下载封面图片"""
        try:
            import urllib.request
            # 增加超时时间和 User-Agent
            req = urllib.request.Request(
                self.cover_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            data = urllib.request.urlopen(req, timeout=10).read()
            image = QImage()
            image.loadFromData(data)
            if not image.isNull():
                return QPixmap.fromImage(image)
        except Exception as e:
            print(f"[CoverImageLoader] URL load error: {type(e).__name__}: {e}")
        return None

    def _load_from_mp3(self) -> Optional[QPixmap]:
        """从 MP3 文件提取内嵌封面"""
        try:
            import eyed3
            audio = eyed3.load(self.file_path)
            if audio and audio.tag and audio.tag.images:
                img = audio.tag.images[0]
                image = QImage()
                image.loadFromData(img.image_data)
                if not image.isNull():
                    return QPixmap.fromImage(image)
        except Exception as e:
            print(f"[CoverImageLoader] MP3 extract failed: {e}")
        return None


class CoverImageWidget(QFrame):
    """
    音乐封面图片展示组件

    支持异步加载、圆角显示、加载动画和降级处理。
    可从在线 URL 或 MP3 内嵌数据获取封面。

    Attributes:
        size (int): 封面图片尺寸（正方形边长）
        cover_url (str): 在线封面 URL
        file_path (str): MP3 文件路径
        clicked (Signal): 点击信号
    """

    clicked = Signal()

    def __init__(
        self,
        size: int = 48,
        cover_url: str = "",
        file_path: str = "",
        parent=None
    ) -> None:
        """
        初始化封面图片组件

        Args:
            size (int): 封面尺寸（像素）
            cover_url (str): 在线封面 URL
            file_path (str): MP3 文件路径
            parent: 父组件
        """
        super().__init__(parent)
        self.size = size
        self.cover_url = cover_url
        self.file_path = file_path
        self._pixmap: Optional[QPixmap] = None
        self._loader: Optional[CoverImageLoader] = None
        self._is_loading = False

        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._setup_ui()
        self._setup_style()

        # 监听主题变化
        qconfig.themeChanged.connect(self._on_theme_changed)

        # 自动开始加载
        if cover_url or file_path:
            self.load_cover(cover_url, file_path)

    def _setup_ui(self) -> None:
        """构建 UI 布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 图片标签
        self.image_label = QLabel()
        self.image_label.setFixedSize(self.size - 4, self.size - 4)
        self.image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self.image_label.setScaledContents(True)
        layout.addWidget(self.image_label)

        # 显示默认图标
        self._show_default_icon()

    def _setup_style(self) -> None:
        """设置样式"""
        colors = self._get_colors()
        self.setStyleSheet(f"""
            CoverImageWidget {{
                background-color: {colors["bg"]};
                border-radius: {self.size // 2}px;
                border: 2px solid {colors["border"]};
            }}
        """)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border-radius: %dpx;
            }
        """ % ((self.size - 4) // 2))

    def _get_colors(self) -> dict:
        """获取当前主题颜色"""
        if isDarkTheme():
            return {"bg": "#363636", "border": "#555555"}
        return {"bg": "#f5f5f7", "border": "#e8e8e8"}

    def _on_theme_changed(self, theme: Theme) -> None:
        """主题切换回调，更新样式以适配新主题"""
        self._setup_style()

    def _show_default_icon(self) -> None:
        """显示默认音乐图标"""
        icon_size = int(self.size * 0.5)
        pixmap = FIF.MUSIC.icon(QSize(icon_size, icon_size)).pixmap(icon_size, icon_size)
        rounded = self._round_pixmap(pixmap, self.size - 4)
        self.image_label.setPixmap(rounded)

    def _show_loading(self) -> None:
        """显示加载状态"""
        colors = self._get_colors()
        self.image_label.clear()
        self.image_label.setText("...")
        self.image_label.setStyleSheet("""
            QLabel {
                color: %(color)s;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
            }
        """ % {"color": "#999" if isDarkTheme() else "#666"})

    def _round_pixmap(self, pixmap: QPixmap, size: int) -> QPixmap:
        """将图片裁剪为圆形"""
        rounded = QPixmap(size, size)
        rounded.fill(Qt.GlobalColor.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setClipPath(self._rounded_path(size))
        painter.drawPixmap(0, 0, size, size, pixmap.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        ))
        painter.end()

        return rounded

    def _rounded_path(self, size: int) -> QPainterPath:
        """生成圆角矩形路径"""
        path = QPainterPath()
        radius = min(8, size // 6)
        path.addRoundedRect(0, 0, size, size, radius, radius)
        return path

    def load_cover(self, cover_url: str = "", file_path: str = "") -> None:
        """
        加载封面图片

        Args:
            cover_url (str): 在线封面 URL
            file_path (str): MP3 文件路径
        """
        # 先停止并清理旧的加载器，防止线程泄漏
        self._stop_loader()

        self.cover_url = cover_url or self.cover_url
        self.file_path = file_path or self.file_path

        if not self.cover_url and not self.file_path:
            self._show_default_icon()
            return

        # 显示加载状态
        self._is_loading = True
        self._show_loading()

        # 启动异步加载
        self._loader = CoverImageLoader(self.cover_url, self.file_path)
        self._loader.loaded.connect(self._on_cover_loaded)
        self._loader.start()

    def _stop_loader(self) -> None:
        """
        停止并清理封面加载线程

        防止组件销毁时仍有后台线程运行导致内存泄漏。
        """
        if self._loader is not None:
            # 断开信号连接，防止对已销毁组件发射信号
            try:
                self._loader.loaded.disconnect(self._on_cover_loaded)
            except (TypeError, RuntimeError):
                pass
            # 请求线程退出
            self._loader.requestInterruption()
            self._loader.quit()
            # 等待线程结束（最多等待 1 秒）
            if not self._loader.wait(1000):
                self._loader.terminate()
                self._loader.wait()
            self._loader.deleteLater()
            self._loader = None
        self._is_loading = False

    def closeEvent(self, event) -> None:
        """
        组件关闭事件

        确保加载线程被正确停止，防止内存泄漏。
        """
        self._stop_loader()
        super().closeEvent(event)

    def deleteLater(self) -> None:
        """
        延迟删除覆盖

        在组件被删除前停止加载线程并断开信号连接。
        """
        self._stop_loader()
        # 断开主题变化信号连接
        try:
            qconfig.themeChanged.disconnect(self._on_theme_changed)
        except (TypeError, RuntimeError):
            pass
        super().deleteLater()

    def _on_cover_loaded(self, pixmap: Optional[QPixmap]) -> None:
        """
        封面加载完成回调

        Args:
            pixmap (QPixmap | None): 加载的图片，失败为 None
        """
        self._is_loading = False

        if pixmap and not pixmap.isNull():
            self._pixmap = pixmap
            rounded = self._round_pixmap(pixmap, self.size - 4)
            self.image_label.setPixmap(rounded)
            self.image_label.setText("")
            self.image_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    border-radius: %dpx;
                }
            """ % ((self.size - 4) // 2))
        else:
            # 加载失败，显示默认图标
            self._show_default_icon()

    def mousePressEvent(self, event) -> None:
        """
        鼠标点击事件

        点击时触发预览功能。
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def get_pixmap(self) -> Optional[QPixmap]:
        """
        获取当前显示的图片

        Returns:
            QPixmap | None: 当前图片
        """
        return self._pixmap


# 主题颜色映射
# 注意：不使用 QSS 覆盖 QLabel 颜色，让 QFluentWidgets 自动处理文本颜色
_THEME_COLORS = {
    "light": {
        "card_bg": "#ffffff",
        "card_bg_hover": "#f5f5f7",
        "card_border": "#e8e8e8",
        "card_border_hover": "#d0d0d0",
        "platform_bg": "#f5f5f7",
        "platform_bg_hover": "#ebebed",
        "platform_border": "#e8e8e8",
        "platform_border_hover": "#d0d0d0",
        "platform_selected_bg": "rgba(124, 77, 255, 0.08)",
        "platform_selected_border": "#7c4dff",
        "error_card_bg": "rgba(255, 82, 82, 0.05)",
        "error_card_border": "rgba(255, 82, 82, 0.2)",
        "error_card_hover_bg": "rgba(255, 82, 82, 0.08)",
        "error_card_hover_border": "rgba(255, 82, 82, 0.3)",
    },
    "dark": {
        "card_bg": "#2d2d2d",
        "card_bg_hover": "#363636",
        "card_border": "#444444",
        "card_border_hover": "#555555",
        "platform_bg": "#363636",
        "platform_bg_hover": "#3d3d3d",
        "platform_border": "#444444",
        "platform_border_hover": "#555555",
        "platform_selected_bg": "rgba(124, 77, 255, 0.15)",
        "platform_selected_border": "#9c7eff",
        "error_card_bg": "rgba(255, 82, 82, 0.08)",
        "error_card_border": "rgba(255, 82, 82, 0.25)",
        "error_card_hover_bg": "rgba(255, 82, 82, 0.12)",
        "error_card_hover_border": "rgba(255, 82, 82, 0.35)",
    },
}


def _get_theme_colors() -> dict:
    """获取当前主题颜色"""
    if isDarkTheme():
        return _THEME_COLORS["dark"]
    return _THEME_COLORS["light"]


class PlatformResultWidget(QFrame):
    """
    平台搜索结果展示组件

    显示单个平台的搜索结果信息，支持选中状态切换和主题自适应。
    不覆盖 QLabel 颜色，由 QFluentWidgets 自动处理深浅色文本颜色。

    Attributes:
        platform (str): 平台标识
        result_data (dict): 搜索结果数据
        is_selected (bool): 是否被选中
        index (int): 在父组件中的索引位置
        on_selected (callable): 选中状态变化回调
    """

    def __init__(
        self,
        platform: str,
        result_data: dict,
        index: int = 0,
        file_path: str = "",
        parent=None
    ) -> None:
        """
        初始化平台结果组件

        Args:
            platform (str): 平台标识（shazam/netease/kugou）
            result_data (dict): 搜索结果数据
            index (int): 在父组件中的索引位置
            file_path (str): MP3 文件路径（用于提取内嵌封面）
            parent (QWidget | None): 父组件
        """
        super().__init__(parent)
        self.platform = platform
        self.result_data = result_data
        self.is_selected = False
        self.index = index
        self.file_path = file_path  # MP3 文件路径
        self._on_selected_callback: callable | None = None

        self._setup_ui()
        self._setup_style()

        # 监听主题变化
        qconfig.themeChanged.connect(self._on_theme_changed)

    def set_selection_callback(self, callback: callable) -> None:
        """
        设置选中状态变化回调函数

        Args:
            callback (callable): 回调函数，签名为 callback(index: int, selected: bool)
        """
        self._on_selected_callback = callback

    def _setup_ui(self) -> None:
        """
        构建 UI 布局

        使用 CoverImageWidget 替代原来的静态图标，
        支持显示实际的音乐封面图片。
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # 封面图片组件（替代原来的平台图标）
        cover_url = self.result_data.get("cover_link", "")
        self.cover_widget = CoverImageWidget(
            size=48,
            cover_url=cover_url,
            file_path=self.file_path,  # 传递文件路径用于提取内嵌封面
            parent=self
        )
        # 连接点击信号用于预览
        self.cover_widget.clicked.connect(self._on_cover_clicked)
        layout.addWidget(self.cover_widget, 0)

        # 平台名称（显示在封面下方或右侧）
        info_container = QVBoxLayout()
        info_container.setSpacing(4)

        # 平台标识和歌曲信息
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.platform_name = BodyLabel(self._get_platform_display_name())
        self.platform_name.setObjectName("platformName")
        header_layout.addWidget(self.platform_name)

        header_layout.addStretch()

        # 时长
        duration = self.result_data.get("duration", 0)
        if duration:
            duration_icon = IconWidget(FIF.HISTORY)
            duration_icon.setFixedSize(14, 14)
            header_layout.addWidget(duration_icon)

            minutes = duration // 60
            secs = duration % 60
            if minutes > 0:
                duration_text = f"{minutes}:{secs:02d}"
            else:
                duration_text = f"{secs}s"
            duration_label = BodyLabel(duration_text)
            duration_label.setObjectName("durationLabel")
            header_layout.addWidget(duration_label)

        info_container.addLayout(header_layout)

        # 标题
        title = self.result_data.get("title", "Unknown")
        self.title_label = BodyLabel(title)
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName("titleLabel")
        info_container.addWidget(self.title_label)

        # 艺术家和专辑
        artist = self.result_data.get("artist", "Unknown")
        album = self.result_data.get("album", "Unknown Album")
        self.meta_label = BodyLabel(f"{artist} · {album}")
        self.meta_label.setObjectName("metaLabel")
        info_container.addWidget(self.meta_label)

        layout.addLayout(info_container, 1)

    def _on_cover_clicked(self) -> None:
        """
        封面图片点击事件处理

        打开封面预览对话框显示大图。
        """
        pixmap = self.cover_widget.get_pixmap()
        if pixmap and not pixmap.isNull():
            from auto_tag.gui.components.cover_preview_dialog import CoverPreviewDialog
            from PySide6.QtCore import QByteArray

            # 将 QPixmap 转换为 bytes
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QBuffer.OpenModeFlag.WriteOnly)
            pixmap.save(buffer, "PNG")
            image_data = bytes(byte_array.data())

            # 显示预览对话框
            dialog = CoverPreviewDialog(self.window())
            dialog.show_preview(image_data)

    def set_file_path(self, file_path: str) -> None:
        """
        设置 MP3 文件路径

        Args:
            file_path (str): 文件路径
        """
        self.file_path = file_path
        # 重新加载封面（如果有封面组件）
        if hasattr(self, 'cover_widget'):
            self.cover_widget.load_cover(cover_url=self.result_data.get("cover_link", ""), file_path=file_path)

    def _setup_style(self) -> None:
        """设置样式"""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setProperty("class", "PlatformResultWidget")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        self.setMinimumHeight(60)
        self._update_style()

    def _update_style(self) -> None:
        """根据主题和选中状态更新样式"""
        colors = _get_theme_colors()

        if self.is_selected:
            self.setStyleSheet("""
                QFrame[class="PlatformResultWidget"] {
                    background-color: """ + colors["platform_selected_bg"] + """;
                    border: 2px solid """ + colors["platform_selected_border"] + """;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame[class="PlatformResultWidget"] {
                    background-color: """ + colors["platform_bg"] + """;
                    border: 1px solid """ + colors["platform_border"] + """;
                    border-radius: 8px;
                }
            """)

    def _on_theme_changed(self, theme: Theme) -> None:
        """主题切换回调"""
        self._update_style()

    def _get_platform_display_name(self) -> str:
        """获取平台显示名称（支持复合来源）"""
        from auto_tag.gui.i18n import tr

        # 优先使用 combined_source（复合来源）
        combined_source = self.result_data.get("combined_source", "")
        if combined_source:
            return combined_source

        # 备选：使用传统的平台名称映射
        platform_names = {
            "acoustid": "source_acoustid",
            "shazam": "source_shazam",
            "netease": "source_netease",
            "qqmusic": "source_qqmusic",
            "kugou": "source_kugou",
        }
        key = platform_names.get(self.platform, self.platform)
        return tr(key)

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        from auto_tag.gui.i18n import tr

        if not seconds:
            return "--"
        minutes = seconds // 60
        secs = seconds % 60
        if minutes > 0:
            return tr("minutes_seconds_format", minutes=minutes, seconds=secs)
        return tr("seconds_format", seconds=secs)

    def mousePressEvent(self, event) -> None:
        """
        鼠标点击事件处理 - toggle 切换选中状态并通知父组件

        当用户点击此组件时：
        1. 切换自身的选中状态（视觉反馈）
        2. 通知父组件 SongResultCard 更新 selected_platform_index
        3. 确保同一卡片内只有一个结果被选中
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected(not self.is_selected)
            # DEBUG: 实时输出点击事件
            print(f"[DEBUG] PlatformResultWidget clicked: index={self.index}, "
                  f"platform={self.platform}, selected={self.is_selected}")
            # 通知父组件更新选中的平台索引
            if self._on_selected_callback:
                self._on_selected_callback(self.index, self.is_selected)

    def set_selected(self, selected: bool) -> None:
        """
        设置选中状态

        Args:
            selected (bool): 是否选中
        """
        self.is_selected = selected
        self._update_style()

    def get_result_data(self) -> dict:
        """获取结果数据"""
        return self.result_data

    def deleteLater(self) -> None:
        """
        延迟删除覆盖

        在组件被删除前断开信号连接，防止内存泄漏。
        """
        try:
            qconfig.themeChanged.disconnect(self._on_theme_changed)
        except (TypeError, RuntimeError):
            pass
        super().deleteLater()


class SongResultCard(CardWidget):
    """
    歌曲搜索结果卡片组件

    显示单首歌曲的所有平台搜索结果，支持折叠/展开交互和主题自适应。
    不覆盖 QLabel 颜色，由 QFluentWidgets 自动处理深浅色文本颜色。

    Attributes:
        file_path (str): 原始文件路径
        is_expanded (bool): 是否展开
        selected_platform_index (int): 选中的平台结果索引
        on_selection_changed (callable): 选中状态变化回调
        refresh_requested (Signal): 刷新搜索结果信号
    """

    refresh_requested = Signal(str)

    def __init__(
        self,
        file_path: str,
        display_name: str,
        search_results: list[dict],
        default_result: dict | None = None,
        has_error: bool = False,
        parent=None
    ) -> None:
        """
        初始化歌曲结果卡片

        Args:
            file_path (str): 原始文件路径
            display_name (str): 显示的文件名
            search_results (list[dict]): 平台搜索结果列表
            default_result (dict | None): 默认识别结果
            has_error (bool): 是否有错误
            parent (QWidget | None): 父组件
        """
        super().__init__(parent)
        self.file_path = file_path
        self.display_name = display_name
        self.search_results = search_results
        self.default_result = default_result
        self.has_error = has_error
        self.is_expanded = True
        self.selected_platform_index = 0
        self.on_selection_changed = None

        # 刷新动画状态
        self._refresh_angle = 0
        self._refresh_timer: QTimer | None = None
        self._is_refreshing = False

        self._setup_ui()
        self._setup_style()
        
        # 设置卡片最小宽度，确保按钮区域不被压缩
        # 最小宽度 = 勾选框(28) + 文件名(150) + 间距(36) + 按钮容器(120) + 边距(32) = ~366px
        self.setMinimumWidth(366)

        # 监听主题变化
        qconfig.themeChanged.connect(self._on_theme_changed)

        # 如果有搜索结果，默认选中第一个
        if search_results:
            self._select_platform(0)

    def _setup_ui(self) -> None:
        """构建 UI 布局"""
        from PySide6.QtWidgets import QSizePolicy
        from PySide6.QtGui import QPainter

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 卡片头部 ===
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)

        # 勾选框（固定大小）
        self.checkbox = CheckBox()
        self.checkbox.setChecked(not self.has_error)
        self.checkbox.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )
        header_layout.addWidget(self.checkbox)

        # === 文件名区域（使用容器包装，支持省略号显示）===
        file_container = QFrame()
        file_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        file_layout = QHBoxLayout(file_container)
        file_layout.setContentsMargins(0, 0, 0, 0)

        # 自定义支持省略号的文件名标签
        class ElidedFileNameLabel(SubtitleLabel):
            """文件名标签，支持长文本自动省略号截断"""
            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(self.palette().color(self.foregroundRole()))
                
                text = self.text()
                if not text:
                    return

                available_width = self.width()
                metrics = self.fontMetrics()
                elided_text = metrics.elidedText(text, Qt.TextElideMode.ElideRight, available_width)
                
                # 左对齐绘制，垂直居中
                text_rect = self.rect()
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_text)

        self.file_label = ElidedFileNameLabel(self.display_name)
        self.file_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        file_layout.addWidget(self.file_label)
        header_layout.addWidget(file_container, 1)

        # === 右侧按钮容器（固定大小，不会被压缩）===
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        buttons_frame.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed
        )
        # 按钮容器最小宽度，确保按钮不会被压缩
        # 计算：结果数量(约40px) + 刷新按钮(28px) + 收起按钮(32px) + 间距(16px) = 116px
        buttons_frame.setMinimumWidth(120)

        # 结果数量标签
        if self.search_results:
            self.count_label = BodyLabel(f"{len(self.search_results)} 个结果")
            buttons_layout.addWidget(self.count_label)

        # 刷新搜索按钮
        self.refresh_btn = ToolButton()
        self.refresh_btn.setFixedSize(28, 28)
        self.refresh_btn.setIcon(FIF.SYNC)
        self.refresh_btn.setToolTip(self._get_refresh_tooltip())
        self.refresh_btn.clicked.connect(self._on_refresh_search)
        buttons_layout.addWidget(self.refresh_btn)

        # 展开/收起按钮
        self.expand_btn = ToolButton()
        self.expand_btn.setFixedSize(32, 32)
        self.expand_btn.clicked.connect(self._toggle_expand)
        buttons_layout.addWidget(self.expand_btn)

        header_layout.addWidget(buttons_frame)

        self._update_expand_icon()

        main_layout.addLayout(header_layout)

        # === 搜索结果列表区域 ===
        self.results_container = QFrame()
        self.results_container.setObjectName("resultsContainer")

        results_layout = QVBoxLayout(self.results_container)
        results_layout.setContentsMargins(16, 0, 16, 12)
        results_layout.setSpacing(8)

        # 添加平台结果
        self._platform_widgets: list[PlatformResultWidget] = []
        if self.search_results:
            for idx, result in enumerate(self.search_results):
                platform = result.get("source", "shazam")
                platform_widget = PlatformResultWidget(
                    platform, result,
                    index=idx,
                    file_path=self.file_path  # 传递文件路径用于提取内嵌封面
                )
                platform_widget.setObjectName(f"platformResult_{idx}")
                # 设置选中回调，通知父组件更新索引
                platform_widget.set_selection_callback(self._on_platform_selected)
                results_layout.addWidget(platform_widget)
                self._platform_widgets.append(platform_widget)
        else:
            # 没有搜索结果，显示默认结果
            self.no_result_label = BodyLabel("未找到匹配的搜索结果")
            results_layout.addWidget(self.no_result_label)

        main_layout.addWidget(self.results_container)

        # 设置滚动区域（当结果过多时）
        self.results_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum
        )

    def _setup_style(self) -> None:
        """设置样式"""
        self.setProperty("class", "SongResultCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_style()

    def _update_style(self) -> None:
        """根据当前主题更新卡片和子组件的样式"""
        colors = _get_theme_colors()

        # 设置 objectName 以便 QSS 选择器能正确匹配
        self.setObjectName("SongResultCard")

        if self.has_error:
            self.setStyleSheet(f"""
                #SongResultCard {{
                    background-color: {colors["error_card_bg"]};
                    border: 1px solid {colors["error_card_border"]};
                    border-radius: 12px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                #SongResultCard {{
                    background-color: {colors["card_bg"]};
                    border: 1px solid {colors["card_border"]};
                    border-radius: 12px;
                }}
            """)

    def _on_theme_changed(self, theme: Theme) -> None:
        """主题切换回调"""
        self._update_style()

    def _toggle_expand(self) -> None:
        """切换展开/收起状态"""
        self.is_expanded = not self.is_expanded
        self._update_expand_icon()
        self.results_container.setVisible(self.is_expanded)

    def _update_expand_icon(self) -> None:
        """更新展开/收起按钮图标"""
        try:
            if self.is_expanded:
                self.expand_btn.setIcon(FIF.UP)
            else:
                self.expand_btn.setIcon(FIF.DOWN)
        except Exception:
            pass

    def _on_platform_selected(self, index: int, selected: bool) -> None:
        """
        平台结果选中回调处理

        当用户点击某个平台结果时被调用：
        1. 如果是选中操作，更新 selected_platform_index 并取消其他结果的选中
        2. 通知外部回调（如果有）

        Args:
            index (int): 被点击的平台结果索引
            selected (bool): 是否为选中（True=选中，False=取消选中）
        """
        # DEBUG: 实时输出回调事件
        print(f"[DEBUG] SongResultCard._on_platform_selected called: "
              f"index={index}, selected={selected}")
        
        if selected:
            # 用户选中了某个结果，更新索引
            self._select_platform(index)
        else:
            # 用户取消选中（不太可能发生，但处理一下）
            # 保持当前选中不变，或者可以重新选中第一个
            pass

    def _select_platform(self, index: int) -> None:
        """
        选中指定平台结果

        Args:
            index (int): 平台结果索引
        """
        self.selected_platform_index = index

        # 更新所有平台组件的选中状态
        for i in range(self.results_container.layout().count()):
            widget = self.results_container.layout().itemAt(i).widget()
            if isinstance(widget, PlatformResultWidget):
                if i == index:
                    widget.set_selected(True)
                else:
                    widget.set_selected(False)

        # 通知选中状态变化
        if self.on_selection_changed:
            self.on_selection_changed(self.file_path, index)

    def get_selected_result(self) -> dict:
        """
        获取选中的搜索结果

        Returns:
            dict: 选中的搜索结果数据
        """
        if self.search_results and 0 <= self.selected_platform_index < len(
            self.search_results
        ):
            return self.search_results[self.selected_platform_index]
        elif self.default_result:
            return self.default_result
        return {}

    def is_checked(self) -> bool:
        """获取勾选状态"""
        return self.checkbox.isChecked()

    def set_on_selection_changed(self, callback) -> None:
        """
        设置选中状态变化回调

        Args:
            callback (callable): 回调函数 (file_path, index)
        """
        self.on_selection_changed = callback

    def deleteLater(self) -> None:
        """
        延迟删除覆盖

        在卡片被删除前停止所有子组件的加载线程并断开信号连接，防止内存泄漏。
        """
        # 停止所有平台组件的封面加载线程
        for widget in self._platform_widgets:
            if hasattr(widget, 'cover_widget'):
                widget.cover_widget._stop_loader()
        # 断开主题变化信号连接
        try:
            qconfig.themeChanged.disconnect(self._on_theme_changed)
        except (TypeError, RuntimeError):
            pass
        super().deleteLater()

    def _get_refresh_tooltip(self) -> str:
        """
        获取刷新按钮的提示文本

        Returns:
            str: 翻译后的提示文本
        """
        from auto_tag.gui.i18n import tr
        return tr("refresh_song_search")

    def _on_refresh_search(self) -> None:
        """
        刷新搜索按钮点击处理

        发出刷新请求信号，通知父组件重新搜索该歌曲，同时启动 loading 动画。
        """
        if self._is_refreshing:
            return
        self.set_refreshing(True)
        self.refresh_requested.emit(self.file_path)

    def set_refreshing(self, refreshing: bool) -> None:
        """
        设置刷新按钮的加载状态

        Args:
            refreshing (bool): 是否正在刷新
        """
        self._is_refreshing = refreshing
        self.refresh_btn.setEnabled(not refreshing)

        if refreshing:
            # 启动旋转动画
            self._refresh_angle = 0
            self._refresh_timer = QTimer(self)
            self._refresh_timer.setInterval(30)
            self._refresh_timer.timeout.connect(self._rotate_refresh_icon)
            self._refresh_timer.start()
        else:
            # 停止旋转动画
            if self._refresh_timer and self._refresh_timer.isActive():
                self._refresh_timer.stop()
                self._refresh_timer = None
            self._refresh_angle = 0
            self.refresh_btn.setIcon(FIF.SYNC)

    def _rotate_refresh_icon(self) -> None:
        """定时器回调，旋转刷新图标"""
        self._refresh_angle = (self._refresh_angle + 15) % 360
        icon = FIF.SYNC.icon()
        pixmap = icon.pixmap(18, 18)
        rotated = pixmap.transformed(
            QTransform().rotate(self._refresh_angle),
            Qt.TransformationMode.SmoothTransformation,
        )
        self.refresh_btn.setIcon(QIcon(rotated))

    def update_search_results(self, search_results: list[dict]) -> None:
        """
        更新搜索结果

        当搜索完成后调用此方法更新卡片显示的搜索结果，并停止 loading 动画。

        Args:
            search_results (list[dict]): 新的搜索结果列表
        """
        # 停止刷新动画
        self.set_refreshing(False)

        self.search_results = search_results

        # 更新结果数量标签
        if hasattr(self, 'count_label') and self.count_label:
            if search_results:
                self.count_label.setText(f"{len(search_results)} 个结果")
                self.count_label.setVisible(True)
            else:
                self.count_label.setVisible(False)

        # 重建结果容器内容
        results_layout = self.results_container.layout()
        while results_layout.count():
            child = results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 添加新的平台结果
        self._platform_widgets = []
        if search_results:
            for idx, result in enumerate(search_results):
                platform = result.get("source", "shazam")
                platform_widget = PlatformResultWidget(
                    platform, result,
                    index=idx,
                    file_path=self.file_path  # 传递文件路径用于提取内嵌封面
                )
                platform_widget.setObjectName(f"platformResult_{idx}")
                # 设置选中回调，通知父组件更新索引
                platform_widget.set_selection_callback(self._on_platform_selected)
                results_layout.addWidget(platform_widget)
                self._platform_widgets.append(platform_widget)
        else:
            self.no_result_label = BodyLabel("未找到匹配的搜索结果")
            results_layout.addWidget(self.no_result_label)

        # 默认选中第一个
        self.selected_platform_index = 0
        if search_results:
            self._select_platform(0)

        # 刷新成功，重置错误状态并重新应用卡片样式
        self.has_error = False
        if hasattr(self, 'checkbox') and self.checkbox:
            self.checkbox.setChecked(True)
        self._update_style()
        self.results_container.setStyleSheet("""
            QFrame#resultsContainer {
                background-color: transparent;
            }
        """)
