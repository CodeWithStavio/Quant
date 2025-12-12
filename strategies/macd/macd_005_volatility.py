"""
MACD_005: MACD-V (Volatility Normalized) Strategy
-------------------------------------------------
MACD divided by ATR for volatility-adjusted signals.

Entry Long: MACD-V crosses above signal
Entry Short: MACD-V crosses below signal

Optimal Timeframes: 15m, 1h, 4h
Complexity: 4/10
Crypto Suitability: 9/10 (great for volatile crypto markets)
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MACDVolatility(Strategy):
    """MACD-V (Volatility Normalized) Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MACD_005"
        self.strategy_name = "MACD-V"
        self.complexity = 4
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 8, 'max': 15, 'default': 12},
            {'name': 'slow_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'signal_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'atr_period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _get_macd_v(self, candles=None) -> tuple:
        """Get MACD-V (MACD / ATR)"""
        if candles is None:
            candles = self.candles

        macd, signal, hist = ta.macd(
            candles,
            fast_period=self.hp['fast_period'],
            slow_period=self.hp['slow_period'],
            signal_period=self.hp['signal_period']
        )
        atr_val = ta.atr(candles, period=self.hp['atr_period'])

        if atr_val == 0:
            return macd, signal

        macd_v = macd / atr_val
        signal_v = signal / atr_val

        return macd_v, signal_v

    @property
    def macd_v(self) -> float:
        macd_v, signal_v = self._get_macd_v()
        return macd_v

    @property
    def signal_v(self) -> float:
        macd_v, signal_v = self._get_macd_v()
        return signal_v

    @property
    def macd_v_prev(self) -> float:
        macd_v, signal_v = self._get_macd_v(self.candles[:-1])
        return macd_v

    @property
    def signal_v_prev(self) -> float:
        macd_v, signal_v = self._get_macd_v(self.candles[:-1])
        return signal_v

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.macd_v_prev <= self.signal_v_prev and self.macd_v > self.signal_v

    def should_short(self) -> bool:
        return self.macd_v_prev >= self.signal_v_prev and self.macd_v < self.signal_v

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
        if self.is_long and self.macd_v < self.signal_v:
            self.liquidate()
        elif self.is_short and self.macd_v > self.signal_v:
            self.liquidate()
