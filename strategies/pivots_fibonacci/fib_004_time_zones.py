"""
FIB_004: Fibonacci Time Zones Strategy
--------------------------------------
Apply Fibonacci sequence to time intervals.
Expect significant moves at Fib time intervals.

Entry: Trade near Fibonacci time zones

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class FibonacciTimeZones(Strategy):
    """Fibonacci Time Zones Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "FIB_004"
        self.strategy_name = "Fibonacci Time Zones"
        self.complexity = 5
        self.crypto_suitability = 7
        self._last_swing_idx = None

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'swing_lookback', 'type': int, 'min': 30, 'max': 100, 'default': 50},
            {'name': 'time_tolerance', 'type': int, 'min': 1, 'max': 3, 'default': 2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _find_last_swing(self):
        """Find the most recent significant swing point"""
        lookback = self.hp['swing_lookback']
        candles = self.candles[-lookback:]

        # Find highest high and lowest low indices
        high_idx = np.argmax(candles[:, 3])
        low_idx = np.argmin(candles[:, 4])

        # Return the more recent one
        if high_idx > low_idx:
            return len(self.candles) - lookback + high_idx, True  # Recent swing high
        else:
            return len(self.candles) - lookback + low_idx, False  # Recent swing low

    def _get_fib_time_zones(self, start_idx):
        """Calculate Fibonacci time zone indices"""
        fib_sequence = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
        current_idx = len(self.candles) - 1
        bars_since_swing = current_idx - start_idx

        # Check if we're at a Fibonacci time zone
        tolerance = self.hp['time_tolerance']
        for fib in fib_sequence:
            if abs(bars_since_swing - fib) <= tolerance:
                return True, fib

        return False, 0

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def ma(self) -> float:
        return ta.ema(self.candles, period=20)

    def should_long(self) -> bool:
        swing_idx, was_swing_high = self._find_last_swing()
        at_fib_zone, _ = self._get_fib_time_zones(swing_idx)

        if at_fib_zone:
            # If last swing was high, expect potential reversal up
            if was_swing_high and self.close > self.ma and self.close > self.open:
                return True
            # If last swing was low, expect continuation up
            if not was_swing_high and self.close > self.ma and self.close > self.open:
                return True
        return False

    def should_short(self) -> bool:
        swing_idx, was_swing_high = self._find_last_swing()
        at_fib_zone, _ = self._get_fib_time_zones(swing_idx)

        if at_fib_zone:
            if not was_swing_high and self.close < self.ma and self.close < self.open:
                return True
            if was_swing_high and self.close < self.ma and self.close < self.open:
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
