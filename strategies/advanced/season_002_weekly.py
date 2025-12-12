"""
SEASON_002: Weekly Seasonality Strategy
---------------------------------------
Trade based on day-of-week patterns.

Entry Long: Historically bullish days with confirmation
Entry Short: Historically bearish days with confirmation

Optimal Timeframes: 4h, 1d
Complexity: 4/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from datetime import datetime
from typing import List, Dict


class WeeklySeason(Strategy):
    """Weekly Seasonality Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SEASON_002"
        self.strategy_name = "Weekly Season"
        self.complexity = 4
        self.crypto_suitability = 7
        # Common pattern: weak Sunday/Monday, strong mid-week
        self.bullish_days = [2, 3, 4]  # Tue, Wed, Thu
        self.bearish_days = [6, 0]  # Sat, Sun

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'trend_period', 'type': int, 'min': 10, 'max': 25, 'default': 15},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _get_day_of_week(self) -> int:
        """Get current day (0=Mon, 6=Sun)"""
        timestamp = self.candles[-1, 0] / 1000
        dt = datetime.utcfromtimestamp(timestamp)
        return dt.weekday()

    @property
    def is_bullish_day(self) -> bool:
        return self._get_day_of_week() in self.bullish_days

    @property
    def is_bearish_day(self) -> bool:
        return self._get_day_of_week() in self.bearish_days

    @property
    def momentum(self) -> float:
        return ta.roc(self.candles, period=5)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.is_bullish_day and self.momentum > 0

    def should_short(self) -> bool:
        return self.is_bearish_day and self.momentum < 0

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
        # Exit after 2-3 days or on reversal
        if self.is_long and (self.is_bearish_day or self.momentum < -1):
            self.liquidate()
        elif self.is_short and (self.is_bullish_day or self.momentum > 1):
            self.liquidate()
