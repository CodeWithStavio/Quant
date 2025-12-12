"""
CNDL_013: Three Outside Up/Down Strategy
----------------------------------------
Three Outside Up = Engulfing + Confirmation candle.
Three Outside Down = Engulfing + Confirmation candle.

Entry: Trade after third candle confirms

Optimal Timeframes: 4h, 1d
Complexity: 4/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ThreeOutsideStrategy(Strategy):
    """Three Outside Up/Down Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CNDL_013"
        self.strategy_name = "Three Outside"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'min_engulf_ratio', 'type': float, 'min': 1.1, 'max': 2.0, 'default': 1.3},
            {'name': 'trend_period', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 4.5, 'default': 3.5},
        ]

    def _is_three_outside_up(self) -> bool:
        """Three Outside Up = Bullish Engulfing + Confirmation"""
        # First candle (small bearish) at -3
        c1_open = self.candles[-3, 1]
        c1_close = self.candles[-3, 2]
        c1_body = abs(c1_close - c1_open)

        if c1_close >= c1_open:  # Not bearish
            return False

        # Second candle (large bullish engulfing) at -2
        c2_open = self.candles[-2, 1]
        c2_close = self.candles[-2, 2]
        c2_body = abs(c2_close - c2_open)

        if c2_close <= c2_open:  # Not bullish
            return False

        # Check engulfing
        if not (c2_open <= c1_close and c2_close >= c1_open):
            return False

        # Check body ratio
        if c1_body > 0 and c2_body / c1_body < self.hp['min_engulf_ratio']:
            return False

        # Third candle confirms by closing higher
        c3_close = self.close
        return c3_close > c2_close

    def _is_three_outside_down(self) -> bool:
        """Three Outside Down = Bearish Engulfing + Confirmation"""
        # First candle (small bullish) at -3
        c1_open = self.candles[-3, 1]
        c1_close = self.candles[-3, 2]
        c1_body = abs(c1_close - c1_open)

        if c1_close <= c1_open:  # Not bullish
            return False

        # Second candle (large bearish engulfing) at -2
        c2_open = self.candles[-2, 1]
        c2_close = self.candles[-2, 2]
        c2_body = abs(c2_close - c2_open)

        if c2_close >= c2_open:  # Not bearish
            return False

        # Check engulfing
        if not (c2_open >= c1_close and c2_close <= c1_open):
            return False

        # Check body ratio
        if c1_body > 0 and c2_body / c1_body < self.hp['min_engulf_ratio']:
            return False

        # Third candle confirms by closing lower
        c3_close = self.close
        return c3_close < c2_close

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
        return self._is_three_outside_up() and self._in_downtrend()

    def should_short(self) -> bool:
        return self._is_three_outside_down() and self._in_uptrend()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        pattern_low = min(self.candles[-3, 4], self.candles[-2, 4], self.low)
        stop = pattern_low - (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        pattern_high = max(self.candles[-3, 3], self.candles[-2, 3], self.high)
        stop = pattern_high + (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        pass
