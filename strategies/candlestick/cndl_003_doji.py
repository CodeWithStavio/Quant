"""
CNDL_003: Doji Strategy
-----------------------
Doji indicates indecision. At extremes, signals reversal.

Entry: Doji at trend extreme with next candle confirmation

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DojiStrategy(Strategy):
    """Doji Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CNDL_003"
        self.strategy_name = "Doji"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'doji_threshold', 'type': float, 'min': 0.05, 'max': 0.15, 'default': 0.1},
            {'name': 'trend_period', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _is_doji(self, idx=-2) -> bool:
        o = self.candles[idx, 1]
        c = self.candles[idx, 2]
        h = self.candles[idx, 3]
        l = self.candles[idx, 4]

        body = abs(c - o)
        total_range = h - l
        if total_range == 0:
            return False

        body_pct = body / total_range
        return body_pct < self.hp['doji_threshold']

    def _in_uptrend(self) -> bool:
        period = self.hp['trend_period']
        ma = np.mean(self.candles[-period:-1, 2])
        return self.candles[-2, 2] > ma

    def _in_downtrend(self) -> bool:
        period = self.hp['trend_period']
        ma = np.mean(self.candles[-period:-1, 2])
        return self.candles[-2, 2] < ma

    @property
    def bullish_confirmation(self) -> bool:
        return self.close > self.open and self.close > self.candles[-2, 3]

    @property
    def bearish_confirmation(self) -> bool:
        return self.close < self.open and self.close < self.candles[-2, 4]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_doji() and self._in_downtrend() and self.bullish_confirmation

    def should_short(self) -> bool:
        return self._is_doji() and self._in_uptrend() and self.bearish_confirmation

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
