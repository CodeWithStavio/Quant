"""
SC_002: Range Scalp Strategy
----------------------------
Scalp within tight price ranges.

Entry Long: At range bottom
Entry Short: At range top

Optimal Timeframes: 1m, 5m, 15m
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class RangeScalp(Strategy):
    """Range Scalp Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SC_002"
        self.strategy_name = "Range Scalp"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'range_period', 'type': int, 'min': 10, 'max': 25, 'default': 15},
            {'name': 'entry_zone', 'type': float, 'min': 0.1, 'max': 0.2, 'default': 0.15},
            {'name': 'max_range_pct', 'type': float, 'min': 0.5, 'max': 1.5, 'default': 1.0},
            {'name': 'tp_pct', 'type': float, 'min': 0.2, 'max': 0.5, 'default': 0.3},
            {'name': 'sl_pct', 'type': float, 'min': 0.15, 'max': 0.3, 'default': 0.2},
        ]

    @property
    def range_high(self) -> float:
        return np.max(self.candles[-self.hp['range_period']:, 3])

    @property
    def range_low(self) -> float:
        return np.min(self.candles[-self.hp['range_period']:, 4])

    @property
    def range_mid(self) -> float:
        return (self.range_high + self.range_low) / 2

    @property
    def range_pct(self) -> float:
        if self.range_mid == 0:
            return float('inf')
        return ((self.range_high - self.range_low) / self.range_mid) * 100

    @property
    def in_tight_range(self) -> bool:
        return self.range_pct <= self.hp['max_range_pct']

    @property
    def position_in_range(self) -> float:
        """0 = at low, 1 = at high"""
        range_size = self.range_high - self.range_low
        if range_size == 0:
            return 0.5
        return (self.close - self.range_low) / range_size

    def should_long(self) -> bool:
        # At bottom of tight range with reversal
        return (self.in_tight_range and
                self.position_in_range < self.hp['entry_zone'] and
                self.close > self.open)

    def should_short(self) -> bool:
        # At top of tight range with reversal
        return (self.in_tight_range and
                self.position_in_range > (1 - self.hp['entry_zone']) and
                self.close < self.open)

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry * (1 - self.hp['sl_pct'] / 100)
        target = min(self.range_mid, entry * (1 + self.hp['tp_pct'] / 100))
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry * (1 + self.hp['sl_pct'] / 100)
        target = max(self.range_mid, entry * (1 - self.hp['tp_pct'] / 100))
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        pass
