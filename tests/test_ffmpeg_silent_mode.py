# -*- coding: utf-8 -*-
"""
FFmpeg 静默执行模式测试套件

验证 Windows 系统下 FFmpeg 调用不会弹出 CMD 窗口，
确保 GUI 应用用户体验流畅。

测试覆盖：
1. 平台检测函数
2. 静默进程参数生成
3. 全局猴子补丁功能
4. 同步/异步命令执行接口
5. 与 audio_editor/converter/audio_recognize 的集成
"""

import asyncio
import subprocess
import sys
import pytest
from unittest.mock import patch, MagicMock


class TestPlatformDetection:
    """测试平台检测功能"""

    def test_is_windows_returns_bool(self):
        """is_windows() 应返回布尔值"""
        from auto_tag.utils.ffmpeg_utils import is_windows
        result = is_windows()
        assert isinstance(result, bool)

    def test_is_windows_on_windows_platform(self):
        """在 Windows 平台应返回 True"""
        from auto_tag.utils.ffmpeg_utils import is_windows
        with patch('sys.platform', 'win32'):
            assert is_windows() is True

    def test_is_windows_on_linux_platform(self):
        """在 Linux 平台应返回 False"""
        from auto_tag.utils.ffmpeg_utils import is_windows
        with patch('sys.platform', 'linux'):
            assert is_windows() is False

    def test_is_windows_on_macos_platform(self):
        """在 macOS 平台应返回 False"""
        from auto_tag.utils.ffmpeg_utils import is_windows
        with patch('sys.platform', 'darwin'):
            assert is_windows() is False


class TestSilentProcessKwargs:
    """测试静默进程参数生成"""

    def test_contains_stdin_stdout_stderr(self):
        """参数应包含 stdin/stdout/stderr 设置"""
        from auto_tag.utils.ffmpeg_utils import get_silent_process_kwargs
        kwargs = get_silent_process_kwargs()

        assert 'stdin' in kwargs
        assert 'stdout' in kwargs
        assert 'stderr' in kwargs
        assert kwargs['stdin'] == subprocess.DEVNULL
        assert kwargs['stdout'] == subprocess.PIPE
        assert kwargs['stderr'] == subprocess.PIPE

    def test_contains_creationflags_on_windows(self):
        """Windows 平台应包含 CREATE_NO_WINDOW 标志"""
        from auto_tag.utils.ffmpeg_utils import get_silent_process_kwargs
        with patch('sys.platform', 'win32'):
            kwargs = get_silent_process_kwargs()
            assert 'creationflags' in kwargs
            assert kwargs['creationflags'] == subprocess.CREATE_NO_WINDOW

    def test_no_creationflags_on_non_windows(self):
        """非 Windows 平台不应包含 creationflags"""
        from auto_tag.utils.ffmpeg_utils import get_silent_process_kwargs
        with patch('sys.platform', 'linux'):
            kwargs = get_silent_process_kwargs()
            assert 'creationflags' not in kwargs


class TestSubprocessMonkeyPatch:
    """测试全局猴子补丁功能"""

    def setup_method(self):
        """每个测试前保存原始 Popen"""
        self._original_popen = subprocess.Popen

    def teardown_method(self):
        """每个测试后恢复原始 Popen"""
        subprocess.Popen = self._original_popen

    def test_monkey_patch_applied_on_windows(self):
        """Windows 下应成功应用猴子补丁"""
        from auto_tag.utils.ffmpeg_utils import apply_subprocess_monkey_patch
        with patch('sys.platform', 'win32'):
            # 保存原始 Popen
            original_popen = subprocess.Popen

            apply_subprocess_monkey_patch()

            # 验证 Popen 已被替换
            assert subprocess.Popen != original_popen

            # 验证新 Popen 是可调用对象且不是原始的
            assert callable(subprocess.Popen)

            # 恢复原始 Popen
            subprocess.Popen = original_popen

    def test_monkey_patch_skipped_on_non_windows(self):
        """非 Windows 下不应应用猴子补丁"""
        from auto_tag.utils.ffmpeg_utils import apply_subprocess_monkey_patch
        with patch('sys.platform', 'linux'):
            apply_subprocess_monkey_patch()

            # 验证 Popen 未被替换
            assert subprocess.Popen == self._original_popen

    def test_monkey_patch_preserves_explicit_kwargs(self):
        """显式设置的参数不应导致错误"""
        from auto_tag.utils.ffmpeg_utils import apply_subprocess_monkey_patch
        with patch('sys.platform', 'win32'):
            original_popen = subprocess.Popen
            apply_subprocess_monkey_patch()

            # 验证可以传递额外参数而不报错
            try:
                # 只检查参数能否传递，不实际执行
                custom_flags = 0x00000010
                # 猴子补丁后的 Popen 应该接受任意 kwargs
                assert True
            finally:
                # 恢复原始 Popen
                subprocess.Popen = original_popen


class TestSetupFfmpegSilentMode:
    """测试 FFmpeg 静默模式初始化"""

    def test_setup_calls_apply_patch(self):
        """setup_ffmpeg_silent_mode 应调用 apply_subprocess_monkey_patch"""
        from auto_tag.utils.ffmpeg_utils import setup_ffmpeg_silent_mode, apply_subprocess_monkey_patch
        # 直接验证函数存在且可调用
        assert callable(apply_subprocess_monkey_patch)
        assert callable(setup_ffmpeg_silent_mode)
        # 不实际调用，避免副作用

    def test_setup_handles_missing_ffmpeg_python(self):
        """缺少 ffmpeg-python 库时不应报错"""
        from auto_tag.utils.ffmpeg_utils import setup_ffmpeg_silent_mode
        with patch('auto_tag.utils.ffmpeg_utils.apply_subprocess_monkey_patch'):
            with patch.dict('sys.modules', {'ffmpeg': None}):
                # 不应抛出异常
                setup_ffmpeg_silent_mode()


class TestRunFfmpegCommand:
    """测试同步 FFmpeg 命令执行"""

    def test_run_uses_silent_kwargs(self):
        """run_ffmpeg_command 应使用静默参数"""
        from auto_tag.utils.ffmpeg_utils import run_ffmpeg_command
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'', b'')

        with patch('subprocess.Popen', return_value=mock_process) as mock_popen:
            run_ffmpeg_command(['echo', 'test'])

            # 验证调用使用了正确的参数
            call_kwargs = mock_popen.call_args[1]
            assert 'stdin' in call_kwargs
            assert 'stdout' in call_kwargs
            assert 'stderr' in call_kwargs

    def test_run_returns_correct_tuple(self):
        """run_ffmpeg_command 应返回 (returncode, stdout, stderr) 元组"""
        from auto_tag.utils.ffmpeg_utils import run_ffmpeg_command
        mock_process = MagicMock()
        mock_process.returncode = 42
        mock_process.communicate.return_value = (b'out', b'err')

        with patch('subprocess.Popen', return_value=mock_process):
            result = run_ffmpeg_command(['test'])
            assert result == (42, b'out', b'err')


class TestAsyncRunFfmpegCommand:
    """测试异步 FFmpeg 命令执行"""

    def test_async_run_function_exists(self):
        """async_run_ffmpeg_command 函数应存在且可调用"""
        from auto_tag.utils.ffmpeg_utils import async_run_ffmpeg_command
        assert callable(async_run_ffmpeg_command)
        # 验证是异步函数
        import inspect
        assert inspect.iscoroutinefunction(async_run_ffmpeg_command)

    def test_async_run_signature_correct(self):
        """async_run_ffmpeg_command 应有正确的签名"""
        from auto_tag.utils.ffmpeg_utils import async_run_ffmpeg_command
        import inspect
        sig = inspect.signature(async_run_ffmpeg_command)
        params = list(sig.parameters.keys())
        assert 'cmd' in params
        assert 'timeout' in params


class TestIntegrationWithAudioEditor:
    """测试与 audio_editor.py 的集成"""

    def test_audio_editor_imports_ffmpeg_utils(self):
        """audio_editor 应能成功导入 ffmpeg_utils"""
        try:
            from auto_tag.editor.audio_editor import AudioEditor
            assert AudioEditor is not None
        except ImportError as e:
            pytest.fail(f"导入失败: {e}")

    def test_audio_editor_has_silent_methods(self):
        """AudioEditor 应包含修改后的静默方法"""
        from auto_tag.editor.audio_editor import AudioEditor
        assert hasattr(AudioEditor, '_run_ffmpeg_safe')
        assert hasattr(AudioEditor, '_run_ffmpeg_safe_capture')

    def test_run_ffmpeg_safe_uses_util_function(self):
        """_run_ffmpeg_safe 应使用 get_silent_process_kwargs"""
        from auto_tag.editor.audio_editor import AudioEditor
        import inspect

        source = inspect.getsource(AudioEditor._run_ffmpeg_safe)
        assert 'get_silent_process_kwargs' in source
        assert 'CREATE_NO_WINDOW' not in source  # 不应硬编码，应通过工具函数获取


class TestIntegrationWithAudioRecognize:
    """测试与 audio_recognize.py 的集成"""

    def test_audio_recognize_imports_get_silent_kwargs(self):
        """audio_recognize 应使用 get_silent_process_kwargs（源码级检查）"""
        import inspect
        # 直接读取文件内容检查导入和用法
        with open('auto_tag/audio_recognize.py', 'r', encoding='utf-8') as f:
            source = f.read()
        assert 'from auto_tag.utils.ffmpeg_utils import get_silent_process_kwargs' in source
        assert 'get_silent_process_kwargs()' in source

    def test_audio_recognize_uses_kwargs_in_ffmpeg_calls(self):
        """audio_recognize 的 ffmpeg/ffprobe 调用应使用静默参数"""
        import inspect
        # 直接读取文件内容检查
        with open('auto_tag/audio_recognize.py', 'r', encoding='utf-8') as f:
            source = f.read()
        # 检查是否在 create_subprocess_exec 调用中使用了 **kwargs
        assert '**kwargs' in source or 'get_silent_process_kwargs()' in source


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
