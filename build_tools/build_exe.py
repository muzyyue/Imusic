#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys


def run(cmd, **kwargs):
    print(f"\n$ {' '.join(cmd)}")
    res = subprocess.run(cmd, check=False, **kwargs)
    if res.returncode != 0:
        print(f"✖ Command failed with exit code {res.returncode}. Aborting.")
        sys.exit(res.returncode)


def main():
    # This script lives in <project_root>/build_tools/
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

        # 4) Build executable
        ico_path = os.path.join(project_root, "assets", "auto_tag.ico")
        # on Windows use ';', on POSIX use ':'
        delim = ";" if os.name == "nt" else ":"
        add_data_arg = f"{ico_path}{delim}assets"

        run(
            [
                python,
                "-m",
                "PyInstaller",
                "--onefile",
                "--noconsole",
                f"--icon={ico_path}",
                f"--add-data={add_data_arg}",
                "--workpath=build",
                "--distpath=build",
                "--specpath=build",
                "main.py",
            ]
        )

        print(
            "\n✅ Build complete!  Check the `build/` directory under your project root."
        )
    finally:
        os.chdir(cwd_before)


if __name__ == "__main__":
    main()
