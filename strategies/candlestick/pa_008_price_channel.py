"""
PA_008: Price Channel Strategy
------------------------------
Trade breakouts from horizontal price channels.

Entry Long: Breakout above channel resistance
Entry Short: Breakdown below channel support

Optimal Timeframes: 15m, 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class PriceChannel(Strategy):
    """Price Channel Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PA_008"
        self.strategy_name = "Price Channel"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'channel_period', 'type': int, 'min': 15, 'max': 50, 'default': 30},
            {'name': 'consolidation_threshold', 'type': float, 'min': 0.02, 'max': 0.06, 'default': 0.04},
            {'name': 'breakout_confirm', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def channel_high(self) -> float:
        """Calculate channel high"""
        period = self.hp['channel_period']
        return np.max(self.candles[-period:, 3])

    @property
    def channel_low(self) -> float:
        """Calculate channel low"""
        period = self.hp['channel_period']
        return np.min(self.candles[-period:, 4])

    @property
    def channel_width(self) -> float:
        """Calculate channel width as percentage"""
        mid = (self.channel_high + self.channel_low) / 2
        if mid == 0:
            return 0
        return (self.channel_high - self.channel_low) / mid

    @property
    def in_consolidation(self) -> bool:
        """Check if price is in consolidation (tight channel)"""
        return self.channel_width <= self.hp['consolidation_threshold']

    @property
    def prev_channel_high(self) -> float:
        """Previous bar's channel high"""
        period = self.hp['channel_period']
        return np.max(self.candles[-(period+1):-1, 3])

    @property
    def prev_channel_low(self) -> float:
        """Previous bar's channel low"""
        period = self.hp['channel_period']
        return np.min(self.candles[-(period+1):-1, 4])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Breakout above channel high after consolidation
        if not self.in_consolidation:
            return False

        confirm = self.close * self.hp['breakout_confirm']
        prev_close = self.candles[-2, 2]

        return prev_close <= self.prev_channel_high and self.close > self.channel_high + confirm

    def should_short(self) -> bool:
        # Breakdown below channel low after consolidation
        if not self.in_consolidation:
            return False

        confirm = self.close * self.hp['breakout_confirm']
        prev_close = self.candles[-2, 2]

        return prev_close >= self.prev_channel_low and self.close < self.channel_low - confirm

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        channel_mid = (self.channel_high + self.channel_low) / 2
        stop = max(channel_mid, entry - (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        channel_mid = (self.channel_high + self.channel_low) / 2
        stop = min(channel_mid, entry + (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        # Exit if price returns to channel mid
        channel_mid = (self.channel_high + self.channel_low) / 2
        if self.is_long and self.close < channel_mid:
            self.liquidate()
        elif self.is_short and self.close > channel_mid:
            self.liquidate()
