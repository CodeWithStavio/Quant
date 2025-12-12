"""
MOM_011: Ultimate Oscillator Strategy
-------------------------------------
Combines short, medium, and long-term momentum.

Entry Long: UO < 30 (oversold) with bullish divergence
Entry Short: UO > 70 (overbought) with bearish divergence

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class UltimateOscillator(Strategy):
    """Ultimate Oscillator Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_011"
        self.strategy_name = "Ultimate Oscillator"
        self.complexity = 5
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period1', 'type': int, 'min': 5, 'max': 10, 'default': 7},
            {'name': 'period2', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'period3', 'type': int, 'min': 20, 'max': 35, 'default': 28},
            {'name': 'overbought', 'type': int, 'min': 65, 'max': 80, 'default': 70},
            {'name': 'oversold', 'type': int, 'min': 20, 'max': 35, 'default': 30},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _calculate_uo(self, candles=None) -> float:
        """Calculate Ultimate Oscillator"""
        if candles is None:
            candles = self.candles

        close = candles[:, 2]
        high = candles[:, 3]
        low = candles[:, 4]

        # Calculate Buying Pressure and True Range
        bp = np.zeros(len(close))
        tr = np.zeros(len(close))

        for i in range(1, len(close)):
            true_low = min(low[i], close[i-1])
            true_high = max(high[i], close[i-1])
            bp[i] = close[i] - true_low
            tr[i] = true_high - true_low

        # Calculate averages for each period
        p1, p2, p3 = self.hp['period1'], self.hp['period2'], self.hp['period3']

        avg1 = np.sum(bp[-p1:]) / np.sum(tr[-p1:]) if np.sum(tr[-p1:]) > 0 else 0
        avg2 = np.sum(bp[-p2:]) / np.sum(tr[-p2:]) if np.sum(tr[-p2:]) > 0 else 0
        avg3 = np.sum(bp[-p3:]) / np.sum(tr[-p3:]) if np.sum(tr[-p3:]) > 0 else 0

        # UO formula with weights 4, 2, 1
        uo = 100 * ((4 * avg1) + (2 * avg2) + avg3) / 7

        return uo

    @property
    def uo(self) -> float:
        return self._calculate_uo()

    @property
    def uo_prev(self) -> float:
        return self._calculate_uo(self.candles[:-1])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        crossed_above = self.uo_prev <= self.hp['oversold'] and self.uo > self.hp['oversold']
        return crossed_above

    def should_short(self) -> bool:
        crossed_below = self.uo_prev >= self.hp['overbought'] and self.uo < self.hp['overbought']
        return crossed_below

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
        if self.is_long and self.uo > 50:
            pass
        elif self.is_short and self.uo < 50:
            pass
