"""
BRK_006: ATR Breakout Strategy
------------------------------
Trade breakouts based on ATR-based price levels.

Entry Long: Price exceeds previous close + ATR multiplier
Entry Short: Price falls below previous close - ATR multiplier

Optimal Timeframes: 15m, 1h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ATRBreakoutStrategy(Strategy):
    """ATR Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BRK_006"
        self.strategy_name = "ATR Breakout"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'atr_period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'breakout_mult', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=self.hp['atr_period'])

    @property
    def prev_close(self) -> float:
        return self.candles[-2, 2]

    @property
    def upper_breakout(self) -> float:
        return self.prev_close + (self.atr * self.hp['breakout_mult'])

    @property
    def lower_breakout(self) -> float:
        return self.prev_close - (self.atr * self.hp['breakout_mult'])

    def should_long(self) -> bool:
        return self.close > self.upper_breakout

    def should_short(self) -> bool:
        return self.close < self.lower_breakout

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        target = entry + (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        target = entry - (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        pass
