"""
BRK_005: Inside Bar Breakout Strategy
-------------------------------------
Trade breakouts from inside bar patterns.

Entry Long: Price breaks above inside bar high
Entry Short: Price breaks below inside bar low

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class InsideBarBreakout(Strategy):
    """Inside Bar Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BRK_005"
        self.strategy_name = "Inside Bar Breakout"
        self.complexity = 3
        self.crypto_suitability = 8
        self.inside_bar_detected = False
        self.mother_high = None
        self.mother_low = None

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'breakout_confirm', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _is_inside_bar(self) -> bool:
        """Check if previous bar is an inside bar"""
        mother_high = self.candles[-3, 3]
        mother_low = self.candles[-3, 4]
        inside_high = self.candles[-2, 3]
        inside_low = self.candles[-2, 4]

        return inside_high < mother_high and inside_low > mother_low

    def _update_inside_bar(self):
        """Track inside bar pattern"""
        if self._is_inside_bar():
            self.inside_bar_detected = True
            self.mother_high = self.candles[-3, 3]
            self.mother_low = self.candles[-3, 4]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        self._update_inside_bar()
        if not self.inside_bar_detected:
            return False

        confirm = self.close * self.hp['breakout_confirm']
        return self.close > self.mother_high + confirm

    def should_short(self) -> bool:
        self._update_inside_bar()
        if not self.inside_bar_detected:
            return False

        confirm = self.close * self.hp['breakout_confirm']
        return self.close < self.mother_low - confirm

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.mother_low - (self.atr * 0.5)
        target = entry + (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target
        self.inside_bar_detected = False

    def go_short(self):
        entry = self.price
        stop = self.mother_high + (self.atr * 0.5)
        target = entry - (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target
        self.inside_bar_detected = False

    def update_position(self):
        pass
