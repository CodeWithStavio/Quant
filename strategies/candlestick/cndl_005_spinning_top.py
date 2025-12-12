"""
CNDL_005: Spinning Top Strategy
-------------------------------
Spinning top = indecision with equal shadows.

Entry: After spinning top, trade in direction of next candle

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SpinningTopStrategy(Strategy):
    """Spinning Top Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CNDL_005"
        self.strategy_name = "Spinning Top"
        self.complexity = 3
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'body_max', 'type': float, 'min': 0.2, 'max': 0.4, 'default': 0.3},
            {'name': 'shadow_balance', 'type': float, 'min': 0.5, 'max': 0.9, 'default': 0.7},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _is_spinning_top(self, idx=-2) -> bool:
        o = self.candles[idx, 1]
        c = self.candles[idx, 2]
        h = self.candles[idx, 3]
        l = self.candles[idx, 4]

        body = abs(c - o)
        total_range = h - l
        if total_range == 0:
            return False

        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - l

        body_pct = body / total_range
        shadow_ratio = min(upper_shadow, lower_shadow) / max(upper_shadow, lower_shadow) if max(upper_shadow, lower_shadow) > 0 else 0

        return body_pct < self.hp['body_max'] and shadow_ratio > self.hp['shadow_balance']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_spinning_top() and self.close > self.open and self.close > self.candles[-2, 3]

    def should_short(self) -> bool:
        return self._is_spinning_top() and self.close < self.open and self.close < self.candles[-2, 4]

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
