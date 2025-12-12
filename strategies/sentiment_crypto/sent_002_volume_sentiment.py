"""
SENT_002: Volume Sentiment Strategy
-----------------------------------
Use volume patterns as sentiment proxy.

Entry Long: Volume surge on green candles (buying enthusiasm)
Entry Short: Volume surge on red candles (selling panic)

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolumeSentiment(Strategy):
    """Volume-based Sentiment Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SENT_002"
        self.strategy_name = "Volume Sentiment"
        self.complexity = 5
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'vol_lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'vol_multiplier', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'consecutive_bars', 'type': int, 'min': 2, 'max': 4, 'default': 2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def avg_volume(self) -> float:
        return np.mean(self.candles[-self.hp['vol_lookback']-1:-1, 5])

    @property
    def current_volume(self) -> float:
        return self.candles[-1, 5]

    @property
    def is_volume_surge(self) -> bool:
        return self.current_volume > self.avg_volume * self.hp['vol_multiplier']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _count_consecutive_green(self) -> int:
        """Count consecutive green high-volume bars"""
        count = 0
        for i in range(1, min(10, len(self.candles))):
            idx = -i
            if self.candles[idx, 2] > self.candles[idx, 1]:  # close > open
                vol = self.candles[idx, 5]
                if vol > self.avg_volume * self.hp['vol_multiplier']:
                    count += 1
                else:
                    break
            else:
                break
        return count

    def _count_consecutive_red(self) -> int:
        """Count consecutive red high-volume bars"""
        count = 0
        for i in range(1, min(10, len(self.candles))):
            idx = -i
            if self.candles[idx, 2] < self.candles[idx, 1]:  # close < open
                vol = self.candles[idx, 5]
                if vol > self.avg_volume * self.hp['vol_multiplier']:
                    count += 1
                else:
                    break
            else:
                break
        return count

    def should_long(self) -> bool:
        return self._count_consecutive_green() >= self.hp['consecutive_bars']

    def should_short(self) -> bool:
        return self._count_consecutive_red() >= self.hp['consecutive_bars']

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Exit on volume exhaustion
        if self.is_long and self.current_volume < self.avg_volume * 0.5:
            self.liquidate()
        elif self.is_short and self.current_volume < self.avg_volume * 0.5:
            self.liquidate()
