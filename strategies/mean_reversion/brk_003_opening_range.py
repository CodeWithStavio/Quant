"""
BRK_003: Opening Range Breakout Strategy
----------------------------------------
Trade breakouts from the opening range.

Entry Long: Price breaks above opening range high
Entry Short: Price breaks below opening range low

Optimal Timeframes: 5m, 15m
Complexity: 4/10
Crypto Suitability: 6/10 (crypto has no clear "open")
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class OpeningRangeBreakout(Strategy):
    """Opening Range Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BRK_003"
        self.strategy_name = "Opening Range Breakout"
        self.complexity = 4
        self.crypto_suitability = 6
        self.opening_high = None
        self.opening_low = None
        self.range_set = False

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'range_bars', 'type': int, 'min': 3, 'max': 12, 'default': 6},
            {'name': 'breakout_confirm', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _update_opening_range(self):
        """Calculate opening range from first N bars"""
        range_bars = self.hp['range_bars']
        if len(self.candles) >= range_bars:
            self.opening_high = np.max(self.candles[:range_bars, 3])
            self.opening_low = np.min(self.candles[:range_bars, 4])
            self.range_set = True

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        self._update_opening_range()
        if not self.range_set:
            return False

        confirm = self.close * self.hp['breakout_confirm']
        prev_close = self.candles[-2, 2]
        return (prev_close <= self.opening_high and
                self.close > self.opening_high + confirm)

    def should_short(self) -> bool:
        self._update_opening_range()
        if not self.range_set:
            return False

        confirm = self.close * self.hp['breakout_confirm']
        prev_close = self.candles[-2, 2]
        return (prev_close >= self.opening_low and
                self.close < self.opening_low - confirm)

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.opening_low - (self.atr * 0.5)
        target = entry + (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = self.opening_high + (self.atr * 0.5)
        target = entry - (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        pass
