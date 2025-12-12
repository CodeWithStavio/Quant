"""
MR_002: RSI Mean Reversion Strategy
-----------------------------------
Trade RSI extremes expecting reversion.

Entry Long: RSI below oversold level
Entry Short: RSI above overbought level

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class RSIMeanReversion(Strategy):
    """RSI Mean Reversion Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MR_002"
        self.strategy_name = "RSI Mean Reversion"
        self.complexity = 3
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 7, 'max': 21, 'default': 14},
            {'name': 'oversold', 'type': int, 'min': 20, 'max': 35, 'default': 30},
            {'name': 'overbought', 'type': int, 'min': 65, 'max': 80, 'default': 70},
            {'name': 'exit_level', 'type': int, 'min': 45, 'max': 55, 'default': 50},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def prev_rsi(self) -> float:
        return ta.rsi(self.candles[:-1], period=self.hp['rsi_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # RSI crosses above oversold level (reversal confirmation)
        return self.prev_rsi < self.hp['oversold'] and self.rsi > self.hp['oversold']

    def should_short(self) -> bool:
        # RSI crosses below overbought level (reversal confirmation)
        return self.prev_rsi > self.hp['overbought'] and self.rsi < self.hp['overbought']

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Exit when RSI reaches neutral zone
        if self.is_long and self.rsi >= self.hp['exit_level']:
            self.liquidate()
        elif self.is_short and self.rsi <= self.hp['exit_level']:
            self.liquidate()
