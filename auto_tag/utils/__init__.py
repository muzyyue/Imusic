"""
工具模块

提供项目通用的工具函数和 FFmpeg 执行辅助功能。
"""

import re
import os
import sys
import errno
import time
import logging
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


# ==================== 通用工具函数 ====================

def find_deepest_metadata_key(data: Dict[str, Any], key: str) -> Optional[Any]:
    """
    在嵌套字典中查找最深层的元数据键值对

    Args:
        data: 嵌套的元数据字典
        key: 要查找的键名（不区分大小写）

    Returns:
        找到的值，如果不存在则返回 None
    """
    if not isinstance(data, dict):
        return None

    # 直接匹配（不区分大小写）
    for k, v in data.items():
        if str(k).lower() == key.lower():
            return v

    # 递归搜索嵌套结构
    for v in data.values():
        if isinstance(v, dict):
            result = find_deepest_metadata_key(v, key)
            if result is not None:
                return result
        elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
            for item in v:
                result = find_deepest_metadata_key(item, key)
                if result is not None:
                    return result

    return None


def sanitize(value: Any) -> str:
    """
    清理和标准化字符串值

    Args:
        value: 输入值（可以是任意类型）

    Returns:
        清理后的安全字符串
    """
    if value is None:
        return ""

    text = str(value).strip()

    # 移除控制字符（保留换行）
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # 标准化空白字符
    text = ' '.join(text.split())

    return text


def sanitize_filename_safe(filename: str) -> str:
    """
    生成安全的文件名（移除非法字符）

    Args:
        filename: 原始文件名

    Returns:
        安全的文件名字符串
    """
    if not filename:
        return "unknown"

    # 移除 Windows/Linux 非法字符
    illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
    safe_name = re.sub(illegal_chars, '_', filename)

    # 移除首尾空格和点号
    safe_name = safe_name.strip(' .')

    # 替换连续的空格或下划线
    safe_name = re.sub(r'[\s_]+', '_', safe_name)

    # 限制长度
    max_length = 200
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length].rstrip('_')

    return safe_name or "unknown"


def is_file_in_use_error(error: Exception) -> bool:
    """
    检查异常是否为文件被占用错误

    Args:
        error: 异常对象

    Returns:
        如果是文件占用错误返回 True
    """
    if isinstance(error, OSError):
        if hasattr(errno, 'EACCES') and error.errno == errno.EACCES:
            return True
        if hasattr(errno, 'EBUSY') and error.errno == errno.EBUSY:
            return True
        if sys.platform == 'win32':
            win_error_codes = [13, 32, 33]
            if error.winerror in win_error_codes:
                return True

    error_msg = str(error).lower()
    in_use_indicators = [
        'being used by another process',
        'access is denied',
        'permission denied',
        'file is locked',
        'cannot access the file',
    ]
    return any(indicator in error_msg for indicator in in_use_indicators)


def retry_on_file_in_use(
    func,
    max_retries: int = 3,
    delay: float = 1.0,
    *args,
    **kwargs
) -> Any:
    """
    在文件被占用时自动重试的操作包装器

    Args:
        func: 要执行的函数
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        函数执行结果

    Raises:
        最后一次重试失败时的异常
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries and is_file_in_use_error(e):
                logger.warning(f"文件被占用 ({attempt + 1}/{max_retries})，{delay}秒后重试...")
                time.sleep(delay)
                continue
            raise

    raise last_exception


# ==================== FFmpeg 静默执行功能 ====================

import subprocess
import asyncio
from typing import List, Optional, Tuple


def is_windows() -> bool:
    """检测当前操作系统是否为 Windows"""
    return sys.platform == 'win32'


def get_silent_process_kwargs() -> dict:
    """
    获取 Windows 下隐藏 CMD 窗口的进程参数

    Returns:
        dict: 包含 stdin/stdout/stderr 和 creationflags 的参数字典
    """
    kwargs = {
        'stdin': subprocess.DEVNULL,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
    }

    if is_windows():
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    return kwargs


def run_ffmpeg_command(
    cmd: List[str],
    timeout: Optional[int] = None,
    **extra_kwargs
) -> Tuple[int, bytes, bytes]:
    """
    同步执行 FFmpeg 命令（隐藏窗口）

    Args:
        cmd: 命令参数列表（如 ['ffmpeg', '-i', 'input.mp4', 'output.mp3']）
        timeout: 超时时间（秒），None 表示不限时
        **extra_kwargs: 额外的 Popen 参数

    Returns:
        tuple: (返回码, stdout, stderr)

    Raises:
        subprocess.TimeoutExpired: 命令执行超时
        FileNotFoundError: ffmpeg 可执行文件未找到
    """
    kwargs = get_silent_process_kwargs()
    kwargs.update(extra_kwargs)
    kwargs.setdefault('shell', False)

    logger.debug(f"执行 FFmpeg 命令: {' '.join(cmd)}")

    process = subprocess.Popen(cmd, **kwargs)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        raise

    return process.returncode, stdout, stderr


async def async_run_ffmpeg_command(
    cmd: List[str],
    timeout: Optional[float] = None,
    **extra_kwargs
) -> Tuple[int, bytes, bytes]:
    """
    异步执行 FFmpeg 命令（隐藏窗口）

    Args:
        cmd: 命令参数列表
        timeout: 超时时间（秒），None 表示不限时
        **extra_kwargs: 额外的 create_subprocess_exec 参数

    Returns:
        tuple: (返回码, stdout, stderr)

    Raises:
        asyncio.TimeoutError: 命令执行超时
        FileNotFoundError: ffmpeg 可执行文件未找到
    """
    kwargs = get_silent_process_kwargs()
    kwargs.update(extra_kwargs)

    logger.debug(f"异步执行 FFmpeg 命令: {' '.join(cmd)}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        **kwargs
    )

    try:
        if timeout:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        else:
            stdout, stderr = await process.communicate()
    except asyncio.TimeoutError:
        process.kill()
        stdout, stderr = process.communicate()
        raise

    return process.returncode, stdout, stderr


def apply_subprocess_monkey_patch() -> None:
    """
    应用全局猴子补丁，自动为所有 subprocess.Popen 调用添加窗口隐藏参数

    此函数应在程序启动时调用（如在 GUI 初始化之前），
    可以自动修复包括 ffmpeg-python 在内的所有第三方库的进程创建行为。

    注意：
    - 仅在 Windows 系统下生效
    - 会影响所有后续的 subprocess.Popen 调用
    - 如果某些场景需要显示窗口，可以通过 extra_kwargs 显式覆盖
    """
    if not is_windows():
        logger.debug("非 Windows 系统，跳过 subprocess 猴子补丁")
        return

    _original_popen = subprocess.Popen

    def _silent_popen(*args, **kwargs):
        # 自动添加窗口隐藏参数（如果未显式设置）
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        # 设置标准输入输出（如果未显式设置）
        if kwargs.get('stdin', None) is None:
            kwargs['stdin'] = subprocess.DEVNULL
        if kwargs.get('stdout', None) is None:
            kwargs['stdout'] = subprocess.PIPE
        if kwargs.get('stderr', None) is None:
            kwargs['stderr'] = subprocess.PIPE

        return _original_popen(*args, **kwargs)

    # 应用补丁
    subprocess.Popen = _silent_popen
    logger.info("已应用 subprocess 全局猴子补丁，所有子进程将隐藏CMD窗口")


def setup_ffmpeg_silent_mode() -> None:
    """
    初始化 FFmpeg 静默模式（一次性配置）

    此函数整合了所有必要的初始化步骤：
    1. 应用 subprocess 猴子补丁
    2. 配置 ffmpeg-python 库（如果可用）

    应在程序启动时调用一次即可。
    """
    logger.info("正在初始化 FFmpeg 静默执行模式...")

    # 应用全局猴子补丁
    apply_subprocess_monkey_patch()

    # 尝试配置 ffmpeg-python 库
    try:
        import ffmpeg as ffmpeg_lib
        # ffmpeg-python 使用 subprocess.run 或 subprocess.Popen 内部实现
        # 通过猴子补丁已经可以覆盖大部分情况
        logger.info("ffmpeg-python 库将通过猴子补丁自动优化")
    except ImportError:
        logger.debug("ffmpeg-python 库未安装，跳过配置")

    logger.info("FFmpeg 静默模式初始化完成")


# ==================== 模块导出列表 ====================

__all__ = [
    # === 通用工具函数 ===
    'find_deepest_metadata_key',
    'sanitize',
    'sanitize_filename_safe',
    'is_file_in_use_error',
    'retry_on_file_in_use',

    # === FFmpeg 静默执行相关函数 ===
    'is_windows',
    'get_silent_process_kwargs',
    'run_ffmpeg_command',
    'async_run_ffmpeg_command',
    'apply_subprocess_monkey_patch',
    'setup_ffmpeg_silent_mode',
]
