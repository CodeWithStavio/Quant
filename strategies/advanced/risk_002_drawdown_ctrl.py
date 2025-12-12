"""
RISK_002: Drawdown Control Strategy
-----------------------------------
Reduce exposure during drawdown periods.

Entry Long: Signal with drawdown-adjusted sizing
Entry Short: Signal with drawdown-adjusted sizing

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DrawdownControl(Strategy):
    """Drawdown Control Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "RISK_002"
        self.strategy_name = "Drawdown Control"
        self.complexity = 6
        self.crypto_suitability = 8
        self.peak_balance = None

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'base_risk', 'type': float, 'min': 0.01, 'max': 0.03, 'default': 0.02},
            {'name': 'max_drawdown', 'type': float, 'min': 0.1, 'max': 0.25, 'default': 0.15},
            {'name': 'reduction_rate', 'type': float, 'min': 0.3, 'max': 0.7, 'default': 0.5},
        ]

    def _update_peak(self):
        """Track peak balance"""
        if self.peak_balance is None or self.balance > self.peak_balance:
            self.peak_balance = self.balance

    @property
    def current_drawdown(self) -> float:
        """Calculate current drawdown from peak"""
        self._update_peak()
        if self.peak_balance is None or self.peak_balance == 0:
            return 0
        return (self.peak_balance - self.balance) / self.peak_balance

    @property
    def risk_scalar(self) -> float:
        """Reduce risk during drawdown"""
        dd = self.current_drawdown
        max_dd = self.hp['max_drawdown']

        if dd >= max_dd:
            return 0  # Stop trading
        elif dd > max_dd * 0.5:
            # Reduce proportionally
            return 1 - (dd / max_dd) * self.hp['reduction_rate']
        return 1.0

    @property
    def adjusted_risk(self) -> float:
        return self.hp['base_risk'] * self.risk_scalar

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def trend(self) -> int:
        ma = ta.sma(self.candles, period=20)
        if self.close > ma:
            return 1
        elif self.close < ma:
            return -1
        return 0

    def should_long(self) -> bool:
        return self.risk_scalar > 0 and self.trend == 1

    def should_short(self) -> bool:
        return self.risk_scalar > 0 and self.trend == -1

    def should_cancel_entry(self) -> bool:
        return self.risk_scalar == 0

    def go_long(self):
        if self.adjusted_risk <= 0:
            return
        entry = self.price
        stop = entry - (self.atr * 2)
        qty = utils.size_to_qty(self.balance * self.adjusted_risk, entry)
        if qty > 0:
            self.buy = qty, entry
            self.stop_loss = qty, stop

    def go_short(self):
        if self.adjusted_risk <= 0:
            return
        entry = self.price
        stop = entry + (self.atr * 2)
        qty = utils.size_to_qty(self.balance * self.adjusted_risk, entry)
        if qty > 0:
            self.sell = qty, entry
            self.stop_loss = qty, stop

    def update_position(self):
        self._update_peak()
        if self.is_long and self.trend == -1:
            self.liquidate()
        elif self.is_short and self.trend == 1:
            self.liquidate()
