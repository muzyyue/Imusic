#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建脚本

该脚本用于构建 MP3 Shazam Auto Tag 的可执行文件。
使用 PyInstaller 将应用程序打包为独立的可执行文件。

功能：
    - 创建虚拟环境
    - 安装依赖
    - 运行测试
    - 构建可执行文件

使用方法：
    python build_tools/build_exe.py
"""

import os
import shutil
import subprocess
import sys


def run(cmd, **kwargs):
    """
    执行命令并检查返回码

    Args:
        cmd (list): 命令及参数列表
        **kwargs: 传递给 subprocess.run 的额外参数

    如果命令返回非零退出码，脚本将终止。
    """
    print(f"\n$ {' '.join(cmd)}")
    res = subprocess.run(cmd, check=False, **kwargs)
    if res.returncode != 0:
        print(f"✖ Command failed with exit code {res.returncode}. Aborting.")
        sys.exit(res.returncode)


def main():
    """
    主构建函数

    执行完整的构建流程：
    1. 创建虚拟环境
    2. 安装项目依赖
    3. 运行测试
    4. 使用 PyInstaller 构建可执行文件
    """
    # 该脚本位于 <project_root>/build_tools/
    build_tools_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(build_tools_dir, os.pardir))

    print(f"Project root detected at:\n  {project_root}")

    # 1) (Re)create virtual environment under project_root/venv
    venv_dir = os.path.join(project_root, "venv")
    if os.path.isdir(venv_dir):
        print("Removing existing venv/")
        shutil.rmtree(venv_dir)
    run([sys.executable, "-m", "venv", venv_dir])

    # Determine pip/python inside venv
    if os.name == "nt":
        pip = os.path.join(venv_dir, "Scripts", "pip.exe")
        python = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        pip = os.path.join(venv_dir, "bin", "pip")
        python = os.path.join(venv_dir, "bin", "python")

    # We'll run all commands from project_root
    cwd_before = os.getcwd()
    os.chdir(project_root)
    try:
        # 2) Install package and tools
        run([pip, "install", "."])
        run([pip, "install", "pyinstaller", "pytest", "pytest-asyncio"])

        # 3) Run tests
        run([python, "-m", "pytest"])

        # 4) Build executable (目录模式：启动更快，依赖清晰可见)
        ico_path = os.path.join(project_root, "assets", "auto_tag.ico")
        i18n_src = os.path.join(project_root, "auto_tag", "gui", "i18n", "locales")
        assets_src = os.path.join(project_root, "assets")
        # on Windows use ';', on POSIX use ':'
        delim = ";" if os.name == "nt" else ":"

        # 数据文件收集：i18n 语言文件 + 图标资源
        i18n_data = f"{i18n_src}{delim}auto_tag/gui/i18n/locales"
        assets_data = f"{assets_src}{delim}assets"

        # PyInstaller 参数（目录模式优化配置）
        pyinstaller_args = [
            python,
            "-m",
            "PyInstaller",
            # 目录模式（移除 --onefile）
            "--onedir",
            "--noconsole",
            f"--icon={ico_path}",
            # 数据文件
            f"--add-data={i18n_data}",
            f"--add-data={assets_data}",
            # 核心模块隐藏导入
            "--hidden-import=auto_tag",
            "--hidden-import=auto_tag.audio_recognize",
            "--hidden-import=auto_tag.gui",
            "--hidden-import=auto_tag.gui.main_window",
            "--hidden-import=auto_tag.gui.workers",
            "--hidden-import=auto_tag.gui.workers.recognize_worker",
            "--hidden-import=auto_tag.gui.components",
            "--hidden-import=auto_tag.gui.components.song_result_card",
            "--hidden-import=auto_tag.gui.pages",
            "--hidden-import=auto_tag.gui.pages.home_page",
            "--hidden-import=auto_tag.gui.i18n",
            "--hidden-import=auto_tag.gui.i18n.translator",
            "--hidden-import=auto_tag.utils",
            "--hidden-import=auto_tag.music_library_manager",
            # PySide6 相关
            "--hidden-import=PySide6",
            "--hidden-import=PySide6.QtCore",
            "--hidden-import=PySide6.QtGui",
            "--hidden-import=PySide6.QtWidgets",
            # qfluentwidgets 相关
            "--hidden-import=qfluentwidgets",
            "--hidden-import=qfluentwidgets.components",
            "--hidden-import=qfluentwidgets.common",
            "--hidden-import=qfluentwidgets.navigation",
            "--hidden-import=qfluentwidgets.widgets",
            # 音频处理库
            "--hidden-import=mutagen",
            "--hidden-import=mutagen.mp3",
            "--hidden-import=mutagen.flac",
            "--hidden-import=mutagen.ogg",
            "--hidden-import=mutagen.id3",
            "--hidden-import=eyed3",
            "--hidden-import=eyed3.id3",
            "--hidden-import=shazamio",
            "--hidden-import=soundfile",
            "--hidden-import=ffmpeg",
            "--hidden-import=pymusiclibrary",
            # 收集资源文件
            "--collect-data=qfluentwidgets",
            # 收集 PySide6 的所有内容（包括插件）
            "--collect-all=PySide6",
            # 排除测试/开发工具（减少体积）
            "--exclude-module=pytest",
            "--exclude-module=py",
            "--exclude-module=_pytest",
            "--exclude-module=pluggy",
            "--exclude-module=iniconfig",
            "--exclude-module=packaging",
            "--exclude-module=setuptools",
            "--exclude-module=pip",
            # 输出目录配置
            "--workpath=build/work",
            "--distpath=build/dist",
            "--specpath=build",
            # 程序名称（任务栏显示）
            "--name=mp3ShazamAutoTag",
            "main.py",
        ]

        run(pyinstaller_args)

        print(
            "\n✅ Build complete!  Check the `build/` directory under your project root."
        )
    finally:
        os.chdir(cwd_before)


if __name__ == "__main__":
    main()
