"""
SEASON_004: Quarterly Pattern Strategy
--------------------------------------
Trade based on quarterly patterns (Q1-Q4).

Entry Long: Historically strong quarters
Entry Short: Historically weak quarters

Optimal Timeframes: 1d
Complexity: 5/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from datetime import datetime
from typing import List, Dict


class QuarterlyPattern(Strategy):
    """Quarterly Pattern Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SEASON_004"
        self.strategy_name = "Quarterly Pattern"
        self.complexity = 5
        self.crypto_suitability = 7
        # Q4 and Q1 typically strong for crypto
        self.bullish_quarters = [4, 1]
        self.bearish_quarters = [2, 3]

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'trend_period', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.5, 'max': 4.0, 'default': 3.0},
        ]

    def _get_quarter(self) -> int:
        """Get current quarter (1-4)"""
        timestamp = self.candles[-1, 0] / 1000
        dt = datetime.utcfromtimestamp(timestamp)
        return (dt.month - 1) // 3 + 1

    @property
    def is_bullish_quarter(self) -> bool:
        return self._get_quarter() in self.bullish_quarters

    @property
    def is_bearish_quarter(self) -> bool:
        return self._get_quarter() in self.bearish_quarters

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
        return self.is_bullish_quarter and self.trend == 1

    def should_short(self) -> bool:
        return self.is_bearish_quarter and self.trend == -1

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
        if self.is_long and (self.is_bearish_quarter or self.trend == -1):
            self.liquidate()
        elif self.is_short and (self.is_bullish_quarter or self.trend == 1):
            self.liquidate()
