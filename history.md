# 项目变更历史

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
