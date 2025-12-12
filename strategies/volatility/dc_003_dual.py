"""
DC_003: Dual Donchian System
----------------------------
Original Turtle Trading dual-period system.
System 1: 20-day entry, 10-day exit
System 2: 55-day entry, 20-day exit

Entry Long: Break 20/55-day high
Entry Short: Break 20/55-day low
Exit: Opposite channel break

Optimal Timeframes: 4h, 1d
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DualDonchian(Strategy):
    """Dual Donchian System (Turtle S1/S2)"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "DC_003"
        self.strategy_name = "Dual Donchian"
        self.complexity = 4
        self.crypto_suitability = 8
        self.last_trade_profitable = False

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 's1_entry', 'type': int, 'min': 15, 'max': 25, 'default': 20},
            {'name': 's1_exit', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 's2_entry', 'type': int, 'min': 45, 'max': 65, 'default': 55},
            {'name': 's2_exit', 'type': int, 'min': 15, 'max': 25, 'default': 20},
            {'name': 'use_s2_failsafe', 'type': bool, 'default': True},
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
    def s1_entry_upper(self) -> float:
        upper, _, _ = self._donchian(self.hp['s1_entry'])
        return upper

    @property
    def s1_entry_lower(self) -> float:
        _, _, lower = self._donchian(self.hp['s1_entry'])
        return lower

    @property
    def s1_exit_upper(self) -> float:
        upper, _, _ = self._donchian(self.hp['s1_exit'])
        return upper

    @property
    def s1_exit_lower(self) -> float:
        _, _, lower = self._donchian(self.hp['s1_exit'])
        return lower

    @property
    def s2_entry_upper(self) -> float:
        upper, _, _ = self._donchian(self.hp['s2_entry'])
        return upper

    @property
    def s2_entry_lower(self) -> float:
        _, _, lower = self._donchian(self.hp['s2_entry'])
        return lower

    @property
    def s2_exit_upper(self) -> float:
        upper, _, _ = self._donchian(self.hp['s2_exit'])
        return upper

    @property
    def s2_exit_lower(self) -> float:
        _, _, lower = self._donchian(self.hp['s2_exit'])
        return lower

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=self.hp['atr_period'])

    def _s1_long_signal(self) -> bool:
        """System 1 long signal - skip if last S1 trade was profitable"""
        if self.hp['use_s2_failsafe'] and self.last_trade_profitable:
            return False
        return self.high >= self.s1_entry_upper

    def _s1_short_signal(self) -> bool:
        """System 1 short signal - skip if last S1 trade was profitable"""
        if self.hp['use_s2_failsafe'] and self.last_trade_profitable:
            return False
        return self.low <= self.s1_entry_lower

    def _s2_long_signal(self) -> bool:
        """System 2 long signal - always take"""
        return self.high >= self.s2_entry_upper

    def _s2_short_signal(self) -> bool:
        """System 2 short signal - always take"""
        return self.low <= self.s2_entry_lower

    def should_long(self) -> bool:
        return self._s1_long_signal() or self._s2_long_signal()

    def should_short(self) -> bool:
        return self._s1_short_signal() or self._s2_short_signal()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        # Determine which system triggered
        is_s2 = self._s2_long_signal()
        entry = self.s2_entry_upper if is_s2 else self.s1_entry_upper
        stop = entry - (self.atr * self.hp['risk_units'])

        # Turtle position sizing
        risk_per_unit = self.atr
        risk_amount = self.balance * 0.01
        qty = risk_amount / risk_per_unit

        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        is_s2 = self._s2_short_signal()
        entry = self.s2_entry_lower if is_s2 else self.s1_entry_lower
        stop = entry + (self.atr * self.hp['risk_units'])

        risk_per_unit = self.atr
        risk_amount = self.balance * 0.01
        qty = risk_amount / risk_per_unit

        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Exit on opposite channel break (use S1 exit for S1, S2 exit for S2)
        if self.is_long:
            if self.low <= self.s1_exit_lower:
                self.liquidate()
        elif self.is_short:
            if self.high >= self.s1_exit_upper:
                self.liquidate()

    def on_close_position(self, order):
        """Track if last trade was profitable for S1 filtering"""
        if hasattr(order, 'pnl'):
            self.last_trade_profitable = order.pnl > 0
