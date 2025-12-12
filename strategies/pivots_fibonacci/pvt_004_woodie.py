"""
PVT_004: Woodie Pivot Points Strategy
-------------------------------------
Woodie's pivot formula gives more weight to close.
PP = (H + L + 2*C) / 4

Entry: Trade pivots with Woodie's formula

Optimal Timeframes: 15m, 1h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class WoodiePivots(Strategy):
    """Woodie Pivot Points Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PVT_004"
        self.strategy_name = "Woodie Pivots"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 24, 'max': 96, 'default': 48},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    def _calculate_woodie(self):
        lookback = self.hp['lookback']
        candles = self.candles[-lookback:-1]

        h = np.max(candles[:, 3])
        l = np.min(candles[:, 4])
        c = candles[-1, 2]

        pp = (h + l + 2 * c) / 4
        r1 = 2 * pp - l
        r2 = pp + (h - l)
        s1 = 2 * pp - h
        s2 = pp - (h - l)

        return {'pp': pp, 'r1': r1, 'r2': r2, 's1': s1, 's2': s2}

    @property
    def pivots(self) -> dict:
        return self._calculate_woodie()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        pivots = self.pivots
        # Long on bounce from support
        if self.low <= pivots['s1'] and self.close > pivots['s1'] and self.close > self.open:
            return True
        return False

    def should_short(self) -> bool:
        pivots = self.pivots
        # Short on rejection from resistance
        if self.high >= pivots['r1'] and self.close < pivots['r1'] and self.close < self.open:
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
        self.take_profit = qty, self.pivots['pp']

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, self.pivots['pp']

    def update_position(self):
        pass
