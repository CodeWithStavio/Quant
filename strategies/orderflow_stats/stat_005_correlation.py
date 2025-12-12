"""
STAT_005: Correlation Regime Strategy
-------------------------------------
Trade based on autocorrelation regime changes.

Entry Long: Positive autocorrelation with uptrend
Entry Short: Positive autocorrelation with downtrend

Optimal Timeframes: 1h, 4h
Complexity: 7/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class CorrelationRegime(Strategy):
    """Correlation Regime Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "STAT_005"
        self.strategy_name = "Correlation Regime"
        self.complexity = 7
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 30, 'max': 60, 'default': 40},
            {'name': 'autocorr_threshold', 'type': float, 'min': 0.2, 'max': 0.5, 'default': 0.3},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _calculate_autocorrelation(self, lag: int = 1) -> float:
        """Calculate autocorrelation of returns"""
        lookback = self.hp['lookback']
        returns = np.diff(self.candles[-lookback:, 2]) / self.candles[-lookback-1:-1, 2]

        if len(returns) <= lag:
            return 0

        # Autocorrelation at specified lag
        n = len(returns)
        mean = np.mean(returns)
        variance = np.var(returns)

        if variance == 0:
            return 0

        autocov = np.sum((returns[lag:] - mean) * (returns[:-lag] - mean)) / n
        return autocov / variance

    @property
    def autocorr(self) -> float:
        return self._calculate_autocorrelation(lag=1)

    @property
    def trend(self) -> int:
        """Determine trend direction"""
        ma = ta.sma(self.candles, period=20)
        if self.close > ma:
            return 1
        elif self.close < ma:
            return -1
        return 0

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Positive autocorrelation = trend persistence
        trending = self.autocorr > self.hp['autocorr_threshold']
        uptrend = self.trend == 1
        return trending and uptrend

    def should_short(self) -> bool:
        # Positive autocorrelation = trend persistence
        trending = self.autocorr > self.hp['autocorr_threshold']
        downtrend = self.trend == -1
        return trending and downtrend

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
        # Exit when autocorrelation breaks down
        if abs(self.autocorr) < 0.1:
            self.liquidate()
