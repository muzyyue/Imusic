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


# ==================== 中英文文本处理工具 ====================

def split_multilingual_text(text: str) -> dict:
    """
    多语言文本分离器 - 支持中日韩泰越俄阿等多语言

    智能识别并提取混合名称中的各种语言成分，
    将非拉丁字母语言统一归类为 native 部分，拉丁字母归为 latin 部分。

    支持的语言：
    - 🇨🇳 中文: 小小奇迹、晴天
    - 🇯🇵 日文: 準備フェイズ、アニメソング
    - 🇰🇷 韩文: 사랑해요、안녕하세요
    - 🇹🇭 泰文: สวัสดี、รักเธอ
    - 🇻🇳 越南文: Xin chào、Yêu bạn
    - 🇷🇺 俄文: Привет、Люблю тебя
    - 🇸🇦 阿拉伯文: مرحبا、أحبك
    - 🇮🇳 印地文: नमस्ते、प्यार करता हूँ

    Args:
        text: 输入文本（可能包含多语言混合）

    Returns:
        dict: 分离结果字典
            - native (str): 非拉丁字母部分（中日韩泰越俄阿等）
            - latin (str): 拉丁字母/数字部分（英文等）
            - original (str): 原始输入文本
            - has_both (bool): 是否同时包含 native 和 latin
            - detected_languages (list): 检测到的语言列表

    Example:
        >>> split_chinese_english_text("A Small Miracle 小小奇迹")
        {'native': '小小奇迹', 'latin': 'A Small Miracle', ...}

        >>> split_chinese_english_text("準備フェイズ Vol.31")
        {'native': '準備フェイズ', 'latin': 'Vol 31', ...}

        >>> split_chinese_english_text("사랑해요 Love Song")
        {'native': '사랑해요', 'latin': 'Love Song', ...}
    """
    if not text or not isinstance(text, str):
        return {
            'native': '',
            'latin': '',
            'original': '',
            'has_both': False,
            'detected_languages': []
        }

    original = text.strip()
    if not original:
        return {
            'native': '',
            'latin': '',
            'original': '',
            'has_both': False,
            'detected_languages': []
        }

    # ==================== 语言定义 ====================
    # 各语言的 Unicode 范围

    LANGUAGE_PATTERNS = {
        # 东亚语言
        'chinese': r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]',  # CJK Unified Ideographs
        'japanese_hiragana': r'[\u3040-\u309f]',                   # 平假名
        'japanese_katakana': r'[\u30a0-\u30ff\u31f0-\u31ff]',     # 片假名（含片假名语音扩展）
        'korean': r'[\uac00-\ud7af\u1100-\u11ff]',                 # 韩文音节 + Jamo

        # 东南亚语言
        'thai': r'[\u0e00-\u0e7f]',                               # 泰文
        'vietnamese_tone': r'[\u0300-\u036f\u1ab0-\u1aff]',       # 越南语声调符号（组合字符）

        # 西里尔字母（俄文等）
        'cyrillic': r'[\u0400-\u04ff\u0500-\u052f]',              # 西里尔字母

        # 阿拉伯字母
        'arabic': r'[\u0600-\u06ff\u0750-\u077f\ufb50-\ufdff\ufe70-\ufeff]',  # 阿拉伯文

        # 印度语言（天城文等）
        'devanagari': r'[\u0900-\u097f]',                         # 天城文（印地语等）

        # 其他可能的非拉丁文字
        'greek': r'[\u0370-\u03ff]',                              # 希腊字母
        'georgian': r'[\u10a0-\u10ff]',                          # 格鲁吉亚文
        'armenian': r'[\u0530-\u058f]',                         # 亚美尼亚文
    }

    # 拉丁字母和数字模式
    # 使用 Python re 模块支持的 \uXXXX 格式（不是 PCRE 的 \x{} 格式）
    LATIN_PATTERN = r'[a-zA-Z\u00C0-\u024F\u1E00-\u1EFF][a-zA-Z0-9\s\'\-]*'
    DIGIT_PATTERN = r'[0-9]+'

    # ==================== 语言检测 ====================
    detected_languages = []

    for lang_name, pattern in LANGUAGE_PATTERNS.items():
        if re.search(pattern, original):
            if lang_name not in detected_languages:
                detected_languages.append(lang_name)

    has_latin = bool(re.search(r'[a-zA-Z]', original))
    has_digit = bool(re.search(r'[0-9]', original))

    # 判断是否为特殊语言文本（需要保持连贯性）
    is_japanese = any(l in detected_languages for l in ['japanese_hiragana', 'japanese_katakana'])
    is_korean = 'korean' in detected_languages
    is_thai = 'thai' in detected_languages
    is_arabic = 'arabic' in detected_languages
    is_cyrillic = 'cyrillic' in detected_languages

    is_special_language = is_japanese or is_korean or is_thai or is_arabic or is_cyrillic

    # ==================== 文本提取 ====================

    # 构建统一的非拉丁字符模式（所有非拉丁语言）
    NON_LATIN_PATTERN = '|'.join(LANGUAGE_PATTERNS.values())
    non_latins_pattern = f'(?:{NON_LATIN_PATTERN})+'

    # 提取非拉丁字符片段
    native_matches = re.findall(non_latins_pattern, original)

    # 提取拉丁字符/数字片段
    latin_matches = re.findall(LATIN_PATTERN, original)
    digit_matches = re.findall(DIGIT_PATTERN, original)

    # 合并非拉丁字符
    if is_special_language:
        # 特殊语言：用空字符串连接（保持连贯性）
        native_part = ''.join(''.join(m) if isinstance(m, tuple) else m for m in native_matches)
    else:
        # 中文等：可以适当分隔
        native_raw = ''.join(''.join(m) if isinstance(m, tuple) else m for m in native_matches)

        # 对于纯中文或中英混合，尝试按语义单位分割（可选）
        # 这里简单处理：直接连接
        native_part = native_raw

    native_part = native_part.strip()

    # 合并拉丁字符
    latin_raw = ' '.join(latin_matches) + ' ' + ' '.join(digit_matches)
    latin_part = re.sub(r'\s+', ' ', latin_raw).strip()

    # 清理拉丁部分
    def _clean_latin(text: str) -> str:
        """清理拉丁部分，移除无效内容"""
        if not text:
            return ''
        words = text.split()
        cleaned_words = []
        for word in words:
            if len(word) >= 2 or (word.isdigit() and len(word) >= 2):
                cleaned_words.append(word)
            elif word and not word.isdigit():
                cleaned_words.append(word)
        result = ' '.join(cleaned_words)
        return result if len(result) >= 2 else ''

    latin_part = _clean_latin(latin_part)

    has_both = bool(native_part) and bool(latin_part)

    # ==================== 智能优化 ====================

    # 如果提取的 native 部分太短但原文很长，说明可能是错误拆分
    if is_special_language and len(native_part) < 4 and len(original) > 8:
        first_latin_match = re.search(LATIN_PATTERN, original)
        if first_latin_match:
            lat_start = first_latin_match.start()
            native_before_lat = original[:lat_start].strip()
            if len(native_before_lat) > len(native_part):
                native_part = native_before_lat

    # 语言名称映射（用于日志输出）
    LANG_DISPLAY_NAMES = {
        'chinese': 'Chinese',
        'japanese_hiragana': 'Japanese(Hiragana)',
        'japanese_katakana': 'Japanese(Katakana)',
        'korean': 'Korean',
        'thai': 'Thai',
        'cyrillic': 'Cyrillic(Russian)',
        'arabic': 'Arabic',
        'devanagari': 'Devanagari(Hindi)',
        'greek': 'Greek',
    }

    detected_display = [LANG_DISPLAY_NAMES.get(l, l) for l in detected_languages]

    logger.debug(
        f"[TextSplit] Input: '{original[:50]}...' "
        f"→ Native: '{native_part[:30]}...', Latin: '{latin_part[:30]}...', "
        f"Languages: {detected_display}"
    )

    return {
        'native': native_part,
        'latin': latin_part,
        'original': original,
        'has_both': has_both,
        'detected_languages': detected_display
    }


def is_multilingual_text(text: str) -> bool:
    """
    检测文本是否同时包含非拉丁字符和拉丁/英文字符

    支持检测中日韩泰越俄阿等多语言与英文的混合。

    Args:
        text: 待检测的文本

    Returns:
        bool: 如果同时包含非拉丁字符（CJK、韩文、泰文等）和英文字符返回 True，否则返回 False
    """
    if not text or not isinstance(text, str):
        return False

    # 非拉丁字母模式（包含所有支持的语言）
    NON_LATIN_PATTERN = (
        r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff'  # CJK Unified Ideographs
        r'\u3040-\u309f\u31f0-\u31ff'              # Japanese Hiragana
        r'\u30a0-\u30ff'                             # Japanese Katakana
        r'\uac00-\ud7af\u1100-\u11ff'               # Korean
        r'\u0e00-\u0e7f'                             # Thai
        r'\u0400-\u04ff\u0500-\u052f'               # Cyrillic
        r'\u0600-\u06ff\u0750-\u077f'               # Arabic
        r'\u0900-\u097f'                             # Devanagari
        r']'
    )

    has_non_latin = bool(re.search(NON_LATIN_PATTERN, text))
    has_latin = bool(re.search(r'[a-zA-Z]', text))

    return has_non_latin and has_latin


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

    # === 中英文文本处理工具 ===
    'split_multilingual_text',
    'is_multilingual_text',

    # === FFmpeg 静默执行相关函数 ===
    'is_windows',
    'get_silent_process_kwargs',
    'run_ffmpeg_command',
    'async_run_ffmpeg_command',
    'apply_subprocess_monkey_patch',
    'setup_ffmpeg_silent_mode',
]
