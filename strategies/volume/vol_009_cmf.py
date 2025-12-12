"""
VOL_009: Chaikin Money Flow (CMF) Strategy
------------------------------------------
Marc Chaikin's indicator measuring buying/selling pressure.
CMF > 0 = buying pressure, CMF < 0 = selling pressure.

Entry Long: CMF crosses above zero
Entry Short: CMF crosses below zero

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class CMFStrategy(Strategy):
    """Chaikin Money Flow Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_009"
        self.strategy_name = "Chaikin Money Flow"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'cmf_period', 'type': int, 'min': 15, 'max': 25, 'default': 20},
            {'name': 'signal_threshold', 'type': float, 'min': 0.0, 'max': 0.1, 'default': 0.05},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_cmf(self, candles=None) -> float:
        """Calculate Chaikin Money Flow"""
        if candles is None:
            candles = self.candles

        period = self.hp['cmf_period']

        high = candles[:, 3]
        low = candles[:, 4]
        close = candles[:, 2]
        volume = candles[:, 5]

        # Money Flow Multiplier = [(Close - Low) - (High - Close)] / (High - Low)
        high_low_diff = high - low
        high_low_diff = np.where(high_low_diff == 0, 1, high_low_diff)

        mf_mult = ((close - low) - (high - close)) / high_low_diff

        # Money Flow Volume = MF Multiplier * Volume
        mf_vol = mf_mult * volume

        # CMF = Sum(MF Volume, n) / Sum(Volume, n)
        sum_mf_vol = np.sum(mf_vol[-period:])
        sum_vol = np.sum(volume[-period:])

        if sum_vol == 0:
            return 0

        return sum_mf_vol / sum_vol

    @property
    def cmf(self) -> float:
        return self._calculate_cmf()

    @property
    def cmf_prev(self) -> float:
        return self._calculate_cmf(self.candles[:-1])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def cmf_crossed_above_zero(self) -> bool:
        threshold = self.hp['signal_threshold']
        return self.cmf_prev <= threshold and self.cmf > threshold

    @property
    def cmf_crossed_below_zero(self) -> bool:
        threshold = -self.hp['signal_threshold']
        return self.cmf_prev >= threshold and self.cmf < threshold

    @property
    def cmf_positive(self) -> bool:
        return self.cmf > self.hp['signal_threshold']

    @property
    def cmf_negative(self) -> bool:
        return self.cmf < -self.hp['signal_threshold']

    def should_long(self) -> bool:
        return self.cmf_crossed_above_zero

    def should_short(self) -> bool:
        return self.cmf_crossed_below_zero

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
        # Exit on CMF reversal
        if self.is_long and self.cmf_negative:
            self.liquidate()
        elif self.is_short and self.cmf_positive:
            self.liquidate()
