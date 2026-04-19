---
alwaysApply: false
description: 第一次会话开始时
---
# Imusic 项目技术规范

> 本文档用于 AI 快速了解项目架构、技术栈和开发规范

## 1. 项目概述

**项目名称**: Imusic  
**版本**: 0.4.3  
**作者**: ling  
**许可证**: MIT  

**核心功能**:
- 使用 Shazam API 自动识别音频文件（MP3/OGG）
- 根据识别结果重命名文件（`Title - Artist - Album.ext`）
- 自动更新音频元数据标签（ID3/Vorbis）
- 自动下载并嵌入专辑封面
- 支持 Plex 媒体服务器目录结构
- 提供 CLI 和 GUI 两种操作界面
- 支持音频/视频格式转换（基于 ffmpeg）
- 国际化支持（英文/中文）
- 歌词获取与嵌入（支持多提供商：网易云/酷狗/LRCLib/Apple Music/MusixMatch）
- 音乐元信息编辑与封面管理

**运行环境**:
- Python >= 3.6（注意：Python 3.11/3.12 可能存在兼容性问题）
- 跨平台支持（Windows/macOS/Linux）
- 搭建虚拟环境（如 venv）以隔离项目依赖

---

## 2. 技术栈

### 2.1 核心依赖

| 依赖包 | 版本要求 | 用途 |
|--------|----------|------|
| `shazamio` | >= 0.5.0 | Shazam 音频识别 API |
| `mutagen` | - | 音频元数据处理（通用） |
| `eyed3` | - | MP3 ID3 标签处理 |
| `soundfile` | - | OGG 转 WAV 音频转换 |
| `unidecode` | - | Unicode 字符转 ASCII |
| `tqdm` | - | 进度条显示 |
| `ffmpeg-python` | >= 0.2.0 | 音频/视频格式转换 |
| `pymusiclibrary` | - | 网易云/酷狗音乐 API 集成 |

### 2.2 开发依赖

| 依赖包 | 用途 |
|--------|------|
| `pytest` | 单元测试框架 |
| `pytest-asyncio` | 异步测试支持 |
| `pyinstaller` | 可执行文件打包 |

### 2.3 GUI 技术栈

- **框架**: PySide6（Qt for Python）
- **UI 组件库**: PySide6-Fluent-Widgets（Fluent Design 风格）
- **主要组件**: FluentWindow, ComboBox, PushButton, TreeWidget 等

### 2.4 国际化支持

- **翻译框架**: 自定义 Translator 类
- **支持语言**: English (en)、中文 (zh)
- **翻译文件**: JSON 格式（`locales/en.json`, `locales/zh.json`）

---

## 3. 项目结构

```
mp3ShazamAutoTag/
├── main.py                    # 主入口，CLI 参数解析
├── pyproject.toml             # 项目配置（PEP 517/518）
├── requirements.txt           # 依赖列表
├── Readme.md                  # 项目说明
├── LICENSE                    # MIT 许可证
├── .gitignore                 # Git 忽略规则
│
├── auto_tag/                  # 核心模块包
│   ├── __init__.py
│   ├── audio_recognize.py     # 音频识别与处理核心逻辑
│   ├── utils.py               # 工具函数（字符串处理等）
│   │
│   ├── lyric/                 # 歌词模块
│   │   ├── __init__.py
│   │   ├── manager.py         # 歌词管理器（LyricManager）
│   │   └── provider.py        # 歌词提供商配置
│   │
│   ├── music_library_manager.py # 全局 MusicLibrary API 管理器
│   │
│   ├── gui/                   # GUI 模块（PySide6 + QFluentWidgets）
│   │   ├── __init__.py        # launch_gui() 入口
│   │   ├── main_window.py     # 主窗口（FluentWindow）
│   │   ├── config.py          # GUI 配置管理（语言/主题）
│   │   ├── style.qss          # 全局样式表
│   │   │
│   │   ├── pages/             # 页面组件
│   │   │   ├── __init__.py
│   │   │   ├── home_page.py   # 主页（音频识别）
│   │   │   ├── settings_page.py # 设置页面（语言/主题切换）
│   │   │   ├── converter_page.py # 转换页面
│   │   │   └── music_manager_page.py # 音乐管理页面
│   │   │
│   │   ├── components/        # 可复用组件
│   │   │   ├── __init__.py
│   │   │   ├── cover_preview_dialog.py # 封面预览对话框
│   │   │   └── song_search_dialog.py   # 搜索结果选择对话框
│   │   │
│   │   ├── workers/           # 工作线程
│   │   │   ├── __init__.py
│   │   │   ├── recognize_worker.py # 音频识别工作线程
│   │   │   ├── lyric_worker.py     # 歌词获取工作线程
│   │   │   └── converter_worker.py # 音频转换工作线程
│   │   │
│   │   └── i18n/              # 国际化模块
│   │       ├── __init__.py
│   │       ├── translator.py  # 翻译器类
│   │       └── locales/       # 翻译文件
│   │           ├── en.json    # 英文翻译
│   │           └── zh.json    # 中文翻译
│   │
│   └── converter/             # 音频转换模块
│       ├── __init__.py
│       ├── config.py          # 转换配置
│       ├── converter.py       # 音频转换核心类
│       ├── metadata_manager.py # 元数据管理器
│       └── custom_format.py   # 自定义格式管理
│
├── assets/                    # 静态资源
│   └── auto_tag.ico           # 应用图标
│
├── build_tools/               # 构建工具
│   └── build_exe.py           # PyInstaller 打包脚本
│
└── tests/                     # 测试目录
    ├── __init__.py
    ├── test_recognize.py      # 核心功能测试
    ├── fileToTest.mp3         # 测试音频文件
    └── fileToTest.ogg         # 测试音频文件
```

---

## 4. 核心模块说明

### 4.1 main.py - 程序入口

**职责**: CLI 参数解析，启动 GUI 或 CLI 模式

**关键参数**:

| 参数 | 短参数 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--directory` | `-di` | str | cwd | 处理目录 |
| `--modify` | `-m` | bool | True | 是否应用修改 |
| `--delay` | `-de` | int | 10 | 重试延迟（秒） |
| `--nbrRetry` | `-n` | int | 3 | 最大重试次数 |
| `--trace` | `-tr` | bool | False | 调试输出 |
| `--gui` | `-g` | bool | True | 启动 GUI |
| `--extensions` | `-e` | str | mp3,ogg | 文件扩展名 |
| `--output` | `-o` | str | None | 输出目录 |
| `--plex` | `-p` | flag | False | Plex 目录结构 |
| `--copy` | `-c` | str | None | 复制到指定目录 |
| `--tag_only` | `-to` | bool | False | 仅更新标签 |

### 4.2 audio_recognize.py - 核心处理模块

**主要函数**:

```python
async def find_and_recognize_audio_files(
    folder_path: str,
    *,
    modify: bool = True,
    delay: int = 10,
    nbr_retry: int = 3,
    trace: bool = False,
    extensions: list[str] | tuple[str, ...] = ("mp3", "ogg"),
    output_dir: str | None = None,
    plex_structure: bool = False,
    copy_to: str | None = None,
    tag_only: bool = False,
) -> None
```

**处理流程**:
1. 遍历目录，收集音频文件（跳过 test 目录）
2. 对每个文件调用 `recognize_and_rename_file()`
3. 统计成功/失败数量

```python
async def recognize_and_rename_file(
    *,
    file_path: str,
    shazam: Shazam,
    modify: bool,
    delay: int,
    nbr_retry: int,
    trace: bool,
    output_dir: str | None,
    plex_structure: bool,
    copy_to: str | None = None,
    tag_only: bool = False,
) -> dict
```

**返回结构**:
```python
{
    "file_path": str,        # 原始文件路径
    "new_file_path": str,    # 新文件路径
    "title": str,            # 歌曲标题
    "author": str,           # 艺术家
    "album": str,            # 专辑名
    "cover_link": str,       # 封面 URL
    "error": str | None      # 错误信息（可选）
}
```

**标签更新函数**:
- `update_mp3_tags()` - 更新 MP3 ID3 标签
- `update_mp3_cover_art()` - 更新 MP3 封面
- `update_ogg_tags()` - 更新 OGG Vorbis/Opus 标签

### 4.3 GUI 模块

#### 4.3.1 main_window.py - 主窗口

**类**: `MainWindow(FluentWindow)`

**主要功能**:
- Fluent Design 风格主窗口
- 侧边导航栏（主页/设置）
- 主题和语言配置加载
- 信号槽连接

#### 4.3.2 pages/home_page.py - 主页

**类**: `HomePage(ScrollArea)`

**主要功能**:
- 目录选择与浏览
- 文件列表展示（TreeWidget）
- 进度条显示
- 文件名编辑
- 批量勾选/取消
- 应用更改（普通/Plex 结构）

#### 4.3.3 pages/settings_page.py - 设置页面

**类**: `SettingsPage(QWidget)`

**主要功能**:
- 语言切换（English/中文）
- 主题切换（Light/Dark/Follow System）
- 配置持久化

#### 4.3.4 workers/recognize_worker.py - 识别工作线程

**类**: `RecognizeWorker(QThread)`

**信号**:
- `progress_updated(int, int, int)` - 进度更新
- `file_processed(dict)` - 单文件处理完成
- `all_finished(list)` - 全部完成
- `error_occurred(str)` - 错误发生

#### 4.3.5 config.py - GUI 配置管理

**类**: `AppConfig`

**属性**:
- `language`: 语言设置（默认 "zh"）
- `theme`: 主题设置（"light"/"dark"/"auto"）

**配置文件**: `~/.mp3shazamautotag/config.json`

#### 4.3.6 i18n/translator.py - 翻译器

**类**: `Translator`

**主要方法**:
- `load_language(lang_code)` - 加载语言文件
- `get(key, **kwargs)` - 获取翻译文本

**便捷函数**: `tr(key, **kwargs)`

### 4.4 converter 模块

#### 4.4.1 模块概述

音频转换模块提供音频和视频文件的格式转换功能，支持多种输入输出格式。基于 FFmpeg 实现底层转换操作，提供单文件转换、批量转换和进度回调等功能。

**设计目标**:
- 支持多种音频/视频格式转换
- 提供灵活的配置选项（质量、采样率、比特率等）
- 支持进度回调，便于 GUI 集成
- 保留原始元数据（可选）

**核心功能**:
- 格式检测：使用 FFprobe 检测文件真实格式
- 单文件转换：支持自定义输出参数
- 批量转换：支持批量处理多个文件
- 进度报告：实时报告转换进度

#### 4.4.2 模块结构

```
auto_tag/converter/
├── __init__.py              # 模块入口
├── config.py                # 配置类（ConverterConfig, FormatConfig）
├── converter.py             # 核心转换器（AudioConverter）
├── metadata_manager.py      # 元数据管理器（待实现）
└── workers/
    ├── __init__.py          # 工作线程入口
    └── converter_worker.py  # 转换工作线程（ConverterWorker）
```

#### 4.4.3 AudioConverter 类

**支持格式**:
- **输入格式**: mp3, flac, aac, ogg, wav, m4a, mp4, mkv, avi, mov, wmv, webm
- **输出格式**: mp3, flac, aac, ogg, wav, m4a

**主要方法**:
- `detect_format(file_path)` - 检测文件格式
- `convert_file(input_path, output_path, config, progress_callback)` - 单文件转换
- `convert_batch(files, output_dir, config, progress_callback)` - 批量转换

**使用示例**:
```python
from auto_tag.converter import AudioConverter
from auto_tag.converter.config import ConverterConfig

# 创建转换器实例
converter = AudioConverter()

# 检测文件格式
format_name = converter.detect_format("song.mp4")
print(f"检测到格式: {format_name}")

# 配置转换参数
config = ConverterConfig()
config.set_output_format("mp3", QualityPreset.HIGH)

# 单文件转换
success = converter.convert_file(
    "input.mp4",
    "output.mp3",
    config,
    lambda p: print(f"进度: {p*100:.1f}%")
)

# 批量转换
files = ["song1.mp4", "song2.avi"]
results = converter.convert_batch(
    files,
    "output/",
    config,
    lambda i, total, f: print(f"处理 {i}/{total}: {f}")
)
```

#### 4.4.4 ConverterWorker 类

基于 QThread 的异步转换工作线程，用于 GUI 环境中避免阻塞 UI 线程。

**信号**:
- `progress_updated(int, int, str)` - 进度更新（当前索引, 总数, 当前文件名）
- `file_converted(str, bool, str)` - 单文件转换完成（文件路径, 是否成功, 错误信息）
- `finished_all(list)` - 所有文件转换完成（结果列表）
- `error_occurred(str)` - 错误发生（错误消息）

**使用示例**:
```python
from auto_tag.converter.workers import ConverterWorker
from auto_tag.converter.config import ConverterConfig

# 创建配置
config = ConverterConfig()
config.set_output_format("mp3")

# 创建工作线程
worker = ConverterWorker(
    files=["/path/to/file1.mp4", "/path/to/file2.avi"],
    output_dir="/path/to/output",
    config=config
)

# 连接信号
worker.progress_updated.connect(lambda i, total, f: print(f"{i}/{total}: {f}"))
worker.file_converted.connect(lambda path, success, err: print(f"完成: {path}"))
worker.finished_all.connect(lambda results: print("全部完成"))

# 启动线程
worker.start()
```

### 4.5 utils.py - 工具模块

**函数**:

```python
def find_deepest_metadata_key(data, search_key) -> str | None
```
- 递归搜索嵌套结构中的元数据

```python
def sanitize(s: str, trace: bool) -> str
```
- Unicode 转 ASCII
- 移除括号内容
- 过滤非法文件名字符
- 单词首字母大写

### 4.6 lyric 模块 - 歌词管理

#### 4.6.1 LyricManager 类

**模块路径**: `auto_tag/lyric/manager.py`

**主要功能**:
- 从多个提供商获取歌词（netease, kugou, lrclib, applemusic, musixmatch）
- 歌词嵌入音频文件（MP3/OGG/FLAC/M4A）
- 从音频文件提取歌词
- 歌词格式转换（LRC/TTML/SRT/JSON）
- 歌词模式选择（original/merged/translation）
- 批量获取和嵌入歌词
- 歌词时长匹配度计算

**主要方法**:

```python
def fetch_lyrics(file_path: str, provider: str = 'netease', lyric_mode: str = 'merged') -> dict | None
```
- 获取歌词，支持多提供商和多歌词模式

```python
def search_songs(file_path: str, provider: str = 'netease') -> list[dict]
```
- 搜索歌曲（返回结果列表供用户选择）

```python
def fetch_lyric_by_id(song_id: int | str, provider: str, lyric_mode: str = 'merged') -> dict | None
```
- 根据歌曲 ID 获取歌词

```python
def embed_lyrics(file_path: str, lyrics: str, format: str = 'lrc', mode: str = 'embed_only') -> bool
```
- 嵌入歌词到音频文件，支持 embed_only 和 embed_and_lrc 两种模式

```python
def extract_lyrics(file_path: str) -> dict | None
```
- 从音频文件提取已嵌入的歌词

```python
def convert_lyrics(lyrics: str, from_format: str, to_format: str) -> str | None
```
- 歌词格式转换

```python
def batch_fetch_lyrics(file_paths: list[str], provider: str) -> dict
```
- 批量获取歌词

```python
def batch_embed_lyrics(file_lyrics_pairs: list[tuple], format: str, mode: str) -> dict
```
- 批量嵌入歌词

**歌词数据结构**:
```python
{
    'plain_lyrics': str,      # 纯文本歌词
    'synced_lyrics': str,     # 同步歌词（LRC 格式）
    'provider': str,          # 提供商名称
    'track_name': str,        # 歌曲名称
    'artist_name': str,       # 艺术家
    'album_name': str,        # 专辑名
    'duration': int           # 时长（秒）
}
```

#### 4.6.2 MusicLibraryManager 模块

**模块路径**: `auto_tag/music_library_manager.py`

**主要功能**:
- 全局单例管理 pymusiclibrary API 实例
- 确保主线程初始化，避免线程安全问题
- Monkey Patch 修复 pymusiclibrary 库的 Bug

**主要函数**:
```python
def initialize() -> None
def get_netease_api() -> NeteaseCloudMusicApi | None
def get_kugou_api() -> KuGouMusicApi | None
def is_available() -> bool
```

### 4.7 MusicManagerPage - 音乐管理页面

#### 4.7.1 类定义

**类**: `MusicManagerPage(QWidget)`
**模块路径**: `auto_tag/gui/pages/music_manager_page.py`

**主要功能**:
- 文件列表展示（支持多选和批量操作）
- 元信息编辑表单（标题/艺术家/专辑/年份/流派）
- 封面管理（显示/更换封面，支持从文件或 URL）
- 歌词获取和嵌入（支持多提供商）
- 标签页切换（Metadata/Lyrics）

**属性**:
```python
files: list[str]                    # 当前加载的文件路径列表
selected_files: list[str]           # 当前选中的文件路径列表
current_file: str | None            # 当前正在编辑的文件路径
metadata_manager: MetadataManager   # 元数据管理器实例
lyric_manager: LyricManager         # 歌词管理器实例
lyric_worker: LyricWorker | None    # 歌词获取工作线程
embed_worker: LyricEmbedWorker | None # 歌词嵌入工作线程
```

#### 4.7.2 歌词工作线程

**类**: `LyricWorker(QThread)`
**模块路径**: `auto_tag/gui/workers/lyric_worker.py`

**信号**:
```python
progress_updated = Signal(int, int, int)  # 进度更新（已完成数, 总数, 剩余秒数）
lyric_fetched = Signal(str, object)       # 单文件歌词获取完成
finished_all = Signal(dict)               # 全部完成
error_occurred = Signal(str)              # 错误发生
```

**参数**:
```python
def __init__(
    file_paths: list[str],
    provider: str = "lrclib",
    song_id: int | str | None = None,
    parent=None
)
```

#### 4.7.3 SongSearchResultDialog - 搜索结果选择对话框

**类**: `SongSearchResultDialog(MessageBoxBase)`
**模块路径**: `auto_tag/gui/components/song_search_dialog.py`

**主要功能**:
- 展示搜索结果列表（歌曲名/艺术家/专辑/时长）
- 智能排序（按时长匹配度）
- 时长对比可视化（歌曲时长 vs 歌词时长）
- 重新搜索功能
- Fluent Design 动画效果
- 响应式布局

**主要方法**:
```python
def set_search_results(
    songs: list[dict],
    keyword: str = "",
    current_song_duration: float = 0.0,
    search_callback: callable | None = None
) -> None
```

### 4.8 converter 模块（更新）

#### 4.8.1 MetadataManager - 元数据管理器

**类**: `MetadataManager`
**模块路径**: `auto_tag/converter/metadata_manager.py`

**主要方法**:
```python
def read_metadata(file_path: str) -> dict[str, Any]
def write_metadata(file_path: str, metadata: dict[str, Any]) -> bool
def parse_filename(filename: str) -> dict[str, str]
def batch_edit(file_paths: list[str], metadata: dict[str, Any]) -> dict[str, bool]
def get_cover(file_path: str) -> bytes | None
def set_cover(file_path: str, cover_data: bytes) -> bool
```

#### 4.8.2 CustomFormatManager - 自定义格式管理器

**类**: `CustomFormatManager`
**模块路径**: `auto_tag/converter/custom_format.py`

**内置格式**: mp3, flac, aac, ogg, wav, m4a, mp4, mkv, avi, mov, wmv, webm

**主要方法**:
```python
def add_format(extension: str, description: str = "") -> tuple[bool, str]
def remove_format(extension: str) -> tuple[bool, str]
def update_format(extension: str, new_description: str) -> tuple[bool, str]
def get_all_extensions() -> list[str]
def to_dict_list() -> list[dict]
def from_dict_list(data: list[dict]) -> CustomFormatManager
```

---

## 5. 数据流与架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户界面层                                │
│  ┌─────────────────┐    ┌──────────────────────────────────┐    │
│  │   CLI (main.py) │    │   GUI (PySide6 + Fluent)         │    │
│  │                 │    │  ┌───────────────────────────┐   │    │
│  │                 │    │  │ MainWindow                │   │    │
│  │                 │    │  │ ├─ HomePage               │   │    │
│  │                 │    │  │ ├─ ConverterPage          │   │    │
│  │                 │    │  │ ├─ MusicManagerPage       │   │    │
│  │                 │    │  │ └─ SettingsPage           │   │    │
│  │                 │    │  └───────────────────────────┘   │    │
│  └────────┬────────┘    └──────────────┬───────────────────┘    │
└───────────┼─────────────────────────────┼───────────────────────┘
            │                             │
            └──────────────┬──────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     业务逻辑层                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           audio_recognize.py                             │  │
│  │  ┌─────────────────┐  ┌─────────────────────────────┐   │  │
│  │  │ 文件遍历与收集  │─▶│ Shazam API 识别与重试     │   │  │
│  │  └─────────────────┘  └───────────┬─────────────────┘   │  │
│  │                                   ▼                      │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │ 元数据提取 → 文件名生成 → 目录结构构建        │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           lyric/manager.py (LyricManager)               │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │ 多平台搜索 → 歌词获取 → 格式转换 → 嵌入音频   │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           converter/converter.py                         │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │ 格式检测 → ffmpeg 转换 → 元数据保留           │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     数据处理层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │   shazamio   │  │   mutagen    │  │     eyed3          │    │
│  │ (音频识别)   │  │ (OGG 标签)   │  │ (MP3 标签)         │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  soundfile   │  │   unidecode  │  │    ffmpeg          │    │
│  │ (OGG→WAV)    │  │ (字符转换)   │  │ (格式转换)         │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │     pymusiclibrary (NeteaseCloudMusicApi/KuGouMusicApi)  │   │
│  │     (网易云/酷狗音乐 API 集成)                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. 关键设计决策

### 6.1 OGG 文件处理策略

```
OGG 文件 → 尝试转换为 WAV → Shazam 识别
                    ↓ 失败
              直接使用原始 OGG → Shazam 识别
```

### 6.2 文件命名规则

**普通模式**: `Title - Artist - Album.ext`  
**Plex 模式**: `Artist/Album/Title.ext`

### 6.3 重试机制

- 默认重试 3 次
- 每次重试间隔 10 秒
- 支持调试输出（`--trace`）

### 6.4 并发模型

- 使用 `asyncio` 进行异步 I/O
- GUI 使用 QThread 运行异步任务
- 进度条实时更新（信号槽机制）

### 6.5 国际化设计

- 默认语言：中文（zh）
- 配置持久化到用户目录
- 实时语言切换无需重启

### 6.6 歌词获取策略

```
音频文件 → 提取元数据 → 搜索歌曲 → 用户选择（网易云/酷狗）
                    ↓ 自动匹配
              多提供商获取歌词（LRCLib/Apple/MusixMatch）
                    ↓
              歌词嵌入（USLT/SYLT/LYRICS 帧）
```

**支持的歌词提供商**:
- **网易云音乐**: 支持搜索、多选、三种歌词模式（original/merged/translation）
- **酷狗音乐**: 支持搜索、自动获取歌词
- **LRCLib**: 开源歌词库，直接获取
- **Apple Music**: Apple 音乐歌词
- **MusixMatch**: 第三方歌词服务

### 6.7 线程安全设计

- pymusiclibrary 使用全局单例模式，主线程预初始化
- 避免子线程中的内存访问违规（access violation）
- Monkey Patch 修复原生库初始化失败时的 AttributeError
- LyricWorker 在线程中调用预初始化的 LyricManager 实例

---

## 7. 测试策略

### 7.1 测试框架

- **pytest** + **pytest-asyncio**
- 使用 `DummyShazam` 模拟 Shazam API

### 7.2 测试用例

| 测试名称 | 覆盖场景 |
|----------|----------|
| `test_recognize_and_rename_file_flat` | 普通重命名 |
| `test_recognize_and_rename_file_with_plex` | Plex 目录结构 |
| `test_copy_to_directory_flat` | 复制模式（普通） |
| `test_copy_to_directory_with_plex` | 复制模式（Plex） |
| `test_lyric_fetch_and_embed` | 歌词获取和嵌入 |
| `test_lyric_mode_selection` | 三种歌词模式选择 |
| `test_lyric_format_conversion` | 歌词格式转换 |
| `test_song_search_dialog` | 搜索结果选择对话框 |
| `test_metadata_manager` | 元数据读取和写入 |
| `test_custom_format_manager` | 自定义格式管理 |
| `test_converter_worker` | 异步音频转换 |

### 7.3 Mock 策略

```python
@pytest.fixture(autouse=True)
def patch_tag_functions(monkeypatch):
    monkeypatch.setattr(audio_recognize, "update_mp3_tags", lambda *a, **k: None)
    monkeypatch.setattr(audio_recognize, "update_mp3_cover_art", lambda *a, **k: None)
    monkeypatch.setattr(audio_recognize, "update_ogg_tags", lambda *a, **k: None)
```

### 7.4 歌词测试策略

**测试覆盖场景**:
- 正常歌词获取（各提供商）
- 三种歌词模式（original/merged/translation）
- 歌词嵌入和提取（MP3/OGG/FLAC/M4A）
- 歌词格式转换（LRC/TTML/SRT/JSON）
- 批量获取和嵌入
- 时长匹配度计算
- 线程安全（LyricWorker 异步操作）
- 主线程预初始化（MusicLibraryManager）

**Mock 策略**:
```python
# Mock 音乐平台 API 调用
@pytest.fixture
def mock_netease_api(monkeypatch):
    monkeypatch.setattr(
        neteaseCloudMusicApi.NeteaseCloudMusicApi, 
        "search", 
        mock_search_response
    )
    monkeypatch.setattr(
        neteaseCloudMusicApi.NeteaseCloudMusicApi, 
        "lyric", 
        mock_lyric_response
    )
```

---

## 8. 构建与部署

### 8.1 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/muzyyue/mp3ShazamAutoTag.git
cd mp3ShazamAutoTag

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install .

# 安装开发依赖
pip install pytest pytest-asyncio
```

### 8.2 运行测试

```bash
pytest
```

### 8.3 构建可执行文件

```bash
# 使用构建脚本
python build_tools/build_exe.py

# 或手动构建
pip install pyinstaller
pyinstaller --onefile --noconsole --icon="assets/auto_tag.ico" --add-data="assets/auto_tag.ico;assets" main.py
```

### 8.4 FFmpeg 环境配置

音频转换模块依赖 FFmpeg，需要提前安装并配置到系统 PATH 中。

#### 8.4.1 Windows 安装方法

**方法一：官网下载（推荐）**
1. 访问 [FFmpeg 官网](https://ffmpeg.org/download.html)
2. 选择 Windows 版本，下载预编译的二进制文件
3. 解压到任意目录（如 `C:\ffmpeg`）
4. 将 `C:\ffmpeg\bin` 添加到系统 PATH 环境变量
5. 重启终端或命令行窗口

**方法二：使用 Chocolatey**
```powershell
# 安装 Chocolatey（如果未安装）
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 安装 FFmpeg
choco install ffmpeg
```

**方法三：使用 Scoop**
```powershell
# 安装 Scoop（如果未安装）
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# 安装 FFmpeg
scoop install ffmpeg
```

#### 8.4.2 macOS 安装方法

**方法一：使用 Homebrew（推荐）**
```bash
# 安装 Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 FFmpeg
brew install ffmpeg
```

**方法二：官网下载**
1. 访问 [FFmpeg 官网](https://ffmpeg.org/download.html)
2. 选择 macOS 版本，下载预编译的二进制文件
3. 解压并将 `ffmpeg` 可执行文件移动到 `/usr/local/bin/`
   ```bash
   sudo mv ffmpeg /usr/local/bin/
   sudo mv ffprobe /usr/local/bin/
   ```

#### 8.4.3 Linux 安装方法

**Ubuntu/Debian**
```bash
sudo apt update
sudo apt install ffmpeg
```

**CentOS/RHEL/Fedora**
```bash
# CentOS/RHEL
sudo yum install epel-release
sudo yum install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

**Arch Linux**
```bash
sudo pacman -S ffmpeg
```

#### 8.4.4 验证安装

安装完成后，运行以下命令验证 FFmpeg 是否正确安装：

```bash
# 检查 FFmpeg 版本
ffmpeg -version

# 检查 FFprobe 版本
ffprobe -version
```

如果显示版本信息，说明安装成功。如果提示"命令未找到"，请检查 PATH 环境变量配置。

---

## 9. 已知问题

1. **Python 3.11/3.12 兼容性问题** - 见 [Issue #1](https://github.com/davidAlgis/mp3ShazamAutoTag/issues/1)
2. **macOS shazamio 安装问题** - 见 [Issue #5](https://github.com/davidAlgis/mp3ShazamAutoTag/issues/5)
3. **杀毒软件误报** - 可执行文件可能被隔离（源代码无害）

---

## 10. 扩展开发指南

### 10.1 添加新的音频格式支持

1. 在 `audio_recognize.py` 中添加格式检测逻辑
2. 实现对应的标签更新函数
3. 更新 CLI 参数默认值
4. 添加测试用例

### 10.2 自定义命名规则

修改 `recognize_and_rename_file()` 中的文件名生成逻辑：

```python
if plex_structure:
    new_name = f"{s_title}{ext}"
else:
    new_name = f"{s_title} - {s_artist} - {s_album}{ext}"
```

### 10.3 添加新的元数据源

在 `find_deepest_metadata_key()` 中扩展搜索逻辑，或添加新的元数据提取函数。

### 10.4 添加新的翻译语言

1. 在 `auto_tag/gui/i18n/locales/` 创建新的 JSON 文件（如 `ja.json`）
2. 在 `settings_page.py` 中添加语言选项
3. 更新 `lang_index_map` 和 `lang_code_map`

### 10.5 添加新的歌词提供商

1. 在 `auto_tag/lyric/provider.py` 中添加提供商配置
2. 在 `LyricManager` 中实现对应的获取逻辑
3. 更新 `music_manager_page.py` 的动态加载列表
4. 添加对应的测试用例

### 10.6 歌词获取流程

**网易云/酷狗音乐**:
```python
# 1. 搜索歌曲（返回结果列表）
songs = lyric_manager.search_songs(file_path, 'netease')

# 2. 用户选择歌曲（通过 SongSearchResultDialog）
song_id = dialog.selected_song_id

# 3. 根据 ID 获取歌词
lyrics = lyric_manager.fetch_lyric_by_id(song_id, 'netease', lyric_mode='merged')

# 4. 嵌入歌词
success = lyric_manager.embed_lyrics(file_path, lyrics['synced_lyrics'], 'lrc')
```

**其他提供商（LRCLib/Apple/MusixMatch）**:
```python
# 直接获取歌词（无需搜索）
lyrics = lyric_manager.fetch_lyrics(file_path, 'lrclib')
success = lyric_manager.embed_lyrics(file_path, lyrics['synced_lyrics'], 'lrc')
```

### 10.7 音频转换使用示例

#### 10.7.1 基础单文件转换

将视频文件转换为 MP3 格式：

```python
from auto_tag.converter import AudioConverter
from auto_tag.converter.config import ConverterConfig, QualityPreset

# 创建转换器实例
converter = AudioConverter()

# 创建配置
config = ConverterConfig()
config.set_output_format("mp3", QualityPreset.HIGH)

# 执行转换
success = converter.convert_file(
    input_path="video.mp4",
    output_path="audio.mp3",
    config=config
)

if success:
    print("转换成功！")
else:
    print("转换失败")
```

#### 10.5.2 批量转换音频文件

批量将多个视频文件转换为 FLAC 格式：

```python
from auto_tag.converter import AudioConverter
from auto_tag.converter.config import ConverterConfig, QualityPreset

converter = AudioConverter()
config = ConverterConfig()
config.set_output_format("flac", QualityPreset.LOSSLESS)

# 文件列表
files = [
    "video1.mp4",
    "video2.avi",
    "video3.mkv"
]

# 批量转换
results = converter.convert_batch(
    files=files,
    output_dir="output/",
    config=config,
    progress_callback=lambda i, total, f: print(f"处理 {i}/{total}: {f}")
)

# 统计结果
success_count = sum(1 for v in results.values() if v)
print(f"成功转换 {success_count}/{len(files)} 个文件")
```

#### 10.5.3 自定义转换参数

使用自定义参数进行转换：

```python
from auto_tag.converter import AudioConverter
from auto_tag.converter.config import ConverterConfig, FormatConfig, OutputFormat

converter = AudioConverter()

# 创建自定义配置
config = ConverterConfig()
config.output_format = FormatConfig(
    format=OutputFormat.MP3,
    bitrate=256,           # 256 kbps
    sample_rate=48000,     # 48 kHz
    channels=2,            # 立体声
    codec="libmp3lame"     # MP3 编解码器
)
config.overwrite_existing = True

# 执行转换
success = converter.convert_file(
    input_path="input.wav",
    output_path="output.mp3",
    config=config
)
```

#### 10.5.4 GUI 中使用异步转换

在 GUI 应用中使用 ConverterWorker 进行异步转换：

```python
from PySide6.QtWidgets import QMainWindow, QProgressBar
from auto_tag.converter.workers import ConverterWorker
from auto_tag.converter.config import ConverterConfig

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.progress_bar = QProgressBar()
        
    def start_conversion(self, files, output_dir):
        # 创建配置
        config = ConverterConfig()
        config.set_output_format("mp3")
        
        # 创建工作线程
        self.worker = ConverterWorker(
            files=files,
            output_dir=output_dir,
            config=config
        )
        
        # 连接信号
        self.worker.progress_updated.connect(self.on_progress)
        self.worker.file_converted.connect(self.on_file_done)
        self.worker.finished_all.connect(self.on_finished)
        self.worker.error_occurred.connect(self.on_error)
        
        # 启动线程
        self.worker.start()
    
    def on_progress(self, current, total, filename):
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        print(f"处理进度: {current}/{total} - {filename}")
    
    def on_file_done(self, file_path, success, error):
        if success:
            print(f"转换成功: {file_path}")
        else:
            print(f"转换失败: {file_path}, 错误: {error}")
    
    def on_finished(self, results):
        success_count = sum(1 for r in results if r["success"])
        print(f"全部完成！成功 {success_count}/{len(results)} 个文件")
    
    def on_error(self, error_msg):
        print(f"错误: {error_msg}")
    
    def stop_conversion(self):
        if hasattr(self, 'worker'):
            self.worker.stop()
```

#### 10.5.5 检测文件格式

检测音频/视频文件的真实格式：

```python
from auto_tag.converter import AudioConverter

converter = AudioConverter()

# 检测文件格式
files = ["song.mp3", "video.mp4", "unknown.dat"]

for file_path in files:
    format_name = converter.detect_format(file_path)
    if format_name:
        print(f"{file_path}: {format_name}")
    else:
        print(f"{file_path}: 无法检测格式")
```

---

## 11. API 参考

### 11.1 Shazam 响应结构

```json
{
  "track": {
    "title": "歌曲标题",
    "subtitle": "艺术家",
    "images": {
      "coverart": "封面图片URL"
    },
    "sections": [
      {
        "metadata": [
          {"title": "Album", "text": "专辑名"}
        ]
      }
    ]
  }
}
```

### 11.2 LyricManager API

#### 11.2.1 类定义

```python
class LyricManager:
    """歌词管理器，支持多平台歌词获取、嵌入和格式转换"""
```

#### 11.2.2 主要方法

**`fetch_lyrics(file_path: str, provider: str = 'netease', lyric_mode: str = 'merged') -> dict | None`**

从指定提供商获取歌词。

**Args**:
- `file_path`: 音频文件路径
- `provider`: 提供商名称（'netease', 'kugou', 'lrclib', 'applemusic', 'musixmatch'）
- `lyric_mode`: 歌词模式（'original' | 'merged' | 'translation'）

**Returns**:
- `dict | None`: 歌词数据字典，包含 synced_lyrics, plain_lyrics, provider 等字段

---

**`search_songs(file_path: str, provider: str = 'netease') -> list[dict]`**

搜索歌曲并返回结果列表供用户选择。

**Returns**:
- `list[dict]`: 搜索结果列表，每个字典包含 id, name, artist, album, duration

---

**`fetch_lyric_by_id(song_id: int | str, provider: str, lyric_mode: str = 'merged') -> dict | None`**

根据歌曲 ID 获取歌词。

---

**`embed_lyrics(file_path: str, lyrics: str, format: str = 'lrc', mode: str = 'embed_only') -> bool`**

将歌词嵌入到音频文件。

**Args**:
- `file_path`: 音频文件路径
- `lyrics`: 歌词内容（LRC/TTML/SRT/JSON 格式）
- `format`: 歌词格式
- `mode`: 嵌入模式（'embed_only' | 'embed_and_lrc'）

**Returns**:
- `bool`: 嵌入成功返回 True

---

**`extract_lyrics(file_path: str) -> dict | None`**

从音频文件提取已嵌入的歌词。

---

**`convert_lyrics(lyrics: str, from_format: str, to_format: str) -> str | None`**

转换歌词格式。

---

**`parse_lrc_duration(lrc_text: str) -> float`** (静态方法)

解析 LRC 歌词文本，提取总时长（秒）。

---

**`calculate_duration_match_ratio(song_duration: float, lyric_duration: float, threshold: float = 0.10) -> dict`** (静态方法)

计算歌曲时长与歌词时长的匹配度。

### 11.3 MusicLibraryManager API

#### 11.3.1 全局函数

**`initialize() -> None`**

在主线程预初始化 MusicLibrary API 实例。

**`get_netease_api() -> NeteaseCloudMusicApi | None`**

获取 NetEase API 实例。

**`get_kugou_api() -> KuGouMusicApi | None`**

获取 KuGou API 实例。

**`is_available() -> bool`**

检查 MusicLibrary 是否可用。

### 11.4 MetadataManager API

#### 11.4.1 类定义

```python
class MetadataManager:
    """音频文件元数据管理器，支持 MP3/OGG 格式"""
```

#### 11.4.2 主要方法

**`read_metadata(file_path: str) -> dict[str, Any]`**

读取音频文件的元数据。

**Returns**:
- `dict`: 包含 title, artist, album, year, genre, cover 的字典

---

**`write_metadata(file_path: str, metadata: dict[str, Any]) -> bool`**

写入元数据到音频文件。

---

**`parse_filename(filename: str) -> dict[str, str]`**

从文件名解析元数据。

**Returns**:
- `dict`: 包含 title, artist, album 的字典

---

**`batch_edit(file_paths: list[str], metadata: dict[str, Any]) -> dict[str, bool]`**

批量编辑多个音频文件的元数据。

---

**`get_cover(file_path: str) -> bytes | None`**

获取音频文件的封面图片数据。

---

**`set_cover(file_path: str, cover_data: bytes) -> bool`**

设置音频文件的封面图片。

### 11.5 AudioConverter API

#### 11.5.1 类属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `SUPPORTED_INPUT_FORMATS` | set[str] | 支持的输入格式集合 |
| `SUPPORTED_OUTPUT_FORMATS` | set[str] | 支持的输出格式集合 |

#### 11.5.2 方法

**`__init__()`**

初始化音频转换器，检查 FFmpeg 是否可用。

**Raises**:
- `RuntimeError`: 如果 FFmpeg 未安装或不在系统 PATH 中

---

**`detect_format(file_path: str) -> str | None`**

检测文件的音频/视频格式。

**Args**:
- `file_path`: 文件路径

**Returns**:
- `str | None`: 检测到的格式名称（如 'mp3', 'mp4'），如果检测失败返回 None

**Example**:
```python
converter = AudioConverter()
format_name = converter.detect_format("song.mp3")
print(format_name)  # 输出: 'mp3'
```

---

**`convert_file(input_path: str, output_path: str, config: ConverterConfig, progress_callback: Callable[[float], None] | None = None) -> bool`**

转换单个音频/视频文件。

**Args**:
- `input_path`: 输入文件路径
- `output_path`: 输出文件路径
- `config`: 转换配置对象
- `progress_callback`: 进度回调函数，接收 0.0-1.0 之间的进度值

**Returns**:
- `bool`: 转换成功返回 True，失败返回 False

**Example**:
```python
converter = AudioConverter()
config = ConverterConfig()
success = converter.convert_file(
    "input.mp4",
    "output.mp3",
    config,
    lambda p: print(f"进度: {p*100:.1f}%")
)
```

---

**`convert_batch(files: list[str], output_dir: str, config: ConverterConfig, progress_callback: Callable[[int, int, str], None] | None = None) -> dict[str, bool]`**

批量转换音频/视频文件。

**Args**:
- `files`: 输入文件路径列表
- `output_dir`: 输出目录路径
- `config`: 转换配置对象
- `progress_callback`: 进度回调函数，参数为 (当前索引, 总数, 当前文件路径)

**Returns**:
- `dict[str, bool]`: 转换结果字典，键为输入文件路径，值为转换是否成功

**Example**:
```python
converter = AudioConverter()
config = ConverterConfig()
files = ["song1.mp4", "song2.avi"]
results = converter.convert_batch(
    files,
    "output/",
    config,
    lambda i, total, f: print(f"处理 {i}/{total}: {f}")
)
```

### 11.6 ConverterConfig API

#### 11.6.1 类定义

```python
@dataclass
class ConverterConfig:
    output_format: FormatConfig
    output_directory: Optional[str]
    quality_preset: QualityPreset
    preserve_metadata: bool
    overwrite_existing: bool
    filename_template: str
    supported_input_formats: list[str]
```

#### 11.6.2 方法

**`set_output_format(format_name: str, preset: QualityPreset = QualityPreset.HIGH) -> None`**

设置输出格式。

**Args**:
- `format_name`: 格式名称（mp3, flac, aac 等）
- `preset`: 质量预设（默认 HIGH）

**Raises**:
- `ValueError`: 如果格式名称不支持

---

**`get_ffmpeg_args() -> list[str]`**

获取 FFmpeg 命令行参数。

**Returns**:
- `list[str]`: FFmpeg 参数列表

---

**`get_output_extension() -> str`**

获取输出文件扩展名。

**Returns**:
- `str`: 文件扩展名（包含点号）

### 11.7 ConverterWorker API

#### 11.7.1 信号

| 信号名 | 参数类型 | 说明 |
|--------|----------|------|
| `progress_updated` | `(int, int, str)` | 进度更新（当前索引, 总数, 当前文件名） |
| `file_converted` | `(str, bool, str)` | 单文件转换完成（文件路径, 是否成功, 错误信息） |
| `finished_all` | `(list)` | 所有文件转换完成（结果列表） |
| `error_occurred` | `(str)` | 错误发生（错误消息） |

#### 11.7.2 方法

**`__init__(files: list[str], output_dir: str, config: ConverterConfig, parent=None)`**

初始化转换工作线程。

**Args**:
- `files`: 要转换的文件路径列表
- `output_dir`: 输出目录路径
- `config`: 转换配置对象
- `parent`: 父对象，用于 Qt 对象树管理

---

**`run() -> None`**

执行转换任务（由 Qt 框架自动调用，使用 `start()` 方法启动线程）。

---

**`stop() -> None`**

停止转换操作（设置停止标志，线程会在当前文件转换完成后退出）。

### 11.8 FormatConfig API

#### 11.8.1 类定义

```python
@dataclass
class FormatConfig:
    format: OutputFormat
    bitrate: Optional[int]
    sample_rate: Optional[int]
    channels: Optional[int]
    codec: Optional[str]
```

#### 11.8.2 枚举类型

**OutputFormat** - 输出音频格式枚举:
- `MP3 = "mp3"`
- `FLAC = "flac"`
- `AAC = "aac"`
- `OGG = "ogg"`
- `WAV = "wav"`
- `M4A = "m4a"`

**QualityPreset** - 质量预设枚举:
- `LOW = "low"` - 低质量
- `MEDIUM = "medium"` - 中等质量
- `HIGH = "high"` - 高质量
- `LOSSLESS = "lossless"` - 无损质量
- `CUSTOM = "custom"` - 自定义

### 11.9 SongSearchResultDialog API

#### 11.9.1 类定义

```python
class SongSearchResultDialog(MessageBoxBase):
    """搜索结果选择对话框（Fluent Design 风格）"""
```

#### 11.9.2 信号

| 信号名 | 参数类型 | 说明 |
|--------|----------|------|
| `song_selected` | `(dict)` | 歌曲选择信号，参数为选中的歌曲信息 |

#### 11.9.3 主要方法

**`set_search_results(songs: list[dict], keyword: str = "", current_song_duration: float = 0.0, search_callback: callable | None = None) -> None`**

设置搜索结果数据。

**Args**:
- `songs`: 搜索结果列表（id, name, artist, album, duration）
- `keyword`: 搜索关键词
- `current_song_duration`: 当前歌曲实际时长（秒），用于歌词时长对比
- `search_callback`: 重新搜索回调函数

**Properties**:
- `selected_song`: 选中的歌曲信息
- `selected_song_id`: 选中歌曲的 ID

**`update_duration_comparison(song_duration: float, lyric_text: str | None = None, lyric_duration: float | None = None) -> None`**

更新时长对比信息（歌曲时长 vs 歌词时长）。

### 11.10 LyricWorker API

#### 11.10.1 类定义

```python
class LyricWorker(QThread):
    """歌词获取工作线程"""
```

#### 11.10.2 信号

| 信号名 | 参数类型 | 说明 |
|--------|----------|------|
| `progress_updated` | `(int, int, int)` | 进度更新（已完成数, 总数, 剩余秒数） |
| `lyric_fetched` | `(str, object)` | 单文件歌词获取完成 |
| `finished_all` | `(dict)` | 全部完成 |
| `error_occurred` | `(str)` | 错误发生 |

#### 11.10.3 构造函数

```python
def __init__(
    file_paths: list[str],
    provider: str = "lrclib",
    song_id: int | str | None = None,
    parent=None
)
```

### 11.11 LyricEmbedWorker API

#### 11.11.1 类定义

```python
class LyricEmbedWorker(QThread):
    """歌词嵌入工作线程"""
```

#### 11.11.2 信号

| 信号名 | 参数类型 | 说明 |
|--------|----------|------|
| `progress_updated` | `(int, int, int)` | 进度更新 |
| `lyric_embedded` | `(str, bool)` | 单文件歌词嵌入完成 |
| `finished_all` | `(dict)` | 全部完成 |
| `error_occurred` | `(str)` | 错误发生 |

#### 11.11.3 构造函数

```python
def __init__(
    file_lyrics_pairs: list[tuple[str, str]],
    format: str = "lrc",
    parent=None
)
```

### 11.12 CustomFormatManager API

#### 11.12.1 类定义

```python
class CustomFormatManager:
    """自定义格式管理器"""
```

#### 11.12.2 内置格式

**音频格式**: mp3, flac, aac, ogg, wav, m4a  
**视频格式**: mp4, mkv, avi, mov, wmv, webm

#### 11.12.3 主要方法

**`add_format(extension: str, description: str = "") -> tuple[bool, str]`**

添加新的自定义格式。

---

**`remove_format(extension: str) -> tuple[bool, str]`**

删除自定义格式（内置格式不可删除）。

---

**`get_all_extensions() -> list[str]`**

获取所有支持的格式扩展名（包括内置和自定义）。

---

**`to_dict_list() -> list[dict]`**

将自定义格式转换为字典列表（用于序列化到 config.json）。

---

**`from_dict_list(data: list[dict]) -> CustomFormatManager`** (类方法)

从字典列表创建格式管理器（用于从 config.json 反序列化）。

---

*文档生成日期: 2026-04-20*
