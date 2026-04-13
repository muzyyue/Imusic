# -*- coding: utf-8 -*-
"""
AudioConverter 使用示例

演示如何使用 AudioConverter 类进行音频格式转换。
"""

from auto_tag.converter import AudioConverter, ConverterConfig
from auto_tag.converter.config import OutputFormat, QualityPreset


def example_detect_format():
    """示例：检测文件格式"""
    converter = AudioConverter()
    
    # 检测单个文件的格式
    file_path = "song.mp3"
    format_name = converter.detect_format(file_path)
    
    if format_name:
        print(f"文件格式: {format_name}")
    else:
        print("无法检测文件格式")


def example_convert_single_file():
    """示例：转换单个文件"""
    converter = AudioConverter()
    
    # 创建配置
    config = ConverterConfig()
    config.set_output_format("flac", QualityPreset.LOSSLESS)
    
    # 定义进度回调函数
    def progress_callback(progress: float):
        print(f"转换进度: {progress * 100:.1f}%")
    
    # 转换文件
    input_path = "input.mp4"
    output_path = "output.flac"
    
    success = converter.convert_file(
        input_path,
        output_path,
        config,
        progress_callback=progress_callback
    )
    
    if success:
        print("转换成功！")
    else:
        print("转换失败")


def example_convert_batch():
    """示例：批量转换文件"""
    converter = AudioConverter()
    
    # 创建配置
    config = ConverterConfig()
    config.set_output_format("mp3", QualityPreset.HIGH)
    
    # 定义进度回调函数
    def batch_progress_callback(current: int, total: int, file_path: str):
        print(f"处理进度: {current}/{total} - {file_path}")
    
    # 批量转换
    files = ["song1.mp4", "song2.avi", "song3.mkv"]
    output_dir = "output/"
    
    results = converter.convert_batch(
        files,
        output_dir,
        config,
        progress_callback=batch_progress_callback
    )
    
    # 统计结果
    success_count = sum(1 for success in results.values() if success)
    print(f"转换完成: {success_count}/{len(files)} 成功")


def example_custom_config():
    """示例：自定义配置"""
    converter = AudioConverter()
    
    # 创建自定义配置
    config = ConverterConfig()
    config.set_output_format("aac", QualityPreset.HIGH)
    config.preserve_metadata = True
    config.overwrite_existing = False
    
    # 转换文件
    success = converter.convert_file(
        "input.wav",
        "output.m4a",
        config
    )
    
    print(f"转换结果: {'成功' if success else '失败'}")


if __name__ == "__main__":
    # 运行示例
    print("=== 示例 1: 检测文件格式 ===")
    # example_detect_format()
    
    print("\n=== 示例 2: 转换单个文件 ===")
    # example_convert_single_file()
    
    print("\n=== 示例 3: 批量转换文件 ===")
    # example_convert_batch()
    
    print("\n=== 示例 4: 自定义配置 ===")
    # example_custom_config()
    
    print("\n注意：请取消注释上面的示例函数调用来运行实际示例")
