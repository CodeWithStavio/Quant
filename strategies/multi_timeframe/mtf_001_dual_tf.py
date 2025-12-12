"""
MTF_001: Dual Timeframe Confirmation Strategy
---------------------------------------------
Simulates dual timeframe analysis using different period lengths.
Fast periods represent lower TF, slow periods represent higher TF.

Entry Long: Both timeframe views bullish
Entry Short: Both timeframe views bearish

Optimal Timeframes: 15m, 1h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DualTFConfirmation(Strategy):
    """Dual Timeframe Confirmation Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MTF_001"
        self.strategy_name = "Dual TF Confirmation"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_ma', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'medium_ma', 'type': int, 'min': 18, 'max': 25, 'default': 20},
            {'name': 'htf_fast', 'type': int, 'min': 40, 'max': 60, 'default': 50},
            {'name': 'htf_slow', 'type': int, 'min': 180, 'max': 220, 'default': 200},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    # Lower timeframe view (fast periods)
    @property
    def ltf_fast_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['fast_ma'])

    @property
    def ltf_slow_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['medium_ma'])

    @property
    def ltf_bullish(self) -> bool:
        return self.ltf_fast_ma > self.ltf_slow_ma and self.close > self.ltf_fast_ma

    @property
    def ltf_bearish(self) -> bool:
        return self.ltf_fast_ma < self.ltf_slow_ma and self.close < self.ltf_fast_ma

    # Higher timeframe view (slow periods)
    @property
    def htf_fast_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['htf_fast'])

    @property
    def htf_slow_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['htf_slow'])

    @property
    def htf_bullish(self) -> bool:
        return self.htf_fast_ma > self.htf_slow_ma

    @property
    def htf_bearish(self) -> bool:
        return self.htf_fast_ma < self.htf_slow_ma

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.htf_bullish and self.ltf_bullish

    def should_short(self) -> bool:
        return self.htf_bearish and self.ltf_bearish

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
        if self.is_long and (not self.htf_bullish or self.ltf_bearish):
            self.liquidate()
        elif self.is_short and (not self.htf_bearish or self.ltf_bullish):
            self.liquidate()
