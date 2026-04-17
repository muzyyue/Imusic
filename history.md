# 项目变更历史

## v0.4.0 (2026-04-16)
- feat(lyric): 添加歌词获取功能的全面测试用例和修复API调用逻辑
  - 设计并实现了65个歌词获取功能测试用例，覆盖正常场景、边界条件、异常处理、性能和兼容性测试
  - 创建了完整的测试框架，包含fixtures、mock数据和预期歌词文件
  - 修复了LyricManager中的API调用逻辑，使歌词获取功能能够正确工作
  - 添加了对多种歌词格式（LRC/TTML/SRT/JSON）的支持
  - 实现了多提供商（LRCLib/Apple Music/MusixMatch）支持
- feat(lyric): 新增歌词管理模块
  - 创建 LyricManager 类封装 lrxy 库功能
  - 实现歌词获取、嵌入、提取和格式转换功能
  - 创建 LyricProvider 数据类管理提供商配置
  - 支持 LRCLib、Apple Music、MusixMatch 三个提供商
- fix(lyric): 修复歌词嵌入和提取功能
  - 移除对 lrxy 库的依赖，直接使用 eyed3 和 mutagen 嵌入歌词
  - 修复 MP3 歌词嵌入方法，使用 USLT 帧格式（网易云音乐等播放器支持）
  - 增强 MP3 歌词提取方法，支持多种标签位置（USLT/SYLT/TXXX/comments）
  - 添加备用保存方法，兼容不同版本的 eyed3
  - 解决用户手动添加歌词后无法识别的问题

## v0.3.9 (2026-04-16)
- fix(gui): 优化主窗口初始尺寸
  - 调整窗口高度从700px降至600px，减少约14%垂直空间
  - 改善低分辨率屏幕下的显示效果（1366×768适配）
  - 保持宽度1000px不变

## v0.3.8 (2026-04-15)
- feat(gui): 创建音乐管理页面 MusicManagerPage
  - 实现文件列表组件，支持多选和批量操作
  - 实现元信息编辑表单（标题、艺术家、专辑、年份、流派）
  - 实现封面显示和更换功能（从文件/从URL）
  - 实现歌词获取和嵌入功能
  - 使用 SegmentedWidget 实现标签页切换
  - 集成 MetadataManager 和 LyricManager
  - 支持批量获取歌词和批量编辑元信息
  - 实现完整的国际化支持（refresh_texts方法）

## v0.3.7 (2026-04-14)
- feat(converter): 新增自定义文件格式管理功能
  - 创建 CustomFormat 数据类和 CustomFormatManager 管理器
  - 支持用户自定义文件扩展名（如 opus、m4s 等）
  - 实现格式验证机制（扩展名检查、重复检测）
  - 提供完整的 CRUD 操作（添加、编辑、删除）
  - 配置持久化到 config.json
  - 添加 24 个单元测试全部通过
- feat(converter): 新增文件格式过滤功能
  - 音频格式组：MP3、FLAC、AAC、OGG、WAV、M4A
  - 视频格式组：MP4、MKV、AVI、MOV、WMV、WEBM
  - 提供全选/取消全选快捷按钮
  - 格式选择持久化保存
  - 添加 12 个单元测试全部通过
- fix(converter): 修复 ConverterWorker 导入错误
  - 修复 TYPE_CHECKING 导致的 NameError
  - 修复停止转换按钮无反应问题
- fix(i18n): 修复语言切换问题
  - 修复自定义格式区域文本未切换
  - 添加缺失的翻译键（confirm_delete 等）
- fix(converter): 修复删除格式对话框错误
  - 使用标准 QMessageBox 替代不支持的 MessageBox API
- test: 新增测试文件
  - test_converter_page.py：文件格式过滤和自定义格式 UI 测试
  - test_custom_format.py：自定义格式管理器测试
- test: 更新测试结果
  - 88个测试用例通过
  - 9个测试失败（已知环境问题：async测试缺插件、主题测试中文环境）
- docs: 更新国际化翻译
  - 新增 10+ 个翻译键（中英文）
  - 完善自定义格式相关的翻译

## v0.3.6 (2026-04-14)
- docs: 全面更新 Readme.md 文档
  - 添加版本徽章（Version、Python、License）
  - 更新功能特性列表，新增音频转换、国际化、Fluent Design UI
  - 重写 GUI 说明，描述 PySide6 + QFluentWidgets 界面
  - 新增 Converter Page（音频转换）功能说明
  - 新增 Settings Page（语言/主题切换）说明
  - 更新项目结构，反映最新的目录树
  - 更新依赖列表，新增 PySide6、PySide6-Fluent-Widgets、ffmpeg-python
  - 更新构建命令，支持 PySide6 打包
  - 新增 FFmpeg 依赖说明
  - 添加致谢部分

## v0.3.5 (2026-04-13)
- fix(i18n): 修复转换页面语言切换问题
  - 将所有硬编码中文替换为 tr() 翻译函数调用
  - 更新 refresh_texts() 方法正确刷新所有 UI 组件
  - 添加缺失的翻译键：converter_file_list、check
  - 更新中英文翻译文件

## v0.3.4 (2026-04-13)
- test(converter): 完善 MetadataManager 单元测试
  - 添加 test_read_metadata 测试元数据读取（MP3/OGG 格式）
  - 添加 test_write_metadata 测试元数据写入
  - 添加 test_parse_filename 测试文件名解析（三段式/两段式/单段）
  - 添加 test_batch_edit 测试批量编辑功能
  - 添加 test_get_cover/test_set_cover 测试封面图片管理
  - 使用 unittest.mock 模拟 eyed3 和 mutagen 操作
  - 测试覆盖正常流程和异常处理
  - 所有 31 个测试用例全部通过

## v0.3.3 (2026-04-13)
- feat(converter): 创建 ConverterWorker 音频转换工作线程
  - 继承 QThread 实现异步转换，避免阻塞 UI
  - 实现进度更新信号（progress_updated）
  - 实现单文件转换完成信号（file_converted）
  - 实现所有文件转换完成信号（finished_all）
  - 实现错误发生信号（error_occurred）
  - 支持取消操作（stop 方法）
  - 使用 AudioConverter 进行实际转换
  - 提供详细的错误日志记录
  - 添加完整的单元测试（11 个测试用例全部通过）

## v0.3.2 (2026-04-13)
- feat(converter): 创建 AudioConverter 音频转换器类
  - 支持输入格式：MP3/FLAC/AAC/OGG/WAV/M4A/MP4/MKV/AVI/MOV/WMV/WEBM
  - 支持输出格式：MP3/FLAC/AAC/OGG/WAV/M4A
  - 实现 detect_format() 方法检测文件格式
  - 实现 convert_file() 方法转换单个文件
  - 实现 convert_batch() 方法批量转换文件
  - 支持进度回调功能
  - 提供详细的错误日志记录
  - 添加完整的单元测试（15 个测试用例全部通过）
- chore: 更新 requirements.txt，添加 ffmpeg-python 依赖

## v0.3.1 (2026-04-13)
- feat(converter): 创建元数据管理器 MetadataManager
  - 实现读取元数据功能（read_metadata）
  - 实现写入元数据功能（write_metadata）
  - 实现文件名解析功能（parse_filename）
  - 实现批量编辑功能（batch_edit）
  - 实现封面图片管理功能（get_cover/set_cover）
  - 支持 MP3（ID3）和 OGG（Vorbis/Opus）格式
  - 使用 mutagen 和 eyed3 库处理音频标签
  - 提供完整的错误处理和日志记录

## v0.3.0 (2026-04-13)
- **BREAKING**: GUI 框架从 tkinter 迁移到 PySide6 + QFluentWidgets
- feat(gui): 完成 Fluent Design 风格 UI 重构
  - 使用 FluentWindow 作为主窗口，侧边导航栏切换页面
  - 主页（HomePage）：音频识别功能完整实现
  - 设置页面（SettingsPage）：语言和主题切换
  - 识别工作线程（RecognizeWorker）：QThread 异步处理
- feat(i18n): 国际化系统支持英文/中文切换
  - 翻译文件：en.json、zh.json
  - 翻译器：Translator 类 + tr() 便捷函数
- feat(config): 配置管理模块
  - 语言/主题偏好持久化到 ~/.mp3shazamautotag/config.json
- chore: 更新依赖
  - 新增 PySide6、PySide6-Fluent-Widgets
- chore: 更新构建脚本支持 PySide6 打包
- 删除旧的 tkinter GUI 文件

## v0.2.5 (2026-04-13)
- feat(gui): 创建设置页面 SettingsPage
  - 实现语言切换功能（English/中文）
  - 实现主题切换功能（Light/Dark/Follow System）
  - 集成 config 模块实现配置持久化
  - 集成 i18n 模块实现实时语言切换
  - 使用 QFluentWidgets 组件构建 UI
  - 添加完整的单元测试

## v0.2.4 (2026-04-13)
- feat(gui): 创建主页（音频识别页面）HomePage
  - 使用 QFluentWidgets 重写原始 tkinter GUI
  - 实现目录选择、文件识别、进度显示功能
  - 实现结果表格显示，支持勾选和双击编辑
  - 实现批量操作：全选、取消全选、应用更改
  - 支持 copy_to、tag_only、plex_structure 功能
  - 集成 RecognizeWorker 工作线程
  - 使用 tr() 函数实现国际化

## v0.2.3 (2026-04-13)
- feat(config): 创建配置管理模块 AppConfig
  - 实现语言和主题配置管理
  - 配置文件存储在 ~/.mp3shazamautotag/config.json
  - 支持配置的加载、保存和修改
  - 提供全局单例 config 实例
  - 添加完整的单元测试

## v0.2.2 (2026-04-13)
- feat(i18n): 创建国际化模块支持多语言
  - 创建 auto_tag/gui/i18n/ 目录结构
  - 实现 Translator 类管理语言翻译
  - 支持 en/zh 两种语言
  - 提供便捷函数 tr() 简化翻译调用
  - 支持格式化参数替换

## v0.2.1 (2026-04-13)
- feat(gui): 创建识别工作线程模块 RecognizeWorker
  - 使用 QThread 实现后台音频识别
  - 添加进度更新、文件处理完成、全部完成、错误发生等信号
  - 支持异步处理音频文件并发射信号通知主线程
  - 跳过 test 目录，支持 tag_only 模式

## v0.2.0 (2026-04-13)
- 初始化项目：克隆 mp3ShazamAutoTag 仓库
- 配置环境：安装 Rust 工具链解决 shazamio-core 编译依赖
- 兼容性修复：安装 audioop-lts 解决 Python 3.13 兼容性问题
- 依赖安装：完成项目所有依赖包的安装配置
