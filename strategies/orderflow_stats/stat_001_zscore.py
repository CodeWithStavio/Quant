"""
STAT_001: Z-Score Mean Reversion Strategy
-----------------------------------------
Trade based on z-score deviations from mean.

Entry Long: Z-score below negative threshold
Entry Short: Z-score above positive threshold

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ZScoreMeanReversion(Strategy):
    """Z-Score Mean Reversion Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "STAT_001"
        self.strategy_name = "Z-Score Mean Reversion"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 30, 'max': 80, 'default': 50},
            {'name': 'entry_zscore', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'exit_zscore', 'type': float, 'min': 0.3, 'max': 0.8, 'default': 0.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    @property
    def zscore(self) -> float:
        """Calculate current z-score"""
        lookback = self.hp['lookback']
        prices = self.candles[-lookback:, 2]
        mean = np.mean(prices)
        std = np.std(prices)
        if std == 0:
            return 0
        return (self.close - mean) / std

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.zscore < -self.hp['entry_zscore']

    def should_short(self) -> bool:
        return self.zscore > self.hp['entry_zscore']

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
        # Exit when z-score returns to normal
        if self.is_long and self.zscore > -self.hp['exit_zscore']:
            self.liquidate()
        elif self.is_short and self.zscore < self.hp['exit_zscore']:
            self.liquidate()
