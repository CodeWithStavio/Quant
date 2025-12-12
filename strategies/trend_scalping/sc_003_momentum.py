"""
SC_003: Momentum Scalp Strategy
-------------------------------
Scalp on momentum bursts.

Entry Long: Strong momentum burst up
Entry Short: Strong momentum burst down

Optimal Timeframes: 1m, 5m
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MomentumScalp(Strategy):
    """Momentum Scalp Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SC_003"
        self.strategy_name = "Momentum Scalp"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'mom_period', 'type': int, 'min': 5, 'max': 12, 'default': 8},
            {'name': 'mom_threshold', 'type': float, 'min': 0.3, 'max': 0.8, 'default': 0.5},
            {'name': 'tp_pct', 'type': float, 'min': 0.2, 'max': 0.5, 'default': 0.3},
            {'name': 'sl_pct', 'type': float, 'min': 0.15, 'max': 0.3, 'default': 0.2},
        ]

    @property
    def momentum_pct(self) -> float:
        """Momentum as percentage"""
        period = self.hp['mom_period']
        prev_close = self.candles[-period, 2]
        if prev_close == 0:
            return 0
        return ((self.close - prev_close) / prev_close) * 100

    @property
    def candle_momentum(self) -> float:
        """Current candle momentum"""
        if self.open == 0:
            return 0
        return ((self.close - self.open) / self.open) * 100

    def should_long(self) -> bool:
        # Strong upward momentum
        return (self.momentum_pct > self.hp['mom_threshold'] and
                self.candle_momentum > 0)

    def should_short(self) -> bool:
        # Strong downward momentum
        return (self.momentum_pct < -self.hp['mom_threshold'] and
                self.candle_momentum < 0)

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
        # Quick exit if momentum reverses
        if self.is_long and self.candle_momentum < -0.2:
            self.liquidate()
        elif self.is_short and self.candle_momentum > 0.2:
            self.liquidate()
