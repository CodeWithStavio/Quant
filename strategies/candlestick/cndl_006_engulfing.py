"""
CNDL_006: Engulfing Pattern Strategy
------------------------------------
Bullish engulfing = large green candle engulfs previous red.
Bearish engulfing = large red candle engulfs previous green.

Entry: Trade in direction of engulfing candle

Optimal Timeframes: 1h, 4h, 1d
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class EngulfingStrategy(Strategy):
    """Engulfing Pattern Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CNDL_006"
        self.strategy_name = "Engulfing Pattern"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'min_engulf_ratio', 'type': float, 'min': 1.1, 'max': 2.0, 'default': 1.5},
            {'name': 'trend_period', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _is_bullish_engulfing(self) -> bool:
        """Check for bullish engulfing pattern"""
        # Previous candle
        prev_open = self.candles[-2, 1]
        prev_close = self.candles[-2, 2]
        prev_body = abs(prev_close - prev_open)

        # Current candle
        curr_open = self.open
        curr_close = self.close
        curr_body = abs(curr_close - curr_open)

        # Previous was red, current is green
        prev_red = prev_close < prev_open
        curr_green = curr_close > curr_open

        # Current body engulfs previous body
        engulfs = (curr_open <= prev_close and curr_close >= prev_open)

        # Body ratio check
        if prev_body == 0:
            return False
        ratio = curr_body / prev_body

        return prev_red and curr_green and engulfs and ratio >= self.hp['min_engulf_ratio']

    def _is_bearish_engulfing(self) -> bool:
        """Check for bearish engulfing pattern"""
        # Previous candle
        prev_open = self.candles[-2, 1]
        prev_close = self.candles[-2, 2]
        prev_body = abs(prev_close - prev_open)

        # Current candle
        curr_open = self.open
        curr_close = self.close
        curr_body = abs(curr_close - curr_open)

        # Previous was green, current is red
        prev_green = prev_close > prev_open
        curr_red = curr_close < curr_open

        # Current body engulfs previous body
        engulfs = (curr_open >= prev_close and curr_close <= prev_open)

        # Body ratio check
        if prev_body == 0:
            return False
        ratio = curr_body / prev_body

        return prev_green and curr_red and engulfs and ratio >= self.hp['min_engulf_ratio']

    def _in_downtrend(self) -> bool:
        """Check if price is in downtrend"""
        ma = ta.sma(self.candles, period=self.hp['trend_period'])
        return self.close < ma

    def _in_uptrend(self) -> bool:
        """Check if price is in uptrend"""
        ma = ta.sma(self.candles, period=self.hp['trend_period'])
        return self.close > ma

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Bullish engulfing after downtrend
        return self._is_bullish_engulfing() and self._in_downtrend()

    def should_short(self) -> bool:
        # Bearish engulfing after uptrend
        return self._is_bearish_engulfing() and self._in_uptrend()

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
