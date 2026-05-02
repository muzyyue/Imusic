# -*- coding: utf-8 -*-
"""
CI Lint 规则: 验证 Legacy 模块已完全移除

目的:
- 确认 _legacy_utils.py 已被删除（2026-05-02 重构完成）
- 验证 utils/__init__.py 中无遗留适配器函数
- 防止未来意外重新引入 legacy 依赖

历史背景:
- 2026-04-25: utils.py 重命名为 _legacy_utils.py，开始渐进式迁移
- 2026-05-02: audio_recognize.py 完成重构，移除所有 legacy 依赖
- 2026-05-02: 清理 legacy 代码，删除 _legacy_utils.py 和适配器

运行方式:
    uv run pytest tests/test_legacy_import_restriction.py -v

集成到 CI:
    此测试会自动包含在 pytest 全套测试中
"""

import os
import re
from pathlib import Path


# 正则匹配模式：检测任何 legacy 相关的导入或引用
LEGACY_REFERENCE_PATTERN = re.compile(
    r'_legacy_utils|_legacy_find_deepest|_legacy_sanitize',
    re.MULTILINE
)

# 需要扫描的目录（排除 tests 和 .venv）
SCAN_DIRS = ['auto_tag']

# 需要排除的目录
EXCLUDE_DIRS = {'__pycache__', '.venv', 'node_modules', '.git'}


class TestLegacyCompleteRemoval:
    """验证 Legacy 代码已完全清理"""

    def test_legacy_utils_file_exists_but_isolated(self):
        """
        验证 _legacy_utils.py 存在但已被隔离（无官方导入路径）

        背景:
        - _legacy_utils.py 被保留作为历史参考
        - 但 utils/__init__.py 中的适配器已删除
        - 源代码不应直接导入此文件

        断言:
        - _legacy_utils.py 可以存在（用户选择保留）
        - 但 utils/__init__.py 不应再导出 legacy 适配器
        """
        project_root = Path(__file__).parent.parent
        legacy_file = project_root / 'auto_tag' / '_legacy_utils.py'
        init_file = project_root / 'auto_tag' / 'utils' / '__init__.py'

        # 文件可以存在（保留历史参考）
        if legacy_file.exists():
            # 但必须确保 __init__.py 不再导入它
            init_content = init_file.read_text(encoding='utf-8')
            has_legacy_import = 'from auto_tag._legacy_utils' in init_content

            assert not has_legacy_import, (
                "❌ utils/__init__.py 仍导入 _legacy_utils\n"
                "虽然保留了 _legacy_utils.py 文件，但适配器应已删除"
            )

    def test_no_legacy_adapters_in_utils_init(self):
        """
        验证 utils/__init__.py 中无遗留适配器函数

        应删除的适配器:
        - _legacy_find_deepest_metadata_key() (原第359行)
        - _legacy_sanitize() (原第377行)
        - __all__ 中的导出 (原第414-415行)

        断言:
        - utils/__init__.py 不包含 _legacy_* 函数定义
        - __all__ 列表不包含 legacy 导出
        """
        project_root = Path(__file__).parent.parent
        init_file = project_root / 'auto_tag' / 'utils' / '__init__.py'

        if not init_file.exists():
            pytest.skip("utils/__init__.py 不存在")

        import pytest
        content = init_file.read_text(encoding='utf-8')

        # 检查是否还有 legacy 适配器函数定义
        has_legacy_adapter_def = bool(re.search(
            r'def _legacy_(find_deepest_metadata_key|sanitize)\s*\(',
            content
        ))

        # 检查 __all__ 是否还导出 legacy 函数
        has_legacy_export = bool(re.search(
            r"'_legacy_(find_deepest_metadata_key|sanitize)'",
            content
        ))

        assert not has_legacy_adapter_def, (
            "❌ utils/__init__.py 中仍存在 legacy 适配器函数\n"
            "请删除 _legacy_find_deepest_metadata_key() 和 _legacy_sanitize() 定义"
        )

        assert not has_legacy_export, (
            "❌ utils/__init__.py 的 __all__ 仍导出 legacy 函数\n"
            "请从 __all__ 列表移除 '_legacy_find_deepest_metadata_key' 和 '_legacy_sanitize'"
        )

    def test_no_legacy_imports_in_source_code(self):
        """
        静态分析：验证源代码中无任何 legacy 引用

        扫描范围:
        - auto_tag/ 目录下所有 .py 文件
        - 排除 __pycache__、.venv 等

        允许的例外:
        - 注释中的历史说明（如"比旧版更高效"）
        - 本测试文件的文档字符串

        违规示例:
            ❌ from auto_tag._legacy_utils import xxx
            ❌ from auto_tag.utils import _legacy_xxx
            ❌ import auto_tag._legacy_utils
        """
        project_root = Path(__file__).parent.parent
        violations = []

        for scan_dir in SCAN_DIRS:
            dir_path = project_root / scan_dir
            if not dir_path.exists():
                continue

            for py_file in dir_path.rglob('*.py'):
                # 跳过排除目录
                if any(exclude in py_file.parts for exclude in EXCLUDE_DIRS):
                    continue

                # 跳过本测试文件自身
                if py_file.name == 'test_legacy_import_restriction.py':
                    continue

                # 跳过 _legacy_utils.py（保留的历史参考文件）
                if py_file.name == '_legacy_utils.py':
                    continue

                # 读取文件内容并检测违规引用
                content = py_file.read_text(encoding='utf-8')

                # 查找非注释行的 legacy 引用
                for line_num, line in enumerate(content.split('\n'), 1):
                    # 跳过注释行和空行
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#'):
                        continue

                    if LEGACY_REFERENCE_PATTERN.search(line):
                        violations.append({
                            'file': str(py_file.relative_to(project_root)),
                            'line': line_num,
                            'content': stripped,
                        })

        assert not violations, self._format_violation_message(violations)

    def test_audio_recognize_refactored(self):
        """
        验证 audio_recognize.py 已完全使用新版 API

        检查项:
        - 无 _legacy_* 导入
        - 使用新版 is_file_in_use_error
        - 使用新版 sanitize (_safe_filename 函数内)
        - 使用自主实现的 _flatten_shazam_metadata
        """
        project_root = Path(__file__).parent.parent
        recognizer_file = project_root / 'auto_tag' / 'audio_recognize.py'

        if not recognizer_file.exists():
            pytest.skip("audio_recognize.py 不存在")

        import pytest
        content = recognizer_file.read_text(encoding='utf-8')

        # 检查是否有 legacy 导入（排除注释）
        code_lines = [
            line for line in content.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]
        code_content = '\n'.join(code_lines)

        has_legacy_import = bool(re.search(
            r'from\s+auto_tag\.(utils)?\._legacy_|import\s+.*_legacy_utils',
            code_content
        ))

        assert not has_legacy_import, (
            "❌ audio_recognize.py 仍包含 legacy 导入\n"
            "预期状态: 完全使用新版 API\n"
            "请检查导入部分和函数实现"
        )

        # 验证使用了新版 API
        assert 'from auto_tag.utils import (' in content, (
            "❌ 未发现从 auto_tag.utils 导入新版 API"
        )

        assert 'is_file_in_use_error' in content, (
            "❌ 未使用新版 is_file_in_use_error"
        )

    def _format_violation_message(self, violations):
        """
        格式化违规信息，提供清晰的修复指导

        Args:
            violations: 违规列表，每个元素包含 file, line, content

        Returns:
            str: 格式化的错误消息
        """
        msg = [
            "",
            "=" * 80,
            "❌ 发现遗留 legacy 代码引用（违反项目规范）",
            "=" * 80,
            "",
            "📋 违规详情:",
            "",
        ]

        for i, v in enumerate(violations, 1):
            msg.append(f"  {i}. 文件: {v['file']}")
            msg.append(f"     行号: {v['line']}")
            msg.append(f"     代码: {v['content']}")
            msg.append("")

        msg.extend([
            "🔧 修复方法:",
            "",
            "  1. 删除所有 _legacy_* 相关的导入语句",
            "  2. 替换为对应的新版 API:",
            "     - _legacy_find_deepest_metadata_key → 自主实现或新版",
            "     - _legacy_sanitize → auto_tag.utils.sanitize",
            "     - _legacy_utils 直接导入 → 完全移除",
            "",
            "📖 历史背景:",
            "    - 2026-05-02: audio_recognize.py 重构完成",
            "    - Legacy 代码已全部清理",
            "    - 不应再有任何 legacy 引用",
            "",
            f"⚠️  共发现 {len(violations)} 处违规",
            "=" * 80,
            "",
        ])

        return '\n'.join(msg)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
