# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, '.')
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from auto_tag.editor.audio_editor import AudioEditor

test_file = r'F:\Code\Imusic\tests\fixtures\song\Grand Escape  [feat. Toko Miura] [From Weathering With You] [For Piano Solo] - daigoro789 - Weathering With You Piano Collections.mp3'
temp_input, cleanup = AudioEditor._create_safe_temp_link(test_file)

import ffmpeg, tempfile

def test_sr(name, **kwargs):
    out = os.path.join(tempfile.gettempdir(), f'sr_{name}.mp3')
    try:
        s = ffmpeg.input(temp_input).audio.filter('silenceremove', **kwargs).output(out, t=5)
        AudioEditor._run_ffmpeg_safe(s)
        size = os.path.getsize(out)
        print(f'  {name}: OK ({size} bytes)')
        os.unlink(out)
        return True
    except Exception as e:
        err = e.stderr.decode('utf-8', errors='ignore') if isinstance(e.stderr, bytes) else str(e.stderr)
        lines = [l.strip() for l in err.split('\n') if l.strip()]
        error_line = [l for l in lines if 'option not found' in l.lower() or 'error' in l.lower()]
        print(f'  {name}: FAIL - {(error_line[0] if error_line else err[:200])}')
        return False

print("逐步添加参数测试:\n")

# 基础成功配置
base = {"start_periods": 1}
test_sr("base", **base)

# 逐个添加参数
params_to_test = [
    ("+stop_duration", "stop_duration", 0.5),
    ("+start_threshold(dB)", "start_threshold", "-50dB"),
    ("+stop_threshold(dB)", "stop_threshold", "-50dB"),
    ("+start_duration", "start_duration", 0.5),
    ("+stop_periods", "stop_periods", 1),
    ("+min_silence_duration", "min_silence_duration", 1.0),
]

current = dict(base)
for name, key, value in params_to_test:
    current[key] = value
    test_sr(name, **current)

cleanup()
print("\nDone!")
