"""
PVT_005: DeMark Pivot Points Strategy
-------------------------------------
Tom DeMark's pivot calculation.
Different formulas based on open vs close relationship.

Entry: Trade DeMark pivot levels

Optimal Timeframes: 15m, 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DeMarkPivots(Strategy):
    """DeMark Pivot Points Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PVT_005"
        self.strategy_name = "DeMark Pivots"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 24, 'max': 96, 'default': 48},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    def _calculate_demark(self):
        lookback = self.hp['lookback']
        candles = self.candles[-lookback:-1]

        h = np.max(candles[:, 3])
        l = np.min(candles[:, 4])
        o = candles[0, 1]
        c = candles[-1, 2]

        # DeMark calculation depends on close vs open relationship
        if c < o:
            x = h + 2 * l + c
        elif c > o:
            x = 2 * h + l + c
        else:
            x = h + l + 2 * c

        pp = x / 4
        r1 = x / 2 - l
        s1 = x / 2 - h

        return {'pp': pp, 'r1': r1, 's1': s1}

    @property
    def pivots(self) -> dict:
        return self._calculate_demark()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        pivots = self.pivots
        if self.low <= pivots['s1'] and self.close > pivots['s1'] and self.close > self.open:
            return True
        return False

    def should_short(self) -> bool:
        pivots = self.pivots
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
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        pass
