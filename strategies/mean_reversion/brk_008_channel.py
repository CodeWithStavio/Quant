"""
BRK_008: Channel Breakout Strategy
----------------------------------
Trade breakouts from Donchian-style channels.

Entry Long: Price breaks above channel high
Entry Short: Price breaks below channel low

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ChannelBreakout(Strategy):
    """Channel Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BRK_008"
        self.strategy_name = "Channel Breakout"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'entry_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'exit_period', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    @property
    def entry_high(self) -> float:
        return np.max(self.candles[-self.hp['entry_period']:-1, 3])

    @property
    def entry_low(self) -> float:
        return np.min(self.candles[-self.hp['entry_period']:-1, 4])

    @property
    def exit_high(self) -> float:
        return np.max(self.candles[-self.hp['exit_period']:, 3])

    @property
    def exit_low(self) -> float:
        return np.min(self.candles[-self.hp['exit_period']:, 4])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.high >= self.entry_high

    def should_short(self) -> bool:
        return self.low <= self.entry_low

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.entry_high
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.entry_low
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Exit on opposite channel break
        if self.is_long and self.low <= self.exit_low:
            self.liquidate()
        elif self.is_short and self.high >= self.exit_high:
            self.liquidate()
