"""
DC_001: Donchian Channel Breakout (Turtle Trading) Strategy
-----------------------------------------------------------
Classic Turtle Trading system using Donchian Channels.

Entry Long: Price breaks 20-day high
Entry Short: Price breaks 20-day low
Exit: Price breaks 10-day low/high

Optimal Timeframes: 4h, 1d
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DonchianTurtle(Strategy):
    """Donchian Channel Turtle Trading Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "DC_001"
        self.strategy_name = "Donchian Turtle"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'entry_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'exit_period', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'atr_period', 'type': int, 'min': 14, 'max': 21, 'default': 20},
            {'name': 'risk_units', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
        ]

    def _donchian(self, period: int, candles=None):
        """Calculate Donchian Channel"""
        if candles is None:
            candles = self.candles

        high = candles[:, 3]
        low = candles[:, 4]

        upper = np.max(high[-period:])
        lower = np.min(low[-period:])
        middle = (upper + lower) / 2

        return upper, middle, lower

    @property
    def entry_upper(self) -> float:
        upper, middle, lower = self._donchian(self.hp['entry_period'])
        return upper

    @property
    def entry_lower(self) -> float:
        upper, middle, lower = self._donchian(self.hp['entry_period'])
        return lower

    @property
    def exit_upper(self) -> float:
        upper, middle, lower = self._donchian(self.hp['exit_period'])
        return upper

    @property
    def exit_lower(self) -> float:
        upper, middle, lower = self._donchian(self.hp['exit_period'])
        return lower

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=self.hp['atr_period'])

    @property
    def prev_entry_upper(self) -> float:
        upper, middle, lower = self._donchian(self.hp['entry_period'], self.candles[:-1])
        return upper

    @property
    def prev_entry_lower(self) -> float:
        upper, middle, lower = self._donchian(self.hp['entry_period'], self.candles[:-1])
        return lower

    def should_long(self) -> bool:
        # Break above entry high
        return self.candles[-2, 3] < self.prev_entry_upper and self.high >= self.entry_upper

    def should_short(self) -> bool:
        # Break below entry low
        return self.candles[-2, 4] > self.prev_entry_lower and self.low <= self.entry_lower

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.entry_upper
        stop = entry - (self.atr * self.hp['risk_units'])

        # Turtle position sizing: risk 1% per ATR unit
        risk_per_unit = self.atr
        risk_amount = self.balance * 0.01
        qty = risk_amount / risk_per_unit

        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.entry_lower
        stop = entry + (self.atr * self.hp['risk_units'])

        risk_per_unit = self.atr
        risk_amount = self.balance * 0.01
        qty = risk_amount / risk_per_unit

        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Exit on opposite channel break
        if self.is_long and self.low <= self.exit_lower:
            self.liquidate()
        elif self.is_short and self.high >= self.exit_upper:
            self.liquidate()
