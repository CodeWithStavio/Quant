"""
CNDL_009: Morning/Evening Star Strategy
---------------------------------------
Morning Star = 3-candle bullish reversal pattern.
Evening Star = 3-candle bearish reversal pattern.

Entry: Trade after pattern completion

Optimal Timeframes: 4h, 1d
Complexity: 5/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MorningEveningStar(Strategy):
    """Morning/Evening Star Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CNDL_009"
        self.strategy_name = "Morning Evening Star"
        self.complexity = 5
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'star_body_max', 'type': float, 'min': 0.1, 'max': 0.3, 'default': 0.2},
            {'name': 'recovery_min', 'type': float, 'min': 0.4, 'max': 0.7, 'default': 0.5},
            {'name': 'trend_period', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 4.5, 'default': 3.5},
        ]

    def _is_morning_star(self) -> bool:
        """Check for morning star pattern (3 candles ending at -1)"""
        # First candle (large bearish) at -3
        c1_open = self.candles[-3, 1]
        c1_close = self.candles[-3, 2]
        c1_body = abs(c1_close - c1_open)

        if c1_close >= c1_open:  # Not bearish
            return False

        # Second candle (small star) at -2
        c2_open = self.candles[-2, 1]
        c2_close = self.candles[-2, 2]
        c2_high = self.candles[-2, 3]
        c2_low = self.candles[-2, 4]
        c2_body = abs(c2_close - c2_open)
        c2_range = c2_high - c2_low

        # Star must be small
        if c2_range > 0:
            star_ratio = c2_body / c2_range
            if star_ratio > self.hp['star_body_max']:
                return False

        # Star gaps down from first candle
        if max(c2_open, c2_close) > c1_close:
            return False

        # Third candle (large bullish) at -1
        c3_open = self.open
        c3_close = self.close
        c3_body = abs(c3_close - c3_open)

        if c3_close <= c3_open:  # Not bullish
            return False

        # Third candle recovers into first candle body
        recovery_level = c1_close + (c1_body * self.hp['recovery_min'])
        return c3_close > recovery_level

    def _is_evening_star(self) -> bool:
        """Check for evening star pattern (3 candles ending at -1)"""
        # First candle (large bullish) at -3
        c1_open = self.candles[-3, 1]
        c1_close = self.candles[-3, 2]
        c1_body = abs(c1_close - c1_open)

        if c1_close <= c1_open:  # Not bullish
            return False

        # Second candle (small star) at -2
        c2_open = self.candles[-2, 1]
        c2_close = self.candles[-2, 2]
        c2_high = self.candles[-2, 3]
        c2_low = self.candles[-2, 4]
        c2_body = abs(c2_close - c2_open)
        c2_range = c2_high - c2_low

        # Star must be small
        if c2_range > 0:
            star_ratio = c2_body / c2_range
            if star_ratio > self.hp['star_body_max']:
                return False

        # Star gaps up from first candle
        if min(c2_open, c2_close) < c1_close:
            return False

        # Third candle (large bearish) at -1
        c3_open = self.open
        c3_close = self.close
        c3_body = abs(c3_close - c3_open)

        if c3_close >= c3_open:  # Not bearish
            return False

        # Third candle drops into first candle body
        recovery_level = c1_close - (c1_body * self.hp['recovery_min'])
        return c3_close < recovery_level

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
        return self._is_morning_star() and self._in_downtrend()

    def should_short(self) -> bool:
        return self._is_evening_star() and self._in_uptrend()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        # Stop below the star low
        star_low = self.candles[-2, 4]
        stop = min(star_low, entry - (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        # Stop above the star high
        star_high = self.candles[-2, 3]
        stop = max(star_high, entry + (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        pass
