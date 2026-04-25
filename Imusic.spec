# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('auto_tag/gui/i18n/locales', 'auto_tag/gui/i18n/locales'), ('assets', 'assets')],
    hiddenimports=['auto_tag', 'auto_tag.audio_recognize', 'auto_tag.gui', 'auto_tag.gui.main_window', 'auto_tag.gui.workers', 'auto_tag.gui.workers.recognize_worker', 'auto_tag.gui.components', 'auto_tag.gui.components.song_result_card', 'auto_tag.gui.pages', 'auto_tag.gui.pages.home_page', 'auto_tag.gui.i18n', 'auto_tag.gui.i18n.translator', 'auto_tag.utils', 'auto_tag.music_library_manager', 'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'PySide6.QtNetwork', 'qfluentwidgets', 'mutagen', 'mutagen.mp3', 'mutagen.flac', 'mutagen.ogg', 'mutagen.id3', 'eyed3', 'eyed3.id3', 'eyed3.compat', 'eyed3.plugins', 'shazamio', 'soundfile', 'ffmpeg', 'pymusiclibrary', 'filetype', 'pydub', 'pydub.generators', 'pydub.utils'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.Qt3DCore', 'PySide6.QtCharts', 'PySide6.QtMultimedia', 'PySide6.QtQuick', 'PySide6.QtSql', 'PySide6.QtPositioning', 'tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Imusic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\auto_tag.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Imusic',
)
