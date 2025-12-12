"""
OF_007: Iceberg Detector Strategy
---------------------------------
Detect iceberg order patterns through volume analysis.

Entry Long: Hidden buying detected
Entry Short: Hidden selling detected

Optimal Timeframes: 5m, 15m
Complexity: 7/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class IcebergDetector(Strategy):
    """Iceberg Detector Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "OF_007"
        self.strategy_name = "Iceberg Detector"
        self.complexity = 7
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 10, 'max': 25, 'default': 15},
            {'name': 'vol_consistency', 'type': float, 'min': 0.7, 'max': 0.9, 'default': 0.8},
            {'name': 'price_tolerance', 'type': float, 'min': 0.1, 'max': 0.3, 'default': 0.2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _detect_iceberg_buying(self) -> bool:
        """Detect iceberg buying (consistent volume at similar price)"""
        lookback = self.hp['lookback']

        # Check for consistent volume with stable/rising price
        volumes = self.candles[-lookback:, 5]
        closes = self.candles[-lookback:, 2]

        # Volume consistency (low variance)
        vol_mean = np.mean(volumes)
        vol_std = np.std(volumes)
        vol_consistent = (vol_std / vol_mean) < (1 - self.hp['vol_consistency'])

        # Price stability with slight upward bias
        price_range = (np.max(closes) - np.min(closes)) / np.mean(closes) * 100
        price_stable = price_range < self.hp['price_tolerance'] * 5

        # Trend bias
        price_rising = closes[-1] > closes[0]

        # Volume above average
        overall_avg = np.mean(self.candles[-50:-lookback, 5]) if len(self.candles) > 50 else vol_mean
        high_volume = vol_mean > overall_avg * 1.2

        return vol_consistent and price_stable and price_rising and high_volume

    def _detect_iceberg_selling(self) -> bool:
        """Detect iceberg selling (consistent volume with falling price)"""
        lookback = self.hp['lookback']

        volumes = self.candles[-lookback:, 5]
        closes = self.candles[-lookback:, 2]

        # Volume consistency
        vol_mean = np.mean(volumes)
        vol_std = np.std(volumes)
        vol_consistent = (vol_std / vol_mean) < (1 - self.hp['vol_consistency'])

        # Price stability with slight downward bias
        price_range = (np.max(closes) - np.min(closes)) / np.mean(closes) * 100
        price_stable = price_range < self.hp['price_tolerance'] * 5

        # Trend bias
        price_falling = closes[-1] < closes[0]

        # Volume above average
        overall_avg = np.mean(self.candles[-50:-lookback, 5]) if len(self.candles) > 50 else vol_mean
        high_volume = vol_mean > overall_avg * 1.2

        return vol_consistent and price_stable and price_falling and high_volume

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._detect_iceberg_buying()

    def should_short(self) -> bool:
        return self._detect_iceberg_selling()

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
        # Trail stop
        if self.is_long:
            ma = ta.sma(self.candles, period=10)
            if self.close < ma:
                self.liquidate()
        elif self.is_short:
            ma = ta.sma(self.candles, period=10)
            if self.close > ma:
                self.liquidate()
