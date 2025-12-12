"""
KC_001: Keltner Channel Breakout Strategy
-----------------------------------------
Trade breakouts beyond Keltner Channels.

Entry Long: Price closes above upper KC
Entry Short: Price closes below lower KC

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class KeltnerBreakout(Strategy):
    """Keltner Channel Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "KC_001"
        self.strategy_name = "Keltner Breakout"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ema_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_period', 'type': int, 'min': 7, 'max': 20, 'default': 10},
            {'name': 'multiplier', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _get_keltner(self, candles=None):
        """Calculate Keltner Channels"""
        if candles is None:
            candles = self.candles

        ema = ta.ema(candles, period=self.hp['ema_period'])
        atr_val = ta.atr(candles, period=self.hp['atr_period'])

        upper = ema + (atr_val * self.hp['multiplier'])
        lower = ema - (atr_val * self.hp['multiplier'])

        return upper, ema, lower

    @property
    def kc_upper(self) -> float:
        upper, middle, lower = self._get_keltner()
        return upper

    @property
    def kc_middle(self) -> float:
        upper, middle, lower = self._get_keltner()
        return middle

    @property
    def kc_lower(self) -> float:
        upper, middle, lower = self._get_keltner()
        return lower

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.close > self.kc_upper

    def should_short(self) -> bool:
        return self.close < self.kc_lower

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.kc_upper - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = self.kc_lower + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        if self.is_long and self.close < self.kc_middle:
            self.liquidate()
        elif self.is_short and self.close > self.kc_middle:
            self.liquidate()
