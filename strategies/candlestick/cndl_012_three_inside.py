"""
CNDL_012: Three Inside Up/Down Strategy
---------------------------------------
Three Inside Up = harami + confirmation candle.
Three Inside Down = harami + confirmation candle.

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


class ThreeInsideStrategy(Strategy):
    """Three Inside Up/Down Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CNDL_012"
        self.strategy_name = "Three Inside"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'body_ratio_max', 'type': float, 'min': 0.3, 'max': 0.6, 'default': 0.5},
            {'name': 'trend_period', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 4.5, 'default': 3.5},
        ]

    def _is_three_inside_up(self) -> bool:
        """Three Inside Up = Bullish Harami + Confirmation"""
        # First candle (large bearish) at -3
        c1_open = self.candles[-3, 1]
        c1_close = self.candles[-3, 2]
        c1_body = abs(c1_close - c1_open)

        if c1_close >= c1_open:  # Not bearish
            return False

        # Second candle (small bullish inside first) at -2
        c2_open = self.candles[-2, 1]
        c2_close = self.candles[-2, 2]
        c2_body = abs(c2_close - c2_open)

        if c2_close <= c2_open:  # Not bullish
            return False

        # Check harami (second inside first)
        if not (c2_open > c1_close and c2_close < c1_open):
            return False

        # Check body ratio
        if c1_body > 0 and c2_body / c1_body > self.hp['body_ratio_max']:
            return False

        # Third candle (confirmation) closes above first candle open
        c3_close = self.close
        return c3_close > c1_open

    def _is_three_inside_down(self) -> bool:
        """Three Inside Down = Bearish Harami + Confirmation"""
        # First candle (large bullish) at -3
        c1_open = self.candles[-3, 1]
        c1_close = self.candles[-3, 2]
        c1_body = abs(c1_close - c1_open)

        if c1_close <= c1_open:  # Not bullish
            return False

        # Second candle (small bearish inside first) at -2
        c2_open = self.candles[-2, 1]
        c2_close = self.candles[-2, 2]
        c2_body = abs(c2_close - c2_open)

        if c2_close >= c2_open:  # Not bearish
            return False

        # Check harami (second inside first)
        if not (c2_open < c1_close and c2_close > c1_open):
            return False

        # Check body ratio
        if c1_body > 0 and c2_body / c1_body > self.hp['body_ratio_max']:
            return False

        # Third candle (confirmation) closes below first candle open
        c3_close = self.close
        return c3_close < c1_open

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
        return self._is_three_inside_up() and self._in_downtrend()

    def should_short(self) -> bool:
        return self._is_three_inside_down() and self._in_uptrend()

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
