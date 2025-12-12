"""
MA_013: MA Fan/Ribbon Strategy
------------------------------
Uses multiple MAs to form a ribbon. Trade when all MAs align.

Multiple MAs: 10, 20, 30, 40, 50 periods

Entry Long: All MAs aligned bullish (stacked ascending)
Entry Short: All MAs aligned bearish (stacked descending)

Optimal Timeframes: 1h, 4h, 1d
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MARibbon(Strategy):
    """MA Fan/Ribbon Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_013"
        self.strategy_name = "MA Ribbon"
        self.complexity = 3
        self.crypto_suitability = 8
        self._ribbon_periods = [10, 20, 30, 40, 50]

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ma_type', 'type': str, 'default': 'ema'},
            {'name': 'ribbon_expansion_threshold', 'type': float, 'min': 0.001, 'max': 0.01, 'default': 0.003},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 4.0, 'default': 2.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 6.0, 'default': 4.0},
        ]

    def _get_ribbon_values(self) -> List[float]:
        """Get all MA values in the ribbon"""
        ma_func = ta.ema if self.hp.get('ma_type', 'ema') == 'ema' else ta.sma
        return [ma_func(self.candles, period=p) for p in self._ribbon_periods]

    def _get_ribbon_values_prev(self) -> List[float]:
        """Get previous MA values"""
        ma_func = ta.ema if self.hp.get('ma_type', 'ema') == 'ema' else ta.sma
        return [ma_func(self.candles[:-1], period=p) for p in self._ribbon_periods]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _ribbon_bullish_stack(self) -> bool:
        """Check if ribbon is stacked bullishly (shorter MAs above longer)"""
        values = self._get_ribbon_values()
        # Each shorter MA should be above the longer ones
        for i in range(len(values) - 1):
            if values[i] <= values[i + 1]:
                return False
        return True

    def _ribbon_bearish_stack(self) -> bool:
        """Check if ribbon is stacked bearishly (shorter MAs below longer)"""
        values = self._get_ribbon_values()
        # Each shorter MA should be below the longer ones
        for i in range(len(values) - 1):
            if values[i] >= values[i + 1]:
                return False
        return True

    def _ribbon_expanding(self) -> bool:
        """Check if ribbon is expanding (trend strengthening)"""
        current = self._get_ribbon_values()
        prev = self._get_ribbon_values_prev()

        current_spread = abs(current[0] - current[-1]) / current[-1]
        prev_spread = abs(prev[0] - prev[-1]) / prev[-1]

        return current_spread > prev_spread

    def _ribbon_just_aligned_bullish(self) -> bool:
        """Check if ribbon just became bullish aligned"""
        current_bullish = self._ribbon_bullish_stack()
        prev_values = self._get_ribbon_values_prev()
        prev_bullish = all(prev_values[i] > prev_values[i+1] for i in range(len(prev_values)-1))
        return current_bullish and not prev_bullish

    def _ribbon_just_aligned_bearish(self) -> bool:
        """Check if ribbon just became bearish aligned"""
        current_bearish = self._ribbon_bearish_stack()
        prev_values = self._get_ribbon_values_prev()
        prev_bearish = all(prev_values[i] < prev_values[i+1] for i in range(len(prev_values)-1))
        return current_bearish and not prev_bearish

    def should_long(self) -> bool:
        return (self._ribbon_bullish_stack() and
                self._ribbon_expanding() and
                self.close > self._get_ribbon_values()[0])

    def should_short(self) -> bool:
        return (self._ribbon_bearish_stack() and
                self._ribbon_expanding() and
                self.close < self._get_ribbon_values()[0])

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        ribbon = self._get_ribbon_values()
        stop = min(ribbon[-1], entry - (self.atr * self.hp['atr_multiplier_sl']))
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
        ribbon = self._get_ribbon_values()
        stop = max(ribbon[-1], entry + (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.4, entry - (self.atr * self.hp['atr_multiplier_tp'])),
            (0.3, entry - (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
            (0.3, entry - (self.atr * self.hp['atr_multiplier_tp'] * 2)),
        ]

    def update_position(self):
        ribbon = self._get_ribbon_values()
        # Exit if ribbon alignment breaks
        if self.is_long and not self._ribbon_bullish_stack():
            self.liquidate()
        elif self.is_short and not self._ribbon_bearish_stack():
            self.liquidate()
