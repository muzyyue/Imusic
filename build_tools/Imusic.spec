# -*- mode: python ; coding: utf-8 -*-
"""
Imusic 的 PyInstaller 规格文件（目录模式）

该文件精细控制打包过程，包括：
- 使用目录模式（--onedir），启动更快，依赖清晰
- 排除不需要的 Qt 模块（WebEngine、3D、Charts 等）
- 保留 GUI 必需的核心模块
- 正确收集数据文件（i18n、图标等）
- 优化体积

注意：v0.4.55 曾尝试迁移至 Nuitka，但因 Nuitka 上游 bug (GCC 下载链接 404)
      暂时回退到 PyInstaller。将来 Nuitka 稳定后可重新评估迁移。
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

# 项目根目录
spec_dir = os.path.dirname(os.path.abspath(SPEC))
project_root = os.path.dirname(spec_dir)

# 数据文件收集
datas = []
binaries = []
hiddenimports = [
    # 项目核心模块
    'auto_tag',
    'auto_tag.audio_recognize',
    'auto_tag.gui',
    'auto_tag.gui.main_window',
    'auto_tag.gui.workers',
    'auto_tag.gui.workers.recognize_worker',
    'auto_tag.gui.components',
    'auto_tag.gui.components.song_result_card',
    'auto_tag.gui.pages',
    'auto_tag.gui.pages.home_page',
    'auto_tag.gui.i18n',
    'auto_tag.gui.i18n.translator',
    'auto_tag.utils',
    'auto_tag.music_library_manager',
    
    # PySide6 核心模块（仅 GUI 必需的）
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',
    
    # qfluentwidgets 依赖
    'qfluentwidgets',
    'qfluentwidgets.components',
    'qfluentwidgets.common',
    'qfluentwidgets.navigation',
    'qfluentwidgets.widgets',
    
    # 音频处理库
    'mutagen',
    'mutagen.mp3',
    'mutagen.flac',
    'mutagen.ogg',
    'mutagen.id3',
    'eyed3',
    'eyed3.id3',
    'eyed3.compat',
    'eyed3.plugins',
    'shazamio',
    'soundfile',
    '_soundfile_data',
    'cffi',
    'ffmpeg',
    'pymusiclibrary',
    
    # eyed3 依赖
    'eyed3.utils.log',
    'eyed3.utils.console',
    'eyed3.plugins.default',
    'eyed3.plugins.classic',
    'eyed3.plugins.lame',
    
    # 其他必需依赖
    'filetype',
    'pydub',
    'pydub.generators',
    'pydub.utils',
    'asyncio',
    'concurrent.futures',
    'threading',
    'logging',
    'json',
    're',
    'os',
    'sys',
    'platform',
    'time',
    'datetime',
]

# 收集 i18n 语言文件
i18n_path = os.path.join(project_root, 'auto_tag', 'gui', 'i18n', 'locales')
if os.path.exists(i18n_path):
    datas.append((i18n_path, 'auto_tag/gui/i18n/locales'))

# 收集 assets 资源
assets_path = os.path.join(project_root, 'assets')
if os.path.exists(assets_path):
    datas.append((assets_path, 'assets'))

# 收集 qfluentwidgets 数据文件
datas.extend(collect_data_files('qfluentwidgets', include_py_files=False))

# 收集 eyed3 的数据文件（ID3 标签定义文件）
datas.extend(collect_data_files('eyed3', include_py_files=False))

# 收集 soundfile 的所有文件（包括 libsndfile 动态库）
soundfile_datas, soundfile_binaries, soundfile_hiddenimports = collect_all('soundfile')
datas.extend(soundfile_datas)
binaries.extend(soundfile_binaries)
hiddenimports.extend(soundfile_hiddenimports)

# 收集 lrxy 库的数据文件和依赖
try:
    lrxy_datas, lrxy_binaries, lrxy_hiddenimports = collect_all('lrxy')
    datas.extend(lrxy_datas)
    binaries.extend(lrxy_binaries)
    hiddenimports.extend(lrxy_hiddenimports)
    print("[Spec] lrxy library collected successfully")
except Exception as e:
    print(f"[Spec] Warning: lrxy collection failed: {e}")

# 收集 pymusiclibrary 的数据文件
try:
    pymusiclibrary_datas, pymusiclibrary_binaries, pymusiclibrary_hiddenimports = collect_all('pymusiclibrary')
    datas.extend(pymusiclibrary_datas)
    binaries.extend(pymusiclibrary_binaries)
    hiddenimports.extend(pymusiclibrary_hiddenimports)
    print("[Spec] pymusiclibrary library collected successfully")
except Exception as e:
    print(f"[Spec] Warning: pymusiclibrary collection failed: {e}")

# 验证资源路径存在性
datas_validated = []
for src, dst in datas:
    if os.path.exists(src):
        datas_validated.append((src, dst))
    else:
        print(f"[Spec] Warning: Data path does not exist: {src}")
datas = datas_validated

print(f"[Spec] Total datas files to collect: {len(datas)}")
print(f"[Spec] Total binaries files to collect: {len(binaries)}")
print(f"[Spec] Total hiddenimports: {len(hiddenimports)}")

# 分析隐藏导入
a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除测试/开发工具
        'pytest',
        'py',
        '_pytest',
        'pluggy',
        'iniconfig',
        
        # 排除不需要的 Qt 模块（大幅减小体积）
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DAnimation',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineQuick',
        'PySide6.QtWebView',
        'PySide6.QtWebChannel',
        'PySide6.QtWebSockets',
        'PySide6.QtBluetooth',
        'PySide6.QtDesigner',
        'PySide6.QtHelp',
        'PySide6.QtLocation',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtNfc',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtPositioning',
        'PySide6.QtPrintSupport',
        'PySide6.QtQuick',
        'PySide6.QtQuick3D',
        'PySide6.QtQuickControls2',
        'PySide6.QtQuickWidgets',
        'PySide6.QtRemoteObjects',
        'PySide6.QtScxml',
        'PySide6.QtSensors',
        'PySide6.QtSerialBus',
        'PySide6.QtSerialPort',
        'PySide6.QtSpatialAudio',
        'PySide6.QtSql',
        'PySide6.QtStateMachine',
        'PySide6.QtTest',
        'PySide6.QtTextToSpeech',
        'PySide6.QtUiTools',
        'PySide6.QtDBus',
        'PySide6.QtAxContainer',
        'tkinter',
        'turtle',
        'idlelib',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

# 检测 UPX 是否可用（可选，减小体积）
import shutil
upx_enabled = shutil.which('upx') is not None
if upx_enabled:
    print("[Spec] UPX compressor detected and will be enabled")
else:
    print("[Spec] UPX not found, skipping compression")

exe = EXE(
    pyz,
    a.scripts,
    [],
    name='Imusic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=upx_enabled,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'assets', 'auto_tag.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=upx_enabled,
    name='Imusic',
)
