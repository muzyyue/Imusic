# -*- coding: utf-8 -*-
"""
版本号模块

在模块加载时从 pyproject.toml 读取版本号并导出。
PyInstaller 打包后，该版本号会被编译进 .pyc 文件，
解决打包应用显示 "unknown" 版本的问题。

Attributes:
    __version__ (str): 应用版本号，读取失败时返回 "unknown"
"""

import os
import sys

__version__: str = "unknown"


def _load_version_from_pyproject() -> str:
    """
    从 pyproject.toml 读取版本号

    Returns:
        str: 版本号字符串
    """
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            return "unknown"

    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        here = os.path.abspath(os.path.dirname(__file__))
        base_dir = os.path.abspath(os.path.join(here, os.pardir))

    pyproject_path = os.path.join(base_dir, "pyproject.toml")
    if not os.path.exists(pyproject_path):
        return "unknown"

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return data.get("project", {}).get("version", "unknown")
    except Exception:
        return "unknown"


__version__ = _load_version_from_pyproject()
