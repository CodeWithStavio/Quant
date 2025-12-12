"""
PVT_002: Fibonacci Pivot Points Strategy
----------------------------------------
Pivot points using Fibonacci ratios for R/S levels.
More precise levels based on Fibonacci numbers.

Entry Long: Bounce off Fibonacci support
Entry Short: Bounce off Fibonacci resistance

Optimal Timeframes: 15m, 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class FibonacciPivots(Strategy):
    """Fibonacci Pivot Points Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PVT_002"
        self.strategy_name = "Fibonacci Pivots"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 24, 'max': 96, 'default': 48},
            {'name': 'bounce_threshold', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    def _calculate_fib_pivots(self):
        """Calculate Fibonacci pivot points"""
        lookback = self.hp['lookback']
        candles = self.candles[-lookback:-1]

        period_high = np.max(candles[:, 3])
        period_low = np.min(candles[:, 4])
        period_close = candles[-1, 2]

        pp = (period_high + period_low + period_close) / 3
        range_hl = period_high - period_low

        r1 = pp + 0.382 * range_hl
        r2 = pp + 0.618 * range_hl
        r3 = pp + 1.000 * range_hl
        s1 = pp - 0.382 * range_hl
        s2 = pp - 0.618 * range_hl
        s3 = pp - 1.000 * range_hl

        return {'pp': pp, 'r1': r1, 'r2': r2, 'r3': r3, 's1': s1, 's2': s2, 's3': s3}

    @property
    def pivots(self) -> dict:
        return self._calculate_fib_pivots()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _bounced_up_from(self, level) -> bool:
        threshold = level * self.hp['bounce_threshold']
        prev_low = self.candles[-2, 4]
        touched = abs(prev_low - level) < threshold
        bounced = self.close > level and self.close > self.open
        return touched and bounced

    def _bounced_down_from(self, level) -> bool:
        threshold = level * self.hp['bounce_threshold']
        prev_high = self.candles[-2, 3]
        touched = abs(prev_high - level) < threshold
        bounced = self.close < level and self.close < self.open
        return touched and bounced

    def should_long(self) -> bool:
        pivots = self.pivots
        for level_name in ['s1', 's2', 's3', 'pp']:
            if self._bounced_up_from(pivots[level_name]):
                return True
        return False

    def should_short(self) -> bool:
        pivots = self.pivots
        for level_name in ['r1', 'r2', 'r3', 'pp']:
            if self._bounced_down_from(pivots[level_name]):
                return True
        return False

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
        pass  # Let TP/SL handle exits
