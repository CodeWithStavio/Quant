"""
VOL_011: Force Index Strategy
-----------------------------
Alexander Elder's Force Index combines price and volume.
Force Index = Close Change * Volume

Entry Long: Force Index crosses above zero
Entry Short: Force Index crosses below zero

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ForceIndex(Strategy):
    """Force Index Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_011"
        self.strategy_name = "Force Index"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fi_period', 'type': int, 'min': 10, 'max': 20, 'default': 13},
            {'name': 'trend_ma_period', 'type': int, 'min': 20, 'max': 50, 'default': 26},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_force_index(self, candles=None) -> float:
        """Calculate smoothed Force Index"""
        if candles is None:
            candles = self.candles

        close = candles[:, 2]
        volume = candles[:, 5]

        # Raw Force Index = (Close - Close[1]) * Volume
        raw_fi = np.zeros(len(candles))
        for i in range(1, len(candles)):
            raw_fi[i] = (close[i] - close[i-1]) * volume[i]

        # EMA smoothing
        period = self.hp['fi_period']
        multiplier = 2 / (period + 1)
        ema = np.zeros(len(candles))
        ema[period] = np.mean(raw_fi[1:period+1])

        for i in range(period + 1, len(candles)):
            ema[i] = (raw_fi[i] * multiplier) + (ema[i-1] * (1 - multiplier))

        return ema[-1]

    @property
    def force_index(self) -> float:
        return self._calculate_force_index()

    @property
    def force_index_prev(self) -> float:
        return self._calculate_force_index(self.candles[:-1])

    @property
    def trend_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['trend_ma_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def fi_crossed_above_zero(self) -> bool:
        return self.force_index_prev <= 0 and self.force_index > 0

    @property
    def fi_crossed_below_zero(self) -> bool:
        return self.force_index_prev >= 0 and self.force_index < 0

    @property
    def uptrend(self) -> bool:
        return self.close > self.trend_ma

    @property
    def downtrend(self) -> bool:
        return self.close < self.trend_ma

    def should_long(self) -> bool:
        return self.fi_crossed_above_zero and self.uptrend

    def should_short(self) -> bool:
        return self.fi_crossed_below_zero and self.downtrend

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
        # Exit on Force Index reversal
        if self.is_long and self.force_index < 0:
            self.liquidate()
        elif self.is_short and self.force_index > 0:
            self.liquidate()
