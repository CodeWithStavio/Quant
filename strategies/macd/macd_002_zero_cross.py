"""
MACD_002: MACD Zero Line Cross Strategy
---------------------------------------
Trade MACD crossing the zero line for trend confirmation.

Entry Long: MACD crosses above 0
Entry Short: MACD crosses below 0

Optimal Timeframes: 1h, 4h
Complexity: 2/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MACDZeroCross(Strategy):
    """MACD Zero Line Cross Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MACD_002"
        self.strategy_name = "MACD Zero Cross"
        self.complexity = 2
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 8, 'max': 15, 'default': 12},
            {'name': 'slow_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'signal_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 4.0, 'default': 2.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 6.0, 'default': 4.0},
        ]

    @property
    def macd_line(self) -> float:
        macd, signal, hist = ta.macd(
            self.candles,
            fast_period=self.hp['fast_period'],
            slow_period=self.hp['slow_period'],
            signal_period=self.hp['signal_period']
        )
        return macd

    @property
    def macd_line_prev(self) -> float:
        macd, signal, hist = ta.macd(
            self.candles[:-1],
            fast_period=self.hp['fast_period'],
            slow_period=self.hp['slow_period'],
            signal_period=self.hp['signal_period']
        )
        return macd

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.macd_line_prev <= 0 and self.macd_line > 0

    def should_short(self) -> bool:
        return self.macd_line_prev >= 0 and self.macd_line < 0

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
        if self.is_long and self.macd_line < 0:
            self.liquidate()
        elif self.is_short and self.macd_line > 0:
            self.liquidate()
