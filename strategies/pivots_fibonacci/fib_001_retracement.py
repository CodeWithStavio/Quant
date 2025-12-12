"""
FIB_001: Fibonacci Retracement Strategy
---------------------------------------
Classic Fibonacci retracement levels.
23.6%, 38.2%, 50%, 61.8%, 78.6%

Entry: Bounce from Fibonacci retracement level

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class FibonacciRetracement(Strategy):
    """Fibonacci Retracement Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "FIB_001"
        self.strategy_name = "Fibonacci Retracement"
        self.complexity = 4
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'swing_lookback', 'type': int, 'min': 30, 'max': 100, 'default': 50},
            {'name': 'fib_tolerance', 'type': float, 'min': 0.002, 'max': 0.01, 'default': 0.005},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _find_swing_points(self):
        """Find swing high and low for Fibonacci"""
        lookback = self.hp['swing_lookback']
        candles = self.candles[-lookback:]

        swing_high = np.max(candles[:, 3])
        swing_low = np.min(candles[:, 4])

        # Determine trend direction
        high_idx = np.argmax(candles[:, 3])
        low_idx = np.argmin(candles[:, 4])

        # If high came before low, we're in a downtrend
        is_downtrend = high_idx < low_idx

        return swing_high, swing_low, is_downtrend

    def _calculate_fib_levels(self):
        """Calculate Fibonacci retracement levels"""
        swing_high, swing_low, is_downtrend = self._find_swing_points()
        range_size = swing_high - swing_low

        fib_levels = {
            '0.0': swing_low if is_downtrend else swing_high,
            '23.6': swing_low + 0.236 * range_size if is_downtrend else swing_high - 0.236 * range_size,
            '38.2': swing_low + 0.382 * range_size if is_downtrend else swing_high - 0.382 * range_size,
            '50.0': swing_low + 0.500 * range_size if is_downtrend else swing_high - 0.500 * range_size,
            '61.8': swing_low + 0.618 * range_size if is_downtrend else swing_high - 0.618 * range_size,
            '78.6': swing_low + 0.786 * range_size if is_downtrend else swing_high - 0.786 * range_size,
            '100.0': swing_high if is_downtrend else swing_low,
        }

        return fib_levels, is_downtrend

    @property
    def fib_levels(self) -> dict:
        levels, _ = self._calculate_fib_levels()
        return levels

    @property
    def is_downtrend(self) -> bool:
        _, is_down = self._calculate_fib_levels()
        return is_down

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _near_fib_level(self, fib_level_names=['38.2', '50.0', '61.8']) -> tuple:
        """Check if price is near a Fibonacci level"""
        tolerance = self.close * self.hp['fib_tolerance']
        levels = self.fib_levels

        for level_name in fib_level_names:
            level = levels[level_name]
            if abs(self.close - level) < tolerance:
                return True, level
        return False, None

    def should_long(self) -> bool:
        # Long on bounce from Fib level in uptrend (retracement complete)
        if self.is_downtrend:
            return False

        near, level = self._near_fib_level()
        if near and self.close > self.open:  # Bullish candle at Fib level
            return True
        return False

    def should_short(self) -> bool:
        # Short on bounce from Fib level in downtrend
        if not self.is_downtrend:
            return False

        near, level = self._near_fib_level()
        if near and self.close < self.open:  # Bearish candle at Fib level
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
