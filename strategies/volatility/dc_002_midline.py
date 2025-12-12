"""
DC_002: Donchian Mid-Line Strategy
----------------------------------
Trade bounces and breaks of the Donchian midline.

Entry Long: Price crosses above midline from below
Entry Short: Price crosses below midline from above

Optimal Timeframes: 1h, 4h
Complexity: 2/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DonchianMidline(Strategy):
    """Donchian Mid-Line Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "DC_002"
        self.strategy_name = "Donchian Midline"
        self.complexity = 2
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.5, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.5, 'default': 2.5},
        ]

    def _donchian(self, candles=None):
        """Calculate Donchian Channel"""
        if candles is None:
            candles = self.candles

        high = candles[:, 3]
        low = candles[:, 4]
        period = self.hp['period']

        upper = np.max(high[-period:])
        lower = np.min(low[-period:])
        middle = (upper + lower) / 2

        return upper, middle, lower

    @property
    def midline(self) -> float:
        upper, middle, lower = self._donchian()
        return middle

    @property
    def midline_prev(self) -> float:
        upper, middle, lower = self._donchian(self.candles[:-1])
        return middle

    @property
    def upper(self) -> float:
        upper, middle, lower = self._donchian()
        return upper

    @property
    def lower(self) -> float:
        upper, middle, lower = self._donchian()
        return lower

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Price crosses above midline
        return self.candles[-2, 2] < self.midline_prev and self.close > self.midline

    def should_short(self) -> bool:
        # Price crosses below midline
        return self.candles[-2, 2] > self.midline_prev and self.close < self.midline

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        # Exit at channel boundaries
        if self.is_long and self.close >= self.upper:
            self.liquidate()
        elif self.is_short and self.close <= self.lower:
            self.liquidate()
