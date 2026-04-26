# 项目变更历史

## v0.4.68 (2026-04-26)
- fix(ui): 修复转换器页面浅色模式背景色问题
  - 移除硬编码颜色值，使用 transparent 透明背景
  - 让 QFluentWidgets 自动处理深浅色主题适配
  - _on_theme_changed() 同时调用 _apply_page_scroll_theme() 确保主题切换生效
  - 涉及文件: `converter_page.py`

## v0.4.67 (2026-04-26)
- fix(ui): 修复转换器页面深色模式背景色适配问题
  - 将 QPalette 方式改为 QSS 样式表方式，参考 home_page.py 的成功实现
  - 使用 QScrollArea > QWidget > QWidget 选择器处理嵌套 widget 层级
  - 修正 QScrollArea 类名选择器（大写 Q）
  - 移除 setAutoFillBackground(True) 和 PySide6.QtGui 导入
  - 确保深色模式下内容区域显示 #1e1e1e 深色背景
  - 涉及文件: `converter_page.py`

## v0.4.66 (2026-04-26)
- fix(ui): 修复转换器页面变量名错误
  - 修复 setWidget() 调用中 content_widget → self.content_widget 的引用错误
  - 解决 NameError: name 'content_widget' is not defined 运行时异常
  - 涉及文件: `converter_page.py`

## v0.4.65 (2026-04-26)
- fix(ui): 修复转换器页面深色模式背景色适配问题
  - 使用 QPalette 设置 content_widget 和页面自身的背景色，比样式表更可靠
  - 设置 content_widget.setAutoFillBackground(True) 确保背景色正确填充
  - 同时设置 Window 和 Base 调色板角色，确保所有子控件继承正确的背景色
  - 保留样式表作为辅助，确保深色/浅色主题切换时背景色正确更新
  - 涉及文件: `converter_page.py`

## v0.4.64 (2026-04-26)
- refactor(ui): 转换器页面从局部滚动改为全页面滚动
  - 将原先仅文件列表区域的独立 ScrollArea 调整为包裹整个页面内容的统一 ScrollArea
  - 当页面内容（格式过滤、自定义格式、文件列表等）超出视口时，整个页面一起滚动
  - 移除 file_list_scroll 的独立滚动容器和最小高度限制
  - 新增 page_scroll 属性，保留 file_list_scroll 别名确保向后兼容
  - 新增 _apply_page_scroll_theme() 方法替代原 _apply_scroll_area_theme()
  - 操作按钮和内容区域布局结构保持不变，视觉一致性不受影响
  - 涉及文件: `converter_page.py`

## v0.4.63 (2026-04-26)
- feat(ui): 文件列表页面实现垂直滚动功能
  - 使用 QFluentWidgets ScrollArea 包裹文件表格和操作按钮容器
  - 文件表格和操作按钮始终在一起滚动，按钮固定在容器底部
  - 操作按钮（全选/取消全选/开始转换/停止转换/清除数据）随内容一起滚动
  - 滚动区域最小高度 400px，支持 expand 尺寸策略自动适配窗口大小
  - 新增 _apply_scroll_area_theme() 方法，适配深色/浅色主题背景色
  - 隐藏表格内置滚动条，由外层 ScrollArea 统一接管垂直滚动
  - 新增 file_list_scroll 属性，方便测试和后续扩展
  - 新增 23 个测试用例，全部通过（9个滚动区域测试 + 14个其他测试）
  - 涉及文件: `converter_page.py`, `tests/test_converter_page.py`

## v0.4.62 (2026-04-26)
- fix(lyric): 修复歌词数据在切换歌曲或重新选择目录后丢失的问题
  - _load_file_info(): 优先从 lyrics_cache 加载歌词，缓存未命中时才从文件标签提取
  - _scan_audio_files(): 重选目录时自动清理 lyrics_cache，避免缓存污染
  - _on_lyric_fetched(): 增加 file_path in self.files 校验，防止异步回调污染新目录界面
  - _on_clear_data(): 同步清理 lyrics_cache，修复 self.lyrics_edit 拼写错误为 self.lyric_text
  - 涉及文件: `music_manager_page.py`

## v0.4.61 (2026-04-26)
- feat(ui): 文件列表页面实现垂直滚动功能
  - 使用 QFluentWidgets ScrollArea 包裹文件表格和操作按钮容器
  - 文件表格和操作按钮始终在一起滚动，按钮固定在容器底部
  - 操作按钮（全选/取消全选/开始转换/停止转换/清除数据）随内容一起滚动
  - 滚动区域最小高度 400px，支持 expand 尺寸策略自动适配窗口大小
  - 新增 _apply_scroll_area_theme() 方法，适配深色/浅色主题背景色
  - 隐藏表格内置滚动条，由外层 ScrollArea 统一接管垂直滚动
  - 新增 file_list_scroll 属性，方便测试和后续扩展
  - 涉及文件: `converter_page.py`

## v0.4.60 (2026-04-26)
- feat(ui): 搜索结果栏显示复合来源标识
  - 当通过音频指纹引擎（Acoustid/Shazam/音频标签）识别后再搜索网易云等平台时，显示组合来源
  - 新增 SearchResult.fingerprint_engine 字段和 get_combined_source() 方法
  - 新增 combined_source 字段到 SearchResult.to_dict()，返回如 "Acoustid + 网易云音乐" 的格式
  - PlatformResultWidget 优先使用 combined_source 显示平台名称，备选传统映射
  - 支持 fingerprint_engine 值：acoustid、shazam、metadata、filename、none
  - audio_recognize.py: 在 _search_netease_rest、_search_qqmusic 中传递 fingerprint_engine
  - song_result_card.py: 修改 _get_platform_display_name() 支持复合来源
  - 涉及文件: `audio_recognize.py`, `song_result_card.py`

## v0.4.59 (2026-04-26)
- feat(settings): 设置页面新增「搜索关键词模式」选项
  - 用户可选择传给网易云/QQ音乐等平台的关键词格式
  - 「仅歌曲名」(title_only)：默认选项，用纯歌名搜索，对冷门/日文歌曲更精准
  - 「艺术家 + 歌曲名」(artist_title)：传统组合搜索方式
  - config.py: 新增 search_keyword_mode 属性及 VALID_KEYWORD_MODES 常量
  - settings_page.py: 新增 keyword_mode ComboBox 行及回调方法
  - audio_recognize.py: 根据 config.search_keyword_mode 动态构建 keyword
  - zh.json / en.json: 新增 keyword_mode_label、keyword_modes 翻译键

## v0.4.58 (2026-04-26)
- feat(core): 新增音频元数据回退策略 - 无意义文件名文件的搜索增强
  - 当音频指纹引擎（Acoustid/Shazam）全部失败，且文件名无意义时，从文件内部标签读取元数据作为搜索关键词
  - 新增 `_read_audio_metadata_from_file()` 函数：支持 MP3 (ID3) 和 OGG (Vorbis/Opus) 格式的标签读取
  - 新增 `_is_metadata_valid()` 函数：验证元数据是否可用于搜索（排除占位符值）
  - 新增 `_build_keyword_from_metadata()` 函数：从元数据构建搜索关键词
  - 优化 fallback 流程：文件名无意义 → 尝试读取文件标签 → 用标签内容搜索网易云等平台
  - 涉及文件: `audio_recognize.py`

## v0.4.57 (2026-04-26)
- feat(settings): 设置页面搜索源拆分为「识别引擎」和「补充搜索」两行
  - 将混在一起的5个搜索源按类型分组展示，用户可清晰区分音频指纹识别与关键词文本搜索
  - 第一行「识别引擎」：Acoustid (Chromaprint)、Shazam（真正的音频内容识别）
  - 第二行「补充搜索」：网易云音乐、酷狗音乐、QQ音乐（关键词文本匹配）
  - 调整最小选中校验逻辑：确保至少保留一个识别引擎（而非任意源）
  - settings_page.py: 拆分 CheckBox 布局为 engine_layout + supplement_layout 两行
  - zh.json / en.json: 新增 engine_label、supplement_label 翻译键
- fix(search): 网易云/QQ音乐搜索关键词改为仅使用歌曲名
  - 原逻辑用 "艺术家 歌曲名" 组合搜索，对冷门/日文名艺术家匹配不准确
  - 改为仅传歌曲名(title)作为关键词，提升网易云等平台的搜索精准度
  - audio_recognize.py: keyword 从 f"{artist} {title}" 改为 title

## v0.4.56 (2026-04-25)
- fix(build): 回退打包工具链从 Nuitka 至 PyInstaller（Nuitka 4.0.8 上游 bug）
  - 原因: Nuitka 依赖的 winlibs-gcc 下载链接返回 HTTP 404 (Not Found)
  - 影响: 无法完成编译，必须回退到稳定的 PyInstaller 方案
  - build_exe.py: 完全重写回 PyInstaller 版本（移除 Nuitka 相关代码）
  - pyproject.toml: 版本升级至 0.4.56
  - pyproject.toml: dev 依赖改回 pyinstaller>=6.0（移除 nuitka 和 ordered-set）
  - .gitignore: 恢复 spec 文件保留规则（!build_tools/*.spec）
  - .gitignore: 保留 Nuitka 构建产物忽略规则以备将来迁移
  - Imusic.spec: 恢复为活跃配置文件（移除废弃标记）
  - Imusic.spec: 更新文档字符串添加迁移历史说明
  - program.md: 全面更新构建文档（8.3 节改回 PyInstaller 说明）
  - program.md: 更新版本号和开发依赖列表
  - program.md: 添加迁移历史记录和未来计划说明
  - 涉及文件: `build_tools/build_exe.py`, `pyproject.toml`, `.gitignore`, `build_tools/Imusic.spec`, `program.md`

## v0.4.55 (2026-04-25)
- refactor(build): 将打包工具链从 PyInstaller 迁移至 Nuitka
  - build_exe.py: 完全重写为 Nuitka 构建脚本，新增 C 编译器检测功能
  - build_exe.py: 实现 Nuitka 参数生成（Qt 插件、数据文件、模块包含等）
  - build_exe.py: 新增 --skip-compiler-check 参数（跳过编译器检测）
  - pyproject.toml: 版本升级至 0.4.55
  - pyproject.toml: dev 依赖添加 nuitka>=2.0 和 ordered-set
  - .gitignore: 添加 Nuitka 构建产物忽略规则（*.build/, *.dist/ 等）
  - .gitignore: 更新 spec 文件规则为忽略模式
  - Imusic.spec: 标记为已废弃并归档（保留作为回退参考）
  - program.md: 全面更新构建文档（8.3 节重写为 Nuitka 说明）
  - program.md: 更新版本号和开发依赖列表
  - 涉及文件: `build_tools/build_exe.py`, `pyproject.toml`, `.gitignore`, `build_tools/Imusic.spec`, `program.md`

## v0.4.54 (2026-04-25)
- refactor(build): 根据 python-pyinstaller-onedir skill 优化打包流程
  - spec 文件: 添加 lrxy/pymusiclibrary 库的自动收集支持
  - spec 文件: 启用 UPX 压缩（自动检测可用性）
  - spec 文件: 添加资源路径验证和打包统计输出
  - build_exe.py: 添加虚拟环境复用逻辑（--force-rebuild 控制）
  - build_exe.py: 添加可选参数（--skip-tests 跳过测试）
  - build_exe.py: 添加打包体积统计和 Top 10 大文件列表
  - build_exe.py: 修复 Windows 控制台 UTF-8 编码问题
  - 涉及文件: `build_tools/Imusic.spec`, `build_tools/build_exe.py`, `pyproject.toml`

## v0.4.53 (2026-04-25)
- fix(build): 修复单目录打包后 soundfile 模块缺失问题
  - 在 hiddenimports 中添加 `_soundfile_data` 和 `cffi`
  - 修复 EXE 段结构（目录模式不应在 EXE 中传递 a.binaries）
  - 完全禁用 UPX 压缩避免 DLL 损坏
  - 修复 "Failed to start embedded python interpreter!" 和 "No module named soundfile" 问题
  - 涉及文件: `build_tools/Imusic.spec`

## v0.4.52 (2026-04-25)
- fix(qqmusic): 优化 QQ 音乐搜索 - 增强日志输出和空结果诊断
  - 添加元数据信息提取（estimate_sum, actual_sum）
  - 区分"API有结果但列表为空"和"完全无结果"两种情况
  - 提示可能的原因：认证或参数问题
  - 涉及文件: `auto_tag/audio_recognize.py`

## v0.4.51 (2026-04-25)
- fix(qqmusic): 修复 QQ 音乐搜索功能 - 从废弃公共代理迁移到官方统一网关接口
  - 将 API 端点从 `http://api.qq.jsososo.com`（DNS 失败）改为 `https://u.y.qq.com/cgi-bin/musicu.fcg`
  - 请求方式从 GET 改为 POST（JSON 格式请求体）
  - 更新响应数据路径：`search.data.body.item_song[]`
  - 更新字段映射：songname→name, songid→id, albumname→album.name（嵌套对象）
  - 保持 SearchResult 数据结构和 [QQMusic] 日志前缀不变
  - 涉及文件: `auto_tag/audio_recognize.py`, `tests/debug_qq_music.py`

## v0.4.50 (2026-04-25)
- fix(build): 修复 UPX 排除配置导致嵌入 Python 解释器启动失败
  - 将 upx_exclude 中的 `python313.dll` 更正为 `python312.dll`（匹配实际 Python 3.12 运行时）
  - 同步更新 EXE 和 COLLECT 两处的 UPX 排除列表
  - 涉及文件: `build_tools/Imusic.spec`
- chore(build): 执行单目录模式打包（PyInstaller --onedir）
  - 输出目录结构：dist/Imusic/Imusic.exe + _internal/ 依赖文件夹

## v0.4.49 (2026-04-25)
- chore(build): 执行单目录打包（PyInstaller onedir 模式）
  - 使用 build_tools/Imusic.spec 打包配置
  - 输出目录模式可执行文件到 dist/Imusic/
  - 涉及文件: `build_tools/Imusic.spec`, `pyproject.toml`

## v0.4.48 (2026-04-25)
- fix(i18n): 修复音乐管理页面歌词提供商下拉框未翻译的问题
  - 将 `tr(provider_name)` 改为 `tr(f'lyrics.providers.{provider_name}')` 匹配嵌套翻译键路径
  - 涉及文件: `music_manager_page.py`

## v0.4.47 (2026-04-25)
- feat(settings): 搜索源支持多选 - ComboBox 单选改为 CheckBox 多选（保持原有布局结构）
  - UI层: 搜索源行从 ComboBox 改为 CheckBox 水平多选，保持左右行布局不变
  - 配置层: search_source (str) → search_sources (list[str])，兼容旧版单字符串自动转列表
  - 搜索层: multi_source_search() 传入 config.search_sources 列表
  - 网易云条件选项：选中包含 netease 时显示搜索类型和电台开关
  - 修复循环导入: audio_recognize.py 中 config 模块导入改为函数内懒加载
  - 涉及文件: `config.py`, `settings_page.py`, `audio_recognize.py`

## v0.4.46 (2026-04-25)
- refactor(build): 将项目构建配置中的 mp3ShazamAutoTag 统一替换为 Imusic
  - 重命名 `mp3ShazamAutoTag.spec` 为 `Imusic.spec`
  - 更新 `build_exe.py` 中的 spec 文件引用和输出目录名
  - 更新 `netease_recognize.py` 和 `acoustid_recognize.py` 中的测试路径
  - 涉及文件: `Imusic.spec`, `build_exe.py`, `netease_recognize.py`, `acoustid_recognize.py`

## v0.4.45 (2026-04-25)
- refactor(i18n): 优化国际化文件为嵌套分组结构，支持点号分隔的嵌套键访问
  - 涉及文件: `translator.py`, `zh.json`, `en.json`

## v0.4.42 (2026-04-25)
- fix(core): 修复 MP3 封面写入失败 - urlopen 缺少 User-Agent 导致 CDN 拒绝请求
  - 涉及文件: `audio_recognize.py`, `home_page.py`

## v0.4.41 (2026-04-25)
- fix(gui): 修复重新获取歌曲数据后卡片背景色未更新的问题
  - 涉及文件: `song_result_card.py`

## v0.4.40 (2026-04-25)
- fix(gui): 修复重新获取歌曲数据后封面图片组件主题颜色未更新的问题
  - 涉及文件: `song_result_card.py`

## v0.4.39 (2026-04-24)
- chore(build): 优化 PyInstaller 打包配置 - 切换目录模式，体积从 700MB 优化到 240MB
  - 涉及文件: `build_exe.py`, `mp3ShazamAutoTag.spec`

## v0.4.38 (2026-04-24)
- feat(core): 优化文件名识别策略 - 不像歌曲名时优先 Shazam 音频识别
  - 涉及文件: `audio_recognize.py`

## v0.4.37 (2026-04-24)
- feat(core): 添加清除数据功能和修复 WinError 32 错误
  - 涉及文件: `home_page.py`, `music_manager_page.py`, `zh.json`, `en.json`

## v0.4.36 (2026-04-24)
- refine(gui): 增强搜索加载对话框视觉效果（旋转图标、取消按钮、文本换行）
  - 涉及文件: `home_page.py`

## v0.4.36 (2026-04-24)
- fix(core): 完善网易云封面获取 - 通过歌曲详情接口获取封面URL
  - 涉及文件: `audio_recognize.py`

## v0.4.35 (2026-04-24)
- fix(gui): 歌词搜索异步化 - 消除UI未响应卡顿
  - 涉及文件: `song_search_worker.py`, `music_manager_page.py`

## v0.4.34 (2026-04-24)
- fix(core): 修复网易云封面显示问题 - 游客登录+URL解析
  - 涉及文件: `audio_recognize.py`, `song_result_card.py`

## v0.4.33 (2026-04-24)
- fix(lyric): 歌词搜索增强 - 增加 REST API 备用方案
  - 涉及文件: `manager.py`

## v0.4.32 (2026-04-23)
- fix(core): 优化封面图片获取逻辑 - 多策略封面获取
  - 涉及文件: `audio_recognize.py`, `song_result_card.py`

## v0.4.31 (2026-04-23)
- feat(gui): 音乐封面图片展示功能 - CoverImageWidget 异步加载组件
  - 涉及文件: `song_result_card.py`

## v0.4.30 (2026-04-23)
- fix(core): 保留多语言原始字符 - 解决标签写入时日语/中文等被转成拼音的问题
  - 涉及文件: `home_page.py`

## v0.4.29 (2026-04-23)
- fix(gui): 解决"点击应用后歌曲信息未改变"问题 - 添加平台选择回调机制
  - 涉及文件: `song_result_card.py`

## v0.4.28 (2026-04-23)
- fix(gui): 解决应用后文件信息仍未改变的问题 - 实现多策略路径查找算法
  - 涉及文件: `home_page.py`

## v0.4.27 (2026-04-23)
- fix(core): 解决点击"应用"后文件信息未改变的问题 - 增强标签写入错误处理
  - 涉及文件: `audio_recognize.py`, `home_page.py`

## v0.4.26 (2026-04-20)
- feat(ui): 优化窗口尺寸并添加手动调整大小功能（1200×580，最小 900×500，最大 1920×1080）
  - 涉及文件: `main_window.py`

## v0.4.25 (2026-04-22)
- chore(tool): 将虚拟环境从 venv 迁移到 uv
  - 涉及文件: `pyproject.toml`

## v0.4.24 (2026-04-20)
- fix(core): 彻底修复选择目录后程序崩溃的问题 - 默认禁用 pymusiclibrary
  - 涉及文件: `audio_recognize.py`, `recognize_worker.py`

## v0.4.23 (2026-04-20)
- feat(core): 重新启用网易云/酷狗搜索（线程安全版本）- 使用 threading.local()
  - 涉及文件: `audio_recognize.py`

## v0.4.22 (2026-04-20)
- fix(core): 修复选择文件夹后应用直接崩溃的问题 - 移除 pymusiclibrary 初始化
  - 涉及文件: `recognize_worker.py`

## v0.4.21 (2026-04-20)
- fix(core): 修复 pymusiclibrary 原生库崩溃导致进度卡死的问题
  - 涉及文件: `audio_recognize.py`

## v0.4.20 (2026-04-20)
- fix(ui): 完成深色模式样式适配
  - 涉及文件: `home_page.py`

## v0.4.19 (2026-04-20)
- fix(core+ui): 修复搜索结果卡片创建失败导致完全不显示的问题
  - 涉及文件: `home_page.py`, `song_result_card.py`

## v0.4.18 (2026-04-20)
- fix(ui): 修复卡片式布局搜索结果完全不显示的问题
  - 涉及文件: `home_page.py`

## v0.4.17 (2026-04-20)
- fix(ui): 修复展开/收起按钮图标不显示问题
  - fix(core): 增强 MusicLibrary 初始化日志
  - 涉及文件: `home_page.py`, `audio_recognize.py`

## v0.4.16 (2026-04-20)
- fix(ui): 修复深色模式下搜索结果卡片文本不可见问题
  - 涉及文件: `song_result_card.py`

## v0.4.15 (2026-04-20)
- fix(core): 修复多平台搜索结果未显示在歌曲卡片中的问题
  - 涉及文件: `recognize_worker.py`

## v0.4.14 (2026-04-20)
- fix(ui): 适配卡片式搜索结果组件的深浅色主题
  - 涉及文件: `song_result_card.py`

## v0.4.13 (2026-04-20)
- feat(ui): 优化主窗口尺寸为更宽扁的比例（1600×480）
  - 涉及文件: `main_window.py`

## v0.4.12 (2026-04-20)
- feat(ui): 重构首页搜索结果展示为卡片式布局
  - 涉及文件: `home_page.py`, `song_result_card.py`

## v0.4.11 (2026-04-20)
- feat(ui): 调整主窗口尺寸为扁平化布局（1200×650）
  - 涉及文件: `main_window.py`

## v0.4.10 (2026-04-20)
- feat(ui): 调整主窗口尺寸为扁平化布局（1200×650）
- feat(lyric): 重构歌词嵌入架构，MP3 使用 eyed3，其他格式使用 mutagen
- fix(lyric): 修复 eyed3 v0.9.9 歌词嵌入失败问题
- fix(lyric): 修复保存歌词和嵌入歌词按钮的错误提示
- feat(lyric): 新增歌词嵌入模式选择器
- feat(lyric): 新增保存歌词按钮
- fix(core): 修复 pymusiclibrary 多线程崩溃问题
  - 涉及文件: `main_window.py`, `manager.py`, `music_library_manager.py`, `lyric_worker.py`

## v0.4.9 (2026-04-20)
- refactor(ui): 调整窗口尺寸为扁平化布局，还原内部组件样式
  - 涉及文件: `main_window.py`, `style.qss`, 各页面文件

## v0.4.8 (2026-04-20)
- chore: 升级版本号至 0.4.8
- docs: 在 Readme.md 的 Acknowledgments 部分添加对原仓库的感谢

## v0.4.6 (2026-04-20)
- refactor: 将项目名称修改为 Imusic，作者修改为 ling
  - 涉及文件: `pyproject.toml`, `Readme.md`, `program.md`

## v0.4.5 (2026-04-20)
- feat(ui): 全面重构 UI 为扁平化设计风格（QSS 样式表、统一组件高度和圆角）
  - 涉及文件: `style.qss`, `main_window.py`, 各页面和对话框文件

## v0.4.4 (2026-04-20)
- docs(program): 全面更新项目技术规范文档
  - 涉及文件: `program.md`

## v0.4.3 (2026-04-19)
- fix(core): 解决 Shazam API 返回数据结构变化导致的解析崩溃
- fix(threading): 解决 pymusiclibrary 多线程初始化崩溃问题
- fix(ui): 修复 Shazam 识别后标题、艺术家等信息不显示的问题
- fix(core): 修复网易云音乐和酷狗音乐多源搜索未生效的问题
- refactor(logging): 统一日志规范
  - 涉及文件: `audio_recognize.py`, `home_page.py`, `recognize_worker.py`

## v0.4.2 (2026-04-17)
- feat(lyric): 添加网易云歌词模式选择功能（original/merged/translation）
  - 涉及文件: `manager.py`

## v0.4.1 (2026-04-17)
- feat(lyric): 使用 MusicLibrary (pymusiclibrary) 替换 lrxy 库
- feat(ui): 新增搜索结果多选功能（SongSearchResultDialog）
- fix(ui): 修复歌词提供商下拉框未显示网易云和酷狗的问题
- fix(worker): 改进 LyricWorker 错误处理和日志输出
  - 涉及文件: `manager.py`, `song_search_dialog.py`, `music_manager_page.py`, `lyric_worker.py`

## v0.4.0 (2026-04-16)
- feat(lyric): 添加歌词获取功能的全面测试用例和修复API调用逻辑
- feat(lyric): 新增歌词管理模块（LyricManager）
- fix(lyric): 修复歌词嵌入和提取功能
  - 涉及文件: `manager.py`, `provider.py`

## v0.3.9 (2026-04-16)
- fix(gui): 优化主窗口初始尺寸（1000×600）
  - 涉及文件: `main_window.py`

## v0.3.8 (2026-04-15)
- feat(gui): 创建音乐管理页面 MusicManagerPage
  - 涉及文件: `music_manager_page.py`

## v0.3.7 (2026-04-14)
- feat(converter): 新增自定义文件格式管理功能
- feat(converter): 新增文件格式过滤功能
- fix(converter): 修复 ConverterWorker 导入错误
- fix(i18n): 修复语言切换问题
- fix(converter): 修复删除格式对话框错误
  - 涉及文件: `custom_format.py`, `converter_page.py`, `converter_worker.py`, 翻译文件

## v0.3.6 (2026-04-14)
- docs: 全面更新 Readme.md 文档
  - 涉及文件: `Readme.md`

## v0.3.5 (2026-04-13)
- fix(i18n): 修复转换页面语言切换问题
  - 涉及文件: `converter_page.py`, `zh.json`, `en.json`

## v0.3.4 (2026-04-13)
- test(converter): 完善 MetadataManager 单元测试
  - 涉及文件: `test_metadata_manager.py`

## v0.3.3 (2026-04-13)
- feat(converter): 创建 ConverterWorker 音频转换工作线程
  - 涉及文件: `converter_worker.py`

## v0.3.2 (2026-04-13)
- feat(converter): 创建 AudioConverter 音频转换器类
  - 涉及文件: `converter.py`, `requirements.txt`

## v0.3.1 (2026-04-13)
- feat(converter): 创建元数据管理器 MetadataManager
  - 涉及文件: `metadata_manager.py`

## v0.3.0 (2026-04-13)
- **BREAKING**: GUI 框架从 tkinter 迁移到 PySide6 + QFluentWidgets
- feat(gui): 完成 Fluent Design 风格 UI 重构
- feat(i18n): 国际化系统支持英文/中文切换
- feat(config): 配置管理模块
  - 涉及文件: 全部 GUI 相关文件

## v0.2.5 (2026-04-13)
- feat(gui): 创建设置页面 SettingsPage
  - 涉及文件: `settings_page.py`

## v0.2.4 (2026-04-13)
- feat(gui): 创建主页（音频识别页面）HomePage
  - 涉及文件: `home_page.py`

## v0.2.3 (2026-04-13)
- feat(config): 创建配置管理模块 AppConfig
  - 涉及文件: `config.py`

## v0.2.2 (2026-04-13)
- feat(i18n): 创建国际化模块支持多语言
  - 涉及文件: `translator.py`, `zh.json`, `en.json`

## v0.2.1 (2026-04-13)
- feat(gui): 创建识别工作线程模块 RecognizeWorker
  - 涉及文件: `recognize_worker.py`

## v0.2.0 (2026-04-13)
- 初始化项目：克隆 mp3ShazamAutoTag 仓库
- 配置环境：安装 Rust 工具链解决 shazamio-core 编译依赖
- 兼容性修复：安装 audioop-lts 解决 Python 3.13 兼容性问题
- 依赖安装：完成项目所有依赖包的安装配置
