"""
PVT_001: Standard Pivot Points Strategy
---------------------------------------
Classic floor trader pivot points.
PP = (High + Low + Close) / 3
R1 = 2*PP - Low, S1 = 2*PP - High
R2 = PP + (High - Low), S2 = PP - (High - Low)

Entry Long: Bounce off support levels
Entry Short: Bounce off resistance levels

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class StandardPivots(Strategy):
    """Standard Pivot Points Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PVT_001"
        self.strategy_name = "Standard Pivots"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 24, 'max': 96, 'default': 48},
            {'name': 'bounce_threshold', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    def _calculate_pivots(self):
        """Calculate standard pivot points from recent period"""
        lookback = self.hp['lookback']
        candles = self.candles[-lookback:-1]

        period_high = np.max(candles[:, 3])
        period_low = np.min(candles[:, 4])
        period_close = candles[-1, 2]

        pp = (period_high + period_low + period_close) / 3
        r1 = 2 * pp - period_low
        s1 = 2 * pp - period_high
        r2 = pp + (period_high - period_low)
        s2 = pp - (period_high - period_low)
        r3 = period_high + 2 * (pp - period_low)
        s3 = period_low - 2 * (period_high - pp)

        return {'pp': pp, 'r1': r1, 'r2': r2, 'r3': r3, 's1': s1, 's2': s2, 's3': s3}

    @property
    def pivots(self) -> dict:
        return self._calculate_pivots()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _near_level(self, level) -> bool:
        threshold = level * self.hp['bounce_threshold']
        return abs(self.close - level) < threshold

    def _bounced_up_from(self, level) -> bool:
        prev_low = self.candles[-2, 4]
        touched = prev_low <= level * 1.001
        bounced = self.close > level and self.close > self.open
        return touched and bounced

    def _bounced_down_from(self, level) -> bool:
        prev_high = self.candles[-2, 3]
        touched = prev_high >= level * 0.999
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
        pivots = self.pivots
        if self.is_long:
            # Take profit at next resistance level
            if self.close >= pivots['r1']:
                self.liquidate()
        elif self.is_short:
            # Take profit at next support level
            if self.close <= pivots['s1']:
                self.liquidate()
