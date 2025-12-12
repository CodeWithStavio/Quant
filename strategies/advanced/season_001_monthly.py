"""
SEASON_001: Monthly Seasonality Strategy
----------------------------------------
Trade based on monthly seasonal patterns.

Entry Long: Historically bullish months with confirmation
Entry Short: Historically bearish months with confirmation

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


class MonthlySeason(Strategy):
    """Monthly Seasonality Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SEASON_001"
        self.strategy_name = "Monthly Season"
        self.complexity = 5
        self.crypto_suitability = 7
        # Crypto typically bullish: Oct-Apr, bearish: May-Sep
        self.bullish_months = [10, 11, 12, 1, 2, 3, 4]
        self.bearish_months = [5, 6, 7, 8, 9]

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'trend_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.5, 'default': 2.5},
        ]

    def _get_month(self) -> int:
        """Get current month"""
        timestamp = self.candles[-1, 0] / 1000
        dt = datetime.utcfromtimestamp(timestamp)
        return dt.month

    @property
    def is_bullish_season(self) -> bool:
        return self._get_month() in self.bullish_months

    @property
    def is_bearish_season(self) -> bool:
        return self._get_month() in self.bearish_months

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
        return self.is_bullish_season and self.trend == 1

    def should_short(self) -> bool:
        return self.is_bearish_season and self.trend == -1

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
        # Exit on season change or trend reversal
        if self.is_long and (self.is_bearish_season or self.trend == -1):
            self.liquidate()
        elif self.is_short and (self.is_bullish_season or self.trend == 1):
            self.liquidate()
