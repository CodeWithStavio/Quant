"""
OF_003: Absorption Detector Strategy
------------------------------------
Detect volume absorption at key levels.

Entry Long: Selling absorbed (support holding)
Entry Short: Buying absorbed (resistance holding)

Optimal Timeframes: 5m, 15m
Complexity: 7/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class AbsorptionDetector(Strategy):
    """Absorption Detector Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "OF_003"
        self.strategy_name = "Absorption Detector"
        self.complexity = 7
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'volume_spike', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'price_tolerance', 'type': float, 'min': 0.2, 'max': 0.5, 'default': 0.3},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _is_selling_absorbed(self) -> bool:
        """Detect if selling is being absorbed at support"""
        lookback = self.hp['lookback']
        avg_vol = np.mean(self.candles[-lookback:-1, 5])

        # Look for high volume with small range near recent lows
        recent_low = np.min(self.candles[-lookback:, 4])
        near_low = self.close < recent_low * (1 + self.hp['price_tolerance'] / 100)

        # High volume but price held
        high_volume = self.candles[-1, 5] > avg_vol * self.hp['volume_spike']
        small_range = (self.high - self.low) < (self.atr * 0.5)

        # Close near high of candle (rejection of lows)
        close_near_high = (self.close - self.low) > (self.high - self.low) * 0.7

        return near_low and high_volume and (small_range or close_near_high)

    def _is_buying_absorbed(self) -> bool:
        """Detect if buying is being absorbed at resistance"""
        lookback = self.hp['lookback']
        avg_vol = np.mean(self.candles[-lookback:-1, 5])

        # Look for high volume with small range near recent highs
        recent_high = np.max(self.candles[-lookback:, 3])
        near_high = self.close > recent_high * (1 - self.hp['price_tolerance'] / 100)

        # High volume but price held
        high_volume = self.candles[-1, 5] > avg_vol * self.hp['volume_spike']
        small_range = (self.high - self.low) < (self.atr * 0.5)

        # Close near low of candle (rejection of highs)
        close_near_low = (self.high - self.close) > (self.high - self.low) * 0.7

        return near_high and high_volume and (small_range or close_near_low)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_selling_absorbed()

    def should_short(self) -> bool:
        return self._is_buying_absorbed()

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
        # Trail with ATR
        if self.is_long:
            trail = self.close - self.atr
            if trail > self.average_entry_price:
                self.stop_loss = self.position.qty, trail
        elif self.is_short:
            trail = self.close + self.atr
            if trail < self.average_entry_price:
                self.stop_loss = self.position.qty, trail
