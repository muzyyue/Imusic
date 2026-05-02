# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, '.')
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from auto_tag.editor.audio_editor import AudioEditor

test_file = r'F:\Code\Imusic\tests\fixtures\song\Grand Escape  [feat. Toko Miura] [From Weathering With You] [For Piano Solo] - daigoro789 - Weathering With You Piano Collections.mp3'
temp_input, cleanup = AudioEditor._create_safe_temp_link(test_file)

import ffmpeg, tempfile

results = []

# Test 1: 最小参数集
print('TEST 1: start_periods=1 only')
out1 = os.path.join(tempfile.gettempdir(), 't1.mp3')
try:
    s = ffmpeg.input(temp_input).audio.filter('silenceremove', start_periods=1).output(out1, t=5)
    AudioEditor._run_ffmpeg_safe(s)
    size = os.path.getsize(out1)
    print(f'SUCCESS: {size} bytes')
    results.append(('TEST 1', 'OK', f'{size} bytes'))
    os.unlink(out1)
except Exception as e:
    err = e.stderr.decode('utf-8', errors='ignore') if isinstance(e.stderr, bytes) else str(e.stderr)
    print(f'FAIL: {err[:500]}')
    results.append(('TEST 1', 'FAIL', err[:500]))

# Test 2: 带 threshold (dB后缀)
print('\nTEST 2: with dB suffix (start_threshold=-50dB)')
out2 = os.path.join(tempfile.gettempdir(), 't2.mp3')
try:
    s = ffmpeg.input(temp_input).audio.filter('silenceremove', start_periods=1, stop_duration=0.5, start_threshold='-50dB').output(out2, t=5)
    AudioEditor._run_ffmpeg_safe(s)
    size = os.path.getsize(out2)
    print(f'SUCCESS: {size} bytes')
    results.append(('TEST 2', 'OK', f'{size} bytes'))
    os.unlink(out2)
except Exception as e:
    err = e.stderr.decode('utf-8', errors='ignore') if isinstance(e.stderr, bytes) else str(e.stderr)
    print(f'FAIL: {err[:500]}')
    results.append(('TEST 2', 'FAIL', err[:500]))

# Test 3: 带 threshold (纯数字)
print('\nTEST 3: numeric threshold (start_threshold=-50)')
out3 = os.path.join(tempfile.gettempdir(), 't3.mp3')
try:
    s = ffmpeg.input(temp_input).audio.filter('silenceremove', start_periods=1, stop_duration=0.5, start_threshold=-50).output(out3, t=5)
    AudioEditor._run_ffmpeg_safe(s)
    size = os.path.getsize(out3)
    print(f'SUCCESS: {size} bytes')
    results.append(('TEST 3', 'OK', f'{size} bytes'))
    os.unlink(out3)
except Exception as e:
    err = e.stderr.decode('utf-8', errors='ignore') if isinstance(e.stderr, bytes) else str(e.stderr)
    print(f'FAIL: {err[:500]}')
    results.append(('TEST 3', 'FAIL', err[:500]))

# Test 4: 完整参数集 (当前代码用的)
print('\nTEST 4: full params (current code)')
out4 = os.path.join(tempfile.gettempdir(), 't4.mp3')
try:
    s = ffmpeg.input(temp_input).audio.filter('silenceremove',
        start_periods=1,
        start_duration=0.5,
        start_threshold='-50dB',
        stop_periods=1,
        stop_duration=0.5,
        stop_threshold='-50dB',
        min_silence_duration=1.0,
    ).output(out4, t=5)
    AudioEditor._run_ffmpeg_safe(s)
    size = os.path.getsize(out4)
    print(f'SUCCESS: {size} bytes')
    results.append(('TEST 4', 'OK', f'{size} bytes'))
    os.unlink(out4)
except Exception as e:
    err = e.stderr.decode('utf-8', errors='ignore') if isinstance(e.stderr, bytes) else str(e.stderr)
    print(f'FAIL: {err[:500]}')
    results.append(('TEST 4', 'FAIL', err[:500]))

cleanup()

# Save summary
with open(os.path.join(tempfile.gettempdir(), 'sr_diagnosis.txt'), 'w', encoding='utf-8') as f:
    for name, status, detail in results:
        f.write(f"{name}: {status}\n")
        if status == 'FAIL':
            f.write(f"  Error: {detail}\n")

print("\nDone!")
