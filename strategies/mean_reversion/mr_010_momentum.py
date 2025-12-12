"""
MR_010: Momentum Mean Reversion Strategy
----------------------------------------
Trade extreme momentum readings expecting reversion.

Entry Long: After extreme negative momentum
Entry Short: After extreme positive momentum

Optimal Timeframes: 15m, 1h
Complexity: 4/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MomentumMeanReversion(Strategy):
    """Momentum Mean Reversion Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MR_010"
        self.strategy_name = "Momentum Mean Reversion"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'mom_period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'roc_period', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'extreme_threshold', 'type': float, 'min': 3.0, 'max': 7.0, 'default': 5.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    @property
    def momentum(self) -> float:
        """Price momentum"""
        return ta.mom(self.candles, period=self.hp['mom_period'])

    @property
    def roc(self) -> float:
        """Rate of change as percentage"""
        return ta.roc(self.candles, period=self.hp['roc_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Extreme negative momentum (oversold momentum)
        return self.roc < -self.hp['extreme_threshold']

    def should_short(self) -> bool:
        # Extreme positive momentum (overbought momentum)
        return self.roc > self.hp['extreme_threshold']

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
        # Exit when momentum normalizes
        if self.is_long and self.roc > 0:
            self.liquidate()
        elif self.is_short and self.roc < 0:
            self.liquidate()
