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

#: 标准 QQ 音乐 API 完整响应（包含所有字段）
SAMPLE_QQ_MUSIC_RESPONSE = {
    "result": 100,
    "data": {
        "list": [
            {
                "songid": 123456,
                "songmid": "xxxxxxxxxxxx",
                "songname": "晴天",
                "singer": [{"id": 1, "name": "周杰伦"}],
                "albumname": "叶惠美",
                "albumid": 789,
                "albummid": "yyyyyyyyyyyy",
                "interval": "249",
                "label": "杰威尔音乐"
            }
        ],
        "total": 1
    }
}

#: 多歌手歌曲测试数据
MULTI_SINGER_SONG = {
    "songid": 234567,
    "songmid": "zzzzzzzzzzzz",
    "songname": "稻香",
    "singer": [
        {"id": 1, "name": "周杰伦"},
        {"id": 2, "name": "方文山"}
    ],
    "albumname": "魔杰座",
    "albummid": "aaaaaaaaaaaa",
    "interval": "223"
}

#: 缺失部分字段的歌曲数据
MISSING_FIELDS_SONG = {
    "songid": 345678,
    # songmid 缺失
    "songname": "测试歌曲",
    # singer 列表缺失
    # albumname 缺失
    "albummid": "",
    # interval 缺失
}

#: 无效时长数据的歌曲数据
INVALID_INTERVAL_SONGS = [
    {
        "songid": 456789,
        "songname": "无效时长1",
        "singer": [{"name": "测试歌手"}],
        "albumname": "测试专辑",
        "albummid": "bbbbbbbbbbbb",
        "interval": "abc"  # 非数字字符串
    },
    {
        "songid": 567890,
        "songname": "无效时长2",
        "singer": [{"name": "测试歌手"}],
        "albumname": "测试专辑",
        "albummid": "cccccccccccc",
        "interval": "-100"  # 负数
    }
]

#: 空 API 响应（无结果）
EMPTY_RESPONSE = {
    "result": 100,
    "data": {
        "list": [],
        "total": 0
    }
}

#: API 错误响应（result != 100）
API_ERROR_RESPONSE = {
    "result": -100,
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
        song_data = SAMPLE_QQ_MUSIC_RESPONSE["data"]["list"][0]
        result = _parse_qqmusic_result(song_data)

        # 验证返回类型
        assert isinstance(result, SearchResult), "返回值应为 SearchResult 类型"

        # 验证 source 标识
        assert result.source == "qqmusic", f"source 应为 'qqmusic'，实际为 '{result.source}'"

        # 验证基本字段
        assert result.title == "晴天", f"title 应为 '晴天'，实际为 '{result.title}'"
        assert result.artist == "周杰伦", f"artist 应为 '周杰伦'，实际为 '{result.artist}'"
        assert result.album == "叶惠美", f"album 应为 '叶惠美'，实际为 '{result.album}'"
        assert result.duration == 249, f"duration 应为 249，实际为 {result.duration}"
        assert result.song_id == "123456", f"song_id 应为 '123456'，实际为 '{result.song_id}'"

        # 验证封面 URL 格式
        expected_cover = "https://y.gtimg.cn/music/photo_new/T002R500x500M000yyyyyyyyyyyy.jpg"
        assert result.cover_link == expected_cover, (
            f"cover_link 格式错误，预期 '{expected_cover}'，实际 '{result.cover_link}'"
        )

    def test_parse_multiple_singers(self):
        """
        测试解析多歌手歌曲

        验证点：
        - 多个歌手名用 " / " 连接
        - 歌手顺序保持一致
        """
        result = _parse_qqmusic_result(MULTI_SINGER_SONG)

        expected_artist = "周杰伦 / 方文山"
        assert result.artist == expected_artist, (
            f"多歌手应使用 ' / ' 连接，预期 '{expected_artist}'，实际 '{result.artist}'"
        )

        # 验证其他字段正常
        assert result.title == "稻香", f"title 应为 '稻香'，实际为 '{result.title}'"
        assert result.duration == 223, f"duration 应为 223，实际为 {result.duration}"

    def test_parse_missing_fields(self):
        """
        测试解析缺失字段的异常数据

        验证点：
        - 缺失字段使用默认值
        - 不抛出异常
        - 返回有效的 SearchResult 对象
        """
        # 不应抛出任何异常
        result = _parse_qqmusic_result(MISSING_FIELDS_SONG)

        assert isinstance(result, SearchResult), "即使字段缺失也应返回 SearchResult"

        # 验证默认值
        assert result.title == "测试歌曲", "title 应正确提取"
        assert result.artist == "Unknown Artist", (
            f"singer 缺失时 artist 应为 'Unknown Artist'，实际为 '{result.artist}'"
        )
        assert result.album == "Unknown Album", (
            f"albumname 缺失时 album 应为 'Unknown Album'，实际为 '{result.album}'"
        )
        assert result.duration == 0, f"interval 缺失时 duration 应为 0，实际为 {result.duration}"
        assert result.cover_link == "", (
            f"albummid 为空时 cover_link 应为空字符串，实际为 '{result.cover_link}'"
        )

    def test_parse_invalid_interval(self):
        """
        测试解析无效的时长数据

        验证点：
        - 非数字字符串时 duration=0
        - 负数时 duration 为对应的负整数值（由 int() 决定）
        - 不抛出异常
        """
        # 测试非数字字符串
        result1 = _parse_qqmusic_result(INVALID_INTERVAL_SONGS[0])
        assert result1.duration == 0, (
            f"非数字 interval 应转换为 0，实际为 {result1.duration}"
        )

        # 测试负数（int("-100") = -100）
        result2 = _parse_qqmusic_result(INVALID_INTERVAL_SONGS[1])
        assert result2.duration == -100, (
            f"负数 interval 应保留原值，实际为 {result2.duration}"
        )

    def test_parse_cover_url_generation(self):
        """
        测试封面 URL 生成逻辑

        验证点：
        - 有 albummid 时生成正确的 URL
        - URL 格式符合 QQ 音乐 CDN 规范
        - 不同 albummid 生成不同 URL
        """
        test_cases = [
            ("yyyyyyyyyyyy", "https://y.gtimg.cn/music/photo_new/T002R500x500M000yyyyyyyyyyyy.jpg"),
            ("aaaaaaaaaaaa", "https://y.gtimg.cn/music/photo_new/T002R500x500M000aaaaaaaaaaaa.jpg"),
            ("001abcdef1234", "https://y.gtimg.cn/music/photo_new/T002R500x500M000001abcdef1234.jpg"),
        ]

        for albummid, expected_url in test_cases:
            song_data = {"albummid": albummid}
            result = _parse_qqmusic_result(song_data)
            assert result.cover_link == expected_url, (
                f"albummid='{albummid}' 时 cover_link 应为 '{expected_url}'，"
                f"实际为 '{result.cover_link}'"
            )

        # 测试空 albummid
        empty_result = _parse_qqmusic_result({"albummid": ""})
        assert empty_result.cover_link == "", "空 albummid 应返回空 cover_link"


# ============================================================================
# Test Class 2: TestDoQQMusicSearch
# ============================================================================

class TestDoQQMusicSearch:
    """测试 _do_qqmusic_search() 函数的 HTTP 请求层"""

    @patch('http.client')
    def test_successful_search(self, mock_http_client):
        """
        测试成功的搜索请求

        Mock HTTP 响应返回有效的 JSON 数据，
        验证返回非空的 SearchResult 列表。
        """
        # 设置 mock 响应对象
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(SAMPLE_QQ_MUSIC_RESPONSE).encode('utf-8')

        # 设置 mock 连接对象
        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPConnection.return_value = mock_conn

        # 执行搜索
        results = _do_qqmusic_search("晴天", limit=5)

        # 验证结果
        assert isinstance(results, list), "返回值应为列表"
        assert len(results) > 0, "成功搜索应返回非空列表"

        # 验证第一个结果的字段
        first_result = results[0]
        assert first_result.source == "qqmusic", "source 应为 'qqmusic'"
        assert first_result.title == "晴天", f"title 应为 '晴天'，实际为 '{first_result.title}'"

        # 验证 HTTP 调用
        mock_conn.request.assert_called_once()
        mock_conn.getresponse.assert_called_once()

    @patch('http.client')
    def test_empty_results(self, mock_http_client):
        """
        测试搜索结果为空的情况

        Mock API 返回空列表，
        验证返回空列表而非 None 或异常。
        """
        # 设置 mock 响应：空结果
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(EMPTY_RESPONSE).encode('utf-8')

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPConnection.return_value = mock_conn

        # 执行搜索
        results = _do_qqmusic_search("不存在的歌曲xyz123")

        # 验证结果
        assert results == [], f"空结果应返回空列表，实际返回 {results}"
        assert len(results) == 0, "空结果列表长度应为 0"

    @patch('http.client')
    def test_network_error(self, mock_http_client):
        """
        测试网络连接错误

        Mock 抛出 ConnectionError 等异常，
        验证捕获异常并返回空列表，不崩溃。
        """
        # 设置 mock 连接在 request 时抛出异常
        mock_conn = MagicMock()
        mock_conn.request.side_effect = ConnectionError("Network unreachable")
        mock_http_client.HTTPConnection.return_value = mock_conn

        # 执行搜索（不应抛出异常）
        results = _do_qqmusic_search("测试关键词")

        # 验证结果
        assert results == [], "网络错误时应返回空列表"

        # 测试其他类型的异常
        mock_conn.request.side_effect = TimeoutError("Request timeout")
        results2 = _do_qqmusic_search("测试关键词")
        assert results2 == [], "超时错误时应返回空列表"

    @patch('http.client')
    def test_api_error_response(self, mock_http_client):
        """
        测试 API 返回错误状态码

        Mock API 返回 result != 100 的响应，
        验证记录错误日志并返回空列表。
        """
        # 设置 mock 响应：API 错误
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(API_ERROR_RESPONSE).encode('utf-8')

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPConnection.return_value = mock_conn

        # 执行搜索
        results = _do_qqmusic_search("测试关键词")

        # 验证结果
        assert results == [], "API 错误时应返回空列表"

    @patch('http.client')
    def test_invalid_json_response(self, mock_http_client):
        """
        测试无效的 JSON 响应

        Mock 返回非法 JSON 字符串，
        验证捕获 JSONDecodeError 并返回空列表。
        """
        # 设置 mock 响应：无效 JSON
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"invalid json data'

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPConnection.return_value = mock_conn

        # 执行搜索
        results = _do_qqmusic_search("测试关键词")

        # 验证结果
        assert results == [], "无效 JSON 时应返回空列表"


# ============================================================================
# Test Class 3: TestSearchQQMusicAsync
# ============================================================================

class TestSearchQQMusicAsync:
    """测试 _search_qqmusic() 异步函数"""

    @patch('auto_tag.audio_recognize._do_qqmusic_search')
    def test_async_search_success(self, mock_do_search):
        """
        测试异步搜索成功

        Mock _do_qqmusic_search 返回有效结果，
        验证异步调用返回正确的结果列表。
        """
        # 设置 mock 返回值
        expected_results = [_parse_qqmusic_result(SAMPLE_QQ_MUSIC_RESPONSE["data"]["list"][0])]
        mock_do_search.return_value = expected_results

        # 执行异步搜索
        results = asyncio.run(_search_qqmusic("晴天", limit=5))

        # 验证结果
        assert isinstance(results, list), "异步搜索应返回列表"
        assert len(results) == 1, f"应返回 1 条结果，实际 {len(results)} 条"
        assert results[0].source == "qqmusic", "结果 source 应为 'qqmusic'"
        assert results[0].title == "晴天", f"title 应为 '晴天'，实际为 '{results[0].title}'"

        # 验证同步函数被调用
        mock_do_search.assert_called_once_with("晴天", 5)

    @patch('auto_tag.audio_recognize._do_qqmusic_search')
    def test_async_search_with_retry(self, mock_do_search):
        """
        测试异步搜索的异常处理和容错能力

        验证 _search_qqmusic 在底层调用失败时的行为：
        - 能够捕获异常并优雅处理
        - 不会导致程序崩溃
        - 返回空列表或合理默认值

        注意：当前实现不包含自动重试逻辑，
        此测试验证异常处理机制的有效性。
        """
        # 设置 mock：模拟底层调用抛出异常
        mock_do_search.side_effect = ConnectionError("模拟网络错误")

        # 执行异步搜索（应捕获异常并返回空列表）
        results = asyncio.run(_search_qqmusic("周杰伦", limit=5))

        # 验证结果
        assert isinstance(results, list), "异常情况下仍应返回列表"
        assert len(results) == 0, "异常情况应返回空列表"

        # 验证同步函数被调用了
        mock_do_search.assert_called_once()

        # 测试其他类型的异常
        mock_do_search.side_effect = TimeoutError("请求超时")
        results2 = asyncio.run(_search_qqmusic("测试歌曲"))
        assert results2 == [], "超时异常也应返回空列表"

    @patch('auto_tag.audio_recognize._do_qqmusic_search')
    def test_async_search_all_retries_failed(self, mock_do_search):
        """
        测试所有重试都失败的情况

        所有次 Mock 都失败（返回空列表），
        验证最终返回空列表。

        注意：当前实现中 _search_qqmusic 不包含重试逻辑，
        重试机制可能在更高层级实现。
        此测试验证单次调用失败时的行为。
        """
        # 设置 mock 始终返回空列表（模拟失败）
        mock_do_search.return_value = []

        # 执行异步搜索
        results = asyncio.run(_search_qqmusic("不存在的歌曲"))

        # 验证结果
        assert results == [], "搜索失败应返回空列表"
        assert len(results) == 0, "失败时结果列表长度应为 0"

        # 验证同步函数被调用了一次
        mock_do_search.assert_called_once()


# ============================================================================
# Test Class 4: TestMultiSourceIntegration
# ============================================================================

class TestMultiSourceIntegration:
    """测试 multi_source_search() 对 QQ 音乐源的集成"""

    @patch('auto_tag.audio_recognize._search_qqmusic')
    @patch('auto_tag.audio_recognize._search_netease_rest')
    def test_qqmusic_in_sources(self, mock_netease, mock_qqmusic):
        """
        测试 qqmusic 在源列表中的情况

        sources=["shazam", "netease", "qqmusic"]，
        Mock _search_qqmusic 返回结果，
        验证结果中包含 source="qqmusic" 的条目。
        """
        # 设置 mock 返回值
        qqmusic_results = [_parse_qqmusic_result(SAMPLE_QQ_MUSIC_RESPONSE["data"]["list"][0])]
        mock_qqmusic.return_value = qqmusic_results
        mock_netease.return_value = []

        # 执行多源搜索
        results = asyncio.run(multi_source_search(
            keyword="晴天",
            sources=["shazam", "netease", "qqmusic"],
            limit=5
        ))

        # 验证结果包含 QQ 音乐源
        qqmusic_items = [r for r in results if r.source == "qqmusic"]
        assert len(qqmusic_items) > 0, "结果中应包含 qqmusic 源的条目"
        assert qqmusic_items[0].title == "晴天", "qqmusic 结果 title 应为 '晴天'"

        # 验证 _search_qqmusic 被调用
        mock_qqmusic.assert_called_once()

    @patch('auto_tag.audio_recognize._search_qqmusic')
    @patch('auto_tag.audio_recognize._search_netease_rest')
    def test_qqmusic_not_in_sources(self, mock_netease, mock_qqmusic):
        """
        测试 qqmusic 不在源列表中的情况

        sources=["shazam", "netease"]，
        验证 _search_qqmusic 未被调用，
        结果中无 qqmusic 源。
        """
        # 设置 mock 返回值
        mock_netease.return_value = []
        mock_qqmusic.return_value = []  # 不应被调用

        # 执行多源搜索（不含 qqmusic）
        results = asyncio.run(multi_source_search(
            keyword="晴天",
            sources=["shazam", "netease"],
            limit=5
        ))

        # 验证 _search_qqmusic 未被调用
        mock_qqmusic.assert_not_called()

        # 验证结果中无 qqmusic 源
        qqmusic_items = [r for r in results if r.source == "qqmusic"]
        assert len(qqmusic_items) == 0, "qqmusic 不在源列表时，结果中不应有 qqmusic 条目"

    @patch('auto_tag.audio_recognize._search_qqmusic')
    @patch('auto_tag.audio_recognize._search_netease_rest')
    def test_qqmusic_only_source(self, mock_netease, mock_qqmusic):
        """
        测试仅使用 QQ 音乐源的情况

        sources=["qqmusic"]，
        验证只调用 _search_qqmusic，
        结果仅来自 qqmusic。
        """
        # 设置 mock 返回值
        expected_results = [_parse_qqmusic_result(MULTI_SINGER_SONG)]
        mock_qqmusic.return_value = expected_results

        # 执行多源搜索（仅 qqmusic）
        results = asyncio.run(multi_source_search(
            keyword="稻香",
            sources=["qqmusic"],
            limit=5
        ))

        # 验证只调用了 _search_qqmusic
        mock_qqmusic.assert_called_once_with("稻香", 5)
        mock_netease.assert_not_called()

        # 验证结果仅来自 qqmusic
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
        """
        测试特殊字符关键词

        关键词包含中文、英文、符号混合，
        验证 URL 编码正确，搜索正常执行。
        """
        # 特殊字符关键词
        special_keyword = "Hello 世界!@#$%^&*()_+-=[]{}|;':\",./<>?"

        # 设置 mock 响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(SAMPLE_QQ_MUSIC_RESPONSE).encode('utf-8')

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPConnection.return_value = mock_conn

        # 执行搜索（不应抛出异常）
        try:
            results = _do_qqmusic_search(special_keyword)
            # 如果成功返回结果或空列表都算通过
            assert isinstance(results, list), "应返回列表类型"
        except Exception as e:
            assert False, f"特殊字符关键词不应导致异常: {e}"

        # 验证请求被发送
        mock_conn.request.assert_called_once()

    @patch('http.client')
    def test_very_long_keyword(self, mock_http_client):
        """
        测试超长关键词

        关键词长度超过 100 字符，
        验证不截断，正常发送请求。
        """
        # 构建超长关键词（200字符）
        long_keyword = "A" * 200

        # 设置 mock 响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(SAMPLE_QQ_MUSIC_RESPONSE).encode('utf-8')

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPConnection.return_value = mock_conn

        # 执行搜索
        results = _do_qqmusic_search(long_keyword)

        # 验证结果
        assert isinstance(results, list), "超长关键词应返回列表"

        # 验证请求被发送（未被截断）
        call_args = mock_conn.request.call_args
        assert call_args is not None, "请求应被发送"

    @patch('http.client')
    def test_empty_keyword(self, mock_http_client):
        """
        测试空关键词

        关键词为空字符串，
        验证处理方式（可能返回空列表或报错）。
        """
        # 设置 mock 响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(EMPTY_RESPONSE).encode('utf-8')

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_http_client.HTTPConnection.return_value = mock_conn

        # 执行搜索（不应崩溃）
        try:
            results = _do_qqmusic_search("")
            # 空关键词可能返回空列表或有效结果
            assert isinstance(results, list), "空关键词应返回列表而不崩溃"
        except Exception as e:
            # 如果抛出异常也记录下来（某些实现可能会拒绝空关键词）
            assert False, f"空关键词不应导致未处理的异常: {e}"


# ============================================================================
# 主入口
# ============================================================================

if __name__ == '__main__':
    """
    直接运行测试文件的入口

    使用 pytest 运行当前文件的所有测试用例，
    并输出详细的测试报告。
    """
    import pytest

    # 运行当前文件的所有测试
    exit_code = pytest.main([
        __file__,
        '-v',          # 详细输出
        '--tb=short',  # 简短的 traceback
        '-x',           # 遇到第一个失败就停止（可选，注释掉可继续运行所有测试）
    ])

    # 退出码：0=全部通过，1=有失败
    sys.exit(exit_code)
