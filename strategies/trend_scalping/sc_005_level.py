"""
SC_005: Level Scalp Strategy
----------------------------
Scalp bounces off round number levels.

Entry Long: Bounce off support level
Entry Short: Rejection at resistance level

Optimal Timeframes: 1m, 5m, 15m
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class LevelScalp(Strategy):
    """Level Scalp Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SC_005"
        self.strategy_name = "Level Scalp"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'level_interval', 'type': float, 'min': 50, 'max': 500, 'default': 100},
            {'name': 'tolerance_pct', 'type': float, 'min': 0.05, 'max': 0.2, 'default': 0.1},
            {'name': 'tp_pct', 'type': float, 'min': 0.2, 'max': 0.5, 'default': 0.3},
            {'name': 'sl_pct', 'type': float, 'min': 0.15, 'max': 0.3, 'default': 0.2},
        ]

    def _nearest_level(self, price: float) -> float:
        """Find nearest round number level"""
        interval = self.hp['level_interval']
        return round(price / interval) * interval

    def _lower_level(self, price: float) -> float:
        """Find nearest level below price"""
        interval = self.hp['level_interval']
        return (price // interval) * interval

    def _upper_level(self, price: float) -> float:
        """Find nearest level above price"""
        interval = self.hp['level_interval']
        return ((price // interval) + 1) * interval

    @property
    def near_support(self) -> bool:
        """Check if price is near a support level"""
        support = self._lower_level(self.close)
        tolerance = self.close * (self.hp['tolerance_pct'] / 100)
        return abs(self.low - support) <= tolerance

    @property
    def near_resistance(self) -> bool:
        """Check if price is near a resistance level"""
        resistance = self._upper_level(self.close)
        tolerance = self.close * (self.hp['tolerance_pct'] / 100)
        return abs(self.high - resistance) <= tolerance

    def should_long(self) -> bool:
        # Bounce off support level
        return self.near_support and self.close > self.open

    def should_short(self) -> bool:
        # Rejection at resistance level
        return self.near_resistance and self.close < self.open

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry * (1 - self.hp['sl_pct'] / 100)
        target = entry * (1 + self.hp['tp_pct'] / 100)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry * (1 + self.hp['sl_pct'] / 100)
        target = entry * (1 - self.hp['tp_pct'] / 100)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        pass
