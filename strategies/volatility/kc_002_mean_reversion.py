"""
KC_002: Keltner Channel Mean Reversion Strategy
-----------------------------------------------
Trade mean reversion at Keltner Channel extremes.

Entry Long: Price at lower KC, targeting middle
Entry Short: Price at upper KC, targeting middle

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class KeltnerMeanReversion(Strategy):
    """Keltner Channel Mean Reversion Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "KC_002"
        self.strategy_name = "Keltner Mean Reversion"
        self.complexity = 3
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ema_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_period', 'type': int, 'min': 7, 'max': 20, 'default': 10},
            {'name': 'multiplier', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'require_reversal', 'type': bool, 'default': True},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 0.5, 'max': 2.0, 'default': 1.0},
        ]

    def _get_keltner(self):
        ema = ta.ema(self.candles, period=self.hp['ema_period'])
        atr_val = ta.atr(self.candles, period=self.hp['atr_period'])
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

    def _at_lower(self) -> bool:
        return self.low <= self.kc_lower

    def _at_upper(self) -> bool:
        return self.high >= self.kc_upper

    def _bullish_reversal(self) -> bool:
        if not self.hp.get('require_reversal', True):
            return True
        return self.close > self.open

    def _bearish_reversal(self) -> bool:
        if not self.hp.get('require_reversal', True):
            return True
        return self.close < self.open

    def should_long(self) -> bool:
        return self._at_lower() and self._bullish_reversal()

    def should_short(self) -> bool:
        return self._at_upper() and self._bearish_reversal()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.kc_lower - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, self.kc_middle

    def go_short(self):
        entry = self.price
        stop = self.kc_upper + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, self.kc_middle

    def update_position(self):
        pass
