"""
TF_005: Parabolic SAR Trend Strategy
------------------------------------
Follow Parabolic SAR for trend direction.

Entry Long: SAR flips below price
Entry Short: SAR flips above price

Optimal Timeframes: 15m, 1h
Complexity: 3/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ParabolicTrend(Strategy):
    """Parabolic SAR Trend Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "TF_005"
        self.strategy_name = "Parabolic Trend"
        self.complexity = 3
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'acceleration', 'type': float, 'min': 0.01, 'max': 0.03, 'default': 0.02},
            {'name': 'maximum', 'type': float, 'min': 0.15, 'max': 0.25, 'default': 0.2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def sar(self) -> float:
        return ta.sar(self.candles, acceleration=self.hp['acceleration'], maximum=self.hp['maximum'])

    @property
    def prev_sar(self) -> float:
        return ta.sar(self.candles[:-1], acceleration=self.hp['acceleration'], maximum=self.hp['maximum'])

    @property
    def sar_bullish(self) -> bool:
        return self.sar < self.close

    @property
    def prev_sar_bullish(self) -> bool:
        return self.prev_sar < self.candles[-2, 2]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # SAR just flipped bullish
        return self.sar_bullish and not self.prev_sar_bullish

    def should_short(self) -> bool:
        # SAR just flipped bearish
        return not self.sar_bullish and self.prev_sar_bullish

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.sar - (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = self.sar + (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Trail stop using SAR
        if self.is_long:
            new_stop = self.sar - (self.atr * 0.5)
            if new_stop > self.stop_loss:
                self.stop_loss = self.position.qty, new_stop
            if not self.sar_bullish:
                self.liquidate()
        elif self.is_short:
            new_stop = self.sar + (self.atr * 0.5)
            if new_stop < self.stop_loss:
                self.stop_loss = self.position.qty, new_stop
            if self.sar_bullish:
                self.liquidate()
