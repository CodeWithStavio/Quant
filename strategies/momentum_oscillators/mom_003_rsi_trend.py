"""
MOM_003: RSI Trend Following Strategy
-------------------------------------
Use RSI zones for trend following rather than mean reversion.

Entry Long: RSI > 50 and rising (bullish momentum zone)
Entry Short: RSI < 50 and falling (bearish momentum zone)

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class RSITrendFollowing(Strategy):
    """RSI Trend Following Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_003"
        self.strategy_name = "RSI Trend Following"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 7, 'max': 21, 'default': 14},
            {'name': 'bullish_zone_low', 'type': int, 'min': 40, 'max': 55, 'default': 50},
            {'name': 'bullish_zone_high', 'type': int, 'min': 70, 'max': 85, 'default': 80},
            {'name': 'bearish_zone_low', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'bearish_zone_high', 'type': int, 'min': 45, 'max': 55, 'default': 50},
            {'name': 'momentum_bars', 'type': int, 'min': 2, 'max': 5, 'default': 3},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def rsi_sequential(self) -> np.ndarray:
        return ta.rsi(self.candles, period=self.hp['rsi_period'], sequential=True)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _rsi_rising(self) -> bool:
        """Check if RSI is rising over momentum bars"""
        rsi = self.rsi_sequential
        bars = self.hp['momentum_bars']
        return all(rsi[-i] > rsi[-i-1] for i in range(1, bars + 1))

    def _rsi_falling(self) -> bool:
        """Check if RSI is falling over momentum bars"""
        rsi = self.rsi_sequential
        bars = self.hp['momentum_bars']
        return all(rsi[-i] < rsi[-i-1] for i in range(1, bars + 1))

    def _in_bullish_zone(self) -> bool:
        return self.hp['bullish_zone_low'] < self.rsi < self.hp['bullish_zone_high']

    def _in_bearish_zone(self) -> bool:
        return self.hp['bearish_zone_low'] < self.rsi < self.hp['bearish_zone_high']

    def should_long(self) -> bool:
        return self._in_bullish_zone() and self._rsi_rising()

    def should_short(self) -> bool:
        return self._in_bearish_zone() and self._rsi_falling()

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
        # Exit when momentum reverses
        if self.is_long and self.rsi < self.hp['bullish_zone_low']:
            self.liquidate()
        elif self.is_short and self.rsi > self.hp['bearish_zone_high']:
            self.liquidate()
