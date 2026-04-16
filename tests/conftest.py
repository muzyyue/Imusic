# -*- coding: utf-8 -*-
"""
测试配置模块

定义测试所需的fixtures和辅助函数

@module conftest
@author Backend Architect
@version 1.0.0
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(scope="session")
def test_data_dir():
    """
    测试数据目录fixture

    Returns:
        Path: 测试数据目录路径
    """
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def audio_dir(test_data_dir):
    """
    音频文件目录fixture

    Args:
        test_data_dir: 测试数据目录

    Returns:
        Path: 音频文件目录路径
    """
    return test_data_dir / "audio"


@pytest.fixture(scope="session")
def lyrics_dir(test_data_dir):
    """
    歌词文件目录fixture

    Args:
        test_data_dir: 测试数据目录

    Returns:
        Path: 歌词文件目录路径
    """
    return test_data_dir / "lyrics"


@pytest.fixture(scope="session")
def mock_responses_dir(test_data_dir):
    """
    Mock响应数据目录fixture

    Args:
        test_data_dir: 测试数据目录

    Returns:
        Path: Mock响应数据目录路径
    """
    return test_data_dir / "mock_responses"


@pytest.fixture(scope="session")
def sample_audio_file(audio_dir):
    """
    样本音频文件fixture

    Args:
        audio_dir: 音频文件目录

    Returns:
        Path: 样本音频文件路径，如果文件不存在则跳过测试
    """
    audio_file = audio_dir / "ghost_in_a_flower.mp3"
    if not audio_file.exists():
        pytest.skip("样本音频文件不存在，请先准备测试数据: ghost_in_a_flower.mp3")
    return audio_file


@pytest.fixture(scope="session")
def expected_lrc_lyrics(lyrics_dir):
    """
    预期LRC歌词fixture

    Args:
        lyrics_dir: 歌词文件目录

    Returns:
        str: 预期LRC歌词内容
    """
    lrc_file = lyrics_dir / "expected_lrc.lrc"
    if not lrc_file.exists():
        pytest.skip("预期LRC歌词文件不存在")
    return lrc_file.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def expected_ttml_lyrics(lyrics_dir):
    """
    预期TTML歌词fixture

    Args:
        lyrics_dir: 歌词文件目录

    Returns:
        str: 预期TTML歌词内容
    """
    ttml_file = lyrics_dir / "expected_ttml.ttml"
    if not ttml_file.exists():
        pytest.skip("预期TTML歌词文件不存在")
    return ttml_file.read_text(encoding="utf-8")


@pytest.fixture
def mock_lrclib_success_response(mock_responses_dir):
    """
    Mock LRCLib成功响应fixture

    Args:
        mock_responses_dir: Mock响应数据目录

    Returns:
        dict: Mock LRCLib成功响应数据
    """
    response_file = mock_responses_dir / "lrclib_success.json"
    if response_file.exists():
        return json.loads(response_file.read_text(encoding="utf-8"))
    
    return {
        "id": 12345,
        "trackName": "Ghost In A Flower",
        "artistName": "Yorushika",
        "albumName": "Plagiarism",
        "duration": 245,
        "plainLyrics": "花に亡霊\n夜に駆ける\n星の瞬き\n...",
        "syncedLyrics": "[00:00.00]花に亡霊\n[00:05.00]夜に駆ける\n[00:10.00]星の瞬き\n..."
    }


@pytest.fixture
def mock_lrclib_not_found_response(mock_responses_dir):
    """
    Mock LRCLib未找到响应fixture

    Args:
        mock_responses_dir: Mock响应数据目录

    Returns:
        dict: Mock LRCLib未找到响应数据
    """
    response_file = mock_responses_dir / "lrclib_not_found.json"
    if response_file.exists():
        return json.loads(response_file.read_text(encoding="utf-8"))
    
    return {
        "statusCode": 404,
        "message": "Lyrics not found"
    }


@pytest.fixture
def mock_applemusic_success_response(mock_responses_dir):
    """
    Mock Apple Music成功响应fixture

    Args:
        mock_responses_dir: Mock响应数据目录

    Returns:
        dict: Mock Apple Music成功响应数据
    """
    response_file = mock_responses_dir / "applemusic_success.json"
    if response_file.exists():
        return json.loads(response_file.read_text(encoding="utf-8"))
    
    return {
        "trackName": "Ghost In A Flower",
        "artistName": "Yorushika",
        "albumName": "Plagiarism",
        "duration": 245,
        "plainLyrics": "花に亡霊\n夜に駆ける\n...",
        "syncedLyrics": "[00:00.00]花に亡霊\n[00:05.00]夜に駆ける\n..."
    }


@pytest.fixture
def mock_musixmatch_success_response(mock_responses_dir):
    """
    Mock MusixMatch成功响应fixture

    Args:
        mock_responses_dir: Mock响应数据目录

    Returns:
        dict: Mock MusixMatch成功响应数据
    """
    response_file = mock_responses_dir / "musixmatch_success.json"
    if response_file.exists():
        return json.loads(response_file.read_text(encoding="utf-8"))
    
    return {
        "trackName": "Ghost In A Flower",
        "artistName": "Yorushika",
        "albumName": "Plagiarism",
        "duration": 245,
        "plainLyrics": "花に亡霊\n夜に駆ける\n...",
        "syncedLyrics": "[00:00.00]花に亡霊\n[00:05.00]夜に駆ける\n..."
    }


@pytest.fixture
def temp_audio_file():
    """
    临时音频文件fixture

    Yields:
        str: 临时音频文件路径
    """
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        temp_file = f.name
        f.write(b"fake mp3 content for testing")
    
    yield temp_file
    
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def temp_flac_file():
    """
    临时FLAC文件fixture

    Yields:
        str: 临时FLAC文件路径
    """
    with tempfile.NamedTemporaryFile(suffix=".flac", delete=False) as f:
        temp_file = f.name
        f.write(b"fake flac content for testing")
    
    yield temp_file
    
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def temp_ogg_file():
    """
    临时OGG文件fixture

    Yields:
        str: 临时OGG文件路径
    """
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        temp_file = f.name
        f.write(b"fake ogg content for testing")
    
    yield temp_file
    
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def temp_m4a_file():
    """
    临时M4A文件fixture

    Yields:
        str: 临时M4A文件路径
    """
    with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as f:
        temp_file = f.name
        f.write(b"fake m4a content for testing")
    
    yield temp_file
    
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def temp_empty_file():
    """
    临时空文件fixture

    Yields:
        str: 临时空文件路径
    """
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        temp_file = f.name
    
    yield temp_file
    
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def temp_corrupted_file():
    """
    临时损坏文件fixture

    Yields:
        str: 临时损坏文件路径
    """
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        temp_file = f.name
        f.write(b"\x00\x00\x00\x00\x00\x00\x00\x00")
    
    yield temp_file
    
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def sample_lrc_lyrics():
    """
    样本LRC歌词fixture

    Returns:
        str: 样本LRC歌词内容
    """
    return "[00:00.00]花に亡霊\n[00:05.00]夜に駆ける\n[00:10.00]星の瞬き\n[00:15.00]風の音\n[00:20.00]君の声"


@pytest.fixture
def sample_ttml_lyrics():
    """
    样本TTML歌词fixture

    Returns:
        str: 样本TTML歌词内容
    """
    return """<?xml version="1.0" encoding="UTF-8"?>
<tt xmlns="http://www.w3.org/ns/ttml">
  <body>
    <div>
      <p begin="00:00:00.000" end="00:00:05.000">花に亡霊</p>
      <p begin="00:00:05.000" end="00:00:10.000">夜に駆ける</p>
      <p begin="00:00:10.000" end="00:00:15.000">星の瞬き</p>
    </div>
  </body>
</tt>"""


@pytest.fixture
def sample_srt_lyrics():
    """
    样本SRT歌词fixture

    Returns:
        str: 样本SRT歌词内容
    """
    return """1
00:00:00,000 --> 00:00:05,000
花に亡霊

2
00:00:05,000 --> 00:00:10,000
夜に駆ける

3
00:00:10,000 --> 00:00:15,000
星の瞬き"""


@pytest.fixture
def sample_json_lyrics():
    """
    样本JSON歌词fixture

    Returns:
        str: 样本JSON歌词内容
    """
    return json.dumps({
        "lyrics": [
            {"time": 0, "text": "花に亡霊"},
            {"time": 5, "text": "夜に駆ける"},
            {"time": 10, "text": "星の瞬き"}
        ]
    }, ensure_ascii=False, indent=2)


@pytest.fixture
def mock_audio_object():
    """
    Mock音频对象fixture

    Returns:
        MagicMock: Mock音频对象
    """
    mock_audio = MagicMock()
    mock_audio.title = "Ghost In A Flower"
    mock_audio.artist = "Yorushika"
    mock_audio.album = "Plagiarism"
    mock_audio.duration = 245
    mock_audio.track_name = "Ghost In A Flower"
    mock_audio.artist_name = "Yorushika"
    mock_audio.album_name = "Plagiarism"
    return mock_audio


@pytest.fixture
def mock_iter_files_success(mock_lrclib_success_response):
    """
    Mock iter_files成功响应fixture

    Args:
        mock_lrclib_success_response: Mock LRCLib成功响应

    Returns:
        MagicMock: Mock iter_files函数
    """
    mock_result = {
        'success': True,
        'data': {
            'plainLyrics': mock_lrclib_success_response['plainLyrics'],
            'syncedLyrics': mock_lrclib_success_response['syncedLyrics']
        }
    }
    
    with patch('auto_tag.lyric.manager.iter_files') as mock_iter:
        mock_iter.return_value = [mock_result]
        yield mock_iter


@pytest.fixture
def mock_iter_files_not_found():
    """
    Mock iter_files未找到响应fixture

    Returns:
        MagicMock: Mock iter_files函数
    """
    mock_result = {
        'success': False,
        'error': 'Lyrics not found'
    }
    
    with patch('auto_tag.lyric.manager.iter_files') as mock_iter:
        mock_iter.return_value = [mock_result]
        yield mock_iter


@pytest.fixture
def lyric_manager():
    """
    LyricManager实例fixture

    Returns:
        LyricManager: LyricManager实例
    """
    from auto_tag.lyric import LyricManager
    return LyricManager()


def pytest_configure(config):
    """
    pytest配置钩子

    添加自定义标记

    Args:
        config: pytest配置对象
    """
    config.addinivalue_line(
        "markers", "benchmark: mark test as a benchmark test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )
