"""
Parser Registry & Circuit Breaker Module

Manages 15 Malaysian bank parsers with per-bank circuit breaker protection.
"""
from .registry import (
    BANK_CODES,
    BANK_ALIASES,
    BANK_METADATA,
    detect_bank_code,
    get_supported_banks,
    is_bank_enabled
)
from .circuit_breaker import (
    BankCircuitBreaker,
    get_circuit_breaker,
    record_parse_result,
    is_bank_available
)

__all__ = [
    "BANK_CODES",
    "BANK_ALIASES",
    "BANK_METADATA",
    "detect_bank_code",
    "get_supported_banks",
    "is_bank_enabled",
    "BankCircuitBreaker",
    "get_circuit_breaker",
    "record_parse_result",
    "is_bank_available"
]
