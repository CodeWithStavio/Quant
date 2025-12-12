"""
BRK_004: Consolidation Breakout Strategy
----------------------------------------
Trade breakouts from tight consolidation patterns.

Entry Long: Price breaks above consolidation
Entry Short: Price breaks below consolidation

Optimal Timeframes: 15m, 1h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ConsolidationBreakout(Strategy):
    """Consolidation Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BRK_004"
        self.strategy_name = "Consolidation Breakout"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'consolidation_period', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'squeeze_threshold', 'type': float, 'min': 0.5, 'max': 0.8, 'default': 0.6},
            {'name': 'breakout_confirm', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def consolidation_high(self) -> float:
        return np.max(self.candles[-self.hp['consolidation_period']:, 3])

    @property
    def consolidation_low(self) -> float:
        return np.min(self.candles[-self.hp['consolidation_period']:, 4])

    @property
    def consolidation_range(self) -> float:
        return self.consolidation_high - self.consolidation_low

    @property
    def is_squeezed(self) -> bool:
        """Check if volatility is compressed"""
        # Compare current ATR to average ATR
        current_atr = ta.atr(self.candles, period=14)
        lookback_atr = ta.atr(self.candles[:-self.hp['consolidation_period']], period=14)

        if lookback_atr == 0:
            return False
        return current_atr / lookback_atr < self.hp['squeeze_threshold']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        if not self.is_squeezed:
            return False

        confirm = self.close * self.hp['breakout_confirm']
        prev_close = self.candles[-2, 2]
        return (prev_close <= self.consolidation_high and
                self.close > self.consolidation_high + confirm)

    def should_short(self) -> bool:
        if not self.is_squeezed:
            return False

        confirm = self.close * self.hp['breakout_confirm']
        prev_close = self.candles[-2, 2]
        return (prev_close >= self.consolidation_low and
                self.close < self.consolidation_low - confirm)

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.consolidation_low - (self.atr * 0.5)
        target = entry + self.consolidation_range  # Measure move
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = self.consolidation_high + (self.atr * 0.5)
        target = entry - self.consolidation_range  # Measure move
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        pass
