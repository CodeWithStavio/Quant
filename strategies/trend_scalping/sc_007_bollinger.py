"""
SC_007: Bollinger Scalp Strategy
--------------------------------
Scalp Bollinger Band touches.

Entry Long: Price touches lower band
Entry Short: Price touches upper band

Optimal Timeframes: 1m, 5m
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BollingerScalp(Strategy):
    """Bollinger Scalp Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SC_007"
        self.strategy_name = "Bollinger Scalp"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'bb_period', 'type': int, 'min': 15, 'max': 25, 'default': 20},
            {'name': 'bb_mult', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'tp_pct', 'type': float, 'min': 0.2, 'max': 0.5, 'default': 0.3},
            {'name': 'sl_pct', 'type': float, 'min': 0.15, 'max': 0.3, 'default': 0.2},
        ]

    @property
    def bb(self):
        return ta.bollinger_bands(self.candles, period=self.hp['bb_period'], devup=self.hp['bb_mult'], devdn=self.hp['bb_mult'])

    @property
    def upper_band(self) -> float:
        return self.bb[0]

    @property
    def middle_band(self) -> float:
        return self.bb[1]

    @property
    def lower_band(self) -> float:
        return self.bb[2]

    def should_long(self) -> bool:
        # Price touches lower band with reversal
        return self.low <= self.lower_band and self.close > self.open

    def should_short(self) -> bool:
        # Price touches upper band with reversal
        return self.high >= self.upper_band and self.close < self.open

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry * (1 - self.hp['sl_pct'] / 100)
        target = min(self.middle_band, entry * (1 + self.hp['tp_pct'] / 100))
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry * (1 + self.hp['sl_pct'] / 100)
        target = max(self.middle_band, entry * (1 - self.hp['tp_pct'] / 100))
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        pass
