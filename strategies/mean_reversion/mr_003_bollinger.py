"""
MR_003: Bollinger Mean Reversion Strategy
-----------------------------------------
Trade bounces off Bollinger Bands.

Entry Long: Price touches lower band
Entry Short: Price touches upper band

Optimal Timeframes: 15m, 1h
Complexity: 3/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BollingerMeanReversion(Strategy):
    """Bollinger Mean Reversion Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MR_003"
        self.strategy_name = "Bollinger Mean Reversion"
        self.complexity = 3
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'bb_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'bb_mult', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    @property
    def bb(self):
        return ta.bollinger_bands(self.candles, period=self.hp['bb_period'], devup=self.hp['bb_mult'], devdn=self.hp['bb_mult'])

    @property
    def upper_band(self) -> float:
        return self.bb[0]

    @property
    def middle_band(self) -> float:
        return self.bb[1]

    @property
    def lower_band(self) -> float:
        return self.bb[2]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Price touches or goes below lower band with bullish reversal
        return self.low <= self.lower_band and self.close > self.open

    def should_short(self) -> bool:
        # Price touches or goes above upper band with bearish reversal
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
        # Exit at middle band
        if self.is_long and self.close >= self.middle_band:
            self.liquidate()
        elif self.is_short and self.close <= self.middle_band:
            self.liquidate()
