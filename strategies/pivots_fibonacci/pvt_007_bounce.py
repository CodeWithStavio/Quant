"""
PVT_007: Pivot Bounce Strategy
------------------------------
Pure mean reversion at pivot levels.
Trade bounces with confirmation candles.

Entry: Bounce off pivot level with reversal candle

Optimal Timeframes: 15m, 1h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class PivotBounce(Strategy):
    """Pivot Bounce Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PVT_007"
        self.strategy_name = "Pivot Bounce"
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
        lookback = self.hp['lookback']
        candles = self.candles[-lookback:-1]

        h = np.max(candles[:, 3])
        l = np.min(candles[:, 4])
        c = candles[-1, 2]

        pp = (h + l + c) / 3
        r1 = 2 * pp - l
        s1 = 2 * pp - h

        return {'pp': pp, 'r1': r1, 's1': s1}

    @property
    def pivots(self) -> dict:
        return self._calculate_pivots()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def bullish_candle(self) -> bool:
        return self.close > self.open

    @property
    def bearish_candle(self) -> bool:
        return self.close < self.open

    def _near_level(self, level) -> bool:
        threshold = level * self.hp['bounce_threshold']
        return abs(self.close - level) < threshold

    def should_long(self) -> bool:
        pivots = self.pivots
        # Bounce up from support
        for level in [pivots['s1'], pivots['pp']]:
            if self._near_level(level) and self.bullish_candle and self.low <= level:
                return True
        return False

    def should_short(self) -> bool:
        pivots = self.pivots
        # Bounce down from resistance
        for level in [pivots['r1'], pivots['pp']]:
            if self._near_level(level) and self.bearish_candle and self.high >= level:
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
