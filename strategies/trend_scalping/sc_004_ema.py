"""
SC_004: EMA Scalp Strategy
--------------------------
Scalp using fast EMA crossovers.

Entry Long: Fast EMA crosses above slow EMA
Entry Short: Fast EMA crosses below slow EMA

Optimal Timeframes: 1m, 5m
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class EMAScalp(Strategy):
    """EMA Scalp Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SC_004"
        self.strategy_name = "EMA Scalp"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_ema', 'type': int, 'min': 3, 'max': 8, 'default': 5},
            {'name': 'slow_ema', 'type': int, 'min': 10, 'max': 20, 'default': 13},
            {'name': 'tp_pct', 'type': float, 'min': 0.2, 'max': 0.5, 'default': 0.3},
            {'name': 'sl_pct', 'type': float, 'min': 0.15, 'max': 0.3, 'default': 0.2},
        ]

    @property
    def fast_ema(self) -> float:
        return ta.ema(self.candles, period=self.hp['fast_ema'])

    @property
    def slow_ema(self) -> float:
        return ta.ema(self.candles, period=self.hp['slow_ema'])

    @property
    def prev_fast_ema(self) -> float:
        return ta.ema(self.candles[:-1], period=self.hp['fast_ema'])

    @property
    def prev_slow_ema(self) -> float:
        return ta.ema(self.candles[:-1], period=self.hp['slow_ema'])

    @property
    def bullish_cross(self) -> bool:
        return self.prev_fast_ema <= self.prev_slow_ema and self.fast_ema > self.slow_ema

    @property
    def bearish_cross(self) -> bool:
        return self.prev_fast_ema >= self.prev_slow_ema and self.fast_ema < self.slow_ema

    def should_long(self) -> bool:
        return self.bullish_cross

    def should_short(self) -> bool:
        return self.bearish_cross

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry * (1 - self.hp['sl_pct'] / 100)
        target = entry * (1 + self.hp['tp_pct'] / 100)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry * (1 + self.hp['sl_pct'] / 100)
        target = entry * (1 - self.hp['tp_pct'] / 100)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        # Exit on cross reversal
        if self.is_long and self.fast_ema < self.slow_ema:
            self.liquidate()
        elif self.is_short and self.fast_ema > self.slow_ema:
            self.liquidate()
