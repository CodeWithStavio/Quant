"""
MOM_017: Know Sure Thing (KST) Strategy
---------------------------------------
Multi-timeframe momentum oscillator combining four ROCs.

Entry Long: KST crosses above signal line
Entry Short: KST crosses below signal line

Optimal Timeframes: 4h, 1d
Complexity: 5/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class KnowSureThing(Strategy):
    """Know Sure Thing Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_017"
        self.strategy_name = "KST"
        self.complexity = 5
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'roc1', 'type': int, 'min': 8, 'max': 12, 'default': 10},
            {'name': 'roc2', 'type': int, 'min': 12, 'max': 18, 'default': 15},
            {'name': 'roc3', 'type': int, 'min': 18, 'max': 25, 'default': 20},
            {'name': 'roc4', 'type': int, 'min': 25, 'max': 35, 'default': 30},
            {'name': 'sma1', 'type': int, 'min': 8, 'max': 12, 'default': 10},
            {'name': 'sma2', 'type': int, 'min': 8, 'max': 12, 'default': 10},
            {'name': 'sma3', 'type': int, 'min': 8, 'max': 12, 'default': 10},
            {'name': 'sma4', 'type': int, 'min': 12, 'max': 18, 'default': 15},
            {'name': 'signal_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 4.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _calculate_roc(self, close: np.ndarray, period: int) -> np.ndarray:
        """Calculate Rate of Change"""
        roc = np.zeros(len(close))
        for i in range(period, len(close)):
            if close[i-period] != 0:
                roc[i] = ((close[i] - close[i-period]) / close[i-period]) * 100
        return roc

    def _calculate_sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        sma = np.zeros(len(data))
        for i in range(period - 1, len(data)):
            sma[i] = np.mean(data[i-period+1:i+1])
        return sma

    def _calculate_kst(self, candles=None) -> tuple:
        """Calculate KST and Signal"""
        if candles is None:
            candles = self.candles

        close = candles[:, 2]

        # Calculate ROCs
        roc1 = self._calculate_roc(close, self.hp['roc1'])
        roc2 = self._calculate_roc(close, self.hp['roc2'])
        roc3 = self._calculate_roc(close, self.hp['roc3'])
        roc4 = self._calculate_roc(close, self.hp['roc4'])

        # Smooth ROCs
        sroc1 = self._calculate_sma(roc1, self.hp['sma1'])
        sroc2 = self._calculate_sma(roc2, self.hp['sma2'])
        sroc3 = self._calculate_sma(roc3, self.hp['sma3'])
        sroc4 = self._calculate_sma(roc4, self.hp['sma4'])

        # KST = RCMA1 x 1 + RCMA2 x 2 + RCMA3 x 3 + RCMA4 x 4
        kst = sroc1 * 1 + sroc2 * 2 + sroc3 * 3 + sroc4 * 4

        # Signal line
        signal = self._calculate_sma(kst, self.hp['signal_period'])

        return kst[-1], signal[-1]

    @property
    def kst(self) -> float:
        kst, signal = self._calculate_kst()
        return kst

    @property
    def kst_signal(self) -> float:
        kst, signal = self._calculate_kst()
        return signal

    @property
    def kst_prev(self) -> float:
        kst, signal = self._calculate_kst(self.candles[:-1])
        return kst

    @property
    def kst_signal_prev(self) -> float:
        kst, signal = self._calculate_kst(self.candles[:-1])
        return signal

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.kst_prev <= self.kst_signal_prev and self.kst > self.kst_signal

    def should_short(self) -> bool:
        return self.kst_prev >= self.kst_signal_prev and self.kst < self.kst_signal

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
        if self.is_long and self.kst < self.kst_signal:
            self.liquidate()
        elif self.is_short and self.kst > self.kst_signal:
            self.liquidate()
