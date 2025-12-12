"""
TF_009: Moving Average Ribbon Trend Strategy
--------------------------------------------
Trade based on MA ribbon expansion/contraction.

Entry Long: Ribbon expanding upward
Entry Short: Ribbon expanding downward

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MARibbonTrend(Strategy):
    """Moving Average Ribbon Trend Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "TF_009"
        self.strategy_name = "MA Ribbon Trend"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ma_start', 'type': int, 'min': 8, 'max': 12, 'default': 10},
            {'name': 'ma_step', 'type': int, 'min': 4, 'max': 8, 'default': 5},
            {'name': 'num_mas', 'type': int, 'min': 4, 'max': 8, 'default': 6},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _calculate_ribbon(self, candles=None) -> List[float]:
        """Calculate ribbon of MAs"""
        if candles is None:
            candles = self.candles

        mas = []
        for i in range(self.hp['num_mas']):
            period = self.hp['ma_start'] + (i * self.hp['ma_step'])
            ma = ta.ema(candles, period=period)
            mas.append(ma)
        return mas

    @property
    def ribbon(self) -> List[float]:
        return self._calculate_ribbon()

    @property
    def prev_ribbon(self) -> List[float]:
        return self._calculate_ribbon(self.candles[:-1])

    @property
    def bullish_ribbon(self) -> bool:
        """All MAs aligned bullishly (shortest on top)"""
        r = self.ribbon
        for i in range(len(r) - 1):
            if r[i] <= r[i + 1]:
                return False
        return True

    @property
    def bearish_ribbon(self) -> bool:
        """All MAs aligned bearishly (shortest on bottom)"""
        r = self.ribbon
        for i in range(len(r) - 1):
            if r[i] >= r[i + 1]:
                return False
        return True

    @property
    def ribbon_width(self) -> float:
        """Width of ribbon (spread between first and last MA)"""
        r = self.ribbon
        return abs(r[0] - r[-1])

    @property
    def prev_ribbon_width(self) -> float:
        r = self.prev_ribbon
        return abs(r[0] - r[-1])

    @property
    def ribbon_expanding(self) -> bool:
        return self.ribbon_width > self.prev_ribbon_width

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.bullish_ribbon and self.ribbon_expanding

    def should_short(self) -> bool:
        return self.bearish_ribbon and self.ribbon_expanding

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.ribbon[-1] - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = self.ribbon[-1] + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Exit if ribbon contracts or reverses
        if self.is_long and (not self.bullish_ribbon or not self.ribbon_expanding):
            self.liquidate()
        elif self.is_short and (not self.bearish_ribbon or not self.ribbon_expanding):
            self.liquidate()
