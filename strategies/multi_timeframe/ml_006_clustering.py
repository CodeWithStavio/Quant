"""
ML_006: Clustering Zones Strategy
---------------------------------
Identify price clustering zones as support/resistance.

Entry Long: Price bounces from cluster support
Entry Short: Price rejects from cluster resistance

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ClusteringZones(Strategy):
    """Clustering Zones Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ML_006"
        self.strategy_name = "Clustering Zones"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 80, 'max': 150, 'default': 100},
            {'name': 'num_bins', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'cluster_threshold', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _find_price_clusters(self) -> List[dict]:
        """Find price levels with high activity (clusters)"""
        lookback = self.hp['lookback']
        num_bins = self.hp['num_bins']

        prices = self.candles[-lookback:, 2]  # Close prices
        min_price = np.min(prices)
        max_price = np.max(prices)

        if max_price == min_price:
            return []

        bin_width = (max_price - min_price) / num_bins
        bins = np.zeros(num_bins)

        # Count prices in each bin
        for price in prices:
            bin_idx = int((price - min_price) / bin_width)
            bin_idx = min(bin_idx, num_bins - 1)
            bins[bin_idx] += 1

        avg_count = np.mean(bins)
        clusters = []

        for i, count in enumerate(bins):
            if count > avg_count * self.hp['cluster_threshold']:
                level = min_price + (i + 0.5) * bin_width
                clusters.append({
                    'level': level,
                    'strength': count / avg_count
                })

        return clusters

    @property
    def nearest_support(self) -> float:
        """Find nearest cluster below current price"""
        clusters = self._find_price_clusters()
        supports = [c['level'] for c in clusters if c['level'] < self.close]
        return max(supports) if supports else 0

    @property
    def nearest_resistance(self) -> float:
        """Find nearest cluster above current price"""
        clusters = self._find_price_clusters()
        resistances = [c['level'] for c in clusters if c['level'] > self.close]
        return min(resistances) if resistances else float('inf')

    @property
    def at_support(self) -> bool:
        support = self.nearest_support
        if support == 0:
            return False
        tolerance = self.close * 0.005
        return abs(self.low - support) <= tolerance

    @property
    def at_resistance(self) -> bool:
        resistance = self.nearest_resistance
        if resistance == float('inf'):
            return False
        tolerance = self.close * 0.005
        return abs(self.high - resistance) <= tolerance

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.at_support and self.close > self.open

    def should_short(self) -> bool:
        return self.at_resistance and self.close < self.open

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        support = self.nearest_support
        stop = support - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        resistance = self.nearest_resistance
        stop = resistance + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        pass
