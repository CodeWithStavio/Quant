"""
SC_010: Volume Scalp Strategy
-----------------------------
Scalp on volume spikes.

Entry Long: High volume bullish candle
Entry Short: High volume bearish candle

Optimal Timeframes: 1m, 5m
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolumeScalp(Strategy):
    """Volume Scalp Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SC_010"
        self.strategy_name = "Volume Scalp"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'volume_lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'volume_mult', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'tp_pct', 'type': float, 'min': 0.2, 'max': 0.5, 'default': 0.3},
            {'name': 'sl_pct', 'type': float, 'min': 0.15, 'max': 0.3, 'default': 0.2},
        ]

    @property
    def current_volume(self) -> float:
        return self.candles[-1, 5]

    @property
    def avg_volume(self) -> float:
        return np.mean(self.candles[-self.hp['volume_lookback']:-1, 5])

    @property
    def volume_spike(self) -> bool:
        return self.current_volume > self.avg_volume * self.hp['volume_mult']

    @property
    def bullish_candle(self) -> bool:
        return self.close > self.open

    @property
    def bearish_candle(self) -> bool:
        return self.close < self.open

    def should_long(self) -> bool:
        return self.volume_spike and self.bullish_candle

    def should_short(self) -> bool:
        return self.volume_spike and self.bearish_candle

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
