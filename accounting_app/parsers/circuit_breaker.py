"""
Single-Bank Circuit Breaker

Per-bank error tracking with automatic circuit breaking to prevent cascading failures.
"""
import os
import time
from collections import deque, defaultdict
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta


class BankCircuitBreaker:
    """
    单银行熔断器
    
    Features:
    - 10-minute sliding window error tracking
    - Configurable error rate threshold
    - Automatic cooldown and recovery
    - Per-bank isolation (one bank fails, others continue)
    """
    
    def __init__(
        self,
        error_rate_threshold: float = 0.15,
        consecutive_threshold: int = 5,
        cooldown_minutes: int = 60,
        window_minutes: int = 10
    ):
        """
        Args:
            error_rate_threshold: 错误率阈值（0.15 = 15%）
            consecutive_threshold: 连续错误次数阈值
            cooldown_minutes: 熔断冷却时间（分钟）
            window_minutes: 滑动窗口时间（分钟）
        """
        self.error_rate_threshold = error_rate_threshold
        self.consecutive_threshold = consecutive_threshold
        self.cooldown_seconds = cooldown_minutes * 60
        self.window_seconds = window_minutes * 60
        
        # 每银行数据结构
        self.results: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.consecutive_errors: Dict[str, int] = defaultdict(int)
        self.circuit_open_time: Dict[str, Optional[float]] = defaultdict(lambda: None)
        self.last_success_time: Dict[str, Optional[float]] = defaultdict(lambda: None)
    
    def record_result(self, bank_code: str, success: bool) -> None:
        """
        记录单次解析结果
        
        Args:
            bank_code: 银行代码
            success: 解析是否成功
        """
        timestamp = time.time()
        self.results[bank_code].append((timestamp, success))
        
        if success:
            self.consecutive_errors[bank_code] = 0
            self.last_success_time[bank_code] = timestamp
        else:
            self.consecutive_errors[bank_code] += 1
        
        self._check_circuit(bank_code)
    
    def _check_circuit(self, bank_code: str) -> None:
        """检查是否需要打开熔断器"""
        if self.is_circuit_open(bank_code):
            return
        
        # 连续错误检查
        if self.consecutive_errors[bank_code] >= self.consecutive_threshold:
            self._open_circuit(bank_code, reason="consecutive_errors")
            return
        
        # 错误率检查（10分钟窗口）
        error_rate = self._calculate_error_rate(bank_code)
        if error_rate is not None and error_rate > self.error_rate_threshold:
            self._open_circuit(bank_code, reason="high_error_rate")
    
    def _calculate_error_rate(self, bank_code: str) -> Optional[float]:
        """计算10分钟窗口内错误率"""
        now = time.time()
        cutoff = now - self.window_seconds
        
        recent_results = [(ts, success) for ts, success in self.results[bank_code] if ts >= cutoff]
        
        if len(recent_results) < 3:
            return None
        
        errors = sum(1 for _, success in recent_results if not success)
        return errors / len(recent_results)
    
    def _open_circuit(self, bank_code: str, reason: str) -> None:
        """打开熔断器"""
        self.circuit_open_time[bank_code] = time.time()
        print(f"⚡ 熔断器触发: {bank_code} - 原因: {reason} - 冷却时间: {self.cooldown_seconds // 60}分钟")
    
    def is_circuit_open(self, bank_code: str) -> bool:
        """检查熔断器是否打开（bank不可用）"""
        open_time = self.circuit_open_time[bank_code]
        if open_time is None:
            return False
        
        # 检查是否冷却完成
        if time.time() - open_time >= self.cooldown_seconds:
            self._try_recovery(bank_code)
            return False
        
        return True
    
    def _try_recovery(self, bank_code: str) -> None:
        """尝试恢复（冷却完成后）"""
        print(f"🔄 熔断器尝试恢复: {bank_code}")
        self.circuit_open_time[bank_code] = None
        self.consecutive_errors[bank_code] = 0
    
    def is_bank_available(self, bank_code: str) -> Tuple[bool, Optional[str]]:
        """
        检查银行是否可用
        
        Returns:
            (is_available, reason_if_unavailable)
        """
        if self.is_circuit_open(bank_code):
            open_time = self.circuit_open_time[bank_code]
            remaining = int((open_time + self.cooldown_seconds - time.time()) / 60)
            return False, f"该银行解析暂时不可用，请{remaining}分钟后重试或使用CSV导入。"
        
        return True, None
    
    def get_bank_stats(self, bank_code: str) -> Dict:
        """获取银行统计信息（用于监控看板）"""
        now = time.time()
        cutoff = now - self.window_seconds
        
        recent_results = [(ts, success) for ts, success in self.results[bank_code] if ts >= cutoff]
        
        total = len(recent_results)
        if total == 0:
            return {
                "bank_code": bank_code,
                "total_requests": 0,
                "success_rate": None,
                "error_rate": None,
                "consecutive_errors": self.consecutive_errors[bank_code],
                "circuit_open": self.is_circuit_open(bank_code),
                "last_success": self.last_success_time[bank_code]
            }
        
        successes = sum(1 for _, s in recent_results if s)
        errors = total - successes
        
        return {
            "bank_code": bank_code,
            "total_requests": total,
            "success_rate": successes / total if total > 0 else 0,
            "error_rate": errors / total if total > 0 else 0,
            "consecutive_errors": self.consecutive_errors[bank_code],
            "circuit_open": self.is_circuit_open(bank_code),
            "last_success": self.last_success_time[bank_code]
        }


# Global circuit breaker instance (singleton)
_circuit_breaker: Optional[BankCircuitBreaker] = None


def get_circuit_breaker() -> BankCircuitBreaker:
    """获取全局熔断器实例（单例模式）"""
    global _circuit_breaker
    
    if _circuit_breaker is None:
        error_rate = float(os.getenv("PARSER_CIRCUIT_ERROR_RATE", "0.15"))
        consecutive = int(os.getenv("PARSER_CIRCUIT_CONSECUTIVE", "5"))
        cooldown = int(os.getenv("PARSER_CIRCUIT_COOLDOWN_MIN", "60"))
        
        _circuit_breaker = BankCircuitBreaker(
            error_rate_threshold=error_rate,
            consecutive_threshold=consecutive,
            cooldown_minutes=cooldown
        )
    
    return _circuit_breaker


def record_parse_result(bank_code: str, success: bool) -> None:
    """
    记录解析结果（便捷函数）
    
    Args:
        bank_code: 银行代码
        success: 解析是否成功
    """
    cb = get_circuit_breaker()
    cb.record_result(bank_code, success)


def is_bank_available(bank_code: str) -> Tuple[bool, Optional[str]]:
    """
    检查银行是否可用（便捷函数）
    
    Returns:
        (is_available, reason_if_unavailable)
    """
    cb = get_circuit_breaker()
    return cb.is_bank_available(bank_code)
