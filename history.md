# 项目变更历史

## v0.4.19 (2026-04-20)
- fix(core+ui): 修复搜索结果卡片创建失败导致完全不显示的问题
  - 将 FIF.CLOCK 替换为 FIF.HISTORY（用户 QFluentWidgets 版本无 CLOCK 常量）
  - 移除酷狗 API 的 limit 参数（KuGouMusicApi.search() 不支持）
  - 当 search_results 为空时，将 Shazam 结果包装为搜索结果格式传入卡片
  - 使用 objectName 选择器替代属性选择器，确保深色模式样式正确应用
  - 为 _on_file_processed 添加异常处理和详细日志

## v0.4.18 (2026-04-20)
- fix(ui): 修复卡片式布局搜索结果完全不显示的问题
  - 移除 QScrollArea 的透明背景样式，解决内容不可见问题
  - 使用 UP/DOWN 图标替代可能不存在的 CHEVRON_UP/DOWN
  - ToolButton 初始化时不传图标参数，避免构造函数异常
  - 为 _on_file_processed 添加异常处理和详细日志
  - 确保卡片创建失败时不会阻塞后续文件处理

## v0.4.17 (2026-04-20)
- fix(ui): 修复展开/收起按钮图标不显示问题
  - 将 PushButton 改为 ToolButton 以正确显示 FluentIcon 图标
  - 使用 CHEVRON_UP/CHEVRON_DOWN 图标替代 UP/DOWN
- fix(core): 增强 MusicLibrary 初始化日志
  - 添加 init_music_library() 调用后的可用状态日志
  - 导入 is_available 函数用于状态检查

## v0.4.16 (2026-04-20)
- fix(ui): 修复深色模式下搜索结果卡片文本不可见问题
  - 移除 QSS 中所有 QLabel[class="..."] 颜色覆盖，让 QFluentWidgets 自动处理文本颜色
  - 为 QScrollArea 视口设置透明背景，适配深色模式
  - 深色模式卡片背景色调整为 #2d2d2d（更贴合系统暗色）
  - 移除 platform_name_color/meta_text_color/no_result_color 等文本颜色配置
  - 简化 _THEME_COLORS，仅保留背景色和边框色

## v0.4.15 (2026-04-20)
- fix(core): 修复多平台搜索结果未显示在歌曲卡片中的问题
  - 在 RecognizeWorker._process_files() 中调用 init_music_library() 初始化 API
  - 修复全局单例 _initialized 始终为 False 导致 get_netease_api() 返回 None 的问题
  - 现在 Shazam 识别成功后，网易云/酷狗搜索结果能正确显示在卡片中

## v0.4.14 (2026-04-20)
- fix(ui): 适配卡片式搜索结果组件的深浅色主题
  - 为 PlatformResultWidget 和 SongResultCard 添加完整的主题颜色映射
  - 监听 qconfig.themeChanged 信号实现主题切换时自动刷新样式
  - 深色模式使用 #2c2c2c 卡片背景、#404040 边框等适配颜色
  - 浅色模式使用 #ffffff 卡片背景、#e8e8e8 边框等适配颜色
  - 优化平台选中状态、元数据文字、错误卡片等元素的主题表现

## v0.4.13 (2026-04-20)
- feat(ui): 优化主窗口尺寸为更宽扁的比例，匹配参考图像
  - 窗口尺寸从 1500×500 调整为 1600×480
  - 宽度增加约 7%，高度降低约 4%，使界面更加宽扁
  - 宽高比达到 3.33:1，更贴近参考图像的视觉效果
  - 内部所有组件（按钮、表格、布局等）保持原样不变
  - 验证各页面在不同窗口尺寸下的布局适配性

## v0.4.12 (2026-04-20)
- feat(ui): 重构首页搜索结果展示为卡片式布局
  - 创建 SongResultCard 组件：每首歌曲独立卡片，支持折叠/展开
  - 创建 PlatformResultWidget 子组件：展示各平台搜索结果详情
  - 替换原 TableWidget 为 ScrollArea + CardWidget 布局
  - 实现悬停高亮和选中状态视觉反馈
  - 支持响应式布局，适配不同窗口尺寸
  - 保留所有原有功能（勾选、全选/全不选、应用、Plex结构等）

## v0.4.11 (2026-04-20)
- feat(ui): 调整主窗口尺寸为扁平化布局
  - 窗口尺寸从 1000×800 调整为 1200×650
  - 宽度增加 20%，高度减少约 19%，使界面更加扁平化
  - 内部所有组件（按钮、表格、布局等）保持原样不变

## v0.4.10 (2026-04-20)
- feat(ui): 调整主窗口尺寸为扁平化布局
  - 窗口尺寸从 1000×800 调整为 1200×650
  - 宽度增加 20%，高度减少 19%，使界面更加扁平化
  - 内部组件（按钮、表格、布局间距等）保持原样不变
- feat(lyric): 重构歌词嵌入架构，MP3 使用 eyed3，其他格式使用 mutagen 格式特定 API
  - MP3: 使用 eyed3 处理 ID3 标签（USLT/SYLT 帧，位置参数修复）
  - FLAC: 使用 mutagen.flac.FLAC（LYRICS Vorbis Comment）
  - OGG: 使用 mutagen.oggvorbis.OggVorbis（LYRICS Vorbis Comment）
  - OPUS: 使用 mutagen.oggopus.OggOpus（LYRICS Vorbis Comment）
  - M4A: 使用 mutagen.mp4.MP4（©lyr iTunes 原子）
  - 移除通用的 File(file_path, easy=True)，改用格式特定 API
- fix(lyric): 修复 eyed3 v0.9.9 歌词嵌入失败问题
  - tag.lyrics.set() 要求位置参数而非关键字参数
  - 修复: tag.lyrics.set(lyrics, 'eng', b'') 
- fix(lyric): 修复保存歌词和嵌入歌词按钮的错误提示
  - 失败时显示正确的错误消息而非成功消息
- feat(lyric): 新增歌词嵌入模式选择器
  - 仅嵌入文件（默认）：仅写入 ID3/Vorbis 标签
  - 嵌入文件 + 生成 LRC：兼容网易云音乐
- feat(lyric): 新增保存歌词按钮（保存用户编辑的歌词到文件）
- fix(core): 修复 pymusiclibrary 多线程崩溃问题
  - 创建全局单例管理器 (music_library_manager.py)
  - Monkey Patch 修复 NeteaseCloudMusicApi 初始化失败时的 AttributeError
  - 确保 API 实例只在主线程初始化一次

## v0.4.9 (2026-04-20)
- refactor(ui): 调整窗口尺寸为扁平化布局，还原内部组件样式
  - main_window.py: 窗口尺寸从 1000×800 调整为 1200×650
  - style.qss: 移除所有内部组件样式（按钮、表格等），仅保留滚动条样式
  - 还原各页面布局间距至原始值
    - home_page.py: setContentsMargins(40,30,40,30), setSpacing(16)
    - converter_page.py: setContentsMargins(40,30,40,30), setSpacing(16)
    - music_manager_page.py: setContentsMargins(40,30,40,30), setSpacing(20)
    - settings_page.py: setContentsMargins(40,40,40,40), setSpacing(24)
  - 还原对话框组件圆角至原始值
    - cover_preview_dialog.py: border-radius 恢复为 12px
    - song_search_dialog.py: 恢复所有 border-radius 原始值

## v0.4.8 (2026-04-20)
- chore: 升级版本号至 0.4.8
- docs: 在 Readme.md 的 Acknowledgments 部分添加对原仓库的感谢
  - 添加 mp3ShazamAutoTag 原仓库链接和说明

## v0.4.6 (2026-04-20)
- refactor: 将项目名称修改为 Imusic，作者修改为 ling
  - pyproject.toml: name="Imusic", authors=[{name="ling"}]
  - pyproject.toml: 更新 GitHub URLs 为 ling/Imusic
  - Readme.md: 更新所有仓库链接和项目名称引用
  - .trae/rules/program.md: 更新项目名称和作者信息

## v0.4.5 (2026-04-20)
- feat(ui): **全面重构 UI 为扁平化设计风格**
  - 创建全局扁平化 QSS 样式表 (auto_tag/gui/style.qss)
    - 定义 15+ 种组件的扁平化样式（按钮、卡片、表格、输入框等）
    - 实现深色/浅色主题双重支持
    - 去除所有阴影效果，采用简洁边框设计
    - 统一圆角半径为 6px，组件高度为 36px
    - 主色调采用紫色 (#7c4dff)
  - 修改 MainWindow 加载 QSS 样式表
    - 新增 _load_stylesheet() 方法
    - 在初始化时自动加载全局样式
  - 调整所有页面布局间距
    - 主布局边距从 40px 减至 20px
    - 组件间距从 16-20px 减至 12px
    - 输入区域组件间距从 12px 减至 10px
    - 设置页面边距从 40px 减至 20px
  - 优化对话框组件样式
    - 移除 CoverPreviewDialog 阴影效果
    - 将圆角从 12px 减至 6px
    - 更新 SongSearchResultDialog 所有圆角为 6-8px
    - 清理未使用的 QGraphicsDropShadowEffect 导入
  - 保持所有现有功能完整性
    - 23 个测试用例全部通过
    - 不影响任何业务逻辑
- style: 统一设计语言
  - 采用扁平化设计原则（去除阴影、渐变、拟物化）
  - 统一组件高度（36px）和圆角（6px）
  - 优化视觉层次（减少间距、增强对比度）
  - 适配不同分辨率（响应式布局）

## v0.4.4 (2026-04-20)
- docs(program): 全面更新项目技术规范文档
  - 更新版本号至 0.4.3，添加歌词获取和元信息编辑核心功能
  - 更新项目结构，新增 lyric/、music_library_manager.py、gui/components/、gui/workers/lyric_worker.py
  - 更新依赖列表，新增 pymusiclibrary
  - 新增 lyric 模块文档（LyricManager、MusicLibraryManager）
  - 新增 MusicManagerPage 文档（文件列表、元信息编辑、封面管理、歌词获取）
  - 新增歌词工作线程文档（LyricWorker、LyricEmbedWorker）
  - 新增 SongSearchResultDialog 搜索结果选择对话框文档
  - 新增 MetadataManager 元数据管理器文档
  - 新增 CustomFormatManager 自定义格式管理器文档
  - 更新数据流架构图，新增歌词管理和 pymusiclibrary 层
  - 新增歌词获取策略和线程安全设计决策
  - 更新测试策略，新增歌词相关测试用例和 Mock 策略
  - 扩展开发指南，新增歌词提供商添加和歌词获取流程
  - 更新 API 参考文档，新增 LyricManager/MusicLibraryManager/MetadataManager/SongSearchResultDialog/LyricWorker/CustomFormatManager

#0.4.3(2026-04-19)#修复识别结果信息不显示和多源搜索失败问题

## v0.4.3 (2026-04-19)
- fix(core): **关键修复** - 解决 Shazam API 返回数据结构变化导致的解析崩溃
  - 修复 `_parse_shazam_result` 函数中 `metadata` 字段类型错误（list vs dict）
  - 兼容新旧两种 Shazam API 响应格式
  - 添加类型检查和安全的时长提取逻辑，避免 AttributeError
- fix(threading): **关键修复** - 解决 pymusiclibrary 多线程初始化崩溃问题
  - 在主线程预初始化原生库，避免子线程中的内存访问违规
  - 添加 `_preinit_music_library()` 方法，确保 ctypes 原生库安全加载
  - 增强错误处理，预初始化失败时优雅降级（仅使用 Shazam）
  - 新增 OSError 捕获，避免原生库初始化失败导致进程崩溃
- test: 添加 v0.4.3 修复验证测试用例
  - 测试 Shazam metadata 解析（dict/list 两种格式）
  - 测试主线程预初始化功能
  - 测试多源搜索流程（使用 mock）
  - 测试数据流完整性
  - 10 个测试用例全部通过
- fix(ui): 修复 Shazam 识别后标题、艺术家等信息不显示的问题
  - 改进 home_page.py 的回退逻辑，空字段显示 "--" 而非空白
  - 添加详细的调试日志输出，便于定位数据流断裂点
  - 增强字段验证，当所有基础字段为空时发出警告
- fix(core): 修复网易云音乐和酷狗音乐多源搜索未生效的问题
  - 增强 _search_netease 和 _search_kugou 的异常处理和日志输出
  - 改进 multi_source_search 函数的错误处理，添加完整的堆栈跟踪
  - 优化 API 响应解析逻辑，分步骤记录搜索过程
  - 确保 Shazam 结果解析失败时不会阻塞其他平台搜索
- refactor(logging): 统一日志规范
  - 在 recognize_worker.py 和 home_page.py 中引入 logging 模块
  - 使用 exc_info=True 输出完整异常堆栈
  - 添加关键节点的状态日志（文件处理、搜索结果统计等）

## v0.4.2 (2026-04-17)
- feat(lyric): 添加网易云歌词模式选择功能
  - 新增 lyric_mode 参数，支持三种模式：original（原始歌词）、merged（合并歌词，默认）、translation（翻译歌词）
  - 实现歌词合并功能：一句原始歌词+一句对应翻译歌词交替排列
  - 添加歌词合并测试用例（5个测试全部通过）
  - 添加三种歌词模式的测试用例（3个测试全部通过）
  - 更新文档说明，添加使用示例
  - 保持向后兼容，默认使用 merged 模式

## v0.4.1 (2026-04-17)
- feat(lyric): 使用 MusicLibrary (pymusiclibrary) 替换 lrxy 库
  - 移除对 lrxy 库的依赖，改用 MusicLibrary (pymusiclibrary)
  - 添加网易云音乐和酷狗音乐作为歌词提供商
  - 实现本地歌词格式转换功能，支持 LRC/TTML/SRT/JSON 格式互转
  - 更新 LyricManager 支持从网易云和酷狗搜索并获取歌词
  - 创建 pymusiclibrary skill 文档，记录 API 使用方法
  - 修复 API 调用逻辑，正确处理 Response 对象
  - 所有测试用例通过（14个测试全部通过）
  - 实际测试成功从网易云音乐获取歌词（含原词和翻译）
- feat(ui): 新增搜索结果多选功能
  - 创建 SongSearchResultDialog 搜索结果选择对话框组件
    - 展示歌曲列表（名称、艺术家、专辑、时长）
    - 支持双击或按钮确认选择
    - 单结果时自动跳过选择
  - LyricManager 新增 search_songs() 和 fetch_lyric_by_id() 方法
    - search_songs(): 仅搜索返回结果列表
    - fetch_lyric_by_id(): 根据指定 ID 获取歌词
  - MusicManagerPage 整合搜索选择流程
    - 网易云/酷狗获取歌词前先弹出搜索选择框
    - 用户确认后再获取目标歌曲的歌词
- fix(ui): 修复歌词提供商下拉框未显示网易云和酷狗的问题
  - 更新 MusicManagerPage 动态加载提供商列表（不再硬编码）
  - 默认选中网易云音乐作为首选提供商
  - 添加中英文国际化翻译支持
  - 验证所有5个提供商均可正常显示和使用
- fix(worker): 改进 LyricWorker 错误处理和日志输出
  - 添加详细的调试日志，便于定位问题
  - 区分文件不存在、API 返回空、异常等不同情况
  - 输出完整的堆栈跟踪信息
  - 验证线程安全性（在线程中成功获取歌词）
  - 修复 LyricWorker 缺少 logger 属性的运行时错误
  - 修复 ComboBox.currentData() 返回 None 导致 provider 参数为空的问题
    改用 currentIndex + _provider_list 映射方式获取选中的提供商
  - 安装 pymusiclibrary 到项目虚拟环境 (venv) 中，解决 No module named 'MusicLibrary' 错误

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
