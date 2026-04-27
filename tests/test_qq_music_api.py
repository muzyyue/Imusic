#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QQ 音乐 API 测试套件

覆盖场景：
1. 数据解析逻辑（_parse_qqmusic_result）
2. HTTP请求层（_do_qqmusic_search）
3. 异步搜索函数（_search_qqmusic）
4. 多源搜索集成（multi_source_search包含qqmusic）
5. 错误处理机制

运行方式:
    python -m pytest tests/test_qq_music_api.py -v
    或直接运行:
    python tests/test_qq_music_api.py

作者: ling
创建日期: 2026-04-25
"""

import asyncio
import sys
import os
import json
from unittest.mock import patch, MagicMock, PropertyMock

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_tag.audio_recognize import (
    _parse_qqmusic_result,
    _do_qqmusic_search,
    _search_qqmusic,
    multi_source_search,
    SearchResult,
)


# ============================================================================
# 测试数据常量
# ============================================================================

#: 标准 QQ 音乐 API 完整响应（新版统一网关嵌套结构）
SAMPLE_QQ_MUSIC_RESPONSE = {
    "code": 0,
    "search": {
        "data": {
            "body": {
                "item_song": [
                    {
                        "id": 123456,
                        "mid": "xxxxxxxxxxxx",
                        "name": "晴天",
                        "singer": [{"id": 1, "mid": "s1", "name": "周杰伦"}],
                        "album": {"id": 789, "mid": "yyyyyyyyyyyy", "name": "叶惠美"},
                        "interval": 249,
                        "label": "杰威尔音乐"
                    }
                ]
            },
            "meta": {
                "estimate_sum": 1,
                "sum": 1
            }
        }
    }
}

#: 多歌手歌曲测试数据（新格式）
MULTI_SINGER_SONG = {
    "id": 234567,
    "mid": "zzzzzzzzzzzz",
    "name": "稻香",
    "singer": [
        {"id": 1, "mid": "s1", "name": "周杰伦"},
        {"id": 2, "mid": "s2", "name": "方文山"}
    ],
    "album": {"id": 100, "mid": "aaaaaaaaaaaa", "name": "魔杰座"},
    "interval": 223
}

#: 缺失部分字段的歌曲数据（新格式）
MISSING_FIELDS_SONG = {
    "id": 345678,
    # mid 缺失
    "name": "测试歌曲",
    # singer 列表缺失
    # album 对象缺失或部分字段缺失
    "album": {},
    # interval 缺失
}

#: 无效时长数据的歌曲数据
INVALID_INTERVAL_SONGS = [
    {
        "id": 456789,
        "name": "无效时长1",
        "singer": [{"name": "测试歌手"}],
        "album": {"mid": "bbbbbbbbbbbb", "name": "测试专辑"},
        "interval": "abc"  # 非数字字符串
    },
    {
        "id": 567890,
        "name": "无效时长2",
        "singer": [{"name": "测试歌手"}],
        "album": {"mid": "cccccccccccc", "name": "测试专辑"},
        "interval": "-100"  # 负数
    }
]

#: 空 API 响应（无结果）
EMPTY_RESPONSE = {
    "code": 0,
    "search": {
        "data": {
            "body": {
                "item_song": []
            },
            "meta": {
                "estimate_sum": 0,
                "sum": 0
            }
        }
    }
}

#: API 错误响应（code != 0）
API_ERROR_RESPONSE = {
    "code": -100,
    "msg": "参数错误"
}


# ============================================================================
# Test Class 1: TestParseQQMusicResult
# ============================================================================

class TestParseQQMusicResult:
    """测试 _parse_qqmusic_result() 函数的数据解析能力"""

    def test_parse_normal_song(self):
        """
        测试解析标准歌曲数据（所有字段完整）

        验证点：
        - source 字段为 'qqmusic'
        - title/artist/album/duration 正确提取
        - cover_link 格式符合预期
        """
        song_data = SAMPLE_QQ_MUSIC_RESPONSE["search"]["data"]["body"]["item_song"][0]
        result = _parse_qqmusic_result(song_data)

        assert isinstance(result, SearchResult), "返回值应为 SearchResult 类型"
        assert result.source == "qqmusic", f"source 应为 'qqmusic'，实际为 '{result.source}'"

        assert result.title == "晴天", f"title 应为 '晴天'，实际为 '{result.title}'"
        assert result.artist == "周杰伦", f"artist 应为 '周杰伦'，实际为 '{result.artist}'"
        assert result.album == "叶惠美", f"album 应为 '叶惠美'，实际为 '{result.album}'"
        assert result.duration == 249, f"duration 应为 249，实际为 {result.duration}"
        assert result.song_id == "123456", f"song_id 应为 '123456'，实际为 '{result.song_id}'"

        expected_cover = "https://y.gtimg.cn/music/photo_new/T002R500x500M000yyyyyyyyyyyy.jpg"
        assert result.cover_link == expected_cover, (
            f"cover_link 格式错误，预期 '{expected_cover}'，实际 '{result.cover_link}'"
        )

    def test_parse_multiple_singers(self):
        """测试解析多歌手歌曲"""
        result = _parse_qqmusic_result(MULTI_SINGER_SONG)

        expected_artist = "周杰伦 / 方文山"
        assert result.artist == expected_artist, (
            f"多歌手应使用 ' / ' 连接，预期 '{expected_artist}'，实际为 '{result.artist}'"
        )
        assert result.title == "稻香", f"title 应为 '稻香'，实际为 '{result.title}'"
        assert result.duration == 223, f"duration 应为 223，实际为 {result.duration}"

    def test_parse_missing_fields(self):
        """测试解析缺失字段的异常数据"""
        result = _parse_qqmusic_result(MISSING_FIELDS_SONG)

        assert isinstance(result, SearchResult), "即使字段缺失也应返回 SearchResult"
        assert result.title == "测试歌曲", "title 应正确提取"
        assert result.artist == "Unknown Artist", (
            f"singer 缺失时 artist 应为 'Unknown Artist'，实际为 '{result.artist}'"
        )
        assert result.album == "Unknown Album", (
            f"album 为空字典时 album 应为 'Unknown Album'，实际为 '{result.album}'"
        )
        assert result.duration == 0, f"interval 缺失时 duration 应为 0，实际为 {result.duration}"
        assert result.cover_link == "", (
            f"album.mid 缺失时 cover_link 应为空字符串，实际为 '{result.cover_link}'"
        )

    def test_parse_invalid_interval(self):
        """测试解析无效的时长数据"""
        result1 = _parse_qqmusic_result(INVALID_INTERVAL_SONGS[0])
        assert result1.duration == 0, (
            f"非数字 interval 应转换为 0，实际为 {result1.duration}"
        )

        result2 = _parse_qqmusic_result(INVALID_INTERVAL_SONGS[1])
        assert result2.duration == -100, (
            f"负数 interval 应保留原值，实际为 {result2.duration}"
        )

    def test_parse_cover_url_generation(self):
        """测试封面 URL 生成逻辑"""
        test_cases = [
            ("yyyyyyyyyyyy", "https://y.gtimg.cn/music/photo_new/T002R500x500M000yyyyyyyyyyyy.jpg"),
            ("aaaaaaaaaaaa", "https://y.gtimg.cn/music/photo_new/T002R500x500M000aaaaaaaaaaaa.jpg"),
            ("001abcdef1234", "https://y.gtimg.cn/music/photo_new/T002R500x500M000001abcdef1234.jpg"),
        ]

        for albummid, expected_url in test_cases:
            song_data = {"album": {"mid": albummid}}
            result = _parse_qqmusic_result(song_data)
            assert result.cover_link == expected_url, (
                f"album.mid='{albummid}' 时 cover_link 应为 '{expected_url}'，"
                f"实际为 '{result.cover_link}'"
            )

        empty_result = _parse_qqmusic_result({"album": {}})
        assert empty_result.cover_link == "", "空 album.mid 应返回空 cover_link"


# ============================================================================
# Test Class 2: TestDoQQMusicSearch
# ============================================================================

class TestDoQQMusicSearch:
    """测试 _do_qqmusic_search() 函数的 HTTP 请求层"""

    @patch('http.client')
    def test_successful_search(self, mock_http_client):
        """测试成功的搜索请求"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(SAMPLE_QQ_MUSIC_RESPONSE).encode('utf-8')

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPSConnection.return_value = mock_conn

        results = _do_qqmusic_search("晴天", limit=5)

        assert isinstance(results, list), "返回值应为列表"
        assert len(results) > 0, "成功搜索应返回非空列表"

        first_result = results[0]
        assert first_result.source == "qqmusic", "source 应为 'qqmusic'"
        assert first_result.title == "晴天", f"title 应为 '晴天'，实际为 '{first_result.title}'"

        mock_conn.request.assert_called_once()
        mock_conn.getresponse.assert_called_once()

    @patch('http.client')
    def test_empty_results(self, mock_http_client):
        """测试搜索结果为空的情况"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(EMPTY_RESPONSE).encode('utf-8')

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPSConnection.return_value = mock_conn

        results = _do_qqmusic_search("不存在的歌曲xyz123")

        assert results == [], f"空结果应返回空列表，实际返回 {results}"
        assert len(results) == 0, "空结果列表长度应为 0"

    @patch('http.client')
    def test_network_error(self, mock_http_client):
        """测试网络连接错误"""
        mock_conn = MagicMock()
        mock_conn.request.side_effect = ConnectionError("Network unreachable")
        mock_http_client.HTTPSConnection.return_value = mock_conn

        results = _do_qqmusic_search("测试关键词")
        assert results == [], "网络错误时应返回空列表"

        mock_conn.request.side_effect = TimeoutError("Request timeout")
        results2 = _do_qqmusic_search("测试关键词")
        assert results2 == [], "超时错误时应返回空列表"

    @patch('http.client')
    def test_api_error_response(self, mock_http_client):
        """测试 API 返回错误状态码"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(API_ERROR_RESPONSE).encode('utf-8')

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPSConnection.return_value = mock_conn

        results = _do_qqmusic_search("测试关键词")
        assert results == [], "API 错误时应返回空列表"

    @patch('http.client')
    def test_invalid_json_response(self, mock_http_client):
        """测试无效的 JSON 响应"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"invalid json data'

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPSConnection.return_value = mock_conn

        results = _do_qqmusic_search("测试关键词")
        assert results == [], "无效 JSON 时应返回空列表"


# ============================================================================
# Test Class 3: TestSearchQQMusicAsync
# ============================================================================

class TestSearchQQMusicAsync:
    """测试 _search_qqmusic() 异步函数"""

    @patch('auto_tag.audio_recognize._do_qqmusic_search')
    def test_async_search_success(self, mock_do_search):
        """测试异步搜索成功"""
        song_data = SAMPLE_QQ_MUSIC_RESPONSE["search"]["data"]["body"]["item_song"][0]
        expected_results = [_parse_qqmusic_result(song_data)]
        mock_do_search.return_value = expected_results

        results = asyncio.run(_search_qqmusic("晴天", limit=5))

        assert isinstance(results, list), "异步搜索应返回列表"
        assert len(results) == 1, f"应返回 1 条结果，实际 {len(results)} 条"
        assert results[0].source == "qqmusic", "结果 source 应为 'qqmusic'"
        assert results[0].title == "晴天", f"title 应为 '晴天'，实际为 '{results[0].title}'"

        mock_do_search.assert_called_once_with("晴天", 5)

    @patch('auto_tag.audio_recognize._do_qqmusic_search')
    def test_async_search_with_retry(self, mock_do_search):
        """测试异常处理和容错能力"""
        mock_do_search.side_effect = ConnectionError("模拟网络错误")

        results = asyncio.run(_search_qqmusic("周杰伦", limit=5))

        assert isinstance(results, list), "异常情况下仍应返回列表"
        assert len(results) == 0, "异常情况应返回空列表"
        mock_do_search.assert_called_once()

        mock_do_search.side_effect = TimeoutError("请求超时")
        results2 = asyncio.run(_search_qqmusic("测试歌曲"))
        assert results2 == [], "超时异常也应返回空列表"

    @patch('auto_tag.audio_recognize._do_qqmusic_search')
    def test_async_search_all_retries_failed(self, mock_do_search):
        """测试所有重试都失败的情况"""
        mock_do_search.return_value = []

        results = asyncio.run(_search_qqmusic("不存在的歌曲"))

        assert results == [], "搜索失败应返回空列表"
        assert len(results) == 0, "失败时结果列表长度应为 0"
        mock_do_search.assert_called_once()


# ============================================================================
# Test Class 4: TestMultiSourceIntegration
# ============================================================================

class TestMultiSourceIntegration:
    """测试 multi_source_search() 对 QQ 音乐源的集成"""

    @patch('auto_tag.audio_recognize._search_qqmusic')
    @patch('auto_tag.audio_recognize._search_netease_rest')
    def test_qqmusic_in_sources(self, mock_netease, mock_qqmusic):
        """测试 qqmusic 在源列表中的情况"""
        song_data = SAMPLE_QQ_MUSIC_RESPONSE["search"]["data"]["body"]["item_song"][0]
        qqmusic_results = [_parse_qqmusic_result(song_data)]
        mock_qqmusic.return_value = qqmusic_results
        mock_netease.return_value = []

        results = asyncio.run(multi_source_search(
            keyword="晴天",
            sources=["shazam", "netease", "qqmusic"],
            limit=5
        ))

        qqmusic_items = [r for r in results if r.source == "qqmusic"]
        assert len(qqmusic_items) > 0, "结果中应包含 qqmusic 源的条目"
        assert qqmusic_items[0].title == "晴天", "qqmusic 结果 title 应为 '晴天'"
        mock_qqmusic.assert_called_once()

    @patch('auto_tag.audio_recognize._search_qqmusic')
    @patch('auto_tag.audio_recognize._search_netease_rest')
    def test_qqmusic_not_in_sources(self, mock_netease, mock_qqmusic):
        """测试 qqmusic 不在源列表中的情况"""
        mock_netease.return_value = []
        mock_qqmusic.return_value = []

        results = asyncio.run(multi_source_search(
            keyword="晴天",
            sources=["shazam", "netease"],
            limit=5
        ))

        mock_qqmusic.assert_not_called()
        qqmusic_items = [r for r in results if r.source == "qqmusic"]
        assert len(qqmusic_items) == 0, "qqmusic 不在源列表时，结果中不应有 qqmusic 条目"

    @patch('auto_tag.audio_recognize._search_qqmusic')
    @patch('auto_tag.audio_recognize._search_netease_rest')
    def test_qqmusic_only_source(self, mock_netease, mock_qqmusic):
        """测试仅使用 QQ 音乐源的情况"""
        expected_results = [_parse_qqmusic_result(MULTI_SINGER_SONG)]
        mock_qqmusic.return_value = expected_results

        results = asyncio.run(multi_source_search(
            keyword="稻香",
            sources=["qqmusic"],
            limit=5
        ))

        # multi_source_search 会传递 fingerprint_engine='none' 参数
        mock_qqmusic.assert_called_once()
        call_kwargs = mock_qqmusic.call_args
        assert "稻香" in str(call_kwargs)
        mock_netease.assert_not_called()

        assert len(results) == 1, f"应返回 1 条结果，实际 {len(results)} 条"
        assert results[0].source == "qqmusic", "结果应来自 qqmusic"
        assert results[0].title == "稻香", f"title 应为 '稻香'，实际为 '{results[0].title}'"
        assert results[0].artist == "周杰伦 / 方文山", (
            f"artist 应为 '周杰伦 / 方文山'，实际为 '{results[0].artist}'"
        )


# ============================================================================
# Test Class 5: TestEdgeCases
# ============================================================================

class TestEdgeCases:
    """边界情况和特殊字符处理"""

    @patch('http.client')
    def test_special_characters_keyword(self, mock_http_client):
        """测试特殊字符关键词"""
        special_keyword = "Hello 世界!@#$%^&*()_+-=[]{}|;':\",./<>?"

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(SAMPLE_QQ_MUSIC_RESPONSE).encode('utf-8')

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPSConnection.return_value = mock_conn

        try:
            results = _do_qqmusic_search(special_keyword)
            assert isinstance(results, list), "应返回列表类型"
        except Exception as e:
            assert False, f"特殊字符关键词不应导致异常: {e}"

    @patch('http.client')
    def test_very_long_keyword(self, mock_http_client):
        """测试超长关键词"""
        long_keyword = "A" * 200

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(SAMPLE_QQ_MUSIC_RESPONSE).encode('utf-8')

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPSConnection.return_value = mock_conn

        results = _do_qqmusic_search(long_keyword)
        assert isinstance(results, list), "超长关键词应返回列表"

    @patch('http.client')
    def test_empty_keyword(self, mock_http_client):
        """测试空关键词"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(EMPTY_RESPONSE).encode('utf-8')

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPSConnection.return_value = mock_conn

        try:
            results = _do_qqmusic_search("")
            assert isinstance(results, list), "空关键词应返回列表而不崩溃"
        except Exception as e:
            assert False, f"空关键词不应导致未处理的异常: {e}"


# ============================================================================
# 主入口
# ============================================================================

if __name__ == '__main__':
    import pytest
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
    ])
    sys.exit(exit_code)
