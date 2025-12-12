"""
TF_001: Trend Continuation Strategy
-----------------------------------
Enter on pullbacks in established trends.

Entry Long: Pullback in uptrend
Entry Short: Rally in downtrend

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TrendContinuation(Strategy):
    """Trend Continuation Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "TF_001"
        self.strategy_name = "Trend Continuation"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'trend_ma', 'type': int, 'min': 40, 'max': 60, 'default': 50},
            {'name': 'pullback_ma', 'type': int, 'min': 15, 'max': 25, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def trend_ma(self) -> float:
        return ta.sma(self.candles, period=self.hp['trend_ma'])

    @property
    def pullback_ma(self) -> float:
        return ta.sma(self.candles, period=self.hp['pullback_ma'])

    @property
    def in_uptrend(self) -> bool:
        return self.pullback_ma > self.trend_ma

    @property
    def in_downtrend(self) -> bool:
        return self.pullback_ma < self.trend_ma

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Uptrend with pullback to shorter MA
        if not self.in_uptrend:
            return False
        # Price touched pullback MA and bounced
        touched_ma = self.low <= self.pullback_ma
        bounced = self.close > self.pullback_ma and self.close > self.open
        return touched_ma and bounced

    def should_short(self) -> bool:
        # Downtrend with rally to shorter MA
        if not self.in_downtrend:
            return False
        # Price touched pullback MA and rejected
        touched_ma = self.high >= self.pullback_ma
        rejected = self.close < self.pullback_ma and self.close < self.open
        return touched_ma and rejected

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        target = entry + (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        target = entry - (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        # Exit if trend reverses
        if self.is_long and not self.in_uptrend:
            self.liquidate()
        elif self.is_short and not self.in_downtrend:
            self.liquidate()
