"""
FIB_003: Fibonacci Clusters Strategy
------------------------------------
Multiple Fibonacci levels from different swings.
Confluence zones = stronger support/resistance.

Entry: Price reaches Fibonacci cluster zone

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class FibonacciClusters(Strategy):
    """Fibonacci Clusters Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "FIB_003"
        self.strategy_name = "Fibonacci Clusters"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'short_lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'long_lookback', 'type': int, 'min': 50, 'max': 150, 'default': 100},
            {'name': 'cluster_tolerance', 'type': float, 'min': 0.005, 'max': 0.02, 'default': 0.01},
            {'name': 'min_cluster_size', 'type': int, 'min': 2, 'max': 4, 'default': 2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _get_fib_levels_from_swing(self, lookback):
        candles = self.candles[-lookback:]
        swing_high = np.max(candles[:, 3])
        swing_low = np.min(candles[:, 4])
        range_size = swing_high - swing_low

        fib_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]
        levels = []

        for ratio in fib_ratios:
            levels.append(swing_low + ratio * range_size)
            levels.append(swing_high - ratio * range_size)

        return levels

    def _find_clusters(self):
        short_levels = self._get_fib_levels_from_swing(self.hp['short_lookback'])
        long_levels = self._get_fib_levels_from_swing(self.hp['long_lookback'])
        all_levels = short_levels + long_levels

        tolerance = self.close * self.hp['cluster_tolerance']
        clusters = []

        for level in all_levels:
            count = sum(1 for l in all_levels if abs(l - level) < tolerance)
            if count >= self.hp['min_cluster_size']:
                clusters.append((level, count))

        # Remove duplicates by averaging nearby clusters
        unique_clusters = []
        for level, count in sorted(clusters, key=lambda x: x[0]):
            if not unique_clusters or abs(level - unique_clusters[-1][0]) > tolerance:
                unique_clusters.append((level, count))

        return unique_clusters

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        clusters = self._find_clusters()
        tolerance = self.close * self.hp['cluster_tolerance']

        for level, strength in clusters:
            if self.low <= level <= self.close and abs(self.close - level) < tolerance:
                if self.close > self.open:  # Bullish
                    return True
        return False

    def should_short(self) -> bool:
        clusters = self._find_clusters()
        tolerance = self.close * self.hp['cluster_tolerance']

        for level, strength in clusters:
            if self.close <= level <= self.high and abs(self.close - level) < tolerance:
                if self.close < self.open:  # Bearish
                    return True
        return False

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
        pass
