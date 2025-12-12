"""
STAT_004: Variance Breakout Strategy
------------------------------------
Trade breakouts from low variance periods.

Entry Long: Variance expansion with upward breakout
Entry Short: Variance expansion with downward breakout

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VarianceBreakout(Strategy):
    """Variance Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "STAT_004"
        self.strategy_name = "Variance Breakout"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'low_var_pct', 'type': float, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'breakout_mult', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _get_variance_percentile(self) -> float:
        """Calculate current variance percentile"""
        lookback = self.hp['lookback']
        returns = np.diff(self.candles[-lookback:, 2]) / self.candles[-lookback-1:-1, 2]
        current_var = np.var(returns[-10:])  # Recent variance

        # Historical variances
        var_history = []
        for i in range(10, lookback):
            hist_var = np.var(returns[i-10:i])
            var_history.append(hist_var)

        if not var_history:
            return 50

        return np.sum(np.array(var_history) < current_var) / len(var_history) * 100

    def _was_low_variance(self) -> bool:
        """Check if previous period was low variance"""
        lookback = self.hp['lookback']
        returns = np.diff(self.candles[-lookback-5:-5, 2]) / self.candles[-lookback-6:-6, 2]
        prev_var = np.var(returns[-10:])

        var_history = []
        for i in range(10, lookback):
            hist_var = np.var(returns[i-10:i])
            var_history.append(hist_var)

        if not var_history:
            return False

        percentile = np.sum(np.array(var_history) < prev_var) / len(var_history) * 100
        return percentile < self.hp['low_var_pct']

    @property
    def var_percentile(self) -> float:
        return self._get_variance_percentile()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Variance expansion from low with upward move
        was_low = self._was_low_variance()
        expanding = self.var_percentile > 50
        upward = self.close > self.candles[-5, 2]
        return was_low and expanding and upward

    def should_short(self) -> bool:
        # Variance expansion from low with downward move
        was_low = self._was_low_variance()
        expanding = self.var_percentile > 50
        downward = self.close < self.candles[-5, 2]
        return was_low and expanding and downward

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
        # Trail with ATR
        if self.is_long:
            trail = self.close - (self.atr * 1.5)
            if trail > self.average_entry_price:
                self.stop_loss = self.position.qty, trail
        elif self.is_short:
            trail = self.close + (self.atr * 1.5)
            if trail < self.average_entry_price:
                self.stop_loss = self.position.qty, trail
