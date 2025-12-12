"""
STAT_006: Distribution Analysis Strategy
----------------------------------------
Trade based on return distribution characteristics.

Entry Long: Positive skew with mean reversion
Entry Short: Negative skew with mean reversion

Optimal Timeframes: 1h, 4h
Complexity: 7/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DistributionAnalysis(Strategy):
    """Distribution Analysis Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "STAT_006"
        self.strategy_name = "Distribution Analysis"
        self.complexity = 7
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 40, 'max': 100, 'default': 60},
            {'name': 'skew_threshold', 'type': float, 'min': 0.3, 'max': 0.8, 'default': 0.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _calculate_skewness(self) -> float:
        """Calculate skewness of returns"""
        lookback = self.hp['lookback']
        returns = np.diff(self.candles[-lookback:, 2]) / self.candles[-lookback-1:-1, 2]

        n = len(returns)
        if n < 3:
            return 0

        mean = np.mean(returns)
        std = np.std(returns)

        if std == 0:
            return 0

        skew = np.sum((returns - mean) ** 3) / (n * std ** 3)
        return skew

    def _calculate_kurtosis(self) -> float:
        """Calculate excess kurtosis"""
        lookback = self.hp['lookback']
        returns = np.diff(self.candles[-lookback:, 2]) / self.candles[-lookback-1:-1, 2]

        n = len(returns)
        if n < 4:
            return 0

        mean = np.mean(returns)
        std = np.std(returns)

        if std == 0:
            return 0

        kurt = np.sum((returns - mean) ** 4) / (n * std ** 4) - 3
        return kurt

    @property
    def skewness(self) -> float:
        return self._calculate_skewness()

    @property
    def kurtosis(self) -> float:
        return self._calculate_kurtosis()

    @property
    def zscore(self) -> float:
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
        # Positive skew (more upside potential) at low prices
        positive_skew = self.skewness > self.hp['skew_threshold']
        oversold = self.zscore < -1.5
        return positive_skew and oversold

    def should_short(self) -> bool:
        # Negative skew (more downside risk) at high prices
        negative_skew = self.skewness < -self.hp['skew_threshold']
        overbought = self.zscore > 1.5
        return negative_skew and overbought

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
        # Exit when zscore normalizes
        if abs(self.zscore) < 0.5:
            self.liquidate()
