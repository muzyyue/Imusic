# -*- coding: utf-8 -*-
"""
多语言文本分离功能单元测试

测试 split_multilingual_text() 和 is_multilingual_text() 函数
覆盖各种边界情况和特殊字符处理。
支持中日韩泰越俄阿等多语言。
"""

import pytest
from auto_tag.utils import split_multilingual_text, is_multilingual_text


class TestSplitMultilingualText:
    """测试多语言文本分离功能"""

    def test_pure_chinese(self):
        """纯中文输入"""
        result = split_multilingual_text("小小奇迹")
        assert result['native'] == "小小奇迹"
        assert result['latin'] == ""
        assert result['has_both'] is False
        assert result['original'] == "小小奇迹"

    def test_pure_english(self):
        """纯英文输入"""
        result = split_multilingual_text("A Small Miracle")
        assert result['native'] == ""
        assert result['latin'] == "A Small Miracle"
        assert result['has_both'] is False
        assert result['original'] == "A Small Miracle"

    def test_mixed_chinese_english_basic(self):
        """基本混合中英文"""
        result = split_multilingual_text("A Small Miracle 小小奇迹")
        assert "小小奇迹" in result['native']
        assert "A Small Miracle" in result['latin']
        assert result['has_both'] is True

    def test_mixed_with_parentheses(self):
        """包含括号的混合文本"""
        result = split_multilingual_text("A Small Miracle 小小奇迹 (Instrumental)")
        assert "小小奇迹" in result['native']
        assert "A Small Miracle" in result['latin']
        assert "Instrumental" in result['latin']
        assert result['has_both'] is True

    def test_empty_input(self):
        """空字符串输入"""
        result = split_multilingual_text("")
        assert result['native'] == ""
        assert result['latin'] == ""
        assert result['has_both'] is False
        assert result['original'] == ""

    def test_none_input(self):
        """None 输入"""
        result = split_multilingual_text(None)
        assert result['native'] == ""
        assert result['latin'] == ""
        assert result['has_both'] is False


class TestIsMultilingualText:
    """测试多语言混合检测功能"""

    def test_detects_mixed(self):
        """检测到混合"""
        assert is_multilingual_text("Hello 世界") is True
        assert is_multilingual_text("A Small Miracle 小小奇迹") is True

    def test_no_mixed_pure_chinese(self):
        """纯中文不触发"""
        assert is_multilingual_text("小小奇迹") is False
        assert is_multilingual_text("测试") is False

    def test_no_mixed_pure_english(self):
        """纯英文不触发"""
        assert is_multilingual_text("Hello World") is False
        assert is_multilingual_text("A Small Miracle") is False

    def test_no_mixed_empty(self):
        """空值不触发"""
        assert is_multilingual_text("") is False
        assert is_multilingual_text(None) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
