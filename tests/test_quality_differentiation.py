# -*- coding: utf-8 -*-
"""测试质量差异化是否生效"""
import os
import sys
import tempfile
from auto_tag.editor.audio_editor import AudioEditor
from auto_tag.editor.config import TrimConfig, TrimMode, OutputQuality

# 强制 UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8')

test_file = r'f:\Code\Imusic\tests\fixtures\song\Grand Escape  [feat. Toko Miura] [From Weathering With You] [For Piano Solo] - daigoro789 - Weathering With You Piano Collections.mp3'

if not os.path.exists(test_file):
    print(f'[ERROR] 测试文件不存在: {test_file}')
    exit(1)

print(f'[OK] 测试文件存在: {os.path.getsize(test_file) / 1024 / 1024:.2f} MB')
print()

editor = AudioEditor()
temp_dir = tempfile.gettempdir()

results = {}
for quality in [OutputQuality.HIGH, OutputQuality.STANDARD, OutputQuality.SMALL]:
    output_file = os.path.join(temp_dir, f'test_quality_{quality.value}.mp3')

    if os.path.exists(output_file):
        os.unlink(output_file)

    config = TrimConfig(mode=TrimMode.MANUAL, start_time=10.0, end_time=60.0)

    print(f'[TEST] {quality.display_name} (VBR q:{quality.get_vbr_quality()})...')
    result = editor.trim_audio(test_file, output_file, config, output_quality=quality)

    if result['success'] and os.path.exists(output_file):
        size_kb = os.path.getsize(output_file) / 1024
        results[quality.value] = size_kb
        print(f'       [SUCCESS] Output: {size_kb:.2f} KB ({size_kb/1024:.2f} MB)')
    else:
        error_msg = result.get('error', 'Unknown error')
        print(f'       [FAILED] {error_msg}')
    print()

print('=' * 60)
print('[RESULT] Quality Mode Comparison:')
print('-' * 60)
for mode, size in results.items():
    print(f'  {mode:10s}: {size:8.2f} KB ({size/1024:.2f} MB)')
print('-' * 60)

if len(results) == 3:
    sizes = list(results.values())
    if abs(sizes[0] - sizes[1]) > 1 or abs(sizes[1] - sizes[2]) > 1:
        print('[PASS] Quality differentiation WORKS! Different sizes.')
    else:
        print('[WARN] Quality differentiation NOT working! Same sizes.')
