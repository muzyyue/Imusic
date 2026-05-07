# -*- coding: utf-8 -*-
"""
验证工具模块

该模块提供各种数据验证功能，包括QQ音乐Cookie格式验证等。
所有验证函数返回统一的 (is_valid, error_message) 元组格式。

功能：
    - QQ音乐Cookie格式验证
    - 通用字符串验证

使用示例：
    >>> from auto_tag.utils.validation import validate_qq_music_cookie
    >>> is_valid, error = validate_qq_music_cookie("uin=xxx; qm_keyst=xxx")
    >>> if not is_valid:
    ...     print(f"验证失败: {error}")
"""

from typing import Tuple


def validate_qq_music_cookie(cookie: str) -> Tuple[bool, str]:
    """
    验证QQ音乐Cookie格式是否正确

    该函数执行以下检查：
    1. 非空检查：Cookie不能为空或仅包含空白字符
    2. 基本格式检查：必须符合 key=value; key=value 格式
    3. 必要字段检查：至少包含 uin、qm_keyst、qqmusic_key 中的一个
    4. 长度检查：长度必须在合理范围内（10-10000字符）

    Args:
        cookie (str): 待验证的Cookie字符串

    Returns:
        Tuple[bool, str]: 验证结果元组
            - 第一个元素: True 表示验证通过，False 表示验证失败
            - 第二个元素: 错误信息（验证通过时为空字符串）

    Example:
        >>> # 有效Cookie
        >>> is_valid, error = validate_qq_music_cookie("uin=2253373466; qm_keyst=Q_H_L_63k...")
        >>> print(is_valid, error)
        True ''

        >>> # 空Cookie
        >>> is_valid, error = validate_qq_music_cookie("")
        >>> print(is_valid, error)
        False 'Cookie不能为空'

        >>> # 缺少必要字段
        >>> is_valid, error = validate_qq_music_cookie("test=value; foo=bar")
        >>> print(is_valid, error)
        False 'Cookie缺少必要字段: uin, qm_keyst, qqmusic_key'

    Note:
        - 此函数仅做基本格式验证，不验证Cookie是否有效或未过期
        - 实际有效性需要通过API调用测试
        - Cookie是敏感信息，日志输出时应脱敏处理
    """
    # 使用硬编码常量避免循环依赖（与AppConfig保持同步）
    min_length = 10
    max_length = 10000
    required_keys = ('uin', 'qm_keyst', 'qqmusic_key')

    # 1. 非空检查
    if not cookie or not cookie.strip():
        return False, "Cookie不能为空"

    cookie = cookie.strip()

    # 2. 长度检查（先于格式检查，快速失败）
    if len(cookie) < min_length:
        return False, f"Cookie过短（最少 {min_length} 个字符）"

    if len(cookie) > max_length:
        return False, f"Cookie过长（最多 {max_length} 个字符）"

    # 3. 基本格式检查：必须包含 key=value 结构
    if '=' not in cookie:
        return False, "Cookie格式无效：缺少键值对（key=value）"

    # 尝试解析Cookie为字典
    try:
        cookie_items = [item.strip() for item in cookie.split(';') if item.strip()]
        if not cookie_items:
            return False, "Cookie格式无效：无法解析键值对"

        cookie_dict = {}
        for item in cookie_items:
            if '=' in item:
                key, value = item.split('=', 1)
                cookie_dict[key.strip()] = value.strip()
            else:
                # 允许某些项没有值，但至少大部分应该有
                pass

    except Exception as e:
        return False, f"Cookie解析错误: {str(e)}"

    # 4. 必要字段检查：至少包含一个关键字段
    has_required_key = any(key in cookie_dict for key in required_keys)
    if not has_required_key:
        required_keys_str = ', '.join(required_keys)
        return False, f"Cookie缺少必要字段: {required_keys_str}"

    # 所有检查通过
    return True, ""


def mask_cookie_for_logging(cookie: str, visible_chars: int = 8) -> str:
    """
    对Cookie进行脱敏处理，用于日志输出

    保留前 visible_chars 个字符和最后4个字符，中间用 *** 替代。

    Args:
        cookie (str): 原始Cookie字符串
        visible_chars (int): 开头保留的可见字符数，默认为8

    Returns:
        str: 脱敏后的Cookie字符串

    Example:
        >>> mask_cookie_for_logging("uin=2253373466; qm_keyst=Q_H_L_63k3NmGdH_FJPT48vSrkI5ftXyQV0ZWjm0vfChA4QcVVKvWAiMlZqjNCYivrVAPTwUU0VJaE8YEtaxYtPEbycR-XucUSq2A")
        'uin=225***jNCYivrVAPTwUU0VJaE8YEtaxYtPEbycR-XucUSq2A'

        >>> mask_cookie_for_logging("")
        ''
    """
    if not cookie or len(cookie) <= visible_chars + 4:
        return cookie

    return f"{cookie[:visible_chars]}...{cookie[-4:]}"


def is_cookie_empty_or_whitespace(cookie: str) -> bool:
    """
    检查Cookie是否为空或仅包含空白字符

    Args:
        cookie (str): 待检查的Cookie字符串

    Returns:
        bool: True 表示为空或仅空白，False 表示有实际内容

    Example:
        >>> is_cookie_empty_or_whitespace("")
        True
        >>> is_cookie_empty_or_whitespace("   \\t\\n  ")
        True
        >>> is_cookie_empty_or_whitespace("uin=123")
        False
    """
    return not cookie or not cookie.strip()


def extract_cookie_key_value(cookie: str, key: str) -> str | None:
    """
    从Cookie字符串中提取指定键的值

    Args:
        cookie (str): Cookie字符串
        key (str): 要提取的键名（如 "uin", "qm_keyst"）

    Returns:
        str | None: 键对应的值，如果不存在则返回 None

    Example:
        >>> cookie = "uin=2253373466; qm_keyst=Q_H_L_63k"
        >>> extract_cookie_key_value(cookie, "uin")
        '2253373466'
        >>> extract_cookie_key_value(cookie, "nonexistent")
        None
    """
    if not cookie or not cookie.strip():
        return None

    try:
        for item in cookie.split(';'):
            item = item.strip()
            if '=' in item:
                k, v = item.split('=', 1)
                if k.strip() == key:
                    return v.strip()
    except Exception:
        pass

    return None
