"""
CNDL_010: Three White Soldiers/Black Crows Strategy
---------------------------------------------------
Three White Soldiers = 3 consecutive bullish candles.
Three Black Crows = 3 consecutive bearish candles.

Entry: Trade after pattern completion

Optimal Timeframes: 4h, 1d
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ThreeSoldiersCrows(Strategy):
    """Three White Soldiers/Black Crows Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CNDL_010"
        self.strategy_name = "Three Soldiers Crows"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'min_body_pct', 'type': float, 'min': 0.5, 'max': 0.8, 'default': 0.6},
            {'name': 'trend_period', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 4.5, 'default': 3.5},
        ]

    def _is_strong_bullish(self, idx) -> bool:
        """Check if candle at index is strong bullish"""
        o = self.candles[idx, 1]
        c = self.candles[idx, 2]
        h = self.candles[idx, 3]
        l = self.candles[idx, 4]

        if c <= o:  # Not bullish
            return False

        body = c - o
        total_range = h - l

        if total_range == 0:
            return False

        return (body / total_range) >= self.hp['min_body_pct']

    def _is_strong_bearish(self, idx) -> bool:
        """Check if candle at index is strong bearish"""
        o = self.candles[idx, 1]
        c = self.candles[idx, 2]
        h = self.candles[idx, 3]
        l = self.candles[idx, 4]

        if c >= o:  # Not bearish
            return False

        body = o - c
        total_range = h - l

        if total_range == 0:
            return False

        return (body / total_range) >= self.hp['min_body_pct']

    def _is_three_white_soldiers(self) -> bool:
        """Check for three white soldiers pattern"""
        # All three candles must be strong bullish
        if not (self._is_strong_bullish(-3) and
                self._is_strong_bullish(-2) and
                self._is_strong_bullish(-1)):
            return False

        # Each candle opens within previous body and closes higher
        for i in [-2, -1]:
            prev_open = self.candles[i-1, 1]
            prev_close = self.candles[i-1, 2]
            curr_open = self.candles[i, 1]
            curr_close = self.candles[i, 2]

            # Opens within previous body
            if not (prev_open <= curr_open <= prev_close):
                return False

            # Closes higher than previous
            if curr_close <= prev_close:
                return False

        return True

    def _is_three_black_crows(self) -> bool:
        """Check for three black crows pattern"""
        # All three candles must be strong bearish
        if not (self._is_strong_bearish(-3) and
                self._is_strong_bearish(-2) and
                self._is_strong_bearish(-1)):
            return False

        # Each candle opens within previous body and closes lower
        for i in [-2, -1]:
            prev_open = self.candles[i-1, 1]
            prev_close = self.candles[i-1, 2]
            curr_open = self.candles[i, 1]
            curr_close = self.candles[i, 2]

            # Opens within previous body
            if not (prev_close <= curr_open <= prev_open):
                return False

            # Closes lower than previous
            if curr_close >= prev_close:
                return False

        return True

    def _in_downtrend(self) -> bool:
        ma = ta.sma(self.candles[:-3], period=self.hp['trend_period'])
        return self.candles[-4, 2] < ma

    def _in_uptrend(self) -> bool:
        ma = ta.sma(self.candles[:-3], period=self.hp['trend_period'])
        return self.candles[-4, 2] > ma

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_three_white_soldiers() and self._in_downtrend()

    def should_short(self) -> bool:
        return self._is_three_black_crows() and self._in_uptrend()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.candles[-3, 4] - (self.atr * 0.5)  # Below pattern low
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = self.candles[-3, 3] + (self.atr * 0.5)  # Above pattern high
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        pass
