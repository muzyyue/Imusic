# -*- coding: utf-8 -*-
"""
版本号自动更新脚本

从 pyproject.toml 提取版本号并写入 auto_tag/version.py，
解决 PyInstaller 打包后无法获取版本号的问题。

Usage:
    python build_tools/update_version.py

该脚本会在 PyInstaller 构建前自动调用（集成在 Imusic.spec 中），
确保 version.py 始终包含最新的硬编码版本号。
"""

import os
import sys
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def read_version_from_pyproject(project_root: Path) -> str:
    """
    从 pyproject.toml 读取版本号

    Args:
        project_root: 项目根目录路径

    Returns:
        str: 版本号字符串

    Raises:
        FileNotFoundError: pyproject.toml 不存在
        KeyError: version 字段不存在
    """
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml 不存在: {pyproject_path}")

    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError as e:
            raise ImportError("需要 tomllib (Python 3.11+) 或 tomli 库") from e

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    version = data.get("project", {}).get("version")
    if not version:
        raise KeyError("pyproject.toml 中未找到 project.version")

    return str(version)


def write_version_file(version: str, project_root: Path) -> None:
    """
    将版本号写入 auto_tag/version.py

    Args:
        version: 版本号字符串
        project_root: 项目根目录路径
    """
    version_file = project_root / "auto_tag" / "version.py"

    content = f"""# -*- coding: utf-8 -*-
\"\"\"
版本号模块

版本号由 build_tools/update_version.py 自动从 pyproject.toml 提取。
PyInstaller 打包后，此文件被编译为 .pyc，无需依赖外部文件。

Attributes:
    __version__ (str): 应用版本号
\"\"\"

__version__ = "{version}"
"""

    with open(version_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[OK] 版本号已更新: {version}")
    print(f"    文件: {version_file}")


def main() -> int:
    """主函数"""
    try:
        project_root = get_project_root()
        version = read_version_from_pyproject(project_root)
        write_version_file(version, project_root)
        return 0
    except Exception as e:
        print(f"[FAIL] 更新版本号失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
