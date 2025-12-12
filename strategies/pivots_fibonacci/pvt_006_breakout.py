"""
PVT_006: Pivot Breakout Strategy
--------------------------------
Trade breakouts above/below pivot levels.
Confirms trend continuation.

Entry Long: Price breaks above R1/R2
Entry Short: Price breaks below S1/S2

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class PivotBreakout(Strategy):
    """Pivot Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PVT_006"
        self.strategy_name = "Pivot Breakout"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 24, 'max': 96, 'default': 48},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_pivots(self):
        lookback = self.hp['lookback']
        candles = self.candles[-lookback:-1]

        h = np.max(candles[:, 3])
        l = np.min(candles[:, 4])
        c = candles[-1, 2]

        pp = (h + l + c) / 3
        r1 = 2 * pp - l
        r2 = pp + (h - l)
        s1 = 2 * pp - h
        s2 = pp - (h - l)

        return {'pp': pp, 'r1': r1, 'r2': r2, 's1': s1, 's2': s2}

    @property
    def pivots(self) -> dict:
        return self._calculate_pivots()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _broke_above(self, level) -> bool:
        prev_close = self.candles[-2, 2]
        return prev_close <= level and self.close > level

    def _broke_below(self, level) -> bool:
        prev_close = self.candles[-2, 2]
        return prev_close >= level and self.close < level

    def should_long(self) -> bool:
        pivots = self.pivots
        return self._broke_above(pivots['r1']) or self._broke_above(pivots['r2'])

    def should_short(self) -> bool:
        pivots = self.pivots
        return self._broke_below(pivots['s1']) or self._broke_below(pivots['s2'])

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
        # Exit if price returns to pivot point
        if self.is_long and self.close < pivots['pp']:
            self.liquidate()
        elif self.is_short and self.close > pivots['pp']:
            self.liquidate()
