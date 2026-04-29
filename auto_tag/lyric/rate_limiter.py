# auto_tag/lyric/rate_limiter.py
"""
请求限速器和监控指标模块

提供令牌桶算法实现的频率限制功能和请求统计监控功能，
用于控制歌词 API 的请求频率，避免触发服务器限流。
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class RequestMetrics:
    """
    请求统计监控数据类

    记录所有 API 请求的关键指标，用于诊断性能问题和优化策略。

    Attributes:
        total_requests: 总请求数（含重试）
        successful_requests: 成功完成的请求数
        failed_requests: 失败的请求数
        retry_count: 总重试次数
        total_response_time: 累计响应时间（秒），用于计算平均值
        rate_limited_count: 被限流等待的次数
        last_request_time: 最后一次请求的时间戳（time.monotonic()）
        last_request_success: 最后一次请求是否成功

    Example:
        >>> metrics = RequestMetrics()
        >>> metrics.record_request(success=True, response_time=0.5)
        >>> stats = metrics.get_statistics()
        >>> print(f"成功率: {stats['success_rate']:.1%}")
    """

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    retry_count: int = 0
    total_response_time: float = 0.0
    rate_limited_count: int = 0
    last_request_time: float = 0.0
    last_request_success: bool = True
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record_request(
        self,
        success: bool,
        response_time: float,
        retry_count: int = 0,
        is_rate_limited: bool = False
    ) -> None:
        """
        记录一次请求的结果

        Args:
            success: 请求是否成功完成
            response_time: 响应时间（秒）
            retry_count: 本次请求的重试次数（0表示首次成功）
            is_rate_limited: 是否触发了限流等待
        """
        with self._lock:
            self.total_requests += 1
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            self.retry_count += retry_count
            self.total_response_time += response_time
            if is_rate_limited:
                self.rate_limited_count += 1
            self.last_request_time = time.monotonic()
            self.last_request_success = success

    def get_statistics(self) -> dict[str, Any]:
        """
        获取当前统计信息的格式化字典

        Returns:
            dict: 包含各项统计指标的字典，可直接用于日志输出或UI展示

        Example:
            >>> metrics.get_statistics()
            {
                'total_requests': 100,
                'success_rate': 0.95,
                'avg_response_time_ms': 234.5,
                ...
            }
        """
        with self._lock:
            total = max(self.total_requests, 1)  # 避免除零
            return {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': self.successful_requests / total,
                'failure_rate': self.failed_requests / total,
                'retry_count': self.retry_count,
                'avg_retry_per_request': self.retry_count / total,
                'avg_response_time_ms': (self.total_response_time / total) * 1000 if total > 0 else 0,
                'rate_limited_count': self.rate_limited_count,
                'rate_limited_rate': self.rate_limited_count / total,
                'last_request_time': self.last_request_time,
                'last_request_success': self.last_request_success
            }

    def reset(self) -> None:
        """重置所有计数器为零"""
        with self._lock:
            self.total_requests = 0
            self.successful_requests = 0
            self.failed_requests = 0
            self.retry_count = 0
            self.total_response_time = 0.0
            self.rate_limited_count = 0
            self.last_request_time = 0.0
            self.last_request_success = True


class RateLimiter:
    """
    令牌桶算法实现的请求限速器

    使用令牌桶（Token Bucket）算法控制 API 请求频率，
    允许短暂的突发请求，但长期平均速率不超过设定值。

    特性：
    - 单例模式：全局共享一个实例，避免多实例冲突
    - 线程安全：使用 threading.Lock 保护并发访问
    - 可配置参数：支持自定义请求间隔和突发容量
    - 非阻塞查询：try_acquire() 方法支持立即返回

    Args:
        min_interval: 最小请求间隔（秒），决定长期平均速率（默认1.5秒/次）
        burst_size: 令牌桶容量，允许的最大突发请求数（默认3）

    Example:
        >>> limiter = RateLimiter(min_interval=1.5, burst_size=3)
        >>> # 阻塞式获取许可（推荐）
        >>> if limiter.acquire():
        ...     make_api_request()
        >>>
        >>> # 带超时的获取
        >>> if limiter.acquire(timeout=10):
        ...     make_api_request()
        ... else:
        ...     print("等待超时")
        >>>
        >>> # 非阻塞尝试
        >>> if limiter.try_acquire():
        ...     make_api_request()
        ... else:
        ...     print("限速中，稍后重试")
    """

    _instance: Optional[RateLimiter] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        min_interval: float = 1.5,
        burst_size: int = 3
    ) -> None:
        """
        初始化令牌桶参数

        Args:
            min_interval: 最小请求间隔（秒），即两次请求之间的最小时间差
                         设为 1.5 表示平均每秒最多 0.67 次请求（安全值）
            burst_size: 令牌桶容量，允许的最大突发请求数
                        设为 3 表示可以立即连续发送 3 个请求
        """
        self._min_interval = min_interval
        self._burst_size = burst_size
        self._tokens: float = float(burst_size)  # 初始填满令牌桶
        self._last_refill_time: float = time.monotonic()
        self._mutex = threading.Lock()
        self.logger = logging.getLogger(__name__)

    @classmethod
    def get_instance(cls, **kwargs) -> RateLimiter:
        """
        单例工厂方法，获取全局唯一的 RateLimiter 实例

        使用双重检查锁定模式确保线程安全的单例初始化。

        Args:
            **kwargs: 传递给 __init__ 的参数（仅在首次创建时生效）

        Returns:
            RateLimiter: 全局单例实例

        Example:
            >>> limiter1 = RateLimiter.get_instance(min_interval=2.0)
            >>> limiter2 = RateLimiter.get_instance()  # 返回同一实例
            >>> assert limiter1 is limiter2
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(**kwargs)
                    logging.getLogger(__name__).info(
                        f"[RateLimiter] 创建全局单例 "
                        f"(interval={kwargs.get('min_interval', 1.5)}s, "
                        f"burst={kwargs.get('burst_size', 3)})"
                    )
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """
        重置单例实例（主要用于测试）

        Warning:
            仅在测试环境中使用，生产代码不应调用此方法
        """
        with cls._lock:
            cls._instance = None

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        阻塞式获取一个令牌（请求许可）

        如果令牌桶中有可用令牌，立即消耗一个并返回 True；
        否则阻塞当前线程直到有令牌可用或超时。

        Args:
            timeout: 最大等待时间（秒）
                     - None（默认）：无限等待，直到获取到令牌
                     - 0：非阻塞，等同于 try_acquire()
                     - 正数：最多等待指定秒数

        Returns:
            bool: 是否成功获取到令牌
                  - True: 成功获取，可以发送请求
                  - False: 超时未获取到，不应发送请求

        Example:
            >>> # 无限等待（推荐用于后台批量任务）
            >>> limiter.acquire()  # 阻塞直到可用
            >>>
            >>> # 带超时（推荐用于 UI 触发的请求）
            >>> if not limiter.acquire(timeout=30):
            ...     raise TimeoutError("等待请求许可超时")
        """
        start_time = time.monotonic()
        sleep_interval = 0.05  # 轮询间隔（50ms）

        while True:
            with self._mutex:
                self._refill_tokens()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    self.logger.debug(
                        f"[RateLimiter] 获取令牌成功 "
                        f"(剩余令牌: {self._tokens:.1f}/{self._burst_size})"
                    )
                    return True

            # 检查是否超时
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed >= timeout:
                    self.logger.warning(
                        f"[RateLimiter] 获取令牌超时 "
                        f"(timeout={timeout}s, 已等待={elapsed:.1f}s)"
                    )
                    return False
                # 动态调整睡眠时间，避免忙等待
                remaining = timeout - elapsed
                time.sleep(min(sleep_interval, remaining))
            else:
                time.sleep(sleep_interval)

    def try_acquire(self) -> bool:
        """
        非阻塞式尝试获取一个令牌

        立即返回结果，不等待令牌补充。适用于需要快速判断的场景。

        Returns:
            bool: 是否立即获取成功
                  - True: 令牌桶中有可用令牌，已消耗一个
                  - False: 令牌桶为空，未消耗任何令牌

        Example:
            >>> if limiter.try_acquire():
            ...     make_api_request()
            ... else:
            ...     schedule_retry(make_api_request)
        """
        with self._mutex:
            self._refill_tokens()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                self.logger.debug(
                    f"[RateLimiter] 非阻塞获取成功 "
                    f"(剩余令牌: {self._tokens:.1f}/{self._burst_size})"
                )
                return True
            else:
                self.logger.debug(
                    f"[RateLimiter] 非阻塞获取失败 "
                    f"(令牌不足: {self._tokens:.1f}/{self._burst_size})"
                )
                return False

    def _refill_tokens(self) -> None:
        """
        根据经过的时间补充令牌

        令牌补充速率由 min_interval 决定：
        - 每 min_interval 秒补充 1 个令牌
        - 总量不超过 burst_size（桶容量）

        Note:
            此方法必须在持有 self._mutex 锁的情况下调用
        """
        now = time.monotonic()
        elapsed = now - self._last_refill_time

        if elapsed > 0:
            # 计算应该补充的令牌数（可能有小数部分）
            tokens_to_add = elapsed / self._min_interval
            # 补充令牌，但不能超过桶容量
            self._tokens = min(self._burst_size, self._tokens + tokens_to_add)
            # 更新最后补充时间
            self._last_refill_time = now

    @property
    def available_tokens(self) -> float:
        """
        获取当前可用的令牌数量（只读属性）

        Returns:
            float: 当前令牌桶中的令牌数（0 到 burst_size 之间）

        Example:
            >>> print(f"当前可用令牌: {limiter.available_tokens:.1f}")
        """
        with self._mutex:
            self._refill_tokens()
            return self._tokens

    @property
    def min_interval(self) -> float:
        """获取最小请求间隔配置"""
        return self._min_interval

    @property
    def burst_size(self) -> int:
        """获取突发容量配置"""
        return self._burst_size


def get_rate_limiter(**kwargs) -> RateLimiter:
    """
    获取全局 RateLimiter 单例实例的便捷函数

    这是推荐的获取方式，封装了 RateLimiter.get_instance() 调用。

    Args:
        **kwargs: 传递给 RateLimiter.__init__ 的参数（仅首次生效）

    Returns:
        RateLimiter: 全局单例实例

    Example:
        >>> from auto_tag.lyric.rate_limiter import get_rate_limiter
        >>> limiter = get_rate_limiter(min_interval=2.0)
        >>> limiter.acquire()
    """
    return RateLimiter.get_instance(**kwargs)
