"""
FIB_006: Fibonacci + RSI Strategy
---------------------------------
Combine Fibonacci levels with RSI confirmation.
Enter at Fib levels when RSI confirms reversal.

Entry: Fib level + RSI oversold/overbought

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class FibonacciRSI(Strategy):
    """Fibonacci + RSI Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "FIB_006"
        self.strategy_name = "Fibonacci + RSI"
        self.complexity = 4
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'swing_lookback', 'type': int, 'min': 30, 'max': 100, 'default': 50},
            {'name': 'rsi_period', 'type': int, 'min': 10, 'max': 21, 'default': 14},
            {'name': 'rsi_oversold', 'type': float, 'min': 25, 'max': 35, 'default': 30},
            {'name': 'rsi_overbought', 'type': float, 'min': 65, 'max': 75, 'default': 70},
            {'name': 'fib_tolerance', 'type': float, 'min': 0.003, 'max': 0.01, 'default': 0.005},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_fib_levels(self):
        lookback = self.hp['swing_lookback']
        candles = self.candles[-lookback:]

        swing_high = np.max(candles[:, 3])
        swing_low = np.min(candles[:, 4])
        range_size = swing_high - swing_low

        levels = {
            '38.2': swing_low + 0.382 * range_size,
            '50.0': swing_low + 0.500 * range_size,
            '61.8': swing_low + 0.618 * range_size,
        }

        return levels, swing_high, swing_low

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def rsi_oversold(self) -> bool:
        return self.rsi < self.hp['rsi_oversold']

    @property
    def rsi_overbought(self) -> bool:
        return self.rsi > self.hp['rsi_overbought']

    def _near_fib_level(self):
        levels, swing_high, swing_low = self._calculate_fib_levels()
        tolerance = self.close * self.hp['fib_tolerance']

        for name, level in levels.items():
            if abs(self.close - level) < tolerance:
                return True, level
        return False, None

    def should_long(self) -> bool:
        near_fib, level = self._near_fib_level()
        return near_fib and self.rsi_oversold and self.close > self.open

    def should_short(self) -> bool:
        near_fib, level = self._near_fib_level()
        return near_fib and self.rsi_overbought and self.close < self.open

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
        if self.is_long and self.rsi_overbought:
            self.liquidate()
        elif self.is_short and self.rsi_oversold:
            self.liquidate()
