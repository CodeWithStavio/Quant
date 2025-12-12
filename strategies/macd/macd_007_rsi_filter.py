"""
MACD_007: MACD with RSI Filter Strategy
---------------------------------------
MACD signals confirmed by RSI direction.

Entry Long: MACD bullish cross AND RSI > 50
Entry Short: MACD bearish cross AND RSI < 50

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MACDRSIFilter(Strategy):
    """MACD with RSI Filter Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MACD_007"
        self.strategy_name = "MACD + RSI"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 8, 'max': 15, 'default': 12},
            {'name': 'slow_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'signal_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'rsi_period', 'type': int, 'min': 7, 'max': 21, 'default': 14},
            {'name': 'rsi_threshold', 'type': int, 'min': 45, 'max': 55, 'default': 50},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _get_macd(self, candles=None):
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
    def macd_line_prev(self) -> float:
        macd, signal, hist = self._get_macd(self.candles[:-1])
        return macd

    @property
    def signal_line_prev(self) -> float:
        macd, signal, hist = self._get_macd(self.candles[:-1])
        return signal

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _macd_bullish_cross(self) -> bool:
        return self.macd_line_prev <= self.signal_line_prev and self.macd_line > self.signal_line

    def _macd_bearish_cross(self) -> bool:
        return self.macd_line_prev >= self.signal_line_prev and self.macd_line < self.signal_line

    def should_long(self) -> bool:
        return self._macd_bullish_cross() and self.rsi > self.hp['rsi_threshold']

    def should_short(self) -> bool:
        return self._macd_bearish_cross() and self.rsi < self.hp['rsi_threshold']

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
        if self.is_long and (self._macd_bearish_cross() or self.rsi < 40):
            self.liquidate()
        elif self.is_short and (self._macd_bullish_cross() or self.rsi > 60):
            self.liquidate()
