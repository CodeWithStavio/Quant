"""
TF_004: ADX Trend Strategy
--------------------------
Trade in direction of strong trends identified by ADX.

Entry Long: Strong uptrend (ADX high, +DI > -DI)
Entry Short: Strong downtrend (ADX high, -DI > +DI)

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ADXTrend(Strategy):
    """ADX Trend Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "TF_004"
        self.strategy_name = "ADX Trend"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'adx_period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'adx_threshold', 'type': int, 'min': 20, 'max': 30, 'default': 25},
            {'name': 'di_diff', 'type': int, 'min': 5, 'max': 15, 'default': 10},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def adx(self) -> float:
        return ta.adx(self.candles, period=self.hp['adx_period'])

    @property
    def di_plus(self) -> float:
        return ta.di(self.candles, period=self.hp['adx_period'])[0]

    @property
    def di_minus(self) -> float:
        return ta.di(self.candles, period=self.hp['adx_period'])[1]

    @property
    def strong_trend(self) -> bool:
        return self.adx > self.hp['adx_threshold']

    @property
    def bullish_trend(self) -> bool:
        return self.di_plus > self.di_minus + self.hp['di_diff']

    @property
    def bearish_trend(self) -> bool:
        return self.di_minus > self.di_plus + self.hp['di_diff']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.strong_trend and self.bullish_trend

    def should_short(self) -> bool:
        return self.strong_trend and self.bearish_trend

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
        # Exit when trend weakens or reverses
        if self.is_long and (not self.strong_trend or self.bearish_trend):
            self.liquidate()
        elif self.is_short and (not self.strong_trend or self.bullish_trend):
            self.liquidate()
