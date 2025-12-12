"""
MR_005: Statistical Mean Reversion Strategy
-------------------------------------------
Trade based on statistical deviation from moving average.

Entry Long: Price significantly below MA
Entry Short: Price significantly above MA

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class StatisticalMeanReversion(Strategy):
    """Statistical Mean Reversion Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MR_005"
        self.strategy_name = "Statistical Mean Reversion"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ma_period', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'deviation_pct', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
            {'name': 'exit_deviation', 'type': float, 'min': 0.5, 'max': 1.5, 'default': 1.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    @property
    def ma(self) -> float:
        return ta.sma(self.candles, period=self.hp['ma_period'])

    @property
    def deviation_pct(self) -> float:
        """Calculate percentage deviation from MA"""
        if self.ma == 0:
            return 0
        return ((self.close - self.ma) / self.ma) * 100

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.deviation_pct < -self.hp['deviation_pct']

    def should_short(self) -> bool:
        return self.deviation_pct > self.hp['deviation_pct']

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        target = self.ma
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        target = self.ma
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        if self.is_long and self.deviation_pct > -self.hp['exit_deviation']:
            self.liquidate()
        elif self.is_short and self.deviation_pct < self.hp['exit_deviation']:
            self.liquidate()
