"""
RISK_007: Equity Curve Trading Strategy
---------------------------------------
Trade based on strategy equity curve momentum.

Entry Long: Strategy performing well (equity above MA)
Entry Short: Strategy performing well (equity above MA)

Optimal Timeframes: 4h, 1d
Complexity: 7/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class EquityCurveTrading(Strategy):
    """Equity Curve Trading Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "RISK_007"
        self.strategy_name = "Equity Curve Trading"
        self.complexity = 7
        self.crypto_suitability = 8
        self.equity_history = []
        self.initial_balance = None

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'equity_ma', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _update_equity_history(self):
        """Track equity history"""
        if self.initial_balance is None:
            self.initial_balance = self.balance

        self.equity_history.append(self.balance)

        # Keep last 100 values
        if len(self.equity_history) > 100:
            self.equity_history = self.equity_history[-100:]

    @property
    def equity_above_ma(self) -> bool:
        """Check if equity is above its moving average"""
        self._update_equity_history()

        ma_period = self.hp['equity_ma']
        if len(self.equity_history) < ma_period:
            return True  # Not enough data, allow trading

        equity_ma = np.mean(self.equity_history[-ma_period:])
        return self.balance >= equity_ma

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

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=14)

    def should_long(self) -> bool:
        # Only trade if equity curve is healthy
        if not self.equity_above_ma:
            return False
        return self.trend == 1 and self.rsi > 40 and self.rsi < 70

    def should_short(self) -> bool:
        if not self.equity_above_ma:
            return False
        return self.trend == -1 and self.rsi < 60 and self.rsi > 30

    def should_cancel_entry(self) -> bool:
        return not self.equity_above_ma

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
        self._update_equity_history()
        if self.is_long and self.trend == -1:
            self.liquidate()
        elif self.is_short and self.trend == 1:
            self.liquidate()
