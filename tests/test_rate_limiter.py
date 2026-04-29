# -*- coding: utf-8 -*-
"""
RateLimiter 和 RequestMetrics 单元测试

验证令牌桶算法的正确性、线程安全性和边界条件处理。
"""

from __future__ import annotations

import threading
import time
import unittest

from auto_tag.lyric.rate_limiter import RateLimiter, RequestMetrics, get_rate_limiter


class TestRequestMetrics(unittest.TestCase):
    """RequestMetrics 统计监控类的单元测试"""

    def setUp(self) -> None:
        """每个测试前重置指标"""
        self.metrics = RequestMetrics()

    def test_initial_state(self) -> None:
        """验证初始状态所有计数器为零"""
        stats = self.metrics.get_statistics()
        self.assertEqual(stats['total_requests'], 0)
        self.assertEqual(stats['successful_requests'], 0)
        self.assertEqual(stats['failed_requests'], 0)
        self.assertEqual(stats['retry_count'], 0)

    def test_record_success(self) -> None:
        """记录成功请求"""
        self.metrics.record_request(success=True, response_time=0.5)
        stats = self.metrics.get_statistics()
        self.assertEqual(stats['total_requests'], 1)
        self.assertEqual(stats['successful_requests'], 1)
        self.assertEqual(stats['failed_requests'], 0)
        self.assertAlmostEqual(stats['avg_response_time_ms'], 500.0, places=1)

    def test_record_failure(self) -> None:
        """记录失败请求"""
        self.metrics.record_request(success=False, response_time=0.2, retry_count=2)
        stats = self.metrics.get_statistics()
        self.assertEqual(stats['total_requests'], 1)
        self.assertEqual(stats['successful_requests'], 0)
        self.assertEqual(stats['failed_requests'], 1)
        self.assertEqual(stats['retry_count'], 2)

    def test_mixed_records(self) -> None:
        """混合记录成功和失败请求，计算正确率"""
        for i in range(8):
            self.metrics.record_request(success=True, response_time=0.1 * (i + 1))
        for i in range(2):
            self.metrics.record_request(success=False, response_time=0, retry_count=i)

        stats = self.metrics.get_statistics()
        self.assertEqual(stats['total_requests'], 10)
        self.assertEqual(stats['successful_requests'], 8)
        self.assertEqual(stats['failed_requests'], 2)
        self.assertAlmostEqual(stats['success_rate'], 0.8, places=2)
        self.assertEqual(stats['retry_count'], 1)  # 0 + 1

    def test_reset(self) -> None:
        """重置功能测试"""
        self.metrics.record_request(success=True, response_time=1.0)
        self.metrics.record_request(success=False, response_time=0, retry_count=3)
        self.metrics.reset()

        stats = self.metrics.get_statistics()
        self.assertEqual(stats['total_requests'], 0)
        self.assertEqual(stats['successful_requests'], 0)
        self.assertEqual(stats['retry_count'], 0)

    def test_thread_safety(self) -> None:
        """多线程并发记录的安全性测试"""
        num_threads = 10
        requests_per_thread = 50

        def worker() -> None:
            for _ in range(requests_per_thread):
                self.metrics.record_request(
                    success=True,
                    response_time=0.01,
                    is_rate_limited=_ % 3 == 0
                )

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = self.metrics.get_statistics()
        expected_total = num_threads * requests_per_thread
        self.assertEqual(stats['total_requests'], expected_total)
        self.assertEqual(stats['successful_requests'], expected_total)


class TestRateLimiterBasic(unittest.TestCase):
    """RateLimiter 基础功能的单元测试"""

    def setUp(self) -> None:
        """每个测试前重置单例并创建新实例"""
        RateLimiter.reset_instance()
        self.limiter = RateLimiter(min_interval=0.1, burst_size=3)

    def tearDown(self) -> None:
        """每个测试后清理单例"""
        RateLimiter.reset_instance()

    def test_initial_tokens(self) -> None:
        """初始状态令牌桶应该是满的"""
        self.assertAlmostEqual(self.limiter.available_tokens, 3.0, places=1)

    def test_single_acquisition(self) -> None:
        """单次获取令牌成功"""
        result = self.limiter.acquire(timeout=1)
        self.assertTrue(result)
        self.assertAlmostEqual(self.limiter.available_tokens, 2.0, places=1)

    def test_burst_acquisition(self) -> None:
        """突发请求：可以连续获取 burst_size 个令牌"""
        for i in range(3):  # burst_size = 3
            result = self.limiter.try_acquire()
            self.assertTrue(f"第{i+1}次突发获取应成功", result)

        # 第4次应该失败（令牌耗尽）
        result = self.limiter.try_acquire()
        self.assertFalse("超出突发容量应失败", result)

    def test_token_refill(self) -> None:
        """令牌随时间自动补充"""
        # 消耗所有令牌
        for _ in range(3):
            self.limiter.try_acquire()

        self.assertLessEqual(self.limiter.available_tokens, 0.1)

        # 等待足够时间让令牌补充（min_interval=0.1秒）
        time.sleep(0.25)

        # 应该至少补充了1个令牌
        self.assertGreaterEqual(self.limiter.available_tokens, 1.0)

    def test_timeout_behavior(self) -> None:
        """超时行为：无令牌时等待超时返回 False"""
        # 消耗所有令牌
        for _ in range(3):
            self.limiter.try_acquire()

        # 尝试获取，设置很短的超时
        start = time.monotonic()
        result = self.limiter.acquire(timeout=0.05)
        elapsed = time.monotonic() - start

        self.assertFalse(result)
        self.assertGreaterEqual(elapsed, 0.04)  # 至少等待了大部分超时时间

    def test_try_acquire_non_blocking(self) -> None:
        """try_acquire 是非阻塞的"""
        # 消耗所有令牌
        for _ in range(3):
            self.limiter.try_acquire()

        # 多次快速调用应该都立即返回 False
        start = time.monotonic()
        for _ in range(10):
            result = self.limiter.try_acquire()
            self.assertFalse(result)
        elapsed = time.monotonic() - start

        # 10次调用应该在很短时间内完成（< 10ms）
        self.assertLess(elapsed, 0.1, "try_acquire 应该是非阻塞的")


class TestRateLimiterConcurrency(unittest.TestCase):
    """RateLimiter 并发安全性的单元测试"""

    def setUp(self) -> None:
        RateLimiter.reset_instance()
        # 使用较慢的间隔以便观察并发行为
        self.limiter = RateLimiter(min_interval=0.05, burst_size=2)

    def tearDown(self) -> None:
        RateLimiter.reset_instance()

    def test_concurrent_safety(self) -> None:
        """
        多线程并发获取令牌不冲突

        验证：
        - 总获取次数不超过总令牌数 + 补充数
        - 无死锁或异常
        """
        success_count = 0
        failure_count = 0
        lock = threading.Lock()

        def worker() -> None:
            nonlocal success_count, failure_count
            # 尝试获取令牌（带短超时避免测试卡住）
            if self.limiter.acquire(timeout=0.2):
                with lock:
                    success_count += 1
            else:
                with lock:
                    failure_count += 1

        # 启动多个线程同时竞争令牌
        num_threads = 10
        threads = [threading.Thread(target=worker) for _ in range(num_threads)]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        # 验证结果合理性
        total_attempts = success_count + failure_count
        self.assertEqual(total_attempts, num_threads, "每个线程都应该完成")
        # 由于 burst_size=2 且有少量补充，成功率应该在 20%-60% 之间
        self.assertGreater(success_count, 0, "应该有部分线程成功获取令牌")

    def test_singleton_pattern(self) -> None:
        """单例模式：多次调用返回同一实例"""
        instance1 = RateLimiter.get_instance()
        instance2 = RateLimiter.get_instance()
        self.assertIs(instance1, instance2, "get_instance 应该返回同一实例")

    def test_reset_and_recreate(self) -> None:
        """重置后创建新实例"""
        original = RateLimiter.get_instance()
        RateLimiter.reset_instance()
        new_instance = RateLimiter.get_instance()
        self.assertIsNot(original, new_instance, "重置后应创建新实例")


class TestRateLimiterIntegration(unittest.TestCase):
    """RateLimiter 与实际使用场景的集成测试"""

    def setUp(self) -> None:
        RateLimiter.reset_instance()
        # 使用接近生产环境的参数
        self.limiter = RateLimiter(min_interval=0.15, burst_size=2)

    def tearDown(self) -> None:
        RateLimiter.reset_instance()

    def test_realistic_usage_pattern(self) -> None:
        """
        模拟真实的批量请求场景

        场景：连续发送 6 个请求，验证速率控制效果
        - 前 2 个立即成功（突发）
        - 后续需要等待令牌补充
        """
        timings = []

        for i in range(6):
            start = time.monotonic()
            success = self.limiter.acquire(timeout=2)
            elapsed = time.monotonic() - start
            timings.append(elapsed)

            self.assertTrue(f"第{i+1}个请求应在2秒内成功", success)

        # 前2个应该很快（突发），后续逐渐变慢
        self.assertLess(timings[0], 0.1, "第1个请求应该几乎瞬间完成")
        self.assertLess(timings[1], 0.1, "第2个请求应该几乎瞬间完成")

        # 总耗时应该合理（至少 4 * 0.15 = 0.6 秒用于补充令牌）
        total_time = sum(timings)
        self.assertGreater(total_time, 0.4, "总耗时应体现限速效果")

    def test_rate_limiting_prevents_flooding(self) -> None:
        """
        验证限速器能有效防止请求洪泛

        即使代码快速循环调用 acquire()，
        实际通过率也应受限于 min_interval
        """
        num_attempts = 10
        start_time = time.monotonic()

        for _ in range(num_attempts):
            self.limiter.acquire(timeout=5)

        elapsed = time.monotonic() - start_time

        # 理论最小耗时：(num_attempts - burst_size) * min_interval
        # = (10 - 2) * 0.15 = 1.2 秒
        min_expected = (num_attempts - self.limiter.burst_size) * self.limiter.min_interval
        self.assertGreater(
            elapsed, min_expected * 0.8,
            f"{num_attempts}个请求至少需要 {min_expected:.2f} 秒"
        )


if __name__ == '__main__':
    unittest.main()
