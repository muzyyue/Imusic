# -*- coding: utf-8 -*-
"""
精确诊断：找出 silenceremove 哪个参数不被支持
"""

import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, '.')

from auto_tag.editor.audio_editor import AudioEditor


def diagnose_silenceremove():
    """诊断 silenceremove 参数兼容性"""
    
    test_file = r"F:\Code\Imusic\tests\fixtures\song\Grand Escape  [feat. Toko Miura] [From Weathering With You] [For Piano Solo] - daigoro789 - Weathering With You Piano Collections.mp3"
    
    print("=" * 80)
    print("[DIAGNOSE] silenceremove 参数诊断")
    print("=" * 80)
    
    # 创建临时输入
    temp_input, cleanup = AudioEditor._create_safe_temp_link(test_file)
    print(f"\n[1] 临时输入: {os.path.basename(temp_input)}")
    
    import ffmpeg
    import tempfile
    
    # 测试不同的 silenceremove 参数组合
    test_cases = [
        {
            "name": "完整参数 (当前代码)",
            "kwargs": {
                "start_periods": 1,
                "start_duration": 0.5,
                "start_threshold": "-50dB",
                "stop_periods": 1,
                "stop_duration": 0.5,
                "stop_threshold": "-50dB",
                "min_silence_duration": 1.0,
            }
        },
        {
            "name": "去掉 dB 后缀",
            "kwargs": {
                "start_periods": 1,
                "start_duration": 0.5,
                "start_threshold": -50,  # 纯数字
                "stop_periods": 1,
                "stop_duration": 0.5,
                "stop_threshold": -50,  # 纯数字
                "min_silence_duration": 1.0,
            }
        },
        {
            "name": "最小参数集",
            "kwargs": {
                "start_periods": 1,
                "stop_duration": 0.5,
            }
        },
        {
            "name": "只有 start_periods",
            "kwargs": {
                "start_periods": 1,
            }
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"[TEST {i}] {test['name']}")
        print(f"{'='*80}")
        
        out_path = os.path.join(tempfile.gettempdir(), f"diagnose_sr_{i}.mp3")
        
        try:
            input_stream = ffmpeg.input(temp_input)
            processed = input_stream.audio.filter("silenceremove", **test['kwargs'])
            output_stream = processed.output(out_path, t=10)  # 只处理前10秒加速测试
            
            # 编译命令看实际参数
            cmd = output_stream.compile()
            
            # 找到 filter_complex 参数
            filter_arg = ""
            for j, arg in enumerate(cmd):
                if 'silenceremove' in str(arg):
                    filter_arg = arg
                    break
            
            if filter_arg:
                print(f"滤镜参数: {filter_arg[:200]}...")
            
            AudioEditor._run_ffmpeg_safe(output_stream)
            
            if os.path.exists(out_path):
                size = os.path.getsize(out_path)
                print(f"✅ 成功! 输出大小: {size} bytes ({size/1024:.1f} KB)")
                os.unlink(out_path)
                
        except Exception as e:
            print(f"❌ 失败: {type(e).__name__}: {e}")
            if hasattr(e, 'stderr'):
                stderr_str = e.stderr.decode('utf-8', errors='ignore') if isinstance(e.stderr, bytes) else str(e.stderr)
                lines = [l.strip() for l in stderr_str.split('\n') if l.strip()]
                
                # 找关键错误行
                for line in lines:
                    if any(kw in line.lower() for kw in ['option not found', 'error', 'invalid']):
                        print(f"   关键错误: {line}")
                        break
    
    # 清理
    cleanup()
    print(f"\n{'='*80}")
    print("[DONE]")
    print(f"{'='*80}")


if __name__ == "__main__":
    diagnose_silenceremove()
