"""
STAT_009: Hurst Exponent Strategy
---------------------------------
Trade based on Hurst exponent regime detection.

Entry Long: Mean reverting regime at oversold
Entry Short: Mean reverting regime at overbought

Optimal Timeframes: 4h, 1d
Complexity: 8/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class HurstExponent(Strategy):
    """Hurst Exponent Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "STAT_009"
        self.strategy_name = "Hurst Exponent"
        self.complexity = 8
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 50, 'max': 150, 'default': 100},
            {'name': 'mean_revert_threshold', 'type': float, 'min': 0.35, 'max': 0.48, 'default': 0.45},
            {'name': 'trending_threshold', 'type': float, 'min': 0.52, 'max': 0.65, 'default': 0.55},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _calculate_hurst(self) -> float:
        """Calculate Hurst exponent using R/S method (simplified)"""
        lookback = self.hp['lookback']
        prices = self.candles[-lookback:, 2]
        returns = np.diff(np.log(prices))

        if len(returns) < 20:
            return 0.5

        # Simplified R/S analysis
        n = len(returns)
        mean = np.mean(returns)
        cumdev = np.cumsum(returns - mean)

        # Range
        R = np.max(cumdev) - np.min(cumdev)

        # Standard deviation
        S = np.std(returns)

        if S == 0:
            return 0.5

        # R/S ratio
        rs = R / S

        # Hurst estimate: H = log(R/S) / log(n)
        if rs <= 0 or n <= 1:
            return 0.5

        H = np.log(rs) / np.log(n) * 0.5 + 0.25  # Adjusted estimate

        return np.clip(H, 0, 1)

    @property
    def hurst(self) -> float:
        return self._calculate_hurst()

    @property
    def is_mean_reverting(self) -> bool:
        """H < 0.5 indicates mean reversion"""
        return self.hurst < self.hp['mean_revert_threshold']

    @property
    def is_trending(self) -> bool:
        """H > 0.5 indicates trending"""
        return self.hurst > self.hp['trending_threshold']

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
        # Mean reverting regime at oversold
        if self.is_mean_reverting:
            return self.zscore < -1.5
        # Trending regime with upward momentum
        elif self.is_trending:
            roc = ta.roc(self.candles, period=10)
            return roc > 2
        return False

    def should_short(self) -> bool:
        # Mean reverting regime at overbought
        if self.is_mean_reverting:
            return self.zscore > 1.5
        # Trending regime with downward momentum
        elif self.is_trending:
            roc = ta.roc(self.candles, period=10)
            return roc < -2
        return False

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
        if self.is_mean_reverting:
            # Exit when zscore normalizes
            if abs(self.zscore) < 0.5:
                self.liquidate()
        else:
            # Trail for trending
            if self.is_long and self.close < ta.sma(self.candles, period=20):
                self.liquidate()
            elif self.is_short and self.close > ta.sma(self.candles, period=20):
                self.liquidate()
