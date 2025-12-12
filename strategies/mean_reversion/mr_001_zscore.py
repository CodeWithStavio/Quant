"""
MR_001: Z-Score Mean Reversion Strategy
---------------------------------------
Trade when price deviates significantly from mean using z-score.

Entry Long: Z-score below -2 (oversold)
Entry Short: Z-score above +2 (overbought)

Optimal Timeframes: 15m, 1h
Complexity: 4/10
Crypto Suitability: 7/10
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
        self.strategy_id = "MR_001"
        self.strategy_name = "Z-Score Mean Reversion"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 15, 'max': 50, 'default': 20},
            {'name': 'entry_zscore', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'exit_zscore', 'type': float, 'min': 0.0, 'max': 1.0, 'default': 0.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    @property
    def zscore(self) -> float:
        """Calculate current z-score"""
        closes = self.candles[-self.hp['lookback']:, 2]
        mean = np.mean(closes)
        std = np.std(closes)
        if std == 0:
            return 0
        return (self.close - mean) / std

    @property
    def mean(self) -> float:
        """Calculate mean price"""
        closes = self.candles[-self.hp['lookback']:, 2]
        return np.mean(closes)

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
        target = self.mean  # Target mean
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, max(target, entry + (self.atr * self.hp['atr_multiplier_tp']))

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        target = self.mean  # Target mean
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, min(target, entry - (self.atr * self.hp['atr_multiplier_tp']))

    def update_position(self):
        # Exit when z-score reverts to near zero
        if self.is_long and self.zscore > -self.hp['exit_zscore']:
            self.liquidate()
        elif self.is_short and self.zscore < self.hp['exit_zscore']:
            self.liquidate()
