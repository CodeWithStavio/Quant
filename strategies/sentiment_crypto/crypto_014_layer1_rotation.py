"""
CRYPTO_014: Layer 1 Rotation Strategy
-------------------------------------
Trade based on sector rotation patterns.

Entry Long: Strength emerging (outperformance vs recent history)
Entry Short: Weakness emerging (underperformance)

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class Layer1Rotation(Strategy):
    """Layer 1 Rotation Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_014"
        self.strategy_name = "Layer1 Rotation"
        self.complexity = 6
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'strength_threshold', 'type': float, 'min': 70, 'max': 85, 'default': 75},
            {'name': 'weakness_threshold', 'type': float, 'min': 15, 'max': 30, 'default': 25},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _calculate_relative_strength(self) -> float:
        """Calculate relative strength percentile vs own history"""
        lookback = self.hp['lookback']

        # Current performance (ROC)
        current_roc = ta.roc(self.candles, period=lookback // 2)

        # Historical ROC values
        roc_history = []
        for i in range(1, lookback):
            if len(self.candles) > lookback // 2 + i:
                roc = ta.roc(self.candles[:-i], period=lookback // 2)
                roc_history.append(roc)

        if not roc_history:
            return 50

        # Percentile of current ROC
        return np.sum(np.array(roc_history) < current_roc) / len(roc_history) * 100

    def _is_momentum_improving(self) -> bool:
        """Check if momentum is improving"""
        roc = ta.roc(self.candles, period=10)
        prev_roc = ta.roc(self.candles[:-1], period=10)
        return roc > prev_roc

    @property
    def relative_strength(self) -> float:
        return self._calculate_relative_strength()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Strong relative performance with improving momentum
        strong = self.relative_strength > self.hp['strength_threshold']
        improving = self._is_momentum_improving()
        return strong and improving

    def should_short(self) -> bool:
        # Weak relative performance with declining momentum
        weak = self.relative_strength < self.hp['weakness_threshold']
        declining = not self._is_momentum_improving()
        return weak and declining

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
        # Exit on strength change
        if self.is_long and self.relative_strength < 50:
            self.liquidate()
        elif self.is_short and self.relative_strength > 50:
            self.liquidate()
