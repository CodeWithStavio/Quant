"""
MACD_003: MACD Histogram Reversal Strategy
------------------------------------------
Trade reversals in MACD histogram direction.

Entry Long: Histogram turns from negative to positive
Entry Short: Histogram turns from positive to negative

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MACDHistogram(Strategy):
    """MACD Histogram Reversal Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MACD_003"
        self.strategy_name = "MACD Histogram"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 8, 'max': 15, 'default': 12},
            {'name': 'slow_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'signal_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'min_hist_change', 'type': float, 'min': 0.0001, 'max': 0.001, 'default': 0.0003},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 2.5},
        ]

    def _get_histogram(self, candles=None) -> float:
        if candles is None:
            candles = self.candles
        macd, signal, hist = ta.macd(
            candles,
            fast_period=self.hp['fast_period'],
            slow_period=self.hp['slow_period'],
            signal_period=self.hp['signal_period']
        )
        return hist

    @property
    def histogram(self) -> float:
        return self._get_histogram()

    @property
    def histogram_prev(self) -> float:
        return self._get_histogram(self.candles[:-1])

    @property
    def histogram_prev2(self) -> float:
        return self._get_histogram(self.candles[:-2])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _histogram_turning_up(self) -> bool:
        """Histogram was falling, now rising"""
        was_falling = self.histogram_prev < self.histogram_prev2
        now_rising = self.histogram > self.histogram_prev
        significant = abs(self.histogram - self.histogram_prev) > self.hp['min_hist_change']
        return was_falling and now_rising and significant

    def _histogram_turning_down(self) -> bool:
        """Histogram was rising, now falling"""
        was_rising = self.histogram_prev > self.histogram_prev2
        now_falling = self.histogram < self.histogram_prev
        significant = abs(self.histogram - self.histogram_prev) > self.hp['min_hist_change']
        return was_rising and now_falling and significant

    def should_long(self) -> bool:
        return self._histogram_turning_up() and self.histogram_prev < 0

    def should_short(self) -> bool:
        return self._histogram_turning_down() and self.histogram_prev > 0

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
        if self.is_long and self._histogram_turning_down():
            self.liquidate()
        elif self.is_short and self._histogram_turning_up():
            self.liquidate()
