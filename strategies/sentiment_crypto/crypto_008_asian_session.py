"""
CRYPTO_008: Asian Session Strategy
----------------------------------
Trade based on Asian session patterns (UTC 00:00-08:00).

Entry Long: Asian session breakout up
Entry Short: Asian session breakout down

Optimal Timeframes: 15m, 1h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from datetime import datetime
from typing import List, Dict


class AsianSession(Strategy):
    """Asian Session Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_008"
        self.strategy_name = "Asian Session"
        self.complexity = 5
        self.crypto_suitability = 8
        self.asian_high = None
        self.asian_low = None

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'session_start', 'type': int, 'min': 0, 'max': 2, 'default': 0},
            {'name': 'session_end', 'type': int, 'min': 7, 'max': 9, 'default': 8},
            {'name': 'breakout_buffer', 'type': float, 'min': 0.1, 'max': 0.5, 'default': 0.2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _get_hour(self) -> int:
        """Get current hour in UTC"""
        timestamp = self.candles[-1, 0] / 1000
        dt = datetime.utcfromtimestamp(timestamp)
        return dt.hour

    def _is_asian_session(self) -> bool:
        """Check if in Asian session"""
        hour = self._get_hour()
        return self.hp['session_start'] <= hour < self.hp['session_end']

    def _calculate_asian_range(self):
        """Calculate Asian session high/low"""
        session_start = self.hp['session_start']
        session_end = self.hp['session_end']

        highs = []
        lows = []

        for i in range(1, min(50, len(self.candles))):
            ts = self.candles[-i, 0] / 1000
            dt = datetime.utcfromtimestamp(ts)
            if session_start <= dt.hour < session_end:
                highs.append(self.candles[-i, 3])
                lows.append(self.candles[-i, 4])
            elif highs:  # Exited session
                break

        if highs and lows:
            self.asian_high = max(highs)
            self.asian_low = min(lows)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # After Asian session ends, breakout above range
        if self._is_asian_session():
            self._calculate_asian_range()
            return False

        if self.asian_high is None:
            return False

        buffer = self.atr * self.hp['breakout_buffer']
        return self.close > self.asian_high + buffer

    def should_short(self) -> bool:
        # After Asian session ends, breakout below range
        if self._is_asian_session():
            return False

        if self.asian_low is None:
            return False

        buffer = self.atr * self.hp['breakout_buffer']
        return self.close < self.asian_low - buffer

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Reset range at start of new Asian session
        if self._is_asian_session():
            self.liquidate()
            self.asian_high = None
            self.asian_low = None
