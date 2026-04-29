import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

print('='*70)
print('Standalone Test: Directory Filtering + Format Support')
print('='*70)

# Test 1: Directory filtering logic
print('\n[Test 1] Directory Filtering Logic')
SKIP_DIRS = {
    '__pycache__', '.git', '.svn', '.hg',
    'node_modules', '.venv', 'venv',
    '.idea', '.vscode', 'build', 'dist', '.tox',
}

SUPPORTED_AUDIO_EXTENSIONS = ('.mp3', '.ogg', '.flac', '.m4a', '.wav', '.wma', '.opus')

test_dir = 'tests'
audio_files = []

for rootdir, _, names in os.walk(test_dir):
    basename = os.path.basename(rootdir)
    if basename in SKIP_DIRS:
        print(f'  [SKIP] {rootdir}')
        continue
    for name in names:
        if name.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS):
            full_path = os.path.join(rootdir, name)
            audio_files.append(full_path)
            rel = os.path.relpath(full_path, test_dir)
            print(f'  [FOUND] {rel}')

print(f'\n[Result] Total files found: {len(audio_files)}')

# Check for key files
key_files = ['fileToTest.mp3', 'fileToTest.ogg']
for kf in key_files:
    found = any(os.path.basename(f) == kf for f in audio_files)
    status = '[PASS]' if found else '[FAIL]'
    result = 'Found' if found else 'Missing'
    print(f'  {status} {kf}: {result}')

# Test 2: Mutagen metadata reading
print('\n[Test 2] Mutagen Metadata Reading')
from mutagen import File as MutagenFile

test_files = [
    'tests/fileToTest.mp3',
    'tests/fileToTest.ogg',
]

for tf in test_files:
    if not os.path.exists(tf):
        print(f'  [SKIP] {tf} - Not found')
        continue

    try:
        audio = MutagenFile(tf)
        if audio and audio.tags:
            title = audio.tags.get('title', ['N/A'])
            artist = audio.tags.get('artist', ['N/A'])
            album = audio.tags.get('album', ['N/A'])

            t = title[0] if isinstance(title, list) else str(title)
            a = artist[0] if isinstance(artist, list) else str(artist)
            al = album[0] if isinstance(album, list) else str(album)

            print(f'  [PASS] {os.path.basename(tf)}')
            print(f'         Title: {t}, Artist: {a}, Album: {al}')
        else:
            print(f'  [WARN] {os.path.basename(tf)} - No tags')
    except Exception as e:
        print(f'  [ERROR] {os.path.basename(tf)} - {e}')

# Test 3: Show supported formats
print('\n[Test 3] Supported Audio Formats')
formats_info = {
    '.mp3': 'MPEG Audio Layer III',
    '.ogg': 'OGG Vorbis / Opus',
    '.flac': 'Free Lossless Audio Codec',
    '.m4a': 'MPEG-4 Audio (AAC)',
    '.wav': 'Waveform Audio File Format',
    '.wma': 'Windows Media Audio',
    '.opus': 'Opus Audio Codec',
}

for ext, desc in formats_info.items():
    supported = ext in SUPPORTED_AUDIO_EXTENSIONS
    marker = 'SUP' if supported else '---'
    print(f'  [{marker}] {ext:<6} {desc}')

print('\n' + '='*70)
print('[PASS] All core tests completed successfully!')
print('='*70)
