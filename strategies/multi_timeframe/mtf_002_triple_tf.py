"""
MTF_002: Triple Timeframe Alignment Strategy
--------------------------------------------
Three-tier timeframe analysis using different period lengths.

Entry Long: All three timeframe views aligned bullish
Entry Short: All three timeframe views aligned bearish

Optimal Timeframes: 15m, 1h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TripleTFAlignment(Strategy):
    """Triple Timeframe Alignment Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MTF_002"
        self.strategy_name = "Triple TF Alignment"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ltf_period', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'mtf_period', 'type': int, 'min': 35, 'max': 55, 'default': 45},
            {'name': 'htf_period', 'type': int, 'min': 150, 'max': 250, 'default': 200},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def ltf_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['ltf_period'])

    @property
    def mtf_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['mtf_period'])

    @property
    def htf_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['htf_period'])

    @property
    def all_bullish(self) -> bool:
        return (self.close > self.ltf_ma > self.mtf_ma > self.htf_ma)

    @property
    def all_bearish(self) -> bool:
        return (self.close < self.ltf_ma < self.mtf_ma < self.htf_ma)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.all_bullish

    def should_short(self) -> bool:
        return self.all_bearish

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.htf_ma - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = self.htf_ma + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        if self.is_long and not self.all_bullish:
            self.liquidate()
        elif self.is_short and not self.all_bearish:
            self.liquidate()
