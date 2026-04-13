# -*- coding: utf-8 -*-
"""
ConverterWorker 单元测试

测试音频转换工作线程的功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import QThread

from auto_tag.converter.workers.converter_worker import ConverterWorker
from auto_tag.converter.config import ConverterConfig, OutputFormat


class TestConverterWorker:
    """ConverterWorker 测试类"""

    def test_init(self):
        """测试初始化"""
        files = ["/path/to/file1.mp4", "/path/to/file2.avi"]
        output_dir = "/path/to/output"
        config = ConverterConfig()

        worker = ConverterWorker(files, output_dir, config)

        assert worker._files == files
        assert worker._output_dir == output_dir
        assert worker._config == config
        assert worker._is_stopped is False
        assert worker._converter is None

    def test_stop(self):
        """测试停止方法"""
        files = ["/path/to/file1.mp4"]
        output_dir = "/path/to/output"
        config = ConverterConfig()

        worker = ConverterWorker(files, output_dir, config)
        assert worker._is_stopped is False

        worker.stop()
        assert worker._is_stopped is True

    @patch('auto_tag.converter.workers.converter_worker.AudioConverter')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_run_with_empty_files(self, mock_makedirs, mock_exists, mock_converter_class):
        """测试空文件列表"""
        files = []
        output_dir = "/path/to/output"
        config = ConverterConfig()

        worker = ConverterWorker(files, output_dir, config)

        # 连接信号槽
        error_occurred = Mock()
        worker.error_occurred.connect(error_occurred)

        # 运行
        worker.run()

        # 验证错误信号被发射
        error_occurred.assert_called_once_with("文件列表为空")

    @patch('auto_tag.converter.workers.converter_worker.AudioConverter')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_run_creates_output_dir(self, mock_makedirs, mock_exists, mock_converter_class):
        """测试创建输出目录"""
        files = ["/path/to/file1.mp4"]
        output_dir = "/path/to/output"
        config = ConverterConfig()

        # 模拟输出目录不存在
        mock_exists.side_effect = lambda path: False if path == output_dir else True

        worker = ConverterWorker(files, output_dir, config)

        # 连接信号槽
        finished_all = Mock()
        worker.finished_all.connect(finished_all)

        # 运行
        worker.run()

        # 验证目录创建被调用
        mock_makedirs.assert_called_once_with(output_dir, exist_ok=True)

    @patch('auto_tag.converter.workers.converter_worker.AudioConverter')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_run_with_converter_init_error(self, mock_makedirs, mock_exists, mock_converter_class):
        """测试转换器初始化失败"""
        files = ["/path/to/file1.mp4"]
        output_dir = "/path/to/output"
        config = ConverterConfig()

        # 模拟输出目录存在
        mock_exists.return_value = True

        # 模拟 AudioConverter 初始化失败
        mock_converter_class.side_effect = RuntimeError("FFmpeg 未安装")

        worker = ConverterWorker(files, output_dir, config)

        # 连接信号槽
        error_occurred = Mock()
        worker.error_occurred.connect(error_occurred)

        # 运行
        worker.run()

        # 验证错误信号被发射
        assert error_occurred.called
        call_args = error_occurred.call_args[0][0]
        assert "初始化音频转换器失败" in call_args

    @patch('auto_tag.converter.workers.converter_worker.os.makedirs')
    def test_convert_files_with_nonexistent_file(self, mock_makedirs):
        """测试转换不存在的文件"""
        files = ["/path/to/nonexistent.mp4"]
        output_dir = "/path/to/output"
        config = ConverterConfig()

        worker = ConverterWorker(files, output_dir, config)

        # 连接信号槽
        file_converted = Mock()
        worker.file_converted.connect(file_converted)

        # 运行转换
        results = worker._convert_files()

        # 验证结果
        assert len(results) == 1
        assert results[0]["success"] is False
        assert "文件不存在" in results[0]["error"]

        # 验证信号被发射
        file_converted.assert_called_once()

    @patch('auto_tag.converter.workers.converter_worker.os.makedirs')
    @patch('auto_tag.converter.workers.converter_worker.os.path.exists')
    def test_convert_files_with_stop_flag(self, mock_exists, mock_makedirs):
        """测试停止标志"""
        files = ["/path/to/file1.mp4", "/path/to/file2.mp4"]
        output_dir = "/path/to/output"
        config = ConverterConfig()

        # 模拟文件存在
        mock_exists.return_value = True

        worker = ConverterWorker(files, output_dir, config)

        # 设置停止标志
        worker._is_stopped = True

        # 运行转换
        results = worker._convert_files()

        # 验证结果为空（因为提前退出）
        assert len(results) == 0

    @patch('auto_tag.converter.workers.converter_worker.AudioConverter')
    @patch('auto_tag.converter.workers.converter_worker.os.makedirs')
    @patch('auto_tag.converter.workers.converter_worker.os.path.exists')
    def test_convert_files_success(self, mock_exists, mock_makedirs, mock_converter_class):
        """测试成功转换文件"""
        files = ["/path/to/file1.mp4"]
        output_dir = "/path/to/output"
        config = ConverterConfig()
        config.set_output_format("mp3")

        # 模拟文件存在
        mock_exists.return_value = True

        # 模拟 AudioConverter
        mock_converter = Mock()
        mock_converter.convert_file.return_value = True
        mock_converter_class.return_value = mock_converter

        worker = ConverterWorker(files, output_dir, config)
        
        # 初始化 converter
        worker._converter = mock_converter

        # 连接信号槽
        progress_updated = Mock()
        file_converted = Mock()
        worker.progress_updated.connect(progress_updated)
        worker.file_converted.connect(file_converted)

        # 运行转换
        results = worker._convert_files()

        # 验证结果
        assert len(results) == 1
        assert results[0]["success"] is True
        assert results[0]["error"] is None

        # 验证信号被发射
        progress_updated.assert_called_once()
        file_converted.assert_called_once()

        # 验证 convert_file 被调用
        mock_converter.convert_file.assert_called_once()

    @patch('auto_tag.converter.workers.converter_worker.AudioConverter')
    @patch('auto_tag.converter.workers.converter_worker.os.makedirs')
    @patch('auto_tag.converter.workers.converter_worker.os.path.exists')
    def test_convert_files_failure(self, mock_exists, mock_makedirs, mock_converter_class):
        """测试转换失败"""
        files = ["/path/to/file1.mp4"]
        output_dir = "/path/to/output"
        config = ConverterConfig()

        # 模拟文件存在
        mock_exists.return_value = True

        # 模拟 AudioConverter 转换失败
        mock_converter = Mock()
        mock_converter.convert_file.return_value = False
        mock_converter_class.return_value = mock_converter

        worker = ConverterWorker(files, output_dir, config)
        
        # 初始化 converter
        worker._converter = mock_converter

        # 连接信号槽
        file_converted = Mock()
        worker.file_converted.connect(file_converted)

        # 运行转换
        results = worker._convert_files()

        # 验证结果
        assert len(results) == 1
        assert results[0]["success"] is False
        assert "转换失败" in results[0]["error"]

        # 验证信号被发射
        file_converted.assert_called_once()

    @patch('auto_tag.converter.workers.converter_worker.AudioConverter')
    @patch('auto_tag.converter.workers.converter_worker.os.makedirs')
    @patch('auto_tag.converter.workers.converter_worker.os.path.exists')
    def test_convert_files_with_exception(self, mock_exists, mock_makedirs, mock_converter_class):
        """测试转换时发生异常"""
        files = ["/path/to/file1.mp4"]
        output_dir = "/path/to/output"
        config = ConverterConfig()

        # 模拟文件存在
        mock_exists.return_value = True

        # 模拟 AudioConverter 抛出异常
        mock_converter = Mock()
        mock_converter.convert_file.side_effect = Exception("转换错误")
        mock_converter_class.return_value = mock_converter

        worker = ConverterWorker(files, output_dir, config)
        
        # 初始化 converter
        worker._converter = mock_converter

        # 连接信号槽
        file_converted = Mock()
        worker.file_converted.connect(file_converted)

        # 运行转换
        results = worker._convert_files()

        # 验证结果
        assert len(results) == 1
        assert results[0]["success"] is False
        assert "转换错误" in results[0]["error"]

        # 验证信号被发射
        file_converted.assert_called_once()

    @patch('auto_tag.converter.workers.converter_worker.AudioConverter')
    @patch('auto_tag.converter.workers.converter_worker.os.makedirs')
    @patch('auto_tag.converter.workers.converter_worker.os.path.exists')
    def test_convert_multiple_files(self, mock_exists, mock_makedirs, mock_converter_class):
        """测试批量转换多个文件"""
        files = [
            "/path/to/file1.mp4",
            "/path/to/file2.avi",
            "/path/to/file3.mkv"
        ]
        output_dir = "/path/to/output"
        config = ConverterConfig()

        # 模拟文件存在
        mock_exists.return_value = True

        # 模拟 AudioConverter
        mock_converter = Mock()
        mock_converter.convert_file.return_value = True
        mock_converter_class.return_value = mock_converter

        worker = ConverterWorker(files, output_dir, config)
        
        # 初始化 converter
        worker._converter = mock_converter

        # 连接信号槽
        progress_updated = Mock()
        file_converted = Mock()
        worker.progress_updated.connect(progress_updated)
        worker.file_converted.connect(file_converted)

        # 运行转换
        results = worker._convert_files()

        # 验证结果
        assert len(results) == 3
        assert all(r["success"] for r in results)

        # 验证信号被发射的次数
        assert progress_updated.call_count == 3
        assert file_converted.call_count == 3

        # 验证 convert_file 被调用 3 次
        assert mock_converter.convert_file.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
