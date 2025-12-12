"""
SEASON_005: Holiday Effect Strategy
-----------------------------------
Trade based on holiday/event patterns.

Entry Long: Post-holiday rally pattern
Entry Short: Pre-holiday weakness pattern

Optimal Timeframes: 4h, 1d
Complexity: 5/10
Crypto Suitability: 6/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from datetime import datetime
from typing import List, Dict


class HolidayEffect(Strategy):
    """Holiday Effect Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SEASON_005"
        self.strategy_name = "Holiday Effect"
        self.complexity = 5
        self.crypto_suitability = 6
        # Approximate holiday periods (month, day ranges)
        # Christmas/New Year, Chinese New Year, Thanksgiving
        self.holiday_windows = [
            (12, 20, 31),  # Dec 20-31
            (1, 1, 5),  # Jan 1-5
        ]

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'trend_period', 'type': int, 'min': 10, 'max': 25, 'default': 15},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _is_holiday_window(self) -> bool:
        """Check if in holiday window"""
        timestamp = self.candles[-1, 0] / 1000
        dt = datetime.utcfromtimestamp(timestamp)

        for month, day_start, day_end in self.holiday_windows:
            if dt.month == month and day_start <= dt.day <= day_end:
                return True
        return False

    def _is_post_holiday(self) -> bool:
        """Check if in post-holiday period"""
        timestamp = self.candles[-1, 0] / 1000
        dt = datetime.utcfromtimestamp(timestamp)

        # After New Year
        if dt.month == 1 and 6 <= dt.day <= 15:
            return True
        return False

    @property
    def trend(self) -> int:
        ma = ta.sma(self.candles, period=self.hp['trend_period'])
        if self.close > ma:
            return 1
        elif self.close < ma:
            return -1
        return 0

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Post-holiday rally opportunity
        return self._is_post_holiday() and self.trend == 1

    def should_short(self) -> bool:
        # During holiday quiet period with weakness
        return self._is_holiday_window() and self.trend == -1

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
        rsi = ta.rsi(self.candles, period=14)
        if self.is_long and rsi > 70:
            self.liquidate()
        elif self.is_short and rsi < 30:
            self.liquidate()
