"""
MR_004: Keltner Mean Reversion Strategy
---------------------------------------
Trade bounces off Keltner Channel extremes.

Entry Long: Price touches lower Keltner band
Entry Short: Price touches upper Keltner band

Optimal Timeframes: 15m, 1h
Complexity: 3/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class KeltnerMeanReversion(Strategy):
    """Keltner Mean Reversion Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MR_004"
        self.strategy_name = "Keltner Mean Reversion"
        self.complexity = 3
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ema_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'atr_mult', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    @property
    def keltner(self):
        return ta.keltner(self.candles, period=self.hp['ema_period'], multiplier=self.hp['atr_mult'], atr_period=self.hp['atr_period'])

    @property
    def upper_band(self) -> float:
        return self.keltner[0]

    @property
    def middle_band(self) -> float:
        return self.keltner[1]

    @property
    def lower_band(self) -> float:
        return self.keltner[2]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Price touches lower Keltner band with reversal
        return self.low <= self.lower_band and self.close > self.open

    def should_short(self) -> bool:
        # Price touches upper Keltner band with reversal
        return self.high >= self.upper_band and self.close < self.open

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.lower_band - (self.atr * self.hp['atr_multiplier_sl'])
        target = self.middle_band
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = self.upper_band + (self.atr * self.hp['atr_multiplier_sl'])
        target = self.middle_band
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        if self.is_long and self.close >= self.middle_band:
            self.liquidate()
        elif self.is_short and self.close <= self.middle_band:
            self.liquidate()
