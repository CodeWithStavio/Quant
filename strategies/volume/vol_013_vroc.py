"""
VOL_013: Volume Rate of Change (VROC) Strategy
----------------------------------------------
Rate of change in volume compared to N periods ago.
High VROC indicates unusual volume activity.

Entry Long: VROC spike with bullish price action
Entry Short: VROC spike with bearish price action

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolumeROC(Strategy):
    """Volume Rate of Change Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_013"
        self.strategy_name = "Volume ROC"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'vroc_period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'vroc_threshold', 'type': float, 'min': 50, 'max': 150, 'default': 100},
            {'name': 'ma_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_vroc(self, candles=None) -> float:
        """Calculate Volume Rate of Change"""
        if candles is None:
            candles = self.candles

        period = self.hp['vroc_period']
        volume = candles[:, 5]

        if len(volume) <= period:
            return 0

        current_vol = volume[-1]
        past_vol = volume[-period - 1]

        if past_vol == 0:
            return 0

        vroc = ((current_vol - past_vol) / past_vol) * 100

        return vroc

    @property
    def vroc(self) -> float:
        return self._calculate_vroc()

    @property
    def vroc_prev(self) -> float:
        return self._calculate_vroc(self.candles[:-1])

    @property
    def ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['ma_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def vroc_spike(self) -> bool:
        """Volume ROC above threshold"""
        return self.vroc > self.hp['vroc_threshold']

    @property
    def bullish_bar(self) -> bool:
        return self.close > self.open

    @property
    def bearish_bar(self) -> bool:
        return self.close < self.open

    @property
    def uptrend(self) -> bool:
        return self.close > self.ma

    @property
    def downtrend(self) -> bool:
        return self.close < self.ma

    def should_long(self) -> bool:
        return self.vroc_spike and self.bullish_bar and self.uptrend

    def should_short(self) -> bool:
        return self.vroc_spike and self.bearish_bar and self.downtrend

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
        # Exit on trend change
        if self.is_long and self.close < self.ma:
            self.liquidate()
        elif self.is_short and self.close > self.ma:
            self.liquidate()
