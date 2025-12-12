"""
ATR_006: ATR Channel Strategy
-----------------------------
ATR-based channels similar to Keltner but with different calculation.
Uses ATR bands around a moving average.

Entry: Price breaks channel in trend direction
Exit: Price returns to channel center

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ATRChannel(Strategy):
    """ATR Channel Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ATR_006"
        self.strategy_name = "ATR Channel"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ma_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_period', 'type': int, 'min': 10, 'max': 21, 'default': 14},
            {'name': 'channel_mult', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'ma_type', 'type': str, 'default': 'ema'},  # 'sma' or 'ema'
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def ma(self) -> float:
        if self.hp.get('ma_type', 'ema') == 'sma':
            return ta.sma(self.candles, period=self.hp['ma_period'])
        return ta.ema(self.candles, period=self.hp['ma_period'])

    @property
    def ma_prev(self) -> float:
        if self.hp.get('ma_type', 'ema') == 'sma':
            return ta.sma(self.candles[:-1], period=self.hp['ma_period'])
        return ta.ema(self.candles[:-1], period=self.hp['ma_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=self.hp['atr_period'])

    @property
    def atr_prev(self) -> float:
        return ta.atr(self.candles[:-1], period=self.hp['atr_period'])

    @property
    def upper_channel(self) -> float:
        return self.ma + (self.atr * self.hp['channel_mult'])

    @property
    def lower_channel(self) -> float:
        return self.ma - (self.atr * self.hp['channel_mult'])

    @property
    def upper_channel_prev(self) -> float:
        return self.ma_prev + (self.atr_prev * self.hp['channel_mult'])

    @property
    def lower_channel_prev(self) -> float:
        return self.ma_prev - (self.atr_prev * self.hp['channel_mult'])

    @property
    def trend_up(self) -> bool:
        return self.ma > self.ma_prev

    @property
    def trend_down(self) -> bool:
        return self.ma < self.ma_prev

    def should_long(self) -> bool:
        # Breakout above upper channel with uptrend
        prev_close = self.candles[-2, 2]
        return prev_close <= self.upper_channel_prev and self.close > self.upper_channel and self.trend_up

    def should_short(self) -> bool:
        # Breakout below lower channel with downtrend
        prev_close = self.candles[-2, 2]
        return prev_close >= self.lower_channel_prev and self.close < self.lower_channel and self.trend_down

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
        # Exit when price returns to MA
        if self.is_long and self.close < self.ma:
            self.liquidate()
        elif self.is_short and self.close > self.ma:
            self.liquidate()
