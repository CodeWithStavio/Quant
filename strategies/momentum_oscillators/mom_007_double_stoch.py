"""
MOM_007: Double Stochastic Strategy
-----------------------------------
Stochastic of Stochastic for ultra-sensitive momentum detection.

Entry Long: Double Stochastic crosses above 20
Entry Short: Double Stochastic crosses below 80

Optimal Timeframes: 5m, 15m
Complexity: 5/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DoubleStochastic(Strategy):
    """Double Stochastic Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_007"
        self.strategy_name = "Double Stochastic"
        self.complexity = 5
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 5, 'max': 21, 'default': 10},
            {'name': 'smooth', 'type': int, 'min': 1, 'max': 5, 'default': 3},
            {'name': 'overbought', 'type': int, 'min': 75, 'max': 90, 'default': 80},
            {'name': 'oversold', 'type': int, 'min': 10, 'max': 25, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 4.0, 'default': 2.0},
        ]

    def _calculate_double_stoch(self, candles=None) -> np.ndarray:
        """Calculate Double Stochastic"""
        if candles is None:
            candles = self.candles

        close = candles[:, 2]
        high = candles[:, 3]
        low = candles[:, 4]
        period = self.hp['period']

        # First Stochastic
        stoch1 = np.zeros(len(close))
        for i in range(period - 1, len(close)):
            low_n = np.min(low[i-period+1:i+1])
            high_n = np.max(high[i-period+1:i+1])
            if high_n - low_n > 0:
                stoch1[i] = ((close[i] - low_n) / (high_n - low_n)) * 100

        # Second Stochastic (of first)
        stoch2 = np.zeros(len(stoch1))
        for i in range(period - 1, len(stoch1)):
            low_n = np.min(stoch1[i-period+1:i+1])
            high_n = np.max(stoch1[i-period+1:i+1])
            if high_n - low_n > 0:
                stoch2[i] = ((stoch1[i] - low_n) / (high_n - low_n)) * 100

        # Smooth
        smooth = self.hp['smooth']
        result = np.convolve(stoch2, np.ones(smooth)/smooth, mode='same')

        return result

    @property
    def double_stoch(self) -> float:
        return self._calculate_double_stoch()[-1]

    @property
    def double_stoch_prev(self) -> float:
        return self._calculate_double_stoch()[-2]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.double_stoch_prev <= self.hp['oversold'] and self.double_stoch > self.hp['oversold']

    def should_short(self) -> bool:
        return self.double_stoch_prev >= self.hp['overbought'] and self.double_stoch < self.hp['overbought']

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
        if self.is_long and self.double_stoch > 80:
            self.liquidate()
        elif self.is_short and self.double_stoch < 20:
            self.liquidate()
