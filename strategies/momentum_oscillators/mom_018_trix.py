"""
MOM_018: TRIX Strategy
----------------------
Triple smoothed momentum indicator - very smooth, filters noise.
TRIX = 1-period rate of change of triple EMA

Entry Long: TRIX crosses above signal line or zero
Entry Short: TRIX crosses below signal line or zero

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TRIXStrategy(Strategy):
    """TRIX Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_018"
        self.strategy_name = "TRIX"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 10, 'max': 20, 'default': 15},
            {'name': 'signal_period', 'type': int, 'min': 5, 'max': 12, 'default': 9},
            {'name': 'use_zero_cross', 'type': bool, 'default': False},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA of array"""
        alpha = 2 / (period + 1)
        ema = np.zeros(len(data))
        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        return ema

    def _calculate_trix(self, candles=None) -> tuple:
        """Calculate TRIX and Signal"""
        if candles is None:
            candles = self.candles

        close = candles[:, 2]
        period = self.hp['period']

        # Triple EMA
        ema1 = self._calculate_ema(close, period)
        ema2 = self._calculate_ema(ema1, period)
        ema3 = self._calculate_ema(ema2, period)

        # TRIX = 1-period ROC of triple EMA (percentage)
        trix = np.zeros(len(close))
        for i in range(1, len(close)):
            if ema3[i-1] != 0:
                trix[i] = ((ema3[i] - ema3[i-1]) / ema3[i-1]) * 100

        # Signal line
        signal = self._calculate_ema(trix, self.hp['signal_period'])

        return trix[-1], signal[-1]

    @property
    def trix(self) -> float:
        trix, signal = self._calculate_trix()
        return trix

    @property
    def trix_signal(self) -> float:
        trix, signal = self._calculate_trix()
        return signal

    @property
    def trix_prev(self) -> float:
        trix, signal = self._calculate_trix(self.candles[:-1])
        return trix

    @property
    def trix_signal_prev(self) -> float:
        trix, signal = self._calculate_trix(self.candles[:-1])
        return signal

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        if self.hp.get('use_zero_cross', False):
            return self.trix_prev <= 0 and self.trix > 0
        return self.trix_prev <= self.trix_signal_prev and self.trix > self.trix_signal

    def should_short(self) -> bool:
        if self.hp.get('use_zero_cross', False):
            return self.trix_prev >= 0 and self.trix < 0
        return self.trix_prev >= self.trix_signal_prev and self.trix < self.trix_signal

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
        if self.is_long and self.trix < self.trix_signal:
            self.liquidate()
        elif self.is_short and self.trix > self.trix_signal:
            self.liquidate()
