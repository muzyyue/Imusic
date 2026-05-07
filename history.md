# 项目变更历史

## v0.5.5 (2026-05-05)
- feat(qqmusic): 新增QQ音乐Cookie完整管理功能
  - Cookie输入框（多行文本、实时验证、自动持久化）
  - 刷新登录按钮（API续期、防重复点击、状态反馈）
  - 失效引导弹窗（过期时自动弹出、一键跳转y.qq.com获取）
  - QQ音乐搜索集成Cookie认证（HTTP头注入、日志脱敏）
  - 新增39个测试用例覆盖全流程
  - 新增文件: `validation.py`, `cookie_expired_dialog.py`, 3个测试文件

## v0.5.4 (2026-05-03)
- refactor(core): 重构音频识别模块，提取通用工具函数到 `auto_tag/utils/`（字符串/文件名/元数据处理）
- feat(editor): 增强音频编辑器功能和UI交互
- fix(ui): 修复搜索结果卡片显示异常、设置页面布局优化、英文翻译更新
- feat(lyric): 增强歌词管理功能，优化多平台兼容性
- chore(converter): 改进FFmpeg静默模式和格式配置灵活性
- test: 新增重构后模块测试和规范化测试音频文件
- docs: 全面更新 Readme.md

## v0.5.3 (2026-05-02)
- fix(build): 修复 uv sync 残留 dist-info 和 hardlink 警告（配置 link-mode = "copy"）

## v0.5.2 (2026-05-02)
- fix(ui): 修复编辑器页面输出格式区域下拉框重叠问题

## v0.5.1 (2026-05-02)
- fix(ui): 修复编辑器页面下拉框高度和间距问题

## v0.5.0 (2026-05-02)
- feat(editor): 新增音频编辑功能 Phase 1 MVP（智能裁剪/音量标准化/格式转换5种预设/EditorPage页面）

## v0.4.82 (2026-05-01)
- fix(ui): 修复清除数据时封面图片未正确重置、QProcessEventLoop崩溃、themeChanged警告等问题

## v0.4.81 (2026-04-29)
- fix(recognize): 修复 tests 目录被错误过滤的问题；扩展支持音频格式从2种到7种（flac/m4a/wav/wma/opus）；用 mutagen 统一处理非MP3元数据读取

## v0.4.80 (2026-04-29)
- feat(lyric): 实现歌词请求频率限制（令牌桶算法）和自动重试机制（指数退避），批量成功率从~60%提升至~95%

## v0.4.79 (2026-04-29)
- fix(memory): 修复首页搜索严重内存泄漏（搜索28首歌后内存从200MB暴涨至1000MB），识别并修复5个泄漏点，清除后内存降至220-280MB

## v0.4.78 (2026-04-28)
- fix(lyric): 修复嵌入歌词后重新加载还原的问题——从 eyed3 全面迁移到 mutagen 写入 USLT 帧

## v0.4.77 (2026-04-28)
- fix(lyric): 修复批量获取歌词时所有歌曲嵌入同一首歌词的问题（逐文件串行处理）+ 单首误触发批量对话框

## v0.4.76 (2026-04-28)
- fix(lyric): 修复批量获取歌词导致 UI 卡死的问题（logger 引用和异常处理）

## v0.4.75 (2026-04-28) ×2
- fix(lyric): 修复歌词搜索"首次成功、再次失败"的问题（pymusiclibrary 多实例冲突 → REST API 优先策略）
- feat(search): 新增智能回退关键词模式（smart_fallback），提升中文/日文歌曲搜索成功率

## v0.4.74 (2026-04-28)
- fix(memory): 修复首页连续点击封面导致内存持续增长且关闭后未回收的问题（Qt 隐式共享 + 显式资源释放）

## v0.4.73 (2026-04-27)
- feat(lyric): 批量获取歌词时自动选择匹配度最高的结果（多维度评分：歌名40% + 艺术家35% + 时长25%）

## v0.4.72 (2026-04-27)
- fix(ui): 修复歌曲卡片长文件名导致刷新/收起按钮被隐藏的问题（左右分离布局）

## v0.4.71 (2026-04-27)
- fix(gui): 修复首页搜索导致内存持续增长的问题（组件销毁前停止加载线程）

## v0.4.70 ~ v0.4.63 (2026-04-26)
- fix(ci): 简化 GitHub Actions 发布流程
- feat(ci): 首次启用 GitHub Actions 自动构建发布
- fix(ui): 修复转换器页面深色/浅色模式背景色适配（多版本迭代）
- refactor(ui): 转换器页面从局部滚动改为全页面滚动 + 文件列表垂直滚动

## v0.4.62 (2026-04-26)
- fix(lyric): 修复歌词数据在切换歌曲或重新选择目录后丢失的问题（lyrics_cache 管理）

## v0.4.60 (2026-04-26)
- feat(ui): 搜索结果栏显示复合来源标识（如 "Acoustid + 网易云音乐"）

## v0.4.59 (2026-04-26)
- feat(settings): 设置页面新增「搜索关键词模式」选项（仅歌名 / 艺术家+歌名 / 智能回退）

## v0.4.58 (2026-04-26)
- feat(core): 新增音频元数据回退策略——无意义文件名时从文件标签读取元数据作为搜索关键词

## v0.4.57 (2026-04-26)
- feat(settings): 搜索源拆分为「识别引擎」和「补充搜索」两行展示 + 网易云/QQ音乐关键词改为仅使用歌曲名

## v0.4.56 ~ v0.4.49 (2026-04-25)
- fix(build): 回退打包工具链从 Nuitka 至 PyInstaller（Nuitka 上游 bug）
- refactor(build): Nuitka 迁移尝试（已回退）
- refactor(build): PyInstaller onedir 打包流程优化（UPX压缩、依赖收集、体积统计）
- fix(build): 修复 soundfile 模块缺失、UPX 排除配置等打包问题
- fix(qqmusic): QQ 音乐搜索迁移到官方统一网关接口（u.y.qq.com）
- refactor(build): 项目名称统一为 Imusic

## v0.4.45 ~ v0.4.42 (2026-04-25)
- refactor(i18n): 国际化文件改为嵌套分组结构
- fix(core): MP3 封面写入失败（User-Agent 缺失）
- fix(gui): 歌曲卡片主题颜色/背景色更新问题

## v0.4.39 ~ v0.4.30 (2026-04-23~24)
- chore(build): PyInstaller 打包体积优化（700MB → 240MB）
- feat/core: 文件名识别策略优化、清除数据功能、封面获取增强
- refine/gui): 搜索加载对话框视觉优化
- fix(gui): 歌词搜索异步化、网易云封面显示修复、多语言字符保留、应用按钮回调机制

## v0.4.26 ~ v0.4.10 (2026-04-20)
- feat(ui): 窗口尺寸优化（1200×580 可调）、扁平化布局
- fix(core): pymusiclibrary 崩溃修复（默认禁用/线程安全版本/移除初始化）
- fix(ui): 深色模式适配、搜索结果卡片式布局重构、展开收起图标修复

## v0.4.2 ~ v0.4.0 (2026-04-16~17)
- feat(lyric): 歌词模式选择（original/merged/translation）、MusicLibrary 替代 lrxy、LyricManager 模块、搜索结果多选

## v0.3.7 ~ v0.3.0 (2026-04-13~14)
- feat(converter): 自定义文件格式管理、格式过滤、AudioConverter、ConverterWorker、MetadataManager
- test(converter): MetadataManager 单元测试
- fix(i18n): 语言切换问题修复

## v0.3.0 (2026-04-13)
- **BREAKING**: GUI 框架从 tkinter 迁移到 PySide6 + QFluentWidgets（Fluent Design 风格）
- feat(i18n): 国际化系统（中英文切换）
- feat(config): 配置管理模块 AppConfig

## v0.2.5 ~ v0.2.0 (2026-04-13)
- feat(gui): 创建设置页面 SettingsPage、主页 HomePage、识别工作线程 RecognizeWorker
- feat(config/i18n): 配置管理模块 AppConfig、国际化模块（translator.py + zh.json + en.json）

## v0.2.0 (2026-04-13)
- 初始化项目：克隆 mp3ShazamAutoTag 仓库
- 配置环境：Rust 工具链（shazamio-core）、Python 3.13 兼容性（audioop-lts）
