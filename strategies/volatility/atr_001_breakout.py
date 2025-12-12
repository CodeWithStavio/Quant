"""
ATR_001: ATR Breakout Strategy
------------------------------
Volatility breakout using ATR bands around price.

Entry Long: Price breaks above ATR band
Entry Short: Price breaks below ATR band

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ATRBreakout(Strategy):
    """ATR Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ATR_001"
        self.strategy_name = "ATR Breakout"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'atr_period', 'type': int, 'min': 10, 'max': 21, 'default': 14},
            {'name': 'atr_multiplier', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'ma_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def ma(self) -> float:
        return ta.sma(self.candles, period=self.hp['ma_period'])

    @property
    def ma_prev(self) -> float:
        return ta.sma(self.candles[:-1], period=self.hp['ma_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=self.hp['atr_period'])

    @property
    def upper_band(self) -> float:
        return self.ma + (self.atr * self.hp['atr_multiplier'])

    @property
    def lower_band(self) -> float:
        return self.ma - (self.atr * self.hp['atr_multiplier'])

    @property
    def upper_band_prev(self) -> float:
        atr_prev = ta.atr(self.candles[:-1], period=self.hp['atr_period'])
        return self.ma_prev + (atr_prev * self.hp['atr_multiplier'])

    @property
    def lower_band_prev(self) -> float:
        atr_prev = ta.atr(self.candles[:-1], period=self.hp['atr_period'])
        return self.ma_prev - (atr_prev * self.hp['atr_multiplier'])

    def should_long(self) -> bool:
        # Price breaks above upper ATR band
        return self.candles[-2, 2] < self.upper_band_prev and self.close > self.upper_band

    def should_short(self) -> bool:
        # Price breaks below lower ATR band
        return self.candles[-2, 2] > self.lower_band_prev and self.close < self.lower_band

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
