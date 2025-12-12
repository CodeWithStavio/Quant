"""
Base Output Handler
===================
Abstract base class for all signal output handlers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from signals.signal import Signal, SignalType


class BaseOutput(ABC):
    """
    Abstract base class for signal output handlers.

    All output handlers must implement:
    - send(): Send a single signal
    - send_batch(): Send multiple signals
    - close(): Cleanup resources
    """

    def __init__(self, name: str, enabled: bool = True):
        """
        Initialize output handler.

        Args:
            name: Handler identifier
            enabled: Whether this handler is active
        """
        self.name = name
        self.enabled = enabled
        self._filter_types: Optional[List[SignalType]] = None
        self._filter_strategies: Optional[List[str]] = None
        self._filter_symbols: Optional[List[str]] = None
        self._min_confidence: int = 0

    def set_type_filter(self, signal_types: List[SignalType]) -> 'BaseOutput':
        """Filter signals by type"""
        self._filter_types = signal_types
        return self

    def set_strategy_filter(self, strategy_ids: List[str]) -> 'BaseOutput':
        """Filter signals by strategy ID"""
        self._filter_strategies = strategy_ids
        return self

    def set_symbol_filter(self, symbols: List[str]) -> 'BaseOutput':
        """Filter signals by trading symbol"""
        self._filter_symbols = symbols
        return self

    def set_min_confidence(self, min_confidence: int) -> 'BaseOutput':
        """Filter signals by minimum confidence score"""
        self._min_confidence = min_confidence
        return self

    def should_send(self, signal: Signal) -> bool:
        """Check if signal passes all filters"""
        if not self.enabled:
            return False

        if self._filter_types and signal.signal_type not in self._filter_types:
            return False

        if self._filter_strategies and signal.strategy_id not in self._filter_strategies:
            return False

        if self._filter_symbols and signal.symbol not in self._filter_symbols:
            return False

        if signal.confidence < self._min_confidence:
            return False

        return True

    @abstractmethod
    def send(self, signal: Signal) -> bool:
        """
        Send a single signal.

        Args:
            signal: Signal to send

        Returns:
            True if sent successfully, False otherwise
        """
        pass

    def send_batch(self, signals: List[Signal]) -> int:
        """
        Send multiple signals.

        Args:
            signals: List of signals to send

        Returns:
            Number of successfully sent signals
        """
        sent = 0
        for signal in signals:
            if self.send(signal):
                sent += 1
        return sent

    def close(self) -> None:
        """Cleanup resources (override if needed)"""
        pass

    def __enter__(self) -> 'BaseOutput':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
