"""
MACD_001: Classic MACD Crossover Strategy
-----------------------------------------
Standard MACD line crossing signal line.

Entry Long: MACD crosses above Signal line
Entry Short: MACD crosses below Signal line

Optimal Timeframes: 15m, 1h, 4h
Complexity: 2/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MACDCrossover(Strategy):
    """Classic MACD Crossover Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MACD_001"
        self.strategy_name = "MACD Crossover"
        self.complexity = 2
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 8, 'max': 15, 'default': 12},
            {'name': 'slow_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'signal_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _get_macd(self, candles=None):
        """Get MACD, Signal, and Histogram"""
        if candles is None:
            candles = self.candles
        return ta.macd(
            candles,
            fast_period=self.hp['fast_period'],
            slow_period=self.hp['slow_period'],
            signal_period=self.hp['signal_period']
        )

    @property
    def macd_line(self) -> float:
        macd, signal, hist = self._get_macd()
        return macd

    @property
    def signal_line(self) -> float:
        macd, signal, hist = self._get_macd()
        return signal

    @property
    def histogram(self) -> float:
        macd, signal, hist = self._get_macd()
        return hist

    @property
    def macd_line_prev(self) -> float:
        macd, signal, hist = self._get_macd(self.candles[:-1])
        return macd

    @property
    def signal_line_prev(self) -> float:
        macd, signal, hist = self._get_macd(self.candles[:-1])
        return signal

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.macd_line_prev <= self.signal_line_prev and self.macd_line > self.signal_line

    def should_short(self) -> bool:
        return self.macd_line_prev >= self.signal_line_prev and self.macd_line < self.signal_line

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, entry + (self.atr * self.hp['atr_multiplier_tp'])),
            (0.5, entry + (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
        ]

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, entry - (self.atr * self.hp['atr_multiplier_tp'])),
            (0.5, entry - (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
        ]

    def update_position(self):
        # Exit on opposite crossover
        if self.is_long and self.macd_line < self.signal_line:
            self.liquidate()
        elif self.is_short and self.macd_line > self.signal_line:
            self.liquidate()
