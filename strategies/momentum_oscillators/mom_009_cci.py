"""
MOM_009: CCI (Commodity Channel Index) Strategy
-----------------------------------------------
CCI measures deviation from statistical mean.

Entry Long: CCI crosses above -100 (from oversold)
Entry Short: CCI crosses below +100 (from overbought)

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class CCIStrategy(Strategy):
    """CCI Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_009"
        self.strategy_name = "CCI"
        self.complexity = 3
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'overbought', 'type': int, 'min': 80, 'max': 150, 'default': 100},
            {'name': 'oversold', 'type': int, 'min': -150, 'max': -80, 'default': -100},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    @property
    def cci(self) -> float:
        return ta.cci(self.candles, period=self.hp['period'])

    @property
    def cci_prev(self) -> float:
        return ta.cci(self.candles[:-1], period=self.hp['period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.cci_prev <= self.hp['oversold'] and self.cci > self.hp['oversold']

    def should_short(self) -> bool:
        return self.cci_prev >= self.hp['overbought'] and self.cci < self.hp['overbought']

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
        if self.is_long and self.cci > 100:
            self.liquidate()
        elif self.is_short and self.cci < -100:
            self.liquidate()
