"""
BRK_002: Range Breakout Strategy
--------------------------------
Trade breakouts from established trading ranges.

Entry Long: Price breaks above range high
Entry Short: Price breaks below range low

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class RangeBreakout(Strategy):
    """Range Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BRK_002"
        self.strategy_name = "Range Breakout"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'range_period', 'type': int, 'min': 15, 'max': 40, 'default': 20},
            {'name': 'consolidation_bars', 'type': int, 'min': 5, 'max': 15, 'default': 10},
            {'name': 'breakout_confirm', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def range_high(self) -> float:
        return np.max(self.candles[-self.hp['range_period']:, 3])

    @property
    def range_low(self) -> float:
        return np.min(self.candles[-self.hp['range_period']:, 4])

    @property
    def range_width(self) -> float:
        return self.range_high - self.range_low

    @property
    def in_consolidation(self) -> bool:
        """Check if recent bars are within a tight range"""
        recent_high = np.max(self.candles[-self.hp['consolidation_bars']:, 3])
        recent_low = np.min(self.candles[-self.hp['consolidation_bars']:, 4])
        recent_range = recent_high - recent_low

        if self.range_width == 0:
            return False
        return recent_range / self.range_width < 0.5

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        confirm = self.close * self.hp['breakout_confirm']
        prev_close = self.candles[-2, 2]
        return (prev_close <= self.range_high and
                self.close > self.range_high + confirm)

    def should_short(self) -> bool:
        confirm = self.close * self.hp['breakout_confirm']
        prev_close = self.candles[-2, 2]
        return (prev_close >= self.range_low and
                self.close < self.range_low - confirm)

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.range_high - (self.atr * self.hp['atr_multiplier_sl'])
        target = entry + (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = self.range_low + (self.atr * self.hp['atr_multiplier_sl'])
        target = entry - (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        # Exit if price re-enters range
        if self.is_long and self.close < self.range_high:
            self.liquidate()
        elif self.is_short and self.close > self.range_low:
            self.liquidate()
