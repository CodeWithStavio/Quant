"""
SC_008: Breakout Scalp Strategy
-------------------------------
Quick scalps on micro breakouts.

Entry Long: Break above recent high
Entry Short: Break below recent low

Optimal Timeframes: 1m, 5m
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BreakoutScalp(Strategy):
    """Breakout Scalp Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SC_008"
        self.strategy_name = "Breakout Scalp"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 5, 'max': 15, 'default': 10},
            {'name': 'tp_pct', 'type': float, 'min': 0.2, 'max': 0.5, 'default': 0.3},
            {'name': 'sl_pct', 'type': float, 'min': 0.15, 'max': 0.3, 'default': 0.2},
        ]

    @property
    def recent_high(self) -> float:
        return np.max(self.candles[-self.hp['lookback']:-1, 3])

    @property
    def recent_low(self) -> float:
        return np.min(self.candles[-self.hp['lookback']:-1, 4])

    def should_long(self) -> bool:
        # Break above recent high
        return self.high > self.recent_high and self.close > self.recent_high

    def should_short(self) -> bool:
        # Break below recent low
        return self.low < self.recent_low and self.close < self.recent_low

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
        pass
