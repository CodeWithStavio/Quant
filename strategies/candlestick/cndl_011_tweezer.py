"""
CNDL_011: Tweezer Tops/Bottoms Strategy
---------------------------------------
Tweezer Bottom = two candles with equal lows (reversal).
Tweezer Top = two candles with equal highs (reversal).

Entry: Trade reversal on confirmation

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TweezerStrategy(Strategy):
    """Tweezer Tops/Bottoms Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CNDL_011"
        self.strategy_name = "Tweezer Pattern"
        self.complexity = 3
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'tolerance_pct', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'trend_period', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _is_tweezer_bottom(self) -> bool:
        """Check for tweezer bottom pattern"""
        # Get lows of last two candles
        low1 = self.candles[-2, 4]
        low2 = self.candles[-1, 4]

        # Check if lows are approximately equal
        tolerance = self.close * self.hp['tolerance_pct']
        if abs(low1 - low2) > tolerance:
            return False

        # First candle bearish, second candle bullish (classic pattern)
        c1_open = self.candles[-2, 1]
        c1_close = self.candles[-2, 2]
        c2_open = self.open
        c2_close = self.close

        first_bearish = c1_close < c1_open
        second_bullish = c2_close > c2_open

        return first_bearish and second_bullish

    def _is_tweezer_top(self) -> bool:
        """Check for tweezer top pattern"""
        # Get highs of last two candles
        high1 = self.candles[-2, 3]
        high2 = self.candles[-1, 3]

        # Check if highs are approximately equal
        tolerance = self.close * self.hp['tolerance_pct']
        if abs(high1 - high2) > tolerance:
            return False

        # First candle bullish, second candle bearish (classic pattern)
        c1_open = self.candles[-2, 1]
        c1_close = self.candles[-2, 2]
        c2_open = self.open
        c2_close = self.close

        first_bullish = c1_close > c1_open
        second_bearish = c2_close < c2_open

        return first_bullish and second_bearish

    def _in_downtrend(self) -> bool:
        ma = ta.sma(self.candles, period=self.hp['trend_period'])
        return self.close < ma

    def _in_uptrend(self) -> bool:
        ma = ta.sma(self.candles, period=self.hp['trend_period'])
        return self.close > ma

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_tweezer_bottom() and self._in_downtrend()

    def should_short(self) -> bool:
        return self._is_tweezer_top() and self._in_uptrend()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        tweezer_low = min(self.candles[-2, 4], self.low)
        stop = tweezer_low - (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        tweezer_high = max(self.candles[-2, 3], self.high)
        stop = tweezer_high + (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        pass
