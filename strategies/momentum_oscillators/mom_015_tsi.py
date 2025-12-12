"""
MOM_015: True Strength Index (TSI) Strategy
-------------------------------------------
TSI uses double-smoothed momentum to identify trend and oversold/overbought.

Entry Long: TSI crosses above signal line when TSI < 0
Entry Short: TSI crosses below signal line when TSI > 0

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TrueStrengthIndex(Strategy):
    """True Strength Index Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_015"
        self.strategy_name = "TSI"
        self.complexity = 5
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'long_period', 'type': int, 'min': 20, 'max': 30, 'default': 25},
            {'name': 'short_period', 'type': int, 'min': 10, 'max': 15, 'default': 13},
            {'name': 'signal_period', 'type': int, 'min': 7, 'max': 15, 'default': 13},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _calculate_tsi(self, candles=None) -> tuple:
        """Calculate TSI and Signal line"""
        if candles is None:
            candles = self.candles

        close = candles[:, 2]
        long_p = self.hp['long_period']
        short_p = self.hp['short_period']
        sig_p = self.hp['signal_period']

        # Calculate price change
        pc = np.diff(close)
        pc = np.insert(pc, 0, 0)

        # Double smooth the price change
        pc_ema1 = self._ema(pc, long_p)
        pc_ema2 = self._ema(pc_ema1, short_p)

        # Double smooth the absolute price change
        abs_pc = np.abs(pc)
        abs_ema1 = self._ema(abs_pc, long_p)
        abs_ema2 = self._ema(abs_ema1, short_p)

        # TSI
        tsi = np.zeros(len(close))
        for i in range(len(close)):
            if abs_ema2[i] != 0:
                tsi[i] = 100 * (pc_ema2[i] / abs_ema2[i])

        # Signal line
        signal = self._ema(tsi, sig_p)

        return tsi[-1], signal[-1]

    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA of array"""
        alpha = 2 / (period + 1)
        ema = np.zeros(len(data))
        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        return ema

    @property
    def tsi(self) -> float:
        tsi, signal = self._calculate_tsi()
        return tsi

    @property
    def tsi_signal(self) -> float:
        tsi, signal = self._calculate_tsi()
        return signal

    @property
    def tsi_prev(self) -> float:
        tsi, signal = self._calculate_tsi(self.candles[:-1])
        return tsi

    @property
    def tsi_signal_prev(self) -> float:
        tsi, signal = self._calculate_tsi(self.candles[:-1])
        return signal

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # TSI crosses above signal when TSI < 0 (oversold)
        crossed = self.tsi_prev <= self.tsi_signal_prev and self.tsi > self.tsi_signal
        return crossed and self.tsi < 0

    def should_short(self) -> bool:
        # TSI crosses below signal when TSI > 0 (overbought)
        crossed = self.tsi_prev >= self.tsi_signal_prev and self.tsi < self.tsi_signal
        return crossed and self.tsi > 0

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
        # Exit on opposite crossover
        if self.is_long and self.tsi < self.tsi_signal:
            self.liquidate()
        elif self.is_short and self.tsi > self.tsi_signal:
            self.liquidate()
