"""
FIB_005: Auto Fibonacci Strategy
--------------------------------
Automatically detect swing points and draw Fibonacci.
Adaptive to current market structure.

Entry: Trade at auto-detected Fibonacci levels

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class AutoFibonacci(Strategy):
    """Auto Fibonacci Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "FIB_005"
        self.strategy_name = "Auto Fibonacci"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'pivot_left', 'type': int, 'min': 3, 'max': 10, 'default': 5},
            {'name': 'pivot_right', 'type': int, 'min': 3, 'max': 10, 'default': 5},
            {'name': 'fib_tolerance', 'type': float, 'min': 0.002, 'max': 0.01, 'default': 0.005},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _find_pivot_high(self, idx, left, right, highs):
        """Check if index is a pivot high"""
        if idx < left or idx + right >= len(highs):
            return False

        pivot_val = highs[idx]
        for i in range(1, left + 1):
            if highs[idx - i] >= pivot_val:
                return False
        for i in range(1, right + 1):
            if highs[idx + i] >= pivot_val:
                return False
        return True

    def _find_pivot_low(self, idx, left, right, lows):
        """Check if index is a pivot low"""
        if idx < left or idx + right >= len(lows):
            return False

        pivot_val = lows[idx]
        for i in range(1, left + 1):
            if lows[idx - i] <= pivot_val:
                return False
        for i in range(1, right + 1):
            if lows[idx + i] <= pivot_val:
                return False
        return True

    def _find_swing_points(self):
        """Find most recent significant swing high and low"""
        left = self.hp['pivot_left']
        right = self.hp['pivot_right']
        lookback = 100

        candles = self.candles[-lookback:]
        highs = candles[:, 3]
        lows = candles[:, 4]

        last_pivot_high = None
        last_pivot_low = None

        for i in range(len(candles) - right - 1, left, -1):
            if last_pivot_high is None and self._find_pivot_high(i, left, right, highs):
                last_pivot_high = highs[i]
            if last_pivot_low is None and self._find_pivot_low(i, left, right, lows):
                last_pivot_low = lows[i]
            if last_pivot_high and last_pivot_low:
                break

        if last_pivot_high is None:
            last_pivot_high = np.max(highs)
        if last_pivot_low is None:
            last_pivot_low = np.min(lows)

        return last_pivot_high, last_pivot_low

    def _calculate_auto_fib(self):
        """Calculate auto Fibonacci levels"""
        swing_high, swing_low = self._find_swing_points()
        range_size = swing_high - swing_low

        # Determine trend
        is_uptrend = self.close > (swing_high + swing_low) / 2

        levels = {}
        if is_uptrend:
            # Retracement from high
            levels['38.2'] = swing_high - 0.382 * range_size
            levels['50.0'] = swing_high - 0.500 * range_size
            levels['61.8'] = swing_high - 0.618 * range_size
        else:
            # Retracement from low
            levels['38.2'] = swing_low + 0.382 * range_size
            levels['50.0'] = swing_low + 0.500 * range_size
            levels['61.8'] = swing_low + 0.618 * range_size

        return levels, is_uptrend

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        levels, is_uptrend = self._calculate_auto_fib()
        if not is_uptrend:
            return False

        tolerance = self.close * self.hp['fib_tolerance']
        for level in levels.values():
            if abs(self.close - level) < tolerance and self.close > self.open:
                return True
        return False

    def should_short(self) -> bool:
        levels, is_uptrend = self._calculate_auto_fib()
        if is_uptrend:
            return False

        tolerance = self.close * self.hp['fib_tolerance']
        for level in levels.values():
            if abs(self.close - level) < tolerance and self.close < self.open:
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
