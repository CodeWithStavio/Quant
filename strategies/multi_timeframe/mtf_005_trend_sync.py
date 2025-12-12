"""
MTF_005: Timeframe Trend Sync Strategy
--------------------------------------
Synchronize trend detection across timeframe views.

Entry Long: All trend indicators aligned bullish
Entry Short: All trend indicators aligned bearish

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TFTrendSync(Strategy):
    """Timeframe Trend Sync Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MTF_005"
        self.strategy_name = "TF Trend Sync"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ltf_adx', 'type': int, 'min': 10, 'max': 18, 'default': 14},
            {'name': 'htf_adx', 'type': int, 'min': 50, 'max': 80, 'default': 60},
            {'name': 'adx_threshold', 'type': int, 'min': 20, 'max': 30, 'default': 25},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def ltf_adx(self) -> float:
        return ta.adx(self.candles, period=self.hp['ltf_adx'])

    @property
    def ltf_di_plus(self) -> float:
        return ta.di(self.candles, period=self.hp['ltf_adx'])[0]

    @property
    def ltf_di_minus(self) -> float:
        return ta.di(self.candles, period=self.hp['ltf_adx'])[1]

    @property
    def htf_adx(self) -> float:
        return ta.adx(self.candles, period=self.hp['htf_adx'])

    @property
    def htf_di_plus(self) -> float:
        return ta.di(self.candles, period=self.hp['htf_adx'])[0]

    @property
    def htf_di_minus(self) -> float:
        return ta.di(self.candles, period=self.hp['htf_adx'])[1]

    @property
    def ltf_bullish_trend(self) -> bool:
        return self.ltf_adx > self.hp['adx_threshold'] and self.ltf_di_plus > self.ltf_di_minus

    @property
    def ltf_bearish_trend(self) -> bool:
        return self.ltf_adx > self.hp['adx_threshold'] and self.ltf_di_minus > self.ltf_di_plus

    @property
    def htf_bullish_trend(self) -> bool:
        return self.htf_di_plus > self.htf_di_minus

    @property
    def htf_bearish_trend(self) -> bool:
        return self.htf_di_minus > self.htf_di_plus

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.htf_bullish_trend and self.ltf_bullish_trend

    def should_short(self) -> bool:
        return self.htf_bearish_trend and self.ltf_bearish_trend

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
        if self.is_long and not self.htf_bullish_trend:
            self.liquidate()
        elif self.is_short and not self.htf_bearish_trend:
            self.liquidate()
