"""
MA_003: DEMA/TEMA Crossover Strategy
------------------------------------
Double/Triple Exponential Moving Average for reduced lag trend following.

DEMA = 2*EMA - EMA(EMA)
TEMA = 3*EMA - 3*EMA(EMA) + EMA(EMA(EMA))

Entry Long: DEMA crosses above TEMA (or vice versa)
Entry Short: DEMA crosses below TEMA

Optimal Timeframes: 5m, 15m, 1h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DEMATEMACrossover(Strategy):
    """Double/Triple EMA Crossover Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_003"
        self.strategy_name = "DEMA-TEMA Crossover"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'dema_period', 'type': int, 'min': 5, 'max': 30, 'default': 10},
            {'name': 'tema_period', 'type': int, 'min': 15, 'max': 50, 'default': 21},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 2.5},
        ]

    def _calculate_dema(self, period: int, candles=None) -> float:
        """Calculate Double Exponential Moving Average"""
        if candles is None:
            candles = self.candles
        ema1 = ta.ema(candles, period=period)
        # Create temp candles with EMA values
        ema_candles = candles.copy()
        ema_candles[:, 2] = ta.ema(candles, period=period, sequential=True)  # Close column
        ema2 = ta.ema(ema_candles, period=period)
        return 2 * ema1 - ema2

    def _calculate_tema(self, period: int, candles=None) -> float:
        """Calculate Triple Exponential Moving Average"""
        if candles is None:
            candles = self.candles
        ema1 = ta.ema(candles, period=period)
        ema_candles = candles.copy()
        ema1_seq = ta.ema(candles, period=period, sequential=True)
        ema_candles[:, 2] = ema1_seq
        ema2 = ta.ema(ema_candles, period=period)
        ema2_seq = ta.ema(ema_candles, period=period, sequential=True)
        ema_candles[:, 2] = ema2_seq
        ema3 = ta.ema(ema_candles, period=period)
        return 3 * ema1 - 3 * ema2 + ema3

    @property
    def dema(self) -> float:
        return self._calculate_dema(self.hp['dema_period'])

    @property
    def tema(self) -> float:
        return self._calculate_tema(self.hp['tema_period'])

    @property
    def dema_prev(self) -> float:
        return self._calculate_dema(self.hp['dema_period'], self.candles[:-1])

    @property
    def tema_prev(self) -> float:
        return self._calculate_tema(self.hp['tema_period'], self.candles[:-1])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _bullish_cross(self) -> bool:
        return self.dema_prev <= self.tema_prev and self.dema > self.tema

    def _bearish_cross(self) -> bool:
        return self.dema_prev >= self.tema_prev and self.dema < self.tema

    def should_long(self) -> bool:
        return self._bullish_cross()

    def should_short(self) -> bool:
        return self._bearish_cross()

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
        if self.is_long and self._bearish_cross():
            self.liquidate()
        elif self.is_short and self._bullish_cross():
            self.liquidate()
