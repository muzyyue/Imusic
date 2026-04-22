task:给失败的歌曲那里加一个重试按钮,



# Imusic 项目会话上下文 (2026-04-20)

> 本文档记录本次会话的所有关键信息，供新对话快速了解项目当前状态。

---

## 1. 项目基本信息

| 属性 | 值 |
|------|-----|
| **项目名称** | Imusic (原 mp3ShazamAutoTag) |
| **当前版本** | v0.4.24 |
| **作者** | ling |
| **许可证** | MIT |
| **技术栈** | PySide6 + QFluentWidgets + shazamio + pymusiclibrary |
| **运行环境** | Windows, Python 3.x, 虚拟环境 venv |
| **GUI 框架** | Fluent Design 风格（扁平化设计） |

### 核心功能

- 使用 Shazam API 自动识别音频文件（MP3/OGG）
- 根据识别结果重命名文件和更新元数据标签
- 卡片式搜索结果布局（SongResultCard + PlatformResultWidget）
- 深色/浅色主题切换支持
- 音频/视频格式转换（基于 FFmpeg）
- 歌词获取与嵌入（多提供商：网易云/酷狗/LRCLib/Apple Music/MusixMatch）
- 国际化支持（英文/中文）

---

## 2. 本次会话解决的问题（按时间顺序）

### 2.1 问题1：搜索结果未显示在歌曲卡片中 (v0.4.15)
- **现象**：Shazam 识别成功，但卡片显示"未找到匹配的搜索结果"
- **根因**：`music_library_manager.py` 的全局单例 `_initialized` 始终为 `False`
- **修复**：在 `RecognizeWorker._process_files()` 中调用 `init_music_library()`

### 2.2 问题2：展开/收起按钮图标缺失 (v0.4.17)
- **现象**：右侧按钮区域空白，无图标显示
- **根因**：`PushButton` 不支持直接显示 `FluentIcon` 图标
- **修复**：将 `PushButton` 改为 `ToolButton`，使用 `FIF.UP/DOWN` 图标

### 2.3 问题3：卡片式布局完全不显示 (v0.4.18)
- **现象**：改为卡片布局后搜索结果完全空白
- **根因**：
  - `FIF.CLOCK` 常量在用户 QFluentWidgets 版本中不存在 → `AttributeError`
  - 酷狗 API 的 `search()` 不支持 `limit` 参数 → `TypeError`
- **修复**：
  - `FIF.CLOCK` → `FIF.HISTORY`
  - 移除酷狗 API 的 `limit` 参数
  - 为 `_on_file_processed` 添加异常处理和日志

### 2.4 问题4：深色模式样式破坏 (v0.4.20)
- **现象**：QScrollArea 和 cards_container 使用系统默认白色背景
- **根因**：移除透明样式后未设置正确的背景色
- **修复**：
  - 添加 `_update_scroll_area_style()` / `_update_cards_container_style()`
  - 深色模式使用 `#1e1e1e`，浅色模式使用 `#fafafa`
  - 连接 `qconfig.themeChanged` 信号实现主题切换自动更新

### 2.5 问题5：选择文件夹后应用直接崩溃 (v0.4.22)
- **现象**：选择文件夹后进程直接退出，无 Python 异常堆栈
- **根因**：pymusiclibrary 原生 C 库在子线程中调用时触发 `access violation`（C 级别段错误）
- **修复**：默认完全禁用 pymusiclibrary，仅使用 Shazam 识别

### 2.6 问题6：重新启用网易云搜索（线程安全版本）(v0.4.23)
- **需求**：用户需要网易云搜索功能
- **官方要求**（来自 [pymusiclibrary GitHub](https://github.com/2061360308/NeteaseCloudMusic_PythonSDK)）：
  > "KuGouMusicApi, NeteaseCloudMusicApi 等接口对象 **均不能跨线程使用**，如果需要请为每个线程创建实例"
- **方案**：使用 `threading.local()` 为每个线程创建独立的 API 实例
- **新增函数**：
  - `get_thread_local_netease_api()` — 线程本地 NetEase API
  - `get_thread_local_kugou_api()` — 线程本地 KuGou API
  - `is_permanently_failed()` — 检查是否永久失败

### 2.7 问题7：导入错误 (v0.4.23 补丁)
- **现象**：`ImportError: cannot import name 'get_netease_api' from 'auto_tag.music_library_manager'`
- **根因**：重写 `music_library_manager.py` 后删除了旧函数名，但 `lyric/manager.py` 还在导入
- **修复**：更新 `lyric/manager.py` 的导入为线程安全版本

### 2.8 问题8：选择目录后程序崩溃（彻底修复）(v0.4.24)
- **现象**：选择目录后进程直接退出，无 Python 异常堆栈
- **根因**：
  1. `audio_recognize.py` 第 496 行调用了不存在的 `init_music_library()` 函数
  2. pymusiclibrary 原生 C 库（QuickJS 引擎）在 Windows 环境中触发 access violation
  3. C 级崩溃无法被 Python try-except 捕获，直接导致进程终止
- **修复**：
  - 默认禁用 pymusiclibrary，将 `_init_permanently_failed` 初始值改为 `True`
  - 修复 `audio_recognize.py` 中的函数调用错误
  - 在 `_search_netease()` 和 `_search_kugou()` 中添加早期 `is_permanently_failed()` 检查
  - 更新 `recognize_worker.py` 日志消息
- **结果**：应用稳定运行，仅使用 Shazam 识别（纯 Python，稳定可靠）

### 2.9 最终状态：pymusiclibrary 与用户环境不兼容
- **日志证据**：
  ```
  [MusicLibrary] NetEase native library CRASHED in thread 'asyncio_0': access violation writing 0x0000000000000008
  [MusicLibrary] KuGou native library CRASHED in thread 'asyncio_1': access violation reading 0x0000000000000028
  [MusicLibrary] Disabling all native library usage permanently
  ```
- **结论**：pymusiclibrary 原生 C 库（QuickJS 引擎）在用户的 Windows 环境中无法运行
- **架构原因**：JavaScript → QuickJS (C engine) → Python (ctypes)，QuickJS 初始化时崩溃
- **当前状态**：应用稳定运行，Crash Protection 机制生效，优雅降级到 Shazam only

---

## 3. 当前功能状态

| 功能 | 状态 | 说明 |
|------|------|------|
| ✅ 应用启动 | 正常 | 不再崩溃 |
| ✅ Shazam 识别 | 正常 | 纯 Python 实现，稳定可靠 |
| ✅ 卡片式布局 | 正常 | SongResultCard + PlatformResultWidget |
| ✅ 深色模式 | 已适配 | QScrollArea + cards_container 样式正确 |
| ✅ 进度条 | 正常 | 48/48 文件处理完成 |
| ✅ Crash Protection | 已启用 | 检测到 access violation 后优雅降级 |
| ⚠️ 网易云搜索 | **不可用** | pymusiclibrary 原生库不兼容 Windows 环境 |
| ⚠️ 酷狗搜索 | **不可用** | 同上 |

---

## 4. 关键文件修改清单

| 文件路径 | 主要修改内容 |
|----------|--------------|
| `auto_tag/music_library_manager.py` | **完全重写**为线程安全版本，使用 `threading.local()` 实现每线程独立 API 实例，添加 `_patch_music_library()` Monkey Patch 修复原生库 Bug，添加 `_init_permanently_failed` 全局标记实现 Crash Protection |
| `auto_tag/audio_recognize.py` | 使用 `get_thread_local_netease_api()` / `get_thread_local_kugou_api()` 替代全局单例，添加 `is_permanently_failed()` 快速跳过检查，移除酷狗 `limit` 参数 |
| `auto_tag/gui/workers/recognize_worker.py` | 移除 `init_music_library()` 全局初始化调用，添加详细日志输出，说明原生库禁用原因 |
| `auto_tag/gui/pages/home_page.py` | 添加深色模式样式方法 (`_update_scroll_area_style` / `_update_cards_container_style`)，连接 `qconfig.themeChanged` 信号，为 `_on_file_processed` 添加 try-except 异常处理和日志，当 search_results 为空时将 Shazam 结果包装为搜索结果格式传入卡片 |
| `auto_tag/gui/components/song_result_card.py` | 将 `PushButton` 改为 `ToolButton` 显示图标，`FIF.CLOCK` → `FIF.HISTORY`，使用 `objectName("SongResultCard")` 选择器替代属性选择器，添加 `_on_theme_changed()` 方法支持主题切换刷新 |
| `auto_tag/lyric/manager.py` | 更新导入为 `get_thread_local_netease_api()` / `get_thread_local_kugou_api()`，移除 `init_music_library()` 调用，更新文档注释为"线程本地" |

---

## 5. 技术要点（避免再次出错）

### 5.1 pymusiclibrary 线程安全（最重要！）

```python
# ✅ 正确：每线程创建独立实例
import threading
_thread_local = threading.local()

def get_thread_local_netease_api():
    """获取当前线程的 NetEase API 实例"""
    if not hasattr(_thread_local, 'netease_api'):
        _thread_local.netease_api = NeteaseCloudMusicApi()
    return _thread_local.netease_api

# ❌ 错误：全局单例 + 跨线程调用 → access violation 崩溃
GLOBAL_API = NeteaseCloudMusicApi()  # 在主线程创建
def worker():
    result = GLOBAL_API.search("test")  # 在子线程使用 → 崩溃！
```

### 5.2 FluentIcon 兼容性（已验证）

```python
# 用户版本可用的图标（已验证 OK）：
FIF.UP, FIF.DOWN, FIF.HISTORY, FIF.MENU, FIF.CHEVRON_UP, FIF.CHEVRON_DOWN

# 不可用的图标（会导致 AttributeError）：
FIF.CLOCK  # ❌ 用户版本不存在
```

### 5.3 QFluentWidgets 组件选择

```python
# 显示图标：使用 ToolButton 或 IconButton
from qfluentwidgets import ToolButton
btn = ToolButton(FIF.UP)  # ✅ 正确

# 不显示图标：PushButton
from qfluentwidgets import PushButton
btn = PushButton()  # ❌ 无法显示 FluentIcon
```

### 5.4 KuGou API 参数差异

```python
# ❌ 错误：KuGou 不支持 limit 参数
api.search("keyword", limit=3)  # TypeError!

# ✅ 正确：不传 limit
api.search("keyword")
songs = data.get('lists', [])[:3]  # 手动截取
```

### 5.5 深色模式样式

```python
def _update_scroll_area_style(self):
    """更新滚动区域样式以适配当前主题"""
    if isDarkTheme():
        bg_color = "#1e1e1e"   # 深色背景
        border_color = "#3d3d3d"
    else:
        bg_color = "#fafafa"   # 浅色背景
        border_color = "#e0e0e0"
    
    self.scroll_area.setStyleSheet(f"""
        QScrollArea {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 8px;
        }}
    """)
```

### 5.6 Crash Protection 模式

```python
_permanently_failed = False  # 全局标记

def safe_api_call():
    global _permanently_failed
    
    if _permanently_failed:
        return None  # 快速跳过
    
    try:
        api = create_api_in_current_thread()
        return api
    except Exception as e:
        if "access violation" in str(e).lower():
            _permanently_failed = True  # 标记永久失败
            logger.error(f"CRASHED: {e}")
        return None
```

---

## 6. 项目结构（重点模块）

```
mp3ShazamAutoTag/
├── main.py                          # 主入口
├── pyproject.toml                   # 项目配置 (v0.4.23)
│
├── auto_tag/
│   ├── audio_recognize.py           # 核心：Shazam 识别 + 多平台搜索
│   ├── music_library_manager.py     # 核心：线程安全的 pymusiclibrary 管理
│   │
│   ├── lyric/
│   │   └── manager.py               # 歌词管理器（使用线程本地 API）
│   │
│   └── gui/
│       ├── main_window.py           # FluentWindow 主窗口
│       ├── style.qss                # 全局样式表
│       │
│       ├── pages/
│       │   ├── home_page.py         # 主页（卡片式搜索结果）
│       │   ├── settings_page.py     # 设置页（语言/主题切换）
│       │   ├── converter_page.py    # 转换页
│       │   └── music_manager_page.py # 音乐管理页
│       │
│       ├── components/
│       │   ├── song_result_card.py  # 歌曲卡片组件（含展开/收起）
│       │   ├── cover_preview_dialog.py
│       │   └── song_search_dialog.py
│       │
│       ├── workers/
│       │   ├── recognize_worker.py  # 识别工作线程（QThread）
│       │   ├── lyric_worker.py      # 歌词工作线程
│       │   └── converter_worker.py  # 转换工作线程
│       │
│       └── i18n/
│           ├── translator.py
│           └── locales/ (en.json, zh.json)
│
├── .trae/
│   ├── rules/
│   │   ├── project-rules.md         # 工作区规则
│   │   └── program.md               # 技术规范文档
│   └── skills/
│       └── pymusiclibrary/          # pymusiclibrary skill 文档
│           ├── SKILL.md             # 线程安全最佳实践
│           └── references/
│               ├── search.md        # 线程安全搜索示例
│               ├── api_list.md
│               ├── lyrics.md
│               └── user.md
│
└── tests/                            # 测试目录
```

---

## 7. 数据流架构

```
用户选择文件夹
      │
      ▼
RecognizeWorker (QThread 子线程)
      │
      ├─── recognize_and_rename_file()
      │       │
      │       ├─── Shazam 识别（纯 Python，稳定）✅
      │       │       └── 返回 title, author, album, cover_link
      │       │
      │       └─── multi_source_search()
      │               │
      │               ├─── is_permanently_failed? → 直接返回 Shazam 结果
      │               │
      │               └─── asyncio.gather([
      │                     get_thread_local_netease_api().search(),
      │                     get_thread_local_kugou_api().search()
      │                   ])
      │                       │
      │                       └── 如果 crash → _init_permanently_failed = True
      │
      ▼
file_processed 信号 → home_page._on_file_processed()
      │
      ├─── 包装 Shazam 结果为 search_results 格式（如果为空）
      ├─── 创建 SongResultCard（带异常保护 try-except）
      └─── 插入到 cards_layout
```

---

## 8. Git 提交历史（本次会话）

| 版本 | 类型 | Commit | 说明 |
|------|------|--------|------|
| v0.4.15 | fix | - | 修复多平台搜索结果未显示 |
| v0.4.17 | fix | - | 修复展开按钮图标缺失 |
| v0.4.18 | fix | - | 修复卡片式布局完全不显示 |
| v0.4.19 | fix | - | 修复深色模式文本不可见 + 时长图标 |
| v0.4.20 | fix | cf19109 | 完成深色模式样式适配 |
| v0.4.21 | fix | 1de7f48 | 修复原生库崩溃导致进度卡死 |
| v0.4.22 | fix | ae0af61 | 修复选择文件夹后崩溃 |
| v0.4.23 | feat | c3a94d7 | 重新启用网易云搜索（线程安全版本）|
| 补丁 | fix | 9b7ef74 | 修复 lyric/manager.py 导入错误 |

---

## 9. 待解决问题

### 9.1 pymusiclibrary 兼容性（高优先级）

**问题**：原生 C 库在用户 Windows 环境中无法运行

**错误日志**：
```
[MusicLibrary] NetEase native library CRASHED: access violation writing 0x0000000000000008
[MusicLibrary] KuGou native library CRASHED: access violation reading 0x0000000000000028
```

**可能解决方向**：
1. 更新 pymusiclibrary 到最新版本：`pip install --upgrade pymusiclibrary`
2. 安装 Visual C++ Redistributable（x64）
3. 确认 Python 是 64 位：`python -c "import struct; print(struct.calcsize('P') * 8)"` 应输出 `64`
4. 查看 pymusiclibrary GitHub Issues 搜索 `access violation` 或 `Windows`
5. 尝试在主线程中预初始化（而非子线程）

**当前 Workaround**：仅使用 Shazam 识别功能（纯 Python，稳定）

### 9.2 网易云搜索功能恢复

依赖解决问题 9.1。需要 pymusiclibrary 能正常初始化后才能重新启用。

---

## 10. Skill 文档更新记录

已更新 `.trae/skills/pymusiclibrary/` 目录：

### SKILL.md 新增内容
- ⚠️ **Thread Safety (CRITICAL)** 章节
  - 官方线程安全要求
  - 错误示例 vs 正确示例对比
  - 崩溃症状和诊断方法
  - 推荐的 `threading.local()` 封装模式
  - Crash Protection 完整代码

### references/search.md 新增内容
- **Thread-Safe Search** 章节
  - 线程安全搜索函数完整实现
  - asyncio + ThreadPoolExecutor 并发搜索示例
  - 带 Crash Protection 的封装代码
  - KuGou API 参数差异说明

---

*文档生成时间: 2026-04-20*
*生成者: AI Assistant*
*适用于: 新对话快速了解项目状态*
