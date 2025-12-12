"""
RISK_005: Correlation Hedge Strategy
------------------------------------
Trade with awareness of market correlation.

Entry Long: Low correlation regime opportunities
Entry Short: High correlation breakdown

Optimal Timeframes: 4h, 1d
Complexity: 7/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class CorrelationHedge(Strategy):
    """Correlation Hedge Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "RISK_005"
        self.strategy_name = "Correlation Hedge"
        self.complexity = 7
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'autocorr_threshold', 'type': float, 'min': 0.3, 'max': 0.6, 'default': 0.4},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _calculate_autocorrelation(self) -> float:
        """Calculate return autocorrelation"""
        lookback = self.hp['lookback']
        returns = np.diff(self.candles[-lookback:, 2]) / self.candles[-lookback-1:-1, 2]

        if len(returns) <= 1:
            return 0

        mean = np.mean(returns)
        variance = np.var(returns)

        if variance == 0:
            return 0

        autocov = np.sum((returns[1:] - mean) * (returns[:-1] - mean)) / len(returns)
        return autocov / variance

    @property
    def autocorr(self) -> float:
        return self._calculate_autocorrelation()

    @property
    def is_trending_regime(self) -> bool:
        """High autocorrelation = trending"""
        return self.autocorr > self.hp['autocorr_threshold']

    @property
    def is_mean_reverting_regime(self) -> bool:
        """Negative autocorrelation = mean reverting"""
        return self.autocorr < -self.hp['autocorr_threshold']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def zscore(self) -> float:
        lookback = self.hp['lookback']
        prices = self.candles[-lookback:, 2]
        mean = np.mean(prices)
        std = np.std(prices)
        if std == 0:
            return 0
        return (self.close - mean) / std

    def should_long(self) -> bool:
        if self.is_trending_regime:
            # Follow trend in trending regime
            roc = ta.roc(self.candles, period=10)
            return roc > 1
        elif self.is_mean_reverting_regime:
            # Mean reversion in ranging regime
            return self.zscore < -1.5
        return False

    def should_short(self) -> bool:
        if self.is_trending_regime:
            roc = ta.roc(self.candles, period=10)
            return roc < -1
        elif self.is_mean_reverting_regime:
            return self.zscore > 1.5
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
        if self.is_mean_reverting_regime:
            if abs(self.zscore) < 0.5:
                self.liquidate()
        else:
            ma = ta.sma(self.candles, period=20)
            if self.is_long and self.close < ma:
                self.liquidate()
            elif self.is_short and self.close > ma:
                self.liquidate()
