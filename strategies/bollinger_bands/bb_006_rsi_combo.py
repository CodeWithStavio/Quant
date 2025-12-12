"""
BB_006: BB + RSI Combo Strategy
-------------------------------
Combine BB touch with RSI confirmation.

Entry Long: Price at lower BB AND RSI < 30
Entry Short: Price at upper BB AND RSI > 70

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BBRSICombo(Strategy):
    """BB + RSI Combo Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BB_006"
        self.strategy_name = "BB + RSI"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'bb_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'bb_std', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'rsi_period', 'type': int, 'min': 7, 'max': 21, 'default': 14},
            {'name': 'rsi_oversold', 'type': int, 'min': 20, 'max': 35, 'default': 30},
            {'name': 'rsi_overbought', 'type': int, 'min': 65, 'max': 80, 'default': 70},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.5, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.5},
        ]

    def _get_bb(self):
        return ta.bollinger_bands(
            self.candles,
            period=self.hp['bb_period'],
            devup=self.hp['bb_std'],
            devdn=self.hp['bb_std']
        )

    @property
    def bb_upper(self) -> float:
        upper, middle, lower = self._get_bb()
        return upper

    @property
    def bb_middle(self) -> float:
        upper, middle, lower = self._get_bb()
        return middle

    @property
    def bb_lower(self) -> float:
        upper, middle, lower = self._get_bb()
        return lower

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _at_lower_band(self) -> bool:
        return self.low <= self.bb_lower

    def _at_upper_band(self) -> bool:
        return self.high >= self.bb_upper

    def should_long(self) -> bool:
        return self._at_lower_band() and self.rsi < self.hp['rsi_oversold']

    def should_short(self) -> bool:
        return self._at_upper_band() and self.rsi > self.hp['rsi_overbought']

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.bb_lower - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, self.bb_middle),
            (0.5, self.bb_upper),
        ]

    def go_short(self):
        entry = self.price
        stop = self.bb_upper + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, self.bb_middle),
            (0.5, self.bb_lower),
        ]

    def update_position(self):
        # Exit when RSI returns to neutral
        if self.is_long and self.rsi > 50:
            pass  # Let TP/SL handle
        elif self.is_short and self.rsi < 50:
            pass
