#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建脚本

该脚本用于构建 Imusic 的可执行文件。
使用 PyInstaller + .spec 文件将应用程序打包为目录模式的可执行文件。

功能：
    - 智能虚拟环境管理（支持复用和强制重建）
    - 安装依赖
    - 运行测试（可选）
    - 使用 .spec 文件构建可执行文件（目录模式，优化体积）
    - 打包体积统计

使用方法：
    python build_tools/build_exe.py                   # 默认模式（复用 venv）
    python build_tools/build_exe.py --force-rebuild   # 强制重建 venv
    python build_tools/build_exe.py --skip-tests      # 跳过测试
    python build_tools/build_exe.py --help            # 显示帮助信息
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Windows 控制台编码修复
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


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


def get_dist_size(dist_path):
    """
    计算打包输出目录的总大小

    Args:
        dist_path: 输出目录路径

    Returns:
        int: 总大小（字节）
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(dist_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if not os.path.islink(filepath):
                total_size += os.path.getsize(filepath)
    return total_size


def format_size(size_bytes):
    """
    格式化文件大小显示

    Args:
        size_bytes: 字节数

    Returns:
        str: 格式化后的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def print_build_summary(dist_path, project_root):
    """
    打印打包总结信息

    Args:
        dist_path: 输出目录路径
        project_root: 项目根目录路径
    """
    dist_imusic = os.path.join(dist_path, 'Imusic')
    
    if not os.path.exists(dist_imusic):
        print("\n⚠ Warning: Build output directory not found!")
        return
    
    total_size = get_dist_size(dist_imusic)
    file_count = sum(len(files) for _, _, files in os.walk(dist_imusic))
    
    print("\n" + "=" * 60)
    print("📦 BUILD SUMMARY")
    print("=" * 60)
    print(f"  Output directory: {dist_imusic}")
    print(f"  Total files: {file_count}")
    print(f"  Total size: {format_size(total_size)}")
    
    # 列出最大的10个文件
    print("\n  📊 Top 10 largest files:")
    file_sizes = []
    for dirpath, dirnames, filenames in os.walk(dist_imusic):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if not os.path.islink(filepath):
                file_sizes.append((filepath, os.path.getsize(filepath)))
    
    file_sizes.sort(key=lambda x: x[1], reverse=True)
    for filepath, size in file_sizes[:10]:
        rel_path = os.path.relpath(filepath, dist_imusic)
        print(f"    {format_size(size):>10}  {rel_path}")
    
    print("=" * 60)
    print("✅ Build complete!")
    print(f"   📦 Distributable: {dist_imusic}/")
    print("=" * 60)


def main():
    """
    主构建函数

    执行完整的构建流程：
    1. 解析命令行参数
    2. 创建或复用虚拟环境
    3. 安装项目依赖
    4. 运行测试（可选）
    5. 使用 .spec 文件构建可执行文件（目录模式）
    6. 输出打包总结
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Build Imusic executable')
    parser.add_argument(
        '--force-rebuild',
        action='store_true',
        help='Force recreate the virtual environment and reinstall dependencies'
    )
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip running tests before building'
    )
    args = parser.parse_args()
    
    # 该脚本位于 <project_root>/build_tools/
    build_tools_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(build_tools_dir, os.pardir))

    print("=" * 60)
    print("🚀 Imusic Build Script")
    print("=" * 60)
    print(f"Project root detected at:\n  {project_root}")
    print(f"Force rebuild: {'Yes' if args.force_rebuild else 'No'}")
    print(f"Skip tests: {'Yes' if args.skip_tests else 'No'}")

    # 1) (Re)create virtual environment under project_root/venv
    venv_dir = os.path.join(project_root, "venv")
    
    if os.path.isdir(venv_dir) and not args.force_rebuild:
        print("\n✓ Virtual environment exists, reusing it")
        print("  (Use --force-rebuild to recreate)")
    else:
        if os.path.isdir(venv_dir):
            print("\n🗑 Removing existing venv/ (force rebuild)")
            shutil.rmtree(venv_dir)
        print("\n📦 Creating new virtual environment...")
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
        if args.force_rebuild or not os.path.exists(os.path.join(venv_dir, "Lib", "site-packages", "auto_tag")):
            print("\n📥 Installing dependencies...")
            run([pip, "install", "."])
            run([pip, "install", "pyinstaller", "pytest", "pytest-asyncio"])
        else:
            print("\n✓ Dependencies already installed")
            print("  (Use --force-rebuild to reinstall)")

        # 3) Run tests (optional)
        if not args.skip_tests:
            print("\n🧪 Running tests...")
            run([python, "-m", "pytest"])
        else:
            print("\n⏭ Skipping tests (--skip-tests specified)")

        # 4) Build executable using .spec file (目录模式：启动更快，体积优化)
        print("\n🔨 Building executable...")
        spec_file = os.path.join(build_tools_dir, "Imusic.spec")
        pyinstaller_args = [
            python,
            "-m",
            "PyInstaller",
            "--clean",
            spec_file,
        ]

        run(pyinstaller_args)

        # 5) Print build summary
        dist_path = os.path.join(project_root, "dist")
        print_build_summary(dist_path, project_root)
        
    finally:
        os.chdir(cwd_before)


if __name__ == "__main__":
    main()
