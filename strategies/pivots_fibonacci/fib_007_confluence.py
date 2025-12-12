"""
FIB_007: Fibonacci Confluence Strategy
--------------------------------------
Multiple technical factors aligning at Fibonacci levels.
Fib + MA + Volume = high probability setup.

Entry: Confluence of signals at Fib level

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class FibonacciConfluence(Strategy):
    """Fibonacci Confluence Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "FIB_007"
        self.strategy_name = "Fibonacci Confluence"
        self.complexity = 5
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'swing_lookback', 'type': int, 'min': 30, 'max': 100, 'default': 50},
            {'name': 'ma_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'volume_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'volume_mult', 'type': float, 'min': 1.2, 'max': 2.0, 'default': 1.5},
            {'name': 'fib_tolerance', 'type': float, 'min': 0.003, 'max': 0.01, 'default': 0.005},
            {'name': 'min_confluence', 'type': int, 'min': 2, 'max': 4, 'default': 3},
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

        return levels

    @property
    def ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['ma_period'])

    @property
    def avg_volume(self) -> float:
        return np.mean(self.candles[-self.hp['volume_period']:, 5])

    @property
    def current_volume(self) -> float:
        return self.candles[-1, 5]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _count_bullish_confluence(self):
        """Count bullish confluence factors"""
        count = 0
        levels = self._calculate_fib_levels()
        tolerance = self.close * self.hp['fib_tolerance']

        # Factor 1: Near Fibonacci level
        for level in levels.values():
            if abs(self.close - level) < tolerance:
                count += 1
                break

        # Factor 2: Price above MA
        if self.close > self.ma:
            count += 1

        # Factor 3: Bullish candle
        if self.close > self.open:
            count += 1

        # Factor 4: Volume confirmation
        if self.current_volume > self.avg_volume * self.hp['volume_mult']:
            count += 1

        # Factor 5: Higher low pattern
        if self.low > self.candles[-2, 4]:
            count += 1

        return count

    def _count_bearish_confluence(self):
        """Count bearish confluence factors"""
        count = 0
        levels = self._calculate_fib_levels()
        tolerance = self.close * self.hp['fib_tolerance']

        # Factor 1: Near Fibonacci level
        for level in levels.values():
            if abs(self.close - level) < tolerance:
                count += 1
                break

        # Factor 2: Price below MA
        if self.close < self.ma:
            count += 1

        # Factor 3: Bearish candle
        if self.close < self.open:
            count += 1

        # Factor 4: Volume confirmation
        if self.current_volume > self.avg_volume * self.hp['volume_mult']:
            count += 1

        # Factor 5: Lower high pattern
        if self.high < self.candles[-2, 3]:
            count += 1

        return count

    def should_long(self) -> bool:
        return self._count_bullish_confluence() >= self.hp['min_confluence']

    def should_short(self) -> bool:
        return self._count_bearish_confluence() >= self.hp['min_confluence']

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
        # Exit when confluence disappears
        if self.is_long and self._count_bullish_confluence() < 2:
            self.liquidate()
        elif self.is_short and self._count_bearish_confluence() < 2:
            self.liquidate()
