"""
FIB_002: Fibonacci Extension Strategy
-------------------------------------
Fibonacci extension levels for profit targets.
127.2%, 161.8%, 200%, 261.8%

Entry: On retracement, target extensions

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class FibonacciExtension(Strategy):
    """Fibonacci Extension Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "FIB_002"
        self.strategy_name = "Fibonacci Extension"
        self.complexity = 4
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'swing_lookback', 'type': int, 'min': 30, 'max': 100, 'default': 50},
            {'name': 'retracement_level', 'type': float, 'min': 0.382, 'max': 0.618, 'default': 0.5},
            {'name': 'extension_target', 'type': float, 'min': 1.272, 'max': 1.618, 'default': 1.272},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    def _find_swing_points(self):
        lookback = self.hp['swing_lookback']
        candles = self.candles[-lookback:]

        swing_high = np.max(candles[:, 3])
        swing_low = np.min(candles[:, 4])

        high_idx = np.argmax(candles[:, 3])
        low_idx = np.argmin(candles[:, 4])

        is_uptrend = low_idx < high_idx

        return swing_high, swing_low, is_uptrend

    def _calculate_levels(self):
        swing_high, swing_low, is_uptrend = self._find_swing_points()
        range_size = swing_high - swing_low
        retracement = self.hp['retracement_level']
        extension = self.hp['extension_target']

        if is_uptrend:
            # After upswing, expect retracement down then extension up
            retracement_level = swing_high - (retracement * range_size)
            extension_level = swing_high + ((extension - 1) * range_size)
        else:
            # After downswing, expect retracement up then extension down
            retracement_level = swing_low + (retracement * range_size)
            extension_level = swing_low - ((extension - 1) * range_size)

        return retracement_level, extension_level, is_uptrend

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        retracement, extension, is_uptrend = self._calculate_levels()
        if not is_uptrend:
            return False

        # Look for bounce from retracement level
        tolerance = self.close * 0.005
        if abs(self.close - retracement) < tolerance and self.close > self.open:
            return True
        return False

    def should_short(self) -> bool:
        retracement, extension, is_uptrend = self._calculate_levels()
        if is_uptrend:
            return False

        tolerance = self.close * 0.005
        if abs(self.close - retracement) < tolerance and self.close < self.open:
            return True
        return False

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        retracement, extension, _ = self._calculate_levels()
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, extension

    def go_short(self):
        retracement, extension, _ = self._calculate_levels()
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, extension

    def update_position(self):
        pass
