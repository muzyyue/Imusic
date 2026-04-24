from unidecode import unidecode
import time
import logging

logger = logging.getLogger(__name__)

# Windows 文件占用错误码
WINDOWS_FILE_IN_USE_ERROR = 32


def is_file_in_use_error(exc: Exception) -> bool:
    """
    判断异常是否由文件被占用引起

    Args:
        exc (Exception): 异常对象

    Returns:
        bool: 如果是由文件被占用引起返回 True，否则返回 False
    """
    # Windows: [WinError 32] 另一个程序正在使用此文件
    if hasattr(exc, 'winerror') and getattr(exc, 'winerror') == WINDOWS_FILE_IN_USE_ERROR:
        return True
    # PermissionError 通常表示文件被占用
    if isinstance(exc, PermissionError):
        return True
    # 检查错误信息中是否包含文件占用的关键字
    error_msg = str(exc).lower()
    keywords = ['被占用', 'in use', 'being used', 'locked', 'file busy']
    return any(keyword in error_msg for keyword in keywords)


def retry_on_file_in_use(func, max_retries: int = 3, delay: float = 0.5, **kwargs):
    """
    文件占用重试装饰器

    当文件操作因文件被占用而失败时，自动重试指定次数。

    Args:
        func: 要执行的函数
        max_retries (int): 最大重试次数，默认 3 次
        delay (float): 重试间隔（秒），默认 0.5 秒
        **kwargs: 传递给 func 的关键字参数

    Returns:
        函数执行结果

    Raises:
        Exception: 如果所有重试都失败，抛出最后一次异常
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return func(**kwargs)
        except Exception as exc:
            last_error = exc

            if not is_file_in_use_error(exc) or attempt == max_retries:
                raise

            # 等待后重试
            wait_time = delay * (attempt + 1)  # 递增等待时间
            logger.warning(
                f"文件被占用，将在 {wait_time:.1f} 秒后重试 "
                f"({attempt + 1}/{max_retries}): {exc}"
            )
            time.sleep(wait_time)

    raise last_error


def find_deepest_metadata_key(data, search_key):
    """
    Recursively searches for the 'text' value corresponding to a given 'title' key
    in a deeply nested structure of lists and dictionaries.

    Args:
        data (dict or list): The nested data to search.
        search_key (str): The 'title' value to search for.

    Returns:
        str or None: The 'text' value corresponding to the search_key, or None if not found.
    """
    # If the current level is a dictionary, search within it
    if isinstance(data, dict):
        # Check if the dictionary contains the 'title' and 'text' keys and matches the search_key
        if data.get("title") == search_key and "text" in data:
            return data["text"]
        # Otherwise, recurse into the dictionary's values
        for value in data.values():
            result = find_deepest_metadata_key(value, search_key)
            if result is not None:
                return result

    # If the current level is a list, iterate through it and search each item
    elif isinstance(data, list):
        for item in data:
            result = find_deepest_metadata_key(item, search_key)
            if result is not None:
                return result

    # If no match is found, return None
    return None


def sanitize(s: str, trace: bool) -> str:
    original = s
    s = unidecode(s)

    out, depth = "", 0
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
        elif depth == 0:
            out += ch
    s = out or original

    for bad in '<>:"/\\|?*':
        s = s.replace(bad, "")
    s = s.replace("&", "-")
    s = " ".join(w.capitalize() for w in s.split())

    if not s.strip():
        if trace:
            print("sanitize produced empty string for:", original)
        s = "Unknown"
    return s


def sanitize_filename_safe(s: str) -> str:
    """
    安全的文件名处理函数（保留原始语言字符）

    只移除文件系统非法字符，保留日语、中文、韩语等多语言字符。
    与 sanitize() 不同，本函数不使用 unidecode() 转换。

    Args:
        s (str): 原始字符串

    Returns:
        str: 处理后的安全字符串
    """
    if not s:
        return ""

    # 移除括号内容（与原 sanitize 保持一致）
    out, depth = "", 0
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
        elif depth == 0:
            out += ch
    s = out or s

    # 只移除文件系统非法字符，保留多语言字符
    for bad in '<>:"/\\|?*':
        s = s.replace(bad, "")
    s = s.replace("&", "-")

    # 移除首尾空格
    s = s.strip()

    if not s:
        s = "Unknown"

    return s
