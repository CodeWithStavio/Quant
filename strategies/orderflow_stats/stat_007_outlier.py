"""
STAT_007: Outlier Detector Strategy
-----------------------------------
Trade reversals from statistical outliers.

Entry Long: Extreme negative outlier (oversold)
Entry Short: Extreme positive outlier (overbought)

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class OutlierDetector(Strategy):
    """Outlier Detector Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "STAT_007"
        self.strategy_name = "Outlier Detector"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 30, 'max': 80, 'default': 50},
            {'name': 'outlier_threshold', 'type': float, 'min': 2.5, 'max': 3.5, 'default': 3.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _detect_outlier(self) -> float:
        """Detect if current return is an outlier"""
        lookback = self.hp['lookback']
        returns = np.diff(self.candles[-lookback:, 2]) / self.candles[-lookback-1:-1, 2]

        current_return = (self.close - self.candles[-2, 2]) / self.candles[-2, 2]

        mean = np.mean(returns[:-1])  # Exclude current
        std = np.std(returns[:-1])

        if std == 0:
            return 0

        # Z-score of current return
        return (current_return - mean) / std

    @property
    def return_zscore(self) -> float:
        return self._detect_outlier()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Extreme negative outlier = potential reversal up
        return self.return_zscore < -self.hp['outlier_threshold']

    def should_short(self) -> bool:
        # Extreme positive outlier = potential reversal down
        return self.return_zscore > self.hp['outlier_threshold']

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
        # Exit when return normalizes
        if abs(self.return_zscore) < 1:
            self.liquidate()
