#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建脚本

该脚本用于构建 MP3 Shazam Auto Tag 的可执行文件。
使用 PyInstaller + .spec 文件将应用程序打包为目录模式的可执行文件。

功能：
    - 创建虚拟环境
    - 安装依赖
    - 运行测试
    - 使用 .spec 文件构建可执行文件（目录模式，优化体积）

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
    4. 使用 .spec 文件构建可执行文件（目录模式）
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

        # 4) Build executable using .spec file (目录模式：启动更快，体积优化)
        #    The .spec file contains all the optimization settings:
        #    - Directory mode (--onedir)
        #    - Excludes unnecessary Qt modules (WebEngine, 3D, Charts, etc.)
        #    - Collects data files (i18n, assets, qfluentwidgets, eyed3)
        #    - Includes all required dependencies (packaging, deprecation, etc.)
        spec_file = os.path.join(build_tools_dir, "mp3ShazamAutoTag.spec")
        pyinstaller_args = [
            python,
            "-m",
            "PyInstaller",
            "--clean",
            spec_file,
        ]

        run(pyinstaller_args)

        print(
            "\n✅ Build complete! Check the `dist/` directory under your project root."
        )
        print("   📦 Distributable: dist/mp3ShazamAutoTag/")
    finally:
        os.chdir(cwd_before)


if __name__ == "__main__":
    main()
