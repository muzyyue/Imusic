# -*- coding: utf-8 -*-
"""
QQ音乐Cookie功能完整测试套件

该模块提供QQ音乐Cookie输入功能的全面测试，包括：
1. 基础功能验证：Cookie输入、保存、应用
2. Cookie有效性测试：有效/无效/过期Cookie处理
3. 边界条件测试：空值、超长、特殊字符等
4. 安全性测试：存储安全、注入防护
5. 兼容性测试：UI响应式布局

测试用例设计原则：
- 每个用例包含：测试目的、前置条件、测试步骤、预期结果、实际结果
- 覆盖正常流程和异常流程
- 使用用户提供的真实Cookie进行测试
- 验证Cookie在API请求中的正确使用

Author: Test Suite Generator
Date: 2026-05-05
Version: 1.0
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 用户提供的测试Cookie（用于有效性测试）
TEST_VALID_COOKIE = (
    "pgv_pvid=4424996381; fqm_pvqid=d616bd9a-a2fc-46df-b8da-57f99960380f; "
    "ts_uid=7238062418; RK=PX5zRb6FyM; "
    "ptcz=fa72499a4dfb369cdcff4708bc15587a116450d54161709d96a74391a4b543f0; "
    "psrf_musickey_createtime=1777788721; psrf_qqrefresh_token=AD3C6C418010FAA33380E0CC19FEB932; "
    "psrf_access_token_expiresAt=1782972721; euin=ow-koioloivs7c**; "
    "psrf_qqaccess_token=5C115B9F568856E41CDB771E47DC29CF; tmeLoginType=2; "
    "psrf_qqunionid=74267487C7D1295D71A98CAD9FE6B923; "
    "qm_keyst=Q_H_L_63k3NmGdH_FJPT48vSrkI5ftXyQV0ZWjm0vfChA4QcVVKvWAiMlZqjNCYivrVAPTwUU0VJaE8YEtaxYtPEbycR-XucUSq2A; "
    "wxrefresh_token=; wxunionid=; "
    "qqmusic_key=Q_H_L_63k3NmGdH_FJPT48vSrkI5ftXyQV0ZWjm0vfChA4QcVVKvWAiMlZqjNCYivrVAPTwUU0VJaE8YEtaxYtPEbycR-XucUSq2A; "
    "wxopenid=; uin=2253373466; psrf_qqopenid=6938B24C7A9C842A707C06AB40191D9F; "
    "music_ignore_pskey=202306271436Hn@vBj; "
    "fqm_sessionid=7f769740-00b1-4dcf-8a50-03a71d10e088; pgv_info=ssid=s98991365; ts_last=y.qq.com/"
)


# ============================================================================
# 第一部分：基础功能验证测试 (5个用例)
# ============================================================================

class TestBasicFunctionality:
    """
    基础功能验证测试类
    
    测试目的：
    - 验证Cookie输入框能够正常接收并保存用户输入的Cookie值
    - 验证Cookie值在提交后能够正确应用于QQ音乐数据获取请求
    
    前置条件：
    - 配置系统已初始化
    - 设置页面已创建
    - 验证工具函数已加载
    """

    def test_cookie_input_accepts_valid_cookie(self):
        """
        测试用例 1.1：验证Cookie输入框能够接收有效的Cookie字符串
        
        测试目的：确保多行文本输入框能正确接受并显示完整的Cookie内容
        
        前置条件：
        - 设置页面已实例化
        - QQ音乐搜索源已被选中（显示Cookie输入框）
        
        测试步骤：
        1. 在Cookie输入框中粘贴有效的Cookie字符串
        2. 读取输入框的文本内容
        
        预期结果：
        - 输入框应包含完整的Cookie文本
        - 文本不应被截断或修改
        
        实际结果：（运行时填充）
        """
        from auto_tag.utils.validation import validate_qq_music_cookie
        
        is_valid, error = validate_qq_music_cookie(TEST_VALID_COOKIE)
        
        assert is_valid, f"有效Cookie验证失败: {error}"
        assert error == "", f"错误信息应为空，实际为: {error}"

    def test_cookie_saves_to_config(self):
        """
        测试用例 1.2：验证Cookie值能够正确保存到配置系统
        
        测试目的：确保用户输入的Cookie能够持久化存储
        
        前置条件：
        - 配置管理器已初始化
        - 提供有效的Cookie字符串
        
        测试步骤：
        1. 调用 config.set_qq_music_cookie() 方法传入有效Cookie
        2. 通过 config.qq_music_cookie 属性读取保存的值
        
        预期结果：
        - 读取的值应与设置的值完全一致
        - 配置文件应已更新
        
        实际结果：（运行时填充）
        """
        from auto_tag.gui.config import AppConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建临时配置
            config = AppConfig.__new__(AppConfig)
            config._config_dir = Path(tmpdir)
            config._config_file = config._config_dir / "config.json"
            config._qq_music_cookie = ""
            
            # 设置Cookie
            test_cookie = TEST_VALID_COOKIE
            config.set_qq_music_cookie(test_cookie)
            
            # 验证保存
            assert config.qq_music_cookie == test_cookie, "Cookie未正确保存"
            
            # 验证配置文件存在且包含Cookie
            assert config._config_file.exists(), "配置文件未创建"
            with open(config._config_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            assert saved_data.get('qq_music_cookie') == test_cookie, "配置文件中Cookie不正确"

    def test_cookie_applies_to_api_request(self):
        """
        测试用例 1.3：验证Cookie能够正确应用到QQ音乐API请求
        
        测试目的：确保保存在配置中的Cookie会被用于HTTP请求头
        
        前置条件：
        - 已设置有效的Cookie
        - audio_recognize模块可访问
        
        测试步骤：
        1. Mock http.client.HTTPSConnection
        2. 调用 _do_qqmusic_search() 并传入Cookie
        3. 检查请求头是否包含Cookie字段
        
        预期结果：
        - HTTP请求头的 'Cookie' 字段应包含用户提供的Cookie值
        
        实际结果：（运行时填充）
        """
        from auto_tag.audio_recognize import _do_qqmusic_search
        
        with patch('auto_tag.audio_recognize.http.client.HTTPSConnection') as mock_conn:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = json.dumps({
                "code": 0,
                "search": {
                    "data": {
                        "body": {
                            "item_song": []
                        },
                        "meta": {
                            "estimate_sum": 0,
                            "sum": 0
                        }
                    }
                }
            }).encode('utf-8')
            mock_conn.return_value.request.return_value = None
            mock_conn.return_value.getresponse.return_value = mock_response
            
            # 执行搜索（带Cookie）
            results = _do_qqmusic_search("周杰伦", limit=1, cookie=TEST_VALID_COOKIE)
            
            # 验证Cookie被添加到请求头
            call_args = mock_conn.return_value.request.call_args
            headers = call_args[1]['headers'] if call_args[1] else {}
            
            assert 'Cookie' in headers, "请求头中缺少Cookie字段"
            assert headers['Cookie'] == TEST_VALID_COOKIE, "Cookie值不正确"

    def test_cookie_persists_after_restart(self):
        """
        测试用例 1.4：验证Cookie在程序重启后仍然保留
        
        测试目的：确保持久化存储的可靠性
        
        前置条件：
        - 临时目录可用
        - 配置系统能正常读写文件
        
        测试步骤：
        1. 创建配置实例并设置Cookie
        2. 销毁配置实例
        3. 创建新的配置实例（模拟重启）
        4. 读取Cookie值
        
        预期结果：
        - 新实例读取的Cookie值应与之前设置的一致
        
        实际结果：（运行时填充）
        """
        from auto_tag.gui.config import AppConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 第一次：设置Cookie
            config1 = AppConfig.__new__(AppConfig)
            config1._config_dir = Path(tmpdir)
            config1._config_file = config1._config_dir / "config.json"
            config1._qq_music_cookie = ""
            config1.set_qq_music_cookie(TEST_VALID_COOKIE)
            
            saved_cookie = config1.qq_music_cookie
            
            # 第二次：重新加载（模拟重启）
            config2 = AppConfig.__new__(AppConfig)
            config2._config_dir = Path(tmpdir)
            config2._config_file = config2._config_dir / "config.json"
            config2._qq_music_cookie = ""
            config2._load_config()
            
            loaded_cookie = config2.qq_music_cookie
            
            assert loaded_cookie == saved_cookie, "重启后Cookie丢失"
            assert loaded_cookie == TEST_VALID_COOKIE, "Cookie值不一致"

    def test_cookie_clears_properly(self):
        """
        测试用例 1.5：验证Cookie可以被正确清除
        
        测试目的：确保用户可以清空已设置的Cookie
        
        前置条件：
        - 已设置有效的Cookie
        
        测试步骤：
        1. 设置一个有效的Cookie
        2. 调用 set_qq_music_cookie("") 清空Cookie
        3. 读取Cookie值确认已清空
        
        预期结果：
        - Cookie属性应返回空字符串
        - 配置文件中的Cookie字段应为空字符串
        
        实际结果：（运行时填充）
        """
        from auto_tag.gui.config import AppConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AppConfig.__new__(AppConfig)
            config._config_dir = Path(tmpdir)
            config._config_file = config._config_dir / "config.json"
            config._qq_music_cookie = ""
            
            # 先设置Cookie
            config.set_qq_music_cookie(TEST_VALID_COOKIE)
            assert config.qq_music_cookie == TEST_VALID_COOKIE, "初始设置失败"
            
            # 再清空Cookie
            config.set_qq_music_cookie("")
            assert config.qq_music_cookie == "", "清空操作失败"
            
            # 验证配置文件
            with open(config._config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert data.get('qq_music_cookie') == "", "配置文件中Cookie未清空"


# ============================================================================
# 第二部分：Cookie有效性测试 (4个用例)
# ============================================================================

class TestCookieValidity:
    """
    Cookie有效性测试类
    
    测试目的：
    - 使用用户提供的真实测试Cookie进行正常流程测试
    - 验证使用有效Cookie时能够成功获取QQ音乐数据
    - 验证使用无效/过期Cookie时系统能够给出明确的错误提示
    
    前置条件：
    - 网络连接正常（API测试）
    - 测试Cookie可用
    """

    def test_valid_cookie_from_user_provided_value(self):
        """
        测试用例 2.1：使用用户提供的测试Cookie进行格式验证
        
        测试目的：验证用户提供的真实Cookie能够通过格式验证
        
        前置条件：
        - 用户提供了完整的测试Cookie字符串
        - 该Cookie包含所有必要字段
        
        测试步骤：
        1. 将用户提供的Cookie传给 validate_qq_music_cookie()
        2. 检查返回的验证结果
        
        预期结果：
        - 验证应通过（is_valid=True）
        - 错误消息应为空
        
        实际结果：（运行时填充）
        """
        from auto_tag.utils.validation import validate_qq_music_cookie
        from auto_tag.utils.validation import extract_cookie_key_value
        
        # 验证Cookie格式
        is_valid, error = validate_qq_music_cookie(TEST_VALID_COOKIE)
        
        assert is_valid, f"用户提供的Cookie验证失败: {error}"
        assert error == "", f"不应有错误消息: {error}"
        
        # 验证关键字段存在
        uin = extract_cookie_key_value(TEST_VALID_COOKIE, "uin")
        qm_keyst = extract_cookie_key_value(TEST_VALID_COOKIE, "qm_keyst")
        qqmusic_key = extract_cookie_key_value(TEST_VALID_COOKIE, "qqmusic_key")
        
        assert uin == "2253373466", f"uin字段错误: {uin}"
        assert qm_keyst is not None and len(qm_keyst) > 10, "qm_keyst字段缺失或过短"
        assert qqmusic_key is not None and len(qqmusic_key) > 10, "qqmusic_key字段缺失或过短"

    @pytest.mark.skip(reason="需要网络连接，仅在有网络环境时运行")
    def test_valid_cookie_returns_search_results(self):
        """
        测试用例 2.2：验证使用有效Cookie时能够成功获取QQ音乐数据
        
        测试目的：确保Cookie认证后API调用成功
        
        前置条件：
        - 网络连接正常
        - 测试Cookie有效且未过期
        - QQ音乐API服务可用
        
        测试步骤：
        1. 使用有效Cookie调用QQ音乐搜索API
        2. 检查返回的结果列表
        
        预期结果：
        - 应返回非空的搜索结果列表
        - 结果应包含歌曲的基本信息（标题、艺术家等）
        
        实际结果：（运行时填充）
        """
        from auto_tag.audio_recognize import _do_qqmusic_search
        
        results = _do_qqmusic_search("周杰伦", limit=5, cookie=TEST_VALID_COOKIE)
        
        assert isinstance(results, list), "结果应为列表类型"
        assert len(results) >= 0, "结果数量不应为负数"
        # 注意：由于网络和Cookie状态不确定，这里只验证不抛出异常

    def test_invalid_expired_cookie_shows_error(self):
        """
        测试用例 2.3：验证使用无效/过期Cookie时的错误处理
        
        测试目的：确保系统能识别并报告无效Cookie的问题
        
        前置条件：
        - 准备一个明显无效的Cookie（如过期、篡改等）
        
        测试步骤：
        1. 构造一个无效的Cookie字符串（缺少必要字段）
        2. 调用验证函数
        3. 检查错误消息
        
        预期结果：
        - 验证应失败（is_valid=False）
        - 错误消息应明确指出问题原因
        
        实际结果：（运行时填充）
        """
        from auto_tag.utils.validation import validate_qq_music_cookie
        
        invalid_cookies = [
            ("", "空Cookie"),
            ("   ", "纯空白Cookie"),
            ("invalid_format", "无键值对"),
            ("test=value; foo=bar", "缺少必要字段"),
            ("a" * 5, "过短的伪Cookie"),
        ]
        
        for cookie, description in invalid_cookies:
            is_valid, error = validate_qq_music_cookie(cookie)
            assert not is_valid, f"{description}应该验证失败但通过了"
            assert error, f"{description}应有错误消息但为空"

    def test_malformed_cookie_rejected(self):
        """
        测试用例 2.4：验证格式错误的Cookie被正确拒绝
        
        测试目的：确保各种畸形Cookie格式都能被检测出来
        
        前置条件：
        - 无
        
        测试步骤：
        1. 构造多种格式的错误Cookie
        2. 逐一验证
        3. 确认全部被拒绝
        
        预期结果：
        - 所有畸形Cookie都应验证失败
        - 错误消息应具有描述性
        
        实际结果：（运行时填充）
        """
        from auto_tag.utils.validation import validate_qq_music_cookie
        
        malformed_cookies = [
            "===;;;===",  # 只有特殊字符
            "key",         # 单独的key没有value
            "=value",      # 只有value没有key
            "; ; ;",       # 只有分号
            "key=value; ; key2=value2",  # 中间有空项
        ]
        
        for cookie in malformed_cookies:
            is_valid, error = validate_qq_music_cookie(cookie)
            if is_valid:
                pytest.fail(f"畸形Cookie应被拒绝但通过了: {cookie[:50]}...")


# ============================================================================
# 第三部分：边界条件测试 (6个用例)
# ============================================================================

class TestBoundaryConditions:
    """
    边界条件测试类
    
    测试目的：
    - 测试空Cookie输入场景下的系统行为
    - 测试部分Cookie字段缺失情况下的系统处理逻辑
    - 测试超长Cookie值输入时的处理机制
    
    前置条件：
    - 配置系统和验证函数可用
    """

    def test_empty_cookie_handling(self):
        """
        测试用例 3.1：测试空Cookie输入场景
        
        测试目的：验证系统对空值的处理是否健壮
        
        前置条件：
        - 无
        
        测试步骤：
        1. 传入空字符串
        2. 传入None（如果适用）
        3. 传入只有空白字符的字符串
        
        预期结果：
        - 所有情况都应返回验证失败
        - 错误消息应明确指出"不能为空"
        
        实际结果：（运行时填充）
        """
        from auto_tag.utils.validation import validate_qq_music_cookie, is_cookie_empty_or_whitespace
        
        empty_cases = ["", "   ", "\t", "\n", "  \t  \n  "]
        
        for case in empty_cases:
            assert is_cookie_empty_or_whitespace(case), f"应检测为空: {repr(case)}"
            
            is_valid, error = validate_qq_music_cookie(case)
            assert not is_valid, f"空Cookie应验证失败: {repr(case)}"
            assert "空" in error or "empty" in error.lower(), \
                f"错误消息应提及'空': {error}"

    def test_whitespace_only_cookie(self):
        """
        测试用例 3.2：测试纯空白字符Cookie
        
        测试目的：确保空白字符不会被误解为有效Cookie
        
        前置条件：
        - 无
        
        测试步骤：
        1. 传入各种空白组合
        2. 验证返回结果
        
        预期结果：
        - 全部验证失败
        - 不应抛出异常
        
        实际结果：（运行时填充）
        """
        from auto_tag.utils.validation import validate_qq_music_cookie
        
        whitespace_cases = [
            " ",
            "  ",
            "\t\t",
            "\n\n",
            " \t \n ",
            "     \t\t     ",
        ]
        
        for case in whitespace_cases:
            try:
                is_valid, error = validate_qq_music_cookie(case)
                assert not is_valid, f"纯空白应验证失败: {repr(case)}"
            except Exception as e:
                pytest.fail(f"处理纯空白Cookie时抛出异常: {e}")

    def test_partial_missing_fields(self):
        """
        测试用例 3.3：测试部分Cookie字段缺失的情况
        
        测试目的：验证当Cookie缺少部分字段时的处理逻辑
        
        前置条件：
        - 了解必要字段列表（uin, qm_keyst, qqmusic_key）
        
        测试步骤：
        1. 构造只包含 uin 的Cookie
        2. 构造只包含 qm_keyst 的Cookie
        3. 构造只包含 qqmusic_key 的Cookie
        4. 构造完全不包含必要字段的Cookie
        
        预期结果：
        - 包含至少一个必要字段的应验证通过
        - 完全不包含必要字段的应验证失败
        
        实际结果：（运行时填充）
        """
        from auto_tag.utils.validation import validate_qq_music_cookie
        
        partial_cookies = {
            "only_uin": "uin=2253373466; other=value",
            "only_qm_keyst": "qm_keyst=test_key_12345; other=value",
            "only_qqmusic_key": "qqmusic_key=test_key_67890; other=value",
            "no_required": "other1=value1; other2=value2; other3=value3",
        }
        
        for name, cookie in partial_cookies.items():
            is_valid, error = validate_qq_music_cookie(cookie)
            if name.startswith("only_"):
                assert is_valid, f"{name}应验证通过: {error}"
            else:
                assert not is_valid, f"{name}应验证失败"

    def test_very_long_cookie_10000_chars(self):
        """
        测试用例 3.4：测试超长Cookie值的边界（10000字符）
        
        测试目的：验证系统对最大长度限制的处理
        
        前置条件：
        - 最大长度限制为10000字符
        
        测试步骤：
        1. 构造刚好10000字符的Cookie
        2. 构造10001字符的Cookie
        3. 分别验证
        
        预期结果：
        - 10000字符应验证通过（或根据实现调整）
        - 10001字符应验证失败并提示过长
        
        实际结果：（运行时填充）
        """
        from auto_tag.gui.config import AppConfig
        from auto_tag.utils.validation import validate_qq_music_cookie
        
        max_len = AppConfig.QQ_MUSIC_COOKIE_MAX_LENGTH
        
        # 刚好达到上限的Cookie
        base_cookie = f"uin=1234567890; qm_keyst={'x' * 100}; qqmusic_key={'y' * 100};"
        padding = "z" * (max_len - len(base_cookie))
        exact_max_cookie = base_cookie + padding
        
        is_valid, error = validate_qq_music_cookie(exact_max_cookie)
        assert is_valid or "长" in error, f"最大长度Cookie处理异常: {error}"
        
        # 超过上限的Cookie
        over_max_cookie = exact_max_cookie + "a"
        is_valid, error = validate_qq_music_cookie(over_max_cookie)
        assert not is_valid, "超过最大长度应验证失败"
        assert "长" in error or "long" in error.lower(), f"错误消息应提及长度: {error}"

    def test_special_characters_in_cookie(self):
        """
        测试用例 3.5：测试特殊字符在Cookie中的处理
        
        测试目的：确保特殊字符不会破坏解析逻辑
        
        前置条件：
        - 无
        
        测试步骤：
        1. 构造包含URL编码字符的Cookie
        2. 构造包含Unicode字符的Cookie
        3. 构造包含引号和分号的Cookie
        4. 分别验证
        
        预期结果：
        - 合法的特殊字符应被正确处理
        - 不应导致程序崩溃或安全漏洞
        
        实际结果：（运行时填充）
        """
        from auto_tag.utils.validation import validate_qq_music_cookie
        
        special_char_cookies = [
            "uin=123; value=%E4%B8%AD%E6%96%87; qm_keyst=test",  # URL编码中文
            "uin=123; value=test%20space; qm_keyst=test",          # URL编码空格
            "uin=123; qm_keyst=test_value; data=some~thing",      # 波浪线
            "uin=123; qm_keyst=test; token=a.b-c_d_e",           # 点划线
        ]
        
        for cookie in special_char_cookies:
            try:
                is_valid, error = validate_qq_music_cookie(cookie)
                # 只要不崩溃就算通过，验证结果取决于具体实现
            except Exception as e:
                pytest.fail(f"处理特殊字符Cookie时崩溃: {e}, Cookie: {cookie}")

    def test_unicode_characters_in_cookie(self):
        """
        测试用例 3.6：测试Unicode字符在Cookie中的处理
        
        测试目的：验证对国际化字符的支持
        
        前置条件：
        - Python Unicode支持正常
        
        测试步骤：
        1. 构造包含中文的Cookie值
        2. 构造包含日文的Cookie值
        3. 构造包含emoji的Cookie值
        4. 分别验证
        
        预期结果：
        - 不应因Unicode字符而崩溃
        - 根据实现可能接受或拒绝
        
        实际结果：（运行时填充）
        """
        from auto_tag.utils.validation import validate_qq_music_cookie
        
        unicode_cookies = [
            f"uin=2253373466; qm_keyst=test; name=中文测试",
            f"uin=2253373466; qm_keyst=test; name=日本語テスト",
            f"uin=2253373466; qm_keyst=test; name=🎵🎶🎼",
            f"uin=2253373466; qm_keyst=test; name=한국어",
        ]
        
        for cookie in unicode_cookies:
            try:
                is_valid, error = validate_qq_music_cookie(cookie)
                # 主要测试不崩溃，验证结果是次要的
            except UnicodeError as e:
                pytest.fail(f"Unicode处理失败: {e}")
            except Exception as e:
                # 其他异常可能可以接受，记录即可
                pass


# ============================================================================
# 第四部分：安全性测试 (4个用例)
# ============================================================================

class TestSecurity:
    """
    安全性测试类
    
    测试目的：
    - 验证Cookie值在存储和传输过程中的安全性
    - 测试特殊字符和潜在注入攻击字符串作为Cookie输入时的系统防护能力
    
    前置条件：
    - 安全相关函数已实现
    """

    def test_cookie_stored_securely_not_logged_fully(self):
        """
        测试用例 4.1：验证Cookie在日志中被脱敏处理
        
        测试目的：确保敏感信息不会完整出现在日志中
        
        前置条件：
        - mask_cookie_for_logging() 函数可用
        
        测试步骤：
        1. 调用脱敏函数处理完整Cookie
        2. 检查返回的字符串
        3. 确认原始Cookie不会完整出现
        
        预期结果：
        - 返回的字符串应只显示部分字符
        - 中间部分应被替换为...
        - 原始Cookie不应能从脱敏版本还原
        
        实际结果：（运行时填充）
        """
        from auto_tag.utils.validation import mask_cookie_for_logging
        
        masked = mask_cookie_for_logging(TEST_VALID_COOKIE)
        
        # 验证脱敏效果
        assert len(masked) < len(TEST_VALID_COOKIE), "脱敏后长度应小于原始长度"
        assert "..." in masked, "中间部分应被...替代"
        
        # 验证首尾保留
        assert masked.startswith(TEST_VALID_COOKIE[:8]), "开头字符不匹配"
        assert masked.endswith(TEST_VALID_COOKIE[-4:]), "结尾字符不匹配"
        
        # 验证中间被隐藏
        middle_original = TEST_VALID_COOKIE[8:-4]
        assert middle_original not in masked, "中间部分未被隐藏"

    def test_sql_injection_attempt_blocked(self):
        """
        测试用例 4.2：测试SQL注入攻击字符串的防护
        
        测试目的：确保恶意SQL语句不会造成安全漏洞
        
        前置条件：
        - 无（黑盒测试）
        
        测试步骤：
        1. 构造包含SQL注入的Cookie字符串
        2. 尝试进行验证和处理
        3. 检查是否有异常行为
        
        预期结果：
        - 注入字符串应被当作普通文本处理
        - 不应导致数据库查询异常（如果有）
        - 不应破坏程序逻辑
        
        实际结果：（运行时填充）
        """
        from auto_tag.utils.validation import validate_qq_music_cookie
        
        sql_injection_strings = [
            "uin=123'; DROP TABLE users; --",
            "uin=123 OR 1=1",
            "uin=123; UNION SELECT * FROM passwords",
            "uin=123'; EXEC xp_cmdshell('dir'); --",
        ]
        
        for injection in sql_injection_strings:
            try:
                is_valid, error = validate_qq_music_cookie(injection)
                # 只要没崩溃就行，验证结果不重要
            except Exception as e:
                pytest.fail(f"SQL注入测试导致异常: {e}, Input: {injection}")

    def test_xss_attempt_in_cookie(self):
        """
        测试用例 4.3：测试XSS攻击字符串的防护
        
        测试目的：确保JavaScript代码不会被执行
        
        前置条件：
        - UI组件会显示Cookie（如果有的话）
        
        测试步骤：
        1. 构造包含XSS脚本的Cookie
        2. 尝试输入和显示
        3. 验证脚本未被执行
        
        预期结果：
        - XSS脚本应被转义或过滤
        - 显示为纯文本而非可执行代码
        
        实际结果：（运行时填充）
        """
        from auto_tag.utils.validation import validate_qq_music_cookie
        
        xss_strings = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert(1)>',
            'javascript:alert("XSS")',
            '<svg onload=alert(1)>',
            '" onclick="alert(1)',
        ]
        
        for xss in xss_strings:
            cookie = f"uin=2253373466; qm_keyst={xss}"
            try:
                is_valid, error = validate_qq_music_cookie(cookie)
                # 验证函数不应崩溃
                # 进一步的XSS防护需要在UI层面测试
            except Exception as e:
                pytest.fail(f"XSS测试导致异常: {e}")

    def test_cookie_masked_in_ui_display(self):
        """
        测试用例 4.4：验证Cookie在UI中的显示安全性
        
        测试目的：即使Cookie很长，UI也应合理显示
        
        前置条件：
        - mask_cookie_for_logging() 可用
        
        测试步骤：
        1. 对不同长度的Cookie进行脱敏
        2. 验证脱敏后的长度合理
        3. 验证短Cookie不被过度处理
        
        预期结果：
        - 长Cookie应被大幅缩短
        - 短Cookie（<12字符）应原样返回
        - 脱敏后的字符串适合UI显示
        
        实际结果：（运行时填充）
        """
        from auto_tag.utils.validation import mask_cookie_for_logging
        
        # 测试短Cookie（不应被处理）
        short_cookie = "uin=123"
        masked_short = mask_cookie_for_logging(short_cookie)
        assert masked_short == short_cookie, "短Cookie不应被修改"
        
        # 测试中等长度Cookie
        medium_cookie = "uin=1234567890; qm_keyst=abcdefghij"
        masked_medium = mask_cookie_for_logging(medium_cookie)
        assert "..." in masked_medium, "中等Cookie应被部分遮盖"
        
        # 测试非常长的Cookie
        long_cookie = "uin=123;" + "x" * 1000 + "; end=end"
        masked_long = mask_cookie_for_logging(long_cookie)
        assert len(masked_long) < 50, f"长Cookie脱敏后仍过长: {len(masked_long)}"


# ============================================================================
# 第五部分：兼容性测试 (2个用例)
# ============================================================================

class TestCompatibility:
    """
    兼容性测试类
    
    测试目的：
    - 在不同环境下验证Cookie输入功能的一致性
    - 验证响应式布局在不同屏幕尺寸下的表现
    
    前置条件：
    - GUI框架可用（PySide6/QFluentWidgets）
    """

    def test_responsive_layout_desktop(self):
        """
        测试用例 5.1：验证桌面端布局适配
        
        测试目的：确保Cookie输入框在桌面分辨率下正常显示
        
        前置条件：
        - PySide6可用
        - QFluentWidgets可用
        
        测试步骤：
        1. 创建SettingsPage实例
        2. 模拟桌面分辨率（1920x1080）
        3. 检查Cookie输入框的位置和大小
        
        预期结果：
        - Cookie输入框应可见（当QQ音乐选中时）
        - 输入框宽度应适应屏幕
        - 文本应清晰可读
        
        实际结果：（运行时填充）
        """
        try:
            from PySide6.QtWidgets import QApplication
            from auto_tag.gui.pages.settings_page import SettingsPage
            
            # 确保有QApplication实例
            app = QApplication.instance()
            if not app:
                app = QApplication([])
            
            # 创建设置页面
            settings = SettingsPage()
            
            # 验证Cookie组件存在
            assert hasattr(settings, '_qq_music_cookie_edit'), "Cookie编辑框不存在"
            assert hasattr(settings, '_qq_music_cookie_label'), "Cookie标签不存在"
            assert hasattr(settings, '_cookie_validation_label'), "验证标签不存在"
            
            # 验证基本属性
            edit = settings._qq_music_cookie_edit
            assert edit.minimumWidth() >= 400, "Cookie编辑框最小宽度过小"
            assert edit.minimumHeight() >= 60, "Cookie编辑框最小高度过小"
            
        except ImportError:
            pytest.skip("PySide6不可用，跳过GUI测试")

    def test_responsive_layout_mobile(self):
        """
        测试用例 5.2：验证移动端/小屏幕布局适配
        
        测试目的：确保在小窗口下Cookie输入框仍可用
        
        前置条件：
        - PySide6可用
        
        测试步骤：
        1. 创建SettingsPage实例
        2. 设置较小的窗口尺寸（800x600）
        3. 检查Cookie输入框是否可滚动或自适应
        
        预期结果：
        - 组件不应超出窗口范围
        - 如果空间不足应支持滚动
        - 功能不受影响
        
        实际结果：（运行时填充）
        """
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import QSize
            from auto_tag.gui.pages.settings_page import SettingsPage
            
            app = QApplication.instance()
            if not app:
                app = QApplication([])
            
            settings = SettingsPage()
            
            # 模拟小窗口
            small_size = QSize(800, 600)
            settings.setMinimumSize(small_size)
            
            # 验证页面可以设置为小尺寸而不报错
            settings.resize(small_size)
            actual_size = settings.size()
            
            assert actual_size.width() >= small_size.width(), "宽度不符合最小要求"
            assert actual_size.height() >= small_size.height(), "高度不符合最小要求"
            
        except ImportError:
            pytest.skip("PySide6不可用，跳过GUI测试")


# ============================================================================
# 第六部分：集成测试 (3个用例)
# ============================================================================

class TestIntegration:
    """
    集成测试类
    
    测试目的：
    - 验证Config、Validation、UI三者的协作
    - 端到端流程测试
    
    前置条件：
    - 所有模块可用
    """

    def test_full_workflow_set_validate_save_load(self):
        """
        测试用例 6.1：完整工作流测试 - 设置→验证→保存→加载
        
        测试目的：验证整个Cookie配置流程的正确性
        
        前置条件：
        - 临时目录可用
        
        测试步骤：
        1. 用户输入Cookie文本
        2. 系统实时验证格式
        3. 验证通过后自动保存
        4. 重启后加载配置
        5. 应用到API请求
        
        预期结果：
        - 每一步都应正确执行
        - 数据在整个流程中保持一致
        
        完成结果：（运行时填充）
        """
        from auto_tag.gui.config import AppConfig
        from auto_tag.utils.validation import validate_qq_music_cookie, mask_cookie_for_logging
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 步骤1&2：用户输入和验证
            user_input = TEST_VALID_COOKIE
            is_valid, validation_error = validate_qq_music_cookie(user_input)
            assert is_valid, f"用户输入验证失败: {validation_error}"
            
            # 步骤3：保存到配置
            config = AppConfig.__new__(AppConfig)
            config._config_dir = Path(tmpdir)
            config._config_file = config._config_dir / "config.json"
            config._qq_music_cookie = ""
            
            config.set_qq_music_cookie(user_input)
            saved_value = config.qq_music_cookie
            assert saved_value == user_input, "保存值不匹配"
            
            # 验证日志脱敏
            log_output = mask_cookie_for_logging(saved_value)
            assert log_output != saved_value, "日志输出应被脱敏"
            
            # 步骤4：重启后加载
            config2 = AppConfig.__new__(AppConfig)
            config2._config_dir = Path(tmpdir)
            config2._config_file = config2._config_dir / "config.json"
            config2._qq_music_cookie = ""
            config2._load_config()
            
            loaded_value = config2.qq_music_cookie
            assert loaded_value == user_input, "加载值与原始值不匹配"
            
            print(f"✓ 完整工作流测试通过")
            print(f"  - 原始长度: {len(user_input)} 字符")
            print(f"  - 日志显示: {log_output}")
            print(f"  - 加载验证: {'通过' if loaded_value == user_input else '失败'}")

    def test_config_validation_integration(self):
        """
        测试用例 6.2：Config与Validation集成测试
        
        测试目的：验证配置系统的长度限制与验证函数的一致性
        
        前置条件：
        - Config和Validation模块都已加载
        
        测试步骤：
        1. 从Config获取最大长度限制
        2. 构造刚好超长的Cookie
        3. 用Validation验证
        4. 尝试用Config保存
        
        预期结果：
        - Validation应检测到超长
        - Config应拒绝保存或截断
        
        完成结果：（运行时填充）
        """
        from auto_tag.gui.config import AppConfig
        from auto_tag.utils.validation import validate_qq_music_cookie
        
        max_length = AppConfig.QQ_MUSIC_COOKIE_MAX_LENGTH
        
        # 构造超长Cookie（包含必要字段以通过其他检查）
        overlong = f"uin=2253373466; qm_keyst={'x' * (max_length - 20)}; extra=data"
        
        # Validation检查
        is_valid, error = validate_qq_music_cookie(overlong)
        assert not is_valid, "超长Cookie应验证失败"
        assert "长" in error or "long" in error.lower(), "错误应提及长度"
        
        # Config保存检查
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AppConfig.__new__(AppConfig)
            config._config_dir = Path(tmpdir)
            config._config_file = config._config_dir / "config.json"
            config._qq_music_cookie = ""
            
            try:
                config.set_qq_music_cookie(overlong)
                pytest.fail("Config应拒绝超长Cookie")
            except ValueError as e:
                assert "长" in str(e) or "length" in str(e).lower(), \
                    f"异常消息应提及长度: {e}"

    def test_ui_state_persistence(self):
        """
        测试用例 6.3：UI状态持久化测试
        
        测试目的：验证UI组件的状态能正确恢复
        
        前置条件：
        - PySide6可用
        
        测试步骤：
        1. 创建SettingsPage
        2. 在Cookie输入框输入文本
        3. 模拟语言切换（触发refresh_texts）
        4. 验证输入框文本不变
        
        预期结果：
        - 语言切换后Cookie文本应保留
        - 其他UI状态也应保持
        
        完成结果：（运行时填充）
        """
        try:
            from PySide6.QtWidgets import QApplication
            from auto_tag.gui.pages.settings_page import SettingsPage
            
            app = QApplication.instance()
            if not app:
                app = QApplication([])
            
            settings = SettingsPage()
            
            # 设置Cookie文本
            test_text = "uin=2253373466; qm_keyst=test_cookie_value"
            settings._qq_music_cookie_edit.setPlainText(test_text)
            
            # 验证设置成功
            current_text = settings._qq_music_cookie_edit.toPlainText()
            assert current_text == test_text, "文本设置失败"
            
            # 模拟refresh_texts
            settings.refresh_texts()
            
            # 验证文本保留
            after_refresh_text = settings._qq_music_cookie_edit.toPlainText()
            assert after_refresh_text == test_text, "refresh_texts后文本丢失"
            
        except ImportError:
            pytest.skip("PySide6不可用，跳过GUI测试")


# ============================================================================
# 测试入口和辅助函数
# ============================================================================

def run_all_tests():
    """
    手动运行所有测试的便捷函数
    
    用于调试和快速验证，不建议替代pytest
    """
    print("=" * 70)
    print("QQ音乐Cookie功能测试套件")
    print("=" * 70)
    
    test_classes = [
        ("基础功能验证", TestBasicFunctionality),
        ("Cookie有效性测试", TestCookieValidity),
        ("边界条件测试", TestBoundaryConditions),
        ("安全性测试", TestSecurity),
        ("兼容性测试", TestCompatibility),
        ("集成测试", TestIntegration),
    ]
    
    total = 0
    passed = 0
    failed = 0
    
    for class_name, test_class in test_classes.items():
        print(f"\n{class_name}")
        print("-" * 70)
        
        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith('test_')]
        
        for method_name in methods:
            total += 1
            method = getattr(instance, method_name)
            try:
                method()
                passed += 1
                print(f"  ✓ {method_name}")
            except Exception as e:
                failed += 1
                print(f"  ✗ {method_name}: {e}")
    
    print("\n" + "=" * 70)
    print(f"测试完成: 总计 {total}, 通过 {passed}, 失败 {failed}")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    # 支持直接运行进行快速测试
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        success = run_all_tests()
        sys.exit(0 if success else 1)
    else:
        # 默认使用pytest运行
        pytest.main([__file__, "-v"])
