"""
SENT_006: Trend Strength Sentiment Strategy
-------------------------------------------
Use ADX and trend metrics as sentiment proxy.

Entry Long: Strong uptrend sentiment
Entry Short: Strong downtrend sentiment

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TrendStrengthSentiment(Strategy):
    """Trend Strength Sentiment Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SENT_006"
        self.strategy_name = "Trend Strength Sentiment"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'adx_period', 'type': int, 'min': 10, 'max': 18, 'default': 14},
            {'name': 'adx_threshold', 'type': int, 'min': 20, 'max': 35, 'default': 25},
            {'name': 'di_diff_threshold', 'type': int, 'min': 8, 'max': 20, 'default': 10},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def adx(self) -> float:
        return ta.adx(self.candles, period=self.hp['adx_period'])

    @property
    def di(self) -> tuple:
        return ta.di(self.candles, period=self.hp['adx_period'])

    @property
    def di_plus(self) -> float:
        return self.di[0]

    @property
    def di_minus(self) -> float:
        return self.di[1]

    @property
    def di_diff(self) -> float:
        return self.di_plus - self.di_minus

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def is_strong_trend(self) -> bool:
        return self.adx > self.hp['adx_threshold']

    def should_long(self) -> bool:
        return (self.is_strong_trend and
                self.di_diff > self.hp['di_diff_threshold'])

    def should_short(self) -> bool:
        return (self.is_strong_trend and
                self.di_diff < -self.hp['di_diff_threshold'])

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
        if self.is_long and (self.adx < 20 or self.di_diff < 0):
            self.liquidate()
        elif self.is_short and (self.adx < 20 or self.di_diff > 0):
            self.liquidate()
