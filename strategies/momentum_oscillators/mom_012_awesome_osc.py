"""
MOM_012: Awesome Oscillator Strategy
------------------------------------
Bill Williams' Awesome Oscillator - measures market momentum.
AO = SMA(5, Median Price) - SMA(34, Median Price)

Entry Long: AO crosses above 0 or saucer pattern
Entry Short: AO crosses below 0

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class AwesomeOscillator(Strategy):
    """Awesome Oscillator Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_012"
        self.strategy_name = "Awesome Oscillator"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 3, 'max': 8, 'default': 5},
            {'name': 'slow_period', 'type': int, 'min': 25, 'max': 50, 'default': 34},
            {'name': 'use_saucer', 'type': bool, 'default': True},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _calculate_ao(self, candles=None) -> np.ndarray:
        """Calculate Awesome Oscillator (sequential)"""
        if candles is None:
            candles = self.candles

        high = candles[:, 3]
        low = candles[:, 4]
        median = (high + low) / 2

        # Create temp candles with median price as close
        temp_candles = candles.copy()
        temp_candles[:, 2] = median

        fast_sma = ta.sma(temp_candles, period=self.hp['fast_period'], sequential=True)
        slow_sma = ta.sma(temp_candles, period=self.hp['slow_period'], sequential=True)

        return fast_sma - slow_sma

    @property
    def ao(self) -> float:
        return self._calculate_ao()[-1]

    @property
    def ao_prev(self) -> float:
        return self._calculate_ao()[-2]

    @property
    def ao_prev2(self) -> float:
        return self._calculate_ao()[-3]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _zero_cross_bullish(self) -> bool:
        """AO crosses above zero"""
        return self.ao_prev <= 0 and self.ao > 0

    def _zero_cross_bearish(self) -> bool:
        """AO crosses below zero"""
        return self.ao_prev >= 0 and self.ao < 0

    def _saucer_bullish(self) -> bool:
        """Bullish saucer pattern: AO > 0, red bar followed by green bar"""
        if not self.hp.get('use_saucer', True):
            return False
        return (self.ao > 0 and
                self.ao_prev < self.ao_prev2 and  # Previous bar was red (decreasing)
                self.ao > self.ao_prev)           # Current bar is green (increasing)

    def _saucer_bearish(self) -> bool:
        """Bearish saucer pattern: AO < 0, green bar followed by red bar"""
        if not self.hp.get('use_saucer', True):
            return False
        return (self.ao < 0 and
                self.ao_prev > self.ao_prev2 and  # Previous bar was green
                self.ao < self.ao_prev)           # Current bar is red

    def should_long(self) -> bool:
        return self._zero_cross_bullish() or self._saucer_bullish()

    def should_short(self) -> bool:
        return self._zero_cross_bearish() or self._saucer_bearish()

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
        if self.is_long and self._zero_cross_bearish():
            self.liquidate()
        elif self.is_short and self._zero_cross_bullish():
            self.liquidate()
