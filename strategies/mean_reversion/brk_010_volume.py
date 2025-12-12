"""
BRK_010: Volume Breakout Strategy
---------------------------------
Trade breakouts confirmed by high volume.

Entry Long: Price breaks high with volume surge
Entry Short: Price breaks low with volume surge

Optimal Timeframes: 15m, 1h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolumeBreakout(Strategy):
    """Volume Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BRK_010"
        self.strategy_name = "Volume Breakout"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'price_lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'volume_lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'volume_mult', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def period_high(self) -> float:
        return np.max(self.candles[-self.hp['price_lookback']:-1, 3])

    @property
    def period_low(self) -> float:
        return np.min(self.candles[-self.hp['price_lookback']:-1, 4])

    @property
    def current_volume(self) -> float:
        return self.candles[-1, 5]

    @property
    def avg_volume(self) -> float:
        return np.mean(self.candles[-self.hp['volume_lookback']:-1, 5])

    @property
    def volume_surge(self) -> bool:
        """Check if current volume is significantly above average"""
        return self.current_volume > self.avg_volume * self.hp['volume_mult']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Breakout above period high with volume surge
        return self.close > self.period_high and self.volume_surge

    def should_short(self) -> bool:
        # Breakdown below period low with volume surge
        return self.close < self.period_low and self.volume_surge

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        target = entry + (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        target = entry - (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        pass
