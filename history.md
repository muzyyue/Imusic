# 项目变更历史

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
