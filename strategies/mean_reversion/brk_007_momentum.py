"""
BRK_007: Momentum Breakout Strategy
-----------------------------------
Trade breakouts confirmed by strong momentum.

Entry Long: Price breaks high with strong positive momentum
Entry Short: Price breaks low with strong negative momentum

Optimal Timeframes: 15m, 1h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MomentumBreakout(Strategy):
    """Momentum Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BRK_007"
        self.strategy_name = "Momentum Breakout"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'rsi_threshold', 'type': int, 'min': 55, 'max': 70, 'default': 60},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def period_high(self) -> float:
        return np.max(self.candles[-self.hp['lookback']:-1, 3])

    @property
    def period_low(self) -> float:
        return np.min(self.candles[-self.hp['lookback']:-1, 4])

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=14)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Breakout above period high with strong RSI
        return (self.close > self.period_high and
                self.rsi > self.hp['rsi_threshold'])

    def should_short(self) -> bool:
        # Breakdown below period low with weak RSI
        return (self.close < self.period_low and
                self.rsi < (100 - self.hp['rsi_threshold']))

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
        # Exit on momentum reversal
        if self.is_long and self.rsi < 50:
            self.liquidate()
        elif self.is_short and self.rsi > 50:
            self.liquidate()
