"""
VOL_012: Ease of Movement (EMV) Strategy
----------------------------------------
Richard Arms' indicator showing price/volume relationship.
High positive = easy upward movement, high negative = easy downward.

Entry Long: EMV crosses above zero
Entry Short: EMV crosses below zero

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class EaseOfMovement(Strategy):
    """Ease of Movement Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_012"
        self.strategy_name = "Ease of Movement"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'emv_period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'divisor', 'type': float, 'min': 10000, 'max': 1000000, 'default': 100000},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_emv(self, candles=None) -> float:
        """Calculate Ease of Movement"""
        if candles is None:
            candles = self.candles

        high = candles[:, 3]
        low = candles[:, 4]
        volume = candles[:, 5]
        divisor = self.hp['divisor']

        # Distance Moved = ((High + Low) / 2) - ((High[1] + Low[1]) / 2)
        mid_point = (high + low) / 2
        distance = np.zeros(len(candles))
        for i in range(1, len(candles)):
            distance[i] = mid_point[i] - mid_point[i-1]

        # Box Ratio = (Volume / Divisor) / (High - Low)
        high_low_diff = high - low
        high_low_diff = np.where(high_low_diff == 0, 0.0001, high_low_diff)
        box_ratio = (volume / divisor) / high_low_diff

        # EMV = Distance / Box Ratio
        box_ratio = np.where(box_ratio == 0, 0.0001, box_ratio)
        emv = distance / box_ratio

        # Smooth with SMA
        period = self.hp['emv_period']
        smoothed = np.mean(emv[-period:])

        return smoothed

    @property
    def emv(self) -> float:
        return self._calculate_emv()

    @property
    def emv_prev(self) -> float:
        return self._calculate_emv(self.candles[:-1])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def emv_crossed_above_zero(self) -> bool:
        return self.emv_prev <= 0 and self.emv > 0

    @property
    def emv_crossed_below_zero(self) -> bool:
        return self.emv_prev >= 0 and self.emv < 0

    @property
    def emv_positive(self) -> bool:
        return self.emv > 0

    @property
    def emv_negative(self) -> bool:
        return self.emv < 0

    def should_long(self) -> bool:
        return self.emv_crossed_above_zero

    def should_short(self) -> bool:
        return self.emv_crossed_below_zero

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
        # Exit on EMV reversal
        if self.is_long and self.emv_negative:
            self.liquidate()
        elif self.is_short and self.emv_positive:
            self.liquidate()
