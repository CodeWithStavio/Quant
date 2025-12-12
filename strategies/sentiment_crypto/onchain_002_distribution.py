"""
ONCHAIN_002: Distribution Detector Strategy
--------------------------------------------
Detect distribution patterns using price-volume analysis.

Entry Long: N/A (distribution = bearish only)
Entry Short: Distribution phase detected

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DistributionDetector(Strategy):
    """Distribution Detector Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ONCHAIN_002"
        self.strategy_name = "Distribution Detector"
        self.complexity = 6
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'price_range_pct', 'type': float, 'min': 3.0, 'max': 8.0, 'default': 5.0},
            {'name': 'vol_increase', 'type': float, 'min': 1.2, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _is_distribution_phase(self) -> bool:
        """Detect distribution: tight range at highs with selling volume"""
        lookback = self.hp['lookback']
        prices = self.candles[-lookback:, 2]
        volumes = self.candles[-lookback:, 5]

        # Check tight price range
        price_range = (np.max(prices) - np.min(prices)) / np.mean(prices) * 100
        tight_range = price_range < self.hp['price_range_pct']

        # Check increasing volume trend
        first_half_vol = np.mean(volumes[:lookback//2])
        second_half_vol = np.mean(volumes[lookback//2:])
        vol_increasing = second_half_vol > first_half_vol * self.hp['vol_increase']

        # Check volume on down days vs up days
        up_vol = 0
        down_vol = 0
        for i in range(-lookback, 0):
            if self.candles[i, 2] < self.candles[i, 1]:  # close < open
                down_vol += self.candles[i, 5]
            else:
                up_vol += self.candles[i, 5]

        selling_pressure = down_vol > up_vol * 1.2 if up_vol > 0 else True

        return tight_range and vol_increasing and selling_pressure

    def _is_breakdown_from_distribution(self) -> bool:
        """Detect breakdown from distribution"""
        lookback = self.hp['lookback']
        range_low = np.min(self.candles[-lookback-5:-5, 4])  # Low of range

        # Current close below range low
        breakdown = self.close < range_low

        # Volume confirmation
        avg_vol = np.mean(self.candles[-lookback:-1, 5])
        high_volume = self.candles[-1, 5] > avg_vol * 1.5

        return breakdown and high_volume

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return False  # Distribution is bearish only

    def should_short(self) -> bool:
        return self._is_distribution_phase() or self._is_breakdown_from_distribution()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        pass

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Exit on strength
        rsi = ta.rsi(self.candles, period=14)
        if self.is_short and rsi < 30:
            self.liquidate()
