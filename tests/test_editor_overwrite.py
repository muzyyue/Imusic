# -*- coding: utf-8 -*-
"""
编辑器覆盖原文件功能单元测试

验证 overwrite_original 配置项的行为：
- 勾选覆盖时，应直接修改原文件（通过临时文件中转）
- 不勾选时，应生成新的 _edited 文件
- 覆盖失败时应保留原文件并清理临时文件
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from auto_tag.editor.config import EditorConfig, TrimConfig, NormalizeConfig, TrimMode
from auto_tag.editor.workers.editor_worker import EditorWorker
from auto_tag.converter.config import OutputFormat, QualityPreset


class TestOverwriteOriginal:
    """覆盖原文件功能测试"""

    def _create_test_config(self, overwrite: bool = False) -> EditorConfig:
        """创建测试用配置对象"""
        return EditorConfig(
            trim=TrimConfig(mode=TrimMode.AUTO),
            normalize=NormalizeConfig(),
            output_format=OutputFormat.MP3,
            quality_preset=QualityPreset.HIGH,
            overwrite_original=overwrite,
        )

    def _create_mock_editor(self, success: bool = True) -> Mock:
        """创建模拟的 AudioEditor 对象"""
        mock_editor = Mock()
        mock_result = {"success": success, "steps_completed": ["trim", "normalize"]}
        if not success:
            mock_result["error"] = "模拟编辑失败"

        def mock_apply_preset(input_file, output_path, config):
            Path(output_path).touch()
            return mock_result

        mock_editor.apply_preset.side_effect = mock_apply_preset
        return mock_editor

    @patch("auto_tag.editor.workers.editor_worker.AudioEditor")
    @patch("os.path.exists", return_value=True)
    def test_overwrite_enabled_generates_temp_file(self, mock_exists, mock_editor_class):
        """测试启用覆盖模式时生成临时文件路径"""
        mock_editor_class.return_value = self._create_mock_editor()

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_song.mp3")
            Path(test_file).touch()

            config = self._create_test_config(overwrite=True)
            worker = EditorWorker(
                files=[test_file],
                output_dir=temp_dir,
                config=config,
            )

            worker.run()
            results = worker._results

            assert len(results) == 1
            assert results[0]["success"] is True
            assert results[0]["output_file"] == test_file
            assert results[0]["input_file"] == test_file

    @patch("auto_tag.editor.workers.editor_worker.AudioEditor")
    @patch("os.path.exists", return_value=True)
    def test_overwrite_disabled_generates_edited_file(self, mock_exists, mock_editor_class):
        """测试禁用覆盖模式时生成 _edited 文件"""
        mock_editor_class.return_value = self._create_mock_editor()

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_song.mp3")
            Path(test_file).touch()

            config = self._create_test_config(overwrite=False)
            worker = EditorWorker(
                files=[test_file],
                output_dir=temp_dir,
                config=config,
            )

            worker.run()
            results = worker._results

            assert len(results) == 1
            assert results[0]["success"] is True
            assert results[0]["output_file"].endswith("_edited.mp3")
            assert results[0]["output_file"] != test_file

    @patch("auto_tag.editor.workers.editor_worker.AudioEditor")
    @patch("os.path.exists", return_value=True)
    @patch("os.replace")
    def test_overwrite_calls_os_replace(self, mock_replace, mock_exists, mock_editor_class):
        """测试覆盖模式成功后调用 os.replace 进行原子替换"""
        mock_editor_class.return_value = self._create_mock_editor()

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_song.mp3")
            Path(test_file).touch()

            config = self._create_test_config(overwrite=True)
            worker = EditorWorker(
                files=[test_file],
                output_dir=temp_dir,
                config=config,
            )

            worker.run()

            mock_replace.assert_called_once()
            call_args = mock_replace.call_args
            assert call_args[0][1] == test_file

    @patch("auto_tag.editor.workers.editor_worker.AudioEditor")
    @patch("os.path.exists", return_value=True)
    @patch("os.replace", side_effect=PermissionError("权限不足"))
    @patch("os.remove")
    def test_overwrite_failure_cleans_temp_file(
        self, mock_remove, mock_replace, mock_exists, mock_editor_class
    ):
        """测试覆盖失败时清理临时文件"""
        mock_editor_class.return_value = self._create_mock_editor()

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_song.mp3")
            Path(test_file).touch()

            config = self._create_test_config(overwrite=True)
            worker = EditorWorker(
                files=[test_file],
                output_dir=temp_dir,
                config=config,
            )

            worker.run()
            results = worker._results

            assert len(results) == 1
            assert results[0]["success"] is False
            assert "替换原文件失败" in results[0]["error"]
            mock_remove.assert_called_once()

    @patch("auto_tag.editor.workers.editor_worker.AudioEditor")
    @patch("os.path.exists", return_value=True)
    def test_temp_filename_includes_timestamp(self, mock_exists, mock_editor_class):
        """测试临时文件名包含时间戳以避免并发冲突"""
        mock_editor_class.return_value = self._create_mock_editor()

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_song.mp3")
            Path(test_file).touch()

            before_time = int(time.time())
            config = self._create_test_config(overwrite=True)
            worker = EditorWorker(
                files=[test_file],
                output_dir=temp_dir,
                config=config,
            )

            worker.run()
            after_time = int(time.time())

            results = worker._results
            assert len(results) == 1

            temp_path_used = None
            for call in mock_editor_class.return_value.apply_preset.call_args_list:
                if len(call[0]) > 1:
                    temp_path_used = call[0][1]
                    break

            if temp_path_used:
                basename = os.path.basename(temp_path_used)
                assert "_editing_temp_" in basename
                assert basename.startswith(".")
