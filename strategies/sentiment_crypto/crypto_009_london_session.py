"""
CRYPTO_009: London Session Strategy
------------------------------------
Trade based on London session patterns (UTC 07:00-16:00).

Entry Long: London session breakout up with volume
Entry Short: London session breakout down with volume

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


class LondonSession(Strategy):
    """London Session Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_009"
        self.strategy_name = "London Session"
        self.complexity = 5
        self.crypto_suitability = 8
        self.pre_london_high = None
        self.pre_london_low = None

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'session_start', 'type': int, 'min': 7, 'max': 9, 'default': 8},
            {'name': 'session_end', 'type': int, 'min': 15, 'max': 17, 'default': 16},
            {'name': 'breakout_buffer', 'type': float, 'min': 0.1, 'max': 0.5, 'default': 0.2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _get_hour(self) -> int:
        """Get current hour in UTC"""
        timestamp = self.candles[-1, 0] / 1000
        dt = datetime.utcfromtimestamp(timestamp)
        return dt.hour

    def _is_london_session(self) -> bool:
        """Check if in London session"""
        hour = self._get_hour()
        return self.hp['session_start'] <= hour < self.hp['session_end']

    def _is_early_london(self) -> bool:
        """Check if in first 2 hours of London session"""
        hour = self._get_hour()
        return self.hp['session_start'] <= hour < self.hp['session_start'] + 2

    def _calculate_pre_london_range(self):
        """Calculate pre-London (Asian) range"""
        session_start = self.hp['session_start']

        highs = []
        lows = []

        for i in range(1, min(50, len(self.candles))):
            ts = self.candles[-i, 0] / 1000
            dt = datetime.utcfromtimestamp(ts)
            if 0 <= dt.hour < session_start:
                highs.append(self.candles[-i, 3])
                lows.append(self.candles[-i, 4])
            elif highs:
                break

        if highs and lows:
            self.pre_london_high = max(highs)
            self.pre_london_low = min(lows)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def volume_surge(self) -> bool:
        avg_vol = np.mean(self.candles[-20:-1, 5])
        return self.candles[-1, 5] > avg_vol * 1.5

    def should_long(self) -> bool:
        if not self._is_london_session():
            return False

        if self._is_early_london():
            self._calculate_pre_london_range()
            return False

        if self.pre_london_high is None:
            return False

        buffer = self.atr * self.hp['breakout_buffer']
        breakout = self.close > self.pre_london_high + buffer

        return breakout and self.volume_surge

    def should_short(self) -> bool:
        if not self._is_london_session():
            return False

        if self._is_early_london():
            return False

        if self.pre_london_low is None:
            return False

        buffer = self.atr * self.hp['breakout_buffer']
        breakdown = self.close < self.pre_london_low - buffer

        return breakdown and self.volume_surge

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
        # Close at end of London session
        hour = self._get_hour()
        if hour >= self.hp['session_end']:
            self.liquidate()
            self.pre_london_high = None
            self.pre_london_low = None
