"""
MTF_004: Timeframe Momentum Cascade Strategy
--------------------------------------------
Trade when momentum aligns across timeframe views.

Entry Long: Momentum positive on all timeframe views
Entry Short: Momentum negative on all timeframe views

Optimal Timeframes: 15m, 1h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TFMomentumCascade(Strategy):
    """Timeframe Momentum Cascade Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MTF_004"
        self.strategy_name = "TF Momentum Cascade"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ltf_mom', 'type': int, 'min': 5, 'max': 10, 'default': 8},
            {'name': 'mtf_mom', 'type': int, 'min': 20, 'max': 40, 'default': 30},
            {'name': 'htf_mom', 'type': int, 'min': 80, 'max': 120, 'default': 100},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def ltf_momentum(self) -> float:
        return ta.roc(self.candles, period=self.hp['ltf_mom'])

    @property
    def mtf_momentum(self) -> float:
        return ta.roc(self.candles, period=self.hp['mtf_mom'])

    @property
    def htf_momentum(self) -> float:
        return ta.roc(self.candles, period=self.hp['htf_mom'])

    @property
    def all_positive(self) -> bool:
        return self.ltf_momentum > 0 and self.mtf_momentum > 0 and self.htf_momentum > 0

    @property
    def all_negative(self) -> bool:
        return self.ltf_momentum < 0 and self.mtf_momentum < 0 and self.htf_momentum < 0

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.all_positive

    def should_short(self) -> bool:
        return self.all_negative

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
        if self.is_long and self.htf_momentum < 0:
            self.liquidate()
        elif self.is_short and self.htf_momentum > 0:
            self.liquidate()
