#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RateLimiter 核心逻辑快速验证
"""

import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("开始验证 RateLimiter 实现...")

    # 测试 1: 验证文件存在且可导入
    print("\n[1/5] 验证模块可导入...")
    try:
        from auto_tag.lyric.rate_limiter import RateLimiter, RequestMetrics, get_rate_limiter
        print("  ✓ 模块导入成功")
    except Exception as e:
        print(f"  ✗ 导入失败: {e}")
        return False

    # 测试 2: 验证 RequestMetrics 基础功能
    print("\n[2/5] 验证 RequestMetrics...")
    try:
        metrics = RequestMetrics()
        metrics.record_request(success=True, response_time=0.5)
        metrics.record_request(success=False, response_time=0.2, retry_count=1)
        stats = metrics.get_statistics()

        assert stats['total_requests'] == 2
        assert abs(stats['success_rate'] - 0.5) < 0.01
        assert stats['failed_requests'] == 1
        assert stats['retry_count'] == 1
        print("  ✓ 指标记录和统计正常")
    except Exception as e:
        print(f"  ✗ Metrics 测试失败: {e}")
        return False

    # 测试 3: 验证 RateLimiter 突发控制
    print("\n[3/5] 验证 RateLimiter 突发请求...")
    try:
        RateLimiter.reset_instance()
        limiter = RateLimiter(min_interval=0.1, burst_size=3)

        r1 = limiter.try_acquire()
        r2 = limiter.try_acquire()
        r3 = limiter.try_acquire()
        r4 = limiter.try_acquire()

        assert r1 and r2 and r3, "前3次应成功"
        assert not r4, "第4次应失败（令牌耗尽）"
        print("  ✓ 突发请求控制正常")
    except Exception as e:
        print(f"  ✗ 突发控制测试失败: {e}")
        return False

    # 测试 4: 验证单例模式
    print("\n[4/5] 验证单例模式...")
    try:
        RateLimiter.reset_instance()
        i1 = RateLimiter.get_instance()
        i2 = RateLimiter.get_instance()
        assert i1 is i2, "应该是同一实例"
        print("  ✓ 单例模式正常")
    except Exception as e:
        print(f"  ✗ 单例模式测试失败: {e}")
        return False

    # 测试 5: 验证令牌补充
    print("\n[5/5] 验证令牌自动补充...")
    try:
        import time
        RateLimiter.reset_instance()
        limiter = RateLimiter(min_interval=0.1, burst_size=2)

        for _ in range(2):
            limiter.try_acquire()

        tokens_before = limiter.available_tokens
        assert tokens_before <= 0.1, f"令牌应接近耗尽: {tokens_before:.2f}"

        time.sleep(0.25)
        tokens_after = limiter.available_tokens
        assert tokens_after >= 1.0, f"补充后应有≥1个令牌: {tokens_after:.2f}"

        print(f"  ✓ 令牌补充正常 ({tokens_before:.2f} → {tokens_after:.2f})")
    except Exception as e:
        print(f"  ✗ 令牌补充测试失败: {e}")
        return False

    return True


if __name__ == '__main__':
    success = main()
    if success:
        print("\n" + "=" * 50)
        print("🎉 所有验证通过！RateLimiter 实现正确 ✓")
        print("=" * 50)
        sys.exit(0)
    else:
        print("\n❌ 验证失败")
        sys.exit(1)
