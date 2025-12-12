"""
CNDL_008: Harami Pattern Strategy
---------------------------------
Bullish harami = small green inside large red.
Bearish harami = small red inside large green.

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


class HaramiStrategy(Strategy):
    """Harami Pattern Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CNDL_008"
        self.strategy_name = "Harami Pattern"
        self.complexity = 3
        self.crypto_suitability = 7
        self.harami_detected = None  # 'bullish' or 'bearish'

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'body_ratio_max', 'type': float, 'min': 0.3, 'max': 0.6, 'default': 0.5},
            {'name': 'trend_period', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _is_bullish_harami(self, idx=-2) -> bool:
        """Check for bullish harami pattern at index"""
        # Mother candle (large bearish)
        mother_open = self.candles[idx-1, 1]
        mother_close = self.candles[idx-1, 2]
        mother_body = abs(mother_close - mother_open)

        if mother_close >= mother_open:  # Not bearish
            return False

        # Baby candle (small bullish)
        baby_open = self.candles[idx, 1]
        baby_close = self.candles[idx, 2]
        baby_body = abs(baby_close - baby_open)

        if baby_close <= baby_open:  # Not bullish
            return False

        # Baby body is inside mother body
        inside = baby_open > mother_close and baby_close < mother_open

        # Baby is significantly smaller
        if mother_body == 0:
            return False
        ratio = baby_body / mother_body

        return inside and ratio <= self.hp['body_ratio_max']

    def _is_bearish_harami(self, idx=-2) -> bool:
        """Check for bearish harami pattern at index"""
        # Mother candle (large bullish)
        mother_open = self.candles[idx-1, 1]
        mother_close = self.candles[idx-1, 2]
        mother_body = abs(mother_close - mother_open)

        if mother_close <= mother_open:  # Not bullish
            return False

        # Baby candle (small bearish)
        baby_open = self.candles[idx, 1]
        baby_close = self.candles[idx, 2]
        baby_body = abs(baby_close - baby_open)

        if baby_close >= baby_open:  # Not bearish
            return False

        # Baby body is inside mother body
        inside = baby_open < mother_close and baby_close > mother_open

        # Baby is significantly smaller
        if mother_body == 0:
            return False
        ratio = baby_body / mother_body

        return inside and ratio <= self.hp['body_ratio_max']

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
        # Bullish harami with confirmation candle
        if self._is_bullish_harami() and self._in_downtrend():
            if self.close > self.candles[-2, 3]:  # Confirm above harami high
                return True
        return False

    def should_short(self) -> bool:
        # Bearish harami with confirmation candle
        if self._is_bearish_harami() and self._in_uptrend():
            if self.close < self.candles[-2, 4]:  # Confirm below harami low
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
