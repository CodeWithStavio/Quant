"""
MA_014: Guppy Multiple Moving Average (GMMA) Strategy
-----------------------------------------------------
Uses two groups of EMAs: short-term (traders) and long-term (investors).

Short-term EMAs: 3, 5, 8, 10, 12, 15
Long-term EMAs: 30, 35, 40, 45, 50, 60

Entry Long: Short-term group crosses above long-term group
Entry Short: Short-term group crosses below long-term group

Optimal Timeframes: 1h, 4h, 1d
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class GMMACrossover(Strategy):
    """Guppy Multiple Moving Average Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_014"
        self.strategy_name = "GMMA"
        self.complexity = 4
        self.crypto_suitability = 8

        # GMMA standard periods
        self._short_periods = [3, 5, 8, 10, 12, 15]
        self._long_periods = [30, 35, 40, 45, 50, 60]

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'compression_threshold', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'expansion_threshold', 'type': float, 'min': 0.003, 'max': 0.01, 'default': 0.005},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 4.0, 'default': 2.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 6.0, 'default': 4.0},
        ]

    def _get_short_emas(self, candles=None) -> List[float]:
        """Get short-term EMA group values"""
        if candles is None:
            candles = self.candles
        return [ta.ema(candles, period=p) for p in self._short_periods]

    def _get_long_emas(self, candles=None) -> List[float]:
        """Get long-term EMA group values"""
        if candles is None:
            candles = self.candles
        return [ta.ema(candles, period=p) for p in self._long_periods]

    @property
    def short_group_avg(self) -> float:
        return np.mean(self._get_short_emas())

    @property
    def long_group_avg(self) -> float:
        return np.mean(self._get_long_emas())

    @property
    def short_group_avg_prev(self) -> float:
        return np.mean(self._get_short_emas(self.candles[:-1]))

    @property
    def long_group_avg_prev(self) -> float:
        return np.mean(self._get_long_emas(self.candles[:-1]))

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _short_group_spread(self) -> float:
        """Calculate spread within short-term group (normalized)"""
        emas = self._get_short_emas()
        return (max(emas) - min(emas)) / np.mean(emas)

    def _long_group_spread(self) -> float:
        """Calculate spread within long-term group (normalized)"""
        emas = self._get_long_emas()
        return (max(emas) - min(emas)) / np.mean(emas)

    def _groups_separated(self) -> bool:
        """Check if short and long groups are clearly separated"""
        short_min = min(self._get_short_emas())
        long_max = max(self._get_long_emas())
        short_max = max(self._get_short_emas())
        long_min = min(self._get_long_emas())

        # For bullish: all short EMAs above all long EMAs
        bullish_sep = short_min > long_max
        # For bearish: all short EMAs below all long EMAs
        bearish_sep = short_max < long_min

        return bullish_sep or bearish_sep

    def _bullish_cross(self) -> bool:
        """Check if short group crossed above long group"""
        return (self.short_group_avg_prev <= self.long_group_avg_prev and
                self.short_group_avg > self.long_group_avg)

    def _bearish_cross(self) -> bool:
        """Check if short group crossed below long group"""
        return (self.short_group_avg_prev >= self.long_group_avg_prev and
                self.short_group_avg < self.long_group_avg)

    def _short_group_expanding(self) -> bool:
        """Check if short-term traders are expanding (conviction)"""
        return self._short_group_spread() > self.hp['expansion_threshold']

    def should_long(self) -> bool:
        return (self.short_group_avg > self.long_group_avg and
                self._groups_separated() and
                self._short_group_expanding() and
                self.close > self.short_group_avg)

    def should_short(self) -> bool:
        return (self.short_group_avg < self.long_group_avg and
                self._groups_separated() and
                self._short_group_expanding() and
                self.close < self.short_group_avg)

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = min(self._get_long_emas()) - (self.atr * 0.5)
        stop = min(stop, entry - (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.4, entry + (self.atr * self.hp['atr_multiplier_tp'])),
            (0.3, entry + (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
            (0.3, entry + (self.atr * self.hp['atr_multiplier_tp'] * 2)),
        ]

    def go_short(self):
        entry = self.price
        stop = max(self._get_long_emas()) + (self.atr * 0.5)
        stop = max(stop, entry + (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.4, entry - (self.atr * self.hp['atr_multiplier_tp'])),
            (0.3, entry - (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
            (0.3, entry - (self.atr * self.hp['atr_multiplier_tp'] * 2)),
        ]

    def update_position(self):
        # Exit if groups converge (trend weakening)
        if self.is_long:
            if self.short_group_avg <= self.long_group_avg:
                self.liquidate()
        elif self.is_short:
            if self.short_group_avg >= self.long_group_avg:
                self.liquidate()
