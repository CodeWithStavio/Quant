"""
MOM_001: RSI Overbought/Oversold Strategy
-----------------------------------------
Classic RSI mean reversion at extreme levels.

Entry Long: RSI crosses above oversold level (30)
Entry Short: RSI crosses below overbought level (70)

Optimal Timeframes: 15m, 1h, 4h
Complexity: 2/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class RSIOverboughtOversold(Strategy):
    """RSI Overbought/Oversold Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_001"
        self.strategy_name = "RSI Overbought/Oversold"
        self.complexity = 2
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 7, 'max': 21, 'default': 14},
            {'name': 'overbought', 'type': int, 'min': 65, 'max': 85, 'default': 70},
            {'name': 'oversold', 'type': int, 'min': 15, 'max': 35, 'default': 30},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 4.0, 'default': 2.0},
        ]

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def rsi_prev(self) -> float:
        return ta.rsi(self.candles[:-1], period=self.hp['rsi_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _rsi_crossed_above_oversold(self) -> bool:
        return self.rsi_prev <= self.hp['oversold'] and self.rsi > self.hp['oversold']

    def _rsi_crossed_below_overbought(self) -> bool:
        return self.rsi_prev >= self.hp['overbought'] and self.rsi < self.hp['overbought']

    def should_long(self) -> bool:
        return self._rsi_crossed_above_oversold()

    def should_short(self) -> bool:
        return self._rsi_crossed_below_overbought()

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
        # Exit when RSI returns to neutral
        if self.is_long and self.rsi > 50:
            pass  # Let TP/SL handle
        elif self.is_short and self.rsi < 50:
            pass
