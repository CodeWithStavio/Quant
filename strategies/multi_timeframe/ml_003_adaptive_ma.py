"""
ML_003: Adaptive Moving Average Strategy
----------------------------------------
Moving average that adapts to market volatility.

Entry Long: Price crosses above adaptive MA
Entry Short: Price crosses below adaptive MA

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class AdaptiveMA(Strategy):
    """Adaptive Moving Average Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ML_003"
        self.strategy_name = "Adaptive MA"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 5, 'max': 12, 'default': 8},
            {'name': 'slow_period', 'type': int, 'min': 25, 'max': 50, 'default': 35},
            {'name': 'er_period', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _efficiency_ratio(self) -> float:
        """Calculate Kaufman's Efficiency Ratio"""
        period = self.hp['er_period']
        closes = self.candles[-period-1:, 2]

        # Direction: absolute change over period
        direction = abs(closes[-1] - closes[0])

        # Volatility: sum of absolute changes
        volatility = np.sum(np.abs(np.diff(closes)))

        if volatility == 0:
            return 0
        return direction / volatility

    def _adaptive_ma(self) -> float:
        """Calculate Kaufman Adaptive Moving Average (KAMA)"""
        er = self._efficiency_ratio()

        # Smoothing constants
        fast_sc = 2 / (self.hp['fast_period'] + 1)
        slow_sc = 2 / (self.hp['slow_period'] + 1)

        # Adaptive smoothing constant
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

        # Calculate KAMA (simplified using EMA as base)
        closes = self.candles[:, 2]
        kama = closes[-self.hp['slow_period']]  # Initialize

        for i in range(-self.hp['slow_period'] + 1, 0):
            kama = kama + sc * (closes[i] - kama)

        return kama

    @property
    def adaptive_ma(self) -> float:
        return self._adaptive_ma()

    @property
    def prev_adaptive_ma(self) -> float:
        """Calculate previous KAMA value"""
        # Use simplified calculation
        er = self._efficiency_ratio()
        fast_sc = 2 / (self.hp['fast_period'] + 1)
        slow_sc = 2 / (self.hp['slow_period'] + 1)
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

        closes = self.candles[:-1, 2]
        kama = closes[-self.hp['slow_period']]

        for i in range(-self.hp['slow_period'] + 1, 0):
            kama = kama + sc * (closes[i] - kama)

        return kama

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        prev_close = self.candles[-2, 2]
        return prev_close <= self.prev_adaptive_ma and self.close > self.adaptive_ma

    def should_short(self) -> bool:
        prev_close = self.candles[-2, 2]
        return prev_close >= self.prev_adaptive_ma and self.close < self.adaptive_ma

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
        if self.is_long and self.close < self.adaptive_ma:
            self.liquidate()
        elif self.is_short and self.close > self.adaptive_ma:
            self.liquidate()
