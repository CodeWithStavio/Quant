"""
MA_001: Simple Moving Average Crossover Strategy
-------------------------------------------------
Classic dual SMA crossover system for trend following.

Entry Long: Fast SMA crosses above Slow SMA
Entry Short: Fast SMA crosses below Slow SMA
Exit: Opposite crossover or fixed TP/SL

Optimal Timeframes: 15m, 1h, 4h
Complexity: 2/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SMACrossover(Strategy):
    """Simple Moving Average Crossover Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_001"
        self.strategy_name = "SMA Crossover"
        self.complexity = 2
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 5, 'max': 50, 'default': 10},
            {'name': 'slow_period', 'type': int, 'min': 20, 'max': 200, 'default': 50},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 4.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 6.0, 'default': 3.0},
        ]

    @property
    def fast_sma(self) -> float:
        return ta.sma(self.candles, period=self.hp['fast_period'])

    @property
    def slow_sma(self) -> float:
        return ta.sma(self.candles, period=self.hp['slow_period'])

    @property
    def fast_sma_prev(self) -> float:
        return ta.sma(self.candles[:-1], period=self.hp['fast_period'])

    @property
    def slow_sma_prev(self) -> float:
        return ta.sma(self.candles[:-1], period=self.hp['slow_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _crossed_above(self) -> bool:
        """Check if fast SMA crossed above slow SMA"""
        return self.fast_sma_prev <= self.slow_sma_prev and self.fast_sma > self.slow_sma

    def _crossed_below(self) -> bool:
        """Check if fast SMA crossed below slow SMA"""
        return self.fast_sma_prev >= self.slow_sma_prev and self.fast_sma < self.slow_sma

    def should_long(self) -> bool:
        return self._crossed_above()

    def should_short(self) -> bool:
        return self._crossed_below()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02 / (self.hp['atr_multiplier_sl'] * self.atr / entry), entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, entry + (self.atr * self.hp['atr_multiplier_tp'])),
            (0.5, entry + (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
        ]

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02 / (self.hp['atr_multiplier_sl'] * self.atr / entry), entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, entry - (self.atr * self.hp['atr_multiplier_tp'])),
            (0.5, entry - (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
        ]

    def update_position(self):
        # Exit on opposite crossover
        if self.is_long and self._crossed_below():
            self.liquidate()
        elif self.is_short and self._crossed_above():
            self.liquidate()

    def filters(self) -> List:
        return [
            (self.atr > 0, "ATR must be positive"),
            (abs(self.fast_sma - self.slow_sma) > self.atr * 0.1, "MAs too close together"),
        ]
