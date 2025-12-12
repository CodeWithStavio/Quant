"""
ONCHAIN_001: Accumulation Detector Strategy
--------------------------------------------
Detect accumulation patterns using price-volume analysis.

Entry Long: Accumulation phase detected
Entry Short: N/A (accumulation = bullish only)

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class AccumulationDetector(Strategy):
    """Accumulation Detector Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ONCHAIN_001"
        self.strategy_name = "Accumulation Detector"
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

    def _is_accumulation_phase(self) -> bool:
        """Detect accumulation: tight range with increasing volume"""
        lookback = self.hp['lookback']
        prices = self.candles[-lookback:, 2]  # Close prices
        volumes = self.candles[-lookback:, 5]

        # Check tight price range
        price_range = (np.max(prices) - np.min(prices)) / np.mean(prices) * 100
        tight_range = price_range < self.hp['price_range_pct']

        # Check increasing volume trend
        first_half_vol = np.mean(volumes[:lookback//2])
        second_half_vol = np.mean(volumes[lookback//2:])
        vol_increasing = second_half_vol > first_half_vol * self.hp['vol_increase']

        # Check volume on up days vs down days
        up_vol = 0
        down_vol = 0
        for i in range(-lookback, 0):
            if self.candles[i, 2] > self.candles[i, 1]:  # close > open
                up_vol += self.candles[i, 5]
            else:
                down_vol += self.candles[i, 5]

        buying_pressure = up_vol > down_vol * 1.2 if down_vol > 0 else True

        return tight_range and vol_increasing and buying_pressure

    def _is_breakout_from_accumulation(self) -> bool:
        """Detect breakout from accumulation"""
        lookback = self.hp['lookback']
        range_high = np.max(self.candles[-lookback-5:-5, 3])  # High of range

        # Current close above range high
        breakout = self.close > range_high

        # Volume confirmation
        avg_vol = np.mean(self.candles[-lookback:-1, 5])
        high_volume = self.candles[-1, 5] > avg_vol * 1.5

        return breakout and high_volume

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_accumulation_phase() or self._is_breakout_from_accumulation()

    def should_short(self) -> bool:
        return False  # Accumulation is bullish only

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        pass

    def update_position(self):
        # Exit on weakness
        rsi = ta.rsi(self.candles, period=14)
        if self.is_long and rsi > 70:
            self.liquidate()
