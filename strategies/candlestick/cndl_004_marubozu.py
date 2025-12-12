"""
CNDL_004: Marubozu Strategy
---------------------------
Marubozu = strong momentum candle with no wicks.

Entry: Trade in direction of Marubozu

Optimal Timeframes: 1h, 4h
Complexity: 2/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MarubozuStrategy(Strategy):
    """Marubozu Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CNDL_004"
        self.strategy_name = "Marubozu"
        self.complexity = 2
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'body_ratio', 'type': float, 'min': 0.85, 'max': 0.95, 'default': 0.9},
            {'name': 'min_body_atr', 'type': float, 'min': 0.5, 'max': 1.5, 'default': 1.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _is_bullish_marubozu(self) -> bool:
        o = self.candles[-1, 1]
        c = self.candles[-1, 2]
        h = self.candles[-1, 3]
        l = self.candles[-1, 4]

        if c <= o:
            return False

        body = c - o
        total_range = h - l
        if total_range == 0:
            return False

        body_pct = body / total_range
        return body_pct >= self.hp['body_ratio'] and body >= self.atr * self.hp['min_body_atr']

    def _is_bearish_marubozu(self) -> bool:
        o = self.candles[-1, 1]
        c = self.candles[-1, 2]
        h = self.candles[-1, 3]
        l = self.candles[-1, 4]

        if c >= o:
            return False

        body = o - c
        total_range = h - l
        if total_range == 0:
            return False

        body_pct = body / total_range
        return body_pct >= self.hp['body_ratio'] and body >= self.atr * self.hp['min_body_atr']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_bullish_marubozu()

    def should_short(self) -> bool:
        return self._is_bearish_marubozu()

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
