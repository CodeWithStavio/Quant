"""
CRYPTO_010: NY Session Strategy
-------------------------------
Trade based on New York session patterns (UTC 13:00-22:00).

Entry Long: NY session trend continuation
Entry Short: NY session trend continuation

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


class NYSession(Strategy):
    """NY Session Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_010"
        self.strategy_name = "NY Session"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'session_start', 'type': int, 'min': 13, 'max': 15, 'default': 14},
            {'name': 'session_end', 'type': int, 'min': 20, 'max': 22, 'default': 21},
            {'name': 'trend_period', 'type': int, 'min': 10, 'max': 25, 'default': 15},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _get_hour(self) -> int:
        """Get current hour in UTC"""
        timestamp = self.candles[-1, 0] / 1000
        dt = datetime.utcfromtimestamp(timestamp)
        return dt.hour

    def _is_ny_session(self) -> bool:
        """Check if in NY session"""
        hour = self._get_hour()
        return self.hp['session_start'] <= hour < self.hp['session_end']

    def _get_london_trend(self) -> int:
        """Determine London session trend direction"""
        # Look at last 6-8 hours (London session)
        period = self.hp['trend_period']
        if len(self.candles) < period + 1:
            return 0

        start_price = self.candles[-period, 2]
        end_price = self.candles[-1, 2]
        change_pct = (end_price - start_price) / start_price * 100

        if change_pct > 0.5:
            return 1
        elif change_pct < -0.5:
            return -1
        return 0

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=14)

    @property
    def volume_confirm(self) -> bool:
        avg_vol = np.mean(self.candles[-20:-1, 5])
        return self.candles[-1, 5] > avg_vol

    def should_long(self) -> bool:
        if not self._is_ny_session():
            return False

        # Continue London bullish trend
        london_bullish = self._get_london_trend() == 1
        not_overbought = self.rsi < 70

        return london_bullish and not_overbought and self.volume_confirm

    def should_short(self) -> bool:
        if not self._is_ny_session():
            return False

        # Continue London bearish trend
        london_bearish = self._get_london_trend() == -1
        not_oversold = self.rsi > 30

        return london_bearish and not_oversold and self.volume_confirm

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
        # Close at end of NY session
        hour = self._get_hour()
        if hour >= self.hp['session_end'] or hour < self.hp['session_start']:
            self.liquidate()
