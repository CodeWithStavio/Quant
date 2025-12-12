"""
MR_007: Overbought/Oversold Reversion Strategy
----------------------------------------------
Combine multiple oscillators for extreme readings.

Entry Long: Multiple indicators show oversold
Entry Short: Multiple indicators show overbought

Optimal Timeframes: 15m, 1h
Complexity: 5/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class OverboughtOversoldReversion(Strategy):
    """Overbought/Oversold Reversion Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MR_007"
        self.strategy_name = "Overbought Oversold Reversion"
        self.complexity = 5
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'stoch_period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'cci_period', 'type': int, 'min': 15, 'max': 25, 'default': 20},
            {'name': 'oversold_threshold', 'type': int, 'min': 2, 'max': 3, 'default': 2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def stoch(self):
        return ta.stoch(self.candles, fastk_period=self.hp['stoch_period'], slowk_period=3, slowd_period=3)

    @property
    def stoch_k(self) -> float:
        return self.stoch[0]

    @property
    def cci(self) -> float:
        return ta.cci(self.candles, period=self.hp['cci_period'])

    def _count_oversold_signals(self) -> int:
        """Count how many indicators show oversold"""
        count = 0
        if self.rsi < 30:
            count += 1
        if self.stoch_k < 20:
            count += 1
        if self.cci < -100:
            count += 1
        return count

    def _count_overbought_signals(self) -> int:
        """Count how many indicators show overbought"""
        count = 0
        if self.rsi > 70:
            count += 1
        if self.stoch_k > 80:
            count += 1
        if self.cci > 100:
            count += 1
        return count

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._count_oversold_signals() >= self.hp['oversold_threshold']

    def should_short(self) -> bool:
        return self._count_overbought_signals() >= self.hp['oversold_threshold']

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
        # Exit when indicators normalize
        if self.is_long and self._count_oversold_signals() == 0:
            self.liquidate()
        elif self.is_short and self._count_overbought_signals() == 0:
            self.liquidate()
