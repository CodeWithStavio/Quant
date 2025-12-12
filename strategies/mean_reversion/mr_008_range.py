"""
MR_008: Range Mean Reversion Strategy
-------------------------------------
Trade within established price ranges.

Entry Long: Price at range bottom
Entry Short: Price at range top

Optimal Timeframes: 15m, 1h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class RangeMeanReversion(Strategy):
    """Range Mean Reversion Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MR_008"
        self.strategy_name = "Range Mean Reversion"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'range_period', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'range_pct_max', 'type': float, 'min': 3.0, 'max': 8.0, 'default': 5.0},
            {'name': 'entry_zone', 'type': float, 'min': 0.1, 'max': 0.25, 'default': 0.15},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
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
        """Range as percentage of mid price"""
        if self.range_mid == 0:
            return float('inf')
        return ((self.range_high - self.range_low) / self.range_mid) * 100

    @property
    def position_in_range(self) -> float:
        """0 = at low, 1 = at high"""
        range_size = self.range_high - self.range_low
        if range_size == 0:
            return 0.5
        return (self.close - self.range_low) / range_size

    @property
    def in_range_market(self) -> bool:
        """Check if market is ranging (not trending)"""
        return self.range_pct <= self.hp['range_pct_max']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # At bottom of range in ranging market
        return self.in_range_market and self.position_in_range < self.hp['entry_zone']

    def should_short(self) -> bool:
        # At top of range in ranging market
        return self.in_range_market and self.position_in_range > (1 - self.hp['entry_zone'])

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.range_low - (self.atr * self.hp['atr_multiplier_sl'])
        target = self.range_mid
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = self.range_high + (self.atr * self.hp['atr_multiplier_sl'])
        target = self.range_mid
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        # Exit at range midpoint or if range breaks
        if self.is_long:
            if self.close >= self.range_mid or not self.in_range_market:
                self.liquidate()
        elif self.is_short:
            if self.close <= self.range_mid or not self.in_range_market:
                self.liquidate()
