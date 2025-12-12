"""
VOL_005: Volume Breakout Strategy
---------------------------------
Trade breakouts confirmed by above-average volume.
High volume validates the breakout strength.

Entry Long: Price breakout with volume spike
Entry Short: Price breakdown with volume spike

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 9/10
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
        self.strategy_id = "VOL_005"
        self.strategy_name = "Volume Breakout"
        self.complexity = 3
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'breakout_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'volume_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'volume_mult', 'type': float, 'min': 1.3, 'max': 2.5, 'default': 1.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    @property
    def resistance(self) -> float:
        """Recent high (resistance)"""
        return np.max(self.candles[-self.hp['breakout_period']:-1, 3])

    @property
    def support(self) -> float:
        """Recent low (support)"""
        return np.min(self.candles[-self.hp['breakout_period']:-1, 4])

    @property
    def avg_volume(self) -> float:
        """Average volume"""
        return np.mean(self.candles[-self.hp['volume_period']:, 5])

    @property
    def current_volume(self) -> float:
        return self.candles[-1, 5]

    @property
    def volume_spike(self) -> bool:
        """Current volume is above threshold"""
        return self.current_volume > self.avg_volume * self.hp['volume_mult']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def breakout_up(self) -> bool:
        """Price breaks above resistance"""
        return self.close > self.resistance

    @property
    def breakout_down(self) -> bool:
        """Price breaks below support"""
        return self.close < self.support

    def should_long(self) -> bool:
        return self.breakout_up and self.volume_spike

    def should_short(self) -> bool:
        return self.breakout_down and self.volume_spike

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        # Exit if price returns to breakout level
        if self.is_long and self.close < self.resistance:
            self.liquidate()
        elif self.is_short and self.close > self.support:
            self.liquidate()
