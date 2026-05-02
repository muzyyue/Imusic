# -*- coding: utf-8 -*-
"""
真实文件测试：验证特殊字符文件名的自动静音去除功能

测试目标：
1. 文件名包含 [] 等特殊字符时能否正常处理
2. AUTO 模式（silenceremove）能否正确检测并去除末尾静音
3. 处理后的音频时长是否合理
"""

import os
import sys
import tempfile
from pathlib import Path

# 设置 stdout 编码为 UTF-8（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from auto_tag.editor.audio_editor import AudioEditor
from auto_tag.editor.config import TrimConfig, TrimMode


def test_special_char_filename_auto_trim():
    """测试特殊字符文件名的自动静音去除"""
    
    # 测试文件路径（包含特殊字符：[] () - 空格）
    test_file = Path(__file__).parent / "fixtures" / "song" / "Grand Escape  [feat. Toko Miura] [From Weathering With You] [For Piano Solo] - daigoro789 - Weathering With You Piano Collections.mp3"
    
    print("=" * 80)
    print("[TEST] 特殊字符文件名自动静音去除测试")
    print("=" * 80)
    
    # 1. 验证文件存在
    if not test_file.exists():
        print(f"[FAIL] 测试文件不存在: {test_file}")
        return False
    
    print(f"\n[OK] 测试文件已找到")
    print(f"     路径: {test_file}")
    print(f"     大小: {test_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    try:
        # 2. 初始化编辑器
        print("\n[INIT] 初始化 AudioEditor...")
        editor = AudioEditor()
        print("      OK - FFmpeg 可用")
        
        # 3. 获取原始音频信息
        print("\n[INFO] 获取原始音频信息...")
        original_info = editor.get_audio_info(str(test_file))
        
        if not original_info.get("success"):
            print(f"[FAIL] 无法读取音频信息: {original_info.get('error')}")
            return False
        
        original_duration = original_info.get("duration", 0)
        print(f"      原始时长: {original_duration:.2f} 秒 ({original_duration/60:.2f} 分钟)")
        print(f"      采样率: {original_info.get('sample_rate', 'N/A')} Hz")
        print(f"      声道数: {original_info.get('channels', 'N/A')}")
        
        # 4. 配置 AUTO 模式（自动静音检测）
        config = TrimConfig(
            mode=TrimMode.AUTO,
            silence_threshold=-50,      # -50dB 作为静音阈值（较敏感）
            min_silence_duration=1.0,    # 最少持续 1 秒才认为是静音
        )
        
        print("\n[CONFIG] 配置 AUTO 模式参数:")
        print(f"         模式: 自动静音检测 (silenceremove)")
        print(f"         静音阈值: {config.silence_threshold} dB")
        print(f"         最小静音时长: {config.min_silence_duration} 秒")
        
        # 5. 创建临时输出文件
        with tempfile.NamedTemporaryFile(suffix='_trimmed.mp3', delete=False) as tmp:
            output_path = tmp.name
        
        print(f"\n[PROCESS] 开始处理...")
        print(f"          输入: {test_file.name[:60]}...")
        print(f"          输出: {Path(output_path).name}")
        
        # 6. 执行自动裁剪
        result = editor.trim_audio(
            input_path=str(test_file),
            output_path=output_path,
            config=config,
        )
        
        # 7. 分析结果
        print("\n" + "=" * 80)
        print("[RESULT] 处理结果:")
        print("=" * 80)
        
        if result.get("success"):
            new_duration = result.get("duration", 0)
            time_saved = original_duration - new_duration
            
            print(f"   [SUCCESS] 处理成功!")
            print(f"   原始时长: {original_duration:.2f} 秒")
            print(f"   处理后:   {new_duration:.2f} 秒")
            print(f"   减少时间: {time_saved:.2f} 秒 ({time_saved/original_duration*100:.1f}%)")
            
            if time_saved > 0:
                print(f"   [GOOD] 成功去除末尾静音部分！")
            else:
                print(f"   [INFO] 未检测到需要去除的静音（可能原文件无尾部静音）")
            
            # 验证输出文件存在且大小合理
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024 / 1024
                input_size = test_file.stat().st_size / 1024 / 1024
                print(f"\n   文件大小对比:")
                print(f"   输入: {input_size:.2f} MB")
                print(f"   输出: {output_size:.2f} MB")
                print(f"   压缩: {(1-output_size/input_size)*100:.1f}%")
                
                # 清理临时文件
                os.unlink(output_path)
                print(f"\n[CLEANUP] 临时文件已清理")
            
            return True
            
        else:
            error_msg = result.get("error", "未知错误")
            print(f"   [FAIL] 处理失败: {error_msg}")
            
            # 如果输出文件被创建了，显示它的大小以便调试
            if os.path.exists(output_path):
                print(f"   [DEBUG] 输出文件大小: {os.path.getsize(output_path)} bytes")
                os.unlink(output_path)
            
            return False
    
    except Exception as e:
        print(f"\n[ERROR] 异常发生: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("\n" + "=" * 80)
        print("[DONE] 测试完成")
        print("=" * 80)


if __name__ == "__main__":
    success = test_special_char_filename_auto_trim()
    sys.exit(0 if success else 1)
