"""
TF_002: Multi-MA Trend Strategy
-------------------------------
Trade when multiple MAs align in the same direction.

Entry Long: All MAs bullishly aligned
Entry Short: All MAs bearishly aligned

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MultiMATrend(Strategy):
    """Multi-MA Trend Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "TF_002"
        self.strategy_name = "Multi MA Trend"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_ma', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'medium_ma', 'type': int, 'min': 18, 'max': 25, 'default': 20},
            {'name': 'slow_ma', 'type': int, 'min': 45, 'max': 60, 'default': 50},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def fast_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['fast_ma'])

    @property
    def medium_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['medium_ma'])

    @property
    def slow_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['slow_ma'])

    @property
    def bullish_alignment(self) -> bool:
        return self.fast_ma > self.medium_ma > self.slow_ma

    @property
    def bearish_alignment(self) -> bool:
        return self.fast_ma < self.medium_ma < self.slow_ma

    @property
    def prev_bullish(self) -> bool:
        fast = ta.ema(self.candles[:-1], period=self.hp['fast_ma'])
        medium = ta.ema(self.candles[:-1], period=self.hp['medium_ma'])
        slow = ta.ema(self.candles[:-1], period=self.hp['slow_ma'])
        return fast > medium > slow

    @property
    def prev_bearish(self) -> bool:
        fast = ta.ema(self.candles[:-1], period=self.hp['fast_ma'])
        medium = ta.ema(self.candles[:-1], period=self.hp['medium_ma'])
        slow = ta.ema(self.candles[:-1], period=self.hp['slow_ma'])
        return fast < medium < slow

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # MAs just aligned bullishly
        return self.bullish_alignment and not self.prev_bullish

    def should_short(self) -> bool:
        # MAs just aligned bearishly
        return self.bearish_alignment and not self.prev_bearish

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.slow_ma - (self.atr * self.hp['atr_multiplier_sl'])
        target = entry + (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = self.slow_ma + (self.atr * self.hp['atr_multiplier_sl'])
        target = entry - (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        # Exit if alignment breaks
        if self.is_long and not self.bullish_alignment:
            self.liquidate()
        elif self.is_short and not self.bearish_alignment:
            self.liquidate()
