"""
MOM_008: Williams %R Strategy
-----------------------------
Williams %R oscillator for overbought/oversold conditions.
Range: -100 to 0 (not 0 to 100 like RSI)

Entry Long: %R crosses above -80 (from oversold)
Entry Short: %R crosses below -20 (from overbought)

Optimal Timeframes: 15m, 1h, 4h
Complexity: 2/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class WilliamsPercentR(Strategy):
    """Williams %R Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_008"
        self.strategy_name = "Williams %R"
        self.complexity = 2
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 7, 'max': 21, 'default': 14},
            {'name': 'overbought', 'type': int, 'min': -30, 'max': -10, 'default': -20},
            {'name': 'oversold', 'type': int, 'min': -90, 'max': -70, 'default': -80},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 4.0, 'default': 2.5},
        ]

    @property
    def williams_r(self) -> float:
        return ta.willr(self.candles, period=self.hp['period'])

    @property
    def williams_r_prev(self) -> float:
        return ta.willr(self.candles[:-1], period=self.hp['period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # %R crosses above -80 (from oversold)
        return self.williams_r_prev <= self.hp['oversold'] and self.williams_r > self.hp['oversold']

    def should_short(self) -> bool:
        # %R crosses below -20 (from overbought)
        return self.williams_r_prev >= self.hp['overbought'] and self.williams_r < self.hp['overbought']

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
        # Exit when reaching opposite extreme
        if self.is_long and self.williams_r > -20:
            self.liquidate()
        elif self.is_short and self.williams_r < -80:
            self.liquidate()
