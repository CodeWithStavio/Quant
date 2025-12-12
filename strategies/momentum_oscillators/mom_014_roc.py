"""
MOM_014: Rate of Change (ROC) Strategy
--------------------------------------
ROC = ((Current Price - Price N periods ago) / Price N periods ago) * 100

Entry Long: ROC crosses above 0
Entry Short: ROC crosses below 0

Optimal Timeframes: 15m, 1h, 4h
Complexity: 2/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class RateOfChange(Strategy):
    """Rate of Change Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_014"
        self.strategy_name = "Rate of Change"
        self.complexity = 2
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 5, 'max': 20, 'default': 12},
            {'name': 'overbought', 'type': float, 'min': 3.0, 'max': 10.0, 'default': 5.0},
            {'name': 'oversold', 'type': float, 'min': -10.0, 'max': -3.0, 'default': -5.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 2.5},
        ]

    @property
    def roc(self) -> float:
        close = self.candles[:, 2]
        period = self.hp['period']
        old_price = close[-period-1]
        if old_price == 0:
            return 0
        return ((close[-1] - old_price) / old_price) * 100

    @property
    def roc_prev(self) -> float:
        close = self.candles[:, 2]
        period = self.hp['period']
        old_price = close[-period-2]
        if old_price == 0:
            return 0
        return ((close[-2] - old_price) / old_price) * 100

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # ROC crosses above 0 or rises from oversold
        zero_cross = self.roc_prev <= 0 and self.roc > 0
        from_oversold = self.roc_prev <= self.hp['oversold'] and self.roc > self.hp['oversold']
        return zero_cross or from_oversold

    def should_short(self) -> bool:
        # ROC crosses below 0 or falls from overbought
        zero_cross = self.roc_prev >= 0 and self.roc < 0
        from_overbought = self.roc_prev >= self.hp['overbought'] and self.roc < self.hp['overbought']
        return zero_cross or from_overbought

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
        if self.is_long and self.roc < 0:
            self.liquidate()
        elif self.is_short and self.roc > 0:
            self.liquidate()
