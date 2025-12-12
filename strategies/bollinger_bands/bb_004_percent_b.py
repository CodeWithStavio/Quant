"""
BB_004: Bollinger %B Strategy
-----------------------------
%B shows where price is relative to the bands.
%B = (Price - Lower Band) / (Upper Band - Lower Band)

Entry Long: %B < 0 (price below lower band)
Entry Short: %B > 1 (price above upper band)

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BBPercentB(Strategy):
    """Bollinger %B Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BB_004"
        self.strategy_name = "BB %B"
        self.complexity = 3
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'std_dev', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'oversold', 'type': float, 'min': -0.1, 'max': 0.1, 'default': 0.0},
            {'name': 'overbought', 'type': float, 'min': 0.9, 'max': 1.1, 'default': 1.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.5, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    def _get_percent_b(self, candles=None) -> float:
        if candles is None:
            candles = self.candles

        upper, middle, lower = ta.bollinger_bands(
            candles,
            period=self.hp['period'],
            devup=self.hp['std_dev'],
            devdn=self.hp['std_dev']
        )

        close = candles[-1, 2]
        if upper - lower == 0:
            return 0.5

        return (close - lower) / (upper - lower)

    @property
    def percent_b(self) -> float:
        return self._get_percent_b()

    @property
    def percent_b_prev(self) -> float:
        return self._get_percent_b(self.candles[:-1])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # %B crosses above oversold from below
        return self.percent_b_prev <= self.hp['oversold'] and self.percent_b > self.hp['oversold']

    def should_short(self) -> bool:
        # %B crosses below overbought from above
        return self.percent_b_prev >= self.hp['overbought'] and self.percent_b < self.hp['overbought']

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
        # Exit at middle of bands
        if self.is_long and self.percent_b > 0.5:
            pass  # Let TP/SL handle
        elif self.is_short and self.percent_b < 0.5:
            pass
