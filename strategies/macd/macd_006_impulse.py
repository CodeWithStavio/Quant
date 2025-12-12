"""
MACD_006: Impulse MACD (Elder) Strategy
---------------------------------------
Alexander Elder's Impulse System combining EMA slope and MACD histogram.

Entry Long: Both EMA slope and MACD histogram are green (bullish)
Entry Short: Both EMA slope and MACD histogram are red (bearish)

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MACDImpulse(Strategy):
    """Impulse MACD (Elder) Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MACD_006"
        self.strategy_name = "Impulse MACD"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ema_period', 'type': int, 'min': 10, 'max': 20, 'default': 13},
            {'name': 'fast_period', 'type': int, 'min': 8, 'max': 15, 'default': 12},
            {'name': 'slow_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'signal_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    @property
    def ema(self) -> float:
        return ta.ema(self.candles, period=self.hp['ema_period'])

    @property
    def ema_prev(self) -> float:
        return ta.ema(self.candles[:-1], period=self.hp['ema_period'])

    @property
    def histogram(self) -> float:
        macd, signal, hist = ta.macd(
            self.candles,
            fast_period=self.hp['fast_period'],
            slow_period=self.hp['slow_period'],
            signal_period=self.hp['signal_period']
        )
        return hist

    @property
    def histogram_prev(self) -> float:
        macd, signal, hist = ta.macd(
            self.candles[:-1],
            fast_period=self.hp['fast_period'],
            slow_period=self.hp['slow_period'],
            signal_period=self.hp['signal_period']
        )
        return hist

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _ema_rising(self) -> bool:
        """EMA slope is positive"""
        return self.ema > self.ema_prev

    def _ema_falling(self) -> bool:
        """EMA slope is negative"""
        return self.ema < self.ema_prev

    def _histogram_rising(self) -> bool:
        """MACD histogram is rising"""
        return self.histogram > self.histogram_prev

    def _histogram_falling(self) -> bool:
        """MACD histogram is falling"""
        return self.histogram < self.histogram_prev

    def _impulse_green(self) -> bool:
        """Both EMA and histogram are bullish"""
        return self._ema_rising() and self._histogram_rising()

    def _impulse_red(self) -> bool:
        """Both EMA and histogram are bearish"""
        return self._ema_falling() and self._histogram_falling()

    def should_long(self) -> bool:
        return self._impulse_green() and self.close > self.ema

    def should_short(self) -> bool:
        return self._impulse_red() and self.close < self.ema

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
        # Exit when impulse turns red (for long) or green (for short)
        if self.is_long and self._impulse_red():
            self.liquidate()
        elif self.is_short and self._impulse_green():
            self.liquidate()
