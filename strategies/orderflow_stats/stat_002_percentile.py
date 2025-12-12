"""
STAT_002: Percentile Rank Strategy
----------------------------------
Trade based on price percentile ranking.

Entry Long: Price at extreme low percentile
Entry Short: Price at extreme high percentile

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class PercentileRank(Strategy):
    """Percentile Rank Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "STAT_002"
        self.strategy_name = "Percentile Rank"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 50, 'max': 150, 'default': 100},
            {'name': 'low_percentile', 'type': float, 'min': 5, 'max': 20, 'default': 10},
            {'name': 'high_percentile', 'type': float, 'min': 80, 'max': 95, 'default': 90},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    @property
    def price_percentile(self) -> float:
        """Calculate price percentile over lookback"""
        lookback = self.hp['lookback']
        prices = self.candles[-lookback:, 2]
        return np.sum(prices < self.close) / len(prices) * 100

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.price_percentile < self.hp['low_percentile']

    def should_short(self) -> bool:
        return self.price_percentile > self.hp['high_percentile']

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Exit at median
        if self.is_long and self.price_percentile > 50:
            self.liquidate()
        elif self.is_short and self.price_percentile < 50:
            self.liquidate()
